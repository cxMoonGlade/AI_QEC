"""Exact data-projector reference controls for the XZZX PEPS experiment."""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import stim


REPO = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO / "scripts" / "external_baselines"
EMITTER_PATH = SCRIPT_DIR / "emit_xzzx_record_peps_fixture.py"
EXACT_PATH = SCRIPT_DIR / "xzzx_record_exact_data_reference.py"
DENSE_PATH = SCRIPT_DIR / "xzzx_record_dense_reference.py"
COMPARATOR_PATH = SCRIPT_DIR / "compare_xzzx_record_peps.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixture(distance: int):
    emitter = _load(EMITTER_PATH, f"xzzx_exact_emitter_d{distance}")
    _circuit, fixture = emitter.emit_fixture(
        stim,
        distance=distance,
        rounds=2,
    )
    return emitter, fixture


def test_neutral_ledger_derives_signed_commuting_equal_round_checks() -> None:
    exact = _load(EXACT_PATH, "xzzx_exact_check_parser")
    _emitter, fixture = _fixture(3)

    ledger = exact.derive_projector_ledger(fixture)

    assert ledger["schema"] == exact.LEDGER_SCHEMA
    assert ledger["data_order"] == fixture["frame"]["data_qubits"]
    assert len(ledger["rounds"]) == 2
    assert ledger["rounds"][0] == ledger["rounds"][1]
    assert len(ledger["rounds"][0]) == 8
    assert all(row["sign"] == 1 for row in ledger["rounds"][0])
    assert all(row["support"] == sorted(row["support"]) for row in ledger["rounds"][0])
    assert exact.validate_commuting_checks(ledger["rounds"][0]) is None

    mixed = copy.deepcopy(fixture)
    first_ancilla = mixed["measurement_order"][0]["qubit"]
    first_link = next(
        row
        for row in mixed["operations"]
        if row["op"] == "CX" and first_ancilla in row["qubits"]
    )
    first_link["qubits"].reverse()
    with pytest.raises(ValueError, match="mixed CX orientation"):
        exact.derive_projector_ledger(mixed)


def test_projected_vector_norms_preserve_tiny_positive_probability() -> None:
    exact = _load(EXACT_PATH, "xzzx_exact_projector")
    tiny = 1e-28
    state = np.asarray(
        [math.sqrt(1.0 - tiny), math.sqrt(tiny)],
        dtype=np.complex128,
    )

    p0, p1, plus, minus = exact.projector_probabilities(
        state,
        support=[[0, "Z"]],
        data_order=[0],
        sign=1,
    )

    assert p0 == pytest.approx(float(np.vdot(plus, plus).real))
    assert p1 == pytest.approx(float(np.vdot(minus, minus).real))
    assert p1 > 0.0
    assert p1 == pytest.approx(tiny, rel=1e-14)
    selected, probabilities = exact.select_projector(
        state,
        1,
        support=[[0, "Z"]],
        data_order=[0],
        sign=1,
    )
    assert probabilities == pytest.approx((p0, p1))
    assert selected == pytest.approx(np.asarray([0.0, 1.0], np.complex128))
    with pytest.raises(exact.SelectedBranchUnavailable, match="below 1e-12"):
        exact.select_projector(
            state,
            1,
            support=[[0, "Z"]],
            data_order=[0],
            sign=1,
            minimum_probability=1e-12,
        )


def test_projector_uses_pair_probability_but_raw_weight_poststate_norm() -> None:
    exact = _load(EXACT_PATH, "xzzx_exact_projector_pair_normalization")
    state = np.asarray([2.0, 1.0], dtype=np.complex128)

    p0, p1, _plus, _minus = exact.projector_probabilities(
        state,
        support=[[0, "Z"]],
        data_order=[0],
        sign=1,
    )
    selected, probabilities = exact.select_projector(
        state,
        0,
        support=[[0, "Z"]],
        data_order=[0],
        sign=1,
    )

    assert probabilities == pytest.approx((0.8, 0.2))
    assert (p0, p1) == pytest.approx((0.8, 0.2))
    assert selected == pytest.approx(
        np.asarray([1.0, 0.0], dtype=np.complex128)
    )
    assert float(np.vdot(selected, selected).real) == pytest.approx(1.0)


