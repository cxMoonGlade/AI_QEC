"""Focused contracts for the independent finite-memory dense reference."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import importlib.util
import math
from pathlib import Path
import struct
import subprocess
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "gcapeps_finite_memory_dense_reference.py"
)
EMITTER_PATH = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "emit_gcapeps_finite_memory_fixture.py"
)


def _load_module():
    name = "gcapeps_finite_memory_dense_reference_test"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_emitter():
    name = "emit_gcapeps_finite_memory_fixture_dense_test"
    spec = importlib.util.spec_from_file_location(name, EMITTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _literal_fixture(
    dense,
    *,
    rounds: int = 2,
    probability_numerator: int = 3,
    run_ensemble: bool = False,
):
    emitter = _load_emitter()
    fixture = emitter.build_fixture(
        run_partition="HELDOUT",
        width=7 if run_ensemble else 3,
        rounds=rounds,
        axis_family=3,
        p_event_numerator=probability_numerator,
        seed=emitter.HELDOUT_SEED,
        gamma_index=0,
        run_blpensemble=run_ensemble,
    )
    assert emitter.validate_fixture(fixture) == fixture["result_projection_sha256"]
    assert fixture["schema"] == dense.FIXTURE_SCHEMA
    return fixture


def test_q0_msb_gate_application_has_direct_known_answers():
    dense = _load_module()
    state = np.zeros(4, dtype=np.complex128)
    state[2] = 1.0  # |10>, q0 is the most-significant bit.
    updated = dense.apply_gate_q0_msb(
        state,
        dense.cx_matrix(),
        (0, 1),
        num_qubits=2,
    )
    expected = np.zeros(4, dtype=np.complex128)
    expected[3] = 1.0  # CX(q0 -> q1): |10> -> |11>.
    assert np.array_equal(updated, expected)

    reverse = dense.apply_gate_q0_msb(
        state,
        dense.cx_matrix(),
        (1, 0),
        num_qubits=2,
    )
    assert np.array_equal(reverse, state)  # q1 is zero, so no flip.


def test_partial_swap_sign_and_analytic_global_phase_are_pinned():
    dense = _load_module()
    gamma = np.float64(0.37)
    product = (
        dense.pauli_rotation_matrix("X", -gamma)
        @ dense.pauli_rotation_matrix("Y", -gamma)
        @ dense.pauli_rotation_matrix("Z", -gamma)
    )
    expected = np.exp(-0.5j * gamma) * dense.partial_swap_matrix(gamma)
    assert np.max(np.abs(product - expected)) <= 1.0e-12

    opposite = (
        dense.pauli_rotation_matrix("X", gamma)
        @ dense.pauli_rotation_matrix("Y", gamma)
        @ dense.pauli_rotation_matrix("Z", gamma)
    )
    pivot = np.unravel_index(np.argmax(np.abs(expected)), expected.shape)
    phase = opposite[pivot] / expected[pivot]
    phase /= abs(phase)
    assert np.max(np.abs(opposite - phase * expected)) > 1.0e-2

    audit = dense.partial_swap_factorization_audit(float(gamma))
    assert set(audit["ordered_product_max_abs_errors"]) == {
        "XYZ",
        "XZY",
        "YXZ",
        "YZX",
        "ZXY",
        "ZYX",
    }
    assert max(audit["ordered_product_max_abs_errors"].values()) <= 1.0e-12
    assert audit["sum_instead_of_product_max_abs_residual"] > 1.0e-2
    assert audit["removed_global_phase_max_abs_residual"] > 1.0e-2
    assert audit["opposite_rotation_sign_max_abs_residual"] > 1.0e-2
    assert audit["phase_fit_used"] is False
    assert audit["passed"] is True


def test_runtime_import_audit_rejects_new_forbidden_module(monkeypatch):
    dense = _load_module()
    clean = dense.audit_import_independence()
    assert clean["passed"] is True
    assert clean["forbidden_static_import_roots"] == []
    assert clean["newly_loaded_forbidden_modules"] == []
    assert clean["forbidden_bound_global_modules"] == []

    monkeypatch.setitem(
        sys.modules,
        "quimb.provenance_corruption",
        object(),
    )
    with pytest.raises(RuntimeError, match="import independence audit failed"):
        dense.audit_import_independence()


def test_q0_msb_system_partial_trace_and_entropy_are_known():
    dense = _load_module()
    bell = np.asarray([1.0, 0.0, 0.0, 1.0], dtype=np.complex128)
    bell /= math.sqrt(2.0)
    diagnostic = dense.reduced_state_diagnostics(bell, width=1)
    assert np.max(
        np.abs(diagnostic["reduced_state"] - np.eye(2) / 2.0)
    ) <= 1.0e-15
    assert diagnostic["entropy_s1"] == pytest.approx(1.0)
    assert diagnostic["entropy_s2"] == pytest.approx(1.0)
    assert np.allclose(
        diagnostic["normalized_schmidt_values"],
        np.asarray([1.0, 1.0]) / math.sqrt(2.0),
    )

    memory_one = np.asarray([0.0, 1.0, 0.0, 0.0], dtype=np.complex128)
    system_one = np.asarray([0.0, 0.0, 1.0, 0.0], dtype=np.complex128)
    rho_memory = dense.reduced_state_diagnostics(
        memory_one, width=1
    )["reduced_state"]
    rho_system = dense.reduced_state_diagnostics(
        system_one, width=1
    )["reduced_state"]
    assert dense.trace_distance(
        np.diag([1.0, 0.0]).astype(np.complex128),
        rho_memory,
    )["value"] == pytest.approx(0.0)
    assert dense.trace_distance(
        np.diag([1.0, 0.0]).astype(np.complex128),
        rho_system,
    )["value"] == pytest.approx(1.0)


def test_p0_run_has_structural_no_interaction_and_unit_distances(monkeypatch):
    dense = _load_module()
    materializations: list[str] = []
    releases: list[str] = []
    original_materialized = dense._ArrayLedger.sample_materialized
    original_pre_release = dense._ArrayLedger.sample_pre_release

    def record_materialized(self, label, *arrays):
        materializations.append(label)
        return original_materialized(self, label, *arrays)

    def record_pre_release(self, label, *arrays):
        releases.append(label)
        return original_pre_release(self, label, *arrays)

    monkeypatch.setattr(
        dense._ArrayLedger, "sample_materialized", record_materialized
    )
    monkeypatch.setattr(
        dense._ArrayLedger, "sample_pre_release", record_pre_release
    )

    fixture = _literal_fixture(
        dense,
        rounds=2,
        probability_numerator=0,
        run_ensemble=True,
    )
    result = dense.run_dense_reference(fixture)

    assert result["p_event_zero_control"]["passed"] is True
    assert result["p_event_zero_control"]["active_axis_rotation_count"] == 0
    assert result["fixed_blp"]["trace_distances"] == pytest.approx(
        [1.0, 1.0, 1.0],
        abs=1.0e-12,
    )
    assert result["finite_32_mask_ensemble"]["blp"][
        "trace_distances"
    ] == pytest.approx([1.0, 1.0, 1.0], abs=1.0e-12)
    assert all(
        checkpoint["entropy_s1"] <= 1.0e-12
        and checkpoint["entropy_s2"] <= 1.0e-12
        for path in result["fixed_paths"]
        for checkpoint in path["checkpoints"]
    )
    ensemble = result["finite_32_mask_ensemble"]
    assert len(ensemble["paths"]) == 64
    assert ensemble["weights"] == [1.0 / 32.0] * 32
    assert ensemble["aggregation_order"] == (
        "average_density_matrices_before_trace_distance"
    )
    assert {
        "state.initial.materialized",
        "state.operation.materialized",
        "checkpoint.vector.materialized",
        "reduced_state.rho.materialized",
        "reduced_state.hermitian.materialized",
        "reduced_state.eigensystem.materialized",
        "reduced_state.schmidt.materialized",
        "ensemble.accumulator.materialized",
        "ensemble.accumulator_update.materialized",
        "ensemble.average.materialized",
        "ensemble.hermitian.materialized",
        "ensemble.eigensystem.materialized",
        "comparison.difference.materialized",
        "comparison.eigensystem.materialized",
    }.issubset(materializations)
    assert {
        "state.operation.predecessor.pre_release",
        "state.path.pre_release",
        "reduced_state.validation_auxiliaries.pre_release",
        "reduced_state.amplitude_view.pre_release",
        "reduced_state.positive_eigenvalues.pre_release",
        "ensemble.accumulator.pre_release",
        "ensemble.average_validation.pre_release",
        "comparison.difference.pre_release",
        "dense_reference.result_arrays.pre_release",
    }.issubset(releases)


def test_dense_array_ledger_counts_unique_roots_and_ownership_peaks():
    dense = _load_module()
    ledger = dense._ArrayLedger()
    root = np.zeros(16, dtype=np.complex128)
    view = root.reshape(4, 4)[:, :2]
    other = np.zeros(7, dtype=np.float64)

    ledger.sample_materialized("state.materialized", root, view)
    assert ledger.current == 0
    assert ledger.maximum == root.nbytes

    retained = ledger.retain(
        root,
        label="state.retained",
        coexisting_arrays=(view, other),
    )
    assert retained is root
    assert ledger.current == root.nbytes
    assert ledger.maximum == root.nbytes + other.nbytes

    ledger.sample_pre_release(
        "state.pre_release", root, view, other
    )
    assert ledger.maximum == root.nbytes + other.nbytes
    assert ledger.sample_labels == (
        "state.materialized",
        "state.retained.materialized",
        "state.retained.retained",
        "state.pre_release",
    )


def test_dense_result_memory_matches_unique_persistent_array_roots():
    dense = _load_module()
    result = dense.run_dense_reference(
        _literal_fixture(
            dense,
            rounds=2,
            probability_numerator=3,
            run_ensemble=False,
        )
    )
    roots: dict[int, np.ndarray] = {}

    def collect(value):
        if isinstance(value, np.ndarray):
            root = dense.root_array(value)
            roots[id(root)] = root
        elif isinstance(value, dict):
            for child in value.values():
                collect(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                collect(child)

    collect(result)
    expected_final = sum(int(root.nbytes) for root in roots.values())
    assert result["final_dense_reference_array_bytes"] == expected_final
    assert (
        result["max_sampled_dense_reference_array_bytes"]
        > result["final_dense_reference_array_bytes"]
    )



def test_raw_vector_and_fixture_corruptions_fail_before_metrics():
    dense = _load_module()
    with pytest.raises(ValueError, match="shape"):
        dense.validate_raw_vector(np.ones(2, dtype=np.complex128), width=1)
    with pytest.raises(ValueError, match="complex128"):
        dense.validate_raw_vector(np.ones(4, dtype=np.complex64), width=1)
    with pytest.raises(ValueError, match="positive"):
        dense.validate_raw_vector(np.zeros(4, dtype=np.complex128), width=1)
    bad = np.ones(4, dtype=np.complex128)
    bad[0] = np.nan
    with pytest.raises(ValueError, match="nonfinite"):
        dense.validate_raw_vector(bad, width=1)

    fixture = _literal_fixture(dense)
    broken = copy.deepcopy(fixture)
    broken["carrier_path"]["event_rows"][0]["event"] = True
    broken["result_projection_sha256"] = dense.canonical_sha256(broken)
    with pytest.raises(ValueError, match="event rows"):
        dense.run_dense_reference(broken)
    broken = copy.deepcopy(fixture)
    broken["carrier_path"]["round_ledger"][0]["operations"].reverse()
    broken["result_projection_sha256"] = dense.canonical_sha256(broken)
    with pytest.raises(ValueError, match="operation"):
        dense.run_dense_reference(broken)



def test_reduced_state_guards_clip_only_tiny_negative_and_reject_corruption(
    monkeypatch,
):
    dense = _load_module()
    tiny = np.ascontiguousarray(
        np.diag([1.0 + 5.0e-13, -5.0e-13]),
        dtype=np.complex128,
    )
    diagnostic = dense.validate_reduced_state(tiny)
    assert diagnostic["minimum_raw_eigenvalue"] == pytest.approx(-5.0e-13)
    assert diagnostic["negative_eigenvalue_mass"] == pytest.approx(5.0e-13)
    assert diagnostic["normalized_eigenvalues"] == pytest.approx([0.0, 1.0])

    nonhermitian = np.asarray(
        [[1.0, 1.0e-3], [0.0, 0.0]],
        dtype=np.complex128,
    )
    with pytest.raises(ValueError, match="Hermiticity"):
        dense.validate_reduced_state(nonhermitian)
    bad_trace = np.diag([0.9, 0.0]).astype(np.complex128)
    with pytest.raises(ValueError, match="trace"):
        dense.validate_reduced_state(bad_trace)
    gross_negative = np.diag([1.01, -0.01]).astype(np.complex128)
    with pytest.raises(ValueError, match="eigen"):
        dense.validate_reduced_state(gross_negative)

    pure = np.diag([1.0, 0.0]).astype(np.complex128)
    monkeypatch.setattr(
        dense.np.linalg,
        "eigh",
        lambda _rho: (
            np.asarray([0.0, 1.0], dtype=np.float64),
            np.eye(2, dtype=np.complex128),
        ),
    )
    with pytest.raises(ValueError, match="eigen reconstruction"):
        dense.validate_reduced_state(pure)


def test_ndarray_v1_is_exact_little_endian_and_rejects_corruption():
    dense = _load_module()
    array = np.asarray([complex(-0.0, 1.25), 2.0 - 3.0j], dtype="<c16")
    encoded = dense.ndarray_v1(array, dtype="<c16", shape=(2,))
    decoded = dense.decode_ndarray_v1(encoded, dtype="<c16", shape=(2,))
    assert decoded.tobytes(order="C") == array.tobytes(order="C")

    bad = copy.deepcopy(encoded)
    bad["data_base64"] = bad["data_base64"].rstrip("=")
    with pytest.raises(ValueError):
        dense.decode_ndarray_v1(bad, dtype="<c16", shape=(2,))
    bad = copy.deepcopy(encoded)
    bad["data_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash"):
        dense.decode_ndarray_v1(bad, dtype="<c16", shape=(2,))



def test_core_serialization_and_two_frame_timing_are_canonical():
    dense = _load_module()
    fixture = _literal_fixture(
        dense,
        rounds=2,
        probability_numerator=3,
        run_ensemble=False,
    )
    framed = dense.build_framed_worker_output(fixture)
    core_size = struct.unpack(">Q", framed[:8])[0]
    core_end = 8 + core_size
    trailer_size = struct.unpack(">Q", framed[core_end : core_end + 8])[0]
    assert core_end + 8 + trailer_size == len(framed)
    core_bytes = framed[8:core_end]
    trailer_bytes = framed[core_end + 8 :]
    core = json.loads(core_bytes)
    trailer = json.loads(trailer_bytes)
    assert dense.canonical_json_bytes(core) == core_bytes
    assert dense.canonical_json_bytes(trailer) == trailer_bytes
    assert core["schema"] == dense.SCHEMA
    assert core["result_projection_sha256"] == dense.canonical_sha256(core)
    assert trailer["core_byte_length"] == len(core_bytes)
    assert trailer["core_sha256"] == hashlib.sha256(core_bytes).hexdigest()
    assert trailer["sample_scope"] == "post_worker_root_pre_trailer"
    spans = {row["span_id"]: row for row in trailer["timing"]["spans"]}
    root = spans["dense_reference_worker_total"]
    assert root["wall_duration_ns"] == (
        root["child_wall_ns"] + root["unattributed_wall_ns"]
    )
    assert root["cpu_duration_ns"] == (
        root["child_cpu_ns"] + root["unattributed_cpu_ns"]
    )
    encoded_vector = core["fixed_paths"][0]["checkpoints"][0]["vector"]
    assert encoded_vector["dtype"] == "<c16"
    assert encoded_vector["shape"] == [64]
    assert encoded_vector["data_sha256"] == core["fixed_paths"][0][
        "checkpoints"
    ][0]["raw_vector_guard"]["vector_data_sha256"]


def test_dense_source_and_fresh_process_have_import_firewall():
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(MODULE_PATH))
    assert "gcapeps_finite_memory_logical_memory" not in source
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots.isdisjoint(
        {
            "error_coupling_simulator",
            "gcapeps",
            "quimb",
            "sdim",
            "stim",
        }
    )

    program = "\n".join(
        (
            "import importlib.util, json, pathlib, sys",
            f"path = pathlib.Path({str(MODULE_PATH)!r})",
            "spec = importlib.util.spec_from_file_location('dense_runtime', path)",
            "module = importlib.util.module_from_spec(spec)",
            "sys.modules[spec.name] = module",
            "spec.loader.exec_module(module)",
            "forbidden = sorted(name for name in sys.modules if "
            "name.split('.', 1)[0] in "
            "{'error_coupling_simulator','gcapeps','quimb','sdim','stim'})",
            "print(json.dumps(forbidden))",
        )
    )
    completed = subprocess.run(
        [sys.executable, "-I", "-c", program],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stderr == ""
    assert completed.stdout.strip() == "[]"
