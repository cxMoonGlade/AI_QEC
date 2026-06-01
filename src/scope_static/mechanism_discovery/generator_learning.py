from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.protocols import LEARNER_VALIDATION_STAGE
from .artifacts import feature_schema_matches_stage3a as _feature_schema_matches_s3a
from .artifacts import load_json_object as _load_json
from .artifacts import load_stage3_evaluator_labels
from .artifacts import load_stage3a_frozen_visible_features
from .artifacts import resolve_teacher_dir
from .observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from .protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR
from .baselines import VARIANCE_FLOOR
from .baselines import _diag_log_prob
from .baselines import _logsumexp
from .discovery_model import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3B1_DIR
from .discovery_model import EVALUATOR_MODE_CONTROLLED_CATALOG
from .discovery_model import EVALUATOR_MODE_NO_ORACLE_LABELS
from .discovery_model import _normalize_evaluator_mode
from .discovery_model import _cap_folds
from .discovery_model import _valid_folds


STAGE_NAME = "Stage3C_prototype_generator_learning"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/PHYC_STAGE3_discovery/S3C_prototype_generator_learning"
DEFAULT_MAX_CV_FOLDS = 5
MIN_WEIGHT = 1.0e-12
PROBABILITY_METRICS = {"P0", "P1", "P00", "P01", "P10", "P11", "p_comp"}
PRIMARY_GENERATION_LIKELIHOOD_METRIC = "categorical_population_nll"
SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC = "gaussian_density_nll"


def run_stage3c_prototype_generator_learning(
    *,
    stage3a_dir: str | Path = DEFAULT_STAGE3A_DIR,
    stage3a5_dir: str | Path = DEFAULT_STAGE3A5_DIR,
    stage3b1_dir: str | Path = DEFAULT_STAGE3B1_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    teacher_dir: str | Path | None = None,
    max_cv_folds: int | None = DEFAULT_MAX_CV_FOLDS,
    variance_floor: float = VARIANCE_FLOOR,
    evaluator_mode: str = EVALUATOR_MODE_CONTROLLED_CATALOG,
) -> dict[str, object]:
    """Score heldout visible generation from learned Stage 3 assignments.

    The learner-side generator consumes the frozen Stage 3A visible matrix and
    Stage 3B.1 learned assignments. Mechanism labels are loaded only after the
    predicted-assignment and null generators are fit, for the evaluator-only
    oracle comparator.
    """

    mode = _normalize_evaluator_mode(evaluator_mode)
    s3a = Path(stage3a_dir)
    s3a5 = Path(stage3a5_dir)
    s3b1 = Path(stage3b1_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    s3a_metrics = _load_json(s3a / "metrics.json")
    s3a5_metrics = _load_json(s3a5 / "metrics.json") if mode == EVALUATOR_MODE_CONTROLLED_CATALOG else _no_oracle_stage3a5_metrics()
    s3b1_metrics = _load_json(s3b1 / "metrics.json")
    teacher = resolve_teacher_dir(s3a_metrics, teacher_dir) if mode == EVALUATOR_MODE_CONTROLLED_CATALOG else None

    x, feature_names, feature_matrix = load_stage3a_frozen_visible_features(s3a)
    responsibilities = _load_stage3b1_assignments(s3b1, record_count=int(x.shape[0]))
    feature_match = _feature_schema_matches_s3a(s3a, feature_names)
    split_manifest = dict(s3a_metrics.get("split_manifest", {})) if isinstance(s3a_metrics.get("split_manifest", {}), dict) else {}
    all_folds = _valid_folds(split_manifest, record_count=int(x.shape[0]))
    folds = _cap_folds(all_folds, max_cv_folds=max_cv_folds)
    if not folds:
        folds = [{"train_indices": list(range(int(x.shape[0]))), "validation_indices": [], "test_indices": list(range(int(x.shape[0])))}]

    predicted = evaluate_predicted_assignment_generation(
        x,
        responsibilities,
        feature_names=feature_names,
        folds=folds,
        variance_floor=float(variance_floor),
    )
    global_null = evaluate_global_null_generation(
        x,
        feature_names=feature_names,
        folds=folds,
        variance_floor=float(variance_floor),
    )
    mean_only = evaluate_mean_only_generation(
        x,
        feature_names=feature_names,
        folds=folds,
    )

    if mode == EVALUATOR_MODE_CONTROLLED_CATALOG:
        evaluator = load_stage3_evaluator_labels(s3a, teacher)
        labels = evaluator.exact_labels
        if len(labels) != int(x.shape[0]):
            raise ValueError(f"Stage 3A frozen feature row count {x.shape[0]} does not match evaluator label count {len(labels)}")
        class_names = evaluator.exact_class_names
        oracle = evaluate_oracle_assignment_comparator(
            x,
            labels,
            class_names=class_names,
            feature_names=feature_names,
            folds=folds,
            variance_floor=float(variance_floor),
        )
    else:
        oracle = skipped_oracle_assignment_comparator(feature_names=feature_names, folds=folds)

    prototype_metrics = prototype_generation_metrics(
        predicted_assignment_metrics=predicted,
        global_null_metrics=global_null,
        mean_only_baseline_metrics=mean_only,
        oracle_assignment_comparator_metrics=oracle,
    )
    leakage = generator_leakage_audit(s3b1_metrics=s3b1_metrics, evaluator_mode=mode)
    acceptance = stage3c_acceptance_audit(
        s3a_metrics=s3a_metrics,
        s3a5_metrics=s3a5_metrics,
        s3b1_metrics=s3b1_metrics,
        feature_match=feature_match,
        feature_matrix=feature_matrix,
        responsibilities=responsibilities,
        predicted_assignment_metrics=predicted,
        global_null_metrics=global_null,
        mean_only_baseline_metrics=mean_only,
        oracle_assignment_comparator_metrics=oracle,
        leakage_audit=leakage,
        evaluator_mode=mode,
    )
    result = {
        "schema": "scope_static_stage3c_prototype_generator_learning_v1",
        "stage": STAGE_NAME,
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="prototype_generator_learning"),
        "stage3a_dir": str(s3a),
        "stage3a5_dir": None if mode == EVALUATOR_MODE_NO_ORACLE_LABELS else str(s3a5),
        "stage3b1_dir": str(s3b1),
        "teacher_dir": None if teacher is None else str(teacher),
        "output_dir": str(output),
        "claim_boundary": {
            "trains_supervised_classifier": False,
            "uses_mechanism_labels_for_predicted_assignment_generator": False,
            "uses_mechanism_labels_for_model_selection": False,
            "trains_from_stage3a_frozen_visible_features": True,
            "uses_stage3b1_learned_assignments": True,
            "rebuilds_visible_features_from_oracle_records_for_fit": False,
            "oracle_assignment_comparator_evaluator_only": mode == EVALUATOR_MODE_CONTROLLED_CATALOG,
            "oracle_assignment_comparator_skipped": mode == EVALUATOR_MODE_NO_ORACLE_LABELS,
            "conditional_visible_replay_not_unconditional_future_prediction": True,
            "discovers_cptp_gksl_channels": False,
        },
        "config": {
            "stage3a_dir": str(s3a),
            "stage3a5_dir": None if mode == EVALUATOR_MODE_NO_ORACLE_LABELS else str(s3a5),
            "stage3b1_dir": str(s3b1),
            "teacher_dir": None if teacher is None else str(teacher),
            "output_dir": str(output),
            "max_cv_folds": None if max_cv_folds is None else int(max_cv_folds),
            "variance_floor": float(variance_floor),
            "evaluator_mode": mode,
        },
        "visible_feature_matrix": feature_matrix,
        "feature_schema_match_audit": feature_match,
        "heldout_protocol": heldout_protocol_artifact(all_folds=all_folds, evaluated_folds=folds, max_cv_folds=max_cv_folds),
        "assignment_source_audit": assignment_source_audit(s3b1_dir=s3b1, responsibilities=responsibilities),
        "prototype_generation_metrics": prototype_metrics,
        "predicted_assignment_metrics": predicted,
        "oracle_assignment_comparator_metrics": oracle,
        "global_null_metrics": global_null,
        "mean_only_baseline_metrics": mean_only,
        "leakage_audit": leakage,
        "acceptance_audit": acceptance,
        "decision": "stage3c_prototype_generator_learning_completed" if acceptance["passed"] else "stage3c_prototype_generator_learning_failed",
    }
    _write_outputs(output, result)
    return result


