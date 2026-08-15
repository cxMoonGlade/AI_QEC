from __future__ import annotations

"""Focused contracts for law-neutral restricted-MPS truncation mechanics."""

import inspect
import math

import pytest


def _event(
    discarded: float,
    *,
    trajectory_index: int | None = None,
    incoming_branch_weight: float | None = None,
    branch_ordinal: int | None = None,
) -> dict[str, object]:
    raw_discarded = 2.0 * discarded
    input_norm_sq = 4.0
    raw_output_norm_sq = input_norm_sq - raw_discarded
    observed_loss = max(0.0, input_norm_sq - raw_output_norm_sq)
    return {
        "actual_discarded_weight_fraction_sum": discarded,
        "actual_discarded_weight_raw_sum": raw_discarded,
        "unitary_truncation_mass_loss": observed_loss,
        "split_count": 1,
        "split_records": [
            {
                "sequence_index": 0,
                "path_role": "two_site_operator_split",
                "split_sites": [0, 1],
                "gate_leg_sites": [0, 1],
                "requested_method": "svd",
                "requested_absorb": "right",
                "requested_max_bond": 1,
                "requested_cutoff": 0.0,
                "requested_cutoff_mode": "rsum2",
                "requested_renorm": None,
                "pre_split_total_weight": 2.0,
                "actual_kept_bond_dimension": 1,
                "actual_discarded_weight_raw": raw_discarded,
                "actual_discarded_weight_fraction_of_pre_split": discarded,
                "not_a_global_error_bound": True,
            }
        ],
        "substep_id": "s0",
        "substep_kind": "idle",
        "term_index": 0,
        "operator_family": "ZZ",
        "support": [0, 1],
        "gate_leg_sites": [0, 1],
        "max_bond": 1,
        "quimb_version": "1.14.0",
        "input_norm_sq": input_norm_sq,
        "raw_output_norm_sq": raw_output_norm_sq,
        "restored_output_norm_sq": input_norm_sq,
        "deterministic_norm_restore_factor": math.sqrt(
            input_norm_sq / raw_output_norm_sq
        ),
        "physical_branch_probability": None,
        "worst_actual_discarded_weight_fraction": discarded,
        "ledger_semantics": "per_actual_svd_split_heuristic_not_global_bound",
        "not_a_global_error_bound": True,
        "microstep_index": 0,
        "microstep_count": 1,
        "hamiltonian_pass_index": 0,
        "dt_ns_effective": 1.0,
        "trajectory_index": trajectory_index,
        "incoming_branch_weight": incoming_branch_weight,
        "branch_ordinal": branch_ordinal,
        "branch_record_prefix": [],
        "array_backend": "torch_cuda_complex128",
        "epistemic_class": "c",
        "ledger_method": "quimb_actual_svd_split_per_two_site_unitary_gate",
        "discarded_weight_sum": discarded,
        "worst_cut_discarded_weight": discarded,
        "discarded_weight_units": "fraction_of_pre_split_weight",
        "compatibility_aliases": {
            "discarded_weight_sum": "actual_discarded_weight_fraction_sum",
            "worst_cut_discarded_weight": (
                "worst_actual_discarded_weight_fraction"
            ),
        },
        "n_truncated_cuts": int(raw_discarded > 0.0),
    }


def _occurrence(event: dict[str, object]) -> dict[str, object]:
    fields = (
        "substep_id",
        "term_index",
        "operator_family",
        "support",
        "microstep_index",
        "microstep_count",
        "hamiltonian_pass_index",
        "dt_ns_effective",
    )
    return {field: event[field] for field in fields}


def _nonlocal_event(
    *,
    reverse_support: bool = False,
    trajectory_index: int | None = 0,
    incoming_branch_weight: float | None = None,
    branch_ordinal: int | None = None,
) -> dict[str, object]:
    """Construct a canonical distance-three event with all five actual splits."""

    event = _event(
        0.0,
        trajectory_index=trajectory_index,
        incoming_branch_weight=incoming_branch_weight,
        branch_ordinal=branch_ordinal,
    )
    support = [3, 0] if reverse_support else [0, 3]
    gate_leg_sites = [1, 0] if reverse_support else [0, 1]
    roles = [
        "forward_swap_split",
        "forward_swap_split",
        "two_site_operator_split",
        "reverse_swap_split",
        "reverse_swap_split",
    ]
    split_sites = [[2, 3], [1, 2], [0, 1], [1, 2], [2, 3]]
    absorbs = [
        "left",
        "left",
        "left" if reverse_support else "right",
        "right",
        "right",
    ]
    raw_weights = [0.1, 0.2, 0.3, 0.4, 0.5]
    pre_split_weight = 2.0
    records = [
        {
            "sequence_index": index,
            "path_role": role,
            "split_sites": sites,
            "gate_leg_sites": (
                gate_leg_sites if role == "two_site_operator_split" else None
            ),
            "requested_method": "svd",
            "requested_absorb": absorb,
            "requested_max_bond": 2,
            "requested_cutoff": 0.0,
            "requested_cutoff_mode": "rsum2",
            "requested_renorm": None,
            "pre_split_total_weight": pre_split_weight,
            "actual_kept_bond_dimension": 2,
            "actual_discarded_weight_raw": raw,
            "actual_discarded_weight_fraction_of_pre_split": (
                raw / pre_split_weight
            ),
            "not_a_global_error_bound": True,
        }
        for index, (role, sites, absorb, raw) in enumerate(
            zip(roles, split_sites, absorbs, raw_weights, strict=True)
        )
    ]
    raw_sum = float(sum(raw_weights))
    fraction_sum = float(
        sum(
            record["actual_discarded_weight_fraction_of_pre_split"]
            for record in records
        )
    )
    worst_fraction = float(
        max(
            record["actual_discarded_weight_fraction_of_pre_split"]
            for record in records
        )
    )
    input_norm_sq = 4.0
    raw_output_norm_sq = input_norm_sq - raw_sum
    event.update(
        {
            "support": support,
            "gate_leg_sites": gate_leg_sites,
            "max_bond": 2,
            "split_count": len(records),
            "split_records": records,
            "input_norm_sq": input_norm_sq,
            "raw_output_norm_sq": raw_output_norm_sq,
            "restored_output_norm_sq": input_norm_sq,
            "deterministic_norm_restore_factor": math.sqrt(
                input_norm_sq / raw_output_norm_sq
            ),
            "unitary_truncation_mass_loss": raw_sum,
            "actual_discarded_weight_raw_sum": raw_sum,
            "actual_discarded_weight_fraction_sum": fraction_sum,
            "worst_actual_discarded_weight_fraction": worst_fraction,
            "discarded_weight_sum": fraction_sum,
            "worst_cut_discarded_weight": worst_fraction,
            "n_truncated_cuts": len(records),
        }
    )
    return event


def test_public_truncation_interfaces_choose_law_without_mode_switch() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    for function in (
        aggregate_exact_branch_truncation_events,
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    ):
        assert "mode" not in inspect.signature(function).parameters


def test_sampled_aggregation_serializes_complete_machine_contract() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
    )

    first = [
        _event(value, trajectory_index=index)
        for index, value in enumerate((0.125, 0.25, 0.375))
    ]
    second = [
        _event(value, trajectory_index=index)
        for index, value in enumerate((0.5, 0.625, 0.75))
    ]
    for event in second:
        event.update(
            {
                "substep_id": "s1",
                "term_index": 1,
                "operator_family": "XX",
                "support": [1, 2],
                "gate_leg_sites": [1, 2],
                "microstep_index": 1,
                "microstep_count": 2,
                "hamiltonian_pass_index": 1,
                "dt_ns_effective": 2.0,
            }
        )
    expected_second = _occurrence(second[0])
    expected_first = _occurrence(first[0])

    result = aggregate_sampled_truncation_events(
        [second[2], first[0], second[0], first[2], first[1], second[1]],
        trajectory_count=3,
        expected_gate_occurrences=[expected_second, expected_first],
    )

    assert result == {
        "fraction": 0.875,
        "raw": 1.75,
        "norm_loss": 1.75,
        "metadata": {
            "mode": "sampled_trajectory_mean",
            "weight_source": "uniform_over_explicit_trajectory_count",
            "trajectory_count": 3,
            "observed_context_count": 3,
            "expected_gate_occurrence_count": 2,
            "expected_gate_occurrences": [expected_second, expected_first],
            "observed_gate_occurrence_count": 2,
            "complete_gate_occurrence_count": 2,
            "max_observed_sampled_path_fraction_sum": 1.125,
            "gate_occurrence_identity_fields": [
                "substep_id",
                "term_index",
                "operator_family",
                "support",
                "microstep_index",
                "microstep_count",
                "hamiltonian_pass_index",
                "dt_ns_effective",
            ],
            "coverage_policy": (
                "observed_gate_occurrence_identities_exactly_match_precomputed_"
                "inventory_and_every_gate_occurrence_has_exactly_one_event_per_"
                "declared_trajectory"
            ),
            "coverage_failures": [],
            "context_complete": True,
            "not_a_global_error_bound": True,
        },
    }


