from __future__ import annotations

"""Batched-shot (B-leading) qutrit MPS op core — the OPT2-1 sibling arm of ``mps_forward.py``.

WHAT. The shot-parallel Matrix-Product-State substrate for the MCWF leakage forward
(``docs/twin_validation/batched_mps_backend_prereg.md`` §OPT2-1 DESIGN, v2 — the binding
build contract). Every MPS site tensor carries a leading batch dimension
``[B, cap_{k-1}, 3, cap_k]`` and is ZERO-PADDED to fixed cap shapes at all times
(Doi batch-shots invariant: uniform kernels, per-shot divergence lives only in operator
VALUES, never in shapes or control flow). quimb-free by construction: quimb appears only
in the equivalence TESTS as the serial reference arm (``tests/test_batched_mps_ops.py``).
Torch / cuda / ``complex128`` only.

WHY. The serial quimb trajectory loop is dispatch-bound (measured d3 ~1 s/shot,
d5 ~104 s/shot — prereg §0). The OPT2-0 spike (prereg §OPT2-0 OUTCOMES) fixed the
decomposition routing: ``torch.linalg.svd`` is batch-LOOPED (out of the hot path);
batched reduced QR + Gram + batched ``eigh`` are genuinely batch-parallel. This module
is the op core those measurements anchor; the trajectory driver is OPT2-2.

FAITHFULNESS (docs/FAITHFULNESS_PROTOCOL.md). Every op names its SERIAL REFEREE in
``mps_forward.MpsLeakageForward`` and mirrors its math EXACTLY — same tie-breaks, same
guards, same conventions:

  op                          serial referee                       convention mirrored
  --------------------------  -----------------------------------  ------------------------------
  from_dense / to_dense       quimb ``from_dense``/``to_dense``    engine row-major, site-0 = MSB
  canonicalize_/norm_sq/      ``_norm_sq`` / ``_renormalize``      ``ns <= NUMERICAL_ZERO`` skip
    renormalize_                                                     (serial lines 513-515)
  apply_1site_                ``_apply_gate``                      1-site apply, no renormalize
  site_rdm                    ``local_expectation_canonical``      unnormalized = branch norms
  kraus_sample_               ``_leak_sample``                     cumulative ``<=`` rule
                                                                     (serial line 584), fallback K-1
  local_expectation           ``_parity_expectation`` /            given-order legs; ``.real``
                                ``_site_population``
  apply_window_recompress_    ``_apply_sqrt_Es`` /                 branch_weight == serial ``nt``
                                codestate ``_project``               (lines 692-694)

TIE-BREAK / GUARD REGISTRY (prereg D-2 op 5, complete; serial lines cited — the entries
NOT implemented by an op here belong to the OPT2-2 driver COMPOSITIONS of these ops and
are quoted so driver authors never "harmonize" them silently):
  * ``_leak_sample`` cumulative ``<=`` (line 584)      -> kraus_sample_ (this module);
  * ``_renormalize`` skip at ``ns <= NUMERICAL_ZERO``
    (lines 513-515)                                    -> _scale_center_ per-shot mask;
  * Born-stab strict ``u < p0`` (line 634)             -> OPT2-2 driver;
  * arm-C leak-flag strict ``u < p2`` (line 623), read
    as the NORMALIZED 1-site population of the CURRENT
    (already partially projected) state, sequentially
    in support order, renormalized per site (617-630)  -> OPT2-2 driver (site_rdm +
                                                          per-shot apply_1site_);
  * hard2 strict ``u < p1`` (781), ``wt <=
    NUMERICAL_ZERO => p1 = 0.5`` (780)                 -> OPT2-2 driver;
  * hard3 cumulative STRICT ``target < cum`` with
    fallback ``kbar = 2`` (805-812), ``tot <=
    NUMERICAL_ZERO => kbar = 0`` (802-803)             -> OPT2-2 driver;
  * hard3 |2>->bit sub-draw (824-833): ``gen.random()``
    if gen else the deterministic residual split, bit
    strict ``u2 < b_for_bit``, consumed ONLY when
    ``kbar == 2``                                      -> OPT2-2 driver.
Every guard is realized as a PER-SHOT MASK: a degenerate shot never poisons or
divides-by-zero the batch.

PADDING / ISOMETRY INVARIANT (prereg D-1, pinned): padding is the TRAILING channels of
every bond. (i) The CENTER tensor and every absorbed R/M factor carry exact-zero padded
channels (class (a): the represented state is unchanged). (ii) Isometry factors are
isometric ON THE UNPADDED SUBSPACE only — QR of a rank-deficient padded matrix returns
arbitrary orthonormal completions in padded columns; they multiply exact-zero rows of R
(Householder keeps zero columns/rows exactly zero), so the junk never reaches the state.
(iii) Factor columns produced by the Gram path beyond the structural rank bound are
EXPLICITLY ZEROED (partial isometry). Code asserts (i)+(iii) where the rank is known
(construction), never literal full isometry.

CENTER TABLE (prereg D-2 v3 pins; ``self.center`` is the tracked orthogonality center,
``None`` = unknown gauge):
  * canonicalize_(c)                    -> center = c;
  * apply_1site_ shared [3,3] (REQUIRED unitary, asserted)
                                        -> center unchanged, valid anywhere (incl. None);
  * apply_1site_ per-shot [B,3,3]       -> ALWAYS treated non-unitary: canonicalize to the
                                           site FIRST (the op does it); center = site;
  * site_rdm / kraus_sample_            -> center = the site;
  * local_expectation                   -> canonicalize to the window's LEFTMOST site;
                                           center = that site afterwards;
  * apply_window_recompress_            -> precondition center = window's LEFTMOST site
                                           (the op canonicalizes itself); postcondition
                                           center = window's RIGHTMOST site;
  * norm_sq / renormalize_              -> need a center (canonicalize_(0) if None).
The invariant never depends on call-site discipline: non-unitary forms enforce their
precondition by canonicalizing, not by trusting the caller.

SPLIT ROUTING (prereg D-2 op 7, v2) + DISCARDED-WEIGHT BOOK (D-3): re-splits run
LEFT->RIGHT; per split, CAP ARITHMETIC decides (class (a), batch-uniform):
  * ``cap_j >= min(m, n_cols)`` (no truncation structurally possible — at EXACT grade
    this holds at every split)  -> batched reduced QR; the split contributes the
    LITERAL 0.0 to the discarded book (STRUCTURAL, never a numerical test on computed
    eigenvalues — the batched analog of the serial ``chi >= exact_chi`` fast path,
    lines 679-686);
  * else                        -> Gram + batched ``eigh`` (hermitize ``A A^H``; eigh
    ascending; keep TOP ``cap_j`` eigenpairs; clamp ``max(lambda, 0)`` NEGATIVES-ONLY,
    no positive floor; zero-pad U columns beyond the structural rank bound — decided by
    cap arithmetic, never a numerical-rank threshold; ``M <- U^H A``); the split
    contributes its dropped-eigenvalue mass fraction (Schmidt identity, class (a)).
Batched book per op = ``1 - prod_j (1 - dropped_j)``. ``branch_weight`` = the
POST-truncation PRE-renormalization norm^2 (== the serial ``nt``, lines 692-694;
== ``Tr[E_s rho] * <psi|psi>`` only at exact grade).

LAMBDA-UNITS REGISTRY (prereg D-5): Gram eigenvalues are sigma^2 —
``NUMERICAL_ZERO = 1e-12`` in lambda units means sigma ~ 1e-6. Hence (i) the eigenvalue
clamp is negatives-only, no positive floor; (ii) padding/rank decisions are STRUCTURAL
cap arithmetic, never a threshold on computed lambdas (a threshold rank would also be
batch-heterogeneous, breaking the fixed shapes); (iii) ``from_dense``'s rank assert is a
class-(c) CONSTRUCTOR GUARD declared in lambda units: dropped-mass fraction <= 1e-12 per
split (sensitivity sigma ~ 1e-6; gate test states carry O(1) Schmidt values, far from
the boundary). ``from_dense`` is construction/tests only, NEVER a truncation path.

LEG-ORDER PINS. Multi-site operator legs correspond to ``sites`` IN THE GIVEN ORDER
(the serial/quimb ``where`` convention); implementations permute internally to ascending
window order before identity-extension. The per-shot diagonal form ``d[B, 3^w]`` uses
the SAME enumeration on its ``3^w`` axis: support trit-tuples ROW-MAJOR with ``sites[0]``
the MOST-SIGNIFICANT factor — matching the serial ``sqrt(E_s)`` diagonal build
(``_apply_sqrt_Es``, lines 664-668 comment).

GPU-first (binding): the device is taken from the input tensors; there is NO device
routing and no silent CPU fallback — this project's model compute is GPU-only.
``complex128`` throughout.
"""

