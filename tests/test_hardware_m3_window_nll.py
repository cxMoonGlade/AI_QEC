"""R2-lite M3 -- window-level held-out syndrome NLL on the d=29 release.

PRE-REGISTRATION (docs/metric_results.md "2026-06-09 -- R2-lite M3
PRE-REGISTRATION", three-agent independent-derivation panel, recorded BEFORE
build/run; ADR 0007 Decision 4 M3 + milestone addendum; METRICS.md hardware
ledger: held-out per-shot syndrome NLL). Claim scope: R2-lite only -- no do(),
no attribution; q claims are q^eff ONLY (exact reset/readout gauge); the
factorized window twin at repeats=1-class hardware contexts sits in H2's
theorem-backed dangerous cell, hence NLL-prediction claims only.

FROZEN DESIGN: 19 clean interior 6-site windows ({15, 19} excluded, M2);
forward = Candidate A exact d=5 parity-backend interior forward (2**5
register), 4 fully-interior detectors, boundary marginalized (M2 X2 <= 4.24%);
classical per-site readout flip q_j (exact 2-bit/site convolution);
non-selective burn-in (dephase_parity; fixed-point pin <= 1e-9, B=40 doubling
<= 320) + 3 enumerated rounds (4096 branches); family F_blk = disjoint 2-layer
blocks, starts t in {80, 82, ..., 998} (460 blocks/shot/window), composite
marginal likelihood, s-only, bases never pooled. Split: train = sample_00;
held-out gate = samples_01..04 (4e5 shots); drift-isolated fallback =
sample_00 second half (train on first half). Baselines PINNED: naive = stim MC
1e5 shots seed 20260609 of circuit_noisy_si1000.stim through the IDENTICAL
extractor, KT-smoothed; pij-DEM = train-split Spitz-exact entries,
layer-pooled [80,999], in-block edges {dt=0: di<=3} U {dt=1: di<=2}, clamp
[0, 1/2), mean-matching half-edges, exact 256-cell WHT law. Twin: 5
Stinespring channels + 4 q_logits/window, per-window independent fits, LBFGS
steps=300, seeds {0,1}, train selection. Paired shot bootstrap B=1000 seed
20260609.

GATES (hard asserts):
  P1  Machinery pins -- any failure = build bug, nothing downstream:
      (a) Pauli-slice = stim d=5 within 5 MC SE @ 1e6;
      (b) fixed-point residual <= 1e-9;
      (c) readout convolution vs flip enumeration <= 1e-12;
      (d) extractor pipeline-identity on sim events;
      (e) in-fiber EXACT flatness: iso-{p01,p10} member swap changes per-shot
          NLL < 1e-9 (control: a rate-direction step moves it thousands of
          sigma) -- failure = phase leak;
      (f) per-qubit Z2 value-relabel invariance < 1e-12 rel -- failure =
          absolute-reference leak;
      (g) reset/readout gauge invariance (record-flip folding identity)
          -- failure = family mis-cut.
  P2  Fisher spectrum at the in-class naive point, BEFORE any fit: rank >= 9
      both bases (top-9 >= 99% trace); Z additionally shows the 3 weak
      |delta_{2,3,4}| directions (Fisher ~ delta^2, eigenvalue split
      reported); X numerical rank 9 (dephasing-symmetric delta ~ 0); coherent
      directions in the numerical null.
  P3  M3 GATE: per basis, 19-window aggregate held-out dNLL(naive - twin) > 0
      at one-sided 99% paired bootstrap. Reported: per-window margin in
      [35, 160] central ~55-60 (X) / [30, 150] ~50-56 (Z) nats/shot; windows
      >= +30 (predict 19/19); NLL_twin sanity [550, 700] (X) / [540, 690] (Z)
      nats/shot/window. Registered decomposition: the margin is ~80-125%
      detector-marginal -- "twin beats naive" is CHEAP; the informative
      numbers are P4/P5/P10.

SIDE-BETS (reported, soft-bound; a reversal is a finding -- re-derive,
re-register):
  P4  W_quiet (19 minus {16,17,18}): G3 = NLL_twin - NLL_pij in [-4, +6]
      central +1, TWO-SIDED; ablation pij,nodiag - pij in [1.0, 3.5].
  P5  Hot-pair windows: G3(17) > max over W_quiet, in [+4, +13]; G3(16),(18)
      in [+2.3, +4.5]; basis-independent <= 15%.
  P6  in-class SI1000 - naive-MC in [0, +3] central +0.7.
  P7  q^eff in [1.1, 1.8]e-2; interior f in [0.9, 1.7]e-2; edge - interior
      ~ +1.2e-3 one-sided; shared-site q replicates within max(10%, 5*SE)
      (explodes on {15,19} = positive control).
  P8  per-sample (01-04) NLL_twin range <= 2 nats/shot absent flagged bursts
      (MAD rule); drift-isolated fallback split reported alongside.
  P10 Budget deficit (train AND held-out): sum p_ij(Delta<=1) -
      (-1/2 ln(1-2f)) >= +5e-3 (X) / +6e-3 (Z) per detector-round at >= 10
      sigma -- the measured pij matrix and marginals are JOINTLY UNREALIZABLE
      by any independent-edges DEM.
  P11 Bunching: Z-basis central-qubit (p01+p10)^2/(4 p01 p10) > 1 at >= 10
      sigma; X = 1 within 2 sigma; an iid DEM is structurally pinned at 1.

FALSIFICATION ROUTING: P1/P2 fail => build bug, nothing downstream. P3 fail
=> re-verify pins + split bookkeeping (a >= 35-nat floor does not vanish
physically); if genuine => publish the negative + the REGISTERED alias
analysis (ADR 0007 M3 fallback). P4 high => class-resolved residual audit ->
back-edge (H3/H4 + ADR 0008 input); low/reversed beyond -4 => audit the pij
construction first. P5 miss => refine the located map. P10 deficit vanishes
=> M1 class means inflated by aggregation. P11 X-basis excess =>
non-dephasing-symmetric X-circuit noise -- a finding. P6-P9 misses =>
findings, H0 precedent.

Heavy fits run once behind module-level lru_cache and persist through the
m3_report fit cache (env QEC_TWIN_M3_FIT_CACHE, default
outputs/m3_fit_cache.pt -- run `python -m qec_twin.hardware.m3_report` first
to populate it). Device: QEC_TWIN_M3_DEVICE (default cuda when available).
"""

