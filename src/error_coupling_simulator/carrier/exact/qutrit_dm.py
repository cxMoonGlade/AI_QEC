from __future__ import annotations

"""Exact local-dim ``q`` (qutrit ``q=3`` / ququart ``q=4``) density-matrix engine for
the distance-3 XZZX surface code.

The multi-level (``q**n``) generalization of the 2-level density-matrix primitives in
:mod:`error_coupling_simulator.carrier.exact.circuit_sim`. It holds the
``q**n_data x q**n_data`` density matrix of the data register (no ancilla
instantiated — stabilizers are compiled to direct parity projections on the data
matrix, the existing ``forward/exact`` technique) and evolves it under
single-qudit / two-qudit channels, giving the **EXACT, enumerated** (no Monte-Carlo)
syndrome distribution ``P(s | m)``.

Two local dimensions are supported by ONE parametrized base, :class:`_QuditDM`:

  * ``q = 3`` — :class:`QutritDM`: the ``|2>``-leakage qutrit engine (Phase-1 of the
    historical SIM-ONLY specified-noise process; architecture A; registration
    ``docs/nonpauli_teacher/phase1_qutrit_leakage_registration.md`` §1). At d3 the
    data register is 9 qutrits (``3**9 = 19683``, a ``5.77 GiB`` complex128 density
    matrix that fits the RTX 5090 with ~5.5x headroom); density-matrix projection
    ``Tr[Pi_s rho]`` equals the full Kraus-branch sum exactly
    (``exact_floor_feasibility.py``: agrees to ~1e-16), so the emitted distribution is
    exact, not estimated.
  * ``q = 4`` — :class:`QuquartDM`: the ``|3>``-faithful ququart engine for the
    Path-B leakage-TRANSPORT gap test (Arm 2; pre-registration
    ``docs/twin_validation/leakage_transport_pathB_prereg.md`` §1). The ``|3>``-mediated
    transport (``|12>↔|03>`` superleakage, the on-resonance ``|03>↔|21>`` exchange,
    Miao's ``|30>↔|12>`` / ``|31>↔|22>`` resonances) is NOT representable on the
    qutrit truncation; the Arm-2 channel is a per-CZ ``(16, 16)`` two-ququart Kraus
    set (canonical owner: ``error_coupling_simulator.mechanisms.cz_leakage``). Ququart DM
    is ``4**n`` — RESOURCE-CAPPED at ``n <= 6`` (``4**6 = 4096`` -> 256 MB DM); the
    full 9-data ququart register (``4**9`` -> ~1 TB) is FORBIDDEN. The gap-test
    sub-codes are ``<= 6`` qudits.

Genericity (binding). The engine takes any single-qudit Kraus list, any stabilizer
``paulis`` dict (``{data_site -> 'X'|'Z'}``) and the leaked-readout bias ``b``. It does
NOT import any leakage channel or the XZZX parser. The code geometry (stabilizers +
logical operators) is supplied through :meth:`set_code` by the harness; ``init_logical``
and ``logical_distribution`` use it when present and fall back to a trivial-but-valid
codestate pair otherwise (so the engine is unit-testable on small ``n`` without any
code definition).

Leaked readout — swept-``b`` POVM (registration §2.2). A data qudit found in the
leaked level ``|2>`` during a stabilizer measurement is read by a 2-outcome POVM:
``F1 = |1><1| + b|2><2|``, ``F0 = |0><0| + (1-b)|2><2|`` (so ``F0 + F1 = I`` on the
``{|0>,|1>,|2>}`` block), where ``b = P(|2> reads "1"-like) in [0, 1]`` is a SWEPT
nuisance parameter — NOT a pinned magic constant. For ``q = 4`` the additional
non-computational level ``|3>`` is read with the SAME leaked classifier as ``|2>`` (the
device IQ readout discriminates computational ``{0,1}`` vs "anything higher" — a leaked
qudit is leaked regardless of WHICH high level it sits in); this is the engine's
declared, bounded readout simplification for the higher leakage level (Arm-2; the
``|3>`` population during measurement is small and reported by Builder A's channel).
``project_stabilizer`` / ``syndrome_distribution`` take ``b`` directly (a ``float``);
for backward compatibility a legacy hard-bit ``leaked_map`` callable is also accepted
and resolved to the boundary ``b in {0,1}`` (:func:`resolve_readout_bias`), so ``b = 1``
reproduces the engine's original hard-bit ``|leaked> -> "1"`` behavior BIT-FOR-BIT.

Conventions
-----------
Basis ``{|0>, ..., |q-1>}`` per qudit; qudit 0 is the most-significant tensor factor,
so digit ``k`` of basis index ``i`` is ``(i // q**(n - 1 - k)) % q`` (the qudit analog
of ``circuit_sim``'s ``(i >> (n - 1 - k)) & 1`` for qubit 0 = MSB). A single-qudit
gate / Kraus is ``(q, q)``; a two-qudit Kraus is ``(q**2, q**2)`` with row/col index
``q*t_i + t_j`` and ``site_i`` the MORE-significant qudit of the pair. The computational
subspace is ``{|0>, |1>}`` and ``|2>`` (and ``|3>`` for ``q=4``) is the leaked level.

GPU only (binding, §1.6). The density matrix lives on ``device='cuda'`` and the
evolution uses plain torch CUDA contractions — no CPU fallback in the evolution path,
no fused kernel (the fused-Kraus kernel is 2-level only; a multi-level kernel is a
deferred optimization). ``complex128`` throughout (precision-first; mirrors
``cptp_channel``).
"""

import torch

from ..cptp_channel import hermitianize
from ...numerics import NUMERICAL_ZERO

CDTYPE = torch.complex128
RDTYPE = torch.float64
QUDIT = 3  # qutrit local dimension (the module's HISTORICAL default; QutritDM uses it,
#            and downstream code imports this constant expecting the value 3 — preserved).


# --------------------------------------------------------------------------- #
# Single-qudit constant operators (dim-parametrized core + qutrit-named shims) #
# --------------------------------------------------------------------------- #
def qudit_eye(q: int, device) -> torch.Tensor:
    return torch.eye(int(q), dtype=CDTYPE, device=device)


def qudit_hadamard(q: int, device) -> torch.Tensor:
    """Hadamard on the computational subspace ``{|0>, |1>}``, identity on the leaked
    levels ``|2>..|q-1>``.

    Diagonalizes the X-type stabilizer parity into the Z basis: ``H X H = Z`` on the
    ``{0, 1}`` block, while the leaked levels are left untouched (their syndrome bit is
    set by the leaked-readout POVM, not by an eigenvalue).
    """
    q = int(q)
    h = torch.zeros((q, q), dtype=CDTYPE, device=device)
    inv2 = 1.0 / (2.0 ** 0.5)
    h[0, 0] = inv2
    h[0, 1] = inv2
    h[1, 0] = inv2
    h[1, 1] = -inv2
    for k in range(2, q):
        h[k, k] = 1.0
    return h


def qutrit_eye(device) -> torch.Tensor:
    return qudit_eye(QUDIT, device)


def qutrit_hadamard(device) -> torch.Tensor:
    """Hadamard on the computational subspace ``{|0>, |1>}``, identity on ``|2>``.

    Diagonalizes the X-type stabilizer parity into the Z basis: ``H X H = Z`` on the
    ``{0, 1}`` block, while ``|2>`` (leaked) is left untouched (its syndrome bit is set
    by ``leaked_map``, not by an eigenvalue). (The qutrit-specific shim over
    :func:`qudit_hadamard`; downstream code imports this name.)
    """
    return qudit_hadamard(QUDIT, device)


# --------------------------------------------------------------------------- #
# Local-operator embedding (qudit Kronecker + axis permutation)               #
# --------------------------------------------------------------------------- #
def embed_operator_q(op: torch.Tensor, site: int, n: int, q: int, *, device=None) -> torch.Tensor:
    """Embed a single-qudit ``(q, q)`` operator on ``site`` into the ``n``-qudit register
    (Kronecker with identity, then permute the qudit axis into place).

    Qudit analog of :func:`circuit_sim.embed_operator` (reshapes to ``[q]*(2n)``).
    Differentiable in ``op``.
    """
    site = int(site)
    n = int(n)
    q = int(q)
    if op.shape != (q, q):
        raise ValueError(f"single-qudit operator must be ({q}, {q}), got {tuple(op.shape)}")
    if device is None:
        device = op.device
    op = op.to(device).contiguous()
    rest = n - 1
    if rest > 0:
        full = torch.kron(op, torch.eye(q ** rest, dtype=CDTYPE, device=device))
    else:
        full = op
    # `full` treats qudit order as: [site, then the rest in ascending order].
    current = [site] + [k for k in range(n) if k != site]
    perm_row = [current.index(k) for k in range(n)]
    perm = perm_row + [n + a for a in perm_row]
    dim = q ** n
    full = full.reshape([q] * (2 * n)).permute(*perm).contiguous().reshape(dim, dim)
    return full


def embed_operator(op: torch.Tensor, site: int, n: int, *, device=None) -> torch.Tensor:
    """Embed a single-qutrit ``(3, 3)`` operator on ``site`` into the ``n``-qutrit
    register (the qutrit-specific shim over :func:`embed_operator_q`; downstream code
    imports this name). Differentiable in ``op``.
    """
    return embed_operator_q(op, site, n, QUDIT, device=device)


