from __future__ import annotations

import json
from pathlib import Path

from scope_static.physical.sampled_quantum_error_quality import channel_vector, run_sampled_quantum_error_quality_audit


def test_channel_vector_represents_quantum_and_readout_errors() -> None:
    quantum = channel_vector(
        {
            "oracle_label": "M6",
            "mechanism_id": "M6",
            "name": "coherent_rx_overrotation",
            "num_qubits": 1,
            "parameters": {"epsilon": 0.035},
            "instruction": "rx",
            "qubits": [0],
            "circuit_id": 0,
            "probe_indices": [0],
        }
    )
    readout = channel_vector(
        {
            "oracle_label": "M1",
            "mechanism_id": "M1",
            "name": "readout_0_to_1_bias",
            "num_qubits": 1,
            "parameters": {"p": 0.025},
            "instruction": "measure",
            "qubits": [0],
            "circuit_id": 0,
            "probe_indices": [0],
        }
    )

    assert quantum.representation == "pauli_transfer_matrix"
    assert quantum.family == "quantum_ptm:1q:4x4"
    assert quantum.vector.shape == (16,)
    assert readout.representation == "readout_assignment_matrix"
    assert readout.family == "readout_assignment:2x2"
    assert readout.vector.shape == (4,)


def test_phyc3_quantum_error_quality_uses_phyc2_fold_predictions(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYS1_teacher"
    phyc2 = tmp_path / "PHYC2"
    output = tmp_path / "PHYC3"
    teacher.mkdir()
    phyc2.mkdir()
    records = [
        _record(0, "M0", "stochastic_pauli_gate_error", "id", {"p_x": 0.0015, "p_y": 0.0008, "p_z": 0.0022}),
        _record(1, "M6", "coherent_rx_overrotation", "rx", {"epsilon": 0.25}),
        _record(2, "M0", "stochastic_pauli_gate_error", "id", {"p_x": 0.0015, "p_y": 0.0008, "p_z": 0.0022}, circuit_id=1),
        _record(3, "M6", "coherent_rx_overrotation", "rx", {"epsilon": 0.25}, circuit_id=1),
    ]
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}) + "\n")
    phyc2_metrics = {
        "balanced_accuracy": 1.0,
        "min_class_recall": 1.0,
        "prevalence_weighted_accuracy": 1.0,
        "rare_class_recall_min": 1.0,
        "supervised_grouped_ceiling": {
            "grouped_fold_predictions": [
                {"fold": 0, "test_circuit_id": 0, "true_labels": ["M0", "M6"], "predicted_labels": ["M0", "M6"]},
                {"fold": 1, "test_circuit_id": 1, "true_labels": ["M0", "M6"], "predicted_labels": ["M0", "M6"]},
            ]
        },
    }
    (phyc2 / "metrics.json").write_text(json.dumps(phyc2_metrics) + "\n")

    result = run_sampled_quantum_error_quality_audit(teacher_dir=teacher, phyc2_dir=phyc2, output_dir=output)

    assert result["schema"] == "scope_static_phyc3_sampled_quantum_error_quality_v1"
    assert result["stage"] == "PHYC3_sampled_quantum_error_quality"
    assert result["contract_passed"] is True
    assert result["mechanism_classification"]["balanced_accuracy"] == 1.0
    assert result["quality_summary"]["num_records"] == 4
    assert result["quality_summary"]["incompatible_prediction_count"] == 0
    assert result["quality_summary"]["predicted_channel_distance"]["mean"] == 0.0
    assert (output / "metrics.json").exists()
    assert (output / "summary.md").exists()


def _record(
    location_id: int,
    mechanism_id: str,
    name: str,
    instruction: str,
    parameters: dict[str, float],
    *,
    circuit_id: int = 0,
) -> dict[str, object]:
    return {
        "location_id": int(location_id),
        "oracle_label": mechanism_id,
        "mechanism_id": mechanism_id,
        "name": name,
        "num_qubits": 1,
        "parameters": parameters,
        "instruction": instruction,
        "qubits": [0],
        "circuit_id": int(circuit_id),
        "probe_indices": [0],
    }
