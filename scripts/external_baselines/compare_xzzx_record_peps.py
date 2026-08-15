#!/usr/bin/env python3
"""Registered metrics for the bounded XZZX PEPS trajectory experiment."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping, Sequence

import numpy as np


RESULT_SCHEMA = "error_coupling_simulator.external_xzzx_record_peps.comparison.v1"
BRANCH_SCHEMA = "error_coupling_simulator.external_xzzx_record_peps.branch.v1"
EXACT_REFERENCE_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_exact_data_reference.v1"
)
DENSE_REFERENCE_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_dense_reference.v1"
)
PRETERMINAL_CHECKPOINT = (
    "after_round_1_ry_before_terminal_data_measurements"
)
REFERENCE_SCHEMAS = {EXACT_REFERENCE_SCHEMA}
CANDIDATE_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_quimb_candidate.v1"
)
BRANCH_AUTHORITY_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_exact_data_reference."
    "branch_authority.v1"
)
CANDIDATE_BRANCH_FIELDS = {
    "schema",
    "fixture_sha256",
    "run_spec_sha256",
    "distance",
    "rounds",
    "branch_id",
    "outcomes",
}
FIXTURE_POLICIES = {
    2: {
        "fixture_sha256": (
            "dbf2a0979c9a4cd0a95f2afe393083d97a27ea1e90720596352a191010beb0f5"
        ),
        "run_spec_sha256": (
            "02aef76a65383fbfec9a2f3e0b62a7dd0691a574ee739a4b6b33326ba13681ca"
        ),
        "num_measurements": 10,
        "num_detectors": 5,
        "num_observables": 1,
    },
    3: {
        "fixture_sha256": (
            "3b2bf7d81f7241e0a3b6abb14c76474c362e696cf374c55e20e3d121946bbf3c"
        ),
        "run_spec_sha256": (
            "7dfa0a8ef9620712e6ea190aeda651c681295f9841963ce77686640255cc22a9"
        ),
        "num_qubits": 17,
        "num_measurements": 25,
        "num_resets": 16,
        "num_ancillas": 8,
        "ancillas": [1, 5, 7, 9, 10, 12, 14, 16],
        "state_size": 1 << 17,
        "state_scope": "all_active_qubits",
    },
    5: {
        "fixture_sha256": (
            "659fda875a91f2a6e3c64f8f03487b5a431edecb9849dd897bf2e6f390583495"
        ),
        "run_spec_sha256": (
            "06151ea1244495475259d40bf6ca7ad16cbdaf5f8184ee61b344fb2e81b413a4"
        ),
        "num_qubits": 49,
        "num_measurements": 73,
        "num_resets": 48,
        "num_ancillas": 24,
        "ancillas": [
            1,
            4,
            8,
            10,
            12,
            14,
            16,
            17,
            19,
            21,
            23,
            25,
            28,
            30,
            32,
            34,
            36,
            37,
            39,
            41,
            43,
            45,
            47,
            48,
        ],
        "state_size": 1 << 25,
        "state_scope": "sorted_data_qubits_after_reset_projection",
    },
}
_SHA256 = re.compile(r"[0-9a-f]{64}")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json_sha256(value: Any) -> str:
    payload = (
        json.dumps(
            value,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _complete_complex128_vector(value: object, *, name: str) -> np.ndarray:
    vector = np.asarray(value)
    if vector.dtype != np.complex128:
        raise ValueError(f"{name} must have dtype complex128")
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError(f"{name} must be a nonempty one-dimensional vector")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain only finite amplitudes")
    return vector


def complete_vector_fidelity(reference: object, candidate: object) -> float:
    """Return normalized pure-state fidelity for two complete state vectors."""

    left = _complete_complex128_vector(reference, name="reference")
    right = _complete_complex128_vector(candidate, name="candidate")
    if left.shape != right.shape:
        raise ValueError("reference and candidate shape mismatch")
    left_norm = float(np.vdot(left, left).real)
    right_norm = float(np.vdot(right, right).real)
    if left_norm <= 0.0 or right_norm <= 0.0:
        raise ValueError("complete vectors must have positive norm")
    overlap = np.vdot(left, right)
    fidelity = float(abs(overlap) ** 2 / (left_norm * right_norm))
    return min(1.0, max(0.0, fidelity))


def _probability_law(
    value: Mapping[str, float],
    *,
    support: Sequence[str],
    name: str,
    normalization_atol: float = 1e-10,
) -> np.ndarray:
    ordered_support = list(support)
    if not ordered_support or len(set(ordered_support)) != len(ordered_support):
        raise ValueError("support must be nonempty and unique")
    if set(value) != set(ordered_support):
        raise ValueError(f"{name} must contain the complete declared support")
    if any(
        isinstance(value[label], bool)
        or not isinstance(value[label], (int, float))
        for label in ordered_support
    ):
        raise ValueError(f"{name} contains a non-numeric probability")
    probabilities = np.asarray(
        [value[label] for label in ordered_support],
        dtype=np.float64,
    )
    if (
        not np.all(np.isfinite(probabilities))
        or np.any(probabilities < 0.0)
        or np.any(probabilities > 1.0)
    ):
        raise ValueError(f"{name} contains an invalid probability")
    if not math.isclose(
        float(probabilities.sum()),
        1.0,
        rel_tol=0.0,
        abs_tol=normalization_atol,
    ):
        raise ValueError(f"{name} must be normalized")
    return probabilities


def raw_trajectory_total_variation(
    reference: Mapping[str, float],
    candidate: Mapping[str, float],
    *,
    support: Sequence[str],
    object_kind: str,
) -> float:
    """Return TV on one declared raw-outcome support, never on Record."""

    if object_kind != "raw_trajectory":
        raise ValueError("raw trajectory TV must not be labelled Record")
    left = _probability_law(reference, support=support, name="reference")
    right = _probability_law(candidate, support=support, name="candidate")
    return 0.5 * float(np.abs(left - right).sum())


def _selected_probability(
    row: Mapping[str, Any],
    *,
    name: str,
    normalization_atol: float,
) -> float:
    bit = row.get("bit")
    if bit not in (0, 1):
        raise ValueError(f"{name} has an invalid selected bit")
    try:
        raw_p0 = row["p0"]
        raw_p1 = row["p1"]
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"{name} must contain numeric p0 and p1") from error
    if (
        isinstance(raw_p0, bool)
        or isinstance(raw_p1, bool)
        or not isinstance(raw_p0, (int, float))
        or not isinstance(raw_p1, (int, float))
    ):
        raise ValueError(f"{name} must contain numeric p0 and p1")
    p0 = float(raw_p0)
    p1 = float(raw_p1)
    if (
        not math.isfinite(p0)
        or not math.isfinite(p1)
        or p0 < 0.0
        or p1 < 0.0
        or p0 > 1.0
        or p1 > 1.0
    ):
        raise ValueError(f"{name} contains an invalid Bernoulli probability")
    if not math.isclose(
        p0 + p1,
        1.0,
        rel_tol=0.0,
        abs_tol=normalization_atol,
    ):
        raise ValueError(f"{name} Bernoulli probabilities are not normalized")
    return p0 if bit == 0 else p1


def selected_branch_metrics(
    reference: Sequence[Mapping[str, Any]],
    candidate: Sequence[Mapping[str, Any]],
    *,
    reference_normalization_atol: float = 1e-12,
    candidate_normalization_atol: float = 1e-10,
) -> dict[str, float]:
    """Compare aligned conditional probabilities along one forced branch."""

    if not reference or len(reference) != len(candidate):
        raise ValueError("reference and candidate branch columns must align")
    reference_selected: list[float] = []
    candidate_selected: list[float] = []
    for index, (reference_row, candidate_row) in enumerate(
        zip(reference, candidate, strict=True)
    ):
        reference_column = reference_row.get("column")
        candidate_column = candidate_row.get("column")
        if (
            not isinstance(reference_column, int)
            or reference_column != candidate_column
            or reference_column != index
        ):
            raise ValueError("reference and candidate column order mismatch")
        if reference_row.get("bit") != candidate_row.get("bit"):
            raise ValueError("reference and candidate selected bit mismatch")
        reference_probability = _selected_probability(
            reference_row,
            name=f"reference column {index}",
            normalization_atol=reference_normalization_atol,
        )
        candidate_probability = _selected_probability(
            candidate_row,
            name=f"candidate column {index}",
            normalization_atol=candidate_normalization_atol,
        )
        if reference_probability < 1e-12:
            raise ValueError("selected reference probability is below 1e-12")
        if candidate_probability == 0.0:
            raise ValueError("selected branch has zero candidate probability")
        reference_selected.append(reference_probability)
        candidate_selected.append(candidate_probability)

    reference_log_mass = math.fsum(math.log(p) for p in reference_selected)
    candidate_log_mass = math.fsum(math.log(p) for p in candidate_selected)
    return {
        "max_probability_error": max(
            abs(left - right)
            for left, right in zip(
                reference_selected,
                candidate_selected,
                strict=True,
            )
        ),
        "log_branch_mass_error": abs(
            candidate_log_mass - reference_log_mass
        ),
        "reference_log_branch_mass": reference_log_mass,
        "candidate_log_branch_mass": candidate_log_mass,
    }


def reset_trace_distance_to_zero(density_matrix: object) -> float:
    """Return one-site trace distance to the reset state ``|0><0|``."""

    rho = np.asarray(density_matrix)
    if rho.dtype != np.complex128:
        raise ValueError("density matrix must have dtype complex128")
    if rho.shape != (2, 2):
        raise ValueError("density matrix must have shape (2, 2)")
    if not np.all(np.isfinite(rho)):
        raise ValueError("density matrix must contain only finite values")
    if not np.allclose(rho, rho.conj().T, rtol=0.0, atol=1e-12):
        raise ValueError("density matrix must be Hermitian")
    trace = np.trace(rho)
    if abs(trace.imag) > 1e-12 or abs(float(trace.real) - 1.0) > 1e-12:
        raise ValueError("density matrix must have trace one")
    if float(np.linalg.eigvalsh(rho).min()) < -1e-12:
        raise ValueError("density matrix must be positive semidefinite")
    reset = np.asarray([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)
    return 0.5 * float(np.abs(np.linalg.eigvalsh(rho - reset)).sum())


def load_complete_state(
    metadata: Mapping[str, Any],
    *,
    expected_axis_order: Sequence[int],
) -> np.ndarray:
    """Load a hash-bound complete vector and reject overlap/proxy summaries."""

    if (
        metadata.get("source_kind")
        != "complete_complex128_state_vector"
    ):
        raise ValueError("state proxy is forbidden; a complete vector is required")
    if metadata.get("dtype") != "complex128":
        raise ValueError("complete state metadata must declare complex128")
    axis_order = list(expected_axis_order)
    if metadata.get("qubit_axis_order") != axis_order:
        raise ValueError("complete state axis order mismatch")
    if metadata.get("q0_bit_significance") != "most_significant":
        raise ValueError("complete state bit-significance convention mismatch")
    state_path = Path(str(metadata.get("path", "")))
    if not state_path.is_absolute() or not state_path.is_file():
        raise ValueError("complete state path must be an existing absolute file")
    if _file_sha256(state_path) != metadata.get("file_sha256"):
        raise ValueError("complete state file hash mismatch")
    state = np.load(state_path, mmap_mode="r", allow_pickle=False)
    expected_shape = (2 ** len(axis_order),)
    if state.dtype != np.complex128:
        raise ValueError("complete state file must have dtype complex128")
    if state.shape != expected_shape or metadata.get("shape") != list(expected_shape):
        raise ValueError("complete state shape mismatch")
    if not np.all(np.isfinite(state)):
        raise ValueError("complete state must contain only finite amplitudes")
    return state


def validate_branch_identity(
    branch: Mapping[str, Any],
    *,
    expected_fixture_sha256: str,
    expected_run_spec_sha256: str,
    expected_distance: int,
    expected_rounds: int,
    expected_measurement_count: int,
) -> list[int]:
    """Validate one hash-bound branch and return its ordered raw bits."""

    for expected_hash in (
        expected_fixture_sha256,
        expected_run_spec_sha256,
    ):
        if _SHA256.fullmatch(expected_hash) is None:
            raise ValueError("expected identity is not a SHA-256 digest")
    if branch.get("schema") != BRANCH_SCHEMA:
        raise ValueError("unsupported branch schema")
    if branch.get("fixture_sha256") != expected_fixture_sha256:
        raise ValueError("branch fixture hash mismatch")
    if branch.get("run_spec_sha256") != expected_run_spec_sha256:
        raise ValueError("branch run-spec hash mismatch")
    if branch.get("distance") != expected_distance:
        raise ValueError("branch distance mismatch")
    if branch.get("rounds") != expected_rounds:
        raise ValueError("branch round count mismatch")
    if not isinstance(branch.get("branch_id"), str) or not branch["branch_id"]:
        raise ValueError("branch id must be a nonempty string")
    outcomes = branch.get("outcomes")
    if not isinstance(outcomes, list) or len(outcomes) != expected_measurement_count:
        raise ValueError("branch outcome count mismatch")
    bits: list[int] = []
    for expected_column, row in enumerate(outcomes):
        if (
            not isinstance(row, Mapping)
            or row.get("column") != expected_column
        ):
            raise ValueError("branch columns must be contiguous and ordered")
        bit = row.get("bit")
        if bit not in (0, 1):
            raise ValueError("branch outcome bit must be binary")
        bits.append(bit)
    return bits


def _bound_sha256(
    value: Mapping[str, Any],
    *,
    expected: str,
    label: str,
) -> str:
    observed = {
        item
        for key in ("canonical_sha256", "sha256")
        if isinstance((item := value.get(key)), str)
    }
    if observed != {expected}:
        raise ValueError(f"{label} SHA-256 mismatch")
    return expected


def _checkpoint_id(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping) and isinstance(value.get("id"), str):
        return value["id"]
    raise ValueError("checkpoint must be a string or an object with id")


def _probability_rows(summary: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    rows = summary.get("probability_rows")
    if rows is None and isinstance(summary.get("branch"), Mapping):
        rows = summary["branch"].get("probability_rows")
    if not isinstance(rows, list) or not all(
        isinstance(row, Mapping) for row in rows
    ):
        raise ValueError("summary lacks ordered probability rows")
    return rows


def _folded_bits(summary: Mapping[str, Any]) -> tuple[list[int], list[int]]:
    branch = summary.get("branch")
    if isinstance(branch, Mapping) and {
        "detector_bits",
        "observable_bits",
    } <= set(branch):
        detectors = branch["detector_bits"]
        observables = branch["observable_bits"]
    elif isinstance(summary.get("folded_record"), Mapping):
        detectors = summary["folded_record"].get("detectors")
        observables = summary["folded_record"].get("observables")
    elif isinstance(summary.get("record"), Mapping):
        detectors = summary["record"].get("detector_bits")
        observables = summary["record"].get("observable_bits")
    else:
        raise ValueError("summary lacks a realized absolute fold")
    if (
        not isinstance(detectors, list)
        or not isinstance(observables, list)
        or any(bit not in (0, 1) for bit in (*detectors, *observables))
    ):
        raise ValueError("realized fold must contain binary lists")
    return list(detectors), list(observables)


def _require_candidate_firewall(candidate: Mapping[str, Any]) -> None:
    if (
        candidate.get("private_candidate_tensors_or_gauges_exported") is not False
        or candidate.get("reference_tensor_or_gauge_consumed") is not False
        or candidate.get("forbidden_substitute_used") is not False
    ):
        raise ValueError("candidate independence/proxy firewall failed")


def _require_exact_reference_firewall(reference: Mapping[str, Any]) -> None:
    contract = reference.get("reference_state_contract")
    if (
        reference.get("method") != "numpy_exact_data_projector"
        or reference.get("candidate_payload_consumed") is not False
        or reference.get("external_circuit_runtime_imported") is not False
        or reference.get("forbidden_substitute_used") is not False
        or not isinstance(contract, Mapping)
        or contract.get("probability_floor") is not None
        or contract.get("truncation") is not None
        or contract.get("normalization_square_root") != "positive_real"
        or contract.get("post_hoc_phase_canonicalization") is not None
    ):
        raise ValueError("exact reference independence/truncation firewall failed")


def compare_d2_tracer_laws(
    dense: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare the complete d2 raw and absolute-folded Record laws."""

    policy = FIXTURE_POLICIES[2]
    if (
        dense.get("schema") != DENSE_REFERENCE_SCHEMA
        or dense.get("status") != "completed"
        or dense.get("mode") != "tracer_full_law"
    ):
        raise ValueError("unsupported or incomplete dense d2 tracer")
    if (
        candidate.get("schema") != CANDIDATE_SCHEMA
        or candidate.get("status") != "completed"
        or candidate.get("mode") != "d2_complete_raw_and_record_law"
    ):
        raise ValueError("unsupported or incomplete Quimb d2 tracer")
    _require_candidate_firewall(candidate)
    if (
        dense.get("fixture_sha256") != policy["fixture_sha256"]
        or dense.get("enumeration_spec_sha256")
        != policy["run_spec_sha256"]
    ):
        raise ValueError("dense d2 tracer identity mismatch")
    fixture = candidate.get("fixture")
    run_spec = candidate.get("run_spec")
    if not isinstance(fixture, Mapping) or not isinstance(run_spec, Mapping):
        raise ValueError("candidate d2 tracer lacks fixture/spec identity")
    if fixture.get("distance") != 2 or fixture.get("rounds") != 2:
        raise ValueError("candidate d2 tracer distance/round mismatch")
    _bound_sha256(
        fixture,
        expected=policy["fixture_sha256"],
        label="candidate d2 fixture",
    )
    _bound_sha256(
        run_spec,
        expected=policy["run_spec_sha256"],
        label="candidate d2 enumeration spec",
    )
    if run_spec.get("enumeration") is not True:
        raise ValueError("candidate d2 run spec is not an enumeration")

    configuration = candidate.get("candidate")
    diagnostics = candidate.get("diagnostics")
    if not isinstance(configuration, Mapping) or (
        configuration.get("requested_max_bond") != 8
        or configuration.get("rdm_radius") != "complete"
        or configuration.get("cutoff") != 0.0
    ):
        raise ValueError("candidate d2 tracer configuration mismatch")
    if not isinstance(diagnostics, Mapping) or (
        diagnostics.get("all_reset_tensor_slices_exact_zero") is not True
        or diagnostics.get("all_rdm_coverage_complete") is not True
    ):
        raise ValueError("candidate d2 tracer reset/RDM evidence failed")
    reset_distance = diagnostics.get("max_reset_trace_distance")
    if (
        isinstance(reset_distance, bool)
        or not isinstance(reset_distance, (int, float))
        or not math.isfinite(reset_distance)
        or not 0.0 <= float(reset_distance) <= 1e-10
    ):
        raise ValueError("candidate d2 reset trace distance failed")

    raw_order = "measurement_column_ascending_big_endian"
    record_order = (
        "detector_row_ascending_then_observable_row_ascending_big_endian"
    )
    if (
        dense.get("raw_bit_order") != raw_order
        or candidate.get("raw_bit_order") != raw_order
        or dense.get("record_bit_order") != record_order
        or candidate.get("record_bit_order") != record_order
    ):
        raise ValueError("d2 tracer bit order mismatch")
    raw_support = [f"{index:010b}" for index in range(1024)]
    record_support = [f"{index:06b}" for index in range(64)]
    dense_raw = _probability_law(
        dense.get("raw_law", {}),
        support=raw_support,
        name="dense raw law",
        normalization_atol=1e-12,
    )
    candidate_raw = _probability_law(
        candidate.get("raw_law", {}),
        support=raw_support,
        name="candidate raw law",
        normalization_atol=1e-10,
    )
    dense_record = _probability_law(
        dense.get("record_law", {}),
        support=record_support,
        name="dense Record law",
        normalization_atol=1e-12,
    )
    candidate_record = _probability_law(
        candidate.get("record_law", {}),
        support=record_support,
        name="candidate Record law",
        normalization_atol=1e-10,
    )
    ry_zero_record = _probability_law(
        dense.get("ry_zero_record_law", {}),
        support=record_support,
        name="dense zero-RY Record law",
        normalization_atol=1e-12,
    )
    raw_tv = 0.5 * float(np.abs(dense_raw - candidate_raw).sum())
    record_tv = 0.5 * float(
        np.abs(dense_record - candidate_record).sum()
    )
    ry_nondegeneracy_tv = 0.5 * float(
        np.abs(dense_record - ry_zero_record).sum()
    )
    dense_raw_residual = abs(
        math.fsum(float(value) for value in dense["raw_law"].values())
        - 1.0
    )
    candidate_raw_residual = abs(
        math.fsum(
            float(value) for value in candidate["raw_law"].values()
        )
        - 1.0
    )
    passes = (
        dense_raw_residual <= 1e-12
        and candidate_raw_residual <= 1e-10
        and raw_tv <= 1e-8
        and record_tv <= 1e-8
        and ry_nondegeneracy_tv > 1e-6
    )
    return {
        "schema": RESULT_SCHEMA,
        "status": "completed",
        "mode": "d2_complete_law_gate",
        "distance": 2,
        "rounds": 2,
        "fixture_sha256": policy["fixture_sha256"],
        "enumeration_spec_sha256": policy["run_spec_sha256"],
        "raw_law_support_size": len(raw_support),
        "record_law_support_size": len(record_support),
        "dense_raw_normalization_residual": dense_raw_residual,
        "candidate_raw_normalization_residual": candidate_raw_residual,
        "raw_law_tv": raw_tv,
        "record_law_tv": record_tv,
        "ry_record_nondegeneracy_tv": ry_nondegeneracy_tv,
        "max_reset_trace_distance": float(reset_distance),
        "passes": passes,
    }


