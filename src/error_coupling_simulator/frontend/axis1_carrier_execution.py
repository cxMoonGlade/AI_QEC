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
import math
from numbers import Real
from typing import Any

from ..carrier.mps.controls import (
    normalize_mps_bool,
    normalize_mps_choice,
    normalize_mps_device,
    normalize_mps_finite_real,
    normalize_mps_index,
    normalize_mps_index_sequence,
    normalize_mps_max_bond,
    normalize_optional_mps_index,
)
from .analog_schedule import SubstepSchedule
from .axis1_carrier_program import (
    AXIS1_CARRIER_DEFAULT_BACKEND_CONTRACT,
    AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    AXIS1_CARRIER_PROGRAM_SCHEMA,
    axis1_carrier_program_manifest,
)
from .axis1_channel_evidence import (
    _validate_schedule_for_axis1_channel_evidence,
)
from .axis1_record_evidence import (
    Axis1ReadoutResetInstrumentSpec,
    axis1_measurement_record_evidence_manifest,
)
from .axis1_record_layout import (
    _validate_axis1_projected_record_payload,
    axis1_record_layout_from_schedule,
)
from .axis1_state_evidence import (
    AXIS1_STATE_MAX_EXACT_QUBITS,
    _require_cuda_device,
    axis1_state_evolution_evidence_manifest,
)
from .axis1_qutip_cuquantum_probe import (
    AXIS1_QUTIP_CUQUANTUM_PROBE_BACKEND_CONTRACT,
    axis1_qutip_cuquantum_record_probe_manifest,
    axis1_qutip_cuquantum_trajectory_probe_manifest,
)


