from __future__ import annotations

"""qutip-cuquantum symbolic lowering probe for Axis-1 carrier programs.

The probe consumes `Axis1CarrierProgram` rows and builds qutip-cuquantum
`CuOperator` objects for Hamiltonian and collapse terms. It intentionally does
not call a solver, does not execute state or record evolution, and does not emit
dense channel evidence.
"""

import hashlib
import json
import math
from typing import Any

import numpy as np

from qec_twin.simulator.analog_schedule import SubstepSchedule
from qec_twin.simulator.axis1_carrier_program import axis1_carrier_program_manifest
from qec_twin.simulator.axis1_channel_evidence import (
    _validate_schedule_for_axis1_channel_evidence,
)
from qec_twin.simulator.axis1_state_evidence import _require_cuda_device


AXIS1_QUTIP_CUQUANTUM_PROBE_SCHEMA = (
    "qec_twin.simulator.axis1_qutip_cuquantum_probe.v1"
)
AXIS1_QUTIP_CUQUANTUM_PROBE_REPRESENTABILITY = (
    "axis1_qutip_cuquantum_symbolic_lowering_probe_no_state_record_execution"
)
AXIS1_QUTIP_CUQUANTUM_PROBE_BACKEND_CONTRACT = "qutip_cuquantum_probe"
AXIS1_QUTIP_CUQUANTUM_STATE_PROBE_SCHEMA = (
    "qec_twin.simulator.axis1_qutip_cuquantum_state_probe.v1"
)
AXIS1_QUTIP_CUQUANTUM_STATE_PROBE_REPRESENTABILITY = (
    "axis1_qutip_cuquantum_state_probe_restricted_no_record_execution"
)
AXIS1_QUTIP_CUQUANTUM_STATE_PROBE_BACKEND_CONTRACT = "qutip_cuquantum_state_probe"
AXIS1_QUTIP_CUQUANTUM_TRAJECTORY_PROBE_SCHEMA = (
    "qec_twin.simulator.axis1_qutip_cuquantum_trajectory_probe.v1"
)
AXIS1_QUTIP_CUQUANTUM_TRAJECTORY_PROBE_REPRESENTABILITY = (
    "axis1_qutip_cuquantum_trajectory_probe_no_record_execution"
)
AXIS1_QUTIP_CUQUANTUM_TRAJECTORY_PROBE_BACKEND_CONTRACT = (
    "qutip_cuquantum_trajectory_probe"
)
AXIS1_QUTIP_CUQUANTUM_RECORD_PROBE_SCHEMA = (
    "qec_twin.simulator.axis1_qutip_cuquantum_record_probe.v1"
)
AXIS1_QUTIP_CUQUANTUM_RECORD_PROBE_REPRESENTABILITY = (
    "axis1_qutip_cuquantum_record_probe_restricted_no_b8_no_decoder"
)
AXIS1_QUTIP_CUQUANTUM_RECORD_PROBE_BACKEND_CONTRACT = "qutip_cuquantum_record_probe"


