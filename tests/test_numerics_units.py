from __future__ import annotations

import math
import sys

import mpmath
import numpy as np
import pytest

import error_coupling_simulator.numerics as numerics


def _mp_float(value: float) -> mpmath.mpf:
    numerator, denominator = float(value).as_integer_ratio()
    return mpmath.mpf(numerator) / denominator


def _ulp_distance(left: float, right: float) -> int:
    left_bits = int(np.asarray(float(left), dtype=np.float64).view(np.uint64))
    right_bits = int(np.asarray(float(right), dtype=np.float64).view(np.uint64))
    return abs(left_bits - right_bits)


def _raises_exact(message: str, call) -> None:
    with pytest.raises(ValueError) as excinfo:
        call()
    assert str(excinfo.value) == message


def test_public_surface_is_explicit_and_does_not_export_implementation_modules() -> None:
    assert numerics.__all__ == [
        "NUMERICAL_ZERO",
        "scaled_exp_multiply",
        "scaled_product_ratio",
        "shifted_probability_from_odds",
    ]


def test_scaled_exp_multiply_validates_inputs_and_preserves_zero_shift_bits() -> None:
    for base in (math.nextafter(0.0, 1.0), 1.25, sys.float_info.max):
        for shift in (0.0, -0.0):
            got = numerics.scaled_exp_multiply(base, shift, name="scaled")
            assert got.hex() == base.hex()

    _raises_exact(
        "scaled base must be finite and > 0, got 0.0",
        lambda: numerics.scaled_exp_multiply(0.0, 1.0, name="scaled"),
    )
    _raises_exact(
        "scaled base must be finite and > 0, got nan",
        lambda: numerics.scaled_exp_multiply(math.nan, 1.0, name="scaled"),
    )
    _raises_exact(
        "scaled shift must be finite, got inf",
        lambda: numerics.scaled_exp_multiply(1.0, math.inf, name="scaled"),
    )


def test_scaled_exp_multiply_matches_exact_float_oracle_on_direct_and_recovery_paths() -> None:
    cases = (
        (1.25, 0.3),
        (1.0e-300, 710.0),
        (1.0e-300, 1000.0),
        (1.0e300, -1000.0),
        (1.67e260, -744.86),
    )
    with mpmath.workdps(200):
        for base, shift in cases:
            got = numerics.scaled_exp_multiply(base, shift, name="scaled")
            oracle = float(_mp_float(base) * mpmath.exp(_mp_float(shift)))
            assert _ulp_distance(got, oracle) <= 1

    _raises_exact(
        "scaled is not representable as a positive float64",
        lambda: numerics.scaled_exp_multiply(1.0, 1.0e6, name="scaled"),
    )
    _raises_exact(
        "scaled is not representable as a positive float64",
        lambda: numerics.scaled_exp_multiply(1.0, -1000.0, name="scaled"),
    )
    _raises_exact(
        "scaled is not representable as a positive float64",
        lambda: numerics.scaled_exp_multiply(1.0e308, 100.0, name="scaled"),
    )


def test_scaled_exp_multiply_recovers_correctly_rounded_fallback_edges() -> None:
    cases = (
        (
            float.fromhex("0x1.dc19faf815eb8p+1022"),
            float.fromhex("0x1.881c47ff9c882p-1"),
        ),
        (
            float.fromhex("0x1.25dc3564d5324p-181"),
            float.fromhex("0x1.a18d5dd4066fcp+9"),
        ),
    )
    with mpmath.workdps(200):
        for base, shift in cases:
            oracle = float(_mp_float(base) * mpmath.exp(_mp_float(shift)))
            got = numerics.scaled_exp_multiply(base, shift, name="scaled")
            assert _ulp_distance(got, oracle) <= 1


