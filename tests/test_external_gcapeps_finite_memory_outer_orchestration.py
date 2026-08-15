from __future__ import annotations

import ast
import copy
import hashlib
import json
import importlib.util
import itertools
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATION = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "gcapeps_finite_memory_orchestration.py"
)
EMITTER = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "emit_gcapeps_finite_memory_fixture.py"
)
SUPERVISOR = (
    ROOT
    / "scripts"
    / "external_baselines"
    / "run_gcapeps_finite_memory_bond32.py"
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _module():
    return _load(
        ORCHESTRATION,
        "gcapeps_finite_memory_outer_orchestration_test_module",
    )


def _emitter():
    return _load(EMITTER, "gcapeps_finite_memory_fixture_for_outer_tests")

def _supervisor():
    return _load(
        SUPERVISOR,
        "gcapeps_finite_memory_supervisor_for_outer_tests",
    )



def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _observation(module, spec, *, qualifier=None, terminal="completed_result"):
    return module.NodeObservation(
        terminal_kind=terminal,
        qualifier=qualifier,
        envelope_complete_file_sha256=_digest(spec.launch_id + "-envelope"),
        launch_receipt_complete_file_sha256=_digest(spec.launch_id + "-receipt"),
    )


def _clock(start=10_000, step=100):
    values = itertools.count(start, step)
    return lambda: next(values)


def _supporting_identities(module):
    documents = {
        name: {
            "path": f"docs/{name}.md",
            "complete_file_sha256": _digest(name),
        }
        for name in (
            "literature_closure",
            "preregistration",
            "metrics",
            "numerical_provenance",
            "partial_swap_sign_audit",
            "partial_swap_sign_independent_review",
            "independent_preregistration_rereview",
            "theory_erratum_rereview",
        )
    }
    return {
        "source_documents": documents,
        "theory_checkpoint": {"commit": "1" * 40, "tree": "2" * 40},
        "theory_erratum_checkpoint": {
            "commit": "a" * 40,
            "tree": "b" * 40,
        },
        "implementations": {
            "parent": {"commit": "3" * 40, "tree": "4" * 40},
            "fork": {"commit": "5" * 40, "tree": "6" * 40},
        },
        "environment": {
            "main_lock": {
                "path": "uv.lock",
                "complete_file_sha256": _digest("main-lock"),
            },
            "fork_lock": {
                "path": "external/forks/quimb-gcapeps/pixi.lock",
                "complete_file_sha256": _digest("fork-lock"),
            },
        },
        "sdim": {
            "bootstrap": {
                "path": "environment-gcapeps-sdim.yml",
                "complete_file_sha256": _digest("sdim-bootstrap"),
            },
            "runtime_inventory_schema": (
                module.SCHEMA_PREFIX + "sdim_inventory.v1"
            ),
            "state_sha256": _digest("sdim-state"),
            "projection_sha256": _digest("sdim-projection"),
            "envelope_complete_file_sha256": _digest("sdim-envelope"),
            "launch_receipt_complete_file_sha256": _digest("sdim-receipt"),
        },
        "manager_preflight": {
            "path": "outputs/manager_preflight_receipt.json",
            "schema": module.SCHEMA_PREFIX + "manager_preflight_receipt.v1",
            "result_projection_sha256": _digest("manager-projection"),
            "byte_length": 1234,
            "complete_file_sha256": _digest("manager-file"),
            "security_projection": {
                "selected_scope": "system",
                "systemd_major": 255,
                "cgroup_version": 2,
                "runner_dumpable": 0,
            },
        },
        "result_schemas": {
            "fixture": module.SCHEMA_PREFIX + "fixture.v1",
            "dense": module.SCHEMA_PREFIX + "dense_reference.v1",
            "plain_evidence": module.SCHEMA_PREFIX
            + "plain_evidence_worker.v1",
            "gc_evidence": module.SCHEMA_PREFIX
            + "gcapeps_evidence_worker.v1",
            "sdim": module.SCHEMA_PREFIX + "sdim_frame_control.v1",
            "comparator": module.SCHEMA_PREFIX + "comparator_worker.v1",
        },
        "mask_contract": {
            "namespace_version": "gcapeps-finite-memory-mask-v1",
            "carrier_mask_index": 0,
            "blpensemble_mask_indices": list(range(32)),
            "probability_denominator": 4,
            "structural_endpoints": True,
            "nested_probability_sweep": True,
        },
    }


def _selected_search(module):
    calls = []

    def launch(spec):
        calls.append(spec)
        parameters = spec.parameter_map()
        seed = parameters.get("seed")
        if spec.role == module.DENSE_REFERENCE:
            return _observation(module, spec, qualifier=seed in {0, 1})
        if spec.role in {
            module.PLAIN_CAP_PROBE,
            module.GCAPEPS_CAP_PROBE,
            module.PLAIN_EVIDENCE,
            module.GCAPEPS_EVIDENCE,
            module.TERMINAL_COMPARATOR,
        }:
            return _observation(module, spec, qualifier=True)
        return _observation(module, spec)

    result = module.run_calibration_search(launch, clock_ns=_clock())
    return result, calls


def _calibration_artifacts(module):
    search, _ = _selected_search(module)
    identities = _supporting_identities(module)
    report = module.build_calibration_report(
        search,
        identity_bindings=identities,
    )
    report_raw = module.canonical_json_bytes(report)
    gates = {
        "temporary_file_fsync": True,
        "rename_noreplace": True,
        "parent_directory_fsync": True,
        "destination_reopen_nofollow": True,
        "destination_identity_match": True,
        "exact_byte_reread": True,
    }
    receipt = module.build_calibration_publication_receipt(
        report_path="outputs/calibration_report.json",
        report=report,
        report_byte_length=len(report_raw),
        report_complete_file_sha256=hashlib.sha256(report_raw).hexdigest(),
        publication_start_offset_ns=1_000,
        publication_committed_offset_ns=2_000,
        publication_gates=gates,
    )
    return identities, report, receipt


def _amendment(module, *, rounds_star=4, gamma_index=0):
    identities, report, receipt = _calibration_artifacts(module)
    assert report["selection"]["rounds_star"] == rounds_star
    assert report["selection"]["gamma_index"] == gamma_index
    materialization = _emitter().materialize_heldout_fixtures(
        rounds_star=rounds_star,
        gamma_index=gamma_index,
    )
    report_raw = module.canonical_json_bytes(report)
    receipt_raw = module.canonical_json_bytes(receipt)
    amendment = module.build_target_amendment(
        calibration_report=report,
        calibration_publication_receipt=receipt,
        calibration_report_path="outputs/calibration_report.json",
        calibration_report_complete_file_sha256=hashlib.sha256(
            report_raw
        ).hexdigest(),
        calibration_publication_receipt_path=(
            "outputs/calibration_publication_receipt.json"
        ),
        calibration_publication_receipt_complete_file_sha256=hashlib.sha256(
            receipt_raw
        ).hexdigest(),
        heldout_materialization=materialization,
        supporting_identities=identities,
    )
    return amendment


def _checkpoint(module, amendment):
    return module.AmendmentCheckpoint(
        commit="7" * 40,
        tree="8" * 40,
        amendment_file_sha256=hashlib.sha256(
            module.canonical_json_bytes(amendment)
        ).hexdigest(),
    )


def test_outer_orchestration_has_a_stdlib_only_import_firewall():
    tree = ast.parse(ORCHESTRATION.read_text(encoding="utf-8"))
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.partition(".")[0])
    assert imported_roots == {
        "__future__", "dataclasses", "hashlib", "json", "math", "statistics", "typing"
    }
    assert imported_roots.isdisjoint(
        {"quimb", "stim", "sdim", "numpy", "error_coupling_simulator"}
    )


