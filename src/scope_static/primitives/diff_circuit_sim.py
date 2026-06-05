from __future__ import annotations

"""Differentiable n-qubit density-matrix circuit forward model (small scale).

L2 minimal core for the QEC digital twin (see project memory
``qec-digital-twin-goal``). It extends the channel kernel
(:mod:`scope_static.primitives.diff_cptp_channel`) to a multi-qubit register so
local non-Clifford gates and local CPTP channels can be composed through a
circuit and read out as exact, differentiable measurement / detection-event
probabilities.

Scope and method
----------------
Exact density-matrix simulation at small ``n`` (<= ~10 qubits), prioritizing
fidelity over scale. Local operators are embedded into the full register by
Kronecker product with identity plus an axis permutation -- simple and exact at
this scale. The index-contraction / DEM-with-coherent-corrections optimization
for device scale (72-105 qubits) is the *next* L2 sub-step and is deliberately
not done here.

Qubit ordering: qubit 0 is the most-significant tensor factor, so a basis index
``i`` encodes bit ``(i >> (n - 1 - q)) & 1`` for qubit ``q`` (matches
``diff_cptp_channel.measurement_probabilities_z``). Everything is ``complex128``
and differentiable (gates and channels may depend on leaf parameters), so
``d P(detector) / d theta`` -- the gradient that powers the L4 priority-list and
bottleneck knobs -- is available by autograd.
"""

import torch

from scope_static.primitives.diff_cptp_channel import (
    CDTYPE,
    RDTYPE,
    apply_kraus,
    hermitianize,
    measurement_probabilities_z,
)


# --------------------------------------------------------------------------- #
# Register state and local-operator embedding                                  #
# --------------------------------------------------------------------------- #
def zero_state(n: int, *, device: str | torch.device = "cpu") -> torch.Tensor:
    dim = 2 ** int(n)
    rho = torch.zeros((dim, dim), dtype=CDTYPE, device=device)
    rho[0, 0] = 1.0
    return rho


def embed_operator(op: torch.Tensor, targets, n: int) -> torch.Tensor:
    """Embed a ``k``-qubit operator acting on ``targets`` into the n-qubit
    register (Kronecker with identity, then permute qubit axes into place).

    Differentiable in ``op`` (so parameterized gates/Kraus pass gradients).
    """
    targets = [int(q) for q in targets]
    k = len(targets)
    rest = int(n) - k
    if rest > 0:
        full = torch.kron(op, torch.eye(2 ** rest, dtype=CDTYPE, device=op.device))
    else:
        full = op
    # `full` currently treats qubit order as: targets first, then the rest.
    current = targets + [q for q in range(n) if q not in targets]
    perm_row = [current.index(q) for q in range(n)]
    perm = perm_row + [n + a for a in perm_row]
    full = full.reshape([2] * (2 * n)).permute(*perm).contiguous().reshape(2 ** n, 2 ** n)
    return full


def apply_unitary(rho: torch.Tensor, unitary: torch.Tensor, targets, n: int) -> torch.Tensor:
    u = embed_operator(unitary, targets, n)
    return hermitianize(u @ rho @ u.conj().transpose(-1, -2))


def apply_channel_local(rho: torch.Tensor, kraus: torch.Tensor, targets, n: int) -> torch.Tensor:
    """Apply a local CPTP channel (stack of ``k``-qubit Kraus ops) on ``targets``."""
    embedded = torch.stack([embed_operator(k, targets, n) for k in kraus])
    return apply_kraus(rho, embedded)


# --------------------------------------------------------------------------- #
# Measurement read-out (exact, differentiable)                                 #
# --------------------------------------------------------------------------- #
def qubit_marginal_one(rho: torch.Tensor, qubit: int, n: int) -> torch.Tensor:
    """``P(qubit == 1)`` from the computational-basis diagonal of ``rho``."""
    probs = measurement_probabilities_z(rho)
    idx = torch.arange(2 ** int(n), device=rho.device)
    bit = (idx >> (int(n) - 1 - int(qubit))) & 1
    return probs[bit == 1].sum()


def parity_marginal_one(rho: torch.Tensor, qubits, n: int) -> torch.Tensor:
    """``P(XOR of the given qubits == 1)`` -- a detection-event probability."""
    probs = measurement_probabilities_z(rho)
    idx = torch.arange(2 ** int(n), device=rho.device)
    parity = torch.zeros_like(idx)
    for q in qubits:
        parity = parity ^ ((idx >> (int(n) - 1 - int(q))) & 1)
    return probs[parity == 1].sum()


