from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.experiments.qec_noise_catalog.teacher_physicality_audit import run_teacher_physicality_audit_from_config
from scope_static.primitives.mechanism_catalog import MECHANISM_NAMES
from scope_static.data_preparation import run_teacher_physicality_audit


def test_teacher_physicality_audit_accepts_cptp_povm_teacher_and_writes_bundle(tmp_path: Path) -> None:
    teacher = _write_teacher(
        tmp_path,
        [
            _record("M0", "M0", 0),
            _record("M1", "M1", 0, instruction="measure"),
            _record("M4", "M4", 1),
            _record("M8", "M8", 1, num_qubits=2, instruction="rzz"),
            _record("M13", "M13", 2, parameters={"operation_axis": "rx", "epsilon": 0.031, "epsilon_mean": 0.032, "epsilon_span": 0.018}, instruction="rx"),
            _record("M14", "M14", 2, parameters={"operation_axis": "rx", "error_axis": "rz", "epsilon": 0.028}, instruction="rx"),
            _record("M17", "M17", 2, instruction="reset"),
            _record("M34", "M34", 2),
        ],
    )
    output = tmp_path / "Layer1_teacher_physicality_audit"

    result = run_teacher_physicality_audit(teacher_dir=teacher, output_dir=output)

    assert result["decision"] == "teacher_physicality_passed"
    assert result["summary"]["teacher_physicality_passed"] is True
    assert result["claim_boundary"]["data_are_cptp"] is False
    assert result["claim_boundary"]["audits_generating_maps_not_data_as_cptp"] is True
    assert result["acceptance_audit"]["checks"]["all_local_quantum_channels_cptp_within_tolerance"] is True
    assert result["readout_stochasticity_audit"]["passed"] is True
    assert result["povm_instrument_audit"]["passed"] is True
    assert result["leakage_space_audit"]["silent_renormalization_used"] is False
    assert result["leakage_space_audit"]["records"][0]["true_qutrit_leakage_claim_allowed"] is False
    assert result["circuit_probability_audit"]["all_probability_distributions_valid"] is True
    assert float(result["summary"]["max_probability_sum_defect"]) <= 1.0e-12

    for name in [
        "config.yaml",
        "mechanism_catalog_manifest.json",
        "mechanism_parameter_ranges.json",
        "channel_representation_manifest.json",
        "unitary_audit.json",
        "kraus_audit.json",
        "choi_audit.json",
        "gksl_audit.json",
        "readout_stochasticity_audit.json",
        "povm_instrument_audit.json",
        "reset_prep_audit.json",
        "leakage_space_audit.json",
        "circuit_probability_audit.json",
        "sampling_audit.json",
        "physicality_by_mechanism.csv",
        "failure_cases.json",
        "summary.md",
    ]:
        assert (output / name).exists()


def test_teacher_physicality_audit_rejects_invalid_parameter_range(tmp_path: Path) -> None:
    teacher = _write_teacher(tmp_path, [_record("M4", "M4", 0, parameters={"gamma": 1.5})])

    result = run_teacher_physicality_audit(teacher_dir=teacher, output_dir=tmp_path / "audit")

    assert result["decision"] == "teacher_physicality_failed"
    assert result["summary"]["teacher_physicality_passed"] is False
    assert result["mechanism_parameter_ranges"]["passed"] is False
    assert result["failure_cases"]["total_failure_count"] > 0


def test_teacher_physicality_audit_rejects_invalid_observation_bits(tmp_path: Path) -> None:
    teacher = _write_teacher(tmp_path, [_record("M0", "M0", 0)])
    np.savez(teacher / "observations.npz", observations=np.asarray([[[0, 1], [2, 0]]], dtype=np.int64), probe_names=np.asarray(["bad"]), shots=np.asarray([2]))

    result = run_teacher_physicality_audit(teacher_dir=teacher, output_dir=tmp_path / "audit")

    assert result["decision"] == "teacher_physicality_failed"
    assert result["circuit_probability_audit"]["bit_values_are_binary"] is False
    assert result["acceptance_audit"]["checks"]["all_circuit_output_distributions_valid"] is False


def test_teacher_physicality_audit_config_wrapper_runs_from_yaml(tmp_path: Path) -> None:
    teacher = _write_teacher(tmp_path, [_record("M0", "M0", 0), _record("M1", "M1", 1, instruction="measure")])
    output = tmp_path / "configured"
    config = tmp_path / "teacher_physicality.yaml"
    config.write_text(
        "\n".join(
            [
                "teacher_physicality_audit:",
                f"  teacher_dir: {teacher}",
                f"  output_dir: {output}",
                "  tolerance_mode: strict",
            ]
        )
        + "\n"
    )

    result = run_teacher_physicality_audit_from_config(config_path=config)

    assert result["decision"] == "teacher_physicality_passed"
    assert (output / "summary.md").exists()


def _write_teacher(tmp_path: Path, records: list[dict[str, object]]) -> Path:
    teacher = tmp_path / "S2D_PHYC1_teacher"
    teacher.mkdir(exist_ok=True)
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}, indent=2) + "\n")
    observations = np.asarray(
        [
            [[0, 0], [0, 1], [1, 0], [1, 1]],
            [[0, 1], [0, 1], [1, 1], [1, 0]],
        ],
        dtype=np.uint8,
    )
    np.savez(teacher / "observations.npz", observations=observations, probe_names=np.asarray(["p0", "p1"]), shots=np.asarray([4]))
    (teacher / "sampling_audit.json").write_text(json.dumps({"schema": "test_sampling_audit", "total_wall_clock_seconds": 0.1}) + "\n")
    return teacher


def _record(
    label: str,
    mechanism_id: str,
    group: int,
    *,
    parameters: dict[str, object] | None = None,
    num_qubits: int = 1,
    instruction: str = "id",
) -> dict[str, object]:
    return {
        "oracle_label": label,
        "mechanism_id": mechanism_id,
        "name": MECHANISM_NAMES[mechanism_id],
        "num_qubits": int(num_qubits),
        "parameters": {} if parameters is None else dict(parameters),
        "instruction": instruction,
        "qubits": [0, 1] if int(num_qubits) == 2 else [0],
        "circuit_id": int(group),
        "location_id": int(group),
        "probe_indices": [],
    }