def test_supporting_identities_require_the_complete_theory_erratum_chain():
    module = _module()
    identities = _supporting_identities(module)
    module.validate_supporting_identities(identities)

    missing_review = copy.deepcopy(identities)
    del missing_review["source_documents"]["theory_erratum_rereview"]
    with pytest.raises(ValueError, match="source_documents keys differ"):
        module.validate_supporting_identities(missing_review)

    missing_checkpoint = copy.deepcopy(identities)
    del missing_checkpoint["theory_erratum_checkpoint"]
    with pytest.raises(ValueError, match="supporting identities keys differ"):
        module.validate_supporting_identities(missing_checkpoint)

    malformed_checkpoint = copy.deepcopy(identities)
    malformed_checkpoint["theory_erratum_checkpoint"]["tree"] = "b" * 39
    with pytest.raises(ValueError, match="full Git identity"):
        module.validate_supporting_identities(malformed_checkpoint)

    malformed_review = copy.deepcopy(identities)
    malformed_review["source_documents"]["theory_erratum_rereview"][
        "complete_file_sha256"
    ] = "c" * 63
    with pytest.raises(ValueError, match="must be a lower-case SHA-256"):
        module.validate_supporting_identities(malformed_review)


def test_calibration_grid_and_selected_search_are_display_order_and_staged():
    module = _module()
    pairs = module.build_calibration_pairs()
    assert len(pairs) == 20
    assert [
        (row.gamma_index, row.rounds_index) for row in pairs[:6]
    ] == [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0)]
    assert [row.gamma_float64_hex for row in pairs[::5]] == [
        "0x1.247426bd47de3p-2",
        "0x1.657184ae74487p-2",
        "0x1.cb91f3bbba140p-2",
        "0x1.41b2f769cf0e0p-1",
    ]

    result, calls = _selected_search(module)
    assert result.prepublication_disposition == module.CALIBRATION_PASS
    assert result.selection is not None
    assert result.selection.pair == pairs[0]
    assert result.selection.qualifying_seeds == (0, 1)
    assert result.probe_attempt_count == 8
    assert len(result.stage_seed_audit) == 20 * 4 * 4
    selected_later_seeds = [
        row
        for row in result.stage_seed_audit
        if row.pair_id == "g00-r00" and row.stage == "D" and row.seed in {2, 3}
    ]
    assert {row.disposition for row in selected_later_seeds} == {
        "FORBIDDEN_AFTER_SECOND_STAGE_D_PASS"
    }
    later_pairs = [
        row for row in result.stage_seed_audit if row.pair_id != "g00-r00"
    ]
    assert later_pairs
    assert {row.disposition for row in later_pairs} == {
        "FORBIDDEN_AFTER_SELECTION"
    }
    probe_rows = [
        row for row in result.launch_audit if row.spec.consumes_probe_attempt
    ]
    assert [row.probe_attempt_before for row in probe_rows] == list(range(8))
    assert [row.probe_attempt_after for row in probe_rows] == list(range(1, 9))
    assert all(
        row.prelaunch_wall_offset_ns is not None
        and row.terminal_wall_offset_ns is not None
        and row.prelaunch_wall_offset_ns <= row.terminal_wall_offset_ns
        for row in result.launch_audit
    )
    phases = [row.phase for row in calls]
    last_a = max(index for index, phase in enumerate(phases) if phase in {"A", "A_FIXTURE"})
    first_b = min(index for index, phase in enumerate(phases) if phase == "B")
    last_b = max(index for index, phase in enumerate(phases) if phase == "B")
    first_c = min(index for index, phase in enumerate(phases) if phase == "C")
    last_c = max(index for index, phase in enumerate(phases) if phase == "C")
    first_d = min(index for index, phase in enumerate(phases) if phase == "D")
    assert last_a < first_b <= last_b < first_c <= last_c < first_d
    assert all(row.spec.ordinal == index for index, row in enumerate(result.launch_audit))


