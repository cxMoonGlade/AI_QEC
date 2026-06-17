from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import yaml

from scope_static.experiments.qec_noise_catalog.config import load_s2d_physical_config, output_root_from_config
from scope_static.numerics import NUMERICAL_ZERO
from scope_static.mechanism_observability import rzz_family_metrics
from scope_static.mechanism_observability import (
    build_rzz_minimal_intervention_features,
    evaluate_rzz_minimal_intervention_methods,
)
from scope_static.mechanism_observability import (
    FeatureBlock,
    audit_labels_schema,
    evaluate_ceiling_feature_blocks,
    features_schema,
    grouped_fold_audit,
    leakage_guardrail_audit,
)
from scope_static.mechanism_observability import RZZ_FAMILY, build_targeted_v3_features, evaluate_targeted_v3_methods
from scope_static.catalog_pipeline import run_catalog_pipeline, pipeline_stage_results


DEFAULT_RUNS = [
    {
        "name": "phys9_setA",
        "profile": "phys9_chain",
        "mechanism_set": "set_A",
        "purpose": "regression sanity profile before minimal intervention primary runs",
    },
    {
        "name": "phys9_multicircuit_setB_balanced",
        "profile": "phys9_multicircuit_setB_balanced",
        "mechanism_set": "set_B",
        "purpose": "balanced set_B minimal RZZ intervention target",
    },
    {
        "name": "phys9_multicircuit_setC_balanced",
        "profile": "phys9_multicircuit_setC_balanced",
        "mechanism_set": "set_C",
        "purpose": "balanced set_C minimal RZZ intervention target",
    },
]
PRIMARY_RUNS = {"phys9_multicircuit_setB_balanced", "phys9_multicircuit_setC_balanced"}


