from __future__ import annotations

"""Executable Axis-1 carrier seam.

This module consumes the schedule-derived :mod:`axis1_carrier_program` IR. The
default backend executes only the dense-checkable route through the existing
joint-L state and record evidence paths. A separate explicit qutip-cuquantum
backend executes the restricted over-cap probe slice. Neither path is the future
production QT/MPS carrier, and no path silently replaces over-cap rows with a
dense channel or pairwise fallback.
"""

import hashlib
import json
from typing import Any

from qec_twin.simulator.analog_schedule import SubstepSchedule
from qec_twin.simulator.axis1_carrier_program import (
    AXIS1_CARRIER_DEFAULT_BACKEND_CONTRACT,
    AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    AXIS1_CARRIER_PROGRAM_SCHEMA,
    axis1_carrier_program_manifest,
)
from qec_twin.simulator.axis1_channel_evidence import (
    _validate_schedule_for_axis1_channel_evidence,
)
from qec_twin.simulator.axis1_record_evidence import (
    Axis1ReadoutResetInstrumentSpec,
    axis1_measurement_record_evidence_manifest,
)
from qec_twin.simulator.axis1_state_evidence import (
    AXIS1_STATE_MAX_EXACT_QUBITS,
    _require_cuda_device,
    axis1_state_evolution_evidence_manifest,
)
from qec_twin.simulator.axis1_qutip_cuquantum_probe import (
    AXIS1_QUTIP_CUQUANTUM_PROBE_BACKEND_CONTRACT,
    axis1_qutip_cuquantum_record_probe_manifest,
    axis1_qutip_cuquantum_trajectory_probe_manifest,
)


AXIS1_CARRIER_EXECUTION_SCHEMA = "qec_twin.simulator.axis1_carrier_execution.v1"
AXIS1_CARRIER_EXECUTION_REPRESENTABILITY = (
    "axis1_carrier_execution_dense_jointL_probe_no_scalable_overcap"
)
AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_REPRESENTABILITY = (
    "axis1_carrier_execution_qutip_cuquantum_restricted_no_production_scalable"
)
AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT = "dense_jointL_probe"
AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_BACKEND_CONTRACT = (
    "qutip_cuquantum_restricted_state_record_probe"
)
AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_REPRESENTABILITY = (
    "axis1_carrier_execution_qt_mps_restricted_no_production_scalable"
)
AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT = (
    AXIS1_CARRIER_DEFAULT_BACKEND_CONTRACT
)
AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY = (
    "axis1_carrier_execution_mcwf_mps_fixed_microstep_or_fail_closed"
)
AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT = (
    AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT
)
AXIS1_CARRIER_MCWF_MPS_CONTRACT_ONLY_REPRESENTABILITY = (
    AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY
)
AXIS1_CARRIER_MCWF_MPS_CONTRACT_ONLY_BACKEND_CONTRACT = (
    AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
)
AXIS1_CARRIER_AUTO_BACKEND_CONTRACT = "auto"
AXIS1_CARRIER_AUTO_EXECUTION_SCHEMA = "qec_twin.simulator.axis1_carrier_auto_routed_execution.v1"
# Conservative fraction of FREE VRAM the dense record probe's PROJECTED PEAK is allowed to occupy
# before the auto-router routes to the memory-bounded MCWF/MPS backend instead. 0.25 matches the
# window_channel register guard (_RHO_MEM_FRACTION) and leaves headroom for allocator fragmentation
# and autograd/transient buffers beyond the projection.
AXIS1_CARRIER_DENSE_VRAM_SAFETY_FRACTION = 0.25
# Transient multiplier on the resident branch-batch peak: the record path builds a torch.stack copy
# of the per-branch results plus per-branch project_qubit intermediates, so the instantaneous peak
# exceeds the resident (2^m, 2^n, 2^n) batch. 2x is a deliberate over-estimate (fails toward MCWF).
AXIS1_CARRIER_DENSE_RECORD_TRANSIENT_FACTOR = 2.0
AXIS1_CARRIER_ALLOWED_EXECUTION_BACKEND_CONTRACTS = frozenset(
    {
        AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT,
        AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
        AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
        AXIS1_CARRIER_AUTO_BACKEND_CONTRACT,
    }
)