AXIS1_CARRIER_EXECUTION_SCHEMA = "error_coupling_simulator.frontend.carrier_execution.v3"
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
AXIS1_CARRIER_AUTO_BACKEND_CONTRACT = "auto"
AXIS1_CARRIER_AUTO_EXECUTION_SCHEMA = (
    "error_coupling_simulator.frontend.carrier_auto_routed_execution.v3"
)
_RESTRICTED_POLICY_SCHEMAS = {
    "mcwf": (
        "error_coupling_simulator.frontend."
        "mcwf_mps_restricted_acceptance_policy.v5"
    ),
    "qt": (
        "error_coupling_simulator.frontend."
        "qt_mps_restricted_acceptance_policy.v2"
    ),
}
_RESTRICTED_EXECUTION_SCHEMAS = {
    "mcwf": (
        "error_coupling_simulator.frontend."
        "mcwf_mps_state_record_execution.v6"
    ),
    "qt": (
        "error_coupling_simulator.frontend."
        "qt_mps_restricted_execution.v6"
    ),
}
_RESTRICTED_POLICY_ROLE = "restricted_execution_acceptance_not_metric"
_MCWF_SAMPLED_TRAJECTORY_MODE = "sampled_fixed_microstep_mcwf_trajectories"
_MCWF_MEASUREMENT_SAMPLING_POLICY = (
    "sequential_conditional_single_site_level_xz_v1"
)
_MCWF_RECORD_SUPPORT_POLICY = "observed_empirical_outcomes_only"
_QT_EXACT_TRAJECTORY_MODE = "exact_branch_enumeration"
_QT_SAMPLED_TRAJECTORY_MODE = "sampled_product_channel_trajectories"
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
    free_observation = _available_vram_bytes(device)
    free_is_finite_positive = (
        isinstance(free_observation, Real)
        and type(free_observation) is not bool
        and math.isfinite(float(free_observation))
        and float(free_observation) > 0.0
    )
    free = float(free_observation) if free_is_finite_positive else None
    budget = (
        AXIS1_CARRIER_DENSE_VRAM_SAFETY_FRACTION * free
        if free is not None
        else None
    )
    requires_scalable = _require_manifest_bool(
        program,
        "requires_scalable_backend",
        context="Axis-1 carrier program",
    )
    over_qubit_cap = n > AXIS1_STATE_MAX_EXACT_QUBITS
    over_vram = budget is None or projected > budget
    use_dense = (not requires_scalable) and (not over_qubit_cap) and (not over_vram)
    chosen = (
        AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT
        if use_dense
        else AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    )
    reasons: list[str] = []
    if not free_is_finite_positive:
        reasons.append("invalid_available_vram_bytes")
    if requires_scalable:
        reasons.append("requires_scalable_backend")
    if over_qubit_cap:
        reasons.append(f"num_qubits>{AXIS1_STATE_MAX_EXACT_QUBITS}")
    if over_vram and free_is_finite_positive:
        reasons.append("projected_dense_vram_exceeds_safety_budget")
    decision = {
        "schema": "error_coupling_simulator.frontend.carrier_auto_routing_decision.v3",
        "num_qubits": n,
        "measured_qubits": measured_qubits,
        "branch_factor_log2": measured_qubits,
        "dense_record_transient_factor": AXIS1_CARRIER_DENSE_RECORD_TRANSIENT_FACTOR,
        "projected_dense_vram_bytes": projected,
        "projected_dense_vram_gib": projected / (1024.0**3),
        "free_vram_bytes": free,
        "free_vram_gib": None if free is None else free / (1024.0**3),
        "available_vram_is_finite_positive": free_is_finite_positive,
        "safety_fraction": AXIS1_CARRIER_DENSE_VRAM_SAFETY_FRACTION,
        "dense_vram_budget_bytes": budget,
        "dense_vram_budget_gib": None if budget is None else budget / (1024.0**3),
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
            "fails TOWARD the memory-bounded MCWF backend; a nonfinite or "
            "nonpositive free-VRAM observation also fails toward MCWF and is "
            "never serialized as a nonfinite JSON number"
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

    device = normalize_mps_device(device)
    raw_options = dict(execution_backend_options or {})
    options = (
        _validate_mcwf_mps_execution_options(raw_options)
        if raw_options
        else {}
    )
    dev = _require_cuda_device(device)
    program = axis1_carrier_program_manifest(schedule)
    chosen, decision = _select_dense_or_mcwf(schedule, dev, program)
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
    inner_passed = _require_manifest_bool(
        inner, "passed", context="auto-routed Carrier execution"
    )
    inner_verdict = _require_manifest_text(
        inner, "verdict", context="auto-routed Carrier execution"
    )
    expected_verdict = "pass" if inner_passed else "fail"
    if inner_verdict != expected_verdict:
        raise ValueError(
            "auto-routed Carrier child verdict must agree with its passed field"
        )
    _validate_auto_routed_carrier_child(
        inner,
        schedule=schedule,
        chosen_backend_contract=chosen,
        expected_device=dev,
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
        "verdict": inner_verdict,
        "passed": inner_passed,
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


def _validate_auto_routed_carrier_child(
    child: dict[str, Any],
    *,
    schedule: SubstepSchedule,
    chosen_backend_contract: str,
    expected_device: str,
) -> None:
    """Authenticate the delegated Carrier envelope against the router request."""

    _validate_child_content_hash(child, context="auto-routed Carrier child")
    schema = _require_manifest_text(
        child,
        "schema",
        context="auto-routed Carrier child",
    )
    if schema != AXIS1_CARRIER_EXECUTION_SCHEMA:
        raise ValueError("auto-routed Carrier child schema is not registered")
    expected_representability_by_route = {
        AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT: (
            AXIS1_CARRIER_EXECUTION_REPRESENTABILITY
        ),
        AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT: (
            AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY
        ),
    }
    if chosen_backend_contract not in expected_representability_by_route:
        raise ValueError("auto-routed Carrier resolved backend is not registered")
    expected_text_fields = {
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": expected_representability_by_route[
            chosen_backend_contract
        ],
        "execution_backend_contract": chosen_backend_contract,
        "device": expected_device,
    }
    for field, expected in expected_text_fields.items():
        actual = _require_manifest_text(
            child,
            field,
            context="auto-routed Carrier child",
        )
        if actual != expected:
            raise ValueError(
                f"auto-routed Carrier child {field} must match the resolved request"
            )
    if not _require_manifest_bool(
        child,
        "gpu_required",
        context="auto-routed Carrier child",
    ):
        raise ValueError("auto-routed Carrier child gpu_required must be true")

    if chosen_backend_contract == AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT:
        trusted_program = axis1_carrier_program_manifest(
            schedule,
            backend_contract=chosen_backend_contract,
        )
        expected_program = _restricted_mps_program_summary(trusted_program)
        route_false_claims = (
            "claims_production_scalable_backend",
            "claims_exact_joint_lindblad_generator",
            "claims_qt_mps_backend_execution",
            "claims_qutip_cuquantum_execution",
        )
        optional_route_false_claims: tuple[str, ...] = ()
    else:
        trusted_program = axis1_carrier_program_manifest(schedule)
        expected_program = _carrier_program_summary(trusted_program)
        route_false_claims = ()
        optional_route_false_claims = (
            "claims_production_scalable_backend",
            "claims_exact_joint_lindblad_generator",
            "claims_mcwf_mps_backend_execution",
            "claims_qt_mps_backend_execution",
            "claims_qutip_cuquantum_execution",
        )
    child_program = child.get("carrier_program")
    if not isinstance(child_program, dict):
        raise TypeError("auto-routed Carrier child carrier_program must be a mapping")
    if _stable_payload_hash({"carrier_program": child_program}) != (
        _stable_payload_hash({"carrier_program": expected_program})
    ):
        raise ValueError(
            "auto-routed Carrier child carrier_program must match the trusted "
            "schedule and resolved route"
        )

    for field in (
        "claims_dense_channel_evidence",
        "claims_dem_decoder_semantics",
        "claims_axis2_source_timeline",
        "claims_scalable_backend_completed",
        *route_false_claims,
    ):
        if _require_manifest_bool(
            child,
            field,
            context="auto-routed Carrier child",
        ):
            raise ValueError(f"auto-routed Carrier child {field} must be false")
    for field in optional_route_false_claims:
        if field not in child:
            continue
        if _require_manifest_bool(
            child,
            field,
            context="auto-routed Carrier child",
        ):
            raise ValueError(f"auto-routed Carrier child {field} must be false")


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
    options = _validate_mcwf_mps_execution_options(execution_backend_options or {})
    device = normalize_mps_device(device)
    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(
        schedule,
        allow_multilevel_leakage_context=True,
    )
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT,
    )
    expected = _mcwf_mps_expected_options(
        options,
        num_sites=int(schedule.num_qubits),
    )
    from .axis1_mcwf_mps_execution import (
        AXIS1_MCWF_MPS_EXECUTION_REPRESENTABILITY,
        axis1_mcwf_mps_state_record_execution_manifest,
    )

    mcwf_mps = axis1_mcwf_mps_state_record_execution_manifest(
        schedule,
        device=dev,
        **options,
    )
    _validate_child_content_hash(mcwf_mps, context="MCWF/MPS child")
    if mcwf_mps.get("source_kind") != schedule.source_kind:
        raise ValueError("MCWF/MPS child source_kind must match the requested schedule")
    if mcwf_mps.get("source_hash") != schedule.source_hash:
        raise ValueError("MCWF/MPS child source_hash must match the requested schedule")
    if mcwf_mps.get("schedule_representability") != schedule.representability:
        raise ValueError(
            "MCWF/MPS child schedule_representability must match the schedule"
        )
    if mcwf_mps.get("representability") != (
        AXIS1_MCWF_MPS_EXECUTION_REPRESENTABILITY
    ):
        raise ValueError("MCWF/MPS child representability is not registered")
    if mcwf_mps.get("backend_contract") != (
        AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT
    ):
        raise ValueError("MCWF/MPS child backend_contract is not registered")
    if mcwf_mps.get("gpu_required") is not True:
        raise ValueError("MCWF/MPS child gpu_required must be true")
    if mcwf_mps.get("device") != dev:
        raise ValueError("MCWF/MPS child device must match the requested device")
    if mcwf_mps.get("carrier_program") != _restricted_mps_program_summary(program):
        raise ValueError(
            "MCWF/MPS child carrier_program must match the requested schedule"
        )
    _validate_mcwf_mps_child_options(
        mcwf_mps,
        expected=expected,
    )
    execution = mcwf_mps.get("mps_execution") or {}
    passed = _require_manifest_bool(mcwf_mps, "passed", context="MCWF/MPS execution")
    child_verdict = _require_manifest_text(
        mcwf_mps, "verdict", context="MCWF/MPS execution"
    )
    if child_verdict != ("pass" if passed else "fail"):
        raise ValueError("MCWF/MPS child verdict must agree with its passed field")
    child_schema = _require_manifest_text(
        mcwf_mps,
        "schema",
        context="MCWF/MPS execution",
    )
    if child_schema != _RESTRICTED_EXECUTION_SCHEMAS["mcwf"]:
        raise ValueError("MCWF/MPS execution schema is not registered")
    executed = _require_manifest_bool(
        mcwf_mps,
        "mcwf_mps_backend_executed",
        context="MCWF/MPS execution",
    )
    claimed_execution = _require_manifest_bool(
        mcwf_mps,
        "claims_mcwf_mps_backend_execution",
        context="MCWF/MPS execution",
    )
    if claimed_execution is not executed:
        raise ValueError(
            "MCWF/MPS backend execution claim must equal actual backend state"
        )
    for field in (
        "claims_production_scalable_backend",
        "claims_exact_joint_lindblad_generator",
        "claims_dense_channel_evidence",
        "claims_dem_decoder_semantics",
        "claims_axis2_source_timeline",
    ):
        if _require_manifest_bool(
            mcwf_mps,
            field,
            context="MCWF/MPS execution",
        ):
            raise ValueError(f"MCWF/MPS child {field} must be false")
    acceptance = mcwf_mps.get("restricted_acceptance_policy")
    if not isinstance(acceptance, dict):
        raise TypeError("MCWF/MPS restricted_acceptance_policy must be a mapping")
    accepted = _require_manifest_bool(
        acceptance,
        "accepted_for_restricted_execution",
        context="MCWF/MPS restricted acceptance policy",
    )
    if passed is not accepted:
        raise ValueError(
            "MCWF/MPS execution passed must equal accepted_for_restricted_execution"
        )
    execution_status = _require_manifest_text(
        mcwf_mps, "execution_status", context="MCWF/MPS execution"
    )
    certification_status = _require_manifest_text(
        mcwf_mps, "certification_status", context="MCWF/MPS execution"
    )
    diagnostic_only = _require_manifest_bool(
        mcwf_mps, "diagnostic_only", context="MCWF/MPS execution"
    )
    _validate_restricted_child_state_machine(
        passed=passed,
        child_verdict=child_verdict,
        backend_executed=executed,
        execution_status=execution_status,
        certification_status=certification_status,
        diagnostic_only=diagnostic_only,
        blocked_reason=mcwf_mps.get("blocked_reason"),
        context="MCWF/MPS",
    )
    _validate_restricted_policy_state(
        acceptance,
        execution_status=execution_status,
        certification_status=certification_status,
        diagnostic_only=diagnostic_only,
        blocked_reason=mcwf_mps.get("blocked_reason"),
        context="MCWF/MPS",
        route_kind="mcwf",
    )
    if executed:
        if not isinstance(execution, dict):
            raise TypeError("MCWF/MPS child mps_execution must be a mapping")
        sampling = execution.get("trajectory_sampling")
        if not isinstance(sampling, dict):
            raise TypeError(
                "MCWF/MPS child trajectory_sampling must be a mapping"
            )
        actual_trajectory_mode = _require_manifest_text(
            sampling,
            "mode",
            context="MCWF/MPS child trajectory_sampling",
        )
        if actual_trajectory_mode != acceptance["trajectory"]["mode"]:
            raise ValueError(
                "MCWF/MPS policy trajectory mode must match actual child execution"
            )
        _validate_mcwf_mps_child_execution_options(
            execution,
            policy=acceptance,
            expected=expected,
        )
        from ..certify.axis1_mps import (
            _validate_metric_family_execution_payload,
            dense_jointL_record_certification,
            restricted_acceptance_policy,
        )

        _validate_metric_family_execution_payload(
            execution,
            sampled=True,
            trajectory_count=expected["trajectory_count"],
            declared_local_dims=expected["local_dims"],
            program=program,
        )
        _validate_axis1_projected_record_payload(
            axis1_record_layout_from_schedule(schedule),
            execution,
            context="MCWF/MPS child",
        )
        if expected["mass_residual_budget"] is None:
            certification = {
                "executed": False,
                "passed": False,
                "passed_gross": False,
                "reason": "mass_residual_budget_not_declared_diagnostic_only",
                "comparison_outcome_is_metric": False,
                "epistemic_class": "c",
            }
        else:
            certification = dense_jointL_record_certification(
                schedule,
                execution,
                program,
                declared_local_dims=expected["local_dims"],
                device=dev,
            )
        canonical_acceptance = restricted_acceptance_policy(
            execution=execution,
            certification=certification,
            program=program,
            declared_local_dims=expected["local_dims"],
            rng_seed=expected["rng_seed"],
            trajectory_count=expected["trajectory_count"],
            mass_residual_budget=expected["mass_residual_budget"],
            worst_cut_discarded_weight_gate=(
                expected["worst_cut_discarded_weight_gate"]
            ),
            total_discarded_weight_gate=expected["total_discarded_weight_gate"],
        )
        if _stable_payload_hash({"policy": acceptance}) != _stable_payload_hash(
            {"policy": canonical_acceptance}
        ):
            raise ValueError(
                "MCWF/MPS child restricted_acceptance_policy must equal the "
                "canonical restricted acceptance policy independently recomputed "
                "from the requested schedule, options, execution, and dense metric"
            )
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
        "execution_status": execution_status,
        "certification_status": certification_status,
        "diagnostic_only": diagnostic_only,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "blocked_reason": mcwf_mps.get("blocked_reason"),
        "dense_probe_executed": False,
        "qt_mps_backend_executed": False,
        "mcwf_mps_backend_executed": executed,
        "qutip_cuquantum_probe_executed": False,
        "carrier_program": dict(mcwf_mps["carrier_program"]),
        "local_hilbert_space": dict(mcwf_mps.get("local_hilbert_space", {})),
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
            "execution_status": execution_status,
            "certification_status": certification_status,
            "diagnostic_only": diagnostic_only,
            "passed": passed,
            "mcwf_mps_backend_executed": executed,
            "claims_exact_joint_lindblad_generator": _require_manifest_bool(
                mcwf_mps,
                "claims_exact_joint_lindblad_generator",
                context="MCWF/MPS execution",
            ),
            "claims_dense_channel_evidence": _require_manifest_bool(
                mcwf_mps,
                "claims_dense_channel_evidence",
                context="MCWF/MPS execution",
            ),
            "claims_production_scalable_backend": _require_manifest_bool(
                mcwf_mps,
                "claims_production_scalable_backend",
                context="MCWF/MPS execution",
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
            "mcwf_mps_execution_contract": "a/c",
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
    device = normalize_mps_device(device)
    _validate_schedule_for_axis1_channel_evidence(schedule)
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT,
    )
    carrier_summary = _carrier_program_summary(program)
    qt_mps_options = _validate_qt_mps_backend_options(execution_backend_options or {})
    from .axis1_qt_mps_execution import (
        _record_materialization_preflight_for_schedule,
        _validate_qt_restricted_child,
        axis1_qt_mps_restricted_execution_manifest,
    )
    qt_mps = axis1_qt_mps_restricted_execution_manifest(
        schedule,
        device=device,
        **qt_mps_options,
    )
    expected = _qt_mps_expected_options(qt_mps_options)
    expected_preflight = _record_materialization_preflight_for_schedule(
        schedule,
        max_record_materialization_outcomes=expected[
            "max_record_materialization_outcomes"
        ],
        trajectory_count=expected["trajectory_count"],
    )
    _validate_qt_restricted_child(
        qt_mps,
        context="QT/MPS Carrier child",
        expected_trajectory_mode=(
            _QT_SAMPLED_TRAJECTORY_MODE
            if expected["trajectory_count"] is not None
            else _QT_EXACT_TRAJECTORY_MODE
        ),
        expected_schedule=schedule,
        expected_source_kind=schedule.source_kind,
        expected_source_hash=schedule.source_hash,
        expected_schedule_representability=schedule.representability,
        expected_carrier_program=_restricted_mps_program_summary(program),
        expected_device=device,
        expected_max_bond=expected["max_bond"],
        expected_max_branches=expected["max_branches"],
        expected_record_budget=expected["max_record_materialization_outcomes"],
        expected_record_materialization_preflight=expected_preflight,
        expected_record_layout=axis1_record_layout_from_schedule(schedule),
        expected_microstep_count=expected["microstep_count"],
        expected_finite_step_order=expected["finite_step_order"],
        expected_trajectory_count=expected["trajectory_count"],
        expected_rng_seed=expected["rng_seed"],
        expected_worst_cut_discarded_weight_gate=expected[
            "worst_cut_discarded_weight_gate"
        ],
        expected_total_discarded_weight_gate=expected[
            "total_discarded_weight_gate"
        ],
        expected_dense_oracle_certification=expected[
            "dense_oracle_certification"
        ],
    )
    if qt_mps.get("carrier_program") != _restricted_mps_program_summary(program):
        raise ValueError(
            "QT/MPS child carrier_program must match the requested schedule"
        )
    dev = qt_mps.get("device")
    if not isinstance(dev, str) or not dev:
        raise TypeError("QT/MPS execution manifest device must be a nonempty string")
    if dev != device:
        raise ValueError("QT/MPS child device must match the requested device")
    acceptance = qt_mps.get("restricted_acceptance_policy")
    if not isinstance(acceptance, dict):
        raise TypeError("QT/MPS restricted_acceptance_policy must be a mapping")
    certification = qt_mps.get("dense_jointL_record_certification")
    if not isinstance(certification, dict):
        raise TypeError("QT/MPS dense_jointL_record_certification must be a mapping")
    dense_probe_executed = _require_manifest_bool(
        certification,
        "executed",
        context="QT/MPS dense certification",
    )
    if dense_probe_executed or "passed" in certification:
        _require_manifest_bool(
            certification,
            "passed",
            context="QT/MPS dense certification",
        )
    passed = _require_manifest_bool(qt_mps, "passed", context="QT/MPS execution")
    child_verdict = _require_manifest_text(
        qt_mps, "verdict", context="QT/MPS execution"
    )
    child_schema = _require_manifest_text(
        qt_mps,
        "schema",
        context="QT/MPS execution",
    )
    if child_schema != _RESTRICTED_EXECUTION_SCHEMAS["qt"]:
        raise ValueError("QT/MPS execution schema is not registered")
    accepted = _require_manifest_bool(
        acceptance,
        "accepted_for_restricted_execution",
        context="QT/MPS restricted acceptance policy",
    )
    if passed is not accepted:
        raise ValueError(
            "QT/MPS execution passed must equal "
            "accepted_for_restricted_execution"
        )
    execution_status = _require_manifest_text(
        qt_mps, "execution_status", context="QT/MPS execution"
    )
    certification_status = _require_manifest_text(
        qt_mps, "certification_status", context="QT/MPS execution"
    )
    diagnostic_only = _require_manifest_bool(
        qt_mps, "diagnostic_only", context="QT/MPS execution"
    )
    qt_backend_executed = _require_manifest_bool(
        qt_mps,
        "qt_mps_backend_executed",
        context="QT/MPS execution",
    )
    _validate_restricted_child_state_machine(
        passed=passed,
        child_verdict=child_verdict,
        backend_executed=qt_backend_executed,
        execution_status=execution_status,
        certification_status=certification_status,
        diagnostic_only=diagnostic_only,
        blocked_reason=qt_mps.get("blocked_reason"),
        context="QT/MPS",
    )
    claims_qt_backend_execution = _require_manifest_bool(
        qt_mps,
        "claims_qt_mps_backend_execution",
        context="QT/MPS execution",
    )
    if claims_qt_backend_execution is not qt_backend_executed:
        raise ValueError(
            "QT/MPS backend execution claim must equal actual backend state"
        )
    _validate_restricted_policy_state(
        acceptance,
        execution_status=execution_status,
        certification_status=certification_status,
        diagnostic_only=diagnostic_only,
        blocked_reason=qt_mps.get("blocked_reason"),
        context="QT/MPS",
        route_kind="qt",
    )
    if qt_backend_executed:
        execution = qt_mps.get("mps_execution")
        if not isinstance(execution, dict):
            raise TypeError("QT/MPS child mps_execution must be a mapping")
        sampling = execution.get("trajectory_sampling")
        if not isinstance(sampling, dict):
            raise TypeError("QT/MPS child trajectory_sampling must be a mapping")
        actual_trajectory_mode = _require_manifest_text(
            sampling,
            "mode",
            context="QT/MPS child trajectory_sampling",
        )
        if actual_trajectory_mode != acceptance["trajectory"]["mode"]:
            raise ValueError(
                "QT/MPS policy trajectory mode must match actual child execution"
            )
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
        "execution_status": execution_status,
        "certification_status": certification_status,
        "diagnostic_only": diagnostic_only,
        "verdict": "pass" if passed else "fail",
        "passed": passed,
        "blocked_reason": qt_mps.get("blocked_reason"),
        "dense_probe_executed": dense_probe_executed,
        "qt_mps_backend_executed": qt_backend_executed,
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
        "claims_qt_mps_backend_execution": qt_backend_executed,
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


