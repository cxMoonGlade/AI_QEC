"""Stage-D batch ``axis1_context`` -- per-unit L0+L1+L2 coverage of
``error_coupling_simulator.frontend.axis1_context`` (10 CPU-pure public units: the frozen
dataclass ``Axis1LocalLindbladContextSpec`` -- its load-bearing ``__post_init__``, the
``is_trivial`` / ``include_leakage`` properties, ``to_manifest`` / ``to_metadata``, and the
load-bearing ``to_axis1_primitive_params`` fan-out -- plus the four module functions
``normalize_axis1_local_lindblad_context`` / ``axis1_local_lindblad_context_from_schedule`` /
``axis1_contextual_primitive_names`` / ``axis1_contextual_fsim_residual_primitives``; the
module imports NEITHER torch NOR quimb -- ``dataclasses`` + ``math`` + a sibling
``Axis1PrimitiveParams`` whose torch import is lazy/in-function -- so out_of_scope is empty).

Full-coverage program (docs/SIMULATOR.md SS12.3/12.4;
work-list docs/SIMULATOR.md D22).
``frontend/axis1_context.py`` owns the PUBLIC Axis-1 local-Markovian context: it selects +
parameterizes local-Lindblad primitive lowering before ``carrier.joint_lindbladian``
assembles the joint generator. It is NOT a runnable Pauli/Stim noise model, NOT Axis-2 source
truth, NOT a serialized channel payload.

L2 DISCIPLINE (100% coverage != discrimination). The schema + metadata-key strings are
HARDCODED here (deliberately NOT imported from src): a mutmut string mutation of a module
constant must make the module's manifest STOP matching the hardcoded literal -> the pin fails
-> the mutant is killed. ``epistemic_class='b'`` on the manifest pin makes the rate/leak/fsim
epistemic classes ``'b'`` -- distinct from the hardcoded ``'a'`` collapse/hamiltonian-form and
``'c'`` selection literals -- so any a/b/c literal swap is caught. Every raising guard is
tripped through EVERY public route reaching it with the EXACT message via ``assert_raises_exact``
(kills the string-wrap/case/None-message mutants a substring ``match=`` leaves surviving), and
each boolean/comparison guard is probed at its discriminating boundary (value==0 valid vs
negative raise; one operand true at a time). The ``is_trivial`` / ``include_leakage`` batteries
perturb ONE field at a time so every conjunct/disjunct short-circuit arc fires (100% branch) AND
every ``and``->``or`` / comparator mutant is killed.
"""
from __future__ import annotations

import math
import types

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_pins, assert_raises_exact

from error_coupling_simulator.frontend.axis1_context import (
    Axis1LocalLindbladContextSpec,
    axis1_contextual_fsim_residual_primitives,
    axis1_contextual_primitive_names,
    axis1_local_lindblad_context_from_schedule,
    normalize_axis1_local_lindblad_context,
)
from error_coupling_simulator.mechanisms.axis1_primitives import Axis1PrimitiveParams

# --------------------------------------------------------------------------- #
# INDEPENDENT hardcoded literals (deliberately NOT imported from the module):  #
# a mutmut mutation of the module's SCHEMA / KEY constant must make the         #
# module's output stop matching THIS literal -> the pin fails -> mutant killed. #
# --------------------------------------------------------------------------- #
_SCHEMA = "error_coupling_simulator.frontend.local_lindblad_context.v1"
_KEY = "axis1_local_lindblad_context"

# the nine leakage rate field names, in the module's is_trivial / include_leakage order.
_LEAK_FIELDS = (
    "leak_exchange_12_rad_per_ns",
    "leak_seep_21_per_ns",
    "leak_heat_12_per_ns",
    "leak_exchange_11_02_rad_per_ns",
    "leak_mobility_12_21_rad_per_ns",
    "leak_transport_30_12_rad_per_ns",
    "leak_transport_31_22_rad_per_ns",
    "leak_cond_phase_left2_right_z_rad_per_ns",
    "leak_cond_phase_left_z_right2_rad_per_ns",
)


# =========================================================================== #
# Axis1LocalLindbladContextSpec.__post_init__  --  coercion + validation        #
# =========================================================================== #
def test_L0_post_init_default_is_valid_and_coerces():
    # the all-default spec constructs (no raise): thermal False, fsim False, epistemic 'c',
    # optional rates None -> the ternary None-arc; gamma_up==0 passes _nonnegative_finite at
    # the boundary; schema is the hardcoded literal.
    s = Axis1LocalLindbladContextSpec()
    assert s.include_thermal_excitation is False and s.include_fsim_residual is False
    assert s.gamma_up_per_ns == 0.0 and s.epistemic_class == "c" and s.schema == _SCHEMA
    assert s.zeta_rad_per_ns is None and s.gamma_phi_per_ns is None
    # bool() coercion: a truthy non-bool becomes True (kills a removed bool()).
    s2 = Axis1LocalLindbladContextSpec(include_thermal_excitation=1, gamma_up_per_ns=0.5)
    assert s2.include_thermal_excitation is True
    # int rates coerced to float (kills a removed float() inside the guards).
    s3 = Axis1LocalLindbladContextSpec(gamma_up_per_ns=2, zeta_rad_per_ns=3, leak_seep_21_per_ns=4)
    assert type(s3.gamma_up_per_ns) is float and type(s3.zeta_rad_per_ns) is float
    assert type(s3.leak_seep_21_per_ns) is float
    retired_schema = "_".join(("qec", "twin")) + ".simulator.Axis1LocalLindbladContextSpec.v1"
    with pytest.raises(ValueError, match="unsupported local Lindblad context schema"):
        Axis1LocalLindbladContextSpec(schema=retired_schema)


