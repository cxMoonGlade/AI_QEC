from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .local_pauli_lindblad import build_local_pauli_lindblad_observability
from .sampled_quantum_error_quality import ChannelVector, channel_vector
from .typed_spam_gate_invariant import build_typed_spam_gate_features, classification_metrics, evaluate_typed_spam_gate_learner, grouped_linear_head


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
            "PHYC2 is teacher self-distinguishment only. PHYC2 may use teacher "
            "internal mechanism evidence for this self-test, but it does not "
            "emit learner-visible grouped predictions for PHYC3."
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


def visible_input_identifiability_audit(
    records: list[dict[str, object]],
    probe_names: list[str],
    observations: np.ndarray,
) -> dict[str, object]:
    """Detect identical learner-visible inputs with different evaluator labels.

    Oracle labels are used only to audit whether the visible PHYC2 input surface
    can possibly support exact mechanism recovery. If two rows have the same
    instruction, slots, physical slots, probe slice, and remap bit, every
    sampled-observation feature derived by PHYC2 is identical for those rows.
    """

    labels = [str(record.get("oracle_label", "")) for record in records]
    class_names = sorted(set(labels), key=_mechanism_sort_key)
    by_signature: dict[tuple[object, ...], list[int]] = {}
    for idx, record in enumerate(records):
        by_signature.setdefault(_visible_input_signature(record, len(probe_names), observations), []).append(idx)
    conflicts = {
        signature: indices
        for signature, indices in by_signature.items()
        if len({labels[idx] for idx in indices}) > 1
    }
    conflict_rows = []
    for signature, indices in sorted(conflicts.items(), key=lambda item: (len(item[1]), str(item[0])), reverse=True):
        local_labels = [labels[idx] for idx in indices]
        conflict_rows.append(
            {
                "signature": _json_safe_signature(signature),
                "labels": sorted(set(local_labels), key=_mechanism_sort_key),
                "label_counts": {label: int(local_labels.count(label)) for label in sorted(set(local_labels), key=_mechanism_sort_key)},
                "record_count": int(len(indices)),
            }
        )

    ceiling_pred = _optimistic_visible_signature_predictions(records, labels, by_signature)
    ceiling = classification_metrics(labels, ceiling_pred, class_names)
    conflicting_labels = sorted({label for indices in conflicts.values() for label in (labels[idx] for idx in indices)}, key=_mechanism_sort_key)
    return {
        "schema": "scope_static_phyc2_visible_input_identifiability_audit_v1",
        "purpose": "Diagnostic ceiling for downstream sampled-observation learners; not the PHYC2 teacher self-distinguishment gate.",
        "uses_oracle_labels_for_evaluation_only": True,
        "learner_visible_signature_fields": [
            "circuit_id",
            "instruction",
            "qubits",
            "physical_qubits",
            "probe_indices",
            "local_observable_slot_remap",
        ],
        "num_records": int(len(records)),
        "num_visible_signatures": int(len(by_signature)),
        "conflicting_visible_signature_count": int(len(conflicts)),
        "conflicting_record_count": int(sum(len(indices) for indices in conflicts.values())),
        "conflicting_labels": conflicting_labels,
        "conflict_examples": conflict_rows[:20],
        "perfect_mechanism_recovery_possible_from_visible_inputs": len(conflicts) == 0,
        "optimistic_duplicate_signature_ceiling": {
            "interpretation": "Upper bound for deterministic no-leakage classifiers when identical visible signatures carry multiple labels.",
            "balanced_accuracy": float(ceiling.get("balanced_accuracy", 0.0)),
            "min_class_recall": float(ceiling.get("min_class_recall", 0.0)),
            "adjusted_rand_index": float(ceiling.get("adjusted_rand_index", 0.0)),
            "normalized_mutual_info": float(ceiling.get("normalized_mutual_info", 0.0)),
            "per_class_recall": ceiling.get("per_class_recall", {}),
        },
    }


def _visible_input_signature(record: dict[str, object], num_probes: int, observations: np.ndarray) -> tuple[object, ...]:
    probe_indices = tuple(
        int(value)
        for value in record.get("probe_indices", [])
        if 0 <= int(value) < int(num_probes)
    )
    if not probe_indices:
        probe_indices = tuple(range(int(num_probes)))
    num_qubits = int(observations.shape[2]) if observations.ndim == 3 else _max_qubit_index([record]) + 1
    num_qubits = max(1, num_qubits)
    return (
        int(record.get("circuit_id", 0)),
        str(record.get("instruction", "")),
        tuple(int(value) for value in record.get("qubits", []) if 0 <= int(value) < num_qubits),
        tuple(int(value) for value in record.get("physical_qubits", []) if 0 <= int(value) < num_qubits),
        probe_indices,
        bool(record.get("local_observable_slot_remap", False)),
    )