from typing import Sequence

import torch

from qec_twin.numerics import NUMERICAL_ZERO

__all__ = ["BatchedMps", "bond_caps", "CDTYPE", "RDTYPE", "PHYS"]

CDTYPE = torch.complex128
RDTYPE = torch.float64
PHYS = 3  # qutrit physical dimension

#: class-(c) guard threshold (prereg D-2: unitarity assert ``||U^H U - I||_max <= 1e-12``;
#: D-5: from_dense dropped-mass constructor guard, declared in lambda units). Numerically
#: equal to NUMERICAL_ZERO; kept as the project float floor per code convention.
_GUARD = NUMERICAL_ZERO

#: declared op-set support bound (prereg D-2 ops 6/7: ``w <= 4``).
_MAX_SUPPORT = 4

#: declared window-SPREAD bound for the identity-extended window ops (ops 6/7).
#: ``_MAX_SUPPORT`` fences ``len(sites)`` ONLY; the identity-extended window spans
#: ``spread = max(sites) - min(sites) + 1`` sites, bounded only by chain length.
#: Memory terms: DENSE ``(3^spread)^2 * 16`` bytes (spread 12 => ~4.5 TB, immediate
#: OOM — the dangerous path); DIAGONAL ``3^spread * 16`` bytes (linear, fenced the
#: same for uniformity; the merged window blob also scales as ``3^spread``). The
#: serial referee never materializes a spread-sized dense operator (quimb
#: ``contract='nonlocal'`` works on the support legs). Snake-mapped gapped supports
#: at d5 can exceed this bound; the mitigation (support-leg application without dense
#: identity extension, or a diagonal ``local_expectation`` fast path) is registered
#: OPT2-2/3 territory.
_MAX_WINDOW_SPREAD = 8


def bond_caps(n: int, chi: int | None = None) -> tuple[int, ...]:
    """The fixed bond caps for the internal cuts of an ``n``-site qutrit BatchedMps.

    ``cap_k = min(3^(k+1), 3^(n-k-1), chi)`` for internal cut ``k = 0..n-2`` (prereg D-1);
    ``chi=None`` means no chi term (exact grade at every cut). Boundary caps are always 1
    and are NOT included in the returned tuple (length ``n-1``).
    """
    n = int(n)
    if n < 1:
        raise ValueError(f"bond_caps needs n >= 1 (got {n})")
    caps: list[int] = []
    for k in range(n - 1):
        c = min(PHYS ** (k + 1), PHYS ** (n - k - 1))
        if chi is not None:
            c = min(c, int(chi))
        caps.append(int(c))
    return tuple(caps)


def _full_caps(n: int, chi: int | None) -> tuple[int, ...]:
    """Caps including the boundary 1s: ``full[k]`` is the cap of the bond LEFT of site k
    (``full[0] == full[n] == 1``, length ``n+1``)."""
    return (1,) + bond_caps(n, chi) + (1,)


def _perm_to_ascending(sites: Sequence[int]) -> list[int]:
    """``p[j]`` = the GIVEN-order index of the ``j``-th smallest site (the permutation that
    reorders given-order operator legs into ascending site order)."""
    return sorted(range(len(sites)), key=lambda i: int(sites[i]))


