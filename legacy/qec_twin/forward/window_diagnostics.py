from __future__ import annotations

"""Small-support channel diagnostics for the window-channel object (step-2).

Derived **lenses** read off a Kraus/Stinespring channel (the model's source of
truth, ``complex128``) for ``n``-qubit supports small enough to materialise the
density matrix (1q ``d=2``, 2q ``d=4``; the dictionary supports 3q ready-but-off,
``d=8``). Spec: ``docs/cf_wr/window_channel_spec.md`` §4 (representation &
invariants) + §10 (the frozen interface contract these signatures match exactly).

What lives here
---------------
- ``pauli_basis(n)`` — the normalised ``n``-qubit Pauli operator basis.
- ``ptm(kraus, n)`` — the ``n``-qubit Pauli-transfer matrix, the generalisation
  of ``cptp_channel.pauli_transfer_matrix`` (single-qubit only) to small ``n``.
- ``coherence_budget(kraus, n)`` — the PTM off-diagonal Frobenius mass: **exactly
  what a Pauli twirl / DEM export discards** (§4 — band-tracked, a reportable
  result; never diagonal-truncate the PTM *in the model*, only the downstream
  export).
- ``choi_min_eig(kraus)`` — the CP certificate (min eigenvalue of the reused
  ``choi_matrix``; CP iff ``>= -NUMERICAL_ZERO``).
- ``partial_trace(rho, keep, n)`` — reduced density matrix for the ``rho_BC`` seam
  anchor (step-4); keeps ``keep`` (order preserved), traces the rest.

Conventions
-----------
- **Reuse, not reinvention.** ``choi_min_eig`` is computed from the gauge-invariant
  ``choi_matrix`` of ``cptp_channel.py``; ``ptm`` evolves the basis with
  ``apply_kraus`` from the same module (device-aware, differentiable). The PTM
  convention matches the single-qubit ``pauli_transfer_matrix`` exactly:
  for a normalised basis ``P_hat_a = P_a / sqrt(2**n)`` (so ``Tr[P_hat_a P_hat_b]
  = delta_ab``), ``R_ab = Tr[P_hat_a Phi(P_hat_b)]`` is identically the §10 formula
  ``R_ab = (1/2**n) Tr[P_a Phi(P_b)]`` (the two ``1/sqrt(2**n)`` factors compose to
  ``1/2**n``), so the identity channel maps to the identity PTM.
- **complex128 / device-aware.** A ``device`` kwarg threads through the basis and
  PTM builders (the contract requires it everywhere; the basis/PTM follow the
  Kraus device when one is not passed). The PTM and budget are real-valued.
- **Floors via ``NUMERICAL_ZERO`` only** (the CP tolerance); structural zeros
  (Pauli entries, the trace-out index arithmetic) are never floored.
- **Coherence is the point.** ``coherence_budget`` measures coherent / non-Pauli
  mass; it never collapses a coherent mechanism to a Pauli rate.
"""

import torch

from qec_twin.numerics import NUMERICAL_ZERO

from qec_twin.forward.cptp_channel import (
    CDTYPE,
    RDTYPE,
    apply_kraus,
    choi_matrix,
)


# --------------------------------------------------------------------------- #
# n-qubit Pauli basis                                                         #
# --------------------------------------------------------------------------- #
def _single_qubit_paulis(*, device=None) -> torch.Tensor:
    """The four single-qubit Paulis ``{I, X, Y, Z}`` (unnormalised), ``(4, 2, 2)``."""
    i = torch.eye(2, dtype=CDTYPE, device=device)
    x = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE, device=device)
    y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE, device=device)
    z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE, device=device)
    return torch.stack([i, x, y, z])


def pauli_basis(n: int, *, device=None) -> torch.Tensor:
    """Normalised ``n``-qubit Pauli operator basis, shape ``(4**n, 2**n, 2**n)``.

    Element ``a`` is ``P_hat_a = P_a / sqrt(2**n)`` for the ``a``-th ``n``-fold
    Kronecker product of ``{I, X, Y, Z}`` (lexicographic order, the first factor
    varying slowest — matching ``ptm.pauli_basis`` / ``torch.kron`` ordering). The
    normalisation makes the basis orthonormal under the Hilbert-Schmidt inner
    product, ``Tr[P_hat_a P_hat_b] = delta_ab``, so the PTM of the identity channel
    is the identity (see ``ptm``).
    """
    n = int(n)
    if n <= 0:
        raise ValueError("n must be a positive integer")
    one = _single_qubit_paulis(device=device)  # (4, 2, 2), unnormalised
    basis = one
    for _ in range(n - 1):
        # Kronecker every accumulated operator with each single-qubit Pauli,
        # outer index varying slowest -> lexicographic (III, IIX, ..., ZZZ).
        a = basis.shape[0]
        d = basis.shape[-1]
        left = basis.reshape(a, 1, d, 1, d, 1)
        right = one.reshape(1, 4, 1, 2, 1, 2)
        basis = (left * right).reshape(a * 4, d * 2, d * 2)
    dim = 2 ** n
    norm = float(dim) ** 0.5
    return basis / norm


