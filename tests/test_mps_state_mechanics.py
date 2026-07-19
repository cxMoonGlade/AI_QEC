from __future__ import annotations

"""CPU falsifiers for route-neutral restricted-MPS state mechanics."""

import math

import pytest
import torch

from error_coupling_simulator.carrier.mps.state import (
    commit_mps_candidate_,
    exact_mps_bond_dimension,
    max_mps_bond,
    mps_norm_squared,
)


class _OverlapFixture:
    def __init__(self, value) -> None:
        self.value = value

    @property
    def H(self):
        return self

    def __and__(self, _other):
        return self

    def contract(self, _output_inds):
        return self.value


class _ContractCaptureFixture(_OverlapFixture):
    def __init__(self, value) -> None:
        super().__init__(value)
        self.output_indices: list[object] = []

    def contract(self, output_inds):
        self.output_indices.append(output_inds)
        return self.value


class _BondFixture:
    def __init__(self, sizes: tuple[int, ...]) -> None:
        self.sizes = sizes

    def bond_sizes(self) -> tuple[int, ...]:
        return self.sizes


class _CommitTensorFixture:
    def __init__(
        self,
        value: float,
        *,
        inds: tuple[str, ...] = ("bond",),
        tags: frozenset[str] = frozenset({"SITE"}),
        fail_on_calls: frozenset[int] = frozenset(),
    ) -> None:
        self.data = torch.tensor([value], dtype=torch.complex128)
        self.inds = inds
        self.tags = set(tags)
        self._fail_on_calls = fail_on_calls
        self._modify_calls = 0

    def modify(self, *, data) -> None:
        self._modify_calls += 1
        self.data = data
        if self._modify_calls in self._fail_on_calls:
            raise RuntimeError(f"injected modify failure at call {self._modify_calls}")


class _CommitMpsFixture:
    def __init__(self, tensors: list[_CommitTensorFixture]) -> None:
        self.tensors = tensors
        self.L = len(tensors)

    def __getitem__(self, index: int) -> _CommitTensorFixture:
        return self.tensors[index]


def test_mps_state_norm_is_finite_real_and_does_not_normalize() -> None:
    assert mps_norm_squared(_OverlapFixture(torch.tensor(0.25))) == 0.25

    with pytest.raises(RuntimeError):
        mps_norm_squared(_OverlapFixture(torch.tensor([1.0, 0.0])))
    with pytest.raises(RuntimeError):
        mps_norm_squared(_OverlapFixture(torch.tensor(math.nan)))
    with pytest.raises(RuntimeError):
        mps_norm_squared(_OverlapFixture(torch.tensor(1.0 + 1.0j)))


def test_mps_state_norm_contracts_all_and_pins_realness_boundary() -> None:
    from error_coupling_simulator.numerics import NUMERICAL_ZERO

    fixture = _ContractCaptureFixture(
        torch.tensor(0.5, dtype=torch.float64)
    )
    assert mps_norm_squared(fixture) == 0.5
    assert fixture.output_indices == [all]

    for scale in (0.5, 2.0):
        accepted_imaginary = NUMERICAL_ZERO * max(1.0, abs(scale))
        assert mps_norm_squared(
            _OverlapFixture(
                torch.tensor(
                    complex(scale, accepted_imaginary),
                    dtype=torch.complex128,
                )
            )
        ) == scale
        with pytest.raises(RuntimeError):
            mps_norm_squared(
                _OverlapFixture(
                    torch.tensor(
                        complex(scale, accepted_imaginary * 1.01),
                        dtype=torch.complex128,
                    )
                )
            )


def test_mps_state_max_bond_handles_empty_and_multi_state_inputs() -> None:
    assert max_mps_bond(()) == 1
    assert max_mps_bond((_BondFixture(()),)) == 1
    assert max_mps_bond(
        (_BondFixture((2, 4, 2)), _BondFixture((3,)))
    ) == 4


def test_mps_state_exact_bond_uses_general_open_chain_cut_product() -> None:
    assert exact_mps_bond_dimension(()) == 1
    assert exact_mps_bond_dimension((7,)) == 1
    assert exact_mps_bond_dimension((2, 3, 4)) == 4
    assert exact_mps_bond_dimension((2, 2, 2, 2, 2)) == 4

    for invalid in ((2, 0), (2, -1), (2, True)):
        with pytest.raises((TypeError, ValueError)):
            exact_mps_bond_dimension(invalid)
    with pytest.raises(TypeError):
        exact_mps_bond_dimension((2, 3.0))


def test_mps_state_exact_bond_accepts_unit_sites() -> None:
    assert exact_mps_bond_dimension((2, 1, 3)) == 2