def test_d3_primary_emits_only_valid_bernoulli_rows() -> None:
    exact = _load(EXACT_PATH, "xzzx_exact_primary_probability_domain")
    emitter, fixture = _fixture(3)
    execution = exact.execute_primary_branch(
        fixture,
        emitter.run_spec(fixture),
    )

    assert len(execution["probability_rows"]) == fixture["num_measurements"]
    for row in execution["probability_rows"]:
        assert 0.0 <= row["p0"] <= 1.0
        assert 0.0 <= row["p1"] <= 1.0
        assert row["p0"] + row["p1"] == pytest.approx(1.0, abs=1e-12)
        assert row["selected_probability"] == (row["p0"], row["p1"])[
            row["bit"]
        ]


def test_d3_primary_exact_dense_comparator_seam(tmp_path: Path) -> None:
    exact = _load(EXACT_PATH, "xzzx_exact_primary_comparator_seam")
    dense = _load(DENSE_PATH, "xzzx_dense_primary_comparator_seam")
    comparator = _load(COMPARATOR_PATH, "xzzx_primary_comparator_seam")
    emitter, fixture = _fixture(3)
    run_spec = emitter.run_spec(fixture)
    execution = exact.execute_primary_branch(fixture, run_spec)
    branch = exact.neutral_branch(fixture, run_spec, execution)
    authority = exact.primary_branch_authority(branch, run_spec)
    exact_summary_path = tmp_path / "exact.json"
    exact_state_path = tmp_path / "exact.npy"
    exact_summary = exact.write_reference_artifacts(
        fixture=fixture,
        run_spec=run_spec,
        execution=execution,
        branch_authority=authority,
        input_provenance={"test_control": True},
        resource_usage={"wall_seconds": 0.0, "peak_host_rss_kib": 0},
        summary_path=exact_summary_path,
        state_path=exact_state_path,
    )
    bits, neutral, authenticated_authority = (
        dense.validate_exact_primary_summary(
            exact_summary,
            fixture=fixture,
            run_spec=run_spec,
        )
    )
    dense_execution = dense.forced_branch(
        fixture,
        bits,
        branch_id=neutral["branch_id"],
    )
    dense_summary = dense.write_branch_artifacts(
        fixture=fixture,
        run_spec=run_spec,
        branch=dense_execution,
        branch_authority=authenticated_authority,
        reference_parent={
            "path": str(exact_summary_path.resolve()),
            "file_sha256": hashlib.sha256(
                exact_summary_path.read_bytes()
            ).hexdigest(),
            "summary_schema": exact_summary["schema"],
            "role": "primary",
            "branch_sha256": authority["branch_sha256"],
            "branch_id": branch["branch_id"],
        },
        state_path=tmp_path / "dense.npy",
    )

    comparison = comparator.compare_d3_exact_and_full_dense(
        exact_summary,
        dense_summary,
    )
    assert comparison["passes"] is True
    assert 1.0 - comparison["fidelity"] <= 1e-12
    assert comparison["max_probability_error"] <= 1e-12
    assert comparison["log_branch_mass_error"] <= 1e-9


