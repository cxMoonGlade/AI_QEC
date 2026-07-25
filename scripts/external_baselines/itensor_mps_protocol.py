"""Pure neutral-JSON contract shared by the isolated ITensorMPS tools.

This module deliberately imports only the Python standard library, so ordinary
repository tests validate the external-process seam without a Julia runtime
present.  The worker on the other side of that seam is Julia and cannot import
this module; it re-validates the request against the same literal contract, so
every field here is chosen to be expressible in both languages without
ambiguity.

The leg is a structural port of the Aer MPS leg and deliberately reuses that
leg's frozen circuit fixtures, little-endian amplitude ordering, and bond
policy ladder.  Reusing one fixture family is what makes ITensorMPS a genuine
third comparator of the same object rather than an unrelated second experiment.

Provenance note: a Julia package has no ``direct_url.json`` analogue, so the
clone-to-installed binding is asserted through the resolved package tree hash,
the Manifest digest, and per-file digests of the named upstream source anchors.
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

REQUEST_SCHEMA = "error_coupling_simulator.external_itensor_mps.request.v1"
RESULT_SCHEMA = "error_coupling_simulator.external_itensor_mps.result.v1"
REPORT_SCHEMA = "error_coupling_simulator.external_itensor_mps.comparison.v1"

# The upstream clone this leg is pinned to; the orchestrator re-checks it.
EXPECTED_ITENSOR_COMMIT = "7ce812c"
BASELINE_ENVIRONMENT = "ecs-baseline-itensor"

# Amplitude ordering is a correctness hazard, not a convention detail: a leg
# that disagrees here looks green at full rank only by coincidence. Both the
# Aer leg and this one index qubit 0 as the fastest-varying bit.
AMPLITUDE_ORDERING = "little_endian_qubit0_fastest"

# The other silent-mismatch hazard: ITensor's Spectrum reports SQUARED Schmidt
# coefficients (reduced-density-matrix eigenvalues), so a maximally entangled
# bond gives [0.5, 0.5] rather than [0.707, 0.707]. A comparator that assumes
# the unsquared convention disagrees by a square and still looks plausible, so
# the result must state which convention it carries.
SCHMIDT_CONVENTION = "squared_schmidt_coefficients_reduced_density_matrix_eigenvalues"

# Upstream files whose digests bind the running package to the pristine clone.
ITENSOR_SOURCE_ANCHORS = (
    "src/mps.jl",
    "src/abstractmps.jl",
    "src/mpo.jl",
    "src/defaults.jl",
)

_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")
_TREE_HASH = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

# Gate vocabulary shared with the Aer leg: (qubit arity, parameter arity).
_GATE_ARITY = {
    "h": (1, 0),
    "x": (1, 0),
    "ry": (1, 1),
    "rz": (1, 1),
    "cx": (2, 0),
    "cz": (2, 0),
    "swap": (2, 0),
}


def canonical_json_sha256(payload: Mapping[str, Any]) -> str:
    """Digest of the canonical JSON encoding both languages agree on."""

    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def report_content_sha256(report: Mapping[str, Any]) -> str:
    """Digest of a report excluding its own self-referential digest field."""

    body = {key: value for key, value in report.items() if key != "content_sha256"}
    return canonical_json_sha256(body)


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> str:
    """Publish one JSON object atomically and return its canonical digest."""

    digest = canonical_json_sha256(payload)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)
    return digest


def read_json_object(path: Path) -> dict[str, Any]:
    """Read one JSON object, refusing any other root type."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"JSON root is not an object: {path}")
    return value


def encode_complex_vector(values: Iterable[complex]) -> list[list[float]]:
    """Encode amplitudes as [real, imag] pairs, the only form Julia and Python share."""

    return [[float(value.real), float(value.imag)] for value in values]


