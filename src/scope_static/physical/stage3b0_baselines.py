from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import yaml

from scope_static.metrics import adjusted_rand_index, normalized_mutual_info

from .layers import LAYER3_LEARNER
from .stage3a5_observability_ceiling import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A5_DIR
from .stage3a5_observability_ceiling import _feature_schema_matches_s3a
from .stage3a_protocol_freeze import DEFAULT_OUTPUT_DIR as DEFAULT_STAGE3A_DIR
from .stage3a_protocol_freeze import load_stage3a_frozen_visible_features


STAGE_NAME = "Stage3B0_nonlearned_clustering_baselines"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/PHYC_STAGE3_discovery/S3B0_nonlearned_clustering_baselines"
DEFAULT_MAX_ITER = 30
DEFAULT_SEED = 0
DEFAULT_MAX_FULL_COV_FEATURES = 24
VARIANCE_FLOOR = 1.0e-6


def run_stage3b0_nonlearned_clustering_baselines(
    *,
    stage3a_dir: str | Path = DEFAULT_STAGE3A_DIR,
    stage3a5_dir: str | Path = DEFAULT_STAGE3A5_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    teacher_dir: str | Path | None = None,
    seed: int = DEFAULT_SEED,
    max_iter: int = DEFAULT_MAX_ITER,
    max_full_cov_features: int = DEFAULT_MAX_FULL_COV_FEATURES,
) -> dict[str, object]:
    """Run visible-only Stage 3B.0 clustering baselines.

    This stage fits no supervised classifier and performs no model selection
    using labels. Mechanism and quotient labels are used only after fitting for
    evaluator-only metrics.
    """

    s3a = Path(stage3a_dir)
    s3a5 = Path(stage3a5_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    s3a_metrics = _load_json(s3a / "metrics.json")
    s3a5_metrics = _load_json(s3a5 / "metrics.json")
    s3a_config = dict(s3a_metrics.get("config", {})) if isinstance(s3a_metrics.get("config", {}), dict) else {}
    teacher = Path(teacher_dir) if teacher_dir is not None else Path(str(s3a_config.get("teacher_dir", "")))
    if not str(teacher):
        raise ValueError("teacher_dir is required either directly or through Stage 3A metrics.json")

    x_raw, feature_names, feature_matrix = load_stage3a_frozen_visible_features(s3a)
    x, standardization = _standardize_visible_features(x_raw)
    alias = dict(s3a5_metrics.get("oracle_alias_classes", {})) if isinstance(s3a5_metrics.get("oracle_alias_classes", {}), dict) else {}
    label_to_quotient = {str(k): str(v) for k, v in dict(alias.get("label_to_quotient", {})).items()}
    mechanism_scope = dict(s3a_metrics.get("mechanism_scope", {})) if isinstance(s3a_metrics.get("mechanism_scope", {}), dict) else {}
    class_count = int(mechanism_scope.get("class_count_evaluator_only", max(1, x_raw.shape[0])))
    quotient_class_count = int(alias.get("quotient_class_count", class_count))
    feature_match = _feature_schema_matches_s3a(s3a, feature_names)
    k_runs = k_selection_runs(
        record_count=int(x_raw.shape[0]),
        class_count=class_count,
        quotient_class_count=quotient_class_count,
    )
    rng = np.random.default_rng(int(seed))
    baseline_results = []
    assignment_arrays: dict[str, np.ndarray] = {}
    fitted_rows: list[tuple[dict[str, object], np.ndarray]] = []
    for run in k_runs:
        k = int(run["k"])
        if k <= 0:
            continue
        for baseline_name, assignments, objective in _run_baselines_for_k(
            x,
            k=k,
            rng=rng,
            max_iter=int(max_iter),
            max_full_cov_features=int(max_full_cov_features),
        ):
            key = f"{baseline_name}__{run['mode']}"
            row = {
                "baseline_name": baseline_name,
                "k_mode": run["mode"],
                "k": k,
                "used_mechanism_labels_for_fit": False,
                "used_labels_for_model_selection": False,
                "objective": objective,
            }
            fitted_rows.append((row, assignments))
            assignment_arrays[_safe_npz_key(key)] = _one_hot(assignments, k=int(max(int(np.max(assignments)) + 1 if assignments.size else 1, k)))
    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")
    labels = [str(record.get("oracle_label", record.get("mechanism_id", ""))) for record in records]
    if len(labels) != int(x_raw.shape[0]):
        raise ValueError(f"Stage 3A frozen feature row count {x_raw.shape[0]} does not match evaluator label count {len(labels)}")
    class_names = sorted(set(labels), key=_mechanism_sort_key)
    quotient_labels = [label_to_quotient.get(label, label) for label in labels]
    quotient_class_names = sorted(set(quotient_labels), key=_mechanism_sort_key)
    for row, assignments in fitted_rows:
        metrics = evaluate_cluster_assignments(
            assignments,
            exact_labels=labels,
            exact_class_names=class_names,
            quotient_labels=quotient_labels,
            quotient_class_names=quotient_class_names,
        )
        row.update(metrics)
        baseline_results.append(row)
    control_results = [row for row in baseline_results if row["baseline_name"] in {"global_null_control", "mean_only_control"}]
    primary = _select_primary_baseline(baseline_results)
    primary_assignments = assignment_arrays[_safe_npz_key(str(primary["assignment_key"]))] if primary else np.zeros((int(x_raw.shape[0]), 1), dtype=np.float64)
    learned_summary = learned_assignment_summary(primary, primary_assignments)
    evaluator_metrics = {
        "schema": "scope_static_stage3b0_evaluator_only_label_metrics_v1",
        "baseline_metrics": [
            {
                "baseline_name": row["baseline_name"],
                "k_mode": row["k_mode"],
                "exact": row["exact_label_metrics"],
                "quotient": row["quotient_label_metrics"],
            }
            for row in baseline_results
        ],
    }
    quotient_metrics = {
        "schema": "scope_static_stage3b0_quotient_metrics_v1",
        "quotient_class_count": int(len(quotient_class_names)),
        "baseline_metrics": [
            {
                "baseline_name": row["baseline_name"],
                "k_mode": row["k_mode"],
                **row["quotient_label_metrics"],
            }
            for row in baseline_results
        ],
    }
    model_selection = model_selection_audit(primary)
    acceptance = stage3b0_acceptance_audit(
        s3a_metrics=s3a_metrics,
        s3a5_metrics=s3a5_metrics,
        feature_match=feature_match,
        feature_matrix=feature_matrix,
        baseline_results=baseline_results,
        model_selection=model_selection,
    )
    result = {
        "schema": "scope_static_stage3b0_nonlearned_clustering_baselines_v1",
        "stage": STAGE_NAME,
        "public_layer": LAYER3_LEARNER.metadata(artifact_stage=STAGE_NAME, substage="nonlearned_clustering_baselines"),
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
            "max_full_cov_features": int(max_full_cov_features),
        },
        "visible_feature_matrix": feature_matrix,
        "visible_feature_standardization": standardization,
        "feature_schema_match_audit": feature_match,
        "k_selection_protocol": {
            "schema": "scope_static_stage3b0_k_selection_protocol_v1",
            "runs": k_runs,
            "uses_catalog_cardinality_only_not_labels": True,
            "uses_quotient_count_from_stage3a5": True,
        },
        "baseline_results": baseline_results,
        "controls": {
            "schema": "scope_static_stage3b0_controls_v1",
            "controls": control_results,
        },
        "learned_assignment_summary": learned_summary,
        "evaluator_only_label_metrics": evaluator_metrics,
        "quotient_metrics": quotient_metrics,
        "model_selection_audit": model_selection,
        "acceptance_audit": acceptance,
        "decision": "stage3b0_baselines_completed" if acceptance["passed"] else "stage3b0_baselines_failed",
    }
    _write_outputs(output, result, primary_assignments, assignment_arrays)
    return result


