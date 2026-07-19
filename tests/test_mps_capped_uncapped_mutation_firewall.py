"""CPU-only mutation firewall for restricted capped/uncapped MPS mechanics.

These tests pin semantic boundaries and dependency-call contracts.  They avoid
human-facing exception prose: failures are selected only by exception type and
observable state/call behavior.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
import torch


def _numpy_zero_mps(n_sites: int = 3):
    import quimb.tensor as qtn

    return qtn.MPS_computational_state("0" * int(n_sites)).astype(np.complex128)


def _torch_zero_mps(n_sites: int = 2):
    import quimb.tensor as qtn

    zero = torch.tensor([1.0, 0.0], dtype=torch.complex128)
    return qtn.MPS_product_state([zero.clone() for _ in range(int(n_sites))])


class _SiteTensor:
    def __init__(self, data: Any) -> None:
        self.data = data


class _ValidationMps:
    def __init__(
        self,
        arrays: list[Any],
        *,
        physical_dims: list[int] | None = None,
        cyclic: bool = False,
    ) -> None:
        self.tensors = [_SiteTensor(array) for array in arrays]
        self.L = len(arrays)
        self.cyclic = cyclic
        self._physical_dims = physical_dims or [2] * len(arrays)

    def __getitem__(self, index: int) -> _SiteTensor:
        return self.tensors[index]

    def site_ind(self, index: int) -> str:
        return f"k{index}"

    def ind_size(self, index: str) -> int:
        return self._physical_dims[int(index[1:])]


class _SplitProduct:
    def __init__(self, *, shared_bonds: tuple[str, ...], kept_bond: int) -> None:
        self._shared_bonds = shared_bonds
        self._kept_bond = kept_bond

    def bonds(self, _other: Any) -> tuple[str, ...]:
        return self._shared_bonds

    def ind_size(self, _bond: str) -> int:
        return self._kept_bond


class _JoinedSplitSpy:
    def __init__(
        self,
        *,
        data: Any,
        error: Any = 0.5,
        emit_error: bool = True,
        result: Any = None,
        shared_bonds: tuple[str, ...] = ("new_bond",),
        kept_bond: int = 2,
    ) -> None:
        self.data = data
        self.error = error
        self.emit_error = emit_error
        self.calls: list[dict[str, Any]] = []
        if result is None:
            result = (
                _SplitProduct(shared_bonds=shared_bonds, kept_bond=kept_bond),
                _SplitProduct(shared_bonds=shared_bonds, kept_bond=kept_bond),
            )
        self.result = result

    def split(self, **kwargs: Any) -> Any:
        self.calls.append(dict(kwargs))
        if self.emit_error:
            kwargs["info"]["error"] = self.error
        return self.result


class _SwapTensor:
    def __init__(self, name: str, *, joined: Any = None) -> None:
        self.name = name
        self.data = f"{name}_data"
        self.joined = joined
        self.reindex_calls: list[dict[str, str]] = []
        self.transpose_calls: list[Any] = []
        self.modified: list[Any] = []

    def bonds(self, _other: Any) -> tuple[str, ...]:
        return ("old_bond",)

    def filter_bonds(self, _other: Any) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return ("old_bond",), ("left_aux", "k0")

    def __matmul__(self, _other: Any) -> Any:
        return self.joined

    def reindex_(self, mapping: dict[str, str]) -> _SwapTensor:
        self.reindex_calls.append(dict(mapping))
        return self

    def transpose_like_(self, tensor: Any) -> _SwapTensor:
        self.transpose_calls.append(tensor)
        return self

    def modify(self, *, data: Any) -> None:
        self.modified.append(data)
        self.data = data


class _SwapCandidate:
    def __init__(self) -> None:
        self.joined = object()
        self.tensors = [
            _SwapTensor("site0", joined=self.joined),
            _SwapTensor("site1", joined=self.joined),
        ]
        self.canonicalize_calls: list[tuple[tuple[int, int], dict[str, Any]]] = []

    def __getitem__(self, index: int) -> _SwapTensor:
        return self.tensors[index]

    def site_ind(self, index: int) -> str:
        return f"k{index}"

    def canonicalize_(
        self,
        sites: tuple[int, int],
        *,
        info: dict[str, Any],
    ) -> None:
        self.canonicalize_calls.append((sites, info))


def test_uncapped_resource_preflight_pins_inclusive_caps_and_exact_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.carrier.mps.uncapped_nonlocal as mechanics

    at_cap = mechanics.preflight_uncapped_nonlocal_resource(
        support=(0, 1, 2, 3, 4),
        local_dims=(2, 2, 2, 2, 16),
    )
    assert at_cap == {
        "support": [0, 1, 2, 3, 4],
        "support_local_dims": [2, 2, 2, 2, 16],
        "support_site_count": 5,
        "support_hilbert_dimension": 256,
        "dense_operator_elements": 65_536,
        "max_support_sites": 5,
        "max_support_hilbert_dimension": 256,
        "max_dense_operator_elements": 65_536,
        "resource_gate_role": "numerical_only_preallocation_cap_not_accuracy_gate",
    }

    invalid_calls = (
        ({"support": (0, 1), "local_dims": (2, 2)}, ValueError),
        (
            {
                "support": (0, 1, 2, 3, 4, 5),
                "local_dims": (2, 2, 2, 2, 2, 2),
            },
            ValueError,
        ),
        ({"support": (-1, 0, 1), "local_dims": (2, 2, 2)}, ValueError),
        ({"support": (0, 2, 1), "local_dims": (2, 2, 2)}, ValueError),
        ({"support": (0, 1, 1), "local_dims": (2, 2, 2)}, ValueError),
        ({"support": (0, 1, 2), "local_dims": ()}, ValueError),
        ({"support": (0, 1, 2), "local_dims": (2, 1, 2)}, ValueError),
        ({"support": (0, 1, 3), "local_dims": (2, 2, 2)}, ValueError),
        ({"support": "012", "local_dims": (2, 2, 2)}, TypeError),
        ({"support": (0, 1, 2), "local_dims": (2, 2, 2.0)}, TypeError),
    )
    for kwargs, error_type in invalid_calls:
        with pytest.raises(error_type):
            mechanics.preflight_uncapped_nonlocal_resource(**kwargs)

    with pytest.raises(ValueError):
        mechanics.preflight_uncapped_nonlocal_resource(
            support=(0, 1, 2, 3, 4),
            local_dims=(2, 2, 2, 2, 17),
        )

    monkeypatch.setattr(mechanics, "MAX_SUPPORT_HILBERT_DIMENSION", 2_000)
    with pytest.raises(ValueError):
        mechanics.preflight_uncapped_nonlocal_resource(
            support=(0, 1, 2),
            local_dims=(257, 2, 2),
        )


def test_uncapped_resource_preflight_rejects_bytes_as_support() -> None:
    from error_coupling_simulator.carrier.mps.uncapped_nonlocal import (
        preflight_uncapped_nonlocal_resource,
    )

    with pytest.raises(TypeError):
        preflight_uncapped_nonlocal_resource(
            support=b"\x00\x01\x02",  # type: ignore[arg-type]
            local_dims=(2, 2, 2),
        )


@pytest.mark.parametrize(
    "value",
    [
        np.asarray([1.0, 2.0]),
        torch.tensor([1.0, 2.0], dtype=torch.complex128),
        np.asarray(np.nan),
        np.asarray(np.inf),
        np.asarray(1.0 + 2.0e-12j),
    ],
    ids=("numpy-nonscalar", "torch-nonscalar", "nan", "inf", "imaginary"),
)
def test_uncapped_finite_real_scalar_rejects_non_real_scalar_contract(
    value: Any,
) -> None:
    from error_coupling_simulator.carrier.mps.uncapped_nonlocal import (
        _finite_real_scalar,
    )

    with pytest.raises(RuntimeError):
        _finite_real_scalar(value, name="observed")


def test_uncapped_finite_real_scalar_accepts_inclusive_imaginary_tolerance() -> None:
    from error_coupling_simulator.carrier.mps.uncapped_nonlocal import (
        _finite_real_scalar,
    )

    assert _finite_real_scalar(
        np.asarray(2.0 + 2.0e-12j),
        name="numpy boundary",
    ) == pytest.approx(2.0)
    assert _finite_real_scalar(
        torch.tensor(1.0 + 1.0e-12j, dtype=torch.complex128),
        name="torch boundary",
    ) == pytest.approx(1.0)


def test_uncapped_source_validation_rejects_backend_and_tensor_corruption() -> None:
    from error_coupling_simulator.carrier.mps.uncapped_nonlocal import (
        _validate_source_mps,
    )

    numpy_array = np.ones((1, 2), dtype=np.complex128)
    torch_array = torch.ones((1, 2), dtype=torch.complex128)
    numpy_mps = _ValidationMps([numpy_array.copy() for _ in range(3)])
    torch_mps = _ValidationMps([torch_array.clone() for _ in range(3)])
    assert _validate_source_mps(numpy_mps, local_dims=(2, 2, 2)) == (
        "numpy",
        None,
    )
    backend, device = _validate_source_mps(torch_mps, local_dims=(2, 2, 2))
    assert backend == "torch"
    assert device == torch.device("cpu")

    corruptions = (
        (_ValidationMps([numpy_array] * 3, cyclic=True), (2, 2, 2), ValueError),
        (_ValidationMps([numpy_array] * 3), (2, 2), ValueError),
        (_ValidationMps([]), (), ValueError),
        (
            _ValidationMps([numpy_array, torch_array, numpy_array]),
            (2, 2, 2),
            TypeError,
        ),
        (
            _ValidationMps(
                [numpy_array.astype(np.complex64), numpy_array, numpy_array]
            ),
            (2, 2, 2),
            TypeError,
        ),
        (
            _ValidationMps(
                [
                    numpy_array,
                    np.asarray([[np.nan, 0.0]], dtype=np.complex128),
                    numpy_array,
                ]
            ),
            (2, 2, 2),
            ValueError,
        ),
        (
            _ValidationMps([numpy_array] * 3, physical_dims=[2, 3, 2]),
            (2, 2, 2),
            ValueError,
        ),
    )
    for mps, dims, error_type in corruptions:
        with pytest.raises(error_type):
            _validate_source_mps(mps, local_dims=dims)


def test_uncapped_source_validation_accepts_one_torch_site() -> None:
    from error_coupling_simulator.carrier.mps.uncapped_nonlocal import (
        _validate_source_mps,
    )

    tensor = torch.ones((1, 2), dtype=torch.complex128)
    assert _validate_source_mps(
        _ValidationMps([tensor]),
        local_dims=(2,),
    ) == ("torch", torch.device("cpu"))


def test_uncapped_gate_validation_pins_dtype_shape_finiteness_and_unitarity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.carrier.mps.uncapped_nonlocal as mechanics

    identity = np.eye(8, dtype=np.complex128)
    assert mechanics._validate_gate(
        identity,
        backend="numpy",
        device=None,
        dimension=8,
    ) is identity
    torch_identity = torch.eye(8, dtype=torch.complex128)
    torch_eye = mechanics.torch.eye
    identity_devices: list[Any] = []

    def torch_eye_spy(*args: Any, **kwargs: Any) -> torch.Tensor:
        identity_devices.append(kwargs.get("device", "missing"))
        return torch_eye(*args, **kwargs)

    monkeypatch.setattr(mechanics.torch, "eye", torch_eye_spy)
    assert mechanics._validate_gate(
        torch_identity,
        backend="torch",
        device=torch.device("cpu"),
        dimension=8,
    ) is torch_identity
    assert identity_devices == [torch.device("cpu")]

    invalid = (
        (np.eye(8, dtype=np.complex64), "numpy", None, 8),
        (np.eye(4, dtype=np.complex128), "numpy", None, 8),
        (
            np.full((8, 8), np.complex128(np.nan), dtype=np.complex128),
            "numpy",
            None,
            8,
        ),
        (0.5 * identity, "numpy", None, 8),
        (torch_identity.to(device="meta"), "torch", torch.device("cpu"), 8),
    )
    for gate, backend, device, dimension in invalid:
        with pytest.raises(ValueError):
            mechanics._validate_gate(
                gate,
                backend=backend,
                device=device,
                dimension=dimension,
            )

    monkeypatch.setattr(mechanics.np.linalg, "norm", lambda _value: 1.0e-12)
    mechanics._validate_gate(identity, backend="numpy", device=None, dimension=8)
    monkeypatch.setattr(
        mechanics.np.linalg,
        "norm",
        lambda _value: np.nextafter(1.0e-12, np.inf),
    )
    with pytest.raises(ValueError):
        mechanics._validate_gate(identity, backend="numpy", device=None, dimension=8)


def test_uncapped_candidate_validation_rejects_backend_or_finite_drift() -> None:
    from error_coupling_simulator.carrier.mps.uncapped_nonlocal import (
        _validate_candidate_finite,
    )

    finite_numpy = np.ones((1, 2), dtype=np.complex128)
    finite_torch = torch.ones((1, 2), dtype=torch.complex128)
    _validate_candidate_finite(
        _ValidationMps([finite_numpy, finite_numpy]),
        backend="numpy",
    )
    _validate_candidate_finite(
        _ValidationMps([finite_torch, finite_torch]),
        backend="torch",
    )

    for candidate, backend in (
        (_ValidationMps([finite_numpy, finite_torch]), "numpy"),
        (_ValidationMps([finite_torch, finite_numpy]), "torch"),
        (
            _ValidationMps(
                [finite_numpy, np.asarray([[np.inf, 0.0]], dtype=np.complex128)]
            ),
            "numpy",
        ),
        (
            _ValidationMps(
                [
                    finite_torch,
                    torch.tensor([[complex(float("nan"), 0.0), 0.0j]]),
                ]
            ),
            "torch",
        ),
    ):
        with pytest.raises(RuntimeError):
            _validate_candidate_finite(candidate, backend=backend)


def test_quimb_version_contract_is_an_exact_equality(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.carrier.mps.capped_two_site as capped
    import error_coupling_simulator.carrier.mps.uncapped_nonlocal as uncapped

    monkeypatch.setattr(
        uncapped.importlib.metadata,
        "version",
        lambda package: "1.14.0" if package == "quimb" else "unexpected",
    )
    assert uncapped._assert_quimb_contract() == "1.14.0"
    assert capped._assert_quimb_contract() == "1.14.0"

    monkeypatch.setattr(
        uncapped.importlib.metadata,
        "version",
        lambda _package: "1.14.0.post1",
    )
    with pytest.raises(RuntimeError):
        uncapped._assert_quimb_contract()
    with pytest.raises(RuntimeError):
        capped._assert_quimb_contract()


def test_capped_split_names_every_quimb_control_and_reports_exact_local_mass() -> None:
    from error_coupling_simulator.carrier.mps.capped_two_site import (
        _split_with_event,
    )

    joined = _JoinedSplitSpy(
        data=torch.tensor([1.0, 1.0], dtype=torch.complex128),
    )
    _left, _right, event = _split_with_event(
        joined,
        left_inds=("left", "physical"),
        right_inds=("right",),
        bond_ind="old_bond",
        absorb="right",
        path_role="two_site_operator_split",
        split_sites=(1, 2),
        gate_leg_sites=(2, 1),
        max_bond=3,
        sequence_index=4,
    )

    assert len(joined.calls) == 1
    call = joined.calls[0]
    assert call["info"] == {"error": 0.5}
    assert {key: value for key, value in call.items() if key != "info"} == {
        "cutoff": 0.0,
        "left_inds": ["left", "physical"],
        "right_inds": ["right"],
        "bond_ind": "old_bond",
        "absorb": "right",
        "get": "tensors",
        "method": "svd",
        "max_bond": 3,
        "cutoff_mode": "rsum2",
        "renorm": None,
    }
    assert event == {
        "sequence_index": 4,
        "path_role": "two_site_operator_split",
        "split_sites": [1, 2],
        "gate_leg_sites": [2, 1],
        "requested_method": "svd",
        "requested_absorb": "right",
        "requested_max_bond": 3,
        "requested_cutoff": 0.0,
        "requested_cutoff_mode": "rsum2",
        "requested_renorm": None,
        "pre_split_total_weight": pytest.approx(2.0),
        "actual_kept_bond_dimension": 2,
        "actual_discarded_weight_raw": pytest.approx(0.25),
        "actual_discarded_weight_fraction_of_pre_split": pytest.approx(0.125),
        "not_a_global_error_bound": True,
    }

    without_optional_indices = _JoinedSplitSpy(
        data=torch.tensor([1.0], dtype=torch.complex128),
        error=0.0,
        kept_bond=1,
    )
    _split_with_event(
        without_optional_indices,
        left_inds=["left"],
        right_inds=None,
        bond_ind=None,
        absorb="left",
        path_role="forward_swap_split",
        split_sites=(0, 1),
        gate_leg_sites=None,
        max_bond=1,
        sequence_index=0,
    )
    assert "right_inds" not in without_optional_indices.calls[0]
    assert "bond_ind" not in without_optional_indices.calls[0]


@pytest.mark.parametrize(
    ("joined", "max_bond"),
    [
        pytest.param(
            _JoinedSplitSpy(
                data=torch.zeros(1, dtype=torch.complex128)
            ),
            2,
            id="zero-preweight",
        ),
        pytest.param(
            _JoinedSplitSpy(
                data=torch.ones(1, dtype=torch.complex128),
                result=[],
            ),
            2,
            id="non-tuple-return",
        ),
        pytest.param(
            _JoinedSplitSpy(
                data=torch.ones(1, dtype=torch.complex128),
                error=0.0,
                result=[
                    _SplitProduct(shared_bonds=("new_bond",), kept_bond=1),
                    _SplitProduct(shared_bonds=("new_bond",), kept_bond=1),
                ],
            ),
            2,
            id="two-item-list-return",
        ),
        pytest.param(
            _JoinedSplitSpy(
                data=torch.ones(1, dtype=torch.complex128),
                emit_error=False,
            ),
            2,
            id="missing-error",
        ),
        pytest.param(
            _JoinedSplitSpy(
                data=torch.ones(1, dtype=torch.complex128),
                error=float("nan"),
            ),
            2,
            id="nonfinite-error",
        ),
        pytest.param(
            _JoinedSplitSpy(
                data=torch.ones(1, dtype=torch.complex128),
                error=-0.5,
            ),
            2,
            id="negative-error",
        ),
        pytest.param(
            _JoinedSplitSpy(
                data=torch.ones(1, dtype=torch.complex128),
                error=2.0,
            ),
            2,
            id="discarded-over-preweight",
        ),
        pytest.param(
            _JoinedSplitSpy(
                data=torch.ones(1, dtype=torch.complex128),
                shared_bonds=(),
            ),
            2,
            id="missing-shared-bond",
        ),
        pytest.param(
            _JoinedSplitSpy(
                data=torch.ones(1, dtype=torch.complex128),
                shared_bonds=("a", "b"),
            ),
            2,
            id="two-shared-bonds",
        ),
        pytest.param(
            _JoinedSplitSpy(
                data=torch.ones(1, dtype=torch.complex128),
                kept_bond=0,
            ),
            2,
            id="zero-kept-bond",
        ),
        pytest.param(
            _JoinedSplitSpy(
                data=torch.ones(1, dtype=torch.complex128),
                kept_bond=3,
            ),
            2,
            id="kept-bond-over-cap",
        ),
    ],
)
def test_capped_split_rejects_corrupt_dependency_evidence(
    joined: _JoinedSplitSpy,
    max_bond: int,
) -> None:
    from error_coupling_simulator.carrier.mps.capped_two_site import (
        _split_with_event,
    )

    with pytest.raises(RuntimeError):
        _split_with_event(
            joined,
            left_inds=["left"],
            right_inds=None,
            bond_ind=None,
            absorb="left",
            path_role="forward_swap_split",
            split_sites=(0, 1),
            gate_leg_sites=None,
            max_bond=max_bond,
            sequence_index=0,
        )


def test_capped_adjacent_swap_preserves_exact_split_order_and_index_rewrite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    candidate = _SwapCandidate()
    split_left = _SwapTensor("split_left")
    split_right = _SwapTensor("split_right")
    split_calls: list[tuple[Any, dict[str, Any]]] = []
    expected_event = {"sequence_index": 7, "path_role": "forward_swap_split"}

    def split_spy(joined: Any, **kwargs: Any):
        split_calls.append((joined, dict(kwargs)))
        return split_left, split_right, expected_event

    monkeypatch.setattr(mechanics, "_split_with_event", split_spy)
    orthogonality_info: dict[str, Any] = {"cur_orthog": "calc"}
    event = mechanics._swap_adjacent(
        candidate,
        1,
        0,
        absorb="left",
        path_role="forward_swap_split",
        orthogonality_info=orthogonality_info,
        max_bond=3,
        sequence_index=7,
    )

    assert event is expected_event
    assert candidate.canonicalize_calls == [((0, 1), orthogonality_info)]
    assert split_calls == [
        (
            candidate.joined,
            {
                "left_inds": ["left_aux", "k1"],
                "right_inds": None,
                "bond_ind": None,
                "absorb": "left",
                "path_role": "forward_swap_split",
                "split_sites": (0, 1),
                "gate_leg_sites": None,
                "max_bond": 3,
                "sequence_index": 7,
            },
        )
    ]
    assert split_left.reindex_calls == [{"k1": "k0"}]
    assert split_right.reindex_calls == [{"k0": "k1"}]
    assert split_left.transpose_calls == [candidate.tensors[0]]
    assert split_right.transpose_calls == [candidate.tensors[1]]
    assert candidate.tensors[0].modified == ["split_left_data"]
    assert candidate.tensors[1].modified == ["split_right_data"]
    assert orthogonality_info["cur_orthog"] == (0, 0)

    with pytest.raises(ValueError):
        mechanics._swap_adjacent(
            candidate,
            0,
            2,
            absorb="right",
            path_role="reverse_swap_split",
            orthogonality_info=orthogonality_info,
            max_bond=3,
            sequence_index=8,
        )


def test_capped_scalar_frobenius_and_preflight_contract_boundaries() -> None:
    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    assert mechanics._finite_real_scalar(
        torch.tensor(2.0 + 2.0e-12j, dtype=torch.complex128),
        name="inclusive boundary",
    ) == pytest.approx(2.0)
    assert mechanics._frobenius_weight(
        torch.tensor([1.0 + 2.0j, 3.0], dtype=torch.complex128)
    ) == pytest.approx(14.0)
    for value in (
        torch.tensor([1.0, 2.0], dtype=torch.complex128),
        torch.tensor(float("nan")),
        torch.tensor(float("inf")),
        torch.tensor(1.0 + 2.0e-12j, dtype=torch.complex128),
    ):
        with pytest.raises(RuntimeError):
            mechanics._finite_real_scalar(value, name="invalid")

    gate = torch.eye(4, dtype=torch.complex128)
    valid = _ValidationMps(
        [
            torch.ones((1, 2), dtype=torch.complex128),
            torch.ones((1, 2), dtype=torch.complex128),
        ]
    )
    validated_gate, device = mechanics._preflight(
        valid,
        gate,
        support=(0, 1),
        max_bond=1,
    )
    assert validated_gate is gate
    assert device == torch.device("cpu")

    invalid_calls = (
        (
            _ValidationMps(
                [
                    torch.ones((1, 2), dtype=torch.complex128),
                    torch.ones((1, 2), dtype=torch.complex128),
                ],
                cyclic=True,
            ),
            gate,
            (0, 1),
            1,
        ),
        (valid, gate, (0, 1), 0),
        (valid, gate, (0, 0), 1),
        (valid, gate, (0, 2), 1),
        (valid, gate, (2, 0), 1),
        (
            _ValidationMps(
                [
                    np.ones((1, 2), dtype=np.complex128),
                    np.ones((1, 2), dtype=np.complex128),
                ]
            ),
            gate,
            (0, 1),
            1,
        ),
        (
            _ValidationMps(
                [
                    torch.ones((1, 2), dtype=torch.complex64),
                    torch.ones((1, 2), dtype=torch.complex128),
                ]
            ),
            gate,
            (0, 1),
            1,
        ),
        (
            _ValidationMps(
                [
                    torch.ones((1, 2), dtype=torch.complex128),
                    torch.ones((1, 2), dtype=torch.complex128, device="meta"),
                ]
            ),
            gate,
            (0, 1),
            1,
        ),
        (
            _ValidationMps(
                [
                    torch.ones((1, 2), dtype=torch.complex128),
                    torch.ones((1, 2), dtype=torch.complex128),
                ],
                physical_dims=[2, 3],
            ),
            gate,
            (0, 1),
            1,
        ),
        (valid, torch.eye(4, dtype=torch.complex64), (0, 1), 1),
        (
            valid,
            torch.eye(4, dtype=torch.complex128, device="meta"),
            (0, 1),
            1,
        ),
        (valid, torch.eye(3, dtype=torch.complex128), (0, 1), 1),
        (
            valid,
            torch.full((4, 4), complex(float("nan"), 0.0), dtype=torch.complex128),
            (0, 1),
            1,
        ),
        (valid, 0.5 * gate, (0, 1), 1),
    )
    for mps, invalid_gate, support, max_bond in invalid_calls:
        with pytest.raises((TypeError, ValueError)):
            mechanics._preflight(
                mps,
                invalid_gate,
                support=support,
                max_bond=max_bond,
            )


def test_capped_public_event_overrides_forged_context_with_measured_values() -> None:
    from error_coupling_simulator.carrier.mps.capped_two_site import (
        apply_capped_two_site_unitary,
    )

    source = _torch_zero_mps()
    source_dense = source.to_dense().detach().cpu().numpy().copy()
    candidate, event = apply_capped_two_site_unitary(
        source,
        torch.eye(4, dtype=torch.complex128),
        support=(0, 1),
        max_bond=2,
        context={
            "fixture_id": "adjacent_identity",
            "support": [99, 98],
            "max_bond": 99,
            "not_a_global_error_bound": False,
        },
    )

    np.testing.assert_array_equal(
        source.to_dense().detach().cpu().numpy(),
        source_dense,
    )
    np.testing.assert_allclose(
        candidate.to_dense().detach().cpu().numpy(),
        source_dense,
        rtol=0.0,
        atol=1.0e-14,
    )
    assert event["fixture_id"] == "adjacent_identity"
    assert event["support"] == [0, 1]
    assert event["gate_leg_sites"] == [0, 1]
    assert event["max_bond"] == 2
    assert event["quimb_version"] == "1.14.0"
    assert event["input_norm_sq"] == pytest.approx(1.0)
    assert event["raw_output_norm_sq"] == pytest.approx(1.0)
    assert event["restored_output_norm_sq"] == pytest.approx(1.0)
    assert event["deterministic_norm_restore_factor"] == pytest.approx(1.0)
    assert event["unitary_truncation_mass_loss"] == pytest.approx(0.0)
    assert event["physical_branch_probability"] is None
    assert event["split_count"] == 1
    assert event["actual_discarded_weight_raw_sum"] == pytest.approx(0.0)
    assert event["actual_discarded_weight_fraction_sum"] == pytest.approx(0.0)
    assert event["worst_actual_discarded_weight_fraction"] == pytest.approx(0.0)
    assert event["ledger_semantics"] == (
        "per_actual_svd_split_heuristic_not_global_bound"
    )
    assert event["not_a_global_error_bound"] is True


def test_uncapped_nonlocal_names_every_quimb_compression_control(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both decomposition layers must receive an explicit lossless policy."""
    import quimb.tensor as qtn

    from error_coupling_simulator.carrier.mps.uncapped_nonlocal import (
        apply_uncapped_nonlocal_unitary,
    )

    from_dense_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    apply_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
    original_from_dense = qtn.MatrixProductOperator.from_dense
    original_apply = qtn.MatrixProductState.gate_with_submpo_

    def spy_from_dense(_cls, *args: Any, **kwargs: Any):
        from_dense_calls.append((args, dict(kwargs)))
        return original_from_dense(*args, **kwargs)

    def spy_apply(self, *args: Any, **kwargs: Any):
        apply_calls.append((args, dict(kwargs)))
        return original_apply(self, *args, **kwargs)

    monkeypatch.setattr(
        qtn.MatrixProductOperator,
        "from_dense",
        classmethod(spy_from_dense),
    )
    monkeypatch.setattr(qtn.MatrixProductState, "gate_with_submpo_", spy_apply)

    source = _numpy_zero_mps()
    candidate, _event = apply_uncapped_nonlocal_unitary(
        source,
        np.eye(8, dtype=np.complex128),
        support=(0, 1, 2),
        local_dims=(2, 2, 2),
    )

    assert candidate is not source
    assert len(from_dense_calls) == 1
    assert len(from_dense_calls[0][0]) == 1
    assert from_dense_calls[0][1] == {
        "dims": (2, 2, 2),
        "sites": (0, 1, 2),
        "L": 3,
        "method": "svd",
        "max_bond": None,
        "cutoff": 0.0,
        "cutoff_mode": "rsum2",
        "renorm": None,
    }
    assert len(apply_calls) == 1
    assert len(apply_calls[0][0]) == 1
    assert apply_calls[0][1] == {
        "where": (0, 1, 2),
        "method": "direct",
        "max_bond": None,
        "cutoff": 0.0,
        "cutoff_mode": "rsum2",
        "normalize": False,
    }


