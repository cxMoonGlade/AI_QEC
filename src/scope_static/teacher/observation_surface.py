from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.mechanism_observability import classification_metrics, grouped_linear_head


def visible_input_identifiability_audit(
    records: list[dict[str, object]],
    probe_names: list[str],
    observations: np.ndarray,
) -> dict[str, object]:
    """Detect identical learner-visible inputs with different evaluator labels."""

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
    conflicting_labels = sorted(
        {label for indices in conflicts.values() for label in (labels[idx] for idx in indices)},
        key=_mechanism_sort_key,
    )
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


def slot_only_leakage_control(
    records: list[dict[str, object]],
    probe_names: list[str],
    observations: np.ndarray,
    *,
    seed: int = 0,
) -> dict[str, object]:
    """Grouped classifier using only slot/layout metadata, never sampled bits."""

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


def coverage_audit(
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


def weighted_metrics(primary: dict[str, object], *, rare_class_quantile: float) -> dict[str, object]:
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


def learner_contract_passed(
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


def load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text())
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def load_observations(path: Path) -> tuple[np.ndarray, list[str]]:
    data = np.load(path)
    return np.asarray(data["observations"]), [str(value) for value in data["probe_names"].tolist()]


def local_record(bundle: object) -> dict[str, object]:
    return {
        "generator_coordinate_estimates": bundle.generator_coordinate_estimates,
        "ptm_block_reconstruction": bundle.ptm_block_reconstruction,
        "response_jacobian_json": bundle.response_jacobian_json,
    }


def _coverage(
    records: list[dict[str, object]],
    observations: np.ndarray,
    probe_names: list[str],
    *,
    contract_variant: str,
) -> dict[str, object]:
    return coverage_audit(records, observations, probe_names, contract_variant=contract_variant)


def _weighted_metrics(primary: dict[str, object], *, rare_class_quantile: float) -> dict[str, object]:
    return weighted_metrics(primary, rare_class_quantile=rare_class_quantile)


def _contract_passed(**kwargs: object) -> bool:
    return learner_contract_passed(**kwargs)  # type: ignore[arg-type]


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    return load_mechanism_records(path)


def _load_observations(path: Path) -> tuple[np.ndarray, list[str]]:
    return load_observations(path)


def _local_record(bundle: object) -> dict[str, object]:
    return local_record(bundle)


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
            *_multi_hot(slots, num_qubits),
            *_multi_hot(physical, num_qubits),
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


def _mechanism_sort_key(name: str) -> tuple[int, str]:
    if str(name).startswith("M") and str(name)[1:].isdigit():
        return (int(str(name)[1:]), str(name))
    return (10_000, str(name))