def test_L0_post_init_thermal_guard_exact():
    # include_thermal_excitation with gamma_up==0.0 (the <= boundary) -> raise. Kills `<=`->`<`
    # (0<0 False -> no raise) and the thermal `and`->`or` in tandem with the valid cases below.
    assert_raises_exact(
        ValueError, "include_thermal_excitation requires gamma_up_per_ns > 0",
        lambda: Axis1LocalLindbladContextSpec(include_thermal_excitation=True, gamma_up_per_ns=0.0),
        label="thermal guard at gamma_up==0")
    # thermal True with gamma_up>0 is VALID (no raise): the True arm's non-raising route.
    ok = Axis1LocalLindbladContextSpec(include_thermal_excitation=True, gamma_up_per_ns=0.5)
    assert ok.include_thermal_excitation is True and ok.gamma_up_per_ns == 0.5
    # thermal False with gamma_up==0 is VALID (kills `and`->`or`: under `or`, gamma_up<=0 alone
    # would raise on the default spec) -- already exercised by the default spec above.
    assert Axis1LocalLindbladContextSpec(include_thermal_excitation=False, gamma_up_per_ns=0.0) is not None


def test_L0_post_init_fsim_residual_guard_exact():
    # include_fsim_residual with BOTH angles zero -> raise (kills `dtheta==0`->`!=` and the inner
    # `and`->`or` needs the one-angle cases below; the outer `and`->`or` is killed by the default
    # spec which has residual False + both angles zero and must NOT raise).
    assert_raises_exact(
        ValueError, "include_fsim_residual requires a nonzero fSim residual angle",
        lambda: Axis1LocalLindbladContextSpec(include_fsim_residual=True,
                                              fsim_delta_theta_rad=0.0, fsim_delta_phi_rad=0.0),
        label="fsim residual both-zero")
    # residual True with ONLY theta nonzero is VALID (inner `and`->`or` would raise here) ...
    a = Axis1LocalLindbladContextSpec(include_fsim_residual=True, fsim_delta_theta_rad=0.5)
    assert a.include_fsim_residual is True and a.fsim_delta_theta_rad == 0.5
    # ... and with ONLY phi nonzero is VALID.
    b = Axis1LocalLindbladContextSpec(include_fsim_residual=True, fsim_delta_phi_rad=0.5)
    assert b.fsim_delta_phi_rad == 0.5


def test_L0_post_init_epistemic_class_guard_exact():
    # each valid class accepted (kills a mutated set member) ...
    for cls in ("a", "b", "c"):
        assert Axis1LocalLindbladContextSpec(epistemic_class=cls).epistemic_class == cls
    # ... an invalid class -> exact ValueError with the offending repr.
    assert_raises_exact(
        ValueError, "epistemic_class must be one of 'a', 'b', 'c', got 'x'",
        lambda: Axis1LocalLindbladContextSpec(epistemic_class="x"),
        label="epistemic_class invalid")


def test_L0_post_init_nonnegative_finite_guard_exact():
    # value==0.0 is VALID (kills `< 0.0`->`<= 0.0`): a leak rate 0.0 constructs.
    assert Axis1LocalLindbladContextSpec(leak_seep_21_per_ns=0.0).leak_seep_21_per_ns == 0.0
    # a NEGATIVE rate -> exact message via the `out < 0.0` operand (the second `or` operand).
    assert_raises_exact(
        ValueError, "gamma_up_per_ns must be finite and non-negative, got -0.5",
        lambda: Axis1LocalLindbladContextSpec(gamma_up_per_ns=-0.5),
        label="gamma_up negative")
    # a non-finite rate -> the FIRST `or` operand (not math.isfinite); a leak field routes here.
    assert_raises_exact(
        ValueError, "leak_heat_12_per_ns must be finite and non-negative, got inf",
        lambda: Axis1LocalLindbladContextSpec(leak_heat_12_per_ns=float("inf")),
        label="leak_heat non-finite")
    # an OPTIONAL rate is guarded too (the ternary else-branch -> _nonnegative_finite).
    assert_raises_exact(
        ValueError, "zeta_rad_per_ns must be finite and non-negative, got -1.0",
        lambda: Axis1LocalLindbladContextSpec(zeta_rad_per_ns=-1.0),
        label="optional zeta negative")


