from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import yaml

from scope_static.experiments.s2d_config import load_s2d_physical_config, output_root_from_config
from scope_static.physical.active_mixed_basis import evaluate_active_mixed_basis_methods, rzz_family_metrics
from scope_static.physical.rzz_depth_sweep import evaluate_rzz_depth_sweep_methods
from scope_static.physical.targeted_v3 import evaluate_targeted_v3_methods
from scope_static.physical_oracle import run_physical_oracle_stack, stack_stage_results


DEFAULT_RUNS: list[dict[str, object]] = [
    {
        "name": "phys9_setA",
        "profile": "phys9_chain",
        "mechanism_set": "set_A",
        "purpose": "regression sanity profile before balanced depth sweep runs",
    },
    {
        "name": "phys9_multicircuit_setB_balanced",
        "profile": "phys9_multicircuit_setB_balanced",
        "mechanism_set": "set_B",
        "purpose": "balanced set_B RZZ depth sweep target",
    },
    {
        "name": "phys9_multicircuit_setC_balanced",
        "profile": "phys9_multicircuit_setC_balanced",
        "mechanism_set": "set_C",
        "purpose": "balanced set_C RZZ depth sweep target",
    },
]


def run_s2d8a_rzz_depth_sweep(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    max_runs: int | None = None,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    cfg = _load_config(config_path)
    root = output_root_from_config(physical_cfg)
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", root / "S2D.8_RZZ_dynamical_probe_design")))
    output.mkdir(parents=True, exist_ok=True)
    runs = _enabled_runs(cfg)
    if max_runs is not None:
        runs = runs[: int(max_runs)]

    records = [_run_one(output, physical_cfg, cfg, run_cfg) for run_cfg in runs]
    result = {
        "schema": "scope_static_s2d8a_rzz_depth_sweep_v1",
        "stage": "S2D.8a_RZZ_depth_sweep",
        "output_dir": str(output),
        "run_order": [record["name"] for record in records],
        "records": records,
        "summary": _summary(records),
        "phase_summary": _phase_summary(records),
    }
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_s2d8a_summary(result))
    (output / "depth_probe_manifest.json").write_text(json.dumps(_aggregate(records, "depth_probe_manifest"), indent=2, sort_keys=True) + "\n")
    (output / "depth_response_features.json").write_text(json.dumps(_aggregate_nested(records, "depth_sweep", "depth_response_features"), indent=2, sort_keys=True) + "\n")
    (output / "rzz_family_distance_audit.json").write_text(
        json.dumps(_aggregate_nested(records, "depth_sweep", "rzz_family_distance_audit"), indent=2, sort_keys=True) + "\n"
    )
    (output / "scrambled_depth_control.json").write_text(json.dumps(_scrambled_depth_control(records), indent=2, sort_keys=True) + "\n")
    (output / "baseline_comparison.json").write_text(json.dumps(_baseline_comparison(records), indent=2, sort_keys=True) + "\n")
    (output / "feature_provenance_manifest.json").write_text(json.dumps(_aggregate(records, "feature_provenance_manifest"), indent=2, sort_keys=True) + "\n")
    (output / "phase_summary.json").write_text(json.dumps(result["phase_summary"], indent=2, sort_keys=True) + "\n")
    return result


