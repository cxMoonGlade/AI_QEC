"""RED contract for the MCWF uncapped connected three-site MPS route.

The dense oracle in this file is hand-constructed with NumPy.  It does not use
Quimb decomposition, the future Carrier helper, or frontend grouping logic.
The dependency-only ``auto-mps`` check is a negative control: its inherited MPO
split cutoff deletes the weak component even when the later MPS compression is
passed ``cutoff=0.0``.
"""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pytest


_SUPPORT = (0, 1, 2)
_LOCAL_DIMS = (2, 2, 2)
_WEAK_ANGLE = 2.0e-6
_DENSE_ATOL = 2.0e-14
_EVENT_FIELDS = {
    "schema",
    "support",
    "support_local_dims",
    "support_hilbert_dimension",
    "dense_operator_elements",
    "requested_cutoff",
    "requested_max_bond",
    "requested_truncation",
    "split_method",
    "cutoff_mode",
    "quimb_version",
    "input_norm_sq",
    "output_norm_sq",
    "norm_drift_abs",
    "source_unchanged",
    "context",
    "not_a_scientific_carrier",
    "epistemic_class",
}


def _uncapped_api():
    from error_coupling_simulator.carrier.mps.uncapped_nonlocal import (
        apply_uncapped_nonlocal_unitary,
        preflight_uncapped_nonlocal_resource,
    )

    return preflight_uncapped_nonlocal_resource, apply_uncapped_nonlocal_unitary


def _zero_mps(n_sites: int = 3):
    import quimb.tensor as qtn

    return qtn.MPS_computational_state("0" * int(n_sites)).astype(np.complex128)


def _zero_torch_mps(n_sites: int = 3):
    import quimb.tensor as qtn
    import torch

    zero = torch.tensor([1.0, 0.0], dtype=torch.complex128)
    return qtn.MPS_product_state([zero.clone() for _ in range(int(n_sites))])


def _weak_xxx_unitary(angle: float = _WEAK_ANGLE) -> np.ndarray:
    """Exact exp(-i theta XXX), avoiding a matrix-exponential dependency."""

    x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    xxx = np.kron(np.kron(x, x), x)
    return (
        np.cos(float(angle)) * np.eye(8, dtype=np.complex128)
        - 1j * np.sin(float(angle)) * xxx
    )


def _dense_zero_state(n_sites: int = 3) -> np.ndarray:
    state = np.zeros(2 ** int(n_sites), dtype=np.complex128)
    state[0] = 1.0
    return state


def _as_dense(mps) -> np.ndarray:
    values = mps.to_dense()
    if hasattr(values, "detach"):
        values = values.detach().cpu().numpy()
    return np.asarray(values, dtype=np.complex128).reshape(-1)


def _mps_tensor_fingerprint(mps) -> str:
    digest = hashlib.sha256()
    for tensor in mps.tensors:
        digest.update(repr(tuple(tensor.inds)).encode("utf-8"))
        digest.update(repr(tuple(sorted(tensor.tags))).encode("utf-8"))
        values = tensor.data
        if hasattr(values, "detach"):
            values = values.detach().cpu().numpy()
        array = np.ascontiguousarray(values)
        digest.update(array.dtype.str.encode("ascii"))
        digest.update(repr(array.shape).encode("ascii"))
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def test_quimb_auto_mps_negative_control_deletes_the_weak_xxx_term() -> None:
    """Reproduce the inherited MPO-construction cutoff, not a target behavior."""

    source = _zero_mps()
    gate = _weak_xxx_unitary()
    dense_target = gate @ _dense_zero_state()

    inherited = source.gate(
        gate,
        where=_SUPPORT,
        contract="auto-mps",
        max_bond=None,
        cutoff=0.0,
    )
    got = _as_dense(inherited)

    assert abs(dense_target[-1]) > 1.0e-6
    assert got[-1] == pytest.approx(0.0, abs=1.0e-15)
    assert np.max(np.abs(got - dense_target)) > 1.0e-6


