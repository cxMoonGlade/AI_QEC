#!/usr/bin/env python3
"""Run the deterministic, isolated Qiskit Aer MPS comparison.

This repo-owned orchestrator never imports Qiskit.  It writes a neutral JSON
request for each circuit/bond policy, launches one fresh
``ecs-baseline-aer`` process, validates the neutral response, and publishes a
single atomic comparison artifact.
"""

from __future__ import annotations

import argparse
import cmath
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Mapping, Sequence

from aer_mps_protocol import (
    REPORT_SCHEMA,
    REQUEST_SCHEMA,
    atomic_write_json,
    canonical_json_sha256,
    decode_complex_vector,
    encode_complex_vector,
    phase_aligned_l2,
    read_json_object,
    report_content_sha256,
    state_fidelity,
    validate_request,
    validate_result,
    vector_norm_squared,
)


REPO = Path(__file__).resolve().parents[2]
TESTS_ROOT = REPO / "tests"
WORKER = Path(__file__).with_name("aer_mps_worker.py")
BASELINE_REPO = REPO / "external" / "baselines" / "qiskit-aer"
EXTERNAL_ROOT = REPO / "external"
BASELINE_ENVIRONMENT = "ecs-baseline-aer"
EXPECTED_BASELINE_COMMIT = "837c3ef3c39248aae936580360c22224dcefb265"
EXPECTED_RELEASE_TAG = "0.17.2"
EXPECTED_RELEASE_TAG_COMMIT = "51c679814c3a292d0d7c59bb39976bd6ff91f60e"
EXPECTED_AER_VERSION = "0.17.2"
COMMITTED_SCRIPT_INPUTS = (
    Path("scripts/external_baselines/aer_mps_protocol.py"),
    Path("scripts/external_baselines/aer_mps_worker.py"),
    Path("scripts/external_baselines/run_aer_mps_comparison.py"),
    Path("tests/test_external_aer_mps_comparison.py"),
    Path("tests/harness/proc.py"),
)

SEED = 271_828
TRUNCATION_THRESHOLD = 0.0
BOND_POLICIES: tuple[tuple[str, int | None], ...] = (
    ("full_rank", None),
    ("cap_1", 1),
    ("cap_2", 2),
)

FULL_RANK_MIN_FIDELITY = 1.0 - 1.0e-12
FULL_RANK_MAX_PHASE_ALIGNED_L2 = 1.0e-10
MAX_NORM_ERROR = 1.0e-12
FALSIFIER_MAX_FIDELITY = 0.5
BELL_CAP1_EXPECTED_FIDELITY = 0.5
BELL_FIDELITY_ABS_TOLERANCE = 1.0e-12
HARD_CAP1_MIN_FIDELITY_LOSS = 1.0e-10


def _gate(name: str, *qubits: int, parameters: Sequence[float] = ()) -> dict[str, Any]:
    return {
        "name": name,
        "qubits": list(qubits),
        "parameters": [float(value) for value in parameters],
    }