def test_uncapped_validation_accepts_open_mps_without_optional_cyclic_marker() -> None:
    from error_coupling_simulator.carrier.mps.uncapped_nonlocal import (
        _validate_source_mps,
    )

    array = np.ones((1, 2), dtype=np.complex128)
    mps = _ValidationMps([array.copy() for _ in range(3)])
    del mps.cyclic
    assert _validate_source_mps(mps, local_dims=(2, 2, 2)) == (
        "numpy",
        None,
    )


@pytest.mark.parametrize(
    "observed_norms",
    [
        pytest.param((1.0e6, 1.0e6 + 5.0e-7), id="relative-tolerance"),
        pytest.param((1.0e-13, 2.0e-13), id="absolute-tolerance"),
    ],
)
def test_uncapped_public_norm_gate_uses_both_explicit_tolerance_axes(
    monkeypatch: pytest.MonkeyPatch,
    observed_norms: tuple[float, float],
) -> None:
    import error_coupling_simulator.carrier.mps.uncapped_nonlocal as mechanics

    norms = iter(observed_norms)
    monkeypatch.setattr(mechanics, "mps_norm_squared", lambda _mps: next(norms))
    _candidate, event = mechanics.apply_uncapped_nonlocal_unitary(
        _numpy_zero_mps(),
        np.eye(8, dtype=np.complex128),
        support=(0, 1, 2),
        local_dims=(2, 2, 2),
        context={"fixture_id": "dual_tolerance"},
    )
    assert event["input_norm_sq"] == observed_norms[0]
    assert event["output_norm_sq"] == observed_norms[1]


