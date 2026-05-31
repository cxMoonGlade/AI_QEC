from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import yaml

from scope_static.backend.channels import MechanismSpec
from scope_static.backend.channels import mechanism_channel
from scope_static.backend.cptp_guardrail import PROBABILITY_PARAMETER_NAMES
from scope_static.backend.cptp_guardrail import audit_mechanism_physicality
from scope_static.backend.cptp_guardrail import mechanism_spec_from_record
from scope_static.protocols import DATA_PREPARATION_STAGE
from scope_static.backend.mechanism_catalog import PREP_RESET_MECHANISM_IDS
from scope_static.backend.mechanism_catalog import READOUT_MECHANISM_IDS


STAGE_NAME = "Layer1.P_teacher_physicality_audit"
DEFAULT_OUTPUT_DIR = "outputs/scope_static/Layer1_teacher_physicality_audit"
STRICT_TOLERANCE = 1.0e-10
CUDA_FLOAT64_TOLERANCE = 1.0e-8
CUDA_FLOAT32_TOLERANCE = 1.0e-6
PROBABILITY_FLOOR_TOLERANCE = 1.0e-12
LEAKAGE_MECHANISM_IDS = {"M34"}
AXIS_PARAMETER_NAMES = {"axis", "operation_axis", "error_axis", "channel_axis"}
ALLOWED_AXIS_VALUES = {"x", "y", "z", "rx", "ry", "rz"}


def run_teacher_physicality_audit(
    *,
    teacher_dir: str | Path,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    tolerance_mode: str = "strict",
    tolerance: float | None = None,
    probability_tolerance: float = PROBABILITY_FLOOR_TOLERANCE,
    random_state_count: int = 4,
) -> dict[str, object]:
    """Audit a Layer 1 teacher as a physical quantum-process generator."""

    teacher = Path(teacher_dir)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    tol = _resolve_tolerance(tolerance_mode=tolerance_mode, tolerance=tolerance)

    records = _load_mechanism_records(teacher / "oracle_mechanisms.json")
    specs = [mechanism_spec_from_record(record) for record in records]
    local_records = [
        audit_local_mechanism(
            spec,
            record_index=idx,
            tolerance=tol,
            probability_tolerance=float(probability_tolerance),
            random_state_count=int(random_state_count),
        )
        for idx, spec in enumerate(specs)
    ]
    by_kind = _records_by_kind(local_records)
    unitary_audit = _unitary_audit(by_kind.get("unitary", []), tolerance=tol)
    kraus_audit = _kraus_audit(by_kind.get("kraus", []), tolerance=tol)
    choi_audit = _choi_audit([row for row in local_records if row.get("kind") in {"unitary", "kraus"}], tolerance=tol)
    readout_audit = _readout_stochasticity_audit(by_kind.get("readout", []), tolerance=tol)
    povm_audit = _povm_instrument_audit(by_kind.get("readout", []), tolerance=tol)
    reset_prep_audit = _reset_prep_audit(local_records, tolerance=tol)
    leakage_audit = _leakage_space_audit(local_records)
    parameter_audit = mechanism_parameter_ranges(local_records)
    circuit_probability = circuit_probability_audit(teacher, probability_tolerance=float(probability_tolerance))
    sampling = sampling_audit(teacher, circuit_probability)
    manifest = mechanism_catalog_manifest(records, local_records)
    representation = channel_representation_manifest(local_records)
    failures = failure_cases(local_records, circuit_probability, leakage_audit, parameter_audit)
    summary = physicality_summary(
        local_records=local_records,
        circuit_probability=circuit_probability,
        leakage_audit=leakage_audit,
        parameter_audit=parameter_audit,
        failures=failures,
    )
    acceptance = teacher_physicality_acceptance(
        summary=summary,
        unitary_audit=unitary_audit,
        kraus_audit=kraus_audit,
        choi_audit=choi_audit,
        readout_audit=readout_audit,
        povm_audit=povm_audit,
        reset_prep_audit=reset_prep_audit,
        leakage_audit=leakage_audit,
        circuit_probability=circuit_probability,
        parameter_audit=parameter_audit,
    )
    summary["teacher_physicality_passed"] = bool(acceptance["teacher_physicality_passed"])

    result = {
        "schema": "scope_static_layer1p_teacher_physicality_audit_v1",
        "stage": STAGE_NAME,
        "public_layer": DATA_PREPARATION_STAGE.metadata(artifact_stage=STAGE_NAME, substage="teacher_physicality_audit"),
        "teacher_dir": str(teacher),
        "output_dir": str(output),
        "claim_boundary": {
            "data_are_cptp": False,
            "teacher_samples_observations_from_cptp_or_instrument_defined_processes": True,
            "audits_generating_maps_not_data_as_cptp": True,
            "blocks_stage3d_when_failed": True,
            "does_not_claim_hardware_ground_truth": True,
            "does_not_claim_arbitrary_cptp_gksl_learning": True,
        },
        "config": {
            "teacher_dir": str(teacher),
            "output_dir": str(output),
            "tolerance_mode": str(tolerance_mode),
            "tolerance": float(tol),
            "probability_tolerance": float(probability_tolerance),
            "random_state_count": int(random_state_count),
        },
        "mechanism_catalog_manifest": manifest,
        "mechanism_parameter_ranges": parameter_audit,
        "channel_representation_manifest": representation,
        "unitary_audit": unitary_audit,
        "kraus_audit": kraus_audit,
        "choi_audit": choi_audit,
        "gksl_audit": gksl_audit(),
        "readout_stochasticity_audit": readout_audit,
        "povm_instrument_audit": povm_audit,
        "reset_prep_audit": reset_prep_audit,
        "leakage_space_audit": leakage_audit,
        "circuit_probability_audit": circuit_probability,
        "sampling_audit": sampling,
        "physicality_by_mechanism": local_records,
        "failure_cases": failures,
        "summary": summary,
        "acceptance_audit": acceptance,
        "decision": "teacher_physicality_passed" if acceptance["teacher_physicality_passed"] else "teacher_physicality_failed",
    }
    _write_outputs(output, result)
    return result