def evaluate_predicted_assignment_generation(
    x: np.ndarray,
    responsibilities: np.ndarray,
    *,
    feature_names: list[str],
    folds: list[dict[str, list[int]]],
    variance_floor: float,
) -> dict[str, object]:
    fold_rows = []
    y_rows = []
    pred_rows = []
    nll_rows = []
    for fold_idx, fold in enumerate(folds):
        train_idx = _indices(fold.get("train_indices", []), record_count=int(x.shape[0]))
        heldout_idx = _heldout_indices(fold, record_count=int(x.shape[0]))
        if train_idx.size == 0 or heldout_idx.size == 0:
            continue
        params = _fit_responsibility_generator(x[train_idx], responsibilities[train_idx], variance_floor=float(variance_floor))
        pred_mean = _responsibility_prediction_mean(responsibilities[heldout_idx], params["means"])
        nll = _conditional_responsibility_nll(x[heldout_idx], responsibilities[heldout_idx], params["means"], params["variances"])
        metrics = _score_generation(x[heldout_idx], pred_mean, nll, feature_names)
        fold_rows.append(
            {
                "fold": int(fold_idx),
                "train_count": int(train_idx.size),
                "heldout_count": int(heldout_idx.size),
                "active_prototype_count": int(params["active_prototype_count"]),
                **metrics,
            }
        )
        y_rows.append(x[heldout_idx])
        pred_rows.append(pred_mean)
        nll_rows.append(nll)
    return _generation_artifact(
        schema="scope_static_stage3c_predicted_assignment_metrics_v1",
        model_name="predicted_assignment_generator",
        description="Fold-local diagonal visible generator conditioned on Stage 3B.1 learned assignment probabilities.",
        feature_names=feature_names,
        y_rows=y_rows,
        pred_rows=pred_rows,
        nll_rows=nll_rows,
        fold_rows=fold_rows,
        uses_evaluator_labels=False,
    )


