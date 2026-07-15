from __future__ import annotations

r"""Shared cases for process-isolated current PEPO carrier test files.

The suite checks layout and codestate construction, token superoperators,
stabilizer-channel tensor trains, rank selection, terminal-observable
probabilities, detector folding, negativity guards, contractions, and explicit
corruption images against independent dense references.

The collecting modules split these cases by physical responsibility so repeated
3**9 exact-density references do not accumulate in one native/CUDA process.
High-memory integration checks remain separate files as well.

All implementation imports use ``error_coupling_simulator``. The dense
reference, within-cycle marshalling, record fold, and real-patch parser are
read-only reference components; no retired product API is involved.
"""

import copy
import math
import os

import numpy as np
import pytest
import torch

from _support.pepo_density import (
    ARM,
    B_BIAS,
    TOL_EXACT,
    TOL_TRACE,
    fresh_referee as _fresh_referee,
    max_abs_diff as _max_abs_diff,
    pepo_modules as _pepo,
    pick_stabilizers as _pick_stabs,
    prep_pair as _prep_pair,
    release_cuda as _free,
    requires_cuda,
    sched,
    wc,
)
from error_coupling_simulator.numerics import NUMERICAL_ZERO

# --------------------------------------------------------------------------- #
# Test-local gates not shared with process-isolated integration files.         #
# --------------------------------------------------------------------------- #
KILLER_FLOOR = 1e-6      # a corruption image must differ by MORE than this
NEGATIVITY_BAR = 4.8e-4  # representative absolute diagnostic threshold
OBS_N = int(os.environ.get("QEC_PEPO_TEST_OBS_N", "4096"))  # obs-law MC draws (z=4 band)


# --------------------------------------------------------------------------- #
# Small test helpers                                                            #
# --------------------------------------------------------------------------- #
#: Exception class used by both the carrier and independent dense reference.
TOKEN_RAISES = (ValueError,)


def _rng(seed: int):
    """The rng object handed to the sampling APIs (host-side numpy convention)."""
    return np.random.default_rng(int(seed))


def _tt_ranks(stab_tt) -> tuple[int, ...]:
    """Read the internal TT bond ranks off a StabTT (attr-name adapter)."""
    for name in ("ranks", "bond_ranks", "bond_dims", "tt_ranks"):
        r = getattr(stab_tt, name, None)
        if r is not None:
            return tuple(int(x) for x in r)
    for name in ("cores", "tensors", "tt_cores"):
        cores = getattr(stab_tt, name, None)
        if cores is not None and len(cores) >= 2:
            # cores are (D_left, phys, D_right)-shaped; internal bonds = trailing dims
            return tuple(int(np.asarray(c.shape)[-1]) for c in list(cores)[:-1])
    pytest.fail(
        "StabTT exposes no recognizable rank attribute (tried ranks/bond_ranks/"
        "bond_dims/tt_ranks/cores/tensors/tt_cores) — fix the _tt_ranks adapter")


def _fold_call(fn, rec_flat: np.ndarray, R: int, n_stab: int) -> np.ndarray:
    """Call s_to_det/det_to_s on ONE record; accept flat or (R, n_stab) input shape."""
    rec_flat = np.asarray(rec_flat, dtype=np.uint8).reshape(-1)
    try:
        out = fn(rec_flat, R, n_stab)
    except (ValueError, TypeError):
        out = fn(rec_flat.reshape(R, n_stab), R, n_stab)
    return np.asarray(out, dtype=np.uint8).reshape(-1)


def _isx_map(logical: dict) -> dict:
    """The per-logical-site X flag (the sv_sampler ``log_supp_isx`` convention)."""
    return {int(s): int(str(p).upper() == "X") for s, p in logical.items()}


def _negativity_stats(sampler_m):
    """Construct the current Born-negativity accumulator."""
    return sampler_m.NegativityStats()


def _negativity_ndraws(stats) -> int:
    """Read the current Born-draw count."""
    return int(stats.count)


def _witness(sampler_m, q_raw: float, tr: float, ledger: list, negativity_bar: float,
             stats, log_only: bool = False):
    """Call the current Born-negativity diagnostic."""
    return sampler_m.negativity_witness(
        q_raw, tr, ledger, negativity_bar, stats=stats, log_only=log_only)



def _has_would_trip(ledger: list) -> bool:
    """True iff the ledger carries a ``log_only`` would-trip marker."""
    for e in ledger:
        if isinstance(e, dict) and e.get("kind") == "negativity_would_trip":
            return True
    return False


