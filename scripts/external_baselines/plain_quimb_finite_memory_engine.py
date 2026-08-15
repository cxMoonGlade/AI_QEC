#!/usr/bin/env python3
"""Plain Quimb PEPS mechanics for the finite-memory benchmark.

This module intentionally has no GCAPEPS, Stim, SDIM, dense-reference, or
comparator import.  It applies the neutral physical operation ledger directly
to Quimb's native ``CircuitPEPSSimpleUpdate`` path.

The frozen split policy caps every committed two-site split at
``max_bond = 32``.  Pre-run amendment 2 item 3(i) of
``docs/simulator_validation/GCAPEPS_FINITE_MEMORY_FIXTURE_V2_X8_PREREG_2026-08-01.md``
adds ONE explicit uncapped-bond override for the confirmatory harness's
inherited "untruncated run F = 1" control lane: the keyword-only
``execute_plain(..., untruncated_control=True)`` builds the circuit with
``max_bond=None``, applies every committed split uncapped, and stamps the
result payload ``"untruncated_control": True``.  The override is refused for
instrumented/evidence runs (it exists for the control lane only), and the
default ``untruncated_control=False`` path is byte-identical to the
pre-amendment engine.
"""

from __future__ import annotations

import copy
from contextlib import nullcontext
from dataclasses import dataclass
import importlib.util
import math
from pathlib import Path
import sys
from typing import Any, Callable, ContextManager, Mapping, Sequence

import numpy as np

import quimb.tensor as qtn
from quimb.tensor.circuit.gates import Gate


SPLIT_POLICY = {
    "max_bond": 32,
    "cutoff": 0.0,
    "cutoff_mode": "rel",
    "method": "svd",
    "renorm": False,
    "absorb": None,
    "smudge": 1.0e-12,
    "power": 1.0,
}
POSITIVE_TAIL_THRESHOLD = 1.0e-12


def _require_optional_ownership_callback(callback) -> None:
    if callback is not None and not callable(callback):
        raise TypeError("ownership_callback must be callable or None")


def _emit_ownership(
    callback,
    event: str,
    roots: Sequence[Any],
    *,
    checkpoint: str,
    root_roles: Sequence[str],
    evidence_only: bool,
) -> None:
    if callback is None:
        return
    if event not in {"acquire", "sample", "release"}:
        raise ValueError("unknown plain ownership event")
    frozen_roots = tuple(roots)
    frozen_roles = tuple(root_roles)
    if len(frozen_roots) != len(frozen_roles):
        raise ValueError("plain ownership roots and roles differ in length")
    result = callback(
        event,
        frozen_roots,
        {
            "schema": (
                "error_coupling_simulator.external."
                "gcapeps_finite_memory.plain_ownership_event.v1"
            ),
            "scope": "plain_engine",
            "checkpoint": checkpoint,
            "root_roles": frozen_roles,
            "evidence_only": evidence_only,
        },
    )
    if result is not None:
        raise TypeError("ownership_callback must return None")

def _load_sibling(name: str):
    path = Path(__file__).resolve(strict=True).with_name(f"{name}.py")
    module_name = f"_gcapeps_fm_{name}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load sibling helper {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _independent_circuit_copy(circuit):
    new = circuit.copy()
    new._psi = circuit._psi.copy(deep=True)
    new.gauges = {
        index: copy.deepcopy(value) for index, value in circuit.gauges.items()
    }
    new.gate_opts = copy.deepcopy(circuit.gate_opts)
    new._backend_gate_cache = {}
    new._storage = {}
    new._sampled_conditionals = {}
    new._sample_n_gates = -1
    new._equilibrate_opts = copy.deepcopy(circuit._equilibrate_opts)
    return new


def _matrix(gate_kind: str, *, axis: str | None = None, theta: float | None = None):
    if gate_kind == "H":
        value = np.asarray([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128)
        value /= math.sqrt(2.0)
    elif gate_kind == "S":
        value = np.asarray([[1.0, 0.0], [0.0, 1.0j]], dtype=np.complex128)
    elif gate_kind == "X":
        value = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    elif gate_kind == "CX":
        value = np.asarray(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0, 0.0],
            ],
            dtype=np.complex128,
        )
    elif gate_kind == "PAULI_ROTATION":
        if axis not in {"X", "Y", "Z"} or theta is None:
            raise ValueError("Pauli-pair rotation requires axis and theta")
        paulis = {
            "X": np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128),
            "Y": np.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128),
            "Z": np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128),
        }
        pp = np.kron(paulis[axis], paulis[axis])
        value = math.cos(theta / 2.0) * np.eye(4, dtype=np.complex128)
        value -= 1.0j * math.sin(theta / 2.0) * pp
    else:
        raise ValueError(f"unsupported neutral gate kind {gate_kind!r}")
    return np.ascontiguousarray(value, dtype=np.complex128)


