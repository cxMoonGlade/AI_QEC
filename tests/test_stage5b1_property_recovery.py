from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.experiments.stage5.property_recovery import run_stage5b1_property_recovery_from_config
from scope_static.experiments.stage5.conditional_property_recovery import run_stage5b1b_conditional_property_recovery_from_config
from scope_static.mechanism_discovery.observability_ceiling import run_stage3a5_observability_alias_ceiling
from scope_static.mechanism_discovery.property_recovery import run_stage5b1_property_recovery, stage5b1_contract_breakdown_audit
from scope_static.mechanism_discovery.protocol_freeze import run_stage3a_dataset_protocol_freeze
from scope_static.primitives.mechanism_catalog import MECHANISM_NAMES


def test_stage5b1_recovers_context_relative_location_and_strength_from_fixed_assignments(tmp_path: Path) -> None:
    teacher, s3a, s3a5, s3b1, assignments = _prepare_s5b1_fixture(tmp_path)
    assignment_path = tmp_path / "fixed_assignments.npy"
    np.save(assignment_path, assignments)
    output = tmp_path / "S5B1"

    result = run_stage5b1_property_recovery(
        stage3a_dir=s3a,
        stage3a5_dir=s3a5,
        stage3b1_dir=s3b1,
        teacher_dir=teacher,
        output_dir=output,
        assignment_source="fixture_fixed_visible_assignments",
        assignment_path=assignment_path,
    )

    assert result["decision"] == "stage5b1_property_recovery_passed"
    assert result["claim_boundary"]["uses_mechanism_labels_for_property_head_fit"] is False
    assert result["claim_boundary"]["uses_oracle_location_or_strength_for_property_head_fit"] is False
    assert result["claim_boundary"]["uses_evaluator_records_after_fit_for_scoring"] is True
    assert result["assignment_source_audit"]["row_stochastic"] is True
    assert result["s5b1_property_recovery_metrics"]["model_name"] == "linear_proto_visible_residual_energy"
    assert result["s5b1_property_recovery_metrics"]["uses_oracle_location_or_strength_for_fit"] is False
    assert result["context_relative_location_recovery_audit"]["passed"] is True
    assert result["context_normalized_strength_recovery_audit"]["passed"] is True
    assert result["overlay_contract_audit"]["passed"] is True
    assert result["overlay_recovery_audit"]["passed"] is True
    breakdown = result["s5b1_contract_breakdown_audit"]
    assert breakdown["s5b1_location_passed"] is True
    assert breakdown["s5b1_strength_passed"] is True
    assert breakdown["s5b1_dimension_passed"] is True
    assert breakdown["s5b1_contract_passed"] is True
    assert result["acceptance_audit"]["checks"]["s5b1_location_passed"] is True
    assert result["acceptance_audit"]["checks"]["s5b1_strength_passed"] is True
    assert result["acceptance_audit"]["checks"]["s5b1_dimension_passed"] is True
    assert result["s5_context_relative_mechanism_effect_audit"]["contract_typed_recovery_metrics"]["passed"] is True
    assert result["mechanism_dimension_recovery_audit"]["passed"] is True
    assert result["targeted_m6_m13_m18_m27_property_audit"]["rows"]["M13"]["present"] is True

    for name in [
        "metrics.json",
        "s5b1_property_recovery_metrics.json",
        "context_relative_location_recovery_audit.json",
        "context_normalized_strength_recovery_audit.json",
        "s5_context_relative_mechanism_effect_audit.json",
        "mechanism_dimension_recovery_audit.json",
        "overlay_contract_audit.json",
        "overlay_recovery_audit.json",
        "s5b1_contract_breakdown_audit.json",
        "acceptance_audit.json",
        "summary.md",
    ]:
        assert (output / name).exists()


