#!/usr/bin/env python3
"""Fail-closed supervisor for the finite-memory bond-32 run.

It owns byte transport, child dispatch, canonical publication, terminal and
receipt envelopes, system-scope transient-service lifecycles, stopped-process
barriers, failure-snapshot capture, and heldout serial propagation.  Production
execution remains gated on the dedicated manager preflight and its frozen
security/property evidence.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
import errno
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import signal
import stat
import struct
import subprocess
import sys
import time
import uuid
from typing import Any, Callable, Mapping, Sequence


_SCHEMA_PREFIX = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
)
INPUT_TRANSPORT_SCHEMA = _SCHEMA_PREFIX + "input_transport.v1"
NODE_TERMINAL_SCHEMA = _SCHEMA_PREFIX + "node_terminal.v1"
LAUNCH_RECEIPT_SCHEMA = _SCHEMA_PREFIX + "launch_receipt.v1"
MANAGER_PREFLIGHT_RECEIPT_SCHEMA = (
    _SCHEMA_PREFIX + "manager_preflight_receipt.v1"
)
TARGET_AMENDMENT_SCHEMA = _SCHEMA_PREFIX + "calibration_amendment.v1"
SACRIFICIAL_PREFLIGHT_SCHEMA = (
    _SCHEMA_PREFIX + "sacrificial_manager_preflight.v1"
)
TRAILER_SCHEMA = _SCHEMA_PREFIX + "late_telemetry_trailer.v1"

FIXTURE_SCHEMA = _SCHEMA_PREFIX + "fixture.v1"
DENSE_REFERENCE_SCHEMA = _SCHEMA_PREFIX + "dense_reference.v1"
PLAIN_EVIDENCE_SCHEMA = _SCHEMA_PREFIX + "plain_evidence_worker.v1"
PLAIN_CAP_PROBE_SCHEMA = _SCHEMA_PREFIX + "plain_cap_probe_worker.v1"
PLAIN_PERFORMANCE_SCHEMA = _SCHEMA_PREFIX + "plain_performance_worker.v1"
GCAPEPS_EVIDENCE_SCHEMA = _SCHEMA_PREFIX + "gcapeps_evidence_worker.v1"
GCAPEPS_CAP_PROBE_SCHEMA = _SCHEMA_PREFIX + "gcapeps_cap_probe_worker.v1"
GCAPEPS_PERFORMANCE_SCHEMA = _SCHEMA_PREFIX + "gcapeps_performance_worker.v1"
SDIM_FRAME_SCHEMA = _SCHEMA_PREFIX + "sdim_frame_control.v1"
SDIM_INVENTORY_SCHEMA = _SCHEMA_PREFIX + "sdim_inventory.v1"
COMPARATOR_SCHEMA = _SCHEMA_PREFIX + "comparator_worker.v1"
FAILURE_SNAPSHOT_SCHEMA = _SCHEMA_PREFIX + "systemd_failure_snapshot.v1"

BOOTSTRAP = "BOOTSTRAP"
CALIBRATION = "CALIBRATION"
HELDOUT = "HELDOUT"
RUN_PARTITIONS = frozenset({BOOTSTRAP, CALIBRATION, HELDOUT})

SACRIFICIAL_MANAGER_PREFLIGHT = "sacrificial_manager_preflight"
SDIM_INVENTORY_COLLECTOR = "sdim_inventory_collector"
NEUTRAL_FIXTURE_EMITTER = "neutral_fixture_emitter"
DENSE_REFERENCE = "dense_reference"
PLAIN_CAP_PROBE = "plain_cap_probe"
GCAPEPS_CAP_PROBE = "gcapeps_cap_probe"
PLAIN_EVIDENCE = "plain_evidence"
GCAPEPS_EVIDENCE = "gcapeps_evidence"
PLAIN_PERFORMANCE = "plain_performance"
GCAPEPS_PERFORMANCE = "gcapeps_performance"
SDIM_COMPUTATION = "sdim_computation"
TERMINAL_COMPARATOR = "terminal_comparator"

PRODUCTION_ROLES = frozenset(
    {
        SACRIFICIAL_MANAGER_PREFLIGHT,
        SDIM_INVENTORY_COLLECTOR,
        NEUTRAL_FIXTURE_EMITTER,
        DENSE_REFERENCE,
        PLAIN_CAP_PROBE,
        GCAPEPS_CAP_PROBE,
        PLAIN_EVIDENCE,
        GCAPEPS_EVIDENCE,
        PLAIN_PERFORMANCE,
        GCAPEPS_PERFORMANCE,
        SDIM_COMPUTATION,
        TERMINAL_COMPARATOR,
    }
)

ROLE_CORE_SCHEMAS: Mapping[str, str | None] = {
    SACRIFICIAL_MANAGER_PREFLIGHT: SACRIFICIAL_PREFLIGHT_SCHEMA,
    SDIM_INVENTORY_COLLECTOR: SDIM_INVENTORY_SCHEMA,
    NEUTRAL_FIXTURE_EMITTER: FIXTURE_SCHEMA,
    DENSE_REFERENCE: DENSE_REFERENCE_SCHEMA,
    PLAIN_CAP_PROBE: PLAIN_CAP_PROBE_SCHEMA,
    GCAPEPS_CAP_PROBE: GCAPEPS_CAP_PROBE_SCHEMA,
    PLAIN_EVIDENCE: PLAIN_EVIDENCE_SCHEMA,
    GCAPEPS_EVIDENCE: GCAPEPS_EVIDENCE_SCHEMA,
    PLAIN_PERFORMANCE: PLAIN_PERFORMANCE_SCHEMA,
    GCAPEPS_PERFORMANCE: GCAPEPS_PERFORMANCE_SCHEMA,
    SDIM_COMPUTATION: SDIM_FRAME_SCHEMA,
    TERMINAL_COMPARATOR: COMPARATOR_SCHEMA,
}

_ROLE_WORKER_FILENAMES: Mapping[str, str] = {
    SACRIFICIAL_MANAGER_PREFLIGHT: "run_gcapeps_finite_memory_bond32.py",
    SDIM_INVENTORY_COLLECTOR: "collect_gcapeps_finite_memory_sdim_inventory.py",
    NEUTRAL_FIXTURE_EMITTER: "emit_gcapeps_finite_memory_fixture.py",
    DENSE_REFERENCE: "gcapeps_finite_memory_dense_reference.py",
    PLAIN_CAP_PROBE: "plain_quimb_finite_memory_cap_probe_worker.py",
    GCAPEPS_CAP_PROBE: "gcapeps_finite_memory_cap_probe_worker.py",
    PLAIN_EVIDENCE: "plain_quimb_finite_memory_evidence_worker.py",
    GCAPEPS_EVIDENCE: "gcapeps_finite_memory_evidence_worker.py",
    PLAIN_PERFORMANCE: "plain_quimb_finite_memory_performance_worker.py",
    GCAPEPS_PERFORMANCE: "gcapeps_finite_memory_performance_worker.py",
    SDIM_COMPUTATION: "gcapeps_finite_memory_sdim_worker.py",
    TERMINAL_COMPARATOR: "compare_gcapeps_finite_memory_bond32.py",
}

MANIFEST_MAX_BYTES = 16_777_216
MANIFEST_MAX_ENTRIES = 64
ORDINARY_STDIN_MAX_BYTES = 67_108_864
COMPARATOR_STDIN_MAX_BYTES = 4_294_967_296
TRAILER_MAX_BYTES = 16_777_216
STDERR_MAX_BYTES = 1_048_576
FAILURE_SNAPSHOT_MAX_BYTES = 1_048_576
MAX_U64 = (1 << 64) - 1

_DENSE_CORE_MAX = 1_073_741_824
_EVIDENCE_CORE_MAX = 268_435_456
_OTHER_CORE_MAX = 67_108_864

_FRAME_LIMITS: Mapping[str, tuple[int, int, int]] = {
    DENSE_REFERENCE: (
        _DENSE_CORE_MAX,
        TRAILER_MAX_BYTES,
        1_090_519_056,
    ),
    PLAIN_EVIDENCE: (
        _EVIDENCE_CORE_MAX,
        TRAILER_MAX_BYTES,
        285_212_688,
    ),
    GCAPEPS_EVIDENCE: (
        _EVIDENCE_CORE_MAX,
        TRAILER_MAX_BYTES,
        285_212_688,
    ),
}
_OTHER_FRAME_LIMITS = (
    _OTHER_CORE_MAX,
    TRAILER_MAX_BYTES,
    83_886_096,
)

I_CAL = (
    "manager_preflight_receipt",
    "sdim_inventory_envelope",
    "sdim_inventory_launch_receipt",
)
I_HELD = I_CAL + ("target_amendment",)
B_CAL = I_CAL + (
    "neutral_fixture_envelope",
    "neutral_fixture_launch_receipt",
)
B_HELD = I_HELD + (
    "neutral_fixture_envelope",
    "neutral_fixture_launch_receipt",
)
X = (
    "dense_envelope",
    "dense_launch_receipt",
    "plain_input1_envelope",
    "plain_input1_launch_receipt",
    "plain_input2_envelope",
    "plain_input2_launch_receipt",
    "gc_input1_envelope",
    "gc_input1_launch_receipt",
    "gc_input2_envelope",
    "gc_input2_launch_receipt",
    "sdim_envelope",
    "sdim_launch_receipt",
)

_RECEIPT_TO_ENVELOPE: Mapping[str, str] = {
    "sdim_inventory_launch_receipt": "sdim_inventory_envelope",
    "neutral_fixture_launch_receipt": "neutral_fixture_envelope",
    "dense_launch_receipt": "dense_envelope",
    "plain_input1_launch_receipt": "plain_input1_envelope",
    "plain_input2_launch_receipt": "plain_input2_envelope",
    "gc_input1_launch_receipt": "gc_input1_envelope",
    "gc_input2_launch_receipt": "gc_input2_envelope",
    "sdim_launch_receipt": "sdim_envelope",
}

_ENTRY_SCHEMAS: Mapping[str, str] = {
    "manager_preflight_receipt": MANAGER_PREFLIGHT_RECEIPT_SCHEMA,
    "sdim_inventory_envelope": NODE_TERMINAL_SCHEMA,
    "sdim_inventory_launch_receipt": LAUNCH_RECEIPT_SCHEMA,
    "target_amendment": TARGET_AMENDMENT_SCHEMA,
    "neutral_fixture_envelope": NODE_TERMINAL_SCHEMA,
    "neutral_fixture_launch_receipt": LAUNCH_RECEIPT_SCHEMA,
    "dense_envelope": NODE_TERMINAL_SCHEMA,
    "dense_launch_receipt": LAUNCH_RECEIPT_SCHEMA,
    "plain_input1_envelope": NODE_TERMINAL_SCHEMA,
    "plain_input1_launch_receipt": LAUNCH_RECEIPT_SCHEMA,
    "plain_input2_envelope": NODE_TERMINAL_SCHEMA,
    "plain_input2_launch_receipt": LAUNCH_RECEIPT_SCHEMA,
    "gc_input1_envelope": NODE_TERMINAL_SCHEMA,
    "gc_input1_launch_receipt": LAUNCH_RECEIPT_SCHEMA,
    "gc_input2_envelope": NODE_TERMINAL_SCHEMA,
    "gc_input2_launch_receipt": LAUNCH_RECEIPT_SCHEMA,
    "sdim_envelope": NODE_TERMINAL_SCHEMA,
    "sdim_launch_receipt": LAUNCH_RECEIPT_SCHEMA,
}

_LAUNCH_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,95}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_CALIBRATION_ROUNDS = (4, 6, 8, 10, 12)
_HELDOUT_SEED = int.from_bytes(
    hashlib.sha256(b"gcapeps-finite-memory-heldout-v1").digest()[:8],
    "big",
)

_SCRIPT_PATH = Path(__file__).resolve(strict=True)
_SCRIPT_DIR = _SCRIPT_PATH.parent
_SNAPSHOT_HELPER = (
    _SCRIPT_DIR / "gcapeps_finite_memory_systemd_snapshot.py"
)


def _load_timing_module() -> Any:
    path = _SCRIPT_DIR / "gcapeps_finite_memory_timing.py"
    spec = importlib.util.spec_from_file_location(
        "_gcapeps_finite_memory_supervisor_timing",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the finite-memory timing owner")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


_TIMING = _load_timing_module()


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """Delegate the protocol's sole canonical encoder to the timing owner."""

    return _TIMING.canonical_json_bytes(payload)


def sha256_hex(raw: bytes) -> str:
    if not isinstance(raw, bytes):
        raise TypeError("SHA-256 input must be bytes")
    return hashlib.sha256(raw).hexdigest()


def _reject_constant(token: str) -> None:
    raise ValueError(f"non-finite JSON constant is forbidden: {token}")


def _unique_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_canonical_json_object(raw: bytes) -> dict[str, Any]:
    """Decode one exact finite canonical JSON object, with no compatibility."""

    if not isinstance(raw, bytes):
        raise TypeError("canonical JSON input must be bytes")
    try:
        text = raw.decode("utf-8", errors="strict")
        payload = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid UTF-8 JSON object") from exc
    if not isinstance(payload, dict):
        raise ValueError("canonical JSON top level must be an object")
    try:
        encoded = canonical_json_bytes(payload)
    except (TypeError, ValueError) as exc:
        raise ValueError("JSON object contains a noncanonical value") from exc
    if encoded != raw:
        raise ValueError("JSON bytes are not the exact canonical encoding")
    return payload


def _exact_keys(
    value: Mapping[str, Any],
    expected: set[str] | frozenset[str],
    *,
    name: str,
) -> None:
    if not isinstance(value, Mapping) or set(value) != set(expected):
        raise ValueError(f"{name} has the wrong exact key set")


def _plain_int(
    value: Any,
    *,
    name: str,
    minimum: int = 0,
    maximum: int = MAX_U64,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < minimum
        or value > maximum
    ):
        raise ValueError(
            f"{name} must be a non-boolean integer in [{minimum},{maximum}]"
        )
    return value


def _sha256(value: Any, *, name: str) -> str:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be lower-case SHA-256")
    return value


def _projection_sha256(payload: Mapping[str, Any]) -> str:
    projection = dict(payload)
    projection.pop("result_projection_sha256", None)
    return sha256_hex(canonical_json_bytes(projection))


