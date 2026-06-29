from __future__ import annotations

"""Differentiable n-qubit density-matrix circuit forward model (small scale).

L2 minimal core for the QEC digital twin (see project memory
``qec-digital-twin-goal``). It extends the channel kernel
(:mod:`qec_twin.forward.cptp_channel`) to a multi-qubit register so
local non-Clifford gates and local CPTP channels can be composed through a
circuit and read out as exact, differentiable measurement / detection-event
probabilities.

Overview and method
----------------
Exact density-matrix simulation at small ``n`` (<= ~10 qubits), prioritizing
fidelity over scale. Local operators are embedded into the full register by
Kronecker product with identity plus an axis permutation -- simple and exact at
this scale. The optimization for device scale (72-105 qubits) is the *next* step —
a scalable backend (``forward/scalable``; carrier deferred, ADR 0005) — and is
deliberately not done here.

Qubit ordering: qubit 0 is the most-significant tensor factor, so a basis index
``i`` encodes bit ``(i >> (n - 1 - q)) & 1`` for qubit ``q`` (matches
``diff_cptp_channel.measurement_probabilities_z``). Everything is ``complex128``
and differentiable (gates and channels may depend on leaf parameters), so
``d P(detector) / d theta`` -- the gradient that powers the L4 priority-list and
bottleneck knobs -- is available by autograd.
"""

import torch

