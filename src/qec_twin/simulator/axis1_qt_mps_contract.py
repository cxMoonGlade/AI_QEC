from __future__ import annotations

"""Axis-1 QT/MPS production-carrier contract seam.

This module does not execute the future QT/MPS backend. It pins the manifest
surface that backend must satisfy, delegates dense-checkable schedules to the
existing GPU joint-L carrier probe, and fails closed on scalable-required rows.
"""

import hashlib
import json
from typing import Any

from qec_twin.simulator.analog_schedule import SubstepSchedule
from qec_twin.simulator.axis1_carrier_execution import axis1_carrier_execution_manifest
from qec_twin.simulator.axis1_carrier_program import (
    AXIS1_CARRIER_DEFAULT_BACKEND_CONTRACT,
    axis1_carrier_program_manifest,
)
from qec_twin.simulator.axis1_channel_evidence import (
    _validate_schedule_for_axis1_channel_evidence,
)
from qec_twin.simulator.axis1_record_evidence import Axis1ReadoutResetInstrumentSpec
from qec_twin.simulator.axis1_state_evidence import _require_cuda_device


AXIS1_QT_MPS_CONTRACT_SCHEMA = "qec_twin.simulator.axis1_qt_mps_state_record_contract.v1"
AXIS1_QT_MPS_CONTRACT_REPRESENTABILITY = (
    "axis1_qt_mps_state_record_contract_no_backend_execution"
)
AXIS1_QT_MPS_CONTRACT_BACKEND_CONTRACT = AXIS1_CARRIER_DEFAULT_BACKEND_CONTRACT


def axis1_qt_mps_state_record_contract_manifest(
    schedule: SubstepSchedule,
    *,
    device: str = "cuda",
    instrument_spec: Axis1ReadoutResetInstrumentSpec | None = None,
) -> dict[str, Any]:
    """Return the QT/MPS carrier contract manifest for ``schedule``.

    Dense-checkable rows are certified through the existing dense joint-L probe.
    Scalable-required rows remain explicit blockers until the real GPU QT/MPS
    execution backend is implemented.
    """

    dev = _require_cuda_device(device)
    _validate_schedule_for_axis1_channel_evidence(schedule)
    program = axis1_carrier_program_manifest(
        schedule,
        backend_contract=AXIS1_QT_MPS_CONTRACT_BACKEND_CONTRACT,
    )
    book = dict(program["program"]["approximation_book"])
    _validate_approximation_book(book)
    base: dict[str, Any] = {
        "schema": AXIS1_QT_MPS_CONTRACT_SCHEMA,
        "source_kind": schedule.source_kind,
        "source_hash": schedule.source_hash,
        "schedule_representability": schedule.representability,
        "representability": AXIS1_QT_MPS_CONTRACT_REPRESENTABILITY,
        "backend_contract": AXIS1_QT_MPS_CONTRACT_BACKEND_CONTRACT,
        "gpu_required": True,
        "device": dev,
        "carrier_program": _program_summary(program),
        "approximation_book": book,
        "claims_qt_mps_backend_execution": False,
        "claims_production_scalable_backend": False,
        "claims_dense_channel_evidence": False,
        "claims_dem_decoder_semantics": False,
        "claims_axis2_source_timeline": False,
        "scored_quantity_policy": (
            "contract and dense-oracle verification only; no new scored quantity"
        ),
        "epistemic_classes": {
            "program_consumption": "a",
            "contract_surface": "a/c",
            "dense_oracle_certification": "a/c",
            "scalable_backend_status": "a",
        },
    }
    if bool(program["requires_scalable_backend"]):
        payload = {
            **base,
            "verdict": "fail",
            "passed": False,
            "blocked_reason": "qt_mps_backend_not_implemented_for_scalable_required",
            "qt_mps_backend_executed": False,
            "dense_oracle_certification": {
                "executed": False,
                "reason": "schedule_contains_scalable_required_rows",
            },
            "required_backend_slice": "qt_mps_state_record_execution",
            "scope": (
                "QT/MPS production-carrier contract only; scalable_required rows "
                "must wait for the GPU trajectory/MPS backend and are not replaced "
                "by dense pair fallback, Pauli/DEM semantics, or sequential "
                "composition"
            ),
        }
        payload["content_hash"] = _stable_payload_hash(payload)
        return payload

    dense = axis1_carrier_execution_manifest(
        schedule,
        device=dev,
        instrument_spec=instrument_spec,
    )
    payload = {
        **base,
        "verdict": "pass" if bool(dense["passed"]) else "fail",
        "passed": bool(dense["passed"]),
        "blocked_reason": dense.get("blocked_reason"),
        "qt_mps_backend_executed": False,
        "dense_oracle_certification": {
            "executed": True,
            "backend_contract": dense["execution_backend_contract"],
            "evidence_schema": dense["schema"],
            "evidence_content_hash": dense["content_hash"],
            "passed": bool(dense["passed"]),
            "state_execution": dense.get("state_execution"),
            "record_execution": dense.get("record_execution"),
            "comparison_outcome_is_metric": False,
        },
        "required_backend_slice": "qt_mps_state_record_execution",
        "scope": (
            "QT/MPS production-carrier contract with dense-oracle-compatible "
            "certification only; no QT/MPS backend execution yet, no over-cap "
            "state/record claim, no DEM/decoder semantics"
        ),
    }
    payload["content_hash"] = _stable_payload_hash(payload)
    return payload


def _validate_approximation_book(book: dict[str, Any]) -> None:
    if book.get("schema") != "qec_twin.simulator.axis1_carrier_approximation_book.v1":
        raise ValueError(
            "Axis-1 QT/MPS contract requires axis1_carrier_approximation_book.v1"
        )
    if book.get("backend_contract") != AXIS1_QT_MPS_CONTRACT_BACKEND_CONTRACT:
        raise ValueError(
            "Axis-1 QT/MPS contract requires backend_contract="
            f"{AXIS1_QT_MPS_CONTRACT_BACKEND_CONTRACT!r}"
        )
    dense = dict(book.get("dense_oracle_certification", {}))
    if bool(dense.get("overcap_dense_channel_rows_claimed")):
        raise ValueError("QT/MPS contract cannot claim over-cap dense channel rows")
    record = dict(book.get("record_branching", {}))
    if bool(record.get("claims_dem_decoder_semantics")):
        raise ValueError("QT/MPS contract cannot claim DEM/decoder semantics")


def _program_summary(program: dict[str, Any]) -> dict[str, Any]:
    substeps = list(program.get("program", {}).get("substeps", ()))
    return {
        "schema": program.get("schema"),
        "content_hash": program.get("content_hash"),
        "backend_contract": program.get("backend_contract"),
        "requires_scalable_backend": bool(program.get("requires_scalable_backend")),
        "routes": sorted({str(step.get("route")) for step in substeps}),
        "substep_count": len(substeps),
        "approximation_book_schema": program.get("program", {})
        .get("approximation_book", {})
        .get("schema"),
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
    "AXIS1_QT_MPS_CONTRACT_BACKEND_CONTRACT",
    "AXIS1_QT_MPS_CONTRACT_REPRESENTABILITY",
    "AXIS1_QT_MPS_CONTRACT_SCHEMA",
    "axis1_qt_mps_state_record_contract_manifest",
]
