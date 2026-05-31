from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.protocols import LEARNER_VALIDATION_STAGE
from .artifacts import feature_schema_matches_stage3a as _feature_schema_matches_s3a
from .artifacts import load_json_object as _load_json
from .artifacts import load_stage3_evaluator_labels
from .artifacts import load_stage3a_frozen_visible_features
from .artifacts import mechanism_sort_key
from .artifacts import resolve_teacher_dir
from .baselines import VARIANCE_FLOOR
from .baselines import evaluate_cluster_assignments
from .discovery_model import context_dependent_mechanism_diagnostics
from .discovery_model import _cap_folds
from .discovery_model import _valid_folds
from .generator_learning import DEFAULT_MAX_CV_FOLDS
from .generator_learning import PRIMARY_GENERATION_LIKELIHOOD_METRIC
from .generator_learning import SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC
from .generator_learning import evaluate_global_null_generation
from .generator_learning import evaluate_mean_only_generation
from .generator_learning import evaluate_predicted_assignment_generation
from .generator_learning import heldout_protocol_artifact
from .k_stress_audit import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3D4_DIR
from .observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from .protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR


STAGE_NAME = "Stage3D4b_overcomplete_merge_prune_audit"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/PHYC_STAGE3_discovery/S3D4b_overcomplete_merge_prune_audit"
DEFAULT_OVERCOMPLETE_ASSIGNMENT_KEY = "overcomplete_2x"
DEFAULT_MAX_MICROCLUSTER_SUPPORT = 3
DEFAULT_MAX_MICROCLUSTER_FRACTION = 0.01
DEFAULT_MIN_MICROCLUSTER_FAMILY_COUNT = 2
DEFAULT_MIN_POSTMERGE_NMI = 0.99
DEFAULT_MIN_POSTMERGE_ARI = 0.99
DEFAULT_MIN_POSTMERGE_BA = 0.99
DEFAULT_MIN_POSTMERGE_MIN_RECALL = 0.99
DEFAULT_MAX_GENERATION_NLL_INCREASE = 0.05


