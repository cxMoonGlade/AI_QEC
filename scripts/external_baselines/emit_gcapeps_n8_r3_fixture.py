#!/usr/bin/env python3
"""Emit the neutral n=8, active-rank-3 GCAPEPS differential fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping, Sequence

import numpy as np


FIXTURE_SCHEMA = "error_coupling_simulator.external.gcapeps_n8_r3_fixture.v1"
EXPECTED_FIXTURE_SHA256 = (
    "a494512a74ed20b28c067734359e9a09ab3df72ad07467160855c3c475ed0b8d"
)
PREPARATION_GATE_STREAM_SHA256 = (
    "e42a195ba2736164700fcf86c1f5949f5a49d39c1932cfd9ee6b8cf6efab3538"
)
CLIFFORD_GATE_STREAM_SHA256 = (
    "aeb75e08b6ac4a592d31199c2eafe9ed0c968465e50d05fa45b7d139a397e50c"
)
GATE_MATRIX_SHA256 = {
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
PREPARATION_GATES = (
    ("H", (0,)),
    ("CX", (0, 1)),
    ("CX", (1, 2)),
    ("CX", (2, 3)),
    ("H", (4,)),
    ("CX", (4, 5)),
    ("CX", (5, 6)),
    ("CX", (6, 7)),
    ("CX", (1, 5)),
)
CLIFFORD_GATES = (
    ("H", (0,)),
    ("S", (1,)),
    ("CX", (0, 4)),
    ("H", (3,)),
    ("CZ", (2, 6)),
    ("S_DAG", (7,)),
    ("SWAP", (5, 6)),
    ("CX", (6, 7)),
    ("SWAP", (5, 6)),
    ("SWAP", (1, 2)),
)
SITE_ORDER = tuple((q // 4, q % 4) for q in range(8))
GRAPH_EDGES = (
    (0, 1),
    (1, 2),
    (2, 3),
    (4, 5),
    (5, 6),
    (6, 7),
    (0, 4),
    (1, 5),
    (2, 6),
    (3, 7),
)


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """Return the fixture's canonical UTF-8 JSON representation."""

    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_sha256(payload: Mapping[str, Any]) -> str:
    """Hash a fixture using its canonical representation."""

    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def gate_matrix(token: str) -> np.ndarray:
    """Build one frozen raw gate as C-contiguous little-endian complex128."""

    one = np.float64(1.0)
    zero = np.float64(0.0)
    if token == "H":
        scale = one / np.sqrt(np.float64(2.0))
        values = [[scale, scale], [scale, -scale]]
    elif token == "S":
        values = [[one, zero], [zero, 1.0j]]
    elif token == "S_DAG":
        values = [[one, zero], [zero, -1.0j]]
    elif token == "CX":
        values = [
            [one, zero, zero, zero],
            [zero, one, zero, zero],
            [zero, zero, zero, one],
            [zero, zero, one, zero],
        ]
    elif token == "CZ":
        values = [
            [one, zero, zero, zero],
            [zero, one, zero, zero],
            [zero, zero, one, zero],
            [zero, zero, zero, -one],
        ]
    elif token == "SWAP":
        values = [
            [one, zero, zero, zero],
            [zero, zero, one, zero],
            [zero, one, zero, zero],
            [zero, zero, zero, one],
        ]
    else:
        raise ValueError(f"unsupported frozen gate token: {token!r}")
    return np.ascontiguousarray(np.asarray(values, dtype="<c16"))


def matrix_sha256(matrix: np.ndarray) -> str:
    """Hash the exact `<c16` C-order matrix bytes."""

    array = np.asarray(matrix)
    if (
        array.dtype != np.dtype("<c16")
        or not array.flags.c_contiguous
        or array.ndim != 2
    ):
        raise ValueError("gate matrix must be a C-contiguous little-endian <c16 matrix")
    return hashlib.sha256(array.tobytes(order="C")).hexdigest()


def unitarity_residual(matrix: np.ndarray) -> float:
    """Return the frozen max-absolute unitary residual."""

    array = np.asarray(matrix)
    identity = np.eye(array.shape[0], dtype=np.complex128)
    return float(np.max(np.abs(array.conj().T @ array - identity)))


