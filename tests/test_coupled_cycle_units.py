"""Stage-D batch ``coupled_cycle`` -- per-unit L0+L1+L2 coverage of
``error_coupling_simulator.teachers.coupled_cycle`` (17 in-scope public units;
``CoupledCycleTeacher.emit`` is gpu_bound out_of_scope).

Full-coverage program (docs/twin_validation/wave2_6_unit_test_contract.md SS12.3/12.4;
work-list docs/twin_validation/l3_release_package_unit_inventory.md). ``CoupledCycleTeacher``
is the evaluator-only source-coupled record teacher (slice 1, dense): a shared memory-ful
source trajectory is fanned out per QEC cycle into per-round Axis-1 params and emitted as
``{det,obs}`` records through the sealed dense Axis-1 record path.

CPU DISCIPLINE. Every in-scope unit is exercised WITHOUT a GPU:
  * __init__ / schedule-compile / round-map / fixtures / truth / export are pure metadata +
    numpy + stim (no torch touched);
  * ``channels()`` runs on CPU by monkeypatching its SOLE gpu callee
    ``_assemble_selection_joint_channel`` at the boundary; the stub captures the (device,
    params, calibrations) it is called with so the CPU-logic can be value-pinned;
  * ``emit()`` is gpu_bound out_of_scope (torch multinomial on cuda) and is NOT covered here --
    its seal / regime / m=0 / N>=1 contracts are separately CPU-tested in
    ``tests/test_coupled_cycle_teacher.py`` (mutmut is coverage-guided: leaving emit uncovered in
    THIS selection keeps its GPU body out of the L2 denominator).

L2 DISCIPLINE (the standing lesson: 100% coverage != discrimination). Every load-bearing value is
PINNED against an INDEPENDENT recompute, and every validation RAISE asserts its EXACT message
string (mutmut wraps/roundtrips string literals -- a substring ``match=`` still passes them, an
exact-equality assert kills them). VALUE-PINS: the round map (tick witness), the per-round param
fan-out, the truth dict, the trajectory-mean instrument, the derived seed, the full export
manifest, the full d3_repz code-spec structure, the wrapped Theta(0) metadata context, and the
ablation-arm inheritance. assert_discriminates gives each three-witness / round-label invariant
teeth.
"""
from __future__ import annotations

import copy
import dataclasses
import hashlib
import re

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates

import error_coupling_simulator.teachers.coupled_cycle as cc
from error_coupling_simulator.teachers.coupled_cycle import (
    CoupledCycleTeacher,
    default_coupled_code_spec,
    default_coupled_code_spec_4q,
    default_coupled_code_spec_d3_repz,
    derive_round_map_for_substep_schedule,
    params_for_substep_from_round_map,
    per_round_axis1_params,
    trajectory_mean_instrument,
)
from error_coupling_simulator.certify.types import Regime
from error_coupling_simulator.mechanisms.axis1_primitives import Axis1PrimitiveParams
from error_coupling_simulator.source.coupling import (
    cross_mechanism_correlation,
    default_source_coupling_config,
    independent_baseline_trajectory_to_params,
    parameter_series,
    source_to_params,
    trajectory_to_params,
)
from error_coupling_simulator.source.process import (
    OneOverFDriftSource,
    PhaseBurstSource,
    RTNSource,
)
from error_coupling_simulator.frontend.analog_schedule import (
    AnalogSubstepIR,
    SubstepOperation,
    SubstepSchedule,
    compile_code_spec_to_substep_schedule,
    h3_h5_duration_policy,
)
from error_coupling_simulator.frontend.axis1_record_evidence import (
    Axis1ReadoutResetInstrumentSpec,
)

# --------------------------------------------------------------------------- #
# INDEPENDENT recompute helpers (from-scratch; NOT the module's own derivation) #
# --------------------------------------------------------------------------- #
#: the schema string the seed + truth pins check against, hard-coded so a mutation of the
#: module's COUPLED_TEACHER_SCHEMA diverges from this independent copy.
_SCHEMA = "qec_twin.mechanisms.CoupledCycleTeacher.v1"
_ROUND_RE = re.compile(r"^round(\d+):")
_FINAL_RE = re.compile(r"^final:q(\d+):[XYZ]$")

#: a NON-default coupling config: source_to_params(0.0, .) then differs from the default in
#: gamma_phi (base x3), so a mutant that swaps ``self._config`` for None/default is caught.
_CUSTOM_CFG = dataclasses.replace(
    default_source_coupling_config(),
    gamma_phi_base_per_ns=3.0 * default_source_coupling_config().gamma_phi_base_per_ns,
)


def _raises_exact(exc, msg, fn):
    """pytest.raises but pinning the EXACT message string (kills mutmut's string-literal
    wrap/roundtrip mutations that a substring ``match=`` lets survive)."""
    with pytest.raises(exc) as ei:
        fn()
    assert str(ei.value) == msg, f"message mismatch\n got: {str(ei.value)!r}\n exp: {msg!r}"


def _indep_seed(base_seed: int, trajectory: int, purpose: str) -> int:
    payload = f"{_SCHEMA}:{int(base_seed)}:{int(trajectory)}:{purpose}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % (2**63 - 1)


def _indep_round_map(schedule, rounds: int) -> dict:
    """WITNESS A (tick_index): substep -> (round, terminal) from the tick alone."""
    out = {}
    for s in schedule.substeps:
        tick = int(s.tick_index)
        out[s.substep_id] = (tick, False) if tick < rounds else (rounds - 1, True)
    return out


def _sealed(rounds: int, **kw):
    return compile_code_spec_to_substep_schedule(default_coupled_code_spec(rounds, **kw))


def _baseline_params() -> Axis1PrimitiveParams:
    return Axis1PrimitiveParams(
        zeta_rad_per_ns=2.0e-3, gamma_phi_per_ns=1.0 / 30000.0, gamma_1_per_ns=1.0 / 30000.0
    )


