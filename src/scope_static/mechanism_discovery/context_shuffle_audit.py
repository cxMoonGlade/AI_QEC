from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.protocols import LEARNER_VALIDATION_STAGE
from .artifacts import feature_schema_matches_stage3a as _feature_schema_matches_s3a
from .artifacts import load_json_object as _load_json
from .artifacts import load_stage3a_frozen_visible_features
from .baselines import VARIANCE_FLOOR
from .discovery_model import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3B1_DIR
from .discovery_model import _cap_folds
from .generator_learning import DEFAULT_MAX_CV_FOLDS
from .generator_learning import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3C_DIR
from .generator_learning import PRIMARY_GENERATION_LIKELIHOOD_METRIC
from .generator_learning import SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC
from .generator_learning import assignment_source_audit
from .generator_learning import evaluate_global_null_generation
from .generator_learning import evaluate_mean_only_generation
from .generator_learning import evaluate_predicted_assignment_generation
from .generator_learning import heldout_protocol_artifact
from .generator_learning import _load_stage3b1_assignments
from .observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from .protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR


STAGE_NAME = "Stage3D3_context_shuffle_audit"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/PHYC_STAGE3_discovery/S3D3_context_shuffle_audit"
DEFAULT_SEED = 0
DEFAULT_SHUFFLE_COUNT = 16
DEFAULT_MAX_ORIGINAL_ADVANTAGE_OVER_CONTEXT_SHUFFLE = 0.05
METRIC_KEYS = (
    "categorical_population_nll",
    "gaussian_density_nll",
    "gaussian_nll",
    "raw_visible_feature_mae",
    "population_cross_entropy",
    "population_mae",
    "expectation_mae",
)


