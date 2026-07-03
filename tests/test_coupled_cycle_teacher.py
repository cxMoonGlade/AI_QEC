"""CoupledCycleTeacher — constraint-ledger falsifiers (C-1..C-12).

Ledger: the module docstring of ``qec_twin.mechanisms.coupled_teachers``.
CPU-fine tests cover construction/validation/fan-out (pure metadata + numpy);
CUDA-marked tests cover the dense GPU emit path. The two independent
ground-truth tests (faithfulness rule I) carry their closed-form derivations
in their docstrings, written before the asserts.
"""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pytest
import torch

from qec_twin.audit.certify.types import Regime
from qec_twin.mechanisms.axis1_primitives import Axis1PrimitiveParams
from qec_twin.mechanisms.coupled_teachers import (
    CoupledCycleTeacher,
    default_coupled_code_spec,
    derive_round_map_for_substep_schedule,
    params_for_substep_from_round_map,
    per_round_axis1_params,
    trajectory_mean_instrument,
)
from qec_twin.mechanisms.source_coupling import (
    cross_mechanism_correlation,
    default_source_coupling_config,
    parameter_series,
    source_to_params,
    trajectory_to_params,
)
from qec_twin.mechanisms.source_process import (
    OneOverFDriftSource,
    PhaseBurstSource,
    RTNSource,
)
from qec_twin.simulator.analog_schedule import (
    AnalogSubstepIR,
    SubstepOperation,
    SubstepSchedule,
    compile_code_spec_to_substep_schedule,
    h3_h5_duration_policy,
)
from qec_twin.simulator.axis1_record_evidence import (
    Axis1ReadoutResetInstrumentSpec,
    axis1_measurement_record_evidence_manifest,
)

requires_cuda = pytest.mark.skipif(
    not torch.cuda.is_available(), reason="GPU-only: dense Axis-1 record emit path"
)


def _sealed_schedule(rounds: int) -> SubstepSchedule:
    return compile_code_spec_to_substep_schedule(default_coupled_code_spec(rounds))


def _nonconstant_source_seed(source: OneOverFDriftSource, n_cycles: int) -> int:
    for seed in range(64):
        z = source.sample(seed=seed, n_cycles=n_cycles).payload_series("z_radns")
        if np.unique(z).size >= 2:
            return seed
    raise AssertionError("no non-constant trajectory found in 64 seeds")


# --------------------------------------------------------------------------- #
# C-4 — round derivation (CPU)                                                 #
# --------------------------------------------------------------------------- #
def test_round_map_two_round_schedule():
    """Terminal off-by-one control on a known 2-round compiled schedule:
    tick 0 -> round 0, tick 1 -> round 1, terminal block (tick 2, the final
    data readout) -> clamped to round 1 and flagged terminal."""
    schedule = _sealed_schedule(2)
    round_map = derive_round_map_for_substep_schedule(schedule, rounds=2)
    assert set(round_map) == {s.substep_id for s in schedule.substeps}
    saw_terminal = False
    for substep in schedule.substeps:
        round_index, terminal = round_map[substep.substep_id]
        if substep.tick_index == 0:
            assert (round_index, terminal) == (0, False)
        elif substep.tick_index == 1:
            assert (round_index, terminal) == (1, False)
        else:
            assert substep.tick_index == 2
            assert (round_index, terminal) == (1, True)
            saw_terminal = True
    assert saw_terminal
    barriers = [s for s in schedule.substeps if s.kind == "barrier"]
    assert sorted(b.tick_index for b in barriers) == [0, 1]


def test_round_map_rejects_wrong_rounds_argument():
    """rounds argument disagreeing with the compiled schedule must raise
    (tick 2 substeps land beyond the terminal block of a 1-round map; a
    3-round map misses round-2 measurement keys)."""
    schedule = _sealed_schedule(2)
    with pytest.raises(ValueError):
        derive_round_map_for_substep_schedule(schedule, rounds=1)
    with pytest.raises(ValueError):
        derive_round_map_for_substep_schedule(schedule, rounds=3)