def test_L0_post_init_finite_guard_exact():
    # _finite (fsim angles): a non-finite angle -> exact 'must be finite, got inf' (kills
    # `not math.isfinite`->`math.isfinite`). residual defaults False so the residual guard is
    # not reached -- this isolates _finite.
    assert_raises_exact(
        ValueError, "fsim_delta_theta_rad must be finite, got inf",
        lambda: Axis1LocalLindbladContextSpec(fsim_delta_theta_rad=float("inf")),
        label="fsim theta non-finite")
    assert_raises_exact(
        ValueError, "fsim_delta_phi_rad must be finite, got -inf",
        lambda: Axis1LocalLindbladContextSpec(fsim_delta_phi_rad=float("-inf")),
        label="fsim phi non-finite")


def test_L0_post_init_optional_rate_ternary_both_arcs():
    # None arc (default) -> stays None; value arc -> coerced float. Kills the `is None`->`is not
    # None` ternary (a set value would become None, and a None value would hit float(None)).
    s_none = Axis1LocalLindbladContextSpec()
    assert s_none.gamma_1_per_ns is None and s_none.gamma_readout_phi_per_ns is None
    s_set = Axis1LocalLindbladContextSpec(zeta_rad_per_ns=0.1, gamma_phi_per_ns=0.2,
                                          gamma_1_per_ns=0.3, gamma_readout_phi_per_ns=0.4)
    assert (s_set.zeta_rad_per_ns, s_set.gamma_phi_per_ns, s_set.gamma_1_per_ns,
            s_set.gamma_readout_phi_per_ns) == (0.1, 0.2, 0.3, 0.4)


# =========================================================================== #
# Axis1LocalLindbladContextSpec.is_trivial  (18-way `and`)                       #
# =========================================================================== #
# each entry: (kwargs producing a spec with exactly ONE trivial conjunct FALSE).
# Fields 1 (thermal) and 7 (fsim_residual) cannot be perturbed alone (their guards force a
# companion field), so they carry a companion; every OTHER conjunct is isolated.
_NONTRIVIAL_ONE_FIELD = [
    dict(include_thermal_excitation=True, gamma_up_per_ns=0.5),  # conjunct 1 (+2)
    dict(gamma_up_per_ns=0.5),                                   # conjunct 2
    dict(zeta_rad_per_ns=0.5),                                   # conjunct 3
    dict(gamma_phi_per_ns=0.5),                                  # conjunct 4
    dict(gamma_1_per_ns=0.5),                                    # conjunct 5
    dict(gamma_readout_phi_per_ns=0.5),                          # conjunct 6
    dict(include_fsim_residual=True, fsim_delta_theta_rad=0.5),  # conjunct 7 (+8)
    dict(fsim_delta_theta_rad=0.5),                              # conjunct 8
    dict(fsim_delta_phi_rad=0.5),                                # conjunct 9
] + [dict([(name, 0.5)]) for name in _LEAK_FIELDS]              # conjuncts 10..18


def test_L0_is_trivial_true_on_default():
    assert Axis1LocalLindbladContextSpec().is_trivial is True


@pytest.mark.parametrize("kwargs", _NONTRIVIAL_ONE_FIELD)
def test_L0_is_trivial_false_per_conjunct(kwargs):
    # exactly one conjunct is FALSE -> is_trivial False, and (because the earlier conjuncts are
    # all True) THIS conjunct's short-circuit arc fires -> 100% branch of is_trivial.
    assert Axis1LocalLindbladContextSpec(**kwargs).is_trivial is False


def test_L0_is_trivial_discriminates_and_to_or():
    # the gamma_up-only-nontrivial spec's single False conjunct sits in the mutated prefix, so
    # EVERY `and`->`or` mutant flips is_trivial to True here -> the False pin kills it.
    trivial = Axis1LocalLindbladContextSpec()
    nontrivial = Axis1LocalLindbladContextSpec(gamma_up_per_ns=0.5)

    def prop(spec):
        assert spec.is_trivial is False

    assert_discriminates(prop, nontrivial, trivial, label="is_trivial discriminates")


# =========================================================================== #
# Axis1LocalLindbladContextSpec.include_leakage  (9-way `or`)                    #
# =========================================================================== #
def test_L0_include_leakage_false_on_no_leak():
    # no leak rate set (default) -> False; ALSO kills every `>`->`>=` mutant (0.0>=0.0 True
    # would flip this to True) and gives each disjunct's False->continue arc.
    assert Axis1LocalLindbladContextSpec().is_trivial is True
    assert Axis1LocalLindbladContextSpec().include_leakage is False
    # a NON-leak field being nontrivial does not turn on leakage.
    assert Axis1LocalLindbladContextSpec(gamma_up_per_ns=0.5).include_leakage is False


