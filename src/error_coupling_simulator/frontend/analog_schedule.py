from __future__ import annotations

"""Axis-1 analog schedule metadata for the simulator frontend.

This module is only the compiler/schedule seam. It records which public circuit
operations occupy the same substep, the duration bracket attached to that
substep, and the record-boundary provenance needed by later Axis-1 bridge code.
It deliberately does not contain Hamiltonians, collapse operators, channels,
Kraus matrices, source timelines, or evaluator-only mechanism truth.
"""

from dataclasses import dataclass, field
import hashlib
import hmac
import json
import secrets
from collections.abc import Sequence
from typing import Any

from .circuit_ir import (
    CircuitIR,
    CircuitStep,
    DetectorDef,
    GateOp,
    MeasureOp,
    ObservableDef,
    Tick,
)
from .metadata_guard import (
    AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY,
    AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY,
    axis1_static_zz_calibrations_to_manifest,
    normalize_axis1_static_zz_calibrations,
    normalize_axis1_static_zz_couplings,
)
from .axis1_context import (
    AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY,
    normalize_axis1_local_lindblad_context,
)
from .schedule import ScheduleTemplate

SCHEDULE_SCHEMA_VERSION = "error_coupling_simulator.frontend.substep_schedule.v1"
ANALOG_SCHEDULE_REPRESENTABILITY = "analog_schedule_metadata_only"
H3_H5_DURATION_POLICY_ID = "h3_h5_v1"
COMPILER_SCHEDULE_SEAL_SCHEMA = "error_coupling_simulator.frontend.compiler_schedule_seal.v1"
_COMPILER_SCHEDULE_SEAL_KEY = secrets.token_bytes(32)

_SOURCE_PROJECTION_AUDIT_METADATA_KEY = "_source_projection_evaluator_audit"
_NOISE_PROJECTION_METADATA_KEY = "noise_projection"
_AXIS2_METADATA_KEY_PARTS = (
    "source_timeline",
    "source_binding",
    "source_payload",
    "source_process",
    "source_fanout",
)
_SOURCE_KIND_AUTHORITY = object()

_ONE_QUBIT_GATES = {
    "C_XYZ",
    "C_ZYX",
    "H",
    "H_XY",
    "H_XZ",
    "I",
    "S",
    "S_DAG",
    "SQRT_X",
    "SQRT_X_DAG",
    "SQRT_Y",
    "SQRT_Y_DAG",
    "SQRT_Z",
    "SQRT_Z_DAG",
    "X",
    "Y",
    "Z",
}
_TWO_QUBIT_GATES = {
    "CX",
    "CY",
    "CZ",
    "ISWAP",
    "ISWAP_DAG",
    "SQRT_XX",
    "SQRT_XX_DAG",
    "SQRT_YY",
    "SQRT_YY_DAG",
    "SQRT_ZZ",
    "SQRT_ZZ_DAG",
    "SWAP",
    "XCX",
    "XCY",
    "XCZ",
    "YCX",
    "YCY",
    "YCZ",
}
_RESET_GATES = {"R", "RX", "RY", "RZ"}
_STIM_NOISE_GATES = {
    "CORRELATED_ERROR",
    "DEPOLARIZE1",
    "DEPOLARIZE2",
    "E",
    "ELSE_CORRELATED_ERROR",
    "HERALDED_ERASE",
    "HERALDED_PAULI_CHANNEL_1",
    "I_ERROR",
    "II_ERROR",
    "PAULI_CHANNEL_1",
    "PAULI_CHANNEL_2",
    "X_ERROR",
    "Y_ERROR",
    "Z_ERROR",
}
_MEASUREMENT_BASES = {
    "M": "Z",
    "MR": "Z",
    "MX": "X",
    "MRX": "X",
    "MY": "Y",
    "MRY": "Y",
    "MZ": "Z",
    "MRZ": "Z",
}


@dataclass(frozen=True)
class DurationBracket:
    """Bracketed substep duration metadata.

    A ``None`` nominal means the schedule records a physical bracket, but this
    first slice treats the substep as structural and does not authorize a
    joint-L call.
    """

    kind: str
    low_ns: float
    high_ns: float
    nominal_ns: float | None
    source: str = H3_H5_DURATION_POLICY_ID
    epistemic_class: str = "c"

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", str(self.kind))
        object.__setattr__(self, "low_ns", float(self.low_ns))
        object.__setattr__(self, "high_ns", float(self.high_ns))
        nominal = None if self.nominal_ns is None else float(self.nominal_ns)
        object.__setattr__(self, "nominal_ns", nominal)
        object.__setattr__(self, "source", str(self.source))
        object.__setattr__(self, "epistemic_class", str(self.epistemic_class))
        if self.low_ns < 0.0 or self.high_ns < self.low_ns:
            raise ValueError(
                f"invalid duration bracket for {self.kind!r}: "
                f"[{self.low_ns}, {self.high_ns}]"
            )
        if nominal is not None and not (self.low_ns <= nominal <= self.high_ns):
            raise ValueError(
                f"duration nominal {nominal} outside bracket "
                f"[{self.low_ns}, {self.high_ns}] for {self.kind!r}"
            )
        if self.epistemic_class not in {"a", "b", "c"}:
            raise ValueError(f"invalid epistemic_class {self.epistemic_class!r}")

    def to_manifest(self) -> dict:
        return {
            "kind": self.kind,
            "low_ns": self.low_ns,
            "high_ns": self.high_ns,
            "nominal_ns": self.nominal_ns,
            "source": self.source,
            "epistemic_class": self.epistemic_class,
        }