def test_calibration_probe_input_two_is_not_short_circuited_and_attempt_100_is_legal():
    module = _module()
    calls = []

    def launch(spec):
        calls.append(spec)
        if spec.role == module.DENSE_REFERENCE:
            return _observation(
                module,
                spec,
                qualifier=spec.parameter_map()["seed"] == 0,
            )
        if spec.role == module.PLAIN_CAP_PROBE:
            return _observation(
                module,
                spec,
                qualifier=spec.parameter_map()["input_id"] == 2,
            )
        if spec.role in {
            module.GCAPEPS_CAP_PROBE,
            module.PLAIN_EVIDENCE,
            module.GCAPEPS_EVIDENCE,
            module.TERMINAL_COMPARATOR,
        }:
            return _observation(module, spec, qualifier=True)
        return _observation(module, spec)

    result = module.run_calibration_search(launch, clock_ns=_clock())
    first_pair_plain = [
        spec
        for spec in calls
        if spec.phase == "B"
        and spec.parameter_map()["gamma_index"] == 0
        and spec.parameter_map()["rounds_index"] == 0
    ]
    assert [row.parameter_map()["input_id"] for row in first_pair_plain] == [1, 2]
    assert module.next_probe_attempt(99) == 100
    with pytest.raises(RuntimeError, match="101"):
        module.next_probe_attempt(100)
    assert result.probe_attempt_count <= 100


