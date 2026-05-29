from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np

from .channels import MechanismSpec, mechanism_channel
from .layers import LAYER3_LEARNER
from ..metrics import adjusted_rand_index, normalized_mutual_info
from .ptm import ptm_from_kraus, ptm_from_unitary


@dataclass(frozen=True)
class ChannelVector:
    family: str
    vector: np.ndarray
    representation: str
    mechanism_id: str


def run_sampled_quantum_error_quality_audit(
    *,
    teacher_dir: str | Path,
    phyc2_dir: str | Path,
    output_dir: str | Path,
    min_mechanism_balanced_accuracy: float = 0.95,
    min_mechanism_min_recall: float = 0.95,
    max_mean_predicted_channel_distance: float = 0.02,
    max_worst_predicted_channel_distance: float = 0.005,
    min_nearest_wrong_channel_gap: float | None = None,
) -> dict[str, object]:
    """Layer 3 diagnostic: mechanism classification plus quantum-error quality.

    This audit consumes no-leakage learner grouped predictions from a Layer 3
    learner-recovery artifact. It rejects Layer 2 teacher-self predictions as
    learner evidence. For each held-out circuit group, it builds
    class-conditional channel/readout prototypes only from the training groups,
    then compares the predicted prototype against the evaluator-only oracle
    mechanism channel.
    """

    teacher = Path(teacher_dir)
    phyc2 = Path(phyc2_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")
    phyc2_metrics = json.loads((phyc2 / "metrics.json").read_text())
    prediction_source = _learner_prediction_source(phyc2_metrics)
    folds = prediction_source.get("grouped_fold_predictions", [])
    if not isinstance(folds, list) or not folds:
        result = _not_evaluable_result(teacher, phyc2, output, str(prediction_source.get("reason", "PHYC3 no-leakage learner predictions are missing")))
        result["prediction_source_audit"] = prediction_source
        _write_outputs(output, result)
        return result

    rows = []
    for fold in folds:
        if not isinstance(fold, dict):
            continue
        test_group = int(fold.get("test_circuit_id", fold.get("fold", -1)))
        true_labels = [str(item) for item in fold.get("true_labels", [])]
        predicted_labels = [str(item) for item in fold.get("predicted_labels", [])]
        test_records = _records_for_fold(records, test_group, true_labels)
        train_records = [record for record in records if int(record.get("circuit_id", 0)) != test_group]
        prototypes = _channel_prototypes(train_records)
        for row_idx, (record, true_label, predicted_label) in enumerate(zip(test_records, true_labels, predicted_labels)):
            true_channel = channel_vector(record)
            predicted_proto = prototypes.get(predicted_label)
            true_proto = prototypes.get(true_label)
            predicted_distance, predicted_compatible = _distance(true_channel, predicted_proto)
            oracle_prototype_distance, oracle_compatible = _distance(true_channel, true_proto)
            nearest_wrong = _nearest_wrong_distance(true_channel, prototypes, true_label)
            rows.append(
                {
                    "fold": int(fold.get("fold", len(rows))),
                    "test_circuit_id": int(test_group),
                    "row_in_fold": int(row_idx),
                    "location_id": int(record.get("location_id", row_idx)),
                    "true_label_evaluator_only": true_label,
                    "predicted_label": predicted_label,
                    "classification_correct": bool(true_label == predicted_label),
                    "channel_family": true_channel.family,
                    "channel_representation": true_channel.representation,
                    "predicted_channel_compatible": bool(predicted_compatible),
                    "oracle_prototype_compatible": bool(oracle_compatible),
                    "predicted_channel_distance": float(predicted_distance),
                    "same_label_train_prototype_distance": float(oracle_prototype_distance),
                    "nearest_wrong_label_distance": float(nearest_wrong),
                    "nearest_wrong_gap": float(nearest_wrong - predicted_distance),
                }
            )

    summary = _quality_summary(rows)
    mechanism_balanced_accuracy = float(prediction_source.get("balanced_accuracy", 0.0))
    mechanism_min_recall = float(prediction_source.get("min_class_recall", 0.0))
    mechanism_ari = float(prediction_source.get("adjusted_rand_index", 0.0))
    mechanism_nmi = float(prediction_source.get("normalized_mutual_info", 0.0))
    learner_contract_passed = bool(prediction_source.get("learner_contract_passed", False))
    leakage_clean = bool(prediction_source.get("leakage_clean", False))
    passed = (
        bool(rows)
        and learner_contract_passed
        and leakage_clean
        and mechanism_balanced_accuracy >= float(min_mechanism_balanced_accuracy)
        and mechanism_min_recall >= float(min_mechanism_min_recall)
        and mechanism_ari >= 1.0
        and mechanism_nmi >= 1.0
        and summary["predicted_channel_distance"]["mean"] <= float(max_mean_predicted_channel_distance)
        and summary["predicted_channel_distance"]["max"] <= float(max_worst_predicted_channel_distance)
        and (
            min_nearest_wrong_channel_gap is None
            or summary["nearest_wrong_gap"]["mean"] >= float(min_nearest_wrong_channel_gap)
        )
        and summary["incompatible_prediction_count"] == 0
    )
    result = {
        "schema": "scope_static_phyc3_sampled_quantum_error_quality_v1",
        "stage": "PHYC3_sampled_quantum_error_quality",
        "public_layer": LAYER3_LEARNER.metadata(
            artifact_stage="PHYC3_sampled_quantum_error_quality",
            substage="learner_noise_generation_quality",
        ),
        "teacher_dir": str(teacher),
        "prediction_dir": str(phyc2),
        "output_dir": str(output),
        "contract": {
            "name": "sampled_observation_mechanism_predictions_yield_good_quantum_error_prototypes",
            "primary_role": LAYER3_LEARNER.public_name,
            "teacher_self_predictions_allowed": False,
            "learner_contract_passed_required": True,
            "leakage_clean_required": True,
            "mechanism_balanced_accuracy_ge": float(min_mechanism_balanced_accuracy),
            "mechanism_min_class_recall_ge": float(min_mechanism_min_recall),
            "mechanism_ARI_eq": 1.0,
            "mechanism_NMI_eq": 1.0,
            "mean_predicted_channel_distance_le": float(max_mean_predicted_channel_distance),
            "max_predicted_channel_distance_le": float(max_worst_predicted_channel_distance),
            "mean_nearest_wrong_channel_gap_ge": None if min_nearest_wrong_channel_gap is None else float(min_nearest_wrong_channel_gap),
            "mean_nearest_wrong_channel_gap_role": "diagnostic_only" if min_nearest_wrong_channel_gap is None else "gating",
            "incompatible_prediction_count_eq": 0,
        },
        "claim_boundary": (
            "Layer 3 consumes no-leakage learner predictions, not Layer 2 teacher-self predictions. "
            "Channel/readout quality is then measured against evaluator-only mechanism-channel definitions."
        ),
        "contract_passed": bool(passed),
        "decision": "sampled_predictions_yield_good_quantum_error_prototypes" if passed else "quantum_error_quality_diagnostic_failed",
        "prediction_source_audit": prediction_source,
        "mechanism_classification": {
            "balanced_accuracy": mechanism_balanced_accuracy,
            "min_class_recall": mechanism_min_recall,
            "adjusted_rand_index": mechanism_ari,
            "normalized_mutual_info": mechanism_nmi,
            "prevalence_weighted_accuracy": float(prediction_source.get("prevalence_weighted_accuracy", 0.0)),
            "rare_class_recall_min": float(prediction_source.get("rare_class_recall_min", 0.0)),
        },
        "quality_summary": summary,
        "records": rows,
    }
    _write_outputs(output, result)
    return result


def _learner_prediction_source(phyc2_metrics: dict[str, object]) -> dict[str, object]:
    primary_block = str(phyc2_metrics.get("primary_feature_block", ""))
    stage = str(phyc2_metrics.get("stage", ""))
    if stage == "PHYC3_no_leakage_learner_recovery" or primary_block == "typed_gate_readout_prep_invariant_learner":
        source = _prediction_source_from_metrics(
            phyc2_metrics,
            source_name="phyc3_no_leakage_learner_recovery",
            teacher_self=False,
        )
    else:
        primary_block = str(phyc2_metrics.get("primary_feature_block", ""))
        if primary_block.startswith("teacher_self"):
            reason = "Layer 3 requires no-leakage learner predictions from Layer 3 learner recovery; Layer 2 teacher-self predictions are forbidden"
            teacher_self = True
        elif isinstance(phyc2_metrics.get("sampled_observation_learner_diagnostic"), dict):
            reason = "legacy PHYC2-embedded learner diagnostics must be regenerated as PHYC3_no_leakage_learner_recovery artifacts"
            teacher_self = False
        else:
            reason = "PHYC3 learner-recovery predictions are missing"
            teacher_self = False
        return {
            "schema": "scope_static_phyc3_prediction_source_audit_v1",
            "source_name": "none",
            "teacher_self_predictions": bool(teacher_self),
            "teacher_self_predictions_allowed": False,
            "learner_contract_passed": False,
            "leakage_clean": False,
            "grouped_fold_predictions": [],
            "reason": reason,
        }

    leakage_guardrail = phyc2_metrics.get("leakage_guardrail_audit", {})
    leakage_guardrail_passed = bool(leakage_guardrail.get("passed", True)) if isinstance(leakage_guardrail, dict) else True
    slot_only = phyc2_metrics.get("slot_only_leakage_control", {})
    slot_only_leakage_suspected = bool(slot_only.get("leakage_suspected", False)) if isinstance(slot_only, dict) else False
    source["leakage_guardrail_passed"] = leakage_guardrail_passed
    source["slot_only_leakage_suspected"] = slot_only_leakage_suspected
    source["leakage_clean"] = bool(leakage_guardrail_passed and not slot_only_leakage_suspected)
    return source


def _prediction_source_from_metrics(metrics: dict[str, object], *, source_name: str, teacher_self: bool) -> dict[str, object]:
    ceiling = metrics.get("supervised_grouped_ceiling", {})
    folds = ceiling.get("grouped_fold_predictions", []) if isinstance(ceiling, dict) else []
    true, pred = _fold_true_pred(folds if isinstance(folds, list) else [])
    ari, nmi = _partition_scores(true, pred)
    return {
        "schema": "scope_static_phyc3_prediction_source_audit_v1",
        "source_name": source_name,
        "teacher_self_predictions": bool(teacher_self),
        "teacher_self_predictions_allowed": False,
        "learner_contract_passed": bool(metrics.get("contract_passed", False)),
        "primary_feature_block": metrics.get("primary_feature_block"),
        "primary_head": metrics.get("primary_head"),
        "balanced_accuracy": float(metrics.get("balanced_accuracy", 0.0)),
        "min_class_recall": float(metrics.get("min_class_recall", 0.0)),
        "adjusted_rand_index": float(metrics.get("adjusted_rand_index", ari)),
        "normalized_mutual_info": float(metrics.get("normalized_mutual_info", nmi)),
        "prevalence_weighted_accuracy": float(metrics.get("prevalence_weighted_accuracy", 0.0)),
        "rare_class_recall_min": float(metrics.get("rare_class_recall_min", 0.0)),
        "grouped_fold_predictions": folds if isinstance(folds, list) else [],
    }


def _fold_true_pred(folds: list[object]) -> tuple[list[str], list[str]]:
    true: list[str] = []
    pred: list[str] = []
    for fold in folds:
        if not isinstance(fold, dict):
            continue
        true.extend(str(item) for item in fold.get("true_labels", []))
        pred.extend(str(item) for item in fold.get("predicted_labels", []))
    return true, pred


def _partition_scores(true: list[str], pred: list[str]) -> tuple[float, float]:
    labels = sorted(set(true) | set(pred), key=_mechanism_sort_key)
    if not labels:
        return 0.0, 0.0
    index = {label: idx for idx, label in enumerate(labels)}
    left = [index[label] for label in true]
    right = [index[label] for label in pred]
    return float(adjusted_rand_index(left, right)), float(normalized_mutual_info(left, right))


def channel_vector(record: dict[str, object]) -> ChannelVector:
    spec = MechanismSpec(
        mechanism_id=str(record.get("oracle_label", record.get("mechanism_id", ""))),
        name=str(record.get("name", record.get("oracle_label", ""))),
        num_qubits=int(record.get("num_qubits", 1)),
        parameters=dict(record.get("parameters", {})),
        instruction=None if record.get("instruction") is None else str(record.get("instruction")),
        qubits=tuple(int(value) for value in record.get("qubits", [])),
        circuit_id=int(record.get("circuit_id", 0)),
        probe_indices=tuple(int(value) for value in record.get("probe_indices", [])),
    )
    channel = mechanism_channel(spec)
    kind = str(channel["kind"])
    if kind == "readout":
        matrix = np.asarray(channel["matrix"], dtype=np.float64)
        vector = matrix.reshape(-1)
        family = f"readout_assignment:{matrix.shape[0]}x{matrix.shape[1]}"
        return ChannelVector(family=family, vector=_finite(vector), representation="readout_assignment_matrix", mechanism_id=spec.mechanism_id)
    if kind == "unitary":
        matrix = ptm_from_unitary(np.asarray(channel["unitary"], dtype=np.complex128))
    elif kind == "kraus":
        matrix = ptm_from_kraus(channel["kraus"])  # type: ignore[arg-type]
    else:
        raise ValueError(f"unknown channel kind {kind!r}")
    family = f"quantum_ptm:{int(spec.num_qubits)}q:{matrix.shape[0]}x{matrix.shape[1]}"
    return ChannelVector(family=family, vector=_finite(matrix.reshape(-1)), representation="pauli_transfer_matrix", mechanism_id=spec.mechanism_id)


def format_sampled_quantum_error_quality_summary(result: dict[str, object]) -> str:
    quality = result.get("quality_summary", {})
    predicted = quality.get("predicted_channel_distance", {}) if isinstance(quality, dict) else {}
    gap = quality.get("nearest_wrong_gap", {}) if isinstance(quality, dict) else {}
    classification = result.get("mechanism_classification", {})
    if not isinstance(classification, dict):
        classification = {}
    prediction_source = result.get("prediction_source_audit", {})
    if not isinstance(prediction_source, dict):
        prediction_source = {}
    return "\n".join(
        [
            "# Layer 3: Learner Noise Generation Quality",
            "",
            f"- Legacy alias: `{dict(result.get('public_layer', {})).get('legacy_alias', 'PHYC3')}`",
            f"- Decision: `{result.get('decision')}`",
            f"- Contract passed: `{str(bool(result.get('contract_passed'))).lower()}`",
            f"- Prediction source: `{prediction_source.get('source_name', 'unknown')}`",
            f"- Mechanism balanced accuracy: `{float(classification.get('balanced_accuracy', 0.0)):.4f}`",
            f"- Mechanism min class recall: `{float(classification.get('min_class_recall', 0.0)):.4f}`",
            f"- Mechanism ARI: `{float(classification.get('adjusted_rand_index', 0.0)):.4f}`",
            f"- Mechanism NMI: `{float(classification.get('normalized_mutual_info', 0.0)):.4f}`",
            f"- Mean predicted channel distance: `{float(predicted.get('mean', 0.0)):.6f}`",
            f"- Max predicted channel distance: `{float(predicted.get('max', 0.0)):.6f}`",
            f"- Mean nearest-wrong gap: `{float(gap.get('mean', 0.0)):.6f}`",
            f"- Incompatible predictions: `{int(quality.get('incompatible_prediction_count', 0)) if isinstance(quality, dict) else 0}`",
            "",
            "## Claim Boundary",
            "",
            str(result.get("claim_boundary", "")),
            "",
        ]
    )


def _channel_prototypes(records: list[dict[str, object]]) -> dict[str, ChannelVector]:
    grouped: dict[str, list[ChannelVector]] = {}
    for record in records:
        grouped.setdefault(str(record.get("oracle_label", "")), []).append(channel_vector(record))
    prototypes = {}
    for label, vectors in grouped.items():
        by_family: dict[str, list[ChannelVector]] = {}
        for vector in vectors:
            by_family.setdefault(vector.family, []).append(vector)
        family, local = max(by_family.items(), key=lambda item: len(item[1]))
        matrix = np.stack([item.vector for item in local], axis=0)
        prototypes[label] = ChannelVector(
            family=family,
            vector=_finite(np.mean(matrix, axis=0)),
            representation=local[0].representation,
            mechanism_id=label,
        )
    return prototypes


def _distance(true_channel: ChannelVector, predicted: ChannelVector | None) -> tuple[float, bool]:
    if predicted is None or true_channel.family != predicted.family or true_channel.vector.shape != predicted.vector.shape:
        return float("inf"), False
    scale = float(np.sqrt(max(1, true_channel.vector.size)))
    return float(np.linalg.norm(true_channel.vector - predicted.vector) / scale), True


def _nearest_wrong_distance(true_channel: ChannelVector, prototypes: dict[str, ChannelVector], true_label: str) -> float:
    distances = [
        _distance(true_channel, prototype)[0]
        for label, prototype in prototypes.items()
        if str(label) != str(true_label) and prototype.family == true_channel.family
    ]
    finite = [float(value) for value in distances if np.isfinite(value)]
    return float(min(finite)) if finite else float("inf")


def _quality_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    predicted = [float(row["predicted_channel_distance"]) for row in rows]
    oracle = [float(row["same_label_train_prototype_distance"]) for row in rows]
    wrong = [float(row["nearest_wrong_label_distance"]) for row in rows]
    gaps = [float(row["nearest_wrong_gap"]) for row in rows]
    by_label = {}
    for label in sorted({str(row["true_label_evaluator_only"]) for row in rows}, key=_mechanism_sort_key):
        local = [row for row in rows if str(row["true_label_evaluator_only"]) == label]
        by_label[label] = {
            "support": int(len(local)),
            "classification_accuracy": float(np.mean([bool(row["classification_correct"]) for row in local])) if local else 0.0,
            "mean_predicted_channel_distance": _distribution([float(row["predicted_channel_distance"]) for row in local])["mean"],
            "mean_nearest_wrong_gap": _distribution([float(row["nearest_wrong_gap"]) for row in local])["mean"],
        }
    return {
        "num_records": int(len(rows)),
        "classification_accuracy": float(np.mean([bool(row["classification_correct"]) for row in rows])) if rows else 0.0,
        "compatible_prediction_count": int(sum(bool(row["predicted_channel_compatible"]) for row in rows)),
        "incompatible_prediction_count": int(sum(not bool(row["predicted_channel_compatible"]) for row in rows)),
        "predicted_channel_distance": _distribution(predicted),
        "same_label_train_prototype_distance": _distribution(oracle),
        "nearest_wrong_label_distance": _distribution(wrong),
        "nearest_wrong_gap": _distribution(gaps),
        "by_true_label": by_label,
    }


def _distribution(values: list[float]) -> dict[str, float]:
    finite = np.asarray([float(value) for value in values if np.isfinite(value)], dtype=np.float64)
    if finite.size == 0:
        return {"mean": float("inf"), "median": float("inf"), "p95": float("inf"), "max": float("inf")}
    return {
        "mean": float(np.mean(finite)),
        "median": float(np.median(finite)),
        "p95": float(np.quantile(finite, 0.95)),
        "max": float(np.max(finite)),
    }


def _records_for_fold(records: list[dict[str, object]], test_group: int, true_labels: list[str]) -> list[dict[str, object]]:
    local = [record for record in records if int(record.get("circuit_id", 0)) == int(test_group)]
    if [str(record.get("oracle_label", "")) for record in local] == true_labels:
        return local
    unused = list(local)
    aligned = []
    for label in true_labels:
        match_idx = next((idx for idx, record in enumerate(unused) if str(record.get("oracle_label", "")) == str(label)), None)
        if match_idx is None:
            raise ValueError(f"cannot align PHYC2 fold records for circuit_id={test_group}, label={label}")
        aligned.append(unused.pop(match_idx))
    return aligned


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text())
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "metrics.json").write_text(json.dumps(_json_safe(result), indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_sampled_quantum_error_quality_summary(result))


def _not_evaluable_result(teacher: Path, phyc2: Path, output: Path, reason: str) -> dict[str, object]:
    return {
        "schema": "scope_static_phyc3_sampled_quantum_error_quality_v1",
        "stage": "PHYC3_sampled_quantum_error_quality",
        "public_layer": LAYER3_LEARNER.metadata(
            artifact_stage="PHYC3_sampled_quantum_error_quality",
            substage="learner_noise_generation_quality",
        ),
        "teacher_dir": str(teacher),
        "phyc2_dir": str(phyc2),
        "prediction_dir": str(phyc2),
        "output_dir": str(output),
        "contract_passed": False,
        "decision": "insufficient_phyc2_predictions",
        "reason": str(reason),
        "quality_summary": _quality_summary([]),
    }


def _finite(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)


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
    if isinstance(value, float) and not np.isfinite(value):
        return "inf" if value > 0.0 else "-inf"
    return value


def _mechanism_sort_key(name: str) -> tuple[int, str]:
    text = str(name)
    if text.startswith("M") and text[1:].isdigit():
        return (int(text[1:]), text)
    return (10_000, text)
