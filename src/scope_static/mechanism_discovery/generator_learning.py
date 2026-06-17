from __future__ import annotations

import json
from pathlib import Path
import time

import numpy as np
import yaml

from scope_static.primitives.mechanism_catalog import mechanism_taxonomy_contract_audit
from scope_static.protocols import LEARNER_VALIDATION_STAGE
from .assignment_matrix import normalize_rows as _normalize_rows
from .artifacts import feature_schema_matches_stage3a as _feature_schema_matches_s3a
from .artifacts import load_json_object as _load_json
from .artifacts import load_stage3_evaluator_labels
from .artifacts import load_stage3a_frozen_visible_features
from .artifacts import resolve_teacher_dir
from .audit_values import optional_difference as _optional_difference
from .audit_values import optional_float as _optional_float
from .feature_blocks import feature_block_indices as _feature_block_indices
from .observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from .protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR
from .baselines import VARIANCE_FLOOR
from .baselines import _diag_log_prob
from .baselines import _logsumexp
from .contract_claims import artifact_acceptance_passed
from .contract_claims import stage3d4b_claim_gate_audit
from .contract_claims import stage3d4b_claim_gate_passed
from .discovery_model import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3B1_DIR
from .discovery_model import EVALUATOR_MODE_CONTROLLED_CATALOG
from .discovery_model import EVALUATOR_MODE_NO_ORACLE_LABELS
from .discovery_model import _normalize_evaluator_mode
from .discovery_model import _cap_folds
from .discovery_model import _valid_folds
from .recovery_metrics import evaluate_soft_family_classification
from .recovery_metrics import evaluate_soft_family_strength_location_audit
from .recovery_metrics import skipped_soft_family_classification
from .recovery_metrics import skipped_soft_family_strength_location_audit


