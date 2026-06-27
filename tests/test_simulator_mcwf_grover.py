from __future__ import annotations

import json
import inspect

import pytest

import qec_twin.simulator.mcwf_grover as mcwf_grover
from qec_twin.simulator.cudaq_grover import grover_theory_prediction, optimal_grover_iterations
from qec_twin.simulator.mcwf_grover import compile_mcwf_grover_program, simulate_mcwf_qutrit_grover_leakage

torch = pytest.importorskip("torch", reason="MCWF Grover backend requires torch")
requires_cuda = pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="MCWF Grover backend is GPU-only; CUDA-MISSING is NOT A RELEASE BASIS",
)


@requires_cuda
def test_mcwf_qutrit_grover_measurement_backend_writes_artifacts(tmp_path):
    result = simulate_mcwf_qutrit_grover_leakage(
        num_qubits=3,
        marked_state="111",
        shots=8,
        seed=3,
        batch_size=4,
        out_dir=tmp_path / "mcwf_grover3",
    )

    assert result.artifacts is not None
    assert result.manifest["backend"] == "qec_twin.simulator.mcwf_backend.DenseQutritMcwfBackend"
    assert result.manifest["workload_adapter"] == "qec_twin.simulator.mcwf_grover"
    assert result.manifest["representability"] == "dense_qutrit_statevector_mcwf_leakage"
    assert result.manifest["algorithm"] == "single_solution_grover_gate_level"
    assert result.manifest["executor"]["schema"] == "qec_twin.simulator.GraphCapturedMcwfExecutor.v1"
    assert result.manifest["program"]["schema"] == "qec_twin.simulator.CompiledMcwfProgram.v1"
    assert result.manifest["program"]["description"] == "single_solution_grover_gate_level_with_qutrit_wg_leakage_slots"
    assert result.manifest["program"]["operation_counts"]["McwfKrausAllSitesOp"] == result.iterations + 1
    assert result.manifest["grover_realization"]["oracle"] == (
        "x_mask_to_all_ones_then_multi_controlled_phase_then_unmask"
    )
    assert result.manifest["noise"]["type"] == "qutrit_leakage_mcwf"
    assert result.manifest["decoder"] is None
    assert result.trajectory_summary["execution"]["executor"] == (
        "qec_twin.simulator.mcwf_executor.GraphCapturedMcwfExecutor"
    )
    assert result.trajectory_summary["execution"]["batches"] == 2
    assert result.trajectory_summary["execution"]["physics_program_s"] >= 0.0
    assert result.trajectory_summary["execution"]["measurement_sampling_s"] >= 0.0
    assert result.iterations == 2
    assert result.shots == 8
    assert sum(result.counts.values()) == 8
    assert sum(result.qutrit_counts.values()) == 8
    assert result.mean_pre_readout_marked_probability > 0.5
    assert 0.0 <= result.marked_fraction <= 1.0

    assert result.artifacts.measurement_counts.exists()
    assert result.artifacts.qutrit_outcome_counts.exists()
    assert result.artifacts.leakage_by_site.exists()
    assert result.artifacts.trajectory_summary.exists()
    assert result.artifacts.theory_prediction.exists()
    assert result.artifacts.manifest.exists()
    forbidden_suffixes = {".stim", ".dem", ".b8"}
    assert not any(path.suffix in forbidden_suffixes for path in result.artifacts.out_dir.iterdir())
    assert not (result.artifacts.out_dir / "decoder_results.json").exists()

    manifest = json.loads(result.artifacts.manifest.read_text())
    assert manifest["artifacts"]["measurement_counts"] == "measurement_counts.json"
    assert manifest["artifacts"]["qutrit_outcome_counts"] == "qutrit_outcome_counts.json"


@requires_cuda
def test_mcwf_grover_zero_leakage_matches_closed_form_without_basis_phase_shortcut():
    result = simulate_mcwf_qutrit_grover_leakage(
        num_qubits=3,
        marked_state="101",
        shots=4,
        seed=9,
        batch_size=2,
        theta=0.0,
        g_seep=0.0,
        g_heat=0.0,
    )
    theory = grover_theory_prediction(
        num_qubits=3,
        iterations=optimal_grover_iterations(3),
    )

    assert result.mean_pre_readout_marked_probability == pytest.approx(
        theory["success_probability"],
        abs=1e-12,
    )
    assert result.mean_final_leaked_sites == 0.0
    assert all("2" not in key for key in result.qutrit_counts)

    source = inspect.getsource(mcwf_grover)
    assert "apply_basis_phase" not in source


@requires_cuda
def test_mcwf_grover_block_trajectory_executor_matches_closed_form_zero_leakage():
    result = simulate_mcwf_qutrit_grover_leakage(
        num_qubits=3,
        marked_state="101",
        shots=4,
        seed=10,
        batch_size=2,
        theta=0.0,
        g_seep=0.0,
        g_heat=0.0,
        executor_mode="block_traj",
    )
    theory = grover_theory_prediction(
        num_qubits=3,
        iterations=optimal_grover_iterations(3),
    )

    assert result.manifest["executor"]["schema"] == "qec_twin.simulator.BlockTrajectoryMcwfExecutor.v1"
    assert result.manifest["kernel_backend"] == "block_trajectory_opstream_cuda"
    assert result.mean_pre_readout_marked_probability == pytest.approx(
        theory["success_probability"],
        abs=1e-12,
    )
    assert result.mean_final_leaked_sites == 0.0


def test_compile_mcwf_grover_program_is_gate_level_and_algorithm_neutral():
    program = compile_mcwf_grover_program(num_qutrits=3, marked_state="101", iterations=2)
    summary = program.summary()

    assert summary["schema"] == "qec_twin.simulator.CompiledMcwfProgram.v1"
    assert summary["num_qutrits"] == 3
    assert summary["num_operations"] == 38
    assert summary["operation_counts"] == {
        "McwfAllOnesPhaseOp": 4,
        "McwfCachedQubitGateOp": 31,
        "McwfKrausAllSitesOp": 3,
    }
