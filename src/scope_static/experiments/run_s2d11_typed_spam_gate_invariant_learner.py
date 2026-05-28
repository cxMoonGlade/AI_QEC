from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.experiments.run_s2d_physical_teacher import generate_physical_teacher_dataset
from scope_static.experiments.s2d_config import load_s2d_physical_config, output_root_from_config
from scope_static.physical.local_pauli_lindblad import build_local_pauli_lindblad_observability
from scope_static.physical.mechanism_catalog import IMPLEMENTED_MECHANISM_IDS
from scope_static.physical.typed_spam_gate_invariant import (
    TypedSpamGateBundle,
    build_typed_spam_gate_features,
    evaluate_typed_spam_gate_learner,
)


DEFAULT_RUNS = [
    {
        "name": "phys9_multicircuit_setD_balanced",
        "profile": "phys9_multicircuit_setD_balanced",
        "mechanism_set": "set_D",
        "purpose": "primary typed gate/readout/prep invariant learner verdict",
    }
]
SECONDARY_ALLM_RUN = {
    "name": "phys9_multicircuit_allM_balanced",
    "profile": "phys9_multicircuit_allM_balanced",
    "mechanism_set": list(IMPLEMENTED_MECHANISM_IDS),
    "purpose": "secondary M19/other-mechanism stress test only after primary set_D pass",
    "secondary_stress": True,
}
PRIMARY_RUN = "phys9_multicircuit_setD_balanced"
ARTIFACT_NAMES = (
    "typed_branch_feature_manifest",
    "typed_branch_feature_schema_physics_visible",
    "audit_labels_schema_oracle_only",
    "branch_assignment_audit",
    "branch_budget_audit",
    "grouped_fold_coverage_audit",
    "gate_process_feature_table",
    "readout_branch_feature_table",
    "prep_reset_branch_feature_table",
    "branch_ablation_metrics",
    "typed_metric_head_report",
    "pairwise_margin_report",
    "confusion_matrix_by_branch",
    "readout_mechanism_audit",
    "m5_readout_audit",
    "m5_overfragmentation_report",
    "prep_reset_audit",
    "m11_prep_reset_audit",
    "prep_reset_readout_confound_audit",
    "m11_readout_confound_audit",
    "single_qubit_invariant_reconstruction_audit",
    "gate_family_audit",
    "oracle_upper_bound_metrics",
    "scrambled_branch_control_audit",
    "controls",
    "leakage_guardrail_audit",
    "grouped_fold_predictions",
    "m11_prep_observability_preflight",
    "m11_prep_feature_snr",
    "m11_vs_m4_preflight_margin",
    "prep_reconstruction_assumption_audit",
    "m13_confidence_audit",
    "m19_confidence_audit",
)


def run_s2d11_typed_spam_gate_invariant_learner(
    config_path: str | Path | None = None,
    *,
    output_dir: str | Path | None = None,
    max_runs: int | None = None,
) -> dict[str, object]:
    physical_cfg = load_s2d_physical_config(config_path)
    cfg = _load_config(config_path)
    root = output_root_from_config(physical_cfg)
    default_output = root / "S2D.11_typed_SPAM_gate_invariant_learner"
    output = Path(output_dir) if output_dir is not None else Path(str(cfg.get("output_dir", default_output)))
    output.mkdir(parents=True, exist_ok=True)

    runs = _enabled_runs(cfg)
    if max_runs is not None:
        runs = runs[: int(max_runs)]
    records = [_run_one(output, physical_cfg, cfg, run_cfg, role="primary" if str(run_cfg["name"]) == PRIMARY_RUN else "context") for run_cfg in runs]

    primary_pass = any(record["name"] == PRIMARY_RUN and record["decision"] == "success" for record in records)
    secondary_record = None
    if primary_pass and bool(cfg.get("run_secondary_allM_if_primary_passes", True)):
        secondary_record = _run_one(output, physical_cfg, cfg, dict(cfg.get("secondary_allM_run", SECONDARY_ALLM_RUN)), role="secondary_stress")
        records.append(secondary_record)

    result = {
        "schema": "scope_static_s2d11_typed_spam_gate_invariant_learner_v1",
        "stage": "S2D.11_typed_SPAM_gate_invariant_learner",
        "preferred_precise_name": "S2D.11_typed_gate_readout_prep_invariant_learner",
        "spam_branch_clarification": "SPAM is implemented as two explicit typed branches: readout_branch and prep_reset_branch.",
        "output_dir": str(output),
        "run_order": [record["name"] for record in records],
        "records": records,
        "summary": _summary(records),
        "phase_summary": _phase_summary(records),
        "secondary_record_written": secondary_record is not None,
    }
    _write_artifacts(output, result)
    return result


