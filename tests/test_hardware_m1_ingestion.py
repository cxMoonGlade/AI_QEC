"""R2-lite M1 -- ingestion parity on the local Google d=29 repetition-code release.

PRE-REGISTRATION (docs/metric_results.md "2026-06-09 -- R2-lite M1 PRE-REGISTRATION",
recorded BEFORE build/run; ADR 0007 Decision 4 M1; theory-first; METRICS.md
hardware-data ledger: detection-event fraction, Spitz Eq. 13 EXACT p_ij). Claim
scope: R2-lite restrictions -- no do(), no mechanism attribution.

GATES (any failure = M1 FAIL -> fix the reader/forward; nothing downstream runs):
  P1  Structure exact, per sample/basis: 28,056 detectors = 28 x 1002 layers
      (1 init + 1000 bulk + 1 final); 28,057 measurements = 28 x 1001 + 29;
      1 observable; 29 sweep bits; b8 bytes/shot 3507/3508/4/1. Exact integers.
  P2  stim m2d on measurements.b8 + sweep_bits.b8 reproduces shipped
      detection_events.b8 and obs_flips_actual.b8 BIT-FOR-BIT, samples
      {00,50,99} x {X,Z}. 0 mismatched bytes (deterministic; zero tolerance).
  P3  Bulk (layers 1-1000) detection fraction, each basis, sample_00 in
      [3.0%, 7.0%] and < 7.7% (published d=3 surface anchor); bootstrap SE < 1e-3.
  P4  p_ij significant support (class-mean > 10*SE) = exactly {time-like dt=1;
      space-like di=1; ONE diagonal orientation (set by CZ-layer order); boundary
      edges} = DEM support of shipped circuit_noisy_si1000.stim; null classes
      (|di|>=2 or |dt|>=2) |mean| < max(1e-4, 5*SE); <1% of null entries beyond
      5*SE; positive long-range leakage/burst tail permitted, REPORTED as
      misspecification direction (M2/H2 back-edge), never gated/attributed.

SIDE-BETS (reported, soft-bound; a reversal is a finding -- re-derive, re-register):
  P5  p_det(X) > p_det(Z); X in [4.0,7.0]% (central ~5.5%), Z in [3.0,6.0]%.
  P6  layer-0/bulk in [0.3, 0.9]; final/bulk in [0.5, 1.5]; bulk flat
      (rel. std over t in [2,999] < 10%, burst outliers reported).
  P7  Class means: time-like in [1.0, 2.5]% (largest class); space-like in
      [0.3, 2.0]% (X >= Z); diagonal in [0.03, 0.6]% with populated/mirror >= 3.
  P8  MC detection fraction of shipped SI1000(p=1e-3) circuit = 2.55% +- 0.65%,
      X ~ Z within 10%.
  P9  obs_flips_actual mean in [0.492, 0.508] each basis.

STATISTICS (pre-registered): sample_00 per basis = 1e5 shots; shot-level
bootstrap (B=1000), shots iid units (within-shot detector correlation -> never
naive binomial); pair set |dt|<=5 same index U |di|<=5 same layer U
|di|<=2 x |dt|<=2 block U 1e4 seeded random far pairs; bases never pooled.
Failure semantics: P1/P2 (or unexplained P3/P4) -> M1 FAIL, fix the reader,
nothing downstream; P3/P4 miss with P2 green + documented physical cause ->
derivation miss, kept honestly, re-registered.

COMMITTED ADJUDICATION (recorded with the build, before any run; see also
qec_twin.hardware.m1_report): P2 converter circuit (ideal vs noisy) is reported,
not tuned -- bit-exactness is required either way. P4 permitted-tail clause:
positive long-range exceedances are reported, never gated; gating violations are
a missing DEM-support class, a significant non-null non-DEM class (e.g. the
mirror diagonal), a NEGATIVE null-class mean beyond max(1e-4, 5*SE), or null
entries with negative-side exceedance >= 1% / total exceedance >= 1% at < 90%
positive share. P6 burst outliers: beyond median +- 5*(1.4826*MAD). Class-mean
SEs: shot-level bootstrap (B=1000) of the delta-method per-shot projection;
per-entry SEs: analytic delta method (exact trinomial moment covariance).
"""

