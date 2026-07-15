from __future__ import annotations

"""Axis-1 scalable-carrier program seam.

This module builds a JSON-safe program IR from the public compiler schedule and
Axis-1 selection metadata. It does not execute a scalable MPS/trajectory backend,
does not materialize Hamiltonian/collapse matrices, and does not replace the
dense joint-channel evidence backend. Its job is to make over-cap schedule rows
explicitly routable instead of silently dropped by the dense local-window cap.
"""

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any

from ..mechanisms.axis1_primitives import Axis1PrimitiveParams
from .analog_schedule import SubstepSchedule
from .joint_channel_comparison import (
    JOINT_CHANNEL_GAMMA_1_PER_NS,
    JOINT_CHANNEL_GAMMA_PHI_PER_NS,
    JOINT_CHANNEL_ZETA_RAD_PER_NS,
)
from .axis1_channel_evidence import _coverage_manifest
from .axis1_context import (
    Axis1LocalLindbladContextSpec,
    axis1_local_lindblad_context_from_schedule,
)
from .axis1_ideal_controls import lower_ideal_controls_for_selection
from .axis1_selection import (
    AXIS1_FRONTEND_ONE_QUBIT_CONTROL_GATES,
    AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES,
    AXIS1_IDLE_CLUSTER_MAX_SUPPORT,
    AXIS1_ONE_QUBIT_CLUSTER_MAX_SUPPORT,
    AXIS1_READOUT_CLUSTER_MAX_SUPPORT,
    AXIS1_TWO_QUBIT_CLUSTER_MAX_SUPPORT,
    Axis1MechanismSelection,
    build_axis1_schedule_selection_plan,
)


AXIS1_CARRIER_PROGRAM_SCHEMA = "error_coupling_simulator.frontend.carrier_program.v1"
AXIS1_CARRIER_PROGRAM_REPRESENTABILITY = (
    "axis1_scalable_carrier_program_metadata_no_channel_payload"
)
AXIS1_CARRIER_DEFAULT_BACKEND_CONTRACT = "qt_mps_state_record"
AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT = "mcwf_mps_state_record"
AXIS1_CARRIER_ALLOWED_BACKEND_CONTRACTS = frozenset(
    {
        AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
        "qt_mps_state_record",
        "qutip_cuquantum_probe",
    }
)


@dataclass(frozen=True)
class Axis1CarrierTerm:
    """One JSON-safe term in the Axis-1 scalable-carrier program."""

    kind: str
    support: tuple[int, ...]
    operator_family: str
    coefficient: float | None
    coefficient_source: str
    provenance: dict[str, Any]
    epistemic_class: str = "c"

    def __post_init__(self) -> None:
        kind = str(self.kind)
        if kind not in {"hamiltonian", "collapse", "instrument", "measurement_boundary"}:
            raise ValueError(f"invalid Axis-1 carrier term kind {kind!r}")
        object.__setattr__(self, "kind", kind)
        support = tuple(int(q) for q in self.support)
        if any(q < 0 for q in support):
            raise ValueError(f"Axis-1 carrier term has negative support: {support!r}")
        object.__setattr__(self, "support", support)
        object.__setattr__(self, "operator_family", str(self.operator_family).upper())
        coefficient = None if self.coefficient is None else float(self.coefficient)
        if coefficient is not None and not math.isfinite(coefficient):
            raise ValueError(f"invalid Axis-1 carrier coefficient {coefficient!r}")
        object.__setattr__(self, "coefficient", coefficient)
        object.__setattr__(self, "coefficient_source", str(self.coefficient_source))
        object.__setattr__(self, "provenance", dict(self.provenance))
        object.__setattr__(self, "epistemic_class", str(self.epistemic_class))

    def to_manifest(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "support": list(self.support),
            "operator_family": self.operator_family,
            "coefficient": self.coefficient,
            "coefficient_source": self.coefficient_source,
            "provenance": _jsonable(self.provenance),
            "epistemic_class": self.epistemic_class,
        }