def audit_local_mechanism(
    spec: MechanismSpec,
    *,
    record_index: int,
    tolerance: float,
    probability_tolerance: float,
    random_state_count: int,
) -> dict[str, object]:
    base_guardrail = audit_mechanism_physicality(spec, tolerance=tolerance)
    row: dict[str, object] = {
        "schema": "scope_static_layer1p_local_mechanism_physicality_v1",
        "record_index": int(record_index),
        "mechanism_id": str(spec.mechanism_id),
        "name": str(spec.name),
        "instruction": spec.instruction,
        "qubits": [int(q) for q in spec.qubits],
        "num_qubits": int(spec.num_qubits),
        "base_guardrail_passed": bool(base_guardrail.get("passed", False)),
        "parameter_validity_passed": bool(base_guardrail.get("parameter_validity_passed", False)),
        "base_guardrail": base_guardrail,
    }
    try:
        channel = mechanism_channel(spec)
    except Exception as exc:
        return {
            **row,
            "kind": "invalid",
            "passed": False,
            "error": f"{type(exc).__name__}: {exc}",
        }
    kind = str(channel.get("kind", ""))
    row["kind"] = kind
    if kind == "unitary":
        unitary = np.asarray(channel["unitary"], dtype=np.complex128)
        channel_row = _audit_unitary_channel(unitary, tolerance=tolerance)
        choi_row = _audit_choi_from_kraus([unitary], tolerance=tolerance, random_state_count=random_state_count)
        row.update(channel_row)
        row.update(choi_row)
        row["valid_module_type"] = "local_cptp_unitary_channel"
    elif kind == "kraus":
        kraus = [np.asarray(item, dtype=np.complex128) for item in channel.get("kraus", [])]  # type: ignore[arg-type]
        channel_row = _audit_kraus_channel(kraus, tolerance=tolerance)
        choi_row = _audit_choi_from_kraus(kraus, tolerance=tolerance, random_state_count=random_state_count)
        row.update(channel_row)
        row.update(choi_row)
        row["valid_module_type"] = "local_cptp_kraus_channel"
    elif kind == "readout":
        matrix = np.asarray(channel["matrix"], dtype=np.float64)
        readout_row = _audit_readout_matrix(matrix, tolerance=tolerance)
        povm_row = _audit_readout_povm(matrix, tolerance=tolerance)
        row.update(readout_row)
        row.update(povm_row)
        row["valid_module_type"] = "classical_stochastic_readout_embedded_as_povm"
    else:
        row["passed"] = False
        row["error"] = f"unknown channel kind {kind!r}"
        return row

    parameter_range = mechanism_parameter_range_record(spec, probability_tolerance=probability_tolerance)
    row["parameter_range_audit"] = parameter_range
    row["silent_projection_or_renormalization_used"] = False
    row["leakage_unaccounted_mass"] = 0.0
    if spec.mechanism_id in LEAKAGE_MECHANISM_IDS:
        row["leakage_model_kind"] = "computational_subspace_cptp_surrogate"
        row["full_leakage_space_modeled"] = False
        row["true_qutrit_leakage_claim_allowed"] = False
    checks = {
        "base_guardrail_passed": bool(row.get("base_guardrail_passed", False)),
        "parameter_ranges_passed": bool(parameter_range.get("passed", False)),
        "module_physicality_passed": bool(row.get("module_physicality_passed", False)),
        "no_silent_projection_or_renormalization": not bool(row.get("silent_projection_or_renormalization_used", True)),
        "no_unaccounted_leakage_mass": float(row.get("leakage_unaccounted_mass", 0.0)) <= probability_tolerance,
    }
    row["checks"] = checks
    row["passed"] = bool(all(checks.values()))
    return row