def test_calibration_deadline_and_late_publication_have_distinct_classes():
    module = _module()
    times = iter((5, 5 + module.CALIBRATION_WALL_NS))
    result = module.run_calibration_search(
        lambda spec: pytest.fail("deadline must stop before launch"),
        clock_ns=lambda: next(times),
    )
    assert result.prepublication_disposition == module.CALIBRATION_INCOMPLETE
    assert result.launch_audit[0].disposition == "SKIPPED_DEADLINE_CENSOR"

    late_times = iter((0, 1, module.CALIBRATION_WALL_NS + 1))
    late_child = module.run_calibration_search(
        lambda spec: _observation(module, spec),
        clock_ns=lambda: next(late_times),
    )
    assert late_child.prepublication_disposition == module.CALIBRATION_INVALID
    assert late_child.launch_audit[0].terminal_kind == "completed_result"

    identities, report, _ = _calibration_artifacts(module)
    del identities
    raw = module.canonical_json_bytes(report)
    receipt = module.build_calibration_publication_receipt(
        report_path="outputs/calibration_report.json",
        report=report,
        report_byte_length=len(raw),
        report_complete_file_sha256=hashlib.sha256(raw).hexdigest(),
        publication_start_offset_ns=module.CALIBRATION_WALL_NS - 1,
        publication_committed_offset_ns=module.CALIBRATION_WALL_NS + 1,
        publication_gates={
            "temporary_file_fsync": True,
            "rename_noreplace": True,
            "parent_directory_fsync": True,
            "destination_reopen_nofollow": True,
            "destination_identity_match": True,
            "exact_byte_reread": True,
        },
    )
    assert receipt["committed_by_deadline"] is False
    assert receipt["final_calibration_class"] == module.CALIBRATION_INVALID


def test_amendment_binds_exact_materialization_and_forbids_self_commit():
    module = _module()
    amendment = _amendment(module)
    module.validate_target_amendment(amendment)
    assert amendment["selection"]["qualifying_seeds"] == [0, 1]
    assert len(amendment["heldout"]["cell_list"]) == 11
    assert amendment["self_commit_binding"] is False

    damaged = copy.deepcopy(amendment)
    stress_row = next(
        row
        for row in damaged["heldout"]["cell_list"]
        if row["cell"] == [7, 4, 3, 3, 4]
    )
    stress_row["slice_membership"].reverse()
    damaged["result_projection_sha256"] = module._projection_sha256(damaged)
    with pytest.raises(ValueError, match="cell list"):
        module.validate_target_amendment(damaged)

    self_bound = copy.deepcopy(amendment)
    self_bound["self_commit_binding"] = True
    self_bound["result_projection_sha256"] = module._projection_sha256(self_bound)
    with pytest.raises(ValueError, match="own containing commit"):
        module.validate_target_amendment(self_bound)


def test_heldout_plan_has_exact_union_and_per_cell_launch_order():
    module = _module()
    amendment = _amendment(module)
    plans = module.build_heldout_plan(
        amendment,
        checkpoint=_checkpoint(module, amendment),
    )
    assert len(plans) == 11
    assert [plan.cell for plan in plans] == sorted(plan.cell for plan in plans)
    stress = [
        plan
        for plan in plans
        if plan.cell == (7, 4, 3, 3, 4)
    ]
    assert len(stress) == 1
    assert stress[0].slice_membership == (
        "width",
        "rounds",
        "axis_family",
        "probability",
    )
    assert stress[0].run_blpensemble is True
    expected_roles = [
        module.DENSE_REFERENCE,
        module.PLAIN_EVIDENCE,
        module.PLAIN_EVIDENCE,
        module.GCAPEPS_EVIDENCE,
        module.GCAPEPS_EVIDENCE,
        module.PLAIN_PERFORMANCE,
        module.GCAPEPS_PERFORMANCE,
        module.PLAIN_PERFORMANCE,
        module.GCAPEPS_PERFORMANCE,
        module.GCAPEPS_PERFORMANCE,
        module.PLAIN_PERFORMANCE,
        module.PLAIN_PERFORMANCE,
        module.GCAPEPS_PERFORMANCE,
        module.SDIM_COMPUTATION,
        module.TERMINAL_COMPARATOR,
    ]
    assert [row.role for row in plans[0].workflow_launches] == expected_roles
    measured = [
        row.parameter_map()
        for row in plans[0].workflow_launches
        if row.parameter_map().get("sample_kind") == "measured"
    ]
    assert [
        (
            "plain" if expected_roles[index + 7] == module.PLAIN_PERFORMANCE else "gc",
            row["sample_index"],
        )
        for index, row in enumerate(measured)
    ] == [
        ("plain", 0),
        ("gc", 0),
        ("gc", 1),
        ("plain", 1),
        ("plain", 2),
        ("gc", 2),
    ]
    workflow_ordinals = [
        row.workflow_ordinal for plan in plans for row in plan.workflow_launches
    ]
    assert workflow_ordinals == list(range(15 * len(plans)))


