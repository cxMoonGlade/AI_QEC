from __future__ import annotations

import pytest

torch = pytest.importorskip("torch", reason="MCWF backend tests require torch")
requires_cuda = pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="Dense qutrit MCWF backend is GPU-only; CUDA-MISSING is NOT A RELEASE BASIS",
)

from qec_twin.simulator.mcwf_backend import (  # noqa: E402
    CDTYPE,
    DenseQuditMcwfBackend,
    DenseQutritMcwfBackend,
    qutrit_index_from_digits,
)
from qec_twin.simulator.mcwf_executor import (  # noqa: E402
    BlockTrajectoryMcwfExecutor,
    DenseQutritMcwfExecutor,
    GraphCapturedMcwfExecutor,
    NativeOpStreamMcwfExecutor,
)
from qec_twin.simulator.mcwf_program import CompiledMcwfProgram, all_ones_phase, h, kraus_all_sites, x  # noqa: E402


@requires_cuda
def test_dense_qudit_mcwf_backend_supports_qubit_hilbert_space():
    backend = DenseQuditMcwfBackend((2,), seed=101, device="cuda")
    inv = 2.0**-0.5
    h_gate = torch.tensor(
        [[inv, inv], [inv, -inv]],
        dtype=CDTYPE,
        device=backend.device,
    )

    psi = backend.basis_state(3, [0])
    out = backend.apply_operator(psi, h_gate, [0])
    probs = backend.probabilities(out)

    assert backend.local_dims == (2,)
    assert backend.dim == 2
    assert torch.allclose(
        probs,
        torch.full((3, 2), 0.5, dtype=probs.dtype, device=backend.device),
        atol=1e-12,
        rtol=1e-12,
    )


@requires_cuda
def test_dense_qudit_mcwf_backend_supports_qutrit_leakage_level():
    backend = DenseQuditMcwfBackend((3,), seed=102, device="cuda")
    leak_12 = torch.eye(3, dtype=CDTYPE, device=backend.device)
    leak_12[1, 1] = 0.0
    leak_12[2, 2] = 0.0
    leak_12[2, 1] = 1.0
    leak_12[1, 2] = 1.0

    psi = backend.basis_state(4, [1])
    out = backend.apply_operator(psi, leak_12, [0])
    probs = backend.probabilities(out)

    assert backend.index_from_digits([2]) == 2
    assert torch.allclose(
        probs[:, 2],
        torch.ones(4, dtype=probs.dtype, device=backend.device),
        atol=1e-12,
        rtol=1e-12,
    )
    assert torch.allclose(
        probs[:, 1],
        torch.zeros(4, dtype=probs.dtype, device=backend.device),
        atol=1e-12,
        rtol=1e-12,
    )


@requires_cuda
def test_dense_qudit_mcwf_backend_supports_ququart_level_and_measurement():
    backend = DenseQuditMcwfBackend((4,), seed=103, device="cuda")
    phase3 = torch.diag(
        torch.tensor([1.0, 1.0, 1.0, -1.0], dtype=CDTYPE, device=backend.device)
    )

    psi = backend.basis_state(5, [3])
    out = backend.apply_operator(psi, phase3, [0])
    outcomes, collapsed = backend.measure_sites(out, [0])

    assert backend.local_dims == (4,)
    assert torch.equal(outcomes, torch.full((5, 1), 3, dtype=torch.long, device=backend.device))
    assert torch.allclose(collapsed, -psi, atol=1e-12, rtol=1e-12)


@requires_cuda
def test_dense_qudit_mcwf_backend_samples_kraus_on_mixed_local_dimensions():
    backend = DenseQuditMcwfBackend((2, 4), seed=104, device="cuda")
    promote = torch.eye(4, dtype=CDTYPE, device=backend.device)
    promote[1, 1] = 0.0
    promote[3, 3] = 0.0
    promote[3, 1] = 1.0
    promote[1, 3] = 1.0

    psi = backend.basis_state(6, [1, 1])
    out = backend.apply_kraus(psi, promote.unsqueeze(0), [1])
    probs = backend.probabilities(out)
    target_index = backend.index_from_digits([1, 3])

    assert backend.local_dims == (2, 4)
    assert torch.allclose(
        probs[:, target_index],
        torch.ones(6, dtype=probs.dtype, device=backend.device),
        atol=1e-12,
        rtol=1e-12,
    )