def compare_d3_exact_and_full_dense(
    exact: Mapping[str, Any],
    dense: Mapping[str, Any],
) -> dict[str, Any]:
    """Gate the data-projector d3 reference against full active-qubit dense."""

    policy = FIXTURE_POLICIES[3]
    if (
        exact.get("schema") != EXACT_REFERENCE_SCHEMA
        or exact.get("status") != "completed"
    ):
        raise ValueError("unsupported or incomplete exact-data d3 reference")
    _require_exact_reference_firewall(exact)
    if (
        dense.get("schema") != DENSE_REFERENCE_SCHEMA
        or dense.get("status") != "completed"
    ):
        raise ValueError("unsupported or incomplete full-dense d3 reference")
    for label, summary in (("exact", exact), ("dense", dense)):
        fixture = summary.get("fixture")
        run_spec = summary.get("run_spec")
        if not isinstance(fixture, Mapping) or not isinstance(
            run_spec,
            Mapping,
        ):
            raise ValueError(f"{label} d3 summary lacks fixture/spec identity")
        if fixture.get("distance") != 3 or fixture.get("rounds") != 2:
            raise ValueError(f"{label} d3 distance/round mismatch")
        _bound_sha256(
            fixture,
            expected=policy["fixture_sha256"],
            label=f"{label} d3 fixture",
        )
        _bound_sha256(
            run_spec,
            expected=policy["run_spec_sha256"],
            label=f"{label} d3 run spec",
        )
        if _checkpoint_id(summary.get("checkpoint")) != PRETERMINAL_CHECKPOINT:
            raise ValueError(f"{label} d3 checkpoint mismatch")

    exact_branch = exact.get("branch")
    dense_branch = dense.get("branch")
    if not isinstance(exact_branch, Mapping) or not isinstance(
        dense_branch,
        Mapping,
    ):
        raise ValueError("d3 reference summaries lack branch identities")
    exact_bits = validate_branch_identity(
        exact_branch,
        expected_fixture_sha256=policy["fixture_sha256"],
        expected_run_spec_sha256=policy["run_spec_sha256"],
        expected_distance=3,
        expected_rounds=2,
        expected_measurement_count=policy["num_measurements"],
    )
    dense_bits = validate_branch_identity(
        dense_branch,
        expected_fixture_sha256=policy["fixture_sha256"],
        expected_run_spec_sha256=policy["run_spec_sha256"],
        expected_distance=3,
        expected_rounds=2,
        expected_measurement_count=policy["num_measurements"],
    )
    if (
        exact_bits != dense_bits
        or exact_branch.get("branch_id") != dense_branch.get("branch_id")
    ):
        raise ValueError("d3 exact/dense branch identity mismatch")
    exact_authority = exact.get("branch_authority")
    dense_authority = dense.get("branch_authority")
    if (
        not isinstance(exact_authority, Mapping)
        or dense_authority != exact_authority
        or exact_authority.get("schema") != BRANCH_AUTHORITY_SCHEMA
        or exact_authority.get("branch_sha256")
        != _canonical_json_sha256(exact_branch)
    ):
        raise ValueError("d3 exact/dense branch authority mismatch")

    exact_state = exact.get("state")
    dense_state = dense.get("state")
    if not isinstance(exact_state, Mapping) or not isinstance(
        dense_state,
        Mapping,
    ):
        raise ValueError("d3 exact/dense summaries lack complete states")
    axes = list(range(17))
    if (
        exact_state.get("state_scope") != "all_active_qubits"
        or dense_state.get("state_scope") != "all_active_qubits"
    ):
        raise ValueError("d3 exact/dense state scope mismatch")
    exact_vector = load_complete_state(
        exact_state,
        expected_axis_order=axes,
    )
    dense_vector = load_complete_state(
        dense_state,
        expected_axis_order=axes,
    )
    fidelity = complete_vector_fidelity(exact_vector, dense_vector)
    branch_metrics = selected_branch_metrics(
        _probability_rows(exact),
        _probability_rows(dense),
        reference_normalization_atol=1e-12,
        candidate_normalization_atol=1e-12,
    )
    passes = (
        1.0 - fidelity <= 1e-12
        and branch_metrics["max_probability_error"] <= 1e-12
        and branch_metrics["log_branch_mass_error"] <= 1e-9
    )
    return {
        "schema": RESULT_SCHEMA,
        "status": "completed",
        "mode": "d3_exact_data_vs_full_dense_gate",
        "distance": 3,
        "rounds": 2,
        "fixture_sha256": policy["fixture_sha256"],
        "run_spec_sha256": policy["run_spec_sha256"],
        "branch_id": exact_branch["branch_id"],
        "fidelity": fidelity,
        **branch_metrics,
        "passes": passes,
    }


