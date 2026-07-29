#!/usr/bin/env python3
"""Independent NumPy construction for one frozen n=8 state action."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
from typing import Any, Mapping, Sequence

import numpy as np


ANCHOR_WORKER_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_n8_r3_dense_anchor_worker.v1"
)
ANCHOR_COMPUTATION_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_n8_r3_dense_anchor_computation.v1"
)
FIXTURE_SCHEMA = "error_coupling_simulator.external.gcapeps_n8_r3_fixture.v1"
EXPECTED_FIXTURE_SHA256 = (
    "a494512a74ed20b28c067734359e9a09ab3df72ad07467160855c3c475ed0b8d"
)
EXPECTED_PREPARATION_STREAM_SHA256 = (
    "e42a195ba2736164700fcf86c1f5949f5a49d39c1932cfd9ee6b8cf6efab3538"
)
EXPECTED_CLIFFORD_STREAM_SHA256 = (
    "aeb75e08b6ac4a592d31199c2eafe9ed0c968465e50d05fa45b7d139a397e50c"
)
EXPECTED_MATRIX_SHA256 = {
    "H": "b8a0541aa80b1a09f1847692e688d8f59e6f7b27904794cb34e3a00547af4cc1",
    "S": "1ea2137ca5d78fbfcef3cfa04052cd34575f5e62ee440b714e6397cc6614322b",
    "S_DAG": (
        "ccdbdd050e820173b78aad0ea053b667a57470bece9c154274926d4192add3a8"
    ),
    "CX": "8147eeddb2b56869f494b2194eb43a7926d1bb5edb4d4f35c6fa9e9633dd4bf8",
    "CZ": "411d2854573bf05718bccb74b2bea00f6180dd0104861c8f112aa0295ea85b45",
    "SWAP": (
        "0fe211d0be6e5908155c70589905d5f91f528440f5a2ddcd39a477b25fd7e70d"
    ),
}


def _canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _fixture_sha256(fixture: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json_bytes(fixture)).hexdigest()


def _matrix(token: str) -> np.ndarray:
    """Independently spell the literal output-row/input-column gate."""

    if token == "H":
        s = np.float64(1.0) / np.sqrt(np.float64(2.0))
        values = ((s, s), (s, -s))
    elif token == "S":
        values = ((1.0, 0.0), (0.0, 1.0j))
    elif token == "S_DAG":
        values = ((1.0, 0.0), (0.0, -1.0j))
    elif token == "CX":
        values = (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0, 0.0),
        )
    elif token == "CZ":
        values = (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, -1.0),
        )
    elif token == "SWAP":
        values = (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        )
    else:
        raise ValueError(f"unsupported anchor gate token: {token!r}")
    matrix = np.ascontiguousarray(np.asarray(values, dtype="<c16"))
    digest = hashlib.sha256(matrix.tobytes(order="C")).hexdigest()
    if digest != EXPECTED_MATRIX_SHA256[token]:
        raise RuntimeError(f"independent {token} gate matrix hash drifted")
    residual = np.max(
        np.abs(
            matrix.conj().T @ matrix
            - np.eye(matrix.shape[0], dtype=np.complex128)
        )
    )
    if not np.isfinite(residual) or residual > 8.0 * np.finfo(np.float64).eps:
        raise RuntimeError(f"independent {token} gate is not unitary")
    return matrix


def _validate_gate_ledger(
    block: Mapping[str, Any],
    *,
    expected_stream_sha256: str,
) -> list[tuple[str, tuple[int, ...]]]:
    rows = block.get("gates")
    if not isinstance(rows, list):
        raise ValueError("anchor gate ledger is unavailable")
    gates: list[tuple[str, tuple[int, ...]]] = []
    stream = bytearray()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or row.get("index") != index:
            raise ValueError("anchor gate ledger index drifted")
        token = row.get("token")
        targets = row.get("logical_targets")
        if token not in EXPECTED_MATRIX_SHA256 or not isinstance(targets, list):
            raise ValueError("anchor gate ledger token or targets drifted")
        logical_targets = tuple(int(target) for target in targets)
        if (
            not logical_targets
            or len(set(logical_targets)) != len(logical_targets)
            or any(target < 0 or target >= 8 for target in logical_targets)
        ):
            raise ValueError("anchor gate targets are invalid")
        matrix = _matrix(str(token))
        digest = hashlib.sha256(matrix.tobytes(order="C")).hexdigest()
        if row.get("matrix_sha256") != digest:
            raise ValueError("anchor gate matrix binding drifted")
        target_text = ",".join(str(target) for target in logical_targets)
        stream.extend(
            f"{index:02d}|{token}|{target_text}|{digest}\n".encode("utf-8")
        )
        gates.append((str(token), logical_targets))
    observed = hashlib.sha256(bytes(stream)).hexdigest()
    if (
        observed != expected_stream_sha256
        or block.get("gate_stream_sha256") != expected_stream_sha256
    ):
        raise ValueError("anchor gate stream binding drifted")
    return gates


def _apply_gate(
    vector: np.ndarray,
    matrix: np.ndarray,
    targets: Sequence[int],
) -> np.ndarray:
    array = np.asarray(vector)
    target_tuple = tuple(int(target) for target in targets)
    if array.shape != (256,) or array.dtype != np.dtype("complex128"):
        raise ValueError("anchor vector contract drifted")
    if matrix.shape != (2 ** len(target_tuple),) * 2:
        raise ValueError("anchor gate shape does not match target count")
    remaining = tuple(q for q in range(8) if q not in target_tuple)
    permutation = target_tuple + remaining
    permuted = np.transpose(
        array.reshape((2,) * 8),
        permutation,
    ).reshape(2 ** len(target_tuple), -1)
    updated = matrix @ permuted
    inverse = tuple(int(axis) for axis in np.argsort(permutation))
    return np.ascontiguousarray(
        np.transpose(updated.reshape((2,) * 8), inverse).reshape(256),
        dtype=np.complex128,
    )


def _apply_gate_stream(
    vector: np.ndarray,
    gates: Sequence[tuple[str, tuple[int, ...]]],
) -> np.ndarray:
    state = np.asarray(vector).copy()
    for token, targets in gates:
        state = _apply_gate(state, _matrix(token), targets)
    return state


def _closed_form_preparation() -> np.ndarray:
    state = np.zeros(256, dtype=np.complex128)
    for a in (0, 1):
        for b in (0, 1):
            bits = (a, a, a, a, b, a ^ b, b, b)
            index = sum(bit << (7 - q) for q, bit in enumerate(bits))
            state[index] = np.complex128(0.5 + 0.0j)
    return state


def _pauli_action(vector: np.ndarray, body: str) -> np.ndarray:
    if len(body) != 8 or any(symbol not in "IXYZ" for symbol in body):
        raise ValueError("anchor Pauli body drifted")
    state = np.asarray(vector)
    if state.shape != (256,) or state.dtype != np.dtype("complex128"):
        raise ValueError("anchor Pauli input vector contract drifted")
    result = np.zeros(256, dtype=np.complex128)
    for input_index, amplitude in enumerate(state):
        output_index = input_index
        phase = np.complex128(1.0 + 0.0j)
        for q, symbol in enumerate(body):
            shift = 7 - q
            bit = (input_index >> shift) & 1
            if symbol == "X":
                output_index ^= 1 << shift
            elif symbol == "Y":
                output_index ^= 1 << shift
                phase *= np.complex128(1.0j if bit == 0 else -1.0j)
            elif symbol == "Z" and bit:
                phase *= np.complex128(-1.0)
        result[output_index] += phase * amplitude
    return result


def _coefficient(term: Mapping[str, Any]) -> np.complex128:
    real = np.float64(str(term.get("coefficient_real")))
    imag = np.float64(str(term.get("coefficient_imag")))
    phase = term.get("word_phase")
    if phase not in (-1, 1):
        raise ValueError("anchor word phase drifted")
    return np.complex128(complex(real, imag) * int(phase))


def _apply_pauli_sum(
    vector: np.ndarray,
    terms: Sequence[Mapping[str, Any]],
) -> np.ndarray:
    result = np.zeros(256, dtype=np.complex128)
    if len(terms) != 3:
        raise ValueError("anchor requires exactly three Pauli terms")
    for index, term in enumerate(terms):
        if term.get("term_index") != index:
            raise ValueError("anchor Pauli term order drifted")
        result += _coefficient(term) * _pauli_action(
            vector,
            str(term.get("pauli_body")),
        )
    return result


def _vector_sha256(vector: np.ndarray) -> str:
    array = np.asarray(vector)
    if (
        array.shape != (256,)
        or array.dtype != np.dtype("complex128")
        or not array.flags.c_contiguous
        or not np.all(np.isfinite(array))
    ):
        raise ValueError("anchor vector cannot be sealed")
    little = np.ascontiguousarray(array, dtype="<c16")
    return hashlib.sha256(little.tobytes(order="C")).hexdigest()


def compute_anchor(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Construct the residual and physical forms without simulator code."""

    if (
        not isinstance(fixture, Mapping)
        or fixture.get("schema") != FIXTURE_SCHEMA
        or fixture.get("n_qubits") != 8
        or fixture.get("active_rank") != 3
        or fixture.get("dtype") != "complex128"
    ):
        raise ValueError("anchor fixture contract drifted")
    fixture_digest = _fixture_sha256(fixture)
    if fixture_digest != EXPECTED_FIXTURE_SHA256:
        raise ValueError("anchor fixture canonical hash drifted")
    preparation = fixture.get("preparation")
    clifford = fixture.get("clifford")
    if not isinstance(preparation, Mapping) or not isinstance(clifford, Mapping):
        raise ValueError("anchor fixture gate blocks are unavailable")
    preparation_gates = _validate_gate_ledger(
        preparation,
        expected_stream_sha256=EXPECTED_PREPARATION_STREAM_SHA256,
    )
    clifford_gates = _validate_gate_ledger(
        clifford,
        expected_stream_sha256=EXPECTED_CLIFFORD_STREAM_SHA256,
    )

    closed_form = _closed_form_preparation()
    zero_state = np.zeros(256, dtype=np.complex128)
    zero_state[0] = np.complex128(1.0)
    gate_replay = _apply_gate_stream(zero_state, preparation_gates)
    residual = _apply_pauli_sum(
        closed_form,
        fixture.get("residual_terms", []),
    )
    physical_from_residual = _apply_gate_stream(residual, clifford_gates)
    physical_preparation = _apply_gate_stream(gate_replay, clifford_gates)
    physical_from_terms = _apply_pauli_sum(
        physical_preparation,
        fixture.get("physical_terms", []),
    )

    vectors = {
        "closed_form_preparation": closed_form,
        "gate_replay_preparation": gate_replay,
        "residual_state": residual,
        "physical_preparation_after_clifford": physical_preparation,
        "physical_from_residual_lift": physical_from_residual,
        "physical_from_signed_terms": physical_from_terms,
    }
    return {
        "schema": ANCHOR_COMPUTATION_SCHEMA,
        "fixture_sha256": fixture_digest,
        "vectors": vectors,
        "vector_sha256": {
            name: _vector_sha256(vector) for name, vector in vectors.items()
        },
        "imports_forbidden_simulator_module": False,
        "enters_efficiency_timing_or_rss": False,
        "qualification_scope": "one_n8_input_state_action_only",
    }


