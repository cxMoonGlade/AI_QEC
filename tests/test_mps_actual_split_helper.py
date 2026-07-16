"""Behavioral contract for one capped two-site Quimb MPS operation.

The helper under test owns the actual split ledger for the restricted MPS
execution routes.  These fixtures intentionally keep the dense oracle in the
test only: production callers receive the capped candidate and the local
split/norm event, not a dense-state error bound.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

import numpy as np
import pytest


_EVENT_FIELDS = {
    "support",
    "gate_leg_sites",
    "max_bond",
    "input_norm_sq",
    "raw_output_norm_sq",
    "restored_output_norm_sq",
    "deterministic_norm_restore_factor",
    "split_count",
    "split_records",
    "not_a_global_error_bound",
    "physical_branch_probability",
}
_SPLIT_FIELDS = {
    "sequence_index",
    "path_role",
    "split_sites",
    "gate_leg_sites",
    "actual_kept_rank",
    "actual_discarded_weight_raw",
    "actual_discarded_weight_fraction_of_pre_split",
    "requested_cutoff_mode",
}
_NONADJACENT_ROLES = [
    "forward_swap_split",
    "forward_swap_split",
    "forward_swap_split",
    "two_site_operator_split",
    "reverse_swap_split",
    "reverse_swap_split",
    "reverse_swap_split",
]
_NONADJACENT_SPLIT_SITES = [
    [3, 4],
    [2, 3],
    [1, 2],
    [0, 1],
    [1, 2],
    [2, 3],
    [3, 4],
]


def _cnot() -> np.ndarray:
    return np.asarray(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
        dtype=np.complex128,
    )


def _five_qubit_product_mps(*, plus_site: int):
    import quimb.tensor as qtn
    import torch

    zero = torch.tensor([1.0, 0.0], dtype=torch.complex128)
    plus = torch.tensor([1.0, 1.0], dtype=torch.complex128) / math.sqrt(2.0)
    factors = [zero.clone() for _ in range(5)]
    factors[int(plus_site)] = plus
    return qtn.MPS_product_state(factors)


def _torch_gate(values: np.ndarray):
    import torch

    return torch.as_tensor(values, dtype=torch.complex128, device="cpu")


def _apply_capped_two_site_unitary(
    mps,
    gate,
    *,
    support: tuple[int, int],
    max_bond: Any,
    context: dict[str, Any],
):
    from error_coupling_simulator.frontend._mps_actual_split import (
        apply_capped_two_site_unitary,
    )

    return apply_capped_two_site_unitary(
        mps,
        gate,
        support=support,
        max_bond=max_bond,
        context=context,
    )


def _as_dense(mps) -> np.ndarray:
    values = mps.to_dense()
    if hasattr(values, "detach"):
        values = values.detach().cpu().numpy()
    return np.asarray(values, dtype=np.complex128).reshape(-1)


def _norm_sq(mps) -> float:
    values = _as_dense(mps)
    return float(np.vdot(values, values).real)


def _normalized_fidelity(reference: np.ndarray, candidate: np.ndarray) -> float:
    ref = np.asarray(reference, dtype=np.complex128).reshape(-1)
    got = np.asarray(candidate, dtype=np.complex128).reshape(-1)
    ref = ref / np.linalg.norm(ref)
    got = got / np.linalg.norm(got)
    return float(abs(np.vdot(ref, got)) ** 2)


def _apply_two_site_dense(
    state: np.ndarray,
    gate: np.ndarray,
    *,
    support: tuple[int, int],
) -> np.ndarray:
    """Independent ordered-leg dense oracle with site 0 most significant."""

    n_sites = int(round(math.log2(np.asarray(state).size)))
    rest = tuple(site for site in range(n_sites) if site not in support)
    permutation = tuple(support) + rest
    inverse = np.argsort(permutation)
    front = np.transpose(
        np.asarray(state, dtype=np.complex128).reshape((2,) * n_sites),
        permutation,
    ).reshape(4, -1)
    acted = (np.asarray(gate, dtype=np.complex128) @ front).reshape(
        (2, 2) + (2,) * len(rest)
    )
    return np.transpose(acted, inverse).reshape(-1)


def _mps_tensor_fingerprint(mps) -> str:
    """Hash the stored tensors, indices, and tags without changing gauge."""

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


def _assert_event_shape(event: dict[str, Any]) -> list[dict[str, Any]]:
    assert _EVENT_FIELDS <= set(event)
    assert event["split_count"] == len(event["split_records"])
    assert event["not_a_global_error_bound"] is True
    assert event["physical_branch_probability"] is None
    records = event["split_records"]
    assert all(_SPLIT_FIELDS <= set(record) for record in records)
    assert [record["sequence_index"] for record in records] == list(
        range(len(records))
    )
    assert all(record["requested_cutoff_mode"] == "rsum2" for record in records)
    return records


def test_nonadjacent_cap_one_reports_all_splits_and_restores_only_unitary_norm() -> None:
    mps = _five_qubit_product_mps(plus_site=0)
    original_dense = _as_dense(mps)
    original_fingerprint = _mps_tensor_fingerprint(mps)
    gate_np = _cnot()
    dense_target = _apply_two_site_dense(
        original_dense, gate_np, support=(0, 4)
    )

    candidate, event = _apply_capped_two_site_unitary(
        mps,
        _torch_gate(gate_np),
        support=(0, 4),
        max_bond=1,
        context={"fixture_id": "nonadjacent_cnot_5q_cap1"},
    )

    records = _assert_event_shape(event)
    assert event["support"] == [0, 4]
    assert event["gate_leg_sites"] == [0, 1]
    assert event["max_bond"] == 1
    assert event["split_count"] == 7
    assert [record["path_role"] for record in records] == _NONADJACENT_ROLES
    assert [record["split_sites"] for record in records] == (
        _NONADJACENT_SPLIT_SITES
    )
    assert records[3]["gate_leg_sites"] == [0, 1]
    assert all(record["actual_kept_rank"] == 1 for record in records)
    assert sum(
        record["actual_discarded_weight_raw"] for record in records
    ) == pytest.approx(0.5, abs=1.0e-14)
    assert sum(
        record["actual_discarded_weight_fraction_of_pre_split"]
        for record in records
    ) == pytest.approx(0.5, abs=1.0e-14)

    assert event["input_norm_sq"] == pytest.approx(1.0, abs=1.0e-14)
    assert event["raw_output_norm_sq"] == pytest.approx(0.5, abs=1.0e-14)
    assert event["restored_output_norm_sq"] == pytest.approx(1.0, abs=1.0e-14)
    assert event["deterministic_norm_restore_factor"] == pytest.approx(
        math.sqrt(2.0), abs=1.0e-14
    )
    assert _norm_sq(candidate) == pytest.approx(1.0, abs=1.0e-14)
    assert _normalized_fidelity(dense_target, _as_dense(candidate)) == pytest.approx(
        0.5, abs=1.0e-14
    )
    assert _mps_tensor_fingerprint(mps) == original_fingerprint
    np.testing.assert_array_equal(_as_dense(mps), original_dense)


def test_nonadjacent_exact_cap_has_zero_discard_and_dense_fidelity_one() -> None:
    import quimb.tensor as qtn

    mps = _five_qubit_product_mps(plus_site=0)
    original_dense = _as_dense(mps)
    original_fingerprint = _mps_tensor_fingerprint(mps)
    dense_target = _apply_two_site_dense(
        original_dense, _cnot(), support=(0, 4)
    )
    split_identity = qtn.Tensor.split

    candidate, event = _apply_capped_two_site_unitary(
        mps,
        _torch_gate(_cnot()),
        support=(0, 4),
        max_bond=8,
        context={"fixture_id": "nonadjacent_cnot_5q_exact_cap"},
    )

    records = _assert_event_shape(event)
    assert qtn.Tensor.split is split_identity
    assert event["split_count"] == 7
    assert [record["path_role"] for record in records] == _NONADJACENT_ROLES
    assert max(
        record["actual_discarded_weight_raw"] for record in records
    ) == pytest.approx(0.0, abs=1.0e-14)
    assert max(
        record["actual_discarded_weight_fraction_of_pre_split"]
        for record in records
    ) == pytest.approx(0.0, abs=1.0e-14)
    assert event["input_norm_sq"] == pytest.approx(1.0, abs=1.0e-14)
    assert event["raw_output_norm_sq"] == pytest.approx(1.0, abs=1.0e-14)
    assert event["restored_output_norm_sq"] == pytest.approx(1.0, abs=1.0e-14)
    assert event["deterministic_norm_restore_factor"] == pytest.approx(
        1.0, abs=1.0e-14
    )
    assert _normalized_fidelity(dense_target, _as_dense(candidate)) == pytest.approx(
        1.0, abs=1.0e-14
    )
    assert _mps_tensor_fingerprint(mps) == original_fingerprint


def test_corrupted_split_error_cannot_hide_observed_unitary_norm_loss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The split ledger is cross-checked against the independently observed norm."""
    import quimb.tensor.tensor_core as tensor_core

    original_split = tensor_core.Tensor.split

    def _corrupted_split(self, *args, **kwargs):
        result = original_split(self, *args, **kwargs)
        info = kwargs.get("info")
        if isinstance(info, dict) and "error" in info:
            info["error"] = 0.0
        return result

    monkeypatch.setattr(tensor_core.Tensor, "split", _corrupted_split)
    mps = _five_qubit_product_mps(plus_site=0)
    before = _mps_tensor_fingerprint(mps)

    with pytest.raises(RuntimeError, match="discarded-weight ledger.*norm loss"):
        _apply_capped_two_site_unitary(
            mps,
            _torch_gate(_cnot()),
            support=(0, 4),
            max_bond=1,
            context={"fixture_id": "corrupted_error_info"},
        )

    assert _mps_tensor_fingerprint(mps) == before


