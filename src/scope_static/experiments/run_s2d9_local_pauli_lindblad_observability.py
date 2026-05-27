from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments.run_s2d_physical_teacher import generate_physical_teacher_dataset
from scope_static.experiments.s2d_config import load_s2d_physical_config, output_root_from_config
from scope_static.numerics import NUMERICAL_ZERO
from scope_static.physical.local_pauli_lindblad import (
    GENERATOR_COORDINATES,
    LocalPauliLindbladBundle,
    build_local_pauli_lindblad_observability,
)
from scope_static.physical.rzz_observability_ceiling import (
    FeatureBlock,
    audit_labels_schema,
    evaluate_ceiling_feature_blocks,
    features_schema,
    grouped_fold_audit,
    leakage_guardrail_audit,
)
from scope_static.physical.targeted_v3 import RZZ_FAMILY


DEFAULT_RUNS = [
    {
        "name": "phys9_setA",
        "profile": "phys9_chain",
        "mechanism_set": "set_A",
        "purpose": "regression context for local Pauli-Lindblad observability",
    },
    {
        "name": "phys9_multicircuit_setB_balanced",
        "profile": "phys9_multicircuit_setB_balanced",
        "mechanism_set": "set_B",
        "purpose": "balanced set_B local generator-identifiability target",
    },
    {
        "name": "phys9_multicircuit_setC_balanced",
        "profile": "phys9_multicircuit_setC_balanced",
        "mechanism_set": "set_C",
        "purpose": "balanced set_C local generator-identifiability target",
    },
]
PRIMARY_RUNS = {"phys9_multicircuit_setB_balanced", "phys9_multicircuit_setC_balanced"}