@dataclass(frozen=True)
class DurationPolicy:
    """Named table mapping analog substep kinds to duration brackets."""

    table_id: str
    brackets: tuple[DurationBracket, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "table_id", str(self.table_id))
        object.__setattr__(self, "brackets", tuple(self.brackets))
        if not self.brackets:
            raise ValueError("DurationPolicy requires at least one bracket")
        names = [bracket.kind for bracket in self.brackets]
        if len(set(names)) != len(names):
            raise ValueError(f"duplicate duration bracket kind(s): {names}")

    def bracket_for(self, kind: str) -> DurationBracket:
        for bracket in self.brackets:
            if bracket.kind == kind:
                return bracket
        raise ValueError(f"duration policy {self.table_id!r} has no bracket for {kind!r}")

    def to_manifest(self) -> dict:
        return {
            "table_id": self.table_id,
            "brackets": [bracket.to_manifest() for bracket in self.brackets],
        }


@dataclass(frozen=True)
class SubstepOperation:
    """Public operation payload preserved inside one analog substep."""

    name: str
    targets: tuple[int, ...]
    source_step_index: int
    args: tuple[float, ...] = ()
    basis: str | None = None
    measurement_keys: tuple[str, ...] = ()
    reset_after_measurement: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", str(self.name).upper())
        object.__setattr__(self, "targets", tuple(int(t) for t in self.targets))
        object.__setattr__(self, "source_step_index", int(self.source_step_index))
        object.__setattr__(self, "args", tuple(float(a) for a in self.args))
        basis = None if self.basis is None else str(self.basis).upper()
        object.__setattr__(self, "basis", basis)
        object.__setattr__(
            self,
            "measurement_keys",
            tuple(str(key) for key in self.measurement_keys),
        )
        object.__setattr__(
            self,
            "reset_after_measurement",
            bool(self.reset_after_measurement),
        )
        if any(t < 0 for t in self.targets):
            raise ValueError(f"operation {self.name!r} has negative target(s): {self.targets}")

    def to_manifest(self) -> dict:
        out = {
            "name": self.name,
            "targets": list(self.targets),
            "source_step_index": self.source_step_index,
            "args": list(self.args),
        }
        if self.basis is not None:
            out["basis"] = self.basis
        if self.measurement_keys:
            out["measurement_keys"] = list(self.measurement_keys)
        if self.reset_after_measurement:
            out["reset_after_measurement"] = True
        return out


@dataclass(frozen=True)
class AnalogSubstepIR:
    """One ordered public schedule substep for later Axis-1 lowering."""

    substep_id: str
    round_index: int | None
    tick_index: int
    order_index: int
    kind: str
    operations: tuple[SubstepOperation, ...]
    active_qubits: tuple[int, ...]
    idle_qubits: tuple[int, ...]
    participants: tuple[tuple[int, ...], ...]
    dt_ns_nominal: float | None
    dt_ns_bracket: tuple[float, float]
    dt_source: str
    mechanism_slots: tuple[str, ...]
    measurement_keys: tuple[str, ...]
    window_support: tuple[int, ...]
    generated_by_compiler: bool = False
    epistemic_class: str = "c"

    def __post_init__(self) -> None:
        object.__setattr__(self, "substep_id", str(self.substep_id))
        round_index = None if self.round_index is None else int(self.round_index)
        object.__setattr__(self, "round_index", round_index)
        object.__setattr__(self, "tick_index", int(self.tick_index))
        object.__setattr__(self, "order_index", int(self.order_index))
        object.__setattr__(self, "kind", str(self.kind))
        object.__setattr__(self, "operations", tuple(self.operations))
        object.__setattr__(self, "active_qubits", _sorted_unique(self.active_qubits))
        object.__setattr__(self, "idle_qubits", _sorted_unique(self.idle_qubits))
        object.__setattr__(
            self,
            "participants",
            tuple(tuple(int(q) for q in group) for group in self.participants),
        )
        nominal = None if self.dt_ns_nominal is None else float(self.dt_ns_nominal)
        object.__setattr__(self, "dt_ns_nominal", nominal)
        lo, hi = self.dt_ns_bracket
        object.__setattr__(self, "dt_ns_bracket", (float(lo), float(hi)))
        object.__setattr__(self, "dt_source", str(self.dt_source))
        object.__setattr__(
            self,
            "mechanism_slots",
            tuple(str(slot) for slot in self.mechanism_slots),
        )
        object.__setattr__(
            self,
            "measurement_keys",
            tuple(str(key) for key in self.measurement_keys),
        )
        object.__setattr__(self, "window_support", _sorted_unique(self.window_support))
        object.__setattr__(self, "generated_by_compiler", bool(self.generated_by_compiler))
        object.__setattr__(self, "epistemic_class", str(self.epistemic_class))
        if self.tick_index < 0 or self.order_index < 0:
            raise ValueError("tick_index/order_index must be non-negative")
        if nominal is not None and nominal <= 0.0:
            raise ValueError("dt_ns_nominal must be positive when present")
        if self.dt_ns_bracket[0] < 0.0 or self.dt_ns_bracket[1] < self.dt_ns_bracket[0]:
            raise ValueError(f"invalid dt_ns_bracket {self.dt_ns_bracket}")
        if self.epistemic_class not in {"a", "b", "c"}:
            raise ValueError(f"invalid epistemic_class {self.epistemic_class!r}")

    def to_manifest(self) -> dict:
        return {
            "substep_id": self.substep_id,
            "round_index": self.round_index,
            "tick_index": self.tick_index,
            "order_index": self.order_index,
            "kind": self.kind,
            "operations": [op.to_manifest() for op in self.operations],
            "active_qubits": list(self.active_qubits),
            "idle_qubits": list(self.idle_qubits),
            "participants": [list(group) for group in self.participants],
            "dt_ns_nominal": self.dt_ns_nominal,
            "dt_ns_bracket": list(self.dt_ns_bracket),
            "dt_source": self.dt_source,
            "mechanism_slots": list(self.mechanism_slots),
            "measurement_keys": list(self.measurement_keys),
            "window_support": list(self.window_support),
            "generated_by_compiler": self.generated_by_compiler,
            "epistemic_class": self.epistemic_class,
        }


