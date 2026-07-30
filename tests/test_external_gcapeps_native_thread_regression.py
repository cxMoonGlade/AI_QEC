from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = (
    ROOT
    / "scripts/external_baselines/run_gcapeps_native_thread_regression.py"
)
WORKER_PATH = (
    ROOT / "scripts/external_baselines/gcapeps_native_thread_worker.py"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = _load("_test_gcapeps_native_thread_runner", RUNNER_PATH)
worker = _load("_test_gcapeps_native_thread_worker", WORKER_PATH)


def _encode(vector: np.ndarray) -> dict[str, object]:
    assert vector.dtype == np.dtype(np.complex128)
    raw = vector.tobytes(order="C")
    return {
        "encoding": "ndarray-v1",
        "dtype": "<c16",
        "shape": list(vector.shape),
        "order": "C",
        "nbytes": len(raw),
        "data_sha256": hashlib.sha256(raw).hexdigest(),
        "data_base64": base64.b64encode(raw).decode("ascii"),
    }


def _timing(*, evidence: bool) -> dict[str, object]:
    scopes = (
        ("child_total", "fresh_process_worker"),
        ("initialization", "candidate_initialization"),
        ("physical_operation", "PAULI_ROTATION"),
        ("named_algorithm_substep", "native_compile"),
        ("checkpoint_contraction", "raw_complete_physical_vector"),
        ("serialization", "raw_vector_encoding"),
        ("publication_accounting", "core_projection"),
    )
    if evidence:
        scopes += (("evidence_shadow", "uncapped_shadow_replay:3"),)
    spans = []
    for index, (scope, kind) in enumerate(scopes):
        spans.append(
            {
                "span_id": f"span-{index}",
                "parent_span_id": None if index == 0 else "span-0",
                "scope": scope,
                "lane": "gcapeps",
                "case_id": "calibration-g2-s2-w7-r4-a3-p3of4",
                "trajectory_id": "input2",
                "round_index": None,
                "operation_index": None,
                "step_index": None,
                "kind": kind,
                "status": "completed",
                "wall_start_offset_ns": index,
                "wall_end_offset_ns": index + 1,
                "wall_duration_ns": 1,
                "cpu_start_offset_ns": index,
                "cpu_end_offset_ns": index + 1,
                "cpu_duration_ns": 1,
                "child_wall_ns": 0,
                "child_cpu_ns": 0,
                "unattributed_wall_ns": 1,
                "unattributed_cpu_ns": 1,
            }
        )
    return {
        "schema": (
            "error_coupling_simulator.external.gcapeps_finite_memory."
            "layered_timing.v1"
        ),
        "wall_clock": "time.perf_counter_ns",
        "cpu_clock": "time.process_time_ns",
        "spans": spans,
    }


def _metadata(operation_index: int) -> dict[str, object]:
    request = {
        "run_partition": "CALIBRATION",
        "case_id": "calibration-g2-s2-w7-r4-a3-p3of4",
        "input_id": 2,
        "input_preparation_transcript_sha256": "a" * 64,
        "shared_evolution_transcript_sha256": "b" * 64,
        "round_prefix": 3,
        "collision_ordinal": operation_index - 57,
        "round_index": 3,
        "site_index": 3,
        "axis_index": operation_index - 99,
        "physical_pauli_body": (
            "IIIXIIIIIIXIII"
            if operation_index == 99
            else "IIIYIIIIIIYIII"
        ),
    }
    return {
        "operation_index": operation_index,
        "round_index": 3,
        "physical_request": request,
        "physical_pauli": f"+{request['physical_pauli_body']}",
        "signed_pulled_word": "+YXXZIZYIXXYZII",
        "pullback": {
            **request,
            "physical_sign": 1,
            "physical_body": request["physical_pauli_body"],
            "pulled_back_sign": 1,
            "pulled_back_body": "YXXZIZYIXXYZII",
        },
        "strategy": "native_simple_update",
        "update_strategy": (
            "native_graph_local_pauli_rotation_simple_update"
        ),
        "routing_root": 10,
        "routing_vertices": [2, 3, 9, 10],
        "routing_tree_edges": [[2, 3], [2, 9], [3, 10]],
        "configured_max_bond": 32,
        "configured_cutoff": 0.0,
        "plan_digest_sha256": (
            "c" * 63 + str(operation_index % 10)
        ),
        "canonical_gate_transcript": {
            "schema": "quimb.experimental.gcapeps.native_plan.v1",
            "operation_index": operation_index,
        },
        "candidate_kept_dimensions": [32],
    }


def _child(
    fixture,
    *,
    threads: int,
    evidence: bool,
    vector_delta: complex = 0.0j,
) -> dict[str, object]:
    vector = np.zeros(1 << 14, dtype=np.complex128)
    vector[0] = 1.0 + vector_delta
    encoded = _encode(vector)
    pre_metric = {
        "raw_vector_sha256": encoded["data_sha256"],
        "raw_norm_squared_real": float(np.vdot(vector, vector).real),
        "raw_norm_squared_imag_abs": 0.0,
        "stored_vector_normalized_before_metric": False,
        "metric_local_normalized_copy": True,
        "phase_fit": False,
        "coordinate_permutation": False,
        "dtype_cast": False,
    }
    records = []
    for operation_index in (99, 100):
        metadata = _metadata(operation_index)
        split = {
            "step_index": 3,
            "edge": [2, 3],
            "candidate_kept_bond_dimension": 32,
            "full_bond_dimension": 64 if evidence else None,
            "discarded_fraction": 1.0e-4 if evidence else None,
            "cause": (
                "max_bond"
                if evidence
                else "not_observed_without_shadow"
            ),
        }
        metadata["native_execution_ledger"] = {
            "shadow_evidence_bytes": 4096 if evidence else 0,
            "split_records": [split],
        }
        metadata["native_truncation_ledger"] = (
            {"split_records": [split]} if evidence else None
        )
        records.append(metadata)
    checkpoints = {
        str(index): {
            "operation_index": index,
            "pre_metric": pre_metric,
            "vector": encoded,
        }
        for index in (99, 100)
    }
    return {
        "schema": (
            "error_coupling_simulator.external.gcapeps_finite_memory."
            "native_thread_worker.v1"
        ),
        "formal_claim_eligible": False,
        "faithfulness_claim": False,
        "performance_claim": False,
        "lane": "gcapeps_native_finite_cap_development",
        "strategy": "native_simple_update",
        "legacy_diagnostic_only": False,
        "shadow_evidence_enabled": evidence,
        "environment": {
            "requested_thread_count": threads,
            "thread_variables": {
                name: str(threads) for name in runner.THREAD_VARIABLES
            },
            "CUDA_VISIBLE_DEVICES": "",
            "PYTHONHASHSEED": "0",
            "PYTHONPATH_present": False,
            "validated_before_numpy_quimb_stim_import": True,
        },
        "fixture_identity": {
            "case_id": fixture["case_id"],
            "fixture_projection_sha256": fixture[
                "result_projection_sha256"
            ],
            "operation_prefix_count": 101,
            "operation_prefix_sha256": "d" * 64,
            "input_id": 2,
            "stop_after_operation": 100,
            "checkpoint_operations": [99, 100],
        },
        "split_policy": dict(runner.EXPECTED_SPLIT_POLICY),
        "operation_count": 101,
        "checkpoint_metadata": {
            str(index): records[offset]
            for offset, index in enumerate((99, 100))
        },
        "operation_records": records,
        "checkpoints": checkpoints,
        "shadow_builder_call_count": 1 if evidence else 0,
        "shadow_span_count": 1 if evidence else 0,
        "shadow_evidence_bytes": 8192 if evidence else 0,
        "shadow_builder_instrumentation": {
            "no_shadow_uses_throwing_sentinel": not evidence,
            "evidence_uses_counting_wrapper": evidence,
            "original_builder_restored_before_return": True,
        },
        "source_identity": {},
        "stdout_write_included_in_timing": False,
        "claim_boundary": "test fixture",
        "result_projection_sha256": "e" * 64,
        "timing": _timing(evidence=evidence),
        "supervisor_process_receipt": {
            "thread_count": threads,
            "strategy": "native_simple_update",
            "shadow_evidence": evidence,
            "returncode": 0,
            "parent_observed_wall_duration_ns": 1,
            "stdout_nbytes": 1,
            "stdout_sha256": "f" * 64,
            "stderr_nbytes": 0,
        },
    }


def _as_legacy(child):
    child["lane"] = "gcapeps_exact_tree_compress_diagnostic_only"
    child["strategy"] = "exact_tree_then_native_compress"
    child["legacy_diagnostic_only"] = True
    child["supervisor_process_receipt"]["strategy"] = (
        "exact_tree_then_native_compress"
    )
    for row in child["operation_records"]:
        row["strategy"] = "exact_tree_then_native_compress"
        row["update_strategy"] = (
            "exact_tree_then_native_identity_compress"
        )
    return child


def _replace_checkpoint_vector(child, operation_index, vector):
    encoded = _encode(vector)
    child["checkpoints"][str(operation_index)] = {
        "operation_index": operation_index,
        "pre_metric": {
            "raw_vector_sha256": encoded["data_sha256"],
            "raw_norm_squared_real": float(np.vdot(vector, vector).real),
            "raw_norm_squared_imag_abs": 0.0,
            "stored_vector_normalized_before_metric": False,
            "metric_local_normalized_copy": True,
            "phase_fit": False,
            "coordinate_permutation": False,
            "dtype_cast": False,
        },
        "vector": encoded,
    }


def test_frozen_fixture_is_exact_operation_100_cell():
    fixture = runner.build_frozen_fixture()
    assert fixture["result_projection_sha256"] == (
        "4a2abe4d32c15af833d849a62b55c45a3cb23f79383976352efaf02e1f91a463"
    )
    operations = [
        operation
        for round_row in fixture["carrier_path"]["round_ledger"]
        for operation in round_row["operations"]
    ]
    assert len(operations) == 148
    assert operations[99]["physical_pauli_body"] == "IIIXIIIIIIXIII"
    assert operations[100]["physical_pauli_body"] == "IIIYIIIIIIYIII"


def test_child_environment_sets_all_five_threads_and_removes_pythonpath():
    parent = {"PATH": "/bin", "PYTHONPATH": "/forbidden", "KEEP": "yes"}
    environment = runner.child_environment(parent, thread_count=4)
    assert environment["KEEP"] == "yes"
    assert "PYTHONPATH" not in environment
    assert environment["CUDA_VISIBLE_DEVICES"] == ""
    assert environment["PYTHONHASHSEED"] == "0"
    assert {
        environment[name] for name in runner.THREAD_VARIABLES
    } == {"4"}


def test_worker_validates_environment_before_scientific_imports():
    environment = runner.child_environment(os.environ, thread_count=1)
    code = (
        "import importlib.util,pathlib,sys;"
        f"p=pathlib.Path({str(WORKER_PATH)!r});"
        "s=importlib.util.spec_from_file_location('fresh_worker',p);"
        "m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;"
        "s.loader.exec_module(m);"
        "r=m.validate_child_environment(1);"
        "print(r['validated_before_numpy_quimb_stim_import'])"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=environment,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert completed.stdout.strip() == "True"
    assert completed.stderr == ""


def test_raw_metrics_do_not_fit_global_phase():
    reference = np.array([1.0 + 0.0j, 0.0j], dtype=np.complex128)
    candidate = np.array([0.0 + 1.0j, 0.0j], dtype=np.complex128)
    result = runner.raw_complete_vector_metrics(reference, candidate)
    assert result["metrics"]["fidelity"] == pytest.approx(1.0)
    assert result["metrics"]["d2_raw"] == pytest.approx(np.sqrt(2.0))
    assert result["metrics"]["phase_fit"] is False
    assert result["passed"] is False


def test_raw_metrics_reject_zero_and_nonfinite_vectors():
    good = np.array([1.0 + 0.0j], dtype=np.complex128)
    with pytest.raises(ValueError, match="strictly positive"):
        runner.raw_complete_vector_metrics(
            np.array([0.0j], dtype=np.complex128),
            good,
        )
    with pytest.raises(ValueError, match="finite c128"):
        runner.raw_complete_vector_metrics(
            np.array([complex(np.nan, 0.0)], dtype=np.complex128),
            good,
        )


def test_report_passes_exact_native_pairs_and_positive_witness():
    fixture = runner.build_frozen_fixture()
    thread1 = _child(fixture, threads=1, evidence=False)
    thread4 = _child(fixture, threads=4, evidence=False)
    evidence = _child(fixture, threads=1, evidence=True)
    report = runner.build_report(
        fixture=fixture,
        native_thread1=thread1,
        native_thread4=thread4,
        native_evidence_thread1=evidence,
    )
    assert report["passed"] is True
    assert report["verdict"] == "PASS_ENGINEERING_NATIVE_THREAD_REGRESSION"
    assert report["nondegeneracy_witness"] == {
        "operation_index": 99,
        "round_index": 3,
        "split_index": 0,
        "native_step_index": 3,
        "edge": [2, 3],
        "full_bond_dimension": 64,
        "kept_bond_dimension": 32,
        "cause": "max_bond",
        "discarded_fraction": 1.0e-4,
    }
    assert report["formal_claim_eligible"] is False
    assert report["faithfulness_claim"] is False
    assert report["performance_claim"] is False
    assert report["split_policy"] == runner.EXPECTED_SPLIT_POLICY


def test_report_fails_on_cross_thread_vector_or_metadata_change():
    fixture = runner.build_frozen_fixture()
    thread1 = _child(fixture, threads=1, evidence=False)
    thread4 = _child(
        fixture,
        threads=4,
        evidence=False,
        vector_delta=1.0e-4,
    )
    thread4["checkpoint_metadata"]["100"]["routing_root"] = 9
    evidence = _child(fixture, threads=1, evidence=True)
    report = runner.build_report(
        fixture=fixture,
        native_thread1=thread1,
        native_thread4=thread4,
        native_evidence_thread1=evidence,
    )
    assert report["passed"] is False
    assert report["thread_invariance"]["checkpoints"]["99"][
        "raw_metrics"
    ]["passed"] is False
    assert report["thread_invariance"]["checkpoints"]["100"][
        "exact_metadata_equal"
    ] is False


def test_requested_legacy_lane_must_be_red_at_operation_100():
    fixture = runner.build_frozen_fixture()
    native1 = _child(fixture, threads=1, evidence=False)
    native4 = _child(fixture, threads=4, evidence=False)
    evidence = _child(fixture, threads=1, evidence=True)
    legacy1 = _as_legacy(_child(fixture, threads=1, evidence=False))
    legacy4 = _as_legacy(_child(fixture, threads=4, evidence=False))
    unexpectedly_green = runner.build_report(
        fixture=fixture,
        native_thread1=native1,
        native_thread4=native4,
        native_evidence_thread1=evidence,
        legacy_children=(legacy1, legacy4),
    )
    assert unexpectedly_green["legacy_diagnostic"][
        "violates_at_least_one_native_band_at_operation_100"
    ] is False
    assert unexpectedly_green["passed"] is False

    divergent = np.zeros(1 << 14, dtype=np.complex128)
    divergent[1] = 1.0
    _replace_checkpoint_vector(legacy4, 100, divergent)
    required_red = runner.build_report(
        fixture=fixture,
        native_thread1=native1,
        native_thread4=native4,
        native_evidence_thread1=evidence,
        legacy_children=(legacy1, legacy4),
    )
    assert required_red["legacy_diagnostic"][
        "violates_at_least_one_native_band_at_operation_100"
    ] is True
    assert required_red["passed"] is True


def test_report_rejects_split_policy_drift():
    fixture = runner.build_frozen_fixture()
    thread1 = _child(fixture, threads=1, evidence=False)
    thread4 = _child(fixture, threads=4, evidence=False)
    evidence = _child(fixture, threads=1, evidence=True)
    thread4["split_policy"]["smudge_mode"] = "floor"

    with pytest.raises(ValueError, match="split policy drifted"):
        runner.build_report(
            fixture=fixture,
            native_thread1=thread1,
            native_thread4=thread4,
            native_evidence_thread1=evidence,
        )


def test_worker_binds_and_verifies_add_smudge_mode():
    source = WORKER_PATH.read_text(encoding="utf-8")
    assert (
        '"smudge_mode": engine.SPLIT_POLICY["smudge_mode"]' in source
    )
    assert 'circuit.gate_opts.get("smudge_mode")' in source


def test_worker_source_has_throwing_and_counting_shadow_instrumentation():
    source = WORKER_PATH.read_text(encoding="utf-8")
    assert "def forbidden_shadow_builder" in source
    assert "no-shadow execution invoked the evidence builder" in source
    assert "def counted_shadow_builder" in source
    assert '"shadow_builder_call_count": shadow_builder_calls' in source


def test_worker_module_has_no_top_level_scientific_import():
    source = WORKER_PATH.read_text(encoding="utf-8")
    tree = __import__("ast").parse(source)
    forbidden = {"numpy", "quimb", "stim"}
    for node in tree.body:
        if isinstance(node, (__import__("ast").Import, __import__("ast").ImportFrom)):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, __import__("ast").Import)
                else [node.module or ""]
            )
            assert not {
                name.split(".", 1)[0] for name in names
            }.intersection(forbidden)


def test_cli_help_does_not_run_target():
    for script in (WORKER_PATH, RUNNER_PATH):
        completed = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert "usage:" in completed.stdout
        assert completed.stderr == ""
