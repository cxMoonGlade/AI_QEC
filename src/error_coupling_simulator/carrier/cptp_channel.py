from __future__ import annotations

"""Differentiable, CPTP-by-construction quantum-channel learning kernel.

This is the high-precision non-Clifford / non-Pauli core for the learner-side
CPTP upgrade (see project memory ``learner-cptp-upgrade``). It is intentionally
exact and small-scale (1-2 qubit channels now; 6-10 qubit circuits in the
follow-up forward model), prioritizing fidelity over scale.

Design
------
A channel is parameterized through a **Stinespring dilation**: a Hermitian
generator ``H`` -> unitary ``U = exp(iH)`` (``torch.matrix_exp``) -> isometry
``V = U[:, :d]`` (so ``V^dag V = I``) -> Kraus operators ``K_e`` read off the
blocks of ``V``. Because ``V`` is an isometry, ``sum_e K_e^dag K_e = I`` (trace
preserving) and the action ``rho -> sum_e K_e rho K_e^dag`` is completely
positive. The map is therefore **CPTP by construction**, so unconstrained
gradient descent on the generator never leaves the CPTP manifold. The Kraus
operators are arbitrary complex matrices, so the channel is non-Pauli and
non-Clifford capable (it represents coherent rotations, amplitude/phase
damping, leakage surrogates, etc., not just stochastic Pauli noise).

Claim boundary
--------------
This module *learns a CPTP channel*. Whether the channel is *recoverable* from
a given observation surface is a separate identifiability question: the channel
is fixed only up to the observational alias class unless the probe/input set is
informationally complete. It does not (yet) learn an arbitrary GKSL generator;
the Hamiltonian + PSD-Kossakowski (GKSL) parameterization is a planned variant
for interpretability, but the Stinespring form here is already
non-Pauli/non-Clifford capable.

This module intentionally uses ``complex128`` (double precision) for
high-fidelity recovery, a deliberate departure from the GPU-float32 default
justified by the precision-first goal at small scale. ``NUMERICAL_ZERO`` floors
still guard divisions.
"""

from dataclasses import dataclass

import torch

from ..numerics import NUMERICAL_ZERO

CDTYPE = torch.complex128
RDTYPE = torch.float64


# --------------------------------------------------------------------------- #
# Density-matrix ops (differentiable torch mirror of primitives.density_sim)   #
# --------------------------------------------------------------------------- #
def hermitianize(rho: torch.Tensor) -> torch.Tensor:
    return 0.5 * (rho + rho.conj().transpose(-1, -2))


def apply_kraus(rho: torch.Tensor, kraus: torch.Tensor) -> torch.Tensor:
    """Exact Kraus action ``rho -> sum_e K_e rho K_e^dag`` (differentiable).

    ``kraus`` is a ``(r, d, d)`` stack; ``rho`` is ``(d, d)`` or a batch
    ``(S, d, d)``. The result is Hermitianized to absorb round-off.
    """
    if kraus.device != rho.device:
        kraus = kraus.to(rho.device)
    kd = kraus.conj().transpose(-1, -2)
    if rho.dim() == 2:
        out = torch.einsum("eij,jk,ekl->il", kraus, rho, kd)
    else:
        out = torch.einsum("eij,sjk,ekl->sil", kraus, rho, kd)
    return hermitianize(out)


def measurement_probabilities_z(rho: torch.Tensor) -> torch.Tensor:
    diag = torch.diagonal(rho, dim1=-2, dim2=-1).real
    diag = torch.clamp(diag, min=NUMERICAL_ZERO)
    return diag / diag.sum(dim=-1, keepdim=True)


def tp_residual(kraus: torch.Tensor) -> torch.Tensor:
    """``|| sum_e K_e^dag K_e - I ||_F`` -- zero for a trace-preserving map."""
    d = kraus.shape[-1]
    completeness = torch.einsum("eij,eik->jk", kraus.conj(), kraus)
    identity = torch.eye(d, dtype=CDTYPE, device=kraus.device)
    return torch.linalg.matrix_norm(completeness - identity)


def choi_matrix(kraus: torch.Tensor) -> torch.Tensor:
    """Gauge-invariant Choi matrix ``J = sum_e vec(K_e) vec(K_e)^dag``.

    Invariant under Kraus-gauge (unitary mixing of operators), so the Frobenius
    distance between two Choi matrices is a valid channel-equality metric.
    """
    r, d, _ = kraus.shape
    vec = kraus.reshape(r, d * d)
    return torch.einsum("ea,eb->ab", vec, vec.conj())


# --------------------------------------------------------------------------- #
# CPTP-by-construction Stinespring parameterization                            #
# --------------------------------------------------------------------------- #
@dataclass
class StinespringChannel:
    """Learnable CPTP channel: Hermitian generator -> isometry -> Kraus."""

    dim: int
    num_kraus: int
    real: torch.Tensor  # (n, n) real generator part, requires_grad
    imag: torch.Tensor  # (n, n) imag generator part, requires_grad

    @classmethod
    def random(cls, dim: int, num_kraus: int, *, seed: int = 0, scale: float = 0.1,
               device: str | torch.device = "cpu") -> "StinespringChannel":
        gen = torch.Generator(device="cpu").manual_seed(int(seed))
        n = dim * num_kraus
        real = (scale * torch.randn(n, n, generator=gen, dtype=RDTYPE)).to(device).requires_grad_(True)
        imag = (scale * torch.randn(n, n, generator=gen, dtype=RDTYPE)).to(device).requires_grad_(True)
        return cls(dim=dim, num_kraus=num_kraus, real=real, imag=imag)

    def parameters(self) -> list[torch.Tensor]:
        return [self.real, self.imag]

    def kraus(self) -> torch.Tensor:
        m = self.real.to(CDTYPE) + 1j * self.imag.to(CDTYPE)
        hermitian = m + m.conj().transpose(-1, -2)
        unitary = torch.matrix_exp(1j * hermitian)
        isometry = unitary[:, : self.dim]  # (n, d), columns orthonormal -> V^dag V = I
        return isometry.reshape(self.num_kraus, self.dim, self.dim)