def run_stage3d4b_overcomplete_merge_prune_audit(
    *,
    stage3a_dir: str | Path = DEFAULT_STAGE3A_DIR,
    stage3a5_dir: str | Path = DEFAULT_STAGE3A5_DIR,
    stage3d4_dir: str | Path = DEFAULT_STAGE3D4_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    teacher_dir: str | Path | None = None,
    overcomplete_assignment_key: str = DEFAULT_OVERCOMPLETE_ASSIGNMENT_KEY,
    max_microcluster_support: int = DEFAULT_MAX_MICROCLUSTER_SUPPORT,
    max_microcluster_fraction: float = DEFAULT_MAX_MICROCLUSTER_FRACTION,
    min_microcluster_family_count: int = DEFAULT_MIN_MICROCLUSTER_FAMILY_COUNT,
    max_cv_folds: int | None = DEFAULT_MAX_CV_FOLDS,
    variance_floor: float = VARIANCE_FLOOR,
    min_postmerge_nmi: float = DEFAULT_MIN_POSTMERGE_NMI,
    min_postmerge_ari: float = DEFAULT_MIN_POSTMERGE_ARI,
    min_postmerge_ba: float = DEFAULT_MIN_POSTMERGE_BA,
    min_postmerge_min_recall: float = DEFAULT_MIN_POSTMERGE_MIN_RECALL,
    max_generation_nll_increase: float = DEFAULT_MAX_GENERATION_NLL_INCREASE,
) -> dict[str, object]:
    """Merge/prune overcomplete microclusters using visible-only assignments.

    The merge rule intentionally does not inspect mechanism labels. It prunes
    inactive overcomplete clusters, keeps macro clusters separate, and merges
    only assignment microclusters whose support is below a declared visible
    threshold into one tail-submode family. Evaluator labels are loaded only
    after the merge map is fixed.
    """

    s3a = Path(stage3a_dir)
    s3a5 = Path(stage3a5_dir)
    s3d4 = Path(stage3d4_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    s3a_metrics = _load_json(s3a / "metrics.json")
    s3a5_metrics = _load_json(s3a5 / "metrics.json")
    s3d4_metrics = _load_json(s3d4 / "metrics.json")
    teacher = resolve_teacher_dir(s3a_metrics, teacher_dir)
    x, feature_names, feature_matrix = load_stage3a_frozen_visible_features(s3a)
    feature_match = _feature_schema_matches_s3a(s3a, feature_names)
    split_manifest = dict(s3a_metrics.get("split_manifest", {})) if isinstance(s3a_metrics.get("split_manifest", {}), dict) else {}
    all_folds = _valid_folds(split_manifest, record_count=int(x.shape[0]))
    folds = _cap_folds(all_folds, max_cv_folds=max_cv_folds)
    if not folds:
        folds = [{"train_indices": list(range(int(x.shape[0]))), "validation_indices": [], "test_indices": list(range(int(x.shape[0])))}]

    overcomplete = load_overcomplete_assignments(
        s3d4 / "learned_assignments_by_k.npz",
        key=str(overcomplete_assignment_key),
        record_count=int(x.shape[0]),
    )
    raw_hard = np.argmax(overcomplete, axis=1).astype(np.int64) if overcomplete.size else np.zeros(0, dtype=np.int64)
    cluster_summary = overcomplete_cluster_summary(
        x,
        raw_hard,
        responsibilities=overcomplete,
        feature_names=feature_names,
    )
    merge_map = microcluster_merge_map(
        cluster_summary,
        record_count=int(x.shape[0]),
        max_microcluster_support=int(max_microcluster_support),
        max_microcluster_fraction=float(max_microcluster_fraction),
        min_microcluster_family_count=int(min_microcluster_family_count),
    )
    merged_hard, merged_assignments = apply_merge_map(raw_hard, merge_map)

    raw_generation = evaluate_predicted_assignment_generation(
        x,
        overcomplete,
        feature_names=feature_names,
        folds=folds,
        variance_floor=float(variance_floor),
    )
    merged_generation = evaluate_predicted_assignment_generation(
        x,
        merged_assignments,
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

    evaluator = load_stage3_evaluator_labels(s3a, teacher)
    labels = evaluator.exact_labels
    if len(labels) != int(x.shape[0]):
        raise ValueError(f"Stage 3A frozen feature row count {x.shape[0]} does not match evaluator label count {len(labels)}")
    alias = dict(s3a5_metrics.get("oracle_alias_classes", {})) if isinstance(s3a5_metrics.get("oracle_alias_classes", {}), dict) else {}
    label_to_quotient = {str(k): str(v) for k, v in dict(alias.get("label_to_quotient", {})).items()}
    quotient_labels = [label_to_quotient.get(label, label) for label in labels]
    quotient_class_names = sorted(set(quotient_labels), key=mechanism_sort_key)
    raw_recovery = evaluate_cluster_assignments(
        raw_hard,
        exact_labels=labels,
        exact_class_names=evaluator.exact_class_names,
        quotient_labels=quotient_labels,
        quotient_class_names=quotient_class_names,
    )
    postmerge_recovery = evaluate_cluster_assignments(
        merged_hard,
        exact_labels=labels,
        exact_class_names=evaluator.exact_class_names,
        quotient_labels=quotient_labels,
        quotient_class_names=quotient_class_names,
    )
    postmerge_context_dependent = context_dependent_mechanism_diagnostics(
        merged_hard,
        records=evaluator.records,
        cluster_to_label_match=dict(postmerge_recovery["exact_label_metrics"].get("cluster_to_label_match", {})),
    )
    postmerge_metrics = postmerge_metrics_artifact(
        raw_recovery=raw_recovery,
        postmerge_recovery=postmerge_recovery,
        raw_generation=raw_generation,
        postmerge_generation=merged_generation,
        global_null_metrics=global_null,
        postmerge_context_dependent=postmerge_context_dependent,
    )
    leakage = stage3d4b_leakage_audit(s3d4_metrics=s3d4_metrics)
    acceptance = stage3d4b_acceptance_audit(
        s3a_metrics=s3a_metrics,
        s3a5_metrics=s3a5_metrics,
        s3d4_metrics=s3d4_metrics,
        feature_match=feature_match,
        feature_matrix=feature_matrix,
        merge_map=merge_map,
        postmerge_metrics=postmerge_metrics,
        leakage_audit=leakage,
        min_postmerge_nmi=float(min_postmerge_nmi),
        min_postmerge_ari=float(min_postmerge_ari),
        min_postmerge_ba=float(min_postmerge_ba),
        min_postmerge_min_recall=float(min_postmerge_min_recall),
        max_generation_nll_increase=float(max_generation_nll_increase),
    )
    result = {
        "schema": "scope_static_stage3d4b_overcomplete_merge_prune_audit_v1",
        "stage": STAGE_NAME,
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="overcomplete_merge_prune_audit"),
        "stage3a_dir": str(s3a),
        "stage3a5_dir": str(s3a5),
        "stage3d4_dir": str(s3d4),
        "teacher_dir": str(teacher),
        "output_dir": str(output),
        "claim_boundary": {
            "uses_overcomplete_assignments_from_stage3d4": True,
            "uses_visible_features_for_cluster_summaries": True,
            "uses_mechanism_labels_for_merge_rule": False,
            "uses_mechanism_labels_for_model_selection": False,
            "uses_channels_ptms_kraus": False,
            "uses_teacher_self_features": False,
            "evaluator_only_metrics_after_merge": True,
            "postmerge_family_claim_not_raw_hidden_label_supervision": True,
        },
        "config": {
            "stage3a_dir": str(s3a),
            "stage3a5_dir": str(s3a5),
            "stage3d4_dir": str(s3d4),
            "teacher_dir": str(teacher),
            "output_dir": str(output),
            "overcomplete_assignment_key": str(overcomplete_assignment_key),
            "max_microcluster_support": int(max_microcluster_support),
            "max_microcluster_fraction": float(max_microcluster_fraction),
            "min_microcluster_family_count": int(min_microcluster_family_count),
            "max_cv_folds": None if max_cv_folds is None else int(max_cv_folds),
            "variance_floor": float(variance_floor),
            "min_postmerge_nmi": float(min_postmerge_nmi),
            "min_postmerge_ari": float(min_postmerge_ari),
            "min_postmerge_ba": float(min_postmerge_ba),
            "min_postmerge_min_recall": float(min_postmerge_min_recall),
            "max_generation_nll_increase": float(max_generation_nll_increase),
        },
        "visible_feature_matrix": feature_matrix,
        "feature_schema_match_audit": feature_match,
        "heldout_protocol": heldout_protocol_artifact(all_folds=all_folds, evaluated_folds=folds, max_cv_folds=max_cv_folds),
        "merge_prune_plan": merge_prune_plan_artifact(
            overcomplete_assignment_key=str(overcomplete_assignment_key),
            max_microcluster_support=int(max_microcluster_support),
            max_microcluster_fraction=float(max_microcluster_fraction),
            min_microcluster_family_count=int(min_microcluster_family_count),
        ),
        "overcomplete_cluster_summary": cluster_summary,
        "merge_map": merge_map,
        "postmerge_metrics": postmerge_metrics,
        "raw_overcomplete_generation_metrics": raw_generation,
        "postmerge_generation_metrics": merged_generation,
        "global_null_metrics": global_null,
        "mean_only_baseline_metrics": mean_only,
        "leakage_audit": leakage,
        "acceptance_audit": acceptance,
        "decision": "stage3d4b_overcomplete_merge_prune_audit_passed" if acceptance["passed"] else "stage3d4b_overcomplete_merge_prune_audit_failed",
    }
    _write_outputs(output, result, merged_assignments)
    return result


def load_overcomplete_assignments(path: str | Path, *, key: str, record_count: int) -> np.ndarray:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"missing Stage 3D.4 assignment bundle: {source}")
    with np.load(source) as data:
        if key not in data.files:
            raise KeyError(f"{source} does not contain assignment key {key!r}; available keys: {data.files}")
        matrix = np.asarray(data[key], dtype=np.float64)
    if matrix.ndim != 2:
        raise ValueError(f"{source}:{key} must be a 2D assignment matrix")
    if int(matrix.shape[0]) != int(record_count):
        raise ValueError(f"{source}:{key} row count {matrix.shape[0]} does not match Stage 3A record count {record_count}")
    if matrix.size and not np.allclose(np.sum(matrix, axis=1), 1.0):
        raise ValueError(f"{source}:{key} assignment rows must be stochastic")
    return matrix