def run_s2d9_local_pauli_lindblad_observability(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    max_runs: int | None = None,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    cfg = _load_config(config_path)
    root = output_root_from_config(physical_cfg)
    default_output = root / "S2D.9_local_Pauli_Lindblad_observability"
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", default_output)))
    output.mkdir(parents=True, exist_ok=True)
    runs = _enabled_runs(cfg)
    if max_runs is not None:
        runs = runs[: int(max_runs)]

    records = [_run_one(output, physical_cfg, cfg, run_cfg) for run_cfg in runs]
    result = {
        "schema": "scope_static_s2d9_local_pauli_lindblad_observability_v1",
        "stage": "S2D.9_local_Pauli_Lindblad_observability",
        "primary_object": "local_response_jacobian_generator_coordinate_identifiability",
        "output_dir": str(output),
        "run_order": [record["name"] for record in records],
        "records": records,
        "summary": _summary(records),
        "phase_summary": _phase_summary(records),
    }
    _write_artifacts(output, result)
    return result


def _run_one(output: Path, physical_cfg: dict[str, object], cfg: dict[str, object], run_cfg: dict[str, object]) -> dict[str, object]:
    run_dir = output / str(run_cfg["name"])
    run_dir.mkdir(parents=True, exist_ok=True)
    merged = dict(physical_cfg)
    merged.update({key: value for key, value in run_cfg.items() if key not in {"name", "purpose", "enabled"}})
    merged.update(dict(cfg.get("physical_overrides", {})))
    tomo_cfg = {**merged, "probe_set": str(cfg.get("tomography_probe_set", "rzz_local_tomography"))}
    teacher_dir = run_dir / "S2D_PHYS1_teacher"
    teacher = generate_physical_teacher_dataset(tomo_cfg, output_dir=teacher_dir, preflight_dir=run_dir / "S2D_PHYS0_preflight")
    records, observations, probe_names = _load_stack(teacher_dir)
    bundle = build_local_pauli_lindblad_observability(
        records,
        observations,
        probe_names,
        theta=float(tomo_cfg.get("theta", 0.18)),
        ridge=float(cfg.get("ridge", 1e-8)),
    )
    grouped = _grouped_recovery_bundle(
        run_name=str(run_cfg["name"]),
        records=records,
        bundle=bundle,
        source_root=run_dir,
        cfg=cfg,
    )
    signature = _signature_checks(bundle.generator_recovery_metrics)
    decision = _run_decision(bundle, grouped, signature, run_name=str(run_cfg["name"]))
    record = {
        "name": str(run_cfg["name"]),
        "purpose": str(run_cfg.get("purpose", "")),
        "profile": str(merged.get("profile")),
        "mechanism_set": str(merged.get("mechanism_set")),
        "num_qubits": int(teacher.get("num_qubits", tomo_cfg.get("num_qubits", 0))),
        "shots": int(tomo_cfg.get("shots", 0)),
        "tomography_probe_set": str(tomo_cfg.get("probe_set")),
        "decision": decision,
        "teacher": {
            "mechanism_counts": teacher.get("mechanism_counts", {}),
            "num_circuit_batches": teacher.get("num_circuit_batches", 1),
            "balanced_min_instances_per_mechanism": teacher.get("balanced_min_instances_per_mechanism"),
            "num_probes": teacher.get("num_probes"),
        },
        "primary_object": "local_response_jacobian_generator_coordinate_identifiability",
        "generator_dictionary": bundle.generator_dictionary,
        "probe_observable_schema": bundle.probe_observable_schema,
        "ptm_convention_audit": bundle.ptm_convention_audit,
        "response_jacobian_json": bundle.response_jacobian_json,
        "observability_rank_metrics": bundle.observability_rank_metrics,
        "ptm_block_reconstruction": bundle.ptm_block_reconstruction,
        "generator_coordinate_estimates": bundle.generator_coordinate_estimates,
        "generator_recovery_metrics": bundle.generator_recovery_metrics,
        "signature_checks": signature,
        "secondary_grouped_recovery": grouped,
        "leakage_guardrail_audit": bundle.leakage_guardrail_audit,
    }
    _write_run_artifacts(run_dir, record, bundle)
    return record


def _grouped_recovery_bundle(
    *,
    run_name: str,
    records: list[dict[str, object]],
    bundle: LocalPauliLindbladBundle,
    source_root: Path,
    cfg: dict[str, object],
) -> dict[str, object]:
    mask = np.asarray([str(record.get("oracle_label")) in set(RZZ_FAMILY) for record in records], dtype=bool)
    rzz_records = [dict(record) for record, keep in zip(records, mask.tolist()) if keep]
    labels = [str(record["oracle_label"]) for record in rzz_records]
    groups = [int(record.get("circuit_id", 0)) for record in rzz_records]
    features = _rows(bundle.feature_matrix, mask)
    scrambled = _rows(bundle.scrambled_feature_matrix, mask)
    feature_blocks = {
        "generator_coordinates": FeatureBlock(
            "generator_coordinates",
            features,
            bundle.feature_names,
            ["s2d9_local_tomography_generator_coordinates"],
            primary=True,
        ),
        "scrambled_generator_coordinates": FeatureBlock(
            "scrambled_generator_coordinates",
            scrambled,
            bundle.scrambled_feature_names,
            ["s2d9_scrambled_tomography_generator_coordinates"],
            control=True,
        ),
    }
    feature_schema = features_schema(feature_blocks, source_root=str(source_root))
    labels_schema = audit_labels_schema(labels, groups, rzz_records)
    fold_audit = grouped_fold_audit(groups) if len(set(groups)) >= 2 else _single_group_fold_audit(groups)
    leakage = leakage_guardrail_audit(feature_blocks, labels_schema, fold_audit)
    if not bool(leakage["passed"]):
        raise RuntimeError(f"S2D.9 grouped recovery leakage guardrail failed for {run_name}: {leakage['checks']}")
    if len(set(labels)) < 2 or len(set(groups)) < 2:
        return {
            "name": str(run_name),
            "role": "primary" if run_name in PRIMARY_RUNS else "regression_context",
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
        primary_block="generator_coordinates",
        scrambled_control_block="scrambled_generator_coordinates",
        permutation_repeats=int(cfg.get("permutation_repeats", 128)),
        seed=int(cfg.get("seed", 0)),
    )
    return {
        "name": str(run_name),
        "role": "primary" if run_name in PRIMARY_RUNS else "regression_context",
        "verdict": {
            "run": str(run_name),
            "passed": bool(ceiling["run_success"]["passed"]),
            "label": "PASS" if bool(ceiling["run_success"]["passed"]) else "FAIL",
            "checks": ceiling["run_success"]["checks"],
        },
        "ceiling": ceiling,
        "features_schema_physics_visible": feature_schema,
        "audit_labels_schema_oracle_only": labels_schema,
        "grouped_fold_audit": fold_audit,
        "leakage_guardrail_audit": leakage,
    }


def _signature_checks(metrics: dict[str, object]) -> dict[str, object]:
    by_label = metrics.get("by_oracle_label_audit_only", {})
    checks = {}
    if isinstance(by_label, dict):
        for label, expected in {
            "M1": "h_ZZ",
            "M8": "h_XX_or_h_YY",
            "M7": "stochastic",
            "M10": "relaxation_or_nonunital",
        }.items():
            row = by_label.get(label, {})
            mean_abs = row.get("mean_abs_coordinates", {}) if isinstance(row, dict) else {}
            if not isinstance(mean_abs, dict):
                checks[label] = {"available": False, "passed": False, "expected": expected}
                continue
            h_xx = float(mean_abs.get("h_XX", 0.0))
            h_yy = float(mean_abs.get("h_YY", 0.0))
            h_zz = float(mean_abs.get("h_ZZ", 0.0))
            stochastic = float(np.linalg.norm([mean_abs.get("gamma_XX", 0.0), mean_abs.get("gamma_YY", 0.0), mean_abs.get("gamma_ZZ", 0.0)]))
            relaxation = float(abs(float(mean_abs.get("relaxation_pair", 0.0))) + abs(float(mean_abs.get("nonunital_norm_proxy", 0.0))))
            if label == "M1":
                passed = h_zz > max(h_xx, h_yy, stochastic, relaxation)
            elif label == "M8":
                passed = max(h_xx, h_yy) > max(h_zz, stochastic, relaxation)
            elif label == "M7":
                passed = stochastic > max(h_xx, h_yy, h_zz, relaxation)
            else:
                passed = relaxation > max(h_xx, h_yy, h_zz, stochastic)
            checks[label] = {
                "available": bool(row),
                "passed": bool(passed),
                "expected": expected,
                "mean_abs_h_XX": h_xx,
                "mean_abs_h_YY": h_yy,
                "mean_abs_h_ZZ": h_zz,
                "stochastic_norm": stochastic,
                "relaxation_nonunital_score": relaxation,
            }
    available = [item for item in checks.values() if bool(item.get("available"))]
    return {
        "schema": "scope_static_s2d9_signature_checks_v1",
        "role": "physics_interpretation_audit",
        "checks": checks,
        "all_available_passed": bool(available) and all(bool(item.get("passed")) for item in available),
    }


def _run_decision(bundle: LocalPauliLindbladBundle, grouped: dict[str, object], signature: dict[str, object], *, run_name: str) -> str:
    rank_ok = bool(bundle.observability_rank_metrics.get("full_column_rank", False))
    if run_name == "phys9_setA" and rank_ok:
        return "regression_pass"
    grouped_pass = bool(grouped.get("verdict", {}).get("passed", False))
    signatures_ok = bool(signature.get("all_available_passed", False))
    if rank_ok and grouped_pass and signatures_ok:
        return "success"
    if rank_ok:
        return "partial_identifiable"
    return "failure"


def _summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if record["name"] in PRIMARY_RUNS]
    return {
        "num_runs": len(records),
        "num_primary_balanced_runs": len(primary),
        "success": sum(1 for record in records if record["decision"] == "success"),
        "regression_pass": sum(1 for record in records if record["decision"] == "regression_pass"),
        "partial_identifiable": sum(1 for record in records if record["decision"] == "partial_identifiable"),
        "failure": sum(1 for record in records if record["decision"] == "failure"),
        "primary_balanced_success": all(record["decision"] == "success" for record in primary) if primary else False,
    }