def _validate_mcwf_mps_execution_options(options: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "finite_step_order",
        "initial_levels",
        "leaked_readout_b",
        "local_dims",
        "max_bond",
        "mass_residual_budget",
        "microstep_count",
        "rng_seed",
        "total_discarded_weight_gate",
        "trajectory_count",
        "worst_cut_discarded_weight_gate",
    }
    unknown = sorted(set(options) - allowed)
    if unknown:
        joined = ", ".join(unknown)
        raise ValueError(f"unsupported MCWF/MPS execution options: {joined}")
    out = dict(options)
    if "local_dims" in out and out["local_dims"] is not None:
        out["local_dims"] = list(
            normalize_mps_index_sequence(
                out["local_dims"],
                name="local_dims",
                minimum=2,
            )
        )
    if "initial_levels" in out and out["initial_levels"] is not None:
        out["initial_levels"] = list(
            normalize_mps_index_sequence(
                out["initial_levels"],
                name="initial_levels",
                minimum=0,
            )
        )
    if "leaked_readout_b" in out:
        out["leaked_readout_b"] = normalize_mps_finite_real(
            out["leaked_readout_b"],
            name="leaked_readout_b",
            minimum=0.0,
            maximum=1.0,
        )
    if "max_bond" in out and out["max_bond"] is not None:
        out["max_bond"] = normalize_mps_max_bond(
            out["max_bond"], allow_none=False
        )
    if "microstep_count" in out:
        out["microstep_count"] = normalize_mps_index(
            out["microstep_count"],
            name="microstep_count",
            minimum=1,
        )
    if "trajectory_count" in out:
        out["trajectory_count"] = normalize_mps_index(
            out["trajectory_count"],
            name="trajectory_count",
            minimum=1,
        )
    if "rng_seed" in out and out["rng_seed"] is not None:
        out["rng_seed"] = normalize_optional_mps_index(
            out["rng_seed"],
            name="rng_seed",
        )
    if "finite_step_order" in out:
        out["finite_step_order"] = normalize_mps_choice(
            out["finite_step_order"],
            name="finite_step_order",
            choices=("first_order", "strang_second_order"),
        )
    for name in (
        "mass_residual_budget",
        "total_discarded_weight_gate",
        "worst_cut_discarded_weight_gate",
    ):
        if name in out and out[name] is not None:
            out[name] = normalize_mps_finite_real(
                out[name],
                name=name,
                minimum=0.0,
            )
    return out


