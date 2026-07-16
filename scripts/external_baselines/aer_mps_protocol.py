"""Pure neutral-JSON contract shared by the isolated Aer MPS tools.

This module deliberately imports only the Python standard library.  Ordinary
repository tests can therefore validate the external-process seam without
loading Qiskit Aer into the ECS process.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Iterable, Mapping, Sequence


REQUEST_SCHEMA = "error_coupling_simulator.external_aer_mps.request.v1"
RESULT_SCHEMA = "error_coupling_simulator.external_aer_mps.result.v1"
REPORT_SCHEMA = "error_coupling_simulator.external_aer_mps.comparison.v1"

_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")
_FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
_DISCARDED_VALUE = re.compile(rf"discarded_value=({_FLOAT})(?=,)")
_BOND_DIMENSIONS = re.compile(r"BD=\[([^\]]*)\](?=,)")

_GATE_ARITY = {
    "h": (1, 0),
    "x": (1, 0),
    "ry": (1, 1),
    "rz": (1, 1),
    "cx": (2, 0),
    "cz": (2, 0),
    "swap": (2, 0),
}

_AER_APPLY_MEASURE_METADATA_VALUE = 0


def canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    """Return the hash of a strict, canonical JSON encoding."""

    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def report_content_sha256(report: Mapping[str, Any]) -> str:
    """Hash report content while excluding its self-referential hash field."""

    payload = dict(report)
    payload.pop("content_sha256", None)
    return canonical_json_sha256(payload)


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> str:
    """Atomically write deterministic JSON and return its exact-byte hash."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(encoded).hexdigest()


def read_json_object(path: Path) -> dict[str, Any]:
    """Read one JSON object, rejecting arrays and non-object roots."""

    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON root must be an object")
    return value


def encode_complex_vector(values: Iterable[complex]) -> list[list[float]]:
    """Encode a complex vector without numerical chopping."""

    return [[float(complex(value).real), float(complex(value).imag)] for value in values]


def decode_complex_vector(values: Sequence[object]) -> list[complex]:
    """Decode and validate the neutral ``[real, imag]`` representation."""

    decoded: list[complex] = []
    for index, pair in enumerate(values):
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError(f"complex vector entry {index} must be [real, imag]")
        real, imag = pair
        if isinstance(real, bool) or not isinstance(real, (int, float)):
            raise ValueError(f"complex vector real entry {index} is not numeric")
        if isinstance(imag, bool) or not isinstance(imag, (int, float)):
            raise ValueError(f"complex vector imaginary entry {index} is not numeric")
        if not math.isfinite(float(real)) or not math.isfinite(float(imag)):
            raise ValueError(f"complex vector entry {index} is not finite")
        decoded.append(complex(float(real), float(imag)))
    return decoded


def vector_norm_squared(values: Sequence[complex]) -> float:
    return float(sum(abs(value) ** 2 for value in values))


def state_fidelity(left: Sequence[complex], right: Sequence[complex]) -> float:
    """Return pure-state fidelity, insensitive to normalization and phase."""

    if len(left) != len(right) or not left:
        raise ValueError("state vectors must have the same nonzero length")
    left_norm = vector_norm_squared(left)
    right_norm = vector_norm_squared(right)
    if left_norm <= 0.0 or right_norm <= 0.0:
        raise ValueError("state vectors must have nonzero norm")
    overlap = sum(a.conjugate() * b for a, b in zip(left, right, strict=True))
    fidelity = abs(overlap) ** 2 / (left_norm * right_norm)
    # Roundoff alone may place a normalized overlap a few ulps outside [0, 1].
    return float(min(1.0, max(0.0, fidelity)))


def phase_aligned_l2(left: Sequence[complex], right: Sequence[complex]) -> float:
    """Return ``||left - phase * right||_2`` after optimal phase alignment."""

    if len(left) != len(right) or not left:
        raise ValueError("state vectors must have the same nonzero length")
    overlap = sum(a.conjugate() * b for a, b in zip(left, right, strict=True))
    phase = overlap.conjugate() / abs(overlap) if overlap else 1.0 + 0.0j
    return float(
        math.sqrt(
            sum(abs(a - phase * b) ** 2 for a, b in zip(left, right, strict=True))
        )
    )