def evaluate_global_null_generation(
    x: np.ndarray,
    *,
    feature_names: list[str],
    folds: list[dict[str, list[int]]],
    variance_floor: float,
) -> dict[str, object]:
    fold_rows = []
    y_rows = []
    pred_rows = []
    nll_rows = []
    for fold_idx, fold in enumerate(folds):
        train_idx = _indices(fold.get("train_indices", []), record_count=int(x.shape[0]))
        heldout_idx = _heldout_indices(fold, record_count=int(x.shape[0]))
        if train_idx.size == 0 or heldout_idx.size == 0:
            continue
        mean, variance = _fit_global_generator(x[train_idx], variance_floor=float(variance_floor))
        pred_mean = np.tile(mean[None, :], (int(heldout_idx.size), 1))
        nll = -_diag_log_prob(x[heldout_idx], mean[None, :], variance[None, :])[:, 0]
        metrics = _score_generation(x[heldout_idx], pred_mean, nll, feature_names)
        fold_rows.append({"fold": int(fold_idx), "train_count": int(train_idx.size), "heldout_count": int(heldout_idx.size), **metrics})
        y_rows.append(x[heldout_idx])
        pred_rows.append(pred_mean)
        nll_rows.append(nll)
    return _generation_artifact(
        schema="scope_static_stage3c_global_null_metrics_v1",
        model_name="global_null_diagonal_gaussian",
        description="One train-fold visible mean and diagonal covariance for every heldout instance.",
        feature_names=feature_names,
        y_rows=y_rows,
        pred_rows=pred_rows,
        nll_rows=nll_rows,
        fold_rows=fold_rows,
        uses_evaluator_labels=False,
    )


def evaluate_mean_only_generation(
    x: np.ndarray,
    *,
    feature_names: list[str],
    folds: list[dict[str, list[int]]],
) -> dict[str, object]:
    fold_rows = []
    y_rows = []
    pred_rows = []
    for fold_idx, fold in enumerate(folds):
        train_idx = _indices(fold.get("train_indices", []), record_count=int(x.shape[0]))
        heldout_idx = _heldout_indices(fold, record_count=int(x.shape[0]))
        if train_idx.size == 0 or heldout_idx.size == 0:
            continue
        mean = np.mean(x[train_idx], axis=0)
        pred_mean = np.tile(mean[None, :], (int(heldout_idx.size), 1))
        metrics = _score_generation(x[heldout_idx], pred_mean, np.zeros(int(heldout_idx.size), dtype=np.float64), feature_names)
        metrics["gaussian_nll"] = None
        fold_rows.append({"fold": int(fold_idx), "train_count": int(train_idx.size), "heldout_count": int(heldout_idx.size), **metrics})
        y_rows.append(x[heldout_idx])
        pred_rows.append(pred_mean)
    return _generation_artifact(
        schema="scope_static_stage3c_mean_only_baseline_metrics_v1",
        model_name="mean_only_visible_baseline",
        description="One train-fold visible mean for every heldout instance; no density claim.",
        feature_names=feature_names,
        y_rows=y_rows,
        pred_rows=pred_rows,
        nll_rows=[],
        fold_rows=fold_rows,
        uses_evaluator_labels=False,
    )


def evaluate_oracle_assignment_comparator(
    x: np.ndarray,
    labels: list[str],
    *,
    class_names: list[str],
    feature_names: list[str],
    folds: list[dict[str, list[int]]],
    variance_floor: float,
) -> dict[str, object]:
    fold_rows = []
    y_rows = []
    pred_rows = []
    nll_rows = []
    label_array = np.asarray(labels, dtype=object)
    for fold_idx, fold in enumerate(folds):
        train_idx = _indices(fold.get("train_indices", []), record_count=int(x.shape[0]))
        heldout_idx = _heldout_indices(fold, record_count=int(x.shape[0]))
        if train_idx.size == 0 or heldout_idx.size == 0:
            continue
        means, variances = _fit_label_generator(
            x[train_idx],
            label_array[train_idx].tolist(),
            class_names=class_names,
            variance_floor=float(variance_floor),
        )
        label_to_row = {label: idx for idx, label in enumerate(class_names)}
        component_rows = np.asarray([label_to_row[str(label_array[idx])] for idx in heldout_idx.tolist()], dtype=np.int64)
        pred_mean = means[component_rows]
        nll = -_diag_log_prob(x[heldout_idx], means, variances)[np.arange(int(heldout_idx.size)), component_rows]
        metrics = _score_generation(x[heldout_idx], pred_mean, nll, feature_names)
        fold_rows.append(
            {
                "fold": int(fold_idx),
                "train_count": int(train_idx.size),
                "heldout_count": int(heldout_idx.size),
                "oracle_class_count": int(len(class_names)),
                **metrics,
            }
        )
        y_rows.append(x[heldout_idx])
        pred_rows.append(pred_mean)
        nll_rows.append(nll)
    out = _generation_artifact(
        schema="scope_static_stage3c_oracle_assignment_comparator_metrics_v1",
        model_name="oracle_assignment_comparator",
        description="Evaluator-only train-fold class prototypes selected by heldout oracle label.",
        feature_names=feature_names,
        y_rows=y_rows,
        pred_rows=pred_rows,
        nll_rows=nll_rows,
        fold_rows=fold_rows,
        uses_evaluator_labels=True,
    )
    out["evaluator_only"] = True
    out["uses_oracle_labels_for_comparator"] = True
    out["used_for_acceptance_model_selection"] = False
    return out


