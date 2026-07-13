from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import numpy as np


SCRIPT = Path(__file__).parents[1] / "scripts" / "finite_rtn_exact_cpdiv_gate.py"
SPEC = importlib.util.spec_from_file_location("finite_rtn_exact_cpdiv_gate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def test_single_ctmc_formula_matches_two_state_generator() -> None:
    times = (0.0, 0.5, 3.0, 10.0, 40.0)
    for amplitude, gamma in ((0.03, 0.01), (0.01, 0.03), (0.02, 0.02)):
        formula = GATE.single_ctmc_coherence(times, amplitude, gamma)
        oracle = np.asarray(
            [GATE.full_ctmc_coherence(t, [amplitude], [gamma]) for t in times]
        )
        np.testing.assert_allclose(formula, oracle, rtol=1.0e-12, atol=1.0e-12)


def test_joint_generator_has_declared_endpoint_autocorrelation() -> None:
    gamma = 0.037
    transition = GATE.expm(GATE.joint_ctmc_generator([gamma]))
    expected_flip = 0.5 * (1.0 - math.exp(-2.0 * gamma))
    np.testing.assert_allclose(
        transition,
        [[1.0 - expected_flip, expected_flip], [expected_flip, 1.0 - expected_flip]],
        rtol=1.0e-13,
        atol=1.0e-14,
    )


def test_factorized_ctmc_matches_full_joint_oracle() -> None:
    amplitudes = np.asarray([0.035, 0.02, 0.01])
    gammas = np.asarray([0.005, 0.03, 0.2])
    times = (0.0, 1.0, 8.0, 30.0, 100.0)
    product = GATE.product_ctmc_coherence(times, amplitudes, gammas)
    oracle = np.asarray(
        [GATE.full_ctmc_coherence(t, amplitudes, gammas) for t in times]
    )
    np.testing.assert_allclose(product, oracle, rtol=1.0e-11, atol=1.0e-12)


def test_factorized_held_sequence_matches_full_joint_oracle() -> None:
    amplitudes = np.asarray([0.035, 0.02, 0.01])
    gammas = np.asarray([0.005, 0.03, 0.2])
    product = GATE.product_held_sequence(amplitudes, gammas, 80)
    oracle = GATE.full_held_sequence(amplitudes, gammas, 80)
    np.testing.assert_allclose(product, oracle, rtol=1.0e-11, atol=1.0e-12)


def test_registered_controls_are_falsifiable() -> None:
    source = GATE.OneOverFDriftSource()
    amplitudes = source.amplitudes_radns * source.cycle_time_ns
    gammas = source.gammas_per_cycle
    grid = np.arange(0.0, 200.0 + 0.005, 0.01)

    exact = GATE.product_ctmc_coherence(grid, amplitudes, gammas)
    gaussian = GATE.gaussian_surrogate_coherence(grid, amplitudes, gammas)
    weak = GATE.product_ctmc_coherence(grid, amplitudes, 2.0 * amplitudes)

    _, exact_max_step = GATE.positive_excursion(exact)
    _, gaussian_max_step = GATE.positive_excursion(gaussian)
    _, weak_max_step = GATE.positive_excursion(weak)
    assert exact_max_step > GATE.MONOTONIC_TOL
    assert gaussian_max_step <= GATE.MONOTONIC_TOL
    assert weak_max_step <= GATE.MONOTONIC_TOL


def test_adjudication_distinguishes_null_from_implementation_failure() -> None:
    assert GATE.diagnostic_verdict(
        implementation_passed=True, positive_excursion_found=True
    ) == "CONFIRMED_DIAGNOSTIC_ONLY"
    assert GATE.diagnostic_verdict(
        implementation_passed=True, positive_excursion_found=False
    ) == "NULL_WITHIN_HORIZON"
    assert GATE.diagnostic_verdict(
        implementation_passed=False, positive_excursion_found=True
    ) == "IMPLEMENTATION_GATE_FAILED"