def _candidate_reset_evidence(
    candidate: Mapping[str, Any],
    *,
    policy: Mapping[str, Any],
    distance: int,
) -> tuple[float, bool]:
    rows = candidate.get("reset_checks")
    if not isinstance(rows, list) or len(rows) != policy["num_resets"]:
        raise ValueError("candidate reset-check count mismatch")
    expected_columns = list(range(policy["num_resets"]))
    if [row.get("column") for row in rows] != expected_columns:
        raise ValueError("candidate reset-check columns are not ordered")
    if [row.get("qubit") for row in rows] != policy["ancillas"] * 2:
        raise ValueError("candidate reset-check qubits are not ordered")
    distances: list[float] = []
    for row in rows:
        value = row.get("trace_distance_to_zero")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError("candidate reset trace distance is non-finite")
        if value < 0.0:
            raise ValueError("candidate reset trace distance is negative")
        if row.get("physical_one_tensor_slice_exact_zero") is not True:
            raise ValueError("candidate reset tensor slice is not structural zero")
        distances.append(float(value))
    checkpoint_rows = candidate.get("checkpoint_reset_slices")
    expected_ancillas = policy["ancillas"]
    if (
        not isinstance(checkpoint_rows, list)
        or len(checkpoint_rows) != policy["num_ancillas"]
        or any(
            row.get("physical_one_tensor_slice_exact_zero") is not True
            for row in checkpoint_rows
            if isinstance(row, Mapping)
        )
        or not all(isinstance(row, Mapping) for row in checkpoint_rows)
        or [row.get("qubit") for row in checkpoint_rows]
        != expected_ancillas
    ):
        raise ValueError("candidate preterminal reset slices are incomplete")
    maximum = max(distances, default=0.0)
    threshold = 1e-10 if distance == 3 else 1e-8
    return maximum, maximum <= threshold