def overcomplete_cluster_summary(
    x: np.ndarray,
    hard_assignments: np.ndarray,
    *,
    responsibilities: np.ndarray,
    feature_names: list[str],
) -> dict[str, object]:
    rows = []
    active = sorted(set(np.asarray(hard_assignments, dtype=np.int64).tolist()))
    for cluster in active:
        idx = np.asarray([row for row, value in enumerate(hard_assignments.tolist()) if int(value) == int(cluster)], dtype=np.int64)
        local = x[idx]
        mean = np.mean(local, axis=0) if idx.size else np.zeros(int(x.shape[1]), dtype=np.float64)
        top = _top_feature_rows(mean, feature_names, limit=8)
        rows.append(
            {
                "cluster": f"C{int(cluster):03d}",
                "cluster_index": int(cluster),
                "support": int(idx.size),
                "support_fraction": float(idx.size) / float(max(1, int(x.shape[0]))),
                "assignment_mass": float(np.sum(responsibilities[:, int(cluster)])) if int(cluster) < int(responsibilities.shape[1]) else 0.0,
                "prototype_sha256": _vector_digest(mean),
                "top_visible_features_by_abs_mean": top,
            }
        )
    return {
        "schema": "scope_static_stage3d4b_overcomplete_cluster_summary_v1",
        "record_count": int(x.shape[0]),
        "feature_count": int(x.shape[1]) if x.ndim == 2 else 0,
        "active_cluster_count": int(len(rows)),
        "clusters": rows,
    }


