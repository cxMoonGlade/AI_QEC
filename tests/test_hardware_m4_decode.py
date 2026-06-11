"""R2-lite M4 -- decoder-side build tests (B2 scope: m4_decode machinery).

PRE-REGISTRATION (docs/metric_results.md "M4 PRE-REGISTRATION (decoder-prior
utility; recorded 2026-06-10 BEFORE build/run)"; reviewer blueprint in
docs/.reports/m4_panel/). This file covers the BUILD-phase decoder machinery
ONLY -- no pilot, no fleet, no held-out decode happens here. Sample scope of
every hardware-gated test: sample_00 ONLY (train side; samples 01-99 are
off-limits everywhere in the build phase).

Toy-scale coverage (no hardware data needed):
  * S1 decoder pin: pymatching version == 2.4.0 (binding; the provenance
    record itself carries the wheel sha256 build constant).
  * decode_dem explicit bit-packed vs bool handling (+ ambiguity errors).
  * P1d determinism: independent Matching builds decode bit-identically.
  * P1g: pymatching at upstream defaults vs the in-repo brute-force EXACT
    minimum-weight reference, ALL 2^D syndromes of enumerable toy DEMs,
    zero ties by design (class a: exact agreement).
  * G4 jitter guard at toy scale: +-1e-9 weight jitter flips nothing when
    margins are macroscopic.
  * G4 sim round-trip: decoded LER on DEM-self-sampled shots matches the
    exact enumeration prediction within MC error.
  * G4 sim-round-trip PASS RULE (FIX ROUND, reviewer item 5):
    sim_round_trip_check at BOTH scales -- toy-enumerable (exact (a) branch)
    and production (finite/sane/reproducible + second-seed binomial (c)
    branch), plus the sane-bounds tripwire firing on a degenerate DEM.
  * S2 per-unit actual observables (FIX ROUND, reviewer item 2):
    unit_observable_spec chain-ordering on a scrambled-record toy circuit;
    unit_actual_observables on synthetic b8 fixtures vs hand-computed XOR
    references (multiple units incl. the full chain); pin_p1b_units
    synthetic round-trip; the held-out refusal (samples 1-99 raise without
    allow_heldout) and units validation.
  * A3c two-pass: exact no-op at R-hat == 1 (negative control) and a
    decision-flipping effect at R-hat >> 1 on a synthetic burst DEM.
  * decode_fleet: process-parallel results bit-identical to serial decodes,
    deterministic job ordering, chunked streaming from arrays and .b8 files.

Hardware-gated coverage (skips without QEC_TWIN_HW_DATA), sample_00 ONLY:
  * P1a smoke: m2d parity via the literal M1 construction.
  * P1b: our observable construction (leftmost data qubit final readout XOR
    sweep reference) at window == full chain reproduces obs_flips_actual
    bit-exactly (class a).
  * P1b-units (FIX ROUND): unit_actual_observables full-chain unit ==
    obs_flips_actual bit-exact (class a) + spec identity with the P1b
    full-chain spec; a sub-unit (window 16: data 17..21) returns plausible
    nonconstant bits.
  * P1e smoke: shipped RL DEM decoded by the frozen decoder vs shipped
    obs_flips_predicted -- mismatch fraction printed (certification rule and
    routing live in the registration; the build asserts only the outer 1e-3
    bound). Shot budget via QEC_TWIN_M4_P1E_SHOTS (default 20000; 0 = full).
  * P1f smoke: DEM hash audit on sample_00 (report-only).
"""

from __future__ import annotations

import os

import numpy as np
import pytest

pymatching = pytest.importorskip(
    "pymatching", reason="pymatching==2.4.0 is the registered M4 decoder pin (extra [hw])"
)

from qec_twin.hardware import b8_io, m4_decode
from qec_twin.hardware.dataset import RepCodeD29, resolve_rep29_root

requires_hw = pytest.mark.skipif(
    resolve_rep29_root() is None,
    reason="R2-lite d29 dataset absent (set QEC_TWIN_HW_DATA)",
)

BASES = ("X", "Z")


def _p_of_weight(w: float) -> float:
    """Probability whose MWPM weight log((1-p)/p) is exactly ``w``."""

    return 1.0 / (1.0 + float(np.exp(w)))


