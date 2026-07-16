"""Per-unit L0+L1+L2 coverage of
``error_coupling_simulator.source.coupling`` (CPU-pure public units; no GPU, no quimb,
so out_of_scope is empty).

``source/coupling.py`` owns the Axis-2 shared-source parameter fan-out ``Theta(z_t)``: one
explicit source draw conditions many mechanism parameters in the SAME cycle -- the static-ZZ
frequency-drift closed form, the positive-rate exp maps (gamma_phi and drive_omega),
and the logit maps (spillover, readout, reset, cz). It is a parameter
LAYER, not a Stim/DEM noise layer nor a channel assembler.

L2 DISCIPLINE (the standing lesson: 100% coverage != discrimination). This is closed-form
physics, so value-pins are the workhorse: every load-bearing number is PINNED against an
INDEPENDENT from-scratch recompute of the analytic formula (the dispersive static-ZZ cross-Kerr
``zeta = 2 J^2 [1/(D-a) - 1/(D+a)]``, the ``phi = zeta(J)*t_gate/4`` inversion + its EXACT
round-trip, the fail-closed positive-rate exponential map, the open-interval logit map, and a from-scratch
Pearson recompute for ``cross_mechanism_correlation``) -- NEVER the module's own helper. No
numerical-convergence parameter is load-bearing (every map is analytic), so no pin is slow.
Every validation RAISE asserts its EXACT message via ``str(excinfo.value) == ...`` (mutmut wraps/
roundtrips string literals -- a substring ``match=`` still passes them, exact-equality kills them).
``assert_discriminates`` gives each closed-form invariant a demonstrated sabotage variant it rejects.
"""
from __future__ import annotations

import dataclasses
import math
import sys

import mpmath
import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_pins

import error_coupling_simulator.source.coupling as coupling
import error_coupling_simulator.source as source_api
from error_coupling_simulator.source.coupling import (
    CoupledNoiseParameters,
    SourceCouplingConfig,
    StaticZZParameters,
    cross_mechanism_correlation,
    default_source_coupling_config,
    drift_to_t2,
    exchange_j_from_phi,
    independent_baseline_trajectory_to_params,
    parameter_series,
    source_to_params,
    static_zz_zeta,
    trajectory_to_params,
    zz_phi_from_frequency_drift,
)

_TWO_PI = 2.0 * math.pi
_SOURCE_KEYS = (
    "zz",
    "gamma_phi",
    "detuning",
    "drive",
    "spillover",
    "readout",
    "reset",
    "cz",
)

# default StaticZZParameters constants (used by the default config's zz)
_BASE_DELTA = _TWO_PI * (6.0 - 6.1)          # 2*pi*(omega_a - omega_b)
_ALPHA = _TWO_PI * (-300.0) * 1e-3           # 2*pi*alpha_mhz*1e-3


# --------------------------------------------------------------------------- #
# helpers: exact-message raise + INDEPENDENT recomputes (NOT the module's own) #
# --------------------------------------------------------------------------- #
def _raises_exact(exc, msg, fn):
    """pytest.raises pinning the EXACT message string (kills mutmut's string-literal
    wrap/roundtrip mutations that a substring ``match=`` lets survive)."""
    with pytest.raises(exc) as ei:
        fn()
    assert str(ei.value) == msg, f"message mismatch\n got: {str(ei.value)!r}\n exp: {msg!r}"


def _indep_zeta(delta: float, alpha: float, j: float) -> float:
    """static_zz_zeta closed form, recomputed from scratch."""
    return 2.0 * j * j * (1.0 / (delta - alpha) - 1.0 / (delta + alpha))


def _indep_exchange_j(phi: float, delta: float, alpha: float, t_gate: float) -> float:
    """Invert phi = zeta(J)*t_gate/4 for |J| (independent of the module)."""
    coeff = _indep_zeta(delta, alpha, 1.0)
    j2 = 4.0 * phi / (coeff * t_gate)
    return math.sqrt(max(0.0, j2))


def _indep_pos_rate(base: float, x: float, sens: float) -> float:
    """Direct interior ``base*exp(sens*x)`` reference for a positive rate."""
    return base * math.exp(sens * x)


def _indep_prob_logit(p: float, x: float, sens: float) -> float:
    """The logit-domain probability map, recomputed from scratch (p>0 assumed)."""
    shift = sens * x
    if shift == 0.0:
        return p
    y = math.log(p) - math.log1p(-p) + shift
    if y < 0.0:
        exp_y = math.exp(y)
        return exp_y / (1.0 + exp_y)
    exp_neg_y = math.exp(-y)
    return 1.0 - exp_neg_y / (1.0 + exp_neg_y)


def _indep_pearson(a, b) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    am = a - a.mean()
    bm = b - b.mean()
    denom = math.sqrt(float((am * am).sum()) * float((bm * bm).sum()))
    if denom == 0.0:
        return 0.0
    return float((am * bm).sum() / denom)


def _mp_float(value: float):
    numerator, denominator = float(value).as_integer_ratio()
    return mpmath.mpf(numerator) / denominator


def _ulp_distance(left: float, right: float) -> int:
    left_bits = int(np.asarray(float(left), dtype=np.float64).view(np.uint64))
    right_bits = int(np.asarray(float(right), dtype=np.float64).view(np.uint64))
    return abs(left_bits - right_bits)


#: default zz exchange J, recomputed independently (matches cfg.zz.exchange_j_radns).
_J_DEFAULT = _indep_exchange_j(1.6e-4, _BASE_DELTA, _ALPHA, 25.0)


def test_public_parameter_type_names_and_exports():
    """Current types resolve through the complete coupling public surface."""

    expected_exports = {
        "CoupledNoiseParameters",
        "SourceCouplingConfig",
        "StaticZZParameters",
        "cross_mechanism_correlation",
        "default_source_coupling_config",
        "drift_to_t2",
        "exchange_j_from_phi",
        "independent_baseline_trajectory_to_params",
        "parameter_series",
        "source_to_params",
        "static_zz_zeta",
        "trajectory_to_params",
        "zz_phi_from_frequency_drift",
    }

    assert source_api.StaticZZParameters is StaticZZParameters
    assert source_api.CoupledNoiseParameters is CoupledNoiseParameters
    assert isinstance(SourceCouplingConfig().zz, StaticZZParameters)
    assert isinstance(source_to_params(0.0), CoupledNoiseParameters)
    assert set(coupling.__all__) == expected_exports
    assert expected_exports <= set(source_api.__all__)


# =========================================================================== #
# static_zz_zeta                                                              #
# =========================================================================== #
def test_L0_static_zz_zeta_value_and_singular_guard():
    for d, a, j in [(3.0, 1.0, 2.0), (-2.0, 0.5, 1.0), (5.0, -1.5, 0.3)]:
        assert_pins(static_zz_zeta(d, a, j), _indep_zeta(d, a, j), rtol=1e-12, atol=0.0,
                    label=f"zeta({d},{a},{j})")
    # J=0 -> zeta 0 exactly
    assert static_zz_zeta(3.0, 1.0, 0.0) == 0.0
    # singular: Delta == alpha -> denom1 ~ 0 (FIRST operand of the `or` fires)
    _raises_exact(ValueError,
                  "static_zz_zeta singular: Delta too close to +/- alpha (Delta=1.0, alpha=1.0)",
                  lambda: static_zz_zeta(1.0, 1.0, 1.0))
    # singular: Delta == -alpha -> denom2 ~ 0 (SECOND operand fires; kills `or`->`and`)
    _raises_exact(ValueError,
                  "static_zz_zeta singular: Delta too close to +/- alpha (Delta=-1.0, alpha=1.0)",
                  lambda: static_zz_zeta(-1.0, 1.0, 1.0))
    # guards
    _raises_exact(ValueError, "delta_radns must be finite, got nan",
                  lambda: static_zz_zeta(float("nan"), 1.0, 1.0))
    _raises_exact(ValueError, "alpha_radns must be finite, got inf",
                  lambda: static_zz_zeta(1.0, float("inf"), 1.0))
    _raises_exact(ValueError, "exchange_j_radns must be >= 0, got -1.0",
                  lambda: static_zz_zeta(3.0, 1.0, -1.0))


def test_KILLER_static_zz_zeta_discriminates():
    d, a, j = 3.0, 1.0, 2.0

    def prop(v):
        assert_pins(v, _indep_zeta(d, a, j), rtol=1e-12, atol=0.0, label="zeta")

    # wrong: `+` instead of `-` between the two Lorentzian poles (wrong sign structure)
    wrong = 2.0 * j * j * (1.0 / (d - a) + 1.0 / (d + a))
    assert_discriminates(prop, static_zz_zeta(d, a, j), wrong, label="static zz zeta")


def test_static_zz_zeta_preserves_a_representable_cancellation_sensitive_value():
    delta = 1.0e16
    alpha = 1.0
    exchange = 1.0e8
    with mpmath.workdps(200):
        oracle = float(
            4
            * _mp_float(exchange) ** 2
            * _mp_float(alpha)
            / (_mp_float(delta) ** 2 - _mp_float(alpha) ** 2)
        )
    assert oracle > 0.0
    got = static_zz_zeta(delta, alpha, exchange)
    assert _ulp_distance(got, oracle) <= 1
    assert static_zz_zeta(3.0, 1.0, 0.0) == 0.0
    assert static_zz_zeta(3.0, 0.0, 1.0) == 0.0

    recovered = static_zz_zeta(1.0e200, 1.0e100, 1.0e150)
    with mpmath.workdps(200):
        recovered_oracle = float(
            4
            * _mp_float(1.0e150) ** 2
            * _mp_float(1.0e100)
            / (_mp_float(1.0e200) ** 2 - _mp_float(1.0e100) ** 2)
        )
    assert _ulp_distance(recovered, recovered_oracle) <= 1

    _raises_exact(
        ValueError,
        "static_zz_zeta nonzero result is not representable as a finite float64",
        lambda: static_zz_zeta(0.0, 1.0e-10, 5.0e153),
    )


def test_static_zz_zeta_does_not_trust_a_subnormal_product_intermediate():
    cases = (
        (
            float.fromhex("-0x1.625acf6b5dcaap-975"),
            float.fromhex("-0x1.bcd54cf7bba2cp-28"),
            float.fromhex("0x1.df8793bfec1d4p-524"),
        ),
        (math.nextafter(1.0e12, math.inf), 1.0e12, 1.0e-160),
    )
    with mpmath.workdps(200):
        for delta, alpha, exchange in cases:
            assert 0.0 < abs(exchange * exchange) < sys.float_info.min
            oracle = float(
                4
                * _mp_float(exchange) ** 2
                * _mp_float(alpha)
                / (_mp_float(delta) ** 2 - _mp_float(alpha) ** 2)
            )
            got = static_zz_zeta(delta, alpha, exchange)
            assert _ulp_distance(got, oracle) <= 1