def microcluster_merge_map(
    cluster_summary: dict[str, object],
    *,
    record_count: int,
    max_microcluster_support: int,
    max_microcluster_fraction: float,
    min_microcluster_family_count: int,
) -> dict[str, object]:
    clusters = [dict(row) for row in cluster_summary.get("clusters", []) if isinstance(row, dict)]
    micro = [
        row
        for row in clusters
        if int(row.get("support", 0)) <= int(max_microcluster_support)
        and float(row.get("support_fraction", 0.0)) <= float(max_microcluster_fraction)
    ]
    merge_micro = len(micro) >= int(min_microcluster_family_count)
    macro = [row for row in clusters if row not in micro or not merge_micro]
    family_rows = []
    cluster_to_family: dict[str, str] = {}
    for family_idx, row in enumerate(macro):
        family = f"F{family_idx:03d}"
        cluster = str(row["cluster"])
        cluster_to_family[cluster] = family
        family_rows.append(
            {
                "family": family,
                "merge_type": "macro_single_cluster",
                "source_clusters": [cluster],
                "support": int(row.get("support", 0)),
            }
        )
    if merge_micro:
        family = f"F{len(family_rows):03d}"
        source_clusters = [str(row["cluster"]) for row in micro]
        for cluster in source_clusters:
            cluster_to_family[cluster] = family
        family_rows.append(
            {
                "family": family,
                "merge_type": "microcluster_tail_family",
                "source_clusters": source_clusters,
                "support": int(sum(int(row.get("support", 0)) for row in micro)),
            }
        )
    return {
        "schema": "scope_static_stage3d4b_microcluster_merge_map_v1",
        "strategy": "prune inactive clusters, keep macro clusters separate, merge all declared microclusters into one visible-only tail-submode family",
        "uses_labels_for_merge_rule": False,
        "uses_channels_ptms_kraus": False,
        "record_count": int(record_count),
        "active_cluster_count": int(len(clusters)),
        "postmerge_family_count": int(len(family_rows)),
        "microcluster_count": int(len(micro)),
        "microcluster_total_support": int(sum(int(row.get("support", 0)) for row in micro)),
        "microcluster_merge_applied": bool(merge_micro),
        "max_microcluster_support": int(max_microcluster_support),
        "max_microcluster_fraction": float(max_microcluster_fraction),
        "min_microcluster_family_count": int(min_microcluster_family_count),
        "cluster_to_family": cluster_to_family,
        "families": family_rows,
    }