@pytest.mark.parametrize("name", _LEAK_FIELDS)
def test_L0_include_leakage_true_per_leak(name):
    # each leak rate individually > 0 -> True, and (earlier disjuncts False) THIS disjunct's
    # short-circuit arc fires -> 100% branch of include_leakage.
    assert Axis1LocalLindbladContextSpec(**{name: 0.5}).include_leakage is True


def test_L0_include_leakage_discriminates_or_to_and():
    # a single-leak spec: its one True disjunct sits in the mutated prefix, so EVERY `or`->`and`
    # mutant flips include_leakage to False -> the True pin kills it.
    on = Axis1LocalLindbladContextSpec(leak_exchange_12_rad_per_ns=0.5)
    off = Axis1LocalLindbladContextSpec()

    def prop(spec):
        assert spec.include_leakage is True

    assert_discriminates(prop, on, off, label="include_leakage discriminates")


# =========================================================================== #
# Axis1LocalLindbladContextSpec.to_manifest  (exact JSON-safe dict)             #
# =========================================================================== #
def _rich_spec() -> Axis1LocalLindbladContextSpec:
    """A spec with a DISTINCT value in every field (so key<->value misp-mapping is caught) and
    epistemic_class='b' (so the manifest's rate/leak/fsim classes 'b' are distinct from the
    hardcoded 'a'/'c' literals)."""
    return Axis1LocalLindbladContextSpec(
        include_thermal_excitation=True, gamma_up_per_ns=0.7,
        zeta_rad_per_ns=0.11, gamma_phi_per_ns=0.22, gamma_1_per_ns=0.33,
        gamma_readout_phi_per_ns=0.44,
        include_fsim_residual=True, fsim_delta_theta_rad=0.55, fsim_delta_phi_rad=0.66,
        leak_exchange_12_rad_per_ns=1.1, leak_seep_21_per_ns=1.2, leak_heat_12_per_ns=1.3,
        leak_exchange_11_02_rad_per_ns=1.4, leak_mobility_12_21_rad_per_ns=1.5,
        leak_transport_30_12_rad_per_ns=1.6, leak_transport_31_22_rad_per_ns=1.7,
        leak_cond_phase_left2_right_z_rad_per_ns=1.8, leak_cond_phase_left_z_right2_rad_per_ns=1.9,
        epistemic_class="b")


def _expected_rich_manifest() -> dict:
    """INDEPENDENT hand-built manifest literal for _rich_spec (hardcoded schema/key + the a/b/c
    epistemic map from the contract text, NOT read off the module)."""
    return {
        "schema": _SCHEMA,
        "metadata_key": _KEY,
        "include_thermal_excitation": True,
        "gamma_up_per_ns": 0.7,
        "zeta_rad_per_ns": 0.11,
        "gamma_phi_per_ns": 0.22,
        "gamma_1_per_ns": 0.33,
        "gamma_readout_phi_per_ns": 0.44,
        "include_fsim_residual": True,
        "fsim_delta_theta_rad": 0.55,
        "fsim_delta_phi_rad": 0.66,
        "include_leakage": True,
        "leak_exchange_12_rad_per_ns": 1.1,
        "leak_seep_21_per_ns": 1.2,
        "leak_heat_12_per_ns": 1.3,
        "leak_exchange_11_02_rad_per_ns": 1.4,
        "leak_mobility_12_21_rad_per_ns": 1.5,
        "leak_transport_30_12_rad_per_ns": 1.6,
        "leak_transport_31_22_rad_per_ns": 1.7,
        "leak_cond_phase_left2_right_z_rad_per_ns": 1.8,
        "leak_cond_phase_left_z_right2_rad_per_ns": 1.9,
        "contains_operator_payload": False,
        "contains_serialized_channel_payload": False,
        "visibility": "public_axis1_markovian_context_not_evaluator_truth",
        "representability":
            "public_axis1_lindblad_parameter_metadata_no_operator_matrices_no_source",
        "epistemic_class": "b",
        "epistemic_classes": {
            "sigma_plus_collapse_form": "a",
            "fsim_residual_hamiltonian_form": "a",
            "rate_values": "b",
            "thermal_excitation_selection": "c",
            "fsim_residual_angles": "b",
            "leak_exchange_12_rad_per_ns": "b",
            "leak_seep_21_per_ns": "b",
            "leak_heat_12_per_ns": "b",
            "leak_exchange_11_02_rad_per_ns": "b",
            "leak_mobility_12_21_rad_per_ns": "b",
            "leak_transport_30_12_rad_per_ns": "b",
            "leak_transport_31_22_rad_per_ns": "b",
            "leak_cond_phase_left2_right_z_rad_per_ns": "b",
            "leak_cond_phase_left_z_right2_rad_per_ns": "b",
            "leakage_selection": "c",
        },
    }


