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
from .artifacts import mechanism_sort_key as _mechanism_sort_key
from .artifacts import resolve_teacher_dir
from .observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from .protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR
from .baselines import VARIANCE_FLOOR
from .baselines import _diag_log_prob
from .baselines import _logsumexp
from .baselines import evaluate_cluster_assignments
from .baselines import k_selection_runs


STAGE_NAME = "Stage3B1_first_discovery_model"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/PHYC_STAGE3_discovery/S3B1_first_discovery_model"
DEFAULT_MAX_ITER = 50
DEFAULT_SEED = 0
DEFAULT_INITIAL_TEMPERATURE = 1.5
DEFAULT_FINAL_TEMPERATURE = 0.75
DEFAULT_COMPLEXITY_PENALTY = 0.01
DEFAULT_MAX_CV_FOLDS = 5
DEFAULT_CONTEXT_BALANCE_PENALTY = 100_000.0
DEFAULT_OPERATION_CONTEXT_WEIGHT = 2.0
MIN_COMPONENT_MASS = 1.0e-8
CONTEXT_DEPENDENT_MECHANISM_IDS = ("M13",)


def run_stage3b1_first_discovery_model(
    *,
    stage3a_dir: str | Path = DEFAULT_STAGE3A_DIR,
    stage3a5_dir: str | Path = DEFAULT_STAGE3A5_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    teacher_dir: str | Path | None = None,
    seed: int = DEFAULT_SEED,
    max_iter: int = DEFAULT_MAX_ITER,
    initial_temperature: float = DEFAULT_INITIAL_TEMPERATURE,
    final_temperature: float = DEFAULT_FINAL_TEMPERATURE,
    complexity_penalty: float = DEFAULT_COMPLEXITY_PENALTY,
    max_cv_folds: int | None = DEFAULT_MAX_CV_FOLDS,
    context_balance_penalty: float = DEFAULT_CONTEXT_BALANCE_PENALTY,
    operation_context_weight: float = DEFAULT_OPERATION_CONTEXT_WEIGHT,
) -> dict[str, object]:
    """Train the first visible-only Stage 3 discovery model.

    The learner path receives only the Stage 3A approved visible feature table.
    Mechanism and quotient labels are used after fitting for evaluator-only
    metrics, never for fitting or model selection.
    """

    s3a = Path(stage3a_dir)
    s3a5 = Path(stage3a5_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    s3a_metrics = _load_json(s3a / "metrics.json")
    s3a5_metrics = _load_json(s3a5 / "metrics.json")
    teacher = resolve_teacher_dir(s3a_metrics, teacher_dir)

    x_raw, feature_names, feature_matrix = load_stage3a_frozen_visible_features(s3a)
    x, standardization = _standardize_visible_features_with_values(x_raw)
    x, feature_weighting = _apply_visible_feature_weights(
        x,
        feature_names=feature_names,
        operation_context_weight=float(operation_context_weight),
    )
    standardization["feature_weight"] = feature_weighting["feature_weights"]
    alias = dict(s3a5_metrics.get("oracle_alias_classes", {})) if isinstance(s3a5_metrics.get("oracle_alias_classes", {}), dict) else {}
    label_to_quotient = {str(k): str(v) for k, v in dict(alias.get("label_to_quotient", {})).items()}
    mechanism_scope = dict(s3a_metrics.get("mechanism_scope", {})) if isinstance(s3a_metrics.get("mechanism_scope", {}), dict) else {}
    class_count = int(mechanism_scope.get("class_count_evaluator_only", max(1, x_raw.shape[0])))
    quotient_class_count = int(alias.get("quotient_class_count", class_count))
    feature_match = _feature_schema_matches_s3a(s3a, feature_names)
    split_manifest = dict(s3a_metrics.get("split_manifest", {})) if isinstance(s3a_metrics.get("split_manifest", {}), dict) else {}
    context_groups = _context_groups_from_split_manifest(split_manifest, record_count=int(x_raw.shape[0]))
    all_folds = _valid_folds(split_manifest, record_count=int(x_raw.shape[0]))
    folds = _cap_folds(all_folds, max_cv_folds=max_cv_folds)
    k_runs = k_selection_runs(
        record_count=int(x_raw.shape[0]),
        class_count=class_count,
        quotient_class_count=quotient_class_count,
    )
    candidate_results = _evaluate_candidates(
        x,
        context_groups=context_groups,
        folds=folds,
        k_runs=k_runs,
        seed=int(seed),
        max_iter=int(max_iter),
        initial_temperature=float(initial_temperature),
        final_temperature=float(final_temperature),
        complexity_penalty=float(complexity_penalty),
        context_balance_penalty=float(context_balance_penalty),
    )
    selected = _select_candidate(candidate_results)
    selected_k = int(selected.get("k", 1)) if selected else 1
    selected_family = str(selected.get("model_family", "diagonal_covariance_visible_prototype_mixture")) if selected else "diagonal_covariance_visible_prototype_mixture"
    final_model = _fit_candidate_model(
        x,
        context_groups=context_groups,
        model_family=selected_family,
        k=selected_k,
        seed=int(seed),
        max_iter=int(max_iter),
        initial_temperature=float(initial_temperature),
        final_temperature=float(final_temperature),
    )
    responsibilities = _model_responsibilities(
        x,
        context_groups=context_groups,
        model=final_model,
        temperature=float(final_temperature),
    )
    hard_assignments = np.argmax(responsibilities, axis=1).astype(np.int64) if responsibilities.size else np.zeros(0, dtype=np.int64)
    evaluator = load_stage3_evaluator_labels(s3a, teacher)
    labels = evaluator.exact_labels
    if len(labels) != int(x_raw.shape[0]):
        raise ValueError(f"Stage 3A frozen feature row count {x_raw.shape[0]} does not match evaluator label count {len(labels)}")
    class_names = evaluator.exact_class_names
    quotient_labels = [label_to_quotient.get(label, label) for label in labels]
    quotient_class_names = sorted(set(quotient_labels), key=_mechanism_sort_key)
    evaluator_metrics = evaluate_cluster_assignments(
        hard_assignments,
        exact_labels=labels,
        exact_class_names=class_names,
        quotient_labels=quotient_labels,
        quotient_class_names=quotient_class_names,
    )
    context_dependent = context_dependent_mechanism_diagnostics(
        hard_assignments,
        records=evaluator.records,
        cluster_to_label_match=dict(evaluator_metrics["exact_label_metrics"].get("cluster_to_label_match", {})),
    )
    learned_summary = learned_assignment_summary(
        selected=selected,
        responsibilities=responsibilities,
        hard_assignments=hard_assignments,
        split_manifest=split_manifest,
    )
    prototypes = learned_prototypes_artifact(
        final_model,
        feature_names=feature_names,
        standardization=standardization,
    )
    generation_metrics = prototype_generation_metrics(
        x,
        final_model=final_model,
        folds=folds,
        selected_candidate=selected,
        candidate_results=candidate_results,
    )
    model_selection = model_selection_audit(selected, candidate_results)
    hardening = assignment_hardening_audit(
        responsibilities,
        model=final_model,
        initial_temperature=float(initial_temperature),
        final_temperature=float(final_temperature),
    )
    label_permutation = label_permutation_audit(evaluator_metrics)
    quotient_metrics = {
        "schema": "scope_static_stage3b1_quotient_metrics_v1",
        "quotient_class_count": int(len(quotient_class_names)),
        "selected_model_quotient_metrics": evaluator_metrics["quotient_label_metrics"],
        "exact_recovery_required": bool(dict(s3a5_metrics.get("oracle_alias_classes", {})).get("exact_label_recovery_claim_allowed", False)),
    }
    evaluator_only = {
        "schema": "scope_static_stage3b1_evaluator_only_label_metrics_v1",
        "selected_model_exact_metrics": evaluator_metrics["exact_label_metrics"],
        "selected_model_quotient_metrics": evaluator_metrics["quotient_label_metrics"],
        "context_dependent_mechanism_diagnostics": context_dependent,
        "active_cluster_count": evaluator_metrics["active_cluster_count"],
        "assignment_entropy": evaluator_metrics["assignment_entropy"],
    }
    acceptance = stage3b1_acceptance_audit(
        s3a_metrics=s3a_metrics,
        s3a5_metrics=s3a5_metrics,
        feature_match=feature_match,
        feature_matrix=feature_matrix,
        selected=selected,
        responsibilities=responsibilities,
        prototypes=prototypes,
        model_selection=model_selection,
        evaluated_folds=folds,
        hardening=hardening,
        label_permutation=label_permutation,
        evaluator_metrics=evaluator_metrics,
    )
    result = {
        "schema": "scope_static_stage3b1_first_discovery_model_v1",
        "stage": STAGE_NAME,
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="first_discovery_model"),
        "stage3a_dir": str(s3a),
        "stage3a5_dir": str(s3a5),
        "teacher_dir": str(teacher),
        "output_dir": str(output),
        "claim_boundary": {
            "trains_supervised_classifier": False,
            "uses_mechanism_labels_for_fit": False,
            "uses_mechanism_labels_for_model_selection": False,
            "trains_from_stage3a_frozen_visible_features": True,
            "rebuilds_visible_features_from_oracle_records_for_fit": False,
            "uses_visible_validation_objective_for_model_selection": True,
            "evaluator_only_metrics_after_fit": True,
            "discovers_cptp_gksl_channels": False,
        },
        "config": {
            "stage3a_dir": str(s3a),
            "stage3a5_dir": str(s3a5),
            "teacher_dir": str(teacher),
            "output_dir": str(output),
            "seed": int(seed),
            "max_iter": int(max_iter),
            "initial_temperature": float(initial_temperature),
            "final_temperature": float(final_temperature),
            "complexity_penalty": float(complexity_penalty),
            "max_cv_folds": None if max_cv_folds is None else int(max_cv_folds),
            "context_balance_penalty": float(context_balance_penalty),
            "operation_context_weight": float(operation_context_weight),
        },
        "visible_feature_matrix": feature_matrix,
        "visible_feature_standardization": _standardization_summary(standardization),
        "visible_feature_weighting": _feature_weighting_summary(feature_weighting, feature_names),
        "feature_schema_match_audit": feature_match,
        "k_selection_protocol": {
            "schema": "scope_static_stage3b1_k_selection_protocol_v1",
            "runs": k_runs,
            "selected_k_mode": None if selected is None else selected.get("k_mode"),
            "selected_k": None if selected is None else selected.get("k"),
            "uses_catalog_cardinality_only_not_labels": True,
            "uses_quotient_count_from_stage3a5": True,
        },
        "candidate_selection": {
            "schema": "scope_static_stage3b1_candidate_selection_v1",
            "selection_rule": "minimum validation visible NLL plus visible-only complexity and context-balance penalties",
            "cross_validation_protocol": cross_validation_protocol(
                all_folds=all_folds,
                evaluated_folds=folds,
                max_cv_folds=max_cv_folds,
            ),
            "candidate_results": candidate_results,
            "selected": selected,
        },
        "learned_assignment_summary": learned_summary,
        "learned_prototypes": prototypes,
        "prototype_generation_metrics": generation_metrics,
        "assignment_hardening_audit": hardening,
        "label_permutation_audit": label_permutation,
        "model_selection_audit": model_selection,
        "evaluator_only_label_metrics": evaluator_only,
        "context_dependent_mechanism_diagnostics": context_dependent,
        "quotient_metrics": quotient_metrics,
        "acceptance_audit": acceptance,
        "decision": "stage3b1_first_discovery_model_completed" if acceptance["passed"] else "stage3b1_first_discovery_model_failed",
    }
    _write_outputs(output, result, responsibilities, final_model)
    return result