def axis1_carrier_execution_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
    instrument_spec: Axis1ReadoutResetInstrumentSpec | None = None,
    execution_backend_contract: str = AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT,
    execution_backend_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute the carrier program where dense joint-L probe execution is valid.

    The default backend is not the scalable QT/MPS backend. It is a GPU-only
    execution seam that proves the carrier program can drive the already
    registered small-window joint-L state/record path, while over-cap rows remain
    explicit blockers unless the restricted qutip-cuquantum backend contract is
    requested.
    """

    backend = str(execution_backend_contract)
    backend_options = dict(execution_backend_options or {})
    if backend not in AXIS1_CARRIER_ALLOWED_EXECUTION_BACKEND_CONTRACTS:
        raise ValueError(f"unsupported Axis-1 carrier execution backend {backend!r}")
    if backend == AXIS1_CARRIER_AUTO_BACKEND_CONTRACT:
        return _axis1_auto_routed_execution_manifest(
            schedule,
            device=device,
            instrument_spec=instrument_spec,
            execution_backend_options=backend_options,
        )
    if backend == AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT:
        return _axis1_qt_mps_restricted_execution_manifest(
            schedule,
            device=device,
            instrument_spec=instrument_spec,
            execution_backend_options=backend_options,
        )
    if backend == AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT:
        return _axis1_mcwf_mps_execution_manifest(
            schedule,
            device=device,
            instrument_spec=instrument_spec,
            execution_backend_options=backend_options,
        )
    if backend_options:
        raise ValueError(
            "execution_backend_options are currently supported only for "
            f"{AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT!r} "
            f"or {AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT!r}"
        )
    if backend == AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_BACKEND_CONTRACT:
        return _axis1_qutip_cuquantum_restricted_execution_manifest(
            schedule,
            device=device,
            instrument_spec=instrument_spec,
        )

    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(schedule)
    program = axis1_carrier_program_manifest(schedule)
    carrier_summary = _carrier_program_summary(program)
    base_payload: dict[str, Any] = {
        "schema": AXIS1_CARRIER_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_CARRIER_EXECUTION_REPRESENTABILITY,
        "execution_backend_contract": AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT,
        "gpu_required": True,
        "device": dev,
        "carrier_program": carrier_summary,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "claims_scalable_backend_completed": False,
        "scored_quantity_policy": (
            "no new scored quantity; nested state/record evidence keeps its existing "
            "METRICS.md references"
        ),
        "epistemic_classes": {
            "program_consumption": "a",
            "dense_jointL_probe_execution": "a/c",
            "overcap_blocker": "a",
            "scalable_backend_status": "a",
        },
    }
    if bool(program["requires_scalable_backend"]):
        payload = {
            **base_payload,
            "verdict": "fail",
            "passed": False,
            "blocked_reason": "requires_scalable_backend_extension",
            "dense_probe_executed": False,
            "state_execution": None,
            "record_execution": None,
            "scope": (
                "carrier program contains scalable_required rows; dense_jointL_probe "
                "will not approximate them with pairwise or sequential composition"
            ),
        }
        payload["content_hash"] = _stable_payload_hash(payload)
        return payload

    if int(schedule.num_qubits) > AXIS1_STATE_MAX_EXACT_QUBITS:
        payload = {
            **base_payload,
            "verdict": "fail",
            "passed": False,
            "blocked_reason": "dense_jointL_probe_qubit_cap_exceeded",
            "dense_probe_executed": False,
            "state_execution": None,
            "record_execution": None,
            "scope": (
                "dense_jointL_probe is exact-density small-N only; connect the "
                "scalable carrier backend before executing this schedule"
            ),
        }
        payload["content_hash"] = _stable_payload_hash(payload)
        return payload

    state = axis1_state_evolution_evidence_manifest(schedule, device=dev)
    record = (
        axis1_measurement_record_evidence_manifest(
            schedule,
            device=dev,
            instrument_spec=instrument_spec,
        )
        if _has_measurement_substep(schedule)
        else None
    )
    state_execution = _state_execution_summary(state)
    record_execution = _record_execution_summary(record)
    passed = bool(state.get("passed")) and (
        record is None or bool(record.get("passed"))
    )
    payload = {
        **base_payload,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "blocked_reason": None,
        "dense_probe_executed": True,
        "state_execution": state_execution,
        "record_execution": record_execution,
        "scope": (
            "dense-checkable carrier execution probe only; no serialized channel "
            "payload, no DEM/decoder semantics, no Axis-2 source timeline, no "
            "scalable QT/MPS backend claim"
        ),
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def _count_measured_qubits(schedule: SubstepSchedule) -> int:
    """Total measured qubits across the schedule — the dense record branch exponent.

    The dense record enumerator holds a BATCH of measurement branches and doubles
    the batch on every measured qubit (``measure_qubit_enumerate`` returns the
    stacked outcome-0/outcome-1 blocks, ``forward/exact/circuit_sim.py``), with no
    pruning in that path. So the resident branch count is ``2 ** (this count)``.
    """

    total = 0
    for substep in schedule.substeps:
        if substep.kind != "measurement":
            continue
        for op in substep.operations:
            total += len(getattr(op, "measurement_keys", ()) or ())
    return total


def _project_dense_record_vram_bytes(schedule: SubstepSchedule) -> float:
    """Project the dense joint-L record-probe PEAK VRAM need (bytes).

    The dense record path does NOT hold a single ``(2**n, 2**n)`` density matrix —
    it holds ``2**m`` of them stacked along a branch axis, where ``m`` is the total
    number of measured qubits (each measurement doubles the resident batch; no
    pruning). The peak is therefore ``2**m * 4**n * 16`` bytes, with a transient
    multiplier for the ``torch.stack`` copy + per-branch projection intermediates.

    Modelling the branch factor is the load-bearing correction: a bare ``4**n``
    projection is a LOWER bound on the real need, and routing-to-dense on a lower
    bound is UNSAFE (it admits dense for schedules whose branch-inflated peak then
    OOMs). This projection is an over-estimate, so it fails TOWARD MCWF.
    """

    n = int(schedule.num_qubits)
    m = _count_measured_qubits(schedule)
    return (
        AXIS1_CARRIER_DENSE_RECORD_TRANSIENT_FACTOR
        * (2.0**m)
        * (4.0**n)
        * 16.0
    )


def _available_vram_bytes(device: str) -> float:
    """Free VRAM (bytes) on the CUDA device, via the same probe window_channel uses."""

    import torch

    free_bytes, _total = torch.cuda.mem_get_info(device)
    return float(free_bytes)


def _select_dense_or_mcwf(
    schedule: SubstepSchedule,
    device: str,
    program: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Route dense vs MCWF: dense only if it fits VRAM AND is under the structural caps.

    The VRAM trigger is the user-requested rule — if the projected dense need
    exceeds the safety fraction of currently-free VRAM, route to MCWF. The qubit
    cap and ``requires_scalable_backend`` are kept as additional structural
    backstops, all of which fail TOWARD the memory-bounded backend (anti-OOM).
    """

    n = int(schedule.num_qubits)
    measured_qubits = _count_measured_qubits(schedule)
    projected = _project_dense_record_vram_bytes(schedule)
    free = _available_vram_bytes(device)
    budget = AXIS1_CARRIER_DENSE_VRAM_SAFETY_FRACTION * free
    requires_scalable = bool(program.get("requires_scalable_backend"))
    over_qubit_cap = n > AXIS1_STATE_MAX_EXACT_QUBITS
    over_vram = projected > budget
    use_dense = (not requires_scalable) and (not over_qubit_cap) and (not over_vram)
    chosen = (
        AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT
        if use_dense
        else AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    )
    reasons: list[str] = []
    if requires_scalable:
        reasons.append("requires_scalable_backend")
    if over_qubit_cap:
        reasons.append(f"num_qubits>{AXIS1_STATE_MAX_EXACT_QUBITS}")
    if over_vram:
        reasons.append("projected_dense_vram_exceeds_safety_budget")
    decision = {
        "schema": "qec_twin.simulator.axis1_carrier_auto_routing_decision.v2",
        "num_qubits": n,
        "measured_qubits": measured_qubits,
        "branch_factor_log2": measured_qubits,
        "dense_record_transient_factor": AXIS1_CARRIER_DENSE_RECORD_TRANSIENT_FACTOR,
        "projected_dense_vram_bytes": projected,
        "projected_dense_vram_gib": projected / (1024.0**3),
        "free_vram_bytes": free,
        "free_vram_gib": free / (1024.0**3),
        "safety_fraction": AXIS1_CARRIER_DENSE_VRAM_SAFETY_FRACTION,
        "dense_vram_budget_bytes": budget,
        "dense_vram_budget_gib": budget / (1024.0**3),
        "requires_scalable_backend": requires_scalable,
        "over_qubit_cap": over_qubit_cap,
        "over_vram_budget": over_vram,
        "use_dense": use_dense,
        "resolved_backend_contract": chosen,
        "route_reasons": reasons if reasons else ["dense_fits_vram_and_under_caps"],
        "projection_semantics": (
            "dense record peak = transient_factor * 2^(measured_qubits) * (2^n,2^n) "
            "complex128 * 16 bytes; the 2^(measured_qubits) branch batch is the "
            "load-bearing term and this projection over-estimates it, so routing "
            "fails TOWARD the memory-bounded MCWF backend"
        ),
    }
    return chosen, decision