def comparison_circuits() -> list[dict[str, Any]]:
    """Return frozen 4--6-qubit fixtures plus one gate-corruption falsifier."""

    return [
        {
            "id": "bell_adjacent_4",
            "num_qubits": 4,
            "tags": ["four_qubit", "bell_like", "adjacent_two_qubit"],
            "falsifier_of": None,
            "gates": [
                _gate("h", 0),
                _gate("cx", 0, 1),
            ],
        },
        {
            "id": "adjacent_chain_5",
            "num_qubits": 5,
            "tags": ["five_qubit", "adjacent_two_qubit"],
            "falsifier_of": None,
            "gates": [
                _gate("h", 0),
                _gate("cx", 0, 1),
                _gate("ry", 2, parameters=(0.61,)),
                _gate("cx", 1, 2),
                _gate("h", 3),
                _gate("cz", 2, 3),
                _gate("ry", 4, parameters=(-0.47,)),
                _gate("cx", 3, 4),
                _gate("rz", 1, parameters=(0.29,)),
            ],
        },
        {
            "id": "nonadjacent_5",
            "num_qubits": 5,
            "tags": ["five_qubit", "nonadjacent_two_qubit"],
            "falsifier_of": None,
            "gates": [
                _gate("ry", 0, parameters=(0.71,)),
                _gate("h", 2),
                _gate("cx", 0, 4),
                _gate("cz", 2, 4),
                _gate("ry", 1, parameters=(-0.33,)),
                _gate("cx", 1, 3),
                _gate("rz", 4, parameters=(0.19,)),
                _gate("cz", 0, 3),
            ],
        },
        {
            "id": "mixed_entangling_6",
            "num_qubits": 6,
            "tags": [
                "six_qubit",
                "adjacent_two_qubit",
                "nonadjacent_two_qubit",
            ],
            "falsifier_of": None,
            "gates": [
                _gate("h", 0),
                _gate("cx", 0, 1),
                _gate("ry", 2, parameters=(0.61,)),
                _gate("cx", 1, 2),
                _gate("h", 3),
                _gate("cz", 2, 3),
                _gate("ry", 4, parameters=(-0.47,)),
                _gate("cx", 3, 4),
                _gate("h", 5),
                _gate("cz", 4, 5),
                _gate("rz", 1, parameters=(0.29,)),
                _gate("ry", 3, parameters=(-0.38,)),
                _gate("cx", 0, 5),
                _gate("cz", 1, 4),
                _gate("cx", 2, 3),
            ],
        },
        {
            "id": "bell_gate_corruption_4",
            "num_qubits": 4,
            "tags": ["four_qubit", "gate_corruption", "falsifier"],
            "falsifier_of": "bell_adjacent_4",
            # Deliberately replace CX by CZ.  Since q1 starts in |0>, CZ does
            # nothing and cannot create the target Bell pair.
            "gates": [
                _gate("h", 0),
                _gate("cz", 0, 1),
            ],
        },
    ]


def execution_requests() -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for circuit in comparison_circuits():
        for policy_id, maximum_bond in BOND_POLICIES:
            request = {
                "schema": REQUEST_SCHEMA,
                "execution_id": f"{circuit['id']}_{policy_id}",
                "seed": SEED,
                "truncation_threshold": TRUNCATION_THRESHOLD,
                "max_bond_dimension": maximum_bond,
                "circuit": circuit,
            }
            requests.append(validate_request(request))
    return requests


def dense_reference(circuit: Mapping[str, Any]) -> list[complex]:
    """Hand-typed dense circuit reference in Qiskit's little-endian ordering."""

    num_qubits = circuit["num_qubits"]
    state = [0.0j] * (1 << num_qubits)
    state[0] = 1.0 + 0.0j
    inverse_sqrt_two = 1.0 / math.sqrt(2.0)

    for gate in circuit["gates"]:
        name = gate["name"]
        qubits = gate["qubits"]
        parameters = gate["parameters"]
        if name == "h":
            matrix = (
                (inverse_sqrt_two, inverse_sqrt_two),
                (inverse_sqrt_two, -inverse_sqrt_two),
            )
            _apply_single_qubit(state, qubits[0], matrix)
        elif name == "x":
            _apply_single_qubit(state, qubits[0], ((0.0, 1.0), (1.0, 0.0)))
        elif name == "ry":
            cosine = math.cos(parameters[0] / 2.0)
            sine = math.sin(parameters[0] / 2.0)
            _apply_single_qubit(state, qubits[0], ((cosine, -sine), (sine, cosine)))
        elif name == "rz":
            angle = parameters[0]
            _apply_single_qubit(
                state,
                qubits[0],
                (
                    (cmath.exp(-0.5j * angle), 0.0),
                    (0.0, cmath.exp(0.5j * angle)),
                ),
            )
        elif name == "cx":
            _apply_cx(state, qubits[0], qubits[1])
        elif name == "cz":
            _apply_cz(state, qubits[0], qubits[1])
        elif name == "swap":
            _apply_swap(state, qubits[0], qubits[1])
        else:
            raise ValueError(f"unsupported dense-reference gate: {name!r}")
    return state