def _run_one(output: Path, physical_cfg: dict[str, object], cfg: dict[str, object], run_cfg: dict[str, object], *, role: str) -> dict[str, object]:
    run_name = str(run_cfg["name"])
    run_dir = output / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    merged = dict(physical_cfg)
    merged.update({key: value for key, value in run_cfg.items() if key not in {"name", "purpose", "enabled", "secondary_stress"}})
    merged.update(dict(cfg.get("physical_overrides", {})))
    tomo_cfg = {**merged, "probe_set": str(cfg.get("tomography_probe_set", "rzz_local_tomography"))}
    teacher_dir = run_dir / "S2D_PHYS1_teacher"
    teacher = generate_physical_teacher_dataset(tomo_cfg, output_dir=teacher_dir, preflight_dir=run_dir / "S2D_PHYS0_preflight")
    records, observations, probe_names = _load_stack(teacher_dir)
    local = build_local_pauli_lindblad_observability(
        records,
        observations,
        probe_names,
        theta=float(tomo_cfg.get("theta", 0.18)),
        ridge=float(cfg.get("ridge", 1e-8)),
    )
    local_record = _local_record(local)
    enabled = sorted([str(key) for key in teacher.get("mechanism_counts", {}).keys()], key=_mechanism_sort_key)
    bundle = build_typed_spam_gate_features(
        records,
        observations,
        probe_names,
        local_record,
        enabled_mechanisms=enabled,
        seed=int(cfg.get("seed", 0)),
    )
    evaluation = evaluate_typed_spam_gate_learner(
        bundle,
        seed=int(cfg.get("seed", 0)),
        include_m13=bool(run_cfg.get("secondary_stress", False)),
        include_m19=bool(run_cfg.get("secondary_stress", False)),
    )
    decision = _run_decision(evaluation, bundle, role=role, enabled_mechanisms=enabled)
    record = {
        "name": run_name,
        "role": role,
        "purpose": str(run_cfg.get("purpose", "")),
        "profile": str(tomo_cfg.get("profile", "")),
        "mechanism_set": tomo_cfg.get("mechanism_set"),
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
        "enabled_mechanisms_from_visible_run_config": enabled,
        "supervised_grouped_ceiling": evaluation["supervised_grouped_ceiling"],
        "typed_heads": evaluation["typed_heads"],
        "unsupervised_clustering": evaluation["unsupervised_clustering"],
        "branch_ablations": evaluation["branch_ablations"],
        "controls": evaluation["controls"],
        "oracle_upper_bound": evaluation["oracle_upper_bound"],
        "primary_verdict": evaluation["primary_verdict"],
        "secondary_stress": evaluation["secondary_stress"],
        "typed_branch_feature_manifest": bundle.typed_branch_feature_manifest,
        "typed_branch_feature_schema_physics_visible": bundle.typed_branch_feature_schema_physics_visible,
        "audit_labels_schema_oracle_only": bundle.audit_labels_schema_oracle_only,
        "branch_assignment_audit": bundle.branch_assignment_audit,
        "branch_budget_audit": bundle.branch_budget_audit,
        "grouped_fold_coverage_audit": bundle.grouped_fold_coverage_audit,
        "gate_process_feature_table": bundle.gate_process_feature_table,
        "readout_branch_feature_table": bundle.readout_branch_feature_table,
        "prep_reset_branch_feature_table": bundle.prep_reset_branch_feature_table,
        "branch_ablation_metrics": evaluation["branch_ablation_metrics"],
        "typed_metric_head_report": evaluation["typed_metric_head_report"],
        "pairwise_margin_report": evaluation["pairwise_margin_report"],
        "confusion_matrix_by_branch": evaluation["confusion_matrix_by_branch"],
        "readout_mechanism_audit": evaluation["readout_mechanism_audit"],
        "m5_readout_audit": evaluation["m5_readout_audit"],
        "m5_overfragmentation_report": evaluation["m5_overfragmentation_report"],
        "prep_reset_audit": evaluation["m11_prep_reset_audit"],
        "m11_prep_reset_audit": evaluation["m11_prep_reset_audit"],
        "prep_reset_readout_confound_audit": evaluation["m11_readout_confound_audit"],
        "m11_readout_confound_audit": evaluation["m11_readout_confound_audit"],
        "single_qubit_invariant_reconstruction_audit": evaluation["single_qubit_invariant_reconstruction_audit"],
        "gate_family_audit": evaluation["gate_family_audit"],
        "oracle_upper_bound_metrics": evaluation["oracle_upper_bound_metrics"],
        "scrambled_branch_control_audit": evaluation["scrambled_branch_control_audit"],
        "leakage_guardrail_audit": bundle.leakage_guardrail_audit,
        "grouped_fold_predictions": evaluation["grouped_fold_predictions"],
        "m11_prep_observability_preflight": bundle.m11_prep_observability_preflight,
        "m11_prep_feature_snr": bundle.m11_prep_feature_snr,
        "m11_vs_m4_preflight_margin": bundle.m11_vs_m4_preflight_margin,
        "prep_reconstruction_assumption_audit": bundle.prep_reconstruction_assumption_audit,
        "m13_confidence_audit": evaluation["m13_confidence_audit"],
        "m19_confidence_audit": evaluation["m19_confidence_audit"],
    }
    _write_run_artifacts(run_dir, record)
    return record