def _mcwf_mps_expected_options(
    requested: dict[str, Any],
    *,
    num_sites: int,
) -> dict[str, Any]:
    expected = {
        "local_dims": [2] * num_sites,
        "initial_levels": [0] * num_sites,
        "leaked_readout_b": 1.0,
        "max_bond": None,
        "worst_cut_discarded_weight_gate": None,
        "total_discarded_weight_gate": None,
        "microstep_count": 1,
        "mass_residual_budget": 0.1,
        "finite_step_order": "first_order",
        "trajectory_count": 1,
        "rng_seed": None,
    }
    expected.update(requested)
    return expected


def _validate_mcwf_mps_child_options(
    child: dict[str, Any],
    *,
    expected: dict[str, Any],
) -> None:
    for option_name, expected_value in expected.items():
        actual_value = (
            child.get("local_hilbert_space", {}).get("local_dims")
            if option_name == "local_dims"
            else child.get(option_name)
        )
        if (
            actual_value != expected_value
            or type(actual_value) is not type(expected_value)
        ):
            raise ValueError(
                f"MCWF/MPS child {option_name} must match the requested option"
            )


def _validate_mcwf_mps_child_execution_options(
    execution: dict[str, Any],
    *,
    policy: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    sampling = execution.get("trajectory_sampling")
    if not isinstance(sampling, dict):
        raise TypeError("MCWF/MPS child trajectory_sampling must be a mapping")
    expected_seed = 0 if expected["rng_seed"] is None else expected["rng_seed"]
    mirrors = (
        (sampling, "trajectory_count", expected["trajectory_count"], "trajectory_sampling"),
        (sampling, "rng_seed", expected_seed, "trajectory_sampling"),
        (
            sampling,
            "rng_seed_was_explicit",
            expected["rng_seed"] is not None,
            "trajectory_sampling",
        ),
        (
            sampling,
            "measurement_sampling_policy",
            _MCWF_MEASUREMENT_SAMPLING_POLICY,
            "trajectory_sampling",
        ),
        (
            sampling,
            "record_support_policy",
            _MCWF_RECORD_SUPPORT_POLICY,
            "trajectory_sampling",
        ),
        (
            sampling,
            "zero_frequency_records_emitted",
            False,
            "trajectory_sampling",
        ),
    )
    finite_step = execution.get("finite_step_policy")
    if not isinstance(finite_step, dict):
        raise TypeError("MCWF/MPS child finite_step_policy must be a mapping")
    mirrors += (
        (finite_step, "order", expected["finite_step_order"], "finite_step_policy"),
        (
            finite_step,
            "microstep_count",
            expected["microstep_count"],
            "finite_step_policy",
        ),
    )
    ledger = execution.get("mps_truncation_ledger")
    if not isinstance(ledger, dict):
        raise TypeError("MCWF/MPS child mps_truncation_ledger must be a mapping")
    explicit_truncation = _require_manifest_bool(
        ledger,
        "explicit_truncation_requested",
        context="MCWF/MPS child mps_truncation_ledger",
    )
    if explicit_truncation != (expected["max_bond"] is not None):
        raise ValueError(
            "MCWF/MPS child mps_truncation_ledger explicit-truncation state "
            "must match max_bond"
        )
    if expected["max_bond"] is None:
        if "max_bond" in ledger:
            raise ValueError(
                "MCWF/MPS uncapped child ledger cannot carry max_bond"
            )
    else:
        mirrors += (
            (ledger, "max_bond", expected["max_bond"], "mps_truncation_ledger"),
        )
    measurement_policy = execution.get("multilevel_measurement_policy")
    if not isinstance(measurement_policy, dict):
        raise TypeError(
            "MCWF/MPS child multilevel_measurement_policy must be a mapping"
        )
    mirrors += (
        (
            measurement_policy,
            "leaked_readout_b",
            expected["leaked_readout_b"],
            "multilevel_measurement_policy",
        ),
        (execution, "initial_levels", expected["initial_levels"], "mps_execution"),
        (execution, "local_dims", expected["local_dims"], "mps_execution"),
    )
    trajectory_policy = policy.get("trajectory")
    if not isinstance(trajectory_policy, dict):
        raise TypeError("MCWF/MPS policy trajectory must be a mapping")
    mirrors += (
        (
            trajectory_policy,
            "trajectory_count",
            expected["trajectory_count"],
            "policy trajectory",
        ),
        (trajectory_policy, "rng_seed", expected["rng_seed"], "policy trajectory"),
    )
    for container, field, expected_value, context in mirrors:
        if field not in container:
            raise ValueError(f"MCWF/MPS child {context}.{field} is required")
        actual_value = container[field]
        if (
            actual_value != expected_value
            or type(actual_value) is not type(expected_value)
        ):
            raise ValueError(
                f"MCWF/MPS child {context}.{field} must match the requested option"
            )


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
        "max_record_materialization_outcomes",
    }
    unknown = sorted(set(options) - allowed)
    if unknown:
        joined = ", ".join(unknown)
        raise ValueError(f"unsupported QT/MPS execution_backend_options: {joined}")
    out = dict(options)
    if "max_bond" in out:
        out["max_bond"] = normalize_mps_max_bond(out["max_bond"])
    for name in ("max_branches", "microstep_count"):
        if name in out:
            out[name] = normalize_mps_index(
                out[name],
                name=name,
                minimum=1,
            )
    if "max_record_materialization_outcomes" in out:
        out["max_record_materialization_outcomes"] = normalize_mps_index(
            out["max_record_materialization_outcomes"],
            name="max_record_materialization_outcomes",
            minimum=1,
        )
    if "trajectory_count" in out:
        out["trajectory_count"] = normalize_optional_mps_index(
            out["trajectory_count"],
            name="trajectory_count",
            minimum=1,
        )
    if "rng_seed" in out:
        out["rng_seed"] = normalize_optional_mps_index(
            out["rng_seed"],
            name="rng_seed",
        )
    if "finite_step_order" in out:
        out["finite_step_order"] = normalize_mps_choice(
            out["finite_step_order"],
            name="finite_step_order",
            choices=("first_order", "strang_second_order"),
        )
    if "dense_oracle_certification" in out:
        out["dense_oracle_certification"] = normalize_mps_bool(
            out["dense_oracle_certification"],
            name="dense_oracle_certification",
        )
    for name in (
        "total_discarded_weight_gate",
        "worst_cut_discarded_weight_gate",
    ):
        if name in out and out[name] is not None:
            out[name] = normalize_mps_finite_real(
                out[name],
                name=name,
                minimum=0.0,
            )
    return out


