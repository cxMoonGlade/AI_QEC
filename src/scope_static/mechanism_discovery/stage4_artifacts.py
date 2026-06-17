from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping

import numpy as np

from .artifacts import load_json_object, load_stage3a_visible_features, matrix_digest


@dataclass(frozen=True)
class Stage4SourceLabels:
    """Evaluator-only labels for a synthetic Stage 4 source freeze."""

    records: list[dict[str, object]]
    exact_labels: list[str]
    quotient_labels: list[str]
    exact_class_names: list[str]
    quotient_class_names: list[str]


@dataclass(frozen=True)
class Stage4SourceMixtureLabels:
    """Evaluator-only mixture labels for a Google-unit Stage 4 source freeze."""

    records: list[dict[str, object]]
    dominant_families: list[str]
    visible_mode_tags: list[str]
    family_class_names: list[str]
    visible_mode_class_names: list[str]


def load_stage4_source_evaluator_labels(stage4_source_dir: str | Path) -> Stage4SourceLabels:
    source = Path(stage4_source_dir)
    labels_path = source / "source_evaluator_labels.json"
    if labels_path.exists():
        payload = load_json_object(labels_path)
    else:
        payload = load_json_object(source / "source_mixture_evaluator_labels.json")
    records_raw = payload.get("records", [])
    if not isinstance(records_raw, list) or not records_raw:
        raise ValueError(f"{labels_path} must contain non-empty evaluator records")
    records = [dict(row) for row in records_raw]
    exact = [str(row.get("exact_mechanism_label", "")) for row in records]
    quotient = [str(row.get("quotient_label", row.get("alias_label", exact[idx]))) for idx, row in enumerate(records)]
    return Stage4SourceLabels(
        records=records,
        exact_labels=exact,
        quotient_labels=quotient,
        exact_class_names=sorted(set(exact), key=mechanism_sort_key),
        quotient_class_names=sorted(set(quotient), key=mechanism_sort_key),
    )


def load_stage4_source_mixture_evaluator_labels(stage4_source_dir: str | Path) -> Stage4SourceMixtureLabels:
    source = Path(stage4_source_dir)
    payload = load_json_object(source / "source_mixture_evaluator_labels.json")
    records_raw = payload.get("records", [])
    if not isinstance(records_raw, list) or not records_raw:
        raise ValueError(f"{source / 'source_mixture_evaluator_labels.json'} must contain non-empty evaluator records")
    records = [dict(row) for row in records_raw]
    families = [str(row.get("dominant_family", row.get("exact_mechanism_label", ""))) for row in records]
    modes = [str(row.get("visible_mode_tag", row.get("quotient_label", ""))) for row in records]
    return Stage4SourceMixtureLabels(
        records=records,
        dominant_families=families,
        visible_mode_tags=modes,
        family_class_names=sorted(set(families), key=mechanism_sort_key),
        visible_mode_class_names=sorted(set(modes), key=mechanism_sort_key),
    )


def validate_stage4_source_label_separation(stage4_source_dir: str | Path) -> dict[str, object]:
    source = Path(stage4_source_dir)
    manifest = load_json_object(source / "source_label_manifest.json")
    evaluator = load_json_object(source / "source_evaluator_labels.json")
    mixture = load_json_object(source / "source_mixture_evaluator_labels.json") if (source / "source_mixture_evaluator_labels.json").exists() else {}
    visible_schema = load_json_object(source / "visible_feature_schema.json")
    visible_matrix = load_json_object(source / "visible_feature_matrix.json")
    feature_names = [str(item.get("name", "")) for item in visible_schema.get("features", []) if isinstance(item, Mapping)]
    evaluator_fields = [
        str(row.get("field", ""))
        for row in manifest.get("fields", [])
        if isinstance(row, Mapping) and str(row.get("visibility")) == "evaluator_only"
    ]
    forbidden_fields = [
        str(row.get("field", ""))
        for row in manifest.get("fields", [])
        if isinstance(row, Mapping) and str(row.get("visibility")) == "forbidden"
    ]
    joined_features = "\n".join(feature_names).lower()
    checks = {
        "source_label_manifest_exists": bool(manifest),
        "source_evaluator_labels_exists": bool(evaluator.get("records")),
        "source_mixture_evaluator_labels_separated_when_present": not bool(mixture) or bool(mixture.get("records")),
        "visible_feature_schema_contains_no_evaluator_fields": not any(field.lower() in joined_features for field in evaluator_fields),
        "visible_feature_schema_contains_no_forbidden_fields": not any(field.lower() in joined_features for field in forbidden_fields),
        "visible_feature_matrix_declares_no_labels": not bool(visible_matrix.get("contains_evaluator_labels", True)),
        "visible_feature_matrix_declares_no_oracle_fields": not bool(visible_matrix.get("contains_oracle_fields", True)),
    }
    return {
        "schema": "scope_static_stage4_source_label_separation_audit_v1",
        "passed": bool(all(checks.values())),
        "checks": checks,
        "evaluator_only_fields": evaluator_fields,
        "forbidden_fields": forbidden_fields,
    }


def load_stage4_visible_matrix(stage4_source_dir: str | Path) -> tuple[np.ndarray, list[str], dict[str, object]]:
    visible = load_stage3a_visible_features(stage4_source_dir)
    return visible.matrix, visible.feature_names, visible.manifest


def assert_stage4_visible_digest(stage4_source_dir: str | Path) -> None:
    source = Path(stage4_source_dir)
    manifest = load_json_object(source / "visible_feature_matrix.json")
    matrix = np.asarray(np.load(source / str(manifest.get("training_matrix_path", "visible_features.npy"))), dtype=np.float64)
    expected = str(manifest.get("visible_features_sha256", ""))
    if expected and matrix_digest(matrix) != expected:
        raise ValueError(f"{source} visible feature digest mismatch")


def load_stage4_json(path: str | Path) -> dict[str, object]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def mechanism_sort_key(label: str) -> tuple[int, str]:
    text = str(label)
    if text.startswith("M") and text[1:].isdigit():
        return (int(text[1:]), text)
    return (10_000, text)
