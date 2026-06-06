from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np


OVERLAY_MECHANISM_IDS = ("M11",)
REQUIRED_OVERLAY_FIELDS = (
    "spectator_overlay_present",
    "base_mechanism",
    "victim_relative_location",
    "aggressor_relative_location",
    "coupling_axis",
    "timing_context",
    "spectator_strength",
)
OVERLAY_CONTRACT_MISSING_REASON = "M11_overlay_contract_missing"


def overlay_contract_audit(
    records: Sequence[Mapping[str, object]],
    *,
    fail_on_missing_overlay_payload: bool = True,
) -> dict[str, object]:
    rows = []
    missing_by_field = {field: 0 for field in REQUIRED_OVERLAY_FIELDS}
    for idx, record in enumerate(records):
        mechanism_id = str(record.get("mechanism_id", record.get("oracle_label", "")))
        oracle_label = str(record.get("oracle_label", mechanism_id))
        if mechanism_id not in OVERLAY_MECHANISM_IDS and oracle_label not in OVERLAY_MECHANISM_IDS:
            continue
        present = _overlay_present(record)
        extracted = {
            "base_mechanism": _overlay_field(record, "base_mechanism"),
            "victim_relative_location": _overlay_field(record, "victim_relative_location"),
            "aggressor_relative_location": _overlay_field(record, "aggressor_relative_location"),
            "coupling_axis": _overlay_field(record, "coupling_axis"),
            "timing_context": _overlay_field(record, "timing_context"),
            "spectator_strength": _overlay_strength(record),
        }
        missing = []
        if not present:
            missing.append("spectator_overlay_present")
        for field, value in extracted.items():
            if value is None or str(value) == "unknown":
                missing.append(field)
        for field in missing:
            missing_by_field[field] = int(missing_by_field.get(field, 0)) + 1
        rows.append(
            {
                "record_index": int(idx),
                "mechanism_id": mechanism_id,
                "oracle_label": oracle_label,
                "overlay_family": "spectator_crosstalk",
                "spectator_overlay_present": bool(present),
                "overlay_payload_complete": not missing,
                "missing_fields": missing,
                "extracted_overlay_payload": extracted,
                "failure_kind": None if not missing else OVERLAY_CONTRACT_MISSING_REASON,
            }
        )
    missing_rows = [row for row in rows if not bool(row.get("overlay_payload_complete", False))]
    return {
        "schema": "qec_twin_m11_overlay_contract_audit_v1",
        "description": "Hard evaluator-record contract for M11 spectator crosstalk as an overlay-family object, not a flat mechanism leaf.",
        "overlay_mechanism_ids": list(OVERLAY_MECHANISM_IDS),
        "overlay_family": "spectator_crosstalk",
        "required_fields": list(REQUIRED_OVERLAY_FIELDS),
        "fail_on_missing_overlay_payload": bool(fail_on_missing_overlay_payload),
        "num_overlay_records": int(len(rows)),
        "num_overlay_records_missing_payload": int(len(missing_rows)),
        "missing_by_field": missing_by_field,
        "failure_kinds": sorted({str(row.get("failure_kind")) for row in missing_rows if row.get("failure_kind")}),
        "rows": rows,
        "passed": bool((not missing_rows) or not fail_on_missing_overlay_payload),
    }


def overlay_contract_missing(audit: Mapping[str, object]) -> bool:
    return int(audit.get("num_overlay_records_missing_payload", 0) or 0) > 0


def _overlay_present(record: Mapping[str, object]) -> bool:
    if bool(record.get("spectator_overlay_present", False)):
        return True
    overlay = record.get("spectator_overlay", {})
    if isinstance(overlay, Mapping) and bool(overlay.get("present", False)):
        return True
    params = record.get("parameters", {})
    return bool(isinstance(params, Mapping) and params.get("spectator_overlay_present", False))


def _overlay_field(record: Mapping[str, object], field: str) -> object | None:
    if record.get(field) is not None:
        return record.get(field)
    overlay = record.get("spectator_overlay", {})
    if isinstance(overlay, Mapping) and overlay.get(field) is not None:
        return overlay.get(field)
    params = record.get("parameters", {})
    if isinstance(params, Mapping) and params.get(field) is not None:
        return params.get(field)
    return None


def _overlay_strength(record: Mapping[str, object]) -> float | None:
    for container in (record.get("spectator_overlay", {}), record.get("parameters", {}), record):
        if not isinstance(container, Mapping):
            continue
        for key in ("spectator_strength", "strength", "coupling_strength"):
            if container.get(key) is None:
                continue
            try:
                value = float(container.get(key))
            except (TypeError, ValueError):
                continue
            if np.isfinite(value):
                return value
    return None
