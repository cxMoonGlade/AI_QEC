"""Focused contracts for the frozen d5 pure-state external PEPS benchmark."""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest


REPO = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO / "scripts" / "external_baselines"
EMITTER_PATH = SCRIPT_DIR / "emit_peps_d5_pure_state_fixture.py"
DENSE_PATH = SCRIPT_DIR / "peps_d5_dense_reference.py"
QUIMB_PATH = SCRIPT_DIR / "quimb_peps_d5_fidelity_worker.py"
PEPSY_PATH = SCRIPT_DIR / "pepsy_peps_d5_state_worker.py"
COMPARE_PATH = SCRIPT_DIR / "compare_peps_d5_complete_states.py"
RUNNER_PATH = SCRIPT_DIR / "run_peps_d5_complete_state_sweeps.py"
CORRUPTION_CONTROL_PATH = (
    SCRIPT_DIR / "peps_d5_physical_corruption_control.py"
)
EXPECTED_D3_CANONICAL_SHA256 = (
    "d53a3cd27e53f3fcf5fbe8c0d91232d1f81e2f8d914d78bea6914ec3988c4125"
)
EXPECTED_D5_CANONICAL_SHA256 = (
    "c73b932ff8c213d6dce956cddb9bee0c9bfa2b465bde3bc6a3ece5789aed1324"
)


def _load_script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def modules():
    emitter = _load_script(
        EMITTER_PATH,
        "emit_peps_d5_pure_state_fixture",
    )
    sys.modules["emit_peps_d5_pure_state_fixture"] = emitter
    dense = _load_script(
        DENSE_PATH,
        "peps_d5_dense_reference_under_test",
    )
    quimb_worker = _load_script(
        QUIMB_PATH,
        "quimb_peps_d5_fidelity_worker_under_test",
    )
    pepsy_worker = _load_script(
        PEPSY_PATH,
        "pepsy_peps_d5_state_worker_under_test",
    )
    comparison = _load_script(
        COMPARE_PATH,
        "compare_peps_d5_complete_states_under_test",
    )
    return emitter, dense, quimb_worker, pepsy_worker, comparison


def test_d5_fixture_identity_counts_and_order_are_pinned(modules) -> None:
    emitter, _dense, _quimb_worker, _pepsy_worker, _comparison = modules
    fixture = emitter.build_fixture(size=5)

    assert fixture["schema"] == emitter.FIXTURE_SCHEMA
    assert fixture["site_count"] == 25
    assert fixture["edge_count"] == 40
    assert fixture["cycle_count"] == 4
    assert fixture["operation_count"] == 272
    assert fixture["one_site_operation_count"] == 112
    assert fixture["two_site_operation_count"] == 160
    assert fixture["exact_per_edge_bond_ceiling"] == 16
    assert emitter.canonical_sha256(fixture) == EXPECTED_D5_CANONICAL_SHA256
    assert (
        emitter.validate_fixture(fixture, expected_size=5)
        == EXPECTED_D5_CANONICAL_SHA256
    )

    assert [site["qubit"] for site in fixture["sites"]] == list(range(25))
    assert [
        (site["row"], site["column"])
        for site in fixture["sites"]
    ] == [(row, column) for row in range(5) for column in range(5)]
    assert Counter(
        edge["color"] for edge in fixture["edges_in_execution_order"]
    ) == {
        "horizontal_even": 10,
        "horizontal_odd": 10,
        "vertical_even": 10,
        "vertical_odd": 10,
    }
    assert len(
        {
            frozenset((edge["a"], edge["b"]))
            for edge in fixture["edges_in_execution_order"]
        }
    ) == 40

    edge_counts = Counter()
    for operation in fixture["operations"]:
        if operation["kind"] != "PAULI_ROTATION":
            continue
        assert sorted(operation["paulis"]) == ["X", "Z"]
        edge_counts[frozenset(operation["targets"])] += 1
    assert set(edge_counts.values()) == {4}
    assert len(edge_counts) == 40
    assert fixture["amplitude_convention"] == {
        "storage": "one_dimensional_c_order_complex128",
        "qubit_axis_order": list(range(25)),
        "q0_axis": 0,
        "q0_bit_significance": "most_significant",
        "flat_index": "sum_q bit(q)*2**(site_count-1-q)",
        "local_basis": ["|0>", "|1>"],
        "two_qubit_basis": ["|00>", "|01>", "|10>", "|11>"],
        "target_to_kronecker_factor": (
            "targets[0] is the left Kronecker factor and the more "
            "significant local basis bit"
        ),
        "matrix_indices": "row_is_output_column_is_input",
        "chronological_update": (
            "operations execute in ascending index; psi <- U_operation*psi; "
            "final_state=U_last*...*U_1*U_0*initial_state"
        ),
    }
    assert fixture["operations"][156] == {
        "index": 156,
        "kind": "PAULI_ROTATION",
        "targets": [11, 12],
        "paulis": ["Z", "X"],
        "angle_rad": "0.31",
        "cycle": 2,
        "edge_color": "horizontal_odd",
    }


