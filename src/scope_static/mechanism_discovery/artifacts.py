from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Mapping

import numpy as np


@dataclass(frozen=True)
class Stage3VisibleFeatures:
    """Frozen learner-visible Stage 3A feature matrix plus manifest metadata."""

    matrix: np.ndarray
    feature_names: list[str]
    manifest: dict[str, object]


@dataclass(frozen=True)
class Stage3EvaluatorLabels:
    """Evaluator-only labels loaded after learner fitting."""

    records: list[dict[str, object]]
    exact_labels: list[str]
    exact_class_names: list[str]


def load_json_object(path: str | Path) -> dict[str, object]:
    source = Path(path)
    data = json.loads(source.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{source} must contain a JSON object")
    return data


def resolve_teacher_dir(stage3a_metrics: Mapping[str, object], teacher_dir: str | Path | None = None) -> Path:
    if teacher_dir is not None:
        if not str(teacher_dir):
            raise ValueError("teacher_dir is required either directly or through Stage 3A metrics.json")
        return Path(teacher_dir)
    config = stage3a_metrics.get("config", {})
    cfg = dict(config) if isinstance(config, Mapping) else {}
    raw = cfg.get("teacher_dir")
    if raw is None or not str(raw):
        raise ValueError("teacher_dir is required either directly or through Stage 3A metrics.json")
    return Path(str(raw))


def load_stage3a_visible_features(stage3a_dir: str | Path) -> Stage3VisibleFeatures:
    s3a = Path(stage3a_dir)
    manifest_path = s3a / "visible_feature_matrix.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing frozen Stage 3A visible feature matrix manifest: {manifest_path}")
    manifest = load_json_object(manifest_path)
    matrix_path = s3a / str(manifest.get("training_matrix_path", "visible_features.npy"))
    if not matrix_path.exists():
        raise FileNotFoundError(f"missing frozen Stage 3A visible feature matrix: {matrix_path}")
    matrix = np.asarray(np.load(matrix_path), dtype=np.float64)
    schema_path = s3a / str(manifest.get("feature_schema_path", "visible_feature_schema.json"))
    schema = load_json_object(schema_path)
    feature_names = [str(item.get("name", "")) for item in schema.get("features", []) if isinstance(item, dict)]
    if matrix.ndim != 2:
        raise ValueError(f"{matrix_path} must be a 2D visible feature matrix")
    if len(feature_names) != int(matrix.shape[1]):
        raise ValueError(f"{matrix_path} has {matrix.shape[1]} columns but schema has {len(feature_names)} features")
    expected_shape = [int(dim) for dim in manifest.get("shape", [])] if isinstance(manifest.get("shape", []), list) else []
    if expected_shape and expected_shape != [int(dim) for dim in matrix.shape]:
        raise ValueError(f"{matrix_path} shape {matrix.shape} does not match manifest shape {expected_shape}")
    expected_digest = str(manifest.get("visible_features_sha256", ""))
    if expected_digest and matrix_digest(matrix) != expected_digest:
        raise ValueError(f"{matrix_path} digest does not match Stage 3A manifest")
    out_manifest = dict(manifest)
    out_manifest.update(
        {
            "loaded_from_stage3a_artifact": True,
            "resolved_training_matrix_path": str(matrix_path),
            "resolved_feature_schema_path": str(schema_path),
        }
    )
    return Stage3VisibleFeatures(matrix=matrix, feature_names=feature_names, manifest=out_manifest)


def load_stage3a_frozen_visible_features(stage3a_dir: str | Path) -> tuple[np.ndarray, list[str], dict[str, object]]:
    artifact = load_stage3a_visible_features(stage3a_dir)
    return artifact.matrix, artifact.feature_names, artifact.manifest


def feature_schema_matches_stage3a(stage3a_dir: str | Path, feature_names: list[str]) -> dict[str, object]:
    schema = load_json_object(Path(stage3a_dir) / "visible_feature_schema.json")
    expected = [str(item.get("name", "")) for item in schema.get("features", []) if isinstance(item, dict)]
    matches = list(expected) == [str(name) for name in feature_names]
    return {
        "schema": "scope_static_stage3_feature_schema_match_audit_v1",
        "passed": bool(matches),
        "feature_count": int(len(feature_names)),
        "expected_feature_count": int(len(expected)),
        "mismatch_count": int(sum(1 for left, right in zip(expected, feature_names) if str(left) != str(right)) + abs(len(expected) - len(feature_names))),
    }


def load_mechanism_records(path: str | Path) -> list[dict[str, object]]:
    source = Path(path)
    data = load_json_object(source)
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{source} does not contain non-empty mechanisms")
    return [dict(record) for record in records]


def load_stage3_evaluator_labels(stage3a_dir: str | Path, teacher_dir: str | Path | None = None) -> Stage3EvaluatorLabels:
    s3a = Path(stage3a_dir)
    s3a_metrics = load_json_object(s3a / "metrics.json")
    teacher = resolve_teacher_dir(s3a_metrics, teacher_dir)
    records = load_mechanism_records(teacher / "oracle_mechanisms.json")
    labels = [str(record.get("oracle_label", record.get("mechanism_id", ""))) for record in records]
    class_names = sorted(set(labels), key=mechanism_sort_key)
    return Stage3EvaluatorLabels(records=records, exact_labels=labels, exact_class_names=class_names)


def mechanism_sort_key(label: str) -> tuple[int, str]:
    text = str(label)
    if text.startswith("M") and text[1:].isdigit():
        return (int(text[1:]), text)
    return (10_000, text)


def matrix_digest(matrix: np.ndarray) -> str:
    arr = np.ascontiguousarray(np.asarray(matrix, dtype=np.float64))
    return hashlib.sha256(arr.tobytes()).hexdigest()