def parse_mps_log(raw_log: str) -> dict[str, Any]:
    """Extract Aer-reported discard weights and per-instruction bond dimensions."""

    if not isinstance(raw_log, str):
        raise ValueError("MPS_log_data must be a string")
    stripped_log = raw_log.strip()
    if not stripped_log.startswith("{") or not stripped_log.endswith("}"):
        raise ValueError("MPS_log_data must retain Aer's outer braces")
    discarded_matches = _DISCARDED_VALUE.findall(raw_log)
    if raw_log.count("discarded_value") != len(discarded_matches):
        raise ValueError("MPS log contains an unrecognized discarded_value format")
    discarded_values = [float(match) for match in discarded_matches]
    bond_matches = _BOND_DIMENSIONS.findall(raw_log)
    if raw_log.count("BD") != len(bond_matches):
        raise ValueError("MPS log contains an unrecognized bond-dimension format")
    logged_bond_dimensions: list[list[int]] = []
    for body in bond_matches:
        stripped = body.strip()
        try:
            dimensions = [] if not stripped else [int(token) for token in stripped.split()]
        except ValueError as error:
            raise ValueError("MPS log contains a noninteger bond dimension") from error
        if any(dimension <= 0 for dimension in dimensions):
            raise ValueError("MPS log contains a nonpositive bond dimension")
        logged_bond_dimensions.append(dimensions)
    if any(value <= 0.0 or not math.isfinite(value) for value in discarded_values):
        raise ValueError("MPS log contains an invalid discarded value")
    return {
        "raw": raw_log,
        "discarded_values": discarded_values,
        "discarded_value_count": len(discarded_values),
        "discarded_value_sum": float(sum(discarded_values)),
        "discarded_value_max": float(max(discarded_values, default=0.0)),
        "logged_bond_dimensions": logged_bond_dimensions,
    }