@requires_cuda
def test_dense_qutrit_mcwf_backend_applies_generic_qutrit_matrix():
    backend = DenseQutritMcwfBackend(1, seed=1, device="cuda")

    psi = backend.basis_state(1, "0")
    psi = backend.apply_h(psi, 0)
    probs = backend.probabilities(psi)

    assert torch.allclose(
        probs[0, qutrit_index_from_digits((0,))],
        torch.tensor(0.5, dtype=probs.dtype, device=backend.device),
    )
    assert torch.allclose(
        probs[0, qutrit_index_from_digits((1,))],
        torch.tensor(0.5, dtype=probs.dtype, device=backend.device),
    )
    assert torch.allclose(
        probs[0, qutrit_index_from_digits((2,))],
        torch.tensor(0.0, dtype=probs.dtype, device=backend.device),
    )


@requires_cuda
def test_dense_qutrit_mcwf_backend_runs_non_grover_kraus_trajectory():
    backend = DenseQutritMcwfBackend(2, seed=7, device="cuda")
    psi = backend.basis_state(5, "11")

    swap_12 = torch.zeros((3, 3), dtype=CDTYPE)
    swap_12[0, 0] = 1.0
    swap_12[1, 2] = 1.0
    swap_12[2, 1] = 1.0
    psi = backend.apply_kraus_all_sites(psi, swap_12.unsqueeze(0))
    probs = backend.probabilities(psi)

    assert torch.allclose(
        probs[:, qutrit_index_from_digits((2, 2))],
        torch.ones(5, dtype=probs.dtype, device=backend.device),
    )

    measurement = backend.sample_measurements(probabilities=probs, leaked_readout_b=1.0)
    assert measurement.qutrit_counts == {"22": 5}
    assert measurement.bit_counts == {"11": 5}
    assert measurement.leaked_by_site_counts.tolist() == [5.0, 5.0]
    assert measurement.final_leaked_counts.tolist() == [2, 2, 2, 2, 2]


@requires_cuda
def test_multi_controlled_phase_does_not_fire_on_leaked_controls():
    backend = DenseQutritMcwfBackend(2, seed=11, device="cuda")
    psi = backend.basis_state(1, "12")

    out = backend.apply_computational_all_ones_phase(psi, phase=-1.0)
    assert torch.allclose(out, psi)

    psi11 = backend.basis_state(1, "11")
    out11 = backend.apply_computational_all_ones_phase(psi11, phase=-1.0)
    assert torch.allclose(out11, -psi11)


@requires_cuda
def test_qubit_gate_kernel_matches_torch_reference_for_one_two_three_qubit_gates():
    fast = DenseQutritMcwfBackend(3, seed=13, device="cuda", use_fused_kernels=True)
    ref = DenseQutritMcwfBackend(3, seed=13, device="cuda", use_fused_kernels=False)

    psi = torch.randn((4, 3**3), dtype=CDTYPE, device=fast.device)
    psi = psi / torch.linalg.vector_norm(psi, dim=1, keepdim=True)

    h = fast._cached_qubit_gate("h")
    cx = torch.eye(4, dtype=CDTYPE, device=fast.device)
    cx[2, 2] = 0
    cx[3, 3] = 0
    cx[2, 3] = 1
    cx[3, 2] = 1
    ccx = torch.eye(8, dtype=CDTYPE, device=fast.device)
    ccx[6, 6] = 0
    ccx[7, 7] = 0
    ccx[6, 7] = 1
    ccx[7, 6] = 1

    for gate, sites in [(h, [1]), (cx, [0, 2]), (ccx, [0, 1, 2])]:
        out_fast = fast.apply_qubit_gate(psi, gate, sites)
        out_ref = ref.apply_qubit_gate(psi, gate, sites)
        assert torch.allclose(out_fast, out_ref, atol=1e-12, rtol=1e-12)