def test_d3_identity_and_claim_boundary_are_independently_pinned(modules) -> None:
    emitter, _dense, _quimb_worker, _pepsy_worker, _comparison = modules
    fixture = emitter.build_fixture(size=3)
    assert fixture["claim_boundary"].startswith(
        "controlled 3x3 pure-state unitary benchmark only"
    )
    assert emitter.canonical_sha256(fixture) == EXPECTED_D3_CANONICAL_SHA256
    assert (
        emitter.validate_fixture(fixture, expected_size=3)
        == EXPECTED_D3_CANONICAL_SHA256
    )


def test_fixture_signs_and_physical_mutations_change_identity(modules) -> None:
    emitter, _dense, _quimb_worker, _pepsy_worker, _comparison = modules
    fixture = emitter.build_fixture(size=5)

    for cycle in range(4):
        ry = [
            operation
            for operation in fixture["operations"]
            if operation["kind"] == "RY" and operation["cycle"] == cycle
        ]
        assert len(ry) == 25
        for operation in ry:
            target = operation["targets"][0]
            row, column = divmod(target, 5)
            base = float(
                fixture["cycle_parameters"][cycle][
                    "phi_rad_before_checkerboard_sign"
                ]
            )
            expected = base if (row + column) % 2 == 0 else -base
            assert float(operation["angle_rad"]) == expected

    deleted = copy.deepcopy(fixture)
    removed = next(
        index
        for index, operation in enumerate(deleted["operations"])
        if operation["kind"] == "PAULI_ROTATION"
        and operation["cycle"] == 2
        and operation["targets"] == [11, 12]
    )
    deleted["operations"].pop(removed)
    for index, operation in enumerate(deleted["operations"]):
        operation["index"] = index
    deleted["operation_count"] -= 1
    deleted["two_site_operation_count"] -= 1
    with pytest.raises(ValueError, match="two-site operation count"):
        emitter.validate_fixture(deleted, expected_size=5)

    sign_flipped = copy.deepcopy(fixture)
    changed = next(
        operation
        for operation in sign_flipped["operations"]
        if operation["kind"] == "PAULI_ROTATION"
        and operation["cycle"] == 2
        and operation["targets"] == [11, 12]
    )
    changed["angle_rad"] = str(-float(changed["angle_rad"]))
    assert (
        emitter.canonical_sha256(sign_flipped)
        != EXPECTED_D5_CANONICAL_SHA256
    )
    with pytest.raises(ValueError, match="semantic mismatch"):
        emitter.validate_fixture(
            sign_flipped,
            expected_size=5,
            require_pinned_hash=False,
        )


