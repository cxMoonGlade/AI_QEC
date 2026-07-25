#!/usr/bin/env python3
"""Compare ITensorMPS against an independent dense reference on frozen fixtures.

This is the repository-owned orchestrator for the third external MPS leg.  It
never imports ITensorMPS or Julia: it writes a neutral request, runs the Julia
worker in a fresh isolated process inside ``ecs-baseline-itensor``, and checks
the returned state and canonical-split ledger against a dense reference built
here from first principles.

The ordering discipline is the point of this file.  A capped row is only
meaningful if the same pipeline reproduces the reference exactly at full rank,
because an index-convention or gate-convention error is invisible at full rank
only by coincidence and shows up as "truncation damage" once a cap is applied.
So every fixture runs full rank first, and a full-rank fidelity below the
threshold aborts the fixture before any capped row is scored.

This publishes a comparison report.  It is not simulator acceptance and makes
no claim about the project's own carrier: the leg compares ITensorMPS to a
dense reference on shared fixtures.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Sequence

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

import itensor_mps_protocol as protocol  # noqa: E402

WORKER = Path(__file__).with_name("itensor_mps_worker.jl")
PROJECT = Path(__file__).with_name("itensor_project")
CLONE = REPO / "external" / "baselines" / "ITensorMPS.jl"
LOCK = REPO / "baseline-environment-itensor-linux-64.lock.json"
ENVIRONMENT = "ecs-baseline-itensor"
EXPECTED_COMMIT = "7ce812c42bfedcb3da1c250fdd5f19cb20394d4d"
DEFAULT_OUTPUT = (
    REPO / "outputs" / "simulator_validation" / "external_itensor_mps"
)

# A full-rank row that misses this is a convention error, not truncation.
FULL_RANK_MIN_FIDELITY = 1.0 - 1.0e-12
SEED = 271_828

# Frozen neutral fixtures. Deliberately entangling, so the capped rows exercise
# a real canonical split rather than a product state.
FIXTURES: tuple[dict[str, Any], ...] = (
    {
        "id": "bell_chain",
        "qubits": 3,
        "operations": [
            {"gate": "h", "targets": [0], "parameters": []},
            {"gate": "cx", "targets": [0, 1], "parameters": []},
            {"gate": "ry", "targets": [2], "parameters": [0.37]},
            {"gate": "cz", "targets": [1, 2], "parameters": []},
        ],
    },
    {
        "id": "ladder_five",
        "qubits": 5,
        "operations": [
            {"gate": "h", "targets": [0], "parameters": []},
            {"gate": "h", "targets": [2], "parameters": []},
            {"gate": "cx", "targets": [0, 1], "parameters": []},
            {"gate": "cx", "targets": [2, 3], "parameters": []},
            {"gate": "ry", "targets": [4], "parameters": [0.61]},
            {"gate": "cz", "targets": [1, 2], "parameters": []},
            {"gate": "cx", "targets": [3, 4], "parameters": []},
            {"gate": "rz", "targets": [0], "parameters": [0.22]},
        ],
    },
    {
        "id": "nonlocal_pair",
        "qubits": 4,
        "operations": [
            {"gate": "h", "targets": [0], "parameters": []},
            {"gate": "h", "targets": [1], "parameters": []},
            {"gate": "cx", "targets": [0, 3], "parameters": []},
            {"gate": "cz", "targets": [1, 2], "parameters": []},
            {"gate": "ry", "targets": [2], "parameters": [0.45]},
        ],
    },
)

BOND_POLICIES: tuple[tuple[str, int | None], ...] = (
    ("full_rank", None),
    ("cap_2", 2),
    ("cap_1", 1),
)


def _one_qubit(gate: str, parameters: Sequence[float]) -> np.ndarray:
    if gate == "h":
        return np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2.0)
    if gate == "x":
        return np.array([[0, 1], [1, 0]], dtype=complex)
    if gate == "ry":
        half = float(parameters[0]) / 2.0
        return np.array(
            [[math.cos(half), -math.sin(half)], [math.sin(half), math.cos(half)]],
            dtype=complex,
        )
    if gate == "rz":
        half = float(parameters[0]) / 2.0
        return np.array(
            [[complex(math.cos(half), -math.sin(half)), 0],
             [0, complex(math.cos(half), math.sin(half))]],
            dtype=complex,
        )
    raise ValueError(f"not a one-qubit gate: {gate}")


def dense_reference(circuit: dict[str, Any]) -> np.ndarray:
    """Independent little-endian statevector evolution, qubit 0 fastest.

    Written from first principles rather than reusing any tensor-network code,
    so agreement is evidence rather than a shared-implementation tautology.
    """

    qubits = int(circuit["qubits"])
    state = np.zeros(2**qubits, dtype=complex)
    state[0] = 1.0
    for operation in circuit["operations"]:
        gate = operation["gate"]
        targets = [int(t) for t in operation["targets"]]
        parameters = [float(p) for p in operation["parameters"]]
        tensor = state.reshape([2] * qubits)
        # axis order: qubit 0 is the FASTEST index, i.e. the LAST reshape axis
        axes = [qubits - 1 - t for t in targets]
        if len(targets) == 1:
            matrix = _one_qubit(gate, parameters)
            tensor = np.tensordot(matrix, tensor, axes=([1], [axes[0]]))
            tensor = np.moveaxis(tensor, 0, axes[0])
        else:
            control, target = axes
            if gate == "cx":
                matrix = np.array(
                    [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex
                )
            elif gate == "cz":
                matrix = np.diag([1, 1, 1, -1]).astype(complex)
            elif gate == "swap":
                matrix = np.array(
                    [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex
                )
            else:
                raise ValueError(f"not a two-qubit gate: {gate}")
            operator = matrix.reshape(2, 2, 2, 2)
            tensor = np.tensordot(operator, tensor, axes=([2, 3], [control, target]))
            tensor = np.moveaxis(tensor, [0, 1], [control, target])
        state = tensor.reshape(-1)
    return state


def build_request(circuit: dict[str, Any], policy: str, cap: int | None) -> dict[str, Any]:
    return protocol.validate_request(
        {
            "schema": protocol.REQUEST_SCHEMA,
            "execution_id": f"{circuit['id']}_{policy}",
            "seed": SEED,
            "cutoff": 0.0 if cap is None else 1e-16,
            "max_bond_dimension": cap,
            "amplitude_ordering": protocol.AMPLITUDE_ORDERING,
            "circuit": circuit,
        }
    )


def run_worker(request: dict[str, Any], workspace: Path) -> dict[str, Any]:
    """Run one execution in a fresh isolated process and validate its result."""

    request_path = workspace / f"{request['execution_id']}.request.json"
    result_path = workspace / f"{request['execution_id']}.result.json"
    protocol.atomic_write_json(request_path, request)
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("CONDA_", "_CE_", "PYTHON"))
    }
    completed = subprocess.run(
        [
            "conda", "run", "--no-capture-output", "-n", ENVIRONMENT,
            "julia", f"--project={PROJECT}", str(WORKER),
            "--input", str(request_path), "--output", str(result_path),
        ],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=1800,
        env=environment,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"itensor worker failed for {request['execution_id']}:\n"
            f"{completed.stdout[-3000:]}\n{completed.stderr[-3000:]}"
        )
    result = protocol.read_json_object(result_path)
    protocol.validate_result(result, request)
    return result


def compare(result: dict[str, Any], reference: np.ndarray) -> dict[str, Any]:
    amplitudes = protocol.decode_complex_vector(result["statevector"])
    fidelity = protocol.state_fidelity(list(reference), amplitudes)
    distance = protocol.phase_aligned_l2(
        [complex(v) for v in reference], amplitudes
    )
    return {
        "fidelity": fidelity,
        "phase_aligned_l2": distance,
        "norm_squared": result["statevector_norm_squared"],
        "bond_dimensions": result["mps"]["bond_dimensions"],
        "max_bond_dimension_observed": max(result["mps"]["bond_dimensions"], default=1),
        "total_discarded_weight": float(sum(result["mps"]["discarded_weight"])),
        "schmidt_convention": result["mps"]["schmidt_convention"],
        "leading_schmidt_values": [
            spectrum[:4] for spectrum in result["mps"]["schmidt_values"]
        ],
    }


def preflight() -> dict[str, Any]:
    if not WORKER.is_file():
        raise SystemExit(f"worker missing: {WORKER}")
    if not LOCK.is_file():
        raise SystemExit(
            f"environment lock missing: {LOCK}; run "
            "scripts/external_baselines/build_itensor_baseline_environment.py"
        )
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(CLONE), capture_output=True, text=True, check=True
    ).stdout.strip()
    if head != EXPECTED_COMMIT:
        raise SystemExit(f"clone is at {head}, expected {EXPECTED_COMMIT}")
    # ignored build artefacts count: a directory install pollutes the clone and
    # git status hides it without --ignored.
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--ignored"],
        cwd=str(CLONE), capture_output=True, text=True, check=True,
    ).stdout.strip()
    if status:
        raise SystemExit(f"upstream clone is polluted:\n{status}")
    lock = protocol.read_json_object(LOCK)
    if lock["itensor_vcs"]["commit"] != EXPECTED_COMMIT:
        raise SystemExit("environment lock pins a different upstream commit")
    return {
        "clone_commit": head,
        "clone_pristine_including_ignored": True,
        "lock_path": str(LOCK.relative_to(REPO)),
        "lock_tree_hash": lock["itensor_vcs"]["tree_hash"],
    }


def falsifier(workspace: Path) -> dict[str, Any]:
    """A deliberately corrupted circuit must be caught by the comparison.

    Without this, a comparison that silently agreed with everything would look
    exactly like a comparison that agrees with the truth.
    """

    circuit = json.loads(json.dumps(FIXTURES[0]))
    circuit["id"] = "corrupted_bell_chain"
    circuit["operations"][2]["parameters"] = [0.37 + 0.25]
    request = build_request(circuit, "full_rank", None)
    result = run_worker(request, workspace)
    honest = dense_reference(FIXTURES[0])
    observed = compare(result, honest)
    caught = observed["fidelity"] < FULL_RANK_MIN_FIDELITY
    return {
        "description": "rotation angle perturbed by 0.25 rad in the worker's circuit",
        "fidelity_against_uncorrupted_reference": observed["fidelity"],
        "caught": caught,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="report destination")
    parser.add_argument("--workspace", type=Path, help="request/result scratch directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    provenance = preflight()
    workspace = args.workspace or (DEFAULT_OUTPUT / "workspace")
    workspace.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    runtime_identity: dict[str, Any] | None = None
    for circuit in FIXTURES:
        reference = dense_reference(circuit)
        full_rank_ok = False
        for policy, cap in BOND_POLICIES:
            request = build_request(circuit, policy, cap)
            result = run_worker(request, workspace)
            if runtime_identity is None:
                runtime_identity = result["runtime"]
            observed = compare(result, reference)
            row = {
                "circuit_id": circuit["id"],
                "qubits": circuit["qubits"],
                "bond_policy": policy,
                "max_bond_dimension": cap,
                **observed,
            }
            if policy == "full_rank":
                row["full_rank_reproduces_reference"] = (
                    observed["fidelity"] >= FULL_RANK_MIN_FIDELITY
                )
                full_rank_ok = row["full_rank_reproduces_reference"]
                if not full_rank_ok:
                    row["abort_reason"] = (
                        "full-rank fidelity below threshold: this is a convention or "
                        "gate-mapping error, not truncation damage; capped rows for "
                        "this fixture are not scored"
                    )
                    rows.append(row)
                    break
            rows.append(row)
        if not full_rank_ok:
            continue

    report = {
        "schema": protocol.REPORT_SCHEMA,
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "environment": ENVIRONMENT,
        "provenance": provenance,
        "runtime": runtime_identity,
        "full_rank_min_fidelity": FULL_RANK_MIN_FIDELITY,
        "amplitude_ordering": protocol.AMPLITUDE_ORDERING,
        "schmidt_convention": protocol.SCHMIDT_CONVENTION,
        "rows": rows,
        "falsifier": falsifier(workspace),
        "all_full_rank_rows_reproduce_reference": all(
            row.get("full_rank_reproduces_reference", True)
            for row in rows
            if row["bond_policy"] == "full_rank"
        ),
        "claim_boundary": (
            "ITensorMPS versus a repository-owned dense reference on frozen neutral "
            "fixtures; it is not simulator acceptance and makes no claim about the "
            "project's own carrier or about full-record faithfulness"
        ),
    }
    report["content_sha256"] = protocol.report_content_sha256(report)

    destination = args.output or (
        DEFAULT_OUTPUT / f"itensor_mps_comparison_{datetime.now().astimezone():%Y%m%dT%H%M%S%z}.json"
    )
    protocol.atomic_write_json(destination, report)

    print(f"report: {destination}", flush=True)
    for row in rows:
        print(
            f"  {row['circuit_id']:16s} {row['bond_policy']:10s} "
            f"fidelity={row['fidelity']:.12f} "
            f"maxbond={row['max_bond_dimension_observed']} "
            f"discarded={row['total_discarded_weight']:.3e}",
            flush=True,
        )
    caught = report["falsifier"]["caught"]
    print(f"  falsifier caught the corruption: {caught}", flush=True)
    ok = report["all_full_rank_rows_reproduce_reference"] and caught
    print(f"status={'passed' if ok else 'failed'}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