def test_exact_aggregation_serializes_complete_machine_contract() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
    )

    events = [
        _event(
            discarded,
            trajectory_index=None,
            incoming_branch_weight=weight,
            branch_ordinal=ordinal,
        )
        for ordinal, (discarded, weight) in enumerate(
            ((0.125, 0.125), (0.25, 0.25), (0.5, 0.625))
        )
    ]
    events[0]["branch_record_prefix"] = []
    events[1]["branch_record_prefix"] = [0]
    events[2]["branch_record_prefix"] = [1, 0]
    occurrence = _occurrence(events[0])

    result = aggregate_exact_branch_truncation_events(
        [events[2], events[0], events[1]],
        expected_gate_occurrences=[occurrence],
    )

    assert result == {
        "fraction": 0.390625,
        "raw": 0.78125,
        "norm_loss": 0.78125,
        "metadata": {
            "mode": "exact_branch_probability_weighted",
            "weight_source": "incoming_branch_weight",
            "trajectory_count": None,
            "observed_context_count": 3,
            "expected_gate_occurrence_count": 1,
            "expected_gate_occurrences": [occurrence],
            "observed_gate_occurrence_count": 1,
            "complete_gate_occurrence_count": 1,
            "max_observed_sampled_path_fraction_sum": None,
            "gate_occurrence_identity_fields": [
                "substep_id",
                "term_index",
                "operator_family",
                "support",
                "microstep_index",
                "microstep_count",
                "hamiltonian_pass_index",
                "dt_ns_effective",
            ],
            "coverage_policy": (
                "observed_gate_occurrence_identities_exactly_match_precomputed_"
                "inventory_and_every_gate_occurrence_has_unique_contiguous_"
                "branch_ordinals_and_unit_incoming_branch_mass"
            ),
            "coverage_failures": [],
            "context_complete": True,
            "not_a_global_error_bound": True,
        },
    }


def test_exact_aggregation_authenticates_every_complete_occurrence() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
    )

    first = _event(
        0.125,
        trajectory_index=None,
        incoming_branch_weight=1.0,
        branch_ordinal=0,
    )
    second = _event(
        0.25,
        trajectory_index=None,
        incoming_branch_weight=1.0,
        branch_ordinal=0,
    )
    second.update(
        {
            "substep_id": "s1",
            "term_index": 1,
            "operator_family": "XX",
            "support": [1, 2],
            "gate_leg_sites": [1, 2],
            "microstep_index": 1,
            "microstep_count": 2,
            "hamiltonian_pass_index": 1,
            "dt_ns_effective": 2.0,
        }
    )

    result = aggregate_exact_branch_truncation_events(
        [first, second],
        expected_gate_occurrences=[_occurrence(first), _occurrence(second)],
    )

    assert result["metadata"]["observed_gate_occurrence_count"] == 2
    assert result["metadata"]["complete_gate_occurrence_count"] == 2
    assert result["metadata"]["coverage_failures"] == []
    assert result["metadata"]["context_complete"] is True


def test_sampled_aggregation_reports_missing_and_duplicate_paths() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
    )

    event = _event(0.125, trajectory_index=0)
    occurrence = _occurrence(event)
    result = aggregate_sampled_truncation_events(
        [event, _event(0.125, trajectory_index=0)],
        trajectory_count=2,
        expected_gate_occurrences=[occurrence],
    )

    assert result["fraction"] == 0.125
    assert result["raw"] == 0.25
    assert result["norm_loss"] == 0.25
    assert result["metadata"]["observed_context_count"] == 1
    assert result["metadata"]["complete_gate_occurrence_count"] == 0
    assert result["metadata"]["max_observed_sampled_path_fraction_sum"] == 0.25
    assert result["metadata"]["coverage_failures"] == [
        {
            **occurrence,
            "reason": "sampled_trajectory_coverage_incomplete",
            "observed_trajectory_count": 1,
            "missing_trajectory_count": 1,
            "duplicate_event_count": 1,
        }
    ]
    assert result["metadata"]["context_complete"] is False


def test_exact_aggregation_reports_ordinal_and_mass_failures_together() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
    )

    first = _event(
        0.125,
        trajectory_index=None,
        incoming_branch_weight=0.25,
        branch_ordinal=0,
    )
    second = _event(
        0.5,
        trajectory_index=None,
        incoming_branch_weight=0.5,
        branch_ordinal=2,
    )
    occurrence = _occurrence(first)
    result = aggregate_exact_branch_truncation_events(
        [first, second],
        expected_gate_occurrences=[occurrence],
    )

    assert result["fraction"] == 0.28125
    assert result["raw"] == 0.5625
    assert result["norm_loss"] == 0.5625
    assert result["metadata"]["complete_gate_occurrence_count"] == 0
    assert result["metadata"]["coverage_failures"] == [
        {
            **occurrence,
            "reason": (
                "exact_branch_ordinal_coverage_incomplete+"
                "exact_branch_mass_not_unity"
            ),
            "observed_branch_count": 2,
            "unique_branch_ordinal_count": 2,
            "incoming_branch_weight_sum": 0.75,
            "unit_mass_tolerance": 1e-12,
        }
    ]
    assert result["metadata"]["context_complete"] is False


def test_aggregation_distinguishes_missing_and_unexpected_occurrences() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
    )

    observed = _event(0.125, trajectory_index=0)
    expected = _event(0.125, trajectory_index=0)
    expected.update(
        {
            "substep_id": "s1",
            "term_index": 1,
            "operator_family": "XX",
            "support": [1, 2],
            "microstep_index": 1,
            "microstep_count": 2,
            "hamiltonian_pass_index": 1,
            "dt_ns_effective": 2.0,
        }
    )
    result = aggregate_sampled_truncation_events(
        [observed],
        trajectory_count=1,
        expected_gate_occurrences=[_occurrence(expected)],
    )

    assert result["metadata"]["observed_gate_occurrence_count"] == 1
    assert result["metadata"]["complete_gate_occurrence_count"] == 0
    failures = result["metadata"]["coverage_failures"]
    assert [failure["reason"] for failure in failures] == [
        "expected_gate_occurrence_missing",
        "unexpected_gate_occurrence_observed",
    ]
    assert failures[0] | {"reason": "ignored"} == (
        _occurrence(expected) | {"reason": "ignored"}
    )
    assert failures[1] | {"reason": "ignored"} == (
        _occurrence(observed) | {"reason": "ignored"}
    )
    assert result["metadata"]["context_complete"] is False


@pytest.mark.parametrize(
    "corruption",
    [
        "duplicate_occurrence",
        "missing_pass_identity",
        "duplicate_support_site",
        "microstep_outside_count",
        "negative_effective_duration",
        "boolean_term_index",
    ],
)
def test_aggregation_rejects_corrupt_expected_occurrence_inventory(
    corruption: str,
) -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
    )

    event = _event(0.125, trajectory_index=0)
    occurrence = _occurrence(event)
    inventory = [occurrence]
    if corruption == "duplicate_occurrence":
        inventory.append(dict(occurrence))
    elif corruption == "missing_pass_identity":
        occurrence["hamiltonian_pass_index"] = None
    elif corruption == "duplicate_support_site":
        occurrence["support"] = [0, 0]
    elif corruption == "microstep_outside_count":
        occurrence["microstep_index"] = occurrence["microstep_count"]
    elif corruption == "negative_effective_duration":
        occurrence["dt_ns_effective"] = -1.0
    else:
        occurrence["term_index"] = True

    with pytest.raises((TypeError, ValueError)):
        aggregate_sampled_truncation_events(
            [event],
            trajectory_count=1,
            expected_gate_occurrences=inventory,
        )


def test_explicit_aggregators_preserve_exact_and_sampled_value_semantics() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    sampled_events = [_event(0.2, trajectory_index=0), _event(0.6, trajectory_index=1)]
    occurrence = [_occurrence(sampled_events[0])]
    sampled = aggregate_sampled_truncation_events(
        sampled_events,
        trajectory_count=2,
        expected_gate_occurrences=occurrence,
    )
    sampled_ledger = build_mps_truncation_ledger(
        max_bond=1,
        local_dims=(2, 2, 2),
        max_observed_bond=1,
        truncation_events=sampled_events,
        aggregation=sampled,
    )
    assert sampled_ledger["discarded_weight_sum"] == pytest.approx(0.4)
    assert sampled_ledger["aggregation"]["mode"] == "sampled_trajectory_mean"
    assert sampled_ledger["discarded_weight_ledger_complete"] is True

    exact_events = [
        _event(0.2, incoming_branch_weight=0.25, branch_ordinal=0),
        _event(0.6, incoming_branch_weight=0.75, branch_ordinal=1),
    ]
    exact = aggregate_exact_branch_truncation_events(
        exact_events,
        expected_gate_occurrences=[_occurrence(exact_events[0])],
    )
    exact_ledger = build_mps_truncation_ledger(
        max_bond=1,
        local_dims=(2, 2, 2),
        max_observed_bond=1,
        truncation_events=exact_events,
        aggregation=exact,
    )
    assert exact_ledger["discarded_weight_sum"] == pytest.approx(0.5)
    assert exact_ledger["aggregation"]["mode"] == (
        "exact_branch_probability_weighted"
    )
    assert exact_ledger["discarded_weight_ledger_complete"] is True