def test_semantic_validator_rejects_each_hash_independent_corruption(
    modules,
) -> None:
    emitter, _dense, _quimb_worker, _pepsy_worker, _comparison = modules
    fixture = emitter.build_fixture(size=5)

    corruptions = []

    complex64 = copy.deepcopy(fixture)
    complex64["dtype"] = "complex64"
    corruptions.append(complex64)

    widened = copy.deepcopy(fixture)
    widened["claim_boundary"] = "full QEC Record"
    corruptions.append(widened)

    wrong_frame = copy.deepcopy(fixture)
    wrong_frame["sites"][0]["frame_pauli"] = "Z"
    corruptions.append(wrong_frame)

    non_neighbour = copy.deepcopy(fixture)
    non_neighbour["operations"][156]["targets"] = [0, 24]
    corruptions.append(non_neighbour)

    wrong_theta = copy.deepcopy(fixture)
    wrong_theta["operations"][156]["angle_rad"] = "0.32"
    corruptions.append(wrong_theta)

    wrong_cycle = copy.deepcopy(fixture)
    wrong_cycle["operations"][156]["cycle"] = 1
    corruptions.append(wrong_cycle)

    wrong_ry_sign = copy.deepcopy(fixture)
    ry = next(
        operation
        for operation in wrong_ry_sign["operations"]
        if operation["kind"] == "RY"
        and operation["cycle"] == 2
        and operation["targets"] == [1]
    )
    ry["angle_rad"] = str(-float(ry["angle_rad"]))
    corruptions.append(wrong_ry_sign)

    wrong_h_target = copy.deepcopy(fixture)
    wrong_h_target["operations"][0]["targets"] = [0]
    corruptions.append(wrong_h_target)

    duplicate_gate = copy.deepcopy(fixture)
    duplicate_gate["operations"][13] = copy.deepcopy(
        duplicate_gate["operations"][12]
    )
    duplicate_gate["operations"][13]["index"] = 13
    corruptions.append(duplicate_gate)

    permuted_edges = copy.deepcopy(fixture)
    permuted_edges["edges_in_execution_order"][0:2] = reversed(
        permuted_edges["edges_in_execution_order"][0:2]
    )
    corruptions.append(permuted_edges)

    wrong_basis = copy.deepcopy(fixture)
    wrong_basis["amplitude_convention"]["local_basis"] = ["|1>", "|0>"]
    corruptions.append(wrong_basis)

    for corrupted in corruptions:
        with pytest.raises(ValueError, match="semantic mismatch"):
            emitter.validate_fixture(
                corrupted,
                expected_size=5,
                require_pinned_hash=False,
            )


