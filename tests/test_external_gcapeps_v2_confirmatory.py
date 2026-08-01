"""Refusal-path and dry-run controls for the fixture-v2 confirmatory harness.

Covers, per the amendment-1 embedding contract, the amendment-2 rulings,
AND the amendment-3 rescalings/topology of
``scripts/external_baselines/run_gcapeps_v2_confirmatory.py``:

* the frozen fifteen-cell frame (amendment 3 item 1): registered mode
  resolves exactly heldout {hv2-0..hv2-4} x gamma{1,2,3} x w7 r10;
  off-frame cells are refused; every HELDOUT seed is refused in
  development; out-of-grid cells are refused by the emitter gate;
* the owner-release gate: it is the ONE remaining registered gate before
  the first heldout build; no token exists yet, so every registered
  execution refuses there (and only there), and a direct ``--cell-child``
  invocation is never a bypass around it;
* the Stage-0 measured-value gate (amendment 1 item 5): a measured
  worst-pair value above 1e-4 refuses the run; a passing value is
  re-recorded;
* dual-gate wiring (amendment 1 item 3) on the X5-theta0 vehicle adopted
  by amendment 2 item 2, with the run-time op-for-op equivalence
  verification;
* the rescaled adjudication counts (amendment 3 item 2): majority
  >= 10/15, minority <= 5/15, strictly-between NOT-CONFIRMED, and the
  strict all-below-margin table over all fifteen cells;
* the parallel execution topology (amendment 3 item 3): immutable plan
  hashed before any child launches, bounded --jobs, fresh single-threaded
  children, ONE aggregation writer, thread-envelope refusal, and
  byte-identical per-cell payloads between --jobs 1 and --jobs 3;
* the 1e-12 untruncated band (amendment 3 item 4) and the
  engineered-fixture claim-boundary sentence (amendment 3 item 5);
* the amendment-4 untruncated-control vehicle (item 1: the control is
  re-vehicled to ONE uncapped plain child per run on the frozen w3
  v1-native vehicle -- the committed plain-engine tests' engineering
  coordinates -- gated at the unchanged 1e-12 band) and the
  control-child resource-refusal guard (item 2: a frozen wall-clock
  budget; timeout kills the child process-group-clean and refuses with
  the measured elapsed time, never hangs);
* arm schema routing: X8 / cx_only / thin_only route to their owning
  emitters and schemas; unknown arms are refused;
* a development-mode dry run on a CALIBRATION cell only, recording the
  amendment-2 control surfaces (untruncated F=1 wired but NOT_RUN with the
  plain lane off; LOCAL-alphabet removed by item 3(ii)).

ABSOLUTE constraint honored: nothing here builds a HELDOUT fixture.  The
heldout seeds appear only as frozen configuration and refusal-path
requests; every fixture built in this file is CALIBRATION, and the
dry-run test asserts that.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import re
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
    with pytest.raises(runner.Refusal, match="five frozen v2 heldout"):
        runner.resolve_cells(
            "registered", [{"seed": 2, "gamma_index": 2, "rounds": 10}]
        )


def test_registered_mode_resolves_the_frozen_fifteen_cell_frame(runner):
    """Amendment 3 item 1: the frame is frozen, not caller-chosen.

    Resolution builds NOTHING; it returns the frozen coordinates only."""

    frame = runner.resolve_cells("registered", [])
    assert len(frame) == 15
    assert [runner.cell_label(cell) for cell in frame] == [
        f"hv2-{k}-g{g}-r10" for k in range(5) for g in (1, 2, 3)
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
        for k in range(5)
        for g in (1, 2, 3)
    ]
    assert runner.resolve_cells("registered", requested) == frame


def test_heldout_seed_stream_is_the_frozen_hash_chain(runner):
    """Amendment 3 item 1: five seeds from the two-digest hash chain,
    hv2-0/hv2-1 byte-identical to the previously landed pair."""

    import hashlib as _hashlib

    digest_0 = _hashlib.sha256(
        b"gcapeps-finite-memory-heldout-v2"
    ).digest()
    digest_1 = _hashlib.sha256(digest_0).digest()
    stream = digest_0 + digest_1
    assert runner.V2_HELDOUT_SEEDS == tuple(
        int.from_bytes(stream[8 * index : 8 * (index + 1)], "big")
        for index in range(5)
    )
    # Regression: the chain extension moved neither previously frozen seed.
    assert runner.V2_HELDOUT_SEEDS[0] == int.from_bytes(
        digest_0[:8], "big"
    )
    assert runner.V2_HELDOUT_SEEDS[1] == int.from_bytes(
        digest_0[8:16], "big"
    )
    assert len(set(runner.V2_HELDOUT_SEEDS)) == 5
    assert runner.HELDOUT_SEED_LABELS == {
        seed: f"hv2-{index}"
        for index, seed in enumerate(runner.V2_HELDOUT_SEEDS)
    }


def test_registered_mode_refuses_off_frame_heldout_cells(runner):
    """Any heldout-seed cell outside the frozen fifteen-cell list refuses."""

    for off_frame in (
        [{"seed": runner.V2_HELDOUT_SEEDS[0], "gamma_index": 0, "rounds": 10}],
        [{"seed": runner.V2_HELDOUT_SEEDS[4], "gamma_index": 2, "rounds": 4}],
        [
            {
                "seed": runner.V2_HELDOUT_SEEDS[0],
                "gamma_index": 2,
                "rounds": 10,
            }
        ],  # a strict subset of the frame is not the frame
    ):
        with pytest.raises(runner.Refusal, match="frozen fifteen-cell"):
            runner.resolve_cells("registered", off_frame)


def test_parse_cell_accepts_hv2_labels_and_bounds_them(runner):
    assert runner.parse_cell("hv2-0-g1-r10")["seed"] == (
        runner.V2_HELDOUT_SEEDS[0]
    )
    assert runner.parse_cell("hv2-4-g3-r10")["seed"] == (
        runner.V2_HELDOUT_SEEDS[4]
    )
    import argparse as _argparse

    with pytest.raises(
        _argparse.ArgumentTypeError, match=r"hv2-0\.\.hv2-4"
    ):
        runner.parse_cell("hv2-5-g1-r10")


@pytest.mark.parametrize("seed_index", [0, 1, 2, 3, 4])
def test_development_mode_refuses_every_heldout_seed(runner, seed_index):
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


def test_owner_release_gate_requires_the_minted_token(runner):
    """Token minted (2026-08-01): registered still refuses without the
    token, refuses a wrong token, and never stores the token value —
    only its SHA-256 is frozen in the runner."""

    with pytest.raises(runner.Refusal, match="ONE remaining gate") as info:
        runner.enforce_owner_release("registered", None)
    assert "owner-release-token" in str(info.value)

    minted = runner.OWNER_RELEASE_TOKEN_SHA256
    assert isinstance(minted, str)
    assert len(minted) == 64
    assert set(minted) <= set("0123456789abcdef")
    with pytest.raises(runner.Refusal, match="does not match"):
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
    """Amendment 1 item 4 read over all 15 cells (amendment 3 item 2)."""

    verdicts = [runner.VERDICT_BELOW_MARGIN] * 15
    row = runner.adjudicate_margin_outcome(verdicts)
    assert row["fired"] is True
    assert row["outcome"] == runner.VERDICT_CAPABILITY_MISS
    assert row["confirmatory_claim_dies"] is True
    assert row["evidence_of_witness_absence"] is False
    assert "MEASURED err_cell" in row["revisit_requires"]


def test_mixed_margin_table_does_not_fire(runner):
    verdicts = [runner.VERDICT_BELOW_MARGIN] * 14 + [runner.VERDICT_WITNESS]
    row = runner.adjudicate_margin_outcome(verdicts)
    assert row["fired"] is False
    assert "outcome" not in row


def test_incomplete_frame_does_not_fire_the_strict_rule(runner):
    # Neither a two-cell fragment nor the SUPERSEDED six-cell frame is a
    # complete fifteen-cell table.
    for count in (2, 6):
        verdicts = [runner.VERDICT_BELOW_MARGIN] * count
        row = runner.adjudicate_margin_outcome(verdicts)
        assert row["fired"] is False


def test_majority_verdict_boundaries_at_fifteen(runner):
    """Amendment 3 item 2 boundary counts: 10/15 confirms, 9/15 is
    strictly-between, 5/15 is a plain miss, and the superseded six-cell
    total is an incomplete frame."""

    assert runner.CELL_COUNT == 15
    assert runner.MAJORITY_MIN == 10
    assert runner.MINORITY_MAX == 5
    assert runner._majority_verdict(15, 15) == "CONFIRMED"
    assert runner._majority_verdict(10, 15) == "CONFIRMED"
    assert runner._majority_verdict(9, 15) == (
        "NOT_CONFIRMED_MISS_STRICTLY_BETWEEN"
    )
    assert runner._majority_verdict(6, 15) == (
        "NOT_CONFIRMED_MISS_STRICTLY_BETWEEN"
    )
    assert runner._majority_verdict(5, 15) == "NOT_CONFIRMED_MISS"
    assert runner._majority_verdict(0, 15) == "NOT_CONFIRMED_MISS"
    assert runner._majority_verdict(4, 6) == "INCOMPLETE_FRAME"


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


def test_p2_strictly_between_scores_not_confirmed(runner):
    """Amendment 3 item 2 on the thin-only minority mapping: <= 5/15
    positives is a minority PASS; 6/15 positives (complement 9/15) is in
    the strictly-between zone and scores NOT-CONFIRMED."""

    def rows(positive_count, total=15):
        return [
            {"blp": {"positive_above_guard": index < positive_count}}
            for index in range(total)
        ]

    # Boundary count 6: thin-only positives 6 -> complement 9 -> strictly
    # between 5 and 10 -> NOT-CONFIRMED.
    verdict = runner.adjudicate_p2(rows(10), rows(0), rows(6))
    assert verdict["sub_claims"]["thin_only_witness_minority"] == (
        "NOT_CONFIRMED_MISS_STRICTLY_BETWEEN"
    )
    assert verdict["verdict"] == "NOT_CONFIRMED_MISS"

    # Boundary count 5: thin-only positives 5 -> complement 10 -> a
    # minority PASS; with X8 at exactly 10/15 the claim confirms.
    confirmed = runner.adjudicate_p2(rows(10), rows(0), rows(5))
    assert confirmed["sub_claims"]["thin_only_witness_minority"] == (
        "CONFIRMED"
    )
    assert confirmed["verdict"] == "CONFIRMED"

    # Boundary count 9: X8 at 9/15 is strictly between and cannot confirm.
    between = runner.adjudicate_p2(rows(9), rows(0), rows(0))
    assert between["sub_claims"]["x8_witness_majority"] == (
        "NOT_CONFIRMED_MISS_STRICTLY_BETWEEN"
    )
    assert between["verdict"] == "NOT_CONFIRMED_MISS"

    killed = runner.adjudicate_p2(rows(10), rows(0), rows(10))
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


# ------------------------------------------------------- amendment 3 gates


def test_untruncated_band_is_1e_12(runner):
    """Amendment 3 item 4: the untruncated F=1 band is 1e-12 (was 1e-10);
    misses for numerically justified reasons are dated-erratum findings,
    never silent widenings of this constant."""

    assert runner.UNTRUNCATED_ONE_MINUS_F_MAX == 1.0e-12


def test_untruncated_control_vehicle_is_w3_v1_native(runner):
    """Amendment 4 item 1: the untruncated F=1 control is re-vehicled to
    the v1-native w3 coordinates -- exactly the committed plain-engine
    tests' engineering fixture (the ``_fixture`` helper defaults in
    tests/test_external_plain_quimb_finite_memory_engine.py) -- and the
    builder refuses degenerate or v2-heldout-colliding vehicles."""

    assert runner.UNTRUNCATED_VEHICLE == "w3_v1_native_per_amendment_4"
    assert runner.UNTRUNCATED_VEHICLE_COORDINATES == {
        "run_partition": "HELDOUT",  # the v1 emitter's partition label;
        # the v1 line is CLOSED and this is the committed tests' w3
        # engineering fixture, NOT a v2 heldout build
        "width": 3,
        "rounds": 2,
        "axis_family": 3,
        "p_event_numerator": 2,
        "gamma_index": 0,
    }
    assert runner.UNTRUNCATED_VEHICLE_INPUT_ID == 1

    fixture, fixture_hash = runner.build_untruncated_vehicle_fixture()
    emitter = runner._load_sibling("emit_gcapeps_finite_memory_fixture")
    # v1-native: the v1 schema, the v1 emitter's own frozen seed, and a
    # projection hash the v1 validator reproduces.
    assert fixture["schema"].endswith("gcapeps_finite_memory.fixture.v1")
    assert fixture["parameters"]["width"] == 3
    assert fixture["parameters"]["seed"] == emitter.HELDOUT_SEED
    assert emitter.validate_fixture(fixture) == fixture_hash
    # anti-build guard: the vehicle seed is NOT a v2 heldout stream seed
    assert fixture["parameters"]["seed"] not in runner.V2_HELDOUT_SEEDS
    # the fidelity gate reads every-round checkpoints
    rounds = fixture["parameters"]["rounds"]
    assert sorted(fixture["checkpoints"]) == list(range(rounds + 1))
    # non-degenerate: the vehicle exercises rotations AND entangling CX
    ledger = fixture["carrier_path"]["round_ledger"]
    assert sum(len(r["collision_rotations"]) for r in ledger) > 0
    assert any(
        op.get("gate_kind") == "CX"
        for row in ledger
        for op in row["operations"]
    )


def test_control_child_timeout_constant_is_frozen(runner):
    """Amendment 4 item 2: the control-child wall-clock budget is a
    frozen constant; changing it is an amendment, not a tweak."""

    assert runner.CONTROL_CHILD_TIMEOUT_SECONDS == 600


def test_control_child_timeout_guard_refuses_with_elapsed_evidence(
    runner, monkeypatch
):
    """Amendment 4 item 2: a control child that exceeds its wall-clock
    budget is killed process-group-clean and the run REFUSES with the
    measured elapsed time in the message -- it never hangs."""

    monkeypatch.setattr(runner, "CONTROL_CHILD_TIMEOUT_SECONDS", 0.5)
    sleeping_child = [
        sys.executable,
        "-c",
        "import time; time.sleep(600)",
    ]
    import time as _time

    started = _time.monotonic()
    with pytest.raises(runner.Refusal) as excinfo:
        runner._run_control_child(sleeping_child, label="unit-test")
    wall = _time.monotonic() - started
    message = str(excinfo.value)
    assert "amendment 4 item 2" in message
    assert "wall-clock budget of 0.5s" in message
    assert "process-group-clean" in message
    # measured elapsed evidence rides in the refusal message
    elapsed_match = re.search(r"measured\s+elapsed\s+([0-9.]+)s", message)
    assert elapsed_match is not None
    assert float(elapsed_match.group(1)) >= 0.5
    # never hangs: the guard returned promptly, not after the child's
    # 600-second sleep
    assert wall < 30.0


def test_run_control_child_passes_through_a_fast_child(runner):
    """The guard is transparent for a child that finishes in budget."""

    completed = runner._run_control_child(
        [sys.executable, "-c", "print('ok-child')"],
        label="unit-test",
    )
    assert completed.returncode == 0
    assert "ok-child" in completed.stdout


def test_engineered_fixture_claim_sentence_is_frozen(runner):
    """Amendment 3 item 5: the payload claim_boundary carries this exact
    sentence (presence in a real payload is asserted by the dry run)."""

    assert runner.ENGINEERED_FIXTURE_CLAIM_SENTENCE == (
        "engineered-schedule witness-positive test article; no "
        "generic-noise or naturally-occurring-non-Markovianity inference "
        "may ride on any v2 result; v2 results certify instrument "
        "capability only."
    )


def test_child_thread_envelope_refusal(runner):
    """Amendment 3 item 3: the parent refuses any child payload whose
    thread envelope is not exactly 1."""

    runner.check_child_thread_envelope(
        {"cell_id": "s2-g2-r10", "thread_envelope": 1}
    )
    for bad in (2, 0, None, "1"):
        with pytest.raises(runner.Refusal, match="thread"):
            runner.check_child_thread_envelope(
                {"cell_id": "s2-g2-r10", "thread_envelope": bad}
            )


def test_resolve_jobs_is_bounded(runner):
    """Amendment 3 item 3: --jobs is bounded (default min(15, cores-2)),
    never exceeds the cell count, and refuses out-of-bound requests."""

    assert 1 <= runner.resolve_jobs(None, 15) <= 15
    assert runner.resolve_jobs(None, 1) == 1
    assert runner.resolve_jobs(3, 2) == 2
    assert runner.resolve_jobs(15, 15) == 15
    with pytest.raises(runner.Refusal, match="jobs"):
        runner.resolve_jobs(0, 15)
    with pytest.raises(runner.Refusal, match="bounded"):
        runner.resolve_jobs(16, 15)


def test_cell_child_refuses_plan_hash_mismatch(runner, tmp_path):
    """A cell child must refuse when the plan bytes do not hash to the
    parent-declared sha256 (immutable-plan verification)."""

    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "schema": runner.PLAN_SCHEMA,
                "mode": "development",
                "plain_lane": "off",
                "scratch_dir": str(tmp_path),
                "cells": [],
            }
        )
    )
    completed = _run_cli(
        [
            "--cell-child",
            "--mode",
            "development",
            "--cell",
            "s2-g2-r10",
            "--plain-lane",
            "off",
            "--plan",
            str(plan_path),
            "--plan-sha256",
            "0" * 64,
            "--child-output",
            str(tmp_path / "child.json"),
        ]
    )
    assert completed.returncode == 2
    assert "REFUSED" in completed.stdout
    assert "does not hash" in completed.stdout
    assert not (tmp_path / "child.json").exists()


def test_cell_child_is_not_an_owner_release_bypass(runner, tmp_path):
    """ABSOLUTE: a direct registered --cell-child invocation refuses at
    the owner-release gate before any heldout fixture could be built."""

    import hashlib as _hashlib

    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(
            {
                "schema": runner.PLAN_SCHEMA,
                "mode": "registered",
                "plain_lane": "subprocess",
                "scratch_dir": str(tmp_path),
                "cells": [],
            }
        )
    )
    plan_sha = _hashlib.sha256(plan_path.read_bytes()).hexdigest()
    completed = _run_cli(
        [
            "--cell-child",
            "--mode",
            "registered",
            "--cell",
            "hv2-0-g1-r10",
            "--plain-lane",
            "subprocess",
            "--plan",
            str(plan_path),
            "--plan-sha256",
            plan_sha,
            "--child-output",
            str(tmp_path / "child.json"),
        ]
    )
    assert completed.returncode == 2
    assert "REFUSED" in completed.stdout
    assert "OWNER-RELEASE GATE" in completed.stdout
    assert not (tmp_path / "child.json").exists()


def test_parallel_jobs_byte_identity_on_calibration_dev_set(
    runner, tmp_path
):
    """Amendment 3 item 3, serial-semantics proof: --jobs 1 and --jobs 3
    on a three-cell CALIBRATION development set produce byte-identical
    per-cell payloads, the immutable plan is written and hashed BEFORE
    any child launches, every child stamps thread envelope 1, and the
    parent is the one aggregation writer."""

    # r10 cells: the theta0 d_trajectory gate needs the full ten-round
    # window for the Clifford recurrence to appear on cells[0].
    cell_specs = ["s0-g1-r10", "s1-g2-r10", "s2-g3-r10"]
    payloads = {}
    child_bytes = {}
    for jobs in (1, 3):
        output = tmp_path / f"parallel_jobs{jobs}.json"
        arguments = ["--mode", "development"]
        for spec in cell_specs:
            arguments += ["--cell", spec]
        arguments += [
            "--plain-lane",
            "off",
            "--jobs",
            str(jobs),
            "--output",
            str(output),
        ]
        completed = _run_cli(arguments)
        assert completed.returncode == 0, (
            completed.stdout + completed.stderr
        )
        stdout = completed.stdout
        plan_at = stdout.index(
            "immutable plan written and hashed BEFORE any child launch"
        )
        first_launch_at = stdout.index("[parent] launched child")
        assert plan_at < first_launch_at  # plan strictly before any child

        payload = json.loads(output.read_text())
        topology = payload["execution_topology"]
        assert topology["jobs"] == jobs
        assert topology["plan_written_before_any_child_launch"] is True
        assert len(topology["children"]) == 3
        for child in topology["children"]:
            assert child["thread_envelope"] == 1
            assert child["returncode"] == 0
        assert "one writer" in topology["aggregation_writer"]
        payloads[jobs] = payload
        child_bytes[jobs] = {
            child["cell_id"]: Path(child["payload_path"]).read_bytes()
            for child in topology["children"]
        }
        # every fixture stayed CALIBRATION (absolute constraint)
        for cell_row in payload["cells"]:
            assert cell_row["cell"]["run_partition"] == "CALIBRATION"

    # The plan hash is identical across --jobs settings (the plan freezes
    # WHAT is computed; jobs changes wall clock only) ...
    assert payloads[1]["execution_topology"]["plan_sha256"] == (
        payloads[3]["execution_topology"]["plan_sha256"]
    )
    # ... and every per-cell payload is byte-identical.
    assert sorted(child_bytes[1]) == sorted(child_bytes[3]) == sorted(
        cell_specs
    )
    for cell_id in cell_specs:
        assert child_bytes[1][cell_id] == child_bytes[3][cell_id]
    sha_by_cell_1 = {
        child["cell_id"]: child["payload_sha256"]
        for child in payloads[1]["execution_topology"]["children"]
    }
    sha_by_cell_3 = {
        child["cell_id"]: child["payload_sha256"]
        for child in payloads[3]["execution_topology"]["children"]
    }
    assert sha_by_cell_1 == sha_by_cell_3
    # The aggregated records agree exactly as well.
    assert payloads[1]["cells"] == payloads[3]["cells"]
    assert payloads[1]["adjudication"] == payloads[3]["adjudication"]


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

    # amendment 3 item 5: the engineered-fixture sentence rides on the
    # payload claim boundary, verbatim
    assert runner.ENGINEERED_FIXTURE_CLAIM_SENTENCE in (
        payload["claim_boundary"]
    )

    # amendment 3 item 3: the parallel topology is recorded -- immutable
    # plan hashed before launch, fresh children with envelope 1, one
    # aggregation writer
    topology = payload["execution_topology"]
    assert topology["plan_written_before_any_child_launch"] is True
    assert len(topology["plan_sha256"]) == 64
    assert len(topology["children"]) == 1
    assert topology["children"][0]["thread_envelope"] == 1
    assert "one writer" in topology["aggregation_writer"]

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
    # amendment 4 item 1: the wired control names the w3 v1-native
    # vehicle even when NOT_RUN with the plain lane off
    assert controls["untruncated_f_equals_1"]["vehicle"] == (
        runner.UNTRUNCATED_VEHICLE
    )
    assert "amendment 4 item 1" in (
        controls["untruncated_f_equals_1"]["detail"]
    )
    # amendment 4 provisions ride on every payload
    provisions = payload["amendment_4_provisions"]
    assert runner.UNTRUNCATED_VEHICLE in provisions["item_1"]
    assert "resource-refusal" in provisions["item_2"]
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