def apply_merge_map(hard_assignments: np.ndarray, merge_map: dict[str, object]) -> tuple[np.ndarray, np.ndarray]:
    cluster_to_family = {str(k): str(v) for k, v in dict(merge_map.get("cluster_to_family", {})).items()}
    families = [str(row.get("family")) for row in merge_map.get("families", []) if isinstance(row, dict)]
    family_to_idx = {family: idx for idx, family in enumerate(families)}
    merged = np.zeros(int(hard_assignments.shape[0]), dtype=np.int64)
    for idx, cluster in enumerate(np.asarray(hard_assignments, dtype=np.int64).tolist()):
        family = cluster_to_family.get(f"C{int(cluster):03d}")
        if family is None:
            raise ValueError(f"cluster C{int(cluster):03d} missing from merge map")
        merged[idx] = int(family_to_idx[family])
    matrix = np.zeros((int(merged.shape[0]), int(len(families))), dtype=np.float64)
    if matrix.size:
        matrix[np.arange(int(merged.shape[0])), merged] = 1.0
    return merged, matrix


def merge_prune_plan_artifact(
    *,
    overcomplete_assignment_key: str,
    max_microcluster_support: int,
    max_microcluster_fraction: float,
    min_microcluster_family_count: int,
) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3d4b_merge_prune_plan_v1",
        "input_assignment_key": str(overcomplete_assignment_key),
        "rule": "active clusters with support <= max_microcluster_support and support_fraction <= max_microcluster_fraction are microclusters; if enough exist, merge them into one tail-submode family",
        "max_microcluster_support": int(max_microcluster_support),
        "max_microcluster_fraction": float(max_microcluster_fraction),
        "min_microcluster_family_count": int(min_microcluster_family_count),
        "uses_mechanism_labels_for_merge_rule": False,
        "uses_oracle_prototypes": False,
        "uses_channels_ptms_kraus": False,
        "labels_loaded_after_merge_for_evaluator_metrics": True,
    }