class BatchedMps:
    """A batch of B qutrit MPS pure states with fixed zero-padded cap shapes (prereg D-1).

    Site ``k`` tensor: ``[B, cap_{k-1}, 3, cap_k]`` (boundary caps 1), ``complex128``, all
    on one device (taken from the constructing tensors; GPU-first, no CPU fallback logic).
    ``self.center`` tracks the orthogonality center (``None`` = unknown gauge); see the
    module-docstring CENTER TABLE. Shapes NEVER change during a run (structural fact
    asserted at construction: ``cap_k <= 3*cap_{k-1}`` and ``cap_{k-1} <= 3*cap_k``, so
    batched reduced QR at cap shapes returns cap-shaped factors).
    """

    def __init__(self, tensors: "list[torch.Tensor]", chi: int | None = None,
                 center: int | None = None) -> None:
        """Wrap pre-shaped site tensors (each ``[B, cap_{k-1}, 3, cap_k]``, complex128).

        Validates every shape against the D-1 cap formula for (``n``, ``chi``) and asserts
        the structural adjacent-cap facts. ``center`` declares the orthogonality center of
        the given gauge (``None`` = unknown). Construction-level entry point; prefer the
        :meth:`from_dense` / :meth:`broadcast_from_quimb` constructors.
        """
        if not tensors:
            raise ValueError("BatchedMps needs at least one site tensor")
        n = len(tensors)
        caps = _full_caps(n, chi)
        # structural adjacent-cap facts (prereg D-1; provable from the formula, asserted).
        for k in range(n):
            if not (caps[k + 1] <= PHYS * caps[k] and caps[k] <= PHYS * caps[k + 1]):
                raise AssertionError(
                    f"cap structure violated at cut {k}: caps={caps} (needs "
                    f"cap_k <= 3*cap_(k-1) and cap_(k-1) <= 3*cap_k)")
        B = int(tensors[0].shape[0])
        dev = tensors[0].device
        for k, t in enumerate(tensors):
            want = (B, caps[k], PHYS, caps[k + 1])
            if tuple(t.shape) != want:
                raise ValueError(f"site {k} tensor shape {tuple(t.shape)} != cap shape {want}")
            if t.dtype != CDTYPE:
                raise ValueError(f"site {k} dtype {t.dtype} != complex128")
            if t.device != dev:
                raise ValueError(f"site {k} device {t.device} != {dev} (one device, no routing)")
        self._t: list[torch.Tensor] = list(tensors)
        self._caps: tuple[int, ...] = caps
        self._chi: int | None = None if chi is None else int(chi)
        self._center: int | None = None if center is None else int(center)
        if self._center is not None and not (0 <= self._center < n):
            raise ValueError(f"center {center} out of range for n={n}")

    # ------------------------------------------------------------------ #
    # basic properties                                                    #
    # ------------------------------------------------------------------ #
    @property
    def n(self) -> int:
        """Number of sites."""
        return len(self._t)

    @property
    def B(self) -> int:
        """Batch (shot) dimension."""
        return int(self._t[0].shape[0])

    @property
    def device(self) -> torch.device:
        return self._t[0].device

    @property
    def caps(self) -> tuple[int, ...]:
        """Full cap tuple including boundary 1s: ``caps[k]`` = cap of the bond LEFT of
        site ``k`` (length ``n+1``)."""
        return self._caps

    @property
    def center(self) -> int | None:
        """The tracked orthogonality center (``None`` = unknown gauge)."""
        return self._center

    @property
    def tensors(self) -> tuple[torch.Tensor, ...]:
        """The site tensors (read view; mutate only through the ops)."""
        return tuple(self._t)

    def copy(self) -> "BatchedMps":
        """Deep copy (fresh tensor storage; center preserved)."""
        out = BatchedMps.__new__(BatchedMps)
        out._t = [t.clone() for t in self._t]
        out._caps = self._caps
        out._chi = self._chi
        out._center = self._center
        return out

    # ------------------------------------------------------------------ #
    # constructors (prereg D-2 op 1)                                      #
    # ------------------------------------------------------------------ #
    @classmethod
    def from_dense(cls, psi: torch.Tensor, chi: int | None = None) -> "BatchedMps":
        """Exact sequential split of dense states ``psi[B, 3^n]`` (referee: quimb
        ``from_dense``; engine row-major, site-0 = MSB — mps_forward.py line 389).

        CONSTRUCTOR / TESTS ONLY, NEVER a truncation path (prereg D-2 op 1 + D-5): every
        split carries a class-(c) rank guard declared in LAMBDA units — dropped-mass
        fraction <= 1e-12 per split (sensitivity sigma ~ 1e-6) — and RAISES on violation
        instead of truncating. Splits run left->right via Gram + batched eigh (eigenvector
        phases are gauge; G-OP-1 compares dense reconstructions). Postcondition: center =
        site ``n-1`` (left factors are partial isometries; padded factor columns beyond
        the kept rank are EXPLICITLY zeroed — invariant (iii) — so absorbed M rows in the
        padded channels are exact zeros — invariant (i), asserted).
        """
        if psi.dim() != 2:
            raise ValueError(f"psi must be [B, 3^n] (got {tuple(psi.shape)})")
        B, dim = int(psi.shape[0]), int(psi.shape[1])
        n, d = 0, 1
        while d < dim:
            d *= PHYS
            n += 1
        if d != dim or n < 1:
            raise ValueError(f"dense dim {dim} is not a power of 3")
        psi = psi.to(CDTYPE)
        dev = psi.device
        caps = _full_caps(n, chi)
        tensors: list[torch.Tensor] = []
        if n == 1:
            tensors.append(psi.reshape(B, 1, PHYS, 1))
            return cls(tensors, chi=chi, center=0)
        cur = psi.reshape(B, 1, dim)  # [B, lcap(actual, padded as we go), 3^(n-k)]
        for k in range(n - 1):
            lcap = caps[k]
            rem = dim // (PHYS ** (k + 1))  # 3^(n-k-1)
            m = lcap * PHYS
            A = cur.reshape(B, m, rem)
            cap_t = caps[k + 1]
            r_struct = min(m, rem)
            k_keep = min(cap_t, r_struct)
            Gm = A @ A.mH
            Gm = 0.5 * (Gm + Gm.mH)  # hermitize
            lam, U = torch.linalg.eigh(Gm)  # ascending
            keep = lam[:, m - k_keep:].clamp(min=0.0)   # negatives-only clamp
            drop = lam[:, : m - k_keep].clamp(min=0.0)
            tot = keep.sum(dim=1) + drop.sum(dim=1)
            frac = torch.where(tot > NUMERICAL_ZERO,
                               drop.sum(dim=1) / tot.clamp_min(NUMERICAL_ZERO),
                               torch.zeros_like(tot))
            worst = float(frac.max()) if frac.numel() else 0.0
            if worst > _GUARD:
                raise ValueError(
                    f"from_dense split {k}: dropped-mass fraction {worst:.3e} > 1e-12 "
                    f"(lambda units) — state rank exceeds caps {caps}; from_dense is a "
                    f"constructor, never a truncation path (prereg D-2 op 1 / D-5)")
            Uk = U[:, :, m - k_keep:].flip(-1)  # descending eigenvalue order
            if k_keep < cap_t:
                # invariant (iii): explicit zero-padding beyond the STRUCTURAL rank bound
                # (cap arithmetic; never a numerical-rank threshold on computed lambdas).
                Up = torch.zeros((B, m, cap_t), dtype=CDTYPE, device=dev)
                Up[:, :, :k_keep] = Uk
            else:
                Up = Uk
            M = Up.mH @ A  # [B, cap_t, rem]
            if k_keep < cap_t:
                # invariant (i): the absorbed factor's padded channels are exact zeros
                # (zero U columns times A) — asserted where the rank is known.
                if bool((M[:, k_keep:, :] != 0).any()):
                    raise AssertionError("padding invariant (i) violated in from_dense")
            tensors.append(Up.reshape(B, lcap, PHYS, cap_t))
            cur = M
        tensors.append(cur.reshape(B, caps[n - 1], PHYS, 1))
        return cls(tensors, chi=chi, center=n - 1)

    @classmethod
    def broadcast_from_quimb(cls, mps, B: int, chi: int | None = None) -> "BatchedMps":
        """Broadcast one quimb ``MatrixProductState`` (torch-cuda arrays) to a B-shot batch.

        DUCK-TYPED — this module never imports quimb (prereg: quimb only in tests). The
        object must expose ``permute_arrays(shape)`` and ``arrays`` (quimb 1.14
        ``TensorNetwork1DFlat`` API). EXPECTED INDEX ORDER: quimb's MPS default
        ``shape='lrp'`` — interior site ``(left_bond, right_bond, phys)``, first site
        ``(right_bond, phys)``, last site ``(left_bond, phys)``. This matches how the
        serial arm builds its MPS (``MatrixProductState.from_dense(arr, dims=[3]*n)`` at
        mps_forward.py line 401 and ``MPS_product_state`` at line 432 — both construct
        with the quimb default 'lrp'); because per-tensor axis order can DRIFT under
        subsequent ``gate_`` calls, ``permute_arrays('lrp')`` is called FIRST to re-pin
        the convention before reading ``arrays`` (never assumed).

        Arrays must already be torch tensors on one device (the serial arm's
        ``apply_to_arrays(torch.as_tensor(..., device=cuda))`` state); the batch is
        materialized by broadcast + clone. Bond dims must fit the (``n``, ``chi``) caps —
        NEVER a truncation path (raises otherwise). Zero-padding fills the trailing
        channels (the D-1 padding invariant holds by construction). Postcondition:
        center = ``None`` (quimb gauge unknown).
        """
        perm = getattr(mps, "permute_arrays", None)
        if not callable(perm):
            raise TypeError(
                "broadcast_from_quimb needs a quimb-1.14-like MPS exposing "
                "permute_arrays('lrp') to pin the per-tensor index order")
        perm("lrp")
        arrs = getattr(mps, "arrays")
        if callable(arrs):  # duck-type: property in quimb 1.14, method elsewhere
            arrs = arrs()
        arrs = list(arrs)
        n = len(arrs)
        if n < 1:
            raise ValueError("empty MPS")
        B = int(B)
        if B < 1:
            raise ValueError(f"B must be >= 1 (got {B})")
        norm3: list[torch.Tensor] = []  # each -> (l, p, r), unpadded
        for k, a in enumerate(arrs):
            if not torch.is_tensor(a):
                raise TypeError(
                    f"site {k} array is {type(a).__name__}, not a torch tensor — the "
                    f"contract expects the serial arm's torch-cuda-backed quimb MPS")
            t = a.to(CDTYPE)
            if n == 1:
                t = t.reshape(1, PHYS, 1)
            elif k == 0:          # 'lrp' with no left bond: (r, p) -> (1, p, r)
                t = t.permute(1, 0).unsqueeze(0)
            elif k == n - 1:      # 'lrp' with no right bond: (l, p) -> (l, p, 1)
                t = t.unsqueeze(-1)
            else:                 # (l, r, p) -> (l, p, r)
                t = t.permute(0, 2, 1)
            if int(t.shape[1]) != PHYS:
                raise ValueError(f"site {k} physical dim {int(t.shape[1])} != 3")
            norm3.append(t.contiguous())
        caps = _full_caps(n, chi)
        dev = norm3[0].device
        tensors: list[torch.Tensor] = []
        for k, t in enumerate(norm3):
            dl, _, dr = int(t.shape[0]), PHYS, int(t.shape[2])
            if dl > caps[k] or dr > caps[k + 1]:
                raise ValueError(
                    f"site {k} bond dims ({dl},{dr}) exceed caps "
                    f"({caps[k]},{caps[k + 1]}) — broadcast_from_quimb is never a "
                    f"truncation path")
            out = torch.zeros((B, caps[k], PHYS, caps[k + 1]), dtype=CDTYPE, device=dev)
            out[:, :dl, :, :dr] = t.unsqueeze(0)  # broadcast over B; trailing padding = 0
            tensors.append(out)
        return cls(tensors, chi=chi, center=None)

    def to_dense(self) -> torch.Tensor:
        """Contract to dense ``[B, 3^n]`` engine-basis states (site 0 = MSB; referee: quimb
        ``to_dense``). TEST-SCALE ONLY. Exact in any gauge (no canonicalization needed:
        padded-channel junk in isometry completions multiplies exact-zero padded rows of
        the downstream tensors — the trailing-padding invariant)."""
        cur = self._t[0].reshape(self.B, PHYS, self._caps[1])
        D = PHYS
        for k in range(1, self.n):
            T = self._t[k]
            cur = torch.einsum("bdr,brps->bdps", cur, T)
            D *= PHYS
            cur = cur.reshape(self.B, D, T.shape[-1])
        return cur.reshape(self.B, D)

    # ------------------------------------------------------------------ #
    # canonical form + norm (prereg D-2 op 2)                             #
    # ------------------------------------------------------------------ #
    def _shift_right(self, k: int) -> None:
        """Left-QR site ``k``; absorb R into site ``k+1`` (center k -> k+1). Batched
        reduced QR at cap shapes is shape-preserving (``cap_k <= 3*cap_{k-1}``)."""
        T = self._t[k]
        B, l, _, r = T.shape
        Q, R = torch.linalg.qr(T.reshape(B, l * PHYS, r), mode="reduced")
        if int(Q.shape[-1]) != int(r):  # structural: min(3*l, r) == r
            raise AssertionError(f"QR at site {k}: reduced rank {int(Q.shape[-1])} != cap {int(r)}")
        self._t[k] = Q.reshape(B, l, PHYS, r)
        self._t[k + 1] = torch.einsum("bij,bjpr->bipr", R, self._t[k + 1])

    def _shift_left(self, k: int) -> None:
        """Right-QR site ``k``; absorb R^H into site ``k-1`` (center k -> k-1)."""
        T = self._t[k]
        B, l, _, r = T.shape
        A = T.reshape(B, l, PHYS * r)
        Q, R = torch.linalg.qr(A.mH, mode="reduced")  # A^H = Q R  =>  A = R^H Q^H
        if int(Q.shape[-1]) != int(l):  # structural: min(3*r, l) == l
            raise AssertionError(f"QR at site {k}: reduced rank {int(Q.shape[-1])} != cap {int(l)}")
        self._t[k] = Q.mH.reshape(B, l, PHYS, r)
        self._t[k - 1] = torch.einsum("blpi,bij->blpj", self._t[k - 1], R.mH)

    def canonicalize_(self, center: int) -> "BatchedMps":
        """Move (or establish) the orthogonality center at ``center`` via batched reduced
        QR sweeps (referee: the canonical form quimb's ``local_expectation_canonical``
        maintains for the serial reads). Incremental when the current center is known;
        full two-sided sweep from an unknown gauge. Shapes never change (D-1)."""
        c = int(center)
        if not (0 <= c < self.n):
            raise ValueError(f"center {center} out of range for n={self.n}")
        if self._center is None:
            for k in range(0, c):
                self._shift_right(k)
            for k in range(self.n - 1, c, -1):
                self._shift_left(k)
        elif self._center < c:
            for k in range(self._center, c):
                self._shift_right(k)
        elif self._center > c:
            for k in range(self._center, c, -1):
                self._shift_left(k)
        self._center = c
        return self

    def norm_sq(self) -> torch.Tensor:
        """``<psi|psi>`` per shot, ``[B]`` float64 (referee: ``_norm_sq``). A READ: uses
        the canonical center (canonicalize_(0) first if the gauge is unknown) — the norm
        is then the center tensor's Frobenius norm^2 (all other tensors isometric on the
        unpadded subspace; padded channels carry zeros into the center)."""
        if self._center is None:
            self.canonicalize_(0)
        T = self._t[self._center]
        return (T.conj() * T).real.sum(dim=(1, 2, 3)).to(RDTYPE)

    def _scale_center_(self, ns: torch.Tensor) -> None:
        """Scale the center tensor by ``1/sqrt(ns)`` PER SHOT, skipping shots with
        ``ns <= NUMERICAL_ZERO`` (the serial ``_renormalize`` guard, lines 513-515,
        realized as a per-shot mask — a degenerate shot never divides the batch)."""
        inv = torch.where(ns > NUMERICAL_ZERO,
                          1.0 / torch.sqrt(ns.clamp_min(NUMERICAL_ZERO)),
                          torch.ones_like(ns))
        c = self._center
        if c is None:
            raise AssertionError("_scale_center_ requires an established center")
        self._t[c] = self._t[c] * inv.view(-1, 1, 1, 1).to(CDTYPE)

    def renormalize_(self) -> torch.Tensor:
        """Renormalize every shot to unit norm; return the PRE-scale ``<psi|psi>`` ``[B]``
        (the branch weights — referee: ``_renormalize``, incl. its ``ns <=
        NUMERICAL_ZERO`` skip as a per-shot mask)."""
        ns = self.norm_sq()
        self._scale_center_(ns)
        return ns

    # ------------------------------------------------------------------ #
    # 1-site ops (prereg D-2 ops 3-5)                                     #
    # ------------------------------------------------------------------ #
    def apply_1site_(self, U: torch.Tensor, site: int) -> "BatchedMps":
        """Apply a 1-site operator (referee: ``_apply_gate``). Never renormalizes.

        * shared ``[3,3]``: REQUIRED unitary — asserted ``||U^H U - I||_max <= 1e-12``
          (class (c) guard, prereg D-2 v3); center unchanged, valid anywhere (a 1-site
          unitary preserves every isometry condition).
        * per-shot ``[B,3,3]``: ALWAYS treated as non-unitary (the Kraus-gather /
          projector / terminal-collapse form) — canonicalize to the site FIRST (the op
          does it; the invariant never depends on call-site discipline); center = site.
        """
        s = int(site)
        if not (0 <= s < self.n):
            raise ValueError(f"site {site} out of range for n={self.n}")
        U = U.to(CDTYPE)
        if U.dim() == 2:
            if tuple(U.shape) != (PHYS, PHYS):
                raise ValueError(f"shared 1-site operator must be [3,3] (got {tuple(U.shape)})")
            eye = torch.eye(PHYS, dtype=CDTYPE, device=U.device)
            resid = float((U.mH @ U - eye).abs().max())
            if resid > _GUARD:
                raise AssertionError(
                    f"shared [3,3] apply_1site_ form is REQUIRED unitary "
                    f"(||U^H U - I||_max = {resid:.3e} > 1e-12); pass the per-shot "
                    f"[B,3,3] form for non-unitary operators (prereg D-2 v3)")
            self._t[s] = torch.einsum("pq,blqr->blpr", U, self._t[s])
            # center unchanged (valid anywhere, incl. unknown gauge).
        elif U.dim() == 3:
            if tuple(U.shape) != (self.B, PHYS, PHYS):
                raise ValueError(
                    f"per-shot 1-site operator must be [B,3,3]=[{self.B},3,3] "
                    f"(got {tuple(U.shape)})")
            self.canonicalize_(s)  # ALWAYS non-unitary: enforce center = site.
            self._t[s] = torch.einsum("bpq,blqr->blpr", U, self._t[s])
        else:
            raise ValueError(f"1-site operator must be [3,3] or [B,3,3] (got dim {U.dim()})")
        return self

    def site_rdm(self, site: int, normalized: bool = False) -> torch.Tensor:
        """The 1-site reduced density matrix ``[B,3,3]`` at the (enforced) center
        (referee: the serial ``local_expectation_canonical`` reads — ``_leak_sample``'s
        RDM branch norms, ``_site_population``). Default ``normalized=False`` is the
        serial BRANCH-NORM convention (trace = ``<psi|psi>``). ``normalized=True``
        divides by the trace with a per-shot ``<= NUMERICAL_ZERO`` mask (degenerate
        shots are left unscaled — their entries are already ~0). Center = site after."""
        s = int(site)
        self.canonicalize_(s)
        T = self._t[s]
        rho = torch.einsum("blpr,blqr->bpq", T, T.conj())
        if normalized:
            tr = torch.einsum("bpp->b", rho).real
            inv = torch.where(tr > NUMERICAL_ZERO,
                              1.0 / tr.clamp_min(NUMERICAL_ZERO),
                              torch.ones_like(tr))
            rho = rho * inv.view(-1, 1, 1).to(CDTYPE)
        return rho

    def kraus_sample_(self, kraus: torch.Tensor, site: int,
                      u: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """MCWF Kraus-sample ``kraus[K,3,3]`` on ``site`` with per-shot uniforms ``u[B]``
        (referee: ``_leak_sample`` — bit-level match on a shared ``u`` stream).

        Mirrors the serial math EXACTLY: ``p_k = Tr[K_k^H K_k rho]`` from the UNNORMALIZED
        1-site RDM (== the branch norms ``||K_k psi||^2``); selection by the serial
        cumulative rule — the FIRST ``k`` with ``u * tot <= cumsum_k`` (``<=``, serial
        line 584), fallback ``K-1`` — realized as an explicit min-index construction
        (version-proof; never relies on argmax tie-breaking); gather the selected Kraus
        per shot; apply (per-shot non-unitary form; center = site); renormalize by
        ``pk[b, sel]`` with the ``<= NUMERICAL_ZERO`` per-shot skip mask (serial
        ``_renormalize(norm_sq=pk[sel])``, lines 513-515/588).

        Returns ``(sel[B] int64, pk[B,K] float64)``.
        """
        if kraus.dim() != 3 or tuple(kraus.shape[1:]) != (PHYS, PHYS):
            raise ValueError(f"kraus must be [K,3,3] (got {tuple(kraus.shape)})")
        u = u.reshape(-1).to(RDTYPE)
        if int(u.shape[0]) != self.B:
            raise ValueError(f"u must be [B]=[{self.B}] (got {tuple(u.shape)})")
        kraus = kraus.to(CDTYPE)
        K = int(kraus.shape[0])
        rho = self.site_rdm(int(site), normalized=False)  # center -> site
        KhK = kraus.mH @ kraus  # [K,3,3]
        pk = torch.einsum("kpq,bqp->bk", KhK, rho).real.to(RDTYPE)  # Tr[K^H K rho]
        tot = pk.sum(dim=1)
        target = u * tot
        cum = torch.cumsum(pk, dim=1)
        hit = target.unsqueeze(1) <= cum  # cumulative <= rule (serial line 584)
        idx = torch.arange(K, device=pk.device).unsqueeze(0).expand_as(hit)
        cand = torch.where(hit, idx, torch.full_like(idx, K))
        sel = cand.min(dim=1).values.clamp(max=K - 1)  # first hit; fallback K-1
        self.apply_1site_(kraus[sel], int(site))  # per-shot form; center = site
        pk_sel = pk.gather(1, sel.unsqueeze(1)).squeeze(1)
        self._scale_center_(pk_sel)  # per-shot NUMERICAL_ZERO mask (serial 513-515)
        return sel, pk

    # ------------------------------------------------------------------ #
    # window machinery (shared by ops 6 + 7)                              #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _permute_dense_to_asc(G: torch.Tensor, sites: "tuple[int, ...]") -> torch.Tensor:
        """Reorder a dense ``[3^w, 3^w]`` operator whose legs follow ``sites`` IN THE
        GIVEN ORDER (the serial/quimb ``where`` convention) into ascending site order."""
        w = len(sites)
        p = _perm_to_ascending(sites)
        if p == list(range(w)):
            return G
        t = G.reshape([PHYS] * (2 * w))
        perm = p + [w + i for i in p]
        return t.permute(perm).reshape(G.shape[0], G.shape[1])

    @staticmethod
    def _permute_diag_to_asc(d: torch.Tensor, sites: "tuple[int, ...]",
                             batched: bool) -> torch.Tensor:
        """Reorder a diagonal vector (``[3^w]`` or per-shot ``[B, 3^w]``) into ascending
        site order. The ``3^w`` axis enumerates support trit-tuples ROW-MAJOR with
        ``sites[0]`` the MOST-SIGNIFICANT factor (the pinned enumeration — the serial
        ``sqrt(E_s)`` diagonal build convention, mps_forward.py lines 664-668)."""
        w = len(sites)
        p = _perm_to_ascending(sites)
        if p == list(range(w)):
            return d
        pre = 1 if batched else 0
        shape = list(d.shape[:pre]) + [PHYS] * w
        t = d.reshape(shape)
        perm = list(range(pre)) + [pre + i for i in p]
        return t.permute(perm).reshape(*d.shape)

    @staticmethod
    def _identity_extended_dense(G_asc: torch.Tensor, supp_asc: "list[int]",
                                 window: "list[int]") -> torch.Tensor:
        """Identity-extend an ascending-ordered dense support operator onto the full
        contiguous window (exact, class (a) — prereg D-2 op 6): interleave ``I`` on the
        gap sites and reorder the legs into window order. Returns ``[3^w_win, 3^w_win]``.

        MEMORY (declared bound): the dense result is ``(3^spread)^2 * 16`` bytes with
        ``spread = len(window)`` — callers MUST fence ``spread <= _MAX_WINDOW_SPREAD``
        (both public call paths do); see the ``_MAX_WINDOW_SPREAD`` registry entry."""
        w = len(supp_asc)
        supp_set = set(supp_asc)
        gaps = [s for s in window if s not in supp_set]
        t = G_asc.reshape([PHYS] * (2 * w))
        eye = torch.eye(PHYS, dtype=G_asc.dtype, device=G_asc.device)
        for _ in gaps:
            t = t.unsqueeze(-1).unsqueeze(-1) * eye  # appends (ket_gap, bra_gap) legs
        ket: dict[int, int] = {}
        bra: dict[int, int] = {}
        for i, s in enumerate(supp_asc):
            ket[s] = i
            bra[s] = w + i
        for g, s in enumerate(gaps):
            ket[s] = 2 * w + 2 * g
            bra[s] = 2 * w + 2 * g + 1
        perm = [ket[s] for s in window] + [bra[s] for s in window]
        D = PHYS ** len(window)
        return t.permute(perm).reshape(D, D)

    @staticmethod
    def _identity_extended_diag(d_asc: torch.Tensor, supp_asc: "list[int]",
                                window: "list[int]", batched: bool) -> torch.Tensor:
        """Identity-extend an ascending-ordered diagonal (``[3^w]`` or ``[B, 3^w]``) onto
        the window: gap sites contribute the constant 1 (the diagonal of ``I``). The
        window axis enumeration is ROW-MAJOR with the window's leftmost site the MSB
        (the same convention as the dense form's kron order)."""
        w = len(supp_asc)
        supp_set = set(supp_asc)
        gaps = [s for s in window if s not in supp_set]
        pre = 1 if batched else 0
        t = d_asc.reshape(list(d_asc.shape[:pre]) + [PHYS] * w)
        ones3 = torch.ones(PHYS, dtype=d_asc.dtype, device=d_asc.device)
        for _ in gaps:
            t = t.unsqueeze(-1) * ones3
        leg: dict[int, int] = {}
        for i, s in enumerate(supp_asc):
            leg[s] = pre + i
        for g, s in enumerate(gaps):
            leg[s] = pre + w + g
        perm = list(range(pre)) + [leg[s] for s in window]
        D = PHYS ** len(window)
        out_shape = list(d_asc.shape[:pre]) + [D]
        return t.permute(perm).reshape(out_shape)

    def _merge_window(self, lo: int, hi: int) -> torch.Tensor:
        """Contract sites ``lo..hi`` into the window blob ``[B, cap_{lo-1}, 3^w_win,
        cap_hi]`` (the D-2 window sandwich; memory bound declared in D-5)."""
        blob = self._t[lo]
        B, lcap = int(blob.shape[0]), int(blob.shape[1])
        D = PHYS
        blob = blob.reshape(B, lcap, D, blob.shape[-1])
        for s in range(lo + 1, hi + 1):
            T = self._t[s]
            blob = torch.einsum("bldr,brps->bldps", blob, T)
            D *= PHYS
            blob = blob.reshape(B, lcap, D, T.shape[-1])
        return blob

    # ------------------------------------------------------------------ #
    # multi-site expectation (prereg D-2 op 6)                            #
    # ------------------------------------------------------------------ #
    def local_expectation(self, G: torch.Tensor, sites: "Sequence[int]",
                          normalized: bool = True) -> torch.Tensor:
        """``<psi| G |psi>`` per shot, ``[B]`` float64 (referee: ``_parity_expectation`` /
        ``_site_population`` — the serial ``local_expectation_canonical`` reads).

        ``G`` is shared ``[3^w, 3^w]`` with ``w <= 4``; its LEGS correspond to ``sites``
        IN THE GIVEN ORDER (the serial/quimb ``where`` convention) and are permuted
        internally to ascending. NON-CONTIGUOUS supports are handled by the exact
        identity-extended window (class (a)). A READ: canonicalizes to the window's
        LEFTMOST site first (v3 pin, matching the window op's precondition); center =
        that site afterwards. ``normalized=True`` (the serial default for expectation
        reads) divides by ``<psi|psi>`` with the per-shot ``<= NUMERICAL_ZERO`` mask;
        ``normalized=False`` returns the unnormalized sandwich (the branch-norm
        convention). Returns the REAL part (Hermitian observables; the serial referee
        takes ``.real``).

        MEMORY (declared bound): the identity-extended dense window operator is
        ``(3^spread)^2 * 16`` bytes with ``spread = max(sites) - min(sites) + 1`` —
        fenced by ``_MAX_WINDOW_SPREAD`` (see its registry entry; ``_MAX_SUPPORT``
        bounds ``len(sites)`` only, not the spread)."""
        sites = tuple(int(s) for s in sites)
        w = len(sites)
        if not (1 <= w <= _MAX_SUPPORT):
            raise ValueError(f"support width {w} outside the declared op set (1..{_MAX_SUPPORT})")
        if len(set(sites)) != w:
            raise ValueError(f"duplicate sites in {sites}")
        if any(not (0 <= s < self.n) for s in sites):
            raise ValueError(f"sites {sites} out of range for n={self.n}")
        spread = max(sites) - min(sites) + 1
        if spread > _MAX_WINDOW_SPREAD:
            raise ValueError(
                f"window spread {spread} (= max(sites)-min(sites)+1 for sites {sites}) "
                f"exceeds _MAX_WINDOW_SPREAD={_MAX_WINDOW_SPREAD}: the identity-extended "
                f"dense window operator costs (3^spread)^2 * 16 bytes (~4.5 TB at spread "
                f"12; the diagonal form is 3^spread * 16 bytes) — _MAX_SUPPORT fences "
                f"len(sites) only, not the spread, and snake-mapped gapped supports at "
                f"d5 can exceed it. Mitigation (support-leg application without dense "
                f"identity extension, or a diagonal local_expectation fast path) is "
                f"registered OPT2-2/3 territory")
        D_supp = PHYS ** w
        if G.dim() != 2 or tuple(G.shape) != (D_supp, D_supp):
            raise ValueError(f"G must be [3^w,3^w]=[{D_supp},{D_supp}] (got {tuple(G.shape)})")
        G = G.to(CDTYPE)
        lo, hi = min(sites), max(sites)
        window = list(range(lo, hi + 1))
        supp_asc = sorted(sites)
        G_asc = self._permute_dense_to_asc(G, sites)
        G_win = self._identity_extended_dense(G_asc, supp_asc, window)
        self.canonicalize_(lo)  # every read canonicalizes first (D-1); center = lo after.
        blob = self._merge_window(lo, hi)
        val = torch.einsum("bldr,de,bler->b", blob.conj(), G_win, blob)
        if normalized:
            ns = (blob.conj() * blob).real.sum(dim=(1, 2, 3))
            inv = torch.where(ns > NUMERICAL_ZERO,
                              1.0 / ns.clamp_min(NUMERICAL_ZERO),
                              torch.ones_like(ns))
            val = val * inv.to(CDTYPE)
        return val.real.to(RDTYPE)

    # ------------------------------------------------------------------ #
    # windowed gate + recompression (prereg D-2 op 7)                     #
    # ------------------------------------------------------------------ #
    def apply_window_recompress_(self, G: torch.Tensor, sites: "Sequence[int]",
                                 diagonal: bool) -> tuple[torch.Tensor, torch.Tensor]:
        """Apply a multi-site operator on ``sites`` and re-split the window at cap shapes
        (referee: ``_apply_sqrt_Es`` / codestate ``_project``). Renormalizes internally.

        G FORMS (prereg D-2 v4):
          * shared dense ``[3^w, 3^w]`` (``diagonal=False``) — general matmul path;
          * shared diagonal ``[3^w, 3^w]`` (``diagonal=True``) — fast path, guarded by an
            assert that the off-diagonal mass is EXACTLY 0 (structural, not floored);
          * per-shot diagonal ``d[B, 3^w]`` (``diagonal=True``) — the diagonal gather
            analog of apply_1site_'s ``[B,3,3]``, required because the Born-stab
            composition's ``sqrt(E_s)`` is a per-shot-VALUED diagonal (sbit sampled per
            shot; serial lines 666-676). LEG-ORDER PIN: its ``3^w`` axis uses the SAME
            enumeration as the dense form's legs — support trit-tuples ROW-MAJOR with
            ``sites[0]`` the MOST-SIGNIFICANT factor, matching the serial diagonal build
            (mps_forward.py lines 664-668 comment).
          A per-shot NON-diagonal window form is deliberately UNREGISTERED.
          Shape-dispatch pin: a square ``[3^w, 3^w]`` input is ALWAYS read as the shared
          form. In the (test-scale-only) collision ``B == 3^w`` the safety net covers the
          ``diagonal=True`` half ONLY: a mis-passed per-shot ``d`` read as a shared dense
          matrix trips the exact off-diagonal-zero assert. With ``diagonal=False`` a
          square input is ALWAYS read as shared with NO guard — a ``(3^w, 3^w)`` array
          is genuinely indistinguishable from the shared dense form, and the corrective
          ``[B, 3^w]``+``diagonal=False`` ValueError below is unreachable in the
          collision. This is a documented test-scale-only ambiguity (production ``B``
          never equals ``3^w``); callers of the per-shot form must always pass
          ``diagonal=True`` (required for that form anyway).

        LEG ORDER: G's legs correspond to ``sites`` IN THE GIVEN ORDER; permuted
        internally to ascending. Non-contiguous supports are identity-extended (exact;
        memory bound: dense ``(3^spread)^2 * 16`` bytes / diagonal ``3^spread * 16``
        bytes with ``spread = max(sites) - min(sites) + 1``, fenced by
        ``_MAX_WINDOW_SPREAD`` — see its registry entry).

        CENTER TABLE: precondition center = the window's LEFTMOST site (the op
        canonicalizes ITSELF — never trusts the caller); postcondition center = the
        window's RIGHTMOST site.

        SPLIT ROUTING (v2, per split, LEFT->RIGHT, cap arithmetic — class (a),
        batch-uniform): ``cap_j >= min(m, n_cols)`` routes batched reduced QR
        (backward-stable; the discard set is structurally EMPTY -> the split contributes
        the LITERAL 0.0 to the book, prereg D-3 — the batched analog of the serial
        ``chi >= exact_chi`` fast path, lines 679-686); otherwise Gram + batched eigh
        (hermitize ``A A^H``; ascending eigh; keep TOP ``cap_j``; NEGATIVES-ONLY clamp
        ``max(lambda, 0)``, no positive floor; structural zero-padding by cap arithmetic;
        ``M <- U^H A``), contributing its dropped-eigenvalue mass fraction (Schmidt
        identity). Per-op book: ``discarded = 1 - prod_j (1 - dropped_j)``, per shot.

        Returns ``(discarded[B], branch_weight[B])`` float64. ``branch_weight`` is the
        POST-truncation PRE-renormalization norm^2 (== the serial ``nt``, lines 692-694;
        == ``Tr[E_s rho] * <psi|psi>`` only at exact grade). The state is then
        renormalized with the per-shot ``<= NUMERICAL_ZERO`` skip mask.
        """
        sites = tuple(int(s) for s in sites)
        w = len(sites)
        if not (1 <= w <= _MAX_SUPPORT):
            raise ValueError(f"support width {w} outside the declared op set (1..{_MAX_SUPPORT})")
        if len(set(sites)) != w:
            raise ValueError(f"duplicate sites in {sites}")
        if any(not (0 <= s < self.n) for s in sites):
            raise ValueError(f"sites {sites} out of range for n={self.n}")
        spread = max(sites) - min(sites) + 1
        if spread > _MAX_WINDOW_SPREAD:
            raise ValueError(
                f"window spread {spread} (= max(sites)-min(sites)+1 for sites {sites}) "
                f"exceeds _MAX_WINDOW_SPREAD={_MAX_WINDOW_SPREAD}: the identity-extended "
                f"dense window operator costs (3^spread)^2 * 16 bytes (~4.5 TB at spread "
                f"12; the diagonal form is 3^spread * 16 bytes) — _MAX_SUPPORT fences "
                f"len(sites) only, not the spread, and snake-mapped gapped supports at "
                f"d5 can exceed it. Mitigation (support-leg application without dense "
                f"identity extension, or a diagonal local_expectation fast path) is "
                f"registered OPT2-2/3 territory")
        D_supp = PHYS ** w
        B = self.B
        lo, hi = min(sites), max(sites)
        window = list(range(lo, hi + 1))
        supp_asc = sorted(sites)
        w_win = len(window)
        dev = self.device

        # ---- form dispatch (square -> shared, documented pin) ----
        mode: str
        d_win: torch.Tensor | None = None
        G_win: torch.Tensor | None = None
        if G.dim() == 2 and tuple(G.shape) == (D_supp, D_supp):
            G = G.to(CDTYPE)
            G_asc = self._permute_dense_to_asc(G, sites)
            if diagonal:
                # STRUCTURAL off-diagonal-zero assert (exactly 0, not floored — D-2 op 7).
                diag_part = torch.diagonal(G_asc)
                off = G_asc - torch.diag(diag_part)
                if bool((off != 0).any()):
                    raise AssertionError(
                        "diagonal=True but G has EXACTLY-nonzero off-diagonal entries "
                        "(the fast-path guard is structural, never floored)")
                d_asc = diag_part
                d_win = self._identity_extended_diag(d_asc, supp_asc, window, batched=False)
                mode = "diag_shared"
            else:
                G_win = self._identity_extended_dense(G_asc, supp_asc, window)
                mode = "dense"
        elif G.dim() == 2 and tuple(G.shape) == (B, D_supp):
            if not diagonal:
                raise ValueError(
                    "a per-shot NON-diagonal window form is deliberately UNREGISTERED "
                    "(prereg D-2 v4); pass diagonal=True with d[B,3^w]")
            d_asc = self._permute_diag_to_asc(G.to(CDTYPE), sites, batched=True)
            d_win = self._identity_extended_diag(d_asc, supp_asc, window, batched=True)
            mode = "diag_pershot"
        else:
            raise ValueError(
                f"G must be shared [3^w,3^w]=[{D_supp},{D_supp}] or per-shot diagonal "
                f"[B,3^w]=[{B},{D_supp}] (got {tuple(G.shape)}, diagonal={diagonal})")

        # ---- precondition: center at the window's leftmost site (op does it itself) ----
        self.canonicalize_(lo)
        blob = self._merge_window(lo, hi)  # [B, cap_{lo-1}, 3^w_win, cap_hi]

        # ---- apply ----
        if mode == "dense":
            blob = torch.einsum("de,bler->bldr", G_win, blob)
        elif mode == "diag_shared":
            blob = blob * d_win.view(1, 1, -1, 1)
        else:  # diag_pershot
            blob = blob * d_win.view(B, 1, -1, 1)

        # ---- re-split LEFT->RIGHT with the v2 routing rule ----
        one_minus = torch.ones(B, dtype=RDTYPE, device=dev)
        r_cap = self._caps[hi + 1]
        Drem = PHYS ** w_win
        cur = blob  # [B, caps[s], Drem, r_cap] as the loop walks
        for s in range(lo, hi):
            lcap = self._caps[s]
            m = lcap * PHYS
            Drem //= PHYS
            ncols = Drem * r_cap
            A = cur.reshape(B, m, ncols)
            cap_t = self._caps[s + 1]
            if cap_t >= min(m, ncols):
                # QR route: cap arithmetic PROVES no truncation possible at this split
                # (class (a), batch-uniform). Discarded contribution: LITERAL 0.0 (D-3
                # structural book — never a numerical test on computed eigenvalues).
                Q, R = torch.linalg.qr(A, mode="reduced")
                k = int(Q.shape[-1])  # min(m, ncols) <= cap_t
                if k < cap_t:
                    Qp = torch.zeros((B, m, cap_t), dtype=CDTYPE, device=dev)
                    Qp[:, :, :k] = Q
                    Rp = torch.zeros((B, cap_t, ncols), dtype=CDTYPE, device=dev)
                    Rp[:, :k, :] = R
                else:
                    Qp, Rp = Q, R
                self._t[s] = Qp.reshape(B, lcap, PHYS, cap_t)
                cur = Rp.reshape(B, cap_t, Drem, r_cap)
            else:
                # Gram route: hermitized A A^H; ascending eigh; keep TOP cap_t eigenpairs
                # (descending order in the kept factor); NEGATIVES-ONLY clamp; structural
                # zero-padding by CAP ARITHMETIC (never a numerical-rank threshold —
                # D-5 lambda-units registry); M <- U^H A.
                Gm = A @ A.mH
                Gm = 0.5 * (Gm + Gm.mH)
                lam, U = torch.linalg.eigh(Gm)  # ascending
                k_keep = min(cap_t, m)  # == cap_t on this route (cap_t < min(m, ncols) <= m)
                keep = lam[:, m - k_keep:].flip(-1).clamp(min=0.0)
                drop = lam[:, : m - k_keep].clamp(min=0.0)
                Uk = U[:, :, m - k_keep:].flip(-1)
                if k_keep < cap_t:  # unreachable on this route; kept for the invariant (iii) form
                    Up = torch.zeros((B, m, cap_t), dtype=CDTYPE, device=dev)
                    Up[:, :, :k_keep] = Uk
                else:
                    Up = Uk
                M = Up.mH @ A
                self._t[s] = Up.reshape(B, lcap, PHYS, cap_t)
                cur = M.reshape(B, cap_t, Drem, r_cap)
                tot = keep.sum(dim=1) + drop.sum(dim=1)
                # per-shot degenerate mask (mirrors the serial ``ne > NUMERICAL_ZERO``
                # guard, lines 695-698; lambda units).
                frac = torch.where(tot > NUMERICAL_ZERO,
                                   drop.sum(dim=1) / tot.clamp_min(NUMERICAL_ZERO),
                                   torch.zeros_like(tot))
                one_minus = one_minus * (1.0 - frac)
        self._t[hi] = cur.reshape(B, self._caps[hi], PHYS, r_cap)
        self._center = hi  # postcondition: center = the window's RIGHTMOST site.

        discarded = (1.0 - one_minus).to(RDTYPE)
        # branch weight: POST-truncation PRE-renormalization norm^2 (the serial ``nt``,
        # lines 692-694) — read off the center tensor (everything else isometric).
        Tc = self._t[hi]
        branch_weight = (Tc.conj() * Tc).real.sum(dim=(1, 2, 3)).to(RDTYPE)
        self._scale_center_(branch_weight)  # renormalize internally (per-shot mask)
        return discarded, branch_weight