@requires_cuda
def test_kraus_kernel_matches_torch_reference_for_same_random_stream():
    fast = DenseQutritMcwfBackend(2, seed=17, device="cuda", use_fused_kernels=True)
    ref = DenseQutritMcwfBackend(2, seed=17, device="cuda", use_fused_kernels=False)

    psi = torch.randn((6, 3**2), dtype=CDTYPE, device=fast.device)
    psi = psi / torch.linalg.vector_norm(psi, dim=1, keepdim=True)
    kraus = torch.zeros((2, 3, 3), dtype=CDTYPE, device=fast.device)
    kraus[0] = torch.eye(3, dtype=CDTYPE, device=fast.device)
    kraus[0, 2, 2] = 0.0
    kraus[1, 1, 2] = 1.0

    out_fast = fast.apply_kraus_site(psi, kraus, 0)
    out_ref = ref.apply_kraus_site(psi, kraus, 0)
    assert torch.allclose(out_fast, out_ref, atol=1e-12, rtol=1e-12)


@requires_cuda
def test_kraus_all_sites_kernel_matches_torch_reference_for_same_random_stream():
    fast = DenseQutritMcwfBackend(3, seed=19, device="cuda", use_fused_kernels=True)
    ref = DenseQutritMcwfBackend(3, seed=19, device="cuda", use_fused_kernels=False)

    psi = torch.randn((5, 3**3), dtype=CDTYPE, device=fast.device)
    psi = psi / torch.linalg.vector_norm(psi, dim=1, keepdim=True)
    kraus = torch.zeros((2, 3, 3), dtype=CDTYPE, device=fast.device)
    kraus[0] = torch.eye(3, dtype=CDTYPE, device=fast.device)
    kraus[0, 2, 2] = 0.0
    kraus[1, 1, 2] = 1.0

    out_fast = fast.apply_kraus_all_sites(psi, kraus, sites=(0, 2))
    out_ref = ref.apply_kraus_all_sites(psi, kraus, sites=(0, 2))
    assert torch.allclose(out_fast, out_ref, atol=1e-12, rtol=1e-12)


@requires_cuda
def test_dense_qutrit_mcwf_executor_runs_generic_program_and_reports_timing():
    backend = DenseQutritMcwfBackend(2, seed=23, device="cuda")
    executor = DenseQutritMcwfExecutor(backend)

    kraus = torch.zeros((1, 3, 3), dtype=CDTYPE, device=backend.device)
    kraus[0] = torch.eye(3, dtype=CDTYPE, device=backend.device)
    program = CompiledMcwfProgram(
        num_qutrits=2,
        operations=(
            h(0),
            h(1),
            kraus_all_sites("identity", (0, 1)),
        ),
        description="executor_smoke",
    )

    result = executor.run(program, batch_size=3, kraus_families={"identity": kraus})
    probs = backend.probabilities(result.psi)

    assert result.psi.shape == (3, 3**2)
    assert result.timing.timing_method == "cuda_event"
    assert result.timing.physics_program_s >= 0.0
    assert executor.manifest()["schema"] == "qec_twin.simulator.DenseQutritMcwfExecutor.v1"
    for qidx in [qutrit_index_from_digits((0, 0)), qutrit_index_from_digits((0, 1)),
                 qutrit_index_from_digits((1, 0)), qutrit_index_from_digits((1, 1))]:
        assert torch.allclose(
            probs[:, qidx],
            torch.full((3,), 0.25, dtype=probs.dtype, device=backend.device),
            atol=1e-12,
            rtol=1e-12,
        )
    assert torch.allclose(
        probs[:, qutrit_index_from_digits((2, 2))],
        torch.zeros(3, dtype=probs.dtype, device=backend.device),
    )


@requires_cuda
def test_native_opstream_executor_matches_dense_torch_reference():
    fast_backend = DenseQutritMcwfBackend(3, seed=29, device="cuda", use_fused_kernels=True)
    ref_backend = DenseQutritMcwfBackend(3, seed=29, device="cuda", use_fused_kernels=False)
    native = NativeOpStreamMcwfExecutor(fast_backend)
    dense_ref = DenseQutritMcwfExecutor(ref_backend)

    kraus = torch.zeros((2, 3, 3), dtype=CDTYPE, device=fast_backend.device)
    kraus[0] = torch.eye(3, dtype=CDTYPE, device=fast_backend.device)
    kraus[0, 2, 2] = 0.0
    kraus[1, 1, 2] = 1.0
    program = CompiledMcwfProgram(
        num_qutrits=3,
        operations=(
            h(0),
            x(1),
            all_ones_phase((0, 1, 2)),
            kraus_all_sites("leak", (0, 2)),
            h(2),
        ),
        description="native_opstream_equivalence",
    )

    out_native = native.run(program, batch_size=7, kraus_families={"leak": kraus}).psi
    out_ref = dense_ref.run(program, batch_size=7, kraus_families={"leak": kraus}).psi

    assert native.manifest()["schema"] == "qec_twin.simulator.NativeOpStreamMcwfExecutor.v1"
    assert torch.allclose(out_native, out_ref, atol=1e-12, rtol=1e-12)