from __future__ import annotations

import functools
import os
import warnings

import pytest

from qec_twin.hardware import m1_report, pij, stim_artifacts
from qec_twin.hardware.dataset import (
    BASES,
    DETECTOR_BYTES_PER_SHOT,
    MEASUREMENT_BYTES_PER_SHOT,
    NUM_CHAINS,
    NUM_DETECTOR_LAYERS,
    NUM_DETECTORS,
    NUM_MEASUREMENTS,
    NUM_OBSERVABLES,
    NUM_SHOTS,
    NUM_SWEEP_BITS,
    OBSERVABLE_BYTES_PER_SHOT,
    SWEEP_BYTES_PER_SHOT,
    RepCodeD29,
    resolve_rep29_root,
)

pytestmark = pytest.mark.skipif(
    resolve_rep29_root() is None,
    reason="R2-lite d29 dataset absent (set QEC_TWIN_HW_DATA)",
)

PARITY_SAMPLES = (0, 50, 99)


@functools.lru_cache(maxsize=None)
def _ds() -> RepCodeD29:
    return RepCodeD29.from_env()


@functools.lru_cache(maxsize=None)
def _grid(basis: str):
    return m1_report.build_grid(_ds(), basis)


@functools.lru_cache(maxsize=None)
def _detection_block(basis: str):
    return m1_report.run_detection_block(_ds(), basis, _grid(basis))


@functools.lru_cache(maxsize=None)
def _pij_block(basis: str):
    ds = _ds()
    paths = ds.paths(basis, 0)
    analysis = pij.analyze_pij(paths.detection_events, _grid(basis))
    dem = stim_artifacts.dem_pair_support(
        stim_artifacts.load_circuit(paths.circuit_noisy_si1000), _grid(basis)
    )
    return analysis, dem


# ---------------------------------------------------------------- gates


def test_p1_structure_counts():
    # P1: exact structure integers -- b8 file sizes on every sample dir, stim
    # circuit counts + (layer, chain) grid completeness on the parity samples.
    assert (NUM_DETECTORS, NUM_MEASUREMENTS) == (28_056, 28_057)
    assert (NUM_CHAINS, NUM_DETECTOR_LAYERS) == (28, 1002)
    assert (NUM_OBSERVABLES, NUM_SWEEP_BITS) == (1, 29)
    assert (
        DETECTOR_BYTES_PER_SHOT,
        MEASUREMENT_BYTES_PER_SHOT,
        SWEEP_BYTES_PER_SHOT,
        OBSERVABLE_BYTES_PER_SHOT,
    ) == (3507, 3508, 4, 1)

    ds = _ds()
    assert set(ds.bases) == set(BASES)
    result = m1_report.run_p1(ds, circuit_samples=PARITY_SAMPLES)
    assert result["passed"], f"P1 FAIL: {result['failures'][:5]}"
    assert result["b8_samples_checked"] == sum(len(ds.samples(b)) for b in ds.bases)
    for basis in ds.bases:
        grid = _grid(basis)
        assert (grid.num_layers, grid.num_chains) == (NUM_DETECTOR_LAYERS, NUM_CHAINS)


def test_p2_m2d_bitexact_parity():
    # P2: deterministic, zero tolerance -- 0 mismatched bytes on {00,50,99} x {X,Z}.
    ds = _ds()
    for basis in ds.bases:
        for sample in PARITY_SAMPLES:
            result = m1_report.run_p2_sample(ds, basis, sample, verbose=False)
            det, obs = result["detection_events"], result["obs_flips"]
            assert det.bit_exact and obs.bit_exact, (
                f"P2 FAIL {basis}/sample_{sample:02d} (via {result['converter_circuit']}): "
                f"det {det.mismatched_bytes}/{det.total_bytes} mismatched bytes "
                f"(first at {det.first_mismatch_byte}), obs {obs.mismatched_bytes}"
            )
            assert det.total_bytes == NUM_SHOTS * DETECTOR_BYTES_PER_SHOT