def decode_complex_vector(values: Sequence[object]) -> list[complex]:
    """Decode [real, imag] pairs, rejecting anything non-finite or malformed."""

    decoded: list[complex] = []
    for index, entry in enumerate(values):
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            raise ValueError(f"amplitude {index} is not a [real, imag] pair")
        real, imag = entry
        for part in (real, imag):
            if isinstance(part, bool) or not isinstance(part, (int, float)):
                raise ValueError(f"amplitude {index} has a non-numeric component")
            if not math.isfinite(float(part)):
                raise ValueError(f"amplitude {index} is not finite")
        decoded.append(complex(float(real), float(imag)))
    return decoded


def vector_norm_squared(values: Sequence[complex]) -> float:
    return float(sum((value.real * value.real) + (value.imag * value.imag) for value in values))


def state_fidelity(left: Sequence[complex], right: Sequence[complex]) -> float:
    """|<left|right>|^2 with both sides normalized; global phase is irrelevant."""

    if len(left) != len(right):
        raise ValueError("state vectors have different lengths")
    left_norm = vector_norm_squared(left)
    right_norm = vector_norm_squared(right)
    if left_norm <= 0.0 or right_norm <= 0.0:
        raise ValueError("state vectors must have positive norm")
    overlap = sum(complex(a).conjugate() * complex(b) for a, b in zip(left, right))
    magnitude_squared = (overlap.real * overlap.real) + (overlap.imag * overlap.imag)
    return float(magnitude_squared / (left_norm * right_norm))


def phase_aligned_l2(left: Sequence[complex], right: Sequence[complex]) -> float:
    """L2 distance after removing the global phase, for amplitude-level comparison."""

    if len(left) != len(right):
        raise ValueError("state vectors have different lengths")
    overlap = sum(complex(a).conjugate() * complex(b) for a, b in zip(left, right))
    magnitude = abs(overlap)
    phase = complex(1.0, 0.0) if magnitude == 0.0 else overlap / magnitude
    return float(
        math.sqrt(
            sum(abs(complex(b) - phase * complex(a)) ** 2 for a, b in zip(left, right))
        )
    )