def test_gate_unitarity_and_half_angle_have_distinct_falsifiers(
    modules,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _emitter, dense, quimb_worker, pepsy_worker, _comparison = modules
    theta = 0.31
    x = np.asarray([[0, 1], [1, 0]], dtype=np.complex128)
    z = np.asarray([[1, 0], [0, -1]], dtype=np.complex128)
    zx = np.kron(z, x)
    exact = (
        np.cos(theta / 2.0) * np.eye(4, dtype=np.complex128)
        - 1j * np.sin(theta / 2.0) * zx
    )
    residual = np.max(np.abs(exact.conj().T @ exact - np.eye(4)))
    assert residual <= 1e-12

    nonunitary = exact.copy()
    nonunitary[0, 0] += 1e-3
    corrupted_residual = np.max(
        np.abs(nonunitary.conj().T @ nonunitary - np.eye(4))
    )
    assert corrupted_residual > 1e-12

    wrong_half_angle = (
        np.cos(theta) * np.eye(4, dtype=np.complex128)
        - 1j * np.sin(theta) * zx
    )
    assert np.max(np.abs(wrong_half_angle - exact)) > 1e-12
    operation = {
        "index": 156,
        "kind": "PAULI_ROTATION",
        "targets": [11, 12],
        "paulis": ["Z", "X"],
        "angle_rad": "0.31",
    }
    for validator in (
        dense._validate_gate_matrix_numpy,
        quimb_worker._validate_numpy_gate,
    ):
        unitary, semantic = validator(operation, exact)
        assert unitary <= 1e-12
        assert semantic <= 1e-12
        with pytest.raises(RuntimeError, match="nonunitary gate"):
            validator(operation, nonunitary)
        with pytest.raises(RuntimeError, match="half-angle/matrix mismatch"):
            validator(operation, wrong_half_angle)
        with pytest.raises(RuntimeError, match="matrix contract drift"):
            validator(operation, exact.astype(np.complex64))

    _gate, unitary, semantic = pepsy_worker._validated_numpy_gate(operation)
    assert unitary <= 1e-12
    assert semantic <= 1e-12
    monkeypatch.setattr(
        pepsy_worker,
        "_numpy_gate",
        lambda _operation: nonunitary,
    )
    with pytest.raises(RuntimeError, match="unitarity residual"):
        pepsy_worker._validated_numpy_gate(operation)
    monkeypatch.setattr(
        pepsy_worker,
        "_numpy_gate",
        lambda _operation: wrong_half_angle,
    )
    with pytest.raises(RuntimeError, match="closed-form half-angle"):
        pepsy_worker._validated_numpy_gate(operation)
    monkeypatch.setattr(
        pepsy_worker,
        "_numpy_gate",
        lambda _operation: exact.astype(np.complex64),
    )
    with pytest.raises(RuntimeError, match="dtype drifted"):
        pepsy_worker._validated_numpy_gate(operation)


def test_cuda_device_names_are_indexed_before_set_device(modules) -> None:
    _emitter, dense, quimb_worker, _pepsy_worker, _comparison = modules
    assert dense._canonical_torch_device_name("cuda") == "cuda:0"
    assert quimb_worker._canonical_torch_device_name("cuda") == "cuda:0"
    assert dense._canonical_torch_device_name("cpu") == "cpu"
    assert quimb_worker._canonical_torch_device_name("cpu") == "cpu"


def test_d3_independent_dense_routes_and_controls_trip(modules) -> None:
    emitter, dense, _quimb_worker, _pepsy_worker, _comparison = modules
    fixture = emitter.build_fixture(size=3)
    torch_state, diagnostics = dense.evolve_torch(
        fixture,
        device_name="cpu",
        progress_every=0,
    )
    numpy_state = dense.evolve_numpy_bit_index(fixture)

    assert diagnostics["max_gate_unitarity_residual"] <= 1e-12
    assert diagnostics["norm_residual"] <= 1e-12
    assert np.max(np.abs(torch_state - numpy_state)) <= 1e-12
    assert 1.0 - dense.normalized_fidelity(torch_state, numpy_state) <= 1e-12

    global_phase = np.exp(0.731j) * numpy_state
    assert (
        abs(dense.normalized_fidelity(torch_state, global_phase) - 1.0)
        <= 1e-12
    )

    axes_swapped = (
        numpy_state.reshape((2,) * 9)
        .swapaxes(4, 5)
        .reshape(-1)
    )
    assert dense.normalized_fidelity(torch_state, axes_swapped) < 1.0 - 1e-4

    sign_flipped = copy.deepcopy(fixture)
    changed = next(
        operation
        for operation in sign_flipped["operations"]
        if operation["kind"] == "PAULI_ROTATION"
        and operation["cycle"] == 2
        and operation["targets"] == [3, 4]
    )
    changed["angle_rad"] = str(-float(changed["angle_rad"]))
    corrupted_state = dense.evolve_numpy_bit_index(sign_flipped)
    assert (
        dense.normalized_fidelity(torch_state, corrupted_state)
        < 1.0 - 1e-4
    )


def test_dense_worker_is_independent_and_proxy_firewall_is_explicit() -> None:
    dense_source = DENSE_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "import quimb",
        "import pepsy",
        "import yastn",
        "CircuitPEPSSimpleUpdate",
        "PepsOptimizer",
    ):
        assert forbidden not in dense_source

    quimb_source = QUIMB_PATH.read_text(encoding="utf-8")
    assert "EXPECTED_QUIMB_COMMIT" in quimb_source
    assert "--max-bond" in quimb_source
    assert "cutoff=0.0" in quimb_source
    assert "GAUGE_SMUDGE = 1e-12" in quimb_source
    assert ".to_dense(" in quimb_source
    assert "get_fidelities" not in quimb_source
    assert "discarded" not in quimb_source

    pepsy_source = PEPSY_PATH.read_text(encoding="utf-8")
    assert "complete_complex128_state_vector" in pepsy_source
    assert "_validated_numpy_gate" in pepsy_source
    assert "get_fidelities" not in pepsy_source

    comparison_source = COMPARE_PATH.read_text(encoding="utf-8")
    assert "normalized_fidelity_chunked" in comparison_source
    assert "complete state" in comparison_source
    assert "get_fidelities" not in comparison_source
    assert "retained-weight" in comparison_source

    runner_source = RUNNER_PATH.read_text(encoding="utf-8")
    assert "BONDS = (1, 2, 4, 8, 16)" in runner_source
    assert "POINT_TIMEOUT_SECONDS = 1800" in runner_source
    assert "HOST_LIMIT_BYTES = 64 * 1024**3" in runner_source
    assert "DEVICE_LIMIT_BYTES = 28 * 1024**3" in runner_source
    assert "peps_d5_physical_corruption_control.py" in runner_source
    assert "--controls-only" in runner_source
    assert "_run_d3_integration_controls" in runner_source

    corruption_source = CORRUPTION_CONTROL_PATH.read_text(encoding="utf-8")
    assert 'fixture["operations"][156]' in corruption_source
    assert '"angle_rad"] = "-0.31"' in corruption_source
    assert "fidelity_drop > 1e-4" in corruption_source