def test_uncapped_public_norm_gate_rejects_math_default_relative_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.carrier.mps.uncapped_nonlocal as mechanics

    input_norm = 1.0e6
    output_norm = input_norm + 5.0e-4
    assert output_norm - input_norm > mechanics.NUMERICAL_ZERO * input_norm
    norms = iter((input_norm, output_norm))
    monkeypatch.setattr(mechanics, "mps_norm_squared", lambda _mps: next(norms))

    with pytest.raises(RuntimeError):
        mechanics.apply_uncapped_nonlocal_unitary(
            _numpy_zero_mps(),
            np.eye(8, dtype=np.complex128),
            support=(0, 1, 2),
            local_dims=(2, 2, 2),
        )


def test_uncapped_returned_candidate_owns_independent_tensor_storage() -> None:
    from error_coupling_simulator.carrier.mps.uncapped_nonlocal import (
        apply_uncapped_nonlocal_unitary,
    )

    source = _numpy_zero_mps(n_sites=5)
    before = [
        np.asarray(source[site].data).copy()
        for site in range(source.L)
    ]
    candidate, _event = apply_uncapped_nonlocal_unitary(
        source,
        np.eye(8, dtype=np.complex128),
        support=(0, 1, 2),
        local_dims=(2, 2, 2, 2, 2),
    )

    for site in range(source.L):
        assert not np.shares_memory(
            np.asarray(candidate[site].data),
            np.asarray(source[site].data),
        )
        np.testing.assert_array_equal(np.asarray(source[site].data), before[site])