def test_mixed_dim_unbounded_ledger_preserves_mcwf_manifest_semantics() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    aggregation = aggregate_sampled_truncation_events(
        [], trajectory_count=3, expected_gate_occurrences=[]
    )
    ledger = build_mps_truncation_ledger(
        max_bond=None,
        local_dims=(3, 2, 3),
        max_observed_bond=2,
        truncation_events=[],
        aggregation=aggregation,
    )

    assert ledger["local_dims"] == [3, 2, 3]
    assert ledger["exact_bond_dimension_sufficient"] == 3
    assert ledger["ledger_scope"] == (
        "no_explicit_mps_truncation_requested_mixed_local_dims"
    )
    assert ledger["aggregation"]["trajectory_count"] == 3
    assert ledger["epistemic_class"] == "a/c"


def test_qubit_unbounded_ledger_preserves_no_truncation_metadata() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
        build_mps_truncation_ledger,
    )

    aggregation = aggregate_exact_branch_truncation_events(
        [], expected_gate_occurrences=[]
    )
    ledger = build_mps_truncation_ledger(
        max_bond=None,
        local_dims=(2, 2, 2),
        max_observed_bond=2,
        truncation_events=[],
        aggregation=aggregation,
    )

    assert ledger["exact_bond_dimension_sufficient"] == 2
    assert ledger["ledger_scope"] == "no_explicit_mps_truncation_requested"
    assert ledger["aggregation"]["coverage_policy"] == (
        "not_applicable_no_explicit_truncation"
    )
    assert ledger["epistemic_class"] == "a"


def test_aggregators_fail_closed_on_nonfinite_metric() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
    )

    event = _event(float("nan"), trajectory_index=0)
    with pytest.raises(ValueError):
        aggregate_sampled_truncation_events(
            [event],
            trajectory_count=1,
            expected_gate_occurrences=[_occurrence(event)],
        )


def test_aggregation_preserves_closed_boundaries_and_distinct_metric_channels() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
        aggregate_sampled_truncation_events,
    )

    zero_duration = _event(0.0, trajectory_index=0)
    zero_duration["dt_ns_effective"] = 0.0
    zero_occurrence = _occurrence(zero_duration)
    zero_result = aggregate_sampled_truncation_events(
        [zero_duration],
        trajectory_count=1,
        expected_gate_occurrences=[zero_occurrence],
    )
    assert zero_result["metadata"]["context_complete"] is True
    assert zero_result["metadata"]["expected_gate_occurrences"] == [
        zero_occurrence
    ]

    zero_split = _event(0.0, trajectory_index=0)
    zero_split["split_count"] = 0
    zero_split["split_records"] = []
    assert aggregate_sampled_truncation_events(
        [zero_split],
        trajectory_count=1,
        expected_gate_occurrences=[_occurrence(zero_split)],
    )["fraction"] == 0.0

    distinct = _event(0.1, trajectory_index=0)
    distinct["actual_discarded_weight_raw_sum"] = 0.3
    distinct["unitary_truncation_mass_loss"] = 0.4
    distinct_result = aggregate_sampled_truncation_events(
        [distinct],
        trajectory_count=1,
        expected_gate_occurrences=[_occurrence(distinct)],
    )
    assert (
        distinct_result["fraction"],
        distinct_result["raw"],
        distinct_result["norm_loss"],
    ) == (0.1, 0.3, 0.4)

    empty = aggregate_sampled_truncation_events(
        [],
        trajectory_count=1,
        expected_gate_occurrences=[],
    )
    assert empty["metadata"]["max_observed_sampled_path_fraction_sum"] == 0.0

    for weight, expected_fraction in ((0.0, 0.0), (1.0, 0.25)):
        boundary = _event(
            0.25,
            trajectory_index=None,
            incoming_branch_weight=weight,
            branch_ordinal=0,
        )
        boundary_result = aggregate_exact_branch_truncation_events(
            [boundary],
            expected_gate_occurrences=[_occurrence(boundary)],
        )
        assert boundary_result["fraction"] == expected_fraction



@pytest.mark.parametrize(
    "invalid_weight",
    [
        pytest.param(math.nextafter(0.0, -math.inf), id="below-zero"),
        pytest.param(math.nextafter(1.0, math.inf), id="above-one"),
    ],
)
def test_exact_aggregation_rejects_weight_outside_unit_interval(
    invalid_weight: float,
) -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
    )

    invalid = _event(
        0.25,
        trajectory_index=None,
        incoming_branch_weight=invalid_weight,
        branch_ordinal=0,
    )
    with pytest.raises(ValueError):
        aggregate_exact_branch_truncation_events(
            [invalid],
            expected_gate_occurrences=[_occurrence(invalid)],
        )


@pytest.mark.parametrize(
    ("corruption", "error_type"),
    [
        ("substep_type", ValueError),
        ("operator_type", ValueError),
        ("support_width", ValueError),
        ("microstep_count_zero", ValueError),
        ("microstep_outside", ValueError),
        ("negative_duration", ValueError),
        ("trajectory_count_bool", TypeError),
        ("trajectory_count_none", TypeError),
        ("trajectory_count_zero", ValueError),
        ("trajectory_index_bool", TypeError),
        ("trajectory_index_none", TypeError),
        ("trajectory_index_outside", ValueError),
        ("sampled_branch_weight", ValueError),
        ("exact_trajectory", ValueError),
        ("exact_weight_over_one", ValueError),
        ("branch_ordinal_bool", TypeError),
        ("branch_ordinal_none", TypeError),
        ("branch_ordinal_negative", ValueError),
        ("branch_prefix_tuple", ValueError),
    ],
)
def test_aggregation_rejects_invalid_context(
    corruption: str,
    error_type: type[Exception],
) -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
        aggregate_sampled_truncation_events,
    )

    sampled = _event(0.1, trajectory_index=0)
    expected = _occurrence(sampled)
    trajectory_count: object = 1
    if corruption == "substep_type":
        sampled["substep_id"] = 7
    elif corruption == "operator_type":
        sampled["operator_family"] = 7
    elif corruption == "support_width":
        sampled["support"] = [0]
    elif corruption == "microstep_count_zero":
        sampled["microstep_count"] = 0
    elif corruption == "microstep_outside":
        sampled["microstep_index"] = sampled["microstep_count"]
    elif corruption == "negative_duration":
        sampled["dt_ns_effective"] = -1.0
    elif corruption == "trajectory_count_bool":
        trajectory_count = True
    elif corruption == "trajectory_count_none":
        trajectory_count = None
    elif corruption == "trajectory_count_zero":
        trajectory_count = 0
    elif corruption == "trajectory_index_bool":
        sampled["trajectory_index"] = True
    elif corruption == "trajectory_index_none":
        sampled["trajectory_index"] = None
    elif corruption == "trajectory_index_outside":
        sampled["trajectory_index"] = 1
    elif corruption == "sampled_branch_weight":
        sampled["incoming_branch_weight"] = 0.5
    else:
        exact = _event(
            0.1,
            trajectory_index=None,
            incoming_branch_weight=1.0,
            branch_ordinal=0,
        )
        exact_expected = _occurrence(exact)
        if corruption == "exact_trajectory":
            exact["trajectory_index"] = 0
        elif corruption == "exact_weight_over_one":
            exact["incoming_branch_weight"] = 2.0
        elif corruption == "branch_ordinal_bool":
            exact["branch_ordinal"] = True
        elif corruption == "branch_ordinal_none":
            exact["branch_ordinal"] = None
        elif corruption == "branch_ordinal_negative":
            exact["branch_ordinal"] = -1
        else:
            exact["branch_record_prefix"] = ()
        with pytest.raises(error_type):
            aggregate_exact_branch_truncation_events(
                [exact],
                expected_gate_occurrences=[exact_expected],
            )
        return

    with pytest.raises(error_type):
        aggregate_sampled_truncation_events(
            [sampled],
            trajectory_count=trajectory_count,  # type: ignore[arg-type]
            expected_gate_occurrences=[expected],
        )


def test_aggregator_rejects_split_count_that_disagrees_with_records() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
    )

    event = _event(0.1, trajectory_index=0)
    event["split_count"] = 2

    with pytest.raises(ValueError):
        aggregate_sampled_truncation_events(
            [event],
            trajectory_count=1,
            expected_gate_occurrences=[_occurrence(event)],
        )


