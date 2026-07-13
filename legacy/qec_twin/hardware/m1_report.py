"""M1 ingestion-parity scoring driver (R2-lite, ADR 0007 Decision 4 M1).

Scores gates P1-P4 and side-bets P5-P9 strictly against the dated
pre-registration (docs/metric_results.md, 2026-06-09). Run:

    QEC_TWIN_HW_DATA=<parent dir> python -m qec_twin.hardware.m1_report

Committed adjudication notes (recorded with the build, BEFORE the run):
- P2 circuit choice: the registration fixes the artifact equality, not which
  shipped circuit compiles the converter; ideal is tried first, the noisy
  circuit second — bit-exactness is required either way and the choice is
  reported, never tuned.
- P4 permitted-tail clause: positive long-range exceedances (null classes /
  null entries) are reported, never gated; gating violations are (a) a missing
  DEM-support class, (b) a significant non-null non-DEM class (e.g. the mirror
  diagonal), (c) a NEGATIVE null-class mean beyond max(1e-4, 5*SE), (d) null
  entries: negative-side exceedance >= 1%, or total exceedance >= 1% with
  positive share < 90%.
- P6 burst rule: outliers = beyond median +- 5*(1.4826*MAD) over the window,
  reported and excluded from the flatness statistic.
- P8 shots: 20_000 MC shots, seed 20260609 (registration fixes the band, not
  the MC shot count).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field

import numpy as np

from qec_twin.hardware import b8_io, dataset, detection_stats, pij, stim_artifacts
from qec_twin.hardware.dataset import RepCodeD29

P3_BAND = (0.03, 0.07)
P3_SURFACE_ANCHOR = 0.077
P3_SE_MAX = 1e-3
P5_BAND = {"X": (0.04, 0.07), "Z": (0.03, 0.06)}
P6_LAYER0_BAND = (0.3, 0.9)
P6_FINAL_BAND = (0.5, 1.5)
P6_FLATNESS_MAX = 0.10
P7_TIME_BAND = (0.010, 0.025)
P7_SPACE_BAND = (0.003, 0.020)
P7_DIAG_BAND = (0.0003, 0.006)
P7_MIRROR_RATIO_MIN = 3.0
P8_BAND = (0.0255 - 0.0065, 0.0255 + 0.0065)
P8_BASIS_REL_TOL = 0.10
P8_SHOTS = 20_000
P8_SEED = 20260609
P9_BAND = (0.492, 0.508)
P4_SUPPORT_SIGMA = 10.0
P4_NULL_SIGMA = 5.0
P4_NULL_FLOOR = 1e-4
P4_ENTRY_EXCEED_MAX = 0.01
P4_POSITIVE_SHARE_MIN = 0.90

TIME_KEY = (0, 1, 0)
SPACE_KEY = (1, 0, 0)
DIAG_KEYS = ((1, 1, 1), (1, 1, -1))


def _in_band(value: float, band: tuple[float, float]) -> bool:
    return band[0] <= value <= band[1]


def _progress(label: str):
    def callback(done: int, total: int) -> None:
        print(f"    {label}: {done}/{total} shots", flush=True)

    return callback


def build_grid(ds: RepCodeD29, basis: str, sample: int = 0) -> stim_artifacts.DetectorGrid:
    paths = ds.paths(basis, sample)
    ideal = stim_artifacts.load_circuit(paths.circuit_ideal)
    noisy = stim_artifacts.load_circuit(paths.circuit_noisy_si1000)
    qubit_order = dataset.metadata_qubit_order(ds.load_metadata(basis, sample))
    try:
        return stim_artifacts.detector_grid(ideal, dem_circuit=noisy, qubit_order=qubit_order)
    except ValueError:
        return stim_artifacts.detector_grid(noisy, dem_circuit=noisy, qubit_order=qubit_order)


# ---------------------------------------------------------------- P1


def run_p1(ds: RepCodeD29, *, circuit_samples=(0, 50, 99)) -> dict:
    failures: list[str] = []
    checked = 0
    for basis in ds.bases:
        for sample in ds.samples(basis):
            try:
                ds.validate_structure(basis, sample)
                checked += 1
            except (ValueError, OSError) as err:
                failures.append(str(err))
    counts_ok = True
    for basis in ds.bases:
        for sample in circuit_samples:
            counts = stim_artifacts.circuit_counts(
                stim_artifacts.load_circuit(ds.paths(basis, sample).circuit_ideal)
            )
            expected = (
                dataset.NUM_DETECTORS,
                dataset.NUM_MEASUREMENTS,
                dataset.NUM_OBSERVABLES,
                dataset.NUM_SWEEP_BITS,
            )
            actual = (
                counts.num_detectors,
                counts.num_measurements,
                counts.num_observables,
                counts.num_sweep_bits,
            )
            if actual != expected:
                counts_ok = False
                failures.append(f"{basis}/sample_{sample:02d} circuit counts {actual} != {expected}")
            ds.load_metadata(basis, sample)
    passed = not failures and counts_ok and checked > 0
    return {"gate": "P1", "passed": passed, "b8_samples_checked": checked, "failures": failures}


# ---------------------------------------------------------------- P2


def run_p2_sample(
    ds: RepCodeD29, basis: str, sample: int, *, chunk_shots: int = 10_000, verbose: bool = True
) -> dict:
    paths = ds.paths(basis, sample)
    sweep_all = b8_io.read_b8(paths.sweep_bits, dataset.NUM_SWEEP_BITS)
    converters = {}
    chosen: str | None = None
    det_reports: list[stim_artifacts.ParityReport] = []
    obs_reports: list[stim_artifacts.ParityReport] = []
    for start, meas_packed in b8_io.iter_b8_chunks(
        paths.measurements, dataset.NUM_MEASUREMENTS, chunk_shots=chunk_shots
    ):
        stop = start + meas_packed.shape[0]
        shipped_det = b8_io.read_b8(paths.detection_events, dataset.NUM_DETECTORS, (start, stop))
        shipped_obs = b8_io.read_b8(paths.obs_flips_actual, dataset.NUM_OBSERVABLES, (start, stop))
        sweep_packed = sweep_all[start:stop]
        if chosen is None:
            candidates = {}
            for name, circuit_path in (
                ("circuit_ideal", paths.circuit_ideal),
                ("circuit_noisy_si1000", paths.circuit_noisy_si1000),
            ):
                converters[name] = stim_artifacts.M2DConverter(
                    stim_artifacts.load_circuit(circuit_path)
                )
                candidates[name] = converters[name].convert_packed(meas_packed, sweep_packed)
                det, obs = candidates[name]
                if (
                    stim_artifacts.bitexact_parity(det, shipped_det).bit_exact
                    and stim_artifacts.bitexact_parity(obs, shipped_obs).bit_exact
                ):
                    chosen = name
                    break
            if chosen is None:
                chosen = "circuit_ideal"  # report its mismatches
            det, obs = candidates[chosen]
        else:
            det, obs = converters[chosen].convert_packed(meas_packed, sweep_packed)
        det_reports.append(stim_artifacts.bitexact_parity(det, shipped_det))
        obs_reports.append(stim_artifacts.bitexact_parity(obs, shipped_obs))
        if verbose:
            print(f"    P2 {basis}/sample_{sample:02d}: {stop} shots done", flush=True)
    det_total = stim_artifacts.merge_parity_reports(det_reports)
    obs_total = stim_artifacts.merge_parity_reports(obs_reports)
    return {
        "basis": basis,
        "sample": sample,
        "converter_circuit": chosen,
        "detection_events": det_total,
        "obs_flips": obs_total,
        "passed": det_total.bit_exact and obs_total.bit_exact,
    }


def run_p2(ds: RepCodeD29, *, samples=(0, 50, 99), chunk_shots: int = 10_000) -> dict:
    results = [
        run_p2_sample(ds, basis, sample, chunk_shots=chunk_shots)
        for basis in ds.bases
        for sample in samples
    ]
    return {"gate": "P2", "passed": all(r["passed"] for r in results), "results": results}


# ---------------------------------------------------------------- P3 / P5 / P6 / P9 (detection block)


@dataclass
class DetectionBlock:
    basis: str
    stats: detection_stats.DetectionStats
    bulk_se: float
    bulk_ci: tuple[float, float]
    layer0_over_bulk: float
    layer0_over_bulk_se: float
    final_over_bulk: float
    final_over_bulk_se: float
    flatness: detection_stats.FlatnessReport
    obs_mean: float
    obs_se: float


def run_detection_block(ds: RepCodeD29, basis: str, grid, *, sample: int = 0) -> DetectionBlock:
    paths = ds.paths(basis, sample)
    stats = detection_stats.detection_stats_from_file(paths.detection_events, grid)
    chains, layers = stats.num_chains, stats.num_layers
    per_shot = np.stack([stats.per_shot_layer0, stats.per_shot_bulk, stats.per_shot_final], axis=1)
    reps = detection_stats.bootstrap_mean_replicates(per_shot)
    frac_reps = reps / np.array([chains, chains * (layers - 2), chains], dtype=np.float64)
    bulk_se = float(detection_stats.bootstrap_se(frac_reps[:, 1]))
    lo, hi = detection_stats.percentile_ci(frac_reps[:, 1])
    ratio0 = frac_reps[:, 0] / frac_reps[:, 1]
    ratiof = frac_reps[:, 2] / frac_reps[:, 1]

    obs_bits = b8_io.read_b8(paths.obs_flips_actual, dataset.NUM_OBSERVABLES) & 1
    obs_per_shot = obs_bits[:, 0].astype(np.float64)
    obs_reps = detection_stats.bootstrap_mean_replicates(obs_per_shot)
    return DetectionBlock(
        basis=basis,
        stats=stats,
        bulk_se=bulk_se,
        bulk_ci=(float(lo), float(hi)),
        layer0_over_bulk=stats.layer0_fraction / stats.bulk_fraction,
        layer0_over_bulk_se=float(detection_stats.bootstrap_se(ratio0)),
        final_over_bulk=stats.final_fraction / stats.bulk_fraction,
        final_over_bulk_se=float(detection_stats.bootstrap_se(ratiof)),
        flatness=detection_stats.bulk_flatness(stats.per_layer_fraction),
        obs_mean=float(obs_per_shot.mean()),
        obs_se=float(detection_stats.bootstrap_se(obs_reps).ravel()[0]),
    )


def score_p3(blocks: dict) -> dict:
    rows = {}
    passed = True
    for basis, block in blocks.items():
        ok = (
            _in_band(block.stats.bulk_fraction, P3_BAND)
            and block.stats.bulk_fraction < P3_SURFACE_ANCHOR
            and block.bulk_se < P3_SE_MAX
        )
        rows[basis] = {
            "bulk_fraction": block.stats.bulk_fraction,
            "se": block.bulk_se,
            "ci95": block.bulk_ci,
            "band": P3_BAND,
            "anchor": P3_SURFACE_ANCHOR,
            "passed": ok,
        }
        passed &= ok
    return {"gate": "P3", "passed": passed, "rows": rows}


# ---------------------------------------------------------------- P4 / P7 (pij block)


@dataclass
class P4Score:
    basis: str
    dem_pair_classes: frozenset
    dem_singles: int
    dem_higher: int
    significant: set
    missing_expected: list
    gating_extras: list
    reported_positive_tails: list
    null_negative_violations: list
    entry_total_exceed_frac: float
    entry_negative_exceed_frac: float
    entry_positive_share: float
    num_null_entries: int
    passed: bool
    notes: list = field(default_factory=list)


def score_p4_basis(basis: str, analysis: pij.PijAnalysis, dem: stim_artifacts.DemPairSupport) -> P4Score:
    null_keys = set(pij.null_class_keys())
    significant = {
        key
        for key, cls in analysis.class_se.items()
        if cls.mean_pij > P4_SUPPORT_SIGMA * cls.se_boot
    }
    expected = set(dem.pair_classes)
    missing = sorted(k for k in expected if k not in significant)

    gating_extras: list = []
    tails: list = []
    for key in significant - expected:
        cls = analysis.class_se[key]
        if key in null_keys and cls.mean_pij > 0:
            tails.append((key, cls.mean_pij, cls.se_boot))
        else:
            gating_extras.append((key, cls.mean_pij, cls.se_boot))

    null_negative: list = []
    for key in null_keys:
        cls = analysis.class_se[key]
        bound = max(P4_NULL_FLOOR, P4_NULL_SIGMA * cls.se_boot)
        if cls.mean_pij < -bound:
            null_negative.append((key, cls.mean_pij, cls.se_boot))

    values = np.concatenate([analysis.entries[k].pij for k in null_keys])
    ses = np.concatenate([analysis.entries[k].se_delta for k in null_keys])
    exceed = np.abs(values) > P4_NULL_SIGMA * ses
    negative_exceed = values < -P4_NULL_SIGMA * ses
    total_frac = float(exceed.mean())
    negative_frac = float(negative_exceed.mean())
    positive_share = float((values[exceed] > 0).mean()) if exceed.any() else 1.0

    entry_ok = negative_frac < P4_ENTRY_EXCEED_MAX and (
        total_frac < P4_ENTRY_EXCEED_MAX or positive_share >= P4_POSITIVE_SHARE_MIN
    )
    passed = not missing and not gating_extras and not null_negative and entry_ok
    notes = []
    if expected != {TIME_KEY, SPACE_KEY} | {k for k in DIAG_KEYS if k in expected}:
        notes.append(f"DEM pair support {sorted(expected)} differs from the four named sets")
    if sum(k in expected for k in DIAG_KEYS) != 1:
        notes.append(f"DEM diagonal orientations in support: {[k for k in DIAG_KEYS if k in expected]}")
    if tails:
        notes.append("positive long-range tails reported as misspecification direction (M2/H2 back-edge)")
    return P4Score(
        basis=basis,
        dem_pair_classes=dem.pair_classes,
        dem_singles=dem.single_detector_errors,
        dem_higher=dem.higher_weight_errors,
        significant=significant,
        missing_expected=missing,
        gating_extras=gating_extras,
        reported_positive_tails=tails,
        null_negative_violations=null_negative,
        entry_total_exceed_frac=total_frac,
        entry_negative_exceed_frac=negative_frac,
        entry_positive_share=positive_share,
        num_null_entries=int(values.size),
        passed=passed,
        notes=notes,
    )


def score_p7_basis(analysis: pij.PijAnalysis) -> dict:
    cls = analysis.class_se
    diag_means = {k: cls[k].mean_pij for k in DIAG_KEYS}
    populated = max(DIAG_KEYS, key=lambda k: diag_means[k])
    mirror = DIAG_KEYS[0] if populated == DIAG_KEYS[1] else DIAG_KEYS[1]
    ratio = (
        float("inf")
        if diag_means[mirror] <= 0
        else diag_means[populated] / diag_means[mirror]
    )
    time_mean = cls[TIME_KEY].mean_pij
    largest = max(cls.values(), key=lambda c: c.mean_pij).key
    return {
        "time_mean": time_mean,
        "time_se": cls[TIME_KEY].se_boot,
        "time_in_band": _in_band(time_mean, P7_TIME_BAND),
        "time_is_largest": largest == TIME_KEY,
        "space_mean": cls[SPACE_KEY].mean_pij,
        "space_se": cls[SPACE_KEY].se_boot,
        "space_in_band": _in_band(cls[SPACE_KEY].mean_pij, P7_SPACE_BAND),
        "diag_populated": populated,
        "diag_mean": diag_means[populated],
        "diag_se": cls[populated].se_boot,
        "diag_in_band": _in_band(diag_means[populated], P7_DIAG_BAND),
        "mirror_mean": diag_means[mirror],
        "mirror_ratio": ratio,
        "ratio_ok": ratio >= P7_MIRROR_RATIO_MIN,
    }


# ---------------------------------------------------------------- P8


def run_p8(ds: RepCodeD29, grids: dict, *, shots: int = P8_SHOTS, seed: int = P8_SEED) -> dict:
    fractions = {}
    for basis in ds.bases:
        circuit = stim_artifacts.load_circuit(ds.paths(basis, 0).circuit_noisy_si1000)
        stats = detection_stats.detection_stats_from_sampler(
            circuit, grids[basis], shots=shots, seed=seed
        )
        fractions[basis] = stats.bulk_fraction
    rel_gap = abs(fractions["X"] - fractions["Z"]) / np.mean(list(fractions.values()))
    return {
        "fractions": fractions,
        "band": P8_BAND,
        "in_band": all(_in_band(v, P8_BAND) for v in fractions.values()),
        "basis_rel_gap": float(rel_gap),
        "basis_match": rel_gap <= P8_BASIS_REL_TOL,
        "shots": shots,
        "seed": seed,
    }


# ---------------------------------------------------------------- driver


def _fmt_key(key) -> str:
    return key if isinstance(key, str) else f"(di={key[0]},dt={key[1]},o={key[2]:+d})"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skip-p1", action="store_true")
    parser.add_argument("--skip-p2", action="store_true")
    parser.add_argument("--skip-detection", action="store_true", help="skip P3/P5/P6/P9")
    parser.add_argument("--skip-pij", action="store_true", help="skip P4/P7")
    parser.add_argument("--skip-p8", action="store_true")
    parser.add_argument("--parity-samples", type=int, nargs="+", default=[0, 50, 99])
    parser.add_argument("--chunk-shots", type=int, default=10_000)
    parser.add_argument("--replicates", type=int, default=1000)
    args = parser.parse_args(argv)

    ds = RepCodeD29.from_env()
    print(f"dataset: {ds.root}", flush=True)
    grids = {basis: build_grid(ds, basis) for basis in ds.bases}
    for basis, grid in grids.items():
        print(f"grid[{basis}]: {grid.num_layers} layers x {grid.num_chains} chains "
              f"(chain order: {grid.chain_order_source})", flush=True)

    if not args.skip_p1:
        p1 = run_p1(ds)
        print(f"\n== P1 structure: {'PASS' if p1['passed'] else 'FAIL'} "
              f"({p1['b8_samples_checked']} sample dirs size-exact)", flush=True)
        for failure in p1["failures"][:10]:
            print(f"   FAIL: {failure}", flush=True)

    if not args.skip_p2:
        p2 = run_p2(ds, samples=tuple(args.parity_samples), chunk_shots=args.chunk_shots)
        print(f"\n== P2 m2d bit-exact parity: {'PASS' if p2['passed'] else 'FAIL'}", flush=True)
        for r in p2["results"]:
            det, obs = r["detection_events"], r["obs_flips"]
            print(f"   {r['basis']}/sample_{r['sample']:02d} via {r['converter_circuit']}: "
                  f"det {det.mismatched_bytes}/{det.total_bytes} mismatched bytes, "
                  f"obs {obs.mismatched_bytes}/{obs.total_bytes}", flush=True)

    blocks: dict = {}
    if not args.skip_detection:
        for basis in ds.bases:
            print(f"\n-- detection block {basis}/sample_00", flush=True)
            blocks[basis] = run_detection_block(ds, basis, grids[basis])
        p3 = score_p3(blocks)
        print(f"\n== P3 bulk detection fraction: {'PASS' if p3['passed'] else 'FAIL'}", flush=True)
        for basis, row in p3["rows"].items():
            print(f"   {basis}: {row['bulk_fraction']:.5f} (SE {row['se']:.2e}, "
                  f"CI95 [{row['ci95'][0]:.5f}, {row['ci95'][1]:.5f}]) band {row['band']} "
                  f"< {row['anchor']}: {'ok' if row['passed'] else 'MISS'}", flush=True)
        x, z = blocks["X"], blocks["Z"]
        p5_order = x.stats.bulk_fraction > z.stats.bulk_fraction
        print(f"\n== P5 (side-bet) p_det(X) > p_det(Z): {p5_order} "
              f"(X {x.stats.bulk_fraction:.5f} in {P5_BAND['X']}: "
              f"{_in_band(x.stats.bulk_fraction, P5_BAND['X'])}; "
              f"Z {z.stats.bulk_fraction:.5f} in {P5_BAND['Z']}: "
              f"{_in_band(z.stats.bulk_fraction, P5_BAND['Z'])})", flush=True)
        print("\n== P6 (side-bet) layer profile", flush=True)
        for basis, block in blocks.items():
            flat = block.flatness
            print(f"   {basis}: layer0/bulk {block.layer0_over_bulk:.3f}±{block.layer0_over_bulk_se:.3f} "
                  f"in {P6_LAYER0_BAND}: {_in_band(block.layer0_over_bulk, P6_LAYER0_BAND)}; "
                  f"final/bulk {block.final_over_bulk:.3f}±{block.final_over_bulk_se:.3f} "
                  f"in {P6_FINAL_BAND}: {_in_band(block.final_over_bulk, P6_FINAL_BAND)}; "
                  f"rel std {flat.rel_std:.4f} < {P6_FLATNESS_MAX}: {flat.rel_std < P6_FLATNESS_MAX}; "
                  f"outlier layers {list(flat.outlier_layers)}", flush=True)
        print("\n== P9 (side-bet) obs flip mean", flush=True)
        for basis, block in blocks.items():
            print(f"   {basis}: {block.obs_mean:.5f} (SE {block.obs_se:.2e}) in {P9_BAND}: "
                  f"{_in_band(block.obs_mean, P9_BAND)}", flush=True)

    if not args.skip_pij:
        p4_scores = {}
        for basis in ds.bases:
            print(f"\n-- pij block {basis}/sample_00", flush=True)
            paths = ds.paths(basis, 0)
            analysis = pij.analyze_pij(
                paths.detection_events,
                grids[basis],
                chunk_shots=args.chunk_shots,
                replicates=args.replicates,
                progress=_progress(f"pij {basis}"),
            )
            dem = stim_artifacts.dem_pair_support(
                stim_artifacts.load_circuit(paths.circuit_noisy_si1000), grids[basis]
            )
            p4_scores[basis] = (score_p4_basis(basis, analysis, dem), analysis)
        print(f"\n== P4 pij support parity: "
              f"{'PASS' if all(s.passed for s, _ in p4_scores.values()) else 'FAIL'}", flush=True)
        for basis, (score, analysis) in p4_scores.items():
            print(f"   {basis}: DEM support {sorted(_fmt_key(k) for k in score.dem_pair_classes)} "
                  f"(+{score.dem_singles} boundary singles, {score.dem_higher} hyperedges)", flush=True)
            print(f"      significant {sorted(_fmt_key(k) for k in score.significant)}", flush=True)
            print(f"      missing {score.missing_expected}; gating extras {score.gating_extras}; "
                  f"negative null violations {score.null_negative_violations}", flush=True)
            print(f"      null entries: total |pij|>5SE {score.entry_total_exceed_frac:.4%} "
                  f"(negative {score.entry_negative_exceed_frac:.4%}, "
                  f"positive share {score.entry_positive_share:.2%}) of {score.num_null_entries}",
                  flush=True)
            for note in score.notes:
                print(f"      note: {note}", flush=True)
            for key, mean, se in score.reported_positive_tails:
                print(f"      reported tail: {_fmt_key(key)} mean {mean:.3e} (SE {se:.1e})", flush=True)
            p7 = score_p7_basis(analysis)
            print(f"   P7 (side-bet) {basis}: time {p7['time_mean']:.5f}±{p7['time_se']:.1e} "
                  f"in {P7_TIME_BAND}: {p7['time_in_band']} largest: {p7['time_is_largest']}; "
                  f"space {p7['space_mean']:.5f}±{p7['space_se']:.1e} in {P7_SPACE_BAND}: "
                  f"{p7['space_in_band']}; diag {_fmt_key(p7['diag_populated'])} "
                  f"{p7['diag_mean']:.5f}±{p7['diag_se']:.1e} in {P7_DIAG_BAND}: {p7['diag_in_band']}; "
                  f"mirror ratio {p7['mirror_ratio']:.2f} >= 3: {p7['ratio_ok']}", flush=True)
            print(f"      class table ({basis}):", flush=True)
            for key, cls in sorted(analysis.class_se.items(), key=lambda kv: str(kv[0])):
                entry = analysis.entries[key]
                print(f"        {_fmt_key(key):24s} n={cls.num_pairs:7d} mean={cls.mean_pij:+.3e} "
                      f"seB={cls.se_boot:.2e} seL={cls.se_linear:.2e} "
                      f"bulk={entry.mean_pij_bulk:+.3e} bnd={entry.mean_pij_boundary:+.3e}",
                      flush=True)

    if not args.skip_p8:
        p8 = run_p8(ds, grids)
        print(f"\n== P8 (side-bet) SI1000 MC bulk detection fraction "
              f"({p8['shots']} shots, seed {p8['seed']})", flush=True)
        for basis, value in p8["fractions"].items():
            print(f"   {basis}: {value:.5f} in {p8['band']}: {_in_band(value, p8['band'])}", flush=True)
        print(f"   X-Z relative gap {p8['basis_rel_gap']:.3%} <= 10%: {p8['basis_match']}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
