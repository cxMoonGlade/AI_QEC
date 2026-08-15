"""Shared current-PEPO fixtures and memory-safe reference helpers.

The expensive PEPO integration cases live in separate test files so the service
acceptance supervisor gives each native/CUDA lifetime its own process.  Keeping
their common state construction here avoids cloning either the physical setup or
the dense reference operation across those files.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch


LEAKAGE_RATE_TARGET = 5.0e-3
G_SEEP = 0.09
G_HEAT = 0.0
B_BIAS = 0.9
ARM = "A"
TOL_EXACT = 1.0e-12
TOL_TRACE = 1.0e-10

CUDA_AVAILABLE = torch.cuda.is_available()
requires_cuda = pytest.mark.skipif(
    not CUDA_AVAILABLE,
    reason="CUDA unavailable — the current PEPO density carrier is GPU-only",
)


def pepo_modules():
    """Import the current PEPO implementation only when a test executes."""
    from error_coupling_simulator.carrier.pepo import dynamics, layout, sampler

    return layout, dynamics, sampler


def max_abs_diff(a: torch.Tensor, b: torch.Tensor, block: int = 2048) -> float:
    """Chunked max difference without allocating a full dense temporary.

    The independent reference may live on the host so the GPU never has to hold
    both a 5.77 GiB exact density matrix and the expanded PEPO carrier at once.
    """

    assert a.shape == b.shape, (a.shape, b.shape)
    worst = 0.0
    for i0 in range(0, a.shape[0], block):
        reference = b[i0 : i0 + block]
        if reference.device != a.device:
            reference = reference.to(a.device)
        delta = float((a[i0 : i0 + block] - reference).abs().max().item())
        if not np.isfinite(delta):
            raise RuntimeError("non-finite value in dense-reference comparison")
        worst = max(worst, delta)
    return worst


def release_cuda() -> None:
    """Release cached device allocations within one test process."""
    if CUDA_AVAILABLE:
        torch.cuda.empty_cache()


def build_schedule():
    """Load the real d3 XZZX schedule required by these carrier checks."""
    xp = pytest.importorskip("error_coupling_simulator.frontend.xzzx_parser")
    r01c, r01m = xp.default_r01_paths()
    r10c, r10m = xp.default_r10_paths()
    if not (r01c.is_file() and r01m.is_file() and r10c.is_file() and r10m.is_file()):
        pytest.skip(
            "d3 XZZX r01/r10 circuits absent under ECS_D3_DATA_ROOT "
            "(real patch required; no synthetic fallback)"
        )
    schedule = xp.parse_xzzx_circuit(r01c, r01m, verify=True)
    schedule = schedule.with_within_cycle_streams(
        xp.parse_within_cycle_streams(r10c, r10m)
    )
    assert int(schedule.n_data) == 9
    assert len(schedule.stabilizers) == 8
    return schedule


@pytest.fixture(scope="session")
def sched():
    return build_schedule()


def build_within_cycle_cell(schedule):
    """Build the current within-cycle qutrit leakage cell."""
    if not CUDA_AVAILABLE:
        pytest.skip("CUDA unavailable — within-cycle qutrit carrier requires GPU")

    from error_coupling_simulator.carrier.within_cycle import (
        FusedWithinCycleSampler,
        RunSpec,
    )
    from error_coupling_simulator.frontend import xzzx_parser as xp
    from error_coupling_simulator.mechanisms.qutrit_leakage import (
        solve_exchange_angle_for_leakage_rate,
    )

    r01c, r01m = xp.default_r01_paths()
    theta = float(
        solve_exchange_angle_for_leakage_rate(LEAKAGE_RATE_TARGET, g_seep=G_SEEP, g_heat=G_HEAT)
    )
    host = FusedWithinCycleSampler(device="cuda")
    spec = RunSpec(
        circuit_path=r01c,
        metadata_path=r01m,
        m=0,
        theta=theta,
        g_seep=G_SEEP,
        g_heat=G_HEAT,
        arm=ARM,
        b=B_BIAS,
        readout_conv="biased_b",
        N=1,
        base_seed=0,
        R=1,
        dtype="c128",
    )
    leak_t, leak_evidence = host.build_within_cycle_leak(spec)
    assert leak_evidence["cptp_residual"] < TOL_EXACT, leak_evidence
    marshalled = host.marshal_within_cycle(schedule, leak_t, R=1)
    return {
        "sched": schedule,
        "theta": theta,
        "leak_t": leak_t,
        "leak_list": list(marshalled.leak_kraus),
        "streams": dict(marshalled.streams_by_pos),
        "stabs": schedule.stab_paulis(),
        "host": host,
    }


@pytest.fixture(scope="session")
def wc(sched):
    return build_within_cycle_cell(sched)


def fresh_referee(schedule):
    """Construct the exact density-matrix reference on the same code geometry."""
    from error_coupling_simulator.carrier.exact.qutrit_dm import QutritDM

    logical = dict(schedule.logical)
    logical_kind = str(schedule.logical_kind).upper()
    engine = QutritDM(int(schedule.n_data), device="cuda")
    engine.set_code(
        stabilizers=schedule.stab_paulis(),
        logical_z=logical if logical_kind == "Z" else None,
        logical_x=logical if logical_kind == "X" else None,
    )
    return engine


def prep_pair(
    cell,
    seed: int,
    *,
    n_ops: int = 5,
    leak_pump: tuple[int, ...] = (),
    m: int = 0,
):
    """Evolve mirrored PEPO and exact-DM states through one token program."""
    layout, dynamics, _ = pepo_modules()
    state = layout.build_codestate_pepo(cell["sched"], m, device="cuda")
    engine = fresh_referee(cell["sched"])
    engine.init_logical(m)
    program = _token_program(seed, n_ops=n_ops, leak_pump=leak_pump)
    for token, site in program:
        dynamics.apply_token_stream(state, {site: (token,)}, cell["leak_t"])
        engine.apply_within_cycle_premeasure({site: (token,)}, cell["leak_list"])
    return state, engine


def prep_reference(
    cell,
    seed: int,
    *,
    n_ops: int = 5,
    leak_pump: tuple[int, ...] = (),
    m: int = 0,
):
    """Evolve only the independent exact-density reference."""

    engine = fresh_referee(cell["sched"])
    engine.init_logical(m)
    for token, site in _token_program(seed, n_ops=n_ops, leak_pump=leak_pump):
        engine.apply_within_cycle_premeasure(
            {site: (token,)},
            cell["leak_list"],
        )
    return engine


def _token_program(
    seed: int,
    *,
    n_ops: int,
    leak_pump: tuple[int, ...],
) -> tuple[tuple[str, int], ...]:
    """Return the deterministic physical token program shared by both prep paths."""

    program: list[tuple[str, int]] = []
    rng = np.random.default_rng(seed)
    for _ in range(n_ops):
        program.append((str(rng.choice(["H", "X", "LEAK"])), int(rng.integers(0, 9))))
    for site in leak_pump:
        program.extend([("LEAK", int(site))] * 4)
    return tuple(program)


def prep_state(
    cell,
    seed: int,
    *,
    n_ops: int = 5,
    leak_pump: tuple[int, ...] = (),
    m: int = 0,
):
    """Evolve only PEPO state when a test has no exact-reference assertion.

    Constructing a 3**9 by 3**9 complex128 density matrix costs about 5.77 GiB.
    Tests that immediately discarded that mirror gained no independent evidence
    from the allocation and needlessly stressed the CUDA allocator/driver.
    """

    layout, dynamics, _ = pepo_modules()
    state = layout.build_codestate_pepo(cell["sched"], m, device="cuda")
    for token, site in _token_program(seed, n_ops=n_ops, leak_pump=leak_pump):
        dynamics.apply_token_stream(state, {site: (token,)}, cell["leak_t"])
    return state


def pick_stabilizers(schedule):
    """Return one weight-four X-containing and one weight-two stabilizer."""
    weight_four = next(
        dict(stabilizer.paulis)
        for stabilizer in schedule.stabilizers
        if len(stabilizer.paulis) == 4
        and any(str(pauli).upper() == "X" for pauli in stabilizer.paulis.values())
    )
    weight_two = next(
        dict(stabilizer.paulis)
        for stabilizer in schedule.stabilizers
        if len(stabilizer.paulis) == 2
    )
    return weight_four, weight_two


def referee_nonselective_round(engine, stabilizers: list, b: float, arm: str) -> None:
    """Apply the exact branch sum in the same declared stabilizer order."""
    for paulis in stabilizers:
        base = engine.rho.clone()
        engine.project_stabilizer(paulis, 0, b, arm)
        branch_zero = engine.rho
        engine.rho = base
        engine.project_stabilizer(paulis, 1, b, arm)
        branch_zero.add_(engine.rho)
        engine.rho = branch_zero


def max_bond_dim(state) -> int:
    """Return the largest PEPO virtual bond shared by two tensors."""
    largest = 1
    for index, tensor_ids in state.tn.ind_map.items():
        if len(tensor_ids) == 2:
            largest = max(largest, int(state.tn.ind_size(index)))
    return largest