def _run_one(output: Path, physical_cfg: dict[str, object], cfg: dict[str, object], run_cfg: dict[str, object]) -> dict[str, object]:
    run_dir = output / str(run_cfg["name"])
    run_dir.mkdir(parents=True, exist_ok=True)
    merged = dict(physical_cfg)
    merged.update({key: value for key, value in run_cfg.items() if key not in {"name", "purpose", "enabled"}})
    merged.update(dict(cfg.get("physical_overrides", {})))
    base_cfg = {**merged, "probe_set": str(cfg.get("baseline_probe_set", "base"))}
    static_cfg = {**merged, "probe_set": str(cfg.get("static_active_probe_set", "rzz_active_minimal"))}
    depth_cfg = {**merged, "probe_set": str(cfg.get("depth_probe_set", "rzz_depth_sweep"))}

    base_stack = _run_phys_stack(run_dir / "base_probe", base_cfg, cfg)
    static_stack = _run_phys_stack(run_dir / "s2d7_static_active_probe", static_cfg, cfg)
    depth_stack = _run_phys_stack(run_dir / "rzz_depth_probe", depth_cfg, cfg)

    base_records, base_observations, base_probe_names, base_hidden, base_label_names = _load_stack_data(base_stack)
    static_records, static_observations, static_probe_names, static_hidden, static_label_names = _load_stack_data(static_stack)
    depth_records, depth_observations, depth_probe_names, hidden, label_names = _load_stack_data(depth_stack)
    if base_label_names != label_names or static_label_names != label_names or len(base_records) != len(depth_records) or len(static_records) != len(depth_records):
        raise ValueError("S2D.8a probe stacks must produce the same mechanism label inventory")

    base_targeted = _targeted_from_stack(base_stack, base_records, base_observations, base_probe_names, base_hidden, base_label_names)
    static_targeted = _targeted_from_stack(static_stack, static_records, static_observations, static_probe_names, static_hidden, static_label_names)
    static_labels = static_targeted["labels_by_method"]
    static_local_labels = _comparison_labels(static_stack["local"])
    static_active = evaluate_active_mixed_basis_methods(
        static_records,
        static_observations,
        static_probe_names,
        static_hidden,
        static_label_names,
        comparison_labels={
            "active_probe_only_v3c": static_labels["v3c_physical_local_inverse_probability_v3_typed"],
            "direct_Salpha": static_local_labels["direct_S_alpha_assignment"],
            "oracle_fingerprint_upper_bound": static_local_labels["oracle_fingerprint_upper_bound"],
        },
    )
    depth_targeted = _targeted_from_stack(depth_stack, depth_records, depth_observations, depth_probe_names, hidden, label_names)
    depth_labels = depth_targeted["labels_by_method"]
    depth_local_labels = _comparison_labels(depth_stack["local"])
    depth_sweep = evaluate_rzz_depth_sweep_methods(
        depth_records,
        depth_observations,
        depth_probe_names,
        hidden,
        label_names,
        comparison_labels={
            "rzz_depth_probe_only_v3c": depth_labels["v3c_physical_local_inverse_probability_v3_typed"],
            "direct_Salpha": depth_local_labels["direct_S_alpha_assignment"],
            "oracle_fingerprint_upper_bound": depth_local_labels["oracle_fingerprint_upper_bound"],
        },
        bootstrap_replicates=int(cfg.get("bootstrap_replicates", 16)),
        seed=int(depth_cfg.get("seed", 0)),
    )
    combined_labels = _combined_labels(base_targeted, static_active, depth_sweep)
    combined_rzz = rzz_family_metrics(combined_labels, hidden, label_names)
    method_rows = _combined_method_rows(base_targeted, static_active, depth_sweep, combined_rzz)
    decision = _run_decision(method_rows, combined_rzz)
    record = {
        "name": str(run_cfg["name"]),
        "purpose": str(run_cfg.get("purpose", "")),
        "profile": str(merged.get("profile")),
        "mechanism_set": str(merged.get("mechanism_set")),
        "num_qubits": int(depth_stack["teacher"].get("num_qubits", depth_cfg.get("num_qubits", 0))),
        "shots": int(depth_cfg.get("shots", 0)),
        "baseline_probe_set": str(base_cfg.get("probe_set")),
        "static_active_probe_set": str(static_cfg.get("probe_set")),
        "depth_probe_set": str(depth_cfg.get("probe_set")),
        "decision": decision,
        "teacher": {
            "mechanism_counts": depth_stack["teacher"].get("mechanism_counts", {}),
            "num_circuit_batches": depth_stack["teacher"].get("num_circuit_batches", 1),
            "balanced_min_instances_per_mechanism": depth_stack["teacher"].get("balanced_min_instances_per_mechanism"),
        },
        "PHYS2": {
            "baseline": _compact_phys2(base_stack["separability"]),
            "static_active": _compact_phys2(static_stack["separability"]),
            "depth": _compact_phys2(depth_stack["separability"]),
            "audit_only_upper_bound": True,
        },
        "PHYS3": {str(row["method"]): row for row in method_rows},
        "method_rows": method_rows,
        "combined_rzz_family_metrics": combined_rzz,
        "static_active": static_active,
        "depth_sweep": depth_sweep,
        "depth_probe_manifest": depth_sweep["depth_probe_manifest"],
        "feature_provenance_manifest": depth_sweep["feature_provenance_manifest"],
    }
    _write_run_artifacts(run_dir, record)
    return record