def apply_local_op_q(rho: torch.Tensor, op: torch.Tensor, site: int, n: int, q: int) -> torch.Tensor:
    """``rho -> op_site @ rho @ op_site^dag`` by contracting the ``(q, q)`` ``op`` on the
    site's ket/bra factors ONLY -- without ever materializing the full ``q^n x q^n``
    embedded operator.

    Mathematically identical to ``embed_operator_q(op, site, n, q) @ rho @ embed^dag``;
    differs only by floating-point round-off (a different summation order). Differentiable
    in ``op``. ``site`` follows the engine convention: qudit 0 is the most-significant factor.
    """
    site, n, q = int(site), int(n), int(q)
    d = q ** n
    left, right = q ** site, q ** (n - 1 - site)  # factors above/below the site (0 = MSF)
    op = op.contiguous()
    # op on the site factor of the ROW (ket) index:  sum_b op[a,b] rho[l,b,r,c]
    t = torch.einsum("ab,lbrc->larc", op, rho.reshape(left, q, right, d)).reshape(d, d)
    # op^dag on the site factor of the COLUMN (bra) index:  sum_b t[c,l,b,r] conj(op)[a,b]
    t = torch.einsum("ab,clbr->clar", op.conj(), t.reshape(d, left, q, right)).reshape(d, d)
    return t


def apply_local_op(rho: torch.Tensor, op: torch.Tensor, site: int, n: int) -> torch.Tensor:
    """``rho -> op_site @ rho @ op_site^dag`` for a single-qutrit ``(3, 3)`` ``op`` (the
    qutrit-specific shim over :func:`apply_local_op_q`; downstream code imports this name).

    Proven scientifically equivalent (<=1e-12) to the dense embed in
    ``outputs/teacher_prereg/check_subsystem_apply_equiv.py``. ~10^4x fewer FLOPs (no
    ``D^3`` matmul) and no dense operator at n=9. Differentiable in ``op``.
    """
    return apply_local_op_q(rho, op, site, n, QUDIT)


