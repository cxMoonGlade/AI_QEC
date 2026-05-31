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
from .baselines import VARIANCE_FLOOR
from .baselines import evaluate_cluster_assignments
from .discovery_model import DEFAULT_FINAL_TEMPERATURE
from .discovery_model import DEFAULT_INITIAL_TEMPERATURE
from .discovery_model import DEFAULT_MAX_ITER
from .discovery_model import DEFAULT_OPERATION_CONTEXT_WEIGHT
from .discovery_model import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3B1_DIR
from .discovery_model import MIN_COMPONENT_MASS
from .discovery_model import _apply_visible_feature_weights
from .discovery_model import _cap_folds
from .discovery_model import _context_groups_from_split_manifest
from .discovery_model import _fit_candidate_model
from .discovery_model import _model_responsibilities
from .discovery_model import _standardize_visible_features_with_values
from .discovery_model import _valid_folds
from .discovery_model import context_dependent_mechanism_diagnostics
from .generator_learning import DEFAULT_MAX_CV_FOLDS
from .generator_learning import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3C_DIR
from .generator_learning import PRIMARY_GENERATION_LIKELIHOOD_METRIC
from .generator_learning import SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC
from .generator_learning import evaluate_global_null_generation
from .generator_learning import evaluate_mean_only_generation
from .generator_learning import evaluate_predicted_assignment_generation
from .generator_learning import heldout_protocol_artifact
from .observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from .protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR


STAGE_NAME = "Stage3D4_k_stress_audit"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/PHYC_STAGE3_discovery/S3D4_k_stress_audit"
DEFAULT_SEED = 0
DEFAULT_UNDERCOMPLETE_FRACTION = 0.5
DEFAULT_OVERCOMPLETE_MULTIPLIER = 2.0
DEFAULT_MIN_SUCCESS_NMI = 0.9
DEFAULT_MIN_SUCCESS_ARI = 0.85
DEFAULT_MIN_SUCCESS_BA = 0.85
DEFAULT_MIN_UNDERCOMPLETE_NMI_GAP = 0.05
DEFAULT_MIN_GENERATION_NULL_LIFT = 1.0e-6