@pytest.mark.parametrize(
    "corruption",
    [
        "extra_event_field",
        "nonzero_cutoff",
        "wrong_requested_max_bond",
        "wrong_fraction_identity",
        "wrong_norm_restore_identity",
    ],
)
def test_ledger_rejects_noncanonical_actual_split_event(
    corruption: str,
) -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    event = _event(0.1, trajectory_index=0)
    split = event["split_records"][0]
    if corruption == "extra_event_field":
        event["unregistered"] = False
    elif corruption == "nonzero_cutoff":
        split["requested_cutoff"] = 1.0
    elif corruption == "wrong_requested_max_bond":
        split["requested_max_bond"] = 2
    elif corruption == "wrong_fraction_identity":
        split["actual_discarded_weight_fraction_of_pre_split"] = 0.9
    else:
        event["deterministic_norm_restore_factor"] = 1.0
    aggregation = aggregate_sampled_truncation_events(
        [event],
        trajectory_count=1,
        expected_gate_occurrences=[_occurrence(event)],
    )

    with pytest.raises(ValueError):
        build_mps_truncation_ledger(
            max_bond=1,
            local_dims=(2, 2),
            max_observed_bond=1,
            truncation_events=[event],
            aggregation=aggregation,
        )


@pytest.mark.parametrize(
    ("field", "invalid", "error_type"),
    [
        pytest.param(
            "split_records", (), TypeError, id="records",
        ),
        pytest.param(
            "split_count", True, TypeError, id="bool",
        ),
        pytest.param(
            "split_count", 1.0, TypeError, id="float",
        ),
        pytest.param(
            "split_count", -1, ValueError, id="negative",
        ),
    ],
)
def test_aggregator_rejects_invalid_split_inventory_types(
    field: str,
    invalid: object,
    error_type: type[Exception],
) -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
    )

    event = _event(0.1, trajectory_index=0)
    event[field] = invalid

    with pytest.raises(error_type):
        aggregate_sampled_truncation_events(
            [event],
            trajectory_count=1,
            expected_gate_occurrences=[_occurrence(event)],
        )


def test_unbounded_ledger_rejects_any_truncation_event() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    event = _event(0.1, trajectory_index=0)
    aggregation = aggregate_sampled_truncation_events(
        [event],
        trajectory_count=1,
        expected_gate_occurrences=[_occurrence(event)],
    )
    with pytest.raises(RuntimeError):
        build_mps_truncation_ledger(
            max_bond=None,
            local_dims=(2, 2),
            max_observed_bond=1,
            truncation_events=[event],
            aggregation=aggregation,
        )


def test_ledger_rejects_lossless_sampled_aggregation_for_lossy_events() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    event = _event(0.1, trajectory_index=0)
    forged_lossless = aggregate_sampled_truncation_events(
        [], trajectory_count=1, expected_gate_occurrences=[]
    )

    with pytest.raises(ValueError):
        build_mps_truncation_ledger(
            max_bond=1,
            local_dims=(2, 2),
            max_observed_bond=1,
            truncation_events=[event],
            aggregation=forged_lossless,
        )


def test_ledger_rejects_lossless_exact_aggregation_for_lossy_events() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
        build_mps_truncation_ledger,
    )

    event = _event(0.1, incoming_branch_weight=1.0, branch_ordinal=0)
    forged_lossless = aggregate_exact_branch_truncation_events(
        [], expected_gate_occurrences=[]
    )

    with pytest.raises(ValueError):
        build_mps_truncation_ledger(
            max_bond=1,
            local_dims=(2, 2),
            max_observed_bond=1,
            truncation_events=[event],
            aggregation=forged_lossless,
        )


def test_ledger_rejects_bool_replacement_of_equal_numeric_aggregate() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    event = _event(1.0, trajectory_index=0)
    aggregation = aggregate_sampled_truncation_events(
        [event],
        trajectory_count=1,
        expected_gate_occurrences=[_occurrence(event)],
    )
    aggregation["fraction"] = True

    with pytest.raises(ValueError):
        build_mps_truncation_ledger(
            max_bond=1,
            local_dims=(2, 2),
            max_observed_bond=1,
            truncation_events=[event],
            aggregation=aggregation,
        )


@pytest.mark.parametrize(
    ("corruption", "error_type"),
    [
        pytest.param("extra_top_level_field", ValueError, id="extra-field"),
        pytest.param("extra_coverage_failure", ValueError, id="list-length"),
        pytest.param("identity_field_replacement", ValueError, id="list-value"),
        pytest.param("tuple_expected_inventory", TypeError, id="context-type"),
    ],
)
def test_ledger_rejects_noncanonical_aggregation_shape_and_context_types(
    corruption: str,
    error_type: type[Exception],
) -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    event = _event(0.1, trajectory_index=0)
    aggregation = aggregate_sampled_truncation_events(
        [event],
        trajectory_count=1,
        expected_gate_occurrences=[_occurrence(event)],
    )
    metadata = aggregation["metadata"]
    if corruption == "extra_top_level_field":
        aggregation["forged"] = False
    elif corruption == "extra_coverage_failure":
        metadata["coverage_failures"].append({"reason": "forged"})
    elif corruption == "identity_field_replacement":
        metadata["gate_occurrence_identity_fields"][0] = "forged"
    else:
        metadata["expected_gate_occurrences"] = tuple(
            metadata["expected_gate_occurrences"]
        )

    with pytest.raises(error_type):
        build_mps_truncation_ledger(
            max_bond=1,
            local_dims=(2, 2),
            max_observed_bond=1,
            truncation_events=[event],
            aggregation=aggregation,
        )


def test_mixed_dim_ledger_rejects_wrong_law_and_finite_cap() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    exact = aggregate_exact_branch_truncation_events(
        [], expected_gate_occurrences=[]
    )
    with pytest.raises(ValueError):
        build_mps_truncation_ledger(
            max_bond=None,
            local_dims=(3, 2, 3),
            max_observed_bond=1,
            truncation_events=[],
            aggregation=exact,
        )

    sampled = aggregate_sampled_truncation_events(
        [], trajectory_count=1, expected_gate_occurrences=[]
    )
    with pytest.raises(ValueError):
        build_mps_truncation_ledger(
            max_bond=2,
            local_dims=(3, 2, 3),
            max_observed_bond=1,
            truncation_events=[],
            aggregation=sampled,
        )


@pytest.mark.parametrize(
    ("invalid", "error_type"),
    [
        pytest.param(True, TypeError, id="bool"),
        pytest.param(0, ValueError, id="zero"),
        pytest.param(-1, ValueError, id="negative"),
        pytest.param(1.5, TypeError, id="float"),
        pytest.param("2", TypeError, id="string"),
    ],
)
def test_ledger_rejects_non_positive_integral_max_bond(
    invalid: object,
    error_type: type[Exception],
) -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
        build_mps_truncation_ledger,
    )

    aggregation = aggregate_exact_branch_truncation_events(
        [], expected_gate_occurrences=[]
    )
    with pytest.raises(error_type):
        build_mps_truncation_ledger(
            max_bond=invalid,  # type: ignore[arg-type]
            local_dims=(2, 2),
            max_observed_bond=1,
            truncation_events=[],
            aggregation=aggregation,
        )


def test_finite_nonlocal_ledger_serializes_complete_machine_contract() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    event = _nonlocal_event()
    aggregation = aggregate_sampled_truncation_events(
        [event],
        trajectory_count=1,
        expected_gate_occurrences=[_occurrence(event)],
    )
    ledger = build_mps_truncation_ledger(
        max_bond=2,
        local_dims=(2, 2, 2, 2),
        max_observed_bond=2,
        truncation_events=[event],
        aggregation=aggregation,
    )

    assert ledger == {
        "explicit_truncation_requested": True,
        "max_bond": 2,
        "exact_bond_dimension_sufficient": 4,
        "exact_bond_policy": "finite_cap_below_conservative_exact_sufficient_bond",
        "accepted_as_exact_bond_representation": False,
        "discarded_weight_ledger_complete": True,
        "ledger_method": "quimb_actual_svd_split_per_two_site_unitary_gate",
        "actual_discarded_weight_raw_sum": 1.5,
        "actual_discarded_weight_fraction_sum": 0.75,
        "worst_actual_discarded_weight_fraction": 0.25,
        "actual_split_count": 5,
        "unitary_truncation_mass_loss_sum": 1.5,
        "worst_unitary_truncation_mass_loss": 1.5,
        "path_aggregated_local_discarded_fraction_sum": 0.75,
        "path_aggregated_actual_discarded_weight_raw_sum": 1.5,
        "path_aggregated_unitary_truncation_mass_loss_sum": 1.5,
        "discarded_weight_sum": 0.75,
        "worst_cut_discarded_weight": 0.25,
        "discarded_weight_units": "fraction_of_pre_split_weight",
        "compatibility_aliases": {
            "discarded_weight_sum": (
                "path_aggregated_local_discarded_fraction_sum"
            ),
            "worst_cut_discarded_weight": (
                "worst_actual_discarded_weight_fraction"
            ),
        },
        "not_a_global_error_bound": True,
        "aggregation": aggregation["metadata"],
        "n_truncating_ops": 1,
        "n_tracked_two_site_ops": 1,
        "max_observed_bond": 2,
        "truncation_events": [event],
        "ledger_scope": (
            "finite_max_bond_actual_quimb_svd_split_ledger; each local fraction "
            "is relative to that split's pre-split weight and is not a global "
            "state or record error bound"
        ),
        "epistemic_class": "c",
    }


