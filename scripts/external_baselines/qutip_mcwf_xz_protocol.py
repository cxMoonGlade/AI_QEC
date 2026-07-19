#!/usr/bin/env python3
"""Neutral protocol and statistics for the isolated QuTiP MCWF X/Z check.

This module is intentionally standard-library only.  It is shared by the
project-side orchestrator and the isolated baseline worker, and imports no
simulator implementation or external solver.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from pathlib import Path
from typing import Any


FIXTURE_SCHEMA = "ai_qec.neutral.mcwf_xz_fixture.v1"
EXPECTED_FIXTURE_SHA256 = (
    "84bb673ab94de1a477a7c770894a2b3add8bc664f90203db4b1ed127cb36c7fa"
)
EXPECTED_MEASUREMENT_KEYS = (
    "mx_before",
    "mz_before",
    "mx_after",
    "mz_after",
)
EXPECTED_MEASUREMENT_TARGETS = (0, 1, 0, 1)
EXPECTED_MEASUREMENT_BASES = ("X", "Z", "X", "Z")
EXPECTED_RESET_AFTER = (True, True, False, False)
EXPECTED_RESET_STATES = {"X": "|+>", "Z": "|0>"}


def load_fixture(path: Path) -> dict[str, Any]:
    """Load and strictly validate the frozen neutral two-qubit fixture."""

    resolved = Path(path)
    observed_sha256 = fixture_sha256(resolved)
    if observed_sha256 != EXPECTED_FIXTURE_SHA256:
        raise ValueError(
            "neutral MCWF X/Z fixture SHA-256 mismatch: "
            f"expected {EXPECTED_FIXTURE_SHA256}, observed {observed_sha256}"
        )
    raw = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError("neutral MCWF X/Z fixture must be a JSON object")
    fixture = dict(raw)
    if fixture.get("schema") != FIXTURE_SCHEMA:
        raise ValueError("unsupported neutral MCWF X/Z fixture schema")
    if fixture.get("fixture_id") != "two_qubit_t1_ordered_xz_reset":
        raise ValueError("unexpected neutral MCWF X/Z fixture id")
    if fixture.get("num_qubits") != 2:
        raise ValueError("neutral MCWF X/Z fixture must contain two qubits")
    if fixture.get("local_dims") != [2, 2]:
        raise ValueError("neutral MCWF X/Z fixture local_dims must be [2, 2]")
    if fixture.get("initial_levels") != [0, 1]:
        raise ValueError("neutral MCWF X/Z fixture initial_levels must be [0, 1]")
    _require_exact_sequence(
        fixture.get("measurement_keys"),
        EXPECTED_MEASUREMENT_KEYS,
        "measurement_keys",
    )
    _require_exact_sequence(
        fixture.get("measurement_targets"),
        EXPECTED_MEASUREMENT_TARGETS,
        "measurement_targets",
    )
    _require_exact_sequence(
        fixture.get("measurement_bases"),
        EXPECTED_MEASUREMENT_BASES,
        "measurement_bases",
    )
    _require_exact_sequence(
        fixture.get("reset_after"),
        EXPECTED_RESET_AFTER,
        "reset_after",
    )
    if fixture.get("reset_states") != EXPECTED_RESET_STATES:
        raise ValueError("neutral MCWF X/Z reset-state contract drifted")
    gamma_1 = _positive_finite(
        fixture.get("gamma_1_per_ns"), "gamma_1_per_ns"
    )
    _zero(fixture.get("gamma_phi_per_ns"), "gamma_phi_per_ns")
    duration = _positive_finite(
        fixture.get("evolution_duration_ns"),
        "evolution_duration_ns",
    )
    target_survival = _positive_finite(
        fixture.get("target_survival_probability"),
        "target_survival_probability",
    )
    if target_survival != 0.25:
        raise ValueError("neutral fixture target survival must be exactly 0.25")
    if abs(math.exp(-gamma_1 * duration) - target_survival) > 1.0e-15:
        raise ValueError("neutral fixture gamma-duration survival drifted")
    _positive_integer(fixture.get("microstep_count"), "microstep_count")
    if _positive_integer(
        fixture.get("trajectory_count"), "trajectory_count"
    ) < 128:
        raise ValueError("trajectory_count must be at least 128")
    for key in (
        "project_rng_seed",
        "qutip_mcwf_seed",
        "qutip_measurement_seed",
    ):
        _positive_integer(fixture.get(key), key)
    alpha = _positive_finite(fixture.get("comparison_alpha"), "comparison_alpha")
    if not alpha < 1.0:
        raise ValueError("comparison_alpha must be less than one")
    numerical_zero = _positive_finite(
        fixture.get("numerical_zero"), "numerical_zero"
    )
    if numerical_zero != 1.0e-12:
        raise ValueError("neutral fixture numerical_zero must be exactly 1e-12")
    return fixture


def fixture_sha256(path: Path) -> str:
    """Return the byte-level SHA-256 of one neutral fixture file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def analytic_binary_distribution(
    fixture: Mapping[str, Any],
) -> dict[tuple[int, int, int, int], float]:
    """Return the hand-derived Lindblad Record law for the frozen fixture."""

    gamma = _positive_finite(fixture.get("gamma_1_per_ns"), "gamma_1_per_ns")
    duration = _positive_finite(
        fixture.get("evolution_duration_ns"), "evolution_duration_ns"
    )
    survival = math.exp(-gamma * duration)
    p_x_before_zero = 0.5
    p_z_before_one = survival
    p_x_after_zero = 0.5 * (1.0 + math.sqrt(survival))
    law: dict[tuple[int, int, int, int], float] = {}
    for x_before in (0, 1):
        p_x_before = p_x_before_zero if x_before == 0 else 1.0 - p_x_before_zero
        for z_before in (0, 1):
            p_z_before = p_z_before_one if z_before == 1 else 1.0 - p_z_before_one
            for x_after in (0, 1):
                p_x_after = p_x_after_zero if x_after == 0 else 1.0 - p_x_after_zero
                law[(x_before, z_before, x_after, 0)] = (
                    p_x_before * p_z_before * p_x_after
                )
    return law


