"""Physical value-pins for the production Wood--Gambetta qutrit channel.

The operator-sum representation is not unique, so the Kraus tests reconstruct the
channel and compare it with an independently hand-typed GKSL matrix exponential.
Structural CPTP checks are retained, but they are never the only oracle.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import scipy.linalg as sla
import torch

from _support.faithfulness import assert_cptp, assert_discriminates

import error_coupling_simulator.mechanisms.qutrit_leakage as leakage
from error_coupling_simulator.mechanisms.qutrit_leakage import (
    QutritLeakageNoiseProcess,
    coherence_of_leakage,
    leaked_readout_manifest,
    leaked_readout_probabilities,
    leakage_channel_super,
    leakage_kraus,
    leakage_kraus_torch,
    qutrit_leakage_process,
    qutrit_leakage_process_heterogeneous,
    solve_theta_for_wg_l1,
    wg_rates,
)


def _op(output_level: int, input_level: int) -> np.ndarray:
    basis = np.eye(3, dtype=np.complex128)
    return np.outer(basis[output_level], basis[input_level].conj())


def _independent_superoperator(
    theta: float,
    g_seep: float,
    g_heat: float,
    duration: float = 1.0,
) -> np.ndarray:
    """Hand-typed column-vectorized GKSL reference, independent of production helpers."""

    identity = np.eye(3, dtype=np.complex128)
    hamiltonian = theta * (_op(1, 2) + _op(2, 1))
    generator = -1j * (
        np.kron(identity, hamiltonian) - np.kron(hamiltonian.T, identity)
    )
    jumps = []
    if g_seep > 0.0:
        jumps.append(math.sqrt(g_seep) * _op(1, 2))
    if g_heat > 0.0:
        jumps.append(math.sqrt(g_heat) * _op(2, 1))
    for jump in jumps:
        normal = jump.conj().T @ jump
        generator += np.kron(jump.conj(), jump) - 0.5 * (
            np.kron(identity, normal) + np.kron(normal.T, identity)
        )
    return sla.expm(generator * duration)


def _superoperator_from_kraus(kraus: list[np.ndarray]) -> np.ndarray:
    return sum(np.kron(operator.conj(), operator) for operator in kraus)


@pytest.mark.parametrize(
    ("theta", "g_seep", "g_heat"),
    [
        (0.20, 0.05, 0.03),
        (0.15, 0.00, 0.00),
        (0.10, 0.08, 0.00),
        (0.00, 0.00, 0.06),
    ],
)
def test_leakage_superoperator_matches_independent_gksl(
    theta: float,
    g_seep: float,
    g_heat: float,
) -> None:
    expected = _independent_superoperator(theta, g_seep, g_heat)
    actual = leakage_channel_super(theta, g_seep, g_heat)
    np.testing.assert_allclose(actual, expected, atol=1e-11, rtol=0.0)

    wrong_but_cptp = leakage_channel_super(theta + 0.07, g_seep, g_heat)
    assert_discriminates(
        lambda channel: np.testing.assert_allclose(
            channel, expected, atol=1e-11, rtol=0.0
        ),
        actual,
        wrong_but_cptp,
        label="qutrit leakage superoperator",
    )


def test_leakage_superoperator_duration_and_validation() -> None:
    np.testing.assert_allclose(
        leakage_channel_super(0.2, 0.05, 0.03, t=0.0),
        np.eye(9, dtype=np.complex128),
        atol=1e-12,
        rtol=0.0,
    )
    np.testing.assert_allclose(
        leakage_channel_super(0.2, 0.05, 0.03, t=0.4),
        _independent_superoperator(0.2, 0.05, 0.03, 0.4),
        atol=1e-11,
        rtol=0.0,
    )

    for rates in ((-0.1, 0.0), (0.0, -0.1)):
        with pytest.raises(
            ValueError,
            match="qutrit seepage and heating rates must be non-negative",
        ):
            leakage_channel_super(0.2, rates[0], rates[1])
    with pytest.raises(
        ValueError,
        match="qutrit leakage duration must be non-negative",
    ):
        leakage_channel_super(0.2, 0.05, t=-0.1)


@pytest.mark.parametrize(
    ("theta", "g_seep", "g_heat"),
    [(0.2, 0.05, 0.0), (0.2, 0.05, 0.03), (0.15, 0.0, 0.0)],
)
def test_leakage_kraus_is_cptp_and_matches_independent_channel(
    theta: float,
    g_seep: float,
    g_heat: float,
) -> None:
    operators = leakage_kraus(theta, g_seep, g_heat)
    assert_cptp(operators, label="Wood--Gambetta qutrit leakage")
    np.testing.assert_allclose(
        _superoperator_from_kraus(operators),
        _independent_superoperator(theta, g_seep, g_heat),
        atol=1e-10,
        rtol=0.0,
    )


def test_superoperator_factorization_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match=r"must have shape \(9, 9\)"):
        leakage._super_to_kraus(np.eye(4, dtype=np.complex128))
    with pytest.raises(ValueError, match="Choi matrix is not positive semidefinite"):
        leakage._super_to_kraus(-np.eye(9, dtype=np.complex128))


def test_wg_rates_match_closed_form_limits() -> None:
    theta = 0.23
    l1, l2 = wg_rates(theta, 0.0, 0.0)
    expected_transfer = math.sin(theta) ** 2
    assert l1 == pytest.approx(0.5 * expected_transfer, abs=1e-12)
    assert l2 == pytest.approx(expected_transfer, abs=1e-12)

    l1_seep, l2_seep = wg_rates(0.0, 0.17, 0.0)
    assert l1_seep == pytest.approx(0.0, abs=1e-12)
    assert l2_seep == pytest.approx(1.0 - math.exp(-0.17), abs=1e-12)

    l1_heat, l2_heat = wg_rates(0.0, 0.0, 0.11)
    assert l1_heat == pytest.approx(0.5 * (1.0 - math.exp(-0.11)), abs=1e-12)
    assert l2_heat == pytest.approx(0.0, abs=1e-12)


def test_coherence_of_leakage_matches_unitary_limit_and_incoherent_null() -> None:
    for theta in (0.0, 0.07, 0.31):
        assert coherence_of_leakage(theta, 0.0, 0.0) == pytest.approx(
            abs(math.sin(2.0 * theta)), abs=1e-12
        )
    assert coherence_of_leakage(0.0, 0.09, 0.005) == pytest.approx(0.0, abs=1e-12)


def test_solve_theta_hits_requested_wg_rate_and_validates_domain() -> None:
    assert solve_theta_for_wg_l1(0.0) == 0.0
    for target in (1.0e-3, 5.0e-3):
        theta = solve_theta_for_wg_l1(target, g_seep=0.09, g_heat=0.0)
        assert wg_rates(theta, 0.09, 0.0)[0] == pytest.approx(target, abs=1e-10)

    with pytest.raises(ValueError, match=r"target WG_L1 must lie in \(0, 0.5\)"):
        solve_theta_for_wg_l1(0.5)
    with pytest.raises(ValueError, match="target WG_L1=0.1 unreachable"):
        solve_theta_for_wg_l1(0.1, g_seep=10.0)
    assert solve_theta_for_wg_l1(0.1, max_iter=0) == pytest.approx(math.pi / 4.0)


def test_leaked_readout_map_and_audit_record_are_explicit() -> None:
    assert leaked_readout_probabilities(0.75) == {0: 0.0, 1: 1.0, 2: 0.75}
    record = leaked_readout_manifest(0.75)
    assert record["leaked_readout_bias_b"] == 0.75
    assert record["leaked_bit1_prob"] == 0.75
    assert record["readout_role"] == "swept_nuisance"
    assert record["swept"] is True
    assert record["magnitude_pinned"] is False
    assert record["is_coin_flip"] is False
    for invalid in (-0.01, 1.01, float("nan"), float("inf")):
        with pytest.raises(ValueError, match=r"must be a probability in \[0,1\]"):
            leaked_readout_probabilities(invalid)


def test_torch_kraus_is_only_a_carrier_conversion() -> None:
    operators = leakage_kraus_torch(
        0.12,
        0.07,
        0.01,
        device="cpu",
        dtype=torch.complex128,
    )
    reference = leakage_kraus(0.12, 0.07, 0.01)
    assert all(operator.device.type == "cpu" for operator in operators)
    assert all(operator.dtype == torch.complex128 for operator in operators)
    for actual, expected in zip(operators, reference, strict=True):
        np.testing.assert_allclose(actual.numpy(), expected, atol=1e-12, rtol=0.0)


def test_homogeneous_noise_process_uses_physical_channel_and_neutral_type() -> None:
    process = qutrit_leakage_process(
        b=0.75,
        theta=0.10,
        g_seep=0.09,
        g_heat=0.0,
        n_data=3,
        device="cpu",
    )
    assert isinstance(process, QutritLeakageNoiseProcess)
    assert process.leaked_readout == {0: 0.0, 1: 1.0, 2: 0.75}
    assert process.params["n_data"] == 3
    assert process.params["homogeneous"] is True
    assert process.params["C_L"] > 0.0
    assert process.field(0, 0) is process.field(7, 2)
    np.testing.assert_allclose(
        _superoperator_from_kraus([item.numpy() for item in process.field(0, 0)]),
        _independent_superoperator(0.10, 0.09, 0.0),
        atol=1e-10,
        rtol=0.0,
    )

    null_process = qutrit_leakage_process(
        b=0.5,
        theta=0.0,
        g_seep=0.09,
        device="cpu",
    )
    assert null_process.params["WG_L2_over_L1"] == float("inf")


def test_heterogeneous_noise_process_preserves_per_site_rates() -> None:
    process = qutrit_leakage_process_heterogeneous(
        [(0.07, 0.05), (0.11, 0.09, 0.005)],
        b=1.0,
        device="cpu",
    )
    assert isinstance(process, QutritLeakageNoiseProcess)
    assert process.params["rates"] == [(0.07, 0.05, 0.0), (0.11, 0.09, 0.005)]
    assert process.params["n_data"] == 2
    assert process.params["homogeneous"] is False
    for site, rates in enumerate(process.params["rates"]):
        np.testing.assert_allclose(
            _superoperator_from_kraus([item.numpy() for item in process.field(9, site)]),
            _independent_superoperator(*rates),
            atol=1e-10,
            rtol=0.0,
        )