def _validate_exact_branch_authority(
    reference: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    branch: Mapping[str, Any],
    reference_file_sha256: str | None,
) -> dict[str, Any]:
    authority = reference.get("branch_authority")
    candidate_authority = candidate.get("branch_authority")
    if not isinstance(authority, Mapping) or not isinstance(
        candidate_authority,
        Mapping,
    ):
        raise ValueError("exact branch authority is absent")
    if dict(candidate_authority) != dict(authority):
        raise ValueError("candidate branch authority differs from reference")
    branch_sha256 = _canonical_json_sha256(branch)
    if (
        authority.get("schema") != BRANCH_AUTHORITY_SCHEMA
        or authority.get("branch_sha256") != branch_sha256
        or authority.get("role") not in {"primary", "alternate"}
    ):
        raise ValueError("exact branch authority identity mismatch")
    role = authority["role"]
    if role == "primary":
        if (
            set(authority)
            != {"schema", "role", "method", "branch_sha256", "selector"}
            or authority.get("method") != "sha256_prefix_born_v1"
            or not isinstance(authority.get("selector"), Mapping)
        ):
            raise ValueError("primary branch authority is invalid")
    elif (
        set(authority)
        != {
            "schema",
            "role",
            "method",
            "branch_sha256",
            "parent",
            "flip_column",
        }
        or authority.get("method")
        != (
            "first_mr_opposite_probability_at_least_1e-8_then_"
            "greedy_tie_zero"
        )
        or not isinstance(authority.get("parent"), Mapping)
        or not isinstance(authority.get("flip_column"), int)
    ):
        raise ValueError("alternate branch authority is invalid")

    source = candidate.get("exact_reference_authority_source")
    if not isinstance(source, Mapping) or (
        source.get("summary_schema") != EXACT_REFERENCE_SCHEMA
        or source.get("branch_sha256") != branch_sha256
        or source.get("branch_id") != branch.get("branch_id")
        or source.get("authority") != authority
        or source.get("reference_probabilities_or_state_consumed") is not False
        or _SHA256.fullmatch(str(source.get("summary_file_sha256"))) is None
    ):
        raise ValueError("candidate exact-reference authority source is invalid")
    if (
        reference_file_sha256 is not None
        and source.get("summary_file_sha256") != reference_file_sha256
    ):
        raise ValueError("candidate exact-reference summary file hash mismatch")
    return dict(authority)


