from __future__ import annotations

"""Exact 9-data-qutrit density-matrix engine for the distance-3 XZZX surface code.

The qutrit (``3**n``) generalization of the 2-level density-matrix primitives in
:mod:`qec_twin.forward.exact.circuit_sim` / :mod:`density_sim`. It holds the
``3**n_data x 3**n_data`` density matrix of the data register (no ancilla
instantiated — stabilizers are compiled to direct parity projections on the data
matrix, the existing ``forward/exact`` technique) and evolves it under
single-qutrit channels, giving the **EXACT, enumerated** (no Monte-Carlo)
syndrome distribution ``P(s | m)``.

This is Phase-1 of the SIM-ONLY non-Pauli teacher (architecture A; pre-registration
``docs/nonpauli_teacher/phase1_qutrit_leakage_registration.md`` §1; interface
``phase1_build_contract.md``). At d3 the data register is 9 qutrits (``3**9 = 19683``,
a ``5.77 GiB`` complex128 density matrix that fits the RTX 5090 with ~5.5x headroom);
density-matrix projection ``Tr[Pi_s rho]`` equals the full Kraus-branch sum exactly
(``exact_floor_feasibility.py``: agrees to ~1e-16), so the emitted distribution is
exact, not estimated.

Genericity (binding). The engine takes any single-qutrit Kraus list, any stabilizer
``paulis`` dict (``{data_site -> 'X'|'Z'}``) and the leaked-readout bias ``b``. It does
NOT import the leakage channel (Agent B owns ``channels.leakage_kraus``) or the XZZX
parser (Agent C owns ``xzzx_parser``). The code geometry (stabilizers + logical
operators) is supplied through :meth:`set_code` by the harness; ``init_logical`` and
``logical_distribution`` use it when present and fall back to a trivial-but-valid
codestate pair otherwise (so the engine is unit-testable on small ``n`` without any
code definition).

Leaked readout — swept-``b`` POVM (registration §2.2). A data qutrit found in the
leaked level ``|2>`` during a stabilizer measurement is read by a 2-outcome POVM on
``{|0>,|1>,|2>}``: ``F1 = |1><1| + b|2><2|``, ``F0 = |0><0| + (1-b)|2><2|`` (so
``F0 + F1 = I``), where ``b = P(|2> reads "1"-like) in [0, 1]`` is a SWEPT nuisance
parameter — NOT a pinned magic constant. The stabilizer syndrome-bit POVM is
``E_s = sum_{c: XOR c = s} prod_q F_{c_q}`` and ``P(s) = Tr[E_s rho]`` (against the
FULL correlated ``rho``, not a per-qubit marginal product). ``project_stabilizer`` /
``syndrome_distribution`` take ``b`` directly (a ``float``); for backward
compatibility a legacy hard-bit ``leaked_map`` callable is also accepted and resolved
to the boundary ``b in {0,1}`` (:func:`resolve_readout_bias`), so ``b = 1`` reproduces
the engine's original hard-bit ``|2> -> "1"`` behavior BIT-FOR-BIT.

Conventions
-----------
Basis ``{|0>, |1>, |2>}`` per qutrit; qutrit 0 is the most-significant tensor factor,
so trit ``q`` of basis index ``i`` is ``(i // 3**(n - 1 - q)) % 3`` (the qutrit analog
of ``circuit_sim``'s ``(i >> (n - 1 - q)) & 1`` for qubit 0 = MSB). A single-qutrit
gate / Kraus is ``(3, 3)``; the computational subspace is ``{|0>, |1>}`` and ``|2>`` is
the leaked level.

GPU only (binding, §1.6). The density matrix lives on ``device='cuda'`` and the
evolution uses plain torch CUDA contractions — no CPU fallback in the evolution path,
no fused kernel (the fused-Kraus kernel is 2-level only; a qutrit kernel is a deferred
optimization). ``complex128`` throughout (precision-first; mirrors ``cptp_channel``).
"""

import itertools

import torch

from qec_twin.forward.cptp_channel import apply_kraus as _apply_kraus_torch
from qec_twin.forward.cptp_channel import hermitianize
from qec_twin.numerics import NUMERICAL_ZERO

CDTYPE = torch.complex128
RDTYPE = torch.float64
QUDIT = 3  # qutrit local dimension


# --------------------------------------------------------------------------- #
# Single-qutrit constant operators                                            #
# --------------------------------------------------------------------------- #
def qutrit_eye(device) -> torch.Tensor:
    return torch.eye(QUDIT, dtype=CDTYPE, device=device)


def qutrit_hadamard(device) -> torch.Tensor:
    """Hadamard on the computational subspace ``{|0>, |1>}``, identity on ``|2>``.

    Diagonalizes the X-type stabilizer parity into the Z basis: ``H X H = Z`` on the
    ``{0, 1}`` block, while ``|2>`` (leaked) is left untouched (its syndrome bit is set
    by ``leaked_map``, not by an eigenvalue).
    """
    h = torch.zeros((QUDIT, QUDIT), dtype=CDTYPE, device=device)
    inv2 = 1.0 / (2.0 ** 0.5)
    h[0, 0] = inv2
    h[0, 1] = inv2
    h[1, 0] = inv2
    h[1, 1] = -inv2
    h[2, 2] = 1.0
    return h


# --------------------------------------------------------------------------- #
# Local-operator embedding (qutrit Kronecker + axis permutation)              #
# --------------------------------------------------------------------------- #
def embed_operator(op: torch.Tensor, site: int, n: int, *, device=None) -> torch.Tensor:
    """Embed a single-qutrit ``(3, 3)`` operator on ``site`` into the ``n``-qutrit
    register (Kronecker with identity, then permute the qutrit axis into place).

    Qutrit analog of :func:`circuit_sim.embed_operator` (reshapes to ``[3]*(2n)``,
    not ``[2]*(2n)``). Differentiable in ``op``.
    """
    site = int(site)
    n = int(n)
    if op.shape != (QUDIT, QUDIT):
        raise ValueError(f"single-qutrit operator must be (3, 3), got {tuple(op.shape)}")
    if device is None:
        device = op.device
    op = op.to(device).contiguous()
    rest = n - 1
    if rest > 0:
        full = torch.kron(op, torch.eye(QUDIT ** rest, dtype=CDTYPE, device=device))
    else:
        full = op
    # `full` treats qutrit order as: [site, then the rest in ascending order].
    current = [site] + [q for q in range(n) if q != site]
    perm_row = [current.index(q) for q in range(n)]
    perm = perm_row + [n + a for a in perm_row]
    dim = QUDIT ** n
    full = full.reshape([QUDIT] * (2 * n)).permute(*perm).contiguous().reshape(dim, dim)
    return full