def test_uncapped_candidate_write_then_quimb_failure_leaves_source_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import quimb.tensor as qtn

    from error_coupling_simulator.carrier.mps.uncapped_nonlocal import (
        apply_uncapped_nonlocal_unitary,
    )

    source = _numpy_zero_mps(n_sites=5)
    before = [
        np.asarray(source[site].data).copy()
        for site in range(source.L)
    ]
    candidate_writes: list[int] = []

    def corrupt_candidate_then_fail(candidate: Any, *_args: Any, **_kwargs: Any) -> None:
        candidate_writes.append(1)
        np.asarray(candidate[0].data)[...] = np.complex128(7.0)
        raise OSError("injected Quimb failure after candidate write")

    monkeypatch.setattr(
        qtn.MatrixProductState,
        "gate_with_submpo_",
        corrupt_candidate_then_fail,
    )
    with pytest.raises(RuntimeError):
        apply_uncapped_nonlocal_unitary(
            source,
            np.eye(8, dtype=np.complex128),
            support=(0, 1, 2),
            local_dims=(2, 2, 2, 2, 2),
        )

    assert candidate_writes == [1]
    for site in range(source.L):
        np.testing.assert_array_equal(np.asarray(source[site].data), before[site])


def test_capped_validation_accepts_open_mps_without_optional_cyclic_marker() -> None:
    from error_coupling_simulator.carrier.mps.capped_two_site import _preflight

    mps = _ValidationMps(
        [
            torch.ones((1, 2), dtype=torch.complex128),
            torch.ones((1, 2), dtype=torch.complex128),
        ]
    )
    del mps.cyclic
    gate = torch.eye(4, dtype=torch.complex128)
    validated, device = _preflight(mps, gate, support=(0, 1), max_bond=1)
    assert validated is gate
    assert device == torch.device("cpu")