def compare_selected_branch_point(
    reference: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    reference_file_sha256: str | None = None,
) -> dict[str, Any]:
    """Compare one complete-vector XZZX reference/candidate branch pair."""

    reference_schema = reference.get("schema")
    if reference_schema not in REFERENCE_SCHEMAS:
        raise ValueError("unsupported XZZX reference schema")
    if candidate.get("schema") != CANDIDATE_SCHEMA:
        raise ValueError("unsupported XZZX candidate schema")
    if reference.get("status") != "completed":
        raise ValueError("reference point is not completed")
    if candidate.get("status") != "completed":
        raise ValueError("candidate point is not completed")
    _require_candidate_firewall(candidate)
    _require_exact_reference_firewall(reference)

    reference_fixture = reference.get("fixture")
    candidate_fixture = candidate.get("fixture")
    if not isinstance(reference_fixture, Mapping) or not isinstance(
        candidate_fixture,
        Mapping,
    ):
        raise ValueError("summaries lack fixture identities")
    distance = reference_fixture.get("distance")
    if distance not in (3, 5):
        raise ValueError("fixture distance is not registered")
    policy = FIXTURE_POLICIES[distance]
    if (
        candidate_fixture.get("distance") != distance
        or reference_fixture.get("rounds") != 2
        or candidate_fixture.get("rounds") != 2
    ):
        raise ValueError("fixture distance/round mismatch")
    fixture_sha = _bound_sha256(
        reference_fixture,
        expected=policy["fixture_sha256"],
        label="reference fixture",
    )
    _bound_sha256(
        candidate_fixture,
        expected=fixture_sha,
        label="candidate fixture",
    )

    reference_spec = reference.get("run_spec")
    candidate_spec = candidate.get("run_spec")
    if not isinstance(reference_spec, Mapping) or not isinstance(
        candidate_spec,
        Mapping,
    ):
        raise ValueError("summaries lack run-spec identities")
    run_spec_sha = _bound_sha256(
        reference_spec,
        expected=policy["run_spec_sha256"],
        label="reference run-spec",
    )
    _bound_sha256(
        candidate_spec,
        expected=run_spec_sha,
        label="candidate run-spec",
    )
    if (
        _checkpoint_id(reference.get("checkpoint")) != PRETERMINAL_CHECKPOINT
        or _checkpoint_id(candidate.get("checkpoint"))
        != PRETERMINAL_CHECKPOINT
    ):
        raise ValueError("preterminal checkpoint mismatch")

    reference_branch = reference.get("branch")
    candidate_branch = candidate.get("branch")
    if not isinstance(reference_branch, Mapping) or not isinstance(
        candidate_branch,
        Mapping,
    ):
        raise ValueError("summaries lack branch identities")
    if set(candidate_branch) != CANDIDATE_BRANCH_FIELDS:
        raise ValueError("candidate branch does not have the exact neutral field set")
    reference_bits = validate_branch_identity(
        reference_branch,
        expected_fixture_sha256=fixture_sha,
        expected_run_spec_sha256=run_spec_sha,
        expected_distance=distance,
        expected_rounds=2,
        expected_measurement_count=policy["num_measurements"],
    )
    candidate_bits = validate_branch_identity(
        candidate_branch,
        expected_fixture_sha256=fixture_sha,
        expected_run_spec_sha256=run_spec_sha,
        expected_distance=distance,
        expected_rounds=2,
        expected_measurement_count=policy["num_measurements"],
    )
    if (
        candidate_bits != reference_bits
        or candidate_branch.get("branch_id") != reference_branch.get("branch_id")
    ):
        raise ValueError("candidate and reference branch identities differ")
    branch_authority = _validate_exact_branch_authority(
        reference,
        candidate,
        branch=reference_branch,
        reference_file_sha256=reference_file_sha256,
    )

    configuration = candidate.get("candidate")
    if not isinstance(configuration, Mapping):
        raise ValueError("candidate configuration is absent")
    bond = configuration.get("requested_max_bond")
    radius = configuration.get("rdm_radius")
    if (
        not isinstance(bond, int)
        or bond <= 0
        or configuration.get("cutoff") != 0.0
        or configuration.get("reset_trace_distance_limit")
        != (1e-10 if distance == 3 else 1e-8)
    ):
        raise ValueError("candidate bond/cutoff configuration is invalid")
    if distance == 3 and radius != "complete":
        raise ValueError("d3 candidate must use verified-complete graph RDMs")
    if distance == 5 and radius not in (0, 1, 2, 3):
        raise ValueError("d5 candidate RDM radius is not registered")

    reference_state = reference.get("state")
    candidate_state = candidate.get("state")
    if not isinstance(reference_state, Mapping) or not isinstance(
        candidate_state,
        Mapping,
    ):
        raise ValueError("summaries lack complete-state metadata")
    if (
        reference_state.get("state_scope") != policy["state_scope"]
        or candidate_state.get("state_scope") != policy["state_scope"]
    ):
        raise ValueError("complete-state scope mismatch")
    reference_axes = reference_state.get("qubit_axis_order")
    candidate_axes = candidate_state.get("qubit_axis_order")
    if (
        not isinstance(reference_axes, list)
        or candidate_axes != reference_axes
        or reference_axes != sorted(reference_axes)
        or len(set(reference_axes)) != len(reference_axes)
    ):
        raise ValueError("reference/candidate state axis order mismatch")
    if distance == 3 and reference_axes != list(range(17)):
        raise ValueError("d3 state must contain all active qubits in order")
    if distance == 5 and len(reference_axes) != 25:
        raise ValueError("d5 state must contain exactly 25 sorted data qubits")
    left = load_complete_state(
        reference_state,
        expected_axis_order=reference_axes,
    )
    right = load_complete_state(
        candidate_state,
        expected_axis_order=reference_axes,
    )
    if left.size != policy["state_size"] or right.size != policy["state_size"]:
        raise ValueError("complete-vector size differs from frozen target")
    fidelity = complete_vector_fidelity(left, right)

    branch_metrics = selected_branch_metrics(
        _probability_rows(reference),
        _probability_rows(candidate),
    )
    max_reset_distance, reset_pass = _candidate_reset_evidence(
        candidate,
        policy=policy,
        distance=distance,
    )
    realized_fold_pass = _folded_bits(reference) == _folded_bits(candidate)
    verdict = classify_conditioned_trajectory(
        distance=distance,
        fidelity=fidelity,
        max_probability_error=branch_metrics["max_probability_error"],
        log_branch_mass_error=branch_metrics["log_branch_mass_error"],
        reset_checks_pass=reset_pass,
        realized_fold_pass=realized_fold_pass,
        complete_vector_available=True,
    )
    return {
        "schema": RESULT_SCHEMA,
        "status": "completed",
        "distance": distance,
        "rounds": 2,
        "fixture_sha256": fixture_sha,
        "run_spec_sha256": run_spec_sha,
        "checkpoint": PRETERMINAL_CHECKPOINT,
        "branch_id": reference_branch["branch_id"],
        "branch_role": branch_authority["role"],
        "reference_schema": reference_schema,
        "candidate_schema": CANDIDATE_SCHEMA,
        "state_scope": policy["state_scope"],
        "qubit_axis_order": reference_axes,
        "bond_dimension": bond,
        "rdm_radius": radius,
        "fidelity": fidelity,
        **branch_metrics,
        "max_reset_trace_distance": max_reset_distance,
        "reset_checks_pass": reset_pass,
        "realized_fold_pass": realized_fold_pass,
        "forbidden_substitute_used": False,
        "verdict": verdict,
    }