def _hand_built_measurement_schedule(key: str, tick_index: int) -> SubstepSchedule:
    op = SubstepOperation(
        name="M",
        targets=(0,),
        source_step_index=0,
        basis="Z",
        measurement_keys=(key,),
    )
    substep = AnalogSubstepIR(
        substep_id="s0000",
        round_index=None,
        tick_index=tick_index,
        order_index=0,
        kind="measurement",
        operations=(op,),
        active_qubits=(0,),
        idle_qubits=(),
        participants=((0,),),
        dt_ns_nominal=None,
        dt_ns_bracket=(100.0, 1000.0),
        dt_source="bracket",
        mechanism_slots=(),
        measurement_keys=(key,),
        window_support=(0,),
    )
    return SubstepSchedule(
        source_kind="circuit_ir",
        source_hash="tamper-fixture",
        schedule_template=None,
        num_qubits=1,
        substeps=(substep,),
        duration_policy=h3_h5_duration_policy(),
    )


def test_round_map_tampered_keys_raise():
    """A measurement keyed ``round1:`` sitting at tick 0 (mis-keyed layout)
    must raise — never a silent uniform-params fallback (red-team R1)."""
    tampered = _hand_built_measurement_schedule("round1:x0", tick_index=0)
    with pytest.raises(ValueError, match="round derivation mismatch"):
        derive_round_map_for_substep_schedule(tampered, rounds=2)


def test_round_map_unknown_key_raises():
    unknown = _hand_built_measurement_schedule("weird:key", tick_index=0)
    with pytest.raises(ValueError, match="unrecognized measurement key"):
        derive_round_map_for_substep_schedule(unknown, rounds=2)


def test_round_map_terminal_key_off_tick_raises():
    misplaced = _hand_built_measurement_schedule("final:q0:Z", tick_index=0)
    with pytest.raises(ValueError, match="terminal data key"):
        derive_round_map_for_substep_schedule(misplaced, rounds=2)


def test_params_for_substep_callable_no_fallback():
    """The injected callable resolves rounds through the validated map and
    refuses unknown substeps (red-team R1); params differ across rounds."""
    schedule = _sealed_schedule(2)
    round_map = derive_round_map_for_substep_schedule(schedule, rounds=2)
    per_round = (
        Axis1PrimitiveParams(
            zeta_rad_per_ns=1.0e-4, gamma_phi_per_ns=1.0e-5, gamma_1_per_ns=1.0e-5
        ),
        Axis1PrimitiveParams(
            zeta_rad_per_ns=1.0e-4, gamma_phi_per_ns=2.0e-5, gamma_1_per_ns=1.0e-5
        ),
    )
    resolver = params_for_substep_from_round_map(round_map, per_round)
    round0 = next(s for s in schedule.substeps if s.tick_index == 0)
    round1 = next(s for s in schedule.substeps if s.tick_index == 1)
    assert resolver(round0).gamma_phi_per_ns == pytest.approx(1.0e-5)
    assert resolver(round1).gamma_phi_per_ns == pytest.approx(2.0e-5)
    assert resolver(round0).gamma_phi_per_ns != resolver(round1).gamma_phi_per_ns

    @dataclasses.dataclass
    class _Stub:
        substep_id: str

    with pytest.raises(ValueError, match="not in the validated round map"):
        resolver(_Stub(substep_id="not-a-substep"))


def test_params_differ_across_rounds():
    """R1 positive control: a non-constant trajectory through the Theta
    fan-out + baseline lowering yields per-round Axis1PrimitiveParams that
    actually DIFFER across rounds (gamma_phi strictly monotone in z at the
    default sensitivity 0.35 > 0)."""
    cfg = default_source_coupling_config()
    source = OneOverFDriftSource()
    seed = _nonconstant_source_seed(source, n_cycles=4)
    z = source.sample(seed=seed, n_cycles=4).payload_series("z_radns")
    baseline = Axis1PrimitiveParams(
        zeta_rad_per_ns=2.0e-3, gamma_phi_per_ns=1.0 / 30000.0, gamma_1_per_ns=1.0 / 30000.0
    )
    per_round = [
        per_round_axis1_params(baseline, p) for p in trajectory_to_params(z, cfg)
    ]
    gammas = {p.gamma_phi_per_ns for p in per_round}
    assert len(gammas) >= 2
    # gamma_1 and the other baseline fields are HELD (S-3).
    assert {p.gamma_1_per_ns for p in per_round} == {baseline.gamma_1_per_ns}
    assert {p.drive_area_rad for p in per_round} == {baseline.drive_area_rad}