def run_stage3d4_k_stress_audit(
    *,
    stage3a_dir: str | Path = DEFAULT_STAGE3A_DIR,
    stage3a5_dir: str | Path = DEFAULT_STAGE3A5_DIR,
    stage3b1_dir: str | Path = DEFAULT_STAGE3B1_DIR,
    stage3c_dir: str | Path | None = DEFAULT_STAGE3C_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    teacher_dir: str | Path | None = None,
    seed: int = DEFAULT_SEED,
    max_iter: int = DEFAULT_MAX_ITER,
    max_cv_folds: int | None = DEFAULT_MAX_CV_FOLDS,
    initial_temperature: float = DEFAULT_INITIAL_TEMPERATURE,
    final_temperature: float = DEFAULT_FINAL_TEMPERATURE,
    variance_floor: float = VARIANCE_FLOOR,
    undercomplete_fraction: float = DEFAULT_UNDERCOMPLETE_FRACTION,
    overcomplete_multiplier: float = DEFAULT_OVERCOMPLETE_MULTIPLIER,
    min_success_nmi: float = DEFAULT_MIN_SUCCESS_NMI,
    min_success_ari: float = DEFAULT_MIN_SUCCESS_ARI,
    min_success_ba: float = DEFAULT_MIN_SUCCESS_BA,
    min_undercomplete_nmi_gap: float = DEFAULT_MIN_UNDERCOMPLETE_NMI_GAP,
    min_generation_null_lift: float = DEFAULT_MIN_GENERATION_NULL_LIFT,
    operation_context_weight: float = DEFAULT_OPERATION_CONTEXT_WEIGHT,
) -> dict[str, object]:
    """Run fixed-K undercomplete/exact/overcomplete discovery stress tests."""

    s3a = Path(stage3a_dir)
    s3a5 = Path(stage3a5_dir)
    s3b1 = Path(stage3b1_dir)
    s3c = None if stage3c_dir is None else Path(stage3c_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    s3a_metrics = _load_json(s3a / "metrics.json")
    s3a5_metrics = _load_json(s3a5 / "metrics.json")
    s3b1_metrics = _optional_json(s3b1 / "metrics.json")
    s3c_metrics = _optional_json(None if s3c is None else s3c / "metrics.json")
    teacher = resolve_teacher_dir(s3a_metrics, teacher_dir)

    x_raw, feature_names, feature_matrix = load_stage3a_frozen_visible_features(s3a)
    x, _standardization = _standardize_visible_features_with_values(x_raw)
    x, feature_weighting = _apply_visible_feature_weights(
        x,
        feature_names=feature_names,
        operation_context_weight=float(operation_context_weight),
    )
    feature_match = _feature_schema_matches_s3a(s3a, feature_names)
    split_manifest = dict(s3a_metrics.get("split_manifest", {})) if isinstance(s3a_metrics.get("split_manifest", {}), dict) else {}
    all_folds = _valid_folds(split_manifest, record_count=int(x_raw.shape[0]))
    folds = _cap_folds(all_folds, max_cv_folds=max_cv_folds)
    if not folds:
        folds = [{"train_indices": list(range(int(x_raw.shape[0]))), "validation_indices": [], "test_indices": list(range(int(x_raw.shape[0])))}]
    context_groups = _context_groups_from_split_manifest(split_manifest, record_count=int(x_raw.shape[0]))
    alias = dict(s3a5_metrics.get("oracle_alias_classes", {})) if isinstance(s3a5_metrics.get("oracle_alias_classes", {}), dict) else {}
    label_to_quotient = {str(k): str(v) for k, v in dict(alias.get("label_to_quotient", {})).items()}
    mechanism_scope = dict(s3a_metrics.get("mechanism_scope", {})) if isinstance(s3a_metrics.get("mechanism_scope", {}), dict) else {}
    class_count = int(mechanism_scope.get("class_count_evaluator_only", max(1, x_raw.shape[0])))
    quotient_class_count = int(alias.get("quotient_class_count", class_count))
    k_plan = k_stress_plan(
        record_count=int(x_raw.shape[0]),
        class_count=class_count,
        quotient_class_count=quotient_class_count,
        undercomplete_fraction=float(undercomplete_fraction),
        overcomplete_multiplier=float(overcomplete_multiplier),
    )

    fitted = []
    assignment_arrays: dict[str, np.ndarray] = {}
    model_summaries = []
    for run_index, run in enumerate(k_plan["runs"]):
        k = int(run["k"])
        model = _fit_candidate_model(
            x,
            context_groups=context_groups,
            model_family="diagonal_covariance_visible_prototype_mixture",
            k=k,
            seed=int(seed + 101 * run_index),
            max_iter=int(max_iter),
            initial_temperature=float(initial_temperature),
            final_temperature=float(final_temperature),
        )
        responsibilities = _model_responsibilities(
            x,
            context_groups=context_groups,
            model=model,
            temperature=float(final_temperature),
        )
        hard_assignments = np.argmax(responsibilities, axis=1).astype(np.int64) if responsibilities.size else np.zeros(0, dtype=np.int64)
        predicted = evaluate_predicted_assignment_generation(
            x_raw,
            responsibilities,
            feature_names=feature_names,
            folds=folds,
            variance_floor=float(variance_floor),
        )
        fitted.append(
            {
                "run": run,
                "model": model,
                "responsibilities": responsibilities,
                "hard_assignments": hard_assignments,
                "predicted_assignment_metrics": predicted,
            }
        )
        assignment_arrays[_safe_npz_key(str(run["mode"]))] = responsibilities
        model_summaries.append(model_summary_artifact(run=run, model=model, responsibilities=responsibilities, hard_assignments=hard_assignments))

    evaluator = load_stage3_evaluator_labels(s3a, teacher)
    labels = evaluator.exact_labels
    if len(labels) != int(x_raw.shape[0]):
        raise ValueError(f"Stage 3A frozen feature row count {x_raw.shape[0]} does not match evaluator label count {len(labels)}")
    class_names = evaluator.exact_class_names
    quotient_labels = [label_to_quotient.get(label, label) for label in labels]
    quotient_class_names = sorted(set(quotient_labels))
    stress_results = []
    for row in fitted:
        metrics = evaluate_cluster_assignments(
            row["hard_assignments"],
            exact_labels=labels,
            exact_class_names=class_names,
            quotient_labels=quotient_labels,
            quotient_class_names=quotient_class_names,
        )
        context_dependent = context_dependent_mechanism_diagnostics(
            row["hard_assignments"],
            records=evaluator.records,
            cluster_to_label_match=dict(metrics["exact_label_metrics"].get("cluster_to_label_match", {})),
        )
        stress_results.append(
            {
                "schema": "scope_static_stage3d4_k_stress_result_v1",
                **dict(row["run"]),
                "model_family": "diagonal_covariance_visible_prototype_mixture",
                "used_mechanism_labels_for_fit": False,
                "used_labels_for_model_selection": False,
                "used_context_groups_for_fit": False,
                "active_cluster_count": metrics["active_cluster_count"],
                "assignment_entropy": metrics["assignment_entropy"],
                "cluster_masses": metrics["cluster_masses"],
                "exact_label_metrics": metrics["exact_label_metrics"],
                "quotient_label_metrics": metrics["quotient_label_metrics"],
                "context_dependent_mechanism_diagnostics": context_dependent,
                "predicted_assignment_metrics": row["predicted_assignment_metrics"],
                "predicted_assignment_overall": dict(row["predicted_assignment_metrics"].get("overall", {})),
            }
        )

    global_null = evaluate_global_null_generation(
        x_raw,
        feature_names=feature_names,
        folds=folds,
        variance_floor=float(variance_floor),
    )
    null_primary = _optional_float(dict(global_null.get("overall", {})).get(PRIMARY_GENERATION_LIKELIHOOD_METRIC))
    if null_primary is not None:
        for row in stress_results:
            predicted = dict(row.get("predicted_assignment_overall", {}))
            nll = _optional_float(predicted.get(PRIMARY_GENERATION_LIKELIHOOD_METRIC))
            predicted["generation_null_lift"] = None if nll is None else float(null_primary) - float(nll)
            row["predicted_assignment_overall"] = predicted
    mean_only = evaluate_mean_only_generation(
        x_raw,
        feature_names=feature_names,
        folds=folds,
    )
    stress_summary = k_stress_summary(
        stress_results=stress_results,
        global_null_metrics=global_null,
        class_count=class_count,
        quotient_class_count=quotient_class_count,
    )
    leakage = stage3d4_leakage_audit(s3b1_metrics=s3b1_metrics)
    s3c_reference = s3c_reference_audit(s3c_metrics=s3c_metrics, stress_results=stress_results)
    acceptance = stage3d4_acceptance_audit(
        s3a_metrics=s3a_metrics,
        s3a5_metrics=s3a5_metrics,
        s3b1_metrics=s3b1_metrics,
        feature_match=feature_match,
        feature_matrix=feature_matrix,
        k_plan=k_plan,
        stress_results=stress_results,
        stress_summary=stress_summary,
        leakage_audit=leakage,
        s3c_reference_audit=s3c_reference,
        min_success_nmi=float(min_success_nmi),
        min_success_ari=float(min_success_ari),
        min_success_ba=float(min_success_ba),
        min_undercomplete_nmi_gap=float(min_undercomplete_nmi_gap),
        min_generation_null_lift=float(min_generation_null_lift),
    )
    result = {
        "schema": "scope_static_stage3d4_k_stress_audit_v1",
        "stage": STAGE_NAME,
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="k_stress_audit"),
        "stage3a_dir": str(s3a),
        "stage3a5_dir": str(s3a5),
        "stage3b1_dir": str(s3b1),
        "stage3c_dir": None if s3c is None else str(s3c),
        "teacher_dir": str(teacher),
        "output_dir": str(output),
        "claim_boundary": {
            "trains_supervised_classifier": False,
            "uses_mechanism_labels_for_fit": False,
            "uses_mechanism_labels_for_model_selection": False,
            "uses_catalog_cardinality_for_k_values_only": True,
            "uses_stage3a5_quotient_count_for_k_values_only": True,
            "evaluator_only_metrics_after_fit": True,
            "tests_k_robustness_not_new_teacher_sampling": True,
            "discovers_cptp_gksl_channels": False,
        },
        "config": {
            "stage3a_dir": str(s3a),
            "stage3a5_dir": str(s3a5),
            "stage3b1_dir": str(s3b1),
            "stage3c_dir": None if s3c is None else str(s3c),
            "teacher_dir": str(teacher),
            "output_dir": str(output),
            "seed": int(seed),
            "max_iter": int(max_iter),
            "max_cv_folds": None if max_cv_folds is None else int(max_cv_folds),
            "initial_temperature": float(initial_temperature),
            "final_temperature": float(final_temperature),
            "variance_floor": float(variance_floor),
            "undercomplete_fraction": float(undercomplete_fraction),
            "overcomplete_multiplier": float(overcomplete_multiplier),
            "min_success_nmi": float(min_success_nmi),
            "min_success_ari": float(min_success_ari),
            "min_success_ba": float(min_success_ba),
            "min_undercomplete_nmi_gap": float(min_undercomplete_nmi_gap),
            "min_generation_null_lift": float(min_generation_null_lift),
            "operation_context_weight": float(operation_context_weight),
        },
        "visible_feature_matrix": feature_matrix,
        "visible_feature_weighting": _k_stress_feature_weighting_artifact(feature_weighting, feature_names),
        "feature_schema_match_audit": feature_match,
        "heldout_protocol": heldout_protocol_artifact(all_folds=all_folds, evaluated_folds=folds, max_cv_folds=max_cv_folds),
        "k_stress_plan": k_plan,
        "model_summaries": model_summaries,
        "k_stress_results": stress_results,
        "k_stress_summary": stress_summary,
        "global_null_metrics": global_null,
        "mean_only_baseline_metrics": mean_only,
        "leakage_audit": leakage,
        "s3c_reference_audit": s3c_reference,
        "acceptance_audit": acceptance,
        "decision": "stage3d4_k_stress_audit_passed" if acceptance["passed"] else "stage3d4_k_stress_audit_failed",
    }
    _write_outputs(output, result, assignment_arrays)
    return result