def run_stage3d3_context_shuffle_audit(
    *,
    stage3a_dir: str | Path = DEFAULT_STAGE3A_DIR,
    stage3a5_dir: str | Path = DEFAULT_STAGE3A5_DIR,
    stage3b1_dir: str | Path = DEFAULT_STAGE3B1_DIR,
    stage3c_dir: str | Path | None = DEFAULT_STAGE3C_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    seed: int = DEFAULT_SEED,
    shuffle_count: int = DEFAULT_SHUFFLE_COUNT,
    max_cv_folds: int | None = DEFAULT_MAX_CV_FOLDS,
    variance_floor: float = VARIANCE_FLOOR,
    max_original_advantage_over_context_shuffle: float = DEFAULT_MAX_ORIGINAL_ADVANTAGE_OVER_CONTEXT_SHUFFLE,
) -> dict[str, object]:
    """Shuffle protocol-only context groups and rerun the S3C generator.

    S3D.3 keeps frozen visible features and discovered assignments fixed, but
    row-shuffles Stage 3A context-group labels before rebuilding grouped folds.
    This tests the split/context protocol. Under the current context-free B1
    selected model, context shuffle is expected to be neutral or easier; a large
    original advantage would suggest an overly easy context split.
    """

    s3a = Path(stage3a_dir)
    s3a5 = Path(stage3a5_dir)
    s3b1 = Path(stage3b1_dir)
    s3c = None if stage3c_dir is None else Path(stage3c_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    s3a_metrics = _load_json(s3a / "metrics.json")
    s3a5_metrics = _load_json(s3a5 / "metrics.json")
    s3b1_metrics = _load_json(s3b1 / "metrics.json")
    s3c_metrics = _optional_json(None if s3c is None else s3c / "metrics.json")

    x, feature_names, feature_matrix = load_stage3a_frozen_visible_features(s3a)
    responsibilities = _load_stage3b1_assignments(s3b1, record_count=int(x.shape[0]))
    feature_match = _feature_schema_matches_s3a(s3a, feature_names)
    split_manifest = dict(s3a_metrics.get("split_manifest", {})) if isinstance(s3a_metrics.get("split_manifest", {}), dict) else {}
    batch_schema = dict(s3a_metrics.get("batch_context_schema", {})) if isinstance(s3a_metrics.get("batch_context_schema", {}), dict) else {}
    context_groups = context_groups_from_split_manifest(split_manifest, record_count=int(x.shape[0]))
    all_folds = context_folds_from_split_manifest(split_manifest, record_count=int(x.shape[0]))
    folds = _cap_folds(all_folds, max_cv_folds=max_cv_folds)
    if not folds:
        folds = [{"train_indices": list(range(int(x.shape[0]))), "validation_indices": [], "test_indices": list(range(int(x.shape[0])))}]

    original = evaluate_predicted_assignment_generation(
        x,
        responsibilities,
        feature_names=feature_names,
        folds=folds,
        variance_floor=float(variance_floor),
    )
    original_global_null = evaluate_global_null_generation(
        x,
        feature_names=feature_names,
        folds=folds,
        variance_floor=float(variance_floor),
    )
    original_mean_only = evaluate_mean_only_generation(
        x,
        feature_names=feature_names,
        folds=folds,
    )
    shuffle_runs = context_shuffle_runs(
        x,
        responsibilities,
        context_groups,
        base_folds=folds,
        feature_names=feature_names,
        seed=int(seed),
        shuffle_count=int(shuffle_count),
        variance_floor=float(variance_floor),
    )
    shuffled_summary = aggregate_context_shuffle_runs(shuffle_runs)
    shuffle_metrics = context_shuffle_metrics(
        original_assignment_metrics=original,
        original_global_null_metrics=original_global_null,
        original_mean_only_baseline_metrics=original_mean_only,
        context_shuffled_metrics_summary=shuffled_summary,
    )
    context_protocol = context_protocol_audit(
        split_manifest=split_manifest,
        batch_context_schema=batch_schema,
        context_groups=context_groups,
    )
    selected_context = selected_context_usage_audit(s3b1_metrics=s3b1_metrics)
    leakage = stage3d3_leakage_audit(s3b1_metrics=s3b1_metrics)
    s3c_consistency = s3c_consistency_audit(s3c_metrics=s3c_metrics, recomputed_original=original)
    acceptance = stage3d3_acceptance_audit(
        s3a_metrics=s3a_metrics,
        s3a5_metrics=s3a5_metrics,
        s3b1_metrics=s3b1_metrics,
        feature_match=feature_match,
        feature_matrix=feature_matrix,
        responsibilities=responsibilities,
        context_protocol_audit=context_protocol,
        selected_context_usage_audit=selected_context,
        shuffle_runs=shuffle_runs,
        context_shuffle_metrics=shuffle_metrics,
        leakage_audit=leakage,
        s3c_consistency_audit=s3c_consistency,
        max_original_advantage_over_context_shuffle=float(max_original_advantage_over_context_shuffle),
    )
    result = {
        "schema": "scope_static_stage3d3_context_shuffle_audit_v1",
        "stage": STAGE_NAME,
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="context_shuffle_audit"),
        "stage3a_dir": str(s3a),
        "stage3a5_dir": str(s3a5),
        "stage3b1_dir": str(s3b1),
        "stage3c_dir": None if s3c is None else str(s3c),
        "output_dir": str(output),
        "claim_boundary": {
            "keeps_visible_features_fixed": True,
            "keeps_discovered_assignments_fixed": True,
            "scrambles_protocol_only_context_groups": True,
            "context_group_is_not_a_learner_visible_feature": True,
            "refits_stage3c_generator_under_context_shuffled_folds": True,
            "uses_mechanism_labels_for_generator_fit": False,
            "uses_oracle_assignment_comparator": False,
            "uses_channels_ptms_kraus": False,
            "tests_context_split_protocol_not_label_supervision": True,
        },
        "config": {
            "stage3a_dir": str(s3a),
            "stage3a5_dir": str(s3a5),
            "stage3b1_dir": str(s3b1),
            "stage3c_dir": None if s3c is None else str(s3c),
            "output_dir": str(output),
            "seed": int(seed),
            "shuffle_count": int(shuffle_count),
            "max_cv_folds": None if max_cv_folds is None else int(max_cv_folds),
            "variance_floor": float(variance_floor),
            "max_original_advantage_over_context_shuffle": float(max_original_advantage_over_context_shuffle),
        },
        "visible_feature_matrix": feature_matrix,
        "feature_schema_match_audit": feature_match,
        "heldout_protocol": heldout_protocol_artifact(all_folds=all_folds, evaluated_folds=folds, max_cv_folds=max_cv_folds),
        "assignment_source_audit": assignment_source_audit(s3b1_dir=s3b1, responsibilities=responsibilities),
        "context_protocol_audit": context_protocol,
        "selected_context_usage_audit": selected_context,
        "context_shuffle_metrics": shuffle_metrics,
        "original_assignment_metrics": original,
        "original_global_null_metrics": original_global_null,
        "original_mean_only_baseline_metrics": original_mean_only,
        "context_shuffled_metrics_summary": shuffled_summary,
        "context_shuffle_runs": shuffle_runs,
        "s3c_consistency_audit": s3c_consistency,
        "leakage_audit": leakage,
        "acceptance_audit": acceptance,
        "decision": "stage3d3_context_shuffle_audit_passed" if acceptance["passed"] else "stage3d3_context_shuffle_audit_failed",
    }
    _write_outputs(output, result)
    return result


