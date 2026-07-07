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
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import conftest
from _support import fixtures
from _support.fixtures import (
    EVIL_MARGINAL_PREFIX,
    PRECONDITION_PREFIX,
    assert_control_trips,
    assert_with_margin,
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
# (b2) assert_with_margin -- the Side-B margin discipline defends itself       #
#      (two-sided extension (i): all three outcomes DEMONSTRATED)              #
# --------------------------------------------------------------------------- #
def test_assert_with_margin_passes_with_wide_margin():
    """Wide pass (both directions): returns the measured margin factor. Operands are
    binary-exact powers of two so the pinned ratios are EXACT (1e-12/1e-15 is
    999.9999999999999 in doubles -- measured 2026-07-07 -- exactly the K-4 float
    knife-edge this helper exists to police; never pin decimal ratios)."""
    assert assert_with_margin(2.0**-40, 2.0**-30, mode="le",
                              what="probe residual") == 2.0**10
    assert assert_with_margin(1024.0, 1.0, mode="ge", what="probe score") == 1024.0
    # value exactly 0 under a positive tolerance: infinite margin, passes (le, v<=0).
    assert assert_with_margin(0.0, 1.0e-12, mode="le",
                              what="structural zero") == float("inf")
    # ge with a non-positive threshold: documented INFINITE margin (t<=0 branch), passes.
    assert assert_with_margin(1.0, 0.0, mode="ge",
                              what="ge zero-threshold") == float("inf")
    assert assert_with_margin(1.0, -1.0, mode="ge",
                              what="ge negative-threshold") == float("inf")


def test_assert_with_margin_fails_on_violation_without_evil_prefix():
    """Genuine gate miss: plain AssertionError, greppably DISTINCT from the
    EVIL-MARGINAL class (no prefix -- triage must never conflate the two)."""
    with pytest.raises(AssertionError) as ei:
        assert_with_margin(1.0, 1.0e-12, mode="le", what="probe residual")
    msg = str(ei.value)
    assert "FAILS threshold" in msg and not msg.startswith(EVIL_MARGINAL_PREFIX)
    with pytest.raises(AssertionError) as ei2:
        assert_with_margin(0.5, 1.0, mode="ge", what="probe score")
    assert not str(ei2.value).startswith(EVIL_MARGINAL_PREFIX)


def test_assert_with_margin_evil_marginal_on_knife_edge_pass():
    """KILLER (K-4, the 1.181e-12-vs-1e-12 lesson made structural): a pass within
    min_margin of the gate raises with the VERBATIM greppable prefix, NAMING the
    measured margin factor (5e-13 vs 1e-12 -> margin exactly 2, binary-exact)."""
    with pytest.raises(AssertionError) as ei:
        assert_with_margin(5.0e-13, 1.0e-12, mode="le", what="knife-edge residual")
    msg = str(ei.value)
    assert msg.startswith("EVIL-MARGINAL (class c): "), msg
    assert EVIL_MARGINAL_PREFIX == "EVIL-MARGINAL (class c): "
    assert "margin factor 2" in msg and "knife-edge residual" in msg
    # the ge direction is symmetric (margin 2 < 10).
    with pytest.raises(AssertionError, match="EVIL-MARGINAL"):
        assert_with_margin(2.0, 1.0, mode="ge", what="knife-edge score")


def test_assert_with_margin_boundary_margin_passes():
    """margin == min_margin PASSES (the marginal gate is strict '<'); binary-exact
    10x operands (0.0625 / 0.625) so this is not itself a knife-edge float case."""
    assert assert_with_margin(0.0625, 0.625, mode="le", what="boundary") == 10.0
    assert assert_with_margin(0.625, 0.0625, mode="ge", what="boundary") == 10.0


def test_assert_with_margin_rejects_bad_mode_and_nan():
    """Harness misuse fails loud: unknown mode -> ValueError; NaN NEVER passes
    (K-7 -- a NaN-swallowed comparison would otherwise 'pass' nothing silently)."""
    with pytest.raises(ValueError, match="mode"):
        assert_with_margin(0.0, 1.0, mode="lt", what="probe")
    # every mode x NaN-position branch: NaN never passes a gate (K-7). The NaN guard
    # runs BEFORE the direction check, so all four (mode in {le,ge}) x (value / threshold
    # is NaN) combinations must raise the same loud AssertionError.
    with pytest.raises(AssertionError, match="NaN"):
        assert_with_margin(float("nan"), 1.0, mode="le", what="probe")  # le, value NaN
    with pytest.raises(AssertionError, match="NaN"):
        assert_with_margin(1.0, float("nan"), mode="le", what="probe")  # le, thresh NaN
    with pytest.raises(AssertionError, match="NaN"):
        assert_with_margin(float("nan"), 1.0, mode="ge", what="probe")  # ge, value NaN
    with pytest.raises(AssertionError, match="NaN"):
        assert_with_margin(0.0, float("nan"), mode="ge", what="probe")  # ge, thresh NaN
    # both operands NaN also fails (no silent swallow)
    with pytest.raises(AssertionError, match="NaN"):
        assert_with_margin(float("nan"), float("nan"), mode="le", what="probe")


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


def test_random_density_matrix_internal_assert_trips_on_sabotaged_rho():
    """KILLER (K-5, the NEW meta-test): the builder's extracted internal density check
    (_assert_density) is fed sabotaged matrices -- one violating unit trace (scaled by
    1.5 -> tr=1.5, decisively past 1e-12, K-4), one violating hermiticity (a single
    off-diagonal perturbed by 0.5) -- and DEMONSTRATED to trip on each. The clean rho
    passes the same internal check (the positive leg). Extracting the inline asserts
    into _assert_density is behaviour-identical: the meta-test proves the seam still
    fires, guarding the structurally-unreachable defensive branch."""
    rng = np.random.default_rng(29)
    rho = random_density_matrix(5, rng, backend="numpy")
    # the clean rho passes the extracted internal check (positive leg)
    fixtures._assert_density(rho, 1.0e-12)
    # sabotage 1: trace violated (raw scaling breaks unit trace) -> trace check trips
    bad_trace = 1.5 * rho
    with pytest.raises(AssertionError, match="trace check tripped"):
        fixtures._assert_density(bad_trace, 1.0e-12)
    # sabotage 2: hermiticity violated (asymmetric off-diagonal), trace kept ~1 so the
    # hermiticity branch is the one that must fire (not shadowed by the trace branch).
    bad_herm = rho.copy()
    bad_herm[0, 1] = bad_herm[0, 1] + 0.5  # tr unchanged; rho no longer Hermitian
    with pytest.raises(AssertionError, match="hermiticity check tripped"):
        fixtures._assert_density(bad_herm, 1.0e-12)


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
    with pytest.raises(AssertionError, match="PRECONDITION"):
        random_density_matrix(1, rng, backend="numpy")  # dim>=2 precondition
    # numpy backend rejects device/dtype (contract: numpy takes no device/dtype)
    with pytest.raises(ValueError, match="device/dtype"):
        random_cptp_kraus(2, 3, rng, backend="numpy", device="cpu")
    with pytest.raises(ValueError, match="device/dtype"):
        random_density_matrix(3, rng, backend="numpy", dtype="x")


def test_builders_torch_none_leg_raises_runtimeerror(monkeypatch):
    """torch=None leg (§10.6): on a torch-less box, backend='torch' must raise a loud
    RuntimeError, never silently fall back. Simulated by monkeypatching the module's
    torch reference to None (RESTORING monkeypatch auto-reverts -- the real torch is
    untouched for every other test). The numpy backend stays fully functional here,
    proving the guard is specific to the torch path."""
    monkeypatch.setattr(fixtures, "torch", None)
    rng = np.random.default_rng(31)
    with pytest.raises(RuntimeError, match="torch is not importable"):
        random_cptp_kraus(2, 3, rng, backend="torch")
    with pytest.raises(RuntimeError, match="torch is not importable"):
        random_density_matrix(3, rng, backend="torch")
    # numpy backend still works with torch=None (the numpy leg must not depend on torch)
    stack = random_cptp_kraus(2, 3, rng, backend="numpy")
    assert stack.shape == (2, 3, 3)
    rho = random_density_matrix(3, rng, backend="numpy")
    assert rho.shape == (3, 3)


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


def test_load_outputs_module_imports_guarded_script(tmp_path, monkeypatch):
    """Success leg: a __main__-guarded script imports as a module with NO side effects
    run (scripted-execution discipline). Uses a temp repo root via RESTORING monkeypatch
    on _REPO_ROOT so this is portable (outputs/ is gitignored/local-only -- pinning a
    specific committed script would be fragile on a fresh checkout). The guarded body
    must NOT execute on import: a module-level flag set only inside `if __name__ ==
    '__main__'` proves the guard held."""
    scripts = tmp_path / "outputs" / "probe"
    scripts.mkdir(parents=True)
    (scripts / "guarded_probe.py").write_text(
        "IMPORTED_MARKER = 'imported'\n"
        "RAN_MAIN = False\n"
        "def contribution():\n"
        "    return 42\n"
        "if __name__ == '__main__':\n"
        "    RAN_MAIN = True  # must NOT run on import\n",
        encoding="utf-8")
    monkeypatch.setattr(fixtures, "_REPO_ROOT", tmp_path)
    mod = load_outputs_module("outputs/probe/guarded_probe.py")
    assert mod.IMPORTED_MARKER == "imported"
    assert mod.contribution() == 42
    assert mod.RAN_MAIN is False  # the __main__-guarded body did not run on import


# --------------------------------------------------------------------------- #
# L1: Hypothesis property tests -- the random-input INVARIANTS hold for every  #
#     drawn (dim, n_kraus, seed), not just the pinned example seeds above.     #
#     These are genuinely-true invariants of the algebraic constructions       #
#     (QR-complete Kraus; rho = A A^H / tr) -- no legitimate draw can falsify.  #
# --------------------------------------------------------------------------- #
_CPTP_TOL = 1.0e-12
_DENSITY_TOL = 1.0e-12


@settings(max_examples=60, deadline=None,
          suppress_health_check=[HealthCheck.too_slow])
@given(n_kraus=st.integers(min_value=1, max_value=5),
       dim=st.integers(min_value=2, max_value=6),
       seed=st.integers(min_value=0, max_value=2**32 - 1))
def test_random_cptp_kraus_property_cptp_complete(n_kraus, dim, seed):
    """L1 property: for EVERY drawn (n_kraus, dim, seed) the numpy-backend stack is
    exactly CPTP -- ``sum_k K_k^H K_k == I_dim`` to 1e-12. This proves the legitimate
    path of the random builder always preserves the completeness invariant the internal
    _assert_cptp seam guards (the seam's negative leg is the sabotage meta-test above)."""
    rng = np.random.default_rng(seed)
    stack = random_cptp_kraus(n_kraus, dim, rng, backend="numpy", stacked=True)
    assert stack.shape == (n_kraus, dim, dim)
    gram = np.einsum("kij,kil->jl", stack.conj(), stack)
    resid = float(np.abs(gram - np.eye(dim)).max())
    assert resid <= _CPTP_TOL, f"completeness residual {resid:.3e} > {_CPTP_TOL:.1e}"


@settings(max_examples=60, deadline=None,
          suppress_health_check=[HealthCheck.too_slow])
@given(dim=st.integers(min_value=2, max_value=8),
       seed=st.integers(min_value=0, max_value=2**32 - 1))
def test_random_density_matrix_property_hermitian_psd_unit_trace(dim, seed):
    """L1 property: for EVERY drawn (dim, seed) the numpy-backend rho is Hermitian
    (max|rho - rho^H| <= 1e-12), PSD (min eigenvalue >= -1e-12), and unit-trace
    (|Re tr - 1| <= 1e-12, |Im tr| <= 1e-12). Proves the legitimate path always
    preserves the density invariant the extracted _assert_density seam guards -- the
    structurally-unreachable defensive branch is covered by this property (legitimate
    path) plus the sabotaged-rho meta-test (the seam's negative leg)."""
    rng = np.random.default_rng(seed)
    rho = random_density_matrix(dim, rng, backend="numpy")
    assert rho.shape == (dim, dim)
    assert float(np.abs(rho - rho.conj().T).max()) <= _DENSITY_TOL  # Hermitian
    assert float(np.linalg.eigvalsh(rho).min()) >= -_DENSITY_TOL     # PSD
    tr = np.trace(rho)
    assert abs(tr.real - 1.0) <= _DENSITY_TOL and abs(tr.imag) <= _DENSITY_TOL