def learned_assignment_summary(
    *,
    selected: dict[str, object] | None,
    responsibilities: np.ndarray,
    hard_assignments: np.ndarray,
    split_manifest: dict[str, object],
) -> dict[str, object]:
    masses = np.sum(responsibilities, axis=0) if responsibilities.size else np.zeros(0, dtype=np.float64)
    active = int(np.sum(masses > MIN_COMPONENT_MASS))
    return {
        "schema": "scope_static_stage3b1_learned_assignment_summary_v1",
        "source": "Stage 3B.1 visible-only prototype mixture discovery model",
        "assignment_symbol": "Pi[j,k]",
        "assignment_unit": str(split_manifest.get("assignment_unit", "mechanism_condition_instance")),
        "selected_k_mode": None if selected is None else selected.get("k_mode"),
        "selected_k": None if selected is None else selected.get("k"),
        "assignment_matrix_shape": [int(responsibilities.shape[0]), int(responsibilities.shape[1])],
        "row_stochastic": bool(responsibilities.size == 0 or np.allclose(np.sum(responsibilities, axis=1), 1.0)),
        "active_prototype_count": active,
        "hard_cluster_masses": {f"C{idx:03d}": int(np.sum(hard_assignments == idx)) for idx in sorted(set(hard_assignments.tolist()))},
        "compressed_claim_allowed": False,
    }


def learned_prototypes_artifact(
    model: dict[str, np.ndarray | list[dict[str, float]]],
    *,
    feature_names: list[str],
    standardization: dict[str, np.ndarray],
) -> dict[str, object]:
    means = np.asarray(model["means"], dtype=np.float64)
    variances = np.asarray(model["variances"], dtype=np.float64)
    weights = np.asarray(model["weights"], dtype=np.float64)
    feature_weight = np.asarray(standardization.get("feature_weight", np.ones(means.shape[1], dtype=np.float64)), dtype=np.float64)
    feature_weight = np.where(np.abs(feature_weight) > 1.0e-12, feature_weight, 1.0)
    unweighted_means = means / feature_weight[None, :]
    unweighted_variances = variances / (feature_weight[None, :] * feature_weight[None, :])
    raw_mean = unweighted_means * standardization["scale"][None, :] + standardization["mean"][None, :]
    raw_variance = unweighted_variances * standardization["scale"][None, :] * standardization["scale"][None, :]
    prototypes = []
    for idx in range(means.shape[0]):
        prototypes.append(
            {
                "prototype_index": int(idx),
                "weight": float(weights[idx]),
                "standardized_mean": {feature_names[col]: float(means[idx, col]) for col in range(len(feature_names))},
                "standardized_variance": {feature_names[col]: float(variances[idx, col]) for col in range(len(feature_names))},
                "visible_mean": {feature_names[col]: float(raw_mean[idx, col]) for col in range(len(feature_names))},
                "visible_variance": {feature_names[col]: float(raw_variance[idx, col]) for col in range(len(feature_names))},
            }
        )
    return {
        "schema": "scope_static_stage3b1_learned_prototypes_v1",
        "model_family": str(model.get("model_family", "diagonal_covariance_visible_prototype_mixture")),
        "feature_names": [str(name) for name in feature_names],
        "prototype_count": int(means.shape[0]),
        "prototypes": prototypes,
    }


