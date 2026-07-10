from __future__ import annotations

r"""Rung-1 PEPO engine — the registered unit-level referee gates + KILLER variants.

Written AGAINST the binding contract
``docs/nonpauli_teacher/pepo_engine_rung1_contract.md`` (v4.2) under the governing
pre-registration ``docs/nonpauli_teacher/pepo_d5d7_carrier_prereg.md`` (v2.4) — NEVER
against the implementation (the three modules ``layout`` / ``dynamics`` / ``sampler``
are built in parallel; they are imported at TEST RUNTIME ONLY, inside :func:`_pepo`).

Coverage (the test-builder's contract rows):
  * G1.0            — ``build_codestate_pepo`` == ``QutritDM.init_logical`` dense rho,
                      m=0 AND m=1, 1e-12 max-abs (CUDA).
  * token ops       — H/X/LEAK (pre-M) and Y (post-M) superops == the QutritDM dense
                      update (1e-12); the raise-set pinned in contract §3 rows 2-3
                      (pre-M unknown raises; post-M X/H/LEAK raise; post-M
                      other-unknown silently ignored) — all three classes.
  * stab_channel_tt — one full weight-4 X-containing + one weight-2 stabilizer update
                      == ``QutritDM.project_stabilizer`` (unnormalized branch, 1e-12);
                      TT ranks == (9,25,9)/(9,) at the p1c cell b=0.9 arm A; the
                      b=0.5 / b=1.0 DOMAIN behavior (rank <= bound, never ==); + the
                      v4.2 ARM-C DEPHASE dense-equality case (weight-4, arm='C',
                      cross-leak-sector coherence pumped, 1e-12 — certifies the
                      per-site leak-flag dephase mask).
  * gap_rank        — the §3 v4.1 window-bound rule VERBATIM: the frozen 16-gap shape,
                      the exact-zero tail (inf-ratio inside the window), the smooth
                      no-gap spectrum (D_cap + CAP_BINDING), the rank-deficient window
                      (the sigma_k floor guard wins via inf-ratio — the literal
                      count-fallback clause is dead in-domain, re-review 2026-07-10
                      F2), the junk tail below 1e-12*sigma1, and the v4 fix itself
                      (a gap BEYOND the window never wins).
  * obs law         — the v4.2 EXACT-PROBABILITY SEAM ``terminal_readout_obs_prob``
                      held to 1e-10 vs the hand-built DENSE composition of the §3
                      pinned formulas (H-rotate isx sites; F1=|1><1|+b|2><2|,
                      F0=|0><0|+(1-b)|2><2|; parity over the LOGICAL support; XOR m);
                      the sampled ``terminal_readout_obs`` leg as a SECONDARY z=4 MC
                      read; + the b<->(1-b) coherent-double-swap KILLER, now
                      ENGINE-invoking (engine ~ unswapped dense AND != swapped dense).
  * s_to_det/det_to_s — round-trip identity + equality with seam.py's own fold.
  * negativity_witness — C3 rules (i)/(ii) trip (rule (ii) via the v4.2 STATS
                      accumulator, not a ledger rescan); healthy inputs pass; the
                      sign-flip sabotage trips; ``log_only=True`` (the G1.1 R=4
                      exerciser scoping) never raises — a would-trip leaves a
                      ``c3_would_trip`` ledger entry.
  * expect_site_caps — dense Tr(rho * (x)M) equality (1e-10) on a tiny PEPO state;
                      ``stab_expectation`` two-term E_s vs the referee; pepo_trace.
  * integration tier — CUDA real-patch EXECUTION SMOKE (v4.2; loose class-(c) bars,
                      documented — G1.1/G1.2 are the real gates): 2 truncating
                      nonselective rounds at D_cap=8 (the NTU metric path EXECUTES,
                      precondition-asserted) vs the exact referee at the REGISTERED
                      loose 1e-2 max-abs smoke bar + truncation-ledger fields
                      (discarded >= 0, precut_discarded present, finite ntu_eps);
                      the R_n=4 compressed caps path (tensor_network_1d_compress
                      runs; finite, 20% loose); a born_sample_round smoke (8 bits,
                      raw-q range sanity, born_negativity entries, the C3 stats
                      accumulator counts 8 draws); + the v4.2 NTU PRECUT regime
                      (re-review 2026-07-10 F3: exact_rank > 4*D_cap at D_cap=2
                      on a real grown bond -> precut_discarded STRICTLY > 0.0 and
                      dim_out == D_cap, paired with the out-of-regime 0.0-exact
                      report — the sabotage image of a deleted/silent precut).
  * KILLERs         — CorruptStab (letter-swap on the support) breaks the stab-channel
                      dense equality; the transposed fused-leg convention
                      (k = 3*t_bra + t_ket) breaks the dense-vs-oracle equality; a
                      wrong TT outcome sign breaks the dense equality.  Each killer
                      asserts the sabotage IMAGE differs beyond the gate tolerance —
                      i.e. the corresponding load-bearing assert is DEMONSTRATED to
                      trip (G1.5 / K-catalog discipline).

GPU convention: per-test ``skipif`` on ``torch.cuda.is_available()`` (the repo pattern
of ``tests/test_kernels_fused_kraus.py``); the engine is GPU-only (S8), so every test
that constructs a PepoState requires CUDA.  Tests needing the REAL Google d3 circuit
(contract F5 pins the real patch — no textbook fallback is admissible) skip with an
explicit justification when the local dataset is absent.

Referee seams used READ-ONLY: ``error_coupling_simulator.carrier.exact.qutrit_dm``
(the exact-DM oracle), ``qec_twin.forward.scalable.sv_sampler`` (within-cycle
marshalling + pack_shots), ``qec_twin.forward.scalable.seam`` (the detector fold),
``qec_twin.forward.exact.xzzx_parser`` (the real-patch schedule).
"""