@pytest.mark.parametrize("corrupted_error", [float("nan"), 10.0])
def test_invalid_split_error_fails_closed_before_candidate_commit(
    monkeypatch: pytest.MonkeyPatch,
    corrupted_error: float,
) -> None:
    import quimb.tensor.tensor_core as tensor_core

    original_split = tensor_core.Tensor.split

    def _corrupted_split(self, *args, **kwargs):
        result = original_split(self, *args, **kwargs)
        info = kwargs.get("info")
        if isinstance(info, dict) and "error" in info:
            info["error"] = corrupted_error
        return result

    monkeypatch.setattr(tensor_core.Tensor, "split", _corrupted_split)
    mps = _five_qubit_product_mps(plus_site=0)
    before = _mps_tensor_fingerprint(mps)

    with pytest.raises(RuntimeError):
        _apply_capped_two_site_unitary(
            mps,
            _torch_gate(_cnot()),
            support=(0, 4),
            max_bond=1,
            context={"fixture_id": "invalid_error_info"},
        )

    assert _mps_tensor_fingerprint(mps) == before


def test_commit_candidate_rolls_back_mutate_then_raise_at_failing_site() -> None:
    import torch

    from error_coupling_simulator.frontend._mps_actual_split import (
        commit_mps_candidate_,
    )

    class _Tensor:
        def __init__(self, value: float, *, fail_once: bool = False) -> None:
            self.data = torch.tensor([value], dtype=torch.complex128)
            self.inds = ("bond",)
            self.tags = {"SITE"}
            self.fail_once = fail_once

        def modify(self, *, data):
            self.data = data
            if self.fail_once:
                self.fail_once = False
                raise RuntimeError("injected candidate commit failure")

    class _Mps:
        def __init__(self, tensors):
            self.tensors = tensors
            self.L = len(tensors)

        def __getitem__(self, index):
            return self.tensors[index]

    target = _Mps([_Tensor(1.0), _Tensor(2.0, fail_once=True), _Tensor(3.0)])
    candidate = _Mps([_Tensor(10.0), _Tensor(20.0), _Tensor(30.0)])
    originals = [tensor.data.clone() for tensor in target.tensors]

    with pytest.raises(RuntimeError, match="candidate commit failure"):
        commit_mps_candidate_(target, candidate)

    assert all(
        torch.equal(tensor.data, original)
        for tensor, original in zip(target.tensors, originals, strict=True)
    )