def test_L0_to_manifest_exact_dict():
    got = _rich_spec().to_manifest()
    expected = _expected_rich_manifest()
    assert got == expected
    # include_leakage recomputed True in the manifest (leaks > 0); a JSON-safe bool.
    assert got["include_leakage"] is True and type(got["gamma_up_per_ns"]) is float

    def prop(m):
        assert m == expected

    wrong = dict(expected, gamma_1_per_ns=99.0)  # a single field drift must fail
    assert_discriminates(prop, got, wrong, label="to_manifest exact")


def test_L0_to_manifest_trivial_include_leakage_false():
    # a spec with NO leak has include_leakage False in the manifest (the other manifest arc).
    m = Axis1LocalLindbladContextSpec(gamma_phi_per_ns=0.2).to_manifest()
    assert m["include_leakage"] is False and m["epistemic_class"] == "c"
    assert m["epistemic_classes"]["rate_values"] == "c"


# =========================================================================== #
# Axis1LocalLindbladContextSpec.to_metadata                                     #
# =========================================================================== #
def test_L0_to_metadata_trivial_is_empty():
    assert Axis1LocalLindbladContextSpec().to_metadata() == {}


def test_L0_to_metadata_nontrivial_wraps_manifest_under_key():
    spec = _rich_spec()
    md = spec.to_metadata()
    # the metadata key is the hardcoded literal (kills a mutated KEY constant) ...
    assert set(md) == {_KEY}
    # ... and its value is the exact manifest.
    assert md[_KEY] == _expected_rich_manifest()

    def prop(m):
        assert set(m) == {_KEY}

    assert_discriminates(prop, md, {}, label="to_metadata nontrivial wraps")


# =========================================================================== #
# Axis1LocalLindbladContextSpec.to_axis1_primitive_params  (the fan-out)         #
# =========================================================================== #
def _defaults() -> Axis1PrimitiveParams:
    """Defaults with values DISTINCT from any spec value, so 'took defaults' vs 'took spec' is
    discriminated field-by-field."""
    return Axis1PrimitiveParams(
        zeta_rad_per_ns=1.0, gamma_phi_per_ns=2.0, gamma_1_per_ns=3.0, gamma_up_per_ns=9.0,
        gamma_readout_phi_per_ns=4.0, drive_area_rad=math.pi, drive_omega_rad_per_ns=5.0,
        fsim_delta_theta_rad=9.9, fsim_delta_phi_rad=8.8)


def _params_fields(p: Axis1PrimitiveParams) -> dict:
    return {
        "zeta_rad_per_ns": p.zeta_rad_per_ns,
        "gamma_phi_per_ns": p.gamma_phi_per_ns,
        "gamma_1_per_ns": p.gamma_1_per_ns,
        "gamma_up_per_ns": p.gamma_up_per_ns,
        "gamma_readout_phi_per_ns": p.gamma_readout_phi_per_ns,
        "drive_area_rad": p.drive_area_rad,
        "drive_omega_rad_per_ns": p.drive_omega_rad_per_ns,
        "fsim_delta_theta_rad": p.fsim_delta_theta_rad,
        "fsim_delta_phi_rad": p.fsim_delta_phi_rad,
    }


def test_L0_to_axis1_primitive_params_none_rates_take_defaults():
    d = _defaults()
    # all optional rates None -> take DEFAULTS; gamma_up + fsim angles always from the spec;
    # drive_area/drive_omega always from defaults.
    spec = Axis1LocalLindbladContextSpec(gamma_up_per_ns=0.5, include_fsim_residual=True,
                                         fsim_delta_theta_rad=0.6, fsim_delta_phi_rad=0.7)
    out = spec.to_axis1_primitive_params(d)
    expected = {
        "zeta_rad_per_ns": 1.0, "gamma_phi_per_ns": 2.0, "gamma_1_per_ns": 3.0,
        "gamma_up_per_ns": 0.5, "gamma_readout_phi_per_ns": 4.0, "drive_area_rad": math.pi,
        "drive_omega_rad_per_ns": 5.0, "fsim_delta_theta_rad": 0.6, "fsim_delta_phi_rad": 0.7,
    }
    assert_pins(_params_fields(out), expected, label="params fan-out (None->defaults)")