def validate_request(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a neutral single-execution ITensorMPS request."""

    _require_exact_keys(
        payload,
        {
            "schema",
            "execution_id",
            "seed",
            "cutoff",
            "max_bond_dimension",
            "amplitude_ordering",
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
    cutoff = payload["cutoff"]
    if isinstance(cutoff, bool) or not isinstance(cutoff, (int, float)):
        raise ValueError("cutoff must be numeric")
    if not math.isfinite(float(cutoff)) or float(cutoff) < 0.0:
        raise ValueError("cutoff must be finite and nonnegative")
    cap = payload["max_bond_dimension"]
    if cap is not None and (isinstance(cap, bool) or not isinstance(cap, int) or cap <= 0):
        raise ValueError("max_bond_dimension must be null or a positive integer")
    if payload["amplitude_ordering"] != AMPLITUDE_ORDERING:
        raise ValueError(
            f"amplitude_ordering must be {AMPLITUDE_ORDERING!r}; the leg is only "
            "comparable to the Aer fixtures under that convention"
        )
    _validate_circuit(payload["circuit"])
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
        },
        "result",
    )
    if payload["schema"] != RESULT_SCHEMA:
        raise ValueError(f"unsupported result schema: {payload['schema']!r}")
    if payload["request_sha256"] != canonical_json_sha256(request):
        raise ValueError("result request hash does not match request")
    if payload["execution_id"] != request["execution_id"]:
        raise ValueError("result execution_id does not match request")
    if payload["circuit_id"] != request["circuit"]["id"]:
        raise ValueError("result circuit_id does not match request")

    _validate_runtime(payload["runtime"])
    _validate_configuration(payload["configuration"], request)
    _validate_mps(payload["mps"], request["circuit"]["qubits"])

    amplitudes = decode_complex_vector(payload["statevector"])
    expected_length = 2 ** int(request["circuit"]["qubits"])
    if len(amplitudes) != expected_length:
        raise ValueError(
            f"statevector length {len(amplitudes)} does not match "
            f"{expected_length} for {request['circuit']['qubits']} qubits"
        )
    reported_norm = payload["statevector_norm_squared"]
    if isinstance(reported_norm, bool) or not isinstance(reported_norm, (int, float)):
        raise ValueError("statevector_norm_squared must be numeric")
    if not math.isfinite(float(reported_norm)):
        raise ValueError("statevector_norm_squared must be finite")
    if abs(vector_norm_squared(amplitudes) - float(reported_norm)) > 1e-9:
        raise ValueError("statevector_norm_squared disagrees with the encoded amplitudes")


def _validate_runtime(runtime: object) -> None:
    """The Julia-side identity that binds the run to the pristine clone."""

    _require_exact_keys(
        runtime,
        {
            "julia_version",
            "active_project",
            "itensormps_version",
            "itensormps_tree_hash",
            "itensormps_source_path",
            "manifest_sha256",
            "source_anchor_sha256",
        },
        "runtime",
    )
    assert isinstance(runtime, Mapping)  # narrowed by _require_exact_keys
    for key in ("julia_version", "active_project", "itensormps_version", "itensormps_source_path"):
        value = runtime[key]
        if not isinstance(value, str) or not value:
            raise ValueError(f"runtime.{key} must be a nonempty string")
    if not isinstance(runtime["itensormps_tree_hash"], str) or _TREE_HASH.fullmatch(
        runtime["itensormps_tree_hash"]
    ) is None:
        raise ValueError("runtime.itensormps_tree_hash must be a 40-hex-character tree hash")
    if not isinstance(runtime["manifest_sha256"], str) or _SHA256.fullmatch(
        runtime["manifest_sha256"]
    ) is None:
        raise ValueError("runtime.manifest_sha256 must be a sha256 digest")
    anchors = runtime["source_anchor_sha256"]
    if not isinstance(anchors, Mapping):
        raise ValueError("runtime.source_anchor_sha256 must be an object")
    if set(anchors) != set(ITENSOR_SOURCE_ANCHORS):
        missing = sorted(set(ITENSOR_SOURCE_ANCHORS) - set(anchors))
        extra = sorted(set(anchors) - set(ITENSOR_SOURCE_ANCHORS))
        raise ValueError(f"source anchors differ: missing={missing}, extra={extra}")
    for name, digest in anchors.items():
        if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
            raise ValueError(f"source anchor {name} must carry a sha256 digest")


def _validate_configuration(configuration: object, request: Mapping[str, Any]) -> None:
    """The worker must echo the truncation controls it actually applied."""

    _require_exact_keys(
        configuration,
        {"cutoff", "max_bond_dimension", "seed", "amplitude_ordering", "orthogonalized"},
        "configuration",
    )
    assert isinstance(configuration, Mapping)
    if float(configuration["cutoff"]) != float(request["cutoff"]):
        raise ValueError("configuration.cutoff does not match the request")
    if configuration["max_bond_dimension"] != request["max_bond_dimension"]:
        raise ValueError("configuration.max_bond_dimension does not match the request")
    if configuration["seed"] != request["seed"]:
        raise ValueError("configuration.seed does not match the request")
    if configuration["amplitude_ordering"] != AMPLITUDE_ORDERING:
        raise ValueError("configuration.amplitude_ordering is not the pinned convention")
    if configuration["orthogonalized"] is not True:
        raise ValueError(
            "configuration.orthogonalized must be true; Schmidt values are only "
            "meaningful about an orthogonality centre"
        )


def _validate_mps(mps: object, qubits: int) -> None:
    """Bond dimensions and per-bond Schmidt spectra -- this leg's real payload."""

    _require_exact_keys(
        mps,
        {"bond_dimensions", "schmidt_values", "schmidt_convention", "discarded_weight"},
        "mps",
    )
    assert isinstance(mps, Mapping)
    if mps["schmidt_convention"] != SCHMIDT_CONVENTION:
        raise ValueError(
            f"mps.schmidt_convention must be {SCHMIDT_CONVENTION!r}; a comparator "
            "that assumes the unsquared convention disagrees by a square"
        )
    bonds = mps["bond_dimensions"]
    if not isinstance(bonds, list) or len(bonds) != qubits - 1:
        raise ValueError(f"bond_dimensions must list {qubits - 1} internal bonds")
    for index, value in enumerate(bonds):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"bond dimension {index} must be a positive integer")
    spectra = mps["schmidt_values"]
    if not isinstance(spectra, list) or len(spectra) != qubits - 1:
        raise ValueError(f"schmidt_values must list {qubits - 1} internal bonds")
    for index, (spectrum, bond) in enumerate(zip(spectra, bonds)):
        if not isinstance(spectrum, list) or len(spectrum) != bond:
            raise ValueError(
                f"schmidt spectrum {index} must have exactly {bond} values, "
                "matching its retained bond dimension"
            )
        previous = math.inf
        for value in spectrum:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"schmidt spectrum {index} holds a non-numeric value")
            numeric = float(value)
            if not math.isfinite(numeric) or numeric < 0.0:
                raise ValueError(f"schmidt spectrum {index} holds a negative or non-finite value")
            if numeric > previous:
                raise ValueError(f"schmidt spectrum {index} is not in non-increasing order")
            previous = numeric
    discarded = mps["discarded_weight"]
    if not isinstance(discarded, list) or len(discarded) != qubits - 1:
        raise ValueError(f"discarded_weight must list {qubits - 1} internal bonds")
    for index, value in enumerate(discarded):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"discarded weight {index} must be numeric")
        numeric = float(value)
        if not math.isfinite(numeric) or numeric < 0.0:
            raise ValueError(f"discarded weight {index} must be finite and nonnegative")


