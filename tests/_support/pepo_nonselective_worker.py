"""Fresh-child workers for the high-memory PEPO nonselective comparison."""

from __future__ import annotations

import argparse
import faulthandler
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from typing import Mapping

import numpy as np


faulthandler.enable(all_threads=True)


REPO = Path(__file__).resolve().parents[2]
TESTS = REPO / "tests"
sys.path.insert(0, str(TESTS))

SCHEMA = "error_coupling_simulator.pepo_nonselective_reference.v1"
SEED = 160
N_OPS = 6
LEAK_PUMP = (0, 2, 4, 6)
ROUNDS = 2
BOND_CAP = 8
MAX_ABS_LIMIT = 1.0e-2


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_hashes() -> dict[str, str]:
    relative_paths = (
        "src/error_coupling_simulator/carrier/within_cycle.py",
        "src/error_coupling_simulator/frontend/xzzx_parser.py",
        "src/error_coupling_simulator/mechanisms/qutrit_leakage.py",
        "src/error_coupling_simulator/carrier/pepo/dynamics.py",
        "src/error_coupling_simulator/carrier/pepo/layout.py",
        "src/error_coupling_simulator/carrier/exact/qutrit_dm.py",
        "tests/_support/pepo_density.py",
        "tests/_support/pepo_nonselective_worker.py",
        "tests/test_pepo_density_nonselective_round.py",
    )
    return {relative: _sha256(REPO / relative) for relative in relative_paths}


def _external_input_hashes() -> dict[str, str]:
    from error_coupling_simulator.frontend import xzzx_parser as xp

    paths = (*xp.default_r01_paths(), *xp.default_r10_paths())
    return {str(path.resolve()): _sha256(path) for path in paths}


def _cell_sha256(cell: Mapping[str, object]) -> str:
    """Fingerprint the shared physical inputs without sharing either propagator."""

    import torch

    digest = hashlib.sha256()

    def update(value) -> None:
        if torch.is_tensor(value):
            array = value.detach().cpu().contiguous().numpy()
            digest.update(b"tensor\0")
            digest.update(str(array.dtype).encode("ascii"))
            digest.update(json.dumps(list(array.shape)).encode("ascii"))
            digest.update(array.tobytes(order="C"))
            return
        if isinstance(value, Mapping):
            digest.update(b"mapping\0")
            for key in sorted(value, key=lambda item: repr(item)):
                update(key)
                update(value[key])
            return
        if isinstance(value, (list, tuple)):
            digest.update(b"sequence\0")
            digest.update(str(len(value)).encode("ascii"))
            for item in value:
                update(item)
            return
        if value is None or isinstance(value, (str, int, float, bool)):
            digest.update(b"scalar\0")
            digest.update(json.dumps(value, sort_keys=True).encode("utf-8"))
            return
        raise TypeError(f"unsupported cell-fingerprint value: {type(value).__name__}")

    for name in ("theta", "leak_t", "leak_list", "streams", "stabs"):
        update(name)
        update(cell[name])
    return digest.hexdigest()


def _atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _configuration() -> dict:
    return {
        "seed": SEED,
        "n_ops": N_OPS,
        "leak_pump": list(LEAK_PUMP),
        "rounds": ROUNDS,
        "bond_cap": BOND_CAP,
        "max_abs_limit": MAX_ABS_LIMIT,
    }