def test_every_outer_launch_uses_the_supervisor_frozen_role_parameter_schema():
    module = _module()
    supervisor = _supervisor()
    search, calibration_calls = _selected_search(module)
    assert search.prepublication_disposition == module.CALIBRATION_PASS
    amendment = _amendment(module)
    plans = module.build_heldout_plan(
        amendment,
        checkpoint=_checkpoint(module, amendment),
    )
    heldout_calls = [
        launch
        for plan in plans
        for launch in (plan.fixture_launch, *plan.workflow_launches)
    ]
    for launch in (*calibration_calls, *heldout_calls):
        supervisor.validate_role_parameters(
            launch.run_partition, launch.role, launch.parameter_map()
        )


def test_heldout_performance_censor_continues_but_scientific_censor_skips_cell():
    module = _module()
    amendment = _amendment(module)
    plans = module.build_heldout_plan(
        amendment,
        checkpoint=_checkpoint(module, amendment),
    )[:2]
    calls = []

    def performance_censor(spec):
        calls.append(spec.launch_id)
        if spec.launch_id == "held-c00-plain-measured-0":
            return _observation(
                module,
                spec,
                terminal="supervisor_censor",
            )
        qualifier = True if spec.role in {
            module.DENSE_REFERENCE,
            module.PLAIN_EVIDENCE,
            module.GCAPEPS_EVIDENCE,
            module.TERMINAL_COMPARATOR,
        } else None
        return _observation(module, spec, qualifier=qualifier)

    result = module.run_heldout_plan(
        plans,
        performance_censor,
        clock_ns=_clock(),
    )
    assert result.terminal_class == module.HELDOUT_COMPLETE
    assert result.cells[0].timing_disposition == "UNAVAILABLE"
    assert result.cells[0].workflow_status == "completed"
    assert "held-c00-comparator" in calls
    assert "held-c01-dense" in calls

    calls.clear()

    def science_censor(spec):
        calls.append(spec.launch_id)
        if spec.launch_id == "held-c00-plain-evidence-i1":
            return _observation(module, spec, terminal="worker_censor")
        qualifier = True if spec.role in {
            module.DENSE_REFERENCE,
            module.PLAIN_EVIDENCE,
            module.GCAPEPS_EVIDENCE,
            module.TERMINAL_COMPARATOR,
        } else None
        return _observation(module, spec, qualifier=qualifier)

    result = module.run_heldout_plan(plans, science_censor, clock_ns=_clock())
    assert result.terminal_class == module.HELDOUT_INCOMPLETE
    assert result.cells[0].workflow_status == "partial"
    assert "held-c00-comparator" not in calls
    assert "held-c01-dense" in calls