@dataclass(frozen=True)
class SubstepSchedule:
    """Compiler-produced schedule metadata consumed by later Axis-1 bridges."""

    source_kind: str
    source_hash: str
    schedule_template: str | None
    num_qubits: int
    substeps: tuple[AnalogSubstepIR, ...]
    duration_policy: DurationPolicy
    schema_version: str = SCHEDULE_SCHEMA_VERSION
    qubit_roles: dict[int, str] = field(default_factory=dict)
    qubit_coords: dict[int, tuple[float, ...]] = field(default_factory=dict)
    static_zz_couplings: tuple[tuple[int, int], ...] = ()
    static_zz_calibrations: dict[tuple[int, int], dict[str, Any]] = field(default_factory=dict)
    axis1_local_lindblad_context: dict = field(default_factory=dict)
    record_layout_ref: dict = field(default_factory=dict)
    representability: str = ANALOG_SCHEDULE_REPRESENTABILITY
    visibility: str = "public_schedule_metadata_no_mechanism_truth"
    _compiler_signature: str | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_kind", str(self.source_kind))
        object.__setattr__(self, "source_hash", str(self.source_hash))
        template = None if self.schedule_template is None else str(self.schedule_template)
        object.__setattr__(self, "schedule_template", template)
        object.__setattr__(self, "num_qubits", int(self.num_qubits))
        object.__setattr__(self, "substeps", tuple(self.substeps))
        object.__setattr__(self, "schema_version", str(self.schema_version))
        if self.schema_version != SCHEDULE_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported substep-schedule schema {self.schema_version!r}; "
                f"expected {SCHEDULE_SCHEMA_VERSION!r}"
            )
        object.__setattr__(
            self,
            "qubit_roles",
            {int(k): str(v) for k, v in self.qubit_roles.items()},
        )
        object.__setattr__(
            self,
            "qubit_coords",
            {int(k): tuple(float(c) for c in v) for k, v in self.qubit_coords.items()},
        )
        static_edges = normalize_axis1_static_zz_couplings(
            self.static_zz_couplings,
            num_qubits=self.num_qubits,
            label="SubstepSchedule.static_zz_couplings",
        )
        object.__setattr__(self, "static_zz_couplings", static_edges)
        static_calibrations = normalize_axis1_static_zz_calibrations(
            self.static_zz_calibrations,
            num_qubits=self.num_qubits,
            declared_edges=static_edges,
            label="SubstepSchedule.static_zz_calibrations",
        )
        object.__setattr__(self, "static_zz_calibrations", static_calibrations)
        context = normalize_axis1_local_lindblad_context(
            self.axis1_local_lindblad_context
        )
        object.__setattr__(
            self,
            "axis1_local_lindblad_context",
            {} if context.is_trivial else context.to_manifest(),
        )
        object.__setattr__(self, "record_layout_ref", dict(self.record_layout_ref))
        object.__setattr__(self, "representability", str(self.representability))
        object.__setattr__(self, "visibility", str(self.visibility))
        if self.num_qubits <= 0:
            raise ValueError("num_qubits must be positive")
        if not self.source_hash:
            raise ValueError("source_hash must be non-empty")
        if self.representability != ANALOG_SCHEDULE_REPRESENTABILITY:
            raise ValueError(
                "SubstepSchedule representability must be "
                f"{ANALOG_SCHEDULE_REPRESENTABILITY!r}"
            )
        for i, substep in enumerate(self.substeps):
            if substep.order_index != i:
                raise ValueError(
                    f"substep {substep.substep_id!r} has order_index "
                    f"{substep.order_index}, expected {i}"
                )
            for q in substep.window_support:
                if q < 0 or q >= self.num_qubits:
                    raise ValueError(
                        f"substep {substep.substep_id!r} window qubit {q} outside "
                        f"[0, {self.num_qubits})"
                    )

    def to_manifest(self) -> dict:
        out = {
            "schema_version": self.schema_version,
            "source_kind": self.source_kind,
            "source_hash": self.source_hash,
            "schedule_template": self.schedule_template,
            "num_qubits": self.num_qubits,
            "qubit_roles": {str(k): v for k, v in sorted(self.qubit_roles.items())},
            "qubit_coords": {
                str(k): list(v) for k, v in sorted(self.qubit_coords.items())
            },
            "static_zz_couplings": [list(edge) for edge in self.static_zz_couplings],
            "static_zz_calibrations": axis1_static_zz_calibrations_to_manifest(
                self.static_zz_calibrations
            ),
            "record_layout_ref": _jsonable(self.record_layout_ref),
            "duration_policy": self.duration_policy.to_manifest(),
            "representability": self.representability,
            "visibility": self.visibility,
            "compiler_provenance": {
                "seal_schema": COMPILER_SCHEDULE_SEAL_SCHEMA,
                "seal_present": self._compiler_signature is not None,
                "seal_public": False,
                "generated_substeps": all(
                    substep.generated_by_compiler for substep in self.substeps
                ),
            },
            "substeps": [substep.to_manifest() for substep in self.substeps],
        }
        if self.axis1_local_lindblad_context:
            out["axis1_local_lindblad_context"] = dict(
                self.axis1_local_lindblad_context
            )
        return out