def test_sha256_prefix_born_selector_has_frozen_bytes_and_exact_boundary() -> None:
    exact = _load(EXACT_PATH, "xzzx_exact_selector")

    assert exact.selector_digest(seed=0, column=0, prefix=[]).hex() == (
        "46f0b86e440c4140cf5161df395d04b9ad360c609b6164cab2be4113a69cb953"
    )
    assert exact.selector_digest(
        seed=2026072603,
        column=3,
        prefix=[0, 1, 1],
    ).hex() == (
        "4a7888f8e16e713c297ae41dac024da22b4e293f624b9dd875327e8deabc273d"
    )
    half = 1 << 255
    assert exact.born_bit_from_hash_integer(0.5, half - 1) == 0
    assert exact.born_bit_from_hash_integer(0.5, half) == 1
    assert exact.sha256_prefix_born_bit(
        0.5,
        seed=0,
        column=0,
        prefix=[],
    ) == exact.born_bit_from_hash_integer(
        0.5,
        int.from_bytes(
            bytes.fromhex(
                "46f0b86e440c4140cf5161df395d04b9ad360c609b6164cab2be4113a69cb953"
            ),
            "big",
        ),
    )
    with pytest.raises(ValueError, match="prefix length"):
        exact.selector_digest(seed=0, column=1, prefix=[])
    with pytest.raises(ValueError, match="binary64 probability"):
        exact.born_bit_from_hash_integer(-1e-30, 0)
    with pytest.raises(ValueError, match="binary64 probability"):
        exact.born_bit_from_hash_integer(
            math.nextafter(1.0, math.inf),
            (1 << 256) - 1,
        )


def test_fixed_d2_d3_branches_match_full_dense_probabilities_and_checkpoint() -> None:
    exact = _load(EXACT_PATH, "xzzx_exact_fixed_controls")
    dense = _load(DENSE_PATH, "xzzx_dense_for_exact_controls")
    controls = {
        2: [
            "0000000000",
            "0001100100",
            "1001000000",
            "1011011111",
        ],
        3: [
            "0000000000000000011101101",
            "1000000010000000000000000",
            "0010010000100100110110101",
            "0010000000100000101101101",
            "1000000110000001011011000",
        ],
    }

    for distance, bitstrings in controls.items():
        _emitter, fixture = _fixture(distance)
        for branch_index, bitstring in enumerate(bitstrings):
            bits = [int(bit) for bit in bitstring]
            projected = exact.execute_forced_branch(
                fixture,
                bits,
                branch_id=f"d{distance}-fixed-{branch_index}",
            )
            complete = dense.forced_branch(
                fixture,
                bits,
                branch_id=f"d{distance}-fixed-{branch_index}",
            )
            assert len(projected["probability_rows"]) == len(
                complete["probability_rows"]
            )
            for left, right in zip(
                projected["probability_rows"],
                complete["probability_rows"],
                strict=True,
            ):
                assert left["p0"] == pytest.approx(right["p0"], abs=1e-12)
                assert left["p1"] == pytest.approx(right["p1"], abs=1e-12)
                assert left["selected_probability"] == pytest.approx(
                    right["selected_probability"],
                    abs=1e-12,
                )
            embedded = exact.embed_data_state(
                projected["preterminal_data_state"],
                data_order=fixture["frame"]["data_qubits"],
                num_qubits=fixture["num_qubits"],
            )
            fidelity = exact.phase_invariant_fidelity(
                embedded,
                complete["preterminal_state"],
            )
            assert 1.0 - fidelity <= 1e-12
            assert projected["log_branch_mass"] == pytest.approx(
                complete["log_branch_mass"],
                abs=1e-9,
            )


def test_alternate_rule_matches_dense_and_records_first_mr_flip() -> None:
    exact = _load(EXACT_PATH, "xzzx_exact_alternate")
    dense = _load(DENSE_PATH, "xzzx_dense_alternate_control")
    _emitter, fixture = _fixture(3)
    primary = [int(bit) for bit in "0000000000000000011101101"]

    projected = exact.execute_alternate_branch(
        fixture,
        primary,
        branch_id="fixed-alternate-control",
    )
    complete = dense.forced_branch(
        fixture,
        projected["raw_bits"],
        branch_id="fixed-alternate-control",
    )

    assert projected["raw_bits"] == complete["raw_bits"]
    flip = projected["alternate_flip_column"]
    assert fixture["measurement_order"][flip]["reset"] is True
    assert projected["conditional_probabilities"][flip] >= 1e-8
    for left, right in zip(
        projected["probability_rows"],
        complete["probability_rows"],
        strict=True,
    ):
        assert left["p0"] == pytest.approx(right["p0"], abs=1e-12)
        assert left["p1"] == pytest.approx(right["p1"], abs=1e-12)


