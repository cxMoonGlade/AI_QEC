from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.protocols import TEACHER_VALIDATION_STAGE, LEARNER_VALIDATION_STAGE, catalog_validation_stage_metadata
from .zx_visible_probe_suite import build_zx_visible_feature_table
from .gaussian_likelihood import fit_gaussian_fold_model
from scope_static.teacher.observation_surface import _load_mechanism_records
from .quality import ChannelVector, channel_vector


STAGE_NAME = "PHYC3_canonical_quality_acceptance"
ACCEPTED_SOURCE_NAME = "phyc3c_distributional_gaussian_likelihood_head"
PRIMARY_HEAD = "PHYC3c_diagonal_gaussian"


def run_layer3_acceptance(
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
    generation = learner_generation_quality_from_phyc3c_batches(
        records,
        phyc3c,
        primary_head=str(primary_head),
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
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="canonical_quality_acceptance"),
        "public_layer_stack": catalog_validation_stage_metadata(),
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
            "public_name": LEARNER_VALIDATION_STAGE.public_name,
            "canonical_prediction_source": ACCEPTED_SOURCE_NAME,
            "rejects_layer2_teacher_self_predictions": True,
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
        "learner_generation_quality_metrics": generation,
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
        "public_layer": TEACHER_VALIDATION_STAGE.metadata(artifact_stage="PHYC2_teacher_self_only_v4", substage="teacher_self_only"),
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
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage="PHYC3a_old_surface_no_leakage_learner_recovery", substage="old_surface_baseline"),
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
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage="PHYC3b_ZX_visible_alias_breaking_probe_suite", substage="zx_visible_surface_repair"),
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
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage="PHYC3c_distributional_gaussian_likelihood_head", substage="distributional_gaussian_likelihood_head"),
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