def test_nonlocal_reverse_support_split_path_is_accepted() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    event = _nonlocal_event(reverse_support=True)
    aggregation = aggregate_sampled_truncation_events(
        [event],
        trajectory_count=1,
        expected_gate_occurrences=[_occurrence(event)],
    )
    ledger = build_mps_truncation_ledger(
        max_bond=2,
        local_dims=(2, 2, 2, 2),
        max_observed_bond=2,
        truncation_events=[event],
        aggregation=aggregation,
    )

    assert ledger["actual_split_count"] == 5
    assert ledger["truncation_events"][0]["support"] == [3, 0]
    assert ledger["truncation_events"][0]["gate_leg_sites"] == [1, 0]


def test_qubit_unbounded_ledger_serializes_complete_machine_contract() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
        build_mps_truncation_ledger,
    )

    aggregation = aggregate_exact_branch_truncation_events(
        [], expected_gate_occurrences=[]
    )
    ledger = build_mps_truncation_ledger(
        max_bond=None,
        local_dims=(2, 2, 2),
        max_observed_bond=2,
        truncation_events=[],
        aggregation=aggregation,
    )

    assert ledger == {
        "explicit_truncation_requested": False,
        "exact_bond_dimension_sufficient": 2,
        "exact_bond_policy": "unbounded_no_explicit_cap",
        "accepted_as_exact_bond_representation": True,
        "discarded_weight_ledger_complete": True,
        "discarded_weight_sum": 0.0,
        "worst_cut_discarded_weight": 0.0,
        "path_aggregated_local_discarded_fraction_sum": 0.0,
        "path_aggregated_actual_discarded_weight_raw_sum": 0.0,
        "path_aggregated_unitary_truncation_mass_loss_sum": 0.0,
        "aggregation": {
            "mode": "exact_branch_probability_weighted",
            "weight_source": "incoming_branch_weight",
            "trajectory_count": None,
            "observed_context_count": 0,
            "expected_gate_occurrence_count": 0,
            "expected_gate_occurrences": [],
            "observed_gate_occurrence_count": 0,
            "complete_gate_occurrence_count": 0,
            "max_observed_sampled_path_fraction_sum": None,
            "gate_occurrence_identity_fields": [
                "substep_id",
                "term_index",
                "operator_family",
                "support",
                "microstep_index",
                "microstep_count",
                "hamiltonian_pass_index",
                "dt_ns_effective",
            ],
            "coverage_policy": "not_applicable_no_explicit_truncation",
            "coverage_failures": [],
            "context_complete": True,
            "not_a_global_error_bound": True,
        },
        "n_truncating_ops": 0,
        "max_observed_bond": 2,
        "ledger_scope": "no_explicit_mps_truncation_requested",
        "epistemic_class": "a",
    }


def test_mixed_unbounded_ledger_serializes_complete_machine_contract() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    aggregation = aggregate_sampled_truncation_events(
        [], trajectory_count=3, expected_gate_occurrences=[]
    )
    ledger = build_mps_truncation_ledger(
        max_bond=None,
        local_dims=(3, 2, 3),
        max_observed_bond=2,
        truncation_events=[],
        aggregation=aggregation,
    )

    assert ledger == {
        "explicit_truncation_requested": False,
        "local_dims": [3, 2, 3],
        "exact_bond_dimension_sufficient": 3,
        "exact_bond_policy": "unbounded_no_explicit_cap_mixed_local_dims",
        "accepted_as_exact_bond_representation": True,
        "discarded_weight_ledger_complete": True,
        "discarded_weight_sum": 0.0,
        "worst_cut_discarded_weight": 0.0,
        "path_aggregated_local_discarded_fraction_sum": 0.0,
        "path_aggregated_actual_discarded_weight_raw_sum": 0.0,
        "path_aggregated_unitary_truncation_mass_loss_sum": 0.0,
        "aggregation": {
            "mode": "sampled_trajectory_mean",
            "weight_source": "uniform_over_explicit_trajectory_count",
            "trajectory_count": 3,
            "observed_context_count": 0,
            "max_observed_sampled_path_fraction_sum": 0.0,
            "context_complete": True,
            "not_a_global_error_bound": True,
        },
        "n_truncating_ops": 0,
        "max_observed_bond": 2,
        "ledger_scope": "no_explicit_mps_truncation_requested_mixed_local_dims",
        "epistemic_class": "a/c",
    }


@pytest.mark.parametrize(
    ("path", "invalid"),
    [
        pytest.param(("event", "max_bond"), True, id="max-bond-bool"),
        pytest.param(("event", "max_bond"), 1, id="max-bond-mismatch"),
        pytest.param(
            ("event", "gate_leg_sites"), [0, 2], id="gate-leg-topology"
        ),
        pytest.param(("event", "substep_kind"), "", id="empty-substep-kind"),
        pytest.param(
            ("event", "branch_record_prefix"), [True], id="boolean-prefix-bit"
        ),
        pytest.param(
            ("event", "array_backend"), "numpy_complex128", id="backend"
        ),
        pytest.param(("event", "epistemic_class"), "a", id="epistemic-class"),
        pytest.param(("event", "quimb_version"), "1.13.0", id="quimb-version"),
        pytest.param(
            ("event", "physical_branch_probability"), 0.5, id="branch-probability"
        ),
        pytest.param(
            ("event", "actual_discarded_weight_raw_sum"),
            1.4,
            id="raw-sum-identity",
        ),
        pytest.param(
            ("event", "actual_discarded_weight_fraction_sum"),
            0.7,
            id="fraction-sum-identity",
        ),
        pytest.param(
            ("event", "worst_actual_discarded_weight_fraction"),
            0.2,
            id="worst-fraction-identity",
        ),
        pytest.param(
            ("event", "unitary_truncation_mass_loss"),
            1.4,
            id="unitary-loss-identity",
        ),
        pytest.param(("event", "input_norm_sq"), 0.0, id="input-norm-positive"),
        pytest.param(
            ("event", "raw_output_norm_sq"), 5.0, id="raw-output-exceeds-input"
        ),
        pytest.param(
            ("event", "restored_output_norm_sq"),
            3.9,
            id="restored-norm-identity",
        ),
        pytest.param(
            ("event", "deterministic_norm_restore_factor"),
            1.0,
            id="restore-factor-identity",
        ),
        pytest.param(
            ("event", "discarded_weight_sum"), 0.7, id="discarded-alias-sum"
        ),
        pytest.param(
            ("event", "worst_cut_discarded_weight"),
            0.2,
            id="discarded-alias-worst",
        ),
        pytest.param(
            ("event", "ledger_semantics"), "global_bound", id="ledger-semantics"
        ),
        pytest.param(
            ("event", "ledger_method"), "dense_cut", id="ledger-method"
        ),
        pytest.param(
            ("event", "discarded_weight_units"), "raw", id="discarded-units"
        ),
        pytest.param(
            ("event", "compatibility_aliases"), {}, id="compatibility-aliases"
        ),
        pytest.param(
            ("event", "n_truncated_cuts"), 4, id="truncated-cut-count"
        ),
        pytest.param(
            ("event", "not_a_global_error_bound"), False, id="event-disclaimer"
        ),
        pytest.param(("split", 0, "extra"), False, id="extra-split-field"),
        pytest.param(
            ("split", 0, "sequence_index"), True, id="sequence-index-bool"
        ),
        pytest.param(
            ("split", 0, "sequence_index"), 1, id="sequence-index-order"
        ),
        pytest.param(
            ("split", 0, "path_role"),
            "two_site_operator_split",
            id="path-role-order",
        ),
        pytest.param(
            ("split", 0, "split_sites"), [1, 3], id="swap-path-sites"
        ),
        pytest.param(
            ("split", 0, "gate_leg_sites"), [0, 1], id="swap-gate-legs"
        ),
        pytest.param(
            ("split", 2, "gate_leg_sites"), None, id="operator-gate-legs"
        ),
        pytest.param(("split", 0, "requested_method"), "qr", id="method"),
        pytest.param(
            ("split", 0, "requested_absorb"), "right", id="absorb-direction"
        ),
        pytest.param(
            ("split", 0, "requested_max_bond"), True, id="split-max-bond-bool"
        ),
        pytest.param(
            ("split", 0, "requested_max_bond"), 1, id="split-max-bond-mismatch"
        ),
        pytest.param(
            ("split", 0, "requested_cutoff"), 0, id="cutoff-exact-float"
        ),
        pytest.param(
            ("split", 0, "requested_cutoff"), 0.1, id="cutoff-nonzero"
        ),
        pytest.param(
            ("split", 0, "requested_cutoff_mode"), "sum2", id="cutoff-mode"
        ),
        pytest.param(
            ("split", 0, "requested_renorm"), False, id="renorm-policy"
        ),
        pytest.param(
            ("split", 0, "pre_split_total_weight"),
            0.0,
            id="pre-split-positive",
        ),
        pytest.param(
            ("split", 0, "actual_kept_bond_dimension"),
            True,
            id="kept-bond-bool",
        ),
        pytest.param(
            ("split", 0, "actual_kept_bond_dimension"),
            3,
            id="kept-bond-over-cap",
        ),
        pytest.param(
            ("split", 0, "actual_discarded_weight_raw"),
            -0.1,
            id="raw-discard-negative",
        ),
        pytest.param(
            ("split", 0, "actual_discarded_weight_raw"),
            3.0,
            id="raw-discard-over-weight",
        ),
        pytest.param(
            ("split", 0, "actual_discarded_weight_fraction_of_pre_split"),
            0.2,
            id="split-fraction-identity",
        ),
        pytest.param(
            ("split", 0, "not_a_global_error_bound"),
            False,
            id="split-disclaimer",
        ),
    ],
)
def test_nonlocal_split_event_corruption_fails_closed_without_prose_contract(
    path: tuple[object, ...],
    invalid: object,
) -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    event = _nonlocal_event()
    if path[0] == "event":
        event[path[1]] = invalid
    else:
        split_records = event["split_records"]
        split_records[path[1]][path[2]] = invalid
    aggregation = aggregate_sampled_truncation_events(
        [event],
        trajectory_count=1,
        expected_gate_occurrences=[_occurrence(event)],
    )

    with pytest.raises((TypeError, ValueError)):
        build_mps_truncation_ledger(
            max_bond=2,
            local_dims=(2, 2, 2, 2),
            max_observed_bond=2,
            truncation_events=[event],
            aggregation=aggregation,
        )


