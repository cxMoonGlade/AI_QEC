"""Meta-tests: the shared test infrastructure defends itself (DEVIOUS-TEST STANDARD).

CPU-only (no GPU, no dataset). Every helper in ``tests/_support/fixtures.py`` and the
conftest mask hook is DEMONSTRATED to fail when it must -- an internal assert or probe
that has never fired is unproven. K-classes defended here: K-5 (self-comparison /
vacuity -- the double-negative killer on ``assert_control_trips`` and the sabotaged
CPTP stack), K-4 (the sabotage lands cleanly past the tolerance, not a hair above),
plus the AM-2 mask-hook vacuity killer (an unknown mask name must raise loudly).
"""

from __future__ import annotations

import numpy as np
import pytest

import conftest
from _support import fixtures
from _support.fixtures import (
    PRECONDITION_PREFIX,
    assert_control_trips,
    load_outputs_module,
    random_cptp_kraus,
    random_density_matrix,
    require_precondition,
)


# --------------------------------------------------------------------------- #
# (a) require_precondition -- the greppable prefix, verbatim                   #
# --------------------------------------------------------------------------- #
def test_require_precondition_raises_with_verbatim_prefix():
    with pytest.raises(AssertionError) as ei:
        require_precondition(False, "probe message", remedy="probe remedy")
    msg = str(ei.value)
    # the machine-greppable prefix, VERBATIM (contract C2)
    assert msg.startswith("PRECONDITION (class c, not a gate miss): "), msg
    assert PRECONDITION_PREFIX == "PRECONDITION (class c, not a gate miss): "
    assert "probe message" in msg and "remedy: probe remedy" in msg


def test_require_precondition_true_does_not_raise():
    require_precondition(True, "must not raise")  # default remedy path
    require_precondition(1 == 1, "must not raise", remedy="unused")


# --------------------------------------------------------------------------- #
# (b) assert_control_trips -- the double-negative KILLER                       #
# --------------------------------------------------------------------------- #
def _gate_check(value, tol):
    """A stand-in gate check: asserts |value| <= tol (raises AssertionError beyond)."""
    assert abs(value) <= tol, f"residual {value!r} above gate {tol!r}"


def test_assert_control_trips_passes_when_check_genuinely_fails():
    # broken input (1.0) violates the gate (1e-12) -> the check trips -> helper passes
    assert_control_trips(_gate_check, 1.0, 1.0e-12)


def test_assert_control_trips_raises_on_inert_control():
    """The double-negative KILLER: a check that does NOT trip on the broken input must
    make assert_control_trips itself raise (an inert control is a vacuous check)."""

    def inert_check(value, tol):  # noqa: ARG001 -- deliberately never asserts
        return True

    with pytest.raises(AssertionError, match="CONTROL INERT"):
        assert_control_trips(inert_check, 1.0, 1.0e-12)


def test_assert_control_trips_propagates_harness_crash():
    """A crashing harness is a bug, never a fired control: non-AssertionError
    exceptions must PROPAGATE, not count as a trip."""

    def crashing_check(value, tol):  # noqa: ARG001
        raise TypeError("harness bug")

    with pytest.raises(TypeError, match="harness bug"):
        assert_control_trips(crashing_check, 1.0, 1.0e-12)


# --------------------------------------------------------------------------- #
# (c) random builders -- the internal asserts are DEMONSTRATED to trip         #
# --------------------------------------------------------------------------- #
def test_random_cptp_kraus_numpy_is_cptp_and_shapes():
    rng = np.random.default_rng(7)
    stack = random_cptp_kraus(3, 3, rng, backend="numpy", stacked=True)
    assert stack.shape == (3, 3, 3) and stack.dtype == np.complex128
    gram = np.einsum("kij,kil->jl", stack.conj(), stack)
    assert float(np.abs(gram - np.eye(3)).max()) <= 1.0e-12
    lst = random_cptp_kraus(4, 2, np.random.default_rng(8), backend="numpy",
                            stacked=False)
    assert isinstance(lst, list) and len(lst) == 4 and lst[0].shape == (2, 2)


def test_random_cptp_kraus_internal_assert_trips_on_sabotaged_stack():
    """KILLER (K-5): the builder's internal CPTP check is fed a sabotaged stack (one
    Kraus scaled by 1.01 -> completeness residual ~2e-2, decisively past 1e-12, K-4)
    and DEMONSTRATED to trip."""
    rng = np.random.default_rng(11)
    stack = random_cptp_kraus(3, 3, rng, backend="numpy", stacked=True)
    bad = stack.copy()
    bad[0] = 1.01 * bad[0]
    with pytest.raises(AssertionError, match="CPTP"):
        fixtures._assert_cptp(bad, 1.0e-12)
    # and the clean stack passes the same internal check (the positive leg)
    fixtures._assert_cptp(stack, 1.0e-12)