# --------------------------------------------------------------------------- #
# Digit-index helpers (qudit analog of the (i >> shift) & 1 bit reads)        #
# --------------------------------------------------------------------------- #
def _site_digit(idx: torch.Tensor, site: int, n: int, q: int) -> torch.Tensor:
    """Digit value in ``{0, ..., q-1}`` of qudit ``site`` for each basis index in ``idx``
    (qudit 0 = most-significant factor)."""
    place = int(q) ** (int(n) - 1 - int(site))
    return (idx // place) % int(q)


def _site_trit(idx: torch.Tensor, site: int, n: int) -> torch.Tensor:
    """Trit value in ``{0, 1, 2}`` of qutrit ``site`` for each basis index in ``idx``
    (qutrit 0 = most-significant factor). The qutrit-specific shim over
    :func:`_site_digit`; downstream code imports this name."""
    return _site_digit(idx, site, n, QUDIT)


def resolve_readout_bias(b) -> float:
    """Resolve the leaked-readout bias ``b = P(|2> reads "1"-like) in [0, 1]``.

    The engine's readout model is the swept-``b`` 2-outcome POVM (registration
    ``phase1_qutrit_leakage_registration.md`` §2.2): on a stabilizer support the
    per-data-qudit measurement is ``F1 = |1><1| + b|2><2|``, ``F0 = |0><0| +
    (1-b)|2><2|`` (``F0 + F1 = I``); ``b`` is a SWEPT nuisance, NOT a magic constant.

    This helper accepts the swept ``b`` directly as a ``float`` and ALSO accepts the
    legacy hard-bit ``leaked_map`` CALLABLE (``leaked_map(2) -> int``) as a
    backward-compatibility shim: a callable is evaluated at level ``2`` and its hard
    bit is taken as the boundary ``b in {0.0, 1.0}`` (``leaked reads bit 1`` ->
    ``b = 1.0``, the engine's original hard-bit behavior, reproduced BIT-FOR-BIT;
    ``bit 0`` -> ``b = 0.0``). ``None`` defaults to the device-grounded ``b = 1.0``
    (``|2>`` sits above ``|1>`` in the IQ plane, reads ``|1>``-like). The previous
    integer-returning ``leaked_map`` interface is thereby subsumed: every old call
    site (which passed ``lambda: 1``) maps to ``b = 1.0`` and is unchanged.
    """
    if b is None:
        return 1.0
    if callable(b):
        return float(int(b(2)) & 1)  # hard-bit limit: leaked reads bit -> b in {0,1}
    bval = float(b)
    if not 0.0 <= bval <= 1.0:
        raise ValueError(f"readout bias b must be a probability in [0, 1] (got {bval})")
    return bval


#: Memory-lean apply constants (2026-07-06, residual-② fix; class (c) PERFORMANCE knobs —
#: exactness is unaffected: chunking slices FREE axes only, never a contraction sum (the
#: per-element (b,e) sum is complete within its chunk; BLAS-internal summation order may
#: differ — equivalence enforced to <=1e-13, not bit-identity); falsifiers in
#: tests/test_qutrit_dm_memlean.py). Measured pre-fix peak was ~5 live DM copies during an
#: X-support projection (einsum permute/bmm/reshape temporaries + out-of-place hermitianize);
#: post-fix the apply path holds input + output + chunk/tile-sized temporaries only.
_APPLY_CHANNEL_CHUNKS = 8
_HERMITIANIZE_BLOCK = 4096
#: Below this DM dimension the single-contraction path runs instead (2026-07-06 follow-up:
#: at n=5 the chunk loop's fixed per-call overhead made the proxy round ~5.5x slower while
#: the ~5 small copies it avoids are only a few hundred MB — harmless). 2187 = 3^7: qutrit
#: n<=6 and ququart n<=5 take the fast path; every DM-scale register (3^7+, 4^6+) is chunked.
_CHUNK_MIN_DIM = 2187


def _chunk_slices(size: int, n_chunks: int):
    """Contiguous slice cover of ``range(size)`` in ``<= n_chunks`` pieces."""
    n_chunks = max(1, min(int(n_chunks), int(size)))
    step = (int(size) + n_chunks - 1) // n_chunks
    for start in range(0, int(size), step):
        yield slice(start, min(start + step, int(size)))


def hermitianize_inplace_blocked(t: torch.Tensor, block: int = _HERMITIANIZE_BLOCK) -> torch.Tensor:
    """``t -> 0.5 * (t + t^dag)`` IN PLACE, tile-pair-wise (peak extra memory = one tile).

    Elementwise identical arithmetic to ``cptp_channel.hermitianize`` (each entry becomes
    ``0.5*(t[i,j] + conj(t[j,i]))``) without materializing the full ``t^dag`` sum output —
    the memory-lean form for DM-scale matrices (a full-size temporary is 5.77 GiB at
    ``3**9``). Falsifier: ``tests/test_qutrit_dm_memlean.py::test_hermitianize_blocked``.
    """
    d = int(t.shape[0])
    # Keep at least a ~4x4 tile grid: a single whole-matrix "tile" would reintroduce the
    # full-size temporaries this function exists to avoid (the n=7/8 dims are BELOW the
    # absolute default block — caught by the 2026-07-06 bisect: dim 2187 degenerated to one
    # block and the peak stayed at the pre-fix multiplier).
    block = max(1, min(int(block), (d + 3) // 4))
    for i0 in range(0, d, block):
        i1 = min(i0 + block, d)
        for j0 in range(i0, d, block):
            j1 = min(j0 + block, d)
            a = t[i0:i1, j0:j1]
            if i0 == j0:
                # aliasing-safe single tile temp: add allocates once, mul_ is in place
                blk = a.add(a.mH).mul_(0.5)
                a.copy_(blk)
            else:
                b = t[j0:j1, i0:i1]
                blk = a.add(b.mH).mul_(0.5)
                a.copy_(blk)
                b.copy_(blk.mH)
    return t


class _QuditDM:
    """Exact ``q**n_data x q**n_data`` data-register density matrix (local dim ``q``).

    See module docstring for conventions. The engine is generic over channels,
    stabilizers and the leaked-readout map; the code geometry is injected via
    :meth:`set_code`. Subclassed by :class:`QutritDM` (``q=3``) and :class:`QuquartDM`
    (``q=4``); the two share EVERY method here (only the local dim ``self.q`` differs),
    so the ``q=3`` path is bit-identical to the historical hand-written qutrit engine
    (regression-checked in ``tests/test_qutrit_dm_exact.py`` + the dense-embed oracle).
    """

    QDIM: int = 3  # subclasses override (3 for qutrit, 4 for ququart)

    def __init__(self, n_data: int, device: str | torch.device = "cuda", dtype=CDTYPE) -> None:
        self.n = int(n_data)
        if self.n < 1:
            raise ValueError("n_data must be >= 1")
        if dtype != CDTYPE:
            # Precision-first contract: the engine is complex128 only.
            raise ValueError("the exact qudit DM engine is complex128-only (precision-first)")
        self.q = int(self.QDIM)
        if self.q < 2:
            raise ValueError(f"local dim q must be >= 2 (got {self.q})")
        self.device = torch.device(device)
        self.dtype = dtype
        self.dim = self.q ** self.n
        # rho lives here (LAZY since 2026-07-06: the constructor no longer eagerly
        # allocates the q^n x q^n zeros — vector-only uses such as
        # FusedWithinCycleSampler.build_codestate
        # were paying a 5.77 GiB DM at n=9 they never touched; first ACCESS materializes the
        # same all-zero matrix, so every reader sees the historical behavior unchanged).
        self._rho: torch.Tensor | None = None
        # optional code geometry (set by the harness)
        self._stabilizers: list[dict[int, str]] | None = None
        self._logical_x: dict[int, str] | None = None
        self._logical_z: dict[int, str] | None = None

    @property
    def rho(self) -> torch.Tensor:
        if self._rho is None:
            self._rho = torch.zeros((self.dim, self.dim), dtype=self.dtype, device=self.device)
        return self._rho

    @rho.setter
    def rho(self, value: torch.Tensor) -> None:
        self._rho = value

    # ----------------------------------------------------------------------- #
    # Local single-qudit operators (dim-aware versions of the module helpers)  #
    # ----------------------------------------------------------------------- #
    def _eye(self) -> torch.Tensor:
        return qudit_eye(self.q, self.device)

    def _hadamard(self) -> torch.Tensor:
        return qudit_hadamard(self.q, self.device)

    # ----------------------------------------------------------------------- #
    # Code geometry injection (harness-supplied; additive to the frozen API)  #
    # ----------------------------------------------------------------------- #
    def set_code(
        self,
        stabilizers: list[dict[int, str]] | None = None,
        logical_x: dict[int, str] | None = None,
        logical_z: dict[int, str] | None = None,
    ) -> None:
        """Inject the code geometry used by :meth:`init_logical` / :meth:`logical_distribution`.

        ``stabilizers`` is the list of stabilizer ``paulis`` dicts (same format as
        :meth:`project_stabilizer`); ``logical_x`` / ``logical_z`` are the logical
        operator supports as ``{site -> 'X'|'Z'}`` dicts. All optional — without them
        the engine still runs (trivial-but-valid codestates), which is what makes the
        small-``n`` unit checks code-free.
        """
        self._stabilizers = None if stabilizers is None else [dict(s) for s in stabilizers]
        self._logical_x = None if logical_x is None else dict(logical_x)
        self._logical_z = None if logical_z is None else dict(logical_z)

    # ----------------------------------------------------------------------- #
    # State preparation                                                       #
    # ----------------------------------------------------------------------- #
    def set_state(self, rho: torch.Tensor) -> None:
        """Replace the internal density matrix (e.g. with a custom test state)."""
        rho = rho.to(self.device).to(self.dtype)
        if rho.shape != (self.dim, self.dim):
            raise ValueError(f"rho must be ({self.dim}, {self.dim}), got {tuple(rho.shape)}")
        self.rho = hermitianize(rho)

    def init_logical(self, m: int) -> None:
        """Prepare the logical codestate ``|m>_L``, ``m in {0, 1}``.

        With a code geometry set (:meth:`set_code`): build the +1 joint-stabilizer
        eigenstate with logical-Z eigenvalue ``(-1)**m`` by projecting a seed onto
        the stabilizer group and the logical-Z sector (exact, normalized). Without a
        code geometry: a trivial-but-valid orthogonal pair — ``|0...0>`` for ``m=0``
        and its logical-X image for ``m=1`` (logical-X defaults to ``X`` on qudit 0).
        Either way ``init_logical(0)`` and ``init_logical(1)`` are orthogonal pure
        codestates with ``Tr(rho)=1``.
        """
        m = int(m)
        if m not in (0, 1):
            raise ValueError("logical index m must be 0 or 1")

        if self._stabilizers:
            psi = self._codestate_vector(m)
        else:
            # trivial code: |0...0> and its logical-X image
            psi = torch.zeros(self.dim, dtype=self.dtype, device=self.device)
            psi[0] = 1.0
            lx = self._logical_x or {0: "X"}
            psi = self._apply_logical_vector(psi, lx) if m == 1 else psi
        nrm = torch.linalg.vector_norm(psi)
        if nrm.real <= NUMERICAL_ZERO:
            raise RuntimeError(f"logical |{m}>_L preparation collapsed to zero norm")
        psi = psi / nrm.to(self.dtype)
        self.rho = torch.outer(psi, psi.conj())
        self._logical_m = m  # remembered so record_oracle can fold m into the logical-ERROR rate

    def _codestate_vector(self, m: int) -> torch.Tensor:
        """Pure-state ``|m>_L`` via stabilizer + logical-Z projection of a seed.

        ``|m>_L = (prod_g (I + g)/2) (I + (-1)**m Z_L)/2 |seed>`` up to norm, where the
        ``g`` are the stabilizer generators and ``Z_L`` the logical-Z operator (all
        acting on the ``{0,1}`` computational subspace). Exact for any commuting
        stabilizer + logical set.
        """
        seed = torch.zeros(self.dim, dtype=self.dtype, device=self.device)
        # a generic seed with computational-subspace support so the projectors don't
        # annihilate it; |0...0> then a uniform {0,1}-superposition mix.
        seed[0] = 1.0
        # spread into the {0,1}^n subspace so X-type stabilizers have a foothold
        for site in range(self.n):
            h = self._hadamard()
            seed = self._apply_op_vector(seed, h, site)

        psi = seed
        for g in self._stabilizers or []:
            psi = self._project_operator_vector(psi, g, +1)
        lz = self._logical_z or {0: "Z"}
        psi = self._project_operator_vector(psi, lz, (-1) ** m)
        return psi

    # ----------------------------------------------------------------------- #
    # Gate / channel application                                              #
    # ----------------------------------------------------------------------- #
    def apply_gate(self, U: torch.Tensor, site: int) -> None:
        """Apply a single-qudit unitary ``U:(q,q)`` on ``site``: ``rho -> U rho U^dag``.

        Routed through the lean single-pass superoperator :meth:`apply_channel` (a unitary is a
        one-Kraus channel) -- ~3x faster + leaner than the two-einsum ``apply_local_op`` path,
        identical math (``U rho U^dag``). The X-type stabilizer Hadamards ran through here, so
        this is the enumeration's hot path.
        """
        self.apply_channel([U], site)

    def apply_channel(self, kraus, site: int) -> None:
        """Apply a single-qudit CPTP channel on ``site``: ``rho -> sum_k K_k rho K_k^dag``,
        via the SITE SUPEROPERATOR contracted CHUNK-WISE into a preallocated output.

        ``S[a,c,b,e] = sum_k K_k[a,b] conj(K_k[c,e])`` (a tiny ``q x q x q x q``) is contracted
        on the site's ket/bra factors of ``rho`` -- the ``r`` Kraus collapse into a single pass.
        MEMORY-LEAN FORM (2026-07-06, residual-② fix): the contraction is evaluated in
        ``_APPLY_CHANNEL_CHUNKS`` slices of the LARGER FREE axis (ket-left or bra-right), each
        written into a preallocated output, and the hermitian symmetrization runs tile-pair-wise
        in place — peak live memory = input + output + chunk/tile temporaries (~2+eps DM copies),
        instead of the ~5 copies the single whole-DM einsum + out-of-place hermitianize held
        (measured k=5.05-5.44 at n=7/8, residual-② 2026-07-06). Chunking slices FREE axes only —
        the (b, e) contraction sum is complete within each chunk, no partial sums are formed
        across chunks (BLAS-internal summation order may still differ; the equivalence gate
        enforces <=1e-13 agreement, not bit-identity). Identical math to
        ``cptp_channel.apply_kraus(rho, stack(embed_operator_q(k)))`` (proven equivalent in
        check_subsystem_apply_equiv.py for q=3; the same contraction algebra for q=4); the
        chunked==unchunked falsifier is ``tests/test_qutrit_dm_memlean.py``.
        """
        q = self.q
        d = self.dim
        left, right = q ** int(site), q ** (self.n - 1 - int(site))
        ks = torch.stack([torch.as_tensor(k, dtype=self.dtype, device=self.device) for k in kraus]).contiguous()
        if ks.shape[-2:] != (q, q):
            raise ValueError(f"each single-qudit Kraus must be ({q}, {q}), got {tuple(ks.shape[-2:])}")
        sop = torch.einsum("kab,kce->acbe", ks, ks.conj())  # (q,q,q,q) site superoperator
        # rho (d,d) -> (left, b, right, left, e, right); contract S on the site ket(b)/bra(e) axes
        rho6 = self.rho.reshape(left, q, right, left, q, right)
        if d < _CHUNK_MIN_DIM:
            # small-register fast path: the handful of whole-DM temporaries are a few
            # hundred MB at most here, while the chunk loop's fixed per-call overhead
            # dominated (measured 2026-07-06: the n=5 proxy round went 2.09 -> 11.6 ms
            # under unconditional chunking). Identical math either way.
            t = torch.einsum("acbe,lbrLeR->larLcR", sop, rho6).reshape(d, d)
            self.rho = hermitianize(t)
            return
        out = torch.empty((d, d), dtype=self.dtype, device=self.device)
        out6 = out.reshape(left, q, right, left, q, right)
        if left >= right:
            for sl in _chunk_slices(left, _APPLY_CHANNEL_CHUNKS):
                out6[sl] = torch.einsum("acbe,lbrLeR->larLcR", sop, rho6[sl])
        else:
            for sl in _chunk_slices(right, _APPLY_CHANNEL_CHUNKS):
                out6[..., sl] = torch.einsum("acbe,lbrLeR->larLcR", sop, rho6[..., sl])
        hermitianize_inplace_blocked(out)
        self.rho = out

    def apply_channel_2site(self, kraus, site_i: int, site_j: int) -> None:
        """Apply a TWO-qudit CPTP channel on ``(site_i, site_j)``:
        ``rho -> sum_k K_k rho K_k^dag``, via the TWO-SITE SUPEROPERATOR contracted on
        BOTH sites' ket AND bra factors in ONE pass (NO dense ``q^n x q^n`` embed).

        Each ``K_k`` is a ``(q^2, q^2)`` operator on the ``site_i ⊗ site_j`` factor with
        row/col index ``q*t_i + t_j`` — ``site_i`` is the MORE-significant qudit of the
        pair (matching the engine's qudit-0 = MSF convention). Reshaped to
        ``(q, q, q, q)`` it is ``K[ti_out, tj_out, ti_in, tj_in]``.

        This is the two-site generalization of :meth:`apply_channel`'s no-dense-embed
        pattern: the two-site superoperator
        ``S[ai,aj,ci,cj, bi,bj,ei,ej] = sum_k K_k[ai,aj,bi,bj] conj(K_k[ci,cj,ei,ej])``
        (a tiny ``q^8`` tensor) is contracted on the ket digits ``(bi, bj)`` and bra digits
        ``(ei, ej)`` of ``rho`` — so the ``r`` Kraus collapse into a single contraction
        (peak ~2x rho), never an ``r``-fold stack of dense ``q^n`` embedded operators.

        ARBITRARY (possibly non-adjacent) sites are handled by factoring ``rho`` into the
        before / site_lo / between / site_hi / after blocks on BOTH the ket and the bra
        index (5 factors each). The ``(q^2, q^2)`` Kraus is always indexed with ``site_i``
        as the high pair-digit; when ``site_i > site_j`` the pair axes are swapped into the
        ``(lo, hi)`` register layout so the SAME ``(q^2, q^2)`` operator is applied to the
        intended (i, j) sites regardless of their numeric order. Hermitianizes the result.
        Identical math to ``apply_kraus(rho, stack(embed_2site(K, i, j)))`` (proven
        equivalent in ``outputs/teacher_prereg/ws2_two_site_apply_check.py`` for q=3 and in
        ``outputs/teacher_prereg/pathB_ququart_engine_check.py`` for q=4 — vs a from-scratch
        dense Kron-embed, both to ~1e-15).
        """
        q = self.q
        i, j = int(site_i), int(site_j)
        n = self.n
        if i == j:
            raise ValueError(f"apply_channel_2site needs two distinct sites (got {i}, {j})")
        if not (0 <= i < n and 0 <= j < n):
            raise ValueError(f"sites {i}, {j} out of range for n={n}")
        d = self.dim
        q2 = q * q
        # the (q^2,q^2) Kraus index is q*t_i + t_j; reshape -> K[ti_out, tj_out, ti_in, tj_in].
        ks = torch.stack(
            [torch.as_tensor(k, dtype=self.dtype, device=self.device) for k in kraus]
        ).contiguous()
        if ks.shape[-2:] != (q2, q2):
            raise ValueError(
                f"each two-qudit Kraus must be ({q2}, {q2}), got {tuple(ks.shape[-2:])}")
        ks = ks.reshape(-1, q, q, q, q)  # [k, ti_out, tj_out, ti_in, tj_in]
        # Lay the register out as (lo, hi) with lo < hi. The Kraus pair-axes are (i, j);
        # if i > j swap them so axis 0 of the (reshaped) Kraus aligns with the LOW site.
        lo, hi = (i, j) if i < j else (j, i)
        if i > j:
            # swap the two pair legs (out pair and in pair) so K is indexed [t_lo, t_hi, ...]
            ks = ks.permute(0, 2, 1, 4, 3).contiguous()
        # two-site superoperator S[ a_lo,a_hi, c_lo,c_hi, b_lo,b_hi, e_lo,e_hi ]
        #   = sum_k K[a_lo,a_hi,b_lo,b_hi] * conj(K[c_lo,c_hi,e_lo,e_hi])
        sop = torch.einsum("kABbq,kCDes->ABCDbqes", ks, ks.conj())  # (q,)*8
        L = q ** lo                    # factors ABOVE the low site (0 = MSF)
        Mid = q ** (hi - lo - 1)       # factors BETWEEN the two sites
        Rt = q ** (n - 1 - hi)         # factors BELOW the high site
        # rho -> ket [L, b_lo, Mid, b_hi, Rt] , bra [L, e_lo, Mid, e_hi, Rt]
        #   subscript l b m q r P e M s u  (b,q = ket in-digits; e,s = bra in-digits, the
        #   contracted axes — letters MATCH sop's in-indices b,q,e,s). The outputs are the
        #   ket out-pair (A=a_lo at lo slot, B=a_hi at hi slot) and bra out-pair (C, D).
        t = torch.einsum(
            "ABCDbqes,lbmqrPeMsu->lAmBrPCMDu",
            sop,
            self.rho.reshape(L, q, Mid, q, Rt, L, q, Mid, q, Rt),
        ).reshape(d, d)
        self.rho = hermitianize(t)

    def single_qudit_gate(self, name: str) -> torch.Tensor:
        """A single-qudit FRAME gate ``(q,q)`` on the computational ``{0,1}`` subspace
        (leaked levels inert), by stim name: ``X``/``Y``/``Z``/``S``/``S_DAG``/``H``/``I``.

        These are the per-round transversal DATA frame gates the shipped XZZX circuit applies
        (the mid-cycle ``X`` echo + the post-M ``Y``; the P4a interface contract's
        ``SV_GATE_IDS`` alphabet). The leaked levels ``|2>..|q-1>`` are left untouched (the
        leaked level is inert under the computational frame), matching the SV-MC kernel's gate
        convention bit-for-bit so the DM oracle and the SV-MC apply the IDENTICAL per-round gate.
        """
        nm = str(name).upper()
        q = self.q
        m = torch.zeros((q, q), dtype=self.dtype, device=self.device)
        if nm == "X":
            m[0, 1] = 1.0; m[1, 0] = 1.0
        elif nm == "Y":
            m[0, 1] = -1.0j; m[1, 0] = 1.0j
        elif nm == "Z":
            m[0, 0] = 1.0; m[1, 1] = -1.0
        elif nm == "S":
            m[0, 0] = 1.0; m[1, 1] = 1.0j
        elif nm == "S_DAG":
            m[0, 0] = 1.0; m[1, 1] = -1.0j
        elif nm == "H":
            return self._hadamard()
        elif nm == "I":
            return self._eye()
        else:
            raise ValueError(f"unsupported single-qudit frame gate {name!r}")
        # leaked levels inert (identity on |2>..|q-1>)
        for k in range(2, q):
            m[k, k] = 1.0
        return m

    # Backward-compatible alias (the qutrit engine's public name; downstream callers use it).
    def single_qutrit_gate(self, name: str) -> torch.Tensor:
        """Qutrit-named alias of :meth:`single_qudit_gate` (preserves the historical API)."""
        return self.single_qudit_gate(name)

    def apply_round_data_gates(self, gates: list[tuple[str, "list[int] | tuple[int, ...]"]]) -> None:
        """Apply a per-round transversal single-qudit DATA FRAME to ``rho``, IN ORDER.

        ``gates`` is an ordered list of ``(gate_name, sites)`` — for d3 XZZX the per-round DD echo
        ``[("X", [0,..,8]), ("Y", [0,..,8])]`` (the mid-cycle transversal X echo FOLLOWED BY the
        post-M transversal Y). Each entry is applied IN THE GIVEN ORDER as
        ``rho -> (prod_site U_site) rho (prod_site U_site)^dag`` (commuting single-qudit gates,
        leaked levels inert), so passing ``X`` before ``Y`` realizes the physical
        mid-cycle-then-post-M order. The pair ``X;Y = diag(i,-i,1,...)`` on the comp block is the
        DD echo that refocuses the WG ``|1><->|2>`` leakage exchange.

        No-op for an empty ``gates`` list (a frameless / R=1-floor schedule), so existing callers
        are unaffected.
        """
        for name, sites in gates:
            U = self.single_qudit_gate(name)
            for site in sites:
                self.apply_gate(U, int(site))

    # ----------------------------------------------------------------------- #
    # P4a within-cycle leakage (the circuit-faithful per-cycle model §2/§3)    #
    # ----------------------------------------------------------------------- #
    def apply_within_cycle_premeasure(
        self, streams: dict[int, "list[str] | tuple[str, ...]"], leak_kraus
    ) -> None:
        """Apply the per-qudit PRE-measurement within-cycle stream of ONE round to ``rho``.

        ``streams`` maps engine register position ``q`` -> that qudit's ordered interior token
        stream (``H`` / ``X`` / ``LEAK``; the post-M ``Y`` and the ``M`` marker are handled by
        :meth:`apply_within_cycle_postmeasure` and the stabilizer measurement). ``leak_kraus`` is
        the per-CZ-layer leak slice ``exp(L/4)`` (a single-qudit Kraus list).

        For each qudit ``q`` the tokens are replayed IN ORDER on the full ``rho`` (model §2):
        ``H`` -> the qudit Hadamard (leaked inert), ``X`` -> the mid-cycle X echo, ``LEAK`` ->
        the ``exp(L/4)`` channel (one per CZ layer the qudit touches). Because single-qudit ops on
        DISTINCT qudits commute, applying each qudit's stream sequentially in its own order is
        identical to the true global interleaving.

        Tokens stop at the ``M`` boundary (only the pre-M part is applied here). Any ``Y`` in the
        stream is post-M and is IGNORED here (applied after the measurement). Unknown tokens raise.
        """
        kraus = list(leak_kraus)
        for q, toks in streams.items():
            site = int(q)
            for tok in toks:
                if tok == "M":
                    break
                if tok == "LEAK":
                    self.apply_channel(kraus, site)
                elif tok == "H":
                    self.apply_gate(self._hadamard(), site)
                elif tok == "X":
                    self.apply_gate(self.single_qudit_gate("X"), site)
                elif tok == "Y":
                    continue  # post-M frame: applied by apply_within_cycle_postmeasure
                else:
                    raise ValueError(f"within-cycle pre-measure: unknown token {tok!r} at site {site}")

    def apply_within_cycle_postmeasure(
        self, streams: dict[int, "list[str] | tuple[str, ...]"], *, terminal: bool = False
    ) -> None:
        """Apply the per-qudit POST-measurement within-cycle frame (the transversal ``Y``).

        After the stabilizer measurement, each qudit's post-M tokens (the ``Y`` for an interior
        round) are applied to ``rho`` (leaked inert; ``H X H = Z`` plus this ``Y`` form the DD
        echo that refocuses the leaked level). The TERMINAL round drops the post-M ``Y`` (it ends
        in the terminal data readout): pass ``terminal=True`` to skip it.

        ``streams`` is the same per-position token map as
        :meth:`apply_within_cycle_premeasure`; only tokens AFTER the ``M`` marker are applied.
        """
        if terminal:
            return
        for q, toks in streams.items():
            site = int(q)
            seen_m = False
            for tok in toks:
                if tok == "M":
                    seen_m = True
                    continue
                if not seen_m:
                    continue
                if tok == "Y":
                    self.apply_gate(self.single_qudit_gate("Y"), site)
                elif tok in ("X", "H", "LEAK"):
                    raise ValueError(
                        f"within-cycle post-measure: unexpected token {tok!r} after M at site {site} "
                        f"(only the transversal Y is expected post-M for d3 XZZX)")

    def run_within_cycle_single_qudit(
        self, streams: dict[int, "list[str] | tuple[str, ...]"], leak_kraus, site: int,
        init_level: int, R: int, *, with_Y: bool = True,
    ) -> float:
        """The single-isolated-qudit leaked population after ``R`` within-cycle rounds (model §5).

        Reproduces the P4a model §5 deliverable target: an isolated data qudit (``site``) starting
        in ``|init_level>`` evolved through ``R`` interior within-cycle rounds (per-CZ ``exp(L/4)``
        slices at its CZ layers, the per-qubit H's at their slots, the mid-cycle X, and — when
        ``with_Y`` — the post-M Y on every round). No stabilizer measurement. Returns ``rho[2,2]``
        (the ``|2>`` population, real).

        This is a small ``n=1`` engine instance built locally, independent of the n-qudit ``rho``.
        """
        toks = list(streams[int(site)])
        eng = type(self)(1, device=self.device)
        rho0 = torch.zeros((self.q, self.q), dtype=self.dtype, device=self.device)
        rho0[int(init_level), int(init_level)] = 1.0
        eng.set_state(rho0)
        kraus = list(leak_kraus)
        Xg = eng.single_qudit_gate("X")
        Yg = eng.single_qudit_gate("Y")
        Hg = eng._hadamard()
        for _ in range(int(R)):
            for tok in toks:
                if tok == "M":
                    continue
                if tok == "LEAK":
                    eng.apply_channel(kraus, 0)
                elif tok == "H":
                    eng.apply_gate(Hg, 0)
                elif tok == "X":
                    eng.apply_gate(Xg, 0)
                elif tok == "Y":
                    if with_Y:
                        eng.apply_gate(Yg, 0)
                else:
                    raise ValueError(f"within-cycle single-qudit: unknown token {tok!r}")
        return float(torch.diagonal(eng.rho).real[2])

    # ----------------------------------------------------------------------- #
    # Stabilizer parity projection (the qudit analog of project_parity)       #
    # ----------------------------------------------------------------------- #
    def _povm_diag_weight(self, paulis: dict[int, str], outcome: int, b: float, arm: str = "A") -> torch.Tensor:
        """Diagonal of the stabilizer syndrome-bit POVM ``E_s`` over basis indices.

        The syndrome-bit POVM is ``E_s = sum_{c: XOR_q c_q = s} prod_q F_{c_q}^{(q)}``,
        the sum over per-qubit bit assignments whose XOR equals the syndrome ``s``, of
        the tensor product of single-qudit effects ``F_{c}`` (registration §2.2). Each
        single-qudit effect is DIAGONAL in the (already Z-rotated, so all-Z) basis. With
        the per-qudit **parity weight** ``d_q(0) = +1``, ``d_q(1) = -1`` in EVERY arm, the
        XOR-coefficient extraction collapses to

          ``E_s[i,i] = 1/2 * (1 + (-1)^s * prod_q d_q)`` ,   ``d_q = w0(t_q) - w1(t_q)``

        where the **arm** (P4a interface contract §4) sets the LEAKED weight ``d_q(leaked)``:

          arm A / C : ``d_q(leaked) = 1 - 2b``  (the swept-``b`` leaked classifier; Phase-1)
          arm B1    : ``d_q(leaked) = +1``      (leaked ≡ ``|0>``: leaked-DECOUPLED model)
          arm B2    : ``d_q(leaked) = -1``      (leaked ≡ ``|1>``: coherence UPPER bound)

        For ``q = 4`` EVERY non-computational level ``|2>, |3>`` shares the SAME leaked
        weight ``d_q(leaked)`` — the device discriminates computational ``{0,1}`` from "any
        higher level", so ``|3>`` reads with the same leaked classifier as ``|2>`` (the
        engine's declared, bounded Arm-2 readout simplification; see module docstring).
        Arms A and B2 coincide at ``b = 1`` (both give ``d_q(leaked) = -1``), recovering
        the engine's original hard-bit parity projector ``[parity == s]`` — BIT-FOR-BIT.

        Returns the real, nonnegative diagonal vector ``E_s[i,i] in [0, 1]`` (length
        ``dim``). NOTE: every active site is read as a Z parity here; X-type supports are
        Hadamard-rotated into the Z basis by :meth:`project_stabilizer` BEFORE this is
        called (leaked levels untouched by H, so their leaked rows are basis-independent).
        """
        a = str(arm).upper()
        if a in ("A", "C"):
            d2 = 1.0 - 2.0 * float(b)
        elif a == "B1":
            d2 = 1.0
        elif a == "B2":
            d2 = -1.0
        else:
            raise ValueError(f"unknown measurement arm {arm!r} (expected A, C, B1 or B2)")
        idx = torch.arange(self.dim, device=self.device)
        # d_q = +1 (t=0), -1 (t=1), d2 (t>=2, every leaked level); product over the active sites.
        ones = torch.ones(self.dim, dtype=RDTYPE, device=self.device)
        neg = torch.full((self.dim,), -1.0, dtype=RDTYPE, device=self.device)
        leaked = torch.full((self.dim,), d2, dtype=RDTYPE, device=self.device)
        prod = torch.ones(self.dim, dtype=RDTYPE, device=self.device)
        for site in paulis:
            t = _site_digit(idx, site, self.n, self.q)
            d = torch.where(t == 0, ones, torch.where(t == 1, neg, leaked))
            prod = prod * d
        sign = 1.0 if (int(outcome) & 1) == 0 else -1.0
        return 0.5 * (1.0 + sign * prod)

    def _leak_flag_dephase(self, paulis: dict[int, str]) -> None:
        """Arm-C leak-flag projection (DM-faithful): dephase the leaked levels vs ``{0,1}`` on
        the support, preserving the ``{0,1}`` computational coherence (interface contract §4).

        Averaged over leakage-pattern trajectories the SV-MC's Arm-C sampling IS the dephasing
        channel that kills coherence between basis states with DIFFERENT leak flags on the
        support and leaves everything else untouched. The DM oracle applies that channel directly:

          ``rho[i, j] -> rho[i, j]``   if  ``f_q(t_q^i) == f_q(t_q^j)``  for all ``q in supp``
          ``rho[i, j] -> 0``           otherwise,           ``f_q(t) = [t >= 2] in {0, 1}``.

        ``f_q`` is the IS-LEAKED flag (any non-computational level; for ``q = 4`` ``|2>`` and
        ``|3>`` share flag ``1`` — leaked-vs-computational, not which leaked level). This is
        diagonal-population preserving (``i == j`` always survives), so the subsequent diagonal
        ``E_s`` marginal ``P(s)`` is IDENTICAL to Arm A. ``|0>``<->``|1>`` coherence (same flag
        ``f = 0``) is preserved. Applied to ``rho`` IN PLACE; basis-aligned (``f_q`` is
        Hadamard-invariant: H does not touch the leaked levels).
        """
        idx = torch.arange(self.dim, device=self.device)
        flag = torch.zeros(self.dim, dtype=torch.long, device=self.device)
        # encode the per-support leak-flag vector as an integer key (one bit per support site)
        for bit, site in enumerate(paulis):
            t = _site_digit(idx, site, self.n, self.q)
            flag = flag | ((t >= 2).to(torch.long) << bit)
        # zero rho[i,j] where flag[i] != flag[j] (dephasing across leak sectors), IN-PLACE.
        mask_off = flag[:, None] != flag[None, :]
        self.rho = self.rho.masked_fill(mask_off, 0)

    def project_stabilizer(self, paulis: dict[int, str], outcome: int, b=None, arm: str = "A",
                           *, diagonal_z: bool = False) -> float:
        """Apply the ``outcome``-effect of the stabilizer syndrome-bit POVM to ``rho``
        and return the branch probability ``Tr[E_outcome rho]``; leaves ``rho``
        UN-normalized (post-measurement, unnormalized).

        ``paulis: dict[data_site -> 'X'|'Z']`` is the stabilizer support (XZZX). X-type
        sites are conjugated into the Z basis by Hadamard (``H X H = Z`` on ``{0,1}``;
        leaked untouched), the diagonal syndrome-bit POVM ``E_outcome`` (see
        :meth:`_povm_diag_weight`) is applied as a measurement update, then the X-type
        sites are rotated back so ``rho`` stays in the computational basis for the next
        projection.

        PURE DIAGONAL-Z mode (``diagonal_z=True``). Read every support as a pure Z-parity with
        NO X-support Hadamard (for a state ALREADY in the Z measurement basis).

        Leaked readout — the swept-``b`` POVM (registration §2.2). ``b = P(leaked reads
        "1"-like) in [0, 1]`` is the biased-coin readout of the leaked level(s); the per-
        qudit effects are ``F1 = |1><1| + b|leaked><leaked|``, ``F0 = |0><0| +
        (1-b)|leaked><leaked|`` with ``F0 + F1 = I``, handled correctly against the FULL
        correlated ``rho``. ``b`` may also be the legacy hard-bit callable.

        Measurement INSTRUMENT ARM (P4a interface contract §4). ``arm`` selects the
        registered measurement-instrument arm:

          ``"A"`` (DEFAULT) — Lüders ``sqrt(E_s)`` with ``d_q(leaked) = 1-2b``;
          ``"C"`` — same ``E_s`` as A, but with a leak-flag projection first → maximal
            leakage-sector disturbance;
          ``"B1"`` — ``d_q(leaked) = +1`` (leaked ≡ ``|0>``);
          ``"B2"`` — ``d_q(leaked) = -1`` (leaked ≡ ``|1>``).

        Measurement update. ``E_outcome`` is diagonal with entries ``e_i = E_s[i,i] in
        [0,1]``; the (unnormalized) post-measurement state is ``sqrt(E_s) rho sqrt(E_s)``
        i.e. ``rho[i,j] -> sqrt(e_i) sqrt(e_j) rho[i,j]``. Its trace is ``Tr[E_s rho] =
        P(s)``. Because ``E_0 + E_1 = I``, the two outcome branches' traces sum to the
        parent trace. For arm A at ``b = 1`` (and arm B2) ``E_s`` is a 0/1 projector and
        the update is the exact masked outer product the engine used before — BIT-FOR-BIT.
        """
        bias = resolve_readout_bias(b)
        # PURE diagonal-Z mode: the explicit circuit H's already rotated the X-supports to Z.
        x_sites = [] if diagonal_z else [s for s, p in paulis.items() if str(p).upper() == "X"]
        # rotate X-type supports into the Z basis
        for s in x_sites:
            self.apply_gate(self._hadamard(), s)

        # Arm C: leak-flag dephasing BEFORE the diagonal E_s (§4).
        if str(arm).upper() == "C":
            self._leak_flag_dephase(paulis)

        e_diag = self._povm_diag_weight(paulis, outcome, bias, arm)  # E_s[i,i] in [0,1]
        sqrt_e = torch.sqrt(torch.clamp(e_diag, min=0.0)).to(self.dtype)
        # rho[i,j] -> sqrt(e_i) sqrt(e_j) rho[i,j]  (diagonal POVM Kraus update), IN-PLACE.
        self.rho.mul_(sqrt_e[:, None])
        self.rho.mul_(sqrt_e[None, :].conj())
        prob = torch.diagonal(self.rho).real.sum()

        # rotate the X-type supports back (Hadamard is its own inverse on {0,1})
        for s in x_sites:
            self.apply_gate(self._hadamard(), s)
        return float(prob)

    def syndrome_distribution(self, stabs: list[dict[int, str]], b=None, arm: str = "A",
                              *, diagonal_z: bool = False) -> dict[tuple, float]:
        """EXACT ``P(s)`` over all ``2**len(stabs)`` joint syndromes by depth-first
        projection enumeration (NO Monte-Carlo).

        ``diagonal_z`` is forwarded to :meth:`project_stabilizer` (read every stabilizer as a
        pure diagonal Z-parity, for a state already in the Z measurement basis).

        ``stabs`` is the ordered list of stabilizer ``paulis`` dicts; ``b`` is the swept
        leaked-readout bias ``P(leaked reads "1"-like) in [0,1]`` (the legacy hard-bit callable
        is also accepted). ``arm in {A, C, B1, B2}`` selects the measurement-instrument arm
        (default ``"A"`` keeps every existing caller bit-identical).

        Returns a dict keyed by the syndrome tuple ``s in {0,1}**len(stabs)`` with the exact
        probability of each cell; the values sum to ``Tr(rho)`` (== 1 for a normalized
        codestate). Implemented as a recursive descent that snapshots ``rho`` before each binary
        branch so both outcomes are enumerated from the same parent state — the exact integral
        over Kraus branches, by the density-matrix identity. ``E_0 + E_1 = I``, so the two
        children's traces sum to the parent's (no probability is lost).
        """
        base = self.rho.clone()
        dist: dict[tuple, float] = {}

        def descend(rho_in: torch.Tensor, k: int, prefix: tuple) -> None:
            if k == len(stabs):
                p = float(torch.diagonal(rho_in).real.sum())
                dist[prefix] = p
                return
            for outcome in (0, 1):
                self.rho = rho_in.clone()
                self.project_stabilizer(stabs[k], outcome, b, arm, diagonal_z=diagonal_z)
                child = self.rho
                descend(child, k + 1, prefix + (outcome,))

        descend(base, 0, ())
        self.rho = base  # restore the parent state (projection is enumeration-only)
        return dist

    # ----------------------------------------------------------------------- #
    # Logical readout                                                         #
    # ----------------------------------------------------------------------- #
    def logical_distribution(self, readout_bias: float = 0.5) -> tuple[float, float]:
        """Final logical-parity readout ``(p0, p1)`` under the product POVM.

        With a logical-Z operator set: ``p_m = Tr[ (I + (-1)**m Z_L)/2 . rho ]`` read on the
        computational subspace. Without a code geometry: the parity of the logical-X-image
        support (defaults to qudit 0 in the Z basis), so the trivial codestate pair reads out
        ``(1, 0)`` / ``(0, 1)``. ``readout_bias`` is the probability that any leaked
        level reads as bit 1.  Its default, ``0.5``, preserves the historical neutral
        split; passing the run's swept ``b`` exactly matches the carrier's terminal
        ``F0/F1`` product-POVM convention.  For multiple logical-support sites this
        computes the parity effect directly, including cells with more than one
        leaked site; it is not a per-cell hard-bit approximation.
        """
        if self._logical_z is not None:
            op = self._logical_z
        elif self._logical_x is not None:
            op = self._logical_x
        else:
            op = {0: "X"}  # trivial: read qudit 0

        tr = torch.diagonal(self.rho).real.sum()
        if tr.real <= NUMERICAL_ZERO:
            return 0.0, 0.0

        # rotate X-type logical support into the Z basis to read its parity.
        # MEMORY-LEAN (2026-07-06): normalization moved onto the DIAGONAL VECTOR
        # (diagonal(rho/tr) == diagonal(rho)/tr elementwise-exactly), and the working
        # copy is made only when an X rotation is actually needed — the previous
        # normalize-then-clone held 2 extra DM copies at n=9.
        x_sites = [s for s, p in op.items() if str(p).upper() == "X"]
        if x_sites:
            # No working clone: apply_gate -> apply_channel is strictly OUT-OF-PLACE
            # (fresh output tensor, input never mutated), so rotating "in place" on the
            # alias leaves `saved` untouched — the previous clone was redundant and
            # pushed the X-logical readout to 4 live DM copies (2026-07-06 review).
            saved = self.rho
            for s in x_sites:
                self.apply_gate(self._hadamard(), s)
            diag = torch.diagonal(self.rho).real / tr
            self.rho = saved  # restore (read-only operation)
        else:
            diag = torch.diagonal(self.rho).real / tr

        bias = resolve_readout_bias(readout_bias)
        effect1 = self._povm_diag_weight(op, 1, bias, "A")
        p1 = float((diag * effect1).sum())
        p0 = float((diag * (1.0 - effect1)).sum())
        return p0, p1

    def sequential_stabilizer_marginals(
        self,
        stabs: list[dict[int, str]],
        b=None,
        arm: str = "A",
        *,
        diagonal_z: bool = False,
    ) -> tuple[float, ...]:
        r"""Apply an ordered non-selective Lüders measurement and return its marginals.

        For stabilizer ``j`` the returned value is

        ``Tr[E1_j Phi_(j-1) ... Phi_0(rho_pre)]``,

        where ``Phi_j(rho)`` is the sum of the two unnormalised outcome
        branches produced by :meth:`project_stabilizer`.  This is the exact
        marginal semantics of the sequential carrier measurement.  Computing
        every projection from the same ``rho_pre`` instead gives *isolated*
        probe marginals and is generally wrong when the instruments do not
        commute (notably in the leaked sector).

        The engine is intentionally left in the final non-selective state so a
        caller can apply the terminal logical readout to the same post-measurement
        state without enumerating the full joint distribution.
        """

        rho_nonselective = self.rho
        marginals: list[float] = []
        for stab in stabs:
            self.rho = rho_nonselective.clone()
            marginal = self.project_stabilizer(
                stab, 1, b, arm, diagonal_z=diagonal_z
            )
            branch1 = self.rho
            marginals.append(float(marginal))

            # ``rho_nonselective`` has no consumer after the outcome-0 branch.
            # Pure-Z projection may update that tensor in place; X-support
            # projection rotates through out-of-place gates.  Both therefore
            # implement branch0 + branch1 without an extra full-DM snapshot.
            self.rho = rho_nonselective
            self.project_stabilizer(stab, 0, b, arm, diagonal_z=diagonal_z)
            rho_nonselective = self.rho.add_(branch1)
        self.rho = rho_nonselective
        return tuple(marginals)

    # ----------------------------------------------------------------------- #
    # Multi-round EXACT record oracle (Axis-A independent ground truth; §7.2)  #
    # ----------------------------------------------------------------------- #
    def record_oracle(
        self,
        stabs: list[dict[int, str]],
        round_pre,
        round_post=None,
        *,
        R: int = 1,
        b=None,
        arm: str = "A",
        diagonal_z: bool = False,
        prune: float = NUMERICAL_ZERO,
        m: int | None = None,
        frame_offset: int | None = None,
    ) -> dict:
        r"""EXACT multi-round (syndrome-history, logical) record oracle on the qudit DM.

        The implementation-independent KNOWN-TRUTH oracle the scalable MCWF carrier is
        validated against. It evolves the codestate ``rho`` (already set by
        :meth:`init_logical` / :meth:`set_state`) through ``R`` circuit-faithful rounds,
        applying per round the caller-supplied MECHANISM and enumerating the stabilizer
        syndromes by the EXACT density-matrix Lüders-instrument branch sum.

        Per round ``r`` (0-indexed):
          1. ``round_pre(self, r)`` — apply that round's PRE-measurement mechanism on the
             CURRENT (possibly post-measurement, unnormalized) branch state IN PLACE. It MUST
             mutate ``self.rho`` and return ``None``.
          2. enumerate the ``len(stabs)`` stabilizers' joint syndrome via the existing
             :meth:`project_stabilizer` branch logic, keeping each child's UN-normalized
             post-measurement state for the next round.
          3. ``round_post(self, r)`` — the POST-measurement frame (the transversal Y echo for
             an interior round; DROPPED on the terminal round ``r == R-1``).
        After the final round the logical readout :meth:`logical_distribution` splits each
        terminal branch into ``(p0, p1)``.

        See the qutrit engine history for the full seam/record convention. Returns the same
        ``full_joint`` (R == 1) / ``moments`` (R >= 2) dicts, with the LOGICAL-ERROR ``flip_rate``
        (offset folded), the raw ``readout_one_rate``, and the measured ``echo_frame_offset``.

        RESOURCE NOTE (qudit-general). The full register DM is ``q^n x q^n x 16 B``; the exact
        record enumeration recurses to depth ``len(stabs)*R`` with a state COPY per branch level.
        For ``q = 4`` this is the binding cap: the gap test runs on ``n <= 6`` sub-codes
        (``4^6 = 4096`` -> 256 MB / copy), so the depth-``len(stabs)`` copy stack is bounded.
        ``prune`` (default ``NUMERICAL_ZERO``) drops branches whose running trace is below it;
        the dropped mass is RETURNED in ``dropped_mass`` so the simplification is bounded.
        """
        if R < 1:
            raise ValueError(f"R must be >= 1 (got {R})")
        n_stab = len(stabs)
        base = self.rho.clone()
        prune = float(prune)

        tot_bits = R * n_stab

        def _fold_detectors(svec) -> torch.Tensor:
            """The emitted detector vector (length tot_bits, round-major) for one leaf's raw
            syndrome history svec: det[0,j]=s[0,j]; det[r,j]=s[r,j] XOR s[r-1,j] (the seam fold)."""
            s = torch.tensor(svec, dtype=torch.uint8, device=self.device).reshape(R, n_stab)
            d = torch.empty((R, n_stab), dtype=torch.uint8, device=self.device)
            d[0] = s[0]
            if R > 1:
                d[1:] = s[1:] ^ s[:-1]
            return d.reshape(tot_bits).to(RDTYPE)

        sum1 = torch.zeros(tot_bits, dtype=RDTYPE, device=self.device)        # E[det]
        sum2 = torch.zeros((tot_bits, tot_bits), dtype=RDTYPE, device=self.device)  # E[det det]
        flip_sum = [0.0]          # E[logical flip == 1] (folded readout); list for closure write
        total_mass = [0.0]
        dropped_mass = [0.0]
        full_joint: dict[tuple, float] = {}   # only populated for R == 1

        def _emit_leaf(svec: list[int], rho_leaf: torch.Tensor, path_p: float) -> None:
            total_mass[0] += path_p
            self.rho = rho_leaf
            p0, p1 = self.logical_distribution(b)
            flip_sum[0] += path_p * p1
            dv = _fold_detectors(svec)
            sum1.add_(path_p * dv)
            sum2.add_(path_p * torch.outer(dv, dv))
            if R == 1:
                key = tuple(int(x) for x in svec)
                full_joint[(key, 0)] = full_joint.get((key, 0), 0.0) + path_p * p0
                full_joint[(key, 1)] = full_joint.get((key, 1), 0.0) + path_p * p1

        def _measure_round(rho_in: torch.Tensor, r: int, svec: list[int], path_p: float) -> None:
            def sdesc_slots(rho_s: torch.Tensor, k: int, p_so_far: float) -> None:
                if k == n_stab:
                    if p_so_far <= prune:
                        dropped_mass[0] += p_so_far
                        return
                    if r == R - 1:
                        _emit_leaf(svec, rho_s, p_so_far)
                        return
                    self.rho = rho_s
                    if round_post is not None:
                        round_post(self, r)
                    round_pre(self, r + 1)
                    _measure_round(self.rho, r + 1, svec, p_so_far)
                    return
                slot = r * n_stab + k
                for outcome in (0, 1):
                    self.rho = rho_s.clone()
                    self.project_stabilizer(stabs[k], outcome, b, arm, diagonal_z=diagonal_z)
                    child = self.rho
                    p_child = float(torch.diagonal(child).real.sum())
                    if p_child <= prune:
                        dropped_mass[0] += p_child
                        continue
                    svec[slot] = outcome
                    sdesc_slots(child, k + 1, p_child)
                    svec[slot] = 0  # restore (depth-first backtrack)

            sdesc_slots(rho_in, 0, path_p)

        # drive: round 0 pre-measure mechanism on the codestate, then the round recursion.
        svec0 = [0] * tot_bits
        self.rho = base.clone()
        round_pre(self, 0)
        _measure_round(self.rho, 0, svec0, 1.0)
        self.rho = base  # restore the parent codestate (the oracle is read-only on rho)

        if R == 1:
            syndrome: dict[tuple, float] = {}
            for (s_key, _f), p in full_joint.items():
                syndrome[s_key] = syndrome.get(s_key, 0.0) + p
            p1 = float(flip_sum[0])
            p0 = float(total_mass[0] - flip_sum[0])
            tm1 = float(total_mass[0])
            m_eff = int(getattr(self, "_logical_m", 0) if m is None else m) & 1
            raw1 = p1 / tm1 if tm1 > NUMERICAL_ZERO else 0.0
            ler1, fo1 = self._logical_error_rate(base=base, round_post=round_post, R=1, m_eff=m_eff,
                                                 raw_readout_one=raw1, frame_offset=frame_offset)
            return {
                "kind": "full_joint", "R": 1, "n_stab": n_stab,
                "joint": full_joint,
                "syndrome": syndrome,
                "logical": (p0, p1),
                "detectors": dict(syndrome),  # R=1: detector == raw syndrome (identity fold)
                "flip_rate": ler1,
                "readout_one_rate": raw1,
                "echo_frame_offset": fo1,
                "m": m_eff,
                "total_mass": float(total_mass[0]),
                "dropped_mass": float(dropped_mass[0]),
            }

        # R >= 2: the DETECTOR moments are exact from the accumulated detector first/second moments.
        tm = float(total_mass[0])
        if tm <= NUMERICAL_ZERO:
            raise RuntimeError("record_oracle: all branch mass pruned (no realized record)")
        e1 = (sum1 / tm).reshape(R, n_stab)                 # E[det_{r,j}]
        e2 = (sum2 / tm).reshape(R, n_stab, R, n_stab)      # E[det_{r,j} det_{r',j'}]
        det_marg = e1.clone()                               # exact detector marginals

        def _conn_corr(r, j, rp, jp):
            ea = e1[r, j]
            eb = e1[rp, jp]
            cov = e2[r, j, rp, jp] - ea * eb
            va = ea - ea * ea
            vb = eb - eb * eb
            denom = torch.sqrt(torch.clamp(va * vb, min=0.0))
            if float(denom) <= NUMERICAL_ZERO:
                return torch.zeros((), dtype=RDTYPE, device=self.device)
            return cov / denom

        # round-to-round (same stabilizer, consecutive rounds) detector correlation.
        rr_corr = torch.zeros((R - 1, n_stab), dtype=RDTYPE, device=self.device)
        for r in range(R - 1):
            for j in range(n_stab):
                rr_corr[r, j] = _conn_corr(r, j, r + 1, j)

        # same-round cross-detector (spatial) correlation (different stabilizers, same round).
        spatial_corr = torch.zeros((R, n_stab, n_stab), dtype=RDTYPE, device=self.device)
        for r in range(R):
            for j in range(n_stab):
                for jp in range(n_stab):
                    spatial_corr[r, j, jp] = _conn_corr(r, j, r, jp)

        m_eff = int(getattr(self, "_logical_m", 0) if m is None else m) & 1
        raw_readout_one = float(flip_sum[0] / tm)
        ler, fo = self._logical_error_rate(base=base, round_post=round_post, R=R, m_eff=m_eff,
                                           raw_readout_one=raw_readout_one, frame_offset=frame_offset)
        return {
            "kind": "moments", "R": R, "n_stab": n_stab,
            "det_marg": det_marg.reshape(R * n_stab).detach().cpu().numpy(),
            "rr_corr": rr_corr.detach().cpu().numpy(),
            "spatial_corr": spatial_corr.detach().cpu().numpy(),
            "flip_rate": ler,
            "readout_one_rate": raw_readout_one,
            "echo_frame_offset": fo,
            "m": m_eff,
            "total_mass": tm,
            "dropped_mass": float(dropped_mass[0]),
        }

    def _logical_error_rate(self, *, base, round_post, R: int, m_eff: int,
                            raw_readout_one: float, frame_offset: int | None):
        """Fold the prepared ``m`` + the deterministic interior-frame offset into the raw readout-1
        rate to get the LOGICAL-ERROR rate (0 in the noiseless case for ANY R). Returns ``(ler, fo)``.

        The offset ``fo`` is MEASURED, not assumed: it is what the interior ``round_post`` frames do
        to the NOISELESS prepared codestate. A frame that does NOT leave the logical in a
        DETERMINISTIC sector (``|p0-p1| < 1``) is REFUSED (raises); pass an explicit ``frame_offset``
        there. ``frame_offset`` overrides the measurement entirely."""
        if frame_offset is not None:
            fo = int(frame_offset) & 1
        elif round_post is None or R < 2:
            fo = 0  # no interior frame -> no deterministic offset
        else:
            ref = base.clone()
            self.rho = ref
            for r in range(R - 1):  # interior rounds carry the post-frame (terminal drops it)
                round_post(self, r)
            p0r, p1r = self.logical_distribution()
            self.rho = base  # restore (the oracle is read-only on rho)
            if abs(p0r - p1r) < 1.0 - 1e-9:
                raise RuntimeError(
                    f"record_oracle: round_post does not leave the noiseless codestate in a "
                    f"DETERMINISTIC logical sector (|p0-p1|={abs(p0r - p1r):.2e} < 1) — it is not a "
                    f"clean deterministic echo; pass frame_offset explicitly")
            fo = (0 if p0r >= p1r else 1) ^ m_eff
        ler = raw_readout_one if (m_eff ^ fo) == 0 else 1.0 - raw_readout_one
        return ler, fo

    # ----------------------------------------------------------------------- #
    # Diagnostics                                                             #
    # ----------------------------------------------------------------------- #
    def trace(self) -> float:
        """``Tr(rho)`` (real part)."""
        return float(torch.diagonal(self.rho).real.sum())

    # ----------------------------------------------------------------------- #
    # Internal: operator-on-state-vector helpers (for codestate prep / projn) #
    # ----------------------------------------------------------------------- #
    def _apply_op_vector(self, psi: torch.Tensor, op: torch.Tensor, site: int) -> torch.Tensor:
        """``psi -> op_site @ psi`` by contracting the ``(q, q)`` op on the site factor ONLY.

        MEMORY-LEAN FORM (2026-07-06, residual-② fix): the previous dense
        ``embed_operator_q`` materialized the full ``q^n x q^n`` operator (5.77 GiB at
        ``3**9``, plus a second copy inside kron/permute) for every single-site vector op —
        the source of the measured 17.35 GiB ``build_codestate`` peak. The local contraction
        is mathematically identical (same identity as :func:`apply_local_op_q`, vector form)
        and allocates only ``q^n``-vector temporaries. Falsifier:
        ``tests/test_qutrit_dm_memlean.py::test_apply_op_vector_matches_dense_embed``.
        """
        site = int(site)
        q = self.q
        left, right = q ** site, q ** (self.n - 1 - site)
        op = op.to(self.dtype).to(self.device).contiguous()
        out = torch.einsum("ab,lbr->lar", op, psi.reshape(left, q, right))
        return out.reshape(-1)

    def _single_qudit_pauli(self, kind: str) -> torch.Tensor:
        """``X`` or ``Z`` on the computational ``{0,1}`` subspace (identity on leaked levels)."""
        kind = str(kind).upper()
        q = self.q
        m = torch.zeros((q, q), dtype=self.dtype, device=self.device)
        if kind == "X":
            m[0, 1] = 1.0
            m[1, 0] = 1.0
        elif kind == "Z":
            m[0, 0] = 1.0
            m[1, 1] = -1.0
        elif kind == "I":
            return self._eye()
        else:
            raise ValueError(f"unsupported single-qudit Pauli {kind!r}")
        for k in range(2, q):
            m[k, k] = 1.0
        return m

    # Backward-compatible alias (the qutrit engine's private name; used by self-checks).
    def _single_qutrit_pauli(self, kind: str) -> torch.Tensor:
        return self._single_qudit_pauli(kind)

    def _apply_logical_vector(self, psi: torch.Tensor, op: dict[int, str]) -> torch.Tensor:
        for site, kind in op.items():
            psi = self._apply_op_vector(psi, self._single_qudit_pauli(kind), site)
        return psi

    def _project_operator_vector(self, psi: torch.Tensor, op: dict[int, str], eigenvalue: int) -> torch.Tensor:
        """Project ``psi`` onto the ``eigenvalue``-eigenspace of the (multi-site,
        commuting-Pauli) operator ``op``: ``(I + eigenvalue * O)/2 |psi>``."""
        op_psi = self._apply_logical_vector(psi.clone(), op)
        return 0.5 * (psi + float(eigenvalue) * op_psi)


class QutritDM(_QuditDM):
    """Exact ``3**n_data x 3**n_data`` data-register density matrix for d3 XZZX (local dim 3).

    The ``|2>``-leakage qutrit engine — the R2-validated Phase-1 / Axis-A oracle. A thin
    ``QDIM = 3`` specialization of :class:`_QuditDM` (every method is shared; the ``q = 3``
    path is bit-identical to the historical hand-written qutrit engine, regression-checked
    in ``tests/test_qutrit_dm_exact.py`` + the dense-embed oracle). Arm 1 of the Path-B
    leakage-transport gap test stays on THIS class (local dim 3).
    """

    QDIM = 3


class QuquartDM(_QuditDM):
    """Exact ``4**n_data x 4**n_data`` data-register density matrix (local dim 4, ``|3>``-faithful).

    The ``|3>``-faithful ququart engine for Arm 2 of the Path-B leakage-TRANSPORT gap test
    (``docs/twin_validation/leakage_transport_pathB_prereg.md`` §1). It evolves a d3 SUB-CODE
    density matrix under the Arm-2 per-CZ ``(16, 16)`` two-ququart leakage channel (Builder A,
    ``error_coupling_simulator.mechanisms.cz_leakage``: index ``4*t_flux + t_stat``,
    ``site_i = flux = MSF`` — identical to :meth:`apply_channel_2site`'s convention), measures
    stabilizers (the leaked levels ``|2>, |3>`` share the swept-``b`` leaked classifier) and
    computes the logical outcome, MIRRORING :class:`QutritDM` at local dim 3.

    RESOURCE CAP (the 2026-06-25 OOM). Ququart DM is ``4**n`` complex128:
      n=5 -> 1024-dim DM (16 MB);  n=6 -> 4096-dim DM (256 MB);  n=7 -> 16384-dim (4.3 GB).
    The constructor REJECTS ``n_data > 7`` (and the gap-test sub-codes are ``<= 6``); the full
    9-data ququart register (``4**9`` -> ~1 TB) is structurally forbidden. ``n = 7`` is allowed
    only with care (one process, serial GPU).
    """

    QDIM = 4
    # The hard resource cap (the 2026-06-25 OOM): 4**n complex128 DM. n>7 forbidden outright
    # (4**8 = 65536 -> 68 GB; 4**9 -> ~1 TB). n==7 (4.3 GB) is allowed but heavy — serial GPU only.
    MAX_N: int = 7

    def __init__(self, n_data: int, device: str | torch.device = "cuda", dtype=CDTYPE) -> None:
        n = int(n_data)
        if n > self.MAX_N:
            raise ValueError(
                f"QuquartDM is resource-capped at n_data <= {self.MAX_N} (4**{n} complex128 DM "
                f"= {4 ** n} dim ≈ {(4 ** n) ** 2 * 16 / 1e9:.1f} GB / copy; the gap-test sub-codes "
                f"are <= 6 qudits — the full 9-data ququart register 4**9 ≈ 1 TB is forbidden)")
        super().__init__(n, device=device, dtype=dtype)
