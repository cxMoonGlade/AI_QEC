from __future__ import annotations

NUMERICAL_ZERO = 1e-12
NUMERICAL_FLOOR = NUMERICAL_ZERO


def positive_floor(value: float) -> float:
    """Floor a floating numerical quantity away from exact zero."""

    return max(NUMERICAL_ZERO, float(value))


def probability_floor(value: float) -> float:
    """Floor a probability away from exact zero without changing its upper cap."""

    return min(1.0, positive_floor(float(value)))