def _apply_single_qubit(
    state: list[complex],
    qubit: int,
    matrix: Sequence[Sequence[complex]],
) -> None:
    mask = 1 << qubit
    for index in range(len(state)):
        if index & mask:
            continue
        paired = index | mask
        zero = state[index]
        one = state[paired]
        state[index] = matrix[0][0] * zero + matrix[0][1] * one
        state[paired] = matrix[1][0] * zero + matrix[1][1] * one


def _apply_cx(state: list[complex], control: int, target: int) -> None:
    control_mask = 1 << control
    target_mask = 1 << target
    for index in range(len(state)):
        if index & control_mask and not index & target_mask:
            paired = index | target_mask
            state[index], state[paired] = state[paired], state[index]


def _apply_cz(state: list[complex], left: int, right: int) -> None:
    masks = (1 << left) | (1 << right)
    for index in range(len(state)):
        if index & masks == masks:
            state[index] *= -1.0


def _apply_swap(state: list[complex], left: int, right: int) -> None:
    left_mask = 1 << left
    right_mask = 1 << right
    for index in range(len(state)):
        if not index & left_mask and index & right_mask:
            paired = (index | left_mask) & ~right_mask
            state[index], state[paired] = state[paired], state[index]


def worker_command(
    conda_executable: str,
    request_path: Path,
    result_path: Path,
) -> list[str]:
    """Build the argument-vector command; never route neutral JSON through a shell."""

    return [
        conda_executable,
        "run",
        "-n",
        BASELINE_ENVIRONMENT,
        "python",
        str(WORKER),
        "--input",
        str(request_path),
        "--output",
        str(result_path),
    ]