def k_stress_plan(
    *,
    record_count: int,
    class_count: int,
    quotient_class_count: int,
    undercomplete_fraction: float,
    overcomplete_multiplier: float,
) -> dict[str, object]:
    count = max(1, int(record_count))
    exact_k = max(1, min(int(class_count), count))
    quotient_k = max(1, min(int(quotient_class_count), count))
    under_target = int(np.floor(float(quotient_k) * float(undercomplete_fraction)))
    under_k = max(1, min(max(1, quotient_k - 1), under_target if under_target > 0 else 1, count))
    over_k = max(1, min(int(np.ceil(float(exact_k) * float(overcomplete_multiplier))), count))
    runs = [
        {
            "mode": "undercomplete_half_quotient",
            "stress_family": "undercomplete",
            "k": int(under_k),
            "description": "K is below the Stage 3A.5 quotient count; recovery should degrade if quotient size matters.",
        },
        {
            "mode": "fixed_oracle_count",
            "stress_family": "exact",
            "k": int(exact_k),
            "description": "K equals evaluator-declared catalog cardinality, not mechanism labels.",
        },
    ]
    if quotient_k != exact_k:
        runs.append(
            {
                "mode": "quotient_count",
                "stress_family": "quotient",
                "k": int(quotient_k),
                "description": "K equals Stage 3A.5 observable quotient count.",
            }
        )
    runs.append(
        {
            "mode": "overcomplete_2x",
            "stress_family": "overcomplete",
            "k": int(over_k),
            "description": "K_max equals overcomplete_multiplier times catalog cardinality, capped by record count.",
        }
    )
    return {
        "schema": "scope_static_stage3d4_k_stress_plan_v1",
        "record_count": int(count),
        "catalog_class_count_evaluator_only": int(class_count),
        "quotient_class_count_from_stage3a5": int(quotient_class_count),
        "undercomplete_fraction": float(undercomplete_fraction),
        "overcomplete_multiplier": float(overcomplete_multiplier),
        "uses_labels_for_fit": False,
        "uses_catalog_cardinality_for_k_only": True,
        "runs": runs,
        "omitted_duplicate_modes": [] if quotient_k != exact_k else ["quotient_count duplicates fixed_oracle_count in this artifact"],
    }