def test_reversed_ordered_support_preserves_gate_legs() -> None:
    mps = _five_qubit_product_mps(plus_site=4)
    original_dense = _as_dense(mps)
    dense_target = _apply_two_site_dense(
        original_dense, _cnot(), support=(4, 0)
    )

    candidate, event = _apply_capped_two_site_unitary(
        mps,
        _torch_gate(_cnot()),
        support=(4, 0),
        max_bond=8,
        context={"fixture_id": "reversed_nonadjacent_cnot_5q_exact_cap"},
    )

    records = _assert_event_shape(event)
    assert event["support"] == [4, 0]
    assert event["gate_leg_sites"] == [1, 0]
    assert records[3]["path_role"] == "two_site_operator_split"
    assert records[3]["gate_leg_sites"] == [1, 0]
    assert _normalized_fidelity(dense_target, _as_dense(candidate)) == pytest.approx(
        1.0, abs=1.0e-14
    )


@pytest.mark.parametrize("invalid_cap", [None, True, 0, -1, 1.5])
def test_invalid_cap_fails_closed_without_mutating_input(invalid_cap: Any) -> None:
    mps = _five_qubit_product_mps(plus_site=0)
    before = _mps_tensor_fingerprint(mps)
    dense_before = _as_dense(mps)

    with pytest.raises((TypeError, ValueError)):
        _apply_capped_two_site_unitary(
            mps,
            _torch_gate(_cnot()),
            support=(0, 4),
            max_bond=invalid_cap,
            context={"fixture_id": "invalid_cap"},
        )

    assert _mps_tensor_fingerprint(mps) == before
    np.testing.assert_array_equal(_as_dense(mps), dense_before)


def test_gate_failure_is_atomic_and_does_not_leak_a_split_replacement() -> None:
    import quimb.tensor as qtn

    mps = _five_qubit_product_mps(plus_site=0)
    before = _mps_tensor_fingerprint(mps)
    dense_before = _as_dense(mps)
    split_identity = qtn.Tensor.split

    with pytest.raises((TypeError, ValueError)):
        _apply_capped_two_site_unitary(
            mps,
            _torch_gate(np.eye(3, dtype=np.complex128)),
            support=(0, 4),
            max_bond=1,
            context={"fixture_id": "invalid_gate"},
        )

    assert qtn.Tensor.split is split_identity
    assert _mps_tensor_fingerprint(mps) == before
    np.testing.assert_array_equal(_as_dense(mps), dense_before)


def test_qt_production_seam_commits_actual_split_candidate() -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _apply_two_site_gate,
    )

    mps = _five_qubit_product_mps(plus_site=0)
    dense_target = _apply_two_site_dense(_as_dense(mps), _cnot(), support=(0, 4))
    events: list[dict[str, Any]] = []

    _apply_two_site_gate(
        mps,
        _torch_gate(_cnot()),
        support=(0, 4),
        substep={"substep_id": "s0", "substep_kind": "two_qubit_gate"},
        term={"operator_family": "CTRL_CX"},
        term_index=0,
        branch_bits=(1,),
        device="cpu",
        max_bond=1,
        dt_ns=1.0,
        microstep_index=0,
        microstep_count=1,
        truncation_events=events,
        trajectory_index=3,
    )

    assert len(events) == 1
    event = events[0]
    assert event["ledger_method"] == (
        "quimb_actual_svd_split_per_two_site_unitary_gate"
    )
    assert event["split_count"] == 7
    assert event["trajectory_index"] == 3
    assert event["branch_record_prefix"] == [1]
    assert event["hamiltonian_pass_index"] == 0
    assert _norm_sq(mps) == pytest.approx(1.0, abs=1.0e-14)
    assert _normalized_fidelity(dense_target, _as_dense(mps)) == pytest.approx(
        0.5, abs=1.0e-14
    )


@pytest.mark.parametrize("invalid_cap", [True, 1.5, "2"])
@pytest.mark.parametrize("seam", ["qt", "mcwf"])
def test_production_seams_do_not_coerce_invalid_max_bond(
    invalid_cap: Any,
    seam: str,
) -> None:
    """The strict helper contract must survive both production call seams."""
    mps = _five_qubit_product_mps(plus_site=0)
    before = _mps_tensor_fingerprint(mps)
    events: list[dict[str, Any]] = []

    if seam == "qt":
        from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
            _apply_two_site_gate,
        )

        invoke = lambda: _apply_two_site_gate(
            mps,
            _torch_gate(_cnot()),
            support=(0, 4),
            substep={"substep_id": "s0", "substep_kind": "two_qubit_gate"},
            term={"operator_family": "CTRL_CX"},
            term_index=0,
            branch_bits=(),
            device="cpu",
            max_bond=invalid_cap,
            dt_ns=1.0,
            microstep_index=0,
            microstep_count=1,
            truncation_events=events,
        )
    else:
        from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (
            _apply_mps_gate,
        )

        invoke = lambda: _apply_mps_gate(
            mps,
            _torch_gate(_cnot()),
            support=(0, 4),
            substep={"substep_id": "s0", "substep_kind": "two_qubit_gate"},
            term={"operator_family": "CTRL_CX"},
            term_index=0,
            branch_bits=(),
            device="cpu",
            max_bond=invalid_cap,
            dt_ns=1.0,
            microstep_index=0,
            microstep_count=1,
            truncation_events=events,
            track_actual_splits=True,
        )

    with pytest.raises(TypeError):
        invoke()

    assert events == []
    assert _mps_tensor_fingerprint(mps) == before


@pytest.mark.parametrize("threshold", [float("nan"), float("inf")])
def test_truncation_gate_rejects_nonfinite_thresholds(threshold: float) -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_gate_result,
    )

    with pytest.raises(ValueError, match="finite"):
        _truncation_gate_result(
            {"discarded_weight_sum": 0.0, "worst_cut_discarded_weight": 0.0},
            worst_cut_discarded_weight_gate=threshold,
            total_discarded_weight_gate=None,
        )


def test_truncation_gate_fails_closed_on_nonfinite_observed_ledger() -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_gate_result,
    )

    result = _truncation_gate_result(
        {
            "discarded_weight_sum": float("nan"),
            "worst_cut_discarded_weight": 0.0,
        },
        worst_cut_discarded_weight_gate=1.0,
        total_discarded_weight_gate=1.0,
    )

    assert result["passed"] is False
    assert "nonfinite_observed_total_discarded_weight" in result["violations"]


