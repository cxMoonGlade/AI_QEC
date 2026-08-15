#!/usr/bin/env python3
"""Independent dense reference for the frozen GCAPEPS finite-memory fixture.

The scientific path in this file is intentionally NumPy/stdlib only.  It
doesn't import the fixture emitter, Quimb, Stim, SDIM, GCAPEPS, ECS, or any
candidate gate helper.  The neutral fixture supplies primitive gate names,
targets, and angles; this worker independently spells and applies every matrix
in q0-most-significant-bit order.

``run_dense_reference`` is the testable scientific seam.  Transport framing is
kept outside that function so the evaluator math can be exercised without the
systemd worker lifecycle.
"""

from __future__ import annotations

import ast
import base64
from dataclasses import dataclass, field
import hashlib
from itertools import permutations
import json
import math
from pathlib import Path
import resource
import struct
import sys
import time
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "dense_reference.v1"
)
FIXTURE_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory.fixture.v1"
)
INPUT_TRANSPORT_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "input_transport.v1"
)
NDARRAY_ENCODING = "ndarray-v1"
NUMERICAL_ZERO = 1.0e-12
EIGEN_RECONSTRUCTION_TOLERANCE = 1.0e-10
BLP_INCREMENT_TOLERANCE = 1.0e-10
MASK_PREFIX = b"gcapeps-finite-memory-mask-v1\x00"
ACTIVE_AXES = {1: ("Z",), 2: ("X", "Y"), 3: ("X", "Y", "Z")}
FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "error_coupling_simulator",
        "gcapeps",
        "quimb",
        "sdim",
        "stim",
    }
)
_IMPORT_BASELINE_MODULE_NAMES = frozenset(sys.modules)

_H = np.ascontiguousarray(
    np.asarray(
        ((1.0, 1.0), (1.0, -1.0)),
        dtype=np.complex128,
    )
    / np.sqrt(np.float64(2.0))
)
_S = np.ascontiguousarray(
    np.asarray(((1.0, 0.0), (0.0, 1.0j)), dtype=np.complex128)
)
_X = np.ascontiguousarray(
    np.asarray(((0.0, 1.0), (1.0, 0.0)), dtype=np.complex128)
)
_Y = np.ascontiguousarray(
    np.asarray(((0.0, -1.0j), (1.0j, 0.0)), dtype=np.complex128)
)
_Z = np.ascontiguousarray(
    np.asarray(((1.0, 0.0), (0.0, -1.0)), dtype=np.complex128)
)
_I2 = np.ascontiguousarray(np.eye(2, dtype=np.complex128))
_I4 = np.ascontiguousarray(np.eye(4, dtype=np.complex128))
_CX = np.ascontiguousarray(
    np.asarray(
        (
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
            (0.0, 0.0, 1.0, 0.0),
        ),
        dtype=np.complex128,
    )
)
_PAULI = {"X": _X, "Y": _Y, "Z": _Z}


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_u64(value: Any, name: str) -> int:
    if not _is_int(value) or value < 0 or value > (1 << 64) - 1:
        raise ValueError(f"{name} must be an unsigned 64-bit integer")
    return value


def _require_exact_keys(
    value: Mapping[str, Any],
    expected: Iterable[str],
    name: str,
) -> None:
    expected_set = set(expected)
    if set(value) != expected_set:
        missing = sorted(expected_set - set(value))
        extra = sorted(set(value) - expected_set)
        raise ValueError(f"{name} key mismatch: missing={missing}, extra={extra}")


def _finite_float(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite JSON number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    if not isinstance(value, Mapping):
        raise TypeError("canonical JSON root must be an object")
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def canonical_sha256(value: Mapping[str, Any]) -> str:
    projection = dict(value)
    projection.pop("result_projection_sha256", None)
    return hashlib.sha256(canonical_json_bytes(projection)).hexdigest()


def _assert_little_endian() -> None:
    if sys.byteorder != "little" or np.dtype(np.complex128).str != "<c16":
        raise RuntimeError("dense reference requires a little-endian host")
    if np.dtype(np.float64).str != "<f8":
        raise RuntimeError("dense reference requires little-endian float64")


def _validate_matrix(
    matrix: np.ndarray,
    *,
    dimension: int,
    name: str,
) -> np.ndarray:
    if (
        not isinstance(matrix, np.ndarray)
        or matrix.shape != (dimension, dimension)
        or matrix.dtype != np.dtype(np.complex128)
        or not matrix.flags.c_contiguous
        or not np.all(np.isfinite(matrix.real))
        or not np.all(np.isfinite(matrix.imag))
    ):
        raise ValueError(f"{name} matrix violates the c128 contract")
    residual = float(
        np.max(
            np.abs(
                matrix.conj().T @ matrix
                - np.eye(dimension, dtype=np.complex128)
            )
        )
    )
    if not math.isfinite(residual) or residual > 1.0e-12:
        raise ValueError(f"{name} matrix is not unitary")
    return matrix


def one_qubit_matrix(kind: str) -> np.ndarray:
    matrices = {"H": _H, "S": _S, "X": _X}
    if kind not in matrices:
        raise ValueError(f"unsupported independent one-qubit gate: {kind!r}")
    return _validate_matrix(matrices[kind].copy(order="C"), dimension=2, name=kind)


def cx_matrix() -> np.ndarray:
    return _validate_matrix(_CX.copy(order="C"), dimension=4, name="CX")


def pauli_rotation_matrix(axis: str, theta: float) -> np.ndarray:
    """Return exp(-i theta P.P / 2) in output-row/input-column order."""

    if axis not in _PAULI:
        raise ValueError(f"unsupported collision axis: {axis!r}")
    angle = _finite_float(theta, "theta")
    body = np.kron(_PAULI[axis], _PAULI[axis])
    matrix = np.ascontiguousarray(
        np.cos(np.float64(angle / 2.0)) * _I4
        - 1.0j * np.sin(np.float64(angle / 2.0)) * body,
        dtype=np.complex128,
    )
    return _validate_matrix(matrix, dimension=4, name=f"R{axis}{axis}")


def partial_swap_matrix(gamma: float) -> np.ndarray:
    """McCloskey--Paternostro positive-sign partial SWAP."""

    angle = _finite_float(gamma, "gamma")
    swap = np.ascontiguousarray(
        np.asarray(
            (
                (1.0, 0.0, 0.0, 0.0),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 1.0, 0.0, 0.0),
                (0.0, 0.0, 0.0, 1.0),
            ),
            dtype=np.complex128,
        )
    )
    return np.ascontiguousarray(
        np.cos(np.float64(angle)) * _I4
        + 1.0j * np.sin(np.float64(angle)) * swap,
        dtype=np.complex128,
    )


def partial_swap_factorization_audit(gamma: float) -> dict[str, Any]:
    """Pin all commuting XYZ products and reject three map corruptions."""

    angle = _finite_float(gamma, "gamma")
    expected = np.ascontiguousarray(
        np.exp(-0.5j * angle) * partial_swap_matrix(angle),
        dtype=np.complex128,
    )
    factors = {
        axis: pauli_rotation_matrix(axis, -angle)
        for axis in ("X", "Y", "Z")
    }
    order_errors: dict[str, float] = {}
    for order in permutations(("X", "Y", "Z")):
        product = _I4.copy(order="C")
        for axis in order:
            product = np.ascontiguousarray(
                product @ factors[axis],
                dtype=np.complex128,
            )
        order_errors["".join(order)] = float(
            np.max(np.abs(product - expected))
        )
    summed = np.ascontiguousarray(
        factors["X"] + factors["Y"] + factors["Z"],
        dtype=np.complex128,
    )
    phase_removed = partial_swap_matrix(angle)
    opposite = _I4.copy(order="C")
    for axis in ("X", "Y", "Z"):
        opposite = np.ascontiguousarray(
            opposite @ pauli_rotation_matrix(axis, angle),
            dtype=np.complex128,
        )
    sum_corruption_residual = float(np.max(np.abs(summed - expected)))
    phase_removal_residual = float(
        np.max(np.abs(phase_removed - expected))
    )
    opposite_sign_residual = float(
        np.max(np.abs(opposite - expected))
    )
    passed = bool(
        set(order_errors) == {
            "XYZ",
            "XZY",
            "YXZ",
            "YZX",
            "ZXY",
            "ZYX",
        }
        and max(order_errors.values(), default=math.inf) <= NUMERICAL_ZERO
        and sum_corruption_residual > 1.0e-2
        and phase_removal_residual > 1.0e-2
        and opposite_sign_residual > 1.0e-2
    )
    if not passed:
        raise ValueError("partial-SWAP factorization firewall failed")
    return {
        "schema": (
            "error_coupling_simulator.external.gcapeps_finite_memory."
            "partial_swap_factorization_audit.v1"
        ),
        "gamma_float64_hex": float(angle).hex(),
        "rotation_theta_float64_hex": float(-angle).hex(),
        "analytic_global_phase": "exp(-0.5j*gamma)",
        "ordered_product_max_abs_errors": order_errors,
        "sum_instead_of_product_max_abs_residual": (
            sum_corruption_residual
        ),
        "removed_global_phase_max_abs_residual": phase_removal_residual,
        "opposite_rotation_sign_max_abs_residual": (
            opposite_sign_residual
        ),
        "corruption_minimum_residual": 1.0e-2,
        "phase_fit_used": False,
        "passed": True,
    }


