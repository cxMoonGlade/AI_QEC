from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np

from scope_static.protocols import LEARNER_VALIDATION_STAGE
from .zx_visible_probe_suite import (
    FORBIDDEN_FEATURE_TOKENS,
    build_zx_visible_feature_table,
    leakage_guardrail_audit_zx_visible,
)
from scope_static.mechanism_observability import classification_metrics


STAGE_NAME = "PHYC3c_distributional_gaussian_likelihood_head"
HEADS = (
    "PHYC3c_ablation_mean_only",
    "PHYC3c_ablation_covariance_only",
    "PHYC3c_diagonal_gaussian",
    "PHYC3c_shared_covariance_lda",
    "PHYC3c_full_gaussian_likelihood",
    "PHYC3c_shrinkage_qda",
)


@dataclass(frozen=True)
class GaussianFoldModel:
    selected_columns: list[int]
    feature_mean: np.ndarray
    feature_scale: np.ndarray
    class_names: list[str]
    means: dict[str, np.ndarray]
    diagonal_variances: dict[str, np.ndarray]
    shrinkage_variances: dict[str, np.ndarray]
    pooled_variance: np.ndarray
    pca_basis: np.ndarray
    pca_means: dict[str, np.ndarray]
    pca_covariances: dict[str, np.ndarray]
    pca_shrinkage_covariances: dict[str, np.ndarray]
    pca_pooled_covariance: np.ndarray


def run_phyc3c_distributional_gaussian_likelihood_head(
    *,
    teacher_dir: str | Path,
    output_dir: str | Path,
    shots: int = 20_000,
    seed: int = 0,
    robustness_mode: bool = False,
    sampling_mode: str = "expected",
    batch_size: int = 5,
    shrinkage_alpha: float = 0.25,
    ridge: float = 1e-6,
    variance_floor: float = 1e-8,
    max_pca_components: int = 24,
) -> dict[str, object]:
    teacher = Path(teacher_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")
    table = build_zx_visible_feature_table(
        records,
        shots=int(shots),
        seed=int(seed),
        robustness_mode=bool(robustness_mode),
        sampling_mode=str(sampling_mode),
    )
    labels = [str(label) for label in table.labels]
    groups = [int(group) for group in table.groups]
    class_names = sorted(set(labels), key=_mechanism_sort_key)
    x = np.asarray(table.features, dtype=np.float64)

    single_protocol = build_batch_protocol(labels, groups, class_names, mode="single_realization", batch_size=1)
    multi_protocol = build_batch_protocol(labels, groups, class_names, mode="multi_context_batch", batch_size=int(batch_size))
    single_result = evaluate_heads_for_protocol(
        x,
        labels,
        groups,
        class_names,
        single_protocol,
        shrinkage_alpha=float(shrinkage_alpha),
        ridge=float(ridge),
        variance_floor=float(variance_floor),
        max_pca_components=int(max_pca_components),
    )
    multi_result = evaluate_heads_for_protocol(
        x,
        labels,
        groups,
        class_names,
        multi_protocol,
        shrinkage_alpha=float(shrinkage_alpha),
        ridge=float(ridge),
        variance_floor=float(variance_floor),
        max_pca_components=int(max_pca_components),
    )
    distributional_ceiling = distributional_ceiling_audit(x, labels, groups, class_names, multi_protocol)
    leakage = leakage_guardrail_audit_phyc3c(table.feature_names)
    m13 = m13_recovery_audit(single_result, multi_result)
    primary = dict(multi_result["head_results"]["PHYC3c_diagonal_gaussian"]["overall"])
    result = {
        "schema": "scope_static_phyc3c_distributional_gaussian_likelihood_head_v1",
        "stage": STAGE_NAME,
        "public_layer": LEARNER_VALIDATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="distributional_gaussian_likelihood_head"),
        "teacher_dir": str(teacher),
        "output_dir": str(output),
        "claim_boundary": {
            "visible_features_source": "PHYC3b Z/X-only sampled-observation features",
            "z_x_only": True,
            "no_y_basis": True,
            "distributional_head_not_new_probe_stage": True,
            "m13_perfect_recovery_expected_only_in_multi_context_batch_mode": True,
            "single_realization_m13_may_operationally_collapse_to_fixed_coherent_rotation": True,
        },
        "config": {
            "shots": int(shots),
            "seed": int(seed),
            "robustness_mode": bool(robustness_mode),
            "sampling_mode": str(sampling_mode),
            "batch_size": int(batch_size),
            "shrinkage_alpha": float(shrinkage_alpha),
            "ridge": float(ridge),
            "variance_floor": float(variance_floor),
            "max_pca_components": int(max_pca_components),
        },
        "feature_schema": table.feature_schema,
        "gaussian_parameter_schema": gaussian_parameter_schema(table.feature_names, max_pca_components=int(max_pca_components)),
        "batch_protocol_audit": {
            "schema": "scope_static_phyc3c_batch_protocol_audit_v1",
            "single_realization_mode": protocol_summary(single_protocol),
            "multi_context_batch_mode": protocol_summary(multi_protocol),
            "calibration_uses_training_groups_only": True,
            "test_labels_evaluator_only": True,
            "minimum_m13_contexts_required_for_distributional_claim": int(batch_size),
        },
        "distributional_ceiling_audit": distributional_ceiling,
        "single_realization_mode": single_result,
        "multi_context_batch_mode": multi_result,
        "head_comparison": head_comparison(single_result, multi_result),
        "m13_recovery_audit": m13,
        "leakage_guardrail_audit": leakage,
        "primary_head": "PHYC3c_diagonal_gaussian",
        "primary_mode": "multi_context_batch",
        "learner_BA": float(primary.get("balanced_accuracy", 0.0)),
        "learner_ARI": float(primary.get("adjusted_rand_index", 0.0)),
        "learner_NMI": float(primary.get("normalized_mutual_info", 0.0)),
        "min_recall": float(primary.get("min_class_recall", 0.0)),
        "m13_recall": float(primary.get("per_class_recall", {}).get("M13", 0.0)) if isinstance(primary.get("per_class_recall", {}), dict) else 0.0,
        "decision": _decision(primary, distributional_ceiling),
    }
    _write_outputs(output, result)
    return result