@dataclass(frozen=True)
class Axis1CarrierSubstep:
    """One schedule substep routed into the carrier program."""

    substep_id: str
    substep_kind: str
    route: str
    route_reason: str
    support: tuple[int, ...]
    active_qubits: tuple[int, ...]
    idle_qubits: tuple[int, ...]
    coupling_edges: tuple[tuple[int, int], ...]
    operation_records: tuple[dict[str, Any], ...]
    terms: tuple[Axis1CarrierTerm, ...]
    dt_ns: float | None
    dt_ns_nominal: float | None
    dt_ns_bracket: tuple[float, float]
    dt_source: str
    selection_ids: tuple[str, ...] = ()
    row_kinds: tuple[str, ...] = ()
    epistemic_class: str = "c"

    def to_manifest(self) -> dict[str, Any]:
        return {
            "substep_id": self.substep_id,
            "substep_kind": self.substep_kind,
            "route": self.route,
            "route_reason": self.route_reason,
            "support": list(self.support),
            "active_qubits": list(self.active_qubits),
            "idle_qubits": list(self.idle_qubits),
            "coupling_edges": [list(edge) for edge in self.coupling_edges],
            "operation_records": [dict(record) for record in self.operation_records],
            "terms": [term.to_manifest() for term in self.terms],
            "dt_ns": self.dt_ns,
            "dt_ns_nominal": self.dt_ns_nominal,
            "dt_ns_bracket": list(self.dt_ns_bracket),
            "dt_source": self.dt_source,
            "selection_ids": list(self.selection_ids),
            "row_kinds": list(self.row_kinds),
            "epistemic_class": self.epistemic_class,
        }


@dataclass(frozen=True)
class Axis1CarrierProgram:
    """Serializable Axis-1 carrier program from a compiler-produced schedule."""

    source_kind: str
    source_hash: str
    num_qubits: int
    site_order: tuple[int, ...]
    substeps: tuple[Axis1CarrierSubstep, ...]
    backend_contract: str = AXIS1_CARRIER_DEFAULT_BACKEND_CONTRACT
    gpu_required: bool = True
    schema: str = AXIS1_CARRIER_PROGRAM_SCHEMA

    def __post_init__(self) -> None:
        backend = str(self.backend_contract)
        if backend not in AXIS1_CARRIER_ALLOWED_BACKEND_CONTRACTS:
            raise ValueError(f"unsupported Axis-1 carrier backend_contract {backend!r}")
        object.__setattr__(self, "backend_contract", backend)
        object.__setattr__(self, "source_kind", str(self.source_kind))
        object.__setattr__(self, "source_hash", str(self.source_hash))
        object.__setattr__(self, "num_qubits", int(self.num_qubits))
        object.__setattr__(self, "site_order", tuple(int(q) for q in self.site_order))
        object.__setattr__(self, "substeps", tuple(self.substeps))
        object.__setattr__(self, "gpu_required", bool(self.gpu_required))
        if self.schema != AXIS1_CARRIER_PROGRAM_SCHEMA:
            raise ValueError(
                f"unsupported carrier-program schema {self.schema!r}; "
                f"expected {AXIS1_CARRIER_PROGRAM_SCHEMA!r}"
            )

    @property
    def requires_scalable_backend(self) -> bool:
        return any(substep.route == "scalable_required" for substep in self.substeps)

    def to_manifest(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source_kind": self.source_kind,
            "source_hash": self.source_hash,
            "num_qubits": self.num_qubits,
            "site_order": list(self.site_order),
            "site_order_policy": "identity_schedule_qubit_order_v1",
            "backend_contract": self.backend_contract,
            "gpu_required": self.gpu_required,
            "requires_scalable_backend": self.requires_scalable_backend,
            "representability": AXIS1_CARRIER_PROGRAM_REPRESENTABILITY,
            "claims_dense_channel_evidence": False,
            "claims_dem_decoder_semantics": False,
            "claims_axis2_source_timeline": False,
            "substeps": [substep.to_manifest() for substep in self.substeps],
            "approximation_book": _axis1_carrier_approximation_book(
                backend_contract=self.backend_contract,
                site_order_policy="identity_schedule_qubit_order_v1",
            ),
        }


def _axis1_carrier_approximation_book(
    *,
    backend_contract: str,
    site_order_policy: str,
) -> dict[str, Any]:
    return {
        "schema": "error_coupling_simulator.frontend.carrier_approximation_book.v1",
        "backend_contract": str(backend_contract),
        "same_substep_generator_policy": (
            "backend must consume the summed substep H_list and c_list semantics; "
            "sequential channel composition is not exact Axis-1 evidence"
        ),
        "trajectory_sampling": {
            "status": "declared_by_backend_not_executed_in_program_ir",
            "mcwf_status": (
                "mcwf_mps_state_record must interpret H_list/c_list as one "
                "same-substep unraveling problem, not sequential channel "
                "composition"
            ),
            "epistemic_class": "c",
            "single_trajectory_density_claim": False,
        },
        "state_carrier": {
            "backend_contract": str(backend_contract),
            "qt_mps_state_record": (
                "restricted computational-subspace MPS execution currently "
                "uses product-channel trajectories and is not the full MCWF "
                "contract"
            ),
            "mcwf_mps_state_record": (
                "future production route: MCWF trajectory semantics with MPS "
                "pure-state carrier and per-site local Hilbert dimensions"
            ),
            "dimension_polymorphic_local_dims_required": (
                str(backend_contract) == AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT
            ),
            "epistemic_class": "a/c",
        },
        "mps_truncation": {
            "status": "declared_by_backend_not_executed_in_program_ir",
            "required_ledger": "discarded_weight_per_truncating_operation",
            "epistemic_class": "c",
        },
        "trotter_split": {
            "status": "none_in_program_ir_backend_must_declare_if_used",
            "forbidden_exact_claim": (
                "product formulas are approximations to the summed generator, "
                "not replacements for joint_lindbladian channel evidence"
            ),
            "epistemic_class": "c",
        },
        "record_branching": {
            "status": "declared_by_backend_not_executed_in_program_ir",
            "public_record_layout_required": True,
            "claims_dem_decoder_semantics": False,
            "epistemic_class": "a/c",
        },
        "site_ordering": {
            "policy": str(site_order_policy),
            "backend_must_declare_if_changed": True,
            "epistemic_class": "c",
        },
        "dense_oracle_certification": {
            "within_cap_required": True,
            "overcap_dense_channel_rows_claimed": False,
            "comparison_outcome_is_metric": False,
            "epistemic_class": "a/c",
        },
        "scored_quantity_policy": (
            "approximation-book entries are verification gates and risk ledgers; "
            "new scored quantities require docs/METRICS.md registration"
        ),
        "epistemic_class": "c",
    }