def test_axis_embedding_is_q0_msb_exact_and_mass_underflow_stays_explicit() -> None:
    exact = _load(EXACT_PATH, "xzzx_exact_axis_underflow")
    data = np.asarray([1.0, 2.0j, 3.0 + 4.0j, 5.0], dtype=np.complex128)

    embedded = exact.embed_data_state(
        data,
        data_order=[0, 2],
        num_qubits=3,
    )
    expected = np.zeros(8, dtype=np.complex128)
    expected[[0, 1, 4, 5]] = data
    assert np.array_equal(embedded, expected)
    assert np.array_equal(
        exact.project_all_active_to_data(
            embedded,
            data_order=[0, 2],
            num_qubits=3,
        ),
        data,
    )
    reversed_axes = data.reshape(2, 2).transpose().reshape(-1)
    assert exact.phase_invariant_fidelity(data, reversed_axes) < 1.0 - 1e-8

    mass = exact.stable_positive_branch_mass([1e-200, 1e-200])
    assert mass == {
        "branch_mass": None,
        "log_branch_mass": pytest.approx(2.0 * math.log(1e-200)),
        "branch_mass_representable": False,
        "positive_mass_underflowed_to_zero": True,
    }


@pytest.mark.parametrize("distance", [2, 3])
def test_stim_independently_verifies_parser_signs_and_shell_tableaus(
    distance: int,
) -> None:
    exact = _load(EXACT_PATH, f"xzzx_exact_stim_verify_d{distance}")
    _emitter, fixture = _fixture(distance)
    ledger = exact.derive_projector_ledger(fixture)
    data = set(ledger["data_order"])
    frame = set(fixture["frame"]["hadamard_frame_data_qubits"])
    ancillas = set(range(fixture["num_qubits"])) - data
    syndrome_count = distance * distance - 1
    actual_rounds = [stim.Circuit(), stim.Circuit()]
    links = {ancilla: [] for ancilla in ancillas}
    measured = 0
    round_index = 0
    first_measurement_order = []

    for operation in fixture["operations"]:
        name = operation["op"]
        qubits = operation["qubits"]
        if name == "MR":
            if round_index == 0:
                first_measurement_order.append(qubits[0])
            measured += 1
            if measured == syndrome_count:
                round_index += 1
                measured = 0
            continue
        if round_index >= 2 or name in {"M", "MX"}:
            break
        if name in {"H", "CX"}:
            actual_rounds[round_index].append(name, qubits)
            if round_index == 0 and name == "CX":
                control, target = qubits
                ancilla = control if control in ancillas else target
                links[ancilla].append((control, target))
        elif name not in {"R", "RX"}:
            raise AssertionError(f"unexpected test fixture operation {name}")

    assert stim.Tableau.from_circuit(actual_rounds[0]) == stim.Tableau.from_circuit(
        actual_rounds[1]
    )
    inverse = stim.Tableau.from_circuit(actual_rounds[0]).inverse()
    for ancilla, check in zip(
        first_measurement_order,
        ledger["rounds"][0],
        strict=True,
    ):
        observable = inverse.z_output(ancilla)
        assert observable.sign == 1
        assert observable[ancilla] == 3
        assert all(
            observable[other] == (3 if other == ancilla else 0)
            for other in ancillas
        )
        expected = {qubit: pauli for qubit, pauli in check["support"]}
        assert all(
            observable[qubit] == {"X": 1, "Z": 3}.get(expected.get(qubit), 0)
            for qubit in data
        )

    grouped = stim.Circuit()
    for check in ledger["rounds"][0]:
        ancilla = check["ancilla"]
        base_x = links[ancilla][0][0] == ancilla
        if base_x:
            grouped.append("H", [ancilla])
        for control, target in links[ancilla]:
            data_qubit = target if control == ancilla else control
            if data_qubit in frame:
                grouped.append("H", [data_qubit])
            grouped.append("CX", [control, target])
            if data_qubit in frame:
                grouped.append("H", [data_qubit])
        if base_x:
            grouped.append("H", [ancilla])
    assert stim.Tableau.from_circuit(actual_rounds[0]) == stim.Tableau.from_circuit(
        grouped
    )


