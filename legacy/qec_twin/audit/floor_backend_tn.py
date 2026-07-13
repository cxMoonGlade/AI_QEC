from __future__ import annotations

"""quimb LPDO Bayes-floor backend (``TNPathEvaluator``) — the SCALABLE floor carrier (ADR 0010,
task 8d): the locally-purified-MPDO analog of the dense ``DMPathEvaluator`` oracle.

WHAT THIS IS. ``DMPathEvaluator`` (``audit/floor_backend.py``) carries the syndrome-conditioned
state as a dense ``3^n × 3^n`` density matrix — exact, but d3 feasibility-only (3^9 DM = 5.77 GiB;
d5 DM ≈ 10^23 GB, dead). ``TNPathEvaluator`` carries the SAME conditional state as a **locally
purified density operator (LPDO)** ``ρ = X X†`` — an area-law tensor network whose bond ``χ``
stays small and constant in ``d`` (ADR 0010 §Decision-2). It implements the SAME six
``PathJointEvaluator`` seams (``audit/floor_backend.py``), so it plugs into ``audit/bayes_floor``
as ``evaluator=TNPathEvaluator(chi=...)`` WITHOUT touching the floor logic, and at full ``χ`` it
matches the DM oracle bit-for-bit (the C8 anchor; rung-2 certification is task 8e).

THE #1 ARCHITECTURE TRAP (ADR 0010 Decision-2 / constraint C2). The Bayes floor reads
``P(s,f) = tr(Π_f ρ_s)`` from the syndrome-CONDITIONED MIXED state ``ρ_s``. A single quantum
trajectory (the 8c MCWF forward) samples ``P(s)`` — NOT ``P(s,f)`` — so the floor MUST carry the
mixed state. We carry it as an LPDO, where POSITIVITY IS STRUCTURAL: ``ρ = X X† ⪰ 0`` for ANY
``X``, truncated or not. **A plain-MPO-ρ truncation breaks positivity → ``P(s,f) < 0`` →
corrupted floor** (the silent toy-generator C2 forbids). The LPDO never produces a negative
sector trace.

THE LPDO REPRESENTATION (the load-bearing choice; the Darmawan–Poulin construction). ``X`` is a
chain of per-site tensors, each carrying a PHYSICAL (ket) leg ``p{k}`` (``phys_dim=3``), an open
PURIFICATION (Kraus/ancilla) leg ``a{k}``, and spatial bonds ``b{k}``; ``ρ = X X†`` ties every
purification leg ``a{k}`` and the spatial bonds, leaving the physical ket/bra open. The maps:

  * a single-qutrit **CPTP channel** (the WG leakage Kraus slice) attaches the rank-``r`` Kraus
    index to ``p{site}``, FUSES it into that site's purification leg ``a{site}`` (the mixedness
    grows), then re-splits against the neighbour to bound the spatial bond at ``max_bond=χ`` —
    ``X`` stays a valid LPDO, ``ρ`` PSD (C1 + C2);
  * the **√E_s syndrome projector** is a SINGLE Kraus operator, so it acts on the KET only:
    ``ρ_s = (√E_s X)(√E_s X)†``. ``E_s`` is diagonal in the (X-supports-Hadamard-rotated) trit
    basis; ``√E_s`` does not factorize across the support, so it is built as the EXACT dense
    diagonal ``√E_s`` over the ``3^w`` support (``w ≤ 4`` for d3) and applied as one multi-site
    ket gate, re-compressing the spatial bonds at ``χ`` (C2 preserved — ket-only);
  * the per-round transversal **X/Y DD echoes** (C5) + the per-CZ leak slices are replayed from
    ``prob.streams`` / the post-M Y EXACTLY as the DM backend does (same marshalling — no dropped
    echo; the FAITHFULNESS ledger #1 pit).

The reads are SCALABLE TN contractions of ``ρ = X X†`` (no dense ``3^n`` ρ): ``path_trace`` is
``⟨X|X⟩``; ``logical_sector_traces`` uses ``P0 = ½(A + D)``, ``P1 = ½(A − D)`` with ``A = tr ρ``
and ``D = tr(∏_{log} Z̃ · ρ)``, ``Z̃ = diag(1, −1, 0)`` (the leaked-split-evenly logical cancels
in the difference, sums in the trace — derived + validated vs the DM in
``outputs/teacher_prereg/p7d_lpdo_reads_proto.py``); branch sampling reads
``tr(E_s ρ) = ½(A + (−1)^s tr(∏_q D_q ρ))``, ``D_q = diag(1, −1, d₂)``.

Both the spatial bond AND the purification leg are compressed after each op (an SVD re-split with
a tiny ``cutoff`` drops numerically-zero Schmidt values, so the bonds self-shrink to their TRUE
rank — without this the purification grows ×Kraus-rank each leak and the network balloons). The
hard ``max_bond=χ`` is the genuine truncating cap.

TRUNCATION ACCOUNTING (ADR 0010 Design-A; TWO ledgers, never merged). Each truncating op records
its discarded Schmidt weight ``ε_cut = Σ_{i>χ} σ_i²`` into :class:`TnTruncationLedger` — the
STATE-fidelity book, class **(a)** (the Schmidt identity). This is NOT the floor/LER error map
(the separate d3-DM-certified book, task 8e). At exact-grade ``χ`` (the default ``(3^⌈n/2⌉)²`` ≥
the worst operator-Schmidt rank) the discarded weight is structurally 0 (C8). NOTE the exact-grade
bonds equal the (possibly large) TRUE operator-Schmidt rank of the fully-mixed leaked state — so
exact-grade carries DM-scale cost; the carrier's value is at a TRUNCATED ``χ``, where positivity
is STILL structural (the LPDO-vs-MPO discriminator). An unbounded truncation is a STOP
(FAITHFULNESS Rule III): the discarded-weight ledger IS the bound; the C7 drift tripwire (refine
``χ`` ⇒ floor converges) is task 8e's guard.

GPU-only model compute (binding, CLAUDE.md): ``X`` lives on ``device='cuda'`` (no CPU fallback),
``complex128`` throughout (precision-first; mirrors ``QutritDM`` / ``DMPathEvaluator``). The
``PathJointEvaluator`` handle is opaque (a :class:`_TnHandle` carrying the per-path LPDOs); the
floor never inspects it except through the six seams.

src/ commit-gate: STAGED, awaiting confirmation (mainline-code commit gate).
"""