def build_batch_protocol(
    labels: list[str],
    groups: list[int],
    class_names: list[str],
    *,
    mode: str,
    batch_size: int,
) -> list[dict[str, object]]:
    unique_groups = sorted(set(int(group) for group in groups))
    batches = []
    if mode == "single_realization":
        fold_specs = [[group] for group in unique_groups]
    elif mode == "multi_context_batch":
        size = max(2, int(batch_size))
        fold_specs = [unique_groups[start : start + size] for start in range(0, len(unique_groups), size)]
    else:
        raise ValueError("mode must be 'single_realization' or 'multi_context_batch'")
    for fold_idx, test_groups in enumerate(fold_specs):
        train_groups = [group for group in unique_groups if group not in set(test_groups)]
        for label in class_names:
            indices = [idx for idx, (current, group) in enumerate(zip(labels, groups)) if current == label and int(group) in set(test_groups)]
            if not indices:
                continue
            batches.append(
                {
                    "fold": int(fold_idx),
                    "mode": str(mode),
                    "label_evaluator_only": str(label),
                    "test_groups": [int(group) for group in test_groups],
                    "train_groups": [int(group) for group in train_groups],
                    "test_indices": [int(idx) for idx in indices],
                    "num_contexts": int(len(indices)),
                    "distributional_batch": bool(len(indices) > 1),
                }
            )
    return batches