def axis1_carrier_program_manifest(
    schedule: SubstepSchedule,
    *,
    backend_contract: str = AXIS1_CARRIER_DEFAULT_BACKEND_CONTRACT,
) -> dict[str, Any]:
    """Return a JSON-safe Axis-1 carrier program manifest.

    The result is a program/provenance object. It is not a channel-evidence
    manifest and is not a state/record execution result.
    """

    selection_plan = build_axis1_schedule_selection_plan(schedule)
    coverage = _coverage_manifest(schedule, selection_plan)
    axis1_context = axis1_local_lindblad_context_from_schedule(schedule)
    params = _axis1_primitive_params_for_schedule(schedule)
    static_edges = tuple(tuple(int(q) for q in edge) for edge in schedule.static_zz_couplings)
    static_calibrations = {
        _normal_edge(edge): dict(payload)
        for edge, payload in schedule.static_zz_calibrations.items()
    }
    substeps = _carrier_substeps_from_schedule(
        schedule,
        selection_plan.selections,
        static_edges=static_edges,
        static_calibrations=static_calibrations,
        params=params,
        axis1_context=axis1_context,
    )
    program = Axis1CarrierProgram(
        source_kind=schedule.source_kind,
        source_hash=schedule.source_hash,
        num_qubits=schedule.num_qubits,
        site_order=tuple(range(schedule.num_qubits)),
        substeps=substeps,
        backend_contract=backend_contract,
    )
    payload = {
        "schema": AXIS1_CARRIER_PROGRAM_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_CARRIER_PROGRAM_REPRESENTABILITY,
        "backend_contract": program.backend_contract,
        "gpu_required": program.gpu_required,
        "requires_scalable_backend": program.requires_scalable_backend,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "dense_selection_plan": {
            "schema": selection_plan.schema,
            "selector_id": selection_plan.selector_id,
            "selection_count": len(selection_plan.selections),
            "static_zz_pairs": [list(edge) for edge in selection_plan.static_zz_pairs],
            "static_zz_calibrations": [
                {
                    "edge": list(edge),
                    "zeta_rad_per_ns": float(payload["zeta_rad_per_ns"]),
                    "epistemic_class": str(payload["epistemic_class"]),
                }
                for edge, payload in sorted(selection_plan.static_zz_calibrations.items())
            ],
        },
        "coverage": coverage,
        "program": program.to_manifest(),
        "scope": (
            "program IR only; no dense Choi/Kraus payload, no scalable backend execution, "
            "no DEM/decoder semantics, no Axis-2 source timeline"
        ),
        "epistemic_classes": {
            "schedule_to_program_provenance": "a",
            "backend_execution": "not_claimed",
            "approximation_book": "c",
        },
    }
    if not axis1_context.is_trivial:
        payload["axis1_local_lindblad_context"] = axis1_context.to_manifest()
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def _carrier_substeps_from_schedule(
    schedule: SubstepSchedule,
    selections: tuple[Axis1MechanismSelection, ...],
    *,
    static_edges: tuple[tuple[int, int], ...],
    static_calibrations: dict[tuple[int, int], dict[str, Any]],
    params: Axis1PrimitiveParams,
    axis1_context: Axis1LocalLindbladContextSpec,
) -> tuple[Axis1CarrierSubstep, ...]:
    by_substep: dict[str, list[Axis1MechanismSelection]] = {}
    for selection in selections:
        by_substep.setdefault(selection.substep_id, []).append(selection)

    out: list[Axis1CarrierSubstep] = []
    for substep in schedule.substeps:
        dense_selections = tuple(by_substep.get(substep.substep_id, ()))
        if dense_selections:
            out.append(
                _carrier_substep_from_dense_selections(
                    substep,
                    dense_selections,
                    static_calibrations=static_calibrations,
                    params=params,
                    axis1_context=axis1_context,
                )
            )
            continue
        if substep.kind == "reset" or (
            substep.kind == "measurement" and substep.dt_ns_nominal is None
        ):
            out.append(_carrier_substep_from_boundary_only(substep))
            continue
        if substep.dt_ns_nominal is None:
            continue
        static_in_support = _static_edges_within_support(static_edges, substep.window_support)
        if static_in_support and _support_exceeds_dense_cap(substep):
            out.append(
                _carrier_substep_from_over_cap_static_support(
                    substep,
                    static_edges=static_in_support,
                    static_calibrations=static_calibrations,
                    params=params,
                    axis1_context=axis1_context,
                )
            )
    return tuple(out)