def model_summary_artifact(
    *,
    run: dict[str, object],
    model: dict[str, np.ndarray | list[dict[str, float]] | str | bool],
    responsibilities: np.ndarray,
    hard_assignments: np.ndarray,
) -> dict[str, object]:
    weights = np.asarray(model["weights"], dtype=np.float64)
    return {
        "schema": "scope_static_stage3d4_model_summary_v1",
        "mode": str(run["mode"]),
        "stress_family": str(run["stress_family"]),
        "k": int(run["k"]),
        "model_family": str(model.get("model_family", "diagonal_covariance_visible_prototype_mixture")),
        "uses_context_groups": bool(model.get("uses_context_groups", False)),
        "assignment_matrix_shape": [int(responsibilities.shape[0]), int(responsibilities.shape[1])],
        "row_stochastic": bool(responsibilities.size == 0 or np.allclose(np.sum(responsibilities, axis=1), 1.0)),
        "active_prototype_count_by_weight": int(np.sum(weights > MIN_COMPONENT_MASS)),
        "active_hard_cluster_count": int(len(set(np.asarray(hard_assignments, dtype=np.int64).tolist()))),
        "mean_assignment_entropy": float(_assignment_entropy(responsibilities)),
    }


def k_stress_summary(
    *,
    stress_results: list[dict[str, object]],
    global_null_metrics: dict[str, object],
    class_count: int,
    quotient_class_count: int,
) -> dict[str, object]:
    rows = []
    primary = PRIMARY_GENERATION_LIKELIHOOD_METRIC
    null = _optional_float(dict(global_null_metrics.get("overall", {})).get(primary))
    for row in stress_results:
        exact = dict(row.get("exact_label_metrics", {}))
        quotient = dict(row.get("quotient_label_metrics", {}))
        predicted = dict(row.get("predicted_assignment_overall", {}))
        nll = _optional_float(predicted.get(primary))
        rows.append(
            {
                "mode": row.get("mode"),
                "stress_family": row.get("stress_family"),
                "k": row.get("k"),
                "active_cluster_count": row.get("active_cluster_count"),
                "exact_ari": exact.get("adjusted_rand_index"),
                "exact_nmi": exact.get("normalized_mutual_info"),
                "exact_balanced_accuracy": exact.get("balanced_accuracy_after_label_matching"),
                "exact_min_recall": exact.get("min_recall_after_label_matching"),
                "quotient_ari": quotient.get("adjusted_rand_index"),
                "quotient_nmi": quotient.get("normalized_mutual_info"),
                "quotient_balanced_accuracy": quotient.get("balanced_accuracy_after_label_matching"),
                "categorical_population_nll": nll,
                "generation_null_lift": None if nll is None or null is None else null - nll,
                "raw_visible_feature_mae": predicted.get("raw_visible_feature_mae"),
            }
        )
    success_rows = [row for row in rows if str(row.get("stress_family")) in {"exact", "quotient", "overcomplete"}]
    under_rows = [row for row in rows if str(row.get("stress_family")) == "undercomplete"]
    best_success_nmi = max((_optional_float(row.get("exact_nmi")) or 0.0 for row in success_rows), default=0.0)
    best_under_nmi = max((_optional_float(row.get("exact_nmi")) or 0.0 for row in under_rows), default=0.0)
    return {
        "schema": "scope_static_stage3d4_k_stress_summary_v1",
        "primary_generation_likelihood_metric": primary,
        "secondary_continuous_density_diagnostic": SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC,
        "catalog_class_count": int(class_count),
        "quotient_class_count": int(quotient_class_count),
        "global_null_categorical_population_nll": null,
        "rows": rows,
        "best_success_exact_nmi": float(best_success_nmi),
        "best_undercomplete_exact_nmi": float(best_under_nmi),
        "undercomplete_nmi_gap": float(best_success_nmi - best_under_nmi),
    }


