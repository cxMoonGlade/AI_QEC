from __future__ import annotations

import numpy as np
import pytest


qt = pytest.importorskip("qutip", reason="CZ leakage-channel derivation requires QuTiP")

import error_coupling_simulator.mechanisms as mechanisms
from error_coupling_simulator.mechanisms import cz_leakage
from error_coupling_simulator.mechanisms.cz_leakage import (
    CZParams,
    TWO_PI,
    coupling_H,
    ghz,
    interaction_point_omega_flux,
    ladder_couplings,
    mhz,
    superop_to_truncated_kraus,
    transmon_H_static,
)


def test_cz_leakage_api_is_exported_lazily_from_mechanisms() -> None:
    assert set(mechanisms.__all__) == set(cz_leakage.__all__)
    assert mechanisms.CZParams is CZParams
    assert mechanisms.superop_to_truncated_kraus is superop_to_truncated_kraus


def test_cz_parameter_units_and_interaction_point_are_explicit() -> None:
    params = CZParams()

    assert ghz(1.0) == TWO_PI
    assert mhz(1_000.0) == TWO_PI
    assert interaction_point_omega_flux(params) == (
        params.omega_stat - params.alpha_flux + params.detune_int
    )
    assert params.with_(t_gate=17.0).t_gate == 17.0
    assert params.t_gate == 25.0


def test_cz_duffing_operators_use_flux_tensor_stat_order() -> None:
    params = CZParams(sim_levels=3)

    assert transmon_H_static(params.omega_flux_max, params.alpha_flux, 3).shape == (3, 3)
    assert coupling_H(3).shape == (9, 9)

    couplings = ladder_couplings(params)
    assert couplings["g_1120(|11-20|=sqrt2 J1)"] == pytest.approx(np.sqrt(2.0) * params.J1)
    assert couplings["g_1221(|12-21|=2J1)"] == pytest.approx(2.0 * params.J1)


def test_superoperator_to_kraus_identity_conversion_is_cptp() -> None:
    unitary = qt.qeye(4)
    superop = qt.spre(unitary) * qt.spost(unitary.dag())

    kraus, skk, loss_norm, _ = superop_to_truncated_kraus(
        superop,
        track_dim=2,
        sim_levels=2,
    )

    assert len(kraus) == 1
    assert kraus[0].shape == (4, 4)
    np.testing.assert_allclose(skk, np.eye(4), rtol=0.0, atol=1e-12)
    assert loss_norm == pytest.approx(0.0, abs=1e-12)
