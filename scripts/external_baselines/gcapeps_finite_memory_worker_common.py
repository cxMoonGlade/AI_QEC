#!/usr/bin/env python3
"""Shared GCAPEPS worker mechanics for the finite-memory benchmark."""

from __future__ import annotations

import base64
from dataclasses import asdict, fields, is_dataclass
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


_GC_CARRIER_ROLES = frozenset(
    {
        "carrier_candidate",
        "carrier_committed",
        "evidence_shadow",
        "exact_construction_candidate",
        "native_execution_candidate",
        "state_carrier_candidate",
        "state_committed_carrier",
        "state_predecessor_carrier",
    }
)
_GC_FRAME_ROLES = frozenset(
    {"frame_candidate", "frame_predecessor", "state_frame"}
)
_GC_ARRAY_ROLES = frozenset(
    {
        "checkpoint_predecessor_vector",
        "checkpoint_working_vector",
        "compressed_validation_vector",
        "compression_validation_difference",
        "dense_before_validation_vector",
        "literal_lift_array",
        "physical_checkpoint_vector",
        "residual_checkpoint_vector",
        "untruncated_validation_vector",
    }
)
_GC_LEDGER_ROLES = frozenset(
    {
        "candidate_product_maps",
        "carrier_predecessor_state",
        "committed_residual_update",
        "compression_ledger",
        "compression_ledger_in_progress",
        "construction_ledger",
        "construction_validation_snapshot",
        "dense_operator_action_evidence",
        "pending_residual_update",
        "pending_routing_event",
        "route_plan",
        "shadow_replay_ledger_in_progress",
        "signed_pullback_result",
        "state_routing_history",
    }
)
_GC_ROOT_ROLES = (
    _GC_CARRIER_ROLES | _GC_FRAME_ROLES | _GC_ARRAY_ROLES | _GC_LEDGER_ROLES
)


def new_memory_tracker(*, evidence: bool):
    memory = load_sibling("gcapeps_finite_memory_logical_memory")
    return memory.LogicalMemoryTracker(
        tensor_role="gc_residual",
        evidence=evidence,
    )


def _metadata_value(metadata, name: str):
    if isinstance(metadata, Mapping):
        return metadata[name]
    return getattr(metadata, name)