def context_shuffle_runs(
    x: np.ndarray,
    responsibilities: np.ndarray,
    context_groups: np.ndarray,
    *,
    base_folds: list[dict[str, list[int]]],
    feature_names: list[str],
    seed: int,
    shuffle_count: int,
    variance_floor: float,
) -> list[dict[str, object]]:
    rng = np.random.default_rng(int(seed))
    runs = []
    base_digest = _array_digest(context_groups)
    base_counts = _group_counts(context_groups)
    for idx in range(max(0, int(shuffle_count))):
        permutation = _non_identity_permutation(rng, int(context_groups.size))
        shuffled_groups = np.asarray(context_groups, dtype=np.int64)[permutation]
        folds = rebuild_folds_with_context_groups(base_folds, shuffled_groups)
        fold_indices_changed = _fold_indices_digest(folds) != _fold_indices_digest(base_folds)
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
        runs.append(
            {
                "schema": "scope_static_stage3d3_context_shuffle_run_v1",
                "shuffle_index": int(idx),
                "shuffle_mode": "rowwise_protocol_context_group_permutation",
                "permutation_sha256": _permutation_digest(permutation),
                "row_count": int(permutation.size),
                "unchanged_row_fraction": float(np.mean(permutation == np.arange(permutation.size))) if permutation.size else 0.0,
                "context_alignment_changed": bool(permutation.size <= 1 or not np.array_equal(shuffled_groups, context_groups)),
                "context_group_multiset_preserved": bool(base_counts == _group_counts(shuffled_groups)),
                "fold_indices_changed": bool(fold_indices_changed),
                "visible_features_fixed": True,
                "assignments_fixed": True,
                "assignment_matrix_row_stochastic": bool(responsibilities.size == 0 or np.allclose(np.sum(responsibilities, axis=1), 1.0)),
                "original_context_groups_sha256": base_digest,
                "shuffled_context_groups_sha256": _array_digest(shuffled_groups),
                "fold_summary": _fold_summary(folds),
                "predicted_assignment_metrics": predicted,
                "global_null_metrics": global_null,
                "mean_only_baseline_metrics": mean_only,
                "predicted_overall": dict(predicted.get("overall", {})),
                "global_null_overall": dict(global_null.get("overall", {})),
                "mean_only_overall": dict(mean_only.get("overall", {})),
            }
        )
    return runs


def rebuild_folds_with_context_groups(
    base_folds: list[dict[str, list[int]]],
    context_groups: np.ndarray,
) -> list[dict[str, list[int]]]:
    groups = np.asarray(context_groups, dtype=np.int64)
    folds = []
    for fold_idx, fold in enumerate(base_folds):
        train_groups = [int(group) for group in fold.get("train_groups", [])]
        validation_groups = [int(group) for group in fold.get("validation_groups", [])]
        test_groups = [int(group) for group in fold.get("test_groups", [])]
        if not train_groups and not validation_groups and not test_groups:
            train_idx = _indices(fold.get("train_indices", []), record_count=int(groups.size))
            val_idx = _indices(fold.get("validation_indices", []), record_count=int(groups.size))
            test_idx = _indices(fold.get("test_indices", []), record_count=int(groups.size))
        else:
            train_idx = _indices_for_groups(groups, train_groups)
            val_idx = _indices_for_groups(groups, validation_groups)
            test_idx = _indices_for_groups(groups, test_groups)
        folds.append(
            {
                "fold": int(fold.get("fold", fold_idx)),
                "train_groups": train_groups,
                "validation_groups": validation_groups,
                "test_groups": test_groups,
                "train_indices": train_idx.tolist(),
                "validation_indices": val_idx.tolist(),
                "test_indices": test_idx.tolist(),
            }
        )
    return folds