def _synthetic_truncation_event(
    value: float,
    *,
    trajectory_index: int | None = None,
    incoming_branch_weight: float | None = None,
    branch_ordinal: int | None = None,
    hamiltonian_pass_index: int = 0,
) -> dict[str, Any]:
    return {
        "substep_id": "s0",
        "term_index": 0,
        "operator_family": "CTRL_CX",
        "support": [0, 4],
        "dt_ns_effective": 1.0,
        "microstep_index": 0,
        "microstep_count": 1,
        "hamiltonian_pass_index": int(hamiltonian_pass_index),
        "actual_discarded_weight_fraction_sum": float(value),
        "actual_discarded_weight_raw_sum": float(value),
        "unitary_truncation_mass_loss": float(value),
        "split_count": 1,
        "split_records": [
            {
                "actual_discarded_weight_raw": float(value),
                "actual_discarded_weight_fraction_of_pre_split": float(value),
            }
        ],
        "trajectory_index": trajectory_index,
        "incoming_branch_weight": incoming_branch_weight,
        "branch_ordinal": branch_ordinal,
        "branch_record_prefix": [],
    }


_GATE_OCCURRENCE_FIELDS = (
    "substep_id",
    "term_index",
    "operator_family",
    "support",
    "microstep_index",
    "microstep_count",
    "hamiltonian_pass_index",
    "dt_ns_effective",
)


def _expected_gate_occurrence(event: dict[str, Any]) -> dict[str, Any]:
    return {field: event[field] for field in _GATE_OCCURRENCE_FIELDS}


def test_sampled_truncation_aggregation_is_trajectory_count_invariant() -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_gate_result,
        _truncation_ledger,
    )

    events = [
        _synthetic_truncation_event(0.3, trajectory_index=0),
        _synthetic_truncation_event(0.6, trajectory_index=1),
        _synthetic_truncation_event(0.0, trajectory_index=2),
    ]
    ledger = _truncation_ledger(
        max_bond=1,
        num_sites=5,
        max_observed_bond=1,
        truncation_events=events,
        aggregation_mode="sampled_trajectory_mean",
        trajectory_count=3,
        expected_gate_occurrences=[_expected_gate_occurrence(events[0])],
    )
    duplicated = _truncation_ledger(
        max_bond=1,
        num_sites=5,
        max_observed_bond=1,
        truncation_events=events
        + [
            _synthetic_truncation_event(0.3, trajectory_index=3),
            _synthetic_truncation_event(0.6, trajectory_index=4),
            _synthetic_truncation_event(0.0, trajectory_index=5),
        ],
        aggregation_mode="sampled_trajectory_mean",
        trajectory_count=6,
        expected_gate_occurrences=[_expected_gate_occurrence(events[0])],
    )

    assert ledger["actual_discarded_weight_fraction_sum"] == pytest.approx(0.9)
    assert ledger["path_aggregated_local_discarded_fraction_sum"] == pytest.approx(
        0.3
    )
    assert ledger["discarded_weight_sum"] == pytest.approx(0.3)
    assert duplicated["discarded_weight_sum"] == pytest.approx(0.3)
    assert duplicated["actual_discarded_weight_fraction_sum"] == pytest.approx(1.8)
    assert ledger["aggregation"]["mode"] == "sampled_trajectory_mean"
    assert ledger["aggregation"]["context_complete"] is True
    assert ledger["aggregation"]["observed_gate_occurrence_count"] == 1
    for candidate in (ledger, duplicated):
        gate = _truncation_gate_result(
            candidate,
            worst_cut_discarded_weight_gate=1.0,
            total_discarded_weight_gate=0.4,
        )
        assert gate["passed"] is True


def test_exact_truncation_aggregation_uses_incoming_branch_probability() -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_ledger,
    )

    events = [
        _synthetic_truncation_event(
            0.2, incoming_branch_weight=0.25, branch_ordinal=0
        ),
        _synthetic_truncation_event(
            0.6, incoming_branch_weight=0.75, branch_ordinal=1
        ),
    ]
    ledger = _truncation_ledger(
        max_bond=1,
        num_sites=5,
        max_observed_bond=1,
        truncation_events=events,
        aggregation_mode="exact_branch_probability_weighted",
        trajectory_count=None,
        expected_gate_occurrences=[_expected_gate_occurrence(events[0])],
    )

    assert ledger["actual_discarded_weight_fraction_sum"] == pytest.approx(0.8)
    assert ledger["path_aggregated_local_discarded_fraction_sum"] == pytest.approx(
        0.5
    )
    assert ledger["discarded_weight_sum"] == pytest.approx(0.5)
    assert ledger["aggregation"]["weight_source"] == "incoming_branch_weight"
    assert ledger["aggregation"]["context_complete"] is True
    assert ledger["aggregation"]["observed_gate_occurrence_count"] == 1


def _qt_policy_for_synthetic_finite_bond_ledger(
    ledger: dict[str, Any],
    *,
    worst_gate: float | None,
    total_gate: float | None,
) -> dict[str, Any]:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _restricted_acceptance_policy,
    )

    return _restricted_acceptance_policy(
        program={"requires_scalable_backend": True},
        execution={
            "total_probability_residual": 0.0,
            "trajectory_sampling": {
                "mode": "exact_branch_enumeration",
                "trajectory_count": None,
                "rng_seed": None,
                "rng_seed_was_explicit": False,
            },
            "finite_step_policy": {"microstep_count": 1},
            "mps_truncation_ledger": ledger,
        },
        certification={
            "executed": False,
            "reason": "schedule_contains_scalable_required_rows",
            "comparison_outcome_is_metric": False,
        },
        finite_step_order="first_order",
        finite_step_policy="operator_family_product_formula_v1",
        max_bond=1,
        worst_cut_discarded_weight_gate=worst_gate,
        total_discarded_weight_gate=total_gate,
    )