def test_parser_sign_commutator_and_operation_corruptions_fail_closed() -> None:
    exact = _load(EXACT_PATH, "xzzx_exact_parser_corruptions")
    _emitter, fixture = _fixture(3)
    ledger = exact.derive_projector_ledger(fixture)

    wrong_sign = copy.deepcopy(ledger["rounds"][0])
    wrong_sign[0]["sign"] = -1
    with pytest.raises(ValueError, match="sign"):
        exact.validate_commuting_checks(wrong_sign)
    with pytest.raises(ValueError, match="do not commute"):
        exact.validate_commuting_checks(
            [
                {"sign": 1, "support": [[0, "X"]]},
                {"sign": 1, "support": [[0, "Z"]]},
            ]
        )

    duplicate = copy.deepcopy(fixture)
    first_cx_index = next(
        index
        for index, operation in enumerate(duplicate["operations"])
        if operation["op"] == "CX"
    )
    duplicate["operations"].insert(
        first_cx_index + 1,
        copy.deepcopy(duplicate["operations"][first_cx_index]),
    )
    with pytest.raises(ValueError, match="duplicate data support"):
        exact.derive_projector_ledger(duplicate)

    unexpected = copy.deepcopy(fixture)
    unexpected["operations"][first_cx_index]["op"] = "CZ"
    with pytest.raises(ValueError, match="unexpected fixture operation"):
        exact.derive_projector_ledger(unexpected)


def test_exact_worker_imports_no_stim_quimb_or_qiskit() -> None:
    tree = ast.parse(EXACT_PATH.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])
    assert imported.isdisjoint({"stim", "quimb", "qiskit"})