def _optimistic_visible_signature_predictions(
    records: list[dict[str, object]],
    labels: list[str],
    by_signature: dict[tuple[object, ...], list[int]],
) -> list[str]:
    predictions = [""] * len(records)
    tie_counters: dict[tuple[str, ...], int] = {}
    for indices in by_signature.values():
        local_labels = [labels[idx] for idx in indices]
        unique = sorted(set(local_labels), key=_mechanism_sort_key)
        if len(unique) == 1:
            chosen = unique[0]
        else:
            counts = {label: local_labels.count(label) for label in unique}
            max_count = max(counts.values())
            tied = [label for label in unique if counts[label] == max_count]
            key = tuple(tied)
            offset = tie_counters.get(key, 0)
            chosen = tied[offset % len(tied)]
            tie_counters[key] = offset + 1
        for idx in indices:
            predictions[idx] = chosen
    return [prediction if prediction else labels[idx] for idx, prediction in enumerate(predictions)]


def _json_safe_signature(signature: tuple[object, ...]) -> list[object]:
    out = []
    for item in signature:
        if isinstance(item, tuple):
            out.append([int(value) if isinstance(value, (int, np.integer)) else value for value in item])
        elif isinstance(item, (bool, np.bool_)):
            out.append(bool(item))
        elif isinstance(item, (int, np.integer)):
            out.append(int(item))
        else:
            out.append(str(item))
    return out


def slot_only_leakage_control(
    records: list[dict[str, object]],
    probe_names: list[str],
    observations: np.ndarray,
    *,
    seed: int = 0,
) -> dict[str, object]:
    """Grouped classifier using only slot/layout metadata, never sampled bits.

    This is an adversarial leakage control for local-observable slot remapping:
    if this control classifies mechanisms well, the remap/layout metadata are
    carrying mechanism identity and PHYC2 separability is suspect.
    """

    labels = [str(record.get("oracle_label", "")) for record in records]
    groups = [int(record.get("circuit_id", 0)) for record in records]
    class_names = sorted(set(labels), key=_mechanism_sort_key)
    features, feature_names = _slot_only_feature_table(records, probe_names, observations)
    head = grouped_linear_head(features, labels, groups, class_names, seed=int(seed))
    overall = dict(head.get("overall", {}))
    leakage_threshold = max(0.20, 3.0 / max(1, len(class_names)))
    balanced_accuracy = float(overall.get("balanced_accuracy", 0.0))
    weighted = _weighted_metrics(overall, rare_class_quantile=0.25)
    return {
        "schema": "scope_static_phyc2_slot_only_leakage_control_v1",
        "control_name": "PHYC2.slot_only_leakage_control",
        "purpose": "Detect whether observation-slot/layout metadata alone encode mechanism identity.",
        "learner_visible_inputs": [
            "observation_slot",
            "physical_qubits",
            "probe_id_range",
            "slot_remap_metadata",
        ],
        "excluded_inputs": [
            "sampled_bits",
            "sampled_response_means",
            "pair_correlations",
            "local_inverse_features",
            "oracle_label",
            "mechanism_id",
        ],
        "model": head.get("model"),
        "feature_names": feature_names,
        "balanced_accuracy": balanced_accuracy,
        "min_class_recall": float(overall.get("min_class_recall", 0.0)),
        "prevalence_weighted_accuracy": float(weighted["prevalence_weighted_accuracy"]),
        "macro_F1": float(overall.get("macro_F1", 0.0)),
        "per_class_recall": overall.get("per_class_recall", {}),
        "support": overall.get("support", {}),
        "leakage_threshold_balanced_accuracy": float(leakage_threshold),
        "leakage_suspected": bool(balanced_accuracy > leakage_threshold),
        "interpretation": (
            "slot/layout metadata alone are predictive; inspect remap and physical layout before trusting PHYC2"
            if balanced_accuracy > leakage_threshold
            else "slot/layout metadata alone are low-information under grouped folds"
        ),
    }