def prototype_generation_metrics(
    x: np.ndarray,
    *,
    final_model: dict[str, np.ndarray | list[dict[str, float]]],
    folds: list[dict[str, list[int]]],
    selected_candidate: dict[str, object] | None,
    candidate_results: list[dict[str, object]],
) -> dict[str, object]:
    selected_key = None if selected_candidate is None else _candidate_key(selected_candidate)
    selected_cv = [row for row in candidate_results if selected_key is not None and _candidate_key(row) == selected_key]
    return {
        "schema": "scope_static_stage3b1_prototype_generation_metrics_v1",
        "final_all_visible_nll": float(_mixture_nll(x, final_model)),
        "final_all_soft_reconstruction_loss": float(_soft_reconstruction_loss(x, final_model)),
        "heldout_protocol": "grouped Stage 3A folds; validation visible NLL selected the model, test visible NLL is reported only",
        "selected_candidate_cross_validation": selected_cv[0] if selected_cv else None,
        "fold_count": int(len(folds)),
    }


def model_selection_audit(selected: dict[str, object] | None, candidates: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3b1_model_selection_audit_v1",
        "accepted_discovery_model_selected": selected is not None,
        "candidate_count": int(len(candidates)),
        "selected_k_mode": None if selected is None else selected.get("k_mode"),
        "selected_k": None if selected is None else selected.get("k"),
        "selection_score": None if selected is None else selected.get("selection_score"),
        "validation_visible_nll_used_for_selection": True,
        "validation_folds_selected_without_labels": True,
        "validation_reconstruction_loss_used_for_tie_break": True,
        "assignment_entropy_used_for_regularization": False,
        "context_balance_penalty_used_for_selection": True,
        "context_balance_uses_labels": False,
        "validation_ari_used_for_selection": False,
        "validation_nmi_used_for_selection": False,
        "validation_ba_used_for_selection": False,
        "validation_min_recall_used_for_selection": False,
        "test_ari_used_for_selection": False,
        "test_nmi_used_for_selection": False,
        "test_ba_used_for_selection": False,
        "test_min_recall_used_for_selection": False,
        "oracle_label_prototype_quality_used_for_selection": False,
    }


def assignment_hardening_audit(
    responsibilities: np.ndarray,
    *,
    model: dict[str, np.ndarray | list[dict[str, float]]],
    initial_temperature: float,
    final_temperature: float,
) -> dict[str, object]:
    entropy = _assignment_entropy(responsibilities)
    return {
        "schema": "scope_static_stage3b1_assignment_hardening_audit_v1",
        "hardening_method": str(model.get("assignment_method", "annealed softmax responsibilities over diagonal Gaussian prototype likelihoods")),
        "initial_temperature": float(initial_temperature),
        "final_temperature": float(final_temperature),
        "uses_mechanism_labels_in_hardening": False,
        "uses_quotient_labels_in_hardening": False,
        "quotient_awareness": "K protocol and evaluator target honor Stage 3A.5 alias classes; learner loss remains visible-only.",
        "context_groups_used": bool(model.get("uses_context_groups", False)),
        "context_group_labels_used": False,
        "row_stochastic": bool(responsibilities.size == 0 or np.allclose(np.sum(responsibilities, axis=1), 1.0)),
        "mean_assignment_entropy": float(entropy),
        "training_history_tail": list(model.get("history", []))[-5:],
    }


def label_permutation_audit(evaluator_metrics: dict[str, object]) -> dict[str, object]:
    exact = dict(evaluator_metrics.get("exact_label_metrics", {}))
    quotient = dict(evaluator_metrics.get("quotient_label_metrics", {}))
    return {
        "schema": "scope_static_stage3b1_label_permutation_audit_v1",
        "cluster_label_matching_used_only_for_reporting": True,
        "exact_cluster_to_label_match": exact.get("cluster_to_label_match", {}),
        "quotient_cluster_to_label_match": quotient.get("cluster_to_label_match", {}),
        "label_permutation_handled": True,
    }