@pytest.mark.slow
@pytest.mark.skipif(
    not os.environ.get("QEC_TWIN_HW_SLOW"),
    reason="whole-corpus parity is slow (set QEC_TWIN_HW_SLOW=1)",
)
def test_p2_m2d_bitexact_parity_full_corpus():
    ds = _ds()
    for basis in ds.bases:
        for sample in ds.samples(basis):
            result = m1_report.run_p2_sample(ds, basis, sample, verbose=False)
            assert result["passed"], f"P2 FAIL {basis}/sample_{sample:02d}"


def test_p3_detection_fraction_band():
    # P3: bulk (layers 1-1000) fraction per basis in [3%, 7%], < 7.7%, SE < 1e-3.
    blocks = {basis: _detection_block(basis) for basis in _ds().bases}
    result = m1_report.score_p3(blocks)
    for basis, row in result["rows"].items():
        print(f"P3 {basis}: bulk {row['bulk_fraction']:.5f} SE {row['se']:.2e} CI95 {row['ci95']}")
    assert result["passed"], f"P3 FAIL: {result['rows']}"


def test_p4_pij_support_parity():
    # P4 as ADJUDICATED (2026-06-09; metric_results.md M1 RESULTS + the M1-C1 control):
    # the original support-graph identity FAILED on the device because the mirror
    # spacetime-diagonal class (1,1,-1) is physically present (X 9.79e-4 / Z 8.60e-4,
    # ~500 sigma) while absent from the shipped SI1000 model; the C1 artifact control
    # (same pipeline on SI1000 sim shots: mirror ~1e-6 = noise floor) certified the
    # signal as device physics, not a grid/orientation artifact. The adjudicated gate
    # pins that state: every DEM class present; the gating extras are EXACTLY the
    # known mirror class (any other extra is a NEW violation); null-entry bounds and
    # the permitted positive-tail clause unchanged.
    KNOWN_DEVICE_EXTRAS = {(1, 1, -1)}  # back-edge finding, no mechanism attribution
    for basis in _ds().bases:
        analysis, dem = _pij_block(basis)
        score = m1_report.score_p4_basis(basis, analysis, dem)
        print(
            f"P4 {basis}: significant={sorted(map(str, score.significant))} "
            f"dem={sorted(map(str, score.dem_pair_classes))} "
            f"null entries total={score.entry_total_exceed_frac:.4%} "
            f"negative={score.entry_negative_exceed_frac:.4%} "
            f"positive_share={score.entry_positive_share:.2%} "
            f"tails={score.reported_positive_tails}"
        )
        assert not score.missing_expected, f"P4 {basis}: DEM class missing {score.missing_expected}"
        extras = {tuple(k) for (k, _, _) in score.gating_extras}
        assert extras == KNOWN_DEVICE_EXTRAS, (
            f"P4 {basis}: extras {extras} != adjudicated {KNOWN_DEVICE_EXTRAS} "
            f"(a NEW class appeared or the known finding vanished — re-adjudicate)"
        )
        assert not score.null_negative_violations, (
            f"P4 {basis}: negative null violations {score.null_negative_violations}"
        )
        assert score.entry_positive_share >= 0.90, (
            f"P4 {basis}: positive share {score.entry_positive_share:.2%} < 90% "
            f"(permitted-tail clause violated)"
        )


# ---------------------------------------------------------------- side-bets (reported, soft-bound)


def _soft(condition: bool, message: str) -> None:
    print(message)
    if not condition:
        warnings.warn(f"side-bet out of band (finding, not failure): {message}", stacklevel=2)