def _coupled_with(zeta: float, gamma_phi: float):
    return dataclasses.replace(
        source_to_params(0.0, default_source_coupling_config()),
        zz_zeta_radns=float(zeta),
        gamma_phi_per_ns=float(gamma_phi),
    )


def _mk_substep(kind: str, tick: int, keys=(), i: int = 0) -> AnalogSubstepIR:
    ops = (
        (SubstepOperation(name="M", targets=(0,), source_step_index=0, basis="Z",
                          measurement_keys=tuple(keys)),)
        if kind == "measurement" else ()
    )
    return AnalogSubstepIR(
        substep_id=f"s{i:04d}", round_index=None, tick_index=tick, order_index=i, kind=kind,
        operations=ops, active_qubits=(0,), idle_qubits=(), participants=((0,),),
        dt_ns_nominal=None, dt_ns_bracket=(100.0, 1000.0), dt_source="bracket",
        mechanism_slots=(), measurement_keys=tuple(keys), window_support=(0,),
    )


def _hand_schedule(subs) -> SubstepSchedule:
    return SubstepSchedule(
        source_kind="circuit_ir", source_hash="hand-fixture", schedule_template=None,
        num_qubits=1, substeps=tuple(subs), duration_policy=h3_h5_duration_policy(),
    )


class _StubCounts:
    def __init__(self, num_qubits, num_detectors, num_observables, num_measurements):
        self.num_qubits = num_qubits
        self.num_detectors = num_detectors
        self.num_observables = num_observables
        self.num_measurements = num_measurements


class _StubAssembled:
    def __init__(self, kraus):
        self.kraus = kraus


# =========================================================================== #
# derive_round_map_for_substep_schedule -- 100% branch, EXACT raise messages    #
# =========================================================================== #
def test_L0_round_map_happy_two_round():
    sched = _sealed(2)
    rm = derive_round_map_for_substep_schedule(sched, rounds=2)
    assert rm == _indep_round_map(sched, 2)                     # VALUE-PIN vs tick witness
    assert any(term for (_r, term) in rm.values())
    for s in sched.substeps:
        r, term = rm[s.substep_id]
        assert (r, term) == (1, True) if int(s.tick_index) == 2 else (r < 2)


def test_L0_round_map_rounds_below_one_raises():
    _raises_exact(ValueError, "rounds must be >= 1, got 0",
                  lambda: derive_round_map_for_substep_schedule(_sealed(2), rounds=0))


def test_L0_round_map_wrong_rounds_argument_raises():
    sched = _sealed(2)
    with pytest.raises(ValueError, match="1-round schedule"):
        derive_round_map_for_substep_schedule(sched, rounds=1)
    with pytest.raises(ValueError, match="terminal data key"):
        derive_round_map_for_substep_schedule(sched, rounds=3)


def test_L0_round_map_tick_beyond_terminal_raises():
    sched = _hand_schedule([_mk_substep("measurement", 5, (), 0)])
    _raises_exact(
        ValueError,
        "substep 's0000' has tick_index=5 beyond the terminal block of a 2-round schedule; "
        "round derivation cannot be validated",
        lambda: derive_round_map_for_substep_schedule(sched, rounds=2))


def test_L0_round_map_key_round_beyond_rounds_raises():
    sched = _hand_schedule([_mk_substep("measurement", 0, ("round2:x0",), 0)])
    _raises_exact(
        ValueError, "measurement key 'round2:x0' names round 2 outside a 2-round schedule",
        lambda: derive_round_map_for_substep_schedule(sched, rounds=2))


def test_L0_round_map_tampered_key_tick_mismatch_raises():
    sched = _hand_schedule([_mk_substep("measurement", 0, ("round1:x0",), 0)])
    _raises_exact(
        ValueError,
        "round derivation mismatch on substep 's0000': key 'round1:x0' names round 1 but "
        "tick_index=0 (red-team R1: refusing, never falling back to uniform params)",
        lambda: derive_round_map_for_substep_schedule(sched, rounds=2))


def test_L0_round_map_terminal_key_off_tick_raises():
    sched = _hand_schedule([_mk_substep("measurement", 0, ("final:q0:Z",), 0)])
    _raises_exact(
        ValueError,
        "terminal data key 'final:q0:Z' sits at tick_index=0, expected the terminal block "
        "tick_index=2",
        lambda: derive_round_map_for_substep_schedule(sched, rounds=2))


def test_L0_round_map_unrecognized_key_raises():
    sched = _hand_schedule([_mk_substep("measurement", 0, ("weird:key",), 0)])
    _raises_exact(
        ValueError,
        "unrecognized measurement key 'weird:key' on substep 's0000'; round derivation cannot "
        "be validated",
        lambda: derive_round_map_for_substep_schedule(sched, rounds=2))


def test_L0_round_map_barrier_witness_mismatch_raises():
    subs = [
        _mk_substep("measurement", 0, ("round0:x0",), 0),
        _mk_substep("measurement", 1, ("round1:x0",), 1),
        _mk_substep("measurement", 2, ("final:q0:Z",), 2),
    ]
    _raises_exact(
        ValueError,
        "barrier witness mismatch: expected one barrier per round (ticks [0, 1]), got ticks []",
        lambda: derive_round_map_for_substep_schedule(_hand_schedule(subs), rounds=2))


def test_L0_round_map_uncovered_round_raises():
    subs = [
        _mk_substep("barrier", 0, i=0), _mk_substep("barrier", 1, i=1),
        _mk_substep("measurement", 0, ("round0:x0",), 2),
        _mk_substep("measurement", 2, ("final:q0:Z",), 3),
    ]
    _raises_exact(
        ValueError,
        "measurement keys cover rounds [0], expected all of [0, 1]; rounds argument and schedule "
        "disagree",
        lambda: derive_round_map_for_substep_schedule(_hand_schedule(subs), rounds=2))