def context_dependent_mechanism_diagnostics(
    hard_assignments: np.ndarray,
    *,
    records: list[dict[str, object]],
    cluster_to_label_match: dict[str, object],
) -> dict[str, object]:
    """Evaluator-only split-vs-confusion report for declared drift mechanisms.

    Exact label matching permits only one cluster to be credited for a label.
    That is the right strict metric, but it can understate a drift-family result
    when the learner splits one context-dependent mechanism into pure submodes.
    """

    labels = [str(record.get("oracle_label", record.get("mechanism_id", ""))) for record in records]
    clusters = [f"C{int(value):03d}" for value in np.asarray(hard_assignments, dtype=np.int64).tolist()]
    cluster_totals: dict[str, int] = {}
    for cluster in clusters:
        cluster_totals[cluster] = cluster_totals.get(cluster, 0) + 1
    diagnostics = {}
    for mechanism_id in CONTEXT_DEPENDENT_MECHANISM_IDS:
        indices = [
            idx
            for idx, record in enumerate(records)
            if str(record.get("mechanism_id", record.get("oracle_label", ""))) == mechanism_id
            or str(record.get("oracle_label", "")) == mechanism_id
        ]
        if not indices:
            diagnostics[mechanism_id] = {
                "present": False,
                "schema": "scope_static_stage3b1_context_dependent_mechanism_v1",
            }
            continue
        target_label = mechanism_id if mechanism_id in set(labels) else labels[indices[0]]
        cluster_rows = []
        matched_count = 0
        pure_count = 0
        mixed_count = 0
        for cluster in sorted({clusters[idx] for idx in indices}):
            local_indices = [idx for idx in indices if clusters[idx] == cluster]
            mechanism_count = len(local_indices)
            total_count = int(cluster_totals.get(cluster, 0))
            mapped_label = cluster_to_label_match.get(cluster)
            purity = float(mechanism_count) / float(total_count) if total_count else 0.0
            epsilons = _finite_parameter_values([records[idx] for idx in local_indices], "epsilon")
            circuit_ids = sorted(
                {
                    int(records[idx]["circuit_id"])
                    for idx in local_indices
                    if records[idx].get("circuit_id") is not None
                }
            )
            if mapped_label == target_label:
                matched_count += mechanism_count
            if total_count == mechanism_count:
                pure_count += mechanism_count
            else:
                mixed_count += mechanism_count
            cluster_rows.append(
                {
                    "cluster": cluster,
                    "mechanism_count": int(mechanism_count),
                    "cluster_total_count": int(total_count),
                    "purity": purity,
                    "mapped_label": None if mapped_label is None else str(mapped_label),
                    "credited_by_exact_label_matching": mapped_label == target_label,
                    "pure_context_submode": total_count == mechanism_count,
                    "epsilon_min": None if not epsilons else float(min(epsilons)),
                    "epsilon_max": None if not epsilons else float(max(epsilons)),
                    "circuit_ids": circuit_ids,
                }
            )
        support = int(len(indices))
        exact_recall = float(matched_count) / float(support) if support else 0.0
        pure_submode_recall = float(pure_count) / float(support) if support else 0.0
        epsilon_values = _finite_parameter_values([records[idx] for idx in indices], "epsilon")
        if pure_submode_recall >= 1.0 - 1.0e-12 and exact_recall < 1.0:
            interpretation = "split_into_pure_context_submodes_not_cross_mechanism_confusion"
        elif mixed_count > 0:
            interpretation = "mixed_with_other_mechanisms"
        else:
            interpretation = "single_or_matched_context_family"
        diagnostics[mechanism_id] = {
            "schema": "scope_static_stage3b1_context_dependent_mechanism_v1",
            "present": True,
            "mechanism_id": mechanism_id,
            "target_exact_label": target_label,
            "support": support,
            "exact_label_matched_count": int(matched_count),
            "exact_label_recall_after_one_cluster_matching": exact_recall,
            "pure_context_submode_count": int(sum(1 for row in cluster_rows if bool(row["pure_context_submode"]))),
            "pure_context_submode_recall": pure_submode_recall,
            "mixed_cluster_count": int(sum(1 for row in cluster_rows if not bool(row["pure_context_submode"]))),
            "mixed_cluster_row_count": int(mixed_count),
            "assigned_cluster_count": int(len(cluster_rows)),
            "family_recovered_as_pure_submodes": bool(pure_submode_recall >= 1.0 - 1.0e-12 and mixed_count == 0),
            "epsilon_min": None if not epsilon_values else float(min(epsilon_values)),
            "epsilon_max": None if not epsilon_values else float(max(epsilon_values)),
            "epsilon_unique_count": int(len(set(epsilon_values))),
            "cluster_rows": cluster_rows,
            "interpretation": interpretation,
        }
    return {
        "schema": "scope_static_stage3b1_context_dependent_mechanism_diagnostics_v1",
        "evaluator_only": True,
        "used_for_fit": False,
        "used_for_model_selection": False,
        "diagnostics": diagnostics,
    }


def _finite_parameter_values(records: list[dict[str, object]], name: str) -> list[float]:
    values = []
    for record in records:
        parameters = record.get("parameters", {})
        if not isinstance(parameters, dict) or name not in parameters:
            continue
        value = parameters[name]
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if np.isfinite(number):
            values.append(number)
    return values


def cross_validation_protocol(
    *,
    all_folds: list[dict[str, list[int]]],
    evaluated_folds: list[dict[str, list[int]]],
    max_cv_folds: int | None,
) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3b1_cross_validation_protocol_v1",
        "available_fold_count": int(len(all_folds)),
        "evaluated_fold_count": int(len(evaluated_folds)),
        "max_cv_folds": None if max_cv_folds is None else int(max_cv_folds),
        "fold_selection_rule": "first max_cv_folds folds from the Stage 3A split manifest; no labels or evaluator metrics are used",
        "uses_labels_for_fold_selection": False,
        "evaluated_fold_indices": [int(idx) for idx in range(len(evaluated_folds))],
    }


def stage3b1_acceptance_audit(
    *,
    s3a_metrics: dict[str, object],
    s3a5_metrics: dict[str, object],
    feature_match: dict[str, object],
    feature_matrix: dict[str, object],
    selected: dict[str, object] | None,
    responsibilities: np.ndarray,
    prototypes: dict[str, object],
    model_selection: dict[str, object],
    evaluated_folds: list[dict[str, list[int]]],
    hardening: dict[str, object],
    label_permutation: dict[str, object],
    evaluator_metrics: dict[str, object],
) -> dict[str, object]:
    checks = {
        "stage3a_acceptance_passed": bool(dict(s3a_metrics.get("acceptance_audit", {})).get("passed", False)),
        "stage3a5_acceptance_passed": bool(dict(s3a5_metrics.get("acceptance_audit", {})).get("passed", False)),
        "approved_feature_schema_matches_stage3a": bool(feature_match.get("passed", False)),
        "uses_stage3a_frozen_visible_features_for_fit": bool(feature_matrix.get("loaded_from_stage3a_artifact", False)),
        "selected_model_exists": selected is not None,
        "selected_model_chosen_by_visible_validation_objective": bool(model_selection.get("validation_visible_nll_used_for_selection", False)),
        "cross_validation_fold_count_positive": bool(evaluated_folds),
        "validation_fold_selection_uses_no_labels": bool(model_selection.get("validation_folds_selected_without_labels", False)),
        "validation_label_model_selection_count_is_zero": not bool(model_selection.get("validation_ari_used_for_selection", True)),
        "test_label_model_selection_count_is_zero": not bool(model_selection.get("test_ari_used_for_selection", True)),
        "oracle_label_prototype_quality_not_used_for_selection": not bool(model_selection.get("oracle_label_prototype_quality_used_for_selection", True)),
        "assignment_matrix_row_stochastic": bool(responsibilities.size == 0 or np.allclose(np.sum(responsibilities, axis=1), 1.0)),
        "learned_prototypes_written": int(prototypes.get("prototype_count", 0)) > 0,
        "learned_covariance_written": all("standardized_variance" in row for row in prototypes.get("prototypes", []) if isinstance(row, dict)),
        "assignment_hardening_used_no_labels": not bool(hardening.get("uses_mechanism_labels_in_hardening", True)),
        "label_permutation_reporting_only": bool(label_permutation.get("cluster_label_matching_used_only_for_reporting", False)),
        "evaluator_metrics_reported_after_fit": "exact_label_metrics" in evaluator_metrics and "quotient_label_metrics" in evaluator_metrics,
        "does_not_claim_arbitrary_cptp_gksl_learning": True,
    }
    return {
        "schema": "scope_static_stage3b1_acceptance_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
    }


