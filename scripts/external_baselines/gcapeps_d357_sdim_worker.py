#!/usr/bin/env python3
"""Untimed SDIM-qubit signed-pullback control for the d=3/5/7 sweep.

This worker consumes only the repository-owned neutral fixture.  It replays
each frozen H/CX layer through SDIM 1.3.3 and checks every exact signed
``(C^layer)^dagger Y C^layer`` row across all four error locations.  It imports neither Quimb nor GCAPEPS, owns no PEPS
state, and contributes no timing or memory sample.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import secrets
import sys
from typing import Any, Mapping, Sequence


WORKER_SCHEMA = (
    "error_coupling_simulator.external."
    "gcapeps_d357_sdim_accumulated_pullback_control.v2"
)
EXPECTED_SDIM_VERSION = "1.3.3"
SUPPORTED_DISTANCES = frozenset({3, 5, 7})
FIXTURE_EMITTER = Path(__file__).with_name(
    "emit_gcapeps_d357_unitary_prefix_fixture.py"
)

TOP_LEVEL_KEYS = frozenset(
    {
        "schema",
        "worker_role",
        "fixture_identity",
        "runtime_identity",
        "scope",
        "prefix_replay",
        "accumulated_frame_schedule",
        "sdim_control_verdict",
        "content_sha256",
    }
)
FIXTURE_IDENTITY_KEYS = frozenset(
    {
        "path",
        "file_sha256",
        "canonical_sha256",
        "schema",
        "fixture_id",
        "distance",
        "n_qubits",
        "prefix_gate_stream_sha256",
        "error_locations_sha256",
        "accumulated_frame_schedule_sha256",
    }
)
RUNTIME_IDENTITY_KEYS = frozenset(
    {
        "python_version",
        "python_executable",
        "sdim_version",
        "sdim_origin",
        "sdim_origin_sha256",
        "worker_origin",
        "worker_origin_sha256",
    }
)
SCOPE_KEYS = frozenset(
    {
        "dimension",
        "qubit_only",
        "untimed",
        "imports_quimb",
        "imports_gcapeps",
        "receives_peps",
        "emits_peps",
        "receives_state_vector",
        "emits_state_vector",
        "enters_performance_ratio",
        "ground_truth",
        "qutrit_evidence",
    }
)
PREFIX_REPLAY_KEYS = frozenset(
    {
        "gate_count",
        "h_count",
        "cx_count",
        "inverse_replay_order",
        "gate_subset",
        "tableau_dimension",
        "accumulated_layer_count",
        "error_location_count",
        "checked_row_count",
    }
)
ACCUMULATED_SCHEDULE_KEYS = frozenset(
    {
        "frame_boundary",
        "expected_schedule_sha256",
        "observed_schedule_sha256",
        "row_count",
        "expected_rows",
        "observed_rows",
        "exact_match",
    }
)
SCHEDULE_ROW_KEYS = frozenset(
    {
        "layer",
        "location_rank",
        "target",
        "signed_pullback",
        "support",
    }
)


def canonical_json_bytes(value: Any) -> bytes:
    """Return the sole JSON serialization used by this worker."""

    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def canonical_content_sha256(report: Mapping[str, Any]) -> str:
    """Hash a report without its top-level self-hash."""

    body = dict(report)
    body.pop("content_sha256", None)
    return _canonical_sha256(body)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _reject_constant(token: str) -> Any:
    raise ValueError(f"non-finite JSON token is forbidden: {token}")


def _object_without_duplicates(
    pairs: Sequence[tuple[str, Any]],
) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate JSON key is forbidden: {key!r}")
        out[key] = value
    return out


def _load_fixture_contract() -> Any:
    emitter = FIXTURE_EMITTER.resolve(strict=True)
    spec = importlib.util.spec_from_file_location(
        "_gcapeps_d357_fixture_contract_for_sdim",
        emitter,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("fixture contract loader is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    required = (
        "FIXTURE_SCHEMA",
        "canonical_json_bytes",
        "canonical_json_sha256",
        "validate_fixture",
    )
    missing = [name for name in required if not hasattr(module, name)]
    if missing:
        raise RuntimeError(f"fixture contract API is incomplete: {missing}")
    return module


def load_fixture(
    fixture_json: Path,
) -> tuple[Mapping[str, Any], dict[str, Any]]:
    """Load one byte-canonical fixture through its owning validator."""

    path = Path(fixture_json).resolve(strict=True)
    if not path.is_file():
        raise ValueError("fixture path must name a regular file")
    raw = path.read_bytes()
    try:
        decoded = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("fixture must be strict UTF-8 JSON") from exc
    try:
        value = json.loads(
            decoded,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise ValueError("fixture is not valid JSON") from exc
    if not isinstance(value, Mapping):
        raise ValueError("fixture root must be an object")

    contract = _load_fixture_contract()
    canonical = contract.canonical_json_bytes(value)
    if raw != canonical:
        raise ValueError("fixture file is not byte-canonical JSON")
    digest = contract.validate_fixture(value)
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or digest != hashlib.sha256(raw).hexdigest()
        or digest != contract.canonical_json_sha256(value)
    ):
        raise ValueError("fixture validator returned an inconsistent digest")
    if value.get("schema") != contract.FIXTURE_SCHEMA:
        raise ValueError("fixture schema drifted after validation")
    distance = value.get("distance")
    if (
        isinstance(distance, bool)
        or not isinstance(distance, int)
        or distance not in SUPPORTED_DISTANCES
    ):
        raise ValueError("fixture distance must be exactly one of 3, 5, or 7")

    identity = {
        "path": str(path),
        "file_sha256": digest,
        "canonical_sha256": digest,
        "schema": value["schema"],
        "fixture_id": value["fixture_id"],
        "distance": distance,
        "n_qubits": value["n_qubits"],
        "prefix_gate_stream_sha256": value["prefix"][
            "gate_stream_sha256"
        ],
        "error_locations_sha256": value["error_locations_sha256"],
        "accumulated_frame_schedule_sha256": value[
            "accumulated_frame_schedule"
        ]["schedule_sha256"],
    }
    return value, identity


def _load_sdim() -> Any:
    try:
        version = importlib.metadata.version("sdim")
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeError("sdim distribution is unavailable") from exc
    if version != EXPECTED_SDIM_VERSION:
        raise RuntimeError(
            f"sdim version drifted: expected {EXPECTED_SDIM_VERSION}, "
            f"got {version}"
        )
    spec = importlib.util.find_spec("sdim")
    if spec is None or spec.origin is None:
        raise RuntimeError("sdim module origin is unavailable")
    module = importlib.import_module("sdim")
    if getattr(module, "ExtendedTableau", None) is None:
        raise RuntimeError("sdim.ExtendedTableau is unavailable")
    return module


def _require_int(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    return value


def _new_sdim_tableau(
    fixture: Mapping[str, Any],
    *,
    sdim_module: Any,
) -> Any:
    n_qubits = _require_int(fixture["n_qubits"], label="n_qubits")
    tableau = sdim_module.ExtendedTableau(
        num_qudits=n_qubits,
        dimension=2,
    )
    if tableau.dimension != 2 or tableau.num_qudits != n_qubits:
        raise RuntimeError("SDIM tableau dimension or width drifted")
    return tableau


def _apply_inverse_prefix(
    tableau: Any,
    fixture: Mapping[str, Any],
    *,
    layer: int,
) -> None:
    """Accumulate one exact ``C^dagger`` layer on an SDIM tableau."""

    n_qubits = _require_int(fixture["n_qubits"], label="n_qubits")
    gates = fixture["prefix"]["gates"]
    if not isinstance(gates, list):
        raise TypeError("prefix.gates must be a list")
    for reverse_index, row in enumerate(reversed(gates)):
        if not isinstance(row, Mapping):
            raise TypeError("prefix gate rows must be objects")
        token = row["token"]
        targets = row["targets"]
        if not isinstance(targets, list):
            raise TypeError("prefix gate targets must be a list")
        if token == "H":
            if len(targets) != 1:
                raise ValueError("H gate must have exactly one target")
            target = _require_int(
                targets[0],
                label=(
                    f"layer {layer} reverse gate {reverse_index} H target"
                ),
            )
            tableau.hadamard(target)
        elif token == "CX":
            if len(targets) != 2:
                raise ValueError("CX gate must have exactly two targets")
            control = _require_int(
                targets[0],
                label=(
                    f"layer {layer} reverse gate {reverse_index} CX control"
                ),
            )
            target = _require_int(
                targets[1],
                label=(
                    f"layer {layer} reverse gate {reverse_index} CX target"
                ),
            )
            if control == target:
                raise ValueError("CX targets must be distinct")
            tableau.cnot(control, target)
        else:
            raise ValueError(f"unsupported SDIM prefix gate: {token!r}")
    tableau.modulo()
    if tableau.dimension != 2 or tableau.num_qudits != n_qubits:
        raise RuntimeError("SDIM tableau dimension or width drifted")


def _matrix_column(
    matrix: Any,
    *,
    column: int,
    width: int,
    label: str,
) -> list[int]:
    if getattr(matrix, "shape", None) != (width, width):
        raise ValueError(f"{label} shape drifted")
    if getattr(getattr(matrix, "dtype", None), "kind", None) not in ("i", "u"):
        raise TypeError(f"{label} must have integer dtype")
    return [int(matrix[row, column]) % 2 for row in range(width)]


def _phase_entry(
    vector: Any,
    *,
    index: int,
    width: int,
    label: str,
) -> int:
    if getattr(vector, "shape", None) != (width,):
        raise ValueError(f"{label} shape drifted")
    if getattr(getattr(vector, "dtype", None), "kind", None) not in ("i", "u"):
        raise TypeError(f"{label} must have integer dtype")
    return int(vector[index]) % 4


def _signed_y_output(
    tableau: Any,
    *,
    target: int,
    width: int,
) -> str:
    """Translate SDIM's exact image of ``Y_target`` to ``+/-_XYZ`` text.

    SDIM stores columns as ``i^p X^x Z^z``.  For qubits
    ``Y = i X Z``.  Multiplying the X- and Z-generator images adds the
    reordering phase ``2 z_X . x_Z`` modulo four.
    """

    if target < 0 or target >= width:
        raise ValueError("physical Y target is outside the tableau")
    x_x = _matrix_column(
        tableau.destab_x_block,
        column=target,
        width=width,
        label="destab_x_block",
    )
    z_x = _matrix_column(
        tableau.destab_z_block,
        column=target,
        width=width,
        label="destab_z_block",
    )
    x_z = _matrix_column(
        tableau.x_block,
        column=target,
        width=width,
        label="x_block",
    )
    z_z = _matrix_column(
        tableau.z_block,
        column=target,
        width=width,
        label="z_block",
    )
    phase_x = _phase_entry(
        tableau.destab_phase_vector,
        index=target,
        width=width,
        label="destab_phase_vector",
    )
    phase_z = _phase_entry(
        tableau.phase_vector,
        index=target,
        width=width,
        label="phase_vector",
    )

    x = [(left + right) % 2 for left, right in zip(x_x, x_z, strict=True)]
    z = [(left + right) % 2 for left, right in zip(z_x, z_z, strict=True)]
    reordering = sum(
        left * right for left, right in zip(z_x, x_z, strict=True)
    )
    phase = (1 + phase_x + phase_z + 2 * reordering) % 4
    y_count = sum(
        left * right for left, right in zip(x, z, strict=True)
    )
    relative_phase = (phase - y_count) % 4
    if relative_phase == 0:
        sign = "+"
    elif relative_phase == 2:
        sign = "-"
    else:
        raise RuntimeError("SDIM produced a non-Hermitian physical-Y image")

    labels = []
    for xb, zb in zip(x, z, strict=True):
        labels.append(
            {
                (0, 0): "_",
                (1, 0): "X",
                (1, 1): "Y",
                (0, 1): "Z",
            }[(xb, zb)]
        )
    return sign + "".join(labels)


def _support(signed_word: str, *, width: int) -> list[int]:
    if (
        not isinstance(signed_word, str)
        or len(signed_word) != width + 1
        or signed_word[0] not in "+-"
        or any(label not in "_XYZ" for label in signed_word[1:])
    ):
        raise ValueError("signed Pauli word has invalid width or alphabet")
    return [
        index
        for index, label in enumerate(signed_word[1:])
        if label != "_"
    ]


def _replay_accumulated_schedule(
    fixture: Mapping[str, Any],
    *,
    sdim_module: Any,
    fixture_contract: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    """Replay and check every frozen ``layer x location`` pullback row."""

    width = _require_int(fixture["n_qubits"], label="n_qubits")
    distance = _require_int(fixture["distance"], label="distance")
    locations = fixture["error_locations"]
    if not isinstance(locations, list) or len(locations) != 4:
        raise ValueError("fixture must contain exactly four error locations")
    schedule = fixture["accumulated_frame_schedule"]
    if not isinstance(schedule, Mapping):
        raise TypeError("accumulated_frame_schedule must be an object")
    expected_rows_raw = schedule["rows"]
    if not isinstance(expected_rows_raw, list):
        raise TypeError("accumulated frame rows must be a list")
    if len(expected_rows_raw) != distance * len(locations):
        raise ValueError("accumulated frame row count mismatch")
    expected_rows = [dict(row) for row in expected_rows_raw]
    expected_sha256 = schedule["schedule_sha256"]
    if (
        not isinstance(expected_sha256, str)
        or fixture_contract.canonical_json_sha256(expected_rows)
        != expected_sha256
    ):
        raise ValueError("fixture accumulated schedule hash mismatch")

    tableau = _new_sdim_tableau(fixture, sdim_module=sdim_module)
    observed_rows: list[dict[str, Any]] = []
    cursor = 0
    for layer in range(1, distance + 1):
        _apply_inverse_prefix(tableau, fixture, layer=layer)
        for location_rank, location in enumerate(locations, start=1):
            if not isinstance(location, Mapping):
                raise TypeError("error location rows must be objects")
            target = _require_int(
                location["target"],
                label=f"location {location_rank} target",
            )
            expected = expected_rows[cursor]
            required_order = {
                "layer": layer,
                "location_rank": location_rank,
                "target": target,
            }
            if any(expected.get(key) != value for key, value in required_order.items()):
                raise ValueError(
                    "fixture accumulated row order or target drifted at "
                    f"row {cursor}"
                )
            expected_word = expected.get("signed_pullback")
            expected_support = _support(expected_word, width=width)
            if expected.get("support") != expected_support:
                raise ValueError(
                    "fixture accumulated support drifted at "
                    f"layer {layer}, location {location_rank}"
                )
            observed_word = _signed_y_output(
                tableau,
                target=target,
                width=width,
            )
            observed_support = _support(observed_word, width=width)
            observed = {
                **required_order,
                "signed_pullback": observed_word,
                "support": observed_support,
            }
            observed_rows.append(observed)
            if observed != expected:
                raise RuntimeError(
                    "SDIM accumulated signed pullback mismatch at "
                    f"layer {layer}, location {location_rank}: "
                    f"expected {expected_word}, observed {observed_word}"
                )
            cursor += 1

    observed_sha256 = fixture_contract.canonical_json_sha256(observed_rows)
    if observed_sha256 != expected_sha256:
        raise RuntimeError(
            "SDIM accumulated schedule SHA mismatch: "
            f"expected {expected_sha256}, observed {observed_sha256}"
        )
    return expected_rows, observed_rows, observed_sha256


def build_report(*, fixture_json: Path) -> dict[str, Any]:
    """Build one untimed SDIM accumulated-pullback report."""

    fixture, fixture_identity = load_fixture(fixture_json)
    nonclifford = fixture["nonclifford"]
    if nonclifford["physical_pauli"] != "Y":
        raise ValueError("SDIM control requires physical_pauli=Y")
    fixture_contract = _load_fixture_contract()
    sdim_module = _load_sdim()
    expected_rows, observed_rows, observed_schedule_sha256 = (
        _replay_accumulated_schedule(
            fixture,
            sdim_module=sdim_module,
            fixture_contract=fixture_contract,
        )
    )

    sdim_origin_value = importlib.util.find_spec("sdim")
    if sdim_origin_value is None or sdim_origin_value.origin is None:
        raise RuntimeError("sdim module origin disappeared")
    sdim_origin = Path(sdim_origin_value.origin).resolve(strict=True)
    worker_origin = Path(__file__).resolve(strict=True)
    prefix = fixture["prefix"]
    report: dict[str, Any] = {
        "schema": WORKER_SCHEMA,
        "worker_role": "untimed_sdim_qubit_accumulated_pullback_corroboration",
        "fixture_identity": fixture_identity,
        "runtime_identity": {
            "python_version": platform.python_version(),
            "python_executable": str(Path(sys.executable).resolve(strict=True)),
            "sdim_version": importlib.metadata.version("sdim"),
            "sdim_origin": str(sdim_origin),
            "sdim_origin_sha256": _sha256_file(sdim_origin),
            "worker_origin": str(worker_origin),
            "worker_origin_sha256": _sha256_file(worker_origin),
        },
        "scope": {
            "dimension": 2,
            "qubit_only": True,
            "untimed": True,
            "imports_quimb": False,
            "imports_gcapeps": False,
            "receives_peps": False,
            "emits_peps": False,
            "receives_state_vector": False,
            "emits_state_vector": False,
            "enters_performance_ratio": False,
            "ground_truth": False,
            "qutrit_evidence": False,
        },
        "prefix_replay": {
            "gate_count": prefix["gate_count"],
            "h_count": prefix["h_count"],
            "cx_count": prefix["cx_count"],
            "inverse_replay_order": True,
            "gate_subset": ["H", "CX"],
            "tableau_dimension": 2,
            "accumulated_layer_count": fixture["distance"],
            "error_location_count": len(fixture["error_locations"]),
            "checked_row_count": len(observed_rows),
        },
        "accumulated_frame_schedule": {
            "frame_boundary": fixture["accumulated_frame_schedule"][
                "frame_boundary"
            ],
            "expected_schedule_sha256": fixture[
                "accumulated_frame_schedule"
            ]["schedule_sha256"],
            "observed_schedule_sha256": observed_schedule_sha256,
            "row_count": len(observed_rows),
            "expected_rows": expected_rows,
            "observed_rows": observed_rows,
            "exact_match": True,
        },
        "sdim_control_verdict": "PASS",
    }
    report["content_sha256"] = canonical_content_sha256(report)
    validate_report(report)
    return report


def _require_exact_keys(
    value: Any,
    expected: frozenset[str],
    *,
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    observed = frozenset(value)
    if observed != expected:
        raise ValueError(
            f"{label} keys drifted: "
            f"missing={sorted(expected - observed)}, "
            f"extra={sorted(observed - expected)}"
        )
    return value


def validate_report(report: Mapping[str, Any]) -> None:
    """Fail closed on report/schema/self-hash drift."""

    root = _require_exact_keys(report, TOP_LEVEL_KEYS, label="report")
    if (
        root["schema"] != WORKER_SCHEMA
        or root["worker_role"]
        != "untimed_sdim_qubit_accumulated_pullback_corroboration"
        or root["sdim_control_verdict"] != "PASS"
        or root["content_sha256"] != canonical_content_sha256(root)
    ):
        raise ValueError("report identity, verdict, or self-hash drifted")

    fixture = _require_exact_keys(
        root["fixture_identity"],
        FIXTURE_IDENTITY_KEYS,
        label="fixture_identity",
    )
    distance = fixture["distance"]
    if (
        isinstance(distance, bool)
        or not isinstance(distance, int)
        or distance not in SUPPORTED_DISTANCES
        or fixture["n_qubits"] != 2 * distance * distance - 1
        or fixture["file_sha256"] != fixture["canonical_sha256"]
    ):
        raise ValueError("fixture identity drifted")
    for field in (
        "file_sha256",
        "canonical_sha256",
        "prefix_gate_stream_sha256",
        "error_locations_sha256",
        "accumulated_frame_schedule_sha256",
    ):
        value = fixture[field]
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise ValueError(f"fixture_identity.{field} is not SHA-256")

    runtime = _require_exact_keys(
        root["runtime_identity"],
        RUNTIME_IDENTITY_KEYS,
        label="runtime_identity",
    )
    if runtime["sdim_version"] != EXPECTED_SDIM_VERSION:
        raise ValueError("runtime SDIM version drifted")

    scope = _require_exact_keys(
        root["scope"],
        SCOPE_KEYS,
        label="scope",
    )
    expected_scope = {
        "dimension": 2,
        "qubit_only": True,
        "untimed": True,
        "imports_quimb": False,
        "imports_gcapeps": False,
        "receives_peps": False,
        "emits_peps": False,
        "receives_state_vector": False,
        "emits_state_vector": False,
        "enters_performance_ratio": False,
        "ground_truth": False,
        "qutrit_evidence": False,
    }
    if dict(scope) != expected_scope:
        raise ValueError("scope drifted")

    prefix = _require_exact_keys(
        root["prefix_replay"],
        PREFIX_REPLAY_KEYS,
        label="prefix_replay",
    )
    if (
        prefix["gate_subset"] != ["H", "CX"]
        or prefix["inverse_replay_order"] is not True
        or prefix["tableau_dimension"] != 2
        or prefix["gate_count"] != prefix["h_count"] + prefix["cx_count"]
        or prefix["accumulated_layer_count"] != distance
        or prefix["error_location_count"] != 4
        or prefix["checked_row_count"] != 4 * distance
    ):
        raise ValueError("prefix replay ledger drifted")

    schedule = _require_exact_keys(
        root["accumulated_frame_schedule"],
        ACCUMULATED_SCHEDULE_KEYS,
        label="accumulated_frame_schedule",
    )
    expected_rows = schedule["expected_rows"]
    observed_rows = schedule["observed_rows"]
    if (
        not isinstance(schedule["frame_boundary"], str)
        or not schedule["frame_boundary"]
        or not isinstance(expected_rows, list)
        or not isinstance(observed_rows, list)
        or schedule["row_count"] != 4 * distance
        or len(expected_rows) != schedule["row_count"]
        or observed_rows != expected_rows
        or schedule["exact_match"] is not True
        or schedule["expected_schedule_sha256"]
        != fixture["accumulated_frame_schedule_sha256"]
        or schedule["observed_schedule_sha256"]
        != schedule["expected_schedule_sha256"]
    ):
        raise ValueError("accumulated schedule report drifted")

    fixture_contract = _load_fixture_contract()
    if (
        fixture_contract.canonical_json_sha256(expected_rows)
        != schedule["expected_schedule_sha256"]
        or fixture_contract.canonical_json_sha256(observed_rows)
        != schedule["observed_schedule_sha256"]
    ):
        raise ValueError("accumulated schedule report hash drifted")

    targets_by_rank: dict[int, int] = {}
    for index, row_value in enumerate(expected_rows):
        row = _require_exact_keys(
            row_value,
            SCHEDULE_ROW_KEYS,
            label=f"accumulated row {index}",
        )
        layer = index // 4 + 1
        location_rank = index % 4 + 1
        target = row["target"]
        if (
            row["layer"] != layer
            or row["location_rank"] != location_rank
            or isinstance(target, bool)
            or not isinstance(target, int)
            or target < 0
            or target >= fixture["n_qubits"]
        ):
            raise ValueError("accumulated schedule row order or target drifted")
        if layer == 1:
            if target in targets_by_rank.values():
                raise ValueError("accumulated schedule targets are not unique")
            targets_by_rank[location_rank] = target
        elif targets_by_rank.get(location_rank) != target:
            raise ValueError("accumulated schedule target changed across layers")
        if row["support"] != _support(
            row["signed_pullback"],
            width=fixture["n_qubits"],
        ):
            raise ValueError("accumulated schedule support drifted")


def write_report_no_replace(
    output_json: Path,
    report: Mapping[str, Any],
) -> Path:
    """Atomically publish one canonical private JSON file without overwrite."""

    validate_report(report)
    requested = Path(output_json)
    parent = requested.parent.resolve(strict=True)
    if not parent.is_dir():
        raise ValueError("output parent must be a directory")
    if requested.name in ("", ".", ".."):
        raise ValueError("output filename is invalid")
    destination = parent / requested.name
    payload = canonical_json_bytes(report)
    directory_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
    temporary = f".{requested.name}.tmp-{secrets.token_hex(12)}"
    file_fd: int | None = None
    try:
        file_fd = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        with os.fdopen(file_fd, "wb", closefd=True) as stream:
            file_fd = None
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(
                temporary,
                requested.name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            raise FileExistsError(
                f"refusing to replace existing output: {destination}"
            ) from exc
        os.fsync(directory_fd)
        os.unlink(temporary, dir_fd=directory_fd)
        os.fsync(directory_fd)
    except Exception:
        if file_fd is not None:
            os.close(file_fd)
        try:
            os.unlink(temporary, dir_fd=directory_fd)
            os.fsync(directory_fd)
        except FileNotFoundError:
            pass
        raise
    finally:
        os.close(directory_fd)
    return destination


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    fixture = args.fixture.resolve(strict=True)
    output_parent = args.output.parent.resolve(strict=True)
    output = output_parent / args.output.name
    if output == fixture:
        raise ValueError("output JSON must be distinct from the fixture")
    report = build_report(fixture_json=fixture)
    published = write_report_no_replace(output, report)
    print(
        json.dumps(
            {
                "content_sha256": report["content_sha256"],
                "output": str(published),
                "sdim_control_verdict": report["sdim_control_verdict"],
            },
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
