from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scope_static.physical.sampled_observation_separability import _coverage, _weighted_metrics, run_sampled_observation_separability_audit, slot_only_leakage_control


def test_phyc2_reports_insufficient_grouped_sampled_observation_coverage(tmp_path: Path) -> None:
    teacher = tmp_path / "S2D_PHYS1_teacher"
    teacher.mkdir()
    records = [
        {
            "location_id": 0,
            "oracle_label": "M0",
            "mechanism_id": "M0",
            "name": "stochastic_pauli_gate_error",
            "num_qubits": 1,
            "parameters": {},
            "instruction": "id",
            "qubits": [0],
            "circuit_id": 0,
            "probe_indices": [0],
        },
        {
            "location_id": 1,
            "oracle_label": "M1",
            "mechanism_id": "M1",
            "name": "coherent_rzz_overrotation",
            "num_qubits": 2,
            "parameters": {"epsilon": 0.04},
            "instruction": "rzz",
            "qubits": [0, 1],
            "circuit_id": 0,
            "probe_indices": [0],
        },
    ]
    (teacher / "oracle_mechanisms.json").write_text(json.dumps({"mechanisms": records}))
    np.savez(teacher / "observations.npz", observations=np.zeros((1, 4, 2), dtype=np.uint8), probe_names=np.asarray(["cudaq_global_z"]))

    result = run_sampled_observation_separability_audit(teacher_dir=teacher, output_dir=tmp_path / "PHYC2")

    assert result["schema"] == "scope_static_phyc2_sampled_observation_separability_v1"
    assert result["stage"] == "PHYC2_sampled_observation_separability"
    assert result["contract_variant"] == "balanced"
    assert result["contract"]["name"] == "sampled_observations_are_learner_separable_balanced"
    assert result["contract_passed"] is False
    assert result["decision"] == "insufficient_sampled_observation_coverage"
    assert result["coverage"]["contract_evaluable"] is False
    assert (tmp_path / "PHYC2" / "metrics.json").exists()
    assert (tmp_path / "PHYC2" / "summary.md").exists()


def test_phyc2_balanced_requires_equal_class_support_but_weighted_allows_unequal_support() -> None:
    records = [
        {"oracle_label": "M0", "circuit_id": 0},
        {"oracle_label": "M0", "circuit_id": 1},
        {"oracle_label": "M0", "circuit_id": 2},
        {"oracle_label": "M1", "circuit_id": 0},
        {"oracle_label": "M1", "circuit_id": 1},
    ]
    observations = np.zeros((2, 4, 2), dtype=np.uint8)
    probe_names = ["z_basis", "x_measure"]

    balanced = _coverage(records, observations, probe_names, contract_variant="balanced")
    weighted = _coverage(records, observations, probe_names, contract_variant="weighted")

    assert balanced["balanced_class_support"] is False
    assert balanced["contract_evaluable"] is False
    assert balanced["reason"] == "PHYC2-balanced requires equal record support for every mechanism class"
    assert weighted["balanced_class_support"] is False
    assert weighted["contract_evaluable"] is True
    assert weighted["reason"] == "ok"


def test_phyc2_weighted_metrics_report_prevalence_accuracy_and_rare_recall() -> None:
    primary = {
        "confusion_matrix_labels": ["M0", "M1", "M2"],
        "confusion_matrix": [
            [8, 1, 1],
            [0, 2, 0],
            [1, 0, 1],
        ],
        "support": {"M0": 10, "M1": 2, "M2": 2},
        "per_class_recall": {"M0": 0.8, "M1": 1.0, "M2": 0.5},
    }

    metrics = _weighted_metrics(primary, rare_class_quantile=0.25)

    assert metrics["prevalence_weighted_accuracy"] == 11 / 14
    assert metrics["rare_class_names"] == ["M1", "M2"]
    assert metrics["rare_class_recall_min"] == 0.5


def test_slot_only_leakage_control_excludes_sampled_response_features() -> None:
    records = [
        {"oracle_label": "M0", "circuit_id": 0, "qubits": [0], "physical_qubits": [2], "probe_indices": [0, 1], "local_observable_slot_remap": True},
        {"oracle_label": "M1", "circuit_id": 0, "qubits": [1, 2], "physical_qubits": [3, 4], "probe_indices": [0, 1], "local_observable_slot_remap": True},
        {"oracle_label": "M0", "circuit_id": 1, "qubits": [2], "physical_qubits": [4], "probe_indices": [2, 3], "local_observable_slot_remap": True},
        {"oracle_label": "M1", "circuit_id": 1, "qubits": [3, 4], "physical_qubits": [5, 6], "probe_indices": [2, 3], "local_observable_slot_remap": True},
    ]
    observations = np.random.default_rng(0).integers(0, 2, size=(4, 8, 8), dtype=np.uint8)
    control = slot_only_leakage_control(records, ["p0", "p1", "p2", "p3"], observations, seed=0)

    assert control["schema"] == "scope_static_phyc2_slot_only_leakage_control_v1"
    assert control["control_name"] == "PHYC2.slot_only_leakage_control"
    assert "sampled_bits" in control["excluded_inputs"]
    assert all("response" not in name for name in control["feature_names"])
    assert all("corr" not in name for name in control["feature_names"])