def h3_h5_duration_policy() -> DurationPolicy:
    """Return the preregistered H3/H5 heuristic duration-bracket table."""

    return DurationPolicy(
        table_id=H3_H5_DURATION_POLICY_ID,
        brackets=(
            DurationBracket("one_qubit_gate", 20.0, 30.0, 25.0),
            DurationBracket("two_qubit_gate", 25.0, 45.0, 30.0),
            DurationBracket("idle", 0.0, 300.0, None),
            DurationBracket("measurement", 100.0, 1000.0, None),
            DurationBracket("reset", 100.0, 500.0, None),
            DurationBracket("barrier", 0.0, 0.0, None),
        ),
    )


def compile_code_spec_to_substep_schedule(
    spec,
    *,
    schedule_template: str | ScheduleTemplate = "repeated_memory_v1",
    duration_policy: DurationPolicy | None = None,
) -> SubstepSchedule:
    """Compile a `CodeSpec` into `CircuitIR`, then extract Axis-1 schedule metadata."""

    from .compiler import compile_code_spec

    circuit = compile_code_spec(spec, schedule_template=schedule_template)
    return circuit_ir_to_substep_schedule(
        circuit,
        source_kind="code_spec_compiler",
        duration_policy=duration_policy,
        _source_kind_authority=_SOURCE_KIND_AUTHORITY,
    )


def circuit_ir_to_substep_schedule(
    circuit: CircuitIR,
    *,
    source_kind: str = "circuit_ir",
    source_hash: str | None = None,
    duration_policy: DurationPolicy | None = None,
    _source_kind_authority: object | None = None,
) -> SubstepSchedule:
    """Extract compiler-generated analog substep metadata from `CircuitIR`.

    This function rejects pre-noised or source-projected circuits. Those
    frontends are useful record carriers, but they cannot satisfy the Axis-1
    schedule representability contract.
    """

    source_kind = str(source_kind)
    if source_kind != "circuit_ir" and _source_kind_authority is not _SOURCE_KIND_AUTHORITY:
        raise ValueError(
            f"source_kind={source_kind!r} is reserved for compiler/importer wrappers; "
            "public CircuitIR extraction must use source_kind='circuit_ir'"
        )
    _reject_projected_or_noisy_circuit(circuit)
    policy = duration_policy or h3_h5_duration_policy()
    source_manifest = _circuit_ir_manifest(circuit)
    schedule_name = _schedule_template_name(circuit)
    qubit_roles, qubit_coords = _qubit_metadata(circuit)
    static_zz_couplings = _static_zz_couplings_metadata(circuit)
    static_zz_calibrations = _static_zz_calibrations_metadata(
        circuit,
        declared_edges=static_zz_couplings,
    )
    axis1_context = _axis1_local_lindblad_context_metadata(circuit)
    record_layout_ref = _record_layout_ref(circuit)
    substeps = _extract_substeps(circuit, policy)
    return _seal_compiler_schedule(
        SubstepSchedule(
            source_kind=source_kind,
            source_hash=source_hash or _stable_hash(source_manifest),
            schedule_template=schedule_name,
            num_qubits=circuit.num_qubits,
            qubit_roles=qubit_roles,
            qubit_coords=qubit_coords,
            static_zz_couplings=static_zz_couplings,
            static_zz_calibrations=static_zz_calibrations,
            axis1_local_lindblad_context=axis1_context,
            record_layout_ref=record_layout_ref,
            duration_policy=policy,
            substeps=substeps,
        )
    )


def stim_circuit_to_substep_schedule(
    stim_circuit,
    *,
    source_hash: str | None = None,
    duration_policy: DurationPolicy | None = None,
    static_zz_couplings: Any = (),
    static_zz_calibrations: Any = None,
    axis1_local_lindblad_context: Any = None,
) -> SubstepSchedule:
    """Extract Axis-1 schedule metadata from a read-only Stim circuit.

    This importer preserves `TICK`, detector, observable, and qubit-coordinate
    metadata, but rejects embedded Stim noise instructions. A Stim Pauli/noise
    circuit is a record/sampling carrier, not Axis-1 joint-L schedule truth.
    Public static-ZZ device edges may be supplied as an explicit sidecar; they
    are not inferred from Stim `CZ` history.
    """

    circuit = _stim_circuit_to_circuit_ir(stim_circuit)
    static_edges = normalize_axis1_static_zz_couplings(
        static_zz_couplings,
        num_qubits=circuit.num_qubits,
        label="stim_circuit_to_substep_schedule.static_zz_couplings",
    )
    static_calibrations = normalize_axis1_static_zz_calibrations(
        static_zz_calibrations,
        num_qubits=circuit.num_qubits,
        declared_edges=static_edges,
        label="stim_circuit_to_substep_schedule.static_zz_calibrations",
    )
    axis1_context = normalize_axis1_local_lindblad_context(
        axis1_local_lindblad_context
    )
    if static_edges or static_calibrations:
        metadata = dict(circuit.metadata)
        metadata[AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY] = [
            list(edge) for edge in static_edges
        ]
        if static_calibrations:
            metadata[AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY] = (
                axis1_static_zz_calibrations_to_manifest(static_calibrations)
            )
        if not axis1_context.is_trivial:
            metadata[AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY] = (
                axis1_context.to_manifest()
            )
        circuit = CircuitIR(
            num_qubits=circuit.num_qubits,
            steps=circuit.steps,
            metadata=metadata,
        )
    elif not axis1_context.is_trivial:
        metadata = dict(circuit.metadata)
        metadata[AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY] = (
            axis1_context.to_manifest()
        )
        circuit = CircuitIR(
            num_qubits=circuit.num_qubits,
            steps=circuit.steps,
            metadata=metadata,
        )
    stim_hash_payload = {
        "schema": "error_coupling_simulator.frontend.stim_circuit_schedule_hash.v1",
        "stim_circuit": str(stim_circuit),
        "static_zz_couplings": [list(edge) for edge in static_edges],
        "static_zz_calibrations": axis1_static_zz_calibrations_to_manifest(
            static_calibrations
        ),
    }
    if not axis1_context.is_trivial:
        stim_hash_payload["axis1_local_lindblad_context"] = (
            axis1_context.to_manifest()
        )
    stim_hash = source_hash or _stable_hash(stim_hash_payload)
    return circuit_ir_to_substep_schedule(
        circuit,
        source_kind="stim_circuit",
        source_hash=stim_hash,
        duration_policy=duration_policy,
        _source_kind_authority=_SOURCE_KIND_AUTHORITY,
    )


