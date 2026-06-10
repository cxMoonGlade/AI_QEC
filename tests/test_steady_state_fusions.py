"""Bit-exact pins for the M3 steady-state fusions (registered pin P1h).

Two provably bit-exact rewrites of the launch-bound burn-in loop -- launch
scheduling only, never math:

(1) ``dephase_parity_sweep`` collapses the per-round sequential
    ``dephase_parity(rho, j, j+1, n)`` j-loop into ONE cached 0/1-mask
    multiply. Identity: each dephase is an elementwise multiply by
    ``M_j[x, y] = [par_j(x) == par_j(y)]``; the sweep is ``rho * prod_j M_j``.
(2) ``simulate_steady_block(check_residual=False, burn_in=B)`` deletes the
    fixed-point diagnostic / doubling / host sync; it is the SAME computation
    as the default path whenever the default converges in exactly ``B`` rounds.

Equality is asserted with IEEE ``==`` semantics (the registered contract):
killed cross-sector entries are an exact complex zero on BOTH paths, and only
the zero's SIGN bit (``+-0.0``) may differ between them; ``-0.0 == +0.0``, and
every downstream add/multiply/abs/sum treats the two value-identically, so fit
trajectories are unchanged. CPU always; the same pins re-run on CUDA when
available. No dataset needed. Style follows tests/test_kernels_fused_kraus.py.
"""
from __future__ import annotations

import pytest
import torch

from qec_twin.forward.cptp_channel import CDTYPE, RDTYPE
from qec_twin.forward.exact.circuit_sim import dephase_parity, dephase_parity_sweep
from qec_twin.forward.exact.steady_state import (
    DEFAULT_FP_TOL,
    fixed_point_residual,
    simulate_steady_block,
)

DEVICES = ["cpu"] + (["cuda"] if torch.cuda.is_available() else [])


@pytest.fixture(autouse=True)
def _deterministic_algorithms():
    """Mirror the fleet's execution mode (m3_parallel._enable_determinism).

    Without this, CUDA `scatter_add` in the enumeration is atomicAdd-ordered:
    two runs of the SAME computation differ in low-order bits, so the bit-exact
    `==` pins below are only well-posed under deterministic algorithms — which
    is also exactly how every registered fit executes (P1h)."""
    import os

    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    prev = torch.are_deterministic_algorithms_enabled()
    torch.use_deterministic_algorithms(True)
    try:
        yield
    finally:
        torch.use_deterministic_algorithms(prev)


def _sequential_sweep(rho: torch.Tensor, n: int) -> torch.Tensor:
    """The eager reference: the exact j-loop dephase_parity_sweep replaces."""
    for j in range(n - 1):
        rho = dephase_parity(rho, j, j + 1, n)
    return rho


def _rand_hermitian(b: int | None, n: int, *, device, seed: int) -> torch.Tensor:
    """Random Hermitian batch with mixed-sign entries (exercises the +-0 cases)."""
    g = torch.Generator(device="cpu").manual_seed(seed)
    shape = (2**n, 2**n) if b is None else (b, 2**n, 2**n)
    a = torch.randn(*shape, dtype=CDTYPE, generator=g)
    return (a + a.conj().transpose(-1, -2)).to(device)


# ------------------------------------------------------------------ pin (1): sweep
@pytest.mark.parametrize("device", DEVICES)
@pytest.mark.parametrize("batch,n", [(1, 5), (7, 5), (4, 3), (None, 4)])
def test_sweep_forward_bit_exact(device, batch, n) -> None:
    # EXACT equality under IEEE `==`: kept entries are reproduced exactly
    # (adding/subtracting a signed zero to a finite component is exact); killed
    # entries are an exact complex zero from both paths, differing at most in
    # the sign bit of +-0.0 -- which `==` cannot see and no downstream
    # sum/product can convert into a value difference, so trajectories are
    # unchanged (P1h).
    rho = _rand_hermitian(batch, n, device=device, seed=11 + n)
    ref = _sequential_sweep(rho, n)
    fused = dephase_parity_sweep(rho, n)
    assert fused.shape == ref.shape and fused.dtype == ref.dtype
    assert (fused == ref).all()