def _qt_mps_expected_options(requested: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "max_bond": None,
        "max_branches": 4096,
        "max_record_materialization_outcomes": 4096,
        "microstep_count": 1,
        "finite_step_order": "first_order",
        "worst_cut_discarded_weight_gate": None,
        "total_discarded_weight_gate": None,
        "trajectory_count": None,
        "rng_seed": None,
        "dense_oracle_certification": True,
    }
    expected.update(requested)
    return expected


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
        "requires_scalable_backend": _require_manifest_bool(
            program,
            "requires_scalable_backend",
            context="Axis-1 carrier program",
        ),
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


def _restricted_mps_program_summary(program: dict[str, Any]) -> dict[str, Any]:
    substeps = list(program.get("program", {}).get("substeps", ()))
    return {
        "schema": program.get("schema"),
        "content_hash": program.get("content_hash"),
        "backend_contract": program.get("backend_contract"),
        "requires_scalable_backend": _require_manifest_bool(
            program,
            "requires_scalable_backend",
            context="Axis-1 Carrier program",
        ),
        "routes": sorted({str(step.get("route")) for step in substeps}),
        "substep_count": len(substeps),
    }


def _require_manifest_bool(
    manifest: dict[str, Any],
    field: str,
    *,
    context: str,
) -> bool:
    value = manifest[field]
    if type(value) is not bool:
        raise TypeError(f"{context} field {field!r} must be an actual bool")
    return value