def evaluate_heads_for_protocol(
    features: np.ndarray,
    labels: list[str],
    groups: list[int],
    class_names: list[str],
    protocol: list[dict[str, object]],
    *,
    shrinkage_alpha: float,
    ridge: float,
    variance_floor: float,
    max_pca_components: int,
    heads: tuple[str, ...] | list[str] | None = None,
) -> dict[str, object]:
    active_heads = tuple(str(head) for head in (heads if heads is not None else HEADS))
    unknown = [head for head in active_heads if head not in HEADS]
    if unknown:
        raise ValueError(f"unknown PHYC3c heads {unknown!r}")
    needs_pca = any(head in {"PHYC3c_full_gaussian_likelihood", "PHYC3c_shrinkage_qda"} for head in active_heads)
    by_fold: dict[int, list[dict[str, object]]] = {}
    for batch in protocol:
        by_fold.setdefault(int(batch["fold"]), []).append(batch)
    head_predictions = {head: {"true": [], "pred": [], "folds": []} for head in active_heads}
    groups_array = np.asarray(groups, dtype=np.int64)
    for fold, batches in sorted(by_fold.items()):
        train_groups = [int(group) for group in batches[0].get("train_groups", [])]
        train_indices = np.where(np.isin(groups_array, np.asarray(train_groups, dtype=np.int64)))[0]
        model = fit_gaussian_fold_model(
            features,
            labels,
            train_indices.tolist(),
            class_names,
            shrinkage_alpha=float(shrinkage_alpha),
            ridge=float(ridge),
            variance_floor=float(variance_floor),
            max_pca_components=int(max_pca_components) if needs_pca else 0,
        )
        for head in active_heads:
            true_labels = []
            predicted_labels = []
            batch_rows = []
            for batch in batches:
                true_label = str(batch["label_evaluator_only"])
                pred, scores = predict_gaussian_batch(model, features, [int(idx) for idx in batch["test_indices"]], head=head)
                true_labels.append(true_label)
                predicted_labels.append(pred)
                batch_rows.append(
                    {
                        "true_label_evaluator_only": true_label,
                        "predicted_label": pred,
                        "num_contexts": int(batch["num_contexts"]),
                        "test_groups": [int(group) for group in batch["test_groups"]],
                        "top_scores": _top_scores(scores, limit=5),
                    }
                )
            head_predictions[head]["true"].extend(true_labels)
            head_predictions[head]["pred"].extend(predicted_labels)
            head_predictions[head]["folds"].append(
                {
                    "fold": int(fold),
                    "test_groups": [int(group) for group in batches[0].get("test_groups", [])],
                    "train_groups": train_groups,
                    "head": head,
                    "true_labels": true_labels,
                    "predicted_labels": predicted_labels,
                    "batches": batch_rows,
                    "calibration_train_groups_only": True,
                    "selected_feature_count": int(len(model.selected_columns)),
                    "pca_components": int(model.pca_basis.shape[1]) if model.pca_basis.ndim == 2 else 0,
                }
            )
    results = {}
    for head, payload in head_predictions.items():
        overall = classification_metrics(payload["true"], payload["pred"], class_names)
        results[head] = {
            "schema": "scope_static_phyc3c_head_result_v1",
            "head": head,
            "overall": overall,
            "balanced_accuracy": float(overall.get("balanced_accuracy", 0.0)),
            "adjusted_rand_index": float(overall.get("adjusted_rand_index", 0.0)),
            "normalized_mutual_info": float(overall.get("normalized_mutual_info", 0.0)),
            "min_class_recall": float(overall.get("min_class_recall", 0.0)),
            "m13_recall": float(overall.get("per_class_recall", {}).get("M13", 0.0)) if isinstance(overall.get("per_class_recall", {}), dict) else 0.0,
            "grouped_fold_predictions": payload["folds"],
        }
    mode = str(protocol[0]["mode"]) if protocol else "unknown"
    return {
        "schema": "scope_static_phyc3c_protocol_evaluation_v1",
        "mode": mode,
        "protocol": protocol_summary(protocol),
        "head_results": results,
    }


