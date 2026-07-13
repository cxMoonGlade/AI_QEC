from __future__ import annotations

import math

import numpy as np
import pytest

from qec_twin.mechanisms.source_coupling import (
    SourceCouplingConfig,
    StaticZZCalibration,
    _drift_to_T2,
    cross_mechanism_correlation,
    drift_to_t2,
    exchange_j_from_phi,
    independent_baseline_trajectory_to_params,
    parameter_series,
    source_to_params,
    static_zz_zeta,
    trajectory_to_params,
    zz_phi_from_frequency_drift,
)


def test_static_zz_phi_j_inverse_is_closed_form_consistent():
    zz = StaticZZCalibration(base_phi_rad=1.6e-4)
    J = exchange_j_from_phi(
        zz.base_phi_rad,
        delta_radns=zz.base_delta_radns,
        alpha_radns=zz.alpha_radns,
        t_gate_ns=zz.t_gate_ns,
    )
    zeta = static_zz_zeta(zz.base_delta_radns, zz.alpha_radns, J)

    assert J == pytest.approx(zz.exchange_j_radns)
    assert zeta * zz.t_gate_ns / 4.0 == pytest.approx(zz.base_phi_rad, rel=1e-12)


def test_source_to_params_shared_draw_fans_out_to_all_declared_hooks():
    cfg = SourceCouplingConfig(z_scale_radns=1e-4)
    p0 = source_to_params(0.0, cfg)
    p1 = source_to_params(0.5e-4, cfg)

    assert p0.coupling_mode == "shared"
    assert set(dict(p0.source_draws_radns)) == {
        "zz",
        "gamma_phi",
        "detuning",
        "drive",
        "spillover",
        "readout",
        "reset",
        "cz",
        # P2-i (2026-07-06): the Theta->leakage hooks (inert at the default
        # config; gates in tests/test_p2_theta_leakage.py).
        "wg_theta",
        "wg_seep",
    }
    assert len(set(dict(p1.source_draws_radns).values())) == 1
    assert p0.zz_phi_rad == pytest.approx(cfg.zz.base_phi_rad, rel=1e-12)
    assert p1.detuning_radns == pytest.approx(cfg.detuning_base_radns + 0.5e-4)
    assert p1.gamma_phi_per_ns > p0.gamma_phi_per_ns
    assert p1.drive_omega_radns > p0.drive_omega_radns
    assert p1.readout_flip_p > p0.readout_flip_p
    assert p1.reset_flip_p > p0.reset_flip_p
    assert p1.cz_depol_p > p0.cz_depol_p
    assert 0.0 <= p1.spillover_cx < 1.0


def test_drift_to_t2_contract_helper_matches_params_bundle():
    cfg = SourceCouplingConfig(z_scale_radns=1e-4)
    gamma_phi, tphi = drift_to_t2(0.5e-4, cfg)
    gamma_phi_alias, tphi_alias = _drift_to_T2(0.5e-4, cfg)
    params = source_to_params(0.5e-4, cfg)

    assert gamma_phi == pytest.approx(gamma_phi_alias)
    assert tphi == pytest.approx(tphi_alias)
    assert params.gamma_phi_per_ns == pytest.approx(gamma_phi)
    assert params.tphi_ns == pytest.approx(tphi)


def test_zz_phi_from_frequency_drift_uses_raw_detuning_shift():
    cfg = SourceCouplingConfig(z_scale_radns=1e-4)
    phi0, zeta0 = zz_phi_from_frequency_drift(0.0, cfg)
    phi_plus, zeta_plus = zz_phi_from_frequency_drift(1e-5, cfg)
    phi_minus, zeta_minus = zz_phi_from_frequency_drift(-1e-5, cfg)

    assert phi0 == pytest.approx(cfg.zz.base_phi_rad, rel=1e-12)
    assert zeta0 == pytest.approx(4.0 * cfg.zz.base_phi_rad / cfg.zz.t_gate_ns, rel=1e-12)
    assert phi_minus != pytest.approx(phi_plus)
    assert zeta_minus != pytest.approx(zeta_plus)


def test_independent_baseline_preserves_marginals_and_breaks_cross_mechanism_correlation():
    cfg = SourceCouplingConfig(
        z_scale_radns=1e-4,
        gamma_phi_sensitivity=0.4,
        drive_omega_sensitivity=0.4,
        readout_flip_sensitivity=0.4,
    )
    z = np.linspace(-2.0e-4, 2.0e-4, 1001)
    shared = trajectory_to_params(z, cfg)
    independent = independent_baseline_trajectory_to_params(z, cfg, seed=123)

    assert cross_mechanism_correlation(shared, "detuning_radns", "drive_omega_radns") > 0.95
    assert abs(cross_mechanism_correlation(independent, "detuning_radns", "drive_omega_radns")) < 0.15

    shared_drive = np.sort(parameter_series(shared, "drive_omega_radns"))
    independent_drive = np.sort(parameter_series(independent, "drive_omega_radns"))
    np.testing.assert_allclose(shared_drive, independent_drive, rtol=0, atol=1e-15)


def test_source_coupling_manifest_declares_epistemic_classes_and_params_are_serializable():
    cfg = SourceCouplingConfig()
    params = source_to_params(1e-5, cfg)
    cfg_manifest = cfg.to_manifest()
    param_manifest = params.to_manifest()

    assert cfg_manifest["epistemic_class"]["static_zz_formula"] == "a"
    assert cfg_manifest["epistemic_class"]["constants_and_sensitivities"] == "c"
    assert cfg_manifest["zz"]["value_provenance"]["claims_device_calibration"] is False
    assert param_manifest["schema"] == "qec_twin.mechanisms.CoupledMechanismParams.v1"
    assert param_manifest["source_draws_radns"]["zz"] == pytest.approx(1e-5)
    assert math.isfinite(param_manifest["gamma_phi_per_ns"])
    assert math.isfinite(param_manifest["tphi_ns"])


def test_source_coupling_rejects_invalid_probability_and_zero_base_modulation():
    with pytest.raises(ValueError, match="readout_flip_base_p"):
        SourceCouplingConfig(readout_flip_base_p=1.0)

    cfg = SourceCouplingConfig(readout_flip_base_p=0.0, readout_flip_sensitivity=0.4)
    with pytest.raises(ValueError, match="readout_flip_p"):
        source_to_params(1e-4, cfg)
