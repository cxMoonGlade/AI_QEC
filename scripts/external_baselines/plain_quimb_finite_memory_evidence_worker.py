#!/usr/bin/env python3
"""Plain Quimb evidence worker for one finite-memory input trajectory."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from typing import Any, Mapping


SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "plain_evidence_worker.v1"
)


def _load(name: str):
    path = Path(__file__).resolve(strict=True).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(f"_plain_evidence_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load sibling {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run_evidence(fixture: Mapping[str, Any], *, input_id: int) -> dict[str, Any]:
    common = _load("plain_quimb_finite_memory_worker_common")
    timing_module = _load("gcapeps_finite_memory_timing")
    timer = timing_module.LayeredTimer()
    memory_tracker = common.new_memory_tracker(evidence=True)
    core: dict[str, Any]
    with timer.span(
        "evidence.root",
        scope="evidence_worker_total",
        kind="worker",
        lane="plain",
        case_id=fixture["case_id"],
        trajectory_id=f"input{input_id}",
    ):
        with timer.span(
            "evidence.setup",
            scope="setup_and_gate_mask_materialization",
            kind="fixture_validation",
            lane="plain",
            case_id=fixture["case_id"],
            trajectory_id=f"input{input_id}",
        ):
            fixture_hash = common.validate_fixture(fixture)
        with timer.span(
            "evidence.algorithm",
            scope="candidate_algorithm_case_e2e",
            kind="no_shadow_trajectory",
            lane="plain",
            case_id=fixture["case_id"],
            trajectory_id=f"input{input_id}",
        ):
            no_shadow = common.run_trajectory(
                fixture=fixture,
                input_id=input_id,
                instrumented=False,
                materialize_checkpoints=False,
                timer=timer,
                span_prefix="no_shadow",
                initialization_scope="no_shadow_candidate_initialization",
                memory_tracker=memory_tracker,
                memory_branch="base",
                record_round_continuity=True,
            )
        frozen_no_shadow = {
            "operation_count": no_shadow["operation_count"],
            "max_committed_bond": no_shadow["max_committed_bond"],
            "final_committed_bond": no_shadow["final_committed_bond"],
            "final_carrier_hash": no_shadow["final_carrier_hash"],
            "logical_memory": no_shadow["logical_memory"],
            "round_continuity_ledger": no_shadow[
                "round_continuity_ledger"
            ],
        }
        common.release_trajectory(no_shadow)
        with timer.span(
            "evidence.validation",
            scope="validation_and_evidence_materialization",
            kind="evidence",
            lane="plain",
            case_id=fixture["case_id"],
            trajectory_id=f"input{input_id}",
        ):
            with timer.span(
                "evidence.replay",
                scope="instrumented_replay_total",
                kind="instrumented_trajectory",
                lane="plain",
                case_id=fixture["case_id"],
                trajectory_id=f"input{input_id}",
            ):
                replay = common.run_trajectory(
                    fixture=fixture,
                    input_id=input_id,
                    instrumented=True,
                    materialize_checkpoints=True,
                    timer=timer,
                    span_prefix="instrumented",
                    initialization_scope="instrumented_candidate_initialization",
                    memory_tracker=memory_tracker,
                    memory_branch="evidence",
                    record_round_continuity=True,
                )
            if replay["final_carrier_hash"]["sha256"] != frozen_no_shadow[
                "final_carrier_hash"
            ]["sha256"]:
                raise ValueError("no-shadow and instrumented carrier hashes differ")
            checkpoint_rows = []
            for round_index in sorted(replay["checkpoint_vectors"]):
                vector = replay["checkpoint_vectors"][round_index]
                checkpoint_rows.append(
                    {
                        "round_index": round_index,
                        "source_branch": "instrumented_replay",
                        "pre_metric": common.vector_pre_metric(
                            vector,
                            n_qubits=fixture["geometry"]["n_qubits"],
                        ),
                        "vector": vector,
                    }
                )
        with timer.span(
            "evidence.serialization",
            scope="serialization",
            kind="core_encoding",
            lane="plain",
            case_id=fixture["case_id"],
            trajectory_id=f"input{input_id}",
        ):
            serialized_checkpoints = []
            for row in checkpoint_rows:
                pre_hash = row["pre_metric"]["raw_vector_sha256"]
                encoded = common.encode_ndarray_v1(row["vector"], dtype="<c16")
                if encoded["data_sha256"] != pre_hash:
                    raise ValueError("checkpoint vector changed before serialization")
                serialized_checkpoints.append(
                    {
                        "round_index": row["round_index"],
                        "source_branch": row["source_branch"],
                        "pre_metric": row["pre_metric"],
                        "vector": encoded,
                    }
                )
            core = {
                "schema": SCHEMA,
                "lane": "plain",
                "role": "evidence",
                "case_id": fixture["case_id"],
                "input_id": input_id,
                "fixture_projection_sha256": fixture_hash,
                "no_shadow": frozen_no_shadow,
                "instrumented_final_carrier_hash": replay[
                    "final_carrier_hash"
                ],
                "operation_count": replay["operation_count"],
                "max_exact_precompression_bond": None,
                "max_committed_bond": replay["max_committed_bond"],
                "final_committed_bond": replay["final_committed_bond"],
                "positive_cap_event_count": sum(
                    row["positive_discarded_weight"]
                    for row in replay["split_records"]
                ),
                "split_records": common.encode_split_records(
                    replay["split_records"]
                ),
                "round_continuity_ledger": replay[
                    "round_continuity_ledger"
                ],
                "checkpoints": serialized_checkpoints,
                "logical_memory": replay["logical_memory"],
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