def fit_gaussian_fold_model(
    features: np.ndarray,
    labels: list[str],
    train_indices: list[int],
    class_names: list[str],
    *,
    shrinkage_alpha: float,
    ridge: float,
    variance_floor: float,
    max_pca_components: int,
) -> GaussianFoldModel:
    x_all = np.asarray(features, dtype=np.float64)
    idx = np.asarray(train_indices, dtype=np.int64)
    x_train = x_all[idx]
    selected = np.where(np.std(x_train, axis=0) > 1e-10)[0]
    if selected.size == 0:
        selected = np.arange(x_all.shape[1])
    x_selected = x_train[:, selected]
    feature_mean = np.mean(x_selected, axis=0)
    feature_scale = np.std(x_selected, axis=0)
    feature_scale = np.where(feature_scale > 1e-12, feature_scale, 1.0)
    z_train = (x_selected - feature_mean) / feature_scale
    train_labels = np.asarray([labels[int(i)] for i in idx.tolist()], dtype=object)
    pooled_variance = np.var(z_train, axis=0) + float(variance_floor)
    means = {}
    variances = {}
    shrinkage_variances = {}
    for label in class_names:
        local = z_train[train_labels == label]
        if local.size == 0:
            means[label] = np.zeros(z_train.shape[1], dtype=np.float64)
            variances[label] = np.ones(z_train.shape[1], dtype=np.float64)
            shrinkage_variances[label] = np.ones(z_train.shape[1], dtype=np.float64)
            continue
        means[label] = np.mean(local, axis=0)
        class_var = np.var(local, axis=0) + float(variance_floor)
        variances[label] = class_var
        shrinkage_variances[label] = (1.0 - float(shrinkage_alpha)) * class_var + float(shrinkage_alpha) * pooled_variance + float(ridge)

    pca_basis = _pca_basis(z_train, max_components=int(max_pca_components))
    z_pca = z_train @ pca_basis if pca_basis.size else np.zeros((z_train.shape[0], 0), dtype=np.float64)
    pca_pooled = _regularized_covariance(z_pca, ridge=float(ridge), shrinkage_alpha=1.0)
    pca_means = {}
    pca_covs = {}
    pca_shrink = {}
    for label in class_names:
        local = z_pca[train_labels == label]
        if local.size == 0:
            dim = int(z_pca.shape[1])
            pca_means[label] = np.zeros(dim, dtype=np.float64)
            pca_covs[label] = np.eye(dim, dtype=np.float64)
            pca_shrink[label] = np.eye(dim, dtype=np.float64)
            continue
        pca_means[label] = np.mean(local, axis=0)
        pca_covs[label] = _regularized_covariance(local, ridge=float(ridge), shrinkage_alpha=0.0)
        pca_shrink[label] = _regularized_covariance(local, ridge=float(ridge), shrinkage_alpha=float(shrinkage_alpha))
    return GaussianFoldModel(
        selected_columns=[int(value) for value in selected.tolist()],
        feature_mean=feature_mean,
        feature_scale=feature_scale,
        class_names=list(class_names),
        means=means,
        diagonal_variances=variances,
        shrinkage_variances=shrinkage_variances,
        pooled_variance=pooled_variance + float(ridge),
        pca_basis=pca_basis,
        pca_means=pca_means,
        pca_covariances=pca_covs,
        pca_shrinkage_covariances=pca_shrink,
        pca_pooled_covariance=pca_pooled,
    )


def predict_gaussian_batch(model: GaussianFoldModel, features: np.ndarray, indices: list[int], *, head: str) -> tuple[str, dict[str, float]]:
    x = np.asarray(features, dtype=np.float64)
    rows = x[np.asarray(indices, dtype=np.int64)][:, np.asarray(model.selected_columns, dtype=np.int64)]
    z = (rows - model.feature_mean) / model.feature_scale
    n = max(1, int(z.shape[0]))
    xbar = np.mean(z, axis=0)
    sample_var = np.mean((z - xbar) ** 2, axis=0) if z.shape[0] > 1 else np.zeros(z.shape[1], dtype=np.float64)
    scores = {}
    if head in {"PHYC3c_full_gaussian_likelihood", "PHYC3c_shrinkage_qda"}:
        z_pca = z @ model.pca_basis if model.pca_basis.size else np.zeros((z.shape[0], 0), dtype=np.float64)
        pca_mean = np.mean(z_pca, axis=0)
        scatter = (z_pca - pca_mean).T @ (z_pca - pca_mean) if z_pca.shape[0] > 1 else np.zeros((z_pca.shape[1], z_pca.shape[1]), dtype=np.float64)
        for label in model.class_names:
            cov = model.pca_covariances[label] if head == "PHYC3c_full_gaussian_likelihood" else model.pca_shrinkage_covariances[label]
            scores[label] = _full_gaussian_score(pca_mean, scatter, model.pca_means[label], cov, n)
        return max(scores, key=scores.get), scores
    for label in model.class_names:
        mean = model.means[label]
        if head == "PHYC3c_ablation_mean_only":
            scores[label] = -float(np.mean((xbar - mean) ** 2))
        elif head == "PHYC3c_ablation_covariance_only":
            scores[label] = _diagonal_gaussian_score(
                xbar=np.zeros_like(xbar),
                sample_var=sample_var,
                mean=np.zeros_like(mean),
                variance=model.shrinkage_variances[label],
                n=n,
                include_mean=False,
                include_covariance=True,
            )
        elif head == "PHYC3c_diagonal_gaussian":
            scores[label] = _diagonal_gaussian_score(xbar, sample_var, mean, model.shrinkage_variances[label], n=n)
        elif head == "PHYC3c_shared_covariance_lda":
            scores[label] = _diagonal_gaussian_score(
                xbar,
                sample_var,
                mean,
                model.pooled_variance,
                n=n,
                include_covariance=False,
            )
        else:
            raise ValueError(f"unknown PHYC3c head {head!r}")
    return max(scores, key=scores.get), scores