def test_static_zz_zeta_rejects_exact_overflow_that_rounds_to_dbl_max_midway():
    cases = (
        (
            float.fromhex("0x1.4091ace2669adp-32"),
            float.fromhex("0x1.ac7d61cbeb350p-35"),
            float.fromhex("0x1.597dfc7a6101ap+496"),
        ),
        (
            float.fromhex("0x1.1d3315a6d94d2p-33"),
            float.fromhex("0x1.c2ad43f8eb7bdp-36"),
            float.fromhex("0x1.a56dbd4f195f8p+495"),
        ),
    )
    with mpmath.workdps(200):
        for delta, alpha, exchange in cases:
            exact = (
                4
                * _mp_float(exchange) ** 2
                * _mp_float(alpha)
                / ((_mp_float(delta) - _mp_float(alpha)) * (_mp_float(delta) + _mp_float(alpha)))
            )
            assert math.isinf(float(exact))
            _raises_exact(
                ValueError,
                "static_zz_zeta nonzero result is not representable as a finite float64",
                lambda: static_zz_zeta(delta, alpha, exchange),
            )


def test_static_zz_zeta_upper_finite_boundary_stays_within_two_ulps():
    delta = float.fromhex("0x1.1be17864afa97p-13")
    alpha = float.fromhex("0x1.c1b301ec3222dp-16")
    exchange = float.fromhex("0x1.a3e4bcc646b0dp+505")
    with mpmath.workdps(200):
        oracle = float(
            4
            * _mp_float(exchange) ** 2
            * _mp_float(alpha)
            / ((_mp_float(delta) - _mp_float(alpha)) * (_mp_float(delta) + _mp_float(alpha)))
        )
    assert math.isfinite(oracle)
    assert _ulp_distance(static_zz_zeta(delta, alpha, exchange), oracle) <= 2


@settings(max_examples=200, deadline=None)
@given(d=st.floats(-6.0, 6.0, allow_nan=False, allow_infinity=False),
       a=st.floats(-3.0, 3.0, allow_nan=False, allow_infinity=False),
       j=st.floats(0.0, 4.0, allow_nan=False, allow_infinity=False))
def test_L1_static_zz_zeta_matches_independent(d, a, j):
    if abs(d - a) < 1e-3 or abs(d + a) < 1e-3:      # avoid the singular guard
        return
    if j == 0.0 or a == 0.0:
        assert static_zz_zeta(d, a, j) == 0.0
        return
    with mpmath.workdps(200):
        exact = (
            4
            * _mp_float(j) ** 2
            * _mp_float(a)
            / (_mp_float(d) ** 2 - _mp_float(a) ** 2)
        )
        oracle = float(exact)
    if oracle == 0.0 or not math.isfinite(oracle):
        _raises_exact(
            ValueError,
            "static_zz_zeta nonzero result is not representable as a finite float64",
            lambda: static_zz_zeta(d, a, j),
        )
    else:
        assert _ulp_distance(static_zz_zeta(d, a, j), oracle) <= 2


# =========================================================================== #
# exchange_j_from_phi                                                         #
# =========================================================================== #
def test_L0_exchange_j_from_phi_value_roundtrip_and_guards():
    for phi, d, a, tg in [(1.6e-4, _BASE_DELTA, _ALPHA, 25.0), (2e-3, 3.0, 1.0, 10.0)]:
        j = exchange_j_from_phi(phi, delta_radns=d, alpha_radns=a, t_gate_ns=tg)
        assert_pins(j, _indep_exchange_j(phi, d, a, tg), rtol=1e-12, atol=0.0, label="J")
        # EXACT round-trip: zeta(J)*t_gate/4 == phi (independent AND module zeta)
        assert_pins(_indep_zeta(d, a, j) * tg / 4.0, phi, rtol=1e-9, atol=0.0, label="rt phi")
        assert_pins(static_zz_zeta(d, a, j) * tg / 4.0, phi, rtol=1e-9, atol=0.0, label="rt phi mod")
    # guards
    _raises_exact(ValueError, "phi_rad must be finite, got nan",
                  lambda: exchange_j_from_phi(float("nan"), delta_radns=3.0, alpha_radns=1.0,
                                              t_gate_ns=10.0))
    _raises_exact(ValueError, "t_gate_ns must be > 0, got 0.0",
                  lambda: exchange_j_from_phi(1e-4, delta_radns=3.0, alpha_radns=1.0, t_gate_ns=0.0))
    _raises_exact(
        ValueError,
        "static_zz_zeta singular: Delta too close to +/- alpha (Delta=1.0, alpha=1.0)",
        lambda: exchange_j_from_phi(
            1e-4,
            delta_radns=1.0,
            alpha_radns=1.0,
            t_gate_ns=10.0,
        ),
    )
    assert exchange_j_from_phi(
        0.0,
        delta_radns=3.0,
        alpha_radns=1.0,
        t_gate_ns=10.0,
    ) == 0.0
    # zero coefficient: alpha=0 -> zeta(1) == 2*(1/D - 1/D) == 0
    _raises_exact(ValueError, "cannot infer exchange J because zeta coefficient is zero",
                  lambda: exchange_j_from_phi(1e-4, delta_radns=1.0, alpha_radns=0.0, t_gate_ns=10.0))
    small_coeff = static_zz_zeta(1.0e8, 1.0, 1.0)
    assert 0.0 < small_coeff < coupling.NUMERICAL_ZERO
    small_phi = small_coeff * 25.0 / 4.0
    assert _ulp_distance(
        exchange_j_from_phi(
            small_phi,
            delta_radns=1.0e8,
            alpha_radns=1.0,
            t_gate_ns=25.0,
        ),
        1.0,
    ) <= 1
    # sign inconsistency: coeff = zeta(1) = 0.5 > 0, phi < 0 -> J2 < 0
    _raises_exact(ValueError,
                  "phi sign is inconsistent with the static-ZZ coefficient; "
                  "phi=-1.0, coeff=0.5, t_gate=1.0",
                  lambda: exchange_j_from_phi(-1.0, delta_radns=3.0, alpha_radns=1.0, t_gate_ns=1.0))
    coeff = static_zz_zeta(_BASE_DELTA, _ALPHA, 1.0)
    tiny_negative_phi = (-5.0e-13) * coeff * 25.0 / 4.0
    _raises_exact(
        ValueError,
        "phi sign is inconsistent with the static-ZZ coefficient; "
        f"phi={tiny_negative_phi}, coeff={coeff}, t_gate=25.0",
        lambda: exchange_j_from_phi(
            tiny_negative_phi,
            delta_radns=_BASE_DELTA,
            alpha_radns=_ALPHA,
            t_gate_ns=25.0,
        ),
    )
    zz = StaticZZParameters()
    largest = sys.float_info.max
    coeff = static_zz_zeta(zz.base_delta_radns, zz.alpha_radns, 1.0)
    with mpmath.workdps(200):
        for small_phi, small_t_gate in ((1.0e-320, 1.0e-320), (1.0e-320, 25.0)):
            small_oracle = float(
                mpmath.sqrt(
                    4
                    * _mp_float(small_phi)
                    / (_mp_float(coeff) * _mp_float(small_t_gate))
                )
            )
            small_result = exchange_j_from_phi(
                small_phi,
                delta_radns=zz.base_delta_radns,
                alpha_radns=zz.alpha_radns,
                t_gate_ns=small_t_gate,
            )
            assert _ulp_distance(small_result, small_oracle) <= 1
    with mpmath.workdps(200):
        oracle = float(
            mpmath.sqrt(
                4 * _mp_float(largest) / (_mp_float(coeff) * _mp_float(largest))
            )
        )
    recovered = exchange_j_from_phi(
        largest,
        delta_radns=zz.base_delta_radns,
        alpha_radns=zz.alpha_radns,
        t_gate_ns=largest,
    )
    assert _ulp_distance(recovered, oracle) <= 1
    min_subnormal = math.nextafter(0.0, 1.0)
    with mpmath.workdps(200):
        tiny_oracle = float(
            mpmath.sqrt(
                4 * _mp_float(min_subnormal) / (_mp_float(coeff) * _mp_float(25.0))
            )
        )
    tiny_recovered = exchange_j_from_phi(
        min_subnormal,
        delta_radns=zz.base_delta_radns,
        alpha_radns=zz.alpha_radns,
        t_gate_ns=25.0,
    )
    assert tiny_oracle > 0.0
    assert _ulp_distance(tiny_recovered, tiny_oracle) <= 1
    _raises_exact(
        ValueError,
        "exchange_j_radns is not representable as a finite positive float64",
        lambda: exchange_j_from_phi(
            sys.float_info.max,
            delta_radns=zz.base_delta_radns,
            alpha_radns=zz.alpha_radns,
            t_gate_ns=math.nextafter(0.0, 1.0),
        ),
    )


def test_KILLER_exchange_j_from_phi_discriminates():
    phi, d, a, tg = 2e-3, 3.0, 1.0, 10.0

    def prop(j):
        assert_pins(j, _indep_exchange_j(phi, d, a, tg), rtol=1e-12, atol=0.0, label="J")

    # wrong: drop the factor 4 (phi instead of 4*phi in the inversion)
    coeff = _indep_zeta(d, a, 1.0)
    wrong = math.sqrt(max(0.0, phi / (coeff * tg)))
    assert_discriminates(prop, exchange_j_from_phi(phi, delta_radns=d, alpha_radns=a, t_gate_ns=tg),
                         wrong, label="exchange J")


@pytest.mark.parametrize(
    "alpha",
    (
        float.fromhex("0x1.2p+195"),
        float.fromhex("0x1.cp+194"),
    ),
)
def test_exchange_j_uses_end_to_end_inputs_when_coefficient_is_subnormal(alpha):
    delta = float.fromhex("0x1p+636")
    phi = float.fromhex("0x1p-65")
    t_gate = float.fromhex("0x1p+440")
    with mpmath.workdps(200):
        exact_j = mpmath.sqrt(
            _mp_float(phi)
            * (_mp_float(delta) - _mp_float(alpha))
            * (_mp_float(delta) + _mp_float(alpha))
            / (_mp_float(alpha) * _mp_float(t_gate))
        )
        oracle = float(exact_j)
    got = exchange_j_from_phi(
        phi,
        delta_radns=delta,
        alpha_radns=alpha,
        t_gate_ns=t_gate,
    )
    assert _ulp_distance(got, oracle) <= 1