def operation_matrix(operation: Mapping[str, Any]) -> np.ndarray:
    if operation["operation_class"] == "clifford":
        return _matrix(operation["gate_kind"])
    if operation["operation_class"] == "collision_rotation":
        if operation["gate_kind"] != "PAULI_ROTATION":
            raise ValueError("collision gate kind drifted")
        return _matrix(
            operation["gate_kind"],
            axis=operation["axis"],
            theta=float.fromhex(operation["theta_float64_hex"]),
        )
    raise ValueError("unknown operation class")


def _validate_array_precision(circuit) -> None:
    for tensor in circuit._psi.tensors:
        array = np.asarray(tensor.data)
        if array.dtype != np.dtype(np.complex128):
            raise TypeError("plain PEPS tensor left complex128")
        if not np.isfinite(array.real).all() or not np.isfinite(array.imag).all():
            raise ValueError("plain PEPS tensor contains non-finite data")
    for index, gauge in circuit.gauges.items():
        if (
            not isinstance(gauge, np.ndarray)
            or gauge.dtype != np.dtype(np.float64)
            or gauge.ndim != 1
            or not gauge.flags.c_contiguous
        ):
            raise TypeError(f"gauge {index!r} is not C-contiguous float64")
        if not np.isfinite(gauge).all() or np.any(gauge < 0.0):
            raise ValueError(f"gauge {index!r} is not finite nonnegative")


def _edge_index_map(circuit) -> dict[str, tuple[int, int]]:
    result = {}
    for left, right in circuit.edges:
        index = circuit._psi.bond(left, right)
        edge = (min(int(left), int(right)), max(int(left), int(right)))
        if index in result:
            raise ValueError("multiple graph edges share one internal index")
        result[index] = edge
    return result


def _eligible_gauges(circuit, where: tuple[int, int]):
    left, right = where
    inner = circuit._psi.bond(left, right)
    index_to_edge = _edge_index_map(circuit)
    eligible = set()
    for site in where:
        physical = circuit._psi.site_ind(site)
        tensor = circuit._psi[site]
        for index in tensor.inds:
            if index != physical and index in circuit.gauges:
                if index not in index_to_edge:
                    raise ValueError("selected tensor gauge has no declared edge")
                eligible.add(index)
    eligible.add(inner)
    ordered = tuple(sorted(eligible, key=lambda index: index_to_edge[index]))
    return inner, ordered, index_to_edge


def _preprocess_selected_zero_gauges(circuit, where: tuple[int, int]):
    inner, eligible, index_to_edge = _eligible_gauges(circuit, where)
    materialized = []
    for index in eligible:
        gauge = circuit.gauges.get(index)
        if gauge is None or not np.any(gauge == 0.0):
            continue
        circuit._psi.gauge_simple_insert(
            {index: gauge},
            remove=False,
            smudge=0.0,
            power=1.0,
        )
        del circuit.gauges[index]
        materialized.append(index_to_edge[index])
    outer_present = any(
        index != inner and index in circuit.gauges for index in eligible
    )
    _validate_array_precision(circuit)
    return {
        "eligible_edges": [list(index_to_edge[index]) for index in eligible],
        "materialized_zero_gauge_edges": [
            list(edge) for edge in materialized
        ],
        "smudge_actually_used": outer_present,
    }


def _spectrum(circuit, where: tuple[int, int]) -> np.ndarray:
    bond = circuit._psi.bond(*where)
    if bond not in circuit.gauges:
        raise ValueError("two-site split did not emit its inner-bond gauge")
    values = circuit.gauges[bond]
    _validate_array_precision(circuit)
    if any(
        right > left + 1.0e-12 * max(1.0, float(left))
        for left, right in zip(values, values[1:])
    ):
        raise ValueError("split spectrum is not nonincreasing")
    return values.copy()