def has_valid_compiler_schedule_seal(schedule: SubstepSchedule) -> bool:
    """Return whether `schedule` was sealed by this process's compiler builder."""

    signature = getattr(schedule, "_compiler_signature", None)
    if not isinstance(signature, str) or not signature:
        return False
    expected = _compiler_schedule_signature(schedule)
    return hmac.compare_digest(signature, expected)


def require_compiler_schedule_seal(schedule: SubstepSchedule) -> None:
    """Fail unless `schedule` carries the builder-owned compiler seal."""

    if not has_valid_compiler_schedule_seal(schedule):
        raise ValueError(
            "Axis-1 frontend gates require a compiler-owned schedule seal; "
            "build schedules via circuit_ir_to_substep_schedule(...) or "
            "compile_code_spec_to_substep_schedule(...)"
        )


def _seal_compiler_schedule(schedule: SubstepSchedule) -> SubstepSchedule:
    object.__setattr__(
        schedule,
        "_compiler_signature",
        _compiler_schedule_signature(schedule),
    )
    return schedule


def _compiler_schedule_signature(schedule: SubstepSchedule) -> str:
    payload = json.dumps(
        _schedule_signature_manifest(schedule),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hmac.new(
        _COMPILER_SCHEDULE_SEAL_KEY,
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _schedule_signature_manifest(schedule: SubstepSchedule) -> dict:
    manifest = dict(schedule.to_manifest())
    manifest.pop("compiler_provenance", None)
    return manifest


def _extract_substeps(
    circuit: CircuitIR,
    policy: DurationPolicy,
) -> tuple[AnalogSubstepIR, ...]:
    substeps: list[AnalogSubstepIR] = []
    pending: list[SubstepOperation] = []
    pending_kind: str | None = None
    pending_support: set[int] = set()
    pending_participants: list[tuple[int, ...]] = []
    tick_index = 0

    def flush() -> None:
        nonlocal pending, pending_kind, pending_support, pending_participants
        if not pending:
            return
        assert pending_kind is not None
        substeps.append(
            _make_substep(
                order_index=len(substeps),
                tick_index=tick_index,
                kind=pending_kind,
                operations=tuple(pending),
                participants=tuple(pending_participants),
                num_qubits=circuit.num_qubits,
                policy=policy,
            )
        )
        pending = []
        pending_kind = None
        pending_support = set()
        pending_participants = []

    for source_step_index, step in enumerate(circuit.steps):
        if isinstance(step, Tick):
            flush()
            substeps.append(
                _make_barrier_substep(
                    order_index=len(substeps),
                    tick_index=tick_index,
                    policy=policy,
                )
            )
            tick_index += 1
            continue
        if isinstance(step, (DetectorDef, ObservableDef)):
            flush()
            continue

        op, kind, support, participants = _operation_from_step(step, source_step_index)
        if (
            pending
            and (pending_kind != kind or pending_support.intersection(support))
        ):
            flush()
        pending_kind = kind
        pending.append(op)
        pending_support.update(support)
        pending_participants.extend(participants)

    flush()
    return tuple(substeps)


def _stim_circuit_to_circuit_ir(stim_circuit) -> CircuitIR:
    steps: list[CircuitStep] = []
    measurement_keys: list[str] = []
    qubit_coords: dict[int, tuple[float, ...]] = {}
    detector_count = 0

    try:
        num_qubits = int(stim_circuit.num_qubits)
    except AttributeError as exc:
        raise TypeError("stim_circuit_to_substep_schedule expects a stim.Circuit") from exc

    for inst in stim_circuit:
        if not hasattr(inst, "name"):
            raise ValueError("Stim REPEAT blocks are not supported by the Axis-1 schedule importer")
        name = str(inst.name).upper()
        args = tuple(float(a) for a in inst.gate_args_copy())
        targets = tuple(inst.targets_copy())
        if name == "QUBIT_COORDS":
            if len(targets) != 1:
                raise ValueError("QUBIT_COORDS must target exactly one qubit")
            q = _stim_qubit_target(targets[0], instruction=name)
            qubit_coords[q] = args
            continue
        if name in {"SHIFT_COORDS", "TICK"}:
            if name == "TICK":
                steps.append(Tick())
                continue
            raise ValueError("Stim SHIFT_COORDS is not supported by the Axis-1 schedule importer")
        if name in _STIM_NOISE_GATES:
            raise ValueError(
                f"source-embedded Stim noise instruction {name!r} is not analog joint-L schedule metadata"
            )
        if name == "DETECTOR":
            keys = _stim_record_keys(targets, measurement_keys, instruction=name)
            steps.append(DetectorDef(f"d{detector_count}", keys, args))
            detector_count += 1
            continue
        if name == "OBSERVABLE_INCLUDE":
            keys = _stim_record_keys(targets, measurement_keys, instruction=name)
            index = int(args[0]) if args else 0
            steps.append(ObservableDef(f"logical{index}", keys, index))
            continue
        qubit_targets = tuple(_stim_qubit_target(target, instruction=name) for target in targets)
        if name in _MEASUREMENT_BASES:
            keys = tuple(f"m{len(measurement_keys) + i}" for i in range(len(qubit_targets)))
            measurement_keys.extend(keys)
            steps.append(MeasureOp(name, qubit_targets, keys))
            continue
        if name in _ONE_QUBIT_GATES or name in _TWO_QUBIT_GATES or name in _RESET_GATES:
            steps.append(GateOp(name, qubit_targets, args))
            continue
        raise ValueError(
            f"unsupported Stim instruction {name!r} for Axis-1 SubstepSchedule extraction"
        )

    metadata = {
        "imported_from": "stim_circuit",
        "qubit_coords": {str(q): list(coords) for q, coords in sorted(qubit_coords.items())},
    }
    return CircuitIR(num_qubits=num_qubits, steps=tuple(steps), metadata=metadata)


def _stim_qubit_target(target, *, instruction: str) -> int:
    if not bool(getattr(target, "is_qubit_target", False)):
        raise ValueError(f"{instruction} target {target!r} is not a qubit target")
    return int(target.qubit_value)


def _stim_record_keys(
    targets: tuple[Any, ...],
    measurement_keys: list[str],
    *,
    instruction: str,
) -> tuple[str, ...]:
    keys: list[str] = []
    measurement_count = len(measurement_keys)
    for target in targets:
        if not bool(getattr(target, "is_measurement_record_target", False)):
            raise ValueError(f"{instruction} target {target!r} is not a measurement record target")
        index = measurement_count + int(target.value)
        if index < 0 or index >= measurement_count:
            raise ValueError(
                f"{instruction} record target {target!r} points outside previous measurements"
            )
        keys.append(measurement_keys[index])
    return tuple(keys)


def _make_substep(
    *,
    order_index: int,
    tick_index: int,
    kind: str,
    operations: tuple[SubstepOperation, ...],
    participants: tuple[tuple[int, ...], ...],
    num_qubits: int,
    policy: DurationPolicy,
) -> AnalogSubstepIR:
    bracket = policy.bracket_for(kind)
    explicit_duration = _explicit_duration_ns(kind, operations)
    active = _active_qubits(kind, operations)
    explicit_idle = _explicit_idle_qubits(kind, operations)
    nominal = bracket.nominal_ns
    dt_bracket = (bracket.low_ns, bracket.high_ns)
    dt_source = bracket.source
    epistemic_class = bracket.epistemic_class
    if explicit_duration is not None:
        nominal = explicit_duration
        dt_bracket = (explicit_duration, explicit_duration)
        dt_source = f"explicit_circuit_{kind}_duration"
        epistemic_class = "c"
    if kind == "idle":
        idle = explicit_idle
    elif nominal is not None:
        idle = tuple(q for q in range(num_qubits) if q not in set(active))
    else:
        idle = explicit_idle
    measurement_keys = tuple(
        key for op in operations for key in op.measurement_keys
    )
    slots = _mechanism_slots_for(kind, operations)
    window_support = _sorted_unique(tuple(active) + tuple(idle))
    return AnalogSubstepIR(
        substep_id=f"s{order_index:04d}",
        round_index=None,
        tick_index=tick_index,
        order_index=order_index,
        kind=kind,
        operations=operations,
        active_qubits=active,
        idle_qubits=idle,
        participants=participants,
        dt_ns_nominal=nominal,
        dt_ns_bracket=dt_bracket,
        dt_source=dt_source,
        mechanism_slots=slots,
        measurement_keys=measurement_keys,
        window_support=window_support,
        generated_by_compiler=True,
        epistemic_class=epistemic_class,
    )


def _make_barrier_substep(
    *,
    order_index: int,
    tick_index: int,
    policy: DurationPolicy,
) -> AnalogSubstepIR:
    bracket = policy.bracket_for("barrier")
    return AnalogSubstepIR(
        substep_id=f"s{order_index:04d}",
        round_index=None,
        tick_index=tick_index,
        order_index=order_index,
        kind="barrier",
        operations=(),
        active_qubits=(),
        idle_qubits=(),
        participants=(),
        dt_ns_nominal=bracket.nominal_ns,
        dt_ns_bracket=(bracket.low_ns, bracket.high_ns),
        dt_source=bracket.source,
        mechanism_slots=(),
        measurement_keys=(),
        window_support=(),
        generated_by_compiler=True,
        epistemic_class=bracket.epistemic_class,
    )


def _operation_from_step(
    step: CircuitStep,
    source_step_index: int,
) -> tuple[SubstepOperation, str, set[int], tuple[tuple[int, ...], ...]]:
    if isinstance(step, GateOp):
        kind = _gate_kind(step)
        participants = _gate_participants(step, kind)
        op = SubstepOperation(
            name=step.name,
            targets=step.targets,
            source_step_index=source_step_index,
            args=step.args,
        )
        support = set(step.targets)
        return op, kind, support, participants
    if isinstance(step, MeasureOp):
        basis = _MEASUREMENT_BASES.get(step.name)
        if basis is None:
            raise ValueError(f"unsupported measurement instruction {step.name!r}")
        op = SubstepOperation(
            name=step.name,
            targets=step.targets,
            source_step_index=source_step_index,
            args=step.args,
            basis=basis,
            measurement_keys=step.keys,
            reset_after_measurement=step.name.startswith("MR"),
        )
        participants = tuple((target,) for target in step.targets)
        return op, "measurement", set(step.targets), participants
    raise TypeError(f"record-only step {type(step)!r} should not reach operation extraction")


def _explicit_duration_ns(
    kind: str,
    operations: tuple[SubstepOperation, ...],
) -> float | None:
    if kind not in {"idle", "measurement"}:
        return None
    durations = []
    for op in operations:
        if not op.args:
            continue
        if len(op.args) != 1:
            raise ValueError(
                f"{kind} operation expects at most one duration_ns argument, got {op.args}"
            )
        duration = float(op.args[0])
        if duration <= 0.0:
            raise ValueError(f"{kind} duration_ns must be positive, got {duration!r}")
        durations.append(duration)
    if not durations:
        return None
    first = durations[0]
    if any(duration != first for duration in durations):
        raise ValueError(f"grouped {kind} operations have inconsistent durations {durations}")
    return first


def _gate_kind(step: GateOp) -> str:
    if step.name in _RESET_GATES:
        return "reset"
    if step.name == "I":
        return "idle"
    if step.name in _ONE_QUBIT_GATES:
        return "one_qubit_gate"
    if step.name in _TWO_QUBIT_GATES:
        if len(step.targets) % 2:
            raise ValueError(f"{step.name} requires an even-length target pair list")
        return "two_qubit_gate"
    raise ValueError(
        f"unsupported operation {step.name!r} for Axis-1 SubstepSchedule extraction"
    )


def _gate_participants(
    step: GateOp,
    kind: str,
) -> tuple[tuple[int, ...], ...]:
    if kind in {"one_qubit_gate", "reset", "idle"}:
        return tuple((target,) for target in step.targets)
    if kind == "two_qubit_gate":
        pairs = tuple(
            tuple(step.targets[i : i + 2])
            for i in range(0, len(step.targets), 2)
        )
        seen: set[int] = set()
        for pair in pairs:
            if len(pair) != 2 or pair[0] == pair[1]:
                raise ValueError(f"{step.name} has invalid pair participant {pair}")
            overlap = seen.intersection(pair)
            if overlap:
                raise ValueError(
                    f"{step.name} has overlapping pair participant(s): {pairs}"
                )
            seen.update(pair)
        return pairs
    return ()


def _active_qubits(
    kind: str,
    operations: tuple[SubstepOperation, ...],
) -> tuple[int, ...]:
    if kind == "idle":
        return ()
    return _sorted_unique(tuple(q for op in operations for q in op.targets))


def _explicit_idle_qubits(
    kind: str,
    operations: tuple[SubstepOperation, ...],
) -> tuple[int, ...]:
    if kind != "idle":
        return ()
    return _sorted_unique(tuple(q for op in operations for q in op.targets))


def _mechanism_slots_for(
    kind: str,
    operations: tuple[SubstepOperation, ...],
) -> tuple[str, ...]:
    if kind == "one_qubit_gate":
        return ("drive", "idle", "spectator")
    if kind == "two_qubit_gate":
        return ("two_qubit_drive", "zz_spectator", "idle")
    if kind == "idle":
        return ("idle",)
    if kind == "measurement":
        if any(op.reset_after_measurement for op in operations):
            return ("readout_boundary", "reset_boundary")
        return ("readout_boundary",)
    if kind == "reset":
        return ("reset_boundary",)
    return ()


def _reject_projected_or_noisy_circuit(circuit: CircuitIR) -> None:
    metadata = circuit.metadata
    if _NOISE_PROJECTION_METADATA_KEY in metadata:
        projection = metadata[_NOISE_PROJECTION_METADATA_KEY]
        projection_type = projection.get("type") if isinstance(projection, dict) else projection
        raise ValueError(
            "Axis-1 SubstepSchedule requires an unprojected frontend circuit; "
            f"noise_projection={projection_type!r} is a Stim/Pauli/source projection, "
            "not analog joint-L schedule metadata"
        )
    if _SOURCE_PROJECTION_AUDIT_METADATA_KEY in metadata:
        raise ValueError(
            "Source projection evaluator audit cannot be used as Axis-1 schedule metadata"
        )
    source_path = _find_axis2_source_metadata_path(metadata)
    if source_path is not None:
        raise ValueError(
            "Axis-1 SubstepSchedule metadata cannot contain Axis-2 source truth; "
            f"found {source_path}"
        )


def _find_axis2_source_metadata_path(value: Any, *, path: str = "CircuitIR.metadata") -> str | None:
    if isinstance(value, dict):
        for raw_key, item in value.items():
            key = str(raw_key)
            normalized = key.lower().replace("-", "_").replace(" ", "_")
            if any(part in normalized for part in _AXIS2_METADATA_KEY_PARTS):
                return f"{path}.{key}"
            found = _find_axis2_source_metadata_path(item, path=f"{path}.{key}")
            if found is not None:
                return found
    elif isinstance(value, (list, tuple)):
        for i, item in enumerate(value):
            found = _find_axis2_source_metadata_path(item, path=f"{path}[{i}]")
            if found is not None:
                return found
    return None


def _schedule_template_name(circuit: CircuitIR) -> str | None:
    schedule = circuit.metadata.get("schedule")
    if isinstance(schedule, dict):
        name = schedule.get("name")
        return None if name is None else str(name)
    return None


def _qubit_metadata(circuit: CircuitIR) -> tuple[dict[int, str], dict[int, tuple[float, ...]]]:
    roles: dict[int, str] = {}
    coords: dict[int, tuple[float, ...]] = {}
    code_spec = circuit.metadata.get("code_spec")
    if isinstance(code_spec, dict):
        for key, role in (("data_qubits", "data"), ("ancilla_qubits", "ancilla")):
            entries = code_spec.get(key, ())
            if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
                continue
            for entry in entries:
                if not isinstance(entry, dict) or "index" not in entry:
                    continue
                q = int(entry["index"])
                roles[q] = str(entry.get("role", role))
                raw_coords = entry.get("coords", ())
                coords[q] = tuple(float(c) for c in raw_coords)
    raw_coords = circuit.metadata.get("qubit_coords")
    if isinstance(raw_coords, dict):
        for key, value in raw_coords.items():
            coords[int(key)] = tuple(float(c) for c in value)
    return roles, coords


def _static_zz_couplings_metadata(circuit: CircuitIR) -> tuple[tuple[int, int], ...]:
    raw = circuit.metadata.get(AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY, ())
    return normalize_axis1_static_zz_couplings(
        raw,
        num_qubits=circuit.num_qubits,
        label=f"CircuitIR.metadata.{AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY}",
    )


def _static_zz_calibrations_metadata(
    circuit: CircuitIR,
    *,
    declared_edges: tuple[tuple[int, int], ...],
) -> dict[tuple[int, int], dict[str, Any]]:
    raw = circuit.metadata.get(AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY, {})
    return normalize_axis1_static_zz_calibrations(
        raw,
        num_qubits=circuit.num_qubits,
        declared_edges=declared_edges,
        label=f"CircuitIR.metadata.{AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY}",
    )


def _axis1_local_lindblad_context_metadata(circuit: CircuitIR) -> dict:
    raw = circuit.metadata.get(AXIS1_LOCAL_LINDBLAD_CONTEXT_METADATA_KEY, {})
    context = normalize_axis1_local_lindblad_context(raw)
    return {} if context.is_trivial else context.to_manifest()


def _record_layout_ref(circuit: CircuitIR) -> dict:
    record_layout = circuit.metadata.get("record_layout")
    ref = {
        "measurement_keys": list(circuit.measurement_keys),
        "detector_names": list(circuit.detector_names),
        "observable_names": list(circuit.observable_names),
        "detectors": [
            {
                "name": step.name,
                "keys": list(step.keys),
                "coords": list(step.coords),
            }
            for step in circuit.steps
            if isinstance(step, DetectorDef)
        ],
        "observables": [
            {
                "name": step.name,
                "keys": list(step.keys),
                "index": int(step.index),
            }
            for step in circuit.steps
            if isinstance(step, ObservableDef)
        ],
    }
    if isinstance(record_layout, dict):
        ref["record_layout_hash"] = _stable_hash(record_layout)
        schedule_name = record_layout.get("schedule_name")
        if schedule_name is not None:
            ref["schedule_name"] = str(schedule_name)
    return ref


def _circuit_ir_manifest(circuit: CircuitIR) -> dict:
    return {
        "schema": "error_coupling_simulator.frontend.circuit_ir_schedule_hash.v1",
        "num_qubits": circuit.num_qubits,
        "metadata": _jsonable(circuit.metadata),
        "steps": [_step_manifest(step) for step in circuit.steps],
    }


def _step_manifest(step: CircuitStep) -> dict:
    if isinstance(step, GateOp):
        return {
            "kind": "gate",
            "name": step.name,
            "targets": list(step.targets),
            "args": list(step.args),
        }
    if isinstance(step, Tick):
        return {"kind": "tick"}
    if isinstance(step, MeasureOp):
        return {
            "kind": "measurement",
            "name": step.name,
            "targets": list(step.targets),
            "keys": list(step.keys),
            "args": list(step.args),
        }
    if isinstance(step, DetectorDef):
        return {
            "kind": "detector",
            "name": step.name,
            "keys": list(step.keys),
            "coords": list(step.coords),
        }
    if isinstance(step, ObservableDef):
        return {
            "kind": "observable",
            "name": step.name,
            "keys": list(step.keys),
            "index": step.index,
        }
    raise TypeError(f"unknown CircuitIR step {type(step)!r}")


def _stable_hash(value: Any) -> str:
    payload = json.dumps(
        _jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _sorted_unique(values: Sequence[int]) -> tuple[int, ...]:
    return tuple(sorted({int(v) for v in values}))


__all__ = [
    "ANALOG_SCHEDULE_REPRESENTABILITY",
    "AXIS1_STATIC_ZZ_CALIBRATIONS_METADATA_KEY",
    "AXIS1_STATIC_ZZ_COUPLINGS_METADATA_KEY",
    "COMPILER_SCHEDULE_SEAL_SCHEMA",
    "H3_H5_DURATION_POLICY_ID",
    "SCHEDULE_SCHEMA_VERSION",
    "AnalogSubstepIR",
    "DurationBracket",
    "DurationPolicy",
    "SubstepOperation",
    "SubstepSchedule",
    "circuit_ir_to_substep_schedule",
    "compile_code_spec_to_substep_schedule",
    "h3_h5_duration_policy",
    "has_valid_compiler_schedule_seal",
    "require_compiler_schedule_seal",
    "stim_circuit_to_substep_schedule",
]
