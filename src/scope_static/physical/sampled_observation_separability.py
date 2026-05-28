from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .local_pauli_lindblad import build_local_pauli_lindblad_observability
from .typed_spam_gate_invariant import build_typed_spam_gate_features, evaluate_typed_spam_gate_learner, grouped_linear_head


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
    """PHYC2: learner-visible separability from sampled observations.

    This is intentionally different from the legacy PHYS2 oracle-fingerprint
    ceiling: exact PTMs, exact channel fingerprints, and oracle mechanism
    labels are evaluator-only. The contract passes only when the sampled
    observation tensor and visible probe/instruction metadata support grouped
    mechanism classification.
    """

    variant = _normalize_contract_variant(contract_variant)
    teacher = Path(teacher_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")
    observations, probe_names = _load_observations(teacher / "observations.npz")
    enabled_mechanisms = sorted({str(record.get("oracle_label", "")) for record in records}, key=_mechanism_sort_key)
    coverage = _coverage(records, observations, probe_names, contract_variant=variant)

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
            "contract_passed": False,
            "decision": "insufficient_sampled_observation_coverage",
            "reason": coverage["reason"],
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
        contract_variant=variant,
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
        "contract_passed": bool(passed),
        "decision": _decision(contract_variant=variant, passed=bool(passed)),
        "primary_feature_block": "typed_gate_readout_prep_invariant_learner",
        "primary_head": "typed_linear_head",
        "balanced_accuracy": balanced_accuracy,
        "min_class_recall": min_class_recall,
        "macro_F1": float(primary.get("macro_F1", 0.0)),
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
    lines = [
        "# PHYC2 Sampled Observation Separability",
        "",
        f"- Contract variant: `{result.get('contract_variant', 'balanced')}`",
        f"- Decision: `{result.get('decision')}`",
        f"- Contract passed: `{str(bool(result.get('contract_passed'))).lower()}`",
        f"- Balanced accuracy: `{float(result.get('balanced_accuracy', 0.0)):.4f}`",
        f"- Prevalence-weighted accuracy: `{float(result.get('prevalence_weighted_accuracy', 0.0)):.4f}`",
        f"- Min class recall: `{float(result.get('min_class_recall', 0.0)):.4f}`",
        f"- Rare-class min recall: `{float(result.get('rare_class_recall_min', 0.0)):.4f}`",
        f"- Real minus within-branch scrambled BA: `{float(result.get('real_minus_within_branch_scrambled_balanced_accuracy', 0.0)):.4f}`",
        "",
        "## Coverage",
        "",
    ]
    coverage = result.get("coverage", {})
    if isinstance(coverage, dict):
        for key in ("num_records", "num_classes", "num_groups", "num_probes", "num_shots", "num_qubits", "reason"):
            lines.append(f"- {key}: `{coverage.get(key)}`")
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
        "num_probes_ge": 2,
        "each_class_in_at_least_two_groups": True,
        "real_minus_within_branch_scrambled_balanced_accuracy_ge": float(min_scrambled_control_gap),
    }
    if variant == "balanced":
        requirements.update(
            {
                "equal_class_support": True,
                "balanced_accuracy_ge": float(min_balanced_accuracy),
                "min_class_recall_ge": float(min_min_class_recall),
            }
        )
    else:
        requirements.update(
            {
                "equal_class_support": False,
                "prevalence_weighted_accuracy_ge": float(min_prevalence_weighted_accuracy),
                "macro_balanced_accuracy_ge": float(min_balanced_accuracy),
                "rare_class_recall_ge": float(min_rare_class_recall),
                "rare_class_quantile": float(rare_class_quantile),
            }
        )
    return {
        "name": f"sampled_observations_are_learner_separable_{variant}",
        "variant": variant,
        "learner_visible_inputs": ["observations.npz", "probe_names", "visible_instruction_type", "visible_qubits"],
        "evaluator_only_inputs": ["oracle_label", "mechanism_id", "exact_ptm", "exact_channel_fingerprint"],
        "requirements": requirements,
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