STAGE_NAME = "Stage3C_prototype_generator_learning"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/PHYC_STAGE3_discovery/S3C_prototype_generator_learning"
DEFAULT_MAX_CV_FOLDS = 5
DEFAULT_ASSIGNMENT_SHUFFLE_SEEDS = (0,)
DEFAULT_FEATURE_SCRAMBLE_SEEDS = (0,)
MIN_WEIGHT = 1.0e-12
PROBABILITY_METRICS = {"P0", "P1", "P00", "P01", "P10", "P11", "p_comp"}
PRIMARY_GENERATION_LIKELIHOOD_METRIC = "categorical_population_nll"
SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC = "gaussian_density_nll"
FALLBACK_GENERATION_LIKELIHOOD_METRIC = SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC
TARGET_SCORE_PROFILE_FULL = "full_target"
TARGET_SCORE_PROFILE_RAW = "raw_target_only"
TARGET_SCORE_PROFILE_BLOCK_NORMALIZED = "block_normalized"
TARGET_SCORE_PROFILE_NAMES = (
    TARGET_SCORE_PROFILE_FULL,
    TARGET_SCORE_PROFILE_RAW,
    TARGET_SCORE_PROFILE_BLOCK_NORMALIZED,
)
DEFAULT_PUBLIC_STRATIFICATION_FIELDS = ("dataset_family", "distance", "basis", "region_family", "round_band")
DEFAULT_MIN_STRATIFIED_TRAIN_ROWS = 2


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
    assignment_shuffle_seeds: tuple[int, ...] | list[int] | None = DEFAULT_ASSIGNMENT_SHUFFLE_SEEDS,
    feature_scramble_seeds: tuple[int, ...] | list[int] | None = DEFAULT_FEATURE_SCRAMBLE_SEEDS,
    stage3b1_residualized_dir: str | Path | None = None,
    stage3d4b_dir: str | Path | None = None,
    stage5b1_dir: str | Path | None = None,
) -> dict[str, object]:
    """Score heldout visible generation from learned Stage 3 assignments.

    The learner-side generator consumes the frozen Stage 3A visible matrix and
    Stage 3B.1 learned assignments. Mechanism labels are loaded only after the
    predicted-assignment and null generators are fit, for the evaluator-only
    oracle comparator.
    """

    started = time.perf_counter()
    mode = _normalize_evaluator_mode(evaluator_mode)
    s3a = Path(stage3a_dir)
    s3a5 = Path(stage3a5_dir)
    s3b1 = Path(stage3b1_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    s3a_metrics = _load_json(s3a / "metrics.json")
    s3a5_metrics = _load_json(s3a5 / "metrics.json") if mode == EVALUATOR_MODE_CONTROLLED_CATALOG else _no_oracle_stage3a5_metrics()
    s3b1_metrics = _load_json(s3b1 / "metrics.json")
    s3b1_residualized_metrics = _optional_json(None if stage3b1_residualized_dir is None else Path(stage3b1_residualized_dir) / "metrics.json")
    s3d4b_metrics = _optional_json(None if stage3d4b_dir is None else Path(stage3d4b_dir) / "metrics.json")
    stage5b1_metrics = _optional_json(None if stage5b1_dir is None else Path(stage5b1_dir) / "metrics.json")
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
    stratified_null = evaluate_public_stratified_null_generation(
        x,
        feature_names=feature_names,
        folds=folds,
        split_manifest=split_manifest,
        variance_floor=float(variance_floor),
    )
    mean_only = evaluate_mean_only_generation(
        x,
        feature_names=feature_names,
        folds=folds,
    )
    shuffle_audit = assignment_shuffle_audit(
        x,
        responsibilities,
        feature_names=feature_names,
        folds=folds,
        variance_floor=float(variance_floor),
        predicted_assignment_metrics=predicted,
        global_null_metrics=global_null,
        stratified_null_metrics=stratified_null,
        mean_only_baseline_metrics=mean_only,
        seeds=assignment_shuffle_seeds,
    )
    scramble_audit = feature_scramble_audit(
        x,
        responsibilities,
        feature_names=feature_names,
        folds=folds,
        split_manifest=split_manifest,
        variance_floor=float(variance_floor),
        predicted_assignment_metrics=predicted,
        global_null_metrics=global_null,
        stratified_null_metrics=stratified_null,
        mean_only_baseline_metrics=mean_only,
        seeds=feature_scramble_seeds,
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
        soft_family = evaluate_soft_family_classification(
            responsibilities,
            evaluator.records,
            evaluator_mode=mode,
        )
        strength_location = evaluate_soft_family_strength_location_audit(
            x,
            responsibilities,
            evaluator.records,
            feature_names=feature_names,
            evaluator_mode=mode,
        )
    else:
        oracle = skipped_oracle_assignment_comparator(feature_names=feature_names, folds=folds)
        soft_family = skipped_soft_family_classification()
        strength_location = skipped_soft_family_strength_location_audit()
    taxonomy_contract = mechanism_taxonomy_contract_audit()

    prototype_metrics = prototype_generation_metrics(
        predicted_assignment_metrics=predicted,
        global_null_metrics=global_null,
        stratified_null_metrics=stratified_null,
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
        stratified_null_metrics=stratified_null,
        mean_only_baseline_metrics=mean_only,
        oracle_assignment_comparator_metrics=oracle,
        soft_family_classification_metrics=soft_family,
        soft_family_strength_location_audit=strength_location,
        mechanism_taxonomy_contract_audit=taxonomy_contract,
        leakage_audit=leakage,
        evaluator_mode=mode,
    )
    claim_gate = stage3c_claim_gate_audit(
        s3b1_metrics=s3b1_metrics,
        s3b1_residualized_metrics=s3b1_residualized_metrics,
        stage3d4b_metrics=s3d4b_metrics,
        stage5b1_metrics=stage5b1_metrics,
        evaluator_mode=mode,
    )
    stage3b1_k_prior_contract = _stage3b1_k_prior_contract(s3b1_metrics)
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
            "uses_family_labels_for_predicted_assignment_generator": False,
            "uses_mechanism_labels_for_model_selection": False,
            "uses_family_labels_for_model_selection": False,
            "trains_from_stage3a_frozen_visible_features": True,
            "uses_stage3b1_learned_assignments": True,
            "rebuilds_visible_features_from_oracle_records_for_fit": False,
            "oracle_assignment_comparator_evaluator_only": mode == EVALUATOR_MODE_CONTROLLED_CATALOG,
            "oracle_assignment_comparator_skipped": mode == EVALUATOR_MODE_NO_ORACLE_LABELS,
            "soft_family_classification_evaluator_only": mode == EVALUATOR_MODE_CONTROLLED_CATALOG,
            "soft_family_classification_skipped": mode == EVALUATOR_MODE_NO_ORACLE_LABELS,
            "soft_family_strength_location_audit_evaluator_only": mode == EVALUATOR_MODE_CONTROLLED_CATALOG,
            "soft_family_strength_location_audit_skipped": mode == EVALUATOR_MODE_NO_ORACLE_LABELS,
            "s5_context_relative_mechanism_effect_audit_evaluator_only": mode == EVALUATOR_MODE_CONTROLLED_CATALOG,
            "s5_context_relative_mechanism_effect_audit_skipped": mode == EVALUATOR_MODE_NO_ORACLE_LABELS,
            "claim_gate_allows_assignment_dependent_generator_claim": bool(claim_gate.get("claim_allowed", False)),
            "diagnostic_only_until_s3b1_s5b1_gates_pass": not bool(claim_gate.get("claim_allowed", False)),
            "mechanism_taxonomy_contract_audit_reported": True,
            "mechanism_dimension_recovery_audit_evaluator_only": mode == EVALUATOR_MODE_CONTROLLED_CATALOG,
            "mechanism_dimension_recovery_audit_skipped": mode == EVALUATOR_MODE_NO_ORACLE_LABELS,
            "claims_physical_parameter_recovery": False,
            "conditional_visible_replay_not_unconditional_future_prediction": True,
            "stage3b1_k_prior_contract": stage3b1_k_prior_contract,
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
            "assignment_shuffle_seeds": [int(seed) for seed in _audit_seed_list(assignment_shuffle_seeds)],
            "feature_scramble_seeds": [int(seed) for seed in _audit_seed_list(feature_scramble_seeds)],
            "stage3b1_residualized_dir": None if stage3b1_residualized_dir is None else str(stage3b1_residualized_dir),
            "stage3d4b_dir": None if stage3d4b_dir is None else str(stage3d4b_dir),
            "stage5b1_dir": None if stage5b1_dir is None else str(stage5b1_dir),
        },
        "wall_clock_seconds": float(time.perf_counter() - started),
        "visible_feature_matrix": feature_matrix,
        "feature_schema_match_audit": feature_match,
        "heldout_protocol": heldout_protocol_artifact(all_folds=all_folds, evaluated_folds=folds, max_cv_folds=max_cv_folds),
        "assignment_source_audit": assignment_source_audit(
            s3b1_dir=s3b1,
            responsibilities=responsibilities,
            s3b1_metrics=s3b1_metrics,
        ),
        "prototype_generation_metrics": prototype_metrics,
        "predicted_assignment_metrics": predicted,
        "oracle_assignment_comparator_metrics": oracle,
        "soft_family_classification_metrics": soft_family,
        "soft_family_strength_location_audit": strength_location,
        "s5_context_relative_mechanism_effect_audit": strength_location,
        "mechanism_taxonomy_contract_audit": taxonomy_contract,
        "mechanism_dimension_recovery_audit": strength_location.get("mechanism_dimension_recovery_audit", {}),
        "overlay_contract_audit": strength_location.get("overlay_contract_audit", {}),
        "overlay_recovery_audit": strength_location.get("overlay_recovery_audit", {}),
        "global_null_metrics": global_null,
        "stratified_null_metrics": stratified_null,
        "mean_only_baseline_metrics": mean_only,
        "assignment_shuffle_audit": shuffle_audit,
        "feature_scramble_audit": scramble_audit,
        "leakage_audit": leakage,
        "claim_gate_audit": claim_gate,
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
    profile_nll_rows = []
    for fold_idx, fold in enumerate(folds):
        train_idx = _indices(fold.get("train_indices", []), record_count=int(x.shape[0]))
        heldout_idx = _heldout_indices(fold, record_count=int(x.shape[0]))
        if train_idx.size == 0 or heldout_idx.size == 0:
            continue
        params = _fit_responsibility_generator(x[train_idx], responsibilities[train_idx], variance_floor=float(variance_floor))
        pred_mean = _responsibility_prediction_mean(responsibilities[heldout_idx], params["means"])
        nll = _conditional_responsibility_nll(x[heldout_idx], responsibilities[heldout_idx], params["means"], params["variances"])
        profile_nll = _responsibility_target_profile_nll(
            x[heldout_idx],
            responsibilities[heldout_idx],
            params["means"],
            params["variances"],
            feature_names,
            full_nll=nll,
        )
        metrics = _score_generation(x[heldout_idx], pred_mean, nll, feature_names)
        fold_rows.append(
            {
                "fold": int(fold_idx),
                "train_count": int(train_idx.size),
                "heldout_count": int(heldout_idx.size),
                "active_prototype_count": int(params["active_prototype_count"]),
                "target_score_profiles": _target_score_profiles(
                    x[heldout_idx],
                    pred_mean,
                    feature_names,
                    profile_nll=profile_nll,
                ),
                **metrics,
            }
        )
        y_rows.append(x[heldout_idx])
        pred_rows.append(pred_mean)
        nll_rows.append(nll)
        profile_nll_rows.append(profile_nll)
    return _generation_artifact(
        schema="scope_static_stage3c_predicted_assignment_metrics_v1",
        model_name="predicted_assignment_generator",
        description="Fold-local diagonal visible generator conditioned on Stage 3B.1 learned assignment probabilities.",
        feature_names=feature_names,
        y_rows=y_rows,
        pred_rows=pred_rows,
        nll_rows=nll_rows,
        profile_nll_rows=profile_nll_rows,
        fold_rows=fold_rows,
        uses_evaluator_labels=False,
    )


def assignment_shuffle_audit(
    x: np.ndarray,
    responsibilities: np.ndarray,
    *,
    feature_names: list[str],
    folds: list[dict[str, list[int]]],
    variance_floor: float,
    predicted_assignment_metrics: dict[str, object],
    global_null_metrics: dict[str, object],
    stratified_null_metrics: dict[str, object],
    mean_only_baseline_metrics: dict[str, object],
    seeds: tuple[int, ...] | list[int] | None,
) -> dict[str, object]:
    seed_list = _audit_seed_list(seeds)
    predicted = dict(predicted_assignment_metrics.get("overall", {}))
    global_null = dict(global_null_metrics.get("overall", {}))
    stratified_null = dict(stratified_null_metrics.get("overall", {}))
    mean_only = dict(mean_only_baseline_metrics.get("overall", {}))
    metric = _effective_primary_generation_likelihood_metric(predicted)
    runs = []
    for seed in seed_list:
        permutation = np.random.default_rng(int(seed)).permutation(int(responsibilities.shape[0]))
        shuffled = responsibilities[permutation]
        metrics = evaluate_predicted_assignment_generation(
            x,
            shuffled,
            feature_names=feature_names,
            folds=folds,
            variance_floor=float(variance_floor),
        )
        overall = dict(metrics.get("overall", {}))
        runs.append(
            {
                "seed": int(seed),
                "assignment_permutation_mode": "global_row_shuffle_preserving_responsibility_rows",
                "prototype_mass_preserved": True,
                "row_stochastic": bool(shuffled.size == 0 or np.allclose(np.sum(shuffled, axis=1), 1.0)),
                "overall": overall,
                "target_score_profiles": metrics.get("target_score_profiles", {}),
                "predicted_minus_shuffle": _gap(predicted, overall),
                "global_null_minus_shuffle": _optional_difference(
                    global_null.get(metric),
                    overall.get(metric),
                ),
                "stratified_null_minus_shuffle": _optional_difference(
                    stratified_null.get(metric),
                    overall.get(metric),
                ),
                "mean_only_minus_shuffle": _optional_difference(
                    mean_only.get(metric),
                    overall.get(metric),
                ),
            }
        )
    aggregate = _aggregate_shuffle_runs(runs)
    target_profile_aggregate = _aggregate_target_score_profile_runs(
        [dict(row.get("target_score_profiles", {})) for row in runs if isinstance(row.get("target_score_profiles", {}), dict)]
    )
    primary_mean = aggregate.get(f"{metric}_mean")
    predicted_primary = predicted.get(metric)
    global_primary = global_null.get(metric)
    checks = {
        "assignment_shuffle_runs_reported": bool(runs),
        "shuffled_assignments_row_stochastic": all(bool(row.get("row_stochastic", False)) for row in runs),
        "shuffle_preserves_prototype_masses": all(bool(row.get("prototype_mass_preserved", False)) for row in runs),
        "shuffled_primary_nll_not_better_than_predicted": (
            True if primary_mean is None or predicted_primary is None else float(primary_mean) >= float(predicted_primary)
        ),
        "shuffled_primary_lift_no_better_than_predicted_lift": (
            True
            if primary_mean is None or predicted_primary is None or global_primary is None
            else (float(global_primary) - float(primary_mean)) <= (float(global_primary) - float(predicted_primary)) + 1.0e-12
        ),
    }
    return {
        "schema": "scope_static_stage3c_assignment_shuffle_audit_v1",
        "description": "Evaluator-side falsification audit: row-shuffle Stage 3B.1 assignments before fitting/scoring the S3C visible generator.",
        "primary_generation_likelihood_metric": metric,
        "assignment_shuffle_mode": "global row permutation of responsibility rows; visible features and folds unchanged",
        "uses_evaluator_labels": False,
        "used_for_model_selection": False,
        "seed_count": int(len(seed_list)),
        "seeds": [int(seed) for seed in seed_list],
        "runs": runs,
        "aggregate": aggregate,
        "target_score_profile_aggregate": target_profile_aggregate,
        "reference_metrics": {
            "predicted_assignment": predicted,
            "global_null": global_null,
            "stratified_null": stratified_null,
            "mean_only_baseline": mean_only,
            "target_score_profiles": {
                "predicted_assignment": predicted_assignment_metrics.get("target_score_profiles", {}),
                "global_null": global_null_metrics.get("target_score_profiles", {}),
                "stratified_null": stratified_null_metrics.get("target_score_profiles", {}),
                "mean_only_baseline": mean_only_baseline_metrics.get("target_score_profiles", {}),
            },
        },
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


def feature_scramble_audit(
    x: np.ndarray,
    responsibilities: np.ndarray,
    *,
    feature_names: list[str],
    folds: list[dict[str, list[int]]],
    split_manifest: dict[str, object],
    variance_floor: float,
    predicted_assignment_metrics: dict[str, object],
    global_null_metrics: dict[str, object],
    stratified_null_metrics: dict[str, object],
    mean_only_baseline_metrics: dict[str, object],
    seeds: tuple[int, ...] | list[int] | None,
) -> dict[str, object]:
    seed_list = _audit_seed_list(seeds)
    predicted = dict(predicted_assignment_metrics.get("overall", {}))
    global_null = dict(global_null_metrics.get("overall", {}))
    stratified_null = dict(stratified_null_metrics.get("overall", {}))
    mean_only = dict(mean_only_baseline_metrics.get("overall", {}))
    metric = _effective_primary_generation_likelihood_metric(predicted)
    runs = []
    for seed in seed_list:
        scrambled_x = _scramble_visible_feature_columns(x, seed=int(seed))
        scrambled_predicted = evaluate_predicted_assignment_generation(
            scrambled_x,
            responsibilities,
            feature_names=feature_names,
            folds=folds,
            variance_floor=float(variance_floor),
        )
        scrambled_global = evaluate_global_null_generation(
            scrambled_x,
            feature_names=feature_names,
            folds=folds,
            variance_floor=float(variance_floor),
        )
        scrambled_stratified = evaluate_public_stratified_null_generation(
            scrambled_x,
            feature_names=feature_names,
            folds=folds,
            split_manifest=split_manifest,
            variance_floor=float(variance_floor),
        )
        scrambled_mean = evaluate_mean_only_generation(
            scrambled_x,
            feature_names=feature_names,
            folds=folds,
        )
        pred_overall = dict(scrambled_predicted.get("overall", {}))
        global_overall = dict(scrambled_global.get("overall", {}))
        stratified_overall = dict(scrambled_stratified.get("overall", {}))
        mean_overall = dict(scrambled_mean.get("overall", {}))
        runs.append(
            {
                "seed": int(seed),
                "feature_scramble_mode": "independent_column_row_permutation",
                "feature_marginals_preserved": True,
                "row_order_preserved": True,
                "fold_indices_preserved": True,
                "assignment_matrix_preserved": True,
                "predicted_assignment": pred_overall,
                "global_null": global_overall,
                "stratified_null": stratified_overall,
                "mean_only_baseline": mean_overall,
                "target_score_profiles": {
                    "predicted_assignment": scrambled_predicted.get("target_score_profiles", {}),
                    "global_null": scrambled_global.get("target_score_profiles", {}),
                    "stratified_null": scrambled_stratified.get("target_score_profiles", {}),
                    "mean_only_baseline": scrambled_mean.get("target_score_profiles", {}),
                },
                "global_null_minus_predicted": _optional_difference(
                    global_overall.get(metric),
                    pred_overall.get(metric),
                ),
                "mean_only_minus_predicted": _optional_difference(
                    mean_overall.get(metric),
                    pred_overall.get(metric),
                ),
            }
        )
    predicted_aggregate = _aggregate_overall_runs([dict(row.get("predicted_assignment", {})) for row in runs])
    global_aggregate = _aggregate_overall_runs([dict(row.get("global_null", {})) for row in runs])
    stratified_aggregate = _aggregate_overall_runs([dict(row.get("stratified_null", {})) for row in runs])
    mean_aggregate = _aggregate_overall_runs([dict(row.get("mean_only_baseline", {})) for row in runs])
    target_profile_aggregate = {
        "predicted_assignment": _aggregate_target_score_profile_runs(
            [
                dict(dict(row.get("target_score_profiles", {})).get("predicted_assignment", {}))
                for row in runs
                if isinstance(dict(row.get("target_score_profiles", {})).get("predicted_assignment", {}), dict)
            ]
        ),
        "global_null": _aggregate_target_score_profile_runs(
            [
                dict(dict(row.get("target_score_profiles", {})).get("global_null", {}))
                for row in runs
                if isinstance(dict(row.get("target_score_profiles", {})).get("global_null", {}), dict)
            ]
        ),
        "stratified_null": _aggregate_target_score_profile_runs(
            [
                dict(dict(row.get("target_score_profiles", {})).get("stratified_null", {}))
                for row in runs
                if isinstance(dict(row.get("target_score_profiles", {})).get("stratified_null", {}), dict)
            ]
        ),
        "mean_only_baseline": _aggregate_target_score_profile_runs(
            [
                dict(dict(row.get("target_score_profiles", {})).get("mean_only_baseline", {}))
                for row in runs
                if isinstance(dict(row.get("target_score_profiles", {})).get("mean_only_baseline", {}), dict)
            ]
        ),
    }
    original_lift = _optional_difference(global_null.get(metric), predicted.get(metric))
    scrambled_lift = _optional_difference(
        global_aggregate.get(f"{metric}_mean"),
        predicted_aggregate.get(f"{metric}_mean"),
    )
    lift_fraction = None
    if original_lift is not None and abs(float(original_lift)) > MIN_WEIGHT and scrambled_lift is not None:
        lift_fraction = float(scrambled_lift) / float(original_lift)
    checks = {
        "feature_scramble_runs_reported": bool(runs),
        "feature_marginals_preserved": all(bool(row.get("feature_marginals_preserved", False)) for row in runs),
        "row_order_fold_and_assignments_preserved": all(
            bool(row.get("row_order_preserved", False))
            and bool(row.get("fold_indices_preserved", False))
            and bool(row.get("assignment_matrix_preserved", False))
            for row in runs
        ),
        "scrambled_primary_nll_not_better_than_original_predicted": (
            True
            if predicted_aggregate.get(f"{metric}_mean") is None
            or predicted.get(metric) is None
            else float(predicted_aggregate[f"{metric}_mean"])
            >= float(predicted[metric])
        ),
        "scrambled_primary_lift_no_better_than_original_lift": (
            True
            if original_lift is None or scrambled_lift is None
            else float(scrambled_lift) <= float(original_lift) + 1.0e-12
        ),
    }
    return {
        "schema": "scope_static_stage3c_feature_scramble_audit_v1",
        "description": "Evaluator-side falsification audit: independently permute each visible feature column across rows before fitting/scoring S3C.",
        "primary_generation_likelihood_metric": metric,
        "feature_scramble_mode": "independent column-wise row permutation; one-feature marginals preserved, row-level visible semantics broken",
        "uses_evaluator_labels": False,
        "used_for_model_selection": False,
        "seed_count": int(len(seed_list)),
        "seeds": [int(seed) for seed in seed_list],
        "runs": runs,
        "aggregate": {
            "predicted_assignment": predicted_aggregate,
            "global_null": global_aggregate,
            "stratified_null": stratified_aggregate,
            "mean_only_baseline": mean_aggregate,
            "target_score_profiles": target_profile_aggregate,
            "target_score_profile_lift": _scrambled_target_score_profile_lift(target_profile_aggregate),
            "original_global_null_minus_predicted_lift": original_lift,
            "scrambled_global_null_minus_predicted_lift": scrambled_lift,
            "scrambled_lift_fraction_of_original": lift_fraction,
        },
        "reference_metrics": {
            "predicted_assignment": predicted,
            "global_null": global_null,
            "stratified_null": stratified_null,
            "mean_only_baseline": mean_only,
            "target_score_profiles": {
                "predicted_assignment": predicted_assignment_metrics.get("target_score_profiles", {}),
                "global_null": global_null_metrics.get("target_score_profiles", {}),
                "stratified_null": stratified_null_metrics.get("target_score_profiles", {}),
                "mean_only_baseline": mean_only_baseline_metrics.get("target_score_profiles", {}),
            },
        },
        "checks": checks,
        "passed": bool(all(checks.values())),
    }


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
    profile_nll_rows = []
    for fold_idx, fold in enumerate(folds):
        train_idx = _indices(fold.get("train_indices", []), record_count=int(x.shape[0]))
        heldout_idx = _heldout_indices(fold, record_count=int(x.shape[0]))
        if train_idx.size == 0 or heldout_idx.size == 0:
            continue
        mean, variance = _fit_global_generator(x[train_idx], variance_floor=float(variance_floor))
        pred_mean = np.tile(mean[None, :], (int(heldout_idx.size), 1))
        nll = -_diag_log_prob(x[heldout_idx], mean[None, :], variance[None, :])[:, 0]
        profile_nll = _global_target_profile_nll(x[heldout_idx], mean, variance, feature_names, full_nll=nll)
        metrics = _score_generation(x[heldout_idx], pred_mean, nll, feature_names)
        fold_rows.append(
            {
                "fold": int(fold_idx),
                "train_count": int(train_idx.size),
                "heldout_count": int(heldout_idx.size),
                "target_score_profiles": _target_score_profiles(
                    x[heldout_idx],
                    pred_mean,
                    feature_names,
                    profile_nll=profile_nll,
                ),
                **metrics,
            }
        )
        y_rows.append(x[heldout_idx])
        pred_rows.append(pred_mean)
        nll_rows.append(nll)
        profile_nll_rows.append(profile_nll)
    return _generation_artifact(
        schema="scope_static_stage3c_global_null_metrics_v1",
        model_name="global_null_diagonal_gaussian",
        description="One train-fold visible mean and diagonal covariance for every heldout instance.",
        feature_names=feature_names,
        y_rows=y_rows,
        pred_rows=pred_rows,
        nll_rows=nll_rows,
        profile_nll_rows=profile_nll_rows,
        fold_rows=fold_rows,
        uses_evaluator_labels=False,
    )


def evaluate_public_stratified_null_generation(
    x: np.ndarray,
    *,
    feature_names: list[str],
    folds: list[dict[str, list[int]]],
    split_manifest: dict[str, object],
    variance_floor: float,
    public_stratification_fields: tuple[str, ...] = DEFAULT_PUBLIC_STRATIFICATION_FIELDS,
    min_stratum_train_rows: int = DEFAULT_MIN_STRATIFIED_TRAIN_ROWS,
) -> dict[str, object]:
    labels, label_audit = _public_stratification_labels(
        split_manifest,
        record_count=int(x.shape[0]),
        fields=tuple(public_stratification_fields),
    )
    fold_rows = []
    y_rows = []
    pred_rows = []
    nll_rows = []
    profile_nll_rows = []
    fallback_total = 0
    heldout_total = 0
    train_stratum_counts = []
    for fold_idx, fold in enumerate(folds):
        train_idx = _indices(fold.get("train_indices", []), record_count=int(x.shape[0]))
        heldout_idx = _heldout_indices(fold, record_count=int(x.shape[0]))
        if train_idx.size == 0 or heldout_idx.size == 0:
            continue
        global_mean, global_var = _fit_global_generator(x[train_idx], variance_floor=float(variance_floor))
        means_by_label: dict[str, np.ndarray] = {}
        variances_by_label: dict[str, np.ndarray] = {}
        train_labels = labels[train_idx]
        for label in sorted(set(train_labels.tolist())):
            mask = train_labels == label
            if int(np.sum(mask)) < int(min_stratum_train_rows):
                continue
            rows = x[train_idx[mask]]
            mean = np.mean(rows, axis=0)
            var = np.maximum(np.var(rows, axis=0), float(variance_floor))
            means_by_label[str(label)] = mean
            variances_by_label[str(label)] = var
        pred_mean = np.empty((int(heldout_idx.size), int(x.shape[1])), dtype=np.float64)
        pred_var = np.empty_like(pred_mean)
        fallback_count = 0
        for local_row, record_idx in enumerate(heldout_idx.tolist()):
            label = str(labels[int(record_idx)])
            if label in means_by_label:
                pred_mean[local_row] = means_by_label[label]
                pred_var[local_row] = variances_by_label[label]
            else:
                pred_mean[local_row] = global_mean
                pred_var[local_row] = global_var
                fallback_count += 1
        nll = _rowwise_diag_nll(x[heldout_idx], pred_mean, pred_var)
        profile_nll = _rowwise_target_profile_nll(x[heldout_idx], pred_mean, pred_var, feature_names, full_nll=nll)
        metrics = _score_generation(x[heldout_idx], pred_mean, nll, feature_names)
        fold_rows.append(
            {
                "fold": int(fold_idx),
                "train_count": int(train_idx.size),
                "heldout_count": int(heldout_idx.size),
                "train_stratum_count": int(len(means_by_label)),
                "heldout_fallback_to_global_count": int(fallback_count),
                "target_score_profiles": _target_score_profiles(
                    x[heldout_idx],
                    pred_mean,
                    feature_names,
                    profile_nll=profile_nll,
                ),
                **metrics,
            }
        )
        fallback_total += int(fallback_count)
        heldout_total += int(heldout_idx.size)
        train_stratum_counts.append(int(len(means_by_label)))
        y_rows.append(x[heldout_idx])
        pred_rows.append(pred_mean)
        nll_rows.append(nll)
        profile_nll_rows.append(profile_nll)
    out = _generation_artifact(
        schema="scope_static_stage3c_public_stratified_null_metrics_v1",
        model_name="public_stratified_null_diagonal_gaussian",
        description="Fold-local diagonal visible generator conditioned only on public Stage 3A metadata strata.",
        feature_names=feature_names,
        y_rows=y_rows,
        pred_rows=pred_rows,
        nll_rows=nll_rows,
        profile_nll_rows=profile_nll_rows,
        fold_rows=fold_rows,
        uses_evaluator_labels=False,
    )
    out["stratification_audit"] = {
        "schema": "scope_static_stage3c_public_stratified_null_audit_v1",
        "description": "Strong no-oracle baseline: condition visible replay on public Stage 3A strata, never on labels, paths, samples, or learned assignments.",
        "public_stratification_fields": [str(field) for field in public_stratification_fields],
        "min_stratum_train_rows": int(min_stratum_train_rows),
        "uses_evaluator_labels": False,
        "uses_learned_assignments": False,
        "uses_context_path_sample_ids": False,
        "fit_from_training_fold_only": True,
        "record_count": int(x.shape[0]),
        "stratum_count": int(label_audit["stratum_count"]),
        "stratum_count_positive": int(label_audit["stratum_count"]) > 0,
        "public_fields_available": bool(label_audit["public_fields_available"]),
        "fallback_to_global_heldout_count": int(fallback_total),
        "heldout_count": int(heldout_total),
        "fallback_to_global_fraction": float(fallback_total / max(1, heldout_total)),
        "mean_train_stratum_count": float(np.mean(train_stratum_counts)) if train_stratum_counts else 0.0,
        "label_audit": label_audit,
    }
    return out


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
        fold_rows.append(
            {
                "fold": int(fold_idx),
                "train_count": int(train_idx.size),
                "heldout_count": int(heldout_idx.size),
                "target_score_profiles": _target_score_profiles(
                    x[heldout_idx],
                    pred_mean,
                    feature_names,
                    profile_nll={},
                ),
                **metrics,
            }
        )
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
        profile_nll_rows=[],
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
    profile_nll_rows = []
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
        profile_nll = _label_target_profile_nll(
            x[heldout_idx],
            component_rows,
            means,
            variances,
            feature_names,
            full_nll=nll,
        )
        metrics = _score_generation(x[heldout_idx], pred_mean, nll, feature_names)
        fold_rows.append(
            {
                "fold": int(fold_idx),
                "train_count": int(train_idx.size),
                "heldout_count": int(heldout_idx.size),
                "oracle_class_count": int(len(class_names)),
                "target_score_profiles": _target_score_profiles(
                    x[heldout_idx],
                    pred_mean,
                    feature_names,
                    profile_nll=profile_nll,
                ),
                **metrics,
            }
        )
        y_rows.append(x[heldout_idx])
        pred_rows.append(pred_mean)
        nll_rows.append(nll)
        profile_nll_rows.append(profile_nll)
    out = _generation_artifact(
        schema="scope_static_stage3c_oracle_assignment_comparator_metrics_v1",
        model_name="oracle_assignment_comparator",
        description="Evaluator-only train-fold class prototypes selected by heldout oracle label.",
        feature_names=feature_names,
        y_rows=y_rows,
        pred_rows=pred_rows,
        nll_rows=nll_rows,
        profile_nll_rows=profile_nll_rows,
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
    stratified_null_metrics: dict[str, object],
    mean_only_baseline_metrics: dict[str, object],
    oracle_assignment_comparator_metrics: dict[str, object],
) -> dict[str, object]:
    predicted = dict(predicted_assignment_metrics.get("overall", {}))
    global_null = dict(global_null_metrics.get("overall", {}))
    stratified_null = dict(stratified_null_metrics.get("overall", {}))
    mean_only = dict(mean_only_baseline_metrics.get("overall", {}))
    oracle = dict(oracle_assignment_comparator_metrics.get("overall", {}))
    metric = _effective_primary_generation_likelihood_metric(predicted)
    primary_target_profile = _effective_primary_target_score_profile(predicted_assignment_metrics)
    return {
        "schema": "scope_static_stage3c_prototype_generation_metrics_v1",
        "heldout_generation_protocol": "fold-local generators fit on Stage 3A train folds and scored on validation+test heldout rows",
        "primary_generation_likelihood_metric": metric,
        "primary_target_score_profile": primary_target_profile,
        "secondary_continuous_density_diagnostic": SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC,
        "primary_likelihood_report": primary_likelihood_report(
            predicted_assignment=predicted,
            oracle_assignment=oracle,
            global_null=global_null,
            stratified_null=stratified_null,
            mean_only=mean_only,
            metric=metric,
        ),
        "predicted_assignment_model": predicted,
        "global_null_model": global_null,
        "stratified_null_model": stratified_null,
        "mean_only_baseline": mean_only,
        "oracle_assignment_comparator_evaluator_only": oracle,
        "global_null_lift": _lift(predicted, global_null),
        "stratified_null_lift": _lift(predicted, stratified_null),
        "mean_only_lift": _lift(predicted, mean_only),
        "oracle_comparator_gap": _gap(predicted, oracle),
        "feature_block_lift": _feature_block_lift_report(
            predicted_assignment_metrics=predicted_assignment_metrics,
            global_null_metrics=global_null_metrics,
            stratified_null_metrics=stratified_null_metrics,
            mean_only_baseline_metrics=mean_only_baseline_metrics,
            oracle_assignment_comparator_metrics=oracle_assignment_comparator_metrics,
        ),
        "target_score_profile_report": _target_score_profile_report(
            predicted_assignment_metrics=predicted_assignment_metrics,
            global_null_metrics=global_null_metrics,
            stratified_null_metrics=stratified_null_metrics,
            mean_only_baseline_metrics=mean_only_baseline_metrics,
            oracle_assignment_comparator_metrics=oracle_assignment_comparator_metrics,
        ),
    }


def primary_likelihood_report(
    *,
    predicted_assignment: dict[str, object],
    oracle_assignment: dict[str, object],
    global_null: dict[str, object],
    stratified_null: dict[str, object],
    mean_only: dict[str, object],
    metric: str | None = None,
) -> dict[str, object]:
    metric = str(metric or _effective_primary_generation_likelihood_metric(predicted_assignment))
    metric_kind = (
        "positive_discrete_probability_mass_nll"
        if metric == PRIMARY_GENERATION_LIKELIHOOD_METRIC
        else "diagonal_gaussian_visible_density_nll"
    )
    return {
        "schema": "scope_static_stage3c_primary_likelihood_report_v1",
        "metric": metric,
        "metric_kind": metric_kind,
        "lower_is_better": True,
        "predicted_assignment": _optional_float(predicted_assignment.get(metric)),
        "oracle_assignment_comparator": _optional_float(oracle_assignment.get(metric)),
        "predicted_minus_oracle_gap": _optional_difference(predicted_assignment.get(metric), oracle_assignment.get(metric)),
        "global_null": _optional_float(global_null.get(metric)),
        "stratified_null": _optional_float(stratified_null.get(metric)),
        "mean_only_baseline": _optional_float(mean_only.get(metric)),
        "global_null_minus_predicted_lift": _optional_difference(global_null.get(metric), predicted_assignment.get(metric)),
        "stratified_null_minus_predicted_lift": _optional_difference(stratified_null.get(metric), predicted_assignment.get(metric)),
        "mean_only_minus_predicted_lift": _optional_difference(mean_only.get(metric), predicted_assignment.get(metric)),
    }


def _target_score_profile_report(
    *,
    predicted_assignment_metrics: dict[str, object],
    global_null_metrics: dict[str, object],
    stratified_null_metrics: dict[str, object],
    mean_only_baseline_metrics: dict[str, object],
    oracle_assignment_comparator_metrics: dict[str, object],
) -> dict[str, object]:
    predicted = _profiles_from_generation_metrics(predicted_assignment_metrics)
    global_null = _profiles_from_generation_metrics(global_null_metrics)
    stratified_null = _profiles_from_generation_metrics(stratified_null_metrics)
    mean_only = _profiles_from_generation_metrics(mean_only_baseline_metrics)
    oracle = _profiles_from_generation_metrics(oracle_assignment_comparator_metrics)
    profile_names = list(TARGET_SCORE_PROFILE_NAMES)
    for source in (predicted, global_null, stratified_null, mean_only, oracle):
        for name in source:
            if name not in profile_names:
                profile_names.append(name)
    profiles: dict[str, object] = {}
    for name in profile_names:
        pred = dict(predicted.get(name, {}))
        glob = dict(global_null.get(name, {}))
        strat = dict(stratified_null.get(name, {}))
        mean = dict(mean_only.get(name, {}))
        ora = dict(oracle.get(name, {}))
        profiles[name] = {
            "profile": name,
            "target_feature_count": int(pred.get("target_feature_count", glob.get("target_feature_count", 0)) or 0),
            "included_blocks": list(pred.get("included_blocks", glob.get("included_blocks", [])) or []),
            "metric_definition": pred.get("metric_definition", glob.get("metric_definition")),
            "gaussian_density_nll": {
                "predicted_assignment": _optional_float(pred.get("gaussian_density_nll")),
                "global_null": _optional_float(glob.get("gaussian_density_nll")),
                "stratified_null": _optional_float(strat.get("gaussian_density_nll")),
                "mean_only_baseline": _optional_float(mean.get("gaussian_density_nll")),
                "oracle_assignment_comparator": _optional_float(ora.get("gaussian_density_nll")),
                "global_null_minus_predicted_lift": _optional_difference(
                    glob.get("gaussian_density_nll"),
                    pred.get("gaussian_density_nll"),
                ),
                "mean_only_minus_predicted_lift": _optional_difference(
                    mean.get("gaussian_density_nll"),
                    pred.get("gaussian_density_nll"),
                ),
                "stratified_null_minus_predicted_lift": _optional_difference(
                    strat.get("gaussian_density_nll"),
                    pred.get("gaussian_density_nll"),
                ),
            },
            "gaussian_density_nll_per_feature": {
                "predicted_assignment": _optional_float(pred.get("gaussian_density_nll_per_feature")),
                "global_null": _optional_float(glob.get("gaussian_density_nll_per_feature")),
                "stratified_null": _optional_float(strat.get("gaussian_density_nll_per_feature")),
                "mean_only_baseline": _optional_float(mean.get("gaussian_density_nll_per_feature")),
                "oracle_assignment_comparator": _optional_float(ora.get("gaussian_density_nll_per_feature")),
                "global_null_minus_predicted_lift": _optional_difference(
                    glob.get("gaussian_density_nll_per_feature"),
                    pred.get("gaussian_density_nll_per_feature"),
                ),
                "mean_only_minus_predicted_lift": _optional_difference(
                    mean.get("gaussian_density_nll_per_feature"),
                    pred.get("gaussian_density_nll_per_feature"),
                ),
                "stratified_null_minus_predicted_lift": _optional_difference(
                    strat.get("gaussian_density_nll_per_feature"),
                    pred.get("gaussian_density_nll_per_feature"),
                ),
            },
            "raw_visible_feature_mae": {
                "predicted_assignment": _optional_float(pred.get("raw_visible_feature_mae")),
                "global_null": _optional_float(glob.get("raw_visible_feature_mae")),
                "stratified_null": _optional_float(strat.get("raw_visible_feature_mae")),
                "mean_only_baseline": _optional_float(mean.get("raw_visible_feature_mae")),
                "oracle_assignment_comparator": _optional_float(ora.get("raw_visible_feature_mae")),
                "global_null_minus_predicted_lift": _optional_difference(
                    glob.get("raw_visible_feature_mae"),
                    pred.get("raw_visible_feature_mae"),
                ),
                "mean_only_minus_predicted_lift": _optional_difference(
                    mean.get("raw_visible_feature_mae"),
                    pred.get("raw_visible_feature_mae"),
                ),
                "stratified_null_minus_predicted_lift": _optional_difference(
                    strat.get("raw_visible_feature_mae"),
                    pred.get("raw_visible_feature_mae"),
                ),
            },
        }
    return {
        "schema": "scope_static_stage3c_target_score_profile_report_v1",
        "description": "Headline scoring profiles separating full target, raw observation target, and equal-block-weight target views.",
        "profiles": profiles,
        "block_profiles": _target_score_block_profile_report(
            predicted_assignment_metrics=predicted_assignment_metrics,
            global_null_metrics=global_null_metrics,
            stratified_null_metrics=stratified_null_metrics,
            mean_only_baseline_metrics=mean_only_baseline_metrics,
            oracle_assignment_comparator_metrics=oracle_assignment_comparator_metrics,
        ),
    }


def _target_score_block_profile_report(
    *,
    predicted_assignment_metrics: dict[str, object],
    global_null_metrics: dict[str, object],
    stratified_null_metrics: dict[str, object],
    mean_only_baseline_metrics: dict[str, object],
    oracle_assignment_comparator_metrics: dict[str, object],
) -> dict[str, object]:
    predicted = _block_profiles_from_generation_metrics(predicted_assignment_metrics)
    global_null = _block_profiles_from_generation_metrics(global_null_metrics)
    stratified_null = _block_profiles_from_generation_metrics(stratified_null_metrics)
    mean_only = _block_profiles_from_generation_metrics(mean_only_baseline_metrics)
    oracle = _block_profiles_from_generation_metrics(oracle_assignment_comparator_metrics)
    block_names = sorted(set(predicted) | set(global_null) | set(stratified_null) | set(mean_only) | set(oracle))
    blocks: dict[str, object] = {}
    for name in block_names:
        pred = dict(predicted.get(name, {}))
        glob = dict(global_null.get(name, {}))
        strat = dict(stratified_null.get(name, {}))
        mean = dict(mean_only.get(name, {}))
        ora = dict(oracle.get(name, {}))
        blocks[name] = {
            "block": name,
            "target_feature_count": int(pred.get("target_feature_count", glob.get("target_feature_count", 0)) or 0),
            "metric_definition": pred.get("metric_definition", glob.get("metric_definition")),
            "gaussian_density_nll": {
                "predicted_assignment": _optional_float(pred.get("gaussian_density_nll")),
                "global_null": _optional_float(glob.get("gaussian_density_nll")),
                "stratified_null": _optional_float(strat.get("gaussian_density_nll")),
                "mean_only_baseline": _optional_float(mean.get("gaussian_density_nll")),
                "oracle_assignment_comparator": _optional_float(ora.get("gaussian_density_nll")),
                "global_null_minus_predicted_lift": _optional_difference(
                    glob.get("gaussian_density_nll"),
                    pred.get("gaussian_density_nll"),
                ),
                "stratified_null_minus_predicted_lift": _optional_difference(
                    strat.get("gaussian_density_nll"),
                    pred.get("gaussian_density_nll"),
                ),
            },
            "gaussian_density_nll_per_feature": {
                "predicted_assignment": _optional_float(pred.get("gaussian_density_nll_per_feature")),
                "global_null": _optional_float(glob.get("gaussian_density_nll_per_feature")),
                "stratified_null": _optional_float(strat.get("gaussian_density_nll_per_feature")),
                "mean_only_baseline": _optional_float(mean.get("gaussian_density_nll_per_feature")),
                "oracle_assignment_comparator": _optional_float(ora.get("gaussian_density_nll_per_feature")),
                "global_null_minus_predicted_lift": _optional_difference(
                    glob.get("gaussian_density_nll_per_feature"),
                    pred.get("gaussian_density_nll_per_feature"),
                ),
                "stratified_null_minus_predicted_lift": _optional_difference(
                    strat.get("gaussian_density_nll_per_feature"),
                    pred.get("gaussian_density_nll_per_feature"),
                ),
            },
            "raw_visible_feature_mae": {
                "predicted_assignment": _optional_float(pred.get("raw_visible_feature_mae")),
                "global_null": _optional_float(glob.get("raw_visible_feature_mae")),
                "stratified_null": _optional_float(strat.get("raw_visible_feature_mae")),
                "mean_only_baseline": _optional_float(mean.get("raw_visible_feature_mae")),
                "oracle_assignment_comparator": _optional_float(ora.get("raw_visible_feature_mae")),
                "global_null_minus_predicted_lift": _optional_difference(
                    glob.get("raw_visible_feature_mae"),
                    pred.get("raw_visible_feature_mae"),
                ),
                "stratified_null_minus_predicted_lift": _optional_difference(
                    strat.get("raw_visible_feature_mae"),
                    pred.get("raw_visible_feature_mae"),
                ),
            },
        }
    return {
        "schema": "scope_static_stage3c_target_score_block_profile_report_v1",
        "blocks": blocks,
    }


def _profiles_from_generation_metrics(metrics: dict[str, object]) -> dict[str, dict[str, object]]:
    target = metrics.get("target_score_profiles", {})
    if not isinstance(target, dict):
        return {}
    profiles = target.get("profiles", {})
    if not isinstance(profiles, dict):
        return {}
    return {str(name): dict(value) for name, value in profiles.items() if isinstance(value, dict)}


def _block_profiles_from_generation_metrics(metrics: dict[str, object]) -> dict[str, dict[str, object]]:
    target = metrics.get("target_score_profiles", {})
    if not isinstance(target, dict):
        return {}
    profiles = target.get("block_profiles", {})
    if not isinstance(profiles, dict):
        return {}
    return {str(name): dict(value) for name, value in profiles.items() if isinstance(value, dict)}


def assignment_source_audit(
    *,
    s3b1_dir: Path,
    responsibilities: np.ndarray,
    s3b1_metrics: dict[str, object] | None = None,
) -> dict[str, object]:
    metrics = {} if s3b1_metrics is None else dict(s3b1_metrics)
    summary = dict(metrics.get("learned_assignment_summary", {})) if isinstance(metrics.get("learned_assignment_summary", {}), dict) else {}
    k_protocol = dict(metrics.get("k_selection_protocol", {})) if isinstance(metrics.get("k_selection_protocol", {}), dict) else {}
    return {
        "schema": "scope_static_stage3c_assignment_source_audit_v1",
        "assignment_path": str(s3b1_dir / "learned_assignments.npy"),
        "source_stage": "Stage 3B.1",
        "row_count": int(responsibilities.shape[0]),
        "prototype_count": int(responsibilities.shape[1]) if responsibilities.ndim == 2 else 0,
        "selected_k": None if summary.get("selected_k") is None else int(summary.get("selected_k")),
        "selected_k_mode": None if summary.get("selected_k_mode") is None else str(summary.get("selected_k_mode")),
        "k_selection_protocol": k_protocol,
        "k_prior_contract": _stage3b1_k_prior_contract(metrics),
        "row_stochastic": bool(responsibilities.size == 0 or np.allclose(np.sum(responsibilities, axis=1), 1.0)),
        "uses_evaluator_labels": False,
        "assignment_is_visible_only_b1_output": True,
    }


def _stage3b1_k_prior_contract(s3b1_metrics: dict[str, object]) -> dict[str, object]:
    protocol = dict(s3b1_metrics.get("k_selection_protocol", {})) if isinstance(s3b1_metrics.get("k_selection_protocol", {}), dict) else {}
    contract = protocol.get("k_prior_contract")
    if isinstance(contract, dict):
        return dict(contract)
    config = dict(s3b1_metrics.get("config", {})) if isinstance(s3b1_metrics.get("config", {}), dict) else {}
    contract = config.get("k_prior_contract")
    if isinstance(contract, dict):
        return dict(contract)
    boundary = dict(s3b1_metrics.get("claim_boundary", {})) if isinstance(s3b1_metrics.get("claim_boundary", {}), dict) else {}
    contract = boundary.get("k_prior_contract")
    if isinstance(contract, dict):
        return dict(contract)
    return {
        "schema": "scope_static_stage3b1_k_prior_contract_v1",
        "enabled": False,
        "source": None,
        "mechanism_count_prior": None,
        "overcomplete_multiplier": None,
        "role": "not_declared",
        "uses_google_true_labels": False,
        "used_for_feature_construction": False,
        "used_for_oracle_scoring": False,
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
    stratified_null_metrics: dict[str, object],
    mean_only_baseline_metrics: dict[str, object],
    oracle_assignment_comparator_metrics: dict[str, object],
    soft_family_classification_metrics: dict[str, object],
    soft_family_strength_location_audit: dict[str, object],
    mechanism_taxonomy_contract_audit: dict[str, object],
    leakage_audit: dict[str, object],
    evaluator_mode: str = EVALUATOR_MODE_CONTROLLED_CATALOG,
) -> dict[str, object]:
    mode = _normalize_evaluator_mode(evaluator_mode)
    predicted = dict(predicted_assignment_metrics.get("overall", {}))
    global_null = dict(global_null_metrics.get("overall", {}))
    stratified_null = dict(stratified_null_metrics.get("overall", {}))
    mean_only = dict(mean_only_baseline_metrics.get("overall", {}))
    oracle = dict(oracle_assignment_comparator_metrics.get("overall", {}))
    soft_family = dict(soft_family_classification_metrics)
    strength_location = dict(soft_family_strength_location_audit)
    taxonomy_contract = dict(mechanism_taxonomy_contract_audit)
    dimension_audit = (
        dict(strength_location.get("mechanism_dimension_recovery_audit", {}))
        if isinstance(strength_location.get("mechanism_dimension_recovery_audit", {}), dict)
        else {}
    )
    contract_typed_recovery = (
        dict(strength_location.get("contract_typed_recovery_metrics", {}))
        if isinstance(strength_location.get("contract_typed_recovery_metrics", {}), dict)
        else {}
    )
    primary_strength_reference = _primary_strength_reference_frame(strength_location)
    b1_acceptance = dict(s3b1_metrics.get("acceptance_audit", {})) if isinstance(s3b1_metrics.get("acceptance_audit", {}), dict) else {}
    metric = _effective_primary_generation_likelihood_metric(predicted)
    primary_target_profile = _effective_primary_target_score_profile(predicted_assignment_metrics)
    categorical_primary = metric == PRIMARY_GENERATION_LIKELIHOOD_METRIC
    stratification_audit = (
        dict(stratified_null_metrics.get("stratification_audit", {}))
        if isinstance(stratified_null_metrics.get("stratification_audit", {}), dict)
        else {}
    )
    stratified_applicable = int(stratification_audit.get("stratum_count", 0) or 0) > 1
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
        "soft_family_classification_evaluator_only_or_skipped": (
            bool(soft_family.get("evaluator_only", False))
            if mode == EVALUATOR_MODE_CONTROLLED_CATALOG
            else bool(soft_family.get("skipped", False))
        ),
        "soft_family_classification_not_used_for_training": not bool(soft_family.get("used_for_training", True)),
        "soft_family_classification_not_used_for_model_selection": not bool(soft_family.get("used_for_model_selection", True)),
        "soft_family_classification_nmi_is_one": (
            True if mode == EVALUATOR_MODE_NO_ORACLE_LABELS else _is_one(soft_family.get("normalized_mutual_info"))
        ),
        "soft_family_classification_ari_is_one": (
            True if mode == EVALUATOR_MODE_NO_ORACLE_LABELS else _is_one(soft_family.get("adjusted_rand_index"))
        ),
        "soft_family_classification_balanced_accuracy_is_one": (
            True if mode == EVALUATOR_MODE_NO_ORACLE_LABELS else _is_one(soft_family.get("balanced_accuracy"))
        ),
        "soft_family_classification_min_recall_is_one": (
            True if mode == EVALUATOR_MODE_NO_ORACLE_LABELS else _is_one(soft_family.get("min_recall"))
        ),
        "soft_family_strength_location_audit_evaluator_only_or_skipped": (
            bool(strength_location.get("evaluator_only", False))
            if mode == EVALUATOR_MODE_CONTROLLED_CATALOG
            else bool(strength_location.get("skipped", False))
        ),
        "soft_family_strength_location_not_used_for_training": not bool(strength_location.get("used_for_training", True)),
        "soft_family_strength_location_not_used_for_model_selection": not bool(strength_location.get("used_for_model_selection", True)),
        "soft_family_strength_location_is_context_relative": (
            True if mode == EVALUATOR_MODE_NO_ORACLE_LABELS else str(strength_location.get("location_reference_frame", "")) == "context_relative"
        ),
        "soft_family_strength_does_not_claim_physical_parameter_recovery": not bool(
            strength_location.get("claims_physical_parameter_recovery", True)
        ),
        "s5_context_relative_effect_audit_evaluator_only_or_skipped": (
            bool(strength_location.get("evaluator_only", False))
            if mode == EVALUATOR_MODE_CONTROLLED_CATALOG
            else bool(strength_location.get("skipped", False))
        ),
        "s5_context_relative_effect_uses_context_relative_location": (
            True if mode == EVALUATOR_MODE_NO_ORACLE_LABELS else str(strength_location.get("location_reference_frame", "")) == "context_relative"
        ),
        "s5_context_relative_effect_uses_context_relative_strength": (
            True if mode == EVALUATOR_MODE_NO_ORACLE_LABELS else primary_strength_reference == "context_relative"
        ),
        "s5_context_relative_effect_does_not_claim_physical_parameter_recovery": not bool(
            strength_location.get("claims_physical_parameter_recovery", True)
        ),
        "s5_context_relative_effect_recovery_metrics_passed": (
            True
            if mode == EVALUATOR_MODE_NO_ORACLE_LABELS
            else bool(contract_typed_recovery.get("passed", False))
        ),
        "mechanism_taxonomy_contract_audit_passed": bool(taxonomy_contract.get("passed", False)),
        "mechanism_dimension_recovery_audit_evaluator_only_or_skipped": (
            bool(dimension_audit.get("evaluator_only", False))
            if mode == EVALUATOR_MODE_CONTROLLED_CATALOG
            else bool(dimension_audit.get("skipped", False))
        ),
        "mechanism_dimension_recovery_audit_not_used_for_training": not bool(dimension_audit.get("used_for_training", True)),
        "mechanism_dimension_recovery_audit_not_used_for_model_selection": not bool(dimension_audit.get("used_for_model_selection", True)),
        "mechanism_dimension_recovery_does_not_claim_physical_parameter_recovery": not bool(
            dimension_audit.get("claims_physical_parameter_recovery", True)
        ),
        "mechanism_dimension_recovery_audit_passed": (
            True if mode == EVALUATOR_MODE_NO_ORACLE_LABELS else bool(dimension_audit.get("passed", False))
        ),
        "s5_contract_typed_recovery_metrics_passed": (
            True if mode == EVALUATOR_MODE_NO_ORACLE_LABELS else bool(contract_typed_recovery.get("passed", False))
        ),
        "primary_generation_likelihood_metric_reported": predicted.get(metric) is not None,
        "primary_categorical_population_nll_reported": (
            predicted.get(PRIMARY_GENERATION_LIKELIHOOD_METRIC) is not None if categorical_primary else True
        ),
        "oracle_categorical_population_nll_reported": (
            True
            if mode == EVALUATOR_MODE_NO_ORACLE_LABELS
            else True
            if not categorical_primary
            else oracle.get(PRIMARY_GENERATION_LIKELIHOOD_METRIC) is not None
        ),
        "categorical_population_group_count_positive": (
            int(predicted.get("categorical_population_group_count", 0)) > 0 if categorical_primary else True
        ),
        "heldout_generation_beats_global_null_primary_likelihood": (
            _metric_less(predicted, global_null, metric)
            if primary_target_profile == TARGET_SCORE_PROFILE_FULL
            else _target_profile_metric_less(predicted_assignment_metrics, global_null_metrics, primary_target_profile, metric)
        ),
        "stratified_null_metrics_reported": bool(stratified_null),
        "stratified_null_uses_public_fields_only": (
            not bool(stratification_audit.get("uses_evaluator_labels", True))
            and not bool(stratification_audit.get("uses_learned_assignments", True))
            and not bool(stratification_audit.get("uses_context_path_sample_ids", True))
        ),
        "heldout_generation_beats_stratified_null_raw_target_only": (
            True
            if not stratified_applicable
            else _target_profile_metric_less(
                predicted_assignment_metrics,
                stratified_null_metrics,
                TARGET_SCORE_PROFILE_RAW,
                "gaussian_density_nll",
            )
        ),
        "heldout_generation_beats_global_null_categorical_population_nll": _metric_less(
            predicted,
            global_null,
            PRIMARY_GENERATION_LIKELIHOOD_METRIC,
        )
        if categorical_primary
        else True,
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
        "primary_generation_likelihood_metric": metric,
        "primary_target_score_profile": primary_target_profile,
        "checks": checks,
    }


def _no_oracle_stage3a5_metrics() -> dict[str, object]:
    return {
        "schema": "scope_static_stage3a5_no_oracle_placeholder_v1",
        "evaluator_mode": EVALUATOR_MODE_NO_ORACLE_LABELS,
        "acceptance_audit": {"passed": True, "checks": {"stage3a5_not_required_without_oracle_labels": True}},
    }


def stage3c_claim_gate_audit(
    *,
    s3b1_metrics: dict[str, object],
    s3b1_residualized_metrics: dict[str, object] | None,
    stage3d4b_metrics: dict[str, object] | None,
    stage5b1_metrics: dict[str, object] | None,
    evaluator_mode: str = EVALUATOR_MODE_CONTROLLED_CATALOG,
) -> dict[str, object]:
    mode = _normalize_evaluator_mode(evaluator_mode)
    if mode == EVALUATOR_MODE_NO_ORACLE_LABELS:
        checks = {
            "no_oracle_mode_diagnostic_gate": True,
            "claim_allowed_without_controlled_s5b1": False,
        }
        return {
            "schema": "scope_static_stage3c_claim_gate_audit_v1",
            "description": "No-oracle mode may report replay diagnostics, but controlled S3B1/S5B1 claim gates are unavailable.",
            "claim_allowed": False,
            "diagnostic_only": True,
            "evaluator_mode": mode,
            "checks": checks,
            "passed": False,
        }
    raw_b1_passed = artifact_acceptance_passed(s3b1_metrics)
    residual_b1_passed = artifact_acceptance_passed(s3b1_residualized_metrics)
    transform = (
        dict(s3b1_residualized_metrics.get("visible_transform_audit", {}))
        if isinstance(s3b1_residualized_metrics, dict) and isinstance(s3b1_residualized_metrics.get("visible_transform_audit", {}), dict)
        else {}
    )
    residual_claim_allowed = bool(transform.get("claim_allowed", False))
    d4b_passed = stage3d4b_claim_gate_passed(stage3d4b_metrics)
    d4b_legacy_acceptance_passed = artifact_acceptance_passed(stage3d4b_metrics)
    s5b1_passed = _stage5b1_property_recovery_passed(stage5b1_metrics)
    s5b1_claim_passed = _stage5b1_claim_gate_passed(stage5b1_metrics)
    s5b1_decision_passed = str((stage5b1_metrics or {}).get("decision", "")) == "stage5b1_property_recovery_passed"
    s5b1_source = (
        dict(stage5b1_metrics.get("assignment_source_audit", {}))
        if isinstance(stage5b1_metrics, dict) and isinstance(stage5b1_metrics.get("assignment_source_audit", {}), dict)
        else {}
    )
    s5b1_assignment_source = str(s5b1_source.get("assignment_source", ""))
    s5b1_uses_raw = s5b1_assignment_source in {
        "stage3b1",
        "raw_stage3b1",
        "s3b1_raw",
    }
    s5b1_uses_postmerge = s5b1_assignment_source in {
        "stage3d4b_postmerge",
        "s3d4b_postmerge",
        "postmerge",
    }
    raw_assignment_source_ready = bool(raw_b1_passed and s5b1_uses_raw)
    postmerge_assignment_source_ready = bool(d4b_passed and s5b1_uses_postmerge)
    raw_or_postmerge_assignment_source_recognized = bool(s5b1_uses_raw or s5b1_uses_postmerge)
    raw_or_postmerge_assignment_source = bool(raw_assignment_source_ready or postmerge_assignment_source_ready)
    checks = {
        "s3b1_raw_acceptance_passed": raw_b1_passed,
        "s3b1_residualized_diagnostic_reported": bool(s3b1_residualized_metrics is not None),
        "s3b1_residualized_diagnostic_passed_if_present": (True if s3b1_residualized_metrics is None else residual_b1_passed),
        "s3b1_residualized_not_used_as_claim_assignment_source": True,
        "stage3d4b_overcomplete_postmerge_passed_if_present": (True if stage3d4b_metrics is None else d4b_passed),
        "s5b1_assignment_source_is_raw_or_postmerge": raw_or_postmerge_assignment_source_recognized,
        "s5b1_assignment_source_matches_raw_or_postmerge_gate": raw_or_postmerge_assignment_source_recognized,
        "raw_or_postmerge_assignment_source_available": raw_or_postmerge_assignment_source,
        "s3b1_residualized_or_stage3d4b_overcomplete_gate_passed": raw_or_postmerge_assignment_source,
        "s5b1_property_recovery_acceptance_passed": s5b1_passed,
        "s5b1_property_recovery_decision_passed": s5b1_decision_passed,
        "s5b1_claim_gate_passed": s5b1_claim_passed,
        "s3c_claim_not_allowed_from_raw_s3b1_alone": True,
    }
    claim_allowed = bool(all(checks.values()))
    return {
        "schema": "scope_static_stage3c_claim_gate_audit_v1",
        "description": "Scientific claim gate for assignment-dependent S3C/S5 replay/effect claims.",
        "claim_allowed": claim_allowed,
        "diagnostic_only": not claim_allowed,
        "evaluator_mode": mode,
        "raw_s3b1_decision": s3b1_metrics.get("decision"),
        "residualized_s3b1_decision": None if not isinstance(s3b1_residualized_metrics, dict) else s3b1_residualized_metrics.get("decision"),
        "stage3d4b_decision": None if not isinstance(stage3d4b_metrics, dict) else stage3d4b_metrics.get("decision"),
        "stage3d4b_legacy_all_exact_acceptance_passed": d4b_legacy_acceptance_passed,
        "stage3d4b_claimable_gate": stage3d4b_claim_gate_audit(stage3d4b_metrics),
        "stage5b1_decision": None if not isinstance(stage5b1_metrics, dict) else stage5b1_metrics.get("decision"),
        "stage5b1_claim_allowed_flag": _stage5b1_claim_allowed_flag(stage5b1_metrics),
        "residualized_s3b1_claim_allowed_flag": residual_claim_allowed,
        "residualized_s3b1_role": "diagnostic_only_shortcut_and_bleed_audit",
        "s5b1_assignment_source": s5b1_assignment_source or None,
        "s5b1_assignment_source_ready": raw_or_postmerge_assignment_source,
        "claim_assignment_source": (
            "stage3d4b_postmerge"
            if postmerge_assignment_source_ready
            else ("stage3b1_raw" if raw_assignment_source_ready else None)
        ),
        "checks": checks,
        "passed": claim_allowed,
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


def _responsibility_target_profile_nll(
    x: np.ndarray,
    responsibilities: np.ndarray,
    means: np.ndarray,
    variances: np.ndarray,
    feature_names: list[str],
    *,
    full_nll: np.ndarray,
) -> dict[str, object]:
    masks = _target_profile_feature_masks(feature_names)
    profiles: dict[str, np.ndarray] = {TARGET_SCORE_PROFILE_FULL: np.asarray(full_nll, dtype=np.float64)}
    raw_mask = masks.get(TARGET_SCORE_PROFILE_RAW)
    if raw_mask is not None and bool(np.any(raw_mask)):
        profiles[TARGET_SCORE_PROFILE_RAW] = _conditional_responsibility_nll(
            x[:, raw_mask],
            responsibilities,
            np.asarray(means, dtype=np.float64)[:, raw_mask],
            np.asarray(variances, dtype=np.float64)[:, raw_mask],
        )
    blocks: dict[str, np.ndarray] = {}
    for block_name, mask in _feature_block_masks(feature_names).items():
        if bool(np.any(mask)):
            blocks[block_name] = _conditional_responsibility_nll(
                x[:, mask],
                responsibilities,
                np.asarray(means, dtype=np.float64)[:, mask],
                np.asarray(variances, dtype=np.float64)[:, mask],
            )
    return {"profiles": profiles, "blocks": blocks}


def _global_target_profile_nll(
    x: np.ndarray,
    mean: np.ndarray,
    variance: np.ndarray,
    feature_names: list[str],
    *,
    full_nll: np.ndarray,
) -> dict[str, object]:
    masks = _target_profile_feature_masks(feature_names)
    profiles: dict[str, np.ndarray] = {TARGET_SCORE_PROFILE_FULL: np.asarray(full_nll, dtype=np.float64)}
    raw_mask = masks.get(TARGET_SCORE_PROFILE_RAW)
    if raw_mask is not None and bool(np.any(raw_mask)):
        profiles[TARGET_SCORE_PROFILE_RAW] = -_diag_log_prob(
            x[:, raw_mask],
            np.asarray(mean, dtype=np.float64)[None, raw_mask],
            np.asarray(variance, dtype=np.float64)[None, raw_mask],
        )[:, 0]
    blocks: dict[str, np.ndarray] = {}
    for block_name, mask in _feature_block_masks(feature_names).items():
        if bool(np.any(mask)):
            blocks[block_name] = -_diag_log_prob(
                x[:, mask],
                np.asarray(mean, dtype=np.float64)[None, mask],
                np.asarray(variance, dtype=np.float64)[None, mask],
            )[:, 0]
    return {"profiles": profiles, "blocks": blocks}


def _label_target_profile_nll(
    x: np.ndarray,
    component_rows: np.ndarray,
    means: np.ndarray,
    variances: np.ndarray,
    feature_names: list[str],
    *,
    full_nll: np.ndarray,
) -> dict[str, object]:
    masks = _target_profile_feature_masks(feature_names)
    profiles: dict[str, np.ndarray] = {TARGET_SCORE_PROFILE_FULL: np.asarray(full_nll, dtype=np.float64)}
    raw_mask = masks.get(TARGET_SCORE_PROFILE_RAW)
    row_indices = np.arange(int(x.shape[0]))
    if raw_mask is not None and bool(np.any(raw_mask)):
        profiles[TARGET_SCORE_PROFILE_RAW] = -_diag_log_prob(
            x[:, raw_mask],
            np.asarray(means, dtype=np.float64)[:, raw_mask],
            np.asarray(variances, dtype=np.float64)[:, raw_mask],
        )[row_indices, component_rows]
    blocks: dict[str, np.ndarray] = {}
    for block_name, mask in _feature_block_masks(feature_names).items():
        if bool(np.any(mask)):
            blocks[block_name] = -_diag_log_prob(
                x[:, mask],
                np.asarray(means, dtype=np.float64)[:, mask],
                np.asarray(variances, dtype=np.float64)[:, mask],
            )[row_indices, component_rows]
    return {"profiles": profiles, "blocks": blocks}


def _rowwise_target_profile_nll(
    x: np.ndarray,
    means: np.ndarray,
    variances: np.ndarray,
    feature_names: list[str],
    *,
    full_nll: np.ndarray,
) -> dict[str, object]:
    masks = _target_profile_feature_masks(feature_names)
    profiles: dict[str, np.ndarray] = {TARGET_SCORE_PROFILE_FULL: np.asarray(full_nll, dtype=np.float64)}
    raw_mask = masks.get(TARGET_SCORE_PROFILE_RAW)
    if raw_mask is not None and bool(np.any(raw_mask)):
        profiles[TARGET_SCORE_PROFILE_RAW] = _rowwise_diag_nll(x[:, raw_mask], means[:, raw_mask], variances[:, raw_mask])
    blocks: dict[str, np.ndarray] = {}
    for block_name, mask in _feature_block_masks(feature_names).items():
        if bool(np.any(mask)):
            blocks[block_name] = _rowwise_diag_nll(x[:, mask], means[:, mask], variances[:, mask])
    return {"profiles": profiles, "blocks": blocks}


def _rowwise_diag_nll(x: np.ndarray, means: np.ndarray, variances: np.ndarray) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    mu = np.asarray(means, dtype=np.float64)
    var = np.maximum(np.asarray(variances, dtype=np.float64), MIN_WEIGHT)
    if arr.shape != mu.shape or arr.shape != var.shape:
        raise ValueError("rowwise diagonal NLL inputs must have matching shapes")
    if arr.size == 0:
        return np.zeros(int(arr.shape[0]), dtype=np.float64)
    log_norm = np.sum(np.log(2.0 * np.pi * var), axis=1)
    quad = np.sum((arr - mu) * (arr - mu) / var, axis=1)
    return 0.5 * (log_norm + quad)


def _concat_target_profile_nll(rows: list[dict[str, object]]) -> dict[str, object]:
    profile_rows: dict[str, list[np.ndarray]] = {}
    block_rows: dict[str, list[np.ndarray]] = {}
    for row in rows:
        profiles = dict(row.get("profiles", {})) if isinstance(row.get("profiles", {}), dict) else {}
        blocks = dict(row.get("blocks", {})) if isinstance(row.get("blocks", {}), dict) else {}
        for name, values in profiles.items():
            arr = np.asarray(values, dtype=np.float64)
            if arr.size:
                profile_rows.setdefault(str(name), []).append(arr)
        for name, values in blocks.items():
            arr = np.asarray(values, dtype=np.float64)
            if arr.size:
                block_rows.setdefault(str(name), []).append(arr)
    return {
        "profiles": {name: np.concatenate(parts, axis=0) for name, parts in profile_rows.items()},
        "blocks": {name: np.concatenate(parts, axis=0) for name, parts in block_rows.items()},
    }


def _target_profile_feature_masks(feature_names: list[str]) -> dict[str, np.ndarray]:
    return {
        TARGET_SCORE_PROFILE_FULL: np.ones(len(feature_names), dtype=bool),
        TARGET_SCORE_PROFILE_RAW: _raw_feature_mask(feature_names),
    }


def _public_stratification_labels(
    split_manifest: dict[str, object],
    *,
    record_count: int,
    fields: tuple[str, ...],
) -> tuple[np.ndarray, dict[str, object]]:
    labels = np.asarray(["global"] * int(record_count), dtype=object)
    seen = np.zeros(int(record_count), dtype=bool)
    public_available = False
    for row in split_manifest.get("assignment_instances", []):
        if not isinstance(row, dict):
            continue
        idx = int(row.get("record_index", -1))
        if not (0 <= idx < int(record_count)):
            continue
        public_fields = row.get("public_fields", {})
        if not isinstance(public_fields, dict) or not public_fields:
            continue
        public_available = True
        parts = []
        for field in fields:
            value = public_fields.get(field, "unknown")
            parts.append(f"{field}={_stratum_value(value)}")
        labels[idx] = "|".join(parts)
        seen[idx] = True
    if not public_available:
        seen[:] = True
    counts = _label_counts(labels.tolist())
    values = list(counts.values())
    return labels, {
        "schema": "scope_static_stage3c_public_stratification_label_audit_v1",
        "public_fields_available": bool(public_available),
        "fields": [str(field) for field in fields],
        "record_count": int(record_count),
        "assigned_record_count": int(np.sum(seen)),
        "missing_record_count": int(record_count - int(np.sum(seen))),
        "stratum_count": int(len(counts)),
        "min_stratum_count": int(min(values)) if values else 0,
        "max_stratum_count": int(max(values)) if values else 0,
        "singleton_stratum_count": int(sum(1 for value in values if int(value) == 1)),
        "stratum_counts": counts,
    }


def _stratum_value(value: object) -> str:
    text = str(value)
    return text.replace("|", "_").replace("=", "_")


def _label_counts(labels: list[object]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for label in labels:
        key = str(label)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _feature_block_masks(feature_names: list[str]) -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    for block_name, indices in _feature_block_indices(feature_names).items():
        mask = np.zeros(len(feature_names), dtype=bool)
        mask[np.asarray(indices, dtype=np.int64)] = True
        out[block_name] = mask
    return out


def _score_generation(y: np.ndarray, predicted_mean: np.ndarray, nll: np.ndarray, feature_names: list[str]) -> dict[str, object]:
    probability_mask, expectation_mask = _feature_masks(feature_names)
    probability_groups = _probability_groups(feature_names)
    raw_mae = float(np.mean(np.abs(y - predicted_mean))) if y.size else 0.0
    probability_mae = _masked_mae(y, predicted_mean, probability_mask)
    expectation_mae = _masked_mae(y, predicted_mean, expectation_mask)
    gaussian_density_nll = float(np.mean(nll)) if nll.size else 0.0
    categorical_population_nll = None if not probability_groups else _categorical_population_nll(y, predicted_mean, probability_groups)
    return {
        "categorical_population_nll": categorical_population_nll,
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
    profile_nll_rows: list[dict[str, object]] | None,
    fold_rows: list[dict[str, object]],
    uses_evaluator_labels: bool,
) -> dict[str, object]:
    y = np.concatenate(y_rows, axis=0) if y_rows else np.zeros((0, len(feature_names)), dtype=np.float64)
    pred = np.concatenate(pred_rows, axis=0) if pred_rows else np.zeros((0, len(feature_names)), dtype=np.float64)
    nll = np.concatenate(nll_rows, axis=0) if nll_rows else np.zeros(0, dtype=np.float64)
    profile_nll = _concat_target_profile_nll(profile_nll_rows or [])
    overall = _score_generation(y, pred, nll, feature_names)
    if not nll_rows:
        overall["gaussian_nll"] = None
        overall["gaussian_density_nll"] = None
        profile_nll = {}
    primary_metric = _effective_primary_generation_likelihood_metric(overall)
    return {
        "schema": schema,
        "model_name": str(model_name),
        "description": str(description),
        "primary_generation_likelihood_metric": primary_metric,
        "secondary_continuous_density_diagnostic": SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC,
        "uses_evaluator_labels": bool(uses_evaluator_labels),
        "uses_channels_ptms_kraus": False,
        "heldout_row_count": int(y.shape[0]),
        "feature_count": int(y.shape[1]) if y.ndim == 2 else 0,
        "overall": overall,
        "feature_block_metrics": _feature_block_metrics(y, pred, feature_names),
        "target_score_profiles": _target_score_profiles(y, pred, feature_names, profile_nll=profile_nll),
        "fold_metrics": fold_rows,
    }


def _effective_primary_generation_likelihood_metric(overall: dict[str, object]) -> str:
    if int(overall.get("categorical_population_group_count", 0) or 0) > 0 and overall.get(PRIMARY_GENERATION_LIKELIHOOD_METRIC) is not None:
        return PRIMARY_GENERATION_LIKELIHOOD_METRIC
    return FALLBACK_GENERATION_LIKELIHOOD_METRIC


def _effective_primary_target_score_profile(metrics: dict[str, object]) -> str:
    overall = dict(metrics.get("overall", {})) if isinstance(metrics.get("overall", {}), dict) else {}
    if _effective_primary_generation_likelihood_metric(overall) == PRIMARY_GENERATION_LIKELIHOOD_METRIC:
        return TARGET_SCORE_PROFILE_FULL
    profiles = _profiles_from_generation_metrics(metrics)
    raw = dict(profiles.get(TARGET_SCORE_PROFILE_RAW, {}))
    if int(raw.get("target_feature_count", 0) or 0) > 0 and raw.get(FALLBACK_GENERATION_LIKELIHOOD_METRIC) is not None:
        return TARGET_SCORE_PROFILE_RAW
    return TARGET_SCORE_PROFILE_FULL


def _feature_block_metrics(y: np.ndarray, predicted: np.ndarray, feature_names: list[str]) -> dict[str, dict[str, object]]:
    blocks = _feature_block_indices(feature_names)
    out: dict[str, dict[str, object]] = {}
    for block_name, indices in blocks.items():
        cols = np.asarray(indices, dtype=np.int64)
        if y.shape[0] == 0 or cols.size == 0:
            mae = 0.0
            mse = 0.0
            target_abs_mean = 0.0
        else:
            residual = y[:, cols] - predicted[:, cols]
            mae = float(np.mean(np.abs(residual)))
            mse = float(np.mean(residual * residual))
            target_abs_mean = float(np.mean(np.abs(y[:, cols])))
        out[block_name] = {
            "feature_count": int(cols.size),
            "raw_visible_feature_mae": mae,
            "raw_visible_feature_mse": mse,
            "target_abs_mean": target_abs_mean,
        }
    return out


def _target_score_profiles(
    y: np.ndarray,
    predicted: np.ndarray,
    feature_names: list[str],
    *,
    profile_nll: dict[str, object] | None,
) -> dict[str, object]:
    nll_payload = dict(profile_nll or {})
    profile_nlls = dict(nll_payload.get("profiles", {})) if isinstance(nll_payload.get("profiles", {}), dict) else {}
    block_nlls = dict(nll_payload.get("blocks", {})) if isinstance(nll_payload.get("blocks", {}), dict) else {}
    block_indices = _feature_block_indices(feature_names)
    all_mask = np.ones(len(feature_names), dtype=bool)
    raw_mask = _raw_feature_mask(feature_names)
    full = _target_profile_metrics(
        y,
        predicted,
        all_mask,
        _optional_nll_array(profile_nlls.get(TARGET_SCORE_PROFILE_FULL)),
        profile_name=TARGET_SCORE_PROFILE_FULL,
        included_blocks=sorted(block_indices),
        metric_definition="all frozen Stage 3A visible features; current legacy S3C full-target behavior",
    )
    raw = _target_profile_metrics(
        y,
        predicted,
        raw_mask,
        _optional_nll_array(profile_nlls.get(TARGET_SCORE_PROFILE_RAW)),
        profile_name=TARGET_SCORE_PROFILE_RAW,
        included_blocks=[name for name in sorted(block_indices) if name.startswith("raw__")],
        metric_definition="only raw learner-visible observation features; public metadata excluded",
    )
    block_profiles: dict[str, dict[str, object]] = {}
    for block_name, indices in block_indices.items():
        mask = np.zeros(len(feature_names), dtype=bool)
        mask[np.asarray(indices, dtype=np.int64)] = True
        block_profiles[block_name] = _target_profile_metrics(
            y,
            predicted,
            mask,
            _optional_nll_array(block_nlls.get(block_name)),
            profile_name=block_name,
            included_blocks=[block_name],
            metric_definition="single feature-block target profile",
        )
    block_normalized = _block_normalized_profile(block_profiles)
    return {
        "schema": "scope_static_stage3c_target_score_profiles_v1",
        "description": "Evaluator-side target scoring views; learner fitting and assignments are unchanged.",
        "profiles": {
            TARGET_SCORE_PROFILE_FULL: full,
            TARGET_SCORE_PROFILE_RAW: raw,
            TARGET_SCORE_PROFILE_BLOCK_NORMALIZED: block_normalized,
        },
        "block_profiles": block_profiles,
    }


def _target_profile_metrics(
    y: np.ndarray,
    predicted: np.ndarray,
    mask: np.ndarray,
    nll: np.ndarray | None,
    *,
    profile_name: str,
    included_blocks: list[str],
    metric_definition: str,
) -> dict[str, object]:
    target_feature_count = int(np.sum(mask))
    if target_feature_count <= 0:
        return {
            "profile": str(profile_name),
            "metric_definition": str(metric_definition),
            "target_feature_count": 0,
            "included_blocks": list(included_blocks),
            "gaussian_density_nll": None,
            "gaussian_density_nll_per_feature": None,
            "raw_visible_feature_mae": None,
            "raw_visible_feature_mse": None,
            "target_abs_mean": None,
        }
    if y.shape[0] == 0:
        mae = 0.0
        mse = 0.0
        target_abs_mean = 0.0
    else:
        residual = y[:, mask] - predicted[:, mask]
        mae = float(np.mean(np.abs(residual)))
        mse = float(np.mean(residual * residual))
        target_abs_mean = float(np.mean(np.abs(y[:, mask])))
    gaussian_density_nll = float(np.mean(nll)) if nll is not None and nll.size else None
    gaussian_density_nll_per_feature = (
        None if gaussian_density_nll is None else float(gaussian_density_nll) / float(max(1, target_feature_count))
    )
    return {
        "profile": str(profile_name),
        "metric_definition": str(metric_definition),
        "target_feature_count": int(target_feature_count),
        "included_blocks": list(included_blocks),
        "gaussian_density_nll": gaussian_density_nll,
        "gaussian_density_nll_per_feature": gaussian_density_nll_per_feature,
        "raw_visible_feature_mae": mae,
        "raw_visible_feature_mse": mse,
        "target_abs_mean": target_abs_mean,
    }


def _block_normalized_profile(block_profiles: dict[str, dict[str, object]]) -> dict[str, object]:
    rows = [dict(block_profiles[name]) for name in sorted(block_profiles)]
    nll_values = [float(row["gaussian_density_nll_per_feature"]) for row in rows if row.get("gaussian_density_nll_per_feature") is not None]
    mae_values = [float(row["raw_visible_feature_mae"]) for row in rows if row.get("raw_visible_feature_mae") is not None]
    mse_values = [float(row["raw_visible_feature_mse"]) for row in rows if row.get("raw_visible_feature_mse") is not None]
    target_abs_values = [float(row["target_abs_mean"]) for row in rows if row.get("target_abs_mean") is not None]
    target_feature_count = int(sum(int(row.get("target_feature_count", 0) or 0) for row in rows))
    return {
        "profile": TARGET_SCORE_PROFILE_BLOCK_NORMALIZED,
        "metric_definition": "equal-weight average across feature blocks; Gaussian NLL uses each block's per-feature NLL before block averaging",
        "target_feature_count": target_feature_count,
        "included_blocks": [str(row.get("profile")) for row in rows],
        "block_count": int(len(rows)),
        "gaussian_density_nll": float(np.mean(nll_values)) if nll_values else None,
        "gaussian_density_nll_per_feature": float(np.mean(nll_values)) if nll_values else None,
        "raw_visible_feature_mae": float(np.mean(mae_values)) if mae_values else None,
        "raw_visible_feature_mse": float(np.mean(mse_values)) if mse_values else None,
        "target_abs_mean": float(np.mean(target_abs_values)) if target_abs_values else None,
        "block_metrics": block_profiles,
    }


def _optional_nll_array(value: object) -> np.ndarray | None:
    if value is None:
        return None
    arr = np.asarray(value, dtype=np.float64)
    if arr.size == 0:
        return None
    return arr


def _raw_feature_mask(feature_names: list[str]) -> np.ndarray:
    return np.asarray([str(name).startswith("raw__") for name in feature_names], dtype=bool)


def _feature_block_lift_report(
    *,
    predicted_assignment_metrics: dict[str, object],
    global_null_metrics: dict[str, object],
    stratified_null_metrics: dict[str, object],
    mean_only_baseline_metrics: dict[str, object],
    oracle_assignment_comparator_metrics: dict[str, object],
) -> dict[str, object]:
    predicted = dict(predicted_assignment_metrics.get("feature_block_metrics", {}))
    global_null = dict(global_null_metrics.get("feature_block_metrics", {}))
    stratified_null = dict(stratified_null_metrics.get("feature_block_metrics", {}))
    mean_only = dict(mean_only_baseline_metrics.get("feature_block_metrics", {}))
    oracle = dict(oracle_assignment_comparator_metrics.get("feature_block_metrics", {}))
    blocks = sorted(set(predicted) | set(global_null) | set(stratified_null) | set(mean_only) | set(oracle))
    return {
        "schema": "scope_static_stage3c_feature_block_lift_v1",
        "block_metric": "raw_visible_feature_mae",
        "higher_lift_is_better": True,
        "global_null_minus_predicted": _feature_block_lift(predicted, global_null),
        "stratified_null_minus_predicted": _feature_block_lift(predicted, stratified_null),
        "mean_only_minus_predicted": _feature_block_lift(predicted, mean_only),
        "oracle_minus_predicted_gap": _feature_block_gap(predicted, oracle),
        "block_count": int(len(blocks)),
        "blocks": blocks,
    }


def _feature_block_lift(predicted: dict[str, object], baseline: dict[str, object]) -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for block in sorted(set(predicted) | set(baseline)):
        pred = dict(predicted.get(block, {})) if isinstance(predicted.get(block, {}), dict) else {}
        base = dict(baseline.get(block, {})) if isinstance(baseline.get(block, {}), dict) else {}
        out[block] = {
            "feature_count": int(pred.get("feature_count", base.get("feature_count", 0)) or 0),
            "raw_visible_feature_mae_reduction": _optional_difference(
                base.get("raw_visible_feature_mae"),
                pred.get("raw_visible_feature_mae"),
            ),
            "raw_visible_feature_mse_reduction": _optional_difference(
                base.get("raw_visible_feature_mse"),
                pred.get("raw_visible_feature_mse"),
            ),
        }
    return out


def _feature_block_gap(predicted: dict[str, object], comparator: dict[str, object]) -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for block in sorted(set(predicted) | set(comparator)):
        pred = dict(predicted.get(block, {})) if isinstance(predicted.get(block, {}), dict) else {}
        comp = dict(comparator.get(block, {})) if isinstance(comparator.get(block, {}), dict) else {}
        out[block] = {
            "feature_count": int(pred.get("feature_count", comp.get("feature_count", 0)) or 0),
            "raw_visible_feature_mae_gap": _optional_difference(
                pred.get("raw_visible_feature_mae"),
                comp.get("raw_visible_feature_mae"),
            ),
            "raw_visible_feature_mse_gap": _optional_difference(
                pred.get("raw_visible_feature_mse"),
                comp.get("raw_visible_feature_mse"),
            ),
        }
    return out


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


def _categorical_population_nll(y: np.ndarray, predicted: np.ndarray, groups: list[dict[str, object]]) -> float | None:
    if y.shape[0] == 0 or not groups:
        return None
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


def _audit_seed_list(seeds: tuple[int, ...] | list[int] | None) -> list[int]:
    if seeds is None:
        return []
    out = []
    seen = set()
    for seed in seeds:
        value = int(seed)
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _aggregate_shuffle_runs(runs: list[dict[str, object]]) -> dict[str, object]:
    return _aggregate_overall_runs([dict(row.get("overall", {})) for row in runs])


def _aggregate_overall_runs(overalls: list[dict[str, object]]) -> dict[str, object]:
    keys = (
        "categorical_population_nll",
        "gaussian_density_nll",
        "gaussian_nll",
        "raw_visible_feature_mae",
        "population_cross_entropy",
        "population_mae",
        "expectation_mae",
    )
    aggregate: dict[str, object] = {"run_count": int(len(overalls))}
    for key in keys:
        values = [float(row.get(key)) for row in overalls if row.get(key) is not None]
        if not values:
            aggregate[f"{key}_mean"] = None
            aggregate[f"{key}_std"] = None
            aggregate[f"{key}_min"] = None
            aggregate[f"{key}_max"] = None
            continue
        arr = np.asarray(values, dtype=np.float64)
        aggregate[f"{key}_mean"] = float(np.mean(arr))
        aggregate[f"{key}_std"] = float(np.std(arr))
        aggregate[f"{key}_min"] = float(np.min(arr))
        aggregate[f"{key}_max"] = float(np.max(arr))
    return aggregate


def _aggregate_target_score_profile_runs(profile_artifacts: list[dict[str, object]]) -> dict[str, object]:
    profiles_by_name: dict[str, list[dict[str, object]]] = {}
    for artifact in profile_artifacts:
        profiles = dict(artifact.get("profiles", {})) if isinstance(artifact.get("profiles", {}), dict) else {}
        for name, row in profiles.items():
            if isinstance(row, dict):
                profiles_by_name.setdefault(str(name), []).append(dict(row))
    out: dict[str, object] = {
        "schema": "scope_static_stage3c_target_score_profile_aggregate_v1",
        "run_count": int(len(profile_artifacts)),
        "profiles": {},
    }
    profile_out: dict[str, object] = {}
    for profile_name in TARGET_SCORE_PROFILE_NAMES:
        rows = profiles_by_name.get(profile_name, [])
        profile_out[profile_name] = _aggregate_target_profile_rows(rows)
    for profile_name in sorted(set(profiles_by_name) - set(TARGET_SCORE_PROFILE_NAMES)):
        profile_out[profile_name] = _aggregate_target_profile_rows(profiles_by_name[profile_name])
    out["profiles"] = profile_out
    return out


def _aggregate_target_profile_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    first = rows[0] if rows else {}
    out: dict[str, object] = {
        "run_count": int(len(rows)),
        "target_feature_count": int(first.get("target_feature_count", 0) or 0),
        "included_blocks": list(first.get("included_blocks", []) or []),
        "metric_definition": first.get("metric_definition"),
    }
    for key in (
        "gaussian_density_nll",
        "gaussian_density_nll_per_feature",
        "raw_visible_feature_mae",
        "raw_visible_feature_mse",
        "target_abs_mean",
    ):
        values = [float(row.get(key)) for row in rows if row.get(key) is not None]
        if not values:
            out[f"{key}_mean"] = None
            out[f"{key}_std"] = None
            out[f"{key}_min"] = None
            out[f"{key}_max"] = None
            continue
        arr = np.asarray(values, dtype=np.float64)
        out[f"{key}_mean"] = float(np.mean(arr))
        out[f"{key}_std"] = float(np.std(arr))
        out[f"{key}_min"] = float(np.min(arr))
        out[f"{key}_max"] = float(np.max(arr))
    return out


def _scrambled_target_score_profile_lift(target_profile_aggregate: dict[str, object]) -> dict[str, object]:
    predicted = _aggregate_profiles_from_target_aggregate(target_profile_aggregate.get("predicted_assignment", {}))
    global_null = _aggregate_profiles_from_target_aggregate(target_profile_aggregate.get("global_null", {}))
    stratified_null = _aggregate_profiles_from_target_aggregate(target_profile_aggregate.get("stratified_null", {}))
    mean_only = _aggregate_profiles_from_target_aggregate(target_profile_aggregate.get("mean_only_baseline", {}))
    profiles: dict[str, object] = {}
    for name in TARGET_SCORE_PROFILE_NAMES:
        pred = dict(predicted.get(name, {}))
        glob = dict(global_null.get(name, {}))
        strat = dict(stratified_null.get(name, {}))
        mean = dict(mean_only.get(name, {}))
        profiles[name] = {
            "gaussian_density_nll_mean_lift": _optional_difference(
                glob.get("gaussian_density_nll_mean"),
                pred.get("gaussian_density_nll_mean"),
            ),
            "gaussian_density_nll_per_feature_mean_lift": _optional_difference(
                glob.get("gaussian_density_nll_per_feature_mean"),
                pred.get("gaussian_density_nll_per_feature_mean"),
            ),
            "raw_visible_feature_mae_mean_lift": _optional_difference(
                glob.get("raw_visible_feature_mae_mean"),
                pred.get("raw_visible_feature_mae_mean"),
            ),
            "mean_only_raw_visible_feature_mae_mean_lift": _optional_difference(
                mean.get("raw_visible_feature_mae_mean"),
                pred.get("raw_visible_feature_mae_mean"),
            ),
            "stratified_null_gaussian_density_nll_mean_lift": _optional_difference(
                strat.get("gaussian_density_nll_mean"),
                pred.get("gaussian_density_nll_mean"),
            ),
            "stratified_null_gaussian_density_nll_per_feature_mean_lift": _optional_difference(
                strat.get("gaussian_density_nll_per_feature_mean"),
                pred.get("gaussian_density_nll_per_feature_mean"),
            ),
            "stratified_null_raw_visible_feature_mae_mean_lift": _optional_difference(
                strat.get("raw_visible_feature_mae_mean"),
                pred.get("raw_visible_feature_mae_mean"),
            ),
        }
    return {
        "schema": "scope_static_stage3c_scrambled_target_score_profile_lift_v1",
        "profiles": profiles,
    }


def _aggregate_profiles_from_target_aggregate(value: object) -> dict[str, dict[str, object]]:
    aggregate = dict(value) if isinstance(value, dict) else {}
    profiles = aggregate.get("profiles", {})
    if not isinstance(profiles, dict):
        return {}
    return {str(name): dict(row) for name, row in profiles.items() if isinstance(row, dict)}


def _scramble_visible_feature_columns(x: np.ndarray, *, seed: int) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim != 2:
        raise ValueError("visible feature matrix must be 2D")
    scrambled = np.array(arr, copy=True)
    if scrambled.shape[0] <= 1:
        return scrambled
    rng = np.random.default_rng(int(seed))
    for col in range(int(scrambled.shape[1])):
        scrambled[:, col] = arr[rng.permutation(int(arr.shape[0])), col]
    return scrambled


def _is_one(value: object, *, atol: float = 1.0e-12) -> bool:
    if value is None:
        return False
    return bool(abs(float(value) - 1.0) <= float(atol))


def _stage5b1_property_recovery_passed(metrics: dict[str, object] | None) -> bool:
    if not isinstance(metrics, dict):
        return False
    acceptance = metrics.get("acceptance_audit", {})
    if isinstance(acceptance, dict) and "property_recovery_passed" in acceptance:
        return bool(acceptance.get("property_recovery_passed", False))
    return artifact_acceptance_passed(metrics)


def _stage5b1_claim_allowed_flag(metrics: dict[str, object] | None) -> bool | None:
    if not isinstance(metrics, dict):
        return None
    claim_boundary = metrics.get("claim_boundary", {})
    if isinstance(claim_boundary, dict) and "claim_allowed" in claim_boundary:
        return bool(claim_boundary.get("claim_allowed", False))
    acceptance = metrics.get("acceptance_audit", {})
    if isinstance(acceptance, dict) and "claim_passed" in acceptance:
        return bool(acceptance.get("claim_passed", False))
    return None


def _stage5b1_claim_gate_passed(metrics: dict[str, object] | None) -> bool:
    flag = _stage5b1_claim_allowed_flag(metrics)
    if flag is not None:
        return bool(flag)
    if not isinstance(metrics, dict):
        return False
    return bool(artifact_acceptance_passed(metrics) and str(metrics.get("decision", "")).endswith("_passed"))


def _optional_json(path: Path | None) -> dict[str, object] | None:
    if path is None or not Path(path).exists():
        return None
    return _load_json(Path(path))


def _primary_strength_reference_frame(audit: dict[str, object]) -> str:
    per_family = audit.get("per_family", {})
    if not isinstance(per_family, dict):
        return ""
    for payload in per_family.values():
        row = dict(payload) if isinstance(payload, dict) else {}
        strength = row.get("visible_strength", {})
        if isinstance(strength, dict):
            frame = str(strength.get("primary_reference_frame", ""))
            if frame:
                return frame
    return ""


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


def _target_profile_metric_less(left: dict[str, object], right: dict[str, object], profile: str, key: str) -> bool:
    left_profiles = _profiles_from_generation_metrics(left)
    right_profiles = _profiles_from_generation_metrics(right)
    left_profile = dict(left_profiles.get(profile, {}))
    right_profile = dict(right_profiles.get(profile, {}))
    if left_profile.get(key) is None or right_profile.get(key) is None:
        return False
    return bool(float(left_profile[key]) < float(right_profile[key]))


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


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "prototype_generation_metrics.json": result["prototype_generation_metrics"],
        "target_score_profile_report.json": result["prototype_generation_metrics"]["target_score_profile_report"],
        "predicted_assignment_metrics.json": result["predicted_assignment_metrics"],
        "oracle_assignment_comparator_metrics.json": result["oracle_assignment_comparator_metrics"],
        "soft_family_classification_metrics.json": result["soft_family_classification_metrics"],
        "soft_family_strength_location_audit.json": result["soft_family_strength_location_audit"],
        "s5_context_relative_mechanism_effect_audit.json": result["s5_context_relative_mechanism_effect_audit"],
        "mechanism_taxonomy_contract_audit.json": result["mechanism_taxonomy_contract_audit"],
        "mechanism_dimension_recovery_audit.json": result["mechanism_dimension_recovery_audit"],
        "overlay_contract_audit.json": result["overlay_contract_audit"],
        "overlay_recovery_audit.json": result["overlay_recovery_audit"],
        "global_null_metrics.json": result["global_null_metrics"],
        "stratified_null_metrics.json": result["stratified_null_metrics"],
        "mean_only_baseline_metrics.json": result["mean_only_baseline_metrics"],
        "assignment_shuffle_audit.json": result["assignment_shuffle_audit"],
        "feature_scramble_audit.json": result["feature_scramble_audit"],
        "leakage_audit.json": result["leakage_audit"],
        "claim_gate_audit.json": result["claim_gate_audit"],
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
    claim_gate = dict(result.get("claim_gate_audit", {}))
    predicted = dict(dict(result.get("predicted_assignment_metrics", {})).get("overall", {}))
    global_null = dict(dict(result.get("global_null_metrics", {})).get("overall", {}))
    stratified_null = dict(dict(result.get("stratified_null_metrics", {})).get("overall", {}))
    oracle = dict(dict(result.get("oracle_assignment_comparator_metrics", {})).get("overall", {}))
    family = dict(result.get("soft_family_classification_metrics", {}))
    s5 = dict(result.get("s5_context_relative_mechanism_effect_audit", result.get("soft_family_strength_location_audit", {})))
    primary_metric = str(dict(result.get("prototype_generation_metrics", {})).get("primary_generation_likelihood_metric", PRIMARY_GENERATION_LIKELIHOOD_METRIC))
    shuffle = dict(dict(result.get("assignment_shuffle_audit", {})).get("aggregate", {}))
    scramble = dict(dict(dict(result.get("feature_scramble_audit", {})).get("aggregate", {})).get("predicted_assignment", {}))
    return "\n".join(
        [
            "# Stage 3C: Prototype And Generator Learning",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Claim allowed: `{str(bool(claim_gate.get('claim_allowed', False))).lower()}`",
            f"- Wall-clock seconds: `{_format_metric(result.get('wall_clock_seconds'))}`",
            f"- Primary generation likelihood metric: `{primary_metric}`",
            f"- Predicted-assignment primary NLL: `{_format_metric(predicted.get(primary_metric))}`",
            f"- Global-null primary NLL: `{_format_metric(global_null.get(primary_metric))}`",
            f"- Stratified-null primary NLL: `{_format_metric(stratified_null.get(primary_metric))}`",
            f"- Assignment-shuffle mean primary NLL: `{_format_metric(shuffle.get(f'{primary_metric}_mean'))}`",
            f"- Feature-scramble mean primary NLL: `{_format_metric(scramble.get(f'{primary_metric}_mean'))}`",
            f"- Predicted-assignment categorical population NLL: `{_format_metric(predicted.get('categorical_population_nll'))}`",
            f"- Assignment-shuffle mean categorical population NLL: `{_format_metric(shuffle.get('categorical_population_nll_mean'))}`",
            f"- Feature-scramble mean categorical population NLL: `{_format_metric(scramble.get('categorical_population_nll_mean'))}`",
            f"- Oracle-comparator categorical population NLL: `{_format_metric(oracle.get('categorical_population_nll'))}`",
            f"- Predicted-minus-oracle categorical NLL gap: `{_format_metric(_optional_difference(predicted.get('categorical_population_nll'), oracle.get('categorical_population_nll')))}`",
            f"- Predicted-assignment Gaussian density NLL: `{_format_metric(predicted.get('gaussian_density_nll'))}`",
            f"- Global-null Gaussian density NLL: `{_format_metric(global_null.get('gaussian_density_nll'))}`",
            f"- Predicted-assignment raw MAE: `{_format_metric(predicted.get('raw_visible_feature_mae'))}`",
            f"- Oracle-comparator raw MAE: `{_format_metric(oracle.get('raw_visible_feature_mae'))}`",
            f"- Soft-family NMI / ARI: `{_format_metric(family.get('normalized_mutual_info'))}` / `{_format_metric(family.get('adjusted_rand_index'))}`",
            f"- S5 effect reference frame: `{str(s5.get('location_reference_frame', 'none'))}`",
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