def validate_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a neutral single-execution Aer request."""

    _require_exact_keys(
        payload,
        {
            "schema",
            "execution_id",
            "seed",
            "truncation_threshold",
            "max_bond_dimension",
            "circuit",
        },
        "request",
    )
    if payload["schema"] != REQUEST_SCHEMA:
        raise ValueError(f"unsupported request schema: {payload['schema']!r}")
    _validate_identifier(payload["execution_id"], "execution_id")
    seed = payload["seed"]
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    threshold = payload["truncation_threshold"]
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise ValueError("truncation_threshold must be numeric")
    if not math.isfinite(float(threshold)) or float(threshold) < 0.0:
        raise ValueError("truncation_threshold must be finite and nonnegative")
    cap = payload["max_bond_dimension"]
    if cap is not None and (
        isinstance(cap, bool) or not isinstance(cap, int) or cap <= 0
    ):
        raise ValueError("max_bond_dimension must be null or a positive integer")
    _validate_circuit(payload["circuit"])
    # JSON round-trip strips Mapping subclasses and gives the caller an owned tree.
    return json.loads(json.dumps(payload, allow_nan=False))


def validate_result(payload: Mapping[str, Any], request: Mapping[str, Any]) -> None:
    """Validate the result fields consumed by the repo-owned orchestrator."""

    _require_exact_keys(
        payload,
        {
            "schema",
            "request_sha256",
            "execution_id",
            "circuit_id",
            "runtime",
            "configuration",
            "statevector",
            "statevector_norm_squared",
            "mps",
            "mps_log",
            "simulator_metadata",
        },
        "result",
    )
    if payload["schema"] != RESULT_SCHEMA:
        raise ValueError(f"unsupported result schema: {payload['schema']!r}")
    if payload["request_sha256"] != canonical_json_sha256(request):
        raise ValueError("result request hash does not match request")
    if payload["execution_id"] != request["execution_id"]:
        raise ValueError("result execution_id does not match request")
    circuit = request["circuit"]
    if payload["circuit_id"] != circuit["id"]:
        raise ValueError("result circuit_id does not match request")
    _require_exact_keys(
        payload["configuration"],
        {
            "method",
            "device",
            "seed_simulator",
            "truncation_threshold",
            "max_bond_dimension",
            "mps_log_data",
            "mps_swap_direction",
            "mps_lapack",
            "sample_measure_algorithm",
            "chop_threshold",
            "shots",
        },
        "result.configuration",
    )
    configuration = payload["configuration"]
    expected_configuration = {
        "method": "matrix_product_state",
        "device": "CPU",
        "seed_simulator": request["seed"],
        "truncation_threshold": request["truncation_threshold"],
        "max_bond_dimension": request["max_bond_dimension"],
        "mps_log_data": True,
        "mps_swap_direction": "mps_swap_left",
        "mps_lapack": False,
        "sample_measure_algorithm": "mps_apply_measure",
        "chop_threshold": 0.0,
        "shots": 1,
    }
    if configuration != expected_configuration:
        raise ValueError(
            "result static configuration differs from the frozen comparison protocol"
        )

    state = decode_complex_vector(payload["statevector"])
    expected_size = 1 << circuit["num_qubits"]
    if len(state) != expected_size:
        raise ValueError(
            f"statevector length {len(state)} does not match {expected_size} amplitudes"
        )
    reported_norm = payload["statevector_norm_squared"]
    if isinstance(reported_norm, bool) or not isinstance(reported_norm, (int, float)):
        raise ValueError("statevector_norm_squared must be numeric")
    if not math.isclose(
        float(reported_norm),
        vector_norm_squared(state),
        rel_tol=0.0,
        abs_tol=1.0e-13,
    ):
        raise ValueError("reported statevector norm does not match amplitudes")

    mps = payload["mps"]
    _require_exact_keys(
        mps,
        {
            "num_sites",
            "site_tensor_shapes",
            "bond_dimensions",
            "schmidt_values",
        },
        "result.mps",
    )
    num_qubits = circuit["num_qubits"]
    if mps["num_sites"] != num_qubits:
        raise ValueError("saved MPS site count does not match circuit width")
    if len(mps["site_tensor_shapes"]) != num_qubits:
        raise ValueError("saved MPS tensor-shape count does not match circuit width")
    bond_dimensions = mps["bond_dimensions"]
    if len(bond_dimensions) != num_qubits - 1:
        raise ValueError("saved MPS bond count does not match circuit width")
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in bond_dimensions):
        raise ValueError("saved MPS bond dimensions must be positive integers")
    if [len(values) for values in mps["schmidt_values"]] != bond_dimensions:
        raise ValueError("saved Schmidt-vector lengths do not match bond dimensions")
    for values in mps["schmidt_values"]:
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for value in values
        ):
            raise ValueError("saved Schmidt values must be finite numbers")
    cap = request["max_bond_dimension"]
    if cap is not None and max(bond_dimensions, default=1) > cap:
        raise ValueError("saved MPS exceeds requested maximum bond dimension")

    log = payload["mps_log"]
    if not isinstance(log, dict) or parse_mps_log(log.get("raw", "")) != log:
        raise ValueError("parsed MPS log fields are inconsistent with raw log")
    two_qubit_gate_count = sum(
        len(gate["qubits"]) == 2 for gate in circuit["gates"]
    )
    logged_bonds = log["logged_bond_dimensions"]
    if len(logged_bonds) < two_qubit_gate_count:
        raise ValueError(
            "MPS log is missing per-gate bond-dimension evidence; absence of "
            "discarded_value cannot be interpreted as no positive discard"
        )
    if any(len(dimensions) != num_qubits - 1 for dimensions in logged_bonds):
        raise ValueError("MPS log bond-dimension width does not match circuit width")
    if not isinstance(payload["runtime"], dict):
        raise ValueError("runtime must be an object")
    metadata = payload["simulator_metadata"]
    _require_exact_keys(
        metadata,
        {
            "method",
            "device",
            "matrix_product_state_truncation_threshold",
            "matrix_product_state_max_bond_dimension",
            "matrix_product_state_sample_measure_algorithm",
            "matrix_product_state_lapack",
        },
        "result.simulator_metadata",
    )
    if metadata["method"] != configuration["method"]:
        raise ValueError("Aer metadata does not prove the requested MPS method")
    if metadata["device"] != configuration["device"]:
        raise ValueError("Aer metadata does not prove the requested CPU device")
    if (
        metadata["matrix_product_state_truncation_threshold"]
        != configuration["truncation_threshold"]
    ):
        raise ValueError("Aer metadata truncation threshold differs from the request")
    actual_max_bond = metadata["matrix_product_state_max_bond_dimension"]
    requested_max_bond = configuration["max_bond_dimension"]
    if isinstance(actual_max_bond, bool) or not isinstance(actual_max_bond, int):
        raise ValueError("Aer metadata maximum bond dimension must be an integer")
    if requested_max_bond is None:
        required_full_rank = 1 << (num_qubits // 2)
        if actual_max_bond < required_full_rank:
            raise ValueError("Aer metadata maximum bond cannot represent full rank")
    elif actual_max_bond != requested_max_bond:
        raise ValueError("Aer metadata maximum bond differs from the requested cap")
    if metadata["matrix_product_state_sample_measure_algorithm"] != (
        _AER_APPLY_MEASURE_METADATA_VALUE
    ):
        raise ValueError(
            "Aer metadata sample algorithm enum differs from APPLY_MEASURE=0"
        )
    if metadata["matrix_product_state_lapack"] is not configuration["mps_lapack"]:
        raise ValueError("Aer metadata LAPACK setting differs from the frozen protocol")


def _validate_circuit(circuit: object) -> None:
    if not isinstance(circuit, Mapping):
        raise ValueError("circuit must be an object")
    _require_exact_keys(
        circuit,
        {"id", "num_qubits", "tags", "falsifier_of", "gates"},
        "circuit",
    )
    _validate_identifier(circuit["id"], "circuit.id")
    num_qubits = circuit["num_qubits"]
    if isinstance(num_qubits, bool) or not isinstance(num_qubits, int):
        raise ValueError("circuit.num_qubits must be an integer")
    if not 4 <= num_qubits <= 6:
        raise ValueError("comparison circuits must contain 4 through 6 qubits")
    tags = circuit["tags"]
    if not isinstance(tags, list) or not tags:
        raise ValueError("circuit.tags must be a nonempty list")
    for tag in tags:
        _validate_identifier(tag, "circuit tag")
    falsifier_of = circuit["falsifier_of"]
    if falsifier_of is not None:
        _validate_identifier(falsifier_of, "circuit.falsifier_of")
    gates = circuit["gates"]
    if not isinstance(gates, list) or not gates:
        raise ValueError("circuit.gates must be a nonempty list")
    for gate_index, gate in enumerate(gates):
        if not isinstance(gate, Mapping):
            raise ValueError(f"circuit gate {gate_index} must be an object")
        _require_exact_keys(gate, {"name", "qubits", "parameters"}, f"gate {gate_index}")
        name = gate["name"]
        if name not in _GATE_ARITY:
            raise ValueError(f"unsupported gate {name!r}")
        qubit_arity, parameter_arity = _GATE_ARITY[name]
        qubits = gate["qubits"]
        parameters = gate["parameters"]
        if not isinstance(qubits, list) or len(qubits) != qubit_arity:
            raise ValueError(f"gate {gate_index} has invalid qubit arity")
        if len(set(qubits)) != len(qubits):
            raise ValueError(f"gate {gate_index} repeats a qubit")
        if any(
            isinstance(qubit, bool)
            or not isinstance(qubit, int)
            or not 0 <= qubit < num_qubits
            for qubit in qubits
        ):
            raise ValueError(f"gate {gate_index} has an out-of-range qubit")
        if not isinstance(parameters, list) or len(parameters) != parameter_arity:
            raise ValueError(f"gate {gate_index} has invalid parameter arity")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for value in parameters
        ):
            raise ValueError(f"gate {gate_index} has an invalid parameter")


def _validate_identifier(value: object, label: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"{label} must match {_IDENTIFIER.pattern}")


def _require_exact_keys(
    value: object,
    expected: set[str],
    label: str,
) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"{label} keys differ: missing={missing}, extra={extra}")