def _k_stress_feature_weighting_artifact(weighting: dict[str, object], feature_names: list[str]) -> dict[str, object]:
    weights = np.asarray(weighting.get("feature_weights", np.ones(len(feature_names), dtype=np.float64)), dtype=np.float64)
    weighted_features = [
        {"feature": str(feature_names[idx]), "weight": float(weights[idx])}
        for idx in range(len(feature_names))
        if abs(float(weights[idx]) - 1.0) > 1.0e-12
    ]
    return {
        "schema": "scope_static_stage3d4_visible_feature_weighting_v1",
        "uses_mechanism_labels": False,
        "uses_visible_operation_context": True,
        "operation_context_weight": float(weighting.get("operation_context_weight", 1.0)),
        "operation_context_feature_count": int(weighting.get("operation_context_feature_count", 0)),
        "weighted_feature_count": int(len(weighted_features)),
        "weighted_features": weighted_features,
    }


def stage3d4_leakage_audit(*, s3b1_metrics: dict[str, object] | None) -> dict[str, object]:
    boundary = dict(s3b1_metrics.get("claim_boundary", {})) if isinstance(s3b1_metrics, dict) and isinstance(s3b1_metrics.get("claim_boundary", {}), dict) else {}
    checks = {
        "uses_stage3a_frozen_visible_features": True,
        "k_stress_uses_labels_for_fit": False,
        "k_stress_uses_labels_for_model_selection": False,
        "k_stress_uses_channels_ptms_kraus": False,
        "k_stress_uses_teacher_self_features": False,
        "k_stress_uses_oracle_prototypes": False,
        "catalog_cardinality_used_for_k_only": True,
        "quotient_count_used_for_k_only": True,
        "stage3b1_labels_not_used_for_fit": True if not boundary else not bool(boundary.get("uses_mechanism_labels_for_fit", True)),
        "stage3b1_labels_not_used_for_model_selection": True
        if not boundary
        else not bool(boundary.get("uses_mechanism_labels_for_model_selection", True)),
    }
    return {
        "schema": "scope_static_stage3d4_leakage_audit_v1",
        "passed": bool(
            checks["uses_stage3a_frozen_visible_features"]
            and not checks["k_stress_uses_labels_for_fit"]
            and not checks["k_stress_uses_labels_for_model_selection"]
            and not checks["k_stress_uses_channels_ptms_kraus"]
            and not checks["k_stress_uses_teacher_self_features"]
            and not checks["k_stress_uses_oracle_prototypes"]
            and checks["catalog_cardinality_used_for_k_only"]
            and checks["quotient_count_used_for_k_only"]
            and checks["stage3b1_labels_not_used_for_fit"]
            and checks["stage3b1_labels_not_used_for_model_selection"]
        ),
        "checks": checks,
    }