def test_stage5b1_config_wrapper_runs_from_yaml(tmp_path: Path) -> None:
    teacher, s3a, s3a5, s3b1, assignments = _prepare_s5b1_fixture(tmp_path)
    assignment_path = tmp_path / "fixed_assignments.npy"
    np.save(assignment_path, assignments)
    output = tmp_path / "configured"
    config = tmp_path / "stage5b1.yaml"
    config.write_text(
        "\n".join(
            [
                "stage5b1_property_recovery:",
                f"  stage3a_dir: {s3a}",
                f"  stage3a5_dir: {s3a5}",
                f"  stage3b1_dir: {s3b1}",
                f"  teacher_dir: {teacher}",
                f"  output_dir: {output}",
                "  assignment_source: fixture_fixed_visible_assignments",
                f"  assignment_path: {assignment_path}",
            ]
        )
        + "\n"
    )

    result = run_stage5b1_property_recovery_from_config(config_path=config)

    assert result["decision"] == "stage5b1_property_recovery_passed"
    assert (output / "s5b1_property_recovery_metrics.json").exists()


def test_stage5b1_contract_breakdown_separates_location_strength_from_dimension() -> None:
    breakdown = stage5b1_contract_breakdown_audit(
        family={"passed": True},
        s5={
            "effect_recovery_metrics": {"passed": True},
            "contract_typed_recovery_metrics": {
                "passed": False,
                "family_failed_labels": [],
                "atomic_flat_exact_failed_labels": [],
            },
            "mechanism_dimension_recovery_audit": {
                "passed": False,
                "targets": [{"mechanism_id": "M13", "passed": False}],
            },
        },
        location={"passed": True, "failed_labels": []},
        strength={"passed": True, "failed_labels": []},
        targeted={"passed": True, "rows": {}},
    )

    assert breakdown["s5b1_location_passed"] is True
    assert breakdown["s5b1_strength_passed"] is True
    assert breakdown["s5b1_location_strength_passed"] is True
    assert breakdown["s5b1_dimension_passed"] is False
    assert breakdown["s5b1_property_without_dimension_passed"] is True
    assert breakdown["s5b1_contract_passed"] is False
    assert breakdown["dimension_failed_labels"] == ["M13"]


def test_stage5b1_contract_breakdown_relabels_overlay_missing_payload() -> None:
    breakdown = stage5b1_contract_breakdown_audit(
        family={"passed": True},
        s5={
            "effect_recovery_metrics": {"passed": True},
            "overlay_contract_audit": {"passed": False, "failure_kinds": ["M11_overlay_contract_missing"]},
            "overlay_recovery_audit": {"passed": False, "failure_kind": "M11_overlay_contract_missing"},
            "contract_typed_recovery_metrics": {
                "passed": False,
                "family_failed_labels": [],
                "atomic_flat_exact_failed_labels": [],
                "overlay_contract_missing_target_ids": ["M11"],
                "overlay_failure_kinds": ["M11_overlay_contract_missing"],
            },
            "mechanism_dimension_recovery_audit": {
                "passed": True,
                "recovery_passed_excluding_not_evaluable": True,
                "targets": [
                    {
                        "mechanism_id": "M11",
                        "passed": True,
                        "not_evaluable": True,
                        "not_evaluable_reason": "M11_overlay_contract_missing",
                    }
                ],
            },
        },
        location={"passed": True, "failed_labels": []},
        strength={"passed": True, "failed_labels": []},
        targeted={"passed": True, "rows": {}},
    )

    assert breakdown["s5b1_dimension_passed"] is True
    assert breakdown["s5b1_overlay_contract_passed"] is False
    assert breakdown["s5b1_contract_passed"] is False
    assert breakdown["dimension_failed_labels"] == []
    assert breakdown["overlay_not_evaluable_labels"] == ["M11"]
    assert breakdown["overlay_contract_missing_labels"] == ["M11"]
    assert breakdown["overlay_failure_kinds"] == ["M11_overlay_contract_missing"]


