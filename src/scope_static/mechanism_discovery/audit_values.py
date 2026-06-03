from __future__ import annotations


def optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def optional_difference(left: object, right: object) -> float | None:
    if left is None or right is None:
        return None
    return float(left) - float(right)