def _run_phys_stack(run_dir: Path, cfg: dict[str, object], s2d8_cfg: dict[str, object]) -> dict[str, object]:
    stack = run_physical_oracle_stack(
        cfg,
        output_dir=run_dir,
        bootstrap_replicates=int(s2d8_cfg.get("bootstrap_replicates", 16)),
        random_baseline_trials=int(s2d8_cfg.get("random_baseline_trials", 64)),
        run_local_inverse="always",
    )
    return stack_stage_results(stack)


def _load_stack_data(stack: dict[str, object]) -> tuple[list[dict[str, object]], np.ndarray, list[str], torch.Tensor, list[str]]:
    records = _load_mechanism_records(stack["teacher_dir"] / "oracle_mechanisms.json")
    observations, probe_names = _load_observations(stack["teacher_dir"] / "observations.npz")
    hidden, label_names = _encode_labels([str(record["oracle_label"]) for record in records])
    return records, observations, probe_names, hidden, label_names


def _targeted_from_stack(
    stack: dict[str, object],
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: list[str],
    hidden: torch.Tensor,
    label_names: list[str],
) -> dict[str, object]:
    comparisons = _comparison_labels(stack["local"])
    return evaluate_targeted_v3_methods(
        records,
        observations,
        probe_names,
        hidden,
        label_names,
        comparison_labels={
            "physical_local_inverse_probability": comparisons["physical_local_inverse_probability"],
            **({"physical_local_inverse_probability_v2": comparisons["physical_local_inverse_probability_v2"]} if "physical_local_inverse_probability_v2" in comparisons else {}),
            "direct_S_alpha_assignment": comparisons["direct_S_alpha_assignment"],
            "oracle_fingerprint_upper_bound": comparisons["oracle_fingerprint_upper_bound"],
        },
    )


def _comparison_labels(local: object) -> dict[str, list[int]]:
    return {str(item["comparison"]): [int(value) for value in item["labels"]] for item in local["comparisons"]}  # type: ignore[index]


def _combined_labels(base_targeted: dict[str, object], static_active: dict[str, object], depth_sweep: dict[str, object]) -> dict[str, list[int]]:
    base = base_targeted["labels_by_method"]
    static = static_active["labels_by_method"]
    depth = depth_sweep["labels_by_method"]
    return {
        "baseline_v3c": [int(value) for value in base["v3c_physical_local_inverse_probability_v3_typed"]],
        "S2D.7_active_mixed_basis_moments_plus_signed_contrasts": [
            int(value) for value in static["active_mixed_basis_moments_plus_signed_contrasts"]
        ],
        "rzz_depth_probe_only_v3c": [int(value) for value in depth["rzz_depth_probe_only_v3c"]],
        "rzz_depth_features": [int(value) for value in depth["rzz_depth_features"]],
        "scrambled_depth_control": [int(value) for value in depth["scrambled_depth_control"]],
        "direct_Salpha": [int(value) for value in depth["direct_Salpha"]],
        "oracle_fingerprint_upper_bound": [int(value) for value in depth["oracle_fingerprint_upper_bound"]],
    }


def _combined_method_rows(
    base_targeted: dict[str, object],
    static_active: dict[str, object],
    depth_sweep: dict[str, object],
    combined_rzz: dict[str, object],
) -> list[dict[str, object]]:
    rows = []
    base_map = {str(row["method"]): row for row in base_targeted["methods"]}  # type: ignore[index]
    baseline = dict(base_map["v3c_physical_local_inverse_probability_v3_typed"])
    baseline["method"] = "baseline_v3c"
    baseline["probe_role"] = "baseline_base_probe"
    rows.append(_with_rzz_metrics(baseline, combined_rzz))
    static_map = {str(row["method"]): row for row in static_active["methods"]}  # type: ignore[index]
    static = dict(static_map["active_mixed_basis_moments_plus_signed_contrasts"])
    static["method"] = "S2D.7_active_mixed_basis_moments_plus_signed_contrasts"
    static["probe_role"] = "S2D.7_static_active_reference"
    rows.append(_with_rzz_metrics(static, combined_rzz))
    for row in depth_sweep["methods"]:  # type: ignore[index]
        current = dict(row)
        current["probe_role"] = "S2D.8a_depth_sweep"
        rows.append(_with_rzz_metrics(current, combined_rzz))
    order = [
        "baseline_v3c",
        "S2D.7_active_mixed_basis_moments_plus_signed_contrasts",
        "rzz_depth_probe_only_v3c",
        "rzz_depth_features",
        "scrambled_depth_control",
        "direct_Salpha",
        "oracle_fingerprint_upper_bound",
    ]
    index = {name: idx for idx, name in enumerate(order)}
    return sorted(rows, key=lambda item: index.get(str(item["method"]), 10_000))


