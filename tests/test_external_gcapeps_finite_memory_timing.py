from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
import time

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "gcapeps_finite_memory_timing.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("gcapeps_fm_timing", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_layered_timer_reconciles_nested_wall_and_cpu_exactly():
    timing = _load_module()
    timer = timing.LayeredTimer()
    with timer.span("root", scope="performance_worker_total", kind="root"):
        with timer.span(
            "setup",
            scope="setup_and_gate_mask_materialization",
            kind="setup",
        ):
            sum(range(100))
        with timer.span(
            "algorithm",
            scope="candidate_algorithm_case_e2e",
            kind="algorithm",
            lane="plain",
            case_id="case",
            trajectory_id="input1",
        ):
            with timer.span(
                "round1",
                scope="round",
                kind="round",
                round_index=1,
            ):
                sum(range(100))
        with timer.span("serialization", scope="serialization", kind="encoding"):
            time.sleep(0)
    payload = timer.finish()
    timing.validate_layered_timing(
        payload,
        positive_scopes=("performance_worker_total",),
    )
    rows = {row["span_id"]: row for row in payload["spans"]}
    root = rows["root"]
    assert root["wall_duration_ns"] == (
        root["child_wall_ns"] + root["unattributed_wall_ns"]
    )
    assert root["cpu_duration_ns"] == (
        root["child_cpu_ns"] + root["unattributed_cpu_ns"]
    )
    assert rows["round1"]["round_index"] == 1
    assert rows["round1"]["operation_index"] is None


def test_validator_rejects_overlap_and_bad_exact_identity():
    timing = _load_module()
    timer = timing.LayeredTimer()
    with timer.span("root", scope="root", kind="root"):
        with timer.span("a", scope="leaf", kind="leaf"):
            pass
        with timer.span("b", scope="leaf", kind="leaf"):
            pass
    payload = timer.finish()

    bad = copy.deepcopy(payload)
    rows = {row["span_id"]: row for row in bad["spans"]}
    rows["b"]["wall_start_offset_ns"] = rows["a"]["wall_end_offset_ns"] - 1
    rows["b"]["wall_duration_ns"] = (
        rows["b"]["wall_end_offset_ns"] - rows["b"]["wall_start_offset_ns"]
    )
    rows["root"]["child_wall_ns"] = (
        rows["a"]["wall_duration_ns"] + rows["b"]["wall_duration_ns"]
    )
    rows["root"]["unattributed_wall_ns"] = (
        rows["root"]["wall_duration_ns"] - rows["root"]["child_wall_ns"]
    )
    with pytest.raises(ValueError, match="overlap"):
        timing.validate_layered_timing(bad)

    bad = copy.deepcopy(payload)
    bad["spans"][0]["wall_duration_ns"] += 1
    with pytest.raises(ValueError, match="duration identity"):
        timing.validate_layered_timing(bad)


def test_validator_accepts_zero_leaf_but_can_require_positive_scope():
    timing = _load_module()
    timer = timing.LayeredTimer()
    with timer.span("root", scope="root", kind="root"):
        with timer.span("leaf", scope="may_be_zero", kind="leaf"):
            pass
    payload = timer.finish()
    leaf = next(row for row in payload["spans"] if row["span_id"] == "leaf")
    for family in ("wall", "cpu"):
        start = leaf[f"{family}_start_offset_ns"]
        leaf[f"{family}_end_offset_ns"] = start
        leaf[f"{family}_duration_ns"] = 0
        leaf[f"child_{family}_ns"] = 0
        leaf[f"unattributed_{family}_ns"] = 0
    root = next(row for row in payload["spans"] if row["span_id"] == "root")
    root["child_wall_ns"] = 0
    root["child_cpu_ns"] = 0
    root["unattributed_wall_ns"] = root["wall_duration_ns"]
    root["unattributed_cpu_ns"] = root["cpu_duration_ns"]
    timing.validate_layered_timing(payload)
    with pytest.raises(ValueError, match="required-positive"):
        timing.validate_layered_timing(payload, positive_scopes=("may_be_zero",))


def test_canonical_json_and_two_frame_round_trip_are_strict():
    timing = _load_module()
    core = timing.canonical_json_bytes({"z": 1, "a": "μ"})
    assert core == b'{"a":"\\u03bc","z":1}'
    trailer = timing.canonical_json_bytes({"schema": timing.TRAILER_SCHEMA})
    framed = timing.encode_two_frames(core, trailer)
    assert timing.decode_two_frames(
        framed,
        core_max=len(core),
        trailer_max=len(trailer),
    ) == (core, trailer)
    with pytest.raises(ValueError, match="trailing"):
        timing.decode_two_frames(
            framed + b"x",
            core_max=len(core),
            trailer_max=len(trailer),
        )
    with pytest.raises(ValueError, match="exceeds"):
        timing.decode_two_frames(
            framed,
            core_max=len(core) - 1,
            trailer_max=len(trailer),
        )
    with pytest.raises(ValueError, match="non-finite"):
        timing.canonical_json_bytes({"bad": float("nan")})


def test_trailer_binds_core_hash_and_completed_timing():
    timing = _load_module()
    timer = timing.LayeredTimer()
    with timer.span("root", scope="worker_total", kind="root"):
        pass
    payload = timer.finish()
    core = b'{"schema":"example"}'
    trailer = timing.build_late_telemetry_trailer(core, payload)
    decoded = json.loads(trailer)
    assert decoded["core_byte_length"] == len(core)
    assert decoded["core_sha256"] == timing.sha256_hex(core)
    assert decoded["sample_scope"] == "post_worker_root_pre_trailer"
    assert decoded["timing"] == payload