def _generic_toy():
    """Small chain with generic (tie-free) probabilities."""

    return m4_decode.toy_chain_dem(
        2,
        3,
        p_space=lambda c, layer: 0.03 + 0.011 * c + 0.007 * layer,
        p_time=lambda c, layer: 0.02 + 0.009 * c + 0.005 * layer,
        p_left=[0.041, 0.067, 0.053],
        p_right=[0.072, 0.058, 0.089],
    )


def _uniform_toy():
    """Per-class uniform chain: every space edge carries exactly its class
    probability, i.e. the static-arm situation where the A3c R-hat == 1
    negative control must be an exact no-op."""

    return m4_decode.toy_chain_dem(3, 3, p_space=0.05, p_time=0.031, p_left=0.07, p_right=0.09)


_UNIFORM_R1_TABLE = {
    (-1, 0): (0.07, 1.0),
    (0, 1): (0.05, 1.0),
    (1, 2): (0.05, 1.0),
    (2, 3): (0.09, 1.0),
}


def _sample_dets(dem, shots: int, seed: int):
    det_data, _, _ = dem.compile_sampler(seed=seed).sample(int(shots))
    return np.asarray(det_data, dtype=np.bool_)


# ---------------------------------------------------------------- S1 pin


def test_pymatching_version_pin_and_provenance():
    prov = m4_decode.pymatching_provenance()
    print(f"pymatching provenance: {prov}")
    assert prov["pinned_version"] == "2.4.0"
    assert prov["installed_version"] == prov["pinned_version"], (
        f"S1 decoder pin violated: installed pymatching {prov['installed_version']} "
        f"!= registered {prov['pinned_version']} (install via the [hw] extra)"
    )
    for key in ("wheel_filename", "wheel_sha256", "installed_binary_sha256", "provenance_complete"):
        assert key in prov
    if not prov["provenance_complete"]:
        print(
            "WARNING: wheel sha256 not yet recorded -- run "
            "`pip download --no-deps pymatching==2.4.0 -d /tmp/pm_wheel` and pin "
            "record_wheel_provenance('/tmp/pm_wheel') into m4_decode.py"
        )


# ---------------------------------------------------------------- decode path


def test_decode_dem_bool_vs_packed_inputs():
    dem = _generic_toy()
    dets = _sample_dets(dem, 500, seed=m4_decode.M4_SEED)
    preds_bool = m4_decode.decode_dem(dem, dets)
    packed = np.packbits(dets.astype(np.uint8), axis=1, bitorder="little")
    preds_packed = m4_decode.decode_dem(dem, packed)
    assert preds_bool.dtype == np.uint8 and preds_bool.shape == (500, 1)
    assert np.array_equal(preds_bool, preds_packed)

    preds_w, weights = m4_decode.decode_with_weights(dem, dets)
    assert np.array_equal(preds_w, preds_bool)
    assert weights.shape == (500,) and np.all(np.isfinite(weights)) and np.all(weights >= 0)

    with pytest.raises(ValueError):
        m4_decode.decode_dem(dem, dets.astype(np.float64))
    with pytest.raises(ValueError):
        m4_decode.decode_dem(dem, np.zeros((4, 3), dtype=np.uint8))  # width matches nothing


def test_pin_p1d_determinism_toy():
    dem = _generic_toy()
    dets = _sample_dets(dem, 400, seed=m4_decode.M4_SEED + 1)
    result = m4_decode.pin_p1d(dem, dets)
    assert result["passed"] and result["bit_identical"] and result["n_shots"] == 400


# ---------------------------------------------------------------- P1g


def test_pin_p1g_exact_vs_pymatching():
    result = m4_decode.pin_p1g()
    for row in result["results"]:
        print(
            f"P1g {row['toy']}: D={row['num_detectors']} M={row['num_errors']} "
            f"syndromes={row['num_syndromes']} ties={row['num_ties']} "
            f"disagreements={row['num_disagreements']} "
            f"min_margin={row['min_nonzero_margin']}"
        )
        assert row["num_ties"] == 0, f"P1g toy {row['toy']} has exact ties -- redesign the toy"
        assert row["num_disagreements"] == 0, (
            f"P1g FAIL on {row['toy']}: pymatching disagrees with the exact "
            f"minimum-weight reference at syndrome {row['first_disagreement']}"
        )
        # margins must dwarf pymatching's 2^24-bucket weight quantization
        # (bucket ~ max_weight / 2^24 ~ 3e-7 on these toys)
        assert row["min_nonzero_margin"] is not None
        assert row["min_nonzero_margin"] > 1e-5
    assert result["passed"]