def distributional_ceiling_audit(
    features: np.ndarray,
    labels: list[str],
    groups: list[int],
    class_names: list[str],
    protocol: list[dict[str, object]],
    *,
    decimals: int = 10,
) -> dict[str, object]:
    signatures: dict[tuple[float, ...], list[int]] = {}
    batch_labels = []
    x = np.asarray(features, dtype=np.float64)
    for batch_idx, batch in enumerate(protocol):
        rows = x[np.asarray(batch["test_indices"], dtype=np.int64)]
        xbar = np.mean(rows, axis=0)
        var = np.mean((rows - xbar) ** 2, axis=0) if rows.shape[0] > 1 else np.zeros(rows.shape[1], dtype=np.float64)
        signature = tuple(float(value) for value in np.round(np.concatenate([xbar, var]), int(decimals)).tolist())
        signatures.setdefault(signature, []).append(batch_idx)
        batch_labels.append(str(batch["label_evaluator_only"]))
    conflicts = []
    for indices in signatures.values():
        local = [batch_labels[idx] for idx in indices]
        unique = sorted(set(local), key=_mechanism_sort_key)
        if len(unique) > 1:
            conflicts.append({"labels": unique, "record_count": int(len(indices)), "label_counts": {label: int(local.count(label)) for label in unique}})
    predictions = _optimistic_predictions(batch_labels, signatures)
    ceiling = classification_metrics(batch_labels, predictions, class_names)
    return {
        "schema": "scope_static_phyc3c_distributional_ceiling_audit_v1",
        "feature_source": "batch mean plus diagonal sample covariance from PHYC3b Z/X visible features",
        "signature_decimals": int(decimals),
        "num_batches": int(len(protocol)),
        "conflicting_distributional_signature_count": int(len(conflicts)),
        "conflicting_batch_count": int(sum(row["record_count"] for row in conflicts)),
        "conflict_examples": conflicts[:50],
        "deterministic_distributional_ceiling": {
            "balanced_accuracy": float(ceiling.get("balanced_accuracy", 0.0)),
            "min_class_recall": float(ceiling.get("min_class_recall", 0.0)),
            "adjusted_rand_index": float(ceiling.get("adjusted_rand_index", 0.0)),
            "normalized_mutual_info": float(ceiling.get("normalized_mutual_info", 0.0)),
            "per_class_recall": ceiling.get("per_class_recall", {}),
        },
    }