def _synthetic_complete_finite_bond_ledger(*, discarded: float) -> dict[str, Any]:
    return {
        "explicit_truncation_requested": True,
        "exact_bond_dimension_sufficient": 4,
        "exact_bond_policy": "finite_cap_below_conservative_exact_sufficient_bond",
        "accepted_as_exact_bond_representation": False,
        "discarded_weight_ledger_complete": True,
        "discarded_weight_sum": float(discarded),
        "worst_cut_discarded_weight": float(discarded),
        "n_truncating_ops": int(discarded > 0.0),
        "epistemic_class": "c",
    }


def test_finite_bond_restricted_acceptance_requires_gate_after_actual_loss() -> None:
    ledger = _synthetic_complete_finite_bond_ledger(discarded=0.1)
    ungated = _qt_policy_for_synthetic_finite_bond_ledger(
        ledger,
        worst_gate=None,
        total_gate=None,
    )
    gated = _qt_policy_for_synthetic_finite_bond_ledger(
        ledger,
        worst_gate=0.2,
        total_gate=0.2,
    )
    half_gated = _qt_policy_for_synthetic_finite_bond_ledger(
        ledger,
        worst_gate=0.2,
        total_gate=None,
    )

    assert ungated["accepted_for_restricted_execution"] is False
    assert "finite_bond_candidate_gate_not_evaluated" in ungated[
        "production_blockers"
    ]
    assert half_gated["accepted_for_restricted_execution"] is False
    assert "finite_bond_candidate_gate_incomplete" in half_gated[
        "production_blockers"
    ]
    assert gated["accepted_for_restricted_execution"] is True
    assert gated["mps_truncation"]["accepted_as_finite_bond_candidate"] is True
    assert gated["accepted_for_production_scalable_backend"] is False


def test_observed_lossless_finite_bond_run_needs_no_discard_gate() -> None:
    policy = _qt_policy_for_synthetic_finite_bond_ledger(
        _synthetic_complete_finite_bond_ledger(discarded=0.0),
        worst_gate=None,
        total_gate=None,
    )

    assert policy["accepted_for_restricted_execution"] is True
    assert policy["mps_truncation"][
        "observed_lossless_finite_bond_execution"
    ] is True


def test_mcwf_finite_bond_acceptance_consumes_the_authenticated_ledger() -> None:
    from error_coupling_simulator.frontend.axis1_mcwf_dense_certification import (
        restricted_acceptance_policy,
    )

    ledger = _synthetic_complete_finite_bond_ledger(discarded=0.1)
    common = {
        "execution": {
            "total_probability_residual": 0.0,
            "trajectory_sampling": {
                "mode": "sampled_fixed_microstep_mcwf_trajectories"
            },
            "mps_truncation_ledger": ledger,
        },
        "certification": {
            "executed": True,
            "passed": True,
            "passed_gross": True,
            "comparison_outcome_is_metric": True,
        },
        "program": {"requires_scalable_backend": False},
        "rng_seed": 17,
        "trajectory_count": 2,
    }
    ungated = restricted_acceptance_policy(**common)
    gated = restricted_acceptance_policy(
        **common,
        worst_cut_discarded_weight_gate=0.2,
        total_discarded_weight_gate=0.2,
    )

    assert ungated["accepted_for_restricted_execution"] is False
    assert "finite_bond_candidate_gate_not_evaluated" in ungated[
        "production_blockers"
    ]
    assert gated["accepted_for_restricted_execution"] is True
    assert gated["mps_truncation"]["accepted_as_finite_bond_candidate"] is True
    assert gated["accepted_for_production_scalable_backend"] is False


def test_sampled_truncation_aggregation_authenticates_strang_passes_separately() -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_ledger,
    )

    events = [
        _synthetic_truncation_event(
            0.1,
            trajectory_index=trajectory_index,
            hamiltonian_pass_index=pass_index,
        )
        for pass_index in (0, 1)
        for trajectory_index in (0, 1)
    ]
    ledger = _truncation_ledger(
        max_bond=1,
        num_sites=5,
        max_observed_bond=1,
        truncation_events=events,
        aggregation_mode="sampled_trajectory_mean",
        trajectory_count=2,
        expected_gate_occurrences=[
            _expected_gate_occurrence(
                _synthetic_truncation_event(
                    0.0,
                    trajectory_index=0,
                    hamiltonian_pass_index=pass_index,
                )
            )
            for pass_index in (0, 1)
        ],
    )

    assert ledger["discarded_weight_sum"] == pytest.approx(0.2)
    assert ledger["aggregation"]["context_complete"] is True
    assert ledger["aggregation"]["observed_gate_occurrence_count"] == 2
    assert ledger["aggregation"]["complete_gate_occurrence_count"] == 2


def test_sampled_truncation_aggregation_fails_closed_on_one_of_100_coverage() -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_gate_result,
        _truncation_ledger,
    )

    event = _synthetic_truncation_event(0.2, trajectory_index=0)
    ledger = _truncation_ledger(
        max_bond=1,
        num_sites=5,
        max_observed_bond=1,
        truncation_events=[event],
        aggregation_mode="sampled_trajectory_mean",
        trajectory_count=100,
        expected_gate_occurrences=[_expected_gate_occurrence(event)],
    )

    assert ledger["discarded_weight_sum"] == pytest.approx(0.002)
    assert ledger["aggregation"]["context_complete"] is False
    assert ledger["discarded_weight_ledger_complete"] is False
    gate = _truncation_gate_result(
        ledger,
        worst_cut_discarded_weight_gate=1.0,
        total_discarded_weight_gate=1.0,
    )
    assert gate["passed"] is False
    assert "incomplete_truncation_aggregation_context" in gate["violations"]


def test_exact_truncation_aggregation_fails_closed_on_point_zero_one_mass() -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_gate_result,
        _truncation_ledger,
    )

    event = _synthetic_truncation_event(
        0.2,
        incoming_branch_weight=0.01,
        branch_ordinal=0,
    )
    ledger = _truncation_ledger(
        max_bond=1,
        num_sites=5,
        max_observed_bond=1,
        truncation_events=[event],
        aggregation_mode="exact_branch_probability_weighted",
        trajectory_count=None,
        expected_gate_occurrences=[_expected_gate_occurrence(event)],
    )

    assert ledger["discarded_weight_sum"] == pytest.approx(0.002)
    assert ledger["aggregation"]["context_complete"] is False
    assert ledger["discarded_weight_ledger_complete"] is False
    gate = _truncation_gate_result(
        ledger,
        worst_cut_discarded_weight_gate=1.0,
        total_discarded_weight_gate=1.0,
    )
    assert gate["passed"] is False
    assert "incomplete_truncation_aggregation_context" in gate["violations"]


