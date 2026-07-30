#!/usr/bin/env python3
"""Run one fresh-process GCAPEPS operation-100 thread-regression child.

This is a development-only engineering instrument for the preregistered T3/T4
checks in ``GCAPEPS_FINITE_MEMORY_NATIVE_REPAIR_PREREG_2026-07-29.md``.  It
materializes raw complete vectors after operations 99 and 100.  It does not
claim PEPS faithfulness, a QEC Record, or a performance result.

The module intentionally imports only the Python standard library before
validating the child thread environment.  NumPy, Stim, Quimb, and the local
finite-memory helpers are loaded only after that validation.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence


SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "native_thread_worker.v1"
)
THREAD_VARIABLES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "BLIS_NUM_THREADS",
)
CHECKPOINT_OPERATIONS = (99, 100)
STOP_AFTER_OPERATION = 100
INPUT_ID = 2
NATIVE_STRATEGY = "native_simple_update"
LEGACY_STRATEGY = "exact_tree_then_native_compress"
STRATEGIES = (NATIVE_STRATEGY, LEGACY_STRATEGY)
_NATIVE_UPDATE_STRATEGY = "native_graph_local_pauli_rotation_simple_update"
_LEGACY_UPDATE_STRATEGY = "exact_tree_then_native_identity_compress"
_NO_SHADOW_CAUSE = "not_observed_without_shadow"
_REPOSITORY = Path(__file__).resolve().parents[2]
_FORK_ROOT = _REPOSITORY / "external/forks/quimb-gcapeps"


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _projection_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path.resolve(strict=True))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_sibling(name: str):
    return _load_path(
        f"_gcapeps_native_thread_{name}",
        Path(__file__).resolve(strict=True).with_name(f"{name}.py"),
    )


def _reject_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _parse_fixture(raw: bytes) -> Mapping[str, Any]:
    if not isinstance(raw, bytes) or not raw:
        raise ValueError("fixture stdin must contain nonempty JSON bytes")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON token {token}")
            ),
        )
    except UnicodeDecodeError as exc:
        raise ValueError("fixture stdin is not UTF-8") from exc
    if not isinstance(value, Mapping):
        raise ValueError("fixture JSON root must be an object")
    return value


def validate_child_environment(expected_threads: int) -> dict[str, Any]:
    """Validate the BLAS envelope before any scientific dependency import."""

    if isinstance(expected_threads, bool) or expected_threads not in (1, 4):
        raise ValueError("expected_threads must be exactly 1 or 4")
    expected = str(expected_threads)
    observed = {name: os.environ.get(name) for name in THREAD_VARIABLES}
    if any(value != expected for value in observed.values()):
        raise RuntimeError(
            "all five BLAS thread variables must equal the requested count"
        )
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise RuntimeError("CUDA_VISIBLE_DEVICES must be the empty string")
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise RuntimeError("PYTHONHASHSEED must be exactly 0")
    if "PYTHONPATH" in os.environ:
        raise RuntimeError("PYTHONPATH must be absent")
    forbidden_loaded = sorted(
        name
        for name in sys.modules
        if name.split(".", 1)[0] in {"numpy", "quimb", "stim"}
    )
    if forbidden_loaded:
        raise RuntimeError(
            "scientific dependencies loaded before thread validation: "
            + ",".join(forbidden_loaded)
        )
    return {
        "requested_thread_count": expected_threads,
        "thread_variables": observed,
        "CUDA_VISIBLE_DEVICES": "",
        "PYTHONHASHSEED": "0",
        "PYTHONPATH_present": False,
        "validated_before_numpy_quimb_stim_import": True,
    }


def _git_value(*args: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(_FORK_ROOT), *args),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def _fork_identity(quimb_module) -> dict[str, Any]:
    origin = Path(quimb_module.__file__).resolve(strict=True)
    if not origin.is_relative_to(_FORK_ROOT.resolve(strict=True)):
        raise RuntimeError("Quimb did not import from the registered fork")
    status = _git_value(
        "status",
        "--porcelain",
        "--untracked-files=all",
    )
    if status:
        raise RuntimeError(
            "registered Quimb fork must be clean before target execution"
        )
    return {
        "root": str(_FORK_ROOT.resolve(strict=True)),
        "commit": _git_value("rev-parse", "HEAD"),
        "tree": _git_value("rev-parse", "HEAD^{tree}"),
        "worktree_clean": True,
        "quimb_import_origin": str(origin),
        "quimb_version": str(quimb_module.__version__),
    }


def _plain(value: Any) -> Any:
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, complex):
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            raise ValueError("ledger contains non-finite complex data")
        return {"real": value.real, "imag": value.imag}
    if hasattr(value, "item"):
        return _plain(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("ledger contains non-finite float data")
    return value


def _initialize_state(
    *,
    engine,
    fixture: Mapping[str, Any],
    strategy: str,
    shadow_evidence: bool,
):
    """Construct the same finite-memory state with an explicit GC strategy."""

    geometry = fixture["geometry"]
    parameters = fixture["parameters"]
    if parameters["max_bond"] != engine.SPLIT_POLICY["max_bond"]:
        raise ValueError("fixture max_bond disagrees with GC split policy")
    circuit = engine.qtn.CircuitPEPSSimpleUpdate(
        N=geometry["n_qubits"],
        edges=tuple(tuple(edge) for edge in geometry["graph_edges"]),
        max_bond=engine.SPLIT_POLICY["max_bond"],
        cutoff=engine.SPLIT_POLICY["cutoff"],
        renorm=engine.SPLIT_POLICY["renorm"],
        gauge_smudge=engine.SPLIT_POLICY["smudge"],
        equilibrate_every=None,
        gate_opts={
            "cutoff_mode": engine.SPLIT_POLICY["cutoff_mode"],
            "method": engine.SPLIT_POLICY["method"],
            "absorb": engine.SPLIT_POLICY["absorb"],
            "power": engine.SPLIT_POLICY["power"],
        },
        dtype="complex128",
    )
    input_rows = {row["input_id"]: row for row in fixture["inputs"]}
    input_row = input_rows[INPUT_ID]
    if any(input_row["gc_residual_initial_bits"]):
        raise ValueError("GC residual initialization must be all zero")
    frame = engine.StimCliffordFrame(geometry["n_qubits"])
    transcript = []
    for operation in input_row["gc_frame_preparation_gates"]:
        frame.apply_clifford(engine._stim_circuit(operation))
        transcript.append(
            {
                "gate_kind": operation["gate_kind"],
                "targets": list(operation["targets"]),
            }
        )
    state = engine.GCAPEPSState.from_quimb(
        frame,
        circuit,
        site_order=tuple(range(geometry["n_qubits"])),
        contraction_optimize="greedy",
        pauli_rotation_strategy=strategy,
        compression_evidence=shadow_evidence,
    )
    engine._validate_array_precision(state._carrier._circuit)
    state_kwargs = {
        "fixture": fixture,
        "input_id": INPUT_ID,
        "state": state,
        "physical_frame_transcript": transcript,
        "pullback_rows": [],
        "algorithm_ledger": [],
        "max_exact_precompression_bond": 1,
        "max_committed_bond": 1,
    }
    # Another development session may have an additive round-reparameterization
    # ledger in its worktree. T3 is bound to the committed operation prefix and
    # deliberately does not consume that optional surface.
    if "scale_rebalance_ledger" in engine.GCState.__dataclass_fields__:
        state_kwargs["scale_rebalance_ledger"] = []
    return engine.GCState(**state_kwargs)


def _native_metadata(update) -> dict[str, Any]:
    plan = update.native_plan
    execution = update.native_execution_ledger
    if plan is None or execution is None:
        raise ValueError("native update omitted plan or execution ledger")
    if update.strategy != _NATIVE_UPDATE_STRATEGY:
        raise ValueError("native update strategy label drifted")
    if plan.plan_digest_sha256 != execution.plan_digest_sha256:
        raise ValueError("native plan and execution ledger digests differ")
    return {
        "strategy": NATIVE_STRATEGY,
        "update_strategy": update.strategy,
        "plan_digest_sha256": plan.plan_digest_sha256,
        "canonical_gate_transcript": _plain(plan.canonical_transcript),
        "routing_root": _plain(plan.routing_root),
        "routing_vertices": _plain(plan.routing_vertices),
        "routing_tree_edges": _plain(plan.routing_tree_edges),
        "configured_max_bond": update.max_bond_limit,
        "configured_cutoff": update.cutoff,
        "candidate_kept_dimensions": [
            row.candidate_kept_bond_dimension
            for row in execution.split_records
        ],
        "native_execution_ledger": _plain(execution),
        "native_truncation_ledger": _plain(update.native_truncation_ledger),
    }


def _legacy_metadata(update) -> dict[str, Any]:
    ledger = update.tree_compression_ledger
    if update.strategy != _LEGACY_UPDATE_STRATEGY or ledger is None:
        raise ValueError("legacy diagnostic update omitted its ledger")
    return {
        "strategy": LEGACY_STRATEGY,
        "update_strategy": update.strategy,
        "routing_root": _plain(update.routing_root),
        "routing_vertices": _plain(update.routing_vertices),
        "routing_tree_edges": _plain(update.routing_tree_edges),
        "configured_max_bond": update.max_bond_limit,
        "configured_cutoff": update.cutoff,
        "tree_compression_ledger": _plain(ledger),
    }


def _apply_operation(
    *,
    engine,
    state,
    operation: Mapping[str, Any],
    strategy: str,
    span_factory,
) -> dict[str, Any] | None:
    if operation["operation_class"] == "clifford":
        event = state.state.apply_clifford(
            engine._stim_circuit(operation),
            span_factory=span_factory,
        )
        state.physical_frame_transcript.append(
            {
                "gate_kind": operation["gate_kind"],
                "targets": list(operation["targets"]),
            }
        )
        state.algorithm_ledger.append(engine._algorithm_update_projection(event))
        if event.peps_gate_count_before != event.peps_gate_count_after:
            raise ValueError("Clifford frame update changed residual gate count")
        return None
    if operation["operation_class"] != "collision_rotation":
        raise ValueError("unknown neutral operation class")
    physical = engine.QubitPauliWord.from_labels(
        operation["physical_pauli_body"]
    )
    request = state._request_for_operation(operation)
    event = state.state.apply_pauli_rotation(
        physical,
        float.fromhex(operation["theta_float64_hex"]),
        span_factory=span_factory,
    )
    update = event.residual_update
    if update is None or event.pulled_back_pauli is None:
        raise ValueError("collision omitted its residual update or pullback")
    pulled = engine._signed_word_text_value(
        event.pulled_back_pauli,
        num_qubits=physical.num_qubits,
    )
    pullback = {
        **request,
        "physical_sign": 1,
        "physical_body": operation["physical_pauli_body"],
        "pulled_back_sign": pulled["sign"],
        "pulled_back_body": pulled["body"],
    }
    state.pullback_rows.append(pullback)
    metadata = (
        _native_metadata(update)
        if strategy == NATIVE_STRATEGY
        else _legacy_metadata(update)
    )
    metadata.update(
        {
            "operation_index": operation["operation_index"],
            "round_index": operation["round_index"],
            "physical_request": dict(request),
            "physical_pauli": event.physical_pauli,
            "signed_pulled_word": event.pulled_back_pauli,
            "pullback": pullback,
        }
    )
    if strategy == NATIVE_STRATEGY:
        execution = update.native_execution_ledger
        full_dimensions = [
            row.full_bond_dimension
            for row in execution.split_records
            if row.full_bond_dimension is not None
        ]
        if full_dimensions:
            state.max_exact_precompression_bond = max(
                state.max_exact_precompression_bond,
                *full_dimensions,
            )
    else:
        exact_dimensions = [
            row.exact_precompression_bond
            for row in update.tree_compression_ledger.split_records
        ]
        if exact_dimensions:
            state.max_exact_precompression_bond = max(
                state.max_exact_precompression_bond,
                *exact_dimensions,
            )
    state.max_committed_bond = max(
        state.max_committed_bond,
        update.max_bond_after,
    )
    state.algorithm_ledger.append(metadata)
    engine._validate_array_precision(state.circuit)
    return metadata


def _operation_prefix(fixture: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = [
        operation
        for round_row in fixture["carrier_path"]["round_ledger"]
        for operation in round_row["operations"]
        if operation["operation_index"] <= STOP_AFTER_OPERATION
    ]
    if [row["operation_index"] for row in rows] != list(
        range(STOP_AFTER_OPERATION + 1)
    ):
        raise ValueError("fixture does not contain the exact operation-100 prefix")
    return rows


def _run(
    *,
    fixture: Mapping[str, Any],
    environment_receipt: Mapping[str, Any],
    strategy: str,
    shadow_evidence: bool,
) -> dict[str, Any]:
    if strategy not in STRATEGIES:
        raise ValueError("unsupported GC strategy")
    if strategy == LEGACY_STRATEGY and shadow_evidence:
        raise ValueError("legacy diagnostic does not use native shadow evidence")

    # These imports happen only after validate_child_environment.
    import numpy as np
    import quimb
    import stim

    fixture_owner = _load_sibling("emit_gcapeps_finite_memory_fixture")
    engine = _load_sibling("gcapeps_finite_memory_engine")
    common = _load_sibling("gcapeps_finite_memory_worker_common")
    timing_owner = _load_sibling("gcapeps_finite_memory_timing")
    import quimb.experimental.gcapeps.native as native_owner

    original_shadow_builder = native_owner._build_native_evidence_shadow
    shadow_builder_calls = 0
    if strategy == NATIVE_STRATEGY:
        if shadow_evidence:

            def counted_shadow_builder(*args, **kwargs):
                nonlocal shadow_builder_calls
                shadow_builder_calls += 1
                return original_shadow_builder(*args, **kwargs)

            native_owner._build_native_evidence_shadow = counted_shadow_builder
        else:

            def forbidden_shadow_builder(*_args, **_kwargs):
                nonlocal shadow_builder_calls
                shadow_builder_calls += 1
                raise AssertionError(
                    "no-shadow execution invoked the evidence builder"
                )

            native_owner._build_native_evidence_shadow = forbidden_shadow_builder
    fixture_hash = fixture_owner.validate_fixture(fixture)
    expected_parameters = {
        "width": 7,
        "rounds": 4,
        "axis_family": 3,
        "p_event_numerator": 3,
        "seed": 2,
        "gamma_index": 2,
        "max_bond": 32,
    }
    if fixture["run_partition"] != "CALIBRATION":
        raise ValueError("T3 fixture must use CALIBRATION")
    for key, expected in expected_parameters.items():
        if fixture["parameters"][key] != expected:
            raise ValueError(f"T3 fixture parameter {key} drifted")
    if fixture["geometry"]["n_qubits"] != 14:
        raise ValueError("T3 fixture must contain 14 qubits")
    prefix = _operation_prefix(fixture)
    prefix_hash = _projection_sha256(prefix)

    timer = timing_owner.LayeredTimer()
    checkpoints = {}
    checkpoint_metadata = {}
    operation_records = []
    with timer.span(
        "worker.root",
        scope="child_total",
        kind="fresh_process_worker",
        lane="gcapeps",
        case_id=fixture["case_id"],
        trajectory_id=f"input{INPUT_ID}",
    ):
        with timer.span(
            "worker.initialization",
            scope="initialization",
            kind="candidate_initialization",
            lane="gcapeps",
            case_id=fixture["case_id"],
            trajectory_id=f"input{INPUT_ID}",
        ):
            state = _initialize_state(
                engine=engine,
                fixture=fixture,
                strategy=strategy,
                shadow_evidence=shadow_evidence,
            )
        operation_count = 0
        stopped = False
        for round_row in fixture["carrier_path"]["round_ledger"]:
            round_index = round_row["round_index"]
            with timer.span(
                f"worker.round.{round_index}",
                scope="round",
                kind="persistent_round",
                lane="gcapeps",
                case_id=fixture["case_id"],
                trajectory_id=f"input{INPUT_ID}",
                round_index=round_index,
            ):
                state.advance_round(round_index)
                for operation in round_row["operations"]:
                    operation_index = operation["operation_index"]
                    if operation_index > STOP_AFTER_OPERATION:
                        stopped = True
                        break
                    if operation_index != operation_count:
                        raise ValueError("operation prefix is not ascending")
                    with timer.span(
                        f"worker.operation.{operation_index}",
                        scope="physical_operation",
                        kind=operation["gate_kind"],
                        lane="gcapeps",
                        case_id=fixture["case_id"],
                        trajectory_id=f"input{INPUT_ID}",
                        round_index=round_index,
                        operation_index=operation_index,
                    ):
                        step_index = 0

                        def substep(name: str):
                            nonlocal step_index
                            current = step_index
                            step_index += 1
                            scope = (
                                "evidence_shadow"
                                if name.startswith("uncapped_shadow_replay:")
                                else "named_algorithm_substep"
                            )
                            return timer.span(
                                (
                                    f"worker.operation.{operation_index}."
                                    f"step.{current}"
                                ),
                                scope=scope,
                                kind=name,
                                lane="gcapeps",
                                case_id=fixture["case_id"],
                                trajectory_id=f"input{INPUT_ID}",
                                round_index=round_index,
                                operation_index=operation_index,
                                step_index=current,
                            )

                        metadata = _apply_operation(
                            engine=engine,
                            state=state,
                            operation=operation,
                            strategy=strategy,
                            span_factory=substep,
                        )
                    operation_count += 1
                    if metadata is not None:
                        operation_records.append(metadata)
                    if operation_index in CHECKPOINT_OPERATIONS:
                        with timer.span(
                            f"worker.checkpoint.{operation_index}",
                            scope="checkpoint_contraction",
                            kind="raw_complete_physical_vector",
                            lane="gcapeps",
                            case_id=fixture["case_id"],
                            trajectory_id=f"input{INPUT_ID}",
                            round_index=round_index,
                            operation_index=operation_index,
                        ):
                            vector = state.physical_state_vector()
                        if vector.dtype != np.dtype(np.complex128):
                            raise TypeError("checkpoint vector left complex128")
                        checkpoints[operation_index] = vector
                        if metadata is None:
                            raise ValueError(
                                "registered checkpoint is not a collision"
                            )
                        checkpoint_metadata[operation_index] = metadata
                if stopped:
                    break
            if stopped:
                break
        if operation_count != STOP_AFTER_OPERATION + 1:
            raise ValueError("worker did not stop immediately after operation 100")
        if set(checkpoints) != set(CHECKPOINT_OPERATIONS):
            raise ValueError("worker did not materialize both T3 checkpoints")

        with timer.span(
            "worker.serialization",
            scope="serialization",
            kind="raw_vector_encoding",
            lane="gcapeps",
            case_id=fixture["case_id"],
            trajectory_id=f"input{INPUT_ID}",
        ):
            encoded_checkpoints = {}
            for operation_index, vector in checkpoints.items():
                pre_metric = common.vector_pre_metric(
                    vector,
                    n_qubits=fixture["geometry"]["n_qubits"],
                )
                encoded = common.encode_ndarray_v1(vector, dtype="<c16")
                if (
                    encoded["data_sha256"]
                    != pre_metric["raw_vector_sha256"]
                ):
                    raise ValueError("checkpoint changed during serialization")
                encoded_checkpoints[str(operation_index)] = {
                    "operation_index": operation_index,
                    "pre_metric": pre_metric,
                    "vector": encoded,
                }

        with timer.span(
            "worker.accounting",
            scope="publication_accounting",
            kind="core_projection",
            lane="gcapeps",
            case_id=fixture["case_id"],
            trajectory_id=f"input{INPUT_ID}",
        ):
            native_rows = [
                row
                for row in operation_records
                if row["strategy"] == NATIVE_STRATEGY
            ]
            shadow_span_count = sum(
                1
                for row in timer._spans
                if row["scope"] == "evidence_shadow"
            )
            shadow_bytes = sum(
                row["native_execution_ledger"]["shadow_evidence_bytes"]
                for row in native_rows
            )
            if strategy == NATIVE_STRATEGY and not shadow_evidence:
                if (
                    shadow_builder_calls != 0
                    or shadow_span_count != 0
                    or shadow_bytes != 0
                ):
                    raise ValueError("no-shadow child emitted shadow work")
                for operation_row in native_rows:
                    for split in operation_row[
                        "native_execution_ledger"
                    ]["split_records"]:
                        if split["cause"] != _NO_SHADOW_CAUSE:
                            raise ValueError(
                                "no-shadow split inferred an evidence cause"
                            )
            if strategy == NATIVE_STRATEGY and shadow_evidence:
                if (
                    shadow_builder_calls <= 0
                    or shadow_builder_calls != shadow_span_count
                    or shadow_bytes <= 0
                ):
                    raise ValueError(
                        "evidence shadow builder/span/byte accounting differs"
                    )
            core = {
                "schema": SCHEMA,
                "formal_claim_eligible": False,
                "faithfulness_claim": False,
                "performance_claim": False,
                "lane": (
                    "gcapeps_native_finite_cap_development"
                    if strategy == NATIVE_STRATEGY
                    else "gcapeps_exact_tree_compress_diagnostic_only"
                ),
                "strategy": strategy,
                "legacy_diagnostic_only": strategy == LEGACY_STRATEGY,
                "shadow_evidence_enabled": shadow_evidence,
                "environment": dict(environment_receipt),
                "fixture_identity": {
                    "case_id": fixture["case_id"],
                    "fixture_projection_sha256": fixture_hash,
                    "operation_prefix_count": len(prefix),
                    "operation_prefix_sha256": prefix_hash,
                    "input_id": INPUT_ID,
                    "stop_after_operation": STOP_AFTER_OPERATION,
                    "checkpoint_operations": list(CHECKPOINT_OPERATIONS),
                },
                "split_policy": dict(engine.SPLIT_POLICY),
                "operation_count": operation_count,
                "checkpoint_metadata": {
                    str(index): checkpoint_metadata[index]
                    for index in CHECKPOINT_OPERATIONS
                },
                "operation_records": operation_records,
                "checkpoints": encoded_checkpoints,
                "shadow_builder_call_count": shadow_builder_calls,
                "shadow_span_count": shadow_span_count,
                "shadow_evidence_bytes": shadow_bytes,
                "shadow_builder_instrumentation": {
                    "no_shadow_uses_throwing_sentinel": (
                        strategy == NATIVE_STRATEGY
                        and not shadow_evidence
                    ),
                    "evidence_uses_counting_wrapper": (
                        strategy == NATIVE_STRATEGY
                        and shadow_evidence
                    ),
                    "original_builder_restored_before_return": True,
                },
                "source_identity": {
                    "worker_source_sha256": _source_sha256(
                        Path(__file__).resolve(strict=True)
                    ),
                    "fixture_owner_source_sha256": _source_sha256(
                        Path(fixture_owner.__file__).resolve(strict=True)
                    ),
                    "engine_source_sha256": _source_sha256(
                        Path(engine.__file__).resolve(strict=True)
                    ),
                    "native_source_sha256": _source_sha256(
                        _FORK_ROOT
                        / "quimb/experimental/gcapeps/native.py"
                    ),
                    "carrier_source_sha256": _source_sha256(
                        _FORK_ROOT
                        / "quimb/experimental/gcapeps/carrier.py"
                    ),
                    "fork": _fork_identity(quimb),
                    "python_executable": str(
                        Path(sys.executable).resolve(strict=True)
                    ),
                    "python_version": sys.version,
                    "numpy_version": np.__version__,
                    "stim_version": getattr(stim, "__version__", None),
                },
                "stdout_write_included_in_timing": False,
                "claim_boundary": (
                    "fresh-process deterministic finite-cap engineering "
                    "regression only; not PEPS faithfulness, a QEC Record, "
                    "or a speed claim"
                ),
                "result_projection_sha256": "",
            }
    native_owner._build_native_evidence_shadow = original_shadow_builder
    timing = timer.finish()
    result = {
        **core,
        "timing": timing,
    }
    result["result_projection_sha256"] = _projection_sha256(
        {
            key: value
            for key, value in result.items()
            if key != "result_projection_sha256"
        }
    )
    return result


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--thread-count", type=int, choices=(1, 4), required=True)
    parser.add_argument(
        "--strategy",
        choices=STRATEGIES,
        default=NATIVE_STRATEGY,
    )
    parser.add_argument("--shadow-evidence", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    environment = validate_child_environment(args.thread_count)
    fixture = _parse_fixture(sys.stdin.buffer.read())
    result = _run(
        fixture=fixture,
        environment_receipt=environment,
        strategy=args.strategy,
        shadow_evidence=args.shadow_evidence,
    )
    sys.stdout.buffer.write(_canonical_json_bytes(result))
    sys.stdout.buffer.write(b"\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