def test_primary_timing_uses_exact_three_raw_samples_median_mad_and_hash_gate():
    module = _module()
    plain_hash = _digest("plain-carrier")
    gc_hash = _digest("gc-carrier")
    def sample(*, lane, index, wall, cpu, launch, carrier_hash):
        state_wall = wall // 2
        state_cpu = cpu // 2
        return module.MeasuredTimingSample(
            lane=lane,
            sample_index=index,
            algorithm_wall_ns=wall,
            algorithm_cpu_ns=cpu,
            state_update_wall_ns=state_wall,
            state_update_cpu_ns=state_cpu,
            supervisor_launch_wall_ns=launch,
            final_carrier_hash=carrier_hash,
            population_rows=(
                (
                    "candidate_algorithm_case_e2e",
                    None,
                    None,
                    None,
                    "no_shadow_trajectory",
                    wall,
                    cpu,
                ),
                (
                    "physical_operation",
                    1,
                    0,
                    None,
                    "CX",
                    state_wall,
                    state_cpu,
                ),
            ),
        )

    rows = [
        sample(
            lane="plain",
            index=index,
            wall=wall,
            cpu=cpu,
            launch=launch,
            carrier_hash=plain_hash,
        )
        for index, (wall, cpu, launch) in enumerate(
            ((100, 70, 150), (120, 90, 180), (110, 80, 160))
        )
    ]
    rows += [
        sample(
            lane="gc",
            index=index,
            wall=wall,
            cpu=cpu,
            launch=launch,
            carrier_hash=gc_hash,
        )
        for index, (wall, cpu, launch) in enumerate(
            ((90, 60, 140), (100, 70, 150), (95, 65, 145))
        )
    ]
    result = module.aggregate_primary_timing(
        rows,
        plain_evidence_worker_wall_ns=300,
        gc_evidence_worker_wall_ns=330,
        plain_evidence_final_carrier_hash=plain_hash,
        gc_evidence_final_carrier_hash=gc_hash,
    )
    plain = result["lanes"]["plain"]["candidate_algorithm_case_e2e_wall_ns"]
    assert plain == {
        "raw": [100, 120, 110],
        "median": 110,
        "mad": 10,
        "minimum": 100,
        "maximum": 120,
    }
    assert result["ratios"]["candidate_algorithm_wall_gc_over_plain"] == 95 / 110
    assert result["ratios"]["evidence_worker_wall_gc_over_plain"] == 1.1
    assert result["lanes"]["plain"]["state_update_only_wall_ns"] == {
        "raw": [50, 60, 55],
        "median": 55,
        "mad": 5,
        "minimum": 50,
        "maximum": 60,
    }
    assert result["lanes"]["gc"]["state_update_only_cpu_ns"]["median"] == 32
    assert result["state_update_only_is_report_only_no_registered_ratio"] is True
    assert all("state_update" not in key for key in result["ratios"])
    assert result["primary_wall_band"] == "SAME_ORDER"

    damaged = list(rows)
    damaged[-1] = sample(
        lane="gc",
        index=2,
        wall=95,
        cpu=65,
        launch=145,
        carrier_hash=_digest("wrong"),
    )
    with pytest.raises(ValueError, match="hash mismatch"):
        module.aggregate_primary_timing(
            damaged,
            plain_evidence_worker_wall_ns=300,
            gc_evidence_worker_wall_ns=330,
            plain_evidence_final_carrier_hash=plain_hash,
            gc_evidence_final_carrier_hash=gc_hash,
        )


def test_nonpositive_registered_timing_scope_makes_only_its_ratio_unavailable():
    module = _module()
    plain_hash = _digest("plain-zero-carrier")
    gc_hash = _digest("gc-positive-carrier")

    def sample(lane, index, algorithm, carrier_hash):
        return module.MeasuredTimingSample(
            lane=lane,
            sample_index=index,
            algorithm_wall_ns=algorithm,
            algorithm_cpu_ns=algorithm,
            state_update_wall_ns=algorithm,
            state_update_cpu_ns=algorithm,
            supervisor_launch_wall_ns=10,
            final_carrier_hash=carrier_hash,
            population_rows=(
                (
                    "candidate_algorithm_case_e2e",
                    None,
                    None,
                    None,
                    "no_shadow_trajectory",
                    algorithm,
                    algorithm,
                ),
                (
                    "physical_operation",
                    1,
                    0,
                    None,
                    "CX",
                    algorithm,
                    algorithm,
                ),
            ),
        )

    rows = [
        sample("plain", index, 0, plain_hash) for index in range(3)
    ] + [
        sample("gc", index, 1, gc_hash) for index in range(3)
    ]
    result = module.aggregate_primary_timing(
        rows,
        plain_evidence_worker_wall_ns=10,
        gc_evidence_worker_wall_ns=10,
        plain_evidence_final_carrier_hash=plain_hash,
        gc_evidence_final_carrier_hash=gc_hash,
    )
    assert result["ratios"]["candidate_algorithm_wall_gc_over_plain"] is None
    assert result["ratio_dispositions"][
        "candidate_algorithm_wall_gc_over_plain"
    ]["status"] == "UNAVAILABLE"
    assert result["ratios"]["supervisor_launch_wall_gc_over_plain"] == 1.0
    assert result["primary_wall_band"] == "UNAVAILABLE"