def _phase_summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if record["name"] in PRIMARY_RUNS]
    primary_success = bool(primary) and all(record["decision"] == "success" for record in primary)
    primary_partial = bool(primary) and any(record["decision"] == "partial_identifiable" for record in primary)
    primary_failed = bool(primary) and all(record["decision"] == "failure" for record in primary)
    if primary_success:
        label = "local_generator_observability_positive"
        conclusion = "Local Pauli-Lindblad tomography exposes identifiable RZZ-family generator coordinates on balanced primary runs."
        next_step = "use generator coordinates as the S2D RZZ-family recovery substrate"
    elif primary_partial:
        label = "local_generator_observability_partial"
        conclusion = "The response Jacobian is identifiable, but recovery/signature evidence is incomplete."
        next_step = "debug normalization, nuisance residualization, and generator decision geometry"
    elif primary_failed:
        label = "local_generator_observability_negative"
        conclusion = "The local tomography implementation did not produce sufficient identifiable RZZ-family generator evidence."
        next_step = "inspect PTM/sign tests and consider GST-like self-consistent characterization"
    else:
        label = "local_generator_observability_not_frozen"
        conclusion = "S2D.9 requires balanced primary runs before freezing the phase."
        next_step = None
    return {
        "schema": "scope_static_s2d9_phase_summary_v1",
        "stage": "S2D.9_local_Pauli_Lindblad_observability",
        "phase_label": label,
        "main_conclusion": conclusion,
        "primary_object": "local_response_jacobian_generator_coordinate_identifiability",
        "secondary_recovery_role": "diagnostic_not_primary_verdict",
        "next_recommended_step": next_step,
    }


