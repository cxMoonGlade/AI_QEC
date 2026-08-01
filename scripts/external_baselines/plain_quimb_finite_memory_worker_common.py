#!/usr/bin/env python3
"""Shared plain-lane worker mechanics without evaluator or GC imports."""

from __future__ import annotations

import base64
import gc
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np


def load_sibling(name: str):
    path = Path(__file__).resolve(strict=True).with_name(f"{name}.py")
    module_name = f"_gcapeps_fm_worker_{name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load sibling {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def encode_ndarray_v1(array: np.ndarray, *, dtype: str) -> dict[str, Any]:
    if not isinstance(array, np.ndarray) or array.dtype.str != dtype:
        raise TypeError(f"array must already have dtype {dtype}")
    if not array.flags.c_contiguous:
        raise ValueError("array must already be C-contiguous")
    if not np.isfinite(array).all():
        raise ValueError("array contains a non-finite value")
    raw = array.tobytes(order="C")
    return {
        "encoding": "ndarray-v1",
        "dtype": dtype,
        "shape": list(array.shape),
        "order": "C",
        "nbytes": len(raw),
        "data_sha256": hashlib.sha256(raw).hexdigest(),
        "data_base64": base64.b64encode(raw).decode("ascii"),
    }


def vector_pre_metric(vector: np.ndarray, *, n_qubits: int) -> dict[str, Any]:
    if (
        not isinstance(vector, np.ndarray)
        or vector.dtype.str != "<c16"
        or vector.shape != (2**n_qubits,)
        or not vector.flags.c_contiguous
    ):
        raise ValueError("candidate vector identity is invalid")
    if not np.isfinite(vector.real).all() or not np.isfinite(vector.imag).all():
        raise ValueError("candidate vector contains non-finite data")
    z = np.vdot(vector, vector)
    if abs(float(z.imag)) > 1.0e-12 or not math.isfinite(float(z.real)):
        raise ValueError("candidate vector norm residual is invalid")
    if float(z.real) <= 0.0:
        raise ValueError("candidate vector norm is nonpositive")
    raw = vector.tobytes(order="C")
    return {
        "raw_vector_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_norm_squared_real": float(z.real),
        "raw_norm_squared_imag_abs": abs(float(z.imag)),
        "stored_vector_normalized_before_metric": False,
        "metric_local_normalized_copy": True,
        "phase_fit": False,
        "coordinate_permutation": False,
        "dtype_cast": False,
    }


def _root_array(array: np.ndarray) -> np.ndarray:
    root = array
    seen = set()
    while isinstance(root.base, np.ndarray):
        if id(root) in seen:
            raise ValueError("NumPy base cycle")
        seen.add(id(root))
        root = root.base
    return root