def _slot_only_feature_table(
    records: list[dict[str, object]],
    probe_names: list[str],
    observations: np.ndarray,
) -> tuple[np.ndarray, list[str]]:
    num_qubits = int(observations.shape[2]) if observations.ndim == 3 else _max_qubit_index(records) + 1
    num_qubits = max(1, int(num_qubits))
    num_probes = max(1, len(probe_names))
    feature_names = [
        "slot_count",
        "slot_mean_norm",
        "slot_span_norm",
        "slot_min_norm",
        "slot_max_norm",
        "physical_count",
        "physical_mean_norm",
        "physical_span_norm",
        "physical_min_norm",
        "physical_max_norm",
        "probe_start_norm",
        "probe_end_norm",
        "probe_mean_norm",
        "probe_count_norm",
        "slot_remapped_record",
        *[f"observation_slot_{idx}" for idx in range(num_qubits)],
        *[f"physical_qubit_{idx}" for idx in range(num_qubits)],
    ]
    rows = []
    for record in records:
        slots = [int(value) for value in record.get("qubits", []) if 0 <= int(value) < num_qubits]
        physical = [int(value) for value in record.get("physical_qubits", []) if 0 <= int(value) < num_qubits]
        probe_indices = [int(value) for value in record.get("probe_indices", []) if 0 <= int(value) < num_probes]
        slot_one_hot = _multi_hot(slots, num_qubits)
        physical_one_hot = _multi_hot(physical, num_qubits)
        row = [
            float(len(slots)),
            _mean_norm(slots, num_qubits),
            _span_norm(slots, num_qubits),
            _min_norm(slots, num_qubits),
            _max_norm(slots, num_qubits),
            float(len(physical)),
            _mean_norm(physical, num_qubits),
            _span_norm(physical, num_qubits),
            _min_norm(physical, num_qubits),
            _max_norm(physical, num_qubits),
            _min_norm(probe_indices, num_probes),
            _max_norm(probe_indices, num_probes),
            _mean_norm(probe_indices, num_probes),
            float(len(probe_indices) / num_probes),
            float(bool(record.get("local_observable_slot_remap", False))),
            *slot_one_hot,
            *physical_one_hot,
        ]
        rows.append(row)
    return np.asarray(rows, dtype=np.float64), feature_names


def _multi_hot(indices: list[int], size: int) -> list[float]:
    out = np.zeros(int(size), dtype=np.float64)
    for idx in indices:
        if 0 <= int(idx) < int(size):
            out[int(idx)] = 1.0
    return out.tolist()


def _mean_norm(values: list[int], denominator: int) -> float:
    if not values:
        return 0.0
    return float(np.mean(values) / max(1, int(denominator) - 1))


def _span_norm(values: list[int], denominator: int) -> float:
    if len(values) < 2:
        return 0.0
    return float((max(values) - min(values)) / max(1, int(denominator) - 1))


def _min_norm(values: list[int], denominator: int) -> float:
    if not values:
        return 0.0
    return float(min(values) / max(1, int(denominator) - 1))


def _max_norm(values: list[int], denominator: int) -> float:
    if not values:
        return 0.0
    return float(max(values) / max(1, int(denominator) - 1))


def _max_qubit_index(records: list[dict[str, object]]) -> int:
    values = []
    for record in records:
        values.extend(int(value) for value in record.get("qubits", []))
        values.extend(int(value) for value in record.get("physical_qubits", []))
    return max(values) if values else 0