# --------------------------------------------------------------------------- #
# Dense obs/caps references. Shared memory-safe helpers live in                #
# ``tests/_support/pepo_density.py``.                                          #
# --------------------------------------------------------------------------- #
def _site_trits(idx: torch.Tensor, site: int, n: int) -> torch.Tensor:
    """Trit of ``site`` per basis index (qudit 0 = most-significant factor — the
    qutrit_dm module-docstring convention, recomputed here independently)."""
    return (idx // (3 ** (n - 1 - int(site)))) % 3


def _left_mul_site(rho: torch.Tensor, op: torch.Tensor, site: int, n: int) -> torch.Tensor:
    """``M_site @ rho`` without a dense embed (row-index site contraction only)."""
    d = rho.shape[0]
    left, right = 3 ** int(site), 3 ** (n - 1 - int(site))
    return torch.einsum("ab,lbrc->larc", op, rho.reshape(left, 3, right, d)).reshape(d, d)


def _obs_prob_dense(rho: torch.Tensor, logical: dict, b: float, m: int, *,
                    swap_b: bool = False) -> float:
    """Hand-build the observable-law composition on the dense terminal rho.

    H-rotate the X-flagged LOGICAL sites, then the per-site diagonal F0/F1 with the
    formulas F1 = |1><1| + b|2><2|, F0 = |0><0| + (1-b)|2><2|; parity over the
    logical support only; XOR m. ``swap_b=True`` builds the bias-swapped
    corruption image, with b <-> 1-b in the leaked rows.
    Returns P(obs = 1).
    """
    from error_coupling_simulator.carrier.exact.qutrit_dm import qudit_hadamard

    n = round(math.log(rho.shape[0]) / math.log(3))
    assert 3 ** n == rho.shape[0]
    h = qudit_hadamard(3, rho.device)
    work = rho
    x_sites = [s for s, p in logical.items() if str(p).upper() == "X"]
    for s in x_sites:
        # H rho H^dag on the logical X-site (H is Hermitian: H == H^dag)
        work = _left_mul_site(work, h, s, n)
        work = _left_mul_site(work.conj().transpose(-1, -2), h, s, n).conj().transpose(-1, -2)
    diag = torch.diagonal(work).real
    del work
    b1 = (1.0 - float(b)) if swap_b else float(b)
    # f1(t) = P(site reads "1"): t=0 -> 0, t=1 -> 1, t=2 -> b.
    f1_by_trit = torch.tensor([0.0, 1.0, b1], dtype=torch.float64, device=rho.device)
    idx = torch.arange(rho.shape[0], device=rho.device)
    factor = torch.ones_like(diag)
    for s in logical:
        t = _site_trits(idx, int(s), n)
        factor = factor * (1.0 - 2.0 * f1_by_trit[t])
    p_odd = float((diag * 0.5 * (1.0 - factor)).sum().item())
    return p_odd if int(m) == 0 else 1.0 - p_odd


def _leaked_logical_mass(rho: torch.Tensor, logical: dict) -> float:
    """Diagonal mass with ANY logical-support site in |2> (obs-killer precondition)."""
    n = round(math.log(rho.shape[0]) / math.log(3))
    idx = torch.arange(rho.shape[0], device=rho.device)
    any2 = torch.zeros_like(idx, dtype=torch.bool)
    for s in logical:
        any2 |= _site_trits(idx, int(s), n) == 2
    return float(torch.diagonal(rho).real[any2].sum().item())


def _cross_leak_coherence_max(rho: torch.Tensor, sites, block: int = 2048) -> float:
    """Max ``|rho[i,j]|`` over elements whose per-site leak flag ``(t >= 2)`` DIFFERS
    ket vs bra on at least one of ``sites`` — exactly the entries the arm-C
    dephase mask zeroes (entry 1 iff ``(t>=2) == (t'>=2)``). The arm-C
    dense-equality case's NON-VACUITY precondition: without such coherence the mask
    is inert and arm C degenerates to arm A. Chunked over row blocks (never a full
    3^9 x 3^9 float temp)."""
    n = round(math.log(rho.shape[0]) / math.log(3))
    d = rho.shape[0]
    idx = torch.arange(d, device=rho.device)
    flags = [(_site_trits(idx, int(s), n) == 2) for s in sites]
    worst = 0.0
    for i0 in range(0, d, block):
        i1 = min(i0 + block, d)
        cross = torch.zeros((i1 - i0, d), dtype=torch.bool, device=rho.device)
        for f in flags:
            cross |= f[i0:i1, None] ^ f[None, :]
        vals = rho[i0:i1].abs()[cross]
        if vals.numel():
            worst = max(worst, float(vals.max().item()))
        del cross, vals
    return worst


# =========================================================================== #
# layout — grid transform, frozen cut, plaquette paths, PepoState structure    #
# =========================================================================== #
class TestLayout:
    def test_grid_is_integer_unique_dxd(self, sched):
        layout_m, _, _ = _pepo()
        lay = layout_m.PepoLayout.from_sched(sched)
        assert int(lay.n_data) == 9 and int(lay.d) == 3
        seen = set()
        for pos in range(9):
            u, v = lay.grid[pos]
            assert u == int(u) and v == int(v), f"non-integer grid coord at pos {pos}"
            assert 0 <= int(u) <= 2 and 0 <= int(v) <= 2, (pos, u, v)
            seen.add((int(u), int(v)))
            assert lay.pos_at[(u, v)] == pos
        assert len(seen) == 9, "grid (u,v) not unique / not the full 3x3"

    def test_frozen_cut_site_lists(self, sched):
        # Every frozen number uses the explicit site list A=[0,1,2]|B=[3..8].
        layout_m, _, _ = _pepo()
        lay = layout_m.PepoLayout.from_sched(sched)
        assert tuple(lay.frozen_cut_a) == (0, 1, 2)
        assert tuple(sorted(lay.frozen_cut_b)) == (3, 4, 5, 6, 7, 8)
        assert set(lay.frozen_cut_a).isdisjoint(lay.frozen_cut_b)

    def test_plaquette_paths_grid_adjacent_through_support(self, sched):
        layout_m, _, _ = _pepo()
        lay = layout_m.PepoLayout.from_sched(sched)
        for s in sched.stabilizers:
            supp = set(int(k) for k in s.paulis)
            path = [int(p) for p in lay.plaquette_path(dict(s.paulis))]
            assert supp.issubset(set(path)), (supp, path)
            for a, b in zip(path[:-1], path[1:]):
                (ua, va), (ub, vb) = lay.grid[a], lay.grid[b]
                assert abs(int(ua) - int(ub)) + abs(int(va) - int(vb)) == 1, (
                    f"path step {a}->{b} not grid-adjacent: {(ua, va)}->{(ub, vb)}")


@requires_cuda
class TestPepoStateStructure:
    def test_fused_leg_tags_dtype_device(self, wc):
        # Site tag Q{pos}; fused physical index k{pos} of dimension 9;
        # tensors are torch-cuda-complex128.
        layout_m, _, _ = _pepo()
        state = layout_m.build_codestate_pepo(wc["sched"], 0, device="cuda")
        for pos in range(9):
            assert f"Q{pos}" in state.tn.tag_map, f"missing site tag Q{pos}"
            assert int(state.tn.ind_size(f"k{pos}")) == 9, f"fused leg k{pos} dim != 9"
        for t in state.tn:
            assert torch.is_tensor(t.data), "site tensor is not a torch tensor"
            assert t.data.dtype == torch.complex128, t.data.dtype
            assert t.data.is_cuda, "site tensor not on CUDA"
        assert isinstance(state.ledger, list)
        del state
        _free()


# =========================================================================== #
# Codestate equals the independent oracle for both logical sectors             #
# =========================================================================== #
@requires_cuda
class TestG10Codestate:
    @pytest.mark.parametrize("m", [0, 1])
    def test_codestate_matches_oracle(self, wc, m):
        layout_m, _, _ = _pepo()
        state = layout_m.build_codestate_pepo(wc["sched"], m, device="cuda")
        dense = layout_m.dense_rho(state)
        assert dense.shape == (3 ** 9, 3 ** 9)
        eng = _fresh_referee(wc["sched"])
        eng.init_logical(m)
        tr = float(torch.diagonal(dense).real.sum().item())
        assert abs(tr - 1.0) <= 1e-9, f"codestate trace {tr} != 1"
        worst = _max_abs_diff(dense, eng.rho)
        assert worst <= TOL_EXACT, f"codestate m={m}: max-abs {worst:.3e} > 1e-12"
        del dense, eng, state
        _free()


# =========================================================================== #
# Token ops — H/X/LEAK/Y equal the QutritDM dense update and raise set        #
# =========================================================================== #
@requires_cuda
class TestTokenOps:
    @pytest.mark.parametrize("tok", ["H", "X", "LEAK"])
    def test_premeasure_token_matches_referee(self, wc, tok):
        layout_m, dynamics_m, _ = _pepo()
        state, eng = _prep_pair(wc, seed=101, n_ops=4, leak_pump=(0,))
        for site in (0, 4, 8):
            dynamics_m.apply_token_stream(state, {site: (tok,)}, wc["leak_t"])
            eng.apply_within_cycle_premeasure({site: (tok,)}, wc["leak_list"])
        worst = _max_abs_diff(layout_m.dense_rho(state), eng.rho)
        assert worst <= TOL_EXACT, f"token {tok}: max-abs {worst:.3e} > 1e-12"
        del state, eng
        _free()

    def test_postmeasure_y_matches_referee_and_terminal_skips(self, wc):
        layout_m, dynamics_m, _ = _pepo()
        state, eng = _prep_pair(wc, seed=102, n_ops=4, leak_pump=(2,))
        streams = {site: ("M", "Y") for site in range(9)}
        # terminal=True is a no-op because the terminal round drops post-M Y.
        before = layout_m.dense_rho(state)
        dynamics_m.apply_postmeasure(state, streams, terminal=True)
        after = layout_m.dense_rho(state)
        worst_noop = _max_abs_diff(before, after)
        del before, after
        _free()
        assert worst_noop <= TOL_EXACT, f"terminal=True mutated the state ({worst_noop:.3e})"
        # interior round: transversal Y == the referee's post-measure Y
        dynamics_m.apply_postmeasure(state, streams, terminal=False)
        eng.apply_within_cycle_postmeasure(streams, terminal=False)
        worst = _max_abs_diff(layout_m.dense_rho(state), eng.rho)
        assert worst <= TOL_EXACT, f"post-M Y: max-abs {worst:.3e} > 1e-12"
        del state, eng
        _free()

    def test_raise_set_pre_m_unknown_raises(self, wc):
        _, dynamics_m, _ = _pepo()
        state, _eng = _prep_pair(wc, seed=103, n_ops=0)
        with pytest.raises(TOKEN_RAISES):
            dynamics_m.apply_token_stream(state, {0: ("FROB",)}, wc["leak_t"])
        del state, _eng
        _free()

    @pytest.mark.parametrize("bad", ["X", "H", "LEAK"])
    def test_raise_set_post_m_xhleak_raises(self, wc, bad):
        _, dynamics_m, _ = _pepo()
        state, _eng = _prep_pair(wc, seed=104, n_ops=0)
        with pytest.raises(TOKEN_RAISES):
            dynamics_m.apply_postmeasure(state, {0: ("M", bad)}, terminal=False)
        del state, _eng
        _free()

    def test_raise_set_post_m_other_unknown_silently_ignored(self, wc):
        # The dense reference does not raise on arbitrary post-M tokens, so this
        # must be a no-op.
        layout_m, dynamics_m, _ = _pepo()
        state, _eng = _prep_pair(wc, seed=105, n_ops=3)
        before = layout_m.dense_rho(state)
        dynamics_m.apply_postmeasure(state, {0: ("M", "FROB")}, terminal=False)
        after = layout_m.dense_rho(state)
        worst = _max_abs_diff(before, after)
        del before, after, state, _eng
        _free()
        assert worst <= TOL_EXACT, f"post-M unknown token mutated the state ({worst:.3e})"


# =========================================================================== #
# stab_channel_tt — dense equality vs project_stabilizer; the TT rank asserts  #
# =========================================================================== #
@requires_cuda
class TestStabChannel:
    @pytest.mark.parametrize("which", ["w4", "w2"])
    @pytest.mark.parametrize("outcome", [0, 1])
    def test_branch_matches_referee_unnormalized(self, wc, which, outcome):
        layout_m, dynamics_m, _ = _pepo()
        w4, w2 = _pick_stabs(wc["sched"])
        paulis = w4 if which == "w4" else w2
        # leak_pump on the support so the b = 0.9 leaked rows are LIVE (non-vacuous)
        pump = tuple(sorted(paulis))[:2]
        state, eng = _prep_pair(wc, seed=110 + outcome, n_ops=5, leak_pump=pump)
        tt = dynamics_m.stab_channel_tt(paulis, outcome, B_BIAS, ARM,
                                        state.layout, "cuda")
        dynamics_m.apply_stab_branch(state, tt)          # unnormalized branch
        eng.project_stabilizer(paulis, outcome, B_BIAS, ARM)  # referee: unnormalized
        worst = _max_abs_diff(layout_m.dense_rho(state), eng.rho)
        assert worst <= TOL_EXACT, (
            f"stab {which} outcome={outcome}: max-abs {worst:.3e} > 1e-12")
        del state, eng
        _free()

    def test_tt_ranks_at_p1c_cell(self, wc):
        # Exact fused-leg TT ranks equal (2*min(w_L, w_R) + 1)^2 per bond for
        # arm A, b = 0.9: (9, 25, 9) at w=4 and (9,) at w=2.
        layout_m, dynamics_m, _ = _pepo()
        w4, w2 = _pick_stabs(wc["sched"])
        lay = layout_m.PepoLayout.from_sched(wc["sched"])
        tt4 = dynamics_m.stab_channel_tt(w4, 0, B_BIAS, ARM, lay, "cuda")
        assert _tt_ranks(tt4) == (9, 25, 9), _tt_ranks(tt4)
        tt2 = dynamics_m.stab_channel_tt(w2, 0, B_BIAS, ARM, lay, "cuda")
        assert _tt_ranks(tt2) == (9,), _tt_ranks(tt2)

    def test_arm_c_dense_equality_certifies_dephase_mask(self, wc):
        """The engine's arm='C' weight-4
        branch — the per-site fused-leg leak-flag dephase mask (entry 1 iff
        ``(t>=2) == (t'>=2)``) applied on the support before the TT — must equal the
        referee's dephase-then-E_s update (``QutritDM.project_stabilizer`` arm='C')
        at 1e-12 on a rho carrying CROSS-LEAK-SECTOR coherence on the support.
        The coherence precondition is ASSERTED (scrutinize-vacuous rule: on a
        cross-sector-diagonal rho the mask is inert and arm C == arm A — an
        arm-C bug would be invisible)."""
        layout_m, dynamics_m, _ = _pepo()
        w4, _ = _pick_stabs(wc["sched"])
        pump = tuple(sorted(w4))
        state, eng = _prep_pair(wc, seed=115, n_ops=6, leak_pump=pump)
        coh = _cross_leak_coherence_max(eng.rho, sorted(int(s) for s in w4))
        assert coh > 1e-6, (
            f"arm-C precondition FAILED: max cross-leak-sector coherence on the "
            f"support is {coh:.3e} <= 1e-6 — the dephase mask would act vacuously; "
            f"pump more LEAK/H on the support")
        tt = dynamics_m.stab_channel_tt(w4, 0, B_BIAS, "C", state.layout, "cuda")
        dynamics_m.apply_stab_branch(state, tt)
        eng.project_stabilizer(w4, 0, B_BIAS, "C")  # referee: dephase-then-E_s
        worst = _max_abs_diff(layout_m.dense_rho(state), eng.rho)
        assert worst <= TOL_EXACT, (
            f"arm-C stab branch: max-abs {worst:.3e} > 1e-12 (the leak-flag dephase "
            f"mask does not reproduce the referee's dephase-then-E_s order)")
        del state, eng
        _free()

    @pytest.mark.parametrize("b_dom, mid_bound", [(0.5, 9), (1.0, 4), (0.0, 4)])
    def test_tt_rank_domain_behavior(self, wc, b_dom, mid_bound):
        # At b = 0.5 the product classes collapse (w=4 mid-bond <= 9); at b in
        # {0, 1} the bound is 4. Outside the domain the assertion is rank <= the
        # domain bound and the build must not raise.
        layout_m, dynamics_m, _ = _pepo()
        w4, _ = _pick_stabs(wc["sched"])
        lay = layout_m.PepoLayout.from_sched(wc["sched"])
        tt = dynamics_m.stab_channel_tt(w4, 0, float(b_dom), ARM, lay, "cuda")
        ranks = _tt_ranks(tt)
        assert len(ranks) == 3
        assert all(r <= bnd for r, bnd in zip(ranks, (9, 25, 9))), ranks
        assert ranks[1] <= mid_bound, (b_dom, ranks)


# =========================================================================== #
# Corruption images that must break dense equality                              #
# =========================================================================== #
@requires_cuda
class TestKillers:
    def test_k_corrupt_stab_letter_swap_breaks_dense_equality(self, wc):
        """CorruptStab: flip ONE support site's X/Z letter (wrong support content,
        path-preserving so the TT still builds) — the branch must DIVERGE from the
        dense-reference update by more than the ``1e-12`` tolerance. A one-site
        letter flip works for both mixed-letter and single-letter stabilizers.
        """
        layout_m, dynamics_m, _ = _pepo()
        w4, _ = _pick_stabs(wc["sched"])
        sites = sorted(w4)
        corrupt = dict(w4)
        s0 = sites[0]
        corrupt[s0] = "Z" if str(w4[s0]).upper() == "X" else "X"
        assert corrupt != w4  # sabotage sanity
        state, eng = _prep_pair(wc, seed=120, n_ops=6, leak_pump=(sites[0],))
        tt_bad = dynamics_m.stab_channel_tt(corrupt, 0, B_BIAS, ARM,
                                            state.layout, "cuda")
        dynamics_m.apply_stab_branch(state, tt_bad)
        eng.project_stabilizer(w4, 0, B_BIAS, ARM)  # the TRUE update
        worst = _max_abs_diff(layout_m.dense_rho(state), eng.rho)
        assert worst > KILLER_FLOOR, (
            f"CorruptStab sabotage did NOT trip the dense equality (diff {worst:.3e}) "
            f"— the stab-channel gate has no teeth")
        del state, eng
        _free()

    def test_k_wrong_tt_outcome_sign_breaks_dense_equality(self, wc):
        """A flipped E_s outcome sign in the TT (outcome 1 vs referee outcome 0)
        must diverge from the referee branch by >> the gate bar."""
        layout_m, dynamics_m, _ = _pepo()
        w4, _ = _pick_stabs(wc["sched"])
        state, eng = _prep_pair(wc, seed=121, n_ops=6, leak_pump=tuple(sorted(w4))[:1])
        tt_flipped = dynamics_m.stab_channel_tt(w4, 1, B_BIAS, ARM,
                                                state.layout, "cuda")
        dynamics_m.apply_stab_branch(state, tt_flipped)
        eng.project_stabilizer(w4, 0, B_BIAS, ARM)
        worst = _max_abs_diff(layout_m.dense_rho(state), eng.rho)
        assert worst > KILLER_FLOOR, (
            f"outcome-sign sabotage did NOT trip the dense equality (diff {worst:.3e})")
        del state, eng
        _free()

    def test_k_transposed_fused_leg_breaks_dense_equality(self, wc):
        """The transposed fused-leg convention k = 3*t_bra + t_ket reconstructs
        rho^T (per-site ket/bra swap at EVERY site == the global transpose).
        The compiled-circuit primitives are real superoperators in this basis, so
        the test injects the valid complex-phase unitary Kraus
        ``diag(1, e^{i pi/4}, 1)`` through the leakage operation in both the carrier
        and dense reference. This makes the transposed convention observable.
        """
        layout_m, dynamics_m, _ = _pepo()
        state, eng = _prep_pair(wc, seed=122, n_ops=4, leak_pump=(0, 1, 4))
        streams = {site: ("M", "Y") for site in range(9)}
        dynamics_m.apply_postmeasure(state, streams, terminal=False)
        eng.apply_within_cycle_postmeasure(streams, terminal=False)
        # synthetic complex-phase Kraus (exactly unitary => exactly CPTP), applied
        # identically to engine and referee through the existing LEAK machinery
        ph = torch.zeros((1, 3, 3), dtype=torch.complex128, device="cuda")
        ph[0, 0, 0] = 1.0
        ph[0, 1, 1] = complex(math.cos(math.pi / 4), math.sin(math.pi / 4))
        ph[0, 2, 2] = 1.0
        for site in (0, 4):
            dynamics_m.apply_token_stream(state, {site: ("H", "LEAK")}, ph)
            eng.apply_within_cycle_premeasure({site: ("H", "LEAK")}, [ph[0]])
        # PRECONDITION (non-vacuity): the sabotage image differs from rho only through
        # Im(rho) — assert the evolved state actually carries an imaginary part.
        im_max = float(eng.rho.imag.abs().max().item())
        assert im_max > 1e-9, (
            f"killer precondition FAILED: evolved rho is real (max|Im|={im_max:.3e}) — "
            f"the transpose sabotage would be vacuous; change the prep program")
        dense = layout_m.dense_rho(state)
        worst_correct = _max_abs_diff(dense, eng.rho)
        assert worst_correct <= TOL_EXACT, (
            f"correct-convention sanity failed first ({worst_correct:.3e})")
        # the sabotage image: the transposed-convention reconstruction == dense.T
        worst_sab = _max_abs_diff(dense.transpose(-1, -2), eng.rho)
        assert worst_sab > KILLER_FLOOR, (
            f"transposed fused-leg sabotage did NOT trip (diff {worst_sab:.3e})")
        del dense, state, eng
        _free()


# =========================================================================== #
# gap_rank — window-bound rule, case by case                                   #
# =========================================================================== #
class TestGapRank:
    """Pure spectrum-rule units (CPU float64 tensors; no CUDA needed)."""

    @staticmethod
    def _gr(sigma, d_cap):
        _, dynamics_m, _ = _pepo()
        rank, ratio, cap = dynamics_m.gap_rank(
            torch.as_tensor(sigma, dtype=torch.float64), int(d_cap))
        return int(rank), float(ratio), bool(cap)

    def test_frozen_16_gap_shape(self):
        # 16 strong values then a >= 10x drop: rank 16, ratio >= 10, cap NOT binding
        sigma = np.concatenate([np.linspace(1.0, 0.5, 16), np.full(24, 0.01)])
        rank, ratio, cap = self._gr(sigma, 16)
        assert rank == 16 and not cap, (rank, cap)
        assert ratio >= 10.0, ratio

    def test_exact_zero_tail_inside_window(self):
        # sigma_{k+1} exactly 0 inside the window -> ratio(k) := inf -> last nonzero
        sigma = np.array([1.0, 0.8, 0.6, 0.4, 0.2] + [0.0] * 20)
        rank, ratio, cap = self._gr(sigma, 16)
        assert rank == 5 and not cap, (rank, cap)
        assert math.isinf(ratio) or ratio >= 10.0, ratio

    def test_smooth_no_gap_spectrum_caps(self):
        # geometric decay, every ratio ~1.11 < 10, all above the floor:
        # none qualifying => effective rank = D_cap + CAP_BINDING
        sigma = 0.9 ** np.arange(40)
        rank, _ratio, cap = self._gr(sigma, 16)
        assert rank == 16 and cap, (rank, cap)

    def test_rank_deficient_window_floor_guard_wins_via_inf_ratio(self):
        # sigma_k guard on a rank-deficient window: the floor filter excludes
        # every sub-floor k from candidacy, so the largest ABOVE-floor k (= 3 here)
        # qualifies via ratio := inf (sigma_4 <= 1e-12*sigma_1) and wins on the MAIN
        # route — structurally equal to the count of sigma > floor.  What this
        # certifies: the guard-removal mutant DIES (without the floor filter, k = 16
        # would qualify via inf and win -> rank 16 != 3).  What it does NOT exercise:
        # the literal `if not candidates` count-fallback clause is DEAD in-domain —
        # after the s[0] <= 0 early return, k = 1 always passes the sigma_k floor, so
        # candidates is never empty.
        sigma = np.array([1.0, 0.5, 0.25] + [1e-15] * 30)
        rank, _ratio, cap = self._gr(sigma, 16)
        assert rank == 3 and not cap, (rank, cap)

    def test_junk_tail_below_floor_excluded(self):
        # tail below 1e-12*sigma1 is junk: the gap at k=4 wins (ratio inf), rank 4
        sigma = np.array([1.0, 0.9, 0.8, 0.7] + [1e-14] * 10)
        rank, ratio, cap = self._gr(sigma, 8)
        assert rank == 4 and not cap, (rank, cap)
        assert math.isinf(ratio) or ratio >= 10.0, ratio

    def test_gap_beyond_window_never_wins(self):
        # A huge gap at k = 20 > D_cap = 16 must not win; the
        # qualifying k = 8 gap inside the window does.
        head = np.linspace(1.0, 0.8, 8)                    # k = 1..8
        mid = np.linspace(0.05, 0.02, 12)                  # k = 9..20 (mild decay)
        tail = np.full(10, 1e-13)                          # k = 21.. (exact-ish zero)
        sigma = np.concatenate([head, mid, tail])
        rank, ratio, cap = self._gr(sigma, 16)
        assert rank == 8 and not cap, (rank, cap)
        assert ratio >= 10.0 and not math.isinf(ratio), ratio


# =========================================================================== #
# obs law — terminal_readout_obs vs the hand-built dense composition + KILLER  #
# =========================================================================== #
@requires_cuda
class TestObsLaw:
    def _pumped_pair(self, wc):
        # pump LEAK on every LOGICAL site so the leaked F0/F1 rows are live
        log_sites = tuple(sorted(wc["sched"].logical))
        return _prep_pair(wc, seed=130, n_ops=4, leak_pump=log_sites)

    def _sample(self, sampler_m, state, logical, isx, m, n, seed):
        rng = _rng(seed)
        ones = 0
        for _ in range(int(n)):
            st = copy.deepcopy(state)  # terminal readout may collapse; never reuse
            ones += int(sampler_m.terminal_readout_obs(st, logical, isx, B_BIAS, m, rng)) & 1
        return ones / float(n)

    def test_obs_distribution_matches_dense_composition(self, wc):
        _, _, sampler_m = _pepo()
        state, eng = self._pumped_pair(wc)
        logical = dict(wc["sched"].logical)
        isx = _isx_map(logical)
        p_ref = {m: _obs_prob_dense(eng.rho, logical, B_BIAS, m) for m in (0, 1)}
        assert abs(p_ref[0] + p_ref[1] - 1.0) <= 1e-10  # XOR-m consistency of the ref
        # The engine-side exact
        # P(obs=1) composition — through the SAME effect-construction code the
        # sampling path uses — held to the 1e-10 bar vs the dense composition.
        for m in (0, 1):
            p_eng = float(sampler_m.terminal_readout_obs_prob(
                copy.deepcopy(state), logical, isx, B_BIAS, m))
            assert abs(p_eng - p_ref[m]) <= TOL_TRACE, (
                f"exact obs route m={m}: engine {p_eng:.12e} vs dense {p_ref[m]:.12e} "
                f"differ beyond 1e-10")
        # SECONDARY read: the sampling-only API cannot be checked at 1e-10 on
        # probabilities; the sampled leg runs at the z=4 MC band.
        for m in (0, 1):
            p_hat = self._sample(sampler_m, state, logical, isx, m, OBS_N, seed=7 + m)
            band = 4.0 * math.sqrt(max(p_ref[m] * (1 - p_ref[m]), 1e-4) / OBS_N)
            assert abs(p_hat - p_ref[m]) <= band, (
                f"obs law m={m}: p_hat={p_hat:.4f} vs dense {p_ref[m]:.4f} "
                f"(z=4 band {band:.4f}, N={OBS_N})")
        del state, eng
        _free()

    def test_k_swapped_b_variant_differs(self, wc):
        """Corruption image for the coherent-double-swap. The engine's exact
        observable probability must match the
        pinned dense composition (1e-10) AND DIFFER from the b <-> (1-b) swapped
        composition (> 1e-6) on a leaked state."""
        _, _, sampler_m = _pepo()
        state, eng = self._pumped_pair(wc)
        logical = dict(wc["sched"].logical)
        isx = _isx_map(logical)
        mass2 = _leaked_logical_mass(eng.rho, logical)
        assert mass2 > 1e-4, (
            f"killer precondition FAILED: leaked logical mass {mass2:.3e} <= 1e-4 — "
            f"the b-swap would be numerically invisible; pump more LEAK")
        p_ok = _obs_prob_dense(eng.rho, logical, B_BIAS, 0, swap_b=False)
        p_swap = _obs_prob_dense(eng.rho, logical, B_BIAS, 0, swap_b=True)
        # instrument-teeth precondition: the two dense compositions must be separated
        assert abs(p_swap - p_ok) > KILLER_FLOOR, (
            f"b-swap sabotage did NOT move the dense obs probability "
            f"(|{p_swap:.6e} - {p_ok:.6e}| <= {KILLER_FLOOR}) — the obs gate has no "
            f"teeth against the double-swap")
        p_eng = float(sampler_m.terminal_readout_obs_prob(
            copy.deepcopy(state), logical, isx, B_BIAS, 0))
        assert abs(p_eng - p_ok) <= TOL_TRACE, (
            f"ENGINE exact obs prob {p_eng:.12e} != unswapped dense {p_ok:.12e} "
            f"(> 1e-10) — the engine does not implement the pinned F0/F1 composition")
        assert abs(p_eng - p_swap) > KILLER_FLOOR, (
            f"ENGINE exact obs prob {p_eng:.6e} matches the FORBIDDEN swapped "
            f"composition {p_swap:.6e} within {KILLER_FLOOR} — the coherent "
            f"double-swap is live in the engine")
        del state, eng
        _free()


# =========================================================================== #
# s_to_det / det_to_s — round-trip + independent hand-typed fold              #
# =========================================================================== #
class TestDetectorFold:
    """Host-side conventions; no CUDA required."""

    def test_round_trip_and_seam_equality(self):
        _, _, sampler_m = _pepo()

        R, n_stab, N = 4, 8, 32
        rng = np.random.default_rng(2026)
        s = rng.integers(0, 2, size=(N, R * n_stab)).astype(np.uint8)
        shaped = s.reshape(N, R, n_stab)
        det_ref = np.empty_like(shaped)
        det_ref[:, 0, :] = shaped[:, 0, :]
        det_ref[:, 1:, :] = shaped[:, 1:, :] ^ shaped[:, :-1, :]
        det_ref = det_ref.reshape(N, R * n_stab)
        for i in range(N):
            det_i = _fold_call(sampler_m.s_to_det, s[i], R, n_stab)
            assert np.array_equal(det_i, det_ref[i]), (
                f"shot {i}: s_to_det != independent fold\n got {det_i}\n exp {det_ref[i]}")
            s_back = _fold_call(sampler_m.det_to_s, det_i, R, n_stab)
            assert np.array_equal(s_back, s[i]), f"shot {i}: det_to_s(s_to_det) != id"
            det_back = _fold_call(
                sampler_m.s_to_det, _fold_call(sampler_m.det_to_s, det_ref[i], R, n_stab),
                R, n_stab)
            assert np.array_equal(det_back, det_ref[i]), (
                f"shot {i}: s_to_det(det_to_s) != id")

    def test_det_to_s_is_prefix_xor(self):
        # s(r, j) = XOR_{r' <= r} det(r', j)
        _, _, sampler_m = _pepo()
        R, n_stab = 5, 8
        rng = np.random.default_rng(7)
        det = rng.integers(0, 2, size=(R, n_stab)).astype(np.uint8)
        s = _fold_call(sampler_m.det_to_s, det.reshape(-1), R, n_stab).reshape(R, n_stab)
        expect = np.bitwise_xor.accumulate(det, axis=0) % 2
        assert np.array_equal(s, expect.astype(np.uint8))


# =========================================================================== #
# negativity_witness — stop rules, healthy pass, and sign-flip corruption      #
# =========================================================================== #
class TestNegativityWitness:
    """The diagnostic stops if (i) any
    SINGLE raw Born weight q_raw < -(10x bar) => STOP; (ii) the MEAN over all Born
    draws — accumulated on the stats object threaded through the calls, never a
    ledger rescan — of max(0, -q_raw)/Tr(rho) > bar => STOP; STOP ==
    RuntimeError('NEGATIVITY_STOP: ...'). ``log_only=True`` never raises; a
    ``negativity_would_trip`` ledger entry records the event and the draw is counted."""

    def test_healthy_inputs_pass(self):
        _, _, sampler_m = _pepo()
        ledger: list = []
        stats = _negativity_stats(sampler_m)
        rng = np.random.default_rng(11)
        for _ in range(50):
            q = float(rng.uniform(0.01, 1.0))
            _witness(sampler_m, q, 1.0, ledger, NEGATIVITY_BAR, stats)
        # tiny negative round-off well under both bars must also pass
        for _ in range(10):
            _witness(sampler_m, -1e-9, 1.0, ledger, NEGATIVITY_BAR, stats)
        assert _negativity_ndraws(stats) == 60, (
            f"negativity stats counted {_negativity_ndraws(stats)} draws != 60")

    def test_rule_i_single_weight_trips(self):
        _, _, sampler_m = _pepo()
        with pytest.raises(RuntimeError, match="NEGATIVITY_STOP"):
            _witness(sampler_m, -10.5 * NEGATIVITY_BAR, 1.0, [], NEGATIVITY_BAR,
                     _negativity_stats(sampler_m))

    def test_rule_ii_mean_negative_mass_trips(self):
        # each draw is ABOVE the rule-(i) bar (-2x bar > -10x bar) but the per-draw
        # mean negative mass 2x bar > bar => rule (ii) must fire — evaluated off the
        # The same stats accumulator is threaded through every call.
        _, _, sampler_m = _pepo()
        ledger: list = []
        stats = _negativity_stats(sampler_m)
        tripped = False
        try:
            for _ in range(50):
                _witness(
                    sampler_m, -2.0 * NEGATIVITY_BAR, 1.0, ledger,
                    NEGATIVITY_BAR, stats)
        except RuntimeError as e:
            assert "NEGATIVITY_STOP" in str(e), str(e)
            tripped = True
        assert tripped, "rule (ii) never fired on mean negative mass 2x the bar"

    def test_log_only_would_trip_logged_never_raises(self):
        """A rule-(i)-grade weight under ``log_only=True`` must not raise; the
        ``negativity_would_trip`` ledger entry records it and the draw still counts on the stats
        accumulator."""
        _, _, sampler_m = _pepo()
        ledger: list = []
        stats = _negativity_stats(sampler_m)
        _witness(sampler_m, -20.0 * NEGATIVITY_BAR, 1.0, ledger,
                 NEGATIVITY_BAR, stats,
                 log_only=True)  # a rule-(i) trip magnitude — must NOT raise
        assert _has_would_trip(ledger), (
            "log_only would-trip left no negativity_would_trip ledger entry")
        assert _negativity_ndraws(stats) == 1, (
            f"log_only draw not counted on the stats accumulator "
            f"({_negativity_ndraws(stats)} != 1)")

    def test_k_sign_flip_sabotage_trips(self):
        # Corruption image: a healthy Born weight with its sign flipped.
        _, _, sampler_m = _pepo()
        healthy = 0.31
        _witness(sampler_m, healthy, 1.0, [], NEGATIVITY_BAR,
                 _negativity_stats(sampler_m))  # passes as-is
        with pytest.raises(RuntimeError, match="NEGATIVITY_STOP"):
            _witness(sampler_m, -healthy, 1.0, [], NEGATIVITY_BAR,
                     _negativity_stats(sampler_m))


# =========================================================================== #
# expect_site_caps / stab_expectation / pepo_trace — Tr(rho * Pi) checks       #
# =========================================================================== #
@requires_cuda
class TestExpectation:
    def test_pepo_trace_matches_referee(self, wc):
        _, _, sampler_m = _pepo()
        state, eng = _prep_pair(wc, seed=140, n_ops=4, leak_pump=(3,))
        tr_e = complex(sampler_m.pepo_trace(state))
        tr_ref = complex(torch.diagonal(eng.rho).sum().item())
        assert abs(tr_e - tr_ref) <= TOL_TRACE, (tr_e, tr_ref)
        del state, eng
        _free()

    def test_expect_site_caps_matches_dense(self, wc):
        # Caps are general single-site (3,3) operators; absent sites get the
        # trace-cap.  Dense reference: Tr((x)M rho) via row-side contraction on the
        # dense reference rho, independent of the carrier contraction path.
        _, _, sampler_m = _pepo()
        state, eng = _prep_pair(wc, seed=141, n_ops=4, leak_pump=(1, 5))
        g = torch.Generator(device="cpu").manual_seed(5)
        caps = {}
        for site in (2, 5):
            a = torch.randn(3, 3, dtype=torch.complex128, generator=g)
            caps[site] = ((a + a.conj().T) / 2).to("cuda")  # random Hermitian cap
        w = eng.rho
        for site, m_op in caps.items():
            w = _left_mul_site(w, m_op, site, 9)
        expected = complex(torch.diagonal(w).sum().item())
        del w
        _free()
        got = complex(sampler_m.expect_site_caps(state, caps))
        assert abs(got - expected) <= TOL_TRACE, (got, expected)
        # with an explicit norm cache (R_n = 16 covers the exact d3 boundary)
        cache = sampler_m.norm_cache(state, 16)
        got_c = complex(sampler_m.expect_site_caps(state, caps, cache=cache, R_n=16))
        assert abs(got_c - expected) <= TOL_TRACE, (got_c, expected)
        del state, eng
        _free()

    @pytest.mark.parametrize("which", ["w4", "w2"])
    def test_stab_expectation_two_term_matches_referee(self, wc, which):
        # Tr(E_s rho) = 1/2 Tr(rho) + 1/2 (-1)^s Tr(rho (x)M_q), checked against
        # the referee's project_stabilizer branch probability on the mirrored rho.
        _, _, sampler_m = _pepo()
        w4, w2 = _pick_stabs(wc["sched"])
        paulis = w4 if which == "w4" else w2
        state, eng = _prep_pair(wc, seed=142, n_ops=5,
                                leak_pump=tuple(sorted(paulis))[:1])
        base = eng.rho.clone()
        tr = float(torch.diagonal(base).real.sum().item())
        probs = {}
        for outcome in (0, 1):
            e_engine = float(sampler_m.stab_expectation(
                state, paulis, outcome, B_BIAS, ARM))
            eng.rho = base.clone()
            e_ref = float(eng.project_stabilizer(paulis, outcome, B_BIAS, ARM))
            assert abs(e_engine - e_ref) <= TOL_TRACE, (which, outcome, e_engine, e_ref)
            probs[outcome] = e_engine
        # E_0 + E_1 = I  =>  the two branch expectations sum to Tr(rho)
        assert abs(probs[0] + probs[1] - tr) <= TOL_TRACE, (probs, tr)
        del state, eng, base
        _free()


# Numerical-floor wiring sanity.                                               #
def test_numerical_zero_is_the_contract_floor():
    assert NUMERICAL_ZERO == 1e-12
