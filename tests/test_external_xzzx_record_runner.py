"""Terminal-runner contracts for the frozen XZZX PEPS experiment."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
RUNNER_PATH = (
    REPO
    / "scripts"
    / "external_baselines"
    / "run_xzzx_record_peps_experiment.py"
)


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_xzzx_record_peps_experiment_under_test",
        RUNNER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _point(
    *,
    branch: str,
    bond: int,
    fidelity: float,
    verdict: str = "useful_conditioned_trajectory",
    radius: str | int = "complete",
) -> dict:
    return {
        "branch_id": branch,
        "bond_dimension": bond,
        "rdm_radius": radius,
        "fidelity": fidelity,
        "verdict": verdict,
    }


def test_execution_plan_pins_order_and_never_adds_d5_D8() -> None:
    runner = _load_runner()
    plan = runner.execution_plan()

    assert plan["rounds"] == 2
    assert plan["d2"] == {
        "distance": 2,
        "bond_dimensions": [8],
        "rdm_radii": ["complete"],
        "raw_support_size": 1024,
        "record_support_size": 64,
    }
    assert plan["d3"]["branches"] == ["primary", "alternate"]
    assert plan["d3"]["bond_dimensions"] == [1, 2, 4, 8]
    assert plan["d3"]["rdm_radii"] == ["complete"]
    assert plan["d5"]["branches"] == ["primary"]
    assert plan["d5"]["bond_dimensions"] == [1, 2, 4]
    assert plan["d5"]["rdm_radii"] == [0, 1, 2, 3]
    assert [row["bond"] for row in plan["d5"]["points"]] == [
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        2,
        4,
        4,
        4,
        4,
    ]
    assert [row["radius"] for row in plan["d5"]["points"]] == [
        0,
        1,
        2,
        3,
        0,
        1,
        2,
        3,
        0,
        1,
        2,
        3,
    ]
    assert all(row["bond"] != 8 for row in plan["d5"]["points"])


def test_child_environment_removes_python_and_conda_inheritance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    monkeypatch.setenv("PYTHONPATH", "/forbidden")
    monkeypatch.setenv("VIRTUAL_ENV", "/forbidden")
    monkeypatch.setenv("CONDA_PREFIX", "/forbidden")
    monkeypatch.setenv("CONDA_DEFAULT_ENV", "forbidden")
    monkeypatch.setenv("_CE_CONDA", "forbidden")
    monkeypatch.setenv("LD_PRELOAD", "/forbidden")
    monkeypatch.setenv("CUDA_HOME", "/forbidden")
    monkeypatch.setenv("OMP_NUM_THREADS", "99")
    monkeypatch.setenv("ECS_FORCE_UNFACTORIZED_AXIS1", "1")

    environment = runner.child_environment()

    assert "PYTHONPATH" not in environment
    assert "VIRTUAL_ENV" not in environment
    assert "CONDA_PREFIX" not in environment
    assert "CONDA_DEFAULT_ENV" not in environment
    assert "_CE_CONDA" not in environment
    assert "LD_PRELOAD" not in environment
    assert "CUDA_HOME" not in environment
    assert "ECS_FORCE_UNFACTORIZED_AXIS1" not in environment
    assert environment["PYTHONNOUSERSITE"] == "1"
    assert environment["CUDA_VISIBLE_DEVICES"] == "0"
    assert environment["OMP_NUM_THREADS"] == "1"
    assert environment["OPENBLAS_NUM_THREADS"] == "1"


def test_d3_gate_is_conjunctive_and_checks_bond_movement() -> None:
    runner = _load_runner()
    points = []
    for branch in ("primary", "alternate"):
        points.extend(
            [
                _point(branch=branch, bond=1, fidelity=0.9800),
                _point(branch=branch, bond=2, fidelity=0.9850),
                _point(branch=branch, bond=4, fidelity=0.9920),
                _point(branch=branch, bond=8, fidelity=0.9950),
            ]
        )
    passed = runner.evaluate_d3_gate(
        control_processes_passed=True,
        d2_comparison={"passes": True},
        exact_dense_comparisons={
            "primary": {"passes": True},
            "alternate": {"passes": True},
        },
        d3_points=points,
    )
    assert passed["passes"] is True
    assert passed["primary"]["bond_knob_movement"] == pytest.approx(0.015)
    assert passed["alternate"]["monotonic_non_decreasing"] is True

    reported_miss = [dict(row) for row in points]
    reported_miss[2]["fidelity"] = 0.996
    nonmonotonic = runner.evaluate_d3_gate(
        control_processes_passed=True,
        d2_comparison={"passes": True},
        exact_dense_comparisons={
            "primary": {"passes": True},
            "alternate": {"passes": True},
        },
        d3_points=reported_miss,
    )
    assert nonmonotonic["primary"]["monotonic_non_decreasing"] is False
    assert nonmonotonic["passes"] is True

    no_movement = [dict(row) for row in points]
    for row in no_movement:
        if row["branch_id"] == "alternate":
            row["fidelity"] = 0.995
    assert runner.evaluate_d3_gate(
        control_processes_passed=True,
        d2_comparison={"passes": True},
        exact_dense_comparisons={
            "primary": {"passes": True},
            "alternate": {"passes": True},
        },
        d3_points=no_movement,
    )["passes"] is False

    bad_alternate = [dict(row) for row in points]
    bad_alternate[-1]["verdict"] = "state_useful_mass_unresolved"
    assert runner.evaluate_d3_gate(
        control_processes_passed=True,
        d2_comparison={"passes": True},
        exact_dense_comparisons={
            "primary": {"passes": True},
            "alternate": {"passes": True},
        },
        d3_points=bad_alternate,
    )["passes"] is False

    unavailable = [dict(row) for row in points]
    unavailable[3]["fidelity"] = None
    unavailable[3]["verdict"] = "unavailable"
    unavailable_gate = runner.evaluate_d3_gate(
        control_processes_passed=True,
        d2_comparison={"passes": True},
        exact_dense_comparisons={
            "primary": {"passes": True},
            "alternate": {"passes": True},
        },
        d3_points=unavailable,
    )
    assert unavailable_gate["passes"] is False
    assert unavailable_gate["primary"]["all_points_available"] is False


def test_d5_terminal_verdict_is_only_D4_radius3() -> None:
    runner = _load_runner()
    points = [
        _point(
            branch="primary",
            bond=bond,
            radius=radius,
            fidelity=0.97,
            verdict="marginal_state",
        )
        for bond in (1, 2, 4)
        for radius in (0, 1, 2, 3)
    ]
    points[-1] = _point(
        branch="primary",
        bond=4,
        radius=3,
        fidelity=0.995,
    )
    summary = runner.summarize_d5(points)
    assert summary["all_registered_points_present"] is True
    assert summary["terminal_point"] == points[-1]
    assert summary["verdict"] == "pass"

    points[-1] = {
        **points[-1],
        "verdict": "state_useful_mass_unresolved",
    }
    assert runner.summarize_d5(points)["verdict"] == (
        "state_useful_mass_unresolved"
    )


def test_resource_gate_rejects_over_limit_or_nonintegral_evidence() -> None:
    runner = _load_runner()
    summary = {
        "resource_usage": {
            "python_peak_rss_bytes": runner.HOST_LIMIT_BYTES,
            "peak_device_allocated_bytes": runner.DEVICE_LIMIT_BYTES,
        }
    }
    assert runner.validate_resource_usage(summary) == {
        "python_peak_rss_bytes": runner.HOST_LIMIT_BYTES,
        "peak_device_allocated_bytes": runner.DEVICE_LIMIT_BYTES,
    }

    summary["resource_usage"]["peak_device_allocated_bytes"] += 1
    with pytest.raises(RuntimeError, match="device"):
        runner.validate_resource_usage(summary)
    summary["resource_usage"]["peak_device_allocated_bytes"] = 0.5
    with pytest.raises(RuntimeError, match="integer"):
        runner.validate_resource_usage(summary)

    exact = {
        "resource_usage": {
            "wall_seconds": 12.5,
            "peak_host_rss_kib": 2048,
            "peak_device_allocation_bytes": 0,
        }
    }
    assert runner.validate_exact_resource_usage(exact) == {
        "wall_seconds": 12.5,
        "python_peak_rss_bytes": 2 * 1024**2,
        "peak_device_allocated_bytes": 0,
    }


def test_fresh_process_records_wall_and_peak_host_rss(tmp_path: Path) -> None:
    runner = _load_runner()
    row = runner.run_fresh_process(
        label="true-control",
        command=["/bin/true"],
        log_path=tmp_path / "true.log",
        timeout_seconds=5,
    )
    assert row["returncode"] == 0
    assert row["timed_out"] is False
    assert row["fresh_process_group"] is True
    assert isinstance(row["peak_host_rss_bytes"], int)
    assert 0 <= row["peak_host_rss_bytes"] <= runner.HOST_LIMIT_BYTES
    assert Path(row["resource_log_path"]).is_file()


def test_artifact_manifest_rejects_symlinks(tmp_path: Path) -> None:
    runner = _load_runner()
    regular = tmp_path / "regular.txt"
    regular.write_text("bound", encoding="utf-8")
    (tmp_path / "alias.txt").symlink_to(regular)
    with pytest.raises(RuntimeError, match="symlink"):
        runner._artifact_manifest(tmp_path)


def _patch_terminal_dependencies(
    runner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    d2_passes: bool,
) -> tuple[list[tuple], list[str]]:
    events: list[tuple] = []
    verify_events: list[str] = []
    frozen = {
        "git_head": "a" * 40,
        "repository_is_shallow": False,
        "committed_inputs": {},
    }

    def verify():
        verify_events.append("verify")
        return frozen

    monkeypatch.setattr(runner, "verify_frozen_inputs", verify)
    monkeypatch.setattr(
        runner,
        "verify_artifact_only_review",
        lambda _frozen: {"status": "pass"},
    )
    monkeypatch.setattr(runner, "GPU_LOCK", tmp_path / "gpu.lock")
    monkeypatch.setattr(
        runner,
        "run_unit_and_corruption_controls",
        lambda **_kwargs: {"status": "passed"},
    )

    fixture_paths: dict[int, dict[str, Path]] = {}
    for distance in (2, 3, 5):
        rows = {}
        for name in ("fixture", "stim", "spec"):
            path = tmp_path / f"d{distance}_{name}"
            path.write_text(f"{distance}-{name}", encoding="utf-8")
            rows[name] = path
        fixture_paths[distance] = rows
    monkeypatch.setattr(
        runner,
        "materialize_fixture",
        lambda *, distance, **_kwargs: fixture_paths[distance],
    )
    monkeypatch.setattr(
        runner,
        "run_d2_complete_law_gate",
        lambda **_kwargs: {"status": "completed", "passes": d2_passes},
    )

    def exact(*, distance, mode, **_kwargs):
        events.append(("exact", distance, mode))
        prefix = f"d{distance}_{mode}"
        paths = {}
        for name in ("summary", "state", "branch"):
            path = tmp_path / f"{prefix}_{name}"
            path.write_text(name, encoding="utf-8")
            paths[f"{name}_path"] = str(path)
        return {
            "status": "completed",
            "distance": distance,
            "branch_role": mode,
            "branch_id": mode,
            **paths,
        }

    monkeypatch.setattr(runner, "run_exact_reference", exact)

    def dense(*, mode, **_kwargs):
        events.append(("dense", mode))
        summary = tmp_path / f"dense_{mode}.json"
        state = tmp_path / f"dense_{mode}.npy"
        summary.write_text("{}", encoding="utf-8")
        state.write_text("state", encoding="utf-8")
        return {
            "status": "completed",
            "branch_role": mode,
            "branch_id": mode,
            "summary_path": str(summary),
            "state_path": str(state),
        }

    monkeypatch.setattr(runner, "run_dense_d3", dense)

    def compare(**kwargs):
        events.append(("compare", kwargs["mode"], kwargs["label"]))
        kwargs["output_path"].write_text(
            json.dumps({"passes": True}),
            encoding="utf-8",
        )
        return {"status": "completed", "passes": True}

    monkeypatch.setattr(runner, "compare_summaries", compare)
    return events, verify_events


def test_main_never_starts_d5_when_any_authorization_conjunct_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    events, verify_events = _patch_terminal_dependencies(
        runner,
        monkeypatch,
        tmp_path,
        d2_passes=False,
    )

    def forbidden_candidate(**_kwargs):
        pytest.fail("PEPS candidate ran after the pre-d3 gate failed")

    monkeypatch.setattr(runner, "_candidate_point", forbidden_candidate)
    output = tmp_path / "failed-gate"
    assert runner.main(["--output-directory", str(output)]) == 0
    result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert result["d5_authorized"] is False
    assert result["terminal_verdict"] == "d5_blocked_by_pretarget_gate"
    assert not any(event[:2] == ("exact", 5) for event in events)
    assert len(verify_events) >= 3


def test_main_runs_d5_only_after_gate_in_frozen_D_major_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    events, verify_events = _patch_terminal_dependencies(
        runner,
        monkeypatch,
        tmp_path,
        d2_passes=True,
    )
    point_calls: list[tuple[int, str, int, str | int]] = []

    def point(*, distance, branch_role, bond, radius, **_kwargs):
        point_calls.append((distance, branch_role, bond, radius))
        fidelity = (
            {1: 0.980, 2: 0.985, 4: 0.992, 8: 0.995}[bond]
            if distance == 3
            else 0.995
        )
        return {
            "status": "completed",
            "distance": distance,
            "branch_role": branch_role,
            "branch_id": branch_role,
            "bond_dimension": bond,
            "rdm_radius": radius,
            "fidelity": fidelity,
            "verdict": "useful_conditioned_trajectory",
        }

    monkeypatch.setattr(runner, "_candidate_point", point)
    publish_events: list[str] = []

    def publish(**_kwargs):
        publish_events.append("publish")
        return tmp_path / "result.json"

    monkeypatch.setattr(runner, "_publish_terminal_result", publish)
    output = tmp_path / "passed-gate"
    assert runner.main(["--output-directory", str(output)]) == 0
    assert ("exact", 5, "primary") in events
    assert point_calls[:8] == [
        (3, branch, bond, "complete")
        for branch in ("primary", "alternate")
        for bond in (1, 2, 4, 8)
    ]
    assert point_calls[8:] == [
        (5, "primary", bond, radius)
        for bond in (1, 2, 4)
        for radius in (0, 1, 2, 3)
    ]
    assert publish_events == ["publish"]
    assert verify_events[-1] == "verify"