def test_reference_summary_has_frozen_schema_authority_state_and_immutable_outputs(
    tmp_path: Path,
) -> None:
    exact = _load(EXACT_PATH, "xzzx_exact_summary")
    emitter, fixture = _fixture(3)
    run_spec = emitter.run_spec(fixture)
    bits = [int(bit) for bit in "0000000000000000011101101"]
    execution = exact.execute_forced_branch(
        fixture,
        bits,
        branch_id="xzzx-exact-data-d3-fixed-control",
    )
    branch = exact.neutral_branch(fixture, run_spec, execution)
    authority = exact.primary_branch_authority(branch, run_spec)
    summary_path = tmp_path / "summary.json"
    state_path = tmp_path / "state.npy"

    summary = exact.write_reference_artifacts(
        fixture=fixture,
        run_spec=run_spec,
        execution=execution,
        branch_authority=authority,
        input_provenance={"test_control": True},
        resource_usage={"wall_seconds": 0.0, "peak_host_rss_kib": 0},
        summary_path=summary_path,
        state_path=state_path,
    )

    assert summary["schema"] == (
        "error_coupling_simulator.external_xzzx_record_exact_data_reference.v1"
    )
    assert summary["run_spec"]["schema"].endswith("run_spec.v2")
    assert set(summary["branch"]) == {
        "schema",
        "fixture_sha256",
        "run_spec_sha256",
        "distance",
        "rounds",
        "branch_id",
        "outcomes",
    }
    assert summary["branch_authority"] == {
        "schema": exact.BRANCH_AUTHORITY_SCHEMA,
        "role": "primary",
        "method": "sha256_prefix_born_v1",
        "branch_sha256": exact.canonical_json_sha256(summary["branch"]),
        "selector": run_spec["reference_branch"]["selector"],
    }
    assert [row["column"] for row in summary["probability_rows"]] == list(
        range(25)
    )
    assert summary["record"]["raw_measurements"] == bits
    assert summary["record"]["absolute_xor_rows"] is True
    assert summary["state"]["state_scope"] == "all_active_qubits"
    assert summary["state"]["qubit_axis_order"] == list(range(17))
    assert summary["state"]["shape"] == [2**17]
    assert summary["state"]["file_sha256"] == hashlib.sha256(
        state_path.read_bytes()
    ).hexdigest()
    assert summary["reference_state_contract"] == {
        "probability_floor": None,
        "truncation": None,
        "normalization_square_root": "positive_real",
        "post_hoc_phase_canonicalization": None,
    }
    assert summary["candidate_payload_consumed"] is False
    assert summary["external_circuit_runtime_imported"] is False
    assert summary["forbidden_substitute_used"] is False
    assert json.loads(summary_path.read_text(encoding="utf-8")) == summary
    dense = _load(DENSE_PATH, "xzzx_dense_exact_summary_seam")
    dense_bits, dense_branch, dense_authority = (
        dense.validate_exact_primary_summary(
            summary,
            fixture=fixture,
            run_spec=run_spec,
        )
    )
    assert list(dense_bits) == bits
    assert dense_branch == summary["branch"]
    assert dense_authority == summary["branch_authority"]
    assert exact.validate_parent_primary_summary(
        summary,
        fixture=fixture,
        run_spec=run_spec,
    ) == bits

    injected = copy.deepcopy(summary)
    injected["branch"]["candidate_probability"] = 0.5
    with pytest.raises(ValueError, match="neutral branch"):
        exact.validate_parent_primary_summary(
            injected,
            fixture=fixture,
            run_spec=run_spec,
        )
    injected_state = copy.deepcopy(summary)
    injected_state["state"]["candidate_tensor"] = [1.0]
    with pytest.raises(ValueError, match="non-exact record/state/ledger"):
        exact.validate_parent_primary_summary(
            injected_state,
            fixture=fixture,
            run_spec=run_spec,
        )
    invalid_probability = copy.deepcopy(summary)
    invalid_probability["probability_rows"][0]["p0"] = math.nextafter(
        1.0,
        math.inf,
    )
    invalid_probability["probability_rows"][0]["p1"] = 0.0
    invalid_probability["probability_rows"][0]["selected_probability"] = (
        invalid_probability["probability_rows"][0]["p0"]
    )
    with pytest.raises(ValueError, match="probability"):
        exact.validate_parent_primary_summary(
            invalid_probability,
            fixture=fixture,
            run_spec=run_spec,
        )
    with pytest.raises(ValueError, match="probability"):
        dense.validate_exact_primary_summary(
            invalid_probability,
            fixture=fixture,
            run_spec=run_spec,
        )

    alternate_execution = exact.execute_alternate_branch(
        fixture,
        bits,
        branch_id=(
            f"xzzx-v2-alternate-from-{summary['branch']['branch_id']}"
        ),
    )
    alternate_branch = exact.neutral_branch(
        fixture,
        run_spec,
        alternate_execution,
    )
    alternate_authority = exact.alternate_branch_authority(
        alternate_branch,
        parent_summary_raw=summary_path.read_bytes(),
        parent_summary=summary,
        flip_column=alternate_execution["alternate_flip_column"],
    )
    assert alternate_authority["role"] == "alternate"
    assert alternate_authority["parent"] == {
        "summary_schema": exact.RESULT_SCHEMA,
        "summary_file_sha256": hashlib.sha256(
            summary_path.read_bytes()
        ).hexdigest(),
        "branch_sha256": exact.canonical_json_sha256(summary["branch"]),
        "branch_id": summary["branch"]["branch_id"],
    }
    assert alternate_authority["flip_column"] == (
        alternate_execution["alternate_flip_column"]
    )
    assert alternate_authority == dense.alternate_branch_authority(
        branch=alternate_branch,
        parent_summary_file_sha256=hashlib.sha256(
            summary_path.read_bytes()
        ).hexdigest(),
        parent_branch=summary["branch"],
        flip_column=alternate_execution["alternate_flip_column"],
    )

    before_summary = summary_path.read_bytes()
    before_state = state_path.read_bytes()
    with pytest.raises(FileExistsError, match="refusing to replace"):
        exact.write_reference_artifacts(
            fixture=fixture,
            run_spec=run_spec,
            execution=execution,
            branch_authority=authority,
            input_provenance={"test_control": True},
            resource_usage={"wall_seconds": 0.0, "peak_host_rss_kib": 0},
            summary_path=summary_path,
            state_path=state_path,
        )
    assert summary_path.read_bytes() == before_summary
    assert state_path.read_bytes() == before_state


