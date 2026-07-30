from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import subprocess
import sys
import threading

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = (
    ROOT
    / "scripts/external_baselines/"
    "run_gcapeps_native_trajectory_process_regression.py"
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


runner = _load("_test_gcapeps_native_trajectory_process_runner", RUNNER_PATH)
worker = _load("_test_gcapeps_native_trajectory_process_worker", WORKER_PATH)


def _fixture(seed: int) -> dict[str, object]:
    identity = runner.EXPECTED_TRAJECTORY_IDENTITIES[seed]
    return {
        "case_id": f"calibration-g2-s{seed}-w7-r4-a3-p3of4",
        "result_projection_sha256": identity["fixture"],
        "parameters": {
            "seed": seed,
            "width": 7,
            "rounds": 4,
            "axis_family": 3,
            "p_event_numerator": 3,
            "gamma_index": 2,
            "max_bond": 32,
        },
        "state_contract": {
            "joint_state_retained_across_rounds": True,
            "memory_row_policy": "never_discard_reset_or_recreate",
            "candidate_restart_between_rounds": False,
        },
        "carrier_path": {
            "full_mask_sha256": identity["mask"],
            "realized_event_count": identity["events"],
        },
    }


def _fixtures():
    return runner.build_frozen_trajectory_fixtures()


def _child(seed: int, *, state: str | None = None):
    return {
        "seed": seed,
        "state": state if state is not None else f"state-{seed}",
        "source_identity": {"shared_test_identity": True},
        "supervisor_process_receipt": {
            "parent_observed_wall_duration_ns": 100 + seed,
        },
    }


def _batch_receipt(mode: str, wall: int):
    return runner._batch_receipt(
        mode=mode,
        process_count=4,
        children={seed: _child(seed) for seed in runner.TRAJECTORY_SEEDS},
        wall_duration_ns=wall,
        cpu_duration_ns=5,
    )


def _overall_receipt():
    return runner._overall_receipt(
        wall_duration_ns=1000,
        cpu_duration_ns=10,
        serial_child_count=4,
        parallel_child_count=4,
    )


def _patch_report_helpers(monkeypatch, *, witness=True):
    validations = []

    def validate(child, *, fixture, thread_count, strategy, shadow_evidence):
        validations.append(
            (
                child["seed"],
                fixture["parameters"]["seed"],
                thread_count,
                strategy,
                shadow_evidence,
            )
        )

    def compare(left, right, *, name):
        passed = left["state"] == right["state"]
        return {"name": name, "passed": passed, "checkpoints": {}}

    monkeypatch.setattr(
        runner.thread_runner, "_validate_child_identity", validate
    )
    monkeypatch.setattr(runner.thread_runner, "_pair_comparison", compare)
    monkeypatch.setattr(
        runner.thread_runner,
        "_timing_inventory",
        lambda child: {"seed": child["seed"], "substeps": True},
    )
    monkeypatch.setattr(
        runner.thread_runner,
        "select_nondegeneracy_witness",
        lambda child: {"seed": child["seed"]} if witness else None,
    )
    return validations


def test_frozen_family_contains_four_distinct_persistent_memory_trajectories():
    fixtures = runner.build_frozen_trajectory_fixtures()
    assert tuple(fixtures) == runner.TRAJECTORY_SEEDS
    assert {
        fixture["carrier_path"]["full_mask_sha256"]
        for fixture in fixtures.values()
    }.__len__() == 4
    for seed, fixture in fixtures.items():
        assert fixture["parameters"]["seed"] == seed
        assert fixture["state_contract"][
            "joint_state_retained_across_rounds"
        ] is True
        assert fixture["state_contract"]["memory_row_policy"] == (
            "never_discard_reset_or_recreate"
        )


def test_trajectory_family_discloses_exact_partial_round_and_event_prefix():
    fixtures = runner.build_frozen_trajectory_fixtures()
    rows = runner._trajectory_family_projection(fixtures)
    expected_partial_site = {
        0: (16, 2), 1: (16, 2), 2: (17, 3), 3: (20, 6)
    }
    for row in rows:
        seed = row["trajectory_seed"]
        prefix = row["executed_prefix"]
        event_row_index, site_index = expected_partial_site[seed]
        assert row["fixture_total_realized_event_count"] in (22, 24)
        assert prefix == {
            "fixture_declared_rounds": 4,
            "first_operation_index": 0,
            "stop_after_operation_inclusive": 100,
            "executed_operation_count": 101,
            "last_executed_round_index": 3,
            "completed_round_indices": [1, 2],
            "partial_round_index": 3,
            "round_4_executed": False,
            "executed_collision_rotation_count": 44,
            "completed_event_count": 14,
            "partial_event": {
                "round_index": 3,
                "event_row_index": event_row_index,
                "site_index": site_index,
                "executed_axes": ["X", "Y"],
                "remaining_axes": ["Z"],
                "next_fixture_operation_index": 101,
            },
        }



def test_worker_accepts_exact_registered_trajectory_fixture_family():
    fixtures = runner.build_frozen_trajectory_fixtures()
    for seed, fixture in fixtures.items():
        worker.validate_registered_trajectory_fixture(
            fixture,
            fixture["result_projection_sha256"],
        )
        assert worker.REGISTERED_TRAJECTORY_FIXTURES[seed] == {
            "case_id": fixture["case_id"],
            "fixture_projection_sha256": (
                runner.EXPECTED_TRAJECTORY_IDENTITIES[seed]["fixture"]
            ),
        }



def test_worker_rejects_seed_case_and_hash_outside_registered_family():
    fixture = runner.build_frozen_trajectory_fixtures()[0]
    wrong_seed = {
        **fixture,
        "parameters": {**fixture["parameters"], "seed": 4},
    }
    with pytest.raises(ValueError, match="outside the registered family"):
        worker.validate_registered_trajectory_fixture(
            wrong_seed,
            fixture["result_projection_sha256"],
        )

    wrong_case = {**fixture, "case_id": "calibration-forged"}
    with pytest.raises(ValueError, match="case_id drifted"):
        worker.validate_registered_trajectory_fixture(
            wrong_case,
            fixture["result_projection_sha256"],
        )

    with pytest.raises(ValueError, match="fixture hash drifted"):
        worker.validate_registered_trajectory_fixture(
            fixture,
            "0" * 64,
        )


def test_parallel_batch_uses_fresh_one_thread_child_per_trajectory(monkeypatch):
    calls = []
    lock = threading.Lock()
    barrier = threading.Barrier(4)
    active = 0
    maximum_active = 0

    def fake_run_one(*, fixture, fork_python, timeout_seconds, shadow_evidence):
        nonlocal active, maximum_active
        seed = fixture["parameters"]["seed"]
        with lock:
            active += 1
            maximum_active = max(maximum_active, active)
            calls.append(
                (seed, fork_python, timeout_seconds, shadow_evidence)
            )
        barrier.wait(timeout=2.0)
        with lock:
            active -= 1
        return _child(seed)

    monkeypatch.setattr(runner, "_run_one_trajectory", fake_run_one)
    children, receipt = runner._run_batch(
        fixtures=_fixtures(),
        fork_python=Path("/fake/fork-python"),
        timeout_seconds=12.0,
        mode="parallel",
        process_count=4,
    )
    assert tuple(children) == runner.TRAJECTORY_SEEDS
    assert sorted(seed for seed, *_rest in calls) == [0, 1, 2, 3]
    assert all(call[-1] is False for call in calls)
    assert receipt["scientific_compute_unit"] == "fresh_subprocess"
    assert receipt["configured_scientific_threads_per_child"] == 1
    assert receipt["configured_maximum_scientific_children"] == 4
    assert receipt["orchestration"] == (
        "thread_pool_waiting_on_fresh_subprocesses"
    )
    assert maximum_active == 4


def test_report_passes_schedule_invariance_independent_of_speed(monkeypatch):
    validations = _patch_report_helpers(monkeypatch)
    fixtures = _fixtures()
    serial = {seed: _child(seed) for seed in runner.TRAJECTORY_SEEDS}
    parallel = {seed: _child(seed) for seed in runner.TRAJECTORY_SEEDS}
    evidence = _child(runner.EVIDENCE_SEED)
    report = runner.build_report(
        fixtures=fixtures,
        serial_children=serial,
        parallel_children=parallel,
        evidence_child=evidence,
        serial_batch_receipt=_batch_receipt("serial", 100),
        parallel_batch_receipt=_batch_receipt("parallel", 200),
        overall_execution_receipt=_overall_receipt(),
    )
    assert report["passed"] is True
    assert report["verdict"] == (
        "PASS_ENGINEERING_TRAJECTORY_PROCESS_REGRESSION"
    )
    assert report["performance_claim"] is False
    assert report["non_markovianity_claim"] is False
    assert report["timing"][
        "observed_serial_over_parallel_wall_ratio_diagnostic_only"
    ] == pytest.approx(0.5)
    assert report["trajectory_execution_model"][
        "parallel_unit"
    ] == "distinct_seeded_persistent_memory_unitary_prefix"
    assert len(validations) == 9
    assert all(row[2] == 1 for row in validations)


def test_report_fails_one_changed_trajectory_or_missing_witness(monkeypatch):
    _patch_report_helpers(monkeypatch)
    fixtures = _fixtures()
    serial = {seed: _child(seed) for seed in runner.TRAJECTORY_SEEDS}
    parallel = {seed: _child(seed) for seed in runner.TRAJECTORY_SEEDS}
    parallel[3]["state"] = "changed-under-parallel-schedule"
    report = runner.build_report(
        fixtures=fixtures,
        serial_children=serial,
        parallel_children=parallel,
        evidence_child=_child(runner.EVIDENCE_SEED),
        serial_batch_receipt=_batch_receipt("serial", 200),
        parallel_batch_receipt=_batch_receipt("parallel", 100),
        overall_execution_receipt=_overall_receipt(),
    )
    assert report["passed"] is False
    assert report["process_schedule_invariance"]["comparisons"]["3"][
        "passed"
    ] is False

    _patch_report_helpers(monkeypatch, witness=False)
    parallel[3]["state"] = serial[3]["state"]
    no_witness = runner.build_report(
        fixtures=fixtures,
        serial_children=serial,
        parallel_children=parallel,
        evidence_child=_child(runner.EVIDENCE_SEED),
        serial_batch_receipt=_batch_receipt("serial", 200),
        parallel_batch_receipt=_batch_receipt("parallel", 100),
        overall_execution_receipt=_overall_receipt(),
    )
    assert no_witness["passed"] is False
    assert no_witness["nondegeneracy_passed"] is False


def test_run_one_trajectory_binds_one_thread_native_child(monkeypatch):
    fixture = _fixture(2)
    captured = {}

    def fake_run_child(**kwargs):
        captured.update(kwargs)
        return {"child": "ok"}

    monkeypatch.setattr(runner.thread_runner, "_run_child", fake_run_child)
    result = runner._run_one_trajectory(
        fixture=fixture,
        fork_python=Path("/fork/python"),
        timeout_seconds=17.0,
        shadow_evidence=False,
    )
    assert result == {"child": "ok"}
    assert captured == {
        "fixture_bytes": runner.thread_runner._canonical_json_bytes(fixture),
        "fork_python": Path("/fork/python"),
        "thread_count": 1,
        "strategy": runner.thread_runner.NATIVE_STRATEGY,
        "shadow_evidence": False,
        "timeout_seconds": 17.0,
    }


def test_report_rejects_rehashed_batch_and_overall_receipt_corruption(
    monkeypatch,
):
    _patch_report_helpers(monkeypatch)
    fixtures = _fixtures()
    serial = {seed: _child(seed) for seed in runner.TRAJECTORY_SEEDS}
    parallel = {seed: _child(seed) for seed in runner.TRAJECTORY_SEEDS}
    evidence = _child(runner.EVIDENCE_SEED)
    serial_receipt = _batch_receipt("serial", 100)
    serial_receipt["mode"] = "parallel"
    serial_receipt["result_projection_sha256"] = (
        runner.thread_runner._projection_sha256(
            {
                key: value
                for key, value in serial_receipt.items()
                if key != "result_projection_sha256"
            }
        )
    )
    with pytest.raises(ValueError, match="batch receipt"):
        runner.build_report(
            fixtures=fixtures,
            serial_children=serial,
            parallel_children=parallel,
            evidence_child=evidence,
            serial_batch_receipt=serial_receipt,
            parallel_batch_receipt=_batch_receipt("parallel", 200),
            overall_execution_receipt=_overall_receipt(),
        )

    overall = _overall_receipt()
    overall["scientific_child_count"] = 0
    overall["result_projection_sha256"] = (
        runner.thread_runner._projection_sha256(
            {
                key: value
                for key, value in overall.items()
                if key != "result_projection_sha256"
            }
        )
    )
    with pytest.raises(ValueError, match="overall receipt"):
        runner.build_report(
            fixtures=fixtures,
            serial_children=serial,
            parallel_children=parallel,
            evidence_child=evidence,
            serial_batch_receipt=_batch_receipt("serial", 100),
            parallel_batch_receipt=_batch_receipt("parallel", 200),
            overall_execution_receipt=overall,
        )


def test_report_rejects_cross_child_source_identity_drift(monkeypatch):
    _patch_report_helpers(monkeypatch)
    fixtures = _fixtures()
    serial = {seed: _child(seed) for seed in runner.TRAJECTORY_SEEDS}
    parallel = {seed: _child(seed) for seed in runner.TRAJECTORY_SEEDS}
    parallel[3]["source_identity"] = {"different_runtime": True}
    with pytest.raises(ValueError, match="source/runtime identities differ"):
        runner.build_report(
            fixtures=fixtures,
            serial_children=serial,
            parallel_children=parallel,
            evidence_child=_child(runner.EVIDENCE_SEED),
            serial_batch_receipt=_batch_receipt("serial", 100),
            parallel_batch_receipt=_batch_receipt("parallel", 200),
            overall_execution_receipt=_overall_receipt(),
        )



def test_process_receipts_reject_bool_or_float_integer_fields():
    children = {
        seed: _child(seed) for seed in runner.TRAJECTORY_SEEDS
    }
    children[0]["supervisor_process_receipt"][
        "parent_observed_wall_duration_ns"
    ] = True
    with pytest.raises(ValueError, match="child wall timing types"):
        runner._batch_receipt(
            mode="serial",
            process_count=4,
            children=children,
            wall_duration_ns=100,
            cpu_duration_ns=5,
        )

    with pytest.raises(ValueError, match="overall child counts"):
        runner._overall_receipt(
            wall_duration_ns=100,
            cpu_duration_ns=5,
            serial_child_count=True,
            parallel_child_count=4,
        )

    with pytest.raises(ValueError, match="overall timing"):
        runner._overall_receipt(
            wall_duration_ns=100.0,
            cpu_duration_ns=5,
            serial_child_count=4,
            parallel_child_count=4,
        )


@pytest.mark.parametrize("value", [True, 0, 1, 5, -1])
def test_process_count_rejects_non_multicore_or_out_of_range(value):
    with pytest.raises(ValueError, match=r"\[2, 4\]"):
        runner._validate_process_count(value)


def test_runner_has_no_top_level_scientific_import():
    tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
    forbidden = {"numpy", "quimb", "stim", "numba", "scipy"}
    for node in tree.body:
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        names = (
            [alias.name for alias in node.names]
            if isinstance(node, ast.Import)
            else [node.module or ""]
        )
        assert not {
            name.split(".", 1)[0] for name in names
        }.intersection(forbidden)


def test_cli_help_does_not_run_trajectories():
    completed = subprocess.run(
        [sys.executable, str(RUNNER_PATH), "--help"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert "--processes" in completed.stdout
    assert completed.stderr == ""
