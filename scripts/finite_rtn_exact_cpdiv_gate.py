#!/usr/bin/env python3
"""Exact finite-RTN free-induction diagnostic gate.

This script implements the frozen preregistration in
``docs/twin_validation/finite_rtn_exact_cpdiv_prereg_2026-07-13.md``.  It
tests two explicitly declared single-qubit diagnostic lifts of the production
``OneOverFDriftSource`` endpoint process.  It does not test the production
source-to-mechanism fan-out, QEC channel, syndrome record, or decoder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Sequence

import mpmath as mp
import numpy as np
from scipy.linalg import expm

from error_coupling_simulator.source.process import OneOverFDriftSource


ORACLE_TOL = 1.0e-10
MONOTONIC_TOL = 1.0e-12
HORIZON_CYCLES = 200
GRID_STEP_CYCLES = 0.01
CTMC_ORACLE_TIMES = (0.0, 1.0, 10.0, 25.0, 50.0, 75.0, 100.0, 150.0, 200.0)
HELD_ORACLE_CYCLES = (0, 1, 2, 5, 25, 50, 75, 100, 150, 200)


def single_ctmc_coherence(
    times: np.ndarray | Sequence[float] | float,
    amplitude_per_cycle: float,
    gamma_per_cycle: float,
) -> np.ndarray:
    """Exact symmetric-RTN free-induction coherence in cycle units."""

    t = np.asarray(times, dtype=np.float64)
    v = float(amplitude_per_cycle)
    gamma = float(gamma_per_cycle)
    if v < 0.0 or gamma <= 0.0 or np.any(t < 0.0):
        raise ValueError("require amplitude >= 0, gamma > 0, and times >= 0")
    if math.isclose(v, gamma, rel_tol=1.0e-14, abs_tol=0.0):
        return np.exp(-gamma * t) * (1.0 + gamma * t)
    if v < gamma:
        delta = math.sqrt(gamma * gamma - v * v)
        # This exponential combination is the stable form of
        # exp(-gamma*t) [cosh(delta*t)+(gamma/delta)sinh(delta*t)].
        return 0.5 * (
            (1.0 + gamma / delta) * np.exp((-gamma + delta) * t)
            + (1.0 - gamma / delta) * np.exp((-gamma - delta) * t)
        )
    omega = math.sqrt(v * v - gamma * gamma)
    return np.exp(-gamma * t) * (
        np.cos(omega * t) + (gamma / omega) * np.sin(omega * t)
    )


def product_ctmc_coherence(
    times: np.ndarray | Sequence[float] | float,
    amplitudes_per_cycle: Sequence[float],
    gammas_per_cycle: Sequence[float],
) -> np.ndarray:
    """Product of independent exact RTN coherence factors."""

    amplitudes, gammas = _validated_modes(amplitudes_per_cycle, gammas_per_cycle)
    t = np.asarray(times, dtype=np.float64)
    out = np.ones_like(t, dtype=np.float64)
    for amplitude, gamma in zip(amplitudes, gammas, strict=True):
        out *= single_ctmc_coherence(t, float(amplitude), float(gamma))
    return out


def joint_sign_states(mode_count: int) -> np.ndarray:
    """Joint states in the big-endian ordering used by ``np.kron``."""

    if mode_count <= 0:
        raise ValueError("mode_count must be positive")
    indexes = np.arange(1 << mode_count, dtype=np.uint64)
    bits = np.stack(
        [(indexes >> np.uint64(mode_count - 1 - k)) & np.uint64(1) for k in range(mode_count)],
        axis=1,
    )
    return np.where(bits == 0, -1.0, 1.0)


def joint_ctmc_generator(gammas_per_cycle: Sequence[float]) -> np.ndarray:
    """Row generator for independent symmetric CTMC modes."""

    gammas = np.asarray(gammas_per_cycle, dtype=np.float64)
    if gammas.ndim != 1 or gammas.size == 0 or np.any(gammas <= 0.0):
        raise ValueError("gammas_per_cycle must be a nonempty positive vector")
    mode_count = int(gammas.size)
    state_count = 1 << mode_count
    generator = np.zeros((state_count, state_count), dtype=np.float64)
    for state in range(state_count):
        for mode, gamma in enumerate(gammas):
            flipped = state ^ (1 << (mode_count - 1 - mode))
            generator[state, flipped] = float(gamma)
        generator[state, state] = -float(np.sum(gammas))
    return generator


def full_ctmc_coherence(
    time_cycles: float,
    amplitudes_per_cycle: Sequence[float],
    gammas_per_cycle: Sequence[float],
) -> complex:
    """Independent full-``2^K`` Feynman--Kac oracle."""

    amplitudes, gammas = _validated_modes(amplitudes_per_cycle, gammas_per_cycle)
    if time_cycles < 0.0:
        raise ValueError("time_cycles must be nonnegative")
    states = joint_sign_states(int(amplitudes.size))
    frequencies = states @ amplitudes
    tilted = joint_ctmc_generator(gammas).astype(np.complex128)
    tilted += 1j * np.diag(frequencies)
    state_count = int(states.shape[0])
    stationary = np.full(state_count, 1.0 / state_count, dtype=np.complex128)
    return complex(stationary @ expm(tilted * float(time_cycles)) @ np.ones(state_count))


def single_held_sequence(
    amplitude_per_cycle: float,
    gamma_per_cycle: float,
    horizon_cycles: int,
) -> np.ndarray:
    """Exact cycle-held single-mode characteristic function."""

    if horizon_cycles < 0:
        raise ValueError("horizon_cycles must be nonnegative")
    v = float(amplitude_per_cycle)
    gamma = float(gamma_per_cycle)
    if v < 0.0 or gamma <= 0.0:
        raise ValueError("require amplitude >= 0 and gamma > 0")
    probability = 0.5 * (1.0 - math.exp(-2.0 * gamma))
    transition = np.asarray(
        [[1.0 - probability, probability], [probability, 1.0 - probability]],
        dtype=np.complex128,
    )
    phase = np.exp(1j * np.asarray([-v, v], dtype=np.float64))
    weighted = np.asarray([0.5, 0.5], dtype=np.complex128)
    out = np.ones(horizon_cycles + 1, dtype=np.complex128)
    for cycle in range(1, horizon_cycles + 1):
        weighted *= phase
        out[cycle] = np.sum(weighted)
        weighted = weighted @ transition
    return out


def product_held_sequence(
    amplitudes_per_cycle: Sequence[float],
    gammas_per_cycle: Sequence[float],
    horizon_cycles: int,
) -> np.ndarray:
    """Factorized exact cycle-held characteristic function."""

    amplitudes, gammas = _validated_modes(amplitudes_per_cycle, gammas_per_cycle)
    out = np.ones(horizon_cycles + 1, dtype=np.complex128)
    for amplitude, gamma in zip(amplitudes, gammas, strict=True):
        out *= single_held_sequence(float(amplitude), float(gamma), horizon_cycles)
    return out


def full_held_sequence(
    amplitudes_per_cycle: Sequence[float],
    gammas_per_cycle: Sequence[float],
    horizon_cycles: int,
) -> np.ndarray:
    """Independent full-``2^K`` cycle-held transfer-matrix oracle."""

    amplitudes, gammas = _validated_modes(amplitudes_per_cycle, gammas_per_cycle)
    if horizon_cycles < 0:
        raise ValueError("horizon_cycles must be nonnegative")
    transition = np.asarray([[1.0]], dtype=np.complex128)
    for gamma in gammas:
        probability = 0.5 * (1.0 - math.exp(-2.0 * float(gamma)))
        mode_transition = np.asarray(
            [[1.0 - probability, probability], [probability, 1.0 - probability]],
            dtype=np.complex128,
        )
        transition = np.kron(transition, mode_transition)
    states = joint_sign_states(int(amplitudes.size))
    phase = np.exp(1j * (states @ amplitudes))
    state_count = int(states.shape[0])
    weighted = np.full(state_count, 1.0 / state_count, dtype=np.complex128)
    out = np.ones(horizon_cycles + 1, dtype=np.complex128)
    for cycle in range(1, horizon_cycles + 1):
        weighted *= phase
        out[cycle] = np.sum(weighted)
        weighted = weighted @ transition
    return out


def gaussian_surrogate_coherence(
    times: np.ndarray | Sequence[float] | float,
    amplitudes_per_cycle: Sequence[float],
    gammas_per_cycle: Sequence[float],
) -> np.ndarray:
    """Second-cumulant coherence for the same positive exponential covariance."""

    amplitudes, gammas = _validated_modes(amplitudes_per_cycle, gammas_per_cycle)
    t = np.asarray(times, dtype=np.float64)
    if np.any(t < 0.0):
        raise ValueError("times must be nonnegative")
    chi = np.zeros_like(t)
    for amplitude, gamma in zip(amplitudes, gammas, strict=True):
        chi += amplitude * amplitude * (
            t / (2.0 * gamma) - (1.0 - np.exp(-2.0 * gamma * t)) / (4.0 * gamma * gamma)
        )
    return np.exp(-chi)


def positive_excursion(values: Sequence[complex] | np.ndarray) -> tuple[float, float]:
    """Return total and maximum adjacent positive excursion of ``abs(values)``."""

    magnitude = np.abs(np.asarray(values))
    increments = np.diff(magnitude)
    positive = increments[increments > 0.0]
    total = float(np.sum(positive)) if positive.size else 0.0
    maximum = float(np.max(increments)) if increments.size else 0.0
    return total, maximum


def diagnostic_verdict(*, implementation_passed: bool, positive_excursion_found: bool) -> str:
    """Adjudicate one diagnostic without conflating a scientific null with a code failure."""

    if not implementation_passed:
        return "IMPLEMENTATION_GATE_FAILED"
    if positive_excursion_found:
        return "CONFIRMED_DIAGNOSTIC_ONLY"
    return "NULL_WITHIN_HORIZON"


def earliest_strong_zero(
    amplitudes_per_cycle: Sequence[float],
    gammas_per_cycle: Sequence[float],
) -> tuple[int, mp.mpf]:
    """Return the mode and first positive zero of the earliest strong factor."""

    amplitudes, gammas = _validated_modes(amplitudes_per_cycle, gammas_per_cycle)
    roots: list[tuple[int, mp.mpf]] = []
    with mp.workdps(80):
        for index, (amplitude, gamma) in enumerate(zip(amplitudes, gammas, strict=True)):
            v_mp = mp.mpf(str(float(amplitude)))
            g_mp = mp.mpf(str(float(gamma)))
            if v_mp <= g_mp:
                continue
            omega = mp.sqrt(v_mp * v_mp - g_mp * g_mp)
            root = (mp.pi - mp.atan(omega / g_mp)) / omega
            roots.append((index, root))
    if not roots:
        raise ValueError("no strong RTN modes")
    return min(roots, key=lambda item: item[1])


def high_precision_product(
    time_cycles: mp.mpf,
    amplitudes_per_cycle: Sequence[float],
    gammas_per_cycle: Sequence[float],
) -> mp.mpf:
    """80-digit product used for the zero/recovery witness."""

    amplitudes, gammas = _validated_modes(amplitudes_per_cycle, gammas_per_cycle)
    with mp.workdps(80):
        out = mp.mpf("1")
        for amplitude, gamma in zip(amplitudes, gammas, strict=True):
            v_mp = mp.mpf(str(float(amplitude)))
            g_mp = mp.mpf(str(float(gamma)))
            if v_mp < g_mp:
                delta = mp.sqrt(g_mp * g_mp - v_mp * v_mp)
                factor = mp.exp(-g_mp * time_cycles) * (
                    mp.cosh(delta * time_cycles)
                    + (g_mp / delta) * mp.sinh(delta * time_cycles)
                )
            elif v_mp > g_mp:
                omega = mp.sqrt(v_mp * v_mp - g_mp * g_mp)
                factor = mp.exp(-g_mp * time_cycles) * (
                    mp.cos(omega * time_cycles)
                    + (g_mp / omega) * mp.sin(omega * time_cycles)
                )
            else:
                factor = mp.exp(-g_mp * time_cycles) * (1.0 + g_mp * time_cycles)
            out *= factor
        return +out


def build_report() -> dict[str, Any]:
    """Execute every preregistered gate and return a JSON-safe report."""

    source = OneOverFDriftSource()
    _assert_registered_defaults(source)
    gammas = source.gammas_per_cycle
    amplitudes = source.amplitudes_radns * float(source.cycle_time_ns)
    ratios = amplitudes / gammas
    strong_modes = np.flatnonzero(ratios > 1.0)

    oracle_values = np.asarray(
        [full_ctmc_coherence(t, amplitudes, gammas) for t in CTMC_ORACLE_TIMES]
    )
    product_values = product_ctmc_coherence(CTMC_ORACLE_TIMES, amplitudes, gammas)
    ctmc_oracle_error = float(np.max(np.abs(oracle_values - product_values)))

    zero_mode, zero_time = earliest_strong_zero(amplitudes, gammas)
    zero_value = abs(high_precision_product(zero_time, amplitudes, gammas))
    recovery_value = abs(high_precision_product(zero_time + mp.mpf("1"), amplitudes, gammas))

    grid = np.arange(
        0.0,
        HORIZON_CYCLES + 0.5 * GRID_STEP_CYCLES,
        GRID_STEP_CYCLES,
        dtype=np.float64,
    )
    exact_grid = product_ctmc_coherence(grid, amplitudes, gammas)
    ctmc_blp, ctmc_max_step = positive_excursion(exact_grid)

    gaussian = gaussian_surrogate_coherence(grid, amplitudes, gammas)
    gaussian_blp, gaussian_max_step = positive_excursion(gaussian)
    weak_gammas = 2.0 * amplitudes
    weak_product = product_ctmc_coherence(grid, amplitudes, weak_gammas)
    weak_blp, weak_max_step = positive_excursion(weak_product)

    rate_corruption = product_ctmc_coherence(CTMC_ORACLE_TIMES, amplitudes, 2.0 * gammas)
    rate_corruption_error = float(np.max(np.abs(oracle_values - rate_corruption)))
    omitted_product = product_ctmc_coherence(
        CTMC_ORACLE_TIMES,
        amplitudes[1:],
        gammas[1:],
    )
    omitted_mode_error = float(np.max(np.abs(oracle_values - omitted_product)))

    held_product = product_held_sequence(amplitudes, gammas, HORIZON_CYCLES)
    held_oracle = full_held_sequence(amplitudes, gammas, HORIZON_CYCLES)
    held_indexes = np.asarray(HELD_ORACLE_CYCLES, dtype=np.int64)
    held_oracle_error = float(
        np.max(np.abs(held_product[held_indexes] - held_oracle[held_indexes]))
    )
    held_blp, held_max_step = positive_excursion(held_product)

    checks = {
        "registered_defaults_unchanged": True,
        "exactly_three_strong_modes": int(strong_modes.size) == 3,
        "ctmc_product_matches_256_state_oracle": ctmc_oracle_error <= ORACLE_TOL,
        "ctmc_analytic_zero": zero_value <= mp.mpf("1e-60"),
        "ctmc_nonzero_recovery": recovery_value > mp.mpf("1e-12"),
        "ctmc_positive_excursion": ctmc_blp > MONOTONIC_TOL,
        "held_product_matches_256_state_oracle": held_oracle_error <= ORACLE_TOL,
        "held_positive_excursion_within_horizon": held_max_step > MONOTONIC_TOL,
        "gaussian_control_monotone": gaussian_max_step <= MONOTONIC_TOL,
        "all_weak_control_monotone": weak_max_step <= MONOTONIC_TOL,
        "rate_convention_corruption_rejected": rate_corruption_error > 100.0 * ORACLE_TOL,
        "omitted_mode_corruption_rejected": omitted_mode_error > 100.0 * ORACLE_TOL,
        "production_qec_bridge_claimed": False,
    }
    continuous_implementation_passed = all(
        checks[key]
        for key in (
            "registered_defaults_unchanged",
            "exactly_three_strong_modes",
            "ctmc_product_matches_256_state_oracle",
            "gaussian_control_monotone",
            "all_weak_control_monotone",
            "rate_convention_corruption_rejected",
            "omitted_mode_corruption_rejected",
        )
    )
    held_implementation_passed = all(
        checks[key]
        for key in (
            "registered_defaults_unchanged",
            "held_product_matches_256_state_oracle",
        )
    )
    implementation_passed = continuous_implementation_passed and held_implementation_passed
    continuous_positive = all(
        checks[key]
        for key in (
            "ctmc_analytic_zero",
            "ctmc_nonzero_recovery",
            "ctmc_positive_excursion",
        )
    )
    ctmc_verdict = diagnostic_verdict(
        implementation_passed=continuous_implementation_passed,
        positive_excursion_found=continuous_positive,
    )
    held_verdict = diagnostic_verdict(
        implementation_passed=held_implementation_passed,
        positive_excursion_found=checks["held_positive_excursion_within_horizon"],
    )

    report: dict[str, Any] = {
        "schema": "error_coupling_simulator.finite_rtn_exact_cpdiv_gate.v1",
        "preregistration": "docs/twin_validation/finite_rtn_exact_cpdiv_prereg_2026-07-13.md",
        "claim_boundary": {
            "tested": [
                "continuous_symmetric_ctmc_free_induction_diagnostic",
                "cycle_held_free_induction_diagnostic",
            ],
            "not_tested": [
                "production_source_to_theta_fanout",
                "production_qec_channel",
                "syndrome_record_markov_order",
                "process_tensor_quantum_memory",
                "decoder_logical_error_rate",
            ],
            "production_qec_bridge": "OPEN",
        },
        "source_defaults": {
            "amplitude_radns": float(source.amplitude_radns),
            "n_fluctuators": int(source.n_fluctuators),
            "gamma_min_per_cycle": float(source.gamma_min_per_cycle),
            "gamma_max_per_cycle": float(source.gamma_max_per_cycle),
            "cycle_time_ns": float(source.cycle_time_ns),
            "amplitudes_per_cycle": amplitudes.tolist(),
            "gammas_per_cycle": gammas.tolist(),
            "amplitude_to_gamma_ratios": ratios.tolist(),
            "strong_mode_indexes": strong_modes.tolist(),
            "value_provenance": "project-design_not_hardware-calibrated",
        },
        "registered_numerics": {
            "horizon_cycles": HORIZON_CYCLES,
            "grid_step_cycles": GRID_STEP_CYCLES,
            "oracle_tolerance": ORACLE_TOL,
            "monotonic_tolerance": MONOTONIC_TOL,
            "ctmc_oracle_times": list(CTMC_ORACLE_TIMES),
            "held_oracle_cycles": list(HELD_ORACLE_CYCLES),
        },
        "continuous_ctmc_diagnostic": {
            "verdict": ctmc_verdict,
            "product_vs_256_state_max_abs_error": ctmc_oracle_error,
            "earliest_zero_mode": int(zero_mode),
            "earliest_zero_time_cycles": mp.nstr(zero_time, 40),
            "abs_product_at_zero": mp.nstr(zero_value, 20),
            "abs_product_one_cycle_after_zero": mp.nstr(recovery_value, 20),
            "grid_blp_positive_excursion_estimate": ctmc_blp,
            "grid_max_positive_step": ctmc_max_step,
            "gaussian_control_positive_excursion": gaussian_blp,
            "gaussian_control_max_positive_step": gaussian_max_step,
            "all_weak_control_positive_excursion": weak_blp,
            "all_weak_control_max_positive_step": weak_max_step,
            "rate_convention_corruption_max_abs_error": rate_corruption_error,
            "omitted_mode_corruption_max_abs_error": omitted_mode_error,
        },
        "cycle_held_diagnostic": {
            "verdict": held_verdict,
            "product_vs_256_state_max_abs_error": held_oracle_error,
            "integer_blp_positive_excursion": held_blp,
            "integer_max_positive_step": held_max_step,
        },
        "checks": checks,
        "continuous_implementation_gate_passed": continuous_implementation_passed,
        "held_implementation_gate_passed": held_implementation_passed,
        "implementation_gate_passed": implementation_passed,
        "overall_verdict": (
            "GATE_PASS_DIAGNOSTIC_ONLY" if implementation_passed else "IMPLEMENTATION_GATE_FAILED"
        ),
    }
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    report["content_hash_sha256"] = hashlib.sha256(canonical).hexdigest()
    return report


def _validated_modes(
    amplitudes_per_cycle: Sequence[float],
    gammas_per_cycle: Sequence[float],
) -> tuple[np.ndarray, np.ndarray]:
    amplitudes = np.asarray(amplitudes_per_cycle, dtype=np.float64)
    gammas = np.asarray(gammas_per_cycle, dtype=np.float64)
    if amplitudes.ndim != 1 or gammas.ndim != 1 or amplitudes.size == 0:
        raise ValueError("amplitudes and gammas must be nonempty vectors")
    if amplitudes.shape != gammas.shape:
        raise ValueError("amplitudes and gammas must have identical shapes")
    if np.any(~np.isfinite(amplitudes)) or np.any(~np.isfinite(gammas)):
        raise ValueError("amplitudes and gammas must be finite")
    if np.any(amplitudes < 0.0) or np.any(gammas <= 0.0):
        raise ValueError("amplitudes must be nonnegative and gammas positive")
    return amplitudes, gammas


def _assert_registered_defaults(source: OneOverFDriftSource) -> None:
    expected = {
        "amplitude_radns": 1.0e-4,
        "n_fluctuators": 8,
        "gamma_min_per_cycle": 0.005,
        "gamma_max_per_cycle": 0.5,
        "cycle_time_ns": 1_000.0,
    }
    actual = {key: getattr(source, key) for key in expected}
    if actual != expected:
        raise RuntimeError(f"registered OneOverFDriftSource defaults drifted: {actual!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/twin_validation/finite_rtn_exact_cpdiv_gate.json"),
    )
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FINITE_RTN_GATE",
        report["overall_verdict"],
        "continuous=",
        report["continuous_ctmc_diagnostic"]["verdict"],
        "held=",
        report["cycle_held_diagnostic"]["verdict"],
        "artifact=",
        args.output,
        "sha256=",
        report["content_hash_sha256"],
    )
    if not report["implementation_gate_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