def _carrier_substep_from_boundary_only(substep) -> Axis1CarrierSubstep:
    terms: list[Axis1CarrierTerm] = []
    terms.extend(_measurement_boundary_terms(substep))
    terms.extend(_reset_boundary_terms(substep))
    return Axis1CarrierSubstep(
        substep_id=substep.substep_id,
        substep_kind=substep.kind,
        route="boundary_only",
        route_reason=(
            "projective measurement/reset boundary with no positive-duration "
            "Axis-1 joint-generator row"
        ),
        support=tuple(int(q) for q in substep.window_support),
        active_qubits=substep.active_qubits,
        idle_qubits=substep.idle_qubits,
        coupling_edges=(),
        operation_records=tuple(op.to_manifest() for op in substep.operations),
        terms=tuple(terms),
        dt_ns=substep.dt_ns_nominal,
        dt_ns_nominal=substep.dt_ns_nominal,
        dt_ns_bracket=substep.dt_ns_bracket,
        dt_source=substep.dt_source,
    )


def _carrier_substep_from_dense_selections(
    substep,
    selections: tuple[Axis1MechanismSelection, ...],
    *,
    static_calibrations: dict[tuple[int, int], dict[str, Any]],
    params: Axis1PrimitiveParams,
    axis1_context: Axis1LocalLindbladContextSpec,
) -> Axis1CarrierSubstep:
    support = _union_support(tuple(selection.participant for selection in selections))
    coupling_edges = tuple(
        edge
        for selection in selections
        for edge in selection.coupling_edges
    )
    terms: list[Axis1CarrierTerm] = []
    for selection in selections:
        terms.extend(
            _terms_for_selection(
                selection,
                static_calibrations=static_calibrations,
                params=params,
                axis1_context=axis1_context,
            )
        )
    return Axis1CarrierSubstep(
        substep_id=substep.substep_id,
        substep_kind=substep.kind,
        route="dense_oracle_available",
        route_reason="within_dense_axis1_selection_cap",
        support=support,
        active_qubits=substep.active_qubits,
        idle_qubits=substep.idle_qubits,
        coupling_edges=tuple(_normal_edge(edge) for edge in coupling_edges),
        operation_records=tuple(op.to_manifest() for op in substep.operations),
        terms=tuple(terms),
        dt_ns=substep.dt_ns_nominal,
        dt_ns_nominal=substep.dt_ns_nominal,
        dt_ns_bracket=substep.dt_ns_bracket,
        dt_source=substep.dt_source,
        selection_ids=tuple(selection.selection_id for selection in selections),
        row_kinds=tuple(selection.row_kind for selection in selections),
    )


def _carrier_substep_from_over_cap_static_support(
    substep,
    *,
    static_edges: tuple[tuple[int, int], ...],
    static_calibrations: dict[tuple[int, int], dict[str, Any]],
    params: Axis1PrimitiveParams,
    axis1_context: Axis1LocalLindbladContextSpec,
) -> Axis1CarrierSubstep:
    terms: list[Axis1CarrierTerm] = []
    terms.extend(
        _ideal_control_terms_for_over_cap_static_substep(
            substep,
            static_edges=static_edges,
        )
    )
    terms.extend(
        _static_zz_terms(
            static_edges,
            substep_id=substep.substep_id,
            static_calibrations=static_calibrations,
            params=params,
        )
    )
    terms.extend(
        _local_markov_terms(
            substep,
            support=tuple(int(q) for q in substep.window_support),
            params=params,
            axis1_context=axis1_context,
        )
    )
    terms.extend(_measurement_boundary_terms(substep))
    return Axis1CarrierSubstep(
        substep_id=substep.substep_id,
        substep_kind=substep.kind,
        route="scalable_required",
        route_reason="over_dense_cap_static_zz_union_support",
        support=tuple(int(q) for q in substep.window_support),
        active_qubits=substep.active_qubits,
        idle_qubits=substep.idle_qubits,
        coupling_edges=tuple(_normal_edge(edge) for edge in static_edges),
        operation_records=tuple(op.to_manifest() for op in substep.operations),
        terms=tuple(terms),
        dt_ns=substep.dt_ns_nominal,
        dt_ns_nominal=substep.dt_ns_nominal,
        dt_ns_bracket=substep.dt_ns_bracket,
        dt_source=substep.dt_source,
    )


