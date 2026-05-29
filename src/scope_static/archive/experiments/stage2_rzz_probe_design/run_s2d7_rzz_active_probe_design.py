from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import yaml

from scope_static.experiments.s2d_config import load_s2d_physical_config, output_root_from_config
from scope_static.physical.active_mixed_basis import evaluate_active_mixed_basis_methods, rzz_family_metrics
from scope_static.physical.targeted_v3 import evaluate_targeted_v3_methods
from scope_static.physical_oracle import run_physical_oracle_stack, stack_stage_results


DEFAULT_RUNS: list[dict[str, object]] = [
    {
        "name": "phys9_setA",
        "profile": "phys9_chain",
        "mechanism_set": "set_A",
        "purpose": "regression sanity profile before balanced active runs",
    },
    {
        "name": "phys9_multicircuit_setB_balanced",
        "profile": "phys9_multicircuit_setB_balanced",
        "mechanism_set": "set_B",
        "purpose": "balanced set_B active-observability target",
    },
    {
        "name": "phys9_multicircuit_setC_balanced",
        "profile": "phys9_multicircuit_setC_balanced",
        "mechanism_set": "set_C",
        "purpose": "balanced set_C active-observability target",
    },
]

S2D7_FREEZE_LABEL = "negative_static_mixed_basis_probe_result"
S2D7_FREEZE_TAGS = [
    "active_mixed_basis_edge_moments_negative",
    "scrambled_control_matched_real_active_features",
    "RZZ_family_gap_not_closed",
    "next_requires_dynamical_RZZ_probes",
]
S2D7_RULED_OUT_HYPOTHESIS = "RZZ-family gap can be solved by static mixed-basis edge moments computed from final shot bits."
S2D8_NEXT_STEP = "S2D.8_RZZ_dynamical_probe_design"


def run_s2d7_rzz_active_probe_design(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    max_runs: int | None = None,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    cfg = _load_config(config_path)
    root = output_root_from_config(physical_cfg)
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", root / "S2D.7_RZZ_active_probe_design")))
    output.mkdir(parents=True, exist_ok=True)
    runs = _enabled_runs(cfg)
    if max_runs is not None:
        runs = runs[: int(max_runs)]

    records = [_run_one(output, physical_cfg, cfg, run_cfg) for run_cfg in runs]
    result = {
        "schema": "scope_static_s2d7_rzz_active_probe_design_v1",
        "stage": "S2D.7_RZZ_active_probe_design",
        "output_dir": str(output),
        "run_order": [record["name"] for record in records],
        "records": records,
        "summary": _summary(records),
        "freeze_summary": _freeze_summary(records),
    }
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_s2d7_summary(result))
    (output / "active_probe_manifest.json").write_text(json.dumps(_aggregate(records, "active_probe_manifest"), indent=2, sort_keys=True) + "\n")
    (output / "feature_provenance_manifest.json").write_text(
        json.dumps(_aggregate(records, "feature_provenance_manifest"), indent=2, sort_keys=True) + "\n"
    )
    (output / "visibility_matrix.json").write_text(json.dumps(_aggregate(records, "visibility_matrix"), indent=2, sort_keys=True) + "\n")
    (output / "rzz_family_distance_audit.json").write_text(
        json.dumps(_aggregate_nested(records, "active_mixed_basis", "rzz_family_distance_audit"), indent=2, sort_keys=True) + "\n"
    )
    (output / "feature_block_ablation.json").write_text(json.dumps(_feature_block_ablation(records), indent=2, sort_keys=True) + "\n")
    (output / "scrambled_basis_control.json").write_text(json.dumps(_scrambled_basis_control(records), indent=2, sort_keys=True) + "\n")
    (output / "phys2_phys3_boundary_audit.json").write_text(json.dumps(_boundary_audit(records), indent=2, sort_keys=True) + "\n")
    (output / "freeze_summary.json").write_text(json.dumps(result["freeze_summary"], indent=2, sort_keys=True) + "\n")
    return result