def skipped_oracle_assignment_comparator(*, feature_names: list[str], folds: list[dict[str, list[int]]]) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3c_oracle_assignment_comparator_metrics_v1",
        "model_name": "oracle_assignment_comparator",
        "description": "Skipped because no controlled-catalog evaluator labels are available.",
        "primary_generation_likelihood_metric": PRIMARY_GENERATION_LIKELIHOOD_METRIC,
        "secondary_continuous_density_diagnostic": SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC,
        "uses_evaluator_labels": False,
        "uses_channels_ptms_kraus": False,
        "heldout_row_count": 0,
        "feature_count": int(len(feature_names)),
        "overall": {
            "categorical_population_nll": None,
            "categorical_population_group_count": 0,
            "gaussian_density_nll": None,
            "gaussian_nll": None,
            "raw_visible_feature_mae": None,
            "population_mae": None,
            "population_cross_entropy": None,
            "expectation_mae": None,
            "probability_feature_count": 0,
            "expectation_feature_count": 0,
        },
        "fold_metrics": [],
        "evaluator_only": False,
        "skipped": True,
        "evaluator_mode": EVALUATOR_MODE_NO_ORACLE_LABELS,
        "used_for_acceptance_model_selection": False,
        "available_fold_count": int(len(folds)),
    }


def prototype_generation_metrics(
    *,
    predicted_assignment_metrics: dict[str, object],
    global_null_metrics: dict[str, object],
    mean_only_baseline_metrics: dict[str, object],
    oracle_assignment_comparator_metrics: dict[str, object],
) -> dict[str, object]:
    predicted = dict(predicted_assignment_metrics.get("overall", {}))
    global_null = dict(global_null_metrics.get("overall", {}))
    mean_only = dict(mean_only_baseline_metrics.get("overall", {}))
    oracle = dict(oracle_assignment_comparator_metrics.get("overall", {}))
    return {
        "schema": "scope_static_stage3c_prototype_generation_metrics_v1",
        "heldout_generation_protocol": "fold-local generators fit on Stage 3A train folds and scored on validation+test heldout rows",
        "primary_generation_likelihood_metric": PRIMARY_GENERATION_LIKELIHOOD_METRIC,
        "secondary_continuous_density_diagnostic": SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC,
        "primary_likelihood_report": primary_likelihood_report(
            predicted_assignment=predicted,
            oracle_assignment=oracle,
            global_null=global_null,
            mean_only=mean_only,
        ),
        "predicted_assignment_model": predicted,
        "global_null_model": global_null,
        "mean_only_baseline": mean_only,
        "oracle_assignment_comparator_evaluator_only": oracle,
        "global_null_lift": _lift(predicted, global_null),
        "mean_only_lift": _lift(predicted, mean_only),
        "oracle_comparator_gap": _gap(predicted, oracle),
    }


def primary_likelihood_report(
    *,
    predicted_assignment: dict[str, object],
    oracle_assignment: dict[str, object],
    global_null: dict[str, object],
    mean_only: dict[str, object],
) -> dict[str, object]:
    metric = PRIMARY_GENERATION_LIKELIHOOD_METRIC
    return {
        "schema": "scope_static_stage3c_primary_likelihood_report_v1",
        "metric": metric,
        "metric_kind": "positive_discrete_probability_mass_nll",
        "lower_is_better": True,
        "predicted_assignment": _optional_float(predicted_assignment.get(metric)),
        "oracle_assignment_comparator": _optional_float(oracle_assignment.get(metric)),
        "predicted_minus_oracle_gap": _optional_difference(predicted_assignment.get(metric), oracle_assignment.get(metric)),
        "global_null": _optional_float(global_null.get(metric)),
        "mean_only_baseline": _optional_float(mean_only.get(metric)),
        "global_null_minus_predicted_lift": _optional_difference(global_null.get(metric), predicted_assignment.get(metric)),
        "mean_only_minus_predicted_lift": _optional_difference(mean_only.get(metric), predicted_assignment.get(metric)),
    }


def assignment_source_audit(*, s3b1_dir: Path, responsibilities: np.ndarray) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3c_assignment_source_audit_v1",
        "assignment_path": str(s3b1_dir / "learned_assignments.npy"),
        "source_stage": "Stage 3B.1",
        "row_count": int(responsibilities.shape[0]),
        "prototype_count": int(responsibilities.shape[1]) if responsibilities.ndim == 2 else 0,
        "row_stochastic": bool(responsibilities.size == 0 or np.allclose(np.sum(responsibilities, axis=1), 1.0)),
        "uses_evaluator_labels": False,
        "assignment_is_visible_only_b1_output": True,
    }


def heldout_protocol_artifact(
    *,
    all_folds: list[dict[str, list[int]]],
    evaluated_folds: list[dict[str, list[int]]],
    max_cv_folds: int | None,
) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3c_heldout_protocol_v1",
        "available_fold_count": int(len(all_folds)),
        "evaluated_fold_count": int(len(evaluated_folds)),
        "max_cv_folds": None if max_cv_folds is None else int(max_cv_folds),
        "heldout_rows": "validation_indices plus test_indices from each evaluated Stage 3A fold",
        "fold_selection_uses_labels": False,
    }