def test_capped_preflight_accepts_inclusive_unitarity_residual_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    tensor = torch.ones((1, 2), dtype=torch.complex128)
    mps = _ValidationMps([tensor, tensor.clone()])
    gate = torch.eye(4, dtype=torch.complex128)
    monkeypatch.setattr(
        mechanics,
        "_finite_real_scalar",
        lambda _value, *, name: mechanics.NUMERICAL_ZERO,
    )
    validated, _device = mechanics._preflight(
        mps,
        gate,
        support=(0, 1),
        max_bond=1,
    )
    assert validated is gate


@pytest.mark.parametrize(
    ("preweight", "discarded", "should_raise"),
    [
        pytest.param(1.0, 1.0, False, id="inside-lower-tolerance"),
        pytest.param(
            1.0,
            1.0 + 100.0e-12,
            False,
            id="inclusive-upper-tolerance",
        ),
        pytest.param(1.0, 1.0 + 100.5e-12, True, id="between-100-and-101"),
        pytest.param(0.25, 0.25 + 1.5e-10, True, id="scale-floor-one"),
        pytest.param(4.0, 4.0 + 1.0e-10, False, id="scale-multiplies"),
    ],
)
def test_capped_actual_split_uses_the_closed_scaled_weight_boundary(
    monkeypatch: pytest.MonkeyPatch,
    preweight: float,
    discarded: float,
    should_raise: bool,
) -> None:
    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    monkeypatch.setattr(mechanics, "_frobenius_weight", lambda _data: preweight)
    joined = _JoinedSplitSpy(
        data=torch.ones(1, dtype=torch.complex128),
        error=torch.tensor(discarded**0.5, dtype=torch.float64),
        kept_bond=1,
    )

    def _call() -> Any:
        return mechanics._split_with_event(
            joined,
            left_inds=["left"],
            right_inds=None,
            bond_ind=None,
            absorb="left",
            path_role="forward_swap_split",
            split_sites=(0, 1),
            gate_leg_sites=None,
            max_bond=1,
            sequence_index=0,
        )

    if should_raise:
        with pytest.raises(RuntimeError):
            _call()
    else:
        _left, _right, event = _call()
        assert event["actual_discarded_weight_raw"] == pytest.approx(
            discarded,
            rel=0.0,
            abs=5.0e-15,
        )