def test_scaled_exp_multiply_classifies_global_float64_rounding_boundaries() -> None:
    min_subnormal = math.nextafter(0.0, 1.0)
    recovered_min_subnormal = (
        float.fromhex("0x1.fffffffffffffp+1023"),
        -float.fromhex("0x1.6b8e421f3d5d9p+10"),
    )
    rounded_overflow = (
        float.fromhex("0x1.21657beebfcf3p+893"),
        float.fromhex("0x1.6ab7f8f5de4a5p+6"),
    )
    below_half_min_subnormal = (
        float.fromhex("0x1.5a29d699bf0b0p-851"),
        -float.fromhex("0x1.372226c3fc5e6p+7"),
    )
    with mpmath.workdps(200):
        base, shift = recovered_min_subnormal
        oracle = float(_mp_float(base) * mpmath.exp(_mp_float(shift)))
        assert oracle == min_subnormal
        assert numerics.scaled_exp_multiply(base, shift, name="scaled") == oracle

        base, shift = rounded_overflow
        oracle = float(_mp_float(base) * mpmath.exp(_mp_float(shift)))
        assert math.isinf(oracle)
        _raises_exact(
            "scaled is not representable as a positive float64",
            lambda: numerics.scaled_exp_multiply(base, shift, name="scaled"),
        )

        base, shift = below_half_min_subnormal
        exact = _mp_float(base) * mpmath.exp(_mp_float(shift))
        assert exact < _mp_float(min_subnormal) / 2
        _raises_exact(
            "scaled is not representable as a positive float64",
            lambda: numerics.scaled_exp_multiply(base, shift, name="scaled"),
        )


def test_scaled_product_ratio_preserves_interior_and_recovers_endpoint_intermediates() -> None:
    assert numerics.scaled_product_ratio(0.25, 2.0, 4.0, name="ratio") == 0.125
    min_subnormal = math.nextafter(0.0, 1.0)
    assert numerics.scaled_product_ratio(
        min_subnormal,
        1.0,
        min_subnormal,
        name="ratio",
    ) == 1.0

    with mpmath.workdps(200):
        got = numerics.scaled_product_ratio(
            1.0e260,
            1.0,
            sys.float_info.max,
            name="ratio",
        )
        oracle = float(_mp_float(1.0e260) / _mp_float(sys.float_info.max))
        assert _ulp_distance(got, oracle) <= 1

    assert math.copysign(
        1.0,
        numerics.scaled_product_ratio(0.0, -2.0, 1.0, name="ratio"),
    ) < 0.0
    _raises_exact(
        "ratio numerator factors must be finite",
        lambda: numerics.scaled_product_ratio(math.nan, 1.0, 1.0, name="ratio"),
    )
    _raises_exact(
        "ratio numerator factors must be finite",
        lambda: numerics.scaled_product_ratio(1.0, math.inf, 1.0, name="ratio"),
    )
    _raises_exact(
        "ratio denominator must be finite and > 0",
        lambda: numerics.scaled_product_ratio(1.0, 1.0, 0.0, name="ratio"),
    )
    _raises_exact(
        "ratio denominator must be finite and > 0",
        lambda: numerics.scaled_product_ratio(1.0, 1.0, math.inf, name="ratio"),
    )
    _raises_exact(
        "ratio is not representable as a finite float64",
        lambda: numerics.scaled_product_ratio(
            sys.float_info.max,
            sys.float_info.max,
            min_subnormal,
            name="ratio",
        ),
    )
    # A normal ratio intermediate can still make the final multiplication
    # overflow or round to zero; both must route through the checked recovery.
    _raises_exact(
        "ratio is not representable as a finite float64",
        lambda: numerics.scaled_product_ratio(
            sys.float_info.max,
            2.0,
            1.0,
            name="ratio",
        ),
    )
    _raises_exact(
        "ratio is not representable as a finite float64",
        lambda: numerics.scaled_product_ratio(
            min_subnormal,
            0.5,
            1.0,
            name="ratio",
        ),
    )
    _raises_exact(
        "ratio is not representable as a finite float64",
        lambda: numerics.scaled_product_ratio(
            min_subnormal,
            min_subnormal,
            sys.float_info.max,
            name="ratio",
        ),
    )