from __future__ import annotations

import functools
import os
import warnings

import pytest
import torch

from qec_twin.hardware.dataset import RepCodeD29, resolve_rep29_root

pytestmark = pytest.mark.skipif(
    resolve_rep29_root() is None, reason="R2-lite d29 dataset absent (set QEC_TWIN_HW_DATA)"
)

from qec_twin.hardware import m3_report  # noqa: E402

BASES = ("X", "Z")


def _device() -> str:
    return os.environ.get(
        "QEC_TWIN_M3_DEVICE", "cuda" if torch.cuda.is_available() else "cpu"
    )


def _max_burn_in() -> int:
    return int(os.environ.get("QEC_TWIN_M3_MAX_BURN_IN", "320"))


def _cache_path() -> str:
    return os.environ.get("QEC_TWIN_M3_FIT_CACHE", "outputs/m3_fit_cache.pt")


def _pin_shots() -> int:
    return int(os.environ.get("QEC_TWIN_M3_PIN_SHOTS", str(m3_report.PIN_SHOTS)))


@functools.lru_cache(maxsize=None)
def _ds() -> RepCodeD29:
    return RepCodeD29.from_env()


@functools.lru_cache(maxsize=None)
def _fits(basis: str, split: str = "full"):
    return m3_report.fit_windows(
        _ds(),
        basis,
        m3_report.CLEAN_WINDOWS,
        device=_device(),
        max_burn_in=_max_burn_in(),
        split=split,
        cache_path=_cache_path(),
    )


@functools.lru_cache(maxsize=None)
def _hot_fits(basis: str):
    return m3_report.fit_windows(
        _ds(),
        basis,
        m3_report.HOT_CONTROL_WINDOWS,
        device=_device(),
        max_burn_in=_max_burn_in(),
        cache_path=_cache_path(),
    )


@functools.lru_cache(maxsize=None)
def _per_shot(basis: str):
    laws = m3_report.build_model_laws(
        _ds(), basis, m3_report.CLEAN_WINDOWS, _fits(basis),
        device=_device(), max_burn_in=_max_burn_in(),
    )
    return m3_report.heldout_per_shot(_ds(), basis, m3_report.CLEAN_WINDOWS, laws)


def _soft(condition: bool, message: str) -> None:
    print(message)
    if not condition:
        warnings.warn(f"side-bet out of band (finding, not failure): {message}", stacklevel=2)


# ---------------------------------------------------------------- P1 machinery pins (hard)


def test_p1a_stim_pauli_slice():
    result = m3_report.run_p1a_pauli_slice(shots=_pin_shots(), device=_device())
    print(f"P1a: max |z| {result['max_abs_z']:.2f} (<= 5), TVD {result['tvd']:.2e}")
    assert result["passed"], f"P1a FAIL (build bug): {result}"


def test_p1b_fixed_point():
    result = m3_report.run_p1b_fixed_point(device=_device(), max_burn_in=_max_burn_in())
    for basis, row in result["rows"].items():
        print(f"P1b {basis} (delta={row['delta']:.1e}): residual {row['residual']:.2e} "
              f"at B={row['rounds']}")
    assert result["passed"], f"P1b FAIL (build bug -- fixed point not pinned): {result}"


