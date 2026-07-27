#!/usr/bin/env python3
"""Independent exact data-projector reference for the frozen XZZX fixture.

The formal worker consumes only the neutral fixture/run specification.  It
does not import a circuit runtime or tensor-network package.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import resource
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Mapping, Sequence

import numpy as np


FIXTURE_SCHEMA = "error_coupling_simulator.external_xzzx_record_peps.fixture.v1"
RUN_SPEC_SCHEMA = "error_coupling_simulator.external_xzzx_record_peps.run_spec.v2"
BRANCH_SCHEMA = "error_coupling_simulator.external_xzzx_record_peps.branch.v1"
RESULT_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_exact_data_reference.v1"
)
BRANCH_AUTHORITY_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_exact_data_reference."
    "branch_authority.v1"
)
LEDGER_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_exact_data_reference."
    "projector_ledger.v1"
)
PRETERMINAL_CHECKPOINT = (
    "after_round_1_ry_before_terminal_data_measurements"
)
REFERENCE_PROBABILITY_TOLERANCE = 1e-12
SELECTED_BRANCH_MIN_PROBABILITY = 1e-12
SELECTOR_DOMAIN = b"ECS-XZZX-DATA-ONLY-BRANCH-V2\x00"
EXPECTED_FIXTURE_SHA256 = {
    2: "dbf2a0979c9a4cd0a95f2afe393083d97a27ea1e90720596352a191010beb0f5",
    3: "3b2bf7d81f7241e0a3b6abb14c76474c362e696cf374c55e20e3d121946bbf3c",
    5: "659fda875a91f2a6e3c64f8f03487b5a431edecb9849dd897bf2e6f390583495",
}
EXPECTED_STIM_SHA256 = {
    2: "18492ad9bc8b286d1cf9f97f45546fac40552a10d83be9ef61fa892a941cb671",
    3: "7067b1241251bd7558e7dc85b2f84bc13a45c1217a49f8fcfa2e51205879ecb0",
    5: "be26b8708efe36a027bcf79074bc936de552b1a5d22b35b627d7d9cdbb27f008",
}
EXPECTED_RUN_SPEC_SHA256 = {
    3: "7dfa0a8ef9620712e6ea190aeda651c681295f9841963ce77686640255cc22a9",
    5: "06151ea1244495475259d40bf6ca7ad16cbdaf5f8184ee61b344fb2e81b413a4",
}
EXPECTED_SEEDS = {3: 2026072603, 5: 2026072605}
EXPECTED_D5_DATA_ORDER = [
    0,
    2,
    3,
    5,
    6,
    7,
    9,
    11,
    13,
    15,
    18,
    20,
    22,
    24,
    26,
    27,
    29,
    31,
    33,
    35,
    38,
    40,
    42,
    44,
    46,
]
REPO = Path(__file__).resolve().parents[2]
FORMAL_INPUT_PATHS = (
    "docs/METRICS.md",
    (
        "docs/simulator_validation/"
        "PEPS_XZZX_MEASUREMENT_RESET_RECORD_PREREG_V2_2026-07-27.md"
    ),
    "scripts/external_baselines/emit_xzzx_record_peps_fixture.py",
    "scripts/external_baselines/xzzx_record_exact_data_reference.py",
    "tests/test_external_xzzx_record_exact_data_reference.py",
    "core-environment-cu130.lock",
)
REFERENCE_SUMMARY_FIELDS = {
    "schema",
    "status",
    "method",
    "claim_boundary",
    "fixture",
    "run_spec",
    "checkpoint",
    "branch",
    "branch_authority",
    "projector_ledger",
    "probability_rows",
    "branch_mass",
    "log_branch_mass",
    "branch_mass_representable",
    "positive_mass_underflowed_to_zero",
    "record",
    "state",
    "reference_state_contract",
    "input_provenance",
    "resource_usage",
    "candidate_payload_consumed",
    "external_circuit_runtime_imported",
    "forbidden_substitute_used",
}


class SelectedBranchUnavailable(RuntimeError):
    """The frozen selector chose a branch below the preregistered gate."""


def selector_digest(
    *,
    seed: int,
    column: int,
    prefix: Sequence[int],
) -> bytes:
    if (
        isinstance(seed, bool)
        or not isinstance(seed, int)
        or not 0 <= seed < (1 << 64)
    ):
        raise ValueError("selector seed must be an unsigned 64-bit integer")
    if (
        isinstance(column, bool)
        or not isinstance(column, int)
        or not 0 <= column < (1 << 32)
    ):
        raise ValueError("selector column must be an unsigned 32-bit integer")
    prefix_bits = list(prefix)
    if column != len(prefix_bits):
        raise ValueError("selector column must equal prefix length")
    if any(
        isinstance(bit, bool) or not isinstance(bit, int) or bit not in (0, 1)
        for bit in prefix_bits
    ):
        raise ValueError("selector prefix must contain integer bits")
    payload = (
        SELECTOR_DOMAIN
        + seed.to_bytes(8, "big")
        + column.to_bytes(4, "big")
        + bytes(prefix_bits)
    )
    return hashlib.sha256(payload).digest()


def born_bit_from_hash_integer(p0: float, hash_integer: int) -> int:
    if (
        isinstance(p0, bool)
        or not isinstance(p0, float)
        or not math.isfinite(p0)
        or not 0.0 <= p0 <= 1.0 + REFERENCE_PROBABILITY_TOLERANCE
    ):
        raise ValueError("p0 must be a finite binary64 probability")
    if (
        isinstance(hash_integer, bool)
        or not isinstance(hash_integer, int)
        or not 0 <= hash_integer < (1 << 256)
    ):
        raise ValueError("selector hash must be an unsigned 256-bit integer")
    numerator, denominator = p0.as_integer_ratio()
    return (
        0
        if hash_integer * denominator < numerator * (1 << 256)
        else 1
    )


def sha256_prefix_born_bit(
    p0: float,
    *,
    seed: int,
    column: int,
    prefix: Sequence[int],
) -> int:
    digest = selector_digest(seed=seed, column=column, prefix=prefix)
    return born_bit_from_hash_integer(p0, int.from_bytes(digest, "big"))


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_fixture(fixture: Mapping[str, Any]) -> str:
    _frame_sets(fixture)
    distance = fixture.get("distance")
    if distance not in EXPECTED_FIXTURE_SHA256:
        raise ValueError("unsupported fixture distance")
    digest = canonical_json_sha256(fixture)
    if digest != EXPECTED_FIXTURE_SHA256[distance]:
        raise ValueError("fixture canonical SHA mismatch")
    if (
        fixture.get("rounds") != 2
        or fixture.get("stim_circuit_sha256")
        != EXPECTED_STIM_SHA256[distance]
    ):
        raise ValueError("fixture schedule or Stim identity mismatch")
    return digest


def validate_run_spec(
    run_spec: Mapping[str, Any],
    fixture: Mapping[str, Any],
) -> str:
    fixture_sha256 = validate_fixture(fixture)
    distance = fixture["distance"]
    if distance not in EXPECTED_RUN_SPEC_SHA256:
        raise ValueError("formal exact-data run spec requires d3 or d5")
    if run_spec.get("schema") != RUN_SPEC_SCHEMA:
        raise ValueError("unsupported exact-data run-spec schema")
    digest = canonical_json_sha256(run_spec)
    if digest != EXPECTED_RUN_SPEC_SHA256[distance]:
        raise ValueError("run-spec canonical SHA mismatch")
    selector = run_spec.get("reference_branch", {}).get("selector")
    if (
        run_spec.get("base_fixture_sha256") != fixture_sha256
        or run_spec.get("stim_circuit_sha256")
        != fixture["stim_circuit_sha256"]
        or run_spec.get("distance") != distance
        or run_spec.get("rounds") != 2
        or run_spec.get("reference_branch", {}).get("sampler")
        != "numpy_exact_data_projector"
        or run_spec.get("reference_branch", {}).get("shots") != 1
        or not isinstance(selector, Mapping)
        or selector.get("algorithm") != "sha256_prefix_born_v1"
        or selector.get("seed") != EXPECTED_SEEDS[distance]
        or run_spec.get("reference_state")
        != {
            "checkpoint": PRETERMINAL_CHECKPOINT,
            "method": "numpy_exact_data_projector",
            "probability_floor": None,
            "truncation": None,
        }
    ):
        raise ValueError("run spec does not bind the frozen exact-data route")
    if distance == 5 and fixture["frame"]["data_qubits"] != EXPECTED_D5_DATA_ORDER:
        raise ValueError("d5 data-axis order differs from preregistration")
    return digest


def _frame_sets(
    fixture: Mapping[str, Any],
) -> tuple[list[int], set[int], set[int]]:
    if fixture.get("schema") != FIXTURE_SCHEMA:
        raise ValueError("unsupported fixture schema")
    frame = fixture.get("frame")
    if not isinstance(frame, Mapping):
        raise ValueError("fixture frame is absent")
    data_order = frame.get("data_qubits")
    hadamard_order = frame.get("hadamard_frame_data_qubits")
    if (
        not isinstance(data_order, list)
        or not data_order
        or any(
            isinstance(qubit, bool) or not isinstance(qubit, int)
            for qubit in data_order
        )
        or data_order != sorted(data_order)
        or len(set(data_order)) != len(data_order)
    ):
        raise ValueError("data qubits must be unique and strictly ascending")
    if (
        not isinstance(hadamard_order, list)
        or any(
            isinstance(qubit, bool) or not isinstance(qubit, int)
            for qubit in hadamard_order
        )
        or hadamard_order != sorted(hadamard_order)
        or len(set(hadamard_order)) != len(hadamard_order)
        or not set(hadamard_order) <= set(data_order)
    ):
        raise ValueError("Hadamard-frame data qubits are invalid")
    num_qubits = fixture.get("num_qubits")
    if (
        isinstance(num_qubits, bool)
        or not isinstance(num_qubits, int)
        or num_qubits <= 0
        or data_order[-1] >= num_qubits
    ):
        raise ValueError("fixture qubit count is invalid")
    data = set(data_order)
    ancillas = set(range(num_qubits)) - data
    if not ancillas:
        raise ValueError("fixture has no syndrome ancillas")
    return list(data_order), set(hadamard_order), ancillas


def _commutes(
    left: Sequence[Sequence[Any]],
    right: Sequence[Sequence[Any]],
) -> bool:
    left_map = {int(qubit): str(pauli) for qubit, pauli in left}
    right_map = {int(qubit): str(pauli) for qubit, pauli in right}
    parity = 0
    for qubit in set(left_map) & set(right_map):
        if left_map[qubit] != right_map[qubit]:
            parity ^= 1
    return parity == 0


def validate_commuting_checks(checks: Sequence[Mapping[str, Any]]) -> None:
    for index, left in enumerate(checks):
        if left.get("sign") != 1:
            raise ValueError("projector check sign must be +1")
        support = left.get("support")
        if (
            not isinstance(support, list)
            or not support
            or support != sorted(support)
            or any(
                not isinstance(row, list)
                or len(row) != 2
                or row[1] not in {"X", "Z"}
                for row in support
            )
        ):
            raise ValueError("projector check support is invalid")
        for right in checks[index + 1 :]:
            if not _commutes(support, right["support"]):
                raise ValueError("projector checks do not commute")


def _validated_state(
    state: object,
    *,
    data_order: Sequence[int],
) -> np.ndarray:
    vector = np.asarray(state)
    if vector.dtype != np.complex128:
        raise ValueError("exact state must have dtype complex128")
    if vector.ndim != 1 or vector.shape != (1 << len(data_order),):
        raise ValueError("exact state shape does not match data axes")
    if not np.all(np.isfinite(vector)):
        raise ValueError("exact state contains nonfinite amplitudes")
    return vector


def pauli_action(
    state: object,
    *,
    support: Sequence[Sequence[Any]],
    data_order: Sequence[int],
) -> np.ndarray:
    vector = _validated_state(state, data_order=data_order)
    if (
        list(data_order) != sorted(data_order)
        or len(set(data_order)) != len(data_order)
    ):
        raise ValueError("data axis order must be unique and ascending")
    axes = {qubit: axis for axis, qubit in enumerate(data_order)}
    support_rows = [list(row) for row in support]
    if (
        not support_rows
        or support_rows != sorted(support_rows)
        or len({row[0] for row in support_rows}) != len(support_rows)
        or any(
            len(row) != 2
            or row[0] not in axes
            or row[1] not in {"X", "Z"}
            for row in support_rows
        )
    ):
        raise ValueError("Pauli support is invalid")
    tensor = vector.reshape((2,) * len(data_order))
    flip_axes = tuple(
        axes[qubit] for qubit, pauli in support_rows if pauli == "X"
    )
    transformed = np.array(
        np.flip(tensor, axis=flip_axes) if flip_axes else tensor,
        copy=True,
    )
    for qubit, pauli in support_rows:
        if pauli == "Z":
            index: list[Any] = [slice(None)] * len(data_order)
            index[axes[qubit]] = 1
            transformed[tuple(index)] *= -1.0
    return transformed.reshape(-1)


def projector_probabilities(
    state: object,
    *,
    support: Sequence[Sequence[Any]],
    data_order: Sequence[int],
    sign: int,
) -> tuple[float, float, np.ndarray, np.ndarray]:
    """Return both Born probabilities from explicit projected-vector norms."""

    vector = _validated_state(state, data_order=data_order)
    if isinstance(sign, bool) or sign not in {-1, 1}:
        raise ValueError("projector sign must be integer +1 or -1")
    transformed = pauli_action(
        vector,
        support=support,
        data_order=data_order,
    )
    signed = sign * transformed
    plus = 0.5 * (vector + signed)
    minus = 0.5 * (vector - signed)
    p0 = float(np.vdot(plus, plus).real)
    p1 = float(np.vdot(minus, minus).real)
    if (
        not math.isfinite(p0)
        or not math.isfinite(p1)
        or p0 < 0.0
        or p1 < 0.0
    ):
        raise ValueError("projected-vector probability is invalid")
    return p0, p1, plus, minus


def select_projector(
    state: object,
    bit: int,
    *,
    support: Sequence[Sequence[Any]],
    data_order: Sequence[int],
    sign: int,
    minimum_probability: float | None = None,
) -> tuple[np.ndarray, tuple[float, float]]:
    if isinstance(bit, bool) or not isinstance(bit, int) or bit not in (0, 1):
        raise ValueError("selected bit must be integer zero or one")
    if minimum_probability is not None and (
        not math.isfinite(minimum_probability) or minimum_probability <= 0.0
    ):
        raise ValueError("minimum probability must be finite and positive")
    p0, p1, plus, minus = projector_probabilities(
        state,
        support=support,
        data_order=data_order,
        sign=sign,
    )
    probability = (p0, p1)[bit]
    if probability <= 0.0:
        raise SelectedBranchUnavailable("selected branch has zero probability")
    if (
        minimum_probability is not None
        and probability < minimum_probability
    ):
        raise SelectedBranchUnavailable(
            f"selected branch probability is below {minimum_probability:g}"
        )
    selected = (plus, minus)[bit] / math.sqrt(probability)
    if not np.all(np.isfinite(selected)):
        raise ValueError("selected poststate is nonfinite")
    return selected, (p0, p1)


def initial_data_state(
    fixture: Mapping[str, Any],
) -> tuple[np.ndarray, list[int]]:
    data_order, hadamard_frame, _ancillas = _frame_sets(fixture)
    state = np.ones(1, dtype=np.complex128)
    for qubit in data_order:
        local = (
            np.asarray([1.0, 1.0], dtype=np.complex128) / math.sqrt(2.0)
            if qubit in hadamard_frame
            else np.asarray([1.0, 0.0], dtype=np.complex128)
        )
        state = np.kron(state, local)
    return state, data_order


def apply_ry_all(
    state: object,
    *,
    data_order: Sequence[int],
    angle_radians: float,
) -> np.ndarray:
    vector = _validated_state(state, data_order=data_order)
    if not math.isfinite(angle_radians):
        raise ValueError("RY angle must be finite")
    cosine = math.cos(angle_radians / 2.0)
    sine = math.sin(angle_radians / 2.0)
    tensor = vector.reshape((2,) * len(data_order))
    for axis in range(len(data_order)):
        zero_index: list[Any] = [slice(None)] * len(data_order)
        one_index: list[Any] = [slice(None)] * len(data_order)
        zero_index[axis] = 0
        one_index[axis] = 1
        zero = np.array(tensor[tuple(zero_index)], copy=True)
        one = np.array(tensor[tuple(one_index)], copy=True)
        tensor[tuple(zero_index)] = cosine * zero - sine * one
        tensor[tuple(one_index)] = sine * zero + cosine * one
    return tensor.reshape(-1)


def fold_record(
    bits: Sequence[int],
    detector_rows: Sequence[Sequence[int]],
    observable_rows: Sequence[Sequence[int]],
) -> tuple[list[int], list[int]]:
    raw = list(bits)
    if any(
        isinstance(bit, bool) or not isinstance(bit, int) or bit not in (0, 1)
        for bit in raw
    ):
        raise ValueError("raw record must contain integer bits")

    def fold(rows: Sequence[Sequence[int]]) -> list[int]:
        folded: list[int] = []
        for row in rows:
            columns = list(row)
            if not columns or any(
                isinstance(column, bool)
                or not isinstance(column, int)
                or not 0 <= column < len(raw)
                for column in columns
            ):
                raise ValueError("absolute XOR row is invalid")
            folded.append(sum(raw[column] for column in columns) % 2)
        return folded

    return fold(detector_rows), fold(observable_rows)


def stable_positive_branch_mass(
    probabilities: Sequence[float],
) -> dict[str, Any]:
    values = list(probabilities)
    if not values or any(
        isinstance(value, bool)
        or not isinstance(value, float)
        or not math.isfinite(value)
        or value <= 0.0
        or value > 1.0 + REFERENCE_PROBABILITY_TOLERANCE
        for value in values
    ):
        raise ValueError("branch probabilities must be finite and positive")
    log_mass = math.fsum(math.log(value) for value in values)
    product = math.prod(values)
    underflow = product == 0.0
    return {
        "branch_mass": None if underflow else product,
        "log_branch_mass": log_mass,
        "branch_mass_representable": not underflow,
        "positive_mass_underflowed_to_zero": underflow,
    }


def phase_invariant_fidelity(left: object, right: object) -> float:
    left_vector = np.asarray(left)
    right_vector = np.asarray(right)
    if (
        left_vector.dtype != np.complex128
        or right_vector.dtype != np.complex128
        or left_vector.ndim != 1
        or right_vector.shape != left_vector.shape
        or not np.all(np.isfinite(left_vector))
        or not np.all(np.isfinite(right_vector))
    ):
        raise ValueError("fidelity requires equal finite complex128 vectors")
    left_norm = float(np.vdot(left_vector, left_vector).real)
    right_norm = float(np.vdot(right_vector, right_vector).real)
    if left_norm <= 0.0 or right_norm <= 0.0:
        raise ValueError("fidelity operands must have positive norm")
    overlap = np.vdot(left_vector, right_vector)
    return float(abs(overlap) ** 2 / (left_norm * right_norm))


def embed_data_state(
    state: object,
    *,
    data_order: Sequence[int],
    num_qubits: int,
) -> np.ndarray:
    vector = _validated_state(state, data_order=data_order)
    if (
        isinstance(num_qubits, bool)
        or not isinstance(num_qubits, int)
        or num_qubits <= 0
        or not data_order
        or min(data_order) < 0
        or max(data_order) >= num_qubits
    ):
        raise ValueError("all-active qubit count is invalid")
    full = np.zeros((2,) * num_qubits, dtype=np.complex128)
    data = set(data_order)
    index = tuple(
        slice(None) if qubit in data else 0 for qubit in range(num_qubits)
    )
    full[index] = vector.reshape((2,) * len(data_order))
    return full.reshape(-1)


def project_all_active_to_data(
    state: object,
    *,
    data_order: Sequence[int],
    num_qubits: int,
) -> np.ndarray:
    vector = np.asarray(state)
    if (
        vector.dtype != np.complex128
        or vector.ndim != 1
        or vector.shape != (1 << num_qubits,)
        or not np.all(np.isfinite(vector))
    ):
        raise ValueError("all-active state is not a complete complex128 vector")
    if (
        list(data_order) != sorted(data_order)
        or len(set(data_order)) != len(data_order)
        or not data_order
        or min(data_order) < 0
        or max(data_order) >= num_qubits
    ):
        raise ValueError("data axis order is invalid")
    data = set(data_order)
    index = tuple(
        slice(None) if qubit in data else 0 for qubit in range(num_qubits)
    )
    return np.array(
        vector.reshape((2,) * num_qubits)[index].reshape(-1),
        copy=True,
    )


def _execute_branch(
    fixture: Mapping[str, Any],
    chooser: Callable[[int, Mapping[str, Any], tuple[float, float]], int],
    *,
    branch_id: str,
    minimum_probability: float | None,
) -> dict[str, Any]:
    ledger = derive_projector_ledger(fixture)
    measurements = fixture["measurement_order"]
    data_order = ledger["data_order"]
    state, initialized_order = initial_data_state(fixture)
    if initialized_order != data_order:
        raise RuntimeError("initial-state data order drifted")
    selected_probabilities: list[float] = []
    probability_rows: list[dict[str, Any]] = []
    bits: list[int] = []
    column = 0

    for round_checks in ledger["rounds"]:
        for check in round_checks:
            measurement = measurements[column]
            if (
                measurement.get("column") != column
                or measurement.get("qubit") != check["ancilla"]
                or measurement.get("basis") != "Z"
                or measurement.get("reset") is not True
            ):
                raise ValueError("syndrome measurement/check order mismatch")
            p0, p1, _plus, _minus = projector_probabilities(
                state,
                support=check["support"],
                data_order=data_order,
                sign=check["sign"],
            )
            if abs((p0 + p1) - 1.0) > REFERENCE_PROBABILITY_TOLERANCE:
                raise ValueError("reference Bernoulli row is not normalized")
            bit = chooser(column, measurement, (p0, p1))
            state, _probabilities = select_projector(
                state,
                bit,
                support=check["support"],
                data_order=data_order,
                sign=check["sign"],
                minimum_probability=minimum_probability,
            )
            selected = (p0, p1)[bit]
            probability_rows.append(
                {
                    "column": column,
                    "qubit": int(measurement["qubit"]),
                    "basis": "Z",
                    "reset": True,
                    "bit": bit,
                    "p0": p0,
                    "p1": p1,
                    "selected_probability": selected,
                }
            )
            selected_probabilities.append(selected)
            bits.append(bit)
            column += 1
        state = apply_ry_all(
            state,
            data_order=data_order,
            angle_radians=0.02,
        )
    preterminal = np.array(state, copy=True)

    for measurement in measurements[column:]:
        if (
            measurement.get("column") != column
            or measurement.get("reset") is not False
            or measurement.get("qubit") not in set(data_order)
            or measurement.get("basis") not in {"X", "Z"}
        ):
            raise ValueError("terminal measurement order mismatch")
        support = [[
            int(measurement["qubit"]),
            str(measurement["basis"]),
        ]]
        p0, p1, _plus, _minus = projector_probabilities(
            state,
            support=support,
            data_order=data_order,
            sign=1,
        )
        if abs((p0 + p1) - 1.0) > REFERENCE_PROBABILITY_TOLERANCE:
            raise ValueError("reference Bernoulli row is not normalized")
        bit = chooser(column, measurement, (p0, p1))
        state, _probabilities = select_projector(
            state,
            bit,
            support=support,
            data_order=data_order,
            sign=1,
            minimum_probability=minimum_probability,
        )
        selected = (p0, p1)[bit]
        probability_rows.append(
            {
                "column": column,
                "qubit": int(measurement["qubit"]),
                "basis": str(measurement["basis"]),
                "reset": False,
                "bit": bit,
                "p0": p0,
                "p1": p1,
                "selected_probability": selected,
            }
        )
        selected_probabilities.append(selected)
        bits.append(bit)
        column += 1
    if column != fixture.get("num_measurements"):
        raise RuntimeError("not every measurement column was executed")
    detector_bits, observable_bits = fold_record(
        bits,
        fixture["detector_rows"],
        fixture["observable_rows"],
    )
    mass = stable_positive_branch_mass(selected_probabilities)
    return {
        "branch_id": branch_id,
        "raw_bits": tuple(bits),
        "probability_rows": probability_rows,
        "conditional_probabilities": tuple(selected_probabilities),
        **mass,
        "detector_bits": detector_bits,
        "observable_bits": observable_bits,
        "preterminal_data_state": preterminal,
        "final_data_state": state,
        "checkpoint": PRETERMINAL_CHECKPOINT,
        "projector_ledger": ledger,
    }


def execute_forced_branch(
    fixture: Mapping[str, Any],
    bits: Sequence[int],
    *,
    branch_id: str = "exact-data-forced-control",
) -> dict[str, Any]:
    forced = list(bits)
    if len(forced) != fixture.get("num_measurements") or any(
        isinstance(bit, bool) or not isinstance(bit, int) or bit not in (0, 1)
        for bit in forced
    ):
        raise ValueError("forced branch must contain one integer bit per column")

    def chooser(
        column: int,
        _measurement: Mapping[str, Any],
        _probabilities: tuple[float, float],
    ) -> int:
        return forced[column]

    return _execute_branch(
        fixture,
        chooser,
        branch_id=branch_id,
        minimum_probability=None,
    )


def execute_primary_branch(
    fixture: Mapping[str, Any],
    run_spec: Mapping[str, Any],
) -> dict[str, Any]:
    validate_run_spec(run_spec, fixture)
    seed = run_spec["reference_branch"]["selector"]["seed"]
    prefix: list[int] = []

    def chooser(
        column: int,
        _measurement: Mapping[str, Any],
        probabilities: tuple[float, float],
    ) -> int:
        bit = sha256_prefix_born_bit(
            probabilities[0],
            seed=seed,
            column=column,
            prefix=prefix,
        )
        prefix.append(bit)
        return bit

    return _execute_branch(
        fixture,
        chooser,
        branch_id=(
            f"xzzx-exact-data-d{fixture['distance']}-seed-{seed}-primary"
        ),
        minimum_probability=SELECTED_BRANCH_MIN_PROBABILITY,
    )


def execute_alternate_branch(
    fixture: Mapping[str, Any],
    primary_bits: Sequence[int],
    *,
    branch_id: str = "xzzx-exact-data-d3-alternate",
    minimum_probability: float | None = None,
) -> dict[str, Any]:
    primary = list(primary_bits)
    if fixture.get("distance") != 3:
        raise ValueError("the frozen alternate rule is registered only for d3")
    if len(primary) != fixture.get("num_measurements") or any(
        isinstance(bit, bool) or not isinstance(bit, int) or bit not in (0, 1)
        for bit in primary
    ):
        raise ValueError("primary branch must contain one integer bit per column")
    flipped_column: int | None = None

    def chooser(
        column: int,
        measurement: Mapping[str, Any],
        probabilities: tuple[float, float],
    ) -> int:
        nonlocal flipped_column
        if flipped_column is None:
            if measurement.get("reset") is True:
                opposite = 1 - primary[column]
                if probabilities[opposite] >= 1e-8:
                    flipped_column = column
                    return opposite
            return primary[column]
        return 0 if probabilities[0] >= probabilities[1] else 1

    result = _execute_branch(
        fixture,
        chooser,
        branch_id=branch_id,
        minimum_probability=minimum_probability,
    )
    if flipped_column is None:
        raise SelectedBranchUnavailable("frozen d3 alternate is unavailable")
    result["alternate_flip_column"] = flipped_column
    return result


def neutral_branch(
    fixture: Mapping[str, Any],
    run_spec: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> dict[str, Any]:
    fixture_sha256 = validate_fixture(fixture)
    run_spec_sha256 = validate_run_spec(run_spec, fixture)
    bits = list(execution.get("raw_bits", ()))
    if len(bits) != fixture["num_measurements"] or any(
        isinstance(bit, bool) or not isinstance(bit, int) or bit not in (0, 1)
        for bit in bits
    ):
        raise ValueError("execution lacks one integer bit per measurement")
    branch_id = execution.get("branch_id")
    if not isinstance(branch_id, str) or not branch_id:
        raise ValueError("execution branch id must be nonempty")
    return {
        "schema": BRANCH_SCHEMA,
        "fixture_sha256": fixture_sha256,
        "run_spec_sha256": run_spec_sha256,
        "distance": fixture["distance"],
        "rounds": 2,
        "branch_id": branch_id,
        "outcomes": [
            {"column": column, "bit": bit}
            for column, bit in enumerate(bits)
        ],
    }


def _validate_neutral_branch(
    branch: Mapping[str, Any],
    *,
    fixture_sha256: str,
    run_spec_sha256: str,
    distance: int,
    measurement_count: int,
) -> list[int]:
    expected_fields = {
        "schema",
        "fixture_sha256",
        "run_spec_sha256",
        "distance",
        "rounds",
        "branch_id",
        "outcomes",
    }
    if (
        set(branch) != expected_fields
        or branch.get("schema") != BRANCH_SCHEMA
        or branch.get("fixture_sha256") != fixture_sha256
        or branch.get("run_spec_sha256") != run_spec_sha256
        or branch.get("distance") != distance
        or branch.get("rounds") != 2
        or not isinstance(branch.get("branch_id"), str)
        or not branch["branch_id"]
    ):
        raise ValueError("neutral branch identity/field set mismatch")
    outcomes = branch.get("outcomes")
    if not isinstance(outcomes, list) or len(outcomes) != measurement_count:
        raise ValueError("neutral branch outcome count mismatch")
    bits: list[int] = []
    for column, row in enumerate(outcomes):
        if (
            not isinstance(row, Mapping)
            or set(row) != {"column", "bit"}
            or row.get("column") != column
            or isinstance(row.get("bit"), bool)
            or not isinstance(row.get("bit"), int)
            or row.get("bit") not in (0, 1)
        ):
            raise ValueError("neutral branch outcomes are not exact ordered bits")
        bits.append(row["bit"])
    return bits


def primary_branch_authority(
    branch: Mapping[str, Any],
    run_spec: Mapping[str, Any],
) -> dict[str, Any]:
    selector = run_spec.get("reference_branch", {}).get("selector")
    if not isinstance(selector, Mapping):
        raise ValueError("run spec lacks selector authority")
    return {
        "schema": BRANCH_AUTHORITY_SCHEMA,
        "role": "primary",
        "method": "sha256_prefix_born_v1",
        "branch_sha256": canonical_json_sha256(branch),
        "selector": dict(selector),
    }


def alternate_branch_authority(
    branch: Mapping[str, Any],
    *,
    parent_summary_raw: bytes,
    parent_summary: Mapping[str, Any],
    flip_column: int,
) -> dict[str, Any]:
    parent_branch = parent_summary.get("branch")
    if not isinstance(parent_branch, Mapping):
        raise ValueError("parent summary lacks neutral branch")
    if (
        isinstance(flip_column, bool)
        or not isinstance(flip_column, int)
        or flip_column < 0
    ):
        raise ValueError("alternate flip column is invalid")
    expected_branch_id = (
        f"xzzx-v2-alternate-from-{parent_branch.get('branch_id')}"
    )
    if branch.get("branch_id") != expected_branch_id:
        raise ValueError("alternate branch id does not bind its primary parent")
    return {
        "schema": BRANCH_AUTHORITY_SCHEMA,
        "role": "alternate",
        "method": (
            "first_mr_opposite_probability_at_least_1e-8_then_"
            "greedy_tie_zero"
        ),
        "branch_sha256": canonical_json_sha256(branch),
        "parent": {
            "summary_schema": RESULT_SCHEMA,
            "summary_file_sha256": hashlib.sha256(
                parent_summary_raw
            ).hexdigest(),
            "branch_sha256": canonical_json_sha256(parent_branch),
            "branch_id": parent_branch.get("branch_id"),
        },
        "flip_column": flip_column,
    }


def preflight_output_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    resolved: list[Path] = []
    for path_like in paths:
        path = Path(path_like)
        try:
            parent = path.parent.resolve(strict=True)
        except FileNotFoundError as error:
            raise FileNotFoundError(
                f"output parent directory does not exist: {path.parent}"
            ) from error
        if not parent.is_dir():
            raise NotADirectoryError(f"output parent is not a directory: {parent}")
        resolved.append(parent / path.name)
    if len(set(resolved)) != len(resolved):
        raise ValueError("output paths must be pairwise distinct")
    existing = [str(path) for path in resolved if os.path.lexists(path)]
    if existing:
        raise FileExistsError(f"refusing to replace existing outputs: {existing}")
    return tuple(resolved)


def _publish_temporary_exclusive(temporary: Path, destination: Path) -> None:
    try:
        os.link(temporary, destination)
    except FileExistsError as error:
        raise FileExistsError(
            f"refusing to replace existing output: {destination}"
        ) from error
    directory_descriptor = os.open(destination.parent, os.O_RDONLY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)


def _atomic_write(path: Path, payload: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        _publish_temporary_exclusive(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_save_npy(path: Path, state: np.ndarray) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            np.save(stream, state, allow_pickle=False)
            stream.flush()
            os.fsync(stream.fileno())
        _publish_temporary_exclusive(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _validate_branch_authority(
    authority: Mapping[str, Any],
    *,
    branch: Mapping[str, Any],
    run_spec: Mapping[str, Any],
) -> None:
    common = {"schema", "role", "method", "branch_sha256"}
    role = authority.get("role")
    expected = common | ({"selector"} if role == "primary" else {"parent", "flip_column"})
    if (
        set(authority) != expected
        or authority.get("schema") != BRANCH_AUTHORITY_SCHEMA
        or authority.get("branch_sha256") != canonical_json_sha256(branch)
    ):
        raise ValueError("branch authority field set/hash mismatch")
    if role == "primary":
        if (
            authority.get("method") != "sha256_prefix_born_v1"
            or authority.get("selector")
            != run_spec["reference_branch"]["selector"]
        ):
            raise ValueError("primary branch authority mismatch")
    elif role == "alternate":
        if (
            authority.get("method")
            != "first_mr_opposite_probability_at_least_1e-8_then_greedy_tie_zero"
            or not isinstance(authority.get("parent"), Mapping)
            or isinstance(authority.get("flip_column"), bool)
            or not isinstance(authority.get("flip_column"), int)
        ):
            raise ValueError("alternate branch authority mismatch")
    else:
        raise ValueError("branch authority role is unsupported")


def validate_parent_primary_summary(
    parent: Mapping[str, Any],
    *,
    fixture: Mapping[str, Any],
    run_spec: Mapping[str, Any],
) -> list[int]:
    fixture_sha256 = validate_fixture(fixture)
    run_spec_sha256 = validate_run_spec(run_spec, fixture)
    if (
        set(parent) != REFERENCE_SUMMARY_FIELDS
        or parent.get("schema") != RESULT_SCHEMA
        or parent.get("status") != "completed"
        or parent.get("method") != "numpy_exact_data_projector"
        or parent.get("checkpoint") != PRETERMINAL_CHECKPOINT
        or parent.get("candidate_payload_consumed") is not False
        or parent.get("external_circuit_runtime_imported") is not False
        or parent.get("forbidden_substitute_used") is not False
    ):
        raise ValueError("parent is not an exact-data completed summary")
    parent_fixture = parent.get("fixture")
    parent_spec = parent.get("run_spec")
    if (
        not isinstance(parent_fixture, Mapping)
        or set(parent_fixture)
        != {
            "schema",
            "canonical_sha256",
            "stim_circuit_sha256",
            "distance",
            "rounds",
            "num_qubits",
            "num_measurements",
        }
        or parent_fixture.get("canonical_sha256") != fixture_sha256
        or parent_fixture.get("distance") != fixture["distance"]
        or parent_fixture.get("rounds") != 2
        or not isinstance(parent_spec, Mapping)
        or set(parent_spec) != {"schema", "canonical_sha256"}
        or parent_spec.get("schema") != RUN_SPEC_SCHEMA
        or parent_spec.get("canonical_sha256") != run_spec_sha256
    ):
        raise ValueError("parent fixture/run-spec identity mismatch")
    branch = parent.get("branch")
    authority = parent.get("branch_authority")
    if not isinstance(branch, Mapping) or not isinstance(authority, Mapping):
        raise ValueError("parent lacks branch authority")
    bits = _validate_neutral_branch(
        branch,
        fixture_sha256=fixture_sha256,
        run_spec_sha256=run_spec_sha256,
        distance=fixture["distance"],
        measurement_count=fixture["num_measurements"],
    )
    _validate_branch_authority(authority, branch=branch, run_spec=run_spec)
    if authority.get("role") != "primary":
        raise ValueError("alternate parent must be the exact primary")
    rows = parent.get("probability_rows")
    probability_fields = {
        "column",
        "qubit",
        "basis",
        "reset",
        "bit",
        "p0",
        "p1",
        "selected_probability",
    }
    if (
        not isinstance(rows, list)
        or len(rows) != fixture["num_measurements"]
        or any(
            not isinstance(row, Mapping)
            or set(row) != probability_fields
            or row.get("column") != column
            for column, row in enumerate(rows)
        )
    ):
        raise ValueError("parent probability rows are incomplete")
    record = parent.get("record")
    state = parent.get("state")
    ledger = parent.get("projector_ledger")
    if (
        not isinstance(record, Mapping)
        or set(record)
        != {
            "raw_measurements",
            "detector_bits",
            "observable_bits",
            "absolute_xor_rows",
        }
        or record.get("raw_measurements") != bits
        or record.get("absolute_xor_rows") is not True
        or not isinstance(state, Mapping)
        or set(state)
        != {
            "source_kind",
            "path",
            "file_sha256",
            "sha256",
            "dtype",
            "shape",
            "qubit_axis_order",
            "qubit_order",
            "q0_bit_significance",
            "state_scope",
            "norm_sq",
            "checkpoint",
        }
        or state.get("source_kind")
        != "complete_complex128_state_vector"
        or not isinstance(ledger, Mapping)
        or set(ledger)
        != {
            "schema",
            "distance",
            "rounds",
            "data_order",
            "canonical_sha256",
        }
    ):
        raise ValueError("parent contains non-exact record/state/ledger fields")
    ledger_payload = {
        key: ledger[key] for key in ledger if key != "canonical_sha256"
    }
    if ledger.get("canonical_sha256") != canonical_json_sha256(ledger_payload):
        raise ValueError("parent projector-ledger hash mismatch")
    return bits


def write_reference_artifacts(
    *,
    fixture: Mapping[str, Any],
    run_spec: Mapping[str, Any],
    execution: Mapping[str, Any],
    branch_authority: Mapping[str, Any],
    input_provenance: Mapping[str, Any],
    resource_usage: Mapping[str, Any],
    summary_path: Path,
    state_path: Path,
    started_at: float | None = None,
) -> dict[str, Any]:
    summary_path, state_path = preflight_output_paths((summary_path, state_path))
    fixture_sha256 = validate_fixture(fixture)
    run_spec_sha256 = validate_run_spec(run_spec, fixture)
    branch = neutral_branch(fixture, run_spec, execution)
    _validate_neutral_branch(
        branch,
        fixture_sha256=fixture_sha256,
        run_spec_sha256=run_spec_sha256,
        distance=fixture["distance"],
        measurement_count=fixture["num_measurements"],
    )
    _validate_branch_authority(
        branch_authority,
        branch=branch,
        run_spec=run_spec,
    )
    data_state = np.asarray(execution.get("preterminal_data_state"))
    data_order = list(fixture["frame"]["data_qubits"])
    _validated_state(data_state, data_order=data_order)
    if fixture["distance"] == 3:
        state = embed_data_state(
            data_state,
            data_order=data_order,
            num_qubits=fixture["num_qubits"],
        )
        axis_order = list(range(fixture["num_qubits"]))
        state_scope = "all_active_qubits"
    elif fixture["distance"] == 5:
        state = np.array(data_state, copy=True)
        axis_order = data_order
        state_scope = "sorted_data_qubits_after_reset_projection"
    else:
        raise ValueError("formal selected-branch artifacts require d3 or d5")
    norm_sq = float(np.vdot(state, state).real)
    if not math.isfinite(norm_sq) or abs(norm_sq - 1.0) > 1e-12:
        raise ValueError("preterminal checkpoint vector is not normalized")
    _atomic_save_npy(state_path, np.ascontiguousarray(state))
    state_sha256 = _file_sha256(state_path)
    observed_resource_usage = (
        _resource_usage(started_at)
        if started_at is not None
        else dict(resource_usage)
    )
    ledger = execution.get("projector_ledger")
    if not isinstance(ledger, Mapping):
        raise ValueError("execution lacks projector ledger")
    summary = {
        "schema": RESULT_SCHEMA,
        "status": "completed",
        "method": "numpy_exact_data_projector",
        "claim_boundary": (
            "bounded all-qubit selected trajectory; no leakage, Kraus, "
            "decoded-LER, full d3/d5 law, or scalability claim"
        ),
        "fixture": {
            "schema": fixture["schema"],
            "canonical_sha256": fixture_sha256,
            "stim_circuit_sha256": fixture["stim_circuit_sha256"],
            "distance": fixture["distance"],
            "rounds": 2,
            "num_qubits": fixture["num_qubits"],
            "num_measurements": fixture["num_measurements"],
        },
        "run_spec": {
            "schema": run_spec["schema"],
            "canonical_sha256": run_spec_sha256,
        },
        "checkpoint": PRETERMINAL_CHECKPOINT,
        "branch": branch,
        "branch_authority": dict(branch_authority),
        "projector_ledger": dict(ledger),
        "probability_rows": list(execution["probability_rows"]),
        "branch_mass": execution["branch_mass"],
        "log_branch_mass": execution["log_branch_mass"],
        "branch_mass_representable": execution["branch_mass_representable"],
        "positive_mass_underflowed_to_zero": execution[
            "positive_mass_underflowed_to_zero"
        ],
        "record": {
            "raw_measurements": list(execution["raw_bits"]),
            "detector_bits": list(execution["detector_bits"]),
            "observable_bits": list(execution["observable_bits"]),
            "absolute_xor_rows": True,
        },
        "state": {
            "source_kind": "complete_complex128_state_vector",
            "path": str(state_path),
            "file_sha256": state_sha256,
            "sha256": state_sha256,
            "dtype": "complex128",
            "shape": [state.size],
            "qubit_axis_order": axis_order,
            "qubit_order": axis_order,
            "q0_bit_significance": "most_significant",
            "state_scope": state_scope,
            "norm_sq": norm_sq,
            "checkpoint": PRETERMINAL_CHECKPOINT,
        },
        "reference_state_contract": {
            "probability_floor": None,
            "truncation": None,
            "normalization_square_root": "positive_real",
            "post_hoc_phase_canonicalization": None,
        },
        "input_provenance": dict(input_provenance),
        "resource_usage": observed_resource_usage,
        "candidate_payload_consumed": False,
        "external_circuit_runtime_imported": False,
        "forbidden_substitute_used": False,
    }
    _atomic_write(summary_path, canonical_json_bytes(summary))
    return summary


def _read_json_with_raw(path: Path) -> tuple[dict[str, Any], bytes]:
    resolved = path.resolve(strict=True)
    if not resolved.is_file():
        raise ValueError(f"input is not a regular file: {resolved}")
    raw = resolved.read_bytes()

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    payload = json.loads(raw, object_pairs_hook=reject_duplicates)
    if not isinstance(payload, dict):
        raise ValueError("JSON root must be an object")
    return payload, raw


def formal_input_provenance(
    *,
    fixture_path: Path,
    run_spec_path: Path,
    parent_summary_path: Path | None,
    raw_input_bytes: Mapping[str, bytes] | None = None,
) -> dict[str, Any]:
    if os.environ.get("PYTHONPATH"):
        raise RuntimeError("formal exact-data worker rejects PYTHONPATH")
    try:
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
        status = subprocess.run(
            [
                "git",
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
                "--ignored=matching",
                "--",
                *FORMAL_INPUT_PATHS,
            ],
            cwd=REPO,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError("cannot bind exact-data worker to Git inputs") from error
    if len(head) != 40 or any(character not in "0123456789abcdef" for character in head):
        raise RuntimeError("Git HEAD is not a full lowercase commit")
    if shallow != "false":
        raise RuntimeError("formal exact-data worker requires a non-shallow clone")
    if status.strip():
        raise RuntimeError(
            "formal exact-data worker requires committed byte-clean inputs: "
            + status.strip().replace("\n", "; ")
        )
    files: dict[str, str] = {}
    for relative in FORMAL_INPUT_PATHS:
        working = (REPO / relative).read_bytes()
        try:
            committed = subprocess.run(
                ["git", "show", f"{head}:{relative}"],
                cwd=REPO,
                check=True,
                capture_output=True,
            ).stdout
        except (OSError, subprocess.CalledProcessError) as error:
            raise RuntimeError("formal source is absent from committed HEAD") from error
        if working != committed:
            raise RuntimeError(f"formal input differs from committed HEAD: {relative}")
        files[relative] = hashlib.sha256(working).hexdigest()

    conda_prefix_raw = os.environ.get("CONDA_PREFIX")
    if not conda_prefix_raw:
        raise RuntimeError("formal exact-data worker requires CONDA_PREFIX")
    conda_prefix = Path(conda_prefix_raw).resolve(strict=True)
    executable = Path(sys.executable).resolve(strict=True)
    python_prefix = Path(sys.prefix).resolve(strict=True)
    try:
        executable.relative_to(conda_prefix)
    except ValueError as error:
        raise RuntimeError("Python executable is outside CONDA_PREFIX") from error
    if python_prefix != conda_prefix:
        raise RuntimeError("sys.prefix differs from CONDA_PREFIX")
    lock_path = (REPO / "core-environment-cu130.lock").resolve(strict=True)
    lock_bytes = lock_path.read_bytes()
    expected_numpy = next(
        (
            line.split("==", 1)[1]
            for line in lock_bytes.decode("utf-8").splitlines()
            if line.startswith("numpy==")
        ),
        None,
    )
    if expected_numpy != np.__version__:
        raise RuntimeError("installed NumPy differs from core lock")
    distribution = importlib.metadata.distribution("numpy")
    metadata_text = distribution.read_text("METADATA")
    numpy_origin = Path(np.__file__).resolve(strict=True)
    if metadata_text is None:
        raise RuntimeError("installed NumPy METADATA is unavailable")

    requested = {
        "fixture": Path(fixture_path),
        "run_spec": Path(run_spec_path),
    }
    if parent_summary_path is not None:
        requested["parent_summary"] = Path(parent_summary_path)
    if raw_input_bytes is not None and set(raw_input_bytes) != set(requested):
        raise ValueError("raw input byte labels differ from declared inputs")
    input_files: dict[str, dict[str, str]] = {}
    for label, path in requested.items():
        resolved = path.resolve(strict=True)
        observed = resolved.read_bytes()
        bound = observed if raw_input_bytes is None else raw_input_bytes[label]
        if observed != bound:
            raise RuntimeError(f"formal input changed while binding: {label}")
        input_files[label] = {
            "path": str(resolved),
            "file_sha256": hashlib.sha256(bound).hexdigest(),
        }
    return {
        "git_head": head,
        "repository_root": str(REPO),
        "repository_is_shallow": False,
        "required_paths_clean": True,
        "files_sha256": files,
        "input_files": input_files,
        "external_clone_dependency": None,
        "runtime": {
            "python_executable": str(executable),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "conda_prefix": str(conda_prefix),
            "numpy": {
                "version": np.__version__,
                "import_origin": str(numpy_origin),
                "import_origin_sha256": _file_sha256(numpy_origin),
                "distribution_metadata_sha256": hashlib.sha256(
                    metadata_text.encode("utf-8")
                ).hexdigest(),
            },
            "core_environment_lock": {
                "path": str(lock_path),
                "file_sha256": hashlib.sha256(lock_bytes).hexdigest(),
                "numpy_pin_checked": True,
            },
        },
    }


def _resource_usage(started: float) -> dict[str, Any]:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "wall_seconds": time.perf_counter() - started,
        "peak_host_rss_kib": int(usage.ru_maxrss),
        "peak_device_allocation_bytes": 0,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--run-spec", type=Path, required=True)
    parser.add_argument("--mode", choices=("primary", "alternate"), required=True)
    parser.add_argument("--parent-summary", type=Path)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-state", type=Path, required=True)
    args = parser.parse_args(argv)
    if (args.mode == "alternate") != (args.parent_summary is not None):
        raise ValueError("alternate mode requires exactly one parent summary")
    summary_path, state_path = preflight_output_paths(
        (args.output_summary, args.output_state)
    )
    fixture, fixture_raw = _read_json_with_raw(args.fixture)
    run_spec, run_spec_raw = _read_json_with_raw(args.run_spec)
    parent: dict[str, Any] | None = None
    parent_raw: bytes | None = None
    if args.parent_summary is not None:
        parent, parent_raw = _read_json_with_raw(args.parent_summary)
    raw_inputs = {"fixture": fixture_raw, "run_spec": run_spec_raw}
    if parent_raw is not None:
        raw_inputs["parent_summary"] = parent_raw
    provenance = formal_input_provenance(
        fixture_path=args.fixture,
        run_spec_path=args.run_spec,
        parent_summary_path=args.parent_summary,
        raw_input_bytes=raw_inputs,
    )
    validate_run_spec(run_spec, fixture)
    started = time.perf_counter()
    if args.mode == "primary":
        execution = execute_primary_branch(fixture, run_spec)
        branch = neutral_branch(fixture, run_spec, execution)
        authority = primary_branch_authority(branch, run_spec)
    else:
        if parent is None or parent_raw is None:
            raise RuntimeError("validated parent summary is absent")
        primary_bits = validate_parent_primary_summary(
            parent,
            fixture=fixture,
            run_spec=run_spec,
        )
        parent_branch_id = parent["branch"]["branch_id"]
        execution = execute_alternate_branch(
            fixture,
            primary_bits,
            branch_id=f"xzzx-v2-alternate-from-{parent_branch_id}",
            minimum_probability=SELECTED_BRANCH_MIN_PROBABILITY,
        )
        branch = neutral_branch(fixture, run_spec, execution)
        authority = alternate_branch_authority(
            branch,
            parent_summary_raw=parent_raw,
            parent_summary=parent,
            flip_column=execution["alternate_flip_column"],
        )
    write_reference_artifacts(
        fixture=fixture,
        run_spec=run_spec,
        execution=execution,
        branch_authority=authority,
        input_provenance=provenance,
        resource_usage=_resource_usage(started),
        summary_path=summary_path,
        state_path=state_path,
        started_at=started,
    )
    print(
        f"exact XZZX data reference mode={args.mode} "
        f"distance={fixture['distance']} status=completed",
        flush=True,
    )
    return 0


def derive_projector_ledger(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Derive the signed data checks directly from the neutral operation list."""

    data_order, hadamard_frame, ancillas = _frame_sets(fixture)
    distance = fixture.get("distance")
    if (
        isinstance(distance, bool)
        or not isinstance(distance, int)
        or distance < 2
        or fixture.get("rounds") != 2
    ):
        raise ValueError("exact projector worker requires two valid rounds")
    syndrome_count = distance * distance - 1
    operations = fixture.get("operations")
    measurements = fixture.get("measurement_order")
    if not isinstance(operations, list) or not isinstance(measurements, list):
        raise ValueError("fixture operation/measurement ledger is absent")

    links: dict[int, list[tuple[str, int]]] = {
        ancilla: [] for ancilla in ancillas
    }
    measured: list[int] = []
    rounds: list[list[dict[str, Any]]] = []
    measurement_column = 0
    terminal_started = False

    for operation in operations:
        if (
            not isinstance(operation, Mapping)
            or set(operation) != {"op", "qubits"}
            or not isinstance(operation["op"], str)
            or not isinstance(operation["qubits"], list)
        ):
            raise ValueError("fixture operation row is invalid")
        name = operation["op"]
        qubits = operation["qubits"]
        if name == "CX":
            if terminal_started or len(qubits) != 2:
                raise ValueError("unexpected two-qubit gate")
            control, target = qubits
            control_is_data = control in set(data_order)
            target_is_data = target in set(data_order)
            if control_is_data == target_is_data:
                raise ValueError("every CX must join one data and one ancilla")
            if control in ancillas:
                links[control].append(("ancilla_control", target))
            else:
                links[target].append(("ancilla_target", control))
            continue
        if name == "MR":
            if terminal_started or len(qubits) != 1:
                raise ValueError("wrong MR grouping/order")
            if measurement_column >= len(measurements):
                raise ValueError("MR has no measurement column")
            row = measurements[measurement_column]
            ancilla = qubits[0]
            if (
                not isinstance(row, Mapping)
                or row.get("column") != measurement_column
                or row.get("qubit") != ancilla
                or row.get("basis") != "Z"
                or row.get("reset") is not True
                or ancilla not in ancillas
            ):
                raise ValueError("wrong MR grouping/order")
            measured.append(ancilla)
            measurement_column += 1
            if len(measured) == syndrome_count:
                if len(set(measured)) != syndrome_count:
                    raise ValueError("wrong MR grouping/order")
                checks: list[dict[str, Any]] = []
                for measured_ancilla in measured:
                    ancilla_links = links[measured_ancilla]
                    if not ancilla_links:
                        raise ValueError("measured ancilla has empty support")
                    orientations = {
                        orientation for orientation, _qubit in ancilla_links
                    }
                    if len(orientations) != 1:
                        raise ValueError("mixed CX orientation")
                    support_qubits = [qubit for _orientation, qubit in ancilla_links]
                    if len(set(support_qubits)) != len(support_qubits):
                        raise ValueError("duplicate data support")
                    base = (
                        "X"
                        if ancilla_links[0][0] == "ancilla_control"
                        else "Z"
                    )
                    support = sorted(
                        [
                            qubit,
                            (
                                ("Z" if base == "X" else "X")
                                if qubit in hadamard_frame
                                else base
                            ),
                        ]
                        for qubit in support_qubits
                    )
                    checks.append(
                        {
                            "ancilla": measured_ancilla,
                            "sign": 1,
                            "support": support,
                        }
                    )
                validate_commuting_checks(checks)
                rounds.append(checks)
                measured = []
                links = {ancilla: [] for ancilla in ancillas}
            continue
        if name in {"M", "MX"}:
            terminal_started = True
            if len(rounds) != 2 or measured or len(qubits) != 1:
                raise ValueError("wrong MR grouping/order")
            measurement_column += 1
            continue
        if name in {"R", "RX", "H"}:
            if len(qubits) != 1 or terminal_started and name != "H":
                raise ValueError("unexpected single-qubit gate")
            continue
        raise ValueError(f"unexpected fixture operation {name}")

    if (
        measured
        or len(rounds) != 2
        or rounds[0] != rounds[1]
        or measurement_column != len(measurements)
        or measurement_column != fixture.get("num_measurements")
    ):
        raise ValueError("unequal rounds or incomplete measurement ledger")
    ledger = {
        "schema": LEDGER_SCHEMA,
        "distance": distance,
        "rounds": rounds,
        "data_order": data_order,
    }
    ledger["canonical_sha256"] = canonical_json_sha256(ledger)
    return ledger


if __name__ == "__main__":
    raise SystemExit(main())