def _configuration_sha256() -> str:
    encoded = json.dumps(
        _configuration(),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_reference(nonce: str, artifact: Path, manifest: Path) -> None:
    import torch

    from _support.pepo_density import (
        ARM,
        B_BIAS,
        build_schedule,
        build_within_cycle_cell,
        prep_reference,
        referee_nonselective_round,
    )

    cell = build_within_cycle_cell(build_schedule())
    cell_sha256 = _cell_sha256(cell)
    stabilizers = [dict(paulis) for paulis in cell["stabs"]]
    reference = prep_reference(
        cell,
        seed=SEED,
        n_ops=N_OPS,
        leak_pump=LEAK_PUMP,
    )
    for _ in range(ROUNDS):
        referee_nonselective_round(reference, stabilizers, B_BIAS, ARM)

    temporary = artifact.with_name(f".{artifact.name}.tmp")
    shape = tuple(int(dim) for dim in reference.rho.shape)
    if reference.rho.dtype != torch.complex128:
        raise RuntimeError(f"unexpected exact-reference dtype: {reference.rho.dtype}")
    dtype = np.dtype(np.complex128)
    array_digest = hashlib.sha256()
    mapped = np.lib.format.open_memmap(
        temporary,
        mode="w+",
        dtype=dtype,
        shape=shape,
    )
    for row0 in range(0, shape[0], 256):
        host_block = np.ascontiguousarray(
            reference.rho[row0 : row0 + 256].detach().cpu().numpy()
        )
        mapped[row0 : row0 + host_block.shape[0]] = host_block
        array_digest.update(host_block.tobytes(order="C"))
        del host_block
    mapped.flush()
    del mapped
    descriptor = os.open(temporary, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, artifact)
    payload = {
        "schema": SCHEMA,
        "nonce": nonce,
        "reference_scope": (
            "independent_propagation_given_shared_specified_channel_"
            "and_separately_checked_initial_state"
        ),
        "configuration": _configuration(),
        "configuration_sha256": _configuration_sha256(),
        "source_sha256": _source_hashes(),
        "external_input_sha256": _external_input_hashes(),
        "cell_sha256": cell_sha256,
        "artifact": {
            "file": artifact.name,
            "shape": list(shape),
            "dtype": str(dtype),
            "bytes": artifact.stat().st_size,
            "array_sha256": array_digest.hexdigest(),
        },
    }
    _atomic_json(manifest, payload)
    torch.cuda.synchronize()
    del reference, cell


def verify_carrier(
    nonce: str,
    artifact: Path,
    manifest: Path,
    result_path: Path,
) -> None:
    import torch

    from _support.pepo_density import (
        ARM,
        B_BIAS,
        build_schedule,
        build_within_cycle_cell,
        pepo_modules,
        prep_state,
    )

    payload = json.loads(manifest.read_text(encoding="utf-8"))
    print("carrier: manifest loaded", flush=True)
    if payload.get("schema") != SCHEMA:
        raise RuntimeError(f"unexpected reference schema: {payload.get('schema')!r}")
    if payload.get("nonce") != nonce:
        raise RuntimeError("reference nonce does not match this invocation")
    if payload.get("configuration") != _configuration():
        raise RuntimeError("reference configuration does not match the current worker")
    if payload.get("configuration_sha256") != _configuration_sha256():
        raise RuntimeError("reference case fingerprint does not match the current worker")
    if payload.get("source_sha256") != _source_hashes():
        raise RuntimeError("reference source hashes do not match the current checkout")
    if payload.get("external_input_sha256") != _external_input_hashes():
        raise RuntimeError("reference dataset hashes do not match the current inputs")
    if payload.get("artifact", {}).get("file") != artifact.name:
        raise RuntimeError("reference manifest does not bind the supplied artifact")
    if int(payload["artifact"]["bytes"]) != artifact.stat().st_size:
        raise RuntimeError("reference artifact size does not match its manifest")

    reference = np.load(artifact, mmap_mode="r", allow_pickle=False)
    print("carrier: reference mmap opened", flush=True)
    if list(reference.shape) != payload["artifact"]["shape"]:
        raise RuntimeError("reference artifact shape does not match its manifest")
    if str(reference.dtype) != payload["artifact"]["dtype"]:
        raise RuntimeError("reference artifact dtype does not match its manifest")

    layout, dynamics, _ = pepo_modules()
    cell = build_within_cycle_cell(build_schedule())
    torch.cuda.synchronize()
    print("carrier: specified channel built", flush=True)
    if payload.get("cell_sha256") != _cell_sha256(cell):
        raise RuntimeError("reference channel/cell fingerprint does not match")
    stabilizers = [dict(paulis) for paulis in cell["stabs"]]
    state = prep_state(
        cell,
        seed=SEED,
        n_ops=N_OPS,
        leak_pump=LEAK_PUMP,
    )
    torch.cuda.synchronize()
    print("carrier: initial PEPO token program complete", flush=True)
    for _ in range(ROUNDS):
        print(f"carrier: starting nonselective round {_ + 1}", flush=True)
        dynamics.nonselective_round(state, stabilizers, B_BIAS, ARM, BOND_CAP)
        torch.cuda.synchronize()
        print(f"carrier: completed nonselective round {_ + 1}", flush=True)

    entries = [
        entry
        for entry in state.ledger
        if isinstance(entry, dict) and entry.get("op") == "ntu_truncate"
    ]
    if not entries:
        raise AssertionError("no NTU ledger entry: the truncation path did not execute")
    if not any(int(entry["exact_rank"]) > BOND_CAP for entry in entries):
        raise AssertionError(f"bond cap {BOND_CAP} never constrained an insertion rank")
    for entry in entries:
        if float(entry["discarded"]) < 0.0:
            raise AssertionError(f"negative discarded weight: {entry}")
        if "precut_discarded" not in entry:
            raise AssertionError(f"missing precut ledger value: {entry}")
        if not math.isfinite(float(entry["ntu_eps"])):
            raise AssertionError(f"non-finite NTU residual: {entry}")

    dense = layout.dense_rho(state)
    if tuple(dense.shape) != tuple(reference.shape):
        raise AssertionError(f"shape mismatch: {tuple(dense.shape)} vs {reference.shape}")
    worst = 0.0
    array_digest = hashlib.sha256()
    # Keep the comparison transfer below 80 MiB so it cannot perturb the
    # high-water PEPO allocation whose value is under test.
    block_rows = 256
    for row0 in range(0, dense.shape[0], block_rows):
        host_block = np.array(reference[row0 : row0 + block_rows], copy=True)
        array_digest.update(host_block.tobytes(order="C"))
        reference_block = torch.from_numpy(host_block).to(dense.device)
        delta = float((dense[row0 : row0 + block_rows] - reference_block).abs().max())
        if not math.isfinite(delta):
            raise RuntimeError("non-finite value in PEPO/reference comparison")
        worst = max(worst, delta)
        del reference_block, host_block
    if array_digest.hexdigest() != payload["artifact"]["array_sha256"]:
        raise RuntimeError("reference array content hash does not match its manifest")
    if worst > MAX_ABS_LIMIT:
        raise AssertionError(
            f"two-round truncated PEPO differs from exact reference by {worst:.3e}"
        )

    _atomic_json(
        result_path,
        {
            "schema": "error_coupling_simulator.pepo_nonselective_result.v1",
            "nonce": nonce,
            "reference_manifest_sha256": _sha256(manifest),
            "source_sha256": _source_hashes(),
            "max_abs_difference": worst,
            "max_abs_limit": MAX_ABS_LIMIT,
            "ntu_entries": len(entries),
            "cap_was_binding": True,
        },
    )
    torch.cuda.synchronize()
    del dense, state, cell, reference


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    reference = subparsers.add_parser("reference")
    reference.add_argument("nonce")
    reference.add_argument("artifact", type=Path)
    reference.add_argument("manifest", type=Path)
    carrier = subparsers.add_parser("carrier")
    carrier.add_argument("nonce")
    carrier.add_argument("artifact", type=Path)
    carrier.add_argument("manifest", type=Path)
    carrier.add_argument("result", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "reference":
        build_reference(args.nonce, args.artifact, args.manifest)
    else:
        verify_carrier(args.nonce, args.artifact, args.manifest, args.result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