def test_p1c_readout_convolution_vs_enumeration():
    result = m3_report.run_p1c_convolution_vs_enumeration(device=_device())
    print(f"P1c: max |conv - enum| {result['max_abs_diff']:.2e} (<= 1e-12)")
    assert result["passed"], f"P1c FAIL (build bug): {result}"


def test_p1d_extractor_pipeline_identity():
    result = m3_report.run_p1d_extractor_identity(_ds())
    print(f"P1d: histograms identical {result['histograms_identical']}, "
          f"per-shot vs histogram NLL gap {result['per_shot_vs_histogram_nll_gap']:.2e}")
    assert result["passed"], f"P1d FAIL (build bug): {result}"


def test_p1e_in_fiber_flatness():
    result = m3_report.run_p1e_in_fiber_flatness(device=_device())
    print(f"P1e: swap NLL/shot {result['swap_nll_per_shot']:.2e} (< 1e-9), law diff "
          f"{result['swap_law_max_diff']:.2e}; rate-step control "
          f"{result['rate_step_sigma_units']:.0f} sigma")
    assert result["passed"], f"P1e FAIL (phase leak): {result}"


def test_p1f_z2_swap_invariance():
    result = m3_report.run_p1f_z2_swap(device=_device())
    print(f"P1f: max rel diff {result['max_rel_diff']:.2e} (< 1e-12)")
    assert result["passed"], f"P1f FAIL (absolute-reference leak): {result}"


def test_p1g_reset_readout_gauge():
    result = m3_report.run_p1g_reset_readout_gauge(device=_device())
    print(f"P1g: max |fold gap| {result['max_abs_diff']:.2e} (< 1e-12)")
    assert result["passed"], f"P1g FAIL (family mis-cut): {result}"


# ---------------------------------------------------------------- P2 DOF gate (hard, BEFORE fits)


def test_p2_fisher_rank():
    result = m3_report.run_p2_fisher(device=_device(), max_burn_in=_max_burn_in())
    for basis, row in result["rows"].items():
        eig = row["eigenvalues"]
        print(f"P2 {basis}: rank {row['rank']} (>= 9), top-9 share "
              f"{row['top9_trace_share']:.4%} (>= 99%); weak eigs 10+ {row['weak_eigs_10_plus']}")
        assert row["rank"] >= 9, f"P2 FAIL {basis}: rank {row['rank']} < 9 (DOF gate)"
        assert row["top9_trace_share"] >= m3_report.P2_TOP9_SHARE_MIN, (
            f"P2 FAIL {basis}: top-9 trace share {row['top9_trace_share']:.4%} < 99%"
        )
        assert eig[8] > 0.0, f"P2 FAIL {basis}: ninth eigenvalue not positive"


# ---------------------------------------------------------------- P3 gate (hard, heavy)


def test_p3_gate():
    for basis in BASES:
        result = m3_report.run_p3(basis, m3_report.CLEAN_WINDOWS, _per_shot(basis))
        agg = result["aggregate"]
        print(f"P3 {basis}: aggregate dNLL(naive - twin) {agg['mean']:.2f} nats/shot/window "
              f"(boot q01 {agg['q01']:.2f}, SE {agg['se']:.3f}); margins in {result['band']}: "
              f"{result['margins_in_band']}/19; >= +30: {result['count_ge_30']}/19")
        print(f"P3 {basis} per-window margins: {result['per_window_margin']}")
        assert result["passed"], (
            f"P3 GATE FAIL {basis}: one-sided 99% bootstrap q01 = {agg['q01']:.3f} <= 0 "
            f"-- re-verify pins + split bookkeeping before adjudicating (registered routing)"
        )
        _soft(
            result["count_ge_30"] == len(m3_report.CLEAN_WINDOWS),
            f"P3 {basis}: windows >= +30 nats = {result['count_ge_30']}/19 (predicted 19/19)",
        )
        _soft(
            result["nll_sanity_ok"],
            f"P3 {basis}: NLL_twin per window within sanity {result['nll_sanity_band']}",
        )


# ---------------------------------------------------------------- P4-P11 (reported)


