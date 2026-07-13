"""Stage-D batch ``source_coupling`` -- per-unit L0+L1+L2 coverage of
``error_coupling_simulator.source.coupling`` (20 CPU-pure public units; no GPU, no quimb,
so out_of_scope is empty).

Full-coverage program (docs/twin_validation/wave2_6_unit_test_contract.md SS12.3/12.4;
work-list docs/twin_validation/l3_release_package_unit_inventory.md D12).
``source/coupling.py`` owns the Axis-2 shared-source parameter fan-out ``Theta(z_t)``: one
explicit source draw conditions many mechanism parameters in the SAME cycle -- the static-ZZ
frequency-drift closed form, the positive-rate exp maps (gamma_phi, drive_omega, the P2-i
Theta->leakage cell), and the logit maps (spillover, readout, reset, cz). It is a parameter
LAYER, not a Stim/DEM noise layer nor a channel assembler.

L2 DISCIPLINE (the standing lesson: 100% coverage != discrimination). This is closed-form
physics, so value-pins are the workhorse: every load-bearing number is PINNED against an
INDEPENDENT from-scratch recompute of the analytic formula (the dispersive static-ZZ cross-Kerr
``zeta = 2 J^2 [1/(D-a) - 1/(D+a)]``, the ``phi = zeta(J)*t_gate/4`` inversion + its EXACT
round-trip, the positive-rate ``base*exp(clamp(sens*x))`` map, the logit map, and a from-scratch
Pearson recompute for ``cross_mechanism_correlation``) -- NEVER the module's own helper. No
numerical-convergence parameter is load-bearing (every map is analytic), so no pin is slow.
Every validation RAISE asserts its EXACT message via ``str(excinfo.value) == ...`` (mutmut wraps/
roundtrips string literals -- a substring ``match=`` still passes them, exact-equality kills them).
``assert_discriminates`` gives each closed-form invariant a demonstrated sabotage variant it rejects.
"""
from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from _support.faithfulness import assert_discriminates, assert_pins

import error_coupling_simulator.source.coupling as coupling
from error_coupling_simulator.source.coupling import (
    CoupledMechanismParams,
    SourceCouplingConfig,
    StaticZZCalibration,
    cross_mechanism_correlation,
    default_source_coupling_config,
    drift_to_t2,
    exchange_j_from_phi,
    independent_baseline_trajectory_to_params,
    leakage_from_drift,
    parameter_series,
    source_to_params,
    static_zz_zeta,
    trajectory_to_params,
    zz_phi_from_frequency_drift,
)

_TWO_PI = 2.0 * math.pi
_SOURCE_KEYS = ("zz", "gamma_phi", "detuning", "drive", "spillover", "readout", "reset",
                "cz", "wg_theta", "wg_seep")

# default StaticZZCalibration constants (used by the default config's zz)
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
    """base*exp(clamp(sens*x, -60, 60)) for base>0 (the module's positive-rate exp map)."""
    expo = max(-60.0, min(60.0, sens * x))
    return base * math.exp(expo)


def _indep_prob_logit(p: float, x: float, sens: float) -> float:
    """The logit-domain probability map, recomputed from scratch (p>0 assumed)."""
    p = min(max(p, 1e-12), 1.0 - 1e-12)
    logit = math.log(p / (1.0 - p))
    y = max(-60.0, min(60.0, logit + sens * x))
    return 1.0 / (1.0 + math.exp(-y))


def _indep_pearson(a, b) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    am = a - a.mean()
    bm = b - b.mean()
    denom = math.sqrt(float((am * am).sum()) * float((bm * bm).sum()))
    if denom == 0.0:
        return 0.0
    return float((am * bm).sum() / denom)


#: default zz exchange J, recomputed independently (matches cfg.zz.exchange_j_radns).
_J_DEFAULT = _indep_exchange_j(1.6e-4, _BASE_DELTA, _ALPHA, 25.0)


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


@settings(max_examples=200, deadline=None)
@given(d=st.floats(-6.0, 6.0, allow_nan=False, allow_infinity=False),
       a=st.floats(-3.0, 3.0, allow_nan=False, allow_infinity=False),
       j=st.floats(0.0, 4.0, allow_nan=False, allow_infinity=False))
