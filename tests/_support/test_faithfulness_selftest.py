"""Self-test for the faithfulness test-method API (tests/_support/faithfulness.py). The
discrimination helpers are load-bearing, so they carry their own teeth: assert_discriminates
must ACCEPT a real KILLER and REJECT a vacuous property; assert_pins must catch a mismatch;
the structural asserts must pass valid objects and fail broken ones."""
from __future__ import annotations

import numpy as np
import pytest

from _support import faithfulness as F


# --- assert_discriminates: the anti-vacuity core -------------------------------------- #
def test_assert_discriminates_accepts_a_real_killer():
    # property: "value is non-negative"; real=+1 satisfies, wrong=-1 violates -> discriminating
    prop = lambda x: (_ for _ in ()).throw(AssertionError("neg")) if x < 0 else None
    F.assert_discriminates(prop, real=1.0, wrong=-1.0, label="non-negativity")


def test_assert_discriminates_rejects_a_vacuous_property():
    # a property that ALWAYS passes (never asserts) is vacuous; the helper must flag it.
    always_ok = lambda x: None
    with pytest.raises(AssertionError, match="VACUOUS"):
        F.assert_discriminates(always_ok, real=1.0, wrong=-1.0, label="always-true")


def test_assert_discriminates_flags_property_wrong_for_real():
    # if the property does NOT hold for the correct object, that is a distinct loud failure.
    prop = lambda x: (_ for _ in ()).throw(AssertionError("always"))
    with pytest.raises(AssertionError, match="CORRECT object"):
        F.assert_discriminates(prop, real=1.0, wrong=-1.0, label="broken-prop")


# --- assert_pins: value pin vs independent reference ---------------------------------- #
def test_assert_pins_passes_on_match_and_fails_on_mismatch():
    F.assert_pins(0.75, 0.75, label="scalar")
    F.assert_pins({"a": 0.1, "b": 0.9}, {"a": 0.1, "b": 0.9}, label="dict")
    with pytest.raises(AssertionError, match="independent reference"):
        F.assert_pins(0.75, 0.50, label="scalar")
    with pytest.raises(AssertionError, match="key mismatch"):
        F.assert_pins({"a": 1.0}, {"b": 1.0}, label="dict")


# --- structural asserts: pass valid, fail broken -------------------------------------- #
def test_structural_cptp_and_unitary():
    # identity channel is CPTP; a scaled (non-TP) Kraus set is not.
    F.assert_cptp([np.eye(2)], label="identity")
    with pytest.raises(AssertionError, match="trace-preserving"):
        F.assert_cptp([0.5 * np.eye(2)], label="scaled")
    F.assert_unitary(np.array([[0, 1], [1, 0]], dtype=complex), label="X")
    with pytest.raises(AssertionError, match="unitary"):
        F.assert_unitary(np.array([[1, 1], [0, 1]], dtype=complex), label="shear")


def test_structural_density_and_prob():
    F.assert_density(F.bell_state(), label="bell")
    F.assert_density(F.maximally_mixed(2), label="I/2")
    with pytest.raises(AssertionError):
        F.assert_trace_one(2.0 * F.bell_state(), label="trace2")
    F.assert_prob_dist({"x": 0.3, "y": 0.7})
    with pytest.raises(AssertionError):
        F.assert_prob_dist({"x": 0.3, "y": 0.3})   # sums to 0.6


def test_builders_have_expected_entanglement_structure():
    # sanity: the shared builders are what they claim (used across batches).
    bell, prod = F.bell_state(), F.product_state(0, 0)
    F.assert_density(bell); F.assert_density(prod)
    # Bell is entangled (rank-1 pure, off-diagonal coherence), product is separable.
    assert abs(bell[0, 3] - 0.5) < 1e-12 and abs(prod[0, 3]) < 1e-12
    j = F.valid_joint_distribution([(0, 0), (0, 1), (1, 0), (1, 1)], seed=3)
    F.assert_prob_dist(j)