# ---------------------------------------------------------------- G4 guards


def test_jitter_control_no_flips_at_toy_margins():
    dem = _generic_toy()
    dets = _sample_dets(dem, 500, seed=m4_decode.M4_SEED + 2)
    rate = m4_decode.jitter_control(dem, dets, eps=1e-9, seed=m4_decode.M4_SEED)
    print(f"G4 jitter flip rate (toy, eps=1e-9): {rate}")
    assert rate == 0.0  # toy margins are O(0.1); 1e-9 jitter cannot reorder


def test_sim_round_trip_toy_matches_exact_prediction():
    dem = _generic_toy()
    result = m4_decode.sim_round_trip(dem, 20_000, seed=m4_decode.M4_SEED)
    print(
        f"G4 sim round-trip: sim_ler={result.sim_ler:.5f} "
        f"predicted_ler={result.predicted_ler:.5f} raw={result.raw_flip_rate:.5f}"
    )
    assert np.isfinite(result.predicted_ler)
    sigma = float(
        np.sqrt(result.predicted_ler * (1.0 - result.predicted_ler) / result.n_shots)
    )
    assert abs(result.sim_ler - result.predicted_ler) <= 5.0 * sigma + 1e-12, (
        "sim round-trip miss = pipeline bug, nothing downstream"
    )
    assert 0.0 <= result.sim_ler <= 1.0 and 0.0 <= result.raw_flip_rate <= 1.0


# ------------------------------------------- G4 sim-round-trip pass rule (FIX)


def test_sim_round_trip_rule_declaration_constants():
    # No silent constants: the declared rule carries its constants + tags.
    rule = m4_decode.SIM_ROUND_TRIP_RULE
    assert rule["z_sigmas"] == m4_decode.SIM_ROUND_TRIP_Z
    assert rule["second_seed_offset"] == m4_decode.SIM_ROUND_TRIP_SECOND_SEED_OFFSET
    assert tuple(rule["sane_ler_bounds"]) == m4_decode.SIM_ROUND_TRIP_SANE_LER_BOUNDS
    assert rule["epistemic"]["exact_enumeration"] == "a"
    assert rule["epistemic"]["comparison_bands"] == "c"


def test_sim_round_trip_check_toy_enumerable():
    result = m4_decode.sim_round_trip_check(_generic_toy(), 20_000, seed=m4_decode.M4_SEED)
    print(
        f"G4 rule (toy): sim={result.sim_ler:.5f} pred={result.predicted_ler:.5f} "
        f"second={result.sim_ler_second_seed:.5f} band={result.binomial_band:.3g} "
        f"failures={result.failures}"
    )
    assert result.scale == "toy-enumerable"
    assert np.isfinite(result.predicted_ler)  # exact enumeration branch alive (a)
    assert result.exact_within_band is True
    assert result.reproducible_bit_exact
    assert result.binomial_consistent
    assert result.passed and result.failures == ()


def test_sim_round_trip_check_production_scale():
    # 3 chains x 4 layers = 25 errors > the enumeration cap => production branch.
    dem = m4_decode.toy_chain_dem(3, 4)
    assert len(m4_decode.dem_errors(dem)) > m4_decode.MAX_ENUM_ERRORS
    result = m4_decode.sim_round_trip_check(dem, 20_000, seed=m4_decode.M4_SEED)
    print(
        f"G4 rule (production): sim={result.sim_ler:.5f} "
        f"second={result.sim_ler_second_seed:.5f} band={result.binomial_band:.3g} "
        f"raw={result.raw_flip_rate:.5f} failures={result.failures}"
    )
    assert result.scale == "production"
    assert np.isnan(result.predicted_ler)  # declared, never silently invented
    assert result.exact_within_band is None
    lo, hi = m4_decode.SIM_ROUND_TRIP_SANE_LER_BOUNDS
    assert lo < result.sim_ler < hi
    assert result.reproducible_bit_exact
    assert result.binomial_consistent
    assert result.passed and result.failures == ()