def test_L0_to_axis1_primitive_params_set_rates_take_spec():
    d = _defaults()
    # all optional rates SET -> take the SPEC values (kills the `is None`->`is not None` ternary,
    # which would take defaults instead).
    spec = Axis1LocalLindbladContextSpec(
        zeta_rad_per_ns=0.11, gamma_phi_per_ns=0.22, gamma_1_per_ns=0.33,
        gamma_readout_phi_per_ns=0.44, gamma_up_per_ns=0.55,
        include_fsim_residual=True, fsim_delta_theta_rad=0.66, fsim_delta_phi_rad=0.77)
    out = spec.to_axis1_primitive_params(d)
    expected = {
        "zeta_rad_per_ns": 0.11, "gamma_phi_per_ns": 0.22, "gamma_1_per_ns": 0.33,
        "gamma_up_per_ns": 0.55, "gamma_readout_phi_per_ns": 0.44, "drive_area_rad": math.pi,
        "drive_omega_rad_per_ns": 5.0, "fsim_delta_theta_rad": 0.66, "fsim_delta_phi_rad": 0.77,
    }
    assert_pins(_params_fields(out), expected, label="params fan-out (set->spec)")

    def prop(p):
        assert _params_fields(p) == expected

    # a wrong-coefficient variant (gamma_up off) must fail the pin -> teeth.
    wrong = Axis1PrimitiveParams(
        zeta_rad_per_ns=0.11, gamma_phi_per_ns=0.22, gamma_1_per_ns=0.33,
        gamma_up_per_ns=123.0, gamma_readout_phi_per_ns=0.44, drive_area_rad=math.pi,
        drive_omega_rad_per_ns=5.0, fsim_delta_theta_rad=0.66, fsim_delta_phi_rad=0.77)
    assert_discriminates(prop, out, wrong, label="params fan-out discriminates")


# =========================================================================== #
# normalize_axis1_local_lindblad_context                                        #
# =========================================================================== #
def test_L0_normalize_empty_inputs_return_default_spec():
    default = Axis1LocalLindbladContextSpec()
    assert normalize_axis1_local_lindblad_context(None) == default
    assert normalize_axis1_local_lindblad_context({}) == default
    assert normalize_axis1_local_lindblad_context(()) == default


def test_L0_normalize_spec_returned_by_identity():
    spec = _rich_spec()
    assert normalize_axis1_local_lindblad_context(spec) is spec


def test_L0_normalize_non_dict_raises_exact():
    # a non-dict non-spec (int) -> exact ValueError (first route past the empty-input + spec arms)
    assert_raises_exact(
        ValueError,
        "axis1_local_lindblad_context must be a dict or Axis1LocalLindbladContextSpec",
        lambda: normalize_axis1_local_lindblad_context(5),
        label="normalize int")
    # a str is ALSO not a dict -> same exact message (a str is iterable but still rejected).
    assert_raises_exact(
        ValueError,
        "axis1_local_lindblad_context must be a dict or Axis1LocalLindbladContextSpec",
        lambda: normalize_axis1_local_lindblad_context("nope"),
        label="normalize str")


def test_L0_normalize_manifest_roundtrips_to_equal_spec():
    # the FULL to_manifest() dict (carrying metadata_key/contains_*/visibility/representability/
    # epistemic_classes/include_leakage -- all NON-field keys) round-trips to an EQUAL spec. If
    # ANY of the seven payload.pop key strings is mutated, the stray key survives -> **payload
    # TypeError -> mutant killed. This is the reachability probe for all seven pops.
    spec = _rich_spec()
    assert normalize_axis1_local_lindblad_context(spec.to_manifest()) == spec
    # a plain dict of field values reconstructs the same spec (constructs past line 267).
    got = normalize_axis1_local_lindblad_context({"gamma_up_per_ns": 0.5, "epistemic_class": "a"})
    assert got == Axis1LocalLindbladContextSpec(gamma_up_per_ns=0.5, epistemic_class="a")


def test_L0_normalize_schema_guard_exact():
    # an UNSUPPORTED schema -> exact ValueError (kills `!=`->`==` in one direction + the get-key
    # mutant, which would fall back to the default schema and NOT raise).
    assert_raises_exact(
        ValueError, "unsupported Axis-1 local Lindblad context schema 'bogus.v0'",
        lambda: normalize_axis1_local_lindblad_context({"schema": "bogus.v0"}),
        label="normalize bad schema")
    # the CORRECT schema present -> constructs (kills `!=`->`==` the other direction).
    assert normalize_axis1_local_lindblad_context(
        {"schema": _SCHEMA, "gamma_up_per_ns": 0.5}) == Axis1LocalLindbladContextSpec(
        gamma_up_per_ns=0.5)


def test_L0_normalize_field_values_constructed():
    # a dict with real field values builds a spec carrying them (not the default).
    got = normalize_axis1_local_lindblad_context(
        {"zeta_rad_per_ns": 0.25, "leak_seep_21_per_ns": 0.5})
    assert got.zeta_rad_per_ns == 0.25 and got.leak_seep_21_per_ns == 0.5
    assert got.include_leakage is True

    def prop(s):
        assert s.zeta_rad_per_ns == 0.25

    assert_discriminates(prop, got, Axis1LocalLindbladContextSpec(), label="normalize field values")


