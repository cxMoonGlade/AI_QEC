"""P2-i gates — the Theta->leakage fan-out extension (prereg
``docs/twin_validation/p2_conjunction_wiring_prereg.md`` §1 P2-i).

Registered gates, all class (a) identities on the DECLARED map (CPU):
  G-1  Theta(0) off-source identity: at z=0 the fan-out returns the configured
       bases EXACTLY (bit-equal floats, not approx).
  G-2  map identity: theta(x)/theta(0) == exp(s_theta * x) and
       g_seep(x)/g_seep(0) == exp(s_seep * x) to 1e-12 rel (the declared
       positive-rate exp form).
  G-3  liveness (the C-9/R1 pattern): a non-constant z trajectory with live
       sensitivities yields non-constant wg_theta/wg_g_seep; the g-doubled
       negative control differs.
  G-4  inert defaults: the default config emits wg_theta_rad == wg_g_seep == 0
       for ANY draw, and pre-P2 direct CoupledMechanismParams constructors
       still work (backward compatibility).
  G-5  independent-baseline marginal preservation extends to the new keys:
       sorted one-field marginals equal the shared arm's exactly.
  G-6  guard: nonzero sensitivity on a zero base raises (never a silent 0).
  G-7  manifests carry the new fields (config + params).
"""

import math

import numpy as np
import pytest

from error_coupling_simulator.source.coupling import (
    CoupledMechanismParams,
    SourceCouplingConfig,
    default_source_coupling_config,
    independent_baseline_trajectory_to_params,
    leakage_from_drift,
    parameter_series,
    source_to_params,
    trajectory_to_params,
)

THETA_CELL = 0.102444  # the calibrated WG_L1=5e-3 physical point (class (c) cell)
G_SEEP_CELL = 0.09     # McEwen WG_L2 band point


def _cfg(s_theta: float = 0.30, s_seep: float = 0.30) -> SourceCouplingConfig:
    return SourceCouplingConfig(
        wg_theta_base_rad=THETA_CELL,
        wg_theta_sensitivity=s_theta,
        wg_g_seep_base=G_SEEP_CELL,
        wg_g_seep_sensitivity=s_seep,
    )


def test_g1_theta0_identity_exact():
    cfg = _cfg()
    p = source_to_params(0.0, cfg)
    assert p.wg_theta_rad == THETA_CELL
    assert p.wg_g_seep == G_SEEP_CELL


def test_g2_exp_map_identity():
    cfg = _cfg(s_theta=0.30, s_seep=0.45)
    for x in (-3.0, -1.0, -0.1, 0.5, 2.0):
        z = x * cfg.z_scale_radns
        theta, seep = leakage_from_drift(z, z, cfg)
        assert abs(theta / THETA_CELL - math.exp(0.30 * x)) < 1e-12
        assert abs(seep / G_SEEP_CELL - math.exp(0.45 * x)) < 1e-12


def test_g3_liveness_and_negative_control():
    cfg = _cfg()
    rng = np.random.default_rng(20260706)
    z = rng.normal(scale=cfg.z_scale_radns, size=32)
    params = trajectory_to_params(z, cfg)
    thetas = parameter_series(params, "wg_theta_rad")
    seeps = parameter_series(params, "wg_g_seep")
    assert np.unique(thetas).size > 1 and np.unique(seeps).size > 1
    # negative control: doubled sensitivity produces a DIFFERENT trajectory
    params2 = trajectory_to_params(z, _cfg(s_theta=0.60, s_seep=0.60))
    assert float(np.max(np.abs(parameter_series(params2, "wg_theta_rad") - thetas))) > 0.0


def test_g4_inert_defaults_and_backward_compat():
    cfg = default_source_coupling_config()
    for z in (0.0, 3.0 * cfg.z_scale_radns, -5.0 * cfg.z_scale_radns):
        p = source_to_params(z, cfg)
        assert p.wg_theta_rad == 0.0 and p.wg_g_seep == 0.0
    # pre-P2 direct constructor (no wg fields) still valid
    q = CoupledMechanismParams(
        source_draws_radns=(("zz", 0.0),), normalized_draws=(("zz", 0.0),),
        zz_phi_rad=0.0, zz_zeta_radns=0.0, zz_exchange_j_radns=0.0,
        gamma_phi_per_ns=1e-5, tphi_ns=1e5, detuning_radns=0.0,
        drive_omega_radns=0.1, spillover_cx=1e-3, readout_flip_p=1e-2,
        reset_flip_p=5e-3, cz_depol_p=2e-3)
    assert q.wg_theta_rad == 0.0 and q.wg_g_seep == 0.0


def test_g5_independent_baseline_preserves_new_marginals():
    cfg = _cfg()
    rng = np.random.default_rng(7)
    z = rng.normal(scale=cfg.z_scale_radns, size=200)
    shared = trajectory_to_params(z, cfg)
    indep = independent_baseline_trajectory_to_params(z, cfg, seed=11)
    for fld in ("wg_theta_rad", "wg_g_seep"):
        a = np.sort(parameter_series(shared, fld))
        b = np.sort(parameter_series(indep, fld))
        assert np.allclose(a, b, rtol=0.0, atol=1e-15)


def test_g6_zero_base_nonzero_sensitivity_raises():
    cfg = SourceCouplingConfig(wg_theta_base_rad=0.0, wg_theta_sensitivity=0.3)
    with pytest.raises(ValueError, match="wg_theta_rad"):
        leakage_from_drift(1.0e-4, 0.0, cfg)


def test_g7_manifests_carry_new_fields():
    cfg = _cfg()
    m = cfg.to_manifest()
    for key in ("wg_theta_base_rad", "wg_theta_sensitivity",
                "wg_g_seep_base", "wg_g_seep_sensitivity"):
        assert key in m
    pm = source_to_params(0.0, cfg).to_manifest()
    assert pm["wg_theta_rad"] == THETA_CELL and pm["wg_g_seep"] == G_SEEP_CELL
    draws = dict(source_to_params(0.0, cfg).source_draws_radns)
    assert "wg_theta" in draws and "wg_seep" in draws