def _terms_for_selection(
    selection: Axis1MechanismSelection,
    *,
    static_calibrations: dict[tuple[int, int], dict[str, Any]],
    params: Axis1PrimitiveParams,
    axis1_context: Axis1LocalLindbladContextSpec,
) -> tuple[Axis1CarrierTerm, ...]:
    terms: list[Axis1CarrierTerm] = []
    terms.extend(_ideal_control_terms(selection))
    terms.extend(
        _static_zz_terms(
            selection.coupling_edges,
            substep_id=selection.substep_id,
            static_calibrations=static_calibrations,
            params=params,
        )
    )
    terms.extend(_two_site_leakage_terms(selection, context=axis1_context))
    for q in selection.participant:
        terms.extend(
            (
                _collapse_term(
                    "T2",
                    support=(int(q),),
                    coefficient=math.sqrt(2.0 * params.gamma_phi_per_ns),
                    substep_id=selection.substep_id,
                    coefficient_source="axis1_primitive_params",
                ),
                _collapse_term(
                    "T1",
                    support=(int(q),),
                    coefficient=math.sqrt(params.gamma_1_per_ns),
                    substep_id=selection.substep_id,
                    coefficient_source="axis1_primitive_params",
                ),
            )
        )
        if params.gamma_up_per_ns > 0.0:
            terms.append(
                _collapse_term(
                    "T1_UP",
                    support=(int(q),),
                    coefficient=math.sqrt(params.gamma_up_per_ns),
                    substep_id=selection.substep_id,
                    coefficient_source="axis1_local_lindblad_context",
                )
            )
        terms.extend(
            _leakage_terms(
                support=(int(q),),
                substep_id=selection.substep_id,
                context=axis1_context,
            )
        )
    return tuple(terms)


def _two_site_leakage_terms(
    selection: Axis1MechanismSelection,
    *,
    context: Axis1LocalLindbladContextSpec,
) -> tuple[Axis1CarrierTerm, ...]:
    if not context.include_leakage or selection.substep_kind != "two_qubit_gate":
        return ()
    families = (
        (
            "LEAK_EXCHANGE_11_02",
            context.leak_exchange_11_02_rad_per_ns,
            "qutrit_ordered_pair_levels_11_02",
        ),
        (
            "LEAK_MOBILITY_12_21",
            context.leak_mobility_12_21_rad_per_ns,
            "qutrit_ordered_pair_levels_12_21",
        ),
        (
            "LEAK_TRANSPORT_30_12",
            context.leak_transport_30_12_rad_per_ns,
            "ququart_ordered_pair_levels_30_12",
        ),
        (
            "LEAK_TRANSPORT_31_22",
            context.leak_transport_31_22_rad_per_ns,
            "ququart_ordered_pair_levels_31_22",
        ),
        (
            "LEAK_COND_PHASE_LEFT2_RIGHTZ",
            context.leak_cond_phase_left2_right_z_rad_per_ns,
            "qutrit_ordered_pair_left_level_2_conditions_right_computational_z",
        ),
        (
            "LEAK_COND_PHASE_LEFTZ_RIGHT2",
            context.leak_cond_phase_left_z_right2_rad_per_ns,
            "qutrit_ordered_pair_right_level_2_conditions_left_computational_z",
        ),
    )
    active_families = tuple(
        (family, float(rate), level_model)
        for family, rate, level_model in families
        if float(rate) > 0.0
    )
    if not active_families:
        return ()
    pairs = _ordered_two_qubit_operation_pairs(selection.operation_records)
    participant_set = set(int(q) for q in selection.participant)
    out: list[Axis1CarrierTerm] = []
    for pair in pairs:
        if pair[0] not in participant_set or pair[1] not in participant_set:
            continue
        for family, rate, level_model in active_families:
            out.append(
                Axis1CarrierTerm(
                    kind="hamiltonian",
                    support=pair,
                    operator_family=family,
                    coefficient=rate,
                    coefficient_source="axis1_local_lindblad_context",
                    provenance={
                        "substep_id": selection.substep_id,
                        "selection_id": selection.selection_id,
                        "row_kind": selection.row_kind,
                        "metadata_visibility": (
                            "public_axis1_instantaneous_context_not_axis2_source"
                        ),
                        "local_level_model": level_model,
                        "orientation_policy": (
                            "ordered_frontend_two_qubit_operation_targets"
                        ),
                    },
                    epistemic_class=context.epistemic_class,
                )
            )
    return tuple(out)


