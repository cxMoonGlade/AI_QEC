from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
import math
import sys

__all__ = [
    "NUMERICAL_ZERO",
    "scaled_exp_multiply",
    "scaled_product_ratio",
    "shifted_probability_from_odds",
]

NUMERICAL_ZERO = 1e-12

_MIN_OPEN_PROBABILITY = math.nextafter(0.0, 1.0)
_MAX_OPEN_PROBABILITY = math.nextafter(1.0, 0.0)
_MAX_BINARY64_EXP_SHIFT = (
    math.log(sys.float_info.max)
    - math.log(_MIN_OPEN_PROBABILITY)
    + math.log(2.0)
)


def _decimal_to_float64(value: Decimal) -> float:
    """Round a Decimal to binary64, including subnormal ties-to-even.

    CPython's Decimal-to-float underflow conversion rounds an exact half of the
    smallest subnormal upward on supported builds. Handle the subnormal lattice
    explicitly so a nonrepresentable positive value cannot become a fabricated
    structural minimum.
    """

    if not value.is_finite():
        return math.copysign(math.inf, -1.0 if value.is_signed() else 1.0)
    if value.is_zero():
        return math.copysign(0.0, -1.0 if value.is_signed() else 1.0)
    sign = -1.0 if value.is_signed() else 1.0
    magnitude = abs(value)
    minimum_normal = Decimal.from_float(sys.float_info.min)
    if magnitude < minimum_normal:
        minimum_subnormal = Decimal.from_float(_MIN_OPEN_PROBABILITY)
        with localcontext() as context:
            context.prec = 300
            units = (magnitude / minimum_subnormal).to_integral_value(
                rounding=ROUND_HALF_EVEN
            )
        unit_count = int(units)
        if unit_count == 0:
            return math.copysign(0.0, sign)
        rounded = math.ldexp(float(unit_count), -1074)
        return math.copysign(rounded, sign)
    return float(value)


def _exact_float64_mean(values: Iterable[float], *, name: str) -> float:
    """Average finite binary64 values once, rejecting a false rounded zero."""

    numeric_values = tuple(float(value) for value in values)
    if not numeric_values:
        raise ValueError(f"{name} requires at least one value")
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError(f"{name} values must be finite")
    exact = sum((Fraction.from_float(value) for value in numeric_values), Fraction())
    exact /= len(numeric_values)
    if exact == 0:
        return 0.0
    recovered = float(exact)
    if not math.isfinite(recovered) or recovered == 0.0:
        raise ValueError(f"{name} is not representable as a nonzero float64")
    return recovered


def scaled_exp_multiply(base: float, shift: float, *, name: str) -> float:
    """Return the representable positive float64 value ``base * exp(shift)``.

    A normal finite exponential uses the ordinary multiplication so established
    interior results remain bit-identical. Overflowing, zero, or subnormal
    exponential intermediates use a high-precision exact-float product and
    exponential; a subnormal ``exp(shift)`` is never trusted because its lost
    relative precision can be magnified into a badly rounded normal product.
    """

    base_value = float(base)
    shift_value = float(shift)
    if not math.isfinite(base_value) or base_value <= 0.0:
        raise ValueError(f"{name} base must be finite and > 0, got {base_value!r}")
    if not math.isfinite(shift_value):
        raise ValueError(f"{name} shift must be finite, got {shift_value!r}")
    if shift_value == 0.0:
        return base_value

    try:
        exp_shift = math.exp(shift_value)
    except OverflowError:
        exp_shift = math.inf
    if math.isfinite(exp_shift) and exp_shift >= sys.float_info.min:
        direct = float(base_value * exp_shift)
        if (
            math.isfinite(direct)
            and sys.float_info.min <= direct < sys.float_info.max
        ):
            return direct

    # No binary64 base can compensate a larger exponent span.
    if abs(shift_value) > _MAX_BINARY64_EXP_SHIFT:
        raise ValueError(f"{name} is not representable as a positive float64")

    # This path is rare and boundary-sensitive. Decimal.from_float preserves the
    # exact binary64 inputs. Boundary routing avoids trusting a rounded normal
    # exp intermediate when the final product is subnormal or at DBL_MAX.
    with localcontext() as context:
        context.prec = 200
        recovered = _decimal_to_float64(
            Decimal.from_float(base_value)
            * Decimal.from_float(shift_value).exp()
        )
    if not math.isfinite(recovered) or recovered <= 0.0:
        raise ValueError(f"{name} is not representable as a positive float64")
    return recovered


