from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Mapping

import numpy as np
import yaml

from .artifacts import load_stage3a_frozen_visible_features
from .google_transfer import _apply_source_standardization, _assign_to_source_centers, _load_source_standardization
from .stage4_artifacts import load_stage4_visible_matrix


STAGE_NAME = "Stage4_support_alignment_audit"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/S4_bridge/S4_support_alignment_audit"


def run_stage4_support_alignment_audit(
    *,
    stage4_source_dir: str | Path,
    google_stage3a_dir: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    source_pretrain_dir: str | Path | None = None,
) -> dict[str, object]:
    """Audit whether the S4 source surface covers the real Google V2 surface."""

    source = Path(stage4_source_dir)
    google = Path(google_stage3a_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    source_raw, source_feature_names, source_manifest = load_stage4_visible_matrix(source)
    google_raw, google_feature_names, google_manifest = load_stage3a_frozen_visible_features(google)
    if list(source_feature_names) != list(google_feature_names):
        raise ValueError("source and Google feature schemas must match before support audit")

    mean, scale, standardization_loaded = _source_standardization_for_audit(
        source_pretrain_dir=source_pretrain_dir,
        source_raw=source_raw,
    )
    source_z = _apply_source_standardization(source_raw, mean=mean, scale=scale)
    google_z = _apply_source_standardization(google_raw, mean=mean, scale=scale)

    block_shift = _block_shift_ranking(source_z, google_z, source_feature_names)
    domain = _domain_classifier_audit(source_z, google_z)
    nearest = _nearest_source_coverage(source_z, google_z)
    codebook = _codebook_google_coverage(
        google_z,
        source_pretrain_dir=source_pretrain_dir,
    )
    decision = _support_decision(domain, nearest, codebook)
    report = {
        "schema": "scope_static_stage4_source_google_support_report_v1",
        "stage": STAGE_NAME,
        "decision": decision,
        "stage4_source_dir": str(source),
        "google_stage3a_dir": str(google),
        "source_pretrain_dir": str(source_pretrain_dir) if source_pretrain_dir is not None else None,
        "feature_schema_match": True,
        "source_shape": [int(dim) for dim in source_raw.shape],
        "google_shape": [int(dim) for dim in google_raw.shape],
        "coordinate_system": {
            "source_standardization_loaded_from_pretrain": bool(standardization_loaded),
            "comparison_coordinate_system": "source_standardized_visible_features",
            "raw_source_manifest": source_manifest,
            "raw_google_manifest": google_manifest,
        },
        "domain_classifier_audit": domain,
        "nearest_source_coverage": nearest,
        "codebook_google_coverage": codebook,
        "top_block_shifts": block_shift["blocks"][:10],
    }
    result = {
        "schema": "scope_static_stage4_support_alignment_audit_v1",
        "stage": STAGE_NAME,
        "output_dir": str(output),
        "source_google_support_report": report,
        "block_shift_ranking": block_shift,
        "domain_classifier_audit": domain,
        "nearest_source_coverage": nearest,
        "codebook_google_coverage": codebook,
        "decision": decision,
    }
    _write_outputs(output, result)
    return result


def _source_standardization_for_audit(*, source_pretrain_dir: str | Path | None, source_raw: np.ndarray) -> tuple[np.ndarray, np.ndarray, bool]:
    if source_pretrain_dir is not None:
        codebook_path = Path(source_pretrain_dir) / "source_codebook.npz"
        if codebook_path.exists():
            payload = np.load(codebook_path, allow_pickle=True)
            standardization = _load_source_standardization(payload, feature_count=int(source_raw.shape[1]))
            return (
                np.asarray(standardization["mean"], dtype=np.float64),
                np.asarray(standardization["scale"], dtype=np.float64),
                bool(standardization.get("loaded_from_source_codebook", False)),
            )
    mean = np.mean(source_raw, axis=0) if source_raw.size else np.zeros(source_raw.shape[1], dtype=np.float64)
    scale = np.std(source_raw, axis=0) if source_raw.size else np.ones(source_raw.shape[1], dtype=np.float64)
    scale = np.where(scale > 1.0e-12, scale, 1.0)
    return mean, scale, False


def _block_shift_ranking(source_z: np.ndarray, google_z: np.ndarray, feature_names: list[str]) -> dict[str, object]:
    blocks: dict[str, list[int]] = defaultdict(list)
    for idx, name in enumerate(feature_names):
        parts = str(name).split("__")
        block = "__".join(parts[:2]) if len(parts) >= 2 else str(name)
        blocks[block].append(idx)
    rows = []
    for block, indices in blocks.items():
        s = source_z[:, indices]
        g = google_z[:, indices]
        source_mean = np.mean(s, axis=0) if s.size else np.zeros(len(indices), dtype=np.float64)
        google_mean = np.mean(g, axis=0) if g.size else np.zeros(len(indices), dtype=np.float64)
        source_std = np.std(s, axis=0) if s.size else np.ones(len(indices), dtype=np.float64)
        google_std = np.std(g, axis=0) if g.size else np.ones(len(indices), dtype=np.float64)
        mean_l2 = float(np.linalg.norm(google_mean - source_mean) / max(1, len(indices)))
        mean_abs = float(np.mean(np.abs(google_mean - source_mean))) if indices else 0.0
        std_abs = float(np.mean(np.abs(google_std - source_std))) if indices else 0.0
        rows.append(
            {
                "block": block,
                "feature_count": int(len(indices)),
                "mean_shift_l2_per_feature": mean_l2,
                "mean_shift_abs": mean_abs,
                "std_shift_abs": std_abs,
                "support_shift_score": float(mean_abs + std_abs),
            }
        )
    rows.sort(key=lambda row: float(row["support_shift_score"]), reverse=True)
    return {"schema": "scope_static_stage4_block_shift_ranking_v1", "blocks": rows}


def _domain_classifier_audit(source_z: np.ndarray, google_z: np.ndarray) -> dict[str, object]:
    source_centroid = np.mean(source_z, axis=0) if source_z.size else np.zeros(source_z.shape[1], dtype=np.float64)
    google_centroid = np.mean(google_z, axis=0) if google_z.size else np.zeros(google_z.shape[1], dtype=np.float64)
    x = np.vstack([source_z, google_z]) if source_z.size or google_z.size else np.zeros((0, source_z.shape[1]), dtype=np.float64)
    labels = np.asarray([0] * int(source_z.shape[0]) + [1] * int(google_z.shape[0]), dtype=np.int64)
    dist_source = np.sum((x - source_centroid[None, :]) ** 2, axis=1) if x.size else np.zeros(0, dtype=np.float64)
    dist_google = np.sum((x - google_centroid[None, :]) ** 2, axis=1) if x.size else np.zeros(0, dtype=np.float64)
    scores = dist_source - dist_google
    predictions = (scores >= 0.0).astype(np.int64)
    return {
        "schema": "scope_static_stage4_domain_classifier_audit_v1",
        "classifier": "nearest_centroid_source_vs_google",
        "accuracy": float(np.mean(predictions == labels)) if labels.size else 0.0,
        "roc_auc": _roc_auc(scores, labels),
        "uses_mechanism_labels": False,
    }


def _nearest_source_coverage(source_z: np.ndarray, google_z: np.ndarray) -> dict[str, object]:
    source_nearest = _nearest_self_distances(source_z)
    google_to_source = _nearest_cross_distances(google_z, source_z)
    p50 = float(np.quantile(source_nearest, 0.50)) if source_nearest.size else 0.0
    p95 = float(np.quantile(source_nearest, 0.95)) if source_nearest.size else 0.0
    g50 = float(np.quantile(google_to_source, 0.50)) if google_to_source.size else 0.0
    g95 = float(np.quantile(google_to_source, 0.95)) if google_to_source.size else 0.0
    within_p95 = float(np.mean(google_to_source <= p95)) if google_to_source.size else 0.0
    return {
        "schema": "scope_static_stage4_nearest_source_coverage_v1",
        "source_nearest_p50": p50,
        "source_nearest_p95": p95,
        "google_to_source_nearest_p50": g50,
        "google_to_source_nearest_p95": g95,
        "google_within_source_p95_ratio": within_p95,
        "distance_coordinate_system": "source_standardized_visible_features",
    }


def _codebook_google_coverage(google_z: np.ndarray, *, source_pretrain_dir: str | Path | None) -> dict[str, object]:
    if source_pretrain_dir is None:
        return {"schema": "scope_static_stage4_codebook_google_coverage_v1", "skipped": True, "reason": "source_pretrain_dir_not_provided"}
    codebook_path = Path(source_pretrain_dir) / "source_codebook.npz"
    if not codebook_path.exists():
        return {"schema": "scope_static_stage4_codebook_google_coverage_v1", "skipped": True, "reason": "source_codebook_missing"}
    payload = np.load(codebook_path, allow_pickle=True)
    centers = np.asarray(payload["centers"], dtype=np.float64)
    assignments, recon = _assign_to_source_centers(google_z, centers)
    counts = Counter(int(value) for value in assignments.tolist())
    active = sum(1 for idx in range(int(centers.shape[0])) if counts.get(idx, 0) > 0)
    total = max(1, int(assignments.size))
    probs = np.asarray([counts.get(idx, 0) / total for idx in range(int(centers.shape[0]))], dtype=np.float64)
    entropy = float(-np.sum([p * np.log(p) for p in probs if p > 0.0]))
    distances = np.sqrt(np.sum((google_z - recon) ** 2, axis=1)) if google_z.size else np.zeros(0, dtype=np.float64)
    return {
        "schema": "scope_static_stage4_codebook_google_coverage_v1",
        "skipped": False,
        "source_code_count": int(centers.shape[0]),
        "active_source_code_count": int(active),
        "active_source_code_ratio": float(active / max(1, int(centers.shape[0]))),
        "assignment_entropy": entropy,
        "assignment_counts": {f"C{idx:03d}": int(counts.get(idx, 0)) for idx in range(int(centers.shape[0]))},
        "nearest_code_distance_p50": float(np.quantile(distances, 0.50)) if distances.size else 0.0,
        "nearest_code_distance_p95": float(np.quantile(distances, 0.95)) if distances.size else 0.0,
    }


def _support_decision(domain: Mapping[str, object], nearest: Mapping[str, object], codebook: Mapping[str, object]) -> str:
    auc = float(domain.get("roc_auc", 0.5) or 0.5)
    within_p95 = float(nearest.get("google_within_source_p95_ratio", 0.0) or 0.0)
    active_ratio = float(codebook.get("active_source_code_ratio", 1.0) or 0.0) if not bool(codebook.get("skipped", False)) else 1.0
    if active_ratio <= 0.10 or within_p95 <= 0.10 or auc >= 0.90:
        return "source_google_support_mismatch"
    if active_ratio <= 0.25 or within_p95 <= 0.50 or auc >= 0.75:
        return "source_google_support_shifted"
    return "source_google_support_overlap"


def _nearest_self_distances(x: np.ndarray) -> np.ndarray:
    if x.shape[0] <= 1:
        return np.zeros(0, dtype=np.float64)
    distances = np.sqrt(np.maximum(_squared_distances(x, x), 0.0))
    np.fill_diagonal(distances, np.inf)
    return np.min(distances, axis=1)


def _nearest_cross_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    if left.size == 0 or right.size == 0:
        return np.zeros(0, dtype=np.float64)
    return np.sqrt(np.maximum(np.min(_squared_distances(left, right), axis=1), 0.0))


def _squared_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return np.sum((left[:, None, :] - right[None, :, :]) ** 2, axis=2)


def _roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    positives = np.asarray(scores[labels == 1], dtype=np.float64)
    negatives = np.asarray(scores[labels == 0], dtype=np.float64)
    if positives.size == 0 or negatives.size == 0:
        return 0.5
    greater = 0.0
    total = float(positives.size * negatives.size)
    for value in positives:
        greater += float(np.sum(value > negatives))
        greater += 0.5 * float(np.sum(value == negatives))
    return float(greater / total)


def _write_outputs(output: Path, result: Mapping[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "source_google_support_report.json": result["source_google_support_report"],
        "block_shift_ranking.json": result["block_shift_ranking"],
        "domain_classifier_audit.json": result["domain_classifier_audit"],
        "nearest_source_coverage.json": result["nearest_source_coverage"],
        "codebook_google_coverage.json": result["codebook_google_coverage"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "config.yaml").write_text(
        yaml.safe_dump({"stage4_support_audit_v1": {"output_dir": str(output)}}, sort_keys=False),
        encoding="utf-8",
    )
    (output / "summary.md").write_text(format_support_audit_summary(result), encoding="utf-8")


def format_support_audit_summary(result: Mapping[str, object]) -> str:
    report = dict(result.get("source_google_support_report", {}))
    nearest = dict(result.get("nearest_source_coverage", {}))
    codebook = dict(result.get("codebook_google_coverage", {}))
    return "\n".join(
        [
            "# S4 Source-Google Support Alignment Audit",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Google within source p95: `{float(nearest.get('google_within_source_p95_ratio', 0.0)):.4f}`",
            f"- Active source code ratio: `{float(codebook.get('active_source_code_ratio', 0.0)):.4f}`",
            f"- Domain classifier AUC: `{float(dict(report.get('domain_classifier_audit', {})).get('roc_auc', 0.5)):.4f}`",
            "",
        ]
    )