def test_formal_provenance_binds_committed_sources_environment_and_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exact = _load(EXACT_PATH, "xzzx_exact_provenance")
    fixture_path = tmp_path / "fixture.json"
    run_spec_path = tmp_path / "run_spec.json"
    fixture_path.write_text('{"fixture":1}\n', encoding="utf-8")
    run_spec_path.write_text('{"run_spec":2}\n', encoding="utf-8")
    monkeypatch.delenv("PYTHONPATH", raising=False)
    monkeypatch.setenv("CONDA_PREFIX", str(Path(exact.sys.prefix).resolve()))
    commands = []

    def clean_run(command, **_kwargs):
        commands.append(command)
        if command[1:3] == ["rev-parse", "HEAD"]:
            output = "a" * 40 + "\n"
        elif command[1:3] == ["rev-parse", "--is-shallow-repository"]:
            output = "false\n"
        elif command[1] == "show":
            relative = command[2].split(":", 1)[1]
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(REPO / relative).read_bytes(),
                stderr=b"",
            )
        else:
            output = ""
        return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

    monkeypatch.setattr(exact.subprocess, "run", clean_run)
    provenance = exact.formal_input_provenance(
        fixture_path=fixture_path,
        run_spec_path=run_spec_path,
        parent_summary_path=None,
    )
    assert provenance["git_head"] == "a" * 40
    assert provenance["repository_is_shallow"] is False
    assert set(provenance["files_sha256"]) == set(exact.FORMAL_INPUT_PATHS)
    assert provenance["runtime"]["numpy"]["version"] == np.__version__
    assert provenance["runtime"]["core_environment_lock"]["numpy_pin_checked"] is True
    assert provenance["input_files"]["fixture"]["file_sha256"] == hashlib.sha256(
        fixture_path.read_bytes()
    ).hexdigest()
    status_command = next(command for command in commands if command[1] == "status")
    assert "--untracked-files=all" in status_command
    assert "--ignored=matching" in status_command

    monkeypatch.setenv("PYTHONPATH", str(REPO))
    with pytest.raises(RuntimeError, match="rejects PYTHONPATH"):
        exact.formal_input_provenance(
            fixture_path=fixture_path,
            run_spec_path=run_spec_path,
            parent_summary_path=None,
        )


def test_worker_import_isolated_process_loads_no_forbidden_runtime() -> None:
    command = (
        "import importlib.util,sys;"
        f"p={str(EXACT_PATH)!r};"
        "s=importlib.util.spec_from_file_location('exact_isolated',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "bad={'stim','quimb','qiskit'} & set(sys.modules);"
        "assert not bad,bad"
    )
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=REPO,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
