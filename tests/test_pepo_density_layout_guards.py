"""Host-side PEPO layout, rank, detector-fold, and negativity guards."""

import pytest
import torch

from _support.pepo_density import max_abs_diff, sched
from _support.pepo_density_carrier_cases import (
    TestDetectorFold,
    TestGapRank,
    TestLayout,
    TestNegativityWitness,
    test_numerical_zero_is_the_contract_floor,
)


def test_terminal_probability_validation_preserves_zeros_and_rejects_illegal_mass():
    from error_coupling_simulator.carrier.pepo import sampler

    validate = sampler._validated_conditional_probability
    assert validate(0.0, 1.0, where="zero") == 0.0
    assert validate(1.0, 1.0, where="one") == 1.0
    with pytest.raises(RuntimeError, match="illegal conditional probability"):
        validate(-1.0e-15, 1.0, where="negative")
    with pytest.raises(RuntimeError, match="illegal conditional probability"):
        validate(1.0 + 1.0e-15, 1.0, where="above one")


def test_dense_comparison_rejects_nonfinite_values():
    valid = torch.zeros((1, 1), dtype=torch.complex128)
    invalid = torch.full((1, 1), complex(float("nan"), 0.0), dtype=torch.complex128)
    with pytest.raises(RuntimeError, match="non-finite"):
        max_abs_diff(invalid, valid)


__all__ = (
    "TestDetectorFold",
    "TestGapRank",
    "TestLayout",
    "TestNegativityWitness",
    "test_numerical_zero_is_the_contract_floor",
    "test_terminal_probability_validation_preserves_zeros_and_rejects_illegal_mass",
    "test_dense_comparison_rejects_nonfinite_values",
)
