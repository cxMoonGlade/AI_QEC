"""Deep authentication firewall for QT/MPS aggregate evidence.

These tests exercise the public bundle constructor with internally consistent,
rehashable child manifests.  A self-hash is not authority: the parent must
independently bind the retained raw evidence to the requested schedule and to
the restricted scientific policy.
"""

from __future__ import annotations

import copy
from typing import Any, Callable

import pytest

from test_mps_qt_transitive_semantics import (
    _accepted_bundle,
    _accepted_sweeps,
    _bundle_request,
    _install_fake_cuda,
    _install_sweeps,
    _rehash,
    _resource_request,
)


def _accepted_resource_manifest(
    monkeypatch: pytest.MonkeyPatch,
    qt: Any,
) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    schedule, bundle = _accepted_bundle(monkeypatch, qt)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_evidence_bundle_manifest",
        lambda *_args, **_kwargs: bundle,
    )
    _install_fake_cuda(monkeypatch, qt)
    return schedule, bundle, _resource_request(qt, schedule)


def _validate_resource_manifest(
    qt: Any,
    manifest: dict[str, Any],
    *,
    schedule: Any,
    bundle: dict[str, Any],
) -> None:
    qt._validate_qt_resource_probe_manifest(
        manifest,
        expected_schedule=schedule,
        expected_bundle=bundle,
        expected_bonds=(1, 2),
        expected_trajectory_count=5,
        expected_seeds=(3, 7),
        expected_device="cuda",
        expected_max_branches=4096,
        expected_max_record_materialization_outcomes=4096,
        expected_microstep_count=1,
        expected_finite_step_order="first_order",
        expected_convergence_record_probability_gate=0.0,
        expected_seed_record_frequency_spread_gate=0.0,
        expected_dense_record_frequency_gate=0.0,
        expected_worst_cut_discarded_weight_gate=None,
        expected_total_discarded_weight_gate=None,
        expected_min_peak_allocated_gib=None,
        expected_min_peak_reserved_gib=None,
        expected_peak_allocated_bytes=1,
        expected_peak_reserved_bytes=1,
        expected_bundle_backend_executed=True,
    )


def _install_counted_bundle_child(
    monkeypatch: pytest.MonkeyPatch,
    qt: Any,
    bundle: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, int]]:
    expected_bundle = copy.deepcopy(bundle)
    calls = {"bundle": 0}

    def bundle_child(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        calls["bundle"] += 1
        return bundle

    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_evidence_bundle_manifest",
        bundle_child,
    )
    return expected_bundle, calls