def test_p5_basis_ordering_reported():
    x = _detection_block("X")
    z = _detection_block("Z")
    _soft(
        x.stats.bulk_fraction > z.stats.bulk_fraction,
        f"P5 order: X {x.stats.bulk_fraction:.5f} > Z {z.stats.bulk_fraction:.5f} "
        f"(SEs {x.bulk_se:.2e}/{z.bulk_se:.2e})",
    )
    _soft(
        m1_report._in_band(x.stats.bulk_fraction, m1_report.P5_BAND["X"]),
        f"P5 X band: {x.stats.bulk_fraction:.5f} in {m1_report.P5_BAND['X']}",
    )
    _soft(
        m1_report._in_band(z.stats.bulk_fraction, m1_report.P5_BAND["Z"]),
        f"P5 Z band: {z.stats.bulk_fraction:.5f} in {m1_report.P5_BAND['Z']}",
    )


def test_p6_layer_profile_reported():
    for basis in _ds().bases:
        block = _detection_block(basis)
        flat = block.flatness
        _soft(
            m1_report._in_band(block.layer0_over_bulk, m1_report.P6_LAYER0_BAND),
            f"P6 {basis} layer0/bulk: {block.layer0_over_bulk:.3f}"
            f"±{block.layer0_over_bulk_se:.3f} in {m1_report.P6_LAYER0_BAND}",
        )
        _soft(
            m1_report._in_band(block.final_over_bulk, m1_report.P6_FINAL_BAND),
            f"P6 {basis} final/bulk: {block.final_over_bulk:.3f}"
            f"±{block.final_over_bulk_se:.3f} in {m1_report.P6_FINAL_BAND}",
        )
        _soft(
            flat.rel_std < m1_report.P6_FLATNESS_MAX,
            f"P6 {basis} flatness: rel std {flat.rel_std:.4f} < {m1_report.P6_FLATNESS_MAX} "
            f"(outlier layers {list(flat.outlier_layers)} reported, excluded)",
        )


def test_p7_pij_class_means_reported():
    space_means = {}
    for basis in _ds().bases:
        analysis, _ = _pij_block(basis)
        p7 = m1_report.score_p7_basis(analysis)
        space_means[basis] = p7["space_mean"]
        _soft(
            p7["time_in_band"] and p7["time_is_largest"],
            f"P7 {basis} time-like: {p7['time_mean']:.5f}±{p7['time_se']:.1e} in "
            f"{m1_report.P7_TIME_BAND}, largest={p7['time_is_largest']}",
        )
        _soft(
            p7["space_in_band"],
            f"P7 {basis} space-like: {p7['space_mean']:.5f}±{p7['space_se']:.1e} in "
            f"{m1_report.P7_SPACE_BAND}",
        )
        _soft(
            p7["diag_in_band"] and p7["ratio_ok"],
            f"P7 {basis} diagonal {p7['diag_populated']}: {p7['diag_mean']:.5f}"
            f"±{p7['diag_se']:.1e} in {m1_report.P7_DIAG_BAND}, "
            f"mirror ratio {p7['mirror_ratio']:.2f} >= 3",
        )
    _soft(
        space_means["X"] >= space_means["Z"],
        f"P7 space-like X >= Z: {space_means['X']:.5f} vs {space_means['Z']:.5f}",
    )


def test_p8_si1000_mc_detection_fraction_reported():
    ds = _ds()
    result = m1_report.run_p8(ds, {basis: _grid(basis) for basis in ds.bases})
    for basis, value in result["fractions"].items():
        _soft(
            m1_report._in_band(value, result["band"]),
            f"P8 {basis}: MC bulk fraction {value:.5f} in {result['band']} "
            f"({result['shots']} shots, seed {result['seed']})",
        )
    _soft(
        result["basis_match"],
        f"P8 X~Z: relative gap {result['basis_rel_gap']:.3%} <= 10%",
    )


def test_p9_obs_flip_mean_reported():
    for basis in _ds().bases:
        block = _detection_block(basis)
        _soft(
            m1_report._in_band(block.obs_mean, m1_report.P9_BAND),
            f"P9 {basis}: obs flip mean {block.obs_mean:.5f} (SE {block.obs_se:.2e}) "
            f"in {m1_report.P9_BAND}",
        )