# --------------------------------------------------------------------------- #
# C-2 — memory-ful shared arm (CPU)                                            #
# --------------------------------------------------------------------------- #
def test_shared_arm_rejects_non_memoryful_source():
    with pytest.raises(ValueError, match="memory-ful"):
        CoupledCycleTeacher(2, source=PhaseBurstSource(event_times=(0,)))


def test_shared_arm_rejects_baseline_timeline():
    """A permuted/baseline timeline is not a valid shared arm (red-team R3):
    the arm dispatch seam refuses coupling_mode='independent' and
    baseline-marked timelines. (Reaches the private ``_fan_out`` seam on
    purpose — it is the arm-dispatch unit under test.)"""
    teacher = CoupledCycleTeacher(2)
    timeline = OneOverFDriftSource().sample(seed=3, n_cycles=2)
    baseline = timeline.independent_baseline(seed=4)
    with pytest.raises(ValueError, match="red-team R3"):
        teacher._fan_out(baseline, base_seed=0, trajectory=0)


def test_constructor_validation():
    with pytest.raises(ValueError, match="rounds >= 2"):
        CoupledCycleTeacher(1)
    with pytest.raises(ValueError, match="shots_per_trajectory"):
        CoupledCycleTeacher(2, shots_per_trajectory=0)
    with pytest.raises(ValueError, match="GPU-only"):
        CoupledCycleTeacher(2, device="cpu")
    with pytest.raises(ValueError, match="coupling_arm"):
        CoupledCycleTeacher(2, coupling_arm="banana")


# --------------------------------------------------------------------------- #
# C-9 — ablation arms (CPU)                                                    #
# --------------------------------------------------------------------------- #
def test_markovian_baseline_marginals_and_decorrelation():
    """Matched marginals + broken coupling (thresholds reused from
    test_source_process.py: shared > 0.9, independent |corr| < 0.25;
    sorted-marginal equality at atol=1e-15)."""
    teacher = CoupledCycleTeacher(2)
    baseline = teacher.markovian_baseline()
    assert teacher.coupling_arm == "shared"
    assert baseline.coupling_arm == "independent"
    timeline = OneOverFDriftSource().sample(seed=11, n_cycles=600)
    shared = teacher._fan_out(timeline, base_seed=7, trajectory=0)
    independent = baseline._fan_out(timeline, base_seed=7, trajectory=0)
    assert {p.coupling_mode for p in shared} == {"shared"}
    assert {p.coupling_mode for p in independent} == {"independent"}
    assert (
        cross_mechanism_correlation(shared, "detuning_radns", "drive_omega_radns")
        > 0.9
    )
    assert (
        abs(
            cross_mechanism_correlation(
                independent, "detuning_radns", "drive_omega_radns"
            )
        )
        < 0.25
    )
    for field in ("gamma_phi_per_ns", "zz_zeta_radns", "readout_flip_p"):
        np.testing.assert_allclose(
            np.sort(parameter_series(shared, field)),
            np.sort(parameter_series(independent, field)),
            rtol=0,
            atol=1e-15,
        )
    # trajectory-mean instrument is permutation-invariant => identical arms.
    assert trajectory_mean_instrument(shared).readout_p0_to_1 == pytest.approx(
        trajectory_mean_instrument(independent).readout_p0_to_1
    )


def test_off_source_constant_params():
    teacher = CoupledCycleTeacher(2)
    off = teacher.off_source()
    assert off.coupling_arm == "off"
    timeline = off._source.sample(seed=5, n_cycles=2)
    assert np.all(timeline.payload_series("z_radns") == 0.0)
    params = off._fan_out(timeline, base_seed=0, trajectory=0)
    theta0 = source_to_params(0.0, default_source_coupling_config()).to_manifest()
    for p in params:
        assert p.to_manifest() == theta0