@requires_cuda
def test_native_and_block_executors_exactly_coalesce_adjacent_x_layer():
    fast_backend = DenseQutritMcwfBackend(3, seed=28, device="cuda", use_fused_kernels=True)
    block_backend = DenseQutritMcwfBackend(3, seed=28, device="cuda", use_fused_kernels=True)
    ref_backend = DenseQutritMcwfBackend(3, seed=28, device="cuda", use_fused_kernels=False)
    native = NativeOpStreamMcwfExecutor(fast_backend)
    block = BlockTrajectoryMcwfExecutor(block_backend)
    dense_ref = DenseQutritMcwfExecutor(ref_backend)

    program = CompiledMcwfProgram(
        num_qutrits=3,
        operations=(
            x(0),
            x(1),
            x(2),
            all_ones_phase((0, 1, 2)),
            x(2),
            x(0),
        ),
        initial_levels=(2, 0, 1),
        description="adjacent_x_layer_equivalence_with_leakage",
    )

    out_native = native.run(program, batch_size=3, kraus_families={}).psi
    out_block = block.run(program, batch_size=3, kraus_families={}).psi
    out_ref = dense_ref.run(program, batch_size=3, kraus_families={}).psi

    assert torch.allclose(out_native, out_ref, atol=1e-12, rtol=1e-12)
    assert torch.allclose(out_block, out_ref, atol=1e-12, rtol=1e-12)


@requires_cuda
def test_block_trajectory_executor_matches_native_opstream_reference():
    block_backend = DenseQutritMcwfBackend(3, seed=30, device="cuda", use_fused_kernels=True)
    native_backend = DenseQutritMcwfBackend(3, seed=30, device="cuda", use_fused_kernels=True)
    block = BlockTrajectoryMcwfExecutor(block_backend)
    native = NativeOpStreamMcwfExecutor(native_backend)

    kraus = torch.zeros((2, 3, 3), dtype=CDTYPE, device=block_backend.device)
    kraus[0] = torch.eye(3, dtype=CDTYPE, device=block_backend.device)
    kraus[0, 2, 2] = 0.0
    kraus[1, 1, 2] = 1.0
    program = CompiledMcwfProgram(
        num_qutrits=3,
        operations=(
            h(0),
            x(1),
            all_ones_phase((0, 1, 2)),
            kraus_all_sites("leak", (0, 2)),
            h(2),
        ),
        description="block_trajectory_equivalence",
    )

    out_block = block.run(program, batch_size=7, kraus_families={"leak": kraus}).psi
    out_native = native.run(program, batch_size=7, kraus_families={"leak": kraus}).psi

    assert block.manifest()["schema"] == "qec_twin.simulator.BlockTrajectoryMcwfExecutor.v1"
    assert torch.allclose(out_block, out_native, atol=1e-12, rtol=1e-12)


@requires_cuda
def test_block_trajectory_executor_runs_deterministic_program_without_kraus_ops():
    block_backend = DenseQutritMcwfBackend(2, seed=32, device="cuda", use_fused_kernels=True)
    native_backend = DenseQutritMcwfBackend(2, seed=32, device="cuda", use_fused_kernels=True)
    block = BlockTrajectoryMcwfExecutor(block_backend)
    native = NativeOpStreamMcwfExecutor(native_backend)
    program = CompiledMcwfProgram(
        num_qutrits=2,
        operations=(
            h(0),
            x(1),
            all_ones_phase((0, 1)),
            h(1),
        ),
        description="block_trajectory_no_kraus",
    )

    out_block = block.run(program, batch_size=5, kraus_families={}).psi
    out_native = native.run(program, batch_size=5, kraus_families={}).psi

    assert torch.allclose(out_block, out_native, atol=1e-12, rtol=1e-12)