def test_L0_round_map_no_terminal_keys_raises():
    subs = [
        _mk_substep("barrier", 0, i=0), _mk_substep("barrier", 1, i=1),
        _mk_substep("measurement", 0, ("round0:x0",), 2),
        _mk_substep("measurement", 1, ("round1:x0",), 3),
    ]
    _raises_exact(
        ValueError, "no terminal 'final:q{i}:{basis}' measurement keys found",
        lambda: derive_round_map_for_substep_schedule(_hand_schedule(subs), rounds=2))


def test_L0_round_map_hand_built_happy_matches_independent():
    subs = [
        _mk_substep("barrier", 0, i=0), _mk_substep("barrier", 1, i=1),
        _mk_substep("measurement", 0, ("round0:x0",), 2),
        _mk_substep("measurement", 1, ("round1:x0",), 3),
        _mk_substep("measurement", 2, ("final:q0:Z",), 4),
    ]
    sched = _hand_schedule(subs)
    assert derive_round_map_for_substep_schedule(sched, rounds=2) == _indep_round_map(sched, 2)


# =========================================================================== #
# params_for_substep_from_round_map -- callable + its (nested) resolver          #
# =========================================================================== #
def test_L0_params_for_substep_resolves_and_refuses_unknown():
    sched = _sealed(2)
    rm = derive_round_map_for_substep_schedule(sched, rounds=2)
    per_round = (
        Axis1PrimitiveParams(zeta_rad_per_ns=1e-4, gamma_phi_per_ns=1e-5, gamma_1_per_ns=1e-5),
        Axis1PrimitiveParams(zeta_rad_per_ns=1e-4, gamma_phi_per_ns=2e-5, gamma_1_per_ns=1e-5),
    )
    resolver = params_for_substep_from_round_map(rm, per_round)
    r0 = next(s for s in sched.substeps if s.tick_index == 0)
    r1 = next(s for s in sched.substeps if s.tick_index == 1)
    assert resolver(r0).gamma_phi_per_ns == pytest.approx(1e-5)
    assert resolver(r1).gamma_phi_per_ns == pytest.approx(2e-5)
    assert resolver(r0).gamma_phi_per_ns != resolver(r1).gamma_phi_per_ns

    @dataclasses.dataclass
    class _Stub:
        substep_id: str

    _raises_exact(
        ValueError,
        "substep 'not-a-substep' is not in the validated round map; refusing to guess its round "
        "(red-team R1)",
        lambda: resolver(_Stub(substep_id="not-a-substep")))


def test_L1_params_for_substep_maps_every_round():
    """DISCRIMINATING: for EVERY substep resolver == per_round[independent-tick-round(substep)]."""
    sched = _sealed(3)
    rm = derive_round_map_for_substep_schedule(sched, rounds=3)
    ind = _indep_round_map(sched, 3)
    per_round = tuple(
        Axis1PrimitiveParams(zeta_rad_per_ns=1e-4, gamma_phi_per_ns=(k + 1) * 1e-5,
                             gamma_1_per_ns=1e-5)
        for k in range(3)
    )
    resolver = params_for_substep_from_round_map(rm, per_round)
    for s in sched.substeps:
        r = ind[s.substep_id][0]
        assert resolver(s).gamma_phi_per_ns == pytest.approx(per_round[r].gamma_phi_per_ns)


# =========================================================================== #
# per_round_axis1_params -- unit-exact 1:1 field map, held fields at baseline    #
# =========================================================================== #
_HELD_FIELDS = (
    "gamma_1_per_ns", "gamma_up_per_ns", "gamma_readout_phi_per_ns", "drive_area_rad",
    "drive_omega_rad_per_ns", "fsim_delta_theta_rad", "fsim_delta_phi_rad",
)


def _prop_per_round_field_map(pair):
    baseline, coupled, got = pair
    assert got.zeta_rad_per_ns == pytest.approx(float(coupled.zz_zeta_radns))
    assert got.gamma_phi_per_ns == pytest.approx(float(coupled.gamma_phi_per_ns))
    for f in _HELD_FIELDS:
        assert getattr(got, f) == getattr(baseline, f)


def test_L0_per_round_axis1_params_maps_and_holds():
    baseline = _baseline_params()
    coupled = _coupled_with(zeta=7.0e-4, gamma_phi=9.0e-5)
    got = per_round_axis1_params(baseline, coupled)
    _prop_per_round_field_map((baseline, coupled, got))
    assert got.zeta_rad_per_ns != baseline.zeta_rad_per_ns
    assert got.gamma_phi_per_ns != baseline.gamma_phi_per_ns


def test_KILLER_per_round_field_map_discriminates():
    baseline = _baseline_params()
    coupled = _coupled_with(zeta=7.0e-4, gamma_phi=9.0e-5)
    real = per_round_axis1_params(baseline, coupled)
    wrong = dataclasses.replace(real, gamma_phi_per_ns=float(coupled.zz_zeta_radns))
    assert_discriminates(
        lambda g: _prop_per_round_field_map((baseline, coupled, g)), real, wrong,
        label="per_round zeta/gamma_phi field map")


@settings(max_examples=200, deadline=None)
@given(
    zeta=st.floats(0.0, 1.0e-2, allow_nan=False, allow_infinity=False),
    gamma=st.floats(0.0, 1.0e-3, allow_nan=False, allow_infinity=False),
)
def test_L1_per_round_axis1_params_field_map(zeta, gamma):
    baseline = _baseline_params()
    coupled = _coupled_with(zeta=zeta, gamma_phi=gamma)
    _prop_per_round_field_map((baseline, coupled, per_round_axis1_params(baseline, coupled)))


# =========================================================================== #
# trajectory_mean_instrument -- symmetric mean readout/reset, pair-flip 0, source #
# =========================================================================== #
def _prop_trajectory_mean(cycles, inst):
    r = float(np.mean([float(p.readout_flip_p) for p in cycles]))
    s = float(np.mean([float(p.reset_flip_p) for p in cycles]))
    assert inst.readout_p0_to_1 == pytest.approx(r)
    assert inst.readout_p1_to_0 == pytest.approx(r)
    assert inst.reset_flip_probability == pytest.approx(s)
    assert inst.readout_pair_flip_probability == 0.0
    assert inst.epistemic_class == "c"
    assert inst.source == "coupled_cycle_teacher_trajectory_mean_v1"   # provenance pin


