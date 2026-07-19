from __future__ import annotations

"""Law-neutral float64 probability-mass mechanics for restricted MPS routes.

This module validates and preserves raw candidate mass.  It deliberately does
not decide whether a route requires unit mass: QT Kraus/projective operations
and MCWF first-order jumps have different acceptance laws.
"""

from collections.abc import Iterable
from dataclasses import dataclass
import math
from numbers import Real

import torch

from ...numerics import scaled_product_ratio


@dataclass(frozen=True, slots=True)
class RawProbabilityMass:
    values: tuple[float, ...]
    total: float
    residual_from_one: float
    positive_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.values, tuple):
            raise TypeError("RawProbabilityMass.values must be a tuple")
        if not self.values:
            raise ValueError("RawProbabilityMass.values must not be empty")
        normalized = tuple(
            _finite_nonnegative_real(
                value,
                name=f"RawProbabilityMass.values[{index}]",
            )
            for index, value in enumerate(self.values)
        )
        try:
            expected_total = float(math.fsum(normalized))
        except OverflowError as exc:
            raise ValueError("RawProbabilityMass total mass must be finite") from exc
        if not math.isfinite(expected_total):
            raise ValueError("RawProbabilityMass total mass must be finite")
        total = _finite_nonnegative_real(
            self.total,
            name="RawProbabilityMass.total",
        )
        if total != expected_total:
            raise ValueError("RawProbabilityMass.total does not match values")
        residual = _finite_nonnegative_real(
            self.residual_from_one,
            name="RawProbabilityMass.residual_from_one",
        )
        if residual != abs(expected_total - 1.0):
            raise ValueError(
                "RawProbabilityMass.residual_from_one does not match total"
            )
        if not isinstance(self.positive_indices, tuple) or any(
            type(index) is not int for index in self.positive_indices
        ):
            raise TypeError(
                "RawProbabilityMass.positive_indices must be a tuple of integers"
            )
        expected_indices = tuple(
            index for index, value in enumerate(normalized) if value > 0.0
        )
        if self.positive_indices != expected_indices:
            raise ValueError(
                "RawProbabilityMass.positive_indices does not match values"
            )
        object.__setattr__(self, "values", normalized)
        object.__setattr__(self, "total", total)
        object.__setattr__(self, "residual_from_one", residual)


def _finite_nonnegative_real(value: object, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number, not bool or a coercible value")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    if normalized < 0.0:
        raise ValueError(f"{name} must be nonnegative")
    return 0.0 if normalized == 0.0 else normalized


def validate_raw_probability_mass(
    values: Iterable[float],
    *,
    name: str,
) -> RawProbabilityMass:
    """Freeze finite nonnegative candidates without normalizing their mass."""

    if isinstance(values, (str, bytes)):
        raise TypeError(f"{name} must be an iterable of real probability values")
    try:
        raw_values = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{name} must be an iterable of real probability values") from exc
    if not raw_values:
        raise ValueError(f"{name} must contain at least one probability value")
    normalized = tuple(
        _finite_nonnegative_real(value, name=f"{name}[{index}]")
        for index, value in enumerate(raw_values)
    )
    try:
        total = float(math.fsum(normalized))
    except OverflowError as exc:
        raise ValueError(f"{name} total mass must be finite") from exc
    if not math.isfinite(total):
        raise ValueError(f"{name} total mass must be finite")
    return RawProbabilityMass(
        values=normalized,
        total=total,
        residual_from_one=abs(total - 1.0),
        positive_indices=tuple(
            index for index, value in enumerate(normalized) if value > 0.0
        ),
    )


def multiply_probability_values(left: float, right: float, *, name: str) -> float:
    """Multiply raw masses while preserving structural zero versus underflow."""

    left_value = _finite_nonnegative_real(left, name=f"{name} left")
    right_value = _finite_nonnegative_real(right, name=f"{name} right")
    if left_value == 0.0 or right_value == 0.0:
        return 0.0
    return scaled_product_ratio(
        left_value,
        right_value,
        1.0,
        name=name,
    )


def one_minus_exp_neg_probability(exponent: float, *, name: str) -> float:
    """Return ``1-exp(-x)`` without cancellation or a false open endpoint."""

    value = _finite_nonnegative_real(exponent, name=f"{name} exponent")
    if value == 0.0:
        return 0.0
    probability = -math.expm1(-value)
    if not math.isfinite(probability) or not 0.0 < probability < 1.0:
        raise ValueError(
            f"{name} is not representable in the open float64 probability interval"
        )
    return float(probability)


def sample_raw_probability_mass(
    mass: RawProbabilityMass,
    *,
    device: str,
    generator: torch.Generator,
) -> int:
    """Draw from validated positive candidates and map to the raw index order."""

    if not isinstance(mass, RawProbabilityMass):
        raise TypeError("mass must be a validated RawProbabilityMass")
    if not mass.positive_indices:
        raise ValueError("cannot sample a raw probability mass with no positive candidate")
    positive = tuple(mass.values[index] for index in mass.positive_indices)
    probabilities = torch.tensor(positive, dtype=torch.float64, device=device)
    total = torch.sum(probabilities)
    probabilities = probabilities / total
    local_index = int(
        torch.multinomial(probabilities, 1, generator=generator)
        .detach()
        .cpu()
        .item()
    )
    return int(mass.positive_indices[local_index])


__all__ = [
    "RawProbabilityMass",
    "multiply_probability_values",
    "one_minus_exp_neg_probability",
    "sample_raw_probability_mass",
    "validate_raw_probability_mass",
]