def aggregate_context_shuffle_runs(shuffle_runs: list[dict[str, object]]) -> dict[str, object]:
    predicted = _metric_summary_from_runs(shuffle_runs, run_key="predicted_overall")
    global_null = _metric_summary_from_runs(shuffle_runs, run_key="global_null_overall")
    mean_only = _metric_summary_from_runs(shuffle_runs, run_key="mean_only_overall")
    return {
        "schema": "scope_static_stage3d3_context_shuffled_metrics_summary_v1",
        "shuffle_count": int(len(shuffle_runs)),
        "shuffle_mode": "rowwise_protocol_context_group_permutation",
        "primary_generation_likelihood_metric": PRIMARY_GENERATION_LIKELIHOOD_METRIC,
        "secondary_continuous_density_diagnostic": SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC,
        "predicted_assignment_metrics": predicted,
        "global_null_metrics": global_null,
        "mean_only_baseline_metrics": mean_only,
        "all_visible_features_fixed": bool(shuffle_runs and all(bool(run.get("visible_features_fixed", False)) for run in shuffle_runs)),
        "all_assignments_fixed": bool(shuffle_runs and all(bool(run.get("assignments_fixed", False)) for run in shuffle_runs)),
        "all_context_group_multisets_preserved": bool(
            shuffle_runs and all(bool(run.get("context_group_multiset_preserved", False)) for run in shuffle_runs)
        ),
        "all_context_alignments_changed": bool(
            shuffle_runs and all(bool(run.get("context_alignment_changed", False)) for run in shuffle_runs)
        ),
        "all_fold_indices_changed": bool(shuffle_runs and all(bool(run.get("fold_indices_changed", False)) for run in shuffle_runs)),
        "max_unchanged_row_fraction": float(max((float(run.get("unchanged_row_fraction", 0.0)) for run in shuffle_runs), default=0.0)),
    }


def context_shuffle_metrics(
    *,
    original_assignment_metrics: dict[str, object],
    original_global_null_metrics: dict[str, object],
    original_mean_only_baseline_metrics: dict[str, object],
    context_shuffled_metrics_summary: dict[str, object],
) -> dict[str, object]:
    original = dict(original_assignment_metrics.get("overall", {}))
    original_null = dict(original_global_null_metrics.get("overall", {}))
    original_mean = dict(original_mean_only_baseline_metrics.get("overall", {}))
    predicted_summary = dict(context_shuffled_metrics_summary.get("predicted_assignment_metrics", {}))
    null_summary = dict(context_shuffled_metrics_summary.get("global_null_metrics", {}))
    mean_summary = dict(context_shuffled_metrics_summary.get("mean_only_baseline_metrics", {}))
    primary = PRIMARY_GENERATION_LIKELIHOOD_METRIC
    return {
        "schema": "scope_static_stage3d3_context_shuffle_metrics_v1",
        "control": "keep visible features and discovered assignments fixed, row-shuffle protocol-only context groups, rebuild grouped folds, refit/evaluate Stage 3C generator",
        "expected_result": "context-free selected models should remain meaningful and the original grouped-context split should not be artificially easier than context-shuffled folds",
        "primary_generation_likelihood_metric": primary,
        "secondary_continuous_density_diagnostic": SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC,
        "primary_context_report": _context_report(
            original_value=original.get(primary),
            original_global_null_value=original_null.get(primary),
            original_mean_only_value=original_mean.get(primary),
            shuffled_value=dict(predicted_summary.get(primary, {})).get("mean"),
            shuffled_global_null_value=dict(null_summary.get(primary, {})).get("mean"),
            shuffled_mean_only_value=dict(mean_summary.get(primary, {})).get("mean"),
        ),
        "original_assignment_model": original,
        "original_global_null_model": original_null,
        "context_shuffled_assignment_model_mean": {key: dict(predicted_summary.get(key, {})).get("mean") for key in METRIC_KEYS},
        "context_shuffled_global_null_model_mean": {key: dict(null_summary.get(key, {})).get("mean") for key in METRIC_KEYS},
        "context_shuffled_mean_only_baseline_mean": {key: dict(mean_summary.get(key, {})).get("mean") for key in METRIC_KEYS},
    }


def context_protocol_audit(
    *,
    split_manifest: dict[str, object],
    batch_context_schema: dict[str, object],
    context_groups: np.ndarray,
) -> dict[str, object]:
    primary = dict(batch_context_schema.get("primary_protocol", {})) if isinstance(batch_context_schema.get("primary_protocol", {}), dict) else {}
    unique_groups = sorted(set(np.asarray(context_groups, dtype=np.int64).tolist()))
    checks = {
        "split_policy_fixed_before_training": bool(split_manifest.get("split_policy_fixed_before_training", False)),
        "context_group_key_declared": bool(primary.get("context_group_key") or split_manifest.get("group_key")),
        "multi_context_batch_protocol_explicit": str(primary.get("mode", "")) == "multi_context_batch",
        "context_group_count_at_least_two": len(unique_groups) >= 2,
        "context_group_is_protocol_only": "context_group" in [str(item) for item in batch_context_schema.get("protocol_only_fields", [])],
        "context_group_not_learner_visible": "context_group" not in [str(item) for item in batch_context_schema.get("learner_visible_fields", [])],
    }
    return {
        "schema": "scope_static_stage3d3_context_protocol_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
        "context_group_count": int(len(unique_groups)),
        "context_group_counts": _group_counts(context_groups),
        "group_key": str(primary.get("context_group_key", split_manifest.get("group_key", ""))),
        "split_policy": str(split_manifest.get("split_policy", "")),
    }


