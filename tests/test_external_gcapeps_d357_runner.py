"""Pure controls for the GCAPEPS d=3/5/7 performance supervisor."""

from __future__ import annotations

import ast
import copy
import importlib.util
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
RUNNER_PATH = (
    REPO
    / "scripts"
    / "external_baselines"
    / "run_gcapeps_d357_performance.py"
)
EMITTER_PATH = (
    REPO
    / "scripts"
    / "external_baselines"
    / "emit_gcapeps_d357_unitary_prefix_fixture.py"
)


def _runner():
    spec = importlib.util.spec_from_file_location(
        "run_gcapeps_d357_performance_under_test",
        RUNNER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _completed_runs(runner):
    rows = []
    for spec in runner.target_launch_plan():
        scale = 2 if spec["lane"] == "plain" else 1
        distance = spec["distance"]
        cell = runner.frozen_grid_cell(distance, spec["cell_id"])
        rows.append(
            {
                **spec,
                "status": "completed",
                "censor_reason": None,
                "validated": {
                    "update_ns": scale * (100 + distance),
                    "peak_rss_bytes": scale * (1000 + distance),
                    "cgroup_memory_peak_bytes": scale * (2000 + distance),
                    "maximum_bond_dimension": scale,
                    "total_tensor_elements": scale * (3000 + distance),
                    "logical_tensor_bytes": scale * 16 * (3000 + distance),
                    "persistent_state_instances": 1,
                    "prefix_batches_completed": cell["round_layers"],
                    "completed_layers": cell["round_layers"],
                    "completed_rotations": cell["expected_rotation_count"],
                    "attempted_rotations": cell["expected_rotation_count"],
                },
                "output_sha256": f"{scale}" * 64,
                "process": {
                    "returncode": 0,
                    "launch_and_process_elapsed_ns": 1,
                },
            }
        )
    return rows


def _controls_inputs(runner):
    fixtures = {
        distance: {
            "fixture_sha256": runner.EXPECTED_FIXTURE_SHA256[distance],
            "stim_sha256": str(distance) * 64,
            "fixture": {"n_qubits": 2 * distance**2 - 1},
        }
        for distance in runner.DISTANCES
    }
    sdim = {
        distance: {
            "status": "PASS",
            "output_sha256": str(distance) * 64,
            "enters_performance_ratio": False,
        }
        for distance in runner.DISTANCES
    }
    candidates = {
        lane: {
            "status": "completed",
            "distance": 3,
            "cell_id": "d3-baseline",
            "lane": lane,
            "sample_kind": "control",
            "output_sha256": ("a" if lane == "plain" else "b") * 64,
        }
        for lane in runner.LANES
    }
    return fixtures, sdim, candidates


def _synthetic_fixture(runner, distance: int = 3) -> dict:
    targets = {
        3: [6, 5, 7, 12],
        5: [22, 21, 23, 30],
        7: [44, 43, 45, 58],
    }[distance]
    locations = [
        {"location_rank": rank, "target": target, "kind": "test", "xy": [0, 0]}
        for rank, target in enumerate(targets, start=1)
    ]
    cells = []
    for frozen in runner.frozen_grid_cells():
        if frozen["distance"] != distance:
            continue
        selected = targets[: frozen["noise_complexity"]]
        operations = []
        for layer in range(1, frozen["round_layers"] + 1):
            operations.append(
                {
                    "operation_index": len(operations),
                    "layer": layer,
                    "kind": "clifford_prefix",
                }
            )
            for rank, target in enumerate(selected, start=1):
                operations.append(
                    {
                        "operation_index": len(operations),
                        "layer": layer,
                        "kind": "physical_ry",
                        "location_rank": rank,
                        "target": target,
                    }
                )
        cells.append(
            {
                "cell_id": frozen["cell_id"],
                "role": frozen["role"],
                "round_layers": frozen["round_layers"],
                "noise_complexity": frozen["noise_complexity"],
                "p_twirl": frozen["p_twirl"],
                "p_twirl_float64_hex": frozen["p_twirl_float64_hex"],
                "theta_radians": frozen["theta_radians"],
                "theta_float64_hex": frozen["theta_float64_hex"],
                "selected_targets": selected,
                "prefix_application_count": frozen["round_layers"],
                "rotation_count": frozen["expected_rotation_count"],
                "operation_ledger": operations,
            }
        )
    return {
        "schema": "error_coupling_simulator.external_gcapeps_d357_unitary_prefix.fixture.v2",
        "fixture_id": f"synthetic-d{distance}-v2",
        "distance": distance,
        "n_qubits": 2 * distance**2 - 1,
        "prefix": {"gate_count": 2, "gate_stream_sha256": "f" * 64},
        "graph": {"edge_count": 1, "edge_stream_sha256": "e" * 64},
        "grid_cells": cells,
        "grid_cells_sha256": "d" * 64,
        "error_locations": locations,
        "accumulated_frame_schedule": {"schedule_sha256": "c" * 64},
        "gcapeps_multi_resource_limits": {
            "max_local_operator_elements": 64,
            "max_total_operator_elements": 64 * (2 * distance**2 - 1),
            "max_local_candidate_tensor_elements": 4_194_304,
            "max_total_candidate_tensor_elements": 16_777_216,
            "max_predicted_bond_dimension": 64,
            "max_routed_rank_product": 64,
            "max_total_bond_growth_product": 64,
            "expected_refactor_factor_product": 1,
        },
        "peps_settings": {
            "cutoff": 1e-12,
            "renorm": False,
            "gauge_smudge": 0.0,
            "equilibrate_every": None,
            "max_bond": None,
            "to_backend": None,
            "convert_eager": True,
        },
    }


def _candidate_report(runner, *, lane: str, fixture: dict, fork: Path):
    cell = next(row for row in fixture["grid_cells"] if row["role"] == "baseline")
    if lane == "plain":
        schema = runner.PLAIN_WORKER_SCHEMA
        lane_name = "plain_quimb_persistent_physical_layers_plus_local_ry"
        timing = {
            "physical_prefix_apply_ns": 11,
            "physical_local_ry_apply_ns": 7,
            "update_ns": 18,
            "worker_total_ns": 30,
        }
    else:
        schema = runner.GCAPEPS_WORKER_SCHEMA
        lane_name = "gcapeps_persistent_live_frame_plus_rank2_tree_residual"
        timing = {
            "tableau_prefix_apply_ns": 5,
            "certified_tree_rotation_apply_ns": 13,
            "update_ns": 18,
            "worker_total_ns": 30,
        }
    timing["operation_rows"] = [
        {
            "operation_index": row["operation_index"],
            "layer": row["layer"],
            "kind": row["kind"],
            "target": row.get("target"),
            "location_rank": row.get("location_rank"),
            "elapsed_ns": 1,
            "status": "completed",
        }
        for row in cell["operation_ledger"]
    ]
    fixture_row = {
        "schema": fixture["schema"],
        "fixture_id": fixture["fixture_id"],
        "canonical_sha256": runner.EXPECTED_FIXTURE_SHA256[3],
        "distance": 3,
        "n_qubits": 17,
        "dtype": "complex128",
        "prefix_gate_count": fixture["prefix"]["gate_count"],
        "prefix_stream_sha256": fixture["prefix"]["gate_stream_sha256"],
        "graph_edge_count": fixture["graph"]["edge_count"],
        "graph_edge_stream_sha256": fixture["graph"]["edge_stream_sha256"],
        "grid_cells_sha256": fixture["grid_cells_sha256"],
        "cell_id": cell["cell_id"],
        "role": cell["role"],
        "round_layers": cell["round_layers"],
        "noise_complexity": cell["noise_complexity"],
        "p_twirl": cell["p_twirl"],
        "p_twirl_float64_hex": cell["p_twirl_float64_hex"],
        "theta_radians": cell["theta_radians"],
        "theta_float64_hex": cell["theta_float64_hex"],
        "selected_targets": cell["selected_targets"],
        "expected_rotation_count": cell["rotation_count"],
    }
    if lane == "gcapeps":
        fixture_row["accumulated_frame_schedule_sha256"] = fixture[
            "accumulated_frame_schedule"
        ]["schedule_sha256"]
    final = {
        "tensor_count": 17,
        "maximum_bond_dimension": 2,
        "total_tensor_elements": 72,
        "logical_tensor_bytes": 1152,
        "dtype": "complex128",
    }
    report = {
        "schema": schema,
        "status": "completed",
        "lane": lane_name,
        "fixture": fixture_row,
        "numerical_settings": {"dtype": "complex128", **fixture["peps_settings"]},
        "rotation": {
            "physical_pauli": "Y",
            "selected_targets": cell["selected_targets"],
            "theta_radians": cell["theta_radians"],
            "theta_float64_hex": cell["theta_float64_hex"],
            "p_twirl": cell["p_twirl"],
            "active_rank_per_rotation": 2,
        },
        "progress": {
            "persistent_state_instances": 1,
            "prefix_batches_completed": 1,
            "completed_layers": 1,
            "completed_rotations": 1,
            "attempted_rotations": 1,
            "expected_layers": 1,
            "expected_rotations": 1,
        },
        "timing_ns": timing,
        "resource_usage": {
            "peak_rss_bytes": 10_000,
            "cgroup_memory_peak": {
                "status": "available",
                "bytes": 20_000,
                "source": "/sys/fs/cgroup/test/memory.peak",
            },
        },
        "process_envelope": {
            "cpu_affinity": [2],
            "python_no_user_site": True,
            "python_dont_write_bytecode": True,
            "pythonpath_absent": True,
        },
        "fork": {
            "path": str(fork.resolve()),
            "commit": runner.EXPECTED_FORK_COMMIT,
            "tree": runner.EXPECTED_FORK_TREE,
            "clean_including_ignored": True,
        },
        "representation": {"initial": {}, "after_prefix": {}, "final": final},
        "candidate_semantics": {
            "is_truth": False,
            "complete_state_contraction_performed": False,
            "norm_computed": False,
            "fidelity_computed": False,
            "measurement_reset_or_record_computed": False,
            "round_layers_are_complete_qec_rounds": False,
            "p_twirl_is_sampled_frequency": False,
        },
    }
    if lane == "gcapeps":
        report["representation"]["final_or_partial"] = final
        report["construction"] = {
            "updates": [{}],
            "successful_update_count": 1,
            "partial_ledger_complete_through_last_success": True,
            "multi_resource_limits": {
                key: value
                for key, value in fixture["gcapeps_multi_resource_limits"].items()
                if key != "expected_refactor_factor_product"
            },
            "expected_refactor_factor_product": 1,
        }
        report["censor"] = None
    return report


def _resource_censor_report(runner, *, fixture: dict, fork: Path) -> dict:
    report = _candidate_report(
        runner, lane="gcapeps", fixture=fixture, fork=fork
    )
    cell = next(row for row in fixture["grid_cells"] if row["role"] == "baseline")
    partial = report["representation"]["final"]
    report["status"] = "resource_guard_censored"
    report["progress"].update(
        {
            "prefix_batches_completed": 1,
            "completed_layers": 0,
            "completed_rotations": 0,
            "attempted_rotations": 1,
        }
    )
    report["timing_ns"] = {
        "tableau_prefix_apply_ns": 5,
        "certified_tree_rotation_apply_ns": 7,
        "update_ns": 12,
        "worker_total_ns": 20,
        "operation_rows": [
            {
                "operation_index": 0,
                "layer": 1,
                "kind": "clifford_prefix",
                "target": None,
                "location_rank": None,
                "elapsed_ns": 5,
                "status": "completed",
            },
            {
                "operation_index": 1,
                "layer": 1,
                "kind": "physical_ry",
                "target": cell["selected_targets"][0],
                "location_rank": 1,
                "elapsed_ns": 7,
                "status": "resource_guard_censored",
            },
        ],
    }
    report["representation"]["final"] = None
    report["representation"]["final_or_partial"] = partial
    report["construction"]["updates"] = []
    report["construction"]["successful_update_count"] = 0
    report["censor"] = {
        "classification": "RESOURCE_GUARD_CENSORED",
        "error_type": "PEPOResourceError",
        "stage": "candidate_tensor",
        "metric": "max_predicted_bond_dimension",
        "predicted": 65,
        "limit": 64,
        "message": "synthetic preregistered guard hit",
        "failed_operation_index": 1,
        "failed_layer": 1,
        "failed_location_rank": 1,
        "failed_target": cell["selected_targets"][0],
        "failed_routing_event_not_committed": True,
        "carrier_update_contract": "candidate_then_commit",
    }
    return report


def test_launch_plan_is_exact_for_all_24_cells() -> None:
    runner = _runner()
    cells = runner.frozen_grid_cells()
    plan = runner.target_launch_plan()

    assert len(cells) == 24
    assert len({row["cell_id"] for row in cells}) == 24
    assert len(plan) == 192
    assert {row["distance"] for row in plan} == {3, 5, 7}
    for cell in cells:
        rows = [row for row in plan if row["cell_id"] == cell["cell_id"]]
        assert len(rows) == 8
        assert [row["lane"] for row in rows[:2]] == ["plain", "gcapeps"]
        assert [row["sample_kind"] for row in rows[:2]] == ["warmup", "warmup"]
        measured = rows[2:]
        assert [row["lane"] for row in measured] == [
            "plain", "gcapeps", "gcapeps", "plain", "plain", "gcapeps"
        ]
        for lane in runner.LANES:
            assert [
                row["sample_index"] for row in measured if row["lane"] == lane
            ] == [0, 1, 2]
    assert [row["role"] for row in cells[:8]] == [
        "baseline",
        "depth-2",
        "depth-d",
        "complexity-2",
        "complexity-4",
        "low-probability",
        "high-probability",
        "stress-corner",
    ]


def test_population_attempts_later_distances_after_censoring() -> None:
    runner = _runner()
    calls = []

    def launch(**spec):
        calls.append(dict(spec))
        if spec["distance"] == 3 and spec["lane"] == "plain":
            raise RuntimeError("synthetic timeout")
        return {
            "status": "completed",
            "censor_reason": None,
            "validated": {
                **{field: 1 for field in runner.METRIC_FIELDS},
                "persistent_state_instances": 1,
                "prefix_batches_completed": 1,
                "completed_layers": 1,
                "completed_rotations": 1,
                "attempted_rotations": 1,
            },
            "process": {"returncode": 0},
            "output_sha256": "a" * 64,
        }

    rows = runner.execute_target_population(launch)
    assert calls == runner.target_launch_plan()
    assert len(rows) == 192
    assert any(row["status"] == "censored" for row in rows)
    assert {row["cell_id"] for row in rows} == {
        cell["cell_id"] for cell in runner.frozen_grid_cells()
    }
    summary = runner.summarize_cell(
        distance=3,
        cell_id="d3-baseline",
        runs=rows,
        controls_passed=True,
    )
    assert summary["joint_ratio_eligible"] is False
    assert len(summary["raw_launch_rows"]) == 8
    assert any(
        row["process_returncode"] is None
        for row in summary["raw_launch_rows"]
        if row["status"] == "censored"
    )


def test_cell_summary_emits_standard_metrics_and_directional_ratios() -> None:
    runner = _runner()
    summary = runner.summarize_cell(
        distance=5,
        cell_id="d5-baseline",
        runs=_completed_runs(runner),
        controls_passed=True,
    )

    assert summary["joint_ratio_eligible"] is True
    assert set(summary["metrics"]) == set(runner.METRIC_FIELDS)
    for metric in summary["metrics"].values():
        assert metric["ratio_plain_over_gcapeps"] == 2.0
        assert len(metric["plain"]["raw"]) == 3
        assert len(metric["gcapeps"]["raw"]) == 3
    assert summary["no_interaction_or_asymptotic_fit_performed"] is True


def test_any_censored_row_suppresses_only_that_cell_ratio() -> None:
    runner = _runner()
    rows = _completed_runs(runner)
    row = next(
        item
        for item in rows
        if item["cell_id"] == "d7-stress-corner"
        and item["lane"] == "gcapeps"
        and item["sample_kind"] == "measured"
        and item["sample_index"] == 2
    )
    row["status"] = "censored"
    row["censor_reason"] = "memory_limit_or_oom"
    row.pop("validated")

    stress = runner.summarize_cell(
        distance=7,
        cell_id="d7-stress-corner",
        runs=rows,
        controls_passed=True,
    )
    baseline = runner.summarize_cell(
        distance=7,
        cell_id="d7-baseline",
        runs=rows,
        controls_passed=True,
    )
    assert stress["joint_ratio_eligible"] is False
    assert stress["metrics"] is None
    assert stress["lane_status"]["gcapeps"]["status"] == "censored"
    assert baseline["joint_ratio_eligible"] is True
    assert baseline["metrics"] is not None


def test_median_mad_rejects_wrong_count_nonpositive_and_bool() -> None:
    runner = _runner()
    assert runner.median_and_mad(
        [1, 2, 3]
    ) == {
        "raw": [1, 2, 3],
        "median": 2.0,
        "mad": 1.0,
    }
    for values in ([1] * 2, [1, 1, 0], [1, 1, True]):
        with pytest.raises(ValueError):
            runner.median_and_mad(values)


def test_controls_report_has_no_target_and_binds_all_sources() -> None:
    runner = _runner()
    fixtures, sdim, candidates = _controls_inputs(runner)
    report = runner.build_controls_report(
        fixtures=fixtures,
        sdim_runs=sdim,
        candidate_controls=candidates,
        parent_identity={"commit": "1" * 40},
        fork_identity={"commit": runner.EXPECTED_FORK_COMMIT},
        environment_identity={"environment": "testpymid"},
        systemd_identity={"passed": True},
    )
    runner.validate_controls_report(report)

    assert report["execution_scope"]["target_worker_count"] == 0
    assert report["target_execution_authorized_by_this_report_alone"] is False
    assert set(report["sdim_controls"]) == {"d3", "d5", "d7"}
    assert set(report["source_sha256"]) == {
        path.resolve().relative_to(REPO).as_posix()
        for path in runner.CLAIM_BEARING_PATHS
    }

    corrupted = copy.deepcopy(report)
    corrupted["execution_scope"]["target_worker_count"] = 1
    corrupted["content_sha256"] = runner._canonical_sha256(
        {key: value for key, value in corrupted.items() if key != "content_sha256"}
    )
    with pytest.raises(ValueError, match="headline/scope"):
        runner.validate_controls_report(corrupted)


@pytest.mark.parametrize("lane", ["plain", "gcapeps"])
def test_candidate_report_validation_extracts_only_registered_metrics(
    tmp_path: Path,
    lane: str,
) -> None:
    runner = _runner()
    fork = tmp_path / "fork"
    fork.mkdir()
    fixture = _synthetic_fixture(runner)
    report = _candidate_report(
        runner,
        lane=lane,
        fixture=fixture,
        fork=fork,
    )
    metrics = runner.validate_candidate_report(
        report,
        lane=lane,
        cell_id="d3-baseline",
        fixture=fixture,
        fixture_sha256=runner.EXPECTED_FIXTURE_SHA256[3],
        cpu_id=2,
        fork_checkout=fork,
    )
    assert set(runner.METRIC_FIELDS).issubset(metrics)
    assert metrics["persistent_state_instances"] == 1
    assert metrics["completed_rotations"] == 1

    truth = copy.deepcopy(report)
    truth["candidate_semantics"]["is_truth"] = True
    with pytest.raises(ValueError, match="scope widened"):
        runner.validate_candidate_report(
            truth,
            lane=lane,
            cell_id="d3-baseline",
            fixture=fixture,
            fixture_sha256=runner.EXPECTED_FIXTURE_SHA256[3],
            cpu_id=2,
            fork_checkout=fork,
        )

    vector = copy.deepcopy(report)
    vector["state_vector"] = [1.0]
    with pytest.raises(ValueError, match="forbidden truth payload"):
        runner.validate_candidate_report(
            vector,
            lane=lane,
            cell_id="d3-baseline",
            fixture=fixture,
            fixture_sha256=runner.EXPECTED_FIXTURE_SHA256[3],
            cpu_id=2,
            fork_checkout=fork,
        )


def test_completed_report_rejects_cell_progress_site_and_semantic_mutations(
    tmp_path: Path,
) -> None:
    runner = _runner()
    fork = tmp_path / "fork"
    fork.mkdir()
    fixture = _synthetic_fixture(runner)
    report = _candidate_report(
        runner, lane="gcapeps", fixture=fixture, fork=fork
    )

    mutations = []
    wrong_probability = copy.deepcopy(report)
    wrong_probability["fixture"]["p_twirl"] = 1e-2
    mutations.append((wrong_probability, "cell identity"))
    wrong_progress = copy.deepcopy(report)
    wrong_progress["progress"]["persistent_state_instances"] = 2
    mutations.append((wrong_progress, "persistent-state progress"))
    wrong_target = copy.deepcopy(report)
    wrong_target["timing_ns"]["operation_rows"][1]["target"] = 5
    mutations.append((wrong_target, "operation timing ledger"))
    wrong_dtype = copy.deepcopy(report)
    wrong_dtype["numerical_settings"]["dtype"] = "complex64"
    mutations.append((wrong_dtype, "numerical settings"))
    wrong_probability_semantics = copy.deepcopy(report)
    wrong_probability_semantics["candidate_semantics"][
        "p_twirl_is_sampled_frequency"
    ] = True
    mutations.append((wrong_probability_semantics, "scope widened"))

    for mutated, message in mutations:
        with pytest.raises(ValueError, match=message):
            runner.validate_candidate_report(
                mutated,
                lane="gcapeps",
                cell_id="d3-baseline",
                fixture=fixture,
                fixture_sha256=runner.EXPECTED_FIXTURE_SHA256[3],
                cpu_id=2,
                fork_checkout=fork,
            )


def test_structured_resource_guard_censor_is_validated_and_mutations_fail(
    tmp_path: Path,
) -> None:
    runner = _runner()
    fork = tmp_path / "fork"
    fork.mkdir()
    fixture = _synthetic_fixture(runner)
    report = _resource_censor_report(runner, fixture=fixture, fork=fork)

    evidence = runner.validate_candidate_censor_report(
        report,
        lane="gcapeps",
        cell_id="d3-baseline",
        fixture=fixture,
        fixture_sha256=runner.EXPECTED_FIXTURE_SHA256[3],
        cpu_id=2,
        fork_checkout=fork,
    )
    assert evidence["classification"] == "RESOURCE_GUARD_CENSORED"
    assert evidence["progress"]["persistent_state_instances"] == 1
    assert evidence["progress"]["attempted_rotations"] == 1

    wrong_target = copy.deepcopy(report)
    wrong_target["censor"]["failed_target"] = 5
    with pytest.raises(ValueError, match="failed-operation binding"):
        runner.validate_candidate_censor_report(
            wrong_target,
            lane="gcapeps",
            cell_id="d3-baseline",
            fixture=fixture,
            fixture_sha256=runner.EXPECTED_FIXTURE_SHA256[3],
            cpu_id=2,
            fork_checkout=fork,
        )

    wrong_round_semantics = copy.deepcopy(report)
    wrong_round_semantics["candidate_semantics"][
        "round_layers_are_complete_qec_rounds"
    ] = True
    with pytest.raises(ValueError, match="runtime/scope"):
        runner.validate_candidate_censor_report(
            wrong_round_semantics,
            lane="gcapeps",
            cell_id="d3-baseline",
            fixture=fixture,
            fixture_sha256=runner.EXPECTED_FIXTURE_SHA256[3],
            cpu_id=2,
            fork_checkout=fork,
        )


def test_worker_commands_use_only_neutral_fixture_fork_and_private_output(
    tmp_path: Path,
) -> None:
    runner = _runner()
    python = tmp_path / "python"
    fixture = tmp_path / "fixture.json"
    fork = tmp_path / "fork"
    output = tmp_path / "out.json"

    plain = runner.candidate_worker_command(
        lane="plain",
        python_executable=python,
        fixture_path=fixture,
        cell_id="d3-baseline",
        fork_checkout=fork,
        output_json=output,
    )
    assert plain[-8:] == [
        "--fixture",
        str(fixture),
        "--cell-id",
        "d3-baseline",
        "--fork-checkout",
        str(fork),
        "--output",
        str(output),
    ]
    assert "gcapeps_d357_worker.py" not in plain[3]
    gc = runner.candidate_worker_command(
        lane="gcapeps",
        python_executable=python,
        fixture_path=fixture,
        cell_id="d3-baseline",
        fork_checkout=fork,
        output_json=output,
    )
    assert gc[-8:] == plain[-8:]
    assert gc[3].endswith("gcapeps_d357_worker.py")
    sdim = runner.sdim_worker_command(
        sdim_python=python,
        fixture_path=fixture,
        output_json=output,
    )
    assert sdim[-4:] == ["--fixture", str(fixture), "--output", str(output)]


def test_fixture_bytes_are_checked_with_emitter_owned_encoding(
    tmp_path: Path,
) -> None:
    runner = _runner()
    spec = importlib.util.spec_from_file_location(
        "gcapeps_d357_emitter_encoding_under_test", EMITTER_PATH
    )
    assert spec is not None and spec.loader is not None
    emitter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(emitter)
    payload = {"schema": "synthetic", "nested": {"value": 1}}
    raw = emitter.canonical_json_bytes(payload)
    path = tmp_path / "fixture.json"
    path.write_bytes(raw)

    assert raw != runner.canonical_json_bytes(payload)
    loaded = runner.load_strict_json(path, canonical=False)
    assert raw == emitter.canonical_json_bytes(loaded)
    with pytest.raises(ValueError, match="not canonical"):
        runner.load_strict_json(path, canonical=True)
    source = RUNNER_PATH.read_text(encoding="utf-8")
    assert "output_json.read_bytes() != emitter.canonical_json_bytes(payload)" in source


def test_runner_has_no_direct_candidate_import_and_target_is_cli_explicit() -> None:
    runner = _runner()
    tree = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not any(name.startswith("quimb") for name in imported)
    assert not any(name.startswith("stim") for name in imported)
    source = RUNNER_PATH.read_text(encoding="utf-8")
    assert source.count("parent_after = verify_committed_parent_checkout()") == 2
    assert "parent or claim-bearing source changed during controls" in source
    assert "parent or claim-bearing source changed during target" in source
    assert runner._parse_args(
        ["controls-only", "--destination", "/tmp/control-bundle"]
    ).command == "controls-only"
    assert runner._parse_args(
        [
            "target",
            "--destination",
            "/tmp/target-bundle",
            "--controls-bundle",
            "/tmp/control-bundle",
        ]
    ).command == "target"


def test_shared_atomic_bundle_publisher_is_reused(tmp_path: Path) -> None:
    runner = _runner()
    foundation = runner.load_foundation()
    destination = tmp_path / "bundle"
    with foundation.preflight_publication(destination) as preflight:
        confirmation = foundation.publish_bundle_noreplace(
            preflight,
            artifacts={"result.json": runner.canonical_json_bytes({"ok": True})},
            manifest_payload={"schema": runner.RESULT_SCHEMA, "status": "test"},
        )
    manifest, artifacts = foundation.load_published_bundle(destination)
    assert confirmation["rename_noreplace_success"] is True
    assert manifest["schema"] == runner.RESULT_SCHEMA
    assert artifacts == {
        "result.json": runner.canonical_json_bytes({"ok": True})
    }
    with pytest.raises(FileExistsError):
        foundation.preflight_publication(destination)