def test_sim_round_trip_check_production_tripwire_fires():
    # Degenerate production-branch DEM (rates ~1e-7, 100 shots): the seeded
    # sampler produces zero flips, sim_ler == 0.0 violates the OPEN sane
    # interval and the (c) tripwire must fire loudly.
    dem = m4_decode.toy_chain_dem(3, 4, p_space=1e-7, p_time=1e-7, p_left=1e-7, p_right=1e-7)
    assert len(m4_decode.dem_errors(dem)) > m4_decode.MAX_ENUM_ERRORS
    result = m4_decode.sim_round_trip_check(dem, 100, seed=m4_decode.M4_SEED)
    assert result.scale == "production"
    assert result.sim_ler == 0.0
    assert not result.passed
    assert any("sane" in f for f in result.failures)


# ------------------------------------------ S2 per-unit actual observables (FIX)


def _toy_readout_circuit():
    """3 data qubits (0, 2, 4) / 2 measure qubits (1, 3), one ancilla round,
    SCRAMBLED final transversal readout order (M 4 0 2) so chain ordering must
    come from the final-layer detectors + the observable anchor, never from
    record order. Sweep frame: CX (X Pauli, anticommutes with the Z readout)
    on each data qubit; one CZ on qubit 0 that COMMUTES and must be excluded.

    Record map: 0 = MR q1, 1 = MR q3, 2 = M q4, 3 = M q0, 4 = M q2.
    Chain order (data position -> record): 0 -> 3 (q0), 1 -> 4 (q2), 2 -> 2 (q4).
    """

    import stim

    return stim.Circuit(
        """
        CX sweep[0] 0 sweep[1] 2 sweep[2] 4
        CZ sweep[3] 0
        MR 1 3
        M 4 0 2
        DETECTOR rec[-2] rec[-1] rec[-5]
        DETECTOR rec[-1] rec[-3] rec[-4]
        OBSERVABLE_INCLUDE(0) rec[-2]
        """
    )


def _write_synthetic_ds(tmp_path, n_shots: int = 257):
    """Fake RepCodeD29 tree (X/sample_00) around the toy readout circuit with
    random b8 fixtures; obs_flips_actual.b8 = the hand-derived full-chain
    observable (record 3 XOR sweep bit 0)."""

    root = tmp_path / "fake_d29"
    d = root / "X" / "sample_00"
    d.mkdir(parents=True)
    (d / "circuit_ideal.stim").write_text(str(_toy_readout_circuit()))
    rng = np.random.default_rng(m4_decode.M4_SEED)
    meas = rng.integers(0, 2, size=(n_shots, 5)).astype(np.uint8)
    sweep = rng.integers(0, 2, size=(n_shots, 4)).astype(np.uint8)
    b8_io.pack_bits(meas).tofile(str(d / "measurements.b8"))
    b8_io.pack_bits(sweep).tofile(str(d / "sweep_bits.b8"))
    full_chain = (meas[:, 3] ^ sweep[:, 0]).astype(np.uint8)
    b8_io.pack_bits(full_chain[:, None]).tofile(str(d / "obs_flips_actual.b8"))
    return RepCodeD29(root), meas, sweep


def test_unit_observable_spec_toy_chain_ordering():
    spec = m4_decode.unit_observable_spec(_toy_readout_circuit())
    assert spec.num_measurements == 5
    assert spec.num_data == 3
    assert spec.data_records == (3, 4, 2)  # structural order, NOT record order
    assert spec.data_qubits == (0, 2, 4)
    assert spec.data_bases == ("Z", "Z", "Z")
    # anticommutation filter: CX included per qubit; the commuting CZ excluded
    assert spec.sweep_refs == ((0,), (1,), (2,))
    assert spec.anchor_record == 3


def test_unit_actual_observables_synthetic_b8(tmp_path):
    ds, meas, sweep = _write_synthetic_ds(tmp_path)
    units = [(0, 2), (1, 2), (0, 1)]  # full chain + sub-units sharing a leftmost
    arr = m4_decode.unit_actual_observables(ds, "X", 0, units, chunk_shots=64)
    assert arr.dtype == np.uint8 and arr.shape == (meas.shape[0], 3)
    # hand-computed XOR references (record map in _toy_readout_circuit):
    assert np.array_equal(arr[:, 0], meas[:, 3] ^ sweep[:, 0])  # leftmost = q0
    assert np.array_equal(arr[:, 1], meas[:, 4] ^ sweep[:, 1])  # leftmost = q2
    assert np.array_equal(arr[:, 2], meas[:, 3] ^ sweep[:, 0])  # same leftmost as full
    assert 0.0 < arr[:, 1].mean() < 1.0  # plausible nonconstant bits