def selected_context_usage_audit(*, s3b1_metrics: dict[str, object]) -> dict[str, object]:
    selection = dict(s3b1_metrics.get("candidate_selection", {})) if isinstance(s3b1_metrics.get("candidate_selection", {}), dict) else {}
    selected = dict(selection.get("selected", {})) if isinstance(selection.get("selected", {}), dict) else {}
    hardening = dict(s3b1_metrics.get("assignment_hardening_audit", {})) if isinstance(s3b1_metrics.get("assignment_hardening_audit", {}), dict) else {}
    model_selection = dict(s3b1_metrics.get("model_selection_audit", {})) if isinstance(s3b1_metrics.get("model_selection_audit", {}), dict) else {}
    uses_context = bool(selected.get("uses_context_groups_for_fit", False) or hardening.get("context_groups_used", False))
    return {
        "schema": "scope_static_stage3d3_selected_context_usage_audit_v1",
        "selected_model_family": selected.get("model_family"),
        "selected_k_mode": selected.get("k_mode"),
        "selected_k": selected.get("k"),
        "selected_model_uses_context_groups": uses_context,
        "context_groups_used_for_fit": bool(selected.get("uses_context_groups_for_fit", False)),
        "context_group_labels_used": bool(selected.get("uses_context_labels_for_fit", False)),
        "context_balance_penalty_used_for_selection": bool(model_selection.get("context_balance_penalty_used_for_selection", False)),
        "context_balance_uses_labels": bool(model_selection.get("context_balance_uses_labels", True)),
        "interpretation": (
            "selected_model_context_sensitive"
            if uses_context
            else "selected_model_context_free; context shuffle audits the grouped split protocol rather than learner context leakage"
        ),
    }


def stage3d3_leakage_audit(*, s3b1_metrics: dict[str, object]) -> dict[str, object]:
    boundary = dict(s3b1_metrics.get("claim_boundary", {})) if isinstance(s3b1_metrics.get("claim_boundary", {}), dict) else {}
    checks = {
        "uses_stage3a_frozen_visible_features": True,
        "uses_stage3b1_learned_assignments": True,
        "context_shuffle_uses_protocol_context_groups": True,
        "context_shuffle_uses_labels": False,
        "context_shuffle_uses_channels_ptms_kraus": False,
        "context_shuffle_uses_teacher_self_features": False,
        "context_shuffle_uses_oracle_prototypes": False,
        "stage3b1_assignments_trained_from_frozen_visible_features": bool(boundary.get("trains_from_stage3a_frozen_visible_features", False)),
        "stage3b1_labels_not_used_for_fit": not bool(boundary.get("uses_mechanism_labels_for_fit", True)),
        "stage3b1_labels_not_used_for_model_selection": not bool(boundary.get("uses_mechanism_labels_for_model_selection", True)),
    }
    return {
        "schema": "scope_static_stage3d3_leakage_audit_v1",
        "passed": bool(
            checks["uses_stage3a_frozen_visible_features"]
            and checks["uses_stage3b1_learned_assignments"]
            and checks["context_shuffle_uses_protocol_context_groups"]
            and not checks["context_shuffle_uses_labels"]
            and not checks["context_shuffle_uses_channels_ptms_kraus"]
            and not checks["context_shuffle_uses_teacher_self_features"]
            and not checks["context_shuffle_uses_oracle_prototypes"]
            and checks["stage3b1_assignments_trained_from_frozen_visible_features"]
            and checks["stage3b1_labels_not_used_for_fit"]
            and checks["stage3b1_labels_not_used_for_model_selection"]
        ),
        "checks": checks,
    }


def s3c_consistency_audit(*, s3c_metrics: dict[str, object] | None, recomputed_original: dict[str, object]) -> dict[str, object]:
    if not s3c_metrics:
        return {
            "schema": "scope_static_stage3d3_s3c_consistency_audit_v1",
            "s3c_metrics_present": False,
            "passed": True,
            "reason": "No Stage 3C metrics artifact was provided; original assignment metrics were recomputed from frozen Stage 3A and Stage 3B.1 artifacts.",
        }
    s3c_predicted = dict(dict(s3c_metrics.get("predicted_assignment_metrics", {})).get("overall", {}))
    recomputed = dict(recomputed_original.get("overall", {}))
    deltas = {}
    for key in METRIC_KEYS:
        if s3c_predicted.get(key) is not None and recomputed.get(key) is not None:
            deltas[f"{key}_abs_delta"] = abs(float(s3c_predicted[key]) - float(recomputed[key]))
    max_delta = max(deltas.values(), default=0.0)
    return {
        "schema": "scope_static_stage3d3_s3c_consistency_audit_v1",
        "s3c_metrics_present": True,
        "passed": bool(max_delta <= 1.0e-9),
        "max_abs_delta": float(max_delta),
        "metric_abs_deltas": deltas,
    }