def _with_rzz_metrics(row: dict[str, object], combined_rzz: dict[str, object]) -> dict[str, object]:
    method = str(row["method"])
    metrics = combined_rzz.get("methods", {}).get(method, {}) if isinstance(combined_rzz.get("methods"), dict) else {}
    return {**row, "rzz_family_metrics": metrics}


def _run_decision(method_rows: list[dict[str, object]], combined_rzz: dict[str, object]) -> str:
    methods = {str(row["method"]): row for row in method_rows}
    depth = methods.get("rzz_depth_features", {})
    scrambled = methods.get("scrambled_depth_control", {})
    direct = methods.get("direct_Salpha", {})
    baseline = methods.get("baseline_v3c", {})
    static = methods.get("S2D.7_active_mixed_basis_moments_plus_signed_contrasts", {})
    reference_rzz = min(_rzz_error(combined_rzz, "baseline_v3c"), _rzz_error(combined_rzz, "S2D.7_active_mixed_basis_moments_plus_signed_contrasts"))
    depth_rzz = _rzz_error(combined_rzz, "rzz_depth_features")
    m1_m6_m9_ref = min(
        _rzz_error(combined_rzz, "baseline_v3c", include_transverse=False),
        _rzz_error(combined_rzz, "S2D.7_active_mixed_basis_moments_plus_signed_contrasts", include_transverse=False),
    )
    m1_m6_m9_depth = _rzz_error(combined_rzz, "rzz_depth_features", include_transverse=False)
    regression_clean = (
        float(baseline.get("ari", 0.0)) >= 0.99
        and float(static.get("ari", 0.0)) >= 0.99
        and float(depth.get("ari", 0.0)) >= 0.99
        and float(depth.get("nmi", 0.0)) >= 0.99
        and depth_rzz <= reference_rzz
    )
    if regression_clean:
        return "regression_pass"
    global_ok = float(depth.get("ari", 0.0)) >= 0.80 and float(depth.get("nmi", 0.0)) >= 0.80
    if global_ok and depth_rzz < reference_rzz and _beats(depth, scrambled) and _beats(depth, direct):
        return "success"
    if m1_m6_m9_depth < m1_m6_m9_ref:
        return "partial_m1_m6_m9_improved"
    return "failure"


def _rzz_error(combined_rzz: dict[str, object], method: str, *, include_transverse: bool = True) -> int:
    metrics = combined_rzz.get("methods", {}).get(method, {}) if isinstance(combined_rzz.get("methods"), dict) else {}
    keys = ["M8_M9_merge_count", "M8_M12_merge_count", "M8_split_count"]
    if include_transverse:
        keys.append("M8_M10_merge_count")
    return int(sum(int(metrics.get(key, 0)) for key in keys))


def _beats(left: dict[str, object], right: dict[str, object]) -> bool:
    return float(left.get("ari", 0.0)) > float(right.get("ari", 0.0)) and float(left.get("nmi", 0.0)) > float(right.get("nmi", 0.0))


def _summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if "balanced" in str(record.get("profile", ""))]
    return {
        "num_runs": len(records),
        "num_primary_balanced_runs": len(primary),
        "success": sum(1 for record in records if record["decision"] == "success"),
        "regression_pass": sum(1 for record in records if record["decision"] == "regression_pass"),
        "partial_m1_m6_m9_improved": sum(1 for record in records if record["decision"] == "partial_m1_m6_m9_improved"),
        "failure": sum(1 for record in records if record["decision"] == "failure"),
        "primary_balanced_success": all(record["decision"] == "success" for record in primary) if primary else False,
    }