def postmerge_metrics_artifact(
    *,
    raw_recovery: dict[str, object],
    postmerge_recovery: dict[str, object],
    raw_generation: dict[str, object],
    postmerge_generation: dict[str, object],
    global_null_metrics: dict[str, object],
    postmerge_context_dependent: dict[str, object],
) -> dict[str, object]:
    raw_exact = dict(raw_recovery.get("exact_label_metrics", {}))
    post_exact = dict(postmerge_recovery.get("exact_label_metrics", {}))
    raw_overall = dict(raw_generation.get("overall", {}))
    post_overall = dict(postmerge_generation.get("overall", {}))
    null_overall = dict(global_null_metrics.get("overall", {}))
    primary = PRIMARY_GENERATION_LIKELIHOOD_METRIC
    raw_nll = _optional_float(raw_overall.get(primary))
    post_nll = _optional_float(post_overall.get(primary))
    null_nll = _optional_float(null_overall.get(primary))
    return {
        "schema": "scope_static_stage3d4b_postmerge_metrics_v1",
        "primary_generation_likelihood_metric": primary,
        "secondary_continuous_density_diagnostic": SECONDARY_CONTINUOUS_DENSITY_DIAGNOSTIC,
        "raw_overcomplete_exact_metrics": raw_exact,
        "postmerge_exact_metrics": post_exact,
        "raw_overcomplete_quotient_metrics": raw_recovery.get("quotient_label_metrics", {}),
        "postmerge_quotient_metrics": postmerge_recovery.get("quotient_label_metrics", {}),
        "postmerge_context_dependent_mechanism_diagnostics": postmerge_context_dependent,
        "metric_deltas": {
            "exact_ari_delta": _delta(post_exact.get("adjusted_rand_index"), raw_exact.get("adjusted_rand_index")),
            "exact_nmi_delta": _delta(post_exact.get("normalized_mutual_info"), raw_exact.get("normalized_mutual_info")),
            "exact_ba_delta": _delta(post_exact.get("balanced_accuracy_after_label_matching"), raw_exact.get("balanced_accuracy_after_label_matching")),
            "exact_min_recall_delta": _delta(post_exact.get("min_recall_after_label_matching"), raw_exact.get("min_recall_after_label_matching")),
            "categorical_population_nll_delta": _delta(post_nll, raw_nll),
        },
        "generation_report": {
            "raw_overcomplete_categorical_population_nll": raw_nll,
            "postmerge_categorical_population_nll": post_nll,
            "global_null_categorical_population_nll": null_nll,
            "raw_overcomplete_null_lift": None if raw_nll is None or null_nll is None else null_nll - raw_nll,
            "postmerge_null_lift": None if post_nll is None or null_nll is None else null_nll - post_nll,
            "postmerge_minus_raw_nll": None if post_nll is None or raw_nll is None else post_nll - raw_nll,
        },
    }


def stage3d4b_leakage_audit(*, s3d4_metrics: dict[str, object]) -> dict[str, object]:
    d4_boundary = dict(s3d4_metrics.get("claim_boundary", {})) if isinstance(s3d4_metrics.get("claim_boundary", {}), dict) else {}
    checks = {
        "uses_stage3a_frozen_visible_features": True,
        "uses_stage3d4_overcomplete_assignments": True,
        "merge_rule_uses_labels": False,
        "merge_rule_uses_channels_ptms_kraus": False,
        "merge_rule_uses_teacher_self_features": False,
        "merge_rule_uses_oracle_prototypes": False,
        "stage3d4_labels_not_used_for_fit": not bool(d4_boundary.get("uses_mechanism_labels_for_fit", True)),
        "stage3d4_labels_not_used_for_model_selection": not bool(d4_boundary.get("uses_mechanism_labels_for_model_selection", True)),
    }
    return {
        "schema": "scope_static_stage3d4b_leakage_audit_v1",
        "passed": bool(
            checks["uses_stage3a_frozen_visible_features"]
            and checks["uses_stage3d4_overcomplete_assignments"]
            and not checks["merge_rule_uses_labels"]
            and not checks["merge_rule_uses_channels_ptms_kraus"]
            and not checks["merge_rule_uses_teacher_self_features"]
            and not checks["merge_rule_uses_oracle_prototypes"]
            and checks["stage3d4_labels_not_used_for_fit"]
            and checks["stage3d4_labels_not_used_for_model_selection"]
        ),
        "checks": checks,
    }