def test_exchange_j_direct_path_declares_its_two_ulp_bound():
    delta = float.fromhex("-0x1.a837c88962923p+191")
    alpha = float.fromhex("-0x1.2b0db576e809ep+185")
    phi = float.fromhex("-0x1.82cdc8fe2d8c7p-243")
    t_gate = float.fromhex("0x1.c9eada0d47998p+783")
    oracle = float.fromhex("0x1.fe1f81ed61c17p-415")

    got = exchange_j_from_phi(
        phi,
        delta_radns=delta,
        alpha_radns=alpha,
        t_gate_ns=t_gate,
    )
    assert got.hex() == "0x1.fe1f81ed61c15p-415"
    assert _ulp_distance(got, oracle) == 2


def test_exchange_j_sign_error_survives_an_unrepresentable_coefficient():
    delta = float.fromhex("0x1p+636")
    alpha = float.fromhex("0x1.cp+194")
    phi = -float.fromhex("0x1p-65")
    t_gate = float.fromhex("0x1p+440")
    _raises_exact(
        ValueError,
        "phi sign is inconsistent with the static-ZZ coefficient; "
        f"phi={phi}, coeff=positive, t_gate={t_gate}",
        lambda: exchange_j_from_phi(
            phi,
            delta_radns=delta,
            alpha_radns=alpha,
            t_gate_ns=t_gate,
        ),
    )


# =========================================================================== #
# zz_phi_from_frequency_drift                                                 #
# =========================================================================== #
def test_L0_zz_phi_from_frequency_drift_value_and_base_identity():
    cfg = SourceCouplingConfig(z_scale_radns=1e-4)
    for z in (0.0, 1e-5, -1e-5, 2e-4):
        phi, zeta = zz_phi_from_frequency_drift(z, cfg)
        zeta_ref = _indep_zeta(_BASE_DELTA + z, _ALPHA, _J_DEFAULT)
        assert_pins(zeta, zeta_ref, rtol=1e-9, atol=0.0, label=f"zeta@{z}")
        assert_pins(phi, zeta_ref * 25.0 / 4.0, rtol=1e-9, atol=0.0, label=f"phi@{z}")
    # off-source identity: phi(0) == base_phi_rad
    phi0, zeta0 = zz_phi_from_frequency_drift(0.0, cfg)
    assert_pins(phi0, 1.6e-4, rtol=1e-9, atol=0.0, label="phi0==base")
    assert_pins(zeta0, 4.0 * 1.6e-4 / 25.0, rtol=1e-9, atol=0.0, label="zeta0")
    # guard
    _raises_exact(ValueError, "z_t_radns must be finite, got nan",
                  lambda: zz_phi_from_frequency_drift(float("nan"), cfg))
    extreme_phi = sys.float_info.max / 2.0
    extreme_cfg = SourceCouplingConfig(
        zz=StaticZZParameters(t_gate_ns=4.0, base_phi_rad=extreme_phi)
    )
    recovered_phi, recovered_zeta = zz_phi_from_frequency_drift(0.0, extreme_cfg)
    assert math.isfinite(recovered_zeta)
    assert recovered_phi == extreme_phi


def test_KILLER_zz_phi_from_frequency_drift_discriminates():
    cfg = SourceCouplingConfig(z_scale_radns=1e-4)
    z = 0.2                          # a large detuning shift so +z vs -z zeta clearly differ

    def prop(pz):
        _, zeta = pz
        assert_pins(zeta, _indep_zeta(_BASE_DELTA + z, _ALPHA, _J_DEFAULT), rtol=1e-9, atol=0.0,
                    label="zeta")

    real = zz_phi_from_frequency_drift(z, cfg)
    wrong = (0.0, _indep_zeta(_BASE_DELTA - z, _ALPHA, _J_DEFAULT))    # `- z` instead of `+ z`
    assert_discriminates(prop, real, wrong, label="zz phi drift")


# =========================================================================== #
# drift_to_t2                                                                  #
# =========================================================================== #
def test_L0_drift_to_t2_value_config_branch_and_tphi():
    base, sens, zscale = 1.0 / 50_000.0, 0.5, 2e-4
    cfg = SourceCouplingConfig(z_scale_radns=zscale, gamma_phi_base_per_ns=base,
                               gamma_phi_sensitivity=sens)
    for z in (0.0, 1e-4, -1e-4, 3e-4):
        g, tphi = drift_to_t2(z, cfg)
        g_ref = _indep_pos_rate(base, z / zscale, sens)
        assert_pins(g, g_ref, rtol=1e-12, atol=0.0, label=f"gamma@{z}")
        assert_pins(tphi, 1.0 / g_ref, rtol=1e-12, atol=0.0, label=f"tphi@{z}")
    # config None -> the default config (base 1/75000, z=0 -> gamma == base, tphi == 1/base)
    g_def, tphi_def = drift_to_t2(0.0, None)
    assert_pins(g_def, 1.0 / 75_000.0, rtol=1e-12, atol=0.0, label="default gamma@0")
    assert_pins(tphi_def, 75_000.0, rtol=1e-12, atol=0.0, label="default tphi@0")
    # given cfg differs from default (base 1/50000 != 1/75000) -> kills `config or default`->`and`
    assert drift_to_t2(0.0, cfg)[0] != g_def
    # tphi == inf branch: base 0 AND sens 0 -> gamma 0
    cfg0 = SourceCouplingConfig(gamma_phi_base_per_ns=0.0, gamma_phi_sensitivity=0.0)
    g0, tphi0 = drift_to_t2(1e-4, cfg0)
    assert g0 == 0.0 and tphi0 == math.inf
    cfg_tiny = SourceCouplingConfig(
        gamma_phi_base_per_ns=math.nextafter(0.0, 1.0),
        gamma_phi_sensitivity=0.0,
    )
    _raises_exact(
        ValueError,
        "gamma_phi_per_ns is positive but its reciprocal is not representable as a finite float64 Tphi",
        lambda: drift_to_t2(0.0, cfg_tiny),
    )
    # guard
    _raises_exact(ValueError, "z_t_radns must be finite, got nan", lambda: drift_to_t2(float("nan"), cfg))


def test_source_fanout_forms_shift_from_raw_three_factor_inputs():
    source_draw = math.nextafter(0.0, 1.0)
    scale = 1.15
    sensitivity = sys.float_info.max
    rate_cfg = SourceCouplingConfig(
        z_scale_radns=scale,
        gamma_phi_base_per_ns=1.0,
        gamma_phi_sensitivity=sensitivity,
    )
    with mpmath.workdps(200):
        shift = _mp_float(sensitivity) * _mp_float(source_draw) / _mp_float(scale)
        gamma_oracle = float(mpmath.exp(shift))
    gamma, _ = drift_to_t2(source_draw, rate_cfg)
    assert gamma == gamma_oracle

    probability_cfg = SourceCouplingConfig(
        z_scale_radns=scale,
        gamma_phi_sensitivity=0.0,
        drive_omega_sensitivity=0.0,
        spillover_sensitivity=0.0,
        readout_flip_base_p=0.01,
        readout_flip_sensitivity=sensitivity,
        reset_flip_sensitivity=0.0,
        cz_depol_sensitivity=0.0,
    )
    with mpmath.workdps(200):
        base_probability = _mp_float(probability_cfg.readout_flip_base_p)
        odds = base_probability / (1 - base_probability)
        probability_oracle = float(odds * mpmath.exp(shift) / (1 + odds * mpmath.exp(shift)))
    emitted = source_to_params(source_draw, probability_cfg)
    assert emitted.readout_flip_p == probability_oracle


def test_L0_modulate_positive_rate_rejects_unrepresentable_drift():
    # sens*x = +/-5e5 cannot produce a finite positive float64 rate.
    cfg = SourceCouplingConfig(z_scale_radns=1e-6, gamma_phi_base_per_ns=1e-4,
                               gamma_phi_sensitivity=0.5)
    message = "gamma_phi_per_ns: modulated positive rate is not representable"
    _raises_exact(ValueError, message, lambda: drift_to_t2(1.0, cfg))
    _raises_exact(ValueError, message, lambda: drift_to_t2(-1.0, cfg))


def test_KILLER_drift_to_t2_discriminates():
    base, sens, zscale = 1e-4, 0.6, 2e-4
    cfg = SourceCouplingConfig(z_scale_radns=zscale, gamma_phi_base_per_ns=base,
                               gamma_phi_sensitivity=sens)
    z = 3e-4

    def prop(g):
        assert_pins(g, _indep_pos_rate(base, z / zscale, sens), rtol=1e-12, atol=0.0, label="gamma")

    wrong = base * math.exp(-sens * z / zscale)      # wrong-sign exponent
    assert_discriminates(prop, drift_to_t2(z, cfg)[0], wrong, label="drift gamma")


# =========================================================================== #
# default_source_coupling_config                                             #
# =========================================================================== #
def test_L0_default_source_coupling_config_pins_documented_defaults():
    cfg = default_source_coupling_config()
    assert isinstance(cfg, SourceCouplingConfig)
    assert_pins(cfg.z_scale_radns, 1e-4, rtol=1e-12, atol=0.0, label="z_scale")
    assert_pins(cfg.gamma_phi_base_per_ns, 1.0 / 75_000.0, rtol=1e-12, atol=0.0, label="gamma base")
    assert_pins(cfg.gamma_phi_sensitivity, 0.35, rtol=1e-12, atol=0.0, label="gamma sens")
    assert_pins(cfg.drive_omega_base_radns, math.pi / 25.0, rtol=1e-12, atol=0.0, label="drive base")
    assert cfg.schema == "error_coupling_simulator.source.coupling_config.v2"


def test_source_coupling_config_rejects_unsupported_schema():
    unsupported_schema = "error_coupling_simulator.source.coupling_config.v0"
    with pytest.raises(ValueError, match="unsupported source coupling schema"):
        SourceCouplingConfig(schema=unsupported_schema)