def test_shifted_probability_classifies_minimum_subnormal_endpoint_shifts() -> None:
    p_min = math.nextafter(0.0, 1.0)
    p_max = math.nextafter(1.0, 0.0)
    tiny_shift = p_min
    message = "p probability is outside the representable float64 open interval"
    _raises_exact(
        message,
        lambda: numerics.shifted_probability_from_odds(p_max, tiny_shift, name="p"),
    )
    _raises_exact(
        message,
        lambda: numerics.shifted_probability_from_odds(p_min, -tiny_shift, name="p"),
    )
    assert numerics.shifted_probability_from_odds(p_max, -tiny_shift, name="p") == p_max
    assert numerics.shifted_probability_from_odds(p_min, tiny_shift, name="p") == p_min


def test_shifted_probability_from_odds_matches_oracle_and_exact_endpoint_neighbours() -> None:
    p_min = math.nextafter(0.0, 1.0)
    p_max = math.nextafter(1.0, 0.0)
    cancelling_shift = float.fromhex("0x1.8696a3c1fe543p+9")
    outside_shift = math.nextafter(cancelling_shift, math.inf)

    assert numerics.shifted_probability_from_odds(p_min, 0.0, name="mapped") == p_min
    assert numerics.shifted_probability_from_odds(p_max, -0.0, name="mapped") == p_max
    assert numerics.shifted_probability_from_odds(
        p_min,
        cancelling_shift,
        name="mapped",
    ) == p_max
    assert numerics.shifted_probability_from_odds(
        p_max,
        -cancelling_shift,
        name="mapped",
    ) == p_min

    with mpmath.workdps(200):
        for probability, shift in ((0.2, 1.0), (0.8, 0.25), (p_min, 744.4400719213812)):
            p_exact = _mp_float(probability)
            shift_exact = _mp_float(shift)
            oracle = float(
                1
                / (
                    1
                    + mpmath.exp(
                        -(mpmath.log(p_exact / (1 - p_exact)) + shift_exact)
                    )
                )
            )
            got = numerics.shifted_probability_from_odds(
                probability,
                shift,
                name="mapped",
            )
            assert _ulp_distance(got, oracle) <= 2

    for probability, shift in (
        (p_min, outside_shift),
        (p_max, -outside_shift),
        (0.5, 1.0e6),
    ):
        _raises_exact(
            "mapped probability is outside the representable float64 open interval",
            lambda probability=probability, shift=shift: numerics.shifted_probability_from_odds(
                probability,
                shift,
                name="mapped",
            ),
        )


def test_shifted_probability_rechecks_a_rounded_endpoint_from_the_adjacent_odds_ulp() -> None:
    probability = float.fromhex("0x1.bddb02c78d406p-816")
    shift = float.fromhex("0x1.2ce5216bb0403p+9")
    assert not numerics._exact_shifted_log_odds_is_in_open_float64_domain(
        probability,
        shift,
    )
    _raises_exact(
        "mapped probability is outside the representable float64 open interval",
        lambda: numerics.shifted_probability_from_odds(
            probability,
            shift,
            name="mapped",
        ),
    )


def test_shifted_probability_from_odds_validates_contract_and_defensive_endpoint(monkeypatch) -> None:
    _raises_exact(
        "mapped base probability must be finite and in (0, 1)",
        lambda: numerics.shifted_probability_from_odds(0.0, 1.0, name="mapped"),
    )
    _raises_exact(
        "mapped base probability must be finite and in (0, 1)",
        lambda: numerics.shifted_probability_from_odds(math.nan, 1.0, name="mapped"),
    )
    _raises_exact(
        "mapped shift must be finite, got inf",
        lambda: numerics.shifted_probability_from_odds(0.5, math.inf, name="mapped"),
    )

    monkeypatch.setattr(
        numerics,
        "scaled_exp_multiply",
        lambda _base, _shift, *, name: sys.float_info.max,
    )
    _raises_exact(
        "mapped probability rounded to a structural endpoint",
        lambda: numerics.shifted_probability_from_odds(0.5, 1.0, name="mapped"),
    )