def test_L1_static_zz_zeta_matches_independent(d, a, j):
    if abs(d - a) < 1e-3 or abs(d + a) < 1e-3:      # avoid the singular guard
        return
    assert_pins(static_zz_zeta(d, a, j), _indep_zeta(d, a, j), rtol=1e-9, atol=1e-18,
                label="zeta")


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
    # zero coefficient: alpha=0 -> zeta(1) == 2*(1/D - 1/D) == 0
    _raises_exact(ValueError, "cannot infer exchange J because zeta coefficient is zero",
                  lambda: exchange_j_from_phi(1e-4, delta_radns=1.0, alpha_radns=0.0, t_gate_ns=10.0))
    # sign inconsistency: coeff = zeta(1) = 0.5 > 0, phi < 0 -> J2 < 0
    _raises_exact(ValueError,
                  "phi sign is inconsistent with the static-ZZ coefficient; "
                  "phi=-1.0, coeff=0.5, t_gate=1.0",
                  lambda: exchange_j_from_phi(-1.0, delta_radns=3.0, alpha_radns=1.0, t_gate_ns=1.0))


def test_KILLER_exchange_j_from_phi_discriminates():
    phi, d, a, tg = 2e-3, 3.0, 1.0, 10.0

    def prop(j):
        assert_pins(j, _indep_exchange_j(phi, d, a, tg), rtol=1e-12, atol=0.0, label="J")

    # wrong: drop the factor 4 (phi instead of 4*phi in the inversion)
    coeff = _indep_zeta(d, a, 1.0)
    wrong = math.sqrt(max(0.0, phi / (coeff * tg)))
    assert_discriminates(prop, exchange_j_from_phi(phi, delta_radns=d, alpha_radns=a, t_gate_ns=tg),
                         wrong, label="exchange J")


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
# drift_to_t2 (+ the _drift_to_T2 alias)                                       #
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
    # guard
    _raises_exact(ValueError, "z_t_radns must be finite, got nan", lambda: drift_to_t2(float("nan"), cfg))


def test_L0_drift_to_t2_alias_matches_and_config_load_bearing():
    cfg = SourceCouplingConfig(z_scale_radns=2e-4, gamma_phi_sensitivity=0.5)
    assert coupling._drift_to_T2(1e-4, cfg) == drift_to_t2(1e-4, cfg)
    # the alias forwards its config: dropping it (mutant) would use the default -> divergence
    assert coupling._drift_to_T2(1e-4, cfg) != drift_to_t2(1e-4, None)


def test_L0_modulate_positive_rate_exponent_clamp_via_drift():
    # sens*x = 0.5 * (1.0/1e-6) = 5e5 >> 60 -> clamp to +/-60
    cfg = SourceCouplingConfig(z_scale_radns=1e-6, gamma_phi_base_per_ns=1e-4,
                               gamma_phi_sensitivity=0.5)
    g_hi, _ = drift_to_t2(1.0, cfg)
    assert_pins(g_hi, 1e-4 * math.exp(60.0), rtol=1e-12, atol=0.0, label="clamp hi")
    g_lo, _ = drift_to_t2(-1.0, cfg)
    assert_pins(g_lo, 1e-4 * math.exp(-60.0), rtol=1e-12, atol=0.0, label="clamp lo")


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
# leakage_from_drift                                                          #
# =========================================================================== #
def test_L0_leakage_from_drift_value_config_branch_and_inert_default():
    zscale, tb, ts, sb, ss = 1e-4, 5e-3, 0.2, 0.09, 0.3
    cfg = SourceCouplingConfig(z_scale_radns=zscale, wg_theta_base_rad=tb, wg_theta_sensitivity=ts,
                               wg_g_seep_base=sb, wg_g_seep_sensitivity=ss)
    for tz, sz in [(0.0, 0.0), (1e-4, 2e-4), (-1e-4, 3e-4)]:
        theta, gseep = leakage_from_drift(tz, sz, cfg)
        assert_pins(theta, _indep_pos_rate(tb, tz / zscale, ts), rtol=1e-12, atol=0.0, label="theta")
        assert_pins(gseep, _indep_pos_rate(sb, sz / zscale, ss), rtol=1e-12, atol=0.0, label="gseep")
    # off-source identity: Theta(0) returns the configured bases exactly
    theta0, gseep0 = leakage_from_drift(0.0, 0.0, cfg)
    assert_pins(theta0, tb, rtol=1e-12, atol=0.0, label="theta base")
    assert_pins(gseep0, sb, rtol=1e-12, atol=0.0, label="gseep base")
    # default config is fully INERT (base 0 + sens 0) -> (0, 0); also covers config None branch
    assert leakage_from_drift(1e-4, 2e-4, None) == (0.0, 0.0)
    # guards
    _raises_exact(ValueError, "theta_z_radns must be finite, got nan",
                  lambda: leakage_from_drift(float("nan"), 0.0, cfg))
    _raises_exact(ValueError, "seep_z_radns must be finite, got inf",
                  lambda: leakage_from_drift(0.0, float("inf"), cfg))