def _apply_raw_two_site(
    circuit,
    matrix: np.ndarray,
    where: tuple[int, int],
    *,
    max_bond: int | None,
) -> dict[str, Any]:
    preprocessing = _preprocess_selected_zero_gauges(circuit, where)
    info: dict[str, Any] = {}
    circuit._psi.gate_simple_(
        matrix,
        where,
        circuit.gauges,
        max_bond=max_bond,
        cutoff=SPLIT_POLICY["cutoff"],
        cutoff_mode=SPLIT_POLICY["cutoff_mode"],
        method=SPLIT_POLICY["method"],
        renorm=SPLIT_POLICY["renorm"],
        absorb=SPLIT_POLICY["absorb"],
        smudge=SPLIT_POLICY["smudge"],
        power=SPLIT_POLICY["power"],
        info=info,
        contract="reduce-split",
    )
    circuit._gates.append(Gate.from_raw(matrix.copy(), qubits=where))
    _validate_array_precision(circuit)
    return {"preprocessing": preprocessing, "info_was_fresh": True}


def _split_record(
    *,
    operation: Mapping[str, Any],
    full: np.ndarray,
    kept: np.ndarray,
    preprocessing: Mapping[str, Any],
    pre_split_state_sha256: str,
    shadow_pre_split_state_sha256: str,
) -> dict[str, Any]:
    full_dimension = len(full)
    kept_dimension = len(kept)
    expected_kept = min(full_dimension, SPLIT_POLICY["max_bond"])
    if kept_dimension != expected_kept:
        raise ValueError("kept dimension disagrees with max_bond and cutoff=0")
    if not np.allclose(
        kept,
        full[:kept_dimension],
        rtol=1.0e-12,
        atol=1.0e-12,
    ):
        raise ValueError("kept spectrum is not the uncapped prefix")
    pre_weight = float(np.sum(np.square(full)))
    discarded = float(np.sum(np.square(full[kept_dimension:])))
    if not math.isfinite(pre_weight) or pre_weight <= 0.0:
        raise ValueError("uncapped split weight is nonpositive")
    cause = "max_bond" if kept_dimension < full_dimension else "none"
    if (
        not isinstance(pre_split_state_sha256, str)
        or len(pre_split_state_sha256) != 64
        or shadow_pre_split_state_sha256 != pre_split_state_sha256
    ):
        raise ValueError(
            "plain uncapped shadow did not bind the immediate pre-split state"
        )
    return {
        "operation_index": operation["operation_index"],
        "round_index": operation["round_index"],
        "collision_ordinal": operation.get("collision_ordinal"),
        "ordered_sites": list(operation["targets"]),
        "pre_split_state_sha256": pre_split_state_sha256,
        "shadow_pre_split_state_sha256": (
            shadow_pre_split_state_sha256
        ),
        "configured_max_bond": SPLIT_POLICY["max_bond"],
        "configured_cutoff": SPLIT_POLICY["cutoff"],
        "configured_cutoff_mode": SPLIT_POLICY["cutoff_mode"],
        "configured_method": SPLIT_POLICY["method"],
        "configured_renorm": SPLIT_POLICY["renorm"],
        "configured_absorb": SPLIT_POLICY["absorb"],
        "configured_power": SPLIT_POLICY["power"],
        "configured_smudge": SPLIT_POLICY["smudge"],
        "full_singular_values": full,
        "kept_singular_values": kept,
        "full_bond_dimension": full_dimension,
        "kept_bond_dimension": kept_dimension,
        "pre_split_weight": pre_weight,
        "discarded_squared_weight": discarded,
        "discarded_fraction": discarded / pre_weight,
        "cause": cause,
        "positive_discarded_weight": discarded > POSITIVE_TAIL_THRESHOLD,
        "positive_discarded_weight_threshold": POSITIVE_TAIL_THRESHOLD,
        **preprocessing,
    }


