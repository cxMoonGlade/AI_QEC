#!/usr/bin/env python3
"""Run one hash-bound XZZX trajectory with Quimb arbitrary-graph PEPS.

This worker consumes only neutral JSON.  It never imports a dense or Aer
reference and never exports Quimb tensors or gauges.
"""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import itertools
import json
import math
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping, Sequence

import numpy as np


RESULT_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_quimb_candidate.v1"
)
FIXTURE_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_peps.fixture.v1"
)
RUN_SPEC_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_peps.run_spec.v2"
)
ENUMERATION_SPEC_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_peps."
    "enumeration_spec.v1"
)
BRANCH_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_peps.branch.v1"
)
EXACT_REFERENCE_RESULT_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_exact_data_reference.v1"
)
BRANCH_AUTHORITY_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_exact_data_reference."
    "branch_authority.v1"
)
EXPECTED_QUIMB_COMMIT = "3c89529fe0a3487133a3928201691161e110abdf"
EXPECTED_QUIMB_TREE = "d81d043a27b7abf20e6c3a423f9b772682bbef40"
ENVIRONMENT_NAME = "ecs-baseline-quimb-peps"
ENVIRONMENT_LOCK_SCHEMA = (
    "error_coupling_simulator.environment_lock.quimb_peps_d5.v2"
)
REPO = Path(__file__).resolve().parents[2]
QUIMB_CLONE = REPO / "external" / "baselines" / "quimb"
ENVIRONMENT_LOCK = REPO / "baseline-environment-quimb-peps-linux-64.lock.json"
GAUGE_SMUDGE = 1e-12
SERIAL_CONTRACTION_POLICY = "auto-hq-serial"
WALL_TIME_LIMIT_SECONDS = 1800.0
HOST_RSS_LIMIT_BYTES = 64 * 1024**3
DEVICE_ALLOCATION_LIMIT_BYTES = 28 * 1024**3
FROZEN_V2_PREREG_COMMIT = (
    "dc7f6a6a4bbc2ae3e8ba8dea6f00343ef9a9fc67"
)
FROZEN_V2_PREREG_PATH = (
    "docs/simulator_validation/"
    "PEPS_XZZX_MEASUREMENT_RESET_RECORD_PREREG_V2_2026-07-27.md"
)
PRETERMINAL_CHECKPOINT = (
    "after_round_1_ry_before_terminal_data_measurements"
)
EXPECTED_FIXTURES = {
    2: {
        "fixture_sha256": (
            "dbf2a0979c9a4cd0a95f2afe393083d97a27ea1e90720596352a191010beb0f5"
        ),
        "stim_sha256": (
            "18492ad9bc8b286d1cf9f97f45546fac40552a10d83be9ef61fa892a941cb671"
        ),
        "shape": (7, 10, 5, 1),
        "operations": 57,
        "resets": 6,
        "spec_sha256": (
            "02aef76a65383fbfec9a2f3e0b62a7dd0691a574ee739a4b6b33326ba13681ca"
        ),
    },
    3: {
        "fixture_sha256": (
            "3b2bf7d81f7241e0a3b6abb14c76474c362e696cf374c55e20e3d121946bbf3c"
        ),
        "stim_sha256": (
            "7067b1241251bd7558e7dc85b2f84bc13a45c1217a49f8fcfa2e51205879ecb0"
        ),
        "shape": (17, 25, 16, 1),
        "operations": 154,
        "resets": 16,
        "spec_sha256": (
            "7dfa0a8ef9620712e6ea190aeda651c681295f9841963ce77686640255cc22a9"
        ),
    },
    5: {
        "fixture_sha256": (
            "659fda875a91f2a6e3c64f8f03487b5a431edecb9849dd897bf2e6f390583495"
        ),
        "stim_sha256": (
            "be26b8708efe36a027bcf79074bc936de552b1a5d22b35b627d7d9cdbb27f008"
        ),
        "shape": (49, 73, 48, 1),
        "operations": 490,
        "resets": 48,
        "spec_sha256": (
            "06151ea1244495475259d40bf6ca7ad16cbdaf5f8184ee61b344fb2e81b413a4"
        ),
    },
}
INTERVENTION = {
    "after_rounds": [0, 1],
    "angle_radians": 0.02,
    "gate": "RY",
    "placement": (
        "after_each_complete_syndrome_round_before_the_next_base_operation"
    ),
    "targets": "all_data_qubits_in_ascending_dense_id_order",
}
RESET_GAUGE_POLICY = {
    "strategy": "preserve_pre_reset_simple_update_gauges_byte_for_byte",
    "rank_one_gate": "direct_normalized_A_b_on_physical_leg",
    "no_psi0_reconstruction": True,
    "no_gauge_refresh": True,
    "no_corrective_projector": True,
    "gauge_interpretation": (
        "unchanged_heuristic_environment_for_later_simple_update_gates_"
        "not_exact_postmeasurement_schmidt_spectra"
    ),
    "private_gauge_values_exported": False,
}
PRETARGET_DEVIATION_EVIDENCE = {
    "status": "declared_before_formal_target_execution",
    "frozen_preregistration_commit": (
        "15bb541f91f243f9d328b00357ff125bc44554db"
    ),
    "frozen_preregistration_path": (
        "docs/simulator_validation/"
        "PEPS_XZZX_MEASUREMENT_RESET_RECORD_PREREG_2026-07-26.md"
    ),
    "frozen_declared_path": (
        "rank_one_local_tensor_gate_then_reconstruction_of_"
        "CircuitPEPSSimpleUpdate"
    ),
    "selected_path": (
        "copy_with_private_backend_cache_then_direct_normalized_A_b_"
        "with_pre_reset_gauges_preserved_byte_for_byte"
    ),
    "reason": (
        "psi0 reconstruction smudges rank-deficient reset state; "
        "zero-smudge gauge equilibration divides by exact-zero gauges"
    ),
    "psi0_reconstruction_rejected": True,
    "reset_time_gauge_equilibration_rejected": True,
    "tolerance_authorized_repair_used": False,
    "formal_target_output_inspected_before_declaration": False,
}
COMMITTED_INPUTS = (
    "baseline-environment-quimb-peps-linux-64.lock.json",
    FROZEN_V2_PREREG_PATH,
    "scripts/external_baselines/emit_xzzx_record_peps_fixture.py",
    "scripts/external_baselines/xzzx_record_quimb_candidate.py",
    "scripts/external_baselines/compare_xzzx_record_peps.py",
    "tests/test_external_xzzx_record_fixture.py",
    "tests/test_external_xzzx_record_quimb_candidate.py",
    "tests/test_external_xzzx_record_metrics.py",
)