@pytest.mark.parametrize("device", DEVICES)
@pytest.mark.parametrize("batch,n", [(1, 5), (7, 5), (4, 3)])
def test_sweep_gradients_bit_exact(device, batch, n) -> None:
    # Backward of a constant 0/1-mask multiply is the same mask multiply (no
    # custom autograd), so gradients obey the identical +-0.0-only argument.
    rho0 = _rand_hermitian(batch, n, device=device, seed=29 + n)

    def grad_of(fn):
        rho = rho0.clone().requires_grad_(True)
        out = fn(rho, n)
        loss = (out.real**2 + out.imag**2).sum()
        loss.backward()
        return rho.grad.clone()

    g_ref = grad_of(_sequential_sweep)
    g_fused = grad_of(dephase_parity_sweep)
    assert (g_fused == g_ref).all()


def test_sweep_trivial_register_is_identity() -> None:
    # n < 2: the sequential loop body never runs; the fused sweep must return
    # rho untouched (bit-identical, same object semantics not required).
    rho = _rand_hermitian(3, 1, device="cpu", seed=5)
    assert (dephase_parity_sweep(rho, 1) == rho).all()


# ---------------------------------------------------- pin (2): check_residual=False
# Time-shared strictly diagonal/antidiagonal flip field at device-scale rates
# ~1e-2 (the m3_report.flip_channel_kraus / in_class_field idiom, rebuilt
# locally so this test needs no hardware module). Zero cat-term leak, so the
# diagonal stationary init is already the fixed point and the default path
# converges in exactly the base 40 rounds -- the regime where the two paths
# are the same op sequence.
_FLIP_P01 = [0.012, 0.010, 0.014, 0.011, 0.013]
_FLIP_P10 = [0.011, 0.013, 0.010, 0.012, 0.012]


def _flip_kraus(p01, p10) -> torch.Tensor:
    """Flip pair ``{(p01, p10)}``: K0 diagonal, K1 antidiagonal; differentiable."""
    p01 = torch.as_tensor(p01, dtype=RDTYPE)
    p10 = torch.as_tensor(p10, dtype=RDTYPE).to(p01.device)
    zero = torch.zeros((), dtype=CDTYPE, device=p01.device)
    k0 = torch.stack(
        [
            torch.stack([torch.sqrt(1 - p01).to(CDTYPE), zero]),
            torch.stack([zero, torch.sqrt(1 - p10).to(CDTYPE)]),
        ]
    )
    k1 = torch.stack(
        [
            torch.stack([zero, torch.sqrt(p10).to(CDTYPE)]),
            torch.stack([torch.sqrt(p01).to(CDTYPE), zero]),
        ]
    )
    return torch.stack([k0, k1])


def _flip_field(device):
    stacks = [
        _flip_kraus(p01, p10).to(device) for p01, p10 in zip(_FLIP_P01, _FLIP_P10)
    ]
    return lambda t, i: stacks[i]


@pytest.mark.parametrize("device", DEVICES)
def test_check_residual_false_matches_default(device) -> None:
    field = _flip_field(device)
    # Premise guard: the equality claim holds when the residual-checked path
    # converges in EXACTLY the base 40 rounds (no doubling).
    residual, rounds_used = fixed_point_residual(field, device=device)
    assert residual <= DEFAULT_FP_TOL
    assert rounds_used == 40

    law_checked = simulate_steady_block(field, device=device)  # default: True
    law_free = simulate_steady_block(field, device=device, check_residual=False, burn_in=40)
    # Same init, same 40 rounds, same enumeration: the False path only deletes
    # the no_grad diagnostic (which inspects a detached copy), so the laws are
    # the same computation -- exactly equal, not merely close.
    assert (law_free == law_checked).all()
    assert torch.equal(law_free, law_checked)


@pytest.mark.parametrize("device", DEVICES)
def test_check_residual_false_gradients_match_default(device) -> None:
    # P1h trajectory clause: with identical leaves the two paths produce
    # identical gradients, so an LBFGS fit stepping on either path walks the
    # exact same trajectory.
    def law_and_grad(check_residual: bool):
        p01 = torch.tensor(_FLIP_P01, dtype=RDTYPE, device=device, requires_grad=True)
        stacks = [
            _flip_kraus(p01[i], torch.as_tensor(_FLIP_P10[i], dtype=RDTYPE, device=device))
            for i in range(5)
        ]
        field = lambda t, i: stacks[i]  # noqa: E731
        law = simulate_steady_block(
            field, device=device, check_residual=check_residual, burn_in=40
        )
        (law**2).sum().backward()
        return law.detach(), p01.grad.clone()

    law_checked, grad_checked = law_and_grad(True)
    law_free, grad_free = law_and_grad(False)
    assert (law_free == law_checked).all()
    assert (grad_free == grad_checked).all()