def test_p4_p5_pij_comparison_reported():
    hot = {}
    for basis in BASES:
        result = m3_report.run_p4_p5(basis, m3_report.CLEAN_WINDOWS, _per_shot(basis))
        g3 = result["g3_quiet"]
        hot[basis] = result["hot_g3"]
        _soft(
            result["g3_in_band"],
            f"P4 {basis}: G3 quiet {g3['mean']:.2f} [{g3['q025']:.2f}, {g3['q975']:.2f}] "
            f"in {result['g3_band']}",
        )
        _soft(
            result["ablation_in_band"],
            f"P4 {basis}: pij,nodiag - pij {result['ablation_quiet']:.2f} in "
            f"{result['ablation_band']}",
        )
        _soft(
            result["hot_17_exceeds_quiet_max"],
            f"P5 {basis}: G3(17) {result['hot_g3'][17]:.2f} > quiet max "
            f"{result['quiet_max_g3']:.2f}",
        )
        for w, band in m3_report.P5_BAND.items():
            _soft(
                band[0] <= result["hot_g3"][w] <= band[1],
                f"P5 {basis}: G3({w}) {result['hot_g3'][w]:.2f} in {band}",
            )
    for w in m3_report.HOT_PAIR_WINDOWS:
        x, z = hot["X"][w], hot["Z"][w]
        rel = abs(x - z) / max(abs(x + z) / 2.0, 1e-12)
        _soft(rel <= m3_report.P5_BASIS_REL_TOL,
              f"P5 basis-independence window {w}: |X-Z|/mean {rel:.1%} <= 15%")


def test_p6_in_class_vs_naive_reported():
    for basis in BASES:
        result = m3_report.run_p6(basis, m3_report.CLEAN_WINDOWS, _per_shot(basis))
        _soft(
            result["in_band"],
            f"P6 {basis}: in-class SI1000 - naive-MC {result['in_class_minus_naive']:.2f} "
            f"in {result['band']} (central +0.7)",
        )


def test_p7_parameter_bands_reported():
    for basis in BASES:
        result = m3_report.run_p7(basis, m3_report.CLEAN_WINDOWS, _fits(basis), _hot_fits(basis))
        _soft(
            m3_report.P7_Q_BAND[0] <= result["q_mean"] <= m3_report.P7_Q_BAND[1],
            f"P7 {basis}: q^eff mean {result['q_mean']:.4e} in {result['q_band']} "
            f"({result['q_in_band_frac']:.0%} of entries)",
        )
        _soft(
            m3_report.P7_F_BAND[0] <= result["interior_f_mean"] <= m3_report.P7_F_BAND[1],
            f"P7 {basis}: interior f {result['interior_f_mean']:.4e} in {result['f_band']}",
        )
        _soft(
            result["edge_minus_interior"] > 0.0,
            f"P7 {basis}: edge - interior f {result['edge_minus_interior']:+.2e} "
            f"(predict +{m3_report.P7_EDGE_EXCESS:.1e}, one-sided)",
        )
        _soft(
            result["replicate_worst"] <= m3_report.P7_REPLICATE_REL
            or result["replicate_worst"] <= 5 * max(result["seed_q_gap"].values() or [0.0]),
            f"P7 {basis}: worst shared-site q spread {result['replicate_worst']:.2%} "
            f"within max(10%, 5*SE)",
        )
        if result["hot_control_replicate"]:
            worst_hot = max(result["hot_control_replicate"].values())
            _soft(
                worst_hot > result["replicate_worst"],
                f"P7 {basis}: hot-control {{15,19}} q deviation {worst_hot:.2%} exceeds clean "
                f"{result['replicate_worst']:.2%} (positive control)",
            )


def test_p8_per_sample_stability_reported():
    for basis in BASES:
        result = m3_report.run_p8(basis, m3_report.CLEAN_WINDOWS, _per_shot(basis))
        flagged = {s: sum(row["flagged_shots"].values()) for s, row in result["per_sample"].items()}
        _soft(
            result["in_band"],
            f"P8 {basis}: worst per-window NLL range {result['worst_range']:.2f} <= 2 "
            f"nats/shot (MAD-flagged shots per sample: {flagged})",
        )


def test_p10_budget_deficit_reported():
    for basis in BASES:
        result = m3_report.run_p10(_ds(), basis, verbose=False)
        for split, row in result["rows"].items():
            _soft(
                row["ok"],
                f"P10 {basis}/{split}: deficit {row['deficit']:.3e} (SE {row['se']:.1e}, "
                f"{row['sigma']:.0f} sigma) >= {row['floor']:.0e} at >= 10 sigma",
            )


def test_p11_bunching_reported():
    for basis in BASES:
        result = m3_report.run_p11(basis, _fits(basis))
        _soft(
            result["ordering_ok"],
            f"P11 {basis}: central bunching ratio {result['central_ratio_mean']:.4f} "
            f"(SE {result['central_ratio_se']:.4f}, {result['sigma_above_1']:.1f} sigma above 1; "
            f"Z predicts >= 10 sigma, X predicts |.| <= 2 sigma) "
            f"|delta'| {result['central_delta_prime_mean']:.3f} -- {result['jensen_caveat']}",
        )