def s3c_reference_audit(*, s3c_metrics: dict[str, object] | None, stress_results: list[dict[str, object]]) -> dict[str, object]:
    if not s3c_metrics:
        return {
            "schema": "scope_static_stage3d4_s3c_reference_audit_v1",
            "s3c_metrics_present": False,
            "passed": True,
        }
    predicted = dict(dict(s3c_metrics.get("predicted_assignment_metrics", {})).get("overall", {}))
    primary = PRIMARY_GENERATION_LIKELIHOOD_METRIC
    over = next((row for row in stress_results if row.get("mode") == "overcomplete_2x"), None)
    over_pred = dict(over.get("predicted_assignment_overall", {})) if isinstance(over, dict) else {}
    delta = None
    if predicted.get(primary) is not None and over_pred.get(primary) is not None:
        delta = abs(float(predicted[primary]) - float(over_pred[primary]))
    return {
        "schema": "scope_static_stage3d4_s3c_reference_audit_v1",
        "s3c_metrics_present": True,
        "reference": "S3C predicted-assignment metrics should match the D4 overcomplete_2x generator only when seeds and iteration budgets match B1 exactly.",
        "passed": True,
        "overcomplete_primary_abs_delta_from_s3c": delta,
    }


def stage3d4_acceptance_audit(
    *,
    s3a_metrics: dict[str, object],
    s3a5_metrics: dict[str, object],
    s3b1_metrics: dict[str, object] | None,
    feature_match: dict[str, object],
    feature_matrix: dict[str, object],
    k_plan: dict[str, object],
    stress_results: list[dict[str, object]],
    stress_summary: dict[str, object],
    leakage_audit: dict[str, object],
    s3c_reference_audit: dict[str, object],
    min_success_nmi: float,
    min_success_ari: float,
    min_success_ba: float,
    min_undercomplete_nmi_gap: float,
    min_generation_null_lift: float,
) -> dict[str, object]:
    by_family = {str(row.get("stress_family")): row for row in stress_results}
    exact = by_family.get("exact")
    over = by_family.get("overcomplete")
    under = by_family.get("undercomplete")
    success_rows = [row for row in [exact, over] if isinstance(row, dict)]
    generation_lifts = [_generation_null_lift(row) for row in success_rows]
    recovery_rows_ok = [_recovery_ok(row, min_nmi=min_success_nmi, min_ari=min_success_ari, min_ba=min_success_ba) for row in success_rows]
    checks = {
        "stage3a_acceptance_passed": bool(dict(s3a_metrics.get("acceptance_audit", {})).get("passed", False)),
        "stage3a5_acceptance_passed": bool(dict(s3a5_metrics.get("acceptance_audit", {})).get("passed", False)),
        "stage3b1_acceptance_passed_or_not_required": True
        if s3b1_metrics is None
        else bool(dict(s3b1_metrics.get("acceptance_audit", {})).get("passed", False)),
        "approved_feature_schema_matches_stage3a": bool(feature_match.get("passed", False)),
        "uses_stage3a_frozen_visible_features": bool(feature_matrix.get("loaded_from_stage3a_artifact", False)),
        "undercomplete_exact_overcomplete_runs_present": all(family in by_family for family in ["undercomplete", "exact", "overcomplete"]),
        "all_runs_use_no_labels_for_fit": all(not bool(row.get("used_mechanism_labels_for_fit", True)) for row in stress_results),
        "all_runs_use_no_labels_for_model_selection": all(not bool(row.get("used_labels_for_model_selection", True)) for row in stress_results),
        "exact_and_overcomplete_recovery_meet_thresholds": bool(success_rows and all(recovery_rows_ok)),
        "exact_and_overcomplete_generation_beat_null": bool(
            success_rows and all(lift is not None and float(lift) >= float(min_generation_null_lift) for lift in generation_lifts)
        ),
        "undercomplete_k_is_below_quotient_count": bool(under and int(under.get("k", 0)) < int(k_plan.get("quotient_class_count_from_stage3a5", 0))),
        "undercomplete_recovery_degrades": bool(
            float(stress_summary.get("undercomplete_nmi_gap", 0.0)) >= float(min_undercomplete_nmi_gap)
        ),
        "leakage_audit_passed": bool(leakage_audit.get("passed", False)),
        "s3c_reference_audit_passed": bool(s3c_reference_audit.get("passed", False)),
    }
    return {
        "schema": "scope_static_stage3d4_acceptance_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
        "thresholds": {
            "min_success_nmi": float(min_success_nmi),
            "min_success_ari": float(min_success_ari),
            "min_success_ba": float(min_success_ba),
            "min_undercomplete_nmi_gap": float(min_undercomplete_nmi_gap),
            "min_generation_null_lift": float(min_generation_null_lift),
        },
        "undercomplete_nmi_gap": stress_summary.get("undercomplete_nmi_gap"),
    }