def test_random_density_matrix_numpy_properties():
    rng = np.random.default_rng(23)
    rho = random_density_matrix(6, rng, backend="numpy")
    assert rho.shape == (6, 6)
    assert abs(np.trace(rho).real - 1.0) <= 1.0e-12
    assert float(np.abs(rho - rho.conj().T).max()) <= 1.0e-12
    assert float(np.linalg.eigvalsh(rho).min()) >= -1.0e-12  # PSD


def test_builders_torch_backend_shapes_cpu():
    """Torch-backend return-shape flags on CPU tensors (no GPU touched)."""
    torch = pytest.importorskip("torch")
    rng = np.random.default_rng(5)
    t = random_cptp_kraus(2, 3, rng, backend="torch", stacked=True)
    assert isinstance(t, torch.Tensor) and t.shape == (2, 3, 3)
    assert t.dtype == torch.complex128 and t.device.type == "cpu"
    lst = random_cptp_kraus(2, 3, np.random.default_rng(6), backend="torch",
                            stacked=False)
    assert isinstance(lst, list) and lst[0].shape == (3, 3)
    rho = random_density_matrix(4, np.random.default_rng(9), backend="torch")
    assert isinstance(rho, torch.Tensor) and rho.shape == (4, 4)


def test_builders_reject_unknown_backend_and_bad_args():
    rng = np.random.default_rng(1)
    with pytest.raises(ValueError, match="backend"):
        random_cptp_kraus(2, 3, rng, backend="tensorflow")
    with pytest.raises(ValueError, match="backend"):
        random_density_matrix(3, rng, backend="jax")
    with pytest.raises(AssertionError, match="PRECONDITION"):
        random_cptp_kraus(0, 3, rng, backend="numpy")


# --------------------------------------------------------------------------- #
# (d) the conftest mask hook defends itself (AM-2 vacuity killer)              #
# --------------------------------------------------------------------------- #
def test_d3_mask_unknown_name_raises_listing_valid_names():
    """A typo silently masking nothing would make the AM-2 probe vacuous -- an unknown
    logical name must raise ValueError listing the valid names."""
    with pytest.raises(ValueError, match="r01_circ"):
        conftest._has_data(mask="r10_meta,bogus_name")
    with pytest.raises(ValueError, match="bogus_name"):
        conftest._has_data(mask="bogus_name")


def test_d3_mask_env_var_unknown_name_raises(monkeypatch):
    """The env-var route (mask=None) validates too -- _has_data is a callable so this
    needs no module reimport (conftest design requirement)."""
    monkeypatch.setenv("QEC_TWIN_D3_MASK", "typo_name")
    with pytest.raises(ValueError, match="typo_name"):
        conftest._has_data()


def test_d3_mask_flips_predicate_per_name(monkeypatch):
    """Rule-II shape at the unit level: each masked name must flip the predicate to
    False (informative only where the full patch is present; otherwise the baseline is
    already False and the flip is unobservable -> precondition skip, not a failure)."""
    monkeypatch.delenv("QEC_TWIN_D3_MASK", raising=False)
    if not conftest._has_data(mask=()):
        pytest.skip("d3 patch absent here -- the mask flip is unobservable "
                    "(the committed probe runs this on the data box)")
    assert conftest._has_data(mask="") is True
    for name in conftest._D3_LOGICAL_NAMES:
        assert conftest._has_data(mask=(name,)) is False, name
    assert conftest._has_data(mask=",".join(conftest._D3_LOGICAL_NAMES)) is False


def test_canonical_markers_reflect_probes():
    """The skipif conditions carry the probes verbatim, and the canonical reason
    strings are EXACT (they ARE the migration target -- contract C1)."""
    assert conftest.requires_data.args[0] == (not conftest._HAS_DATA)
    assert conftest.requires_cuda.args[0] == (not conftest._HAS_CUDA)
    assert conftest.requires_cuda.kwargs["reason"] == \
        "GPU-only model compute (house rule: hard skip, never CPU fallback)"
    assert conftest.requires_data.kwargs["reason"] == \
        "shipped d3_at_q6_7 r01/r10 patch absent (all four files required)"


# --------------------------------------------------------------------------- #
# load_outputs_module                                                          #
# --------------------------------------------------------------------------- #
def test_load_outputs_module_missing_file_is_loud_precondition():
    with pytest.raises(AssertionError, match="PRECONDITION"):
        load_outputs_module("outputs/definitely_missing_zzz_probe.py")