def _ordered_two_qubit_operation_pairs(
    operation_records: tuple[dict[str, Any], ...],
) -> tuple[tuple[int, int], ...]:
    pairs: list[tuple[int, int]] = []
    for record in operation_records:
        targets = tuple(int(q) for q in record.get("targets", ()))
        if len(targets) < 2:
            continue
        if len(targets) % 2:
            raise ValueError(
                f"two-qubit operation record has odd target count: {targets!r}"
            )
        for index in range(0, len(targets), 2):
            left, right = int(targets[index]), int(targets[index + 1])
            if left == right:
                raise ValueError(f"two-qubit leakage pair repeats a site: {(left, right)!r}")
            pairs.append((left, right))
    return tuple(pairs)


def _static_zz_terms(
    static_edges: tuple[tuple[int, int], ...],
    *,
    substep_id: str,
    static_calibrations: dict[tuple[int, int], dict[str, Any]],
    params: Axis1PrimitiveParams,
) -> tuple[Axis1CarrierTerm, ...]:
    terms: list[Axis1CarrierTerm] = []
    for edge in tuple(_normal_edge(edge) for edge in static_edges):
        calibration = static_calibrations.get(edge)
        if calibration is None:
            coefficient = float(params.zeta_rad_per_ns)
            coefficient_source = "axis1_primitive_default"
            coeff_class = "c"
        else:
            coefficient = float(calibration["zeta_rad_per_ns"])
            coefficient_source = "public_static_zz_calibration"
            coeff_class = str(calibration["epistemic_class"])
        terms.append(
            Axis1CarrierTerm(
                kind="hamiltonian",
                support=edge,
                operator_family="ZZ",
                coefficient=coefficient,
                coefficient_source=coefficient_source,
                provenance={
                    "substep_id": substep_id,
                    "coupling_edge": list(edge),
                    "metadata_visibility": "public",
                    "coefficient_epistemic_class": coeff_class,
                },
                epistemic_class=coeff_class,
            )
        )
    return tuple(terms)


def _ideal_control_terms(
    selection: Axis1MechanismSelection,
) -> tuple[Axis1CarrierTerm, ...]:
    if selection.substep_kind not in {"one_qubit_gate", "two_qubit_gate"}:
        return ()
    if selection.dt_ns_nominal is None or float(selection.dt_ns_nominal) <= 0.0:
        return ()
    controls = lower_ideal_controls_for_selection(
        selection,
        dt_ns=float(selection.dt_ns_nominal),
        device="cuda",
    )
    terms: list[Axis1CarrierTerm] = []
    for record in controls.records:
        support = tuple(int(selection.participant[int(i)]) for i in record.support)
        terms.append(
            Axis1CarrierTerm(
                kind="hamiltonian",
                support=support,
                operator_family=record.name,
                coefficient=float(record.coefficient),
                coefficient_source="axis1_ideal_control",
                provenance={
                    "substep_id": selection.substep_id,
                    "selection_id": selection.selection_id,
                    "row_kind": selection.row_kind,
                    "gate_name": record.gate_name,
                    "generator_kind": record.generator_kind,
                    "local_support_indices": list(record.support),
                    "source_step_indices": list(record.source_step_indices),
                    "metadata_visibility": "public_frontend_operation",
                },
                epistemic_class=record.epistemic_class,
            )
        )
    return tuple(terms)


def _ideal_control_terms_for_over_cap_static_substep(
    substep,
    *,
    static_edges: tuple[tuple[int, int], ...],
) -> tuple[Axis1CarrierTerm, ...]:
    if substep.kind == "one_qubit_gate":
        if not all(
            str(op.name).upper() in AXIS1_FRONTEND_ONE_QUBIT_CONTROL_GATES
            for op in substep.operations
        ):
            return ()
        row_kind = "one_qubit_drive_zz_cluster_joint_channel"
        mechanism_pair = ("CTRL_1Q", "ZZ_CLUSTER")
    elif substep.kind == "two_qubit_gate":
        if not all(
            str(op.name).upper() in AXIS1_FRONTEND_TWO_QUBIT_CONTROL_GATES
            for op in substep.operations
        ):
            return ()
        row_kind = "two_qubit_control_zz_cluster_joint_channel"
        mechanism_pair = ("CTRL_2Q", "ZZ_CLUSTER")
    else:
        return ()
    if substep.dt_ns_nominal is None or float(substep.dt_ns_nominal) <= 0.0:
        return ()
    operation_records = tuple(op.to_manifest() for op in substep.operations)
    selection = Axis1MechanismSelection(
        selection_id=(
            f"{substep.substep_id}:over_cap_static_support_carrier_row"
        ),
        row_kind=row_kind,
        substep_id=substep.substep_id,
        substep_kind=substep.kind,
        participant=tuple(int(q) for q in substep.window_support),
        primitive_names=("ZZ", "T2", "T1", "T2_B", "T1_B"),
        mechanism_pair=mechanism_pair,
        context_mechanisms=("T2", "T1", "T2_B", "T1_B"),
        operation_names=tuple(str(op.name).upper() for op in substep.operations),
        source_step_indices=tuple(
            int(record["source_step_index"]) for record in operation_records
        ),
        operation_records=operation_records,
        dt_ns_nominal=substep.dt_ns_nominal,
        dt_ns_bracket=substep.dt_ns_bracket,
        dt_source=substep.dt_source,
        mechanism_slots=substep.mechanism_slots,
        reason=(
            "over-cap static-ZZ carrier row keeps frontend control Hamiltonians "
            "inside the same program substep as static ZZ and local Markov terms"
        ),
        coupling_edges=static_edges,
    )
    return _ideal_control_terms(selection)