def test_truncation_aggregation_fails_closed_without_occurrence_pass_identity() -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_ledger,
    )

    event = _synthetic_truncation_event(0.2, trajectory_index=0)
    expected = _expected_gate_occurrence(event)
    event.pop("hamiltonian_pass_index")
    ledger = _truncation_ledger(
        max_bond=1,
        num_sites=5,
        max_observed_bond=1,
        truncation_events=[event],
        aggregation_mode="sampled_trajectory_mean",
        trajectory_count=1,
        expected_gate_occurrences=[expected],
    )

    assert ledger["aggregation"]["context_complete"] is False
    assert ledger["discarded_weight_ledger_complete"] is False
    assert ledger["aggregation"]["coverage_failures"][0]["reason"] == (
        "gate_occurrence_identity_incomplete"
    )


@pytest.mark.parametrize(
    ("mode", "trajectory_count", "event"),
    [
        (
            "sampled_trajectory_mean",
            2,
            _synthetic_truncation_event(0.1, trajectory_index=None),
        ),
        (
            "sampled_trajectory_mean",
            2,
            _synthetic_truncation_event(0.1, trajectory_index=2),
        ),
        (
            "exact_branch_probability_weighted",
            None,
            _synthetic_truncation_event(
                0.1, incoming_branch_weight=float("nan"), branch_ordinal=0
            ),
        ),
    ],
)
def test_truncation_aggregation_rejects_incomplete_or_nonfinite_context(
    mode: str,
    trajectory_count: int | None,
    event: dict[str, Any],
) -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_ledger,
    )

    with pytest.raises((TypeError, ValueError), match="aggregation|trajectory|branch"):
        _truncation_ledger(
            max_bond=1,
            num_sites=5,
            max_observed_bond=1,
            truncation_events=[event],
            aggregation_mode=mode,
            trajectory_count=trajectory_count,
            expected_gate_occurrences=[
                _expected_gate_occurrence(
                    _synthetic_truncation_event(0.0, trajectory_index=0)
                )
            ],
        )


@pytest.mark.parametrize(
    ("mode", "trajectory_count"),
    [
        ("sampled_trajectory_mean", 3),
        ("exact_branch_probability_weighted", None),
    ],
)
def test_zero_two_site_occurrence_inventory_is_vacuously_complete(
    mode: str,
    trajectory_count: int | None,
) -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_ledger,
    )

    ledger = _truncation_ledger(
        max_bond=1,
        num_sites=5,
        max_observed_bond=1,
        truncation_events=[],
        aggregation_mode=mode,
        trajectory_count=trajectory_count,
        expected_gate_occurrences=[],
    )

    assert ledger["discarded_weight_ledger_complete"] is True
    assert ledger["discarded_weight_sum"] == 0.0
    assert ledger["aggregation"]["context_complete"] is True
    assert ledger["aggregation"]["expected_gate_occurrence_count"] == 0
    assert ledger["aggregation"]["observed_gate_occurrence_count"] == 0
    assert ledger["aggregation"]["coverage_failures"] == []
    if mode == "exact_branch_probability_weighted":
        acceptance = _qt_policy_for_synthetic_finite_bond_ledger(
            ledger,
            worst_gate=None,
            total_gate=None,
        )
    else:
        from error_coupling_simulator.frontend.axis1_mcwf_dense_certification import (
            restricted_acceptance_policy,
        )

        acceptance = restricted_acceptance_policy(
            execution={
                "total_probability_residual": 0.0,
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories"
                },
                "mps_truncation_ledger": ledger,
            },
            certification={
                "executed": True,
                "passed": True,
                "passed_gross": True,
                "comparison_outcome_is_metric": True,
            },
            program={"requires_scalable_backend": False},
            rng_seed=17,
            trajectory_count=3,
        )
    assert acceptance["accepted_for_restricted_execution"] is True
    assert acceptance["mps_truncation"][
        "observed_lossless_finite_bond_execution"
    ] is True


@pytest.mark.parametrize(
    ("mode", "trajectory_count"),
    [
        ("sampled_trajectory_mean", 2),
        ("exact_branch_probability_weighted", None),
    ],
)
def test_truncation_aggregation_fails_closed_when_whole_strang_pass_is_missing(
    mode: str,
    trajectory_count: int | None,
) -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_gate_result,
        _truncation_ledger,
    )

    pass_zero = _synthetic_truncation_event(
        0.1,
        trajectory_index=0 if trajectory_count is not None else None,
        incoming_branch_weight=None if trajectory_count is not None else 1.0,
        branch_ordinal=None if trajectory_count is not None else 0,
        hamiltonian_pass_index=0,
    )
    events = (
        [
            pass_zero,
            _synthetic_truncation_event(
                0.2,
                trajectory_index=1,
                hamiltonian_pass_index=0,
            ),
        ]
        if trajectory_count is not None
        else [pass_zero]
    )
    expected = [
        _expected_gate_occurrence(
            _synthetic_truncation_event(
                0.0,
                hamiltonian_pass_index=pass_index,
            )
        )
        for pass_index in (0, 1)
    ]
    ledger = _truncation_ledger(
        max_bond=1,
        num_sites=5,
        max_observed_bond=1,
        truncation_events=events,
        aggregation_mode=mode,
        trajectory_count=trajectory_count,
        expected_gate_occurrences=expected,
    )

    assert ledger["discarded_weight_ledger_complete"] is False
    assert ledger["aggregation"]["expected_gate_occurrence_count"] == 2
    assert ledger["aggregation"]["observed_gate_occurrence_count"] == 1
    assert any(
        failure["reason"] == "expected_gate_occurrence_missing"
        and failure["hamiltonian_pass_index"] == 1
        for failure in ledger["aggregation"]["coverage_failures"]
    )
    gate = _truncation_gate_result(
        ledger,
        worst_cut_discarded_weight_gate=1.0,
        total_discarded_weight_gate=1.0,
    )
    assert gate["passed"] is False
    assert "incomplete_truncation_aggregation_context" in gate["violations"]
    if mode == "exact_branch_probability_weighted":
        acceptance = _qt_policy_for_synthetic_finite_bond_ledger(
            ledger,
            worst_gate=1.0,
            total_gate=1.0,
        )
    else:
        from error_coupling_simulator.frontend.axis1_mcwf_dense_certification import (
            restricted_acceptance_policy,
        )

        acceptance = restricted_acceptance_policy(
            execution={
                "total_probability_residual": 0.0,
                "trajectory_sampling": {
                    "mode": "sampled_fixed_microstep_mcwf_trajectories"
                },
                "mps_truncation_ledger": ledger,
            },
            certification={
                "executed": True,
                "passed": True,
                "passed_gross": True,
                "comparison_outcome_is_metric": True,
            },
            program={"requires_scalable_backend": False},
            rng_seed=17,
            trajectory_count=2,
            worst_cut_discarded_weight_gate=1.0,
            total_discarded_weight_gate=1.0,
        )
    assert acceptance["accepted_for_restricted_execution"] is False
    assert "incomplete_mps_truncation_aggregation_context" in acceptance[
        "production_blockers"
    ]