def stage3d4b_acceptance_audit(
    *,
    s3a_metrics: dict[str, object],
    s3a5_metrics: dict[str, object],
    s3d4_metrics: dict[str, object],
    feature_match: dict[str, object],
    feature_matrix: dict[str, object],
    merge_map: dict[str, object],
    postmerge_metrics: dict[str, object],
    leakage_audit: dict[str, object],
    min_postmerge_nmi: float,
    min_postmerge_ari: float,
    min_postmerge_ba: float,
    min_postmerge_min_recall: float,
    max_generation_nll_increase: float,
) -> dict[str, object]:
    post = dict(postmerge_metrics.get("postmerge_exact_metrics", {}))
    deltas = dict(postmerge_metrics.get("metric_deltas", {}))
    generation = dict(postmerge_metrics.get("generation_report", {}))
    post_nll_lift = generation.get("postmerge_null_lift")
    post_minus_raw = generation.get("postmerge_minus_raw_nll")
    checks = {
        "stage3a_acceptance_passed": bool(dict(s3a_metrics.get("acceptance_audit", {})).get("passed", False)),
        "stage3a5_acceptance_passed": bool(dict(s3a5_metrics.get("acceptance_audit", {})).get("passed", False)),
        "stage3d4_acceptance_passed": bool(dict(s3d4_metrics.get("acceptance_audit", {})).get("passed", False)),
        "approved_feature_schema_matches_stage3a": bool(feature_match.get("passed", False)),
        "uses_stage3a_frozen_visible_features": bool(feature_matrix.get("loaded_from_stage3a_artifact", False)),
        "microcluster_merge_applied": bool(merge_map.get("microcluster_merge_applied", False)),
        "postmerge_reduces_active_cluster_count": int(merge_map.get("postmerge_family_count", 0)) < int(merge_map.get("active_cluster_count", 0)),
        "merge_rule_uses_no_labels": not bool(merge_map.get("uses_labels_for_merge_rule", True)),
        "postmerge_exact_nmi_passed": float(post.get("normalized_mutual_info", 0.0)) >= float(min_postmerge_nmi),
        "postmerge_exact_ari_passed": float(post.get("adjusted_rand_index", 0.0)) >= float(min_postmerge_ari),
        "postmerge_exact_ba_passed": float(post.get("balanced_accuracy_after_label_matching", 0.0)) >= float(min_postmerge_ba),
        "postmerge_exact_min_recall_passed": float(post.get("min_recall_after_label_matching", 0.0)) >= float(min_postmerge_min_recall),
        "postmerge_min_recall_improves": float(deltas.get("exact_min_recall_delta", 0.0)) > 0.0,
        "postmerge_generation_beats_null": bool(post_nll_lift is not None and float(post_nll_lift) > 0.0),
        "postmerge_generation_not_materially_worse_than_raw": bool(
            post_minus_raw is not None and float(post_minus_raw) <= float(max_generation_nll_increase)
        ),
        "leakage_audit_passed": bool(leakage_audit.get("passed", False)),
    }
    return {
        "schema": "scope_static_stage3d4b_acceptance_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
        "thresholds": {
            "min_postmerge_nmi": float(min_postmerge_nmi),
            "min_postmerge_ari": float(min_postmerge_ari),
            "min_postmerge_ba": float(min_postmerge_ba),
            "min_postmerge_min_recall": float(min_postmerge_min_recall),
            "max_generation_nll_increase": float(max_generation_nll_increase),
        },
    }


def _top_feature_rows(vector: np.ndarray, feature_names: list[str], *, limit: int) -> list[dict[str, object]]:
    order = np.argsort(-np.abs(np.asarray(vector, dtype=np.float64)))[: max(0, int(limit))]
    return [
        {
            "feature": str(feature_names[int(idx)]) if int(idx) < len(feature_names) else f"feature_{int(idx)}",
            "value": float(vector[int(idx)]),
            "abs_value": float(abs(vector[int(idx)])),
        }
        for idx in order.tolist()
    ]