# =========================================================================== #
# axis1_local_lindblad_context_from_schedule                                    #
# =========================================================================== #
def test_L0_from_schedule_with_dict_attribute():
    # a schedule carrying the attribute as a dict -> the normalized spec (kills the getattr
    # attr-name mutant: a wrong name would miss the attr -> default spec instead).
    sched = types.SimpleNamespace(axis1_local_lindblad_context={"gamma_up_per_ns": 0.5})
    got = axis1_local_lindblad_context_from_schedule(sched)
    assert got == Axis1LocalLindbladContextSpec(gamma_up_per_ns=0.5)

    def prop(s):
        assert s.gamma_up_per_ns == 0.5

    assert_discriminates(prop, got, Axis1LocalLindbladContextSpec(), label="from_schedule dict")


def test_L0_from_schedule_with_spec_attribute():
    spec = _rich_spec()
    sched = types.SimpleNamespace(axis1_local_lindblad_context=spec)
    assert axis1_local_lindblad_context_from_schedule(sched) is spec


def test_L0_from_schedule_missing_attribute_defaults():
    # a schedule WITHOUT the attribute -> getattr default {} -> default spec (the default-branch).
    sched = types.SimpleNamespace()
    assert axis1_local_lindblad_context_from_schedule(sched) == Axis1LocalLindbladContextSpec()


# =========================================================================== #
# axis1_contextual_primitive_names                                             #
# =========================================================================== #
_TRIVIAL_CTX = Axis1LocalLindbladContextSpec()
_THERMAL_CTX = Axis1LocalLindbladContextSpec(include_thermal_excitation=True, gamma_up_per_ns=0.5)


def test_L0_contextual_names_non_thermal_returns_upper_verbatim():
    # non-thermal -> names upper-cased + returned verbatim (no T1_UP expansion). Kills the
    # `.upper()` removal (lower input) AND the `not include_thermal_excitation` route-removal (a
    # T1 name would gain T1_UP under the mutant's expansion loop).
    assert axis1_contextual_primitive_names(("t1", "zz"), _TRIVIAL_CTX) == ("T1", "ZZ")
    assert axis1_contextual_primitive_names(("T1",), _TRIVIAL_CTX) == ("T1",)
    assert axis1_contextual_primitive_names((), _TRIVIAL_CTX) == ()


def test_L0_contextual_names_thermal_expands_t1():
    # thermal -> T1 gains T1_UP; a lower-case 't1' still matches after .upper().
    assert axis1_contextual_primitive_names(("T1",), _THERMAL_CTX) == ("T1", "T1_UP")
    assert axis1_contextual_primitive_names(("t1",), _THERMAL_CTX) == ("T1", "T1_UP")
    # T1_B gains T1_UP_B.
    assert axis1_contextual_primitive_names(("T1_B",), _THERMAL_CTX) == ("T1_B", "T1_UP_B")


def test_L0_contextual_names_thermal_no_dup_when_up_present_in_input():
    # T1_UP already in the INPUT names -> not duplicated (kills `"T1_UP" not in names`->`in`).
    assert axis1_contextual_primitive_names(("T1", "T1_UP"), _THERMAL_CTX) == ("T1", "T1_UP")
    assert axis1_contextual_primitive_names(("T1_B", "T1_UP_B"), _THERMAL_CTX) == (
        "T1_B", "T1_UP_B")


def test_L0_contextual_names_thermal_no_dup_when_up_already_appended():
    # T1 appears TWICE -> T1_UP appended once (kills `"T1_UP" not in out`->`in out`).
    assert axis1_contextual_primitive_names(("T1", "T1"), _THERMAL_CTX) == ("T1", "T1_UP", "T1")
    assert axis1_contextual_primitive_names(("T1_B", "T1_B"), _THERMAL_CTX) == (
        "T1_B", "T1_UP_B", "T1_B")


def test_L0_contextual_names_thermal_non_t1_not_expanded():
    # a non-T1 name under thermal is NOT given a _UP (kills the two inner `and`->`or` mutants:
    # under `or`, a non-T1 name whose T1_UP-absence conditions are True would spuriously expand).
    assert axis1_contextual_primitive_names(("ZZ",), _THERMAL_CTX) == ("ZZ",)
    assert axis1_contextual_primitive_names(("ZZ", "T1"), _THERMAL_CTX) == ("ZZ", "T1", "T1_UP")

    def prop(names_out):
        assert names_out == ("ZZ",)

    assert_discriminates(
        prop, axis1_contextual_primitive_names(("ZZ",), _THERMAL_CTX),
        axis1_contextual_primitive_names(("T1",), _THERMAL_CTX), label="non-T1 not expanded")


# =========================================================================== #
# axis1_contextual_fsim_residual_primitives                                     #
# =========================================================================== #
def test_L0_fsim_residual_off_returns_empty():
    # residual off -> (); ALSO residual off WITH a nonzero angle -> () (kills the `not
    # include_fsim_residual` removal: under the mutant the angle check would emit FSIM_SWAP).
    assert axis1_contextual_fsim_residual_primitives(Axis1LocalLindbladContextSpec()) == ()
    off_with_angle = Axis1LocalLindbladContextSpec(fsim_delta_theta_rad=0.5)
    assert axis1_contextual_fsim_residual_primitives(off_with_angle) == ()