def test_L0_trajectory_mean_instrument_value_and_empty_raise():
    cycles = [
        dataclasses.replace(source_to_params(0.0, default_source_coupling_config()),
                            readout_flip_p=r, reset_flip_p=s)
        for r, s in [(0.01, 0.005), (0.03, 0.007), (0.02, 0.009)]
    ]
    inst = trajectory_mean_instrument(cycles)
    _prop_trajectory_mean(cycles, inst)
    assert inst.readout_p0_to_1 == pytest.approx(0.02)
    assert inst.reset_flip_probability == pytest.approx(0.007)
    _raises_exact(ValueError, "trajectory_mean_instrument requires at least one cycle",
                  lambda: trajectory_mean_instrument([]))


def test_KILLER_trajectory_mean_discriminates():
    cfg = default_source_coupling_config()
    cycles = [
        dataclasses.replace(source_to_params(0.0, cfg), readout_flip_p=r, reset_flip_p=s)
        for r, s in [(0.01, 0.005), (0.03, 0.011)]
    ]
    real = trajectory_mean_instrument(cycles)
    wrong = dataclasses.replace(real, readout_p0_to_1=float(cycles[0].readout_flip_p),
                                readout_p1_to_0=float(cycles[0].readout_flip_p))
    assert_discriminates(lambda inst: _prop_trajectory_mean(cycles, inst), real, wrong,
                         label="trajectory-mean readout")


@settings(max_examples=150, deadline=None)
@given(
    reads=st.lists(st.floats(0.0, 0.4, allow_nan=False), min_size=1, max_size=6),
    resets=st.lists(st.floats(0.0, 0.4, allow_nan=False), min_size=1, max_size=6),
)
def test_L1_trajectory_mean_instrument(reads, resets):
    cfg = default_source_coupling_config()
    n = min(len(reads), len(resets))
    cycles = [
        dataclasses.replace(source_to_params(0.0, cfg), readout_flip_p=reads[i], reset_flip_p=resets[i])
        for i in range(n)
    ]
    _prop_trajectory_mean(cycles, trajectory_mean_instrument(cycles))


# =========================================================================== #
# default_coupled_code_spec / _4q / _d3_repz -- fixture builders + Theta(0) wrap #
# =========================================================================== #
def _assert_theta0_context(spec, cfg):
    """VALUE-PIN the wrapped Theta(0) lindblad context + static-ZZ edge (kills the cfg / z=0
    / num_qubits mutations in _wrap_coupled_code_spec and the fixture builders): the context's
    gamma_phi/zeta are source_to_params(0.0, cfg) at the SPECIFIC (non-default) config."""
    theta0 = source_to_params(0.0, cfg)
    ctx = spec.metadata["axis1_local_lindblad_context"]
    assert ctx["gamma_phi_per_ns"] == pytest.approx(float(theta0.gamma_phi_per_ns))
    assert ctx["zeta_rad_per_ns"] == pytest.approx(float(theta0.zz_zeta_radns))
    assert [0, 3] in spec.metadata["axis1_static_zz_couplings"]


def test_L0_default_coupled_code_spec_5q():
    # config=None resolves to the default; an explicit NON-default config threads through the wrap.
    spec_default = default_coupled_code_spec(2, config=None)
    _assert_theta0_context(spec_default, default_source_coupling_config())
    spec = default_coupled_code_spec(2, config=_CUSTOM_CFG)
    _assert_theta0_context(spec, _CUSTOM_CFG)
    assert spec.num_qubits == 5 and spec.rounds == 2
    assert {c.name for c in spec.checks} == {"x0", "z1"}
    assert [o.name for o in spec.logical_observables] == ["logical_z2"]


def test_L0_default_coupled_code_spec_4q():
    _assert_theta0_context(default_coupled_code_spec_4q(3, config=None),
                           default_source_coupling_config())
    spec = default_coupled_code_spec_4q(3, config=_CUSTOM_CFG)
    _assert_theta0_context(spec, _CUSTOM_CFG)
    assert spec.num_qubits == 4 and spec.rounds == 3
    assert {c.name for c in spec.checks} == {"x0"}
    assert [o.name for o in spec.logical_observables] == ["logical_z2"]


def test_L0_default_coupled_code_spec_d3_repz_full_structure():
    """FULL structural VALUE-PIN of the d3 bit-flip repetition fixture (kills every CodeQubit
    coord/index, ancilla index, PauliTerm qubit/basis, and check-coords mutation)."""
    for cfg in (None, _CUSTOM_CFG):
        spec = default_coupled_code_spec_d3_repz(2, config=cfg)
        _assert_theta0_context(spec, cfg or default_source_coupling_config())
        assert spec.name == "d3_repz_coupled_fixture"
        assert spec.num_qubits == 5 and spec.rounds == 2
        # data qubits: index / role / coords all pinned.
        assert [(q.index, q.role, q.coords) for q in spec.data_qubits] == [
            (0, "data", (0.0,)), (1, "data", (2.0,)), (2, "data", (4.0,))
        ]
        assert [(q.index, q.role, q.coords) for q in spec.ancilla_qubits] == [
            (3, "ancilla", (1.0,)), (4, "ancilla", (3.0,))
        ]
        # weight-2 Z checks: name / ancilla / (qubit,basis) terms / coords all pinned.
        checks = {c.name: c for c in spec.checks}
        z01, z12 = checks["z01"], checks["z12"]
        assert z01.ancilla == 3 and z01.coords == (1.0,)
        assert [(t.qubit, t.basis) for t in z01.terms] == [(0, "Z"), (1, "Z")]
        assert z12.ancilla == 4 and z12.coords == (3.0,)
        assert [(t.qubit, t.basis) for t in z12.terms] == [(1, "Z"), (2, "Z")]
        obs = spec.logical_observables[0]
        assert obs.name == "logical_z2"
        assert [(t.qubit, t.basis) for t in obs.terms] == [(2, "Z")]