def _local_markov_terms(
    substep,
    *,
    support: tuple[int, ...],
    params: Axis1PrimitiveParams,
    axis1_context: Axis1LocalLindbladContextSpec,
) -> tuple[Axis1CarrierTerm, ...]:
    terms: list[Axis1CarrierTerm] = []
    active = set(int(q) for q in substep.active_qubits)
    for q in support:
        if substep.kind == "measurement" and int(q) in active:
            terms.append(
                _collapse_term(
                    "RD",
                    support=(int(q),),
                    coefficient=math.sqrt(2.0 * params.gamma_readout_phi_per_ns),
                    substep_id=substep.substep_id,
                    coefficient_source="axis1_primitive_params",
                )
            )
        terms.append(
            _collapse_term(
                "T2",
                support=(int(q),),
                coefficient=math.sqrt(2.0 * params.gamma_phi_per_ns),
                substep_id=substep.substep_id,
                coefficient_source="axis1_primitive_params",
            )
        )
        terms.append(
            _collapse_term(
                "T1",
                support=(int(q),),
                coefficient=math.sqrt(params.gamma_1_per_ns),
                substep_id=substep.substep_id,
                coefficient_source="axis1_primitive_params",
            )
        )
        if params.gamma_up_per_ns > 0.0:
            terms.append(
                _collapse_term(
                    "T1_UP",
                    support=(int(q),),
                    coefficient=math.sqrt(params.gamma_up_per_ns),
                    substep_id=substep.substep_id,
                    coefficient_source="axis1_local_lindblad_context",
                )
            )
        terms.extend(
            _leakage_terms(
                support=(int(q),),
                substep_id=substep.substep_id,
                context=axis1_context,
            )
        )
    return tuple(terms)


def _leakage_terms(
    *,
    support: tuple[int, ...],
    substep_id: str,
    context: Axis1LocalLindbladContextSpec,
) -> tuple[Axis1CarrierTerm, ...]:
    if not context.include_leakage:
        return ()
    terms: list[Axis1CarrierTerm] = []
    provenance = {
        "substep_id": str(substep_id),
        "metadata_visibility": "public_axis1_instantaneous_context_not_axis2_source",
        "local_level_model": "qutrit_levels_1_2",
    }
    if context.leak_exchange_12_rad_per_ns > 0.0:
        terms.append(
            Axis1CarrierTerm(
                kind="hamiltonian",
                support=support,
                operator_family="LEAK_EXCHANGE_12",
                coefficient=float(context.leak_exchange_12_rad_per_ns),
                coefficient_source="axis1_local_lindblad_context",
                provenance=provenance,
                epistemic_class=context.epistemic_class,
            )
        )
    if context.leak_seep_21_per_ns > 0.0:
        terms.append(
            Axis1CarrierTerm(
                kind="collapse",
                support=support,
                operator_family="LEAK_SEEP_21",
                coefficient=math.sqrt(float(context.leak_seep_21_per_ns)),
                coefficient_source="axis1_local_lindblad_context",
                provenance=provenance,
                epistemic_class=context.epistemic_class,
            )
        )
    if context.leak_heat_12_per_ns > 0.0:
        terms.append(
            Axis1CarrierTerm(
                kind="collapse",
                support=support,
                operator_family="LEAK_HEAT_12",
                coefficient=math.sqrt(float(context.leak_heat_12_per_ns)),
                coefficient_source="axis1_local_lindblad_context",
                provenance=provenance,
                epistemic_class=context.epistemic_class,
            )
        )
    return tuple(terms)


def _collapse_term(
    operator_family: str,
    *,
    support: tuple[int, ...],
    coefficient: float,
    substep_id: str,
    coefficient_source: str,
) -> Axis1CarrierTerm:
    return Axis1CarrierTerm(
        kind="collapse",
        support=support,
        operator_family=operator_family,
        coefficient=float(coefficient),
        coefficient_source=coefficient_source,
        provenance={
            "substep_id": str(substep_id),
            "metadata_visibility": "public_defaults_or_public_context",
        },
        epistemic_class="c",
    )


