from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments.s2d_config import output_root_from_config, load_s2d_physical_config
from scope_static.physical.active_mixed_basis import build_active_mixed_basis_features
from scope_static.physical.rzz_depth_sweep import build_rzz_depth_sweep_features
from scope_static.physical.rzz_echo_contrast import build_rzz_echo_contrast_features
from scope_static.physical.rzz_observability_ceiling import (
    FeatureBlock,
    audit_labels_schema,
    evaluate_ceiling_feature_blocks,
    features_schema,
    grouped_fold_audit,
    leakage_guardrail_audit,
)
from scope_static.physical.targeted_v3 import RZZ_FAMILY, build_targeted_v3_features


DEFAULT_RUNS = ["phys9_setA", "phys9_multicircuit_setB_balanced", "phys9_multicircuit_setC_balanced"]
PRIMARY_RUNS = ["phys9_multicircuit_setB_balanced", "phys9_multicircuit_setC_balanced"]


def run_s2d8c_rzz_observability_ceiling(
    config_path: str | Path | None = None,
    *,
    source_root: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    cfg = _load_config(config_path)
    root = output_root_from_config(physical_cfg)
    default_source = root / "S2D.8_RZZ_dynamical_probe_design" / "S2D.8b_RZZ_echo_no_echo_probe_design"
    source = Path(source_root) if source_root is not None else Path(str(cfg.get("source_root", default_source)))
    default_output = root / "S2D.8_RZZ_dynamical_probe_design" / "S2D.8c_RZZ_observability_ceiling_audit"
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", default_output)))
    output.mkdir(parents=True, exist_ok=True)

    runs = [str(value) for value in cfg.get("runs", DEFAULT_RUNS)]
    records = [_run_one(source, run_name, cfg) for run_name in runs]
    primary = [record for record in records if record["name"] in set(PRIMARY_RUNS)]
    result = {
        "schema": "scope_static_s2d8c_rzz_observability_ceiling_v1",
        "stage": "S2D.8c_RZZ_observability_ceiling_audit",
        "source_root": str(source),
        "output_dir": str(output),
        "no_new_teacher_sampling": True,
        "records": records,
        "verdict": _global_verdict(primary),
        "summary": _summary(records),
    }
    _write_artifacts(output, result)
    return result


def _run_one(source: Path, run_name: str, cfg: dict[str, object]) -> dict[str, object]:
    run_dir = source / str(run_name)
    base_records, base_obs, base_names = _load_stack(run_dir / "base_probe" / "S2D_PHYS1_teacher")
    static_records, static_obs, static_names = _load_stack(run_dir / "s2d7_static_active_probe" / "S2D_PHYS1_teacher")
    depth_records, depth_obs, depth_names = _load_stack(run_dir / "s2d8a_depth_probe" / "S2D_PHYS1_teacher")
    echo_records, echo_obs, echo_names = _load_stack(run_dir / "rzz_echo_probe" / "S2D_PHYS1_teacher")
    _assert_same_inventory(base_records, static_records, depth_records, echo_records)

    all_labels = [str(record["oracle_label"]) for record in base_records]
    label_names = sorted(set(all_labels))
    num_clusters = len(label_names)
    base_bundle = build_targeted_v3_features(base_records, base_obs, base_names, num_clusters=num_clusters)
    static_bundle = build_active_mixed_basis_features(static_records, static_obs, static_names, num_clusters=num_clusters)
    depth_bundle = build_rzz_depth_sweep_features(depth_records, depth_obs, depth_names, num_clusters=num_clusters)
    echo_bundle = build_rzz_echo_contrast_features(echo_records, echo_obs, echo_names, num_clusters=num_clusters)

    mask = np.asarray([str(record["oracle_label"]) in set(RZZ_FAMILY) for record in base_records], dtype=bool)
    records = [dict(record) for record, keep in zip(base_records, mask.tolist()) if keep]
    labels = [str(record["oracle_label"]) for record in records]
    groups = [int(record.get("circuit_id", 0)) for record in records]

    feature_blocks = _build_feature_blocks(
        base_bundle,
        static_bundle,
        depth_bundle,
        echo_bundle,
        mask=mask,
    )
    feature_schema = features_schema(feature_blocks, source_root=str(source / str(run_name)))
    labels_schema = audit_labels_schema(labels, groups, records)
    fold_audit = grouped_fold_audit(groups) if len(set(groups)) >= 2 else _single_group_fold_audit(groups)
    leakage = leakage_guardrail_audit(feature_blocks, labels_schema, fold_audit)
    if not bool(leakage["passed"]):
        raise RuntimeError(f"S2D.8c leakage guardrail failed for {run_name}: {leakage['checks']}")
    if len(set(labels)) < 2 or len(set(groups)) < 2:
        return {
            "name": str(run_name),
            "role": "primary" if run_name in set(PRIMARY_RUNS) else "regression_context",
            "source_run_dir": str(run_dir),
            "num_rzz_rows": int(len(labels)),
            "labels": labels,
            "groups": groups,
            "verdict": {"run": str(run_name), "passed": False, "label": "SKIP", "reason": "fewer than two RZZ-family labels or circuit_id groups"},
            "ceiling": _skipped_ceiling(labels, groups),
            "features_schema_physics_visible": feature_schema,
            "audit_labels_schema_oracle_only": labels_schema,
            "grouped_fold_audit": fold_audit,
            "leakage_guardrail_audit": leakage,
        }
    ceiling = evaluate_ceiling_feature_blocks(
        feature_blocks,
        labels,
        groups,
        primary_block="v3c_plus_active_all",
        scrambled_control_block="v3c_plus_scrambled_active_all",
        permutation_repeats=int(cfg.get("permutation_repeats", 128)),
        seed=int(cfg.get("seed", 0)),
    )
    verdict = _run_verdict(run_name, ceiling)
    return {
        "name": str(run_name),
        "role": "primary" if run_name in set(PRIMARY_RUNS) else "regression_context",
        "source_run_dir": str(run_dir),
        "num_rzz_rows": int(len(labels)),
        "labels": labels,
        "groups": groups,
        "verdict": verdict,
        "ceiling": ceiling,
        "features_schema_physics_visible": feature_schema,
        "audit_labels_schema_oracle_only": labels_schema,
        "grouped_fold_audit": fold_audit,
        "leakage_guardrail_audit": leakage,
    }


def _build_feature_blocks(
    base_bundle,
    static_bundle,
    depth_bundle,
    echo_bundle,
    *,
    mask: np.ndarray,
) -> dict[str, FeatureBlock]:
    v3c = _rows(base_bundle.feature_spaces["physical_local_inverse_probability_v3_typed"], mask)
    v3c_names = [f"baseline_v3c_{idx}" for idx in range(v3c.shape[1])]
    static_real, static_names = _strip_v3c(
        static_bundle.feature_spaces["active_mixed_basis_moments_plus_signed_contrasts"],
        static_bundle.feature_names["active_mixed_basis_moments_plus_signed_contrasts"],
    )
    static_scrambled, static_scrambled_names = _strip_v3c(
        static_bundle.feature_spaces["active_mixed_basis_scrambled"],
        static_bundle.feature_names["active_mixed_basis_scrambled"],
    )
    depth_real, depth_names = _strip_v3c(depth_bundle.feature_spaces["rzz_depth_features"], depth_bundle.feature_names["rzz_depth_features"])
    depth_scrambled, depth_scrambled_names = _strip_v3c(
        depth_bundle.feature_spaces["scrambled_depth_control"],
        depth_bundle.feature_names["scrambled_depth_control"],
    )
    echo_real, echo_names = _strip_v3c(echo_bundle.feature_spaces["rzz_echo_contrast_features"], echo_bundle.feature_names["rzz_echo_contrast_features"])
    echo_scrambled, echo_scrambled_names = _strip_v3c(
        echo_bundle.feature_spaces["scrambled_echo_control"],
        echo_bundle.feature_names["scrambled_echo_control"],
    )
    static_real = _rows(static_real, mask)
    static_scrambled = _rows(static_scrambled, mask)
    depth_real = _rows(depth_real, mask)
    depth_scrambled = _rows(depth_scrambled, mask)
    echo_real = _rows(echo_real, mask)
    echo_scrambled = _rows(echo_scrambled, mask)
    active_all = _finite(np.concatenate([static_real, depth_real, echo_real], axis=1))
    scrambled_active_all = _finite(np.concatenate([static_scrambled, depth_scrambled, echo_scrambled], axis=1))
    active_names = [
        *[f"s2d7_{name}" for name in static_names],
        *[f"s2d8a_{name}" for name in depth_names],
        *[f"s2d8b_{name}" for name in echo_names],
    ]
    scrambled_active_names = [
        *[f"s2d7_{name}" for name in static_scrambled_names],
        *[f"s2d8a_{name}" for name in depth_scrambled_names],
        *[f"s2d8b_{name}" for name in echo_scrambled_names],
    ]
    return {
        "baseline_v3c_visible": FeatureBlock("baseline_v3c_visible", v3c, v3c_names, ["base_probe:v3c"], explanatory=True),
        "s2d7_static_mixed_basis": FeatureBlock(
            "s2d7_static_mixed_basis",
            static_real,
            [f"s2d7_{name}" for name in static_names],
            ["s2d7_static_active_probe"],
            explanatory=True,
        ),
        "s2d8a_depth": FeatureBlock("s2d8a_depth", depth_real, [f"s2d8a_{name}" for name in depth_names], ["s2d8a_depth_probe"], explanatory=True),
        "s2d8b_echo": FeatureBlock("s2d8b_echo", echo_real, [f"s2d8b_{name}" for name in echo_names], ["rzz_echo_probe"], explanatory=True),
        "active_all": FeatureBlock("active_all", active_all, active_names, ["s2d7", "s2d8a", "s2d8b"], explanatory=True),
        "scrambled_active_all": FeatureBlock(
            "scrambled_active_all",
            scrambled_active_all,
            scrambled_active_names,
            ["s2d7_scrambled", "s2d8a_scrambled", "s2d8b_scrambled"],
            control=True,
        ),
        "v3c_plus_active_all": FeatureBlock(
            "v3c_plus_active_all",
            _finite(np.concatenate([v3c, active_all], axis=1)),
            [*v3c_names, *active_names],
            ["base_probe:v3c", "s2d7", "s2d8a", "s2d8b"],
            primary=True,
        ),
        "v3c_plus_scrambled_active_all": FeatureBlock(
            "v3c_plus_scrambled_active_all",
            _finite(np.concatenate([v3c, scrambled_active_all], axis=1)),
            [*v3c_names, *scrambled_active_names],
            ["base_probe:v3c", "s2d7_scrambled", "s2d8a_scrambled", "s2d8b_scrambled"],
            control=True,
        ),
        "active_residualized_against_v3c": FeatureBlock(
            "active_residualized_against_v3c",
            active_all,
            active_names,
            ["s2d7", "s2d8a", "s2d8b"],
            residualize_against=v3c,
            residualize_feature_names=v3c_names,
            explanatory=True,
        ),
        "scrambled_active_residualized_against_v3c": FeatureBlock(
            "scrambled_active_residualized_against_v3c",
            scrambled_active_all,
            scrambled_active_names,
            ["s2d7_scrambled", "s2d8a_scrambled", "s2d8b_scrambled"],
            residualize_against=v3c,
            residualize_feature_names=v3c_names,
            control=True,
            explanatory=True,
        ),
    }


def _strip_v3c(features: np.ndarray, names: list[str]) -> tuple[np.ndarray, list[str]]:
    keep = [idx for idx, name in enumerate(names) if not str(name).startswith("v3c_")]
    return np.asarray(features, dtype=np.float64)[:, keep], [str(names[idx]) for idx in keep]


def _rows(features: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return _finite(np.asarray(features, dtype=np.float64)[np.asarray(mask, dtype=bool)])


def _finite(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)


def _load_stack(path: Path) -> tuple[list[dict[str, object]], np.ndarray, list[str]]:
    records = _load_mechanism_records(path / "oracle_mechanisms.json")
    observations, probe_names = _load_observations(path / "observations.npz")
    return records, observations, probe_names


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text())
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def _load_observations(path: Path) -> tuple[np.ndarray, list[str]]:
    data = np.load(path)
    return np.asarray(data["observations"], dtype=np.float64), [str(value) for value in data["probe_names"].tolist()]


def _assert_same_inventory(*record_lists: list[dict[str, object]]) -> None:
    reference = [(int(record.get("location_id", idx)), str(record.get("oracle_label")), int(record.get("circuit_id", 0))) for idx, record in enumerate(record_lists[0])]
    for current in record_lists[1:]:
        probe = [(int(record.get("location_id", idx)), str(record.get("oracle_label")), int(record.get("circuit_id", 0))) for idx, record in enumerate(current)]
        if probe != reference:
            raise ValueError("S2D.8c source stacks do not share the same mechanism inventory")


def _run_verdict(run_name: str, ceiling: dict[str, object]) -> dict[str, object]:
    success = ceiling["run_success"]
    passed = bool(success["passed"])
    return {
        "run": str(run_name),
        "passed": passed,
        "label": "PASS" if passed else "FAIL",
        "checks": success["checks"],
    }


def _global_verdict(records: list[dict[str, object]]) -> dict[str, object]:
    by_name = {str(record["name"]): bool(record["verdict"]["passed"]) for record in records}
    set_b = by_name.get("phys9_multicircuit_setB_balanced", False)
    set_c = by_name.get("phys9_multicircuit_setC_balanced", False)
    if set_b and set_c:
        global_label = "GLOBAL_SUCCESS"
    elif set_b or set_c:
        global_label = "MIXED_CONDITION_SPECIFIC_SIGNAL"
    else:
        global_label = "GLOBAL_FAILURE"
    return {
        "setB": "PASS" if set_b else "FAIL",
        "setC": "PASS" if set_c else "FAIL",
        "global": global_label,
        "mixed_interpretation": (
            "Existing S2D.8b artifacts contain learner-visible RZZ-family signal only under some balanced regimes. "
            "This points to condition-specific masking, mechanism-composition effects, or nuisance dominance rather "
            "than a simple universal observability failure."
            if global_label == "MIXED_CONDITION_SPECIFIC_SIGNAL"
            else None
        ),
    }


def _single_group_fold_audit(groups: list[int]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d8c_grouped_fold_audit_v1",
        "splitter": "LeaveOneGroupOut",
        "group_key": "circuit_id",
        "num_folds": 0,
        "folds": [],
        "all_test_groups_disjoint_from_train": True,
        "skipped_reason": "fewer than two circuit_id groups",
        "groups": sorted({int(value) for value in groups}),
    }


def _skipped_ceiling(labels: list[str], groups: list[int]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d8c_grouped_ceiling_v1",
        "skipped": True,
        "skip_reason": "fewer than two RZZ-family labels or circuit_id groups",
        "class_names": sorted(set(labels)),
        "num_rows": int(len(labels)),
        "groups": sorted({int(value) for value in groups}),
        "feature_block_results": {},
        "grouped_fold_predictions": {},
        "controls": {},
        "run_success": {"passed": False, "checks": {}},
        "residualized_active_attribution": {},
        "secondary_nonlinear_diagnostics": {},
    }


def _summary(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "num_runs": len(records),
        "primary_runs": PRIMARY_RUNS,
        "primary_pass_count": sum(1 for record in records if record["name"] in set(PRIMARY_RUNS) and bool(record["verdict"]["passed"])),
    }


def _write_artifacts(output: Path, result: dict[str, object]) -> None:
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_s2d8c_summary(result))
    (output / "features_schema_physics_visible.json").write_text(json.dumps(_collect(result, "features_schema_physics_visible"), indent=2, sort_keys=True) + "\n")
    (output / "audit_labels_schema_oracle_only.json").write_text(json.dumps(_collect(result, "audit_labels_schema_oracle_only"), indent=2, sort_keys=True) + "\n")
    (output / "grouped_ceiling_metrics.json").write_text(json.dumps(_collect_nested(result, "ceiling"), indent=2, sort_keys=True) + "\n")
    (output / "grouped_fold_predictions.json").write_text(json.dumps(_collect_nested(result, "ceiling", "grouped_fold_predictions"), indent=2, sort_keys=True) + "\n")
    (output / "feature_block_results.json").write_text(json.dumps(_collect_nested(result, "ceiling", "feature_block_results"), indent=2, sort_keys=True) + "\n")
    (output / "controls.json").write_text(json.dumps(_collect_nested(result, "ceiling", "controls"), indent=2, sort_keys=True) + "\n")
    (output / "leakage_guardrail_audit.json").write_text(json.dumps(_collect(result, "leakage_guardrail_audit"), indent=2, sort_keys=True) + "\n")
    (output / "residualized_active_attribution.json").write_text(
        json.dumps(_collect_nested(result, "ceiling", "residualized_active_attribution"), indent=2, sort_keys=True) + "\n"
    )