def test_stage5b1b_conditional_head_uses_visible_context_only_before_scoring(tmp_path: Path) -> None:
    teacher, s3a, s3a5, s3b1, assignments = _prepare_s5b1_fixture(tmp_path)
    assignment_path = tmp_path / "fixed_assignments.npy"
    np.save(assignment_path, assignments)
    output = tmp_path / "S5B1b"
    config = tmp_path / "stage5b1b.yaml"
    config.write_text(
        "\n".join(
            [
                "stage5b1_property_recovery:",
                f"  stage3a_dir: {s3a}",
                f"  stage3a5_dir: {s3a5}",
                f"  stage3b1_dir: {s3b1}",
                f"  teacher_dir: {teacher}",
                f"  output_dir: {output}",
                "  assignment_source: fixture_fixed_visible_assignments",
                f"  assignment_path: {assignment_path}",
                "  property_head_model: conditional_visible_context_property_head",
            ]
        )
        + "\n"
    )

    result = run_stage5b1b_conditional_property_recovery_from_config(config_path=config)

    head = result["s5b1_property_recovery_metrics"]
    assert result["decision"] == "stage5b1_property_recovery_passed"
    assert head["model_name"] == "conditional_visible_context_property_head"
    assert head["uses_oracle_location_or_strength_for_fit"] is False
    assert head["uses_evaluator_records_for_fit"] is False
    assert head["evaluator_records_loaded_after_fit_for_scoring"] is True
    assert result["claim_boundary"]["uses_oracle_location_or_strength_for_property_head_fit"] is False


def _prepare_s5b1_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path, np.ndarray]:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir()
    labels = ["M1", "M8", "M13", "M17", "M24"]
    records = []
    for context in range(5):
        for slot, label in enumerate(labels):
            records.append(_record(label, context, slot))
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    s3a = tmp_path / "S3A"
    s3a5 = tmp_path / "S3A5"
    run_stage3a_dataset_protocol_freeze(teacher_dir=teacher, output_dir=s3a, shots=1000, batch_size=5)
    run_stage3a5_observability_alias_ceiling(stage3a_dir=s3a, output_dir=s3a5)
    s3b1 = tmp_path / "S3B1"
    s3b1.mkdir()
    (s3b1 / "metrics.json").write_text(
        json.dumps(
            {
                "schema": "scope_static_stage3b1_fixture_metrics_v1",
                "decision": "stage3b1_first_discovery_model_completed",
                "acceptance_audit": {"passed": True},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    assignments = np.zeros((len(records), len(labels)), dtype=np.float64)
    label_to_index = {label: idx for idx, label in enumerate(labels)}
    for row, record in enumerate(records):
        assignments[row, label_to_index[str(record["oracle_label"])]] = 1.0
    np.save(s3b1 / "learned_assignments.npy", assignments)
    return teacher, s3a, s3a5, s3b1, assignments


def _record(label: str, context: int, slot: int) -> dict[str, object]:
    instruction = {
        "M1": "measure",
        "M8": "rzz",
        "M13": "rx",
        "M17": "reset",
        "M24": "id",
    }[label]
    parameters = {
        "M1": {"p": 0.02 + 0.001 * context},
        "M8": {"epsilon": 0.03 + 0.002 * context},
        "M13": {"epsilon": 0.025 + 0.002 * context, "operation_axis": "rx", "error_axis": "rx"},
        "M17": {"p": 0.015 + 0.001 * context},
        "M24": {"gamma_up": 0.01 + 0.001 * context},
    }[label]
    two_qubit = label == "M8"
    left = (context + slot) % 7
    return {
        "oracle_label": label,
        "mechanism_id": label,
        "name": MECHANISM_NAMES[label],
        "num_qubits": 2 if two_qubit else 1,
        "parameters": parameters,
        "instruction": instruction,
        "qubits": [left, (left + 1) % 7] if two_qubit else [left],
        "circuit_id": int(context),
        "location_id": int(100 * context + slot),
        "probe_indices": [],
    }
