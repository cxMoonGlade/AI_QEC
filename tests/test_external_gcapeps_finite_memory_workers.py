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
    spec = importlib.util.spec_from_file_location(f"_test_gc_worker_{name}", path)
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
        rounds=1,
        axis_family=1,
        p_event_numerator=4,
        seed=emitter.HELDOUT_SEED,
        gamma_index=0,
        run_blpensemble=False,
    )


def test_evidence_has_two_replays_vectors_pullbacks_and_no_cross_metrics():
    worker = _load("gcapeps_finite_memory_evidence_worker")
    result = worker.run_evidence(_heldout_fixture(), input_id=1)
    core = result["core"]
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
                    "lane": "gcapeps",
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
    assert core["signed_pullback_rows"]
    assert core["checkpoints"]
    assert all(
        row["source_branch"] == "instrumented_replay"
        and row["vector"]["encoding"] == "ndarray-v1"
        for row in core["checkpoints"]
    )
    scopes = [row["scope"] for row in result["timing"]["spans"]]
    assert scopes.count("instrumented_replay_total") == 1
    assert "validation_and_evidence_materialization" in scopes
    kinds = {
        row["kind"]
        for row in result["timing"]["spans"]
        if row["scope"] == "named_instrumented_algorithm_substep"
    }
    assert "frame_composition" in kinds
    assert "signed_pullback" in kinds
    assert "route_planning" in kinds
    assert "exact_PEPO_lowering" in kinds
    assert "construction_validation" in kinds
    assert "native_identity_compression" in kinds
    assert "compression_validation" in kinds
    assert "candidate_commit" in kinds

    split_spans = [
        row for row in result["timing"]["spans"]
        if row["kind"].startswith("native_compression_split:")
    ]
    shadow_spans = [
        row for row in result["timing"]["spans"]
        if row["scope"] == "uncapped_shadow_replay"
    ]
    assert len(split_spans) == 2 * len(core["split_records"])
    assert len(shadow_spans) == len(core["split_records"])
    memory = core["logical_memory"]
    assert (
        memory["final_committed_owned_logical_bytes"]
        <= memory["max_committed_owned_logical_bytes"]
        <= memory["max_sampled_algorithm_owned_logical_bytes"]
    )
    assert memory["max_sampled_evidence_owned_logical_bytes"] > memory[
        "final_committed_owned_logical_bytes"
    ]
    assert "max_sampled_evidence_owned_logical_bytes" not in core[
        "no_shadow"
    ]["logical_memory"]

def test_performance_omits_vectors_spectra_tail_and_evidence():
    worker = _load("gcapeps_finite_memory_performance_worker")
    result = worker.run_performance(_heldout_fixture(), input_id=1)
    core = result["core"]
    assert core["contains_evidence"] is False
    serialized = result["core_bytes"]
    for forbidden in (
        b"checkpoint",
        b"singular_values",
        b"discarded_squared_weight",
        b"positive_cap_event",
        b"signed_pullback_rows",
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


def test_cap_probe_rejects_heldout_fixture():
    worker = _load("gcapeps_finite_memory_cap_probe_worker")
    try:
        worker.run_cap_probe(_heldout_fixture(), input_id=1)
    except ValueError as error:
        assert "calibration only" in str(error)
    else:
        raise AssertionError("held-out fixture unexpectedly entered cap probe")


def test_gc_worker_sources_do_not_import_reference_plain_sdim_or_comparator():
    for name in (
        "gcapeps_finite_memory_engine",
        "gcapeps_finite_memory_worker_common",
        "gcapeps_finite_memory_evidence_worker",
        "gcapeps_finite_memory_performance_worker",
        "gcapeps_finite_memory_cap_probe_worker",
    ):
        source = (SCRIPT_DIR / f"{name}.py").read_text(encoding="utf-8")
        for forbidden in (
            "gcapeps_finite_memory_dense_reference",
            "plain_quimb_finite_memory",
            "compare_gcapeps_finite_memory_bond32",
            "import sdim",
            "from sdim",
            "import error_coupling_simulator",
            "from error_coupling_simulator",
        ):
            assert forbidden not in source