# =========================================================================== #
# source_to_params (the shared-draw fan-out)                                   #
# =========================================================================== #
def test_L0_source_to_params_fanout_value_pins_and_config_branch():
    zscale = 1e-4
    cfg = SourceCouplingConfig(z_scale_radns=zscale, gamma_phi_sensitivity=0.4,
                               drive_omega_sensitivity=0.3, spillover_sensitivity=0.2,
                               readout_flip_sensitivity=0.4, reset_flip_sensitivity=0.35,
                               cz_depol_sensitivity=0.3)
    z = 0.5e-4
    p = source_to_params(z, cfg)
    assert p.coupling_mode == "shared"
    assert dict(p.source_draws_radns) == {k: z for k in _SOURCE_KEYS}
    assert_pins([v for _, v in p.normalized_draws], [z / zscale] * len(_SOURCE_KEYS),
                rtol=1e-12, atol=0.0, label="normalized")
    # every emitted field pinned against the independent closed form
    assert_pins(p.zz_zeta_radns, _indep_zeta(_BASE_DELTA + z, _ALPHA, _J_DEFAULT), rtol=1e-9,
                atol=0.0, label="zeta")
    assert_pins(p.zz_phi_rad, _indep_zeta(_BASE_DELTA + z, _ALPHA, _J_DEFAULT) * 25.0 / 4.0,
                rtol=1e-9, atol=0.0, label="phi")
    assert_pins(p.zz_exchange_j_radns, _J_DEFAULT, rtol=1e-9, atol=0.0, label="exchange_j")
    assert_pins(p.gamma_phi_per_ns, _indep_pos_rate(1.0 / 75_000.0, z / zscale, 0.4), rtol=1e-12,
                atol=0.0, label="gamma")
    assert_pins(p.tphi_ns, 1.0 / _indep_pos_rate(1.0 / 75_000.0, z / zscale, 0.4), rtol=1e-12,
                atol=0.0, label="tphi")
    assert_pins(p.detuning_radns, 0.0 + z, rtol=1e-12, atol=0.0, label="detuning")
    assert_pins(p.drive_omega_radns, _indep_pos_rate(math.pi / 25.0, z / zscale, 0.3), rtol=1e-12,
                atol=0.0, label="drive")
    assert_pins(p.spillover_cx, _indep_prob_logit(1e-3, z / zscale, 0.2), rtol=1e-12, atol=0.0,
                label="spillover")
    assert_pins(p.readout_flip_p, _indep_prob_logit(1e-2, z / zscale, 0.4), rtol=1e-12, atol=0.0,
                label="readout")
    assert_pins(p.reset_flip_p, _indep_prob_logit(5e-3, z / zscale, 0.35), rtol=1e-12, atol=0.0,
                label="reset")
    assert_pins(p.cz_depol_p, _indep_prob_logit(2e-3, z / zscale, 0.3), rtol=1e-12, atol=0.0,
                label="cz")
    # config None -> default (sens 0.35); differs from the given cfg (sens 0.4) at z != 0
    pd = source_to_params(z, None)
    assert_pins(pd.gamma_phi_per_ns, _indep_pos_rate(1.0 / 75_000.0, z / zscale, 0.35), rtol=1e-12,
                atol=0.0, label="default gamma")
    assert p.gamma_phi_per_ns != pd.gamma_phi_per_ns
    # guard
    _raises_exact(ValueError, "z_t_radns must be finite, got nan",
                  lambda: source_to_params(float("nan"), cfg))


def test_L0_source_to_params_zero_base_probability_raises():
    # a zero base_p with a nonzero sensitivity cannot be logit-modulated -> raise
    cfg = SourceCouplingConfig(readout_flip_base_p=0.0, readout_flip_sensitivity=0.4)
    _raises_exact(ValueError, "readout_flip_p: nonzero sensitivity cannot logit-modulate p=0",
                  lambda: source_to_params(1e-4, cfg))


# =========================================================================== #
# trajectory_to_params                                                        #
# =========================================================================== #
def test_L0_trajectory_to_params_maps_each_draw_and_config_branch():
    zscale = 1e-4
    cfg = SourceCouplingConfig(z_scale_radns=zscale, gamma_phi_sensitivity=0.4)
    z = np.array([0.0, 1e-5, -1e-5, 2e-5])
    out = trajectory_to_params(z, cfg)
    assert len(out) == 4
    for i, zi in enumerate(z):
        ref = source_to_params(float(zi), cfg)
        assert out[i].to_manifest() == ref.to_manifest()
    # independent value-pin on one element (kills a body mutation not seen via the delegate)
    assert_pins(out[1].gamma_phi_per_ns, _indep_pos_rate(1.0 / 75_000.0, 1e-5 / zscale, 0.4),
                rtol=1e-12, atol=0.0, label="traj gamma")
    # config None -> default; differs from the given cfg at z != 0 -> kills `config or default`->`and`
    outd = trajectory_to_params(z, None)
    assert outd[1].gamma_phi_per_ns != out[1].gamma_phi_per_ns
    # _as_1d_finite guards (empty / non-1D / non-finite)
    _raises_exact(ValueError, "z_trajectory_radns must be a non-empty 1-D trajectory",
                  lambda: trajectory_to_params([], cfg))
    _raises_exact(ValueError, "z_trajectory_radns must be a non-empty 1-D trajectory",
                  lambda: trajectory_to_params(np.zeros((2, 2)), cfg))
    _raises_exact(ValueError, "z_trajectory_radns contains non-finite values",
                  lambda: trajectory_to_params([1e-5, np.inf], cfg))


# =========================================================================== #
# independent_baseline_trajectory_to_params                                   #
# =========================================================================== #
def test_L0_independent_baseline_marginals_preserved_and_permutation_exact():
    zscale = 1e-4
    cfg = SourceCouplingConfig(
        z_scale_radns=zscale,
        gamma_phi_sensitivity=0.4,
        drive_omega_sensitivity=0.4,
    )
    z = np.linspace(-2e-4, 2e-4, 50)
    out = independent_baseline_trajectory_to_params(z, cfg, seed=123)
    assert {p.coupling_mode for p in out} == {"independent"}
    # marginal preserved: sorted detuning == sorted(base + z)
    det = parameter_series(out, "detuning_radns")
    np.testing.assert_allclose(np.sort(det), np.sort(0.0 + z))
    # permutation-EXACT: reproduce the per-key shuffles from the same seeded rng call order
    rng = np.random.default_rng(123)
    permuted = {k: np.array(z, copy=True) for k in _SOURCE_KEYS}
    for k in _SOURCE_KEYS:
        rng.shuffle(permuted[k])
    np.testing.assert_allclose(det, 0.0 + permuted["detuning"])
    gam = parameter_series(out, "gamma_phi_per_ns")
    np.testing.assert_allclose(
        gam, [_indep_pos_rate(1.0 / 75_000.0, gp / zscale, 0.4) for gp in permuted["gamma_phi"]])
    # config None -> default (differs from given cfg at same seed) -> kills `config or default`->`and`
    outd = independent_baseline_trajectory_to_params(z, None, seed=123)
    assert not np.allclose(parameter_series(outd, "gamma_phi_per_ns"), gam)
    # guard
    _raises_exact(ValueError, "z_trajectory_radns must be a non-empty 1-D trajectory",
                  lambda: independent_baseline_trajectory_to_params([], cfg, seed=1))


def test_KILLER_independent_baseline_breaks_cross_mechanism_correlation():
    cfg = SourceCouplingConfig(z_scale_radns=1e-4, gamma_phi_sensitivity=0.2,
                               drive_omega_sensitivity=0.2, readout_flip_sensitivity=0.2)
    z = np.linspace(-2e-4, 2e-4, 400)
    shared = trajectory_to_params(z, cfg)
    indep = independent_baseline_trajectory_to_params(z, cfg, seed=7)

    def prop(params):
        # the shared latent makes detuning and drive move together; the baseline destroys it
        assert abs(cross_mechanism_correlation(params, "detuning_radns", "drive_omega_radns")) > 0.9

    assert_discriminates(prop, shared, indep, label="cross-mechanism correlation")


# =========================================================================== #
# parameter_series                                                            #
# =========================================================================== #
def test_L0_parameter_series_value_dtype_and_attribute_error():
    cfg = SourceCouplingConfig(z_scale_radns=1e-4, gamma_phi_sensitivity=0.4)
    params = trajectory_to_params(np.array([0.0, 1e-5, 2e-5]), cfg)
    s = parameter_series(params, "detuning_radns")
    assert s.dtype == np.float64
    np.testing.assert_allclose(s, [p.detuning_radns for p in params])
    assert_pins(s, [0.0, 1e-5, 2e-5], rtol=1e-12, atol=1e-18, label="detuning series")  # detuning == z
    _raises_exact(AttributeError, "CoupledNoiseParameters has no field 'nope'",
                  lambda: parameter_series(params, "nope"))


# =========================================================================== #
# cross_mechanism_correlation                                                 #
# =========================================================================== #
def test_L0_cross_mechanism_correlation_value_zero_std_and_guards():
    cfg = SourceCouplingConfig(z_scale_radns=1e-4, gamma_phi_sensitivity=0.4,
                               drive_omega_sensitivity=0.4)
    z = np.linspace(-1e-4, 1e-4, 20)
    params = trajectory_to_params(z, cfg)
    a = parameter_series(params, "detuning_radns")
    b = parameter_series(params, "drive_omega_radns")
    got = cross_mechanism_correlation(params, "detuning_radns", "drive_omega_radns")
    assert_pins(got, _indep_pearson(a, b), rtol=1e-9, atol=1e-12, label="corr")
    assert -1.0 <= got <= 1.0
    # constant field a (zz_exchange_j is fixed across params) -> std(a)<=Z -> 0.0 (FIRST operand)
    assert cross_mechanism_correlation(params, "zz_exchange_j_radns", "detuning_radns") == 0.0
    # constant field b (swap) -> SECOND operand of the `or`
    assert cross_mechanism_correlation(params, "detuning_radns", "zz_exchange_j_radns") == 0.0
    # size-2 boundary does NOT raise (kills `size < 2` -> `size <= 2`)
    two = trajectory_to_params(np.array([0.0, 1e-5]), cfg)
    c2 = cross_mechanism_correlation(two, "detuning_radns", "drive_omega_radns")
    assert_pins(c2, _indep_pearson(parameter_series(two, "detuning_radns"),
                                   parameter_series(two, "drive_omega_radns")),
                rtol=1e-9, atol=1e-12, label="corr size2")
    # size-1 -> raise
    one = trajectory_to_params(np.array([0.0]), cfg)
    _raises_exact(ValueError, "need at least two paired samples",
                  lambda: cross_mechanism_correlation(one, "detuning_radns", "drive_omega_radns"))


def test_cross_mechanism_correlation_preserves_scale_and_fails_closed_nonfinite(monkeypatch):
    base = source_to_params(0.0)
    tiny = (
        dataclasses.replace(base, detuning_radns=0.0, zz_phi_rad=0.0),
        dataclasses.replace(base, detuning_radns=5e-13, zz_phi_rad=5e-13),
    )
    assert cross_mechanism_correlation(tiny, "detuning_radns", "zz_phi_rad") == 1.0

    largest = sys.float_info.max
    huge = (
        dataclasses.replace(base, detuning_radns=-largest, zz_phi_rad=-largest),
        dataclasses.replace(base, detuning_radns=largest, zz_phi_rad=largest),
    )
    assert cross_mechanism_correlation(huge, "detuning_radns", "zz_phi_rad") == 1.0

    zero_rate = source_to_params(
        0.0,
        SourceCouplingConfig(
            gamma_phi_base_per_ns=0.0,
            gamma_phi_sensitivity=0.0,
        ),
    )
    _raises_exact(
        ValueError,
        "tphi_ns must contain only finite emitted values for correlation",
        lambda: cross_mechanism_correlation(
            (zero_rate, zero_rate),
            "tphi_ns",
            "detuning_radns",
        ),
    )
    _raises_exact(
        ValueError,
        "tphi_ns must contain only finite emitted values for correlation",
        lambda: cross_mechanism_correlation(
            (zero_rate, zero_rate),
            "detuning_radns",
            "tphi_ns",
        ),
    )

    monkeypatch.setattr(coupling.np, "dot", lambda *_: math.inf)
    _raises_exact(
        ValueError,
        "Pearson correlation is not representable as a finite float64",
        lambda: cross_mechanism_correlation(tiny, "detuning_radns", "zz_phi_rad"),
    )