def test_capped_operator_split_rejects_a_missing_shared_bond_transactionally(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import quimb.tensor as qtn

    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    candidate = _torch_zero_mps()
    before = candidate.to_dense().detach().clone()
    monkeypatch.setattr(qtn, "group_inds", lambda _left, _right: ((), (), ()))

    with pytest.raises(RuntimeError):
        mechanics._operator_split(
            candidate,
            torch.eye(4, dtype=torch.complex128),
            where=(0, 1),
            absorb="left",
            max_bond=2,
            sequence_index=0,
        )

    torch.testing.assert_close(
        candidate.to_dense(),
        before,
        rtol=0.0,
        atol=0.0,
    )


def test_capped_operator_split_passes_both_tensor_partitions_to_actual_split(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    candidate = _torch_zero_mps()
    original_split = mechanics._split_with_event
    calls: list[dict[str, Any]] = []

    def split_spy(joined: Any, **kwargs: Any):
        calls.append(dict(kwargs))
        return original_split(joined, **kwargs)

    monkeypatch.setattr(mechanics, "_split_with_event", split_spy)
    event = mechanics._operator_split(
        candidate,
        torch.eye(4, dtype=torch.complex128),
        where=(0, 1),
        absorb="right",
        max_bond=2,
        sequence_index=0,
    )

    assert event["path_role"] == "two_site_operator_split"
    assert len(calls) == 1
    assert calls[0]["left_inds"] == [candidate.site_ind(0)]
    assert calls[0]["right_inds"] == [candidate.site_ind(1)]


def _zero_actual_split_event(*_args: Any, **_kwargs: Any) -> dict[str, float]:
    return {
        "actual_discarded_weight_raw": 0.0,
        "actual_discarded_weight_fraction_of_pre_split": 0.0,
    }


def test_capped_public_ledger_consistency_accepts_its_closed_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    threshold = 100.0 * mechanics.NUMERICAL_ZERO
    norms = iter((1.0, 1.0, 1.0))
    monkeypatch.setattr(mechanics, "mps_norm_squared", lambda _mps: next(norms))
    monkeypatch.setattr(
        mechanics,
        "_operator_split",
        lambda *_args, **_kwargs: {
            "actual_discarded_weight_raw": threshold,
            "actual_discarded_weight_fraction_of_pre_split": threshold,
        },
    )

    _candidate, event = mechanics.apply_capped_two_site_unitary(
        _torch_zero_mps(),
        torch.eye(4, dtype=torch.complex128),
        support=(0, 1),
        max_bond=2,
    )

    assert event["actual_discarded_weight_raw_sum"] == threshold
    assert event["unitary_truncation_mass_loss"] == 0.0


@pytest.mark.parametrize(
    ("input_norm", "multiple", "should_raise"),
    [
        pytest.param(1.0, 1.0, False, id="inclusive-unit-scale"),
        pytest.param(4.0, 1.0, False, id="inclusive-input-scale"),
        pytest.param(0.25, 1.5, True, id="above-unit-scale-floor"),
    ],
)
def test_capped_public_raw_norm_gate_uses_its_closed_scaled_boundary(
    monkeypatch: pytest.MonkeyPatch,
    input_norm: float,
    multiple: float,
    should_raise: bool,
) -> None:
    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    tolerance = mechanics.NUMERICAL_ZERO * max(1.0, input_norm)
    raw_norm = input_norm + multiple * tolerance
    values = [input_norm, raw_norm]
    if not should_raise:
        values.append(input_norm)
    norms = iter(values)
    monkeypatch.setattr(mechanics, "mps_norm_squared", lambda _mps: next(norms))
    monkeypatch.setattr(mechanics, "_operator_split", _zero_actual_split_event)

    def action() -> tuple[Any, dict[str, Any]]:
        return mechanics.apply_capped_two_site_unitary(
            _torch_zero_mps(),
            torch.eye(4, dtype=torch.complex128),
            support=(0, 1),
            max_bond=2,
        )

    if should_raise:
        with pytest.raises(RuntimeError):
            action()
    else:
        _candidate, event = action()
        assert event["raw_output_norm_sq"] == raw_norm


@pytest.mark.parametrize(
    "observed_norms",
    [
        pytest.param(
            (1.0e6, 1.0e6, 1.0e6 + 5.0e-7),
            id="relative-tolerance",
        ),
        pytest.param(
            (1.0e-13, 1.0e-13, 2.0e-13),
            id="absolute-tolerance",
        ),
    ],
)
def test_capped_public_norm_restoration_uses_both_explicit_tolerance_axes(
    monkeypatch: pytest.MonkeyPatch,
    observed_norms: tuple[float, float, float],
) -> None:
    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    norms = iter(observed_norms)
    monkeypatch.setattr(mechanics, "mps_norm_squared", lambda _mps: next(norms))
    monkeypatch.setattr(mechanics, "_operator_split", _zero_actual_split_event)

    _candidate, event = mechanics.apply_capped_two_site_unitary(
        _torch_zero_mps(),
        torch.eye(4, dtype=torch.complex128),
        support=(0, 1),
        max_bond=2,
    )

    assert (
        event["input_norm_sq"],
        event["raw_output_norm_sq"],
        event["restored_output_norm_sq"],
    ) == observed_norms


def test_capped_public_norm_restoration_rejects_math_default_relative_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    input_norm = 1.0e6
    restored_norm = input_norm + 5.0e-4
    assert restored_norm - input_norm > mechanics.NUMERICAL_ZERO * input_norm
    norms = iter((input_norm, input_norm, restored_norm))
    monkeypatch.setattr(mechanics, "mps_norm_squared", lambda _mps: next(norms))
    monkeypatch.setattr(
        mechanics,
        "_operator_split",
        lambda *_args, **_kwargs: {
            "actual_discarded_weight_raw": 0.0,
            "actual_discarded_weight_fraction_of_pre_split": 0.0,
        },
    )

    with pytest.raises(RuntimeError):
        mechanics.apply_capped_two_site_unitary(
            _torch_zero_mps(),
            torch.eye(4, dtype=torch.complex128),
            support=(0, 1),
            max_bond=2,
        )


@pytest.mark.parametrize("observed_norms", [(0.0,), (1.0, 0.0)])
def test_capped_public_nonpositive_norm_failures_leave_source_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    observed_norms: tuple[float, ...],
) -> None:
    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    source = _torch_zero_mps()
    before = source.to_dense().detach().clone()
    norms = iter(observed_norms)
    monkeypatch.setattr(mechanics, "mps_norm_squared", lambda _mps: next(norms))
    monkeypatch.setattr(mechanics, "_operator_split", _zero_actual_split_event)

    with pytest.raises(RuntimeError):
        mechanics.apply_capped_two_site_unitary(
            source,
            torch.eye(4, dtype=torch.complex128),
            support=(0, 1),
            max_bond=2,
        )

    torch.testing.assert_close(source.to_dense(), before, rtol=0.0, atol=0.0)


def test_capped_preflight_authenticates_backend_shape_and_identity_device(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    class _TensorLookalike:
        dtype = torch.complex128
        device = torch.device("cpu")

    gate = torch.eye(4, dtype=torch.complex128)
    with pytest.raises(TypeError):
        mechanics._preflight(
            _ValidationMps([_TensorLookalike(), _TensorLookalike()]),
            gate,
            support=(0, 1),
            max_bond=1,
        )

    valid = _ValidationMps(
        [
            torch.ones((1, 2), dtype=torch.complex128),
            torch.ones((1, 2), dtype=torch.complex128),
        ]
    )
    with pytest.raises(ValueError):
        mechanics._preflight(
            valid,
            torch.eye(3, dtype=torch.complex128),
            support=(0, 1),
            max_bond=1,
        )

    torch_eye = mechanics.torch.eye
    identity_devices: list[Any] = []

    def torch_eye_spy(*args: Any, **kwargs: Any) -> torch.Tensor:
        identity_devices.append(kwargs.get("device", "missing"))
        return torch_eye(*args, **kwargs)

    monkeypatch.setattr(mechanics.torch, "eye", torch_eye_spy)
    mechanics._preflight(valid, gate, support=(0, 1), max_bond=1)
    assert identity_devices == [torch.device("cpu")]


def test_capped_split_rejects_zero_weight_before_dependency_execution() -> None:
    from error_coupling_simulator.carrier.mps.capped_two_site import (
        _split_with_event,
    )

    joined = _JoinedSplitSpy(data=torch.zeros(1, dtype=torch.complex128))
    with pytest.raises(RuntimeError):
        _split_with_event(
            joined,
            left_inds=["left"],
            right_inds=None,
            bond_ind=None,
            absorb="left",
            path_role="forward_swap_split",
            split_sites=(0, 1),
            gate_leg_sites=None,
            max_bond=1,
            sequence_index=0,
        )
    assert joined.calls == []


def test_capped_operator_split_preserves_gate_partition_and_old_bond(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import quimb.tensor as qtn

    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    candidate = _torch_zero_mps()
    old_bond = tuple(candidate[0].bonds(candidate[1]))[0]
    tensor_type = qtn.Tensor
    tensor_calls: list[dict[str, Any]] = []
    split_calls: list[dict[str, Any]] = []
    split = mechanics._split_with_event

    def tensor_spy(*args: Any, **kwargs: Any) -> Any:
        tensor_calls.append(dict(kwargs))
        return tensor_type(*args, **kwargs)

    def split_spy(joined: Any, **kwargs: Any) -> Any:
        split_calls.append(dict(kwargs))
        return split(joined, **kwargs)

    monkeypatch.setattr(qtn, "Tensor", tensor_spy)
    monkeypatch.setattr(mechanics, "_split_with_event", split_spy)
    mechanics._operator_split(
        candidate,
        torch.eye(4, dtype=torch.complex128),
        where=(0, 1),
        absorb="right",
        max_bond=2,
        sequence_index=0,
    )

    assert len(tensor_calls) == 1
    assert tensor_calls[0]["left_inds"] == tensor_calls[0]["inds"][2:]
    assert split_calls[0]["bond_ind"] == old_bond


def test_capped_nonadjacent_orchestration_preserves_canonical_state_and_restore_site(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import quimb.tensor as qtn

    from error_coupling_simulator.carrier.mps.capped_two_site import (
        apply_capped_two_site_unitary,
    )

    canonicalize = qtn.MatrixProductState.canonicalize_
    multiply = qtn.MatrixProductState.multiply_
    canonical_calls: list[tuple[tuple[int, ...], int | None, dict[str, Any] | None]] = []
    multiply_spreads: list[Any] = []

    def canonicalize_spy(self: Any, where: Any, *args: Any, **kwargs: Any) -> Any:
        sites = (int(where),) if isinstance(where, int) else tuple(map(int, where))
        info = kwargs.get("info")
        canonical_calls.append(
            (sites, None if info is None else id(info), None if info is None else dict(info))
        )
        return canonicalize(self, where, *args, **kwargs)

    def multiply_spy(self: Any, value: Any, *args: Any, **kwargs: Any) -> Any:
        multiply_spreads.append(kwargs.get("spread_over", "missing"))
        return multiply(self, value, *args, **kwargs)

    monkeypatch.setattr(qtn.MatrixProductState, "canonicalize_", canonicalize_spy)
    monkeypatch.setattr(qtn.MatrixProductState, "multiply_", multiply_spy)
    apply_capped_two_site_unitary(
        _torch_zero_mps(5),
        torch.eye(4, dtype=torch.complex128),
        support=(0, 4),
        max_bond=8,
    )

    assert [row[0] for row in canonical_calls] == [
        (3, 4),
        (2, 3),
        (1, 2),
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 4),
    ]
    assert all(row[1] == canonical_calls[0][1] for row in canonical_calls)
    assert canonical_calls[0][2] == {"cur_orthog": "calc"}
    assert canonical_calls[4][2] == {"cur_orthog": (1, 1)}
    assert multiply_spreads == [1]


def test_capped_zero_raw_norm_cannot_reach_restore_division(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    norms = iter((1.0, 0.0))
    monkeypatch.setattr(mechanics, "mps_norm_squared", lambda _mps: next(norms))
    monkeypatch.setattr(
        mechanics,
        "_operator_split",
        lambda *_args, **_kwargs: {
            "actual_discarded_weight_raw": 1.0,
            "actual_discarded_weight_fraction_of_pre_split": 1.0,
        },
    )
    with pytest.raises(RuntimeError):
        mechanics.apply_capped_two_site_unitary(
            _torch_zero_mps(),
            torch.eye(4, dtype=torch.complex128),
            support=(0, 1),
            max_bond=2,
        )


@pytest.mark.parametrize(
    ("input_norm", "discarded", "should_raise"),
    [
        pytest.param(0.25, 50.0e-12, False, id="unit-scale-floor"),
        pytest.param(4.0, 200.0e-12, False, id="input-scale"),
        pytest.param(0.25, 150.0e-12, True, id="floor-is-one-not-two"),
        pytest.param(1.0, 100.5e-12, True, id="factor-is-100-not-101"),
    ],
)
def test_capped_ledger_reconciliation_pins_scaled_closed_boundary(
    monkeypatch: pytest.MonkeyPatch,
    input_norm: float,
    discarded: float,
    should_raise: bool,
) -> None:
    import error_coupling_simulator.carrier.mps.capped_two_site as mechanics

    norms = iter((input_norm, input_norm, input_norm))
    monkeypatch.setattr(mechanics, "mps_norm_squared", lambda _mps: next(norms))
    monkeypatch.setattr(
        mechanics,
        "_operator_split",
        lambda *_args, **_kwargs: {
            "actual_discarded_weight_raw": discarded,
            "actual_discarded_weight_fraction_of_pre_split": discarded,
        },
    )

    def action() -> tuple[Any, dict[str, Any]]:
        return mechanics.apply_capped_two_site_unitary(
            _torch_zero_mps(),
            torch.eye(4, dtype=torch.complex128),
            support=(0, 1),
            max_bond=2,
        )

    if should_raise:
        with pytest.raises(RuntimeError):
            action()
    else:
        _candidate, event = action()
        assert event["actual_discarded_weight_raw_sum"] == discarded
