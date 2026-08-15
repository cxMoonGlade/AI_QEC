from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "run_gcapeps_finite_memory_bond32.py"
)


def _load_module():
    name = "gcapeps_finite_memory_serial_orchestrator"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _plan(module):
    rows = (
        ("cell-a", "a-dense", module.DENSE_REFERENCE),
        ("cell-a", "a-plain", module.PLAIN_EVIDENCE),
        ("cell-a", "a-gc", module.GCAPEPS_EVIDENCE),
        ("cell-a", "a-perf-plain", module.PLAIN_PERFORMANCE),
        ("cell-a", "a-perf-gc", module.GCAPEPS_PERFORMANCE),
        ("cell-a", "a-sdim", module.SDIM_COMPUTATION),
        ("cell-a", "a-compare", module.TERMINAL_COMPARATOR),
        ("cell-b", "b-dense", module.DENSE_REFERENCE),
        ("cell-b", "b-perf", module.GCAPEPS_PERFORMANCE),
        ("cell-b", "b-sdim", module.SDIM_COMPUTATION),
        ("cell-b", "b-compare", module.TERMINAL_COMPARATOR),
    )
    return tuple(
        module.SerialLaunchRequest(
            ordinal=index,
            cell_id=cell,
            launch_id=launch,
            role=role,
        )
        for index, (cell, launch, role) in enumerate(rows)
    )


def test_scientific_censor_skips_current_cell_then_runs_next_cell():
    module = _load_module()
    calls = []

    def launch(request):
        calls.append(request.launch_id)
        if request.launch_id == "a-plain":
            return "worker_censor"
        return "completed_result"

    outcomes = module.run_heldout_serial_launch_plan(_plan(module), launch)
    by_id = {row.request.launch_id: row for row in outcomes}
    assert by_id["a-plain"].terminal_kind == "worker_censor"
    for launch_id in (
        "a-gc",
        "a-perf-plain",
        "a-perf-gc",
        "a-sdim",
        "a-compare",
    ):
        assert by_id[launch_id].disposition == "SKIPPED_PREREQUISITE"
        assert by_id[launch_id].executed is False
    assert by_id["b-dense"].executed is True
    assert by_id["b-compare"].executed is True
    assert "a-gc" not in calls
    assert "b-dense" in calls


def test_performance_only_censor_keeps_later_science_running():
    module = _load_module()
    calls = []

    def launch(request):
        calls.append(request.launch_id)
        if request.launch_id == "a-perf-plain":
            return "supervisor_censor"
        return "completed_result"

    outcomes = module.run_heldout_serial_launch_plan(_plan(module), launch)
    by_id = {row.request.launch_id: row for row in outcomes}
    assert by_id["a-perf-plain"].terminal_kind == "supervisor_censor"
    assert by_id["a-perf-gc"].executed is True
    assert by_id["a-sdim"].executed is True
    assert by_id["a-compare"].executed is True
    assert by_id["b-dense"].executed is True
    assert calls == [row.request.launch_id for row in outcomes]


def test_invalid_control_stops_current_and_all_later_cells():
    module = _load_module()
    calls = []

    def launch(request):
        calls.append(request.launch_id)
        if request.launch_id == "a-perf-plain":
            return "invalid_control"
        return "completed_result"

    outcomes = module.run_heldout_serial_launch_plan(_plan(module), launch)
    by_id = {row.request.launch_id: row for row in outcomes}
    assert by_id["a-perf-plain"].terminal_kind == "invalid_control"
    for row in outcomes:
        if row.request.ordinal > by_id["a-perf-plain"].request.ordinal:
            assert row.disposition == "SKIPPED_INVALID_CONTROL"
            assert row.executed is False
    assert calls[-1] == "a-perf-plain"


def test_serial_plan_rejects_role_regression_and_launch_reuse():
    module = _load_module()
    regressed = (
        module.SerialLaunchRequest(
            ordinal=0,
            cell_id="cell-a",
            launch_id="late",
            role=module.SDIM_COMPUTATION,
        ),
        module.SerialLaunchRequest(
            ordinal=1,
            cell_id="cell-a",
            launch_id="early",
            role=module.DENSE_REFERENCE,
        ),
    )
    with pytest.raises(ValueError, match="stage order"):
        module.run_heldout_serial_launch_plan(
            regressed,
            lambda request: "completed_result",
        )
    reused = list(_plan(module))
    reused[1] = module.SerialLaunchRequest(
        ordinal=1,
        cell_id="cell-a",
        launch_id=reused[0].launch_id,
        role=module.PLAIN_EVIDENCE,
    )
    with pytest.raises(ValueError, match="reused"):
        module.run_heldout_serial_launch_plan(
            reused,
            lambda request: "completed_result",
        )