def generator_leakage_audit(
    *,
    s3b1_metrics: dict[str, object],
    evaluator_mode: str = EVALUATOR_MODE_CONTROLLED_CATALOG,
) -> dict[str, object]:
    mode = _normalize_evaluator_mode(evaluator_mode)
    boundary = dict(s3b1_metrics.get("claim_boundary", {})) if isinstance(s3b1_metrics.get("claim_boundary", {}), dict) else {}
    checks = {
        "predicted_generator_uses_mechanism_labels": False,
        "predicted_generator_uses_channels_ptms_kraus": False,
        "predicted_generator_rebuilds_features_from_oracle_records": False,
        "predicted_generator_uses_teacher_self_features": False,
        "oracle_comparator_is_evaluator_only": mode == EVALUATOR_MODE_CONTROLLED_CATALOG,
        "oracle_comparator_skipped_without_oracle_labels": mode == EVALUATOR_MODE_NO_ORACLE_LABELS,
        "stage3b1_assignments_trained_from_frozen_visible_features": bool(boundary.get("trains_from_stage3a_frozen_visible_features", False)),
        "stage3b1_labels_not_used_for_fit": not bool(boundary.get("uses_mechanism_labels_for_fit", True)),
        "stage3b1_labels_not_used_for_model_selection": not bool(boundary.get("uses_mechanism_labels_for_model_selection", True)),
    }
    return {
        "schema": "scope_static_stage3c_leakage_audit_v1",
        "passed": bool(
            not checks["predicted_generator_uses_mechanism_labels"]
            and not checks["predicted_generator_uses_channels_ptms_kraus"]
            and not checks["predicted_generator_rebuilds_features_from_oracle_records"]
            and not checks["predicted_generator_uses_teacher_self_features"]
            and (checks["oracle_comparator_is_evaluator_only"] or checks["oracle_comparator_skipped_without_oracle_labels"])
            and checks["stage3b1_assignments_trained_from_frozen_visible_features"]
            and checks["stage3b1_labels_not_used_for_fit"]
            and checks["stage3b1_labels_not_used_for_model_selection"]
        ),
        "evaluator_mode": mode,
        "checks": checks,
    }


def stage3c_acceptance_audit(
    *,
    s3a_metrics: dict[str, object],
    s3a5_metrics: dict[str, object],
    s3b1_metrics: dict[str, object],
    feature_match: dict[str, object],
    feature_matrix: dict[str, object],
    responsibilities: np.ndarray,
    predicted_assignment_metrics: dict[str, object],
    global_null_metrics: dict[str, object],
    mean_only_baseline_metrics: dict[str, object],
    oracle_assignment_comparator_metrics: dict[str, object],
    leakage_audit: dict[str, object],
    evaluator_mode: str = EVALUATOR_MODE_CONTROLLED_CATALOG,
) -> dict[str, object]:
    mode = _normalize_evaluator_mode(evaluator_mode)
    predicted = dict(predicted_assignment_metrics.get("overall", {}))
    global_null = dict(global_null_metrics.get("overall", {}))
    mean_only = dict(mean_only_baseline_metrics.get("overall", {}))
    oracle = dict(oracle_assignment_comparator_metrics.get("overall", {}))
    b1_acceptance = dict(s3b1_metrics.get("acceptance_audit", {})) if isinstance(s3b1_metrics.get("acceptance_audit", {}), dict) else {}
    checks = {
        "stage3a_acceptance_passed": bool(dict(s3a_metrics.get("acceptance_audit", {})).get("passed", False)),
        "stage3a5_acceptance_passed": (
            True if mode == EVALUATOR_MODE_NO_ORACLE_LABELS else bool(dict(s3a5_metrics.get("acceptance_audit", {})).get("passed", False))
        ),
        "stage3b1_acceptance_passed": bool(b1_acceptance.get("passed", False)),
        "approved_feature_schema_matches_stage3a": bool(feature_match.get("passed", False)),
        "uses_stage3a_frozen_visible_features": bool(feature_matrix.get("loaded_from_stage3a_artifact", False)),
        "assignment_matrix_row_stochastic": bool(responsibilities.size == 0 or np.allclose(np.sum(responsibilities, axis=1), 1.0)),
        "predicted_assignment_metrics_reported": bool(predicted),
        "oracle_assignment_comparator_reported_separately": (
            bool(oracle_assignment_comparator_metrics.get("evaluator_only", False))
            if mode == EVALUATOR_MODE_CONTROLLED_CATALOG
            else bool(oracle_assignment_comparator_metrics.get("skipped", False))
        ),
        "oracle_comparator_not_used_for_model_selection": not bool(oracle_assignment_comparator_metrics.get("used_for_acceptance_model_selection", True)),
        "primary_categorical_population_nll_reported": predicted.get(PRIMARY_GENERATION_LIKELIHOOD_METRIC) is not None,
        "oracle_categorical_population_nll_reported": (
            True
            if mode == EVALUATOR_MODE_NO_ORACLE_LABELS
            else oracle.get(PRIMARY_GENERATION_LIKELIHOOD_METRIC) is not None
        ),
        "categorical_population_group_count_positive": int(predicted.get("categorical_population_group_count", 0)) > 0,
        "heldout_generation_beats_global_null_categorical_population_nll": _metric_less(
            predicted,
            global_null,
            PRIMARY_GENERATION_LIKELIHOOD_METRIC,
        ),
        "heldout_generation_beats_global_null_mae": _metric_less(predicted, global_null, "raw_visible_feature_mae"),
        "heldout_generation_beats_mean_only_mae": _metric_less(predicted, mean_only, "raw_visible_feature_mae"),
        "oracle_comparator_not_worse_than_predicted_assignment_mae": (
            True if mode == EVALUATOR_MODE_NO_ORACLE_LABELS else _metric_less_or_equal(oracle, predicted, "raw_visible_feature_mae")
        ),
        "leakage_audit_passed": bool(leakage_audit.get("passed", False)),
        "does_not_claim_arbitrary_cptp_gksl_learning": True,
    }
    return {
        "schema": "scope_static_stage3c_acceptance_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
    }


