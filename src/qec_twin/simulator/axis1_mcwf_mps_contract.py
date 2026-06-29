from __future__ import annotations

"""Axis-1 MCWF/MPS carrier contract seam.

This module pins the combined architecture boundary: MCWF is the trajectory
unraveling semantics for same-substep ``H_list`` and ``c_list``; MPS is the
pure-state carrier representation. It does not execute that future backend.
"""

import hashlib
import json
import math
from typing import Any, Sequence

from qec_twin.simulator.analog_schedule import SubstepSchedule
from qec_twin.simulator.axis1_carrier_program import (
    AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT,
    axis1_carrier_program_manifest,
)
from qec_twin.simulator.axis1_channel_evidence import (
    _validate_schedule_for_axis1_channel_evidence,
)
from qec_twin.simulator.axis1_state_evidence import _require_cuda_device


AXIS1_MCWF_MPS_CONTRACT_SCHEMA = (
    "qec_twin.simulator.axis1_mcwf_mps_state_record_contract.v1"
)
AXIS1_MCWF_MPS_CONTRACT_REPRESENTABILITY = (
    "axis1_mcwf_mps_state_record_contract_no_backend_execution"
)
AXIS1_MCWF_MPS_CONTRACT_BACKEND_CONTRACT = AXIS1_CARRIER_MCWF_MPS_BACKEND_CONTRACT