def stage3d3_acceptance_audit(
    *,
    s3a_metrics: dict[str, object],
    s3a5_metrics: dict[str, object],
    s3b1_metrics: dict[str, object],
    feature_match: dict[str, object],
    feature_matrix: dict[str, object],
    responsibilities: np.ndarray,
    context_protocol_audit: dict[str, object],
    selected_context_usage_audit: dict[str, object],
    shuffle_runs: list[dict[str, object]],
    context_shuffle_metrics: dict[str, object],
    leakage_audit: dict[str, object],
    s3c_consistency_audit: dict[str, object],
    max_original_advantage_over_context_shuffle: float,
) -> dict[str, object]:
    report = dict(context_shuffle_metrics.get("primary_context_report", {}))
    original_lift = report.get("original_global_null_minus_original_lift")
    shuffled_lift = report.get("context_shuffled_global_null_minus_context_shuffled_lift")
    original_advantage = report.get("original_advantage_over_context_shuffle")
    selected_uses_context = bool(selected_context_usage_audit.get("selected_model_uses_context_groups", False))
    context_interpretation_ok = _context_interpretation_ok(
        selected_uses_context=selected_uses_context,
        original_advantage=original_advantage,
        shuffled_lift=shuffled_lift,
        max_original_advantage=float(max_original_advantage_over_context_shuffle),
    )
    checks = {
        "stage3a_acceptance_passed": bool(dict(s3a_metrics.get("acceptance_audit", {})).get("passed", False)),
        "stage3a5_acceptance_passed": bool(dict(s3a5_metrics.get("acceptance_audit", {})).get("passed", False)),
        "stage3b1_acceptance_passed": bool(dict(s3b1_metrics.get("acceptance_audit", {})).get("passed", False)),
        "approved_feature_schema_matches_stage3a": bool(feature_match.get("passed", False)),
        "uses_stage3a_frozen_visible_features": bool(feature_matrix.get("loaded_from_stage3a_artifact", False)),
        "assignment_matrix_row_stochastic": bool(responsibilities.size == 0 or np.allclose(np.sum(responsibilities, axis=1), 1.0)),
        "context_protocol_audit_passed": bool(context_protocol_audit.get("passed", False)),
        "selected_context_usage_declared": "selected_model_uses_context_groups" in selected_context_usage_audit,
        "shuffle_count_positive": bool(len(shuffle_runs) > 0),
        "visible_features_fixed_for_all_shuffles": bool(
            shuffle_runs and all(bool(run.get("visible_features_fixed", False)) for run in shuffle_runs)
        ),
        "assignments_fixed_for_all_shuffles": bool(shuffle_runs and all(bool(run.get("assignments_fixed", False)) for run in shuffle_runs)),
        "context_group_multiset_preserved_for_all_shuffles": bool(
            shuffle_runs and all(bool(run.get("context_group_multiset_preserved", False)) for run in shuffle_runs)
        ),
        "context_alignment_changed_for_all_shuffles": bool(
            shuffle_runs and all(bool(run.get("context_alignment_changed", False)) for run in shuffle_runs)
        ),
        "fold_indices_changed_for_all_shuffles": bool(
            shuffle_runs and all(bool(run.get("fold_indices_changed", False)) for run in shuffle_runs)
        ),
        "original_assignment_beats_original_global_null_primary_nll": bool(original_lift is not None and float(original_lift) > 0.0),
        "context_interpretation_accepted": context_interpretation_ok,
        "s3c_consistency_passed": bool(s3c_consistency_audit.get("passed", False)),
        "leakage_audit_passed": bool(leakage_audit.get("passed", False)),
    }
    return {
        "schema": "scope_static_stage3d3_acceptance_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
        "thresholds": {
            "max_original_advantage_over_context_shuffle": float(max_original_advantage_over_context_shuffle),
        },
        "selected_model_uses_context_groups": selected_uses_context,
        "primary_context_report": report,
    }