def test_L0_leakage_from_drift_zero_base_nonzero_sens_raises():
    # base 0 with a nonzero sensitivity is a modelling error -> the positive-rate map raises
    cfg_t = SourceCouplingConfig(wg_theta_base_rad=0.0, wg_theta_sensitivity=0.5)
    _raises_exact(ValueError, "wg_theta_rad: nonzero sensitivity cannot modulate a zero base rate",
                  lambda: leakage_from_drift(1e-4, 0.0, cfg_t))
    cfg_s = SourceCouplingConfig(wg_g_seep_base=0.0, wg_g_seep_sensitivity=0.5)
    _raises_exact(ValueError, "wg_g_seep: nonzero sensitivity cannot modulate a zero base rate",
                  lambda: leakage_from_drift(0.0, 1e-4, cfg_s))


def test_KILLER_leakage_from_drift_discriminates():
    zscale, tb, ts = 1e-4, 5e-3, 0.4
    cfg = SourceCouplingConfig(z_scale_radns=zscale, wg_theta_base_rad=tb, wg_theta_sensitivity=ts,
                               wg_g_seep_base=0.09, wg_g_seep_sensitivity=0.3)
    tz = 2e-4

    def prop(theta):
        assert_pins(theta, _indep_pos_rate(tb, tz / zscale, ts), rtol=1e-12, atol=0.0, label="theta")

    wrong = tb * math.exp(-ts * tz / zscale)          # wrong-sign exponent
    assert_discriminates(prop, leakage_from_drift(tz, 0.0, cfg)[0], wrong, label="leakage theta")


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
    assert cfg.schema == "qec_twin.mechanisms.SourceCouplingConfig.v1"
    # wg leakage fields are inert by default
    assert cfg.wg_theta_base_rad == 0.0 and cfg.wg_g_seep_base == 0.0
    assert cfg.wg_theta_sensitivity == 0.0 and cfg.wg_g_seep_sensitivity == 0.0


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
    # wg leakage inert at default wg fields
    assert p.wg_theta_rad == 0.0 and p.wg_g_seep == 0.0
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
    cfg = SourceCouplingConfig(z_scale_radns=zscale, gamma_phi_sensitivity=0.4,
                               drive_omega_sensitivity=0.4)
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
    _raises_exact(AttributeError, "CoupledMechanismParams has no field 'nope'",
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
# StaticZZCalibration -- __post_init__ + properties + to_manifest              #
# =========================================================================== #
def test_L0_static_zz_calibration_properties_and_post_init():
    zz = StaticZZCalibration()
    assert_pins(zz.base_delta_radns, _TWO_PI * (6.0 - 6.1), rtol=1e-12, atol=0.0, label="base_delta")
    assert_pins(zz.alpha_radns, _TWO_PI * (-300.0) * 1e-3, rtol=1e-12, atol=0.0, label="alpha")
    assert_pins(zz.exchange_j_radns, _J_DEFAULT, rtol=1e-9, atol=0.0, label="exchange_j")
    # a NON-default instance -> the properties genuinely depend on inputs (kill return-constant).
    # constants chosen so Delta != +/- alpha (no singular) AND coeff sign matches base_phi>0.
    zz2 = StaticZZCalibration(omega_a_ghz=6.2, omega_b_ghz=6.1, alpha_mhz=-250.0, t_gate_ns=30.0,
                              base_phi_rad=1.7e-4)
    bd2, al2 = _TWO_PI * (6.2 - 6.1), _TWO_PI * (-250.0) * 1e-3
    assert_pins(zz2.base_delta_radns, bd2, rtol=1e-12, atol=0.0, label="base_delta2")
    assert_pins(zz2.alpha_radns, al2, rtol=1e-12, atol=0.0, label="alpha2")
    assert_pins(zz2.exchange_j_radns, _indep_exchange_j(1.7e-4, bd2, al2, 30.0), rtol=1e-9, atol=0.0,
                label="exchange_j2")
    # __post_init__ guards
    _raises_exact(ValueError, "omega_a_ghz must be finite, got inf",
                  lambda: StaticZZCalibration(omega_a_ghz=float("inf")))
    _raises_exact(ValueError, "omega_b_ghz must be finite, got nan",
                  lambda: StaticZZCalibration(omega_b_ghz=float("nan")))
    _raises_exact(ValueError, "alpha_mhz must be finite, got inf",
                  lambda: StaticZZCalibration(alpha_mhz=float("inf")))
    _raises_exact(ValueError, "t_gate_ns must be > 0, got 0.0",
                  lambda: StaticZZCalibration(t_gate_ns=0.0))
    _raises_exact(ValueError, "base_phi_rad must be finite",
                  lambda: StaticZZCalibration(base_phi_rad=float("inf")))


def test_L0_static_zz_calibration_to_manifest_all_keys_distinct():
    # all-distinct inputs so a key->wrong-attr routing mutation in to_manifest diverges
    zz = StaticZZCalibration(omega_a_ghz=6.2, omega_b_ghz=6.1, alpha_mhz=-250.0, t_gate_ns=30.0,
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


def test_KILLER_static_zz_base_delta_discriminates():
    zz = StaticZZCalibration(omega_a_ghz=6.3, omega_b_ghz=6.05)

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
    cz_depol_base_p=2.4e-3, cz_depol_sensitivity=0.41,
    wg_theta_base_rad=6.0e-3, wg_theta_sensitivity=0.43,
    wg_g_seep_base=0.07, wg_g_seep_sensitivity=0.47)


def test_L0_source_coupling_config_post_init_happy_path_and_guards():
    SourceCouplingConfig()          # default valid construction covers both for-loops + all guards
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
    # sensitivity loop: trip EACH of the six tuple entries
    _raises_exact(ValueError, "spillover_sensitivity must be finite, got inf",
                  lambda: SourceCouplingConfig(spillover_sensitivity=float("inf")))
    _raises_exact(ValueError, "readout_flip_sensitivity must be finite, got nan",
                  lambda: SourceCouplingConfig(readout_flip_sensitivity=float("nan")))
    _raises_exact(ValueError, "reset_flip_sensitivity must be finite, got inf",
                  lambda: SourceCouplingConfig(reset_flip_sensitivity=float("inf")))
    _raises_exact(ValueError, "cz_depol_sensitivity must be finite, got inf",
                  lambda: SourceCouplingConfig(cz_depol_sensitivity=float("inf")))
    _raises_exact(ValueError, "wg_theta_sensitivity must be finite, got inf",
                  lambda: SourceCouplingConfig(wg_theta_sensitivity=float("inf")))
    _raises_exact(ValueError, "wg_g_seep_sensitivity must be finite, got nan",
                  lambda: SourceCouplingConfig(wg_g_seep_sensitivity=float("nan")))
    # trailing nonneg guards
    _raises_exact(ValueError, "wg_theta_base_rad must be >= 0, got -0.1",
                  lambda: SourceCouplingConfig(wg_theta_base_rad=-0.1))
    _raises_exact(ValueError, "wg_g_seep_base must be >= 0, got -0.1",
                  lambda: SourceCouplingConfig(wg_g_seep_base=-0.1))


def test_L0_source_coupling_config_to_manifest_all_keys_distinct():
    m = _DISTINCT_CFG.to_manifest()
    assert set(m) == {"schema", "epistemic_class", "z_scale_radns", "zz", "gamma_phi_base_per_ns",
                      "gamma_phi_sensitivity", "detuning_base_radns", "drive_omega_base_radns",
                      "drive_omega_sensitivity", "spillover_base_p", "spillover_sensitivity",
                      "readout_flip_base_p", "readout_flip_sensitivity", "reset_flip_base_p",
                      "reset_flip_sensitivity", "cz_depol_base_p", "cz_depol_sensitivity",
                      "wg_theta_base_rad", "wg_theta_sensitivity", "wg_g_seep_base",
                      "wg_g_seep_sensitivity"}
    assert m["schema"] == "qec_twin.mechanisms.SourceCouplingConfig.v1"
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
        "wg_theta_base_rad": 6.0e-3, "wg_theta_sensitivity": 0.43,
        "wg_g_seep_base": 0.07, "wg_g_seep_sensitivity": 0.47,
    }
    for key, val in expected.items():
        assert_pins(m[key], val, rtol=1e-12, atol=0.0, label=f"m[{key}]")