def logical_memory(state, *, ledger: Mapping[str, Any]) -> dict[str, Any]:
    categories: dict[str, set[int]] = {
        "carrier_tensor_bytes": set(),
        "gauge_spectrum_bytes": set(),
    }
    roots: dict[int, int] = {}
    for tensor in state.circuit._psi.tensors:
        array = np.asarray(tensor.data)
        root = _root_array(array)
        categories["carrier_tensor_bytes"].add(id(root))
        roots[id(root)] = int(root.nbytes)
    for gauge in state.circuit.gauges.values():
        root = _root_array(gauge)
        categories["gauge_spectrum_bytes"].add(id(root))
        roots[id(root)] = int(root.nbytes)
    overlap = categories["carrier_tensor_bytes"].intersection(
        categories["gauge_spectrum_bytes"]
    )
    if overlap:
        raise ValueError("logical-memory categories alias")
    carrier = sum(roots[key] for key in categories["carrier_tensor_bytes"])
    gauges = sum(roots[key] for key in categories["gauge_spectrum_bytes"])
    ledger_bytes = len(
        json.dumps(
            ledger,
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("ascii")
    )
    total = carrier + gauges + ledger_bytes
    return {
        "tensor_role": "plain_physical",
        "carrier_tensor_bytes": carrier,
        "gauge_spectrum_bytes": gauges,
        "frame_bytes": 0,
        "ledger_bytes": ledger_bytes,
        "total_owned_logical_bytes": total,
    }


def new_memory_tracker(*, evidence: bool):
    memory = load_sibling("gcapeps_finite_memory_logical_memory")
    return memory.LogicalMemoryTracker(
        tensor_role="plain_physical",
        evidence=evidence,
    )


def _circuit_arrays(circuit):
    tensors = [np.asarray(tensor.data) for tensor in circuit._psi.tensors]
    gauges = list(circuit.gauges.values())
    return tensors, gauges


def _split_projection(row: Mapping[str, Any]) -> dict[str, Any]:
    output = {}
    for key, value in row.items():
        if key in {"full_singular_values", "kept_singular_values"}:
            array = value
            output[key] = {
                "array_reference": True,
                "dtype": array.dtype.str,
                "shape": list(array.shape),
                "nbytes": int(array.nbytes),
            }
        else:
            output[key] = value
    return output


class _PlainTrajectoryMemory:
    def __init__(
        self,
        *,
        tracker,
        branch: str,
        state,
        operation_ledger,
        split_records,
        checkpoints,
    ):
        if branch not in {"base", "evidence", "probe"}:
            raise ValueError("unknown plain logical-memory branch")
        self.memory = load_sibling("gcapeps_finite_memory_logical_memory")
        self.tracker = tracker
        self.branch = branch
        self.state = state
        self.operation_ledger = operation_ledger
        self.split_records = split_records
        self.checkpoints = checkpoints

    def _persistent_evidence_arrays(self):
        arrays = list(self.checkpoints.values())
        for row in self.split_records:
            arrays.extend(
                (
                    row["full_singular_values"],
                    row["kept_singular_values"],
                )
            )
        return arrays

    def _evidence_ledger_payload(self, metadata=None, extra_records=()):
        return {
            "operation_ledger": self.operation_ledger,
            "split_records": [
                _split_projection(row)
                for row in (*self.split_records, *tuple(extra_records))
            ],
            "ownership_event": metadata,
        }

    def _collect_callback_roots(self, roots, roles):
        circuits = []
        arrays = []
        records = []
        for root, role in zip(roots, roles):
            if hasattr(root, "_psi") and hasattr(root, "gauges"):
                circuits.append(root)
            elif isinstance(root, np.ndarray):
                arrays.append(root)
            elif (
                isinstance(root, Mapping)
                and "full_singular_values" in root
                and "kept_singular_values" in root
            ):
                records.append(root)
                arrays.extend(
                    (
                        root["full_singular_values"],
                        root["kept_singular_values"],
                    )
                )
            else:
                raise TypeError(
                    f"unaccounted plain ownership root role {role!r}"
                )
        return circuits, arrays, records

    def sample_committed(self, label: str, *, final: bool = False):
        tensors, gauges = _circuit_arrays(self.state.circuit)
        sample = self.memory.measure_logical_memory(
            label=label,
            tensor_role="plain_physical",
            carrier_arrays=tensors,
            gauge_arrays=gauges,
            ledger_payloads=(self.operation_ledger,),
        )
        self.tracker.sample_committed(sample, final=final)

    def sample_evidence(self, label: str, *, metadata=None):
        tensors, gauges = _circuit_arrays(self.state.circuit)
        sample = self.memory.measure_logical_memory(
            label=label,
            tensor_role="none",
            evidence_auxiliary_arrays=(
                *tensors,
                *gauges,
                *self._persistent_evidence_arrays(),
            ),
            evidence_auxiliary_ledger_payloads=(
                self._evidence_ledger_payload(metadata),
            ),
        )
        self.tracker.sample_evidence(sample)

    def callback(self, event, roots, metadata):
        roles = tuple(metadata["root_roles"])
        circuits, arrays, records = self._collect_callback_roots(
            roots,
            roles,
        )
        label = f"{self.branch}:{event}:{metadata['checkpoint']}"
        if self.branch in {"base", "probe"}:
            tensor_arrays = []
            gauge_arrays = []
            for circuit in circuits:
                tensors, gauges = _circuit_arrays(circuit)
                tensor_arrays.extend(tensors)
                gauge_arrays.extend(gauges)
            sample = self.memory.measure_logical_memory(
                label=label,
                tensor_role="plain_physical",
                carrier_arrays=tensor_arrays,
                gauge_arrays=gauge_arrays,
                ledger_payloads=(self.operation_ledger,),
            )
            self.tracker.sample_algorithm(sample)
        if self.branch in {"evidence", "probe"}:
            auxiliary_arrays = list(arrays)
            for circuit in circuits:
                tensors, gauges = _circuit_arrays(circuit)
                auxiliary_arrays.extend((*tensors, *gauges))
            auxiliary_arrays.extend(self._persistent_evidence_arrays())
            sample = self.memory.measure_logical_memory(
                label=label,
                tensor_role="none",
                evidence_auxiliary_arrays=auxiliary_arrays,
                evidence_auxiliary_ledger_payloads=(
                    self._evidence_ledger_payload(metadata, records),
                ),
            )
            self.tracker.sample_evidence(sample)

_FIXTURE_VALIDATOR_SIBLINGS = {
    "error_coupling_simulator.external.gcapeps_finite_memory.fixture.v1": (
        "emit_gcapeps_finite_memory_fixture"
    ),
    "error_coupling_simulator.external.gcapeps_finite_memory.fixture.v2": (
        "emit_gcapeps_finite_memory_fixture_v2"
    ),
}


def validate_fixture(fixture: Mapping[str, Any]) -> str:
    """Dispatch to the emitter that owns the fixture's declared schema.

    v1 routes to the v1 emitter, v2 to the v2 emitter; any other schema is
    rejected without fallback.  Each owning emitter then re-checks the
    schema itself and enforces byte-identical deterministic reconstruction.
    """

    if not isinstance(fixture, Mapping):
        raise TypeError("fixture must be a mapping")
    schema = fixture.get("schema")
    sibling = (
        _FIXTURE_VALIDATOR_SIBLINGS.get(schema)
        if isinstance(schema, str)
        else None
    )
    if sibling is None:
        raise ValueError(
            f"unsupported fixture schema: {schema!r}; supported schemas "
            f"are {sorted(_FIXTURE_VALIDATOR_SIBLINGS)}"
        )
    emitter = load_sibling(sibling)
    return emitter.validate_fixture(fixture)


def run_trajectory(
    *,
    fixture: Mapping[str, Any],
    input_id: int,
    instrumented: bool,
    materialize_checkpoints: bool,
    timer,
    span_prefix: str,
    initialization_scope: str,
    stop_after_first_positive_operation: bool = False,
    memory_tracker=None,
    memory_branch: str | None = None,
    record_round_continuity: bool = False,
):
    engine = load_sibling("plain_quimb_finite_memory_engine")
    lane = "plain"
    case_id = fixture["case_id"]
    trajectory_id = f"input{input_id}"
    with timer.span(
        f"{span_prefix}.init",
        scope=initialization_scope,
        kind="candidate_initialization",
        lane=lane,
        case_id=case_id,
        trajectory_id=trajectory_id,
    ):
        state = engine.PlainState.initialize(fixture, input_id)
    checkpoints = {}
    split_records = []
    operation_ledger = []
    round_continuity_ledger = []
    if memory_branch is None:
        memory_branch = "probe" if instrumented else "base"
    if memory_branch not in {"base", "evidence", "probe"}:
        raise ValueError("unknown plain logical-memory branch")
    if memory_tracker is None:
        memory_tracker = new_memory_tracker(
            evidence=memory_branch in {"evidence", "probe"},
        )
    memory_sampler = _PlainTrajectoryMemory(
        tracker=memory_tracker,
        branch=memory_branch,
        state=state,
        operation_ledger=operation_ledger,
        split_records=split_records,
        checkpoints=checkpoints,
    )
    if memory_branch in {"base", "probe"}:
        memory_sampler.sample_committed("after_initialization")
    if memory_branch in {"evidence", "probe"}:
        memory_sampler.sample_evidence("after_instrumented_initialization")
    if materialize_checkpoints and 0 in fixture["checkpoints"]:
        with timer.span(
            f"{span_prefix}.checkpoint.0",
            scope="checkpoint_evidence_materialization",
            kind="state_vector",
            lane=lane,
            case_id=case_id,
            trajectory_id=trajectory_id,
            round_index=0,
        ):
            checkpoints[0] = state.state_vector()
        if memory_branch in {"evidence", "probe"}:
            memory_sampler.sample_evidence("after_checkpoint_0")
    operation_count = 0
    stop_locator = None
    previous_round_end_sha256 = (
        state.final_carrier_hash()["sha256"]
        if record_round_continuity
        else None
    )
    for round_row in fixture["carrier_path"]["round_ledger"]:
        round_index = round_row["round_index"]
        round_start_sha256 = (
            state.final_carrier_hash()["sha256"]
            if record_round_continuity
            else None
        )
        if (
            record_round_continuity
            and round_start_sha256 != previous_round_end_sha256
        ):
            raise ValueError("plain candidate state restarted between rounds")
        with timer.span(
            f"{span_prefix}.round.{round_index}",
            scope="instrumented_round" if instrumented else "round",
            kind="round",
            lane=lane,
            case_id=case_id,
            trajectory_id=trajectory_id,
            round_index=round_index,
        ):
            for operation in round_row["operations"]:
                operation_index = operation["operation_index"]
                if operation_index != operation_count:
                    raise ValueError("operation sequence is not ascending")
                operation_ledger.append(
                    {
                        "operation": operation,
                        "status": "pending",
                    }
                )
                with timer.span(
                    f"{span_prefix}.operation.{operation_index}",
                    scope="physical_operation",
                    kind=operation["gate_kind"],
                    lane=lane,
                    case_id=case_id,
                    trajectory_id=trajectory_id,
                    round_index=round_index,
                    operation_index=operation_index,
                ):
                    step_index = 0

                    def substep(name: str):
                        nonlocal step_index
                        current = step_index
                        step_index += 1
                        return timer.span(
                            (
                                f"{span_prefix}.operation.{operation_index}."
                                f"step.{current}"
                            ),
                            scope=(
                                "uncapped_shadow_replay"
                                if name == "uncapped_shadow_replay"
                                else (
                                    "named_instrumented_algorithm_substep"
                                    if instrumented
                                    else "named_algorithm_substep"
                                )
                            ),
                            kind=name,
                            lane=lane,
                            case_id=case_id,
                            trajectory_id=trajectory_id,
                            round_index=round_index,
                            operation_index=operation_index,
                            step_index=current,
                        )

                    record = state.apply_operation(
                        operation,
                        instrumented=instrumented,
                        span_factory=substep,
                        ownership_callback=memory_sampler.callback,
                    )
                operation_count += 1
                operation_ledger[-1]["status"] = "committed"
                if record is not None:
                    split_records.append(record)
                if memory_branch in {"base", "probe"}:
                    memory_sampler.sample_committed(
                        f"after_operation_{operation_index}"
                    )
                if memory_branch in {"evidence", "probe"}:
                    memory_sampler.sample_evidence(
                        f"after_operation_{operation_index}"
                    )
                if (
                    record is not None
                    and record["positive_discarded_weight"]
                    and stop_after_first_positive_operation
                ):
                    stop_locator = {
                        "round_index": round_index,
                        "operation_index": operation_index,
                    }
                    break
            if record_round_continuity:
                round_end_sha256 = state.final_carrier_hash()["sha256"]
                round_continuity_ledger.append(
                    {
                        "round_index": round_index,
                        "prior_round_end_state_sha256": (
                            previous_round_end_sha256
                        ),
                        "round_start_state_sha256": round_start_sha256,
                        "round_end_state_sha256": round_end_sha256,
                        "starts_from_prior_round_end": True,
                        "candidate_restarted_between_rounds": False,
                        "memory_reset_between_rounds": False,
                    }
                )
                previous_round_end_sha256 = round_end_sha256
            if (
                materialize_checkpoints
                and round_index in fixture["checkpoints"]
            ):
                with timer.span(
                    f"{span_prefix}.checkpoint.{round_index}",
                    scope="checkpoint_evidence_materialization",
                    kind="state_vector",
                    lane=lane,
                    case_id=case_id,
                    trajectory_id=trajectory_id,
                    round_index=round_index,
                ):
                    checkpoints[round_index] = state.state_vector()
                if memory_branch in {"evidence", "probe"}:
                    memory_sampler.sample_evidence(
                        f"after_checkpoint_{round_index}"
                    )
        if stop_locator is not None:
            break
    carrier_hash = state.final_carrier_hash()
    if memory_branch in {"base", "probe"}:
        memory_sampler.sample_committed("final_committed", final=True)
    if memory_branch in {"evidence", "probe"}:
        memory_sampler.sample_evidence("final_instrumented")
    memory = (
        memory_tracker.report()
        if memory_branch in {"evidence", "probe"}
        else memory_tracker.base_report()
    )
    return {
        "state": state,
        "checkpoint_vectors": checkpoints,
        "split_records": split_records,
        "round_continuity_ledger": round_continuity_ledger,
        "operation_count": operation_count,
        "stop_locator": stop_locator,
        "max_committed_bond": state.max_committed_bond,
        "final_committed_bond": int(state.circuit._psi.max_bond() or 1),
        "final_carrier_hash": carrier_hash,
        "logical_memory": memory,
    }


def release_trajectory(result: dict[str, Any]) -> None:
    result.pop("state", None)
    result.pop("checkpoint_vectors", None)
    gc.collect()


def encode_split_records(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        encoded = dict(row)
        encoded["full_singular_values"] = encode_ndarray_v1(
            row["full_singular_values"],
            dtype="<f8",
        )
        encoded["kept_singular_values"] = encode_ndarray_v1(
            row["kept_singular_values"],
            dtype="<f8",
        )
        encoded["spectrum_producer_binding_sha256"] = hashlib.sha256(
            json.dumps(
                {
                    "schema": (
                        "error_coupling_simulator.external."
                        "gcapeps_finite_memory.split_spectrum_producer.v1"
                    ),
                    "lane": "plain",
                    "split_row": encoded,
                },
                ensure_ascii=True,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("ascii")
        ).hexdigest()
        output.append(encoded)
    return output