def _recovery_ok(row: dict[str, object], *, min_nmi: float, min_ari: float, min_ba: float) -> bool:
    exact = dict(row.get("exact_label_metrics", {}))
    quotient = dict(row.get("quotient_label_metrics", {}))
    return bool(
        max(float(exact.get("normalized_mutual_info", 0.0)), float(quotient.get("normalized_mutual_info", 0.0))) >= float(min_nmi)
        and max(float(exact.get("adjusted_rand_index", 0.0)), float(quotient.get("adjusted_rand_index", 0.0))) >= float(min_ari)
        and max(float(exact.get("balanced_accuracy_after_label_matching", 0.0)), float(quotient.get("balanced_accuracy_after_label_matching", 0.0)))
        >= float(min_ba)
    )


def _generation_null_lift(row: dict[str, object]) -> float | None:
    predicted = dict(row.get("predicted_assignment_overall", {}))
    value = predicted.get("generation_null_lift")
    if value is not None:
        return float(value)
    return None


def _assignment_entropy(responsibilities: np.ndarray) -> float:
    if responsibilities.size == 0:
        return 0.0
    clipped = np.maximum(responsibilities, MIN_COMPONENT_MASS)
    return float(np.mean(-np.sum(responsibilities * np.log(clipped), axis=1)))