def _validate_circuit(circuit: object) -> None:
    """The frozen neutral circuit description shared with the Aer leg."""

    _require_exact_keys(circuit, {"id", "qubits", "operations"}, "circuit")
    assert isinstance(circuit, Mapping)
    _validate_identifier(circuit["id"], "circuit.id")
    qubits = circuit["qubits"]
    if isinstance(qubits, bool) or not isinstance(qubits, int) or not 1 <= qubits <= 24:
        raise ValueError("circuit.qubits must be an integer in [1, 24]")
    operations = circuit["operations"]
    if not isinstance(operations, list) or not operations:
        raise ValueError("circuit.operations must be a nonempty list")
    for index, operation in enumerate(operations):
        _require_exact_keys(operation, {"gate", "targets", "parameters"}, f"operation {index}")
        assert isinstance(operation, Mapping)
        gate = operation["gate"]
        if gate not in _GATE_ARITY:
            raise ValueError(f"operation {index} uses an unsupported gate: {gate!r}")
        target_arity, parameter_arity = _GATE_ARITY[gate]
        targets = operation["targets"]
        if not isinstance(targets, list) or len(targets) != target_arity:
            raise ValueError(f"operation {index} must name exactly {target_arity} targets")
        for target in targets:
            if isinstance(target, bool) or not isinstance(target, int):
                raise ValueError(f"operation {index} has a non-integer target")
            if not 0 <= target < qubits:
                raise ValueError(f"operation {index} targets a qubit outside the register")
        if len(set(targets)) != len(targets):
            raise ValueError(f"operation {index} repeats a target")
        parameters = operation["parameters"]
        if not isinstance(parameters, list) or len(parameters) != parameter_arity:
            raise ValueError(f"operation {index} must carry exactly {parameter_arity} parameters")
        for parameter in parameters:
            if isinstance(parameter, bool) or not isinstance(parameter, (int, float)):
                raise ValueError(f"operation {index} has a non-numeric parameter")
            if not math.isfinite(float(parameter)):
                raise ValueError(f"operation {index} has a non-finite parameter")


def _validate_identifier(value: object, label: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"{label} must match {_IDENTIFIER.pattern}")


def _require_exact_keys(value: object, expected: set[str], label: str) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"{label} keys differ: missing={missing}, extra={extra}")