@pytest.mark.parametrize(
    ("corruption", "error_type"),
    [
        ("exact_missing_weight", ValueError),
        ("exact_missing_ordinal", ValueError),
        ("sampled_weight", ValueError),
        ("sampled_ordinal_bool", TypeError),
        ("incoming_weight_over_one", ValueError),
        ("support_tuple", ValueError),
        ("support_width", ValueError),
        ("support_bool", ValueError),
        ("duration_int", TypeError),
        ("microstep_count_zero", ValueError),
        ("microstep_outside", ValueError),
        ("pass_bool", TypeError),
    ],
)
def test_actual_split_validator_rejects_context_corruption(
    corruption: str,
    error_type: type[Exception],
) -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        _validate_actual_split_event,
    )

    event = _nonlocal_event()
    if corruption == "exact_missing_weight":
        event["trajectory_index"] = None
        event["incoming_branch_weight"] = None
        event["branch_ordinal"] = 0
    elif corruption == "exact_missing_ordinal":
        event["trajectory_index"] = None
        event["incoming_branch_weight"] = 1.0
        del event["branch_ordinal"]
    elif corruption == "sampled_weight":
        event["incoming_branch_weight"] = 0.5
    elif corruption == "sampled_ordinal_bool":
        event["branch_ordinal"] = True
    elif corruption == "incoming_weight_over_one":
        event["trajectory_index"] = None
        event["incoming_branch_weight"] = 1.5
        event["branch_ordinal"] = 0
    elif corruption == "support_tuple":
        event["support"] = (0, 3)
    elif corruption == "support_width":
        event["support"] = [0]
    elif corruption == "support_bool":
        event["support"] = [True, 3]
    elif corruption == "duration_int":
        event["dt_ns_effective"] = 1
    elif corruption == "microstep_count_zero":
        event["microstep_count"] = 0
    elif corruption == "microstep_outside":
        event["microstep_index"] = event["microstep_count"]
    else:
        event["hamiltonian_pass_index"] = True

    with pytest.raises(error_type):
        _validate_actual_split_event(
            event,
            expected_max_bond=2,
            context="unit_event",
        )


def test_actual_split_validator_accepts_shifted_support_and_exact_weight_endpoints() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        _validate_actual_split_event,
    )

    shifted = _nonlocal_event()
    shifted["support"] = [1, 4]
    shifted["gate_leg_sites"] = [1, 2]
    records = shifted["split_records"]
    assert isinstance(records, list)
    for record in records:
        record["split_sites"] = [site + 1 for site in record["split_sites"]]
        if record["gate_leg_sites"] is not None:
            record["gate_leg_sites"] = [
                site + 1 for site in record["gate_leg_sites"]
            ]
    assert _validate_actual_split_event(
        shifted,
        expected_max_bond=2,
        context="shifted",
    ) is None

    for weight in (0.0, 1.0):
        boundary = _nonlocal_event(
            trajectory_index=None,
            incoming_branch_weight=weight,
            branch_ordinal=0,
        )
        assert _validate_actual_split_event(
            boundary,
            expected_max_bond=2,
            context="boundary",
        ) is None



@pytest.mark.parametrize(
    "invalid_weight",
    [
        pytest.param(math.nextafter(0.0, -math.inf), id="below-zero"),
        pytest.param(math.nextafter(1.0, math.inf), id="above-one"),
    ],
)
def test_actual_split_validator_rejects_weight_outside_unit_interval(
    invalid_weight: float,
) -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        _validate_actual_split_event,
    )

    invalid = _nonlocal_event(
        trajectory_index=None,
        incoming_branch_weight=invalid_weight,
        branch_ordinal=0,
    )
    with pytest.raises(ValueError):
        _validate_actual_split_event(
            invalid,
            expected_max_bond=2,
            context="invalid_boundary",
        )


def test_aggregation_validator_and_authenticator_reject_corruption() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        _validate_aggregation_result,
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    event = _event(0.1, trajectory_index=0)
    canonical = aggregate_sampled_truncation_events(
        [event],
        trajectory_count=1,
        expected_gate_occurrences=[_occurrence(event)],
    )
    validation_cases = (
        (None, TypeError),
        ({**canonical, "raw": -1.0}, ValueError),
        ({**canonical, "metadata": None}, TypeError),
        (
            {
                **canonical,
                "metadata": {**canonical["metadata"], "mode": "forged"},
            },
            ValueError,
        ),
        (
            {
                **canonical,
                "metadata": {
                    **canonical["metadata"],
                    "context_complete": 1,
                },
            },
            TypeError,
        ),
    )
    for candidate, error_type in validation_cases:
        with pytest.raises(error_type):
            _validate_aggregation_result(candidate)  # type: ignore[arg-type]

    metadata = canonical["metadata"]
    assert isinstance(metadata, dict)
    expected_occurrences = metadata["expected_gate_occurrences"]
    assert isinstance(expected_occurrences, list)
    wrong_inventory_type = {
        **canonical,
        "metadata": {
            **metadata,
            "expected_gate_occurrences": tuple(expected_occurrences),
        },
    }
    with pytest.raises(TypeError):
        build_mps_truncation_ledger(
            max_bond=1,
            local_dims=(2, 2),
            max_observed_bond=1,
            truncation_events=[event],
            aggregation=wrong_inventory_type,
        )

    forged = {**canonical, "fraction": canonical["fraction"] + 0.25}
    with pytest.raises(ValueError):
        build_mps_truncation_ledger(
            max_bond=1,
            local_dims=(2, 2),
            max_observed_bond=1,
            truncation_events=[event],
            aggregation=forged,
        )


def test_empty_finite_ledger_keeps_zero_worst_case_and_operation_counts() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    aggregation = aggregate_sampled_truncation_events(
        [],
        trajectory_count=1,
        expected_gate_occurrences=[],
    )
    ledger = build_mps_truncation_ledger(
        max_bond=1,
        local_dims=(2, 2),
        max_observed_bond=1,
        truncation_events=[],
        aggregation=aggregation,
    )
    assert ledger["worst_actual_discarded_weight_fraction"] == 0.0
    assert ledger["worst_unitary_truncation_mass_loss"] == 0.0
    assert ledger["n_truncating_ops"] == 0


def _sampled_ledger_for_boundary_event(
    event: dict[str, object],
) -> dict[str, object]:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
        build_mps_truncation_ledger,
    )

    aggregation = aggregate_sampled_truncation_events(
        [event],
        trajectory_count=1,
        expected_gate_occurrences=[_occurrence(event)],
    )
    return build_mps_truncation_ledger(
        max_bond=1,
        local_dims=(2, 2),
        max_observed_bond=1,
        truncation_events=[event],
        aggregation=aggregation,
    )