def analyze_results(
    requests: Sequence[Mapping[str, Any]],
    results: Sequence[Mapping[str, Any]],
    *,
    installed_distribution_evidence_captured: bool,
) -> dict[str, Any]:
    """Compare full-rank and capped Aer states with independent dense states."""

    if len(requests) != len(results):
        raise ValueError("request/result counts differ")
    result_by_execution = {result["execution_id"]: result for result in results}
    if len(result_by_execution) != len(results):
        raise ValueError("duplicate result execution_id")
    checks: dict[str, bool] = {
        "installed_aer_distribution_evidence_captured": (
            installed_distribution_evidence_captured
        ),
    }
    circuit_rows: list[dict[str, Any]] = []
    policy_metrics: dict[tuple[str, str], dict[str, Any]] = {}

    for circuit in comparison_circuits():
        reference = dense_reference(circuit)
        full_id = f"{circuit['id']}_full_rank"
        full_result = result_by_execution[full_id]
        full_state = decode_complex_vector(full_result["statevector"])
        reference_fidelity = state_fidelity(reference, full_state)
        reference_l2 = phase_aligned_l2(reference, full_state)
        checks[f"full_rank_reference_{circuit['id']}"] = (
            reference_fidelity >= FULL_RANK_MIN_FIDELITY
            and reference_l2 <= FULL_RANK_MAX_PHASE_ALIGNED_L2
        )
        policy_rows: list[dict[str, Any]] = []
        for policy_id, cap in BOND_POLICIES:
            execution_id = f"{circuit['id']}_{policy_id}"
            result = result_by_execution[execution_id]
            state = decode_complex_vector(result["statevector"])
            norm_error = abs(vector_norm_squared(state) - 1.0)
            bond_dimensions = result["mps"]["bond_dimensions"]
            cap_respected = cap is None or max(bond_dimensions, default=1) <= cap
            checks[f"normalized_{execution_id}"] = norm_error <= MAX_NORM_ERROR
            checks[f"bond_cap_{execution_id}"] = cap_respected
            policy_row = {
                "policy": policy_id,
                "max_bond_dimension": cap,
                "saved_bond_dimensions": bond_dimensions,
                "norm_error": norm_error,
                "fidelity_to_full_rank": state_fidelity(full_state, state),
                "phase_aligned_l2_to_full_rank": phase_aligned_l2(full_state, state),
                "fidelity_to_dense_reference": state_fidelity(reference, state),
                "discard_log": {
                    "mps_log_evidence_present": True,
                    "positive_discard_values_present": bool(
                        result["mps_log"]["discarded_value_count"]
                    ),
                    "discarded_values": result["mps_log"]["discarded_values"],
                    "discarded_value_sum": result["mps_log"]["discarded_value_sum"],
                    "discarded_value_max": result["mps_log"]["discarded_value_max"],
                    "logged_bond_dimensions": result["mps_log"][
                        "logged_bond_dimensions"
                    ],
                },
            }
            policy_rows.append(policy_row)
            policy_metrics[(circuit["id"], policy_id)] = policy_row
        circuit_rows.append(
            {
                "circuit_id": circuit["id"],
                "tags": circuit["tags"],
                "full_rank_vs_dense_reference": {
                    "fidelity": reference_fidelity,
                    "phase_aligned_l2": reference_l2,
                },
                "policies": policy_rows,
            }
        )

    bell_full = policy_metrics[("bell_adjacent_4", "full_rank")]
    bell_cap1 = policy_metrics[("bell_adjacent_4", "cap_1")]
    bell_cap2 = policy_metrics[("bell_adjacent_4", "cap_2")]
    checks["bell_full_exact_and_no_positive_discard"] = (
        bell_full["fidelity_to_full_rank"] >= FULL_RANK_MIN_FIDELITY
        and bell_full["discard_log"]["mps_log_evidence_present"]
        and not bell_full["discard_log"]["positive_discard_values_present"]
    )
    checks["bell_cap2_exact_and_no_positive_discard"] = (
        bell_cap2["fidelity_to_full_rank"] >= FULL_RANK_MIN_FIDELITY
        and bell_cap2["discard_log"]["mps_log_evidence_present"]
        and not bell_cap2["discard_log"]["positive_discard_values_present"]
    )
    checks["bell_cap1_has_expected_loss_discard_and_cap"] = (
        abs(
            bell_cap1["fidelity_to_full_rank"] - BELL_CAP1_EXPECTED_FIDELITY
        )
        <= BELL_FIDELITY_ABS_TOLERANCE
        and bell_cap1["discard_log"]["discarded_value_sum"] > 0.0
        and max(bell_cap1["saved_bond_dimensions"], default=1) <= 1
    )
    for hard_circuit_id in ("nonadjacent_5", "mixed_entangling_6"):
        hard_cap1 = policy_metrics[(hard_circuit_id, "cap_1")]
        checks[f"{hard_circuit_id}_cap1_is_nonvacuous"] = (
            hard_cap1["discard_log"]["discarded_value_sum"] > 0.0
            or hard_cap1["fidelity_to_full_rank"]
            <= 1.0 - HARD_CAP1_MIN_FIDELITY_LOSS
        )

    source_id = "bell_adjacent_4"
    corrupted_id = "bell_gate_corruption_4"
    source_reference = dense_reference(_circuit_by_id(source_id))
    corrupted_reference = dense_reference(_circuit_by_id(corrupted_id))
    source_aer = decode_complex_vector(
        result_by_execution[f"{source_id}_full_rank"]["statevector"]
    )
    corrupted_aer = decode_complex_vector(
        result_by_execution[f"{corrupted_id}_full_rank"]["statevector"]
    )
    reference_corruption_fidelity = state_fidelity(source_reference, corrupted_reference)
    aer_corruption_fidelity = state_fidelity(source_aer, corrupted_aer)
    checks["gate_corruption_falsifier_reference_detected"] = (
        reference_corruption_fidelity <= FALSIFIER_MAX_FIDELITY
    )
    checks["gate_corruption_falsifier_aer_detected"] = (
        aer_corruption_fidelity <= FALSIFIER_MAX_FIDELITY
    )
    return {
        "thresholds": {
            "full_rank_min_fidelity": FULL_RANK_MIN_FIDELITY,
            "full_rank_max_phase_aligned_l2": FULL_RANK_MAX_PHASE_ALIGNED_L2,
            "max_norm_error": MAX_NORM_ERROR,
            "falsifier_max_fidelity": FALSIFIER_MAX_FIDELITY,
            "bell_cap1_expected_fidelity": BELL_CAP1_EXPECTED_FIDELITY,
            "bell_fidelity_abs_tolerance": BELL_FIDELITY_ABS_TOLERANCE,
            "hard_cap1_min_fidelity_loss": HARD_CAP1_MIN_FIDELITY_LOSS,
        },
        "circuits": circuit_rows,
        "falsifier": {
            "kind": "gate_corruption",
            "source_circuit_id": source_id,
            "corrupted_circuit_id": corrupted_id,
            "corruption": "replace Bell-pair CX(0,1) with CZ(0,1)",
            "reference_fidelity": reference_corruption_fidelity,
            "aer_full_rank_fidelity": aer_corruption_fidelity,
            "detected": (
                reference_corruption_fidelity <= FALSIFIER_MAX_FIDELITY
                and aer_corruption_fidelity <= FALSIFIER_MAX_FIDELITY
            ),
        },
        "checks": checks,
        "all_checks_passed": all(checks.values()),
    }


