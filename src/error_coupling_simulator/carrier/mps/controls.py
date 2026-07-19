from __future__ import annotations

"""Law-neutral, lossless normalization for restricted MPS controls.

These helpers only validate Python-facing control values.  They do not choose
scientific defaults, numerical tolerances, execution routes, or acceptance
policy.  In particular, integer controls use ``operator.index`` so floats,
strings, and booleans cannot be silently narrowed before a public MPS entry
point records or acts on them.
"""

import math
import operator
from numbers import Real
from typing import Any, Iterable


def normalize_mps_bool(value: Any, *, name: str) -> bool:
    """Return an exact bool, rejecting truthy substitutes."""

    if type(value) is not bool:
        raise TypeError(f"{name} must be bool, got {value!r}")
    return value


def normalize_mps_device(value: Any, *, name: str = "device") -> str:
    """Return a nonempty device string without calling the device backend."""

    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string, got {value!r}")
    if not value:
        raise ValueError(f"{name} must be a nonempty string")
    return value


def normalize_mps_index(
    value: Any,
    *,
    name: str,
    minimum: int | None = None,
) -> int:
    """Return an integer control without lossy ``int(...)`` coercion."""

    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer, not bool")
    try:
        normalized = operator.index(value)
    except TypeError as exc:
        raise TypeError(f"{name} must be an integer, got {value!r}") from exc
    result = int(normalized)
    if minimum is not None and result < minimum:
        qualifier = "positive" if minimum == 1 else f">= {minimum}"
        raise ValueError(f"{name} must be {qualifier}, got {result}")
    return result


def normalize_optional_mps_index(
    value: Any,
    *,
    name: str,
    minimum: int | None = None,
) -> int | None:
    if value is None:
        return None
    return normalize_mps_index(value, name=name, minimum=minimum)


def normalize_mps_max_bond(
    value: Any,
    *,
    allow_none: bool = True,
) -> int | None:
    """Normalize the shared MPS bond cap without lossy coercion."""

    if value is None:
        if allow_none:
            return None
        raise TypeError("max_bond must be an integer, got None")
    return normalize_mps_index(value, name="max_bond", minimum=1)


def normalize_mps_index_sequence(
    values: Iterable[Any],
    *,
    name: str,
    minimum: int | None = None,
    require_nonempty: bool = False,
) -> tuple[int, ...]:
    """Normalize an iterable of integer controls, naming the bad element."""

    if isinstance(values, (str, bytes, bytearray)):
        raise TypeError(f"{name} must be an iterable of integers")
    try:
        raw_values = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{name} must be an iterable of integers") from exc
    if require_nonempty and not raw_values:
        raise ValueError(f"{name} must not be empty")
    return tuple(
        normalize_mps_index(
            value,
            name=f"{name}[{index}]",
            minimum=minimum,
        )
        for index, value in enumerate(raw_values)
    )


def normalize_mps_choice(
    value: Any,
    *,
    name: str,
    choices: tuple[str, ...],
) -> str:
    """Validate a string-valued enumerated control without ``str(...)``."""

    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string, got {value!r}")
    if value not in choices:
        allowed = ", ".join(choices)
        raise ValueError(f"{name} must be one of: {allowed}")
    return value


def normalize_mps_finite_real(
    value: Any,
    *,
    name: str,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    """Normalize a finite real control while rejecting bool and text."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number, got {value!r}")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite, got {value!r}")
    if minimum is not None and result < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {result}")
    if maximum is not None and result > maximum:
        raise ValueError(f"{name} must be <= {maximum}, got {result}")
    return result


def normalize_optional_mps_nonnegative_real(
    value: Any,
    *,
    name: str,
) -> float | None:
    """Normalize an optional finite, nonnegative MPS control."""

    if value is None:
        return None
    return normalize_mps_finite_real(
        value,
        name=name,
        minimum=0.0,
    )
