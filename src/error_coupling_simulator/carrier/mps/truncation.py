from __future__ import annotations

"""Law-neutral truncation aggregation and ledger mechanics for MPS routes."""

import math
import operator
from typing import Any

from ...numerics import NUMERICAL_ZERO
from .controls import normalize_mps_max_bond
from .state import exact_mps_bond_dimension


_SAMPLED_MODE = "sampled_trajectory_mean"
_EXACT_MODE = "exact_branch_probability_weighted"
_ACTUAL_SPLIT_EVENT_KEYS = {
    "substep_id",
    "substep_kind",
    "term_index",
    "operator_family",
    "branch_record_prefix",
    "trajectory_index",
    "incoming_branch_weight",
    "array_backend",
    "dt_ns_effective",
    "microstep_index",
    "microstep_count",
    "hamiltonian_pass_index",
    "epistemic_class",
    "support",
    "gate_leg_sites",
    "max_bond",
    "quimb_version",
    "input_norm_sq",
    "raw_output_norm_sq",
    "restored_output_norm_sq",
    "deterministic_norm_restore_factor",
    "unitary_truncation_mass_loss",
    "physical_branch_probability",
    "split_count",
    "split_records",
    "actual_discarded_weight_raw_sum",
    "actual_discarded_weight_fraction_sum",
    "worst_actual_discarded_weight_fraction",
    "ledger_semantics",
    "not_a_global_error_bound",
    "ledger_method",
    "discarded_weight_sum",
    "worst_cut_discarded_weight",
    "discarded_weight_units",
    "compatibility_aliases",
    "n_truncated_cuts",
}
_ACTUAL_SPLIT_RECORD_KEYS = {
    "sequence_index",
    "path_role",
    "split_sites",
    "gate_leg_sites",
    "requested_method",
    "requested_absorb",
    "requested_max_bond",
    "requested_cutoff",
    "requested_cutoff_mode",
    "requested_renorm",
    "pre_split_total_weight",
    "actual_kept_bond_dimension",
    "actual_discarded_weight_raw",
    "actual_discarded_weight_fraction_of_pre_split",
    "not_a_global_error_bound",
}


