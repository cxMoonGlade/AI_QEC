from __future__ import annotations

"""Canonical test fixture for policy-only MCWF artifact-certification tests.

Runtime and Carrier tests must use the real compiler/reference authority.  This
factory exists only for unit tests whose subject is a downstream policy branch
and which therefore construct synthetic execution/program dictionaries.
"""

import hashlib
import json
from typing import Any

from error_coupling_simulator.certify import axis1_mps as certification


def passing_mcwf_artifact_certification(
    program: dict[str, Any],
    *,
    local_dims: list[int] | tuple[int, ...],
    microstep_count: int = 1,
    finite_step_order: str = "first_order",
) -> dict[str, Any]:
    program_payload = program.get("program")
    if program_payload is None:
        substeps: list[dict[str, Any]] | tuple[dict[str, Any], ...] = []
    else:
        if not isinstance(program_payload, dict):
            raise TypeError("synthetic carrier program payload must be a mapping")
        substeps = program_payload.get("substeps", [])
        if not isinstance(substeps, (list, tuple)):
            raise TypeError("synthetic carrier program substeps must be a sequence")
    if "content_hash" not in program:
        encoded = json.dumps(
            program,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        program["content_hash"] = hashlib.sha256(encoded).hexdigest()

    hamiltonian_count = 0
    collapse_count = 0
    group_count = 0
    for substep in substeps:
        terms = tuple(substep.get("terms", ()))
        hamiltonian_terms = [
            term for term in terms if str(term.get("kind", "")) == "hamiltonian"
        ]
        hamiltonian_count += len(hamiltonian_terms)
        collapse_count += sum(
            str(term.get("kind", "")) == "collapse" for term in terms
        )
        group_count += len(hamiltonian_terms)

    payload: dict[str, Any] = {
        "schema": (
            certification.MCWF_DYNAMICS_ARTIFACT_REFERENCE_CERTIFICATION_SCHEMA
        ),
        "executed": True,
        "passed": True,
        "status": "passed",
        "reason": None,
        "dynamics_artifact_content_hash": "a" * 64,
        "carrier_program_content_hash": str(program["content_hash"]),
        "local_dims": [int(dim) for dim in local_dims],
        "microstep_count": int(microstep_count),
        "finite_step_order": str(finite_step_order),
        "substep_count": len(substeps),
        "hamiltonian_term_count": hamiltonian_count,
        "hamiltonian_group_count": group_count,
        "collapse_term_count": collapse_count,
        "all_substeps_covered": True,
        "all_terms_covered": True,
        "all_groups_covered": True,
        "reference_oracle": (
            "certifier_local_hand_typed_numpy_operators_and_scipy_group_expm"
        ),
        **certification._mcwf_reference_source_hashes(),
        "reference_independent_of_carrier_operator_builders": True,
        "artifacts_bound_before_execution": True,
        "post_execution_integrity_verified": True,
        "structural_zero_policy": (
            "reference_declared_structural_zeros_must_be_exact_zero"
        ),
        "operator_reference_tolerance": float(certification.NUMERICAL_ZERO),
        "group_gate_reference_tolerance": float(
            certification._MCWF_GROUP_GATE_REFERENCE_TOLERANCE
        ),
        "comparison_outcome_is_metric": False,
        "epistemic_class": "a/c",
    }
    payload["content_hash"] = certification._mcwf_reference_packet_content_hash(
        payload
    )
    return payload