def scaled_product_ratio(
    left: float,
    right: float,
    denominator: float,
    *,
    name: str,
) -> float:
    """Return a representable float64 ``left * right / denominator``.

    The ordinary operation order is retained when its ratio and final-product
    intermediates are safely normal. Otherwise an exact-input Decimal fallback
    recovers the final value without trusting an overflowing or low-precision
    subnormal intermediate.
    """

    left_value = float(left)
    right_value = float(right)
    denominator_value = float(denominator)
    if not math.isfinite(left_value) or not math.isfinite(right_value):
        raise ValueError(f"{name} numerator factors must be finite")
    if not math.isfinite(denominator_value) or denominator_value <= 0.0:
        raise ValueError(f"{name} denominator must be finite and > 0")
    if left_value == 0.0 or right_value == 0.0:
        negative = (left_value < 0.0) != (right_value < 0.0)
        return -0.0 if negative else 0.0

    ratio = right_value / denominator_value
    if math.isfinite(ratio) and abs(ratio) >= sys.float_info.min:
        direct = float(left_value * ratio)
        if (
            math.isfinite(direct)
            and sys.float_info.min <= abs(direct) < sys.float_info.max
        ):
            return direct

    exact = (
        Fraction.from_float(left_value)
        * Fraction.from_float(right_value)
        / Fraction.from_float(denominator_value)
    )
    try:
        recovered = float(exact)
    except OverflowError:
        recovered = math.copysign(math.inf, 1.0 if exact > 0 else -1.0)
    if not math.isfinite(recovered) or recovered == 0.0:
        raise ValueError(f"{name} is not representable as a finite float64")
    return recovered


def shifted_probability_from_odds(
    base_probability: float,
    shift: float,
    *,
    name: str,
) -> float:
    """Apply a finite log-odds shift without forming ``logit(p) + shift``.

    The value path is ``odds * exp(shift) / (1 + odds * exp(shift))``.
    Exact-float decimal comparison is used only when the scaled odds lands on
    a conservative float64 open-interval boundary, where rounded intermediates
    cannot safely distinguish an inside point from an outside point.
    """

    probability = float(base_probability)
    shift_value = float(shift)
    if not math.isfinite(probability) or not 0.0 < probability < 1.0:
        raise ValueError(f"{name} base probability must be finite and in (0, 1)")
    if not math.isfinite(shift_value):
        raise ValueError(f"{name} shift must be finite, got {shift_value!r}")
    if shift_value == 0.0:
        return probability

    odds = probability / (1.0 - probability)
    try:
        scaled_odds = scaled_exp_multiply(odds, shift_value, name=f"{name} odds")
    except ValueError as exc:
        raise ValueError(
            f"{name} probability is outside the representable float64 open interval"
        ) from exc

    if scaled_odds <= 1.0:
        result = scaled_odds / (1.0 + scaled_odds)
    else:
        result = 1.0 - 1.0 / (1.0 + scaled_odds)
    if result in (0.0, _MIN_OPEN_PROBABILITY, _MAX_OPEN_PROBABILITY, 1.0):
        if not _exact_shifted_log_odds_is_in_open_float64_domain(
            probability,
            shift_value,
        ):
            raise ValueError(
                f"{name} probability is outside the representable float64 open interval"
            )
        if result in (0.0, 1.0):
            raise ValueError(f"{name} probability rounded to a structural endpoint")
        return float(result)
    return float(result)


def _exact_shifted_log_odds_is_in_open_float64_domain(
    probability: float,
    shift: float,
) -> bool:
    """Classify a cancellation-sensitive boundary from the exact float inputs."""

    with localcontext() as context:
        # A minimum-subnormal shift can move an endpoint probability outside
        # the open domain only in the 324th decimal place. Retain enough
        # precision to classify that cross-scale case rather than accepting a
        # rounded endpoint as unchanged.
        context.prec = 1200
        one = Decimal(1)
        probability_decimal = Decimal.from_float(float(probability))
        shifted_log_odds = (
            probability_decimal / (one - probability_decimal)
        ).ln() + Decimal.from_float(float(shift))
        min_probability = Decimal.from_float(_MIN_OPEN_PROBABILITY)
        max_probability = Decimal.from_float(_MAX_OPEN_PROBABILITY)
        lower = (min_probability / (one - min_probability)).ln()
        upper = (max_probability / (one - max_probability)).ln()
        return bool(lower <= shifted_log_odds <= upper)