def k_selection_runs(*, record_count: int, class_count: int, quotient_class_count: int) -> list[dict[str, object]]:
    count = max(1, int(record_count))
    fixed = max(1, min(int(class_count), count))
    overcomplete = max(1, min(2 * int(class_count), count))
    quotient = max(1, min(int(quotient_class_count), count))
    runs = [
        {"mode": "fixed_oracle_count", "k": fixed, "description": "K equals evaluator-declared catalog cardinality, not labels."},
        {"mode": "overcomplete_2x", "k": overcomplete, "description": "K_max equals twice catalog cardinality, capped by record count."},
        {"mode": "quotient_count", "k": quotient, "description": "K equals Stage 3A.5 observable quotient count."},
    ]
    deduped = []
    seen = set()
    for row in runs:
        key = (row["mode"], int(row["k"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def evaluate_cluster_assignments(
    assignments: np.ndarray,
    *,
    exact_labels: list[str],
    exact_class_names: list[str],
    quotient_labels: list[str],
    quotient_class_names: list[str],
) -> dict[str, object]:
    cluster_labels = [f"C{int(value):03d}" for value in assignments.tolist()]
    exact = _cluster_metrics(exact_labels, cluster_labels, exact_class_names)
    quotient = _cluster_metrics(quotient_labels, cluster_labels, quotient_class_names)
    masses = {label: int(cluster_labels.count(label)) for label in sorted(set(cluster_labels))}
    probs = np.asarray(list(masses.values()), dtype=np.float64)
    probs = probs / max(float(np.sum(probs)), 1.0)
    entropy = float(-np.sum([p * np.log(p) for p in probs if p > 0.0]))
    return {
        "active_cluster_count": int(len(masses)),
        "assignment_entropy": entropy,
        "cluster_masses": masses,
        "exact_label_metrics": exact,
        "quotient_label_metrics": quotient,
    }


def learned_assignment_summary(primary: dict[str, object] | None, assignments: np.ndarray) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3b0_learned_assignment_summary_v1",
        "source": "Stage 3B.0 non-learned visible-only baseline",
        "primary_baseline": None if primary is None else primary.get("baseline_name"),
        "primary_k_mode": None if primary is None else primary.get("k_mode"),
        "assignment_matrix_shape": [int(assignments.shape[0]), int(assignments.shape[1])],
        "row_stochastic": bool(assignments.size == 0 or np.allclose(np.sum(assignments, axis=1), 1.0)),
        "compressed_claim_allowed": False,
    }


def model_selection_audit(primary: dict[str, object] | None) -> dict[str, object]:
    return {
        "schema": "scope_static_stage3b0_model_selection_audit_v1",
        "accepted_discovery_model_selected": False,
        "primary_baseline_for_artifact": None if primary is None else primary.get("baseline_name"),
        "primary_baseline_selection_rule": "fixed priority among visible-only baselines; evaluator metrics are reported after fit only",
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


def stage3b0_acceptance_audit(
    *,
    s3a_metrics: dict[str, object],
    s3a5_metrics: dict[str, object],
    feature_match: dict[str, object],
    feature_matrix: dict[str, object],
    baseline_results: list[dict[str, object]],
    model_selection: dict[str, object],
) -> dict[str, object]:
    names = {str(row.get("baseline_name")) for row in baseline_results}
    checks = {
        "stage3a_acceptance_passed": bool(dict(s3a_metrics.get("acceptance_audit", {})).get("passed", False)),
        "stage3a5_acceptance_passed": bool(dict(s3a5_metrics.get("acceptance_audit", {})).get("passed", False)),
        "approved_feature_schema_matches_stage3a": bool(feature_match.get("passed", False)),
        "uses_stage3a_frozen_visible_features_for_fit": bool(feature_matrix.get("loaded_from_stage3a_artifact", False)),
        "gaussian_diagonal_baseline_run": "gaussian_mixture_diagonal" in names,
        "gaussian_full_baseline_run": "gaussian_mixture_full" in names,
        "kmeans_baseline_run": "kmeans_visible" in names,
        "global_null_control_run": "global_null_control" in names,
        "mean_only_control_run": "mean_only_control" in names,
        "evaluator_metrics_reported_after_fit": all("exact_label_metrics" in row and "quotient_label_metrics" in row for row in baseline_results),
        "validation_label_model_selection_count_is_zero": not bool(model_selection.get("validation_ari_used_for_selection", True)),
        "test_label_model_selection_count_is_zero": not bool(model_selection.get("test_ari_used_for_selection", True)),
        "oracle_label_prototype_quality_not_used_for_selection": not bool(model_selection.get("oracle_label_prototype_quality_used_for_selection", True)),
    }
    return {
        "schema": "scope_static_stage3b0_acceptance_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
    }


def _run_baselines_for_k(
    x: np.ndarray,
    *,
    k: int,
    rng: np.random.Generator,
    max_iter: int,
    max_full_cov_features: int,
) -> list[tuple[str, np.ndarray, dict[str, object]]]:
    n = int(x.shape[0])
    active_k = max(1, min(int(k), max(1, n)))
    outputs: list[tuple[str, np.ndarray, dict[str, object]]] = []
    global_assignments = np.zeros(n, dtype=np.int64)
    outputs.append(("global_null_control", global_assignments, {"visible_objective": "single_cluster_null"}))
    outputs.append(("mean_only_control", global_assignments.copy(), {"visible_objective": "global_mean_only"}))
    kmeans_assignments, kmeans_centers, inertia = _kmeans(x, active_k, max_iter=max_iter)
    outputs.append(("kmeans_visible", kmeans_assignments, {"visible_objective": "within_cluster_sse", "inertia": float(inertia)}))
    diag_assignments, diag_nll = _gmm_diagonal(x, active_k, init_centers=kmeans_centers, max_iter=max_iter)
    outputs.append(("gaussian_mixture_diagonal", diag_assignments, {"visible_objective": "diagonal_gaussian_mixture_nll", "nll": float(diag_nll)}))
    x_full, selected = _select_high_variance_columns(x, max_features=int(max_full_cov_features))
    full_centers = kmeans_centers[:, selected] if selected else np.zeros((active_k, 0), dtype=np.float64)
    full_assignments, full_nll = _gmm_full(x_full, active_k, init_centers=full_centers, max_iter=max(3, min(int(max_iter), 15)))
    outputs.append(
        (
            "gaussian_mixture_full",
            full_assignments,
            {
                "visible_objective": "full_covariance_gaussian_mixture_nll",
                "nll": float(full_nll),
                "selected_visible_feature_count": int(len(selected)),
            },
        )
    )
    return outputs


def _kmeans(x: np.ndarray, k: int, *, max_iter: int) -> tuple[np.ndarray, np.ndarray, float]:
    n, d = x.shape
    if n == 0:
        return np.zeros(0, dtype=np.int64), np.zeros((max(1, k), d), dtype=np.float64), 0.0
    centers = _farthest_first_centers(x, k)
    assignments = np.zeros(n, dtype=np.int64)
    for _ in range(max(1, int(max_iter))):
        distances = _squared_distances(x, centers)
        new_assignments = np.argmin(distances, axis=1).astype(np.int64)
        new_centers = centers.copy()
        for idx in range(k):
            mask = new_assignments == idx
            if np.any(mask):
                new_centers[idx] = np.mean(x[mask], axis=0)
        if np.array_equal(new_assignments, assignments) and np.allclose(new_centers, centers):
            centers = new_centers
            assignments = new_assignments
            break
        centers = new_centers
        assignments = new_assignments
    inertia = float(np.sum(np.min(_squared_distances(x, centers), axis=1)))
    return assignments, centers, inertia


def _gmm_diagonal(x: np.ndarray, k: int, *, init_centers: np.ndarray, max_iter: int) -> tuple[np.ndarray, float]:
    n, d = x.shape
    if n == 0:
        return np.zeros(0, dtype=np.int64), 0.0
    means = np.asarray(init_centers, dtype=np.float64).copy()
    variances = np.ones((k, d), dtype=np.float64)
    weights = np.full(k, 1.0 / float(k), dtype=np.float64)
    log_resp = np.zeros((n, k), dtype=np.float64)
    nll = 0.0
    for _ in range(max(1, int(max_iter))):
        log_prob = _diag_log_prob(x, means, variances) + np.log(np.maximum(weights, 1.0e-12))[None, :]
        norm = _logsumexp(log_prob, axis=1)
        log_resp = log_prob - norm[:, None]
        resp = np.exp(log_resp)
        nk = np.maximum(np.sum(resp, axis=0), 1.0e-12)
        weights = nk / float(n)
        means = (resp.T @ x) / nk[:, None]
        for idx in range(k):
            diff = x - means[idx]
            variances[idx] = np.maximum((resp[:, idx][:, None] * diff * diff).sum(axis=0) / nk[idx], VARIANCE_FLOOR)
        nll = float(-np.mean(norm))
    return np.argmax(log_resp, axis=1).astype(np.int64), nll


def _gmm_full(x: np.ndarray, k: int, *, init_centers: np.ndarray, max_iter: int) -> tuple[np.ndarray, float]:
    n, d = x.shape
    if n == 0:
        return np.zeros(0, dtype=np.int64), 0.0
    if d == 0:
        return np.zeros(n, dtype=np.int64), 0.0
    means = np.asarray(init_centers, dtype=np.float64).copy()
    covariances = np.stack([np.eye(d, dtype=np.float64) for _ in range(k)], axis=0)
    weights = np.full(k, 1.0 / float(k), dtype=np.float64)
    log_resp = np.zeros((n, k), dtype=np.float64)
    nll = 0.0
    for _ in range(max(1, int(max_iter))):
        log_prob = _full_log_prob(x, means, covariances) + np.log(np.maximum(weights, 1.0e-12))[None, :]
        norm = _logsumexp(log_prob, axis=1)
        log_resp = log_prob - norm[:, None]
        resp = np.exp(log_resp)
        nk = np.maximum(np.sum(resp, axis=0), 1.0e-12)
        weights = nk / float(n)
        means = (resp.T @ x) / nk[:, None]
        for idx in range(k):
            diff = x - means[idx]
            cov = (diff * resp[:, idx][:, None]).T @ diff / nk[idx]
            covariances[idx] = cov + np.eye(d, dtype=np.float64) * VARIANCE_FLOOR
        nll = float(-np.mean(norm))
    return np.argmax(log_resp, axis=1).astype(np.int64), nll


def _cluster_metrics(true_labels: list[str], cluster_labels: list[str], class_names: list[str]) -> dict[str, object]:
    cluster_names = sorted(set(cluster_labels))
    mapping = _greedy_cluster_label_match(true_labels, cluster_labels, class_names, cluster_names)
    predicted = [mapping.get(cluster, "__unmatched__") for cluster in cluster_labels]
    support = {name: 0 for name in class_names}
    correct = {name: 0 for name in class_names}
    for true, pred in zip(true_labels, predicted):
        if true in support:
            support[true] += 1
            if true == pred:
                correct[true] += 1
    recalls = [float(correct[name]) / float(support[name]) if support[name] else 0.0 for name in class_names]
    true_ids = _encode_partition(true_labels)
    cluster_ids = _encode_partition(cluster_labels)
    return {
        "balanced_accuracy_after_label_matching": float(np.mean(recalls)) if recalls else 0.0,
        "min_recall_after_label_matching": float(min(recalls)) if recalls else 0.0,
        "adjusted_rand_index": float(adjusted_rand_index(true_ids, cluster_ids)),
        "normalized_mutual_info": float(normalized_mutual_info(true_ids, cluster_ids)),
        "cluster_to_label_match": mapping,
        "support": {name: int(value) for name, value in support.items()},
    }


def _greedy_cluster_label_match(
    true_labels: list[str],
    cluster_labels: list[str],
    class_names: list[str],
    cluster_names: list[str],
) -> dict[str, str]:
    counts = []
    for cluster in cluster_names:
        for label in class_names:
            count = sum(1 for a, b in zip(true_labels, cluster_labels) if a == label and b == cluster)
            counts.append((count, cluster, label))
    counts.sort(key=lambda row: (-row[0], row[1], row[2]))
    used_clusters: set[str] = set()
    used_labels: set[str] = set()
    mapping: dict[str, str] = {}
    for count, cluster, label in counts:
        if count <= 0 or cluster in used_clusters or label in used_labels:
            continue
        mapping[cluster] = label
        used_clusters.add(cluster)
        used_labels.add(label)
    return mapping


def _select_primary_baseline(rows: list[dict[str, object]]) -> dict[str, object] | None:
    priority = [
        ("kmeans_visible", "fixed_oracle_count"),
        ("gaussian_mixture_diagonal", "fixed_oracle_count"),
        ("gaussian_mixture_full", "fixed_oracle_count"),
        ("kmeans_visible", "quotient_count"),
    ]
    for baseline, mode in priority:
        for row in rows:
            if row.get("baseline_name") == baseline and row.get("k_mode") == mode:
                out = dict(row)
                out["assignment_key"] = f"{baseline}__{mode}"
                return out
    if not rows:
        return None
    out = dict(rows[0])
    out["assignment_key"] = f"{out.get('baseline_name')}__{out.get('k_mode')}"
    return out


def _standardize_visible_features(x: np.ndarray) -> tuple[np.ndarray, dict[str, object]]:
    mean = np.mean(x, axis=0) if x.size else np.zeros(x.shape[1], dtype=np.float64)
    scale = np.std(x, axis=0) if x.size else np.ones(x.shape[1], dtype=np.float64)
    scale = np.where(scale > 1.0e-12, scale, 1.0)
    z = (x - mean) / scale if x.size else x
    return z, {
        "schema": "scope_static_stage3b0_visible_feature_standardization_v1",
        "method": "feature-wise z-score over visible instances",
        "feature_count": int(x.shape[1]) if x.ndim == 2 else 0,
        "zero_scale_replaced_with_one": True,
    }


def _farthest_first_centers(x: np.ndarray, k: int) -> np.ndarray:
    n, d = x.shape
    first = int(np.argmax(np.sum(x * x, axis=1))) if n else 0
    centers = [x[first].copy()] if n else [np.zeros(d, dtype=np.float64)]
    while len(centers) < k:
        distances = _squared_distances(x, np.asarray(centers, dtype=np.float64))
        min_dist = np.min(distances, axis=1)
        idx = int(np.argmax(min_dist))
        if any(np.allclose(x[idx], center) for center in centers):
            centers.append(x[len(centers) % max(1, n)].copy())
        else:
            centers.append(x[idx].copy())
    return np.asarray(centers, dtype=np.float64)


def _squared_distances(x: np.ndarray, centers: np.ndarray) -> np.ndarray:
    diff = x[:, None, :] - centers[None, :, :]
    return np.sum(diff * diff, axis=2)


def _diag_log_prob(x: np.ndarray, means: np.ndarray, variances: np.ndarray) -> np.ndarray:
    n, d = x.shape
    k = int(means.shape[0])
    if k == 0:
        return np.zeros((n, 0), dtype=np.float64)
    out = np.empty((n, k), dtype=np.float64)
    max_elements = 20_000_000
    chunk = max(1, min(k, max_elements // max(1, n * max(1, d))))
    for start in range(0, k, chunk):
        stop = min(k, start + chunk)
        local_var = variances[start:stop]
        diff = x[:, None, :] - means[None, start:stop, :]
        log_norm = np.sum(np.log(2.0 * np.pi * local_var), axis=1)
        quad = np.sum(diff * diff / local_var[None, :, :], axis=2)
        out[:, start:stop] = -0.5 * (log_norm[None, :] + quad)
    return out


def _full_log_prob(x: np.ndarray, means: np.ndarray, covariances: np.ndarray) -> np.ndarray:
    d = x.shape[1]
    rows = []
    for mean, cov in zip(means, covariances):
        sign, logdet = np.linalg.slogdet(cov)
        if sign <= 0:
            cov = cov + np.eye(d, dtype=np.float64) * VARIANCE_FLOOR
            sign, logdet = np.linalg.slogdet(cov)
        inv = np.linalg.pinv(cov)
        diff = x - mean
        quad = np.sum((diff @ inv) * diff, axis=1)
        rows.append(-0.5 * (d * np.log(2.0 * np.pi) + float(logdet) + quad))
    return np.asarray(rows, dtype=np.float64).T if rows else np.zeros((x.shape[0], 0), dtype=np.float64)


def _logsumexp(x: np.ndarray, *, axis: int) -> np.ndarray:
    peak = np.max(x, axis=axis, keepdims=True)
    return np.squeeze(peak, axis=axis) + np.log(np.sum(np.exp(x - peak), axis=axis))


def _select_high_variance_columns(x: np.ndarray, *, max_features: int) -> tuple[np.ndarray, list[int]]:
    if x.size == 0:
        return x, []
    count = max(1, min(int(max_features), x.shape[1]))
    variance = np.var(x, axis=0)
    indices = np.argsort(-variance)[:count]
    indices = np.asarray(sorted(int(idx) for idx in indices.tolist()), dtype=np.int64)
    return x[:, indices], [int(idx) for idx in indices.tolist()]


def _one_hot(assignments: np.ndarray, *, k: int) -> np.ndarray:
    out = np.zeros((int(assignments.size), int(max(1, k))), dtype=np.float64)
    for row, cluster in enumerate(assignments.tolist()):
        out[int(row), int(cluster)] = 1.0
    return out


def _encode_partition(labels: list[str]) -> list[int]:
    mapping: dict[str, int] = {}
    out = []
    for label in labels:
        if label not in mapping:
            mapping[label] = len(mapping)
        out.append(mapping[label])
    return out


def _write_outputs(output: Path, result: dict[str, object], primary_assignments: np.ndarray, assignment_arrays: dict[str, np.ndarray]) -> None:
    artifacts = {
        "metrics.json": result,
        "baseline_results.json": result["baseline_results"],
        "learned_assignment_summary.json": result["learned_assignment_summary"],
        "controls.json": result["controls"],
        "evaluator_only_label_metrics.json": result["evaluator_only_label_metrics"],
        "quotient_metrics.json": result["quotient_metrics"],
        "model_selection_audit.json": result["model_selection_audit"],
        "acceptance_audit.json": result["acceptance_audit"],
        "feature_schema_match_audit.json": result["feature_schema_match_audit"],
        "visible_feature_matrix.json": result["visible_feature_matrix"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    np.save(output / "learned_assignments.npy", primary_assignments)
    np.savez(output / "baseline_assignments.npz", **assignment_arrays)
    (output / "config.yaml").write_text(yaml.safe_dump({"stage3b0_nonlearned_clustering_baselines": result["config"]}, sort_keys=False))
    (output / "summary.md").write_text(format_stage3b0_summary(result))


def format_stage3b0_summary(result: dict[str, object]) -> str:
    acceptance = dict(result.get("acceptance_audit", {}))
    summary = dict(result.get("learned_assignment_summary", {}))
    primary = summary.get("primary_baseline")
    metrics = None
    for row in result.get("baseline_results", []):
        if isinstance(row, dict) and row.get("baseline_name") == primary and row.get("k_mode") == summary.get("primary_k_mode"):
            metrics = row
            break
    exact = dict(metrics.get("exact_label_metrics", {})) if isinstance(metrics, dict) else {}
    quotient = dict(metrics.get("quotient_label_metrics", {})) if isinstance(metrics, dict) else {}
    return "\n".join(
        [
            "# Stage 3B.0: Non-Learned Clustering Baselines",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Acceptance passed: `{str(bool(acceptance.get('passed', False))).lower()}`",
            f"- Primary baseline: `{summary.get('primary_baseline')}`",
            f"- Primary K mode: `{summary.get('primary_k_mode')}`",
            f"- Exact-label NMI: `{float(exact.get('normalized_mutual_info', 0.0)):.4f}`",
            f"- Quotient-label NMI: `{float(quotient.get('normalized_mutual_info', 0.0)):.4f}`",
            "",
            "## Claim Boundary",
            "",
            "Stage 3B.0 reports visible-only non-learned baselines. Evaluator labels are used only after fitting for ARI/NMI/BA/min-recall audits, and no accepted discovery model is selected at this stage.",
            "",
        ]
    )


def _load_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = _load_json(path)
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def _safe_npz_key(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in str(value))


def _mechanism_sort_key(label: str) -> tuple[int, str]:
    text = str(label)
    if text.startswith("M") and text[1:].isdigit():
        return (int(text[1:]), text)
    return (10_000, text)
