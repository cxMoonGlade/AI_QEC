#!/usr/bin/env python3
"""Build the independent dense state for the frozen d3/d5 PEPS fixture.

This worker imports no external PEPS implementation.  It reads only the
neutral gate-list fixture, applies the gates directly to a complex128 state
vector, writes the complete vector, and records numerical/provenance evidence.
The d3 control can additionally be replayed by a separate NumPy bit-index
implementation.
"""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import resource
import subprocess
import tempfile
import time
from typing import Any, Mapping, Sequence

import numpy as np

from emit_peps_d5_pure_state_fixture import (
    FIXTURE_SCHEMA,
    canonical_sha256,
    validate_fixture,
)


RESULT_SCHEMA = (
    "error_coupling_simulator.external.peps_d5_dense_reference.v1"
)
REPO = Path(__file__).resolve().parents[2]
COMMITTED_INPUTS = (
    "docs/METRICS.md",
    (
        "docs/simulator_validation/"
        "PEPS_D5_PURE_STATE_FIDELITY_LITERATURE_CLOSURE_2026-07-26.md"
    ),
    (
        "docs/simulator_validation/"
        "PEPS_D5_PURE_STATE_FIDELITY_PREREG_2026-07-26.md"
    ),
    "scripts/external_baselines/emit_peps_d5_pure_state_fixture.py",
    "scripts/external_baselines/peps_d5_dense_reference.py",
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


def _git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _verify_committed_inputs() -> dict[str, str]:
    head = _git_head()
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
    return {"git_head": head, **hashes}


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


def _torch_matrices(torch: Any, *, device: Any) -> dict[str, Any]:
    dtype = torch.complex128
    one = torch.tensor(1.0, dtype=dtype, device=device)
    zero = torch.tensor(0.0, dtype=dtype, device=device)
    x = torch.stack(
        (torch.stack((zero, one)), torch.stack((one, zero)))
    )
    z = torch.stack(
        (torch.stack((one, zero)), torch.stack((zero, -one)))
    )
    h = torch.stack(
        (torch.stack((one, one)), torch.stack((one, -one)))
    ) / np.sqrt(2.0)
    eye2 = torch.eye(2, dtype=dtype, device=device)
    eye4 = torch.eye(4, dtype=dtype, device=device)
    return {"I2": eye2, "I4": eye4, "X": x, "Z": z, "H": h}


def _canonical_torch_device_name(device_name: str) -> str:
    return "cuda:0" if device_name == "cuda" else device_name


def _torch_gate_for_operation(
    torch: Any,
    operation: Mapping[str, Any],
    matrices: Mapping[str, Any],
) -> Any:
    kind = operation["kind"]
    if kind == "H":
        return matrices["H"]
    angle = float(operation["angle_rad"])
    cosine = torch.cos(
        torch.tensor(angle / 2.0, dtype=torch.float64, device=matrices["I2"].device)
    )
    sine = torch.sin(
        torch.tensor(angle / 2.0, dtype=torch.float64, device=matrices["I2"].device)
    )
    if kind == "RY":
        return torch.stack(
            (
                torch.stack((cosine, -sine)),
                torch.stack((sine, cosine)),
            )
        ).to(torch.complex128)
    if kind == "PAULI_ROTATION":
        pauli = torch.kron(
            matrices[operation["paulis"][0]],
            matrices[operation["paulis"][1]],
        )
        return cosine * matrices["I4"] - 1j * sine * pauli
    raise ValueError(f"unsupported operation kind: {kind!r}")


def _expected_numpy_gate(operation: Mapping[str, Any]) -> np.ndarray:
    one = np.asarray(1.0, dtype=np.complex128)
    zero = np.asarray(0.0, dtype=np.complex128)
    x = np.asarray([[zero, one], [one, zero]], dtype=np.complex128)
    z = np.asarray([[one, zero], [zero, -one]], dtype=np.complex128)
    kind = operation["kind"]
    if kind == "H":
        return np.asarray([[one, one], [one, -one]]) / np.sqrt(2.0)
    angle = float(operation["angle_rad"])
    if kind == "RY":
        return np.asarray(
            [
                [np.cos(angle / 2.0), -np.sin(angle / 2.0)],
                [np.sin(angle / 2.0), np.cos(angle / 2.0)],
            ],
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


def _validate_gate_matrix_numpy(
    operation: Mapping[str, Any],
    gate: np.ndarray,
) -> tuple[float, float]:
    observed = np.asarray(gate)
    expected = _expected_numpy_gate(operation)
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


def _apply_torch_gate(
    torch: Any,
    state: Any,
    gate: Any,
    targets: Sequence[int],
    *,
    site_count: int,
) -> Any:
    target_tuple = tuple(targets)
    remaining = tuple(
        axis for axis in range(site_count) if axis not in target_tuple
    )
    permutation = remaining + target_tuple
    inverse = [0] * site_count
    for new_axis, old_axis in enumerate(permutation):
        inverse[old_axis] = new_axis
    local_dimension = 1 << len(target_tuple)
    tensor = state.reshape((2,) * site_count)
    matrix = tensor.permute(permutation).reshape(-1, local_dimension)
    updated = matrix @ gate.transpose(0, 1)
    return (
        updated.reshape((2,) * site_count)
        .permute(tuple(inverse))
        .contiguous()
        .reshape(-1)
    )


def evolve_torch(
    fixture: Mapping[str, Any],
    *,
    device_name: str,
    progress_every: int = 25,
) -> tuple[np.ndarray, dict[str, Any]]:
    import torch

    if device_name == "auto":
        device_name = "cuda" if torch.cuda.is_available() else "cpu"
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is unavailable in process")
    device_name = _canonical_torch_device_name(device_name)
    device = torch.device(device_name)
    if device.type == "cuda":
        torch.cuda.set_device(device)
        torch.cuda.reset_peak_memory_stats(device)

    site_count = int(fixture["site_count"])
    state = torch.zeros(
        1 << site_count,
        dtype=torch.complex128,
        device=device,
    )
    state[0] = 1.0 + 0.0j
    matrices = _torch_matrices(torch, device=device)
    gate_cache: dict[tuple[Any, ...], Any] = {}
    max_unitarity_residual = 0.0
    max_gate_semantic_residual = 0.0
    applied_operation_count = 0
    started = time.perf_counter()

    with torch.no_grad():
        for operation_index, operation in enumerate(fixture["operations"]):
            key = (
                operation["kind"],
                operation.get("angle_rad"),
                tuple(operation.get("paulis", ())),
            )
            gate = gate_cache.get(key)
            if gate is None:
                gate = _torch_gate_for_operation(torch, operation, matrices)
                gate_numpy = np.asarray(gate.detach().cpu().numpy())
                residual, semantic_residual = _validate_gate_matrix_numpy(
                    operation,
                    gate_numpy,
                )
                max_unitarity_residual = max(
                    max_unitarity_residual,
                    float(residual),
                )
                max_gate_semantic_residual = max(
                    max_gate_semantic_residual,
                    semantic_residual,
                )
                gate_cache[key] = gate
            state = _apply_torch_gate(
                torch,
                state,
                gate,
                operation["targets"],
                site_count=site_count,
            )
            applied_operation_count += 1
            if progress_every and (
                (operation_index + 1) % progress_every == 0
                or operation_index + 1 == fixture["operation_count"]
            ):
                print(
                    f"dense-reference operation "
                    f"{operation_index + 1}/{fixture['operation_count']}",
                    flush=True,
                )

        if device.type == "cuda":
            torch.cuda.synchronize(device)
        elapsed = time.perf_counter() - started
        norm_squared = torch.vdot(state, state).real.item()
        if not np.isfinite(norm_squared) or norm_squared <= 0.0:
            raise RuntimeError(f"invalid dense-state norm: {norm_squared!r}")
        norm_residual = abs(float(norm_squared) - 1.0)
        if norm_residual > 1e-12:
            raise RuntimeError(
                f"dense reference norm residual exceeded 1e-12: "
                f"{norm_residual}"
            )
        state_numpy = np.asarray(state.detach().cpu().numpy())
        if state_numpy.dtype != np.complex128:
            raise RuntimeError(
                f"dense state dtype drifted to {state_numpy.dtype!r}"
            )
        if not np.isfinite(state_numpy).all():
            raise RuntimeError("dense state contains a non-finite amplitude")

    device_identity: dict[str, Any] = {
        "type": device.type,
        "torch_version": metadata.version("torch"),
        "torch_build_cuda": torch.version.cuda,
    }
    peak_device_bytes = 0
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
        "device": device_identity,
        "elapsed_seconds": elapsed,
        "peak_device_allocated_bytes": peak_device_bytes,
        "norm_squared": float(norm_squared),
        "norm_residual": norm_residual,
        "max_gate_unitarity_residual": max_unitarity_residual,
        "max_gate_semantic_residual": max_gate_semantic_residual,
        "operation_count": applied_operation_count,
        "unique_gate_matrix_count": len(gate_cache),
    }
    return state_numpy, diagnostics


def _replace_target_bits(
    index: int,
    *,
    targets: Sequence[int],
    local_value: int,
    site_count: int,
) -> int:
    output = index
    arity = len(targets)
    for local_axis, target in enumerate(targets):
        shift = site_count - 1 - target
        output &= ~(1 << shift)
        bit = (local_value >> (arity - 1 - local_axis)) & 1
        output |= bit << shift
    return output


def evolve_numpy_bit_index(fixture: Mapping[str, Any]) -> np.ndarray:
    """Independent d3 replay using explicit computational-basis bit edits."""

    site_count = int(fixture["site_count"])
    if site_count > 9:
        raise ValueError("the independent NumPy replay is bounded to d3")
    state = np.zeros(1 << site_count, dtype=np.complex128)
    state[0] = 1.0
    x = np.asarray([[0, 1], [1, 0]], dtype=np.complex128)
    z = np.asarray([[1, 0], [0, -1]], dtype=np.complex128)
    h = np.asarray([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2)
    matrices = {"X": x, "Z": z}

    for operation in fixture["operations"]:
        kind = operation["kind"]
        if kind == "H":
            gate = h
        elif kind == "RY":
            angle = float(operation["angle_rad"])
            cosine = np.cos(angle / 2.0)
            sine = np.sin(angle / 2.0)
            gate = np.asarray(
                [[cosine, -sine], [sine, cosine]],
                dtype=np.complex128,
            )
        elif kind == "PAULI_ROTATION":
            angle = float(operation["angle_rad"])
            pauli = np.kron(
                matrices[operation["paulis"][0]],
                matrices[operation["paulis"][1]],
            )
            gate = (
                np.cos(angle / 2.0) * np.eye(4, dtype=np.complex128)
                - 1j * np.sin(angle / 2.0) * pauli
            )
        else:
            raise ValueError(f"unsupported operation kind: {kind!r}")

        targets = tuple(operation["targets"])
        arity = len(targets)
        updated = np.zeros_like(state)
        for input_index, amplitude in enumerate(state):
            local_input = 0
            for target in targets:
                local_input = (local_input << 1) | (
                    (input_index >> (site_count - 1 - target)) & 1
                )
            for local_output in range(1 << arity):
                output_index = _replace_target_bits(
                    input_index,
                    targets=targets,
                    local_value=local_output,
                    site_count=site_count,
                )
                updated[output_index] += (
                    gate[local_output, local_input] * amplitude
                )
        state = updated
    return state


def normalized_fidelity(left: np.ndarray, right: np.ndarray) -> float:
    if left.shape != right.shape or left.dtype != right.dtype:
        raise ValueError("fidelity inputs must have equal shape and dtype")
    if left.dtype != np.complex128:
        raise ValueError("fidelity inputs must use complex128")
    left_norm = float(np.vdot(left, left).real)
    right_norm = float(np.vdot(right, right).real)
    if (
        not np.isfinite(left_norm)
        or not np.isfinite(right_norm)
        or left_norm <= 0.0
        or right_norm <= 0.0
    ):
        raise ValueError("fidelity inputs must have finite positive norms")
    overlap = np.vdot(left, right)
    value = float(abs(overlap) ** 2 / (left_norm * right_norm))
    if not np.isfinite(value) or not -1e-10 <= value <= 1.0 + 1e-10:
        raise ValueError(f"invalid normalized fidelity: {value!r}")
    return min(1.0, max(0.0, value))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output-state", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
    )
    parser.add_argument(
        "--require-numpy-crosscheck",
        action="store_true",
        help="For the d3 fixture, require the separate NumPy bit-index replay.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    committed_inputs = _verify_committed_inputs()
    if args.output_state.resolve() == args.output_summary.resolve():
        raise ValueError("state and summary outputs must be distinct")
    fixture, fixture_file_hash, fixture_canonical_hash = _read_fixture(
        args.fixture
    )
    if args.require_numpy_crosscheck and fixture["distance_label"] != 3:
        raise ValueError("the NumPy cross-check is bounded to the d3 fixture")

    state, diagnostics = evolve_torch(
        fixture,
        device_name=args.device,
    )
    numpy_crosscheck: dict[str, Any] | None = None
    if args.require_numpy_crosscheck:
        independent = evolve_numpy_bit_index(fixture)
        max_difference = float(np.max(np.abs(state - independent)))
        fidelity = normalized_fidelity(state, independent)
        numpy_crosscheck = {
            "max_amplitude_difference": max_difference,
            "normalized_fidelity": fidelity,
            "passed": max_difference <= 1e-12 and 1.0 - fidelity <= 1e-12,
        }
        if not numpy_crosscheck["passed"]:
            raise RuntimeError(
                f"d3 independent dense cross-check failed: {numpy_crosscheck}"
            )

    _atomic_save_npy(args.output_state, state)
    state_hash = _file_sha256(args.output_state)
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
            "file_sha256": state_hash,
            "shape": list(state.shape),
            "dtype": str(state.dtype),
            "source_kind": "complete_complex128_state_vector",
            "amplitude_convention": fixture["amplitude_convention"],
        },
        "diagnostics": diagnostics,
        "numpy_d3_crosscheck": numpy_crosscheck,
        "provenance": {
            "git_head": committed_inputs.pop("git_head"),
            "committed_input_sha256": committed_inputs,
            "worker_path": str(Path(__file__).resolve()),
            "worker_sha256": _file_sha256(Path(__file__).resolve()),
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
