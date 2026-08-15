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


def test_ntu_pinv_stage_probe_brackets_sync_and_solver(monkeypatch):
    from error_coupling_simulator.carrier.pepo import dynamics

    matrix = torch.tensor(
        [[2.0, 0.0], [0.0, 4.0]],
        dtype=torch.complex128,
    )
    rhs = torch.tensor([2.0, 8.0], dtype=torch.complex128)
    events = []

    def stage_logger(stage, tensor, context):
        events.append(("stage", stage, tensor.clone(), dict(context)))

    def synchronize(tensor):
        events.append(("sync", tensor.clone()))

    real_pinv = torch.linalg.pinv

    def pinv(tensor, *, rtol):
        events.append(("pinv", tensor.clone(), rtol))
        return real_pinv(tensor, rtol=rtol)

    monkeypatch.setattr(dynamics, "_NTU_STAGE_LOGGER", stage_logger)
    monkeypatch.setattr(dynamics, "_synchronize_ntu_stage_device", synchronize)
    monkeypatch.setattr(torch.linalg, "pinv", pinv)

    solution = dynamics._ntu_pinv_solve(
        matrix,
        rhs,
        bond="B1_2",
        sites=(1, 2),
        sweep_index=3,
        solver_side="A",
        re=2,
        D_kept=1,
    )

    assert [event[0] for event in events] == [
        "stage", "sync", "stage", "pinv", "stage",
    ]
    assert events[0][1] == "before_pre_pinv_sync"
    assert torch.equal(events[1][1], matrix)
    assert events[2][1] == "pre_pinv_synced"
    assert torch.equal(events[3][1], matrix)
    assert events[4][1] == "post_pinv"
    assert torch.allclose(solution, torch.tensor([1.0, 2.0], dtype=torch.complex128))
    before_context = events[0][3]
    assert before_context == {
        "bond": "B1_2",
        "sites": (1, 2),
        "sweep_index": 3,
        "solver_side": "A",
        "re": 2,
        "D_kept": 1,
        "rtol": 1e-12,
        "tensor_role": "GA",
    }
    assert events[2][3] == before_context
    assert events[4][3] == {**before_context, "tensor_role": "GA_pinv"}


def test_ntu_pinv_stage_probe_runtime_smoke():
    from error_coupling_simulator.carrier.pepo import dynamics

    matrix = torch.tensor(
        [[2.0, 0.0], [0.0, 4.0]],
        dtype=torch.complex128,
    )
    rhs = torch.tensor([2.0, 8.0], dtype=torch.complex128)
    solution = dynamics._ntu_pinv_solve(
        matrix,
        rhs,
        bond="B1_2",
        sites=(1, 2),
        sweep_index=1,
        solver_side="B",
        re=2,
        D_kept=1,
    )
    assert torch.allclose(solution, torch.tensor([1.0, 2.0], dtype=torch.complex128))


__all__ = (
    "TestDetectorFold",
    "TestGapRank",
    "TestLayout",
    "TestNegativityWitness",
    "test_numerical_zero_is_the_contract_floor",
    "test_terminal_probability_validation_preserves_zeros_and_rejects_illegal_mass",
    "test_dense_comparison_rejects_nonfinite_values",
)