# =========================================================================== #
# CoupledMechanismParams -- source_draw_for + to_manifest                      #
# =========================================================================== #
def test_L0_coupled_params_source_draw_for_value_and_keyerror():
    p = source_to_params(3e-5, SourceCouplingConfig())
    for k in _SOURCE_KEYS:
        assert_pins(p.source_draw_for(k), 3e-5, rtol=1e-12, atol=1e-18, label=f"draw {k}")
    _raises_exact(KeyError, repr("nope"), lambda: p.source_draw_for("nope"))


def test_L0_coupled_params_to_manifest_routes_each_field():
    # nonzero wg fields + z != 0 so wg_theta_rad != wg_g_seep and every attr is distinct
    cfg = SourceCouplingConfig(z_scale_radns=1e-4, gamma_phi_sensitivity=0.4,
                               drive_omega_sensitivity=0.3, wg_theta_base_rad=5e-3,
                               wg_theta_sensitivity=0.2, wg_g_seep_base=0.09,
                               wg_g_seep_sensitivity=0.3)
    p = source_to_params(2e-5, cfg)
    m = p.to_manifest()
    assert set(m) == {"schema", "coupling_mode", "source_draws_radns", "normalized_draws",
                      "zz_phi_rad", "zz_zeta_radns", "zz_exchange_j_radns", "gamma_phi_per_ns",
                      "tphi_ns", "detuning_radns", "drive_omega_radns", "spillover_cx",
                      "readout_flip_p", "reset_flip_p", "cz_depol_p", "wg_theta_rad", "wg_g_seep"}
    assert m["schema"] == "qec_twin.mechanisms.CoupledMechanismParams.v1"
    assert m["coupling_mode"] == "shared"
    assert m["source_draws_radns"] == {k: 2e-5 for k in _SOURCE_KEYS}
    assert m["normalized_draws"] == {k: 2e-5 / 1e-4 for k in _SOURCE_KEYS}
    # every scalar key routed to its (distinct-valued) attr -> a swap diverges
    for key in ("zz_phi_rad", "zz_zeta_radns", "zz_exchange_j_radns", "gamma_phi_per_ns",
                "tphi_ns", "detuning_radns", "drive_omega_radns", "spillover_cx",
                "readout_flip_p", "reset_flip_p", "cz_depol_p", "wg_theta_rad", "wg_g_seep"):
        assert_pins(m[key], getattr(p, key), rtol=1e-12, atol=0.0, label=f"m[{key}]")
    # wg_theta_rad and wg_g_seep are genuinely distinct here (guards their manifest swap)
    assert p.wg_theta_rad != p.wg_g_seep


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
        cz_depol_base_p=2e-3, cz_depol_sensitivity=0.3,
        wg_theta_base_rad=5e-3, wg_theta_sensitivity=0.25,
        wg_g_seep_base=0.09, wg_g_seep_sensitivity=0.33)
    # DISTINCT draw per key -> a wrong-key route (draws["readout"]->draws["reset"], ...) diverges
    draws = {"zz": 1e-5, "gamma_phi": 2e-5, "detuning": 3e-5, "drive": 4e-5, "spillover": 5e-5,
             "readout": 6e-5, "reset": 7e-5, "cz": 8e-5, "wg_theta": 9e-5, "wg_seep": 1e-4}
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
    assert_pins(p.wg_theta_rad, _indep_pos_rate(5e-3, 9e-5 / zscale, 0.25), rtol=1e-12, atol=0.0,
                label="wg_theta<-wg_theta")
    assert_pins(p.wg_g_seep, _indep_pos_rate(0.09, 1e-4 / zscale, 0.33), rtol=1e-12, atol=0.0,
                label="wg_seep<-wg_seep")