def test_occurrence_inventory_compares_identity_not_only_count() -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _truncation_ledger,
    )

    observed = [
        _synthetic_truncation_event(
            0.1,
            trajectory_index=trajectory_index,
            hamiltonian_pass_index=1,
        )
        for trajectory_index in (0, 1)
    ]
    expected = [
        _expected_gate_occurrence(
            _synthetic_truncation_event(
                0.0,
                hamiltonian_pass_index=0,
            )
        )
    ]
    ledger = _truncation_ledger(
        max_bond=1,
        num_sites=5,
        max_observed_bond=1,
        truncation_events=observed,
        aggregation_mode="sampled_trajectory_mean",
        trajectory_count=2,
        expected_gate_occurrences=expected,
    )

    assert ledger["aggregation"]["expected_gate_occurrence_count"] == 1
    assert ledger["aggregation"]["observed_gate_occurrence_count"] == 1
    assert ledger["discarded_weight_ledger_complete"] is False
    assert {
        failure["reason"]
        for failure in ledger["aggregation"]["coverage_failures"]
    } == {
        "expected_gate_occurrence_missing",
        "unexpected_gate_occurrence_observed",
    }


def test_qt_expected_occurrence_inventory_covers_terms_microsteps_and_strang_passes() -> None:
    from error_coupling_simulator.frontend.axis1_qt_mps_execution import (
        _qt_expected_actual_split_occurrences,
    )

    occurrences = _qt_expected_actual_split_occurrences(
        {
            "program": {
                "substeps": [
                    {
                        "substep_id": "s0",
                        "substep_kind": "idle",
                        "dt_ns": 2.0,
                        "terms": [
                            {
                                "kind": "hamiltonian",
                                "operator_family": "CTRL_X",
                                "support": [2],
                            },
                            {
                                "kind": "hamiltonian",
                                "operator_family": "ZZ",
                                "support": [0, 4],
                            },
                            {
                                "kind": "collapse",
                                "operator_family": "T1",
                                "support": [1],
                            },
                        ],
                    }
                ]
            }
        },
        microstep_count=2,
        finite_step_order="strang_second_order",
    )

    assert len(occurrences) == 4
    assert {row["term_index"] for row in occurrences} == {1}
    assert {tuple(row["support"]) for row in occurrences} == {(0, 4)}
    assert {row["microstep_index"] for row in occurrences} == {0, 1}
    assert {row["hamiltonian_pass_index"] for row in occurrences} == {0, 1}
    assert {row["dt_ns_effective"] for row in occurrences} == {0.5}


def test_mcwf_expected_occurrence_inventory_matches_connected_group_identity() -> None:
    from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (
        _mcwf_expected_actual_split_occurrences,
    )

    occurrences = _mcwf_expected_actual_split_occurrences(
        {
            "program": {
                "substeps": [
                    {
                        "substep_id": "s0",
                        "substep_kind": "idle",
                        "dt_ns": 2.0,
                        "terms": [
                            {
                                "kind": "hamiltonian",
                                "operator_family": "COH_RX",
                                "support": [0],
                            },
                            {
                                "kind": "hamiltonian",
                                "operator_family": "ZZ",
                                "support": [0, 4],
                            },
                            {
                                "kind": "hamiltonian",
                                "operator_family": "COH_RY",
                                "support": [2],
                            },
                        ],
                    }
                ]
            }
        },
        microstep_count=2,
        finite_step_order="strang_second_order",
    )

    assert len(occurrences) == 4
    assert {row["term_index"] for row in occurrences} == {0}
    assert {row["operator_family"] for row in occurrences} == {
        "H_CLUSTER[COH_RX+ZZ]"
    }
    assert {tuple(row["support"]) for row in occurrences} == {(0, 4)}
    assert {row["microstep_index"] for row in occurrences} == {0, 1}
    assert {row["hamiltonian_pass_index"] for row in occurrences} == {0, 1}
    assert {row["dt_ns_effective"] for row in occurrences} == {0.5}


def test_mcwf_production_seam_uses_actual_split_only_for_two_site_unitary() -> None:
    from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (
        _apply_mps_gate,
    )

    mps = _five_qubit_product_mps(plus_site=0)
    events: list[dict[str, Any]] = []
    _apply_mps_gate(
        mps,
        _torch_gate(_cnot()),
        support=(0, 4),
        substep={"substep_id": "s0", "substep_kind": "two_qubit_gate"},
        term={"operator_family": "CTRL_CX"},
        term_index=0,
        branch_bits=(),
        device="cpu",
        max_bond=1,
        dt_ns=1.0,
        microstep_index=0,
        microstep_count=1,
        truncation_events=events,
        track_actual_splits=True,
        trajectory_index=4,
    )

    assert len(events) == 1
    assert events[0]["split_count"] == 7
    assert events[0]["trajectory_index"] == 4
    assert events[0]["hamiltonian_pass_index"] == 0
    assert events[0]["physical_branch_probability"] is None
    assert _norm_sq(mps) == pytest.approx(1.0, abs=1.0e-14)

    from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (
        _sample_joint_jump_or_nojump,
    )
    import torch

    generator = torch.Generator(device="cpu")
    generator.manual_seed(0)
    _selected, branch = _sample_joint_jump_or_nojump(
        mps,
        {
            "terms": [
                {
                    "kind": "collapse",
                    "operator_family": "T2",
                    "support": [0],
                    "coefficient": 0.1,
                }
            ]
        },
        dt_ns=1.0e-3,
        device="cpu",
        generator=generator,
        local_dims=(2, 2, 2, 2, 2),
    )
    assert branch["probability_mass"] == pytest.approx(1.0, abs=1.0e-8)
    assert branch["probability_mass_residual"] <= 1.0e-8


