#!/usr/bin/env python3
"""Evolve the frozen d3/d5 pure-state fixture with Quimb main PEPS.

The worker must run in an isolated environment whose Quimb distribution is
installed from the pristine full clone at the exact expected commit.  It
materializes the complete state vector by an exact tensor-network contraction;
local simple-update diagnostics never substitute for the later independent
dense-vector fidelity calculation.
"""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping

import numpy as np

from emit_peps_d5_pure_state_fixture import (
    FIXTURE_SCHEMA,
    canonical_sha256,
    validate_fixture,
)


RESULT_SCHEMA = "error_coupling_simulator.external.quimb_peps_d5_state.v1"
EXPECTED_QUIMB_COMMIT = "3c89529fe0a3487133a3928201691161e110abdf"
REPO = Path(__file__).resolve().parents[2]
QUIMB_CLONE = REPO / "external" / "baselines" / "quimb"
ENVIRONMENT_NAME = "ecs-baseline-quimb-peps"
ENVIRONMENT_LOCK = (
    REPO / "baseline-environment-quimb-peps-linux-64.lock.json"
)
ENVIRONMENT_LOCK_SCHEMA = (
    "error_coupling_simulator.environment_lock.quimb_peps_d5.v1"
)
GAUGE_SMUDGE = 1e-12
COMMITTED_INPUTS = (
    "baseline-environment-quimb-peps-linux-64.lock.json",
    "docs/METRICS.md",
    (
        "docs/simulator_validation/"
        "PEPS_D5_PURE_STATE_FIDELITY_LITERATURE_CLOSURE_2026-07-26.md"
    ),
    (
        "docs/simulator_validation/"
        "PEPS_D5_PURE_STATE_FIDELITY_PREREG_2026-07-26.md"
    ),
    (
        "scripts/external_baselines/"
        "build_quimb_peps_d5_environment_lock.py"
    ),
    "scripts/external_baselines/emit_peps_d5_pure_state_fixture.py",
    "scripts/external_baselines/quimb_peps_d5_fidelity_worker.py",
    "tests/test_external_peps_d5_pure_state_fidelity.py",
)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to replace existing output: {path}")
    encoded = (
        json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_save_npy(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to replace existing output: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".npy",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            np.save(stream, array, allow_pickle=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def _run_git(*arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(QUIMB_CLONE), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _verify_pristine_clone() -> dict[str, Any]:
    head = _run_git("rev-parse", "HEAD")
    if head != EXPECTED_QUIMB_COMMIT:
        raise RuntimeError(f"Quimb clone HEAD {head} != {EXPECTED_QUIMB_COMMIT}")
    if _run_git("rev-parse", "--is-shallow-repository") != "false":
        raise RuntimeError("Quimb source clone is shallow")
    status = _run_git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignored",
    )
    if status:
        raise RuntimeError(f"Quimb source clone is not pristine:\n{status}")
    remote = _run_git("remote", "get-url", "origin")
    if remote != "https://github.com/jcmgray/quimb.git":
        raise RuntimeError(f"unexpected Quimb origin: {remote!r}")
    return {
        "path": str(QUIMB_CLONE.resolve()),
        "origin": remote,
        "commit": head,
        "tree": _run_git("rev-parse", "HEAD^{tree}"),
        "is_shallow": False,
        "clean_including_ignored": True,
    }


def _verify_installed_quimb() -> dict[str, Any]:
    if os.environ.get("CONDA_DEFAULT_ENV") != ENVIRONMENT_NAME:
        raise RuntimeError(
            f"worker must run in Conda environment {ENVIRONMENT_NAME!r}"
        )
    distribution = metadata.distribution("quimb")
    direct_url_text = distribution.read_text("direct_url.json")
    if direct_url_text is None:
        raise RuntimeError("installed Quimb has no direct_url.json")
    direct_url = json.loads(direct_url_text)
    vcs_info = direct_url.get("vcs_info", {})
    if (
        direct_url.get("vcs") not in {None, "git"}
        and vcs_info.get("vcs") != "git"
    ):
        raise RuntimeError("installed Quimb is not Git-bound")
    commit = vcs_info.get("commit_id")
    requested = vcs_info.get("requested_revision")
    if commit != EXPECTED_QUIMB_COMMIT or requested != EXPECTED_QUIMB_COMMIT:
        raise RuntimeError(
            "installed Quimb commit binding mismatch: "
            f"commit={commit!r}, requested={requested!r}"
        )
    return {
        "version": distribution.version,
        "direct_url": direct_url,
    }


def _normalize_distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _runtime_distribution_records() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for distribution in metadata.distributions():
        raw_name = distribution.metadata.get("Name")
        if not raw_name:
            continue
        name = _normalize_distribution_name(raw_name)
        if name == "error-coupling-simulator":
            raise RuntimeError(
                "project distribution leaked into Quimb baseline environment"
            )
        if name in rows:
            raise RuntimeError(f"duplicate installed distribution: {name}")
        direct_url = None
        record_path = None
        for item in distribution.files or ():
            if item.name == "direct_url.json":
                direct_url = json.loads(item.read_text())
            if item.name == "RECORD" and ".dist-info" in str(item):
                record_path = Path(distribution.locate_file(item))
        rows[name] = {
            "version": distribution.version,
            "direct_url": direct_url,
            "record_sha256": (
                _file_sha256(record_path)
                if record_path is not None
                else None
            ),
        }
    return dict(sorted(rows.items()))


def _runtime_conda_explicit_urls() -> list[str]:
    output = subprocess.run(
        [
            "/home/cx/miniforge3/bin/conda",
            "list",
            "-p",
            sys.prefix,
            "--explicit",
            "--sha256",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [
        line.strip()
        for line in output.splitlines()
        if line.strip().startswith("http")
    ]


def _verify_process_isolation() -> dict[str, Any]:
    if os.environ.get("PYTHONPATH"):
        raise RuntimeError("PYTHONPATH must be absent in Quimb worker")
    if os.environ.get("VIRTUAL_ENV"):
        raise RuntimeError("VIRTUAL_ENV must be absent in Quimb worker")
    if not sys.flags.no_user_site:
        raise RuntimeError(
            "user-site imports must be disabled with PYTHONNOUSERSITE=1"
        )
    if os.environ.get("CONDA_DEFAULT_ENV") != ENVIRONMENT_NAME:
        raise RuntimeError(
            f"worker must run in Conda environment {ENVIRONMENT_NAME!r}"
        )
    return {
        "python_executable": str(Path(sys.executable).resolve()),
        "python_prefix": str(Path(sys.prefix).resolve()),
        "python_version": sys.version.split()[0],
        "conda_default_env": os.environ["CONDA_DEFAULT_ENV"],
        "pythonpath_absent": True,
        "virtual_env_absent": True,
        "user_site_disabled": True,
    }


def _verify_committed_inputs() -> dict[str, Any]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    hashes: dict[str, str] = {}
    for relative in COMMITTED_INPUTS:
        path = REPO / relative
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", relative],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        if tracked.returncode != 0:
            raise RuntimeError(f"claim-bearing input is untracked: {relative}")
        changed = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", relative],
            cwd=REPO,
        )
        if changed.returncode != 0:
            raise RuntimeError(
                f"claim-bearing input differs from HEAD: {relative}"
            )
        hashes[relative] = _file_sha256(path)
    return {"git_head": head, "sha256": hashes}


def _verify_environment_lock() -> dict[str, Any]:
    payload = json.loads(ENVIRONMENT_LOCK.read_text(encoding="utf-8"))
    if payload.get("schema") != ENVIRONMENT_LOCK_SCHEMA:
        raise RuntimeError("Quimb environment lock schema mismatch")
    if payload.get("environment_name") != ENVIRONMENT_NAME:
        raise RuntimeError("Quimb environment lock name mismatch")
    upstream = payload.get("upstream", {})
    if upstream.get("commit") != EXPECTED_QUIMB_COMMIT:
        raise RuntimeError("Quimb environment lock source commit mismatch")
    selected = payload.get("selected_distribution_records", {}).get(
        "quimb", {}
    )
    vcs = selected.get("direct_url", {}).get("vcs_info", {})
    if vcs.get("commit_id") != EXPECTED_QUIMB_COMMIT:
        raise RuntimeError("Quimb environment lock installed commit mismatch")
    if payload.get("pip_check") != "No broken requirements found.":
        raise RuntimeError("Quimb environment lock did not pass pip check")
    runtime_records = _runtime_distribution_records()
    if runtime_records != payload.get("pip_distribution_records"):
        raise RuntimeError(
            "installed Python distribution records differ from Quimb lock"
        )
    runtime_conda_urls = _runtime_conda_explicit_urls()
    if runtime_conda_urls != payload.get("conda_explicit_sha256_urls"):
        raise RuntimeError("Conda explicit URLs differ from Quimb lock")
    pip_check = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if pip_check != payload["pip_check"]:
        raise RuntimeError("runtime pip check differs from Quimb lock")
    return {
        "path": str(ENVIRONMENT_LOCK.resolve()),
        "file_sha256": _file_sha256(ENVIRONMENT_LOCK),
        "schema": payload["schema"],
        "environment_name": payload["environment_name"],
        "authoritative_runtime_conformance_checked": True,
        "pip_distribution_records_exact": True,
        "conda_explicit_urls_exact": True,
        "pip_check_exact": True,
    }


def _read_fixture(path: Path) -> tuple[dict[str, Any], str, str]:
    raw = path.read_bytes()
    payload = json.loads(raw)
    if not isinstance(payload, dict) or payload.get("schema") != FIXTURE_SCHEMA:
        raise ValueError("unsupported PEPS d5 fixture")
    size = payload.get("distance_label")
    if size not in {3, 5}:
        raise ValueError("fixture distance must be the frozen d3 or d5 value")
    fingerprint = validate_fixture(
        payload,
        expected_size=size,
        require_pinned_hash=True,
    )
    if fingerprint != canonical_sha256(payload):
        raise RuntimeError("fixture canonical hash changed during validation")
    return payload, hashlib.sha256(raw).hexdigest(), fingerprint


def _numpy_gate(operation: Mapping[str, Any]) -> np.ndarray:
    x = np.asarray([[0, 1], [1, 0]], dtype=np.complex128)
    z = np.asarray([[1, 0], [0, -1]], dtype=np.complex128)
    h = np.asarray([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2)
    kind = operation["kind"]
    if kind == "H":
        return h
    angle = float(operation["angle_rad"])
    if kind == "RY":
        cosine = np.cos(angle / 2.0)
        sine = np.sin(angle / 2.0)
        return np.asarray(
            [[cosine, -sine], [sine, cosine]],
            dtype=np.complex128,
        )
    if kind == "PAULI_ROTATION":
        matrices = {"X": x, "Z": z}
        pauli = np.kron(
            matrices[operation["paulis"][0]],
            matrices[operation["paulis"][1]],
        )
        return (
            np.cos(angle / 2.0) * np.eye(4, dtype=np.complex128)
            - 1j * np.sin(angle / 2.0) * pauli
        )
    raise ValueError(f"unsupported operation kind: {kind!r}")


def _validate_numpy_gate(
    operation: Mapping[str, Any],
    gate: np.ndarray,
) -> tuple[float, float]:
    observed = np.asarray(gate)
    kind = operation["kind"]
    if kind == "H":
        expected = np.asarray(
            [[1.0, 1.0], [1.0, -1.0]],
            dtype=np.complex128,
        ) / np.sqrt(2.0)
    else:
        angle = float(operation["angle_rad"])
        if kind == "RY":
            expected = np.asarray(
                [
                    [np.cos(angle / 2.0), -np.sin(angle / 2.0)],
                    [np.sin(angle / 2.0), np.cos(angle / 2.0)],
                ],
                dtype=np.complex128,
            )
        elif kind == "PAULI_ROTATION":
            x = np.asarray([[0, 1], [1, 0]], dtype=np.complex128)
            z = np.asarray([[1, 0], [0, -1]], dtype=np.complex128)
            matrices = {"X": x, "Z": z}
            pauli = np.kron(
                matrices[operation["paulis"][0]],
                matrices[operation["paulis"][1]],
            )
            expected = (
                np.cos(angle / 2.0) * np.eye(4, dtype=np.complex128)
                - 1j * np.sin(angle / 2.0) * pauli
            )
        else:
            raise ValueError(f"unsupported operation kind: {kind!r}")
    if observed.dtype != np.complex128 or observed.shape != expected.shape:
        raise RuntimeError(
            f"gate matrix contract drift at operation {operation['index']}"
        )
    semantic_residual = float(np.max(np.abs(observed - expected)))
    identity = np.eye(observed.shape[0], dtype=np.complex128)
    unitarity_residual = float(
        np.max(np.abs(observed.conj().T @ observed - identity))
    )
    if unitarity_residual > 1e-12:
        raise RuntimeError(
            f"nonunitary gate at operation {operation['index']}: "
            f"{unitarity_residual}"
        )
    if semantic_residual > 1e-12:
        raise RuntimeError(
            f"gate half-angle/matrix mismatch at operation "
            f"{operation['index']}: {semantic_residual}"
        )
    return unitarity_residual, semantic_residual


def _canonical_torch_device_name(device_name: str) -> str:
    return "cuda:0" if device_name == "cuda" else device_name


def _torch_converter(device_name: str) -> tuple[Any, Any]:
    import torch

    if device_name == "auto":
        device_name = "cuda" if torch.cuda.is_available() else "cpu"
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable in Quimb worker")
    device_name = _canonical_torch_device_name(device_name)
    device = torch.device(device_name)
    if device.type == "cuda":
        torch.cuda.set_device(device)
        torch.cuda.reset_peak_memory_stats(device)

    def convert(value: Any) -> Any:
        return torch.as_tensor(
            value,
            dtype=torch.complex128,
            device=device,
        )

    return device, convert


def evolve_quimb(
    fixture: Mapping[str, Any],
    *,
    max_bond: int,
    device_name: str,
    optimize: str,
) -> tuple[np.ndarray, dict[str, Any]]:
    import quimb.tensor as qtn
    import torch

    if (
        isinstance(max_bond, bool)
        or not isinstance(max_bond, int)
        or max_bond < 1
    ):
        raise ValueError("max_bond must be a positive integer")
    device, converter = _torch_converter(device_name)
    edges = [
        (edge["a"], edge["b"])
        for edge in fixture["edges_in_execution_order"]
    ]
    if len(edges) != len({frozenset(edge) for edge in edges}):
        raise ValueError("fixture contains duplicate geometry edges")

    circuit = qtn.CircuitPEPSSimpleUpdate(
        N=fixture["site_count"],
        edges=edges,
        max_bond=max_bond,
        cutoff=0.0,
        renorm=False,
        gauge_smudge=GAUGE_SMUDGE,
        dtype="complex128",
        to_backend=converter,
        convert_eager=True,
    )
    if tuple(circuit.sites) != tuple(range(fixture["site_count"])):
        raise RuntimeError(
            f"Quimb site order drift: {circuit.sites!r}"
        )

    started = time.perf_counter()
    max_gate_unitarity_residual = 0.0
    max_gate_semantic_residual = 0.0
    for operation_index, operation in enumerate(fixture["operations"]):
        gate_matrix = _numpy_gate(operation)
        unitarity_residual, semantic_residual = _validate_numpy_gate(
            operation,
            gate_matrix,
        )
        max_gate_unitarity_residual = max(
            max_gate_unitarity_residual,
            unitarity_residual,
        )
        max_gate_semantic_residual = max(
            max_gate_semantic_residual,
            semantic_residual,
        )
        gate = qtn.Gate.from_raw(
            gate_matrix,
            qubits=operation["targets"],
        )
        circuit.apply_gate(gate)
        if (
            (operation_index + 1) % 25 == 0
            or operation_index + 1 == fixture["operation_count"]
        ):
            print(
                f"quimb D={max_bond} operation "
                f"{operation_index + 1}/{fixture['operation_count']} "
                f"actual_max_bond={circuit.psi.max_bond()}",
                flush=True,
            )

    evolution_seconds = time.perf_counter() - started
    actual_max_bond = int(circuit.psi.max_bond())
    if actual_max_bond > max_bond:
        raise RuntimeError("Quimb exceeded the declared state-bond cap")

    contraction_started = time.perf_counter()
    dense = circuit.to_dense(optimize=optimize)
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    contraction_seconds = time.perf_counter() - contraction_started
    if isinstance(dense, torch.Tensor):
        dense_numpy = np.asarray(dense.detach().cpu().numpy()).reshape(-1)
    else:
        dense_numpy = np.asarray(dense).reshape(-1)
    if dense_numpy.shape != (1 << fixture["site_count"],):
        raise RuntimeError(
            f"Quimb dense-state shape drift: {dense_numpy.shape!r}"
        )
    if dense_numpy.dtype != np.complex128:
        raise RuntimeError(
            f"Quimb dense state dtype drifted to {dense_numpy.dtype!r}"
        )
    if not np.isfinite(dense_numpy).all():
        raise RuntimeError("Quimb dense state contains non-finite amplitudes")
    norm_squared = float(np.vdot(dense_numpy, dense_numpy).real)
    if not np.isfinite(norm_squared) or norm_squared <= 0.0:
        raise RuntimeError(f"invalid Quimb state norm: {norm_squared!r}")

    peak_device_bytes = 0
    device_identity: dict[str, Any] = {
        "type": device.type,
        "torch_version": metadata.version("torch"),
        "torch_build_cuda": torch.version.cuda,
    }
    if device.type == "cuda":
        properties = torch.cuda.get_device_properties(device)
        peak_device_bytes = int(torch.cuda.max_memory_allocated(device))
        device_identity.update(
            {
                "name": properties.name,
                "total_memory_bytes": int(properties.total_memory),
                "compute_capability": [
                    int(properties.major),
                    int(properties.minor),
                ],
            }
        )
    diagnostics = {
        "requested_max_bond": max_bond,
        "actual_max_bond": actual_max_bond,
        "cutoff": 0.0,
        "gauge_smudge": GAUGE_SMUDGE,
        "renorm": False,
        "operation_count": circuit.num_gates,
        "evolution_seconds": evolution_seconds,
        "exact_dense_contraction_seconds": contraction_seconds,
        "contraction_optimizer": optimize,
        "norm_squared": norm_squared,
        "norm_residual": abs(norm_squared - 1.0),
        "max_gate_unitarity_residual": max_gate_unitarity_residual,
        "max_gate_semantic_residual": max_gate_semantic_residual,
        "peak_device_allocated_bytes": peak_device_bytes,
        "device": device_identity,
    }
    return dense_numpy, diagnostics


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--max-bond", type=int, required=True)
    parser.add_argument("--output-state", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
    )
    parser.add_argument(
        "--optimize",
        default="auto-hq",
        help="Exact contraction path optimizer passed to Quimb.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.output_state.resolve() == args.output_summary.resolve():
        raise ValueError("state and summary outputs must be distinct")
    process_isolation = _verify_process_isolation()
    committed_inputs = _verify_committed_inputs()
    environment_lock = _verify_environment_lock()
    clone_identity = _verify_pristine_clone()
    installed_identity = _verify_installed_quimb()
    fixture, fixture_file_hash, fixture_canonical_hash = _read_fixture(
        args.fixture
    )
    state, diagnostics = evolve_quimb(
        fixture,
        max_bond=args.max_bond,
        device_name=args.device,
        optimize=args.optimize,
    )
    _atomic_save_npy(args.output_state, state)
    summary = {
        "schema": RESULT_SCHEMA,
        "status": "completed",
        "claim_boundary": fixture["claim_boundary"],
        "fixture": {
            "path": str(args.fixture.resolve()),
            "file_sha256": fixture_file_hash,
            "canonical_sha256": fixture_canonical_hash,
            "schema": fixture["schema"],
            "distance_label": fixture["distance_label"],
            "operation_count": fixture["operation_count"],
        },
        "state": {
            "path": str(args.output_state.resolve()),
            "file_sha256": _file_sha256(args.output_state),
            "shape": list(state.shape),
            "dtype": str(state.dtype),
            "source_kind": "complete_complex128_state_vector",
            "amplitude_convention": fixture["amplitude_convention"],
        },
        "diagnostics": diagnostics,
        "quimb_source_clone": clone_identity,
        "installed_quimb": installed_identity,
        "environment_lock": environment_lock,
        "provenance": {
            "git_head": committed_inputs["git_head"],
            "committed_input_sha256": committed_inputs["sha256"],
            "worker_path": str(Path(__file__).resolve()),
            "worker_sha256": _file_sha256(Path(__file__).resolve()),
            "process_isolation": process_isolation,
            "python_peak_rss_kib": int(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            ),
        },
    }
    _atomic_write_json(args.output_summary, summary)
    print(json.dumps(summary, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