def _run_decision(evaluation: dict[str, object], bundle: TypedSpamGateBundle, *, role: str, enabled_mechanisms: list[str]) -> str:
    success = bool(evaluation.get("run_success", {}).get("passed", False))
    preflight_relevant = bool({"M17", "M18"} & set(enabled_mechanisms))
    preflight_pass = bool(bundle.m11_prep_observability_preflight.get("passed", False)) if preflight_relevant else True
    if role == "secondary_stress":
        return "secondary_stress_pass" if success else "secondary_stress_diagnostic"
    if success and preflight_pass:
        return "success"
    checks = evaluation.get("run_success", {}).get("checks", {})
    gate_ok = bool(checks.get("gate_family_balanced_accuracy_ge_0_80", False))
    m5_ok = bool(checks.get("readout_split_fixed", checks.get("m5_split_fixed", False)))
    coverage_ok = bool(checks.get("grouped_fold_coverage_valid", False))
    scrambled_ok = bool(checks.get("beats_within_branch_scrambled_by_0_25", False))
    if preflight_relevant and not preflight_pass and gate_ok and m5_ok and coverage_ok and scrambled_ok:
        return "partial_gate_readout_validated_m11_observability_limited"
    if preflight_pass and not success:
        return "failure_typed_branch_or_prep_design"
    return "failure"


def _summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = [record for record in records if record["name"] == PRIMARY_RUN]
    return {
        "num_runs": int(len(records)),
        "primary_setD_success": bool(primary) and primary[0]["decision"] == "success",
        "primary_setD_partial_m11_observability_limited": bool(primary) and primary[0]["decision"] == "partial_gate_readout_validated_m11_observability_limited",
        "success": int(sum(1 for record in records if record["decision"] == "success")),
        "partial": int(sum(1 for record in records if str(record["decision"]).startswith("partial"))),
        "failure": int(sum(1 for record in records if str(record["decision"]).startswith("failure"))),
        "secondary_stress_runs": int(sum(1 for record in records if record["role"] == "secondary_stress")),
    }