def total_variation(
    left: Mapping[Sequence[int], float],
    right: Mapping[Sequence[int], float],
) -> float:
    """Compute TV after normalizing two finite nonnegative laws."""

    normalized_left = _normalized_distribution(left, "left")
    normalized_right = _normalized_distribution(right, "right")
    support = set(normalized_left) | set(normalized_right)
    return 0.5 * math.fsum(
        abs(normalized_left.get(row, 0.0) - normalized_right.get(row, 0.0))
        for row in support
    )


def binary_column_marginal(
    distribution: Mapping[Sequence[int], float], *, column: int
) -> dict[tuple[int], float]:
    """Return one binary-column marginal of a finite Record law."""

    if isinstance(column, bool) or not isinstance(column, int) or column < 0:
        raise ValueError("column must be a nonnegative integer")
    normalized = _normalized_distribution(distribution, "record")
    marginal = {(0,): 0.0, (1,): 0.0}
    for row, mass in normalized.items():
        if column >= len(row):
            raise ValueError("marginal column is outside the Record width")
        value = row[column]
        if value not in (0, 1):
            raise ValueError("binary marginal requires a binary Record column")
        marginal[(value,)] += mass
    return marginal


def population_rate_x_coherence_mutation(
    fixture: Mapping[str, Any],
) -> dict[tuple[int], float]:
    """Return the X-after law for the load-bearing ``sqrt(s) -> s`` mutation."""

    gamma = _positive_finite(fixture.get("gamma_1_per_ns"), "gamma_1_per_ns")
    duration = _positive_finite(
        fixture.get("evolution_duration_ns"), "evolution_duration_ns"
    )
    survival = math.exp(-gamma * duration)
    return {
        (0,): 0.5 * (1.0 + survival),
        (1,): 0.5 * (1.0 - survival),
    }


def canonical_content_hash(payload: Mapping[str, Any]) -> str:
    """Hash one JSON payload while excluding its top-level content hash."""

    normalized = dict(payload)
    normalized.pop("content_hash", None)
    encoded = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def multinomial_tv_radius(
    *, sample_count: int, alphabet_size: int, alpha: float
) -> float:
    """Weissman-style finite-sample TV radius for one multinomial law.

    The bound used is ``P(TV(phat, p) >= r) <=
    (2**k - 2) exp(-2 n r**2)`` for alphabet size ``k``.
    """

    n = _positive_integer(sample_count, "sample_count")
    k = _positive_integer(alphabet_size, "alphabet_size")
    risk = _positive_finite(alpha, "alpha")
    if risk >= 1.0:
        raise ValueError("alpha must be less than one")
    prefactor = math.pow(2.0, k) - 2.0
    if prefactor <= 0.0:
        return 0.0
    radius = math.sqrt(math.log(prefactor / risk) / (2.0 * n))
    return min(1.0, radius)


