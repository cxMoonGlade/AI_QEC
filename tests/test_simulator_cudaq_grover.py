from __future__ import annotations

import json

import numpy as np
import pytest

from error_coupling_simulator.frontend.cudaq_grover import (
    bitstring_from_index,
    grover_theory_prediction,
    index_from_bitstring,
    normalize_marked_state,
    optimal_grover_iterations,
    simulate_cudaq_grover_noiseless,
)


cudaq = pytest.importorskip("cudaq", reason="CUDA-Q Grover backend requires cudaq")


def test_bitstring_convention_is_cudaq_allocation_order():
    assert index_from_bitstring("100") == 1
    assert index_from_bitstring("010") == 2
    assert index_from_bitstring("001") == 4
    assert bitstring_from_index(5, 3) == "101"
    assert normalize_marked_state(5, 3) == "101"


def test_cudaq_grover_small_state_matches_closed_form():
    result = simulate_cudaq_grover_noiseless(
        num_qubits=3,
        marked_state="101",
        shots=0,
    )
    theory = grover_theory_prediction(
        num_qubits=3,
        iterations=optimal_grover_iterations(3),
    )

    assert result.iterations == 2
    assert result.marked_state == "101"
    assert result.marked_index == index_from_bitstring("101")
    assert result.shots == 0
    assert result.counts == {}
    assert result.marked_probability == pytest.approx(theory["success_probability"], abs=2e-6)
    assert np.isclose(result.probabilities.sum(), 1.0)


def test_cudaq_grover_12q_noiseless_artifacts(tmp_path):
    result = simulate_cudaq_grover_noiseless(
        num_qubits=12,
        marked_state="1" * 12,
        shots=128,
        seed=7,
        out_dir=tmp_path / "grover12",
    )

    assert result.artifacts is not None
    assert result.iterations == optimal_grover_iterations(12)
    assert result.statevector.shape == (4096,)
    assert result.probabilities.shape == (4096,)
    assert result.marked_probability > 0.999
    assert result.marked_counts >= 120
    assert result.artifacts.statevector.exists()
    assert result.artifacts.probabilities.exists()
    assert result.artifacts.measurement_counts.exists()
    assert result.artifacts.theory_prediction.exists()
    assert result.artifacts.manifest.exists()
    forbidden_suffixes = {".stim", ".dem", ".b8"}
    assert not any(path.suffix in forbidden_suffixes for path in result.artifacts.out_dir.iterdir())
    assert not (result.artifacts.out_dir / "decoder_results.json").exists()

    manifest = json.loads(result.artifacts.manifest.read_text())
    assert manifest["schema"] == "error_coupling_simulator.frontend.cudaq_grover_noiseless.v1"
    assert manifest["backend"] == "cudaq"
    assert manifest["representability"] == "cudaq_statevector_noiseless"
    assert manifest["algorithm"] == "single_solution_grover"
    assert manifest["noise"] is None
    assert manifest["num_qubits"] == 12
    assert manifest["marked_state"] == "1" * 12
    assert manifest["artifacts"]["statevector"] == "statevector.npy"
    assert np.load(result.artifacts.probabilities).shape == (4096,)
