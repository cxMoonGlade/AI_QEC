from __future__ import annotations

"""Axis-1 mechanism selection plans derived from public schedule metadata."""

from dataclasses import dataclass
from typing import Any

from .analog_schedule import AnalogSubstepIR, SubstepSchedule
from .axis1_context import (
    axis1_contextual_fsim_residual_primitives,
    axis1_contextual_primitive_names,
    axis1_local_lindblad_context_from_schedule,
)
from .metadata_guard import (
    axis1_static_zz_calibrations_to_manifest,
    normalize_axis1_static_zz_calibrations,
)


AXIS1_SELECTION_SCHEMA = "qec_twin.simulator.Axis1MechanismSelectionPlan.v1"
AXIS1_SELECTION_PARTITION_SCHEMA = "qec_twin.simulator.Axis1SelectionPartition.v1"
AXIS1_G2_SELECTOR_ID = "axis1_g2_registered_rows_v1"
AXIS1_SCHEDULE_SELECTOR_ID = "axis1_schedule_joint_channel_selector_v1"
AXIS1_IDLE_CLUSTER_MAX_SUPPORT = 5
AXIS1_ONE_QUBIT_CLUSTER_MAX_SUPPORT = 5
AXIS1_READOUT_CLUSTER_MAX_SUPPORT = 5
AXIS1_TWO_QUBIT_CLUSTER_MAX_SUPPORT = 5
AXIS1_G2_DRIVE_GATE_NAMES = frozenset({"H", "X", "SQRT_X", "SQRT_X_DAG", "H_XY", "H_XZ"})
AXIS1_FRONTEND_ONE_QUBIT_CONTROL_GATES = frozenset(
    {
        "C_XYZ",
        "C_ZYX",
        "H",
        "H_XY",
        "H_XZ",
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
)
AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES = frozenset(
    {
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
)
AXIS1_G2_DRIVE_SLOTS = frozenset({"drive", "idle", "spectator"})
AXIS1_SUPPORTED_SELECTION_ROW_KINDS = frozenset(
    {
        "zz_t2_exact_zero",
        "dr_zz_prediction_band",
        "multi_one_qubit_drive_cluster_joint_channel",
        "multi_one_qubit_drive_local_joint_channel",
        "multi_one_qubit_drive_zz_cluster_joint_channel",
        "one_qubit_drive_cluster_joint_channel",
        "one_qubit_drive_joint_channel",
        "one_qubit_drive_local_joint_channel",
        "one_qubit_drive_zz_cluster_joint_channel",
        "one_qubit_drive_zz_joint_channel",
        "idle_cluster_joint_channel",
        "idle_pair_joint_channel",
        "idle_zz_cluster_joint_channel",
        "readout_cluster_joint_channel",
        "readout_pair_joint_channel",
        "readout_zz_cluster_joint_channel",
        "two_qubit_control_cluster_joint_channel",
        "two_qubit_control_zz_cluster_joint_channel",
        "two_qubit_zz_joint_channel",
        "two_qubit_control_joint_channel",
    }
)


@dataclass(frozen=True)
class Axis1MechanismSelection:
    """One schedule-derived primitive-selection record."""

    selection_id: str
    row_kind: str
    substep_id: str
    substep_kind: str
    participant: tuple[int, ...]
    primitive_names: tuple[str, ...]
    mechanism_pair: tuple[str, str]
    context_mechanisms: tuple[str, ...]
    operation_names: tuple[str, ...]
    source_step_indices: tuple[int, ...]
    operation_records: tuple[dict[str, Any], ...]
    dt_ns_nominal: float | None
    dt_ns_bracket: tuple[float, float]
    dt_source: str
    mechanism_slots: tuple[str, ...]
    reason: str
    coupling_edges: tuple[tuple[int, int], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "selection_id", str(self.selection_id))
        object.__setattr__(self, "row_kind", str(self.row_kind))
        object.__setattr__(self, "substep_id", str(self.substep_id))
        object.__setattr__(self, "substep_kind", str(self.substep_kind))
        participant = tuple(int(q) for q in self.participant)
        if len(participant) < 1:
            raise ValueError("Axis-1 selection participant must contain at least one qubit")
        if len(set(participant)) != len(participant):
            raise ValueError("Axis-1 selection participant must contain distinct qubits")
        object.__setattr__(self, "participant", participant)
        object.__setattr__(self, "primitive_names", tuple(str(x).upper() for x in self.primitive_names))
        object.__setattr__(self, "mechanism_pair", tuple(str(x).upper() for x in self.mechanism_pair))
        object.__setattr__(self, "context_mechanisms", tuple(str(x).upper() for x in self.context_mechanisms))
        object.__setattr__(self, "operation_names", tuple(str(x).upper() for x in self.operation_names))
        object.__setattr__(self, "source_step_indices", tuple(int(i) for i in self.source_step_indices))
        object.__setattr__(self, "operation_records", tuple(dict(record) for record in self.operation_records))
        nominal = None if self.dt_ns_nominal is None else float(self.dt_ns_nominal)
        object.__setattr__(self, "dt_ns_nominal", nominal)
        lo, hi = self.dt_ns_bracket
        object.__setattr__(self, "dt_ns_bracket", (float(lo), float(hi)))
        object.__setattr__(self, "dt_source", str(self.dt_source))
        object.__setattr__(self, "mechanism_slots", tuple(str(slot) for slot in self.mechanism_slots))
        object.__setattr__(self, "reason", str(self.reason))
        participant_set = set(participant)
        raw_edges = tuple(tuple(int(q) for q in edge) for edge in self.coupling_edges)
        for edge in raw_edges:
            if len(edge) != 2:
                raise ValueError(f"invalid Axis-1 coupling edge {edge!r}")
        edges = tuple(_normal_pair(*edge) for edge in raw_edges)
        if len(set(edges)) != len(edges):
            raise ValueError("Axis-1 selection coupling_edges must be unique")
        for edge in edges:
            if len(edge) != 2 or edge[0] == edge[1]:
                raise ValueError(f"invalid Axis-1 coupling edge {edge!r}")
            if edge[0] not in participant_set or edge[1] not in participant_set:
                raise ValueError(
                    "Axis-1 selection coupling_edges must be contained in participant; "
                    f"edge={edge!r} participant={participant!r}"
                )
        zz_cluster_rows = {
            "idle_zz_cluster_joint_channel",
            "multi_one_qubit_drive_zz_cluster_joint_channel",
            "one_qubit_drive_zz_cluster_joint_channel",
            "readout_zz_cluster_joint_channel",
            "two_qubit_control_zz_cluster_joint_channel",
        }
        active_pair_edge_rows = {
            "one_qubit_drive_zz_joint_channel",
            "two_qubit_zz_joint_channel",
        }
        if edges and self.row_kind not in zz_cluster_rows | active_pair_edge_rows:
            raise ValueError(
                "Axis-1 coupling_edges are currently only valid for "
                "static-ZZ union-support cluster selections or active CZ/ZZ pair provenance"
            )
        if self.row_kind in zz_cluster_rows:
            if not edges:
                raise ValueError(
                    f"{self.row_kind} requires coupling_edges"
                )
            if len(participant) < 2:
                raise ValueError(
                    f"{self.row_kind} requires at least two qubits in its union support"
                )
        if self.row_kind in active_pair_edge_rows and edges:
            if len(participant) != 2 or edges != (_normal_pair(participant[0], participant[1]),):
                raise ValueError(
                    f"{self.row_kind} coupling_edges must be exactly the "
                    "selected participant pair"
                )
        object.__setattr__(self, "coupling_edges", edges)
        if self.row_kind not in AXIS1_SUPPORTED_SELECTION_ROW_KINDS:
            raise ValueError(f"unsupported Axis-1 selection row_kind {self.row_kind!r}")
        if not self.primitive_names:
            raise ValueError("Axis-1 selection requires at least one primitive")
        if len(self.mechanism_pair) != 2:
            raise ValueError("Axis-1 selection mechanism_pair must have length 2")
        if self.dt_ns_bracket[0] < 0.0 or self.dt_ns_bracket[1] < self.dt_ns_bracket[0]:
            raise ValueError(f"invalid selection dt bracket {self.dt_ns_bracket}")

    def to_manifest(self) -> dict[str, Any]:
        payload = {
            "selection_id": self.selection_id,
            "row_kind": self.row_kind,
            "substep_id": self.substep_id,
            "substep_kind": self.substep_kind,
            "participant": list(self.participant),
            "primitive_names": list(self.primitive_names),
            "mechanism_pair": list(self.mechanism_pair),
            "context_mechanisms": list(self.context_mechanisms),
            "operation_names": list(self.operation_names),
            "source_step_indices": list(self.source_step_indices),
            "source_operation_ids": [f"step:{i}" for i in self.source_step_indices],
            "operations": [dict(record) for record in self.operation_records],
            "dt_ns_nominal": self.dt_ns_nominal,
            "dt_ns_bracket": list(self.dt_ns_bracket),
            "dt_source": self.dt_source,
            "mechanism_slots": list(self.mechanism_slots),
            "reason": self.reason,
            "epistemic_class": "c",
        }
        if self.coupling_edges:
            payload["coupling_edges"] = [list(edge) for edge in self.coupling_edges]
        return payload


@dataclass(frozen=True)
class Axis1MechanismSelectionPlan:
    """Schedule-derived selection plan consumed by the Axis-1 bridge."""

    source_kind: str
    source_hash: str
    selections: tuple[Axis1MechanismSelection, ...]
    static_zz_pairs: tuple[tuple[int, int], ...]
    static_zz_calibrations: dict[tuple[int, int], dict[str, Any]] | None = None
    selector_id: str = AXIS1_G2_SELECTOR_ID
    schema: str = AXIS1_SELECTION_SCHEMA
    axis1_local_lindblad_context: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_kind", str(self.source_kind))
        object.__setattr__(self, "source_hash", str(self.source_hash))
        object.__setattr__(self, "selections", tuple(self.selections))
        pairs = tuple(_normal_pair(*pair) for pair in self.static_zz_pairs)
        object.__setattr__(self, "static_zz_pairs", tuple(sorted(set(pairs))))
        calibrations = normalize_axis1_static_zz_calibrations(
            self.static_zz_calibrations or {},
            declared_edges=tuple(sorted(set(pairs))),
            label="Axis1MechanismSelectionPlan.static_zz_calibrations",
        )
        object.__setattr__(self, "static_zz_calibrations", calibrations)
        object.__setattr__(self, "selector_id", str(self.selector_id))
        object.__setattr__(self, "schema", str(self.schema))
        context = (
            None
            if self.axis1_local_lindblad_context is None
            else dict(self.axis1_local_lindblad_context)
        )
        object.__setattr__(self, "axis1_local_lindblad_context", context)
        if not self.source_hash:
            raise ValueError("Axis-1 selection plan requires source_hash")

    def by_kind(self, row_kind: str) -> tuple[Axis1MechanismSelection, ...]:
        return tuple(selection for selection in self.selections if selection.row_kind == row_kind)

    def require_kind(self, row_kind: str) -> tuple[Axis1MechanismSelection, ...]:
        found = self.by_kind(row_kind)
        if not found:
            raise ValueError(f"Axis-1 selection plan has no {row_kind!r} selection")
        return found

    def to_manifest(self) -> dict[str, Any]:
        out = {
            "schema": self.schema,
            "selector_id": self.selector_id,
            "source_kind": self.source_kind,
            "source_hash": self.source_hash,
            "static_zz_pairs": [list(pair) for pair in self.static_zz_pairs],
            "static_zz_calibrations": axis1_static_zz_calibrations_to_manifest(
                self.static_zz_calibrations
            ),
            "selections": [selection.to_manifest() for selection in self.selections],
            "representability": "schedule_derived_axis1_selection_no_h_or_c_payload",
            "scope": "selection only; primitive lowering happens in qec_twin.mechanisms.axis1_primitives",
        }
        if self.axis1_local_lindblad_context:
            out["axis1_local_lindblad_context"] = dict(
                self.axis1_local_lindblad_context
            )
        return out


@dataclass(frozen=True)
class Axis1SelectionLayer:
    """Schedule-ordered, same-substep selection layer."""

    substep_id: str
    order_index: int
    substep_kind: str
    selections: tuple[Axis1MechanismSelection, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "substep_id", str(self.substep_id))
        object.__setattr__(self, "order_index", int(self.order_index))
        object.__setattr__(self, "substep_kind", str(self.substep_kind))
        selections = tuple(self.selections)
        if not selections:
            raise ValueError("Axis-1 selection layer requires at least one selection")
        for selection in selections:
            if selection.substep_id != self.substep_id:
                raise ValueError(
                    "Axis-1 selection layer substep mismatch: "
                    f"layer={self.substep_id!r} selection={selection.substep_id!r}"
                )
        object.__setattr__(self, "selections", selections)

    @property
    def participants(self) -> tuple[tuple[int, ...], ...]:
        return tuple(selection.participant for selection in self.selections)

    @property
    def selection_ids(self) -> tuple[str, ...]:
        return tuple(selection.selection_id for selection in self.selections)

    def to_manifest(self) -> dict[str, Any]:
        return {
            "substep_id": self.substep_id,
            "order_index": self.order_index,
            "substep_kind": self.substep_kind,
            "selection_ids": list(self.selection_ids),
            "row_kinds": [selection.row_kind for selection in self.selections],
            "participants": [list(participant) for participant in self.participants],
            "window_count": len(self.selections),
            "same_substep_semantics": "qubit_disjoint_parallel_windows_or_single_union_support",
        }


def axis1_selection_layers_in_schedule_order(
    schedule: SubstepSchedule,
    selections: tuple[Axis1MechanismSelection, ...],
    *,
    consumer_name: str = "Axis-1 selected-window evidence",
) -> tuple[Axis1SelectionLayer, ...]:
    """Partition selections into schedule-ordered, qubit-disjoint substep layers."""

    order_by_substep = {substep.substep_id: int(substep.order_index) for substep in schedule.substeps}
    kind_by_substep = {substep.substep_id: str(substep.kind) for substep in schedule.substeps}
    grouped: dict[str, list[Axis1MechanismSelection]] = {}
    for selection in selections:
        if selection.substep_id not in order_by_substep:
            raise ValueError(f"selection {selection.selection_id!r} references unknown substep")
        if len(selection.participant) < 1:
            raise ValueError(
                f"{consumer_name} requires local windows with at least one "
                f"participants; got {selection.participant!r}"
            )
        grouped.setdefault(selection.substep_id, []).append(selection)
    layers: list[Axis1SelectionLayer] = []
    for substep_id in sorted(grouped, key=lambda item: order_by_substep[item]):
        layer = tuple(sorted(grouped[substep_id], key=lambda selection: selection.selection_id))
        used: set[int] = set()
        for selection in layer:
            overlap = used.intersection(selection.participant)
            if overlap:
                raise ValueError(
                    f"{consumer_name} supports same-substep selections only when "
                    "their supports are qubit-disjoint; overlapping selected "
                    f"window(s) on {substep_id!r}: participant={selection.participant} "
                    f"overlap={sorted(overlap)}"
                )
            used.update(selection.participant)
        layers.append(
            Axis1SelectionLayer(
                substep_id=substep_id,
                order_index=order_by_substep[substep_id],
                substep_kind=kind_by_substep[substep_id],
                selections=layer,
            )
        )
    return tuple(layers)


def flatten_axis1_selection_layers(
    layers: tuple[Axis1SelectionLayer, ...],
) -> tuple[Axis1MechanismSelection, ...]:
    """Flatten schedule-ordered selection layers."""

    return tuple(selection for layer in layers for selection in layer.selections)


def axis1_selection_partition_manifest(
    layers: tuple[Axis1SelectionLayer, ...],
) -> dict[str, Any]:
    """Return JSON-safe partition evidence shared by channel/state/record paths."""

    return {
        "schema": AXIS1_SELECTION_PARTITION_SCHEMA,
        "layer_count": len(layers),
        "selection_count": sum(len(layer.selections) for layer in layers),
        "supports_are_qubit_disjoint_within_each_substep": True,
        "layer_order": "schedule_order_index_then_selection_id",
        "same_substep_semantics": "qubit_disjoint_parallel_windows_or_single_union_support",
        "layers": [layer.to_manifest() for layer in layers],
        "epistemic_class": "a",
    }


def build_axis1_g2_selection_plan(schedule: SubstepSchedule) -> Axis1MechanismSelectionPlan:
    """Build the registered G2 primitive-selection plan from schedule metadata."""

    static_pairs = _static_zz_pairs(schedule)
    if not static_pairs and _has_two_qubit_gate(schedule, "CX"):
        raise ValueError("CX is not silently relabeled as CZ for Axis-1 G2 static-ZZ selection")
    selections: list[Axis1MechanismSelection] = []
    selections.extend(_cz_exact_zero_selections(schedule))
    selections.extend(_drive_zz_selections(schedule, static_pairs=static_pairs))
    return Axis1MechanismSelectionPlan(
        source_kind=schedule.source_kind,
        source_hash=schedule.source_hash,
        static_zz_pairs=tuple(static_pairs),
        static_zz_calibrations=_static_zz_calibrations(schedule),
        selections=tuple(selections),
    )


def build_axis1_schedule_selection_plan(schedule: SubstepSchedule) -> Axis1MechanismSelectionPlan:
    """Build generic schedule-derived selections for joint-channel evidence.

    This selector is broader than the G2 gate selector. It selects supported
    positive-duration one-qubit control, explicit-duration idle, supported
    two-qubit frontend controls, and explicit-duration readout substeps for
    local joint-channel carrier evidence.
    DR remains a G2 diagnostic primitive; generic frontend gates are lowered by
    the Axis-1 bridge as ideal control Hamiltonians.
    """

    static_pairs = _static_zz_pairs(schedule)
    selections: list[Axis1MechanismSelection] = []
    selections.extend(_generic_drive_selections(schedule, static_pairs=static_pairs))
    idle_cluster_selections = _generic_idle_cluster_selections(
        schedule,
        static_pairs=static_pairs,
    )
    selections.extend(idle_cluster_selections)
    unsupported_static_cluster_substeps = _unsupported_static_cluster_substep_ids(
        schedule,
        static_pairs=static_pairs,
    )
    clustered_idle_substeps = {
        selection.substep_id for selection in idle_cluster_selections
    }
    selections.extend(
        _generic_idle_joint_channel_selections(
            schedule,
            skip_substep_ids=clustered_idle_substeps | unsupported_static_cluster_substeps,
        )
    )
    two_qubit_cluster_selections = _generic_two_qubit_layer_cluster_selections(
        schedule,
        static_pairs=static_pairs,
    )
    selections.extend(two_qubit_cluster_selections)
    clustered_two_qubit_substeps = {
        selection.substep_id for selection in two_qubit_cluster_selections
    }
    selections.extend(
        _generic_cz_joint_channel_selections(
            schedule,
            skip_substep_ids=clustered_two_qubit_substeps | unsupported_static_cluster_substeps,
            static_pairs=static_pairs,
        )
    )
    selections.extend(
        _generic_frontend_two_qubit_joint_channel_selections(
            schedule,
            skip_substep_ids=clustered_two_qubit_substeps | unsupported_static_cluster_substeps,
        )
    )
    readout_cluster_selections = _generic_readout_cluster_selections(
        schedule,
        static_pairs=static_pairs,
    )
    selections.extend(readout_cluster_selections)
    clustered_readout_substeps = {
        selection.substep_id for selection in readout_cluster_selections
    }
    selections.extend(
        _generic_readout_joint_channel_selections(
            schedule,
            skip_substep_ids=clustered_readout_substeps | unsupported_static_cluster_substeps,
        )
    )
    context = axis1_local_lindblad_context_from_schedule(schedule)
    if not context.is_trivial:
        selections = [
            _selection_with_lindblad_context(selection, context)
            for selection in selections
        ]
    return Axis1MechanismSelectionPlan(
        source_kind=schedule.source_kind,
        source_hash=schedule.source_hash,
        static_zz_pairs=tuple(static_pairs),
        static_zz_calibrations=_static_zz_calibrations(schedule),
        selections=tuple(selections),
        selector_id=AXIS1_SCHEDULE_SELECTOR_ID,
        axis1_local_lindblad_context=(
            None if context.is_trivial else context.to_manifest()
        ),
    )


def _cz_exact_zero_selections(schedule: SubstepSchedule) -> tuple[Axis1MechanismSelection, ...]:
    out: list[Axis1MechanismSelection] = []
    for substep in schedule.substeps:
        if substep.kind != "two_qubit_gate":
            continue
        for op in substep.operations:
            if op.name != "CZ":
                continue
            for pair in _operation_pair_participants(op):
                out.append(
                    _selection_from_substep(
                        substep,
                        participant=pair,
                        row_kind="zz_t2_exact_zero",
                        primitive_names=("ZZ", "T2"),
                        mechanism_pair=("ZZ", "T2"),
                        context_mechanisms=(),
                        reason=(
                            "explicit CZ participant supplies the registered same-substep "
                            "ZZ x T2 exact-zero diagnostic row; persistent static-ZZ "
                            "couplings are not inferred from CZ history"
                        ),
                    )
                )
    return tuple(out)


def _generic_drive_selections(
    schedule: SubstepSchedule,
    *,
    static_pairs: frozenset[tuple[int, int]],
) -> tuple[Axis1MechanismSelection, ...]:
    out: list[Axis1MechanismSelection] = []
    for substep in schedule.substeps:
        if substep.kind != "one_qubit_gate" or not substep.active_qubits:
            continue
        _validate_drive_slots(substep)
        if not all(op.name in AXIS1_FRONTEND_ONE_QUBIT_CONTROL_GATES for op in substep.operations):
            continue
        active_qubits = tuple(int(q) for q in substep.active_qubits)
        idle_qubits = tuple(int(q) for q in substep.idle_qubits)
        visible_support = active_qubits + idle_qubits
        visible_static_edges = _static_pairs_within_support(static_pairs, visible_support)
        if visible_static_edges:
            if len(visible_support) > AXIS1_ONE_QUBIT_CLUSTER_MAX_SUPPORT:
                continue
            if len(visible_support) > 2 or len(active_qubits) > 1:
                multi_active = len(active_qubits) > 1
                has_idle = bool(idle_qubits)
                out.append(
                    _selection_from_substep(
                        substep,
                        participant=visible_support,
                        row_kind=(
                            "multi_one_qubit_drive_zz_cluster_joint_channel"
                            if multi_active
                            else "one_qubit_drive_zz_cluster_joint_channel"
                        ),
                        primitive_names=(
                            ("ZZ", "T2", "T1", "T2_B", "T1_B")
                            if has_idle
                            else ("ZZ", "T2", "T1")
                        ),
                        mechanism_pair=(
                            ("CTRL_1Q_LAYER", "ZZ_CLUSTER")
                            if multi_active
                            else ("CTRL_1Q", "ZZ_CLUSTER")
                        ),
                        context_mechanisms=(
                            ("T2", "T1", "T2_B", "T1_B")
                            if has_idle
                            else ("T2", "T1")
                        ),
                        coupling_edges=visible_static_edges,
                        reason=(
                            "supported one-qubit frontend-control substep with declared "
                            "static-ZZ edge(s) inside the visible active+idle support; "
                            "generic joint-channel evidence embeds all ideal one-qubit "
                            "controls, all declared static-ZZ Hamiltonian edges in the "
                            "support, and all local T1/T2 context in one union-support "
                            "generator"
                        ),
                    )
                )
                continue
            active = int(active_qubits[0])
            spectator = int(idle_qubits[0])
            out.append(
                _selection_from_substep(
                    substep,
                    participant=(active, spectator),
                    row_kind="one_qubit_drive_zz_joint_channel",
                    primitive_names=("ZZ", "T2", "T1", "T2_B", "T1_B"),
                    mechanism_pair=("CTRL_1Q", "ZZ"),
                    context_mechanisms=("T2", "T1", "T2_B", "T1_B"),
                    coupling_edges=visible_static_edges,
                    reason=(
                        "supported one-qubit frontend control with a single idle "
                        "spectator on a declared static-ZZ pair; generic "
                        "joint-channel evidence adds the ideal control term plus "
                        "both-qubit Markovian context"
                    ),
                )
            )
            continue
        if len(active_qubits) > 1 and idle_qubits:
            if len(visible_support) > AXIS1_ONE_QUBIT_CLUSTER_MAX_SUPPORT:
                continue
            out.append(
                _selection_from_substep(
                    substep,
                    participant=visible_support,
                    row_kind="multi_one_qubit_drive_cluster_joint_channel",
                    primitive_names=("T2", "T1", "T2_B", "T1_B"),
                    mechanism_pair=("CTRL_1Q_LAYER", "T2_T1_CLUSTER"),
                    context_mechanisms=("T2", "T1", "T2_B", "T1_B"),
                    reason=(
                        "supported multi-active one-qubit frontend-control layer "
                        "with visible idle spectators and no declared static-ZZ edge "
                        "inside the visible support; generic joint-channel evidence "
                        "embeds all ideal one-qubit controls and all local T1/T2 "
                        "context in one union-support generator"
                    ),
                )
            )
            continue
        if len(active_qubits) > 1:
            if len(visible_support) > AXIS1_ONE_QUBIT_CLUSTER_MAX_SUPPORT:
                continue
            out.append(
                _selection_from_substep(
                    substep,
                    participant=visible_support,
                    row_kind="multi_one_qubit_drive_local_joint_channel",
                    primitive_names=("T2", "T1"),
                    mechanism_pair=("CTRL_1Q_LAYER", "T2_T1_LOCAL"),
                    context_mechanisms=("T2", "T1"),
                    reason=(
                        "supported active-only multi-one-qubit frontend-control layer; "
                        "generic joint-channel evidence embeds all ideal one-qubit "
                        "controls and local T1/T2 context in one active-support "
                        "generator"
                    ),
                )
            )
            continue
        for active in substep.active_qubits:
            active = int(active)
            if len(substep.idle_qubits) > 1:
                if len(visible_support) <= AXIS1_ONE_QUBIT_CLUSTER_MAX_SUPPORT:
                    out.append(
                        _selection_from_substep(
                            substep,
                            participant=(active,) + tuple(int(q) for q in substep.idle_qubits),
                            row_kind="one_qubit_drive_cluster_joint_channel",
                            primitive_names=("T2", "T1", "T2_B", "T1_B"),
                            mechanism_pair=("CTRL_1Q", "T2_T1_CLUSTER"),
                            context_mechanisms=("T2", "T1", "T2_B", "T1_B"),
                            reason=(
                                "supported one-qubit frontend control with multiple idle "
                                "spectators and no declared static-ZZ spectator; generic "
                                "joint-channel evidence embeds the ideal control and all "
                                "local T1/T2 spectator context in one union-support generator"
                            ),
                        )
                    )
                    continue
            if not idle_qubits:
                out.append(
                    _selection_from_substep(
                        substep,
                        participant=(active,),
                        row_kind="one_qubit_drive_local_joint_channel",
                        primitive_names=("T2", "T1"),
                        mechanism_pair=("CTRL_1Q", "T2_T1_LOCAL"),
                        context_mechanisms=("T2", "T1"),
                        reason=(
                            "supported active-only one-qubit frontend control; generic "
                            "joint-channel evidence embeds the ideal control term plus "
                            "local T1/T2 context"
                        ),
                    )
                )
                continue
            spectator = int(substep.idle_qubits[0])
            out.append(
                _selection_from_substep(
                    substep,
                    participant=(active, spectator),
                    row_kind="one_qubit_drive_joint_channel",
                    primitive_names=("T2", "T1", "T2_B", "T1_B"),
                    mechanism_pair=("CTRL_1Q", "T2_T1"),
                    context_mechanisms=("T2", "T1", "T2_B", "T1_B"),
                    reason=(
                        "supported one-qubit frontend control with an idle reference spectator; "
                        "generic joint-channel evidence adds the ideal control term plus "
                        "both-qubit Markovian context but no static-ZZ primitive"
                    ),
                )
            )
            continue
    return tuple(out)


def _generic_two_qubit_layer_cluster_selections(
    schedule: SubstepSchedule,
    *,
    static_pairs: frozenset[tuple[int, int]],
) -> tuple[Axis1MechanismSelection, ...]:
    out: list[Axis1MechanismSelection] = []
    for substep in schedule.substeps:
        if substep.kind != "two_qubit_gate":
            continue
        if not all(op.name in AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES for op in substep.operations):
            continue
        visible_support = tuple(int(q) for q in substep.active_qubits) + tuple(
            int(q) for q in substep.idle_qubits
        )
        if len(visible_support) > AXIS1_TWO_QUBIT_CLUSTER_MAX_SUPPORT:
            continue
        visible_static_edges = _static_pairs_within_support(static_pairs, visible_support)
        operation_pairs = _two_qubit_operation_pairs(substep)
        cross_window_static_edges = tuple(
            edge for edge in visible_static_edges if edge not in operation_pairs
        )
        has_non_cz_control = any(
            op.name != "CZ" and op.name in AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES
            for op in substep.operations
        )
        active_pair_static_edges = tuple(
            edge for edge in visible_static_edges if edge in operation_pairs
        )
        if visible_static_edges and (
            substep.idle_qubits
            or cross_window_static_edges
            or (has_non_cz_control and active_pair_static_edges)
        ):
            out.append(
                _selection_from_substep(
                    substep,
                    participant=visible_support,
                    row_kind="two_qubit_control_zz_cluster_joint_channel",
                    primitive_names=("ZZ", "T2", "T1", "T2_B", "T1_B"),
                    mechanism_pair=("CTRL_2Q_LAYER", "ZZ_CLUSTER"),
                    context_mechanisms=("T2", "T1", "T2_B", "T1_B"),
                    coupling_edges=visible_static_edges,
                    reason=(
                        "supported two-qubit frontend-control substep with visible "
                        "idle spectators or cross-window declared static-ZZ edge(s) "
                        "inside the active+idle support; generic joint-channel evidence embeds "
                        "all ideal two-qubit controls, all declared static-ZZ "
                        "Hamiltonian edges in the support, and all local T1/T2 "
                        "context in one union-support generator"
                    ),
                )
            )
            continue
        if not substep.idle_qubits:
            continue
        out.append(
            _selection_from_substep(
                substep,
                participant=visible_support,
                row_kind="two_qubit_control_cluster_joint_channel",
                primitive_names=("T2", "T1", "T2_B", "T1_B"),
                mechanism_pair=("CTRL_2Q_LAYER", "T2_T1_CLUSTER"),
                context_mechanisms=("T2", "T1", "T2_B", "T1_B"),
                reason=(
                    "supported two-qubit frontend-control substep with visible idle "
                    "spectators and no declared static-ZZ edge inside the visible "
                    "support; generic joint-channel evidence embeds all ideal "
                    "two-qubit controls and all local T1/T2 context in one "
                    "union-support generator"
                ),
            )
        )
    return tuple(out)


def _generic_cz_joint_channel_selections(
    schedule: SubstepSchedule,
    *,
    skip_substep_ids: set[str] | frozenset[str] = frozenset(),
    static_pairs: frozenset[tuple[int, int]] = frozenset(),
) -> tuple[Axis1MechanismSelection, ...]:
    out: list[Axis1MechanismSelection] = []
    for substep in schedule.substeps:
        if substep.kind != "two_qubit_gate":
            continue
        if substep.substep_id in skip_substep_ids:
            continue
        for op in substep.operations:
            if op.name != "CZ":
                continue
            for pair in _operation_pair_participants(op):
                declared_edge = _normal_pair(pair[0], pair[1])
                coupling_edges = (declared_edge,) if declared_edge in static_pairs else ()
                reason = (
                    "CZ participant selects a same-substep CZ/ZZ carrier window; "
                    "generic joint-channel evidence adds the ideal CZ control term "
                    "plus both-qubit Markovian context"
                )
                if coupling_edges:
                    reason += (
                        "; public static-ZZ metadata declares the active pair and "
                        "is recorded as provenance for the same local ZZ carrier "
                        "without adding a second ZZ term"
                    )
                else:
                    reason += " without declaring persistent static-ZZ metadata"
                out.append(
                    _selection_from_substep(
                        substep,
                        participant=pair,
                        row_kind="two_qubit_zz_joint_channel",
                        primitive_names=("ZZ", "T2", "T1", "T2_B", "T1_B"),
                        mechanism_pair=("CTRL_CZ", "ZZ"),
                        context_mechanisms=("T2", "T1", "T2_B", "T1_B"),
                        coupling_edges=coupling_edges,
                        reason=reason,
                    )
                )
    return tuple(out)


def _generic_frontend_two_qubit_joint_channel_selections(
    schedule: SubstepSchedule,
    *,
    skip_substep_ids: set[str] | frozenset[str] = frozenset(),
) -> tuple[Axis1MechanismSelection, ...]:
    out: list[Axis1MechanismSelection] = []
    for substep in schedule.substeps:
        if substep.kind != "two_qubit_gate":
            continue
        if substep.substep_id in skip_substep_ids:
            continue
        for op in substep.operations:
            if op.name == "CZ" or op.name not in AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES:
                continue
            for pair in _operation_pair_participants_ordered(op):
                out.append(
                    _selection_from_substep(
                        substep,
                        participant=pair,
                        row_kind="two_qubit_control_joint_channel",
                        primitive_names=("T2", "T1", "T2_B", "T1_B"),
                        mechanism_pair=(f"CTRL_{op.name}", "T2_T1"),
                        context_mechanisms=("T2", "T1", "T2_B", "T1_B"),
                        reason=(
                            f"{op.name} participant declares an ordered frontend-control "
                            "window; generic joint-channel evidence adds the ideal "
                            f"{op.name} control term plus both-qubit Markovian context"
                        ),
                    )
                )
    return tuple(out)


def _generic_idle_cluster_selections(
    schedule: SubstepSchedule,
    *,
    static_pairs: frozenset[tuple[int, int]],
) -> tuple[Axis1MechanismSelection, ...]:
    out: list[Axis1MechanismSelection] = []
    for substep in schedule.substeps:
        if substep.kind != "idle" or substep.dt_ns_nominal is None:
            continue
        idle_qubits = tuple(int(q) for q in substep.idle_qubits)
        if not idle_qubits or len(idle_qubits) > AXIS1_IDLE_CLUSTER_MAX_SUPPORT:
            continue
        visible_static_edges = _static_pairs_within_support(static_pairs, idle_qubits)
        if visible_static_edges:
            out.append(
                _selection_from_substep(
                    substep,
                    participant=idle_qubits,
                    row_kind="idle_zz_cluster_joint_channel",
                    primitive_names=("ZZ", "T2", "T1"),
                    mechanism_pair=("IDLE", "ZZ_CLUSTER"),
                    context_mechanisms=("T2", "T1"),
                    coupling_edges=visible_static_edges,
                    reason=(
                        "explicit-duration idle substep with declared static-ZZ "
                        "edge(s) inside the idle support; generic joint-channel "
                        "evidence embeds all declared static-ZZ Hamiltonian edges "
                        "and local T1/T2 idle context in one union-support generator"
                    ),
                )
            )
            continue
        if len(idle_qubits) == 2:
            continue
        out.append(
            _selection_from_substep(
                substep,
                participant=idle_qubits,
                row_kind="idle_cluster_joint_channel",
                primitive_names=("T2", "T1"),
                mechanism_pair=("IDLE", "T2_T1_CLUSTER"),
                context_mechanisms=("T2", "T1"),
                reason=(
                    "explicit-duration idle substep over one or more idle qubits; "
                    "generic joint-channel evidence embeds local T1/T2 idle "
                    "context in one union-support generator"
                ),
            )
        )
    return tuple(out)


def _generic_idle_joint_channel_selections(
    schedule: SubstepSchedule,
    *,
    skip_substep_ids: set[str] | frozenset[str] = frozenset(),
) -> tuple[Axis1MechanismSelection, ...]:
    out: list[Axis1MechanismSelection] = []
    for substep in schedule.substeps:
        if substep.kind != "idle" or substep.dt_ns_nominal is None:
            continue
        if substep.substep_id in skip_substep_ids:
            continue
        if len(substep.idle_qubits) < 2 or len(substep.idle_qubits) % 2:
            continue
        for i in range(0, len(substep.idle_qubits), 2):
            pair = (int(substep.idle_qubits[i]), int(substep.idle_qubits[i + 1]))
            out.append(
                _selection_from_substep(
                    substep,
                    participant=pair,
                    row_kind="idle_pair_joint_channel",
                    primitive_names=("T2", "T1", "T2_B", "T1_B"),
                    mechanism_pair=("T2_T1", "T2_T1"),
                    context_mechanisms=("T2", "T1", "T2_B", "T1_B"),
                    reason=(
                        "explicit-duration idle pair; generic joint-channel evidence "
                        "includes both-qubit Markovian idle context"
                    ),
                )
            )
    return tuple(out)


def _generic_readout_cluster_selections(
    schedule: SubstepSchedule,
    *,
    static_pairs: frozenset[tuple[int, int]],
) -> tuple[Axis1MechanismSelection, ...]:
    out: list[Axis1MechanismSelection] = []
    for substep in schedule.substeps:
        if substep.kind != "measurement" or substep.dt_ns_nominal is None:
            continue
        if any(op.basis != "Z" for op in substep.operations):
            continue
        measured = tuple(int(q) for q in substep.active_qubits)
        visible_support = tuple(int(q) for q in substep.window_support)
        if not measured or not visible_support:
            continue
        if len(visible_support) > AXIS1_READOUT_CLUSTER_MAX_SUPPORT:
            continue
        visible_static_edges = _static_pairs_within_support(static_pairs, visible_support)
        if visible_static_edges:
            out.append(
                _selection_from_substep(
                    substep,
                    participant=visible_support,
                    row_kind="readout_zz_cluster_joint_channel",
                    primitive_names=("ZZ", "RD", "T2", "T1", "T2_B", "T1_B"),
                    mechanism_pair=("READOUT", "ZZ_CLUSTER"),
                    context_mechanisms=("RD", "T2", "T1", "T2_B", "T1_B"),
                    coupling_edges=visible_static_edges,
                    reason=(
                        "explicit-duration Z readout window with declared static-ZZ "
                        "edge(s) inside the measured+idle support; generic "
                        "joint-channel evidence embeds readout dephasing on measured "
                        "qubits, declared static-ZZ Hamiltonian edges, and local "
                        "T1/T2 context in one union-support generator before "
                        "projective measurement branching"
                    ),
                )
            )
            continue
        if len(visible_support) == 2 and len(measured) == 2 and not substep.idle_qubits:
            continue
        primitive_names = (
            ("RD", "T2", "T1", "T2_B", "T1_B")
            if substep.idle_qubits
            else ("RD", "T2", "T1")
        )
        context_mechanisms = (
            ("T2", "T1", "T2_B", "T1_B")
            if substep.idle_qubits
            else ("T2", "T1")
        )
        out.append(
            _selection_from_substep(
                substep,
                participant=visible_support,
                row_kind="readout_cluster_joint_channel",
                primitive_names=primitive_names,
                mechanism_pair=("READOUT", "T2_T1_CLUSTER"),
                context_mechanisms=context_mechanisms,
                reason=(
                    "explicit-duration Z readout window over one or more measured "
                    "qubits; generic joint-channel evidence embeds readout dephasing "
                    "on measured qubits and local T1/T2 context in one union-support "
                    "generator before projective measurement branching"
                ),
            )
        )
    return tuple(out)


def _generic_readout_joint_channel_selections(
    schedule: SubstepSchedule,
    *,
    skip_substep_ids: set[str] | frozenset[str] = frozenset(),
) -> tuple[Axis1MechanismSelection, ...]:
    out: list[Axis1MechanismSelection] = []
    for substep in schedule.substeps:
        if substep.substep_id in skip_substep_ids:
            continue
        if substep.kind != "measurement" or substep.dt_ns_nominal is None:
            continue
        measured = tuple(int(q) for q in substep.active_qubits)
        if len(measured) < 2:
            continue
        if any(op.basis != "Z" for op in substep.operations):
            continue
        for i in range(0, len(measured) - 1, 2):
            pair = (measured[i], measured[i + 1])
            out.append(
                _selection_from_substep(
                    substep,
                    participant=pair,
                    row_kind="readout_pair_joint_channel",
                    primitive_names=("RD", "RD_B", "T2", "T1", "T2_B", "T1_B"),
                    mechanism_pair=("RD", "T2_T1"),
                    context_mechanisms=("RD_B", "T2", "T1", "T2_B", "T1_B"),
                    reason=(
                        "explicit-duration Z readout pair; generic joint-channel evidence "
                        "applies readout-window dephasing plus both-qubit Markovian context "
                        "before projective measurement branching"
                    ),
                )
            )
    return tuple(out)


def _drive_zz_selections(
    schedule: SubstepSchedule,
    *,
    static_pairs: frozenset[tuple[int, int]],
) -> tuple[Axis1MechanismSelection, ...]:
    out: list[Axis1MechanismSelection] = []
    for substep in schedule.substeps:
        if substep.kind != "one_qubit_gate" or not substep.active_qubits or not substep.idle_qubits:
            continue
        _validate_drive_slots(substep)
        if not any(op.name in AXIS1_G2_DRIVE_GATE_NAMES for op in substep.operations):
            continue
        for active in substep.active_qubits:
            for idle in substep.idle_qubits:
                pair = _normal_pair(int(active), int(idle))
                if pair not in static_pairs:
                    continue
                out.append(
                    _selection_from_substep(
                        substep,
                        participant=(int(active), int(idle)),
                        row_kind="dr_zz_prediction_band",
                        primitive_names=("DR", "ZZ", "T2", "T1"),
                        mechanism_pair=("DR", "ZZ"),
                        context_mechanisms=("T2", "T1"),
                        reason=(
                            "drive gate on one qubit with idle spectator on a declared static-ZZ pair; "
                            "context includes T2/T1"
                        ),
                    )
                )
    return tuple(out)


def _static_pairs_within_support(
    static_pairs: frozenset[tuple[int, int]],
    support: tuple[int, ...],
) -> tuple[tuple[int, int], ...]:
    support_set = set(int(q) for q in support)
    return tuple(
        pair
        for pair in sorted(static_pairs)
        if int(pair[0]) in support_set and int(pair[1]) in support_set
    )


def _selection_from_substep(
    substep: AnalogSubstepIR,
    *,
    participant: tuple[int, ...],
    row_kind: str,
    primitive_names: tuple[str, ...],
    mechanism_pair: tuple[str, str],
    context_mechanisms: tuple[str, ...],
    reason: str,
    coupling_edges: tuple[tuple[int, int], ...] = (),
) -> Axis1MechanismSelection:
    return Axis1MechanismSelection(
        selection_id=f"{substep.substep_id}:{row_kind}:{'_'.join(str(q) for q in participant)}",
        row_kind=row_kind,
        substep_id=substep.substep_id,
        substep_kind=substep.kind,
        participant=participant,
        primitive_names=primitive_names,
        mechanism_pair=mechanism_pair,
        context_mechanisms=context_mechanisms,
        operation_names=tuple(op.name for op in substep.operations),
        source_step_indices=tuple(op.source_step_index for op in substep.operations),
        operation_records=tuple(op.to_manifest() for op in substep.operations),
        dt_ns_nominal=substep.dt_ns_nominal,
        dt_ns_bracket=substep.dt_ns_bracket,
        dt_source=substep.dt_source,
        mechanism_slots=substep.mechanism_slots,
        reason=reason,
        coupling_edges=coupling_edges,
    )


def _selection_with_lindblad_context(
    selection: Axis1MechanismSelection,
    context,
) -> Axis1MechanismSelection:
    primitive_names = axis1_contextual_primitive_names(
        selection.primitive_names,
        context,
    )
    context_mechanisms = axis1_contextual_primitive_names(
        selection.context_mechanisms,
        context,
    )
    fsim_primitives = _fsim_residual_primitives_for_selection(selection, context)
    if fsim_primitives:
        primitive_names = _append_unique(primitive_names, fsim_primitives)
        context_mechanisms = _append_unique(context_mechanisms, fsim_primitives)
    if primitive_names == selection.primitive_names:
        return selection
    context_features: list[str] = []
    if context.include_thermal_excitation:
        context_features.append("computational-subspace thermal excitation primitives")
    if fsim_primitives:
        context_features.append("computational-subspace fSim residual Hamiltonian primitives")
    reason = f"{selection.reason}; public Axis1LocalLindbladContextSpec selects "
    reason += " and ".join(context_features)
    return Axis1MechanismSelection(
        selection_id=selection.selection_id,
        row_kind=selection.row_kind,
        substep_id=selection.substep_id,
        substep_kind=selection.substep_kind,
        participant=selection.participant,
        primitive_names=primitive_names,
        mechanism_pair=selection.mechanism_pair,
        context_mechanisms=context_mechanisms,
        operation_names=selection.operation_names,
        source_step_indices=selection.source_step_indices,
        operation_records=selection.operation_records,
        dt_ns_nominal=selection.dt_ns_nominal,
        dt_ns_bracket=selection.dt_ns_bracket,
        dt_source=selection.dt_source,
        mechanism_slots=selection.mechanism_slots,
        reason=reason,
        coupling_edges=selection.coupling_edges,
    )


def _fsim_residual_primitives_for_selection(
    selection: Axis1MechanismSelection,
    context,
) -> tuple[str, ...]:
    if selection.substep_kind != "two_qubit_gate":
        return ()
    if selection.row_kind not in {
        "two_qubit_control_cluster_joint_channel",
        "two_qubit_control_joint_channel",
        "two_qubit_control_zz_cluster_joint_channel",
        "two_qubit_zz_joint_channel",
    }:
        return ()
    return axis1_contextual_fsim_residual_primitives(context)


def _append_unique(base: tuple[str, ...], extra: tuple[str, ...]) -> tuple[str, ...]:
    out = list(base)
    for name in extra:
        if name not in out:
            out.append(name)
    return tuple(out)


def _validate_drive_slots(substep: AnalogSubstepIR) -> None:
    actual = set(substep.mechanism_slots)
    if actual != AXIS1_G2_DRIVE_SLOTS:
        raise ValueError(
            "Axis-1 G2 drive selection requires one-qubit drive mechanism slots "
            f"{sorted(AXIS1_G2_DRIVE_SLOTS)}, got {sorted(actual)} on {substep.substep_id!r}"
        )


def _static_zz_pairs(schedule: SubstepSchedule) -> frozenset[tuple[int, int]]:
    return frozenset(
        _normal_pair(edge[0], edge[1])
        for edge in getattr(schedule, "static_zz_couplings", ())
    )


def _static_zz_calibrations(schedule: SubstepSchedule) -> dict[tuple[int, int], dict[str, Any]]:
    return normalize_axis1_static_zz_calibrations(
        getattr(schedule, "static_zz_calibrations", {}),
        declared_edges=tuple(sorted(_static_zz_pairs(schedule))),
        label="SubstepSchedule.static_zz_calibrations",
    )


def _unsupported_static_cluster_substep_ids(
    schedule: SubstepSchedule,
    *,
    static_pairs: frozenset[tuple[int, int]],
) -> set[str]:
    out: set[str] = set()
    if not static_pairs:
        return out
    for substep in schedule.substeps:
        if substep.kind == "one_qubit_gate":
            max_support = AXIS1_ONE_QUBIT_CLUSTER_MAX_SUPPORT
        elif substep.kind == "two_qubit_gate":
            max_support = AXIS1_TWO_QUBIT_CLUSTER_MAX_SUPPORT
        elif substep.kind == "idle":
            max_support = AXIS1_IDLE_CLUSTER_MAX_SUPPORT
        elif substep.kind == "measurement":
            max_support = AXIS1_READOUT_CLUSTER_MAX_SUPPORT
        else:
            continue
        support = tuple(int(q) for q in substep.window_support)
        if (
            len(support) > max_support
            and _static_pairs_within_support(static_pairs, support)
        ):
            out.add(substep.substep_id)
    return out


def _operation_pair_participants(op) -> tuple[tuple[int, int], ...]:
    targets = tuple(int(q) for q in op.targets)
    if len(targets) % 2:
        raise ValueError(f"{op.name} operation has odd target count: {targets}")
    pairs: list[tuple[int, int]] = []
    for i in range(0, len(targets), 2):
        pairs.append(_normal_pair(targets[i], targets[i + 1]))
    return tuple(pairs)


def _two_qubit_operation_pairs(substep: AnalogSubstepIR) -> frozenset[tuple[int, int]]:
    pairs: set[tuple[int, int]] = set()
    for op in substep.operations:
        if op.name in AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES:
            pairs.update(_operation_pair_participants(op))
    return frozenset(pairs)


def _operation_pair_participants_ordered(op) -> tuple[tuple[int, int], ...]:
    targets = tuple(int(q) for q in op.targets)
    if len(targets) % 2:
        raise ValueError(f"{op.name} operation has odd target count: {targets}")
    pairs: list[tuple[int, int]] = []
    seen: set[int] = set()
    for i in range(0, len(targets), 2):
        a = targets[i]
        b = targets[i + 1]
        if a == b:
            raise ValueError(f"{op.name} operation has repeated pair target: {(a, b)}")
        overlap = seen.intersection((a, b))
        if overlap:
            raise ValueError(f"{op.name} operation has overlapping pair target(s): {targets}")
        seen.update((a, b))
        pairs.append((a, b))
    return tuple(pairs)


def _has_two_qubit_gate(schedule: SubstepSchedule, name: str) -> bool:
    target_name = str(name).upper()
    return any(
        substep.kind == "two_qubit_gate" and any(op.name == target_name for op in substep.operations)
        for substep in schedule.substeps
    )


def _normal_pair(a: int, b: int) -> tuple[int, int]:
    a = int(a)
    b = int(b)
    if a == b:
        raise ValueError("Axis-1 mechanism-selection pair must contain distinct qubits")
    return (a, b) if a < b else (b, a)


__all__ = [
    "AXIS1_G2_DRIVE_GATE_NAMES",
    "AXIS1_G2_DRIVE_SLOTS",
    "AXIS1_FRONTEND_ONE_QUBIT_CONTROL_GATES",
    "AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES",
    "AXIS1_G2_SELECTOR_ID",
    "AXIS1_IDLE_CLUSTER_MAX_SUPPORT",
    "AXIS1_ONE_QUBIT_CLUSTER_MAX_SUPPORT",
    "AXIS1_READOUT_CLUSTER_MAX_SUPPORT",
    "AXIS1_SCHEDULE_SELECTOR_ID",
    "AXIS1_TWO_QUBIT_CLUSTER_MAX_SUPPORT",
    "AXIS1_SELECTION_SCHEMA",
    "AXIS1_SELECTION_PARTITION_SCHEMA",
    "AXIS1_SUPPORTED_SELECTION_ROW_KINDS",
    "Axis1MechanismSelection",
    "Axis1MechanismSelectionPlan",
    "Axis1SelectionLayer",
    "axis1_selection_layers_in_schedule_order",
    "axis1_selection_partition_manifest",
    "build_axis1_g2_selection_plan",
    "build_axis1_schedule_selection_plan",
    "flatten_axis1_selection_layers",
]