def apply_local_op(rho: torch.Tensor, op: torch.Tensor, site: int, n: int) -> torch.Tensor:
    """``rho -> op_site @ rho @ op_site^dag`` by contracting the ``(3, 3)`` ``op`` on the
    site's ket/bra factors ONLY -- without ever materializing the full ``3^n x 3^n``
    embedded operator (which is 5.77 GiB at n=9, and an r-fold stack for channels).

    Mathematically identical to ``embed_operator(op, site, n) @ rho @ embed^dag``; differs
    only by floating-point round-off (a different summation order) -- proven scientifically
    equivalent (<=1e-12) in ``outputs/teacher_prereg/check_subsystem_apply_equiv.py``.
    ~10^4x fewer FLOPs (no ``D^3`` matmul) and no dense operator at n=9. Differentiable in
    ``op``. ``site`` follows the engine convention: qutrit 0 is the most-significant factor.
    """
    site, n = int(site), int(n)
    d = QUDIT ** n
    left, right = QUDIT ** site, QUDIT ** (n - 1 - site)  # factors above/below the site (0 = MSF)
    op = op.contiguous()
    # op on the site factor of the ROW (ket) index:  sum_b op[a,b] rho[l,b,r,c]
    t = torch.einsum("ab,lbrc->larc", op, rho.reshape(left, QUDIT, right, d)).reshape(d, d)
    # op^dag on the site factor of the COLUMN (bra) index:  sum_b t[c,l,b,r] conj(op)[a,b]
    t = torch.einsum("ab,clbr->clar", op.conj(), t.reshape(d, left, QUDIT, right)).reshape(d, d)
    return t