@requires_cuda
def test_graph_captured_executor_matches_native_opstream_reference():
    graph_backend = DenseQutritMcwfBackend(3, seed=31, device="cuda", use_fused_kernels=True)
    native_backend = DenseQutritMcwfBackend(3, seed=31, device="cuda", use_fused_kernels=True)
    graph = GraphCapturedMcwfExecutor(graph_backend)
    native = NativeOpStreamMcwfExecutor(native_backend)

    kraus = torch.zeros((2, 3, 3), dtype=CDTYPE, device=graph_backend.device)
    kraus[0] = torch.eye(3, dtype=CDTYPE, device=graph_backend.device)
    kraus[0, 2, 2] = 0.0
    kraus[1, 1, 2] = 1.0
    program = CompiledMcwfProgram(
        num_qutrits=3,
        operations=(
            h(0),
            x(1),
            all_ones_phase((0, 1, 2)),
            kraus_all_sites("leak", (0, 2)),
            h(2),
        ),
        description="graph_capture_equivalence",
    )

    out_graph = graph.run(program, batch_size=7, kraus_families={"leak": kraus}).psi
    out_native = native.run(program, batch_size=7, kraus_families={"leak": kraus}).psi

    assert graph.manifest()["schema"] == "qec_twin.simulator.GraphCapturedMcwfExecutor.v1"
    assert torch.allclose(out_graph, out_native, atol=1e-12, rtol=1e-12)


@requires_cuda
def test_graph_captured_executor_replay_updates_random_stream_like_native():
    graph_backend = DenseQutritMcwfBackend(3, seed=37, device="cuda", use_fused_kernels=True)
    native_backend = DenseQutritMcwfBackend(3, seed=37, device="cuda", use_fused_kernels=True)
    graph = GraphCapturedMcwfExecutor(graph_backend)
    native = NativeOpStreamMcwfExecutor(native_backend)

    kraus = torch.zeros((2, 3, 3), dtype=CDTYPE, device=graph_backend.device)
    kraus[0] = torch.eye(3, dtype=CDTYPE, device=graph_backend.device)
    kraus[0, 2, 2] = 0.0
    kraus[1, 1, 2] = 1.0
    program = CompiledMcwfProgram(
        num_qutrits=3,
        operations=(
            h(0),
            kraus_all_sites("leak", (0, 1, 2)),
            all_ones_phase((0, 1, 2)),
            kraus_all_sites("leak", (2,)),
        ),
        description="graph_replay_random_equivalence",
    )

    first_graph = graph.run(program, batch_size=5, kraus_families={"leak": kraus}).psi.clone()
    first_native = native.run(program, batch_size=5, kraus_families={"leak": kraus}).psi
    second_graph = graph.run(program, batch_size=5, kraus_families={"leak": kraus}).psi.clone()
    second_native = native.run(program, batch_size=5, kraus_families={"leak": kraus}).psi

    assert torch.allclose(first_graph, first_native, atol=1e-12, rtol=1e-12)
    assert torch.allclose(second_graph, second_native, atol=1e-12, rtol=1e-12)


@requires_cuda
def test_graph_captured_executor_replay_updates_kraus_values_for_same_shape():
    backend = DenseQutritMcwfBackend(1, seed=41, device="cuda", use_fused_kernels=True)
    graph = GraphCapturedMcwfExecutor(backend)

    identity = torch.eye(3, dtype=CDTYPE, device=backend.device).reshape(1, 3, 3)
    swap_12 = torch.zeros((1, 3, 3), dtype=CDTYPE, device=backend.device)
    swap_12[0, 0, 0] = 1.0
    swap_12[0, 1, 2] = 1.0
    swap_12[0, 2, 1] = 1.0
    program = CompiledMcwfProgram(
        num_qutrits=1,
        operations=(kraus_all_sites("leak", (0,)),),
        initial_levels=(1,),
        description="graph_replay_kraus_value_refresh",
    )

    first = graph.run(program, batch_size=4, kraus_families={"leak": identity}).psi.clone()
    second = graph.run(program, batch_size=4, kraus_families={"leak": swap_12}).psi.clone()
    first_probs = backend.probabilities(first)
    second_probs = backend.probabilities(second)

    assert torch.allclose(
        first_probs[:, qutrit_index_from_digits((1,))],
        torch.ones(4, dtype=first_probs.dtype, device=backend.device),
        atol=1e-12,
        rtol=1e-12,
    )
    assert torch.allclose(
        second_probs[:, qutrit_index_from_digits((2,))],
        torch.ones(4, dtype=second_probs.dtype, device=backend.device),
        atol=1e-12,
        rtol=1e-12,
    )