def aggregate_sampled_truncation_events(
    events: list[dict[str, Any]],
    *,
    trajectory_count: int,
    expected_gate_occurrences: tuple[dict[str, Any], ...] | list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate per-trajectory events with explicit uniform path weighting."""

    return _aggregate_truncation_events(
        events,
        aggregation_law=_SAMPLED_MODE,
        trajectory_count=trajectory_count,
        expected_gate_occurrences=expected_gate_occurrences,
    )


def aggregate_exact_branch_truncation_events(
    events: list[dict[str, Any]],
    *,
    expected_gate_occurrences: tuple[dict[str, Any], ...] | list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate exact-branch events with incoming branch-probability weights."""

    return _aggregate_truncation_events(
        events,
        aggregation_law=_EXACT_MODE,
        trajectory_count=None,
        expected_gate_occurrences=expected_gate_occurrences,
    )


def build_mps_truncation_ledger(
    *,
    max_bond: int | None,
    local_dims: tuple[int, ...] | list[int],
    max_observed_bond: int,
    truncation_events: list[dict[str, Any]],
    aggregation: dict[str, Any],
) -> dict[str, Any]:
    """Build the shared restricted-MPS ledger from an explicit aggregation law."""

    normalized_max_bond = normalize_mps_max_bond(max_bond)
    dimensions = tuple(local_dims)
    exact_bond = exact_mps_bond_dimension(dimensions)
    if normalized_max_bond is None and truncation_events:
        raise RuntimeError(
            "unbounded MPS execution unexpectedly emitted truncation events"
        )
    if normalized_max_bond is not None:
        for event_index, event in enumerate(truncation_events):
            _validate_actual_split_event(
                event,
                expected_max_bond=normalized_max_bond,
                context=f"truncation_events[{event_index}]",
            )
    _validate_aggregation_result(aggregation)
    _authenticate_aggregation_against_events(
        truncation_events,
        aggregation=aggregation,
    )
    metadata = aggregation["metadata"]

    if normalized_max_bond is None:
        if any(dimension != 2 for dimension in dimensions):
            if metadata["mode"] != _SAMPLED_MODE:
                raise ValueError(
                    "mixed-dimension unbounded ledger requires sampled aggregation"
                )
            return {
                "explicit_truncation_requested": False,
                "local_dims": list(dimensions),
                "exact_bond_dimension_sufficient": exact_bond,
                "exact_bond_policy": "unbounded_no_explicit_cap_mixed_local_dims",
                "accepted_as_exact_bond_representation": True,
                "discarded_weight_ledger_complete": True,
                "discarded_weight_sum": 0.0,
                "worst_cut_discarded_weight": 0.0,
                "path_aggregated_local_discarded_fraction_sum": 0.0,
                "path_aggregated_actual_discarded_weight_raw_sum": 0.0,
                "path_aggregated_unitary_truncation_mass_loss_sum": 0.0,
                "aggregation": {
                    "mode": _SAMPLED_MODE,
                    "weight_source": "uniform_over_explicit_trajectory_count",
                    "trajectory_count": metadata["trajectory_count"],
                    "observed_context_count": 0,
                    "max_observed_sampled_path_fraction_sum": 0.0,
                    "context_complete": True,
                    "not_a_global_error_bound": True,
                },
                "n_truncating_ops": 0,
                "max_observed_bond": int(max_observed_bond),
                "ledger_scope": (
                    "no_explicit_mps_truncation_requested_mixed_local_dims"
                ),
                "epistemic_class": "a/c",
            }
        unbounded_aggregation = {
            **metadata,
            "context_complete": True,
            "coverage_policy": "not_applicable_no_explicit_truncation",
            "coverage_failures": [],
        }
        return {
            "explicit_truncation_requested": False,
            "exact_bond_dimension_sufficient": exact_bond,
            "exact_bond_policy": "unbounded_no_explicit_cap",
            "accepted_as_exact_bond_representation": True,
            "discarded_weight_ledger_complete": True,
            "discarded_weight_sum": 0.0,
            "worst_cut_discarded_weight": 0.0,
            "path_aggregated_local_discarded_fraction_sum": 0.0,
            "path_aggregated_actual_discarded_weight_raw_sum": 0.0,
            "path_aggregated_unitary_truncation_mass_loss_sum": 0.0,
            "aggregation": unbounded_aggregation,
            "n_truncating_ops": 0,
            "max_observed_bond": int(max_observed_bond),
            "ledger_scope": "no_explicit_mps_truncation_requested",
            "epistemic_class": "a",
        }

    if any(dimension != 2 for dimension in dimensions):
        raise ValueError(
            "finite-bond multilevel ledger should fail closed before execution"
        )
    discarded_fraction = [
        _finite_nonnegative(
            event["actual_discarded_weight_fraction_sum"],
            name="actual_discarded_weight_fraction_sum",
        )
        for event in truncation_events
    ]
    discarded_raw = [
        _finite_nonnegative(
            record["actual_discarded_weight_raw"],
            name="actual_discarded_weight_raw",
        )
        for event in truncation_events
        for record in event.get("split_records", ())
    ]
    split_fraction = [
        _finite_nonnegative(
            record["actual_discarded_weight_fraction_of_pre_split"],
            name="actual_discarded_weight_fraction_of_pre_split",
        )
        for event in truncation_events
        for record in event.get("split_records", ())
    ]
    norm_loss = [
        _finite_nonnegative(
            event["unitary_truncation_mass_loss"],
            name="unitary_truncation_mass_loss",
        )
        for event in truncation_events
    ]
    return {
        "explicit_truncation_requested": True,
        "max_bond": normalized_max_bond,
        "exact_bond_dimension_sufficient": exact_bond,
        "exact_bond_policy": (
            "finite_cap_at_or_above_conservative_exact_sufficient_bond"
            if normalized_max_bond >= exact_bond
            else "finite_cap_below_conservative_exact_sufficient_bond"
        ),
        "accepted_as_exact_bond_representation": bool(
            normalized_max_bond >= exact_bond
        ),
        "discarded_weight_ledger_complete": bool(metadata["context_complete"]),
        "ledger_method": "quimb_actual_svd_split_per_two_site_unitary_gate",
        "actual_discarded_weight_raw_sum": float(math.fsum(discarded_raw)),
        "actual_discarded_weight_fraction_sum": float(
            math.fsum(discarded_fraction)
        ),
        "worst_actual_discarded_weight_fraction": float(
            max(split_fraction, default=0.0)
        ),
        "actual_split_count": int(
            sum(int(event["split_count"]) for event in truncation_events)
        ),
        "unitary_truncation_mass_loss_sum": float(math.fsum(norm_loss)),
        "worst_unitary_truncation_mass_loss": float(max(norm_loss, default=0.0)),
        "path_aggregated_local_discarded_fraction_sum": aggregation["fraction"],
        "path_aggregated_actual_discarded_weight_raw_sum": aggregation["raw"],
        "path_aggregated_unitary_truncation_mass_loss_sum": aggregation["norm_loss"],
        "discarded_weight_sum": aggregation["fraction"],
        "worst_cut_discarded_weight": float(max(split_fraction, default=0.0)),
        "discarded_weight_units": "fraction_of_pre_split_weight",
        "compatibility_aliases": {
            "discarded_weight_sum": "path_aggregated_local_discarded_fraction_sum",
            "worst_cut_discarded_weight": "worst_actual_discarded_weight_fraction",
        },
        "not_a_global_error_bound": True,
        "aggregation": metadata,
        "n_truncating_ops": sum(1 for value in discarded_fraction if value > 0.0),
        "n_tracked_two_site_ops": len(truncation_events),
        "max_observed_bond": int(max_observed_bond),
        "truncation_events": truncation_events,
        "ledger_scope": (
            "finite_max_bond_actual_quimb_svd_split_ledger; each local fraction "
            "is relative to that split's pre-split weight and is not a global "
            "state or record error bound"
        ),
        "epistemic_class": "c",
    }


def _validate_actual_split_event(
    event: dict[str, Any],
    *,
    expected_max_bond: int,
    context: str,
) -> None:
    if type(event) is not dict:
        raise TypeError(f"{context} actual-split event must be an exact mapping")
    expected_keys = set(_ACTUAL_SPLIT_EVENT_KEYS)
    if "branch_ordinal" in event:
        expected_keys.add("branch_ordinal")
    if set(event) != expected_keys:
        raise ValueError(f"{context} actual-split event fields are noncanonical")

    def exact_int(value: Any, *, name: str, minimum: int = 0) -> int:
        if type(value) is not int:
            raise TypeError(f"{name} must be an exact integer")
        if value < minimum:
            raise ValueError(f"{name} must be >= {minimum}")
        return value

    def exact_float(
        value: Any,
        *,
        name: str,
        positive: bool = False,
    ) -> float:
        if type(value) is not float:
            raise TypeError(f"{name} must be an exact float")
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
        if value < 0.0 or (positive and value <= 0.0):
            qualifier = "positive" if positive else "nonnegative"
            raise ValueError(f"{name} must be {qualifier}")
        return value

    def exact_text(value: Any, *, name: str) -> str:
        if type(value) is not str or not value:
            raise TypeError(f"{name} must be nonempty exact text")
        return value

    max_bond = exact_int(
        event["max_bond"],
        name=f"{context}.max_bond",
        minimum=1,
    )
    if max_bond != expected_max_bond:
        raise ValueError(f"{context} max_bond disagrees with ledger request")
    support = event["support"]
    if (
        type(support) is not list
        or len(support) != 2
        or any(type(site) is not int or site < 0 for site in support)
        or support[0] == support[1]
    ):
        raise ValueError(f"{context} support must be two distinct exact indices")
    lo, hi = sorted(support)
    gate_leg_sites = event["gate_leg_sites"]
    expected_gate_legs = [lo, lo + 1] if support[0] < support[1] else [lo + 1, lo]
    if gate_leg_sites != expected_gate_legs:
        raise ValueError(f"{context} gate_leg_sites disagree with swap path")
    exact_text(event["substep_id"], name=f"{context}.substep_id")
    exact_text(event["substep_kind"], name=f"{context}.substep_kind")
    exact_int(event["term_index"], name=f"{context}.term_index")
    exact_text(event["operator_family"], name=f"{context}.operator_family")
    branch_prefix = event["branch_record_prefix"]
    if type(branch_prefix) is not list or any(
        type(bit) is not int or bit not in {0, 1} for bit in branch_prefix
    ):
        raise TypeError(f"{context}.branch_record_prefix must be exact bits")
    trajectory_index = event["trajectory_index"]
    if trajectory_index is not None:
        exact_int(
            trajectory_index,
            name=f"{context}.trajectory_index",
        )
    incoming_weight = event["incoming_branch_weight"]
    if incoming_weight is not None:
        incoming_weight = exact_float(
            incoming_weight,
            name=f"{context}.incoming_branch_weight",
        )
        if incoming_weight > 1.0:
            raise ValueError(
                f"{context}.incoming_branch_weight must lie in [0, 1]"
            )
    if trajectory_index is None:
        if incoming_weight is None:
            raise ValueError(f"{context} exact event requires incoming branch weight")
        if "branch_ordinal" not in event:
            raise ValueError(f"{context} exact event requires branch_ordinal")
        exact_int(event["branch_ordinal"], name=f"{context}.branch_ordinal")
    elif incoming_weight is not None:
        raise ValueError(f"{context} sampled event cannot carry branch weight")
    elif "branch_ordinal" in event and event["branch_ordinal"] is not None:
        exact_int(event["branch_ordinal"], name=f"{context}.branch_ordinal")

    backend = exact_text(event["array_backend"], name=f"{context}.array_backend")
    if not backend.startswith("torch_cuda") or not backend.endswith("_complex128"):
        raise ValueError(f"{context}.array_backend is not registered")
    exact_float(event["dt_ns_effective"], name=f"{context}.dt_ns_effective")
    microstep_count = exact_int(
        event["microstep_count"],
        name=f"{context}.microstep_count",
        minimum=1,
    )
    microstep_index = exact_int(
        event["microstep_index"],
        name=f"{context}.microstep_index",
    )
    if microstep_index >= microstep_count:
        raise ValueError(f"{context}.microstep_index lies outside microstep_count")
    exact_int(
        event["hamiltonian_pass_index"],
        name=f"{context}.hamiltonian_pass_index",
    )
    if event["epistemic_class"] != "c":
        raise ValueError(f"{context}.epistemic_class must be c")
    if event["quimb_version"] != "1.14.0":
        raise ValueError(f"{context}.quimb_version is not registered")
    if event["physical_branch_probability"] is not None:
        raise ValueError(f"{context} unitary split cannot claim branch probability")

    split_records = event["split_records"]
    if type(split_records) is not list:
        raise TypeError(f"{context}.split_records must be an exact list")
    split_count = exact_int(event["split_count"], name=f"{context}.split_count")
    expected_split_count = 2 * (hi - lo) - 1
    if split_count != len(split_records) or split_count != expected_split_count:
        raise ValueError(f"{context} split_count disagrees with the swap path")
    forward_count = hi - lo - 1
    expected_roles = (
        ["forward_swap_split"] * forward_count
        + ["two_site_operator_split"]
        + ["reverse_swap_split"] * forward_count
    )
    expected_split_sites = (
        [[site, site + 1] for site in range(hi - 1, lo, -1)]
        + [[lo, lo + 1]]
        + [[site, site + 1] for site in range(lo + 1, hi)]
    )
    expected_absorb = (
        ["left"] * forward_count
        + ["right" if support[0] < support[1] else "left"]
        + ["right"] * forward_count
    )
    split_raw: list[float] = []
    split_fraction: list[float] = []
    for index, record in enumerate(split_records):
        split_context = f"{context}.split_records[{index}]"
        if type(record) is not dict or set(record) != _ACTUAL_SPLIT_RECORD_KEYS:
            raise ValueError(f"{split_context} split fields are noncanonical")
        if exact_int(
            record["sequence_index"],
            name=f"{split_context}.sequence_index",
        ) != index:
            raise ValueError(f"{split_context} sequence_index is noncanonical")
        if record["path_role"] != expected_roles[index]:
            raise ValueError(f"{split_context} path_role is noncanonical")
        if record["split_sites"] != expected_split_sites[index]:
            raise ValueError(f"{split_context} split_sites are noncanonical")
        expected_record_gate_legs = (
            gate_leg_sites
            if expected_roles[index] == "two_site_operator_split"
            else None
        )
        if record["gate_leg_sites"] != expected_record_gate_legs:
            raise ValueError(f"{split_context} gate_leg_sites are noncanonical")
        if record["requested_method"] != "svd":
            raise ValueError(f"{split_context} requested_method must be svd")
        if record["requested_absorb"] != expected_absorb[index]:
            raise ValueError(f"{split_context} requested_absorb is noncanonical")
        if exact_int(
            record["requested_max_bond"],
            name=f"{split_context}.requested_max_bond",
            minimum=1,
        ) != max_bond:
            raise ValueError(f"{split_context} requested max bond disagrees")
        if type(record["requested_cutoff"]) is not float or record[
            "requested_cutoff"
        ] != 0.0:
            raise ValueError(f"{split_context} requested cutoff must be explicit 0.0")
        if record["requested_cutoff_mode"] != "rsum2":
            raise ValueError(f"{split_context} cutoff mode must be rsum2")
        if record["requested_renorm"] is not None:
            raise ValueError(f"{split_context} requested renorm must be None")
        pre_weight = exact_float(
            record["pre_split_total_weight"],
            name=f"{split_context}.pre_split_total_weight",
            positive=True,
        )
        kept_bond = exact_int(
            record["actual_kept_bond_dimension"],
            name=f"{split_context}.actual_kept_bond_dimension",
            minimum=1,
        )
        if kept_bond > max_bond:
            raise ValueError(f"{split_context} kept bond exceeds max_bond")
        raw = exact_float(
            record["actual_discarded_weight_raw"],
            name=f"{split_context}.actual_discarded_weight_raw",
        )
        if raw > pre_weight + 100.0 * NUMERICAL_ZERO * max(1.0, pre_weight):
            raise ValueError(f"{split_context} discarded weight exceeds pre-weight")
        fraction = exact_float(
            record["actual_discarded_weight_fraction_of_pre_split"],
            name=(
                f"{split_context}."
                "actual_discarded_weight_fraction_of_pre_split"
            ),
        )
        if fraction != raw / pre_weight:
            raise ValueError(f"{split_context} discarded fraction identity failed")
        if record["not_a_global_error_bound"] is not True:
            raise ValueError(f"{split_context} must disclaim a global bound")
        split_raw.append(raw)
        split_fraction.append(fraction)

    input_norm = exact_float(
        event["input_norm_sq"],
        name=f"{context}.input_norm_sq",
        positive=True,
    )
    raw_output_norm = exact_float(
        event["raw_output_norm_sq"],
        name=f"{context}.raw_output_norm_sq",
        positive=True,
    )
    if raw_output_norm > input_norm + NUMERICAL_ZERO * max(1.0, input_norm):
        raise ValueError(f"{context} raw output norm exceeds input norm")
    observed_loss = max(0.0, input_norm - raw_output_norm)
    declared_loss = exact_float(
        event["unitary_truncation_mass_loss"],
        name=f"{context}.unitary_truncation_mass_loss",
    )
    if declared_loss != observed_loss:
        raise ValueError(f"{context} unitary norm loss identity failed")
    raw_sum = float(sum(split_raw))
    if exact_float(
        event["actual_discarded_weight_raw_sum"],
        name=f"{context}.actual_discarded_weight_raw_sum",
    ) != raw_sum:
        raise ValueError(f"{context} raw discarded-weight sum identity failed")
    if abs(raw_sum - observed_loss) > (
        100.0 * NUMERICAL_ZERO * max(1.0, input_norm, raw_sum)
    ):
        raise ValueError(f"{context} split ledger disagrees with norm loss")
    restore_factor = exact_float(
        event["deterministic_norm_restore_factor"],
        name=f"{context}.deterministic_norm_restore_factor",
        positive=True,
    )
    if restore_factor != math.sqrt(input_norm / raw_output_norm):
        raise ValueError(f"{context} deterministic norm restore identity failed")
    restored_norm = exact_float(
        event["restored_output_norm_sq"],
        name=f"{context}.restored_output_norm_sq",
        positive=True,
    )
    if not math.isclose(
        restored_norm,
        input_norm,
        rel_tol=NUMERICAL_ZERO,
        abs_tol=NUMERICAL_ZERO,
    ):
        raise ValueError(f"{context} restored output norm is inconsistent")
    fraction_sum = float(sum(split_fraction))
    worst_fraction = float(max(split_fraction, default=0.0))
    for field, expected in (
        ("actual_discarded_weight_fraction_sum", fraction_sum),
        ("worst_actual_discarded_weight_fraction", worst_fraction),
        ("discarded_weight_sum", fraction_sum),
        ("worst_cut_discarded_weight", worst_fraction),
    ):
        if exact_float(event[field], name=f"{context}.{field}") != expected:
            raise ValueError(f"{context}.{field} identity failed")
    if event["ledger_semantics"] != (
        "per_actual_svd_split_heuristic_not_global_bound"
    ):
        raise ValueError(f"{context} ledger_semantics is not registered")
    if event["ledger_method"] != (
        "quimb_actual_svd_split_per_two_site_unitary_gate"
    ):
        raise ValueError(f"{context} ledger_method is not registered")
    if event["discarded_weight_units"] != "fraction_of_pre_split_weight":
        raise ValueError(f"{context} discarded_weight_units are not registered")
    if event["compatibility_aliases"] != {
        "discarded_weight_sum": "actual_discarded_weight_fraction_sum",
        "worst_cut_discarded_weight": (
            "worst_actual_discarded_weight_fraction"
        ),
    }:
        raise ValueError(f"{context} compatibility aliases are noncanonical")
    truncated_count = sum(1 for value in split_raw if value > 0.0)
    if exact_int(
        event["n_truncated_cuts"],
        name=f"{context}.n_truncated_cuts",
    ) != truncated_count:
        raise ValueError(f"{context} n_truncated_cuts is inconsistent")
    if event["not_a_global_error_bound"] is not True:
        raise ValueError(f"{context} must disclaim a global error bound")


def _finite_nonnegative(value: Any, *, name: str) -> float:
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0.0:
        raise ValueError(f"truncation aggregation event {name} must be finite and nonnegative")
    return normalized


def _validate_aggregation_result(aggregation: dict[str, Any]) -> None:
    if not isinstance(aggregation, dict):
        raise TypeError("truncation aggregation result must be a dictionary")
    for key in ("fraction", "raw", "norm_loss"):
        _finite_nonnegative(aggregation.get(key), name=key)
    metadata = aggregation.get("metadata")
    if not isinstance(metadata, dict):
        raise TypeError("truncation aggregation metadata must be a dictionary")
    if metadata.get("mode") not in {_SAMPLED_MODE, _EXACT_MODE}:
        raise ValueError("truncation aggregation metadata has unknown mode")
    if not isinstance(metadata.get("context_complete"), bool):
        raise TypeError("truncation aggregation context_complete must be boolean")


def _payloads_match_exactly(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _payloads_match_exactly(left[key], right[key]) for key in left
        )
    if isinstance(left, (list, tuple)):
        return len(left) == len(right) and all(
            _payloads_match_exactly(left_value, right_value)
            for left_value, right_value in zip(left, right, strict=True)
        )
    return bool(left == right)


def _authenticate_aggregation_against_events(
    events: list[dict[str, Any]],
    *,
    aggregation: dict[str, Any],
) -> None:
    metadata = aggregation["metadata"]
    expected_gate_occurrences = metadata.get("expected_gate_occurrences")
    if not isinstance(expected_gate_occurrences, list):
        raise TypeError(
            "truncation aggregation expected_gate_occurrences must be a list"
        )
    mode = metadata["mode"]
    if mode == _SAMPLED_MODE:
        canonical = aggregate_sampled_truncation_events(
            events,
            trajectory_count=metadata.get("trajectory_count"),
            expected_gate_occurrences=expected_gate_occurrences,
        )
    else:
        canonical = aggregate_exact_branch_truncation_events(
            events,
            expected_gate_occurrences=expected_gate_occurrences,
        )
    if not _payloads_match_exactly(aggregation, canonical):
        raise ValueError(
            "truncation aggregation disagrees with supplied events and route context"
        )


def _aggregate_truncation_events(
    events: list[dict[str, Any]],
    *,
    aggregation_law: str,
    trajectory_count: int | None,
    expected_gate_occurrences: tuple[dict[str, Any], ...] | list[dict[str, Any]],
) -> dict[str, Any]:
    def validate_split_inventory(event: dict[str, Any]) -> None:
        split_records = event.get("split_records")
        if not isinstance(split_records, list):
            raise TypeError("truncation aggregation split_records must be a list")
        split_count = event.get("split_count")
        if isinstance(split_count, bool):
            raise TypeError("truncation aggregation split_count must be integer")
        try:
            normalized_count = operator.index(split_count)
        except TypeError as exc:
            raise TypeError(
                "truncation aggregation split_count must be integer"
            ) from exc
        if normalized_count < 0:
            raise ValueError("truncation aggregation split_count must be nonnegative")
        if normalized_count != len(split_records):
            raise ValueError(
                "truncation aggregation split_count disagrees with split_records"
            )

    def metric(event: dict[str, Any], key: str) -> float:
        return _finite_nonnegative(event[key], name=key)

    def context_integer(
        event: dict[str, Any],
        key: str,
        *,
        minimum: int = 0,
    ) -> int:
        value = event.get(key)
        if isinstance(value, bool):
            raise TypeError(f"truncation aggregation {key} must be integer")
        try:
            normalized = operator.index(value)
        except TypeError as exc:
            raise TypeError(
                f"truncation aggregation requires integer {key}"
            ) from exc
        if normalized < minimum:
            raise ValueError(f"truncation aggregation {key} must be >= {minimum}")
        return int(normalized)

    def occurrence_key(event: dict[str, Any]) -> tuple[Any, ...]:
        substep_id = event.get("substep_id")
        operator_family = event.get("operator_family")
        support_value = event.get("support")
        if not isinstance(substep_id, str) or not substep_id:
            raise ValueError("truncation aggregation requires nonempty substep_id")
        if not isinstance(operator_family, str) or not operator_family:
            raise ValueError(
                "truncation aggregation requires nonempty operator_family"
            )
        if not isinstance(support_value, (list, tuple)) or len(support_value) != 2:
            raise ValueError(
                "truncation aggregation requires two-site support identity"
            )
        support = tuple(
            context_integer({"site": site}, "site") for site in support_value
        )
        if support[0] == support[1]:
            raise ValueError(
                "truncation aggregation support identity requires distinct sites"
            )
        term_index = context_integer(event, "term_index")
        microstep_count = context_integer(event, "microstep_count", minimum=1)
        microstep_index = context_integer(event, "microstep_index")
        if microstep_index >= microstep_count:
            raise ValueError(
                "truncation aggregation microstep_index lies outside microstep_count"
            )
        pass_value = event.get("hamiltonian_pass_index")
        pass_index = (
            None
            if pass_value is None
            else context_integer(event, "hamiltonian_pass_index")
        )
        dt_ns_effective = float(event.get("dt_ns_effective"))
        if not math.isfinite(dt_ns_effective) or dt_ns_effective < 0.0:
            raise ValueError(
                "truncation aggregation dt_ns_effective must be finite and nonnegative"
            )
        return (
            substep_id,
            term_index,
            operator_family,
            support,
            microstep_index,
            microstep_count,
            pass_index,
            dt_ns_effective,
        )

    def occurrence_identity(key: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "substep_id": key[0],
            "term_index": key[1],
            "operator_family": key[2],
            "support": list(key[3]),
            "microstep_index": key[4],
            "microstep_count": key[5],
            "hamiltonian_pass_index": key[6],
            "dt_ns_effective": key[7],
        }

    expected_keys_in_order = [
        occurrence_key(dict(occurrence)) for occurrence in expected_gate_occurrences
    ]
    if any(key[6] is None for key in expected_keys_in_order):
        raise ValueError(
            "expected truncation gate-occurrence inventory requires pass identity"
        )
    expected_keys = set(expected_keys_in_order)
    if len(expected_keys) != len(expected_keys_in_order):
        raise ValueError(
            "expected truncation gate-occurrence inventory contains duplicates"
        )

    for event in events:
        validate_split_inventory(event)

    values = [
        (
            metric(event, "actual_discarded_weight_fraction_sum"),
            metric(event, "actual_discarded_weight_raw_sum"),
            metric(event, "unitary_truncation_mass_loss"),
        )
        for event in events
    ]
    if aggregation_law == _SAMPLED_MODE:
        if isinstance(trajectory_count, bool):
            raise TypeError(
                "truncation aggregation trajectory_count must be an integer"
            )
        try:
            count = operator.index(trajectory_count)
        except TypeError as exc:
            raise TypeError(
                "sampled truncation aggregation requires trajectory_count"
            ) from exc
        if count < 1:
            raise ValueError(
                "sampled truncation aggregation trajectory_count must be positive"
            )
        per_trajectory: dict[int, list[float]] = {}
        occurrence_trajectories: dict[tuple[Any, ...], list[int]] = {}
        for event, triple in zip(events, values, strict=True):
            index_value = event.get("trajectory_index")
            if isinstance(index_value, bool):
                raise TypeError(
                    "truncation aggregation trajectory_index must be integer"
                )
            try:
                index = operator.index(index_value)
            except TypeError as exc:
                raise TypeError(
                    "sampled truncation aggregation requires trajectory_index"
                ) from exc
            if not 0 <= index < count:
                raise ValueError(
                    "sampled truncation aggregation trajectory_index lies outside "
                    f"[0, {count})"
                )
            if event.get("incoming_branch_weight") is not None:
                raise ValueError(
                    "sampled truncation aggregation cannot carry branch weight"
                )
            key = occurrence_key(event)
            occurrence_trajectories.setdefault(key, []).append(index)
            totals = per_trajectory.setdefault(index, [0.0, 0.0, 0.0])
            for offset, value in enumerate(triple):
                totals[offset] += value
        aggregate = tuple(
            float(math.fsum(triple[offset] for triple in values) / count)
            for offset in range(3)
        )
        max_path_fraction = float(
            max((totals[0] for totals in per_trajectory.values()), default=0.0)
        )
        weight_source = "uniform_over_explicit_trajectory_count"
        observed_contexts = len(per_trajectory)
        coverage_failures: list[dict[str, Any]] = []
        complete_occurrence_keys: set[tuple[Any, ...]] = set()
        expected_trajectories = set(range(count))
        for key, trajectory_indices in occurrence_trajectories.items():
            observed_trajectories = set(trajectory_indices)
            missing_count = len(expected_trajectories - observed_trajectories)
            duplicate_count = len(trajectory_indices) - len(observed_trajectories)
            identity_complete = key[6] is not None
            if missing_count == 0 and duplicate_count == 0 and identity_complete:
                complete_occurrence_keys.add(key)
                continue
            reasons = []
            if not identity_complete:
                reasons.append("gate_occurrence_identity_incomplete")
            if missing_count or duplicate_count:
                reasons.append("sampled_trajectory_coverage_incomplete")
            coverage_failures.append(
                {
                    **occurrence_identity(key),
                    "reason": "+".join(reasons),
                    "observed_trajectory_count": len(observed_trajectories),
                    "missing_trajectory_count": missing_count,
                    "duplicate_event_count": duplicate_count,
                }
            )
        observed_occurrence_keys = set(occurrence_trajectories)
        per_occurrence_coverage_policy = (
            "every_gate_occurrence_has_exactly_one_event_per_declared_trajectory"
        )
    elif aggregation_law == _EXACT_MODE:
        if trajectory_count is not None:
            raise ValueError(
                "exact branch truncation aggregation requires trajectory_count=None"
            )
        weighted: list[tuple[float, float, float]] = []
        occurrence_branches: dict[tuple[Any, ...], list[tuple[int, float]]] = {}
        for event, triple in zip(events, values, strict=True):
            if event.get("trajectory_index") is not None:
                raise ValueError(
                    "exact branch truncation aggregation cannot carry trajectory_index"
                )
            weight = float(event.get("incoming_branch_weight"))
            if (
                not math.isfinite(weight)
                or weight < 0.0
                or weight > 1.0
            ):
                raise ValueError(
                    "exact branch truncation aggregation branch weight must be "
                    f"finite and lie in [0, 1], got {weight!r}"
                )
            branch_ordinal = event.get("branch_ordinal")
            if isinstance(branch_ordinal, bool):
                raise TypeError(
                    "exact branch aggregation branch_ordinal must be integer"
                )
            try:
                ordinal = operator.index(branch_ordinal)
            except TypeError as exc:
                raise TypeError(
                    "exact branch truncation aggregation requires branch_ordinal"
                ) from exc
            if ordinal < 0 or not isinstance(event.get("branch_record_prefix"), list):
                raise ValueError(
                    "exact branch truncation aggregation context is incomplete"
                )
            key = occurrence_key(event)
            occurrence_branches.setdefault(key, []).append((int(ordinal), weight))
            weighted.append(tuple(weight * value for value in triple))
        aggregate = tuple(
            float(math.fsum(triple[offset] for triple in weighted))
            for offset in range(3)
        )
        max_path_fraction = None
        weight_source = "incoming_branch_weight"
        observed_contexts = len(events)
        coverage_failures = []
        complete_occurrence_keys = set()
        for key, branch_entries in occurrence_branches.items():
            ordinals = [ordinal for ordinal, _weight in branch_entries]
            unique_ordinals = set(ordinals)
            branch_mass = float(
                math.fsum(weight for _ordinal, weight in branch_entries)
            )
            ordinal_complete = sorted(unique_ordinals) == list(
                range(len(branch_entries))
            ) and len(unique_ordinals) == len(branch_entries)
            mass_complete = abs(branch_mass - 1.0) <= NUMERICAL_ZERO
            identity_complete = key[6] is not None
            if ordinal_complete and mass_complete and identity_complete:
                complete_occurrence_keys.add(key)
                continue
            reasons = []
            if not identity_complete:
                reasons.append("gate_occurrence_identity_incomplete")
            if not ordinal_complete:
                reasons.append("exact_branch_ordinal_coverage_incomplete")
            if not mass_complete:
                reasons.append("exact_branch_mass_not_unity")
            coverage_failures.append(
                {
                    **occurrence_identity(key),
                    "reason": "+".join(reasons),
                    "observed_branch_count": len(branch_entries),
                    "unique_branch_ordinal_count": len(unique_ordinals),
                    "incoming_branch_weight_sum": branch_mass,
                    "unit_mass_tolerance": NUMERICAL_ZERO,
                }
            )
        observed_occurrence_keys = set(occurrence_branches)
        per_occurrence_coverage_policy = (
            "every_gate_occurrence_has_unique_contiguous_branch_ordinals_and_"
            "unit_incoming_branch_mass"
        )
    else:  # pragma: no cover - only explicit public wrappers select a law.
        raise RuntimeError(f"unsupported private truncation law {aggregation_law!r}")

    missing_occurrences = expected_keys - observed_occurrence_keys
    unexpected_occurrences = observed_occurrence_keys - expected_keys
    coverage_failures.extend(
        {
            **occurrence_identity(key),
            "reason": "expected_gate_occurrence_missing",
        }
        for key in sorted(missing_occurrences, key=repr)
    )
    coverage_failures.extend(
        {
            **occurrence_identity(key),
            "reason": "unexpected_gate_occurrence_observed",
        }
        for key in sorted(unexpected_occurrences, key=repr)
    )
    occurrence_count = len(observed_occurrence_keys)
    complete_occurrence_count = len(complete_occurrence_keys & expected_keys)
    context_complete = not coverage_failures
    coverage_policy = (
        "observed_gate_occurrence_identities_exactly_match_precomputed_inventory_and_"
        + per_occurrence_coverage_policy
    )
    return {
        "fraction": aggregate[0],
        "raw": aggregate[1],
        "norm_loss": aggregate[2],
        "metadata": {
            "mode": aggregation_law,
            "weight_source": weight_source,
            "trajectory_count": trajectory_count,
            "observed_context_count": int(observed_contexts),
            "expected_gate_occurrence_count": int(len(expected_keys_in_order)),
            "expected_gate_occurrences": [
                occurrence_identity(key) for key in expected_keys_in_order
            ],
            "observed_gate_occurrence_count": int(occurrence_count),
            "complete_gate_occurrence_count": int(complete_occurrence_count),
            "max_observed_sampled_path_fraction_sum": max_path_fraction,
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
            "coverage_policy": coverage_policy,
            "coverage_failures": coverage_failures,
            "context_complete": bool(context_complete),
            "not_a_global_error_bound": True,
        },
    }