def test_cross_mechanism_correlation_rejects_corrupted_finite_ratio(monkeypatch):
    base = source_to_params(0.0)
    values = (
        dataclasses.replace(base, detuning_radns=0.0, zz_phi_rad=0.0),
        dataclasses.replace(base, detuning_radns=1.0, zz_phi_rad=1.0),
    )
    dot_values = iter((sys.float_info.max, sys.float_info.min, 1.0))
    monkeypatch.setattr(coupling.np, "dot", lambda *_: next(dot_values))
    _raises_exact(
        ValueError,
        "Pearson correlation is not representable as a finite float64",
        lambda: cross_mechanism_correlation(values, "detuning_radns", "zz_phi_rad"),
    )


def test_KILLER_cross_mechanism_correlation_discriminates():
    cfg = SourceCouplingConfig(z_scale_radns=1e-4, drive_omega_sensitivity=0.4)
    z = np.linspace(-1e-4, 1e-4, 30)
    params = trajectory_to_params(z, cfg)
    a = parameter_series(params, "detuning_radns")
    b = parameter_series(params, "drive_omega_radns")

    def prop(c):
        assert_pins(c, _indep_pearson(a, b), rtol=1e-9, atol=1e-12, label="corr")

    wrong = _indep_pearson(a, -b)    # anti-correlated variant (sign flips)
    assert_discriminates(prop, cross_mechanism_correlation(params, "detuning_radns",
                                                           "drive_omega_radns"),
                         wrong, label="cross-mechanism correlation")


# =========================================================================== #
# StaticZZParameters -- __post_init__ + properties + to_manifest               #
# =========================================================================== #
def test_L0_static_zz_parameters_properties_and_post_init():
    zz = StaticZZParameters()
    assert_pins(zz.base_delta_radns, _TWO_PI * (6.0 - 6.1), rtol=1e-12, atol=0.0, label="base_delta")
    assert_pins(zz.alpha_radns, _TWO_PI * (-300.0) * 1e-3, rtol=1e-12, atol=0.0, label="alpha")
    assert_pins(zz.exchange_j_radns, _J_DEFAULT, rtol=1e-9, atol=0.0, label="exchange_j")
    # a NON-default instance -> the properties genuinely depend on inputs (kill return-constant).
    # constants chosen so Delta != +/- alpha (no singular) AND coeff sign matches base_phi>0.
    zz2 = StaticZZParameters(omega_a_ghz=6.2, omega_b_ghz=6.1, alpha_mhz=-250.0, t_gate_ns=30.0,
                              base_phi_rad=1.7e-4)
    bd2, al2 = _TWO_PI * (6.2 - 6.1), _TWO_PI * (-250.0) * 1e-3
    assert_pins(zz2.base_delta_radns, bd2, rtol=1e-12, atol=0.0, label="base_delta2")
    assert_pins(zz2.alpha_radns, al2, rtol=1e-12, atol=0.0, label="alpha2")
    assert_pins(zz2.exchange_j_radns, _indep_exchange_j(1.7e-4, bd2, al2, 30.0), rtol=1e-9, atol=0.0,
                label="exchange_j2")
    # __post_init__ guards
    _raises_exact(ValueError, "omega_a_ghz must be finite, got inf",
                  lambda: StaticZZParameters(omega_a_ghz=float("inf")))
    _raises_exact(ValueError, "omega_b_ghz must be finite, got nan",
                  lambda: StaticZZParameters(omega_b_ghz=float("nan")))
    _raises_exact(ValueError, "alpha_mhz must be finite, got inf",
                  lambda: StaticZZParameters(alpha_mhz=float("inf")))
    _raises_exact(ValueError, "t_gate_ns must be > 0, got 0.0",
                  lambda: StaticZZParameters(t_gate_ns=0.0))
    _raises_exact(ValueError, "base_phi_rad must be finite",
                  lambda: StaticZZParameters(base_phi_rad=float("inf")))
    extreme = StaticZZParameters(base_phi_rad=sys.float_info.max)
    with mpmath.workdps(200):
        coeff = (
            4
            * _mp_float(extreme.alpha_radns)
            / (
                _mp_float(extreme.base_delta_radns) ** 2
                - _mp_float(extreme.alpha_radns) ** 2
            )
        )
        extreme_oracle = float(
            mpmath.sqrt(
                4
                * _mp_float(sys.float_info.max)
                / (coeff * _mp_float(extreme.t_gate_ns))
            )
        )
    assert _ulp_distance(extreme.exchange_j_radns, extreme_oracle) <= 1
    assert math.isfinite(extreme.to_manifest()["exchange_j_radns"])
    assert math.isfinite(SourceCouplingConfig(zz=extreme).to_manifest()["zz"]["exchange_j_radns"])

    extreme_alpha = StaticZZParameters(alpha_mhz=1.0e308, base_phi_rad=0.0)
    with mpmath.workdps(300):
        alpha_oracle = float(_mp_float(1.0e308) * (2 * mpmath.pi) / 1000)
    assert _ulp_distance(extreme_alpha.alpha_radns, alpha_oracle) <= 1


def test_L0_static_zz_parameters_to_manifest_all_keys_distinct():
    # all-distinct inputs so a key->wrong-attr routing mutation in to_manifest diverges
    zz = StaticZZParameters(omega_a_ghz=6.2, omega_b_ghz=6.1, alpha_mhz=-250.0, t_gate_ns=30.0,
                             base_phi_rad=1.7e-4)
    m = zz.to_manifest()
    assert set(m) == {"value_provenance", "omega_a_ghz", "omega_b_ghz", "alpha_mhz", "t_gate_ns", "base_phi_rad",
                      "base_delta_radns", "alpha_radns", "exchange_j_radns"}
    assert m["value_provenance"] == {
        "built_in_defaults": "project-design",
        "instance_source_locator": None,
        "claims_device_calibration": False,
    }
    assert m["omega_a_ghz"] == 6.2 and m["omega_b_ghz"] == 6.1 and m["alpha_mhz"] == -250.0
    assert m["t_gate_ns"] == 30.0 and m["base_phi_rad"] == 1.7e-4
    assert_pins(m["base_delta_radns"], zz.base_delta_radns, rtol=1e-12, atol=0.0, label="m base_delta")
    assert_pins(m["alpha_radns"], zz.alpha_radns, rtol=1e-12, atol=0.0, label="m alpha")
    assert_pins(m["exchange_j_radns"], zz.exchange_j_radns, rtol=1e-12, atol=0.0, label="m exchange_j")


def test_static_zz_parameters_snapshot_mutable_numeric_inputs():
    omega = np.asarray(6.0)
    zz = StaticZZParameters(omega_a_ghz=omega)
    omega[...] = math.inf
    assert zz.omega_a_ghz == 6.0
    assert math.isfinite(zz.to_manifest()["omega_a_ghz"])


def test_KILLER_static_zz_base_delta_discriminates():
    zz = StaticZZParameters(omega_a_ghz=6.3, omega_b_ghz=6.05)

    def prop(v):
        assert_pins(v, _TWO_PI * (6.3 - 6.05), rtol=1e-12, atol=0.0, label="base_delta")

    # wrong: `+` instead of `-` between the qubit frequencies
    assert_discriminates(prop, zz.base_delta_radns, _TWO_PI * (6.3 + 6.05), label="base_delta")


# =========================================================================== #
# SourceCouplingConfig -- __post_init__ + to_manifest                          #
# =========================================================================== #
#: an all-distinct config so every to_manifest key->attr route + every scalar is discriminated.
_DISTINCT_CFG = SourceCouplingConfig(
    z_scale_radns=1.1e-4, gamma_phi_base_per_ns=2.2e-5, gamma_phi_sensitivity=0.31,
    detuning_base_radns=0.13, drive_omega_base_radns=0.17, drive_omega_sensitivity=0.19,
    spillover_base_p=1.1e-3, spillover_sensitivity=0.23,
    readout_flip_base_p=1.2e-2, readout_flip_sensitivity=0.29,
    reset_flip_base_p=5.3e-3, reset_flip_sensitivity=0.37,
    cz_depol_base_p=2.4e-3, cz_depol_sensitivity=0.41)


def test_L0_source_coupling_config_post_init_happy_path_and_guards():
    SourceCouplingConfig()          # default valid construction covers both for-loops + all guards
    _raises_exact(
        TypeError,
        "zz must be a StaticZZParameters instance",
        lambda: SourceCouplingConfig(zz=object()),
    )
    # scalar guards
    _raises_exact(ValueError, "z_scale_radns must be > 0, got 0.0",
                  lambda: SourceCouplingConfig(z_scale_radns=0.0))
    _raises_exact(ValueError, "gamma_phi_base_per_ns must be >= 0, got -1.0",
                  lambda: SourceCouplingConfig(gamma_phi_base_per_ns=-1.0))
    _raises_exact(ValueError, "gamma_phi_sensitivity must be finite, got inf",
                  lambda: SourceCouplingConfig(gamma_phi_sensitivity=float("inf")))
    _raises_exact(ValueError, "detuning_base_radns must be finite, got nan",
                  lambda: SourceCouplingConfig(detuning_base_radns=float("nan")))
    _raises_exact(ValueError, "drive_omega_base_radns must be >= 0, got -0.1",
                  lambda: SourceCouplingConfig(drive_omega_base_radns=-0.1))
    _raises_exact(ValueError, "drive_omega_sensitivity must be finite, got inf",
                  lambda: SourceCouplingConfig(drive_omega_sensitivity=float("inf")))
    # probability-base loop: trip EACH of the four tuple entries (kills tuple-content mutations)
    _raises_exact(ValueError, "spillover_base_p must be in [0, 1), got 1.5",
                  lambda: SourceCouplingConfig(spillover_base_p=1.5))
    _raises_exact(ValueError, "readout_flip_base_p must be in [0, 1), got 1.0",
                  lambda: SourceCouplingConfig(readout_flip_base_p=1.0))
    _raises_exact(ValueError, "reset_flip_base_p must be in [0, 1), got -0.1",
                  lambda: SourceCouplingConfig(reset_flip_base_p=-0.1))
    _raises_exact(ValueError, "cz_depol_base_p must be in [0, 1), got 1.0",
                  lambda: SourceCouplingConfig(cz_depol_base_p=1.0))
    # sensitivity loop: trip each tuple entry
    _raises_exact(ValueError, "spillover_sensitivity must be finite, got inf",
                  lambda: SourceCouplingConfig(spillover_sensitivity=float("inf")))
    _raises_exact(ValueError, "readout_flip_sensitivity must be finite, got nan",
                  lambda: SourceCouplingConfig(readout_flip_sensitivity=float("nan")))
    _raises_exact(ValueError, "reset_flip_sensitivity must be finite, got inf",
                  lambda: SourceCouplingConfig(reset_flip_sensitivity=float("inf")))
    _raises_exact(ValueError, "cz_depol_sensitivity must be finite, got inf",
                  lambda: SourceCouplingConfig(cz_depol_sensitivity=float("inf")))