def test_mcwf_frontend_uncapped_three_site_route_preserves_the_weak_term() -> None:
    import torch

    from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (
        _apply_mps_gate,
    )

    source = _zero_torch_mps()
    gate = _weak_xxx_unitary()
    dense_target = gate @ _dense_zero_state()
    events: list[dict[str, Any]] = []

    _apply_mps_gate(
        source,
        torch.as_tensor(gate, dtype=torch.complex128),
        support=_SUPPORT,
        substep={"substep_id": "weak_xxx", "substep_kind": "idle"},
        term={"operator_family": "WEAK_XXX"},
        term_index=0,
        branch_bits=(),
        device="cpu",
        max_bond=None,
        dt_ns=1.0,
        microstep_index=0,
        microstep_count=1,
        truncation_events=events,
        track_actual_splits=True,
    )

    np.testing.assert_allclose(
        _as_dense(source),
        dense_target,
        rtol=0.0,
        atol=_DENSE_ATOL,
    )
    assert _as_dense(source)[-1] == pytest.approx(
        dense_target[-1], abs=_DENSE_ATOL
    )


def test_mcwf_uncapped_microstep_refinement_does_not_delete_the_weak_term() -> None:
    import torch

    from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (
        _apply_mps_gate,
    )

    dense_target = _weak_xxx_unitary() @ _dense_zero_state()
    for microstep_count in (1, 4):
        source = _zero_torch_mps()
        events: list[dict[str, Any]] = []
        micro_gate = torch.as_tensor(
            _weak_xxx_unitary(_WEAK_ANGLE / microstep_count),
            dtype=torch.complex128,
        )
        for microstep_index in range(microstep_count):
            _apply_mps_gate(
                source,
                micro_gate,
                support=_SUPPORT,
                substep={"substep_id": "weak_xxx", "substep_kind": "idle"},
                term={"operator_family": "WEAK_XXX"},
                term_index=0,
                branch_bits=(),
                device="cpu",
                max_bond=None,
                dt_ns=1.0 / microstep_count,
                microstep_index=microstep_index,
                microstep_count=microstep_count,
                truncation_events=events,
                track_actual_splits=True,
            )
        np.testing.assert_allclose(
            _as_dense(source),
            dense_target,
            rtol=0.0,
            atol=_DENSE_ATOL,
        )
        assert _as_dense(source)[-1] == pytest.approx(
            dense_target[-1], abs=_DENSE_ATOL
        )


def test_mcwf_uncapped_over_cap_cluster_fails_before_dense_gate_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as execution

    source = _zero_torch_mps(6)
    before = _mps_tensor_fingerprint(source)
    construction_calls: list[str] = []

    def _must_not_construct(*_args: Any, **_kwargs: Any):
        construction_calls.append("called")
        raise AssertionError("over-cap connected gate construction was reached")

    monkeypatch.setattr(execution, "_hamiltonian_group_gates", _must_not_construct)
    substep = {
        "substep_id": "six_site_connected_cluster",
        "terms": [
            {"kind": "hamiltonian", "support": [site, site + 1]}
            for site in range(5)
        ],
    }

    with pytest.raises(ValueError):
        execution._apply_hamiltonian_terms_multilevel(
            source,
            substep,
            device="cpu",
            max_bond=None,
            branch_bits=(),
            truncation_events=[],
            dt_ns=1.0,
            microstep_index=0,
            microstep_count=1,
            local_dims=(2, 2, 2, 2, 2, 2),
        )

    assert construction_calls == []
    assert _mps_tensor_fingerprint(source) == before


