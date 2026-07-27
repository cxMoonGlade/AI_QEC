#!/usr/bin/env python3
"""Independent NumPy truth for the bounded XZZX measurement/Record bridge.

The worker consumes a neutral, hash-bound fixture and, for formal d3 branch
replay, the full exact-data reference summary.  It authenticates that summary
and rebuilds a bits-only neutral branch before invoking the forced executor.
It implements complete complex128 state-vector gates and the selective
measurement/reset instrument directly.  It deliberately has no tensor-network
or external circuit-runtime dependency.

Supported truth objects are the exact d=2 ten-bit law and selected d=3
branches.  A d=5 complete dense simulation is intentionally out of scope.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from typing import Any, Callable, Mapping, Sequence

import numpy as np


FIXTURE_SCHEMA = "error_coupling_simulator.external_xzzx_record_peps.fixture.v1"
ENUMERATION_SPEC_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_peps.enumeration_spec.v1"
)
RUN_SPEC_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_peps.run_spec.v2"
)
BRANCH_SCHEMA = "error_coupling_simulator.external_xzzx_record_peps.branch.v1"
RESULT_SCHEMA = "error_coupling_simulator.external_xzzx_record_dense_reference.v1"
EXACT_REFERENCE_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_exact_data_reference.v1"
)
BRANCH_AUTHORITY_SCHEMA = (
    "error_coupling_simulator.external_xzzx_record_exact_data_reference."
    "branch_authority.v1"
)
PRIMARY_AUTHORITY_METHOD = "sha256_prefix_born_v1"
ALTERNATE_AUTHORITY_METHOD = (
    "first_mr_opposite_probability_at_least_1e-8_then_greedy_tie_zero"
)
PRETERMINAL_CHECKPOINT = (
    "after_round_1_ry_before_terminal_data_measurements"
)
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
EXPECTED_SPEC_SHA256 = {
    2: "02aef76a65383fbfec9a2f3e0b62a7dd0691a574ee739a4b6b33326ba13681ca",
    3: "7dfa0a8ef9620712e6ea190aeda651c681295f9841963ce77686640255cc22a9",
    5: "06151ea1244495475259d40bf6ca7ad16cbdaf5f8184ee61b344fb2e81b413a4",
}
DETERMINISTIC_RESET_TOLERANCE = 1e-15
FORCED_BRANCH_MIN_PROBABILITY = 1e-12
FORMAL_INPUT_PATHS = (
    "docs/METRICS.md",
    (
        "docs/simulator_validation/"
        "PEPS_XZZX_MEASUREMENT_RESET_RECORD_PREREG_V2_2026-07-27.md"
    ),
    (
        "docs/simulator_validation/"
        "PEPS_XZZX_MEASUREMENT_RESET_RECORD_PREREG_2026-07-26.md"
    ),
    "scripts/external_baselines/emit_xzzx_record_peps_fixture.py",
    "scripts/external_baselines/xzzx_record_dense_reference.py",
    "tests/test_external_xzzx_record_fixture.py",
    "tests/test_external_xzzx_record_dense_reference.py",
    "core-environment-cu130.lock",
)

H = np.asarray(
    [[1.0, 1.0], [1.0, -1.0]],
    dtype=np.complex128,
) / np.sqrt(2.0)
CX = np.asarray(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
    ],
    dtype=np.complex128,
)
CZ = np.diag(
    np.asarray([1.0, 1.0, 1.0, -1.0], dtype=np.complex128)
)


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def preflight_output_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    """Resolve outputs and reject aliasing, absent parents, and replacement."""

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
            raise NotADirectoryError(
                f"output parent is not a directory: {path.parent}"
            )
        resolved.append(parent / path.name)
    if len(set(resolved)) != len(resolved):
        raise ValueError("output paths must be pairwise distinct")
    existing = [str(path) for path in resolved if os.path.lexists(path)]
    if existing:
        raise FileExistsError(f"refusing to replace existing outputs: {existing}")
    return tuple(resolved)


def _publish_temporary_exclusive(temporary: Path, destination: Path) -> None:
    """Atomically link a complete temporary into place without replacement."""

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


def _atomic_write(path: Path, data: bytes) -> None:
    destination = preflight_output_paths((path,))[0]
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        dir=destination.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        _publish_temporary_exclusive(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_save_npy(path: Path, state: np.ndarray) -> None:
    destination = preflight_output_paths((path,))[0]
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        dir=destination.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            np.save(stream, state, allow_pickle=False)
            stream.flush()
            os.fsync(stream.fileno())
        _publish_temporary_exclusive(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def formal_input_provenance(
    *,
    fixture_path: Path,
    spec_path: Path,
    reference_summary_path: Path | None,
    raw_input_bytes: Mapping[str, bytes] | None = None,
) -> dict[str, Any]:
    """Bind formal output to exact files, runtime, and committed source bytes."""

    repository = Path(__file__).resolve().parents[2]
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        shallow = subprocess.run(
            ["git", "rev-parse", "--is-shallow-repository"],
            cwd=repository,
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
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError("cannot bind dense worker to git inputs") from error
    if len(head) != 40 or any(
        character not in "0123456789abcdef" for character in head
    ):
        raise RuntimeError("git HEAD is not a full lowercase commit identity")
    if shallow not in {"true", "false"}:
        raise RuntimeError("git did not return a valid shallow-repository state")
    if shallow == "true":
        raise RuntimeError("formal dense CLI rejects a shallow repository")
    if status.strip():
        raise RuntimeError(
            "formal dense CLI requires committed byte-clean inputs: "
            + status.strip().replace("\n", "; ")
        )

    files: dict[str, str] = {}
    try:
        for relative_path in FORMAL_INPUT_PATHS:
            working_bytes = (repository / relative_path).read_bytes()
            committed_bytes = subprocess.run(
                ["git", "show", f"{head}:{relative_path}"],
                cwd=repository,
                check=True,
                capture_output=True,
            ).stdout
            if working_bytes != committed_bytes:
                raise RuntimeError(
                    "formal dense CLI input differs from committed HEAD: "
                    f"{relative_path}"
                )
            files[relative_path] = hashlib.sha256(working_bytes).hexdigest()
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError(
            "formal dense CLI requires every source input at committed HEAD"
        ) from error

    conda_prefix_raw = os.environ.get("CONDA_PREFIX")
    if not conda_prefix_raw:
        raise RuntimeError("formal dense CLI requires an active CONDA_PREFIX")
    try:
        conda_prefix = Path(conda_prefix_raw).resolve(strict=True)
        python_prefix = Path(sys.prefix).resolve(strict=True)
        python_executable = Path(sys.executable).resolve(strict=True)
        python_executable.relative_to(conda_prefix)
    except (FileNotFoundError, ValueError) as error:
        raise RuntimeError(
            "formal dense CLI executable is outside the active conda prefix"
        ) from error
    if conda_prefix != python_prefix:
        raise RuntimeError(
            "formal dense CLI sys.prefix differs from the active conda prefix"
        )

    requested_inputs: dict[str, Path] = {
        "fixture": Path(fixture_path),
        "spec": Path(spec_path),
    }
    if reference_summary_path is not None:
        requested_inputs["reference_summary"] = Path(reference_summary_path)
    if raw_input_bytes is not None and set(raw_input_bytes) != set(requested_inputs):
        raise ValueError("raw input bytes do not match the declared input files")
    input_files: dict[str, dict[str, str]] = {}
    for label, path in requested_inputs.items():
        try:
            resolved = path.resolve(strict=True)
            observed = resolved.read_bytes()
        except OSError as error:
            raise RuntimeError(f"cannot bind dense input file {label}") from error
        if not resolved.is_file():
            raise RuntimeError(f"dense input is not a regular file: {resolved}")
        bound_bytes = observed if raw_input_bytes is None else raw_input_bytes[label]
        if observed != bound_bytes:
            raise RuntimeError(f"dense input changed while binding: {label}")
        input_files[label] = {
            "path": str(resolved),
            "file_sha256": hashlib.sha256(bound_bytes).hexdigest(),
        }

    lock_path = (repository / "core-environment-cu130.lock").resolve(strict=True)
    return {
        "git_head": head,
        "repository_root": str(repository),
        "repository_is_shallow": False,
        "files_sha256": files,
        "required_paths_clean": True,
        "input_files": input_files,
        "runtime": {
            "python_executable": str(python_executable),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "numpy_version": np.__version__,
            "conda_prefix": str(conda_prefix),
            "core_environment_lock": {
                "path": str(lock_path),
                "file_sha256": _file_sha256(lock_path),
            },
        },
    }


def validate_fixture(fixture: Mapping[str, Any]) -> str:
    if fixture.get("schema") != FIXTURE_SCHEMA:
        raise ValueError("unsupported fixture schema")
    distance = fixture.get("distance")
    if distance not in EXPECTED_FIXTURE_SHA256:
        raise ValueError("unsupported fixture distance")
    digest = canonical_json_sha256(fixture)
    if digest != EXPECTED_FIXTURE_SHA256[distance]:
        raise ValueError("fixture canonical SHA mismatch")
    if (
        fixture.get("rounds") != 2
        or fixture.get("stim_circuit_sha256") != EXPECTED_STIM_SHA256[distance]
    ):
        raise ValueError("fixture schedule or Stim identity mismatch")
    measurements = fixture.get("measurement_order")
    if not isinstance(measurements, list) or [
        row.get("column") for row in measurements
    ] != list(range(fixture.get("num_measurements", -1))):
        raise ValueError("fixture measurement columns are not contiguous")
    return digest


def validate_spec(
    spec: Mapping[str, Any],
    fixture: Mapping[str, Any],
) -> str:
    fixture_sha256 = validate_fixture(fixture)
    distance = int(fixture["distance"])
    expected_schema = (
        ENUMERATION_SPEC_SCHEMA if distance == 2 else RUN_SPEC_SCHEMA
    )
    if spec.get("schema") != expected_schema:
        raise ValueError("unsupported run/enumeration spec schema")
    digest = canonical_json_sha256(spec)
    if digest != EXPECTED_SPEC_SHA256[distance]:
        raise ValueError("run/enumeration spec canonical SHA mismatch")
    if (
        spec.get("base_fixture_sha256") != fixture_sha256
        or spec.get("stim_circuit_sha256") != fixture["stim_circuit_sha256"]
        or spec.get("distance") != distance
        or spec.get("rounds") != 2
    ):
        raise ValueError("run/enumeration spec does not bind the fixture")
    return digest


def validate_branch(
    branch: Mapping[str, Any],
    *,
    fixture_sha256: str,
    spec_sha256: str,
    fixture: Mapping[str, Any],
) -> tuple[int, ...]:
    distance = int(fixture["distance"])
    spec_key = (
        "enumeration_spec_sha256" if distance == 2 else "run_spec_sha256"
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
    if (
        branch.get("schema") != BRANCH_SCHEMA
        or branch.get("fixture_sha256") != fixture_sha256
        or branch.get(spec_key) != spec_sha256
        or branch.get("distance") != distance
        or branch.get("rounds") != 2
        or not isinstance(branch.get("branch_id"), str)
        or not branch["branch_id"]
    ):
        raise ValueError("branch identity mismatch")
    if set(branch) != required_fields:
        raise ValueError(
            "branch must contain exact bits-only fields without reference data"
        )
    outcomes = branch.get("outcomes")
    count = int(fixture["num_measurements"])
    if not isinstance(outcomes, list) or len(outcomes) != count:
        raise ValueError("branch outcome count mismatch")
    bits: list[int] = []
    for column, row in enumerate(outcomes):
        if (
            not isinstance(row, dict)
            or set(row) != {"column", "bit"}
            or row.get("column") != column
        ):
            raise ValueError("branch outcomes must have exact contiguous columns")
        bit = row["bit"]
        if isinstance(bit, bool) or not isinstance(bit, int) or bit not in (0, 1):
            raise ValueError("branch outcomes must be integer bits")
        bits.append(bit)
    return tuple(bits)


def _require_sha256(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def _neutral_branch(
    *,
    fixture_sha256: str,
    run_spec_sha256: str,
    fixture: Mapping[str, Any],
    branch_id: str,
    bits: Sequence[int],
) -> dict[str, Any]:
    return {
        "schema": BRANCH_SCHEMA,
        "fixture_sha256": fixture_sha256,
        "run_spec_sha256": run_spec_sha256,
        "branch_id": branch_id,
        "distance": int(fixture["distance"]),
        "rounds": 2,
        "outcomes": [
            {"column": column, "bit": int(bit)}
            for column, bit in enumerate(bits)
        ],
    }


def validate_exact_primary_summary(
    summary: Mapping[str, Any],
    *,
    fixture: Mapping[str, Any],
    run_spec: Mapping[str, Any],
) -> tuple[tuple[int, ...], dict[str, Any], dict[str, Any]]:
    """Authenticate a full exact-data primary and rebuild its bits-only branch."""

    fixture_sha256 = validate_fixture(fixture)
    run_spec_sha256 = validate_spec(run_spec, fixture)
    if fixture["distance"] != 3:
        raise ValueError("full-dense exact-reference replay is registered only for d3")
    if (
        summary.get("schema") != EXACT_REFERENCE_SCHEMA
        or summary.get("status") != "completed"
        or summary.get("method") != "numpy_exact_data_projector"
        or summary.get("checkpoint") != PRETERMINAL_CHECKPOINT
    ):
        raise ValueError("exact-reference root identity mismatch")
    summary_fixture = summary.get("fixture")
    summary_spec = summary.get("run_spec")
    if (
        not isinstance(summary_fixture, Mapping)
        or summary_fixture.get("schema") != FIXTURE_SCHEMA
        or summary_fixture.get("canonical_sha256") != fixture_sha256
        or summary_fixture.get("stim_circuit_sha256")
        != fixture["stim_circuit_sha256"]
        or summary_fixture.get("distance") != 3
        or summary_fixture.get("rounds") != 2
    ):
        raise ValueError("exact-reference fixture identity mismatch")
    if (
        not isinstance(summary_spec, Mapping)
        or summary_spec.get("schema") != RUN_SPEC_SCHEMA
        or summary_spec.get("canonical_sha256") != run_spec_sha256
    ):
        raise ValueError("exact-reference run-spec identity mismatch")

    source_branch = summary.get("branch")
    if not isinstance(source_branch, Mapping):
        raise ValueError("exact-reference summary lacks a neutral branch")
    bits = validate_branch(
        source_branch,
        fixture_sha256=fixture_sha256,
        spec_sha256=run_spec_sha256,
        fixture=fixture,
    )
    neutral = _neutral_branch(
        fixture_sha256=fixture_sha256,
        run_spec_sha256=run_spec_sha256,
        fixture=fixture,
        branch_id=str(source_branch["branch_id"]),
        bits=bits,
    )
    branch_sha256 = canonical_json_sha256(neutral)
    authority = summary.get("branch_authority")
    required_authority_fields = {
        "schema",
        "role",
        "method",
        "branch_sha256",
        "selector",
    }
    if (
        not isinstance(authority, Mapping)
        or set(authority) != required_authority_fields
        or authority.get("schema") != BRANCH_AUTHORITY_SCHEMA
        or authority.get("role") != "primary"
        or authority.get("method") != PRIMARY_AUTHORITY_METHOD
        or authority.get("branch_sha256") != branch_sha256
        or authority.get("selector")
        != run_spec["reference_branch"]["selector"]
    ):
        raise ValueError("exact-reference primary authority mismatch")

    probability_rows = summary.get("probability_rows")
    if (
        not isinstance(probability_rows, list)
        or len(probability_rows) != int(fixture["num_measurements"])
    ):
        raise ValueError("exact-reference probability rows are incomplete")
    for column, (row, bit) in enumerate(zip(probability_rows, bits, strict=True)):
        if (
            not isinstance(row, Mapping)
            or row.get("column") != column
            or row.get("bit") != bit
        ):
            raise ValueError("exact-reference probability rows are not aligned")
        p0 = row.get("p0")
        p1 = row.get("p1")
        selected = row.get("selected_probability")
        if (
            isinstance(p0, bool)
            or isinstance(p1, bool)
            or isinstance(selected, bool)
            or not isinstance(p0, (int, float))
            or not isinstance(p1, (int, float))
            or not isinstance(selected, (int, float))
            or not all(math.isfinite(float(value)) for value in (p0, p1, selected))
            or p0 < 0.0
            or p1 < 0.0
            or abs(float(p0 + p1) - 1.0) > 1e-12
            or float(selected) != float((p0, p1)[bit])
        ):
            raise ValueError("exact-reference probability row is invalid")
    if not isinstance(summary.get("state"), Mapping):
        raise ValueError("exact-reference summary lacks complete state metadata")
    record = summary.get("record")
    expected_detectors, expected_observables = fold_record(
        bits,
        fixture["detector_rows"],
        fixture["observable_rows"],
    )
    if (
        not isinstance(record, Mapping)
        or record.get("detector_bits") != list(expected_detectors)
        or record.get("observable_bits") != list(expected_observables)
    ):
        raise ValueError("exact-reference absolute fold mismatch")
    if not isinstance(summary.get("input_provenance"), Mapping):
        raise ValueError("exact-reference input provenance is absent")
    return bits, neutral, dict(authority)


def alternate_branch_authority(
    *,
    branch: Mapping[str, Any],
    parent_summary_file_sha256: str,
    parent_branch: Mapping[str, Any],
    flip_column: int,
) -> dict[str, Any]:
    """Build the exact frozen authority proof for a dense-derived alternate."""

    parent_branch_sha256 = canonical_json_sha256(parent_branch)
    return {
        "schema": BRANCH_AUTHORITY_SCHEMA,
        "role": "alternate",
        "method": ALTERNATE_AUTHORITY_METHOD,
        "branch_sha256": canonical_json_sha256(branch),
        "parent": {
            "summary_schema": EXACT_REFERENCE_SCHEMA,
            "summary_file_sha256": _require_sha256(
                parent_summary_file_sha256,
                label="parent summary file hash",
            ),
            "branch_sha256": parent_branch_sha256,
            "branch_id": parent_branch["branch_id"],
        },
        "flip_column": int(flip_column),
    }


def ry(angle_radians: float) -> np.ndarray:
    if not math.isfinite(angle_radians):
        raise ValueError("RY angle must be finite")
    cosine = math.cos(angle_radians / 2.0)
    sine = math.sin(angle_radians / 2.0)
    return np.asarray(
        [[cosine, -sine], [sine, cosine]],
        dtype=np.complex128,
    )


def _validated_vector(state: object) -> tuple[np.ndarray, int]:
    vector = np.asarray(state)
    if vector.dtype != np.complex128:
        raise ValueError("state must have dtype complex128")
    if vector.ndim != 1 or vector.size == 0:
        raise ValueError("state must be a nonempty flat vector")
    if vector.size & (vector.size - 1):
        raise ValueError("state length must be a power of two")
    if not np.all(np.isfinite(vector)):
        raise ValueError("state contains nonfinite amplitudes")
    return vector, vector.size.bit_length() - 1


def zero_state(num_qubits: int) -> np.ndarray:
    if isinstance(num_qubits, bool) or not isinstance(num_qubits, int):
        raise ValueError("num_qubits must be an integer")
    if not 1 <= num_qubits <= 25:
        raise ValueError("num_qubits must lie in [1, 25]")
    state = np.zeros(2**num_qubits, dtype=np.complex128)
    state[0] = 1.0
    return state


def apply_single_qubit_gate(
    state: object,
    gate: object,
    qubit: int,
) -> np.ndarray:
    vector, num_qubits = _validated_vector(state)
    matrix = np.asarray(gate)
    if matrix.dtype != np.complex128 or matrix.shape != (2, 2):
        raise ValueError("single-qubit gate must be complex128 with shape (2, 2)")
    if not 0 <= qubit < num_qubits:
        raise ValueError("single-qubit target is out of range")
    tensor = vector.reshape((2,) * num_qubits)
    moved = np.moveaxis(tensor, qubit, 0)
    evolved = np.tensordot(matrix, moved, axes=((1,), (0,)))
    return np.ascontiguousarray(
        np.moveaxis(evolved, 0, qubit).reshape(-1),
        dtype=np.complex128,
    )


def apply_two_qubit_gate(
    state: object,
    gate: object,
    first_qubit: int,
    second_qubit: int,
) -> np.ndarray:
    vector, num_qubits = _validated_vector(state)
    matrix = np.asarray(gate)
    if matrix.dtype != np.complex128 or matrix.shape != (4, 4):
        raise ValueError("two-qubit gate must be complex128 with shape (4, 4)")
    if (
        first_qubit == second_qubit
        or not 0 <= first_qubit < num_qubits
        or not 0 <= second_qubit < num_qubits
    ):
        raise ValueError("two-qubit targets must be distinct and in range")
    tensor = vector.reshape((2,) * num_qubits)
    moved = np.moveaxis(
        tensor,
        (first_qubit, second_qubit),
        (0, 1),
    )
    evolved = (matrix @ moved.reshape(4, -1)).reshape(moved.shape)
    restored = np.moveaxis(
        evolved,
        (0, 1),
        (first_qubit, second_qubit),
    )
    return np.ascontiguousarray(restored.reshape(-1), dtype=np.complex128)


def measurement_probabilities(
    state: object,
    qubit: int,
) -> tuple[float, float]:
    vector, num_qubits = _validated_vector(state)
    if not 0 <= qubit < num_qubits:
        raise ValueError("measurement target is out of range")
    moved = np.moveaxis(
        vector.reshape((2,) * num_qubits),
        qubit,
        0,
    ).reshape(2, -1)
    weights = np.sum(np.abs(moved) ** 2, axis=1, dtype=np.float64)
    total = float(weights.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("state must have positive finite norm")
    probabilities = weights / total
    p0 = float(probabilities[0])
    p1 = float(probabilities[1])
    if abs((p0 + p1) - 1.0) > 1e-12:
        raise RuntimeError("Bernoulli probabilities are not normalized")
    return p0, p1


def select_measurement(
    state: object,
    *,
    qubit: int,
    outcome: int,
    reset: bool,
) -> tuple[np.ndarray, float]:
    if isinstance(outcome, bool) or outcome not in (0, 1):
        raise ValueError("measurement outcome must be integer zero or one")
    vector, num_qubits = _validated_vector(state)
    p0, p1 = measurement_probabilities(vector, qubit)
    probability = (p0, p1)[outcome]
    if probability <= 0.0:
        raise ValueError("cannot select a zero-probability outcome")

    tensor = vector.reshape((2,) * num_qubits)
    moved = np.moveaxis(tensor, qubit, 0)
    selected = np.zeros_like(moved)
    selected[0 if reset else outcome] = moved[outcome]
    selected_norm = float(np.linalg.norm(selected))
    if not math.isfinite(selected_norm) or selected_norm <= 0.0:
        raise RuntimeError("selected branch has invalid norm")
    selected /= selected_norm
    restored = np.moveaxis(selected, 0, qubit).reshape(-1)
    return (
        np.ascontiguousarray(restored, dtype=np.complex128),
        probability,
    )


def apply_reset(state: object, *, qubit: int) -> np.ndarray:
    """Apply fixture reset where the incoming pure target is deterministic.

    A general reset channel can make the unmeasured subsystem mixed, which is
    not representable by this pure-state worker.  The frozen fixture uses
    ``R``/``RX`` only on the initial all-zero state; mid-circuit selective
    reset is represented explicitly by ``MR``.
    """

    p0, p1 = measurement_probabilities(state, qubit)
    if p1 <= DETERMINISTIC_RESET_TOLERANCE:
        reset_state, _ = select_measurement(
            state,
            qubit=qubit,
            outcome=0,
            reset=True,
        )
        return reset_state
    if p0 <= DETERMINISTIC_RESET_TOLERANCE:
        reset_state, _ = select_measurement(
            state,
            qubit=qubit,
            outcome=1,
            reset=True,
        )
        return reset_state
    raise ValueError(
        "nonselective reset of a nondeterministic or entangled target is "
        "outside this pure-state reference"
    )


def fold_record(
    raw_bits: Sequence[int],
    detector_rows: Sequence[Sequence[int]],
    observable_rows: Sequence[Sequence[int]],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    bits = tuple(raw_bits)
    if any(
        isinstance(bit, bool) or not isinstance(bit, (int, np.integer)) or bit not in (0, 1)
        for bit in bits
    ):
        raise ValueError("raw measurements must be integer bits")

    def fold(rows: Sequence[Sequence[int]]) -> tuple[int, ...]:
        output: list[int] = []
        for row in rows:
            if not row:
                raise ValueError("absolute XOR rows must be nonempty")
            value = 0
            for column in row:
                if (
                    isinstance(column, bool)
                    or not isinstance(column, (int, np.integer))
                    or not 0 <= int(column) < len(bits)
                ):
                    raise ValueError("absolute XOR column is out of range")
                value ^= int(bits[int(column)])
            output.append(value)
        return tuple(output)

    return fold(detector_rows), fold(observable_rows)


Chooser = Callable[
    [int, Mapping[str, Any], tuple[float, float]],
    int,
]


def _execute(
    fixture: Mapping[str, Any],
    chooser: Chooser,
    *,
    branch_id: str,
    intervention_angle: float,
    intervention_mode: str = "after_rounds",
    intervention_rounds: Sequence[int] = (0, 1),
    omit_first_mx_h: bool = False,
    allow_structural_zero: bool = False,
) -> dict[str, Any]:
    distance = int(fixture["distance"])
    if distance not in (2, 3):
        raise ValueError("dense execution is registered only for distance 2 or 3")
    if fixture.get("rounds") != 2:
        raise ValueError("dense execution requires exactly two rounds")
    if intervention_mode not in {"after_rounds", "after_terminal"}:
        raise ValueError("unsupported intervention placement")
    requested_intervention_rounds = tuple(intervention_rounds)
    if (
        any(
            isinstance(round_index, bool)
            or not isinstance(round_index, (int, np.integer))
            or int(round_index) not in (0, 1)
            for round_index in requested_intervention_rounds
        )
        or tuple(sorted(map(int, requested_intervention_rounds)))
        != requested_intervention_rounds
        or len(set(requested_intervention_rounds))
        != len(requested_intervention_rounds)
    ):
        raise ValueError(
            "intervention rounds must be an ordered subset of (0, 1)"
        )

    num_qubits = int(fixture["num_qubits"])
    state = zero_state(num_qubits)
    data_qubits = tuple(int(q) for q in fixture["frame"]["data_qubits"])
    syndrome_per_round = distance * distance - 1
    measurement_rows = fixture["measurement_order"]
    measurement_column = 0
    raw_bits: list[int] = []
    probability_rows: list[dict[str, Any]] = []
    selected_probabilities: list[float] = []
    post_measurement_one_weights: list[float] = []
    preterminal_state: np.ndarray | None = None
    first_mx_seen = False
    applied_intervention_rounds: list[int] = []

    for operation_index, operation in enumerate(fixture["operations"]):
        name = operation["op"]
        qubits = operation["qubits"]
        if name == "R":
            state = apply_reset(state, qubit=int(qubits[0]))
            continue
        if name == "RX":
            target = int(qubits[0])
            state = apply_reset(state, qubit=target)
            state = apply_single_qubit_gate(state, H, target)
            continue
        if name == "H":
            state = apply_single_qubit_gate(state, H, int(qubits[0]))
            continue
        if name in {"CX", "CZ"}:
            gate = CX if name == "CX" else CZ
            state = apply_two_qubit_gate(
                state,
                gate,
                int(qubits[0]),
                int(qubits[1]),
            )
            continue
        if name not in {"M", "MX", "MR"}:
            raise ValueError(
                f"unsupported operation {name!r} at index {operation_index}"
            )

        if measurement_column >= len(measurement_rows):
            raise ValueError("operation stream contains excess measurements")
        fixture_row = measurement_rows[measurement_column]
        target = int(qubits[0])
        if fixture_row.get("column") != measurement_column:
            raise ValueError("measurement columns are not contiguous")
        if fixture_row.get("qubit") != target:
            raise ValueError("measurement qubit does not match operation stream")

        basis = "X" if name == "MX" else "Z"
        if name == "MX":
            skip_h = omit_first_mx_h and not first_mx_seen
            first_mx_seen = True
            if not skip_h:
                state = apply_single_qubit_gate(state, H, target)
        probabilities = measurement_probabilities(state, target)
        outcome = chooser(
            measurement_column,
            {
                "column": measurement_column,
                "qubit": target,
                "basis": basis,
                "reset": name == "MR",
            },
            probabilities,
        )
        if isinstance(outcome, bool) or outcome not in (0, 1):
            raise ValueError("branch chooser returned a non-binary outcome")
        selected_probability = probabilities[outcome]
        if selected_probability <= 0.0:
            if allow_structural_zero:
                return {
                    "schema": RESULT_SCHEMA,
                    "branch_id": branch_id,
                    "raw_bits": tuple(raw_bits + [outcome]),
                    "conditional_probabilities": tuple(
                        selected_probabilities + [0.0]
                    ),
                    "probability_rows": tuple(
                        probability_rows
                        + [
                            {
                                "column": measurement_column,
                                "qubit": target,
                                "basis": basis,
                                "reset": name == "MR",
                                "bit": outcome,
                                "p0": probabilities[0],
                                "p1": probabilities[1],
                                "selected_probability": 0.0,
                            }
                        ]
                    ),
                    "branch_mass": 0.0,
                    "log_branch_mass": -math.inf,
                    "structural_zero_column": measurement_column,
                    "post_measurement_one_weights": tuple(
                        post_measurement_one_weights
                    ),
                    "intervention_rounds_applied": tuple(
                        applied_intervention_rounds
                    ),
                    "preterminal_state": None,
                }
            raise ValueError(
                "forced branch selected a zero-probability or below-threshold "
                f"outcome at column {measurement_column}"
            )
        if (
            not allow_structural_zero
            and selected_probability < FORCED_BRANCH_MIN_PROBABILITY
        ):
            raise ValueError(
                "forced branch selected a zero-probability or below-threshold "
                f"outcome at column {measurement_column}"
            )

        state, applied_probability = select_measurement(
            state,
            qubit=target,
            outcome=outcome,
            reset=name == "MR",
        )
        if abs(applied_probability - selected_probability) > 1e-14:
            raise RuntimeError("selective instrument probability drift")
        post_measurement_one_weights.append(
            measurement_probabilities(state, target)[1]
        )
        raw_bits.append(outcome)
        selected_probabilities.append(selected_probability)
        probability_rows.append(
            {
                "column": measurement_column,
                "qubit": target,
                "basis": basis,
                "reset": name == "MR",
                "bit": outcome,
                "p0": probabilities[0],
                "p1": probabilities[1],
                "selected_probability": selected_probability,
            }
        )
        measurement_column += 1

        if measurement_column in {
            syndrome_per_round,
            2 * syndrome_per_round,
        }:
            round_index = measurement_column // syndrome_per_round - 1
            if (
                intervention_mode == "after_rounds"
                and round_index in requested_intervention_rounds
            ):
                gate = ry(intervention_angle)
                for data_qubit in data_qubits:
                    state = apply_single_qubit_gate(state, gate, data_qubit)
                applied_intervention_rounds.append(round_index)
            if (
                intervention_mode == "after_rounds"
                and measurement_column == 2 * syndrome_per_round
            ):
                preterminal_state = state.copy()

    if measurement_column != len(measurement_rows):
        raise ValueError("operation stream did not consume every measurement row")
    if intervention_mode == "after_terminal":
        gate = ry(intervention_angle)
        for round_index in requested_intervention_rounds:
            for data_qubit in data_qubits:
                state = apply_single_qubit_gate(state, gate, data_qubit)
            applied_intervention_rounds.append(int(round_index))
    if intervention_mode == "after_rounds" and preterminal_state is None:
        raise RuntimeError("preterminal checkpoint was not reached")

    detector_bits, observable_bits = fold_record(
        raw_bits,
        fixture["detector_rows"],
        fixture["observable_rows"],
    )
    log_branch_mass = math.fsum(
        math.log(probability) for probability in selected_probabilities
    )
    branch_mass = math.prod(selected_probabilities)
    return {
        "schema": RESULT_SCHEMA,
        "branch_id": branch_id,
        "raw_bits": tuple(raw_bits),
        "conditional_probabilities": tuple(selected_probabilities),
        "probability_rows": tuple(probability_rows),
        "branch_mass": float(branch_mass),
        "log_branch_mass": float(log_branch_mass),
        "detector_bits": detector_bits,
        "observable_bits": observable_bits,
        "checkpoint": PRETERMINAL_CHECKPOINT,
        "preterminal_state": preterminal_state,
        "final_state": state,
        "structural_zero_column": None,
        "post_measurement_one_weights": tuple(post_measurement_one_weights),
        "intervention_rounds_applied": tuple(applied_intervention_rounds),
    }


def forced_branch(
    fixture: Mapping[str, Any],
    raw_bits: Sequence[int],
    *,
    branch_id: str = "forced",
    intervention_angle: float = 0.02,
) -> dict[str, Any]:
    validate_fixture(fixture)
    expected_count = int(fixture["num_measurements"])
    bits = tuple(raw_bits)
    if len(bits) != expected_count:
        raise ValueError(
            f"forced branch needs exactly {expected_count} measurement bits"
        )
    if any(
        isinstance(bit, bool) or not isinstance(bit, (int, np.integer)) or bit not in (0, 1)
        for bit in bits
    ):
        raise ValueError("forced branch bits must be integer zero or one")

    def chooser(
        column: int,
        _row: Mapping[str, Any],
        _probabilities: tuple[float, float],
    ) -> int:
        return int(bits[column])

    return _execute(
        fixture,
        chooser,
        branch_id=branch_id,
        intervention_angle=intervention_angle,
    )


def greedy_branch(
    fixture: Mapping[str, Any],
    *,
    branch_id: str = "dense-greedy",
    intervention_angle: float = 0.02,
) -> dict[str, Any]:
    validate_fixture(fixture)

    def chooser(
        _column: int,
        _row: Mapping[str, Any],
        probabilities: tuple[float, float],
    ) -> int:
        return 0 if probabilities[0] >= probabilities[1] else 1

    return _execute(
        fixture,
        chooser,
        branch_id=branch_id,
        intervention_angle=intervention_angle,
    )


def alternate_branch(
    fixture: Mapping[str, Any],
    primary_bits: Sequence[int],
    *,
    branch_id: str = "dense-frozen-alternate",
    intervention_angle: float = 0.02,
) -> dict[str, Any] | None:
    validate_fixture(fixture)
    expected_count = int(fixture["num_measurements"])
    primary = tuple(primary_bits)
    if len(primary) != expected_count or any(
        isinstance(bit, bool) or not isinstance(bit, (int, np.integer)) or bit not in (0, 1)
        for bit in primary
    ):
        raise ValueError("primary branch has invalid bits or measurement count")
    flipped_column: int | None = None

    def chooser(
        column: int,
        row: Mapping[str, Any],
        probabilities: tuple[float, float],
    ) -> int:
        nonlocal flipped_column
        if flipped_column is None:
            if row["reset"]:
                opposite = 1 - int(primary[column])
                if probabilities[opposite] >= 1e-8:
                    flipped_column = column
                    return opposite
            return int(primary[column])
        return 0 if probabilities[0] >= probabilities[1] else 1

    result = _execute(
        fixture,
        chooser,
        branch_id=branch_id,
        intervention_angle=intervention_angle,
    )
    if flipped_column is None:
        return None
    result["alternate_flip_column"] = flipped_column
    return result


def _path_probability(
    fixture: Mapping[str, Any],
    bits: tuple[int, ...],
    *,
    intervention_angle: float,
    intervention_mode: str,
    omit_first_mx_h: bool,
) -> float:
    def chooser(
        column: int,
        _row: Mapping[str, Any],
        _probabilities: tuple[float, float],
    ) -> int:
        return bits[column]

    result = _execute(
        fixture,
        chooser,
        branch_id="enumerated",
        intervention_angle=intervention_angle,
        intervention_mode=intervention_mode,
        omit_first_mx_h=omit_first_mx_h,
        allow_structural_zero=True,
    )
    return float(result["branch_mass"])


def _enumerate_tracer_unchecked(
    fixture: Mapping[str, Any],
    *,
    intervention_angle: float,
    intervention_mode: str = "after_rounds",
    omit_first_mx_h: bool = False,
) -> dict[str, Any]:
    if fixture.get("distance") != 2 or fixture.get("num_measurements") != 10:
        raise ValueError("exact tracer enumeration requires the d=2 fixture")
    raw_probabilities = np.zeros(1024, dtype=np.float64)
    record_probabilities = np.zeros(64, dtype=np.float64)
    for index in range(1024):
        bits = tuple(int(bit) for bit in f"{index:010b}")
        probability = _path_probability(
            fixture,
            bits,
            intervention_angle=intervention_angle,
            intervention_mode=intervention_mode,
            omit_first_mx_h=omit_first_mx_h,
        )
        raw_probabilities[index] = probability
        detector_bits, observable_bits = fold_record(
            bits,
            fixture["detector_rows"],
            fixture["observable_rows"],
        )
        record_index = int(
            "".join(map(str, detector_bits + observable_bits)),
            2,
        )
        record_probabilities[record_index] += probability
    return {
        "schema": RESULT_SCHEMA,
        "mode": "tracer_full_law",
        "distance": 2,
        "rounds": 2,
        "intervention_angle_radians": intervention_angle,
        "intervention_mode": intervention_mode,
        "raw_bit_order": "measurement_column_ascending_big_endian",
        "record_bit_order": (
            "detector_row_ascending_then_observable_row_ascending_big_endian"
        ),
        "raw_probabilities": raw_probabilities,
        "record_probabilities": record_probabilities,
    }


def enumerate_tracer(
    fixture: Mapping[str, Any],
    *,
    intervention_angle: float = 0.02,
) -> dict[str, Any]:
    fixture_sha256 = validate_fixture(fixture)
    result = _enumerate_tracer_unchecked(
        fixture,
        intervention_angle=intervention_angle,
    )
    result["fixture_sha256"] = fixture_sha256
    return result


def total_variation(left: object, right: object) -> float:
    left_array = np.asarray(left, dtype=np.float64)
    right_array = np.asarray(right, dtype=np.float64)
    if (
        left_array.shape != right_array.shape
        or left_array.ndim != 1
        or not np.all(np.isfinite(left_array))
        or not np.all(np.isfinite(right_array))
        or np.any(left_array < 0.0)
        or np.any(right_array < 0.0)
    ):
        raise ValueError("TV inputs must be aligned finite nonnegative vectors")
    return 0.5 * float(np.abs(left_array - right_array).sum())


def _law_distance(
    clean: Mapping[str, Any],
    corrupted: Mapping[str, Any],
) -> float:
    return max(
        total_variation(
            clean["raw_probabilities"],
            corrupted["raw_probabilities"],
        ),
        total_variation(
            clean["record_probabilities"],
            corrupted["record_probabilities"],
        ),
    )


def _without_first_local_h_pair(
    fixture: Mapping[str, Any],
) -> tuple[dict[str, Any], int]:
    corrupted = copy.deepcopy(fixture)
    operations = corrupted["operations"]
    for index in range(1, len(operations) - 1):
        previous = operations[index - 1]
        operation = operations[index]
        following = operations[index + 1]
        if (
            operation["op"] == "CX"
            and previous["op"] == "H"
            and following["op"] == "H"
            and previous["qubits"] == following["qubits"]
            and previous["qubits"][0] in operation["qubits"]
        ):
            corrupted["operations"] = (
                operations[: index - 1]
                + [operation]
                + operations[index + 2 :]
            )
            return corrupted, index
    raise RuntimeError("fixture has no local-H entangler pair")


def physical_corruption_controls(
    fixture: Mapping[str, Any],
    d3_fixture: Mapping[str, Any],
) -> dict[str, float]:
    """Execute every dense-owned preregistered physical corruption."""

    validate_fixture(fixture)
    if fixture["distance"] != 2:
        raise ValueError("physical full-law controls use the d=2 tracer")
    validate_fixture(d3_fixture)
    if d3_fixture["distance"] != 3:
        raise ValueError("RY-sign state control requires the d=3 fixture")
    clean = _enumerate_tracer_unchecked(
        fixture,
        intervention_angle=0.02,
    )

    missing_h, _index = _without_first_local_h_pair(fixture)
    missing_h_law = _enumerate_tracer_unchecked(
        missing_h,
        intervention_angle=0.02,
    )

    swapped_tv = 0.0
    for index, operation in enumerate(fixture["operations"]):
        if operation["op"] != "CX":
            continue
        swapped = copy.deepcopy(fixture)
        swapped["operations"][index]["qubits"] = list(
            reversed(operation["qubits"])
        )
        swapped_law = _enumerate_tracer_unchecked(
            swapped,
            intervention_angle=0.02,
        )
        swapped_tv = _law_distance(clean, swapped_law)
        if swapped_tv > 1e-8:
            break

    missing_reset = copy.deepcopy(fixture)
    first_mr = next(
        index
        for index, operation in enumerate(missing_reset["operations"])
        if operation["op"] == "MR"
    )
    missing_reset["operations"][first_mr]["op"] = "M"
    missing_reset_law = _enumerate_tracer_unchecked(
        missing_reset,
        intervention_angle=0.02,
    )

    def first_one_then_greedy(
        column: int,
        _row: Mapping[str, Any],
        probabilities: tuple[float, float],
    ) -> int:
        if column == 0:
            return 1
        return 0 if probabilities[0] >= probabilities[1] else 1

    missing_reset_branch = _execute(
        missing_reset,
        first_one_then_greedy,
        branch_id="mr-without-reset-invariant-corruption",
        intervention_angle=0.02,
    )
    positive_d3 = greedy_branch(
        d3_fixture,
        branch_id="positive-ry-control",
        intervention_angle=0.02,
    )
    negative_d3 = forced_branch(
        d3_fixture,
        positive_d3["raw_bits"],
        branch_id="negative-ry-control",
        intervention_angle=-0.02,
    )
    negative_ry_difference = max(
        1.0
        - _fidelity(
            positive_d3["preterminal_state"],
            negative_d3["preterminal_state"],
        ),
        max(
            abs(left - right)
            for left, right in zip(
                positive_d3["conditional_probabilities"],
                negative_d3["conditional_probabilities"],
                strict=True,
            )
        ),
    )
    late_ry = _enumerate_tracer_unchecked(
        fixture,
        intervention_angle=0.02,
        intervention_mode="after_terminal",
    )
    missing_mx_h = _enumerate_tracer_unchecked(
        fixture,
        intervention_angle=0.02,
        omit_first_mx_h=True,
    )

    corrupted_rows = copy.deepcopy(fixture["detector_rows"])
    corrupted_rows[-1] = corrupted_rows[-1][:2]
    disagreement_mass = 0.0
    for index, probability in enumerate(clean["raw_probabilities"]):
        if probability == 0.0:
            continue
        bits = tuple(int(bit) for bit in f"{index:010b}")
        clean_fold = fold_record(
            bits,
            fixture["detector_rows"],
            fixture["observable_rows"],
        )
        corrupted_fold = fold_record(
            bits,
            corrupted_rows,
            fixture["observable_rows"],
        )
        if clean_fold != corrupted_fold:
            disagreement_mass += float(probability)

    return {
        "deleted_first_local_h_pair_tv": _law_distance(clean, missing_h_law),
        "swapped_first_nonsymmetric_cx_tv": swapped_tv,
        "mr_without_reset_tv": _law_distance(clean, missing_reset_law),
        "mr_without_reset_post_measurement_one_weight": float(
            missing_reset_branch["post_measurement_one_weights"][0]
        ),
        "negative_ry_state_or_probability_difference": (
            negative_ry_difference
        ),
        "ry_after_terminal_tv": _law_distance(clean, late_ry),
        "omitted_first_x_readout_h_tv": _law_distance(clean, missing_mx_h),
        "ragged_record_row_corruption_probability": disagreement_mass,
    }


def _fidelity(left: np.ndarray, right: np.ndarray) -> float:
    numerator = abs(np.vdot(left, right)) ** 2
    denominator = float(np.vdot(left, left).real * np.vdot(right, right).real)
    if denominator <= 0.0:
        raise ValueError("fidelity operands must have positive norm")
    return float(numerator / denominator)


def synthetic_corruption_controls() -> dict[str, dict[str, float]]:
    """Return nonvacuous analytic controls fixed before target execution."""

    phase = np.exp(1j * np.pi / 7.0)
    state = np.asarray(
        [np.sqrt(0.8), phase * np.sqrt(0.2)],
        dtype=np.complex128,
    )
    selected_zero = np.asarray([state[0], 0.0], dtype=np.complex128)
    wrongly_normalized = selected_zero / np.sqrt(0.2)
    norm_error = abs(float(np.vdot(wrongly_normalized, wrongly_normalized).real) - 1.0)

    scaled_projectors_probability_sum = 0.9**2 * (0.8 + 0.2)
    correct_log_mass = math.log(0.8) + math.log(0.3)
    omitted_log_mass = math.log(0.3)

    asymmetric = np.asarray(
        [1.0, 2.0j, 3.0 + 4.0j, 5.0],
        dtype=np.complex128,
    )
    asymmetric /= np.linalg.norm(asymmetric)
    reversed_axes = asymmetric.reshape(2, 2).T.reshape(-1)

    reset_to_one = np.asarray([0.0, 1.0], dtype=np.complex128)
    return {
        "wrong_born_normalization": {"norm_error": norm_error},
        "projector_scaled_0p9": {
            "completeness_error": abs(1.0 - scaled_projectors_probability_sum)
        },
        "omitted_path_factor": {
            "log_mass_error": abs(correct_log_mass - omitted_log_mass)
        },
        "reversed_asymmetric_axes": {
            "identity_fidelity": _fidelity(asymmetric, reversed_axes)
        },
        "reset_to_one": {
            "post_reset_one_weight": float(abs(reset_to_one[1]) ** 2)
        },
    }


def write_branch_artifacts(
    *,
    fixture: Mapping[str, Any],
    run_spec: Mapping[str, Any],
    branch: Mapping[str, Any],
    branch_authority: Mapping[str, Any],
    reference_parent: Mapping[str, Any],
    state_path: Path,
) -> dict[str, Any]:
    """Write a complete preterminal vector and return its neutral summary."""

    fixture_sha256 = validate_fixture(fixture)
    spec_sha256 = validate_spec(run_spec, fixture)
    if fixture["distance"] != 3:
        raise ValueError("complete dense branch artifacts are registered only for d3")
    state = np.asarray(branch.get("preterminal_state"))
    if (
        state.dtype != np.complex128
        or state.shape != (2 ** int(fixture["num_qubits"]),)
        or not np.all(np.isfinite(state))
    ):
        raise ValueError("branch lacks a complete finite complex128 checkpoint")
    norm = float(np.vdot(state, state).real)
    if abs(norm - 1.0) > 1e-12:
        raise ValueError("checkpoint state is not normalized")
    raw_bits = tuple(branch.get("raw_bits", ()))
    if len(raw_bits) != fixture["num_measurements"]:
        raise ValueError("branch raw-bit count mismatch")
    branch_summary = _neutral_branch(
        fixture_sha256=fixture_sha256,
        run_spec_sha256=spec_sha256,
        fixture=fixture,
        branch_id=str(branch["branch_id"]),
        bits=raw_bits,
    )
    branch_sha256 = canonical_json_sha256(branch_summary)
    authority = dict(branch_authority)
    role = authority.get("role")
    common_authority = {
        "schema",
        "role",
        "method",
        "branch_sha256",
    }
    if (
        authority.get("schema") != BRANCH_AUTHORITY_SCHEMA
        or authority.get("branch_sha256") != branch_sha256
        or role not in {"primary", "alternate"}
    ):
        raise ValueError("dense branch authority does not bind the neutral branch")
    if role == "primary":
        if (
            set(authority) != common_authority | {"selector"}
            or authority.get("method") != PRIMARY_AUTHORITY_METHOD
            or authority.get("selector")
            != run_spec["reference_branch"]["selector"]
        ):
            raise ValueError("dense primary authority mismatch")
    else:
        alternate_parent = authority.get("parent")
        if (
            set(authority)
            != common_authority | {"parent", "flip_column"}
            or authority.get("method") != ALTERNATE_AUTHORITY_METHOD
            or not isinstance(alternate_parent, Mapping)
            or set(alternate_parent)
            != {
                "summary_schema",
                "summary_file_sha256",
                "branch_sha256",
                "branch_id",
            }
            or alternate_parent.get("summary_schema")
            != EXACT_REFERENCE_SCHEMA
            or not isinstance(alternate_parent.get("branch_id"), str)
            or not alternate_parent["branch_id"]
            or isinstance(authority.get("flip_column"), bool)
            or not isinstance(authority.get("flip_column"), int)
            or not 0
            <= authority["flip_column"]
            < int(fixture["num_measurements"])
        ):
            raise ValueError("dense alternate authority mismatch")

    parent = dict(reference_parent)
    required_parent_fields = {
        "path",
        "file_sha256",
        "summary_schema",
        "role",
        "branch_sha256",
        "branch_id",
    }
    if (
        set(parent) != required_parent_fields
        or parent.get("summary_schema") != EXACT_REFERENCE_SCHEMA
        or parent.get("role") != "primary"
        or parent.get("branch_sha256")
        != (
            authority["branch_sha256"]
            if role == "primary"
            else authority["parent"]["branch_sha256"]
        )
        or not isinstance(parent.get("branch_id"), str)
        or not parent["branch_id"]
        or (
            role == "primary"
            and parent.get("branch_id") != branch_summary["branch_id"]
        )
    ):
        raise ValueError("dense reference-parent authority mismatch")
    parent_path = Path(str(parent.get("path", "")))
    parent_file_sha256 = _require_sha256(
        parent.get("file_sha256"),
        label="reference parent file hash",
    )
    if (
        not parent_path.is_absolute()
        or not parent_path.is_file()
        or _file_sha256(parent_path) != parent_file_sha256
    ):
        raise ValueError("dense reference-parent file binding mismatch")
    if role == "alternate" and (
        authority["parent"]["summary_schema"] != parent["summary_schema"]
        or authority["parent"]["summary_file_sha256"]
        != parent["file_sha256"]
        or authority["parent"]["branch_id"] != parent["branch_id"]
    ):
        raise ValueError("alternate authority does not bind its exact primary")

    absolute_state_path = state_path.resolve()
    _atomic_save_npy(
        absolute_state_path,
        np.ascontiguousarray(state, dtype=np.complex128),
    )
    state_sha256 = _file_sha256(absolute_state_path)
    probability_rows = [
        {
            "column": int(row["column"]),
            "qubit": int(row["qubit"]),
            "basis": str(row["basis"]),
            "reset": bool(row["reset"]),
            "bit": int(row["bit"]),
            "p0": float(row["p0"]),
            "p1": float(row["p1"]),
            "selected_probability": float(row["selected_probability"]),
        }
        for row in branch["probability_rows"]
    ]
    state_metadata = {
        "source_kind": "complete_complex128_state_vector",
        "path": str(absolute_state_path),
        "file_sha256": state_sha256,
        "sha256": state_sha256,
        "dtype": "complex128",
        "shape": [state.size],
        "qubit_axis_order": list(range(int(fixture["num_qubits"]))),
        "qubit_order": list(range(int(fixture["num_qubits"]))),
        "q0_bit_significance": "most_significant",
        "state_scope": "all_active_qubits",
        "norm_sq": norm,
        "checkpoint": PRETERMINAL_CHECKPOINT,
    }
    return {
        "schema": RESULT_SCHEMA,
        "status": "completed",
        "method": "numpy_complete_state_vector",
        "fixture": {
            "schema": fixture["schema"],
            "canonical_sha256": fixture_sha256,
            "stim_circuit_sha256": fixture["stim_circuit_sha256"],
            "distance": 3,
            "rounds": 2,
        },
        "run_spec": {
            "schema": run_spec["schema"],
            "canonical_sha256": spec_sha256,
        },
        "checkpoint": PRETERMINAL_CHECKPOINT,
        "branch": branch_summary,
        "branch_authority": authority,
        "reference_parent": parent,
        "probability_rows": probability_rows,
        "conditional_probabilities": [
            float(value) for value in branch["conditional_probabilities"]
        ],
        "branch_mass": float(branch["branch_mass"]),
        "log_branch_mass": float(branch["log_branch_mass"]),
        "record": {
            "detector_bits": list(branch["detector_bits"]),
            "observable_bits": list(branch["observable_bits"]),
            "absolute_xor_rows": True,
        },
        "state": state_metadata,
        "claim_boundary": (
            "bounded all-qubit dense reference; no leakage, Kraus, decoder, "
            "or scaling claim"
        ),
    }


def tracer_summary(
    fixture: Mapping[str, Any],
    enumeration_spec: Mapping[str, Any],
    law: Mapping[str, Any],
    ry_zero_law: Mapping[str, Any],
) -> dict[str, Any]:
    fixture_sha256 = validate_fixture(fixture)
    spec_sha256 = validate_spec(enumeration_spec, fixture)
    raw = np.asarray(law["raw_probabilities"], dtype=np.float64)
    record = np.asarray(law["record_probabilities"], dtype=np.float64)
    zero_record = np.asarray(
        ry_zero_law["record_probabilities"],
        dtype=np.float64,
    )
    if (
        raw.shape != (1024,)
        or record.shape != (64,)
        or zero_record.shape != (64,)
    ):
        raise ValueError("tracer law has wrong complete-support shape")
    record_tv = total_variation(record, zero_record)
    if record_tv <= 1e-6:
        raise ValueError("tracer RY nondegeneracy control did not trip")
    return {
        "schema": RESULT_SCHEMA,
        "status": "completed",
        "mode": "tracer_full_law",
        "fixture_sha256": fixture_sha256,
        "enumeration_spec_sha256": spec_sha256,
        "raw_bit_order": law["raw_bit_order"],
        "record_bit_order": law["record_bit_order"],
        "raw_law": {
            f"{index:010b}": float(probability)
            for index, probability in enumerate(raw)
        },
        "record_law": {
            f"{index:06b}": float(probability)
            for index, probability in enumerate(record)
        },
        "ry_zero_record_law": {
            f"{index:06b}": float(probability)
            for index, probability in enumerate(zero_record)
        },
        "ry_record_total_variation": record_tv,
        "ry_non_degeneracy_threshold": 1e-6,
        "ry_non_degeneracy_pass": True,
    }


def _read_json_with_raw(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload, raw


def _read_json(path: Path) -> dict[str, Any]:
    payload, _raw = _read_json_with_raw(path)
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument(
        "--mode",
        choices=("tracer", "primary", "alternate"),
        required=True,
    )
    parser.add_argument("--reference-summary", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-state", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    reference_input_required = args.mode in {"primary", "alternate"}
    if reference_input_required and args.reference_summary is None:
        raise ValueError(
            "primary/alternate mode requires --reference-summary"
        )
    if not reference_input_required and args.reference_summary is not None:
        raise ValueError("tracer mode does not consume --reference-summary")
    if args.mode == "tracer":
        if args.output_state is not None:
            raise ValueError("tracer mode has no state artifact")
        (args.output_json,) = preflight_output_paths((args.output_json,))
    else:
        if args.output_state is None:
            raise ValueError("branch mode requires --output-state")
        args.output_json, args.output_state = preflight_output_paths(
            (args.output_json, args.output_state)
        )

    fixture, fixture_raw = _read_json_with_raw(args.fixture)
    spec, spec_raw = _read_json_with_raw(args.spec)
    reference_summary: dict[str, Any] | None = None
    reference_raw: bytes | None = None
    if args.reference_summary is not None:
        reference_summary, reference_raw = _read_json_with_raw(
            args.reference_summary
        )
    raw_input_bytes = {
        "fixture": fixture_raw,
        "spec": spec_raw,
    }
    if reference_raw is not None:
        raw_input_bytes["reference_summary"] = reference_raw
    input_provenance = formal_input_provenance(
        fixture_path=args.fixture,
        spec_path=args.spec,
        reference_summary_path=args.reference_summary,
        raw_input_bytes=raw_input_bytes,
    )
    fixture_sha256 = validate_fixture(fixture)
    spec_sha256 = validate_spec(spec, fixture)

    if args.mode == "tracer":
        if fixture["distance"] != 2:
            raise ValueError("tracer mode requires distance=2")
        result = tracer_summary(
            fixture,
            spec,
            enumerate_tracer(fixture),
            enumerate_tracer(fixture, intervention_angle=0.0),
        )
    else:
        if fixture["distance"] != 3:
            raise ValueError("dense branch modes require distance=3")
        if reference_summary is None or reference_raw is None:
            raise RuntimeError(
                "validated exact-reference input is unexpectedly absent"
            )
        primary_bits, parent_branch, primary_authority = (
            validate_exact_primary_summary(
                reference_summary,
                fixture=fixture,
                run_spec=spec,
            )
        )
        parent_file_sha256 = hashlib.sha256(reference_raw).hexdigest()
        reference_parent = {
            "path": str(args.reference_summary.resolve()),
            "file_sha256": parent_file_sha256,
            "summary_schema": EXACT_REFERENCE_SCHEMA,
            "role": "primary",
            "branch_sha256": canonical_json_sha256(parent_branch),
            "branch_id": parent_branch["branch_id"],
        }
        if args.mode == "primary":
            branch_result = forced_branch(
                fixture,
                primary_bits,
                branch_id=parent_branch["branch_id"],
            )
            branch_authority = primary_authority
        else:
            alternate = alternate_branch(
                fixture,
                primary_bits,
                branch_id=(
                    f"xzzx-v2-alternate-from-"
                    f"{parent_branch['branch_id']}"
                ),
            )
            if alternate is None:
                raise RuntimeError("frozen alternate branch is unavailable")
            branch_result = alternate
            alternate_neutral = _neutral_branch(
                fixture_sha256=fixture_sha256,
                run_spec_sha256=spec_sha256,
                fixture=fixture,
                branch_id=str(alternate["branch_id"]),
                bits=alternate["raw_bits"],
            )
            branch_authority = alternate_branch_authority(
                branch=alternate_neutral,
                parent_summary_file_sha256=parent_file_sha256,
                parent_branch=parent_branch,
                flip_column=int(alternate["alternate_flip_column"]),
            )
        if args.output_state is None:
            raise RuntimeError("validated state output is unexpectedly absent")
        result = write_branch_artifacts(
            fixture=fixture,
            run_spec=spec,
            branch=branch_result,
            branch_authority=branch_authority,
            reference_parent=reference_parent,
            state_path=args.output_state,
        )
    result["input_provenance"] = input_provenance
    _atomic_write(args.output_json, canonical_json_bytes(result))
    print(
        f"dense XZZX mode={args.mode} distance={fixture['distance']} "
        f"fixture_sha256={fixture_sha256} spec_sha256={spec_sha256}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
