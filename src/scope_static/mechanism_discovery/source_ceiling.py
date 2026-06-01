from __future__ import annotations

from collections import Counter, defaultdict
import json
import math
from pathlib import Path
from typing import Mapping

import numpy as np
import yaml

from scope_static.dem.metrics import adjusted_rand_index, normalized_mutual_info

from .baselines import _kmeans, _run_baselines_for_k, _standardize_visible_features, evaluate_cluster_assignments
from .discovery_model import run_stage3b1_first_discovery_model
from .stage4_artifacts import (
    load_stage4_source_evaluator_labels,
    load_stage4_visible_matrix,
    mechanism_sort_key,
    validate_stage4_source_label_separation,
)


STAGE_NAME = "Stage4_0_5_source_surface_survival_audit"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/S4_bridge/S4_0_5_source_surface_survival_audit"
PASS_EXACT_NMI = 0.80
PASS_QUOTIENT_NMI = 0.70


def run_stage4_source_surface_survival_audit(
    *,
    stage4_source_dir: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    seed: int = 0,
    max_iter: int = 30,
    stage3b1_output_dir: str | Path | None = None,
) -> dict[str, object]:
    """Audit whether controlled mechanism structure survives the S4.0 projection."""

    source = Path(stage4_source_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    x_raw, feature_names, feature_matrix = load_stage4_visible_matrix(source)
    x, standardization = _standardize_visible_features(x_raw)
    labels = load_stage4_source_evaluator_labels(source)
    if len(labels.exact_labels) != int(x.shape[0]):
        raise ValueError("source evaluator label count must match visible feature row count")
    class_count = max(1, len(labels.exact_class_names))
    quotient_count = max(1, len(labels.quotient_class_names))
    rng = np.random.default_rng(int(seed))
    baseline_rows = []
    primary_assignments = np.zeros(int(x.shape[0]), dtype=np.int64)
    for mode, k in [("exact_count", class_count), ("quotient_count", quotient_count), ("overcomplete_2x", min(max(1, x.shape[0]), 2 * class_count))]:
        for name, assignments, objective in _run_baselines_for_k(
            x,
            k=max(1, min(int(k), max(1, x.shape[0]))),
            rng=rng,
            max_iter=int(max_iter),
            max_full_cov_features=min(24, max(1, x.shape[1])),
        ):
            metrics = evaluate_cluster_assignments(
                assignments,
                exact_labels=labels.exact_labels,
                exact_class_names=labels.exact_class_names,
                quotient_labels=labels.quotient_labels,
                quotient_class_names=labels.quotient_class_names,
            )
            row = {"baseline_name": name, "k_mode": mode, "k": int(k), "objective": objective, **metrics}
            baseline_rows.append(row)
            if name == "kmeans_visible" and mode == "exact_count":
                primary_assignments = np.asarray(assignments, dtype=np.int64)
    stage3b1 = _run_stage3b1_probe(source, output, stage3b1_output_dir=stage3b1_output_dir, seed=int(seed), max_iter=max(5, min(int(max_iter), 20)))
    linear = _nearest_centroid_probe(x, labels.exact_labels)
    knn = _knn_probe(x, labels.exact_labels)
    purity = _prototype_purity(primary_assignments, labels.exact_labels)
    silhouette = _silhouette_by_label(x, labels.exact_labels)
    block_mi = _blockwise_mutual_information(x_raw, feature_names, labels.exact_labels)
    collapse = _projection_collapse_matrix(x, labels.exact_labels)
    alias = _alias_classes(collapse)
    exact_metrics = _partition_metrics(primary_assignments, labels.exact_labels, labels.exact_class_names)
    quotient_metrics = _partition_metrics(primary_assignments, labels.quotient_labels, labels.quotient_class_names)
    decision = _surface_decision(exact_metrics, quotient_metrics, alias)
    label_separation = validate_stage4_source_label_separation(source)
    mechanism_survival = {
        "schema": "scope_static_stage4_mechanism_survival_report_v1",
        "decision": decision,
        "visible_ceiling": exact_metrics,
        "quotient_ceiling": quotient_metrics,
        "source_label_linear_probe_accuracy": linear["accuracy"],
        "source_label_knn_accuracy": knn["accuracy"],
        "prototype_purity": purity,
        "silhouette_by_mechanism_label": silhouette,
        "blockwise_mutual_information_with_evaluator_labels": block_mi,
        "alias_class_map": alias["alias_class_map"],
        "mechanism_collapse_matrix": collapse,
        "uses_labels_for_training": False,
        "uses_labels_for_validation_selection": False,
    }
    adequacy = {
        "schema": "scope_static_stage4_source_projection_adequacy_v1",
        "passed": bool(decision != "bridge_surface_fail" and label_separation["passed"]),
        "decision": decision,
        "label_separation_audit": label_separation,
        "visible_feature_matrix": feature_matrix,
    }
    result = {
        "schema": "scope_static_stage4_source_surface_survival_audit_v1",
        "stage": STAGE_NAME,
        "stage4_source_dir": str(source),
        "output_dir": str(output),
        "config": {
            "stage4_source_dir": str(source),
            "output_dir": str(output),
            "seed": int(seed),
            "max_iter": int(max_iter),
        },
        "visible_feature_standardization": standardization,
        "mechanism_survival_report": mechanism_survival,
        "alias_ceiling": {
            "schema": "scope_static_stage4_alias_ceiling_v1",
            "exact": exact_metrics,
            "quotient": quotient_metrics,
            "alias_classes": alias,
        },
        "projection_collapse_matrix": collapse,
        "source_visible_ceiling": {
            "schema": "scope_static_stage4_source_visible_ceiling_v1",
            "visible_ceiling_ari": exact_metrics["adjusted_rand_index"],
            "visible_ceiling_nmi": exact_metrics["normalized_mutual_info"],
            "quotient_ceiling_ari": quotient_metrics["adjusted_rand_index"],
            "quotient_ceiling_nmi": quotient_metrics["normalized_mutual_info"],
        },
        "source_alias_classes": alias,
        "source_baseline_results": {
            "schema": "scope_static_stage4_source_baseline_results_v1",
            "baselines": baseline_rows,
            "linear_probe": linear,
            "knn_probe": knn,
            "stage3b1_probe": stage3b1,
        },
        "source_projection_adequacy": adequacy,
        "decision": decision,
    }
    _write_outputs(output, result)
    return result


def _run_stage3b1_probe(source: Path, output: Path, *, stage3b1_output_dir: str | Path | None, seed: int, max_iter: int) -> dict[str, object]:
    target = Path(stage3b1_output_dir) if stage3b1_output_dir is not None else output / "stage3b1_probe"
    try:
        result = run_stage3b1_first_discovery_model(
            stage3a_dir=source,
            output_dir=target,
            seed=int(seed),
            max_iter=int(max_iter),
            evaluator_mode="no_oracle_labels",
            k_values=(2, 4, 8),
            learner_input_profile="raw_multiview_only",
        )
    except Exception as exc:  # pragma: no cover - defensive audit path
        return {"schema": "scope_static_stage4_stage3b1_probe_v1", "skipped": True, "error": f"{type(exc).__name__}: {exc}"}
    summary = dict(result.get("learned_assignment_summary", {}))
    return {
        "schema": "scope_static_stage4_stage3b1_probe_v1",
        "skipped": False,
        "decision": result.get("decision"),
        "selected_k": summary.get("selected_k"),
        "model_family": summary.get("selected_model_family"),
        "used_labels_for_fit": False,
    }


def _partition_metrics(assignments: np.ndarray, labels: list[str], class_names: list[str]) -> dict[str, object]:
    clusters = [f"C{int(value):03d}" for value in np.asarray(assignments, dtype=np.int64).tolist()]
    left = _encode(labels)
    right = _encode(clusters)
    return {
        "adjusted_rand_index": float(adjusted_rand_index(left, right)),
        "normalized_mutual_info": float(normalized_mutual_info(left, right)),
        "class_count": int(len(class_names)),
        "cluster_count": int(len(set(clusters))),
        "used_for_training": False,
        "used_for_validation_selection": False,
    }


def _nearest_centroid_probe(x: np.ndarray, labels: list[str]) -> dict[str, object]:
    preds = []
    for idx in range(int(x.shape[0])):
        train_idx = [j for j in range(int(x.shape[0])) if j != idx]
        centroids = {
            label: np.mean(x[[j for j in train_idx if labels[j] == label]], axis=0)
            for label in sorted(set(labels))
            if any(labels[j] == label for j in train_idx)
        }
        if not centroids:
            preds.append(labels[idx])
            continue
        distances = {label: float(np.sum((x[idx] - centroid) ** 2)) for label, centroid in centroids.items()}
        preds.append(min(distances, key=distances.get))
    return {
        "schema": "scope_static_stage4_linear_probe_audit_v1",
        "probe": "leave_one_out_nearest_centroid_linear_probe",
        "accuracy": float(np.mean([pred == label for pred, label in zip(preds, labels)])) if labels else 0.0,
        "used_for_model_selection": False,
    }


def _knn_probe(x: np.ndarray, labels: list[str]) -> dict[str, object]:
    preds = []
    for idx in range(int(x.shape[0])):
        candidates = [j for j in range(int(x.shape[0])) if j != idx]
        if not candidates:
            preds.append(labels[idx])
            continue
        nearest = min(candidates, key=lambda j: float(np.sum((x[idx] - x[j]) ** 2)))
        preds.append(labels[nearest])
    return {
        "schema": "scope_static_stage4_knn_probe_audit_v1",
        "probe": "leave_one_out_1nn",
        "accuracy": float(np.mean([pred == label for pred, label in zip(preds, labels)])) if labels else 0.0,
        "used_for_model_selection": False,
    }


def _prototype_purity(assignments: np.ndarray, labels: list[str]) -> dict[str, object]:
    clusters: dict[int, list[str]] = defaultdict(list)
    for cluster, label in zip(np.asarray(assignments, dtype=np.int64).tolist(), labels):
        clusters[int(cluster)].append(str(label))
    purities = {}
    weighted = 0.0
    total = max(1, len(labels))
    for cluster, values in clusters.items():
        count = Counter(values)
        purity = max(count.values()) / max(1, len(values))
        purities[f"C{cluster:03d}"] = float(purity)
        weighted += purity * len(values) / total
    return {"schema": "scope_static_stage4_prototype_purity_v1", "weighted_purity": float(weighted), "cluster_purity": purities}


def _silhouette_by_label(x: np.ndarray, labels: list[str]) -> dict[str, object]:
    values = []
    for idx, label in enumerate(labels):
        same = [j for j, other in enumerate(labels) if other == label and j != idx]
        other_labels = sorted(set(other for other in labels if other != label))
        a = float(np.mean([np.linalg.norm(x[idx] - x[j]) for j in same])) if same else 0.0
        b_values = []
        for other in other_labels:
            indices = [j for j, value in enumerate(labels) if value == other]
            if indices:
                b_values.append(float(np.mean([np.linalg.norm(x[idx] - x[j]) for j in indices])))
        b = min(b_values) if b_values else 0.0
        denom = max(a, b, 1.0e-12)
        values.append((label, float((b - a) / denom)))
    by_label = {label: float(np.mean([value for row_label, value in values if row_label == label])) for label in sorted(set(labels))}
    return {"schema": "scope_static_stage4_silhouette_by_label_v1", "overall": float(np.mean([value for _label, value in values])) if values else 0.0, "by_label": by_label}


def _blockwise_mutual_information(x: np.ndarray, feature_names: list[str], labels: list[str]) -> dict[str, object]:
    blocks: dict[str, list[int]] = defaultdict(list)
    for idx, name in enumerate(feature_names):
        parts = str(name).split("__")
        blocks["__".join(parts[:2]) if len(parts) >= 2 else str(name)].append(idx)
    out = {}
    for block, indices in blocks.items():
        score = float(normalized_mutual_info(_encode(labels), _encode(_binned_block_values(x[:, indices]))))
        out[block] = score
    return {"schema": "scope_static_stage4_blockwise_mi_v1", "normalized_mutual_info_by_block": dict(sorted(out.items()))}


def _binned_block_values(block: np.ndarray) -> list[str]:
    arr = np.mean(np.asarray(block, dtype=np.float64), axis=1) if block.size else np.zeros(block.shape[0], dtype=np.float64)
    if arr.size == 0 or math.isclose(float(np.max(arr)), float(np.min(arr))):
        return ["bin0" for _ in arr.tolist()]
    q1, q2 = np.quantile(arr, [1.0 / 3.0, 2.0 / 3.0])
    return [f"bin{0 if value <= q1 else 1 if value <= q2 else 2}" for value in arr.tolist()]


def _projection_collapse_matrix(x: np.ndarray, labels: list[str]) -> dict[str, object]:
    class_names = sorted(set(labels), key=mechanism_sort_key)
    centroids = {label: np.mean(x[[idx for idx, value in enumerate(labels) if value == label]], axis=0) for label in class_names}
    distances = np.zeros((len(class_names), len(class_names)), dtype=np.float64)
    for i, left in enumerate(class_names):
        for j, right in enumerate(class_names):
            distances[i, j] = float(np.linalg.norm(centroids[left] - centroids[right]))
    positive = distances[distances > 0.0]
    threshold = float(np.quantile(positive, 0.10)) if positive.size else 0.0
    collapsed = (distances <= max(threshold, 1.0e-9)).astype(int)
    np.fill_diagonal(collapsed, 1)
    return {
        "schema": "scope_static_stage4_projection_collapse_matrix_v1",
        "class_names": class_names,
        "centroid_distance_matrix": distances.tolist(),
        "collapse_threshold": threshold,
        "collapsed_binary_matrix": collapsed.tolist(),
    }


def _alias_classes(collapse: Mapping[str, object]) -> dict[str, object]:
    names = [str(value) for value in collapse.get("class_names", [])]
    mat = np.asarray(collapse.get("collapsed_binary_matrix", []), dtype=np.int64)
    seen: set[int] = set()
    classes = []
    label_to_alias = {}
    for idx, name in enumerate(names):
        if idx in seen:
            continue
        group = [j for j in range(len(names)) if mat.size and (mat[idx, j] or mat[j, idx])]
        for j in group:
            seen.add(j)
        alias = "~".join(names[j] for j in group)
        classes.append({"alias_label": alias, "members": [names[j] for j in group]})
        for j in group:
            label_to_alias[names[j]] = alias
    return {
        "schema": "scope_static_stage4_source_alias_classes_v1",
        "alias_class_count": int(len(classes)),
        "alias_classes": classes,
        "alias_class_map": label_to_alias,
    }


def _surface_decision(exact: Mapping[str, object], quotient: Mapping[str, object], alias: Mapping[str, object]) -> str:
    exact_nmi = float(exact.get("normalized_mutual_info", 0.0) or 0.0)
    quotient_nmi = float(quotient.get("normalized_mutual_info", 0.0) or 0.0)
    if exact_nmi >= PASS_EXACT_NMI:
        return "bridge_surface_pass"
    if quotient_nmi >= PASS_QUOTIENT_NMI:
        return "bridge_surface_quotient_only"
    if int(alias.get("alias_class_count", 0)) < int(exact.get("class_count", 0)):
        return "bridge_surface_projection_aliasing"
    return "bridge_surface_fail"


def _write_outputs(output: Path, result: dict[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "mechanism_survival_report.json": result["mechanism_survival_report"],
        "alias_ceiling.json": result["alias_ceiling"],
        "projection_alias_classes.json": result["source_alias_classes"],
        "projection_collapse_matrix.json": result["projection_collapse_matrix"],
        "source_visible_ceiling.json": result["source_visible_ceiling"],
        "source_alias_classes.json": result["source_alias_classes"],
        "source_baseline_results.json": result["source_baseline_results"],
        "source_projection_adequacy.json": result["source_projection_adequacy"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "config.yaml").write_text(yaml.safe_dump({"stage4_source_ceiling_v1": result["config"]}, sort_keys=False), encoding="utf-8")
    (output / "summary.md").write_text(format_source_survival_summary(result), encoding="utf-8")


def _encode(labels: list[str]) -> list[int]:
    mapping: dict[str, int] = {}
    out = []
    for label in labels:
        text = str(label)
        if text not in mapping:
            mapping[text] = len(mapping)
        out.append(mapping[text])
    return out


def format_source_survival_summary(result: Mapping[str, object]) -> str:
    report = dict(result.get("mechanism_survival_report", {}))
    visible = dict(report.get("visible_ceiling", {}))
    quotient = dict(report.get("quotient_ceiling", {}))
    return "\n".join(
        [
            "# S4.0.5 Source Surface Survival Audit",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Visible NMI: `{float(visible.get('normalized_mutual_info', 0.0)):.4f}`",
            f"- Quotient NMI: `{float(quotient.get('normalized_mutual_info', 0.0)):.4f}`",
            "",
        ]
    )
