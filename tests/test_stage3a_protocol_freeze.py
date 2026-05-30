from __future__ import annotations

import json
from pathlib import Path

import pytest

from scope_static.physical.mechanism_catalog import MECHANISM_NAMES
from scope_static.physical.stage3a_protocol_freeze import (
    forbidden_feature_audit,
    run_stage3a_dataset_protocol_freeze,
)
from scope_static.experiments.run_stage3a_protocol_freeze import run_stage3a_protocol_freeze_from_config


def test_stage3a_freezes_visible_schema_splits_and_protocol_without_training(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    records = []
    for group in range(3):
        records.extend([_record("M0", group), _record("M4", group), _record("M8", group)])
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    output = tmp_path / "S3A_protocol_freeze"

    result = run_stage3a_dataset_protocol_freeze(
        teacher_dir=teacher,
        output_dir=output,
        shots=1000,
        seed=0,
        batch_size=2,
    )

    assert result["stage"] == "Stage3A_dataset_protocol_freeze"
    assert result["decision"] == "stage3a_protocol_freeze_passed"
    assert result["claim_boundary"]["stage3a_trains_model"] is False
    assert result["claim_boundary"]["observability_ceiling_stage"] == "Stage 3A.5"
    assert result["assignment_unit"]["j_definition"] == "mechanism_condition_instance"
    assert result["assignment_unit"]["single_shot_j_allowed_first_pass"] is False
    assert result["forbidden_feature_audit"]["passed"] is True
    assert result["batch_context_schema"]["primary_protocol"]["mode"] == "multi_context_batch"
    assert result["batch_context_schema"]["single_context_m13_claim_allowed"] is False
    assert result["split_manifest"]["train_validation_test_splits_non_empty"] is True
    assert result["acceptance_audit"]["checks"]["validation_label_model_selection_disabled"] is True
    assert result["acceptance_audit"]["checks"]["test_label_model_selection_disabled"] is True

    learner_fields = set(result["batch_context_schema"]["learner_visible_fields"])
    assert "true_mechanism_id" not in learner_fields
    assert "mechanism_name" not in learner_fields
    assert "oracle_prototypes" not in learner_fields

    for name in [
        "metrics.json",
        "config.yaml",
        "visible_feature_schema.json",
        "forbidden_feature_audit.json",
        "split_manifest.json",
        "probe_schedule_manifest.json",
        "batch_context_schema.json",
        "assignment_unit.json",
        "acceptance_audit.json",
        "summary.md",
    ]:
        assert (output / name).exists()

    assert not (output / "learned_assignments.npy").exists()


def test_stage3a_forbidden_feature_audit_rejects_identity_feature_names() -> None:
    audit = forbidden_feature_audit(["raw__single__prep_0__meas_Z__P0", "oracle_mechanism_id"])

    assert audit["passed"] is False
    assert audit["forbidden_feature_count"] >= 1
    assert any(hit["token"] == "oracle" for hit in audit["forbidden_feature_hits"])


def test_stage3a_config_wrapper_runs_from_yaml(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    records = []
    for group in range(3):
        records.extend([_record("M0", group), _record("M4", group)])
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    output = tmp_path / "configured"
    config = tmp_path / "stage3a.yaml"
    config.write_text(
        "\n".join(
            [
                "stage3a_protocol_freeze:",
                f"  teacher_dir: {teacher}",
                f"  output_dir: {output}",
                "  shots: 1000",
                "  seed: 7",
                "  batch_size: 2",
                "  assignment_unit: mechanism_condition_instance",
            ]
        )
        + "\n"
    )

    result = run_stage3a_protocol_freeze_from_config(config_path=config)

    assert result["decision"] == "stage3a_protocol_freeze_passed"
    assert (output / "split_manifest.json").exists()


def test_stage3a_rejects_single_shot_assignment_unit(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": [_record("M0", 0), _record("M0", 1), _record("M0", 2)]}) + "\n")

    with pytest.raises(ValueError, match="assignment_unit"):
        run_stage3a_dataset_protocol_freeze(teacher_dir=teacher, output_dir=tmp_path / "out", assignment_unit="single_shot")


def _record(label: str, group: int) -> dict[str, object]:
    two_qubit = label in {"M8", "M9", "M10", "M12", "M21", "M22", "M23", "M28", "M29", "M30", "M31", "M32", "M33"}
    return {
        "oracle_label": label,
        "mechanism_id": label,
        "name": MECHANISM_NAMES[label],
        "num_qubits": 2 if two_qubit else 1,
        "parameters": {},
        "instruction": "rzz" if two_qubit else "id",
        "qubits": [0, 1] if two_qubit else [0],
        "circuit_id": int(group),
        "location_id": int(group),
        "probe_indices": [],
    }