def test_uncapped_nonlocal_route_preserves_weak_term_and_event_contract() -> None:
    _, apply_uncapped = _uncapped_api()
    source = _zero_mps()
    before = _mps_tensor_fingerprint(source)
    gate = _weak_xxx_unitary()
    dense_target = gate @ _dense_zero_state()
    context = {"fixture_id": "weak_xxx_three_site", "trajectory_index": 7}

    candidate, event = apply_uncapped(
        source,
        gate,
        support=_SUPPORT,
        local_dims=_LOCAL_DIMS,
        context=context,
    )

    assert candidate is not source
    assert _mps_tensor_fingerprint(source) == before
    np.testing.assert_allclose(
        _as_dense(candidate),
        dense_target,
        rtol=0.0,
        atol=_DENSE_ATOL,
    )
    assert _as_dense(candidate)[-1] == pytest.approx(
        dense_target[-1], abs=_DENSE_ATOL
    )

    assert _EVENT_FIELDS <= set(event)
    assert event["schema"] == (
        "error_coupling_simulator.carrier.mps.uncapped_nonlocal_event.v1"
    )
    assert event["support"] == [0, 1, 2]
    assert event["support_local_dims"] == [2, 2, 2]
    assert event["support_hilbert_dimension"] == 8
    assert event["dense_operator_elements"] == 64
    assert event["requested_cutoff"] == 0.0
    assert event["requested_max_bond"] is None
    assert event["requested_truncation"] is False
    assert event["split_method"] == "svd"
    assert event["cutoff_mode"] == "rsum2"
    assert event["quimb_version"] == "1.14.0"
    assert event["input_norm_sq"] == pytest.approx(1.0, abs=_DENSE_ATOL)
    assert event["output_norm_sq"] == pytest.approx(1.0, abs=_DENSE_ATOL)
    assert event["norm_drift_abs"] <= _DENSE_ATOL
    assert event["source_unchanged"] is True
    assert event["context"] == context
    assert event["context"] is not context
    assert event["not_a_scientific_carrier"] is True
    assert event["epistemic_class"] == "c"


def test_uncapped_nonlocal_resource_preflight_has_frozen_boundaries() -> None:
    preflight, _ = _uncapped_api()

    preflight(support=(0, 1, 2), local_dims=(2, 2, 2))
    preflight(support=(0, 1, 2, 3), local_dims=(4, 4, 4, 4))

    with pytest.raises(ValueError):
        preflight(support=(0, 1), local_dims=(2, 2))
    with pytest.raises(ValueError):
        preflight(
            support=(0, 1, 2, 3, 4, 5),
            local_dims=(2, 2, 2, 2, 2, 2),
        )
    with pytest.raises(ValueError):
        preflight(support=(0, 1, 2, 3), local_dims=(4, 4, 4, 5))
    with pytest.raises(TypeError):
        preflight(support=(0, 1, True), local_dims=(2, 2, 2))
    with pytest.raises(TypeError):
        preflight(support=(0, 1, 2), local_dims=(2, 2, True))


def test_uncapped_resource_preflight_rejects_each_invalid_resource_axis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.carrier.mps.uncapped_nonlocal as mechanics

    invalid_resources = (
        {"support": (-1, 0, 1), "local_dims": (2, 2, 2)},
        {"support": (0, 1, 2), "local_dims": ()},
        {"support": (0, 1, 2), "local_dims": (2, 1, 2)},
        {"support": (0, 1, 3), "local_dims": (2, 2, 2)},
    )
    for resource in invalid_resources:
        with pytest.raises(ValueError):
            mechanics.preflight_uncapped_nonlocal_resource(**resource)

    monkeypatch.setattr(mechanics, "MAX_DENSE_OPERATOR_ELEMENTS", 63)
    with pytest.raises(ValueError):
        mechanics.preflight_uncapped_nonlocal_resource(
            support=_SUPPORT,
            local_dims=_LOCAL_DIMS,
        )


def test_uncapped_nonlocal_context_must_be_a_mapping_before_execution() -> None:
    _, apply_uncapped = _uncapped_api()
    source = _zero_mps()
    before = _mps_tensor_fingerprint(source)

    with pytest.raises(TypeError):
        apply_uncapped(
            source,
            _weak_xxx_unitary(),
            support=_SUPPORT,
            local_dims=_LOCAL_DIMS,
            context=[],  # type: ignore[arg-type]
        )

    assert _mps_tensor_fingerprint(source) == before


@pytest.mark.parametrize(
    "dtype",
    [
        pytest.param(np.complex64, id="complex64"),
        pytest.param(np.float64, id="float64"),
    ],
)
def test_uncapped_nonlocal_rejects_non_complex128_numpy_source_before_promotion(
    monkeypatch: pytest.MonkeyPatch,
    dtype: type[np.generic],
) -> None:
    import quimb.tensor as qtn

    import error_coupling_simulator.carrier.mps.uncapped_nonlocal as mechanics

    source = qtn.MPS_computational_state("000").astype(dtype)
    before = _mps_tensor_fingerprint(source)
    monkeypatch.setattr(
        mechanics,
        "mps_norm_squared",
        lambda _mps: (_ for _ in ()).throw(
            AssertionError("invalid source reached candidate promotion")
        ),
    )

    with pytest.raises(TypeError):
        mechanics.apply_uncapped_nonlocal_unitary(
            source,
            _weak_xxx_unitary(),
            support=_SUPPORT,
            local_dims=_LOCAL_DIMS,
            context={"fixture_id": "invalid_source_precision"},
        )

    assert _mps_tensor_fingerprint(source) == before


