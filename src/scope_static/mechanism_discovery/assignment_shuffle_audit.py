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
from .observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from .protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR
from .baselines import VARIANCE_FLOOR
from .discovery_model import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3B1_DIR
from .discovery_model import _cap_folds
from .discovery_model import _valid_folds
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


STAGE_NAME = "Stage3D1_assignment_shuffle_generator_audit"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/PHYC_STAGE3_discovery/S3D1_assignment_shuffle_audit"
DEFAULT_SEED = 0
DEFAULT_SHUFFLE_COUNT = 16
DEFAULT_MIN_CATEGORICAL_NLL_DEGRADATION = 1.0e-6
DEFAULT_MIN_COLLAPSE_FRACTION = 0.5
METRIC_KEYS = (
    "categorical_population_nll",
    "gaussian_density_nll",
    "gaussian_nll",
    "raw_visible_feature_mae",
    "population_cross_entropy",
    "population_mae",
    "expectation_mae",
)


def run_stage3d1_assignment_shuffle_audit(
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
    min_categorical_nll_degradation: float = DEFAULT_MIN_CATEGORICAL_NLL_DEGRADATION,
    min_collapse_fraction: float = DEFAULT_MIN_COLLAPSE_FRACTION,
) -> dict[str, object]:
    """Break assignment/feature row alignment and rerun the S3C generator.

    The audit keeps the Stage 3A frozen visible feature matrix fixed and only
    permutes Stage 3B.1 assignment rows. A real S3C signal should degrade toward
    the global-null baseline after this shuffle.
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
    all_folds = _valid_folds(split_manifest, record_count=int(x.shape[0]))
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
    shuffle_runs = assignment_shuffle_runs(
        x,
        responsibilities,
        feature_names=feature_names,
        folds=folds,
        seed=int(seed),
        shuffle_count=int(shuffle_count),
        variance_floor=float(variance_floor),
    )
    shuffled_summary = aggregate_shuffle_runs(shuffle_runs)
    shuffle_metrics = assignment_shuffle_metrics(
        original_assignment_metrics=original,
        shuffled_assignment_metrics_summary=shuffled_summary,
        global_null_metrics=global_null,
        mean_only_baseline_metrics=mean_only,
    )
    leakage = stage3d1_leakage_audit(s3b1_metrics=s3b1_metrics)
    s3c_consistency = s3c_consistency_audit(s3c_metrics=s3c_metrics, recomputed_original=original)
    acceptance = stage3d1_acceptance_audit(
        s3a_metrics=s3a_metrics,
        s3a5_metrics=s3a5_metrics,
        s3b1_metrics=s3b1_metrics,
        feature_match=feature_match,
        feature_matrix=feature_matrix,
        responsibilities=responsibilities,
        shuffle_runs=shuffle_runs,
        assignment_shuffle_metrics=shuffle_metrics,
        leakage_audit=leakage,
        s3c_consistency_audit=s3c_consistency,
        min_categorical_nll_degradation=float(min_categorical_nll_degradation),
        min_collapse_fraction=float(min_collapse_fraction),
    )
    result = {
        "schema": "scope_static_stage3d1_assignment_shuffle_audit_v1",
        "stage": STAGE_NAME,
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="assignment_shuffle_generator_audit"),
        "stage3a_dir": str(s3a),
        "stage3a5_dir": str(s3a5),
        "stage3b1_dir": str(s3b1),
        "stage3c_dir": None if s3c is None else str(s3c),
        "output_dir": str(output),
        "claim_boundary": {
            "keeps_visible_features_fixed": True,
            "shuffles_discovered_assignment_rows": True,
            "preserves_assignment_column_distribution": True,
            "refits_stage3c_generator_after_shuffle": True,
            "uses_mechanism_labels_for_generator_fit": False,
            "uses_oracle_assignment_comparator": False,
            "uses_channels_ptms_kraus": False,
            "tests_latent_structure_not_unconditional_generator": True,
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
            "min_categorical_nll_degradation": float(min_categorical_nll_degradation),
            "min_collapse_fraction": float(min_collapse_fraction),
        },
        "visible_feature_matrix": feature_matrix,
        "feature_schema_match_audit": feature_match,
        "heldout_protocol": heldout_protocol_artifact(all_folds=all_folds, evaluated_folds=folds, max_cv_folds=max_cv_folds),
        "assignment_source_audit": assignment_source_audit(s3b1_dir=s3b1, responsibilities=responsibilities),
        "assignment_shuffle_metrics": shuffle_metrics,
        "original_assignment_metrics": original,
        "shuffled_assignment_metrics_summary": shuffled_summary,
        "shuffle_runs": shuffle_runs,
        "global_null_metrics": global_null,
        "mean_only_baseline_metrics": mean_only,
        "s3c_consistency_audit": s3c_consistency,
        "leakage_audit": leakage,
        "acceptance_audit": acceptance,
        "decision": "stage3d1_assignment_shuffle_audit_passed" if acceptance["passed"] else "stage3d1_assignment_shuffle_audit_failed",
    }
    _write_outputs(output, result)
    return result


def assignment_shuffle_runs(
    x: np.ndarray,
    responsibilities: np.ndarray,
    *,
    feature_names: list[str],
    folds: list[dict[str, list[int]]],
    seed: int,
    shuffle_count: int,
    variance_floor: float,
) -> list[dict[str, object]]:
    rng = np.random.default_rng(int(seed))
    runs = []
    base_mass = np.sum(responsibilities, axis=0)
    for idx in range(max(0, int(shuffle_count))):
        permutation = _non_identity_permutation(rng, int(responsibilities.shape[0]))
        shuffled = responsibilities[permutation]
        metrics = evaluate_predicted_assignment_generation(
            x,
            shuffled,
            feature_names=feature_names,
            folds=folds,
            variance_floor=float(variance_floor),
        )
        shuffled_mass = np.sum(shuffled, axis=0)
        runs.append(
            {
                "schema": "scope_static_stage3d1_assignment_shuffle_run_v1",
                "shuffle_index": int(idx),
                "permutation_sha256": _permutation_digest(permutation),
                "row_count": int(permutation.size),
                "unchanged_row_fraction": float(np.mean(permutation == np.arange(permutation.size))) if permutation.size else 0.0,
                "row_alignment_changed": bool(permutation.size <= 1 or not np.array_equal(permutation, np.arange(permutation.size))),
                "visible_features_fixed": True,
                "assignment_column_distribution_preserved": bool(np.allclose(base_mass, shuffled_mass)),
                "max_assignment_column_mass_abs_diff": float(np.max(np.abs(base_mass - shuffled_mass))) if base_mass.size else 0.0,
                "row_stochastic": bool(shuffled.size == 0 or np.allclose(np.sum(shuffled, axis=1), 1.0)),
                "metrics": metrics,
                "overall": dict(metrics.get("overall", {})),
            }
        )
    return runs


def aggregate_shuffle_runs(shuffle_runs: list[dict[str, object]]) -> dict[str, object]:
    metric_summary = {}
    for key in METRIC_KEYS:
        values = []
        for run in shuffle_runs:
            overall = dict(run.get("overall", {})) if isinstance(run.get("overall", {}), dict) else {}
            if overall.get(key) is not None:
                values.append(float(overall[key]))
        metric_summary[key] = _summarize_values(values)
    return {
        "schema": "scope_static_stage3d1_shuffled_assignment_metrics_summary_v1",
        "shuffle_count": int(len(shuffle_runs)),
        "primary_generation_likelihood_metric": PRIMARY_GENERATION_LIKELIHOOD_METRIC,
        "secondary_continuous_density_diagnostic": SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC,
        "metrics": metric_summary,
        "all_assignment_column_distributions_preserved": bool(
            shuffle_runs and all(bool(run.get("assignment_column_distribution_preserved", False)) for run in shuffle_runs)
        ),
        "all_visible_features_fixed": bool(shuffle_runs and all(bool(run.get("visible_features_fixed", False)) for run in shuffle_runs)),
        "all_row_alignments_changed": bool(
            shuffle_runs and all(bool(run.get("row_alignment_changed", False)) for run in shuffle_runs)
        ),
        "max_unchanged_row_fraction": float(max((float(run.get("unchanged_row_fraction", 0.0)) for run in shuffle_runs), default=0.0)),
        "max_assignment_column_mass_abs_diff": float(
            max((float(run.get("max_assignment_column_mass_abs_diff", 0.0)) for run in shuffle_runs), default=0.0)
        ),
    }


def assignment_shuffle_metrics(
    *,
    original_assignment_metrics: dict[str, object],
    shuffled_assignment_metrics_summary: dict[str, object],
    global_null_metrics: dict[str, object],
    mean_only_baseline_metrics: dict[str, object],
) -> dict[str, object]:
    original = dict(original_assignment_metrics.get("overall", {}))
    global_null = dict(global_null_metrics.get("overall", {}))
    mean_only = dict(mean_only_baseline_metrics.get("overall", {}))
    metric_summary = dict(shuffled_assignment_metrics_summary.get("metrics", {}))
    primary = PRIMARY_GENERATION_LIKELIHOOD_METRIC
    shuffled_primary = dict(metric_summary.get(primary, {}))
    return {
        "schema": "scope_static_stage3d1_assignment_shuffle_metrics_v1",
        "control": "keep visible features fixed, shuffle discovered assignment rows, refit/evaluate Stage 3C generator",
        "expected_result": "categorical_population_nll and replay metrics collapse toward null if S3C depends on learned latent structure",
        "primary_generation_likelihood_metric": primary,
        "secondary_continuous_density_diagnostic": SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC,
        "primary_collapse_report": _collapse_report(
            original_value=original.get(primary),
            shuffled_mean=shuffled_primary.get("mean"),
            global_null_value=global_null.get(primary),
            mean_only_value=mean_only.get(primary),
        ),
        "original_assignment_model": original,
        "shuffled_assignment_model_mean": {key: dict(metric_summary.get(key, {})).get("mean") for key in METRIC_KEYS},
        "global_null_model": global_null,
        "mean_only_baseline": mean_only,
    }


def stage3d1_leakage_audit(*, s3b1_metrics: dict[str, object]) -> dict[str, object]:
    boundary = dict(s3b1_metrics.get("claim_boundary", {})) if isinstance(s3b1_metrics.get("claim_boundary", {}), dict) else {}
    checks = {
        "uses_stage3a_frozen_visible_features": True,
        "uses_stage3b1_learned_assignments": True,
        "assignment_shuffle_uses_labels": False,
        "assignment_shuffle_uses_channels_ptms_kraus": False,
        "assignment_shuffle_uses_teacher_self_features": False,
        "assignment_shuffle_uses_oracle_prototypes": False,
        "stage3b1_assignments_trained_from_frozen_visible_features": bool(boundary.get("trains_from_stage3a_frozen_visible_features", False)),
        "stage3b1_labels_not_used_for_fit": not bool(boundary.get("uses_mechanism_labels_for_fit", True)),
        "stage3b1_labels_not_used_for_model_selection": not bool(boundary.get("uses_mechanism_labels_for_model_selection", True)),
    }
    return {
        "schema": "scope_static_stage3d1_leakage_audit_v1",
        "passed": bool(
            checks["uses_stage3a_frozen_visible_features"]
            and checks["uses_stage3b1_learned_assignments"]
            and not checks["assignment_shuffle_uses_labels"]
            and not checks["assignment_shuffle_uses_channels_ptms_kraus"]
            and not checks["assignment_shuffle_uses_teacher_self_features"]
            and not checks["assignment_shuffle_uses_oracle_prototypes"]
            and checks["stage3b1_assignments_trained_from_frozen_visible_features"]
            and checks["stage3b1_labels_not_used_for_fit"]
            and checks["stage3b1_labels_not_used_for_model_selection"]
        ),
        "checks": checks,
    }


def s3c_consistency_audit(*, s3c_metrics: dict[str, object] | None, recomputed_original: dict[str, object]) -> dict[str, object]:
    if not s3c_metrics:
        return {
            "schema": "scope_static_stage3d1_s3c_consistency_audit_v1",
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
        "schema": "scope_static_stage3d1_s3c_consistency_audit_v1",
        "s3c_metrics_present": True,
        "passed": bool(max_delta <= 1.0e-9),
        "max_abs_delta": float(max_delta),
        "metric_abs_deltas": deltas,
    }


def stage3d1_acceptance_audit(
    *,
    s3a_metrics: dict[str, object],
    s3a5_metrics: dict[str, object],
    s3b1_metrics: dict[str, object],
    feature_match: dict[str, object],
    feature_matrix: dict[str, object],
    responsibilities: np.ndarray,
    shuffle_runs: list[dict[str, object]],
    assignment_shuffle_metrics: dict[str, object],
    leakage_audit: dict[str, object],
    s3c_consistency_audit: dict[str, object],
    min_categorical_nll_degradation: float,
    min_collapse_fraction: float,
) -> dict[str, object]:
    collapse = dict(assignment_shuffle_metrics.get("primary_collapse_report", {}))
    original_lift = collapse.get("global_null_minus_original_lift")
    degradation = collapse.get("shuffled_mean_minus_original_degradation")
    collapse_fraction = collapse.get("collapse_fraction_toward_global_null")
    checks = {
        "stage3a_acceptance_passed": bool(dict(s3a_metrics.get("acceptance_audit", {})).get("passed", False)),
        "stage3a5_acceptance_passed": bool(dict(s3a5_metrics.get("acceptance_audit", {})).get("passed", False)),
        "stage3b1_acceptance_passed": bool(dict(s3b1_metrics.get("acceptance_audit", {})).get("passed", False)),
        "approved_feature_schema_matches_stage3a": bool(feature_match.get("passed", False)),
        "uses_stage3a_frozen_visible_features": bool(feature_matrix.get("loaded_from_stage3a_artifact", False)),
        "assignment_matrix_row_stochastic": bool(responsibilities.size == 0 or np.allclose(np.sum(responsibilities, axis=1), 1.0)),
        "shuffle_count_positive": bool(len(shuffle_runs) > 0),
        "visible_features_fixed_for_all_shuffles": bool(
            shuffle_runs and all(bool(run.get("visible_features_fixed", False)) for run in shuffle_runs)
        ),
        "assignment_distribution_preserved_for_all_shuffles": bool(
            shuffle_runs and all(bool(run.get("assignment_column_distribution_preserved", False)) for run in shuffle_runs)
        ),
        "assignment_row_alignment_changed_for_all_shuffles": bool(
            shuffle_runs and all(bool(run.get("row_alignment_changed", False)) for run in shuffle_runs)
        ),
        "original_assignment_beats_global_null_primary_nll": bool(original_lift is not None and float(original_lift) > 0.0),
        "shuffled_assignment_primary_nll_worse_than_original": bool(
            degradation is not None and float(degradation) >= float(min_categorical_nll_degradation)
        ),
        "shuffle_collapses_toward_global_null": bool(
            collapse_fraction is not None and float(collapse_fraction) >= float(min_collapse_fraction)
        ),
        "s3c_consistency_passed": bool(s3c_consistency_audit.get("passed", False)),
        "leakage_audit_passed": bool(leakage_audit.get("passed", False)),
    }
    return {
        "schema": "scope_static_stage3d1_acceptance_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
        "thresholds": {
            "min_categorical_nll_degradation": float(min_categorical_nll_degradation),
            "min_collapse_fraction": float(min_collapse_fraction),
        },
        "primary_collapse_report": collapse,
    }


def _collapse_report(
    *,
    original_value: object,
    shuffled_mean: object,
    global_null_value: object,
    mean_only_value: object,
) -> dict[str, object]:
    original = _optional_float(original_value)
    shuffled = _optional_float(shuffled_mean)
    global_null = _optional_float(global_null_value)
    mean_only = _optional_float(mean_only_value)
    original_lift = None if original is None or global_null is None else global_null - original
    shuffled_lift = None if shuffled is None or global_null is None else global_null - shuffled
    degradation = None if original is None or shuffled is None else shuffled - original
    collapse_fraction = None
    residual_lift_fraction = None
    if original_lift is not None and abs(float(original_lift)) > 0.0 and degradation is not None and shuffled_lift is not None:
        collapse_fraction = float(degradation) / float(original_lift)
        residual_lift_fraction = float(shuffled_lift) / float(original_lift)
    return {
        "metric": PRIMARY_GENERATION_LIKELIHOOD_METRIC,
        "lower_is_better": True,
        "original_assignment": original,
        "shuffled_assignment_mean": shuffled,
        "global_null": global_null,
        "mean_only_baseline": mean_only,
        "global_null_minus_original_lift": original_lift,
        "global_null_minus_shuffled_lift": shuffled_lift,
        "shuffled_mean_minus_original_degradation": degradation,
        "collapse_fraction_toward_global_null": collapse_fraction,
        "residual_lift_fraction_after_shuffle": residual_lift_fraction,
    }


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
        "assignment_shuffle_metrics.json": result["assignment_shuffle_metrics"],
        "original_assignment_metrics.json": result["original_assignment_metrics"],
        "shuffled_assignment_metrics_summary.json": result["shuffled_assignment_metrics_summary"],
        "shuffle_runs.json": result["shuffle_runs"],
        "global_null_metrics.json": result["global_null_metrics"],
        "mean_only_baseline_metrics.json": result["mean_only_baseline_metrics"],
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
    (output / "config.yaml").write_text(yaml.safe_dump({"stage3d1_assignment_shuffle_audit": result["config"]}, sort_keys=False))
    (output / "summary.md").write_text(format_stage3d1_summary(result))


def format_stage3d1_summary(result: dict[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    collapse = dict(dict(result.get("assignment_shuffle_metrics", {})).get("primary_collapse_report", {}))
    return "\n".join(
        [
            "# Stage 3D.1: Assignment-Shuffle Generator Audit",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Original categorical population NLL: `{_format_metric(collapse.get('original_assignment'))}`",
            f"- Shuffled categorical population NLL mean: `{_format_metric(collapse.get('shuffled_assignment_mean'))}`",
            f"- Global-null categorical population NLL: `{_format_metric(collapse.get('global_null'))}`",
            f"- Shuffled-minus-original degradation: `{_format_metric(collapse.get('shuffled_mean_minus_original_degradation'))}`",
            f"- Collapse fraction toward global null: `{_format_metric(collapse.get('collapse_fraction_toward_global_null'))}`",
            "",
            "## Claim Boundary",
            "",
            "Stage 3D.1 keeps the frozen visible feature matrix fixed, shuffles only discovered Stage 3B.1 assignment rows, and refits/evaluates the Stage 3C generator. Passing means the S3C replay signal degrades toward the null baseline when latent assignment structure is broken.",
            "",
        ]
    )


def _format_metric(value: object) -> str:
    if value is None:
        return "none"
    return f"{float(value):.6f}"