# =========================================================================== #
# CoupledCycleTeacher construction (ctor CPU-logic; EXACT validation messages)   #
# =========================================================================== #
def test_L0_ctor_validation_raises():
    _raises_exact(
        ValueError,
        "CoupledCycleTeacher requires rounds >= 2: cross-cycle source memory needs at least two "
        "cycles, got rounds=1",
        lambda: CoupledCycleTeacher(1))
    _raises_exact(ValueError, "shots_per_trajectory must be >= 1, got 0",
                  lambda: CoupledCycleTeacher(2, shots_per_trajectory=0))
    _raises_exact(
        ValueError, "CoupledCycleTeacher is GPU-only (repo device policy); pass device='cuda', "
        "got 'cpu'",
        lambda: CoupledCycleTeacher(2, device="cpu"))
    _raises_exact(ValueError, "unknown coupling_arm 'banana'",
                  lambda: CoupledCycleTeacher(2, coupling_arm="banana"))
    _raises_exact(
        ValueError,
        "CoupledCycleTeacher accepts only the declared memory-ful source classes "
        "(OneOverFDriftSource, RTNSource) — an i.i.d./uncertified source as the shared arm is "
        "red-team R3; got PhaseBurstSource",
        lambda: CoupledCycleTeacher(2, source=PhaseBurstSource(event_times=(0,))))
    _raises_exact(
        ValueError,
        "unknown fixture 'not-a-fixture'; expected one of ['4q', '5q', 'd3_repz'] (or pass an "
        "explicit code_spec_builder)",
        lambda: CoupledCycleTeacher(2, fixture="not-a-fixture"))


def test_L0_ctor_accepts_fixtures_and_custom_builder():
    for fixture in ("5q", "4q", "d3_repz"):
        t = CoupledCycleTeacher(2, fixture=fixture)
        assert t.truth["fixture"] == fixture
    t = CoupledCycleTeacher(2, code_spec_builder=lambda r: default_coupled_code_spec_4q(r))
    assert t.n_stab == 1
    assert CoupledCycleTeacher(2, source=RTNSource()).coupling_arm == "shared"


def test_L1_ctor_baseline_params_match_independent_recompute():
    """The stored baseline params == an INDEPENDENT recompute from the SAME schedule (kills the
    ``_axis1_primitive_params_for_schedule(None)`` mutation on the ctor baseline)."""
    t = CoupledCycleTeacher(2)
    ref = cc._axis1_primitive_params_for_schedule(t._sched)
    assert t._baseline_params.to_manifest() == ref.to_manifest()


def test_L1_ctor_threads_config_into_fixture_builder():
    """The ctor passes self._config (not None) into the fixture builder, so the compiled spec's
    Theta(0) lindblad context reflects the SPECIFIC config (kills the ``builder(rounds, None)``
    mutation on the default-fixture path)."""
    t = CoupledCycleTeacher(2, config=_CUSTOM_CFG)
    ctx = t._spec.metadata["axis1_local_lindblad_context"]
    assert ctx["gamma_phi_per_ns"] == pytest.approx(
        float(source_to_params(0.0, _CUSTOM_CFG).gamma_phi_per_ns))


def test_L0_ctor_rejects_code_spec_rounds_mismatch():
    """A custom builder whose spec declares a different round count is refused (exact message)."""
    _raises_exact(
        ValueError,
        "code spec declares rounds=3, teacher was constructed with rounds=2",
        lambda: CoupledCycleTeacher(2, code_spec_builder=lambda r: default_coupled_code_spec(r + 1)))


# =========================================================================== #
# CoupledCycleTeacher.sched / .coupling_arm / .rounds / .n_stab (getters)        #
# =========================================================================== #
def test_L0_property_getters():
    t = CoupledCycleTeacher(2)
    assert t.sched is t._sched
    assert t.coupling_arm == "shared"
    assert t.rounds == 2
    assert t.n_stab == 2
    t3 = CoupledCycleTeacher(3, fixture="4q")
    assert t3.rounds == 3 and t3.n_stab == 1


