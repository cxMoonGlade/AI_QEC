from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np

from .channels import MechanismSpec, mechanism_channel


PROBABILITY_PARAMETER_NAMES = {
    "p",
    "p_x",
    "p_y",
    "p_z",
    "p0_to_1",
    "p1_to_0",
    "gamma",
    "gamma_phi",
    "gamma_up",
    "eta",
    "probability",
}


def build_cptp_guardrail_audit(
    mechanisms: Sequence[MechanismSpec],
    *,
    tolerance: float = 1.0e-9,
) -> dict[str, object]:
    """Audit catalog physicality for enabled Layer 1 mechanism definitions."""

    records = [audit_mechanism_physicality(spec, tolerance=tolerance) for spec in mechanisms]
    failed = [record for record in records if not bool(record.get("passed"))]
    residuals = {
        "max_unitary_residual": _max_record_value(records, "unitary_residual_max_abs"),
        "max_kraus_tp_residual": _max_record_value(records, "kraus_tp_residual_max_abs"),
        "max_readout_row_sum_residual": _max_record_value(records, "readout_row_sum_residual_max_abs"),
        "invalid_parameter_record_count": int(sum(not bool(record.get("parameter_validity_passed", False)) for record in records)),
    }
    return {
        "schema": "scope_static_layer1_cptp_guardrail_audit_v1",
        "description": "Layer 1 physicality audit for catalog unitary/Kraus/readout mechanism definitions.",
        "tolerance": float(tolerance),
        "passed": not failed,
        "num_mechanism_records": int(len(records)),
        "num_failed_records": int(len(failed)),
        "residual_summary": residuals,
        "records": records,
    }


def build_cptp_guardrail_audit_from_records(
    records: Sequence[Mapping[str, object]],
    *,
    tolerance: float = 1.0e-9,
) -> dict[str, object]:
    return build_cptp_guardrail_audit([mechanism_spec_from_record(record) for record in records], tolerance=tolerance)