def _phase_summary(records: list[dict[str, object]]) -> dict[str, object]:
    primary = next((record for record in records if record["name"] == PRIMARY_RUN), None)
    if not primary:
        label = "typed_gate_readout_prep_invariant_learner_not_frozen"
        conclusion = "S2D.11 primary set_D run is missing."
        next_step = "run phys9_multicircuit_setD_balanced"
    elif primary["decision"] == "success":
        label = "typed_gate_readout_prep_invariant_learner_positive"
        conclusion = "Typed gate/readout/prep branches pass set_D grouped ceiling with leakage-clean invariant features."
        next_step = "optionally run secondary M19 stress or freeze typed invariant learner"
    elif primary["decision"] == "partial_gate_readout_validated_m11_observability_limited":
        label = "typed_gate_readout_positive_m11_observability_limited"
        conclusion = "Gate/process and readout branches validate, but prep/reset observability is weak under the no-new-probe constraint."
        next_step = "defer prep/reset mechanisms to future prep-specific observability or probe expansion"
    else:
        label = "typed_gate_readout_prep_invariant_learner_negative"
        conclusion = "Typed branch structure did not beat required grouped controls or class-level criteria on set_D."
        next_step = "inspect branch feature observability before adding probes"
    return {
        "schema": "scope_static_s2d11_phase_summary_v1",
        "stage": "S2D.11_typed_SPAM_gate_invariant_learner",
        "preferred_precise_name": "S2D.11_typed_gate_readout_prep_invariant_learner",
        "phase_label": label,
        "main_conclusion": conclusion,
        "next_recommended_step": next_step,
        "no_new_probe_family": True,
        "no_transformer": True,
        "primary_setD_only": True,
        "m13_secondary_only": True,
    }


def format_s2d11_summary(result: dict[str, object]) -> str:
    lines = [
        "# S2D.11 Typed Gate/Readout/Prep Invariant Learner",
        "",
        "SPAM is implemented as two explicit typed branches: `readout_branch` and `prep_reset_branch`.",
        "",
        "| run | role | decision | bal acc | macro F1 | min recall | M5 split | M11 preflight | real-within gap | maha bal acc |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |",
    ]
    for record in result["records"]:
        primary = record["branch_ablation_metrics"].get("typed_gate_readout_prep_invariant_learner", {}).get("overall", {})
        maha = record["typed_metric_head_report"].get("typed_mahalanobis_prototype_head", {}).get("overall", {})
        controls = record["controls"]
        m5 = record["m5_overfragmentation_report"]
        preflight = record["m11_prep_observability_preflight"]
        lines.append(
            f"| {record['name']} | {record['role']} | {record['decision']} | "
            f"{_fmt(primary.get('balanced_accuracy'))} | "
            f"{_fmt(primary.get('macro_F1'))} | "
            f"{_fmt(primary.get('min_class_recall'))} | "
            f"{int(m5.get('M5_split_count', 0))} | "
            f"{bool(preflight.get('passed', False))} | "
            f"{_fmt(controls.get('real_minus_within_branch_scrambled_balanced_accuracy'))} | "
            f"{_fmt(maha.get('balanced_accuracy'))} |"
        )
    phase = result.get("phase_summary", {})
    lines.extend(["", "## Phase Conclusion", "", f"- Label: `{phase.get('phase_label')}`", f"- Conclusion: {phase.get('main_conclusion')}", f"- Next: `{phase.get('next_recommended_step')}`", ""])
    return "\n".join(lines)


def _write_artifacts(output: Path, result: dict[str, object]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_s2d11_summary(result))
    for artifact in ARTIFACT_NAMES:
        (output / f"{artifact}.json").write_text(json.dumps(_aggregate_artifact(result["records"], artifact), indent=2, sort_keys=True) + "\n")
    _write_predictions_csv(output / "grouped_fold_predictions.csv", result["records"])