def _canonical_projection(value: Any, *, _seen=None) -> Any:
    """Project a live ledger without copying any owned NumPy buffer."""

    if _seen is None:
        _seen = set()
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("logical ledger contains a non-finite float")
        return value
    if isinstance(value, complex):
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            raise ValueError("logical ledger contains non-finite complex data")
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, np.generic):
        return _canonical_projection(value.item(), _seen=_seen)
    if isinstance(value, np.ndarray):
        return {
            "array_reference": True,
            "dtype": value.dtype.str,
            "shape": list(value.shape),
            "nbytes": int(value.nbytes),
        }
    if isinstance(value, bytes):
        return {
            "bytes_reference": True,
            "length": len(value),
            "sha256": hashlib.sha256(value).hexdigest(),
        }
    if hasattr(value, "_circuit") and hasattr(value._circuit, "_psi"):
        return {
            "owned_carrier_reference": type(value).__name__,
            "revision": int(value._revision),
            "construction_epoch": int(value._construction_epoch),
        }
    if hasattr(value, "_psi") and hasattr(value, "gauges"):
        return {
            "owned_circuit_reference": type(value).__name__,
            "tensor_count": len(value._psi.tensors),
            "gauge_count": len(value.gauges),
        }
    if hasattr(value, "as_stim_tableau") and hasattr(value, "num_qubits"):
        return {
            "owned_frame_reference": type(value).__name__,
            "num_qubits": int(value.num_qubits),
            "revision": int(value.revision),
        }

    identity = id(value)
    if identity in _seen:
        return {"shared_reference": type(value).__name__}
    _seen.add(identity)
    try:
        if is_dataclass(value):
            return {
                field.name: _canonical_projection(
                    getattr(value, field.name),
                    _seen=_seen,
                )
                for field in fields(value)
            }
        if isinstance(value, Mapping):
            output = {}
            for key, item in value.items():
                projected_key = str(key)
                if projected_key in output:
                    raise ValueError("logical ledger keys collide as strings")
                output[projected_key] = _canonical_projection(
                    item,
                    _seen=_seen,
                )
            return output
        if isinstance(value, (tuple, list)):
            return [
                _canonical_projection(item, _seen=_seen) for item in value
            ]
        if isinstance(value, (set, frozenset)):
            projected = [
                _canonical_projection(item, _seen=_seen) for item in value
            ]
            return sorted(
                projected,
                key=lambda item: json.dumps(
                    item,
                    ensure_ascii=True,
                    allow_nan=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            )
    finally:
        _seen.remove(identity)
    raise TypeError(
        "unsupported logical-ledger value "
        f"{type(value).__module__}.{type(value).__name__}"
    )


def _circuit_arrays(circuit):
    return (
        [np.asarray(tensor.data) for tensor in circuit._psi.tensors],
        list(circuit.gauges.values()),
    )


class _GCRootInventory:
    """Classify one synchronous set of privately owned GC roots."""

    def __init__(self, *, engine):
        self.engine = engine
        self.carrier_arrays = []
        self.gauge_arrays = []
        self.loose_arrays = []
        self.frame_payloads = []
        self.ledger_payloads = []
        self._carriers = set()
        self._circuits = set()
        self._frames = set()
        self._ledgers = set()

    def add_carrier(self, value) -> None:
        if hasattr(value, "_circuit") and hasattr(value._circuit, "_psi"):
            identity = id(value)
            if identity in self._carriers:
                return
            self._carriers.add(identity)
            self.ledger_payloads.append(
                {
                    "revision": int(value._revision),
                    "construction_epoch": int(value._construction_epoch),
                    "routed_rank_products": _canonical_projection(
                        value._routed_rank_products
                    ),
                    "refactor_operator_schmidt_products": (
                        _canonical_projection(
                            value._refactor_operator_schmidt_products
                        )
                    ),
                    "physical_gate_count": len(value._circuit._gates),
                }
            )
            self.add_circuit(value._circuit)
            return
        self.add_circuit(value)

    def add_circuit(self, circuit) -> None:
        if not hasattr(circuit, "_psi") or not hasattr(circuit, "gauges"):
            raise TypeError("GC carrier root is not an owned Quimb circuit")
        identity = id(circuit)
        if identity in self._circuits:
            return
        self._circuits.add(identity)
        tensors, gauges = _circuit_arrays(circuit)
        self.carrier_arrays.extend(tensors)
        self.gauge_arrays.extend(gauges)

    def add_frame(self, frame) -> None:
        identity = id(frame)
        if identity in self._frames:
            return
        self._frames.add(identity)
        self.frame_payloads.append(self.engine._frame_payload(frame))

    def add_ledger(self, value) -> None:
        identity = id(value)
        if identity in self._ledgers:
            return
        self._ledgers.add(identity)
        self.ledger_payloads.append(_canonical_projection(value))
        self._walk_nested_owned_arrays(value)

    def _walk_nested_owned_arrays(self, value, *, seen=None) -> None:
        if seen is None:
            seen = set()
        if isinstance(value, np.ndarray):
            self.loose_arrays.append(value)
            return
        if hasattr(value, "_circuit") and hasattr(value._circuit, "_psi"):
            self.add_carrier(value)
            return
        if hasattr(value, "_psi") and hasattr(value, "gauges"):
            self.add_circuit(value)
            return
        if value is None or isinstance(
            value,
            (bool, int, float, complex, str, bytes, np.generic),
        ):
            return
        identity = id(value)
        if identity in seen:
            return
        seen.add(identity)
        if is_dataclass(value):
            for field in fields(value):
                self._walk_nested_owned_arrays(
                    getattr(value, field.name),
                    seen=seen,
                )
        elif isinstance(value, Mapping):
            for key, item in value.items():
                self._walk_nested_owned_arrays(key, seen=seen)
                self._walk_nested_owned_arrays(item, seen=seen)
        elif isinstance(value, (tuple, list, set, frozenset)):
            for item in value:
                self._walk_nested_owned_arrays(item, seen=seen)

    def add_root(self, root, role: str) -> None:
        if role not in _GC_ROOT_ROLES:
            raise TypeError(f"unaccounted GC ownership root role {role!r}")
        if role in _GC_CARRIER_ROLES:
            self.add_carrier(root)
        elif role in _GC_FRAME_ROLES:
            self.add_frame(root)
        elif role in _GC_ARRAY_ROLES:
            if not isinstance(root, np.ndarray):
                raise TypeError(
                    f"GC ownership array role {role!r} is not ndarray"
                )
            self.loose_arrays.append(root)
        else:
            self.add_ledger(root)


class _GCTrajectoryMemory:
    def __init__(
        self,
        *,
        tracker,
        branch: str,
        state,
        operation_ledger,
        split_records,
        checkpoints,
        engine,
    ):
        if branch not in {"base", "evidence", "probe"}:
            raise ValueError("unknown GC logical-memory branch")
        self.memory = load_sibling("gcapeps_finite_memory_logical_memory")
        self.tracker = tracker
        self.branch = branch
        self.state = state
        self.operation_ledger = operation_ledger
        self.split_records = split_records
        self.checkpoints = checkpoints
        self.engine = engine

    def _inventory(self, roots=(), roles=()):
        roots = tuple(roots)
        roles = tuple(roles)
        if len(roots) != len(roles):
            raise ValueError("GC ownership roots and roles differ in length")
        inventory = _GCRootInventory(engine=self.engine)
        inventory.add_carrier(self.state.state._carrier)
        inventory.add_frame(self.state.state._frame)
        inventory.add_ledger(self.state.state._events)
        inventory.add_ledger(self.state.physical_frame_transcript)
        inventory.add_ledger(self.state.pullback_rows)
        inventory.add_ledger(self.state.algorithm_ledger)
        inventory.add_ledger(self.operation_ledger)
        for root, role in zip(roots, roles):
            inventory.add_root(root, role)
        return inventory

    def _persistent_evidence_arrays(self):
        arrays = list(self.checkpoints.values())
        inventory = _GCRootInventory(engine=self.engine)
        for row in self.split_records:
            inventory._walk_nested_owned_arrays(row)
        arrays.extend(inventory.loose_arrays)
        return arrays

    def _evidence_ledgers(self, inventory, metadata=None):
        payloads = [
            *inventory.frame_payloads,
            *inventory.ledger_payloads,
            _canonical_projection(self.split_records),
        ]
        if metadata is not None:
            payloads.append(
                {
                    "ownership_event": _canonical_projection(metadata),
                }
            )
        return payloads

    def sample_committed(self, label: str, *, final: bool = False):
        inventory = self._inventory()
        sample = self.memory.measure_logical_memory(
            label=label,
            tensor_role="gc_residual",
            carrier_arrays=inventory.carrier_arrays,
            gauge_arrays=inventory.gauge_arrays,
            frame_payloads=inventory.frame_payloads,
            ledger_payloads=inventory.ledger_payloads,
        )
        self.tracker.sample_committed(sample, final=final)

    def sample_evidence(self, label: str, *, metadata=None):
        inventory = self._inventory()
        sample = self.memory.measure_logical_memory(
            label=label,
            tensor_role="none",
            evidence_auxiliary_arrays=(
                *inventory.carrier_arrays,
                *inventory.gauge_arrays,
                *inventory.loose_arrays,
                *self._persistent_evidence_arrays(),
            ),
            evidence_auxiliary_ledger_payloads=self._evidence_ledgers(
                inventory,
                metadata,
            ),
        )
        self.tracker.sample_evidence(sample)

    def callback(self, event, roots, metadata):
        roles = tuple(_metadata_value(metadata, "root_roles"))
        roots = tuple(roots)
        inventory = self._inventory(roots, roles)
        label = (
            f"{self.branch}:{event}:"
            f"{_metadata_value(metadata, 'scope')}:"
            f"{_metadata_value(metadata, 'checkpoint')}"
        )
        evidence_only = bool(_metadata_value(metadata, "evidence_only"))
        if self.branch in {"base", "probe"} and not evidence_only:
            sample = self.memory.measure_logical_memory(
                label=label,
                tensor_role="gc_residual",
                carrier_arrays=inventory.carrier_arrays,
                gauge_arrays=inventory.gauge_arrays,
                frame_payloads=inventory.frame_payloads,
                ledger_payloads=inventory.ledger_payloads,
            )
            self.tracker.sample_algorithm(sample)
        if self.branch in {"evidence", "probe"}:
            sample = self.memory.measure_logical_memory(
                label=label,
                tensor_role="none",
                evidence_auxiliary_arrays=(
                    *inventory.carrier_arrays,
                    *inventory.gauge_arrays,
                    *inventory.loose_arrays,
                    *self._persistent_evidence_arrays(),
                ),
                evidence_auxiliary_ledger_payloads=(
                    *self._evidence_ledgers(inventory, metadata),
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


def _split_scope(name: str) -> str:
    if name.startswith("uncapped_shadow_replay"):
        return "uncapped_shadow_replay"
    return "named_algorithm_substep"


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
    engine = load_sibling("gcapeps_finite_memory_engine")
    lane = "gcapeps"
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
        state = engine.GCState.initialize(
            fixture,
            input_id,
            instrumented=instrumented,
        )
    checkpoints = {}
    split_records = []
    operation_ledger = []
    round_continuity_ledger = []
    if memory_branch is None:
        memory_branch = "probe" if instrumented else "base"
    if memory_branch not in {"base", "evidence", "probe"}:
        raise ValueError("unknown GC logical-memory branch")
    if memory_tracker is None:
        memory_tracker = new_memory_tracker(
            evidence=memory_branch in {"evidence", "probe"},
        )
    memory_sampler = _GCTrajectoryMemory(
        tracker=memory_tracker,
        branch=memory_branch,
        state=state,
        operation_ledger=operation_ledger,
        split_records=split_records,
        checkpoints=checkpoints,
        engine=engine,
    )
    if memory_branch in {"base", "probe"}:
        memory_sampler.sample_committed("after_initialization")
    if memory_branch in {"evidence", "probe"}:
        memory_sampler.sample_evidence("after_instrumented_initialization")
    if materialize_checkpoints and 0 in fixture["checkpoints"]:
        with timer.span(
            f"{span_prefix}.checkpoint.0",
            scope="checkpoint_evidence_materialization",
            kind="state_vector_and_frame_lift",
            lane=lane,
            case_id=case_id,
            trajectory_id=trajectory_id,
            round_index=0,
        ):
            checkpoints[0] = state.physical_state_vector(
                ownership_callback=memory_sampler.callback,
            )
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
            raise ValueError("GC candidate state restarted between rounds")
        with timer.span(
            f"{span_prefix}.round.{round_index}",
            scope="instrumented_round" if instrumented else "round",
            kind="round",
            lane=lane,
            case_id=case_id,
            trajectory_id=trajectory_id,
            round_index=round_index,
        ):
            state.advance_round(round_index)
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
                        if not isinstance(name, str) or not name:
                            raise ValueError("GC substep name must be nonempty")
                        current = step_index
                        step_index += 1
                        base_scope = _split_scope(name)
                        scope = (
                            base_scope
                            if base_scope == "uncapped_shadow_replay"
                            else (
                                "named_instrumented_algorithm_substep"
                                if instrumented
                                else "named_algorithm_substep"
                            )
                        )
                        return timer.span(
                            (
                                f"{span_prefix}.operation.{operation_index}."
                                f"step.{current}"
                            ),
                            scope=scope,
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
                        span_factory=substep,
                        ownership_callback=memory_sampler.callback,
                    )
                operation_count += 1
                operation_ledger[-1]["status"] = "committed"
                positive_in_operation = False
                if record is not None:
                    for split in record["compression_ledger"].split_records:
                        split_records.append(
                            {
                                "operation_index": operation_index,
                                "round_index": round_index,
                                "collision_ordinal": operation[
                                    "collision_ordinal"
                                ],
                                "split": split,
                            }
                        )
                        positive_in_operation |= (
                            split.positive_discarded_weight
                        )
                if memory_branch in {"base", "probe"}:
                    memory_sampler.sample_committed(
                        f"after_operation_{operation_index}"
                    )
                if memory_branch in {"evidence", "probe"}:
                    memory_sampler.sample_evidence(
                        f"after_operation_{operation_index}"
                    )
                if (
                    positive_in_operation
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
                    kind="state_vector_and_frame_lift",
                    lane=lane,
                    case_id=case_id,
                    trajectory_id=trajectory_id,
                    round_index=round_index,
                ):
                    checkpoints[round_index] = state.physical_state_vector(
                        ownership_callback=memory_sampler.callback,
                    )
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
        "pullback_rows": list(state.pullback_rows),
        "algorithm_ledger": list(state.algorithm_ledger),
        "operation_count": operation_count,
        "stop_locator": stop_locator,
        "max_exact_precompression_bond": (
            state.max_exact_precompression_bond
        ),
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
    for wrapper in rows:
        split = wrapper["split"]
        encoded = asdict(split)
        for field in ("full_singular_values", "kept_singular_values"):
            values = getattr(split, field)
            if values is not None:
                array = np.ascontiguousarray(values, dtype=np.float64)
                encoded[field] = encode_ndarray_v1(array, dtype="<f8")
        output_row = {
            "operation_index": wrapper["operation_index"],
            "round_index": wrapper["round_index"],
            "collision_ordinal": wrapper["collision_ordinal"],
            **encoded,
        }
        output_row["spectrum_producer_binding_sha256"] = hashlib.sha256(
            json.dumps(
                {
                    "schema": (
                        "error_coupling_simulator.external."
                        "gcapeps_finite_memory.split_spectrum_producer.v1"
                    ),
                    "lane": "gcapeps",
                    "split_row": output_row,
                },
                ensure_ascii=True,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("ascii")
        ).hexdigest()
        output.append(output_row)
    return output


def frozen_base_projection(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "operation_count": result["operation_count"],
        "max_exact_precompression_bond": result[
            "max_exact_precompression_bond"
        ],
        "max_committed_bond": result["max_committed_bond"],
        "final_committed_bond": result["final_committed_bond"],
        "final_carrier_hash": result["final_carrier_hash"],
        "logical_memory": result["logical_memory"],
        "algorithm_ledger": result["algorithm_ledger"],
        "round_continuity_ledger": result[
            "round_continuity_ledger"
        ],
    }