@pytest.mark.parametrize(
    ("local_dims", "expected"),
    [
        ((2, 3, 5, 7), 7),
        ((5, 2, 3, 2), 6),
        ((2, 7, 3), 3),
        ((11, 2), 2),
    ],
)
def test_mps_state_exact_bond_pins_each_asymmetric_cut(
    local_dims: tuple[int, ...],
    expected: int,
) -> None:
    assert exact_mps_bond_dimension(iter(local_dims)) == expected


def test_commit_candidate_rejects_length_index_and_tag_structure_drift() -> None:
    target = _CommitMpsFixture([_CommitTensorFixture(1.0)])

    with pytest.raises(ValueError):
        commit_mps_candidate_(
            target,
            _CommitMpsFixture(
                [_CommitTensorFixture(2.0), _CommitTensorFixture(3.0)]
            ),
        )
    with pytest.raises(RuntimeError):
        commit_mps_candidate_(
            target,
            _CommitMpsFixture([_CommitTensorFixture(2.0, inds=("other",))]),
        )
    with pytest.raises(RuntimeError):
        commit_mps_candidate_(
            target,
            _CommitMpsFixture(
                [_CommitTensorFixture(2.0, tags=frozenset({"OTHER"}))]
            ),
        )

    assert torch.equal(
        target[0].data,
        torch.tensor([1.0], dtype=torch.complex128),
    )
    assert target[0]._modify_calls == 0


def test_commit_candidate_reports_commit_and_rollback_double_failure() -> None:
    target = _CommitMpsFixture(
        [
            _CommitTensorFixture(1.0, fail_on_calls=frozenset({2})),
            _CommitTensorFixture(2.0, fail_on_calls=frozenset({1})),
        ]
    )
    candidate = _CommitMpsFixture(
        [_CommitTensorFixture(10.0), _CommitTensorFixture(20.0)]
    )

    with pytest.raises(RuntimeError) as failure:
        commit_mps_candidate_(target, candidate)

    assert isinstance(failure.value.__cause__, RuntimeError)
    assert [tensor._modify_calls for tensor in target.tensors] == [2, 2]


def test_commit_candidate_reports_every_failed_rollback_site() -> None:
    target = _CommitMpsFixture(
        [
            _CommitTensorFixture(1.0, fail_on_calls=frozenset({2})),
            _CommitTensorFixture(2.0, fail_on_calls=frozenset({1, 2})),
        ]
    )
    candidate = _CommitMpsFixture(
        [_CommitTensorFixture(10.0), _CommitTensorFixture(20.0)]
    )

    with pytest.raises(RuntimeError) as failure:
        commit_mps_candidate_(target, candidate)

    assert isinstance(failure.value.__cause__, RuntimeError)
    assert [tensor._modify_calls for tensor in target.tensors] == [2, 2]


def test_commit_candidate_success_replaces_every_site_once() -> None:
    target = _CommitMpsFixture(
        [_CommitTensorFixture(1.0), _CommitTensorFixture(2.0)]
    )
    candidate = _CommitMpsFixture(
        [_CommitTensorFixture(10.0), _CommitTensorFixture(20.0)]
    )
    candidate_before = [tensor.data.clone() for tensor in candidate.tensors]

    commit_mps_candidate_(target, candidate)

    assert [tensor._modify_calls for tensor in target.tensors] == [1, 1]
    assert [
        complex(tensor.data.item()) for tensor in target.tensors
    ] == [10.0 + 0.0j, 20.0 + 0.0j]
    assert all(
        torch.equal(tensor.data, before)
        for tensor, before in zip(
            candidate.tensors,
            candidate_before,
            strict=True,
        )
    )


def test_commit_candidate_preflights_all_sites_before_first_write() -> None:
    target = _CommitMpsFixture(
        [_CommitTensorFixture(1.0), _CommitTensorFixture(2.0)]
    )
    candidate = _CommitMpsFixture(
        [
            _CommitTensorFixture(10.0),
            _CommitTensorFixture(20.0, inds=("other",)),
        ]
    )

    with pytest.raises(RuntimeError):
        commit_mps_candidate_(target, candidate)

    assert [tensor._modify_calls for tensor in target.tensors] == [0, 0]
    assert [
        complex(tensor.data.item()) for tensor in target.tensors
    ] == [1.0 + 0.0j, 2.0 + 0.0j]


def test_commit_candidate_rolls_back_every_site_after_commit_failure() -> None:
    target = _CommitMpsFixture(
        [
            _CommitTensorFixture(1.0),
            _CommitTensorFixture(2.0, fail_on_calls=frozenset({1})),
        ]
    )
    candidate = _CommitMpsFixture(
        [_CommitTensorFixture(10.0), _CommitTensorFixture(20.0)]
    )

    with pytest.raises(RuntimeError):
        commit_mps_candidate_(target, candidate)

    assert [tensor._modify_calls for tensor in target.tensors] == [2, 2]
    assert [
        complex(tensor.data.item()) for tensor in target.tensors
    ] == [1.0 + 0.0j, 2.0 + 0.0j]