# --------------------------------------------------------------------------- #
# Informationally-complete probe inputs and recovery loop                      #
# --------------------------------------------------------------------------- #
def _ic_single_qubit_states(device: str | torch.device = "cpu") -> torch.Tensor:
    """The IC set {|0>, |1>, |+>, |+i>} as density matrices, spanning Herm(2)."""
    ket0 = torch.tensor([1.0, 0.0], dtype=CDTYPE, device=device)
    ket1 = torch.tensor([0.0, 1.0], dtype=CDTYPE, device=device)
    plus = torch.tensor([1.0, 1.0], dtype=CDTYPE, device=device) / (2 ** 0.5)
    plus_i = torch.tensor([1.0, 1.0j], dtype=CDTYPE, device=device) / (2 ** 0.5)
    return torch.stack([torch.outer(k, k.conj()) for k in (ket0, ket1, plus, plus_i)])


def informationally_complete_inputs(dim: int, device: str | torch.device = "cpu") -> torch.Tensor:
    """IC input density matrices for a ``dim``-dimensional system.

    Single-qubit IC states tensored across ``log2(dim)`` qubits stay IC.
    """
    num_qubits = int(round(float(torch.log2(torch.tensor(float(dim))))))
    if 2 ** num_qubits != dim:
        raise ValueError("dim must be a power of two")
    states = _ic_single_qubit_states(device=device)
    acc = states
    for _ in range(num_qubits - 1):
        acc = torch.stack([torch.kron(a, b) for a in acc for b in states])
    return acc


def recover_channel(
    target_kraus: torch.Tensor,
    *,
    num_kraus: int | None = None,
    steps: int = 200,
    seed: int = 0,
    device: str | torch.device = "cpu",
) -> dict[str, object]:
    """Fit a CPTP-by-construction channel to ``target_kraus`` via its action on
    an informationally-complete input set, using LBFGS in double precision.

    Returns the recovered channel plus action loss, Choi distance, and TP
    residual diagnostics. Zero action loss on IC inputs implies the recovered
    channel equals the target (up to nothing -- the action determines the map).
    """
    target_kraus = target_kraus.to(CDTYPE).to(device)
    dim = target_kraus.shape[-1]
    num_kraus = int(num_kraus or dim * dim)  # full Kraus rank can represent any CPTP map

    inputs = informationally_complete_inputs(dim, device=device)
    target_outputs = apply_kraus(inputs, target_kraus)

    channel = StinespringChannel.random(dim, num_kraus, seed=seed, device=device)
    opt = torch.optim.LBFGS(
        channel.parameters(), lr=1.0, max_iter=steps, line_search_fn="strong_wolfe",
        tolerance_grad=1e-18, tolerance_change=1e-20, history_size=50,
    )

    def closure() -> torch.Tensor:
        opt.zero_grad()
        outs = apply_kraus(inputs, channel.kraus())
        loss = ((outs - target_outputs).abs() ** 2).sum()
        loss.backward()
        return loss

    opt.step(closure)

    with torch.no_grad():
        recovered = channel.kraus()
        outs = apply_kraus(inputs, recovered)
        action_loss = float(((outs - target_outputs).abs() ** 2).sum())
        choi_distance = float(torch.linalg.matrix_norm(choi_matrix(recovered) - choi_matrix(target_kraus)))
        residual = float(tp_residual(recovered))
    return {
        "channel": channel,
        "recovered_kraus": recovered,
        "action_loss": action_loss,
        "choi_distance": choi_distance,
        "tp_residual": residual,
    }


# --------------------------------------------------------------------------- #
# Single-qubit Pauli-transfer matrix (coherence / non-Pauli diagnostic)        #
# --------------------------------------------------------------------------- #
def single_qubit_paulis(device: str | torch.device = "cpu") -> torch.Tensor:
    i = torch.eye(2, dtype=CDTYPE, device=device)
    x = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE, device=device)
    y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE, device=device)
    z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE, device=device)
    return torch.stack([i, x, y, z])


def pauli_transfer_matrix(kraus: torch.Tensor) -> torch.Tensor:
    """Single-qubit PTM ``R_ab = (1/2) Tr[P_a Phi(P_b)]``.

    A stochastic Pauli channel has a diagonal PTM; nonzero off-diagonal entries
    certify coherent / non-Pauli action.
    """
    paulis = single_qubit_paulis(device=kraus.device)
    transformed = apply_kraus(paulis, kraus)  # Phi(P_b), b indexes the batch
    r = 0.5 * torch.einsum("aij,bji->ab", paulis, transformed).real
    return r
