from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts" / "external_baselines"


def _load(name):
    path = SCRIPT_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_test_gc_fm_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _fixture(*, p_event_numerator: int, axis_family: int = 1):
    emitter = _load("emit_gcapeps_finite_memory_fixture")
    return emitter.build_fixture(
        run_partition="HELDOUT",
        width=3,
        rounds=1,
        axis_family=axis_family,
        p_event_numerator=p_event_numerator,
        seed=emitter.HELDOUT_SEED,
        gamma_index=0,
        run_blpensemble=False,
    )


def _dense_checkpoints(fixture, input_id):
    dense = _load("gcapeps_finite_memory_dense_reference")
    result = dense.run_dense_reference(fixture)
    path = next(
        row for row in result["fixed_paths"] if row["input_id"] == input_id
    )
    return {
        row["round_index"]: row["vector"] for row in path["checkpoints"]
    }


def test_engine_binds_floor_smudge_mode_to_circuit():
    engine = _load("gcapeps_finite_memory_engine")
    fixture = _fixture(p_event_numerator=0)

    state = engine.GCState.initialize(
        fixture,
        input_id=2,
        instrumented=False,
    )

    assert engine.SPLIT_POLICY["smudge_mode"] == "floor"
    assert state.circuit.gate_opts["smudge_mode"] == "floor"


def test_frame_only_input_and_p0_physical_checkpoints_match_dense():
    engine = _load("gcapeps_finite_memory_engine")
    fixture = _fixture(p_event_numerator=0)
    result = engine.execute_gcapeps(
        fixture,
        input_id=2,
        instrumented=False,
        materialize_checkpoints=True,
    )
    expected = _dense_checkpoints(fixture, 2)
    assert result["pullback_rows"] == []
    assert result["max_exact_precompression_bond"] == 1
    assert result["max_committed_bond"] == 1
    assert result["logical_memory"]["tensor_role"] == "gc_residual"
    assert result["logical_memory"]["frame_bytes"] > 0
    for round_index, vector in result["checkpoint_vectors"].items():
        np.testing.assert_array_equal(vector, expected[round_index])


def test_event_path_uses_tree_compression_and_matches_dense():
    engine = _load("gcapeps_finite_memory_engine")
    fixture = _fixture(p_event_numerator=4)
    result = engine.execute_gcapeps(
        fixture,
        input_id=1,
        instrumented=False,
        materialize_checkpoints=True,
    )
    expected = _dense_checkpoints(fixture, 1)
    assert len(result["pullback_rows"]) == 3
    assert result["max_exact_precompression_bond"] == 4
    assert result["max_committed_bond"] == 8
    assert all(
        row["split"].shadow_evidence_enabled is False
        and row["split"].full_singular_values is None
        and row["split"].cause == "not_observed_without_shadow"
        for row in result["split_records"]
    )
    for round_index, vector in result["checkpoint_vectors"].items():
        np.testing.assert_allclose(
            vector,
            expected[round_index],
            rtol=2.0e-13,
            atol=2.0e-13,
        )


def test_instrumented_replay_preserves_carrier_and_emits_uncapped_spectra():
    engine = _load("gcapeps_finite_memory_engine")
    fixture = _fixture(p_event_numerator=4)
    base = engine.execute_gcapeps(
        fixture,
        input_id=2,
        instrumented=False,
        materialize_checkpoints=False,
    )
    replay = engine.execute_gcapeps(
        fixture,
        input_id=2,
        instrumented=True,
        materialize_checkpoints=True,
    )
    assert base["final_carrier_hash"]["sha256"] == replay[
        "final_carrier_hash"
    ]["sha256"]
    assert replay["split_records"]
    for row in replay["split_records"]:
        split = row["split"]
        assert split.shadow_evidence_enabled is True
        assert split.shadow_pre_split_state_sha256 == (
            split.pre_split_state_sha256
        )
        assert split.full_singular_values is not None
        assert split.kept_singular_values is not None
        assert split.full_bond_dimension == len(split.full_singular_values)
        assert split.kept_bond_dimension == len(split.kept_singular_values)


def test_frame_lift_exposes_old_new_vector_and_literal_matrix_lifetimes():
    engine = _load("gcapeps_finite_memory_engine")
    residual = np.zeros(8, dtype=np.complex128)
    residual[0] = 1.0
    samples = []

    def callback(event, roots, metadata):
        samples.append(
            {
                "event": event,
                "checkpoint": metadata.checkpoint,
                "roles": metadata.root_roles,
                "root_ids": tuple(id(root) for root in roots),
            }
        )

    result = engine._lift_frame_transcript(
        residual,
        (
            {"gate_kind": "H", "targets": [0]},
            {"gate_kind": "CX", "targets": [0, 2]},
        ),
        n_qubits=3,
        ownership_callback=callback,
    )
    assert result.dtype == np.dtype(np.complex128)
    post = [
        row for row in samples
        if row["checkpoint"].startswith("post_literal_frame_lift_")
    ]
    assert len(post) == 2
    assert all(
        row["roles"] == (
            "checkpoint_predecessor_vector",
            "literal_lift_array",
            "checkpoint_working_vector",
        )
        and row["root_ids"][0] != row["root_ids"][2]
        for row in post
    )
    assert samples[-1]["checkpoint"] == "residual_checkpoint_vector_release"


def test_gc_worker_engine_has_no_reference_plain_or_sdim_import():
    source = (
        SCRIPT_DIR / "gcapeps_finite_memory_engine.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "gcapeps_finite_memory_dense_reference",
        "plain_quimb_finite_memory",
        "compare_gcapeps_finite_memory_bond32",
        "import sdim",
        "from sdim",
        "error_coupling_simulator",
    ):
        assert forbidden not in source
