from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from scope_static.experiments.qec_noise_catalog.data_preparation_teacher import run_data_preparation_teacher_from_config
from scope_static.data_preparation import (
    build_layer1p_pre_sampling_contract,
    generate_layer1p_teacher_dataset,
)


def _reset_cudaq_target_if_available() -> None:
    cudaq = pytest.importorskip("cudaq")
    if hasattr(cudaq, "reset_target"):
        cudaq.reset_target()


def _skip_unless_cudaq_smoke_enabled() -> None:
    if os.environ.get("AIQEC_RUN_CUDAQ_SMOKE") != "1":
        pytest.skip("set AIQEC_RUN_CUDAQ_SMOKE=1 to run CUDA-Q Layer1.P smoke")


def test_layer1p_teacher_generates_first_class_physical_teacher(tmp_path: Path) -> None:
    _skip_unless_cudaq_smoke_enabled()
    _reset_cudaq_target_if_available()
    output = tmp_path / "Layer1P_teacher"

    result = generate_layer1p_teacher_dataset(_small_config(), output_dir=output)

    assert result["decision"] == "layer1p_teacher_generated"
    assert result["stage"] == "Layer1.P_teacher"
    assert result["claim_boundary"]["is_teacher_generator_not_posthoc_only_audit"] is True
    assert result["claim_boundary"]["pre_sampling_cptp_povm_contract_enforced"] is True
    assert result["pre_sampling_contract"]["passed"] is True
    assert result["acceptance_audit"]["passed"] is True
    assert result["layer1p_teacher_contract"]["pre_sampling_contract_passed"] is True
    assert result["layer1p_teacher_contract"]["post_sampling_physicality_passed"] is True
    assert result["layer1p_teacher_contract"]["sampling_completed"] is True
    assert result["teacher_physicality_audit"]["decision"] == "teacher_physicality_passed"

    summary = json.loads((output / "summary.json").read_text())
    assert summary["stage"] == "Layer1.P_teacher"
    assert (output / "full_circuit_cudaq_summary.json").exists()
    assert (output / "layer1p_teacher_contract.json").exists()
    assert (output / "layer1p_pre_sampling_contract.json").exists()
    assert (output / "Layer1_teacher_physicality_audit" / "metrics.json").exists()
    observations = np.load(output / "observations.npz")
    assert observations["observations"].shape == (3, 8, 2)


def test_layer1p_pre_sampling_contract_rejects_ill_defined_m14_before_sampling(tmp_path: Path) -> None:
    config = {
        "num_qubits": 5,
        "circuit_depth": 1,
        "probe_set": "base",
        "mechanism_set": ["M14"],
        "balanced_min_instances_per_mechanism": 1,
        "mechanisms": {"M14": {"operation_axis": "rx", "error_axis": "rx", "epsilon": 0.028}},
        "shots": 8,
        "cudaq_target": "",
        "full_circuit_cudaq_progress_logging": False,
    }

    contract = build_layer1p_pre_sampling_contract(config)

    assert contract["passed"] is False
    assert contract["checks"]["mechanism_definition_contract_passed"] is False
    with pytest.raises(ValueError):
        generate_layer1p_teacher_dataset(config, output_dir=tmp_path / "bad")
    assert not (tmp_path / "bad" / "observations.npz").exists()


def test_layer1p_teacher_config_wrapper_runs_from_yaml(tmp_path: Path) -> None:
    _skip_unless_cudaq_smoke_enabled()
    _reset_cudaq_target_if_available()
    output = tmp_path / "configured"
    config = tmp_path / "layer1p.yaml"
    config.write_text(
        "\n".join(
            [
                "data_preparation_teacher:",
                f"  output_dir: {output}",
                "  teacher_config:",
                "    num_qubits: 2",
                "    circuit_depth: 1",
                "    probe_set: base",
                "    mechanism_set: [M8]",
                "    balanced_min_instances_per_mechanism: 1",
                "    shots: 8",
                "    seed: 3",
                "    cudaq_target: ''",
                "    full_circuit_cudaq_progress_logging: false",
            ]
        )
        + "\n"
    )

    result = run_data_preparation_teacher_from_config(config_path=config)

    assert result["decision"] == "layer1p_teacher_generated"
    assert (output / "summary.json").exists()
    assert (output / "Layer1_teacher_physicality_audit" / "metrics.json").exists()


def _small_config() -> dict[str, object]:
    return {
        "num_qubits": 2,
        "circuit_depth": 1,
        "probe_set": "base",
        "mechanism_set": ["M8"],
        "balanced_min_instances_per_mechanism": 1,
        "shots": 8,
        "seed": 0,
        "cudaq_target": "",
        "full_circuit_cudaq_progress_logging": False,
    }