def audit_mechanism_physicality(spec: MechanismSpec, *, tolerance: float = 1.0e-9) -> dict[str, object]:
    parameter_audit = _parameter_validity_audit(spec.parameters)
    expected_dim = 2 ** int(spec.num_qubits)
    base: dict[str, object] = {
        "mechanism_id": str(spec.mechanism_id),
        "name": str(spec.name),
        "instruction": spec.instruction,
        "qubits": [int(q) for q in spec.qubits],
        "num_qubits": int(spec.num_qubits),
        "channel_dimension_expected": int(expected_dim),
        "parameter_validity_passed": bool(parameter_audit["passed"]),
        "parameter_validity": parameter_audit,
    }
    try:
        channel = mechanism_channel(spec)
    except Exception as exc:  # pragma: no cover - defensive artifact detail
        return {
            **base,
            "kind": "invalid",
            "passed": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    kind = str(channel["kind"])
    if kind == "unitary":
        unitary = np.asarray(channel["unitary"], dtype=np.complex128)
        dimension_passed = bool(unitary.ndim == 2 and unitary.shape == (expected_dim, expected_dim))
        cp_passed = bool(dimension_passed and np.all(np.isfinite(unitary)))
        residual = _unitary_residual(unitary)
        passed = bool(parameter_audit["passed"]) and dimension_passed and bool(np.isfinite(residual)) and residual <= float(tolerance)
        return {
            **base,
            "kind": kind,
            "complete_positivity_source": "unitary_representation",
            "complete_positivity_passed": cp_passed,
            "channel_dimension_actual": [int(value) for value in unitary.shape],
            "channel_dimension_passed": dimension_passed,
            "unitary_residual_max_abs": float(residual),
            "passed": passed,
        }
    if kind == "kraus":
        kraus = [np.asarray(item, dtype=np.complex128) for item in channel["kraus"]]  # type: ignore[index]
        shape = kraus[0].shape if kraus else ()
        dimension_passed = bool(kraus and all(op.ndim == 2 and op.shape == (expected_dim, expected_dim) for op in kraus))
        cp_passed = bool(dimension_passed and all(np.all(np.isfinite(op)) for op in kraus))
        residual = _kraus_tp_residual(kraus)
        passed = bool(parameter_audit["passed"]) and dimension_passed and bool(np.isfinite(residual)) and residual <= float(tolerance)
        return {
            **base,
            "kind": kind,
            "complete_positivity_source": "kraus_representation",
            "complete_positivity_passed": cp_passed,
            "channel_dimension_actual": [int(value) for value in shape],
            "channel_dimension_passed": dimension_passed,
            "kraus_tp_residual_max_abs": float(residual),
            "passed": passed,
        }
    if kind == "readout":
        matrix = np.asarray(channel["matrix"], dtype=np.float64)
        dimension_passed = bool(matrix.ndim == 2 and matrix.shape == (expected_dim, expected_dim))
        row_residual, entries_in_range = _readout_residual(matrix, tolerance=float(tolerance))
        passed = bool(parameter_audit["passed"]) and dimension_passed and entries_in_range and row_residual <= float(tolerance)
        return {
            **base,
            "kind": kind,
            "complete_positivity_source": "classical_stochastic_readout_matrix",
            "complete_positivity_passed": bool(dimension_passed and entries_in_range),
            "channel_dimension_actual": [int(value) for value in matrix.shape],
            "channel_dimension_passed": dimension_passed,
            "readout_row_sum_residual_max_abs": float(row_residual),
            "readout_entries_in_range": bool(entries_in_range),
            "passed": passed,
        }
    return {**base, "kind": kind, "passed": False, "error": f"unknown channel kind {kind!r}"}


def mechanism_spec_from_record(record: Mapping[str, object]) -> MechanismSpec:
    qubits_raw = record.get("qubits", ())
    qubits = tuple(int(q) for q in qubits_raw) if isinstance(qubits_raw, (list, tuple)) else ()
    parameters = record.get("parameters", {})
    probe_indices_raw = record.get("probe_indices", ())
    probe_indices = tuple(int(idx) for idx in probe_indices_raw) if isinstance(probe_indices_raw, (list, tuple)) else ()
    return MechanismSpec(
        mechanism_id=str(record.get("mechanism_id", record.get("oracle_label", ""))),
        name=str(record.get("name", "")),
        num_qubits=int(record.get("num_qubits", len(qubits) if qubits else 1)),
        parameters=parameters if isinstance(parameters, Mapping) else {},
        instruction=None if record.get("instruction") is None else str(record.get("instruction")),
        qubits=qubits,
        circuit_id=int(record.get("circuit_id", 0) or 0),
        probe_indices=probe_indices,
    )


def _unitary_residual(unitary: np.ndarray) -> float:
    if unitary.ndim != 2 or unitary.shape[0] != unitary.shape[1]:
        return float("inf")
    identity = np.eye(unitary.shape[0], dtype=np.complex128)
    return float(np.max(np.abs(unitary.conj().T @ unitary - identity)))


def _kraus_tp_residual(kraus: Sequence[np.ndarray]) -> float:
    if not kraus:
        return float("inf")
    dim = kraus[0].shape[0]
    accum = np.zeros((dim, dim), dtype=np.complex128)
    for op in kraus:
        if op.ndim != 2 or op.shape[0] != dim or op.shape[1] != dim:
            return float("inf")
        accum += op.conj().T @ op
    return float(np.max(np.abs(accum - np.eye(dim, dtype=np.complex128))))


def _readout_residual(matrix: np.ndarray, *, tolerance: float) -> tuple[float, bool]:
    if matrix.ndim != 2:
        return float("inf"), False
    row_residual = float(np.max(np.abs(np.sum(matrix, axis=1) - 1.0)))
    entries_in_range = bool(np.all(np.isfinite(matrix)) and np.all(matrix >= -tolerance) and np.all(matrix <= 1.0 + tolerance))
    return row_residual, entries_in_range


def _parameter_validity_audit(parameters: Mapping[str, object]) -> dict[str, object]:
    invalid: list[dict[str, object]] = []
    checked: list[str] = []
    for key, value in parameters.items():
        text = str(key)
        if text not in PROBABILITY_PARAMETER_NAMES:
            continue
        checked.append(text)
        try:
            number = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            invalid.append({"parameter": text, "value": str(value), "reason": "not_numeric"})
            continue
        if not np.isfinite(number) or number < 0.0 or number > 1.0:
            invalid.append({"parameter": text, "value": number, "reason": "outside_[0,1]"})
    return {
        "passed": not invalid,
        "checked_parameters": checked,
        "invalid_parameters": invalid,
    }


def _max_record_value(records: Sequence[Mapping[str, object]], key: str) -> float:
    values = [float(record[key]) for record in records if key in record and np.isfinite(float(record[key]))]
    return float(max(values)) if values else 0.0