def two_sample_tv_comparison(
    left: Mapping[Sequence[int], float],
    right: Mapping[Sequence[int], float],
    *,
    left_sample_count: int,
    right_sample_count: int,
    alphabet_size: int,
    alpha: float,
) -> dict[str, Any]:
    """Apply a Bonferroni two-sample multinomial TV gate."""

    risk = _positive_finite(alpha, "alpha")
    if risk >= 1.0:
        raise ValueError("alpha must be less than one")
    left_radius = multinomial_tv_radius(
        sample_count=left_sample_count,
        alphabet_size=alphabet_size,
        alpha=risk / 2.0,
    )
    right_radius = multinomial_tv_radius(
        sample_count=right_sample_count,
        alphabet_size=alphabet_size,
        alpha=risk / 2.0,
    )
    simultaneous_radius = min(1.0, left_radius + right_radius)
    observed = total_variation(left, right)
    return {
        "schema": "ai_qec.external_baseline.two_sample_multinomial_tv.v1",
        "total_variation": observed,
        "left_sample_count": int(left_sample_count),
        "right_sample_count": int(right_sample_count),
        "alphabet_size": int(alphabet_size),
        "alpha": risk,
        "left_tv_radius": left_radius,
        "right_tv_radius": right_radius,
        "simultaneous_tv_radius": simultaneous_radius,
        "gate_rule": "observed_total_variation <= left_radius + right_radius",
        "passed": bool(observed <= simultaneous_radius),
    }


def flip_binary_column(
    distribution: Mapping[Sequence[int], float], *, column: int
) -> dict[tuple[int, ...], float]:
    """Deterministically corrupt one binary Record column."""

    if isinstance(column, bool) or not isinstance(column, int) or column < 0:
        raise ValueError("column must be a nonnegative integer")
    flipped: dict[tuple[int, ...], float] = {}
    for raw_row, raw_mass in distribution.items():
        row = tuple(int(value) for value in raw_row)
        if column >= len(row):
            raise ValueError("corruption column is outside the Record width")
        if any(value not in (0, 1) for value in row):
            raise ValueError("binary corruption requires binary Record rows")
        corrupted = list(row)
        corrupted[column] ^= 1
        key = tuple(corrupted)
        flipped[key] = flipped.get(key, 0.0) + float(raw_mass)
    return flipped


def _normalized_distribution(
    distribution: Mapping[Sequence[int], float], name: str
) -> dict[tuple[int, ...], float]:
    if not isinstance(distribution, Mapping) or not distribution:
        raise ValueError(f"{name} distribution must be a nonempty mapping")
    normalized: dict[tuple[int, ...], float] = {}
    width: int | None = None
    for raw_row, raw_mass in distribution.items():
        row = tuple(int(value) for value in raw_row)
        if width is None:
            width = len(row)
        if not row or len(row) != width:
            raise ValueError(f"{name} distribution has inconsistent row width")
        if isinstance(raw_mass, bool):
            raise TypeError(f"{name} distribution mass must be real, not bool")
        mass = float(raw_mass)
        if not math.isfinite(mass) or mass < 0.0:
            raise ValueError(f"{name} distribution mass must be finite and nonnegative")
        normalized[row] = normalized.get(row, 0.0) + mass
    total = math.fsum(normalized.values())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError(f"{name} distribution must have positive finite mass")
    return {row: mass / total for row, mass in normalized.items()}


def _require_exact_sequence(value: object, expected: Sequence[object], name: str) -> None:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{name} must be a JSON array")
    if tuple(value) != tuple(expected):
        raise ValueError(f"neutral MCWF X/Z {name} drifted")


def _positive_finite(value: object, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be real, not bool")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return normalized


def _zero(value: object, name: str) -> None:
    if isinstance(value, bool) or float(value) != 0.0:
        raise ValueError(f"{name} must be exactly zero")


def _positive_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value
