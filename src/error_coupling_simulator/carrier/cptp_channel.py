from __future__ import annotations

"""Differentiable, CPTP-by-construction quantum-channel parameterization.

This module supplies high-precision non-Clifford / non-Pauli channel algebra for
the simulator and its certification checks. It is intentionally exact and
small-scale, prioritizing channel fidelity over carrier scale.

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
This module parameterizes and applies a specified CPTP channel. It does not fit
a channel from emitted records, establish identifiability, or perform model
selection. Those are downstream inference tasks outside the simulator product.
The Stinespring form here is already non-Pauli/non-Clifford capable; it is not a
claim that every physical process has been represented or hardware-validated.

This module intentionally uses ``complex128`` (double precision) for
high-fidelity channel calculations, a deliberate departure from the GPU-float32
default justified by the precision-first goal at small scale. ``NUMERICAL_ZERO`` floors
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
    """Differentiable CPTP channel: Hermitian generator -> isometry -> Kraus."""

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