def _run_one(output: Path, physical_cfg: dict[str, object], cfg: dict[str, object], run_cfg: dict[str, object]) -> dict[str, object]:
    run_dir = output / str(run_cfg["name"])
    run_dir.mkdir(parents=True, exist_ok=True)
    merged = dict(physical_cfg)
    merged.update({key: value for key, value in run_cfg.items() if key not in {"name", "purpose", "enabled"}})
    merged.update(dict(cfg.get("physical_overrides", {})))
    base_cfg = {**merged, "probe_set": str(cfg.get("baseline_probe_set", "base"))}
    active_cfg = {**merged, "probe_set": str(cfg.get("active_probe_set", "rzz_active_minimal"))}

    base_stack = _run_phys_stack(run_dir / "base_probe", base_cfg, cfg)
    active_stack = _run_phys_stack(run_dir / "active_probe", active_cfg, cfg)

    base_records = _load_mechanism_records(base_stack["teacher_dir"] / "oracle_mechanisms.json")
    base_observations, base_probe_names = _load_observations(base_stack["teacher_dir"] / "observations.npz")
    active_records = _load_mechanism_records(active_stack["teacher_dir"] / "oracle_mechanisms.json")
    active_observations, active_probe_names = _load_observations(active_stack["teacher_dir"] / "observations.npz")
    hidden, label_names = _encode_labels([str(record["oracle_label"]) for record in active_records])
    base_hidden, base_label_names = _encode_labels([str(record["oracle_label"]) for record in base_records])
    if base_label_names != label_names or len(base_records) != len(active_records):
        raise ValueError("base and active probe stacks must produce the same mechanism label inventory")

    base_targeted = _targeted_from_stack(base_stack, base_records, base_observations, base_probe_names, base_hidden, base_label_names)
    active_targeted = _targeted_from_stack(active_stack, active_records, active_observations, active_probe_names, hidden, label_names)
    active_labels = active_targeted["labels_by_method"]
    active_local_labels = _comparison_labels(active_stack["local"])
    active_mixed = evaluate_active_mixed_basis_methods(
        active_records,
        active_observations,
        active_probe_names,
        hidden,
        label_names,
        comparison_labels={
            "active_probe_only_v3c": active_labels["v3c_physical_local_inverse_probability_v3_typed"],
            "direct_Salpha": active_local_labels["direct_S_alpha_assignment"],
            "oracle_fingerprint_upper_bound": active_local_labels["oracle_fingerprint_upper_bound"],
        },
    )
    combined_labels = _combined_labels(base_targeted, active_mixed)
    combined_rzz = rzz_family_metrics(combined_labels, hidden, label_names)
    method_rows = _combined_method_rows(base_targeted, active_mixed, combined_rzz)
    decision = _run_decision(method_rows, combined_rzz)
    record = {
        "name": str(run_cfg["name"]),
        "purpose": str(run_cfg.get("purpose", "")),
        "profile": str(merged.get("profile")),
        "mechanism_set": str(merged.get("mechanism_set")),
        "num_qubits": int(active_stack["teacher"].get("num_qubits", active_cfg.get("num_qubits", 0))),
        "shots": int(active_cfg.get("shots", 0)),
        "baseline_probe_set": str(base_cfg.get("probe_set")),
        "active_probe_set": str(active_cfg.get("probe_set")),
        "decision": decision,
        "freeze_label": _record_freeze_label(decision),
        "next_recommended_step": S2D8_NEXT_STEP if decision == "failure" else None,
        "teacher": {
            "mechanism_counts": active_stack["teacher"].get("mechanism_counts", {}),
            "num_circuit_batches": active_stack["teacher"].get("num_circuit_batches", 1),
            "balanced_min_instances_per_mechanism": active_stack["teacher"].get("balanced_min_instances_per_mechanism"),
        },
        "PHYS2": {
            "baseline": _compact_phys2(base_stack["separability"]),
            "active": _compact_phys2(active_stack["separability"]),
            "audit_only_upper_bound": True,
        },
        "PHYS3": {
            "baseline_v1": _method_by_name(method_rows, "baseline_v1"),
            "baseline_v2": _method_by_name(method_rows, "baseline_v2"),
            "baseline_v3c": _method_by_name(method_rows, "baseline_v3c"),
            "active_probe_only_v3c": _method_by_name(method_rows, "active_probe_only_v3c"),
            "active_basis_marginals_only": _method_by_name(method_rows, "active_basis_marginals_only"),
            "active_mixed_basis_moments": _method_by_name(method_rows, "active_mixed_basis_moments"),
            "active_mixed_basis_moments_plus_signed_contrasts": _method_by_name(method_rows, "active_mixed_basis_moments_plus_signed_contrasts"),
            "active_mixed_basis_scrambled": _method_by_name(method_rows, "active_mixed_basis_scrambled"),
            "direct_Salpha": _method_by_name(method_rows, "direct_Salpha"),
            "oracle_fingerprint_upper_bound": _method_by_name(method_rows, "oracle_fingerprint_upper_bound"),
        },
        "method_rows": method_rows,
        "combined_rzz_family_metrics": combined_rzz,
        "active_mixed_basis": active_mixed,
        "active_probe_manifest": active_mixed["active_probe_manifest"],
        "feature_provenance_manifest": active_mixed["feature_provenance_manifest"],
        "visibility_matrix": active_mixed["visibility_matrix"],
        "phys2_phys3_boundary_audit": _run_boundary_audit(base_stack, active_stack, active_mixed),
    }
    _write_run_artifacts(run_dir, record)
    return record


