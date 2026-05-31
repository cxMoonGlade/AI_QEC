from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.protocols import LEARNER_VALIDATION_STAGE
from scope_static.mechanism_observability import build_local_pauli_lindblad_observability
from scope_static.teacher.observation_surface import (
    _contract_passed,
    _coverage,
    _load_mechanism_records,
    _load_observations,
    _local_record,
    _mechanism_sort_key,
    _weighted_metrics,
    slot_only_leakage_control,
    visible_input_identifiability_audit,
)
from scope_static.mechanism_observability import build_typed_spam_gate_features, evaluate_typed_spam_gate_learner


STAGE_NAME = "PHYC3_no_leakage_learner_recovery"


def run_phyc3_no_leakage_learner_recovery(
    *,
    teacher_dir: str | Path,
    output_dir: str | Path,
    contract_variant: str = "balanced",
    theta: float = 0.18,
    ridge: float = 1e-8,
    seed: int = 0,
    min_balanced_accuracy: float = 0.80,
    min_min_class_recall: float = 0.50,
    min_scrambled_control_gap: float = 0.25,
    min_prevalence_weighted_accuracy: float = 0.90,
    min_rare_class_recall: float = 0.30,
    rare_class_quantile: float = 0.25,
) -> dict[str, object]:
    teacher = Path(teacher_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")
    observations, probe_names = _load_observations(teacher / "observations.npz")
    enabled_mechanisms = sorted({str(record.get("oracle_label", "")) for record in records}, key=_mechanism_sort_key)
    coverage = _coverage(records, observations, probe_names, contract_variant=contract_variant)
    identifiability = visible_input_identifiability_audit(records, probe_names, observations)
    if not coverage["contract_evaluable"]:
        result = {
            "schema": "scope_static_phyc3_no_leakage_learner_recovery_v1",
            "stage": STAGE_NAME,
            "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="old_surface_learner_recovery"),
            "teacher_dir": str(teacher),
            "output_dir": str(output),
            "contract_variant": str(contract_variant),
            "coverage": coverage,
            "visible_input_identifiability_audit": identifiability,
            "contract_passed": False,
            "decision": "insufficient_no_leakage_learner_coverage",
            "reason": coverage["reason"],
            "teacher_self_predictions": False,
            "teacher_self_predictions_allowed": False,
        }
        _write_outputs(output, result)
        return result

    local = build_local_pauli_lindblad_observability(records, observations, probe_names, theta=float(theta), ridge=float(ridge))
    bundle = build_typed_spam_gate_features(
        records,
        observations,
        probe_names,
        _local_record(local),
        enabled_mechanisms=enabled_mechanisms,
        seed=int(seed),
    )
    evaluation = evaluate_typed_spam_gate_learner(bundle, seed=int(seed), include_m13=True, include_m19=True)
    slot_only = slot_only_leakage_control(records, probe_names, observations, seed=int(seed))
    primary = evaluation["supervised_grouped_ceiling"]["overall"]
    controls = evaluation["controls"]
    balanced_accuracy = float(primary.get("balanced_accuracy", 0.0))
    min_class_recall = float(primary.get("min_class_recall", 0.0))
    scrambled_gap = float(controls.get("real_minus_within_branch_scrambled_balanced_accuracy", 0.0))
    weighted_metrics = _weighted_metrics(primary, rare_class_quantile=float(rare_class_quantile))
    passed = _contract_passed(
        contract_variant=contract_variant,
        coverage=coverage,
        balanced_accuracy=balanced_accuracy,
        min_class_recall=min_class_recall,
        scrambled_gap=scrambled_gap,
        weighted_metrics=weighted_metrics,
        min_balanced_accuracy=float(min_balanced_accuracy),
        min_min_class_recall=float(min_min_class_recall),
        min_scrambled_control_gap=float(min_scrambled_control_gap),
        min_prevalence_weighted_accuracy=float(min_prevalence_weighted_accuracy),
        min_rare_class_recall=float(min_rare_class_recall),
    )
    result = {
        "schema": "scope_static_phyc3_no_leakage_learner_recovery_v1",
        "stage": STAGE_NAME,
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="old_surface_learner_recovery"),
        "teacher_dir": str(teacher),
        "output_dir": str(output),
        "contract_variant": str(contract_variant),
        "contract": {
            "name": f"no_leakage_sampled_observation_learner_recovery_{contract_variant}",
            "primary_role": LEARNER_VALIDATION_STAGE.public_name,
            "teacher_self_predictions_allowed": False,
            "learner_visible_inputs_only": True,
            "oracle_labels_used_for_supervised_training_and_evaluation_only": True,
            "mechanism_balanced_accuracy_ge": float(min_balanced_accuracy),
            "mechanism_min_class_recall_ge": float(min_min_class_recall),
            "real_minus_within_branch_scrambled_balanced_accuracy_ge": float(min_scrambled_control_gap),
            "prevalence_weighted_accuracy_ge": float(min_prevalence_weighted_accuracy),
            "rare_class_recall_ge": float(min_rare_class_recall),
        },
        "claim_boundary": (
            "Layer 3 learner recovery owns grouped sampled-observation predictions. "
            "The feature matrix is learner-visible; oracle labels are supervision/evaluator fields, not features."
        ),
        "coverage": coverage,
        "visible_input_identifiability_audit": identifiability,
        "contract_passed": bool(passed),
        "decision": "no_leakage_learner_recovered_mechanisms" if passed else "no_leakage_learner_recovery_failed",
        "teacher_self_predictions": False,
        "teacher_self_predictions_allowed": False,
        "primary_feature_block": "typed_gate_readout_prep_invariant_learner",
        "primary_head": "typed_linear_head",
        "balanced_accuracy": balanced_accuracy,
        "min_class_recall": min_class_recall,
        "macro_F1": float(primary.get("macro_F1", 0.0)),
        "adjusted_rand_index": float(primary.get("adjusted_rand_index", 0.0)),
        "normalized_mutual_info": float(primary.get("normalized_mutual_info", 0.0)),
        "prevalence_weighted_accuracy": float(weighted_metrics["prevalence_weighted_accuracy"]),
        "rare_class_recall_min": float(weighted_metrics["rare_class_recall_min"]),
        "rare_class_recall_mean": float(weighted_metrics["rare_class_recall_mean"]),
        "rare_class_names": weighted_metrics["rare_class_names"],
        "real_minus_within_branch_scrambled_balanced_accuracy": scrambled_gap,
        "class_names": evaluation["class_names"],
        "supervised_grouped_ceiling": evaluation["supervised_grouped_ceiling"],
        "typed_heads": evaluation["typed_heads"],
        "controls": controls,
        "slot_only_leakage_control": slot_only,
        "grouped_fold_coverage_audit": bundle.grouped_fold_coverage_audit,
        "branch_assignment_audit": bundle.branch_assignment_audit,
        "leakage_guardrail_audit": bundle.leakage_guardrail_audit,
    }
    _write_outputs(output, result)
    return result