def run_s2d8d_rzz_minimal_intervention(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    max_runs: int | None = None,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    cfg = _load_config(config_path)
    root = output_root_from_config(physical_cfg)
    default_output = root / "S2D.8_RZZ_dynamical_probe_design" / "S2D.8d_RZZ_minimal_intervention_probe"
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", default_output)))
    output.mkdir(parents=True, exist_ok=True)
    runs = _enabled_runs(cfg)
    if max_runs is not None:
        runs = runs[: int(max_runs)]

    records = [_run_one(output, physical_cfg, cfg, run_cfg) for run_cfg in runs]
    result = {
        "schema": "scope_static_s2d8d_rzz_minimal_intervention_v1",
        "stage": "S2D.8d_RZZ_minimal_intervention_probe",
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
    base_cfg = {**merged, "probe_set": str(cfg.get("baseline_probe_set", "base"))}
    intervention_cfg = {**merged, "probe_set": str(cfg.get("intervention_probe_set", "rzz_minimal_intervention"))}

    base_stack = _run_phys_stack(run_dir / "base_probe", base_cfg, cfg)
    intervention_stack = _run_phys_stack(run_dir / "rzz_minimal_intervention_probe", intervention_cfg, cfg)

    base_records, base_observations, base_probe_names, base_hidden, base_label_names = _load_pipeline_data(base_stack)
    intervention_records, intervention_observations, intervention_probe_names, hidden, label_names = _load_pipeline_data(intervention_stack)
    if base_label_names != label_names or len(base_records) != len(intervention_records):
        raise ValueError("S2D.8d probe stacks must produce the same mechanism label inventory")

    base_targeted = _targeted_from_stack(base_stack, base_records, base_observations, base_probe_names, base_hidden, base_label_names)
    base_labels = base_targeted["labels_by_method"]
    intervention_targeted = _targeted_from_stack(
        intervention_stack,
        intervention_records,
        intervention_observations,
        intervention_probe_names,
        hidden,
        label_names,
    )
    intervention_labels = intervention_targeted["labels_by_method"]
    intervention_local_labels = _comparison_labels(intervention_stack["local"])
    intervention = evaluate_rzz_minimal_intervention_methods(
        intervention_records,
        intervention_observations,
        intervention_probe_names,
        hidden,
        label_names,
        comparison_labels={
            "minimal_intervention_probe_only_v3c": intervention_labels["v3c_physical_local_inverse_probability_v3_typed"],
            "direct_Salpha": intervention_local_labels["direct_S_alpha_assignment"],
            "oracle_fingerprint_upper_bound": intervention_local_labels["oracle_fingerprint_upper_bound"],
        },
        bootstrap_replicates=int(cfg.get("bootstrap_replicates", 16)),
        seed=int(intervention_cfg.get("seed", 0)),
    )
    combined_labels = _combined_labels(base_targeted, intervention)
    combined_rzz = rzz_family_metrics(combined_labels, hidden, label_names)
    method_rows = _combined_method_rows(base_targeted, intervention, combined_rzz)
    ceiling_bundle = _grouped_ceiling_bundle(
        run_name=str(run_cfg["name"]),
        records=base_records,
        base_records=base_records,
        base_observations=base_observations,
        base_probe_names=base_probe_names,
        intervention_records=intervention_records,
        intervention_observations=intervention_observations,
        intervention_probe_names=intervention_probe_names,
        label_names=label_names,
        cfg=cfg,
        source_root=run_dir,
    )
    decision = _run_decision(method_rows, combined_rzz, ceiling_bundle)
    record = {
        "name": str(run_cfg["name"]),
        "purpose": str(run_cfg.get("purpose", "")),
        "profile": str(merged.get("profile")),
        "mechanism_set": str(merged.get("mechanism_set")),
        "num_qubits": int(intervention_stack["teacher"].get("num_qubits", intervention_cfg.get("num_qubits", 0))),
        "shots": int(intervention_cfg.get("shots", 0)),
        "baseline_probe_set": str(base_cfg.get("probe_set")),
        "intervention_probe_set": str(intervention_cfg.get("probe_set")),
        "decision": decision,
        "teacher": {
            "mechanism_counts": intervention_stack["teacher"].get("mechanism_counts", {}),
            "num_circuit_batches": intervention_stack["teacher"].get("num_circuit_batches", 1),
            "balanced_min_instances_per_mechanism": intervention_stack["teacher"].get("balanced_min_instances_per_mechanism"),
        },
        "PHYS2": {
            "baseline": _compact_phys2(base_stack["separability"]),
            "minimal_intervention": _compact_phys2(intervention_stack["separability"]),
            "audit_only_upper_bound": True,
        },
        "PHYS3": {str(row["method"]): row for row in method_rows},
        "method_rows": method_rows,
        "combined_rzz_family_metrics": combined_rzz,
        "minimal_intervention": intervention,
        "intervention_schema": intervention["intervention_schema"],
        "mechanism_response_table": intervention["mechanism_response_table"],
        "twirl_response_metrics": intervention["twirl_response_metrics"],
        "basis_response_metrics": intervention["basis_response_metrics"],
        "echo_response_metrics": intervention["echo_response_metrics"],
        "feature_provenance_manifest": intervention["feature_provenance_manifest"],
        "grouped_ceiling": ceiling_bundle,
    }
    _write_run_artifacts(run_dir, record)
    return record


def _run_phys_stack(run_dir: Path, cfg: dict[str, object], s2d8_cfg: dict[str, object]) -> dict[str, object]:
    pipeline = run_catalog_pipeline(
        cfg,
        output_dir=run_dir,
        bootstrap_replicates=int(s2d8_cfg.get("bootstrap_replicates", 16)),
        random_baseline_trials=int(s2d8_cfg.get("random_baseline_trials", 64)),
        run_local_inverse="always",
    )
    return pipeline_stage_results(pipeline)


def _load_pipeline_data(stack: dict[str, object]) -> tuple[list[dict[str, object]], np.ndarray, list[str], torch.Tensor, list[str]]:
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


def _grouped_ceiling_bundle(
    *,
    run_name: str,
    records: list[dict[str, object]],
    base_records: list[dict[str, object]],
    base_observations: np.ndarray,
    base_probe_names: list[str],
    intervention_records: list[dict[str, object]],
    intervention_observations: np.ndarray,
    intervention_probe_names: list[str],
    label_names: list[str],
    cfg: dict[str, object],
    source_root: Path,
) -> dict[str, object]:
    base_hidden, base_label_names = _encode_labels([str(record["oracle_label"]) for record in base_records])
    base_bundle = build_targeted_v3_features(
        base_records,
        base_observations,
        base_probe_names,
        num_clusters=len(base_label_names),
    )
    intervention_bundle = build_rzz_minimal_intervention_features(
        intervention_records,
        intervention_observations,
        intervention_probe_names,
        num_clusters=len(label_names),
    )
    mask = np.asarray([str(record["oracle_label"]) in set(RZZ_FAMILY) for record in records], dtype=bool)
    rzz_records = [dict(record) for record, keep in zip(records, mask.tolist()) if keep]
    labels = [str(record["oracle_label"]) for record in rzz_records]
    groups = [int(record.get("circuit_id", 0)) for record in rzz_records]
    feature_blocks = _ceiling_feature_blocks(base_bundle, intervention_bundle, mask)
    feature_schema = features_schema(feature_blocks, source_root=str(source_root))
    labels_schema = audit_labels_schema(labels, groups, rzz_records)
    fold_audit = grouped_fold_audit(groups) if len(set(groups)) >= 2 else _single_group_fold_audit(groups)
    leakage = leakage_guardrail_audit(feature_blocks, labels_schema, fold_audit)
    if not bool(leakage["passed"]):
        raise RuntimeError(f"S2D.8d leakage guardrail failed for {run_name}: {leakage['checks']}")
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
        primary_block="v3c_plus_active_all",
        scrambled_control_block="v3c_plus_scrambled_active_all",
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


def _ceiling_feature_blocks(base_bundle: dict[str, object], intervention_bundle, mask: np.ndarray) -> dict[str, FeatureBlock]:
    v3c = _rows(base_bundle.feature_spaces["physical_local_inverse_probability_v3_typed"], mask)
    v3c_names = [f"baseline_v3c_{idx}" for idx in range(v3c.shape[1])]
    real, real_names = _strip_v3c(
        intervention_bundle.feature_spaces["minimal_intervention_all"],
        intervention_bundle.feature_names["minimal_intervention_all"],
    )
    scrambled, scrambled_names = _strip_v3c(
        intervention_bundle.feature_spaces["scrambled_minimal_intervention_control"],
        intervention_bundle.feature_names["scrambled_minimal_intervention_control"],
    )
    real = _rows(real, mask)
    scrambled = _rows(scrambled, mask)
    real_names = [f"s2d8d_{name}" for name in real_names]
    scrambled_names = [f"s2d8d_{name}" for name in scrambled_names]
    return {
        "baseline_v3c_visible": FeatureBlock("baseline_v3c_visible", v3c, v3c_names, ["base_probe:v3c"], explanatory=True),
        "active_all": FeatureBlock("active_all", real, real_names, ["s2d8d_minimal_intervention"], explanatory=True),
        "scrambled_active_all": FeatureBlock("scrambled_active_all", scrambled, scrambled_names, ["s2d8d_scrambled_intervention"], control=True),
        "v3c_plus_active_all": FeatureBlock(
            "v3c_plus_active_all",
            _finite(np.concatenate([v3c, real], axis=1)),
            [*v3c_names, *real_names],
            ["base_probe:v3c", "s2d8d_minimal_intervention"],
            primary=True,
        ),
        "v3c_plus_scrambled_active_all": FeatureBlock(
            "v3c_plus_scrambled_active_all",
            _finite(np.concatenate([v3c, scrambled], axis=1)),
            [*v3c_names, *scrambled_names],
            ["base_probe:v3c", "s2d8d_scrambled_intervention"],
            control=True,
        ),
        "active_residualized_against_v3c": FeatureBlock(
            "active_residualized_against_v3c",
            real,
            real_names,
            ["s2d8d_minimal_intervention"],
            residualize_against=v3c,
            residualize_feature_names=v3c_names,
            explanatory=True,
        ),
        "scrambled_active_residualized_against_v3c": FeatureBlock(
            "scrambled_active_residualized_against_v3c",
            scrambled,
            scrambled_names,
            ["s2d8d_scrambled_intervention"],
            residualize_against=v3c,
            residualize_feature_names=v3c_names,
            control=True,
            explanatory=True,
        ),
    }


def _combined_labels(base_targeted: dict[str, object], intervention: dict[str, object]) -> dict[str, list[int]]:
    base = base_targeted["labels_by_method"]
    intervention_labels = intervention["labels_by_method"]
    return {
        "baseline_v3c": [int(value) for value in base["v3c_physical_local_inverse_probability_v3_typed"]],
        "twirl_intervention_features": [int(value) for value in intervention_labels["twirl_intervention_features"]],
        "basis_intervention_features": [int(value) for value in intervention_labels["basis_intervention_features"]],
        "echo_sign_intervention_features": [int(value) for value in intervention_labels["echo_sign_intervention_features"]],
        "minimal_intervention_all": [int(value) for value in intervention_labels["minimal_intervention_all"]],
        "scrambled_minimal_intervention_control": [int(value) for value in intervention_labels["scrambled_minimal_intervention_control"]],
        "direct_Salpha": [int(value) for value in intervention_labels["direct_Salpha"]],
        "oracle_fingerprint_upper_bound": [int(value) for value in intervention_labels["oracle_fingerprint_upper_bound"]],
    }


def _combined_method_rows(base_targeted: dict[str, object], intervention: dict[str, object], combined_rzz: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    base_map = {str(row["method"]): row for row in base_targeted["methods"]}
    baseline = dict(base_map["v3c_physical_local_inverse_probability_v3_typed"])
    baseline["method"] = "baseline_v3c"
    baseline["probe_role"] = "baseline_base_probe"
    rows.append(_with_rzz_metrics(baseline, combined_rzz))
    for row in intervention["methods"]:
        current = dict(row)
        current["probe_role"] = "S2D.8d_minimal_intervention"
        rows.append(_with_rzz_metrics(current, combined_rzz))
    order = [
        "baseline_v3c",
        "minimal_intervention_probe_only_v3c",
        "twirl_intervention_features",
        "basis_intervention_features",
        "echo_sign_intervention_features",
        "minimal_intervention_all",
        "scrambled_minimal_intervention_control",
        "direct_Salpha",
        "oracle_fingerprint_upper_bound",
    ]
    index = {name: idx for idx, name in enumerate(order)}
    return sorted(rows, key=lambda item: index.get(str(item["method"]), 10_000))


def _with_rzz_metrics(row: dict[str, object], combined_rzz: dict[str, object]) -> dict[str, object]:
    method = str(row["method"])
    metrics = combined_rzz.get("methods", {}).get(method, {}) if isinstance(combined_rzz.get("methods"), dict) else {}
    return {**row, "rzz_family_metrics": metrics}


def _run_decision(method_rows: list[dict[str, object]], combined_rzz: dict[str, object], ceiling_bundle: dict[str, object]) -> str:
    methods = {str(row["method"]): row for row in method_rows}
    baseline = methods.get("baseline_v3c", {})
    real = methods.get("minimal_intervention_all", {})
    scrambled = methods.get("scrambled_minimal_intervention_control", {})
    direct = methods.get("direct_Salpha", {})
    if (
        float(baseline.get("ari", 0.0)) >= 0.99
        and float(real.get("ari", 0.0)) >= 0.99
        and float(real.get("nmi", 0.0)) >= 0.99
        and _rzz_error(combined_rzz, "minimal_intervention_all") <= _rzz_error(combined_rzz, "baseline_v3c")
    ):
        return "regression_pass"
    global_ok = float(real.get("ari", 0.0)) >= 0.80 and float(real.get("nmi", 0.0)) >= 0.80
    rzz_improved = _rzz_error(combined_rzz, "minimal_intervention_all") < _rzz_error(combined_rzz, "baseline_v3c")
    ceiling_passed = bool(ceiling_bundle.get("verdict", {}).get("passed", False))
    if global_ok and rzz_improved and _beats(real, scrambled) and _beats(real, direct) and ceiling_passed:
        return "success"
    if rzz_improved or ceiling_passed:
        return "partial_observability_signal"
    return "failure"


def _rzz_error(combined_rzz: dict[str, object], method: str) -> int:
    metrics = combined_rzz.get("methods", {}).get(method, {}) if isinstance(combined_rzz.get("methods"), dict) else {}
    keys = ["M8_M9_merge_count", "M8_M10_merge_count", "M8_M12_merge_count", "M8_split_count"]
    return int(sum(int(metrics.get(key, 0)) for key in keys))


def _beats(left: dict[str, object], right: dict[str, object]) -> bool:
    return float(left.get("ari", 0.0)) > float(right.get("ari", 0.0)) and float(left.get("nmi", 0.0)) > float(right.get("nmi", 0.0))


def _summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if record["name"] in PRIMARY_RUNS]
    return {
        "num_runs": len(records),
        "num_primary_balanced_runs": len(primary),
        "success": sum(1 for record in records if record["decision"] == "success"),
        "regression_pass": sum(1 for record in records if record["decision"] == "regression_pass"),
        "partial_observability_signal": sum(1 for record in records if record["decision"] == "partial_observability_signal"),
        "failure": sum(1 for record in records if record["decision"] == "failure"),
        "primary_balanced_success": all(record["decision"] == "success" for record in primary) if primary else False,
    }


def _phase_summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if record["name"] in PRIMARY_RUNS]
    primary_success = bool(primary) and all(record["decision"] == "success" for record in primary)
    primary_failed = bool(primary) and all(record["decision"] == "failure" for record in primary)
    primary_partial = bool(primary) and any(record["decision"] == "partial_observability_signal" for record in primary)
    controls_ok = bool(primary) and all(record["minimal_intervention"]["scrambled_intervention_control"].get("real_beats_scrambled") for record in primary)
    ceiling_ok = bool(primary) and all(record["grouped_ceiling"]["verdict"].get("passed") for record in primary)
    if primary_success:
        label = "minimal_intervention_positive"
        conclusion = "Minimal RZZ intervention probes expose learner-visible RZZ-family signal on balanced primary runs."
        next_step = "freeze S2D.8d positive and diagnose remaining pair-specific errors"
    elif primary_partial:
        label = "minimal_intervention_partial"
        conclusion = "Minimal RZZ intervention probes expose condition-specific or incomplete RZZ-family signal."
        next_step = "inspect pairwise response tables before adding heavier tomography-like probes"
    elif primary_failed and not controls_ok and not ceiling_ok:
        label = "minimal_intervention_negative"
        conclusion = "Minimal RZZ intervention probes do not beat controls and do not expose a grouped transferable RZZ-family ceiling."
        next_step = "S2D.8e stronger benchmarking/tomography-like local channel probes"
    else:
        label = "minimal_intervention_not_frozen"
        conclusion = "S2D.8d requires primary balanced decisions plus control and grouped-ceiling interpretation."
        next_step = None
    return {
        "schema": "scope_static_s2d8d_phase_summary_v1",
        "stage": "S2D.8d_RZZ_minimal_intervention_probe",
        "phase_label": label,
        "main_conclusion": conclusion,
        "control_requirement": "real minimal intervention must beat scrambled intervention control",
        "grouped_ceiling_requirement": "primary grouped ceiling must pass for full success",
        "next_recommended_step": next_step,
    }


def format_s2d8d_summary(result: dict[str, object]) -> str:
    lines = [
        "# S2D.8d RZZ Minimal Intervention Probe",
        "",
        "| run | decision | baseline v3c | twirl | basis | echo/sign | intervention all | scrambled | grouped ceiling | RZZ error base/all |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |",
    ]
    for record in result["records"]:
        methods = {str(row["method"]): row for row in record["method_rows"]}
        baseline = methods["baseline_v3c"]
        twirl = methods["twirl_intervention_features"]
        basis = methods["basis_intervention_features"]
        echo = methods["echo_sign_intervention_features"]
        all_features = methods["minimal_intervention_all"]
        scrambled = methods["scrambled_minimal_intervention_control"]
        ceiling = record["grouped_ceiling"]["verdict"]
        rzz = record["combined_rzz_family_metrics"]
        lines.append(
            f"| {record['name']} | {record['decision']} | "
            f"{float(baseline['ari']):.4f}/{float(baseline['nmi']):.4f} | "
            f"{float(twirl['ari']):.4f}/{float(twirl['nmi']):.4f} | "
            f"{float(basis['ari']):.4f}/{float(basis['nmi']):.4f} | "
            f"{float(echo['ari']):.4f}/{float(echo['nmi']):.4f} | "
            f"{float(all_features['ari']):.4f}/{float(all_features['nmi']):.4f} | "
            f"{float(scrambled['ari']):.4f}/{float(scrambled['nmi']):.4f} | "
            f"{ceiling.get('label')} | {_rzz_error(rzz, 'baseline_v3c')}/{_rzz_error(rzz, 'minimal_intervention_all')} |"
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


def _write_run_artifacts(run_dir: Path, record: dict[str, object]) -> None:
    (run_dir / "metrics.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    (run_dir / "summary.md").write_text(format_s2d8d_summary({"records": [record]}))
    (run_dir / "intervention_schema.json").write_text(json.dumps(record["intervention_schema"], indent=2, sort_keys=True) + "\n")
    (run_dir / "mechanism_response_table.json").write_text(json.dumps(record["mechanism_response_table"], indent=2, sort_keys=True) + "\n")
    (run_dir / "twirl_response_metrics.json").write_text(json.dumps(record["twirl_response_metrics"], indent=2, sort_keys=True) + "\n")
    (run_dir / "basis_response_metrics.json").write_text(json.dumps(record["basis_response_metrics"], indent=2, sort_keys=True) + "\n")
    (run_dir / "echo_response_metrics.json").write_text(json.dumps(record["echo_response_metrics"], indent=2, sort_keys=True) + "\n")
    _write_ceiling_artifacts(run_dir, [record])


def _write_artifacts(output: Path, result: dict[str, object]) -> None:
    records = result["records"]
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_s2d8d_summary(result))
    (output / "intervention_schema.json").write_text(json.dumps(_aggregate(records, "intervention_schema"), indent=2, sort_keys=True) + "\n")
    (output / "mechanism_response_table.json").write_text(json.dumps(_aggregate(records, "mechanism_response_table"), indent=2, sort_keys=True) + "\n")
    (output / "twirl_response_metrics.json").write_text(json.dumps(_aggregate(records, "twirl_response_metrics"), indent=2, sort_keys=True) + "\n")
    (output / "basis_response_metrics.json").write_text(json.dumps(_aggregate(records, "basis_response_metrics"), indent=2, sort_keys=True) + "\n")
    (output / "echo_response_metrics.json").write_text(json.dumps(_aggregate(records, "echo_response_metrics"), indent=2, sort_keys=True) + "\n")
    (output / "phase_summary.json").write_text(json.dumps(result["phase_summary"], indent=2, sort_keys=True) + "\n")
    _write_ceiling_artifacts(output, records)


def _write_ceiling_artifacts(output: Path, records: list[dict[str, object]]) -> None:
    (output / "grouped_fold_predictions.json").write_text(
        json.dumps(_aggregate_nested(records, "grouped_ceiling", "ceiling", "grouped_fold_predictions"), indent=2, sort_keys=True) + "\n"
    )
    (output / "feature_block_results.json").write_text(
        json.dumps(_aggregate_nested(records, "grouped_ceiling", "ceiling", "feature_block_results"), indent=2, sort_keys=True) + "\n"
    )
    (output / "controls.json").write_text(json.dumps(_aggregate_nested(records, "grouped_ceiling", "ceiling", "controls"), indent=2, sort_keys=True) + "\n")
    (output / "leakage_guardrail_audit.json").write_text(json.dumps(_aggregate_nested(records, "grouped_ceiling", "leakage_guardrail_audit"), indent=2, sort_keys=True) + "\n")
    (output / "residualized_active_attribution.json").write_text(
        json.dumps(_aggregate_nested(records, "grouped_ceiling", "ceiling", "residualized_active_attribution"), indent=2, sort_keys=True) + "\n"
    )


def _aggregate(records: list[dict[str, object]], key: str) -> dict[str, object]:
    return {"schema": f"scope_static_s2d8d_{key}_aggregate_v1", "runs": {str(record["name"]): record[key] for record in records}}


def _aggregate_nested(records: list[dict[str, object]], *keys: str) -> dict[str, object]:
    out = {}
    for record in records:
        value: object = record
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, {})
            else:
                value = {}
        out[str(record["name"])] = value
    return {"schema": f"scope_static_s2d8d_{'_'.join(keys)}_aggregate_v1", "runs": out}


def _compact_phys2(metrics: dict[str, object]) -> dict[str, object]:
    return {
        "ari": metrics.get("ari"),
        "nmi": metrics.get("nmi"),
        "active_clusters": metrics.get("active_clusters"),
        "separability_gate": metrics.get("separability_gate"),
        "feature_shape": metrics.get("feature_shape"),
        "fingerprint_families": metrics.get("fingerprint_families"),
    }


def _comparison_labels(local: object) -> dict[str, list[int]]:
    return {str(item["comparison"]): [int(value) for value in item["labels"]] for item in local["comparisons"]}  # type: ignore[index]


def _strip_v3c(features: np.ndarray, names: list[str]) -> tuple[np.ndarray, list[str]]:
    keep = [idx for idx, name in enumerate(names) if not str(name).startswith("v3c_")]
    return np.asarray(features, dtype=np.float64)[:, keep], [str(names[idx]) for idx in keep]


def _rows(features: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return _finite(np.asarray(features, dtype=np.float64)[np.asarray(mask, dtype=bool)])


def _finite(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=NUMERICAL_ZERO, posinf=NUMERICAL_ZERO, neginf=-NUMERICAL_ZERO)


def _single_group_fold_audit(groups: list[int]) -> dict[str, object]:
    return {
        "schema": "scope_static_s2d8d_grouped_fold_audit_v1",
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
        "schema": "scope_static_s2d8d_grouped_ceiling_v1",
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


def _enabled_runs(cfg: dict[str, object]) -> list[dict[str, object]]:
    raw = cfg.get("runs", DEFAULT_RUNS)
    if not isinstance(raw, list):
        raise ValueError("s2d8d_rzz_minimal_intervention.runs must be a list")
    return [dict(item) for item in raw if isinstance(item, dict) and bool(item.get("enabled", True))]


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {"runs": DEFAULT_RUNS}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D.8d config must be a mapping")
    section = data.get("s2d8d_rzz_minimal_intervention", {})
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise ValueError("s2d8d_rzz_minimal_intervention config must be a mapping")
    result = dict(section)
    result.setdefault("runs", DEFAULT_RUNS)
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S2D.8d RZZ minimal intervention probe design.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-runs", type=int, default=None)
    args = parser.parse_args(argv)
    result = run_s2d8d_rzz_minimal_intervention(args.config, output_dir=args.output_dir, max_runs=args.max_runs)
    print(
        "S2D.8d RZZ minimal intervention complete\n"
        f"  runs={result['run_order']}\n"
        f"  output={result['output_dir']}\n"
        f"  summary={result['summary']}"
    )


if __name__ == "__main__":
    main()