def _measurement_boundary_terms(substep) -> tuple[Axis1CarrierTerm, ...]:
    if substep.kind != "measurement":
        return ()
    return tuple(
        Axis1CarrierTerm(
            kind="measurement_boundary",
            support=(int(q),),
            operator_family="MEASURE",
            coefficient=None,
            coefficient_source="projective_record_boundary",
            provenance={
                "substep_id": substep.substep_id,
                "measurement_keys": list(substep.measurement_keys),
                "metadata_visibility": "public",
            },
            epistemic_class="a",
        )
        for q in substep.active_qubits
    )


def _reset_boundary_terms(substep) -> tuple[Axis1CarrierTerm, ...]:
    if substep.kind != "reset":
        return ()
    terms: list[Axis1CarrierTerm] = []
    for op in substep.operations:
        basis = _reset_basis(str(op.name))
        if basis is None:
            continue
        for q in op.targets:
            terms.append(
                Axis1CarrierTerm(
                    kind="instrument",
                    support=(int(q),),
                    operator_family=f"RESET_{basis}",
                    coefficient=None,
                    coefficient_source="reset_boundary",
                    provenance={
                        "substep_id": substep.substep_id,
                        "operation": op.to_manifest(),
                        "metadata_visibility": "public",
                    },
                    epistemic_class="a",
                )
            )
    return tuple(terms)


def _reset_basis(name: str) -> str | None:
    op_name = str(name).upper()
    if op_name in {"R", "RZ"}:
        return "Z"
    if op_name == "RX":
        return "X"
    if op_name == "RY":
        return "Y"
    return None


def _axis1_primitive_params_for_schedule(schedule: SubstepSchedule) -> Axis1PrimitiveParams:
    defaults = Axis1PrimitiveParams(
        zeta_rad_per_ns=JOINT_CHANNEL_ZETA_RAD_PER_NS,
        gamma_phi_per_ns=JOINT_CHANNEL_GAMMA_PHI_PER_NS,
        gamma_1_per_ns=JOINT_CHANNEL_GAMMA_1_PER_NS,
    )
    context = axis1_local_lindblad_context_from_schedule(schedule)
    return context.to_axis1_primitive_params(defaults)


def _support_exceeds_dense_cap(substep) -> bool:
    if substep.kind == "one_qubit_gate":
        cap = AXIS1_ONE_QUBIT_CLUSTER_MAX_SUPPORT
    elif substep.kind == "two_qubit_gate":
        cap = AXIS1_TWO_QUBIT_CLUSTER_MAX_SUPPORT
    elif substep.kind == "idle":
        cap = AXIS1_IDLE_CLUSTER_MAX_SUPPORT
    elif substep.kind == "measurement":
        cap = AXIS1_READOUT_CLUSTER_MAX_SUPPORT
    else:
        return False
    return len(tuple(substep.window_support)) > cap


def _static_edges_within_support(
    static_edges: tuple[tuple[int, int], ...],
    support: tuple[int, ...],
) -> tuple[tuple[int, int], ...]:
    support_set = set(int(q) for q in support)
    return tuple(
        _normal_edge(edge)
        for edge in sorted(static_edges)
        if int(edge[0]) in support_set and int(edge[1]) in support_set
    )


def _union_support(groups: tuple[tuple[int, ...], ...]) -> tuple[int, ...]:
    out: list[int] = []
    seen: set[int] = set()
    for group in groups:
        for q in group:
            q = int(q)
            if q not in seen:
                out.append(q)
                seen.add(q)
    return tuple(out)


def _normal_edge(edge: tuple[int, int]) -> tuple[int, int]:
    a, b = int(edge[0]), int(edge[1])
    if a == b:
        raise ValueError(f"Axis-1 carrier edge has duplicate endpoint: {edge!r}")
    return (a, b) if a < b else (b, a)


def _stable_payload_hash(payload: dict[str, Any]) -> str:
    without_hash = dict(payload)
    without_hash.pop("content_hash", None)
    data = json.dumps(
        without_hash,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


__all__ = [
    "AXIS1_CARRIER_ALLOWED_BACKEND_CONTRACTS",
    "AXIS1_CARRIER_DEFAULT_BACKEND_CONTRACT",
    "AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT",
    "AXIS1_CARRIER_PROGRAM_REPRESENTABILITY",
    "AXIS1_CARRIER_PROGRAM_SCHEMA",
    "Axis1CarrierProgram",
    "Axis1CarrierSubstep",
    "Axis1CarrierTerm",
    "axis1_carrier_program_manifest",
]