def gate_ledger(
    gates: Sequence[tuple[str, tuple[int, ...]]],
) -> tuple[list[dict[str, Any]], str]:
    """Build and hash one chronological logical-target gate ledger."""

    rows: list[dict[str, Any]] = []
    serialized = bytearray()
    tolerance = 8.0 * np.finfo(np.float64).eps
    for index, (token, targets) in enumerate(gates):
        matrix = gate_matrix(token)
        digest = matrix_sha256(matrix)
        expected = GATE_MATRIX_SHA256[token]
        if digest != expected:
            raise RuntimeError(f"{token} matrix hash drifted")
        residual = unitarity_residual(matrix)
        if not np.isfinite(residual) or residual > tolerance:
            raise RuntimeError(f"{token} matrix is not unitary within the frozen band")
        target_text = ",".join(str(target) for target in targets)
        serialized.extend(
            f"{index:02d}|{token}|{target_text}|{digest}\n".encode("utf-8")
        )
        rows.append(
            {
                "index": index,
                "token": token,
                "logical_targets": list(targets),
                "matrix_sha256": digest,
            }
        )
    return rows, hashlib.sha256(bytes(serialized)).hexdigest()


def build_fixture() -> dict[str, Any]:
    """Construct the fully frozen neutral state-action fixture."""

    preparation_rows, preparation_hash = gate_ledger(PREPARATION_GATES)
    clifford_rows, clifford_hash = gate_ledger(CLIFFORD_GATES)
    if preparation_hash != PREPARATION_GATE_STREAM_SHA256:
        raise RuntimeError("preparation gate stream hash drifted")
    if clifford_hash != CLIFFORD_GATE_STREAM_SHA256:
        raise RuntimeError("Clifford gate stream hash drifted")

    return {
        "schema": FIXTURE_SCHEMA,
        "fixture_id": "gcapeps_n8_r3_equal_status_candidate_state_action",
        "claim_boundary": (
            "one untruncated n=8 input-state action and fixture-level "
            "plain-Quimb-versus-GCAPEPS efficiency only"
        ),
        "n_qubits": 8,
        "active_rank": 3,
        "dtype": "complex128",
        "site_map": [
            {"logical_qubit": q, "coordinate": list(SITE_ORDER[q])}
            for q in range(8)
        ],
        "site_order": [list(site) for site in SITE_ORDER],
        "graph_edges": [list(edge) for edge in GRAPH_EDGES],
        "amplitude_convention": {
            "local_basis": ["|0>", "|1>"],
            "axes": list(range(8)),
            "q0_axis": 0,
            "q0_bit_significance": "most_significant",
            "flat_index": "sum_q bit(q)*2**(7-q)",
            "matrix_indices": "row_is_output_column_is_input",
            "two_qubit_basis": ["|00>", "|01>", "|10>", "|11>"],
        },
        "gate_matrix_contract": {
            "dtype": "<c16",
            "layout": "C",
            "matrix_sha256": dict(GATE_MATRIX_SHA256),
            "unitarity_max_abs_bound": float(
                8.0 * np.finfo(np.float64).eps
            ),
        },
        "plain_pepo_local_axis_contract": {
            "semantic_matrix_axes": ["output_ket", "input_bra"],
            "quimb_product_operator_raw_axes": ["bra_input", "ket_output"],
            "lowering": "raw_bra_ket=desired_output_input.T",
            "runtime_control": "one_site_nonsymmetric_dense_equals_raw_transpose",
            "pauli_desired_sha256": {
                "I": "fbfcd8f81e798f2e4e04256375c0766e6166910440ffd3de2b9b37a88ab5aac7",
                "X": "33c11b461fe67e717e37ac34a568cd1c27a89013703bf5b84194f0732a33a26d",
                "Y": "dd9ec1e25765af2c4c067c9cb272c3e394d0044e941c70a6f2c078830a77c373",
                "Z": "c8f478783d65670e5d4823a34aa1be2ec54809ad61ca0d10e4da56195c4778fc"
            },
            "pauli_raw_bra_ket_sha256": {
                "I": "fbfcd8f81e798f2e4e04256375c0766e6166910440ffd3de2b9b37a88ab5aac7",
                "X": "33c11b461fe67e717e37ac34a568cd1c27a89013703bf5b84194f0732a33a26d",
                "Y": "84f1031f8456b7da8f6096a18778bb8974665c5bcbda2270e004f833162deaf6",
                "Z": "c8f478783d65670e5d4823a34aa1be2ec54809ad61ca0d10e4da56195c4778fc"
            }
        },
        "preparation": {
            "gates": preparation_rows,
            "gate_stream_sha256": preparation_hash,
            "closed_form_support": [
                {
                    "a": a,
                    "b": b,
                    "bits": [
                        a,
                        a,
                        a,
                        a,
                        b,
                        a ^ b,
                        b,
                        b,
                    ],
                    "amplitude_real": "0.5",
                    "amplitude_imag": "0.0",
                }
                for a in (0, 1)
                for b in (0, 1)
            ],
        },
        "residual_terms": [
            {
                "term_index": 0,
                "coefficient_real": "0.0",
                "coefficient_imag": "-0.8",
                "pauli_body": "XXYIZZXZ",
                "word_phase": 1,
            },
            {
                "term_index": 1,
                "coefficient_real": "0.0",
                "coefficient_imag": "-0.48",
                "pauli_body": "YXYZIZXZ",
                "word_phase": 1,
            },
            {
                "term_index": 2,
                "coefficient_real": "0.0",
                "coefficient_imag": "-0.36",
                "pauli_body": "ZXYZZZXI",
                "word_phase": 1,
            },
        ],
        "clifford": {
            "gates": clifford_rows,
            "gate_stream_sha256": clifford_hash,
            "stim_phase_dagger_token": "S_DAG",
            "logical_prefix_gate_count": 8,
            "graph_local_gate_count": 10,
        },
        "physical_terms": [
            {
                "term_index": 0,
                "coefficient_real": "0.0",
                "coefficient_imag": "-0.8",
                "pauli_body": "IXYIZIYZ",
                "word_phase": -1,
                "expected_signed_pullback": "+XXYIZZXZ",
            },
            {
                "term_index": 1,
                "coefficient_real": "0.0",
                "coefficient_imag": "-0.48",
                "pauli_body": "YXYXXIYZ",
                "word_phase": 1,
                "expected_signed_pullback": "+YXYZIZXZ",
            },
            {
                "term_index": 2,
                "coefficient_real": "0.0",
                "coefficient_imag": "-0.36",
                "pauli_body": "YXYXYZYI",
                "word_phase": 1,
                "expected_signed_pullback": "+ZXYZZZXI",
            },
        ],
        "routing": {
            "dependence_set": [0, 3, 4, 7],
            "conservative_support": list(range(8)),
            "root": 0,
            "vertices": [0, 1, 2, 3, 4, 7],
            "edges": [[0, 1], [0, 4], [1, 2], [2, 3], [3, 7]],
        },
        "gcapeps_resource_limits": {
            "max_local_operator_elements": 36,
            "max_total_operator_elements": 176,
            "max_local_candidate_tensor_elements": 144,
            "max_total_candidate_tensor_elements": 336,
            "max_predicted_bond_dimension": 6,
            "max_routed_rank_product": 3,
            "max_total_bond_growth_product": 3,
        },
        "expected_representation": {
            "preparation_state_bonds": [2, 2, 2, 2, 2, 2, 1, 2, 1, 1],
            "preparation_site_elements": [4, 16, 8, 4, 4, 16, 8, 4],
            "gcapeps_operator_total_elements": 176,
            "gcapeps_operator_max_local_elements": 36,
            "gcapeps_state_after_total_elements": 336,
            "gcapeps_state_after_max_local_elements": 144,
            "plain_operator_bond_dimension": 3,
            "plain_operator_total_elements": 576,
            "plain_operator_max_local_elements": 108,
        },
        "metric_bands": {
            "d_rel_max": 2.0e-11,
            "d_norm_max": 2.0e-11,
            "infidelity_max": 1.0e-12,
            "fidelity_roundoff_correction_max": 1.0e-12,
            "corruption_movement_min": 1.0e-8,
        },
    }


def validate_fixture(fixture: Mapping[str, Any]) -> str:
    """Reject every semantic or canonical-JSON drift from the frozen fixture."""

    if not isinstance(fixture, Mapping):
        raise ValueError("fixture must be an object")
    observed = canonical_json_bytes(fixture)
    expected = canonical_json_bytes(build_fixture())
    if observed != expected:
        raise ValueError("GCAPEPS n=8 r=3 fixture semantic mismatch")
    digest = hashlib.sha256(observed).hexdigest()
    if digest != EXPECTED_FIXTURE_SHA256:
        raise ValueError("GCAPEPS n=8 r=3 fixture canonical hash drifted")
    return digest


def _publish_bytes_noreplace(path: Path, payload: bytes) -> None:
    destination = Path(path).absolute()
    parent = destination.parent
    if not parent.is_dir():
        raise FileNotFoundError(f"fixture output parent does not exist: {parent}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".stage",
        dir=parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, destination)
        directory_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    fixture = build_fixture()
    validate_fixture(fixture)
    _publish_bytes_noreplace(
        arguments.output,
        canonical_json_bytes(fixture),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
