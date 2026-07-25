"""Contract tests for the isolated ITensorMPS third comparison leg.

Every test here runs inside the ordinary ``ecs`` environment with no Julia
present: the point of the neutral protocol is that the external-process seam is
checkable without the external runtime.  The opt-in integration run that does
require Julia is gated behind ``ECS_RUN_ITENSOR_MPS_COMPARISON=1`` and is not
part of the default surface.

These are seam and contract tests. They make no scientific claim about MPS
truncation; the comparison report produced by the orchestrator does that.
"""

from __future__ import annotations

import ast
import copy
import json
import math
import os
from pathlib import Path
import sys

import pytest

REPO = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = REPO / "scripts" / "external_baselines" / "itensor_mps_protocol.py"
sys.path.insert(0, str(PROTOCOL_PATH.parent))

import itensor_mps_protocol as protocol  # noqa: E402


def _request(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": protocol.REQUEST_SCHEMA,
        "execution_id": "bell_full_rank",
        "seed": 0,
        "cutoff": 1e-16,
        "max_bond_dimension": None,
        "amplitude_ordering": protocol.AMPLITUDE_ORDERING,
        "circuit": {
            "id": "bell_chain",
            "qubits": 3,
            "operations": [
                {"gate": "h", "targets": [0], "parameters": []},
                {"gate": "cx", "targets": [0, 1], "parameters": []},
                {"gate": "ry", "targets": [2], "parameters": [0.37]},
                {"gate": "cz", "targets": [1, 2], "parameters": []},
            ],
        },
    }
    payload.update(overrides)
    return payload


def _result(request: dict[str, object], **overrides: object) -> dict[str, object]:
    qubits = int(request["circuit"]["qubits"])  # type: ignore[index]
    amplitudes = [complex(0.0, 0.0)] * (2**qubits)
    amplitudes[0] = complex(1.0, 0.0)
    payload: dict[str, object] = {
        "schema": protocol.RESULT_SCHEMA,
        "request_sha256": protocol.canonical_json_sha256(request),
        "execution_id": request["execution_id"],
        "circuit_id": request["circuit"]["id"],  # type: ignore[index]
        "runtime": {
            "julia_version": "1.11.3",
            "active_project": "/home/cx/miniforge3/envs/ecs-baseline-itensor/share/julia",
            "itensormps_version": "0.4.1",
            "itensormps_tree_hash": "0" * 40,
            "itensormps_source_path": "/home/cx/AI_QEC/AI_QEC/external/baselines/ITensorMPS.jl",
            "manifest_sha256": "1" * 64,
            "source_anchor_sha256": {name: "2" * 64 for name in protocol.ITENSOR_SOURCE_ANCHORS},
        },
        "configuration": {
            "cutoff": request["cutoff"],
            "max_bond_dimension": request["max_bond_dimension"],
            "seed": request["seed"],
            "amplitude_ordering": protocol.AMPLITUDE_ORDERING,
            "orthogonalized": True,
        },
        "statevector": protocol.encode_complex_vector(amplitudes),
        "statevector_norm_squared": 1.0,
        "mps": {
            "bond_dimensions": [1] * (qubits - 1),
            "schmidt_values": [[1.0] for _ in range(qubits - 1)],
            "schmidt_convention": protocol.SCHMIDT_CONVENTION,
            "discarded_weight": [0.0] * (qubits - 1),
        },
    }
    payload.update(overrides)
    return payload


