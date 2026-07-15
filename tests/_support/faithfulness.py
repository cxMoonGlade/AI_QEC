"""Reusable FAITHFULNESS test methods -- the maintained test-authoring API for the
coverage program (the fixtures/referee layer of feedback-api-first-no-adhoc-harness).

Motivation: batch after batch reached 100% coverage with VACUOUS asserts (K>=0 on a
sum-of-abs is a tautology; sum(P)==1 holds for ANY CPTP channel). The cure is not another
run-script -- it is a shared library of standard helpers so DISCRIMINATING, faithful tests
are the DEFAULT, written once and reused, not hand-rolled (and gotten wrong) per batch.

Two tiers, HONESTLY separated so an author never mistakes one for the other:

  (1) STRUCTURAL sanity -- necessary, NOT sufficient. These hold for MANY wrong
      implementations too, so a green here is NOT evidence of correctness; use them to catch
      gross breakage, never as a unit's faithfulness property. Named `assert_*` on the object
      shape: assert_trace_one, assert_hermitian, assert_psd, assert_cptp, assert_unitary,
      assert_prob_dist, assert_row_stochastic.

  (2) DISCRIMINATION -- the anti-vacuity core; THIS is what makes a test bite:
      * assert_discriminates(prop, real, wrong): prop must HOLD for the correct object AND
        FAIL for a sabotaged variant -- the KILLER pattern as ONE reusable method. It fails
        loudly if the property is vacuous (passes for the wrong variant too).
      * assert_pins(actual, reference): pin a VALUE against an INDEPENDENT recompute (a closed
        form or a from-scratch reimplementation -- NOT the SUT's own private helper). The cure
        for structural tautologies: pin the number, not a >=0 bound.

  Shared builders (deterministic given a seed): bell_state, product_state, maximally_mixed,
  random_density_matrix (re-exported from fixtures), valid_joint_distribution.

Standard stack only: numpy + plain asserts (usable in any pytest test or as a Hypothesis
property callable). No bespoke framework.
"""
from __future__ import annotations

from typing import Callable, Mapping, Sequence

import numpy as np

# a single tolerance knob; callers may override per-assert.
TOL = 1e-9


# --------------------------------------------------------------------------- #
# (1) STRUCTURAL sanity -- necessary, NOT sufficient (documented as such)      #
# --------------------------------------------------------------------------- #
def assert_hermitian(M, tol: float = TOL, *, label: str = "operator") -> None:
    M = np.asarray(M)
    err = float(np.max(np.abs(M - M.conj().T))) if M.size else 0.0
    assert err <= tol, f"{label} not Hermitian: max|M-M^H|={err:.2e} > {tol:.1e}"


def assert_psd(M, tol: float = TOL, *, label: str = "operator") -> None:
    M = np.asarray(M)
    assert_hermitian(M, tol, label=label)
    ev = float(np.min(np.linalg.eigvalsh((M + M.conj().T) / 2))) if M.size else 0.0
    assert ev >= -tol, f"{label} not PSD: min eigenvalue {ev:.2e} < -{tol:.1e}"


def assert_trace_one(rho, tol: float = TOL, *, label: str = "density matrix") -> None:
    tr = complex(np.trace(np.asarray(rho)))
    assert abs(tr - 1.0) <= tol, f"{label} trace {tr:.6g} != 1 (tol {tol:.1e})"


def assert_density(rho, tol: float = TOL, *, label: str = "density matrix") -> None:
    """Hermitian + PSD + unit-trace (a valid quantum state). STRUCTURAL."""
    assert_hermitian(rho, tol, label=label)
    assert_psd(rho, tol, label=label)
    assert_trace_one(rho, tol, label=label)


def assert_unitary(U, tol: float = TOL, *, label: str = "operator") -> None:
    U = np.asarray(U)
    n = U.shape[0]
    err = float(np.max(np.abs(U.conj().T @ U - np.eye(n))))
    assert err <= tol, f"{label} not unitary: max|U^H U - I|={err:.2e} > {tol:.1e}"


def assert_cptp(kraus: Sequence, tol: float = TOL, *, label: str = "channel") -> None:
    """sum_k K_k^H K_k == I (trace-preserving; CP by Kraus construction). STRUCTURAL."""
    ks = [np.asarray(k) for k in kraus]
    assert ks, f"{label}: empty Kraus set"
    dim = ks[0].shape[1]
    s = sum(k.conj().T @ k for k in ks)
    err = float(np.max(np.abs(s - np.eye(dim))))
    assert err <= tol, f"{label} not trace-preserving: max|sum K^H K - I|={err:.2e} > {tol:.1e}"


def assert_prob_dist(p, tol: float = TOL, *, label: str = "distribution") -> None:
    """Non-negative and sums to 1. Accepts a dict of values or an array. STRUCTURAL."""
    vals = np.asarray(list(p.values()) if isinstance(p, Mapping) else p, dtype=float)
    assert float(vals.min(initial=0.0)) >= -tol, f"{label} has a negative entry {vals.min():.2e}"
    assert abs(float(vals.sum()) - 1.0) <= tol, f"{label} sums to {vals.sum():.6g} != 1"


def assert_row_stochastic(M, tol: float = TOL, *, label: str = "matrix") -> None:
    M = np.asarray(M, dtype=float)
    rs = M.sum(axis=1)
    assert float(np.max(np.abs(rs - 1.0))) <= tol, f"{label} rows not stochastic: {rs}"
    assert float(M.min()) >= -tol, f"{label} has a negative entry {M.min():.2e}"