# --------------------------------------------------------------------------- #
# Trit-index helpers (qutrit analog of the (i >> shift) & 1 bit reads)        #
# --------------------------------------------------------------------------- #
def _site_trit(idx: torch.Tensor, site: int, n: int) -> torch.Tensor:
    """Trit value in ``{0, 1, 2}`` of qutrit ``site`` for each basis index in ``idx``
    (qutrit 0 = most-significant factor)."""
    place = QUDIT ** (int(n) - 1 - int(site))
    return (idx // place) % QUDIT


def resolve_readout_bias(b) -> float:
    """Resolve the leaked-readout bias ``b = P(|2> reads "1"-like) in [0, 1]``.

    The engine's readout model is the swept-``b`` 2-outcome POVM (registration
    ``phase1_qutrit_leakage_registration.md`` §2.2): on a stabilizer support the
    per-data-qutrit measurement is ``F1 = |1><1| + b|2><2|``, ``F0 = |0><0| +
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


class QutritDM:
    """Exact ``3**n_data x 3**n_data`` data-register density matrix for d3 XZZX.

    See module docstring for conventions. The engine is generic over channels,
    stabilizers and the leaked-readout map; the code geometry is injected via
    :meth:`set_code`.
    """

    def __init__(self, n_data: int, device: str | torch.device = "cuda", dtype=CDTYPE) -> None:
        self.n = int(n_data)
        if self.n < 1:
            raise ValueError("n_data must be >= 1")
        if dtype != CDTYPE:
            # Precision-first contract: the engine is complex128 only.
            raise ValueError("QutritDM is complex128-only (precision-first)")
        self.device = torch.device(device)
        self.dtype = dtype
        self.dim = QUDIT ** self.n
        # rho lives here; init_logical / a manual set_state must fill it.
        self.rho: torch.Tensor = torch.zeros((self.dim, self.dim), dtype=self.dtype, device=self.device)
        # optional code geometry (set by the harness)
        self._stabilizers: list[dict[int, str]] | None = None
        self._logical_x: dict[int, str] | None = None
        self._logical_z: dict[int, str] | None = None

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
        and its logical-X image for ``m=1`` (logical-X defaults to ``X`` on qutrit 0).
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
            h = qutrit_hadamard(self.device)
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
        """Apply a single-qutrit unitary ``U:(3,3)`` on ``site``: ``rho -> U rho U^dag``.

        Routed through the lean single-pass superoperator :meth:`apply_channel` (a unitary is a
        one-Kraus channel) -- ~3x faster + leaner than the two-einsum ``apply_local_op`` path,
        identical math (``U rho U^dag``). The X-type stabilizer Hadamards (~511/enumeration) ran
        through here, so this is the enumeration's hot path.
        """
        self.apply_channel([U], site)

    def apply_channel(self, kraus, site: int) -> None:
        """Apply a single-qutrit CPTP channel on ``site``: ``rho -> sum_k K_k rho K_k^dag``,
        via the SITE SUPEROPERATOR in ONE contraction (NOT a per-Kraus loop).

        ``S[a,c,b,e] = sum_k K_k[a,b] conj(K_k[c,e])`` (a tiny ``3x3x3x3``) is contracted on
        the site's ket/bra factors of ``rho`` -- so the ``r`` Kraus collapse into a single pass
        with peak ~2x rho, instead of summing ``r`` separate 5.77 GiB terms (the per-Kraus loop
        peaked at 34.7 GiB > the 32 GB card -> host-spill thrash, 44 s/site at n=9). Identical
        math to ``cptp_channel.apply_kraus(rho, stack(embed_operator(k)))`` (proven equivalent in
        check_subsystem_apply_equiv.py).
        """
        d = self.dim
        left, right = QUDIT ** int(site), QUDIT ** (self.n - 1 - int(site))
        ks = torch.stack([torch.as_tensor(k, dtype=self.dtype, device=self.device) for k in kraus]).contiguous()
        sop = torch.einsum("kab,kce->acbe", ks, ks.conj())  # (3,3,3,3) site superoperator
        # rho (d,d) -> (left, b, right, left, e, right); contract S on the site ket(b)/bra(e) axes
        t = torch.einsum("acbe,lbrLeR->larLcR", sop,
                         self.rho.reshape(left, QUDIT, right, left, QUDIT, right)).reshape(d, d)
        self.rho = hermitianize(t)

    def single_qutrit_gate(self, name: str) -> torch.Tensor:
        """A single-qutrit FRAME gate ``(3,3)`` on the computational ``{0,1}`` subspace
        (``|2>`` inert), by stim name: ``X``/``Y``/``Z``/``S``/``S_DAG``/``H``/``I``.

        These are the per-round transversal DATA frame gates the shipped XZZX circuit applies
        (the mid-cycle ``X`` echo + the post-M ``Y``; the P4a interface contract's
        ``SV_GATE_IDS`` alphabet). ``|2>`` is left untouched (the leaked level is inert under
        the computational frame), matching the SV-MC kernel's gate convention bit-for-bit so the
        DM oracle and the SV-MC apply the IDENTICAL per-round gate (Gate-4 validity).
        """
        nm = str(name).upper()
        m = torch.zeros((QUDIT, QUDIT), dtype=self.dtype, device=self.device)
        if nm == "X":
            m[0, 1] = 1.0; m[1, 0] = 1.0; m[2, 2] = 1.0
        elif nm == "Y":
            m[0, 1] = -1.0j; m[1, 0] = 1.0j; m[2, 2] = 1.0
        elif nm == "Z":
            m[0, 0] = 1.0; m[1, 1] = -1.0; m[2, 2] = 1.0
        elif nm == "S":
            m[0, 0] = 1.0; m[1, 1] = 1.0j; m[2, 2] = 1.0
        elif nm == "S_DAG":
            m[0, 0] = 1.0; m[1, 1] = -1.0j; m[2, 2] = 1.0
        elif nm == "H":
            return qutrit_hadamard(self.device)
        elif nm == "I":
            return qutrit_eye(self.device)
        else:
            raise ValueError(f"unsupported single-qutrit frame gate {name!r}")
        return m

    def apply_round_data_gates(self, gates: list[tuple[str, "list[int] | tuple[int, ...]"]]) -> None:
        """Apply a per-round transversal single-qutrit DATA FRAME to ``rho``, IN ORDER.

        ``gates`` is an ordered list of ``(gate_name, sites)`` — for d3 XZZX the per-round DD echo
        ``[("X", [0,..,8]), ("Y", [0,..,8])]`` (the mid-cycle transversal X echo FOLLOWED BY the
        post-M transversal Y; FIX-1). Each entry is applied IN THE GIVEN ORDER as
        ``rho -> (prod_site U_site) rho (prod_site U_site)^dag`` (commuting single-qutrit gates,
        ``|2>`` inert), so passing ``X`` before ``Y`` realizes the physical mid-cycle-then-post-M
        order. This is the DM oracle's counterpart to the SV-MC kernel's per-round gate CSR; the
        certification harness (Gate 4) calls it at the SAME per-round position the host marshals the
        echo into the kernel — i.e. as the PRE-leakage gates of each round (the following-slot
        placement, X then Y; see ``sv_sampler.marshal_schedule``), so the DM oracle and the SV-MC
        implement the IDENTICAL ``leakage -> {X, Y}`` per-round dynamics and Gate 4 stays valid. The
        pair ``X;Y = diag(i,-i,1)`` is the DD echo that refocuses the WG ``|1><->|2>`` leakage
        exchange (the post-M Y suppresses the leaked ``|2>`` population ~10x at R>1; it must be
        present in BOTH engines or Gate 4's |2> trajectory disagrees).

        No-op for an empty ``gates`` list (a frameless / R=1-floor schedule), so existing callers
        are unaffected.
        """
        for name, sites in gates:
            U = self.single_qutrit_gate(name)
            for site in sites:
                self.apply_gate(U, int(site))

    # ----------------------------------------------------------------------- #
    # P4a within-cycle leakage (the circuit-faithful per-cycle model §2/§3)    #
    # ----------------------------------------------------------------------- #
    def apply_within_cycle_premeasure(
        self, streams: dict[int, "list[str] | tuple[str, ...]"], leak_kraus
    ) -> None:
        """Apply the per-qutrit PRE-measurement within-cycle stream of ONE round to ``rho``.

        ``streams`` maps engine register position ``q`` -> that qutrit's ordered interior token
        stream (``H`` / ``X`` / ``LEAK``; the post-M ``Y`` and the ``M`` marker are handled by
        :meth:`apply_within_cycle_postmeasure` and the stabilizer measurement). ``leak_kraus`` is
        the per-CZ-layer leak slice ``exp(L/4)`` (a single-qutrit Kraus list); the host asserts
        ``‖exp(L) − (exp(L/4))⁴‖ < 1e-12`` and ``Σ K†K = I`` before passing it (P4a model §3).

        For each qutrit ``q`` the tokens are replayed IN ORDER on the full ``rho`` (model §2):
        ``H`` -> the qutrit Hadamard (``|2>`` inert), ``X`` -> the mid-cycle X echo, ``LEAK`` ->
        the ``exp(L/4)`` channel (one per CZ layer the qutrit touches — so a 2-CZ qutrit leaks
        ``exp(L·2/4)`` total, a 4-CZ qutrit the full ``exp(L)``). Because single-qutrit ops on
        DISTINCT qutrits commute, applying each qutrit's stream sequentially in its own order is
        identical to the true global interleaving; the relative order ACROSS qutrits is
        immaterial (only within a qutrit). The explicit H's interleaved with the leak slices
        REFOCUS the coherent ``|1><->|2>`` exchange (``H X H = Z``) — the load-bearing fix the
        lumped per-round channel misses (model §4 R2).

        Tokens stop at the ``M`` boundary (only the pre-M part is applied here). Any ``Y`` in the
        stream is post-M and is IGNORED here (applied after the measurement). Unknown tokens
        raise — the stream must be a parsed :class:`WithinCycleStream` token sequence.
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
                    self.apply_gate(qutrit_hadamard(self.device), site)
                elif tok == "X":
                    self.apply_gate(self.single_qutrit_gate("X"), site)
                elif tok == "Y":
                    continue  # post-M frame: applied by apply_within_cycle_postmeasure
                else:
                    raise ValueError(f"within-cycle pre-measure: unknown token {tok!r} at site {site}")

    def apply_within_cycle_postmeasure(
        self, streams: dict[int, "list[str] | tuple[str, ...]"], *, terminal: bool = False
    ) -> None:
        """Apply the per-qutrit POST-measurement within-cycle frame (the transversal ``Y``).

        After the stabilizer measurement, each qutrit's post-M tokens (the ``Y`` for an interior
        round) are applied to ``rho`` (``|2>`` inert; ``H X H = Z`` plus this ``Y`` form the DD
        echo that refocuses the leaked ``|2>``). The TERMINAL round drops the post-M ``Y`` (it
        ends in the terminal data readout — model §1/§8): pass ``terminal=True`` to skip it.

        ``streams`` is the same per-position token map as
        :meth:`apply_within_cycle_premeasure`; only tokens AFTER the ``M`` marker are applied.
        No-op (besides the terminal flag) if a qutrit has no post-M frame.
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
                    self.apply_gate(self.single_qutrit_gate("Y"), site)
                elif tok in ("X", "H", "LEAK"):
                    raise ValueError(
                        f"within-cycle post-measure: unexpected token {tok!r} after M at site {site} "
                        f"(only the transversal Y is expected post-M for d3 XZZX)")

    def run_within_cycle_single_qutrit(
        self, streams: dict[int, "list[str] | tuple[str, ...]"], leak_kraus, site: int,
        init_level: int, R: int, *, with_Y: bool = True,
    ) -> float:
        """The single-isolated-qutrit ``|2>`` population after ``R`` within-cycle rounds (model §5).

        Reproduces the P4a model §5 deliverable target: an isolated data qutrit (``site``)
        starting in ``|init_level>`` evolved through ``R`` interior within-cycle rounds (per-CZ
        ``exp(L/4)`` slices at its CZ layers, the per-qubit H's at their slots, the mid-cycle X,
        and — when ``with_Y`` — the post-M Y on every round, matching the §5 table's uniform-Y
        convention). No stabilizer measurement (the §5 target is the FREE single-qutrit
        trajectory). Returns ``rho[2,2]`` (real).

        This is a small ``n=1`` engine instance built locally (3x3 channel algebra on the GPU),
        independent of the 9-qutrit ``rho`` — the calibration/physics control. ``streams[site]``
        is the qutrit's interior token stream; only that qutrit's tokens drive the evolution.
        """
        toks = list(streams[int(site)])
        eng = QutritDM(1, device=self.device)
        rho0 = torch.zeros((QUDIT, QUDIT), dtype=self.dtype, device=self.device)
        rho0[int(init_level), int(init_level)] = 1.0
        eng.set_state(rho0)
        kraus = list(leak_kraus)
        Xg = eng.single_qutrit_gate("X")
        Yg = eng.single_qutrit_gate("Y")
        Hg = qutrit_hadamard(self.device)
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
                    raise ValueError(f"within-cycle single-qutrit: unknown token {tok!r}")
        return float(torch.diagonal(eng.rho).real[2])

    # ----------------------------------------------------------------------- #
    # Stabilizer parity projection (the qutrit analog of project_parity)      #
    # ----------------------------------------------------------------------- #
    def _povm_diag_weight(self, paulis: dict[int, str], outcome: int, b: float, arm: str = "A") -> torch.Tensor:
        """Diagonal of the stabilizer syndrome-bit POVM ``E_s`` over basis indices.

        The syndrome-bit POVM is ``E_s = sum_{c: XOR_q c_q = s} prod_q F_{c_q}^{(q)}``,
        the sum over per-qubit bit assignments whose XOR equals the syndrome ``s``, of
        the tensor product of single-qutrit effects ``F_{c}`` (registration §2.2). Each
        single-qutrit effect is DIAGONAL in the (already Z-rotated, so all-Z) basis:

          ``F1 = |1><1| + b|2><2|``  ->  diag weight for bit 1 of trit ``t``:
              ``w1(t) = [t==1] + b*[t==2]``   (1 if t=1, b if t=2, 0 if t=0)
          ``F0 = |0><0| + (1-b)|2><2|``  ->  diag weight for bit 0 of trit ``t``:
              ``w0(t) = [t==0] + (1-b)*[t==2]``  (1 if t=0, 1-b if t=2, 0 if t=1)

        so ``E_s`` is diagonal too. Per basis index ``i`` with trit ``t_q`` on each
        active site ``q``, ``w0(t_q) + w1(t_q) = 1`` for every ``t_q`` (the POVM
        completeness ``F0 + F1 = I`` per site), so the XOR-coefficient extraction
        collapses to

          ``E_s[i,i] = 1/2 * (1 + (-1)^s * prod_q d_q)`` ,   ``d_q = w0(t_q) - w1(t_q)``

        with the per-qutrit **parity weight** ``d_q(0) = +1``, ``d_q(1) = -1`` in EVERY
        arm; the **arm** (P4a interface contract §4) sets ``d_q(2)``:

          arm A / C : ``d_q(2) = 1 - 2b``  (the swept-``b`` leaked classifier; Phase-1)
          arm B1    : ``d_q(2) = +1``      (``|2>`` ≡ ``|0>``: leaked-DECOUPLED model)
          arm B2    : ``d_q(2) = -1``      (``|2>`` ≡ ``|1>``: coherence UPPER bound)

        ``b`` enters ONLY through ``d_q(2)`` for A/C; for B1/B2 the syndrome is
        ``b``-independent (a different leaked coupling). Arms A and B2 coincide at
        ``b = 1`` (both give ``d_q(2) = -1``), recovering the engine's original hard-bit
        parity projector ``[parity == s]`` (leaked reads bit 1) — BIT-FOR-BIT.

        Returns the real, nonnegative diagonal vector ``E_s[i,i] in [0, 1]`` (length
        ``dim``). NOTE: every active site is read as a Z parity here; X-type supports are
        Hadamard-rotated into the Z basis by :meth:`project_stabilizer` BEFORE this is
        called (``|2>`` untouched by H, so its leaked row is basis-independent).
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
        # d_q = +1 (t=0), -1 (t=1), d2 (t=2); product over the active sites.
        prod = torch.ones(self.dim, dtype=RDTYPE, device=self.device)
        for site in paulis:
            t = _site_trit(idx, site, self.n)
            d = torch.where(
                t == 0,
                torch.ones(self.dim, dtype=RDTYPE, device=self.device),
                torch.where(
                    t == 1,
                    torch.full((self.dim,), -1.0, dtype=RDTYPE, device=self.device),
                    torch.full((self.dim,), d2, dtype=RDTYPE, device=self.device),
                ),
            )
            prod = prod * d
        sign = 1.0 if (int(outcome) & 1) == 0 else -1.0
        return 0.5 * (1.0 + sign * prod)

    def _leak_flag_dephase(self, paulis: dict[int, str]) -> None:
        """Arm-C leak-flag projection (DM-faithful): dephase ``|2>`` vs ``{0,1}`` on the
        support, preserving the ``{0,1}`` computational coherence (interface contract §4).

        The SV-MC realizes Arm C by SAMPLING one leakage pattern ``L ⊆ supp`` (which
        support qutrits are ``|2>``) with ``p(L) = sum_{c consistent with L} |psi[c]|^2``
        and projecting ``psi`` onto it. Averaged over trajectories that sampling IS the
        dephasing channel that kills coherence between basis states with DIFFERENT leak
        flags on the support and leaves everything else untouched. The DM oracle (which
        does not sample — it carries the full ``rho``) applies that channel directly:

          ``rho[i, j] -> rho[i, j]``   if  ``f_q(t_q^i) == f_q(t_q^j)``  for all ``q in supp``
          ``rho[i, j] -> 0``           otherwise,           ``f_q(t) = [t == 2] in {0, 1}``.

        This is diagonal-population preserving (``i == j`` always survives), so the
        subsequent diagonal ``E_s`` marginal ``P(s)`` is IDENTICAL to Arm A (Gate-4 A<->C
        R=1 agreement); but the ``|2>``-vs-``{0,1}`` coherence (hence ``C_L`` and the
        temporal memory) is maximally removed on the support — the same-``E_s``,
        maximal-leakage-disturbance comparator. ``|0>``<->``|1>`` coherence (same flag
        ``f = 0`` on both sides) is preserved. Applied to ``rho`` IN PLACE; basis-aligned,
        so it is called on the Z-rotated state inside :meth:`project_stabilizer`
        (``f_q`` is Hadamard-invariant: H does not touch ``|2>``).
        """
        idx = torch.arange(self.dim, device=self.device)
        flag = torch.zeros(self.dim, dtype=torch.long, device=self.device)
        # encode the per-support leak-flag vector as an integer key (one bit per support site)
        for bit, site in enumerate(paulis):
            t = _site_trit(idx, site, self.n)
            flag = flag | ((t == 2).to(torch.long) << bit)
        # zero rho[i,j] where flag[i] != flag[j] (dephasing across leak sectors), IN-PLACE:
        # mask_off is a dim*dim bool (no dim*dim complex temp); masked_fill_ keeps the
        # diagonal (flag[i]==flag[i]) so the syndrome marginal is unchanged. The oracle
        # runs at the small Gate-4 scale (n<=5), where the bool mask is trivial.
        mask_off = flag[:, None] != flag[None, :]
        self.rho = self.rho.masked_fill(mask_off, 0)

    def project_stabilizer(self, paulis: dict[int, str], outcome: int, b=None, arm: str = "A",
                           *, diagonal_z: bool = False) -> float:
        """Apply the ``outcome``-effect of the stabilizer syndrome-bit POVM to ``rho``
        and return the branch probability ``Tr[E_outcome rho]``; leaves ``rho``
        UN-normalized (post-measurement, unnormalized).

        ``paulis: dict[data_site -> 'X'|'Z']`` is the stabilizer support (XZZX). X-type
        sites are conjugated into the Z basis by Hadamard (``H X H = Z`` on ``{0,1}``;
        ``|2>`` untouched), the diagonal syndrome-bit POVM ``E_outcome`` (see
        :meth:`_povm_diag_weight`) is applied as a measurement update, then the X-type
        sites are rotated back so ``rho`` stays in the computational basis for the next
        projection.

        PURE DIAGONAL-Z mode (``diagonal_z=True``). A general capability: read every support as a
        pure Z-parity with NO X-support Hadamard (for a state ALREADY in the Z measurement basis).
        NOTE — this is NOT used by the P4a within-cycle path: the spec text (model §4 R3) claimed
        the explicit within-cycle H's leave the X-supports Z-rotated at the M (so drop
        ``stab_supp_isx``), but that contradicts §4 R1 (each qutrit has 2 H's per round → even →
        net identity → the qutrit returns to the COMPUTATIONAL basis at the M). Verified on the d3
        codestate (``p4a_host_wc_marshal.py`` §3): with pure-Z the X-stabilizers read 0 (wrong
        syndrome); the within-cycle measurement KEEPS ``stab_supp_isx`` (``diagonal_z=False``).
        The flag remains available for genuinely pre-rotated states.

        Leaked readout — the swept-``b`` POVM (registration §2.2). ``b = P(|2> reads
        "1"-like) in [0, 1]`` is the biased-coin readout of the leaked level; the per-
        qubit effects are ``F1 = |1><1| + b|2><2|``, ``F0 = |0><0| + (1-b)|2><2|`` with
        ``F0 + F1 = I``, handled correctly against the FULL correlated ``rho`` (a trace
        against ``rho``, NOT a per-qubit product of marginals). ``b`` may also be the
        legacy hard-bit callable (resolved to ``b in {0,1}`` by :func:`resolve_readout_bias`).

        Measurement INSTRUMENT ARM (P4a interface contract §4). ``arm`` selects the
        registered measurement-instrument arm (the load-bearing R>1 axis; the R=1 floor
        is arm-A == arm-C and unchanged for B-arms only by their different ``E_s``):

          ``"A"`` (DEFAULT) — Lüders ``sqrt(E_s)`` with ``d_q(2) = 1-2b`` (the Phase-1
            instrument, BIT-IDENTICAL to all existing callers that omit ``arm``);
          ``"C"`` — same ``E_s`` as A (same ``P(s)``), but with a leak-flag projection
            (:meth:`_leak_flag_dephase`) applied FIRST → maximal leakage-sector
            disturbance (``C_L -> 0``); the same-``E_s`` disturbance comparator;
          ``"B1"`` — ``d_q(2) = +1`` (``|2>`` ≡ ``|0>``): leaked-decoupled, different ``E_s``;
          ``"B2"`` — ``d_q(2) = -1`` (``|2>`` ≡ ``|1>``): coherence upper bound, different ``E_s``.

        The DM ``project_stabilizer`` is the exact oracle the SV-MC engine is certified
        against (Gate 4), so the arm semantics MUST match the SV-MC arm exactly.

        Measurement update. ``E_outcome`` is diagonal with entries ``e_i = E_s[i,i] in
        [0,1]``; the (unnormalized) post-measurement state is ``sqrt(E_s) rho sqrt(E_s)``
        i.e. ``rho[i,j] -> sqrt(e_i) sqrt(e_j) rho[i,j]`` (a diagonal Kraus measurement,
        the POVM generalization of the projector mask). Its trace is ``sum_i e_i
        rho[i,i] = Tr[E_s rho] = P(s)``. The map is intentionally unnormalized: the
        running trace of a branch equals the joint probability of its outcomes so far,
        which is exactly what makes the sequential enumeration in
        :meth:`syndrome_distribution` exact. Because ``F0 + F1 = I`` (so ``E_0 + E_1 =
        I`` and ``e_i^{(0)} + e_i^{(1)} = 1``), the two outcome branches' traces sum back
        to the parent trace. For arm A at ``b = 1`` (and arm B2) ``E_s`` is a 0/1
        projector and the update is the exact masked outer product the engine used
        before — BIT-FOR-BIT.
        """
        bias = resolve_readout_bias(b)
        # PURE diagonal-Z mode (within-cycle, model §4 R3): the explicit circuit H's already
        # rotated the X-supports to Z, so DROP the support Hadamard here (no double-H).
        x_sites = [] if diagonal_z else [s for s, p in paulis.items() if str(p).upper() == "X"]
        # rotate X-type supports into the Z basis
        for s in x_sites:
            self.apply_gate(qutrit_hadamard(self.device), s)

        # Arm C: leak-flag dephasing BEFORE the diagonal E_s (§4) — kills |2>-vs-{0,1}
        # coherence on the support, leaves the diagonal (so P(s) == arm A) untouched.
        if str(arm).upper() == "C":
            self._leak_flag_dephase(paulis)

        e_diag = self._povm_diag_weight(paulis, outcome, bias, arm)  # E_s[i,i] in [0,1]
        sqrt_e = torch.sqrt(torch.clamp(e_diag, min=0.0)).to(self.dtype)
        # rho[i,j] -> sqrt(e_i) sqrt(e_j) rho[i,j]  (diagonal POVM Kraus update), IN-PLACE:
        # two row/col rescalings, NOT an outer-product (which would be a 5.77 GiB temp per call).
        self.rho.mul_(sqrt_e[:, None])
        self.rho.mul_(sqrt_e[None, :].conj())
        prob = torch.diagonal(self.rho).real.sum()

        # rotate the X-type supports back (Hadamard is its own inverse on {0,1})
        for s in x_sites:
            self.apply_gate(qutrit_hadamard(self.device), s)
        return float(prob)

    def syndrome_distribution(self, stabs: list[dict[int, str]], b=None, arm: str = "A",
                              *, diagonal_z: bool = False) -> dict[tuple, float]:
        """EXACT ``P(s)`` over all ``2**len(stabs)`` joint syndromes by depth-first
        projection enumeration (NO Monte-Carlo).

        ``diagonal_z`` (a general capability) is forwarded to :meth:`project_stabilizer`: when
        ``True``, every stabilizer is read as a pure diagonal Z-parity (no support Hadamard), for
        a state ALREADY in the Z measurement basis. NOT used by the P4a within-cycle path — the
        within-cycle measurement KEEPS ``stab_supp_isx`` (the in-stream H's net to identity, so
        the X-supports are NOT Z-rotated at the M; the spec text's §4 R3 pure-Z is a slip — see
        :meth:`project_stabilizer`).

        ``stabs`` is the ordered list of stabilizer ``paulis`` dicts; ``b`` is the
        swept leaked-readout bias ``P(|2> reads "1"-like) in [0,1]`` (registration §2.2;
        the legacy hard-bit callable is also accepted, resolved to ``b in {0,1}``).
        ``arm in {A, C, B1, B2}`` selects the measurement-instrument arm (P4a interface
        contract §4; default ``"A"`` keeps every existing caller bit-identical). This is
        the SAME enumeration the SV-MC samples from, so an ``arm``-matched DM oracle is
        the Gate-4 ground truth (``TV(SV-MC, DM) ~ C/sqrt(N)``). Arms A and C give an
        identical ``P(s)`` (C only adds an off-diagonal dephasing) — they differ for the
        SV-MC only through the post-measurement state at R>1; B1/B2 give a different
        ``P(s)`` already at R=1.

        Returns a dict keyed by the syndrome tuple ``s in {0,1}**len(stabs)`` with the
        exact probability of each cell; the values sum to ``Tr(rho)`` (== 1 for a
        normalized codestate). Implemented as a recursive descent that snapshots ``rho``
        before each binary branch so both outcomes are enumerated from the same parent
        state — the exact integral over Kraus branches, by the density-matrix identity.
        The biased-coin ``|2>`` readout keeps the enumeration exact: ``E_0 + E_1 = I``,
        so the two children's traces sum to the parent's (no probability is lost).
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
                # prune exact-zero branches (no probability) but keep them in the key
                # space implicitly: a zero-prob cell contributes 0 to the sum.
                descend(child, k + 1, prefix + (outcome,))

        descend(base, 0, ())
        self.rho = base  # restore the parent state (projection is enumeration-only)
        return dist

    # ----------------------------------------------------------------------- #
    # Logical readout                                                         #
    # ----------------------------------------------------------------------- #
    def logical_distribution(self) -> tuple[float, float]:
        """Final logical readout ``(p0, p1)``.

        With a logical-Z operator set: ``p_m = Tr[ (I + (-1)**m Z_L)/2 . rho ]`` read
        on the computational subspace (the eigenvalue-(-1)**m projector of the logical
        operator). Without a code geometry: the parity of the logical-X-image support
        (defaults to qutrit 0 in the Z basis), so the trivial codestate pair reads out
        ``(1, 0)`` / ``(0, 1)``. Leaked population (trit ``= 2`` on the logical support)
        is split evenly — a neutral default; the harness can override via ``set_code``.
        """
        # Determine which operator defines the logical readout parity. For XZZX the
        # protected observable is the logical operator from OBSERVABLE_INCLUDE; the
        # harness passes it as logical_z (Z-basis) or logical_x (X-basis).
        if self._logical_z is not None:
            op = self._logical_z
        elif self._logical_x is not None:
            op = self._logical_x
        else:
            op = {0: "X"}  # trivial: read qutrit 0

        rho = self.rho
        tr = torch.diagonal(rho).real.sum()
        if tr.real <= NUMERICAL_ZERO:
            return 0.0, 0.0
        rho = rho / tr.to(self.dtype)

        # rotate X-type logical support into the Z basis to read its parity
        x_sites = [s for s, p in op.items() if str(p).upper() == "X"]
        saved = self.rho
        self.rho = rho.clone()
        for s in x_sites:
            self.apply_gate(qutrit_hadamard(self.device), s)
        diag = torch.diagonal(self.rho).real
        self.rho = saved  # restore (read-only operation)

        idx = torch.arange(self.dim, device=self.device)
        parity = torch.zeros(self.dim, dtype=torch.long, device=self.device)
        leaked_weight0 = torch.zeros(self.dim, dtype=RDTYPE, device=self.device)
        for site in op:
            t = _site_trit(idx, site, self.n)
            # computational bit = t for t in {0,1}; leaked (t==2) split evenly
            bit = torch.where(t == 2, torch.zeros_like(t), t)
            parity = parity ^ (bit & 1)
            leaked_weight0 = leaked_weight0 + (t == 2).to(RDTYPE)
        leaked = leaked_weight0 > 0
        p0 = float(diag[(parity == 0) & (~leaked)].sum() + 0.5 * diag[leaked].sum())
        p1 = float(diag[(parity == 1) & (~leaked)].sum() + 0.5 * diag[leaked].sum())
        return p0, p1

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
    ) -> dict:
        r"""EXACT multi-round (syndrome-history, logical) record oracle on the d3 qutrit DM.

        The implementation-independent KNOWN-TRUTH oracle the scalable MCWF carrier
        (``forward/scalable`` SV-MC / MPS) is validated against (the Axis-A teacher
        pre-registration ``docs/twin_validation/axisA_teacher_prereg.md`` §7.1/§7.2). It
        evolves the codestate ``rho`` (already set by :meth:`init_logical` / :meth:`set_state`)
        through ``R`` circuit-faithful rounds, applying per round the caller-supplied
        MECHANISM and enumerating the stabilizer syndromes by the EXACT density-matrix
        Lüders-instrument branch sum (the same recursion as :meth:`syndrome_distribution`,
        carried ACROSS rounds with the post-measurement, unnormalized branch state). It is
        mechanism-agnostic: the teacher's actual per-round op-schedule (rx over-rotation →
        per-qutrit H/X/LEAK within-cycle stream, then the post-M Y echo) is injected through
        the callbacks, so the oracle's record matches the teacher's emitted surface bit-for-bit
        (the seam, below) without this engine importing any mechanism.

        Per round ``r`` (0-indexed):
          1. ``round_pre(self, r)`` — apply that round's PRE-measurement mechanism on the
             CURRENT (possibly post-measurement, unnormalized) branch state IN PLACE
             (gates via :meth:`apply_gate`, single-qutrit channels via :meth:`apply_channel`).
             This is the caller's faithful within-cycle stream (model §2). It MUST mutate
             ``self.rho`` and return ``None``.
          2. enumerate the ``len(stabs)`` stabilizers' joint syndrome via the existing
             :meth:`project_stabilizer` branch logic (the diagonal ``E_s`` Lüders update,
             ``E_0 + E_1 = I`` so the two children's traces sum to the parent's — exact, no
             probability lost), keeping each child's UN-normalized post-measurement state for
             the next round.
          3. ``round_post(self, r)`` — the POST-measurement frame (the transversal Y echo for
             an interior round; DROPPED on the terminal round ``r == R-1``). ``None`` (default)
             applies nothing. Applied on each surviving syndrome branch (so the next round's
             mechanism sees the post-M state, as the carrier does).
        After the final round the logical readout :meth:`logical_distribution` splits each
        terminal branch into ``(p0, p1)``.

        SEAM / record convention (matches ``forward/scalable/seam.py:teacher_shots_to_events``
        + the kernel emission). The per-round raw syndrome bits ``s[r, j]`` are the joint-parity
        POVM outcomes (this method's branch labels), round-major then ``stabs``-order. The
        emitted DETECTORS are folded ``det[0, j] = s[0, j]`` (first round raw),
        ``det[r, j] = s[r, j] XOR s[r-1, j]`` for ``r >= 1`` (interior round-to-round XOR). The
        observable is the single logical flip ``parity(terminal logical readout) XOR m`` — and
        because the caller prepares ``|m>_L`` (so the readout splits to ``(p0, p1)`` about the
        ``(-1)^m`` logical sector) and the post-M Y echoes flip the parity by
        ``(R-1)*|logical_supp| mod 2``, the oracle reports the readout split directly; the
        caller maps it to the flip convention (the teacher's ``run_teacher``).

        ┌─ THE BOUND (declared exactly as §7.2; memory, prevent-toy honesty) ────────────────┐
        │  The full 9-data-qutrit DM is ``3^9 x 3^9 x 16 B = 6.2 GB / copy``. The exact record │
        │  enumeration recurses to depth ``len(stabs)*R`` with a state COPY per branch level.  │
        │  Therefore:                                                                          │
        │   * ``return_joint=True`` path (R == 1): the FULL exact joint ``P(s, f)`` over all    │
        │     ``2^len(stabs)`` syndromes x 2 logical IS returned (the gold-standard GT). At the │
        │     full 9q register the depth-8 enumeration peaks at ~``8 x 6.2 = 50 GB`` of live    │
        │     DM copies; on a 32 GB card this is delivered at a FEASIBLE sub-register (and the  │
        │     9q R=1 surface is cross-checked against the carrier on the moments) — the script  │
        │     measures and reports the exact feasible register, never silently truncates.      │
        │   * R >= 2: the full ``2^(8R)`` joint is memory-infeasible (R=2 full joint ≈ 100 GB;  │
        │     and the depth-``8R`` copy stack alone is ``16 x 6.2 = 100 GB`` at 9q). So at      │
        │     R >= 2 this returns the exact per-detector MARGINALS + round-to-round (per-stab   │
        │     consecutive-round) detector CORRELATIONS + same-round cross-detector (SPATIAL)    │
        │     correlations — the very moments an iid-Pauli foil cannot match — accumulated over │
        │     the pruned branch tree, NOT the full joint. The carrier (a ``3^9`` state vector ≈ │
        │     0.3 MB) is the scalable sampler certified against exactly these moments.          │
        │  ``prune`` (default ``NUMERICAL_ZERO = 1e-12``) drops branches whose running trace    │
        │  (joint probability so far) is below it; the dropped probability mass is RETURNED in  │
        │  ``dropped_mass`` so the simplification is bounded, not silent. UNBOUNDED ⇒ STOP.     │
        └────────────────────────────────────────────────────────────────────────────────────┘

        Parameters
        ----------
        stabs : list of stabilizer ``paulis`` dicts (``{site -> 'X'|'Z'}``), the per-round
            stabilizer set (same every round — the d3 XZZX geometry).
        round_pre : callable ``(eng, r) -> None`` applying round ``r``'s PRE-measure mechanism
            in place on ``eng.rho``.
        round_post : callable ``(eng, r) -> None`` or ``None``; the POST-measure frame for
            interior rounds. The oracle calls it only for ``r < R-1`` (terminal round drops it),
            so the caller need not branch on ``r`` for the Y-drop. ``None`` ⇒ no post-M frame.
        R : number of rounds (``>= 1``).
        b, arm, diagonal_z : forwarded to :meth:`project_stabilizer` (the swept leaked-readout
            bias, the measurement-instrument arm, the pure-Z mode) — the SAME measurement
            semantics the carrier samples, so the oracle is the Gate-4 ground truth.
        prune : branch trace floor (see the bound). ``0.0`` disables pruning (exact, but no
            zero-branch shortcut).

        Returns
        -------
        For R == 1 (``kind == "full_joint"``)::

            {"kind": "full_joint", "R": 1, "n_stab": len(stabs),
             "joint": {(s_tuple, f): prob},            # 2^n_stab syndromes x f in {0,1}
             "syndrome": {s_tuple: P(s)},              # logical-marginal P(s)
             "logical": (P(f=0), P(f=1)),
             "detectors": {s_tuple: P(det)},           # R=1 det == raw s (identity fold)
             "total_mass": sum of joint, "dropped_mass": pruned probability}

        For R >= 2 (``kind == "moments"``)::

            {"kind": "moments", "R": R, "n_stab": len(stabs),
             "det_marg": ndarray[R*n_stab],            # E[det_{r,j}]
             "rr_corr": ndarray[R-1, n_stab],          # connected corr(det_{r,j}, det_{r+1,j})
             "spatial_corr": ndarray[R, n_stab, n_stab],  # same-round connected cov, normalized
             "flip_rate": P(logical flip == 1 under the folded readout),
             "total_mass": traversed probability, "dropped_mass": pruned probability}

        Both keep the existing ``arm``/``b``/``diagonal_z`` semantics so the moments line up
        with the carrier's emission (Gate-4 logic, two independent implementations).
        """
        if R < 1:
            raise ValueError(f"R must be >= 1 (got {R})")
        n_stab = len(stabs)
        base = self.rho.clone()
        prune = float(prune)

        # accumulators -----------------------------------------------------------------
        # Over the pruned branch tree we accumulate the first + pairwise SECOND moments of the
        # emitted DETECTOR bits ``det[r,j]`` directly (NOT the raw syndrome bits): each terminal
        # leaf is a SINGLE deterministic point in detector space (det is a fixed GF(2)-linear
        # fold of that leaf's raw syndrome history — det[0,j]=s[0,j], det[r,j]=s[r,j]^s[r-1,j]),
        # so accumulating ``path_p * det`` and ``path_p * outer(det, det)`` gives the EXACT
        # detector marginals E[det] and the EXACT pairwise detector second moments E[det det]
        # over the full distribution — with NO higher-moment problem and NO full joint stored
        # (the moments are weighted sums over leaves, accumulated as we go; §7.2). The connected
        # detector correlation corr(det_a, det_b) = (E[det_a det_b] - E[det_a]E[det_b]) / sqrt(
        # Var det_a Var det_b) is then exact; it is IDENTICALLY ZERO for any independent-bit-flip
        # foil (which factorizes across (round, stab)), so a nonzero value is exactly the
        # temporal/spatial structure the iid model misses.
        tot_bits = R * n_stab

        def _fold_detectors(svec) -> torch.Tensor:
            """The emitted detector vector (length tot_bits, round-major) for one leaf's raw
            syndrome history svec: det[0,j]=s[0,j]; det[r,j]=s[r,j] XOR s[r-1,j] (the seam fold,
            matching ``forward/scalable/seam.py:teacher_shots_to_events``)."""
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
            """A terminal branch: record its syndrome history svec (length tot_bits, the raw
            s[r,j] round-major) with un-normalized leaf state rho_leaf (trace == path_p), into
            the detector moment accumulators and (R==1) the full joint."""
            total_mass[0] += path_p
            # logical readout split on the (terminal) leaf state. logical_distribution
            # internally normalizes by Tr, returning (p0, p1) with p0+p1≈1; the JOINT readout
            # mass is path_p * (p0, p1).
            self.rho = rho_leaf
            p0, p1 = self.logical_distribution()
            # contribution to E[flip==1]: path_p * p1 (flip == the logical readout bit here;
            # the caller folds in m + the Y-echo offset — a deterministic relabel that does not
            # change the RATE of flips, so flip_rate is reported on the readout bit directly).
            flip_sum[0] += path_p * p1
            dv = _fold_detectors(svec)
            sum1.add_(path_p * dv)
            sum2.add_(path_p * torch.outer(dv, dv))
            if R == 1:
                key = tuple(int(x) for x in svec)
                full_joint[(key, 0)] = full_joint.get((key, 0), 0.0) + path_p * p0
                full_joint[(key, 1)] = full_joint.get((key, 1), 0.0) + path_p * p1

        def _measure_round(rho_in: torch.Tensor, r: int, svec: list[int], path_p: float) -> None:
            """Enumerate round r's n_stab-stabilizer syndrome on rho_in (the post-round_pre
            state), recursing into the next round / leaf. Depth-first with eager release so
            only O(n_stab) live DM copies exist per active path (the §7.2 copy bound). The
            per-round raw bit s[r,k]=outcome is written into the shared svec slot
            ``r*n_stab + k`` on descent and restored on backtrack."""

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
            return {
                "kind": "full_joint", "R": 1, "n_stab": n_stab,
                "joint": full_joint,
                "syndrome": syndrome,
                "logical": (p0, p1),
                "detectors": dict(syndrome),  # R=1: detector == raw syndrome (identity fold)
                "total_mass": float(total_mass[0]),
                "dropped_mass": float(dropped_mass[0]),
            }

        # R >= 2: the DETECTOR moments are exact from the accumulated detector first/second
        # moments (each leaf is a single deterministic detector point — see the accumulator note;
        # NO higher-moment problem, NO full joint stored).
        tm = float(total_mass[0])
        if tm <= NUMERICAL_ZERO:
            raise RuntimeError("record_oracle: all branch mass pruned (no realized record)")
        e1 = (sum1 / tm).reshape(R, n_stab)                 # E[det_{r,j}]
        e2 = (sum2 / tm).reshape(R, n_stab, R, n_stab)      # E[det_{r,j} det_{r',j'}]
        det_marg = e1.clone()                               # exact detector marginals

        def _conn_corr(r, j, rp, jp):
            """Exact connected (Pearson) correlation of two DETECTOR bits. For {0,1} bits the
            variance is E[d] - E[d]^2; IDENTICALLY ZERO for an independent-bit-flip foil."""
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

        return {
            "kind": "moments", "R": R, "n_stab": n_stab,
            "det_marg": det_marg.reshape(R * n_stab).detach().cpu().numpy(),
            "rr_corr": rr_corr.detach().cpu().numpy(),
            "spatial_corr": spatial_corr.detach().cpu().numpy(),
            "flip_rate": float(flip_sum[0] / tm),
            "total_mass": tm,
            "dropped_mass": float(dropped_mass[0]),
        }

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
        full = embed_operator(op.to(self.dtype), site, self.n, device=self.device)
        return full @ psi

    def _single_qutrit_pauli(self, kind: str) -> torch.Tensor:
        """``X`` or ``Z`` on the computational ``{0,1}`` subspace (identity on ``|2>``)."""
        kind = str(kind).upper()
        m = torch.zeros((QUDIT, QUDIT), dtype=self.dtype, device=self.device)
        if kind == "X":
            m[0, 1] = 1.0
            m[1, 0] = 1.0
            m[2, 2] = 1.0
        elif kind == "Z":
            m[0, 0] = 1.0
            m[1, 1] = -1.0
            m[2, 2] = 1.0
        elif kind == "I":
            m = qutrit_eye(self.device)
        else:
            raise ValueError(f"unsupported single-qutrit Pauli {kind!r}")
        return m

    def _apply_logical_vector(self, psi: torch.Tensor, op: dict[int, str]) -> torch.Tensor:
        for site, kind in op.items():
            psi = self._apply_op_vector(psi, self._single_qutrit_pauli(kind), site)
        return psi

    def _project_operator_vector(self, psi: torch.Tensor, op: dict[int, str], eigenvalue: int) -> torch.Tensor:
        """Project ``psi`` onto the ``eigenvalue``-eigenspace of the (multi-site,
        commuting-Pauli) operator ``op``: ``(I + eigenvalue * O)/2 |psi>``."""
        op_psi = self._apply_logical_vector(psi.clone(), op)
        return 0.5 * (psi + float(eigenvalue) * op_psi)