# =========================================================================== #
# CoupledCycleTeacher.truth -- isolation, deep-copy, VALUE-PINS                  #
# =========================================================================== #
def _assert_no_record_keys(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            assert k not in {"det", "obs"}, f"record key {k!r} at {path}"
            _assert_no_record_keys(v, f"{path}.{k}")
    elif isinstance(node, (list, tuple)):
        for i, v in enumerate(node):
            _assert_no_record_keys(v, f"{path}[{i}]")


def test_L0_truth_value_pins_and_isolation():
    t = CoupledCycleTeacher(2)
    truth = t.truth
    _assert_no_record_keys(truth)
    assert truth["schema"] == _SCHEMA
    assert truth["visibility"] == "evaluator_only"
    assert truth["coupling_arm"] == "shared"
    assert truth["fixture"] == "5q"
    assert truth["rounds"] == 2
    assert truth["n_stab"] == 2
    assert truth["num_qubits"] == 5
    assert truth["per_round_modulated_fields"] == ["zeta_rad_per_ns", "gamma_phi_per_ns"]
    assert set(truth["deferred_theta_fields"]) == {
        "detuning_radns", "drive_omega_radns", "spillover_cx", "cz_depol_p"
    }
    assert "gamma_1_per_ns" in truth["held_at_baseline_fields"]
    assert truth["instrument_policy"]["epistemic_class"] == "c"
    assert truth["schedule"]["sealed"] is True
    assert truth["shots_per_trajectory"] == 1
    assert truth["last_emit"] is None
    assert truth["detector_names"] == list(t._detector_names)
    assert truth["observable_names"] == list(t._observable_names)
    assert truth["source"]["class"] == "OneOverFDriftSource"


def test_L1_truth_last_emit_is_a_deep_copy():
    """DEEP-COPY TRUTH (F7): mutating truth['last_emit'] must NOT alias the teacher's internal
    _last_emit (a mutant that returns a reference instead of copy.deepcopy is killed)."""
    t = CoupledCycleTeacher(2)
    t._last_emit = {"nested": {"x": [1, 2, 3]}, "N": 5}
    truth = t.truth
    assert truth["last_emit"] == {"nested": {"x": [1, 2, 3]}, "N": 5}
    truth["last_emit"]["nested"]["x"].append(999)
    truth["last_emit"]["N"] = -1
    assert t._last_emit == {"nested": {"x": [1, 2, 3]}, "N": 5}
    assert t.truth["last_emit"] == {"nested": {"x": [1, 2, 3]}, "N": 5}


def test_L1_truth_reflects_arm_and_fixture():
    assert CoupledCycleTeacher(2).off_source().truth["coupling_arm"] == "off"
    assert CoupledCycleTeacher(2).markovian_baseline().truth["coupling_arm"] == "independent"


# =========================================================================== #
# CoupledCycleTeacher.channels -- CPU (GPU assembler STUBBED at the boundary)    #
# =========================================================================== #
def _run_channels_cpu(t, monkeypatch):
    calls = []

    def fake_assemble(selection, *, dt_ns, params, device, static_zz_calibrations):
        calls.append({"substep_id": selection.substep_id, "device": device,
                      "gamma_phi": float(params.gamma_phi_per_ns),
                      "zeta": float(params.zeta_rad_per_ns), "dt_ns": float(dt_ns),
                      "calib": static_zz_calibrations})
        return _StubAssembled(np.eye(2, dtype=complex))

    monkeypatch.setattr(cc, "_assemble_selection_joint_channel", fake_assemble)
    return t.channels(), calls


def test_L0_channels_labels_and_pins(monkeypatch):
    # NON-default config so a mutant that swaps self._config for None/default is caught by the
    # captured (gamma_phi, zeta) params.
    t = CoupledCycleTeacher(2, config=_CUSTOM_CFG)
    rows, calls = _run_channels_cpu(t, monkeypatch)
    assert rows, "expected at least one assembled substep channel"
    assert len(rows) == len(calls)
    rm = derive_round_map_for_substep_schedule(t.sched, rounds=2)
    dt_by_id = {c["substep_id"]: c["dt_ns"] for c in calls}
    for row in rows:
        assert (row["round_index"], row["terminal"]) == rm[row["substep_id"]]
        assert row["params_point"] == "theta_zero_mean_field"
        assert row["epistemic_class"] == "c"
        assert 0 <= row["round_index"] < 2
        # the per-row payload keys are load-bearing (kill the dict-key rename mutations).
        assert isinstance(row["participant"], tuple)
        assert isinstance(row["primitive_names"], tuple)
        assert row["selection_id"]
        assert row["dt_ns"] == pytest.approx(dt_by_id[row["substep_id"]])
        assert row["kraus"] is not None
    # the assembler was invoked at the teacher device, with the Theta(0) LOWERED params, and the
    # REAL static-ZZ calibrations (kills the device / config / calibrations mutations).
    theta0 = per_round_axis1_params(t._baseline_params, source_to_params(0.0, t._config))
    real_calib = cc._axis1_static_zz_calibrations_for_schedule(t._sched)
    assert {c["device"] for c in calls} == {"cuda"}
    for c in calls:
        assert c["gamma_phi"] == pytest.approx(theta0.gamma_phi_per_ns)
        assert c["zeta"] == pytest.approx(theta0.zeta_rad_per_ns)
        assert c["calib"] is not None
        assert c["calib"] == real_calib


def test_KILLER_channels_round_label_discriminates(monkeypatch):
    t = CoupledCycleTeacher(2)
    rows, _ = _run_channels_cpu(t, monkeypatch)
    rm = derive_round_map_for_substep_schedule(t.sched, rounds=2)

    def prop(rs):
        for row in rs:
            assert (row["round_index"], row["terminal"]) == rm[row["substep_id"]]

    wrong = [dict(r) for r in rows]
    wrong[0]["round_index"] = 1 - wrong[0]["round_index"]
    assert_discriminates(prop, rows, wrong, label="channels round labels")


# =========================================================================== #
# CoupledCycleTeacher.export_stim_circuit -- full manifest pin + all guard arcs   #
# =========================================================================== #
_EXPECTED_5Q_MANIFEST = {
    "schema": "qec_twin.mechanisms.CoupledCycleTeacher.v1.stim_export.v1",
    "fixture": "5q",
    "code_spec_name": "axis1_codespec_mixed_basis_frontend",
    "rounds": 2,
    "n_stab": 2,
    "num_qubits": 5,
    "num_detectors": 4,
    "num_observables": 1,
    "num_measurements": 7,
    "detector_names": ["delta:x0:round1", "delta:z1:round1", "final:x0", "final:z1"],
    "observable_names": ["logical_z2"],
    "measurement_keys": ["round0:x0", "round0:z1", "round1:x0", "round1:z1",
                         "final:q0:X", "final:q1:Z", "final:q2:Z"],
    "det_column_semantics": (
        "stim detector index k == emitted det column k (record-layout declaration order)"),
    "noise_representability": (
        "ideal Clifford geometry only; Axis-1 analog noise is not representable in the stim "
        "circuit (declared); decoder-facing noise summary = frontend.interop.records_to_dem"),
}


def test_L0_export_stim_circuit_happy_full_manifest_pin():
    """P0 interop: the ideal-geometry stim circuit + manifest. FULL-MANIFEST VALUE-PIN against the
    known 5q-fixture facts (M(R)=2R+3 measurements; rounds*n_stab detectors; 1 observable) --
    kills every manifest key-rename / value-string / count mutation."""
    _circuit, manifest = CoupledCycleTeacher(2).export_stim_circuit()
    assert manifest == _EXPECTED_5Q_MANIFEST


def test_L0_export_detector_layout_mismatch_raises():
    t = CoupledCycleTeacher(2)
    t._detector_names = ("bogus",)
    with pytest.raises(RuntimeError) as ei:
        t.export_stim_circuit()
    # start-anchored so a wrap/roundtrip of the first message literal is caught.
    assert str(ei.value).startswith(
        "export/emit detector layout mismatch: recompiled circuit declares (")


def test_L0_export_observable_mismatch_raises():
    t = CoupledCycleTeacher(2)
    t._observable_names = ("bogus",)
    with pytest.raises(RuntimeError, match="observable mismatch"):
        t.export_stim_circuit()


def test_L0_export_measurement_key_mismatch_raises():
    t = CoupledCycleTeacher(2)
    t._measurement_keys = ("bogus",)
    _raises_exact(
        RuntimeError,
        "export/emit measurement-key mismatch between the recompiled circuit and the sealed "
        "schedule",
        t.export_stim_circuit)


def test_L0_export_stim_count_guards_raise(monkeypatch):
    """The three stim-count guards fire independently (monkeypatch ``counts`` so exactly one of
    num_detectors / num_observables / num_measurements is wrong at a time)."""
    t = CoupledCycleTeacher(2)
    monkeypatch.setattr("error_coupling_simulator.frontend.stim_io.counts",
                        lambda c: _StubCounts(5, 99, 1, 7))
    _raises_exact(RuntimeError,
                  "stim circuit has 99 detectors, expected rounds*n_stab = 4", t.export_stim_circuit)
    monkeypatch.setattr("error_coupling_simulator.frontend.stim_io.counts",
                        lambda c: _StubCounts(5, 4, 2, 7))
    _raises_exact(RuntimeError, "stim circuit has 2 observables, expected exactly 1",
                  t.export_stim_circuit)
    monkeypatch.setattr("error_coupling_simulator.frontend.stim_io.counts",
                        lambda c: _StubCounts(5, 4, 1, 99))
    _raises_exact(RuntimeError, "stim circuit has 99 measurements, expected 7", t.export_stim_circuit)
    # sanity: with the correct stub the happy path still returns a good manifest.
    monkeypatch.setattr("error_coupling_simulator.frontend.stim_io.counts",
                        lambda c: _StubCounts(5, 4, 1, 7))
    _c, m = t.export_stim_circuit()
    assert m["num_measurements"] == 7


# =========================================================================== #
# CoupledCycleTeacher.emit_clifford_slice -- intentionally NotImplemented        #
# =========================================================================== #
def test_L0_emit_clifford_slice_not_implemented():
    _raises_exact(
        NotImplementedError,
        "CoupledCycleTeacher slice-1 has no Clifford/bit-flip emission seam; the stim wiring "
        "anchor is a later-slice extension",
        lambda: CoupledCycleTeacher(2).emit_clifford_slice(
            Regime(R=2, n_stab=2), p_x=1e-3, m=0, N=4, seed=0))


# =========================================================================== #
# CoupledCycleTeacher.markovian_baseline / off_source -- ablation arms           #
# =========================================================================== #
def test_L0_markovian_baseline_inherits_surface():
    """The G6 negative control inherits source / config / shots / fixture and flips only the arm
    (kills the source=None / config=None / shots / fixture-inheritance mutations)."""
    parent = CoupledCycleTeacher(2, source=RTNSource(), config=_CUSTOM_CFG, shots_per_trajectory=3)
    mk = parent.markovian_baseline()
    assert parent.coupling_arm == "shared"
    assert mk.coupling_arm == "independent"
    assert mk.rounds == parent.rounds and mk.n_stab == parent.n_stab
    assert mk.truth["source"]["class"] == "RTNSource"
    assert mk.truth["shots_per_trajectory"] == 3
    assert mk.truth["fixture"] == parent.truth["fixture"]
    assert mk.truth["config"] == parent.truth["config"]


def test_L0_off_source_arm_and_constant_theta0():
    t = CoupledCycleTeacher(2)
    off = t.off_source()
    assert off.coupling_arm == "off"
    timeline = off._source.sample(seed=5, n_cycles=2)
    assert np.all(timeline.payload_series("z_radns") == 0.0)
    params = off._fan_out(timeline, base_seed=0, trajectory=0)
    theta0 = source_to_params(0.0, default_source_coupling_config()).to_manifest()
    for p in params:
        assert p.to_manifest() == theta0


def test_L0_off_source_inherits_source_config_shots():
    """off collapses amplitude to 0 but PRESERVES source class / config / shots (kills the
    off=None / amplitude=1.0 / name=None / source=None / config=None mutations)."""
    parent = CoupledCycleTeacher(2, source=RTNSource(), config=_CUSTOM_CFG, shots_per_trajectory=3)
    off = parent.off_source()
    assert off.coupling_arm == "off"
    assert off.truth["source"]["class"] == "RTNSource"
    assert off.truth["source"]["amplitude_radns"] == 0.0
    assert str(off.truth["source"]["name"]).endswith(".off")
    assert off.truth["shots_per_trajectory"] == 3
    assert off.truth["config"] == parent.truth["config"]


def test_L0_off_source_and_markovian_inherit_builder():
    """A custom code_spec_builder is inherited by both arms (kills code_spec_builder=None)."""
    parent = CoupledCycleTeacher(2, code_spec_builder=lambda r: default_coupled_code_spec_4q(r))
    assert parent.n_stab == 1
    assert parent.off_source().n_stab == 1
    assert parent.markovian_baseline().n_stab == 1


def test_L0_arms_inherit_fixture_selector():
    """A NON-default ``fixture`` (no custom builder) is inherited by both arms (kills the
    ``fixture=self._fixture`` -> default-'5q' mutation): a 4q parent yields 4q (n_stab=1) arms."""
    parent = CoupledCycleTeacher(2, fixture="4q")
    assert parent.n_stab == 1
    assert parent.off_source().n_stab == 1
    assert parent.markovian_baseline().n_stab == 1


def test_L0_off_source_requires_amplitude_bearing_source():
    t = CoupledCycleTeacher(2)

    class _NoAmp:
        name = "no-amp"

    t._source = _NoAmp()
    _raises_exact(
        NotImplementedError,
        "off_source requires an amplitude-bearing source; _NoAmp has no amplitude_radns field",
        t.off_source)


# =========================================================================== #
# private-seam value pins (CPU-reachable; mutation-covered via public callers)   #
# =========================================================================== #
def test_L1_derived_seed_matches_independent_sha256():
    for seed in (0, 7, 12345):
        for traj in (0, 3, 31):
            for purpose in ("source", "independent_permutation", "sample"):
                assert cc._derived_seed(seed, traj, purpose) == _indep_seed(seed, traj, purpose)


def test_L1_fan_out_shared_off_independent_arms():
    """_fan_out arm dispatch (C-2/C-9). NON-default config so the delegation config arg is pinned
    (a mutant swapping self._config for None/default diverges)."""
    t = CoupledCycleTeacher(2, config=_CUSTOM_CFG)
    mk = t.markovian_baseline()
    timeline = OneOverFDriftSource().sample(seed=11, n_cycles=400)
    shared = t._fan_out(timeline, base_seed=7, trajectory=0)
    indep = mk._fan_out(timeline, base_seed=7, trajectory=0)
    assert {p.coupling_mode for p in shared} == {"shared"}
    assert {p.coupling_mode for p in indep} == {"independent"}
    z = timeline.payload_series("z_radns")
    ref = trajectory_to_params(z, _CUSTOM_CFG)
    assert parameter_series(shared, "gamma_phi_per_ns").tolist() == \
        parameter_series(ref, "gamma_phi_per_ns").tolist()
    ref_ind = independent_baseline_trajectory_to_params(
        z, _CUSTOM_CFG, seed=_indep_seed(7, 0, "independent_permutation"))
    assert parameter_series(indep, "gamma_phi_per_ns").tolist() == \
        parameter_series(ref_ind, "gamma_phi_per_ns").tolist()
    assert cross_mechanism_correlation(shared, "detuning_radns", "drive_omega_radns") > 0.9
    assert abs(cross_mechanism_correlation(indep, "detuning_radns", "drive_omega_radns")) < 0.25


def test_L0_fan_out_rejects_wrong_coupling_mode():
    t = CoupledCycleTeacher(2)
    timeline = dataclasses.replace(
        OneOverFDriftSource().sample(seed=3, n_cycles=2), coupling_mode="independent")
    _raises_exact(
        ValueError,
        "the shared/off arm requires a coupling_mode='shared' timeline, got 'independent' "
        "(red-team R3)",
        lambda: t._fan_out(timeline, base_seed=0, trajectory=0))


@pytest.mark.parametrize("marker", ["baseline", "baseline_of", "ablation", "ablation_of"])
def test_L0_fan_out_rejects_each_baseline_marker(marker):
    """Each of the four rejected markers is checked (kills the marker-tuple string mutations):
    a shared-mode timeline carrying EXACTLY that marker must be refused with the exact message."""
    t = CoupledCycleTeacher(2)
    base = OneOverFDriftSource().sample(seed=3, n_cycles=2)
    timeline = dataclasses.replace(base, metadata={marker: True})
    _raises_exact(
        ValueError,
        f"timeline carries the {marker!r} marker; a permuted/baseline timeline is not a valid "
        "shared arm (red-team R3)",
        lambda: t._fan_out(timeline, base_seed=0, trajectory=0))


# =========================================================================== #
# L1 -- round-map THREE-WITNESS cross-validation                                #
# =========================================================================== #
def test_L1_round_map_three_witness_agreement():
    """THREE-WITNESS: the module's round map agrees with all three INDEPENDENT witnesses --
    (A) tick_index, (B) measurement-key round{r}: prefixes, (C) one barrier per round."""
    for rounds in (2, 3):
        sched = _sealed(rounds)
        module_map = derive_round_map_for_substep_schedule(sched, rounds=rounds)
        assert module_map == _indep_round_map(sched, rounds)             # (A)
        seen = set()
        for s in sched.substeps:
            for key in s.measurement_keys:
                m = _ROUND_RE.match(key)
                if m is not None:
                    r = int(m.group(1))
                    assert r == module_map[s.substep_id][0] == int(s.tick_index)   # (B)
                    seen.add(r)
                elif _FINAL_RE.match(key) is not None:
                    assert int(s.tick_index) == rounds
        assert seen == set(range(rounds))
        barrier_ticks = sorted(int(s.tick_index) for s in sched.substeps if s.kind == "barrier")
        assert barrier_ticks == list(range(rounds))                      # (C)


def test_KILLER_round_map_tick_witness_discriminates():
    sched = _sealed(3)
    real = derive_round_map_for_substep_schedule(sched, rounds=3)

    def prop(rm):
        assert rm == _indep_round_map(sched, 3)

    bad_key = next(k for k, v in real.items() if not v[1])
    wrong = dict(real)
    r, term = wrong[bad_key]
    wrong[bad_key] = ((r + 1) % 3, term)
    assert_discriminates(prop, real, wrong, label="round-map tick witness")


# =========================================================================== #
# L1 -- det/obs LAYOUT IDENTITY (schedule layout == code spec)                   #
# =========================================================================== #
def test_L1_layout_identity_schedule_matches_code_spec():
    t = CoupledCycleTeacher(2)
    assert len(t._detector_names) == t.rounds * t.n_stab
    assert len(t._observable_names) == 1
    assert list(t._observable_names) == ["logical_z2"]
    _circuit, manifest = t.export_stim_circuit()
    assert manifest["detector_names"] == list(t._detector_names) == t.truth["detector_names"]
    assert manifest["observable_names"] == list(t._observable_names) == t.truth["observable_names"]


def test_L1_layout_identity_4q_fixture():
    t = CoupledCycleTeacher(3, fixture="4q")
    assert t.n_stab == 1
    assert len(t._detector_names) == 3 * 1
    assert len(t._observable_names) == 1