def test_L0_source_coupling_config_to_manifest_all_keys_distinct():
    m = _DISTINCT_CFG.to_manifest()
    assert set(m) == {"schema", "epistemic_class", "z_scale_radns", "zz", "gamma_phi_base_per_ns",
                      "gamma_phi_sensitivity", "detuning_base_radns", "drive_omega_base_radns",
                      "drive_omega_sensitivity", "spillover_base_p", "spillover_sensitivity",
                      "readout_flip_base_p", "readout_flip_sensitivity", "reset_flip_base_p",
                      "reset_flip_sensitivity", "cz_depol_base_p", "cz_depol_sensitivity"}
    assert m["schema"] == "error_coupling_simulator.source.coupling_config.v2"
    assert m["epistemic_class"] == {"static_zz_formula": "a",
                                    "constants_and_sensitivities": "c",
                                    "log_rate_and_logit_maps": "c"}
    assert m["zz"] == _DISTINCT_CFG.zz.to_manifest()
    # each scalar routed to the RIGHT key (all inputs distinct -> a swap diverges)
    expected = {
        "z_scale_radns": 1.1e-4, "gamma_phi_base_per_ns": 2.2e-5, "gamma_phi_sensitivity": 0.31,
        "detuning_base_radns": 0.13, "drive_omega_base_radns": 0.17, "drive_omega_sensitivity": 0.19,
        "spillover_base_p": 1.1e-3, "spillover_sensitivity": 0.23,
        "readout_flip_base_p": 1.2e-2, "readout_flip_sensitivity": 0.29,
        "reset_flip_base_p": 5.3e-3, "reset_flip_sensitivity": 0.37,
        "cz_depol_base_p": 2.4e-3, "cz_depol_sensitivity": 0.41,
    }
    for key, val in expected.items():
        assert_pins(m[key], val, rtol=1e-12, atol=0.0, label=f"m[{key}]")


def test_source_coupling_config_snapshots_mutable_numeric_inputs():
    sensitivity = np.asarray(0.35)
    schema = np.asarray("error_coupling_simulator.source.coupling_config.v2")
    cfg = SourceCouplingConfig(
        gamma_phi_sensitivity=sensitivity,
        schema=schema,
    )
    sensitivity[...] = math.inf
    schema[...] = "invalid"
    assert cfg.gamma_phi_sensitivity == 0.35
    assert cfg.schema == "error_coupling_simulator.source.coupling_config.v2"
    assert math.isfinite(cfg.to_manifest()["gamma_phi_sensitivity"])


# =========================================================================== #
# CoupledNoiseParameters -- source_draw_for + to_manifest                     #
# =========================================================================== #
def test_L0_coupled_params_source_draw_for_value_and_keyerror():
    p = source_to_params(3e-5, SourceCouplingConfig())
    for k in _SOURCE_KEYS:
        assert_pins(p.source_draw_for(k), 3e-5, rtol=1e-12, atol=1e-18, label=f"draw {k}")
    _raises_exact(KeyError, repr("nope"), lambda: p.source_draw_for("nope"))


def test_L0_coupled_params_to_manifest_routes_each_field():
    cfg = SourceCouplingConfig(z_scale_radns=1e-4, gamma_phi_sensitivity=0.4,
                               drive_omega_sensitivity=0.3)
    p = source_to_params(2e-5, cfg)
    m = p.to_manifest()
    assert set(m) == {"schema", "coupling_mode", "source_draws_radns", "normalized_draws",
                      "zz_phi_rad", "zz_zeta_radns", "zz_exchange_j_radns", "gamma_phi_per_ns",
                      "tphi_ns", "detuning_radns", "drive_omega_radns", "spillover_cx",
                      "readout_flip_p", "reset_flip_p", "cz_depol_p"}
    assert m["schema"] == "error_coupling_simulator.source.coupled_process_params.v2"
    assert m["coupling_mode"] == "shared"
    assert m["source_draws_radns"] == {k: 2e-5 for k in _SOURCE_KEYS}
    assert m["normalized_draws"] == {k: 2e-5 / 1e-4 for k in _SOURCE_KEYS}
    # every scalar key routed to its (distinct-valued) attr -> a swap diverges
    for key in ("zz_phi_rad", "zz_zeta_radns", "zz_exchange_j_radns", "gamma_phi_per_ns",
                "tphi_ns", "detuning_radns", "drive_omega_radns", "spillover_cx",
                "readout_flip_p", "reset_flip_p", "cz_depol_p"):
        assert_pins(m[key], getattr(p, key), rtol=1e-12, atol=0.0, label=f"m[{key}]")


def test_L0_coupled_params_emission_boundary_rejects_nonfinite_and_bad_tphi_relation():
    positive = source_to_params(0.0)
    _raises_exact(
        ValueError,
        "detuning_radns must be finite at the coupling emission boundary, got inf",
        lambda: dataclasses.replace(positive, detuning_radns=math.inf),
    )
    _raises_exact(
        ValueError,
        "zz must be finite at the coupling emission boundary, got nan",
        lambda: dataclasses.replace(
            positive,
            source_draws_radns=(("zz", math.nan),) + positive.source_draws_radns[1:],
        ),
    )
    zero = source_to_params(
        0.0,
        SourceCouplingConfig(
            gamma_phi_base_per_ns=0.0,
            gamma_phi_sensitivity=0.0,
        ),
    )
    assert zero.gamma_phi_per_ns == 0.0 and zero.tphi_ns == math.inf
    _raises_exact(
        ValueError,
        "tphi_ns must be +inf when gamma_phi_per_ns is structural zero",
        lambda: dataclasses.replace(zero, tphi_ns=1.0),
    )
    _raises_exact(
        ValueError,
        "tphi_ns must be finite and > 0 when gamma_phi_per_ns is positive",
        lambda: dataclasses.replace(positive, tphi_ns=math.inf),
    )
    _raises_exact(
        ValueError,
        "gamma_phi_per_ns must be >= 0 at the coupling emission boundary",
        lambda: dataclasses.replace(positive, gamma_phi_per_ns=-1.0),
    )
    _raises_exact(
        ValueError,
        "tphi_ns must equal 1 / gamma_phi_per_ns at the coupling emission boundary",
        lambda: dataclasses.replace(positive, gamma_phi_per_ns=2.0, tphi_ns=1.0),
    )


def test_coupled_params_snapshot_mutable_draws_and_numeric_scalars():
    positive = source_to_params(0.0)
    draws = list(positive.source_draws_radns)
    detuning = np.asarray(0.0)
    coupling_mode = np.asarray("shared")
    snapshotted = dataclasses.replace(
        positive,
        source_draws_radns=draws,
        normalized_draws=list(positive.normalized_draws),
        detuning_radns=detuning,
        coupling_mode=coupling_mode,
    )
    draws[0] = ("zz", math.inf)
    detuning[...] = math.inf
    coupling_mode[...] = "invalid"
    manifest = snapshotted.to_manifest()
    assert isinstance(snapshotted.source_draws_radns, tuple)
    assert isinstance(snapshotted.normalized_draws, tuple)
    assert snapshotted.coupling_mode == "shared"
    assert manifest["source_draws_radns"]["zz"] == 0.0
    assert manifest["detuning_radns"] == 0.0


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("zz_exchange_j_radns", -1.0),
        ("drive_omega_radns", -1.0),
        ("spillover_cx", -1.0),
        ("readout_flip_p", 1.0),
        ("reset_flip_p", -1.0),
        ("cz_depol_p", 1.0),
    ),
)
def test_coupled_params_emission_boundary_rejects_invalid_physical_domains(field_name, value):
    positive = source_to_params(0.0)
    suffix = (
        "must be >= 0 at the coupling emission boundary"
        if field_name in {"zz_exchange_j_radns", "drive_omega_radns"}
        else "must be in [0, 1) at the coupling emission boundary"
    )
    _raises_exact(
        ValueError,
        f"{field_name} {suffix}, got {value!r}",
        lambda: dataclasses.replace(positive, **{field_name: value}),
    )


def test_coupled_params_emission_boundary_rejects_invalid_mode_and_draw_keys():
    positive = source_to_params(0.0)
    _raises_exact(
        ValueError,
        "coupling_mode must be 'shared' or 'independent', got 'invalid'",
        lambda: dataclasses.replace(positive, coupling_mode="invalid"),
    )
    _raises_exact(
        ValueError,
        "source_draws_radns must contain each source key exactly once in canonical order",
        lambda: dataclasses.replace(
            positive,
            source_draws_radns=positive.source_draws_radns[:-1],
        ),
    )
    _raises_exact(
        ValueError,
        "normalized_draws must contain each source key exactly once in canonical order",
        lambda: dataclasses.replace(
            positive,
            normalized_draws=positive.normalized_draws[:-1]
            + (positive.normalized_draws[0],),
        ),
    )