def format_s2d9_summary(result: dict[str, object]) -> str:
    lines = [
        "# S2D.9 Local Pauli-Lindblad Observability",
        "",
        "| run | decision | rank | condition | grouped ceiling | signatures | probes |",
        "| --- | --- | ---: | ---: | --- | --- | ---: |",
    ]
    for record in result["records"]:
        rank = record["observability_rank_metrics"]
        grouped = record["secondary_grouped_recovery"]["verdict"]
        signatures = record["signature_checks"]
        lines.append(
            f"| {record['name']} | {record['decision']} | "
            f"{int(rank['rank'])}/{int(rank['num_coordinates'])} | "
            f"{float(rank['condition_number']):.4g} | "
            f"{grouped.get('label')} | "
            f"{bool(signatures.get('all_available_passed'))} | "
            f"{int(record['teacher'].get('num_probes') or 0)} |"
        )
    phase = result.get("phase_summary", {})
    if phase:
        lines.extend(
            [
                "",
                "## Phase Conclusion",
                "",
                f"- Label: `{phase.get('phase_label')}`",
                f"- Conclusion: {phase.get('main_conclusion')}",
                f"- Next: `{phase.get('next_recommended_step')}`",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _write_run_artifacts(run_dir: Path, record: dict[str, object], bundle: LocalPauliLindbladBundle) -> None:
    (run_dir / "metrics.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    (run_dir / "summary.md").write_text(format_s2d9_summary({"records": [record]}))
    _write_bundle_artifacts(run_dir, record, bundle)


def _write_artifacts(output: Path, result: dict[str, object]) -> None:
    records = result["records"]
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_s2d9_summary(result))
    if records:
        first = records[0]
        np.save(output / "response_jacobian.npy", np.asarray(first["response_jacobian_json"]["matrix"], dtype=np.float64))
        (output / "generator_dictionary.json").write_text(json.dumps(first["generator_dictionary"], indent=2, sort_keys=True) + "\n")
        (output / "probe_observable_schema.json").write_text(json.dumps(first["probe_observable_schema"], indent=2, sort_keys=True) + "\n")
        (output / "ptm_convention_audit.json").write_text(json.dumps(first["ptm_convention_audit"], indent=2, sort_keys=True) + "\n")
        (output / "response_jacobian.json").write_text(json.dumps(first["response_jacobian_json"], indent=2, sort_keys=True) + "\n")
        (output / "observability_rank_metrics.json").write_text(json.dumps(first["observability_rank_metrics"], indent=2, sort_keys=True) + "\n")
    for artifact in (
        "ptm_block_reconstruction",
        "generator_coordinate_estimates",
        "generator_recovery_metrics",
        "grouped_fold_predictions",
        "feature_block_results",
        "controls",
        "leakage_guardrail_audit",
    ):
        (output / f"{artifact}.json").write_text(json.dumps(_aggregate_artifact(records, artifact), indent=2, sort_keys=True) + "\n")


def _write_bundle_artifacts(run_dir: Path, record: dict[str, object], bundle: LocalPauliLindbladBundle) -> None:
    np.save(run_dir / "response_jacobian.npy", bundle.response_jacobian)
    (run_dir / "generator_dictionary.json").write_text(json.dumps(record["generator_dictionary"], indent=2, sort_keys=True) + "\n")
    (run_dir / "probe_observable_schema.json").write_text(json.dumps(record["probe_observable_schema"], indent=2, sort_keys=True) + "\n")
    (run_dir / "ptm_convention_audit.json").write_text(json.dumps(record["ptm_convention_audit"], indent=2, sort_keys=True) + "\n")
    (run_dir / "response_jacobian.json").write_text(json.dumps(record["response_jacobian_json"], indent=2, sort_keys=True) + "\n")
    (run_dir / "observability_rank_metrics.json").write_text(json.dumps(record["observability_rank_metrics"], indent=2, sort_keys=True) + "\n")
    (run_dir / "ptm_block_reconstruction.json").write_text(json.dumps(record["ptm_block_reconstruction"], indent=2, sort_keys=True) + "\n")
    (run_dir / "generator_coordinate_estimates.json").write_text(json.dumps(record["generator_coordinate_estimates"], indent=2, sort_keys=True) + "\n")
    (run_dir / "generator_recovery_metrics.json").write_text(json.dumps(record["generator_recovery_metrics"], indent=2, sort_keys=True) + "\n")
    _write_grouped_artifacts(run_dir, record)


def _write_grouped_artifacts(path: Path, record: dict[str, object]) -> None:
    ceiling = record["secondary_grouped_recovery"].get("ceiling", {})
    (path / "grouped_fold_predictions.json").write_text(json.dumps(ceiling.get("grouped_fold_predictions", {}), indent=2, sort_keys=True) + "\n")
    (path / "feature_block_results.json").write_text(json.dumps(ceiling.get("feature_block_results", {}), indent=2, sort_keys=True) + "\n")
    (path / "controls.json").write_text(json.dumps(ceiling.get("controls", {}), indent=2, sort_keys=True) + "\n")
    (path / "leakage_guardrail_audit.json").write_text(json.dumps(record["secondary_grouped_recovery"].get("leakage_guardrail_audit", {}), indent=2, sort_keys=True) + "\n")


def _aggregate_artifact(records: list[dict[str, object]], artifact: str) -> dict[str, object]:
    runs = {}
    for record in records:
        if artifact == "grouped_fold_predictions":
            runs[record["name"]] = record["secondary_grouped_recovery"].get("ceiling", {}).get("grouped_fold_predictions", {})
        elif artifact == "feature_block_results":
            runs[record["name"]] = record["secondary_grouped_recovery"].get("ceiling", {}).get("feature_block_results", {})
        elif artifact == "controls":
            runs[record["name"]] = record["secondary_grouped_recovery"].get("ceiling", {}).get("controls", {})
        elif artifact == "leakage_guardrail_audit":
            runs[record["name"]] = {
                "tomography_features": record["leakage_guardrail_audit"],
                "grouped_recovery": record["secondary_grouped_recovery"].get("leakage_guardrail_audit", {}),
            }
        else:
            runs[record["name"]] = record.get(artifact, {})
    return {"schema": f"scope_static_s2d9_{artifact}_aggregate_v1", "runs": runs}


def _rows(features: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return np.nan_to_num(
        np.asarray(features, dtype=np.float64)[np.asarray(mask, dtype=bool)],
        nan=NUMERICAL_ZERO,
        posinf=NUMERICAL_ZERO,
        neginf=-NUMERICAL_ZERO,
    )


def _single_group_fold_audit(groups: list[int]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d9_grouped_fold_audit_v1",
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
        "schema": "scope_static_s2d9_grouped_ceiling_v1",
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


def _enabled_runs(cfg: dict[str, object]) -> list[dict[str, object]]:
    raw = cfg.get("runs", DEFAULT_RUNS)
    if not isinstance(raw, list):
        raise ValueError("s2d9_local_pauli_lindblad_observability.runs must be a list")
    return [dict(item) for item in raw if isinstance(item, dict) and bool(item.get("enabled", True))]


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {"runs": DEFAULT_RUNS}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D.9 config must be a mapping")
    section = data.get("s2d9_local_pauli_lindblad_observability", {})
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise ValueError("s2d9_local_pauli_lindblad_observability config must be a mapping")
    result = dict(section)
    result.setdefault("runs", DEFAULT_RUNS)
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S2D.9 local Pauli-Lindblad observability.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-runs", type=int, default=None)
    args = parser.parse_args(argv)
    result = run_s2d9_local_pauli_lindblad_observability(args.config, output_dir=args.output_dir, max_runs=args.max_runs)
    print(
        "S2D.9 local Pauli-Lindblad observability complete\n"
        f"  runs={result['run_order']}\n"
        f"  output={result['output_dir']}\n"
        f"  summary={result['summary']}"
    )


if __name__ == "__main__":
    main()