def test_exact_branch_mass_completeness_closes_at_numerical_tolerance() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
    )
    from error_coupling_simulator.numerics import NUMERICAL_ZERO

    nearest_inside = 1.0 - NUMERICAL_ZERO
    if abs(nearest_inside - 1.0) > NUMERICAL_ZERO:
        nearest_inside = math.nextafter(nearest_inside, 1.0)
    nearest_outside = math.nextafter(nearest_inside, 0.0)
    assert abs(nearest_inside - 1.0) <= NUMERICAL_ZERO
    assert abs(nearest_outside - 1.0) > NUMERICAL_ZERO

    inside = _event(
        0.0,
        trajectory_index=None,
        incoming_branch_weight=nearest_inside,
        branch_ordinal=0,
    )
    outside = _event(
        0.0,
        trajectory_index=None,
        incoming_branch_weight=nearest_outside,
        branch_ordinal=0,
    )

    accepted = aggregate_exact_branch_truncation_events(
        [inside],
        expected_gate_occurrences=[_occurrence(inside)],
    )
    rejected = aggregate_exact_branch_truncation_events(
        [outside],
        expected_gate_occurrences=[_occurrence(outside)],
    )

    assert accepted["metadata"]["context_complete"] is True
    assert accepted["metadata"]["complete_gate_occurrence_count"] == 1
    assert rejected["metadata"]["context_complete"] is False
    assert rejected["metadata"]["complete_gate_occurrence_count"] == 0


def test_split_raw_weight_closes_at_scaled_pre_split_tolerance() -> None:
    from error_coupling_simulator.numerics import NUMERICAL_ZERO

    pre_split_weight = 2.0
    closed_raw = pre_split_weight + (
        100.0 * NUMERICAL_ZERO * max(1.0, pre_split_weight)
    )
    outside_raw = math.nextafter(closed_raw, math.inf)
    accepted_event = _event(closed_raw / pre_split_weight, trajectory_index=0)
    rejected_event = _event(outside_raw / pre_split_weight, trajectory_index=0)

    accepted = _sampled_ledger_for_boundary_event(accepted_event)
    assert accepted["actual_discarded_weight_raw_sum"] == closed_raw
    with pytest.raises(ValueError):
        _sampled_ledger_for_boundary_event(rejected_event)


def test_raw_output_norm_closes_at_scaled_input_tolerance() -> None:
    from error_coupling_simulator.numerics import NUMERICAL_ZERO

    input_norm = 4.0
    closed_raw_output = input_norm + (
        NUMERICAL_ZERO * max(1.0, input_norm)
    )
    outside_raw_output = math.nextafter(closed_raw_output, math.inf)

    def event_with_raw_output(raw_output: float) -> dict[str, object]:
        event = _event(0.0, trajectory_index=0)
        event["raw_output_norm_sq"] = raw_output
        event["deterministic_norm_restore_factor"] = math.sqrt(
            input_norm / raw_output
        )
        return event

    accepted = _sampled_ledger_for_boundary_event(
        event_with_raw_output(closed_raw_output)
    )
    assert accepted["truncation_events"][0]["raw_output_norm_sq"] == (
        closed_raw_output
    )
    with pytest.raises(ValueError):
        _sampled_ledger_for_boundary_event(
            event_with_raw_output(outside_raw_output)
        )


def test_split_raw_sum_agreement_closes_at_scaled_norm_loss_tolerance() -> None:
    from error_coupling_simulator.numerics import NUMERICAL_ZERO

    input_norm = 4.0
    split_raw = 0.2
    tolerance = 100.0 * NUMERICAL_ZERO * max(1.0, input_norm, split_raw)
    outside_raw_output = input_norm - (split_raw + tolerance)
    inside_raw_output = math.nextafter(outside_raw_output, math.inf)
    inside_loss = input_norm - inside_raw_output
    outside_loss = input_norm - outside_raw_output
    assert abs(split_raw - inside_loss) <= tolerance
    assert abs(split_raw - outside_loss) > tolerance

    def event_with_observed_loss(
        raw_output: float,
        observed_loss: float,
    ) -> dict[str, object]:
        event = _event(split_raw / 2.0, trajectory_index=0)
        event["raw_output_norm_sq"] = raw_output
        event["unitary_truncation_mass_loss"] = observed_loss
        event["deterministic_norm_restore_factor"] = math.sqrt(
            input_norm / raw_output
        )
        return event

    accepted = _sampled_ledger_for_boundary_event(
        event_with_observed_loss(inside_raw_output, inside_loss)
    )
    assert accepted["actual_discarded_weight_raw_sum"] == split_raw
    with pytest.raises(ValueError):
        _sampled_ledger_for_boundary_event(
            event_with_observed_loss(outside_raw_output, outside_loss)
        )


@pytest.mark.parametrize(
    ("input_norm", "tolerance"),
    [
        pytest.param(1.0e-6, 1.0e-12, id="absolute-axis"),
        pytest.param(1.0e6, 1.0e-6, id="relative-axis"),
    ],
)
def test_restored_norm_closes_independently_on_absolute_and_relative_axes(
    input_norm: float,
    tolerance: float,
) -> None:
    nominal_boundary = input_norm + tolerance
    inside_restored = math.nextafter(nominal_boundary, input_norm)
    outside_restored = nominal_boundary
    assert math.isclose(
        inside_restored,
        input_norm,
        rel_tol=1.0e-12,
        abs_tol=1.0e-12,
    )
    assert not math.isclose(
        outside_restored,
        input_norm,
        rel_tol=1.0e-12,
        abs_tol=1.0e-12,
    )

    def event_with_restored_norm(restored_norm: float) -> dict[str, object]:
        event = _event(0.0, trajectory_index=0)
        event["input_norm_sq"] = input_norm
        event["raw_output_norm_sq"] = input_norm
        event["restored_output_norm_sq"] = restored_norm
        event["deterministic_norm_restore_factor"] = 1.0
        return event

    accepted = _sampled_ledger_for_boundary_event(
        event_with_restored_norm(inside_restored)
    )
    assert accepted["truncation_events"][0]["restored_output_norm_sq"] == (
        inside_restored
    )
    with pytest.raises(ValueError):
        _sampled_ledger_for_boundary_event(
            event_with_restored_norm(outside_restored)
        )


def _synchronize_single_split_numerics(
    event: dict[str, object],
    *,
    pre_weight: float,
    raw: float,
    input_norm: float,
    raw_output: float,
    restored: float | None = None,
) -> None:
    """Keep every non-target field canonical around one numerical corruption."""

    split_records = event["split_records"]
    assert isinstance(split_records, list)
    split = split_records[0]
    assert isinstance(split, dict)
    fraction = raw / pre_weight if pre_weight > 0.0 else 0.0
    observed_loss = max(0.0, input_norm - raw_output)
    split.update(
        {
            "pre_split_total_weight": pre_weight,
            "actual_discarded_weight_raw": raw,
            "actual_discarded_weight_fraction_of_pre_split": fraction,
        }
    )
    event.update(
        {
            "input_norm_sq": input_norm,
            "raw_output_norm_sq": raw_output,
            "restored_output_norm_sq": (
                input_norm if restored is None else restored
            ),
            "deterministic_norm_restore_factor": (
                math.sqrt(input_norm / raw_output)
                if raw_output > 0.0
                else 1.0
            ),
            "unitary_truncation_mass_loss": observed_loss,
            "actual_discarded_weight_raw_sum": raw,
            "actual_discarded_weight_fraction_sum": fraction,
            "worst_actual_discarded_weight_fraction": fraction,
            "discarded_weight_sum": fraction,
            "worst_cut_discarded_weight": fraction,
            "n_truncated_cuts": int(raw > 0.0),
        }
    )


def test_actual_split_validator_accepts_binary_prefix_and_sampled_ordinal() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        _validate_actual_split_event,
    )

    exact = _event(
        0.0,
        trajectory_index=None,
        incoming_branch_weight=1.0,
        branch_ordinal=0,
    )
    exact["branch_record_prefix"] = [0, 1]
    assert (
        _validate_actual_split_event(
            exact,
            expected_max_bond=1,
            context="binary_prefix",
        )
        is None
    )

    sampled = _event(0.0, trajectory_index=0, branch_ordinal=0)
    assert (
        _validate_actual_split_event(
            sampled,
            expected_max_bond=1,
            context="sampled_ordinal",
        )
        is None
    )


def test_actual_split_validator_rejects_negative_consistent_support_path() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        _validate_actual_split_event,
    )

    event = _event(0.0, trajectory_index=0)
    event["support"] = [-1, 0]
    event["gate_leg_sites"] = [-1, 0]
    split_records = event["split_records"]
    assert isinstance(split_records, list)
    split = split_records[0]
    assert isinstance(split, dict)
    split["split_sites"] = [-1, 0]
    split["gate_leg_sites"] = [-1, 0]
    with pytest.raises(ValueError):
        _validate_actual_split_event(
            event,
            expected_max_bond=1,
            context="negative_support",
        )