# =========================================================================== #
# PRIVATE HELPERS -- direct value-pins + exact-message raises (mutation teeth)  #
# =========================================================================== #
def test_private_params_from_draws_routes_each_key_to_its_field():
    zscale = 1e-4
    cfg = SourceCouplingConfig(
        z_scale_radns=zscale, gamma_phi_base_per_ns=2e-5, gamma_phi_sensitivity=0.4,
        detuning_base_radns=0.11, drive_omega_base_radns=0.2, drive_omega_sensitivity=0.3,
        spillover_base_p=1e-3, spillover_sensitivity=0.2,
        readout_flip_base_p=1e-2, readout_flip_sensitivity=0.4,
        reset_flip_base_p=5e-3, reset_flip_sensitivity=0.35,
        cz_depol_base_p=2e-3, cz_depol_sensitivity=0.3)
    # DISTINCT draw per key -> a wrong-key route (draws["readout"]->draws["reset"], ...) diverges
    draws = {"zz": 1e-5, "gamma_phi": 2e-5, "detuning": 3e-5, "drive": 4e-5, "spillover": 5e-5,
             "readout": 6e-5, "reset": 7e-5, "cz": 8e-5}
    p = coupling._params_from_draws(draws, cfg, coupling_mode="shared")
    assert p.coupling_mode == "shared"
    assert dict(p.source_draws_radns) == draws
    assert p.normalized_draws == tuple((k, draws[k] / zscale) for k in _SOURCE_KEYS)
    assert_pins(p.zz_zeta_radns, _indep_zeta(_BASE_DELTA + 1e-5, _ALPHA, _J_DEFAULT), rtol=1e-9,
                atol=0.0, label="zeta<-zz")
    assert_pins(p.zz_phi_rad, _indep_zeta(_BASE_DELTA + 1e-5, _ALPHA, _J_DEFAULT) * 25.0 / 4.0,
                rtol=1e-9, atol=0.0, label="phi<-zz")
    assert_pins(p.zz_exchange_j_radns, _J_DEFAULT, rtol=1e-9, atol=0.0, label="exchange_j")
    assert_pins(p.gamma_phi_per_ns, _indep_pos_rate(2e-5, 2e-5 / zscale, 0.4), rtol=1e-12, atol=0.0,
                label="gamma<-gamma_phi")
    assert_pins(p.tphi_ns, 1.0 / _indep_pos_rate(2e-5, 2e-5 / zscale, 0.4), rtol=1e-12, atol=0.0,
                label="tphi")
    assert_pins(p.detuning_radns, 0.11 + 3e-5, rtol=1e-12, atol=0.0, label="detuning<-detuning")
    assert_pins(p.drive_omega_radns, _indep_pos_rate(0.2, 4e-5 / zscale, 0.3), rtol=1e-12, atol=0.0,
                label="drive<-drive")
    assert_pins(p.spillover_cx, _indep_prob_logit(1e-3, 5e-5 / zscale, 0.2), rtol=1e-12, atol=0.0,
                label="spillover<-spillover")
    assert_pins(p.readout_flip_p, _indep_prob_logit(1e-2, 6e-5 / zscale, 0.4), rtol=1e-12, atol=0.0,
                label="readout<-readout")
    assert_pins(p.reset_flip_p, _indep_prob_logit(5e-3, 7e-5 / zscale, 0.35), rtol=1e-12, atol=0.0,
                label="reset<-reset")
    assert_pins(p.cz_depol_p, _indep_prob_logit(2e-3, 8e-5 / zscale, 0.3), rtol=1e-12, atol=0.0,
                label="cz<-cz")


def test_private_params_from_draws_rejects_nonfinite_draw():
    cfg = SourceCouplingConfig()
    draws = {k: 1e-5 for k in _SOURCE_KEYS}
    draws["detuning"] = float("nan")
    _raises_exact(ValueError, "draws_radns[detuning] must be finite, got nan",
                  lambda: coupling._params_from_draws(draws, cfg, coupling_mode="shared"))


def test_private_modulate_positive_rate_paths():
    assert_pins(coupling._modulate_positive_rate(1e-4, 3.0, 0.5, name="r"),
                _indep_pos_rate(1e-4, 3.0, 0.5), rtol=1e-12, atol=0.0, label="posrate normal")
    # Exact zero shift is the structural identity, independent of which factor made it zero.
    assert coupling._modulate_positive_rate(0.0, 5.0, 0.0, name="r") == 0.0
    assert coupling._modulate_positive_rate(0.0, 0.0, 0.5, name="r") == 0.0
    # A zero base with a genuinely nonzero shift cannot be modulated.
    _raises_exact(ValueError, "r: nonzero sensitivity cannot modulate a zero base rate",
                  lambda: coupling._modulate_positive_rate(0.0, 1.0, 0.5, name="r"))
    # base guard
    _raises_exact(ValueError, "r.base must be >= 0, got -1.0",
                  lambda: coupling._modulate_positive_rate(-1.0, 0.0, 0.0, name="r"))
    # the '.sensitivity' / '.x' names are load-bearing (kill name-arg mutations in the finite guards)
    _raises_exact(ValueError, "r.sensitivity must be finite, got inf",
                  lambda: coupling._modulate_positive_rate(1e-4, 0.0, float("inf"), name="r"))
    _raises_exact(ValueError, "r.x must be finite, got inf",
                  lambda: coupling._modulate_positive_rate(1e-4, float("inf"), 0.5, name="r"))
    # A comparison threshold cannot define a structural zero.
    assert coupling._modulate_positive_rate(1e-12, 5.0, 0.0, name="r") == 1e-12
    _raises_exact(ValueError, "r: nonzero sensitivity cannot modulate a zero base rate",
                  lambda: coupling._modulate_positive_rate(0.0, 5.0, 1e-12, name="r"))
    _raises_exact(ValueError, "r: sensitivity*x is not representable as a finite float64",
                  lambda: coupling._modulate_positive_rate(1.0, 1e308, 2.0, name="r"))
    _raises_exact(ValueError, "r: sensitivity*x is not representable as a finite float64",
                  lambda: coupling._modulate_positive_rate(1.0, 0.5,
                                                            math.nextafter(0.0, 1.0), name="r"))
    message = "r: modulated positive rate is not representable"
    _raises_exact(ValueError, message,
                  lambda: coupling._modulate_positive_rate(1e-4, 1e6, 1.0, name="r"))
    _raises_exact(ValueError, message,
                  lambda: coupling._modulate_positive_rate(1e-4, -1e6, 1.0, name="r"))
    # exp(shift) reaches an endpoint, but the final product is representable in both directions.
    assert coupling._modulate_positive_rate(1e-300, 710.0, 1.0, name="r") > 0.0
    assert coupling._modulate_positive_rate(1e300, -1000.0, 1.0, name="r") > 0.0


def test_private_modulate_probability_logit_paths():
    assert_pins(coupling._modulate_probability_logit(0.01, 3.0, 0.4, name="p"),
                _indep_prob_logit(0.01, 3.0, 0.4), rtol=1e-12, atol=0.0, label="logit normal")
    # Exact zero shift is the structural identity, independent of which factor made it zero.
    assert coupling._modulate_probability_logit(0.0, 5.0, 0.0, name="p") == 0.0
    assert coupling._modulate_probability_logit(0.0, 0.0, 0.5, name="p") == 0.0
    # A zero base with a genuinely nonzero shift cannot be logit-modulated.
    _raises_exact(ValueError, "p: nonzero sensitivity cannot logit-modulate p=0",
                  lambda: coupling._modulate_probability_logit(0.0, 1.0, 0.5, name="p"))
    # base_p out of range -> _validate_probability raises (carrying the '.base_p' name)
    _raises_exact(ValueError, "p.base_p must be in [0, 1), got 1.5",
                  lambda: coupling._modulate_probability_logit(1.5, 0.0, 0.0, name="p"))
    # the '.sensitivity' / '.x' names are load-bearing (kill name-arg mutations in the finite guards)
    _raises_exact(ValueError, "p.sensitivity must be finite, got inf",
                  lambda: coupling._modulate_probability_logit(0.5, 0.0, float("inf"), name="p"))
    _raises_exact(ValueError, "p.x must be finite, got inf",
                  lambda: coupling._modulate_probability_logit(0.5, float("inf"), 0.5, name="p"))
    assert coupling._modulate_probability_logit(1e-12, 5.0, 0.0, name="p") == 1e-12
    _raises_exact(ValueError, "p: nonzero sensitivity cannot logit-modulate p=0",
                  lambda: coupling._modulate_probability_logit(0.0, 5.0, 1e-12, name="p"))
    _raises_exact(ValueError, "p: sensitivity*x is not representable as a finite float64",
                  lambda: coupling._modulate_probability_logit(0.5, 1e308, 2.0, name="p"))
    _raises_exact(ValueError, "p: sensitivity*x is not representable as a finite float64",
                  lambda: coupling._modulate_probability_logit(
                      0.5, 0.5, math.nextafter(0.0, 1.0), name="p"
                  ))
    # A near-one input is mapped from its real value; it is never pre-clamped.
    assert_pins(coupling._modulate_probability_logit(1.0 - 1e-13, 2.0, 0.3, name="p"),
                _indep_prob_logit(1.0 - 1e-13, 2.0, 0.3), rtol=0.0, atol=1e-14,
                label="near-one logit")
    message = "p: modulated probability is outside the representable float64 open interval"
    _raises_exact(ValueError, message,
                  lambda: coupling._modulate_probability_logit(0.5, 1e6, 1.0, name="p"))
    _raises_exact(ValueError, message,
                  lambda: coupling._modulate_probability_logit(0.5, -1e6, 1.0, name="p"))


def test_probability_logit_large_opposite_terms_match_exact_float_oracle():
    """A rounded ``logit + shift`` intermediate must not erase a representable result."""

    base_p = float.fromhex("0x0.0000000000001p-1022")
    shift = float.fromhex("0x1.74385446d71c3p+9")
    with mpmath.workdps(200):
        exact_logit = mpmath.log(_mp_float(base_p) / (1 - _mp_float(base_p)))
        oracle = float(1 / (1 + mpmath.exp(-(exact_logit + _mp_float(shift)))))
    got = coupling._modulate_probability_logit(base_p, shift, 1.0, name="p")
    assert _ulp_distance(got, oracle) <= 1


def test_probability_logit_classifies_cancellation_at_exact_open_domain_boundaries():
    """Boundary classification follows the exact-float formula, not rounded ``logit + shift``."""

    min_open = float.fromhex("0x0.0000000000001p-1022")
    max_open = float.fromhex("0x1.fffffffffffffp-1")
    cancelling_shift = float.fromhex("0x1.8696a3c1fe543p+9")

    assert (
        coupling._modulate_probability_logit(
            min_open, cancelling_shift, 1.0, name="p"
        )
        == max_open
    )
    assert (
        coupling._modulate_probability_logit(
            max_open, -cancelling_shift, 1.0, name="p"
        )
        == min_open
    )
    outside_shift = math.nextafter(cancelling_shift, math.inf)
    with pytest.raises(ValueError, match="outside the representable float64 open interval"):
        coupling._modulate_probability_logit(
            min_open, outside_shift, 1.0, name="p"
        )
    with pytest.raises(ValueError, match="outside the representable float64 open interval"):
        coupling._modulate_probability_logit(
            max_open, -outside_shift, 1.0, name="p"
        )


def test_coupled_parameter_bundle_rejects_finite_inputs_that_emit_infinity():
    """Every finite input bundle must fail closed before a non-finite manifest is emitted."""

    largest = sys.float_info.max
    cfg = SourceCouplingConfig(
        z_scale_radns=largest,
        detuning_base_radns=largest,
    )
    draws = {key: 0.0 for key in _SOURCE_KEYS}
    draws["detuning"] = largest
    _raises_exact(
        ValueError,
        "detuning_radns must be finite at the coupling emission boundary, got inf",
        lambda: coupling._params_from_draws(draws, cfg, coupling_mode="shared"),
    )