def _phase_summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if "balanced" in str(record.get("profile", ""))]
    primary_failed = bool(primary) and all(record["decision"] == "failure" for record in primary)
    scrambled_matched = bool(primary) and all(
        record["depth_sweep"]["scrambled_depth_control"].get("real_ari") == record["depth_sweep"]["scrambled_depth_control"].get("scrambled_ari")
        and record["depth_sweep"]["scrambled_depth_control"].get("real_nmi") == record["depth_sweep"]["scrambled_depth_control"].get("scrambled_nmi")
        for record in primary
    )
    return {
        "schema": "scope_static_s2d8a_phase_summary_v1",
        "stage": "S2D.8a_RZZ_depth_sweep",
        "phase_label": "depth_sweep_control_matched_negative" if primary_failed and scrambled_matched else "depth_sweep_not_frozen",
        "main_conclusion": (
            "RZZ depth sweep features are learner-visible and improve some global scores, "
            "but they match the scrambled-depth control and do not close the RZZ-family gap."
            if primary_failed and scrambled_matched
            else "S2D.8a phase conclusion requires failed balanced primary runs and matched scrambled controls."
        ),
        "ruled_out_hypothesis": (
            "RZZ-family gap can be solved by depth-sweep final-shot response features alone."
            if primary_failed and scrambled_matched
            else None
        ),
        "not_ruled_out": "echo/no-echo or twirl-style dynamical probes" if primary_failed and scrambled_matched else None,
        "next_recommended_step": "S2D.8b_RZZ_echo_no_echo_probe_design" if primary_failed and scrambled_matched else None,
    }