# --------------------------------------------------------------------------- #
# C-7 / C-12 / C-1 — isolation, m grounding, seal (CPU)                        #
# --------------------------------------------------------------------------- #
def _assert_no_record_keys(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            assert key not in {"det", "obs"}, f"record key {key!r} at {path}"
            _assert_no_record_keys(value, f"{path}.{key}")
    elif isinstance(node, (list, tuple)):
        for i, value in enumerate(node):
            _assert_no_record_keys(value, f"{path}[{i}]")


def test_truth_isolation():
    """Truth is evaluator-only and carries NO det/obs record arrays (C-7);
    the declared slice-1 scope items are present."""
    teacher = CoupledCycleTeacher(2)
    truth = teacher.truth
    _assert_no_record_keys(truth)
    assert truth["visibility"] == "evaluator_only"
    assert truth["coupling_arm"] == "shared"
    assert truth["per_round_modulated_fields"] == [
        "zeta_rad_per_ns",
        "gamma_phi_per_ns",
    ]
    assert "gamma_1_per_ns" in truth["held_at_baseline_fields"]
    assert set(truth["deferred_theta_fields"]) == {
        "detuning_radns",
        "drive_omega_radns",
        "spillover_cx",
        "cz_depol_p",
    }
    assert truth["instrument_policy"]["epistemic_class"] == "c"
    assert truth["last_emit"] is None


def test_m1_raises():
    teacher = CoupledCycleTeacher(2)
    with pytest.raises(NotImplementedError, match="m=0 only"):
        teacher.emit(Regime(R=2, n_stab=2), m=1, N=4, seed=0)


def test_regime_mismatch_raises():
    teacher = CoupledCycleTeacher(2)
    with pytest.raises(ValueError, match="regime.R"):
        teacher.emit(Regime(R=3, n_stab=2), m=0, N=4, seed=0)
    with pytest.raises(ValueError, match="n_stab"):
        teacher.emit(Regime(R=2, n_stab=8), m=0, N=4, seed=0)


def test_emit_refuses_unsealed_schedule():
    """C-1 / red-team R5: a public-constructor (unsealed) rebuild of the same
    substeps must be refused by emit. The seal check precedes any device
    work, so this runs CPU-fine."""
    teacher = CoupledCycleTeacher(2)
    sealed = teacher.sched
    unsealed = SubstepSchedule(
        source_kind=sealed.source_kind,
        source_hash=sealed.source_hash,
        schedule_template=sealed.schedule_template,
        num_qubits=sealed.num_qubits,
        substeps=sealed.substeps,
        duration_policy=sealed.duration_policy,
        qubit_roles=sealed.qubit_roles,
        qubit_coords=sealed.qubit_coords,
        static_zz_couplings=sealed.static_zz_couplings,
        static_zz_calibrations=sealed.static_zz_calibrations,
        axis1_local_lindblad_context=sealed.axis1_local_lindblad_context,
        record_layout_ref=sealed.record_layout_ref,
    )
    teacher._sched = unsealed
    with pytest.raises(ValueError, match="compiler-owned schedule seal"):
        teacher.emit(Regime(R=2, n_stab=2), m=0, N=4, seed=0)


def test_emit_clifford_slice_not_implemented():
    teacher = CoupledCycleTeacher(2)
    with pytest.raises(NotImplementedError):
        teacher.emit_clifford_slice(Regime(R=2, n_stab=2), p_x=1e-3, m=0, N=4, seed=0)


# --------------------------------------------------------------------------- #
# GPU emit path                                                                #
# --------------------------------------------------------------------------- #
@requires_cuda
def test_emit_payload_surface():
    """C-3 / red-team R4: keys EXACTLY {det, obs}; uint8; (N, R*n_stab)/(N,);
    values in {0,1}; truth records the emit bookkeeping (evaluator-side)."""
    teacher = CoupledCycleTeacher(2, shots_per_trajectory=8)
    n = 32
    payload = teacher.emit(Regime(R=2, n_stab=2), m=0, N=n, seed=101)
    assert set(payload) == {"det", "obs"}
    det, obs = payload["det"], payload["obs"]
    assert isinstance(det, np.ndarray) and isinstance(obs, np.ndarray)
    assert det.dtype == np.uint8 and obs.dtype == np.uint8
    assert det.shape == (n, 2 * 2)
    assert obs.shape == (n,)
    assert set(np.unique(det)) <= {0, 1}
    assert set(np.unique(obs)) <= {0, 1}
    truth = teacher.truth
    assert truth["last_emit"]["N"] == n
    assert truth["last_emit"]["shots_per_trajectory"] == 8
    _assert_no_record_keys(truth)


@requires_cuda
def test_emit_reproducible():
    """C-8: same (regime, m, N, seed) => byte-identical arrays; a different
    seed differs (N large enough that chance-equality is ~exp(-65))."""
    teacher = CoupledCycleTeacher(2, shots_per_trajectory=256)
    regime = Regime(R=2, n_stab=2)
    a = teacher.emit(regime, m=0, N=256, seed=7)
    b = teacher.emit(regime, m=0, N=256, seed=7)
    np.testing.assert_array_equal(a["det"], b["det"])
    np.testing.assert_array_equal(a["obs"], b["obs"])
    c = teacher.emit(regime, m=0, N=256, seed=8)
    assert not (
        np.array_equal(a["det"], c["det"]) and np.array_equal(a["obs"], c["obs"])
    )


@requires_cuda
def test_batched_emit_declares_clusters():
    """C-11 / red-team R6: batching is declared in truth; batched and
    unbatched OFF-source arms share the marginal record law (the off arm has
    no trajectory variation, so batching is exact there — declared)."""
    base = CoupledCycleTeacher(2)
    off_batched = CoupledCycleTeacher(2, shots_per_trajectory=64).off_source()
    n = 512
    payload = off_batched.emit(Regime(R=2, n_stab=2), m=0, N=n, seed=3)
    truth = off_batched.truth
    assert truth["shots_per_trajectory"] == 64
    assert truth["last_emit"]["shots_per_trajectory"] == 64
    assert truth["last_emit"]["n_trajectories"] == n // 64
    off_unbatched = base.off_source()
    payload_u = off_unbatched.emit(Regime(R=2, n_stab=2), m=0, N=n, seed=4)
    # marginal smoke: same law => detector means within 5 sigma of each other.
    for col in range(payload["det"].shape[1]):
        pa = float(payload["det"][:, col].mean())
        pb = float(payload_u["det"][:, col].mean())
        pooled = max((pa + pb) / 2.0, 1.0 / n)
        se = math.sqrt(2.0 * pooled * (1.0 - pooled) / n)
        assert abs(pa - pb) <= 5.0 * se + 1e-9


@requires_cuda
def test_off_source_matches_plain_manifest():
    """Construction-independence positive control (R1-adjacent): the default
    coupled CodeSpec pins its Lindblad-context baseline to the Theta(0)
    fan-out point, so a CONSTANT Theta(0) callable must reproduce the plain
    (no-callable) manifest EXACTLY — catching both a misrouted callable and a
    default-path regression of the pinned injected-emitter interface."""
    cfg = default_source_coupling_config()
    schedule = _sealed_schedule(2)
    round_map = derive_round_map_for_substep_schedule(schedule, rounds=2)
    theta0 = source_to_params(0.0, cfg)
    baseline = Axis1PrimitiveParams(
        zeta_rad_per_ns=float(theta0.zz_zeta_radns),
        gamma_phi_per_ns=float(theta0.gamma_phi_per_ns),
        gamma_1_per_ns=1.0 / 30000.0,
    )
    instrument = Axis1ReadoutResetInstrumentSpec(
        readout_p0_to_1=cfg.readout_flip_base_p,
        readout_p1_to_0=cfg.readout_flip_base_p,
        reset_flip_probability=cfg.reset_flip_base_p,
    )
    with_callable = axis1_measurement_record_evidence_manifest(
        schedule,
        device="cuda",
        instrument_spec=instrument,
        params_for_substep=params_for_substep_from_round_map(
            round_map, (baseline, baseline)
        ),
    )
    plain = axis1_measurement_record_evidence_manifest(
        schedule,
        device="cuda",
        instrument_spec=instrument,
    )
    rec_a = with_callable["record_evidence"]
    rec_b = plain["record_evidence"]
    assert rec_a["measurement_keys"] == rec_b["measurement_keys"]
    assert rec_a["detector_records"] == rec_b["detector_records"]
    assert rec_a["logical_observable_records"] == rec_b["logical_observable_records"]
    np.testing.assert_allclose(
        np.asarray(rec_a["record_probabilities"], dtype=np.float64),
        np.asarray(rec_b["record_probabilities"], dtype=np.float64),
        rtol=0,
        atol=1e-14,
    )


@requires_cuda
def test_z1_rates_match_closed_form():
    """INDEPENDENT ground truth (faithfulness rule I; C-10a) — derivation
    BEFORE the assert:

    The z1 chain of the compiled fixture is Z-diagonal end-to-end: data
    qubit 1 is prepared |0> and never rotated (the Z-basis check applies no
    H), gamma_up = 0 so no excitation channel exists, and dephasing (n-type
    collapse) never moves Z populations => data 1 is EXACTLY |0> in every
    branch, and ancilla 4's pre-instrument outcome is 1 only through the
    reset preparation flip. Per round, with the off-source instrument
    constants p_rs = reset_flip_base_p, p_ro = readout_flip_base_p:

        P(round{r}:z1 = 1) = p_rs XOR p_ro = p_rs + p_ro - 2 p_rs p_ro + eps,
        |eps| <= p_rs * (1 - exp(-gamma_1 * 30ns))  ~ 5e-6
        (the reset-flipped |1> decaying during the single 30 ns CX window
        between ancilla 4's reset and its measurement; gamma_1 = 1/30000).

    Rounds are independent (fresh reset, independent flips), so with
    p := P(round:z1=1):

        rate(delta:z1:round1) = 2 p (1 - p)          [XOR of two ind. rounds]
        rate(final:z1)        = p (1-p_ro) + (1-p) p_ro   [final:q1:Z flips
                                 only through readout: data 1 is exactly |0>]
        rate(obs = logical_z2) = p_ro                  [data 2 exactly |0>]

    These predictions use ONLY config constants + Bernoulli algebra — not the
    emitter's probability tables. Off-source arm => the trajectory-mean
    instrument equals the base constants exactly. Bands: 5 sigma shot noise
    + 1e-4 slack for eps-class corrections (declared class (c))."""
    cfg = default_source_coupling_config()
    n = 1 << 16
    teacher = CoupledCycleTeacher(2, shots_per_trajectory=n).off_source()
    payload = teacher.emit(Regime(R=2, n_stab=2), m=0, N=n, seed=11)
    names = teacher.truth["detector_names"]
    p_rs = cfg.reset_flip_base_p
    p_ro = cfg.readout_flip_base_p
    p = p_rs + p_ro - 2.0 * p_rs * p_ro
    predictions = {
        "delta:z1:round1": 2.0 * p * (1.0 - p),
        "final:z1": p * (1.0 - p_ro) + (1.0 - p) * p_ro,
    }
    for name, predicted in predictions.items():
        rate = float(payload["det"][:, names.index(name)].mean())
        se = math.sqrt(predicted * (1.0 - predicted) / n)
        assert abs(rate - predicted) <= 5.0 * se + 1e-4, (
            f"{name}: measured {rate:.6f}, closed-form {predicted:.6f}"
        )
    obs_rate = float(payload["obs"].mean())
    se_obs = math.sqrt(p_ro * (1.0 - p_ro) / n)
    assert abs(obs_rate - p_ro) <= 5.0 * se_obs + 1e-4


@requires_cuda
def test_x0_delta_rate_tracks_gamma_phi():
    """INDEPENDENT ground truth (faithfulness rule I; C-10b) — derivation
    BEFORE the assert:

    Data qubit 0 carries X-frame coherence between its round-0 and round-1
    X-check projections. A T2 collapse c = sqrt(2 gamma_phi) n decays the
    off-diagonal as exp(-gamma_phi t), so the pre-instrument probability that
    the X outcome flips between the two rounds is

        q(gamma_phi) = 0.5 * (1 - exp(-gamma_phi * tau_eff)).

    tau_eff bracket (from the compiled schedule's declared durations,
    h3_h5_v1: 1q gate 25 ns, 2q gate 30 ns; measurement/reset windows carry
    no nominal dt and lower no channel): between the round-0 H-sandwich end
    and the round-1 H-sandwich start, data 0 is an idle spectator of the
    CX(d1,a4) union-support window (30 ns, fully X-frame-exposed); the two
    H(d0) windows (2 x 25 ns) rotate the frame (exposure factor in [0,1]);
    the CX(d0,a3) window sits INSIDE the sandwich where the X information
    lives in Z populations (n-dephasing inert). Hence

        tau_eff in [30, 80] ns   (declared bracket).

    The instrument + gamma_1-driven flips enter both arms identically and
    only damp the DIFFERENCE by (1-2c)(1-2q_rest) with
    c = 2 p_ro (1-p_ro) ~ 0.0198 and q_rest <~ 2e-3, i.e. damping in
    [0.95, 1.0]. Comparing two OFF-source teachers that differ ONLY in
    gamma_phi_base (x20):

        drate = rate_B - rate_A
              = damping * 0.5 * (exp(-g_A tau) - exp(-g_B tau)),
        band  = [0.85 * 0.5 * d(tau=30) * 0.95, 1.05 * 0.5 * d(tau=80)]
        (declared class-(c) band; direction assert at 5 sigma).
    """
    cfg_a = default_source_coupling_config()
    cfg_b = dataclasses.replace(
        cfg_a, gamma_phi_base_per_ns=20.0 * cfg_a.gamma_phi_base_per_ns
    )
    n = 1 << 18
    teacher_a = CoupledCycleTeacher(2, config=cfg_a, shots_per_trajectory=n).off_source()
    teacher_b = CoupledCycleTeacher(2, config=cfg_b, shots_per_trajectory=n).off_source()
    regime = Regime(R=2, n_stab=2)
    det_a = teacher_a.emit(regime, m=0, N=n, seed=21)["det"]
    det_b = teacher_b.emit(regime, m=0, N=n, seed=22)["det"]
    col = teacher_a.truth["detector_names"].index("delta:x0:round1")
    rate_a = float(det_a[:, col].mean())
    rate_b = float(det_b[:, col].mean())
    drate = rate_b - rate_a
    se = math.sqrt(
        rate_a * (1.0 - rate_a) / n + max(rate_b, 1.0 / n) * (1.0 - rate_b) / n
    )
    # direction: exact theorem (gamma_phi strictly increases the flip rate).
    assert drate > 5.0 * se, f"direction: drate={drate:.3e} <= 5*se={5*se:.3e}"
    g_a = cfg_a.gamma_phi_base_per_ns
    g_b = cfg_b.gamma_phi_base_per_ns

    def _dq(tau_ns: float) -> float:
        return 0.5 * (math.exp(-g_a * tau_ns) - math.exp(-g_b * tau_ns))

    lo = 0.85 * _dq(30.0) * 0.95
    hi = 1.05 * _dq(80.0)
    assert lo <= drate <= hi, (
        f"magnitude: drate={drate:.4e} outside declared band [{lo:.4e}, {hi:.4e}]"
    )


@requires_cuda
def test_channels_mean_field_surface():
    """channels() reports the per-substep Kraus field at Theta(0) with the
    validated round labels; kraus stacks are CPTP-shaped tensors."""
    teacher = CoupledCycleTeacher(2)
    rows = teacher.channels()
    assert rows, "expected at least one assembled substep channel"
    for row in rows:
        assert row["params_point"] == "theta_zero_mean_field"
        assert row["epistemic_class"] == "c"
        assert 0 <= row["round_index"] < 2
        kraus = row["kraus"]
        assert kraus.ndim == 3 and kraus.shape[-1] == kraus.shape[-2]
        dim = kraus.shape[-1]
        identity = torch.eye(dim, dtype=kraus.dtype, device=kraus.device)
        tp_residual = (
            torch.einsum("kij,kil->jl", kraus.conj(), kraus) - identity
        ).abs().max()
        assert float(tp_residual) <= 1e-10