# --------------------------------------------------------------------------- #
# (2) DISCRIMINATION -- the anti-vacuity core (what makes a test BITE)         #
# --------------------------------------------------------------------------- #
def assert_discriminates(prop: Callable, real, wrong, *, label: str = "property") -> None:
    """The KILLER pattern as ONE reusable method. ``prop`` is a callable that ASSERTS a
    property (raises AssertionError on violation). This checks that ``prop``:
      (a) HOLDS for the correct object ``real`` (prop(real) does not raise), AND
      (b) FAILS for the sabotaged variant ``wrong`` (prop(wrong) raises).
    If prop(wrong) also passes, the property is VACUOUS and this raises loudly -- exactly the
    100%-covered-but-non-discriminating failure mode the mutation gate flags mechanically."""
    try:
        prop(real)
    except AssertionError as e:
        raise AssertionError(f"{label}: does NOT hold for the CORRECT object -- the property "
                             f"or the real implementation is wrong: {e}")
    try:
        prop(wrong)
    except AssertionError:
        return  # good: the property distinguishes real from wrong -> it has teeth
    raise AssertionError(
        f"{label}: VACUOUS -- it ALSO passes for the sabotaged variant, so it cannot catch the "
        f"bug. Pin a discriminating VALUE (assert_pins vs an independent recompute) instead of a "
        f"structural bound.")


def assert_pins(actual, reference, *, atol: float = TOL, rtol: float = 0.0,
                label: str = "value") -> None:
    """Pin ``actual`` to a ``reference`` that MUST be an INDEPENDENT recompute (a closed form,
    a from-scratch reimplementation, or a certified constant) -- NOT the system-under-test's own
    private helper (that would be circular). Works for scalars, arrays, and dicts (matched keys).
    This is the cure for sum-of-abs>=0 tautologies: pin the NUMBER, not a bound."""
    if isinstance(actual, Mapping) or isinstance(reference, Mapping):
        ka, kr = set(actual), set(reference)
        assert ka == kr, f"{label}: key mismatch (only-actual={ka - kr}, only-ref={kr - ka})"
        a = np.array([actual[k] for k in sorted(ka)], dtype=float)
        r = np.array([reference[k] for k in sorted(ka)], dtype=float)
    else:
        a, r = np.asarray(actual, dtype=float), np.asarray(reference, dtype=float)
    assert np.allclose(a, r, atol=atol, rtol=rtol), (
        f"{label}: does not match the independent reference "
        f"(max|Δ|={float(np.max(np.abs(a - r))):.2e}, atol={atol:.1e}, rtol={rtol:.1e})")


def assert_raises_exact(exc_type, message: str, call: Callable, *, label: str = "guard"):
    """Assert ``call()`` raises ``exc_type`` with ``str(exc)`` EXACTLY equal to ``message``.

    The EXACT-message check is the whole point (and why a bare ``pytest.raises(match=...)``
    is not enough): mutmut's string mutations (``"foo"`` -> ``"XXfooXX"`` / ``"FOO"``) and a
    ``raise ValueError(None)`` mutant all PASS a substring ``match=`` yet FAIL exact equality
    -- so a raising validation guard tested with this helper KILLS its message-content mutants,
    which a substring test leaves surviving (the recurring D11-D19 finding; 9 batches re-rolled
    a private ``_raises_exact`` for exactly this). Trip the guard through EVERY input route that
    reaches it -- 100% branch coverage of the guard is NOT the same as every routing INTO it
    being exercised (the channel-axis routing lesson). A wrong exception type or no raise
    fails loudly. Returns the caught exception for any further assertion.
    """
    try:
        call()
    except exc_type as exc:
        got = str(exc)
        if got != message:
            raise AssertionError(
                f"{label}: raised {exc_type.__name__} but its message is not the pinned string "
                f"(a message-content mutant would survive a substring match here)\n"
                f"  expected == {message!r}\n  got      == {got!r}") from None
        return exc
    except Exception as exc:  # noqa: BLE001 -- wrong type is a real failure, surface it loudly
        raise AssertionError(
            f"{label}: expected {exc_type.__name__} with message {message!r}, "
            f"but raised {type(exc).__name__}: {exc}") from None
    raise AssertionError(
        f"{label}: expected {exc_type.__name__} with message {message!r}, but nothing was raised "
        f"(the guard/route is not reached -- probe a reaching input; check the PUBLIC entry points, "
        f"not just the internal path)")


# --------------------------------------------------------------------------- #
# shared builders (deterministic; a seed makes them reproducible)             #
# --------------------------------------------------------------------------- #
def bell_state() -> np.ndarray:
    """|Phi+><Phi+| on 2 qubits (concurrence 1, negativity 0.5)."""
    v = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    return np.outer(v, v.conj())


def product_state(a: int = 0, b: int = 0) -> np.ndarray:
    """|ab><ab| on 2 qubits (a product state; concurrence 0)."""
    v = np.zeros(4, dtype=complex)
    v[2 * a + b] = 1.0
    return np.outer(v, v.conj())


def maximally_mixed(dim: int = 2) -> np.ndarray:
    return np.eye(dim, dtype=complex) / dim


def valid_joint_distribution(keys: Sequence, seed: int = 0) -> dict:
    """A random non-negative normalized distribution over ``keys`` (deterministic given seed)."""
    rng = np.random.default_rng(seed)
    w = rng.random(len(keys))
    w = w / w.sum()
    return {k: float(w[i]) for i, k in enumerate(keys)}