def test_modulation_maps_match_mpmath_on_interior_and_float64_boundaries():
    """Old/new agree in the interior; mpmath owns endpoints and recovery accuracy."""

    p_min = math.nextafter(0.0, 1.0)
    p_max = math.nextafter(1.0, 0.0)
    y_min = math.log(p_min) - math.log1p(-p_min)
    y_max = math.log(p_max) - math.log1p(-p_max)

    with mpmath.workdps(200):
        for boundary, direction, expected in (
            (y_min, math.inf, p_min),
            (y_max, -math.inf, p_max),
        ):
            inside = math.nextafter(boundary, direction)
            for y in (boundary, inside):
                got = coupling._modulate_probability_logit(0.5, y, 1.0, name="p")
                oracle = float(1 / (1 + mpmath.exp(-_mp_float(y))))
                assert got == expected
                assert _ulp_distance(got, oracle) <= 1

        lower_outside = math.nextafter(y_min, -math.inf)
        upper_outside = math.nextafter(y_max, math.inf)
        message = "p: modulated probability is outside the representable float64 open interval"
        _raises_exact(ValueError, message,
                      lambda: coupling._modulate_probability_logit(0.5, lower_outside, 1.0, name="p"))
        _raises_exact(ValueError, message,
                      lambda: coupling._modulate_probability_logit(0.5, upper_outside, 1.0, name="p"))

        interior_shifts = np.concatenate(
            (-np.geomspace(1e-12, 30.0, 25), np.asarray([0.0]), np.geomspace(1e-12, 30.0, 25))
        )
        for y in interior_shifts:
            y = float(y)
            got = coupling._modulate_probability_logit(0.5, y, 1.0, name="p")
            oracle = float(1 / (1 + mpmath.exp(-_mp_float(y))))
            legacy = 1.0 / (1.0 + math.exp(-y))
            assert _ulp_distance(got, oracle) <= 1
            assert _ulp_distance(got, legacy) <= 2

        for base in np.geomspace(1e-200, 1e200, 17):
            for shift in interior_shifts:
                base = float(base)
                shift = float(shift)
                legacy = base * math.exp(shift)
                if not math.isfinite(legacy) or legacy <= 0.0:
                    continue
                got = coupling._modulate_positive_rate(base, shift, 1.0, name="r")
                oracle = float(_mp_float(base) * mpmath.exp(_mp_float(shift)))
                assert got == legacy
                assert _ulp_distance(got, oracle) <= 2

        fallback_domains = (
            ((float(base), 710.0) for base in np.geomspace(1e-308, 1e-260, 17)),
            ((float(base), -1000.0) for base in np.geomspace(1e250, 1e308, 17)),
        )
        for domain in fallback_domains:
            for base, shift in domain:
                got = coupling._modulate_positive_rate(base, shift, 1.0, name="r")
                oracle = float(_mp_float(base) * mpmath.exp(_mp_float(shift)))
                legacy_capped = base * math.exp(max(-60.0, min(60.0, shift)))
                assert _ulp_distance(got, oracle) <= 1
                assert got != legacy_capped


def test_positive_rate_rejects_subnormal_exp_intermediate_as_a_direct_result():
    """A low-precision subnormal exp intermediate must route through accurate range reduction."""

    base = 1.67e260
    poisoned_shift = -744.86
    poisoned_direct = base * math.exp(poisoned_shift)
    assert 0.0 < math.exp(poisoned_shift) < sys.float_info.min
    with mpmath.workdps(200):
        oracle = float(_mp_float(base) * mpmath.exp(_mp_float(poisoned_shift)))
        assert abs(poisoned_direct - oracle) / oracle > 0.5
        got = coupling._modulate_positive_rate(base, poisoned_shift, 1.0, name="r")
        assert got != poisoned_direct
        assert _ulp_distance(got, oracle) <= 1

        first_positive_shift = math.nextafter(
            math.log(math.nextafter(0.0, 1.0)) - math.log(2.0),
            math.inf,
        )
        last_subnormal_shift = math.nextafter(math.log(sys.float_info.min), -math.inf)
        for shift in np.linspace(first_positive_shift, last_subnormal_shift, 311):
            shift = float(shift)
            exp_shift = math.exp(shift)
            assert 0.0 < exp_shift < sys.float_info.min
            oracle = float(_mp_float(base) * mpmath.exp(_mp_float(shift)))
            assert math.isfinite(oracle) and oracle >= sys.float_info.min
            got = coupling._modulate_positive_rate(base, shift, 1.0, name="r")
            assert _ulp_distance(got, oracle) <= 1


def test_private_as_1d_finite_valid_and_guards():
    out = coupling._as_1d_finite("v", [1.0, 2.0, 3.0])
    assert out.dtype == np.float64 and out.tolist() == [1.0, 2.0, 3.0]
    # dtype is load-bearing: an INTEGER input must still coerce to float64 (kills dtype=np.float64
    # -> None / omitted, which would infer int64 for integer input).
    assert coupling._as_1d_finite("v", [1, 2, 3]).dtype == np.float64
    _raises_exact(ValueError, "v must be a non-empty 1-D trajectory",
                  lambda: coupling._as_1d_finite("v", []))
    _raises_exact(ValueError, "v must be a non-empty 1-D trajectory",
                  lambda: coupling._as_1d_finite("v", np.zeros((2, 2))))
    _raises_exact(ValueError, "v contains non-finite values",
                  lambda: coupling._as_1d_finite("v", [1.0, np.inf]))


def test_private_require_and_validate_helpers():
    assert coupling._require_finite("x", 1.5) == 1.5
    _raises_exact(ValueError, "x must be finite, got nan", lambda: coupling._require_finite("x", float("nan")))
    assert coupling._require_positive("x", 2.0) == 2.0
    _raises_exact(ValueError, "x must be > 0, got 0.0", lambda: coupling._require_positive("x", 0.0))
    # non-finite routes through _require_finite with the SAME name (kills the name->None mutant)
    _raises_exact(ValueError, "x must be finite, got inf", lambda: coupling._require_positive("x", float("inf")))
    assert coupling._require_nonnegative("x", 0.0) == 0.0
    _raises_exact(ValueError, "x must be >= 0, got -0.1", lambda: coupling._require_nonnegative("x", -0.1))
    _raises_exact(ValueError, "x must be finite, got nan",
                  lambda: coupling._require_nonnegative("x", float("nan")))
    # _validate_probability: both operands of `not lo_ok or v >= 1.0`
    assert coupling._validate_probability("p", 0.0, allow_zero=True) == 0.0
    assert coupling._validate_probability("p", 0.3, allow_zero=False) == 0.3
    _raises_exact(ValueError, "p must be in (0, 1), got 0.0",
                  lambda: coupling._validate_probability("p", 0.0, allow_zero=False))
    _raises_exact(ValueError, "p must be in [0, 1), got 1.0",           # kills `or`->`and`
                  lambda: coupling._validate_probability("p", 1.0, allow_zero=True))
    _raises_exact(ValueError, "p must be in [0, 1), got -0.1",          # not-lo_ok operand
                  lambda: coupling._validate_probability("p", -0.1, allow_zero=True))
    _raises_exact(ValueError, "p must be finite, got nan",
                  lambda: coupling._validate_probability("p", float("nan"), allow_zero=True))


# =========================================================================== #
# residual killers: exact-1e-12 boundaries + name-in-message + int-dtype        #
# =========================================================================== #
def test_L0_exchange_j_from_phi_tiny_positive_phi_not_rejected():
    # J2 in (0, NUMERICAL_ZERO): the `J2 < -NZ` guard must NOT fire (kills `-NZ` -> `+NZ`)
    j = exchange_j_from_phi(5e-14, delta_radns=3.0, alpha_radns=1.0, t_gate_ns=1.0)
    assert_pins(j, _indep_exchange_j(5e-14, 3.0, 1.0, 1.0), rtol=1e-12, atol=0.0, label="tiny J")
    assert j > 0.0


def test_L0_source_to_params_zeroed_base_names_surface_in_message():
    # each Theta->field name is load-bearing: zero one base (its default sensitivity is nonzero)
    # and the shared fan-out raises with the field's EXACT name -> kills the name-string mutations
    # inside _params_from_draws' _modulate_* calls.
    _raises_exact(ValueError,
                  "drive_omega_radns: nonzero sensitivity cannot modulate a zero base rate",
                  lambda: source_to_params(1e-4, SourceCouplingConfig(drive_omega_base_radns=0.0)))
    _raises_exact(ValueError, "spillover_cx: nonzero sensitivity cannot logit-modulate p=0",
                  lambda: source_to_params(1e-4, SourceCouplingConfig(spillover_base_p=0.0)))
    _raises_exact(ValueError, "reset_flip_p: nonzero sensitivity cannot logit-modulate p=0",
                  lambda: source_to_params(1e-4, SourceCouplingConfig(reset_flip_base_p=0.0)))
    _raises_exact(ValueError, "cz_depol_p: nonzero sensitivity cannot logit-modulate p=0",
                  lambda: source_to_params(1e-4, SourceCouplingConfig(cz_depol_base_p=0.0)))


def test_L0_drift_to_t2_zeroed_base_name_surfaces_in_message():
    # gamma_phi_per_ns name is load-bearing (kills the name-string mutations threaded by drift_to_t2)
    _raises_exact(ValueError,
                  "gamma_phi_per_ns: nonzero sensitivity cannot modulate a zero base rate",
                  lambda: drift_to_t2(1e-4, SourceCouplingConfig(gamma_phi_base_per_ns=0.0,
                                                                 gamma_phi_sensitivity=0.5)))


def test_axis2_source_contract_has_no_unimplemented_qutrit_leakage_bridge():
    """The source owner must not emit parameters for the separately owned qutrit route."""

    forbidden_fragments = ("wg", "leak", "seep")
    config_fields = {item.name for item in dataclasses.fields(SourceCouplingConfig)}
    parameter_fields = {item.name for item in dataclasses.fields(CoupledNoiseParameters)}
    assert not any(
        fragment in field_name
        for field_name in config_fields | parameter_fields
        for fragment in forbidden_fragments
    )
    params = source_to_params(0.0)
    manifest_keys = set(params.to_manifest())
    draw_keys = {name for name, _value in params.source_draws_radns}
    assert not any(
        fragment in field_name
        for field_name in manifest_keys | draw_keys
        for fragment in forbidden_fragments
    )
    assert not hasattr(coupling, "leakage_from_drift")
    assert not hasattr(source_api, "leakage_from_drift")