def _write_run_artifacts(run_dir: Path, record: dict[str, object]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "metrics.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    (run_dir / "summary.md").write_text(format_s2d11_summary({"records": [record], "phase_summary": {}}))
    for artifact in ARTIFACT_NAMES:
        (run_dir / f"{artifact}.json").write_text(json.dumps(record.get(artifact, {}), indent=2, sort_keys=True) + "\n")
    _write_predictions_csv(run_dir / "grouped_fold_predictions.csv", [record])


def _write_predictions_csv(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["run", "feature_block", "fold", "test_circuit_id", "row_in_fold", "true_label", "predicted_label"])
        writer.writeheader()
        for record in records:
            predictions = record.get("grouped_fold_predictions", {})
            if not isinstance(predictions, dict):
                continue
            for block_name, folds in predictions.items():
                if not isinstance(folds, list):
                    continue
                for fold in folds:
                    true = fold.get("true_labels", []) if isinstance(fold, dict) else []
                    pred = fold.get("predicted_labels", []) if isinstance(fold, dict) else []
                    for row_idx, (label, got) in enumerate(zip(true, pred)):
                        writer.writerow(
                            {
                                "run": record["name"],
                                "feature_block": block_name,
                                "fold": fold.get("fold", ""),
                                "test_circuit_id": fold.get("test_circuit_id", ""),
                                "row_in_fold": row_idx,
                                "true_label": label,
                                "predicted_label": got,
                            }
                        )


def _aggregate_artifact(records: list[dict[str, object]], artifact: str) -> dict[str, object]:
    return {"schema": f"scope_static_s2d11_{artifact}_aggregate_v1", "runs": {str(record["name"]): record.get(artifact, {}) for record in records}}


def _local_record(bundle: object) -> dict[str, object]:
    return {
        "generator_coordinate_estimates": bundle.generator_coordinate_estimates,
        "ptm_block_reconstruction": bundle.ptm_block_reconstruction,
        "response_jacobian_json": bundle.response_jacobian_json,
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
        raise ValueError("s2d11_typed_spam_gate_invariant_learner.runs must be a list")
    return [dict(item) for item in raw if isinstance(item, dict) and bool(item.get("enabled", True))]


def _load_config(config_path: str | Path | None) -> dict[str, object]:
    if config_path is None:
        return {"runs": DEFAULT_RUNS}
    data = yaml.safe_load(Path(config_path).read_text())
    if not isinstance(data, dict):
        raise ValueError("S2D.11 config must be a mapping")
    section = data.get("s2d11_typed_spam_gate_invariant_learner", {})
    if section is None:
        section = {}
    if not isinstance(section, dict):
        raise ValueError("s2d11_typed_spam_gate_invariant_learner config must be a mapping")
    result = dict(section)
    result.setdefault("runs", DEFAULT_RUNS)
    result.setdefault("secondary_allM_run", SECONDARY_ALLM_RUN)
    return result


def _mechanism_sort_key(name: str) -> tuple[int, str]:
    if str(name).startswith("M") and str(name)[1:].isdigit():
        return (int(str(name)[1:]), str(name))
    return (10_000, str(name))


def _fmt(value: object) -> str:
    if value is None:
        return "NA"
    try:
        current = float(value)
    except (TypeError, ValueError):
        return str(value)
    if not np.isfinite(current):
        return "inf"
    return f"{current:.4f}"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run S2D.11 typed gate/readout/prep invariant learner.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-runs", type=int, default=None)
    args = parser.parse_args(argv)
    result = run_s2d11_typed_spam_gate_invariant_learner(args.config, output_dir=args.output_dir, max_runs=args.max_runs)
    print(
        "S2D.11 typed gate/readout/prep invariant learner complete\n"
        f"  runs={result['run_order']}\n"
        f"  output={result['output_dir']}\n"
        f"  summary={result['summary']}"
    )


if __name__ == "__main__":
    main()
