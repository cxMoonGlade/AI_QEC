from __future__ import annotations

import json
from pathlib import Path

import pytest

from scope_static.backend.mechanism_catalog import MECHANISM_NAMES
from scope_static.mechanism_discovery.artifacts import load_stage3_evaluator_labels
from scope_static.mechanism_discovery.artifacts import load_stage3a_visible_features
from scope_static.mechanism_discovery.artifacts import resolve_teacher_dir
from scope_static.mechanism_discovery.protocol_freeze import run_stage3a_dataset_protocol_freeze


def test_stage3_artifacts_load_frozen_visible_features_and_evaluator_labels(tmp_path: Path) -> None:
    teacher = tmp_path / "Layer1P_teacher"
    teacher.mkdir()
    records = [_record("M0", 0), _record("M4", 0), _record("M0", 1), _record("M4", 1)]
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    s3a = tmp_path / "S3A"
    run_stage3a_dataset_protocol_freeze(teacher_dir=teacher, output_dir=s3a, shots=1000, batch_size=2)

    visible = load_stage3a_visible_features(s3a)
    labels = load_stage3_evaluator_labels(s3a)

    assert visible.matrix.shape[0] == 4
    assert len(visible.feature_names) == visible.matrix.shape[1]
    assert visible.manifest["loaded_from_stage3a_artifact"] is True
    assert labels.exact_labels == ["M0", "M4", "M0", "M4"]
    assert labels.exact_class_names == ["M0", "M4"]


def test_stage3_artifacts_detect_visible_feature_digest_mismatch(tmp_path: Path) -> None:
    teacher = tmp_path / "Layer1P_teacher"
    teacher.mkdir()
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": [_record("M0", 0), _record("M0", 1), _record("M0", 2)]}) + "\n")
    s3a = tmp_path / "S3A"
    run_stage3a_dataset_protocol_freeze(teacher_dir=teacher, output_dir=s3a, shots=1000, batch_size=2)
    manifest = json.loads((s3a / "visible_feature_matrix.json").read_text())
    manifest["visible_features_sha256"] = "not-the-real-digest"
    (s3a / "visible_feature_matrix.json").write_text(json.dumps(manifest, indent=2) + "\n")

    with pytest.raises(ValueError, match="digest"):
        load_stage3a_visible_features(s3a)


def test_stage3_artifacts_resolve_teacher_dir_requires_explicit_source() -> None:
    with pytest.raises(ValueError, match="teacher_dir"):
        resolve_teacher_dir({})


def _record(label: str, group: int) -> dict[str, object]:
    return {
        "oracle_label": label,
        "mechanism_id": label,
        "name": MECHANISM_NAMES[label],
        "num_qubits": 1,
        "parameters": {},
        "instruction": "id",
        "qubits": [0],
        "circuit_id": int(group),
        "location_id": int(group),
        "probe_indices": [],
    }