def test_L0_fsim_residual_on_selects_by_angle():
    # theta-only -> FSIM_SWAP; phi-only -> FSIM_PHASE; both -> both (kills `!=`->`==` on each).
    theta = Axis1LocalLindbladContextSpec(include_fsim_residual=True, fsim_delta_theta_rad=0.5)
    assert axis1_contextual_fsim_residual_primitives(theta) == ("FSIM_SWAP",)
    phi = Axis1LocalLindbladContextSpec(include_fsim_residual=True, fsim_delta_phi_rad=0.5)
    assert axis1_contextual_fsim_residual_primitives(phi) == ("FSIM_PHASE",)
    both = Axis1LocalLindbladContextSpec(include_fsim_residual=True,
                                         fsim_delta_theta_rad=0.5, fsim_delta_phi_rad=0.5)
    assert axis1_contextual_fsim_residual_primitives(both) == ("FSIM_SWAP", "FSIM_PHASE")

    def prop(out):
        assert out == ("FSIM_SWAP",)

    assert_discriminates(
        prop, axis1_contextual_fsim_residual_primitives(theta),
        axis1_contextual_fsim_residual_primitives(both), label="fsim residual selects by angle")


# =========================================================================== #
# L1 PROPERTY (Hypothesis)                                                       #
# =========================================================================== #
@settings(max_examples=200, deadline=None)
@given(leaks=st.lists(st.floats(min_value=0.0, max_value=5.0, allow_nan=False,
                                allow_infinity=False), min_size=9, max_size=9))
def test_L1_include_leakage_iff_any_leak_positive(leaks):
    spec = Axis1LocalLindbladContextSpec(**{n: v for n, v in zip(_LEAK_FIELDS, leaks)})
    # INDEPENDENT recompute: leakage iff ANY leak rate strictly positive.
    assert spec.include_leakage == any(v > 0.0 for v in leaks)


@settings(max_examples=200, deadline=None)
@given(
    zeta=st.one_of(st.none(), st.floats(0.0, 5.0, allow_nan=False, allow_infinity=False)),
    gphi=st.one_of(st.none(), st.floats(0.0, 5.0, allow_nan=False, allow_infinity=False)),
    g1=st.one_of(st.none(), st.floats(0.0, 5.0, allow_nan=False, allow_infinity=False)),
    grd=st.one_of(st.none(), st.floats(0.0, 5.0, allow_nan=False, allow_infinity=False)),
    gup=st.floats(0.0, 5.0, allow_nan=False, allow_infinity=False))
def test_L1_to_axis1_primitive_params_fanout_selects(zeta, gphi, g1, grd, gup):
    d = _defaults()
    spec = Axis1LocalLindbladContextSpec(
        zeta_rad_per_ns=zeta, gamma_phi_per_ns=gphi, gamma_1_per_ns=g1,
        gamma_readout_phi_per_ns=grd, gamma_up_per_ns=gup)
    out = spec.to_axis1_primitive_params(d)
    # INDEPENDENT recompute of the fan-out rule (None -> defaults else spec).
    assert out.zeta_rad_per_ns == (d.zeta_rad_per_ns if zeta is None else zeta)
    assert out.gamma_phi_per_ns == (d.gamma_phi_per_ns if gphi is None else gphi)
    assert out.gamma_1_per_ns == (d.gamma_1_per_ns if g1 is None else g1)
    assert out.gamma_readout_phi_per_ns == (
        d.gamma_readout_phi_per_ns if grd is None else grd)
    assert out.gamma_up_per_ns == gup                       # always from spec
    assert out.drive_area_rad == d.drive_area_rad           # always from defaults
    assert out.drive_omega_rad_per_ns == d.drive_omega_rad_per_ns


@settings(max_examples=150, deadline=None)
@given(
    gup=st.floats(0.0, 5.0, allow_nan=False, allow_infinity=False),
    leaks=st.lists(st.floats(0.0, 5.0, allow_nan=False, allow_infinity=False),
                   min_size=9, max_size=9),
    cls=st.sampled_from(["a", "b", "c"]))
def test_L1_normalize_manifest_roundtrip(gup, leaks, cls):
    spec = Axis1LocalLindbladContextSpec(
        gamma_up_per_ns=gup, epistemic_class=cls,
        **{n: v for n, v in zip(_LEAK_FIELDS, leaks)})
    # a full manifest round-trips to an EQUAL spec; a spec passes through by identity.
    assert normalize_axis1_local_lindblad_context(spec.to_manifest()) == spec
    assert normalize_axis1_local_lindblad_context(spec) is spec
    # to_metadata is {} iff trivial (INDEPENDENT recompute via is_trivial).
    assert (spec.to_metadata() == {}) == spec.is_trivial