def test_protocol_module_imports_only_the_standard_library() -> None:
    tree = ast.parse(PROTOCOL_PATH.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "the protocol must not use relative imports"
            assert node.module is not None
            imported.add(node.module.split(".", 1)[0])
    assert imported <= set(sys.stdlib_module_names)
    assert not any(name.startswith("error_coupling_simulator") for name in imported)


def test_schema_names_follow_the_current_artifact_convention() -> None:
    for schema in (protocol.REQUEST_SCHEMA, protocol.RESULT_SCHEMA, protocol.REPORT_SCHEMA):
        assert schema.startswith("error_coupling_simulator.external_itensor_mps.")
        assert schema.endswith(".v1")


def test_amplitude_ordering_is_pinned_to_the_aer_convention() -> None:
    # A leg that silently disagrees on bit ordering looks green at full rank.
    assert protocol.AMPLITUDE_ORDERING == "little_endian_qubit0_fastest"
    with pytest.raises(ValueError, match="amplitude_ordering"):
        protocol.validate_request(_request(amplitude_ordering="big_endian"))


def test_valid_request_round_trips_and_is_owned_by_the_caller() -> None:
    payload = _request()
    validated = protocol.validate_request(payload)
    assert validated == payload
    validated["seed"] = 99
    assert payload["seed"] == 0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("schema", "error_coupling_simulator.external_itensor_mps.request.v2", "schema"),
        ("execution_id", "Bad-Id", "execution_id"),
        ("seed", -1, "seed"),
        ("cutoff", -1e-9, "cutoff"),
        ("cutoff", float("inf"), "cutoff"),
        ("max_bond_dimension", 0, "max_bond_dimension"),
        ("max_bond_dimension", True, "max_bond_dimension"),
    ],
)
def test_request_validation_rejects_malformed_fields(
    field: str, value: object, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        protocol.validate_request(_request(**{field: value}))


def test_request_validation_rejects_unknown_and_missing_keys() -> None:
    extra = _request()
    extra["unexpected"] = 1
    with pytest.raises(ValueError, match="request keys differ"):
        protocol.validate_request(extra)
    missing = _request()
    del missing["seed"]
    with pytest.raises(ValueError, match="request keys differ"):
        protocol.validate_request(missing)


@pytest.mark.parametrize(
    "operation",
    [
        {"gate": "toffoli", "targets": [0, 1, 2], "parameters": []},
        {"gate": "cx", "targets": [0], "parameters": []},
        {"gate": "cx", "targets": [1, 1], "parameters": []},
        {"gate": "ry", "targets": [0], "parameters": []},
        {"gate": "h", "targets": [7], "parameters": []},
        {"gate": "ry", "targets": [0], "parameters": [float("nan")]},
    ],
)
def test_circuit_validation_rejects_malformed_operations(operation: dict) -> None:
    payload = _request()
    payload["circuit"]["operations"] = [operation]  # type: ignore[index]
    with pytest.raises(ValueError):
        protocol.validate_request(payload)


def test_result_validation_accepts_a_well_formed_synthetic_result() -> None:
    request = protocol.validate_request(_request())
    protocol.validate_result(_result(request), request)


def test_result_must_reference_the_exact_request() -> None:
    request = protocol.validate_request(_request())
    tampered = _result(request, request_sha256="0" * 64)
    with pytest.raises(ValueError, match="request hash"):
        protocol.validate_result(tampered, request)


def test_result_rejects_a_provenance_free_runtime() -> None:
    request = protocol.validate_request(_request())
    result = _result(request)
    runtime = copy.deepcopy(result["runtime"])
    assert isinstance(runtime, dict)
    runtime["itensormps_tree_hash"] = "not-a-tree-hash"
    with pytest.raises(ValueError, match="tree hash"):
        protocol.validate_result(_result(request, runtime=runtime), request)


def test_result_requires_every_pinned_upstream_source_anchor() -> None:
    request = protocol.validate_request(_request())
    result = _result(request)
    runtime = copy.deepcopy(result["runtime"])
    assert isinstance(runtime, dict)
    anchors = dict(runtime["source_anchor_sha256"])
    anchors.pop(protocol.ITENSOR_SOURCE_ANCHORS[0])
    runtime["source_anchor_sha256"] = anchors
    with pytest.raises(ValueError, match="source anchors differ"):
        protocol.validate_result(_result(request, runtime=runtime), request)


def test_result_requires_an_orthogonalized_state_for_schmidt_meaning() -> None:
    request = protocol.validate_request(_request())
    configuration = dict(_result(request)["configuration"])  # type: ignore[arg-type]
    configuration["orthogonalized"] = False
    with pytest.raises(ValueError, match="orthogonalized"):
        protocol.validate_result(_result(request, configuration=configuration), request)


def test_schmidt_spectrum_must_match_its_retained_bond_dimension() -> None:
    request = protocol.validate_request(_request())
    mps = copy.deepcopy(_result(request)["mps"])
    assert isinstance(mps, dict)
    mps["bond_dimensions"] = [2, 1]
    with pytest.raises(ValueError, match="exactly 2 values"):
        protocol.validate_result(_result(request, mps=mps), request)


def test_schmidt_convention_must_be_stated_and_squared() -> None:
    # ITensor reports squared Schmidt coefficients; assuming otherwise is a
    # silent square-factor disagreement.
    assert "squared" in protocol.SCHMIDT_CONVENTION
    request = protocol.validate_request(_request())
    mps = copy.deepcopy(_result(request)["mps"])
    assert isinstance(mps, dict)
    mps["schmidt_convention"] = "schmidt_coefficients"
    with pytest.raises(ValueError, match="schmidt_convention"):
        protocol.validate_result(_result(request, mps=mps), request)


def test_schmidt_spectrum_must_be_non_increasing() -> None:
    request = protocol.validate_request(_request())
    mps = copy.deepcopy(_result(request)["mps"])
    assert isinstance(mps, dict)
    mps["bond_dimensions"] = [2, 1]
    mps["schmidt_values"] = [[0.1, 0.9], [1.0]]
    with pytest.raises(ValueError, match="non-increasing"):
        protocol.validate_result(_result(request, mps=mps), request)


def test_statevector_length_must_match_the_register() -> None:
    request = protocol.validate_request(_request())
    short = protocol.encode_complex_vector([complex(1.0, 0.0)] * 4)
    with pytest.raises(ValueError, match="does not match"):
        protocol.validate_result(_result(request, statevector=short), request)


def test_reported_norm_must_agree_with_the_encoded_amplitudes() -> None:
    request = protocol.validate_request(_request())
    with pytest.raises(ValueError, match="norm_squared disagrees"):
        protocol.validate_result(_result(request, statevector_norm_squared=0.5), request)


def test_fidelity_and_phase_aligned_distance_ignore_global_phase() -> None:
    left = [complex(0.6, 0.0), complex(0.8, 0.0)]
    right = [value * complex(0.0, 1.0) for value in left]
    assert protocol.state_fidelity(left, right) == pytest.approx(1.0, abs=1e-15)
    assert protocol.phase_aligned_l2(left, right) == pytest.approx(0.0, abs=1e-15)


def test_complex_vector_encoding_round_trips_and_rejects_non_finite() -> None:
    values = [complex(0.5, -0.25), complex(-1.0, 0.0)]
    assert protocol.decode_complex_vector(protocol.encode_complex_vector(values)) == values
    with pytest.raises(ValueError, match="finite"):
        protocol.decode_complex_vector([[float("inf"), 0.0]])
    with pytest.raises(ValueError, match="pair"):
        protocol.decode_complex_vector([[1.0]])


def test_atomic_write_publishes_a_stable_digest(tmp_path: Path) -> None:
    payload = {"schema": protocol.REPORT_SCHEMA, "value": 1}
    destination = tmp_path / "report.json"
    digest = protocol.atomic_write_json(destination, payload)
    assert digest == protocol.canonical_json_sha256(payload)
    assert protocol.read_json_object(destination) == payload
    assert not list(tmp_path.glob(".report.json.*"))
    assert protocol.atomic_write_json(destination, payload) == digest


def test_report_content_digest_excludes_its_own_field() -> None:
    body = {"schema": protocol.REPORT_SCHEMA, "value": 2}
    report = dict(body)
    report["content_sha256"] = protocol.report_content_sha256(body)
    assert protocol.report_content_sha256(report) == report["content_sha256"]


def test_upstream_clone_is_pinned_and_present() -> None:
    clone = REPO / "external" / "baselines" / "ITensorMPS.jl"
    assert clone.is_dir(), "the pristine ITensorMPS clone must be vendored"
    for anchor in protocol.ITENSOR_SOURCE_ANCHORS:
        assert (clone / anchor).is_file(), f"pinned source anchor missing: {anchor}"
    assert protocol.EXPECTED_ITENSOR_COMMIT


@pytest.mark.skipif(
    os.environ.get("ECS_RUN_ITENSOR_MPS_COMPARISON") != "1",
    reason="opt-in isolated run; requires the ecs-baseline-itensor Julia environment",
)
def test_isolated_itensor_comparison_runs(tmp_path: Path) -> None:
    """Run the real leg: Julia worker in a fresh process against a dense reference."""

    import subprocess

    report_path = tmp_path / "itensor_comparison.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "external_baselines" / "run_itensor_mps_comparison.py"),
            "--output", str(report_path),
            "--workspace", str(tmp_path / "workspace"),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=3600,
    )
    assert completed.returncode == 0, (
        f"itensor comparison failed:\n{completed.stdout[-4000:]}\n{completed.stderr[-4000:]}"
    )
    report = protocol.read_json_object(report_path)
    assert report["schema"] == protocol.REPORT_SCHEMA
    assert report["content_sha256"] == protocol.report_content_sha256(report)
    assert report["amplitude_ordering"] == protocol.AMPLITUDE_ORDERING
    assert report["schmidt_convention"] == protocol.SCHMIDT_CONVENTION
    assert report["provenance"]["clone_pristine_including_ignored"] is True

    # A leg that agrees with everything is indistinguishable from one that agrees
    # with the truth, so the deliberate corruption must have been caught.
    assert report["falsifier"]["caught"] is True

    # Full rank must reproduce the independent dense reference exactly; only then
    # is a capped row's damage attributable to truncation rather than convention.
    full_rank = [row for row in report["rows"] if row["bond_policy"] == "full_rank"]
    assert full_rank, "no full-rank row was scored"
    for row in full_rank:
        assert row["full_rank_reproduces_reference"] is True
        assert row["fidelity"] >= report["full_rank_min_fidelity"]
        assert row["total_discarded_weight"] == pytest.approx(0.0, abs=1e-12)

    # The canonical-split ledger is the payload this leg exists to expose.
    capped = [row for row in report["rows"] if row["bond_policy"] == "cap_1"]
    assert capped, "no capped row was scored"
    for row in capped:
        assert row["max_bond_dimension_observed"] == 1
        assert row["fidelity"] < 1.0
        assert row["total_discarded_weight"] > 0.0