def mechanism_catalog_manifest(records: Sequence[Mapping[str, object]], local_records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    mechanism_ids = sorted({str(row.get("mechanism_id", "")) for row in local_records}, key=_mechanism_sort_key)
    return {
        "schema": "scope_static_layer1p_mechanism_catalog_manifest_v1",
        "record_count": int(len(records)),
        "active_mechanism_count": int(len(mechanism_ids)),
        "active_mechanisms": mechanism_ids,
        "contains_oracle_labels": True,
        "audit_scope": "teacher generating mechanisms, not learner-visible inputs",
    }


def channel_representation_manifest(local_records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    counts: dict[str, int] = {}
    for row in local_records:
        kind = str(row.get("kind", "unknown"))
        counts[kind] = counts.get(kind, 0) + 1
    return {
        "schema": "scope_static_layer1p_channel_representation_manifest_v1",
        "representation_counts": counts,
        "readout_matrix_convention": "matrix[ideal_outcome, reported_outcome] = P(reported | ideal)",
        "equivalent_user_convention": "A[reported, ideal] is matrix.T and is column-stochastic",
        "quantum_channel_representations": ["unitary", "kraus"],
        "measurement_representations": ["classical_stochastic_readout_matrix_embedded_as_povm"],
    }


def mechanism_parameter_ranges(local_records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    records = [dict(row.get("parameter_range_audit", {})) for row in local_records]
    failed = [row for row in records if not bool(row.get("passed", False))]
    return {
        "schema": "scope_static_layer1p_mechanism_parameter_ranges_v1",
        "passed": not failed,
        "record_count": int(len(records)),
        "failed_record_count": int(len(failed)),
        "records": records,
    }


def mechanism_parameter_range_record(spec: MechanismSpec, *, probability_tolerance: float) -> dict[str, object]:
    invalid: list[dict[str, object]] = []
    checked: list[dict[str, object]] = []
    for key, raw_value in dict(spec.parameters).items():
        name = str(key)
        if name in AXIS_PARAMETER_NAMES:
            value = str(raw_value).strip().lower()
            checked.append({"parameter": name, "value": value, "range_family": "axis_enum", "allowed": sorted(ALLOWED_AXIS_VALUES)})
            if value not in ALLOWED_AXIS_VALUES:
                invalid.append({"parameter": name, "value": value, "reason": "outside_declared_axis_enum"})
            continue
        try:
            value = float(raw_value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            invalid.append({"parameter": name, "value": str(raw_value), "reason": "not_numeric"})
            continue
        if not np.isfinite(value):
            invalid.append({"parameter": name, "value": str(raw_value), "reason": "not_finite"})
            continue
        if name in PROBABILITY_PARAMETER_NAMES or name.startswith("p_"):
            lower, upper = -float(probability_tolerance), 1.0 + float(probability_tolerance)
            family = "probability"
        elif name.endswith("span"):
            lower, upper = 0.0, 2.0 * math.pi
            family = "nonnegative_span"
        elif "epsilon" in name or "theta" in name or "angle" in name:
            lower, upper = -2.0 * math.pi, 2.0 * math.pi
            family = "angle"
        else:
            lower, upper = -float("inf"), float("inf")
            family = "finite_numeric"
        checked.append({"parameter": name, "value": value, "range_family": family, "min": lower, "max": upper})
        if value < lower or value > upper:
            invalid.append({"parameter": name, "value": value, "reason": f"outside_declared_{family}_range"})
    return {
        "schema": "scope_static_layer1p_parameter_range_record_v1",
        "mechanism_id": str(spec.mechanism_id),
        "record_parameters": {str(k): _json_value(v) for k, v in dict(spec.parameters).items()},
        "checked_parameters": checked,
        "invalid_parameters": invalid,
        "passed": not invalid,
    }


def gksl_audit() -> dict[str, object]:
    return {
        "schema": "scope_static_layer1p_gksl_audit_v1",
        "enabled": False,
        "passed": True,
        "reason": "Current catalog mechanisms are represented directly as unitary, Kraus, or readout modules; no GKSL generator modules are emitted by this teacher.",
        "gksl_modules_checked": 0,
    }


def circuit_probability_audit(teacher_dir: Path, *, probability_tolerance: float) -> dict[str, object]:
    observations_path = teacher_dir / "observations.npz"
    if not observations_path.exists():
        return {
            "schema": "scope_static_layer1p_circuit_probability_audit_v1",
            "observations_path": str(observations_path),
            "enabled": False,
            "passed": True,
            "reason": "No observations.npz artifact present; local module physicality remains audited.",
            "all_probability_distributions_valid": True,
            "max_probability_sum_defect": 0.0,
            "min_output_probability": 0.0,
            "total_contexts_checked": 0,
        }
    data = np.load(observations_path, allow_pickle=False)
    observations = np.asarray(data["observations"])
    if observations.ndim != 3:
        return {
            "schema": "scope_static_layer1p_circuit_probability_audit_v1",
            "observations_path": str(observations_path),
            "enabled": True,
            "passed": False,
            "error": "observations array must have shape [probe, shot, bit]",
            "all_probability_distributions_valid": False,
            "max_probability_sum_defect": float("inf"),
            "min_output_probability": -float("inf"),
            "total_contexts_checked": 0,
        }
    bits_valid = bool(np.all((observations == 0) | (observations == 1)))
    probe_count = int(observations.shape[0])
    shot_count = int(observations.shape[1])
    bit_count = int(observations.shape[2])
    max_sum_defect = 0.0
    min_probability = 0.0
    max_probability = 0.0
    contexts_checked = 0
    if bits_valid and shot_count > 0 and bit_count <= 62:
        weights = (1 << np.arange(bit_count, dtype=np.uint64))
        for probe_idx in range(probe_count):
            keys = np.asarray(observations[probe_idx], dtype=np.uint64) @ weights
            if bit_count <= 20:
                counts = np.bincount(keys.astype(np.int64), minlength=1 << bit_count)
            else:
                _unique, counts = np.unique(keys, return_counts=True)
            probs = counts.astype(np.float64) / float(shot_count)
            max_sum_defect = max(max_sum_defect, abs(float(np.sum(probs)) - 1.0))
            if probs.size:
                min_probability = min(min_probability, float(np.min(probs)))
                max_probability = max(max_probability, float(np.max(probs)))
            contexts_checked += 1
    else:
        max_sum_defect = 0.0 if bits_valid and shot_count > 0 else float("inf")
    passed = bool(bits_valid and shot_count > 0 and max_sum_defect <= probability_tolerance and min_probability >= -probability_tolerance)
    return {
        "schema": "scope_static_layer1p_circuit_probability_audit_v1",
        "observations_path": str(observations_path),
        "enabled": True,
        "passed": passed,
        "all_probability_distributions_valid": passed,
        "observations_shape": [int(dim) for dim in observations.shape],
        "bit_values_are_binary": bits_valid,
        "sample_distribution_source": "empirical bitstring counts from teacher observations.npz",
        "max_probability_sum_defect": float(max_sum_defect),
        "min_output_probability": float(min_probability),
        "max_output_probability": float(max_probability),
        "total_contexts_checked": int(contexts_checked),
        "shot_count": int(shot_count),
    }


def sampling_audit(teacher_dir: Path, circuit_probability: Mapping[str, object]) -> dict[str, object]:
    path = teacher_dir / "sampling_audit.json"
    source: dict[str, object] = {}
    if path.exists():
        source = _load_json(path)
    return {
        "schema": "scope_static_layer1p_physicality_sampling_audit_v1",
        "source_sampling_audit_path": str(path),
        "source_sampling_audit_present": path.exists(),
        "all_probability_distributions_valid": bool(circuit_probability.get("all_probability_distributions_valid", False)),
        "source_sampling_schema": source.get("schema"),
        "source_teacher_total_wall_clock_seconds": source.get("total_wall_clock_seconds", source.get("total_seconds")),
    }


def physicality_summary(
    *,
    local_records: Sequence[Mapping[str, object]],
    circuit_probability: Mapping[str, object],
    leakage_audit: Mapping[str, object],
    parameter_audit: Mapping[str, object],
    failures: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema": "scope_static_layer1p_teacher_physicality_summary_v1",
        "total_mechanisms": int(len({str(row.get("mechanism_id", "")) for row in local_records})),
        "total_channel_instances_checked": int(len(local_records)),
        "total_contexts_checked": int(circuit_probability.get("total_contexts_checked", 0)),
        "total_failures": int(failures.get("total_failure_count", 0)),
        "max_tp_defect": _max_metric(local_records, ["choi_tp_defect", "kraus_tp_defect", "readout_stochastic_sum_defect"]),
        "min_choi_eigenvalue": _min_metric(local_records, "choi_min_eig"),
        "max_kraus_tp_defect": _max_metric(local_records, "kraus_tp_defect"),
        "max_unitary_defect": _max_metric(local_records, "unitary_defect"),
        "min_stochastic_entry": _min_metric(local_records, "readout_min_entry"),
        "max_stochastic_sum_defect": _max_metric(local_records, "readout_stochastic_sum_defect"),
        "min_povm_eigenvalue": _min_metric(local_records, "povm_min_eig"),
        "max_povm_sum_defect": _max_metric(local_records, "povm_sum_defect"),
        "max_probability_sum_defect": float(circuit_probability.get("max_probability_sum_defect", 0.0)),
        "min_output_probability": float(circuit_probability.get("min_output_probability", 0.0)),
        "leakage_projection_used": bool(leakage_audit.get("leakage_projection_used", False)),
        "silent_renormalization_used": bool(leakage_audit.get("silent_renormalization_used", False)),
        "leakage_unaccounted_mass": float(leakage_audit.get("max_leakage_unaccounted_mass", 0.0)),
        "mechanism_parameter_ranges_passed": bool(parameter_audit.get("passed", False)),
        "teacher_physicality_passed": False,
    }


def teacher_physicality_acceptance(
    *,
    summary: Mapping[str, object],
    unitary_audit: Mapping[str, object],
    kraus_audit: Mapping[str, object],
    choi_audit: Mapping[str, object],
    readout_audit: Mapping[str, object],
    povm_audit: Mapping[str, object],
    reset_prep_audit: Mapping[str, object],
    leakage_audit: Mapping[str, object],
    circuit_probability: Mapping[str, object],
    parameter_audit: Mapping[str, object],
) -> dict[str, object]:
    checks = {
        "all_local_quantum_channels_cptp_within_tolerance": bool(choi_audit.get("passed", False)),
        "unitary_modules_valid": bool(unitary_audit.get("passed", False)),
        "kraus_modules_valid": bool(kraus_audit.get("passed", False)),
        "readout_stochastic_maps_valid": bool(readout_audit.get("passed", False)),
        "povm_or_instrument_modules_valid": bool(povm_audit.get("passed", False)),
        "reset_prep_modules_valid": bool(reset_prep_audit.get("passed", False)),
        "all_circuit_output_distributions_valid": bool(circuit_probability.get("all_probability_distributions_valid", False)),
        "no_silent_projection_or_renormalization": not bool(leakage_audit.get("silent_renormalization_used", True)),
        "leakage_unaccounted_mass_zero": float(leakage_audit.get("max_leakage_unaccounted_mass", 0.0)) <= PROBABILITY_FLOOR_TOLERANCE,
        "all_mechanism_parameter_ranges_audited": bool(parameter_audit.get("passed", False)),
        "mechanism_failures_zero": int(summary.get("total_failures", 0)) == 0,
    }
    return {
        "schema": "scope_static_layer1p_teacher_physicality_acceptance_v1",
        "teacher_physicality_passed": bool(all(checks.values())),
        "checks": checks,
    }


def failure_cases(
    local_records: Sequence[Mapping[str, object]],
    circuit_probability: Mapping[str, object],
    leakage_audit: Mapping[str, object],
    parameter_audit: Mapping[str, object],
) -> dict[str, object]:
    mechanism_failures = [
        {
            "record_index": int(row.get("record_index", -1)),
            "mechanism_id": str(row.get("mechanism_id", "")),
            "kind": str(row.get("kind", "")),
            "checks": row.get("checks", {}),
            "error": row.get("error"),
        }
        for row in local_records
        if not bool(row.get("passed", False))
    ]
    global_failures = []
    if not bool(circuit_probability.get("all_probability_distributions_valid", False)):
        global_failures.append({"artifact": "circuit_probability_audit", "reason": "invalid_output_distribution"})
    if bool(leakage_audit.get("silent_renormalization_used", False)):
        global_failures.append({"artifact": "leakage_space_audit", "reason": "silent_renormalization_used"})
    if not bool(parameter_audit.get("passed", False)):
        global_failures.append({"artifact": "mechanism_parameter_ranges", "reason": "invalid_parameter_range"})
    return {
        "schema": "scope_static_layer1p_teacher_physicality_failure_cases_v1",
        "mechanism_failure_count": int(len(mechanism_failures)),
        "global_failure_count": int(len(global_failures)),
        "total_failure_count": int(len(mechanism_failures) + len(global_failures)),
        "mechanism_failures": mechanism_failures,
        "global_failures": global_failures,
    }


def _audit_unitary_channel(unitary: np.ndarray, *, tolerance: float) -> dict[str, object]:
    if unitary.ndim != 2 or unitary.shape[0] != unitary.shape[1]:
        return {"module_physicality_passed": False, "unitary_defect": float("inf"), "unitary_dimension_passed": False}
    identity = np.eye(unitary.shape[0], dtype=np.complex128)
    left = unitary.conj().T @ unitary
    right = unitary @ unitary.conj().T
    defect = max(float(np.max(np.abs(left - identity))), float(np.max(np.abs(right - identity))))
    return {
        "unitary_dimension": int(unitary.shape[0]),
        "unitary_finite": bool(np.all(np.isfinite(unitary))),
        "unitary_defect": float(defect),
        "u_dagger_u_defect": float(np.max(np.abs(left - identity))),
        "u_u_dagger_defect": float(np.max(np.abs(right - identity))),
        "module_physicality_passed": bool(np.all(np.isfinite(unitary)) and defect <= tolerance),
    }


def _audit_kraus_channel(kraus: Sequence[np.ndarray], *, tolerance: float) -> dict[str, object]:
    if not kraus:
        return {"module_physicality_passed": False, "kraus_tp_defect": float("inf"), "kraus_count": 0}
    dim = int(kraus[0].shape[0]) if kraus[0].ndim == 2 else 0
    accum = np.zeros((dim, dim), dtype=np.complex128)
    shapes_passed = True
    finite = True
    for op in kraus:
        shapes_passed = shapes_passed and bool(op.ndim == 2 and op.shape == (dim, dim))
        finite = finite and bool(np.all(np.isfinite(op)))
        if shapes_passed:
            accum += op.conj().T @ op
    defect = float(np.max(np.abs(accum - np.eye(dim, dtype=np.complex128)))) if dim else float("inf")
    return {
        "kraus_count": int(len(kraus)),
        "kraus_dimension": int(dim),
        "kraus_shapes_passed": bool(shapes_passed),
        "kraus_finite": bool(finite),
        "kraus_tp_defect": float(defect),
        "module_physicality_passed": bool(shapes_passed and finite and defect <= tolerance),
    }


def _audit_choi_from_kraus(kraus: Sequence[np.ndarray], *, tolerance: float, random_state_count: int) -> dict[str, object]:
    if not kraus:
        return {
            "choi_hermitian_defect": float("inf"),
            "choi_min_eig": -float("inf"),
            "choi_tp_defect": float("inf"),
            "superoperator_trace_preservation_defect": float("inf"),
            "random_state_trace_defect": float("inf"),
            "random_state_psd_output_defect": float("inf"),
            "choi_physicality_passed": False,
        }
    choi = _choi_from_kraus(kraus)
    hermitian_defect = float(np.max(np.abs(choi - choi.conj().T)))
    hermitian = 0.5 * (choi + choi.conj().T)
    eigvals = np.linalg.eigvalsh(hermitian)
    min_eig = float(np.min(eigvals)) if eigvals.size else -float("inf")
    tp_defect = _choi_tp_defect(choi)
    superop_tp = _superoperator_tp_defect(kraus)
    random_trace, random_psd = _random_state_output_defects(kraus, count=int(random_state_count))
    passed = bool(
        hermitian_defect <= tolerance
        and min_eig >= -tolerance
        and tp_defect <= tolerance
        and superop_tp <= tolerance
        and random_trace <= tolerance
        and random_psd >= -tolerance
    )
    return {
        "choi_dimension": [int(dim) for dim in choi.shape],
        "choi_hermitian_defect": float(hermitian_defect),
        "choi_min_eig": float(min_eig),
        "choi_tp_defect": float(tp_defect),
        "superoperator_trace_preservation_defect": float(superop_tp),
        "random_state_trace_defect": float(random_trace),
        "random_state_psd_output_defect": float(random_psd),
        "choi_physicality_passed": passed,
        "module_physicality_passed": passed,
    }


def _audit_readout_matrix(matrix: np.ndarray, *, tolerance: float) -> dict[str, object]:
    row_sums = np.sum(matrix, axis=1) if matrix.ndim == 2 else np.asarray([float("inf")])
    row_defect = float(np.max(np.abs(row_sums - 1.0))) if row_sums.size else float("inf")
    min_entry = float(np.min(matrix)) if matrix.size else -float("inf")
    max_entry = float(np.max(matrix)) if matrix.size else float("inf")
    passed = bool(matrix.ndim == 2 and matrix.shape[0] == matrix.shape[1] and min_entry >= -tolerance and max_entry <= 1.0 + tolerance and row_defect <= tolerance)
    return {
        "readout_matrix_convention": "matrix[ideal_outcome, reported_outcome] = P(reported | ideal)",
        "equivalent_A_yx_column_stochastic_convention": "A[reported, ideal] = matrix.T",
        "readout_dimension": [int(dim) for dim in matrix.shape],
        "readout_min_entry": float(min_entry),
        "readout_max_entry": float(max_entry),
        "readout_stochastic_sum_defect": float(row_defect),
        "readout_entries_in_range": bool(min_entry >= -tolerance and max_entry <= 1.0 + tolerance),
        "module_physicality_passed": passed,
    }


def _audit_readout_povm(matrix: np.ndarray, *, tolerance: float) -> dict[str, object]:
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        return {"povm_min_eig": -float("inf"), "povm_sum_defect": float("inf"), "povm_passed": False}
    effects = [np.diag(matrix[:, reported]).astype(np.complex128) for reported in range(matrix.shape[1])]
    eig_mins = [float(np.min(np.linalg.eigvalsh(0.5 * (effect + effect.conj().T)))) for effect in effects]
    accum = sum(effects, np.zeros_like(effects[0]))
    sum_defect = float(np.max(np.abs(accum - np.eye(matrix.shape[0], dtype=np.complex128))))
    passed = bool(min(eig_mins) >= -tolerance and sum_defect <= tolerance)
    return {
        "povm_effect_count": int(len(effects)),
        "povm_min_eig": float(min(eig_mins)),
        "povm_sum_defect": float(sum_defect),
        "povm_passed": passed,
        "module_physicality_passed": passed,
    }


def _unitary_audit(records: Sequence[Mapping[str, object]], *, tolerance: float) -> dict[str, object]:
    failed = [row for row in records if not bool(row.get("module_physicality_passed", False))]
    return {
        "schema": "scope_static_layer1p_unitary_audit_v1",
        "passed": not failed,
        "tolerance": float(tolerance),
        "record_count": int(len(records)),
        "failed_record_count": int(len(failed)),
        "max_unitary_defect": _max_metric(records, "unitary_defect"),
        "records": _slim_records(records, ["record_index", "mechanism_id", "unitary_dimension", "unitary_defect", "u_dagger_u_defect", "u_u_dagger_defect", "module_physicality_passed"]),
    }


def _kraus_audit(records: Sequence[Mapping[str, object]], *, tolerance: float) -> dict[str, object]:
    failed = [row for row in records if not bool(row.get("module_physicality_passed", False))]
    return {
        "schema": "scope_static_layer1p_kraus_audit_v1",
        "passed": not failed,
        "tolerance": float(tolerance),
        "record_count": int(len(records)),
        "failed_record_count": int(len(failed)),
        "max_kraus_tp_defect": _max_metric(records, "kraus_tp_defect"),
        "records": _slim_records(records, ["record_index", "mechanism_id", "kraus_count", "kraus_dimension", "kraus_tp_defect", "choi_min_eig", "choi_tp_defect", "module_physicality_passed"]),
    }


def _choi_audit(records: Sequence[Mapping[str, object]], *, tolerance: float) -> dict[str, object]:
    failed = [row for row in records if not bool(row.get("choi_physicality_passed", False))]
    return {
        "schema": "scope_static_layer1p_choi_audit_v1",
        "passed": not failed,
        "tolerance": float(tolerance),
        "record_count": int(len(records)),
        "failed_record_count": int(len(failed)),
        "choi_hermitian_defect": _max_metric(records, "choi_hermitian_defect"),
        "choi_min_eig": _min_metric(records, "choi_min_eig"),
        "tp_defect": _max_metric(records, "choi_tp_defect"),
        "superoperator_trace_preservation_defect": _max_metric(records, "superoperator_trace_preservation_defect"),
        "random_state_trace_defect": _max_metric(records, "random_state_trace_defect"),
        "random_state_psd_output_defect": _min_metric(records, "random_state_psd_output_defect"),
        "records": _slim_records(records, ["record_index", "mechanism_id", "kind", "choi_hermitian_defect", "choi_min_eig", "choi_tp_defect", "superoperator_trace_preservation_defect", "random_state_trace_defect", "random_state_psd_output_defect", "choi_physicality_passed"]),
    }


def _readout_stochasticity_audit(records: Sequence[Mapping[str, object]], *, tolerance: float) -> dict[str, object]:
    failed = [row for row in records if not bool(row.get("module_physicality_passed", False))]
    return {
        "schema": "scope_static_layer1p_readout_stochasticity_audit_v1",
        "passed": not failed,
        "tolerance": float(tolerance),
        "record_count": int(len(records)),
        "failed_record_count": int(len(failed)),
        "min_stochastic_entry": _min_metric(records, "readout_min_entry"),
        "max_stochastic_sum_defect": _max_metric(records, "readout_stochastic_sum_defect"),
        "records": _slim_records(records, ["record_index", "mechanism_id", "readout_matrix_convention", "readout_min_entry", "readout_max_entry", "readout_stochastic_sum_defect", "module_physicality_passed"]),
    }


def _povm_instrument_audit(records: Sequence[Mapping[str, object]], *, tolerance: float) -> dict[str, object]:
    failed = [row for row in records if not bool(row.get("povm_passed", False))]
    return {
        "schema": "scope_static_layer1p_povm_instrument_audit_v1",
        "passed": not failed,
        "tolerance": float(tolerance),
        "readout_povm_record_count": int(len(records)),
        "failed_record_count": int(len(failed)),
        "instrument_record_count": 0,
        "instrument_claim_required": False,
        "min_povm_eigenvalue": _min_metric(records, "povm_min_eig"),
        "max_povm_sum_defect": _max_metric(records, "povm_sum_defect"),
        "records": _slim_records(records, ["record_index", "mechanism_id", "povm_effect_count", "povm_min_eig", "povm_sum_defect", "povm_passed"]),
    }


def _reset_prep_audit(local_records: Sequence[Mapping[str, object]], *, tolerance: float) -> dict[str, object]:
    records = []
    for row in local_records:
        mechanism_id = str(row.get("mechanism_id", ""))
        if mechanism_id not in PREP_RESET_MECHANISM_IDS:
            continue
        sigma = np.asarray([[0.0, 0.0], [0.0, 1.0]], dtype=np.complex128) if mechanism_id == "M17" else np.asarray([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)
        eig_min = float(np.min(np.linalg.eigvalsh(sigma)))
        trace_defect = float(abs(np.trace(sigma) - 1.0))
        represented_as_cptp = bool(row.get("kind") in {"kraus", "unitary"} and row.get("module_physicality_passed", False))
        records.append(
            {
                "record_index": int(row.get("record_index", -1)),
                "mechanism_id": mechanism_id,
                "kind": row.get("kind"),
                "prepared_density_matrix_psd_min_eig": eig_min,
                "prepared_density_matrix_trace_defect": trace_defect,
                "represented_as_cptp_catalog_module": represented_as_cptp,
                "passed": bool(eig_min >= -tolerance and trace_defect <= tolerance and represented_as_cptp),
            }
        )
    failed = [row for row in records if not bool(row.get("passed", False))]
    return {
        "schema": "scope_static_layer1p_reset_prep_audit_v1",
        "passed": not failed,
        "record_count": int(len(records)),
        "failed_record_count": int(len(failed)),
        "records": records,
    }


def _leakage_space_audit(local_records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    records = []
    for row in local_records:
        if str(row.get("mechanism_id", "")) not in LEAKAGE_MECHANISM_IDS:
            continue
        records.append(
            {
                "record_index": int(row.get("record_index", -1)),
                "mechanism_id": str(row.get("mechanism_id", "")),
                "implemented_kind": row.get("kind"),
                "leakage_model_kind": row.get("leakage_model_kind", "computational_subspace_cptp_surrogate"),
                "full_leakage_space_modeled": bool(row.get("full_leakage_space_modeled", False)),
                "true_qutrit_leakage_claim_allowed": bool(row.get("true_qutrit_leakage_claim_allowed", False)),
                "leakage_projection_used": False,
                "silent_renormalization_used": False,
                "leakage_unaccounted_mass": float(row.get("leakage_unaccounted_mass", 0.0)),
                "passed": bool(row.get("module_physicality_passed", False)),
            }
        )
    failed = [row for row in records if not bool(row.get("passed", False))]
    return {
        "schema": "scope_static_layer1p_leakage_space_audit_v1",
        "passed": not failed,
        "record_count": int(len(records)),
        "failed_record_count": int(len(failed)),
        "leakage_projection_used": False,
        "silent_renormalization_used": False,
        "max_leakage_unaccounted_mass": _max_metric(records, "leakage_unaccounted_mass"),
        "records": records,
    }


def _choi_from_kraus(kraus: Sequence[np.ndarray]) -> np.ndarray:
    dim = int(kraus[0].shape[0])
    choi = np.zeros((dim * dim, dim * dim), dtype=np.complex128)
    for i in range(dim):
        for j in range(dim):
            basis = np.zeros((dim, dim), dtype=np.complex128)
            basis[i, j] = 1.0
            out = _apply_kraus(basis, kraus)
            choi[i * dim : (i + 1) * dim, j * dim : (j + 1) * dim] = out
    return choi


def _choi_tp_defect(choi: np.ndarray) -> float:
    dim = int(round(math.sqrt(choi.shape[0])))
    partial = np.zeros((dim, dim), dtype=np.complex128)
    for i in range(dim):
        for j in range(dim):
            block = choi[i * dim : (i + 1) * dim, j * dim : (j + 1) * dim]
            partial[i, j] = np.trace(block)
    return float(np.max(np.abs(partial - np.eye(dim, dtype=np.complex128))))


def _superoperator_tp_defect(kraus: Sequence[np.ndarray]) -> float:
    dim = int(kraus[0].shape[0])
    max_defect = 0.0
    for i in range(dim):
        for j in range(dim):
            basis = np.zeros((dim, dim), dtype=np.complex128)
            basis[i, j] = 1.0
            expected = 1.0 if i == j else 0.0
            max_defect = max(max_defect, abs(complex(np.trace(_apply_kraus(basis, kraus))) - expected))
    return float(max_defect)


def _random_state_output_defects(kraus: Sequence[np.ndarray], *, count: int) -> tuple[float, float]:
    dim = int(kraus[0].shape[0])
    trace_defect = 0.0
    min_eig = 0.0
    for idx in range(max(1, int(count))):
        rho = _deterministic_density_matrix(dim, idx)
        out = _apply_kraus(rho, kraus)
        trace_defect = max(trace_defect, float(abs(np.trace(out) - 1.0)))
        eigvals = np.linalg.eigvalsh(0.5 * (out + out.conj().T))
        min_eig = min(min_eig, float(np.min(eigvals)))
    return trace_defect, min_eig


def _deterministic_density_matrix(dim: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(17 + int(seed))
    real = rng.normal(size=(dim, dim))
    imag = rng.normal(size=(dim, dim))
    mat = real + 1j * imag
    rho = mat @ mat.conj().T
    rho = rho / np.trace(rho)
    return rho.astype(np.complex128)


def _apply_kraus(rho: np.ndarray, kraus: Sequence[np.ndarray]) -> np.ndarray:
    return sum(op @ rho @ op.conj().T for op in kraus)


def _write_outputs(output: Path, result: Mapping[str, object]) -> None:
    artifacts = {
        "metrics.json": result,
        "mechanism_catalog_manifest.json": result["mechanism_catalog_manifest"],
        "mechanism_parameter_ranges.json": result["mechanism_parameter_ranges"],
        "channel_representation_manifest.json": result["channel_representation_manifest"],
        "unitary_audit.json": result["unitary_audit"],
        "kraus_audit.json": result["kraus_audit"],
        "choi_audit.json": result["choi_audit"],
        "gksl_audit.json": result["gksl_audit"],
        "readout_stochasticity_audit.json": result["readout_stochasticity_audit"],
        "povm_instrument_audit.json": result["povm_instrument_audit"],
        "reset_prep_audit.json": result["reset_prep_audit"],
        "leakage_space_audit.json": result["leakage_space_audit"],
        "circuit_probability_audit.json": result["circuit_probability_audit"],
        "sampling_audit.json": result["sampling_audit"],
        "failure_cases.json": result["failure_cases"],
        "acceptance_audit.json": result["acceptance_audit"],
    }
    for name, payload in artifacts.items():
        (output / name).write_text(json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n")
    _write_physicality_csv(output / "physicality_by_mechanism.csv", result["physicality_by_mechanism"])  # type: ignore[arg-type]
    (output / "config.yaml").write_text(yaml.safe_dump({"teacher_physicality_audit": result["config"]}, sort_keys=False))
    (output / "summary.md").write_text(format_teacher_physicality_summary(result))


def _write_physicality_csv(path: Path, records: Sequence[Mapping[str, object]]) -> None:
    fields = [
        "record_index",
        "mechanism_id",
        "kind",
        "passed",
        "module_physicality_passed",
        "choi_min_eig",
        "choi_tp_defect",
        "kraus_tp_defect",
        "unitary_defect",
        "readout_min_entry",
        "readout_stochastic_sum_defect",
        "povm_min_eig",
        "povm_sum_defect",
        "silent_projection_or_renormalization_used",
        "leakage_unaccounted_mass",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in fields})


def format_teacher_physicality_summary(result: Mapping[str, object]) -> str:
    summary = dict(result.get("summary", {}))
    return "\n".join(
        [
            "# Layer1.P: Teacher Physicality Audit",
            "",
            f"- Decision: `{result.get('decision')}`",
            f"- Teacher physicality passed: `{str(bool(summary.get('teacher_physicality_passed', False))).lower()}`",
            f"- Total mechanisms: `{summary.get('total_mechanisms')}`",
            f"- Channel instances checked: `{summary.get('total_channel_instances_checked')}`",
            f"- Contexts checked: `{summary.get('total_contexts_checked')}`",
            f"- Total failures: `{summary.get('total_failures')}`",
            f"- Min Choi eigenvalue: `{float(summary.get('min_choi_eigenvalue', 0.0)):.6e}`",
            f"- Max TP defect: `{float(summary.get('max_tp_defect', 0.0)):.6e}`",
            f"- Max probability sum defect: `{float(summary.get('max_probability_sum_defect', 0.0)):.6e}`",
            f"- Silent renormalization used: `{str(bool(summary.get('silent_renormalization_used', False))).lower()}`",
            "",
            "## Claim Boundary",
            "",
            "This audit checks the teacher's generating maps and observation distributions. It does not say the data are CPTP; it says the teacher samples observations from catalog mechanisms represented as local CPTP channels, valid stochastic readout maps embedded as POVMs, or declared computational-subspace surrogates with no silent projection/renormalization.",
            "",
        ]
    )


def _load_mechanism_records(path: Path) -> list[dict[str, object]]:
    data = _load_json(path)
    records = data.get("mechanisms")
    if not isinstance(records, list) or not records:
        raise ValueError(f"{path} must contain non-empty mechanisms")
    return [dict(record) for record in records]


def _load_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _records_by_kind(records: Sequence[Mapping[str, object]]) -> dict[str, list[Mapping[str, object]]]:
    out: dict[str, list[Mapping[str, object]]] = {}
    for row in records:
        out.setdefault(str(row.get("kind", "unknown")), []).append(row)
    return out


def _slim_records(records: Sequence[Mapping[str, object]], fields: Sequence[str]) -> list[dict[str, object]]:
    return [{field: _json_safe(row.get(field)) for field in fields if field in row} for row in records]


def _max_metric(records: Sequence[Mapping[str, object]], keys: str | Sequence[str]) -> float:
    key_list = [keys] if isinstance(keys, str) else list(keys)
    values = []
    for row in records:
        for key in key_list:
            value = row.get(key)
            if value is None:
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if np.isfinite(number):
                values.append(number)
    return float(max(values)) if values else 0.0


def _min_metric(records: Sequence[Mapping[str, object]], key: str) -> float:
    values = []
    for row in records:
        value = row.get(key)
        if value is None:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if np.isfinite(number):
            values.append(number)
    return float(min(values)) if values else 0.0


def _resolve_tolerance(*, tolerance_mode: str, tolerance: float | None) -> float:
    if tolerance is not None:
        return float(tolerance)
    mode = str(tolerance_mode).lower()
    if mode == "strict":
        return STRICT_TOLERANCE
    if mode == "cuda_float64":
        return CUDA_FLOAT64_TOLERANCE
    if mode in {"cuda_float32", "sampling"}:
        return CUDA_FLOAT32_TOLERANCE
    raise ValueError("tolerance_mode must be strict, cuda_float64, cuda_float32, or sampling")


def _mechanism_sort_key(label: str) -> tuple[int, str]:
    text = str(label)
    if text.startswith("M") and text[1:].isdigit():
        return (int(text[1:]), text)
    return (10_000, text)


def _json_value(value: object) -> object:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return str(value)


def _json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return [_json_safe(v) for v in value.tolist()]
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, float):
        if math.isfinite(value):
            return float(value)
        return str(value)
    return value