def with_result_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copied payload with the exact projection digest attached."""

    if "result_projection_sha256" in payload:
        raise ValueError("projection field must be added exactly once")
    result = dict(payload)
    result["result_projection_sha256"] = _projection_sha256(result)
    return result


def validate_result_projection(
    payload: Mapping[str, Any],
    *,
    forbidden_self_digest_keys: Sequence[str] = (),
) -> None:
    for key in forbidden_self_digest_keys:
        if key in payload:
            raise ValueError(f"self digest field is forbidden: {key}")
    _sha256(
        payload.get("result_projection_sha256"),
        name="result_projection_sha256",
    )
    if payload["result_projection_sha256"] != _projection_sha256(payload):
        raise ValueError("result projection SHA-256 mismatch")


def expected_entry_sequence(run_partition: str, role: str) -> tuple[str, ...]:
    """Return the only production artifact sequence for a partition/role."""

    if not isinstance(run_partition, str) or not isinstance(role, str):
        raise ValueError("partition and role must be strings")
    if run_partition not in RUN_PARTITIONS:
        raise ValueError("unsupported run partition")
    if role not in PRODUCTION_ROLES:
        raise ValueError("unsupported production role")
    if run_partition == BOOTSTRAP:
        if role == SACRIFICIAL_MANAGER_PREFLIGHT:
            return ()
        if role == SDIM_INVENTORY_COLLECTOR:
            return ("manager_preflight_receipt",)
        raise ValueError("role is forbidden in BOOTSTRAP")
    if run_partition == CALIBRATION:
        if role == NEUTRAL_FIXTURE_EMITTER:
            return I_CAL
        if role in {
            DENSE_REFERENCE,
            PLAIN_CAP_PROBE,
            GCAPEPS_CAP_PROBE,
            PLAIN_EVIDENCE,
            GCAPEPS_EVIDENCE,
            SDIM_COMPUTATION,
        }:
            return B_CAL
        if role == TERMINAL_COMPARATOR:
            return B_CAL + X
        raise ValueError("role is forbidden in CALIBRATION")
    if role == NEUTRAL_FIXTURE_EMITTER:
        return I_HELD
    if role in {
        DENSE_REFERENCE,
        PLAIN_EVIDENCE,
        GCAPEPS_EVIDENCE,
        PLAIN_PERFORMANCE,
        GCAPEPS_PERFORMANCE,
        SDIM_COMPUTATION,
    }:
        return B_HELD
    if role == TERMINAL_COMPARATOR:
        return B_HELD + X
    raise ValueError("role is forbidden in HELDOUT")


def _validate_fixture_selector(
    parameters: Mapping[str, Any],
    *,
    run_partition: str,
) -> None:
    common = {
        "width",
        "rounds",
        "axis_family",
        "p_event_numerator",
        "p_event_denominator",
        "seed",
        "gamma_index",
        "run_blpensemble",
    }
    if run_partition == CALIBRATION:
        expected = common | {"rounds_index"}
    else:
        expected = common | {"heldout_cell_index"}
    _exact_keys(parameters, expected, name="fixture role_parameters")
    width = _plain_int(parameters["width"], name="width", minimum=1)
    rounds = _plain_int(parameters["rounds"], name="rounds", minimum=1)
    axis = _plain_int(
        parameters["axis_family"],
        name="axis_family",
        minimum=1,
        maximum=3,
    )
    numerator = _plain_int(
        parameters["p_event_numerator"],
        name="p_event_numerator",
        maximum=4,
    )
    denominator = _plain_int(
        parameters["p_event_denominator"],
        name="p_event_denominator",
        minimum=1,
    )
    seed = _plain_int(parameters["seed"], name="seed")
    gamma_index = _plain_int(
        parameters["gamma_index"],
        name="gamma_index",
        maximum=3,
    )
    if not isinstance(parameters["run_blpensemble"], bool):
        raise ValueError("run_blpensemble must be boolean")
    if denominator != 4:
        raise ValueError("p_event_denominator must be exactly four")
    if width not in {3, 5, 7}:
        raise ValueError("width is outside the frozen ladder set")
    if run_partition == CALIBRATION:
        rounds_index = _plain_int(
            parameters["rounds_index"],
            name="rounds_index",
            maximum=4,
        )
        if (
            width != 7
            or rounds != _CALIBRATION_ROUNDS[rounds_index]
            or axis != 3
            or numerator != 3
            or seed > 3
            or parameters["run_blpensemble"]
        ):
            raise ValueError("calibration fixture selector drifted")
    else:
        _plain_int(
            parameters["heldout_cell_index"],
            name="heldout_cell_index",
        )
        if seed != _HELDOUT_SEED:
            raise ValueError("held-out seed drifted")
        # The exact selected gamma, round list, cell ordering, and ensemble flag
        # are additionally re-bound to the target amendment by orchestration.
        if gamma_index > 3:
            raise AssertionError("unreachable gamma validation")


def _validate_calibration_identity(
    parameters: Mapping[str, Any],
    *,
    stage: str,
    extra_keys: set[str],
) -> None:
    expected = {
        "gamma_index",
        "rounds_index",
        "seed",
        "calibration_stage",
    } | extra_keys
    _exact_keys(parameters, expected, name="calibration role_parameters")
    _plain_int(
        parameters["gamma_index"],
        name="gamma_index",
        maximum=3,
    )
    _plain_int(
        parameters["rounds_index"],
        name="rounds_index",
        maximum=4,
    )
    _plain_int(parameters["seed"], name="seed", maximum=3)
    if parameters["calibration_stage"] != stage:
        raise ValueError("calibration stage drifted")
    if "input_id" in extra_keys:
        if _plain_int(
            parameters["input_id"],
            name="input_id",
            minimum=1,
            maximum=2,
        ) not in {1, 2}:
            raise AssertionError("unreachable input id validation")
    if "attempt_ordinal" in extra_keys:
        _plain_int(
            parameters["attempt_ordinal"],
            name="attempt_ordinal",
            minimum=1,
            maximum=100,
        )


def _validate_heldout_identity(
    parameters: Mapping[str, Any],
    *,
    extra_keys: set[str],
) -> None:
    expected = {"heldout_cell_index"} | extra_keys
    _exact_keys(parameters, expected, name="held-out role_parameters")
    _plain_int(
        parameters["heldout_cell_index"],
        name="heldout_cell_index",
    )
    if "input_id" in extra_keys:
        _plain_int(
            parameters["input_id"],
            name="input_id",
            minimum=1,
            maximum=2,
        )


_SACRIFICIAL_PARAMETER_KEYS = frozenset(
    {
        "runner_pid",
        "runner_start_time_ticks",
        "runner_real_uid",
        "runner_real_gid",
        "runner_namespace_identity",
        "selected_cpu",
        "output_root_abs",
        "evaluator_probe_abs",
        "quarantined_spool_probe_abs",
    }
)


def _validate_sacrificial_parameters(
    parameters: Mapping[str, Any],
) -> None:
    _exact_keys(
        parameters,
        _SACRIFICIAL_PARAMETER_KEYS,
        name="sacrificial role_parameters",
    )
    for name in (
        "runner_pid",
        "runner_start_time_ticks",
        "runner_real_uid",
        "runner_real_gid",
        "selected_cpu",
    ):
        _plain_int(
            parameters[name],
            name=name,
            minimum=1 if name in {"runner_pid", "runner_start_time_ticks"} else 0,
        )
    namespaces = parameters["runner_namespace_identity"]
    _exact_keys(
        namespaces,
        {"user", "mnt", "net", "pid"},
        name="runner namespace identity",
    )
    if any(not isinstance(value, str) or not value for value in namespaces.values()):
        raise ValueError("runner namespace identity is invalid")
    paths: dict[str, Path] = {}
    for name in (
        "output_root_abs",
        "evaluator_probe_abs",
        "quarantined_spool_probe_abs",
    ):
        value = parameters[name]
        if not isinstance(value, str) or not value or "\x00" in value:
            raise ValueError(f"{name} is invalid")
        path = Path(value)
        if (
            not path.is_absolute()
            or path != Path(os.path.abspath(path))
            or ".." in path.parts
        ):
            raise ValueError(f"{name} must be a canonical absolute path")
        paths[name] = path
    root = paths["output_root_abs"]
    if not paths["evaluator_probe_abs"].is_relative_to(root):
        raise ValueError("evaluator probe must be inside the output root")
    if not paths["quarantined_spool_probe_abs"].is_relative_to(root):
        raise ValueError("quarantined spool probe must be inside the output root")
    if len(set(paths.values())) != 3:
        raise ValueError("sacrificial probe paths must be distinct")


def validate_role_parameters(
    run_partition: str,
    role: str,
    role_parameters: Mapping[str, Any],
) -> None:
    """Validate the minimal, exact, role-specific selector channel."""

    expected_entry_sequence(run_partition, role)
    if not isinstance(role_parameters, Mapping):
        raise ValueError("role_parameters must be an object")
    if run_partition == BOOTSTRAP:
        if role == SACRIFICIAL_MANAGER_PREFLIGHT:
            _validate_sacrificial_parameters(role_parameters)
        else:
            _exact_keys(role_parameters, set(), name="bootstrap role_parameters")
        return
    if role == NEUTRAL_FIXTURE_EMITTER:
        _validate_fixture_selector(
            role_parameters,
            run_partition=run_partition,
        )
        return
    if run_partition == CALIBRATION:
        if role == DENSE_REFERENCE:
            _validate_calibration_identity(
                role_parameters,
                stage="A",
                extra_keys=set(),
            )
        elif role == PLAIN_CAP_PROBE:
            _validate_calibration_identity(
                role_parameters,
                stage="B",
                extra_keys={"input_id", "attempt_ordinal"},
            )
        elif role == GCAPEPS_CAP_PROBE:
            _validate_calibration_identity(
                role_parameters,
                stage="C",
                extra_keys={"input_id", "attempt_ordinal"},
            )
        elif role in {PLAIN_EVIDENCE, GCAPEPS_EVIDENCE}:
            _validate_calibration_identity(
                role_parameters,
                stage="D",
                extra_keys={"input_id"},
            )
        elif role in {SDIM_COMPUTATION, TERMINAL_COMPARATOR}:
            _validate_calibration_identity(
                role_parameters,
                stage="D",
                extra_keys=set(),
            )
        else:
            raise ValueError("calibration role has no parameter schema")
        return
    if role == DENSE_REFERENCE:
        _validate_heldout_identity(role_parameters, extra_keys=set())
    elif role in {PLAIN_EVIDENCE, GCAPEPS_EVIDENCE}:
        _validate_heldout_identity(
            role_parameters,
            extra_keys={"input_id"},
        )
    elif role in {PLAIN_PERFORMANCE, GCAPEPS_PERFORMANCE}:
        _validate_heldout_identity(
            role_parameters,
            extra_keys={"input_id", "sample_kind", "sample_index"},
        )
        if role_parameters["input_id"] != 1:
            raise ValueError("performance is registered only for input 1")
        sample_kind = role_parameters["sample_kind"]
        sample_index = role_parameters["sample_index"]
        if sample_kind == "warmup":
            if sample_index is not None:
                raise ValueError("warmup sample_index must be null")
        elif sample_kind == "measured":
            _plain_int(
                sample_index,
                name="sample_index",
                maximum=2,
            )
        else:
            raise ValueError("invalid performance sample kind")
    elif role in {SDIM_COMPUTATION, TERMINAL_COMPARATOR}:
        _validate_heldout_identity(role_parameters, extra_keys=set())
    else:
        raise ValueError("held-out role has no parameter schema")


@dataclass(frozen=True)
class TransportArtifact:
    name: str
    schema: str
    raw_bytes: bytes
    external_complete_file_sha256: str

    @classmethod
    def from_payload(
        cls,
        *,
        name: str,
        schema: str,
        payload: Mapping[str, Any],
    ) -> "TransportArtifact":
        raw = canonical_json_bytes(payload)
        return cls(
            name=name,
            schema=schema,
            raw_bytes=raw,
            external_complete_file_sha256=sha256_hex(raw),
        )


@dataclass(frozen=True)
class ParsedInputTransport:
    manifest: dict[str, Any]
    artifacts: tuple[tuple[str, bytes], ...]
    raw_byte_length: int
    raw_sha256: str

    def artifact_map(self) -> dict[str, bytes]:
        return dict(self.artifacts)

    def identity(self) -> dict[str, Any]:
        return {
            "byte_length": self.raw_byte_length,
            "sha256": self.raw_sha256,
            "ordered_entries": [
                {
                    "name": entry["name"],
                    "source_sha256": entry["sha256"],
                }
                for entry in self.manifest["entries"]
            ],
        }


def _stdin_cap(role: str) -> int:
    return (
        COMPARATOR_STDIN_MAX_BYTES
        if role == TERMINAL_COMPARATOR
        else ORDINARY_STDIN_MAX_BYTES
    )


def _validate_artifact_payload(
    raw: bytes,
    *,
    expected_schema: str,
) -> dict[str, Any]:
    payload = parse_canonical_json_object(raw)
    if payload.get("schema") != expected_schema:
        raise ValueError("artifact owning schema mismatch")
    validate_result_projection(payload)
    if expected_schema == NODE_TERMINAL_SCHEMA:
        validate_node_terminal(payload)
    elif expected_schema == LAUNCH_RECEIPT_SCHEMA:
        validate_launch_receipt(payload)
    return payload


def _validate_transport_artifact(
    artifact: TransportArtifact,
    *,
    expected_name: str,
) -> None:
    if not isinstance(artifact, TransportArtifact):
        raise TypeError("transport entries must be TransportArtifact objects")
    if artifact.name != expected_name:
        raise ValueError("artifact entry sequence drifted")
    expected_schema = _ENTRY_SCHEMAS[expected_name]
    if artifact.schema != expected_schema:
        raise ValueError("artifact declared schema drifted")
    if not isinstance(artifact.raw_bytes, bytes):
        raise TypeError("artifact bytes must be immutable bytes")
    actual_sha = sha256_hex(artifact.raw_bytes)
    _sha256(
        artifact.external_complete_file_sha256,
        name="external complete-file SHA-256",
    )
    if artifact.external_complete_file_sha256 != actual_sha:
        raise ValueError("artifact bytes differ from external source SHA-256")
    _validate_artifact_payload(
        artifact.raw_bytes,
        expected_schema=expected_schema,
    )


def _validate_envelope_receipt_pairs(
    artifacts: Mapping[str, bytes],
) -> None:
    for receipt_name, envelope_name in _RECEIPT_TO_ENVELOPE.items():
        if receipt_name not in artifacts:
            continue
        if envelope_name not in artifacts:
            raise ValueError("launch receipt lacks its paired node envelope")
        envelope_raw = artifacts[envelope_name]
        receipt = parse_canonical_json_object(artifacts[receipt_name])
        envelope = parse_canonical_json_object(envelope_raw)
        if receipt["node_terminal_byte_length"] != len(envelope_raw):
            raise ValueError("launch receipt envelope byte length mismatch")
        if receipt["node_terminal_complete_file_sha256"] != sha256_hex(
            envelope_raw
        ):
            raise ValueError("launch receipt envelope SHA-256 mismatch")
        for key in ("launch_id", "run_partition", "role", "terminal_kind"):
            if receipt[key] != envelope[key]:
                raise ValueError(f"launch receipt envelope {key} mismatch")
        if receipt["cleanup"] != envelope["cleanup"]:
            raise ValueError("launch receipt cleanup facts mismatch")
        if receipt["quarantine"] != envelope["quarantine"]:
            raise ValueError("launch receipt quarantine facts mismatch")


def build_input_transport(
    *,
    run_partition: str,
    role: str,
    role_parameters: Mapping[str, Any],
    artifacts: Sequence[TransportArtifact],
) -> bytes:
    """Build one exact input_transport.v1 container."""

    validate_role_parameters(run_partition, role, role_parameters)
    expected = expected_entry_sequence(run_partition, role)
    if isinstance(artifacts, (bytes, bytearray, str)):
        raise TypeError("artifacts must be an ordered object sequence")
    supplied = tuple(artifacts)
    if len(supplied) != len(expected):
        raise ValueError("artifact count differs from the exact role sequence")
    entries: list[dict[str, Any]] = []
    for expected_name, artifact in zip(expected, supplied):
        _validate_transport_artifact(
            artifact,
            expected_name=expected_name,
        )
        entries.append(
            {
                "name": artifact.name,
                "schema": artifact.schema,
                "byte_length": len(artifact.raw_bytes),
                "sha256": artifact.external_complete_file_sha256,
            }
        )
    _validate_envelope_receipt_pairs(
        {artifact.name: artifact.raw_bytes for artifact in supplied}
    )
    manifest = {
        "schema": INPUT_TRANSPORT_SCHEMA,
        "run_partition": run_partition,
        "role": role,
        "role_parameters": dict(role_parameters),
        "entries": entries,
    }
    manifest_bytes = canonical_json_bytes(manifest)
    if len(manifest_bytes) > MANIFEST_MAX_BYTES:
        raise ValueError("input transport manifest exceeds its byte cap")
    if len(entries) > MANIFEST_MAX_ENTRIES:
        raise ValueError("input transport has too many entries")
    chunks = [struct.pack(">Q", len(manifest_bytes)), manifest_bytes]
    total = 8 + len(manifest_bytes)
    for artifact in supplied:
        entry_size = len(artifact.raw_bytes)
        total = _checked_u64_add(total, 8, entry_size)
        if total > _stdin_cap(role):
            raise ValueError("input transport exceeds the role stdin cap")
        chunks.extend((struct.pack(">Q", entry_size), artifact.raw_bytes))
    raw = b"".join(chunks)
    if len(raw) != total:
        raise AssertionError("input transport size accounting drifted")
    # Reparse before any caller writes the bytes to fixture.stdin.
    parse_input_transport(
        raw,
        expected_partition=run_partition,
        expected_role=role,
        external_source_sha256={
            artifact.name: artifact.external_complete_file_sha256
            for artifact in supplied
        },
    )
    return raw


def _checked_u64_add(*values: int) -> int:
    total = 0
    for value in values:
        _plain_int(value, name="u64 length")
        total += value
        if total > MAX_U64:
            raise OverflowError("unsigned 64-bit length arithmetic overflow")
    return total


def parse_input_transport(
    raw: bytes,
    *,
    expected_partition: str | None = None,
    expected_role: str | None = None,
    external_source_sha256: Mapping[str, str] | None = None,
) -> ParsedInputTransport:
    """Parse and authenticate a complete in-memory transport container."""

    if not isinstance(raw, bytes):
        raise TypeError("input transport must be bytes")
    if len(raw) < 8:
        raise ValueError("input transport lacks its manifest prefix")
    manifest_size = struct.unpack(">Q", raw[:8])[0]
    if manifest_size > MANIFEST_MAX_BYTES:
        raise ValueError("input transport manifest exceeds its byte cap")
    manifest_end = _checked_u64_add(8, manifest_size)
    if manifest_end > len(raw):
        raise ValueError("input transport manifest is truncated")
    manifest = parse_canonical_json_object(raw[8:manifest_end])
    _exact_keys(
        manifest,
        {
            "schema",
            "run_partition",
            "role",
            "role_parameters",
            "entries",
        },
        name="input transport manifest",
    )
    if manifest["schema"] != INPUT_TRANSPORT_SCHEMA:
        raise ValueError("wrong input transport schema")
    run_partition = manifest["run_partition"]
    role = manifest["role"]
    if expected_partition is not None and run_partition != expected_partition:
        raise ValueError("input transport partition mismatch")
    if expected_role is not None and role != expected_role:
        raise ValueError("input transport role mismatch")
    validate_role_parameters(
        run_partition,
        role,
        manifest["role_parameters"],
    )
    if len(raw) > _stdin_cap(role):
        raise ValueError("input transport exceeds the role stdin cap")
    entries = manifest["entries"]
    if not isinstance(entries, list) or len(entries) > MANIFEST_MAX_ENTRIES:
        raise ValueError("input transport entries are invalid")
    expected_names = expected_entry_sequence(run_partition, role)
    if len(entries) != len(expected_names):
        raise ValueError("input transport entry count drifted")
    names: list[str] = []
    for index, (entry, expected_name) in enumerate(
        zip(entries, expected_names)
    ):
        _exact_keys(
            entry,
            {"name", "schema", "byte_length", "sha256"},
            name=f"input transport entry {index}",
        )
        if entry["name"] != expected_name or entry["name"] in names:
            raise ValueError("input transport entry order or uniqueness failed")
        names.append(entry["name"])
        if entry["schema"] != _ENTRY_SCHEMAS[expected_name]:
            raise ValueError("input transport entry schema drifted")
        _plain_int(entry["byte_length"], name="artifact byte_length")
        _sha256(entry["sha256"], name="artifact SHA-256")
    if external_source_sha256 is not None:
        if set(external_source_sha256) != set(expected_names):
            raise ValueError("external source hash set differs from entries")
        for entry in entries:
            _sha256(
                external_source_sha256[entry["name"]],
                name="external source SHA-256",
            )
            if external_source_sha256[entry["name"]] != entry["sha256"]:
                raise ValueError("manifest SHA differs from external source")

    cursor = manifest_end
    decoded: list[tuple[str, bytes]] = []
    for entry in entries:
        prefix_end = _checked_u64_add(cursor, 8)
        if prefix_end > len(raw):
            raise ValueError("artifact length prefix is truncated")
        artifact_size = struct.unpack(">Q", raw[cursor:prefix_end])[0]
        if artifact_size != entry["byte_length"]:
            raise ValueError("artifact prefix and manifest length disagree")
        artifact_end = _checked_u64_add(prefix_end, artifact_size)
        if artifact_end > len(raw):
            raise ValueError("artifact bytes are truncated")
        artifact_bytes = raw[prefix_end:artifact_end]
        if sha256_hex(artifact_bytes) != entry["sha256"]:
            raise ValueError("artifact SHA-256 mismatch")
        _validate_artifact_payload(
            artifact_bytes,
            expected_schema=entry["schema"],
        )
        decoded.append((entry["name"], artifact_bytes))
        cursor = artifact_end
    if cursor != len(raw):
        raise ValueError("input transport contains trailing bytes")
    _validate_envelope_receipt_pairs(dict(decoded))
    return ParsedInputTransport(
        manifest=manifest,
        artifacts=tuple(decoded),
        raw_byte_length=len(raw),
        raw_sha256=sha256_hex(raw),
    )


def _validate_transport_manifest_only(
    manifest: Mapping[str, Any],
    *,
    expected_partition: str | None,
    expected_role: str,
    total_size: int,
) -> list[Mapping[str, Any]]:
    """Validate all manifest metadata without reading an artifact payload."""

    _exact_keys(
        manifest,
        {
            "schema",
            "run_partition",
            "role",
            "role_parameters",
            "entries",
        },
        name="input transport manifest",
    )
    if manifest["schema"] != INPUT_TRANSPORT_SCHEMA:
        raise ValueError("wrong input transport schema")
    run_partition = manifest["run_partition"]
    if (
        expected_partition is not None
        and run_partition != expected_partition
    ):
        raise ValueError("input transport partition mismatch")
    if manifest["role"] != expected_role:
        raise ValueError("input transport role mismatch")
    validate_role_parameters(
        run_partition,
        expected_role,
        manifest["role_parameters"],
    )
    if total_size > _stdin_cap(expected_role):
        raise ValueError("input transport exceeds the role stdin cap")
    entries = manifest["entries"]
    if not isinstance(entries, list) or len(entries) > MANIFEST_MAX_ENTRIES:
        raise ValueError("input transport entries are invalid")
    expected_names = expected_entry_sequence(run_partition, expected_role)
    if len(entries) != len(expected_names):
        raise ValueError("input transport entry count drifted")
    names: list[str] = []
    for index, (entry, expected_name) in enumerate(
        zip(entries, expected_names)
    ):
        _exact_keys(
            entry,
            {"name", "schema", "byte_length", "sha256"},
            name=f"input transport entry {index}",
        )
        if entry["name"] != expected_name or entry["name"] in names:
            raise ValueError("input transport entry order or uniqueness failed")
        names.append(entry["name"])
        if entry["schema"] != _ENTRY_SCHEMAS[expected_name]:
            raise ValueError("input transport entry schema drifted")
        _plain_int(entry["byte_length"], name="artifact byte_length")
        _sha256(entry["sha256"], name="artifact SHA-256")
    return entries


def _pread_exact(fd: int, size: int, offset: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    cursor = offset
    while remaining:
        chunk = os.pread(fd, remaining, cursor)
        if not chunk:
            raise ValueError("sealed file became truncated while reading")
        chunks.append(chunk)
        cursor += len(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def read_input_transport_fd(
    fd: int,
    *,
    expected_role: str,
    expected_partition: str | None = None,
) -> ParsedInputTransport:
    """Preflight a sealed fd before bounded allocation and parse it."""

    identity = os.fstat(fd)
    if not stat.S_ISREG(identity.st_mode):
        raise ValueError("input transport fd is not a regular file")
    if identity.st_size < 8 or identity.st_size > _stdin_cap(expected_role):
        raise ValueError("input transport fd size is outside its cap")
    prefix = _pread_exact(fd, 8, 0)
    manifest_size = struct.unpack(">Q", prefix)[0]
    if manifest_size > MANIFEST_MAX_BYTES:
        raise ValueError("input transport manifest exceeds its byte cap")
    manifest_end = _checked_u64_add(8, manifest_size)
    if manifest_end > identity.st_size:
        raise ValueError("input transport manifest is truncated")
    manifest = parse_canonical_json_object(
        _pread_exact(fd, manifest_size, 8)
    )
    entries = _validate_transport_manifest_only(
        manifest,
        expected_partition=expected_partition,
        expected_role=expected_role,
        total_size=identity.st_size,
    )
    cursor = manifest_end
    for entry in entries:
        prefix_end = _checked_u64_add(cursor, 8)
        if prefix_end > identity.st_size:
            raise ValueError("artifact length prefix is truncated")
        artifact_size = struct.unpack(
            ">Q",
            _pread_exact(fd, 8, cursor),
        )[0]
        if artifact_size != entry["byte_length"]:
            raise ValueError("artifact prefix and manifest length disagree")
        cursor = _checked_u64_add(prefix_end, artifact_size)
        if cursor > identity.st_size:
            raise ValueError("artifact bytes are truncated")
    if cursor != identity.st_size:
        raise ValueError("input transport contains trailing bytes")
    # The complete allocation occurs only after fstat, manifest, every bounded
    # prefix, and exact whole-container size gates have passed.
    raw = _pread_exact(fd, identity.st_size, 0)
    return parse_input_transport(
        raw,
        expected_partition=expected_partition,
        expected_role=expected_role,
    )


@dataclass(frozen=True)
class RawFileIdentity:
    byte_length: int
    sha256: str

    @classmethod
    def from_bytes(cls, raw: bytes) -> "RawFileIdentity":
        return cls(byte_length=len(raw), sha256=sha256_hex(raw))

    def as_dict(self) -> dict[str, Any]:
        _plain_int(self.byte_length, name="raw byte length")
        _sha256(self.sha256, name="raw SHA-256")
        return {
            "byte_length": self.byte_length,
            "sha256": self.sha256,
        }


def _validate_raw_identity(value: Mapping[str, Any], *, name: str) -> None:
    _exact_keys(value, {"byte_length", "sha256"}, name=name)
    _plain_int(value["byte_length"], name=f"{name}.byte_length")
    _sha256(value["sha256"], name=f"{name}.sha256")


def _validate_input_identity(value: Mapping[str, Any]) -> None:
    _exact_keys(
        value,
        {"byte_length", "sha256", "ordered_entries"},
        name="input transport identity",
    )
    _plain_int(value["byte_length"], name="input identity byte_length")
    _sha256(value["sha256"], name="input identity sha256")
    rows = value["ordered_entries"]
    if not isinstance(rows, list):
        raise ValueError("input identity entries must be a list")
    names: list[str] = []
    for row in rows:
        _exact_keys(
            row,
            {"name", "source_sha256"},
            name="input identity entry",
        )
        if (
            not isinstance(row["name"], str)
            or not row["name"]
            or row["name"] in names
        ):
            raise ValueError("input identity entry name is invalid")
        names.append(row["name"])
        _sha256(row["source_sha256"], name="input source SHA-256")


_CLEANUP_KEYS = frozenset(
    {
        "status",
        "deadline_ns",
        "unit_load_state",
        "runtime_directory_removed",
        "failure_reason",
    }
)
_QUARANTINE_KEYS = frozenset(
    {
        "status",
        "relative_path",
        "outside_spool_parent_empty",
        "failure_reason",
    }
)


def _validate_cleanup(value: Mapping[str, Any]) -> None:
    _exact_keys(value, _CLEANUP_KEYS, name="cleanup facts")
    if value["status"] not in {"completed", "failed"}:
        raise ValueError("cleanup status is invalid")
    _plain_int(value["deadline_ns"], name="cleanup deadline_ns")
    if not isinstance(value["unit_load_state"], str):
        raise ValueError("cleanup unit_load_state must be a string")
    if not isinstance(value["runtime_directory_removed"], bool):
        raise ValueError("runtime-directory result must be boolean")
    if value["failure_reason"] is not None and not isinstance(
        value["failure_reason"], str
    ):
        raise ValueError("cleanup failure reason must be null or string")
    if value["status"] == "completed" and (
        value["unit_load_state"] != "not-found"
        or not value["runtime_directory_removed"]
        or value["failure_reason"] is not None
    ):
        raise ValueError("completed cleanup facts are inconsistent")


def _validate_quarantine(value: Mapping[str, Any]) -> None:
    _exact_keys(value, _QUARANTINE_KEYS, name="quarantine facts")
    if value["status"] not in {"completed", "failed"}:
        raise ValueError("quarantine status is invalid")
    if value["relative_path"] is not None and (
        not isinstance(value["relative_path"], str)
        or not value["relative_path"]
        or value["relative_path"].startswith("/")
        or ".." in Path(value["relative_path"]).parts
    ):
        raise ValueError("quarantine relative path is invalid")
    if not isinstance(value["outside_spool_parent_empty"], bool):
        raise ValueError("spool exact-set result must be boolean")
    if value["failure_reason"] is not None and not isinstance(
        value["failure_reason"], str
    ):
        raise ValueError("quarantine failure reason must be null or string")
    if value["status"] == "completed" and (
        value["relative_path"] is None
        or not value["outside_spool_parent_empty"]
        or value["failure_reason"] is not None
    ):
        raise ValueError("completed quarantine facts are inconsistent")


def completed_cleanup_facts(*, deadline_ns: int) -> dict[str, Any]:
    return {
        "status": "completed",
        "deadline_ns": _plain_int(deadline_ns, name="cleanup deadline_ns"),
        "unit_load_state": "not-found",
        "runtime_directory_removed": True,
        "failure_reason": None,
    }


def completed_quarantine_facts(*, relative_path: str) -> dict[str, Any]:
    value = {
        "status": "completed",
        "relative_path": relative_path,
        "outside_spool_parent_empty": True,
        "failure_reason": None,
    }
    _validate_quarantine(value)
    return value


_NODE_KEYS = frozenset(
    {
        "schema",
        "launch_id",
        "run_partition",
        "role",
        "terminal_kind",
        "input_transport",
        "core_schema",
        "core",
        "trailer",
        "raw_stdout",
        "raw_stderr",
        "unit_facts",
        "cgroup_barrier",
        "exit_facts",
        "failure_snapshot",
        "final_systemd_memory_peak_bytes",
        "cleanup",
        "quarantine",
        "result_projection_sha256",
    }
)
_TERMINAL_KINDS = frozenset(
    {
        "completed_result",
        "worker_censor",
        "supervisor_censor",
        "invalid_control",
    }
)


def _validate_core_trailer_pair(
    core: Mapping[str, Any],
    trailer: Mapping[str, Any],
) -> tuple[bytes, bytes]:
    core_bytes = canonical_json_bytes(core)
    trailer_bytes = canonical_json_bytes(trailer)
    validate_result_projection(core)
    _exact_keys(
        trailer,
        {
            "schema",
            "core_byte_length",
            "core_sha256",
            "ru_maxrss_raw",
            "ru_maxrss_units",
            "sample_scope",
            "timing",
        },
        name="late telemetry trailer",
    )
    if trailer["schema"] != TRAILER_SCHEMA:
        raise ValueError("late telemetry trailer schema mismatch")
    if trailer["core_byte_length"] != len(core_bytes):
        raise ValueError("trailer core byte length mismatch")
    if trailer["core_sha256"] != sha256_hex(core_bytes):
        raise ValueError("trailer core SHA-256 mismatch")
    _plain_int(trailer["ru_maxrss_raw"], name="ru_maxrss_raw")
    if trailer["ru_maxrss_units"] != "KiB_on_linux":
        raise ValueError("late telemetry RSS units drifted")
    if trailer["sample_scope"] != "post_worker_root_pre_trailer":
        raise ValueError("late telemetry sample scope drifted")
    _TIMING.validate_layered_timing(trailer["timing"])
    return core_bytes, trailer_bytes


def build_node_terminal(
    *,
    launch_id: str,
    run_partition: str,
    role: str,
    terminal_kind: str,
    input_transport: Mapping[str, Any],
    core: Mapping[str, Any] | None,
    trailer: Mapping[str, Any] | None,
    raw_stdout: Mapping[str, Any],
    raw_stderr: Mapping[str, Any],
    unit_facts: Mapping[str, Any] | None,
    cgroup_barrier: Mapping[str, Any] | None,
    exit_facts: Mapping[str, Any] | None,
    failure_snapshot: Mapping[str, Any] | None,
    final_systemd_memory_peak_bytes: int | None,
    cleanup: Mapping[str, Any],
    quarantine: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "schema": NODE_TERMINAL_SCHEMA,
        "launch_id": launch_id,
        "run_partition": run_partition,
        "role": role,
        "terminal_kind": terminal_kind,
        "input_transport": dict(input_transport),
        "core_schema": None if core is None else core.get("schema"),
        "core": None if core is None else dict(core),
        "trailer": None if trailer is None else dict(trailer),
        "raw_stdout": dict(raw_stdout),
        "raw_stderr": dict(raw_stderr),
        "unit_facts": None if unit_facts is None else dict(unit_facts),
        "cgroup_barrier": (
            None if cgroup_barrier is None else dict(cgroup_barrier)
        ),
        "exit_facts": None if exit_facts is None else dict(exit_facts),
        "failure_snapshot": (
            None if failure_snapshot is None else dict(failure_snapshot)
        ),
        "final_systemd_memory_peak_bytes": final_systemd_memory_peak_bytes,
        "cleanup": dict(cleanup),
        "quarantine": dict(quarantine),
    }
    result = with_result_projection(payload)
    validate_node_terminal(result)
    return result


def validate_node_terminal(payload: Mapping[str, Any]) -> None:
    _exact_keys(payload, _NODE_KEYS, name="node terminal")
    if payload["schema"] != NODE_TERMINAL_SCHEMA:
        raise ValueError("wrong node-terminal schema")
    if (
        not isinstance(payload["launch_id"], str)
        or _LAUNCH_ID_RE.fullmatch(payload["launch_id"]) is None
    ):
        raise ValueError("node-terminal launch_id is invalid")
    expected_entry_sequence(payload["run_partition"], payload["role"])
    if payload["terminal_kind"] not in _TERMINAL_KINDS:
        raise ValueError("node terminal kind is invalid")
    _validate_input_identity(payload["input_transport"])
    expected_inputs = expected_entry_sequence(
        payload["run_partition"],
        payload["role"],
    )
    actual_inputs = tuple(
        row["name"] for row in payload["input_transport"]["ordered_entries"]
    )
    if actual_inputs != expected_inputs:
        raise ValueError("node-terminal input entry sequence drifted")
    _validate_raw_identity(payload["raw_stdout"], name="raw stdout")
    _validate_raw_identity(payload["raw_stderr"], name="raw stderr")
    _validate_cleanup(payload["cleanup"])
    _validate_quarantine(payload["quarantine"])
    core = payload["core"]
    trailer = payload["trailer"]
    core_schema = payload["core_schema"]
    if payload["terminal_kind"] in {"completed_result", "worker_censor"}:
        if not isinstance(core, Mapping) or not isinstance(trailer, Mapping):
            raise ValueError("clean worker terminal requires both frames")
    elif payload["terminal_kind"] == "supervisor_censor":
        if core is not None or trailer is not None or core_schema is not None:
            raise ValueError("supervisor censor cannot claim child frames")
    else:
        if (core is None) != (trailer is None):
            raise ValueError("invalid terminal frames must be both present or null")
    if core is not None:
        if core.get("schema") != core_schema:
            raise ValueError("node-terminal core schema binding failed")
        expected_core = ROLE_CORE_SCHEMAS[payload["role"]]
        if expected_core is not None and core_schema != expected_core:
            raise ValueError("role-specific core schema mismatch")
        core_bytes, trailer_bytes = _validate_core_trailer_pair(core, trailer)
        framed = _TIMING.encode_two_frames(core_bytes, trailer_bytes)
        expected_stdout = RawFileIdentity.from_bytes(framed).as_dict()
        if payload["raw_stdout"] != expected_stdout:
            raise ValueError("node-terminal raw stdout identity mismatch")
        empty_stderr = RawFileIdentity.from_bytes(b"").as_dict()
        if payload["terminal_kind"] in {
            "completed_result",
            "worker_censor",
        } and payload["raw_stderr"] != empty_stderr:
            raise ValueError("clean worker stderr must be exactly empty")
    else:
        if core_schema is not None:
            raise ValueError("null core must have a null schema")
    for name in ("unit_facts", "cgroup_barrier", "exit_facts"):
        value = payload[name]
        if value is not None and not isinstance(value, Mapping):
            raise ValueError(f"{name} must be null or an object")
    snapshot = payload["failure_snapshot"]
    if snapshot is not None:
        _exact_keys(
            snapshot,
            {"schema", "byte_length", "sha256"},
            name="failure snapshot identity",
        )
        if snapshot["schema"] != FAILURE_SNAPSHOT_SCHEMA:
            raise ValueError("failure snapshot schema mismatch")
        _plain_int(
            snapshot["byte_length"],
            name="failure snapshot byte_length",
            maximum=FAILURE_SNAPSHOT_MAX_BYTES,
        )
        _sha256(snapshot["sha256"], name="failure snapshot sha256")
    peak = payload["final_systemd_memory_peak_bytes"]
    if peak is not None:
        _plain_int(peak, name="final systemd MemoryPeak")
    validate_result_projection(
        payload,
        forbidden_self_digest_keys=(
            "complete_file_sha256",
            "node_terminal_complete_file_sha256",
        ),
    )


_RECEIPT_KEYS = frozenset(
    {
        "schema",
        "launch_id",
        "run_partition",
        "role",
        "node_terminal_path",
        "node_terminal_schema",
        "node_terminal_byte_length",
        "node_terminal_complete_file_sha256",
        "terminal_kind",
        "cleanup",
        "quarantine",
        "supervisor_launch_wall_ns",
        "result_projection_sha256",
    }
)


def build_launch_receipt(
    *,
    launch_id: str,
    run_partition: str,
    role: str,
    node_terminal_path: Path,
    node_terminal_identity: "PublishedFileIdentity",
    terminal_kind: str,
    cleanup: Mapping[str, Any],
    quarantine: Mapping[str, Any],
    supervisor_launch_wall_ns: int,
) -> dict[str, Any]:
    if str(node_terminal_path) != node_terminal_identity.path:
        raise ValueError("node-terminal path and published identity disagree")
    payload = {
        "schema": LAUNCH_RECEIPT_SCHEMA,
        "launch_id": launch_id,
        "run_partition": run_partition,
        "role": role,
        "node_terminal_path": str(node_terminal_path),
        "node_terminal_schema": NODE_TERMINAL_SCHEMA,
        "node_terminal_byte_length": node_terminal_identity.byte_length,
        "node_terminal_complete_file_sha256": node_terminal_identity.sha256,
        "terminal_kind": terminal_kind,
        "cleanup": dict(cleanup),
        "quarantine": dict(quarantine),
        "supervisor_launch_wall_ns": supervisor_launch_wall_ns,
    }
    result = with_result_projection(payload)
    validate_launch_receipt(result)
    return result


def validate_launch_receipt(payload: Mapping[str, Any]) -> None:
    _exact_keys(payload, _RECEIPT_KEYS, name="launch receipt")
    if payload["schema"] != LAUNCH_RECEIPT_SCHEMA:
        raise ValueError("wrong launch-receipt schema")
    if (
        not isinstance(payload["launch_id"], str)
        or _LAUNCH_ID_RE.fullmatch(payload["launch_id"]) is None
    ):
        raise ValueError("launch-receipt launch id is invalid")
    expected_entry_sequence(payload["run_partition"], payload["role"])
    path = Path(payload["node_terminal_path"])
    if not path.is_absolute():
        raise ValueError("node terminal path must be absolute")
    if payload["node_terminal_schema"] != NODE_TERMINAL_SCHEMA:
        raise ValueError("launch receipt node schema drifted")
    _plain_int(
        payload["node_terminal_byte_length"],
        name="node terminal byte length",
    )
    _sha256(
        payload["node_terminal_complete_file_sha256"],
        name="node terminal complete-file SHA-256",
    )
    if payload["terminal_kind"] not in _TERMINAL_KINDS:
        raise ValueError("launch receipt terminal kind is invalid")
    _validate_cleanup(payload["cleanup"])
    _validate_quarantine(payload["quarantine"])
    _plain_int(
        payload["supervisor_launch_wall_ns"],
        name="supervisor launch wall",
        minimum=1,
    )
    validate_result_projection(
        payload,
        forbidden_self_digest_keys=(
            "complete_file_sha256",
            "launch_receipt_complete_file_sha256",
        ),
    )


@dataclass(frozen=True)
class DecodedWorkerFrames:
    core_bytes: bytes
    trailer_bytes: bytes
    core: dict[str, Any]
    trailer: dict[str, Any]


def frame_limits(role: str) -> tuple[int, int, int]:
    if role not in PRODUCTION_ROLES:
        raise ValueError("unknown role for frame limits")
    return _FRAME_LIMITS.get(role, _OTHER_FRAME_LIMITS)


def decode_clean_worker_frames(
    raw: bytes,
    *,
    role: str,
    expected_core_schema: str | None = None,
) -> DecodedWorkerFrames:
    """Strictly decode the only legal clean exit-zero stdout shape."""

    core_max, trailer_max, limit_fsize = frame_limits(role)
    if len(raw) > limit_fsize:
        raise ValueError("raw stdout exceeds role LimitFSIZE")
    core_bytes, trailer_bytes = _TIMING.decode_two_frames(
        raw,
        core_max=core_max,
        trailer_max=trailer_max,
    )
    core = parse_canonical_json_object(core_bytes)
    trailer = parse_canonical_json_object(trailer_bytes)
    schema = (
        expected_core_schema
        if expected_core_schema is not None
        else ROLE_CORE_SCHEMAS[role]
    )
    if schema is None:
        raise ValueError("role requires an explicit registered core schema")
    if core.get("schema") != schema:
        raise ValueError("clean worker core schema mismatch")
    validate_result_projection(core)
    _exact_keys(
        trailer,
        {
            "schema",
            "core_byte_length",
            "core_sha256",
            "ru_maxrss_raw",
            "ru_maxrss_units",
            "sample_scope",
            "timing",
        },
        name="late telemetry trailer",
    )
    if trailer["schema"] != TRAILER_SCHEMA:
        raise ValueError("late telemetry trailer schema mismatch")
    if trailer["core_byte_length"] != len(core_bytes):
        raise ValueError("trailer core byte length mismatch")
    if trailer["core_sha256"] != sha256_hex(core_bytes):
        raise ValueError("trailer core SHA-256 mismatch")
    _plain_int(trailer["ru_maxrss_raw"], name="ru_maxrss_raw")
    if trailer["ru_maxrss_units"] != "KiB_on_linux":
        raise ValueError("late telemetry RSS units drifted")
    if trailer["sample_scope"] != "post_worker_root_pre_trailer":
        raise ValueError("late telemetry sample scope drifted")
    _TIMING.validate_layered_timing(trailer["timing"])
    return DecodedWorkerFrames(
        core_bytes=core_bytes,
        trailer_bytes=trailer_bytes,
        core=core,
        trailer=trailer,
    )


def read_clean_worker_frames_fd(
    fd: int,
    *,
    role: str,
    expected_core_schema: str | None = None,
) -> DecodedWorkerFrames:
    """Apply fstat and both prefix caps before allocating worker frames."""

    core_max, trailer_max, limit_fsize = frame_limits(role)
    identity = os.fstat(fd)
    if not stat.S_ISREG(identity.st_mode):
        raise ValueError("raw stdout is not a regular file")
    if identity.st_size < 16 or identity.st_size > limit_fsize:
        raise ValueError("raw stdout size is outside its role cap")
    first_prefix = _pread_exact(fd, 8, 0)
    core_size = struct.unpack(">Q", first_prefix)[0]
    if core_size > core_max:
        raise ValueError("core frame exceeds cap")
    second_prefix_offset = _checked_u64_add(8, core_size)
    second_prefix_end = _checked_u64_add(second_prefix_offset, 8)
    if second_prefix_end > identity.st_size:
        raise ValueError("core frame or trailer prefix is truncated")
    trailer_size = struct.unpack(
        ">Q",
        _pread_exact(fd, 8, second_prefix_offset),
    )[0]
    if trailer_size > trailer_max:
        raise ValueError("trailer frame exceeds cap")
    expected_size = _checked_u64_add(second_prefix_end, trailer_size)
    if expected_size != identity.st_size:
        raise ValueError("raw stdout is truncated or has trailing bytes")
    raw = _pread_exact(fd, identity.st_size, 0)
    return decode_clean_worker_frames(
        raw,
        role=role,
        expected_core_schema=expected_core_schema,
    )


@dataclass(frozen=True)
class ExternalStdoutInspection:
    disposition: str
    byte_length: int
    decoded: DecodedWorkerFrames | None
    reason: str | None


def inspect_external_censor_stdout_fd(
    fd: int,
    *,
    role: str,
) -> ExternalStdoutInspection:
    """Classify bounded stdout without interpreting truncated child claims."""

    core_max, trailer_max, limit_fsize = frame_limits(role)
    identity = os.fstat(fd)
    if not stat.S_ISREG(identity.st_mode):
        raise ValueError("external-censor stdout is not a regular file")
    size = int(identity.st_size)
    if size > limit_fsize:
        return ExternalStdoutInspection("invalid", size, None, "limit_fsize")
    if size == 0:
        return ExternalStdoutInspection("absent", 0, None, None)
    if size < 8:
        return ExternalStdoutInspection("truncated", size, None, None)
    core_size = struct.unpack(">Q", _pread_exact(fd, 8, 0))[0]
    if core_size > core_max:
        return ExternalStdoutInspection("invalid", size, None, "core_cap")
    second_prefix_offset = _checked_u64_add(8, core_size)
    second_prefix_end = _checked_u64_add(second_prefix_offset, 8)
    if size < second_prefix_end:
        return ExternalStdoutInspection("truncated", size, None, None)
    trailer_size = struct.unpack(
        ">Q", _pread_exact(fd, 8, second_prefix_offset)
    )[0]
    if trailer_size > trailer_max:
        return ExternalStdoutInspection("invalid", size, None, "trailer_cap")
    expected_size = _checked_u64_add(second_prefix_end, trailer_size)
    if size < expected_size:
        return ExternalStdoutInspection("truncated", size, None, None)
    if size > expected_size:
        return ExternalStdoutInspection("invalid", size, None, "extra_bytes")
    raw = _pread_exact(fd, size, 0)
    try:
        decoded = decode_clean_worker_frames(raw, role=role)
    except (TypeError, ValueError) as exc:
        return ExternalStdoutInspection(
            "invalid",
            size,
            None,
            f"complete_frame_invalid:{type(exc).__name__}",
        )
    return ExternalStdoutInspection("complete", size, decoded, None)


def classify_clean_worker_core(core: Mapping[str, Any]) -> str:
    """Map one validated finite clean core to its terminal disposition."""

    validate_result_projection(core)
    claimed = core.get("terminal_kind", "completed_result")
    if claimed not in {"completed_result", "worker_censor"}:
        raise ValueError("clean worker core terminal kind is invalid")
    return claimed


_RENAME_NOREPLACE = 1


def _renameat2(
    olddirfd: int,
    oldname: bytes,
    newdirfd: int,
    newname: bytes,
    flags: int,
) -> None:
    if platform.system() != "Linux":
        raise OSError(errno.ENOTSUP, "Linux renameat2 is required")
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, "renameat2", None)
    if rename is None:
        raise OSError(errno.ENOTSUP, "renameat2 is unavailable")
    rename.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    rename.restype = ctypes.c_int
    result = rename(olddirfd, oldname, newdirfd, newname, flags)
    if result != 0:
        error_code = ctypes.get_errno()
        raise OSError(error_code, os.strerror(error_code), os.fsdecode(newname))


def _write_all(fd: int, raw: bytes) -> None:
    offset = 0
    while offset < len(raw):
        written = os.write(fd, raw[offset:])
        if written <= 0:
            raise OSError("short write")
        offset += written


def _read_all_fd(fd: int, expected_size: int) -> bytes:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    remaining = expected_size
    while remaining:
        chunk = os.read(fd, min(1 << 20, remaining))
        if not chunk:
            raise ValueError("published file became truncated")
        chunks.append(chunk)
        remaining -= len(chunk)
    if os.read(fd, 1):
        raise ValueError("published file contains trailing bytes")
    return b"".join(chunks)


@dataclass(frozen=True)
class PublishedFileIdentity:
    path: str
    byte_length: int
    sha256: str
    st_dev: int
    st_ino: int
    st_mode: int
    st_nlink: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
            "st_dev": self.st_dev,
            "st_ino": self.st_ino,
            "st_mode": self.st_mode,
            "st_nlink": self.st_nlink,
        }


def _same_inode(left: os.stat_result, right: os.stat_result) -> bool:
    return left.st_dev == right.st_dev and left.st_ino == right.st_ino


def _unlink_owned_temp(
    parent_fd: int,
    name: str,
    expected: os.stat_result | None,
) -> None:
    if expected is None:
        return
    try:
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    if not _same_inode(current, expected):
        return
    os.unlink(name, dir_fd=parent_fd)


def publish_canonical_bytes_noreplace(
    destination: Path,
    raw: bytes,
) -> PublishedFileIdentity:
    """Publish canonical JSON through the protocol's sole file primitive."""

    if not isinstance(raw, bytes):
        raise TypeError("publication bytes must be immutable bytes")
    parse_canonical_json_object(raw)
    destination = Path(destination)
    if not destination.is_absolute() or destination.name in {"", ".", ".."}:
        raise ValueError("publication destination must be an absolute file path")
    parent_lexical = destination.parent
    parent_resolved = parent_lexical.resolve(strict=True)
    if parent_resolved != Path(os.path.abspath(parent_lexical)):
        raise ValueError("publication parent must be a nonsymlink lexical path")
    parent_fd = os.open(
        parent_resolved,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    temporary_name = (
        f".{destination.name}.tmp-{os.getpid()}-{uuid.uuid4().hex}"
    )
    file_fd = -1
    destination_fd = -1
    temporary_identity: os.stat_result | None = None
    renamed = False
    try:
        parent_identity = os.fstat(parent_fd)
        file_fd = os.open(
            temporary_name,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | os.O_CLOEXEC,
            0o644,
            dir_fd=parent_fd,
        )
        temporary_identity = os.fstat(file_fd)
        os.fchmod(file_fd, 0o644)
        _write_all(file_fd, raw)
        os.fsync(file_fd)
        temporary_identity = os.fstat(file_fd)
        if (
            not stat.S_ISREG(temporary_identity.st_mode)
            or stat.S_IMODE(temporary_identity.st_mode) != 0o644
            or temporary_identity.st_nlink != 1
            or temporary_identity.st_size != len(raw)
            or temporary_identity.st_uid != os.geteuid()
        ):
            raise RuntimeError("temporary publication inode identity is invalid")
        os.close(file_fd)
        file_fd = -1
        _renameat2(
            parent_fd,
            os.fsencode(temporary_name),
            parent_fd,
            os.fsencode(destination.name),
            _RENAME_NOREPLACE,
        )
        renamed = True
        os.fsync(parent_fd)
        destination_fd = os.open(
            destination.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=parent_fd,
        )
        destination_identity = os.fstat(destination_fd)
        if (
            not _same_inode(destination_identity, temporary_identity)
            or not stat.S_ISREG(destination_identity.st_mode)
            or stat.S_IMODE(destination_identity.st_mode) != 0o644
            or destination_identity.st_nlink != 1
            or destination_identity.st_size != len(raw)
        ):
            raise RuntimeError("published destination identity mismatch")
        reread = _read_all_fd(destination_fd, len(raw))
        if reread != raw:
            raise RuntimeError("published destination bytes mismatch")
        parent_now = os.stat(parent_resolved, follow_symlinks=False)
        if not _same_inode(parent_now, parent_identity):
            raise RuntimeError("publication parent identity drifted")
        return PublishedFileIdentity(
            path=str(destination),
            byte_length=len(raw),
            sha256=sha256_hex(reread),
            st_dev=int(destination_identity.st_dev),
            st_ino=int(destination_identity.st_ino),
            st_mode=int(destination_identity.st_mode),
            st_nlink=int(destination_identity.st_nlink),
        )
    except BaseException:
        if not renamed:
            _unlink_owned_temp(
                parent_fd,
                temporary_name,
                temporary_identity,
            )
        # A destination that has already been renamed is deliberately retained.
        raise
    finally:
        if destination_fd >= 0:
            os.close(destination_fd)
        if file_fd >= 0:
            os.close(file_fd)
        os.close(parent_fd)


def publish_canonical_json_noreplace(
    destination: Path,
    payload: Mapping[str, Any],
) -> PublishedFileIdentity:
    return publish_canonical_bytes_noreplace(
        destination,
        canonical_json_bytes(payload),
    )


def transport_artifact_from_published_file(
    *,
    name: str,
    identity: PublishedFileIdentity,
) -> TransportArtifact:
    """Reopen and reauthenticate one externally hash-owned source artifact."""

    if name not in _ENTRY_SCHEMAS:
        raise ValueError("unknown transport artifact name")
    path = Path(identity.path)
    if not path.is_absolute() or path.name in {"", ".", ".."}:
        raise ValueError("published source path must be absolute")
    parent = path.parent
    resolved_parent = parent.resolve(strict=True)
    if resolved_parent != Path(os.path.abspath(parent)):
        raise ValueError("published source parent must be nonsymlink lexical")
    _plain_int(
        identity.byte_length,
        name="published source byte length",
        maximum=COMPARATOR_STDIN_MAX_BYTES,
    )
    _sha256(identity.sha256, name="published source SHA-256")
    parent_fd = os.open(
        resolved_parent,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    file_fd = -1
    try:
        file_fd = os.open(
            path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=parent_fd,
        )
        observed = os.fstat(file_fd)
        if (
            not stat.S_ISREG(observed.st_mode)
            or stat.S_IMODE(observed.st_mode) != 0o644
            or observed.st_nlink != 1
            or observed.st_dev != identity.st_dev
            or observed.st_ino != identity.st_ino
            or observed.st_mode != identity.st_mode
            or observed.st_nlink != identity.st_nlink
            or observed.st_size != identity.byte_length
        ):
            raise ValueError("published source inode identity drifted")
        raw = _read_all_fd(file_fd, identity.byte_length)
        if sha256_hex(raw) != identity.sha256:
            raise ValueError("published source SHA-256 drifted")
        schema = _ENTRY_SCHEMAS[name]
        _validate_artifact_payload(raw, expected_schema=schema)
        return TransportArtifact(
            name=name,
            schema=schema,
            raw_bytes=raw,
            external_complete_file_sha256=identity.sha256,
        )
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        os.close(parent_fd)


PR_GET_DUMPABLE = 3
PR_SET_DUMPABLE = 4


def _prctl(
    option: int,
    arg2: int = 0,
    arg3: int = 0,
    arg4: int = 0,
    arg5: int = 0,
) -> int:
    if platform.system() != "Linux":
        raise OSError(errno.ENOTSUP, "Linux prctl is required")
    libc = ctypes.CDLL(None, use_errno=True)
    prctl = libc.prctl
    prctl.argtypes = (
        ctypes.c_int,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_ulong,
    )
    prctl.restype = ctypes.c_int
    result = prctl(option, arg2, arg3, arg4, arg5)
    if result == -1:
        error_code = ctypes.get_errno()
        raise OSError(error_code, os.strerror(error_code))
    return int(result)


def _proc_start_time(pid: int, *, proc_root: Path = Path("/proc")) -> int:
    raw = (proc_root / str(pid) / "stat").read_text(encoding="ascii")
    right = raw.rfind(")")
    if right < 0:
        raise RuntimeError("/proc stat command field is malformed")
    fields = raw[right + 2 :].split()
    if len(fields) < 20 or not fields[19].isdecimal():
        raise RuntimeError("/proc stat start time is malformed")
    return int(fields[19])


def set_runner_nondumpable(
    *,
    prctl_call: Callable[[int, int, int, int, int], int] = _prctl,
    proc_root: Path = Path("/proc"),
) -> dict[str, Any]:
    """Set and verify PR_SET_DUMPABLE=0 before evaluator artifacts load."""

    result = prctl_call(PR_SET_DUMPABLE, 0, 0, 0, 0)
    if result != 0:
        raise RuntimeError("PR_SET_DUMPABLE returned a nonzero result")
    dumpable = prctl_call(PR_GET_DUMPABLE, 0, 0, 0, 0)
    if dumpable != 0:
        raise RuntimeError("PR_GET_DUMPABLE did not confirm zero")
    pid = os.getpid()
    return {
        "pid": pid,
        "proc_start_time_ticks": _proc_start_time(
            pid,
            proc_root=proc_root,
        ),
        "real_uid": os.getuid(),
        "real_gid": os.getgid(),
        "pr_get_dumpable": dumpable,
    }


def capture_process_namespace_identity(
    pid: int,
    *,
    proc_root: Path = Path("/proc"),
) -> dict[str, str]:
    process_id = _plain_int(pid, name="namespace pid", minimum=1)
    result = {
        name: os.readlink(proc_root / str(process_id) / "ns" / name)
        for name in ("user", "mnt", "net", "pid")
    }
    if any(not value for value in result.values()):
        raise ValueError("process namespace identity is empty")
    return result


def build_sacrificial_role_parameters(
    *,
    runner_identity: Mapping[str, Any],
    selected_cpu: int,
    output_root_abs: Path,
    evaluator_probe_abs: Path,
    quarantined_spool_probe_abs: Path,
    proc_root: Path = Path("/proc"),
) -> dict[str, Any]:
    _exact_keys(
        runner_identity,
        {
            "pid",
            "proc_start_time_ticks",
            "real_uid",
            "real_gid",
            "pr_get_dumpable",
        },
        name="runner dumpability identity",
    )
    if runner_identity["pr_get_dumpable"] != 0:
        raise ValueError("runner is not non-dumpable")
    pid = _plain_int(runner_identity["pid"], name="runner pid", minimum=1)
    if _proc_start_time(pid, proc_root=proc_root) != runner_identity[
        "proc_start_time_ticks"
    ]:
        raise ValueError("runner process start identity drifted")
    root = Path(output_root_abs).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("preflight output root is not a directory")
    probe_paths = []
    for value in (evaluator_probe_abs, quarantined_spool_probe_abs):
        path = Path(value).resolve(strict=True)
        if not path.is_file() or not path.is_relative_to(root):
            raise ValueError("preflight probe must be a file inside output root")
        probe_paths.append(path)
    parameters = {
        "runner_pid": pid,
        "runner_start_time_ticks": runner_identity["proc_start_time_ticks"],
        "runner_real_uid": runner_identity["real_uid"],
        "runner_real_gid": runner_identity["real_gid"],
        "runner_namespace_identity": capture_process_namespace_identity(
            pid,
            proc_root=proc_root,
        ),
        "selected_cpu": _plain_int(selected_cpu, name="selected CPU"),
        "output_root_abs": str(root),
        "evaluator_probe_abs": str(probe_paths[0]),
        "quarantined_spool_probe_abs": str(probe_paths[1]),
    }
    _validate_sacrificial_parameters(parameters)
    return parameters


_CHILD_ENVIRONMENT = " ".join(
    (
        "CUDA_VISIBLE_DEVICES=",
        "PYTHONNOUSERSITE=1",
        "PYTHONDONTWRITEBYTECODE=1",
        "PYTHONHASHSEED=0",
        "TZ=UTC",
        "OMP_NUM_THREADS=1",
        "OPENBLAS_NUM_THREADS=1",
        "MKL_NUM_THREADS=1",
        "NUMEXPR_NUM_THREADS=1",
        "BLIS_NUM_THREADS=1",
    )
)


_SYSTEMD_PROPERTY_ORDER = (
    "Type",
    "RemainAfterExit",
    "Restart",
    "DynamicUser",
    "SupplementaryGroups",
    "PrivateUsers",
    "ProtectSystem",
    "ProtectHome",
    "ReadOnlyPaths",
    "InaccessiblePaths",
    "WorkingDirectory",
    "NoNewPrivileges",
    "PrivateTmp",
    "PrivateDevices",
    "PrivateNetwork",
    "RestrictSUIDSGID",
    "CPUAffinity",
    "LimitCORE",
    "TimeoutStartFailureMode",
    "TimeoutStopSec",
    "KillMode",
    "MemoryAccounting",
    "TasksAccounting",
    "RuntimeDirectory",
    "RuntimeDirectoryMode",
    "RuntimeDirectoryPreserve",
    "MemoryMax",
    "MemorySwapMax",
    "TasksMax",
    "TimeoutStartSec",
    "RuntimeMaxSec",
    "LimitFSIZE",
    "StandardInput",
    "StandardOutput",
    "StandardError",
    "Environment",
    "UnsetEnvironment",
    "ExecStopPost",
)


_FROZEN_CHILD_ENVIRONMENT = dict(
    item.split("=", 1) for item in _CHILD_ENVIRONMENT.split(" ")
)


def _read_proc_status_fields(
    *,
    pid: int,
    proc_root: Path = Path("/proc"),
) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in (proc_root / str(pid) / "status").read_text(
        encoding="ascii"
    ).splitlines():
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        if name in fields:
            raise ValueError("proc status contains a duplicate field")
        fields[name] = value.strip()
    return fields


_SACRIFICIAL_ATTACK_PROBES = (
    "output_root_open",
    "evaluator_open",
    "prior_spool_open",
    "runner_proc_root_open",
    "runner_proc_fd_open",
    "runner_proc_mem_open",
    "ptrace_seize",
    "process_vm_readv",
)
_DENIAL_ERRNOS = frozenset({errno.EACCES, errno.EPERM})


def _probe_row(
    *,
    probe: str,
    target: str,
    result: int,
    error_code: int | None,
) -> dict[str, Any]:
    if result >= 0:
        outcome = "accessible"
        error_code = None
    elif error_code in _DENIAL_ERRNOS:
        outcome = "denied"
    else:
        outcome = "error"
    return {
        "probe": probe,
        "target": target,
        "outcome": outcome,
        "errno": error_code,
    }


def _probe_open_denial(
    probe: str,
    target: Path,
    *,
    directory: bool = False,
) -> dict[str, Any]:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    if directory:
        flags |= os.O_DIRECTORY
    try:
        fd = os.open(target, flags)
    except OSError as exc:
        return _probe_row(
            probe=probe,
            target=str(target),
            result=-1,
            error_code=exc.errno,
        )
    else:
        os.close(fd)
        return _probe_row(
            probe=probe,
            target=str(target),
            result=0,
            error_code=None,
        )


class _IOVec(ctypes.Structure):
    _fields_ = [("iov_base", ctypes.c_void_p), ("iov_len", ctypes.c_size_t)]


def _run_sacrificial_attack_probes(
    parameters: Mapping[str, Any],
    *,
    proc_root: Path = Path("/proc"),
) -> list[dict[str, Any]]:
    _validate_sacrificial_parameters(parameters)
    runner_pid = parameters["runner_pid"]
    rows = [
        _probe_open_denial(
            "output_root_open",
            Path(parameters["output_root_abs"]),
            directory=True,
        ),
        _probe_open_denial(
            "evaluator_open",
            Path(parameters["evaluator_probe_abs"]),
        ),
        _probe_open_denial(
            "prior_spool_open",
            Path(parameters["quarantined_spool_probe_abs"]),
        ),
        _probe_open_denial(
            "runner_proc_root_open",
            proc_root / str(runner_pid) / "root",
            directory=True,
        ),
        _probe_open_denial(
            "runner_proc_fd_open",
            proc_root / str(runner_pid) / "fd",
            directory=True,
        ),
        _probe_open_denial(
            "runner_proc_mem_open",
            proc_root / str(runner_pid) / "mem",
        ),
    ]
    libc = ctypes.CDLL(None, use_errno=True)
    ptrace = libc.ptrace
    ptrace.argtypes = (
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_void_p,
        ctypes.c_void_p,
    )
    ptrace.restype = ctypes.c_long
    ctypes.set_errno(0)
    ptrace_result = int(ptrace(0x4206, runner_pid, None, None))
    ptrace_errno = ctypes.get_errno() if ptrace_result < 0 else None
    if ptrace_result >= 0:
        ptrace(17, runner_pid, None, None)
    rows.append(
        _probe_row(
            probe="ptrace_seize",
            target=f"pid:{runner_pid}",
            result=ptrace_result,
            error_code=ptrace_errno,
        )
    )
    local_byte = ctypes.c_ubyte()
    local = _IOVec(ctypes.addressof(local_byte), 1)
    remote = _IOVec(0, 1)
    process_vm_readv = libc.process_vm_readv
    process_vm_readv.argtypes = (
        ctypes.c_int,
        ctypes.POINTER(_IOVec),
        ctypes.c_ulong,
        ctypes.POINTER(_IOVec),
        ctypes.c_ulong,
        ctypes.c_ulong,
    )
    process_vm_readv.restype = ctypes.c_ssize_t
    ctypes.set_errno(0)
    vm_result = int(
        process_vm_readv(
            runner_pid,
            ctypes.byref(local),
            1,
            ctypes.byref(remote),
            1,
            0,
        )
    )
    vm_errno = ctypes.get_errno() if vm_result < 0 else None
    rows.append(
        _probe_row(
            probe="process_vm_readv",
            target=f"pid:{runner_pid}",
            result=vm_result,
            error_code=vm_errno,
        )
    )
    return rows


def _status_first_unsigned(
    status: Mapping[str, str],
    name: str,
) -> int:
    fields = status.get(name, "").split()
    if not fields or not fields[0].isdecimal():
        raise ValueError(f"proc status {name} is malformed")
    return int(fields[0])


def build_sacrificial_preflight_core(
    *,
    parameters: Mapping[str, Any],
    proc_root: Path = Path("/proc"),
    environment: Mapping[str, str] | None = None,
    probe_runner: Callable[
        [Mapping[str, Any]], Sequence[Mapping[str, Any]]
    ] | None = None,
) -> dict[str, Any]:
    """Record child-local isolation facts without scientific input."""

    _validate_sacrificial_parameters(parameters)
    pid = os.getpid()
    status = _read_proc_status_fields(pid=pid, proc_root=proc_root)
    runner_pid = parameters["runner_pid"]
    runner_status = _read_proc_status_fields(
        pid=runner_pid,
        proc_root=proc_root,
    )
    source_environment = os.environ if environment is None else environment
    stdio = []
    for fd in (0, 1, 2):
        observed = os.fstat(fd)
        stdio.append(
            {
                "fd": fd,
                "st_dev": int(observed.st_dev),
                "st_ino": int(observed.st_ino),
                "st_mode": int(observed.st_mode),
                "st_nlink": int(observed.st_nlink),
                "st_uid": int(observed.st_uid),
                "is_regular": stat.S_ISREG(observed.st_mode),
            }
        )
    execute_probes = (
        (lambda value: _run_sacrificial_attack_probes(value, proc_root=proc_root))
        if probe_runner is None
        else probe_runner
    )
    attack_probes = [dict(row) for row in execute_probes(parameters)]
    core = with_result_projection(
        {
            "schema": SACRIFICIAL_PREFLIGHT_SCHEMA,
            "status": "observed",
            "runner_lineage": {
                "pid": runner_pid,
                "proc_start_time_ticks": _proc_start_time(
                    runner_pid,
                    proc_root=proc_root,
                ),
                "real_uid": _status_first_unsigned(runner_status, "Uid"),
                "real_gid": _status_first_unsigned(runner_status, "Gid"),
            },
            "process_identity": {
                "pid": pid,
                "parent_pid": os.getppid(),
                "real_uid": os.getuid(),
                "effective_uid": os.geteuid(),
                "real_gid": os.getgid(),
                "effective_gid": os.getegid(),
                "supplementary_gids": sorted(os.getgroups()),
                "working_directory": str(Path.cwd().resolve(strict=True)),
                "cpu_affinity": sorted(os.sched_getaffinity(0)),
            },
            "stdio_identity": stdio,
            "namespace_identity": capture_process_namespace_identity(
                pid,
                proc_root=proc_root,
            ),
            "proc_security": {
                name: status.get(name, "")
                for name in ("NoNewPrivs", "Seccomp", "Seccomp_filters")
            },
            "environment_contract": {
                "configured_values": {
                    name: source_environment.get(name)
                    for name in _FROZEN_CHILD_ENVIRONMENT
                },
                "pythonpath_present": "PYTHONPATH" in source_environment,
            },
            "attack_probes": attack_probes,
        }
    )
    validate_sacrificial_preflight_core(core)
    return core


def validate_sacrificial_preflight_core(
    core: Mapping[str, Any],
) -> None:
    _exact_keys(
        core,
        {
            "schema",
            "status",
            "runner_lineage",
            "process_identity",
            "stdio_identity",
            "namespace_identity",
            "proc_security",
            "environment_contract",
            "attack_probes",
            "result_projection_sha256",
        },
        name="sacrificial preflight core",
    )
    if (
        core["schema"] != SACRIFICIAL_PREFLIGHT_SCHEMA
        or core["status"] != "observed"
    ):
        raise ValueError("sacrificial preflight identity drifted")
    runner = core["runner_lineage"]
    _exact_keys(
        runner,
        {"pid", "proc_start_time_ticks", "real_uid", "real_gid"},
        name="sacrificial runner lineage",
    )
    for name, value in runner.items():
        _plain_int(
            value,
            name=f"sacrificial runner {name}",
            minimum=1 if name in {"pid", "proc_start_time_ticks"} else 0,
        )
    process = core["process_identity"]
    expected_process = {
        "pid",
        "parent_pid",
        "real_uid",
        "effective_uid",
        "real_gid",
        "effective_gid",
        "supplementary_gids",
        "working_directory",
        "cpu_affinity",
    }
    _exact_keys(process, expected_process, name="sacrificial process")
    excluded = {"supplementary_gids", "working_directory", "cpu_affinity"}
    for name in expected_process - excluded:
        _plain_int(process[name], name=f"sacrificial {name}")
    gids = process["supplementary_gids"]
    if not isinstance(gids, list):
        raise ValueError("sacrificial supplementary gids are invalid")
    for gid in gids:
        _plain_int(gid, name="sacrificial supplementary gid")
    if gids != sorted(set(gids)):
        raise ValueError("sacrificial supplementary gids are invalid")
    affinity = process["cpu_affinity"]
    if not isinstance(affinity, list) or not affinity:
        raise ValueError("sacrificial affinity is invalid")
    for cpu in affinity:
        _plain_int(cpu, name="sacrificial affinity CPU")
    if affinity != sorted(set(affinity)):
        raise ValueError("sacrificial affinity is invalid")
    if not isinstance(process["working_directory"], str) or not Path(
        process["working_directory"]
    ).is_absolute():
        raise ValueError("sacrificial working directory is invalid")
    stdio = core["stdio_identity"]
    if not isinstance(stdio, list) or len(stdio) != 3:
        raise ValueError("sacrificial stdio identity is invalid")
    stdio_keys = {
        "fd",
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_uid",
        "is_regular",
    }
    for expected_fd, row in enumerate(stdio):
        _exact_keys(row, stdio_keys, name="sacrificial stdio row")
        if row["fd"] != expected_fd or not isinstance(
            row["is_regular"], bool
        ):
            raise ValueError("sacrificial stdio binding drifted")
        for name in stdio_keys - {"fd", "is_regular"}:
            _plain_int(row[name], name=f"sacrificial stdio {name}")
    namespaces = core["namespace_identity"]
    _exact_keys(
        namespaces,
        {"user", "mnt", "net", "pid"},
        name="sacrificial namespaces",
    )
    if any(not isinstance(value, str) or not value for value in namespaces.values()):
        raise ValueError("sacrificial namespace identity is invalid")
    security = core["proc_security"]
    _exact_keys(
        security,
        {"NoNewPrivs", "Seccomp", "Seccomp_filters"},
        name="sacrificial proc security",
    )
    if any(not isinstance(value, str) for value in security.values()):
        raise ValueError("sacrificial proc security is invalid")
    environment_contract = core["environment_contract"]
    _exact_keys(
        environment_contract,
        {"configured_values", "pythonpath_present"},
        name="sacrificial environment contract",
    )
    configured = environment_contract["configured_values"]
    _exact_keys(
        configured,
        set(_FROZEN_CHILD_ENVIRONMENT),
        name="sacrificial environment",
    )
    if any(
        value is not None and not isinstance(value, str)
        for value in configured.values()
    ):
        raise ValueError("sacrificial configured environment is invalid")
    if not isinstance(environment_contract["pythonpath_present"], bool):
        raise ValueError("sacrificial environment contract is invalid")
    probes = core["attack_probes"]
    if not isinstance(probes, list) or len(probes) != len(
        _SACRIFICIAL_ATTACK_PROBES
    ):
        raise ValueError("sacrificial attack-probe sequence is invalid")
    for expected_probe, row in zip(_SACRIFICIAL_ATTACK_PROBES, probes):
        _exact_keys(
            row,
            {"probe", "target", "outcome", "errno"},
            name="sacrificial attack probe",
        )
        if row["probe"] != expected_probe:
            raise ValueError("sacrificial attack-probe order drifted")
        if not isinstance(row["target"], str) or not row["target"]:
            raise ValueError("sacrificial attack-probe target is invalid")
        if row["outcome"] not in {"denied", "accessible", "error"}:
            raise ValueError("sacrificial attack-probe outcome is invalid")
        if row["errno"] is not None:
            _plain_int(row["errno"], name="sacrificial attack errno")
    validate_result_projection(core)


@dataclass(frozen=True)
class DispatchRequest:
    """Validated child identity before any scientific owner is imported."""

    role: str
    launch_id: str
    owner_path: Path
    expected_core_schema: str | None
    stdin_max_bytes: int
    core_max_bytes: int
    trailer_max_bytes: int
    limit_fsize_bytes: int


@dataclass(frozen=True)
class PreparedDispatch:
    """Pure dispatch decision plus authenticated stdin transport."""

    request: DispatchRequest
    input_transport: ParsedInputTransport

    @property
    def run_partition(self) -> str:
        return self.input_transport.manifest["run_partition"]


def resolve_role_owner(role: str) -> Path:
    """Resolve the frozen role owner without importing or executing it."""

    if not isinstance(role, str) or role not in PRODUCTION_ROLES:
        raise ValueError("role is not a production role")
    candidate = _SCRIPT_DIR / _ROLE_WORKER_FILENAMES[role]
    try:
        owner = candidate.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("role owner is absent") from exc
    if owner.parent != _SCRIPT_DIR or not owner.is_file():
        raise RuntimeError("role owner escaped the exact script directory")
    return owner


def parse_dispatch_argv(argv: Sequence[str]) -> DispatchRequest:
    """Parse the exact ``ROLE LAUNCH_ID`` child command line."""

    if isinstance(argv, (str, bytes, bytearray)):
        raise ValueError("dispatch argv must be a two-item sequence")
    arguments = tuple(argv)
    if len(arguments) != 2 or any(type(item) is not str for item in arguments):
        raise ValueError("dispatch argv must be exactly ROLE LAUNCH_ID")
    role, launch_id = arguments
    if not role.isascii() or role not in PRODUCTION_ROLES:
        raise ValueError("dispatch role is invalid")
    if (
        not launch_id.isascii()
        or _LAUNCH_ID_RE.fullmatch(launch_id) is None
    ):
        raise ValueError("dispatch launch_id is invalid")
    core_max, trailer_max, limit_fsize = frame_limits(role)
    return DispatchRequest(
        role=role,
        launch_id=launch_id,
        owner_path=resolve_role_owner(role),
        expected_core_schema=ROLE_CORE_SCHEMAS[role],
        stdin_max_bytes=_stdin_cap(role),
        core_max_bytes=core_max,
        trailer_max_bytes=trailer_max,
        limit_fsize_bytes=limit_fsize,
    )


def prepare_child_dispatch(
    argv: Sequence[str],
    *,
    stdin_fd: int = 0,
) -> PreparedDispatch:
    """Authenticate child identity and stdin without executing science."""

    request = parse_dispatch_argv(argv)
    parsed = read_input_transport_fd(
        stdin_fd,
        expected_role=request.role,
    )
    return PreparedDispatch(
        request=request,
        input_transport=parsed,
    )


@dataclass(frozen=True)
class DispatchResult:
    """One validated role result ready for the raw stdout barrier."""

    request: DispatchRequest
    core_bytes: bytes
    trailer_bytes: bytes
    core: dict[str, Any]
    trailer: dict[str, Any]
    framed_bytes: bytes


_ENVELOPE_ROLES: Mapping[str, str] = {
    "sdim_inventory_envelope": SDIM_INVENTORY_COLLECTOR,
    "neutral_fixture_envelope": NEUTRAL_FIXTURE_EMITTER,
    "dense_envelope": DENSE_REFERENCE,
    "plain_input1_envelope": PLAIN_EVIDENCE,
    "plain_input2_envelope": PLAIN_EVIDENCE,
    "gc_input1_envelope": GCAPEPS_EVIDENCE,
    "gc_input2_envelope": GCAPEPS_EVIDENCE,
    "sdim_envelope": SDIM_COMPUTATION,
}


def _validate_prepared_dispatch(
    prepared: PreparedDispatch,
) -> Mapping[str, Any]:
    if not isinstance(prepared, PreparedDispatch):
        raise TypeError("prepared dispatch has the wrong type")
    request = parse_dispatch_argv(
        [prepared.request.role, prepared.request.launch_id]
    )
    if request != prepared.request:
        raise ValueError("prepared dispatch request identity drifted")
    manifest = prepared.input_transport.manifest
    if manifest["role"] != request.role:
        raise ValueError("prepared dispatch role differs from stdin")
    expected_names = expected_entry_sequence(
        manifest["run_partition"],
        request.role,
    )
    actual_names = tuple(
        name for name, _ in prepared.input_transport.artifacts
    )
    if actual_names != expected_names:
        raise ValueError("prepared dispatch artifact sequence drifted")
    validate_role_parameters(
        manifest["run_partition"],
        request.role,
        manifest["role_parameters"],
    )
    return manifest["role_parameters"]


def _dispatch_artifact_payload(
    prepared: PreparedDispatch,
    name: str,
) -> dict[str, Any]:
    artifacts = prepared.input_transport.artifact_map()
    if name not in artifacts:
        raise ValueError(f"dispatch input artifact is absent: {name}")
    payload = parse_canonical_json_object(artifacts[name])
    expected_schema = _ENTRY_SCHEMAS.get(name)
    if expected_schema is None:
        raise ValueError(f"dispatch input artifact is unknown: {name}")
    _validate_artifact_payload(
        artifacts[name],
        expected_schema=expected_schema,
    )
    return payload


def _completed_envelope_core(
    prepared: PreparedDispatch,
    name: str,
    *,
    expected_partition: str,
) -> dict[str, Any]:
    if name not in _ENVELOPE_ROLES:
        raise ValueError("dispatch envelope name is not registered")
    payload = _dispatch_artifact_payload(prepared, name)
    if payload["terminal_kind"] != "completed_result":
        raise ValueError(f"dispatch predecessor is not completed: {name}")
    if payload["role"] != _ENVELOPE_ROLES[name]:
        raise ValueError(f"dispatch predecessor role mismatch: {name}")
    if payload["run_partition"] != expected_partition:
        raise ValueError(f"dispatch predecessor partition mismatch: {name}")
    core = payload["core"]
    if not isinstance(core, Mapping):
        raise ValueError(f"dispatch predecessor has no core: {name}")
    return dict(core)


def _load_dispatch_owner(request: DispatchRequest) -> Any:
    """Import only the already-resolved role owner, after stdin validation."""

    path = resolve_role_owner(request.role)
    if path != request.owner_path:
        raise ValueError("dispatch owner path identity drifted")
    module_name = (
        f"_gcapeps_fm_dispatch_{request.role}_{uuid.uuid4().hex}"
    )
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the registered dispatch owner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def _standard_result_from_core_builder(
    *,
    builder: Callable[[], Mapping[str, Any]],
    root_span_id: str,
    root_scope: str,
    compute_span_id: str,
    compute_scope: str,
    lane: str | None,
    kind: str,
) -> dict[str, Any]:
    """Narrow adapter for owners that currently expose a core builder."""

    timer = _TIMING.LayeredTimer()
    with timer.span(
        root_span_id,
        scope=root_scope,
        kind="worker",
        lane=lane,
    ):
        with timer.span(
            compute_span_id,
            scope=compute_scope,
            kind=kind,
            lane=lane,
        ):
            core = builder()
            if not isinstance(core, Mapping):
                raise TypeError("dispatch core builder returned a non-object")
        with timer.span(
            f"{root_span_id}.serialize",
            scope="serialization",
            kind="canonical_core_encoding",
            lane=lane,
        ):
            core = dict(core)
            core_bytes = canonical_json_bytes(core)
    timing = timer.finish()
    trailer_bytes = _TIMING.build_late_telemetry_trailer(
        core_bytes,
        timing,
    )
    return {
        "core": core,
        "core_bytes": core_bytes,
        "timing": timing,
        "trailer_bytes": trailer_bytes,
        "framed_bytes": _TIMING.encode_two_frames(
            core_bytes,
            trailer_bytes,
        ),
    }


def _normalize_dispatch_result(
    request: DispatchRequest,
    result: Mapping[str, Any] | bytes,
) -> DispatchResult:
    if isinstance(result, bytes):
        framed = result
    else:
        if not isinstance(result, Mapping) or set(result) != {
            "core",
            "core_bytes",
            "timing",
            "trailer_bytes",
            "framed_bytes",
        }:
            raise ValueError("owner result has the wrong exact key set")
        framed = result["framed_bytes"]
        if not isinstance(framed, bytes):
            raise TypeError("owner framed result is not bytes")
    decoded = decode_clean_worker_frames(
        framed,
        role=request.role,
        expected_core_schema=request.expected_core_schema,
    )
    if not isinstance(result, bytes):
        if result["core_bytes"] != decoded.core_bytes:
            raise ValueError("owner core bytes differ from framed bytes")
        if result["trailer_bytes"] != decoded.trailer_bytes:
            raise ValueError("owner trailer bytes differ from framed bytes")
        if result["core"] != decoded.core:
            raise ValueError("owner core object differs from framed bytes")
        if result["timing"] != decoded.trailer["timing"]:
            raise ValueError("owner timing differs from framed trailer")
    return DispatchResult(
        request=request,
        core_bytes=decoded.core_bytes,
        trailer_bytes=decoded.trailer_bytes,
        core=decoded.core,
        trailer=decoded.trailer,
        framed_bytes=framed,
    )


def invoke_prepared_dispatch(
    prepared: PreparedDispatch,
    *,
    owner_loader: Callable[[DispatchRequest], Any] | None = None,
    sacrificial_probe_runner: Callable[
        [Mapping[str, Any]], Sequence[Mapping[str, Any]]
    ] | None = None,
) -> DispatchResult:
    """Invoke exactly one owner using only authenticated in-memory artifacts."""

    parameters = _validate_prepared_dispatch(prepared)
    request = prepared.request
    role = request.role
    partition = prepared.run_partition
    names = tuple(name for name, _ in prepared.input_transport.artifacts)

    if "manager_preflight_receipt" in names:
        _dispatch_artifact_payload(prepared, "manager_preflight_receipt")
    if "target_amendment" in names:
        _dispatch_artifact_payload(prepared, "target_amendment")
    inventory_core: dict[str, Any] | None = None
    if "sdim_inventory_envelope" in names:
        inventory_core = _completed_envelope_core(
            prepared,
            "sdim_inventory_envelope",
            expected_partition=BOOTSTRAP,
        )
    fixture: dict[str, Any] | None = None
    if "neutral_fixture_envelope" in names:
        fixture = _completed_envelope_core(
            prepared,
            "neutral_fixture_envelope",
            expected_partition=partition,
        )

    if role == SACRIFICIAL_MANAGER_PREFLIGHT:
        result = _standard_result_from_core_builder(
            builder=lambda: build_sacrificial_preflight_core(
                parameters=parameters,
                probe_runner=sacrificial_probe_runner,
            ),
            root_span_id="sacrificial_preflight.root",
            root_scope="sacrificial_preflight_worker_total",
            compute_span_id="sacrificial_preflight.observe",
            compute_scope="security_observation",
            lane="manager_preflight",
            kind="security_preflight",
        )
        return _normalize_dispatch_result(request, result)
    load_owner = _load_dispatch_owner if owner_loader is None else owner_loader
    owner = load_owner(request)

    if role == SDIM_INVENTORY_COLLECTOR:
        result = owner.run_inventory_worker()
    elif role == NEUTRAL_FIXTURE_EMITTER:
        def build_fixture() -> Mapping[str, Any]:
            core = owner.build_fixture(
                run_partition=partition,
                width=parameters["width"],
                rounds=parameters["rounds"],
                axis_family=parameters["axis_family"],
                p_event_numerator=parameters["p_event_numerator"],
                seed=parameters["seed"],
                gamma_index=parameters["gamma_index"],
                run_blpensemble=parameters["run_blpensemble"],
            )
            owner.validate_fixture(core)
            return core

        result = _standard_result_from_core_builder(
            builder=build_fixture,
            root_span_id="neutral_fixture.root",
            root_scope="neutral_fixture_worker_total",
            compute_span_id="neutral_fixture.build",
            compute_scope="neutral_fixture_construction",
            lane="neutral_fixture",
            kind="deterministic_fixture",
        )
    elif role == DENSE_REFERENCE:
        if fixture is None:
            raise ValueError("dense dispatch lacks a completed fixture")
        result = owner.build_framed_worker_output(fixture)
    elif role in {PLAIN_CAP_PROBE, GCAPEPS_CAP_PROBE}:
        if fixture is None:
            raise ValueError("cap-probe dispatch lacks a completed fixture")
        result = owner.run_cap_probe(fixture, input_id=parameters["input_id"])
    elif role in {PLAIN_EVIDENCE, GCAPEPS_EVIDENCE}:
        if fixture is None:
            raise ValueError("evidence dispatch lacks a completed fixture")
        result = owner.run_evidence(fixture, input_id=parameters["input_id"])
    elif role in {PLAIN_PERFORMANCE, GCAPEPS_PERFORMANCE}:
        if fixture is None:
            raise ValueError("performance dispatch lacks a completed fixture")
        result = owner.run_performance(
            fixture,
            input_id=parameters["input_id"],
        )
    elif role == SDIM_COMPUTATION:
        if fixture is None or inventory_core is None:
            raise ValueError("SDIM dispatch lacks fixture or inventory core")
        result = owner.run_frame_control_worker(
            fixture,
            inventory_core=inventory_core,
        )
    elif role == TERMINAL_COMPARATOR:
        if fixture is None:
            raise ValueError("comparator dispatch lacks a completed fixture")
        comparator_kwargs = {
            "fixture": fixture,
            "dense_core": _completed_envelope_core(
                prepared, "dense_envelope", expected_partition=partition
            ),
            "plain_input1_core": _completed_envelope_core(
                prepared, "plain_input1_envelope", expected_partition=partition
            ),
            "plain_input2_core": _completed_envelope_core(
                prepared, "plain_input2_envelope", expected_partition=partition
            ),
            "gcapeps_input1_core": _completed_envelope_core(
                prepared, "gc_input1_envelope", expected_partition=partition
            ),
            "gcapeps_input2_core": _completed_envelope_core(
                prepared, "gc_input2_envelope", expected_partition=partition
            ),
            "sdim_core": _completed_envelope_core(
                prepared, "sdim_envelope", expected_partition=partition
            ),
        }
        if hasattr(owner, "run_comparator_worker"):
            result = owner.run_comparator_worker(
                **comparator_kwargs,
                timing_module=_TIMING,
            )
        elif hasattr(owner, "build_comparator_core"):
            result = _standard_result_from_core_builder(
                builder=lambda: owner.build_comparator_core(
                    **comparator_kwargs
                ),
                root_span_id="terminal_comparator.root",
                root_scope="terminal_comparator_total",
                compute_span_id="terminal_comparator.compare",
                compute_scope="independent_metric_comparison",
                lane="comparator",
                kind="terminal_comparison",
            )
        else:
            raise RuntimeError("comparator owner has no dispatch callable")
    else:
        raise AssertionError("registered dispatch role has no owner adapter")
    return _normalize_dispatch_result(request, result)


def emit_dispatch_result_and_self_stop(
    result: DispatchResult,
    *,
    stdout_fd: int = 1,
    process_id: int | None = None,
    stop_process: Callable[[int, int], Any] = os.kill,
) -> None:
    """Write, fsync, verify, and enter the supervisor's stopped barrier."""

    if not isinstance(result, DispatchResult):
        raise TypeError("dispatch result has the wrong type")
    fd = _plain_int(stdout_fd, name="stdout fd")
    identity = os.fstat(fd)
    if not stat.S_ISREG(identity.st_mode):
        raise ValueError("clean worker stdout must be a regular file")
    if identity.st_size != 0 or os.lseek(fd, 0, os.SEEK_CUR) != 0:
        raise ValueError("clean worker stdout must be a fresh empty file")
    _normalize_dispatch_result(result.request, result.framed_bytes)
    cursor = 0
    while cursor < len(result.framed_bytes):
        written = os.write(fd, result.framed_bytes[cursor:])
        if written <= 0:
            raise RuntimeError("clean worker stdout write made no progress")
        cursor += written
    os.fsync(fd)
    written_identity = os.fstat(fd)
    if written_identity.st_size != len(result.framed_bytes):
        raise RuntimeError("clean worker stdout size changed after fsync")
    pid = os.getpid() if process_id is None else _plain_int(
        process_id,
        name="self-stop pid",
        minimum=1,
    )
    stop_process(pid, signal.SIGSTOP)


_SPOOL_FILENAMES = (
    "fixture.stdin",
    "raw.stdout",
    "raw.stderr",
    "failure_snapshot.copy",
)


@dataclass(frozen=True)
class SealedInodeIdentity:
    name: str
    st_dev: int
    st_ino: int
    st_mode: int
    st_nlink: int
    st_uid: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "st_dev": self.st_dev,
            "st_ino": self.st_ino,
            "st_mode": self.st_mode,
            "st_nlink": self.st_nlink,
            "st_uid": self.st_uid,
        }


@dataclass
class SealedLaunchSpool:
    launch_id: str
    parent_path: Path
    spool_path: Path
    parent_fd: int
    spool_fd: int
    file_fds: dict[str, int]
    identities: dict[str, SealedInodeIdentity]
    input_transport: ParsedInputTransport
    moved: bool = False
    closed: bool = False

    def close(self) -> None:
        if self.closed:
            return
        for fd in self.file_fds.values():
            os.close(fd)
        os.close(self.spool_fd)
        os.close(self.parent_fd)
        self.closed = True


@dataclass(frozen=True)
class QuarantinedSpool:
    path: Path
    relative_path: str
    raw_files: Mapping[str, bytes]


def _sealed_inode_identity(name: str, fd: int) -> SealedInodeIdentity:
    observed = os.fstat(fd)
    if (
        not stat.S_ISREG(observed.st_mode)
        or stat.S_IMODE(observed.st_mode) != 0o600
        or observed.st_nlink != 1
        or observed.st_uid != os.geteuid()
    ):
        raise ValueError(f"sealed spool file identity is invalid: {name}")
    return SealedInodeIdentity(
        name=name,
        st_dev=int(observed.st_dev),
        st_ino=int(observed.st_ino),
        st_mode=int(observed.st_mode),
        st_nlink=int(observed.st_nlink),
        st_uid=int(observed.st_uid),
    )


def _require_same_sealed_inode(
    fd: int,
    expected: SealedInodeIdentity,
) -> os.stat_result:
    observed = os.fstat(fd)
    if (
        not stat.S_ISREG(observed.st_mode)
        or observed.st_dev != expected.st_dev
        or observed.st_ino != expected.st_ino
        or observed.st_mode != expected.st_mode
        or observed.st_nlink != expected.st_nlink
        or observed.st_uid != expected.st_uid
    ):
        raise ValueError(f"sealed spool inode drifted: {expected.name}")
    return observed


def _open_exact_parent(path: Path, *, mode: int) -> tuple[Path, int]:
    lexical = Path(path)
    if not lexical.is_absolute():
        raise ValueError("sealed directory path must be absolute")
    resolved = lexical.resolve(strict=True)
    if resolved != Path(os.path.abspath(lexical)):
        raise ValueError("sealed directory path contains a symlink")
    fd = os.open(
        resolved,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    observed = os.fstat(fd)
    if (
        not stat.S_ISDIR(observed.st_mode)
        or stat.S_IMODE(observed.st_mode) != mode
        or observed.st_uid != os.geteuid()
    ):
        os.close(fd)
        raise ValueError("sealed directory owner or mode is invalid")
    return resolved, fd


def create_sealed_launch_spool(
    *,
    spool_parent_abs: Path,
    launch_id: str,
    input_transport_raw: bytes,
    expected_partition: str,
    expected_role: str,
) -> SealedLaunchSpool:
    """Create and reauthenticate the sole four-file child transport spool."""

    if _LAUNCH_ID_RE.fullmatch(launch_id) is None:
        raise ValueError("spool launch id is invalid")
    if not isinstance(input_transport_raw, bytes):
        raise TypeError("sealed stdin transport must be bytes")
    parsed_memory = parse_input_transport(
        input_transport_raw,
        expected_partition=expected_partition,
        expected_role=expected_role,
    )
    parent_path, parent_fd = _open_exact_parent(
        spool_parent_abs,
        mode=0o700,
    )
    spool_fd = -1
    created = False
    opened_fds: dict[str, int] = {}
    try:
        if os.listdir(parent_fd):
            raise ValueError("sealed spool parent is not empty")
        os.mkdir(launch_id, mode=0o700, dir_fd=parent_fd)
        created = True
        spool_fd = os.open(
            launch_id,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=parent_fd,
        )
        spool_stat = os.fstat(spool_fd)
        if (
            not stat.S_ISDIR(spool_stat.st_mode)
            or stat.S_IMODE(spool_stat.st_mode) != 0o700
            or spool_stat.st_uid != os.geteuid()
        ):
            raise ValueError("launch spool directory identity is invalid")
        for name in _SPOOL_FILENAMES:
            fd = os.open(
                name,
                os.O_RDWR
                | os.O_CREAT
                | os.O_EXCL
                | os.O_NOFOLLOW
                | os.O_CLOEXEC,
                0o600,
                dir_fd=spool_fd,
            )
            try:
                os.fchmod(fd, 0o600)
                if name == "fixture.stdin":
                    cursor = 0
                    while cursor < len(input_transport_raw):
                        written = os.write(fd, input_transport_raw[cursor:])
                        if written <= 0:
                            raise RuntimeError("sealed stdin write stalled")
                        cursor += written
                os.fsync(fd)
            finally:
                os.close(fd)
        os.fsync(spool_fd)
        os.fsync(parent_fd)
        if tuple(sorted(os.listdir(spool_fd))) != tuple(
            sorted(_SPOOL_FILENAMES)
        ):
            raise ValueError("launch spool exact child set drifted")
        identities: dict[str, SealedInodeIdentity] = {}
        for name in _SPOOL_FILENAMES:
            access_mode = (
                os.O_RDWR
                if name == "failure_snapshot.copy"
                else os.O_RDONLY
            )
            fd = os.open(
                name,
                access_mode | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                dir_fd=spool_fd,
            )
            opened_fds[name] = fd
            identities[name] = _sealed_inode_identity(name, fd)
        parsed_fd = read_input_transport_fd(
            opened_fds["fixture.stdin"],
            expected_role=expected_role,
            expected_partition=expected_partition,
        )
        if (
            parsed_fd.raw_byte_length != parsed_memory.raw_byte_length
            or parsed_fd.raw_sha256 != parsed_memory.raw_sha256
            or parsed_fd.artifacts != parsed_memory.artifacts
        ):
            raise ValueError("sealed stdin reparse differs from source bytes")
        return SealedLaunchSpool(
            launch_id=launch_id,
            parent_path=parent_path,
            spool_path=parent_path / launch_id,
            parent_fd=parent_fd,
            spool_fd=spool_fd,
            file_fds=opened_fds,
            identities=identities,
            input_transport=parsed_fd,
        )
    except BaseException:
        for fd in opened_fds.values():
            os.close(fd)
        if spool_fd >= 0:
            for name in _SPOOL_FILENAMES:
                try:
                    os.unlink(name, dir_fd=spool_fd)
                except FileNotFoundError:
                    pass
            os.close(spool_fd)
        if created:
            try:
                os.rmdir(launch_id, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
        os.close(parent_fd)
        raise


def quarantine_sealed_launch_spool(
    spool: SealedLaunchSpool,
    *,
    quarantine_parent_abs: Path,
) -> QuarantinedSpool:
    """No-replace move a completed spool and verify every retained inode."""

    if not isinstance(spool, SealedLaunchSpool) or spool.closed or spool.moved:
        raise ValueError("launch spool is not live and movable")
    quarantine_parent, quarantine_fd = _open_exact_parent(
        quarantine_parent_abs,
        mode=0o755,
    )
    destination_fd = -1
    try:
        if os.fstat(quarantine_fd).st_dev != os.fstat(spool.parent_fd).st_dev:
            raise ValueError("spool quarantine must remain on one filesystem")
        _renameat2(
            spool.parent_fd,
            os.fsencode(spool.launch_id),
            quarantine_fd,
            os.fsencode(spool.launch_id),
            _RENAME_NOREPLACE,
        )
        spool.moved = True
        os.fsync(spool.parent_fd)
        os.fsync(quarantine_fd)
        if os.listdir(spool.parent_fd):
            raise RuntimeError("outside spool parent is not empty after move")
        destination_fd = os.open(
            spool.launch_id,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=quarantine_fd,
        )
        if not _same_inode(
            os.fstat(destination_fd),
            os.fstat(spool.spool_fd),
        ):
            raise RuntimeError("quarantined spool directory identity drifted")
        if tuple(sorted(os.listdir(destination_fd))) != tuple(
            sorted(_SPOOL_FILENAMES)
        ):
            raise RuntimeError("quarantined spool child set drifted")
        raw_files: dict[str, bytes] = {}
        for name in _SPOOL_FILENAMES:
            observed = _require_same_sealed_inode(
                spool.file_fds[name],
                spool.identities[name],
            )
            raw_files[name] = _read_all_fd(
                spool.file_fds[name],
                observed.st_size,
            )
        destination = quarantine_parent / spool.launch_id
        spool.spool_path = destination
        return QuarantinedSpool(
            path=destination,
            relative_path=f"raw_spools/{spool.launch_id}",
            raw_files=raw_files,
        )
    finally:
        if destination_fd >= 0:
            os.close(destination_fd)
        os.close(quarantine_fd)


@dataclass(frozen=True)
class SystemdServiceSpec:
    launch_id: str
    role: str
    unit_name: str
    runtime_directory: str
    properties: tuple[tuple[str, str], ...]
    command: tuple[str, ...]

    def property_map(self) -> dict[str, str]:
        return dict(self.properties)


def _absolute_no_whitespace(path: Path, *, name: str) -> str:
    value = str(path)
    if not path.is_absolute() or not value or any(ch.isspace() for ch in value):
        raise ValueError(f"{name} must be an absolute whitespace-free path")
    return value


def select_benchmark_cpu(
    affinity: set[int] | frozenset[int] | None = None,
) -> int:
    """Return the preregistered minimum CPU from the supervisor affinity."""

    current = os.sched_getaffinity(0) if affinity is None else affinity
    if not isinstance(current, (set, frozenset)) or not current:
        raise ValueError("supervisor affinity must be a nonempty CPU set")
    for value in current:
        _plain_int(value, name="affinity CPU")
    return min(current)


def build_systemd_service_spec(
    *,
    launch_id: str,
    role: str,
    repository_abs: Path,
    run_output_abs: Path,
    spool_abs: Path,
    selected_cpu: int,
    repository_read_gid: int,
    python_executable: Path,
    worker_path: Path,
    snapshot_helper_path: Path = _SNAPSHOT_HELPER,
) -> SystemdServiceSpec:
    """Construct, but never execute, the exact system-manager command."""

    if _LAUNCH_ID_RE.fullmatch(launch_id) is None:
        raise ValueError("launch_id is invalid")
    if role not in PRODUCTION_ROLES:
        raise ValueError("role is not a production role")
    cpu = _plain_int(selected_cpu, name="selected CPU")
    if cpu != select_benchmark_cpu():
        raise ValueError("selected CPU is not the minimum supervisor affinity")
    gid = _plain_int(repository_read_gid, name="repository-read gid")
    repository = _absolute_no_whitespace(
        Path(repository_abs),
        name="repository",
    )
    run_output = _absolute_no_whitespace(
        Path(run_output_abs),
        name="run output",
    )
    spool = _absolute_no_whitespace(Path(spool_abs), name="spool")
    python = _absolute_no_whitespace(
        Path(python_executable),
        name="Python executable",
    )
    worker = _absolute_no_whitespace(Path(worker_path), name="worker")
    snapshot = _absolute_no_whitespace(
        Path(snapshot_helper_path),
        name="snapshot helper",
    )
    if worker != str(_SCRIPT_PATH):
        raise ValueError("worker path must be the exact supervisor dispatcher")
    resolve_role_owner(role)
    if snapshot != str(_SNAPSHOT_HELPER):
        raise ValueError("snapshot helper path drifted")
    unit_name = f"gcapeps-fm-{launch_id}.service"
    runtime_directory = f"gcapeps-fm-{launch_id}"
    core_max, trailer_max, limit_fsize = frame_limits(role)
    if limit_fsize != core_max + trailer_max + 16:
        raise AssertionError("role frame and LimitFSIZE accounting drifted")
    performance = role in {PLAIN_PERFORMANCE, GCAPEPS_PERFORMANCE}
    memory_max = 12_884_901_888 if performance else 25_769_803_776
    timeout_start = "600s" if performance else "1800s"
    values = {
        "Type": "oneshot",
        "RemainAfterExit": "yes",
        "Restart": "no",
        "DynamicUser": "yes",
        "SupplementaryGroups": str(gid),
        "PrivateUsers": "yes",
        "ProtectSystem": "strict",
        "ProtectHome": "read-only",
        "ReadOnlyPaths": repository,
        "InaccessiblePaths": run_output,
        "WorkingDirectory": repository,
        "NoNewPrivileges": "yes",
        "PrivateTmp": "yes",
        "PrivateDevices": "yes",
        "PrivateNetwork": "yes",
        "RestrictSUIDSGID": "yes",
        "CPUAffinity": str(cpu),
        "LimitCORE": "0",
        "TimeoutStartFailureMode": "kill",
        "TimeoutStopSec": "15s",
        "KillMode": "control-group",
        "MemoryAccounting": "yes",
        "TasksAccounting": "yes",
        "RuntimeDirectory": runtime_directory,
        "RuntimeDirectoryMode": "0755",
        "RuntimeDirectoryPreserve": "no",
        "MemoryMax": str(memory_max),
        "MemorySwapMax": "0",
        "TasksMax": "32",
        "TimeoutStartSec": timeout_start,
        "RuntimeMaxSec": "infinity",
        "LimitFSIZE": str(limit_fsize),
        "StandardInput": f"file:{spool}/fixture.stdin",
        "StandardOutput": f"file:{spool}/raw.stdout",
        "StandardError": f"file:{spool}/raw.stderr",
        "Environment": _CHILD_ENVIRONMENT,
        "UnsetEnvironment": "PYTHONPATH",
        "ExecStopPost": (
            f"{python} {snapshot} --launch-id {launch_id}"
        ),
    }
    properties = tuple((name, values[name]) for name in _SYSTEMD_PROPERTY_ORDER)
    command = (
        "systemd-run",
        "--system",
        "--no-block",
        "--no-ask-password",
        f"--unit={unit_name}",
        *(f"--property={name}={value}" for name, value in properties),
        "--",
        python,
        worker,
        role,
        launch_id,
    )
    spec = SystemdServiceSpec(
        launch_id=launch_id,
        role=role,
        unit_name=unit_name,
        runtime_directory=runtime_directory,
        properties=properties,
        command=command,
    )
    validate_systemd_service_spec(spec)
    return spec


def validate_systemd_service_spec(spec: SystemdServiceSpec) -> None:
    if not isinstance(spec, SystemdServiceSpec):
        raise TypeError("service spec has the wrong type")
    if _LAUNCH_ID_RE.fullmatch(spec.launch_id) is None:
        raise ValueError("service launch id is invalid")
    if spec.role not in PRODUCTION_ROLES:
        raise ValueError("service role is invalid")
    expected_unit = f"gcapeps-fm-{spec.launch_id}.service"
    expected_runtime = f"gcapeps-fm-{spec.launch_id}"
    if spec.unit_name != expected_unit or spec.runtime_directory != expected_runtime:
        raise ValueError("unit/runtime identity drifted")
    if tuple(name for name, _ in spec.properties) != _SYSTEMD_PROPERTY_ORDER:
        raise ValueError("systemd property names/order drifted")
    if len(dict(spec.properties)) != len(spec.properties):
        raise ValueError("duplicate systemd property")
    properties = spec.property_map()
    fixed = {
        "Type": "oneshot",
        "RemainAfterExit": "yes",
        "Restart": "no",
        "DynamicUser": "yes",
        "PrivateUsers": "yes",
        "ProtectSystem": "strict",
        "ProtectHome": "read-only",
        "NoNewPrivileges": "yes",
        "PrivateTmp": "yes",
        "PrivateDevices": "yes",
        "PrivateNetwork": "yes",
        "RestrictSUIDSGID": "yes",
        "LimitCORE": "0",
        "TimeoutStartFailureMode": "kill",
        "TimeoutStopSec": "15s",
        "KillMode": "control-group",
        "MemoryAccounting": "yes",
        "TasksAccounting": "yes",
        "RuntimeDirectory": expected_runtime,
        "RuntimeDirectoryMode": "0755",
        "RuntimeDirectoryPreserve": "no",
        "MemorySwapMax": "0",
        "TasksMax": "32",
        "RuntimeMaxSec": "infinity",
        "Environment": _CHILD_ENVIRONMENT,
        "UnsetEnvironment": "PYTHONPATH",
    }
    for name, expected in fixed.items():
        if properties[name] != expected:
            raise ValueError(f"systemd property drifted: {name}")
    for name in ("SupplementaryGroups", "CPUAffinity"):
        if not properties[name].isascii() or not properties[name].isdecimal():
            raise ValueError(f"{name} must be one unsigned decimal integer")
    if "AllowedCPUs" in properties:
        raise ValueError("AllowedCPUs is forbidden")
    repository = properties["WorkingDirectory"]
    if properties["ReadOnlyPaths"] != repository:
        raise ValueError("repository path properties disagree")
    for name in (
        "WorkingDirectory",
        "ReadOnlyPaths",
        "InaccessiblePaths",
    ):
        if not Path(properties[name]).is_absolute():
            raise ValueError(f"{name} must be absolute")
    standard_paths = []
    for name, filename in (
        ("StandardInput", "fixture.stdin"),
        ("StandardOutput", "raw.stdout"),
        ("StandardError", "raw.stderr"),
    ):
        value = properties[name]
        if not value.startswith("file:"):
            raise ValueError(f"{name} must use raw file transport")
        path = Path(value[5:])
        if not path.is_absolute() or path.name != filename:
            raise ValueError(f"{name} target drifted")
        standard_paths.append(path.parent)
    if len(set(standard_paths)) != 1:
        raise ValueError("standard streams do not share one spool")
    core_max, trailer_max, expected_fsize = frame_limits(spec.role)
    if int(properties["LimitFSIZE"]) != expected_fsize:
        raise ValueError("LimitFSIZE drifted")
    if expected_fsize != core_max + trailer_max + 16:
        raise AssertionError("frame limit invariant failed")
    performance = spec.role in {PLAIN_PERFORMANCE, GCAPEPS_PERFORMANCE}
    if properties["MemoryMax"] != (
        "12884901888" if performance else "25769803776"
    ):
        raise ValueError("MemoryMax drifted")
    if properties["TimeoutStartSec"] != (
        "600s" if performance else "1800s"
    ):
        raise ValueError("TimeoutStartSec drifted")
    stop_fields = properties["ExecStopPost"].split(" ")
    if (
        len(stop_fields) != 4
        or not Path(stop_fields[0]).is_absolute()
        or not Path(stop_fields[1]).is_absolute()
        or stop_fields[2:] != ["--launch-id", spec.launch_id]
    ):
        raise ValueError("ExecStopPost command drifted")
    expected_prefix = (
        "systemd-run",
        "--system",
        "--no-block",
        "--no-ask-password",
        f"--unit={spec.unit_name}",
    )
    if spec.command[:5] != expected_prefix:
        raise ValueError("system-manager command prefix drifted")
    property_args = tuple(
        f"--property={name}={value}" for name, value in spec.properties
    )
    if spec.command[5 : 5 + len(property_args)] != property_args:
        raise ValueError("systemd command/property projection drifted")
    tail = spec.command[5 + len(property_args) :]
    if (
        len(tail) != 5
        or tail[0] != "--"
        or not Path(tail[1]).is_absolute()
        or tail[2] != str(_SCRIPT_PATH)
        or tail[3:] != (spec.role, spec.launch_id)
    ):
        raise ValueError("systemd ExecStart argv drifted")
    dispatch = parse_dispatch_argv(tail[3:])
    if dispatch.role != spec.role or dispatch.launch_id != spec.launch_id:
        raise ValueError("systemd dispatch identity drifted")
    forbidden = {"--wait", "--pipe", "--collect", "--user"}
    if forbidden.intersection(spec.command):
        raise ValueError("forbidden systemd-run mode present")


@dataclass(frozen=True)
class ManagerCommandObservation:
    command: tuple[str, ...]
    returncode: int
    stdout: bytes
    stderr: bytes


MANAGER_COMMAND_SUCCESS = "SUCCESS"
MANAGER_PERMISSION_BLOCKED = "PERMISSION_BLOCKED"
MANAGER_COMMAND_FAILED = "MANAGER_COMMAND_FAILED"

_MANAGER_PERMISSION_MARKERS = (
    "interactive authentication required",
    "authentication is required",
    "access denied",
    "permission denied",
    "not authorized",
    "authorization failed",
)


def classify_system_manager_observation(
    observation: ManagerCommandObservation,
) -> str:
    if not isinstance(observation, ManagerCommandObservation):
        raise TypeError("manager observation has the wrong type")
    if observation.returncode == 0:
        return MANAGER_COMMAND_SUCCESS
    system_scope = (
        bool(observation.command)
        and observation.command[0] in {"systemd-run", "systemctl"}
        and "--system" in observation.command
        and "--user" not in observation.command
    )
    detail = (observation.stderr + b"\n" + observation.stdout).decode(
        "utf-8", errors="replace"
    ).lower()
    if system_scope and any(
        marker in detail for marker in _MANAGER_PERMISSION_MARKERS
    ):
        return MANAGER_PERMISSION_BLOCKED
    return MANAGER_COMMAND_FAILED


class SystemManagerCommandError(RuntimeError):
    def __init__(self, observation: ManagerCommandObservation) -> None:
        self.observation = observation
        self.classification = classify_system_manager_observation(observation)
        detail = observation.stderr.decode("utf-8", errors="replace").strip()
        super().__init__(
            f"system manager command failed with {observation.returncode}: "
            f"{detail}"
        )


def _run_manager_command(
    command: Sequence[str],
    timeout_seconds: float,
) -> ManagerCommandObservation:
    arguments = tuple(command)
    if not arguments or any(
        not isinstance(item, str) or not item or "\x00" in item
        for item in arguments
    ):
        raise ValueError("manager command argv is invalid")
    completed = subprocess.run(
        arguments,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout_seconds,
    )
    if len(completed.stdout) > FAILURE_SNAPSHOT_MAX_BYTES or len(
        completed.stderr
    ) > FAILURE_SNAPSHOT_MAX_BYTES:
        raise RuntimeError("manager command output exceeded its control cap")
    return ManagerCommandObservation(
        command=arguments,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _parse_systemctl_show(
    raw: bytes,
    *,
    expected_properties: Sequence[str],
) -> dict[str, str]:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("systemctl show output is not UTF-8") from exc
    result: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            raise ValueError("systemctl show line lacks an equals sign")
        name, value = line.split("=", 1)
        if not name or name in result:
            raise ValueError("systemctl show property is duplicate or empty")
        result[name] = value
    expected = tuple(expected_properties)
    if set(result) != set(expected) or len(result) != len(expected):
        raise ValueError("systemctl show property set is incomplete")
    return result


class SystemdManagerClient:
    """Minimal noninteractive system-scope control plane."""

    def __init__(
        self,
        *,
        command_runner: Callable[
            [Sequence[str], float], ManagerCommandObservation
        ] = _run_manager_command,
    ) -> None:
        self._command_runner = command_runner

    def _require_success(
        self,
        command: Sequence[str],
        *,
        timeout_seconds: float = 30.0,
    ) -> ManagerCommandObservation:
        observation = self._command_runner(command, timeout_seconds)
        if observation.returncode != 0:
            raise SystemManagerCommandError(observation)
        return observation

    def show(
        self,
        unit_name: str,
        properties: Sequence[str],
    ) -> dict[str, str]:
        if not unit_name.endswith(".service"):
            raise ValueError("systemctl show unit name is invalid")
        names = tuple(properties)
        if not names or len(set(names)) != len(names):
            raise ValueError("systemctl show properties are invalid")
        command: list[str] = [
            "systemctl",
            "--system",
            "--no-ask-password",
            "show",
            "--no-pager",
        ]
        for name in names:
            if re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name) is None:
                raise ValueError("systemctl show property name is invalid")
            command.extend(("--property", name))
        command.append(unit_name)
        observation = self._require_success(command)
        return _parse_systemctl_show(
            observation.stdout,
            expected_properties=names,
        )

    def submit(self, spec: SystemdServiceSpec) -> ManagerCommandObservation:
        validate_systemd_service_spec(spec)
        return self._require_success(spec.command)

    def signal_continue(self, unit_name: str) -> ManagerCommandObservation:
        return self._require_success(
            (
                "systemctl",
                "--system",
                "--no-ask-password",
                "kill",
                "--kill-whom=main",
                "--signal=CONT",
                unit_name,
            )
        )

    def signal_continue_control(
        self,
        unit_name: str,
    ) -> ManagerCommandObservation:
        return self._require_success(
            (
                "systemctl",
                "--system",
                "--no-ask-password",
                "kill",
                "--kill-whom=control",
                "--signal=CONT",
                unit_name,
            )
        )

    def kill_control_group(self, unit_name: str) -> ManagerCommandObservation:
        return self._require_success(
            (
                "systemctl",
                "--system",
                "--no-ask-password",
                "kill",
                "--kill-whom=all",
                "--signal=KILL",
                unit_name,
            )
        )

    def reset_failed(self, unit_name: str) -> ManagerCommandObservation:
        return self._require_success(
            (
                "systemctl",
                "--system",
                "--no-ask-password",
                "reset-failed",
                unit_name,
            ),
            timeout_seconds=30.0,
        )

    def stop(self, unit_name: str) -> ManagerCommandObservation:
        return self._require_success(
            (
                "systemctl",
                "--system",
                "--no-ask-password",
                "stop",
                unit_name,
            ),
            timeout_seconds=30.0,
        )

    def wait_show(
        self,
        unit_name: str,
        properties: Sequence[str],
        predicate: Callable[[Mapping[str, str]], bool],
        *,
        timeout_seconds: float,
    ) -> dict[str, str]:
        deadline = time.monotonic() + timeout_seconds
        last: dict[str, str] | None = None
        while time.monotonic() < deadline:
            last = self.show(unit_name, properties)
            if predicate(last):
                return last
            time.sleep(0.02)
        raise TimeoutError(f"system manager state did not converge: {last}")


_SMOKE_EFFECTIVE_PROPERTIES = (
    "Type",
    "RemainAfterExit",
    "Restart",
    "DynamicUser",
    "PrivateUsers",
    "ProtectSystem",
    "ProtectHome",
    "WorkingDirectory",
    "NoNewPrivileges",
    "PrivateTmp",
    "PrivateDevices",
    "PrivateNetwork",
    "RestrictSUIDSGID",
    "CPUAffinity",
    "LimitCORE",
    "KillMode",
    "MemoryAccounting",
    "TasksAccounting",
    "RuntimeDirectoryPreserve",
    "MemoryMax",
    "MemorySwapMax",
    "TasksMax",
    "LimitFSIZE",
)


_EFFECTIVE_PROPERTY_NAME = {
    "TimeoutStopSec": "TimeoutStopUSec",
    "TimeoutStartSec": "TimeoutStartUSec",
    "RuntimeMaxSec": "RuntimeMaxUSec",
}
_FULL_EFFECTIVE_PROPERTIES = tuple(
    _EFFECTIVE_PROPERTY_NAME.get(name, name)
    for name in _SYSTEMD_PROPERTY_ORDER
)
_DURATION_READBACK_EQUIVALENTS = {
    "15s": frozenset({"15s"}),
    "600s": frozenset({"600s", "10min"}),
    "1800s": frozenset({"1800s", "30min"}),
    "infinity": frozenset({"infinity"}),
}


def expected_effective_systemd_properties(
    spec: SystemdServiceSpec,
) -> dict[str, str]:
    """Construct a canonical fake-manager readback for lifecycle tests."""

    validate_systemd_service_spec(spec)
    configured = spec.property_map()
    effective: dict[str, str] = {}
    for configured_name in _SYSTEMD_PROPERTY_ORDER:
        effective_name = _EFFECTIVE_PROPERTY_NAME.get(
            configured_name,
            configured_name,
        )
        value = configured[configured_name]
        if configured_name == "TimeoutStartSec":
            value = "10min" if value == "600s" else "30min"
        elif configured_name in {
            "StandardInput",
            "StandardOutput",
            "StandardError",
        }:
            value = "file"
        elif configured_name == "ExecStopPost":
            executable = value.split(" ", 1)[0]
            value = (
                "{ "
                f"path={executable} ; "
                f"argv[]={value} ; "
                "ignore_errors=no ; "
                "start_time=[n/a] ; "
                "stop_time=[n/a] ; "
                "pid=0 ; code=(null) ; status=0/0 "
                "}"
            )
        effective[effective_name] = value
    return effective


def _validate_effective_exec_stop_post(
    observed: str,
    configured: str,
) -> None:
    if observed == configured:
        return
    if not observed.startswith("{ ") or not observed.endswith(" }"):
        raise ValueError("effective systemd property drifted: ExecStopPost")
    fields: dict[str, str] = {}
    for item in observed[2:-2].split(" ; "):
        if "=" not in item:
            raise ValueError("effective ExecStopPost readback is malformed")
        name, value = item.split("=", 1)
        if not name or name in fields:
            raise ValueError("effective ExecStopPost field set is malformed")
        fields[name] = value
    executable = configured.split(" ", 1)[0]
    required = {
        "path": executable,
        "argv[]": configured,
        "ignore_errors": "no",
    }
    if any(fields.get(name) != value for name, value in required.items()):
        raise ValueError("effective systemd property drifted: ExecStopPost")


def validate_effective_systemd_properties(
    effective: Mapping[str, str],
    spec: SystemdServiceSpec,
) -> None:
    """Validate every frozen transient-unit property after normalization."""

    validate_systemd_service_spec(spec)
    if set(effective) != set(_FULL_EFFECTIVE_PROPERTIES) or len(effective) != len(
        _FULL_EFFECTIVE_PROPERTIES
    ):
        raise ValueError("effective systemd property set drifted")
    configured = spec.property_map()
    for configured_name in _SYSTEMD_PROPERTY_ORDER:
        effective_name = _EFFECTIVE_PROPERTY_NAME.get(
            configured_name,
            configured_name,
        )
        observed = effective[effective_name]
        expected = configured[configured_name]
        if configured_name in _EFFECTIVE_PROPERTY_NAME:
            if observed not in _DURATION_READBACK_EQUIVALENTS[expected]:
                raise ValueError(
                    f"effective systemd property drifted: {effective_name}"
                )
        elif configured_name in {
            "StandardInput",
            "StandardOutput",
            "StandardError",
        }:
            if observed != "file":
                raise ValueError(
                    f"effective systemd property drifted: {effective_name}"
                )
        elif configured_name == "ExecStopPost":
            _validate_effective_exec_stop_post(observed, expected)
        elif observed != expected:
            raise ValueError(
                f"effective systemd property drifted: {effective_name}"
            )


def validate_fixture_smoke_effective_properties(
    effective: Mapping[str, str],
    spec: SystemdServiceSpec,
) -> None:
    """Compatibility wrapper for the original fixture-only smoke gate."""

    if spec.role != NEUTRAL_FIXTURE_EMITTER:
        raise ValueError("effective smoke gate is fixture-only")
    if set(effective) == set(_FULL_EFFECTIVE_PROPERTIES):
        validate_effective_systemd_properties(effective, spec)
        return
    if set(effective) != set(_SMOKE_EFFECTIVE_PROPERTIES):
        raise ValueError("effective fixture property set drifted")
    configured = spec.property_map()
    for name in _SMOKE_EFFECTIVE_PROPERTIES:
        if effective[name] != configured[name]:
            raise ValueError(f"effective fixture property drifted: {name}")



def _parse_decimal_text(value: str, *, name: str, minimum: int = 0) -> int:
    if not value.isascii() or not value.isdecimal():
        raise ValueError(f"{name} is not one unsigned decimal integer")
    parsed = int(value)
    if parsed < minimum:
        raise ValueError(f"{name} is below its minimum")
    return parsed


def _read_decimal_file(path: Path, *, name: str) -> int:
    return _parse_decimal_text(
        path.read_text(encoding="ascii").strip(),
        name=name,
    )


def _read_counter_file(path: Path, *, name: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        fields = line.split()
        if len(fields) != 2 or fields[0] in result:
            raise ValueError(f"{name} has an invalid counter line")
        result[fields[0]] = _parse_decimal_text(
            fields[1],
            name=f"{name}.{fields[0]}",
        )
    if not result:
        raise ValueError(f"{name} is empty")
    return result


def _read_id_list(path: Path, *, name: str) -> list[int]:
    values = path.read_text(encoding="ascii").split()
    if not values:
        raise ValueError(f"{name} is empty")
    result = [_parse_decimal_text(value, name=name, minimum=1) for value in values]
    if len(set(result)) != len(result):
        raise ValueError(f"{name} contains duplicate ids")
    return result


def _proc_thread_facts(
    proc_root: Path,
    thread_id: int,
    *,
    selected_cpu: int,
) -> dict[str, Any]:
    status = (proc_root / str(thread_id) / "status").read_text(
        encoding="ascii"
    )
    fields: dict[str, str] = {}
    for line in status.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key in fields:
            raise ValueError("proc status contains a duplicate field")
        fields[key] = value.strip()
    state = fields.get("State", "").split(maxsplit=1)[0]
    if state not in {"T", "t"}:
        raise ValueError("cgroup thread is not stopped")
    if fields.get("Cpus_allowed_list") != str(selected_cpu):
        raise ValueError("cgroup thread affinity is not the singleton CPU")
    uid_values = fields.get("Uid", "").split()
    if len(uid_values) != 4:
        raise ValueError("proc status Uid field is invalid")
    uids = [
        _parse_decimal_text(value, name="proc status uid")
        for value in uid_values
    ]
    return {"thread_id": thread_id, "state": state, "uids": uids}


def capture_stopped_cgroup_snapshot(
    unit_show: Mapping[str, str],
    *,
    selected_cpu: int,
    cgroup_root: Path = Path("/sys/fs/cgroup"),
    proc_root: Path = Path("/proc"),
) -> dict[str, Any]:
    """Prove the one-process/all-threads-stopped cgroup barrier."""

    if set(unit_show) != {"MainPID", "ControlGroup"}:
        raise ValueError("stopped cgroup show projection drifted")
    main_pid = _parse_decimal_text(
        unit_show["MainPID"],
        name="MainPID",
        minimum=1,
    )
    control_group = unit_show["ControlGroup"]
    group_parts = Path(control_group).parts
    if not control_group.startswith("/") or ".." in group_parts:
        raise ValueError("ControlGroup path is invalid")
    root = cgroup_root.resolve(strict=True)
    group = (root / control_group.lstrip("/")).resolve(strict=True)
    if group == root or not group.is_relative_to(root):
        raise ValueError("ControlGroup escaped cgroup root")
    processes = _read_id_list(group / "cgroup.procs", name="cgroup.procs")
    if processes != [main_pid]:
        raise ValueError("cgroup.procs is not exactly MainPID")
    threads = _read_id_list(group / "cgroup.threads", name="cgroup.threads")
    thread_facts = [
        _proc_thread_facts(
            proc_root,
            thread_id,
            selected_cpu=selected_cpu,
        )
        for thread_id in threads
    ]
    memory_events = _read_counter_file(
        group / "memory.events", name="memory.events"
    )
    pids_events = _read_counter_file(group / "pids.events", name="pids.events")
    for name in ("max", "oom", "oom_kill", "oom_group_kill"):
        if memory_events.get(name) != 0:
            raise ValueError(f"memory.events[{name}] is nonzero or absent")
    if pids_events.get("max") != 0:
        raise ValueError("pids.events[max] is nonzero or absent")
    pids_peak = _read_decimal_file(group / "pids.peak", name="pids.peak")
    if pids_peak > 32:
        raise ValueError("pids.peak exceeds TasksMax")
    snapshot = {
        "control_group": control_group,
        "main_pid": main_pid,
        "processes": processes,
        "threads": thread_facts,
        "memory_current": _read_decimal_file(
            group / "memory.current", name="memory.current"
        ),
        "memory_peak": _read_decimal_file(
            group / "memory.peak", name="memory.peak"
        ),
        "memory_swap_current": _read_decimal_file(
            group / "memory.swap.current", name="memory.swap.current"
        ),
        "memory_events": memory_events,
        "pids_current": _read_decimal_file(
            group / "pids.current", name="pids.current"
        ),
        "pids_peak": pids_peak,
        "pids_events": pids_events,
        "cpu_stat": _read_counter_file(group / "cpu.stat", name="cpu.stat"),
    }
    if snapshot["memory_swap_current"] != 0:
        raise ValueError("memory.swap.current is nonzero")
    if snapshot["pids_current"] > 32:
        raise ValueError("pids.current exceeds TasksMax")
    return snapshot


@dataclass(frozen=True)
class FailureSnapshotCapture:
    payload: Mapping[str, Any]
    raw_bytes: bytes
    control_pid: int
    helper_uid: int

    def identity(self) -> dict[str, Any]:
        return {
            "schema": FAILURE_SNAPSHOT_SCHEMA,
            "byte_length": len(self.raw_bytes),
            "sha256": sha256_hex(self.raw_bytes),
        }


_FAILURE_SNAPSHOT_KEYS = frozenset(
    {
        "schema",
        "launch_id",
        "service_result",
        "exit_code",
        "exit_status",
        "invocation_id",
        "cgroup_path",
        "live_cgroup",
        "result_projection_sha256",
    }
)
_FAILURE_LIVE_CGROUP_COUNTERS = frozenset(
    {
        "memory_current",
        "memory_peak",
        "memory_swap_current",
        "pids_current",
        "pids_peak",
    }
)
_FAILURE_LIVE_CGROUP_MAPS = frozenset(
    {"memory_events", "pids_events", "cpu_stat"}
)


def _validate_failure_counter_map(value: Any, *, name: str) -> None:
    if not isinstance(value, Mapping) or not value:
        raise ValueError(f"{name} must be a nonempty counter object")
    for key, counter in value.items():
        if (
            not isinstance(key, str)
            or not key
            or not key.isascii()
            or any(character.isspace() for character in key)
        ):
            raise ValueError(f"{name} has an invalid counter key")
        _plain_int(counter, name=f"{name}.{key}")


def validate_failure_snapshot_payload(
    payload: Mapping[str, Any],
    *,
    expected_launch_id: str,
    expected_unit_show: Mapping[str, str] | None = None,
    cgroup_root: Path = Path("/sys/fs/cgroup"),
) -> None:
    _exact_keys(payload, _FAILURE_SNAPSHOT_KEYS, name="failure snapshot")
    if payload["schema"] != FAILURE_SNAPSHOT_SCHEMA:
        raise ValueError("failure snapshot schema mismatch")
    if payload["launch_id"] != expected_launch_id:
        raise ValueError("failure snapshot launch id mismatch")
    for name in (
        "service_result",
        "exit_code",
        "exit_status",
        "invocation_id",
    ):
        value = payload[name]
        if not isinstance(value, str) or not value or "\x00" in value:
            raise ValueError(f"failure snapshot {name} is invalid")
    cgroup_path = Path(payload["cgroup_path"])
    if (
        not cgroup_path.is_absolute()
        or "." in cgroup_path.parts
        or ".." in cgroup_path.parts
    ):
        raise ValueError("failure snapshot cgroup path is invalid")
    live = payload["live_cgroup"]
    expected_live = _FAILURE_LIVE_CGROUP_COUNTERS | _FAILURE_LIVE_CGROUP_MAPS
    _exact_keys(live, expected_live, name="failure snapshot live cgroup")
    for name in _FAILURE_LIVE_CGROUP_COUNTERS:
        _plain_int(live[name], name=f"failure snapshot {name}")
    for name in _FAILURE_LIVE_CGROUP_MAPS:
        _validate_failure_counter_map(live[name], name=name)
    if expected_unit_show is not None:
        expected_show_keys = {
            "ControlPID",
            "ControlGroup",
            "Result",
            "ExecMainCode",
            "ExecMainStatus",
            "InvocationID",
        }
        _exact_keys(
            expected_unit_show,
            expected_show_keys,
            name="failure helper systemd facts",
        )
        _parse_decimal_text(
            expected_unit_show["ControlPID"],
            name="ControlPID",
            minimum=1,
        )
        bindings = {
            "service_result": "Result",
            "exit_code": "ExecMainCode",
            "exit_status": "ExecMainStatus",
            "invocation_id": "InvocationID",
        }
        for snapshot_name, show_name in bindings.items():
            if payload[snapshot_name] != expected_unit_show[show_name]:
                raise ValueError(
                    f"failure snapshot {snapshot_name} binding drifted"
                )
        control_group = expected_unit_show["ControlGroup"]
        if not control_group.startswith("/") or ".." in Path(control_group).parts:
            raise ValueError("failure helper ControlGroup is invalid")
        expected_cgroup = (
            Path(cgroup_root).resolve(strict=True)
            / control_group.removeprefix("/")
        )
        if cgroup_path.resolve(strict=True) != expected_cgroup.resolve(strict=True):
            raise ValueError("failure snapshot cgroup path binding drifted")
    validate_result_projection(payload)


def capture_stopped_failure_snapshot(
    *,
    spool: SealedLaunchSpool,
    launch_id: str,
    unit_show: Mapping[str, str],
    selected_cpu: int,
    runtime_root: Path = Path("/run"),
    cgroup_root: Path = Path("/sys/fs/cgroup"),
    proc_root: Path = Path("/proc"),
) -> FailureSnapshotCapture:
    """Authenticate and copy one stopped ExecStopPost failure snapshot."""

    if spool.launch_id != launch_id or spool.closed or spool.moved:
        raise ValueError("failure snapshot spool binding is invalid")
    control_pid = _parse_decimal_text(
        unit_show.get("ControlPID", ""),
        name="ControlPID",
        minimum=1,
    )
    helper_facts = _proc_thread_facts(
        proc_root,
        control_pid,
        selected_cpu=selected_cpu,
    )
    if len(set(helper_facts["uids"])) != 1:
        raise ValueError("failure helper uid fields disagree")
    helper_uid = helper_facts["uids"][0]
    root = Path(runtime_root).resolve(strict=True)
    runtime_path = root / f"gcapeps-fm-{launch_id}"
    resolved_runtime = runtime_path.resolve(strict=True)
    if resolved_runtime != runtime_path or resolved_runtime.parent != root:
        raise ValueError("failure RuntimeDirectory path is not exact")
    runtime_fd = os.open(
        resolved_runtime,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    snapshot_fd = -1
    try:
        runtime_stat = os.fstat(runtime_fd)
        if (
            not stat.S_ISDIR(runtime_stat.st_mode)
            or stat.S_IMODE(runtime_stat.st_mode) != 0o755
            or runtime_stat.st_uid != helper_uid
        ):
            raise ValueError("failure RuntimeDirectory identity is invalid")
        names = os.listdir(runtime_fd)
        if tuple(sorted(names)) != ("failure_snapshot.json",):
            raise ValueError("failure RuntimeDirectory exact child set drifted")
        snapshot_fd = os.open(
            "failure_snapshot.json",
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=runtime_fd,
        )
        snapshot_stat = os.fstat(snapshot_fd)
        if (
            not stat.S_ISREG(snapshot_stat.st_mode)
            or stat.S_IMODE(snapshot_stat.st_mode) != 0o644
            or snapshot_stat.st_nlink != 1
            or snapshot_stat.st_uid != helper_uid
            or snapshot_stat.st_size <= 0
            or snapshot_stat.st_size > FAILURE_SNAPSHOT_MAX_BYTES
        ):
            raise ValueError("failure snapshot inode identity is invalid")
        raw = _pread_exact(snapshot_fd, snapshot_stat.st_size, 0)
        payload = parse_canonical_json_object(raw)
        validate_failure_snapshot_payload(
            payload,
            expected_launch_id=launch_id,
            expected_unit_show=unit_show,
            cgroup_root=cgroup_root,
        )
        copy_fd = spool.file_fds["failure_snapshot.copy"]
        copy_identity = spool.identities["failure_snapshot.copy"]
        copy_stat = _require_same_sealed_inode(copy_fd, copy_identity)
        if copy_stat.st_size != 0:
            raise ValueError("failure snapshot copy is not fresh")
        cursor = 0
        while cursor < len(raw):
            written = os.pwrite(copy_fd, raw[cursor:], cursor)
            if written <= 0:
                raise RuntimeError("failure snapshot copy write stalled")
            cursor += written
        os.fsync(copy_fd)
        copied_stat = _require_same_sealed_inode(copy_fd, copy_identity)
        if copied_stat.st_size != len(raw):
            raise RuntimeError("failure snapshot copy length drifted")
        if _pread_exact(copy_fd, len(raw), 0) != raw:
            raise RuntimeError("failure snapshot copy bytes drifted")
        return FailureSnapshotCapture(
            payload=payload,
            raw_bytes=raw,
            control_pid=control_pid,
            helper_uid=helper_uid,
        )
    finally:
        if snapshot_fd >= 0:
            os.close(snapshot_fd)
        os.close(runtime_fd)


def capture_failure_snapshot_and_continue(
    *,
    client: SystemdManagerClient,
    unit_name: str,
    spool: SealedLaunchSpool,
    launch_id: str,
    unit_show: Mapping[str, str],
    selected_cpu: int,
    runtime_root: Path = Path("/run"),
    cgroup_root: Path = Path("/sys/fs/cgroup"),
    proc_root: Path = Path("/proc"),
) -> tuple[FailureSnapshotCapture, ManagerCommandObservation]:
    """Copy and fsync the helper snapshot before releasing ControlPID."""

    capture = capture_stopped_failure_snapshot(
        spool=spool,
        launch_id=launch_id,
        unit_show=unit_show,
        selected_cpu=selected_cpu,
        runtime_root=runtime_root,
        cgroup_root=cgroup_root,
        proc_root=proc_root,
    )
    continued = client.signal_continue_control(unit_name)
    return capture, continued


def classify_preunit_launch_error(error: OSError) -> str:
    if not isinstance(error, OSError):
        raise TypeError("pre-unit launch error has the wrong type")
    if error.errno in {errno.EAGAIN, errno.ENOMEM}:
        return "supervisor_censor"
    return "invalid_control"


def classify_failure_snapshot_terminal(
    payload: Mapping[str, Any],
    *,
    absolute_deadline_initiated: bool = False,
    self_stop_barrier_reached: bool = False,
    sigcont_sent: bool = False,
) -> str:
    """Apply the preregistered trusted-fact external-censor allowlist."""

    if payload.get("schema") != FAILURE_SNAPSHOT_SCHEMA:
        raise ValueError("unvalidated failure snapshot schema")
    service_result = payload.get("service_result")
    live = payload.get("live_cgroup")
    if not isinstance(live, Mapping):
        raise ValueError("unvalidated failure snapshot cgroup facts")
    if service_result == "timeout":
        if self_stop_barrier_reached or sigcont_sent:
            return "invalid_control"
        return "supervisor_censor"
    memory_events = live.get("memory_events")
    pids_events = live.get("pids_events")
    if not isinstance(memory_events, Mapping) or not isinstance(
        pids_events, Mapping
    ):
        raise ValueError("unvalidated failure event counters")
    resource_event = (
        service_result in {"oom-kill", "resources"}
        or any(
            memory_events.get(name, 0) > 0
            for name in ("max", "oom", "oom_kill", "oom_group_kill")
        )
        or pids_events.get("max", 0) > 0
    )
    if absolute_deadline_initiated or resource_event:
        return "supervisor_censor"
    return "invalid_control"


@dataclass(frozen=True)
class SystemdLifecycleResult:
    spec: SystemdServiceSpec
    node_terminal: Mapping[str, Any]
    node_identity: PublishedFileIdentity
    launch_receipt: Mapping[str, Any]
    launch_receipt_identity: PublishedFileIdentity
    quarantined_spool: QuarantinedSpool
    sealed_inodes: Mapping[str, SealedInodeIdentity]


FixtureLifecycleResult = SystemdLifecycleResult


def _observation_identity(
    observation: ManagerCommandObservation,
) -> dict[str, Any]:
    return {
        "command": list(observation.command),
        "returncode": observation.returncode,
        "stdout_byte_length": len(observation.stdout),
        "stdout_sha256": sha256_hex(observation.stdout),
        "stderr_byte_length": len(observation.stderr),
        "stderr_sha256": sha256_hex(observation.stderr),
    }


@dataclass(frozen=True)
class ManagerPreflightDecision:
    status: str
    selected_scope: str | None
    attempted_scope: str
    user_manager_fallback_attempted: bool
    science_launch_eligible: bool
    reason_code: str
    observation: ManagerCommandObservation

    def as_payload(self) -> dict[str, Any]:
        payload = {
            "schema": MANAGER_PREFLIGHT_RECEIPT_SCHEMA,
            "status": self.status,
            "selected_scope": self.selected_scope,
            "attempted_scope": self.attempted_scope,
            "user_manager_fallback_attempted": self.user_manager_fallback_attempted,
            "science_launch_eligible": self.science_launch_eligible,
            "reason_code": self.reason_code,
            "attempted_manager": _observation_identity(self.observation),
        }
        return with_result_projection(payload)


def build_permission_blocked_manager_preflight_decision(
    observation: ManagerCommandObservation,
) -> ManagerPreflightDecision:
    classification = classify_system_manager_observation(observation)
    if classification != MANAGER_PERMISSION_BLOCKED:
        raise ValueError("manager observation is not a permission blocker")
    return ManagerPreflightDecision(
        status=MANAGER_PERMISSION_BLOCKED,
        selected_scope=None,
        attempted_scope="system",
        user_manager_fallback_attempted=False,
        science_launch_eligible=False,
        reason_code="SYSTEM_SCOPE_TRANSIENT_UNIT_AUTHORIZATION_REQUIRED",
        observation=observation,
    )


_MANAGER_PREFLIGHT_SECURITY_GATES = frozenset(
    {
        "system_scope_only",
        "systemd_major_255",
        "unified_cgroup_v2",
        "controllers_cpu_memory_pids",
        "runner_nondumpable",
        "dynamic_uid_distinct",
        "supplementary_gid_exact",
        "repository_read_only",
        "output_root_inaccessible",
        "namespaces_created",
        "raw_stdio_inode_bound",
        "self_stop_barrier",
        "byte_caps",
        "attack_probes_denied",
        "environment_sanitized",
        "retained_memory_peak",
        "spool_quarantined",
        "unit_unloaded",
    }
)


def _validate_published_identity_payload(
    value: Mapping[str, Any],
    *,
    name: str,
) -> None:
    _exact_keys(
        value,
        {
            "path",
            "byte_length",
            "sha256",
            "st_dev",
            "st_ino",
            "st_mode",
            "st_nlink",
        },
        name=name,
    )
    if not isinstance(value["path"], str) or not Path(value["path"]).is_absolute():
        raise ValueError(f"{name} path is invalid")
    for key in ("byte_length", "st_dev", "st_ino", "st_mode", "st_nlink"):
        _plain_int(value[key], name=f"{name}.{key}")
    _sha256(value["sha256"], name=f"{name}.sha256")
    if value["st_nlink"] != 1 or not stat.S_ISREG(value["st_mode"]):
        raise ValueError(f"{name} inode is invalid")


def validate_successful_manager_preflight_receipt(
    payload: Mapping[str, Any],
) -> None:
    expected_keys = {
        "schema",
        "status",
        "selected_scope",
        "attempted_scope",
        "user_manager_fallback_attempted",
        "science_launch_eligible",
        "reason_code",
        "attempted_manager",
        "systemd_build",
        "systemd_major",
        "manager_cgroup",
        "cgroup_controllers",
        "runner_identity",
        "runner_namespace_identity",
        "dynamic_user_policy",
        "repository_read_gid",
        "private_users_effective",
        "effective_properties",
        "security_gates",
        "sacrificial_node_identity",
        "sacrificial_launch_receipt_identity",
        "result_projection_sha256",
    }
    _exact_keys(payload, expected_keys, name="successful manager preflight receipt")
    if (
        payload["schema"] != MANAGER_PREFLIGHT_RECEIPT_SCHEMA
        or payload["status"] != "PASSED"
        or payload["selected_scope"] != "system"
        or payload["attempted_scope"] != "system"
        or payload["user_manager_fallback_attempted"] is not False
        or payload["science_launch_eligible"] is not True
        or payload["reason_code"] is not None
    ):
        raise ValueError("successful manager preflight disposition drifted")
    attempted = payload["attempted_manager"]
    _exact_keys(
        attempted,
        {
            "command",
            "returncode",
            "stdout_byte_length",
            "stdout_sha256",
            "stderr_byte_length",
            "stderr_sha256",
        },
        name="attempted manager identity",
    )
    if (
        not isinstance(attempted["command"], list)
        or attempted["command"][:2] != ["systemd-run", "--system"]
        or "--user" in attempted["command"]
        or attempted["returncode"] != 0
    ):
        raise ValueError("attempted manager identity is invalid")
    for key in ("stdout_byte_length", "stderr_byte_length"):
        _plain_int(attempted[key], name=f"attempted manager {key}")
    for key in ("stdout_sha256", "stderr_sha256"):
        _sha256(attempted[key], name=f"attempted manager {key}")
    build = payload["systemd_build"]
    if not isinstance(build, str) or re.match(r"^systemd 255(?:\s|$)", build) is None:
        raise ValueError("manager preflight requires systemd major 255")
    if payload["systemd_major"] != 255:
        raise ValueError("manager preflight major version drifted")
    manager_cgroup = payload["manager_cgroup"]
    if (
        not isinstance(manager_cgroup, str)
        or re.fullmatch(r"0::/[A-Za-z0-9_.@:/-]*", manager_cgroup) is None
    ):
        raise ValueError("manager cgroup is not unified cgroup v2")
    controllers = payload["cgroup_controllers"]
    if (
        not isinstance(controllers, list)
        or controllers != sorted(set(controllers))
        or not {"cpu", "memory", "pids"}.issubset(controllers)
    ):
        raise ValueError("required cgroup-v2 controllers are absent")
    runner = payload["runner_identity"]
    _exact_keys(
        runner,
        {
            "pid",
            "proc_start_time_ticks",
            "real_uid",
            "real_gid",
            "pr_get_dumpable",
        },
        name="manager receipt runner identity",
    )
    for key in runner:
        _plain_int(runner[key], name=f"manager receipt runner {key}")
    if runner["pr_get_dumpable"] != 0:
        raise ValueError("manager receipt runner is dumpable")
    namespaces = payload["runner_namespace_identity"]
    _exact_keys(
        namespaces,
        {"user", "mnt", "net", "pid"},
        name="manager receipt runner namespaces",
    )
    if any(not isinstance(value, str) or not value for value in namespaces.values()):
        raise ValueError("manager receipt runner namespaces are invalid")
    policy = payload["dynamic_user_policy"]
    _exact_keys(
        policy,
        {
            "runner_host_uid",
            "service_host_uid",
            "host_uid_distinct",
            "supplementary_gids",
        },
        name="manager receipt dynamic-user policy",
    )
    _plain_int(policy["runner_host_uid"], name="runner host uid")
    _plain_int(policy["service_host_uid"], name="service host uid")
    if (
        policy["host_uid_distinct"] is not True
        or policy["runner_host_uid"] == policy["service_host_uid"]
        or policy["supplementary_gids"] != [payload["repository_read_gid"]]
    ):
        raise ValueError("dynamic-user isolation is invalid")
    _plain_int(payload["repository_read_gid"], name="repository read gid")
    if payload["private_users_effective"] != "yes":
        raise ValueError("PrivateUsers was not effective")
    effective = payload["effective_properties"]
    if not isinstance(effective, Mapping) or set(effective) != set(
        _FULL_EFFECTIVE_PROPERTIES
    ):
        raise ValueError("manager receipt effective properties are incomplete")
    gates = payload["security_gates"]
    _exact_keys(gates, _MANAGER_PREFLIGHT_SECURITY_GATES, name="security gates")
    if any(value is not True for value in gates.values()):
        raise ValueError("successful manager preflight has an unpassed gate")
    _validate_published_identity_payload(
        payload["sacrificial_node_identity"],
        name="sacrificial node identity",
    )
    _validate_published_identity_payload(
        payload["sacrificial_launch_receipt_identity"],
        name="sacrificial launch receipt identity",
    )
    validate_result_projection(payload)


def _verify_sacrificial_preflight_lifecycle(
    lifecycle: SystemdLifecycleResult,
    *,
    runner_identity: Mapping[str, Any],
    role_parameters: Mapping[str, Any],
    repository_abs: Path,
    run_output_abs: Path,
    repository_read_gid: int,
    selected_cpu: int,
    proc_root: Path,
) -> tuple[dict[str, bool], int]:
    node = lifecycle.node_terminal
    if (
        lifecycle.spec.role != SACRIFICIAL_MANAGER_PREFLIGHT
        or node["terminal_kind"] != "completed_result"
        or node["role"] != SACRIFICIAL_MANAGER_PREFLIGHT
        or lifecycle.launch_receipt["terminal_kind"] != "completed_result"
        or lifecycle.launch_receipt["node_terminal_complete_file_sha256"]
        != lifecycle.node_identity.sha256
    ):
        raise ValueError("sacrificial lifecycle did not complete and bind")
    core = node["core"]
    if not isinstance(core, Mapping):
        raise ValueError("sacrificial lifecycle lacks a core")
    validate_sacrificial_preflight_core(core)
    if core["runner_lineage"] != {
        "pid": role_parameters["runner_pid"],
        "proc_start_time_ticks": role_parameters["runner_start_time_ticks"],
        "real_uid": role_parameters["runner_real_uid"],
        "real_gid": role_parameters["runner_real_gid"],
    }:
        raise ValueError("sacrificial core runner lineage drifted")
    if dict(runner_identity) != {
        "pid": role_parameters["runner_pid"],
        "proc_start_time_ticks": role_parameters["runner_start_time_ticks"],
        "real_uid": role_parameters["runner_real_uid"],
        "real_gid": role_parameters["runner_real_gid"],
        "pr_get_dumpable": 0,
    }:
        raise ValueError("sacrificial role parameters do not bind the runner")
    process = core["process_identity"]
    service_uid = process["real_uid"]
    if (
        process["effective_uid"] != service_uid
        or service_uid == role_parameters["runner_real_uid"]
        or process["real_gid"] != process["effective_gid"]
        or process["supplementary_gids"] != [repository_read_gid]
        or process["working_directory"] != str(Path(repository_abs).resolve(strict=True))
        or process["cpu_affinity"] != [selected_cpu]
    ):
        raise ValueError("sacrificial process identity violates DynamicUser policy")
    barrier = node["cgroup_barrier"]
    if (
        not isinstance(barrier, Mapping)
        or barrier.get("main_pid") != process["pid"]
        or {row["uids"][0] for row in barrier.get("threads", [])}
        != {service_uid}
    ):
        raise ValueError("sacrificial process does not bind its stopped cgroup")
    stdio_names = ("fixture.stdin", "raw.stdout", "raw.stderr")
    for row, name in zip(core["stdio_identity"], stdio_names):
        sealed = lifecycle.sealed_inodes[name]
        expected = {
            "fd": row["fd"],
            "st_dev": sealed.st_dev,
            "st_ino": sealed.st_ino,
            "st_mode": sealed.st_mode,
            "st_nlink": sealed.st_nlink,
            "st_uid": sealed.st_uid,
            "is_regular": True,
        }
        if row != expected:
            raise ValueError(f"sacrificial stdio inode binding failed: {name}")
    child_namespaces = core["namespace_identity"]
    runner_namespaces = role_parameters["runner_namespace_identity"]
    if any(
        child_namespaces[name] == runner_namespaces[name]
        for name in ("user", "mnt", "net")
    ):
        raise ValueError("sacrificial namespaces were not created")
    if core["proc_security"]["NoNewPrivs"] != "1":
        raise ValueError("NoNewPrivs was not active in sacrificial child")
    environment = core["environment_contract"]
    if (
        environment["configured_values"] != _FROZEN_CHILD_ENVIRONMENT
        or environment["pythonpath_present"] is not False
    ):
        raise ValueError("sacrificial environment was not sanitized")
    expected_targets = (
        role_parameters["output_root_abs"],
        role_parameters["evaluator_probe_abs"],
        role_parameters["quarantined_spool_probe_abs"],
        str(proc_root / str(role_parameters["runner_pid"]) / "root"),
        str(proc_root / str(role_parameters["runner_pid"]) / "fd"),
        str(proc_root / str(role_parameters["runner_pid"]) / "mem"),
        f"pid:{role_parameters['runner_pid']}",
        f"pid:{role_parameters['runner_pid']}",
    )
    for row, target in zip(core["attack_probes"], expected_targets):
        if (
            row["target"] != target
            or row["outcome"] != "denied"
            or row["errno"] not in _DENIAL_ERRNOS
        ):
            raise ValueError("sacrificial attack probe was not denied")
    effective = node["unit_facts"]["effective_properties"]
    validate_effective_systemd_properties(effective, lifecycle.spec)
    properties = lifecycle.spec.property_map()
    if (
        properties["ReadOnlyPaths"] != str(Path(repository_abs).resolve(strict=True))
        or properties["InaccessiblePaths"]
        != str(Path(run_output_abs).resolve(strict=True))
    ):
        raise ValueError("sacrificial filesystem policy drifted")
    final_peak = node["final_systemd_memory_peak_bytes"]
    if final_peak != barrier["memory_peak"]:
        raise ValueError("sacrificial retained MemoryPeak drifted")
    if (
        node["cleanup"] != completed_cleanup_facts(deadline_ns=30_000_000_000)
        or node["quarantine"]["status"] != "completed"
        or node["unit_facts"]["unloaded"] != {"LoadState": "not-found"}
    ):
        raise ValueError("sacrificial cleanup or quarantine is incomplete")
    gates = {name: True for name in _MANAGER_PREFLIGHT_SECURITY_GATES}
    return gates, service_uid


def build_successful_manager_preflight_receipt(
    lifecycle: SystemdLifecycleResult,
    *,
    runner_identity: Mapping[str, Any],
    role_parameters: Mapping[str, Any],
    repository_abs: Path,
    run_output_abs: Path,
    repository_read_gid: int,
    selected_cpu: int,
    systemd_build: str,
    manager_cgroup: str,
    cgroup_controllers: Sequence[str],
    proc_root: Path = Path("/proc"),
) -> dict[str, Any]:
    gates, service_uid = _verify_sacrificial_preflight_lifecycle(
        lifecycle,
        runner_identity=runner_identity,
        role_parameters=role_parameters,
        repository_abs=repository_abs,
        run_output_abs=run_output_abs,
        repository_read_gid=repository_read_gid,
        selected_cpu=selected_cpu,
        proc_root=proc_root,
    )
    controllers = sorted(set(cgroup_controllers))
    node = lifecycle.node_terminal
    payload = with_result_projection(
        {
            "schema": MANAGER_PREFLIGHT_RECEIPT_SCHEMA,
            "status": "PASSED",
            "selected_scope": "system",
            "attempted_scope": "system",
            "user_manager_fallback_attempted": False,
            "science_launch_eligible": True,
            "reason_code": None,
            "attempted_manager": node["unit_facts"]["submit"],
            "systemd_build": systemd_build,
            "systemd_major": 255,
            "manager_cgroup": manager_cgroup,
            "cgroup_controllers": controllers,
            "runner_identity": dict(runner_identity),
            "runner_namespace_identity": dict(
                role_parameters["runner_namespace_identity"]
            ),
            "dynamic_user_policy": {
                "runner_host_uid": role_parameters["runner_real_uid"],
                "service_host_uid": service_uid,
                "host_uid_distinct": True,
                "supplementary_gids": [repository_read_gid],
            },
            "repository_read_gid": repository_read_gid,
            "private_users_effective": node["unit_facts"][
                "effective_properties"
            ]["PrivateUsers"],
            "effective_properties": node["unit_facts"]["effective_properties"],
            "security_gates": gates,
            "sacrificial_node_identity": lifecycle.node_identity.as_dict(),
            "sacrificial_launch_receipt_identity": (
                lifecycle.launch_receipt_identity.as_dict()
            ),
        }
    )
    validate_successful_manager_preflight_receipt(payload)
    return payload


@dataclass(frozen=True)
class ManagerPreflightLifecycleResult:
    lifecycle: SystemdLifecycleResult
    manager_preflight_receipt: Mapping[str, Any]
    manager_preflight_receipt_identity: PublishedFileIdentity


_UNIT_BARRIER_PROPERTIES = (
    "MainPID",
    "ControlPID",
    "ControlGroup",
    "Result",
    "ExecMainCode",
    "ExecMainStatus",
    "InvocationID",
)


@dataclass(frozen=True)
class UnitBarrierResult:
    kind: str
    show: Mapping[str, str]
    cgroup_snapshot: Mapping[str, Any] | None
    deadline_kill_observation: ManagerCommandObservation | None


def _wait_for_unit_barrier(
    client: SystemdManagerClient,
    unit_name: str,
    *,
    selected_cpu: int,
    cgroup_root: Path,
    proc_root: Path,
    timeout_seconds: float,
    absolute_deadline_ns: int | None = None,
    deadline_kill_hook: Callable[
        [SystemdManagerClient, str], ManagerCommandObservation
    ] | None = None,
    monotonic_ns: Callable[[], int] = time.monotonic_ns,
) -> UnitBarrierResult:
    deadline = time.monotonic() + timeout_seconds
    last_error: BaseException | None = None
    kill_observation: ManagerCommandObservation | None = None
    while time.monotonic() < deadline:
        show = client.show(unit_name, _UNIT_BARRIER_PROPERTIES)
        main_pid = show["MainPID"]
        if main_pid.isdecimal() and int(main_pid) > 0:
            try:
                snapshot = capture_stopped_cgroup_snapshot(
                    {
                        "MainPID": main_pid,
                        "ControlGroup": show["ControlGroup"],
                    },
                    selected_cpu=selected_cpu,
                    cgroup_root=cgroup_root,
                    proc_root=proc_root,
                )
            except (FileNotFoundError, ValueError) as exc:
                last_error = exc
            else:
                return UnitBarrierResult(
                    "self_stop",
                    show,
                    snapshot,
                    kill_observation,
                )
        control_pid = show["ControlPID"]
        if (
            control_pid.isdecimal()
            and int(control_pid) > 0
            and show["Result"] not in {"", "success"}
        ):
            return UnitBarrierResult(
                "failure_helper",
                show,
                None,
                kill_observation,
            )
        if (
            absolute_deadline_ns is not None
            and kill_observation is None
            and monotonic_ns() >= absolute_deadline_ns
        ):
            hook = (
                (lambda value, name: value.kill_control_group(name))
                if deadline_kill_hook is None
                else deadline_kill_hook
            )
            kill_observation = hook(client, unit_name)
        time.sleep(0.02)
    raise TimeoutError(
        f"worker/helper did not reach a valid stopped barrier: {last_error}"
    )


_FAILURE_HELPER_EXIT_PROPERTIES = (
    "ActiveState",
    "SubState",
    "ControlPID",
    "Result",
    "ExecMainCode",
    "ExecMainStatus",
    "MemoryPeak",
)


def _finalize_failed_systemd_lifecycle(
    *,
    client: SystemdManagerClient,
    spec: SystemdServiceSpec,
    spool: SealedLaunchSpool,
    parsed: ParsedInputTransport,
    run_partition: str,
    role: str,
    launch_id: str,
    input_transport_raw: bytes,
    prelaunch: Mapping[str, str],
    submit_observation: ManagerCommandObservation,
    effective: Mapping[str, str],
    barrier: UnitBarrierResult,
    selected_cpu: int,
    quarantine_parent_abs: Path,
    node_path: Path,
    receipt_path: Path,
    lifecycle_start_ns: int,
    runtime_root: Path,
    cgroup_root: Path,
    proc_root: Path,
) -> SystemdLifecycleResult:
    if barrier.kind != "failure_helper" or barrier.cgroup_snapshot is not None:
        raise ValueError("failure finalizer requires a stopped helper barrier")
    failure_show = {
        name: barrier.show[name]
        for name in (
            "ControlPID",
            "ControlGroup",
            "Result",
            "ExecMainCode",
            "ExecMainStatus",
            "InvocationID",
        )
    }
    capture, continue_observation = capture_failure_snapshot_and_continue(
        client=client,
        unit_name=spec.unit_name,
        spool=spool,
        launch_id=launch_id,
        unit_show=failure_show,
        selected_cpu=selected_cpu,
        runtime_root=runtime_root,
        cgroup_root=cgroup_root,
        proc_root=proc_root,
    )
    helper_exit = client.wait_show(
        spec.unit_name,
        _FAILURE_HELPER_EXIT_PROPERTIES,
        lambda row: (
            row["ActiveState"] == "failed"
            and row["SubState"] == "failed"
            and row["ControlPID"] == "0"
            and row["Result"] == failure_show["Result"]
            and row["ExecMainCode"] == failure_show["ExecMainCode"]
            and row["ExecMainStatus"] == failure_show["ExecMainStatus"]
            and row["MemoryPeak"].isdecimal()
        ),
        timeout_seconds=10.0,
    )
    retained_peak = _parse_decimal_text(
        helper_exit["MemoryPeak"],
        name="failed retained systemd MemoryPeak",
    )
    if retained_peak < capture.payload["live_cgroup"]["memory_peak"]:
        raise ValueError("failed retained MemoryPeak regressed")
    _require_same_sealed_inode(
        spool.file_fds["raw.stdout"],
        spool.identities["raw.stdout"],
    )
    stdout_inspection = inspect_external_censor_stdout_fd(
        spool.file_fds["raw.stdout"],
        role=role,
    )
    stderr_stat = _require_same_sealed_inode(
        spool.file_fds["raw.stderr"],
        spool.identities["raw.stderr"],
    )
    trusted_terminal = classify_failure_snapshot_terminal(
        capture.payload,
        absolute_deadline_initiated=(
            barrier.deadline_kill_observation is not None
        ),
        self_stop_barrier_reached=False,
        sigcont_sent=False,
    )
    terminal_kind = trusted_terminal
    if (
        stdout_inspection.disposition == "invalid"
        or stderr_stat.st_size > STDERR_MAX_BYTES
    ):
        terminal_kind = "invalid_control"
    stop_observation = client.stop(spec.unit_name)
    reset_observation = client.reset_failed(spec.unit_name)
    unloaded = client.wait_show(
        spec.unit_name,
        ("LoadState",),
        lambda row: row == {"LoadState": "not-found"},
        timeout_seconds=30.0,
    )
    runtime_path = runtime_root / spec.runtime_directory
    if runtime_path.exists():
        raise ValueError("failed RuntimeDirectory still exists after reset")
    copied_size = os.fstat(spool.file_fds["failure_snapshot.copy"]).st_size
    if (
        copied_size != len(capture.raw_bytes)
        or _pread_exact(
            spool.file_fds["failure_snapshot.copy"],
            copied_size,
            0,
        )
        != capture.raw_bytes
    ):
        raise ValueError("failure snapshot copy changed before quarantine")
    quarantined = quarantine_sealed_launch_spool(
        spool,
        quarantine_parent_abs=quarantine_parent_abs,
    )
    if quarantined.raw_files["fixture.stdin"] != input_transport_raw:
        raise ValueError("failed quarantined stdin differs from transport")
    if quarantined.raw_files["failure_snapshot.copy"] != capture.raw_bytes:
        raise ValueError("failed quarantined snapshot copy drifted")
    cleanup = completed_cleanup_facts(deadline_ns=30_000_000_000)
    quarantine = completed_quarantine_facts(
        relative_path=quarantined.relative_path
    )
    node = build_node_terminal(
        launch_id=launch_id,
        run_partition=run_partition,
        role=role,
        terminal_kind=terminal_kind,
        input_transport=parsed.identity(),
        core=None,
        trailer=None,
        raw_stdout=RawFileIdentity.from_bytes(
            quarantined.raw_files["raw.stdout"]
        ).as_dict(),
        raw_stderr=RawFileIdentity.from_bytes(
            quarantined.raw_files["raw.stderr"]
        ).as_dict(),
        unit_facts={
            "prelaunch": dict(prelaunch),
            "submit": _observation_identity(submit_observation),
            "effective_properties": dict(effective),
            "failure_barrier_show": dict(barrier.show),
            "failure_snapshot_payload": dict(capture.payload),
            "helper_continue": _observation_identity(continue_observation),
            "helper_exit": dict(helper_exit),
            "stdout_inspection": {
                "disposition": stdout_inspection.disposition,
                "byte_length": stdout_inspection.byte_length,
                "reason": stdout_inspection.reason,
            },
            "absolute_deadline_kill": (
                None
                if barrier.deadline_kill_observation is None
                else _observation_identity(barrier.deadline_kill_observation)
            ),
            "stop": _observation_identity(stop_observation),
            "reset_failed": _observation_identity(reset_observation),
            "unloaded": dict(unloaded),
        },
        cgroup_barrier=None,
        exit_facts=helper_exit,
        failure_snapshot=capture.identity(),
        final_systemd_memory_peak_bytes=retained_peak,
        cleanup=cleanup,
        quarantine=quarantine,
    )
    node_identity = publish_canonical_json_noreplace(node_path, node)
    receipt = build_launch_receipt(
        launch_id=launch_id,
        run_partition=run_partition,
        role=role,
        node_terminal_path=node_path,
        node_terminal_identity=node_identity,
        terminal_kind=terminal_kind,
        cleanup=cleanup,
        quarantine=quarantine,
        supervisor_launch_wall_ns=max(1, time.monotonic_ns() - lifecycle_start_ns),
    )
    receipt_identity = publish_canonical_json_noreplace(receipt_path, receipt)
    return SystemdLifecycleResult(
        spec=spec,
        node_terminal=node,
        node_identity=node_identity,
        launch_receipt=receipt,
        launch_receipt_identity=receipt_identity,
        quarantined_spool=quarantined,
        sealed_inodes=dict(spool.identities),
    )


def run_systemd_lifecycle(
    *,
    run_partition: str,
    role: str,
    launch_id: str,
    input_transport_raw: bytes,
    repository_abs: Path,
    run_output_abs: Path,
    spool_parent_abs: Path,
    quarantine_parent_abs: Path,
    node_terminal_path: Path,
    launch_receipt_path: Path,
    selected_cpu: int,
    repository_read_gid: int,
    python_executable: Path,
    manager_client: SystemdManagerClient | None = None,
    cgroup_root: Path = Path("/sys/fs/cgroup"),
    proc_root: Path = Path("/proc"),
    runtime_root: Path = Path("/run"),
    barrier_timeout_seconds: float = 60.0,
    absolute_deadline_ns: int | None = None,
    deadline_kill_hook: Callable[
        [SystemdManagerClient, str], ManagerCommandObservation
    ] | None = None,
    monotonic_ns: Callable[[], int] = time.monotonic_ns,
) -> SystemdLifecycleResult:
    """Execute one clean, success-path system-scope child lifecycle."""

    parsed = parse_input_transport(
        input_transport_raw,
        expected_partition=run_partition,
        expected_role=role,
    )
    output_root = Path(run_output_abs).resolve(strict=True)
    node_path = Path(node_terminal_path)
    receipt_path = Path(launch_receipt_path)
    if (
        not node_path.is_absolute()
        or not receipt_path.is_absolute()
        or node_path.parent.resolve(strict=True) != output_root
        or receipt_path.parent.resolve(strict=True) != output_root
    ):
        raise ValueError("node publications must be direct run outputs")
    if node_path.exists() or receipt_path.exists():
        raise FileExistsError("node publication already exists")
    lifecycle_start_ns = time.monotonic_ns()
    spool = create_sealed_launch_spool(
        spool_parent_abs=spool_parent_abs,
        launch_id=launch_id,
        input_transport_raw=input_transport_raw,
        expected_partition=run_partition,
        expected_role=role,
    )
    client = SystemdManagerClient() if manager_client is None else manager_client
    spec = build_systemd_service_spec(
        launch_id=launch_id,
        role=role,
        repository_abs=repository_abs,
        run_output_abs=output_root,
        spool_abs=spool.spool_path,
        selected_cpu=selected_cpu,
        repository_read_gid=repository_read_gid,
        python_executable=python_executable,
        worker_path=_SCRIPT_PATH,
    )
    submitted = False
    completed = False
    try:
        prelaunch = client.show(spec.unit_name, ("LoadState",))
        if prelaunch != {"LoadState": "not-found"}:
            raise ValueError("transient unit name was already loaded")
        submit_observation = client.submit(spec)
        submitted = True
        effective = client.show(
            spec.unit_name,
            _FULL_EFFECTIVE_PROPERTIES,
        )
        validate_effective_systemd_properties(effective, spec)
        barrier = _wait_for_unit_barrier(
            client,
            spec.unit_name,
            selected_cpu=selected_cpu,
            cgroup_root=cgroup_root,
            proc_root=proc_root,
            timeout_seconds=barrier_timeout_seconds,
            absolute_deadline_ns=absolute_deadline_ns,
            deadline_kill_hook=deadline_kill_hook,
            monotonic_ns=monotonic_ns,
        )
        if barrier.kind == "failure_helper":
            failure_result = _finalize_failed_systemd_lifecycle(
                client=client,
                spec=spec,
                spool=spool,
                parsed=parsed,
                run_partition=run_partition,
                role=role,
                launch_id=launch_id,
                input_transport_raw=input_transport_raw,
                prelaunch=prelaunch,
                submit_observation=submit_observation,
                effective=effective,
                barrier=barrier,
                selected_cpu=selected_cpu,
                quarantine_parent_abs=quarantine_parent_abs,
                node_path=node_path,
                receipt_path=receipt_path,
                lifecycle_start_ns=lifecycle_start_ns,
                runtime_root=runtime_root,
                cgroup_root=cgroup_root,
                proc_root=proc_root,
            )
            completed = True
            return failure_result
        if barrier.kind != "self_stop" or barrier.cgroup_snapshot is None:
            raise ValueError("unit barrier kind is invalid")
        barrier_show = barrier.show
        cgroup_snapshot = barrier.cgroup_snapshot
        real_uids = {
            row["uids"][0] for row in cgroup_snapshot["threads"]
        }
        if len(real_uids) != 1 or os.geteuid() in real_uids:
            raise ValueError("DynamicUser host uid is not distinct")
        _require_same_sealed_inode(
            spool.file_fds["raw.stdout"],
            spool.identities["raw.stdout"],
        )
        _require_same_sealed_inode(
            spool.file_fds["raw.stderr"],
            spool.identities["raw.stderr"],
        )
        decoded = read_clean_worker_frames_fd(
            spool.file_fds["raw.stdout"],
            role=role,
        )
        terminal_kind = classify_clean_worker_core(decoded.core)
        stderr_stat = os.fstat(spool.file_fds["raw.stderr"])
        if stderr_stat.st_size != 0:
            raise ValueError("clean worker stderr is not empty")
        if os.fstat(spool.file_fds["failure_snapshot.copy"]).st_size != 0:
            raise ValueError("success-path failure snapshot copy is not empty")
        client.signal_continue(spec.unit_name)
        exit_properties = (
            "ActiveState",
            "SubState",
            "MainPID",
            "Result",
            "ExecMainCode",
            "ExecMainStatus",
            "MemoryPeak",
        )
        exit_show = client.wait_show(
            spec.unit_name,
            exit_properties,
            lambda row: row == {
                "ActiveState": "active",
                "SubState": "exited",
                "MainPID": "0",
                "Result": "success",
                "ExecMainCode": "exited",
                "ExecMainStatus": "0",
                "MemoryPeak": row["MemoryPeak"],
            },
            timeout_seconds=30.0,
        )
        retained_peak = _parse_decimal_text(
            exit_show["MemoryPeak"],
            name="retained systemd MemoryPeak",
        )
        if retained_peak != cgroup_snapshot["memory_peak"]:
            raise ValueError("retained MemoryPeak differs from live cgroup peak")
        stop_observation = client.stop(spec.unit_name)
        unloaded = client.wait_show(
            spec.unit_name,
            ("LoadState",),
            lambda row: row == {"LoadState": "not-found"},
            timeout_seconds=30.0,
        )
        runtime_path = runtime_root / spec.runtime_directory
        if runtime_path.exists():
            raise ValueError("non-preserved RuntimeDirectory still exists")
        if os.fstat(spool.file_fds["failure_snapshot.copy"]).st_size != 0:
            raise ValueError("success-path failure snapshot copy changed")
        quarantined = quarantine_sealed_launch_spool(
            spool,
            quarantine_parent_abs=quarantine_parent_abs,
        )
        if quarantined.raw_files["fixture.stdin"] != input_transport_raw:
            raise ValueError("quarantined stdin differs from sealed transport")
        if quarantined.raw_files["raw.stdout"] != _TIMING.encode_two_frames(
            decoded.core_bytes,
            decoded.trailer_bytes,
        ):
            raise ValueError("quarantined stdout differs from stopped frames")
        if quarantined.raw_files["raw.stderr"] != b"":
            raise ValueError("quarantined clean stderr is not empty")
        if quarantined.raw_files["failure_snapshot.copy"] != b"":
            raise ValueError("quarantined success snapshot copy is not empty")
        cleanup = completed_cleanup_facts(deadline_ns=30_000_000_000)
        quarantine = completed_quarantine_facts(
            relative_path=quarantined.relative_path
        )
        node = build_node_terminal(
            launch_id=launch_id,
            run_partition=run_partition,
            role=role,
            terminal_kind=terminal_kind,
            input_transport=parsed.identity(),
            core=decoded.core,
            trailer=decoded.trailer,
            raw_stdout=RawFileIdentity.from_bytes(
                quarantined.raw_files["raw.stdout"]
            ).as_dict(),
            raw_stderr=RawFileIdentity.from_bytes(
                quarantined.raw_files["raw.stderr"]
            ).as_dict(),
            unit_facts={
                "prelaunch": prelaunch,
                "submit": _observation_identity(submit_observation),
                "barrier_show": barrier_show,
                "effective_properties": effective,
                "unloaded": unloaded,
                "stop": _observation_identity(stop_observation),
            },
            cgroup_barrier=cgroup_snapshot,
            exit_facts=exit_show,
            failure_snapshot=None,
            final_systemd_memory_peak_bytes=retained_peak,
            cleanup=cleanup,
            quarantine=quarantine,
        )
        node_identity = publish_canonical_json_noreplace(node_path, node)
        launch_wall_ns = time.monotonic_ns() - lifecycle_start_ns
        receipt = build_launch_receipt(
            launch_id=launch_id,
            run_partition=run_partition,
            role=role,
            node_terminal_path=node_path,
            node_terminal_identity=node_identity,
            terminal_kind=terminal_kind,
            cleanup=cleanup,
            quarantine=quarantine,
            supervisor_launch_wall_ns=max(1, launch_wall_ns),
        )
        receipt_identity = publish_canonical_json_noreplace(
            receipt_path,
            receipt,
        )
        completed = True
        return SystemdLifecycleResult(
            spec=spec,
            node_terminal=node,
            node_identity=node_identity,
            launch_receipt=receipt,
            launch_receipt_identity=receipt_identity,
            quarantined_spool=quarantined,
            sealed_inodes=dict(spool.identities),
        )
    finally:
        if submitted and not completed:
            try:
                client.stop(spec.unit_name)
            except BaseException:
                pass
        spool.close()


def run_manager_preflight_lifecycle(
    *,
    launch_id: str,
    runner_identity: Mapping[str, Any],
    evaluator_probe_abs: Path,
    quarantined_spool_probe_abs: Path,
    repository_abs: Path,
    run_output_abs: Path,
    spool_parent_abs: Path,
    quarantine_parent_abs: Path,
    node_terminal_path: Path,
    launch_receipt_path: Path,
    manager_preflight_path: Path,
    selected_cpu: int,
    repository_read_gid: int,
    python_executable: Path,
    systemd_build: str,
    manager_cgroup: str,
    cgroup_controllers: Sequence[str],
    manager_client: SystemdManagerClient | None = None,
    cgroup_root: Path = Path("/sys/fs/cgroup"),
    proc_root: Path = Path("/proc"),
    runner_proc_root: Path = Path("/proc"),
    runtime_root: Path = Path("/run"),
    barrier_timeout_seconds: float = 60.0,
) -> ManagerPreflightLifecycleResult:
    """Run and publish the no-scientific-input system-manager gate."""

    output_root = Path(run_output_abs).resolve(strict=True)
    preflight_path = Path(manager_preflight_path)
    if (
        not preflight_path.is_absolute()
        or preflight_path.parent.resolve(strict=True) != output_root
        or preflight_path.exists()
    ):
        raise ValueError("manager preflight publication path is invalid")
    role_parameters = build_sacrificial_role_parameters(
        runner_identity=runner_identity,
        selected_cpu=selected_cpu,
        output_root_abs=output_root,
        evaluator_probe_abs=evaluator_probe_abs,
        quarantined_spool_probe_abs=quarantined_spool_probe_abs,
        proc_root=runner_proc_root,
    )
    transport = build_input_transport(
        run_partition=BOOTSTRAP,
        role=SACRIFICIAL_MANAGER_PREFLIGHT,
        role_parameters=role_parameters,
        artifacts=(),
    )
    lifecycle = run_systemd_lifecycle(
        run_partition=BOOTSTRAP,
        role=SACRIFICIAL_MANAGER_PREFLIGHT,
        launch_id=launch_id,
        input_transport_raw=transport,
        repository_abs=repository_abs,
        run_output_abs=output_root,
        spool_parent_abs=spool_parent_abs,
        quarantine_parent_abs=quarantine_parent_abs,
        node_terminal_path=node_terminal_path,
        launch_receipt_path=launch_receipt_path,
        selected_cpu=selected_cpu,
        repository_read_gid=repository_read_gid,
        python_executable=python_executable,
        manager_client=manager_client,
        cgroup_root=cgroup_root,
        proc_root=proc_root,
        runtime_root=runtime_root,
        barrier_timeout_seconds=barrier_timeout_seconds,
    )
    receipt = build_successful_manager_preflight_receipt(
        lifecycle,
        runner_identity=runner_identity,
        role_parameters=role_parameters,
        repository_abs=repository_abs,
        run_output_abs=output_root,
        repository_read_gid=repository_read_gid,
        selected_cpu=selected_cpu,
        systemd_build=systemd_build,
        manager_cgroup=manager_cgroup,
        cgroup_controllers=cgroup_controllers,
        proc_root=runner_proc_root,
    )
    identity = publish_canonical_json_noreplace(preflight_path, receipt)
    reopened = transport_artifact_from_published_file(
        name="manager_preflight_receipt",
        identity=identity,
    )
    if reopened.raw_bytes != canonical_json_bytes(receipt):
        raise RuntimeError("published manager preflight bytes drifted")
    return ManagerPreflightLifecycleResult(
        lifecycle=lifecycle,
        manager_preflight_receipt=receipt,
        manager_preflight_receipt_identity=identity,
    )


def run_fixture_systemd_lifecycle(
    *,
    launch_id: str,
    input_transport_raw: bytes,
    repository_abs: Path,
    run_output_abs: Path,
    spool_parent_abs: Path,
    quarantine_parent_abs: Path,
    node_terminal_path: Path,
    launch_receipt_path: Path,
    selected_cpu: int,
    repository_read_gid: int,
    python_executable: Path,
    manager_client: SystemdManagerClient | None = None,
    cgroup_root: Path = Path("/sys/fs/cgroup"),
    proc_root: Path = Path("/proc"),
    runtime_root: Path = Path("/run"),
    barrier_timeout_seconds: float = 60.0,
) -> SystemdLifecycleResult:
    """Compatibility entry point for the calibration fixture smoke."""

    return run_systemd_lifecycle(
        run_partition=CALIBRATION,
        role=NEUTRAL_FIXTURE_EMITTER,
        launch_id=launch_id,
        input_transport_raw=input_transport_raw,
        repository_abs=repository_abs,
        run_output_abs=run_output_abs,
        spool_parent_abs=spool_parent_abs,
        quarantine_parent_abs=quarantine_parent_abs,
        node_terminal_path=node_terminal_path,
        launch_receipt_path=launch_receipt_path,
        selected_cpu=selected_cpu,
        repository_read_gid=repository_read_gid,
        python_executable=python_executable,
        manager_client=manager_client,
        cgroup_root=cgroup_root,
        proc_root=proc_root,
        runtime_root=runtime_root,
        barrier_timeout_seconds=barrier_timeout_seconds,
    )


SCIENTIFIC_CENSOR_ROLES = frozenset(
    {
        DENSE_REFERENCE,
        PLAIN_EVIDENCE,
        GCAPEPS_EVIDENCE,
        SDIM_COMPUTATION,
        TERMINAL_COMPARATOR,
    }
)
PERFORMANCE_ONLY_ROLES = frozenset(
    {PLAIN_PERFORMANCE, GCAPEPS_PERFORMANCE}
)
_HELDOUT_ROLE_STAGE = {
    DENSE_REFERENCE: 0,
    PLAIN_EVIDENCE: 1,
    GCAPEPS_EVIDENCE: 2,
    PLAIN_PERFORMANCE: 3,
    GCAPEPS_PERFORMANCE: 3,
    SDIM_COMPUTATION: 4,
    TERMINAL_COMPARATOR: 5,
}


@dataclass(frozen=True)
class SerialLaunchRequest:
    ordinal: int
    cell_id: str
    launch_id: str
    role: str


@dataclass(frozen=True)
class SerialLaunchOutcome:
    request: SerialLaunchRequest
    executed: bool
    terminal_kind: str | None
    disposition: str


def _validate_heldout_serial_plan(
    requests: Sequence[SerialLaunchRequest],
) -> tuple[SerialLaunchRequest, ...]:
    plan = tuple(requests)
    seen_launches: set[str] = set()
    closed_cells: set[str] = set()
    current_cell: str | None = None
    prior_stage = -1
    for index, request in enumerate(plan):
        if not isinstance(request, SerialLaunchRequest):
            raise TypeError("serial launch request has the wrong type")
        if request.ordinal != index:
            raise ValueError("serial launch ordinals are not contiguous")
        if (
            not isinstance(request.cell_id, str)
            or not request.cell_id
            or "\x00" in request.cell_id
        ):
            raise ValueError("serial launch cell id is invalid")
        if (
            _LAUNCH_ID_RE.fullmatch(request.launch_id) is None
            or request.launch_id in seen_launches
        ):
            raise ValueError("serial launch id is invalid or reused")
        if request.role not in _HELDOUT_ROLE_STAGE:
            raise ValueError("role is not in the heldout serial graph")
        if request.cell_id != current_cell:
            if request.cell_id in closed_cells:
                raise ValueError("heldout cell is not contiguous")
            if current_cell is not None:
                closed_cells.add(current_cell)
            current_cell = request.cell_id
            prior_stage = -1
        stage = _HELDOUT_ROLE_STAGE[request.role]
        if stage < prior_stage:
            raise ValueError("heldout role stage order regressed")
        prior_stage = stage
        seen_launches.add(request.launch_id)
    return plan


def run_heldout_serial_launch_plan(
    requests: Sequence[SerialLaunchRequest],
    launch_one: Callable[[SerialLaunchRequest], str],
) -> tuple[SerialLaunchOutcome, ...]:
    """Run the frozen one-at-a-time censor/invalid propagation policy."""

    plan = _validate_heldout_serial_plan(requests)
    outcomes: list[SerialLaunchOutcome] = []
    blocked_cell: str | None = None
    invalid_halt = False
    for request in plan:
        if invalid_halt:
            outcomes.append(
                SerialLaunchOutcome(
                    request=request,
                    executed=False,
                    terminal_kind=None,
                    disposition="SKIPPED_INVALID_CONTROL",
                )
            )
            continue
        if blocked_cell == request.cell_id:
            outcomes.append(
                SerialLaunchOutcome(
                    request=request,
                    executed=False,
                    terminal_kind=None,
                    disposition="SKIPPED_PREREQUISITE",
                )
            )
            continue
        terminal_kind = launch_one(request)
        if terminal_kind not in _TERMINAL_KINDS:
            raise ValueError("launch callback returned an invalid terminal kind")
        outcomes.append(
            SerialLaunchOutcome(
                request=request,
                executed=True,
                terminal_kind=terminal_kind,
                disposition=terminal_kind,
            )
        )
        if terminal_kind == "invalid_control":
            invalid_halt = True
        elif (
            terminal_kind in {"worker_censor", "supervisor_censor"}
            and request.role not in PERFORMANCE_ONLY_ROLES
        ):
            blocked_cell = request.cell_id
    return tuple(outcomes)


def _main(argv: Sequence[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    prepared = prepare_child_dispatch(arguments, stdin_fd=0)
    result = invoke_prepared_dispatch(prepared)
    emit_dispatch_result_and_self_stop(
        result,
        stdout_fd=1,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