def format_phyc3_no_leakage_learner_recovery_summary(result: dict[str, object]) -> str:
    return "\n".join(
        [
            "# Layer 3: Learner Classification and Noise Generation",
            "",
            f"- Legacy alias: `{dict(result.get('public_layer', {})).get('legacy_alias', 'PHYC3')}`",
            f"- Decision: `{result.get('decision')}`",
            f"- Contract passed: `{str(bool(result.get('contract_passed'))).lower()}`",
            f"- Balanced accuracy: `{float(result.get('balanced_accuracy', 0.0)):.4f}`",
            f"- ARI: `{float(result.get('adjusted_rand_index', 0.0)):.4f}`",
            f"- NMI: `{float(result.get('normalized_mutual_info', 0.0)):.4f}`",
            f"- Min class recall: `{float(result.get('min_class_recall', 0.0)):.4f}`",
            f"- Teacher-self predictions allowed: `{str(bool(result.get('teacher_self_predictions_allowed', False))).lower()}`",
            "",
            "## Claim Boundary",
            "",
            str(result.get("claim_boundary", "")),
            "",
        ]
    )


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    (output / "metrics.json").write_text(json.dumps(_json_safe(result), indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_phyc3_no_leakage_learner_recovery_summary(result))


def _json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return _json_safe(list(value))
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value