def _require_manifest_text(
    manifest: dict[str, Any],
    field: str,
    *,
    context: str,
) -> str:
    value = manifest[field]
    if not isinstance(value, str) or not value:
        raise TypeError(f"{context} field {field!r} must be a nonempty string")
    return value


def _validate_restricted_child_state_machine(
    *,
    passed: bool,
    child_verdict: str,
    backend_executed: bool,
    execution_status: str,
    certification_status: str,
    diagnostic_only: bool,
    blocked_reason: Any,
    context: str,
) -> None:
    expected_verdict = "pass" if passed else "fail"
    if child_verdict != expected_verdict:
        raise ValueError(
            f"{context} child verdict must agree with its passed field"
        )

    if backend_executed != (execution_status == "completed"):
        raise ValueError(
            f"{context} backend execution must agree with execution_status"
        )
    if passed and blocked_reason is not None:
        raise ValueError(f"{context} passing child must not carry a blocked reason")

    if passed:
        valid = (
            execution_status == "completed"
            and certification_status == "accepted"
            and not diagnostic_only
        )
    elif execution_status in {"blocked", "failed"}:
        valid = (
            certification_status in {"not_evaluated", "unavailable"}
            and not diagnostic_only
        )
    elif execution_status == "completed" and certification_status == "rejected":
        valid = not diagnostic_only
    elif execution_status == "completed" and certification_status in {
        "not_evaluated",
        "unavailable",
    }:
        valid = diagnostic_only
    else:
        valid = False

    if not valid:
        raise ValueError(
            f"{context} child state machine is inconsistent: "
            f"passed={passed}, execution_status={execution_status!r}, "
            f"certification_status={certification_status!r}, "
            f"diagnostic_only={diagnostic_only}"
        )