def classify_conditioned_trajectory(
    *,
    distance: int,
    fidelity: float | None,
    max_probability_error: float,
    log_branch_mass_error: float,
    reset_checks_pass: bool,
    realized_fold_pass: bool,
    complete_vector_available: bool,
) -> str:
    """Apply the frozen d3/d5 usefulness bands without proxy promotion."""

    if distance not in (3, 5):
        raise ValueError("trajectory verdict is registered only for d3 and d5")
    if not complete_vector_available:
        if fidelity is not None:
            raise ValueError("unavailable complete vector cannot carry fidelity")
        return "unavailable"
    if fidelity is None or not math.isfinite(fidelity) or not 0.0 <= fidelity <= 1.0:
        raise ValueError("fidelity must be finite and lie in [0, 1]")
    for name, value in (
        ("maximum probability error", max_probability_error),
        ("log branch-mass error", log_branch_mass_error),
    ):
        if not math.isfinite(value) or value < 0.0:
            raise ValueError(f"{name} must be finite and nonnegative")
    if fidelity < 0.95:
        return "low_state"
    if fidelity < 0.99:
        return "marginal_state"
    probability_band, log_mass_band = (
        (5e-3, 1e-1) if distance == 3 else (1e-2, 5e-1)
    )
    if (
        max_probability_error <= probability_band
        and log_branch_mass_error <= log_mass_band
        and reset_checks_pass
        and realized_fold_pass
    ):
        return "useful_conditioned_trajectory"
    return "state_useful_mass_unresolved"


