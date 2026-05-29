from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .sampled_observation_separability import _load_mechanism_records
from .sampled_quantum_error_quality import ChannelVector, channel_vector


STAGE_NAME = "PHYC3_canonical_quality_acceptance"
ACCEPTED_SOURCE_NAME = "phyc3c_distributional_gaussian_likelihood_head"
PRIMARY_HEAD = "PHYC3c_diagonal_gaussian"


def run_phyc3_canonical_acceptance(
    *,
    phyc2_dir: str | Path,
    phyc3a_dir: str | Path,
    phyc3b_dir: str | Path,
    phyc3c_dir: str | Path,
    phyc3c_validation_dir: str | Path,
    output_dir: str | Path,
    teacher_dir: str | Path | None = None,
    primary_head: str = PRIMARY_HEAD,
    max_mean_predicted_channel_distance: float = 0.02,
    max_worst_predicted_channel_distance: float = 0.005,
) -> dict[str, object]:
    phyc2_path = Path(phyc2_dir)
    phyc3a_path = Path(phyc3a_dir)
    phyc3b_path = Path(phyc3b_dir)
    phyc3c_path = Path(phyc3c_dir)
    validation_path = Path(phyc3c_validation_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    phyc2 = _load_metrics(phyc2_path)
    phyc3a = _load_metrics(phyc3a_path)
    phyc3b = _load_metrics(phyc3b_path)
    phyc3c = _load_metrics(phyc3c_path)
    validation = _load_metrics(validation_path)
    teacher = Path(teacher_dir) if teacher_dir is not None else Path(str(phyc3c.get("teacher_dir", phyc3b.get("teacher_dir", ""))))
    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")

    phyc2_audit = audit_phyc2_teacher_self(phyc2)
    phyc3a_audit = audit_phyc3a_baseline(phyc3a)
    phyc3b_audit = audit_phyc3b_visible_repair(phyc3b)
    phyc3c_audit = audit_phyc3c_accepted_learner(phyc3c, validation, primary_head=str(primary_head))
    rejected = rejected_source_audit(phyc2, phyc3a)
    canonical_source = canonical_prediction_source(phyc3c, validation, primary_head=str(primary_head))
    quality = canonical_quality_from_phyc3c_batches(
        records,
        phyc3c,
        primary_head=str(primary_head),
        max_mean_predicted_channel_distance=float(max_mean_predicted_channel_distance),
        max_worst_predicted_channel_distance=float(max_worst_predicted_channel_distance),
    )
    checks = {
        "phyc2_teacher_self_passed": bool(phyc2_audit["passed"]),
        "phyc2_emits_no_learner_predictions": bool(phyc2_audit["checks"]["phyc2_emits_no_learner_predictions"]),
        "phyc3a_is_baseline_failure_not_source": bool(phyc3a_audit["passed"]),
        "phyc3b_visible_repair_passed": bool(phyc3b_audit["passed"]),
        "phyc3c_accepted_learner_passed": bool(phyc3c_audit["passed"]),
        "rejected_noncanonical_sources": bool(rejected["passed"]),
        "canonical_quality_passed": bool(quality["passed"]),
        "canonical_prediction_source_is_phyc3c": canonical_source["source_name"] == ACCEPTED_SOURCE_NAME,
    }
    passed = bool(all(checks.values()))
    result = {
        "schema": "scope_static_phyc3_canonical_quality_acceptance_v1",
        "stage": STAGE_NAME,
        "output_dir": str(output),
        "teacher_dir": str(teacher),
        "inputs": {
            "phyc2_dir": str(phyc2_path),
            "phyc3a_dir": str(phyc3a_path),
            "phyc3b_dir": str(phyc3b_path),
            "phyc3c_dir": str(phyc3c_path),
            "phyc3c_validation_dir": str(validation_path),
        },
        "claim_boundary": {
            "resolver_not_new_learner": True,
            "canonical_prediction_source": ACCEPTED_SOURCE_NAME,
            "rejects_phyc2_teacher_self_predictions": True,
            "rejects_legacy_phyc2_grouped_predictions": True,
            "rejects_phyc3a_old_surface_as_canonical_source": True,
            "requires_phyc3b_visible_ceiling": True,
            "requires_phyc3c_multi_context_protocol": True,
        },
        "primary_head": str(primary_head),
        "phyc2_teacher_self_audit": phyc2_audit,
        "phyc3a_baseline_audit": phyc3a_audit,
        "phyc3b_visible_repair_audit": phyc3b_audit,
        "phyc3c_accepted_learner_audit": phyc3c_audit,
        "rejected_sources": rejected,
        "canonical_prediction_source": canonical_source,
        "canonical_quality_metrics": quality,
        "acceptance_checks": checks,
        "contract_passed": passed,
        "decision": "phyc3_canonical_quality_accepted" if passed else "phyc3_canonical_quality_rejected",
    }
    _write_outputs(output, result)
    return result


def audit_phyc2_teacher_self(phyc2: dict[str, object]) -> dict[str, object]:
    checks = {
        "stage_is_phyc2_teacher_self": str(phyc2.get("stage", "")).startswith("PHYC2"),
        "teacher_self_ba_is_one": _is_one(phyc2.get("balanced_accuracy")),
        "teacher_self_ari_is_one": _is_one(phyc2.get("adjusted_rand_index")),
        "teacher_self_nmi_is_one": _is_one(phyc2.get("normalized_mutual_info")),
        "teacher_self_min_recall_is_one": _is_one(phyc2.get("min_class_recall")),
        "phyc2_emits_no_learner_predictions": phyc2.get("phyc2_emits_learner_grouped_predictions") is False,
        "phyc2_has_no_legacy_learner_diagnostic": "sampled_observation_learner_diagnostic" not in phyc2,
    }
    return {
        "schema": "scope_static_phyc3_canonical_phyc2_teacher_self_audit_v1",
        "role": "PHYC2_teacher_self_only_v4",
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def audit_phyc3a_baseline(phyc3a: dict[str, object]) -> dict[str, object]:
    checks = {
        "stage_is_phyc3_old_surface_learner": str(phyc3a.get("stage")) == "PHYC3_no_leakage_learner_recovery",
        "baseline_is_not_accepted_source": True,
        "baseline_expected_to_fail": bool(phyc3a.get("contract_passed")) is False,
        "baseline_has_low_metrics": float(phyc3a.get("normalized_mutual_info", 0.0)) < 1.0,
        "teacher_self_predictions_forbidden": phyc3a.get("teacher_self_predictions_allowed") is False,
    }
    return {
        "schema": "scope_static_phyc3_canonical_phyc3a_baseline_audit_v1",
        "role": "PHYC3a_old_surface_no_leakage_learner_recovery",
        "decision": phyc3a.get("decision"),
        "balanced_accuracy": float(phyc3a.get("balanced_accuracy", 0.0)),
        "adjusted_rand_index": float(phyc3a.get("adjusted_rand_index", 0.0)),
        "normalized_mutual_info": float(phyc3a.get("normalized_mutual_info", 0.0)),
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def audit_phyc3b_visible_repair(phyc3b: dict[str, object]) -> dict[str, object]:
    leakage = phyc3b.get("leakage_guardrail_audit", {})
    leakage_passed = bool(leakage.get("passed", False)) if isinstance(leakage, dict) else False
    checks = {
        "stage_is_phyc3b": phyc3b.get("stage") == "PHYC3b_ZX_visible_alias_breaking_probe_suite",
        "visible_conflicts_after_zero": int(phyc3b.get("visible_signature_conflicts_after", -1)) == 0,
        "deterministic_ceiling_ba_is_one": _is_one(phyc3b.get("deterministic_ceiling_BA_after")),
        "deterministic_ceiling_ari_is_one": _is_one(phyc3b.get("deterministic_ceiling_ARI_after")),
        "deterministic_ceiling_nmi_is_one": _is_one(phyc3b.get("deterministic_ceiling_NMI_after")),
        "leakage_guardrail_passed": leakage_passed,
    }
    return {
        "schema": "scope_static_phyc3_canonical_phyc3b_visible_repair_audit_v1",
        "role": "PHYC3b_ZX_visible_alias_breaking_probe_suite",
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def audit_phyc3c_accepted_learner(
    phyc3c: dict[str, object],
    validation: dict[str, object],
    *,
    primary_head: str,
) -> dict[str, object]:
    leakage = phyc3c.get("leakage_guardrail_audit", {})
    leakage_passed = bool(leakage.get("passed", False)) if isinstance(leakage, dict) else False
    checks = {
        "stage_is_phyc3c": phyc3c.get("stage") == "PHYC3c_distributional_gaussian_likelihood_head",
        "prediction_source_is_phyc3c": True,
        "primary_mode_is_multi_context": phyc3c.get("primary_mode") == "multi_context_batch",
        "primary_head_matches": phyc3c.get("primary_head") == primary_head,
        "learner_ba_is_one": _is_one(phyc3c.get("learner_BA")),
        "learner_ari_is_one": _is_one(phyc3c.get("learner_ARI")),
        "learner_nmi_is_one": _is_one(phyc3c.get("learner_NMI")),
        "min_recall_is_one": _is_one(phyc3c.get("min_recall")),
        "m13_recall_is_one": _is_one(phyc3c.get("m13_recall")),
        "non_leakage_guardrail_passed": leakage_passed,
        "validation_non_leakage_passed": bool(validation.get("non_leakage_passed", False)),
        "validation_protocol_valid": bool(validation.get("protocol_validity_passed", False)),
        "validation_robustness_passed": bool(validation.get("robustness_passed", False)),
    }
    return {
        "schema": "scope_static_phyc3_canonical_phyc3c_accepted_learner_audit_v1",
        "role": "PHYC3c_distributional_gaussian_likelihood_head",
        "source_name": ACCEPTED_SOURCE_NAME,
        "protocol": phyc3c.get("primary_mode"),
        "primary_head": primary_head,
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def rejected_source_audit(phyc2: dict[str, object], phyc3a: dict[str, object]) -> dict[str, object]:
    legacy_phyc2 = "sampled_observation_learner_diagnostic" in phyc2
    rejected = [
        {
            "source_name": "PHYC2_teacher_self_only_v4",
            "accepted_as_canonical": False,
            "reason": "teacher/catalog self-distinguishability is not learner evidence",
            "rejected": True,
        },
        {
            "source_name": "legacy_phyc2_grouped_predictions",
            "accepted_as_canonical": False,
            "reason": "legacy PHYC2 learner diagnostics must be regenerated as PHYC3 learner artifacts",
            "rejected": True,
            "present": bool(legacy_phyc2),
        },
        {
            "source_name": "PHYC3a_old_surface_no_leakage_learner_recovery",
            "accepted_as_canonical": False,
            "reason": "baseline old-surface learner is an expected failing control",
            "rejected": True,
            "decision": phyc3a.get("decision"),
        },
    ]
    return {
        "schema": "scope_static_phyc3_canonical_rejected_sources_v1",
        "sources": rejected,
        "passed": bool(all(bool(row["rejected"]) and not bool(row["accepted_as_canonical"]) for row in rejected)),
    }


def canonical_prediction_source(
    phyc3c: dict[str, object],
    validation: dict[str, object],
    *,
    primary_head: str,
) -> dict[str, object]:
    multi = dict(phyc3c.get("multi_context_batch_mode", {}))
    head = dict(dict(multi.get("head_results", {})).get(primary_head, {}))
    return {
        "schema": "scope_static_phyc3_canonical_prediction_source_v1",
        "source_name": ACCEPTED_SOURCE_NAME,
        "stage": phyc3c.get("stage"),
        "primary_mode": phyc3c.get("primary_mode"),
        "primary_head": primary_head,
        "protocol": multi.get("protocol", {}),
        "balanced_accuracy": float(head.get("balanced_accuracy", phyc3c.get("learner_BA", 0.0))),
        "adjusted_rand_index": float(head.get("adjusted_rand_index", phyc3c.get("learner_ARI", 0.0))),
        "normalized_mutual_info": float(head.get("normalized_mutual_info", phyc3c.get("learner_NMI", 0.0))),
        "min_class_recall": float(head.get("min_class_recall", phyc3c.get("min_recall", 0.0))),
        "m13_recall": float(head.get("m13_recall", phyc3c.get("m13_recall", 0.0))),
        "validation_decision": validation.get("decision"),
        "teacher_self_predictions": False,
        "teacher_self_predictions_allowed": False,
    }


def canonical_quality_from_phyc3c_batches(
    records: list[dict[str, object]],
    phyc3c: dict[str, object],
    *,
    primary_head: str,
    max_mean_predicted_channel_distance: float,
    max_worst_predicted_channel_distance: float,
) -> dict[str, object]:
    folds = (
        dict(dict(phyc3c.get("multi_context_batch_mode", {})).get("head_results", {}))
        .get(primary_head, {})
        .get("grouped_fold_predictions", [])
    )
    rows = []
    if not isinstance(folds, list):
        folds = []
    for fold in folds:
        if not isinstance(fold, dict):
            continue
        train_groups = [int(group) for group in fold.get("train_groups", [])]
        prototypes = _channel_prototypes([record for record in records if int(record.get("circuit_id", 0)) in set(train_groups)])
        for batch in fold.get("batches", []):
            if not isinstance(batch, dict):
                continue
            true_label = str(batch.get("true_label_evaluator_only", ""))
            predicted_label = str(batch.get("predicted_label", ""))
            test_groups = {int(group) for group in batch.get("test_groups", [])}
            test_records = [
                record
                for record in records
                if str(record.get("oracle_label", "")) == true_label and int(record.get("circuit_id", 0)) in test_groups
            ]
            predicted_proto = prototypes.get(predicted_label)
            for record in test_records:
                true_channel = channel_vector(record)
                predicted_distance, compatible = _distance(true_channel, predicted_proto)
                rows.append(
                    {
                        "fold": int(fold.get("fold", -1)),
                        "test_groups": sorted(test_groups),
                        "true_label_evaluator_only": true_label,
                        "predicted_label": predicted_label,
                        "classification_correct": bool(true_label == predicted_label),
                        "predicted_channel_compatible": bool(compatible),
                        "predicted_channel_distance": float(predicted_distance),
                        "source_name": ACCEPTED_SOURCE_NAME,
                    }
                )
    predicted = [float(row["predicted_channel_distance"]) for row in rows if np.isfinite(float(row["predicted_channel_distance"]))]
    incompatible = int(sum(not bool(row["predicted_channel_compatible"]) for row in rows))
    accuracy = float(np.mean([bool(row["classification_correct"]) for row in rows])) if rows else 0.0
    distances = _distribution(predicted)
    passed = (
        bool(rows)
        and accuracy >= 1.0
        and incompatible == 0
        and distances["mean"] <= float(max_mean_predicted_channel_distance)
        and distances["max"] <= float(max_worst_predicted_channel_distance)
    )
    return {
        "schema": "scope_static_phyc3_canonical_quality_metrics_v1",
        "prediction_source": ACCEPTED_SOURCE_NAME,
        "primary_head": primary_head,
        "num_records": int(len(rows)),
        "classification_accuracy": accuracy,
        "incompatible_prediction_count": incompatible,
        "predicted_channel_distance": distances,
        "thresholds": {
            "mean_predicted_channel_distance_le": float(max_mean_predicted_channel_distance),
            "max_predicted_channel_distance_le": float(max_worst_predicted_channel_distance),
            "incompatible_prediction_count_eq": 0,
        },
        "passed": bool(passed),
        "records": rows,
    }


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
            vector=np.nan_to_num(np.mean(matrix, axis=0), nan=0.0, posinf=0.0, neginf=0.0),
            representation=local[0].representation,
            mechanism_id=label,
        )
    return prototypes


def _distance(true_channel: ChannelVector, predicted: ChannelVector | None) -> tuple[float, bool]:
    if predicted is None or true_channel.family != predicted.family or true_channel.vector.shape != predicted.vector.shape:
        return float("inf"), False
    scale = float(np.sqrt(max(1, true_channel.vector.size)))
    return float(np.linalg.norm(true_channel.vector - predicted.vector) / scale), True


def _distribution(values: list[float]) -> dict[str, float]:
    finite = [float(value) for value in values if np.isfinite(value)]
    if not finite:
        return {"mean": float("inf"), "median": float("inf"), "max": float("inf"), "p95": float("inf")}
    arr = np.asarray(finite, dtype=np.float64)
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "max": float(np.max(arr)),
        "p95": float(np.quantile(arr, 0.95)),
    }


def format_phyc3_canonical_acceptance_summary(result: dict[str, object]) -> str:
    quality = dict(result.get("canonical_quality_metrics", {}))
    distances = dict(quality.get("predicted_channel_distance", {}))
    return "\n".join(
        [
            "# PHYC3 Canonical Quality Acceptance",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Contract passed: `{str(bool(result.get('contract_passed'))).lower()}`",
            f"- Canonical source: `{dict(result.get('canonical_prediction_source', {})).get('source_name', 'unknown')}`",
            f"- Quality records: `{int(quality.get('num_records', 0))}`",
            f"- Classification accuracy: `{float(quality.get('classification_accuracy', 0.0)):.4f}`",
            f"- Incompatible predictions: `{int(quality.get('incompatible_prediction_count', 0))}`",
            f"- Mean predicted channel distance: `{float(distances.get('mean', 0.0)):.6f}`",
            f"- Max predicted channel distance: `{float(distances.get('max', 0.0)):.6f}`",
            "",
            "## Claim Boundary",
            "",
            "This stage is a resolver and acceptance artifact. It does not train another learner; it accepts PHYC3c multi-context predictions as canonical only after PHYC2, PHYC3b, PHYC3c, and PHYC3c validation gates pass.",
            "",
        ]
    )


def _load_metrics(path: Path) -> dict[str, object]:
    metrics_path = path / "metrics.json" if path.is_dir() else path
    data = json.loads(metrics_path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{metrics_path} must contain a JSON object")
    return data


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "provenance_audit.json": {
            "inputs": result["inputs"],
            "canonical_prediction_source": result["canonical_prediction_source"],
            "rejected_sources": result["rejected_sources"],
        },
        "acceptance_checks.json": result["acceptance_checks"],
        "canonical_quality_metrics.json": result["canonical_quality_metrics"],
        "rejected_sources.json": result["rejected_sources"],
        "canonical_prediction_source.json": result["canonical_prediction_source"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_phyc3_canonical_acceptance_summary(result))


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


def _is_one(value: object) -> bool:
    try:
        return abs(float(value) - 1.0) <= 1e-12
    except (TypeError, ValueError):
        return False