def audit_import_independence() -> dict[str, Any]:
    """Fail closed on forbidden static, newly loaded, or bound modules."""

    source_path = Path(__file__).resolve(strict=True)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(source_path))
    static_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            static_roots.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            static_roots.add(node.module.split(".", 1)[0])
    forbidden_static = sorted(static_roots & FORBIDDEN_IMPORT_ROOTS)
    newly_loaded_forbidden = sorted(
        name
        for name in sys.modules
        if name not in _IMPORT_BASELINE_MODULE_NAMES
        and name.split(".", 1)[0] in FORBIDDEN_IMPORT_ROOTS
    )
    forbidden_globals: set[str] = set()
    for value in globals().values():
        names = (
            getattr(value, "__name__", None),
            getattr(value, "__module__", None),
        )
        for name in names:
            if (
                isinstance(name, str)
                and name.split(".", 1)[0] in FORBIDDEN_IMPORT_ROOTS
            ):
                forbidden_globals.add(name)
    audit = {
        "schema": (
            "error_coupling_simulator.external.gcapeps_finite_memory."
            "dense_import_independence_audit.v1"
        ),
        "source_sha256": hashlib.sha256(
            source.encode("utf-8")
        ).hexdigest(),
        "forbidden_roots": sorted(FORBIDDEN_IMPORT_ROOTS),
        "static_import_roots": sorted(static_roots),
        "forbidden_static_import_roots": forbidden_static,
        "newly_loaded_forbidden_modules": newly_loaded_forbidden,
        "forbidden_bound_global_modules": sorted(forbidden_globals),
        "scientific_dependency_roots": ["numpy", "python_stdlib"],
        "passed": not (
            forbidden_static
            or newly_loaded_forbidden
            or forbidden_globals
        ),
    }
    if audit["passed"] is not True:
        raise RuntimeError(
            "dense import independence audit failed: "
            + json.dumps(
                audit,
                ensure_ascii=True,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    return audit


def apply_gate_q0_msb(
    vector: np.ndarray,
    matrix: np.ndarray,
    targets: Sequence[int],
    *,
    num_qubits: int,
) -> np.ndarray:
    """Apply a one/two-qubit matrix with q0 as the most-significant axis."""

    expected_shape = (1 << num_qubits,)
    if (
        not isinstance(vector, np.ndarray)
        or vector.shape != expected_shape
        or vector.dtype != np.dtype(np.complex128)
        or not vector.flags.c_contiguous
        or not np.all(np.isfinite(vector.real))
        or not np.all(np.isfinite(vector.imag))
    ):
        raise ValueError("dense input vector violates the q0-MSB c128 contract")
    target_tuple = tuple(targets)
    if (
        not target_tuple
        or len(target_tuple) > 2
        or any(not _is_int(q) or q < 0 or q >= num_qubits for q in target_tuple)
        or len(set(target_tuple)) != len(target_tuple)
    ):
        raise ValueError("dense gate targets are invalid")
    gate_dimension = 1 << len(target_tuple)
    _validate_matrix(matrix, dimension=gate_dimension, name="applied gate")
    remaining = tuple(q for q in range(num_qubits) if q not in target_tuple)
    permutation = target_tuple + remaining
    tensor = vector.reshape((2,) * num_qubits)
    front = np.transpose(tensor, permutation).reshape(gate_dimension, -1)
    updated = matrix @ front
    inverse = tuple(int(axis) for axis in np.argsort(permutation))
    return np.ascontiguousarray(
        np.transpose(updated.reshape((2,) * num_qubits), inverse).reshape(
            expected_shape
        ),
        dtype=np.complex128,
    )


def event_mask_row(
    *,
    namespace: str,
    seed: int,
    mask_index: int,
    width: int,
    round_index: int,
    site_index: int,
    probability_numerator: int,
) -> dict[str, Any]:
    if namespace not in {"CARRIER", "BLPENSEMBLE"}:
        raise ValueError("event-mask namespace is invalid")
    try:
        namespace_bytes = namespace.encode("ascii")
    except UnicodeEncodeError as exc:  # pragma: no cover - exact enum above
        raise ValueError("event-mask namespace must be ASCII") from exc
    fields = (
        _require_u64(seed, "seed"),
        _require_u64(mask_index, "mask_index"),
        _require_u64(width, "width"),
        _require_u64(round_index, "round_index"),
        _require_u64(site_index, "site_index"),
    )
    if round_index == 0:
        raise ValueError("physical event-mask round index is one-based")
    if not _is_int(probability_numerator) or probability_numerator not in range(5):
        raise ValueError("event probability numerator must be in 0..4")
    payload = MASK_PREFIX + namespace_bytes + b"\x00" + b"".join(
        struct.pack(">Q", value) for value in fields
    )
    digest = hashlib.sha256(payload).digest()
    h64 = struct.unpack(">Q", digest[:8])[0]
    if probability_numerator == 0:
        event = False
    elif probability_numerator == 4:
        event = True
    else:
        event = h64 < probability_numerator * (1 << 62)
    return {
        "namespace": namespace,
        "seed": seed,
        "mask_index": mask_index,
        "width": width,
        "round_index": round_index,
        "site_index": site_index,
        "probability_numerator": probability_numerator,
        "probability_denominator": 4,
        "payload_hex": payload.hex(),
        "digest_sha256": digest.hex(),
        "h64": h64,
        "event": event,
    }


def independent_round_operations(
    *,
    width: int,
    round_index: int,
    active_axes: Sequence[str],
    theta: float,
    event_bits: Sequence[bool],
) -> list[dict[str, Any]]:
    """Reconstruct the frozen physical schedule without a fixture helper."""

    if not _is_int(width) or width <= 0:
        raise ValueError("width must be a positive integer")
    if not _is_int(round_index) or round_index <= 0:
        raise ValueError("round_index must be one-based")
    axes = tuple(active_axes)
    if axes not in tuple(ACTIVE_AXES.values()):
        raise ValueError("active axes are not a registered family")
    if (
        len(event_bits) != width
        or any(not isinstance(value, bool) for value in event_bits)
    ):
        raise ValueError("event_bits must be a width-long boolean sequence")
    angle = _finite_float(theta, "theta")
    operations: list[dict[str, Any]] = []

    def append(kind: str, targets: Sequence[int], **extra: Any) -> None:
        operations.append(
            {
                "operation_index": len(operations),
                "round_index": round_index,
                "kind": kind,
                "targets": list(targets),
                **extra,
            }
        )

    for site in range(width):
        if (site + round_index) % 2 == 0:
            append("H", (site,))
    for site in range(width):
        if (site + round_index) % 2 == 1:
            append("S", (site,))
    for parity in (round_index % 2, 1 - round_index % 2):
        for site in range(width - 1):
            if site % 2 == parity:
                append("CX", (site, site + 1))
    for parity in (round_index % 2, 1 - round_index % 2):
        for site in range(width - 1):
            if site % 2 == parity:
                append("CX", (width + site + 1, width + site))
    for site, event in enumerate(event_bits):
        if event:
            for axis_index, axis in enumerate(("X", "Y", "Z")):
                if axis in axes:
                    append(
                        "PAULI_ROTATION",
                        (site, width + site),
                        axis=axis,
                        axis_index=axis_index,
                        theta_float64_hex=float(angle).hex(),
                        site_index=site,
                    )
    return operations


def _canonical_value_sha256(value: Any) -> str:
    raw = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def _validate_gate_definitions(definitions: Any) -> None:
    if not isinstance(definitions, Mapping):
        raise ValueError("fixture gate_definitions must be an object")
    _require_exact_keys(
        definitions,
        {"H", "S", "X", "Y", "Z", "CX", "PAULI_ROTATION"},
        "fixture gate_definitions",
    )
    references = {
        "H": _H,
        "S": _S,
        "X": _X,
        "Y": _Y,
        "Z": _Z,
        "CX": _CX,
    }
    bases = {
        "H": ["|0>", "|1>"],
        "S": ["|0>", "|1>"],
        "X": ["|0>", "|1>"],
        "Y": ["|0>", "|1>"],
        "Z": ["|0>", "|1>"],
        "CX": ["|00>", "|01>", "|10>", "|11>"],
    }
    for token, reference in references.items():
        row = definitions[token]
        if not isinstance(row, Mapping):
            raise ValueError(f"fixture {token} definition must be an object")
        _require_exact_keys(
            row,
            {"kind", "basis_order", "shape", "row_major_entries"},
            f"fixture {token} definition",
        )
        if (
            row["kind"] != "explicit_row_major_complex128"
            or row["basis_order"] != bases[token]
            or row["shape"] != list(reference.shape)
            or not isinstance(row["row_major_entries"], list)
            or len(row["row_major_entries"]) != reference.size
        ):
            raise ValueError(f"fixture {token} definition metadata drifted")
        values: list[complex] = []
        for entry in row["row_major_entries"]:
            if not isinstance(entry, Mapping):
                raise ValueError(f"fixture {token} entry must be an object")
            _require_exact_keys(
                entry,
                {"real_float64_hex", "imag_float64_hex"},
                f"fixture {token} matrix entry",
            )
            real_hex = entry["real_float64_hex"]
            imag_hex = entry["imag_float64_hex"]
            if not isinstance(real_hex, str) or not isinstance(imag_hex, str):
                raise ValueError(f"fixture {token} matrix hex must be strings")
            real = float.fromhex(real_hex)
            imag = float.fromhex(imag_hex)
            if real.hex() != real_hex or imag.hex() != imag_hex:
                raise ValueError(f"fixture {token} matrix hex is noncanonical")
            values.append(complex(real, imag))
        observed = np.ascontiguousarray(
            np.asarray(values, dtype=np.complex128).reshape(reference.shape)
        )
        if not np.array_equal(observed, reference):
            raise ValueError(f"fixture {token} matrix disagrees with dense definition")
    rotation = definitions["PAULI_ROTATION"]
    expected_rotation = {
        "kind": "formula",
        "formula": "cos(theta/2)*I-1j*sin(theta/2)*P",
        "theta_source": "operation.theta_float64_hex",
        "pauli_source": "operation.physical_pauli_body",
        "matrix_indices": "row_is_output_column_is_input",
    }
    if rotation != expected_rotation:
        raise ValueError("fixture PAULI_ROTATION formula drifted")


def _project_exact_path(
    path: Any,
    *,
    namespace: str,
    mask_index: int,
    seed: int,
    width: int,
    rounds: int,
    numerator: int,
    active_axes: Sequence[str],
    gamma_hex: str,
    theta_hex: str,
    weight_numerator: int,
    weight_denominator: int,
) -> dict[str, Any]:
    if not isinstance(path, Mapping):
        raise ValueError("fixture mask path must be an object")
    _require_exact_keys(
        path,
        {
            "namespace",
            "mask_index",
            "seed",
            "weight_numerator",
            "weight_denominator",
            "event_rows",
            "event_rows_sha256",
            "full_mask",
            "full_mask_sha256",
            "eligible_collision_count",
            "realized_event_count",
            "realized_event_fraction",
            "active_axis_rotation_count",
            "mask_multiplicity",
            "distinct_mask_count",
            "round_ledger",
            "shared_evolution_transcript_sha256",
        },
        "fixture mask path",
    )
    if (
        path["namespace"] != namespace
        or path["mask_index"] != mask_index
        or path["seed"] != seed
        or path["weight_numerator"] != weight_numerator
        or path["weight_denominator"] != weight_denominator
    ):
        raise ValueError("fixture mask path identity drifted")
    expected_rows: list[dict[str, Any]] = []
    expected_full_mask: list[list[bool]] = []
    internal_rows: list[dict[str, Any]] = []
    for round_index in range(1, rounds + 1):
        round_bits: list[bool] = []
        for site_index in range(width):
            internal = event_mask_row(
                namespace=namespace,
                seed=seed,
                mask_index=mask_index,
                width=width,
                round_index=round_index,
                site_index=site_index,
                probability_numerator=numerator,
            )
            expected_rows.append(
                {
                    "event_row_index": len(expected_rows),
                    "round_index": round_index,
                    "site_index": site_index,
                    "payload_hex": internal["payload_hex"],
                    "payload_sha256": internal["digest_sha256"],
                    "h64": internal["h64"],
                    "event": internal["event"],
                }
            )
            internal_rows.append(internal)
            round_bits.append(internal["event"])
        expected_full_mask.append(round_bits)
    if path["event_rows"] != expected_rows:
        raise ValueError("fixture event rows disagree with independent SHA-256 mask")
    if path["event_rows_sha256"] != _canonical_value_sha256(expected_rows):
        raise ValueError("fixture event-row hash drifted")
    if path["full_mask"] != expected_full_mask:
        raise ValueError("fixture full mask disagrees with independent mask")
    if path["full_mask_sha256"] != _canonical_value_sha256(expected_full_mask):
        raise ValueError("fixture full-mask hash drifted")
    realized = sum(int(value) for row in expected_full_mask for value in row)
    eligible = width * rounds
    if (
        path["eligible_collision_count"] != eligible
        or path["realized_event_count"] != realized
        or path["realized_event_fraction"]
        != {"numerator": realized, "denominator": eligible}
        or path["active_axis_rotation_count"] != realized * len(active_axes)
    ):
        raise ValueError("fixture mask accounting drifted")
    ledger = path["round_ledger"]
    if not isinstance(ledger, list) or len(ledger) != rounds:
        raise ValueError("fixture round ledger shape drifted")
    normalized_rounds: list[dict[str, Any]] = []
    global_operation_index = 0
    expected_collision_ordinal = 0
    for round_index, round_row in enumerate(ledger, start=1):
        if not isinstance(round_row, Mapping):
            raise ValueError("fixture round row must be an object")
        _require_exact_keys(
            round_row,
            {
                "round_index",
                "layers",
                "operations",
                "clifford_operations",
                "collision_rotations",
            },
            "fixture round row",
        )
        if round_row["round_index"] != round_index:
            raise ValueError("fixture physical rounds are not one-based and ordered")
        expected_ops = independent_round_operations(
            width=width,
            round_index=round_index,
            active_axes=active_axes,
            theta=float.fromhex(theta_hex),
            event_bits=expected_full_mask[round_index - 1],
        )
        operations = round_row["operations"]
        if not isinstance(operations, list) or len(operations) != len(expected_ops):
            raise ValueError("fixture operation count drifted")
        projected_ops: list[dict[str, Any]] = []
        for local_index, (observed, expected) in enumerate(zip(operations, expected_ops)):
            if not isinstance(observed, Mapping):
                raise ValueError("fixture operation must be an object")
            common = {
                "operation_class",
                "operation_index",
                "round_index",
                "layer_index",
                "within_layer_index",
                "gate_kind",
                "targets",
                "matrix_definition",
            }
            collision = expected["kind"] == "PAULI_ROTATION"
            extra = {
                "collision_ordinal",
                "event_row_index",
                "site_index",
                "axis",
                "axis_index",
                "physical_pauli_body",
                "gamma_float64_hex",
                "theta_float64_hex",
                "rotation_convention",
            }
            _require_exact_keys(
                observed,
                common | (extra if collision else set()),
                "fixture physical operation",
            )
            if (
                observed["operation_index"] != global_operation_index
                or observed["round_index"] != round_index
                or observed["gate_kind"] != expected["kind"]
                or observed["targets"] != expected["targets"]
                or observed["matrix_definition"] != expected["kind"]
            ):
                raise ValueError("fixture operation order/kind/targets drifted")
            if collision:
                axis = expected["axis"]
                site = expected["site_index"]
                body = ["I"] * (2 * width)
                body[site] = axis
                body[width + site] = axis
                event_row_index = (round_index - 1) * width + site
                if (
                    observed["operation_class"] != "collision_rotation"
                    or observed["collision_ordinal"] != expected_collision_ordinal
                    or observed["event_row_index"] != event_row_index
                    or observed["site_index"] != site
                    or observed["axis"] != axis
                    or observed["axis_index"] != {"X": 0, "Y": 1, "Z": 2}[axis]
                    or observed["physical_pauli_body"] != "".join(body)
                    or observed["gamma_float64_hex"] != gamma_hex
                    or observed["theta_float64_hex"] != theta_hex
                    or observed["rotation_convention"] != "exp(-0.5j*theta*P)"
                    or observed["layer_index"] != 6
                ):
                    raise ValueError("fixture collision operation drifted")
                expected_collision_ordinal += 1
            else:
                if observed["operation_class"] != "clifford":
                    raise ValueError("fixture Clifford discriminator drifted")
            projected = dict(expected)
            projected["operation_index"] = local_index
            projected_ops.append(projected)
            global_operation_index += 1
        filtered_clifford = [
            row for row in operations if row["operation_class"] == "clifford"
        ]
        filtered_collision = [
            row
            for row in operations
            if row["operation_class"] == "collision_rotation"
        ]
        if (
            round_row["clifford_operations"] != filtered_clifford
            or round_row["collision_rotations"] != filtered_collision
        ):
            raise ValueError("fixture duplicated operation views drifted")
        layers = round_row["layers"]
        first_parity = round_index % 2
        expected_layers = (
            ("system_h", (-round_index) % 2),
            ("system_s", (1 - round_index) % 2),
            (f"system_cx_parity_{first_parity}", first_parity),
            (f"system_cx_parity_{1 - first_parity}", 1 - first_parity),
            (f"memory_reverse_cx_parity_{first_parity}", first_parity),
            (f"memory_reverse_cx_parity_{1 - first_parity}", 1 - first_parity),
            ("event_conditioned_collisions", None),
        )
        if not isinstance(layers, list) or len(layers) != 7:
            raise ValueError("fixture layer count drifted")
        for layer_index, (layer, (name, parity)) in enumerate(
            zip(layers, expected_layers)
        ):
            if not isinstance(layer, Mapping):
                raise ValueError("fixture layer must be an object")
            _require_exact_keys(
                layer,
                {"layer_index", "layer_name", "parity", "operation_indices"},
                "fixture layer",
            )
            members = [
                row for row in operations if row["layer_index"] == layer_index
            ]
            if (
                layer["layer_index"] != layer_index
                or layer["layer_name"] != name
                or layer["parity"] != parity
                or layer["operation_indices"]
                != [row["operation_index"] for row in members]
                or [row["within_layer_index"] for row in members]
                != list(range(len(members)))
            ):
                raise ValueError("fixture layer membership/order drifted")
        normalized_rounds.append(
            {
                "round_index": round_index,
                "event_bits": expected_full_mask[round_index - 1],
                "operations": projected_ops,
            }
        )
    if path["shared_evolution_transcript_sha256"] != _canonical_value_sha256(ledger):
        raise ValueError("fixture evolution transcript hash drifted")
    return {
        "event_rows": internal_rows,
        "full_mask": expected_full_mask,
        "full_mask_sha256": path["full_mask_sha256"],
        "mask_multiplicity": path["mask_multiplicity"],
        "distinct_mask_count": path["distinct_mask_count"],
        "physical_rounds": normalized_rounds,
    }


def _normalized_fixture(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Independently validate the exact neutral fixture core."""

    if not isinstance(fixture, Mapping) or fixture.get("schema") != FIXTURE_SCHEMA:
        raise ValueError("wrong finite-memory fixture schema")
    _require_exact_keys(
        fixture,
        {
            "schema",
            "script_revision",
            "fixture_id",
            "run_partition",
            "case_id",
            "claim_boundary",
            "geometry",
            "coordinate_convention",
            "mask_contract",
            "state_contract",
            "gate_definitions",
            "parameters",
            "inputs",
            "checkpoints",
            "carrier_path",
            "blpensemble",
            "sdim_pullback_requests",
            "result_projection_sha256",
        },
        "fixture",
    )
    if fixture["result_projection_sha256"] != canonical_sha256(fixture):
        raise ValueError("fixture result projection hash drifted")
    if fixture["script_revision"] != "gcapeps-finite-memory-neutral-fixture-v1":
        raise ValueError("fixture script revision drifted")
    if (
        not isinstance(fixture["case_id"], str)
        or not fixture["case_id"]
        or fixture["fixture_id"] != fixture["case_id"]
    ):
        raise ValueError("fixture case identity drifted")
    run_partition = fixture["run_partition"]
    if run_partition not in {"CALIBRATION", "HELDOUT"}:
        raise ValueError("fixture run partition drifted")
    parameters = fixture["parameters"]
    if not isinstance(parameters, Mapping):
        raise ValueError("fixture parameters must be an object")
    _require_exact_keys(
        parameters,
        {
            "width",
            "rounds",
            "axis_family",
            "active_axes",
            "p_event_numerator",
            "p_event_denominator",
            "seed",
            "gamma_index",
            "gamma_label",
            "gamma_float64_hex",
            "theta_float64_hex",
            "max_bond",
        },
        "fixture parameters",
    )
    width = parameters["width"]
    rounds = parameters["rounds"]
    axis_family = parameters["axis_family"]
    numerator = parameters["p_event_numerator"]
    denominator = parameters["p_event_denominator"]
    seed = _require_u64(parameters["seed"], "seed")
    if (
        width not in (3, 5, 7)
        or not _is_int(rounds)
        or rounds <= 0
        or axis_family not in ACTIVE_AXES
        or parameters["active_axes"] != list(ACTIVE_AXES[axis_family])
        or numerator not in range(5)
        or denominator != 4
        or parameters["max_bond"] != 32
    ):
        raise ValueError("fixture scientific parameters drifted")
    gamma_grid = (
        ("pi/11", "0x1.247426bd47de3p-2"),
        ("pi/9", "0x1.657184ae74487p-2"),
        ("pi/7", "0x1.cb91f3bbba140p-2"),
        ("pi/5", "0x1.41b2f769cf0e0p-1"),
    )
    gamma_index = parameters["gamma_index"]
    if not _is_int(gamma_index) or gamma_index not in range(len(gamma_grid)):
        raise ValueError("fixture gamma index drifted")
    gamma_label, gamma_hex = gamma_grid[gamma_index]
    gamma = float.fromhex(gamma_hex)
    theta = -gamma
    theta_hex = theta.hex()
    if (
        parameters["gamma_label"] != gamma_label
        or parameters["gamma_float64_hex"] != gamma_hex
        or parameters["theta_float64_hex"] != theta_hex
    ):
        raise ValueError("fixture gamma/theta identity drifted")
    expected_geometry = {
        "rows": 2,
        "width": width,
        "n_qubits": 2 * width,
        "system_sites": list(range(width)),
        "memory_sites": list(range(width, 2 * width)),
        "site_order": [
            {
                "site_id": site,
                "row": "system" if site < width else "memory",
                "row_index": site if site < width else site - width,
            }
            for site in range(2 * width)
        ],
        "graph_edges": [
            list(edge)
            for edge in sorted(
                [(site, site + 1) for site in range(width - 1)]
                + [
                    (width + site, width + site + 1)
                    for site in range(width - 1)
                ]
                + [(site, width + site) for site in range(width)]
            )
        ],
    }
    if fixture["geometry"] != expected_geometry:
        raise ValueError("fixture geometry drifted")
    expected_coordinate = {
        "qubit_order": list(range(2 * width)),
        "system_axes": list(range(width)),
        "memory_axes": list(range(width, 2 * width)),
        "q0_bit_significance": "most_significant",
        "tensor_axis_order": "S_0..S_(w-1),M_0..M_(w-1)",
        "flat_index": "sum_q bit(q)*2**(2*w-1-q)",
        "two_qubit_basis": ["|00>", "|01>", "|10>", "|11>"],
        "matrix_indices": "row_is_output_column_is_input",
    }
    if fixture["coordinate_convention"] != expected_coordinate:
        raise ValueError("fixture q0-MSB coordinate convention drifted")
    expected_mask_contract = {
        "version": "gcapeps-finite-memory-mask-v1",
        "payload_prefix_hex": MASK_PREFIX.hex(),
        "namespace_values": ["CARRIER", "BLPENSEMBLE"],
        "integer_encoding": "unsigned_u64_big_endian",
        "payload_field_order": [
            "prefix", "namespace_ascii", "namespace_nul", "seed",
            "mask_index", "width", "round", "site",
        ],
        "digest": "SHA256",
        "h64": "uint64_big_endian(digest[0:8])",
        "p_event_denominator": 4,
        "event_rule": (
            "q=0 structural_false; q=4 structural_true; "
            "otherwise h64 < q*2**62"
        ),
        "round_horizon_in_payload": False,
        "p_event_in_payload": False,
        "carrier_mask_index": 0,
        "blpensemble_mask_indices": list(range(32)),
        "blpensemble_equal_weight": {"numerator": 1, "denominator": 32},
    }
    if fixture["mask_contract"] != expected_mask_contract:
        raise ValueError("fixture event-mask contract drifted")
    expected_state_contract = {
        "initial_state_kind": "computational_basis_product",
        "joint_state_retained_across_rounds": True,
        "memory_row_policy": "never_discard_reset_or_recreate",
        "candidate_restart_between_rounds": False,
        "physical_round_indexing": "one_based",
        "checkpoint_zero": "initial_state_only",
        "unconditional_cross_row_gate": False,
    }
    if fixture["state_contract"] != expected_state_contract:
        raise ValueError("fixture persistent joint-state contract drifted")
    _validate_gate_definitions(fixture["gate_definitions"])
    inputs = fixture["inputs"]
    if not isinstance(inputs, list) or len(inputs) != 2:
        raise ValueError("fixture inputs drifted")
    input_hashes: dict[int, str] = {}
    central = width // 2
    for expected_input_id, row in enumerate(inputs, start=1):
        if not isinstance(row, Mapping):
            raise ValueError("fixture input must be an object")
        _require_exact_keys(
            row,
            {
                "input_id",
                "label",
                "central_system_site",
                "dense_plain_initial_bits",
                "gc_residual_initial_bits",
                "gc_frame_preparation_gates",
                "preparation_is_physical_round_gate",
                "input_preparation_transcript",
                "input_preparation_transcript_sha256",
            },
            "fixture input",
        )
        gates = [] if expected_input_id == 1 else [
            {
                "operation_index": 0,
                "gate_kind": "X",
                "targets": [central],
                "matrix_definition": "X",
                "is_physical_round_gate": False,
            }
        ]
        bits = [0] * (2 * width)
        if expected_input_id == 2:
            bits[central] = 1
        transcript = {
            "schema": "gcapeps-finite-memory-input-preparation.v1",
            "input_id": expected_input_id,
            "gates": gates,
        }
        if (
            row["input_id"] != expected_input_id
            or row["label"]
            != ("all_zero" if expected_input_id == 1 else "central_system_x")
            or row["central_system_site"] != central
            or row["dense_plain_initial_bits"] != bits
            or row["gc_residual_initial_bits"] != [0] * (2 * width)
            or row["gc_frame_preparation_gates"] != gates
            or row["preparation_is_physical_round_gate"] is not False
            or row["input_preparation_transcript"] != transcript
            or row["input_preparation_transcript_sha256"]
            != _canonical_value_sha256(transcript)
        ):
            raise ValueError("fixture input preparation drifted")
        input_hashes[expected_input_id] = row[
            "input_preparation_transcript_sha256"
        ]
    expected_checkpoints = sorted({0, 1, 2, 4, rounds}.intersection(range(rounds + 1)))
    if fixture["checkpoints"] != expected_checkpoints:
        raise ValueError("fixture candidate checkpoint list drifted")
    carrier = _project_exact_path(
        fixture["carrier_path"],
        namespace="CARRIER",
        mask_index=0,
        seed=seed,
        width=width,
        rounds=rounds,
        numerator=numerator,
        active_axes=ACTIVE_AXES[axis_family],
        gamma_hex=gamma_hex,
        theta_hex=theta_hex,
        weight_numerator=1,
        weight_denominator=1,
    )
    if carrier["mask_multiplicity"] != 1 or carrier["distinct_mask_count"] != 1:
        raise ValueError("fixture CARRIER multiplicity drifted")
    ensemble_block = fixture["blpensemble"]
    if not isinstance(ensemble_block, Mapping):
        raise ValueError("fixture BLPENSEMBLE block must be an object")
    _require_exact_keys(
        ensemble_block,
        {
            "enabled",
            "registered_path_count",
            "path_count",
            "weight_numerator",
            "weight_denominator",
            "distinct_mask_count",
            "paths",
        },
        "fixture BLPENSEMBLE block",
    )
    enabled = ensemble_block["enabled"]
    if not isinstance(enabled, bool) or (run_partition == "CALIBRATION" and enabled):
        raise ValueError("fixture BLPENSEMBLE partition rule drifted")
    expected_count = 32 if enabled else 0
    if (
        ensemble_block["registered_path_count"] != 32
        or ensemble_block["path_count"] != expected_count
        or ensemble_block["weight_numerator"] != 1
        or ensemble_block["weight_denominator"] != 32
        or not isinstance(ensemble_block["paths"], list)
        or len(ensemble_block["paths"]) != expected_count
    ):
        raise ValueError("fixture BLPENSEMBLE accounting drifted")
    paths_by_key: dict[tuple[str, int], dict[str, Any]] = {
        ("CARRIER", 0): carrier
    }
    ensemble_paths: list[dict[str, Any]] = []
    for mask_index, path in enumerate(ensemble_block["paths"]):
        projected = _project_exact_path(
            path,
            namespace="BLPENSEMBLE",
            mask_index=mask_index,
            seed=seed,
            width=width,
            rounds=rounds,
            numerator=numerator,
            active_axes=ACTIVE_AXES[axis_family],
            gamma_hex=gamma_hex,
            theta_hex=theta_hex,
            weight_numerator=1,
            weight_denominator=32,
        )
        ensemble_paths.append(projected)
        paths_by_key[("BLPENSEMBLE", mask_index)] = projected
    counts: dict[str, int] = {}
    for path in ensemble_paths:
        digest = path["full_mask_sha256"]
        counts[digest] = counts.get(digest, 0) + 1
    distinct = len(counts)
    if ensemble_block["distinct_mask_count"] != distinct:
        raise ValueError("fixture ensemble distinct-mask count drifted")
    for path in ensemble_paths:
        if (
            path["mask_multiplicity"] != counts[path["full_mask_sha256"]]
            or path["distinct_mask_count"] != distinct
        ):
            raise ValueError("fixture ensemble mask multiplicity drifted")
    pullback_keys = (
        "run_partition",
        "case_id",
        "input_id",
        "input_preparation_transcript_sha256",
        "shared_evolution_transcript_sha256",
        "round_prefix",
        "collision_ordinal",
        "round_index",
        "site_index",
        "axis_index",
        "physical_pauli_body",
    )
    expected_requests: list[dict[str, Any]] = []
    carrier_raw = fixture["carrier_path"]
    for input_id in (1, 2):
        for round_row in carrier_raw["round_ledger"]:
            for rotation in round_row["collision_rotations"]:
                expected_requests.append(
                    {
                        "run_partition": run_partition,
                        "case_id": fixture["case_id"],
                        "input_id": input_id,
                        "input_preparation_transcript_sha256": input_hashes[input_id],
                        "shared_evolution_transcript_sha256": carrier_raw[
                            "shared_evolution_transcript_sha256"
                        ],
                        "round_prefix": rotation["round_index"],
                        "collision_ordinal": rotation["collision_ordinal"],
                        "round_index": rotation["round_index"],
                        "site_index": rotation["site_index"],
                        "axis_index": rotation["axis_index"],
                        "physical_pauli_body": rotation["physical_pauli_body"],
                    }
                )
    expected_requests.sort(
        key=lambda row: tuple(row[key] for key in pullback_keys)
    )
    if fixture["sdim_pullback_requests"] != expected_requests:
        raise ValueError("fixture SDIM pullback request sequence drifted")
    return {
        "run_partition": run_partition,
        "case_id": fixture["case_id"],
        "width": width,
        "rounds": rounds,
        "axis_family": axis_family,
        "active_axes": ACTIVE_AXES[axis_family],
        "p_event_numerator": numerator,
        "p_event_denominator": denominator,
        "run_blpensemble": enabled,
        "gamma": gamma,
        "gamma_float64_hex": gamma_hex,
        "theta": theta,
        "theta_float64_hex": theta_hex,
        "seed": seed,
        "physical_rounds": carrier["physical_rounds"],
        "carrier_mask_rows": carrier["event_rows"],
        "paths_by_key": paths_by_key,
        "fixture_projection_sha256": fixture["result_projection_sha256"],
    }
def _operation_matrix(operation: Mapping[str, Any]) -> np.ndarray:
    kind = operation["kind"]
    if kind in {"H", "S"}:
        return one_qubit_matrix(kind)
    if kind == "CX":
        return cx_matrix()
    if kind == "PAULI_ROTATION":
        angle_hex = operation.get("theta_float64_hex")
        if not isinstance(angle_hex, str):
            raise ValueError("rotation operation is missing theta_float64_hex")
        angle = float.fromhex(angle_hex)
        if angle.hex() != angle_hex:
            raise ValueError("rotation operation angle is not canonical")
        return pauli_rotation_matrix(str(operation.get("axis")), angle)
    raise ValueError(f"unsupported dense physical operation: {kind!r}")


def _initial_state(width: int, input_id: int) -> np.ndarray:
    if input_id not in (1, 2):
        raise ValueError("dense input_id must be 1 or 2")
    num_qubits = 2 * width
    state = np.zeros(1 << num_qubits, dtype=np.complex128)
    index = 0
    if input_id == 2:
        central = width // 2
        index = 1 << (num_qubits - 1 - central)
    state[index] = np.complex128(1.0 + 0.0j)
    return np.ascontiguousarray(state)


def root_array(array: np.ndarray) -> np.ndarray:
    """Return the unique owning NumPy root for logical byte accounting."""

    if not isinstance(array, np.ndarray):
        raise TypeError("dense logical-memory values must be NumPy arrays")
    root = array
    seen: set[int] = set()
    while isinstance(root.base, np.ndarray):
        key = id(root)
        if key in seen:
            raise ValueError("NumPy base cycle")
        seen.add(key)
        root = root.base
    return root


@dataclass
class _ArrayLedger:
    """Sample live dense-reference arrays by unique root-buffer identity.

    The dense oracle has one array category, so aliases inside that category
    are deduplicated.  Candidate logical-memory helpers are intentionally not
    imported: this implementation is part of the independent-reference
    firewall.
    """

    maximum: int = 0
    _retained_roots: dict[int, np.ndarray] = field(default_factory=dict)
    _sample_labels: list[str] = field(default_factory=list)

    @property
    def current(self) -> int:
        return sum(int(root.nbytes) for root in self._retained_roots.values())

    @property
    def sample_labels(self) -> tuple[str, ...]:
        return tuple(self._sample_labels)

    @staticmethod
    def _insert_root(
        roots: dict[int, np.ndarray],
        array: np.ndarray,
    ) -> None:
        root = root_array(array)
        key = id(root)
        previous = roots.get(key)
        if previous is not None and previous is not root:
            raise ValueError("NumPy root identity collision")
        roots[key] = root

    def _sample(self, label: str, arrays: Iterable[np.ndarray]) -> int:
        if not isinstance(label, str) or not label:
            raise ValueError("dense logical-memory sample label must be nonempty")
        roots = dict(self._retained_roots)
        for array in arrays:
            self._insert_root(roots, array)
        total = sum(int(root.nbytes) for root in roots.values())
        self.maximum = max(self.maximum, total)
        self._sample_labels.append(label)
        return total

    def sample_materialized(
        self,
        label: str,
        *arrays: np.ndarray,
    ) -> int:
        """Sample immediately after the named arrays materialize."""

        return self._sample(label, arrays)

    def sample_pre_release(
        self,
        label: str,
        *arrays: np.ndarray,
    ) -> int:
        """Sample all arrays that coexist immediately before release."""

        return self._sample(label, arrays)

    def retain(
        self,
        array: np.ndarray,
        *,
        label: str,
        coexisting_arrays: Iterable[np.ndarray] = (),
    ) -> np.ndarray:
        """Transfer one result array into persistent dense-result ownership."""

        if not isinstance(array, np.ndarray):
            raise TypeError("retained dense logical-memory value must be an array")
        coexist = tuple(coexisting_arrays)
        source = array
        if array.base is not None or not array.flags.c_contiguous:
            array = np.ascontiguousarray(array).copy(order="C")
        self.sample_materialized(
            f"{label}.materialized",
            *coexist,
            source,
            array,
        )
        self._insert_root(self._retained_roots, array)
        self._sample(f"{label}.retained", coexist)
        return array


def validate_raw_vector(vector: np.ndarray, *, width: int) -> dict[str, Any]:
    expected = (1 << (2 * width),)
    if not isinstance(vector, np.ndarray):
        raise ValueError("raw vector must be a NumPy ndarray")
    if vector.shape != expected:
        raise ValueError("raw vector has the wrong shape")
    if vector.dtype != np.dtype(np.complex128):
        raise ValueError("raw vector must have exact complex128 dtype")
    if not vector.flags.c_contiguous:
        raise ValueError("raw vector must be C contiguous")
    if not np.all(np.isfinite(vector.real)) or not np.all(np.isfinite(vector.imag)):
        raise ValueError("raw vector contains a nonfinite component")
    z = np.vdot(vector, vector)
    z_complex = complex(z)
    imag_abs = abs(z_complex.imag)
    real = z_complex.real
    if not math.isfinite(imag_abs) or imag_abs > NUMERICAL_ZERO:
        raise ValueError("raw vector has excessive vdot imaginary residual")
    if not math.isfinite(real) or real <= 0.0:
        raise ValueError("raw vector norm must be finite and positive")
    raw = vector.tobytes(order="C")
    return {
        "vector_data_sha256": hashlib.sha256(raw).hexdigest(),
        "norm_squared_real": real,
        "norm_squared_imaginary_abs": imag_abs,
        "norm": math.sqrt(real),
        "stored_vector_normalized_before_metric": False,
        "metric_local_normalized_copy": True,
        "phase_fit": False,
        "coordinate_permutation": False,
        "dtype_cast": False,
    }


def validate_reduced_state(
    rho: np.ndarray,
    *,
    ledger: _ArrayLedger | None = None,
    coexisting_arrays: Iterable[np.ndarray] = (),
) -> dict[str, Any]:
    """Apply the frozen Hermiticity, trace, PSD, and eigensystem guards."""

    if (
        not isinstance(rho, np.ndarray)
        or rho.ndim != 2
        or rho.shape[0] != rho.shape[1]
        or rho.dtype != np.dtype(np.complex128)
        or not rho.flags.c_contiguous
        or not np.all(np.isfinite(rho.real))
        or not np.all(np.isfinite(rho.imag))
    ):
        raise ValueError("reduced state violates the finite square c128 contract")
    coexist = tuple(coexisting_arrays)
    if ledger is not None:
        ledger.sample_materialized(
            "reduced_state.input.materialized", *coexist, rho
        )
    hermiticity = float(np.max(np.abs(rho - rho.conj().T)))
    trace_residual = float(abs(np.trace(rho) - 1.0))
    if (
        not math.isfinite(hermiticity)
        or not math.isfinite(trace_residual)
        or hermiticity > NUMERICAL_ZERO
        or trace_residual > NUMERICAL_ZERO
    ):
        raise ValueError("reduced state failed Hermiticity/trace gates")
    rho_h = np.ascontiguousarray((rho + rho.conj().T) / 2.0)
    if ledger is not None:
        ledger.sample_materialized(
            "reduced_state.hermitian.materialized", *coexist, rho, rho_h
        )
    eigenvalues, eigenvectors = np.linalg.eigh(rho_h)
    eigenvalues = np.ascontiguousarray(eigenvalues, dtype=np.float64)
    eigenvectors = np.ascontiguousarray(eigenvectors, dtype=np.complex128)
    if ledger is not None:
        ledger.sample_materialized(
            "reduced_state.eigensystem.materialized",
            *coexist,
            rho,
            rho_h,
            eigenvalues,
            eigenvectors,
        )
    eigenpair = float(
        np.max(
            np.abs(
                rho_h @ eigenvectors
                - eigenvectors * eigenvalues[np.newaxis, :]
            )
        )
    )
    reconstruction = float(
        np.max(
            np.abs(
                rho_h
                - (eigenvectors * eigenvalues[np.newaxis, :])
                @ eigenvectors.conj().T
            )
        )
    )
    minimum = float(np.min(eigenvalues))
    if (
        minimum < -NUMERICAL_ZERO
        or not math.isfinite(eigenpair)
        or not math.isfinite(reconstruction)
        or eigenpair > EIGEN_RECONSTRUCTION_TOLERANCE
        or reconstruction > EIGEN_RECONSTRUCTION_TOLERANCE
    ):
        raise ValueError("reduced state failed eigen reconstruction gates")
    negative_mass = float(np.maximum(-eigenvalues, 0.0).sum())
    if not math.isfinite(negative_mass) or negative_mass > NUMERICAL_ZERO:
        raise ValueError("reduced state has excessive negative eigenvalue mass")
    clipped = np.ascontiguousarray(np.maximum(eigenvalues, 0.0), dtype=np.float64)
    if ledger is not None:
        ledger.sample_materialized(
            "reduced_state.clipped_eigenvalues.materialized",
            *coexist,
            rho,
            rho_h,
            eigenvalues,
            eigenvectors,
            clipped,
        )
    clipped_sum = float(clipped.sum())
    if not math.isfinite(clipped_sum) or clipped_sum <= 0.0:
        raise ValueError("reduced eigenvalue mass is not positive")
    normalized = np.ascontiguousarray(clipped / clipped_sum, dtype=np.float64)
    if ledger is not None:
        ledger.sample_materialized(
            "reduced_state.normalized_eigenvalues.materialized",
            *coexist,
            rho,
            rho_h,
            eigenvalues,
            eigenvectors,
            clipped,
            normalized,
        )
    positive = normalized[normalized > 0.0]
    if ledger is not None:
        ledger.sample_materialized(
            "reduced_state.positive_eigenvalues.materialized",
            *coexist,
            rho,
            rho_h,
            eigenvalues,
            eigenvectors,
            clipped,
            normalized,
            positive,
        )
    entropy_1 = float(-np.sum(positive * np.log2(positive)))
    purity = float(np.sum(normalized * normalized))
    if not math.isfinite(purity) or purity <= 0.0:
        raise ValueError("reduced purity is invalid")
    entropy_2 = float(-math.log2(purity))
    if ledger is not None:
        ledger.sample_pre_release(
            "reduced_state.positive_eigenvalues.pre_release",
            *coexist,
            rho,
            rho_h,
            eigenvalues,
            eigenvectors,
            clipped,
            normalized,
            positive,
        )
    del positive
    return {
        "hermiticity_residual": hermiticity,
        "trace_residual": trace_residual,
        "hermitization_correction": hermiticity / 2.0,
        "metric_local_hermitian_state": rho_h,
        "raw_eigenvalues": eigenvalues,
        "eigenvectors": eigenvectors,
        "minimum_raw_eigenvalue": minimum,
        "negative_eigenvalue_mass": negative_mass,
        "eigenpair_residual": eigenpair,
        "reconstruction_residual": reconstruction,
        "clipped_eigenvalues": clipped,
        "clipped_eigenvalue_sum": clipped_sum,
        "eigenvalue_renormalization_factor": 1.0 / clipped_sum,
        "normalized_eigenvalues": normalized,
        "entropy_s1": entropy_1,
        "entropy_s2": entropy_2,
    }


def reduced_state_diagnostics(
    vector: np.ndarray,
    *,
    width: int,
    ledger: _ArrayLedger | None = None,
    coexisting_arrays: Iterable[np.ndarray] = (),
) -> dict[str, Any]:
    raw_guard = validate_raw_vector(vector, width=width)
    coexist = tuple(coexisting_arrays)
    dimension = 1 << width
    amplitude = vector.reshape(dimension, dimension)
    if ledger is not None:
        ledger.sample_materialized(
            "reduced_state.amplitude_view.materialized",
            *coexist,
            vector,
            amplitude,
        )
    rho = np.ascontiguousarray(
        amplitude @ amplitude.conj().T / raw_guard["norm_squared_real"],
        dtype=np.complex128,
    )
    if ledger is not None:
        ledger.sample_materialized(
            "reduced_state.rho.materialized", *coexist, amplitude, rho
        )
    validation = validate_reduced_state(
        rho,
        ledger=ledger,
        coexisting_arrays=(*coexist, amplitude),
    )
    schmidt = np.ascontiguousarray(
        np.linalg.svd(amplitude, compute_uv=False) / raw_guard["norm"],
        dtype=np.float64,
    )
    largest = float(schmidt[0])
    numerical_rank = int(np.count_nonzero(schmidt > NUMERICAL_ZERO * largest))
    validation_arrays = tuple(
        value for value in validation.values() if isinstance(value, np.ndarray)
    )
    if ledger is not None:
        ledger.sample_materialized(
            "reduced_state.schmidt.materialized",
            *coexist,
            amplitude,
            rho,
            *validation_arrays,
            schmidt,
        )
        ledger.sample_pre_release(
            "reduced_state.validation_auxiliaries.pre_release",
            *coexist,
            amplitude,
            rho,
            *validation_arrays,
            schmidt,
        )
    validation.pop("metric_local_hermitian_state")
    validation.pop("eigenvectors")
    validation.pop("clipped_eigenvalues")
    del validation_arrays
    if ledger is not None:
        ledger.sample_pre_release(
            "reduced_state.amplitude_view.pre_release",
            *coexist,
            amplitude,
            rho,
            validation["raw_eigenvalues"],
            validation["normalized_eigenvalues"],
            schmidt,
        )
    return {
        "raw_vector_guard": raw_guard,
        "reduced_state": rho,
        **validation,
        "normalized_schmidt_values": schmidt,
        "numerical_schmidt_rank": numerical_rank,
    }


def trace_distance(
    rho_1: np.ndarray,
    rho_2: np.ndarray,
    *,
    ledger: _ArrayLedger | None = None,
) -> dict[str, Any]:
    if (
        not isinstance(rho_1, np.ndarray)
        or not isinstance(rho_2, np.ndarray)
        or rho_1.shape != rho_2.shape
        or rho_1.ndim != 2
        or rho_1.shape[0] != rho_1.shape[1]
        or rho_1.dtype != np.dtype(np.complex128)
        or rho_2.dtype != np.dtype(np.complex128)
    ):
        raise ValueError("trace-distance states violate the c128 square contract")
    difference = np.ascontiguousarray(
        ((rho_1 + rho_1.conj().T) - (rho_2 + rho_2.conj().T)) / 2.0,
        dtype=np.complex128,
    )
    if ledger is not None:
        ledger.sample_materialized(
            "comparison.difference.materialized", rho_1, rho_2, difference
        )
    eigenvalues = np.ascontiguousarray(
        np.linalg.eigvalsh(difference), dtype=np.float64
    )
    if ledger is not None:
        ledger.sample_materialized(
            "comparison.eigensystem.materialized",
            rho_1,
            rho_2,
            difference,
            eigenvalues,
        )
    if not np.all(np.isfinite(eigenvalues)):
        raise ValueError("trace-distance spectrum is nonfinite")
    value = float(0.5 * np.sum(np.abs(eigenvalues)))
    if not math.isfinite(value):
        raise ValueError("trace distance is nonfinite")
    if ledger is not None:
        ledger.sample_pre_release(
            "comparison.difference.pre_release",
            rho_1,
            rho_2,
            difference,
            eigenvalues,
        )
    del difference
    return {"value": value, "difference_eigenvalues": eigenvalues}


def _blp_summary(distances: Sequence[float], *, ensemble: bool) -> dict[str, Any]:
    if len(distances) < 2 or any(not math.isfinite(value) for value in distances):
        raise ValueError("BLP distance sequence is invalid")
    if abs(distances[0] - 1.0) > NUMERICAL_ZERO:
        raise ValueError("initial BLP trace distance must equal one")
    increments = [
        float(distances[index] - distances[index - 1])
        for index in range(1, len(distances))
    ]
    positive_sum = float(math.fsum(max(0.0, value) for value in increments))
    maximum = max(increments)
    witnessed = maximum > BLP_INCREMENT_TOLERANCE
    if ensemble:
        verdict = (
            "BLP_WITNESSED_FINITE_32_MASK_ENSEMBLE"
            if witnessed
            else "NO_WITNESS_FINITE_32_MASK_ENSEMBLE_FOR_REGISTERED_PAIR"
        )
        object_name = "finite_32_mask_ensemble"
    else:
        verdict = (
            "BLP_WITNESSED_FIXED_MASK"
            if witnessed
            else "NO_WITNESS_FIXED_MASK_FOR_REGISTERED_PAIR"
        )
        object_name = "fixed_carrier_mask"
    return {
        "object": object_name,
        "trace_distances": list(distances),
        "increments": increments,
        "summed_positive_increments": positive_sum,
        "maximum_increment": maximum,
        "witness_threshold": BLP_INCREMENT_TOLERANCE,
        "verdict": verdict,
    }


def _checkpoint(
    state: np.ndarray,
    *,
    width: int,
    round_index: int,
    ledger: _ArrayLedger,
) -> dict[str, Any]:
    vector = np.ascontiguousarray(state).copy(order="C")
    ledger.sample_materialized(
        "checkpoint.vector.materialized", state, vector
    )
    vector = ledger.retain(
        vector,
        label="checkpoint.vector",
        coexisting_arrays=(state,),
    )
    reduced = reduced_state_diagnostics(
        vector,
        width=width,
        ledger=ledger,
        coexisting_arrays=(state,),
    )
    checkpoint_arrays = (
        state,
        vector,
        reduced["reduced_state"],
        reduced["raw_eigenvalues"],
        reduced["normalized_eigenvalues"],
        reduced["normalized_schmidt_values"],
    )
    reduced["reduced_state"] = ledger.retain(
        reduced["reduced_state"],
        label="checkpoint.reduced_state",
        coexisting_arrays=checkpoint_arrays,
    )
    reduced["raw_eigenvalues"] = ledger.retain(
        reduced["raw_eigenvalues"],
        label="checkpoint.raw_eigenvalues",
        coexisting_arrays=checkpoint_arrays,
    )
    reduced["normalized_eigenvalues"] = ledger.retain(
        reduced["normalized_eigenvalues"],
        label="checkpoint.normalized_eigenvalues",
        coexisting_arrays=checkpoint_arrays,
    )
    reduced["normalized_schmidt_values"] = ledger.retain(
        reduced["normalized_schmidt_values"],
        label="checkpoint.normalized_schmidt_values",
        coexisting_arrays=checkpoint_arrays,
    )
    return {
        "round_index": round_index,
        "vector": vector,
        **reduced,
    }


def _evolve_path(
    *,
    normalized: Mapping[str, Any],
    input_id: int,
    namespace: str,
    mask_index: int,
    ledger: _ArrayLedger,
) -> dict[str, Any]:
    width = int(normalized["width"])
    rounds = int(normalized["rounds"])
    state = _initial_state(width, input_id)
    ledger.sample_materialized("state.initial.materialized", state)
    path_key = (namespace, mask_index)
    paths_by_key = normalized["paths_by_key"]
    if path_key not in paths_by_key:
        raise ValueError("requested dense mask path is absent from the fixture")
    registered_path = paths_by_key[path_key]
    checkpoints = [
        _checkpoint(state, width=width, round_index=0, ledger=ledger)
    ]
    mask_rows: list[dict[str, Any]] = []
    operation_count = 0
    active_rotation_count = 0
    for round_index in range(1, rounds + 1):
        rows = [
            event_mask_row(
                namespace=namespace,
                seed=int(normalized["seed"]),
                mask_index=mask_index,
                width=width,
                round_index=round_index,
                site_index=site,
                probability_numerator=int(normalized["p_event_numerator"]),
            )
            for site in range(width)
        ]
        event_bits = [row["event"] for row in rows]
        operations = independent_round_operations(
            width=width,
            round_index=round_index,
            active_axes=normalized["active_axes"],
            theta=float(normalized["theta"]),
            event_bits=event_bits,
        )
        expected = registered_path["physical_rounds"][round_index - 1]
        if expected["event_bits"] != event_bits or expected["operations"] != operations:
            raise ValueError("dense path drifted from validated explicit fixture schedule")
        operations = expected["operations"]
        for operation in operations:
            predecessor = state
            candidate = apply_gate_q0_msb(
                predecessor,
                _operation_matrix(operation),
                operation["targets"],
                num_qubits=2 * width,
            )
            ledger.sample_materialized(
                "state.operation.materialized", predecessor, candidate
            )
            ledger.sample_pre_release(
                "state.operation.predecessor.pre_release",
                predecessor,
                candidate,
            )
            state = candidate
            del predecessor, candidate
            operation_count += 1
            if operation["kind"] == "PAULI_ROTATION":
                active_rotation_count += 1
        checkpoints.append(
            _checkpoint(
                state,
                width=width,
                round_index=round_index,
                ledger=ledger,
            )
        )
        mask_rows.extend(rows)
    result = {
        "namespace": namespace,
        "mask_index": mask_index,
        "input_id": input_id,
        "preparation": (
            "all_zero_product"
            if input_id == 1
            else f"central_system_X_q{width // 2}"
        ),
        "persistent_memory_across_rounds": True,
        "checkpoints": checkpoints,
        "mask_rows": mask_rows,
        "event_bits": [row["event"] for row in mask_rows],
        "eligible_collision_count": width * rounds,
        "realized_event_count": sum(row["event"] for row in mask_rows),
        "active_axis_rotation_count": active_rotation_count,
        "physical_operation_count": operation_count,
    }
    ledger.sample_pre_release("state.path.pre_release", state)
    del state
    return result


def _fixed_pair(
    *,
    normalized: Mapping[str, Any],
    ledger: _ArrayLedger,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paths = [
        _evolve_path(
            normalized=normalized,
            input_id=input_id,
            namespace="CARRIER",
            mask_index=0,
            ledger=ledger,
        )
        for input_id in (1, 2)
    ]
    distances: list[float] = []
    spectra: list[np.ndarray] = []
    for left, right in zip(paths[0]["checkpoints"], paths[1]["checkpoints"]):
        metric = trace_distance(
            left["reduced_state"], right["reduced_state"], ledger=ledger
        )
        spectrum = ledger.retain(
            metric["difference_eigenvalues"],
            label="fixed_pair.difference_eigenvalues",
            coexisting_arrays=(
                left["reduced_state"],
                right["reduced_state"],
            ),
        )
        spectra.append(spectrum)
        distances.append(metric["value"])
    summary = _blp_summary(distances, ensemble=False)
    summary["difference_eigenvalues_by_round"] = spectra
    return paths, summary


def _materialize_ensemble_average(
    components: Sequence[np.ndarray],
    *,
    ledger: _ArrayLedger,
) -> np.ndarray:
    if len(components) != 32:
        raise ValueError("finite ensemble average requires exactly 32 states")
    first = components[0]
    if any(
        not isinstance(component, np.ndarray)
        or component.shape != first.shape
        or component.dtype != np.dtype(np.complex128)
        or not component.flags.c_contiguous
        for component in components
    ):
        raise ValueError("finite ensemble components violate the c128 contract")
    accumulator = np.zeros_like(first)
    ledger.sample_materialized(
        "ensemble.accumulator.materialized", *components, accumulator
    )
    for component in components:
        predecessor = accumulator
        candidate = np.ascontiguousarray(
            predecessor + component, dtype=np.complex128
        )
        ledger.sample_materialized(
            "ensemble.accumulator_update.materialized",
            *components,
            predecessor,
            candidate,
        )
        ledger.sample_pre_release(
            "ensemble.accumulator.pre_release",
            *components,
            predecessor,
            candidate,
        )
        accumulator = candidate
        del predecessor, candidate
    average = np.ascontiguousarray(accumulator / 32.0, dtype=np.complex128)
    ledger.sample_materialized(
        "ensemble.average.materialized", *components, accumulator, average
    )
    ledger.sample_pre_release(
        "ensemble.accumulator.pre_release",
        *components,
        accumulator,
        average,
    )
    del accumulator
    return average


def _validate_ensemble_average(
    average: np.ndarray,
    *,
    ledger: _ArrayLedger,
) -> None:
    hermiticity = float(np.max(np.abs(average - average.conj().T)))
    trace_residual = float(abs(np.trace(average) - 1.0))
    hermitian = np.ascontiguousarray((average + average.conj().T) / 2.0)
    ledger.sample_materialized(
        "ensemble.hermitian.materialized", average, hermitian
    )
    eigenvalues, eigenvectors = np.linalg.eigh(hermitian)
    eigenvalues = np.ascontiguousarray(eigenvalues, dtype=np.float64)
    eigenvectors = np.ascontiguousarray(eigenvectors, dtype=np.complex128)
    ledger.sample_materialized(
        "ensemble.eigensystem.materialized",
        average,
        hermitian,
        eigenvalues,
        eigenvectors,
    )
    reconstruction = float(
        np.max(
            np.abs(
                average
                - (eigenvectors * eigenvalues[np.newaxis, :])
                @ eigenvectors.conj().T
            )
        )
    )
    if (
        hermiticity > NUMERICAL_ZERO
        or trace_residual > NUMERICAL_ZERO
        or float(np.min(eigenvalues)) < -NUMERICAL_ZERO
        or reconstruction > EIGEN_RECONSTRUCTION_TOLERANCE
    ):
        raise ValueError("finite-ensemble average state failed guards")
    ledger.sample_pre_release(
        "ensemble.average_validation.pre_release",
        average,
        hermitian,
        eigenvalues,
        eigenvectors,
    )
    del hermitian, eigenvalues, eigenvectors


def _ensemble(
    *,
    normalized: Mapping[str, Any],
    ledger: _ArrayLedger,
) -> dict[str, Any]:
    paths: list[dict[str, Any]] = []
    for mask_index in range(32):
        for input_id in (1, 2):
            paths.append(
                _evolve_path(
                    normalized=normalized,
                    input_id=input_id,
                    namespace="BLPENSEMBLE",
                    mask_index=mask_index,
                    ledger=ledger,
                )
            )
    by_key = {
        (path["mask_index"], path["input_id"]): path
        for path in paths
    }
    averages: dict[int, list[np.ndarray]] = {1: [], 2: []}
    for input_id in (1, 2):
        for round_index in range(int(normalized["rounds"]) + 1):
            components = [
                by_key[(mask_index, input_id)]["checkpoints"][round_index][
                    "reduced_state"
                ]
                for mask_index in range(32)
            ]
            average = _materialize_ensemble_average(
                components, ledger=ledger
            )
            _validate_ensemble_average(average, ledger=ledger)
            averages[input_id].append(
                ledger.retain(
                    average,
                    label="ensemble.average_reduced_state",
                    coexisting_arrays=components,
                )
            )
    distances: list[float] = []
    spectra: list[np.ndarray] = []
    for left, right in zip(averages[1], averages[2]):
        metric = trace_distance(left, right, ledger=ledger)
        distances.append(metric["value"])
        spectra.append(
            ledger.retain(
                metric["difference_eigenvalues"],
                label="ensemble.difference_eigenvalues",
                coexisting_arrays=(left, right),
            )
        )
    summary = _blp_summary(distances, ensemble=True)
    summary["difference_eigenvalues_by_round"] = spectra
    return {
        "weights": [1.0 / 32.0] * 32,
        "paths": paths,
        "average_reduced_states": {
            "input_1": averages[1],
            "input_2": averages[2],
        },
        "blp": summary,
        "aggregation_order": "average_density_matrices_before_trace_distance",
        "path_deduplication": False,
    }


def _negative_control(
    *,
    normalized: Mapping[str, Any],
    fixed_paths: Sequence[Mapping[str, Any]],
    fixed_blp: Mapping[str, Any],
    ensemble: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if normalized["p_event_numerator"] != 0:
        return None
    every_event_false = all(
        not value for path in fixed_paths for value in path["event_bits"]
    )
    active_rotations = sum(
        int(path["active_axis_rotation_count"]) for path in fixed_paths
    )
    entropies = [
        (checkpoint["entropy_s1"], checkpoint["entropy_s2"])
        for path in fixed_paths
        for checkpoint in path["checkpoints"]
    ]
    fixed_unit = all(
        abs(value - 1.0) <= NUMERICAL_ZERO
        for value in fixed_blp["trace_distances"]
    )
    ensemble_unit = True
    ensemble_increment = True
    if ensemble is not None:
        every_event_false = every_event_false and all(
            not value
            for path in ensemble["paths"]
            for value in path["event_bits"]
        )
        active_rotations += sum(
            int(path["active_axis_rotation_count"]) for path in ensemble["paths"]
        )
        entropies.extend(
            (checkpoint["entropy_s1"], checkpoint["entropy_s2"])
            for path in ensemble["paths"]
            for checkpoint in path["checkpoints"]
        )
        ensemble_unit = all(
            abs(value - 1.0) <= NUMERICAL_ZERO
            for value in ensemble["blp"]["trace_distances"]
        )
        ensemble_increment = (
            ensemble["blp"]["maximum_increment"] <= BLP_INCREMENT_TOLERANCE
        )
    passed = bool(
        every_event_false
        and active_rotations == 0
        and all(
            s1 <= NUMERICAL_ZERO and s2 <= NUMERICAL_ZERO
            for s1, s2 in entropies
        )
        and fixed_unit
        and fixed_blp["maximum_increment"] <= BLP_INCREMENT_TOLERANCE
        and ensemble_unit
        and ensemble_increment
    )
    if not passed:
        raise ValueError("p_event=0 structural negative control failed")
    return {
        "every_event_bit_structural_false": every_event_false,
        "active_axis_rotation_count": active_rotations,
        "all_system_memory_s1_s2_at_most_1e_12": True,
        "fixed_trace_distance_one_within_1e_12": fixed_unit,
        "fixed_named_increment_at_most_1e_10": True,
        "ensemble_trace_distance_one_within_1e_12": ensemble_unit,
        "ensemble_named_increment_at_most_1e_10": ensemble_increment,
        "passed": True,
    }


def run_dense_reference(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Execute the independent fixed-mask and optional finite-ensemble oracle."""

    _assert_little_endian()
    import_audit = audit_import_independence()
    normalized = _normalized_fixture(fixture)
    partial_swap_audit = partial_swap_factorization_audit(
        float(normalized["gamma"])
    )
    ledger = _ArrayLedger()
    fixed_paths, fixed_blp = _fixed_pair(normalized=normalized, ledger=ledger)
    ensemble = (
        _ensemble(normalized=normalized, ledger=ledger)
        if normalized["run_blpensemble"]
        else None
    )
    negative_control = _negative_control(
        normalized=normalized,
        fixed_paths=fixed_paths,
        fixed_blp=fixed_blp,
        ensemble=ensemble,
    )
    mask_payloads = [
        row["payload_hex"]
        for row in normalized["carrier_mask_rows"]
    ]
    ledger.sample_pre_release(
        "dense_reference.result_arrays.pre_release"
    )
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "run_partition": normalized["run_partition"],
        "case_id": normalized["case_id"],
        "coordinate_order": "q0_most_significant_bit",
        "system_axes": list(range(normalized["width"])),
        "memory_axes": list(
            range(normalized["width"], 2 * normalized["width"])
        ),
        "width": normalized["width"],
        "rounds": normalized["rounds"],
        "axis_family": normalized["axis_family"],
        "active_axes": list(normalized["active_axes"]),
        "p_event_numerator": normalized["p_event_numerator"],
        "p_event_denominator": 4,
        "gamma_float64_hex": normalized["gamma_float64_hex"],
        "theta_float64_hex": normalized["theta_float64_hex"],
        "seed": normalized["seed"],
        "fixed_mask": {
            "namespace": "CARRIER",
            "mask_index": 0,
            "rows": normalized["carrier_mask_rows"],
            "payload_sequence_sha256": hashlib.sha256(
                b"".join(bytes.fromhex(value) for value in mask_payloads)
            ).hexdigest(),
        },
        "fixed_paths": fixed_paths,
        "fixed_blp": fixed_blp,
        "finite_32_mask_ensemble": ensemble,
        "p_event_zero_control": negative_control,
        "max_sampled_dense_reference_array_bytes": ledger.maximum,
        "final_dense_reference_array_bytes": ledger.current,
        "scientific_dependencies": import_audit[
            "scientific_dependency_roots"
        ],
        "import_independence_audit": import_audit,
        "imports_candidate_or_simulator_helper": not import_audit[
            "passed"
        ],
        "partial_swap_factorization_audit": partial_swap_audit,
        "claim_boundary": (
            "independent_exact_dense_reference_for_frozen_finite_memory_fixture"
        ),
    }
    return result


def ndarray_v1(array: np.ndarray, *, dtype: str, shape: Sequence[int]) -> dict[str, Any]:
    """Encode exact C-order little-endian bytes without casting or normalizing."""

    _assert_little_endian()
    expected_dtype = np.dtype(dtype)
    expected_shape = tuple(shape)
    if (
        not isinstance(array, np.ndarray)
        or array.dtype != expected_dtype
        or array.shape != expected_shape
        or not array.flags.c_contiguous
        or not np.all(np.isfinite(array))
    ):
        raise ValueError("array violates its frozen ndarray-v1 contract")
    raw = array.tobytes(order="C")
    return {
        "encoding": NDARRAY_ENCODING,
        "dtype": dtype,
        "shape": list(expected_shape),
        "order": "C",
        "nbytes": len(raw),
        "data_sha256": hashlib.sha256(raw).hexdigest(),
        "data_base64": base64.b64encode(raw).decode("ascii"),
    }


def decode_ndarray_v1(
    payload: Mapping[str, Any],
    *,
    dtype: str,
    shape: Sequence[int],
) -> np.ndarray:
    expected_keys = {
        "encoding",
        "dtype",
        "shape",
        "order",
        "nbytes",
        "data_sha256",
        "data_base64",
    }
    if not isinstance(payload, Mapping) or set(payload) != expected_keys:
        raise ValueError("ndarray-v1 has the wrong exact key set")
    expected_shape = tuple(shape)
    if (
        payload["encoding"] != NDARRAY_ENCODING
        or payload["dtype"] != dtype
        or payload["shape"] != list(expected_shape)
        or any(not _is_int(value) or value < 0 for value in payload["shape"])
        or payload["order"] != "C"
        or not _is_int(payload["nbytes"])
    ):
        raise ValueError("ndarray-v1 metadata drifted")
    encoded = payload["data_base64"]
    if not isinstance(encoded, str) or any(ord(char) > 127 for char in encoded):
        raise ValueError("ndarray-v1 Base64 must be ASCII")
    try:
        raw = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("ndarray-v1 Base64 is invalid") from exc
    if base64.b64encode(raw).decode("ascii") != encoded:
        raise ValueError("ndarray-v1 Base64 is noncanonical")
    expected_nbytes = math.prod(expected_shape) * np.dtype(dtype).itemsize
    if payload["nbytes"] != expected_nbytes or len(raw) != expected_nbytes:
        raise ValueError("ndarray-v1 byte length drifted")
    if hashlib.sha256(raw).hexdigest() != payload["data_sha256"]:
        raise ValueError("ndarray-v1 data hash drifted")
    array = np.frombuffer(raw, dtype=np.dtype(dtype)).reshape(
        expected_shape, order="C"
    ).copy(order="C")
    if (
        array.dtype != np.dtype(dtype)
        or array.shape != expected_shape
        or not array.flags.c_contiguous
        or array.tobytes(order="C") != raw
        or not np.all(np.isfinite(array))
    ):
        raise ValueError("ndarray-v1 reconstruction gate failed")
    return array


def _serialize_arrays(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        dtype = value.dtype.str
        if dtype not in {"<c16", "<f8"}:
            raise ValueError(f"unregistered dense output array dtype: {dtype}")
        return ndarray_v1(value, dtype=dtype, shape=value.shape)
    if isinstance(value, Mapping):
        return {key: _serialize_arrays(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_serialize_arrays(child) for child in value]
    if isinstance(value, tuple):
        return [_serialize_arrays(child) for child in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def build_core_payload(fixture: Mapping[str, Any]) -> dict[str, Any]:
    scientific = run_dense_reference(fixture)
    payload = _serialize_arrays(scientific)
    payload["result_projection_sha256"] = canonical_sha256(payload)
    return payload



def _timing_span(
    *,
    span_id: str,
    parent_span_id: str | None,
    scope: str,
    case_id: str,
    kind: str,
    wall_start_offset_ns: int,
    wall_end_offset_ns: int,
    cpu_start_offset_ns: int,
    cpu_end_offset_ns: int,
    child_wall_ns: int = 0,
    child_cpu_ns: int = 0,
) -> dict[str, Any]:
    wall_duration = wall_end_offset_ns - wall_start_offset_ns
    cpu_duration = cpu_end_offset_ns - cpu_start_offset_ns
    if (
        wall_start_offset_ns < 0
        or cpu_start_offset_ns < 0
        or wall_duration < 0
        or cpu_duration < 0
        or child_wall_ns < 0
        or child_cpu_ns < 0
        or child_wall_ns > wall_duration
        or child_cpu_ns > cpu_duration
    ):
        raise ValueError("dense timing offsets do not reconcile")
    return {
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "scope": scope,
        "lane": None,
        "case_id": case_id,
        "trajectory_id": None,
        "round_index": None,
        "operation_index": None,
        "step_index": None,
        "kind": kind,
        "status": "completed",
        "wall_start_offset_ns": wall_start_offset_ns,
        "wall_end_offset_ns": wall_end_offset_ns,
        "wall_duration_ns": wall_duration,
        "cpu_start_offset_ns": cpu_start_offset_ns,
        "cpu_end_offset_ns": cpu_end_offset_ns,
        "cpu_duration_ns": cpu_duration,
        "child_wall_ns": child_wall_ns,
        "child_cpu_ns": child_cpu_ns,
        "unattributed_wall_ns": wall_duration - child_wall_ns,
        "unattributed_cpu_ns": cpu_duration - child_cpu_ns,
    }


def build_framed_worker_output(fixture: Mapping[str, Any]) -> bytes:
    """Return the two canonical worker frames; stdout/self-stop is supervisor-owned."""

    wall_root = time.perf_counter_ns()
    cpu_root = time.process_time_ns()
    root_wall_start = time.perf_counter_ns() - wall_root
    root_cpu_start = time.process_time_ns() - cpu_root

    science_wall_start = time.perf_counter_ns() - wall_root
    science_cpu_start = time.process_time_ns() - cpu_root
    scientific = run_dense_reference(fixture)
    science_wall_end = time.perf_counter_ns() - wall_root
    science_cpu_end = time.process_time_ns() - cpu_root

    serialization_wall_start = time.perf_counter_ns() - wall_root
    serialization_cpu_start = time.process_time_ns() - cpu_root
    core = _serialize_arrays(scientific)
    core["result_projection_sha256"] = canonical_sha256(core)
    core_bytes = canonical_json_bytes(core)
    serialization_wall_end = time.perf_counter_ns() - wall_root
    serialization_cpu_end = time.process_time_ns() - cpu_root

    root_wall_end = time.perf_counter_ns() - wall_root
    root_cpu_end = time.process_time_ns() - cpu_root
    science_span = _timing_span(
        span_id="dense_reference_scientific_calculation",
        parent_span_id="dense_reference_worker_total",
        scope="dense_reference_scientific_calculation",
        case_id=str(scientific["case_id"]),
        kind="independent_dense_evolution",
        wall_start_offset_ns=science_wall_start,
        wall_end_offset_ns=science_wall_end,
        cpu_start_offset_ns=science_cpu_start,
        cpu_end_offset_ns=science_cpu_end,
    )
    serialization_span = _timing_span(
        span_id="serialization",
        parent_span_id="dense_reference_worker_total",
        scope="serialization",
        case_id=str(scientific["case_id"]),
        kind="canonical_core_encoding",
        wall_start_offset_ns=serialization_wall_start,
        wall_end_offset_ns=serialization_wall_end,
        cpu_start_offset_ns=serialization_cpu_start,
        cpu_end_offset_ns=serialization_cpu_end,
    )
    root_span = _timing_span(
        span_id="dense_reference_worker_total",
        parent_span_id=None,
        scope="dense_reference_worker_total",
        case_id=str(scientific["case_id"]),
        kind="worker_root",
        wall_start_offset_ns=root_wall_start,
        wall_end_offset_ns=root_wall_end,
        cpu_start_offset_ns=root_cpu_start,
        cpu_end_offset_ns=root_cpu_end,
        child_wall_ns=(
            science_span["wall_duration_ns"]
            + serialization_span["wall_duration_ns"]
        ),
        child_cpu_ns=(
            science_span["cpu_duration_ns"]
            + serialization_span["cpu_duration_ns"]
        ),
    )
    timing = {
        "schema": (
            "error_coupling_simulator.external.gcapeps_finite_memory."
            "layered_timing.v1"
        ),
        "wall_clock": "time.perf_counter_ns",
        "cpu_clock": "time.process_time_ns",
        "spans": [root_span, science_span, serialization_span],
    }
    usage = resource.getrusage(resource.RUSAGE_SELF)
    trailer = {
        "schema": (
            "error_coupling_simulator.external.gcapeps_finite_memory."
            "late_telemetry_trailer.v1"
        ),
        "core_byte_length": len(core_bytes),
        "core_sha256": hashlib.sha256(core_bytes).hexdigest(),
        "ru_maxrss_raw": int(usage.ru_maxrss),
        "ru_maxrss_units": "KiB_on_linux",
        "sample_scope": "post_worker_root_pre_trailer",
        "timing": timing,
    }
    trailer_bytes = canonical_json_bytes(trailer)
    return (
        struct.pack(">Q", len(core_bytes))
        + core_bytes
        + struct.pack(">Q", len(trailer_bytes))
        + trailer_bytes
    )