def axis1_mcwf_mps_state_record_contract_manifest(
    schedule: SubstepSchedule,
    *,
    local_dims: Sequence[int] | None = None,
    device: str = "cuda",
) -> dict[str, Any]:
    """Return the contract manifest for the future MCWF-over-MPS carrier.

    The manifest is deliberately executable only as a contract check. It proves
    that a compiler-generated Axis-1 carrier program can be routed to a
    dimension-polymorphic MCWF/MPS backend surface without falling back to
    Pauli/DEM semantics, source timelines, or sequential channel composition.
    """

    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(
        schedule,
        allow_multilevel_leakage_context=True,
    )
    dims = _normalize_local_dims(local_dims, num_sites=int(schedule.num_qubits))
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_MCWF_MPS_CONTRACT_BACKEND_CONTRACT,
    )
    book = dict(program["program"]["approximation_book"])
    _validate_approximation_book(book)
    dim_classes = _dimension_classes(dims)
    payload: dict[str, Any] = {
        "schema": AXIS1_MCWF_MPS_CONTRACT_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_MCWF_MPS_CONTRACT_REPRESENTABILITY,
        "backend_contract": AXIS1_MCWF_MPS_CONTRACT_BACKEND_CONTRACT,
        "gpu_required": True,
        "device": dev,
        "contract_valid": True,
        # W-J de-overload: this is a CONTRACT-ONLY surface (backend NOT executed), so it must
        # NOT claim verdict:"pass"/passed:True (which read as "executed + passed as evidence").
        # verdict:"contract_only" + contract_valid:True conveys "the contract is valid but no
        # execution evidence was produced"; verdict:"pass" is reserved for executed evidence.
        "verdict": "contract_only",
        "passed": False,
        "backend_executed": False,
        "mcwf_mps_backend_executed": False,
        "implementation_status": "contract_only_backend_not_implemented",
        "blocked_reason": "mcwf_mps_backend_not_implemented_contract_only",
        "required_backend_slice": "mcwf_mps_state_record_execution",
        "carrier_program": _program_summary(program),
        "approximation_book": book,
        "local_hilbert_space": {
            "local_dims": list(dims),
            "num_sites": len(dims),
            "hilbert_dim": int(math.prod(dims)),
            "site_order_policy": "identity_schedule_qubit_order_v1",
            "local_dims_source": (
                "caller_backend_config_or_default_qubit_dims_not_evaluator_truth"
            ),
            "supports_qubit_sites": 2 in dim_classes,
            "supports_qutrit_sites": 3 in dim_classes,
            "supports_ququart_sites": 4 in dim_classes,
            "supports_mixed_local_dimensions": len(set(dims)) > 1,
            "dimension_validation_epistemic_class": "a",
            "modeling_choice_epistemic_class": "c",
        },
        "mcwf_semantics": {
            "trajectory_method": "monte_carlo_wave_function_quantum_trajectories",
            "state_representation": "matrix_product_state_pure_state_carrier",
            "same_substep_policy": (
                "consume summed H_list and c_list for one substep trajectory "
                "unraveling; do not replace Axis-1 with E1_after_E2 channel "
                "composition"
            ),
            "single_trajectory_density_claim": False,
            "exact_joint_lindblad_channel_claim": False,
            "epistemic_class": "a/c",
        },
        "dimension_scope": {
            "qubit": "supported_by_contract_via_local_dim_2",
            "qutrit": "supported_by_contract_via_local_dim_3",
            "ququart_or_general_qudit": "supported_by_contract_via_local_dim_ge_4",
            "computational_subspace_projection": (
                "mechanism_lowering_choice_only_not_mcwf_carrier_limit"
            ),
            "epistemic_class": "a/c",
        },
        "claims_qt_mps_restricted_product_channel_execution": False,
        "claims_production_scalable_backend": False,
        "claims_exact_joint_lindblad_generator": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "scored_quantity_policy": (
            "contract-only verification surface; no new scored quantity and no "
            "METRICS.md extension"
        ),
        "epistemic_classes": {
            "local_dim_validation": "a",
            "mcwf_mps_contract_surface": "a/c",
            "backend_execution_status": "a",
            "production_backend_status": "a",
            "dimension_modeling_choice": "c",
        },
        "scope": (
            "MCWF/MPS carrier contract only; no trajectory execution, no density "
            "channel payload, no .b8/DEM/decoder artifact, no Axis-2 source "
            "timeline, and no production scalable backend claim"
        ),
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def _normalize_local_dims(
    local_dims: Sequence[int] | None,
    *,
    num_sites: int,
) -> tuple[int, ...]:
    if local_dims is None:
        return tuple(2 for _ in range(int(num_sites)))
    dims = tuple(int(dim) for dim in local_dims)
    if len(dims) != int(num_sites):
        raise ValueError(
            f"local_dims must have length {int(num_sites)}, got {len(dims)}"
        )
    if any(dim < 2 for dim in dims):
        raise ValueError(f"local_dims entries must be >= 2, got {dims!r}")
    return dims


def _dimension_classes(local_dims: tuple[int, ...]) -> frozenset[int]:
    out = set()
    for dim in local_dims:
        if dim <= 4:
            out.add(int(dim))
        else:
            out.add(5)
    return frozenset(out)


def _validate_approximation_book(book: dict[str, Any]) -> None:
    if book.get("schema") != "qec_twin.simulator.axis1_carrier_approximation_book.v1":
        raise ValueError(
            "Axis-1 MCWF/MPS contract requires axis1_carrier_approximation_book.v1"
        )
    if book.get("backend_contract") != AXIS1_MCWF_MPS_CONTRACT_BACKEND_CONTRACT:
        raise ValueError(
            "Axis-1 MCWF/MPS contract requires backend_contract="
            f"{AXIS1_MCWF_MPS_CONTRACT_BACKEND_CONTRACT!r}"
        )
    trajectory = dict(book.get("trajectory_sampling", {}))
    if bool(trajectory.get("single_trajectory_density_claim")):
        raise ValueError("MCWF/MPS contract cannot claim a single trajectory is a density state")
    trotter = dict(book.get("trotter_split", {}))
    if "not replacements for joint_lindbladian" not in str(
        trotter.get("forbidden_exact_claim", "")
    ):
        raise ValueError("MCWF/MPS contract requires the joint-L anti-substitution guard")
    record = dict(book.get("record_branching", {}))
    if bool(record.get("claims_dem_decoder_semantics")):
        raise ValueError("MCWF/MPS contract cannot claim DEM/decoder semantics")


def _program_summary(program: dict[str, Any]) -> dict[str, Any]:
    substeps = list(program.get("program", {}).get("substeps", ()))
    term_families = sorted(
        {
            str(term.get("operator_family"))
            for substep in substeps
            for term in substep.get("terms", ())
        }
    )
    return {
        "schema": program.get("schema"),
        "content_hash": program.get("content_hash"),
        "backend_contract": program.get("backend_contract"),
        "requires_scalable_backend": bool(program.get("requires_scalable_backend")),
        "routes": sorted({str(step.get("route")) for step in substeps}),
        "substep_count": len(substeps),
        "term_operator_families": term_families,
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
    "AXIS1_MCWF_MPS_CONTRACT_BACKEND_CONTRACT",
    "AXIS1_MCWF_MPS_CONTRACT_REPRESENTABILITY",
    "AXIS1_MCWF_MPS_CONTRACT_SCHEMA",
    "axis1_mcwf_mps_state_record_contract_manifest",
]