# --------------------------------------------------------------------------- #
# n-qubit Pauli-transfer matrix and coherence budget                          #
# --------------------------------------------------------------------------- #
def ptm(kraus: torch.Tensor, n: int, *, device=None) -> torch.Tensor:
    """``n``-qubit Pauli-transfer matrix, shape ``(4**n, 4**n)``, real.

    ``R_ab = (1/2**n) Tr[P_a Phi(P_b)]`` (§10), computed in the normalised basis as
    ``R_ab = Tr[P_hat_a Phi(P_hat_b)]`` (identical — see the module docstring). A
    stochastic Pauli channel has a diagonal PTM; nonzero off-diagonal entries
    certify coherent / non-Pauli action (the quantity ``coherence_budget`` sums).

    ``kraus`` is a ``(r, 2**n, 2**n)`` stack; differentiable through ``apply_kraus``.
    """
    n = int(n)
    if n <= 0:
        raise ValueError("n must be a positive integer")
    dim = 2 ** n
    if kraus.dim() != 3 or kraus.shape[-1] != dim or kraus.shape[-2] != dim:
        raise ValueError(
            f"kraus must be a (r, {dim}, {dim}) stack for n={n}; got {tuple(kraus.shape)}"
        )
    basis_device = device if device is not None else kraus.device
    basis = pauli_basis(n, device=basis_device).to(CDTYPE)  # (4**n, dim, dim)
    if kraus.device != basis.device:
        kraus = kraus.to(basis.device)
    transformed = apply_kraus(basis, kraus.to(CDTYPE))  # Phi(P_hat_b), b is the batch
    # R_ab = Tr[P_hat_a @ Phi(P_hat_b)] = sum_ij (P_hat_a)_ij (Phi(P_hat_b))_ji
    r = torch.einsum("aij,bji->ab", basis, transformed).real
    return r.to(RDTYPE)


def coherence_budget(kraus: torch.Tensor, n: int) -> float:
    """Frobenius mass of the PTM off-diagonal — the coherence the DEM discards.

    ``sqrt(sum_{a != b} R_ab**2)`` for the ``n``-qubit PTM. Zero for a stochastic
    Pauli channel (diagonal PTM); strictly positive for coherent / non-Pauli
    mechanisms (the §4 band-tracked, reportable result). This never truncates the
    model — it only *measures* what a Pauli/DEM export would throw away.
    """
    matrix = ptm(kraus, n)
    off_diagonal = matrix - torch.diag(torch.diagonal(matrix))
    return float(torch.linalg.matrix_norm(off_diagonal))


# --------------------------------------------------------------------------- #
# Completely-positive certificate                                             #
# --------------------------------------------------------------------------- #
def choi_min_eig(kraus: torch.Tensor) -> float:
    """Minimum eigenvalue of ``choi_matrix(kraus)`` — the CP certificate.

    The channel is completely positive iff its Choi matrix is PSD, i.e. iff this
    minimum eigenvalue is ``>= -NUMERICAL_ZERO``. Reuses the gauge-invariant
    ``choi_matrix`` from ``cptp_channel.py`` (Hermitian by construction; eigenvalues
    via ``eigvalsh`` are real). A CPTP-by-construction Kraus stack returns ``>= 0``
    up to round-off; a non-CP map returns a meaningfully negative value.
    """
    choi = choi_matrix(kraus.to(CDTYPE))
    choi = 0.5 * (choi + choi.conj().transpose(-1, -2))  # symmetrise round-off
    eigenvalues = torch.linalg.eigvalsh(choi)
    return float(eigenvalues.min())


# --------------------------------------------------------------------------- #
# Partial trace (rho_BC seam anchor)                                          #
# --------------------------------------------------------------------------- #
def partial_trace(rho: torch.Tensor, keep: list[int], n: int) -> torch.Tensor:
    """Reduced density matrix on the kept qubits, tracing out the rest.

    ``rho`` is an ``n``-qubit density matrix ``(2**n, 2**n)``; ``keep`` lists the
    qubit indices to retain in the **stated order** (qubit ``0`` is the most
    significant tensor factor, matching the ``pauli_basis`` / ``torch.kron``
    convention). Returns ``(2**k, 2**k)`` with ``k = len(keep)``, the marginal used
    for the ``rho_BC`` overlap anchor (step-4). Differentiable; preserves dtype and
    device.

    The implementation reshapes ``rho`` into the ``2n``-leg tensor
    ``[row_0..row_{n-1}, col_0..col_{n-1}]`` and contracts via a single ``einsum``:
    a traced qubit shares one label across its row and column legs (partial ``Tr``
    over that factor); kept qubits keep distinct row/column labels and appear in the
    output in the requested ``keep`` order, then flatten back to a matrix. Computing
    every leg label once from the original layout avoids fragile running-index
    renumbering across successive contractions.
    """
    n = int(n)
    if n <= 0:
        raise ValueError("n must be a positive integer")
    dim = 2 ** n
    if rho.shape[-1] != dim or rho.shape[-2] != dim:
        raise ValueError(
            f"rho must be a ({dim}, {dim}) density matrix for n={n}; got {tuple(rho.shape)}"
        )
    keep = [int(q) for q in keep]
    if any(q < 0 or q >= n for q in keep):
        raise ValueError(f"keep indices must lie in [0, {n}); got {keep}")
    if len(set(keep)) != len(keep):
        raise ValueError(f"keep indices must be distinct; got {keep}")

    keep_set = set(keep)
    # Per-qubit row/col labels over the original 2n-leg layout. A traced qubit
    # reuses its row label on the column leg (-> contracted = partial trace);
    # a kept qubit gets two fresh labels (preserved on the output).
    row_labels: list[int] = []
    col_labels: list[int] = []
    next_label = 0
    for q in range(n):
        row = next_label
        next_label += 1
        row_labels.append(row)
        if q in keep_set:
            col = next_label
            next_label += 1
        else:
            col = row  # share -> contract this qubit's row/col legs
        col_labels.append(col)

    in_labels = row_labels + col_labels
    out_labels = [row_labels[q] for q in keep] + [col_labels[q] for q in keep]

    tensor = rho.reshape([2] * (2 * n))
    reduced = torch.einsum(tensor, in_labels, out_labels)
    k = len(keep)
    return reduced.reshape(2 ** k, 2 ** k)
