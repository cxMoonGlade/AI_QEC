"""Value-pins for the declared qutrit exchange/seepage/heating channel.

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
    leakage_seepage_rates,
    leaked_readout_manifest,
    leaked_readout_probabilities,
    leakage_channel_super,
    leakage_kraus,
    leakage_kraus_torch,
    level1_output_leakage_coherence,
    qutrit_leakage_process,
    qutrit_leakage_process_heterogeneous,
    solve_exchange_angle_for_leakage_rate,
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
    ("theta", "g_seep", "g_heat", "duration"),
    [
        (float("nan"), 0.05, 0.03, 1.0),
        (0.2, float("inf"), 0.03, 1.0),
        (0.2, 0.05, float("-inf"), 1.0),
        (0.2, 0.05, 0.03, float("nan")),
    ],
)
def test_leakage_superoperator_rejects_nonfinite_declared_parameters(
    theta: float,
    g_seep: float,
    g_heat: float,
    duration: float,
) -> None:
    with pytest.raises(ValueError, match="parameters and duration must be finite"):
        leakage_channel_super(theta, g_seep, g_heat, t=duration)


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
    assert_cptp(operators, label="qutrit exchange/seepage/heating channel")
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


def test_leakage_seepage_rates_match_closed_form_limits() -> None:
    theta = 0.23
    leakage_rate, seepage_rate = leakage_seepage_rates(theta, 0.0, 0.0)
    expected_transfer = math.sin(theta) ** 2
    assert leakage_rate == pytest.approx(0.5 * expected_transfer, abs=1e-12)
    assert seepage_rate == pytest.approx(expected_transfer, abs=1e-12)

    leakage_seep, seepage_seep = leakage_seepage_rates(0.0, 0.17, 0.0)
    assert leakage_seep == pytest.approx(0.0, abs=1e-12)
    assert seepage_seep == pytest.approx(1.0 - math.exp(-0.17), abs=1e-12)

    leakage_heat, seepage_heat = leakage_seepage_rates(0.0, 0.0, 0.11)
    assert leakage_heat == pytest.approx(0.5 * (1.0 - math.exp(-0.11)), abs=1e-12)
    assert seepage_heat == pytest.approx(0.0, abs=1e-12)


def test_level1_output_coherence_matches_unitary_limit_and_incoherent_null() -> None:
    for theta in (0.0, 0.07, 0.31):
        assert level1_output_leakage_coherence(theta, 0.0, 0.0) == pytest.approx(
            abs(math.sin(2.0 * theta)), abs=1e-12
        )
    assert level1_output_leakage_coherence(
        0.0, 0.09, 0.005
    ) == pytest.approx(0.0, abs=1e-12)


@pytest.mark.parametrize(
    "invalid_target",
    [-1.0e-3, 0.51, float("nan"), float("inf")],
)
def test_exchange_angle_solver_rejects_invalid_target(
    invalid_target: float,
) -> None:
    with pytest.raises(ValueError, match=r"must be finite and lie in \[0, 0.5\]"):
        solve_exchange_angle_for_leakage_rate(invalid_target)


def test_exchange_angle_solver_hits_requested_rate_and_endpoints() -> None:
    assert solve_exchange_angle_for_leakage_rate(0.0) == 0.0
    for target in (1.0e-3, 5.0e-3):
        theta = solve_exchange_angle_for_leakage_rate(
            target, g_seep=0.09, g_heat=0.0
        )
        assert leakage_seepage_rates(theta, 0.09, 0.0)[0] == pytest.approx(
            target, abs=1e-10
        )

    upper_endpoint = solve_exchange_angle_for_leakage_rate(
        0.5, g_seep=0.0, g_heat=0.0
    )
    assert upper_endpoint == pytest.approx(0.5 * math.pi, abs=1e-15)
    assert leakage_seepage_rates(upper_endpoint, 0.0, 0.0)[0] == pytest.approx(
        0.5,
        abs=1e-15,
    )

    with pytest.raises(ValueError, match="max_iter must be a positive integer"):
        solve_exchange_angle_for_leakage_rate(0.1, max_iter=0)
    with pytest.raises(ValueError, match="bracket_samples must be an integer >= 2"):
        solve_exchange_angle_for_leakage_rate(0.1, bracket_samples=1)


def test_exchange_angle_solver_does_not_floor_a_positive_target_to_zero() -> None:
    target = 1.0e-14
    theta = solve_exchange_angle_for_leakage_rate(
        target,
        g_seep=0.0,
        g_heat=0.0,
    )

    assert theta > 0.0
    assert leakage_seepage_rates(theta, 0.0, 0.0)[0] == pytest.approx(
        target,
        abs=0.5 * target,
    )


@pytest.mark.parametrize(
    "invalid_tolerance",
    [0.0, -1.0e-10, float("nan"), float("inf")],
)
def test_exchange_angle_solver_rejects_invalid_tolerance(
    invalid_tolerance: float,
) -> None:
    with pytest.raises(ValueError, match="tol must be finite and positive"):
        solve_exchange_angle_for_leakage_rate(0.1, tol=invalid_tolerance)


@pytest.mark.parametrize("invalid_count", [None, "not-an-integer", float("inf")])
def test_exchange_angle_solver_rejects_unconvertible_iteration_controls(
    invalid_count: object,
) -> None:
    with pytest.raises(ValueError, match="max_iter must be a positive integer"):
        solve_exchange_angle_for_leakage_rate(
            0.1, max_iter=invalid_count  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="bracket_samples must be an integer >= 2"):
        solve_exchange_angle_for_leakage_rate(
            0.1, bracket_samples=invalid_count  # type: ignore[arg-type]
        )


def test_exchange_angle_solver_accepts_an_exact_scan_node() -> None:
    theta_on_grid = math.pi / 16.0
    target = leakage_seepage_rates(theta_on_grid, 0.0, 0.0)[0]

    solved = solve_exchange_angle_for_leakage_rate(
        target,
        g_seep=0.0,
        g_heat=0.0,
        bracket_samples=8,
    )

    assert solved == pytest.approx(theta_on_grid, abs=1e-15)
    assert leakage_seepage_rates(solved, 0.0, 0.0)[0] == pytest.approx(
        target,
        abs=1e-15,
    )


def test_exchange_angle_solver_accepts_a_verified_terminal_midpoint() -> None:
    theta_after_one_step = 3.0 * math.pi / 16.0
    target = leakage_seepage_rates(theta_after_one_step, 0.0, 0.0)[0]

    solved = solve_exchange_angle_for_leakage_rate(
        target,
        g_seep=0.0,
        g_heat=0.0,
        tol=1e-14,
        max_iter=1,
        bracket_samples=2,
    )

    assert solved == pytest.approx(theta_after_one_step, abs=1e-15)
    assert leakage_seepage_rates(solved, 0.0, 0.0)[0] == pytest.approx(
        target,
        abs=1e-14,
    )


def test_exchange_angle_solver_fails_closed_after_insufficient_iterations() -> None:
    target = leakage_seepage_rates(0.6, 0.0, 0.0)[0]

    with pytest.raises(RuntimeError, match="did not reach tolerance"):
        solve_exchange_angle_for_leakage_rate(
            target,
            g_seep=0.0,
            g_heat=0.0,
            tol=1e-14,
            max_iter=1,
            bracket_samples=2,
        )


def test_leaked_readout_map_and_audit_record_are_explicit() -> None:
    assert leaked_readout_probabilities(0.75) == {0: 0.0, 1: 1.0, 2: 0.75}
    record = leaked_readout_manifest(0.75)
    assert record["leaked_readout_bias_b"] == 0.75
    assert record["leaked_bit1_prob"] == 0.75
    assert record["readout_role"] == "swept_nuisance"
    assert record["swept"] is True
    assert record["direction_provenance"] == "project-design"
    assert record["literature_supports_binary_map"] is False
    assert record["source"] is None
    assert "direction_grounded" not in record
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


def test_homogeneous_noise_process_uses_declared_channel_and_neutral_type() -> None:
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
    assert process.params["level1_output_leakage_coherence"] > 0.0
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
    assert null_process.params["leakage_rate"] == 0.0
    assert null_process.params["seepage_rate"] > 0.0
    assert "seepage_to_leakage_ratio" not in null_process.params


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


def test_current_qutrit_leakage_api_has_descriptive_names_only() -> None:
    """The hard-cut public surface names declared operations, never an author alias."""

    for current_name in (
        "leakage_seepage_rates",
        "level1_output_leakage_coherence",
        "solve_exchange_angle_for_leakage_rate",
    ):
        assert callable(getattr(leakage, current_name))
    retired_name_fragments = (
        ("w", "g", "_rates"),
        ("coherence", "_of", "_leakage"),
        ("solve", "_theta", "_for", "_w", "g", "_l1"),
    )
    for fragments in retired_name_fragments:
        retired_name = "".join(fragments)
        assert not hasattr(leakage, retired_name)


def test_level1_output_coherence_records_the_fixed_input_not_channel_cause() -> None:
    """A coherent exchange has state-dependent nodes, so the metric cannot label cause."""

    metric = getattr(leakage, "level1_output_leakage_coherence")
    assert metric(math.pi / 4.0, 0.0, 0.0) == pytest.approx(1.0, abs=1e-12)
    assert metric(math.pi / 2.0, 0.0, 0.0) == pytest.approx(0.0, abs=1e-12)


def test_exchange_angle_solver_rejects_zero_below_heating_baseline() -> None:
    """Structural target zero is unreachable when heating leaks at theta=0."""

    rates = getattr(leakage, "leakage_seepage_rates")
    solve = getattr(leakage, "solve_exchange_angle_for_leakage_rate")
    baseline = rates(0.0, 0.0, 0.1)[0]
    assert baseline > 0.0
    assert solve(baseline, g_seep=0.0, g_heat=0.1) == 0.0
    with pytest.raises(ValueError, match="was not bracketed by the 256-sample scan"):
        solve(0.0, g_seep=0.0, g_heat=0.1)
    with pytest.raises(ValueError, match="max_iter must be a positive integer"):
        solve(0.1, max_iter=0)


def test_exchange_angle_solver_brackets_a_nonmonotone_rate_curve() -> None:
    """A reachable interior target must not be rejected from endpoint ordering alone."""

    g_seep = 0.022252004698710224
    g_heat = 0.12602047020945872
    target = 0.4741798745099791
    theta = solve_exchange_angle_for_leakage_rate(
        target,
        g_seep=g_seep,
        g_heat=g_heat,
    )
    actual = leakage_seepage_rates(theta, g_seep, g_heat)[0]
    assert actual == pytest.approx(target, abs=1e-10)
