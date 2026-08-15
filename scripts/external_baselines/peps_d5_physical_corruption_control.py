#!/usr/bin/env python3
"""Demonstrate sensitivity to the frozen d5 operation-156 sign corruption.

The correct reference must already have been generated from the pinned neutral
fixture.  This control intentionally mutates only operation 156 after fixture
validation, replays that corrupted circuit through the independent dense
route, and requires the complete-state fidelity drop to exceed 1e-4 before
any external d5 candidate is run.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Mapping

import numpy as np

import peps_d5_dense_reference as dense_reference


RESULT_SCHEMA = (
    "error_coupling_simulator.external.peps_d5_physical_corruption_control.v1"
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
    "scripts/external_baselines/peps_d5_physical_corruption_control.py",
    "tests/test_external_peps_d5_pure_state_fidelity.py",
)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
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


def _verify_frozen_inputs() -> dict[str, Any]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    hashes: dict[str, str] = {}
    for relative in COMMITTED_INPUTS:
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", relative],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        changed = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--", relative],
            cwd=REPO,
        )
        if tracked.returncode != 0 or changed.returncode != 0:
            raise RuntimeError(
                f"corruption-control input is not frozen: {relative}"
            )
        hashes[relative] = _file_sha256(REPO / relative)
    return {"git_head": head, "committed_input_sha256": hashes}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--reference-state", type=Path, required=True)
    parser.add_argument("--reference-summary", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    provenance = _verify_frozen_inputs()
    fixture, _file_hash, canonical_hash = dense_reference._read_fixture(
        args.fixture
    )
    if fixture["distance_label"] != 5:
        raise ValueError("physical corruption control requires frozen d5")
    operation = fixture["operations"][156]
    expected_operation = {
        "index": 156,
        "kind": "PAULI_ROTATION",
        "targets": [11, 12],
        "paulis": ["Z", "X"],
        "angle_rad": "0.31",
        "cycle": 2,
        "edge_color": "horizontal_odd",
    }
    if operation != expected_operation:
        raise RuntimeError("frozen operation 156 identity drifted")

    reference_summary = json.loads(
        args.reference_summary.read_text(encoding="utf-8")
    )
    if (
        reference_summary.get("schema") != dense_reference.RESULT_SCHEMA
        or reference_summary.get("status") != "completed"
        or reference_summary.get("fixture", {}).get("canonical_sha256")
        != canonical_hash
    ):
        raise ValueError("reference summary does not bind the frozen fixture")
    state_metadata = reference_summary.get("state", {})
    if (
        Path(state_metadata.get("path", "")).resolve()
        != args.reference_state.resolve()
        or state_metadata.get("file_sha256")
        != _file_sha256(args.reference_state)
    ):
        raise ValueError("reference state identity mismatch")
    reference_state = np.load(
        args.reference_state,
        mmap_mode="r",
        allow_pickle=False,
    )
    if (
        reference_state.shape != (1 << 25,)
        or reference_state.dtype != np.complex128
    ):
        raise ValueError("reference state is not complete d5 complex128")

    corrupted_fixture = copy.deepcopy(fixture)
    corrupted_fixture["operations"][156]["angle_rad"] = "-0.31"
    corrupted_state, diagnostics = dense_reference.evolve_torch(
        corrupted_fixture,
        device_name=args.device,
    )
    fidelity = dense_reference.normalized_fidelity(
        reference_state,
        corrupted_state,
    )
    fidelity_drop = 1.0 - fidelity
    passed = fidelity_drop > 1e-4
    if not passed:
        raise RuntimeError(
            f"operation-156 corruption was inert: 1-F={fidelity_drop}"
        )
    result = {
        "schema": RESULT_SCHEMA,
        "status": "completed",
        "fixture_canonical_sha256": canonical_hash,
        "corruption": {
            "operation_index": 156,
            "original_angle_rad": "0.31",
            "corrupted_angle_rad": "-0.31",
            "targets": [11, 12],
            "paulis": ["Z", "X"],
        },
        "normalized_complete_state_fidelity": fidelity,
        "fidelity_drop": fidelity_drop,
        "required_minimum_drop": 1e-4,
        "passed": passed,
        "corrupted_dense_diagnostics": diagnostics,
        "provenance": {
            **provenance,
            "worker_path": str(Path(__file__).resolve()),
            "worker_sha256": _file_sha256(Path(__file__).resolve()),
            "reference_state_sha256": state_metadata["file_sha256"],
            "reference_summary_sha256": _file_sha256(args.reference_summary),
        },
    }
    _atomic_json(args.output_json, result)
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
