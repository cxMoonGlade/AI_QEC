from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts" / "external_baselines"


def _load(name):
    path = SCRIPT_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_test_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _heldout_fixture():
    emitter = _load("emit_gcapeps_finite_memory_fixture")
    return emitter.build_fixture(
        run_partition="HELDOUT",
        width=3,
        rounds=2,
        axis_family=3,
        p_event_numerator=4,
        seed=emitter.HELDOUT_SEED,
        gamma_index=0,
        run_blpensemble=False,
    )


def test_evidence_has_two_replays_raw_vectors_and_no_cross_metrics():
    worker = _load("plain_quimb_finite_memory_evidence_worker")
    result = worker.run_evidence(_heldout_fixture(), input_id=1)
    core = result["core"]
    assert core["positive_cap_event_count"] >= 0
    assert core["contains_cross_artifact_metric"] is False
    assert core["no_shadow"]["final_carrier_hash"]["sha256"] == core[
        "instrumented_final_carrier_hash"
    ]["sha256"]
    assert core["round_continuity_ledger"] == core["no_shadow"][
        "round_continuity_ledger"
    ]
    assert core["round_continuity_ledger"][-1][
        "round_end_state_sha256"
    ] == core["instrumented_final_carrier_hash"]["sha256"]
    for row in core["split_records"]:
        projection = dict(row)
        binding = projection.pop("spectrum_producer_binding_sha256")
        expected = hashlib.sha256(
            json.dumps(
                {
                    "schema": (
                        "error_coupling_simulator.external."
                        "gcapeps_finite_memory.split_spectrum_producer.v1"
                    ),
                    "lane": "plain",
                    "split_row": projection,
                },
                ensure_ascii=True,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("ascii")
        ).hexdigest()
        assert binding == expected
        assert row["pre_split_state_sha256"] == row[
            "shadow_pre_split_state_sha256"
        ]
    assert core["checkpoints"]
    assert all(
        row["source_branch"] == "instrumented_replay"
        and row["vector"]["encoding"] == "ndarray-v1"
        for row in core["checkpoints"]
    )
    scopes = [row["scope"] for row in result["timing"]["spans"]]
    assert scopes.count("instrumented_replay_total") == 1
    assert "validation_and_evidence_materialization" in scopes
    memory = core["logical_memory"]
    assert (
        memory["final_committed_owned_logical_bytes"]
        <= memory["max_committed_owned_logical_bytes"]
        <= memory["max_sampled_algorithm_owned_logical_bytes"]
    )
    assert memory["max_sampled_evidence_owned_logical_bytes"] > 0
    assert memory["max_sampled_evidence_owned_logical_bytes"] > memory[
        "final_committed_owned_logical_bytes"
    ]
    assert "max_sampled_evidence_owned_logical_bytes" not in core[
        "no_shadow"
    ]["logical_memory"]


def test_performance_omits_vectors_spectra_and_evidence():
    worker = _load("plain_quimb_finite_memory_performance_worker")
    result = worker.run_performance(_heldout_fixture(), input_id=1)
    core = result["core"]
    assert core["contains_evidence"] is False
    serialized = result["core_bytes"]
    for forbidden in (
        b"checkpoint",
        b"singular_values",
        b"discarded_squared_weight",
        b"positive_cap_event",
    ):
        assert forbidden not in serialized
    scopes = [row["scope"] for row in result["timing"]["spans"]]
    assert "candidate_algorithm_case_e2e" in scopes
    assert "validation_and_evidence_materialization" not in scopes
    memory = core["logical_memory"]
    assert (
        memory["final_committed_owned_logical_bytes"]
        <= memory["max_committed_owned_logical_bytes"]
        <= memory["max_sampled_algorithm_owned_logical_bytes"]
    )
    assert "max_sampled_evidence_owned_logical_bytes" not in memory


def test_plain_worker_sources_have_no_forbidden_imports():
    for name in (
        "plain_quimb_finite_memory_worker_common",
        "plain_quimb_finite_memory_evidence_worker",
        "plain_quimb_finite_memory_performance_worker",
        "plain_quimb_finite_memory_cap_probe_worker",
    ):
        source = (SCRIPT_DIR / f"{name}.py").read_text(encoding="utf-8")
        for forbidden in (
            "quimb.experimental.gcapeps",
            "import stim",
            "from stim",
            "import sdim",
            "from sdim",
            "gcapeps_finite_memory_dense_reference",
            "compare_gcapeps_finite_memory_bond32",
        ):
            assert forbidden not in source