def _evaluate_candidates(
    x: np.ndarray,
    *,
    context_groups: np.ndarray,
    folds: list[dict[str, list[int]]],
    k_runs: list[dict[str, object]],
    seed: int,
    max_iter: int,
    initial_temperature: float,
    final_temperature: float,
    complexity_penalty: float,
    context_balance_penalty: float,
) -> list[dict[str, object]]:
    results = []
    candidate_specs: list[tuple[dict[str, object], str]] = []
    for run in k_runs:
        candidate_specs.append((run, "diagonal_covariance_visible_prototype_mixture"))
        if _context_balance_supported(context_groups, int(run["k"])):
            candidate_specs.append((run, "context_balanced_visible_prototype_mixture"))
    for order, (run, model_family) in enumerate(candidate_specs):
        k = int(run["k"])
        fold_rows = []
        for fold_idx, fold in enumerate(folds or [{"train_indices": list(range(x.shape[0])), "validation_indices": list(range(x.shape[0])), "test_indices": []}]):
            train_idx = np.asarray(fold.get("train_indices", []), dtype=np.int64)
            val_idx = np.asarray(fold.get("validation_indices", []), dtype=np.int64)
            test_idx = np.asarray(fold.get("test_indices", []), dtype=np.int64)
            if train_idx.size == 0:
                train_idx = np.arange(x.shape[0], dtype=np.int64)
            if val_idx.size == 0:
                val_idx = train_idx
            model = _fit_candidate_model(
                x[train_idx],
                context_groups=context_groups[train_idx],
                model_family=model_family,
                k=k,
                seed=int(seed + 101 * order + fold_idx),
                max_iter=int(max_iter),
                initial_temperature=float(initial_temperature),
                final_temperature=float(final_temperature),
            )
            val_nll = float(_mixture_nll(x[val_idx], model))
            val_resp = _model_responsibilities(
                x[val_idx],
                context_groups=context_groups[val_idx],
                model=model,
                temperature=float(final_temperature),
            )
            val_recon = float(_responsibility_reconstruction_loss(x[val_idx], model, val_resp))
            test_nll = float(_mixture_nll(x[test_idx], model)) if test_idx.size else None
            val_context_violations = context_balance_violation_count(val_resp, context_groups[val_idx], expected_k=int(np.asarray(model["means"]).shape[0]))
            fold_rows.append(
                {
                    "fold": int(fold_idx),
                    "model_family": str(model_family),
                    "effective_k": int(np.asarray(model["means"]).shape[0]),
                    "train_count": int(train_idx.size),
                    "validation_count": int(val_idx.size),
                    "test_count": int(test_idx.size),
                    "validation_visible_nll": val_nll,
                    "validation_soft_reconstruction_loss": val_recon,
                    "validation_context_balance_violation_count": int(val_context_violations),
                    "test_visible_nll_report_only": test_nll,
                    "active_prototype_count": int(np.sum(np.asarray(model["weights"], dtype=np.float64) > MIN_COMPONENT_MASS)),
                }
            )
        validation_nll = _mean_finite([row["validation_visible_nll"] for row in fold_rows])
        validation_recon = _mean_finite([row["validation_soft_reconstruction_loss"] for row in fold_rows])
        test_nll = _mean_finite([row["test_visible_nll_report_only"] for row in fold_rows if row["test_visible_nll_report_only"] is not None])
        effective_k = int(max(row["effective_k"] for row in fold_rows)) if fold_rows else max(1, k)
        validation_count = int(sum(row["validation_count"] for row in fold_rows))
        context_balance_violations = int(sum(row["validation_context_balance_violation_count"] for row in fold_rows))
        feature_count = int(x.shape[1]) if x.ndim == 2 else 0
        parameter_count = int(effective_k * feature_count * 2 + max(0, effective_k - 1))
        penalty = float(complexity_penalty) * float(parameter_count) * np.log(float(max(2, validation_count))) / float(max(1, validation_count))
        context_penalty = float(context_balance_penalty) * float(context_balance_violations)
        selection_score = float(validation_nll + penalty + context_penalty)
        results.append(
            {
                "candidate_index": int(order),
                "model_family": str(model_family),
                "k_mode": str(run["mode"]),
                "k": int(k),
                "effective_k": int(effective_k),
                "validation_visible_nll": validation_nll,
                "validation_soft_reconstruction_loss": validation_recon,
                "validation_context_balance_violation_count": int(context_balance_violations),
                "test_visible_nll_report_only": test_nll,
                "visible_complexity_penalty": penalty,
                "visible_context_balance_penalty": context_penalty,
                "selection_score": selection_score,
                "fold_metrics": fold_rows,
                "uses_labels_for_fit": False,
                "uses_labels_for_model_selection": False,
                "uses_context_groups_for_fit": bool(model_family == "context_balanced_visible_prototype_mixture"),
                "uses_context_labels_for_fit": False,
            }
        )
    return results


def _select_candidate(candidates: list[dict[str, object]]) -> dict[str, object] | None:
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda row: (
            float(row.get("selection_score", np.inf)),
            float(row.get("validation_soft_reconstruction_loss", np.inf)),
            int(row.get("candidate_index", 0)),
        ),
    )


def _fit_candidate_model(
    x: np.ndarray,
    *,
    context_groups: np.ndarray,
    model_family: str,
    k: int,
    seed: int,
    max_iter: int,
    initial_temperature: float,
    final_temperature: float,
) -> dict[str, np.ndarray | list[dict[str, float]] | str | bool]:
    if str(model_family) == "context_balanced_visible_prototype_mixture" and _context_balance_supported(context_groups, int(k)):
        return _fit_context_balanced_prototype_mixture(
            x,
            context_groups=context_groups,
            k=k,
            seed=seed,
            max_iter=max_iter,
        )
    return _fit_prototype_mixture(
        x,
        k=k,
        seed=seed,
        max_iter=max_iter,
        initial_temperature=initial_temperature,
        final_temperature=final_temperature,
    )