def _validate_restricted_policy_state(
    policy: dict[str, Any],
    *,
    execution_status: str,
    certification_status: str,
    diagnostic_only: bool,
    blocked_reason: Any,
    context: str,
    route_kind: str | None = None,
) -> None:
    trajectory_mode: str | None = None
    if route_kind is not None:
        if route_kind not in _RESTRICTED_POLICY_SCHEMAS:
            raise ValueError(f"{context} restricted policy route kind is invalid")
        schema = _require_manifest_text(
            policy,
            "schema",
            context=f"{context} restricted acceptance policy",
        )
        expected_schema = _RESTRICTED_POLICY_SCHEMAS[route_kind]
        if schema != expected_schema:
            raise ValueError(
                f"{context} restricted acceptance policy schema must equal "
                f"{expected_schema!r}"
            )
        policy_role = _require_manifest_text(
            policy,
            "policy_role",
            context=f"{context} restricted acceptance policy",
        )
        if policy_role != _RESTRICTED_POLICY_ROLE:
            raise ValueError(
                f"{context} restricted acceptance policy role is invalid"
            )
        trajectory = policy.get("trajectory")
        if not isinstance(trajectory, dict):
            raise TypeError(
                f"{context} restricted acceptance policy trajectory must be a mapping"
            )
        trajectory_mode = _require_manifest_text(
            trajectory,
            "mode",
            context=f"{context} restricted acceptance policy trajectory",
        )
    policy_execution_status = _require_manifest_text(
        policy,
        "execution_status",
        context=f"{context} restricted acceptance policy",
    )
    policy_certification_status = _require_manifest_text(
        policy,
        "certification_status",
        context=f"{context} restricted acceptance policy",
    )
    policy_diagnostic_only = _require_manifest_bool(
        policy,
        "diagnostic_only",
        context=f"{context} restricted acceptance policy",
    )
    if (
        policy_execution_status != execution_status
        or policy_certification_status != certification_status
        or policy_diagnostic_only != diagnostic_only
    ):
        raise ValueError(
            f"{context} restricted acceptance policy state must match child state"
        )
    if "blocked_reason" not in policy:
        raise KeyError(
            f"{context} restricted acceptance policy missing blocked_reason"
        )
    policy_blocked_reason = policy["blocked_reason"]
    if policy_blocked_reason is not None and not isinstance(
        policy_blocked_reason,
        str,
    ):
        raise TypeError(
            f"{context} restricted acceptance policy blocked_reason must be text or None"
        )
    if policy_blocked_reason != blocked_reason:
        raise ValueError(
            f"{context} restricted acceptance policy blocked_reason must match child"
        )

    accepted = _require_manifest_bool(
        policy,
        "accepted_for_restricted_execution",
        context=f"{context} restricted acceptance policy",
    )
    production_accepted = _require_manifest_bool(
        policy,
        "accepted_for_production_scalable_backend",
        context=f"{context} restricted acceptance policy",
    )
    if production_accepted:
        raise ValueError(
            f"{context} restricted policy cannot claim production scalable acceptance"
        )
    exact_accepted = _require_manifest_bool(
        policy,
        "accepted_for_exact_dense_probability_evidence",
        context=f"{context} restricted acceptance policy",
    )
    sampled_accepted = _require_manifest_bool(
        policy,
        "accepted_for_sampled_execution_evidence",
        context=f"{context} restricted acceptance policy",
    )
    if (exact_accepted or sampled_accepted) and not accepted:
        raise ValueError(
            f"{context} evidence acceptance requires restricted acceptance"
        )
    if route_kind == "mcwf":
        if trajectory_mode != _MCWF_SAMPLED_TRAJECTORY_MODE:
            raise ValueError(
                f"{context} sampled MCWF policy trajectory mode is invalid"
            )
        if exact_accepted:
            raise ValueError(
                f"{context} exact evidence tier is invalid for sampled MCWF"
            )
        if sampled_accepted != accepted:
            raise ValueError(
                f"{context} sampled evidence tier must equal restricted acceptance"
            )
    elif route_kind == "qt":
        if trajectory_mode == _QT_EXACT_TRAJECTORY_MODE:
            if exact_accepted != accepted or sampled_accepted:
                raise ValueError(
                    f"{context} exact QT evidence tier is inconsistent"
                )
        elif trajectory_mode == _QT_SAMPLED_TRAJECTORY_MODE:
            if exact_accepted or sampled_accepted != accepted:
                raise ValueError(
                    f"{context} sampled QT evidence tier is inconsistent"
                )
        else:
            raise ValueError(f"{context} QT trajectory mode is invalid")