def test_pin_p1b_units_synthetic_roundtrip(tmp_path):
    ds, _, _ = _write_synthetic_ds(tmp_path)
    result = m4_decode.pin_p1b_units(ds, "X", extra_units=[(1, 2)], chunk_shots=50)
    assert result["passed"] and result["bit_exact"] and result["spec_match"]
    assert result["full_unit"] == (0, 2)
    assert result["mismatched_shots"] == 0
    row = result["extra_units"][0]
    assert row["unit"] == (1, 2) and row["nonconstant"]


def test_unit_actual_observables_heldout_refusal(tmp_path):
    ds, _, _ = _write_synthetic_ds(tmp_path)
    # samples 1-99 are refused BEFORE any file access without the explicit flag
    for sample in (1, 5, 50, 99):
        with pytest.raises(ValueError, match="allow_heldout"):
            m4_decode.unit_actual_observables(ds, "X", sample, [(0, 2)])
    # the flag unlocks the validation gate ONLY; the absent sample dir then
    # fails on data access (FileNotFoundError), never on the refusal
    with pytest.raises(FileNotFoundError):
        m4_decode.unit_actual_observables(ds, "X", 5, [(0, 2)], allow_heldout=True)
    # out-of-release samples are invalid regardless of the flag
    for sample in (-1, 100):
        with pytest.raises(ValueError):
            m4_decode.unit_actual_observables(ds, "X", sample, [(0, 2)], allow_heldout=True)
    # the pin never passes the flag: held-out samples are refused there too
    with pytest.raises(ValueError, match="allow_heldout"):
        m4_decode.pin_p1b_units(ds, "X", sample=5)


def test_unit_actual_observables_units_validation(tmp_path):
    ds, _, _ = _write_synthetic_ds(tmp_path)
    for bad in ([3], [(2, 1)], [(0, 0)], [(-1, 2)], [(0, 3)], [(0, 1, 2)], []):
        with pytest.raises(ValueError):
            m4_decode.unit_actual_observables(ds, "X", 0, bad)


# ---------------------------------------------------------------- A3c two-pass


def test_two_pass_noop_at_r_hat_one():
    # Negative control (registration S4): with R-hat == 1 on the static-arm
    # values, the bump target equals the current probability everywhere, no
    # mutation happens, and predictions are bit-identical to the static arm
    # over ALL 2^D syndromes.
    dem = _uniform_toy()
    dets = m4_decode.all_syndromes(9)
    static = m4_decode.decode_dem(dem, dets)
    two_pass = m4_decode.two_pass_decode(dem, dets, _UNIFORM_R1_TABLE)
    assert np.array_equal(static, two_pass)


def test_two_pass_burst_reweight_flips_decision():
    # Synthetic burst DEM (weights chosen exactly): chain C=2, L=4 with
    #   w_time = 12, w_left = [2, 2, 2, 8] (layer-resolved), w_space = w_right = 1.5.
    # Syndrome = left-qubit burst {D(0,1), D(0,2), D(0,3)}.
    # Static optimum (weight 7): lb@1 + lb@2 + [space+right]@3 -> L0 parity 0,
    #   margin 1.0 to the best parity-1 matching (weight 8).
    # Pass-1 fires left-boundary space edges at t in {1, 2} -> bumps the left
    # qubit's space edges at layers {0,1,2,3} to min(r*R, 1/2-eps) with
    # r = p(w=2), R = 4 -> p* = 0.4768..., w* = 0.0928...; the re-decode
    # optimum is the all-left-boundary matching (weight ~0.279) -> L0 = 1.
    dem = m4_decode.toy_chain_dem(
        2,
        4,
        p_space=_p_of_weight(1.5),
        p_time=_p_of_weight(12.0),
        p_left=[_p_of_weight(2.0), _p_of_weight(2.0), _p_of_weight(2.0), _p_of_weight(8.0)],
        p_right=_p_of_weight(1.5),
    )
    dets = np.zeros((1, 8), dtype=np.bool_)
    dets[0, [2, 4, 6]] = True  # D(0,1), D(0,2), D(0,3) with det id = 2*layer + chain

    static = m4_decode.decode_dem(dem, dets)
    assert static[0, 0] == 0, "static decode must pick the parity-0 escape matching"

    r_hat = _p_of_weight(2.0)
    table = {(-1, 0): (r_hat, 4.0)}
    two_pass = m4_decode.two_pass_decode(dem, dets, table)
    assert two_pass[0, 0] == 1, "A3c bump must recover the burst (parity-1) matching"

    # state restore: a second two-pass run is bit-identical (no leaked mutation)
    again = m4_decode.two_pass_decode(dem, dets, table)
    assert np.array_equal(two_pass, again)
    # and the static arm is untouched by construction (fresh matching)
    assert np.array_equal(static, m4_decode.decode_dem(dem, dets))