def learner_generation_quality_from_phyc3c_batches(
    records: list[dict[str, object]],
    phyc3c: dict[str, object],
    *,
    primary_head: str,
) -> dict[str, object]:
    """Score held-out visible error-generation quality from PHYC3c predictions.

    This diagnostic re-fits the same fold-local PHYC3c calibration model from
    training groups only. It then evaluates each held-out batch under the
    predicted label's visible-feature generator. True labels appear only in the
    evaluator rows and in the oracle-comparator baseline.
    """

    config = dict(phyc3c.get("config", {})) if isinstance(phyc3c.get("config", {}), dict) else {}
    table = build_zx_visible_feature_table(
        records,
        shots=int(config.get("shots", 20_000)),
        seed=int(config.get("seed", 0)),
        robustness_mode=bool(config.get("robustness_mode", False)),
        sampling_mode=str(config.get("sampling_mode", "expected")),
    )
    labels = [str(label) for label in table.labels]
    groups = [int(group) for group in table.groups]
    class_names = sorted(set(labels), key=_mechanism_sort_key)
    features = np.asarray(table.features, dtype=np.float64)
    folds = (
        dict(dict(phyc3c.get("multi_context_batch_mode", {})).get("head_results", {}))
        .get(primary_head, {})
        .get("grouped_fold_predictions", [])
    )
    if not isinstance(folds, list):
        folds = []
    rows = []
    for fold in folds:
        if not isinstance(fold, dict):
            continue
        train_groups = {int(group) for group in fold.get("train_groups", [])}
        train_indices = [idx for idx, group in enumerate(groups) if int(group) in train_groups]
        if not train_indices:
            continue
        model = fit_gaussian_fold_model(
            features,
            labels,
            train_indices,
            class_names,
            shrinkage_alpha=float(config.get("shrinkage_alpha", 0.25)),
            ridge=float(config.get("ridge", 1e-6)),
            variance_floor=float(config.get("variance_floor", 1e-8)),
            max_pca_components=int(config.get("max_pca_components", 24)),
        )
        prototypes = _visible_feature_prototypes(features, labels, train_indices, class_names)
        global_proto = np.mean(features[np.asarray(train_indices, dtype=np.int64)], axis=0)
        for batch in fold.get("batches", []):
            if not isinstance(batch, dict):
                continue
            true_label = str(batch.get("true_label_evaluator_only", ""))
            predicted_label = str(batch.get("predicted_label", ""))
            test_groups = {int(group) for group in batch.get("test_groups", [])}
            test_indices = [
                idx
                for idx, (label, group) in enumerate(zip(labels, groups))
                if label == true_label and int(group) in test_groups
            ]
            if not test_indices:
                continue
            batch_features = features[np.asarray(test_indices, dtype=np.int64)]
            predicted_proto = prototypes.get(predicted_label)
            oracle_proto = prototypes.get(true_label)
            predicted_visible = _visible_distribution_scores(batch_features, predicted_proto, table.feature_names)
            oracle_visible = _visible_distribution_scores(batch_features, oracle_proto, table.feature_names)
            null_visible = _visible_distribution_scores(batch_features, global_proto, table.feature_names)
            predicted_nll = _diagonal_gaussian_nll(model, features, test_indices, predicted_label, head=primary_head)
            oracle_nll = _diagonal_gaussian_nll(model, features, test_indices, true_label, head=primary_head)
            null_nll = _global_diagonal_gaussian_nll(model, features, test_indices)
            rows.append(
                {
                    "fold": int(fold.get("fold", -1)),
                    "test_groups": sorted(test_groups),
                    "true_label_evaluator_only": true_label,
                    "predicted_label": predicted_label,
                    "classification_correct": bool(true_label == predicted_label),
                    "num_contexts": int(batch_features.shape[0]),
                    "prediction_source": ACCEPTED_SOURCE_NAME,
                    "visible_gaussian_nll_nats_per_feature": float(predicted_nll),
                    "oracle_label_gaussian_nll_nats_per_feature": float(oracle_nll),
                    "global_null_gaussian_nll_nats_per_feature": float(null_nll),
                    "gaussian_nll_gap_to_oracle": float(predicted_nll - oracle_nll),
                    "gaussian_nll_lift_over_global_null": float(null_nll - predicted_nll),
                    "visible_population_cross_entropy_nats_per_probe": float(predicted_visible["population_cross_entropy"]),
                    "oracle_label_population_cross_entropy_nats_per_probe": float(oracle_visible["population_cross_entropy"]),
                    "global_null_population_cross_entropy_nats_per_probe": float(null_visible["population_cross_entropy"]),
                    "population_cross_entropy_gap_to_oracle": float(
                        predicted_visible["population_cross_entropy"] - oracle_visible["population_cross_entropy"]
                    ),
                    "population_cross_entropy_lift_over_global_null": float(
                        null_visible["population_cross_entropy"] - predicted_visible["population_cross_entropy"]
                    ),
                    "visible_raw_feature_mae": float(predicted_visible["raw_feature_mae"]),
                    "visible_population_mae": float(predicted_visible["population_mae"]),
                    "visible_expectation_mae": float(predicted_visible["expectation_mae"]),
                    "oracle_label_raw_feature_mae": float(oracle_visible["raw_feature_mae"]),
                    "global_null_raw_feature_mae": float(null_visible["raw_feature_mae"]),
                    "raw_feature_mae_gap_to_oracle": float(predicted_visible["raw_feature_mae"] - oracle_visible["raw_feature_mae"]),
                    "raw_feature_mae_lift_over_global_null": float(null_visible["raw_feature_mae"] - predicted_visible["raw_feature_mae"]),
                }
            )
    return {
        "schema": "scope_static_phyc3_canonical_learner_generation_quality_v1",
        "prediction_source": ACCEPTED_SOURCE_NAME,
        "primary_head": primary_head,
        "feature_source": "PHYC3b Z/X-only visible sampled-observation features",
        "metric_role": "diagnostic_only_not_used_for_learner_training_or_source_selection",
        "units": {
            "visible_gaussian_nll": "nats_per_selected_feature",
            "visible_population_cross_entropy": "nats_per_probe_distribution",
            "mae": "visible_feature_units",
        },
        "no_leakage_audit": {
            "fold_calibration_uses_training_groups_only": True,
            "test_labels_are_evaluator_only": True,
            "generation_uses_predicted_label_not_true_label": True,
            "oracle_label_metrics_are_comparators_only": True,
            "global_null_metrics_are_comparators_only": True,
            "teacher_self_predictions_used": False,
        },
        "num_batches": int(len(rows)),
        "visible_gaussian_nll_nats_per_feature": _distribution(
            [float(row["visible_gaussian_nll_nats_per_feature"]) for row in rows]
        ),
        "oracle_label_gaussian_nll_nats_per_feature": _distribution(
            [float(row["oracle_label_gaussian_nll_nats_per_feature"]) for row in rows]
        ),
        "global_null_gaussian_nll_nats_per_feature": _distribution(
            [float(row["global_null_gaussian_nll_nats_per_feature"]) for row in rows]
        ),
        "gaussian_nll_gap_to_oracle": _distribution([float(row["gaussian_nll_gap_to_oracle"]) for row in rows]),
        "gaussian_nll_lift_over_global_null": _distribution([float(row["gaussian_nll_lift_over_global_null"]) for row in rows]),
        "visible_population_cross_entropy_nats_per_probe": _distribution(
            [float(row["visible_population_cross_entropy_nats_per_probe"]) for row in rows]
        ),
        "population_cross_entropy_gap_to_oracle": _distribution(
            [float(row["population_cross_entropy_gap_to_oracle"]) for row in rows]
        ),
        "population_cross_entropy_lift_over_global_null": _distribution(
            [float(row["population_cross_entropy_lift_over_global_null"]) for row in rows]
        ),
        "visible_raw_feature_mae": _distribution([float(row["visible_raw_feature_mae"]) for row in rows]),
        "visible_population_mae": _distribution([float(row["visible_population_mae"]) for row in rows]),
        "visible_expectation_mae": _distribution([float(row["visible_expectation_mae"]) for row in rows]),
        "raw_feature_mae_gap_to_oracle": _distribution([float(row["raw_feature_mae_gap_to_oracle"]) for row in rows]),
        "raw_feature_mae_lift_over_global_null": _distribution([float(row["raw_feature_mae_lift_over_global_null"]) for row in rows]),
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


def _visible_feature_prototypes(
    features: np.ndarray,
    labels: list[str],
    train_indices: list[int],
    class_names: list[str],
) -> dict[str, np.ndarray]:
    x = np.asarray(features, dtype=np.float64)
    idx = np.asarray(train_indices, dtype=np.int64)
    out = {}
    for label in class_names:
        local = [int(i) for i in idx.tolist() if labels[int(i)] == label]
        if local:
            out[label] = np.mean(x[np.asarray(local, dtype=np.int64)], axis=0)
    return out


def _visible_distribution_scores(
    rows: np.ndarray,
    prototype: np.ndarray | None,
    feature_names: list[str],
) -> dict[str, float]:
    x = np.asarray(rows, dtype=np.float64)
    if prototype is None or x.size == 0:
        return {
            "population_cross_entropy": float("inf"),
            "population_mae": float("inf"),
            "expectation_mae": float("inf"),
            "raw_feature_mae": float("inf"),
        }
    proto = np.asarray(prototype, dtype=np.float64)
    population_groups = _population_distribution_groups(feature_names)
    ce_values = []
    pop_mae_values = []
    for row in x:
        for cols in population_groups:
            q = _distribution_vector(row, cols)
            p = _distribution_vector(proto, cols)
            ce_values.append(float(-np.sum(q * np.log(np.maximum(p, 1e-12)))))
            pop_mae_values.append(float(np.mean(np.abs(q - p))))
    expectation_cols = _expectation_columns(feature_names)
    raw_cols = _raw_observation_columns(feature_names)
    expectation_mae = float(np.mean(np.abs(x[:, expectation_cols] - proto[expectation_cols]))) if expectation_cols else 0.0
    raw_mae = float(np.mean(np.abs(x[:, raw_cols] - proto[raw_cols]))) if raw_cols else 0.0
    return {
        "population_cross_entropy": float(np.mean(ce_values)) if ce_values else 0.0,
        "population_mae": float(np.mean(pop_mae_values)) if pop_mae_values else 0.0,
        "expectation_mae": expectation_mae,
        "raw_feature_mae": raw_mae,
    }


def _distribution_vector(values: np.ndarray, cols: list[int]) -> np.ndarray:
    probs = np.asarray([float(values[int(col)]) for col in cols], dtype=np.float64)
    probs = np.clip(probs, 0.0, 1.0)
    leftover = max(0.0, 1.0 - float(np.sum(probs)))
    vec = np.concatenate([probs, np.asarray([leftover], dtype=np.float64)])
    total = float(np.sum(vec))
    if total <= 0.0:
        return np.ones_like(vec) / float(max(1, vec.size))
    return vec / total


def _population_distribution_groups(feature_names: list[str]) -> list[list[int]]:
    by_probe: dict[str, dict[str, int]] = {}
    for idx, name in enumerate(feature_names):
        parsed = _raw_feature_metric(name)
        if parsed is None:
            continue
        base, metric = parsed
        if metric in {"P0", "P1", "P00", "P01", "P10", "P11"}:
            by_probe.setdefault(base, {})[metric] = int(idx)
    groups = []
    for local in by_probe.values():
        if {"P0", "P1"}.issubset(local):
            groups.append([local["P0"], local["P1"]])
        elif {"P00", "P01", "P10", "P11"}.issubset(local):
            groups.append([local["P00"], local["P01"], local["P10"], local["P11"]])
    return groups


def _expectation_columns(feature_names: list[str]) -> list[int]:
    cols = []
    for idx, name in enumerate(feature_names):
        parsed = _raw_feature_metric(name)
        if parsed is None:
            continue
        _base, metric = parsed
        if metric.startswith("E_") or metric in {"ZI", "IZ", "ZZ", "XI", "IX", "XX", "ZX", "XZ"}:
            cols.append(int(idx))
    return cols


def _raw_observation_columns(feature_names: list[str]) -> list[int]:
    cols = []
    for idx, name in enumerate(feature_names):
        if _raw_feature_metric(name) is not None:
            cols.append(int(idx))
    return cols


def _raw_feature_metric(name: str) -> tuple[str, str] | None:
    text = str(name)
    if not text.startswith("raw__") or "__se_" in text:
        return None
    if "__" not in text:
        return None
    base, metric = text.rsplit("__", 1)
    return base, metric


def _diagonal_gaussian_nll(
    model: object,
    features: np.ndarray,
    indices: list[int],
    label: str,
    *,
    head: str,
) -> float:
    if str(label) not in getattr(model, "means"):
        return float("inf")
    selected = np.asarray(getattr(model, "selected_columns"), dtype=np.int64)
    rows = np.asarray(features, dtype=np.float64)[np.asarray(indices, dtype=np.int64)][:, selected]
    z = (rows - getattr(model, "feature_mean")) / getattr(model, "feature_scale")
    mean = np.asarray(getattr(model, "means")[str(label)], dtype=np.float64)
    if str(head) == "PHYC3c_shared_covariance_lda":
        variance = np.asarray(getattr(model, "pooled_variance"), dtype=np.float64)
    else:
        variance = np.asarray(getattr(model, "shrinkage_variances")[str(label)], dtype=np.float64)
    return _diagonal_gaussian_nll_from_z(z, mean, variance)


def _global_diagonal_gaussian_nll(model: object, features: np.ndarray, indices: list[int]) -> float:
    selected = np.asarray(getattr(model, "selected_columns"), dtype=np.int64)
    rows = np.asarray(features, dtype=np.float64)[np.asarray(indices, dtype=np.int64)][:, selected]
    z = (rows - getattr(model, "feature_mean")) / getattr(model, "feature_scale")
    mean = np.zeros(z.shape[1], dtype=np.float64)
    variance = np.asarray(getattr(model, "pooled_variance"), dtype=np.float64)
    return _diagonal_gaussian_nll_from_z(z, mean, variance)


def _diagonal_gaussian_nll_from_z(z: np.ndarray, mean: np.ndarray, variance: np.ndarray) -> float:
    if z.size == 0:
        return float("inf")
    var = np.maximum(np.asarray(variance, dtype=np.float64), 1e-12)
    delta = np.asarray(z, dtype=np.float64) - np.asarray(mean, dtype=np.float64)
    total = 0.5 * float(np.sum(np.log(2.0 * np.pi * var)) * z.shape[0] + np.sum((delta * delta) / var))
    return float(total / float(max(1, z.shape[0] * z.shape[1])))


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


def format_layer3_acceptance_summary(result: dict[str, object]) -> str:
    quality = dict(result.get("canonical_quality_metrics", {}))
    distances = dict(quality.get("predicted_channel_distance", {}))
    generation = dict(result.get("learner_generation_quality_metrics", {}))
    gaussian_nll = dict(generation.get("visible_gaussian_nll_nats_per_feature", {}))
    population_ce = dict(generation.get("visible_population_cross_entropy_nats_per_probe", {}))
    raw_mae = dict(generation.get("visible_raw_feature_mae", {}))
    return "\n".join(
        [
            "# Layer 3 Canonical Quality Acceptance",
            "",
            f"- Layer: `{dict(result.get('public_layer', {})).get('layer_name', LEARNER_VALIDATION_STAGE.public_name)}`",
            f"- Decision: `{result.get('decision')}`",
            f"- Contract passed: `{str(bool(result.get('contract_passed'))).lower()}`",
            f"- Canonical source: `{dict(result.get('canonical_prediction_source', {})).get('source_name', 'unknown')}`",
            f"- Quality records: `{int(quality.get('num_records', 0))}`",
            f"- Classification accuracy: `{float(quality.get('classification_accuracy', 0.0)):.4f}`",
            f"- Incompatible predictions: `{int(quality.get('incompatible_prediction_count', 0))}`",
            f"- Mean predicted channel distance: `{float(distances.get('mean', 0.0)):.6f}`",
            f"- Max predicted channel distance: `{float(distances.get('max', 0.0)):.6f}`",
            f"- Learner visible Gaussian NLL: `{float(gaussian_nll.get('mean', 0.0)):.6f}` nats/feature",
            f"- Learner visible population CE: `{float(population_ce.get('mean', 0.0)):.6f}` nats/probe",
            f"- Learner visible raw-feature MAE: `{float(raw_mae.get('mean', 0.0)):.6f}`",
            "",
            "## Claim Boundary",
            "",
            "This stage is a resolver and acceptance artifact. It does not train another learner; it accepts Layer 3c multi-context predictions as canonical only after Layer 2, Layer 3b, Layer 3c, and Layer 3c validation gates pass. The generation-quality block is diagnostic: it scores held-out Z/X visible observations under the Layer 3c predicted-label generator and does not feed back into learner training.",
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
        "learner_generation_quality.json": result["learner_generation_quality_metrics"],
        "rejected_sources.json": result["rejected_sources"],
        "canonical_prediction_source.json": result["canonical_prediction_source"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_layer3_acceptance_summary(result))


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


def _mechanism_sort_key(name: str) -> tuple[int, str]:
    text = str(name)
    if text.startswith("M") and text[1:].isdigit():
        return (int(text[1:]), text)
    return (10_000, text)