def _qt_mps_execution_summary(qt_mps: dict[str, Any]) -> dict[str, Any]:
    acceptance = qt_mps["restricted_acceptance_policy"]
    certification = qt_mps.get("dense_jointL_record_certification", {})
    certification_executed = _require_manifest_bool(
        certification, "executed", context="QT/MPS dense certification"
    )
    certification_passed = (
        _require_manifest_bool(
            certification, "passed", context="QT/MPS dense certification"
        )
        if certification_executed or "passed" in certification
        else False
    )
    return {
        "schema": qt_mps.get("schema"),
        "content_hash": qt_mps.get("content_hash"),
        "representability": qt_mps.get("representability"),
        "backend_contract": qt_mps.get("backend_contract"),
        "execution_status": _require_manifest_text(
            qt_mps, "execution_status", context="QT/MPS execution"
        ),
        "certification_status": _require_manifest_text(
            qt_mps, "certification_status", context="QT/MPS execution"
        ),
        "diagnostic_only": _require_manifest_bool(
            qt_mps, "diagnostic_only", context="QT/MPS execution"
        ),
        "passed": _require_manifest_bool(
            qt_mps, "passed", context="QT/MPS execution"
        ),
        "qt_mps_backend_executed": _require_manifest_bool(
            qt_mps,
            "qt_mps_backend_executed",
            context="QT/MPS execution",
        ),
        "accepted_for_restricted_execution": _require_manifest_bool(
            acceptance,
            "accepted_for_restricted_execution",
            context="QT/MPS restricted acceptance policy",
        ),
        "accepted_for_production_scalable_backend": _require_manifest_bool(
            acceptance,
            "accepted_for_production_scalable_backend",
            context="QT/MPS restricted acceptance policy",
        ),
        "dense_jointL_record_certification_status": (
            "passed"
            if certification_executed and certification_passed
            else certification.get("reason", "not_executed")
        ),
        "claims_exact_joint_lindblad_generator": _require_manifest_bool(
            qt_mps,
            "claims_exact_joint_lindblad_generator",
            context="QT/MPS execution",
        ),
        "claims_dense_channel_evidence": _require_manifest_bool(
            qt_mps,
            "claims_dense_channel_evidence",
            context="QT/MPS execution",
        ),
        "claims_dem_decoder_semantics": _require_manifest_bool(
            qt_mps,
            "claims_dem_decoder_semantics",
            context="QT/MPS execution",
        ),
        "claims_axis2_source_timeline": _require_manifest_bool(
            qt_mps,
            "claims_axis2_source_timeline",
            context="QT/MPS execution",
        ),
        "claims_production_scalable_backend": _require_manifest_bool(
            qt_mps,
            "claims_production_scalable_backend",
            context="QT/MPS execution",
        ),
    }


def _qt_mps_state_execution_summary(qt_mps: dict[str, Any]) -> dict[str, Any]:
    execution = qt_mps.get("mps_execution")
    if not execution:
        return {
            "executed": False,
            "passed": _require_manifest_bool(
                qt_mps, "passed", context="QT/MPS execution"
            ),
            "blocked_reason": qt_mps.get("blocked_reason"),
            "blocked_substeps": list(qt_mps.get("blocked_substeps", ())),
        }
    return {
        "executed": True,
        "evidence_schema": qt_mps["schema"],
        "evidence_content_hash": qt_mps["content_hash"],
        "representability": qt_mps["representability"],
        "passed": _require_manifest_bool(
            qt_mps, "passed", context="QT/MPS execution"
        ),
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
            "passed": _require_manifest_bool(
                qt_mps, "passed", context="QT/MPS execution"
            ),
            "blocked_reason": qt_mps.get("blocked_reason"),
            "blocked_substeps": list(qt_mps.get("blocked_substeps", ())),
        }
    return {
        "executed": True,
        "evidence_schema": qt_mps["schema"],
        "evidence_content_hash": qt_mps["content_hash"],
        "representability": qt_mps["representability"],
        "passed": _require_manifest_bool(
            qt_mps, "passed", context="QT/MPS execution"
        ),
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
            allow_nan=False,
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
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _validate_child_content_hash(
    child: dict[str, Any],
    *,
    context: str,
) -> None:
    declared = child.get("content_hash")
    if not isinstance(declared, str) or not declared:
        raise TypeError(f"{context} content_hash must be a nonempty string")
    if declared != _stable_payload_hash(child):
        raise ValueError(f"{context} content_hash does not authenticate its payload")


__all__ = [
    "AXIS1_CARRIER_ALLOWED_EXECUTION_BACKEND_CONTRACTS",
    "AXIS1_CARRIER_AUTO_BACKEND_CONTRACT",
    "AXIS1_CARRIER_AUTO_EXECUTION_SCHEMA",
    "AXIS1_CARRIER_DENSE_RECORD_TRANSIENT_FACTOR",
    "AXIS1_CARRIER_DENSE_VRAM_SAFETY_FRACTION",
    "AXIS1_CARRIER_EXECUTION_BACKEND_CONTRACT",
    "AXIS1_CARRIER_MCWF_MPS_EXECUTION_BACKEND_CONTRACT",
    "AXIS1_CARRIER_MCWF_MPS_EXECUTION_REPRESENTABILITY",
    "AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_BACKEND_CONTRACT",
    "AXIS1_CARRIER_QUTIP_RESTRICTED_EXECUTION_REPRESENTABILITY",
    "AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_BACKEND_CONTRACT",
    "AXIS1_CARRIER_QT_MPS_RESTRICTED_EXECUTION_REPRESENTABILITY",
    "AXIS1_CARRIER_EXECUTION_REPRESENTABILITY",
    "AXIS1_CARRIER_EXECUTION_SCHEMA",
    "axis1_carrier_execution_manifest",
]