def _context_report(
    *,
    original_value: object,
    original_global_null_value: object,
    original_mean_only_value: object,
    shuffled_value: object,
    shuffled_global_null_value: object,
    shuffled_mean_only_value: object,
) -> dict[str, object]:
    original = _optional_float(original_value)
    original_null = _optional_float(original_global_null_value)
    original_mean = _optional_float(original_mean_only_value)
    shuffled = _optional_float(shuffled_value)
    shuffled_null = _optional_float(shuffled_global_null_value)
    shuffled_mean = _optional_float(shuffled_mean_only_value)
    original_lift = None if original is None or original_null is None else original_null - original
    shuffled_lift = None if shuffled is None or shuffled_null is None else shuffled_null - shuffled
    delta = None if original is None or shuffled is None else shuffled - original
    original_advantage = None if delta is None else max(0.0, float(delta))
    return {
        "metric": PRIMARY_GENERATION_LIKELIHOOD_METRIC,
        "lower_is_better": True,
        "original_assignment": original,
        "original_global_null": original_null,
        "original_mean_only_baseline": original_mean,
        "context_shuffled_assignment_mean": shuffled,
        "context_shuffled_global_null_mean": shuffled_null,
        "context_shuffled_mean_only_baseline_mean": shuffled_mean,
        "original_global_null_minus_original_lift": original_lift,
        "context_shuffled_global_null_minus_context_shuffled_lift": shuffled_lift,
        "context_shuffled_minus_original_delta": delta,
        "original_advantage_over_context_shuffle": original_advantage,
        "context_shuffle_makes_grouped_split_easier": bool(delta is not None and float(delta) < 0.0),
    }


def _context_interpretation_ok(
    *,
    selected_uses_context: bool,
    original_advantage: object,
    shuffled_lift: object,
    max_original_advantage: float,
) -> bool:
    advantage = _optional_float(original_advantage)
    lift = _optional_float(shuffled_lift)
    if selected_uses_context:
        return advantage is not None and lift is not None
    return bool(
        advantage is not None
        and advantage <= float(max_original_advantage)
        and lift is not None
        and float(lift) > 0.0
    )


def context_groups_from_split_manifest(split_manifest: dict[str, object], *, record_count: int) -> np.ndarray:
    groups = np.zeros(int(record_count), dtype=np.int64)
    seen = np.zeros(int(record_count), dtype=bool)
    for row in split_manifest.get("assignment_instances", []):
        if not isinstance(row, dict):
            continue
        idx = int(row.get("record_index", -1))
        if 0 <= idx < int(record_count):
            groups[idx] = int(row.get("context_group", 0))
            seen[idx] = True
    if not bool(np.all(seen)):
        groups = np.arange(int(record_count), dtype=np.int64)
    return groups


def context_folds_from_split_manifest(split_manifest: dict[str, object], *, record_count: int) -> list[dict[str, list[int]]]:
    folds = []
    for row in split_manifest.get("folds", []):
        if not isinstance(row, dict):
            continue
        train = _indices(row.get("train_indices", []), record_count=record_count).tolist()
        validation = _indices(row.get("validation_indices", []), record_count=record_count).tolist()
        test = _indices(row.get("test_indices", []), record_count=record_count).tolist()
        if train and validation:
            folds.append(
                {
                    "fold": int(row.get("fold", len(folds))),
                    "train_groups": [int(group) for group in row.get("train_groups", [])],
                    "validation_groups": [int(group) for group in row.get("validation_groups", [])],
                    "test_groups": [int(group) for group in row.get("test_groups", [])],
                    "train_indices": train,
                    "validation_indices": validation,
                    "test_indices": test,
                }
            )
    return folds


def _metric_summary_from_runs(shuffle_runs: list[dict[str, object]], *, run_key: str) -> dict[str, object]:
    metric_summary = {}
    for key in METRIC_KEYS:
        values = []
        for run in shuffle_runs:
            overall = dict(run.get(run_key, {})) if isinstance(run.get(run_key, {}), dict) else {}
            if overall.get(key) is not None:
                values.append(float(overall[key]))
        metric_summary[key] = _summarize_values(values)
    return metric_summary


def _indices_for_groups(groups: np.ndarray, selected_groups: list[int]) -> np.ndarray:
    selected = set(int(group) for group in selected_groups)
    return np.asarray([int(idx) for idx, group in enumerate(groups.tolist()) if int(group) in selected], dtype=np.int64)


def _indices(values: list[int], *, record_count: int) -> np.ndarray:
    clean = [int(value) for value in values if 0 <= int(value) < int(record_count)]
    return np.asarray(clean, dtype=np.int64)


def _non_identity_permutation(rng: np.random.Generator, n: int) -> np.ndarray:
    identity = np.arange(max(0, int(n)), dtype=np.int64)
    if int(n) <= 1:
        return identity
    for _ in range(32):
        perm = rng.permutation(int(n)).astype(np.int64)
        if not np.array_equal(perm, identity):
            return perm
    return np.roll(identity, 1)