from qec_twin.forward.cptp_channel import (
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
    # Layout normalization (mechanical fix, 2026-06-11): einsum-built operators
    # (e.g. the P1f X-conjugated Kraus on CUDA) can arrive as NON-CONTIGUOUS
    # views; torch.kron's internal .view() then raises. contiguous() copies
    # memory layout only — identical elements, no math change.
    op = op.contiguous()
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
    if unitary.device != rho.device:
        unitary = unitary.to(rho.device)
    if rho.is_cuda and _accel_available():
        from qec_twin.forward import accel

        return accel.apply_channel_local_fused(rho, unitary.unsqueeze(0), targets, n)
    u = embed_operator(unitary, targets, n)
    return hermitianize(u @ rho @ u.conj().transpose(-1, -2))


def apply_channel_local(rho: torch.Tensor, kraus: torch.Tensor, targets, n: int) -> torch.Tensor:
    """Apply a local CPTP channel (stack of ``k``-qubit Kraus ops) on ``targets``."""
    if kraus.device != rho.device:
        kraus = kraus.to(rho.device)
    if rho.is_cuda and len(tuple(targets)) <= 4 and _accel_available():
        from qec_twin.forward import accel

        return accel.apply_channel_local_fused(rho, kraus, targets, n)
    embedded = torch.stack([embed_operator(k, targets, n) for k in kraus])
    return apply_kraus(rho, embedded)


def _accel_available() -> bool:
    global _ACCEL_OK
    if _ACCEL_OK is None:
        from qec_twin.forward import accel

        _ACCEL_OK = accel.available()
    return _ACCEL_OK


_ACCEL_OK: bool | None = None


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
        rho1 = apply_unitary(rho1, pauli_x(rho1.device), [qubit], n)
    rho_new = torch.cat([rho0, rho1], dim=0)
    b = outcomes.shape[0]
    col0 = torch.zeros((b, 1), dtype=outcomes.dtype, device=outcomes.device)
    col1 = torch.ones((b, 1), dtype=outcomes.dtype, device=outcomes.device)
    outcomes_new = torch.cat(
        [torch.cat([outcomes, col0], dim=1), torch.cat([outcomes, col1], dim=1)],
        dim=0,
    )
    return rho_new, outcomes_new


def project_parity(rho: torch.Tensor, qubit_a: int, qubit_b: int, outcome: int, n: int) -> torch.Tensor:
    """Unnormalized projection onto the ``Z_a Z_b`` parity eigenspace ``== outcome``.

    Models a noiseless stabilizer measurement of the two-qubit Z-parity directly on
    the data register: ``Z_a Z_b`` has eigenvalue ``(-1)^(x_a ^ x_b)`` on basis state
    ``|x>``, so the projector keeps the rows/columns whose ``x_a ^ x_b == outcome``.
    Equivalent to the CX-ladder-into-ancilla-then-measure-and-reset sequence when
    the syndrome extraction is noiseless, but stays in the ``2**(data)`` register
    (no ancilla), which is what makes larger code distances tractable.
    """
    dim = 2 ** int(n)
    idx = torch.arange(dim, device=rho.device)
    bit_a = (idx >> (int(n) - 1 - int(qubit_a))) & 1
    bit_b = (idx >> (int(n) - 1 - int(qubit_b))) & 1
    keep = (bit_a ^ bit_b) == int(outcome)
    mask = (keep[:, None] & keep[None, :]).to(rho.dtype)
    return rho * mask


def dephase_parity(rho: torch.Tensor, qubit_a: int, qubit_b: int, n: int) -> torch.Tensor:
    """Non-selective ``Z_a Z_b`` parity measurement: ``P_0 rho P_0 + P_1 rho P_1``.

    The record-discarded (unconditional) state after a parity measurement -- the
    coherence between the two parity eigenspaces is destroyed, populations and
    within-sector coherences are untouched, and the trace is preserved. This is
    the burn-in primitive for steady-state extraction (R2-lite M3): iterating
    ``[channel layer; dephase_parity sweep]`` on a single unbranched ``rho``
    converges to the stationary state of the syndrome-extraction round map
    without enumerating measurement branches. Batch-aware over any leading
    dimensions, like :func:`project_parity`.
    """
    return (
        project_parity(rho, qubit_a, qubit_b, 0, n)
        + project_parity(rho, qubit_a, qubit_b, 1, n)
    )


_PARITY_SWEEP_MASKS: dict[tuple[int, torch.dtype, torch.device], torch.Tensor] = {}


def _parity_sweep_mask(n: int, dtype: torch.dtype, device: torch.device) -> torch.Tensor:
    """Cached fused-sweep 0/1 mask ``M`` (see :func:`dephase_parity_sweep`),
    per ``(n, dtype, device)`` -- the `_dev_const` pattern, keyed by size/dtype too."""
    key = (int(n), dtype, torch.device(device))
    cached = _PARITY_SWEEP_MASKS.get(key)
    if cached is None:
        nn = int(n)
        idx = torch.arange(2 ** nn, device=key[2])
        # bit q of basis index x is (x >> (n - 1 - q)) & 1 (qubit 0 = MSB; matches
        # project_parity); par_j(x) = bit_j(x) ^ bit_{j+1}(x) for j = 0..n-2.
        shifts = torch.arange(nn - 1, -1, -1, device=key[2])
        bits = (idx[:, None] >> shifts[None, :]) & 1
        pars = bits[:, :-1] ^ bits[:, 1:]
        keep = (pars[:, None, :] == pars[None, :, :]).all(-1)
        cached = keep.to(dtype)
        _PARITY_SWEEP_MASKS[key] = cached
    return cached


def dephase_parity_sweep(rho: torch.Tensor, n: int) -> torch.Tensor:
    """Fused adjacent-pair parity-dephase sweep: every ``dephase_parity(rho, j, j+1, n)``
    for ``j = 0..n-2`` collapsed into ONE cached elementwise multiply.

    Derivation (an exact identity, not an approximation). With the register's
    bit convention (qubit 0 = most significant: bit ``q`` of basis index ``x``
    is ``(x >> (n - 1 - q)) & 1``, exactly as :func:`project_parity` reads it),
    let ``par_j(x) = bit_j(x) XOR bit_{j+1}(x)``. :func:`project_parity` is an
    elementwise multiply by the 0/1 mask ``[par_j(x) = s][par_j(y) = s]``, so

        ``dephase_parity(rho, j, j+1, n)[x, y]
            = rho[x, y] * ([par_j(x)=0][par_j(y)=0] + [par_j(x)=1][par_j(y)=1])
            = rho[x, y] * M_j[x, y]``,  ``M_j[x, y] = [par_j(x) == par_j(y)]``.

    Elementwise 0/1 multiplies commute and compose, so the full sweep is one
    multiply by ``M = prod_j M_j``: ``M[x, y] = 1`` iff ``x`` and ``y`` carry
    identical full adjacent-parity (syndrome) vectors.

    IEEE bit-exactness vs the sequential sweep. The mask is cached in ``rho``'s
    own dtype (bool 0/1 -> ``0+0i`` / ``1+0i``), so the multiply is the exact
    same complex-multiply op :func:`project_parity` already performs. Kept
    (same-sector) entries: ``(a + bi)(1 + 0i) = (a - b*0) + (a*0 + b)i``, and
    adding/subtracting a signed zero to a finite component is exact, so the
    value is reproduced exactly; the sequential path additionally adds
    ``rho[x, y] * (0 + 0i) = +-0 +- 0i``, also value-exact. Killed
    (cross-sector) entries: both paths yield an exact complex zero -- only the
    SIGN of that zero (``+-0.0``) may differ between paths, which ``==`` cannot
    distinguish and which no downstream add / multiply / abs / sum can convert
    into a value difference. Backward of a constant-mask multiply is the same
    constant-mask multiply (no custom autograd), so gradients inherit the
    identical argument. Replaces the ``n - 1`` per-round mask-build + two
    multiplies + add of the sequential sweep with a single cached multiply --
    the M3 burn-in loop is launch-bound on CUDA (R2-lite M3, pin P1h).
    Batch-aware over any leading dimensions, like :func:`dephase_parity`.
    """
    if int(n) < 2:
        return rho  # empty sweep: the sequential loop body never runs
    mask = _parity_sweep_mask(int(n), rho.dtype, rho.device)
    return rho * mask


def measure_parity_enumerate(
    rho: torch.Tensor, outcomes: torch.Tensor, qubit_a: int, qubit_b: int, n: int
) -> tuple[torch.Tensor, torch.Tensor]:
    """Branch the enumerated trajectory set on a ``Z_a Z_b`` parity measurement.

    Like :func:`measure_qubit_enumerate` but for a two-qubit Z-parity (a rep-code
    stabilizer) measured directly on the data register; no reset, since there is no
    ancilla to return to ``|0>``. The recorded bit is the parity outcome, matching
    the ancilla backend's record column for that check.
    """
    rho0 = project_parity(rho, qubit_a, qubit_b, 0, n)
    rho1 = project_parity(rho, qubit_a, qubit_b, 1, n)
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
_CONST_CACHE: dict[tuple[str, torch.device], torch.Tensor] = {}


def _dev_const(name: str, device, build) -> torch.Tensor:
    """Per-device cache for the parameterless constant gates (cheap re-use)."""
    key = (name, torch.device(device))
    cached = _CONST_CACHE.get(key)
    if cached is None:
        cached = build().to(key[1])
        _CONST_CACHE[key] = cached
    return cached


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


def cx(device: str | torch.device = "cpu") -> torch.Tensor:
    return _dev_const(
        "cx",
        device,
        lambda: torch.tensor(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=CDTYPE
        ),
    )


def pauli_x(device: str | torch.device = "cpu") -> torch.Tensor:
    return _dev_const("pauli_x", device, lambda: torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE))


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