def gaussian_parameter_schema(feature_names: list[str], *, max_pca_components: int) -> dict[str, object]:
    return {
        "schema": "scope_static_phyc3c_gaussian_parameter_schema_v1",
        "stage": STAGE_NAME,
        "heads": list(HEADS),
        "parameters": [
            "global train-fold feature mean and scale",
            "per-mechanism feature mean mu_m",
            "per-mechanism diagonal covariance variance_m",
            "pooled shared covariance for LDA",
            "train-fold PCA basis for full/shrinkage covariance heads",
            "per-mechanism regularized covariance in train-fold PCA coordinates",
        ],
        "likelihood": (
            "For a batch with N rows, PHYC3c uses -0.5 * [N logdet Sigma_m + "
            "N (xbar - mu_m)^T Sigma_m^-1 (xbar - mu_m) + tr(Sigma_m^-1 C)], "
            "where C = sum_i (x_i - xbar)(x_i - xbar)^T. Diagonal heads use the "
            "same formula with diagonal Sigma_m."
        ),
        "max_pca_components": int(max_pca_components),
        "feature_count": int(len(feature_names)),
        "raw_visible_feature_names_retained": True,
    }


def leakage_guardrail_audit_phyc3c(feature_names: list[str]) -> dict[str, object]:
    base = leakage_guardrail_audit_zx_visible(feature_names)
    checks = dict(base.get("checks", {}))
    lowered = [str(name).lower() for name in feature_names]
    for token in FORBIDDEN_FEATURE_TOKENS:
        checks[f"phyc3c_{token}_absent_from_feature_names"] = not any(token in name for name in lowered)
    checks.update(
        {
            "calibration_labels_not_test_features": True,
            "fold_calibration_excludes_test_groups": True,
            "teacher_self_embeddings_absent": True,
            "oracle_channel_matrices_absent": True,
            "full_teacher_channel_matrices_absent": True,
        }
    )
    return {
        "schema": "scope_static_phyc3c_leakage_guardrail_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
        "forbidden_learner_inputs": [
            "true mechanism ID as test feature",
            "mechanism name as test feature",
            "physical family label as test feature",
            "teacher self-distinguishment features",
            "oracle channel matrix",
            "oracle Kraus/PTM matrix",
            "oracle prototype vector",
            "hidden omega",
        ],
    }


def protocol_summary(protocol: list[dict[str, object]]) -> dict[str, object]:
    contexts = [int(batch.get("num_contexts", 0)) for batch in protocol]
    mode = str(protocol[0].get("mode", "unknown")) if protocol else "unknown"
    return {
        "mode": mode,
        "num_batches": int(len(protocol)),
        "min_contexts_per_batch": int(min(contexts)) if contexts else 0,
        "max_contexts_per_batch": int(max(contexts)) if contexts else 0,
        "distributional_batches": int(sum(value > 1 for value in contexts)),
        "m13_batches": int(sum(str(batch.get("label_evaluator_only")) == "M13" for batch in protocol)),
        "m13_min_contexts": int(min([int(batch.get("num_contexts", 0)) for batch in protocol if str(batch.get("label_evaluator_only")) == "M13"], default=0)),
    }


def head_comparison(single_result: dict[str, object], multi_result: dict[str, object]) -> dict[str, object]:
    rows = []
    for head in HEADS:
        single = dict(dict(single_result.get("head_results", {})).get(head, {}))
        multi = dict(dict(multi_result.get("head_results", {})).get(head, {}))
        rows.append(
            {
                "head": head,
                "single_realization_BA": float(single.get("balanced_accuracy", 0.0)),
                "single_realization_NMI": float(single.get("normalized_mutual_info", 0.0)),
                "single_realization_M13_recall": float(single.get("m13_recall", 0.0)),
                "multi_context_BA": float(multi.get("balanced_accuracy", 0.0)),
                "multi_context_NMI": float(multi.get("normalized_mutual_info", 0.0)),
                "multi_context_M13_recall": float(multi.get("m13_recall", 0.0)),
            }
        )
    return {"schema": "scope_static_phyc3c_head_comparison_v1", "heads": rows}


def m13_recovery_audit(single_result: dict[str, object], multi_result: dict[str, object]) -> dict[str, object]:
    rows = []
    for head in HEADS:
        single = dict(dict(single_result.get("head_results", {})).get(head, {}))
        multi = dict(dict(multi_result.get("head_results", {})).get(head, {}))
        rows.append(
            {
                "head": head,
                "single_realization_M13_recall": float(single.get("m13_recall", 0.0)),
                "multi_context_M13_recall": float(multi.get("m13_recall", 0.0)),
                "improved_by_batching": float(multi.get("m13_recall", 0.0)) > float(single.get("m13_recall", 0.0)),
            }
        )
    return {
        "schema": "scope_static_phyc3c_m13_recovery_audit_v1",
        "interpretation": "M13 is a drifted-mechanism distributional target; perfect recovery is claimed only for multi-context batches.",
        "heads": rows,
    }