def _fit_prototype_mixture(
    x: np.ndarray,
    *,
    k: int,
    seed: int,
    max_iter: int,
    initial_temperature: float,
    final_temperature: float,
) -> dict[str, np.ndarray | list[dict[str, float]]]:
    n, d = x.shape
    active_k = max(1, min(int(k), max(1, n)))
    if n == 0:
        return {
            "means": np.zeros((active_k, d), dtype=np.float64),
            "variances": np.ones((active_k, d), dtype=np.float64),
            "weights": np.full(active_k, 1.0 / float(active_k), dtype=np.float64),
            "history": [],
            "model_family": "diagonal_covariance_visible_prototype_mixture",
            "assignment_method": "annealed softmax responsibilities over diagonal Gaussian prototype likelihoods",
            "uses_context_groups": False,
        }
    means = _seeded_farthest_first_centers(x, active_k, seed=int(seed))
    global_var = np.maximum(np.var(x, axis=0), VARIANCE_FLOOR)
    variances = np.tile(global_var[None, :], (active_k, 1))
    weights = np.full(active_k, 1.0 / float(active_k), dtype=np.float64)
    history: list[dict[str, float]] = []
    iterations = max(1, int(max_iter))
    for step in range(iterations):
        temperature = _annealed_temperature(
            step,
            total=iterations,
            initial_temperature=float(initial_temperature),
            final_temperature=float(final_temperature),
        )
        model = {"means": means, "variances": variances, "weights": weights, "history": history}
        responsibilities = _posterior_responsibilities(x, model, temperature=temperature)
        nk = np.maximum(np.sum(responsibilities, axis=0), MIN_COMPONENT_MASS)
        weights = nk / float(n)
        means = (responsibilities.T @ x) / nk[:, None]
        for idx in range(active_k):
            diff = x - means[idx]
            variances[idx] = np.maximum((responsibilities[:, idx][:, None] * diff * diff).sum(axis=0) / nk[idx], VARIANCE_FLOOR)
        if step == 0 or step == iterations - 1 or (step + 1) % max(1, iterations // 5) == 0:
            model = {"means": means, "variances": variances, "weights": weights, "history": history}
            history.append(
                {
                    "iteration": float(step + 1),
                    "temperature": float(temperature),
                    "visible_nll": float(_mixture_nll(x, model)),
                    "soft_reconstruction_loss": float(_soft_reconstruction_loss(x, model)),
                    "mean_assignment_entropy": float(_assignment_entropy(responsibilities)),
                    "active_prototype_count": float(np.sum(weights > MIN_COMPONENT_MASS)),
                }
            )
    return {
        "means": means,
        "variances": variances,
        "weights": weights,
        "history": history,
        "model_family": "diagonal_covariance_visible_prototype_mixture",
        "assignment_method": "annealed softmax responsibilities over diagonal Gaussian prototype likelihoods",
        "uses_context_groups": False,
    }


def _fit_context_balanced_prototype_mixture(
    x: np.ndarray,
    *,
    context_groups: np.ndarray,
    k: int,
    seed: int,
    max_iter: int,
) -> dict[str, np.ndarray | list[dict[str, float]] | str | bool]:
    n, d = x.shape
    active_k = max(1, min(int(k), max(1, n)))
    if n == 0:
        return {
            "means": np.zeros((active_k, d), dtype=np.float64),
            "variances": np.ones((active_k, d), dtype=np.float64),
            "weights": np.full(active_k, 1.0 / float(active_k), dtype=np.float64),
            "history": [],
            "model_family": "context_balanced_visible_prototype_mixture",
            "assignment_method": "context-balanced one-to-one assignment per context group",
            "uses_context_groups": True,
        }
    groups = np.asarray(context_groups, dtype=np.int64)
    unique_groups = sorted(set(groups.tolist()))
    if not _context_balance_supported(groups, active_k):
        return _fit_prototype_mixture(
            x,
            k=active_k,
            seed=seed,
            max_iter=max_iter,
            initial_temperature=DEFAULT_INITIAL_TEMPERATURE,
            final_temperature=DEFAULT_FINAL_TEMPERATURE,
        )
    anchor_group = unique_groups[int(seed) % len(unique_groups)]
    anchor_idx = np.asarray([idx for idx, group in enumerate(groups.tolist()) if int(group) == int(anchor_group)], dtype=np.int64)
    means = x[anchor_idx].copy()
    global_var = np.maximum(np.var(x, axis=0), VARIANCE_FLOOR)
    variances = np.tile(global_var[None, :], (active_k, 1))
    weights = np.full(active_k, 1.0 / float(active_k), dtype=np.float64)
    history: list[dict[str, float]] = []
    iterations = max(1, int(max_iter))
    for step in range(iterations):
        hard = _context_balanced_hard_assignments(x, groups, means)
        weights = np.asarray([np.mean(hard == idx) for idx in range(active_k)], dtype=np.float64)
        weights = np.maximum(weights, MIN_COMPONENT_MASS)
        weights = weights / float(np.sum(weights))
        for idx in range(active_k):
            mask = hard == idx
            if np.any(mask):
                means[idx] = np.mean(x[mask], axis=0)
        for idx in range(active_k):
            mask = hard == idx
            if np.any(mask):
                diff = x[mask] - means[idx]
                variances[idx] = np.maximum(np.mean(diff * diff, axis=0), VARIANCE_FLOOR)
        if step == 0 or step == iterations - 1 or (step + 1) % max(1, iterations // 5) == 0:
            responsibilities = _one_hot(hard, active_k)
            model = {"means": means, "variances": variances, "weights": weights, "history": history}
            history.append(
                {
                    "iteration": float(step + 1),
                    "visible_nll": float(_mixture_nll(x, model)),
                    "context_balanced_reconstruction_loss": float(_responsibility_reconstruction_loss(x, model, responsibilities)),
                    "context_balance_violation_count": float(context_balance_violation_count(responsibilities, groups, expected_k=active_k)),
                    "active_prototype_count": float(np.sum(weights > MIN_COMPONENT_MASS)),
                }
            )
    return {
        "means": means,
        "variances": variances,
        "weights": weights,
        "history": history,
        "model_family": "context_balanced_visible_prototype_mixture",
        "assignment_method": "context-balanced one-to-one assignment per context group",
        "uses_context_groups": True,
    }


def _context_balanced_hard_assignments(x: np.ndarray, groups: np.ndarray, means: np.ndarray) -> np.ndarray:
    hard = np.zeros(x.shape[0], dtype=np.int64)
    k = int(means.shape[0])
    for group in sorted(set(np.asarray(groups, dtype=np.int64).tolist())):
        idx = np.asarray([row for row, value in enumerate(groups.tolist()) if int(value) == int(group)], dtype=np.int64)
        if idx.size == 0:
            continue
        cost = _squared_distances(x[idx], means)
        if idx.size == k:
            rows, cols = _linear_sum_assignment(cost)
            hard[idx[np.asarray(rows, dtype=np.int64)]] = np.asarray(cols, dtype=np.int64)
        else:
            hard[idx] = np.argmin(cost, axis=1).astype(np.int64)
    return hard


def _linear_sum_assignment(cost: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    try:
        from scipy.optimize import linear_sum_assignment  # type: ignore

        rows, cols = linear_sum_assignment(cost)
        return np.asarray(rows, dtype=np.int64), np.asarray(cols, dtype=np.int64)
    except Exception:
        return _greedy_assignment(cost)


def _greedy_assignment(cost: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    remaining_rows = set(range(int(cost.shape[0])))
    remaining_cols = set(range(int(cost.shape[1])))
    rows: list[int] = []
    cols: list[int] = []
    while remaining_rows and remaining_cols:
        best = min(
            ((float(cost[row, col]), row, col) for row in remaining_rows for col in remaining_cols),
            key=lambda item: (item[0], item[1], item[2]),
        )
        _value, row, col = best
        rows.append(int(row))
        cols.append(int(col))
        remaining_rows.remove(row)
        remaining_cols.remove(col)
    return np.asarray(rows, dtype=np.int64), np.asarray(cols, dtype=np.int64)


def _model_responsibilities(
    x: np.ndarray,
    *,
    context_groups: np.ndarray,
    model: dict[str, np.ndarray | list[dict[str, float]] | str | bool],
    temperature: float,
) -> np.ndarray:
    means = np.asarray(model["means"], dtype=np.float64)
    if bool(model.get("uses_context_groups", False)) and _context_balance_supported(context_groups, int(means.shape[0])):
        hard = _context_balanced_hard_assignments(x, np.asarray(context_groups, dtype=np.int64), means)
        return _one_hot(hard, int(means.shape[0]))
    return _posterior_responsibilities(x, model, temperature=temperature)  # type: ignore[arg-type]


def _one_hot(hard: np.ndarray, k: int) -> np.ndarray:
    out = np.zeros((int(hard.shape[0]), int(k)), dtype=np.float64)
    if out.size:
        out[np.arange(int(hard.shape[0])), np.asarray(hard, dtype=np.int64)] = 1.0
    return out



def _posterior_responsibilities(
    x: np.ndarray,
    model: dict[str, np.ndarray | list[dict[str, float]]],
    *,
    temperature: float,
) -> np.ndarray:
    means = np.asarray(model["means"], dtype=np.float64)
    variances = np.asarray(model["variances"], dtype=np.float64)
    weights = np.asarray(model["weights"], dtype=np.float64)
    if x.shape[0] == 0:
        return np.zeros((0, means.shape[0]), dtype=np.float64)
    log_prob = _diag_log_prob(x, means, variances) + np.log(np.maximum(weights, MIN_COMPONENT_MASS))[None, :]
    scaled = log_prob / max(float(temperature), 1.0e-6)
    norm = _logsumexp(scaled, axis=1)
    return np.exp(scaled - norm[:, None])


def _mixture_nll(x: np.ndarray, model: dict[str, np.ndarray | list[dict[str, float]]]) -> float:
    if x.shape[0] == 0:
        return 0.0
    means = np.asarray(model["means"], dtype=np.float64)
    variances = np.asarray(model["variances"], dtype=np.float64)
    weights = np.asarray(model["weights"], dtype=np.float64)
    log_prob = _diag_log_prob(x, means, variances) + np.log(np.maximum(weights, MIN_COMPONENT_MASS))[None, :]
    return float(-np.mean(_logsumexp(log_prob, axis=1)))


def _soft_reconstruction_loss(x: np.ndarray, model: dict[str, np.ndarray | list[dict[str, float]]]) -> float:
    if x.shape[0] == 0:
        return 0.0
    responsibilities = _posterior_responsibilities(x, model, temperature=1.0)
    return _responsibility_reconstruction_loss(x, model, responsibilities)


def _responsibility_reconstruction_loss(
    x: np.ndarray,
    model: dict[str, np.ndarray | list[dict[str, float]] | str | bool],
    responsibilities: np.ndarray,
) -> float:
    if x.shape[0] == 0:
        return 0.0
    means = np.asarray(model["means"], dtype=np.float64)
    diff = x[:, None, :] - means[None, :, :]
    squared = np.sum(diff * diff, axis=2)
    return float(np.mean(np.sum(responsibilities * squared, axis=1)))


def context_balance_violation_count(responsibilities: np.ndarray, context_groups: np.ndarray, *, expected_k: int) -> int:
    if responsibilities.size == 0:
        return 0
    hard = np.argmax(responsibilities, axis=1).astype(np.int64)
    violations = 0
    for group in sorted(set(np.asarray(context_groups, dtype=np.int64).tolist())):
        local = hard[np.asarray(context_groups, dtype=np.int64) == int(group)]
        if local.size != int(expected_k):
            continue
        counts = np.bincount(local, minlength=int(expected_k))
        violations += int(np.sum(np.abs(counts - 1)))
    return int(violations)


def _assignment_entropy(responsibilities: np.ndarray) -> float:
    if responsibilities.size == 0:
        return 0.0
    clipped = np.maximum(responsibilities, MIN_COMPONENT_MASS)
    return float(np.mean(-np.sum(responsibilities * np.log(clipped), axis=1)))


def _standardize_visible_features_with_values(x: np.ndarray) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    mean = np.mean(x, axis=0) if x.size else np.zeros(x.shape[1], dtype=np.float64)
    scale = np.std(x, axis=0) if x.size else np.ones(x.shape[1], dtype=np.float64)
    scale = np.where(scale > 1.0e-12, scale, 1.0)
    z = (x - mean) / scale if x.size else x
    return z, {"mean": mean, "scale": scale}


def _apply_visible_feature_weights(
    x: np.ndarray,
    *,
    feature_names: list[str],
    operation_context_weight: float,
) -> tuple[np.ndarray, dict[str, np.ndarray | float | int]]:
    weights = _visible_feature_weight_vector(
        feature_names,
        operation_context_weight=float(operation_context_weight),
    )
    weighted = np.asarray(x, dtype=np.float64) * weights[None, :] if x.size else np.asarray(x, dtype=np.float64)
    return weighted, {
        "feature_weights": weights,
        "operation_context_weight": float(operation_context_weight),
        "operation_context_feature_count": int(np.sum(_operation_context_feature_mask(feature_names))),
    }


def _visible_feature_weight_vector(
    feature_names: list[str],
    *,
    operation_context_weight: float,
) -> np.ndarray:
    weights = np.ones(len(feature_names), dtype=np.float64)
    mask = _operation_context_feature_mask(feature_names)
    weights[mask] = float(operation_context_weight)
    return weights


def _operation_context_feature_mask(feature_names: list[str]) -> np.ndarray:
    return np.asarray(
        [
            str(name).startswith("visible_metadata__instruction_")
            or str(name).startswith("visible_metadata__operation_")
            for name in feature_names
        ],
        dtype=bool,
    )


def _standardization_summary(standardization: dict[str, np.ndarray]) -> dict[str, object]:
    weights = np.asarray(standardization.get("feature_weight", np.ones_like(standardization["mean"])), dtype=np.float64)
    return {
        "schema": "scope_static_stage3b1_visible_feature_standardization_v1",
        "method": "feature-wise z-score over visible instances, followed by declared visible-feature group weights",
        "feature_count": int(standardization["mean"].shape[0]),
        "zero_scale_replaced_with_one": True,
        "weighted_feature_count": int(np.sum(np.abs(weights - 1.0) > 1.0e-12)),
    }


def _feature_weighting_summary(weighting: dict[str, np.ndarray | float | int], feature_names: list[str]) -> dict[str, object]:
    weights = np.asarray(weighting.get("feature_weights", np.ones(len(feature_names), dtype=np.float64)), dtype=np.float64)
    weighted = [
        {
            "feature": str(feature_names[idx]),
            "weight": float(weights[idx]),
        }
        for idx in range(len(feature_names))
        if abs(float(weights[idx]) - 1.0) > 1.0e-12
    ]
    return {
        "schema": "scope_static_stage3b1_visible_feature_weighting_v1",
        "uses_mechanism_labels": False,
        "uses_visible_operation_context": True,
        "operation_context_weight": float(weighting.get("operation_context_weight", 1.0)),
        "operation_context_feature_count": int(weighting.get("operation_context_feature_count", 0)),
        "weighted_feature_count": int(len(weighted)),
        "weighted_features": weighted,
    }


def _squared_distances(x: np.ndarray, centers: np.ndarray) -> np.ndarray:
    diff = x[:, None, :] - centers[None, :, :]
    return np.sum(diff * diff, axis=2)


def _seeded_farthest_first_centers(x: np.ndarray, k: int, *, seed: int) -> np.ndarray:
    n, d = x.shape
    if n == 0:
        return np.zeros((max(1, k), d), dtype=np.float64)
    rng = np.random.default_rng(int(seed))
    jitter = rng.normal(loc=0.0, scale=1.0e-12, size=n)
    first = int(np.argmax(np.sum(x * x, axis=1) + jitter))
    centers = [x[first].copy()]
    while len(centers) < k:
        current = np.asarray(centers, dtype=np.float64)
        min_dist = np.min(_squared_distances(x, current), axis=1)
        jitter = rng.normal(loc=0.0, scale=1.0e-12, size=n)
        idx = int(np.argmax(min_dist + jitter))
        if any(np.allclose(x[idx], center) for center in centers):
            idx = len(centers) % n
        centers.append(x[idx].copy())
    return np.asarray(centers, dtype=np.float64)


def _annealed_temperature(
    step: int,
    *,
    total: int,
    initial_temperature: float,
    final_temperature: float,
) -> float:
    if total <= 1:
        return float(final_temperature)
    alpha = float(step) / float(max(1, total - 1))
    return float((1.0 - alpha) * initial_temperature + alpha * final_temperature)


def _valid_folds(split_manifest: dict[str, object], *, record_count: int) -> list[dict[str, list[int]]]:
    out: list[dict[str, list[int]]] = []
    for row in split_manifest.get("folds", []):
        if not isinstance(row, dict):
            continue
        train = _clean_indices(row.get("train_indices", []), record_count=record_count)
        validation = _clean_indices(row.get("validation_indices", []), record_count=record_count)
        test = _clean_indices(row.get("test_indices", []), record_count=record_count)
        if train and validation:
            out.append({"train_indices": train, "validation_indices": validation, "test_indices": test})
    return out


def _context_groups_from_split_manifest(split_manifest: dict[str, object], *, record_count: int) -> np.ndarray:
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


def _context_balance_supported(context_groups: np.ndarray, k: int) -> bool:
    groups = np.asarray(context_groups, dtype=np.int64)
    if groups.size == 0 or int(k) <= 0:
        return False
    counts = [int(np.sum(groups == group)) for group in sorted(set(groups.tolist()))]
    return bool(counts and all(count == int(k) for count in counts))


def _cap_folds(
    folds: list[dict[str, list[int]]],
    *,
    max_cv_folds: int | None,
) -> list[dict[str, list[int]]]:
    if max_cv_folds is None:
        return list(folds)
    return list(folds[: max(1, int(max_cv_folds))])


def _clean_indices(value: object, *, record_count: int) -> list[int]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        idx = int(item)
        if 0 <= idx < int(record_count):
            out.append(idx)
    return out


def _candidate_key(candidate: dict[str, object]) -> tuple[str, int]:
    return (str(candidate.get("k_mode", "")), int(candidate.get("k", 0)))


def _mean_finite(values: list[object]) -> float:
    floats = [float(value) for value in values if value is not None and np.isfinite(float(value))]
    return float(np.mean(floats)) if floats else 0.0


def _write_outputs(
    output: Path,
    result: dict[str, object],
    responsibilities: np.ndarray,
    model: dict[str, np.ndarray | list[dict[str, float]]],
) -> None:
    artifacts = {
        "metrics.json": result,
        "candidate_selection.json": result["candidate_selection"],
        "learned_assignment_summary.json": result["learned_assignment_summary"],
        "learned_prototypes.json": result["learned_prototypes"],
        "prototype_generation_metrics.json": result["prototype_generation_metrics"],
        "assignment_hardening_audit.json": result["assignment_hardening_audit"],
        "label_permutation_audit.json": result["label_permutation_audit"],
        "model_selection_audit.json": result["model_selection_audit"],
        "evaluator_only_label_metrics.json": result["evaluator_only_label_metrics"],
        "context_dependent_mechanism_diagnostics.json": result["context_dependent_mechanism_diagnostics"],
        "quotient_metrics.json": result["quotient_metrics"],
        "acceptance_audit.json": result["acceptance_audit"],
        "feature_schema_match_audit.json": result["feature_schema_match_audit"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
        "visible_feature_weighting.json": result["visible_feature_weighting"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    np.save(output / "learned_assignments.npy", responsibilities)
    np.save(output / "learned_covariances.npy", np.asarray(model["variances"], dtype=np.float64))
    np.savez(
        output / "model_parameters.npz",
        means=np.asarray(model["means"], dtype=np.float64),
        variances=np.asarray(model["variances"], dtype=np.float64),
        weights=np.asarray(model["weights"], dtype=np.float64),
    )
    (output / "config.yaml").write_text(yaml.safe_dump({"stage3b1_first_discovery_model": result["config"]}, sort_keys=False))
    (output / "summary.md").write_text(format_stage3b1_summary(result))


def format_stage3b1_summary(result: dict[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    summary = dict(result.get("learned_assignment_summary", {}))
    evaluator = dict(result.get("evaluator_only_label_metrics", {}))
    exact = dict(evaluator.get("selected_model_exact_metrics", {}))
    quotient = dict(evaluator.get("selected_model_quotient_metrics", {}))
    context_dependent = dict(result.get("context_dependent_mechanism_diagnostics", {}))
    m13 = dict(dict(context_dependent.get("diagnostics", {})).get("M13", {}))
    m13_lines = []
    if bool(m13.get("present", False)):
        m13_lines = [
            f"- M13 exact-label matched recall: `{float(m13.get('exact_label_recall_after_one_cluster_matching', 0.0)):.4f}`",
            f"- M13 pure-submode recall: `{float(m13.get('pure_context_submode_recall', 0.0)):.4f}`",
            f"- M13 assigned clusters: `{int(m13.get('assigned_cluster_count', 0))}`",
            f"- M13 interpretation: `{m13.get('interpretation')}`",
        ]
    return "\n".join(
        [
            "# Stage 3B.1: First Discovery Model",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Selected K mode: `{summary.get('selected_k_mode')}`",
            f"- Selected K: `{summary.get('selected_k')}`",
            f"- Selected model family: `{dict(result.get('candidate_selection', {})).get('selected', {}).get('model_family') if isinstance(dict(result.get('candidate_selection', {})).get('selected', {}), dict) else None}`",
            f"- Active prototypes: `{summary.get('active_prototype_count')}`",
            f"- Exact-label BA: `{float(exact.get('balanced_accuracy_after_label_matching', 0.0)):.4f}`",
            f"- Exact-label min recall: `{float(exact.get('min_recall_after_label_matching', 0.0)):.4f}`",
            f"- Exact-label NMI: `{float(exact.get('normalized_mutual_info', 0.0)):.4f}`",
            f"- Quotient-label NMI: `{float(quotient.get('normalized_mutual_info', 0.0)):.4f}`",
            *m13_lines,
            "",
            "## Claim Boundary",
            "",
            "Stage 3B.1 trains a visible-only prototype mixture. Mechanism labels, quotient labels, channels, teacher IDs, oracle prototypes, and label metrics are withheld from fitting and model selection; evaluator labels are used only after fitting for reporting.",
            "",
        ]
    )