def _no_oracle_stage3a5_metrics() -> dict[str, object]:
    return {
        "schema": "scope_static_stage3a5_no_oracle_placeholder_v1",
        "evaluator_mode": EVALUATOR_MODE_NO_ORACLE_LABELS,
        "acceptance_audit": {"passed": True, "checks": {"stage3a5_not_required_without_oracle_labels": True}},
    }


def _fit_responsibility_generator(x: np.ndarray, responsibilities: np.ndarray, *, variance_floor: float) -> dict[str, np.ndarray | int]:
    resp = _normalize_rows(responsibilities)
    n, d = x.shape
    k = int(resp.shape[1]) if resp.ndim == 2 else 1
    global_mean, global_var = _fit_global_generator(x, variance_floor=float(variance_floor))
    means = np.tile(global_mean[None, :], (k, 1))
    variances = np.tile(global_var[None, :], (k, 1))
    nk = np.sum(resp, axis=0) if resp.size else np.zeros(k, dtype=np.float64)
    for idx in range(k):
        if float(nk[idx]) <= MIN_WEIGHT:
            continue
        means[idx] = (resp[:, idx][:, None] * x).sum(axis=0) / float(nk[idx])
        diff = x - means[idx]
        variances[idx] = np.maximum((resp[:, idx][:, None] * diff * diff).sum(axis=0) / float(nk[idx]), float(variance_floor))
    return {"means": means, "variances": variances, "active_prototype_count": int(np.sum(nk > MIN_WEIGHT)), "train_count": int(n)}


def _fit_global_generator(x: np.ndarray, *, variance_floor: float) -> tuple[np.ndarray, np.ndarray]:
    if x.shape[0] == 0:
        return np.zeros(x.shape[1], dtype=np.float64), np.ones(x.shape[1], dtype=np.float64)
    mean = np.mean(x, axis=0)
    variance = np.maximum(np.var(x, axis=0), float(variance_floor))
    return mean, variance


def _fit_label_generator(
    x: np.ndarray,
    labels: list[str],
    *,
    class_names: list[str],
    variance_floor: float,
) -> tuple[np.ndarray, np.ndarray]:
    global_mean, global_var = _fit_global_generator(x, variance_floor=float(variance_floor))
    means = np.tile(global_mean[None, :], (len(class_names), 1))
    variances = np.tile(global_var[None, :], (len(class_names), 1))
    label_array = np.asarray(labels, dtype=object)
    for row, label in enumerate(class_names):
        mask = label_array == label
        if not bool(np.any(mask)):
            continue
        means[row] = np.mean(x[mask], axis=0)
        variances[row] = np.maximum(np.var(x[mask], axis=0), float(variance_floor))
    return means, variances


def _responsibility_prediction_mean(responsibilities: np.ndarray, means: np.ndarray) -> np.ndarray:
    return _normalize_rows(responsibilities) @ np.asarray(means, dtype=np.float64)


def _conditional_responsibility_nll(
    x: np.ndarray,
    responsibilities: np.ndarray,
    means: np.ndarray,
    variances: np.ndarray,
) -> np.ndarray:
    if x.shape[0] == 0:
        return np.zeros(0, dtype=np.float64)
    resp = _normalize_rows(responsibilities)
    log_prob = _diag_log_prob(x, np.asarray(means, dtype=np.float64), np.asarray(variances, dtype=np.float64))
    log_resp = np.log(np.maximum(resp, MIN_WEIGHT))
    return -_logsumexp(log_prob + log_resp, axis=1)


def _score_generation(y: np.ndarray, predicted_mean: np.ndarray, nll: np.ndarray, feature_names: list[str]) -> dict[str, object]:
    probability_mask, expectation_mask = _feature_masks(feature_names)
    probability_groups = _probability_groups(feature_names)
    raw_mae = float(np.mean(np.abs(y - predicted_mean))) if y.size else 0.0
    probability_mae = _masked_mae(y, predicted_mean, probability_mask)
    expectation_mae = _masked_mae(y, predicted_mean, expectation_mask)
    gaussian_density_nll = float(np.mean(nll)) if nll.size else 0.0
    return {
        "categorical_population_nll": _categorical_population_nll(y, predicted_mean, probability_groups),
        "categorical_population_group_count": int(len(probability_groups)),
        "gaussian_density_nll": gaussian_density_nll,
        "gaussian_nll": gaussian_density_nll,
        "raw_visible_feature_mae": raw_mae,
        "population_mae": probability_mae,
        "population_cross_entropy": _population_cross_entropy(y, predicted_mean, probability_mask),
        "expectation_mae": expectation_mae,
        "probability_feature_count": int(np.sum(probability_mask)),
        "expectation_feature_count": int(np.sum(expectation_mask)),
    }