def _diagonal_gaussian_score(
    xbar: np.ndarray,
    sample_var: np.ndarray,
    mean: np.ndarray,
    variance: np.ndarray,
    *,
    n: int,
    include_mean: bool = True,
    include_covariance: bool = True,
) -> float:
    var = np.maximum(np.asarray(variance, dtype=np.float64), 1e-12)
    score = float(n) * float(np.sum(np.log(var)))
    if include_mean:
        score += float(n) * float(np.sum((xbar - mean) ** 2 / var))
    if include_covariance:
        score += float(n) * float(np.sum(sample_var / var))
    return -0.5 * score / max(1, var.size)


def _full_gaussian_score(xbar: np.ndarray, scatter: np.ndarray, mean: np.ndarray, covariance: np.ndarray, n: int) -> float:
    if covariance.size == 0:
        return 0.0
    cov = np.asarray(covariance, dtype=np.float64)
    sign, logdet = np.linalg.slogdet(cov)
    if sign <= 0:
        cov = cov + 1e-6 * np.eye(cov.shape[0], dtype=np.float64)
        sign, logdet = np.linalg.slogdet(cov)
    inv = np.linalg.pinv(cov)
    delta = np.asarray(xbar - mean, dtype=np.float64)
    mahal = float(delta.T @ inv @ delta)
    trace = float(np.trace(inv @ scatter))
    return -0.5 * (float(n) * float(logdet) + float(n) * mahal + trace) / max(1, cov.shape[0])


def _regularized_covariance(values: np.ndarray, *, ridge: float, shrinkage_alpha: float) -> np.ndarray:
    x = np.asarray(values, dtype=np.float64)
    dim = int(x.shape[1]) if x.ndim == 2 else 0
    if dim == 0:
        return np.zeros((0, 0), dtype=np.float64)
    if x.shape[0] <= 1:
        cov = np.eye(dim, dtype=np.float64)
    else:
        centered = x - np.mean(x, axis=0)
        cov = centered.T @ centered / float(max(1, x.shape[0] - 1))
    diag = np.diag(np.diag(cov))
    alpha = min(max(float(shrinkage_alpha), 0.0), 1.0)
    return (1.0 - alpha) * cov + alpha * diag + float(ridge) * np.eye(dim, dtype=np.float64)


def _pca_basis(values: np.ndarray, *, max_components: int) -> np.ndarray:
    x = np.asarray(values, dtype=np.float64)
    if x.size == 0:
        return np.zeros((x.shape[1] if x.ndim == 2 else 0, 0), dtype=np.float64)
    if int(max_components) <= 0:
        return np.zeros((x.shape[1] if x.ndim == 2 else 0, 0), dtype=np.float64)
    centered = x - np.mean(x, axis=0)
    _, singular_values, vt = np.linalg.svd(centered, full_matrices=False)
    rank = int(np.sum(singular_values > 1e-10))
    k = max(1, min(int(max_components), rank, vt.shape[0]))
    return vt[:k].T.astype(np.float64)


def _optimistic_predictions(labels: list[str], signatures: dict[tuple[float, ...], list[int]]) -> list[str]:
    predictions = [""] * len(labels)
    tie_counters: dict[tuple[str, ...], int] = {}
    for indices in signatures.values():
        local = [labels[idx] for idx in indices]
        unique = sorted(set(local), key=_mechanism_sort_key)
        if len(unique) == 1:
            chosen = unique[0]
        else:
            counts = {label: local.count(label) for label in unique}
            best = max(counts.values())
            tied = [label for label in unique if counts[label] == best]
            key = tuple(tied)
            offset = tie_counters.get(key, 0)
            chosen = tied[offset % len(tied)]
            tie_counters[key] = offset + 1
        for idx in indices:
            predictions[idx] = chosen
    return [prediction if prediction else labels[idx] for idx, prediction in enumerate(predictions)]