def _require_sha256(value: Any, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def validate_fixture(payload: Mapping[str, Any]) -> str:
    """Independently validate one of the three frozen neutral fixtures."""

    if payload.get("schema") != FIXTURE_SCHEMA:
        raise ValueError("unsupported XZZX PEPS fixture schema")
    distance = payload.get("distance")
    if distance not in EXPECTED_FIXTURES:
        raise ValueError("fixture distance must be 2, 3, or 5")
    expected = EXPECTED_FIXTURES[distance]
    digest = canonical_json_sha256(payload)
    if digest != expected["fixture_sha256"]:
        raise ValueError("canonical fixture hash mismatch")
    if payload.get("rounds") != 2:
        raise ValueError("fixture must contain exactly two rounds")
    shape = (
        payload.get("num_qubits"),
        payload.get("num_measurements"),
        payload.get("num_detectors"),
        payload.get("num_observables"),
    )
    if shape != expected["shape"]:
        raise ValueError("fixture shape mismatch")
    if payload.get("stim_circuit_sha256") != expected["stim_sha256"]:
        raise ValueError("fixture transformed Stim hash mismatch")
    operations = payload.get("operations")
    if not isinstance(operations, list) or len(operations) != expected[
        "operations"
    ]:
        raise ValueError("fixture operation count mismatch")
    measurement_order = payload.get("measurement_order")
    if (
        not isinstance(measurement_order, list)
        or len(measurement_order) != shape[1]
        or [row.get("column") for row in measurement_order]
        != list(range(shape[1]))
    ):
        raise ValueError("fixture measurement columns are not contiguous")
    if sum(row.get("reset") is True for row in measurement_order) != expected[
        "resets"
    ]:
        raise ValueError("fixture MR count mismatch")
    if not all(
        row.get("reset") is True
        for row in measurement_order[: expected["resets"]]
    ) or any(
        row.get("reset") is True
        for row in measurement_order[expected["resets"] :]
    ):
        raise ValueError("fixture reset/terminal column partition mismatch")

    qubit_count = shape[0]
    data_qubits = payload.get("frame", {}).get("data_qubits")
    if (
        not isinstance(data_qubits, list)
        or data_qubits != sorted(data_qubits)
        or len(data_qubits) != distance * distance
        or any(
            isinstance(site, bool)
            or not isinstance(site, int)
            or not 0 <= site < qubit_count
            for site in data_qubits
        )
    ):
        raise ValueError("fixture data-qubit order mismatch")
    expected_measurements: list[tuple[int, str, bool]] = []
    initialization_open = True
    for operation in operations:
        if (
            not isinstance(operation, dict)
            or set(operation) != {"op", "qubits"}
        ):
            raise ValueError("fixture operation row schema mismatch")
        kind = operation["op"]
        sites = operation["qubits"]
        expected_arity = 2 if kind == "CX" else 1
        if kind not in {"R", "RX", "H", "CX", "M", "MX", "MR"}:
            raise ValueError(f"unsupported fixture operation: {kind!r}")
        if (
            not isinstance(sites, list)
            or len(sites) != expected_arity
            or any(
                isinstance(site, bool)
                or not isinstance(site, int)
                or not 0 <= site < qubit_count
                for site in sites
            )
        ):
            raise ValueError("fixture operation target mismatch")
        if kind in {"R", "RX"}:
            if not initialization_open:
                raise ValueError("noninitial unconditional reset is unsupported")
        else:
            initialization_open = False
        if kind in {"M", "MX", "MR"}:
            expected_measurements.append(
                (
                    sites[0],
                    "X" if kind == "MX" else "Z",
                    kind == "MR",
                )
            )
    observed_measurements = [
        (row.get("qubit"), row.get("basis"), row.get("reset"))
        for row in measurement_order
    ]
    if observed_measurements != expected_measurements:
        raise ValueError("operation/measurement ledger mismatch")
    for row_name in ("detector_rows", "observable_rows"):
        rows = payload.get(row_name)
        if not isinstance(rows, list):
            raise ValueError(f"fixture {row_name} must be a list")
        for row in rows:
            if (
                not isinstance(row, list)
                or not row
                or any(
                    isinstance(column, bool)
                    or not isinstance(column, int)
                    or not 0 <= column < shape[1]
                    for column in row
                )
            ):
                raise ValueError(f"fixture {row_name} has an invalid row")
    return digest


def validate_run_spec(
    payload: Mapping[str, Any],
    fixture: Mapping[str, Any],
) -> tuple[str, bool]:
    """Validate the frozen enumeration/run spec without importing its emitter."""

    fixture_sha256 = validate_fixture(fixture)
    distance = fixture["distance"]
    enumeration = distance == 2
    expected_schema = (
        ENUMERATION_SPEC_SCHEMA if enumeration else RUN_SPEC_SCHEMA
    )
    if payload.get("schema") != expected_schema:
        raise ValueError("run/enumeration spec schema mismatch")
    digest = canonical_json_sha256(payload)
    if digest != EXPECTED_FIXTURES[distance]["spec_sha256"]:
        raise ValueError("run/enumeration spec canonical hash mismatch")
    if (
        payload.get("base_fixture_sha256") != fixture_sha256
        or payload.get("stim_circuit_sha256")
        != fixture["stim_circuit_sha256"]
        or payload.get("distance") != distance
        or payload.get("rounds") != 2
        or payload.get("intervention") != INTERVENTION
    ):
        raise ValueError("run/enumeration spec does not bind the fixture")
    if enumeration:
        if payload.get("reference") != {
            "method": "dense_complete_enumeration",
            "raw_outcome_count": 10,
            "support_size": 1024,
        }:
            raise ValueError("enumeration reference contract mismatch")
    else:
        if payload.get("reference_branch") != {
            "sampler": "numpy_exact_data_projector",
            "selector": {
                "algorithm": "sha256_prefix_born_v1",
                "comparison": (
                    "bit_0_iff_h_times_den_lt_num_times_2_pow_256_for_"
                    "p0_as_integer_ratio"
                ),
                "domain_separator_ascii": (
                    "ECS-XZZX-DATA-ONLY-BRANCH-V2"
                ),
                "domain_separator_terminated_by_zero_byte": True,
                "hash_integer_encoding": (
                    "sha256_full_digest_unsigned_big_endian"
                ),
                "measurement_column_encoding": (
                    "uint32_big_endian_equal_to_prefix_length"
                ),
                "prefix_encoding": "one_byte_per_bit_0x00_or_0x01",
                "seed": 2026072600 + distance,
                "seed_encoding": "uint64_big_endian",
            },
            "shots": 1,
        }:
            raise ValueError(
                "run-spec exact-reference branch authority mismatch"
            )
        if payload.get("reference_state") != {
            "checkpoint": PRETERMINAL_CHECKPOINT,
            "method": "numpy_exact_data_projector",
            "probability_floor": None,
            "truncation": None,
        }:
            raise ValueError(
                "run-spec exact-reference state authority mismatch"
            )
    return digest, enumeration


def validate_branch(
    payload: Mapping[str, Any],
    *,
    fixture_sha256: str,
    spec_sha256: str,
    distance: int,
    rounds: int,
    measurement_count: int,
    enumeration: bool,
) -> list[int]:
    """Validate and return the branch bits in measurement-column order."""

    if payload.get("schema") != BRANCH_SCHEMA:
        raise ValueError("unsupported branch schema")
    if payload.get("fixture_sha256") != _require_sha256(
        fixture_sha256,
        label="expected fixture hash",
    ):
        raise ValueError("branch fixture hash mismatch")
    spec_key = (
        "enumeration_spec_sha256" if enumeration else "run_spec_sha256"
    )
    required_fields = {
        "schema",
        "fixture_sha256",
        spec_key,
        "branch_id",
        "distance",
        "rounds",
        "outcomes",
    }
    if set(payload) != required_fields:
        raise ValueError(
            "branch must contain the exact neutral fields and no reference data"
        )
    if payload.get(spec_key) != _require_sha256(
        spec_sha256,
        label="expected spec hash",
    ):
        raise ValueError(f"branch {spec_key.replace('_', ' ')} mismatch")
    branch_id = payload.get("branch_id")
    if not isinstance(branch_id, str) or not branch_id:
        raise ValueError("branch_id must be a nonempty string")
    if payload.get("distance") != distance or payload.get("rounds") != rounds:
        raise ValueError("branch distance/rounds mismatch")
    outcomes = payload.get("outcomes")
    if not isinstance(outcomes, list) or len(outcomes) != measurement_count:
        raise ValueError("branch outcome count mismatch")
    bits: list[int] = []
    for column, row in enumerate(outcomes):
        if (
            not isinstance(row, dict)
            or row.get("column") != column
            or set(row) != {"column", "bit"}
        ):
            raise ValueError(
                "branch outcomes must have exact contiguous columns"
            )
        bit = row["bit"]
        if isinstance(bit, bool) or not isinstance(bit, int) or bit not in (0, 1):
            raise ValueError("branch outcomes must be integer bits")
        bits.append(bit)
    return bits


def validate_branch_authority(
    payload: Mapping[str, Any],
    *,
    branch: Mapping[str, Any],
    run_spec: Mapping[str, Any],
    fixture: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate exact-reference authority without consuming reference values."""

    fixture_sha256 = validate_fixture(fixture)
    spec_sha256, enumeration = validate_run_spec(run_spec, fixture)
    distance = int(fixture["distance"])
    if enumeration or distance not in {3, 5}:
        raise ValueError("branch authority is defined only for d3/d5")
    validate_branch(
        branch,
        fixture_sha256=fixture_sha256,
        spec_sha256=spec_sha256,
        distance=distance,
        rounds=2,
        measurement_count=int(fixture["num_measurements"]),
        enumeration=False,
    )
    branch_sha256 = canonical_json_sha256(branch)
    if payload.get("schema") != BRANCH_AUTHORITY_SCHEMA:
        raise ValueError("unsupported branch-authority schema")
    if payload.get("branch_sha256") != branch_sha256:
        raise ValueError("branch-authority branch SHA mismatch")
    role = payload.get("role")
    if role == "primary":
        if set(payload) != {
            "schema",
            "role",
            "method",
            "branch_sha256",
            "selector",
        }:
            raise ValueError(
                "primary branch authority must contain exact fields"
            )
        if (
            payload.get("method") != "sha256_prefix_born_v1"
            or payload.get("selector")
            != run_spec["reference_branch"]["selector"]
        ):
            raise ValueError("primary branch selector authority mismatch")
        return {
            "schema": BRANCH_AUTHORITY_SCHEMA,
            "role": "primary",
            "method": "sha256_prefix_born_v1",
            "branch_sha256": branch_sha256,
            "selector": json.loads(
                json.dumps(payload["selector"], allow_nan=False)
            ),
        }
    if role == "alternate":
        if set(payload) != {
            "schema",
            "role",
            "method",
            "branch_sha256",
            "parent",
            "flip_column",
        }:
            raise ValueError(
                "alternate branch authority must contain exact fields"
            )
        if payload.get("method") != (
            "first_mr_opposite_probability_at_least_1e-8_then_"
            "greedy_tie_zero"
        ):
            raise ValueError("alternate branch method mismatch")
        parent = payload.get("parent")
        if (
            not isinstance(parent, Mapping)
            or set(parent)
            != {
                "summary_schema",
                "summary_file_sha256",
                "branch_sha256",
                "branch_id",
            }
            or parent.get("summary_schema")
            != EXACT_REFERENCE_RESULT_SCHEMA
        ):
            raise ValueError("alternate parent authority mismatch")
        _require_sha256(
            parent.get("summary_file_sha256"),
            label="alternate parent summary hash",
        )
        _require_sha256(
            parent.get("branch_sha256"),
            label="alternate parent branch hash",
        )
        if (
            not isinstance(parent.get("branch_id"), str)
            or not parent["branch_id"]
        ):
            raise ValueError("alternate parent branch id is invalid")
        flip_column = payload.get("flip_column")
        if (
            isinstance(flip_column, bool)
            or not isinstance(flip_column, int)
            or not 0 <= flip_column < int(fixture["num_measurements"])
            or fixture["measurement_order"][flip_column].get("reset")
            is not True
        ):
            raise ValueError("alternate flip column must identify an MR")
        return {
            "schema": BRANCH_AUTHORITY_SCHEMA,
            "role": "alternate",
            "method": payload["method"],
            "branch_sha256": branch_sha256,
            "parent": {
                "summary_schema": EXACT_REFERENCE_RESULT_SCHEMA,
                "summary_file_sha256": parent["summary_file_sha256"],
                "branch_sha256": parent["branch_sha256"],
                "branch_id": parent["branch_id"],
            },
            "flip_column": flip_column,
        }
    raise ValueError("branch authority role must be primary or alternate")


def validate_exact_reference_summary(
    payload: Mapping[str, Any],
    *,
    summary_file_sha256: str,
    branch: Mapping[str, Any],
    run_spec: Mapping[str, Any],
    fixture: Mapping[str, Any],
) -> dict[str, Any]:
    """Extract only neutral authority from one hash-bound exact summary."""

    summary_sha256 = _require_sha256(
        summary_file_sha256,
        label="exact-reference summary file hash",
    )
    if payload.get("schema") != EXACT_REFERENCE_RESULT_SCHEMA:
        raise ValueError("unsupported exact-reference summary schema")
    if payload.get("status") != "completed":
        raise ValueError("exact-reference summary is not completed")
    nested_branch = payload.get("branch")
    if (
        not isinstance(nested_branch, Mapping)
        or canonical_json_bytes(nested_branch)
        != canonical_json_bytes(branch)
    ):
        raise ValueError(
            "exact-reference summary does not authorize the neutral branch"
        )
    authority = payload.get("branch_authority")
    if not isinstance(authority, Mapping):
        raise ValueError("exact-reference summary lacks branch authority")
    sanitized = validate_branch_authority(
        authority,
        branch=branch,
        run_spec=run_spec,
        fixture=fixture,
    )
    return {
        "summary_schema": EXACT_REFERENCE_RESULT_SCHEMA,
        "summary_file_sha256": summary_sha256,
        "branch_sha256": canonical_json_sha256(branch),
        "branch_id": branch["branch_id"],
        "authority": sanitized,
        "reference_probabilities_or_state_consumed": False,
    }


def gate_matrix(
    kind: str,
    *,
    angle_radians: float | None = None,
) -> np.ndarray:
    """Return the frozen local-basis gate matrix."""

    if kind == "H":
        return np.asarray(
            [[1.0, 1.0], [1.0, -1.0]],
            dtype=np.complex128,
        ) / np.sqrt(2.0)
    if kind == "RY":
        if angle_radians is None or not np.isfinite(angle_radians):
            raise ValueError("RY requires one finite angle in radians")
        cosine = np.cos(angle_radians / 2.0)
        sine = np.sin(angle_radians / 2.0)
        return np.asarray(
            [[cosine, -sine], [sine, cosine]],
            dtype=np.complex128,
        )
    if kind == "CX":
        return np.asarray(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
                [0.0, 0.0, 1.0, 0.0],
            ],
            dtype=np.complex128,
        )
    raise ValueError(f"unsupported gate kind: {kind!r}")


def _as_numpy(value: Any) -> np.ndarray:
    try:
        import torch
    except ImportError:
        torch = None
    if torch is not None and isinstance(value, torch.Tensor):
        return np.asarray(value.detach().cpu().numpy())
    return np.asarray(value)


def validated_one_site_born_pair(
    rho: np.ndarray,
) -> tuple[tuple[float, float], dict[str, float]]:
    """Validate one numerical one-site density operator without repairing it."""

    observed = np.asarray(rho, dtype=np.complex128)
    if observed.shape != (2, 2) or not np.isfinite(observed).all():
        raise RuntimeError("one-site RDM is not a finite 2x2 complex matrix")
    hermiticity_residual = float(
        np.max(np.abs(observed - observed.conj().T))
    )
    trace = np.trace(observed)
    trace_imaginary_residual = float(abs(trace.imag))
    trace_residual = float(abs(trace.real - 1.0))
    if (
        hermiticity_residual > 1e-10
        or trace_imaginary_residual > 1e-10
        or trace_residual > 1e-10
    ):
        raise RuntimeError(
            "one-site RDM failed Hermiticity/trace validation: "
            f"{hermiticity_residual=}, {trace_imaginary_residual=}, "
            f"{trace_residual=}"
        )
    minimum_eigenvalue = float(np.linalg.eigvalsh(observed).min())
    if minimum_eigenvalue < -1e-10:
        raise RuntimeError(
            "one-site RDM failed positive-semidefinite validation: "
            f"{minimum_eigenvalue=}"
        )
    diagonal_imaginary_residual = float(
        max(abs(observed[0, 0].imag), abs(observed[1, 1].imag))
    )
    if diagonal_imaginary_residual > 1e-10:
        raise RuntimeError("Born probabilities have imaginary residue")
    probabilities = (
        float(observed[0, 0].real),
        float(observed[1, 1].real),
    )
    for index, probability in enumerate(probabilities):
        if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
            raise RuntimeError(
                f"invalid Born probability p{index}={probability}"
            )
    probability_sum_residual = float(abs(math.fsum(probabilities) - 1.0))
    if probability_sum_residual > 1e-10:
        raise RuntimeError(
            "Born probabilities are not normalized: "
            f"{probability_sum_residual=}"
        )
    return probabilities, {
        "hermiticity_residual": hermiticity_residual,
        "trace_imaginary_residual": trace_imaginary_residual,
        "trace_residual": trace_residual,
        "minimum_eigenvalue": minimum_eigenvalue,
        "rdm_diagonal_imaginary_residual": diagonal_imaginary_residual,
        "probability_sum_residual": probability_sum_residual,
    }


def is_structural_zero_probability(probability: float) -> bool:
    """Return true only for the exact binary64 probability endpoint zero."""

    if (
        isinstance(probability, bool)
        or not isinstance(probability, (int, float))
        or not math.isfinite(probability)
        or not 0.0 <= probability <= 1.0
    ):
        raise RuntimeError(f"invalid probability: {probability!r}")
    return probability == 0.0


def stable_positive_branch_mass(
    probabilities: Sequence[float],
) -> dict[str, float | bool | None]:
    """Accumulate a strictly positive branch without inventing a zero mass."""

    if not probabilities:
        raise ValueError("branch mass requires at least one probability")
    validated: list[float] = []
    for probability in probabilities:
        if (
            isinstance(probability, bool)
            or not isinstance(probability, (int, float))
            or not math.isfinite(probability)
            or not 0.0 < probability <= 1.0
        ):
            raise ValueError(
                "positive branch probabilities must be finite in (0, 1]"
            )
        validated.append(float(probability))
    log_branch_mass = float(math.fsum(math.log(p) for p in validated))
    materialized = float(math.exp(log_branch_mass))
    representable = materialized > 0.0
    return {
        "branch_mass": materialized if representable else None,
        "log_branch_mass": log_branch_mass,
        "branch_mass_representable": representable,
        "positive_mass_underflowed_to_zero": False,
    }


def _trace_distance_to_zero(rho: np.ndarray) -> float:
    observed = np.asarray(rho, dtype=np.complex128)
    validated_one_site_born_pair(observed)
    target = np.asarray([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)
    singular_values = np.linalg.svd(
        observed - target,
        compute_uv=False,
    )
    return float(0.5 * np.sum(singular_values))


class QuimbTrajectory:
    """One arbitrary-graph finite-PEPS trajectory and its public diagnostics."""

    def __init__(
        self,
        *,
        qubit_count: int,
        edges: Sequence[tuple[int, int]],
        max_bond: int,
        rdm_radius: str | int,
        device_name: str,
        optimize: str,
        reset_trace_distance_limit: float = 1e-10,
    ) -> None:
        import quimb.tensor as qtn

        if (
            isinstance(qubit_count, bool)
            or not isinstance(qubit_count, int)
            or qubit_count < 1
        ):
            raise ValueError("qubit_count must be a positive integer")
        if (
            isinstance(max_bond, bool)
            or not isinstance(max_bond, int)
            or max_bond < 1
        ):
            raise ValueError("max_bond must be a positive integer")
        normalized_edges: list[tuple[int, int]] = []
        seen_edges: set[frozenset[int]] = set()
        for edge in edges:
            if len(edge) != 2:
                raise ValueError("every PEPS edge must have two endpoints")
            a, b = edge
            if (
                isinstance(a, bool)
                or isinstance(b, bool)
                or not isinstance(a, int)
                or not isinstance(b, int)
                or not 0 <= a < qubit_count
                or not 0 <= b < qubit_count
                or a == b
            ):
                raise ValueError(f"invalid PEPS edge: {edge!r}")
            key = frozenset((a, b))
            if key in seen_edges:
                raise ValueError(f"duplicate undirected PEPS edge: {edge!r}")
            seen_edges.add(key)
            normalized_edges.append((a, b))
        if qubit_count > 1 and not normalized_edges:
            raise ValueError("multi-qubit PEPS requires declared interactions")
        if rdm_radius != "complete" and (
            isinstance(rdm_radius, bool)
            or not isinstance(rdm_radius, int)
            or rdm_radius < 0
        ):
            raise ValueError("rdm_radius must be 'complete' or nonnegative")
        if optimize not in {SERIAL_CONTRACTION_POLICY, "greedy"}:
            raise ValueError("unsupported contraction policy")
        if (
            isinstance(reset_trace_distance_limit, bool)
            or not isinstance(reset_trace_distance_limit, (int, float))
            or not math.isfinite(reset_trace_distance_limit)
            or reset_trace_distance_limit < 0.0
        ):
            raise ValueError("reset trace-distance limit is invalid")

        self.qubit_count = qubit_count
        self.edges = tuple(normalized_edges)
        self.max_bond = max_bond
        self.rdm_radius = rdm_radius
        self.reset_trace_distance_limit = float(
            reset_trace_distance_limit
        )
        self.device, self.converter = self._make_converter(device_name)
        self.optimize_name = optimize
        self.optimizer = self._make_optimizer(optimize)
        self._qtn = qtn
        self.circuit = self._new_circuit()

    @staticmethod
    def _make_converter(device_name: str) -> tuple[Any, Any]:
        import torch

        if device_name == "auto":
            device_name = "cuda" if torch.cuda.is_available() else "cpu"
        if device_name == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but unavailable")
        device = torch.device(
            "cuda:0" if device_name == "cuda" else device_name
        )
        if device.type == "cuda":
            torch.cuda.set_device(device)
            torch.cuda.reset_peak_memory_stats(device)

        def convert(value: Any) -> Any:
            return torch.as_tensor(
                value,
                dtype=torch.complex128,
                device=device,
            )

        return device, convert

    @staticmethod
    def _make_optimizer(policy: str) -> Any:
        if policy == "greedy":
            return "greedy"
        import cotengra

        optimizer = cotengra.AutoHQOptimizer(parallel=False)
        if getattr(optimizer, "kwargs", {}).get("parallel") is not False:
            raise RuntimeError("serial Cotengra optimizer contract drifted")
        return optimizer

    def _new_circuit(self, psi0: Any | None = None) -> Any:
        circuit = self._qtn.CircuitPEPSSimpleUpdate(
            N=self.qubit_count,
            edges=self.edges,
            psi0=psi0,
            max_bond=self.max_bond,
            cutoff=0.0,
            renorm=False,
            gauge_smudge=GAUGE_SMUDGE,
            dtype="complex128",
            to_backend=self.converter,
            convert_eager=True,
        )
        if tuple(circuit.sites) != tuple(range(self.qubit_count)):
            raise RuntimeError(
                f"Quimb site order drifted: {circuit.sites!r}"
            )
        return circuit

    def _copy_circuit_with_private_backend_cache(self) -> Any:
        copied = self.circuit.copy()
        # Pinned Quimb copies share an id-keyed conversion cache. NumPy source
        # arrays can die between sibling branches while their converted CUDA
        # tensors remain cached, after which Python may reuse the id for a
        # different gate. Prior gates are already contracted, so every branch
        # starts with an empty private conversion cache.
        copied._backend_gate_cache = {}
        return copied

    def copy(self) -> "QuimbTrajectory":
        new = object.__new__(type(self))
        new.qubit_count = self.qubit_count
        new.edges = self.edges
        new.max_bond = self.max_bond
        new.rdm_radius = self.rdm_radius
        new.reset_trace_distance_limit = self.reset_trace_distance_limit
        new.device = self.device
        new.converter = self.converter
        new.optimize_name = self.optimize_name
        new.optimizer = self.optimizer
        new._qtn = self._qtn
        new.circuit = self._copy_circuit_with_private_backend_cache()
        return new

    def apply_unitary(
        self,
        matrix: np.ndarray,
        sites: Sequence[int],
    ) -> None:
        gate = np.asarray(matrix)
        expected_shape = (2 ** len(sites),) * 2
        if gate.dtype != np.complex128 or gate.shape != expected_shape:
            raise ValueError(
                "gate must be a complex128 matrix matching its sites"
            )
        if not np.isfinite(gate).all():
            raise ValueError("gate contains non-finite entries")
        unitarity_residual = float(
            np.max(
                np.abs(
                    gate.conj().T @ gate
                    - np.eye(gate.shape[0], dtype=np.complex128)
                )
            )
        )
        if unitarity_residual > 1e-12:
            raise ValueError(f"gate is not unitary: {unitarity_residual}")
        self.circuit.apply_gate(
            self._qtn.Gate.from_raw(gate, qubits=tuple(sites))
        )

    def _cluster_coverage(self, site: int) -> tuple[int, dict[str, Any]]:
        raw, _gauges = self.circuit.get_state(absorb_gauges="return")
        max_distance = (
            self.qubit_count
            if self.rdm_radius == "complete"
            else self.rdm_radius
        )
        cluster = raw.get_cluster(
            [site],
            gauges=None,
            max_distance=max_distance,
        )
        full_ids = set(raw.tensor_map)
        selected_ids = set(cluster.tensor_map)
        complete = selected_ids == full_ids
        if self.rdm_radius == "complete" and not complete:
            raise RuntimeError(
                "complete-graph RDM did not select every tensor id"
            )
        return int(max_distance), {
            "requested_radius": self.rdm_radius,
            "effective_max_distance": int(max_distance),
            "selected_tensor_ids": sorted(selected_ids),
            "all_tensor_ids": sorted(full_ids),
            "selected_tensor_count": len(selected_ids),
            "all_tensor_count": len(full_ids),
            "complete": complete,
            "verified_by_tensor_id_set_equality": True,
        }

    def one_site_rdm(
        self,
        site: int,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        raw, gauges = self.circuit.get_state(absorb_gauges="return")
        max_distance, coverage = self._cluster_coverage(site)
        if self.rdm_radius == "complete":
            rdm_state = raw.copy()
            rdm_state.gauge_simple_insert(gauges, smudge=0.0)
            rdm_gauges = None
            coverage["complete_graph_gauges_absorbed_exactly"] = True
        else:
            rdm_state = raw
            rdm_gauges = gauges
            coverage["complete_graph_gauges_absorbed_exactly"] = False
        rho = rdm_state.partial_trace_cluster(
            [site],
            gauges=rdm_gauges,
            optimize=self.optimizer,
            normalized=True,
            max_distance=max_distance,
            get="matrix",
        )
        observed = np.asarray(_as_numpy(rho), dtype=np.complex128)
        if observed.shape != (2, 2) or not np.isfinite(observed).all():
            raise RuntimeError("Quimb returned an invalid one-site RDM")
        return observed, coverage

    def _physical_one_slice(self, site: int) -> dict[str, Any]:
        state = self.circuit.get_state(absorb_gauges=True)
        tensor = state[state.site_tag(site)]
        physical_index = state.site_ind(site)
        axis = tensor.inds.index(physical_index)
        physical_one = _as_numpy(tensor.data).take(1, axis=axis)
        max_abs = (
            float(np.max(np.abs(physical_one)))
            if physical_one.size
            else 0.0
        )
        return {
            "physical_one_tensor_slice_exact_zero": bool(
                np.count_nonzero(physical_one) == 0
            ),
            "physical_one_tensor_slice_max_abs": max_abs,
            "physical_one_tensor_slice_entry_count": int(physical_one.size),
            "representation": "quimb_state_with_vidal_gauges_absorbed",
        }

    def verify_reset_slice(
        self,
        site: int,
    ) -> dict[str, Any]:
        """Verify an exact rank-one reset without modifying the candidate."""

        structural = self._physical_one_slice(site)
        if not structural["physical_one_tensor_slice_exact_zero"]:
            raise RuntimeError(
                "rank-one reset did not create an exact physical-one zero"
            )
        rho, coverage = self.one_site_rdm(site)
        trace_distance = _trace_distance_to_zero(rho)
        if trace_distance > self.reset_trace_distance_limit:
            raise RuntimeError(
                "rank-one reset RDM differs from the zero state: "
                f"{trace_distance}"
            )
        return {
            "qubit": site,
            "trace_distance_to_zero": trace_distance,
            "graph_coverage": coverage,
            "rank_one_reset_slice_verified_exact": True,
            "repair_projector_applied": False,
            **structural,
        }

    def _gauge_snapshot(
        self,
    ) -> dict[Any, tuple[str, tuple[int, ...], bytes]]:
        """Capture private gauge identity for an internal byte-equality check."""

        snapshot: dict[Any, tuple[str, tuple[int, ...], bytes]] = {}
        for key, gauge in self.circuit.gauges.items():
            values = np.ascontiguousarray(_as_numpy(gauge))
            if not np.isfinite(values).all():
                raise RuntimeError("simple-update gauge is non-finite")
            snapshot[key] = (
                values.dtype.str,
                tuple(values.shape),
                values.tobytes(order="C"),
            )
        return snapshot

    def _verify_reset_gauges_unchanged(
        self,
        before: Mapping[Any, tuple[str, tuple[int, ...], bytes]],
    ) -> dict[str, Any]:
        """Reject any reset-time mutation or reinterpretation of gauges."""

        after = self._gauge_snapshot()
        keys_unchanged = before.keys() == after.keys()
        shapes_unchanged = keys_unchanged and all(
            before[key][1] == after[key][1] for key in before
        )
        dtypes_unchanged = keys_unchanged and all(
            before[key][0] == after[key][0] for key in before
        )
        bytes_unchanged = keys_unchanged and all(
            before[key][2] == after[key][2] for key in before
        )
        if not (
            keys_unchanged
            and shapes_unchanged
            and dtypes_unchanged
            and bytes_unchanged
        ):
            raise RuntimeError(
                "rank-one reset changed the frozen simple-update gauges"
            )
        return {
            **RESET_GAUGE_POLICY,
            "gauge_keys_unchanged": True,
            "gauge_shapes_unchanged": True,
            "gauge_dtypes_unchanged": True,
            "gauge_bytes_unchanged": True,
            "gauge_count": len(after),
            "copied_backend_conversion_cache_isolated": True,
        }

    def measure(
        self,
        *,
        column: int,
        site: int,
        bit: int,
        reset: bool,
        prepared_rdm: tuple[np.ndarray, Mapping[str, Any]] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        if isinstance(bit, bool) or bit not in (0, 1):
            raise ValueError("measurement bit must be integer zero or one")
        if prepared_rdm is None:
            rho, coverage = self.one_site_rdm(site)
        else:
            rho = np.asarray(prepared_rdm[0], dtype=np.complex128)
            coverage = dict(prepared_rdm[1])
        probabilities, rdm_diagnostics = validated_one_site_born_pair(rho)
        selected_probability = probabilities[bit]
        row = {
            "column": column,
            "qubit": site,
            "bit": bit,
            "p0": probabilities[0],
            "p1": probabilities[1],
            "selected_probability": selected_probability,
            **rdm_diagnostics,
            "graph_coverage": coverage,
        }
        if is_structural_zero_probability(selected_probability):
            return row, None

        if reset:
            operation = np.zeros((2, 2), dtype=np.complex128)
            operation[0, bit] = 1.0 / math.sqrt(selected_probability)
        else:
            operation = np.zeros((2, 2), dtype=np.complex128)
            operation[bit, bit] = 1.0 / math.sqrt(selected_probability)

        reset_gauges_before = self._gauge_snapshot() if reset else None
        continued = self._copy_circuit_with_private_backend_cache()
        continued.apply_gate(
            self._qtn.Gate.from_raw(operation, qubits=(site,))
        )
        self.circuit = continued

        reset_row = None
        if reset:
            assert reset_gauges_before is not None
            gauge_policy = self._verify_reset_gauges_unchanged(
                reset_gauges_before
            )
            slice_row = self.verify_reset_slice(site)
            reset_row = {
                "column": column,
                "qubit": site,
                "reset_gauge_policy": gauge_policy,
                **{
                    key: value
                    for key, value in slice_row.items()
                    if key != "qubit"
                },
            }
        return row, reset_row

    def complete_state_vector(
        self,
        qubit_order: Sequence[int],
    ) -> tuple[np.ndarray, dict[str, Any]]:
        order = list(qubit_order)
        if (
            len(order) != self.qubit_count
            or sorted(order) != list(range(self.qubit_count))
        ):
            raise ValueError("complete state order must contain every qubit")
        state = self.circuit.get_state(absorb_gauges=True)
        indices = tuple(state.site_ind(site) for site in order)
        dense = state.to_dense(
            indices,
            to_ket=False,
            optimize=self.optimizer,
        )
        vector = np.asarray(_as_numpy(dense)).reshape(-1)
        if vector.dtype != np.complex128:
            raise RuntimeError(f"state dtype drifted to {vector.dtype}")
        if vector.shape != (1 << self.qubit_count,):
            raise RuntimeError(f"state shape drifted to {vector.shape}")
        if not np.isfinite(vector).all():
            raise RuntimeError("state contains non-finite amplitudes")
        norm_squared = float(np.vdot(vector, vector).real)
        if not np.isfinite(norm_squared) or norm_squared <= 0.0:
            raise RuntimeError("state has invalid norm")
        vector = np.ascontiguousarray(
            vector / math.sqrt(norm_squared),
            dtype=np.complex128,
        )
        return vector, {
            "source_kind": "complete_complex128_state_vector",
            "state_scope": "all_active_qubits",
            "qubit_order": order,
            "qubit_axis_order": order,
            "q0_bit_significance": "most_significant",
            "shape": list(vector.shape),
            "dtype": str(vector.dtype),
            "norm_squared_before_materialized_normalization": norm_squared,
            "norm_squared": float(np.vdot(vector, vector).real),
            "exact_contraction": True,
            "contraction_truncation": None,
        }

    def projected_data_state_vector(
        self,
        *,
        data_qubits: Sequence[int],
        reset_ancillas: Sequence[int],
    ) -> tuple[np.ndarray, dict[str, Any]]:
        data = list(data_qubits)
        ancillas = list(reset_ancillas)
        if data != sorted(data) or ancillas != sorted(ancillas):
            raise ValueError("data and reset-ancilla orders must be ascending")
        if (
            set(data) & set(ancillas)
            or sorted((*data, *ancillas)) != list(range(self.qubit_count))
        ):
            raise ValueError(
                "data and reset ancillas must partition every active qubit"
            )
        structural_checks = {
            site: self._physical_one_slice(site) for site in ancillas
        }
        failures = [
            site
            for site, row in structural_checks.items()
            if not row["physical_one_tensor_slice_exact_zero"]
        ]
        if failures:
            raise RuntimeError(
                "cannot project non-structurally-reset ancillas: "
                f"{failures}"
            )

        state = self.circuit.get_state(absorb_gauges=True)
        selectors = {state.site_ind(site): 0 for site in ancillas}
        projected = state.isel(selectors)
        data_indices = tuple(projected.site_ind(site) for site in data)
        dense = projected.to_dense(
            data_indices,
            to_ket=False,
            optimize=self.optimizer,
        )
        vector = np.asarray(_as_numpy(dense)).reshape(-1)
        expected_shape = (1 << len(data),)
        if vector.dtype != np.complex128:
            raise RuntimeError(f"data-vector dtype drifted to {vector.dtype}")
        if vector.shape != expected_shape:
            raise RuntimeError(
                f"data-vector shape {vector.shape} != {expected_shape}"
            )
        if not np.isfinite(vector).all():
            raise RuntimeError("data vector contains non-finite amplitudes")
        norm_squared = float(np.vdot(vector, vector).real)
        if not np.isfinite(norm_squared) or norm_squared <= 0.0:
            raise RuntimeError("projected data vector has invalid norm")
        vector = np.ascontiguousarray(
            vector / math.sqrt(norm_squared),
            dtype=np.complex128,
        )
        return vector, {
            "source_kind": "complete_complex128_state_vector",
            "state_scope": "sorted_data_qubits_after_reset_projection",
            "qubit_axis_order": data,
            "q0_bit_significance": "most_significant",
            "projected_ancillas": ancillas,
            "shape": list(vector.shape),
            "dtype": str(vector.dtype),
            "norm_squared_before_materialized_normalization": norm_squared,
            "norm_squared": float(np.vdot(vector, vector).real),
            "exact_contraction": True,
            "contraction_truncation": None,
            "sampled_or_partial_vector": False,
            "all_reset_slices_exact_zero": True,
            "reset_slice_checks": structural_checks,
        }


def _interaction_edges(fixture: Mapping[str, Any]) -> list[tuple[int, int]]:
    edges: list[tuple[int, int]] = []
    seen: set[frozenset[int]] = set()
    for operation in fixture["operations"]:
        if operation["op"] != "CX":
            continue
        a, b = operation["qubits"]
        key = frozenset((a, b))
        if key not in seen:
            seen.add(key)
            edges.append((a, b))
    if not edges:
        raise ValueError("fixture has no two-qubit interaction graph")
    adjacency = {
        site: set() for site in range(int(fixture["num_qubits"]))
    }
    for a, b in edges:
        adjacency[a].add(b)
        adjacency[b].add(a)
    reached = {0}
    frontier = [0]
    while frontier:
        site = frontier.pop()
        for neighbor in adjacency[site] - reached:
            reached.add(neighbor)
            frontier.append(neighbor)
    if reached != set(adjacency):
        raise ValueError("fixture interaction graph is disconnected")
    return edges


def _xor_rows(rows: Sequence[Sequence[int]], bits: Sequence[int]) -> list[int]:
    return [
        int(sum(bits[column] for column in row) % 2)
        for row in rows
    ]


def tracer_law_mappings(
    *,
    raw_rows: Sequence[Mapping[str, Any]],
    folded_rows: Sequence[Mapping[str, Any]],
    raw_width: int,
    detector_width: int,
    observable_width: int,
) -> tuple[dict[str, float], dict[str, float]]:
    """Adapt internal rows to the dense tracer's complete bitstring schema."""

    widths = (raw_width, detector_width, observable_width)
    if any(
        isinstance(width, bool)
        or not isinstance(width, int)
        or width < 1
        for width in widths
    ):
        raise ValueError("tracer bit widths must be positive integers")

    def bitstring(value: Any, *, width: int, label: str) -> str:
        if (
            not isinstance(value, list)
            or len(value) != width
            or any(
                isinstance(bit, bool)
                or not isinstance(bit, int)
                or bit not in (0, 1)
                for bit in value
            )
        ):
            raise ValueError(f"{label} must be an exact binary list")
        return "".join(str(bit) for bit in value)

    def probability(value: Any, *, label: str) -> float:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not 0.0 <= value <= 1.0
        ):
            raise ValueError(f"{label} has an invalid probability")
        return float(value)

    raw_law: dict[str, float] = {}
    for row in raw_rows:
        if not isinstance(row, Mapping):
            raise ValueError("raw law row must be an object")
        label = bitstring(row.get("bits"), width=raw_width, label="raw bits")
        if label in raw_law:
            raise ValueError("raw rows do not define complete raw support")
        raw_law[label] = probability(
            row.get("probability"),
            label=f"raw law {label}",
        )
    expected_raw = {
        f"{index:0{raw_width}b}" for index in range(1 << raw_width)
    }
    if set(raw_law) != expected_raw:
        raise ValueError("raw rows do not define complete raw support")

    record_width = detector_width + observable_width
    record_law: dict[str, float] = {}
    for row in folded_rows:
        if not isinstance(row, Mapping):
            raise ValueError("folded law row must be an object")
        detector_label = bitstring(
            row.get("detector_bits"),
            width=detector_width,
            label="detector bits",
        )
        observable_label = bitstring(
            row.get("observable_bits"),
            width=observable_width,
            label="observable bits",
        )
        label = detector_label + observable_label
        if label in record_law:
            raise ValueError(
                "folded rows do not define complete record support"
            )
        record_law[label] = probability(
            row.get("probability"),
            label=f"record law {label}",
        )
    expected_record = {
        f"{index:0{record_width}b}" for index in range(1 << record_width)
    }
    if set(record_law) != expected_record:
        raise ValueError("folded rows do not define complete record support")
    for name, law in (("raw", raw_law), ("record", record_law)):
        residual = abs(math.fsum(law.values()) - 1.0)
        if residual > 1e-10:
            raise ValueError(f"{name} law is not normalized: {residual}")
    return (
        {label: raw_law[label] for label in sorted(raw_law)},
        {label: record_law[label] for label in sorted(record_law)},
    )


def validate_candidate_configuration(
    *,
    distance: int,
    max_bond: int,
    rdm_radius: str | int,
) -> None:
    """Validate one frozen v2 candidate point without starting evolution."""

    if distance == 2:
        if max_bond != 8:
            raise ValueError("d2 candidate requires bond dimension D=8")
        if rdm_radius != "complete":
            raise ValueError("d2 requires verified-complete graph RDMs")
        return
    if distance == 3:
        if max_bond not in {1, 2, 4, 8}:
            raise ValueError("unsupported d3 bond dimension")
        if rdm_radius != "complete":
            raise ValueError("d3 requires verified-complete graph RDMs")
        return
    if distance == 5:
        if max_bond not in {1, 2, 4}:
            raise ValueError("unsupported d5 bond dimension")
        if rdm_radius not in {0, 1, 2, 3}:
            raise ValueError("d5 RDM radius must be one of 0,1,2,3")
        return
    raise ValueError("candidate distance must be 2, 3, or 5")


def execute_candidate(
    *,
    fixture: Mapping[str, Any],
    run_spec: Mapping[str, Any],
    branch: Mapping[str, Any],
    max_bond: int,
    rdm_radius: str | int,
    device_name: str,
    optimize: str,
    extract_state: bool,
) -> tuple[dict[str, Any], np.ndarray | None]:
    """Execute one validated branch and return neutral evidence plus state."""

    started = time.perf_counter()
    fixture_sha256 = validate_fixture(fixture)
    spec_sha256, enumeration = validate_run_spec(run_spec, fixture)
    distance = int(fixture["distance"])
    validate_candidate_configuration(
        distance=distance,
        max_bond=max_bond,
        rdm_radius=rdm_radius,
    )
    bits = validate_branch(
        branch,
        fixture_sha256=fixture_sha256,
        spec_sha256=spec_sha256,
        distance=distance,
        rounds=2,
        measurement_count=int(fixture["num_measurements"]),
        enumeration=enumeration,
    )
    spec_key = (
        "enumeration_spec_sha256" if enumeration else "run_spec_sha256"
    )
    neutral_branch = {
        "schema": BRANCH_SCHEMA,
        "fixture_sha256": fixture_sha256,
        spec_key: spec_sha256,
        "branch_id": branch["branch_id"],
        "distance": distance,
        "rounds": 2,
        "outcomes": [
            {"column": column, "bit": bit}
            for column, bit in enumerate(bits)
        ],
    }
    edges = _interaction_edges(fixture)
    trajectory = QuimbTrajectory(
        qubit_count=int(fixture["num_qubits"]),
        edges=edges,
        max_bond=max_bond,
        rdm_radius=rdm_radius,
        device_name=device_name,
        optimize=optimize,
        reset_trace_distance_limit=(1e-8 if distance == 5 else 1e-10),
    )
    data_qubits = list(fixture["frame"]["data_qubits"])
    ancillas = sorted(set(range(fixture["num_qubits"])) - set(data_qubits))
    syndrome_per_round = distance * distance - 1
    measurement_order = fixture["measurement_order"]
    measurement_column = 0
    reset_count = 0
    applied_rounds: list[int] = []
    probability_rows: list[dict[str, Any]] = []
    reset_checks: list[dict[str, Any]] = []
    selected_probabilities: list[float] = []
    preterminal: QuimbTrajectory | None = None
    structural_zero_column: int | None = None

    for operation_index, operation in enumerate(fixture["operations"]):
        kind = operation["op"]
        sites = operation["qubits"]
        if kind == "R":
            continue
        if kind == "RX":
            trajectory.apply_unitary(gate_matrix("H"), sites)
            continue
        if kind in {"H", "CX"}:
            trajectory.apply_unitary(gate_matrix(kind), sites)
            continue
        if kind not in {"M", "MX", "MR"}:
            raise RuntimeError(f"validated operation became unsupported: {kind}")
        expected_measurement = measurement_order[measurement_column]
        if kind == "MX":
            trajectory.apply_unitary(gate_matrix("H"), sites)
        row, reset_row = trajectory.measure(
            column=measurement_column,
            site=sites[0],
            bit=bits[measurement_column],
            reset=kind == "MR",
        )
        row.update(
            {
                "basis": expected_measurement["basis"],
                "reset": expected_measurement["reset"],
                "operation_index": operation_index,
            }
        )
        probability_rows.append(row)
        selected_probabilities.append(row["selected_probability"])
        if row["selected_probability"] == 0.0:
            structural_zero_column = measurement_column
            break
        if reset_row is not None:
            reset_checks.append(reset_row)
            reset_count += 1
            if reset_count % syndrome_per_round == 0:
                round_index = reset_count // syndrome_per_round - 1
                if round_index not in INTERVENTION["after_rounds"]:
                    raise RuntimeError("intervention round placement drifted")
                for data_site in data_qubits:
                    trajectory.apply_unitary(
                        gate_matrix(
                            "RY",
                            angle_radians=INTERVENTION["angle_radians"],
                        ),
                        [data_site],
                    )
                applied_rounds.append(round_index)
                if round_index == 1:
                    preterminal = trajectory.copy()
        measurement_column += 1

    if structural_zero_column is not None:
        branch_mass = 0.0
        log_branch_mass = None
        branch_mass_representable = True
        positive_mass_underflowed_to_zero = False
        state = None
        state_metadata = None
        checkpoint_reset_slices = None
        status = "structural_zero_branch"
    else:
        if measurement_column != fixture["num_measurements"]:
            raise RuntimeError("not every fixture measurement was executed")
        if reset_count != EXPECTED_FIXTURES[distance]["resets"]:
            raise RuntimeError("executed MR count differs from fixture")
        if applied_rounds != [0, 1] or preterminal is None:
            raise RuntimeError("two intervention checkpoints were not reached")
        checkpoint_reset_slices = [
            preterminal.verify_reset_slice(site)
            for site in ancillas
        ]
        if not all(
            row["physical_one_tensor_slice_exact_zero"]
            for row in checkpoint_reset_slices
        ):
            raise RuntimeError(
                "preterminal reset ancilla lacks an exact physical-one zero"
            )
        mass_evidence = stable_positive_branch_mass(selected_probabilities)
        branch_mass = mass_evidence["branch_mass"]
        log_branch_mass = mass_evidence["log_branch_mass"]
        branch_mass_representable = mass_evidence[
            "branch_mass_representable"
        ]
        positive_mass_underflowed_to_zero = mass_evidence[
            "positive_mass_underflowed_to_zero"
        ]
        state = None
        state_metadata = None
        if extract_state:
            if distance == 5:
                state, state_metadata = preterminal.projected_data_state_vector(
                    data_qubits=data_qubits,
                    reset_ancillas=ancillas,
                )
            else:
                state, state_metadata = preterminal.complete_state_vector(
                    list(range(fixture["num_qubits"]))
                )
            state_metadata.update(
                {
                    "checkpoint": PRETERMINAL_CHECKPOINT,
                    "path": None,
                    "file_sha256": None,
                }
            )
        status = "completed"

    actual_max_bond = int(
        trajectory.circuit.get_state(absorb_gauges="return")[0].max_bond()
    )
    if actual_max_bond > max_bond:
        raise RuntimeError("Quimb exceeded the declared state-bond cap")
    elapsed = time.perf_counter() - started
    completed_bits = bits if structural_zero_column is None else bits[
        : structural_zero_column + 1
    ]
    record = {
        "raw_measurements": bits,
        "detector_bits": _xor_rows(fixture["detector_rows"], bits),
        "observable_bits": _xor_rows(fixture["observable_rows"], bits),
        "absolute_xor_rows": True,
        "forced_bits_executed_before_zero": completed_bits,
    }
    summary = {
        "schema": RESULT_SCHEMA,
        "status": status,
        "claim_boundary": (
            "bounded all-qubit selected trajectory; no leakage, Kraus, "
            "decoded-LER, d5 full-law, or scalability claim"
        ),
        "fixture": {
            "schema": fixture["schema"],
            "sha256": fixture_sha256,
            "canonical_sha256": fixture_sha256,
            "stim_circuit_sha256": fixture["stim_circuit_sha256"],
            "distance": distance,
            "rounds": fixture["rounds"],
        },
        "run_spec": {
            "schema": run_spec["schema"],
            "sha256": spec_sha256,
            "canonical_sha256": spec_sha256,
            "enumeration": enumeration,
        },
        "branch": neutral_branch,
        "candidate": {
            "implementation": "quimb.CircuitPEPSSimpleUpdate",
            "dtype": "complex128",
            "requested_max_bond": max_bond,
            "actual_max_bond": actual_max_bond,
            "cutoff": 0.0,
            "renorm": False,
            "gauge_smudge": GAUGE_SMUDGE,
            "reset_trace_distance_limit": (
                trajectory.reset_trace_distance_limit
            ),
            "rdm_radius": rdm_radius,
            "interaction_edges": [list(edge) for edge in edges],
            "interaction_edge_count": len(edges),
            "one_tensor_per_active_qubit": True,
            "dummy_lattice_sites": 0,
            "device": str(trajectory.device),
            "contraction_policy": optimize,
            "selective_update_adapter_path": (
                "circuit.copy_with_private_conversion_cache_then_apply_"
                "direct_normalized_rank_one_with_pre_reset_gauges_"
                "preserved_byte_for_byte_then_exact_reset_slice_"
                "verification_without_repair"
            ),
        },
        "reset_gauge_policy": dict(RESET_GAUGE_POLICY),
        "pretarget_deviation_evidence": dict(
            PRETARGET_DEVIATION_EVIDENCE
        ),
        "checkpoint": PRETERMINAL_CHECKPOINT,
        "checkpoint_reset_slices": checkpoint_reset_slices,
        "intervention": {
            **INTERVENTION,
            "applied_after_rounds": applied_rounds,
        },
        "probability_rows": probability_rows,
        "reset_checks": reset_checks,
        "branch_mass": branch_mass,
        "log_branch_mass": log_branch_mass,
        "branch_mass_representable": branch_mass_representable,
        "positive_mass_underflowed_to_zero": (
            positive_mass_underflowed_to_zero
        ),
        "structural_zero_column": structural_zero_column,
        "record": record,
        "state": state_metadata,
        "resource_usage": {
            "elapsed_seconds": elapsed,
            **_resource_usage(trajectory.device),
        },
        "private_candidate_tensors_or_gauges_exported": False,
        "reference_tensor_or_gauge_consumed": False,
        "forbidden_substitute_used": False,
    }
    return summary, state


def enumerate_d2_laws(
    *,
    fixture: Mapping[str, Any],
    enumeration_spec: Mapping[str, Any],
    max_bond: int,
    device_name: str,
    optimize: str,
) -> dict[str, Any]:
    """Enumerate all 1024 d2 raw paths with shared Quimb prefix states."""

    started = time.perf_counter()
    fixture_sha256 = validate_fixture(fixture)
    spec_sha256, enumeration = validate_run_spec(
        enumeration_spec,
        fixture,
    )
    if fixture["distance"] != 2 or not enumeration:
        raise ValueError("full enumeration is defined only for frozen d2")
    if max_bond != 8:
        raise ValueError("frozen d2 full-law gate requires D=8")
    edges = _interaction_edges(fixture)
    root = QuimbTrajectory(
        qubit_count=fixture["num_qubits"],
        edges=edges,
        max_bond=max_bond,
        rdm_radius="complete",
        device_name=device_name,
        optimize=optimize,
    )
    operations = fixture["operations"]
    measurement_order = fixture["measurement_order"]
    data_qubits = list(fixture["frame"]["data_qubits"])
    measurement_count = fixture["num_measurements"]
    raw_probabilities = np.full(
        1 << measurement_count,
        np.nan,
        dtype=np.float64,
    )
    probability_node_count = 0
    selective_update_count = 0
    reset_check_count = 0
    structural_zero_prefix_count = 0
    max_probability_sum_residual = 0.0
    max_reset_trace_distance = 0.0
    all_rdm_coverage_complete = True
    all_reset_tensor_slices_exact_zero = True
    coverage_reference: dict[str, Any] | None = None
    completed_nonzero_leaf_count = 0

    def raw_index(bits: Sequence[int]) -> int:
        value = 0
        for bit in bits:
            value = (value << 1) | bit
        return value

    def store_zero_suffix(prefix: tuple[int, ...]) -> None:
        nonlocal structural_zero_prefix_count
        structural_zero_prefix_count += 1
        remaining = measurement_count - len(prefix)
        for suffix in itertools.product((0, 1), repeat=remaining):
            index = raw_index((*prefix, *suffix))
            if not np.isnan(raw_probabilities[index]):
                raise RuntimeError("raw support path assigned twice")
            raw_probabilities[index] = 0.0

    def walk(
        trajectory: QuimbTrajectory,
        *,
        operation_index: int,
        column: int,
        reset_count: int,
        prefix: tuple[int, ...],
        mass: float,
        applied_rounds: tuple[int, ...],
    ) -> None:
        nonlocal probability_node_count
        nonlocal selective_update_count
        nonlocal reset_check_count
        nonlocal max_probability_sum_residual
        nonlocal max_reset_trace_distance
        nonlocal all_rdm_coverage_complete
        nonlocal all_reset_tensor_slices_exact_zero
        nonlocal coverage_reference
        nonlocal completed_nonzero_leaf_count

        while operation_index < len(operations):
            operation = operations[operation_index]
            kind = operation["op"]
            sites = operation["qubits"]
            if kind == "R":
                operation_index += 1
                continue
            if kind == "RX":
                trajectory.apply_unitary(gate_matrix("H"), sites)
                operation_index += 1
                continue
            if kind in {"H", "CX"}:
                trajectory.apply_unitary(gate_matrix(kind), sites)
                operation_index += 1
                continue
            break

        if operation_index == len(operations):
            if column != measurement_count or len(prefix) != measurement_count:
                raise RuntimeError("enumeration leaf ended before all columns")
            if applied_rounds != (0, 1):
                raise RuntimeError("enumeration leaf missed an RY block")
            index = raw_index(prefix)
            if not np.isnan(raw_probabilities[index]):
                raise RuntimeError("raw support path assigned twice")
            raw_probabilities[index] = mass
            completed_nonzero_leaf_count += 1
            return

        operation = operations[operation_index]
        kind = operation["op"]
        sites = operation["qubits"]
        if kind not in {"M", "MX", "MR"}:
            raise RuntimeError("enumerator reached an unsupported operation")
        expected = measurement_order[column]
        if (
            expected["qubit"] != sites[0]
            or expected["basis"] != ("X" if kind == "MX" else "Z")
            or expected["reset"] != (kind == "MR")
        ):
            raise RuntimeError("enumerator measurement ledger drifted")
        if kind == "MX":
            trajectory.apply_unitary(gate_matrix("H"), sites)

        rho, coverage = trajectory.one_site_rdm(sites[0])
        probability_node_count += 1
        if coverage_reference is None:
            coverage_reference = coverage
        all_rdm_coverage_complete &= bool(coverage["complete"])

        for bit in (0, 1):
            child = trajectory.copy()
            try:
                row, reset_row = child.measure(
                    column=column,
                    site=sites[0],
                    bit=bit,
                    reset=kind == "MR",
                    prepared_rdm=(rho, coverage),
                )
            except Exception as error:
                raise RuntimeError(
                    "Quimb selective update failed at raw prefix "
                    f"{(*prefix, bit)}"
                ) from error
            max_probability_sum_residual = max(
                max_probability_sum_residual,
                row["probability_sum_residual"],
            )
            probability = row["selected_probability"]
            child_prefix = (*prefix, bit)
            if is_structural_zero_probability(probability):
                store_zero_suffix(child_prefix)
                continue
            selective_update_count += 1
            child_reset_count = reset_count
            child_rounds = applied_rounds
            if reset_row is not None:
                reset_check_count += 1
                child_reset_count += 1
                max_reset_trace_distance = max(
                    max_reset_trace_distance,
                    reset_row["trace_distance_to_zero"],
                )
                all_reset_tensor_slices_exact_zero &= bool(
                    reset_row["physical_one_tensor_slice_exact_zero"]
                )
                if child_reset_count % 3 == 0:
                    round_index = child_reset_count // 3 - 1
                    for data_site in data_qubits:
                        child.apply_unitary(
                            gate_matrix(
                                "RY",
                                angle_radians=INTERVENTION["angle_radians"],
                            ),
                            [data_site],
                        )
                    child_rounds = (*child_rounds, round_index)
            child_mass = mass * probability
            if child_mass == 0.0:
                raise RuntimeError(
                    "positive d2 prefix mass underflowed; refusing to "
                    "publish it as a structural zero"
                )
            walk(
                child,
                operation_index=operation_index + 1,
                column=column + 1,
                reset_count=child_reset_count,
                prefix=child_prefix,
                mass=child_mass,
                applied_rounds=child_rounds,
            )

    walk(
        root,
        operation_index=0,
        column=0,
        reset_count=0,
        prefix=(),
        mass=1.0,
        applied_rounds=(),
    )
    if np.isnan(raw_probabilities).any():
        missing = np.flatnonzero(np.isnan(raw_probabilities)).tolist()
        raise RuntimeError(f"enumeration left raw support unassigned: {missing}")
    if np.any(raw_probabilities < 0.0):
        raise RuntimeError("enumeration produced a negative raw probability")

    raw_rows: list[dict[str, Any]] = []
    folded: dict[tuple[int, ...], float] = {
        tuple(bits): 0.0
        for bits in itertools.product(
            (0, 1),
            repeat=fixture["num_detectors"] + fixture["num_observables"],
        )
    }
    for index, probability in enumerate(raw_probabilities):
        bits = [
            (index >> (measurement_count - 1 - column)) & 1
            for column in range(measurement_count)
        ]
        detector_bits = _xor_rows(fixture["detector_rows"], bits)
        observable_bits = _xor_rows(fixture["observable_rows"], bits)
        raw_rows.append(
            {
                "bits": bits,
                "probability": float(probability),
                "detector_bits": detector_bits,
                "observable_bits": observable_bits,
            }
        )
        folded[tuple((*detector_bits, *observable_bits))] += float(
            probability
        )
    folded_rows = [
        {
            "detector_bits": list(key[: fixture["num_detectors"]]),
            "observable_bits": list(key[fixture["num_detectors"] :]),
            "probability": probability,
        }
        for key, probability in sorted(folded.items())
    ]
    raw_sum = float(math.fsum(row["probability"] for row in raw_rows))
    folded_sum = float(
        math.fsum(row["probability"] for row in folded_rows)
    )
    raw_law, record_law = tracer_law_mappings(
        raw_rows=raw_rows,
        folded_rows=folded_rows,
        raw_width=measurement_count,
        detector_width=fixture["num_detectors"],
        observable_width=fixture["num_observables"],
    )
    if coverage_reference is None:
        raise RuntimeError("enumeration produced no RDM coverage evidence")
    return {
        "schema": RESULT_SCHEMA,
        "status": "completed",
        "mode": "d2_complete_raw_and_record_law",
        "claim_boundary": (
            "complete d2/r2 all-qubit Quimb raw and folded Record law; "
            "no d3/d5 full-law, leakage, Kraus, or scalability claim"
        ),
        "fixture": {
            "schema": fixture["schema"],
            "sha256": fixture_sha256,
            "canonical_sha256": fixture_sha256,
            "stim_circuit_sha256": fixture["stim_circuit_sha256"],
            "distance": 2,
            "rounds": 2,
        },
        "run_spec": {
            "schema": enumeration_spec["schema"],
            "sha256": spec_sha256,
            "canonical_sha256": spec_sha256,
            "enumeration": True,
        },
        "candidate": {
            "implementation": "quimb.CircuitPEPSSimpleUpdate",
            "dtype": "complex128",
            "requested_max_bond": max_bond,
            "cutoff": 0.0,
            "renorm": False,
            "gauge_smudge": GAUGE_SMUDGE,
            "rdm_radius": "complete",
            "interaction_edges": [list(edge) for edge in edges],
            "interaction_edge_count": len(edges),
            "contraction_policy": optimize,
            "device": str(root.device),
            "selective_update_adapter_path": (
                "circuit.copy_with_private_conversion_cache_then_apply_"
                "direct_normalized_rank_one_with_pre_reset_gauges_"
                "preserved_byte_for_byte_then_exact_reset_slice_"
                "verification_without_repair"
            ),
        },
        "reset_gauge_policy": dict(RESET_GAUGE_POLICY),
        "pretarget_deviation_evidence": dict(
            PRETARGET_DEVIATION_EVIDENCE
        ),
        "intervention": {
            **INTERVENTION,
            "applied_after_rounds_on_every_nonzero_leaf": [0, 1],
        },
        "raw_bit_order": "measurement_column_ascending_big_endian",
        "record_bit_order": (
            "detector_row_ascending_then_observable_row_ascending_big_endian"
        ),
        "raw_law": raw_law,
        "record_law": record_law,
        "tracer_law_diagnostics": {
            "raw": {
                "object": "ordered_ten_bit_raw_trajectory",
                "support_order": (
                    "lexicographic_bits_column_0_most_significant"
                ),
                "probability_sum": raw_sum,
                "normalization_residual": abs(raw_sum - 1.0),
                "structural_zero_leaf_count": int(
                    np.count_nonzero(raw_probabilities == 0.0)
                ),
            },
            "record": {
                "object": "absolute_xor_folded_detector_observable_record",
                "support_order": (
                    "lexicographic_detector_bits_then_observable_bits"
                ),
                "absolute_detector_rows": fixture["detector_rows"],
                "absolute_observable_rows": fixture["observable_rows"],
                "probability_sum": folded_sum,
                "normalization_residual": abs(folded_sum - 1.0),
            },
        },
        "diagnostics": {
            "cached_prefix_tree": True,
            "probability_node_count": probability_node_count,
            "selective_update_count": selective_update_count,
            "reset_check_count": reset_check_count,
            "structural_zero_prefix_count": structural_zero_prefix_count,
            "positive_probability_floor_used": False,
            "completed_nonzero_leaf_count": completed_nonzero_leaf_count,
            "raw_support_size": len(raw_rows),
            "folded_support_size": len(folded_rows),
            "max_probability_sum_residual": (
                max_probability_sum_residual
            ),
            "all_rdm_coverage_complete": (
                all_rdm_coverage_complete
                and coverage_reference["complete"]
            ),
            "complete_graph_coverage": coverage_reference,
            "all_reset_tensor_slices_exact_zero": (
                all_reset_tensor_slices_exact_zero
            ),
            "max_reset_trace_distance": max_reset_trace_distance,
        },
        "resource_usage": {
            "elapsed_seconds": time.perf_counter() - started,
            **_resource_usage(root.device),
        },
        "private_candidate_tensors_or_gauges_exported": False,
        "reference_tensor_or_gauge_consumed": False,
        "forbidden_substitute_used": False,
    }


def run_d2_reset_reconstruction_control(
    *,
    fixture: Mapping[str, Any],
    prefix: Sequence[int],
    device_name: str,
    optimize: str,
) -> dict[str, Any]:
    """Demonstrate why rank-one continuation must avoid ``psi0`` reseeding."""

    validate_fixture(fixture)
    frozen_prefix = [0, 0, 0, 0, 1, 0]
    if fixture["distance"] != 2 or list(prefix) != frozen_prefix:
        raise ValueError(
            "reset reconstruction control is frozen to d2 prefix 000010"
        )
    trajectory = QuimbTrajectory(
        qubit_count=fixture["num_qubits"],
        edges=_interaction_edges(fixture),
        max_bond=8,
        rdm_radius="complete",
        device_name=device_name,
        optimize=optimize,
    )
    data_qubits = list(fixture["frame"]["data_qubits"])
    column = 0
    reset_count = 0
    last_reset: dict[str, Any] | None = None
    last_site: int | None = None
    selected_probabilities: list[float] = []
    for operation in fixture["operations"]:
        kind = operation["op"]
        sites = operation["qubits"]
        if kind == "R":
            continue
        if kind == "RX":
            trajectory.apply_unitary(gate_matrix("H"), sites)
            continue
        if kind in {"H", "CX"}:
            trajectory.apply_unitary(gate_matrix(kind), sites)
            continue
        if kind == "MX":
            trajectory.apply_unitary(gate_matrix("H"), sites)
        row, reset_row = trajectory.measure(
            column=column,
            site=sites[0],
            bit=frozen_prefix[column],
            reset=kind == "MR",
        )
        selected_probabilities.append(row["selected_probability"])
        if row["selected_probability"] == 0.0:
            raise RuntimeError("frozen control prefix became structural zero")
        if reset_row is not None:
            reset_count += 1
            last_reset = reset_row
            last_site = sites[0]
            if reset_count % 3 == 0:
                for data_site in data_qubits:
                    trajectory.apply_unitary(
                        gate_matrix("RY", angle_radians=0.02),
                        [data_site],
                    )
        column += 1
        if column == len(frozen_prefix):
            break
    if last_reset is None or last_site is None or reset_count != 6:
        raise RuntimeError("frozen control did not reach the second-round MR")

    physical_state = trajectory.circuit.get_state(absorb_gauges=True)
    contaminated = trajectory.copy()
    contaminated.circuit = contaminated._new_circuit(psi0=physical_state)
    contaminated_rho, contaminated_coverage = contaminated.one_site_rdm(
        last_site
    )
    hermiticity_residual = float(
        np.max(
            np.abs(contaminated_rho - contaminated_rho.conj().T)
        )
    )
    return {
        "prefix": frozen_prefix,
        "selected_probabilities": selected_probabilities,
        "last_reset_qubit": last_site,
        "direct_public_gate": {
            "adapter_path": (
                "circuit.copy_with_private_conversion_cache_then_"
                "direct_normalized_rank_one_with_pre_reset_gauges_"
                "preserved_byte_for_byte"
            ),
            **last_reset,
        },
        "psi0_reconstruction": {
            "adapter_path": (
                "get_state_absorb_gauges_true_then_"
                "CircuitPEPSSimpleUpdate_psi0"
            ),
            "physical_one_weight": float(
                contaminated_rho[1, 1].real
            ),
            "hermiticity_residual": hermiticity_residual,
            "rho_real": contaminated_rho.real.tolist(),
            "rho_imag": contaminated_rho.imag.tolist(),
            "graph_coverage": contaminated_coverage,
            "rejected": True,
            "reason": (
                "constructor gauge_all_simple default smudge perturbs "
                "rank-deficient reset state"
            ),
        },
        "repair_selected": (
            "direct_normalized_rank_one_no_reconstruction_no_repair_"
            "no_gauge_refresh"
        ),
        "reset_gauge_policy": dict(RESET_GAUGE_POLICY),
        "pretarget_deviation_evidence": dict(
            PRETARGET_DEVIATION_EVIDENCE
        ),
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json_object(path: Path, *, label: str) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError(f"{label} JSON must contain one object")
    return payload, hashlib.sha256(raw).hexdigest()


def preflight_output_paths(
    *,
    summary_path: Path,
    state_path: Path | None,
) -> None:
    """Reject aliases or occupied outputs before any candidate work starts."""

    outputs = [summary_path]
    if state_path is not None:
        outputs.append(state_path)
    resolved = [path.resolve() for path in outputs]
    if len(set(resolved)) != len(resolved):
        raise ValueError("summary and state outputs must be distinct")
    occupied = [
        path for path in outputs if path.exists() or path.is_symlink()
    ]
    if occupied:
        raise FileExistsError(
            "refusing to use existing output: "
            + ", ".join(str(path) for path in occupied)
        )


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to replace existing output: {path}")
    encoded = canonical_json_bytes(payload)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise FileExistsError(
                f"refusing to replace existing output: {path}"
            ) from error
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_save_npy(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to replace existing output: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".npy",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            np.save(stream, array, allow_pickle=False)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as error:
            raise FileExistsError(
                f"refusing to replace existing output: {path}"
            ) from error
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def _git_clone_identity() -> dict[str, Any]:
    def run(*arguments: str) -> str:
        return subprocess.run(
            ["git", "-C", str(QUIMB_CLONE), *arguments],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    head = run("rev-parse", "HEAD")
    tree = run("rev-parse", "HEAD^{tree}")
    origin = run("remote", "get-url", "origin")
    shallow = run("rev-parse", "--is-shallow-repository")
    status = run(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignored",
    )
    if (
        head != EXPECTED_QUIMB_COMMIT
        or tree != EXPECTED_QUIMB_TREE
        or origin != "https://github.com/jcmgray/quimb.git"
        or shallow != "false"
        or status
    ):
        raise RuntimeError(
            "Quimb clone identity/pristine contract failed: "
            f"{head=}, {tree=}, {origin=}, {shallow=}, {status=!r}"
        )
    return {
        "path": str(QUIMB_CLONE.resolve()),
        "origin": origin,
        "commit": head,
        "tree": tree,
        "is_shallow": False,
        "clean_including_ignored": True,
    }


def _installed_quimb_identity() -> dict[str, Any]:
    import quimb

    distribution = metadata.distribution("quimb")
    direct_url_text = distribution.read_text("direct_url.json")
    if direct_url_text is None:
        raise RuntimeError("installed Quimb has no direct_url.json")
    direct_url = json.loads(direct_url_text)
    vcs = direct_url.get("vcs_info", {})
    if (
        vcs.get("commit_id") != EXPECTED_QUIMB_COMMIT
        or vcs.get("requested_revision") != EXPECTED_QUIMB_COMMIT
    ):
        raise RuntimeError("installed Quimb is not commit-bound")
    origin = Path(quimb.__file__).resolve(strict=True)
    prefix = Path(sys.prefix).resolve(strict=True)
    if not origin.is_relative_to(prefix):
        raise RuntimeError("installed Quimb source escapes environment prefix")
    package_root = origin.parent
    source_manifest: dict[str, str] = {}
    for source in sorted(package_root.rglob("*")):
        if source.is_symlink():
            raise RuntimeError(f"symlink in installed Quimb source: {source}")
        if not source.is_file() or source.suffix != ".py":
            continue
        resolved = source.resolve(strict=True)
        if not resolved.is_relative_to(package_root):
            raise RuntimeError("installed Quimb source escapes package root")
        source_manifest[
            resolved.relative_to(package_root).as_posix()
        ] = _file_sha256(resolved)
    if "__init__.py" not in source_manifest:
        raise RuntimeError("installed Quimb source manifest is incomplete")
    installed_source = {
        "import_origin_relative_to_prefix": (
            origin.relative_to(prefix).as_posix()
        ),
        "package_root_relative_to_prefix": (
            package_root.relative_to(prefix).as_posix()
        ),
        "python_source_manifest_sha256": dict(sorted(source_manifest.items())),
        "python_source_file_count": len(source_manifest),
        "symlinks_rejected": True,
        "prefix_escape_rejected": True,
    }
    return {
        "version": distribution.version,
        "direct_url": direct_url,
        "import_origin": str(origin),
        "installed_source": installed_source,
    }


def _normalize_distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _runtime_distribution_records() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for distribution in metadata.distributions():
        raw_name = distribution.metadata.get("Name")
        if not raw_name:
            continue
        name = _normalize_distribution_name(raw_name)
        if name == "error-coupling-simulator":
            raise RuntimeError(
                "project distribution leaked into Quimb baseline environment"
            )
        if name in rows:
            raise RuntimeError(f"duplicate installed distribution: {name}")
        direct_url = None
        record_path = None
        for item in distribution.files or ():
            if item.name == "direct_url.json":
                direct_url = json.loads(item.read_text())
            if item.name == "RECORD" and ".dist-info" in str(item):
                record_path = Path(distribution.locate_file(item))
        rows[name] = {
            "version": distribution.version,
            "direct_url": direct_url,
            "record_sha256": (
                _file_sha256(record_path)
                if record_path is not None
                else None
            ),
        }
    return dict(sorted(rows.items()))


def _runtime_conda_explicit_urls() -> list[str]:
    output = subprocess.run(
        [
            "/home/cx/miniforge3/bin/conda",
            "list",
            "-p",
            sys.prefix,
            "--explicit",
            "--sha256",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [
        line.strip()
        for line in output.splitlines()
        if line.strip().startswith("http")
    ]


def _verify_environment_lock(
    lock: Mapping[str, Any],
    *,
    clone: Mapping[str, Any],
    installed_quimb: Mapping[str, Any],
) -> dict[str, Any]:
    if lock.get("schema") != ENVIRONMENT_LOCK_SCHEMA:
        raise RuntimeError("Quimb environment lock schema mismatch")
    if lock.get("environment_name") != ENVIRONMENT_NAME:
        raise RuntimeError("Quimb environment lock name mismatch")
    if lock.get("python_version") != sys.version.split()[0]:
        raise RuntimeError("Quimb environment lock Python version mismatch")
    upstream = lock.get("upstream")
    if not isinstance(upstream, Mapping) or (
        upstream.get("commit") != clone.get("commit")
        or upstream.get("tree") != clone.get("tree")
        or upstream.get("origin") != clone.get("origin")
        or upstream.get("is_shallow") is not False
        or upstream.get("pristine_including_ignored_paths") is not True
    ):
        raise RuntimeError("Quimb environment lock upstream identity mismatch")
    selected = lock.get("selected_distribution_records")
    if not isinstance(selected, Mapping):
        raise RuntimeError("Quimb environment lock lacks selected records")
    locked_quimb = selected.get("quimb")
    if not isinstance(locked_quimb, Mapping):
        raise RuntimeError("Quimb environment lock lacks Quimb record")
    if (
        locked_quimb.get("version") != installed_quimb.get("version")
        or locked_quimb.get("direct_url")
        != installed_quimb.get("direct_url")
    ):
        raise RuntimeError("installed Quimb distribution differs from lock")
    if installed_quimb.get("installed_source") != lock.get(
        "installed_quimb_source"
    ):
        raise RuntimeError(
            "installed Quimb source bytes/origin differ from lock"
        )
    runtime_records = _runtime_distribution_records()
    if runtime_records != lock.get("pip_distribution_records"):
        raise RuntimeError(
            "installed Python distribution records differ from Quimb lock"
        )
    runtime_conda_urls = _runtime_conda_explicit_urls()
    if runtime_conda_urls != lock.get("conda_explicit_sha256_urls"):
        raise RuntimeError("Conda explicit URLs differ from Quimb lock")
    pip_check = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if pip_check != lock.get("pip_check"):
        raise RuntimeError("runtime pip check differs from Quimb lock")
    return {
        "path": str(ENVIRONMENT_LOCK.resolve()),
        "file_sha256": _file_sha256(ENVIRONMENT_LOCK),
        "schema": lock["schema"],
        "environment_name": lock["environment_name"],
        "authoritative_runtime_conformance_checked": True,
        "upstream_commit_tree_origin_exact": True,
        "pip_distribution_records_exact": True,
        "installed_quimb_source_bytes_exact": True,
        "conda_explicit_urls_exact": True,
        "pip_check_exact": True,
    }


def _resource_usage(device: Any) -> dict[str, Any]:
    import torch

    peak_device_bytes = 0
    device_evidence: dict[str, Any] = {
        "type": device.type,
        "torch_version": metadata.version("torch"),
        "torch_build_cuda": torch.version.cuda,
    }
    if device.type == "cuda":
        properties = torch.cuda.get_device_properties(device)
        peak_device_bytes = int(torch.cuda.max_memory_allocated(device))
        device_evidence.update(
            {
                "name": properties.name,
                "total_memory_bytes": int(properties.total_memory),
                "compute_capability": [
                    int(properties.major),
                    int(properties.minor),
                ],
            }
        )
    return {
        "python_peak_rss_bytes": int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        ),
        "peak_device_allocated_bytes": peak_device_bytes,
        "device": device_evidence,
    }


def validate_resource_limits(
    usage: Mapping[str, Any],
) -> dict[str, Any]:
    """Fail closed when a completed point exceeds a frozen resource gate."""

    limits = {
        "elapsed_seconds": WALL_TIME_LIMIT_SECONDS,
        "python_peak_rss_bytes": HOST_RSS_LIMIT_BYTES,
        "peak_device_allocated_bytes": DEVICE_ALLOCATION_LIMIT_BYTES,
    }
    observed: dict[str, float | int] = {}
    for field, limit in limits.items():
        value = usage.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise RuntimeError(f"invalid resource evidence: {field}")
        if value > limit:
            raise RuntimeError(
                f"formal resource limit exceeded: {field}={value}>{limit}"
            )
        observed[field] = value
    return {
        "wall_time_limit_seconds": WALL_TIME_LIMIT_SECONDS,
        "host_rss_limit_bytes": HOST_RSS_LIMIT_BYTES,
        "device_allocation_limit_bytes": DEVICE_ALLOCATION_LIMIT_BYTES,
        "observed": observed,
        "all_limits_passed": True,
    }


def _repository_input_identity(
    *,
    require_committed: bool,
) -> dict[str, Any]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    shallow = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    rows: dict[str, Any] = {}
    violations: list[str] = []
    for relative in COMMITTED_INPUTS:
        path = REPO / relative
        if not path.is_file():
            raise RuntimeError(f"claim-bearing input is absent: {relative}")
        tracked = (
            subprocess.run(
                ["git", "ls-files", "--error-unmatch", "--", relative],
                cwd=REPO,
                capture_output=True,
                text=True,
            ).returncode
            == 0
        )
        matches_head = tracked and (
            subprocess.run(
                ["git", "diff", "--quiet", "HEAD", "--", relative],
                cwd=REPO,
            ).returncode
            == 0
        )
        rows[relative] = {
            "sha256": _file_sha256(path),
            "tracked_at_head": tracked,
            "matches_head": matches_head,
        }
        if not tracked:
            violations.append(f"untracked:{relative}")
        elif not matches_head:
            violations.append(f"differs_from_head:{relative}")
    frozen_prereg_bytes = subprocess.run(
        [
            "git",
            "show",
            f"{FROZEN_V2_PREREG_COMMIT}:{FROZEN_V2_PREREG_PATH}",
        ],
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout
    frozen_prereg_sha256 = hashlib.sha256(frozen_prereg_bytes).hexdigest()
    current_prereg_sha256 = rows[FROZEN_V2_PREREG_PATH]["sha256"]
    if current_prereg_sha256 != frozen_prereg_sha256:
        violations.append("v2_prereg_differs_from_freeze_commit")
    if shallow != "false":
        violations.append("repository_is_shallow")
    if require_committed and violations:
        raise RuntimeError(
            "formal target requires committed byte-clean inputs: "
            + ", ".join(violations)
        )
    return {
        "git_head": head,
        "repository_is_shallow": shallow != "false",
        "inputs": rows,
        "frozen_v2_preregistration": {
            "commit": FROZEN_V2_PREREG_COMMIT,
            "path": FROZEN_V2_PREREG_PATH,
            "blob_sha256": frozen_prereg_sha256,
            "working_file_sha256": current_prereg_sha256,
            "matches_freeze_commit": (
                current_prereg_sha256 == frozen_prereg_sha256
            ),
        },
        "all_inputs_tracked_and_match_head": not violations,
        "formal_target_commit_gate_required_for_this_run": (
            require_committed
        ),
        "formal_target_commit_gate_passed": (
            require_committed and not violations
        ),
        "pretarget_smoke_exceptions": (
            violations if not require_committed else []
        ),
    }


def _runtime_provenance(
    *,
    fixture_path: Path,
    fixture_file_sha256: str,
    run_spec_path: Path,
    run_spec_file_sha256: str,
    branch_path: Path | None,
    branch_file_sha256: str | None,
    exact_reference_summary_path: Path | None,
    exact_reference_summary_file_sha256: str | None,
    require_committed_inputs: bool,
) -> dict[str, Any]:
    if os.environ.get("CONDA_DEFAULT_ENV") != ENVIRONMENT_NAME:
        raise RuntimeError(
            f"worker must run in Conda environment {ENVIRONMENT_NAME!r}"
        )
    if os.environ.get("PYTHONPATH"):
        raise RuntimeError("PYTHONPATH must be absent in candidate worker")
    if os.environ.get("VIRTUAL_ENV"):
        raise RuntimeError("VIRTUAL_ENV must be absent in candidate worker")
    if not sys.flags.no_user_site:
        raise RuntimeError(
            "candidate worker requires PYTHONNOUSERSITE=1"
        )
    repository_inputs = _repository_input_identity(
        require_committed=require_committed_inputs
    )
    lock = json.loads(ENVIRONMENT_LOCK.read_text(encoding="utf-8"))
    clone = _git_clone_identity()
    installed_quimb = _installed_quimb_identity()
    environment_lock = _verify_environment_lock(
        lock,
        clone=clone,
        installed_quimb=installed_quimb,
    )
    return {
        "git_head": repository_inputs["git_head"],
        "repository_inputs": repository_inputs,
        "worker_path": str(Path(__file__).resolve()),
        "worker_sha256": _file_sha256(Path(__file__).resolve()),
        "python_executable": str(Path(sys.executable).resolve()),
        "python_version": sys.version.split()[0],
        "python_prefix": str(Path(sys.prefix).resolve()),
        "conda_default_env": os.environ["CONDA_DEFAULT_ENV"],
        "pythonpath_absent": True,
        "virtual_env_absent": True,
        "user_site_disabled": True,
        "quimb_clone": clone,
        "installed_quimb": installed_quimb,
        "environment_lock": environment_lock,
        "inputs": {
            "fixture": {
                "path": str(fixture_path.resolve()),
                "file_sha256": fixture_file_sha256,
            },
            "run_spec": {
                "path": str(run_spec_path.resolve()),
                "file_sha256": run_spec_file_sha256,
            },
            "branch": (
                {
                    "path": str(branch_path.resolve()),
                    "file_sha256": branch_file_sha256,
                }
                if branch_path is not None
                else None
            ),
            "exact_reference_summary": (
                {
                    "path": str(exact_reference_summary_path.resolve()),
                    "file_sha256": (
                        exact_reference_summary_file_sha256
                    ),
                }
                if exact_reference_summary_path is not None
                else None
            ),
        },
        "selective_update_adapter": {
            "selected": (
                "CircuitPEPSSimpleUpdate.copy with private backend cache + "
                "apply_gate(Gate.from_raw(A_b/sqrt(p_b))) + preserve "
                "pre-reset simple-update gauges byte-for-byte"
            ),
            "rejected": "CircuitPEPSSimpleUpdate(psi0=poststate)",
            "rejection_source": {
                "constructor_symbol": (
                    "quimb.tensor.circuit.peps."
                    "CircuitPEPSSimpleUpdate.__init__"
                ),
                "constructor_action": (
                    "gauge_all_simple_(gauges=..., max_iterations=1)"
                ),
                "gauge_symbol": (
                    "quimb.tensor.tensor_core."
                    "TensorNetwork.gauge_all_simple"
                ),
                "default_smudge": 1e-12,
            },
        },
        "reset_gauge_policy": dict(RESET_GAUGE_POLICY),
        "pretarget_deviation_evidence": dict(
            PRETARGET_DEVIATION_EVIDENCE
        ),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--run-spec", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--branch", type=Path)
    mode.add_argument("--enumerate-d2", action="store_true")
    parser.add_argument("--exact-reference-summary", type=Path)
    parser.add_argument("--D", "--max-bond", dest="max_bond", type=int, required=True)
    parser.add_argument("--rdm-radius", required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-state", type=Path)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
    )
    parser.add_argument(
        "--optimize",
        choices=(SERIAL_CONTRACTION_POLICY, "greedy"),
        default=SERIAL_CONTRACTION_POLICY,
    )
    parser.add_argument(
        "--pretarget-smoke",
        action="store_true",
        help=(
            "Permit uncommitted implementation inputs for unit smoke only; "
            "the emitted status is never target-admissible."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if (
        not args.pretarget_smoke
        and args.optimize != SERIAL_CONTRACTION_POLICY
    ):
        raise ValueError(
            "formal target requires the frozen serial contraction policy"
        )
    if args.output_state is not None and args.enumerate_d2:
        raise ValueError(
            "enumeration has no state artifact"
        )
    preflight_output_paths(
        summary_path=args.output_summary,
        state_path=args.output_state,
    )
    fixture, fixture_file_sha256 = _read_json_object(
        args.fixture,
        label="fixture",
    )
    run_spec, run_spec_file_sha256 = _read_json_object(
        args.run_spec,
        label="run spec",
    )
    branch = None
    branch_file_sha256 = None
    if args.branch is not None:
        branch, branch_file_sha256 = _read_json_object(
            args.branch,
            label="branch",
        )
    exact_reference_summary = None
    exact_reference_summary_file_sha256 = None
    if args.exact_reference_summary is not None:
        (
            exact_reference_summary,
            exact_reference_summary_file_sha256,
        ) = _read_json_object(
            args.exact_reference_summary,
            label="exact-reference summary",
        )
    fixture_distance = fixture.get("distance")
    if args.enumerate_d2 or fixture_distance == 2:
        if exact_reference_summary is not None:
            raise ValueError(
                "d2 must not receive a selected-branch authority summary"
            )
        neutral_authority = None
    else:
        if branch is None or exact_reference_summary is None:
            raise ValueError(
                "formal d3/d5 branch execution requires an exact-reference "
                "summary"
            )
        assert exact_reference_summary_file_sha256 is not None
        neutral_authority = validate_exact_reference_summary(
            exact_reference_summary,
            summary_file_sha256=(
                exact_reference_summary_file_sha256
            ),
            branch=branch,
            run_spec=run_spec,
            fixture=fixture,
        )
    radius: str | int
    if args.rdm_radius == "complete":
        radius = "complete"
    else:
        try:
            radius = int(args.rdm_radius)
        except ValueError as error:
            raise ValueError(
                "rdm radius must be 'complete' or an integer"
            ) from error
    provenance = _runtime_provenance(
        fixture_path=args.fixture,
        fixture_file_sha256=fixture_file_sha256,
        run_spec_path=args.run_spec,
        run_spec_file_sha256=run_spec_file_sha256,
        branch_path=args.branch,
        branch_file_sha256=branch_file_sha256,
        exact_reference_summary_path=args.exact_reference_summary,
        exact_reference_summary_file_sha256=(
            exact_reference_summary_file_sha256
        ),
        require_committed_inputs=not args.pretarget_smoke,
    )
    if args.enumerate_d2:
        summary = enumerate_d2_laws(
            fixture=fixture,
            enumeration_spec=run_spec,
            max_bond=args.max_bond,
            device_name=args.device,
            optimize=args.optimize,
        )
        state = None
    else:
        assert branch is not None
        summary, state = execute_candidate(
            fixture=fixture,
            run_spec=run_spec,
            branch=branch,
            max_bond=args.max_bond,
            rdm_radius=radius,
            device_name=args.device,
            optimize=args.optimize,
            extract_state=args.output_state is not None,
        )
    summary["resource_limits"] = validate_resource_limits(
        summary["resource_usage"]
    )
    if state is not None:
        if args.output_state is None:
            raise RuntimeError("materialized state has no output path")
        _atomic_save_npy(args.output_state, state)
        state_metadata = summary.get("state")
        if not isinstance(state_metadata, dict):
            raise RuntimeError("state metadata is absent")
        state_metadata["path"] = str(args.output_state.resolve())
        state_metadata["file_sha256"] = _file_sha256(args.output_state)
    elif args.output_state is not None:
        raise RuntimeError(
            "state output was requested but the branch has no materialized state"
        )
    summary["provenance"] = provenance
    summary["branch_authority"] = (
        neutral_authority["authority"]
        if neutral_authority is not None
        else None
    )
    summary["exact_reference_authority_source"] = neutral_authority
    summary["formal_target_output"] = not args.pretarget_smoke
    if args.pretarget_smoke:
        summary["status"] = "pretarget_smoke"
    summary["output"] = {
        "summary_path": str(args.output_summary.resolve()),
        "atomic_write": True,
        "state_path": (
            str(args.output_state.resolve())
            if args.output_state is not None
            else None
        ),
    }
    _atomic_write_json(args.output_summary, summary)
    print(json.dumps(summary, allow_nan=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