def format_s2d8a_summary(result: dict[str, object]) -> str:
    phase = result.get("phase_summary", {})
    lines = [
        "# S2D.8a RZZ Depth Sweep",
        "",
        "| run | decision | baseline v3c | S2D.7 static | depth features | scrambled depth | RZZ error ref/depth | boot NMI |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for record in result["records"]:  # type: ignore[index]
        methods = {str(row["method"]): row for row in record["method_rows"]}
        baseline = methods["baseline_v3c"]
        static = methods["S2D.7_active_mixed_basis_moments_plus_signed_contrasts"]
        depth = methods["rzz_depth_features"]
        scrambled = methods["scrambled_depth_control"]
        rzz = record["combined_rzz_family_metrics"]
        ref_error = min(_rzz_error(rzz, "baseline_v3c"), _rzz_error(rzz, "S2D.7_active_mixed_basis_moments_plus_signed_contrasts"))
        depth_error = _rzz_error(rzz, "rzz_depth_features")
        bootstrap = depth.get("bootstrap_nmi", {})
        lines.append(
            f"| {record['name']} | {record['decision']} | "
            f"{float(baseline['ari']):.4f}/{float(baseline['nmi']):.4f} | "
            f"{float(static['ari']):.4f}/{float(static['nmi']):.4f} | "
            f"{float(depth['ari']):.4f}/{float(depth['nmi']):.4f} | "
            f"{float(scrambled['ari']):.4f}/{float(scrambled['nmi']):.4f} | "
            f"{ref_error}/{depth_error} | {float(bootstrap.get('min_vs_full', 1.0)):.4f} |"
        )
    if phase:
        lines.extend(
            [
                "",
                "## Phase Conclusion",
                "",
                f"- Label: `{phase.get('phase_label')}`",
                f"- Conclusion: {phase.get('main_conclusion')}",
                f"- Ruled out: `{phase.get('ruled_out_hypothesis')}`",
                f"- Next: `{phase.get('next_recommended_step')}`",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _write_run_artifacts(run_dir: Path, record: dict[str, object]) -> None:
    (run_dir / "metrics.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    (run_dir / "summary.md").write_text(format_s2d8a_summary({"records": [record]}))
    (run_dir / "depth_probe_manifest.json").write_text(json.dumps(record["depth_probe_manifest"], indent=2, sort_keys=True) + "\n")
    (run_dir / "depth_response_features.json").write_text(json.dumps(record["depth_sweep"]["depth_response_features"], indent=2, sort_keys=True) + "\n")
    (run_dir / "rzz_family_distance_audit.json").write_text(json.dumps(record["depth_sweep"]["rzz_family_distance_audit"], indent=2, sort_keys=True) + "\n")
    (run_dir / "scrambled_depth_control.json").write_text(json.dumps(record["depth_sweep"]["scrambled_depth_control"], indent=2, sort_keys=True) + "\n")
    (run_dir / "baseline_comparison.json").write_text(json.dumps(_run_baseline_comparison(record), indent=2, sort_keys=True) + "\n")
    (run_dir / "feature_provenance_manifest.json").write_text(json.dumps(record["feature_provenance_manifest"], indent=2, sort_keys=True) + "\n")


def _aggregate(records: list[dict[str, object]], key: str) -> dict[str, object]:
    return {"schema": f"scope_static_s2d8a_{key}_aggregate_v1", "runs": {str(record["name"]): record[key] for record in records}}


def _aggregate_nested(records: list[dict[str, object]], parent: str, key: str) -> dict[str, object]:
    return {"schema": f"scope_static_s2d8a_{key}_aggregate_v1", "runs": {str(record["name"]): record[parent][key] for record in records}}


def _scrambled_depth_control(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d8a_scrambled_depth_control_v1",
        "runs": {str(record["name"]): record["depth_sweep"]["scrambled_depth_control"] for record in records},
    }


def _baseline_comparison(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d8a_baseline_comparison_v1",
        "runs": {str(record["name"]): _run_baseline_comparison(record) for record in records},
    }


def _run_baseline_comparison(record: dict[str, object]) -> dict[str, object]:
    methods = {str(row["method"]): row for row in record["method_rows"]}
    return {
        "decision": record["decision"],
        "baseline_v3c": _compact_method(methods["baseline_v3c"]),
        "S2D.7_active_mixed_basis_moments_plus_signed_contrasts": _compact_method(
            methods["S2D.7_active_mixed_basis_moments_plus_signed_contrasts"]
        ),
        "rzz_depth_features": _compact_method(methods["rzz_depth_features"]),
        "scrambled_depth_control": _compact_method(methods["scrambled_depth_control"]),
        "direct_Salpha": _compact_method(methods["direct_Salpha"]),
        "oracle_fingerprint_upper_bound": _compact_method(methods["oracle_fingerprint_upper_bound"]),
        "depth_key_comparison": record["depth_sweep"]["key_comparison"],
    }


def _compact_method(row: dict[str, object]) -> dict[str, object]:
    return {
        "ari": row.get("ari"),
        "nmi": row.get("nmi"),
        "active_clusters": row.get("active_clusters"),
        "rzz_family_metrics": row.get("rzz_family_metrics"),
    }


def _compact_phys2(metrics: dict[str, object]) -> dict[str, object]:
    return {
        "ari": metrics.get("ari"),
        "nmi": metrics.get("nmi"),
        "active_clusters": metrics.get("active_clusters"),
        "separability_gate": metrics.get("separability_gate"),
        "feature_shape": metrics.get("feature_shape"),
        "fingerprint_families": metrics.get("fingerprint_families"),
    }


def _enabled_runs(cfg: dict[str, object]) -> list[dict[str, object]]:
    raw = cfg.get("runs", DEFAULT_RUNS)
    if not isinstance(raw, list):
        raise ValueError("s2d8a_rzz_depth_sweep.runs must be a list")
    return [dict(item) for item in raw if isinstance(item, dict) and bool(item.get("enabled", True))]


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {"runs": DEFAULT_RUNS}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D.8a config must be a mapping")
    section = data.get("s2d8a_rzz_depth_sweep", {})
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise ValueError("s2d8a_rzz_depth_sweep config must be a mapping")
    result = dict(section)
    result.setdefault("runs", DEFAULT_RUNS)
    return result


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text())
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def _load_observations(path: Path) -> tuple[np.ndarray, list[str]]:
    data = np.load(path)
    return np.asarray(data["observations"], dtype=np.float64), [str(value) for value in data["probe_names"].tolist()]


def _encode_labels(labels: list[str]) -> tuple[torch.Tensor, list[str]]:
    names = sorted(set(labels))
    index = {name: idx for idx, name in enumerate(names)}
    return torch.tensor([index[label] for label in labels], dtype=torch.long), names


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S2D.8a RZZ depth sweep.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-runs", type=int, default=None)
    args = parser.parse_args(argv)
    result = run_s2d8a_rzz_depth_sweep(args.config, output_dir=args.output_dir, max_runs=args.max_runs)
    print(
        "S2D.8a RZZ depth sweep complete\n"
        f"  runs={result['run_order']}\n"
        f"  output={result['output_dir']}\n"
        f"  summary={result['summary']}"
    )


if __name__ == "__main__":
    main()
