"""Refusal-path and dry-run controls for the fixture-v2 confirmatory harness.

Covers, per the amendment-1 embedding contract AND the amendment-2 rulings
of ``scripts/external_baselines/run_gcapeps_v2_confirmatory.py``:

* the frozen six-cell frame (amendment 2 item 1): registered mode resolves
  exactly heldout {hv2-0, hv2-1} x gamma{1,2,3} x w7 r10; off-frame cells
  are refused; both HELDOUT seeds are refused in development; out-of-grid
  cells are refused by the emitter gate;
* the owner-release gate: with amendment 2 landed it is the ONE remaining
  registered gate before the first heldout build; no token exists yet, so
  every registered execution refuses there (and only there);
* the Stage-0 measured-value gate (amendment 1 item 5): a measured
  worst-pair value above 1e-4 refuses the run; a passing value is
  re-recorded;
* dual-gate wiring (amendment 1 item 3) on the X5-theta0 vehicle adopted
  by amendment 2 item 2, with the run-time op-for-op equivalence
  verification;
* the strict all-below-margin adjudication table (amendment 1 item 4):
  six WITNESS_BELOW_MARGIN cells score a fixture-capability MISS;
* arm schema routing: X8 / cx_only / thin_only route to their owning
  emitters and schemas; unknown arms are refused;
* a development-mode dry run on a CALIBRATION cell only, recording the
  amendment-2 control surfaces (untruncated F=1 wired but NOT_RUN with the
  plain lane off; LOCAL-alphabet removed by item 3(ii)).

ABSOLUTE constraint honored: nothing here builds a HELDOUT fixture.  The
heldout seeds appear only as frozen configuration; every fixture built in
this file is CALIBRATION, and the dry-run test asserts that.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
RUNNER = (
    REPO / "scripts" / "external_baselines" / "run_gcapeps_v2_confirmatory.py"
)
DEV_CELL = {"seed": 2, "gamma_index": 2, "rounds": 10, "run_partition": "CALIBRATION"}


def _load_runner():
    name = "run_gcapeps_v2_confirmatory_under_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return _load_runner()


@pytest.fixture(scope="module")
def oracle(runner):
    return runner.DenseOracle()


def _passing_stage0_payload(runner, worst: float) -> dict:
    pairs = {}
    for index, name in enumerate(runner.STAGE0_EXPECTED_PAIRS):
        value = worst if index == 0 else worst / 10.0
        pairs[name] = {
            "checkpoints": {
                "99": {
                    "raw_metrics": {
                        "metrics": {"one_minus_fidelity": value / 2.0}
                    }
                },
                "100": {
                    "raw_metrics": {
                        "metrics": {"one_minus_fidelity": value}
                    }
                },
            }
        }
    return {
        "schema": runner.STAGE0_SCHEMA,
        "applied_bands": {"band_set": runner.STAGE0_BAND_SET},
        "verdict": runner.STAGE0_PASS_VERDICT,
        "thread_invariance": {"pairs": pairs},
        "result_projection_sha256": "f" * 64,
        "fixture_identity": {"case_id": "synthetic-stage0-for-tests"},
    }


# ---------------------------------------------------------------- cell frame


def test_registered_mode_refuses_non_heldout_seed(runner):
    with pytest.raises(runner.Refusal, match="two frozen v2 heldout"):
        runner.resolve_cells(
            "registered", [{"seed": 2, "gamma_index": 2, "rounds": 10}]
        )


def test_registered_mode_resolves_the_frozen_six_cell_frame(runner):
    """Amendment 2 item 1: the frame is frozen, not caller-chosen.

    Resolution builds NOTHING; it returns the frozen coordinates only."""

    frame = runner.resolve_cells("registered", [])
    assert len(frame) == 6
    assert [runner.cell_label(cell) for cell in frame] == [
        "hv2-0-g1-r10",
        "hv2-0-g2-r10",
        "hv2-0-g3-r10",
        "hv2-1-g1-r10",
        "hv2-1-g2-r10",
        "hv2-1-g3-r10",
    ]
    for cell in frame:
        assert cell["run_partition"] == "HELDOUT"
        assert cell["seed"] in runner.V2_HELDOUT_SEEDS
        assert cell["width"] == 7
        assert cell["rounds"] == 10
        assert cell["axis_family"] == 3
        assert cell["p_event_numerator"] == 3

    # An explicit request matching the frame exactly also resolves.
    requested = [
        runner.parse_cell(f"hv2-{k}-g{g}-r10")
        for k in (0, 1)
        for g in (1, 2, 3)
    ]
    assert runner.resolve_cells("registered", requested) == frame


def test_registered_mode_refuses_off_frame_heldout_cells(runner):
    """Any heldout-seed cell outside the frozen six-cell list refuses."""

    for off_frame in (
        [{"seed": runner.V2_HELDOUT_SEEDS[0], "gamma_index": 0, "rounds": 10}],
        [{"seed": runner.V2_HELDOUT_SEEDS[1], "gamma_index": 2, "rounds": 4}],
        [
            {
                "seed": runner.V2_HELDOUT_SEEDS[0],
                "gamma_index": 2,
                "rounds": 10,
            }
        ],  # a strict subset of the frame is not the frame
    ):
        with pytest.raises(runner.Refusal, match="frozen six-cell"):
            runner.resolve_cells("registered", off_frame)


def test_parse_cell_accepts_hv2_labels_and_bounds_them(runner):
    assert runner.parse_cell("hv2-0-g1-r10")["seed"] == (
        runner.V2_HELDOUT_SEEDS[0]
    )
    assert runner.parse_cell("hv2-1-g3-r10")["seed"] == (
        runner.V2_HELDOUT_SEEDS[1]
    )
    import argparse as _argparse

    with pytest.raises(_argparse.ArgumentTypeError, match="hv2-0 and hv2-1"):
        runner.parse_cell("hv2-2-g1-r10")


@pytest.mark.parametrize("seed_index", [0, 1])
def test_development_mode_refuses_both_heldout_seeds(runner, seed_index):
    with pytest.raises(runner.Refusal, match="CALIBRATION-only"):
        runner.resolve_cells(
            "development",
            [
                {
                    "seed": runner.V2_HELDOUT_SEEDS[seed_index],
                    "gamma_index": 2,
                    "rounds": 10,
                }
            ],
        )


# ---------------------------------------------------------------- release


def test_owner_release_gate_is_the_single_remaining_registered_gate(runner):
    """No token minted: registered refuses at the owner-release gate with
    a message saying it is the ONE remaining gate."""

    with pytest.raises(runner.Refusal, match="ONE remaining gate") as info:
        runner.enforce_owner_release("registered", None)
    assert "owner-release-token" in str(info.value)
    assert "No token has been minted yet" in str(info.value)

    # Any supplied token is refused while no token has been minted.
    assert runner.OWNER_RELEASE_TOKEN_SHA256 is None
    with pytest.raises(
        runner.Refusal, match="no owner-release token has been minted"
    ):
        runner.enforce_owner_release("registered", "guessed-token")


def test_owner_release_gate_is_registered_mode_only(runner):
    row = runner.enforce_owner_release("development", None)
    assert row["status"] == "NOT_APPLICABLE_IN_DEVELOPMENT"
    with pytest.raises(runner.Refusal, match="registered mode"):
        runner.enforce_owner_release("development", "anything")


def test_development_mode_refuses_non_calibration_seed(runner):
    with pytest.raises(runner.Refusal, match="seeds\\s*0\\.\\.3"):
        runner.resolve_cells(
            "development", [{"seed": 7, "gamma_index": 2, "rounds": 10}]
        )


def test_development_cells_are_forced_to_calibration_partition(runner):
    cells = runner.resolve_cells(
        "development", [{"seed": 2, "gamma_index": 2, "rounds": 10}]
    )
    assert all(cell["run_partition"] == "CALIBRATION" for cell in cells)


def test_out_of_grid_cell_is_refused_by_the_emitter_gate(runner):
    """A cell outside the frozen CALIBRATION grid is refused, not built."""

    bad_cell = {
        "seed": 2,
        "gamma_index": 2,
        "rounds": 3,  # not in the frozen calibration rounds
        "run_partition": "CALIBRATION",
    }
    with pytest.raises(runner.Refusal, match="outside the frozen grid"):
        runner.fixture_for_arm("X8", bad_cell)


def _run_cli(arguments):
    """Run the harness CLI in a fresh process (the thread-envelope guard
    intentionally refuses in-process scientific imports)."""

    return subprocess.run(
        [sys.executable, str(RUNNER), *arguments],
        capture_output=True,
        text=True,
    )


def test_registered_cli_refuses_calibration_cell(runner, tmp_path):
    evidence = tmp_path / "stage0.json"
    evidence.write_text(
        json.dumps(_passing_stage0_payload(runner, 1.2e-5))
    )
    completed = _run_cli(
        [
            "--mode",
            "registered",
            "--cell",
            "s2-g2-r10",
            "--stage0-evidence",
            str(evidence),
        ]
    )
    assert completed.returncode == 2
    assert "REFUSED" in completed.stdout


# ---------------------------------------------------------------- stage0


def test_stage0_gate_records_passing_measured_value(runner, tmp_path):
    evidence = tmp_path / "stage0_pass.json"
    evidence.write_text(
        json.dumps(_passing_stage0_payload(runner, 1.2e-5))
    )
    record = runner.stage0_gate(evidence)
    assert record["measured_worst_pair_one_minus_fidelity"] == (
        pytest.approx(1.2e-5)
    )
    assert record["threshold"] == 1.0e-4


def test_stage0_gate_refuses_measured_value_above_1e4(runner, tmp_path):
    evidence = tmp_path / "stage0_fail.json"
    evidence.write_text(
        json.dumps(_passing_stage0_payload(runner, 2.0e-4))
    )
    with pytest.raises(runner.Refusal, match="exceeds the amendment-item-5"):
        runner.stage0_gate(evidence)


def test_stage0_gate_refuses_band_alone_semantics(runner, tmp_path):
    """The 6.1e-4 band value itself must refuse: the criterion is the
    MEASURED value, and 6.1e-4 > 1e-4 (amendment item 5)."""

    evidence = tmp_path / "stage0_band.json"
    evidence.write_text(
        json.dumps(_passing_stage0_payload(runner, 6.1e-4))
    )
    with pytest.raises(runner.Refusal):
        runner.stage0_gate(evidence)


def test_stage0_gate_refuses_wrong_lane_and_verdict(runner, tmp_path):
    payload = _passing_stage0_payload(runner, 1.2e-5)
    payload["applied_bands"]["band_set"] = "something_else"
    evidence = tmp_path / "stage0_lane.json"
    evidence.write_text(json.dumps(payload))
    with pytest.raises(runner.Refusal, match="amended trim_cluster"):
        runner.stage0_gate(evidence)

    payload = _passing_stage0_payload(runner, 1.2e-5)
    payload["verdict"] = "FAIL_ENGINEERING_NATIVE_THREAD_REGRESSION"
    evidence.write_text(json.dumps(payload))
    with pytest.raises(runner.Refusal, match="verdict"):
        runner.stage0_gate(evidence)


def test_registered_mode_requires_stage0_evidence():
    completed = _run_cli(["--mode", "registered", "--cell", "s2-g2-r10"])
    assert completed.returncode == 2
    assert "REFUSED" in completed.stdout


# ---------------------------------------------------------------- dual gates


@pytest.fixture(scope="module")
def theta0_context(runner, oracle):
    return runner.build_theta0_context(oracle, dict(DEV_CELL))


def test_theta0_dual_gates_both_run_and_pass(runner, theta0_context):
    results = runner.run_theta0_dual_gates(theta0_context)
    assert sorted(results) == sorted(runner.THETA0_REQUIRED_GATES)
    adjudication = runner.adjudicate_theta0_dual_gates(results)
    assert adjudication["all_ran"] is True
    assert adjudication["all_passed"] is True
    gate = results["d_trajectory"]
    assert gate["max_abs_stim_minus_dense"] <= 1.0e-12
    assert gate["clifford_recurrence"] is True
    assert gate["vehicle_is_non_flat"] is True
    ag = results["inner_product_ag"]
    assert ag["ag_printed_example_passed"] is True
    assert ag["round_trip_passed"] is True


def test_removing_either_theta0_gate_fails(
    runner, theta0_context, monkeypatch
):
    for removed in runner.THETA0_REQUIRED_GATES:
        implementations = {
            name: impl
            for name, impl in runner._THETA0_GATE_IMPLEMENTATIONS.items()
            if name != removed
        }
        monkeypatch.setattr(
            runner, "_THETA0_GATE_IMPLEMENTATIONS", implementations
        )
        with pytest.raises(runner.Refusal, match="BOTH gates"):
            runner.run_theta0_dual_gates(theta0_context)
        monkeypatch.undo()


def test_missing_gate_result_refuses_adjudication(runner, theta0_context):
    results = runner.run_theta0_dual_gates(theta0_context)
    for removed in runner.THETA0_REQUIRED_GATES:
        partial = {
            name: row for name, row in results.items() if name != removed
        }
        with pytest.raises(runner.Refusal, match="dual-gate"):
            runner.adjudicate_theta0_dual_gates(partial)


def test_x5_theta0_vehicle_equivalence_verified_on_registered_path(
    runner, theta0_context
):
    """Amendment 2 item 2: the vehicle is the registered path and the
    op-for-op equivalence is verified at run time."""

    equivalence = theta0_context["x5_theta0_equivalence"]
    assert equivalence["verified"] is True
    assert equivalence["ruling"].startswith("amendment 2 item 2")
    assert equivalence["operation_count"] > 0
    assert equivalence["round_count"] == DEV_CELL["rounds"]
    assert equivalence["cross_row_gate"] == ["CX", [3, 10]]
    assert "amendment 2 item 2" in theta0_context["vehicle_adopted_by"]
    # The equivalence verification consumed two DIFFERENT committed arms.
    assert equivalence["vehicle_fixture_hash"] != (
        equivalence["reconstruction_fixture_hash"]
    )


def test_x5_theta0_equivalence_mismatch_refuses(runner, monkeypatch):
    """A broken reconstruction must refuse, not silently pass: swapping
    the thin-only reconstruction basis for the X8 arm (even-round CX)
    breaks the op-for-op equality on even rounds."""

    original = runner.fixture_for_arm

    def swapped(arm, cell):
        if arm == "thin_only":
            return original("X8", cell)
        return original(arm, cell)

    monkeypatch.setattr(runner, "fixture_for_arm", swapped)
    with pytest.raises(runner.Refusal, match="amendment 2 item 2"):
        runner.verify_x5_theta0_equivalence(dict(DEV_CELL))


# ---------------------------------------------------------------- margins


def test_strict_all_below_margin_scores_fixture_capability_miss(runner):
    verdicts = [runner.VERDICT_BELOW_MARGIN] * 6
    row = runner.adjudicate_margin_outcome(verdicts)
    assert row["fired"] is True
    assert row["outcome"] == runner.VERDICT_CAPABILITY_MISS
    assert row["confirmatory_claim_dies"] is True
    assert row["evidence_of_witness_absence"] is False
    assert "MEASURED err_cell" in row["revisit_requires"]


def test_mixed_margin_table_does_not_fire(runner):
    verdicts = [runner.VERDICT_BELOW_MARGIN] * 5 + [runner.VERDICT_WITNESS]
    row = runner.adjudicate_margin_outcome(verdicts)
    assert row["fired"] is False
    assert "outcome" not in row


def test_incomplete_frame_does_not_fire_the_strict_rule(runner):
    verdicts = [runner.VERDICT_BELOW_MARGIN] * 2
    row = runner.adjudicate_margin_outcome(verdicts)
    assert row["fired"] is False


def test_margin_classification_vocabulary(runner):
    blp_no = {"max_increment": 5.0e-11, "positive_above_guard": False}
    assert (
        runner.classify_cell_witness(blp_no, 1.0e-3)["verdict"]
        == runner.VERDICT_NO_WITNESS
    )
    blp_low = {"max_increment": 5.0e-3, "positive_above_guard": True}
    assert (
        runner.classify_cell_witness(blp_low, 1.0e-3)["verdict"]
        == runner.VERDICT_BELOW_MARGIN
    )
    blp_high = {"max_increment": 5.0e-2, "positive_above_guard": True}
    assert (
        runner.classify_cell_witness(blp_high, 1.0e-3)["verdict"]
        == runner.VERDICT_WITNESS
    )


def test_p2_majority_tie_scores_not_confirmed(runner):
    def rows(positive_count, total=6):
        return [
            {"blp": {"positive_above_guard": index < positive_count}}
            for index in range(total)
        ]

    verdict = runner.adjudicate_p2(rows(4), rows(0), rows(3))
    assert verdict["sub_claims"]["thin_only_witness_minority"] == (
        "NOT_CONFIRMED_MISS_AT_TIE"
    )
    assert verdict["verdict"] == "NOT_CONFIRMED_MISS"

    confirmed = runner.adjudicate_p2(rows(4), rows(0), rows(1))
    assert confirmed["verdict"] == "CONFIRMED"

    killed = runner.adjudicate_p2(rows(4), rows(0), rows(4))
    assert killed["thin_only_matches_x8_rate"] is True
    assert killed["mechanism_reading"] == (
        "CX_LEVER_NOT_ESTABLISHED_X8_MECHANISM_READING_KILLED"
    )


# ---------------------------------------------------------------- routing


def test_arm_schema_routing(runner):
    cell = dict(DEV_CELL, rounds=4)
    for arm, (_, expected_schema) in runner.ARM_EMITTERS.items():
        fixture, fixture_hash, schema = runner.fixture_for_arm(arm, cell)
        assert schema == expected_schema
        assert fixture["schema"] == expected_schema
        assert fixture["run_partition"] == "CALIBRATION"
        assert len(fixture_hash) == 64
    assert runner.ARM_EMITTERS["X8"][1].endswith(".fixture.v2")
    assert "cx_only_arm" in runner.ARM_EMITTERS["cx_only"][1]
    assert "thin_only_arm" in runner.ARM_EMITTERS["thin_only"][1]


def test_unknown_arm_is_refused(runner):
    with pytest.raises(runner.Refusal, match="unknown arm"):
        runner.fixture_for_arm("X5", dict(DEV_CELL))


def test_x5_absent_from_committed_arm_registry(runner):
    """Structural, by design: no separate X5 emitter is registered; the
    anchor arm is realized as cx_only at theta=0 (amendment 2 item 2)."""

    assert "X5" not in runner.ARM_EMITTERS
    anchor = runner.FROZEN_CONFIRMATORY_CONSTRAINTS["mandatory_anchor_arm"]
    assert anchor.startswith("x5_variant_theta0")
    assert "amendment 2 item 2" in anchor


def test_tampered_fixture_is_refused_by_routing_validation(runner):
    cell = dict(DEV_CELL, rounds=4)
    fixture, _, _ = runner.fixture_for_arm("X8", cell)
    tampered = copy.deepcopy(fixture)
    tampered["carrier_path"]["round_ledger"][0]["operations"][0][
        "targets"
    ] = [0]
    emitter = runner._load_sibling("emit_gcapeps_finite_memory_fixture_v2")
    with pytest.raises(ValueError):
        emitter.validate_fixture(tampered)


# ---------------------------------------------------------------- dry run


def test_development_dry_run_on_calibration_cell(runner, tmp_path):
    evidence = tmp_path / "stage0.json"
    evidence.write_text(
        json.dumps(_passing_stage0_payload(runner, 1.2e-5))
    )
    output = tmp_path / "dry_run.json"
    completed = _run_cli(
        [
            "--mode",
            "development",
            "--cell",
            "s2-g2-r10",
            "--stage0-evidence",
            str(evidence),
            "--plain-lane",
            "off",
            "--output",
            str(output),
        ]
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    # Amendment 2 item 2: the vehicle equivalence is verified and printed.
    assert "op-for-op equivalence VERIFIED" in completed.stdout
    assert "amendment 2 item 2" in completed.stdout
    payload = json.loads(output.read_text())

    # standing and labels
    assert payload["mode"] == "development"
    assert payload["registered_standing"] is False
    assert "DEVELOPMENT" in payload["label"]
    assert payload["adjudication"]["standing"].startswith(
        "DEVELOPMENT_DRY_RUN_NONCLAIM"
    )

    # absolute constraint: nothing built a HELDOUT fixture
    for cell_row in payload["cells"]:
        assert cell_row["cell"]["run_partition"] == "CALIBRATION"
        for arm_row in cell_row["arms"].values():
            assert "calibration-" in arm_row["case_id"]
            assert "heldout" not in arm_row["case_id"].lower()
    for heldout_seed in runner.V2_HELDOUT_SEEDS:
        assert str(heldout_seed) not in json.dumps(payload["cells"])

    # the owner-release gate is registered-only
    assert payload["owner_release_gate"]["status"] == (
        "NOT_APPLICABLE_IN_DEVELOPMENT"
    )

    # stage0 re-record
    assert payload["stage0_gate"][
        "measured_worst_pair_one_minus_fidelity"
    ] == pytest.approx(1.2e-5)

    # dual gates both ran and passed
    dual = payload["adjudication"]["theta0_dual_gates"]
    assert sorted(dual["required_gates"]) == sorted(
        runner.THETA0_REQUIRED_GATES
    )
    assert dual["all_ran"] is True and dual["all_passed"] is True

    # arms present with the routed schemas
    arms = payload["cells"][0]["arms"]
    assert sorted(arms) == ["X8", "cx_only", "thin_only"]
    assert arms["X8"]["fixture_schema"].endswith(".fixture.v2")

    # X8 dense witness on the development cell reproduces screening
    # (X8 s2-g2-r10: +4.227e-2, arrival round <= 5; development data)
    x8_blp = arms["X8"]["blp"]
    assert x8_blp["positive_above_guard"] is True
    assert x8_blp["max_increment"] == pytest.approx(4.227e-2, rel=1e-3)

    # P3 flatness on the X8 theta0 arm; P4 exact frame relevance
    assert arms["X8"]["p3_x8_flatness"]["passed"] is True
    assert arms["X8"]["p4"]["passed"] is True
    assert arms["X8"]["p4"]["cx_coupled_rounds"] == [2, 4, 6, 8, 10]

    # inherited controls: implemented control passed and its trip fired;
    # the untruncated control is WIRED (amendment 2 item 3(i)) but not run
    # with the plain lane off; LOCAL-alphabet is removed by item 3(ii)
    controls = payload["inherited_exactness_controls"]
    assert controls["theta0_plus_no_cx_constant_d"]["passed"] is True
    assert controls["theta0_plus_no_cx_corruption_trip"]["fired"] is True
    assert controls["untruncated_f_equals_1"]["status"] == "NOT_RUN"
    assert "amendment 2 item 3(i)" in (
        controls["untruncated_f_equals_1"]["detail"]
    )
    assert controls["local_alphabet_f_equals_1"]["status"] == (
        "REMOVED_BY_AMENDMENT_2_ITEM_3II"
    )
    assert "disclosed weakening" in (
        controls["local_alphabet_f_equals_1"]["detail"]
    )
    assert controls["registered_mode_blockers"] == []

    # every FA row is ruled by amendment 2, none merely flagged
    rulings = payload["amendment_2_rulings"]
    assert sorted(rulings) == [f"FA-{n}" for n in range(1, 9)]
    assert all("ruled by amendment 2" in row for row in rulings.values())

    # section 3b inert-checkpoint control on the development cell
    inert = payload["inert_checkpoint_control"]
    assert inert["as_expected"] is True
    assert inert["all_rounds_max_increment"] == pytest.approx(
        7.227e-4, rel=1e-3
    )

    # margin: err_cell not measured in this dry run -> unclassified
    assert arms["X8"]["margin_classification"]["verdict"] == (
        "UNCLASSIFIED_MARGIN_ERR_CELL_NOT_MEASURED"
    )
    assert payload["lanes"]["l2bp_compressor_lane"] == (
        "NOT adopted by this preregistration"
    )

    # incomplete frame: adjudication reports it rather than deciding
    assert payload["adjudication"]["p1"]["verdict"] == "INCOMPLETE_FRAME"