def test_private_params_from_draws_rejects_nonfinite_draw():
    cfg = SourceCouplingConfig()
    draws = {k: 1e-5 for k in _SOURCE_KEYS}
    draws["detuning"] = float("nan")
    _raises_exact(ValueError, "draws_radns[detuning] must be finite, got nan",
                  lambda: coupling._params_from_draws(draws, cfg, coupling_mode="shared"))


def test_private_modulate_positive_rate_paths():
    assert_pins(coupling._modulate_positive_rate(1e-4, 3.0, 0.5, name="r"),
                _indep_pos_rate(1e-4, 3.0, 0.5), rtol=1e-12, atol=0.0, label="posrate normal")
    # base 0 AND sens 0 -> 0.0 (the inert branch)
    assert coupling._modulate_positive_rate(0.0, 5.0, 0.0, name="r") == 0.0
    # base 0 AND sens != 0 -> raise
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
    # EXACT-1e-12 boundaries (NUMERICAL_ZERO passed as the literal argument):
    #   base == NZ must take the zero-base branch (kills `base <= NZ` -> `base < NZ`)
    assert coupling._modulate_positive_rate(1e-12, 5.0, 0.0, name="r") == 0.0
    #   abs(sens) == NZ must NOT trip the raise (kills `abs(sens) > NZ` -> `>= NZ`)
    assert coupling._modulate_positive_rate(0.0, 5.0, 1e-12, name="r") == 0.0
    # [-60, 60] exponent clamp
    assert_pins(coupling._modulate_positive_rate(1e-4, 1e6, 1.0, name="r"), 1e-4 * math.exp(60.0),
                rtol=1e-12, atol=0.0, label="posrate clamp hi")
    assert_pins(coupling._modulate_positive_rate(1e-4, -1e6, 1.0, name="r"), 1e-4 * math.exp(-60.0),
                rtol=1e-12, atol=0.0, label="posrate clamp lo")