def _summarize_values(values: list[float]) -> dict[str, object]:
    if not values:
        return {"count": 0, "mean": None, "std": None, "min": None, "max": None}
    arr = np.asarray(values, dtype=np.float64)
    return {
        "count": int(arr.size),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def _group_counts(groups: np.ndarray) -> dict[str, int]:
    arr = np.asarray(groups, dtype=np.int64)
    return {str(int(group)): int(np.sum(arr == int(group))) for group in sorted(set(arr.tolist()))}


def _fold_summary(folds: list[dict[str, list[int]]]) -> dict[str, object]:
    return {
        "fold_count": int(len(folds)),
        "train_counts": [int(len(fold.get("train_indices", []))) for fold in folds],
        "validation_counts": [int(len(fold.get("validation_indices", []))) for fold in folds],
        "test_counts": [int(len(fold.get("test_indices", []))) for fold in folds],
    }


def _fold_indices_digest(folds: list[dict[str, list[int]]]) -> str:
    payload = [
        {
            "train_indices": [int(value) for value in fold.get("train_indices", [])],
            "validation_indices": [int(value) for value in fold.get("validation_indices", [])],
            "test_indices": [int(value) for value in fold.get("test_indices", [])],
        }
        for fold in folds
    ]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _array_digest(values: np.ndarray) -> str:
    arr = np.ascontiguousarray(np.asarray(values, dtype=np.int64))
    return hashlib.sha256(arr.tobytes()).hexdigest()


def _permutation_digest(permutation: np.ndarray) -> str:
    arr = np.asarray(permutation, dtype=np.int64)
    return hashlib.sha256(arr.tobytes()).hexdigest()


def _optional_json(path: Path | None) -> dict[str, object] | None:
    if path is None or not path.exists():
        return None
    return _load_json(path)


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "context_shuffle_metrics.json": result["context_shuffle_metrics"],
        "original_assignment_metrics.json": result["original_assignment_metrics"],
        "original_global_null_metrics.json": result["original_global_null_metrics"],
        "original_mean_only_baseline_metrics.json": result["original_mean_only_baseline_metrics"],
        "context_shuffled_metrics_summary.json": result["context_shuffled_metrics_summary"],
        "context_shuffle_runs.json": result["context_shuffle_runs"],
        "context_protocol_audit.json": result["context_protocol_audit"],
        "selected_context_usage_audit.json": result["selected_context_usage_audit"],
        "s3c_consistency_audit.json": result["s3c_consistency_audit"],
        "leakage_audit.json": result["leakage_audit"],
        "acceptance_audit.json": result["acceptance_audit"],
        "assignment_source_audit.json": result["assignment_source_audit"],
        "heldout_protocol.json": result["heldout_protocol"],
        "feature_schema_match_audit.json": result["feature_schema_match_audit"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    (output / "config.yaml").write_text(yaml.safe_dump({"stage3d3_context_shuffle_audit": result["config"]}, sort_keys=False))
    (output / "summary.md").write_text(format_stage3d3_summary(result))


def format_stage3d3_summary(result: dict[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    report = dict(dict(result.get("context_shuffle_metrics", {})).get("primary_context_report", {}))
    usage = dict(result.get("selected_context_usage_audit", {}))
    return "\n".join(
        [
            "# Stage 3D.3: Context-Shuffle Audit",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Selected model uses context groups: `{str(bool(usage.get('selected_model_uses_context_groups', False))).lower()}`",
            f"- Original categorical population NLL: `{_format_metric(report.get('original_assignment'))}`",
            f"- Context-shuffled categorical population NLL mean: `{_format_metric(report.get('context_shuffled_assignment_mean'))}`",
            f"- Original global-null categorical population NLL: `{_format_metric(report.get('original_global_null'))}`",
            f"- Context-shuffled global-null categorical population NLL mean: `{_format_metric(report.get('context_shuffled_global_null_mean'))}`",
            f"- Context-shuffled-minus-original delta: `{_format_metric(report.get('context_shuffled_minus_original_delta'))}`",
            f"- Original advantage over context shuffle: `{_format_metric(report.get('original_advantage_over_context_shuffle'))}`",
            "",
            "## Claim Boundary",
            "",
            "Stage 3D.3 keeps visible features and discovered assignments fixed, row-shuffles only protocol context-group labels, rebuilds grouped folds, and refits/evaluates the Stage 3C generator. Passing means the context protocol was audited without labels or oracle fields. For context-free selected models, context-shuffled pseudo-folds should remain meaningful and the original grouped split should not be artificially easier.",
            "",
        ]
    )


def _format_metric(value: object) -> str:
    if value is None:
        return "none"
    return f"{float(value):.6f}"