def test_two_pass_geometry_classification():
    geometry = m4_decode.space_edge_geometry(_uniform_toy())
    # 3 chains x 3 layers: space edges per layer = 2 bulk + 2 boundary = 4
    assert geometry.num_space_edges == 12
    assert geometry.num_unclassified_singles == 0
    assert ((-1, 0), 0) in geometry.by_qubit_layer
    assert ((2, 3), 2) in geometry.by_qubit_layer


# ---------------------------------------------------------------- fleet driver


def test_decode_fleet_toy_matches_serial(tmp_path):
    dem_a = _generic_toy()
    dem_b = _uniform_toy()
    dets_a = _sample_dets(dem_a, 137, seed=m4_decode.M4_SEED + 3)
    dets_b = _sample_dets(dem_b, 53, seed=m4_decode.M4_SEED + 4)

    packed_a = np.packbits(dets_a.astype(np.uint8), axis=1, bitorder="little")
    b8_path = tmp_path / "dets_a.b8"
    packed_a.tofile(str(b8_path))

    jobs = [
        m4_decode.DecodeJob("a_mem", str(dem_a), dets=dets_a, chunk_shots=7),
        m4_decode.DecodeJob("b_mem", str(dem_b), dets=dets_b, chunk_shots=10),
        m4_decode.DecodeJob(
            "a_b8",
            str(dem_a),
            dets_path=str(b8_path),
            bits_per_shot=dem_a.num_detectors,
            chunk_shots=13,
        ),
        m4_decode.DecodeJob(
            "b_2pass",
            str(dem_b),
            dets=dets_b,
            chunk_shots=11,
            mode="two_pass",
            rR_table=_UNIFORM_R1_TABLE,
        ),
    ]
    results = m4_decode.decode_fleet(jobs, n_workers=2)
    assert [r.job_id for r in results] == ["a_mem", "b_mem", "a_b8", "b_2pass"]

    serial_a = m4_decode.decode_dem(dem_a, dets_a)
    serial_b = m4_decode.decode_dem(dem_b, dets_b)
    assert np.array_equal(results[0].preds, serial_a)
    assert np.array_equal(results[1].preds, serial_b)
    assert np.array_equal(results[2].preds, serial_a)  # same shots via .b8 streaming
    assert np.array_equal(results[3].preds, serial_b)  # R-hat == 1 no-op inside the fleet
    assert results[0].n_shots == 137 and results[1].n_shots == 53

    # serial path (n_workers=1) is bit-identical to the pool path
    serial_results = m4_decode.decode_fleet(jobs, n_workers=1)
    for pooled, serial in zip(results, serial_results):
        assert pooled.job_id == serial.job_id
        assert np.array_equal(pooled.preds, serial.preds)


# ---------------------------------------------------------------- hardware (sample_00 ONLY)


@requires_hw
def test_hw_p1a_m2d_parity_smoke_sample00():
    ds = RepCodeD29.from_env()
    for basis in BASES:
        result = m4_decode.pin_p1a(ds, [0], basis)
        sample = result["results"][0]
        det, obs = sample["detection_events"], sample["obs_flips"]
        print(
            f"P1a {basis}/sample_00 via {sample['converter_circuit']}: "
            f"det {det.mismatched_bytes}/{det.total_bytes} mismatched bytes, "
            f"obs {obs.mismatched_bytes}/{obs.total_bytes}"
        )
        assert result["passed"], f"P1a FAIL {basis}/sample_00"


