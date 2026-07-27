"""Public metric contracts for the XZZX measurement/reset/Record bridge."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest


REPO = Path(__file__).resolve().parents[1]
COMPARATOR_PATH = (
    REPO
    / "scripts"
    / "external_baselines"
    / "compare_xzzx_record_peps.py"
)


def _load_comparator():
    spec = importlib.util.spec_from_file_location(
        "compare_xzzx_record_peps_under_test",
        COMPARATOR_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_complete_vector_fidelity_has_registered_pure_state_semantics() -> None:
    comparator = _load_comparator()
    reference = np.asarray([1.0, 2.0j, 3.0 + 4.0j, 5.0], dtype=np.complex128)
    phase = np.exp(0.37j)

    assert comparator.complete_vector_fidelity(reference, reference) == pytest.approx(
        1.0
    )
    assert comparator.complete_vector_fidelity(
        reference,
        phase * reference,
    ) == pytest.approx(1.0)
    assert comparator.complete_vector_fidelity(
        np.asarray([1.0, 0.0], dtype=np.complex128),
        np.asarray([0.0, 1.0], dtype=np.complex128),
    ) == pytest.approx(0.0)

    with pytest.raises(ValueError, match="complex128"):
        comparator.complete_vector_fidelity(
            reference.astype(np.complex64),
            reference,
        )
    with pytest.raises(ValueError, match="shape"):
        comparator.complete_vector_fidelity(reference, reference[:2])
    nonfinite = reference.copy()
    nonfinite[0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        comparator.complete_vector_fidelity(nonfinite, reference)


def test_raw_trajectory_tv_pins_support_half_factor_and_label_firewall() -> None:
    comparator = _load_comparator()
    support = ["00", "01", "10", "11"]
    reference = {"00": 0.75, "01": 0.25, "10": 0.0, "11": 0.0}
    candidate = {"00": 0.25, "01": 0.25, "10": 0.5, "11": 0.0}

    value = comparator.raw_trajectory_total_variation(
        reference,
        candidate,
        support=support,
        object_kind="raw_trajectory",
    )
    assert value == pytest.approx(0.5)

    missing_structural_zero = dict(candidate)
    missing_structural_zero.pop("11")
    with pytest.raises(ValueError, match="complete declared support"):
        comparator.raw_trajectory_total_variation(
            reference,
            missing_structural_zero,
            support=support,
            object_kind="raw_trajectory",
        )
    with pytest.raises(ValueError, match="must not be labelled Record"):
        comparator.raw_trajectory_total_variation(
            reference,
            candidate,
            support=support,
            object_kind="record",
        )
    unnormalized = dict(candidate)
    unnormalized["10"] = 0.4
    with pytest.raises(ValueError, match="normalized"):
        comparator.raw_trajectory_total_variation(
            reference,
            unnormalized,
            support=support,
            object_kind="raw_trajectory",
        )


def test_selected_branch_metrics_align_columns_and_preserve_path_mass() -> None:
    comparator = _load_comparator()
    reference = [
        {"column": 0, "bit": 0, "p0": 0.8, "p1": 0.2},
        {"column": 1, "bit": 1, "p0": 0.7, "p1": 0.3},
    ]
    candidate = [
        {"column": 0, "bit": 0, "p0": 0.7, "p1": 0.3},
        {"column": 1, "bit": 1, "p0": 0.6, "p1": 0.4},
    ]

    metrics = comparator.selected_branch_metrics(reference, candidate)
    assert metrics["max_probability_error"] == pytest.approx(0.1)
    assert metrics["log_branch_mass_error"] == pytest.approx(
        abs(np.log(0.8) + np.log(0.3) - np.log(0.7) - np.log(0.4))
    )
    assert metrics["reference_log_branch_mass"] == pytest.approx(
        np.log(0.8) + np.log(0.3)
    )

    mismatched = [dict(row) for row in candidate]
    mismatched[1]["column"] = 2
    with pytest.raises(ValueError, match="column"):
        comparator.selected_branch_metrics(reference, mismatched)

    wrong_bit = [dict(row) for row in candidate]
    wrong_bit[1]["bit"] = 0
    with pytest.raises(ValueError, match="selected bit"):
        comparator.selected_branch_metrics(reference, wrong_bit)

    impossible = [dict(row) for row in candidate]
    impossible[1] = {
        "column": 1,
        "bit": 1,
        "p0": 1.0,
        "p1": 0.0,
    }
    with pytest.raises(ValueError, match="zero candidate probability"):
        comparator.selected_branch_metrics(reference, impossible)

    unnormalized = [dict(row) for row in candidate]
    unnormalized[0]["p0"] = 0.6
    with pytest.raises(ValueError, match="Bernoulli"):
        comparator.selected_branch_metrics(reference, unnormalized)


def test_reset_trace_distance_uses_the_one_site_density_operator() -> None:
    comparator = _load_comparator()
    reset = np.asarray([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)
    diagonal = np.asarray([[0.8, 0.0], [0.0, 0.2]], dtype=np.complex128)
    plus = 0.5 * np.asarray([[1.0, 1.0], [1.0, 1.0]], dtype=np.complex128)

    assert comparator.reset_trace_distance_to_zero(reset) == pytest.approx(0.0)
    assert comparator.reset_trace_distance_to_zero(diagonal) == pytest.approx(0.2)
    assert comparator.reset_trace_distance_to_zero(plus) == pytest.approx(
        1.0 / np.sqrt(2.0)
    )

    nonhermitian = np.asarray(
        [[1.0, 0.1j], [0.0, 0.0]],
        dtype=np.complex128,
    )
    with pytest.raises(ValueError, match="Hermitian"):
        comparator.reset_trace_distance_to_zero(nonhermitian)
    wrong_trace = diagonal * 0.5
    with pytest.raises(ValueError, match="trace one"):
        comparator.reset_trace_distance_to_zero(wrong_trace)
    with pytest.raises(ValueError, match="complex128"):
        comparator.reset_trace_distance_to_zero(diagonal.astype(np.complex64))


def test_complete_state_loader_rejects_proxies_and_axis_reversal(
    tmp_path: Path,
) -> None:
    comparator = _load_comparator()
    state = np.asarray([1.0, 2.0j, 3.0 + 4.0j, 5.0], dtype=np.complex128)
    state_path = tmp_path / "state.npy"
    np.save(state_path, state, allow_pickle=False)
    metadata = {
        "source_kind": "complete_complex128_state_vector",
        "dtype": "complex128",
        "shape": [4],
        "path": str(state_path.resolve()),
        "file_sha256": hashlib.sha256(state_path.read_bytes()).hexdigest(),
        "qubit_axis_order": [2, 4],
        "q0_bit_significance": "most_significant",
    }

    loaded = comparator.load_complete_state(
        metadata,
        expected_axis_order=[2, 4],
    )
    np.testing.assert_array_equal(loaded, state)
    axis_reversed_state = state.reshape(2, 2).T.reshape(-1)
    assert (
        comparator.complete_vector_fidelity(state, axis_reversed_state)
        < 1.0 - 1e-8
    )

    reversed_order = dict(metadata)
    reversed_order["qubit_axis_order"] = [4, 2]
    with pytest.raises(ValueError, match="axis order"):
        comparator.load_complete_state(
            reversed_order,
            expected_axis_order=[2, 4],
        )

    proxy = dict(metadata)
    proxy["source_kind"] = "finite_boundary_overlap"
    with pytest.raises(ValueError, match="proxy"):
        comparator.load_complete_state(proxy, expected_axis_order=[2, 4])


def test_branch_identity_binds_hashes_and_contiguous_measurement_columns() -> None:
    comparator = _load_comparator()
    fixture_sha = "a" * 64
    run_sha = "b" * 64
    branch = {
        "schema": "error_coupling_simulator.external_xzzx_record_peps.branch.v1",
        "fixture_sha256": fixture_sha,
        "run_spec_sha256": run_sha,
        "distance": 3,
        "rounds": 2,
        "branch_id": "primary",
        "outcomes": [
            {"column": 0, "bit": 1},
            {"column": 1, "bit": 0},
        ],
    }

    assert comparator.validate_branch_identity(
        branch,
        expected_fixture_sha256=fixture_sha,
        expected_run_spec_sha256=run_sha,
        expected_distance=3,
        expected_rounds=2,
        expected_measurement_count=2,
    ) == [1, 0]

    wrong_hash = dict(branch)
    wrong_hash["run_spec_sha256"] = "c" * 64
    with pytest.raises(ValueError, match="run-spec"):
        comparator.validate_branch_identity(
            wrong_hash,
            expected_fixture_sha256=fixture_sha,
            expected_run_spec_sha256=run_sha,
            expected_distance=3,
            expected_rounds=2,
            expected_measurement_count=2,
        )

    wrong_columns = dict(branch)
    wrong_columns["outcomes"] = [
        {"column": 1, "bit": 1},
        {"column": 0, "bit": 0},
    ]
    with pytest.raises(ValueError, match="contiguous"):
        comparator.validate_branch_identity(
            wrong_columns,
            expected_fixture_sha256=fixture_sha,
            expected_run_spec_sha256=run_sha,
            expected_distance=3,
            expected_rounds=2,
            expected_measurement_count=2,
        )


def test_trajectory_verdict_never_promotes_high_fidelity_with_wrong_mass() -> None:
    comparator = _load_comparator()

    assert comparator.classify_conditioned_trajectory(
        distance=3,
        fidelity=0.995,
        max_probability_error=0.004,
        log_branch_mass_error=0.09,
        reset_checks_pass=True,
        realized_fold_pass=True,
        complete_vector_available=True,
    ) == "useful_conditioned_trajectory"
    assert comparator.classify_conditioned_trajectory(
        distance=3,
        fidelity=0.995,
        max_probability_error=0.006,
        log_branch_mass_error=0.09,
        reset_checks_pass=True,
        realized_fold_pass=True,
        complete_vector_available=True,
    ) == "state_useful_mass_unresolved"
    assert comparator.classify_conditioned_trajectory(
        distance=5,
        fidelity=0.995,
        max_probability_error=0.009,
        log_branch_mass_error=0.51,
        reset_checks_pass=True,
        realized_fold_pass=True,
        complete_vector_available=True,
    ) == "state_useful_mass_unresolved"
    assert comparator.classify_conditioned_trajectory(
        distance=5,
        fidelity=None,
        max_probability_error=0.0,
        log_branch_mass_error=0.0,
        reset_checks_pass=True,
        realized_fold_pass=True,
        complete_vector_available=False,
    ) == "unavailable"
    assert comparator.classify_conditioned_trajectory(
        distance=5,
        fidelity=0.949,
        max_probability_error=0.0,
        log_branch_mass_error=0.0,
        reset_checks_pass=True,
        realized_fold_pass=True,
        complete_vector_available=True,
    ) == "low_state"


def test_metric_ledger_names_each_xzzx_object_and_owner() -> None:
    ledger = (REPO / "docs" / "METRICS.md").read_text(encoding="utf-8")
    assert "scripts/external_baselines/compare_xzzx_record_peps.py" in ledger
    for object_name in (
        "Complete-vector fidelity",
        "Tracer raw-trajectory TV",
        "Selected-branch maximum conditional-probability error",
        "selected-branch log-mass error",
        "Post-reset one-site trace distance",
    ):
        assert object_name in ledger


def test_metric_owner_does_not_import_candidate_or_reference_implementations() -> None:
    tree = ast.parse(COMPARATOR_PATH.read_text(encoding="utf-8"))
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_modules.update(
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    forbidden_modules = {
        "quimb",
        "qiskit",
        "xzzx_record_dense_reference",
        "xzzx_record_exact_data_reference",
        "xzzx_record_quimb_candidate",
        "xzzx_record_aer_worker",
    }
    assert not {
        imported
        for imported in imported_modules
        if any(
            imported == forbidden or imported.startswith(f"{forbidden}.")
            for forbidden in forbidden_modules
        )
    }


def test_selected_branch_point_binds_objects_and_returns_one_verdict(
    tmp_path: Path,
) -> None:
    comparator = _load_comparator()
    fixture_sha = (
        "3b2bf7d81f7241e0a3b6abb14c76474c362e696cf374c55e20e3d121946bbf3c"
    )
    run_sha = (
        "7dfa0a8ef9620712e6ea190aeda651c681295f9841963ce77686640255cc22a9"
    )
    axis_order = list(range(17))
    state = np.zeros(1 << 17, dtype=np.complex128)
    state[0] = np.sqrt(0.8)
    state[-1] = np.sqrt(0.2) * np.exp(1j * np.pi / 7.0)

    def write_state(name: str) -> dict:
        path = tmp_path / f"{name}.npy"
        np.save(path, state, allow_pickle=False)
        return {
            "source_kind": "complete_complex128_state_vector",
            "state_scope": "all_active_qubits",
            "dtype": "complex128",
            "shape": [1 << 17],
            "path": str(path.resolve()),
            "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "qubit_axis_order": axis_order,
            "q0_bit_significance": "most_significant",
        }

    outcomes = [{"column": column, "bit": 0} for column in range(25)]
    probability_rows = [
        {"column": column, "bit": 0, "p0": 1.0, "p1": 0.0}
        for column in range(25)
    ]
    branch = {
        "schema": "error_coupling_simulator.external_xzzx_record_peps.branch.v1",
        "fixture_sha256": fixture_sha,
        "run_spec_sha256": run_sha,
        "distance": 3,
        "rounds": 2,
        "branch_id": "primary",
        "outcomes": outcomes,
    }
    branch_sha = hashlib.sha256(
        (
            json.dumps(branch, allow_nan=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8")
    ).hexdigest()
    branch_authority = {
        "schema": (
            "error_coupling_simulator.external_xzzx_record_exact_data_reference."
            "branch_authority.v1"
        ),
        "role": "primary",
        "method": "sha256_prefix_born_v1",
        "branch_sha256": branch_sha,
        "selector": {"algorithm": "sha256_prefix_born_v1"},
    }
    fixture = {
        "schema": "error_coupling_simulator.external_xzzx_record_peps.fixture.v1",
        "canonical_sha256": fixture_sha,
        "distance": 3,
        "rounds": 2,
        "num_qubits": 17,
        "num_measurements": 25,
    }
    run_spec = {"canonical_sha256": run_sha}
    reference = {
        "schema": (
            "error_coupling_simulator."
            "external_xzzx_record_exact_data_reference.v1"
        ),
        "status": "completed",
        "method": "numpy_exact_data_projector",
        "reference_state_contract": {
            "probability_floor": None,
            "truncation": None,
            "normalization_square_root": "positive_real",
            "post_hoc_phase_canonicalization": None,
        },
        "candidate_payload_consumed": False,
        "external_circuit_runtime_imported": False,
        "forbidden_substitute_used": False,
        "fixture": fixture,
        "run_spec": run_spec,
        "checkpoint": comparator.PRETERMINAL_CHECKPOINT,
        "branch": branch,
        "branch_authority": branch_authority,
        "probability_rows": probability_rows,
        "record": {
            "detector_bits": [0] * 16,
            "observable_bits": [0],
        },
        "state": write_state("reference"),
    }
    candidate = {
        "schema": "error_coupling_simulator.external_xzzx_record_quimb_candidate.v1",
        "status": "completed",
        "fixture": {**fixture, "sha256": fixture_sha},
        "run_spec": {**run_spec, "sha256": run_sha},
        "checkpoint": comparator.PRETERMINAL_CHECKPOINT,
        "branch": branch,
        "branch_authority": branch_authority,
        "exact_reference_authority_source": {
            "summary_schema": (
                "error_coupling_simulator."
                "external_xzzx_record_exact_data_reference.v1"
            ),
            "summary_file_sha256": "a" * 64,
            "branch_sha256": branch_sha,
            "branch_id": "primary",
            "authority": branch_authority,
            "reference_probabilities_or_state_consumed": False,
        },
        "candidate": {
            "requested_max_bond": 8,
            "rdm_radius": "complete",
            "cutoff": 0.0,
            "reset_trace_distance_limit": 1e-10,
        },
        "probability_rows": probability_rows,
        "reset_checks": [
            {
                "column": column,
                "qubit": qubit,
                "trace_distance_to_zero": 0.0,
                "physical_one_tensor_slice_exact_zero": True,
            }
            for column, qubit in enumerate(
                [1, 5, 7, 9, 10, 12, 14, 16] * 2
            )
        ],
        "checkpoint_reset_slices": [
            {
                "qubit": qubit,
                "physical_one_tensor_slice_exact_zero": True,
            }
            for qubit in [1, 5, 7, 9, 10, 12, 14, 16]
        ],
        "record": {
            "detector_bits": [0] * 16,
            "observable_bits": [0],
        },
        "state": write_state("candidate"),
        "private_candidate_tensors_or_gauges_exported": False,
        "reference_tensor_or_gauge_consumed": False,
        "forbidden_substitute_used": False,
    }

    result = comparator.compare_selected_branch_point(reference, candidate)
    assert result["schema"] == comparator.RESULT_SCHEMA
    assert result["fidelity"] == pytest.approx(1.0)
    assert result["max_probability_error"] == pytest.approx(0.0)
    assert result["log_branch_mass_error"] == pytest.approx(0.0)
    assert result["max_reset_trace_distance"] == pytest.approx(0.0)
    assert result["realized_fold_pass"] is True
    assert result["verdict"] == "useful_conditioned_trajectory"

    dense_substitute = dict(reference)
    dense_substitute["schema"] = (
        "error_coupling_simulator.external_xzzx_record_dense_reference.v1"
    )
    with pytest.raises(ValueError, match="unsupported XZZX reference schema"):
        comparator.compare_selected_branch_point(dense_substitute, candidate)

    aer_substitute = dict(reference)
    aer_substitute["schema"] = (
        "error_coupling_simulator.external_xzzx_record_aer_reference.v1"
    )
    with pytest.raises(ValueError, match="unsupported XZZX reference schema"):
        comparator.compare_selected_branch_point(aer_substitute, candidate)

    candidate_with_reference_payload = dict(candidate)
    candidate_with_reference_payload["branch"] = {
        **candidate["branch"],
        "reference_probability_rows": probability_rows,
    }
    with pytest.raises(ValueError, match="neutral field set"):
        comparator.compare_selected_branch_point(
            reference,
            candidate_with_reference_payload,
        )

    wrong_authority = dict(candidate)
    wrong_authority["branch_authority"] = {
        **branch_authority,
        "branch_sha256": "f" * 64,
    }
    with pytest.raises(ValueError, match="branch authority"):
        comparator.compare_selected_branch_point(reference, wrong_authority)

    reference_path = tmp_path / "reference.json"
    candidate_path = tmp_path / "candidate.json"
    output_path = tmp_path / "comparison.json"
    reference_path.write_text(
        json.dumps(reference, sort_keys=True),
        encoding="utf-8",
    )
    candidate["exact_reference_authority_source"]["summary_file_sha256"] = (
        hashlib.sha256(reference_path.read_bytes()).hexdigest()
    )
    candidate_path.write_text(
        json.dumps(candidate, sort_keys=True),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(COMPARATOR_PATH),
            "--reference-summary",
            str(reference_path),
            "--candidate-summary",
            str(candidate_path),
            "--output",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    persisted = json.loads(output_path.read_text(encoding="utf-8"))
    assert persisted["verdict"] == "useful_conditioned_trajectory"
    assert persisted["input_provenance"] == {
        "reference_summary_path": str(reference_path.resolve()),
        "reference_summary_sha256": hashlib.sha256(
            reference_path.read_bytes()
        ).hexdigest(),
        "candidate_summary_path": str(candidate_path.resolve()),
        "candidate_summary_sha256": hashlib.sha256(
            candidate_path.read_bytes()
        ).hexdigest(),
        "comparator_path": str(COMPARATOR_PATH.resolve()),
        "comparator_sha256": hashlib.sha256(COMPARATOR_PATH.read_bytes()).hexdigest(),
    }

    refused_overwrite = subprocess.run(
        [
            sys.executable,
            str(COMPARATOR_PATH),
            "--reference-summary",
            str(reference_path),
            "--candidate-summary",
            str(candidate_path),
            "--output",
            str(output_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert refused_overwrite.returncode != 0
    assert "already exists" in refused_overwrite.stderr


def test_d2_tracer_comparison_requires_full_raw_and_record_support() -> None:
    comparator = _load_comparator()
    fixture_sha = (
        "dbf2a0979c9a4cd0a95f2afe393083d97a27ea1e90720596352a191010beb0f5"
    )
    spec_sha = (
        "02aef76a65383fbfec9a2f3e0b62a7dd0691a574ee739a4b6b33326ba13681ca"
    )
    raw = {f"{index:010b}": 1.0 / 1024.0 for index in range(1024)}
    record = {f"{index:06b}": 1.0 / 64.0 for index in range(64)}
    ry_zero_record = dict(record)
    ry_zero_record["000000"] += 2e-6
    ry_zero_record["000001"] -= 2e-6
    dense = {
        "schema": "error_coupling_simulator.external_xzzx_record_dense_reference.v1",
        "status": "completed",
        "mode": "tracer_full_law",
        "fixture_sha256": fixture_sha,
        "enumeration_spec_sha256": spec_sha,
        "raw_bit_order": "measurement_column_ascending_big_endian",
        "record_bit_order": (
            "detector_row_ascending_then_observable_row_ascending_big_endian"
        ),
        "raw_law": raw,
        "record_law": record,
        "ry_zero_record_law": ry_zero_record,
    }
    candidate = {
        "schema": "error_coupling_simulator.external_xzzx_record_quimb_candidate.v1",
        "status": "completed",
        "mode": "d2_complete_raw_and_record_law",
        "fixture": {
            "distance": 2,
            "rounds": 2,
            "canonical_sha256": fixture_sha,
            "sha256": fixture_sha,
        },
        "run_spec": {
            "canonical_sha256": spec_sha,
            "sha256": spec_sha,
            "enumeration": True,
        },
        "candidate": {
            "requested_max_bond": 8,
            "rdm_radius": "complete",
            "cutoff": 0.0,
        },
        "raw_bit_order": dense["raw_bit_order"],
        "record_bit_order": dense["record_bit_order"],
        "raw_law": raw,
        "record_law": record,
        "diagnostics": {
            "all_reset_tensor_slices_exact_zero": True,
            "max_reset_trace_distance": 0.0,
            "all_rdm_coverage_complete": True,
        },
        "private_candidate_tensors_or_gauges_exported": False,
        "reference_tensor_or_gauge_consumed": False,
        "forbidden_substitute_used": False,
    }

    result = comparator.compare_d2_tracer_laws(dense, candidate)
    assert result["raw_law_support_size"] == 1024
    assert result["record_law_support_size"] == 64
    assert result["raw_law_tv"] == pytest.approx(0.0)
    assert result["record_law_tv"] == pytest.approx(0.0)
    assert result["ry_record_nondegeneracy_tv"] == pytest.approx(2e-6)
    assert result["passes"] is True

    missing_zero = dict(candidate)
    missing_zero["raw_law"] = dict(raw)
    missing_zero["raw_law"].pop("1111111111")
    with pytest.raises(ValueError, match="complete declared support"):
        comparator.compare_d2_tracer_laws(dense, missing_zero)


def test_d3_exact_data_reference_must_match_independent_full_dense(
    tmp_path: Path,
) -> None:
    comparator = _load_comparator()
    fixture_sha = (
        "3b2bf7d81f7241e0a3b6abb14c76474c362e696cf374c55e20e3d121946bbf3c"
    )
    run_sha = (
        "7dfa0a8ef9620712e6ea190aeda651c681295f9841963ce77686640255cc22a9"
    )
    state = np.zeros(1 << 17, dtype=np.complex128)
    state[0] = 1.0

    def write_state(name: str, vector: np.ndarray) -> dict:
        path = tmp_path / f"{name}.npy"
        np.save(path, vector, allow_pickle=False)
        return {
            "source_kind": "complete_complex128_state_vector",
            "state_scope": "all_active_qubits",
            "dtype": "complex128",
            "shape": [1 << 17],
            "path": str(path.resolve()),
            "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "qubit_axis_order": list(range(17)),
            "q0_bit_significance": "most_significant",
        }

    rows = [
        {"column": column, "bit": 0, "p0": 0.75, "p1": 0.25}
        for column in range(25)
    ]
    branch = {
        "schema": "error_coupling_simulator.external_xzzx_record_peps.branch.v1",
        "fixture_sha256": fixture_sha,
        "run_spec_sha256": run_sha,
        "distance": 3,
        "rounds": 2,
        "branch_id": "primary",
        "outcomes": [{"column": column, "bit": 0} for column in range(25)],
        "probability_rows": rows,
        "detector_bits": [0] * 16,
        "observable_bits": [0],
    }
    branch_authority = {
        "schema": (
            "error_coupling_simulator.external_xzzx_record_exact_data_reference."
            "branch_authority.v1"
        ),
        "role": "primary",
        "method": "sha256_prefix_born_v1",
        "branch_sha256": hashlib.sha256(
            (
                json.dumps(branch, allow_nan=False, indent=2, sort_keys=True)
                + "\n"
            ).encode("utf-8")
        ).hexdigest(),
        "selector": {"algorithm": "sha256_prefix_born_v1"},
    }
    fixture = {
        "canonical_sha256": fixture_sha,
        "distance": 3,
        "rounds": 2,
    }
    run_spec = {"canonical_sha256": run_sha}
    exact = {
        "schema": (
            "error_coupling_simulator."
            "external_xzzx_record_exact_data_reference.v1"
        ),
        "status": "completed",
        "method": "numpy_exact_data_projector",
        "reference_state_contract": {
            "probability_floor": None,
            "truncation": None,
            "normalization_square_root": "positive_real",
            "post_hoc_phase_canonicalization": None,
        },
        "candidate_payload_consumed": False,
        "external_circuit_runtime_imported": False,
        "forbidden_substitute_used": False,
        "fixture": fixture,
        "run_spec": run_spec,
        "checkpoint": comparator.PRETERMINAL_CHECKPOINT,
        "branch": branch,
        "branch_authority": branch_authority,
        "state": write_state("exact", state),
    }
    dense = {
        "schema": "error_coupling_simulator.external_xzzx_record_dense_reference.v1",
        "status": "completed",
        "fixture": fixture,
        "run_spec": run_spec,
        "checkpoint": comparator.PRETERMINAL_CHECKPOINT,
        "branch": branch,
        "branch_authority": branch_authority,
        "state": write_state("dense", state),
    }

    result = comparator.compare_d3_exact_and_full_dense(exact, dense)
    assert result["fidelity"] == pytest.approx(1.0)
    assert result["max_probability_error"] == pytest.approx(0.0)
    assert result["log_branch_mass_error"] == pytest.approx(0.0)
    assert result["passes"] is True

    corrupted = dict(dense)
    corrupted["branch"] = dict(branch)
    corrupted["branch"]["probability_rows"] = [dict(row) for row in rows]
    corrupted["branch"]["probability_rows"][2]["p0"] += 2e-12
    corrupted["branch"]["probability_rows"][2]["p1"] -= 2e-12
    assert (
        comparator.compare_d3_exact_and_full_dense(exact, corrupted)["passes"]
        is False
    )