def _strict_json_loads(payload: bytes) -> Any:
    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key!r}")
            result[key] = value
        return result

    def reject_constant(token: str) -> None:
        raise ValueError(f"nonfinite JSON token is forbidden: {token}")

    return json.loads(
        payload.decode("utf-8"),
        object_pairs_hook=object_pairs,
        parse_constant=reject_constant,
    )


def _report_content_hash(report: Mapping[str, Any]) -> str:
    payload = dict(report)
    payload.pop("content_hash", None)
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _publish_with_writer_noreplace(path: Path, writer: Any) -> None:
    destination = Path(path).absolute()
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".stage",
        dir=destination.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            writer(stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _publish_vector_noreplace(path: Path, vector: np.ndarray) -> None:
    _publish_with_writer_noreplace(
        path,
        lambda stream: np.save(stream, vector, allow_pickle=False),
    )


def _publish_bytes_noreplace(path: Path, payload: bytes) -> None:
    _publish_with_writer_noreplace(path, lambda stream: stream.write(payload))


def _forbidden_loaded_modules() -> list[str]:
    return sorted(
        name
        for name in sys.modules
        if name.split(".", 1)[0] in {"quimb", "stim", "sdim"}
        or ".gcapeps" in name
    )


def _load_frozen_fixture(path: Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    fixture = _strict_json_loads(raw)
    if not isinstance(fixture, dict):
        raise ValueError("anchor fixture JSON must be an object")
    if raw != _canonical_json_bytes(fixture):
        raise ValueError("anchor fixture file is not exact canonical JSON")
    if hashlib.sha256(raw).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise ValueError("anchor fixture file hash drifted")
    return fixture


def _worker_report(
    fixture: Mapping[str, Any],
    computation: Mapping[str, Any],
    output_directory: Path,
) -> dict[str, Any]:
    vectors = computation["vectors"]
    vector_rows: dict[str, dict[str, Any]] = {}
    for name, vector in vectors.items():
        relative_path = f"{name}.npy"
        _publish_vector_noreplace(output_directory / relative_path, vector)
        vector_rows[name] = {
            "relative_path": relative_path,
            "sha256": computation["vector_sha256"][name],
            "shape": [256],
            "dtype": "complex128",
            "byte_order": "little_endian_c_order_payload_hash",
        }

    preparation_delta = float(
        np.max(
            np.abs(
                vectors["closed_form_preparation"]
                - vectors["gate_replay_preparation"]
            )
        )
    )
    physical_delta = float(
        np.max(
            np.abs(
                vectors["physical_from_residual_lift"]
                - vectors["physical_from_signed_terms"]
            )
        )
    )
    forbidden = _forbidden_loaded_modules()
    checks = {
        "preparation_max_abs_difference": preparation_delta,
        "physical_dual_form_max_abs_difference": physical_delta,
        "preparation_pass": preparation_delta <= 2.0e-11,
        "physical_dual_form_pass": physical_delta <= 2.0e-11,
        "forbidden_import_pass": not forbidden,
    }
    checks_passed = (
        checks["preparation_pass"]
        and checks["physical_dual_form_pass"]
        and checks["forbidden_import_pass"]
    )
    report: dict[str, Any] = {
        "schema": ANCHOR_WORKER_SCHEMA,
        "fixture": {
            "schema": fixture["schema"],
            "id": fixture["fixture_id"],
            "sha256": computation["fixture_sha256"],
            "preparation_gate_stream_sha256": fixture["preparation"][
                "gate_stream_sha256"
            ],
            "clifford_gate_stream_sha256": fixture["clifford"][
                "gate_stream_sha256"
            ],
        },
        "vectors": vector_rows,
        "checks": checks,
        "anchor_self_verdict": "PASS" if checks_passed else "FAIL",
        "scope": {
            "qualification": "one_n8_input_state_action_only",
            "enters_efficiency_timing_or_rss": False,
            "generic_peps_truth": False,
            "all_input_operator_equality": False,
            "record_law": False,
        },
        "runtime_provenance": {
            "python_version": platform.python_version(),
            "python_executable": str(Path(sys.executable).resolve()),
            "numpy_version": np.__version__,
            "worker_source_sha256": hashlib.sha256(
                Path(__file__).read_bytes()
            ).hexdigest(),
            "forbidden_loaded_modules": forbidden,
        },
        "all_checks_passed": checks_passed,
    }
    report["content_hash"] = _report_content_hash(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    arguments = parser.parse_args()

    output_directory = arguments.output_directory.absolute()
    if not output_directory.is_dir():
        raise FileNotFoundError("anchor output directory must already exist")
    if any(output_directory.iterdir()):
        raise FileExistsError("anchor output directory must be empty")
    forbidden_before = _forbidden_loaded_modules()
    if forbidden_before:
        raise RuntimeError(
            f"anchor fresh process already loaded forbidden modules: {forbidden_before}"
        )
    fixture = _load_frozen_fixture(arguments.fixture)
    computation = compute_anchor(fixture)
    report = _worker_report(fixture, computation, output_directory)
    if report["all_checks_passed"] is not True:
        raise RuntimeError("anchor self checks failed")
    _publish_bytes_noreplace(
        output_directory / "anchor_report.json",
        _canonical_json_bytes(report),
    )
    directory_fd = os.open(output_directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