@requires_hw
def test_hw_p1b_observable_bitexact_sample00():
    ds = RepCodeD29.from_env()
    for basis in BASES:
        result = m4_decode.pin_p1b(ds, basis)
        print(
            f"P1b {basis}/sample_00 via {result['circuit_used']}: "
            f"rec={result['measurement_indices']} qubits={result['qubits']} "
            f"bases={result['measurement_bases']} coords={result['qubit_coords']} "
            f"sweep={result['sweep_indices']} mismatches="
            f"{result['mismatched_shots']}/{result['total_shots']}"
        )
        assert result["bit_exact"], (
            f"P1b FAIL {basis}/sample_00: our observable construction mismatches "
            f"obs_flips_actual on {result['mismatched_shots']} shots "
            f"(first at {result['first_mismatch_shot']}); attempts: {result['attempts']}"
        )


@requires_hw
def test_hw_p1b_units_fullchain_crosscheck_sample00():
    # FIX ROUND (reviewer item 2): (a)-class cross-check -- the per-unit
    # construction at unit == full chain (0, 28) reproduces obs_flips_actual
    # bit-exactly, and its position-0 spec is IDENTICAL to the P1b spec.
    # Sub-unit (17, 21) = window 16's data qubits: plausible nonconstant bits.
    ds = RepCodeD29.from_env()
    for basis in BASES:
        result = m4_decode.pin_p1b_units(ds, basis, extra_units=[(17, 21)])
        row = result["extra_units"][0]
        print(
            f"P1b-units {basis}/sample_00 via {result['circuit_used']}: "
            f"spec_match={result['spec_match']} bit_exact={result['bit_exact']} "
            f"mismatches={result['mismatched_shots']}/{result['total_shots']} "
            f"anchor=rec{result['anchor_record']} sweep_ref={result['anchor_sweep_ref']}; "
            f"sub-unit {row['unit']}: mean={row['mean']:.4f} "
            f"nonconstant={row['nonconstant']}"
        )
        assert result["num_data"] == 29 and result["full_unit"] == (0, 28)
        assert result["spec_match"], (
            f"P1b-units {basis}/sample_00: per-unit position-0 spec diverges from "
            "the P1b full-chain spec"
        )
        assert result["bit_exact"], (
            f"P1b-units FAIL {basis}/sample_00: full-chain unit mismatches "
            f"obs_flips_actual on {result['mismatched_shots']} shots "
            f"(first at {result['first_mismatch_shot']})"
        )
        assert result["passed"]
        assert row["nonconstant"], "window-16 sub-unit observable constant -- implausible"
        assert 0.0 < row["mean"] < 1.0


@requires_hw
def test_hw_p1e_shipped_prediction_smoke_sample00():
    ds = RepCodeD29.from_env()
    shots = int(os.environ.get("QEC_TWIN_M4_P1E_SHOTS", "20000"))
    shot_slice = None if shots <= 0 else (0, shots)
    for basis in BASES:
        result = m4_decode.pin_p1e(ds, [0], basis, shot_slice=shot_slice)
        r = result["results"][0]
        margins = np.sort(r.weight_margins)[:10]
        print(
            f"P1e {basis}/sample_00: mismatch {r.n_mismatch}/{r.n_shots} "
            f"(fraction {r.mismatch_fraction:.2e}); ours-vs-actual {r.ours_vs_actual_flips}, "
            f"shipped-vs-actual {r.shipped_vs_actual_flips}; "
            f"smallest weight margins on mismatches: {margins}"
        )
        # build smoke asserts only the registered OUTER certification bound;
        # the bit-exact / tie-attribution routing is the scoring driver's job.
        assert r.mismatch_fraction <= 1e-3, (
            f"P1e {basis}/sample_00 mismatch {r.mismatch_fraction:.2e} > 1e-3 -- "
            f"registration routing: HALT + degeneracy audit"
        )


@requires_hw
def test_hw_p1f_dem_hash_audit_sample00():
    ds = RepCodeD29.from_env()
    result = m4_decode.pin_p1f(ds, [0])
    print(f"P1f sample_00 DEM sha256: {result['hashes']}")
    assert result["report_only"] is True
    assert set(result["hashes"]) == {(basis, 0) for basis in ds.bases}
    assert result["num_distinct"] >= 1