def test_workers_reject_unpinned_d5_fixture(
    modules,
    tmp_path: Path,
) -> None:
    emitter, dense, quimb_worker, pepsy_worker, _comparison = modules
    fixture = emitter.build_fixture(size=5)
    fixture["operations"][0]["targets"] = [0]
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")

    with pytest.raises(ValueError, match="semantic mismatch"):
        dense._read_fixture(path)
    with pytest.raises(ValueError, match="semantic mismatch"):
        quimb_worker._read_fixture(path)
    with pytest.raises(ValueError, match="semantic mismatch"):
        pepsy_worker._read_fixture(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _summary(
    *,
    schema: str,
    fixture: dict,
    state_path: Path,
) -> dict:
    comparison = sys.modules[
        "compare_peps_d5_complete_states_under_test"
    ]
    emitter = sys.modules["emit_peps_d5_pure_state_fixture"]
    policy = comparison.SCHEMA_PROVENANCE_POLICIES[schema]
    state = np.load(state_path, allow_pickle=False)
    candidate = schema != (
        "error_coupling_simulator.external.peps_d5_dense_reference.v1"
    )
    payload = {
        "schema": schema,
        "status": "completed",
        "claim_boundary": fixture["claim_boundary"],
        "fixture": {
            "schema": fixture["schema"],
            "distance_label": fixture["distance_label"],
            "operation_count": fixture["operation_count"],
            "canonical_sha256": emitter.canonical_sha256(fixture),
        },
        "state": {
            "path": str(state_path.resolve()),
            "file_sha256": _sha256(state_path),
            "shape": list(state.shape),
            "dtype": str(state.dtype),
            "source_kind": "complete_complex128_state_vector",
            "amplitude_convention": fixture["amplitude_convention"],
        },
        "diagnostics": {
            "norm_residual": 0.0,
            "max_gate_unitarity_residual": 0.0,
            "max_gate_semantic_residual": 0.0,
            **({"requested_max_bond": 4} if candidate else {}),
        },
        "provenance": {
            "git_head": subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=REPO,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "worker_path": str((REPO / policy["worker"]).resolve()),
            "worker_sha256": _sha256(REPO / policy["worker"]),
            "committed_input_sha256": {
                relative: _sha256(REPO / relative)
                for relative in policy["committed_inputs"]
            },
        },
    }
    if candidate:
        lock_path = REPO / policy["environment_lock"]
        commit = policy["source_commit"]
        payload["environment_lock"] = {
            "path": str(lock_path.resolve()),
            "file_sha256": _sha256(lock_path),
            "schema": policy["environment_lock_schema"],
            "environment_name": policy["environment_name"],
        }
        payload[policy["source_key"]] = {
            "commit": commit,
            "clean_including_ignored": True,
        }
        payload[policy["installed_key"]] = {
            "direct_url": {"vcs_info": {"commit_id": commit}},
        }
    return payload


def test_complete_state_metric_formula_phase_and_axis_controls(
    modules,
) -> None:
    emitter, dense, _quimb_worker, _pepsy_worker, comparison = modules
    fixture = emitter.build_fixture(size=3)
    reference = dense.evolve_numpy_bit_index(fixture)
    phase_state = np.exp(0.731j) * reference
    swapped_state = (
        reference.reshape((2,) * 9).swapaxes(4, 5).reshape(-1)
    )
    phase_result = comparison.normalized_fidelity_chunked(
        reference,
        phase_state,
        chunk_amplitudes=37,
    )
    assert (
        abs(
            phase_result["normalized_squared_overlap"] - 1.0
        )
        <= 1e-12
    )
    swapped_result = comparison.normalized_fidelity_chunked(
        reference,
        swapped_state,
        chunk_amplitudes=37,
    )
    assert (
        swapped_result["normalized_squared_overlap"]
        < 1.0 - 1e-4
    )


def test_complete_state_metric_rejects_dtype_nonfinite_and_proxy(
    modules,
    tmp_path: Path,
) -> None:
    _emitter, _dense, _quimb_worker, _pepsy_worker, comparison = modules
    complex64 = np.ones(512, dtype=np.complex64)
    with pytest.raises(ValueError, match="complex128"):
        comparison.normalized_fidelity_chunked(complex64, complex64)

    nonfinite = np.ones(512, dtype=np.complex128)
    nonfinite[7] = np.nan + 0.0j
    with pytest.raises(ValueError, match="non-finite"):
        comparison.normalized_fidelity_chunked(nonfinite, nonfinite)

    proxy_path = tmp_path / "proxy.npy"
    proxy_state = np.ones(512, dtype=np.complex128)
    np.save(proxy_path, proxy_state)
    proxy_summary = {
        "state": {
            "path": str(proxy_path.resolve()),
            "file_sha256": _sha256(proxy_path),
            "shape": [512],
            "dtype": "complex128",
            "source_kind": "retained_weight_product",
        },
    }
    with pytest.raises(ValueError, match="source_kind"):
        comparison._resolve_complete_state(proxy_summary)


def test_complete_state_metric_matches_analytic_unnormalized_pair(
    modules,
) -> None:
    _emitter, _dense, _quimb_worker, _pepsy_worker, comparison = modules
    left = np.asarray([1.0 + 1.0j, 2.0, 0.0], dtype=np.complex128)
    right = np.asarray([1.0, 0.0, 1.0j], dtype=np.complex128)
    overlap = np.vdot(left, right)
    expected = float(
        abs(overlap) ** 2
        / (float(np.vdot(left, left).real) * float(np.vdot(right, right).real))
    )
    assert expected == pytest.approx(1.0 / 6.0, abs=1e-15)
    assert abs(expected - np.sqrt(expected)) > 0.1
    measured = comparison.normalized_fidelity_chunked(
        left,
        right,
        chunk_amplitudes=2,
    )
    assert measured["normalized_squared_overlap"] == pytest.approx(
        expected,
        abs=1e-15,
    )
    rescaled = comparison.normalized_fidelity_chunked(
        (3.1 - 0.7j) * left,
        (-2.3 + 1.9j) * right,
        chunk_amplitudes=2,
    )
    assert rescaled["normalized_squared_overlap"] == pytest.approx(
        expected,
        abs=1e-15,
    )


def test_comparator_rejects_failed_diagnostics_and_bond(modules) -> None:
    _emitter, _dense, _quimb_worker, _pepsy_worker, comparison = modules
    reference = {
        "diagnostics": {
            "norm_residual": 0.0,
            "max_gate_unitarity_residual": 0.0,
            "max_gate_semantic_residual": 0.0,
        }
    }
    candidate = {
        "diagnostics": {
            "requested_max_bond": 4,
            "max_gate_unitarity_residual": 0.0,
            "max_gate_semantic_residual": 0.0,
        }
    }
    comparison._validate_execution_diagnostics(reference, candidate)
    failed_gate = copy.deepcopy(candidate)
    failed_gate["diagnostics"]["max_gate_unitarity_residual"] = 1e-6
    with pytest.raises(ValueError, match="candidate gate unitarity"):
        comparison._validate_execution_diagnostics(reference, failed_gate)

    excessive_bond = copy.deepcopy(candidate)
    excessive_bond["diagnostics"]["requested_max_bond"] = 17
    with pytest.raises(ValueError, match="outside"):
        comparison._validate_execution_diagnostics(reference, excessive_bond)


@pytest.mark.parametrize(
    "candidate_schema",
    (
        "error_coupling_simulator.external.quimb_peps_d5_state.v1",
        "error_coupling_simulator.external.pepsy_peps_d5_state.v1",
    ),
)
def test_comparator_accepts_each_schema_owned_complete_summary(
    modules,
    tmp_path: Path,
    candidate_schema: str,
) -> None:
    emitter, _dense, _quimb_worker, _pepsy_worker, comparison = modules
    fixture = emitter.build_fixture(size=3)
    state_path = tmp_path / "state.npy"
    np.save(state_path, np.ones(512, dtype=np.complex128))
    reference = _summary(
        schema=comparison.REFERENCE_SCHEMA,
        fixture=fixture,
        state_path=state_path,
    )
    candidate = _summary(
        schema=candidate_schema,
        fixture=fixture,
        state_path=state_path,
    )
    reference_path = tmp_path / "reference.json"
    candidate_path = tmp_path / "candidate.json"
    reference_path.write_text(json.dumps(reference))
    candidate_path.write_text(json.dumps(candidate))
    result = comparison.compare_summaries(
        reference_path,
        candidate_path,
        chunk_amplitudes=64,
    )
    assert result["metric"]["normalized_squared_overlap"] == 1.0


@pytest.mark.parametrize(
    "candidate_schema",
    (
        "error_coupling_simulator.external.quimb_peps_d5_state.v1",
        "error_coupling_simulator.external.pepsy_peps_d5_state.v1",
    ),
)
def test_comparator_rejects_provenance_forgery(
    modules,
    tmp_path: Path,
    candidate_schema: str,
) -> None:
    emitter, _dense, _quimb_worker, _pepsy_worker, comparison = modules
    fixture = emitter.build_fixture(size=3)
    state_path = tmp_path / "state.npy"
    np.save(state_path, np.ones(512, dtype=np.complex128))
    candidate = _summary(
        schema=candidate_schema,
        fixture=fixture,
        state_path=state_path,
    )

    forged_lock = copy.deepcopy(candidate)
    forged_lock["environment_lock"]["file_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="environment-lock hash mismatch"):
        comparison._validate_worker_provenance(forged_lock)

    wrong_worker = copy.deepcopy(candidate)
    wrong_worker["provenance"]["worker_path"] = str(COMPARE_PATH.resolve())
    wrong_worker["provenance"]["worker_sha256"] = _sha256(COMPARE_PATH)
    with pytest.raises(ValueError, match="schema-owned worker"):
        comparison._validate_worker_provenance(wrong_worker)

    incomplete_ledger = copy.deepcopy(candidate)
    incomplete_ledger["provenance"]["committed_input_sha256"].pop(
        next(
            iter(
                incomplete_ledger["provenance"][
                    "committed_input_sha256"
                ]
            )
        )
    )
    with pytest.raises(ValueError, match="ledger is incomplete"):
        comparison._validate_worker_provenance(incomplete_ledger)

    wrong_head = copy.deepcopy(candidate)
    wrong_head["provenance"]["git_head"] = "0" * 40
    with pytest.raises(ValueError, match="not the frozen HEAD"):
        comparison._validate_worker_provenance(wrong_head)

    arbitrary_lock_path = tmp_path / "arbitrary.lock.json"
    arbitrary_lock_path.write_text('{"synthetic":true}\n')
    arbitrary_lock = copy.deepcopy(candidate)
    arbitrary_lock["environment_lock"]["path"] = str(
        arbitrary_lock_path.resolve()
    )
    arbitrary_lock["environment_lock"]["file_sha256"] = _sha256(
        arbitrary_lock_path
    )
    with pytest.raises(ValueError, match="path is not schema-owned"):
        comparison._validate_worker_provenance(arbitrary_lock)


def test_comparator_rejects_equal_but_unpinned_fixture_hash(modules) -> None:
    emitter, _dense, _quimb_worker, _pepsy_worker, comparison = modules
    fixture = emitter.build_fixture(size=3)
    convention = fixture["amplitude_convention"]
    base = {
        "claim_boundary": fixture["claim_boundary"],
        "fixture": {
            "schema": fixture["schema"],
            "distance_label": 3,
            "operation_count": 88,
            "canonical_sha256": "0" * 64,
        },
        "state": {
            "shape": [512],
            "amplitude_convention": convention,
        },
    }
    with pytest.raises(ValueError, match="pinned canonical_sha256"):
        comparison._validate_fixture_binding(base, copy.deepcopy(base))


def test_terminal_sweep_owner_classifies_controls_without_proxy() -> None:
    runner = _load_script(
        RUNNER_PATH,
        "run_peps_d5_complete_state_sweeps_under_test",
    )
    rows = [
        {
            "bond": bond,
            "status": "completed",
            "fidelity": fidelity,
            "no_rank_discarded": None,
        }
        for bond, fidelity in zip(
            runner.BONDS,
            (0.81, 0.93, 0.981, 0.995, 0.999),
        )
    ]
    result = runner._summarize_candidate(rows)
    assert result["usefulness_verdict"] == "pass"
    assert result["best_bond"] == 16
    assert result["monotonic_prediction"] == {
        "evaluable": True,
        "passed": True,
        "tolerance": 1e-8,
    }
    assert result["bond_knob_nondegeneracy"]["passed"] is True
    assert result["d16_exact_representation_prediction"] == {
        "evaluable": False,
        "reason_if_not_evaluable": (
            "candidate_has_no_authenticated_no_rank_discarded_ledger"
        ),
        "passed": None,
    }

    nonmonotonic = copy.deepcopy(rows)
    nonmonotonic[3]["fidelity"] = 0.90
    assert (
        runner._summarize_candidate(nonmonotonic)[
            "monotonic_prediction"
        ]["passed"]
        is False
    )