from dataclasses import dataclass
from typing import Any

import torch

from qec_twin.audit.floor_backend import (
    PathJointEvaluator,  # noqa: F401  (documents the Protocol this class implements)
    _require_cuda,
    cptp_residual,
)
from qec_twin.forward.exact.qutrit_dm import QUDIT, qutrit_hadamard
from qec_twin.numerics import NUMERICAL_ZERO

CDTYPE = torch.complex128
RDTYPE = torch.float64
PHYS = QUDIT  # 3 (qutrit physical dimension)


# --------------------------------------------------------------------------- #
# Index-name helpers (the LPDO leg convention).                                #
# --------------------------------------------------------------------------- #
def _pk(k: int) -> str:  return f"p{int(k)}"   # ket physical leg of site k
def _ak(k: int) -> str:  return f"a{int(k)}"   # purification (Kraus/ancilla) leg of site k
def _bk(k: int) -> str:  return f"b{int(k)}"   # spatial bond between sites k and k+1


def exact_chi(n_sites: int) -> int:
    """The spatial bond at which a length-``n`` qutrit purification is EXACT (no spatial
    truncation): ``3^⌈n/2⌉`` is the largest Schmidt rank of a qutrit bipartition. The LPDO
    self-validation + the exact-grade certification run at (a multiple of) this — the C8
    zero-truncation anchor. (The leak channel also grows a purification leg; the backend's
    default ``chi`` multiplies this by a headroom factor so the leak-grown bond is also exact.)"""
    return int(PHYS ** ((int(n_sites) + 1) // 2))


# --------------------------------------------------------------------------- #
# Truncation ledger (ADR 0010 Design-A: the STATE-fidelity book, class (a)).   #
# --------------------------------------------------------------------------- #
@dataclass
class TnTruncationLedger:
    """Per-cut discarded-weight accounting for the LPDO floor (class (a), the STATE book).

    The Schmidt identity ``‖ρ-ρ_χ‖``-style bound: each truncating op records its discarded
    weight ``ε_cut = Σ_{i>χ} σ_i²`` (the quimb ``info['error']²`` of the SVD re-split). This
    bounds the STATE, NOT the floor/LER (that is the separate d3-DM-certified ε↔error map, task
    8e — the two are NEVER merged). ``ok`` is reported against a tolerance by the caller (the C7
    tripwire: refine χ ⇒ floor/LER converges, monotone, no drift)."""

    chi: int
    n_truncating_ops: int = 0
    worst_cut: float = 0.0
    sum_discarded: float = 0.0

    def record_cut(self, discarded: float) -> None:
        d = float(discarded)
        if d < 0.0:
            d = 0.0  # clamp float64 round-off below zero
        self.n_truncating_ops += 1
        self.sum_discarded += d
        if d > self.worst_cut:
            self.worst_cut = d

    def report(self) -> dict[str, Any]:
        return {
            "chi": int(self.chi),
            "exact_grade": bool(self.worst_cut <= NUMERICAL_ZERO),
            "n_truncating_ops": int(self.n_truncating_ops),
            "worst_cut_discarded_weight": float(self.worst_cut),
            "sum_discarded_weight": float(self.sum_discarded),
            "ledger_class": "(a) state-fidelity (Schmidt discarded weight); NOT the LER/floor "
                            "error map (that is the separate d3-DM-certified book, task 8e)",
        }


# --------------------------------------------------------------------------- #
# The LPDO state (rho = X X^dag) — quimb TensorNetwork of per-site tensors.    #
# --------------------------------------------------------------------------- #
class _LPDOState:
    """One locally-purified density operator ``ρ = X X†`` on ``n`` qutrits (one MC path).

    ``X`` is a ``quimb`` :class:`TensorNetwork` of per-site tensors (legs ``p{k}`` physical,
    ``a{k}`` purification, ``b{k}`` spatial bonds). All ops mutate ``X`` in place; positivity of
    ``ρ`` is structural. GPU-only; ``complex128``. ``ledger`` (optional) records discarded weight.
    """

    def __init__(self, tn, n: int, chi: int, device: torch.device,
                 ledger: TnTruncationLedger | None = None) -> None:
        self._qtn = _import_qtn()
        self.tn = tn
        self.n = int(n)
        self.chi = int(chi)
        self.device = device
        self.ledger = ledger

    # -- construction -- #
    @classmethod
    def from_psi(cls, psi: torch.Tensor, n: int, chi: int, device: torch.device,
                 ledger: TnTruncationLedger | None = None) -> "_LPDOState":
        """Build the LPDO of a PURE codestate ``|ψ⟩`` (κ=1 purification legs; exact, full bond).

        ``psi`` is a dense ``3^n`` engine-basis state vector (qutrit ``k`` = the ``k``-th
        most-significant tensor factor — the ``QutritDM`` convention; quimb ``from_dense`` with
        ``dims=[3]*n`` shares it). The MPS factorization is exact (full Schmidt rank), so this is a
        zero-truncation lift. A dim-1 purification leg ``a{k}`` is added per site (a pure state has
        κ=1; the leak channels grow it)."""
        qtn = _import_qtn()
        arr = psi.detach().cpu().numpy()
        mps = qtn.MatrixProductState.from_dense(arr, dims=[PHYS] * n)
        mps.apply_to_arrays(lambda x: torch.as_tensor(x, dtype=CDTYPE, device=device))
        tensors = []
        for k in range(n):
            t = mps[k]
            pind = mps.site_ind(k)
            ren = {pind: _pk(k)}
            if k > 0:
                left = [ix for ix in t.inds if ix in mps[k - 1].inds]
                if left:
                    ren[left[0]] = _bk(k - 1)
            if k < n - 1:
                right = [ix for ix in t.inds if ix in mps[k + 1].inds]
                if right:
                    ren[right[0]] = _bk(k)
            t2 = t.copy()
            t2.reindex_(ren)
            t2.new_ind(_ak(k), size=1, axis=-1)  # dim-1 purification leg (pure state)
            t2.modify(tags={f"S{k}"})
            tensors.append(t2)
        return cls(qtn.TensorNetwork(tensors), n, chi, device, ledger)

    def copy(self) -> "_LPDOState":
        return _LPDOState(self.tn.copy(), self.n, self.chi, self.device, self.ledger)

    def site(self, k: int):
        return self.tn[f"S{int(k)}"]

    # -- ρ = X X† contraction helpers (scalable; no dense 3^n ρ) -- #
    def _conj_tied(self, *, tie_phys: bool):
        """The conjugate copy ``X†`` with bonds mangled to distinct ``bc{k}`` (so each copy's
        spatial bonds contract only within itself) and purification ``a{k}`` TIED to the ket (same
        name → contracted between ket and bra). ``tie_phys`` ties the physical legs too (for a
        full trace); otherwise the bra physical legs are renamed ``q{k}`` (kept open, for a
        diagonal-operator insertion or a dense ρ)."""
        bra = self.tn.conj().copy()
        ren = {}
        for k in range(self.n):
            ren[_bk(k)] = f"bc{k}"
            if not tie_phys:
                ren[_pk(k)] = f"q{k}"
        ren = {a: b for a, b in ren.items() if a in bra.ind_map}
        bra.reindex_(ren)
        return bra

    def trace(self) -> float:
        """``tr ρ = ⟨X|X⟩`` (real) — ties all physical (ket=bra), purification, and bonds."""
        bra = self._conj_tied(tie_phys=True)
        val = (self.tn | bra).contract(output_inds=())
        return float(complex(val).real)

    def _diag_op_trace(self, site_to_diag: dict[int, torch.Tensor]) -> float:
        """``tr(D ρ)`` for ``D = ∏_k diag(site_to_diag[k])`` on the ket (a real per-site diagonal
        operator; sites absent ⇒ identity). One contraction of ``X``, the inserted diagonals, and
        ``X†`` — no dense ρ. The bra ties the ket physical legs (a trace) while the diagonals are
        spliced onto the ket physical legs of the listed sites."""
        bra = self._conj_tied(tie_phys=True)
        ket = self.tn.copy()
        ops = []
        for k, dvec in site_to_diag.items():
            ket.reindex_({_pk(k): f"__in{k}__"})
            ops.append(self._qtn.Tensor(torch.diag(dvec.to(CDTYPE)),
                                        inds=(_pk(k), f"__in{k}__"), tags="DIAG"))
        full = self._qtn.TensorNetwork([*ket.tensors, *ops, *bra.tensors])
        return float(complex(full.contract(output_inds=())).real)

    def to_rho_dense(self) -> torch.Tensor:
        """Dense ``ρ`` (VALIDATION ONLY — defeats the scaling; not used by the seams). Contract to
        ``(p0..p{n-1}, q0..q{n-1})`` and reshape to ``(3^n, 3^n)``."""
        bra = self._conj_tied(tie_phys=False)
        out = [_pk(k) for k in range(self.n)] + [f"q{k}" for k in range(self.n)]
        rho_t = (self.tn | bra).contract(output_inds=out)
        d = PHYS ** self.n
        return rho_t.data.reshape(d, d)

    # -- operations -- #
    def apply_kraus_channel(self, kraus: list[torch.Tensor], site: int) -> float:
        """``ρ → Σ_k K_k ρ K_k†`` on ``site`` (a single-qutrit CPTP channel; the WG leak slice).

        Attaches the ``(rank,3,3)`` Kraus tensor to ``p{site}``; the rank index FUSES into the
        purification leg ``a{site}`` (mixedness grows), then a re-split against the neighbour
        bounds the spatial bond at ``χ`` and records the discarded Schmidt weight. ``X`` stays a
        valid LPDO ⇒ ``ρ`` PSD. Returns the discarded weight (0 at exact-grade ``χ``)."""
        Kt = torch.stack([k.to(CDTYPE) for k in kraus])  # (r,3,3)
        pind = _pk(site)
        gt = self._qtn.Tensor(Kt, inds=("__rank__", "__po__", pind), tags="CH")
        t = self.site(site)
        new = (t | gt).contract()
        new.reindex_({"__po__": pind})
        new.fuse_({_ak(site): ["__rank__", _ak(site)]})  # fuse rank into the purification leg
        nb = site + 1 if site + 1 < self.n else site - 1
        if nb < 0:  # n == 1: no neighbour; the purification leg just grows (no spatial bond)
            new.modify(tags={f"S{site}"})
            self.tn.delete(f"S{site}")
            self.tn.add_tensor(new)
            return 0.0
        bond = _bk(min(site, nb))
        merged = (new | self.site(nb)).contract()
        left_inds = [ix for ix in new.inds if ix != bond and ix in merged.inds]
        info: dict = {}
        # cutoff=1e-14 drops numerically-zero Schmidt values so the bond stays at its TRUE rank
        # (lossless: the dropped weight is ~machine-zero) — without it the bond saturates at χ and
        # every later contraction is over a χ-bond ⇒ the TN balloons and contraction explodes.
        # max_bond=χ is the hard truncating cap (a genuine truncation drops real weight, recorded).
        tl, tr = merged.split(left_inds=left_inds, bond_ind=bond, max_bond=int(self.chi),
                              cutoff=1e-14, cutoff_mode="abs", method="svd", info=info, get="tensors")
        tl.modify(tags={f"S{site}"})
        tr.modify(tags={f"S{nb}"})
        self.tn.delete(f"S{site}")
        self.tn.delete(f"S{nb}")
        self.tn.add_tensor(tl)
        self.tn.add_tensor(tr)
        err = info.get("error", None)
        discarded = float(err) ** 2 if err is not None else 0.0
        # CRUCIAL: also compress the purification leg a{site} — a single-site channel multiplies it
        # by the Kraus rank each call, so without compression it grows unboundedly. a{site} is
        # contracted ONLY with X†'s a{site}, so SVD-capping it truncates the local mixed (operator-
        # Schmidt) rank exactly (lossless at exact-grade κ); ρ stays = X X† (PSD).
        discarded = max(discarded, self._compress_purification(site))
        if self.ledger is not None:
            self.ledger.record_cut(discarded)
        return discarded

    def _compress_purification(self, site: int) -> float:
        """SVD-compress the purification leg ``a{site}`` to ``≤ chi``: split ``[a{site}]`` vs
        ``[p{site}, bonds]`` (``cutoff=1e-14`` ⇒ true local mixed rank, lossless), then rename the
        new bond back to ``a{site}`` (the SVD left factor is an isometry on ``a{site}`` — its
        columns are orthonormal — so ``Σ_a U[a,nb] U*[a,nb'] = δ`` ⇒ ``ρ = Σ_nb (S V†)[nb] (S V†)*[nb]``
        with the truncated ``a`` leg = ``nb``; exact iff no nonzero Schmidt value dropped). Returns
        the discarded weight."""
        t = self.site(site)
        a = _ak(site)
        if a not in t.inds or t.ind_size(a) <= 1:
            return 0.0
        info: dict = {}
        # absorb='right' keeps the singular values in the carrier (the new site tensor); the left
        # factor is the isometry on a{site}, which the trace ρ=XX† contracts to the identity.
        tl, tr = t.split(left_inds=[a], max_bond=int(self.chi), cutoff=1e-14, cutoff_mode="abs",
                         method="svd", info=info, get="tensors", absorb="right")
        newbond = next(iter(tl.bonds(tr)))
        tr2 = tr.copy()
        tr2.reindex_({newbond: a})  # the truncated purification leg keeps the name a{site}
        tr2.modify(tags={f"S{site}"})
        self.tn.delete(f"S{site}")
        self.tn.add_tensor(tr2)
        err = info.get("error", None)
        return float(err) ** 2 if err is not None else 0.0

    def apply_ket_unitary(self, U: torch.Tensor, site: int) -> None:
        """1-site unitary on the KET: ``p{site} → U p{site}`` (``ρ → U ρ U†``; exact, no bond
        growth). Used for the X-support Hadamard rotations and the transversal X/Y DD echoes."""
        gt = self._qtn.Tensor(U.to(CDTYPE), inds=("__po__", _pk(site)), tags="U")
        t = self.site(site)
        new = (t | gt).contract()
        new.reindex_({"__po__": _pk(site)})
        new.modify(tags={f"S{site}"})
        self.tn.delete(f"S{site}")
        self.tn.add_tensor(new)

    def apply_sqrt_Es(self, supp: list[int], outcome: int, d2: float) -> float:
        """Apply ``√E_s`` (a single Kraus operator) on the support to the KET:
        ``ρ → (√E_s X)(√E_s X)†``. ``E_s`` is diagonal in the (rotated) trit basis with
        ``E_s[c] = ½(1 + (−1)^s ∏_q d_q(t_q))``, ``d_q = (1, −1, d₂)``; ``√E_s`` does not
        factorize over the support so it is built as the EXACT dense diagonal ``√E_s`` over the
        ``3^w`` support and applied as one multi-site KET gate (re-compressing the spatial bonds at
        ``χ``). Ket-only ⇒ ρ stays PSD (C2). Returns the discarded weight of the re-split."""
        w = len(supp)
        dlev = torch.tensor([1.0, -1.0, float(d2)], dtype=RDTYPE, device=self.device)
        grids = torch.meshgrid(*([torch.arange(PHYS, device=self.device)] * w), indexing="ij")
        prod = torch.ones([PHYS] * w, dtype=RDTYPE, device=self.device)
        for g in grids:
            prod = prod * dlev[g]
        sgn = 1.0 if (int(outcome) & 1) == 0 else -1.0
        es = torch.clamp(0.5 * (1.0 + sgn * prod), min=0.0)
        sqrt_diag = torch.sqrt(es).reshape(-1).to(CDTYPE)
        return self._apply_diag_ket_support(list(supp), sqrt_diag)

    def _apply_diag_ket_support(self, supp: list[int], diag_w: torch.Tensor) -> float:
        """Apply a diagonal multi-site operator ``diag(diag_w)`` (length ``3^w``) over the support
        to the KET physical legs, then re-split back into per-site tensors bounding the spatial
        bonds at ``χ``. ROBUST to NON-CONTIGUOUS supports (e.g. a stabilizer on sites {0,2}, or the
        logical {0,2}): the GAP sites between ``min(supp)`` and ``max(supp)`` thread the operator's
        bond along the chain without densifying. Tracks the worst discarded weight.

        SCALABLE √E_s (ADR 0010 C2; the full-d3 span-5 fix). ``diag(diag_w)`` (the √E_s POVM Kraus or
        a diagonal-Z mask) is a multi-site DIAGONAL operator, so it factorizes as a SMALL-bond MPO —
        the operator-Schmidt rank of √E_s across any cut is tiny (≤ 5 for d3, measured; the ½(1 ±
        ∏ d_q) parity structure, INDEPENDENT of the support SPAN — gap sites woven with identity add
        no bond), versus the ``3^span`` of a dense merge. A dense block-merge of the full contiguous
        span (the prior implementation) OOMs on the real d3's SPAN-5 stabilizers ({1,3,4,6}, {2,4,5,7}
        → a 6-site ``3^6=729`` block × the spatial bond): the n=4 sub-register (max span 3) never
        exposed it, so the full-9q floor never ran. The fix builds the operator's MPO (the SAME
        ``MatrixProductOperator.from_dense`` mechanism the FORWARD backend's ``contract='nonlocal'``
        stabilizer measurement uses — ``forward/scalable/mps_forward.py``), contracts each MPO tensor
        into ITS OWN ket site (the MPO's virtual bond — which connects consecutive SUPPORT sites,
        skipping gaps — fuses locally), then threads + re-splits site-by-site bounding the spatial
        bonds at ``χ``. NEVER forms the ``3^span`` dense block. Ket-only ⇒ ρ stays PSD (C2). The
        purification legs ``a{k}`` ride along untouched (the gate is on the physical legs only). This
        is BEHAVIOR-PRESERVING: bit-exact vs the prior dense-merge AND an independent dense ``D ρ D``
        oracle on span≤4 LPDOs with grown purification legs (~1e-16; the certified sub-register +
        span≤4 full-9q numbers do NOT move)."""
        order = sorted(int(s) for s in supp)
        w = len(order)
        lo, hi = order[0], order[-1]
        block = list(range(lo, hi + 1))  # the covered window (support + gap sites)
        suppset = set(order)

        # the small-bond MPO of diag(diag_w) over the SUPPORT sites of the length-n chain (gap sites
        # are NOT materialized as tensors — the MPO virtual bond skips them). Rename its physical legs
        # to a collision-free namespace (its default lower-id 'b{}' clashes with the spatial bonds).
        G = torch.diag(diag_w.to(CDTYPE)).reshape([PHYS] * w + [PHYS] * w)
        mpo = self._qtn.MatrixProductOperator.from_dense(
            G.detach().cpu().numpy(), dims=[PHYS] * w, sites=order, L=self.n)
        mpo.upper_ind_id = "__es_k{}__"   # output legs (become the ket physical legs p{s})
        mpo.lower_ind_id = "__es_l{}__"   # input legs (tie to the ket physical legs p{s})
        mpo.apply_to_arrays(lambda x: torch.as_tensor(x, dtype=CDTYPE, device=self.device))
        upper = {s: mpo.upper_ind(s) for s in order}
        lower = {s: mpo.lower_ind(s) for s in order}

        # contract each support MPO tensor into its ket site (local; the site's bond grows only by the
        # MPO virtual bond, ≤ the small operator-Schmidt rank). Gap sites are passed through unchanged.
        new_sites: dict[int, Any] = {}
        for s in block:
            ks = self.site(s).copy()
            if s in suppset:
                M = mpo[f"I{s}"].copy()
                ks.reindex_({_pk(s): lower[s]})          # tie M's input leg to the ket physical leg
                merged = (ks | M).contract()
                merged.reindex_({upper[s]: _pk(s)})      # M's output leg becomes the ket physical leg
                new_sites[s] = merged
            else:
                new_sites[s] = ks
        for s in block:
            self.tn.delete(f"S{s}")

        # sweep left-to-right: accumulate the running left tensor, contract with the next site, peel
        # off site s (keeping p{s}, a{s}, the left bond b{s-1}); the bond to the right is b{s}. This
        # threads the dangling MPO virtual bonds (connecting non-adjacent support sites) into the
        # spatial bonds — the running contraction carries them along — and bounds each at χ.
        worst = 0.0
        remaining = new_sites[block[0]]
        for idx in range(len(block) - 1):
            s = block[idx]
            remaining = (remaining | new_sites[block[idx + 1]]).contract()
            keep = [_pk(s), _ak(s)]
            if _bk(s - 1) in remaining.inds:
                keep.append(_bk(s - 1))
            bond = _bk(s)
            info: dict = {}
            tl, tr = remaining.split(left_inds=[ix for ix in keep if ix in remaining.inds],
                                     bond_ind=bond, max_bond=int(self.chi), cutoff=1e-14,
                                     cutoff_mode="abs", method="svd", info=info, get="tensors")
            tl.modify(tags={f"S{s}"})
            self.tn.add_tensor(tl)
            remaining = tr
            err = info.get("error", None)
            if err is not None:
                worst = max(worst, float(err) ** 2)
        remaining.modify(tags={f"S{block[-1]}"})
        self.tn.add_tensor(remaining)
        if self.ledger is not None and worst > 0.0:
            self.ledger.record_cut(worst)
        return worst

    # -- reads the seams need (scalable; no dense ρ) -- #
    def branch_trace(self, paulis: dict[int, str], outcome: int, d2: float) -> float:
        """``tr(E_s ρ)`` for ``s = outcome`` in the (rotated) basis (the Born branch weight):
        ``½(tr ρ + (−1)^s tr(∏_q D_q ρ))``, ``D_q = diag(1, −1, d₂)`` on the support. Does NOT
        mutate ``ρ`` (the parent state is reused for both branches). The caller must rotate the
        X-supports to Z FIRST (as the projector does)."""
        Dq = torch.tensor([1.0, -1.0, float(d2)], dtype=RDTYPE, device=self.device)
        par = self._diag_op_trace({s: Dq for s in paulis})
        tr = self.trace()
        sign = 1.0 if (int(outcome) & 1) == 0 else -1.0
        return 0.5 * (tr + sign * par)

    def logical_sector_traces(self, logical: dict[int, str]) -> tuple[float, float]:
        """``(P(L=0), P(L=1)) = tr(Π_{L=ℓ} ρ)`` (the UNNORMALIZED logical-parity sector traces;
        leaked logical support split evenly — the engine's neutral default). Reads
        ``P0 = ½(A + D)``, ``P1 = ½(A − D)`` with ``A = tr ρ`` and
        ``D = tr(∏_{log} Z̃ · ρ)``, ``Z̃ = diag(1, −1, 0)`` (the leaked ``|2⟩`` killed in the
        difference so it splits evenly, and summed in ``A``). X-supports are Hadamard-rotated on the
        ket of a COPY first (``ρ → H ρ H†``, whose computational diagonal = ρ's diagonal in the
        rotated basis — exactly the DM read). Sum identity ``P0 + P1 = tr ρ`` holds by
        construction; validated vs the DM in ``p7d_lpdo_reads_proto.py``."""
        H = qutrit_hadamard(self.device)
        rotated = self.copy()
        for s, p in logical.items():
            if str(p).upper() == "X":
                rotated.apply_ket_unitary(H, s)
        A = rotated.trace()
        Zmask = torch.tensor([1.0, -1.0, 0.0], dtype=RDTYPE, device=self.device)
        D = rotated._diag_op_trace({s: Zmask for s in logical})
        return 0.5 * (A + D), 0.5 * (A - D)


# --------------------------------------------------------------------------- #
# The opaque handle (the PathJointEvaluator carrier).                          #
# --------------------------------------------------------------------------- #
@dataclass
class _TnHandle:
    """The opaque ``PathJointEvaluator`` handle for the LPDO backend: the per-path UNNORMALIZED
    conditionals ``ρ_{s|m}`` (one :class:`_LPDOState` per Monte-Carlo path) + provenance. The
    floor never inspects this except through the six seams; ``states[i].trace() = P(s_i|m)``."""

    states: list[_LPDOState]
    n: int
    ledger: TnTruncationLedger


# --------------------------------------------------------------------------- #
# Within-cycle evolution on the LPDO (reuses the DM backend's schedule).       #
# --------------------------------------------------------------------------- #
def _qutrit_X(device: torch.device) -> torch.Tensor:
    m = torch.zeros((PHYS, PHYS), dtype=CDTYPE, device=device)
    m[0, 1] = 1.0; m[1, 0] = 1.0; m[2, 2] = 1.0
    return m


def _qutrit_Y(device: torch.device) -> torch.Tensor:
    m = torch.zeros((PHYS, PHYS), dtype=CDTYPE, device=device)
    m[0, 1] = -1.0j; m[1, 0] = 1.0j; m[2, 2] = 1.0
    return m


def _apply_premeasure(state: _LPDOState, prob: Any) -> None:
    """The per-qutrit pre-M within-cycle stream of ONE round (H / X gates + ``exp(L/4)`` LEAK
    slices), IN ORDER — the EXACT lift of ``DMPathEvaluator``'s ``_apply_premeasure_batched`` /
    ``QutritDM.apply_within_cycle_premeasure``. Single-qutrit ops on distinct qutrits commute, so
    per-qutrit replay equals the true interleaving; the in-stream H's + the mid-cycle X are the DD
    refocusing echoes (C5) — none dropped."""
    H = qutrit_hadamard(state.device)
    X = _qutrit_X(state.device)
    leak = list(prob.leak_kraus)
    for q, toks in prob.streams.items():
        site = int(q)
        for tok in toks:
            if tok == "LEAK":
                state.apply_kraus_channel(leak, site)
            elif tok == "H":
                state.apply_ket_unitary(H, site)
            elif tok == "X":
                state.apply_ket_unitary(X, site)
            elif tok in ("M", "Y"):
                continue  # M is a marker; Y is post-M
            else:
                raise ValueError(f"within-cycle pre-measure: unknown token {tok!r} at site {site}")


def _apply_postmeasure_Y(state: _LPDOState, prob: Any, *, terminal: bool) -> None:
    """The post-M transversal Y on every site (dropped on the terminal round) — the C5 post-M DD
    echo; the uniform-Y interior convention the DM backend / ``dm_floor_history`` use."""
    if terminal:
        return
    Y = _qutrit_Y(state.device)
    for site in range(prob.n):
        state.apply_ket_unitary(Y, site)


def _project_apply(state: _LPDOState, paulis: dict[int, str], outcome: int, d2: float) -> None:
    """Apply ``√E_{outcome}`` for one stabilizer to the LPDO (X-supports Hadamard-rotated to Z
    first, then back) — the EXACT lift of ``DMPathEvaluator``'s ``_project_apply_batched``. (Arm C
    leak-flag dephasing is NOT supported by this backend yet — see :meth:`TNPathEvaluator`.)"""
    H = qutrit_hadamard(state.device)
    x_sites = [s for s, p in paulis.items() if str(p).upper() == "X"]
    for s in x_sites:
        state.apply_ket_unitary(H, s)
    state.apply_sqrt_Es(list(paulis.keys()), outcome, d2)
    for s in x_sites:
        state.apply_ket_unitary(H, s)


def _arm_d2(arm: str, b: float) -> float:
    """The per-qutrit leaked-level Z-parity weight ``d_q(2)`` (mirrors ``DMPathEvaluator`` /
    ``QutritDM._povm_diag_weight``): A → ``1−2b``; B1 → ``+1``; B2 → ``−1``."""
    a = str(arm).upper()
    if a == "A":
        return 1.0 - 2.0 * float(b)
    if a == "B1":
        return 1.0
    if a == "B2":
        return -1.0
    if a == "C":
        raise NotImplementedError(
            "TNPathEvaluator does not implement arm C (leak-flag dephasing) yet — use arm A/B1/B2, "
            "or the DM backend for arm C (the R=1 floor is arm-A == arm-C; arm C is an R>1 "
            "disturbance comparator).")
    raise ValueError(f"unknown measurement arm {arm!r} (expected A, B1 or B2)")


def _import_qtn():
    """Lazy quimb import (mirrors ``mps_forward`` / ``sv_sampler``): the module imports without
    quimb present; the GPU LPDO path requires it."""
    import quimb.tensor as qtn  # noqa: WPS433
    return qtn


def _build_codestate_psi(prob: Any, m: int, device: torch.device) -> torch.Tensor:
    """The pure ``|m⟩_L`` codestate as a dense ``3^n`` engine-basis VECTOR via the certified
    ``QutritDM._codestate_vector`` projector-product (the SAME +1-stabilizer/(-1)^m-logical
    eigenstate construction the DM oracle's ``init_logical`` uses) — reused only for the EXACT,
    zero-truncation LPDO lift (``_LPDOState.from_psi``).

    WHY NOT THE EIGH (the full-9q cost wall this avoids). The LPDO carries ``ρ = X X†``, which is
    GLOBAL-PHASE-INVARIANT, so it needs only the pure ``|ψ⟩`` up to a phase. Recovering ``|ψ⟩`` as the
    top eigenvector of an EIGH of the dense ``3^n × 3^n`` ``ρ = |ψ⟩⟨ψ|`` (the prior implementation)
    HOST-SPILLS at n=9 (the matrix + cuSOLVER workspace exceed the card) and ran >15 min/cell — the
    entire full-9q reevolve wall. ``_codestate_vector`` returns the IDENTICAL state up to that
    immaterial global phase, at state-vector cost (no dense ρ, no eigh). PROVEN equivalent:
    ``|⟨eigh|fast⟩|=1`` and ``|Δρ|=0`` on an n=2 control (``outputs/teacher_prereg/p7i_lpdo_fast_probe``),
    and the full-9q closure re-confirms it bit-exact vs the DM oracle. A behavior-preserving cost fix,
    not a faithfulness change (the resulting ρ is identical)."""
    from qec_twin.forward.exact.qutrit_dm import QutritDM
    e = QutritDM(prob.n, device=device)
    e.set_code(stabilizers=prob.stabs, logical_z=prob.logical)
    psi = e._codestate_vector(int(m))
    nrm = torch.linalg.vector_norm(psi)
    return (psi / nrm.to(CDTYPE)).to(CDTYPE)


# --------------------------------------------------------------------------- #
# The LPDO PathJointEvaluator.                                                  #
# --------------------------------------------------------------------------- #
class TNPathEvaluator:
    """quimb LPDO ``PathJointEvaluator`` — the SCALABLE Bayes-floor backend (ADR 0010, task 8d).

    Carries the syndrome-conditioned MIXED state ``ρ_s = X X†`` as a locally-purified MPDO
    (positivity STRUCTURAL — C2), and implements the same six seams as ``DMPathEvaluator``, so it
    drops into ``audit/bayes_floor`` as ``mc_floor(prob, evaluator=TNPathEvaluator(chi=...))``. At
    full ``χ`` it matches the DM oracle bit-for-bit (the C8 anchor; rung-2 cert is task 8e).

    ``chi`` is the spatial bond cap (default = exact-grade: ``3^⌈n/2⌉`` × a leak-rank headroom, so
    the leak-grown bond is also exact ⇒ zero truncation, the C8 path). Pass a smaller ``chi`` for
    the truncated carrier; the discarded weight is tracked into :class:`TnTruncationLedger` (the
    class-(a) STATE book, NOT the floor-error map). One :class:`_LPDOState` per Monte-Carlo path
    (the seams loop over the ``B`` paths — correctness-first; the sub-register self-validation is
    cheap, the full-9q anchor is task 8e). GPU-only model compute; ``complex128``.

    Effectively stateless apart from ``chi`` and a single shared ``ledger`` accumulating discarded
    weight across calls — two runs with the same seed are bit-identical, so a default instance is
    safe to share.

    KNOWN LIMITATION — arm C not implemented. ``_arm_d2`` raises ``NotImplementedError`` for arm C
    (the leak-flag-dephasing measurement instrument): the LPDO carrier supports arms A/B1/B2 only.
    This is NON-LOAD-BEARING for the carrier certification — every cert run is arm A, and arm C is
    an R>1 disturbance comparator that COINCIDES with arm A at R=1 (no leak-flag to dephase yet).
    For an arm-C floor use the DM backend (``DMPathEvaluator``), which implements the leak-flag
    dephasing (``_leak_flag_dephase_batched``).

    A NOTE on the default (exact-grade) ``chi``: every SVD re-split also uses a tiny ``cutoff``
    (``1e-14``) that drops numerically-zero Schmidt values, so the bonds (spatial AND purification)
    self-shrink to their TRUE rank — the hard ``chi`` cap only needs to sit ABOVE the worst exact
    rank to guarantee zero truncation. The operator-Schmidt rank of an ``n``-qutrit ρ across a cut
    is ``≤ (3^⌈n/2⌉)²``, so the exact-grade default cap is ``exact_chi(n)²`` (the cutoff keeps the
    ACTUAL bonds tiny ⇒ the large cap is never materialized). Pass an explicit ``chi`` for the
    genuinely-truncated carrier."""

    def __init__(self, *, chi: int | None = None) -> None:
        self._chi = None if chi is None else int(chi)
        self.ledger = TnTruncationLedger(chi=(self._chi if self._chi is not None else -1))

    def _resolve_chi(self, n: int) -> int:
        """The bond cap: explicit ``chi`` if given, else the exact-grade ``(3^⌈n/2⌉)²`` (≥ the
        worst operator-Schmidt rank ⇒ the per-cut ``cutoff`` finds the true small rank losslessly —
        the C8 zero-truncation anchor)."""
        if self._chi is not None:
            return self._chi
        return exact_chi(n) ** 2

    # -- the leak channel CPTP residual (the L6 gate) -- #
    def cptp_residual(self, prob: Any) -> float:
        """``max‖Σ_k K_k† K_k − I‖`` of the within-cycle leak slice (CPTP to < 1e-9 when faithful;
        a non-CPTP slice trips HERE — identical gate to ``DMPathEvaluator.cptp_residual``)."""
        return cptp_residual(prob.leak_kraus)

    # -- Born-sample a batch of paths, keep the conditional handle -- #
    def sample_paths(self, prob: Any, m_draw: torch.Tensor, B: int,
                     generator: torch.Generator) -> tuple[_TnHandle, torch.Tensor]:
        """Build the per-path ``|m_draw⟩_L`` LPDO, Born-branch ``B`` paths down a random
        measurement path, return ``(handle, records)`` — ``handle`` carries the kept UNNORMALIZED
        ``ρ_{s|m_draw}`` LPDOs (``trace = P(s|m_draw)``), ``records`` the ``(B, R·n_stab)`` sampled
        syndrome history (uint8). The generator drives ONLY the branch draws (the codestate build
        is deterministic); the branch sampling mirrors ``DMPathEvaluator._sample_paths_batched``
        (per stabilizer: parent trace, ``p0 = tr(E_0 ρ)/tr ρ``, draw ``u``, outcome ``u ≥ p0``,
        project ``√E_s``)."""
        device = m_draw.device
        _require_cuda(device)
        chi = self._resolve_chi(int(prob.n))
        self.ledger.chi = chi
        R, n_stab = int(prob.R), int(prob.n_stab)
        d2 = _arm_d2(prob.arm, prob.b)

        # build the per-(m) pure codestate once, then copy per path (deterministic).
        psi_by_m = {int(mv): _build_codestate_psi(prob, int(mv), device)
                    for mv in torch.unique(m_draw).tolist()}
        states: list[_LPDOState] = []
        m_list = [int(x) for x in m_draw.detach().cpu().tolist()]
        for mv in m_list:
            states.append(_LPDOState.from_psi(psi_by_m[mv], int(prob.n), chi, device, self.ledger))

        records = torch.empty((B, R * n_stab), dtype=torch.uint8, device=device)
        # draw all branch uniforms up front in the SAME (path, round, stab) order the DM backend
        # consumes them (one rand(B) per stabilizer) — so the generator stream matches.
        col = 0
        H = qutrit_hadamard(device)
        for r in range(R):
            is_term = (r == R - 1)
            for st in states:
                _apply_premeasure(st, prob)
            for supp in prob.stabs:
                u = torch.rand(B, generator=generator, device=device, dtype=RDTYPE)
                x_sites = [s for s, p in supp.items() if str(p).upper() == "X"]
                outcomes = torch.empty(B, dtype=torch.uint8, device=device)
                for i, st in enumerate(states):
                    for s in x_sites:
                        st.apply_ket_unitary(H, s)
                    parent = st.trace()
                    tr0 = st.branch_trace(supp, 0, d2)
                    p0 = (tr0 / parent) if parent > NUMERICAL_ZERO else 0.0
                    bit = 0 if (float(u[i]) < p0) else 1
                    st.apply_sqrt_Es(list(supp.keys()), bit, d2)
                    for s in x_sites:
                        st.apply_ket_unitary(H, s)
                    outcomes[i] = bit
                records[:, col] = outcomes
                col += 1
            for st in states:
                _apply_postmeasure_Y(st, prob, terminal=is_term)
        return _TnHandle(states=states, n=int(prob.n), ledger=self.ledger), records

    # -- deterministically re-evolve a (different) m onto fixed records -- #
    def reevolve_onto_records(self, prob: Any, m: torch.Tensor,
                              records: torch.Tensor) -> _TnHandle:
        """Build the per-path ``|m⟩_L`` LPDO and DETERMINISTICALLY evolve it onto the FIXED
        ``records`` → ``ρ_{s|m}`` for the same records (the 'other m' leg of the (s, f) joint).
        ``m`` is a length-B int tensor; ``records`` is ``(B, R·n_stab)`` uint8. Mirrors
        ``DMPathEvaluator._reevolve_onto_records_batched``."""
        device = records.device
        _require_cuda(device)
        chi = self._resolve_chi(int(prob.n))
        self.ledger.chi = chi
        R, n_stab = int(prob.R), int(prob.n_stab)
        d2 = _arm_d2(prob.arm, prob.b)
        B = int(records.shape[0])

        psi_by_m = {int(mv): _build_codestate_psi(prob, int(mv), device)
                    for mv in torch.unique(m).tolist()}
        m_list = [int(x) for x in m.detach().cpu().tolist()]
        states = [_LPDOState.from_psi(psi_by_m[mv], int(prob.n), chi, device, self.ledger)
                  for mv in m_list]
        rec = records.detach().cpu().numpy()
        col = 0
        for r in range(R):
            is_term = (r == R - 1)
            for st in states:
                _apply_premeasure(st, prob)
            for supp in prob.stabs:
                for i, st in enumerate(states):
                    _project_apply(st, supp, int(rec[i, col]), d2)
                col += 1
            for st in states:
                _apply_postmeasure_Y(st, prob, terminal=is_term)
        return _TnHandle(states=states, n=int(prob.n), ledger=self.ledger)

    # -- the logical-parity sector traces (P(L=0), P(L=1)) on a handle -- #
    def logical_sector_traces(self, handle: _TnHandle,
                              logical: dict[int, str]) -> tuple[torch.Tensor, torch.Tensor]:
        """``(P(L=0), P(L=1)) = tr(Π_{L=ℓ} ρ)`` per path on the UNNORMALIZED handle (each ``(B,)``
        real; their sum = ``tr ρ = P(s|m)``). Reads each path's LPDO via the scalable
        masked-diagonal contraction (no dense ρ)."""
        device = handle.states[0].device if handle.states else torch.device("cuda")
        p0 = torch.empty(len(handle.states), dtype=RDTYPE, device=device)
        p1 = torch.empty(len(handle.states), dtype=RDTYPE, device=device)
        for i, st in enumerate(handle.states):
            a, b = st.logical_sector_traces(logical)
            p0[i] = a
            p1[i] = b
        return p0, p1

    # -- the per-path trace tr ρ = P(s|m) (the L6 trace-conservation proxy) -- #
    def path_trace(self, handle: _TnHandle) -> torch.Tensor:
        """``tr ρ = P(s|m)`` per path (``(B,)`` real) via ``⟨X|X⟩`` (no dense ρ) — the LPDO supplies
        its own trace (the seam the floor routes through so a non-DM handle works)."""
        device = handle.states[0].device if handle.states else torch.device("cuda")
        out = torch.empty(len(handle.states), dtype=RDTYPE, device=device)
        for i, st in enumerate(handle.states):
            out[i] = st.trace()
        return out

    # -- EXACT small-R within-cycle history (the L1 enumeration anchor leg) -- #
    def enumerate_history(self, prob: Any, m: int) -> dict[tuple, tuple[float, float]]:
        """The full within-cycle history map ``{path_tuple -> (P(s,L=0|m), P(s,L=1|m))}`` by EXACT
        depth-first projection enumeration on the LPDO (the L1 ground-truth leg). EXACT-by-
        enumeration on the LPDO: ``tr(E_s ρ)`` equals the full Kraus-branch integral and
        ``E_0 + E_1 = I`` keeps the branch traces summing to the parent. Feasible on a sub-register
        at small R. PURE LPDO analog of ``DMPathEvaluator.enumerate_history`` (same recursion; the
        state is the LPDO, not the dense DM). At exact-grade ``χ`` (the default) it matches the DM
        enumeration bit-for-bit (C8)."""
        device = prob.leak_kraus[0].device
        _require_cuda(device)
        chi = self._resolve_chi(int(prob.n))
        self.ledger.chi = chi
        d2 = _arm_d2(prob.arm, prob.b)
        H = qutrit_hadamard(device)
        psi0 = _build_codestate_psi(prob, int(m), device)
        out: dict[tuple, tuple[float, float]] = {}

        def recurse(state: _LPDOState, r: int, prefix: tuple) -> None:
            _apply_premeasure(state, prob)
            is_term = (r == prob.R - 1)
            # enumerate this round's joint syndrome by depth-first branching over the stabilizers,
            # snapshotting before each binary branch (the exact within-cycle integral).
            def descend(st: _LPDOState, k: int, sfx: tuple) -> None:
                if k == len(prob.stabs):
                    new_prefix = prefix + sfx
                    if is_term:
                        L0, L1 = st.logical_sector_traces(prob.logical)
                        prev = out.get(new_prefix, (0.0, 0.0))
                        out[new_prefix] = (prev[0] + float(L0), prev[1] + float(L1))
                    else:
                        tr = st.trace()
                        if tr <= 1e-300:
                            return
                        # normalize the branch, apply post-M Y, recurse carrying the UNNORM weight
                        nxt = st.copy()
                        # rescale to unit trace by folding 1/sqrt(tr) into one ket tensor, then back
                        _scale_ket(nxt, 1.0 / (tr ** 0.5))
                        _apply_postmeasure_Y(nxt, prob, terminal=False)
                        _scale_ket(nxt, tr ** 0.5)  # restore the unnormalized branch weight
                        recurse(nxt, r + 1, new_prefix)
                    return
                supp = prob.stabs[k]
                x_sites = [s for s, p in supp.items() if str(p).upper() == "X"]
                # branch on outcome 0 and 1 from the SAME parent (snapshot), pruning zero weight.
                for outcome in (0, 1):
                    child = st.copy()
                    for s in x_sites:
                        child.apply_ket_unitary(H, s)
                    bt = child.branch_trace(supp, outcome, d2)
                    if bt <= 1e-15:
                        continue
                    child.apply_sqrt_Es(list(supp.keys()), outcome, d2)
                    for s in x_sites:
                        child.apply_ket_unitary(H, s)
                    descend(child, k + 1, sfx + (int(outcome),))

            descend(state, 0, ())

        base = _LPDOState.from_psi(psi0, int(prob.n), chi, device, self.ledger)
        recurse(base, 0, ())
        return out


def _scale_ket(state: _LPDOState, factor: float) -> None:
    """Multiply the LPDO ket ``X`` by a real scalar (``ρ → factor² ρ``) by folding ``factor`` into
    one site tensor — exact, bond-free (used to (de)normalize an enumeration branch while carrying
    its unnormalized weight, mirroring the DM enumeration's ``rho * tr`` rescale)."""
    t = state.site(0)
    t.modify(data=t.data * complex(factor))