def test_mcwf_two_site_branch_operators_disable_all_quimb_cutoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No-jump/jump norm is probability mass, so even default SVD cutoff is forbidden."""
    import torch

    from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (
        _sample_joint_jump_or_nojump,
    )

    mps = _five_qubit_product_mps(plus_site=0)
    mps_type = type(mps)
    original_gate = mps_type.gate_
    two_site_calls: list[dict[str, Any]] = []

    def _audited_gate(self, *args, **kwargs):
        where = kwargs.get("where")
        if isinstance(where, tuple) and len(where) == 2:
            two_site_calls.append(dict(kwargs))
        return original_gate(self, *args, **kwargs)

    monkeypatch.setattr(mps_type, "gate_", _audited_gate)
    generator = torch.Generator(device="cpu")
    generator.manual_seed(17)
    _sample_joint_jump_or_nojump(
        mps,
        {
            "terms": [
                {
                    "kind": "collapse",
                    "operator_family": "CORR_RELAX",
                    "support": [0, 4],
                    "coefficient": 0.1,
                }
            ]
        },
        dt_ns=1.0e-3,
        device="cpu",
        generator=generator,
        local_dims=(2, 2, 2, 2, 2),
    )

    assert len(two_site_calls) == 2  # no-jump and jump candidates
    assert all(call.get("max_bond") is None for call in two_site_calls)
    assert all(call.get("cutoff") == 0.0 for call in two_site_calls)


def test_mcwf_two_site_branch_probability_matches_dense_uncut_oracle() -> None:
    import torch

    from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (
        _joint_collapse_operator,
        _joint_nojump_first_order_kraus,
        _sample_joint_jump_or_nojump,
    )

    mps = _five_qubit_product_mps(plus_site=0)
    initial = _as_dense(mps)
    term = {
        "kind": "collapse",
        "operator_family": "CORR_RELAX",
        "support": [0, 4],
        "coefficient": 0.1,
    }
    dt = 1.0e-3
    dims = (2, 2, 2, 2, 2)
    k0 = _joint_nojump_first_order_kraus(
        term, dt, (0, 4), local_dims=dims, device="cpu"
    )
    jump = math.sqrt(dt) * _joint_collapse_operator(
        term, (0, 4), local_dims=dims, device="cpu"
    )
    dense_nojump = _apply_two_site_dense(
        initial, k0.detach().cpu().numpy(), support=(0, 4)
    )
    dense_jump = _apply_two_site_dense(
        initial, jump.detach().cpu().numpy(), support=(0, 4)
    )
    dense_total = float(
        np.vdot(dense_nojump, dense_nojump).real
        + np.vdot(dense_jump, dense_jump).real
    )
    generator = torch.Generator(device="cpu")
    generator.manual_seed(23)
    _selected, branch = _sample_joint_jump_or_nojump(
        mps,
        {"terms": [term]},
        dt_ns=dt,
        device="cpu",
        generator=generator,
        local_dims=dims,
    )

    assert branch["probability_mass"] == pytest.approx(dense_total, abs=1.0e-14)


def test_mcwf_capped_multisite_cluster_fails_before_state_or_ledger_mutation() -> None:
    import torch

    from error_coupling_simulator.frontend.axis1_mcwf_mps_execution import (
        _apply_mps_gate,
    )

    mps = _five_qubit_product_mps(plus_site=0)
    before = _mps_tensor_fingerprint(mps)
    events: list[dict[str, Any]] = []

    with pytest.raises(
        ValueError,
        match="actual_split_ledger_not_implemented_for_multisite_cluster",
    ):
        _apply_mps_gate(
            mps,
            torch.eye(8, dtype=torch.complex128),
            support=(0, 1, 2),
            substep={"substep_id": "s0", "substep_kind": "idle"},
            term={"operator_family": "CTRL_CLUSTER"},
            term_index=0,
            branch_bits=(),
            device="cpu",
            max_bond=2,
            dt_ns=1.0,
            microstep_index=0,
            microstep_count=1,
            truncation_events=events,
            track_actual_splits=True,
        )

    assert events == []
    assert _mps_tensor_fingerprint(mps) == before


def test_mcwf_capped_multisite_cluster_fails_before_dense_gate_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unsupported connected supports are rejected before matrix_exp or allocation."""
    import error_coupling_simulator.frontend.axis1_mcwf_mps_execution as execution

    mps = _five_qubit_product_mps(plus_site=0)
    before = _mps_tensor_fingerprint(mps)
    events: list[dict[str, Any]] = []
    construction_calls: list[str] = []

    def _must_not_construct(*_args, **_kwargs):
        construction_calls.append("called")
        raise AssertionError("dense Hamiltonian gate construction was reached")

    monkeypatch.setattr(execution, "_hamiltonian_group_gates", _must_not_construct)
    substep = {
        "substep_id": "connected_three_site_cluster",
        "terms": [
            {"kind": "hamiltonian", "support": [0, 1]},
            {"kind": "hamiltonian", "support": [1, 2]},
        ],
    }

    with pytest.raises(
        ValueError,
        match="actual_split_ledger_not_implemented_for_multisite_cluster",
    ):
        execution._apply_hamiltonian_terms_multilevel(
            mps,
            substep,
            device="cpu",
            max_bond=2,
            branch_bits=(),
            truncation_events=events,
            dt_ns=1.0,
            microstep_index=0,
            microstep_count=1,
            local_dims=(2, 2, 2, 2, 2),
        )

    assert construction_calls == []
    assert events == []
    assert _mps_tensor_fingerprint(mps) == before