def _run_phys_stack(run_dir: Path, cfg: dict[str, object], s2d7_cfg: dict[str, object]) -> dict[str, object]:
    stack = run_physical_oracle_stack(
        cfg,
        output_dir=run_dir,
        bootstrap_replicates=int(s2d7_cfg.get("bootstrap_replicates", 16)),
        random_baseline_trials=int(s2d7_cfg.get("random_baseline_trials", 64)),
        run_local_inverse="always",
    )
    return stack_stage_results(stack)


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


def _combined_labels(base_targeted: dict[str, object], active_mixed: dict[str, object]) -> dict[str, list[int]]:
    base = base_targeted["labels_by_method"]
    active = dict(active_mixed["labels_by_method"])
    return {
        "baseline_v1": [int(value) for value in base["v1_physical_local_inverse_probability"]],
        "baseline_v2": [int(value) for value in base["v2_physical_local_inverse_probability_v2"]],
        "baseline_v3c": [int(value) for value in base["v3c_physical_local_inverse_probability_v3_typed"]],
        **{str(key): [int(value) for value in values] for key, values in active.items()},
    }


def _combined_method_rows(base_targeted: dict[str, object], active_mixed: dict[str, object], combined_rzz: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    base_map = {str(row["method"]): row for row in base_targeted["methods"]}  # type: ignore[index]
    rename = {
        "baseline_v1": "v1_physical_local_inverse_probability",
        "baseline_v2": "v2_physical_local_inverse_probability_v2",
        "baseline_v3c": "v3c_physical_local_inverse_probability_v3_typed",
    }
    for new_name, old_name in rename.items():
        row = dict(base_map[old_name])
        row["method"] = new_name
        row["probe_role"] = "baseline_base_probe"
        rows.append(_with_rzz_metrics(row, combined_rzz))
    for row in active_mixed["methods"]:  # type: ignore[index]
        current = dict(row)
        current["probe_role"] = "active_probe"
        rows.append(_with_rzz_metrics(current, combined_rzz))
    order = [
        "baseline_v1",
        "baseline_v2",
        "baseline_v3c",
        "active_probe_only_v3c",
        "active_basis_marginals_only",
        "active_mixed_basis_moments",
        "active_mixed_basis_moments_plus_signed_contrasts",
        "active_mixed_basis_scrambled",
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
    active = methods.get("active_mixed_basis_moments_plus_signed_contrasts", {})
    direct = methods.get("direct_Salpha", {})
    scrambled = methods.get("active_mixed_basis_scrambled", {})
    marginals = methods.get("active_basis_marginals_only", {})
    active_rzz = _rzz_error(combined_rzz, "active_mixed_basis_moments_plus_signed_contrasts")
    baseline_rzz = min(_rzz_error(combined_rzz, name) for name in ("baseline_v1", "baseline_v2", "baseline_v3c"))
    m1_m6_m9_active = _rzz_error(combined_rzz, "active_mixed_basis_moments_plus_signed_contrasts", include_transverse=False)
    m1_m6_m9_base = min(_rzz_error(combined_rzz, name, include_transverse=False) for name in ("baseline_v1", "baseline_v2", "baseline_v3c"))
    global_ok = float(active.get("ari", 0.0)) >= 0.80 and float(active.get("nmi", 0.0)) >= 0.80
    rzz_improved = active_rzz < baseline_rzz if baseline_rzz > 0 else active_rzz <= baseline_rzz
    beats_scrambled = _beats(active, scrambled)
    beats_direct = _beats(active, direct)
    beats_marginals = _beats(active, marginals)
    baseline_best = max((methods.get(name, {}) for name in ("baseline_v1", "baseline_v2", "baseline_v3c")), key=lambda row: (float(row.get("ari", 0.0)), float(row.get("nmi", 0.0))))
    regression_clean = (
        float(baseline_best.get("ari", 0.0)) >= 0.99
        and float(baseline_best.get("nmi", 0.0)) >= 0.99
        and float(active.get("ari", 0.0)) >= 0.99
        and float(active.get("nmi", 0.0)) >= 0.99
        and active_rzz <= baseline_rzz
    )
    if regression_clean:
        return "regression_pass"
    if global_ok and rzz_improved and beats_scrambled and beats_direct and beats_marginals:
        return "success"
    if m1_m6_m9_active < m1_m6_m9_base:
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


def _freeze_summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if "balanced" in str(record.get("profile", ""))]
    primary_negative = bool(primary) and all(record["decision"] == "failure" for record in primary)
    return {
        "schema": "scope_static_s2d7_freeze_summary_v1",
        "stage": "S2D.7_RZZ_active_probe_design",
        "freeze_label": S2D7_FREEZE_LABEL if primary_negative else "not_frozen",
        "freeze_tags": S2D7_FREEZE_TAGS if primary_negative else [],
        "main_conclusion": (
            "Mixed-basis edge moments are learner-visible and leakage-clean, "
            "but they do not expose the missing RZZ-family mechanism signal."
            if primary_negative
            else "S2D.7 freeze condition requires failed balanced primary runs."
        ),
        "ruled_out_hypothesis": S2D7_RULED_OUT_HYPOTHESIS if primary_negative else None,
        "not_ruled_out": "active observability in general" if primary_negative else None,
        "next_recommended_step": S2D8_NEXT_STEP if primary_negative else None,
        "next_step_purpose": (
            "Test whether RZZ-family mechanisms become learner-visible under depth, echo, or twirl-style interventions."
            if primary_negative
            else None
        ),
        "do_not_do_next": [
            "more_static_mixed_basis_features",
            "larger_circuits",
            "setD",
            "Google_transfer",
            "S3",
            "full_robustness_grid",
        ]
        if primary_negative
        else [],
    }


def _record_freeze_label(decision: str) -> str | None:
    if decision == "failure":
        return S2D7_FREEZE_LABEL
    if decision == "regression_pass":
        return "regression_clean"
    return None


def format_s2d7_summary(result: dict[str, object]) -> str:
    freeze = result.get("freeze_summary", {})
    lines = [
        "# S2D.7 RZZ Active Probe Design",
        "",
        "| run | decision | baseline v3c | active probe-only | active moments+signed | scrambled | RZZ error base/active |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for record in result["records"]:  # type: ignore[index]
        methods = {str(row["method"]): row for row in record["method_rows"]}
        baseline = methods["baseline_v3c"]
        probe = methods["active_probe_only_v3c"]
        active = methods["active_mixed_basis_moments_plus_signed_contrasts"]
        scrambled = methods["active_mixed_basis_scrambled"]
        rzz = record["combined_rzz_family_metrics"]
        base_error = min(_rzz_error(rzz, name) for name in ("baseline_v1", "baseline_v2", "baseline_v3c"))
        active_error = _rzz_error(rzz, "active_mixed_basis_moments_plus_signed_contrasts")
        lines.append(
            f"| {record['name']} | {record['decision']} | "
            f"{float(baseline['ari']):.4f}/{float(baseline['nmi']):.4f} | "
            f"{float(probe['ari']):.4f}/{float(probe['nmi']):.4f} | "
            f"{float(active['ari']):.4f}/{float(active['nmi']):.4f} | "
            f"{float(scrambled['ari']):.4f}/{float(scrambled['nmi']):.4f} | "
            f"{base_error}/{active_error} |"
        )
    if freeze:
        lines.extend(
            [
                "",
                "## Freeze",
                "",
                f"- Label: `{freeze.get('freeze_label')}`",
                f"- Conclusion: {freeze.get('main_conclusion')}",
                f"- Ruled out: `{freeze.get('ruled_out_hypothesis')}`",
                f"- Next: `{freeze.get('next_recommended_step')}`",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _write_run_artifacts(run_dir: Path, record: dict[str, object]) -> None:
    (run_dir / "metrics.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    (run_dir / "summary.md").write_text(format_s2d7_summary({"records": [record]}))
    (run_dir / "active_probe_manifest.json").write_text(json.dumps(record["active_probe_manifest"], indent=2, sort_keys=True) + "\n")
    (run_dir / "feature_provenance_manifest.json").write_text(json.dumps(record["feature_provenance_manifest"], indent=2, sort_keys=True) + "\n")
    (run_dir / "visibility_matrix.json").write_text(json.dumps(record["visibility_matrix"], indent=2, sort_keys=True) + "\n")
    (run_dir / "rzz_family_distance_audit.json").write_text(
        json.dumps(record["active_mixed_basis"]["rzz_family_distance_audit"], indent=2, sort_keys=True) + "\n"
    )
    (run_dir / "feature_block_ablation.json").write_text(json.dumps(record["method_rows"], indent=2, sort_keys=True) + "\n")
    (run_dir / "scrambled_basis_control.json").write_text(
        json.dumps(record["active_mixed_basis"]["scrambled_basis_control"], indent=2, sort_keys=True) + "\n"
    )
    (run_dir / "phys2_phys3_boundary_audit.json").write_text(json.dumps(record["phys2_phys3_boundary_audit"], indent=2, sort_keys=True) + "\n")


def _feature_block_ablation(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d7_feature_block_ablation_v1",
        "runs": [{"run": record["name"], "decision": record["decision"], "methods": record["method_rows"]} for record in records],
    }


def _scrambled_basis_control(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d7_scrambled_basis_control_v1",
        "runs": {str(record["name"]): record["active_mixed_basis"]["scrambled_basis_control"] for record in records},
    }


def _boundary_audit(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d7_phys2_phys3_boundary_audit_v1",
        "runs": {str(record["name"]): record["phys2_phys3_boundary_audit"] for record in records},
    }


def _run_boundary_audit(base_stack: dict[str, object], active_stack: dict[str, object], active_mixed: dict[str, object]) -> dict[str, object]:
    return {
        "PHYS2_audit_only": {
            "exact_ptm_entries_allowed": True,
            "exact_rzz_type_features_allowed": True,
            "oracle_fingerprint_allowed": True,
            "teacher_channels_allowed": True,
            "baseline_fingerprint_families": base_stack["separability"].get("fingerprint_families", {}),
            "active_fingerprint_families": active_stack["separability"].get("fingerprint_families", {}),
        },
        "PHYS3_learner_visible": {
            "allowed_inputs": ["shot_bits", "probe_basis_metadata", "visible_edge_schedule"],
            "forbidden_inputs": ["exact_ptm_entries", "exact_teacher_channel", "oracle_mechanism_labels", "PHYS2_oracle_fingerprint_features"],
            "feature_provenance_manifest_schema": active_mixed["feature_provenance_manifest"].get("schema"),
        },
    }


def _aggregate(records: list[dict[str, object]], key: str) -> dict[str, object]:
    return {"schema": f"scope_static_s2d7_{key}_aggregate_v1", "runs": {str(record["name"]): record[key] for record in records}}


def _aggregate_nested(records: list[dict[str, object]], parent: str, key: str) -> dict[str, object]:
    return {"schema": f"scope_static_s2d7_{key}_aggregate_v1", "runs": {str(record["name"]): record[parent][key] for record in records}}


def _compact_phys2(metrics: dict[str, object]) -> dict[str, object]:
    return {
        "ari": metrics.get("ari"),
        "nmi": metrics.get("nmi"),
        "active_clusters": metrics.get("active_clusters"),
        "separability_gate": metrics.get("separability_gate"),
        "feature_shape": metrics.get("feature_shape"),
        "fingerprint_families": metrics.get("fingerprint_families"),
    }


def _method_by_name(rows: list[dict[str, object]], name: str) -> dict[str, object]:
    for row in rows:
        if row.get("method") == name:
            return row
    return {}


def _enabled_runs(cfg: dict[str, object]) -> list[dict[str, object]]:
    raw = cfg.get("runs", DEFAULT_RUNS)
    if not isinstance(raw, list):
        raise ValueError("s2d7_rzz_active_probe_design.runs must be a list")
    return [dict(item) for item in raw if isinstance(item, dict) and bool(item.get("enabled", True))]


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {"runs": DEFAULT_RUNS}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D.7 config must be a mapping")
    section = data.get("s2d7_rzz_active_probe_design", {})
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise ValueError("s2d7_rzz_active_probe_design config must be a mapping")
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
    parser = argparse.ArgumentParser(description="Run S2D.7 RZZ active probe design.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-runs", type=int, default=None)
    args = parser.parse_args(argv)
    result = run_s2d7_rzz_active_probe_design(args.config, output_dir=args.output_dir, max_runs=args.max_runs)
    print(
        "S2D.7 RZZ active probe design complete\n"
        f"  runs={result['run_order']}\n"
        f"  output={result['output_dir']}\n"
        f"  summary={result['summary']}"
    )


if __name__ == "__main__":
    main()
