from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scope_static.primitives.mechanism_catalog import MECHANISM_NAMES
from scope_static.mechanism_discovery.protocol_freeze import (
    forbidden_feature_audit,
    load_stage3a_frozen_visible_features,
    run_stage3a_dataset_protocol_freeze,
)
from scope_static.experiments.stage3.protocol_freeze import run_stage3a_protocol_freeze_from_config


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
    assert result["visible_feature_matrix"]["training_matrix_path"] == "visible_features.npy"
    assert result["visible_feature_matrix"]["contains_evaluator_labels"] is False
    assert "visible_operation_context" in result["batch_context_schema"]["learner_visible_fields"]
    assert result["operation_context_public_audit"]["passed"] is True
    assert result["operation_context_public_audit"]["allowed_source_fields"] == ["instruction"]
    assert result["acceptance_audit"]["checks"]["operation_context_is_public_instruction_context"] is True
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
        "visible_feature_matrix.json",
        "visible_features.npy",
        "sampled_visible_features.npy",
        "forbidden_feature_audit.json",
        "operation_context_public_audit.json",
        "split_manifest.json",
        "probe_schedule_manifest.json",
        "batch_context_schema.json",
        "assignment_unit.json",
        "acceptance_audit.json",
        "summary.md",
    ]:
        assert (output / name).exists()

    assert not (output / "learned_assignments.npy").exists()
    frozen, feature_names, manifest = load_stage3a_frozen_visible_features(output)
    assert frozen.shape == (9, result["visible_feature_schema"]["num_features"])
    assert len(feature_names) == frozen.shape[1]
    assert manifest["loaded_from_stage3a_artifact"] is True
    assert np.allclose(frozen, np.load(output / "visible_features.npy"))


def test_stage3a_forbidden_feature_audit_rejects_identity_feature_names() -> None:
    audit = forbidden_feature_audit(["raw__single__prep_0__meas_Z__P0", "oracle_mechanism_id"])

    assert audit["passed"] is False
    assert audit["forbidden_feature_count"] >= 1
    assert any(hit["token"] == "oracle" for hit in audit["forbidden_feature_hits"])


def test_stage3a_rejects_mechanism_surrogate_instruction_context(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    records = [_record("M0", 0), _record("M4", 1), _record("M8", 2)]
    for record in records:
        record["instruction"] = str(record["mechanism_id"])
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")

    result = run_stage3a_dataset_protocol_freeze(
        teacher_dir=teacher,
        output_dir=tmp_path / "out",
        shots=1000,
        batch_size=2,
    )

    assert result["decision"] == "stage3a_protocol_freeze_failed"
    audit = result["operation_context_public_audit"]
    assert audit["passed"] is False
    assert audit["checks"]["all_record_instructions_in_public_alphabet"] is False
    assert audit["checks"]["operation_context_matches_public_instruction_field"] is False


def test_m11_missing_overlay_payload_fails_teacher_or_stage3a(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    records = [_record("M11", group) for group in range(3)]
    for record in records:
        record["num_qubits"] = 2
        record["instruction"] = "rzz"
        record["qubits"] = [0, 1]
        record["parameters"] = {"epsilon": 0.025, "strength": 0.025}
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")

    result = run_stage3a_dataset_protocol_freeze(
        teacher_dir=teacher,
        output_dir=tmp_path / "out",
        shots=1000,
        batch_size=2,
    )

    assert result["decision"] == "stage3a_protocol_freeze_failed"
    overlay = result["overlay_contract_audit"]
    assert overlay["passed"] is False
    assert overlay["num_overlay_records_missing_payload"] == 3
    assert "M11_overlay_contract_missing" in overlay["failure_kinds"]
    assert result["acceptance_audit"]["checks"]["overlay_contract_payload_complete"] is False


def test_overlay_payload_evaluator_only_not_in_visible_schema(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    records = [_record("M11", group) for group in range(3)]
    for idx, record in enumerate(records):
        record["num_qubits"] = 2
        record["instruction"] = "rzz"
        record["qubits"] = [idx, idx + 1]
        record["parameters"] = {"epsilon": 0.025 + 0.001 * idx, "spectator_strength": 0.003 + 0.001 * idx}
        record["spectator_overlay_present"] = True
        record["spectator_overlay"] = {
            "present": True,
            "base_mechanism": "M8",
            "victim_relative_location": "edge",
            "aggressor_relative_location": "adjacent_gate",
            "coupling_axis": "ZZ",
            "timing_context": "same_cycle",
            "spectator_strength": 0.003 + 0.001 * idx,
        }
        record["base_mechanism"] = "M8"
        record["victim_relative_location"] = "edge"
        record["aggressor_relative_location"] = "adjacent_gate"
        record["coupling_axis"] = "ZZ"
        record["timing_context"] = "same_cycle"
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")

    result = run_stage3a_dataset_protocol_freeze(
        teacher_dir=teacher,
        output_dir=tmp_path / "out",
        shots=1000,
        batch_size=2,
    )

    assert result["decision"] == "stage3a_protocol_freeze_passed"
    assert result["overlay_contract_audit"]["passed"] is True
    feature_names = [str(row["name"]) for row in result["visible_feature_schema"]["features"]]
    forbidden_overlay_tokens = [
        "spectator_overlay",
        "base_mechanism",
        "victim_relative_location",
        "aggressor_relative_location",
        "coupling_axis",
        "timing_context",
        "spectator_strength",
    ]
    assert not any(token in name for token in forbidden_overlay_tokens for name in feature_names)
    evaluator_fields = set(result["batch_context_schema"]["evaluator_only_fields"])
    assert "victim_relative_location" in evaluator_fields
    assert "spectator_strength" in evaluator_fields


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
    two_qubit = label in {"M8", "M9", "M10", "M11", "M12", "M21", "M22", "M23", "M28", "M29", "M30", "M31", "M32", "M33"}
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