def _vector_digest(vector: np.ndarray) -> str:
    arr = np.ascontiguousarray(np.asarray(vector, dtype=np.float64))
    return hashlib.sha256(arr.tobytes()).hexdigest()


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _delta(left: object, right: object) -> float | None:
    if left is None or right is None:
        return None
    return float(left) - float(right)


def _write_outputs(output: Path, result: dict[str, object], merged_assignments: np.ndarray) -> None:
    artifacts = {
        "metrics.json": result,
        "merge_prune_plan.json": result["merge_prune_plan"],
        "overcomplete_cluster_summary.json": result["overcomplete_cluster_summary"],
        "merge_map.json": result["merge_map"],
        "postmerge_metrics.json": result["postmerge_metrics"],
        "raw_overcomplete_generation_metrics.json": result["raw_overcomplete_generation_metrics"],
        "postmerge_generation_metrics.json": result["postmerge_generation_metrics"],
        "global_null_metrics.json": result["global_null_metrics"],
        "mean_only_baseline_metrics.json": result["mean_only_baseline_metrics"],
        "leakage_audit.json": result["leakage_audit"],
        "acceptance_audit.json": result["acceptance_audit"],
        "heldout_protocol.json": result["heldout_protocol"],
        "feature_schema_match_audit.json": result["feature_schema_match_audit"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    np.save(output / "postmerge_assignments.npy", np.asarray(merged_assignments, dtype=np.float64))
    (output / "config.yaml").write_text(yaml.safe_dump({"stage3d4b_overcomplete_merge_prune_audit": result["config"]}, sort_keys=False))
    (output / "summary.md").write_text(format_stage3d4b_summary(result))


def format_stage3d4b_summary(result: dict[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    merge_map = dict(result.get("merge_map", {}))
    metrics = dict(result.get("postmerge_metrics", {}))
    raw = dict(metrics.get("raw_overcomplete_exact_metrics", {}))
    post = dict(metrics.get("postmerge_exact_metrics", {}))
    gen = dict(metrics.get("generation_report", {}))
    return "\n".join(
        [
            "# Stage 3D.4b: Overcomplete Merge/Prune Audit",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Active overcomplete clusters: `{int(merge_map.get('active_cluster_count', 0))}`",
            f"- Post-merge families: `{int(merge_map.get('postmerge_family_count', 0))}`",
            f"- Microclusters merged: `{int(merge_map.get('microcluster_count', 0))}`",
            f"- Raw exact NMI / ARI / BA / min recall: `{_format_metric(raw.get('normalized_mutual_info'))}` / `{_format_metric(raw.get('adjusted_rand_index'))}` / `{_format_metric(raw.get('balanced_accuracy_after_label_matching'))}` / `{_format_metric(raw.get('min_recall_after_label_matching'))}`",
            f"- Post-merge exact NMI / ARI / BA / min recall: `{_format_metric(post.get('normalized_mutual_info'))}` / `{_format_metric(post.get('adjusted_rand_index'))}` / `{_format_metric(post.get('balanced_accuracy_after_label_matching'))}` / `{_format_metric(post.get('min_recall_after_label_matching'))}`",
            f"- Raw overcomplete categorical population NLL: `{_format_metric(gen.get('raw_overcomplete_categorical_population_nll'))}`",
            f"- Post-merge categorical population NLL: `{_format_metric(gen.get('postmerge_categorical_population_nll'))}`",
            f"- Global-null categorical population NLL: `{_format_metric(gen.get('global_null_categorical_population_nll'))}`",
            "",
            "## Claim Boundary",
            "",
            "Stage 3D.4b uses only overcomplete assignments and learner-visible feature summaries to merge/prune microclusters. Mechanism labels are loaded only after the merge map is fixed for evaluator-only scoring.",
            "",
        ]
    )


def _format_metric(value: object) -> str:
    if value is None:
        return "none"
    return f"{float(value):.6f}"