def test_actual_split_validator_rejects_one_sided_split_inventory_mismatch() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        _validate_actual_split_event,
    )

    event = _event(0.0, trajectory_index=0)
    split_records = event["split_records"]
    assert isinstance(split_records, list)
    extra = dict(split_records[0])
    extra["sequence_index"] = 1
    split_records.append(extra)
    event["split_count"] = 2
    with pytest.raises(ValueError):
        _validate_actual_split_event(
            event,
            expected_max_bond=1,
            context="split_inventory",
        )


def test_actual_split_validator_rejects_structural_zero_fields() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        _validate_actual_split_event,
    )
    from error_coupling_simulator.numerics import NUMERICAL_ZERO

    zero_pre_weight = _event(0.0, trajectory_index=0)
    _synchronize_single_split_numerics(
        zero_pre_weight,
        pre_weight=0.0,
        raw=0.0,
        input_norm=1.0,
        raw_output=1.0,
    )
    zero_kept_bond = _event(0.0, trajectory_index=0)
    kept_records = zero_kept_bond["split_records"]
    assert isinstance(kept_records, list)
    kept_records[0]["actual_kept_bond_dimension"] = 0
    zero_raw_output = _event(0.0, trajectory_index=0)
    _synchronize_single_split_numerics(
        zero_raw_output,
        pre_weight=1.0,
        raw=1.0,
        input_norm=1.0,
        raw_output=0.0,
    )
    tiny = 0.5 * NUMERICAL_ZERO
    zero_restored = _event(0.0, trajectory_index=0)
    _synchronize_single_split_numerics(
        zero_restored,
        pre_weight=1.0,
        raw=0.0,
        input_norm=tiny,
        raw_output=tiny,
        restored=0.0,
    )

    for label, event in (
        ("pre_weight", zero_pre_weight),
        ("kept_bond", zero_kept_bond),
        ("raw_output", zero_raw_output),
        ("restored_output", zero_restored),
    ):
        with pytest.raises(ValueError):
            _validate_actual_split_event(
                event,
                expected_max_bond=1,
                context=f"zero_{label}",
            )


def test_actual_split_validator_pins_scaled_tolerance_floors() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        _validate_actual_split_event,
    )
    from error_coupling_simulator.numerics import NUMERICAL_ZERO

    pre_weight = 0.5
    widened_pre_weight = _event(0.0, trajectory_index=0)
    raw = pre_weight + 150.0 * NUMERICAL_ZERO
    _synchronize_single_split_numerics(
        widened_pre_weight,
        pre_weight=pre_weight,
        raw=raw,
        input_norm=1.0,
        raw_output=1.0 - raw,
    )
    with pytest.raises(ValueError):
        _validate_actual_split_event(
            widened_pre_weight,
            expected_max_bond=1,
            context="pre_weight_scale",
        )

    widened_raw_output = _event(0.0, trajectory_index=0)
    _synchronize_single_split_numerics(
        widened_raw_output,
        pre_weight=1.0,
        raw=0.0,
        input_norm=0.5,
        raw_output=0.5 + 1.5 * NUMERICAL_ZERO,
    )
    with pytest.raises(ValueError):
        _validate_actual_split_event(
            widened_raw_output,
            expected_max_bond=1,
            context="raw_output_scale",
        )

    closed = _event(0.0, trajectory_index=0)
    _synchronize_single_split_numerics(
        closed,
        pre_weight=1.0,
        raw=100.0 * NUMERICAL_ZERO,
        input_norm=1.0,
        raw_output=1.0,
    )
    assert (
        _validate_actual_split_event(
            closed,
            expected_max_bond=1,
            context="closed_split_norm",
        )
        is None
    )

    absolute_floor = _event(0.0, trajectory_index=0)
    _synchronize_single_split_numerics(
        absolute_floor,
        pre_weight=1.0,
        raw=75.0 * NUMERICAL_ZERO,
        input_norm=0.5,
        raw_output=0.5,
    )
    assert (
        _validate_actual_split_event(
            absolute_floor,
            expected_max_bond=1,
            context="absolute_floor",
        )
        is None
    )

    doubled_floor = _event(0.0, trajectory_index=0)
    _synchronize_single_split_numerics(
        doubled_floor,
        pre_weight=1.0,
        raw=150.0 * NUMERICAL_ZERO,
        input_norm=0.5,
        raw_output=0.5,
    )
    with pytest.raises(ValueError):
        _validate_actual_split_event(
            doubled_floor,
            expected_max_bond=1,
            context="doubled_floor",
        )


def test_sampled_coverage_failure_binds_missing_pass_and_path_gap() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
    )

    event = _event(0.0, trajectory_index=0)
    expected = _occurrence(event)
    event["hamiltonian_pass_index"] = None
    result = aggregate_sampled_truncation_events(
        [event],
        trajectory_count=2,
        expected_gate_occurrences=[expected],
    )
    failure = result["metadata"]["coverage_failures"][0]
    assert failure["reason"] == (
        "gate_occurrence_identity_incomplete+"
        "sampled_trajectory_coverage_incomplete"
    )
    assert failure["hamiltonian_pass_index"] is None
    assert failure["missing_trajectory_count"] == 1
    assert failure["duplicate_event_count"] == 0


def test_exact_coverage_failure_binds_identity_ordinal_and_mass_gaps() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_exact_branch_truncation_events,
    )

    event = _event(
        0.0,
        trajectory_index=None,
        incoming_branch_weight=0.25,
        branch_ordinal=1,
    )
    expected = _occurrence(event)
    event["hamiltonian_pass_index"] = None
    result = aggregate_exact_branch_truncation_events(
        [event],
        expected_gate_occurrences=[expected],
    )
    failure = result["metadata"]["coverage_failures"][0]
    assert failure["reason"] == (
        "gate_occurrence_identity_incomplete+"
        "exact_branch_ordinal_coverage_incomplete+"
        "exact_branch_mass_not_unity"
    )
    assert failure["hamiltonian_pass_index"] is None
    assert failure["observed_branch_count"] == 1
    assert failure["unique_branch_ordinal_count"] == 1
    assert failure["incoming_branch_weight_sum"] == 0.25


def test_occurrence_failure_rows_have_repr_deterministic_order() -> None:
    from error_coupling_simulator.carrier.mps.truncation import (
        aggregate_sampled_truncation_events,
    )

    expected_template = _event(0.0, trajectory_index=0)
    expected_template["substep_id"] = "expected"
    term_two = _occurrence(expected_template)
    term_two["term_index"] = 2
    term_ten = dict(term_two)
    term_ten["term_index"] = 10
    missing_pass = _event(0.0, trajectory_index=0)
    missing_pass["substep_id"] = "observed"
    missing_pass["hamiltonian_pass_index"] = None
    explicit_pass = _event(0.0, trajectory_index=0)
    explicit_pass["substep_id"] = "observed"
    result = aggregate_sampled_truncation_events(
        [missing_pass, explicit_pass],
        trajectory_count=1,
        expected_gate_occurrences=[term_two, term_ten],
    )
    failures = result["metadata"]["coverage_failures"]
    assert [
        (
            failure["reason"],
            failure["substep_id"],
            failure["term_index"],
            failure["hamiltonian_pass_index"],
        )
        for failure in failures
    ] == [
        ("gate_occurrence_identity_incomplete", "observed", 0, None),
        ("expected_gate_occurrence_missing", "expected", 10, 0),
        ("expected_gate_occurrence_missing", "expected", 2, 0),
        ("unexpected_gate_occurrence_observed", "observed", 0, 0),
        ("unexpected_gate_occurrence_observed", "observed", 0, None),
    ]


def test_zero_discard_event_is_tracked_but_not_truncating() -> None:
    ledger = _sampled_ledger_for_boundary_event(
        _event(0.0, trajectory_index=0)
    )
    assert ledger["actual_split_count"] == 1
    assert ledger["n_tracked_two_site_ops"] == 1
    assert ledger["n_truncating_ops"] == 0


def test_split_norm_tolerance_includes_raw_sum_at_binary64_separator() -> None:
    from error_coupling_simulator.numerics import NUMERICAL_ZERO

    input_norm = float.fromhex("0x1.f8d31f61271c7p+0")
    raw_sum = float.fromhex("0x1.f8d31f61ffee8p+0")
    raw_output = float.fromhex("0x1.0000000000000p-54")
    observed_loss = max(0.0, input_norm - raw_output)
    difference = abs(raw_sum - observed_loss)
    scale = 100.0 * NUMERICAL_ZERO
    assert observed_loss == input_norm
    assert difference > scale * max(1.0, input_norm)
    assert difference <= scale * max(1.0, input_norm, raw_sum)

    event = _event(0.0, trajectory_index=0)
    _synchronize_single_split_numerics(
        event,
        pre_weight=raw_sum,
        raw=raw_sum,
        input_norm=input_norm,
        raw_output=raw_output,
    )
    ledger = _sampled_ledger_for_boundary_event(event)
    assert ledger["actual_discarded_weight_raw_sum"] == raw_sum
    assert ledger["unitary_truncation_mass_loss_sum"] == observed_loss
    assert ledger["discarded_weight_ledger_complete"] is True