def _generation_artifact(
    *,
    schema: str,
    model_name: str,
    description: str,
    feature_names: list[str],
    y_rows: list[np.ndarray],
    pred_rows: list[np.ndarray],
    nll_rows: list[np.ndarray],
    fold_rows: list[dict[str, object]],
    uses_evaluator_labels: bool,
) -> dict[str, object]:
    y = np.concatenate(y_rows, axis=0) if y_rows else np.zeros((0, len(feature_names)), dtype=np.float64)
    pred = np.concatenate(pred_rows, axis=0) if pred_rows else np.zeros((0, len(feature_names)), dtype=np.float64)
    nll = np.concatenate(nll_rows, axis=0) if nll_rows else np.zeros(0, dtype=np.float64)
    overall = _score_generation(y, pred, nll, feature_names)
    if not nll_rows:
        overall["gaussian_nll"] = None
        overall["gaussian_density_nll"] = None
    return {
        "schema": schema,
        "model_name": str(model_name),
        "description": str(description),
        "primary_generation_likelihood_metric": PRIMARY_GENERATION_LIKELIHOOD_METRIC,
        "secondary_continuous_density_diagnostic": SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC,
        "uses_evaluator_labels": bool(uses_evaluator_labels),
        "uses_channels_ptms_kraus": False,
        "heldout_row_count": int(y.shape[0]),
        "feature_count": int(y.shape[1]) if y.ndim == 2 else 0,
        "overall": overall,
        "fold_metrics": fold_rows,
    }


def _feature_masks(feature_names: list[str]) -> tuple[np.ndarray, np.ndarray]:
    probability = []
    expectation = []
    for name in feature_names:
        text = str(name)
        metric = text.rsplit("__", 1)[-1]
        probability.append(text.startswith("raw__") and "__se_" not in text and metric in PROBABILITY_METRICS)
        expectation.append(text.startswith("raw__") and "__se_" not in text and metric.startswith("E_"))
    return np.asarray(probability, dtype=bool), np.asarray(expectation, dtype=bool)


def _masked_mae(y: np.ndarray, predicted: np.ndarray, mask: np.ndarray) -> float:
    if y.shape[0] == 0 or not bool(np.any(mask)):
        return 0.0
    return float(np.mean(np.abs(y[:, mask] - predicted[:, mask])))


def _population_cross_entropy(y: np.ndarray, predicted: np.ndarray, mask: np.ndarray) -> float:
    if y.shape[0] == 0 or not bool(np.any(mask)):
        return 0.0
    target = np.clip(y[:, mask], 0.0, 1.0)
    prob = np.clip(predicted[:, mask], 1.0e-9, 1.0 - 1.0e-9)
    ce = -(target * np.log(prob) + (1.0 - target) * np.log(1.0 - prob))
    return float(np.mean(ce))


def _probability_groups(feature_names: list[str]) -> list[dict[str, object]]:
    by_base: dict[str, dict[str, int]] = {}
    for idx, name in enumerate(feature_names):
        text = str(name)
        if not text.startswith("raw__") or "__se_" in text:
            continue
        base, metric = text.rsplit("__", 1)
        by_base.setdefault(base, {})[metric] = int(idx)
    groups: list[dict[str, object]] = []
    for base in sorted(by_base):
        columns = by_base[base]
        if {"P0", "P1"}.issubset(columns):
            groups.append(
                {
                    "base": base,
                    "outcome_columns": [int(columns["P0"]), int(columns["P1"])],
                    "other_mass_column": None if "p_comp" not in columns else int(columns["p_comp"]),
                }
            )
        elif {"P00", "P01", "P10", "P11"}.issubset(columns):
            groups.append(
                {
                    "base": base,
                    "outcome_columns": [int(columns["P00"]), int(columns["P01"]), int(columns["P10"]), int(columns["P11"])],
                    "other_mass_column": None if "p_comp" not in columns else int(columns["p_comp"]),
                }
            )
    return groups


def _categorical_population_nll(y: np.ndarray, predicted: np.ndarray, groups: list[dict[str, object]]) -> float:
    if y.shape[0] == 0 or not groups:
        return 0.0
    total = 0.0
    group_rows = 0
    for group in groups:
        cols = np.asarray(group.get("outcome_columns", []), dtype=np.int64)
        if cols.size == 0:
            continue
        target = np.clip(y[:, cols], 0.0, 1.0)
        prob = np.clip(predicted[:, cols], 0.0, 1.0)
        other_col = group.get("other_mass_column")
        if other_col is not None:
            idx = int(other_col)
            target_other = np.maximum(0.0, 1.0 - np.clip(y[:, idx], 0.0, 1.0))[:, None]
            prob_other = np.maximum(0.0, 1.0 - np.clip(predicted[:, idx], 0.0, 1.0))[:, None]
            target = np.concatenate([target, target_other], axis=1)
            prob = np.concatenate([prob, prob_other], axis=1)
        target = target / np.maximum(np.sum(target, axis=1, keepdims=True), MIN_WEIGHT)
        prob = prob / np.maximum(np.sum(prob, axis=1, keepdims=True), MIN_WEIGHT)
        prob = np.clip(prob, 1.0e-12, 1.0)
        total += float(np.sum(-target * np.log(prob)))
        group_rows += int(target.shape[0])
    return float(total / float(max(1, group_rows)))


