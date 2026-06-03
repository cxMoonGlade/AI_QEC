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
from .audit_values import optional_float as _optional_float
from .baselines import VARIANCE_FLOOR
from .baselines import evaluate_cluster_assignments
from .contract_claims import stage3d4b_claim_gate_audit
from .discovery_model import DEFAULT_OPERATION_CONTEXT_WEIGHT
from .discovery_model import _apply_visible_feature_weights
from .discovery_model import context_dependent_mechanism_diagnostics
from .discovery_model import _cap_folds
from .discovery_model import _context_groups_from_split_manifest
from .discovery_model import _standardize_visible_features_with_values
from .discovery_model import _valid_folds
from .discovery_model import load_stage3b1_assignment_visible_feature_view
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
DEFAULT_CONTEXT_RESIDUAL_PROFILE_VETO_THRESHOLD = 0.75


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
    context_residual_profile_veto_threshold: float | None = DEFAULT_CONTEXT_RESIDUAL_PROFILE_VETO_THRESHOLD,
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
    s3b1_dir = _stage3b1_dir_from_stage3d4_metrics(s3d4_metrics)
    x_summary_raw, summary_feature_names, assignment_feature_view = load_stage3b1_assignment_visible_feature_view(
        s3b1_dir,
        fallback_matrix=x,
        fallback_feature_names=feature_names,
    )
    x_summary, _summary_standardization = _standardize_visible_features_with_values(x_summary_raw)
    operation_context_weight = float(
        dict(s3d4_metrics.get("config", {})).get("operation_context_weight", DEFAULT_OPERATION_CONTEXT_WEIGHT)
        if isinstance(s3d4_metrics.get("config", {}), dict)
        else DEFAULT_OPERATION_CONTEXT_WEIGHT
    )
    x_summary, summary_feature_weighting = _apply_visible_feature_weights(
        x_summary,
        feature_names=summary_feature_names,
        operation_context_weight=operation_context_weight,
    )
    feature_match = _feature_schema_matches_s3a(s3a, feature_names)
    split_manifest = dict(s3a_metrics.get("split_manifest", {})) if isinstance(s3a_metrics.get("split_manifest", {}), dict) else {}
    context_groups = _context_groups_from_split_manifest(split_manifest, record_count=int(x.shape[0]))
    all_folds = _valid_folds(split_manifest, record_count=int(x.shape[0]))
    folds = _cap_folds(all_folds, max_cv_folds=max_cv_folds)
    if not folds:
        folds = [{"train_indices": list(range(int(x.shape[0]))), "validation_indices": [], "test_indices": list(range(int(x.shape[0])))}]

    overcomplete = load_overcomplete_assignments(
        s3d4 / "learned_assignments_by_k.npz",
        key=str(overcomplete_assignment_key),
        record_count=int(x.shape[0]),
    )
    split_parent_map = load_split_parent_map(
        s3d4 / "overcomplete_split_parent_maps.json",
        key=str(overcomplete_assignment_key),
        cluster_count=int(overcomplete.shape[1]),
    )
    raw_hard = np.argmax(overcomplete, axis=1).astype(np.int64) if overcomplete.size else np.zeros(0, dtype=np.int64)
    cluster_summary = overcomplete_cluster_summary(
        x_summary,
        raw_hard,
        responsibilities=overcomplete,
        feature_names=summary_feature_names,
        context_groups=context_groups,
        split_parent_map=split_parent_map,
    )
    merge_map = microcluster_merge_map(
        cluster_summary,
        record_count=int(x.shape[0]),
        max_microcluster_support=int(max_microcluster_support),
        max_microcluster_fraction=float(max_microcluster_fraction),
        min_microcluster_family_count=int(min_microcluster_family_count),
        context_residual_profile_veto_threshold=context_residual_profile_veto_threshold,
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
    claim_gate = stage3d4b_claim_gate_audit(
        {
            "acceptance_audit": acceptance,
            "postmerge_metrics": postmerge_metrics,
        }
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
            "uses_stage3b1_assignment_feature_view_for_cluster_summaries": str(assignment_feature_view.get("source", ""))
            == "stage3b1_assignment_visible_features",
            "uses_mechanism_labels_for_merge_rule": False,
            "uses_mechanism_labels_for_model_selection": False,
            "uses_channels_ptms_kraus": False,
            "uses_teacher_self_features": False,
            "evaluator_only_metrics_after_merge": True,
            "postmerge_family_claim_not_raw_hidden_label_supervision": True,
            "uses_stage3d4_split_parent_map_without_labels": split_parent_map is not None,
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
            "context_residual_profile_veto_threshold": (
                None
                if context_residual_profile_veto_threshold is None
                else float(context_residual_profile_veto_threshold)
            ),
            "assignment_feature_view_source": str(assignment_feature_view.get("source", "")),
        },
        "visible_feature_matrix": feature_matrix,
        "assignment_feature_view_audit": assignment_feature_view,
        "assignment_feature_weighting": _d4b_assignment_feature_weighting_artifact(summary_feature_weighting, summary_feature_names),
        "feature_schema_match_audit": feature_match,
        "heldout_protocol": heldout_protocol_artifact(all_folds=all_folds, evaluated_folds=folds, max_cv_folds=max_cv_folds),
        "merge_prune_plan": merge_prune_plan_artifact(
            overcomplete_assignment_key=str(overcomplete_assignment_key),
            max_microcluster_support=int(max_microcluster_support),
            max_microcluster_fraction=float(max_microcluster_fraction),
            min_microcluster_family_count=int(min_microcluster_family_count),
            context_residual_profile_veto_threshold=context_residual_profile_veto_threshold,
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
        "claim_gate_audit": claim_gate,
        "claim_decision": (
            "stage3d4b_postmerge_claim_gate_passed"
            if bool(claim_gate.get("passed", False))
            else "stage3d4b_postmerge_claim_gate_failed"
        ),
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


def _stage3b1_dir_from_stage3d4_metrics(metrics: dict[str, object]) -> Path:
    raw = metrics.get("stage3b1_dir")
    if raw is None and isinstance(metrics.get("config", {}), dict):
        raw = dict(metrics.get("config", {})).get("stage3b1_dir")
    if raw is None or not str(raw):
        return Path(".")
    return Path(str(raw))


def _d4b_assignment_feature_weighting_artifact(weighting: dict[str, object], feature_names: list[str]) -> dict[str, object]:
    weights = np.asarray(weighting.get("feature_weights", np.ones(len(feature_names), dtype=np.float64)), dtype=np.float64)
    weighted_features = [
        {"feature": str(feature_names[idx]), "weight": float(weights[idx])}
        for idx in range(len(feature_names))
        if abs(float(weights[idx]) - 1.0) > 1.0e-12
    ]
    return {
        "schema": "scope_static_stage3d4b_assignment_feature_weighting_v1",
        "uses_mechanism_labels": False,
        "uses_visible_operation_context": True,
        "operation_context_weight": float(weighting.get("operation_context_weight", 1.0)),
        "operation_context_feature_count": int(weighting.get("operation_context_feature_count", 0)),
        "weighted_feature_count": int(len(weighted_features)),
        "weighted_features": weighted_features,
    }


def load_split_parent_map(path: str | Path, *, key: str, cluster_count: int) -> list[int] | None:
    source = Path(path)
    if not source.exists():
        return None
    data = _load_json(source)
    maps = data.get("maps")
    if not isinstance(maps, dict):
        return None
    values = maps.get(str(key))
    if not isinstance(values, list):
        return None
    if len(values) != int(cluster_count):
        return None
    return [int(value) for value in values]


def overcomplete_cluster_summary(
    x: np.ndarray,
    hard_assignments: np.ndarray,
    *,
    responsibilities: np.ndarray,
    feature_names: list[str],
    context_groups: np.ndarray | None = None,
    split_parent_map: list[int] | None = None,
) -> dict[str, object]:
    rows = []
    active = sorted(set(np.asarray(hard_assignments, dtype=np.int64).tolist()))
    residual = _context_residual_matrix(x, context_groups)
    for cluster in active:
        idx = np.asarray([row for row, value in enumerate(hard_assignments.tolist()) if int(value) == int(cluster)], dtype=np.int64)
        local = x[idx]
        mean = np.mean(local, axis=0) if idx.size else np.zeros(int(x.shape[1]), dtype=np.float64)
        residual_mean = np.mean(residual[idx], axis=0) if idx.size else np.zeros(int(x.shape[1]), dtype=np.float64)
        top = _top_feature_rows(mean, feature_names, limit=8)
        rows.append(
            {
                "cluster": f"C{int(cluster):03d}",
                "cluster_index": int(cluster),
                "split_parent": None
                if split_parent_map is None or int(cluster) >= len(split_parent_map)
                else int(split_parent_map[int(cluster)]),
                "support": int(idx.size),
                "support_fraction": float(idx.size) / float(max(1, int(x.shape[0]))),
                "assignment_mass": float(np.sum(responsibilities[:, int(cluster)])) if int(cluster) < int(responsibilities.shape[1]) else 0.0,
                "prototype_sha256": _vector_digest(mean),
                "top_visible_features_by_abs_mean": top,
                "context_residual_profile": [float(value) for value in residual_mean.tolist()],
                "context_residual_profile_sha256": _vector_digest(residual_mean),
                "context_residual_profile_l2_norm": float(np.linalg.norm(residual_mean)),
                "top_context_residual_features_by_abs_mean": _top_feature_rows(residual_mean, feature_names, limit=8),
            }
        )
    return {
        "schema": "scope_static_stage3d4b_overcomplete_cluster_summary_v1",
        "record_count": int(x.shape[0]),
        "feature_count": int(x.shape[1]) if x.ndim == 2 else 0,
        "active_cluster_count": int(len(rows)),
        "uses_context_normalized_residual_profiles": True,
        "uses_split_parent_map": split_parent_map is not None,
        "clusters": rows,
    }


def microcluster_merge_map(
    cluster_summary: dict[str, object],
    *,
    record_count: int,
    max_microcluster_support: int,
    max_microcluster_fraction: float,
    min_microcluster_family_count: int,
    context_residual_profile_veto_threshold: float | None = DEFAULT_CONTEXT_RESIDUAL_PROFILE_VETO_THRESHOLD,
) -> dict[str, object]:
    clusters = [dict(row) for row in cluster_summary.get("clusters", []) if isinstance(row, dict)]
    micro = [
        row
        for row in clusters
        if int(row.get("support", 0)) <= int(max_microcluster_support)
        and float(row.get("support_fraction", 0.0)) <= float(max_microcluster_fraction)
    ]
    micro_groups = _microcluster_residual_profile_groups(
        micro,
        threshold=context_residual_profile_veto_threshold,
    )
    mergeable_micro_groups = [group for group in micro_groups if len(group) >= int(min_microcluster_family_count)]
    unmerged_micro_clusters = [row for group in micro_groups if len(group) < int(min_microcluster_family_count) for row in group]
    split_parent_groups = _split_parent_residual_profile_groups(
        clusters,
        threshold=context_residual_profile_veto_threshold,
    )
    mergeable_split_parent_groups = [group for group in split_parent_groups if len(group) >= 2]
    split_parent_merged_clusters = {
        str(row["cluster"])
        for group in mergeable_split_parent_groups
        for row in group
    }
    merge_micro = bool(mergeable_micro_groups)
    merge_split_parent = bool(mergeable_split_parent_groups)
    macro = [
        row
        for row in clusters
        if row not in micro and str(row.get("cluster")) not in split_parent_merged_clusters
    ] + [
        row
        for row in unmerged_micro_clusters
        if str(row.get("cluster")) not in split_parent_merged_clusters
    ]
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
    for group_idx, group in enumerate(mergeable_split_parent_groups):
        family = f"F{len(family_rows):03d}"
        source_clusters = [str(row["cluster"]) for row in group]
        for cluster in source_clusters:
            cluster_to_family[cluster] = family
        family_rows.append(
            {
                "family": family,
                "merge_type": "split_parent_sibling_family",
                "source_clusters": source_clusters,
                "support": int(sum(int(row.get("support", 0)) for row in group)),
                "split_parent": int(group[0].get("split_parent")),
                "residual_profile_group": int(group_idx),
            }
        )
    for group_idx, group in enumerate(mergeable_micro_groups):
        group = [row for row in group if str(row.get("cluster")) not in split_parent_merged_clusters]
        if len(group) < int(min_microcluster_family_count):
            continue
        family = f"F{len(family_rows):03d}"
        source_clusters = [str(row["cluster"]) for row in group]
        for cluster in source_clusters:
            cluster_to_family[cluster] = family
        family_rows.append(
            {
                "family": family,
                "merge_type": "microcluster_tail_family",
                "source_clusters": source_clusters,
                "support": int(sum(int(row.get("support", 0)) for row in group)),
                "residual_profile_group": int(group_idx),
            }
        )
    veto = _residual_profile_veto_audit(micro_groups + split_parent_groups, threshold=context_residual_profile_veto_threshold)
    return {
        "schema": "scope_static_stage3d4b_microcluster_merge_map_v1",
        "strategy": "prune inactive clusters, merge context-residual-profile-compatible S3B1 split siblings, and merge only context-residual-profile-compatible microclusters",
        "uses_labels_for_merge_rule": False,
        "uses_channels_ptms_kraus": False,
        "uses_context_normalized_residual_profile_veto": True,
        "record_count": int(record_count),
        "active_cluster_count": int(len(clusters)),
        "postmerge_family_count": int(len(family_rows)),
        "microcluster_count": int(len(micro)),
        "microcluster_total_support": int(sum(int(row.get("support", 0)) for row in micro)),
        "microcluster_merge_applied": bool(merge_micro),
        "split_parent_merge_applied": bool(merge_split_parent),
        "split_parent_group_count": int(len(split_parent_groups)),
        "split_parent_merged_cluster_count": int(len(split_parent_merged_clusters)),
        "visible_merge_applied": bool(merge_micro or merge_split_parent),
        "microcluster_residual_profile_group_count": int(len(micro_groups)),
        "split_parent_residual_profile_group_count": int(len(split_parent_groups)),
        "microcluster_residual_profile_veto_applied": bool(veto.get("veto_applied", False)),
        "max_microcluster_support": int(max_microcluster_support),
        "max_microcluster_fraction": float(max_microcluster_fraction),
        "min_microcluster_family_count": int(min_microcluster_family_count),
        "context_residual_profile_veto_threshold": (
            None
            if context_residual_profile_veto_threshold is None
            else float(context_residual_profile_veto_threshold)
        ),
        "residual_profile_veto_audit": veto,
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
    context_residual_profile_veto_threshold: float | None,
) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3d4b_merge_prune_plan_v1",
        "input_assignment_key": str(overcomplete_assignment_key),
        "rule": "merge S3B1-seeded split siblings only when context-normalized residual profiles are compatible; active clusters with support <= max_microcluster_support and support_fraction <= max_microcluster_fraction are microclusters and may also merge when compatible",
        "max_microcluster_support": int(max_microcluster_support),
        "max_microcluster_fraction": float(max_microcluster_fraction),
        "min_microcluster_family_count": int(min_microcluster_family_count),
        "context_residual_profile_veto_threshold": (
            None
            if context_residual_profile_veto_threshold is None
            else float(context_residual_profile_veto_threshold)
        ),
        "uses_context_normalized_residual_profile_veto": True,
        "uses_stage3d4_split_parent_map_when_available": True,
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
        "microcluster_merge_applied": bool(merge_map.get("visible_merge_applied", False)),
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


def _microcluster_residual_profile_groups(
    microclusters: list[dict[str, object]],
    *,
    threshold: float | None,
) -> list[list[dict[str, object]]]:
    if not microclusters:
        return []
    if threshold is None or float(threshold) < 0.0:
        return [list(microclusters)]
    groups: list[list[dict[str, object]]] = []
    for row in microclusters:
        profile = _cluster_residual_profile(row)
        placed = False
        for group in groups:
            distances = [
                _normalized_residual_profile_distance(profile, _cluster_residual_profile(member))
                for member in group
            ]
            if not distances or max(distances) <= float(threshold):
                group.append(row)
                placed = True
                break
        if not placed:
            groups.append([row])
    return groups


def _split_parent_residual_profile_groups(
    clusters: list[dict[str, object]],
    *,
    threshold: float | None,
) -> list[list[dict[str, object]]]:
    by_parent: dict[int, list[dict[str, object]]] = {}
    for row in clusters:
        parent = row.get("split_parent")
        if parent is None:
            continue
        by_parent.setdefault(int(parent), []).append(row)
    groups: list[list[dict[str, object]]] = []
    for parent in sorted(by_parent):
        rows = by_parent[parent]
        if len(rows) < 2:
            continue
        groups.extend(_microcluster_residual_profile_groups(rows, threshold=threshold))
    return groups


def _residual_profile_veto_audit(
    groups: list[list[dict[str, object]]],
    *,
    threshold: float | None,
) -> dict[str, object]:
    pair_rows = []
    vetoed = 0
    for group_idx, group in enumerate(groups):
        for row in group:
            pair_rows.append(
                {
                    "cluster": str(row.get("cluster")),
                    "residual_profile_group": int(group_idx),
                    "support": int(row.get("support", 0)),
                    "context_residual_profile_l2_norm": float(row.get("context_residual_profile_l2_norm", 0.0) or 0.0),
                }
            )
    for left_idx, left_group in enumerate(groups):
        for right_idx, right_group in enumerate(groups):
            if right_idx <= left_idx:
                continue
            for left in left_group:
                for right in right_group:
                    distance = _normalized_residual_profile_distance(
                        _cluster_residual_profile(left),
                        _cluster_residual_profile(right),
                    )
                    if threshold is not None and distance > float(threshold):
                        vetoed += 1
    return {
        "schema": "scope_static_stage3d4b_residual_profile_veto_audit_v1",
        "description": "Visible-only non-merge veto: overcomplete components with distinct context-normalized residual profiles are not forced into one merged family.",
        "uses_mechanism_labels": False,
        "uses_oracle_location_or_strength": False,
        "uses_channels_ptms_kraus": False,
        "distance_metric": "rms_normalized_l2_over_context_residual_profile",
        "threshold": None if threshold is None else float(threshold),
        "group_count": int(len(groups)),
        "cluster_count": int(sum(len(group) for group in groups)),
        "vetoed_pair_count": int(vetoed),
        "veto_applied": bool(vetoed > 0),
        "clusters": pair_rows,
        "passed": True,
    }


def _cluster_residual_profile(row: dict[str, object]) -> np.ndarray:
    values = row.get("context_residual_profile", [])
    if not isinstance(values, list):
        return np.zeros(0, dtype=np.float64)
    return np.asarray([float(value) for value in values], dtype=np.float64)


def _normalized_residual_profile_distance(left: np.ndarray, right: np.ndarray) -> float:
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    if a.shape != b.shape or a.size == 0:
        return float(np.linalg.norm(a - b)) if a.shape == b.shape else float("inf")
    return float(np.linalg.norm(a - b) / np.sqrt(float(a.size)))


def _context_residual_matrix(matrix: np.ndarray, context_groups: np.ndarray | None) -> np.ndarray:
    arr = np.asarray(matrix, dtype=np.float64)
    groups = np.asarray([] if context_groups is None else context_groups, dtype=np.int64)
    if arr.ndim != 2:
        return np.zeros_like(arr, dtype=np.float64)
    if int(groups.shape[0]) != int(arr.shape[0]):
        return arr - np.mean(arr, axis=0, keepdims=True)
    out = np.zeros_like(arr, dtype=np.float64)
    for group in sorted(set(groups.tolist())):
        mask = groups == int(group)
        out[mask] = arr[mask] - np.mean(arr[mask], axis=0, keepdims=True)
    return out


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
        "residual_profile_veto_audit.json": result["merge_map"].get("residual_profile_veto_audit", {}),
        "postmerge_metrics.json": result["postmerge_metrics"],
        "raw_overcomplete_generation_metrics.json": result["raw_overcomplete_generation_metrics"],
        "postmerge_generation_metrics.json": result["postmerge_generation_metrics"],
        "global_null_metrics.json": result["global_null_metrics"],
        "mean_only_baseline_metrics.json": result["mean_only_baseline_metrics"],
        "leakage_audit.json": result["leakage_audit"],
        "acceptance_audit.json": result["acceptance_audit"],
        "claim_gate_audit.json": result["claim_gate_audit"],
        "heldout_protocol.json": result["heldout_protocol"],
        "feature_schema_match_audit.json": result["feature_schema_match_audit"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
        "assignment_feature_view_audit.json": result["assignment_feature_view_audit"],
        "assignment_feature_weighting.json": result["assignment_feature_weighting"],
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
    claim_gate = dict(result.get("claim_gate_audit", {}))
    return "\n".join(
        [
            "# Stage 3D.4b: Overcomplete Merge/Prune Audit",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Claim decision: `{result.get('claim_decision')}`",
            f"- Claim gate passed: `{str(bool(claim_gate.get('passed', False))).lower()}`",
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
