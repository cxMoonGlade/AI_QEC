from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.protocols import TEACHER_VALIDATION_STAGE, LEARNER_VALIDATION_STAGE
from scope_static.teacher.observation_surface import (
    _contract_passed,
    _coverage,
    _load_mechanism_records,
    _load_observations,
    _local_record,
    _mechanism_sort_key,
    _normalize_contract_variant,
    _weighted_metrics,
    slot_only_leakage_control,
    visible_input_identifiability_audit,
)
from scope_static.learner.quality import ChannelVector, channel_vector
from scope_static.mechanism_observability import classification_metrics


def run_sampled_observation_separability_audit(
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
    """PHYC2: teacher self-distinguishment only.

    Learner-visible grouped predictions belong to PHYC3. Keeping PHYC2 free of
    learner grouped predictions prevents PHYC3 from accidentally consuming a
    teacher-self artifact as no-leakage learner evidence.
    """

    variant = _normalize_contract_variant(contract_variant)
    teacher = Path(teacher_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")
    coverage = _teacher_self_coverage(records, contract_variant=variant)
    teacher_self = teacher_self_distinguishment_audit(records)

    if not coverage["contract_evaluable"]:
        result = {
            "schema": "scope_static_phyc2_sampled_observation_separability_v1",
            "stage": "PHYC2_sampled_observation_separability",
            "public_layer": TEACHER_VALIDATION_STAGE.metadata(
                artifact_stage="PHYC2_sampled_observation_separability",
                substage="teacher_self_distinguishment",
            ),
            "contract_variant": variant,
            "teacher_dir": str(teacher),
            "output_dir": str(output),
            "contract": _contract(
                contract_variant=variant,
                min_balanced_accuracy=min_balanced_accuracy,
                min_min_class_recall=min_min_class_recall,
                min_scrambled_control_gap=min_scrambled_control_gap,
                min_prevalence_weighted_accuracy=min_prevalence_weighted_accuracy,
                min_rare_class_recall=min_rare_class_recall,
                rare_class_quantile=rare_class_quantile,
            ),
            "coverage": coverage,
            "teacher_self_distinguishment": teacher_self,
            "contract_passed": False,
            "decision": "insufficient_teacher_self_coverage",
            "reason": coverage["reason"],
            "phyc2_emits_learner_grouped_predictions": False,
            "learner_recovery_stage": "PHYC3_no_leakage_learner_recovery",
        }
        _write_outputs(output, result)
        return result

    teacher_primary = dict(teacher_self.get("overall", {}))
    teacher_weighted = _weighted_metrics(teacher_primary, rare_class_quantile=float(rare_class_quantile))
    passed = bool(teacher_self.get("contract_passed", False))
    result = {
        "schema": "scope_static_phyc2_sampled_observation_separability_v1",
        "stage": "PHYC2_sampled_observation_separability",
        "public_layer": TEACHER_VALIDATION_STAGE.metadata(
            artifact_stage="PHYC2_sampled_observation_separability",
            substage="teacher_self_distinguishment",
        ),
        "contract_variant": variant,
        "teacher_dir": str(teacher),
        "output_dir": str(output),
        "contract": _contract(
            contract_variant=variant,
            min_balanced_accuracy=min_balanced_accuracy,
            min_min_class_recall=min_min_class_recall,
            min_scrambled_control_gap=min_scrambled_control_gap,
            min_prevalence_weighted_accuracy=min_prevalence_weighted_accuracy,
            min_rare_class_recall=min_rare_class_recall,
            rare_class_quantile=rare_class_quantile,
        ),
        "coverage": coverage,
        "teacher_self_distinguishment": teacher_self,
        "claim_boundary": (
            "Layer 2 is teacher self-distinguishment only. Layer 2 may use teacher "
            "internal mechanism evidence for this self-test, but it does not "
            "emit learner-visible grouped predictions for Layer 3."
        ),
        "contract_passed": bool(passed),
        "decision": "teacher_self_distinguishes_all_mechanisms" if passed else "teacher_self_distinguishment_failed",
        "primary_feature_block": "teacher_self_mechanism_signature",
        "primary_head": "teacher_self_mechanism_signature_then_channel_prototype",
        "balanced_accuracy": float(teacher_primary.get("balanced_accuracy", 0.0)),
        "min_class_recall": float(teacher_primary.get("min_class_recall", 0.0)),
        "macro_F1": float(teacher_primary.get("macro_F1", 0.0)),
        "adjusted_rand_index": float(teacher_primary.get("adjusted_rand_index", 0.0)),
        "normalized_mutual_info": float(teacher_primary.get("normalized_mutual_info", 0.0)),
        "prevalence_weighted_accuracy": float(teacher_weighted["prevalence_weighted_accuracy"]),
        "rare_class_recall_min": float(teacher_weighted["rare_class_recall_min"]),
        "rare_class_recall_mean": float(teacher_weighted["rare_class_recall_mean"]),
        "rare_class_names": teacher_weighted["rare_class_names"],
        "class_names": sorted({str(record.get("oracle_label", "")) for record in records}, key=_mechanism_sort_key),
        "teacher_self_grouped_predictions": teacher_self.get("grouped_fold_predictions", []),
        "phyc2_emits_learner_grouped_predictions": False,
        "learner_recovery_stage": "PHYC3_no_leakage_learner_recovery",
        "learner_recovery_layer": LEARNER_VALIDATION_STAGE.public_name,
    }
    _write_outputs(output, result)
    return result


def teacher_self_distinguishment_audit(records: list[dict[str, object]]) -> dict[str, object]:
    labels = [str(record.get("oracle_label", "")) for record in records]
    groups = [int(record.get("circuit_id", 0)) for record in records]
    class_names = sorted(set(labels), key=_mechanism_sort_key)
    if len(set(groups)) < 2 or len(class_names) < 2:
        overall = classification_metrics([], [], class_names)
        return {
            "schema": "scope_static_phyc2_teacher_self_distinguishment_v1",
            "contract_passed": False,
            "decision": "insufficient_teacher_self_distinguishment_coverage",
            "model": "TeacherNearestChannelPrototype",
            "overall": overall,
            "supervised_grouped_ceiling": {"overall": overall, "grouped_fold_predictions": []},
            "grouped_fold_predictions": [],
        }
    true_all: list[str] = []
    pred_all: list[str] = []
    folds = []
    for fold_idx, test_group in enumerate(sorted(set(groups))):
        train_records = [record for record in records if int(record.get("circuit_id", 0)) != int(test_group)]
        test_records = [record for record in records if int(record.get("circuit_id", 0)) == int(test_group)]
        prototypes = _teacher_channel_prototypes(train_records)
        signature_labels = _teacher_mechanism_signature_labels(train_records)
        true_labels = [str(record.get("oracle_label", "")) for record in test_records]
        predicted_labels = [_predict_teacher_self_label(record, signature_labels, prototypes, class_names) for record in test_records]
        true_all.extend(true_labels)
        pred_all.extend(predicted_labels)
        folds.append(
            {
                "fold": int(fold_idx),
                "test_circuit_id": int(test_group),
                "true_labels": true_labels,
                "predicted_labels": predicted_labels,
                "prediction_source": "teacher_self_mechanism_signature_then_channel_vector",
                "model": "TeacherMechanismSignature+NearestChannelPrototype",
            }
        )
    overall = classification_metrics(true_all, pred_all, class_names)
    passed = (
        float(overall.get("balanced_accuracy", 0.0)) >= 1.0
        and float(overall.get("min_class_recall", 0.0)) >= 1.0
        and float(overall.get("adjusted_rand_index", 0.0)) >= 1.0
        and float(overall.get("normalized_mutual_info", 0.0)) >= 1.0
    )
    return {
        "schema": "scope_static_phyc2_teacher_self_distinguishment_v1",
        "contract_passed": bool(passed),
        "decision": "teacher_self_distinguishes_all_mechanisms" if passed else "teacher_self_distinguishment_failed",
        "model": "TeacherMechanismSignature+NearestChannelPrototype",
        "teacher_internal_inputs": ["mechanism_name", "mechanism_channel", "mechanism_parameters", "readout_assignment_matrix"],
        "uses_sampled_observation_bits": False,
        "uses_oracle_labels_for_supervised_self_test": True,
        "overall": overall,
        "supervised_grouped_ceiling": {
            "primary_feature_block": "teacher_self_mechanism_signature",
            "primary_head": "teacher_self_mechanism_signature_then_channel_prototype",
            "overall": overall,
            "grouped_fold_predictions": folds,
        },
        "grouped_fold_predictions": folds,
    }


def _teacher_channel_prototypes(records: list[dict[str, object]]) -> dict[str, ChannelVector]:
    grouped: dict[str, list[ChannelVector]] = {}
    for record in records:
        label = str(record.get("oracle_label", ""))
        grouped.setdefault(label, []).append(channel_vector(record))
    prototypes: dict[str, ChannelVector] = {}
    for label, vectors in grouped.items():
        by_family: dict[str, list[ChannelVector]] = {}
        for vector in vectors:
            by_family.setdefault(vector.family, []).append(vector)
        family, local = max(by_family.items(), key=lambda item: len(item[1]))
        matrix = np.stack([item.vector for item in local], axis=0)
        prototypes[label] = ChannelVector(
            family=family,
            vector=np.nan_to_num(np.mean(matrix, axis=0), nan=0.0, posinf=0.0, neginf=0.0),
            representation=local[0].representation,
            mechanism_id=label,
        )
    return prototypes


def _teacher_mechanism_signature_labels(records: list[dict[str, object]]) -> dict[tuple[object, ...], str]:
    out: dict[tuple[object, ...], str] = {}
    for record in records:
        signature = _teacher_mechanism_signature(record)
        label = str(record.get("oracle_label", ""))
        existing = out.get(signature)
        if existing is None or existing == label:
            out[signature] = label
    return out


def _teacher_mechanism_signature(record: dict[str, object]) -> tuple[object, ...]:
    params = dict(record.get("parameters", {}))
    return (
        str(record.get("name", "")),
        int(record.get("num_qubits", 1)),
        str(record.get("instruction", "")),
        tuple(sorted(str(key) for key in params.keys())),
        channel_vector(record).family,
    )


def _predict_teacher_self_label(
    record: dict[str, object],
    signature_labels: dict[tuple[object, ...], str],
    prototypes: dict[str, ChannelVector],
    class_names: list[str],
) -> str:
    signature_label = signature_labels.get(_teacher_mechanism_signature(record))
    if signature_label is not None:
        return signature_label
    current = channel_vector(record)
    best_label = class_names[0] if class_names else ""
    best_distance = float("inf")
    for label in class_names:
        distance = _teacher_channel_distance(current, prototypes.get(label))
        if distance < best_distance:
            best_distance = distance
            best_label = label
    return best_label


def _teacher_channel_distance(left: ChannelVector, right: ChannelVector | None) -> float:
    if right is None or left.family != right.family or left.vector.shape != right.vector.shape:
        return float("inf")
    scale = float(np.sqrt(max(1, left.vector.size)))
    return float(np.linalg.norm(left.vector - right.vector) / scale)


def format_sampled_observation_separability_summary(result: dict[str, object]) -> str:
    diagnostic = result.get("sampled_observation_learner_diagnostic", {})
    if not isinstance(diagnostic, dict):
        diagnostic = {}
    lines = [
        "# Layer 2 teacher self-audit",
        "",
        f"- Primary role: `{dict(result.get('contract', {})).get('primary_role', TEACHER_VALIDATION_STAGE.public_name) if isinstance(result.get('contract', {}), dict) else TEACHER_VALIDATION_STAGE.public_name}`",
        f"- Contract variant: `{result.get('contract_variant', 'balanced')}`",
        f"- Decision: `{result.get('decision')}`",
        f"- Contract passed: `{str(bool(result.get('contract_passed'))).lower()}`",
        f"- Teacher self balanced accuracy: `{float(result.get('balanced_accuracy', 0.0)):.4f}`",
        f"- Teacher self ARI: `{float(result.get('adjusted_rand_index', 0.0)):.4f}`",
        f"- Teacher self NMI: `{float(result.get('normalized_mutual_info', 0.0)):.4f}`",
        f"- Teacher self min class recall: `{float(result.get('min_class_recall', 0.0)):.4f}`",
        "",
        "## Coverage",
        "",
    ]
    coverage = result.get("coverage", {})
    if isinstance(coverage, dict):
        for key in ("num_records", "num_classes", "num_groups", "num_probes", "num_shots", "num_qubits", "reason"):
            lines.append(f"- {key}: `{coverage.get(key)}`")
    if diagnostic:
        lines.extend(
            [
                "",
                "## Sampled-Observation Learner Diagnostic",
                "",
                "- Role: `diagnostic input for Layer 3; not the Layer 2 teacher-self gate`",
                f"- Diagnostic passed: `{str(bool(diagnostic.get('contract_passed', False))).lower()}`",
                f"- Balanced accuracy: `{float(diagnostic.get('balanced_accuracy', 0.0)):.4f}`",
                f"- ARI: `{float(diagnostic.get('adjusted_rand_index', 0.0)):.4f}`",
                f"- NMI: `{float(diagnostic.get('normalized_mutual_info', 0.0)):.4f}`",
                f"- Prevalence-weighted accuracy: `{float(diagnostic.get('prevalence_weighted_accuracy', 0.0)):.4f}`",
                f"- Min class recall: `{float(diagnostic.get('min_class_recall', 0.0)):.4f}`",
                f"- Rare-class min recall: `{float(diagnostic.get('rare_class_recall_min', 0.0)):.4f}`",
                f"- Real minus within-branch scrambled BA: `{float(diagnostic.get('real_minus_within_branch_scrambled_balanced_accuracy', 0.0)):.4f}`",
            ]
        )
    slot_only = result.get("slot_only_leakage_control", {})
    if isinstance(slot_only, dict):
        lines.extend(
            [
                "",
                "## Slot-Only Leakage Control",
                "",
                f"- Balanced accuracy: `{float(slot_only.get('balanced_accuracy', 0.0)):.4f}`",
                f"- Leakage suspected: `{str(bool(slot_only.get('leakage_suspected', False))).lower()}`",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _contract(
    *,
    contract_variant: str,
    min_balanced_accuracy: float,
    min_min_class_recall: float,
    min_scrambled_control_gap: float,
    min_prevalence_weighted_accuracy: float,
    min_rare_class_recall: float,
    rare_class_quantile: float,
) -> dict[str, object]:
    variant = _normalize_contract_variant(contract_variant)
    requirements: dict[str, object] = {
        "num_groups_ge": 2,
        "each_class_in_at_least_two_groups": True,
        "teacher_self_balanced_accuracy_eq": 1.0,
        "teacher_self_min_class_recall_eq": 1.0,
        "teacher_self_ARI_eq": 1.0,
        "teacher_self_NMI_eq": 1.0,
    }
    if variant == "balanced":
        requirements["equal_class_support"] = True
    else:
        requirements["equal_class_support"] = False
    return {
        "name": f"teacher_self_distinguishes_mechanisms_{variant}",
        "variant": variant,
        "primary_role": TEACHER_VALIDATION_STAGE.public_name,
        "teacher_internal_inputs": ["mechanism_channel", "mechanism_parameters", "readout_assignment_matrix"],
        "evaluator_only_inputs": ["oracle_label", "mechanism_id"],
        "requirements": requirements,
        "learner_recovery_moved_to": "PHYC3_no_leakage_learner_recovery",
        "learner_recovery_layer": LEARNER_VALIDATION_STAGE.public_name,
    }


def _teacher_self_coverage(records: list[dict[str, object]], *, contract_variant: str) -> dict[str, object]:
    variant = _normalize_contract_variant(contract_variant)
    labels = [str(record.get("oracle_label", "")) for record in records]
    groups = [int(record.get("circuit_id", 0)) for record in records]
    by_label: dict[str, set[int]] = {}
    for label, group in zip(labels, groups):
        by_label.setdefault(label, set()).add(group)
    class_support = {label: int(labels.count(label)) for label in sorted(set(labels), key=_mechanism_sort_key)}
    support_values = list(class_support.values())
    min_support = min(support_values) if support_values else 0
    max_support = max(support_values) if support_values else 0
    balanced_support = bool(support_values) and min_support == max_support
    missing = sorted([label for label, local_groups in by_label.items() if len(local_groups) < 2], key=_mechanism_sort_key)
    num_groups = len(set(groups))
    reason = "ok"
    evaluable = True
    if num_groups < 2:
        evaluable = False
        reason = "need at least two circuit_id groups for teacher self-distinguishment"
    elif missing:
        evaluable = False
        reason = "each mechanism class must appear in at least two circuit_id groups"
    elif variant == "balanced" and not balanced_support:
        evaluable = False
        reason = "PHYC2-balanced requires equal record support for every mechanism class"
    return {
        "num_records": int(len(records)),
        "num_classes": int(len(class_support)),
        "num_groups": int(num_groups),
        "num_probes": None,
        "num_shots": None,
        "num_qubits": None,
        "class_support": class_support,
        "class_group_counts": {label: int(len(groups_for_label)) for label, groups_for_label in sorted(by_label.items(), key=lambda item: _mechanism_sort_key(item[0]))},
        "min_class_support": int(min_support),
        "max_class_support": int(max_support),
        "balanced_class_support": bool(balanced_support),
        "classes_missing_two_groups": missing,
        "contract_evaluable": bool(evaluable),
        "reason": reason,
    }


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    (output / "metrics.json").write_text(json.dumps(_json_safe(result), indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_sampled_observation_separability_summary(result))


def _json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return _json_safe(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value