@dataclass
class PlainState:
    fixture: Mapping[str, Any]
    input_id: int
    circuit: Any
    max_committed_bond: int
    untruncated_control: bool = False

    @classmethod
    def initialize(
        cls,
        fixture: Mapping[str, Any],
        input_id: int,
        *,
        untruncated_control: bool = False,
    ):
        if not isinstance(untruncated_control, bool):
            raise TypeError("untruncated_control must be a bool")
        geometry = fixture["geometry"]
        parameters = fixture["parameters"]
        if parameters["max_bond"] != SPLIT_POLICY["max_bond"]:
            raise ValueError("fixture max_bond disagrees with plain policy")
        # Amendment 2 item 3(i): the untruncated F=1 control lane lifts the
        # execution cap only; the fixture identity still declares the frozen
        # cap and is validated against it above.
        effective_max_bond = (
            None if untruncated_control else SPLIT_POLICY["max_bond"]
        )
        edges = tuple(tuple(edge) for edge in geometry["graph_edges"])
        circuit = qtn.CircuitPEPSSimpleUpdate(
            N=geometry["n_qubits"],
            edges=edges,
            max_bond=effective_max_bond,
            cutoff=SPLIT_POLICY["cutoff"],
            renorm=SPLIT_POLICY["renorm"],
            gauge_smudge=SPLIT_POLICY["smudge"],
            equilibrate_every=None,
            gate_opts={
                "cutoff_mode": SPLIT_POLICY["cutoff_mode"],
                "method": SPLIT_POLICY["method"],
                "absorb": SPLIT_POLICY["absorb"],
                "power": SPLIT_POLICY["power"],
            },
            dtype="complex128",
        )
        input_rows = {
            row["input_id"]: row for row in fixture["inputs"]
        }
        if input_id not in input_rows:
            raise ValueError("input_id is not registered")
        input_row = input_rows[input_id]
        ones = [
            site
            for site, bit in enumerate(input_row["dense_plain_initial_bits"])
            if bit == 1
        ]
        if ones:
            if len(ones) != 1:
                raise ValueError("plain input preparation is not the frozen one-X form")
            site = ones[0]
            circuit._psi.gate_simple_(
                _matrix("X"),
                (site,),
                circuit.gauges,
                max_bond=effective_max_bond,
                cutoff=SPLIT_POLICY["cutoff"],
                cutoff_mode=SPLIT_POLICY["cutoff_mode"],
                method=SPLIT_POLICY["method"],
                renorm=SPLIT_POLICY["renorm"],
                absorb=SPLIT_POLICY["absorb"],
                smudge=SPLIT_POLICY["smudge"],
                power=SPLIT_POLICY["power"],
                info={},
                contract="reduce-split",
            )
        _validate_array_precision(circuit)
        if circuit.num_gates != 0:
            raise ValueError("direct input preparation polluted physical gate history")
        return cls(
            fixture=fixture,
            input_id=input_id,
            circuit=circuit,
            max_committed_bond=1,
            untruncated_control=untruncated_control,
        )

    def copy(self):
        return PlainState(
            fixture=self.fixture,
            input_id=self.input_id,
            circuit=_independent_circuit_copy(self.circuit),
            max_committed_bond=self.max_committed_bond,
            untruncated_control=self.untruncated_control,
        )

    def apply_operation(
        self,
        operation: Mapping[str, Any],
        *,
        instrumented: bool,
        span_factory: Callable[[str], ContextManager[Any]] | None = None,
        ownership_callback=None,
    ) -> dict[str, Any] | None:
        _require_optional_ownership_callback(ownership_callback)
        if instrumented and self.untruncated_control:
            raise ValueError(
                "the uncapped-bond override is reachable only from the "
                "confirmatory harness's control lane; instrumented/"
                "evidence runs are refused (amendment 2 item 3(i))"
            )

        def span(name: str):
            if span_factory is None:
                return nullcontext()
            return span_factory(name)

        _emit_ownership(
            ownership_callback,
            "sample",
            (self.circuit,),
            checkpoint="pre_matrix_materialization",
            root_roles=("committed_circuit",),
            evidence_only=instrumented,
        )
        matrix = operation_matrix(operation)
        _emit_ownership(
            ownership_callback,
            "sample",
            (self.circuit,),
            checkpoint="post_matrix_materialization",
            root_roles=("committed_circuit",),
            evidence_only=instrumented,
        )
        targets = tuple(operation["targets"])
        if len(targets) == 1:
            _emit_ownership(
                ownership_callback,
                "sample",
                (self.circuit,),
                checkpoint="pre_one_site_absorption",
                root_roles=("committed_circuit",),
                evidence_only=instrumented,
            )
            with span("one_site_absorption"):
                self.circuit.apply_gates(
                    (Gate.from_raw(matrix, qubits=targets),)
                )
                _validate_array_precision(self.circuit)
            _emit_ownership(
                ownership_callback,
                "sample",
                (self.circuit,),
                checkpoint="post_one_site_absorption",
                root_roles=("committed_circuit",),
                evidence_only=instrumented,
            )
            self.max_committed_bond = max(
                self.max_committed_bond,
                int(self.circuit._psi.max_bond() or 1),
            )
            return None
        if len(targets) != 2:
            raise ValueError("plain operation arity must be one or two")
        if not instrumented:
            _emit_ownership(
                ownership_callback,
                "sample",
                (self.circuit,),
                checkpoint="pre_capped_native_split",
                root_roles=("committed_circuit",),
                evidence_only=False,
            )
            with span("capped_native_split"):
                _apply_raw_two_site(
                    self.circuit,
                    matrix,
                    targets,
                    max_bond=(
                        None
                        if self.untruncated_control
                        else SPLIT_POLICY["max_bond"]
                    ),
                )
            _emit_ownership(
                ownership_callback,
                "sample",
                (self.circuit,),
                checkpoint="post_capped_native_split",
                root_roles=("committed_circuit",),
                evidence_only=False,
            )
            self.max_committed_bond = max(
                self.max_committed_bond,
                int(self.circuit._psi.max_bond() or 1),
            )
            return None
        pre_split_state_sha256 = self._carrier_hash_for_circuit(
            self.circuit
        )["sha256"]
        shadow = _independent_circuit_copy(self.circuit)
        shadow_pre_split_state_sha256 = self._carrier_hash_for_circuit(
            shadow
        )["sha256"]
        if shadow_pre_split_state_sha256 != pre_split_state_sha256:
            raise ValueError(
                "plain uncapped shadow copy changed the immediate pre-state"
            )
        _emit_ownership(
            ownership_callback,
            "acquire",
            (self.circuit, shadow),
            checkpoint="uncapped_shadow_copy",
            root_roles=("instrumented_circuit", "uncapped_shadow"),
            evidence_only=True,
        )
        _emit_ownership(
            ownership_callback,
            "sample",
            (self.circuit, shadow),
            checkpoint="pre_uncapped_shadow_replay",
            root_roles=("instrumented_circuit", "uncapped_shadow"),
            evidence_only=True,
        )
        with span("uncapped_shadow_replay"):
            _apply_raw_two_site(
                shadow,
                matrix.copy(),
                targets,
                max_bond=None,
            )
            full = _spectrum(shadow, targets)
        _emit_ownership(
            ownership_callback,
            "sample",
            (self.circuit, shadow, full),
            checkpoint="post_uncapped_shadow_replay",
            root_roles=(
                "instrumented_circuit",
                "uncapped_shadow",
                "full_singular_values",
            ),
            evidence_only=True,
        )
        _emit_ownership(
            ownership_callback,
            "release",
            (self.circuit, shadow, full),
            checkpoint="pre_uncapped_shadow_release",
            root_roles=(
                "instrumented_circuit",
                "uncapped_shadow",
                "full_singular_values",
            ),
            evidence_only=True,
        )
        del shadow
        _emit_ownership(
            ownership_callback,
            "sample",
            (self.circuit, full),
            checkpoint="post_uncapped_shadow_release",
            root_roles=("instrumented_circuit", "full_singular_values"),
            evidence_only=True,
        )
        _emit_ownership(
            ownership_callback,
            "sample",
            (self.circuit, full),
            checkpoint="pre_capped_native_split",
            root_roles=("instrumented_circuit", "full_singular_values"),
            evidence_only=True,
        )
        with span("capped_native_split"):
            actual_meta = _apply_raw_two_site(
                self.circuit,
                matrix,
                targets,
                max_bond=SPLIT_POLICY["max_bond"],
            )
            kept = _spectrum(self.circuit, targets)
        _emit_ownership(
            ownership_callback,
            "sample",
            (self.circuit, full, kept),
            checkpoint="post_capped_native_split",
            root_roles=(
                "instrumented_circuit",
                "full_singular_values",
                "kept_singular_values",
            ),
            evidence_only=True,
        )
        self.max_committed_bond = max(
            self.max_committed_bond,
            int(self.circuit._psi.max_bond() or 1),
        )
        _emit_ownership(
            ownership_callback,
            "sample",
            (self.circuit, full, kept),
            checkpoint="pre_split_ledger_validation",
            root_roles=(
                "instrumented_circuit",
                "full_singular_values",
                "kept_singular_values",
            ),
            evidence_only=True,
        )
        record = _split_record(
            operation=operation,
            full=full,
            kept=kept,
            preprocessing=actual_meta["preprocessing"],
            pre_split_state_sha256=pre_split_state_sha256,
            shadow_pre_split_state_sha256=shadow_pre_split_state_sha256,
        )
        _emit_ownership(
            ownership_callback,
            "sample",
            (self.circuit, full, kept, record),
            checkpoint="post_split_ledger_validation",
            root_roles=(
                "instrumented_circuit",
                "full_singular_values",
                "kept_singular_values",
                "split_record",
            ),
            evidence_only=True,
        )
        return record

    def state_vector(self) -> np.ndarray:
        sites = tuple(range(self.fixture["geometry"]["n_qubits"]))
        psi = self.circuit.psi
        physical_inds = tuple(psi.site_ind(site) for site in sites)
        vector = np.asarray(
            psi.to_dense(
                physical_inds,
                to_qarray=False,
                to_ket=False,
                optimize="greedy",
            ),
            dtype=np.complex128,
        ).reshape(-1)
        return np.ascontiguousarray(vector, dtype=np.complex128)

    def _carrier_hash_for_circuit(self, circuit) -> dict[str, Any]:
        helper = _load_sibling("gcapeps_finite_memory_carrier_hash")
        geometry = self.fixture["geometry"]
        site_tensors = {}
        for site in range(geometry["n_qubits"]):
            tensor = circuit._psi[site]
            site_tensors[site] = {
                "tensor": np.asarray(tensor.data),
                "physical_axis": tensor.inds.index(
                    circuit._psi.site_ind(site)
                ),
                "virtual_axes": {
                    neighbor: tensor.inds.index(
                        circuit._psi.bond(site, neighbor)
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
            index = circuit._psi.bond(*ordered)
            if index in circuit.gauges:
                gauges[ordered] = circuit.gauges[index]
        input_row = next(
            row for row in self.fixture["inputs"] if row["input_id"] == self.input_id
        )
        return helper.canonical_carrier_hash(
            lane="plain",
            site_order=tuple(range(geometry["n_qubits"])),
            graph_edges=tuple(tuple(edge) for edge in geometry["graph_edges"]),
            site_tensors=site_tensors,
            gauges=gauges,
            frame=None,
            input_preparation_transcript_sha256=input_row[
                "input_preparation_transcript_sha256"
            ],
            shared_evolution_transcript_sha256=self.fixture["carrier_path"][
                "shared_evolution_transcript_sha256"
            ],
        )

    def final_carrier_hash(self) -> dict[str, Any]:
        return self._carrier_hash_for_circuit(self.circuit)


def execute_plain(
    fixture: Mapping[str, Any],
    *,
    input_id: int,
    instrumented: bool,
    materialize_checkpoints: bool,
    stop_after_first_positive_operation: bool = False,
    untruncated_control: bool = False,
) -> dict[str, Any]:
    if not isinstance(untruncated_control, bool):
        raise TypeError("untruncated_control must be a bool")
    if untruncated_control and instrumented:
        raise ValueError(
            "the uncapped-bond override is reachable only from the "
            "confirmatory harness's control lane; instrumented/evidence "
            "runs are refused (amendment 2 item 3(i))"
        )
    state = PlainState.initialize(
        fixture, input_id, untruncated_control=untruncated_control
    )
    checkpoints: dict[int, np.ndarray] = {}
    if materialize_checkpoints and 0 in fixture["checkpoints"]:
        checkpoints[0] = state.state_vector()
    split_records = []
    operation_count = 0
    stop_locator = None
    for round_row in fixture["carrier_path"]["round_ledger"]:
        positive_in_operation = False
        for operation in round_row["operations"]:
            if operation["operation_index"] != operation_count:
                raise ValueError("operation indices are not globally ascending")
            record = state.apply_operation(operation, instrumented=instrumented)
            operation_count += 1
            if record is not None:
                split_records.append(record)
                positive_in_operation |= record["positive_discarded_weight"]
            if positive_in_operation and stop_after_first_positive_operation:
                stop_locator = {
                    "operation_index": operation["operation_index"],
                    "round_index": operation["round_index"],
                }
                break
        if materialize_checkpoints and round_row["round_index"] in fixture["checkpoints"]:
            checkpoints[round_row["round_index"]] = state.state_vector()
        if stop_locator is not None:
            break
    result = {
        "state": state,
        "checkpoint_vectors": checkpoints,
        "split_records": split_records,
        "operation_count": operation_count,
        "stop_locator": stop_locator,
        "max_committed_bond": state.max_committed_bond,
        "final_committed_bond": int(state.circuit._psi.max_bond() or 1),
        "final_carrier_hash": state.final_carrier_hash(),
    }
    if untruncated_control:
        # Amendment 2 item 3(i): the control lane stamps its payload; the
        # default path stays byte-identical and carries no stamp.
        result["untruncated_control"] = True
    return result
