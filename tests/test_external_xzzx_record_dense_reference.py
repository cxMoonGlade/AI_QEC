"""Independent dense-instrument tests for the XZZX Record/PEPS bridge."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
from pathlib import Path
import subprocess

import numpy as np
import pytest
import stim


REPO = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO / "scripts" / "external_baselines"
EMITTER_PATH = SCRIPT_DIR / "emit_xzzx_record_peps_fixture.py"
DENSE_PATH = SCRIPT_DIR / "xzzx_record_dense_reference.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixture(distance: int):
    emitter = _load(EMITTER_PATH, f"xzzx_fixture_d{distance}_under_test")
    _circuit, fixture = emitter.emit_fixture(
        stim,
        distance=distance,
        rounds=2,
    )
    return emitter, fixture


def _exact_primary_summary(dense, emitter, fixture):
    """Build a complete exact-reference-shaped primary for dense seam tests."""

    run_spec = emitter.run_spec(fixture)
    fixture_sha256 = dense.validate_fixture(fixture)
    run_spec_sha256 = dense.validate_spec(run_spec, fixture)
    primary = dense.greedy_branch(
        fixture,
        branch_id="exact-selector-primary-test",
    )
    branch = {
        "schema": dense.BRANCH_SCHEMA,
        "fixture_sha256": fixture_sha256,
        "run_spec_sha256": run_spec_sha256,
        "branch_id": primary["branch_id"],
        "distance": 3,
        "rounds": 2,
        "outcomes": [
            {"column": column, "bit": int(bit)}
            for column, bit in enumerate(primary["raw_bits"])
        ],
    }
    branch_authority = {
        "schema": dense.BRANCH_AUTHORITY_SCHEMA,
        "role": "primary",
        "method": dense.PRIMARY_AUTHORITY_METHOD,
        "branch_sha256": dense.canonical_json_sha256(branch),
        "selector": run_spec["reference_branch"]["selector"],
    }
    summary = {
        "schema": dense.EXACT_REFERENCE_SCHEMA,
        "status": "completed",
        "method": "numpy_exact_data_projector",
        "fixture": {
            "schema": fixture["schema"],
            "canonical_sha256": fixture_sha256,
            "stim_circuit_sha256": fixture["stim_circuit_sha256"],
            "distance": 3,
            "rounds": 2,
        },
        "run_spec": {
            "schema": run_spec["schema"],
            "canonical_sha256": run_spec_sha256,
        },
        "checkpoint": dense.PRETERMINAL_CHECKPOINT,
        "branch": branch,
        "branch_authority": branch_authority,
        "probability_rows": [
            {
                "column": int(row["column"]),
                "qubit": int(row["qubit"]),
                "basis": str(row["basis"]),
                "reset": bool(row["reset"]),
                "bit": int(row["bit"]),
                "p0": float(row["p0"]),
                "p1": float(row["p1"]),
                "selected_probability": float(row["selected_probability"]),
            }
            for row in primary["probability_rows"]
        ],
        "record": {
            "detector_bits": list(primary["detector_bits"]),
            "observable_bits": list(primary["observable_bits"]),
            "absolute_xor_rows": True,
        },
        "state": {
            "source_kind": "complete_complex128_state_vector",
            "checkpoint": dense.PRETERMINAL_CHECKPOINT,
        },
        "input_provenance": {"test_fixture": True},
    }
    return run_spec, primary, summary


def test_single_two_qubit_and_reset_instruments_pin_axis_conventions() -> None:
    dense = _load(DENSE_PATH, "xzzx_dense_gates_under_test")
    zero = dense.zero_state(2)

    plus_zero = dense.apply_single_qubit_gate(zero, dense.H, 0)
    bell = dense.apply_two_qubit_gate(plus_zero, dense.CX, 0, 1)
    assert bell == pytest.approx(
        np.array([1, 0, 0, 1], dtype=np.complex128) / np.sqrt(2)
    )
    assert dense.measurement_probabilities(bell, 0) == pytest.approx((0.5, 0.5))

    reset, selected = dense.select_measurement(
        bell,
        qubit=0,
        outcome=1,
        reset=True,
    )
    assert selected == pytest.approx(0.5)
    assert reset == pytest.approx(np.array([0, 1, 0, 0], dtype=np.complex128))
    assert dense.measurement_probabilities(reset, 0) == pytest.approx((1.0, 0.0))

    x_readout_state = dense.apply_single_qubit_gate(
        dense.zero_state(1),
        dense.H,
        0,
    )
    rotated = dense.apply_single_qubit_gate(
        dense.zero_state(1),
        dense.ry(0.02),
        0,
    )
    assert dense.measurement_probabilities(x_readout_state, 0) == pytest.approx(
        (0.5, 0.5)
    )
    assert rotated == pytest.approx(
        np.array([np.cos(0.01), np.sin(0.01)], dtype=np.complex128)
    )


def test_reset_and_reset_x_are_explicit_and_reject_entangled_noninitial_use() -> None:
    dense = _load(DENSE_PATH, "xzzx_dense_reset_under_test")
    zero = dense.zero_state(2)
    assert dense.apply_reset(zero, qubit=1) == pytest.approx(zero)
    reset_x = dense.apply_single_qubit_gate(
        dense.apply_reset(zero, qubit=1),
        dense.H,
        1,
    )
    assert reset_x == pytest.approx(
        np.array([1, 1, 0, 0], dtype=np.complex128) / np.sqrt(2)
    )

    bell = dense.apply_two_qubit_gate(
        dense.apply_single_qubit_gate(zero, dense.H, 0),
        dense.CX,
        0,
        1,
    )
    with pytest.raises(ValueError, match="nonselective reset"):
        dense.apply_reset(bell, qubit=0)


def test_d2_exact_enumeration_retains_all_raw_and_folded_support() -> None:
    _emitter, fixture = _fixture(2)
    dense = _load(DENSE_PATH, "xzzx_dense_enumeration_under_test")

    law = dense.enumerate_tracer(fixture, intervention_angle=0.02)
    assert law["schema"] == dense.RESULT_SCHEMA
    assert law["raw_probabilities"].shape == (1024,)
    assert law["record_probabilities"].shape == (64,)
    assert law["raw_bit_order"] == "measurement_column_ascending_big_endian"
    assert law["record_bit_order"] == (
        "detector_row_ascending_then_observable_row_ascending_big_endian"
    )
    assert np.count_nonzero(law["raw_probabilities"] == 0.0) > 0
    assert law["raw_probabilities"].sum() == pytest.approx(1.0, abs=1e-12)
    assert law["record_probabilities"].sum() == pytest.approx(1.0, abs=1e-12)

    no_ry = dense.enumerate_tracer(fixture, intervention_angle=0.0)
    record_tv = dense.total_variation(
        law["record_probabilities"],
        no_ry["record_probabilities"],
    )
    assert record_tv > 1e-6
    summary = dense.tracer_summary(
        fixture,
        _emitter.enumeration_spec(fixture),
        law,
        no_ry,
    )
    assert len(summary["raw_law"]) == 1024
    assert len(summary["record_law"]) == 64
    assert len(summary["ry_zero_record_law"]) == 64
    assert summary["ry_record_total_variation"] == pytest.approx(record_tv)
    assert summary["ry_non_degeneracy_threshold"] == 1e-6
    assert summary["ry_non_degeneracy_pass"] is True


def test_absolute_record_fold_handles_ragged_rows_without_rectangular_coercion() -> None:
    _emitter, fixture = _fixture(2)
    dense = _load(DENSE_PATH, "xzzx_dense_fold_under_test")
    raw = (1, 0, 1, 1, 0, 1, 0, 1, 1, 0)

    detectors, observables = dense.fold_record(
        raw,
        fixture["detector_rows"],
        fixture["observable_rows"],
    )
    assert detectors == tuple(
        sum(raw[column] for column in row) % 2
        for row in fixture["detector_rows"]
    )
    assert observables == tuple(
        sum(raw[column] for column in row) % 2
        for row in fixture["observable_rows"]
    )

    rectangular_corruption = [row.copy() for row in fixture["detector_rows"]]
    rectangular_corruption[-1] = rectangular_corruption[-1][:2]
    corrupted, _ = dense.fold_record(
        raw,
        rectangular_corruption,
        fixture["observable_rows"],
    )
    assert corrupted != detectors


def test_d3_nonformal_greedy_control_and_frozen_alternate_are_deterministic() -> None:
    _emitter, fixture = _fixture(3)
    dense = _load(DENSE_PATH, "xzzx_dense_branches_under_test")

    primary = dense.greedy_branch(fixture, branch_id="test-primary")
    replay = dense.forced_branch(
        fixture,
        primary["raw_bits"],
        branch_id="test-primary-replay",
    )
    assert replay["raw_bits"] == primary["raw_bits"]
    assert replay["conditional_probabilities"] == pytest.approx(
        primary["conditional_probabilities"],
        abs=1e-14,
    )
    assert replay["preterminal_state"] == pytest.approx(
        primary["preterminal_state"],
        abs=1e-14,
    )
    assert primary["preterminal_state"].shape == (2**17,)
    assert np.vdot(
        primary["preterminal_state"],
        primary["preterminal_state"],
    ).real == pytest.approx(1.0, abs=1e-12)
    assert primary["checkpoint"] == (
        "after_round_1_ry_before_terminal_data_measurements"
    )

    alternate = dense.alternate_branch(fixture, primary["raw_bits"])
    assert alternate is not None
    second = dense.alternate_branch(fixture, primary["raw_bits"])
    assert second is not None
    assert alternate["raw_bits"] == second["raw_bits"]
    changed = [
        column
        for column, (left, right) in enumerate(
            zip(primary["raw_bits"], alternate["raw_bits"], strict=True)
        )
        if left != right
    ]
    assert changed
    first = changed[0]
    assert fixture["measurement_order"][first]["reset"] is True
    assert alternate["alternate_flip_column"] == first
    assert alternate["conditional_probabilities"][first] >= 1e-8
    assert alternate["preterminal_state"].shape == (2**17,)


def test_second_ry_is_applied_before_the_preterminal_checkpoint() -> None:
    _emitter, fixture = _fixture(2)
    dense = _load(DENSE_PATH, "xzzx_dense_second_ry_under_test")
    complete = dense.greedy_branch(
        fixture,
        branch_id="two-ry-control",
    )
    syndrome_columns = 2 * (fixture["distance"] ** 2 - 1)

    def same_syndrome_then_greedy_terminal(column, _row, probabilities):
        if column < syndrome_columns:
            return int(complete["raw_bits"][column])
        return 0 if probabilities[0] >= probabilities[1] else 1

    first_round_only = dense._execute(
        fixture,
        same_syndrome_then_greedy_terminal,
        branch_id="first-ry-only-corruption",
        intervention_angle=0.02,
        intervention_rounds=(0,),
    )
    assert complete["intervention_rounds_applied"] == (0, 1)
    assert first_round_only["intervention_rounds_applied"] == (0,)
    assert 1.0 - dense._fidelity(
        complete["preterminal_state"],
        first_round_only["preterminal_state"],
    ) > 1e-8


def test_forced_branch_rejects_zero_mass_bits_and_wrong_column_count() -> None:
    _emitter, fixture = _fixture(2)
    dense = _load(DENSE_PATH, "xzzx_dense_branch_rejection_under_test")
    with pytest.raises(ValueError, match="exactly 10"):
        dense.forced_branch(fixture, [0] * 9)

    law = dense.enumerate_tracer(fixture)
    zero_index = int(np.flatnonzero(law["raw_probabilities"] == 0.0)[0])
    zero_bits = tuple(int(bit) for bit in f"{zero_index:010b}")
    with pytest.raises(ValueError, match="zero-probability"):
        dense.forced_branch(fixture, zero_bits)


def test_dense_summary_binds_hashes_checkpoint_order_and_state_artifact(
    tmp_path: Path,
) -> None:
    emitter, fixture = _fixture(3)
    dense = _load(DENSE_PATH, "xzzx_dense_summary_under_test")
    run_spec, _source_branch, exact_summary = _exact_primary_summary(
        dense,
        emitter,
        fixture,
    )
    exact_path = tmp_path / "exact-primary.json"
    exact_raw = dense.canonical_json_bytes(exact_summary)
    exact_path.write_bytes(exact_raw)
    bits, neutral_branch, authority = dense.validate_exact_primary_summary(
        exact_summary,
        fixture=fixture,
        run_spec=run_spec,
    )
    branch = dense.forced_branch(
        fixture,
        bits,
        branch_id=neutral_branch["branch_id"],
    )
    reference_parent = {
        "path": str(exact_path.resolve()),
        "file_sha256": hashlib.sha256(exact_raw).hexdigest(),
        "summary_schema": dense.EXACT_REFERENCE_SCHEMA,
        "role": "primary",
        "branch_sha256": dense.canonical_json_sha256(neutral_branch),
        "branch_id": neutral_branch["branch_id"],
    }
    state_path = tmp_path / "state.npy"

    summary = dense.write_branch_artifacts(
        fixture=fixture,
        run_spec=run_spec,
        branch=branch,
        branch_authority=authority,
        reference_parent=reference_parent,
        state_path=state_path,
    )
    assert summary["schema"] == dense.RESULT_SCHEMA
    assert summary["fixture"]["canonical_sha256"] == (
        "3b2bf7d81f7241e0a3b6abb14c76474c362e696cf374c55e20e3d121946bbf3c"
    )
    assert summary["run_spec"]["canonical_sha256"] == (
        "7dfa0a8ef9620712e6ea190aeda651c681295f9841963ce77686640255cc22a9"
    )
    assert summary["checkpoint"] == branch["checkpoint"]
    assert summary["branch"] == neutral_branch
    assert set(summary["branch"]) == {
        "schema",
        "fixture_sha256",
        "run_spec_sha256",
        "branch_id",
        "distance",
        "rounds",
        "outcomes",
    }
    assert [row["column"] for row in summary["probability_rows"]] == list(range(25))
    assert summary["branch_authority"] == authority
    assert summary["reference_parent"] == reference_parent
    assert summary["state"]["dtype"] == "complex128"
    assert summary["state"]["shape"] == [2**17]
    assert summary["state"]["qubit_order"] == list(range(17))
    assert summary["state"]["state_scope"] == "all_active_qubits"
    assert summary["state"]["sha256"] == hashlib.sha256(
        state_path.read_bytes()
    ).hexdigest()
    assert np.load(state_path, allow_pickle=False) == pytest.approx(
        branch["preterminal_state"]
    )


def test_exact_primary_summary_authenticates_bits_authority_and_full_reference() -> None:
    emitter, fixture = _fixture(3)
    dense = _load(DENSE_PATH, "xzzx_dense_exact_primary_under_test")
    run_spec, primary, exact_summary = _exact_primary_summary(
        dense,
        emitter,
        fixture,
    )

    bits, neutral_branch, authority = dense.validate_exact_primary_summary(
        exact_summary,
        fixture=fixture,
        run_spec=run_spec,
    )
    assert bits == primary["raw_bits"]
    assert neutral_branch == exact_summary["branch"]
    assert authority == exact_summary["branch_authority"]

    corruptions = []
    branch_with_reference_data = copy.deepcopy(exact_summary)
    branch_with_reference_data["branch"]["probability_rows"] = []
    corruptions.append(branch_with_reference_data)

    wrong_selector = copy.deepcopy(exact_summary)
    wrong_selector["branch_authority"]["selector"]["seed"] += 1
    corruptions.append(wrong_selector)

    wrong_branch_hash = copy.deepcopy(exact_summary)
    wrong_branch_hash["branch_authority"]["branch_sha256"] = "0" * 64
    corruptions.append(wrong_branch_hash)

    wrong_selected_probability = copy.deepcopy(exact_summary)
    wrong_selected_probability["probability_rows"][0][
        "selected_probability"
    ] = 0.25
    corruptions.append(wrong_selected_probability)

    wrong_fold = copy.deepcopy(exact_summary)
    wrong_fold["record"]["detector_bits"][0] ^= 1
    corruptions.append(wrong_fold)

    for corrupted in corruptions:
        with pytest.raises(ValueError):
            dense.validate_exact_primary_summary(
                corrupted,
                fixture=fixture,
                run_spec=run_spec,
            )


def test_primary_artifact_rejects_parent_branch_id_substitution(
    tmp_path: Path,
) -> None:
    emitter, fixture = _fixture(3)
    dense = _load(DENSE_PATH, "xzzx_dense_primary_parent_under_test")
    run_spec, _primary, exact_summary = _exact_primary_summary(
        dense,
        emitter,
        fixture,
    )
    exact_path = tmp_path / "exact-primary.json"
    exact_raw = dense.canonical_json_bytes(exact_summary)
    exact_path.write_bytes(exact_raw)
    bits, neutral_branch, authority = dense.validate_exact_primary_summary(
        exact_summary,
        fixture=fixture,
        run_spec=run_spec,
    )
    branch = dense.forced_branch(
        fixture,
        bits,
        branch_id=neutral_branch["branch_id"],
    )
    substituted_parent = {
        "path": str(exact_path.resolve()),
        "file_sha256": hashlib.sha256(exact_raw).hexdigest(),
        "summary_schema": dense.EXACT_REFERENCE_SCHEMA,
        "role": "primary",
        "branch_sha256": dense.canonical_json_sha256(neutral_branch),
        "branch_id": "different-primary-with-the-same-bits",
    }

    with pytest.raises(ValueError, match="reference-parent authority"):
        dense.write_branch_artifacts(
            fixture=fixture,
            run_spec=run_spec,
            branch=branch,
            branch_authority=authority,
            reference_parent=substituted_parent,
            state_path=tmp_path / "must-not-exist.npy",
        )
    assert not (tmp_path / "must-not-exist.npy").exists()


def test_alternate_artifact_serializes_exact_parent_flip_and_rule_proof(
    tmp_path: Path,
) -> None:
    emitter, fixture = _fixture(3)
    dense = _load(DENSE_PATH, "xzzx_dense_alternate_authority_under_test")
    run_spec, _primary, exact_summary = _exact_primary_summary(
        dense,
        emitter,
        fixture,
    )
    exact_path = tmp_path / "exact-primary.json"
    exact_raw = dense.canonical_json_bytes(exact_summary)
    exact_path.write_bytes(exact_raw)
    primary_bits, parent_branch, _authority = (
        dense.validate_exact_primary_summary(
            exact_summary,
            fixture=fixture,
            run_spec=run_spec,
        )
    )
    alternate = dense.alternate_branch(
        fixture,
        primary_bits,
        branch_id="dense-frozen-alternate-test",
    )
    assert alternate is not None
    alternate_branch = {
        "schema": dense.BRANCH_SCHEMA,
        "fixture_sha256": dense.validate_fixture(fixture),
        "run_spec_sha256": dense.validate_spec(run_spec, fixture),
        "branch_id": alternate["branch_id"],
        "distance": 3,
        "rounds": 2,
        "outcomes": [
            {"column": column, "bit": int(bit)}
            for column, bit in enumerate(alternate["raw_bits"])
        ],
    }
    exact_file_sha256 = hashlib.sha256(exact_raw).hexdigest()
    authority = dense.alternate_branch_authority(
        branch=alternate_branch,
        parent_summary_file_sha256=exact_file_sha256,
        parent_branch=parent_branch,
        flip_column=int(alternate["alternate_flip_column"]),
    )
    reference_parent = {
        "path": str(exact_path.resolve()),
        "file_sha256": exact_file_sha256,
        "summary_schema": dense.EXACT_REFERENCE_SCHEMA,
        "role": "primary",
        "branch_sha256": dense.canonical_json_sha256(parent_branch),
        "branch_id": parent_branch["branch_id"],
    }
    summary = dense.write_branch_artifacts(
        fixture=fixture,
        run_spec=run_spec,
        branch=alternate,
        branch_authority=authority,
        reference_parent=reference_parent,
        state_path=tmp_path / "alternate.npy",
    )

    flip_column = int(alternate["alternate_flip_column"])
    assert set(summary["branch_authority"]) == {
        "schema",
        "role",
        "method",
        "branch_sha256",
        "parent",
        "flip_column",
    }
    assert summary["branch_authority"]["method"] == (
        dense.ALTERNATE_AUTHORITY_METHOD
    )
    assert summary["branch_authority"]["parent"] == {
        "summary_schema": dense.EXACT_REFERENCE_SCHEMA,
        "summary_file_sha256": exact_file_sha256,
        "branch_sha256": dense.canonical_json_sha256(parent_branch),
        "branch_id": parent_branch["branch_id"],
    }
    assert summary["branch_authority"]["flip_column"] == flip_column
    assert alternate["raw_bits"][:flip_column] == primary_bits[:flip_column]
    assert alternate["raw_bits"][flip_column] == 1 - primary_bits[flip_column]
    for row in alternate["probability_rows"][flip_column + 1 :]:
        assert row["bit"] == (0 if row["p0"] >= row["p1"] else 1)

    malformed_authority = copy.deepcopy(authority)
    malformed_authority["parent"]["unbound_field"] = "forbidden"
    with pytest.raises(ValueError, match="alternate authority"):
        dense.write_branch_artifacts(
            fixture=fixture,
            run_spec=run_spec,
            branch=alternate,
            branch_authority=malformed_authority,
            reference_parent=reference_parent,
            state_path=tmp_path / "malformed-must-not-exist.npy",
        )
    assert not (tmp_path / "malformed-must-not-exist.npy").exists()


def test_synthetic_corruptions_are_asymmetric_and_trip_independent_invariants() -> None:
    dense = _load(DENSE_PATH, "xzzx_dense_controls_under_test")
    controls = dense.synthetic_corruption_controls()

    assert controls["wrong_born_normalization"]["norm_error"] > 1e-8
    assert controls["projector_scaled_0p9"]["completeness_error"] > 1e-10
    assert controls["omitted_path_factor"]["log_mass_error"] > 1e-8
    assert controls["reversed_asymmetric_axes"]["identity_fidelity"] < 1 - 1e-8
    assert controls["reset_to_one"]["post_reset_one_weight"] > 1e-8


def test_dense_owned_physical_corruptions_are_all_nonvacuous() -> None:
    _emitter, fixture = _fixture(2)
    _emitter, d3_fixture = _fixture(3)
    dense = _load(DENSE_PATH, "xzzx_dense_physical_controls_under_test")
    controls = dense.physical_corruption_controls(fixture, d3_fixture)

    assert set(controls) == {
        "deleted_first_local_h_pair_tv",
        "swapped_first_nonsymmetric_cx_tv",
        "mr_without_reset_tv",
        "mr_without_reset_post_measurement_one_weight",
        "negative_ry_state_or_probability_difference",
        "ry_after_terminal_tv",
        "omitted_first_x_readout_h_tv",
        "ragged_record_row_corruption_probability",
    }
    assert all(value > 1e-8 for value in controls.values())
    assert controls["mr_without_reset_post_measurement_one_weight"] == pytest.approx(
        1.0,
        abs=1e-14,
    )


def test_dense_worker_has_no_quimb_or_qiskit_dependency() -> None:
    source = DENSE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    assert "import quimb" not in lowered
    assert "from quimb" not in lowered
    assert "import qiskit" not in lowered
    assert "from qiskit" not in lowered


def test_formal_cli_exposes_exact_primary_and_alternate_but_not_greedy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dense = _load(DENSE_PATH, "xzzx_dense_cli_modes_under_test")
    monkeypatch.setattr(
        dense.sys,
        "argv",
        [
            str(DENSE_PATH),
            "--fixture",
            "fixture.json",
            "--spec",
            "run-spec.json",
            "--mode",
            "greedy",
            "--output-json",
            "result.json",
        ],
    )
    with pytest.raises(SystemExit):
        dense._parse_args()


def test_formal_cli_provenance_binds_head_hashes_and_fails_on_dirty_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dense = _load(DENSE_PATH, "xzzx_dense_provenance_under_test")
    fixture_path = tmp_path / "fixture.json"
    spec_path = tmp_path / "spec.json"
    reference_path = tmp_path / "exact-reference-summary.json"
    fixture_path.write_text('{"fixture": 1}\n', encoding="utf-8")
    spec_path.write_text('{"spec": 2}\n', encoding="utf-8")
    reference_path.write_text('{"reference": 3}\n', encoding="utf-8")
    monkeypatch.setenv("CONDA_PREFIX", str(Path(dense.sys.prefix).resolve()))
    commands = []

    def clean_run(command, **_kwargs):
        commands.append(command)
        if command[1:3] == ["rev-parse", "HEAD"]:
            stdout = "a" * 40 + "\n"
        elif command[1:3] == ["rev-parse", "--is-shallow-repository"]:
            stdout = "false\n"
        elif command[1] == "show":
            relative_path = command[2].split(":", 1)[1]
            stdout = (REPO / relative_path).read_bytes()
        else:
            stdout = ""
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(dense.subprocess, "run", clean_run)
    provenance = dense.formal_input_provenance(
        fixture_path=fixture_path,
        spec_path=spec_path,
        reference_summary_path=reference_path,
    )
    assert provenance["git_head"] == "a" * 40
    assert provenance["required_paths_clean"] is True
    assert set(provenance["files_sha256"]) == set(dense.FORMAL_INPUT_PATHS)
    assert all(
        len(digest) == 64
        for digest in provenance["files_sha256"].values()
    )
    assert provenance["repository_is_shallow"] is False
    status_command = next(command for command in commands if command[1] == "status")
    assert "--untracked-files=all" in status_command
    assert "--ignored=matching" in status_command
    assert provenance["runtime"]["python_executable"] == str(
        Path(dense.sys.executable).resolve()
    )
    assert provenance["runtime"]["python_version"]
    assert provenance["runtime"]["numpy_version"] == np.__version__
    assert provenance["runtime"]["conda_prefix"] == str(
        Path(dense.sys.prefix).resolve()
    )
    assert provenance["runtime"]["core_environment_lock"]["path"] == str(
        (REPO / "core-environment-cu130.lock").resolve()
    )
    assert len(
        provenance["runtime"]["core_environment_lock"]["file_sha256"]
    ) == 64
    assert provenance["input_files"] == {
        "reference_summary": {
            "path": str(reference_path.resolve()),
            "file_sha256": hashlib.sha256(
                reference_path.read_bytes()
            ).hexdigest(),
        },
        "fixture": {
            "path": str(fixture_path.resolve()),
            "file_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
        },
        "spec": {
            "path": str(spec_path.resolve()),
            "file_sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest(),
        },
    }

    def committed_mismatch_run(command, **_kwargs):
        if command[1:3] == ["rev-parse", "HEAD"]:
            stdout = "a" * 40 + "\n"
        elif command[1:3] == ["rev-parse", "--is-shallow-repository"]:
            stdout = "false\n"
        elif command[1] == "show":
            stdout = b"not-the-working-file"
        else:
            stdout = ""
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(dense.subprocess, "run", committed_mismatch_run)
    with pytest.raises(RuntimeError, match="differs from committed HEAD"):
        dense.formal_input_provenance(
            fixture_path=fixture_path,
            spec_path=spec_path,
            reference_summary_path=reference_path,
        )

    def dirty_run(command, **_kwargs):
        if command[1:3] == ["rev-parse", "HEAD"]:
            stdout = "a" * 40 + "\n"
        elif command[1:3] == ["rev-parse", "--is-shallow-repository"]:
            stdout = "false\n"
        else:
            stdout = "?? scripts/external_baselines/xzzx_record_dense_reference.py\n"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(dense.subprocess, "run", dirty_run)
    with pytest.raises(RuntimeError, match="committed byte-clean inputs"):
        dense.formal_input_provenance(
            fixture_path=fixture_path,
            spec_path=spec_path,
            reference_summary_path=reference_path,
        )

    def ignored_run(command, **_kwargs):
        if command[1:3] == ["rev-parse", "HEAD"]:
            stdout = "a" * 40 + "\n"
        elif command[1:3] == ["rev-parse", "--is-shallow-repository"]:
            stdout = "false\n"
        else:
            stdout = "!! tests/test_external_xzzx_record_dense_reference.py\n"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(dense.subprocess, "run", ignored_run)
    with pytest.raises(RuntimeError, match="committed byte-clean inputs"):
        dense.formal_input_provenance(
            fixture_path=fixture_path,
            spec_path=spec_path,
            reference_summary_path=reference_path,
        )

    def shallow_run(command, **_kwargs):
        if command[1:3] == ["rev-parse", "HEAD"]:
            stdout = "a" * 40 + "\n"
        elif command[1:3] == ["rev-parse", "--is-shallow-repository"]:
            stdout = "true\n"
        else:
            stdout = ""
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(dense.subprocess, "run", shallow_run)
    with pytest.raises(RuntimeError, match="shallow"):
        dense.formal_input_provenance(
            fixture_path=fixture_path,
            spec_path=spec_path,
            reference_summary_path=reference_path,
        )


def test_dense_output_preflight_and_atomic_writes_refuse_aliases_and_existing_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dense = _load(DENSE_PATH, "xzzx_dense_outputs_under_test")
    summary_path = tmp_path / "summary.json"
    state_path = tmp_path / "state.npy"

    assert dense.preflight_output_paths(
        (summary_path, state_path)
    ) == (summary_path.resolve(), state_path.resolve())
    with pytest.raises(ValueError, match="pairwise distinct"):
        dense.preflight_output_paths(
            (summary_path, tmp_path / "." / "summary.json")
        )

    summary_path.write_bytes(b"immutable")
    with pytest.raises(FileExistsError, match="refusing to replace"):
        dense.preflight_output_paths((summary_path, state_path))
    with pytest.raises(FileExistsError):
        dense._atomic_write(summary_path, b"replacement")
    assert summary_path.read_bytes() == b"immutable"

    state_path.write_bytes(b"existing-state")
    with pytest.raises(FileExistsError):
        dense._atomic_save_npy(
            state_path,
            np.asarray([1.0, 0.0], dtype=np.complex128),
        )
    assert state_path.read_bytes() == b"existing-state"

    with pytest.raises(FileNotFoundError, match="parent directory"):
        dense.preflight_output_paths((tmp_path / "missing" / "summary.json",))

    raced_path = tmp_path / "raced.json"
    original_link = dense.os.link

    def publish_after_racer(source, destination):
        Path(destination).write_bytes(b"racer-won")
        return original_link(source, destination)

    monkeypatch.setattr(dense.os, "link", publish_after_racer)
    with pytest.raises(FileExistsError, match="refusing to replace"):
        dense._atomic_write(raced_path, b"late-writer")
    assert raced_path.read_bytes() == b"racer-won"