def _circuit_by_id(circuit_id: str) -> dict[str, Any]:
    for circuit in comparison_circuits():
        if circuit["id"] == circuit_id:
            return circuit
    raise KeyError(circuit_id)


def _git_output_at(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(arguments)} failed for {repository}: "
            f"{completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _assert_preconditions(
    output: Path,
    scratch_root: Path | None,
) -> tuple[str, dict[str, Any], str]:
    if not WORKER.is_file():
        raise RuntimeError(f"missing Aer worker: {WORKER}")
    if not BASELINE_REPO.is_dir():
        raise RuntimeError(f"missing frozen Aer clone: {BASELINE_REPO}")
    if output.suffix != ".json":
        raise RuntimeError("comparison output must have a .json suffix")
    if _is_within(output, EXTERNAL_ROOT):
        raise RuntimeError("comparison output must not be written inside external/")
    if scratch_root is not None and _is_within(scratch_root, EXTERNAL_ROOT):
        raise RuntimeError("comparison scratch directory must not be inside external/")
    if any(output == (REPO / path).resolve() for path in COMMITTED_SCRIPT_INPUTS):
        raise RuntimeError("comparison output must not replace a committed comparison input")
    conda_executable = shutil.which("conda")
    if conda_executable is None:
        raise RuntimeError("conda executable was not found")
    relative_scripts = [str(path) for path in COMMITTED_SCRIPT_INPUTS]
    for relative_script in relative_scripts:
        _git_output_at(REPO, "ls-files", "--error-unmatch", relative_script)
    script_status = _git_output_at(
        REPO,
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--",
        *relative_scripts,
    )
    if script_status:
        raise RuntimeError(
            "Aer comparison scripts must be committed and clean before execution:\n"
            f"{script_status}"
        )
    orchestrator_commit = _git_output_at(REPO, "rev-parse", "HEAD")
    observed_commit = _git_output_at(BASELINE_REPO, "rev-parse", "HEAD")
    if observed_commit != EXPECTED_BASELINE_COMMIT:
        raise RuntimeError(
            "Aer baseline commit drifted: "
            f"expected {EXPECTED_BASELINE_COMMIT}, observed {observed_commit}"
        )
    dirty = _git_output_at(
        BASELINE_REPO,
        "status",
        "--porcelain",
        "--untracked-files=all",
    )
    if dirty:
        raise RuntimeError(f"Aer baseline clone is not pristine:\n{dirty}")
    release_tag_commit = _git_output_at(
        BASELINE_REPO,
        "rev-list",
        "-n",
        "1",
        EXPECTED_RELEASE_TAG,
    )
    if release_tag_commit != EXPECTED_RELEASE_TAG_COMMIT:
        raise RuntimeError(
            f"Aer {EXPECTED_RELEASE_TAG} tag drifted: expected "
            f"{EXPECTED_RELEASE_TAG_COMMIT}, observed {release_tag_commit}"
        )
    merge_base = _git_output_at(
        BASELINE_REPO,
        "merge-base",
        release_tag_commit,
        observed_commit,
    )
    if merge_base != release_tag_commit:
        raise RuntimeError("Aer release tag is not an ancestor of the frozen clone HEAD")
    mps_source_diff = _git_output_at(
        BASELINE_REPO,
        "diff",
        "--name-only",
        f"{release_tag_commit}..{observed_commit}",
        "--",
        "src/simulators/matrix_product_state",
    ).splitlines()
    if mps_source_diff:
        raise RuntimeError(
            "Aer MPS C++ source differs between the installed-version tag and clone HEAD:\n"
            + "\n".join(mps_source_diff)
        )
    commits_after_release = int(
        _git_output_at(
            BASELINE_REPO,
            "rev-list",
            "--count",
            f"{release_tag_commit}..{observed_commit}",
        )
    )
    clone_provenance = {
        "expected_head": EXPECTED_BASELINE_COMMIT,
        "observed_head": observed_commit,
        "release_tag": EXPECTED_RELEASE_TAG,
        "release_tag_commit": release_tag_commit,
        "release_tag_is_ancestor": True,
        "commits_after_release_tag": commits_after_release,
        "mps_cpp_source_diff_paths": mps_source_diff,
        "mps_cpp_source_unchanged_since_release_tag": True,
        "relation_to_installed_distribution": "not_established",
        "pristine": True,
    }
    print(
        f"orchestrator: frozen Aer clone {observed_commit} is pristine",
        flush=True,
    )
    print(
        f"orchestrator: comparison scripts are committed at {orchestrator_commit}",
        flush=True,
    )
    return conda_executable, clone_provenance, orchestrator_commit


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def _is_sha256_hex(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _installed_distribution_evidence_captured(runtime: Mapping[str, Any]) -> bool:
    """Validate captured installed-distribution evidence, not source equivalence."""

    if runtime.get("qiskit_aer_version") != EXPECTED_AER_VERSION:
        return False
    prefix_text = runtime.get("python_prefix")
    executable_text = runtime.get("python_executable")
    if not isinstance(prefix_text, str) or not isinstance(executable_text, str):
        return False
    prefix = Path(prefix_text)
    executable = Path(executable_text)
    if prefix.name != BASELINE_ENVIRONMENT:
        return False
    if runtime.get("python_executable_within_prefix") is not True:
        return False
    if not _is_within(executable, prefix):
        return False
    if runtime.get("qiskit_aer_import_matches_distribution") is not True:
        return False
    if runtime.get("qiskit_aer_direct_url") is not None:
        return False
    if runtime.get("qiskit_aer_installation_source") != (
        "pip_distribution_without_direct_url"
    ):
        return False
    distribution = runtime.get("qiskit_aer_distribution")
    if not isinstance(distribution, Mapping):
        return False
    if distribution.get("name") != "qiskit-aer":
        return False
    if distribution.get("version") != EXPECTED_AER_VERSION:
        return False
    if distribution.get("installer") != "pip":
        return False
    root_text = distribution.get("root")
    record_path_text = distribution.get("record_path")
    module_file_text = runtime.get("qiskit_aer_module_file")
    if not all(
        isinstance(value, str)
        for value in (root_text, record_path_text, module_file_text)
    ):
        return False
    distribution_root = Path(root_text)
    record_path = Path(record_path_text)
    module_file = Path(module_file_text)
    if not _is_within(distribution_root, prefix):
        return False
    if not _is_within(record_path, distribution_root):
        return False
    if module_file.resolve() != (
        distribution_root / "qiskit_aer" / "__init__.py"
    ).resolve():
        return False
    record_hash = distribution.get("record_sha256")
    if not _is_sha256_hex(record_hash):
        return False
    selected_hashes = distribution.get("selected_package_sha256")
    if not isinstance(selected_hashes, Mapping):
        return False
    required_python_hashes = {
        "qiskit_aer/__init__.py",
        "qiskit_aer/backends/aer_simulator.py",
    }
    if not required_python_hashes.issubset(selected_hashes):
        return False
    if not all(_is_sha256_hex(selected_hashes[path]) for path in required_python_hashes):
        return False
    controller_hashes = [
        value
        for path, value in selected_hashes.items()
        if "controller_wrappers" in path
    ]
    return bool(controller_hashes) and all(_is_sha256_hex(value) for value in controller_hashes)


def _process_runner() -> Any:
    """Load the repo process-group owner only after committed-clean preflight."""

    tests_root = str(TESTS_ROOT)
    if tests_root not in sys.path:
        sys.path.insert(0, tests_root)
    from harness import proc

    return proc


def _run_worker(
    conda_executable: str,
    request: Mapping[str, Any],
    scratch: Path,
    timeout_seconds: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    execution_id = request["execution_id"]
    request_path = scratch / f"{execution_id}.request.json"
    result_path = scratch / f"{execution_id}.result.json"
    log_path = scratch / f"{execution_id}.log"
    atomic_write_json(request_path, request)
    command = worker_command(conda_executable, request_path, result_path)
    environment = os.environ.copy()
    # Never leak a caller-provided import overlay into the isolated baseline.
    environment.pop("PYTHONPATH", None)
    print(f"orchestrator: launch {execution_id}", flush=True)
    ran = _process_runner().run(
        command,
        cwd=str(REPO),
        env=environment,
        timeout=timeout_seconds,
        log_path=str(log_path),
    )
    log_text = log_path.read_text(encoding="utf-8", errors="replace")
    if log_text:
        print(log_text, end="" if log_text.endswith("\n") else "\n", flush=True)
    execution = {
        "execution_id": execution_id,
        "returncode": ran.returncode,
        "timed_out": ran.timed_out,
        "group_cleanup_verified": ran.group_cleanup_verified,
        "log_bytes": log_path.stat().st_size,
        "log_sha256": _sha256_file(log_path),
    }
    if not ran.ok:
        raise RuntimeError(
            f"Aer worker {execution_id} failed: returncode={ran.returncode}, "
            f"timed_out={ran.timed_out}, "
            f"group_cleanup_verified={ran.group_cleanup_verified}\n{log_text.rstrip()}"
        )
    result = read_json_object(result_path)
    validate_result(result, request)
    print(f"orchestrator: validated {execution_id}", flush=True)
    execution["request_json_sha256"] = _sha256_file(request_path)
    execution["result_json_sha256"] = _sha256_file(result_path)
    return result, execution


def run_comparison(
    output: Path,
    *,
    scratch_root: Path | None = None,
    timeout_seconds: float = 120.0,
) -> dict[str, Any]:
    """Execute all isolated rows, analyze them, and atomically publish a report."""

    output = output.resolve()
    scratch_root = scratch_root.resolve() if scratch_root is not None else None
    conda_executable, clone_provenance, orchestrator_commit = _assert_preconditions(
        output,
        scratch_root,
    )
    if scratch_root is not None:
        scratch_root.mkdir(parents=True, exist_ok=True)
    requests = execution_requests()
    references = {
        circuit["id"]: encode_complex_vector(dense_reference(circuit))
        for circuit in comparison_circuits()
    }
    with tempfile.TemporaryDirectory(
        prefix="ecs-aer-mps-",
        dir=scratch_root,
    ) as temporary_directory:
        scratch = Path(temporary_directory)
        worker_rows = [
            _run_worker(conda_executable, request, scratch, timeout_seconds)
            for request in requests
        ]
    results = [result for result, _execution in worker_rows]
    execution_provenance = [execution for _result, execution in worker_rows]

    runtimes = [result["runtime"] for result in results]
    runtime_fingerprints = {
        json.dumps(runtime, allow_nan=False, sort_keys=True) for runtime in runtimes
    }
    runtime_consistent = len(runtime_fingerprints) == 1
    distribution_evidence_captured = runtime_consistent and all(
        _installed_distribution_evidence_captured(runtime) for runtime in runtimes
    )
    analysis = analyze_results(
        requests,
        results,
        installed_distribution_evidence_captured=distribution_evidence_captured,
    )
    analysis["checks"]["runtime_identity_consistent"] = runtime_consistent
    analysis["all_checks_passed"] = all(analysis["checks"].values())

    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "scope": (
            "qubit_circuit_state_and_local_mps_truncation_diagnostic_only;"
            "not_a_peps_or_full_record_faithfulness_certificate"
        ),
        "baseline": {
            "name": "Qiskit Aer matrix_product_state",
            "environment": BASELINE_ENVIRONMENT,
            "clone": str(BASELINE_REPO.relative_to(REPO)),
            "installed_distribution_evidence": (
                "captured from metadata.distribution('qiskit-aer'): installer, absent "
                "direct_url, RECORD hash, selected package hashes, and import-path match"
            ),
            "provenance_claim_boundary": (
                "the installed distribution is not claimed to originate from, match, or be "
                "cryptographically bound to the external clone or its release tag"
            ),
            "clone_provenance": clone_provenance,
            "expected_qiskit_aer_version": EXPECTED_AER_VERSION,
            "worker_sha256": _sha256_file(WORKER),
            "protocol_sha256": _sha256_file(
                Path(__file__).with_name("aer_mps_protocol.py")
            ),
            "orchestrator_repo_commit": orchestrator_commit,
            "committed_script_inputs": [str(path) for path in COMMITTED_SCRIPT_INPUTS],
            "committed_input_sha256": {
                str(path): _sha256_file(REPO / path) for path in COMMITTED_SCRIPT_INPUTS
            },
        },
        "protocol": {
            "qubit_order": (
                "Qiskit little-endian statevector: amplitude index bit q is qubit q"
            ),
            "precision": "Aer saved complex statevector; JSON float pairs",
            "fresh_process_per_execution": True,
            "transpilation": "none",
            "seed": SEED,
            "truncation_threshold": TRUNCATION_THRESHOLD,
            "sample_measure_algorithm": {
                "requested_option": "mps_apply_measure",
                "expected_aer_metadata_enum": 0,
                "claim_boundary": "fixtures contain no measurement operations",
            },
            "actual_configuration_proved_by_aer_metadata": [
                "method",
                "device",
                "matrix_product_state_truncation_threshold",
                "matrix_product_state_max_bond_dimension",
                "matrix_product_state_sample_measure_algorithm",
                "matrix_product_state_lapack",
            ],
            "worker_declared_not_aer_metadata_proved": [
                "seed_simulator",
                "mps_swap_direction",
                "chop_threshold",
                "shots",
            ],
            "mps_log_data_proof": (
                "required Aer MPS_log_data metadata with valid braces and at least one "
                "full-width BD entry per requested two-qubit gate"
            ),
            "bond_policies": [
                {"id": policy_id, "max_bond_dimension": cap}
                for policy_id, cap in BOND_POLICIES
            ],
            "discard_log_semantics": (
                "Aer MPS_log_data discarded_value entries are per-SVD sums of squared "
                "discarded Schmidt coefficients; zero entries mean no positive value only "
                "after metadata, brace format, and per-two-qubit-gate BD evidence validate"
            ),
        },
        "circuits": comparison_circuits(),
        "dense_references": references,
        "requests": [
            {
                "execution_id": request["execution_id"],
                "request_sha256": canonical_json_sha256(request),
            }
            for request in requests
        ],
        "results": results,
        "worker_execution_provenance": execution_provenance,
        "analysis": analysis,
    }
    report["content_sha256"] = report_content_sha256(report)
    exact_byte_hash = atomic_write_json(output, report)
    print(
        f"orchestrator: wrote {output} exact_byte_sha256={exact_byte_hash}",
        flush=True,
    )
    print(
        "orchestrator: verdict "
        f"{'PASS' if analysis['all_checks_passed'] else 'FAIL'}",
        flush=True,
    )
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="final neutral JSON report")
    parser.add_argument(
        "--scratch-root",
        type=Path,
        default=None,
        help="optional parent for ephemeral worker request/result files",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=120.0,
        help="timeout for each fresh Aer worker",
    )
    args = parser.parse_args()
    if not math.isfinite(args.timeout_seconds) or args.timeout_seconds <= 0.0:
        parser.error("--timeout-seconds must be finite and positive")
    return args


def main() -> int:
    args = _parse_args()
    report = run_comparison(
        args.output,
        scratch_root=args.scratch_root,
        timeout_seconds=args.timeout_seconds,
    )
    return 0 if report["analysis"]["all_checks_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