import copy
import math
import os

import numpy as np
import pytest
import torch

from qec_twin.numerics import NUMERICAL_ZERO

# --------------------------------------------------------------------------- #
# Constants (contract §3/§4 pinned values; p1c cell per prereg §1)             #
# --------------------------------------------------------------------------- #
WG_L1_TARGET = 5.0e-3   # p1c physical cell (prereg §1)
G_SEEP = 0.09
G_HEAT = 0.0
B_BIAS = 0.9            # the registered evidence point for the TT rank asserts
ARM = "A"
TOL_EXACT = 1e-12       # the contract's dense-equality bar (unit gates)
TOL_TRACE = 1e-10       # the Tr(rho*Pi) equality bar (§3 caps row)
KILLER_FLOOR = 1e-6     # a sabotage image must differ by MORE than this (>> TOL_EXACT)
G19_BAR = 4.8e-4        # the Weyl-scale floor of the G1.9 bar (contract §4 G1.9);
#                         the C3 witness unit tests use it as a REPRESENTATIVE bar —
#                         the witness API takes the bar as an argument, so the tests
#                         pin the RULE, not the measured bar (set by G1.9-pre).
OBS_N = int(os.environ.get("QEC_PEPO_TEST_OBS_N", "4096"))  # obs-law MC draws (z=4 band)

_CUDA = torch.cuda.is_available()
requires_cuda = pytest.mark.skipif(not _CUDA, reason="CUDA unavailable — the PEPO engine is GPU-only (S8)")


# --------------------------------------------------------------------------- #
# ADAPTERS (the ONE place to fix if an ambiguous signature detail differs;     #
# contract §1: "ambiguous signatures get ONE adapter at the top")              #
# --------------------------------------------------------------------------- #
#: exception class(es) the pinned raise-set uses — the referee
#: (QutritDM.apply_within_cycle_*) raises ValueError; contract §3 says the raise set
#: "matches the referee EXACTLY", so ValueError is pinned here.
TOKEN_RAISES = (ValueError,)


def _pepo():
    """Runtime-only import of the three parallel-built modules (independence rule)."""
    from error_coupling_simulator.carrier.pepo import dynamics, layout, sampler
    return layout, dynamics, sampler


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


def _c3_stats(sampler_m):
    """Construct the v4.2 C3 stats accumulator (attr-name adapter — the accumulator
    object the amended witness/born APIs thread; contract §4 G1.1 C3 arm-scoping)."""
    for name in ("C3Stats", "C3StatsAccumulator", "NegativityStats",
                 "BornNegativityStats"):
        cls = getattr(sampler_m, name, None)
        if cls is not None:
            return cls()
    for name in ("new_c3_stats", "make_c3_stats", "c3_stats"):
        factory = getattr(sampler_m, name, None)
        if callable(factory):
            return factory()
    pytest.fail(
        "sampler exposes no recognizable C3 stats accumulator (tried C3Stats/"
        "C3StatsAccumulator/NegativityStats/BornNegativityStats/new_c3_stats/"
        "make_c3_stats/c3_stats) — fix the _c3_stats adapter")


def _c3_ndraws(stats) -> int:
    """Read the Born-draw count off the C3 stats accumulator (attr-name adapter)."""
    for name in ("n_draws", "n", "count", "draws", "n_total"):
        v = getattr(stats, name, None)
        if v is not None:
            return int(v() if callable(v) else v)
    pytest.fail(
        "C3 stats accumulator exposes no recognizable draw count (tried "
        "n_draws/n/count/draws/n_total) — fix the _c3_ndraws adapter")


def _witness(sampler_m, q_raw: float, tr: float, ledger: list, g19_bar: float,
             stats, log_only: bool = False):
    """Call the v4.2 ``negativity_witness`` (stats accumulator + ``log_only``) —
    the ONE place to fix if the amended signature's parameter names differ."""
    fn = sampler_m.negativity_witness
    try:
        return fn(q_raw, tr, ledger, g19_bar, stats=stats, log_only=log_only)
    except TypeError as e:
        if "stats" in str(e) or "log_only" in str(e):
            return fn(q_raw, tr, ledger, g19_bar, stats, log_only)
        raise


def _born_round(sampler_m, state, stabs, b, arm, rng, *, R_n: int, R_x: int,
                D_cap: int, g19_bar: float, stats):
    """Call the v4.2 ``born_sample_round`` with the C3 stats accumulator threaded —
    the ONE place to fix if the amended stats-kwarg name differs."""
    fn = sampler_m.born_sample_round
    for kw in ("stats", "c3_stats"):
        try:
            return fn(state, stabs, b, arm, rng, R_n, R_x, D_cap,
                      g19_bar=g19_bar, **{kw: stats})
        except TypeError as e:
            if kw in str(e):
                continue
            raise
    pytest.fail("born_sample_round accepts neither a 'stats' nor a 'c3_stats' "
                "keyword — fix the _born_round adapter")


def _has_would_trip(ledger: list) -> bool:
    """True iff the ledger carries a v4.2 ``log_only`` would-trip marker entry
    (``kind == 'c3_would_trip'`` or a truthy ``c3_would_trip`` field)."""
    for e in ledger:
        if isinstance(e, dict) and (e.get("kind") == "c3_would_trip"
                                    or e.get("c3_would_trip")):
            return True
    return False


