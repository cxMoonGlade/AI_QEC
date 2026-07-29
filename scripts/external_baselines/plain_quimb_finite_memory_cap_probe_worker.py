#!/usr/bin/env python3
"""Calibration-only plain Quimb positive-cap probe."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any, Mapping


SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "plain_cap_probe_worker.v1"
)


def _load(name: str):
    path = Path(__file__).resolve(strict=True).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"_plain_probe_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load sibling {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_cap_probe(fixture: Mapping[str, Any], *, input_id: int) -> dict[str, Any]:
    if fixture["run_partition"] != "CALIBRATION":
        raise ValueError("cap probe is calibration only")
    common = _load("plain_quimb_finite_memory_worker_common")
    timing_module = _load("gcapeps_finite_memory_timing")
    timer = timing_module.LayeredTimer()
    with timer.span(
        "probe.root",
        scope="cap_probe_worker_total",
        kind="worker",
        lane="plain",
        case_id=fixture["case_id"],
        trajectory_id=f"input{input_id}",
    ):
        with timer.span(
            "probe.setup",
            scope="setup_and_gate_mask_materialization",
            kind="fixture_validation",
            lane="plain",
            case_id=fixture["case_id"],
            trajectory_id=f"input{input_id}",
        ):
            fixture_hash = common.validate_fixture(fixture)
        with timer.span(
            "probe.instrumented",
            scope="instrumented_replay_total",
            kind="cap_probe",
            lane="plain",
            case_id=fixture["case_id"],
            trajectory_id=f"input{input_id}",
        ):
            result = common.run_trajectory(
                fixture=fixture,
                input_id=input_id,
                instrumented=True,
                materialize_checkpoints=False,
                timer=timer,
                span_prefix="probe",
                initialization_scope="instrumented_candidate_initialization",
                stop_after_first_positive_operation=True,
            )
        with timer.span(
            "probe.serialization",
            scope="serialization",
            kind="core_encoding",
            lane="plain",
            case_id=fixture["case_id"],
            trajectory_id=f"input{input_id}",
        ):
            core = {
                "schema": SCHEMA,
                "lane": "plain",
                "role": "cap_probe",
                "case_id": fixture["case_id"],
                "input_id": input_id,
                "fixture_projection_sha256": fixture_hash,
                "stop_locator": result["stop_locator"],
                "positive_cap_event_count": sum(
                    row["positive_discarded_weight"]
                    for row in result["split_records"]
                ),
                "split_records": common.encode_split_records(
                    result["split_records"]
                ),
                "contains_complete_vector": False,
                "contains_cross_artifact_metric": False,
                "result_projection_sha256": "",
            }
            core["result_projection_sha256"] = timing_module.sha256_hex(
                timing_module.canonical_json_bytes(
                    {
                        key: value
                        for key, value in core.items()
                        if key != "result_projection_sha256"
                    }
                )
            )
            core_bytes = timing_module.canonical_json_bytes(core)
    timing = timer.finish()
    trailer_bytes = timing_module.build_late_telemetry_trailer(core_bytes, timing)
    return {
        "core": core,
        "core_bytes": core_bytes,
        "timing": timing,
        "trailer_bytes": trailer_bytes,
        "framed_bytes": timing_module.encode_two_frames(
            core_bytes,
            trailer_bytes,
        ),
    }