def test_heldout_report_excludes_partial_workflows_and_has_no_self_file_hash():
    module = _module()
    amendment = _amendment(module)
    checkpoint = _checkpoint(module, amendment)
    plans = module.build_heldout_plan(amendment, checkpoint=checkpoint)[:2]

    def launch(spec):
        if spec.launch_id == "held-c00-gc-evidence-i1":
            return _observation(module, spec, terminal="worker_censor")
        qualifier = True if spec.role in {
            module.DENSE_REFERENCE,
            module.PLAIN_EVIDENCE,
            module.GCAPEPS_EVIDENCE,
            module.TERMINAL_COMPARATOR,
        } else None
        return _observation(module, spec, qualifier=qualifier)

    execution = module.run_heldout_plan(plans, launch, clock_ns=_clock())
    report = module.build_heldout_report(
        amendment=amendment,
        checkpoint=checkpoint,
        execution=execution,
        cell_results={"bounded_test_payload": True},
    )
    module.validate_heldout_report(report, amendment=amendment)
    assert len(report["complete_case_workflow_supervisor_wall_ns"]) == 1
    assert "complete_file_sha256" not in report

    damaged = copy.deepcopy(report)
    damaged["complete_case_workflow_supervisor_wall_ns"].append(1)
    damaged["result_projection_sha256"] = module._projection_sha256(damaged)
    with pytest.raises(ValueError, match="partial workflow"):
        module.validate_heldout_report(damaged, amendment=amendment)


def _performance_worker_frames(*, lane="plain", native_compression=False):
    timing = _load(
        ROOT
        / "scripts"
        / "external_baselines"
        / "gcapeps_finite_memory_timing.py",
        f"gcapeps_finite_memory_timing_for_outer_{lane}",
    )
    case_id = "heldout-w3-r1-a3-p4of4"
    timer = timing.LayeredTimer()
    worker_lane = "plain" if lane == "plain" else "gcapeps"
    with timer.span(
        "performance.root",
        scope="performance_worker_total",
        kind="worker",
        lane=worker_lane,
        case_id=case_id,
        trajectory_id="input1",
    ):
        with timer.span(
            "performance.setup",
            scope="setup_and_gate_mask_materialization",
            kind="fixture_validation",
            lane=worker_lane,
            case_id=case_id,
            trajectory_id="input1",
        ):
            pass
        with timer.span(
            "performance.algorithm",
            scope="candidate_algorithm_case_e2e",
            kind="no_shadow_trajectory",
            lane=worker_lane,
            case_id=case_id,
            trajectory_id="input1",
        ):
            with timer.span(
                "performance.init",
                scope="candidate_initialization",
                kind="candidate_initialization",
                lane=worker_lane,
                case_id=case_id,
                trajectory_id="input1",
            ):
                pass
            with timer.span(
                "performance.round.1",
                scope="round",
                kind="round",
                lane=worker_lane,
                case_id=case_id,
                trajectory_id="input1",
                round_index=1,
            ):
                with timer.span(
                    "performance.operation.0",
                    scope="physical_operation",
                    kind="CX",
                    lane=worker_lane,
                    case_id=case_id,
                    trajectory_id="input1",
                    round_index=1,
                    operation_index=0,
                ):
                    if lane == "gc" and native_compression:
                        with timer.span(
                            "performance.operation.0.step.0",
                            scope="named_algorithm_substep",
                            kind="native_identity_compression",
                            lane=worker_lane,
                            case_id=case_id,
                            trajectory_id="input1",
                            round_index=1,
                            operation_index=0,
                            step_index=0,
                        ):
                            with timer.span(
                                "performance.operation.0.step.1",
                                scope="named_algorithm_substep",
                                kind="native_compression_split:0",
                                lane=worker_lane,
                                case_id=case_id,
                                trajectory_id="input1",
                                round_index=1,
                                operation_index=0,
                                step_index=1,
                            ):
                                pass
                    else:
                        with timer.span(
                            "performance.operation.0.step.0",
                            scope="named_algorithm_substep",
                            kind=(
                                "capped_native_split"
                                if lane == "plain"
                                else "frame_composition"
                            ),
                            lane=worker_lane,
                            case_id=case_id,
                            trajectory_id="input1",
                            round_index=1,
                            operation_index=0,
                            step_index=0,
                        ):
                            pass
        with timer.span(
            "performance.serialization",
            scope="serialization",
            kind="core_encoding",
            lane=worker_lane,
            case_id=case_id,
            trajectory_id="input1",
        ):
            pass
    core_bytes = b"{}"
    trailer_bytes = timing.build_late_telemetry_trailer(
        core_bytes,
        timer.finish(),
    )
    return timing, case_id, core_bytes, trailer_bytes


