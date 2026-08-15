"""Pure contract tests plus an opt-in isolated Aer MPS integration run."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = REPO / "scripts" / "external_baselines"
sys.path.insert(0, str(SCRIPT_ROOT))

import aer_mps_protocol as protocol  # noqa: E402
import aer_mps_worker as worker  # noqa: E402
import run_aer_mps_comparison as comparison  # noqa: E402


def _runtime_identity() -> dict:
    prefix = "/isolated/envs/ecs-baseline-aer"
    distribution_root = f"{prefix}/lib/python3.11/site-packages"
    return {
        "python_version": "3.11.0",
        "python_executable": f"{prefix}/bin/python",
        "python_prefix": prefix,
        "python_executable_within_prefix": True,
        "qiskit_version": "2.2.0",
        "qiskit_aer_version": comparison.EXPECTED_AER_VERSION,
        "qiskit_aer_module_file": f"{distribution_root}/qiskit_aer/__init__.py",
        "qiskit_aer_direct_url": None,
        "qiskit_aer_installation_source": "pip_distribution_without_direct_url",
        "qiskit_aer_import_matches_distribution": True,
        "qiskit_aer_distribution": {
            "name": "qiskit-aer",
            "version": comparison.EXPECTED_AER_VERSION,
            "installer": "pip",
            "root": distribution_root,
            "record_path": f"{distribution_root}/qiskit_aer.dist-info/RECORD",
            "record_sha256": "a" * 64,
            "selected_package_sha256": {
                "qiskit_aer/__init__.py": "d" * 64,
                "qiskit_aer/backends/aer_simulator.py": "b" * 64,
                "qiskit_aer/backends/controller_wrappers.test.so": "c" * 64,
            },
        },
    }


def _synthetic_result(request: dict) -> dict:
    circuit = request["circuit"]
    state = comparison.dense_reference(circuit)
    num_qubits = circuit["num_qubits"]
    is_cap1 = request["max_bond_dimension"] == 1
    if is_cap1 and circuit["id"] == "bell_adjacent_4":
        state = [1.0 + 0.0j] + [0.0j] * ((1 << num_qubits) - 1)
    bond_text = " ".join("1" for _ in range(num_qubits - 1))
    two_qubit_count = sum(len(gate["qubits"]) == 2 for gate in circuit["gates"])
    log_segments = []
    for index in range(two_qubit_count):
        discard_fragment = "discarded_value=0.5, " if is_cap1 and index == 0 else ""
        log_segments.append(
            f"I{index}:cx on qubits 0,1, {discard_fragment}BD=[{bond_text}],  "
        )
    raw_log = "{" + "".join(log_segments) + "}"
    return {
        "schema": protocol.RESULT_SCHEMA,
        "request_sha256": protocol.canonical_json_sha256(request),
        "execution_id": request["execution_id"],
        "circuit_id": circuit["id"],
        "runtime": _runtime_identity(),
        "configuration": {
            "method": "matrix_product_state",
            "device": "CPU",
            "seed_simulator": request["seed"],
            "truncation_threshold": request["truncation_threshold"],
            "max_bond_dimension": request["max_bond_dimension"],
            "mps_log_data": True,
            "mps_swap_direction": "mps_swap_left",
            "mps_lapack": False,
            "sample_measure_algorithm": "mps_apply_measure",
            "chop_threshold": 0.0,
            "shots": 1,
        },
        "statevector": protocol.encode_complex_vector(state),
        "statevector_norm_squared": protocol.vector_norm_squared(state),
        "mps": {
            "num_sites": num_qubits,
            "site_tensor_shapes": [
                [[1, 1], [1, 1]] for _ in range(num_qubits)
            ],
            "bond_dimensions": [1] * (num_qubits - 1),
            "schmidt_values": [[1.0] for _ in range(num_qubits - 1)],
        },
        "mps_log": protocol.parse_mps_log(raw_log),
        "simulator_metadata": {
            "method": "matrix_product_state",
            "device": "CPU",
            "matrix_product_state_truncation_threshold": request[
                "truncation_threshold"
            ],
            "matrix_product_state_max_bond_dimension": (
                request["max_bond_dimension"]
                if request["max_bond_dimension"] is not None
                else (1 << 64) - 1
            ),
            "matrix_product_state_sample_measure_algorithm": 0,
            "matrix_product_state_lapack": False,
        },
    }


def test_fixture_surface_is_deterministic_and_covers_required_gate_shapes() -> None:
    first = comparison.execution_requests()
    second = comparison.execution_requests()
    assert first == second
    assert len(first) == 5 * len(comparison.BOND_POLICIES)
    assert len({request["execution_id"] for request in first}) == len(first)
    assert [
        protocol.canonical_json_sha256(request) for request in first
    ] == [protocol.canonical_json_sha256(request) for request in second]

    circuits = comparison.comparison_circuits()
    assert {circuit["num_qubits"] for circuit in circuits} == {4, 5, 6}
    assert any("bell_like" in circuit["tags"] for circuit in circuits)
    assert any(
        abs(gate["qubits"][0] - gate["qubits"][1]) == 1
        for circuit in circuits
        for gate in circuit["gates"]
        if len(gate["qubits"]) == 2
    )
    assert any(
        abs(gate["qubits"][0] - gate["qubits"][1]) > 1
        for circuit in circuits
        for gate in circuit["gates"]
        if len(gate["qubits"]) == 2
    )
    assert comparison._circuit_by_id("bell_gate_corruption_4")["falsifier_of"] == (
        "bell_adjacent_4"
    )


def test_dense_reference_pins_little_endian_bell_and_detects_gate_corruption() -> None:
    bell = comparison.dense_reference(comparison._circuit_by_id("bell_adjacent_4"))
    expected = [0.0j] * 16
    expected[0] = 1.0 / (2.0**0.5)
    expected[3] = 1.0 / (2.0**0.5)
    assert bell == pytest.approx(expected, abs=1.0e-15)

    corrupted = comparison.dense_reference(
        comparison._circuit_by_id("bell_gate_corruption_4")
    )
    assert protocol.state_fidelity(bell, corrupted) == pytest.approx(0.25, abs=1.0e-15)
    assert protocol.state_fidelity(bell, corrupted) <= comparison.FALSIFIER_MAX_FIDELITY


def test_state_metrics_ignore_global_phase_but_not_gate_corruption() -> None:
    state = [1.0 / (2.0**0.5), 1.0j / (2.0**0.5)]
    phased = [1.0j * value for value in state]
    assert protocol.state_fidelity(state, phased) == pytest.approx(1.0)
    assert protocol.phase_aligned_l2(state, phased) == pytest.approx(0.0, abs=1.0e-15)
    assert protocol.state_fidelity(state, [1.0, 0.0]) == pytest.approx(0.5)


def test_mps_log_parser_preserves_actual_discard_values_and_bond_history() -> None:
    parsed = protocol.parse_mps_log(
        "{discarded_value=5e-1, I0:cx on qubits 0,1, BD=[2 1 4],  "
        "discarded_value=1.25e-03, BD=[1 2 2],  }"
    )
    assert parsed["discarded_values"] == [0.5, 0.00125]
    assert parsed["discarded_value_sum"] == pytest.approx(0.50125)
    assert parsed["discarded_value_max"] == 0.5
    assert parsed["logged_bond_dimensions"] == [[2, 1, 4], [1, 2, 2]]
    for malformed in (
        "",
        "discarded_value=0.5, BD=[1 1]",
        "{discarded_value=nan, BD=[1 1]}",
        "{discarded_value=1e999, BD=[1 1]}",
        "{discarded_value=1x, BD=[1 1]}",
        "{discarded_value =0.5, BD=[1 1]}",
        "{discarded_value=0.5, BD=[1 nope]}",
        "{discarded_value=0.5, BD=[1 1}",
    ):
        with pytest.raises(ValueError):
            protocol.parse_mps_log(malformed)


def test_worker_import_and_neutral_result_validation_do_not_require_aer() -> None:
    assert "qiskit_aer" not in worker.__dict__
    request = comparison.execution_requests()[0]
    result = _synthetic_result(request)
    protocol.validate_result(result, request)

    corrupted = copy.deepcopy(result)
    corrupted["request_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="request hash"):
        protocol.validate_result(corrupted, request)

    wrong_static_configuration = copy.deepcopy(result)
    wrong_static_configuration["configuration"]["device"] = "GPU"
    with pytest.raises(ValueError, match="static configuration"):
        protocol.validate_result(wrong_static_configuration, request)

    missing_metadata = copy.deepcopy(result)
    missing_metadata["simulator_metadata"].pop("method")
    with pytest.raises(ValueError, match="simulator_metadata keys differ"):
        protocol.validate_result(missing_metadata, request)

    contradicted_metadata = copy.deepcopy(result)
    contradicted_metadata["simulator_metadata"]["device"] = "GPU"
    with pytest.raises(ValueError, match="CPU device"):
        protocol.validate_result(contradicted_metadata, request)

    wrong_actual_threshold = copy.deepcopy(result)
    wrong_actual_threshold["simulator_metadata"][
        "matrix_product_state_truncation_threshold"
    ] = 1.0e-16
    with pytest.raises(ValueError, match="truncation threshold"):
        protocol.validate_result(wrong_actual_threshold, request)

    wrong_actual_sample_mode = copy.deepcopy(result)
    wrong_actual_sample_mode["simulator_metadata"][
        "matrix_product_state_sample_measure_algorithm"
    ] = 3
    with pytest.raises(ValueError, match="APPLY_MEASURE=0"):
        protocol.validate_result(wrong_actual_sample_mode, request)

    missing_log_evidence = copy.deepcopy(result)
    missing_log_evidence["mps_log"] = protocol.parse_mps_log("{}")
    with pytest.raises(ValueError, match="missing per-gate"):
        protocol.validate_result(missing_log_evidence, request)


def test_analysis_is_fail_closed_on_distribution_capture_and_passes_corruption() -> None:
    requests = comparison.execution_requests()
    results = [_synthetic_result(request) for request in requests]
    for request, result in zip(requests, results, strict=True):
        protocol.validate_result(result, request)

    passing = comparison.analyze_results(
        requests,
        results,
        installed_distribution_evidence_captured=True,
    )
    assert passing["falsifier"]["detected"] is True
    assert passing["all_checks_passed"] is True

    hard_ids = ("nonadjacent_5", "mixed_entangling_6")
    for circuit_id in hard_ids:
        vacuous = copy.deepcopy(results)
        by_id = {result["execution_id"]: result for result in vacuous}
        cap1 = by_id[f"{circuit_id}_cap_1"]
        cap1["mps_log"] = protocol.parse_mps_log("{}")
        cap1["statevector"] = by_id[f"{circuit_id}_full_rank"]["statevector"]
        cap1["statevector_norm_squared"] = 1.0
        vacuous_analysis = comparison.analyze_results(
            requests,
            vacuous,
            installed_distribution_evidence_captured=True,
        )
        assert vacuous_analysis["checks"][f"{circuit_id}_cap1_is_nonvacuous"] is False
        other_id = next(candidate for candidate in hard_ids if candidate != circuit_id)
        assert vacuous_analysis["checks"][f"{other_id}_cap1_is_nonvacuous"] is True
        assert vacuous_analysis["all_checks_passed"] is False

    bell_vacuous = copy.deepcopy(results)
    bell_by_id = {result["execution_id"]: result for result in bell_vacuous}
    bell_by_id["bell_adjacent_4_cap_1"]["statevector"] = bell_by_id[
        "bell_adjacent_4_full_rank"
    ]["statevector"]
    bell_by_id["bell_adjacent_4_cap_1"]["mps_log"] = protocol.parse_mps_log("{}")
    bell_analysis = comparison.analyze_results(
        requests,
        bell_vacuous,
        installed_distribution_evidence_captured=True,
    )
    assert bell_analysis["checks"][
        "bell_cap1_has_expected_loss_discard_and_cap"
    ] is False

    missing_identity = comparison.analyze_results(
        requests,
        results,
        installed_distribution_evidence_captured=False,
    )
    assert missing_identity["checks"][
        "installed_aer_distribution_evidence_captured"
    ] is False
    assert missing_identity["all_checks_passed"] is False


def test_worker_command_and_committed_preflight_scope_are_explicit(tmp_path: Path) -> None:
    command = comparison.worker_command(
        "/opt/conda/bin/conda",
        tmp_path / "request.json",
        tmp_path / "result.json",
    )
    assert command[:5] == [
        "/opt/conda/bin/conda",
        "run",
        "-n",
        "ecs-baseline-aer",
        "python",
    ]
    assert "--input" in command and "--output" in command
    assert Path("tests/test_external_aer_mps_comparison.py") in (
        comparison.COMMITTED_SCRIPT_INPUTS
    )


def test_installed_distribution_capture_rejects_shadow_import_and_weak_hashes() -> None:
    runtime = _runtime_identity()
    assert comparison._installed_distribution_evidence_captured(runtime) is True

    shadow_import = copy.deepcopy(runtime)
    shadow_import["qiskit_aer_module_file"] = "/shadow/qiskit_aer/__init__.py"
    assert comparison._installed_distribution_evidence_captured(shadow_import) is False

    unproved_import = copy.deepcopy(runtime)
    unproved_import["qiskit_aer_import_matches_distribution"] = False
    assert comparison._installed_distribution_evidence_captured(unproved_import) is False

    nonhex_record = copy.deepcopy(runtime)
    nonhex_record["qiskit_aer_distribution"]["record_sha256"] = "z" * 64
    assert comparison._installed_distribution_evidence_captured(nonhex_record) is False

    direct_source = copy.deepcopy(runtime)
    direct_source["qiskit_aer_direct_url"] = {"url": "file:///tmp/qiskit-aer.whl"}
    direct_source["qiskit_aer_installation_source"] = "distribution_with_direct_url"
    assert comparison._installed_distribution_evidence_captured(direct_source) is False

    wrong_environment = copy.deepcopy(runtime)
    wrong_environment["python_prefix"] = "/isolated/envs/ecs"
    assert comparison._installed_distribution_evidence_captured(wrong_environment) is False


def test_atomic_json_is_exactly_reproducible(tmp_path: Path) -> None:
    payload = {"z": [1, 2], "a": {"value": 0.125}}
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first_hash = protocol.atomic_write_json(first, payload)
    second_hash = protocol.atomic_write_json(second, payload)
    assert first.read_bytes() == second.read_bytes()
    assert first_hash == second_hash
    assert json.loads(first.read_text(encoding="utf-8")) == payload


@pytest.mark.skipif(
    os.environ.get("ECS_RUN_AER_MPS_COMPARISON") != "1",
    reason="set ECS_RUN_AER_MPS_COMPARISON=1 for the isolated Aer integration run",
)
def test_optional_isolated_aer_mps_comparison(tmp_path: Path) -> None:
    report = comparison.run_comparison(tmp_path / "aer_mps_comparison.json")
    assert report["schema"] == protocol.REPORT_SCHEMA
    assert report["analysis"]["all_checks_passed"] is True
    assert all(
        row["group_cleanup_verified"]
        and not row["timed_out"]
        and row["returncode"] == 0
        for row in report["worker_execution_provenance"]
    )
