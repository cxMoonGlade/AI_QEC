#!/usr/bin/env python3
"""Run GCAPEPS trajectories serially and in isolated parallel processes.

The parent thread pool only supervises blocking subprocess calls.  Each
scientific unit is a separately exec'd OS process running one seeded carrier
prefix with known Quimb, NumPy, Numba, and BLAS thread controls configured to
one before scientific imports.  Quimb's own thread and MPI executors are not
used by the registered call graph.

The report checks that serial and process-parallel scheduling preserve each
trajectory's bounded operation-100 result.  Timing is diagnostic only: this
development replay does not make a speed, generic PEPS, non-Markovianity,
faithfulness, or QEC Record claim.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.util
import math
import os
from pathlib import Path
import sys
import time
from typing import Any, Mapping, Sequence


SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "native_trajectory_process_regression.v1"
)
BATCH_RECEIPT_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "native_trajectory_batch_receipt.v1"
)
OVERALL_RECEIPT_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "native_trajectory_overall_receipt.v1"
)
TRAJECTORY_SEEDS = (0, 1, 2, 3)
EVIDENCE_SEED = 2
DEFAULT_PROCESS_COUNT = len(TRAJECTORY_SEEDS)
EXPECTED_TRAJECTORY_IDENTITIES = {
    0: {
        "fixture": (
            "18ab72ff38a1689a64499f20a571ff7bbb0e3633ab64c86ff962131a8481adc4"
        ),
        "mask": (
            "6cafc3559b250bf1435a9dc3cd55b5b19690e85bf3637c79c960ed2b9f60d0ca"
        ),
        "events": 24,
    },
    1: {
        "fixture": (
            "d28e6b885f651d57edb1ad54e970f645434757b97f12820333ff718a3d9b14c1"
        ),
        "mask": (
            "68542e3bf83f5ef092e659c447279fe5a5c784fb64a7a849c23ef949983f6747"
        ),
        "events": 22,
    },
    2: {
        "fixture": (
            "4a2abe4d32c15af833d849a62b55c45a3cb23f79383976352efaf02e1f91a463"
        ),
        "mask": (
            "c467acbb61f7b5d54c45cf25d633088dea2105b2f3b54a93bb9244ca9230d139"
        ),
        "events": 24,
    },
    3: {
        "fixture": (
            "62b57ccab47dcf338bbc9189433db453c55eb3fe78cce5d66f5c1991b6b144aa"
        ),
        "mask": (
            "8798a4e247920e1f2db43a2a79800cde686362e5ced76792dc52842bcb871913"
        ),
        "events": 22,
    },
}
_REPOSITORY = Path(__file__).resolve().parents[2]
_THREAD_RUNNER_PATH = Path(__file__).resolve().with_name(
    "run_gcapeps_native_thread_regression.py"
)


def _load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path.resolve(strict=True))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


thread_runner = _load_path(
    "_gcapeps_native_trajectory_process_thread_runner",
    _THREAD_RUNNER_PATH,
)


def _trajectory_id(fixture: Mapping[str, Any]) -> str:
    return f"{fixture['case_id']}:input{thread_runner.INPUT_ID}"


def _executed_prefix_projection(
    fixture: Mapping[str, Any],
) -> dict[str, Any]:
    """Describe exactly what the operation-100 replay executes."""

    try:
        round_ledger = fixture["carrier_path"]["round_ledger"]
        declared_rounds = fixture["parameters"]["rounds"]
        all_operations = [
            operation
            for round_row in round_ledger
            for operation in round_row["operations"]
        ]
    except (KeyError, TypeError) as error:
        raise ValueError("trajectory round ledger is malformed") from error
    if not all_operations or [
        operation["operation_index"] for operation in all_operations
    ] != list(range(len(all_operations))):
        raise ValueError("trajectory operation ledger is not contiguous")

    stop = thread_runner.STOP_AFTER_OPERATION
    prefix = thread_runner._fixture_operation_prefix(fixture)
    operation_by_index = {
        operation["operation_index"]: operation
        for operation in all_operations
    }
    if stop + 1 not in operation_by_index:
        raise ValueError("trajectory fixture has no post-prefix operation")

    completed_round_indices = []
    partial_round_indices = []
    for round_row in round_ledger:
        indices = [
            operation["operation_index"]
            for operation in round_row["operations"]
        ]
        if not indices:
            raise ValueError("trajectory round contains no operations")
        if max(indices) <= stop:
            completed_round_indices.append(round_row["round_index"])
        elif min(indices) <= stop:
            partial_round_indices.append(round_row["round_index"])

    collision_prefix = [
        operation
        for operation in prefix
        if operation["operation_class"] == "collision_rotation"
    ]
    event_groups: dict[tuple[int, int, int], list[Mapping[str, Any]]] = {}
    for operation in collision_prefix:
        key = (
            operation["round_index"],
            operation["event_row_index"],
            operation["site_index"],
        )
        event_groups.setdefault(key, []).append(operation)
    completed_events = [
        rows
        for rows in event_groups.values()
        if [operation["axis"] for operation in rows] == ["X", "Y", "Z"]
    ]
    partial_events = [
        (key, rows)
        for key, rows in event_groups.items()
        if [operation["axis"] for operation in rows] != ["X", "Y", "Z"]
    ]
    if len(partial_events) != 1:
        raise ValueError("trajectory prefix must contain one partial event")
    partial_key, partial_rows = partial_events[0]
    next_operation = operation_by_index[stop + 1]
    next_key = (
        next_operation["round_index"],
        next_operation["event_row_index"],
        next_operation["site_index"],
    )
    if (
        declared_rounds != 4
        or completed_round_indices != [1, 2]
        or partial_round_indices != [3]
        or len(prefix) != 101
        or len(collision_prefix) != 44
        or len(completed_events) != 14
        or [operation["operation_index"] for operation in partial_rows]
        != [99, 100]
        or [operation["collision_ordinal"] for operation in partial_rows]
        != [42, 43]
        or [operation["axis"] for operation in partial_rows] != ["X", "Y"]
        or next_key != partial_key
        or next_operation["collision_ordinal"] != 44
        or next_operation["axis"] != "Z"
        or any(operation["round_index"] == 4 for operation in prefix)
    ):
        raise ValueError("trajectory operation-100 prefix contract drifted")
    return {
        "fixture_declared_rounds": declared_rounds,
        "first_operation_index": prefix[0]["operation_index"],
        "stop_after_operation_inclusive": stop,
        "executed_operation_count": len(prefix),
        "last_executed_round_index": prefix[-1]["round_index"],
        "completed_round_indices": completed_round_indices,
        "partial_round_index": partial_round_indices[0],
        "round_4_executed": False,
        "executed_collision_rotation_count": len(collision_prefix),
        "completed_event_count": len(completed_events),
        "partial_event": {
            "round_index": partial_key[0],
            "event_row_index": partial_key[1],
            "site_index": partial_key[2],
            "executed_axes": [operation["axis"] for operation in partial_rows],
            "remaining_axes": [next_operation["axis"]],
            "next_fixture_operation_index": next_operation["operation_index"],
        },
    }


def build_frozen_trajectory_fixtures() -> dict[int, Mapping[str, Any]]:
    """Build the four registered calibration trajectories without Quimb."""

    owner = thread_runner._load_path(
        "_gcapeps_native_process_fixture_owner",
        thread_runner._FIXTURE_OWNER,
    )
    fixtures: dict[int, Mapping[str, Any]] = {}
    for seed in TRAJECTORY_SEEDS:
        fixture = owner.build_fixture(
            run_partition="CALIBRATION",
            width=7,
            rounds=4,
            axis_family=3,
            p_event_numerator=3,
            seed=seed,
            gamma_index=2,
            run_blpensemble=False,
        )
        owner.validate_fixture(fixture)
        fixtures[seed] = fixture
    _validate_trajectory_fixtures(fixtures)
    return fixtures


def _validate_trajectory_fixtures(
    fixtures: Mapping[int, Mapping[str, Any]],
) -> None:
    if set(fixtures) != set(TRAJECTORY_SEEDS):
        raise ValueError("trajectory fixture seeds drifted")
    owner = thread_runner._load_path(
        "_gcapeps_native_process_fixture_validator",
        thread_runner._FIXTURE_OWNER,
    )
    event_hashes = []
    for seed in TRAJECTORY_SEEDS:
        fixture = fixtures[seed]
        expected_identity = EXPECTED_TRAJECTORY_IDENTITIES[seed]
        if owner.validate_fixture(fixture) != expected_identity["fixture"]:
            raise ValueError("trajectory fixture reconstruction drifted")
        parameters = fixture["parameters"]
        state_contract = fixture["state_contract"]
        if (
            parameters["seed"] != seed
            or parameters["width"] != 7
            or parameters["rounds"] != 4
            or parameters["axis_family"] != 3
            or parameters["p_event_numerator"] != 3
            or parameters["gamma_index"] != 2
            or parameters["max_bond"] != 32
            or state_contract["joint_state_retained_across_rounds"] is not True
            or state_contract["memory_row_policy"]
            != "never_discard_reset_or_recreate"
            or state_contract["candidate_restart_between_rounds"] is not False
            or fixture["result_projection_sha256"]
            != expected_identity["fixture"]
            or fixture["carrier_path"]["full_mask_sha256"]
            != expected_identity["mask"]
            or fixture["carrier_path"]["realized_event_count"]
            != expected_identity["events"]
        ):
            raise ValueError("trajectory fixture contract drifted")
        _executed_prefix_projection(fixture)
        event_hashes.append(fixture["carrier_path"]["full_mask_sha256"])
    if len(set(event_hashes)) != len(event_hashes):
        raise ValueError("registered trajectory event masks are not distinct")


def _validate_process_count(process_count: int) -> int:
    if (
        isinstance(process_count, bool)
        or not isinstance(process_count, int)
        or process_count < 2
        or process_count > len(TRAJECTORY_SEEDS)
    ):
        raise ValueError("process_count must be an integer in [2, 4]")
    return process_count


def _run_one_trajectory(
    *,
    fixture: Mapping[str, Any],
    fork_python: Path,
    timeout_seconds: float,
    shadow_evidence: bool,
) -> dict[str, Any]:
    return thread_runner._run_child(
        fixture_bytes=thread_runner._canonical_json_bytes(fixture),
        fork_python=fork_python,
        thread_count=1,
        strategy=thread_runner.NATIVE_STRATEGY,
        shadow_evidence=shadow_evidence,
        timeout_seconds=timeout_seconds,
    )


def _batch_receipt(
    *,
    mode: str,
    process_count: int,
    children: Mapping[int, Mapping[str, Any]],
    wall_duration_ns: int,
    cpu_duration_ns: int,
) -> dict[str, Any]:
    if mode not in {"serial", "parallel"}:
        raise ValueError("batch receipt mode is invalid")
    process_count = _validate_process_count(process_count)
    if set(children) != set(TRAJECTORY_SEEDS):
        raise ValueError("batch receipt child seeds drifted")
    if (
        isinstance(wall_duration_ns, bool)
        or not isinstance(wall_duration_ns, int)
        or isinstance(cpu_duration_ns, bool)
        or not isinstance(cpu_duration_ns, int)
    ):
        raise ValueError("batch timing types are invalid")
    if wall_duration_ns <= 0 or cpu_duration_ns < 0:
        raise ValueError("batch timing is invalid")
    child_wall = {
        str(seed): child["supervisor_process_receipt"][
            "parent_observed_wall_duration_ns"
        ]
        for seed, child in sorted(children.items())
    }
    if any(
        not thread_runner._is_plain_int(value, minimum=1)
        for value in child_wall.values()
    ):
        raise ValueError("batch child wall timing types are invalid")
    receipt = {
        "schema": BATCH_RECEIPT_SCHEMA,
        "mode": mode,
        "wall_clock": "time.perf_counter_ns",
        "cpu_clock": "time.process_time_ns",
        "wall_duration_ns": wall_duration_ns,
        "supervisor_cpu_duration_ns": cpu_duration_ns,
        "trajectory_count": len(children),
        "configured_process_count": process_count,
        "trajectory_seeds": list(TRAJECTORY_SEEDS),
        "configured_maximum_scientific_children": (
            1 if mode == "serial" else process_count
        ),
        "scientific_compute_unit": "fresh_subprocess",
        "configured_scientific_threads_per_child": 1,
        "orchestration": (
            "sequential_subprocess_wait"
            if mode == "serial"
            else "thread_pool_waiting_on_fresh_subprocesses"
        ),
        "child_wall_duration_ns_by_seed": child_wall,
        "child_wall_duration_ns_sum": sum(child_wall.values()),
        "child_wall_duration_ns_max": max(child_wall.values()),
        "throughput_trajectories_per_second": (
            len(children) * 1.0e9 / wall_duration_ns
        ),
        "result_projection_sha256": "",
    }
    receipt["result_projection_sha256"] = thread_runner._projection_sha256(
        {
            key: value
            for key, value in receipt.items()
            if key != "result_projection_sha256"
        }
    )
    return receipt


def _validate_batch_receipt(
    receipt: Mapping[str, Any],
    *,
    mode: str,
    process_count: int,
    children: Mapping[int, Mapping[str, Any]],
) -> None:
    expected_keys = {
        "schema",
        "mode",
        "wall_clock",
        "cpu_clock",
        "wall_duration_ns",
        "supervisor_cpu_duration_ns",
        "trajectory_count",
        "trajectory_seeds",
        "configured_process_count",
        "configured_maximum_scientific_children",
        "scientific_compute_unit",
        "configured_scientific_threads_per_child",
        "orchestration",
        "child_wall_duration_ns_by_seed",
        "child_wall_duration_ns_sum",
        "child_wall_duration_ns_max",
        "throughput_trajectories_per_second",
        "result_projection_sha256",
    }
    if not isinstance(receipt, Mapping) or set(receipt) != expected_keys:
        raise ValueError("batch receipt key set drifted")
    expected = _batch_receipt(
        mode=mode,
        process_count=process_count,
        children=children,
        wall_duration_ns=receipt["wall_duration_ns"],
        cpu_duration_ns=receipt["supervisor_cpu_duration_ns"],
    )
    if thread_runner._canonical_json_bytes(receipt) != (
        thread_runner._canonical_json_bytes(expected)
    ):
        raise ValueError("batch receipt content or projection is invalid")


def _overall_receipt(
    *,
    wall_duration_ns: int,
    cpu_duration_ns: int,
    serial_child_count: int,
    parallel_child_count: int,
) -> dict[str, Any]:
    if (
        isinstance(wall_duration_ns, bool)
        or not isinstance(wall_duration_ns, int)
        or wall_duration_ns <= 0
        or isinstance(cpu_duration_ns, bool)
        or not isinstance(cpu_duration_ns, int)
        or cpu_duration_ns < 0
    ):
        raise ValueError("overall timing is invalid")
    if (
        not thread_runner._is_plain_int(serial_child_count, minimum=0)
        or not thread_runner._is_plain_int(
            parallel_child_count, minimum=0
        )
        or serial_child_count != len(TRAJECTORY_SEEDS)
        or parallel_child_count != len(TRAJECTORY_SEEDS)
    ):
        raise ValueError("overall child counts are invalid")
    receipt = {
        "schema": OVERALL_RECEIPT_SCHEMA,
        "wall_clock": "time.perf_counter_ns",
        "cpu_clock": "time.process_time_ns",
        "wall_duration_ns": wall_duration_ns,
        "supervisor_cpu_duration_ns": cpu_duration_ns,
        "scientific_child_count": (
            serial_child_count + parallel_child_count + 1
        ),
        "serial_no_shadow_child_count": serial_child_count,
        "parallel_no_shadow_child_count": parallel_child_count,
        "evidence_child_count": 1,
        "result_projection_sha256": "",
    }
    receipt["result_projection_sha256"] = thread_runner._projection_sha256(
        {
            key: value
            for key, value in receipt.items()
            if key != "result_projection_sha256"
        }
    )
    return receipt


def _validate_overall_receipt(
    receipt: Mapping[str, Any],
    *,
    serial_batch_receipt: Mapping[str, Any],
    parallel_batch_receipt: Mapping[str, Any],
    evidence_child: Mapping[str, Any],
) -> None:
    expected_keys = {
        "schema",
        "wall_clock",
        "cpu_clock",
        "wall_duration_ns",
        "supervisor_cpu_duration_ns",
        "scientific_child_count",
        "serial_no_shadow_child_count",
        "parallel_no_shadow_child_count",
        "evidence_child_count",
        "result_projection_sha256",
    }
    if not isinstance(receipt, Mapping) or set(receipt) != expected_keys:
        raise ValueError("overall receipt key set drifted")
    expected = _overall_receipt(
        wall_duration_ns=receipt["wall_duration_ns"],
        cpu_duration_ns=receipt["supervisor_cpu_duration_ns"],
        serial_child_count=len(TRAJECTORY_SEEDS),
        parallel_child_count=len(TRAJECTORY_SEEDS),
    )
    minimum_wall = (
        serial_batch_receipt["wall_duration_ns"]
        + parallel_batch_receipt["wall_duration_ns"]
        + evidence_child["supervisor_process_receipt"][
            "parent_observed_wall_duration_ns"
        ]
    )
    if (
        thread_runner._canonical_json_bytes(receipt)
        != thread_runner._canonical_json_bytes(expected)
        or receipt["wall_duration_ns"] < minimum_wall
    ):
        raise ValueError("overall receipt content or projection is invalid")


def _run_batch(
    *,
    fixtures: Mapping[int, Mapping[str, Any]],
    fork_python: Path,
    timeout_seconds: float,
    mode: str,
    process_count: int,
) -> tuple[dict[int, Mapping[str, Any]], dict[str, Any]]:
    if mode not in {"serial", "parallel"}:
        raise ValueError("mode must be serial or parallel")
    process_count = _validate_process_count(process_count)
    _validate_trajectory_fixtures(fixtures)
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    children: dict[int, Mapping[str, Any]] = {}
    if mode == "serial":
        for seed in TRAJECTORY_SEEDS:
            children[seed] = _run_one_trajectory(
                fixture=fixtures[seed],
                fork_python=fork_python,
                timeout_seconds=timeout_seconds,
                shadow_evidence=False,
            )
    else:
        with ThreadPoolExecutor(
            max_workers=process_count,
            thread_name_prefix="gcapeps-subprocess-supervisor",
        ) as pool:
            pending = {
                pool.submit(
                    _run_one_trajectory,
                    fixture=fixtures[seed],
                    fork_python=fork_python,
                    timeout_seconds=timeout_seconds,
                    shadow_evidence=False,
                ): seed
                for seed in TRAJECTORY_SEEDS
            }
            for future in as_completed(pending):
                seed = pending[future]
                children[seed] = future.result()
    cpu_duration_ns = time.process_time_ns() - cpu_start
    wall_duration_ns = time.perf_counter_ns() - wall_start
    if set(children) != set(TRAJECTORY_SEEDS):
        raise RuntimeError("trajectory batch did not return every seed")
    ordered = {seed: children[seed] for seed in TRAJECTORY_SEEDS}
    receipt = _batch_receipt(
        mode=mode,
        process_count=process_count,
        children=ordered,
        wall_duration_ns=wall_duration_ns,
        cpu_duration_ns=cpu_duration_ns,
    )
    return ordered, receipt


def _trajectory_family_projection(
    fixtures: Mapping[int, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "trajectory_seed": seed,
            "trajectory_id": _trajectory_id(fixtures[seed]),
            "case_id": fixtures[seed]["case_id"],
            "fixture_projection_sha256": fixtures[seed][
                "result_projection_sha256"
            ],
            "fixture_full_mask_sha256": fixtures[seed]["carrier_path"][
                "full_mask_sha256"
            ],
            "fixture_total_realized_event_count": fixtures[seed]["carrier_path"][
                "realized_event_count"
            ],
            "executed_prefix": _executed_prefix_projection(fixtures[seed]),
        }
        for seed in TRAJECTORY_SEEDS
    ]


def build_report(
    *,
    fixtures: Mapping[int, Mapping[str, Any]],
    serial_children: Mapping[int, Mapping[str, Any]],
    parallel_children: Mapping[int, Mapping[str, Any]],
    evidence_child: Mapping[str, Any],
    serial_batch_receipt: Mapping[str, Any],
    parallel_batch_receipt: Mapping[str, Any],
    overall_execution_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    assembly_wall_start = time.perf_counter_ns()
    assembly_cpu_start = time.process_time_ns()
    _validate_trajectory_fixtures(fixtures)
    expected = set(TRAJECTORY_SEEDS)
    if set(serial_children) != expected or set(parallel_children) != expected:
        raise ValueError("serial/parallel child seed sets drifted")

    trajectory_comparisons: dict[str, Any] = {}
    case_timing: dict[str, Any] = {}
    for seed in TRAJECTORY_SEEDS:
        fixture = fixtures[seed]
        serial_child = serial_children[seed]
        parallel_child = parallel_children[seed]
        for child in (serial_child, parallel_child):
            thread_runner._validate_child_identity(
                child,
                fixture=fixture,
                thread_count=1,
                strategy=thread_runner.NATIVE_STRATEGY,
                shadow_evidence=False,
            )
        comparison = thread_runner._pair_comparison(
            serial_child,
            parallel_child,
            name=f"trajectory_seed_{seed}_serial_vs_process_parallel",
        )
        trajectory_comparisons[str(seed)] = {
            "trajectory_seed": seed,
            "trajectory_id": _trajectory_id(fixture),
            "comparison": comparison,
            "passed": comparison["passed"],
        }
        case_timing[str(seed)] = {
            "serial": thread_runner._timing_inventory(serial_child),
            "process_parallel": thread_runner._timing_inventory(
                parallel_child
            ),
        }

    evidence_fixture = fixtures[EVIDENCE_SEED]
    thread_runner._validate_child_identity(
        evidence_child,
        fixture=evidence_fixture,
        thread_count=1,
        strategy=thread_runner.NATIVE_STRATEGY,
        shadow_evidence=True,
    )
    if not isinstance(parallel_batch_receipt, Mapping):
        raise ValueError("parallel batch receipt must be a mapping")
    process_count = _validate_process_count(
        parallel_batch_receipt.get("configured_process_count")
    )
    _validate_batch_receipt(
        serial_batch_receipt,
        mode="serial",
        process_count=process_count,
        children=serial_children,
    )
    _validate_batch_receipt(
        parallel_batch_receipt,
        mode="parallel",
        process_count=process_count,
        children=parallel_children,
    )
    _validate_overall_receipt(
        overall_execution_receipt,
        serial_batch_receipt=serial_batch_receipt,
        parallel_batch_receipt=parallel_batch_receipt,
        evidence_child=evidence_child,
    )
    all_children = [
        *(serial_children[seed] for seed in TRAJECTORY_SEEDS),
        *(parallel_children[seed] for seed in TRAJECTORY_SEEDS),
        evidence_child,
    ]
    source_identity_bytes = [
        thread_runner._canonical_json_bytes(child["source_identity"])
        for child in all_children
    ]
    if any(
        identity != source_identity_bytes[0]
        for identity in source_identity_bytes[1:]
    ):
        raise ValueError("scientific child source/runtime identities differ")
    shared_child_source_identity_sha256 = hashlib.sha256(
        source_identity_bytes[0]
    ).hexdigest()
    shadow_comparison = thread_runner._pair_comparison(
        serial_children[EVIDENCE_SEED],
        evidence_child,
        name="trajectory_seed_2_no_shadow_vs_evidence_shadow",
    )
    witness = thread_runner.select_nondegeneracy_witness(evidence_child)

    serial_wall = int(serial_batch_receipt["wall_duration_ns"])
    parallel_wall = int(parallel_batch_receipt["wall_duration_ns"])
    if serial_wall <= 0 or parallel_wall <= 0:
        raise ValueError("batch wall timing must be positive")
    speedup = serial_wall / parallel_wall
    if not math.isfinite(speedup) or speedup <= 0.0:
        raise ValueError("observed diagnostic speedup is invalid")

    comparisons_passed = all(
        row["passed"] for row in trajectory_comparisons.values()
    )
    passed = bool(
        comparisons_passed
        and shadow_comparison["passed"]
        and witness is not None
    )
    assembly_wall_duration_ns = time.perf_counter_ns() - assembly_wall_start
    assembly_cpu_duration_ns = time.process_time_ns() - assembly_cpu_start
    report = {
        "schema": SCHEMA,
        "formal_claim_eligible": False,
        "faithfulness_claim": False,
        "performance_claim": False,
        "non_markovianity_claim": False,
        "selected_strategy": thread_runner.NATIVE_STRATEGY,
        "split_policy": dict(thread_runner.EXPECTED_SPLIT_POLICY),
        "trajectory_execution_model": {
            "trajectory_internal_order": "chronological_serial_rounds",
            "joint_state_retained_across_rounds": True,
            "memory_row_policy": "never_discard_reset_or_recreate",
            "candidate_restart_between_rounds": False,
            "parallel_unit": (
                "distinct_seeded_persistent_memory_unitary_prefix"
            ),
            "scientific_compute_unit": "fresh_subprocess",
            "configured_scientific_threads_per_child": 1,
            "thread_environment_variables": list(
                thread_runner.THREAD_VARIABLES
            ),
            "quimb_process_environment": {
                name: "1" for name in thread_runner.PROCESS_VARIABLES
            },
            "dynamic_thread_environment": {
                name: "FALSE" for name in thread_runner.DYNAMIC_VARIABLES
            },
            "quimb_numba_cache": thread_runner.QUIMB_NUMBA_CACHE,
            "absent_mpi_presence_variables": list(
                thread_runner.MPI_PRESENCE_VARIABLES
            ),
            "absent_numba_layer_variables": list(
                thread_runner.NUMBA_LAYER_VARIABLES
            ),
            "quimb_internal_executor_status": (
                "not_invoked_by_the_registered_gcapeps_call_graph; the "
                "environment alone is not a generic no-spawn proof"
            ),
            "supervisor_wait_threads_do_scientific_compute": False,
            "reduced_system_memory_witness": "not_evaluated_by_this_runner",
        },
        "trajectory_family": _trajectory_family_projection(fixtures),
        "process_schedule_invariance": {
            "comparisons": trajectory_comparisons,
            "passed": comparisons_passed,
        },
        "shadow_isolation": shadow_comparison,
        "nondegeneracy_witness": witness,
        "nondegeneracy_passed": witness is not None,
        "timing": {
            "serial_batch": dict(serial_batch_receipt),
            "process_parallel_batch": dict(parallel_batch_receipt),
            "observed_serial_over_parallel_wall_ratio_diagnostic_only": (
                speedup
            ),
            "case_and_substep_timing": case_timing,
            "evidence_trajectory": thread_runner._timing_inventory(
                evidence_child
            ),
            "overall_execution_before_report_assembly": dict(
                overall_execution_receipt
            ),
            "report_assembly": {
                "wall_clock": "time.perf_counter_ns",
                "cpu_clock": "time.process_time_ns",
                "wall_duration_ns": assembly_wall_duration_ns,
                "cpu_duration_ns": assembly_cpu_duration_ns,
            },
        },
        "timing_interpretation": (
            "development throughput diagnostic for four frozen operation-100 "
            "prefixes; not an accepted speed comparison and not part of "
            "pass/fail"
        ),
        "raw_children": {
            "serial": {
                str(seed): serial_children[seed]
                for seed in TRAJECTORY_SEEDS
            },
            "process_parallel": {
                str(seed): parallel_children[seed]
                for seed in TRAJECTORY_SEEDS
            },
            "evidence_seed_2": evidence_child,
        },
        "passed": passed,
        "verdict": (
            "PASS_ENGINEERING_TRAJECTORY_PROCESS_REGRESSION"
            if passed
            else "FAIL_ENGINEERING_TRAJECTORY_PROCESS_REGRESSION"
        ),
        "claim_boundary": (
            "bounded serial-versus-external-process schedule invariance for "
            "operations 0..100 inclusive of four seeded R=4 fixture paths; "
            "every replay stops during round 3 before operation 101 and does "
            "not execute round 4. Persistent-memory denotes retention of the "
            "declared joint system-memory state across the executed round "
            "transitions only; no reduced-map, BLP, process-tensor, "
            "faithfulness, Record, generic PEPS, GPU, or performance conclusion"
        ),
        "source_identity": {
            "runner_source_sha256": thread_runner._source_sha256(
                Path(__file__).resolve(strict=True)
            ),
            "thread_runner_source_sha256": thread_runner._source_sha256(
                _THREAD_RUNNER_PATH
            ),
            "worker_source_sha256": thread_runner._source_sha256(
                thread_runner._WORKER
            ),
            "fixture_owner_source_sha256": thread_runner._source_sha256(
                thread_runner._FIXTURE_OWNER
            ),
            "shared_child_source_identity_sha256": (
                shared_child_source_identity_sha256
            ),
        },
        "result_projection_sha256": "",
    }
    report["result_projection_sha256"] = thread_runner._projection_sha256(
        {
            key: value
            for key, value in report.items()
            if key != "result_projection_sha256"
        }
    )
    return report


def run_regression(
    *,
    fork_python: Path,
    timeout_seconds: float,
    process_count: int,
) -> dict[str, Any]:
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0.0:
        raise ValueError("timeout_seconds must be finite and positive")
    process_count = _validate_process_count(process_count)
    fork_python = fork_python.resolve(strict=True)
    if not fork_python.is_file() or not os.access(fork_python, os.X_OK):
        raise ValueError("fork Python is not an executable file")

    overall_wall_start = time.perf_counter_ns()
    overall_cpu_start = time.process_time_ns()
    fixtures = build_frozen_trajectory_fixtures()
    serial_children, serial_receipt = _run_batch(
        fixtures=fixtures,
        fork_python=fork_python,
        timeout_seconds=timeout_seconds,
        mode="serial",
        process_count=process_count,
    )
    parallel_children, parallel_receipt = _run_batch(
        fixtures=fixtures,
        fork_python=fork_python,
        timeout_seconds=timeout_seconds,
        mode="parallel",
        process_count=process_count,
    )
    evidence_child = _run_one_trajectory(
        fixture=fixtures[EVIDENCE_SEED],
        fork_python=fork_python,
        timeout_seconds=timeout_seconds,
        shadow_evidence=True,
    )
    overall_receipt = _overall_receipt(
        wall_duration_ns=time.perf_counter_ns() - overall_wall_start,
        cpu_duration_ns=(
            time.process_time_ns() - overall_cpu_start
        ),
        serial_child_count=len(serial_children),
        parallel_child_count=len(parallel_children),
    )
    return build_report(
        fixtures=fixtures,
        serial_children=serial_children,
        parallel_children=parallel_children,
        evidence_child=evidence_child,
        serial_batch_receipt=serial_receipt,
        parallel_batch_receipt=parallel_receipt,
        overall_execution_receipt=overall_receipt,
    )


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fork-python-executable",
        type=Path,
        default=thread_runner._DEFAULT_FORK_PYTHON,
    )
    parser.add_argument("--timeout-seconds", type=float, default=3600.0)
    parser.add_argument(
        "--processes",
        type=int,
        default=DEFAULT_PROCESS_COUNT,
        help="simultaneous one-thread scientific child processes (2-4)",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    report = run_regression(
        fork_python=args.fork_python_executable,
        timeout_seconds=args.timeout_seconds,
        process_count=args.processes,
    )
    encoded = thread_runner._canonical_json_bytes(report) + b"\n"
    if args.output is None:
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
    else:
        thread_runner._publish_fresh(args.output, encoded)
        summary = {
            "schema": report["schema"],
            "verdict": report["verdict"],
            "passed": report["passed"],
            "formal_claim_eligible": False,
            "performance_claim": False,
            "output": str(args.output.resolve(strict=True)),
            "output_sha256": hashlib.sha256(encoded).hexdigest(),
        }
        sys.stdout.buffer.write(
            thread_runner._canonical_json_bytes(summary) + b"\n"
        )
        sys.stdout.buffer.flush()
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