# --------------------------------------------------------------------------- #
# Mid-circuit measurement: exact trajectory enumeration                        #
# --------------------------------------------------------------------------- #
def project_qubit(rho: torch.Tensor, qubit: int, outcome: int, n: int) -> torch.Tensor:
    """Unnormalized post-measurement state ``P_b rho P_b`` for ``qubit == b``.

    ``P_b`` is the computational-basis projector, so the result is ``rho`` with
    every row/column whose ``qubit`` bit != ``outcome`` zeroed. Batch-aware over
    any leading dimensions. The map is intentionally *unnormalized*: the trace of
    the result is ``P(outcome)`` for that branch, so a branch's running trace
    stays equal to the joint probability of its outcomes so far.
    """
    dim = 2 ** int(n)
    idx = torch.arange(dim, device=rho.device)
    bit = (idx >> (int(n) - 1 - int(qubit))) & 1
    keep = bit == int(outcome)
    mask = (keep[:, None] & keep[None, :]).to(rho.dtype)
    return rho * mask


def measure_qubit_enumerate(
    rho: torch.Tensor, outcomes: torch.Tensor, qubit: int, n: int, *, reset: bool
) -> tuple[torch.Tensor, torch.Tensor]:
    """Branch the enumerated trajectory set on measuring ``qubit`` in Z.

    ``rho`` is ``(B, dim, dim)`` (``B`` current branches, each unnormalized so its
    trace is the branch probability); ``outcomes`` is ``(B, K)`` of recorded bits.
    Returns ``(2B, dim, dim)`` and ``(2B, K + 1)``: the first ``B`` rows are the
    outcome-0 block, the next ``B`` the outcome-1 block. With ``reset=True`` the
    post-measurement qubit (exactly ``|1>`` on the outcome-1 block, disentangled
    by the projection) is returned to ``|0>`` so the ancilla can be reused next
    round -- the density-matrix analogue of a stim ``MR``.
    """
    rho0 = project_qubit(rho, qubit, 0, n)
    rho1 = project_qubit(rho, qubit, 1, n)
    if reset:
        rho1 = apply_unitary(rho1, pauli_x(), [qubit], n)
    rho_new = torch.cat([rho0, rho1], dim=0)
    b = outcomes.shape[0]
    col0 = torch.zeros((b, 1), dtype=outcomes.dtype, device=outcomes.device)
    col1 = torch.ones((b, 1), dtype=outcomes.dtype, device=outcomes.device)
    outcomes_new = torch.cat(
        [torch.cat([outcomes, col0], dim=1), torch.cat([outcomes, col1], dim=1)],
        dim=0,
    )
    return rho_new, outcomes_new


# --------------------------------------------------------------------------- #
# Small differentiable gate / channel builders (parameter-carrying)            #
# --------------------------------------------------------------------------- #
def rx(theta) -> torch.Tensor:
    t = torch.as_tensor(theta, dtype=RDTYPE)
    c = torch.cos(t / 2).to(CDTYPE)
    s = torch.sin(t / 2).to(CDTYPE)
    return torch.stack([torch.stack([c, -1j * s]), torch.stack([-1j * s, c])])


def ry(theta) -> torch.Tensor:
    t = torch.as_tensor(theta, dtype=RDTYPE)
    c = torch.cos(t / 2).to(CDTYPE)
    s = torch.sin(t / 2).to(CDTYPE)
    return torch.stack([torch.stack([c, -s]), torch.stack([s, c])])


def cx() -> torch.Tensor:
    return torch.tensor(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=CDTYPE
    )


def pauli_x() -> torch.Tensor:
    return torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)


def bit_flip(p) -> torch.Tensor:
    """Bit-flip channel ``{sqrt(1-p) I, sqrt(p) X}`` as a ``(2, 2, 2)`` Kraus stack.

    The stochastic-Pauli channel a stim ``X_ERROR(p)`` represents, in
    differentiable density-matrix form, so the exact forward model can be
    cross-checked against a stim sampler on the pure-Pauli slice.
    """
    pp = torch.as_tensor(p, dtype=RDTYPE)
    eye = torch.eye(2, dtype=CDTYPE)
    x = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    k0 = torch.sqrt(1 - pp).to(CDTYPE) * eye
    k1 = torch.sqrt(pp).to(CDTYPE) * x
    return torch.stack([k0, k1])


def amplitude_damping(gamma) -> torch.Tensor:
    g = torch.as_tensor(gamma, dtype=RDTYPE)
    zero = torch.zeros_like(g).to(CDTYPE)
    one = torch.ones_like(g).to(CDTYPE)
    k0 = torch.stack([torch.stack([one, zero]), torch.stack([zero, torch.sqrt(1 - g).to(CDTYPE)])])
    k1 = torch.stack([torch.stack([zero, torch.sqrt(g).to(CDTYPE)]), torch.stack([zero, zero])])
    return torch.stack([k0, k1])