def test_performance_trailer_drives_overall_and_state_update_only_totals():
    module = _module()
    timing, case_id, core_bytes, trailer_bytes = _performance_worker_frames()
    del timing
    sample = module.measured_timing_sample_from_trailer(
        core_bytes=core_bytes,
        trailer_bytes=trailer_bytes,
        lane="plain",
        case_id=case_id,
        sample_index=0,
        supervisor_launch_wall_ns=123,
        final_carrier_hash=_digest("plain-carrier"),
    )
    by_scope = {row[0]: row for row in sample.population_rows}
    assert sample.algorithm_wall_ns == by_scope[
        "candidate_algorithm_case_e2e"
    ][5]
    assert sample.algorithm_cpu_ns == by_scope[
        "candidate_algorithm_case_e2e"
    ][6]
    assert sample.state_update_wall_ns == by_scope["physical_operation"][5]
    assert sample.state_update_cpu_ns == by_scope["physical_operation"][6]


@pytest.mark.parametrize(
    ("target_scope", "field", "replacement", "message"),
    (
        (
            "physical_operation",
            "scope",
            "setup_and_gate_mask_materialization",
            "unregistered scope",
        ),
        (
            "named_algorithm_substep",
            "kind",
            "matrix_materialization",
            "named algorithm substep",
        ),
    ),
)
def test_performance_trailer_rejects_timing_leaf_misclassification(
    target_scope,
    field,
    replacement,
    message,
):
    module = _module()
    timing, case_id, core_bytes, trailer_bytes = _performance_worker_frames()
    trailer = json.loads(trailer_bytes.decode("ascii"))
    target = next(
        row
        for row in trailer["timing"]["spans"]
        if row["scope"] == target_scope
    )
    target[field] = replacement
    corrupted = timing.canonical_json_bytes(trailer)
    with pytest.raises(ValueError, match=message):
        module.measured_timing_sample_from_trailer(
            core_bytes=core_bytes,
            trailer_bytes=corrupted,
            lane="plain",
            case_id=case_id,
            sample_index=0,
            supervisor_launch_wall_ns=123,
            final_carrier_hash=_digest("plain-carrier"),
        )


def test_gc_native_compression_parent_and_split_leaf_are_both_registered():
    module = _module()
    timing, case_id, core_bytes, trailer_bytes = _performance_worker_frames(
        lane="gc",
        native_compression=True,
    )
    sample = module.measured_timing_sample_from_trailer(
        core_bytes=core_bytes,
        trailer_bytes=trailer_bytes,
        lane="gc",
        case_id=case_id,
        sample_index=0,
        supervisor_launch_wall_ns=123,
        final_carrier_hash=_digest("gc-carrier"),
    )
    kinds = {row[4] for row in sample.population_rows}
    assert "native_identity_compression" in kinds
    assert "native_compression_split:0" in kinds

    trailer = json.loads(trailer_bytes.decode("ascii"))
    split = next(
        row
        for row in trailer["timing"]["spans"]
        if row["kind"] == "native_compression_split:0"
    )
    split["kind"] = "frame_composition"
    corrupted = timing.canonical_json_bytes(trailer)
    with pytest.raises(ValueError, match="named algorithm substep"):
        module.measured_timing_sample_from_trailer(
            core_bytes=core_bytes,
            trailer_bytes=corrupted,
            lane="gc",
            case_id=case_id,
            sample_index=0,
            supervisor_launch_wall_ns=123,
            final_carrier_hash=_digest("gc-carrier"),
        )


def test_performance_trailer_rejects_omitted_registered_leaf():
    module = _module()
    timing, case_id, core_bytes, trailer_bytes = _performance_worker_frames()
    trailer = json.loads(trailer_bytes.decode("ascii"))
    target = next(
        row
        for row in trailer["timing"]["spans"]
        if row["scope"] == "named_algorithm_substep"
    )
    trailer["timing"]["spans"].remove(target)
    corrupted = timing.canonical_json_bytes(trailer)
    with pytest.raises(ValueError, match="reconciliation"):
        module.measured_timing_sample_from_trailer(
            core_bytes=core_bytes,
            trailer_bytes=corrupted,
            lane="plain",
            case_id=case_id,
            sample_index=0,
            supervisor_launch_wall_ns=123,
            final_carrier_hash=_digest("plain-carrier"),
        )