def _safe_npz_key(key: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in str(key))


def _optional_json(path: Path | None) -> dict[str, object] | None:
    if path is None or not path.exists():
        return None
    return _load_json(path)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _write_outputs(output: Path, result: dict[str, object], assignment_arrays: dict[str, np.ndarray]) -> None:
    artifacts = {
        "metrics.json": result,
        "k_stress_plan.json": result["k_stress_plan"],
        "k_stress_results.json": {"schema": "scope_static_stage3d4_k_stress_results_v1", "results": result["k_stress_results"]},
        "k_stress_summary.json": result["k_stress_summary"],
        "model_summaries.json": {"schema": "scope_static_stage3d4_model_summaries_v1", "models": result["model_summaries"]},
        "global_null_metrics.json": result["global_null_metrics"],
        "mean_only_baseline_metrics.json": result["mean_only_baseline_metrics"],
        "leakage_audit.json": result["leakage_audit"],
        "s3c_reference_audit.json": result["s3c_reference_audit"],
        "acceptance_audit.json": result["acceptance_audit"],
        "heldout_protocol.json": result["heldout_protocol"],
        "feature_schema_match_audit.json": result["feature_schema_match_audit"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
        "visible_feature_weighting.json": result["visible_feature_weighting"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    np.savez(output / "learned_assignments_by_k.npz", **assignment_arrays)
    (output / "config.yaml").write_text(yaml.safe_dump({"stage3d4_k_stress_audit": result["config"]}, sort_keys=False))
    (output / "summary.md").write_text(format_stage3d4_summary(result))


def format_stage3d4_summary(result: dict[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    summary = dict(result.get("k_stress_summary", {}))
    lines = [
        "# Stage 3D.4: K Stress Audit",
        "",
        f"- Decision: `{result.get('decision')}`",
        f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
        f"- Global-null categorical population NLL: `{_format_metric(summary.get('global_null_categorical_population_nll'))}`",
        f"- Best success exact NMI: `{_format_metric(summary.get('best_success_exact_nmi'))}`",
        f"- Best undercomplete exact NMI: `{_format_metric(summary.get('best_undercomplete_exact_nmi'))}`",
        f"- Undercomplete NMI gap: `{_format_metric(summary.get('undercomplete_nmi_gap'))}`",
        "",
        "## K Rows",
        "",
        "| Mode | K | Active | Exact NMI | Exact ARI | Exact BA | Gen NLL | Null Lift |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.get("rows", []):
        if not isinstance(row, dict):
            continue
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("mode")),
                    str(row.get("k")),
                    str(row.get("active_cluster_count")),
                    _format_metric(row.get("exact_nmi")),
                    _format_metric(row.get("exact_ari")),
                    _format_metric(row.get("exact_balanced_accuracy")),
                    _format_metric(row.get("categorical_population_nll")),
                    _format_metric(row.get("generation_null_lift")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "Stage 3D.4 reruns visible-only prototype discovery at fixed undercomplete, exact, and overcomplete K settings. Mechanism labels are used only after fitting for evaluator-only recovery metrics. Passing means exact and overcomplete K preserve recovery and heldout replay, while undercomplete K degrades mechanism recovery as expected.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_metric(value: object) -> str:
    if value is None:
        return "none"
    return f"{float(value):.6f}"