def _load_stage3b1_assignments(stage3b1_dir: Path, *, record_count: int) -> np.ndarray:
    path = stage3b1_dir / "learned_assignments.npy"
    if not path.exists():
        raise FileNotFoundError(f"missing Stage 3B.1 assignment matrix: {path}")
    responsibilities = np.asarray(np.load(path), dtype=np.float64)
    if responsibilities.ndim != 2:
        raise ValueError(f"{path} must be a 2D assignment matrix")
    if int(responsibilities.shape[0]) != int(record_count):
        raise ValueError(f"{path} row count {responsibilities.shape[0]} does not match Stage 3A record count {record_count}")
    if responsibilities.shape[1] == 0:
        raise ValueError(f"{path} must contain at least one prototype column")
    return _normalize_rows(responsibilities)


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    arr = np.asarray(matrix, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError("assignment matrix must be 2D")
    clipped = np.maximum(arr, 0.0)
    row_sum = np.sum(clipped, axis=1, keepdims=True)
    if np.any(row_sum <= 0.0):
        raise ValueError("assignment matrix contains an empty row")
    return clipped / row_sum


def _indices(values: object, *, record_count: int) -> np.ndarray:
    if not isinstance(values, list):
        return np.zeros(0, dtype=np.int64)
    out = []
    for item in values:
        idx = int(item)
        if 0 <= idx < int(record_count):
            out.append(idx)
    return np.asarray(sorted(set(out)), dtype=np.int64)


def _heldout_indices(fold: dict[str, list[int]], *, record_count: int) -> np.ndarray:
    values = []
    values.extend(fold.get("validation_indices", []))
    values.extend(fold.get("test_indices", []))
    return _indices(values, record_count=record_count)


def _metric_less(left: dict[str, object], right: dict[str, object], key: str) -> bool:
    if left.get(key) is None or right.get(key) is None:
        return False
    return bool(float(left.get(key, np.inf)) < float(right.get(key, np.inf)))


def _metric_less_or_equal(left: dict[str, object], right: dict[str, object], key: str) -> bool:
    if left.get(key) is None or right.get(key) is None:
        return False
    return bool(float(left.get(key, np.inf)) <= float(right.get(key, np.inf)) + 1.0e-12)


def _lift(predicted: dict[str, object], baseline: dict[str, object]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key in (
        "categorical_population_nll",
        "gaussian_density_nll",
        "gaussian_nll",
        "raw_visible_feature_mae",
        "population_cross_entropy",
        "population_mae",
        "expectation_mae",
    ):
        if predicted.get(key) is None or baseline.get(key) is None:
            out[f"{key}_reduction"] = None
            continue
        out[f"{key}_reduction"] = float(baseline[key]) - float(predicted[key])
    return out


def _gap(predicted: dict[str, object], oracle: dict[str, object]) -> dict[str, object]:
    out: dict[str, object] = {}
    for key in (
        "categorical_population_nll",
        "gaussian_density_nll",
        "gaussian_nll",
        "raw_visible_feature_mae",
        "population_cross_entropy",
        "population_mae",
        "expectation_mae",
    ):
        if predicted.get(key) is None or oracle.get(key) is None:
            out[f"{key}_gap"] = None
            continue
        out[f"{key}_gap"] = float(predicted[key]) - float(oracle[key])
    return out


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_difference(left: object, right: object) -> float | None:
    if left is None or right is None:
        return None
    return float(left) - float(right)


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "prototype_generation_metrics.json": result["prototype_generation_metrics"],
        "predicted_assignment_metrics.json": result["predicted_assignment_metrics"],
        "oracle_assignment_comparator_metrics.json": result["oracle_assignment_comparator_metrics"],
        "global_null_metrics.json": result["global_null_metrics"],
        "mean_only_baseline_metrics.json": result["mean_only_baseline_metrics"],
        "leakage_audit.json": result["leakage_audit"],
        "acceptance_audit.json": result["acceptance_audit"],
        "assignment_source_audit.json": result["assignment_source_audit"],
        "heldout_protocol.json": result["heldout_protocol"],
        "feature_schema_match_audit.json": result["feature_schema_match_audit"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    (output / "config.yaml").write_text(yaml.safe_dump({"stage3c_prototype_generator_learning": result["config"]}, sort_keys=False))
    (output / "summary.md").write_text(format_stage3c_summary(result))


def format_stage3c_summary(result: dict[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    predicted = dict(dict(result.get("predicted_assignment_metrics", {})).get("overall", {}))
    global_null = dict(dict(result.get("global_null_metrics", {})).get("overall", {}))
    oracle = dict(dict(result.get("oracle_assignment_comparator_metrics", {})).get("overall", {}))
    return "\n".join(
        [
            "# Stage 3C: Prototype And Generator Learning",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Predicted-assignment categorical population NLL: `{_format_metric(predicted.get('categorical_population_nll'))}`",
            f"- Oracle-comparator categorical population NLL: `{_format_metric(oracle.get('categorical_population_nll'))}`",
            f"- Predicted-minus-oracle categorical NLL gap: `{_format_metric(_optional_difference(predicted.get('categorical_population_nll'), oracle.get('categorical_population_nll')))}`",
            f"- Predicted-assignment Gaussian density NLL: `{_format_metric(predicted.get('gaussian_density_nll'))}`",
            f"- Global-null Gaussian density NLL: `{_format_metric(global_null.get('gaussian_density_nll'))}`",
            f"- Predicted-assignment raw MAE: `{_format_metric(predicted.get('raw_visible_feature_mae'))}`",
            f"- Oracle-comparator raw MAE: `{_format_metric(oracle.get('raw_visible_feature_mae'))}`",
            "",
            "## Claim Boundary",
            "",
            "Stage 3C scores conditional visible-generation replay from Stage 3B.1 learned assignments. Mechanism labels, channels, PTMs, Kraus matrices, teacher IDs, and oracle prototypes are not used by the predicted-assignment generator; oracle-label prototypes are reported only as evaluator-only comparators.",
            "",
        ]
    )


def _format_metric(value: object) -> str:
    if value is None:
        return "none"
    return f"{float(value):.6f}"