def _assert_forged_sweeps_rejected(
    monkeypatch: pytest.MonkeyPatch,
    qt: Any,
    mutate: Callable[[dict[str, Any], dict[str, Any]], None],
) -> None:
    """Build and forge children before asserting only the bundle rejection.

    Keeping accepted-child construction, the mutation, and rehashing outside
    ``pytest.raises`` prevents a broken fixture or mutation callback from
    satisfying the rejection assertion.  The bundle must consume each exact
    forged child once and must not repair either payload in place.
    """

    schedule, bond, seed = _accepted_sweeps(monkeypatch, qt)
    mutate(bond, seed)
    _rehash(qt, bond)
    _rehash(qt, seed)
    expected_bond = copy.deepcopy(bond)
    expected_seed = copy.deepcopy(seed)
    child_calls = {"bond": 0, "seed": 0}

    def bond_child(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        child_calls["bond"] += 1
        return bond

    def seed_child(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        child_calls["seed"] += 1
        return seed

    monkeypatch.setattr(qt, "axis1_qt_mps_bond_sweep_manifest", bond_child)
    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_trajectory_seed_sweep_manifest",
        seed_child,
    )

    with pytest.raises((TypeError, ValueError)):
        _bundle_request(qt, schedule)

    assert child_calls == {"bond": 1, "seed": 1}
    assert bond == expected_bond
    assert seed == expected_seed


def _assert_bond_sweep_rejects_forged_dense_child(
    monkeypatch: pytest.MonkeyPatch,
    qt: Any,
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    from test_mps_qt_aggregate_binding import (
        _dense_record_oracle_payload,
        _direct_child,
    )
    from test_mps_qt_transitive_semantics import _measurement_schedule

    schedule = _measurement_schedule()
    dense = _dense_record_oracle_payload(qt, schedule, device="cuda")
    mutate(dense)
    _rehash(qt, dense)
    expected_dense = copy.deepcopy(dense)
    dense_calls = 0

    def dense_child(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal dense_calls
        dense_calls += 1
        return copy.deepcopy(dense)

    monkeypatch.setattr(
        qt,
        "axis1_measurement_record_evidence_manifest",
        dense_child,
    )

    def direct_child(schedule_arg: Any, **kwargs: Any) -> dict[str, Any]:
        child = _direct_child(
            qt,
            schedule_arg,
            **kwargs,
        )
        certification = child["dense_jointL_record_certification"]
        if certification["executed"]:
            certification["dense_evidence_content_hash"] = dense["content_hash"]
        return _rehash(qt, child)

    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        direct_child,
    )

    with pytest.raises((TypeError, ValueError)):
        qt.axis1_qt_mps_bond_sweep_manifest(
            schedule,
            bond_values=(1, 2),
            convergence_record_probability_gate=0.0,
        )

    assert dense_calls == 1
    assert dense == expected_dense


def _sync_bond_run(
    qt: Any,
    bond: dict[str, Any],
    index: int,
) -> None:
    run = bond["runs"][index]
    _rehash(qt, run)
    bond["run_summaries"][index] = qt._bond_sweep_run_summary(run)


def _sync_seed_run(
    qt: Any,
    seed: dict[str, Any],
    index: int,
) -> None:
    run = seed["runs"][index]
    _rehash(qt, run)
    seed["run_summaries"][index] = qt._trajectory_seed_sweep_run_summary(run)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (
            "scored_quantity_policy",
            "forged scored quantity claim",
        ),
        (
            "approximation_book",
            {"schema": "forged.approximation_book.v1"},
        ),
        (
            "epistemic_classes",
            {"restricted_mps_execution": "a"},
        ),
        (
            "scope",
            "forged unrestricted scope",
        ),
        (
            "blocked_substeps",
            [{"reason": "forged completed-run blocker"}],
        ),
        (
            "unregistered_top_level_claim",
            False,
        ),
    ],
)
def test_bundle_rejects_rehashed_direct_metadata_forgery(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_metadata(
        _bond: dict[str, Any],
        seed: dict[str, Any],
    ) -> None:
        seed["runs"][0][field] = value
        _sync_seed_run(qt, seed, 0)

    _assert_forged_sweeps_rejected(monkeypatch, qt, forge_metadata)


@pytest.mark.parametrize(
    "corruption",
    [
        "mps_execution",
        "dense_certification",
        "acceptance_policy",
        "blocked_reason",
    ],
)
def test_bond_sweep_rejects_rehashed_noncanonical_blocked_child(
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt
    from test_mps_qt_aggregate_binding import (
        _unsupported_measurement_schedule,
    )

    schedule = _unsupported_measurement_schedule()
    monkeypatch.setattr(qt, "_require_cuda_device", lambda _device: "cuda")
    original = qt.axis1_qt_mps_restricted_execution_manifest

    forged_children: dict[int, dict[str, Any]] = {}
    for bond in (1, 2):
        child = original(
            schedule,
            device="cuda",
            max_bond=bond,
            max_branches=4096,
            max_record_materialization_outcomes=4096,
            microstep_count=1,
            finite_step_order="first_order",
            worst_cut_discarded_weight_gate=None,
            total_discarded_weight_gate=None,
            trajectory_count=None,
            rng_seed=None,
            dense_oracle_certification=True,
        )
        if corruption == "mps_execution":
            child["mps_execution"] = {"unexpected": True}
        elif corruption == "dense_certification":
            child["dense_jointL_record_certification"]["extra"] = False
        elif corruption == "acceptance_policy":
            child["restricted_acceptance_policy"]["extra"] = False
        else:
            child["blocked_reason"] = "forged_blocked_reason"
            child["restricted_acceptance_policy"][
                "blocked_reason"
            ] = "forged_blocked_reason"
            child["dense_jointL_record_certification"][
                "blocked_reason"
            ] = "forged_blocked_reason"
        forged_children[bond] = _rehash(qt, child)
    expected_children = copy.deepcopy(forged_children)
    child_calls: list[int] = []

    def blocked_child(_schedule_arg: Any, **kwargs: Any) -> dict[str, Any]:
        bond = int(kwargs["max_bond"])
        child_calls.append(bond)
        return forged_children[bond]

    monkeypatch.setattr(
        qt,
        "axis1_qt_mps_restricted_execution_manifest",
        blocked_child,
    )
    with pytest.raises((TypeError, ValueError)):
        qt.axis1_qt_mps_bond_sweep_manifest(
            schedule,
            bond_values=(1, 2),
        )
    assert child_calls == [1, 2]
    assert forged_children == expected_children


@pytest.mark.parametrize(
    ("path", "value"),
    [
        pytest.param(
            ("claims_production_scalable_backend",),
            True,
            id="production-claim",
        ),
        pytest.param(
            ("claims_dense_channel_evidence",),
            True,
            id="dense-channel-claim",
        ),
        pytest.param(
            ("exact_joint_generator_claim",),
            True,
            id="joint-generator-claim",
        ),
        pytest.param(
            ("exact_summed_lindbladian_claim",),
            True,
            id="summed-generator-claim",
        ),
        pytest.param(
            ("finite_step_policy", "exact_summed_lindbladian_claim"),
            True,
            id="finite-step-generator-claim",
        ),
        pytest.param(
            ("finite_step_policy", "comparison_outcome_is_metric"),
            True,
            id="finite-step-metric-claim",
        ),
        pytest.param(
            ("physical_dimension",),
            2.0,
            id="physical-dimension-type-smuggling",
        ),
        pytest.param(
            ("mps_library",),
            "forged.mps.Library",
            id="mps-library",
        ),
        pytest.param(
            ("array_backend",),
            "numpy_complex128",
            id="array-backend",
        ),
        pytest.param(
            ("measurement_basis",),
            "X",
            id="measurement-basis",
        ),
        pytest.param(
            ("trajectory_sampling", "rng_backend"),
            "forged.Generator",
            id="rng-backend",
        ),
        pytest.param(
            ("total_probability_residual",),
            1.0e-12,
            id="probability-residual-not-recomputed",
        ),
        pytest.param(
            ("applied_substeps",),
            [],
            id="missing-applied-substeps",
        ),
    ],
)
def test_bundle_rejects_rehashed_nested_execution_promotion(
    monkeypatch: pytest.MonkeyPatch,
    path: tuple[str, ...],
    value: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def promote(_bond: dict[str, Any], seed: dict[str, Any]) -> None:
        target: dict[str, Any] = seed["runs"][0]["mps_execution"]
        for field in path[:-1]:
            target = target[field]
        target[path[-1]] = value
        _sync_seed_run(qt, seed, 0)

    _assert_forged_sweeps_rejected(monkeypatch, qt, promote)


@pytest.mark.parametrize(
    "field",
    [
        "truncation_events",
        "actual_split_count",
        "ledger_method",
        "exact_bond_policy",
        "expected_gate_occurrences",
    ],
)
def test_bundle_rejects_rehashed_noncanonical_actual_split_ledger(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_ledger(bond: dict[str, Any], _seed: dict[str, Any]) -> None:
        ledger = bond["runs"][-1]["mps_execution"]["mps_truncation_ledger"]
        if field == "truncation_events":
            ledger.pop(field)
        elif field == "actual_split_count":
            ledger[field] = 1
        elif field == "ledger_method":
            ledger[field] = "forged_summary_only_ledger"
        elif field == "exact_bond_policy":
            ledger[field] = "forged_exact_bond"
        else:
            ledger["aggregation"][field] = [{}]
        _sync_bond_run(qt, bond, -1)

    _assert_forged_sweeps_rejected(monkeypatch, qt, forge_ledger)


def test_bundle_rejects_impossible_static_branch_upper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_branch_count(
        bond: dict[str, Any],
        _seed: dict[str, Any],
    ) -> None:
        bond["runs"][0]["mps_execution"]["applied_substeps"][0][
            "static_branch_count_upper_bound_after_substep"
        ] = 999
        _sync_bond_run(qt, bond, 0)

    _assert_forged_sweeps_rejected(monkeypatch, qt, forge_branch_count)


def test_bundle_rejects_forged_static_branch_upper_below_exact_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_branch_count(
        bond: dict[str, Any],
        _seed: dict[str, Any],
    ) -> None:
        bond["runs"][0]["mps_execution"]["applied_substeps"][0][
            "static_branch_count_upper_bound_after_substep"
        ] = 3
        _sync_bond_run(qt, bond, 0)

    _assert_forged_sweeps_rejected(monkeypatch, qt, forge_branch_count)


def test_bundle_rejects_legacy_observed_branch_count_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def add_legacy_field(
        bond: dict[str, Any],
        _seed: dict[str, Any],
    ) -> None:
        bond["runs"][0]["mps_execution"]["applied_substeps"][0][
            "branch_count_after_substep"
        ] = 1
        _sync_bond_run(qt, bond, 0)

    _assert_forged_sweeps_rejected(monkeypatch, qt, add_legacy_field)


def test_sampled_applied_substeps_do_not_claim_exact_branch_upper(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    _schedule, _bond, seed = _accepted_sweeps(monkeypatch, qt)
    for run in seed["runs"]:
        assert all(
            "static_branch_count_upper_bound_after_substep" not in entry
            and "branch_count_after_substep" not in entry
            for entry in run["mps_execution"]["applied_substeps"]
        )


@pytest.mark.parametrize(
    ("substep", "current", "microsteps", "cap", "expected"),
    [
        (
            {
                "substep_kind": "reset",
                "terms": [],
                "operation_records": [{"targets": [0, 1]}],
            },
            1,
            1,
            64,
            4,
        ),
        (
            {
                "substep_kind": "idle",
                "terms": [
                    {"kind": "collapse", "coefficient": 1.0},
                    {"kind": "collapse", "coefficient": 2.0},
                ],
                "operation_records": [],
            },
            1,
            2,
            64,
            16,
        ),
        (
            {
                "substep_kind": "measurement",
                "terms": [{"kind": "collapse", "coefficient": 1.0}],
                "operation_records": [
                    {"measurement_keys": ["m0", "m1"]}
                ],
            },
            1,
            2,
            64,
            16,
        ),
        (
            {
                "substep_kind": "reset",
                "terms": [],
                "operation_records": [{"targets": [0, 1]}],
            },
            4,
            1,
            8,
            8,
        ),
    ],
)
def test_static_exact_branch_upper_is_program_derived(
    substep: dict[str, Any],
    current: int,
    microsteps: int,
    cap: int,
    expected: int,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    assert qt._static_exact_branch_upper_after_substep(
        current,
        substep=substep,
        microstep_count=microsteps,
        max_branches=cap,
    ) == expected


def test_bundle_rejects_impossible_sampled_collapse_count_diagnostic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_collapse_count(
        _bond: dict[str, Any],
        seed: dict[str, Any],
    ) -> None:
        seed["runs"][0]["mps_execution"]["applied_substeps"][0][
            "sampled_collapse_term_count"
        ] = 999
        _sync_seed_run(qt, seed, 0)

    _assert_forged_sweeps_rejected(monkeypatch, qt, forge_collapse_count)


def test_bundle_rejects_impossible_rehashed_max_observed_bond(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_max_bond(
        _bond: dict[str, Any],
        seed: dict[str, Any],
    ) -> None:
        run = seed["runs"][0]
        execution = run["mps_execution"]
        execution["applied_substeps"][0][
            "max_observed_bond_after_substep"
        ] = 999
        execution["mps_truncation_ledger"]["max_observed_bond"] = 999
        _sync_seed_run(qt, seed, 0)

    _assert_forged_sweeps_rejected(monkeypatch, qt, forge_max_bond)


def test_bundle_rejects_typed_carrier_program_smuggling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def smuggle_program(bond: dict[str, Any], _seed: dict[str, Any]) -> None:
        run = bond["runs"][0]
        run["carrier_program"]["substep_count"] = float(
            run["carrier_program"]["substep_count"]
        )
        _sync_bond_run(qt, bond, 0)

    _assert_forged_sweeps_rejected(monkeypatch, qt, smuggle_program)


@pytest.mark.parametrize("sweep_name", ["bond", "seed"])
def test_bundle_rejects_extra_claim_in_nested_calibration(
    monkeypatch: pytest.MonkeyPatch,
    sweep_name: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def promote_calibration(
        bond: dict[str, Any],
        seed: dict[str, Any],
    ) -> None:
        calibration = (
            bond["convergence_policy"]["reference_dense_calibration"]
            if sweep_name == "bond"
            else seed["seed_sweep_policy"]["dense_reference_calibration"]
        )
        calibration["accepted_for_production_scalable_backend"] = True

    _assert_forged_sweeps_rejected(
        monkeypatch,
        qt,
        promote_calibration,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("epistemic_class", "a"),
        ("accepted_for_production_scalable_backend", True),
    ],
)
def test_resource_rejects_rehashed_bundle_policy_promotion(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: Any,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bundle = _accepted_bundle(monkeypatch, qt)
    bundle["bundle_policy"][field] = value
    _rehash(qt, bundle)
    expected_bundle, child_calls = _install_counted_bundle_child(
        monkeypatch,
        qt,
        bundle,
    )
    _install_fake_cuda(monkeypatch, qt)
    with pytest.raises((TypeError, ValueError)):
        _resource_request(qt, schedule)
    assert child_calls == {"bundle": 1}
    assert bundle == expected_bundle


@pytest.mark.parametrize("sweep_name", ["bond", "seed"])
def test_bundle_rejects_rehashed_sweep_extra_top_level_field(
    monkeypatch: pytest.MonkeyPatch,
    sweep_name: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def add_extra(
        bond: dict[str, Any],
        seed: dict[str, Any],
    ) -> None:
        target = bond if sweep_name == "bond" else seed
        target["unregistered_top_level_claim"] = False

    _assert_forged_sweeps_rejected(monkeypatch, qt, add_extra)


def test_resource_rejects_rehashed_bundle_extra_top_level_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bundle = _accepted_bundle(monkeypatch, qt)
    bundle["unregistered_top_level_claim"] = False
    _rehash(qt, bundle)
    expected_bundle, child_calls = _install_counted_bundle_child(
        monkeypatch,
        qt,
        bundle,
    )
    _install_fake_cuda(monkeypatch, qt)

    with pytest.raises((TypeError, ValueError)):
        _resource_request(qt, schedule)
    assert child_calls == {"bundle": 1}
    assert bundle == expected_bundle


def test_resource_rejects_rehashed_bundle_missing_top_level_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bundle = _accepted_bundle(monkeypatch, qt)
    bundle.pop("scored_quantity_policy")
    _rehash(qt, bundle)
    expected_bundle, child_calls = _install_counted_bundle_child(
        monkeypatch,
        qt,
        bundle,
    )
    _install_fake_cuda(monkeypatch, qt)

    with pytest.raises((TypeError, ValueError)):
        _resource_request(qt, schedule)
    assert child_calls == {"bundle": 1}
    assert bundle == expected_bundle


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(
            lambda manifest: manifest.__setitem__(
                "unregistered_top_level_claim", False
            ),
            id="extra-field",
        ),
        pytest.param(
            lambda manifest: manifest.pop("scored_quantity_policy"),
            id="missing-field",
        ),
    ],
)
def test_resource_probe_validator_rejects_rehashed_unregistered_top_level_shape(
    monkeypatch: pytest.MonkeyPatch,
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bundle, manifest = _accepted_resource_manifest(
        monkeypatch,
        qt,
    )
    assert len(manifest) == 39
    mutate(manifest)
    _rehash(qt, manifest)
    expected_manifest = copy.deepcopy(manifest)
    expected_bundle = copy.deepcopy(bundle)

    with pytest.raises((TypeError, ValueError)):
        _validate_resource_manifest(
            qt,
            manifest,
            schedule=schedule,
            bundle=bundle,
        )
    assert manifest == expected_manifest
    assert bundle == expected_bundle


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(
            lambda manifest: manifest.__setitem__(
                "workload_schema", "forged.bundle.v1"
            ),
            id="workload-schema",
        ),
        pytest.param(
            lambda manifest: manifest.__setitem__(
                "workload_content_hash", "0" * 64
            ),
            id="workload-content-hash",
        ),
        pytest.param(
            lambda manifest: manifest.__setitem__("workload_passed", False),
            id="workload-passed",
        ),
        pytest.param(
            lambda manifest: manifest["resource_probe_policy"].__setitem__(
                "peak_allocated_bytes", 2
            ),
            id="resource-policy",
        ),
        pytest.param(
            lambda manifest: manifest.__setitem__(
                "claims_qt_mps_backend_execution", False
            ),
            id="backend-claim",
        ),
        pytest.param(
            lambda manifest: manifest.__setitem__(
                "claims_production_scalable_backend", True
            ),
            id="production-claim",
        ),
        pytest.param(
            lambda manifest: (
                manifest.__setitem__("passed", False),
                manifest.__setitem__("verdict", "fail"),
            ),
            id="passed-and-verdict",
        ),
        pytest.param(
            lambda manifest: manifest.__setitem__("verdict", "fail"),
            id="verdict",
        ),
    ],
)
def test_resource_probe_validator_rejects_rehashed_semantic_forgery(
    monkeypatch: pytest.MonkeyPatch,
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bundle, manifest = _accepted_resource_manifest(
        monkeypatch,
        qt,
    )
    mutate(manifest)
    _rehash(qt, manifest)
    expected_manifest = copy.deepcopy(manifest)
    expected_bundle = copy.deepcopy(bundle)

    with pytest.raises((TypeError, ValueError)):
        _validate_resource_manifest(
            qt,
            manifest,
            schedule=schedule,
            bundle=bundle,
        )
    assert manifest == expected_manifest
    assert bundle == expected_bundle


def test_resource_probe_validator_rejects_unauthenticated_content_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    schedule, bundle, manifest = _accepted_resource_manifest(
        monkeypatch,
        qt,
    )
    manifest["content_hash"] = "0" * 64
    expected_manifest = copy.deepcopy(manifest)
    expected_bundle = copy.deepcopy(bundle)

    with pytest.raises((TypeError, ValueError)):
        _validate_resource_manifest(
            qt,
            manifest,
            schedule=schedule,
            bundle=bundle,
        )
    assert manifest == expected_manifest
    assert bundle == expected_bundle


def test_bundle_rejects_promoted_dense_record_child_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt
    from test_mps_qt_aggregate_binding import _dense_record_oracle_payload

    schedule, bond, seed = _accepted_sweeps(monkeypatch, qt)
    dense = _dense_record_oracle_payload(qt, schedule, device="cuda")
    dense["record_evidence"]["claims_full_schedule_coverage"] = True
    _rehash(qt, dense)
    expected_dense = copy.deepcopy(dense)
    dense_calls = 0

    def dense_child(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal dense_calls
        dense_calls += 1
        return copy.deepcopy(dense)

    monkeypatch.setattr(
        qt,
        "axis1_measurement_record_evidence_manifest",
        dense_child,
    )
    _install_sweeps(monkeypatch, qt, bond=bond, seed=seed)
    with pytest.raises((TypeError, ValueError)):
        _bundle_request(qt, schedule)
    assert dense_calls == 1
    assert dense == expected_dense


def test_bond_sweep_rejects_rehashed_dense_record_initial_state_forgery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    _assert_bond_sweep_rejects_forged_dense_child(
        monkeypatch,
        qt,
        lambda dense: dense["record_evidence"].__setitem__(
            "initial_state",
            "forged_nonzero_dense_state",
        ),
    )


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(
            lambda dense: dense.__setitem__("unregistered_claim", False),
            id="extra-top-level-field",
        ),
        pytest.param(
            lambda dense: dense["record_evidence"].__setitem__(
                "unregistered_record_claim",
                False,
            ),
            id="extra-record-field",
        ),
        pytest.param(
            lambda dense: dense["record_evidence"].pop(
                "detector_observable_boundary"
            ),
            id="missing-record-field",
        ),
    ],
)
def test_bond_sweep_rejects_rehashed_dense_record_unregistered_shape(
    monkeypatch: pytest.MonkeyPatch,
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    _assert_bond_sweep_rejects_forged_dense_child(monkeypatch, qt, mutate)


@pytest.mark.parametrize("sweep_name", ["bond", "seed"])
def test_bundle_rejects_sweep_without_full_direct_runs(
    monkeypatch: pytest.MonkeyPatch,
    sweep_name: str,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def remove_runs(bond: dict[str, Any], seed: dict[str, Any]) -> None:
        (bond if sweep_name == "bond" else seed).pop("runs")

    _assert_forged_sweeps_rejected(monkeypatch, qt, remove_runs)


def test_bundle_rejects_rehashed_full_bond_run_source_forgery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_source(bond: dict[str, Any], _seed: dict[str, Any]) -> None:
        bond["runs"][0]["source_hash"] = "f" * 64
        _sync_bond_run(qt, bond, 0)

    _assert_forged_sweeps_rejected(monkeypatch, qt, forge_source)


def test_bundle_rejects_rehashed_full_seed_run_request_forgery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_seed(_bond: dict[str, Any], seed: dict[str, Any]) -> None:
        run = seed["runs"][0]
        run["rng_seed"] = 101
        run["mps_execution"]["trajectory_sampling"]["rng_seed"] = 101
        _sync_seed_run(qt, seed, 0)

    _assert_forged_sweeps_rejected(monkeypatch, qt, forge_seed)


def test_bundle_rejects_rehashed_full_run_truncation_contradiction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_truncation(bond: dict[str, Any], _seed: dict[str, Any]) -> None:
        ledger = bond["runs"][-1]["mps_execution"]["mps_truncation_ledger"]
        ledger.update(
            discarded_weight_sum=0.75,
            worst_cut_discarded_weight=0.75,
            n_truncating_ops=1,
            accepted_as_exact_bond_representation=True,
        )
        _sync_bond_run(qt, bond, -1)

    _assert_forged_sweeps_rejected(monkeypatch, qt, forge_truncation)


def test_bundle_rejects_rehashed_full_run_dense_certification_forgery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_dense(bond: dict[str, Any], _seed: dict[str, Any]) -> None:
        certification = bond["runs"][-1][
            "dense_jointL_record_certification"
        ]
        certification.update(
            dense_evidence_schema="forged.record.schema",
            dense_evidence_content_hash="f" * 64,
            max_abs_probability_difference=1.0,
            passed=True,
        )
        _sync_bond_run(qt, bond, -1)

    _assert_forged_sweeps_rejected(monkeypatch, qt, forge_dense)


def test_bundle_rejects_rehashed_run_records_with_forged_frozen_layout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_layout(bond: dict[str, Any], seed: dict[str, Any]) -> None:
        for sweep in (bond, seed):
            for summary in sweep["run_summaries"]:
                summary["measurement_keys"] = ["forged0", "forged1"]
                summary["measurement_targets"] = [1, 0]

    _assert_forged_sweeps_rejected(monkeypatch, qt, forge_layout)


def test_bundle_rejects_rehashed_run_with_forged_carrier_program(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_program(bond: dict[str, Any], seed: dict[str, Any]) -> None:
        for sweep in (bond, seed):
            for summary in sweep["run_summaries"]:
                program = summary["carrier_program"]
                program["content_hash"] = "forged-program"
                program["backend_contract"] = "forged-backend"
                program["routes"] = ["forged-route"]

    _assert_forged_sweeps_rejected(monkeypatch, qt, forge_program)


def test_bundle_rejects_non_sha_direct_run_content_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_hash(bond: dict[str, Any], _seed: dict[str, Any]) -> None:
        bond["run_summaries"][0]["content_hash"] = "not-a-sha256"

    _assert_forged_sweeps_rejected(monkeypatch, qt, forge_hash)


def test_bundle_rejects_direct_run_truncation_acceptance_contradiction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_truncation(bond: dict[str, Any], _seed: dict[str, Any]) -> None:
        reference = bond["run_summaries"][-1]
        reference["discarded_weight_sum"] = 0.75
        reference["worst_cut_discarded_weight"] = 0.75
        reference["accepted_as_exact_bond_representation"] = True

    _assert_forged_sweeps_rejected(monkeypatch, qt, forge_truncation)


def test_bundle_rejects_contradictory_bond_dense_certification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def forge_dense_certification(
        bond: dict[str, Any], _seed: dict[str, Any]
    ) -> None:
        certification = bond["run_summaries"][-1][
            "dense_jointL_record_certification"
        ]
        certification.update(
            {
                "executed": True,
                "passed": True,
                "dense_evidence_schema": "forged.record.schema",
                "dense_evidence_content_hash": "not-a-sha256",
                "comparison_object": "forged-comparison",
                "max_abs_probability_difference": 1.0,
                "threshold": 0.0,
                "comparison_outcome_is_metric": False,
            }
        )
        bond["convergence_policy"]["reference_dense_calibration"] = {
            "status": "passed",
            "executed": True,
            "passed": True,
            "accepted_as_dense_calibrated_reference": True,
            "dense_evidence_schema": "forged.record.schema",
            "dense_evidence_content_hash": "not-a-sha256",
            "comparison_outcome_is_metric": False,
            "epistemic_class": "a/c",
        }

    _assert_forged_sweeps_rejected(
        monkeypatch,
        qt,
        forge_dense_certification,
    )


def test_bundle_rejects_unauthenticated_dense_record_child_during_recalibration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    real_dense_calibration = qt._trajectory_seed_sweep_dense_calibration
    schedule, bond, seed = _accepted_sweeps(monkeypatch, qt)
    monkeypatch.setattr(
        qt,
        "_trajectory_seed_sweep_dense_calibration",
        real_dense_calibration,
    )
    forged_dense = {
        "schema": "forged.record.schema",
        "content_hash": "not-a-sha256",
        "record_evidence": {
            "measurement_records": [[0, 0]],
            "record_probabilities": [1.0],
        },
    }
    dense_calls = 0

    def dense_child(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        nonlocal dense_calls
        dense_calls += 1
        return copy.deepcopy(forged_dense)

    monkeypatch.setattr(
        qt,
        "axis1_measurement_record_evidence_manifest",
        dense_child,
    )
    seed["seed_sweep_policy"]["dense_reference_calibration"] = {
        "status": "passed",
        "executed": True,
        "passed": True,
        "accepted_as_dense_calibrated_trajectory_evidence": True,
        "dense_evidence_schema": "forged.record.schema",
        "dense_evidence_content_hash": "not-a-sha256",
        "comparison_object": "record_probabilities",
        "record_support_alignment_policy": (
            "union_of_emitted_records_missing_probability_zero"
        ),
        "dense_record_frequency_gate": 0.0,
        "observed_max_abs_frequency_difference": 0.0,
        "observed_max_total_variation_distance": 0.0,
        "total_variation_convention": "TV = 1/2 * sum_i |p_i - q_i|",
        "violations": [],
        "gate_role": "heuristic_dense_record_frequency_gate_not_metric",
        "comparison_outcome_is_metric": False,
        "epistemic_class": "c",
    }
    _rehash(qt, seed)
    _install_sweeps(monkeypatch, qt, bond=bond, seed=seed)
    expected_dense = copy.deepcopy(forged_dense)
    expected_bond = copy.deepcopy(bond)
    expected_seed = copy.deepcopy(seed)

    with pytest.raises((TypeError, ValueError)):
        _bundle_request(qt, schedule)
    assert dense_calls == 1
    assert forged_dense == expected_dense
    assert bond == expected_bond
    assert seed == expected_seed


def test_bundle_rejects_nested_control_type_smuggling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def smuggle_types(bond: dict[str, Any], seed: dict[str, Any]) -> None:
        bond["bond_values"] = [True, 2]
        seed["rng_seeds"] = [3.0, 7]

    _assert_forged_sweeps_rejected(monkeypatch, qt, smuggle_types)


def test_bundle_rejects_rehashed_scientific_false_flag_promotion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import error_coupling_simulator.frontend.axis1_qt_mps_execution as qt

    def promote_scientific_flags(
        bond: dict[str, Any], seed: dict[str, Any]
    ) -> None:
        bond["convergence_policy"][
            "accepted_for_production_scalable_backend"
        ] = True
        seed["seed_sweep_policy"]["accepted_as_production_error_bound"] = True
        seed["seed_sweep_policy"][
            "accepted_for_production_scalable_backend"
        ] = True

    _assert_forged_sweeps_rejected(
        monkeypatch,
        qt,
        promote_scientific_flags,
    )