def _load_json_object(path: Path) -> dict[str, Any]:
    def reject_duplicate_keys(
        pairs: list[tuple[str, Any]],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_nonfinite(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")

    if not path.is_file():
        raise ValueError(f"summary is not an existing file: {path}")
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=reject_nonfinite,
    )
    if not isinstance(value, dict):
        raise ValueError(f"summary must contain one JSON object: {path}")
    return value


def _write_json_exclusive_atomic(path: Path, value: Mapping[str, Any]) -> None:
    if not path.parent.is_dir():
        raise ValueError(f"output parent is not an existing directory: {path.parent}")
    payload = (
        json.dumps(
            value,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError as error:
            raise ValueError(f"output already exists: {path}") from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare one independently persisted XZZX reference/candidate branch pair."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("selected", "d2-tracer", "d3-exact-dense"),
        default="selected",
        help="registered comparison object",
    )
    parser.add_argument(
        "--reference-summary",
        required=True,
        type=Path,
        help="persisted first/reference summary JSON",
    )
    parser.add_argument(
        "--candidate-summary",
        required=True,
        type=Path,
        help="persisted second/candidate summary JSON",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="new immutable comparison JSON path",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    reference_path = args.reference_summary.resolve()
    candidate_path = args.candidate_summary.resolve()
    output_path = args.output.resolve()
    reference = _load_json_object(reference_path)
    candidate = _load_json_object(candidate_path)
    if args.mode == "selected":
        result = compare_selected_branch_point(
            reference,
            candidate,
            reference_file_sha256=_file_sha256(reference_path),
        )
    elif args.mode == "d2-tracer":
        result = compare_d2_tracer_laws(reference, candidate)
    else:
        result = compare_d3_exact_and_full_dense(reference, candidate)
    comparator_path = Path(__file__).resolve()
    result["input_provenance"] = {
        "reference_summary_path": str(reference_path),
        "reference_summary_sha256": _file_sha256(reference_path),
        "candidate_summary_path": str(candidate_path),
        "candidate_summary_sha256": _file_sha256(candidate_path),
        "comparator_path": str(comparator_path),
        "comparator_sha256": _file_sha256(comparator_path),
    }
    _write_json_exclusive_atomic(output_path, result)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error