def test_private_modulate_probability_logit_paths():
    assert_pins(coupling._modulate_probability_logit(0.01, 3.0, 0.4, name="p"),
                _indep_prob_logit(0.01, 3.0, 0.4), rtol=1e-12, atol=0.0, label="logit normal")
    # p 0 AND sens 0 -> 0.0
    assert coupling._modulate_probability_logit(0.0, 5.0, 0.0, name="p") == 0.0
    # p 0 AND sens != 0 -> raise
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
    # EXACT-1e-12 boundaries (kill `p <= NZ` -> `<` and `abs(sens) > NZ` -> `>=`)
    assert coupling._modulate_probability_logit(1e-12, 5.0, 0.0, name="p") == 0.0
    assert coupling._modulate_probability_logit(0.0, 5.0, 1e-12, name="p") == 0.0
    # the upper clamp 1.0 - NZ is load-bearing: a base_p in (1 - NZ, 1) must be clamped to 1 - NZ
    # BEFORE the logit (matching the independent recompute, which clamps identically); the un-clamped
    # mutants (1.0 + NZ / 2.0 - NZ) diverge by ~5e-13. atol 1e-14 catches it, orig matches exactly.
    assert_pins(coupling._modulate_probability_logit(1.0 - 1e-13, 2.0, 0.3, name="p"),
                _indep_prob_logit(1.0 - 1e-13, 2.0, 0.3), rtol=0.0, atol=1e-14, label="upper clamp")
    # the logit-argument clamp [-60, 60]
    assert_pins(coupling._modulate_probability_logit(0.5, 1e6, 1.0, name="p"),
                1.0 / (1.0 + math.exp(-60.0)), rtol=1e-12, atol=0.0, label="logit clamp hi")
    assert_pins(coupling._modulate_probability_logit(0.5, -1e6, 1.0, name="p"),
                1.0 / (1.0 + math.exp(60.0)), rtol=1e-12, atol=0.0, label="logit clamp lo")


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