def axis1_qutip_cuquantum_probe_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
) -> dict[str, Any]:
    """Lower an Axis-1 carrier program into qutip-cuquantum symbolic terms."""

    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(schedule)
    qt, CuOperator = _qutip_cuquantum_imports()
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_QUTIP_CUQUANTUM_PROBE_BACKEND_CONTRACT,
    )
    dims = tuple(2 for _ in range(int(schedule.num_qubits)))
    lowered = tuple(
        _lower_substep(substep, qt=qt, CuOperator=CuOperator, dims=dims)
        for substep in program["program"]["substeps"]
    )
    payload: dict[str, Any] = {
        "schema": AXIS1_QUTIP_CUQUANTUM_PROBE_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_QUTIP_CUQUANTUM_PROBE_REPRESENTABILITY,
        "backend_contract": AXIS1_QUTIP_CUQUANTUM_PROBE_BACKEND_CONTRACT,
        "device": dev,
        "gpu_required": True,
        "carrier_program": _program_summary(program),
        "qutip_cuquantum": {
            "operator_data_type": "CuOperator",
            "solver_called": False,
            "state_materialized": False,
        },
        "claims_state_execution": False,
        "claims_record_execution": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "lowered_substeps": [dict(item) for item in lowered],
        "scope": (
            "symbolic backend lowering probe only; no mesolve/mcsolve call, no "
            "state or record execution, no dense channel payload"
        ),
        "epistemic_classes": {
            "program_to_symbolic_operator_lowering": "a/c",
            "solver_execution": "not_claimed",
            "state_record_execution": "not_claimed",
            "dense_channel_evidence": "not_claimed",
        },
    }
    if "axis1_local_lindblad_context" in program:
        payload["axis1_local_lindblad_context"] = program["axis1_local_lindblad_context"]
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def axis1_qutip_cuquantum_state_probe_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
) -> dict[str, Any]:
    """Execute a restricted qutip-cuquantum state probe for over-cap idle rows.

    This is deliberately narrower than a production carrier: it calls
    ``qutip.mesolve`` only for carrier-program substeps that have no measurement
    boundary. It emits final Z-basis probabilities, not a density-matrix payload
    and not measurement/decoder records.
    """

    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(schedule)
    qt, CuOperator, qutip_cuquantum, cudm = _qutip_cuquantum_solver_imports()
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_QUTIP_CUQUANTUM_PROBE_BACKEND_CONTRACT,
    )
    base = _state_probe_base_payload(schedule, program, dev)
    dims = tuple(2 for _ in range(int(schedule.num_qubits)))
    substeps = list(program["program"]["substeps"])
    unsupported = _unsupported_state_probe_substeps(substeps)
    if unsupported:
        payload = {
            **base,
            "verdict": "fail",
            "passed": False,
            "state_probe_executed": False,
            "blocked_reason": unsupported[0]["reason"],
            "blocked_substeps": unsupported,
            "state_probe": None,
        }
        payload["content_hash"] = _stable_payload_hash(payload)
        return payload

    rho = qt.ket2dm(qt.tensor([qt.basis(2, 0) for _ in dims]))
    applied: list[dict[str, Any]] = []
    final_state_type = None
    solver_methods: list[str] = []
    with qutip_cuquantum.CuQuantumBackend(cudm.WorkStream()):
        for substep in substeps:
            lowered = _lower_substep_for_solver(
                substep,
                qt=qt,
                CuOperator=CuOperator,
                dims=dims,
            )
            result = qt.mesolve(
                lowered["hamiltonian"],
                rho,
                [0.0, float(substep["dt_ns"])],
                c_ops=lowered["collapse_ops"],
                e_ops=[],
                options={
                    "progress_bar": False,
                    "store_states": False,
                    "store_final_state": True,
                },
            )
            rho = result.final_state
            final_state_type = type(rho.data).__name__
            solver_methods.append(str(result.stats.get("method", "unknown")))
            summary = dict(lowered["summary"])
            summary.update(
                {
                    "solver": "qutip.mesolve",
                    "solver_method": solver_methods[-1],
                }
            )
            applied.append(summary)

    probs = _density_z_probabilities(rho)
    total = float(sum(probs))
    state_probe = {
        "initial_state": "computational_zero_density_matrix",
        "solver": "qutip.mesolve",
        "solver_methods": solver_methods,
        "final_state_data_type": final_state_type,
        "density_matrix_payload_serialized": False,
        "record_execution": "not_requested",
        "num_qubits": int(schedule.num_qubits),
        "hilbert_dims": list(dims),
        "final_z_probabilities": probs,
        "final_z_probability_order": "computational_basis_qubit0_msb",
        "final_trace": total,
        "trace_residual": abs(total - 1.0),
        "trace_residual_threshold": 1.0e-8,
        "applied_substeps": applied,
        "epistemic_classes": {
            "solver_execution": "c",
            "trace_residual_threshold": "c",
            "final_z_probabilities": "c",
            "density_payload_non_serialization": "a",
            "record_non_execution": "a",
        },
    }
    passed = bool(state_probe["trace_residual"] <= state_probe["trace_residual_threshold"])
    payload = {
        **base,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "state_probe_executed": True,
        "blocked_reason": None,
        "blocked_substeps": [],
        "state_probe": state_probe,
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def axis1_qutip_cuquantum_trajectory_probe_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
    ntraj: int = 1,
) -> dict[str, Any]:
    """Execute a restricted qutip-cuquantum MCWF trajectory probe.

    This is a fast candidate seam for the future trajectory/MPS carrier. It
    keeps the trajectory state pure and emits final basis probabilities for the
    realized trajectory only; it is not density-matrix evidence and not record
    execution.
    """

    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(schedule)
    if int(ntraj) != 1:
        raise ValueError("Axis-1 qutip-cuquantum trajectory probe currently supports ntraj=1")
    qt, CuOperator, qutip_cuquantum, cudm = _qutip_cuquantum_solver_imports()
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_QUTIP_CUQUANTUM_PROBE_BACKEND_CONTRACT,
    )
    base = _trajectory_probe_base_payload(schedule, program, dev, int(ntraj))
    dims = tuple(2 for _ in range(int(schedule.num_qubits)))
    substeps = list(program["program"]["substeps"])
    unsupported = _unsupported_state_probe_substeps(substeps)
    if unsupported:
        payload = {
            **base,
            "verdict": "fail",
            "passed": False,
            "trajectory_probe_executed": False,
            "blocked_reason": unsupported[0]["reason"],
            "blocked_substeps": unsupported,
            "trajectory_probe": None,
        }
        payload["content_hash"] = _stable_payload_hash(payload)
        return payload

    psi = qt.tensor([qt.basis(2, 0) for _ in dims])
    applied: list[dict[str, Any]] = []
    final_state_type = None
    solver_methods: list[str] = []
    with qutip_cuquantum.CuQuantumBackend(cudm.WorkStream()):
        for substep in substeps:
            lowered = _lower_substep_for_solver(
                substep,
                qt=qt,
                CuOperator=CuOperator,
                dims=dims,
            )
            result = qt.mcsolve(
                lowered["hamiltonian"],
                psi,
                [0.0, float(substep["dt_ns"])],
                c_ops=lowered["collapse_ops"],
                ntraj=1,
                e_ops=[],
                options={
                    "progress_bar": False,
                    "keep_runs_results": True,
                    "store_states": False,
                    "store_final_state": True,
                },
            )
            psi = _single_final_state(result.final_state)
            final_state_type = type(psi.data).__name__
            solver_methods.append(str(result.stats.get("method", "unknown")))
            summary = dict(lowered["summary"])
            summary.update(
                {
                    "solver": "qutip.mcsolve",
                    "solver_method": solver_methods[-1],
                }
            )
            applied.append(summary)

    probs = _ket_z_probabilities(psi)
    total = float(sum(probs))
    trajectory_probe = {
        "initial_state": "computational_zero_ket",
        "solver": "qutip.mcsolve",
        "solver_methods": solver_methods,
        "ntraj": int(ntraj),
        "final_state_data_type": final_state_type,
        "statevector_payload_serialized": False,
        "record_execution": "not_requested",
        "num_qubits": int(schedule.num_qubits),
        "hilbert_dims": list(dims),
        "final_z_probabilities": probs,
        "final_z_probability_order": "computational_basis_qubit0_msb",
        "final_norm": total,
        "norm_residual": abs(total - 1.0),
        "norm_residual_threshold": 1.0e-8,
        "applied_substeps": applied,
        "epistemic_classes": {
            "trajectory_solver_execution": "c",
            "single_trajectory_realization": "c",
            "norm_residual_threshold": "c",
            "statevector_payload_non_serialization": "a",
            "record_non_execution": "a",
        },
    }
    passed = bool(
        trajectory_probe["norm_residual"] <= trajectory_probe["norm_residual_threshold"]
    )
    payload = {
        **base,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "trajectory_probe_executed": True,
        "blocked_reason": None,
        "blocked_substeps": [],
        "trajectory_probe": trajectory_probe,
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def axis1_qutip_cuquantum_record_probe_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
) -> dict[str, Any]:
    """Execute a restricted qutip-cuquantum trajectory plus Z-record probe.

    This record seam is deliberately narrow: idle, one-qubit-control, and
    Z-measurement substeps only, no `.b8`, no DEM, no decoder, and no production
    scalable-backend claim.
    """

    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(schedule)
    qt, CuOperator, qutip_cuquantum, cudm = _qutip_cuquantum_solver_imports()
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_QUTIP_CUQUANTUM_PROBE_BACKEND_CONTRACT,
    )
    base = _record_probe_base_payload(schedule, program, dev)
    substeps = list(program["program"]["substeps"])
    unsupported = _unsupported_record_probe_substeps(schedule, substeps)
    if unsupported:
        payload = {
            **base,
            "verdict": "fail",
            "passed": False,
            "record_probe_executed": False,
            "blocked_reason": unsupported[0]["reason"],
            "blocked_substeps": unsupported,
            "record_probe": None,
        }
        payload["content_hash"] = _stable_payload_hash(payload)
        return payload

    dims = tuple(2 for _ in range(int(schedule.num_qubits)))
    psi = qt.tensor([qt.basis(2, 0) for _ in dims])
    applied: list[dict[str, Any]] = []
    measurement_boundaries = _record_probe_measurement_boundaries(substeps)
    measurement_keys = [
        key
        for boundary in measurement_boundaries
        for key in boundary["measurement_keys"]
    ]
    measurement_targets = [
        target
        for boundary in measurement_boundaries
        for target in boundary["measurement_targets"]
    ]
    solver_method = "not_run"
    solver_methods: list[str] = []
    final_state_type = None
    branches: list[tuple[tuple[int, ...], float, Any]] = [((), 1.0, psi)]
    with qutip_cuquantum.CuQuantumBackend(cudm.WorkStream()):
        for substep in substeps:
            lowered = _lower_substep_for_solver(
                substep,
                qt=qt,
                CuOperator=CuOperator,
                dims=dims,
            )
            next_branches: list[tuple[tuple[int, ...], float, Any]] = []
            for record_bits, branch_weight, branch_state in branches:
                result = qt.mcsolve(
                    lowered["hamiltonian"],
                    branch_state,
                    [0.0, float(substep["dt_ns"])],
                    c_ops=lowered["collapse_ops"],
                    ntraj=1,
                    e_ops=[],
                    options={
                        "progress_bar": False,
                        "keep_runs_results": True,
                        "store_states": False,
                        "store_final_state": True,
                    },
                )
                evolved = _single_final_state(result.final_state)
                final_state_type = type(evolved.data).__name__
                solver_method = str(result.stats.get("method", "unknown"))
                solver_methods.append(solver_method)
                if str(substep["substep_kind"]) != "measurement":
                    next_branches.append((record_bits, branch_weight, evolved))
                    continue
                boundary = _record_probe_boundary_for_substep(
                    substep,
                    measurement_boundaries,
                )
                outcomes = _measurement_records(len(boundary["measurement_targets"]))
                for outcome in outcomes:
                    projected, outcome_probability = _project_z_branch(
                        evolved,
                        outcome_bits=outcome,
                        measurement_targets=boundary["measurement_targets"],
                        qt=qt,
                        CuOperator=CuOperator,
                        dims=dims,
                    )
                    if outcome_probability <= 1.0e-15:
                        continue
                    next_branches.append(
                        (
                            record_bits + tuple(int(bit) for bit in outcome),
                            branch_weight * outcome_probability,
                            projected,
                        )
                    )
            branches = next_branches
            applied.append(
                {
                    **dict(lowered["summary"]),
                    "solver": "qutip.mcsolve",
                    "solver_method": solver_method,
                    "branch_count_after_substep": len(branches),
                }
            )

    probability_by_record: dict[tuple[int, ...], float] = {}
    for record_bits, branch_weight, _branch_state in branches:
        probability_by_record[record_bits] = (
            probability_by_record.get(record_bits, 0.0) + float(branch_weight)
        )
    measurement_records = _measurement_records(len(measurement_keys))
    probabilities = [
        float(probability_by_record.get(tuple(record), 0.0))
        for record in measurement_records
    ]
    detector_records, detector_names = _xor_probe_records(
        measurement_records,
        measurement_keys,
        schedule.record_layout_ref.get("detectors", ()),
    )
    logical_records, logical_names = _xor_probe_records(
        measurement_records,
        measurement_keys,
        schedule.record_layout_ref.get("observables", ()),
    )
    total = float(sum(probabilities))
    record_probe = {
        "initial_state": "computational_zero_ket",
        "solver": "qutip.mcsolve",
        "solver_method": solver_method,
        "solver_methods": solver_methods,
        "final_state_data_type": final_state_type,
        "statevector_payload_serialized": False,
        "measurement_basis": "Z",
        "measurement_keys": measurement_keys,
        "measurement_targets": measurement_targets,
        "measurement_boundaries": measurement_boundaries,
        "measurement_records": measurement_records,
        "record_probabilities": probabilities,
        "record_count": len(measurement_records),
        "total_probability": total,
        "total_probability_residual": abs(total - 1.0),
        "total_probability_residual_threshold": 1.0e-8,
        "applied_substeps": applied,
        "detector_records_emitted": bool(detector_names),
        "detector_names": detector_names,
        "detector_records": detector_records,
        "logical_observables_emitted": bool(logical_names),
        "logical_observable_names": logical_names,
        "logical_observable_records": logical_records,
        "claims_b8_artifact": False,
        "claims_decoder_integration": False,
        "claims_dense_channel_evidence": False,
        "claims_axis2_source_timeline": False,
        "claims_production_scalable_backend": False,
        "epistemic_classes": {
            "trajectory_solver_execution": "c",
            "sequential_measurement_branch_projection": "a/c",
            "detector_logical_xor_projection": "a",
            "b8_non_emission": "a",
            "decoder_non_integration": "a",
            "production_backend_status": "a",
        },
    }
    passed = bool(
        record_probe["total_probability_residual"]
        <= record_probe["total_probability_residual_threshold"]
    )
    payload = {
        **base,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "record_probe_executed": True,
        "blocked_reason": None,
        "blocked_substeps": [],
        "record_probe": record_probe,
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def _state_probe_base_payload(
    schedule: SubstepSchedule,
    program: dict[str, Any],
    device: str,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": AXIS1_QUTIP_CUQUANTUM_STATE_PROBE_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_QUTIP_CUQUANTUM_STATE_PROBE_REPRESENTABILITY,
        "execution_backend_contract": AXIS1_QUTIP_CUQUANTUM_STATE_PROBE_BACKEND_CONTRACT,
        "device": device,
        "gpu_required": True,
        "carrier_program": _program_summary(program),
        "claims_record_execution": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "claims_production_scalable_backend": False,
        "scope": (
            "restricted qutip-cuquantum state probe for carrier-program rows with "
            "no measurement boundary; no record execution, no dense channel evidence, "
            "no production scalable backend claim"
        ),
        "epistemic_classes": {
            "program_consumption": "a/c",
            "restricted_solver_execution": "c",
            "record_non_execution": "a",
            "production_backend_status": "a",
        },
    }
    if "axis1_local_lindblad_context" in program:
        out["axis1_local_lindblad_context"] = program["axis1_local_lindblad_context"]
    return out


def _record_probe_base_payload(
    schedule: SubstepSchedule,
    program: dict[str, Any],
    device: str,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": AXIS1_QUTIP_CUQUANTUM_RECORD_PROBE_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_QUTIP_CUQUANTUM_RECORD_PROBE_REPRESENTABILITY,
        "execution_backend_contract": AXIS1_QUTIP_CUQUANTUM_RECORD_PROBE_BACKEND_CONTRACT,
        "device": device,
        "gpu_required": True,
        "carrier_program": _program_summary(program),
        "claims_b8_artifact": False,
        "claims_decoder_integration": False,
        "claims_dense_channel_evidence": False,
        "claims_axis2_source_timeline": False,
        "claims_production_scalable_backend": False,
        "scope": (
            "restricted qutip-cuquantum trajectory plus Z-record probe for idle, "
            "one-qubit-control, and Z-measurement substeps; no b8 artifact, no DEM, "
            "no decoder, no production scalable backend claim"
        ),
        "epistemic_classes": {
            "program_consumption": "a/c",
            "restricted_trajectory_execution": "c",
            "sequential_measurement_branch_projection": "a/c",
            "b8_non_emission": "a",
            "decoder_non_integration": "a",
            "production_backend_status": "a",
        },
    }
    if "axis1_local_lindblad_context" in program:
        out["axis1_local_lindblad_context"] = program["axis1_local_lindblad_context"]
    return out


def _trajectory_probe_base_payload(
    schedule: SubstepSchedule,
    program: dict[str, Any],
    device: str,
    ntraj: int,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": AXIS1_QUTIP_CUQUANTUM_TRAJECTORY_PROBE_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_QUTIP_CUQUANTUM_TRAJECTORY_PROBE_REPRESENTABILITY,
        "execution_backend_contract": AXIS1_QUTIP_CUQUANTUM_TRAJECTORY_PROBE_BACKEND_CONTRACT,
        "device": device,
        "gpu_required": True,
        "carrier_program": _program_summary(program),
        "ntraj": int(ntraj),
        "claims_record_execution": False,
        "claims_density_state_evidence": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "claims_production_scalable_backend": False,
        "scope": (
            "restricted qutip-cuquantum MCWF trajectory probe for carrier-program "
            "rows with no measurement boundary; no density evidence, no record "
            "execution, no production scalable backend claim"
        ),
        "epistemic_classes": {
            "program_consumption": "a/c",
            "restricted_trajectory_execution": "c",
            "record_non_execution": "a",
            "density_state_non_claim": "a",
            "production_backend_status": "a",
        },
    }
    if "axis1_local_lindblad_context" in program:
        out["axis1_local_lindblad_context"] = program["axis1_local_lindblad_context"]
    return out


def _unsupported_state_probe_substeps(substeps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for substep in substeps:
        if any(str(term["kind"]) == "measurement_boundary" for term in substep.get("terms", ())):
            out.append(
                {
                    "substep_id": str(substep["substep_id"]),
                    "substep_kind": str(substep["substep_kind"]),
                    "reason": "measurement_boundary_not_supported_by_state_probe",
                }
            )
            continue
        if str(substep["substep_kind"]) != "idle":
            out.append(
                {
                    "substep_id": str(substep["substep_id"]),
                    "substep_kind": str(substep["substep_kind"]),
                    "reason": "non_idle_substep_not_supported_by_state_probe",
                }
            )
    if any(item["reason"] == "measurement_boundary_not_supported_by_state_probe" for item in out):
        return [
            item
            for item in out
            if item["reason"] == "measurement_boundary_not_supported_by_state_probe"
        ]
    return out


def _unsupported_record_probe_substeps(
    schedule: SubstepSchedule,
    substeps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    del schedule
    measurement_substeps = [
        substep for substep in substeps if str(substep["substep_kind"]) == "measurement"
    ]
    if not measurement_substeps:
        return [
            {
                "substep_id": "*",
                "substep_kind": "none",
                "reason": "record_probe_requires_at_least_one_measurement_substep",
            }
        ]
    unsupported = [
        {
            "substep_id": str(substep["substep_id"]),
            "substep_kind": str(substep["substep_kind"]),
            "reason": "record_probe_supports_idle_one_qubit_and_measurement_substeps_only",
        }
        for substep in substeps
        if str(substep["substep_kind"]) not in {"idle", "one_qubit_gate", "measurement"}
    ]
    if unsupported:
        return unsupported
    all_keys: list[str] = []
    for substep in measurement_substeps:
        records = list(substep.get("operation_records", ()))
        if len(records) != 1:
            return [
                {
                    "substep_id": str(substep["substep_id"]),
                    "substep_kind": str(substep["substep_kind"]),
                    "reason": "record_probe_supports_one_measurement_operation",
                }
            ]
        op = records[0]
        if str(op.get("basis", "Z")).upper() != "Z":
            return [
                {
                    "substep_id": str(substep["substep_id"]),
                    "substep_kind": str(substep["substep_kind"]),
                    "reason": "record_probe_supports_z_basis_only",
                }
            ]
        targets = [int(q) for q in op.get("targets", ())]
        if not targets:
            return [
                {
                    "substep_id": str(substep["substep_id"]),
                    "substep_kind": str(substep["substep_kind"]),
                    "reason": "record_probe_requires_nonempty_measurement_targets",
                }
            ]
        if len(set(targets)) != len(targets):
            return [
                {
                    "substep_id": str(substep["substep_id"]),
                    "substep_kind": str(substep["substep_kind"]),
                    "reason": "record_probe_measurement_targets_must_be_distinct",
                }
            ]
        keys = [str(key) for key in op.get("measurement_keys", ())]
        if len(keys) != len(targets):
            return [
                {
                    "substep_id": str(substep["substep_id"]),
                    "substep_kind": str(substep["substep_kind"]),
                    "reason": "record_probe_measurement_key_count_mismatch",
                }
            ]
        all_keys.extend(keys)
    if len(set(all_keys)) != len(all_keys):
        return [
            {
                "substep_id": "*",
                "substep_kind": "measurement",
                "reason": "record_probe_measurement_keys_must_be_distinct",
            }
        ]
    return []


def _record_probe_measurement_boundaries(
    substeps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    boundaries: list[dict[str, Any]] = []
    for substep in substeps:
        if str(substep["substep_kind"]) != "measurement":
            continue
        op = dict(substep["operation_records"][0])
        boundaries.append(
            {
                "substep_id": str(substep["substep_id"]),
                "measurement_keys": [str(key) for key in op["measurement_keys"]],
                "measurement_targets": [int(q) for q in op["targets"]],
            }
        )
    if not boundaries:
        raise ValueError("record probe requires at least one measurement substep")
    return boundaries


def _record_probe_boundary_for_substep(
    substep: dict[str, Any],
    boundaries: list[dict[str, Any]],
) -> dict[str, Any]:
    substep_id = str(substep["substep_id"])
    for boundary in boundaries:
        if str(boundary["substep_id"]) == substep_id:
            return boundary
    raise ValueError(f"missing record-probe measurement boundary for {substep_id!r}")


def _lower_substep_for_solver(
    substep: dict[str, Any],
    *,
    qt,
    CuOperator,
    dims: tuple[int, ...],
) -> dict[str, Any]:
    H = _zero_operator_qobj(qt, CuOperator, dims)
    c_ops: list[Any] = []
    h_count = 0
    c_count = 0
    h_families: list[str] = []
    c_families: list[str] = []
    for term in substep.get("terms", ()):
        kind = str(term["kind"])
        if kind == "hamiltonian":
            H = H + _hamiltonian_term_qobj(term, qt=qt, CuOperator=CuOperator, dims=dims)
            h_count += 1
            h_families.append(str(term["operator_family"]))
        elif kind == "collapse":
            c_ops.append(_collapse_term_qobj(term, qt=qt, CuOperator=CuOperator, dims=dims))
            c_count += 1
            c_families.append(str(term["operator_family"]))
        elif kind == "measurement_boundary":
            continue
        else:
            raise ValueError(f"unsupported carrier term kind for state probe: {kind!r}")
    return {
        "hamiltonian": H,
        "collapse_ops": c_ops,
        "summary": {
            "substep_id": str(substep["substep_id"]),
            "substep_kind": str(substep["substep_kind"]),
            "route": str(substep["route"]),
            "route_reason": str(substep["route_reason"]),
            "support": list(substep["support"]),
            "dt_ns": substep["dt_ns"],
            "hamiltonian_term_count": h_count,
            "hamiltonian_operator_families": h_families,
            "collapse_term_count": c_count,
            "collapse_operator_families": c_families,
            "measurement_boundary_count": len(
                [
                    term
                    for term in substep.get("terms", ())
                    if str(term["kind"]) == "measurement_boundary"
                ]
            ),
        },
    }


def _lower_substep(
    substep: dict[str, Any],
    *,
    qt,
    CuOperator,
    dims: tuple[int, ...],
) -> dict[str, Any]:
    h_terms: list[dict[str, Any]] = []
    c_terms: list[dict[str, Any]] = []
    boundaries: list[dict[str, Any]] = []
    H = _zero_operator_qobj(qt, CuOperator, dims)
    for term in substep.get("terms", ()):
        kind = str(term["kind"])
        if kind == "hamiltonian":
            qobj = _hamiltonian_term_qobj(term, qt=qt, CuOperator=CuOperator, dims=dims)
            H = H + qobj
            h_terms.append(_term_summary(term, qobj))
        elif kind == "collapse":
            qobj = _collapse_term_qobj(term, qt=qt, CuOperator=CuOperator, dims=dims)
            c_terms.append(_term_summary(term, qobj))
        elif kind == "measurement_boundary":
            boundaries.append(
                {
                    "kind": kind,
                    "support": list(term["support"]),
                    "operator_family": str(term["operator_family"]),
                    "coefficient": term["coefficient"],
                    "coefficient_source": str(term["coefficient_source"]),
                    "provenance": dict(term.get("provenance", {})),
                    "epistemic_class": str(term.get("epistemic_class", "c")),
                }
            )
        else:
            raise ValueError(f"unsupported carrier term kind for qutip-cuquantum probe: {kind!r}")
    return {
        "substep_id": str(substep["substep_id"]),
        "substep_kind": str(substep["substep_kind"]),
        "route": str(substep["route"]),
        "route_reason": str(substep["route_reason"]),
        "support": list(substep["support"]),
        "hilbert_dims": list(dims),
        "dt_ns": substep["dt_ns"],
        "dt_source": str(substep["dt_source"]),
        "combined_hamiltonian": _operator_summary(H),
        "hamiltonian_terms": h_terms,
        "collapse_terms": c_terms,
        "measurement_boundaries": boundaries,
        "contains_dense_operator_payload": False,
    }


def _hamiltonian_term_qobj(term: dict[str, Any], *, qt, CuOperator, dims: tuple[int, ...]):
    family = str(term["operator_family"]).upper()
    coeff = float(term["coefficient"])
    if family in {"ZZ", "FSIM_PHASE"}:
        support = tuple(int(q) for q in term["support"])
        if len(support) != 2:
            raise ValueError(f"{family} Hamiltonian term requires two-site support")
        return coeff * (
            _local_operator_qobj(_occupation_matrix(), support[0], qt, CuOperator, dims)
            * _local_operator_qobj(_occupation_matrix(), support[1], qt, CuOperator, dims)
        )
    if family.startswith("CTRL_"):
        support = tuple(int(q) for q in term["support"])
        if len(support) != 1:
            raise ValueError(
                f"{family} qutip-cuquantum probe support is currently one-qubit only"
            )
        gate = family.removeprefix("CTRL_")
        matrix = _one_qubit_control_generator_matrix(gate)
        return coeff * _local_operator_qobj(matrix, support[0], qt, CuOperator, dims)
    raise ValueError(f"unsupported qutip-cuquantum Hamiltonian family {family!r}")


def _collapse_term_qobj(term: dict[str, Any], *, qt, CuOperator, dims: tuple[int, ...]):
    family = str(term["operator_family"]).upper()
    coeff = float(term["coefficient"])
    support = tuple(int(q) for q in term["support"])
    if len(support) != 1:
        raise ValueError(f"collapse term {family!r} requires one-site support")
    if family in {"T2", "T2_B", "RD", "RD_B"}:
        matrix = _occupation_matrix()
    elif family in {"T1", "T1_B"}:
        matrix = _sigma_minus_matrix()
    elif family in {"T1_UP", "T1_UP_B"}:
        matrix = _sigma_plus_matrix()
    else:
        raise ValueError(f"unsupported qutip-cuquantum collapse family {family!r}")
    return coeff * _local_operator_qobj(matrix, support[0], qt, CuOperator, dims)


def _local_operator_qobj(matrix, site: int, qt, CuOperator, dims: tuple[int, ...]):
    local = qt.Qobj(np.asarray(matrix, dtype=np.complex128), dims=[[2], [2]])
    data = CuOperator(local.data, mode=int(site), hilbert_dims=tuple(dims))
    return qt.Qobj(data, dims=[list(dims), list(dims)])


def _zero_operator_qobj(qt, CuOperator, dims: tuple[int, ...]):
    return qt.Qobj(CuOperator(hilbert_dims=tuple(dims)), dims=[list(dims), list(dims)])


def _term_summary(term: dict[str, Any], qobj) -> dict[str, Any]:
    out = {
        "kind": str(term["kind"]),
        "support": list(term["support"]),
        "operator_family": str(term["operator_family"]),
        "coefficient": term["coefficient"],
        "coefficient_source": str(term["coefficient_source"]),
        "epistemic_class": str(term.get("epistemic_class", "c")),
    }
    out.update(_operator_summary(qobj))
    return out


def _operator_summary(qobj) -> dict[str, Any]:
    data = qobj.data
    return {
        "data_type": type(data).__name__,
        "shape": [int(x) for x in qobj.shape],
        "term_count": int(len(getattr(data, "terms", ()))),
        "hilbert_dims": [int(x) for x in getattr(data, "hilbert_dims", ())],
    }


def _program_summary(program: dict[str, Any]) -> dict[str, Any]:
    substeps = list(program.get("program", {}).get("substeps", ()))
    return {
        "schema": program.get("schema"),
        "content_hash": program.get("content_hash"),
        "backend_contract": program.get("backend_contract"),
        "requires_scalable_backend": bool(program.get("requires_scalable_backend")),
        "substep_count": len(substeps),
        "routes": sorted({str(step.get("route")) for step in substeps}),
    }


def _qutip_cuquantum_imports():
    try:
        import qutip as qt
        from qutip_cuquantum import CuOperator
    except ImportError as exc:  # pragma: no cover - environment dependent.
        raise RuntimeError(
            "Axis-1 qutip-cuquantum probe requires qutip and qutip_cuquantum"
        ) from exc
    return qt, CuOperator


def _qutip_cuquantum_solver_imports():
    try:
        import qutip as qt
        import qutip_cuquantum
        import cuquantum.densitymat as cudm
        from qutip_cuquantum import CuOperator
    except ImportError as exc:  # pragma: no cover - environment dependent.
        raise RuntimeError(
            "Axis-1 qutip-cuquantum state probe requires qutip_cuquantum and cuquantum.densitymat"
        ) from exc
    return qt, CuOperator, qutip_cuquantum, cudm


def _density_z_probabilities(rho) -> list[float]:
    arr = np.asarray(rho.full(), dtype=np.complex128)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError(f"expected square density matrix, got shape={arr.shape!r}")
    diag = np.array(np.real(np.diag(arr)), copy=True)
    diag[np.abs(diag) < 1.0e-15] = 0.0
    return [float(x) for x in diag.tolist()]


def _single_final_state(final_state):
    if isinstance(final_state, list):
        if len(final_state) != 1:
            raise ValueError(
                f"trajectory probe expected one final state, got {len(final_state)}"
            )
        return final_state[0]
    return final_state


def _ket_z_probabilities(ket) -> list[float]:
    arr = np.asarray(ket.full(), dtype=np.complex128)
    flat = arr.reshape(-1)
    probs = np.array(np.abs(flat) ** 2, dtype=np.float64, copy=True)
    probs[np.abs(probs) < 1.0e-15] = 0.0
    return [float(x) for x in probs.tolist()]


def _measurement_records(num_targets: int) -> list[list[int]]:
    n = int(num_targets)
    return [
        [(index >> bit) & 1 for bit in range(n)]
        for index in range(2**n)
    ]


def _project_z_branch(
    state,
    *,
    outcome_bits: list[int],
    measurement_targets: list[int],
    qt,
    CuOperator,
    dims: tuple[int, ...],
) -> tuple[Any, float]:
    projector = _z_projector_qobj(
        outcome_bits=outcome_bits,
        measurement_targets=measurement_targets,
        qt=qt,
        CuOperator=CuOperator,
        dims=dims,
    )
    projected = projector * state
    norm = float(projected.norm())
    probability = norm * norm
    if probability <= 1.0e-15:
        return projected, 0.0
    return projected / norm, float(probability)


def _z_projector_qobj(
    *,
    outcome_bits: list[int],
    measurement_targets: list[int],
    qt,
    CuOperator,
    dims: tuple[int, ...],
):
    if len(outcome_bits) != len(measurement_targets):
        raise ValueError("Z projector outcome/target length mismatch")
    projector = None
    for bit, target in zip(outcome_bits, measurement_targets, strict=True):
        local = _z_projector_matrix(int(bit))
        local_projector = _local_operator_qobj(
            local,
            int(target),
            qt,
            CuOperator,
            dims,
        )
        projector = local_projector if projector is None else projector * local_projector
    if projector is None:
        raise ValueError("Z projector requires at least one target")
    return projector


def _z_projector_matrix(bit: int) -> np.ndarray:
    if int(bit) == 0:
        return np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)
    if int(bit) == 1:
        return np.array([[0.0, 0.0], [0.0, 1.0]], dtype=np.complex128)
    raise ValueError(f"invalid Z measurement branch bit {bit!r}")


def _xor_probe_records(
    measurement_records: list[list[int]],
    measurement_keys: list[str],
    definitions,
) -> tuple[list[list[int]], list[str]]:
    key_to_index = {str(key): i for i, key in enumerate(measurement_keys)}
    records: list[list[int]] = []
    names: list[str] = []
    for definition in definitions:
        keys = [str(key) for key in definition.get("keys", ())]
        indices = [key_to_index[key] for key in keys]
        names.append(str(definition.get("name", f"xor{len(names)}")))
        records.append(
            [
                sum(row[index] for index in indices) % 2
                for row in measurement_records
            ]
        )
    transposed = [list(row) for row in zip(*records, strict=False)] if records else []
    return transposed, names


def _occupation_matrix() -> np.ndarray:
    return np.array([[0.0, 0.0], [0.0, 1.0]], dtype=np.complex128)


def _sigma_minus_matrix() -> np.ndarray:
    return np.array([[0.0, 1.0], [0.0, 0.0]], dtype=np.complex128)


def _sigma_plus_matrix() -> np.ndarray:
    return np.array([[0.0, 0.0], [1.0, 0.0]], dtype=np.complex128)


def _one_qubit_control_generator_matrix(gate: str) -> np.ndarray:
    U = _one_qubit_control_matrix(str(gate).upper())
    generator, _theta = _su2_axis_angle_generator(U)
    return generator


def _one_qubit_control_matrix(gate: str) -> np.ndarray:
    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    if gate == "H":
        return inv_sqrt2 * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128)
    if gate == "H_XY":
        return np.array([[0.0, 1.0], [1.0j, 0.0]], dtype=np.complex128)
    if gate == "H_XZ":
        return inv_sqrt2 * np.array([[1.0, 1.0], [1.0, -1.0]], dtype=np.complex128)
    if gate == "C_XYZ":
        return inv_sqrt2 * np.array(
            [[1.0, -1.0j], [1.0, 1.0j]],
            dtype=np.complex128,
        )
    if gate == "C_ZYX":
        return inv_sqrt2 * np.array(
            [[1.0, 1.0], [1.0j, -1.0j]],
            dtype=np.complex128,
        )
    if gate == "X":
        return np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    if gate == "Y":
        return np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
    if gate == "Z":
        return np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    if gate == "S":
        return np.array([[1.0, 0.0], [0.0, 1.0j]], dtype=np.complex128)
    if gate == "S_DAG":
        return np.array([[1.0, 0.0], [0.0, -1.0j]], dtype=np.complex128)
    if gate == "SQRT_Z":
        return np.array([[1.0, 0.0], [0.0, 1.0j]], dtype=np.complex128)
    if gate == "SQRT_Z_DAG":
        return np.array([[1.0, 0.0], [0.0, -1.0j]], dtype=np.complex128)
    if gate == "SQRT_X":
        return inv_sqrt2 * np.array(
            [[1.0, -1.0j], [-1.0j, 1.0]],
            dtype=np.complex128,
        )
    if gate == "SQRT_X_DAG":
        return inv_sqrt2 * np.array(
            [[1.0, 1.0j], [1.0j, 1.0]],
            dtype=np.complex128,
        )
    if gate == "SQRT_Y":
        return inv_sqrt2 * np.array(
            [[1.0, -1.0], [1.0, 1.0]],
            dtype=np.complex128,
        )
    if gate == "SQRT_Y_DAG":
        return inv_sqrt2 * np.array(
            [[1.0, 1.0], [-1.0, 1.0]],
            dtype=np.complex128,
        )
    raise ValueError(f"unsupported qutip-cuquantum one-qubit control gate {gate!r}")


def _su2_axis_angle_generator(U: np.ndarray) -> tuple[np.ndarray, float]:
    U = np.asarray(U, dtype=np.complex128)
    det = np.linalg.det(U)
    phase = 0.5 * float(np.angle(det))
    global_phase = complex(math.cos(-phase), math.sin(-phase))
    V = global_phase * U
    cos_theta = float(np.real(np.trace(V)) / 2.0)
    cos_theta = max(-1.0, min(1.0, cos_theta))
    theta = math.acos(cos_theta)
    sin_theta = math.sin(theta)
    if abs(sin_theta) <= 1.0e-12:
        raise ValueError("degenerate one-qubit control has no nontrivial SU(2) axis")
    generator = (V - cos_theta * np.eye(2, dtype=np.complex128)) / (-1j * sin_theta)
    generator = 0.5 * (generator + generator.conj().T)
    return generator, theta


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


__all__ = [
    "AXIS1_QUTIP_CUQUANTUM_PROBE_BACKEND_CONTRACT",
    "AXIS1_QUTIP_CUQUANTUM_PROBE_REPRESENTABILITY",
    "AXIS1_QUTIP_CUQUANTUM_PROBE_SCHEMA",
    "AXIS1_QUTIP_CUQUANTUM_RECORD_PROBE_BACKEND_CONTRACT",
    "AXIS1_QUTIP_CUQUANTUM_RECORD_PROBE_REPRESENTABILITY",
    "AXIS1_QUTIP_CUQUANTUM_RECORD_PROBE_SCHEMA",
    "AXIS1_QUTIP_CUQUANTUM_STATE_PROBE_BACKEND_CONTRACT",
    "AXIS1_QUTIP_CUQUANTUM_STATE_PROBE_REPRESENTABILITY",
    "AXIS1_QUTIP_CUQUANTUM_STATE_PROBE_SCHEMA",
    "AXIS1_QUTIP_CUQUANTUM_TRAJECTORY_PROBE_BACKEND_CONTRACT",
    "AXIS1_QUTIP_CUQUANTUM_TRAJECTORY_PROBE_REPRESENTABILITY",
    "AXIS1_QUTIP_CUQUANTUM_TRAJECTORY_PROBE_SCHEMA",
    "axis1_qutip_cuquantum_probe_manifest",
    "axis1_qutip_cuquantum_record_probe_manifest",
    "axis1_qutip_cuquantum_state_probe_manifest",
    "axis1_qutip_cuquantum_trajectory_probe_manifest",
]
