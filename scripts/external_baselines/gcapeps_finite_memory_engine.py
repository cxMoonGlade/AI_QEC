#!/usr/bin/env python3
"""GCAPEPS mechanics for the finite-memory bond-32 benchmark.

This module consumes only the neutral fixture.  Clifford operations live in a
Stim frame and physical Pauli rotations are pulled back into the persistent
Quimb PEPS residual.  The residual uses the fork's opt-in
``exact_tree_then_native_compress`` path.

It deliberately imports neither the independent dense reference, the plain
Quimb worker, SDIM, nor the terminal comparator.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any, Callable, ContextManager, Mapping

import numpy as np
import stim

import quimb.tensor as qtn
from quimb.experimental.gcapeps import (
    GCAPEPSState,
    OwnershipEventMetadata,
    QubitPauliWord,
    StimCliffordFrame,
)


SPLIT_POLICY = {
    "max_bond": 32,
    "cutoff": 0.0,
    "cutoff_mode": "rel",
    "method": "svd",
    "renorm": False,
    "absorb": None,
    "smudge": 1.0e-12,
    "smudge_mode": "floor",
    "power": 1.0,
}
PAULI_ROTATION_STRATEGY = "exact_tree_then_native_compress"
POSITIVE_TAIL_THRESHOLD = 1.0e-12
_PAULI_LABELS = "IXYZ"
PULLBACK_REQUEST_KEYS = (
    "run_partition",
    "case_id",
    "input_id",
    "input_preparation_transcript_sha256",
    "shared_evolution_transcript_sha256",
    "round_prefix",
    "collision_ordinal",
    "round_index",
    "site_index",
    "axis_index",
    "physical_pauli_body",
)


def _load_sibling(name: str):
    path = Path(__file__).resolve(strict=True).with_name(f"{name}.py")
    module_name = f"_gcapeps_fm_gc_{name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load sibling helper {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _root_array(array: np.ndarray) -> np.ndarray:
    root = array
    seen: set[int] = set()
    while isinstance(root.base, np.ndarray):
        if id(root) in seen:
            raise ValueError("NumPy base cycle")
        seen.add(id(root))
        root = root.base
    return root


def _validate_array_precision(circuit) -> None:
    for tensor in circuit._psi.tensors:
        array = np.asarray(tensor.data)
        if array.dtype != np.dtype(np.complex128):
            raise TypeError("GC residual tensor left complex128")
        if not np.isfinite(array.real).all() or not np.isfinite(array.imag).all():
            raise ValueError("GC residual tensor contains non-finite data")
    for index, gauge in circuit.gauges.items():
        if (
            not isinstance(gauge, np.ndarray)
            or gauge.dtype != np.dtype(np.float64)
            or gauge.ndim != 1
            or not gauge.flags.c_contiguous
        ):
            raise TypeError(f"GC gauge {index!r} is not contiguous float64")
        if not np.isfinite(gauge).all() or np.any(gauge < 0.0):
            raise ValueError(f"GC gauge {index!r} is not finite nonnegative")


def _signed_word_text_value(text: str, *, num_qubits: int) -> dict[str, Any]:
    if not isinstance(text, str) or len(text) != num_qubits + 1:
        raise ValueError("signed Pauli text has wrong width")
    if text[0] == "+":
        sign = 1
    elif text[0] == "-":
        sign = -1
    else:
        raise ValueError("signed Pauli text has a non-real phase")
    body = text[1:]
    if any(label not in _PAULI_LABELS for label in body):
        raise ValueError("signed Pauli text has an invalid body")
    return {"sign": sign, "body": body}


def _stim_pauli_value(pauli) -> dict[str, Any]:
    sign_value = complex(pauli.sign)
    if sign_value == 1.0:
        sign = 1
    elif sign_value == -1.0:
        sign = -1
    else:
        raise ValueError("frame generator has non-real Pauli phase")
    return {
        "sign": sign,
        "body": "".join(_PAULI_LABELS[int(pauli[q])] for q in range(len(pauli))),
    }


def _frame_payload(frame: StimCliffordFrame) -> dict[str, Any]:
    tableau = frame.as_stim_tableau()
    return {
        "kind": "stim_signed_images_v1",
        "num_qubits": frame.num_qubits,
        "x_images": [
            _stim_pauli_value(tableau.x_output(q))
            for q in range(frame.num_qubits)
        ],
        "z_images": [
            _stim_pauli_value(tableau.z_output(q))
            for q in range(frame.num_qubits)
        ],
    }


def _stim_circuit(operation: Mapping[str, Any]) -> stim.Circuit:
    gate = operation["gate_kind"]
    targets = tuple(operation["targets"])
    if gate not in {"X", "H", "S", "CX"}:
        raise ValueError(f"unsupported frame Clifford {gate!r}")
    if (gate == "CX") != (len(targets) == 2):
        raise ValueError("CX arity drifted")
    if gate != "CX" and len(targets) != 1:
        raise ValueError("one-qubit Clifford arity drifted")
    circuit = stim.Circuit()
    circuit.append(gate, targets)
    return circuit


def _one_qubit_matrix(kind: str) -> np.ndarray:
    if kind == "X":
        value = [[0.0, 1.0], [1.0, 0.0]]
    elif kind == "H":
        value = [[1.0, 1.0], [1.0, -1.0]]
    elif kind == "S":
        value = [[1.0, 0.0], [0.0, 1.0j]]
    else:
        raise ValueError(f"unsupported one-qubit Clifford {kind!r}")
    out = np.asarray(value, dtype=np.complex128)
    if kind == "H":
        out /= math.sqrt(2.0)
    return out


def _cx_matrix() -> np.ndarray:
    return np.asarray(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0, 0.0],
        ],
        dtype=np.complex128,
    )


def _apply_local_matrix(
    vector: np.ndarray,
    matrix: np.ndarray,
    targets: tuple[int, ...],
    *,
    n_qubits: int,
) -> np.ndarray:
    """Apply a one/two-qubit matrix to a q0-MSB dense vector."""

    if len(targets) not in (1, 2) or len(set(targets)) != len(targets):
        raise ValueError("physical frame lift target arity is invalid")
    if any(target < 0 or target >= n_qubits for target in targets):
        raise ValueError("physical frame lift target is out of range")
    rank = len(targets)
    expected = 1 << rank
    if matrix.shape != (expected, expected):
        raise ValueError("physical frame lift matrix has wrong shape")
    tensor = vector.reshape((2,) * n_qubits)
    rest = tuple(axis for axis in range(n_qubits) if axis not in targets)
    permutation = targets + rest
    inverse = np.argsort(permutation)
    front = np.transpose(tensor, permutation).reshape(expected, -1)
    updated = (matrix @ front).reshape((2,) * n_qubits)
    return np.ascontiguousarray(
        np.transpose(updated, inverse).reshape(-1),
        dtype=np.complex128,
    )


def _lift_frame_transcript(
    residual: np.ndarray,
    transcript: tuple[dict[str, Any], ...],
    *,
    n_qubits: int,
    ownership_callback=None,
    ownership_context: tuple[tuple[Any, ...], tuple[str, ...]] = ((), ()),
) -> np.ndarray:
    if ownership_callback is not None and not callable(ownership_callback):
        raise TypeError("ownership_callback must be callable or None")
    context_roots, context_roles = ownership_context
    context_roots = tuple(context_roots)
    context_roles = tuple(context_roles)
    if len(context_roots) != len(context_roles):
        raise ValueError("ownership context roots and roles differ in length")

    def emit(
        event: str,
        checkpoint: str,
        roots: tuple[Any, ...],
        roles: tuple[str, ...],
        *,
        transition_roles: tuple[str, ...] = (),
    ) -> None:
        if ownership_callback is None:
            return
        all_roots = context_roots + roots
        all_roles = context_roles + roles
        result = ownership_callback(
            event,
            all_roots,
            OwnershipEventMetadata(
                scope="checkpoint_frame_lift",
                checkpoint=checkpoint,
                root_roles=all_roles,
                transition_roles=transition_roles,
                evidence_only=True,
            ),
        )
        if result is not None:
            raise TypeError("ownership_callback must return None")

    vector = np.ascontiguousarray(residual, dtype=np.complex128)
    if vector.shape != (1 << n_qubits,):
        raise ValueError("residual checkpoint vector has wrong shape")
    emit(
        "acquire",
        "residual_vector_materialization",
        (vector,),
        ("checkpoint_working_vector",),
        transition_roles=("checkpoint_working_vector",),
    )
    emit(
        "sample",
        "residual_vector_materialization",
        (vector,),
        ("checkpoint_working_vector",),
    )
    for operation_index, operation in enumerate(transcript):
        kind = operation["gate_kind"]
        targets = tuple(operation["targets"])
        matrix = _cx_matrix() if kind == "CX" else _one_qubit_matrix(kind)
        emit(
            "acquire",
            f"literal_frame_lift_{operation_index}",
            (vector, matrix),
            ("checkpoint_working_vector", "literal_lift_array"),
            transition_roles=("literal_lift_array",),
        )
        updated = _apply_local_matrix(
            vector,
            matrix,
            targets,
            n_qubits=n_qubits,
        )
        emit(
            "sample",
            f"post_literal_frame_lift_{operation_index}",
            (vector, matrix, updated),
            (
                "checkpoint_predecessor_vector",
                "literal_lift_array",
                "checkpoint_working_vector",
            ),
        )
        vector = updated
        del updated, matrix
        emit(
            "release",
            f"literal_frame_lift_release_{operation_index}",
            (vector,),
            ("checkpoint_working_vector",),
            transition_roles=(
                "checkpoint_predecessor_vector",
                "literal_lift_array",
            ),
        )
    emit(
        "sample",
        "pre_checkpoint_vector_handoff",
        (residual, vector),
        ("residual_checkpoint_vector", "physical_checkpoint_vector"),
    )
    emit(
        "release",
        "residual_checkpoint_vector_release",
        (vector,),
        ("physical_checkpoint_vector",),
        transition_roles=("residual_checkpoint_vector",),
    )
    return vector


def _plain_dataclass(value: Any) -> Any:
    """Convert a GCAPEPS ledger to canonical-JSON-compatible primitives."""

    if is_dataclass(value):
        return _plain_dataclass(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(key): _plain_dataclass(item)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        return [_plain_dataclass(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, complex):
        if value.imag != 0.0:
            return {"real": value.real, "imag": value.imag}
        return value.real
    return value


def _algorithm_update_projection(event) -> dict[str, Any]:
    update = event.residual_update
    if update is None:
        return {
            "column": event.column,
            "round_index": event.round_index,
            "operation": event.operation,
            "frame_revision_before": event.frame_revision_before,
            "frame_revision_after": event.frame_revision_after,
            "residual_revision_before": event.residual_revision_before,
            "residual_revision_after": event.residual_revision_after,
        }
    ledger = update.tree_compression_ledger
    compression = None
    if ledger is not None:
        compression = {
            "compression_revision": ledger.compression_revision,
            "construction_epoch_before": ledger.construction_epoch_before,
            "construction_epoch_after": ledger.construction_epoch_after,
            "routed_edge_order": ledger.routed_edge_order,
            "configured_max_bond": ledger.configured_max_bond,
            "configured_cutoff": ledger.configured_cutoff,
            "configured_cutoff_mode": ledger.configured_cutoff_mode,
            "configured_method": ledger.configured_method,
            "configured_renorm": ledger.configured_renorm,
            "configured_absorb": ledger.configured_absorb,
            "configured_smudge": ledger.configured_smudge,
            "configured_power": ledger.configured_power,
            "low_level_contract": ledger.low_level_contract,
            "routed_split_count": len(ledger.split_records),
            "physical_gate_count_before": ledger.physical_gate_count_before,
            "physical_gate_count_after": ledger.physical_gate_count_after,
            "product_maps_reset_to_one_on_commit": (
                ledger.product_maps_reset_to_one_on_commit
            ),
            "counterfactual_lifetime_product_only": (
                ledger.counterfactual_lifetime_product_only
            ),
            "not_a_global_error_bound": ledger.not_a_global_error_bound,
        }
    return _plain_dataclass(
        {
            "column": event.column,
            "round_index": event.round_index,
            "operation": event.operation,
            "frame_revision_before": event.frame_revision_before,
            "frame_revision_after": event.frame_revision_after,
            "residual_revision_before": event.residual_revision_before,
            "residual_revision_after": event.residual_revision_after,
            "physical_pauli": event.physical_pauli,
            "pulled_back_pauli": event.pulled_back_pauli,
            "strategy": update.strategy,
            "support": update.support,
            "dependence_set": update.dependence_set,
            "routing_root": update.routing_root,
            "routing_vertices": update.routing_vertices,
            "routing_tree_edges": update.routing_tree_edges,
            "max_bond_before": update.max_bond_before,
            "max_bond_after": update.max_bond_after,
            "construction_epoch_before": update.construction_epoch_before,
            "construction_epoch_after": update.construction_epoch_after,
            "edge_bonds": update.edge_bonds,
            "resource_ledger": update.resource_ledger,
            "compression": compression,
        }
    )


@dataclass
class GCState:
    fixture: Mapping[str, Any]
    input_id: int
    state: GCAPEPSState
    physical_frame_transcript: list[dict[str, Any]]
    pullback_rows: list[dict[str, Any]]
    algorithm_ledger: list[dict[str, Any]]
    max_exact_precompression_bond: int
    max_committed_bond: int

    @classmethod
    def initialize(
        cls,
        fixture: Mapping[str, Any],
        input_id: int,
        *,
        instrumented: bool,
    ) -> "GCState":
        geometry = fixture["geometry"]
        parameters = fixture["parameters"]
        if parameters["max_bond"] != SPLIT_POLICY["max_bond"]:
            raise ValueError("fixture max_bond disagrees with GC policy")
        circuit = qtn.CircuitPEPSSimpleUpdate(
            N=geometry["n_qubits"],
            edges=tuple(tuple(edge) for edge in geometry["graph_edges"]),
            max_bond=SPLIT_POLICY["max_bond"],
            cutoff=SPLIT_POLICY["cutoff"],
            renorm=SPLIT_POLICY["renorm"],
            gauge_smudge=SPLIT_POLICY["smudge"],
            equilibrate_every=None,
            gate_opts={
                "cutoff_mode": SPLIT_POLICY["cutoff_mode"],
                "method": SPLIT_POLICY["method"],
                "absorb": SPLIT_POLICY["absorb"],
                "power": SPLIT_POLICY["power"],
                "smudge_mode": SPLIT_POLICY["smudge_mode"],
            },
            dtype="complex128",
        )
        if (
            circuit.gate_opts.get("smudge_mode")
            != SPLIT_POLICY["smudge_mode"]
        ):
            raise RuntimeError("GC circuit smudge_mode was not retained")
        input_rows = {
            row["input_id"]: row for row in fixture["inputs"]
        }
        if input_id not in input_rows:
            raise ValueError("input_id is not registered")
        input_row = input_rows[input_id]
        if any(input_row["gc_residual_initial_bits"]):
            raise ValueError("GC residual initialization must be all zero")
        frame = StimCliffordFrame(geometry["n_qubits"])
        transcript: list[dict[str, Any]] = []
        for operation in input_row["gc_frame_preparation_gates"]:
            frame.apply_clifford(_stim_circuit(operation))
            transcript.append(
                {
                    "gate_kind": operation["gate_kind"],
                    "targets": list(operation["targets"]),
                }
            )
        state = GCAPEPSState.from_quimb(
            frame,
            circuit,
            site_order=tuple(range(geometry["n_qubits"])),
            contraction_optimize="greedy",
            pauli_rotation_strategy=PAULI_ROTATION_STRATEGY,
            compression_evidence=instrumented,
        )
        _validate_array_precision(state._carrier._circuit)
        return cls(
            fixture=fixture,
            input_id=input_id,
            state=state,
            physical_frame_transcript=transcript,
            pullback_rows=[],
            algorithm_ledger=[],
            max_exact_precompression_bond=1,
            max_committed_bond=1,
        )

    @property
    def circuit(self):
        """Private owned circuit, exposed only to the benchmark sampler."""

        return self.state._carrier._circuit

    def advance_round(self, round_index: int) -> None:
        if self.state.advance_round() != round_index:
            raise ValueError("GC persistent round cursor drifted")

    def _request_for_operation(
        self,
        operation: Mapping[str, Any],
    ) -> dict[str, Any]:
        matches = [
            request
            for request in self.fixture["sdim_pullback_requests"]
            if request["input_id"] == self.input_id
            and request["collision_ordinal"] == operation["collision_ordinal"]
        ]
        if len(matches) != 1:
            raise ValueError("collision does not map to exactly one pullback request")
        request = dict(matches[0])
        checks = {
            "round_prefix": operation["round_index"],
            "round_index": operation["round_index"],
            "collision_ordinal": operation["collision_ordinal"],
            "site_index": operation["site_index"],
            "axis_index": operation["axis_index"],
            "physical_pauli_body": operation["physical_pauli_body"],
        }
        if any(request[key] != value for key, value in checks.items()):
            raise ValueError("pullback request disagrees with physical operation")
        return request

    def apply_operation(
        self,
        operation: Mapping[str, Any],
        *,
        span_factory: Callable[[str], ContextManager[Any]] | None = None,
        ownership_callback=None,
    ) -> dict[str, Any] | None:
        if operation["operation_class"] == "clifford":
            event = self.state.apply_clifford(
                _stim_circuit(operation),
                span_factory=span_factory,
                ownership_callback=ownership_callback,
            )
            self.physical_frame_transcript.append(
                {
                    "gate_kind": operation["gate_kind"],
                    "targets": list(operation["targets"]),
                }
            )
            self.algorithm_ledger.append(_algorithm_update_projection(event))
            if event.peps_gate_count_before != event.peps_gate_count_after:
                raise ValueError("Clifford frame update changed residual gate count")
            return None

        if operation["operation_class"] != "collision_rotation":
            raise ValueError("unknown neutral operation class")
        if operation["gate_kind"] != "PAULI_ROTATION":
            raise ValueError("collision gate kind drifted")
        physical = QubitPauliWord.from_labels(operation["physical_pauli_body"])
        request = self._request_for_operation(operation)
        event = self.state.apply_pauli_rotation(
            physical,
            float.fromhex(operation["theta_float64_hex"]),
            span_factory=span_factory,
            ownership_callback=ownership_callback,
        )
        update = event.residual_update
        if update is None or update.strategy != (
            "exact_tree_then_native_identity_compress"
        ):
            raise ValueError("collision did not use exact-tree native compression")
        if event.pulled_back_pauli is None:
            raise ValueError("collision event omitted the signed pullback")
        if event.physical_pauli != str(physical):
            raise ValueError("collision event physical Pauli disagrees")
        pulled_value = _signed_word_text_value(
            event.pulled_back_pauli,
            num_qubits=physical.num_qubits,
        )
        self.pullback_rows.append(
            {
                **request,
                "physical_sign": 1,
                "physical_body": operation["physical_pauli_body"],
                "pulled_back_sign": pulled_value["sign"],
                "pulled_back_body": pulled_value["body"],
            }
        )
        ledger = update.tree_compression_ledger
        if ledger is None:
            raise ValueError("tree-compression collision omitted its ledger")
        exact_bonds = [
            row.exact_precompression_bond for row in ledger.split_records
        ]
        if exact_bonds:
            self.max_exact_precompression_bond = max(
                self.max_exact_precompression_bond,
                *exact_bonds,
            )
        self.max_committed_bond = max(
            self.max_committed_bond,
            update.max_bond_after,
        )
        self.algorithm_ledger.append(_algorithm_update_projection(event))
        _validate_array_precision(self.circuit)
        return {
            "operation_index": operation["operation_index"],
            "round_index": operation["round_index"],
            "collision_ordinal": operation["collision_ordinal"],
            "event": event,
            "update": update,
            "compression_ledger": ledger,
        }

    def residual_state_vector(self) -> np.ndarray:
        vector = self.state._carrier.state_vector(max_qubits=14)
        return np.ascontiguousarray(vector, dtype=np.complex128)

    def physical_state_vector(self, *, ownership_callback=None) -> np.ndarray:
        residual = self.residual_state_vector()
        return _lift_frame_transcript(
            residual,
            tuple(self.physical_frame_transcript),
            n_qubits=self.fixture["geometry"]["n_qubits"],
            ownership_callback=ownership_callback,
            ownership_context=(
                (
                    self.state._carrier,
                    self.state._frame,
                    self.state._events,
                ),
                (
                    "state_committed_carrier",
                    "state_frame",
                    "state_routing_history",
                ),
            ),
        )

    def logical_memory(self) -> dict[str, Any]:
        categories: dict[str, set[int]] = {
            "carrier_tensor_bytes": set(),
            "gauge_spectrum_bytes": set(),
        }
        roots: dict[int, int] = {}
        for tensor in self.circuit._psi.tensors:
            root = _root_array(np.asarray(tensor.data))
            categories["carrier_tensor_bytes"].add(id(root))
            roots[id(root)] = int(root.nbytes)
        for gauge in self.circuit.gauges.values():
            root = _root_array(gauge)
            categories["gauge_spectrum_bytes"].add(id(root))
            roots[id(root)] = int(root.nbytes)
        if categories["carrier_tensor_bytes"].intersection(
            categories["gauge_spectrum_bytes"]
        ):
            raise ValueError("GC logical-memory categories alias")
        carrier = sum(roots[key] for key in categories["carrier_tensor_bytes"])
        gauges = sum(roots[key] for key in categories["gauge_spectrum_bytes"])
        frame_bytes = len(_canonical_json_bytes(_frame_payload(self.state._frame)))
        ledger_bytes = len(
            _canonical_json_bytes(
                {
                    "algorithm_ledger": self.algorithm_ledger,
                    "physical_frame_transcript": self.physical_frame_transcript,
                    "signed_pullback_rows": self.pullback_rows,
                }
            )
        )
        total = carrier + gauges + frame_bytes + ledger_bytes
        return {
            "tensor_role": "gc_residual",
            "carrier_tensor_bytes": carrier,
            "gauge_spectrum_bytes": gauges,
            "frame_bytes": frame_bytes,
            "ledger_bytes": ledger_bytes,
            "total_owned_logical_bytes": total,
        }

    def final_carrier_hash(self) -> dict[str, Any]:
        helper = _load_sibling("gcapeps_finite_memory_carrier_hash")
        geometry = self.fixture["geometry"]
        site_tensors = {}
        for site in range(geometry["n_qubits"]):
            tensor = self.circuit._psi[site]
            site_tensors[site] = {
                "tensor": np.asarray(tensor.data),
                "physical_axis": tensor.inds.index(
                    self.circuit._psi.site_ind(site)
                ),
                "virtual_axes": {
                    neighbor: tensor.inds.index(
                        self.circuit._psi.bond(site, neighbor)
                    )
                    for edge in geometry["graph_edges"]
                    for neighbor in (
                        edge[1] if edge[0] == site else edge[0],
                    )
                    if site in edge
                },
            }
        gauges = {}
        for edge in geometry["graph_edges"]:
            ordered = tuple(edge)
            index = self.circuit._psi.bond(*ordered)
            if index in self.circuit.gauges:
                gauges[ordered] = self.circuit.gauges[index]
        input_row = next(
            row for row in self.fixture["inputs"]
            if row["input_id"] == self.input_id
        )
        return helper.canonical_carrier_hash(
            lane="gcapeps",
            site_order=tuple(range(geometry["n_qubits"])),
            graph_edges=tuple(tuple(edge) for edge in geometry["graph_edges"]),
            site_tensors=site_tensors,
            gauges=gauges,
            frame=_frame_payload(self.state._frame),
            input_preparation_transcript_sha256=input_row[
                "input_preparation_transcript_sha256"
            ],
            shared_evolution_transcript_sha256=self.fixture["carrier_path"][
                "shared_evolution_transcript_sha256"
            ],
        )


def execute_gcapeps(
    fixture: Mapping[str, Any],
    *,
    input_id: int,
    instrumented: bool,
    materialize_checkpoints: bool,
    stop_after_first_positive_operation: bool = False,
) -> dict[str, Any]:
    state = GCState.initialize(
        fixture,
        input_id,
        instrumented=instrumented,
    )
    checkpoints: dict[int, np.ndarray] = {}
    if materialize_checkpoints and 0 in fixture["checkpoints"]:
        checkpoints[0] = state.physical_state_vector()
    split_records = []
    operation_count = 0
    stop_locator = None
    for round_row in fixture["carrier_path"]["round_ledger"]:
        round_index = round_row["round_index"]
        state.advance_round(round_index)
        positive_in_operation = False
        for operation in round_row["operations"]:
            if operation["operation_index"] != operation_count:
                raise ValueError("operation indices are not globally ascending")
            record = state.apply_operation(operation)
            operation_count += 1
            if record is not None:
                for split in record["compression_ledger"].split_records:
                    split_records.append(
                        {
                            "operation_index": operation["operation_index"],
                            "round_index": round_index,
                            "collision_ordinal": operation["collision_ordinal"],
                            "split": split,
                        }
                    )
                    positive_in_operation |= split.positive_discarded_weight
            if positive_in_operation and stop_after_first_positive_operation:
                stop_locator = {
                    "operation_index": operation["operation_index"],
                    "round_index": round_index,
                }
                break
        if (
            materialize_checkpoints
            and round_index in fixture["checkpoints"]
        ):
            checkpoints[round_index] = state.physical_state_vector()
        if stop_locator is not None:
            break
    expected_pullbacks = [
        row
        for row in fixture["sdim_pullback_requests"]
        if row["input_id"] == input_id
        and (
            stop_locator is None
            or row["collision_ordinal"]
            <= max(
                item["collision_ordinal"]
                for item in state.pullback_rows
            )
        )
    ]
    observed_keys = [
        {key: row[key] for key in PULLBACK_REQUEST_KEYS}
        for row in state.pullback_rows
    ]
    if observed_keys != expected_pullbacks:
        raise ValueError("GC pullback rows do not exactly cover processed requests")
    return {
        "state": state,
        "checkpoint_vectors": checkpoints,
        "split_records": split_records,
        "pullback_rows": list(state.pullback_rows),
        "operation_count": operation_count,
        "stop_locator": stop_locator,
        "max_exact_precompression_bond": (
            state.max_exact_precompression_bond
        ),
        "max_committed_bond": state.max_committed_bond,
        "final_committed_bond": int(state.circuit._psi.max_bond() or 1),
        "final_carrier_hash": state.final_carrier_hash(),
        "logical_memory": state.logical_memory(),
    }