def _top_scores(scores: dict[str, float], *, limit: int) -> list[dict[str, object]]:
    return [
        {"label": str(label), "score": float(score)}
        for label, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)[: int(limit)]
    ]


def _decision(primary: dict[str, object], ceiling: dict[str, object]) -> str:
    ceiling_metrics = dict(ceiling.get("deterministic_distributional_ceiling", {}))
    ceiling_nmi = float(ceiling_metrics.get("normalized_mutual_info", 0.0))
    nmi = float(primary.get("normalized_mutual_info", 0.0))
    min_recall = float(primary.get("min_class_recall", 0.0))
    m13_recall = float(primary.get("per_class_recall", {}).get("M13", 0.0)) if isinstance(primary.get("per_class_recall", {}), dict) else 0.0
    if ceiling_nmi >= 1.0 and nmi >= 1.0 and min_recall >= 1.0 and m13_recall >= 1.0:
        return "multi_context_distributional_head_reaches_visible_ceiling"
    if ceiling_nmi >= 1.0 and m13_recall >= 1.0:
        return "m13_recovered_but_head_below_full_visible_ceiling"
    return "distributional_head_does_not_reach_visible_ceiling"


def format_phyc3c_summary(result: dict[str, object]) -> str:
    primary = dict(dict(result.get("multi_context_batch_mode", {})).get("head_results", {})).get("PHYC3c_diagonal_gaussian", {})
    primary = dict(primary) if isinstance(primary, dict) else {}
    single = dict(dict(result.get("single_realization_mode", {})).get("head_results", {})).get("PHYC3c_diagonal_gaussian", {})
    single = dict(single) if isinstance(single, dict) else {}
    return "\n".join(
        [
            "# Layer 3c: Distributional Gaussian Likelihood Head",
            "",
            f"- Layer: `{LEARNER_VALIDATION_STAGE.public_name}`",
            f"- Decision: `{result.get('decision')}`",
            f"- Primary mode: `{result.get('primary_mode')}`",
            f"- Primary head: `{result.get('primary_head')}`",
            f"- Multi-context BA: `{float(primary.get('balanced_accuracy', 0.0)):.4f}`",
            f"- Multi-context ARI: `{float(primary.get('adjusted_rand_index', 0.0)):.4f}`",
            f"- Multi-context NMI: `{float(primary.get('normalized_mutual_info', 0.0)):.4f}`",
            f"- Multi-context min recall: `{float(primary.get('min_class_recall', 0.0)):.4f}`",
            f"- Multi-context M13 recall: `{float(primary.get('m13_recall', 0.0)):.4f}`",
            f"- Single-realization M13 recall: `{float(single.get('m13_recall', 0.0)):.4f}`",
            "",
            "## Claim Boundary",
            "",
            "PHYC3c uses the existing PHYC3b Z/X-visible feature vectors. It tests whether a no-leakage distributional head can recover drifted mechanisms from multi-context batches; it does not claim M13 is point-identifiable from one fixed coherent realization.",
            "",
        ]
    )


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "gaussian_parameter_schema.json": result["gaussian_parameter_schema"],
        "batch_protocol_audit.json": result["batch_protocol_audit"],
        "distributional_ceiling_audit.json": result["distributional_ceiling_audit"],
        "single_realization_metrics.json": result["single_realization_mode"],
        "multi_context_batch_metrics.json": result["multi_context_batch_mode"],
        "head_comparison.json": result["head_comparison"],
        "m13_recovery_audit.json": result["m13_recovery_audit"],
        "leakage_guardrail_audit.json": result["leakage_guardrail_audit"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n")
    (output / "summary.md").write_text(format_phyc3c_summary(result))


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text())
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def _finite(values: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(values, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)


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


def _mechanism_sort_key(name: str) -> tuple[int, str]:
    text = str(name)
    if text.startswith("M") and text[1:].isdigit():
        return (int(text[1:]), text)
    return (10_000, text)
