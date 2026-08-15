#!/usr/bin/env python3
"""Strict timing and two-frame transport for the finite-memory benchmark.

This module is deliberately scientific-backend free.  It owns only the
preregistered nested wall/CPU timing representation, canonical JSON encoding,
and the worker's ``u64be || core || u64be || trailer`` stdout framing.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import math
import resource
import struct
import time
from typing import Any, Iterator, Mapping, Sequence


TIMING_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "layered_timing.v1"
)
TRAILER_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "late_telemetry_trailer.v1"
)
WALL_CLOCK = "time.perf_counter_ns"
CPU_CLOCK = "time.process_time_ns"

_SPAN_KEYS = frozenset(
    {
        "span_id",
        "parent_span_id",
        "scope",
        "lane",
        "case_id",
        "trajectory_id",
        "round_index",
        "operation_index",
        "step_index",
        "kind",
        "status",
        "wall_start_offset_ns",
        "wall_end_offset_ns",
        "wall_duration_ns",
        "cpu_start_offset_ns",
        "cpu_end_offset_ns",
        "cpu_duration_ns",
        "child_wall_ns",
        "child_cpu_ns",
        "unattributed_wall_ns",
        "unattributed_cpu_ns",
    }
)


def _reject_nonfinite(value: Any, path: str = "$") -> None:
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite value at {path}")
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise TypeError(f"non-string JSON key at {path}")
            _reject_nonfinite(child, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _reject_nonfinite(child, f"{path}[{index}]")


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """Encode one finite JSON object as compact ASCII without a newline."""

    if not isinstance(payload, Mapping):
        raise TypeError("canonical payload must be a mapping")
    _reject_nonfinite(payload)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    if encoded.endswith(b"\n"):
        raise AssertionError("canonical JSON unexpectedly ended in a newline")
    return encoded


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class _OpenSpan:
    span_id: str
    parent_span_id: str | None
    scope: str
    lane: str | None
    case_id: str | None
    trajectory_id: str | None
    round_index: int | None
    operation_index: int | None
    step_index: int | None
    kind: str
    wall_start_offset_ns: int
    cpu_start_offset_ns: int


class LayeredTimer:
    """Collect strictly nested, sequential worker wall and process-CPU spans."""

    def __init__(self) -> None:
        self._wall_root_ns = time.perf_counter_ns()
        self._cpu_root_ns = time.process_time_ns()
        self._stack: list[_OpenSpan] = []
        self._spans: list[dict[str, Any]] = []
        self._ids: set[str] = set()
        self._finished = False

    @contextmanager
    def span(
        self,
        span_id: str,
        *,
        scope: str,
        kind: str,
        lane: str | None = None,
        case_id: str | None = None,
        trajectory_id: str | None = None,
        round_index: int | None = None,
        operation_index: int | None = None,
        step_index: int | None = None,
    ) -> Iterator[None]:
        if self._finished:
            raise RuntimeError("timer is already finalized")
        if not span_id or span_id in self._ids:
            raise ValueError(f"duplicate or empty span_id: {span_id!r}")
        for name, value in (
            ("round_index", round_index),
            ("operation_index", operation_index),
            ("step_index", step_index),
        ):
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ValueError(f"{name} must be null or a nonnegative integer")
        parent_id = self._stack[-1].span_id if self._stack else None
        opened = _OpenSpan(
            span_id=span_id,
            parent_span_id=parent_id,
            scope=scope,
            lane=lane,
            case_id=case_id,
            trajectory_id=trajectory_id,
            round_index=round_index,
            operation_index=operation_index,
            step_index=step_index,
            kind=kind,
            wall_start_offset_ns=time.perf_counter_ns() - self._wall_root_ns,
            cpu_start_offset_ns=time.process_time_ns() - self._cpu_root_ns,
        )
        self._ids.add(span_id)
        self._stack.append(opened)
        failed = False
        try:
            yield
        except BaseException:
            failed = True
            raise
        finally:
            closed = self._stack.pop()
            if closed is not opened:
                raise RuntimeError("timing stack corruption")
            wall_end = time.perf_counter_ns() - self._wall_root_ns
            cpu_end = time.process_time_ns() - self._cpu_root_ns
            self._spans.append(
                {
                    "span_id": opened.span_id,
                    "parent_span_id": opened.parent_span_id,
                    "scope": opened.scope,
                    "lane": opened.lane,
                    "case_id": opened.case_id,
                    "trajectory_id": opened.trajectory_id,
                    "round_index": opened.round_index,
                    "operation_index": opened.operation_index,
                    "step_index": opened.step_index,
                    "kind": opened.kind,
                    "status": "failed" if failed else "completed",
                    "wall_start_offset_ns": opened.wall_start_offset_ns,
                    "wall_end_offset_ns": wall_end,
                    "wall_duration_ns": wall_end - opened.wall_start_offset_ns,
                    "cpu_start_offset_ns": opened.cpu_start_offset_ns,
                    "cpu_end_offset_ns": cpu_end,
                    "cpu_duration_ns": cpu_end - opened.cpu_start_offset_ns,
                    "child_wall_ns": 0,
                    "child_cpu_ns": 0,
                    "unattributed_wall_ns": 0,
                    "unattributed_cpu_ns": 0,
                }
            )

    def finish(self) -> dict[str, Any]:
        if self._finished:
            raise RuntimeError("timer can be finalized only once")
        if self._stack:
            raise RuntimeError("cannot finalize with open spans")
        self._finished = True
        by_id = {row["span_id"]: row for row in self._spans}
        for row in self._spans:
            parent_id = row["parent_span_id"]
            if parent_id is not None:
                parent = by_id[parent_id]
                parent["child_wall_ns"] += row["wall_duration_ns"]
                parent["child_cpu_ns"] += row["cpu_duration_ns"]
        for row in self._spans:
            row["unattributed_wall_ns"] = (
                row["wall_duration_ns"] - row["child_wall_ns"]
            )
            row["unattributed_cpu_ns"] = (
                row["cpu_duration_ns"] - row["child_cpu_ns"]
            )
        payload = {
            "schema": TIMING_SCHEMA,
            "wall_clock": WALL_CLOCK,
            "cpu_clock": CPU_CLOCK,
            "spans": sorted(
                self._spans,
                key=lambda row: (
                    row["wall_start_offset_ns"],
                    -row["wall_end_offset_ns"],
                    row["span_id"],
                ),
            ),
        }
        validate_layered_timing(payload)
        return payload


def validate_layered_timing(
    payload: Mapping[str, Any],
    *,
    positive_scopes: Sequence[str] = (),
) -> None:
    """Validate exact identities, topology, and sequential nesting."""

    if payload.get("schema") != TIMING_SCHEMA:
        raise ValueError("wrong timing schema")
    if payload.get("wall_clock") != WALL_CLOCK:
        raise ValueError("wrong wall clock")
    if payload.get("cpu_clock") != CPU_CLOCK:
        raise ValueError("wrong CPU clock")
    spans = payload.get("spans")
    if not isinstance(spans, list) or not spans:
        raise ValueError("timing spans must be a nonempty list")
    by_id: dict[str, Mapping[str, Any]] = {}
    children: dict[str, list[Mapping[str, Any]]] = {}
    roots: list[Mapping[str, Any]] = []
    for row in spans:
        if not isinstance(row, Mapping) or set(row) != _SPAN_KEYS:
            raise ValueError("timing row has the wrong exact key set")
        span_id = row["span_id"]
        if not isinstance(span_id, str) or not span_id or span_id in by_id:
            raise ValueError("duplicate or invalid span id")
        by_id[span_id] = row
        for key in (
            "wall_start_offset_ns",
            "wall_end_offset_ns",
            "wall_duration_ns",
            "cpu_start_offset_ns",
            "cpu_end_offset_ns",
            "cpu_duration_ns",
            "child_wall_ns",
            "child_cpu_ns",
            "unattributed_wall_ns",
            "unattributed_cpu_ns",
        ):
            value = row[key]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{span_id}: {key} must be a nonnegative integer")
        if (
            row["wall_duration_ns"]
            != row["wall_end_offset_ns"] - row["wall_start_offset_ns"]
            or row["cpu_duration_ns"]
            != row["cpu_end_offset_ns"] - row["cpu_start_offset_ns"]
        ):
            raise ValueError(f"{span_id}: duration identity failed")
        for key in ("round_index", "operation_index", "step_index"):
            value = row[key]
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ValueError(f"{span_id}: invalid {key}")
        if row["status"] not in {"completed", "failed"}:
            raise ValueError(f"{span_id}: invalid status")
    for row in spans:
        parent_id = row["parent_span_id"]
        if parent_id is None:
            roots.append(row)
        else:
            if parent_id not in by_id:
                raise ValueError(f"{row['span_id']}: missing parent")
            parent = by_id[parent_id]
            if not (
                parent["wall_start_offset_ns"] <= row["wall_start_offset_ns"]
                and row["wall_end_offset_ns"] <= parent["wall_end_offset_ns"]
                and parent["cpu_start_offset_ns"] <= row["cpu_start_offset_ns"]
                and row["cpu_end_offset_ns"] <= parent["cpu_end_offset_ns"]
            ):
                raise ValueError(f"{row['span_id']}: child is outside parent")
            children.setdefault(parent_id, []).append(row)
    if len(roots) != 1:
        raise ValueError("timing tree must have exactly one root")
    positive = set(positive_scopes)
    for row in spans:
        direct = sorted(
            children.get(row["span_id"], []),
            key=lambda child: (
                child["wall_start_offset_ns"],
                child["wall_end_offset_ns"],
                child["span_id"],
            ),
        )
        for left, right in zip(direct, direct[1:]):
            if left["wall_end_offset_ns"] > right["wall_start_offset_ns"]:
                raise ValueError(f"{row['span_id']}: wall siblings overlap")
            if left["cpu_end_offset_ns"] > right["cpu_start_offset_ns"]:
                raise ValueError(f"{row['span_id']}: CPU siblings overlap")
        child_wall = sum(child["wall_duration_ns"] for child in direct)
        child_cpu = sum(child["cpu_duration_ns"] for child in direct)
        if row["child_wall_ns"] != child_wall or row["child_cpu_ns"] != child_cpu:
            raise ValueError(f"{row['span_id']}: child sum mismatch")
        if row["wall_duration_ns"] != child_wall + row["unattributed_wall_ns"]:
            raise ValueError(f"{row['span_id']}: wall reconciliation failed")
        if row["cpu_duration_ns"] != child_cpu + row["unattributed_cpu_ns"]:
            raise ValueError(f"{row['span_id']}: CPU reconciliation failed")
        if row["scope"] in positive and (
            row["wall_duration_ns"] <= 0 or row["cpu_duration_ns"] <= 0
        ):
            raise ValueError(f"{row['span_id']}: required-positive scope is zero")


def build_late_telemetry_trailer(
    core_bytes: bytes,
    timing: Mapping[str, Any],
) -> bytes:
    """Build the explicitly post-root late telemetry trailer."""

    validate_layered_timing(timing)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    payload = {
        "schema": TRAILER_SCHEMA,
        "core_byte_length": len(core_bytes),
        "core_sha256": sha256_hex(core_bytes),
        "ru_maxrss_raw": int(usage.ru_maxrss),
        "ru_maxrss_units": "KiB_on_linux",
        "sample_scope": "post_worker_root_pre_trailer",
        "timing": timing,
    }
    return canonical_json_bytes(payload)


def encode_two_frames(core_bytes: bytes, trailer_bytes: bytes) -> bytes:
    for name, raw in (("core", core_bytes), ("trailer", trailer_bytes)):
        if not isinstance(raw, bytes):
            raise TypeError(f"{name} frame must be bytes")
        if len(raw) > (1 << 64) - 1:
            raise OverflowError(f"{name} frame is too large")
    return (
        struct.pack(">Q", len(core_bytes))
        + core_bytes
        + struct.pack(">Q", len(trailer_bytes))
        + trailer_bytes
    )


def decode_two_frames(
    raw: bytes,
    *,
    core_max: int,
    trailer_max: int,
) -> tuple[bytes, bytes]:
    """Parse with checked lengths and reject every trailing byte."""

    if core_max < 0 or trailer_max < 0:
        raise ValueError("frame caps must be nonnegative")
    if len(raw) < 16:
        raise ValueError("framed payload is too short")
    core_size = struct.unpack(">Q", raw[:8])[0]
    if core_size > core_max:
        raise ValueError("core frame exceeds cap")
    core_end = 8 + core_size
    if core_end + 8 > len(raw):
        raise ValueError("core frame is truncated")
    trailer_size = struct.unpack(">Q", raw[core_end : core_end + 8])[0]
    if trailer_size > trailer_max:
        raise ValueError("trailer frame exceeds cap")
    trailer_start = core_end + 8
    expected = trailer_start + trailer_size
    if expected != len(raw):
        raise ValueError("framed payload is truncated or has trailing bytes")
    return raw[8:core_end], raw[trailer_start:expected]