def format_sampled_observation_separability_summary(result: dict[str, object]) -> str:
    diagnostic = result.get("sampled_observation_learner_diagnostic", {})
    if not isinstance(diagnostic, dict):
        diagnostic = {}
    lines = [
        "# PHYC2 Teacher Self-Distinguishment",
        "",
        f"- Primary role: `{dict(result.get('contract', {})).get('primary_role', 'PHYC2 teacher self-distinguishment') if isinstance(result.get('contract', {}), dict) else 'PHYC2 teacher self-distinguishment'}`",
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
                "- Role: `diagnostic input for PHYC3; not the PHYC2 teacher-self gate`",
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
        "primary_role": "PHYC2 teacher self-distinguishment",
        "teacher_internal_inputs": ["mechanism_channel", "mechanism_parameters", "readout_assignment_matrix"],
        "evaluator_only_inputs": ["oracle_label", "mechanism_id"],
        "requirements": requirements,
        "learner_recovery_moved_to": "PHYC3_no_leakage_learner_recovery",
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


def _coverage(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: list[str],
    *,
    contract_variant: str,
) -> dict[str, object]:
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
    num_probes = len(probe_names)
    reason = "ok"
    evaluable = True
    if num_groups < 2:
        evaluable = False
        reason = "need at least two circuit_id groups for grouped learner evaluation"
    elif num_probes < 2:
        evaluable = False
        reason = "need at least two probe settings for sampled-observation separability"
    elif missing:
        evaluable = False
        reason = "each mechanism class must appear in at least two circuit_id groups"
    elif variant == "balanced" and not balanced_support:
        evaluable = False
        reason = "PHYC2-balanced requires equal record support for every mechanism class"
    return {
        "num_records": int(len(records)),
        "num_classes": int(len(set(labels))),
        "num_groups": int(num_groups),
        "num_probes": int(num_probes),
        "num_shots": int(observations.shape[1]) if observations.ndim == 3 else 0,
        "num_qubits": int(observations.shape[2]) if observations.ndim == 3 else 0,
        "class_support": class_support,
        "class_support_min": int(min_support),
        "class_support_max": int(max_support),
        "class_recall_resolution": float(1.0 / min_support) if min_support > 0 else 0.0,
        "balanced_class_support": bool(balanced_support),
        "classes_missing_two_group_coverage": missing,
        "contract_evaluable": bool(evaluable),
        "reason": reason,
    }


def _weighted_metrics(primary: dict[str, object], *, rare_class_quantile: float) -> dict[str, object]:
    matrix = np.asarray(primary.get("confusion_matrix", []), dtype=np.float64)
    labels = [str(label) for label in primary.get("confusion_matrix_labels", [])]
    support = {str(key): int(value) for key, value in dict(primary.get("support", {})).items()}
    total = float(np.sum(matrix))
    correct = float(np.trace(matrix)) if matrix.ndim == 2 else 0.0
    prevalence_weighted_accuracy = correct / total if total > 0.0 else 0.0
    support_values = np.asarray([support.get(label, 0) for label in labels], dtype=np.float64)
    positive = support_values[support_values > 0]
    if positive.size:
        threshold = float(np.quantile(positive, min(max(float(rare_class_quantile), 0.0), 1.0)))
    else:
        threshold = 0.0
    rare = [label for label in labels if 0 < support.get(label, 0) <= threshold]
    if not rare and labels:
        min_support = min(support.get(label, 0) for label in labels)
        rare = [label for label in labels if support.get(label, 0) == min_support]
    recalls = dict(primary.get("per_class_recall", {}))
    rare_recalls = [float(recalls.get(label, 0.0)) for label in rare]
    return {
        "prevalence_weighted_accuracy": float(prevalence_weighted_accuracy),
        "rare_class_support_threshold": float(threshold),
        "rare_class_names": rare,
        "rare_class_recall_min": float(min(rare_recalls)) if rare_recalls else 0.0,
        "rare_class_recall_mean": float(np.mean(rare_recalls)) if rare_recalls else 0.0,
    }


def _contract_passed(
    *,
    contract_variant: str,
    coverage: dict[str, object],
    balanced_accuracy: float,
    min_class_recall: float,
    scrambled_gap: float,
    weighted_metrics: dict[str, object],
    min_balanced_accuracy: float,
    min_min_class_recall: float,
    min_scrambled_control_gap: float,
    min_prevalence_weighted_accuracy: float,
    min_rare_class_recall: float,
) -> bool:
    if scrambled_gap < min_scrambled_control_gap:
        return False
    if _normalize_contract_variant(contract_variant) == "balanced":
        return bool(coverage.get("balanced_class_support", False)) and balanced_accuracy >= min_balanced_accuracy and min_class_recall >= min_min_class_recall
    return (
        float(weighted_metrics.get("prevalence_weighted_accuracy", 0.0)) >= min_prevalence_weighted_accuracy
        and balanced_accuracy >= min_balanced_accuracy
        and float(weighted_metrics.get("rare_class_recall_min", 0.0)) >= min_rare_class_recall
    )


def _decision(*, contract_variant: str, passed: bool) -> str:
    variant = _normalize_contract_variant(contract_variant)
    if passed:
        return f"{variant}_sampled_observations_learner_separable"
    return f"{variant}_sampled_observations_not_learner_separable"


def _normalize_contract_variant(value: str) -> str:
    text = str(value).strip().lower().replace("-", "_")
    aliases = {
        "": "balanced",
        "balanced": "balanced",
        "phyc2_balanced": "balanced",
        "mechanism_separability": "balanced",
        "weighted": "weighted",
        "schedule_weighted": "weighted",
        "phyc2_weighted": "weighted",
        "prevalence_weighted": "weighted",
    }
    if text not in aliases:
        raise ValueError("contract_variant must be 'balanced' or 'weighted'")
    return aliases[text]


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text())
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def _load_observations(path: Path) -> tuple[np.ndarray, list[str]]:
    data = np.load(path)
    return np.asarray(data["observations"]), [str(value) for value in data["probe_names"].tolist()]


def _local_record(bundle: object) -> dict[str, object]:
    return {
        "generator_coordinate_estimates": bundle.generator_coordinate_estimates,
        "ptm_block_reconstruction": bundle.ptm_block_reconstruction,
        "response_jacobian_json": bundle.response_jacobian_json,
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


def _mechanism_sort_key(name: str) -> tuple[int, str]:
    if str(name).startswith("M") and str(name)[1:].isdigit():
        return (int(str(name)[1:]), str(name))
    return (10_000, str(name))
