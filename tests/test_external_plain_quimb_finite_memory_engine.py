from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
from numpy.testing import assert_allclose


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


def _fixture(*, p=2, rounds=2, axis=3):
    emitter = _load("emit_gcapeps_finite_memory_fixture")
    return emitter.build_fixture(
        run_partition="HELDOUT",
        width=3,
        rounds=rounds,
        axis_family=axis,
        p_event_numerator=p,
        seed=emitter.HELDOUT_SEED,
        gamma_index=0,
        run_blpensemble=False,
    )


def test_plain_no_shadow_and_instrumented_replay_are_identical():
    engine = _load("plain_quimb_finite_memory_engine")
    fixture = _fixture(p=4)
    base = engine.execute_plain(
        fixture,
        input_id=2,
        instrumented=False,
        materialize_checkpoints=True,
    )
    evidence = engine.execute_plain(
        fixture,
        input_id=2,
        instrumented=True,
        materialize_checkpoints=True,
    )
    assert base["final_carrier_hash"]["sha256"] == evidence[
        "final_carrier_hash"
    ]["sha256"]
    assert base["state"].circuit.num_gates == base["operation_count"]
    assert evidence["state"].circuit.num_gates == evidence["operation_count"]
    for checkpoint in fixture["checkpoints"]:
        assert_allclose(
            base["checkpoint_vectors"][checkpoint],
            evidence["checkpoint_vectors"][checkpoint],
            rtol=0.0,
            atol=1.0e-12,
        )
    assert evidence["split_records"]


def test_plain_initial_inputs_use_physical_tensor_not_round_gate():
    engine = _load("plain_quimb_finite_memory_engine")
    fixture = _fixture(p=0, rounds=1, axis=1)
    input1 = engine.PlainState.initialize(fixture, 1)
    input2 = engine.PlainState.initialize(fixture, 2)
    assert input1.circuit.num_gates == 0
    assert input2.circuit.num_gates == 0
    expected1 = np.zeros(64, dtype=np.complex128)
    expected2 = np.zeros(64, dtype=np.complex128)
    expected1[0] = 1.0
    expected2[16] = 1.0
    assert_allclose(input1.state_vector(), expected1, atol=0.0)
    assert_allclose(input2.state_vector(), expected2, atol=0.0)


def test_plain_p0_has_no_cross_row_rotation_and_preserves_pair_overlap():
    engine = _load("plain_quimb_finite_memory_engine")
    fixture = _fixture(p=0, rounds=2, axis=3)
    first = engine.execute_plain(
        fixture,
        input_id=1,
        instrumented=False,
        materialize_checkpoints=True,
    )
    second = engine.execute_plain(
        fixture,
        input_id=2,
        instrumented=False,
        materialize_checkpoints=True,
    )
    assert all(
        not row["collision_rotations"]
        for row in fixture["carrier_path"]["round_ledger"]
    )
    for checkpoint in fixture["checkpoints"]:
        assert abs(
            np.vdot(
                first["checkpoint_vectors"][checkpoint],
                second["checkpoint_vectors"][checkpoint],
            )
        ) < 1.0e-12


def test_plain_source_has_no_gcapeps_stim_sdim_or_evaluator_import():
    source = (
        SCRIPT_DIR / "plain_quimb_finite_memory_engine.py"
    ).read_text(encoding="utf-8")
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

def test_plain_ownership_callback_covers_shadow_release_and_substeps():
    engine = _load("plain_quimb_finite_memory_engine")
    fixture = _fixture(p=4, rounds=1, axis=1)
    state = engine.PlainState.initialize(fixture, 1)
    operation = next(
        operation
        for row in fixture["carrier_path"]["round_ledger"]
        for operation in row["operations"]
        if len(operation["targets"]) == 2
    )
    events = []

    def callback(event, roots, metadata):
        events.append(
            (
                event,
                metadata["checkpoint"],
                metadata["root_roles"],
                len(roots),
            )
        )

    record = state.apply_operation(
        operation,
        instrumented=True,
        ownership_callback=callback,
    )
    assert record is not None
    checkpoints = [row[1] for row in events]
    assert checkpoints.index("uncapped_shadow_copy") < checkpoints.index(
        "pre_uncapped_shadow_release"
    )
    assert checkpoints.index("pre_uncapped_shadow_release") < (
        checkpoints.index("post_uncapped_shadow_release")
    )
    assert checkpoints.index("post_uncapped_shadow_release") < (
        checkpoints.index("pre_capped_native_split")
    )
    assert checkpoints[-1] == "post_split_ledger_validation"
    release = next(row for row in events if row[0] == "release")
    assert "uncapped_shadow" in release[2]


def test_plain_ownership_callback_must_return_none():
    engine = _load("plain_quimb_finite_memory_engine")
    fixture = _fixture(p=0, rounds=1, axis=1)
    state = engine.PlainState.initialize(fixture, 1)
    operation = fixture["carrier_path"]["round_ledger"][0]["operations"][0]
    with np.testing.assert_raises_regex(
        TypeError,
        "ownership_callback must return None",
    ):
        state.apply_operation(
            operation,
            instrumented=False,
            ownership_callback=lambda *_: object(),
        )