@pytest.mark.parametrize(
    ("observed_norms", "error_type"),
    [
        ((0.0,), ValueError),
        ((1.0, 0.0), RuntimeError),
    ],
    ids=("nonpositive_source", "nonpositive_candidate"),
)
def test_uncapped_nonlocal_rejects_nonpositive_norm_without_source_mutation(
    monkeypatch: pytest.MonkeyPatch,
    observed_norms: tuple[float, ...],
    error_type: type[Exception],
) -> None:
    import error_coupling_simulator.carrier.mps.uncapped_nonlocal as mechanics

    source = _zero_mps()
    before = _mps_tensor_fingerprint(source)
    norm_values = iter(observed_norms)
    monkeypatch.setattr(
        mechanics,
        "mps_norm_squared",
        lambda _mps: next(norm_values),
    )

    with pytest.raises(error_type):
        mechanics.apply_uncapped_nonlocal_unitary(
            source,
            _weak_xxx_unitary(),
            support=_SUPPORT,
            local_dims=_LOCAL_DIMS,
            context={"fixture_id": "nonpositive_norm"},
        )

    assert _mps_tensor_fingerprint(source) == before


def test_over_cap_rejects_before_gate_materialization_or_quimb_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import quimb.tensor as qtn

    _, apply_uncapped = _uncapped_api()
    source = _zero_mps(6)
    before = _mps_tensor_fingerprint(source)
    construction_calls: list[str] = []

    class _MustNotMaterialize:
        def __array__(self, *_args: Any, **_kwargs: Any) -> np.ndarray:
            raise AssertionError("over-cap gate was materialized")

    def _must_not_construct(*_args: Any, **_kwargs: Any):
        construction_calls.append("called")
        raise AssertionError("over-cap MPO was constructed")

    monkeypatch.setattr(
        qtn.MatrixProductOperator,
        "from_dense",
        classmethod(_must_not_construct),
    )

    with pytest.raises(ValueError):
        apply_uncapped(
            source,
            _MustNotMaterialize(),
            support=(0, 1, 2, 3, 4, 5),
            local_dims=(2, 2, 2, 2, 2, 2),
            context={"fixture_id": "six_site_over_cap"},
        )

    assert construction_calls == []
    assert _mps_tensor_fingerprint(source) == before


@pytest.mark.parametrize(
    "support",
    [
        (0, 2, 1),
        (0, 1, 1),
        (0, 1, True),
    ],
)
def test_support_order_or_identity_corruption_fails_transactionally(
    support: tuple[int, ...],
) -> None:
    _, apply_uncapped = _uncapped_api()
    source = _zero_mps()
    before = _mps_tensor_fingerprint(source)

    error_type = TypeError if any(isinstance(site, bool) for site in support) else ValueError
    with pytest.raises(error_type):
        apply_uncapped(
            source,
            _weak_xxx_unitary(),
            support=support,
            local_dims=_LOCAL_DIMS,
            context={"fixture_id": "corrupt_support"},
        )

    assert _mps_tensor_fingerprint(source) == before


@pytest.mark.parametrize(
    "gate",
    [
        np.eye(4, dtype=np.complex128),
        0.5 * np.eye(8, dtype=np.complex128),
        np.where(
            np.eye(8, dtype=bool),
            np.complex128(np.nan),
            np.complex128(0.0),
        ),
    ],
    ids=("wrong_shape", "nonunitary", "nonfinite"),
)
def test_invalid_unitary_fails_before_source_mutation(gate: np.ndarray) -> None:
    _, apply_uncapped = _uncapped_api()
    source = _zero_mps()
    before = _mps_tensor_fingerprint(source)

    with pytest.raises(ValueError):
        apply_uncapped(
            source,
            gate,
            support=_SUPPORT,
            local_dims=_LOCAL_DIMS,
            context={"fixture_id": "invalid_unitary"},
        )

    assert _mps_tensor_fingerprint(source) == before