def _collect(result: dict[str, object], key: str) -> dict[str, object]:
    return {"schema": f"scope_static_s2d8c_{key}_aggregate_v1", "runs": {str(record["name"]): record[key] for record in result["records"]}}


def _collect_nested(result: dict[str, object], parent: str, key: str | None = None) -> dict[str, object]:
    if key is None:
        return {"schema": f"scope_static_s2d8c_{parent}_aggregate_v1", "runs": {str(record["name"]): record[parent] for record in result["records"]}}
    return {"schema": f"scope_static_s2d8c_{key}_aggregate_v1", "runs": {str(record["name"]): record[parent][key] for record in result["records"]}}


def format_s2d8c_summary(result: dict[str, object]) -> str:
    verdict = result["verdict"]
    lines = [
        "# S2D.8c RZZ Observability Ceiling Audit",
        "",
        "```text",
        "S2D.8c verdict:",
        f"  setB: {verdict['setB']}",
        f"  setC: {verdict['setC']}",
        f"  global: {verdict['global']}",
        "```",
        "",
        "| run | role | verdict | macro F1 | balanced acc | real-scrambled bal | real-permutation bal | min recall |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for record in result["records"]:
        if bool(record["ceiling"].get("skipped", False)):
            lines.append(
                f"| {record['name']} | {record['role']} | {record['verdict']['label']} | n/a | n/a | n/a | n/a | n/a |"
            )
            continue
        primary = record["ceiling"]["feature_block_results"]["v3c_plus_active_all"]["overall"]
        controls = record["ceiling"]["controls"]
        lines.append(
            f"| {record['name']} | {record['role']} | {record['verdict']['label']} | "
            f"{float(primary['macro_F1']):.4f} | {float(primary['balanced_accuracy']):.4f} | "
            f"{float(controls['real_minus_scrambled_balanced_accuracy']):.4f} | "
            f"{float(controls['real_minus_permutation_balanced_accuracy']):.4f} | "
            f"{float(primary['min_class_recall']):.4f} |"
        )
    if verdict.get("mixed_interpretation"):
        lines.extend(["", "## Mixed Interpretation", "", str(verdict["mixed_interpretation"])])
    lines.append("")
    return "\n".join(lines)


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {"runs": DEFAULT_RUNS}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D.8c config must be a mapping")
    section = data.get("s2d8c_rzz_observability_ceiling", {})
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise ValueError("s2d8c_rzz_observability_ceiling config must be a mapping")
    result = dict(section)
    result.setdefault("runs", DEFAULT_RUNS)
    result.setdefault("permutation_repeats", 128)
    result.setdefault("seed", 0)
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S2D.8c RZZ observability ceiling audit.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--source-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    result = run_s2d8c_rzz_observability_ceiling(args.config, source_root=args.source_root, output_dir=args.output_dir)
    print(
        "S2D.8c RZZ observability ceiling audit complete\n"
        f"  source={result['source_root']}\n"
        f"  output={result['output_dir']}\n"
        f"  verdict={result['verdict']}"
    )


if __name__ == "__main__":
    main()