def _axis1_auto_routed_execution_manifest(
    schedule: SubstepSchedule,
    *,
    device: str,
    instrument_spec: Axis1ReadoutResetInstrumentSpec | None,
    execution_backend_options: dict[str, Any] | None,
) -> dict[str, Any]:
    """VRAM-aware auto-router: pick dense vs MCWF, delegate, wrap with the decision.

    On over-cap / over-VRAM it routes to the memory-bounded MCWF/MPS backend
    instead of failing closed. Two caller inputs are incompatible with that
    routing and are rejected UP FRONT with a clear message rather than failing
    deep inside the chosen backend: (1) an ``instrument_spec`` (readout/reset
    noise) is dense-only — MCWF does not implement it; (2) MCWF-tuning
    ``execution_backend_options`` are meaningless for the dense backend (which
    rejects any options), so they are forwarded ONLY when MCWF is chosen.
    """

    dev = _require_cuda_device(device)
    program = axis1_carrier_program_manifest(schedule)
    chosen, decision = _select_dense_or_mcwf(schedule, dev, program)
    options = dict(execution_backend_options or {})
    routes_to_mcwf = chosen == AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    if routes_to_mcwf and instrument_spec is not None:
        raise ValueError(
            "auto routing selected the MCWF/MPS backend "
            f"(reasons={decision['route_reasons']}) but an Axis1ReadoutResetInstrumentSpec "
            "was supplied; the readout/reset instrument is dense-only. Request "
            f"{AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT!r} explicitly for the small-N "
            "instrument path, or drop the instrument_spec for the scalable backend."
        )
    if options and not routes_to_mcwf:
        raise ValueError(
            "auto routing selected the dense backend "
            f"(reasons={decision['route_reasons']}) but execution_backend_options "
            f"{sorted(options)} were supplied; those tune the MCWF/MPS backend and the "
            "dense probe accepts none. Drop the options, or force the scalable backend."
        )
    inner = axis1_carrier_execution_manifest(
        schedule,
        device=dev,
        instrument_spec=instrument_spec,
        execution_backend_contract=chosen,
        execution_backend_options=options if routes_to_mcwf else None,
    )
    payload: dict[str, Any] = {
        "schema": AXIS1_CARRIER_AUTO_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "gpu_required": True,
        "device": dev,
        "requested_backend_contract": AXIS1_CARRIER_AUTO_BACKEND_CONTRACT,
        "resolved_backend_contract": chosen,
        "auto_routing": decision,
        "verdict": inner.get("verdict"),
        "passed": bool(inner.get("passed")),
        "blocked_reason": inner.get("blocked_reason"),
        "execution": inner,
        "scored_quantity_policy": (
            "VRAM-aware backend router; no new scored quantity; the delegated "
            "backend keeps its own representability and evidence"
        ),
        "claims_dense_channel_evidence": False,
        "claims_axis2_source_timeline": False,
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def _axis1_mcwf_mps_execution_manifest(
    schedule: SubstepSchedule,
    *,
    device: str,
    instrument_spec: Axis1ReadoutResetInstrumentSpec | None,
    execution_backend_options: dict[str, Any] | None,
) -> dict[str, Any]:
    """Execute or fail closed through the MCWF/MPS carrier endpoint."""

    if instrument_spec is not None:
        raise ValueError(
            "MCWF/MPS carrier execution does not support "
            "Axis1ReadoutResetInstrumentSpec in the first slice"
        )
    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(
        schedule,
        allow_multilevel_leakage_context=True,
    )
    options = _validate_mcwf_mps_contract_options(execution_backend_options or {})
    from qec_twin.simulator.axis1_mcwf_mps_execution import (
        axis1_mcwf_mps_state_record_execution_manifest,
    )

    mcwf_mps = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        device=dev,
        **options,
    )
    execution = mcwf_mps.get("mps_execution") or {}
    passed = bool(mcwf_mps.get("passed", False))
    executed = bool(mcwf_mps.get("mcwf_mps_backend_executed", False))
    record_executed = bool(executed and execution.get("measurement_keys"))
    payload: dict[str, Any] = {
        "schema": AXIS1_CARRIER_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY,
        "execution_backend_contract": (
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
        ),
        "gpu_required": True,
        "device": dev,
        "execution_backend_options": _jsonable(options),
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "blocked_reason": mcwf_mps.get("blocked_reason"),
        "contract_surface_valid": bool(
            mcwf_mps.get("mcwf_mps_contract", {}).get("contract_valid", False)
        ),
        "dense_probe_executed": False,
        "qt_mps_backend_executed": False,
        "mcwf_mps_backend_executed": executed,
        "qutip_cuquantum_probe_executed": False,
        "carrier_program": dict(mcwf_mps["carrier_program"]),
        "mcwf_mps_contract": {
            **dict(mcwf_mps.get("mcwf_mps_contract", {})),
            "local_hilbert_space": dict(mcwf_mps.get("local_hilbert_space", {})),
        },
        "state_execution": {
            "executed": executed,
            "reason": None if executed else mcwf_mps.get("blocked_reason"),
            "evidence_schema": mcwf_mps.get("schema"),
            "evidence_content_hash": mcwf_mps.get("content_hash"),
            "representability": mcwf_mps.get("representability"),
            "mps_library": execution.get("mps_library"),
            "array_backend": execution.get("array_backend"),
            "unraveling_policy": execution.get("unraveling_policy"),
            "finite_step_policy": dict(execution.get("finite_step_policy", {})),
            "mps_truncation_ledger": dict(execution.get("mps_truncation_ledger", {})),
        },
        "record_execution": {
            "executed": record_executed,
            "reason": (
                None
                if record_executed
                else (
                    mcwf_mps.get("blocked_reason")
                    if not executed
                    else "schedule_has_no_measurement_substep"
                )
            ),
            "measurement_keys": list(execution.get("measurement_keys", ())),
            "measurement_records": list(execution.get("measurement_records", ())),
            "record_counts": list(execution.get("record_counts", ())),
            "record_probabilities": list(execution.get("record_probabilities", ())),
            "detector_records": list(execution.get("detector_records", ())),
            "logical_observable_records": list(
                execution.get("logical_observable_records", ())
            ),
            "trajectory_sampling": dict(execution.get("trajectory_sampling", {})),
            "jump_sampling": dict(execution.get("jump_sampling", {})),
            "claims_b8_artifact": bool(execution.get("claims_b8_artifact", False)),
            "claims_decoder_integration": bool(
                execution.get("claims_decoder_integration", False)
            ),
        },
        "mcwf_mps_execution": {
            "schema": mcwf_mps.get("schema"),
            "content_hash": mcwf_mps.get("content_hash"),
            "representability": mcwf_mps.get("representability"),
            "backend_contract": mcwf_mps.get("backend_contract"),
            "passed": bool(mcwf_mps.get("passed", False)),
            "mcwf_mps_backend_executed": executed,
            "claims_exact_joint_lindblad_generator": bool(
                mcwf_mps.get("claims_exact_joint_lindblad_generator", False)
            ),
            "claims_dense_channel_evidence": bool(
                mcwf_mps.get("claims_dense_channel_evidence", False)
            ),
            "claims_production_scalable_backend": bool(
                mcwf_mps.get("claims_production_scalable_backend", False)
            ),
        },
        "restricted_acceptance_policy": dict(
            mcwf_mps.get("restricted_acceptance_policy", {})
        ),
        "claims_mcwf_mps_backend_execution": executed,
        "claims_qt_mps_backend_execution": False,
        "claims_qutip_cuquantum_execution": False,
        "claims_production_scalable_backend": False,
        "claims_scalable_backend_completed": False,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "scored_quantity_policy": (
            "MCWF/MPS execution/fail-closed carrier wrapper; no new scored quantity"
        ),
        "epistemic_classes": {
            "program_consumption": "a",
            "mcwf_mps_contract_surface": "a/c",
            "backend_execution_status": "a",
            "production_backend_status": "a",
            "dem_decoder_non_claim": "a",
        },
        "scope": (
            "Axis-1 carrier execution endpoint for the MCWF/MPS backend; first "
            "slice executes fixed-microstep MCWF/MPS with declared local_dims "
            "and fails closed for multilevel finite-bond ledgers, with no dense "
            "fallback, no DEM/decoder semantics, and no Axis-2 source timeline"
        ),
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def _axis1_qt_mps_restricted_execution_manifest(
    schedule: SubstepSchedule,
    *,
    device: str,
    instrument_spec: Axis1ReadoutResetInstrumentSpec | None,
    execution_backend_options: dict[str, Any] | None,
) -> dict[str, Any]:
    """Execute the restricted QT/MPS carrier backend through the carrier seam."""

    if instrument_spec is not None:
        raise ValueError(
            "QT/MPS restricted carrier execution does not support "
            "Axis1ReadoutResetInstrumentSpec; use dense_jointL_probe for the "
            "small-N instrument path"
        )
    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(schedule)
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
    )
    carrier_summary = _carrier_program_summary(program)
    qt_mps_options = _validate_qt_mps_backend_options(execution_backend_options or {})
    from qec_twin.simulator.axis1_qt_mps_execution import (
        axis1_qt_mps_restricted_execution_manifest,
    )

    qt_mps = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        device=dev,
        **qt_mps_options,
    )
    passed = bool(qt_mps.get("passed"))
    payload: dict[str, Any] = {
        "schema": AXIS1_CARRIER_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_REPRESENTABILITY,
        "execution_backend_contract": (
            AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT
        ),
        "gpu_required": True,
        "device": dev,
        "carrier_program": carrier_summary,
        "execution_backend_options": _jsonable(qt_mps_options),
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "blocked_reason": qt_mps.get("blocked_reason"),
        "dense_probe_executed": bool(
            qt_mps.get("dense_jointL_record_certification", {}).get("executed", False)
        ),
        "qt_mps_backend_executed": bool(qt_mps.get("qt_mps_backend_executed", False)),
        "qutip_cuquantum_probe_executed": False,
        "state_execution": _qt_mps_state_execution_summary(qt_mps),
        "record_execution": _qt_mps_record_execution_summary(qt_mps),
        "qt_mps_execution": _qt_mps_execution_summary(qt_mps),
        "dense_jointL_record_certification": dict(
            qt_mps.get("dense_jointL_record_certification", {})
        ),
        "restricted_acceptance_policy": dict(
            qt_mps.get("restricted_acceptance_policy", {})
        ),
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "claims_scalable_backend_completed": False,
        "claims_production_scalable_backend": False,
        "claims_qt_mps_backend_execution": True,
        "claims_qutip_cuquantum_execution": False,
        "claims_exact_joint_lindblad_generator": False,
        "scored_quantity_policy": (
            "restricted QT/MPS carrier execution is a verification gate only; "
            "no new scored quantity"
        ),
        "epistemic_classes": {
            "program_consumption": "a",
            "restricted_qt_mps_execution": "c",
            "dense_oracle_certification": "a/c",
            "production_backend_status": "a",
            "dem_decoder_non_claim": "a",
        },
        "scope": (
            "restricted QT/MPS state/record execution through the carrier seam; "
            "no dense channel payload, no DEM/decoder semantics, no Axis-2 source "
            "timeline, no exact joint-Lindblad generator claim, no production "
            "scalable backend claim"
        ),
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def _validate_mcwf_mps_contract_options(options: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "finite_step_order",
        "initial_levels",
        "leaked_readout_b",
        "local_dims",
        "max_bond",
        "microstep_count",
        "rng_seed",
        "trajectory_count",
    }
    unknown = sorted(set(options) - allowed)
    if unknown:
        joined = ", ".join(unknown)
        raise ValueError(f"unsupported MCWF/MPS contract options: {joined}")
    out = dict(options)
    if "local_dims" in out and out["local_dims"] is not None:
        out["local_dims"] = [int(dim) for dim in out["local_dims"]]
    if "initial_levels" in out and out["initial_levels"] is not None:
        out["initial_levels"] = [int(level) for level in out["initial_levels"]]
    if "leaked_readout_b" in out:
        out["leaked_readout_b"] = float(out["leaked_readout_b"])
    if "max_bond" in out and out["max_bond"] is not None:
        out["max_bond"] = int(out["max_bond"])
    if "microstep_count" in out:
        out["microstep_count"] = int(out["microstep_count"])
    if "trajectory_count" in out:
        out["trajectory_count"] = int(out["trajectory_count"])
    if "rng_seed" in out and out["rng_seed"] is not None:
        out["rng_seed"] = int(out["rng_seed"])
    return out


def _validate_qt_mps_backend_options(options: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "max_bond",
        "max_branches",
        "microstep_count",
        "finite_step_order",
        "worst_cut_discarded_weight_gate",
        "total_discarded_weight_gate",
        "trajectory_count",
        "rng_seed",
        "dense_oracle_certification",
    }
    unknown = sorted(set(options) - allowed)
    if unknown:
        joined = ", ".join(unknown)
        raise ValueError(f"unsupported QT/MPS execution_backend_options: {joined}")
    return dict(options)


def _axis1_qutip_cuquantum_restricted_execution_manifest(
    schedule: SubstepSchedule,
    *,
    device: str,
    instrument_spec: Axis1ReadoutResetInstrumentSpec | None,
) -> dict[str, Any]:
    """Execute the restricted qutip-cuquantum carrier-probe backend.

    This backend is an executable over-cap adapter, not the production QT/MPS
    carrier. It delegates to the qutip-cuquantum trajectory or record probes and
    keeps their representability boundaries intact.
    """

    if instrument_spec is not None:
        raise ValueError(
            "qutip-cuquantum restricted carrier execution does not support "
            "Axis1ReadoutResetInstrumentSpec; use dense_jointL_probe for the "
            "small-N instrument path"
        )
    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(schedule)
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_QUTIP_CUQUANTUM_PROBE_BACKEND_CONTRACT,
    )
    carrier_summary = _carrier_program_summary(program)
    base_payload: dict[str, Any] = {
        "schema": AXIS1_CARRIER_EXECUTION_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_REPRESENTABILITY,
        "execution_backend_contract": (
            AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_BACKEND_CONTRACT
        ),
        "gpu_required": True,
        "device": dev,
        "carrier_program": carrier_summary,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "claims_scalable_backend_completed": False,
        "claims_production_scalable_backend": False,
        "claims_qt_mps_backend_execution": False,
        "claims_qutip_cuquantum_execution": True,
        "scored_quantity_policy": (
            "restricted qutip-cuquantum execution is a verification gate only; "
            "no new scored quantity"
        ),
        "epistemic_classes": {
            "program_consumption": "a",
            "restricted_qutip_execution": "c",
            "production_backend_status": "a",
            "dem_decoder_non_claim": "a",
        },
    }
    if _has_measurement_substep(schedule):
        record = axis1_qutip_cuquantum_record_probe_manifest(schedule, device=dev)
        passed = bool(record.get("passed"))
        payload = {
            **base_payload,
            "verdict": "pass" if passed else "fail",
            "passed": passed,
            "blocked_reason": record.get("blocked_reason"),
            "dense_probe_executed": False,
            "qutip_cuquantum_probe_executed": bool(record.get("record_probe_executed")),
            "state_execution": {
                "executed": False,
                "reason": "record_probe_executes_trajectory_branches_not_density_state",
            },
            "record_execution": _qutip_record_execution_summary(record),
            "qutip_probe": {
                "schema": record.get("schema"),
                "content_hash": record.get("content_hash"),
                "representability": record.get("representability"),
                "execution_backend_contract": record.get("execution_backend_contract"),
                "passed": bool(record.get("passed")),
            },
            "scope": (
                "restricted qutip-cuquantum state/record execution probe; no QT/MPS "
                "backend execution, no dense channel payload, no DEM/decoder "
                "semantics, no Axis-2 source timeline, no production scalable "
                "backend claim"
            ),
        }
        payload["content_hash"] = _stable_payload_hash(payload)
        return payload

    trajectory = axis1_qutip_cuquantum_trajectory_probe_manifest(schedule, device=dev)
    passed = bool(trajectory.get("passed"))
    payload = {
        **base_payload,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "blocked_reason": trajectory.get("blocked_reason"),
        "dense_probe_executed": False,
        "qutip_cuquantum_probe_executed": bool(
            trajectory.get("trajectory_probe_executed")
        ),
        "state_execution": _qutip_trajectory_execution_summary(trajectory),
        "record_execution": {
            "executed": False,
            "reason": "schedule_has_no_measurement_substep",
        },
        "qutip_probe": {
            "schema": trajectory.get("schema"),
            "content_hash": trajectory.get("content_hash"),
            "representability": trajectory.get("representability"),
            "execution_backend_contract": trajectory.get("execution_backend_contract"),
            "passed": bool(trajectory.get("passed")),
        },
        "scope": (
            "restricted qutip-cuquantum state/record execution probe; no QT/MPS "
            "backend execution, no dense channel payload, no DEM/decoder semantics, "
            "no Axis-2 source timeline, no production scalable backend claim"
        ),
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def _carrier_program_summary(program: dict[str, Any]) -> dict[str, Any]:
    if program.get("schema") != AXIS1_CARRIER_PROGRAM_SCHEMA:
        raise ValueError(
            "Axis-1 carrier execution requires an Axis1CarrierProgram manifest; "
            f"got schema={program.get('schema')!r}"
        )
    substeps = list(program.get("program", {}).get("substeps", ()))
    routes = sorted({str(step.get("route")) for step in substeps})
    return {
        "schema": program.get("schema"),
        "content_hash": program.get("content_hash"),
        "backend_contract": program.get("backend_contract"),
        "requires_scalable_backend": bool(program.get("requires_scalable_backend")),
        "substep_count": len(substeps),
        "routes": routes,
        "route_reasons": sorted({str(step.get("route_reason")) for step in substeps}),
        "claims_dense_channel_evidence": bool(
            program.get("claims_dense_channel_evidence")
        ),
        "claims_dem_decoder_semantics": bool(
            program.get("claims_dem_decoder_semantics")
        ),
        "claims_axis2_source_timeline": bool(
            program.get("claims_axis2_source_timeline")
        ),
    }


def _qt_mps_execution_summary(qt_mps: dict[str, Any]) -> dict[str, Any]:
    acceptance = qt_mps.get("restricted_acceptance_policy", {})
    certification = qt_mps.get("dense_jointL_record_certification", {})
    return {
        "schema": qt_mps.get("schema"),
        "content_hash": qt_mps.get("content_hash"),
        "representability": qt_mps.get("representability"),
        "backend_contract": qt_mps.get("backend_contract"),
        "passed": bool(qt_mps.get("passed", False)),
        "qt_mps_backend_executed": bool(qt_mps.get("qt_mps_backend_executed", False)),
        "accepted_for_restricted_execution": bool(
            acceptance.get("accepted_for_restricted_execution", False)
        ),
        "accepted_for_production_scalable_backend": bool(
            acceptance.get("accepted_for_production_scalable_backend", False)
        ),
        "dense_jointL_record_certification_status": (
            "passed"
            if bool(certification.get("executed", False))
            and bool(certification.get("passed", False))
            else certification.get("reason", "not_executed")
        ),
        "claims_exact_joint_lindblad_generator": bool(
            qt_mps.get("claims_exact_joint_lindblad_generator", False)
        ),
        "claims_dense_channel_evidence": bool(
            qt_mps.get("claims_dense_channel_evidence", False)
        ),
        "claims_dem_decoder_semantics": bool(
            qt_mps.get("claims_dem_decoder_semantics", False)
        ),
        "claims_axis2_source_timeline": bool(
            qt_mps.get("claims_axis2_source_timeline", False)
        ),
        "claims_production_scalable_backend": bool(
            qt_mps.get("claims_production_scalable_backend", False)
        ),
    }


def _qt_mps_state_execution_summary(qt_mps: dict[str, Any]) -> dict[str, Any]:
    execution = qt_mps.get("mps_execution")
    if not execution:
        return {
            "executed": False,
            "passed": bool(qt_mps.get("passed", False)),
            "blocked_reason": qt_mps.get("blocked_reason"),
            "blocked_substeps": list(qt_mps.get("blocked_substeps", ())),
        }
    return {
        "executed": True,
        "evidence_schema": qt_mps["schema"],
        "evidence_content_hash": qt_mps["content_hash"],
        "representability": qt_mps["representability"],
        "passed": bool(qt_mps["passed"]),
        "mps_library": execution["mps_library"],
        "array_backend": execution["array_backend"],
        "finite_step_policy": dict(execution["finite_step_policy"]),
        "mps_truncation_ledger": dict(execution["mps_truncation_ledger"]),
        "applied_substeps": list(execution["applied_substeps"]),
        "total_probability_residual": float(execution["total_probability_residual"]),
        "claims_density_state_evidence": False,
        "claims_exact_joint_lindblad_generator": False,
    }


def _qt_mps_record_execution_summary(qt_mps: dict[str, Any]) -> dict[str, Any]:
    execution = qt_mps.get("mps_execution")
    if not execution:
        return {
            "executed": False,
            "passed": bool(qt_mps.get("passed", False)),
            "blocked_reason": qt_mps.get("blocked_reason"),
            "blocked_substeps": list(qt_mps.get("blocked_substeps", ())),
        }
    return {
        "executed": True,
        "evidence_schema": qt_mps["schema"],
        "evidence_content_hash": qt_mps["content_hash"],
        "representability": qt_mps["representability"],
        "passed": bool(qt_mps["passed"]),
        "measurement_keys": list(execution["measurement_keys"]),
        "measurement_records": list(execution["measurement_records"]),
        "record_probabilities": list(execution["record_probabilities"]),
        "detector_records": list(execution["detector_records"]),
        "logical_observable_records": list(execution["logical_observable_records"]),
        "total_probability": float(execution["total_probability"]),
        "total_probability_residual": float(execution["total_probability_residual"]),
        "trajectory_sampling": dict(execution["trajectory_sampling"]),
        "claims_b8_artifact": bool(execution["claims_b8_artifact"]),
        "claims_decoder_integration": bool(execution["claims_decoder_integration"]),
        "claims_dense_channel_evidence": bool(
            qt_mps.get("claims_dense_channel_evidence", False)
        ),
        "claims_axis2_source_timeline": bool(
            qt_mps.get("claims_axis2_source_timeline", False)
        ),
        "claims_production_scalable_backend": bool(
            qt_mps.get("claims_production_scalable_backend", False)
        ),
    }


def _state_execution_summary(state: dict[str, Any]) -> dict[str, Any]:
    evolution = state["state_evolution"]
    return {
        "executed": True,
        "evidence_schema": state["schema"],
        "evidence_content_hash": state["content_hash"],
        "representability": state["representability"],
        "passed": bool(state["passed"]),
        "applied_channel_count": int(evolution["applied_channel_count"]),
        "final_trace": float(evolution["final_trace"]),
        "trace_residual": float(evolution["trace_residual"]),
        "final_z_probabilities": list(evolution["final_z_probabilities"]),
        "joint_generator_semantics": "single_joint_generator_expm",
        "claims_record_emission": bool(evolution["claims_record_emission"]),
        "claims_axis2_source_projection": bool(
            evolution["claims_axis2_source_projection"]
        ),
    }


def _record_execution_summary(record: dict[str, Any] | None) -> dict[str, Any]:
    if record is None:
        return {
            "executed": False,
            "reason": "schedule_has_no_measurement_substep",
        }
    evidence = record["record_evidence"]
    return {
        "executed": True,
        "evidence_schema": record["schema"],
        "evidence_content_hash": record["content_hash"],
        "representability": record["representability"],
        "passed": bool(record["passed"]),
        "applied_channel_count": int(evidence["applied_channel_count"]),
        "measurement_keys": list(evidence["measurement_keys"]),
        "measurement_records": list(evidence["measurement_records"]),
        "record_probabilities": list(evidence["record_probabilities"]),
        "detector_records": list(evidence["detector_records"]),
        "logical_observable_records": list(evidence["logical_observable_records"]),
        "total_probability": float(evidence["total_probability"]),
        "total_probability_residual": float(evidence["total_probability_residual"]),
        "joint_generator_semantics": "single_joint_generator_expm",
        "claims_b8_artifact": bool(evidence["claims_b8_artifact"]),
        "claims_decoder_integration": bool(evidence["claims_decoder_integration"]),
        "claims_axis2_source_projection": bool(
            evidence["claims_axis2_source_projection"]
        ),
    }


def _qutip_trajectory_execution_summary(trajectory: dict[str, Any]) -> dict[str, Any]:
    probe = trajectory.get("trajectory_probe")
    if not probe:
        return {
            "executed": False,
            "passed": bool(trajectory.get("passed")),
            "blocked_reason": trajectory.get("blocked_reason"),
            "blocked_substeps": list(trajectory.get("blocked_substeps", ())),
        }
    return {
        "executed": True,
        "evidence_schema": trajectory["schema"],
        "evidence_content_hash": trajectory["content_hash"],
        "representability": trajectory["representability"],
        "passed": bool(trajectory["passed"]),
        "solver": probe["solver"],
        "solver_methods": list(probe["solver_methods"]),
        "ntraj": int(probe["ntraj"]),
        "final_z_probabilities": list(probe["final_z_probabilities"]),
        "final_norm": float(probe["final_norm"]),
        "norm_residual": float(probe["norm_residual"]),
        "applied_substeps": list(probe["applied_substeps"]),
        "statevector_payload_serialized": bool(
            probe["statevector_payload_serialized"]
        ),
        "claims_record_execution": False,
        "claims_density_state_evidence": False,
    }


def _qutip_record_execution_summary(record: dict[str, Any]) -> dict[str, Any]:
    probe = record.get("record_probe")
    if not probe:
        return {
            "executed": False,
            "passed": bool(record.get("passed")),
            "blocked_reason": record.get("blocked_reason"),
            "blocked_substeps": list(record.get("blocked_substeps", ())),
        }
    return {
        "executed": True,
        "evidence_schema": record["schema"],
        "evidence_content_hash": record["content_hash"],
        "representability": record["representability"],
        "passed": bool(record["passed"]),
        "solver": probe["solver"],
        "solver_methods": list(probe["solver_methods"]),
        "measurement_keys": list(probe["measurement_keys"]),
        "measurement_records": list(probe["measurement_records"]),
        "record_probabilities": list(probe["record_probabilities"]),
        "detector_records": list(probe["detector_records"]),
        "logical_observable_records": list(probe["logical_observable_records"]),
        "total_probability": float(probe["total_probability"]),
        "total_probability_residual": float(
            probe["total_probability_residual"]
        ),
        "applied_substeps": list(probe["applied_substeps"]),
        "claims_b8_artifact": bool(probe["claims_b8_artifact"]),
        "claims_decoder_integration": bool(probe["claims_decoder_integration"]),
        "claims_dense_channel_evidence": bool(
            probe["claims_dense_channel_evidence"]
        ),
        "claims_axis2_source_timeline": bool(
            probe["claims_axis2_source_timeline"]
        ),
        "claims_production_scalable_backend": bool(
            probe["claims_production_scalable_backend"]
        ),
    }


def _has_measurement_substep(schedule: SubstepSchedule) -> bool:
    return any(substep.kind == "measurement" for substep in schedule.substeps)


def _jsonable(value: Any) -> Any:
    return json.loads(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
    )


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
    "AXIS1_CARRIER_ALLOWED_EXECUTION_BACKEND_CONTRACTS",
    "AXIS1_CARRIER_AUTO_BACKEND_CONTRACT",
    "AXIS1_CARRIER_AUTO_EXECUTION_SCHEMA",
    "AXIS1_CARRIER_DENSE_RECORD_TRANSIENT_FACTOR",
    "AXIS1_CARRIER_DENSE_VRAM_SAFETY_FRACTION",
    "AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT",
    "AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT",
    "AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY",
    "AXIS1_CARRIER_MCWF_MPS_CONTRACT_ONLY_BACKEND_CONTRACT",
    "AXIS1_CARRIER_MCWF_MPS_CONTRACT_ONLY_REPRESENTABILITY",
    "AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_BACKEND_CONTRACT",
    "AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_REPRESENTABILITY",
    "AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT",
    "AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_REPRESENTABILITY",
    "AXIS1_CARRIER_EXECUTION_REPRESENTABILITY",
    "AXIS1_CARRIER_EXECUTION_SCHEMA",
    "axis1_carrier_execution_manifest",
]