def test_quimb_execution_exception_is_wrapped_and_transactional(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import quimb.tensor as qtn

    _, apply_uncapped = _uncapped_api()
    source = _zero_mps()
    before = _mps_tensor_fingerprint(source)

    def _injected_failure(*_args: Any, **_kwargs: Any):
        raise OSError("injected Quimb construction failure")

    monkeypatch.setattr(
        qtn.MatrixProductOperator,
        "from_dense",
        classmethod(_injected_failure),
    )

    with pytest.raises(RuntimeError):
        apply_uncapped(
            source,
            _weak_xxx_unitary(),
            support=_SUPPORT,
            local_dims=_LOCAL_DIMS,
            context={"fixture_id": "injected_quimb_failure"},
        )

    assert _mps_tensor_fingerprint(source) == before


def test_candidate_norm_corruption_fails_before_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import quimb.tensor as qtn

    _, apply_uncapped = _uncapped_api()
    source = _zero_mps()
    before = _mps_tensor_fingerprint(source)
    original_public = qtn.MatrixProductState.gate_with_submpo
    original_inplace = qtn.MatrixProductState.gate_with_submpo_

    def _scale_first_tensor(candidate):
        tensor = candidate.tensors[0]
        tensor.modify(data=np.asarray(tensor.data) * 0.5)
        return candidate

    def _corrupt_public(self, *args: Any, **kwargs: Any):
        return _scale_first_tensor(original_public(self, *args, **kwargs))

    def _corrupt_inplace(self, *args: Any, **kwargs: Any):
        return _scale_first_tensor(original_inplace(self, *args, **kwargs))

    monkeypatch.setattr(
        qtn.MatrixProductState,
        "gate_with_submpo",
        _corrupt_public,
    )
    monkeypatch.setattr(
        qtn.MatrixProductState,
        "gate_with_submpo_",
        _corrupt_inplace,
    )

    with pytest.raises(RuntimeError):
        apply_uncapped(
            source,
            _weak_xxx_unitary(),
            support=_SUPPORT,
            local_dims=_LOCAL_DIMS,
            context={"fixture_id": "corrupt_candidate_norm"},
        )

    assert _mps_tensor_fingerprint(source) == before


def test_public_mcwf_schedule_reaches_uncapped_three_site_mechanics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from error_coupling_simulator.frontend import (
        CircuitBuilder,
        circuit_ir_to_substep_schedule,
    )
    import error_coupling_simulator.frontend.axis1_carrier_program as carrier_program
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as execution

    monkeypatch.setattr(execution, "_require_cuda_device", lambda _device: "cpu")
    lower_controls = carrier_program.lower_ideal_controls_for_selection

    def lower_controls_on_cpu(selection, *, dt_ns, device):
        assert device == "cuda"
        return lower_controls(selection, dt_ns=dt_ns, device="cpu")

    monkeypatch.setattr(
        carrier_program,
        "lower_ideal_controls_for_selection",
        lower_controls_on_cpu,
    )

    builder = CircuitBuilder(num_qubits=3)
    builder.declare_static_zz_couplings(((0, 1), (0, 2)))
    builder.h(0)
    builder.measure((0, 1, 2), key=("m0", "m1", "m2"))
    schedule = circuit_ir_to_substep_schedule(builder.build())

    manifest = execution.axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        device="cpu",
        max_bond=None,
        mass_residual_budget=None,
        trajectory_count=1,
        rng_seed=7,
    )

    assert manifest["execution_status"] == "completed"
    assert manifest["certification_status"] == "not_evaluated"
    assert manifest["verdict"] == "fail"
    events = manifest["mps_execution"]["uncapped_nonlocal_unitary_events"]
    assert len(events) == 1
    assert events[0]["support"] == [0, 1, 2]
    assert events[0]["requested_cutoff"] == 0.0
    assert events[0]["requested_truncation"] is False
    assert events[0]["not_a_scientific_carrier"] is True