# --------------------------------------------------------------------------- #
# Helpers (memory-lean dense comparison + dense obs/caps references)           #
# --------------------------------------------------------------------------- #
def _max_abs_diff(a: torch.Tensor, b: torch.Tensor, block: int = 2048) -> float:
    """Chunked max-abs difference (never materializes a full 5.77-GiB temp at n=9)."""
    assert a.shape == b.shape, (a.shape, b.shape)
    worst = 0.0
    for i0 in range(0, a.shape[0], block):
        d = float((a[i0:i0 + block] - b[i0:i0 + block]).abs().max().item())
        worst = max(worst, d)
    return worst


def _free() -> None:
    if _CUDA:
        torch.cuda.empty_cache()


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
    """The §3-pinned obs-law composition, hand-built on the DENSE terminal rho.

    H-rotate the X-flagged LOGICAL sites, then the per-site diagonal F0/F1 with the
    PINNED formulas F1 = |1><1| + b|2><2|, F0 = |0><0| + (1-b)|2><2|; parity over the
    LOGICAL support ONLY; XOR m.  ``swap_b=True`` builds the FORBIDDEN
    coherent-double-swap variant (b <-> 1-b in the leaked rows) for the KILLER.
    Returns P(obs = 1).
    """
    from error_coupling_simulator.carrier.exact.qutrit_dm import qutrit_hadamard

    n = round(math.log(rho.shape[0]) / math.log(3))
    assert 3 ** n == rho.shape[0]
    h = qutrit_hadamard(rho.device)
    work = rho
    x_sites = [s for s, p in logical.items() if str(p).upper() == "X"]
    for s in x_sites:
        # H rho H^dag on the logical X-site (H is Hermitian: H == H^dag)
        work = _left_mul_site(work, h, s, n)
        work = _left_mul_site(work.conj().transpose(-1, -2), h, s, n).conj().transpose(-1, -2)
    diag = torch.diagonal(work).real
    del work
    b1 = (1.0 - float(b)) if swap_b else float(b)
    # f1(t) = P(site reads "1"): t=0 -> 0, t=1 -> 1, t=2 -> b   (pinned formulas)
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
    ket vs bra on at least one of ``sites`` — exactly the entries the v4.2 arm-C
    dephase mask zeroes (contract §3, entry 1 iff ``(t>=2) == (t'>=2)``). The arm-C
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


# --------------------------------------------------------------------------- #
# Fixtures (real-Google d3 schedule + the p1c within-cycle cell)               #
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def sched():
    """The REAL d3_at_q6_7 XZZX schedule + r10 within-cycle streams (contract F5).

    Skip justification: F5 pins the layout to the real Google patch parsed by
    ``xzzx_parser`` — a textbook stand-in would silently change every frozen number
    (cut site list, n_cross, the 16-gap), so absence of the local dataset is a SKIP,
    never a fallback.
    """
    xp = pytest.importorskip("qec_twin.forward.exact.xzzx_parser")
    r01c, r01m = xp.default_r01_paths()
    r10c, r10m = xp.default_r10_paths()
    if not (r01c.is_file() and r01m.is_file() and r10c.is_file() and r10m.is_file()):
        pytest.skip("d3 XZZX r01/r10 real-Google circuits absent under "
                    "DEFAULT_DATASET_ROOT (contract F5: real patch only, no fallback)")
    s = xp.parse_xzzx_circuit(r01c, r01m, verify=True)
    s = s.with_within_cycle_streams(xp.parse_within_cycle_streams(r10c, r10m))
    assert int(s.n_data) == 9 and len(s.stabilizers) == 8, (s.n_data, len(s.stabilizers))
    return s


@pytest.fixture(scope="session")
def wc(sched):
    """The p1c within-cycle cell: calibrated theta, leak Kraus, per-pos token streams."""
    if not _CUDA:
        pytest.skip("CUDA unavailable — the within-cycle cell is built on the GPU host")
    from qec_twin.forward.exact import xzzx_parser as xp
    from qec_twin.forward.scalable.sv_sampler import RunSpec, SvSampler
    from qec_twin.mechanisms.qutrit_teachers import calibrate_theta_for_wg_l1

    r01c, r01m = xp.default_r01_paths()
    theta = float(calibrate_theta_for_wg_l1(WG_L1_TARGET, g_seep=G_SEEP, g_heat=G_HEAT))
    host = SvSampler(device="cuda")
    spec = RunSpec(circuit_path=r01c, metadata_path=r01m, m=0, theta=theta,
                   g_seep=G_SEEP, g_heat=G_HEAT, arm=ARM, b=B_BIAS,
                   readout_conv="biased_b", N=1, base_seed=0, R=1, dtype="c128")
    leak_t, leak_ev = host.build_within_cycle_leak(spec)
    assert leak_ev["cptp_residual"] < TOL_EXACT, leak_ev  # C4 on the referee-side Kraus
    marsh = host.marshal_within_cycle(sched, leak_t, R=1)
    return {
        "sched": sched,
        "theta": theta,
        "leak_t": leak_t,                       # (n_kraus, 3, 3) complex128 cuda
        "leak_list": list(marsh.leak_kraus),
        "streams": dict(marsh.streams_by_pos),
        "stabs": sched.stab_paulis(),
        "host": host,
    }


def _fresh_referee(sched):
    """A fresh exact-DM oracle with the real code geometry (the G1.0/G1.x referee)."""
    from qec_twin.forward.scalable.sv_sampler import SvSampler
    return SvSampler(device="cuda").within_cycle_dm_engine(sched)


def _prep_pair(wc, seed: int, *, n_ops: int = 5, leak_pump: tuple[int, ...] = (),
               m: int = 0):
    """A mirrored (PepoState, QutritDM) pair evolved through the SAME random
    single-site token program (H/X/LEAK) from |m>_L — the 'random small state' of the
    contract's unit rows.  ``leak_pump`` sites get extra LEAK slices (builds |2> mass
    so the b-dependent branches are exercised NON-vacuously — the scrutinize-vacuous
    rule: without leaked mass, b never enters and a b-bug is invisible)."""
    layout_m, dynamics_m, _ = _pepo()
    state = layout_m.build_codestate_pepo(wc["sched"], m, device="cuda")
    eng = _fresh_referee(wc["sched"])
    eng.init_logical(m)
    prog: list[tuple[str, int]] = []
    r = np.random.default_rng(seed)
    for _ in range(n_ops):
        prog.append((str(r.choice(["H", "X", "LEAK"])), int(r.integers(0, 9))))
    for s in leak_pump:
        prog.extend([("LEAK", int(s))] * 4)  # ~one full cycle of exp(L/4) slices
    for tok, site in prog:
        dynamics_m.apply_token_stream(state, {site: (tok,)}, wc["leak_t"])
        eng.apply_within_cycle_premeasure({site: (tok,)}, wc["leak_list"])
    return state, eng


def _pick_stabs(sched):
    """(weight-4 X-containing, weight-2) supports from the REAL schedule."""
    w4 = next(dict(s.paulis) for s in sched.stabilizers
              if len(s.paulis) == 4
              and any(str(p).upper() == "X" for p in s.paulis.values()))
    w2 = next(dict(s.paulis) for s in sched.stabilizers if len(s.paulis) == 2)
    return w4, w2


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
        # §2: every frozen number is defined at the EXPLICIT site list A=[0,1,2]|B=[3..8]
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
        # §2 representation: site tag Q{pos}; fused phys index k{pos} of dim 9;
        # tensors torch-cuda-complex128 ALWAYS (S8).
        layout_m, _, _ = _pepo()
        state = layout_m.build_codestate_pepo(wc["sched"], 0, device="cuda")
        for pos in range(9):
            assert f"Q{pos}" in state.tn.tag_map, f"missing site tag Q{pos}"
            assert int(state.tn.ind_size(f"k{pos}")) == 9, f"fused leg k{pos} dim != 9"
        for t in state.tn:
            assert torch.is_tensor(t.data), "site tensor is not a torch tensor"
            assert t.data.dtype == torch.complex128, t.data.dtype
            assert t.data.is_cuda, "site tensor not on CUDA (S8)"
        assert isinstance(state.ledger, list)
        del state
        _free()


# =========================================================================== #
# G1.0 — codestate == oracle (m = 0 AND m = 1), 1e-12 max-abs                  #
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
        assert worst <= TOL_EXACT, f"G1.0 m={m}: max-abs {worst:.3e} > 1e-12"
        del dense, eng, state
        _free()


# =========================================================================== #
# token ops — H/X/LEAK/Y == the QutritDM dense update; the pinned raise-set    #
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
        # terminal=True must be a NO-OP (F1: the terminal round drops the post-M Y)
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
        # §3 row 3 (v2 fix): the referee does NOT raise on arbitrary post-M tokens —
        # a raises-on-unknown engine would split engine vs referee.  Must be a no-op.
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
        # §3: exact fused-leg TT ranks == (2*min(w_L, w_R) + 1)^2 per bond for
        # arm A, b = 0.9 (the registered evidence point): (9, 25, 9) at w=4, (9,) at w=2.
        layout_m, dynamics_m, _ = _pepo()
        w4, w2 = _pick_stabs(wc["sched"])
        lay = layout_m.PepoLayout.from_sched(wc["sched"])
        tt4 = dynamics_m.stab_channel_tt(w4, 0, B_BIAS, ARM, lay, "cuda")
        assert _tt_ranks(tt4) == (9, 25, 9), _tt_ranks(tt4)
        tt2 = dynamics_m.stab_channel_tt(w2, 0, B_BIAS, ARM, lay, "cuda")
        assert _tt_ranks(tt2) == (9,), _tt_ranks(tt2)

    def test_arm_c_dense_equality_certifies_dephase_mask(self, wc):
        """v4.2 ARM-C DEPHASE row (contract §3): the engine's arm='C' weight-4
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
        # §3 v3 domain pin: at b = 0.5 the product classes collapse (w=4 mid-bond <= 9);
        # at b in {0, 1} the bound is 4.  Outside the domain the assert is rank <= the
        # domain bound, NEVER == — and the build must not raise.
        layout_m, dynamics_m, _ = _pepo()
        w4, _ = _pick_stabs(wc["sched"])
        lay = layout_m.PepoLayout.from_sched(wc["sched"])
        tt = dynamics_m.stab_channel_tt(w4, 0, float(b_dom), ARM, lay, "cuda")
        ranks = _tt_ranks(tt)
        assert len(ranks) == 3
        assert all(r <= bnd for r, bnd in zip(ranks, (9, 25, 9))), ranks
        assert ranks[1] <= mid_bound, (b_dom, ranks)


# =========================================================================== #
# KILLERs — sabotage variants DEMONSTRATED to break the dense equality (G1.5)  #
# =========================================================================== #
@requires_cuda
class TestKillers:
    def test_k_corrupt_stab_letter_swap_breaks_dense_equality(self, wc):
        """CorruptStab: flip ONE support site's X/Z letter (wrong support content,
        path-preserving so the TT still builds) — the branch must DIVERGE from the
        true-referee update by >> the 1e-12 gate bar.  (First-run finding 2026-07-10:
        the original two-site X<->Z swap assumed BOTH letters present in the w4 stab
        and StopIteration'd on the real patch's single-letter stab; a one-site letter
        flip is the same sabotage class without the both-letters assumption.)"""
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
        FIRST-RUN FINDING (2026-07-10): every compiled-circuit primitive is a REAL
        superoperator in this basis (H/X real; Y (x) conj(Y) real; sqrt(E_s) real;
        the within-cycle leak Kraus measured real — evolved max|Im| ~ 3e-23), so
        circuit-reachable rho is real-symmetric and the transpose sabotage is
        INVISIBLE on any in-circuit prep.  The killer therefore injects a SYNTHETIC
        complex-phase unitary Kraus diag(1, e^{i pi/4}, 1) (single-element, exactly
        CPTP) through the PUBLIC LEAK seam on BOTH engine and referee — a valid
        instrument check: the discriminator must fire on some valid CPTP input, not
        necessarily a circuit-reachable one."""
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
# gap_rank — the §3 v4.1 window-bound rule, case by case                       #
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
        # v4.1 sigma_k guard on a rank-deficient window: the floor filter excludes
        # every sub-floor k from candidacy, so the largest ABOVE-floor k (= 3 here)
        # qualifies via ratio := inf (sigma_4 <= 1e-12*sigma_1) and wins on the MAIN
        # route — structurally equal to the count of sigma > floor.  What this
        # certifies: the guard-removal mutant DIES (without the floor filter, k = 16
        # would qualify via inf and win -> rank 16 != 3).  What it does NOT exercise:
        # the literal `if not candidates` count-fallback clause is DEAD in-domain —
        # after the s[0] <= 0 early return, k = 1 always passes the sigma_k floor, so
        # candidates is never empty (refuter-proven; re-review 2026-07-10 F2 —
        # contract §3 wording corrected the same day).
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
        # the v4 fix itself: a HUGE gap at k = 20 > D_cap = 16 must NOT win; the
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
        # PRIMARY (v4.2 EXACT-PROBABILITY SEAM, contract §3): the engine-side exact
        # P(obs=1) composition — through the SAME effect-construction code the
        # sampling path uses — held to the 1e-10 bar vs the dense composition.
        for m in (0, 1):
            p_eng = float(sampler_m.terminal_readout_obs_prob(
                copy.deepcopy(state), logical, isx, B_BIAS, m))
            assert abs(p_eng - p_ref[m]) <= TOL_TRACE, (
                f"exact obs seam m={m}: engine {p_eng:.12e} vs dense {p_ref[m]:.12e} "
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
        """KILLER (kills the coherent-double-swap), ENGINE-invoking per the v4.2
        EXACT-PROBABILITY SEAM: the ENGINE's exact obs probability must MATCH the
        pinned dense composition (1e-10) AND DIFFER from the b <-> (1-b) swapped
        composition (> 1e-6) on a leaked state.  (The pre-v4.2 variant compared the
        test's own dense referee to itself and never invoked the engine — the
        Stage-4 vacuity catch.)"""
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
# s_to_det / det_to_s — round-trip + equality with seam.py's own fold          #
# =========================================================================== #
class TestDetectorFold:
    """Host-side conventions; no CUDA required (seam.py is numpy-only)."""

    def test_round_trip_and_seam_equality(self):
        _, _, sampler_m = _pepo()
        from qec_twin.forward.scalable import seam
        from qec_twin.forward.scalable.sv_sampler import SvSampler

        R, n_stab, N = 4, 8, 32
        rng = np.random.default_rng(2026)
        s = rng.integers(0, 2, size=(N, R * n_stab)).astype(np.uint8)
        flips = rng.integers(0, 2, size=N).astype(np.uint8)
        # seam.py's OWN fold (the canonical convention statement)
        det_ref, _obs = seam.teacher_shots_to_events(
            SvSampler.pack_shots(s, flips), n_stab, R)
        for i in range(N):
            det_i = _fold_call(sampler_m.s_to_det, s[i], R, n_stab)
            assert np.array_equal(det_i, det_ref[i]), (
                f"shot {i}: s_to_det != seam fold\n got {det_i}\n exp {det_ref[i]}")
            s_back = _fold_call(sampler_m.det_to_s, det_i, R, n_stab)
            assert np.array_equal(s_back, s[i]), f"shot {i}: det_to_s(s_to_det) != id"
            det_back = _fold_call(
                sampler_m.s_to_det, _fold_call(sampler_m.det_to_s, det_ref[i], R, n_stab),
                R, n_stab)
            assert np.array_equal(det_back, det_ref[i]), (
                f"shot {i}: s_to_det(det_to_s) != id")

    def test_det_to_s_is_prefix_xor(self):
        # §3 pinned inversion: s(r, j) = XOR_{r' <= r} det(r', j)
        _, _, sampler_m = _pepo()
        R, n_stab = 5, 8
        rng = np.random.default_rng(7)
        det = rng.integers(0, 2, size=(R, n_stab)).astype(np.uint8)
        s = _fold_call(sampler_m.det_to_s, det.reshape(-1), R, n_stab).reshape(R, n_stab)
        expect = np.bitwise_xor.accumulate(det, axis=0) % 2
        assert np.array_equal(s, expect.astype(np.uint8))


# =========================================================================== #
# negativity_witness — C3 rules (i)/(ii); healthy pass; sign-flip sabotage     #
# =========================================================================== #
class TestNegativityWitness:
    """C3 (contract §4 G1.9, v4.1 rules + the v4.2 stats/log_only signature): (i) any
    SINGLE raw Born weight q_raw < -(10x bar) => STOP; (ii) the MEAN over all Born
    draws — accumulated on the C3 STATS OBJECT threaded through the calls, never a
    ledger rescan — of max(0, -q_raw)/Tr(rho) > bar => STOP; STOP ==
    RuntimeError('C3_STOP: ...').  ``log_only=True`` (the v4.2 G1.1 C3 arm-scoping:
    the R=4 exerciser arm) NEVER raises — a would-trip is recorded as a
    ``c3_would_trip`` ledger entry (an S9 finding), the draw still counted.
    The bar is passed in (set by G1.9-pre at run time); units use the Weyl floor."""

    def test_healthy_inputs_pass(self):
        _, _, sampler_m = _pepo()
        ledger: list = []
        stats = _c3_stats(sampler_m)
        rng = np.random.default_rng(11)
        for _ in range(50):
            q = float(rng.uniform(0.01, 1.0))
            _witness(sampler_m, q, 1.0, ledger, G19_BAR, stats)
        # tiny negative round-off well under both bars must also pass
        for _ in range(10):
            _witness(sampler_m, -1e-9, 1.0, ledger, G19_BAR, stats)
        assert _c3_ndraws(stats) == 60, (
            f"C3 stats accumulator counted {_c3_ndraws(stats)} draws != 60")

    def test_rule_i_single_weight_trips(self):
        _, _, sampler_m = _pepo()
        with pytest.raises(RuntimeError, match="C3_STOP"):
            _witness(sampler_m, -10.5 * G19_BAR, 1.0, [], G19_BAR,
                     _c3_stats(sampler_m))

    def test_rule_ii_mean_negative_mass_trips(self):
        # each draw is ABOVE the rule-(i) bar (-2x bar > -10x bar) but the per-draw
        # mean negative mass 2x bar > bar => rule (ii) must fire — evaluated off the
        # SAME stats accumulator threaded through every call (v4.2 signature).
        _, _, sampler_m = _pepo()
        ledger: list = []
        stats = _c3_stats(sampler_m)
        tripped = False
        try:
            for _ in range(50):
                _witness(sampler_m, -2.0 * G19_BAR, 1.0, ledger, G19_BAR, stats)
        except RuntimeError as e:
            assert "C3_STOP" in str(e), str(e)
            tripped = True
        assert tripped, "rule (ii) never fired on mean negative mass 2x the bar"

    def test_log_only_would_trip_logged_never_raises(self):
        """v4.2 C3 arm-scoping (G1.1 R=4 exerciser arm): a rule-(i)-grade weight
        under ``log_only=True`` must NOT raise; the would-trip is REPORTED as a
        ``c3_would_trip`` ledger entry and the draw still counts on the stats
        accumulator."""
        _, _, sampler_m = _pepo()
        ledger: list = []
        stats = _c3_stats(sampler_m)
        _witness(sampler_m, -20.0 * G19_BAR, 1.0, ledger, G19_BAR, stats,
                 log_only=True)  # a rule-(i) trip magnitude — must NOT raise
        assert _has_would_trip(ledger), (
            "log_only would-trip left no c3_would_trip ledger entry (the S9 finding "
            "record is mandatory — contract §4 G1.1 C3 arm-scoping)")
        assert _c3_ndraws(stats) == 1, (
            f"log_only draw not counted on the stats accumulator "
            f"({_c3_ndraws(stats)} != 1)")

    def test_k_sign_flip_sabotage_trips(self):
        # the registered G1.9 sabotage: a healthy Born weight with its sign flipped
        _, _, sampler_m = _pepo()
        healthy = 0.31
        _witness(sampler_m, healthy, 1.0, [], G19_BAR,
                 _c3_stats(sampler_m))  # passes as-is
        with pytest.raises(RuntimeError, match="C3_STOP"):
            _witness(sampler_m, -healthy, 1.0, [], G19_BAR, _c3_stats(sampler_m))


# =========================================================================== #
# expect_site_caps / stab_expectation / pepo_trace — Tr(rho * Pi) seams        #
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
        # §3: caps = GENERAL single-site (3,3) operators; absent sites get the
        # trace-cap.  Dense reference: Tr((x)M rho) via row-side contraction on the
        # referee's mirrored rho (independent of the engine's contraction path).
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
        # §3: Tr(E_s rho) = 1/2 Tr(rho) + 1/2 (-1)^s Tr(rho (x)M_q) — checked against
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


# =========================================================================== #
# Integration tier (v4.2) — the truncation/sampling spine EXECUTES end to end #
# =========================================================================== #
def _referee_nonselective_round(eng, stabs: list, b: float, arm: str) -> None:
    """The F3 branch-sum loop on the exact-DM referee (mirrors
    ``dynamics.nonselective_round``'s given-order semantics; memory-lean: in-place
    accumulate, never four live 3^9 x 3^9 copies)."""
    for paulis in stabs:
        base = eng.rho.clone()
        eng.project_stabilizer(paulis, 0, b, arm)
        r0 = eng.rho
        eng.rho = base
        eng.project_stabilizer(paulis, 1, b, arm)
        r0.add_(eng.rho)
        eng.rho = r0


def _max_bond_dim(state) -> int:
    """Largest virtual-bond dimension of the PEPO (inds shared by two tensors)."""
    mx = 1
    for ix, tids in state.tn.ind_map.items():
        if len(tids) == 2:
            mx = max(mx, int(state.tn.ind_size(ix)))
    return mx


@requires_cuda
class TestIntegrationTier:
    """v4.2 integration tier (CUDA, real-patch fixture, small and fast): the
    previously-untested truncation/sampling spine EXECUTES end to end.  EXECUTION
    SMOKE + SANITY, not the gate — the registered record/marginal bars live at
    G1.1/G1.2 (contract §4); the 1e-2 max-abs and 20% bars here are REGISTERED
    loose class-(c) smoke bars, documented as such."""

    def test_nonselective_round_truncating_matches_oracle(self, wc):
        # (a) 2 rounds at D_cap=8 — FORCED below the exact insertion rank so
        # ntu_truncate's metric path EXECUTES (precondition asserted off the ledger).
        layout_m, dynamics_m, _ = _pepo()
        stabs = [dict(p) for p in wc["stabs"]]
        d_cap = 8
        state, eng = _prep_pair(wc, seed=160, n_ops=6, leak_pump=(0, 2, 4, 6))
        for _ in range(2):
            dynamics_m.nonselective_round(state, stabs, B_BIAS, ARM, d_cap)
            _referee_nonselective_round(eng, stabs, B_BIAS, ARM)
        entries = [e for e in state.ledger
                   if isinstance(e, dict) and e.get("op") == "ntu_truncate"]
        assert entries, "no ntu_truncate ledger entries — the truncation spine never ran"
        assert any(int(e["exact_rank"]) > d_cap for e in entries), (
            f"D_cap={d_cap} never fell below the exact insertion rank — the NTU "
            f"metric path did NOT execute (vacuity: pump more LEAK / add rounds / "
            f"lower D_cap)")
        for e in entries:
            assert float(e["discarded"]) >= 0.0, e
            assert "precut_discarded" in e, (
                f"v4.2 precut_discarded ledger field missing from a truncation "
                f"entry: {e}")
            assert math.isfinite(float(e["ntu_eps"])), e
        worst = _max_abs_diff(layout_m.dense_rho(state), eng.rho)
        assert worst <= 1e-2, (
            f"truncating 2-round smoke: max-abs {worst:.3e} > the REGISTERED loose "
            f"1e-2 smoke bar (execution/sanity tier — G1.2 is the real record gate)")
        del state, eng
        _free()

    def test_ntu_precut_fires_in_regime_and_zero_is_the_sabotage_image(self, wc):
        """v4.2 NTU PRE-COMPRESSION executes (re-review 2026-07-10 F3 — the precut
        path was never asserted to RUN anywhere; a deleted/silent precut left the
        suite green).  Drive a REAL support-path insertion into the precut regime
        (exact insertion rank > 4*D_cap at D_cap=2) by growing one w4 stab branch
        on a round-mixed state WITHOUT truncation, then call ``ntu_truncate``
        directly on the largest grown bond:

          * PRECONDITION (class c): ``exact_rank > 4*D_cap`` on the targeted
            entry — the regime was actually REACHED (a miss means the HARNESS
            construction is wrong, not the precut gate);
          * ``precut_discarded`` STRICTLY > 0.0 (every precut-dropped sigma is
            above the 1e-12*sigma_1 floor BY CONSTRUCTION of re, so the dropped
            squared weight cannot vanish) and ``dim_out == D_cap``
            (D_kept = min(D_cap, 4*D_cap)); no cross-field relation (e.g.
            precut_discarded <= discarded) is asserted — the ledger schema does
            not pin one;
          * KILLER pairing (G1.5 discipline, both arms EXECUTE real code): the
            SAME insertion (deepcopy, bit-identical tensors) truncated OUT of
            the precut regime (D_cap' >= exact_rank => exact write-back, no
            precut can fire) must report ``precut_discarded == 0.0`` EXACTLY —
            the ledger image a deleted precut (field never set) or a
            fires-but-reports-0.0 mutant emits on EVERY entry — so the strict
            > 0.0 assert above is DEMONSTRATED to trip both registered
            sabotages on an in-regime insertion."""
        _, dynamics_m, _ = _pepo()
        stabs = [dict(p) for p in wc["stabs"]]
        d_cap = 2                                   # precut threshold 4*D_cap = 8
        state, eng = _prep_pair(wc, seed=163, n_ops=6, leak_pump=(0, 2, 4, 6))
        del eng
        _free()
        # mix + grow: one truncating round (bonds -> <= 8), then ONE w4 branch
        # WITHOUT truncation so a support-path bond carries an insertion of
        # exact rank >> 8 (path bonds grow x(9, 25, 9)).
        dynamics_m.nonselective_round(state, stabs, B_BIAS, ARM, 8)
        w4, _ = _pick_stabs(wc["sched"])
        tt = dynamics_m.stab_channel_tt(w4, 0, B_BIAS, ARM, state.layout, "cuda")
        dynamics_m.apply_stab_branch(state, tt)
        # target = the largest virtual bond (inds shared by exactly 2 tensors);
        # after the untruncated w4 branch that is a support-path bond.
        cands = [(ix, int(state.tn.ind_size(ix)))
                 for ix, tids in state.tn.ind_map.items() if len(tids) == 2]
        bond, dim = max(cands, key=lambda c: c[1])
        assert dim > 4 * d_cap, (
            f"largest grown bond dim {dim} <= {4 * d_cap} — the growth "
            f"construction is wrong (a mid-path bond ~ 8*25 was expected)")
        mirror = copy.deepcopy(state)               # same insertion, for the pair
        entry = dynamics_m.ntu_truncate(state, bond, d_cap)
        # PRECONDITION (class c): the precut regime was actually reached.
        assert int(entry["exact_rank"]) > 4 * d_cap, (
            f"precut precondition FAILED: exact_rank {entry['exact_rank']} <= "
            f"4*D_cap = {4 * d_cap} on bond {bond!r} (dim {dim}) — grow a richer "
            f"insertion (more rounds / more LEAK pump); the harness is wrong, "
            f"not the gate")
        assert float(entry["precut_discarded"]) > 0.0, (
            f"in-regime precut_discarded not strictly positive: {entry} — the "
            f"v4.2 precut did not fire (or its report is broken); every "
            f"precut-dropped sigma is above the 1e-12*sigma_1 floor by "
            f"construction of re, so the dropped weight cannot be 0.0")
        assert int(entry["dim_out"]) == d_cap, entry
        assert math.isfinite(float(entry["ntu_eps"])), entry
        # paired sabotage image: OUT of the regime (D_cap' >= exact_rank with
        # margin => the exact write-back path; the metric is skipped and no
        # precut can fire), the SAME insertion must report 0.0 EXACTLY.
        d_off = int(entry["exact_rank"]) + 8
        entry_off = dynamics_m.ntu_truncate(mirror, bond, d_off)
        assert int(entry_off["exact_rank"]) > 4 * d_cap, (
            f"mirror lost the insertion richness: {entry_off}")
        assert int(entry_off["exact_rank"]) <= 4 * d_off, entry_off  # regime OFF
        assert float(entry_off["precut_discarded"]) == 0.0, (
            f"no-precut entry reports nonzero precut_discarded: {entry_off} — "
            f"the 0.0-when-no-precut schema clause (contract §2 units table) is "
            f"broken and the strict > 0.0 instrument above loses its teeth")
        del state, mirror
        _free()

    def test_expect_site_caps_compressed_path_executes(self, wc):
        # (b) R_n=4, below the exact d3 boundary 16, so tensor_network_1d_compress
        # actually RUNS; the arm is under-resolved by design — finite + 20% loose.
        _, dynamics_m, sampler_m = _pepo()
        stabs = [dict(p) for p in wc["stabs"]]
        state, eng = _prep_pair(wc, seed=161, n_ops=5, leak_pump=(1, 5))
        del eng
        _free()
        dynamics_m.nonselective_round(state, stabs, B_BIAS, ARM, 16)  # grow bonds
        assert _max_bond_dim(state) > 4, (
            "no virtual bond exceeds R_n=4 — the compressed fit path would be "
            "vacuous (grow the state first)")
        caps = {}
        for site, diag in ((1, (0.8, 0.3, 0.6)), (7, (0.5, 0.9, 0.4))):
            caps[site] = torch.diag(
                torch.tensor(diag, dtype=torch.complex128)).to("cuda")
        exact = complex(sampler_m.expect_site_caps(state, caps))  # exact route
        assert abs(exact) >= 0.05, (
            f"exact cap expectation {exact!r} too small for a 20% relative read — "
            f"adjust the cap diagonals (non-vacuity precondition)")
        got = complex(sampler_m.expect_site_caps(state, caps, R_n=4))  # compressed
        assert math.isfinite(got.real) and math.isfinite(got.imag), got
        assert abs(got - exact) <= 0.20 * abs(exact), (
            f"R_n=4 compressed caps read {got!r} vs exact {exact!r} beyond the "
            f"loose 20% smoke band (the arm is under-resolved by design)")
        del state
        _free()

    def test_born_sample_round_smoke(self, wc):
        # (c) one shot, R=1, D_cap=16, seeded rng: 8 bits, raw-q range sanity,
        # born_negativity ledger entries, the C3 stats accumulator counts 8 draws.
        pytest.skip(
            "F-SEL-1 (contract v4.3, adjudicated 2026-07-10, option C): the selective "
            "per-bond-D sampling arm is infeasible under the current truncation toolkit "
            "(engine verified faithful vs the exact referee at 1e-15 — E1; loop-trapped "
            "rank — E2/E3); G1.1 demoted to characterization, born_sample_round is not a "
            "green bar. REGISTERED skip (tests/_support/skip_allowlist.json); revisit on "
            "the loop-update probe outcome.")
        _, _, sampler_m = _pepo()
        stabs = [dict(p) for p in wc["stabs"]]
        assert len(stabs) == 8, len(stabs)
        state, eng = _prep_pair(wc, seed=162, n_ops=4, leak_pump=(0, 4))
        del eng
        _free()
        stats = _c3_stats(sampler_m)
        bits = _born_round(sampler_m, state, stabs, B_BIAS, ARM, _rng(2027),
                           R_n=16, R_x=16, D_cap=16, g19_bar=G19_BAR, stats=stats)
        assert len(bits) == 8 and all(int(x) in (0, 1) for x in bits), bits
        renorms = [e for e in state.ledger
                   if isinstance(e, dict) and e.get("kind") == "renorm"]
        assert len(renorms) == 8, f"{len(renorms)} renorm ledger entries != 8 stabs"
        for e in renorms:
            for q in (float(e["q0_raw"]), float(e["q1_raw"])):
                assert -G19_BAR <= q <= 1.0 + 1e-6, (
                    f"raw Born weight {q!r} outside the [-bar, 1+eps] sanity range: {e}")
        negs = [e for e in state.ledger
                if isinstance(e, dict) and e.get("kind") == "born_negativity"]
        assert negs, "no born_negativity ledger entries emitted by the round"
        assert _c3_ndraws(stats) == 8, (
            f"C3 stats accumulator counted {_c3_ndraws(stats)} draws != 8")
        del state
        _free()


# --------------------------------------------------------------------------- #
# NUMERICAL_ZERO wiring sanity (the contract's 1e-12-grade floor source)       #
# --------------------------------------------------------------------------- #
def test_numerical_zero_is_the_contract_floor():
    assert NUMERICAL_ZERO == 1e-12
