#!/usr/bin/env python3
"""Materialize a complete complex128 state with commit-bound Pepsy.

This worker accepts only the frozen neutral d3/d5 pure-state fixture.  It
applies the gate stream through Pepsy's public finite-PEPS gate surface and
then performs an exact contraction with every physical index left open in the
fixture's declared order.  The only successful payload is the complete
``2**N`` complex128 vector.  Resource refusal is emitted as ``UNAVAILABLE``;
no local truncation score, boundary residual, or retained-weight diagnostic
can stand in for the vector.

The worker deliberately computes no fidelity.  The root comparator owns the
normalized overlap with its implementation-independent dense reference.
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
import shutil
import subprocess
import sys
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
    "error_coupling_simulator.external.pepsy_peps_d5_state.v1"
)
ENVIRONMENT_LOCK_SCHEMA = (
    "error_coupling_simulator.environment_lock.pepsy_peps_d5.v1"
)
ENVIRONMENT_NAME = "ecs-baseline-pepsy"
EXPECTED_PEPSY_ORIGIN = (
    "https://github.com/quantinuum-dev/pepsy.git"
)
EXPECTED_PEPSY_COMMIT = "27cb956ec88a739daece90407833bd3c3f8e1d8f"
EXPECTED_PEPSY_TREE = "933de533b0fb4775987656f4a18adefbcdcbf2a9"
REPO = Path(__file__).resolve().parents[2]
PEPSY_CLONE = REPO / "external" / "baselines" / "pepsy"
ENVIRONMENT_LOCK = (
    REPO / "baseline-environment-pepsy-linux-64.lock.json"
)
COMMITTED_INPUTS = (
    "baseline-environment-pepsy-linux-64.lock.json",
    "docs/METRICS.md",
    (
        "docs/simulator_validation/"
        "PEPS_D5_PURE_STATE_FIDELITY_LITERATURE_CLOSURE_2026-07-26.md"
    ),
    (
        "docs/simulator_validation/"
        "PEPS_D5_PURE_STATE_FIDELITY_PREREG_2026-07-26.md"
    ),
    "scripts/external_baselines/build_pepsy_baseline_environment.py",
    "scripts/external_baselines/emit_peps_d5_pure_state_fixture.py",
    "scripts/external_baselines/pepsy_peps_d5_state_worker.py",
    "tests/test_external_peps_d5_pure_state_fidelity.py",
)
DEFAULT_MAX_DENSE_BYTES = 2 * 1024**3
DEFAULT_MAX_CONTRACTION_INTERMEDIATE_BYTES = 28 * 1024**3
DEFAULT_MAX_HOST_RSS_BYTES = 64 * 1024**3
DEFAULT_MAX_DEVICE_ALLOCATION_BYTES = 28 * 1024**3
GATE_RESIDUAL_LIMIT = 1.0e-12
SERIAL_CONTRACTION_POLICY = "auto-hq-serial"
_MEMORY_ERROR_MARKERS = (
    "out of memory",
    "cannot allocate memory",
    "not enough memory",
    "cuda error: out of memory",
)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError(f"duplicate JSON key: {key!r}")
        output[key] = value
    return output


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _strict_json_bytes(raw: bytes) -> Any:
    return json.loads(
        raw,
        object_pairs_hook=_strict_object,
        parse_constant=_reject_json_constant,
    )


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to replace existing output: {path}")
    encoded = (
        json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
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


def _run(
    command: Sequence[str],
    *,
    cwd: Path = REPO,
    timeout: int = 900,
) -> str:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): "
            f"{' '.join(command)}\n"
            f"{completed.stdout[-4000:]}\n{completed.stderr[-4000:]}"
        )
    return completed.stdout


def _git(*arguments: str) -> str:
    return _run(["git", *arguments], cwd=PEPSY_CLONE).strip()


def _verify_process_isolation() -> dict[str, Any]:
    if os.environ.get("CONDA_DEFAULT_ENV") != ENVIRONMENT_NAME:
        raise RuntimeError(
            f"worker must run in Conda environment {ENVIRONMENT_NAME!r}"
        )
    if Path(sys.prefix).resolve().name != ENVIRONMENT_NAME:
        raise RuntimeError(
            f"Python prefix is not the isolated environment: {sys.prefix}"
        )
    if os.environ.get("PYTHONPATH"):
        raise RuntimeError("PYTHONPATH must be absent for the isolated worker")
    if not sys.flags.no_user_site:
        raise RuntimeError(
            "user-site imports must be disabled with PYTHONNOUSERSITE=1"
        )
    if os.environ.get("VIRTUAL_ENV"):
        raise RuntimeError("VIRTUAL_ENV must be absent for the Conda worker")
    return {
        "conda_default_env": os.environ["CONDA_DEFAULT_ENV"],
        "python_executable": str(Path(sys.executable).resolve()),
        "python_prefix": str(Path(sys.prefix).resolve()),
        "python_version": sys.version.split()[0],
        "pythonpath_absent": True,
        "user_site_disabled": True,
        "virtual_env_absent": True,
    }


def _verify_pristine_clone() -> dict[str, Any]:
    if not PEPSY_CLONE.is_dir():
        raise RuntimeError(f"missing Pepsy full clone: {PEPSY_CLONE}")
    commit = _git("rev-parse", "HEAD")
    tree = _git("rev-parse", "HEAD^{tree}")
    origin = _git("remote", "get-url", "origin")
    if commit != EXPECTED_PEPSY_COMMIT:
        raise RuntimeError(
            f"Pepsy clone HEAD {commit} != {EXPECTED_PEPSY_COMMIT}"
        )
    if tree != EXPECTED_PEPSY_TREE:
        raise RuntimeError(
            f"Pepsy clone tree {tree} != {EXPECTED_PEPSY_TREE}"
        )
    if origin != EXPECTED_PEPSY_ORIGIN:
        raise RuntimeError(f"unexpected Pepsy origin: {origin!r}")
    if _git("rev-parse", "--is-shallow-repository") != "false":
        raise RuntimeError("Pepsy source clone is shallow")
    status = _git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignored",
    )
    if status:
        raise RuntimeError(
            "Pepsy source clone is not pristine (ignored paths included):\n"
            f"{status}"
        )
    return {
        "path": str(PEPSY_CLONE.resolve()),
        "origin": origin,
        "commit": commit,
        "tree": tree,
        "is_shallow": False,
        "clean_including_ignored": True,
        "license_sha256": _file_sha256(PEPSY_CLONE / "LICENSE"),
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
        if name in rows:
            raise RuntimeError(f"duplicate installed distribution: {name}")
        direct_url = None
        record_path = None
        for item in distribution.files or ():
            if item.name == "direct_url.json":
                direct_url = _strict_json_bytes(
                    Path(distribution.locate_file(item)).read_bytes()
                )
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


def _tracked_package_sources() -> tuple[str, ...]:
    names = _git("ls-files", "src/pepsy").splitlines()
    sources = tuple(
        sorted(
            name
            for name in names
            if name.endswith((".py", ".json", ".toml", ".txt"))
            and (PEPSY_CLONE / name).is_file()
        )
    )
    if not sources:
        raise RuntimeError("Pepsy tracked package-source inventory is empty")
    return sources


def _installed_pepsy_source_identity() -> dict[str, Any]:
    import pepsy

    package_root = Path(pepsy.__file__).resolve().parent
    prefix = Path(sys.prefix).resolve()
    try:
        package_root.relative_to(prefix)
    except ValueError as error:
        raise RuntimeError(
            f"Pepsy import escaped the isolated environment: {package_root}"
        ) from error
    try:
        package_root.relative_to(PEPSY_CLONE.resolve())
    except ValueError:
        pass
    else:
        raise RuntimeError("worker imported Pepsy directly from the clone")

    relative_hashes: dict[str, str] = {}
    mismatches: list[str] = []
    for clone_relative in _tracked_package_sources():
        package_relative = clone_relative.removeprefix("src/pepsy/")
        clone_hash = _file_sha256(PEPSY_CLONE / clone_relative)
        installed_path = package_root / package_relative
        if not installed_path.is_file():
            mismatches.append(f"{package_relative}:missing")
            continue
        installed_hash = _file_sha256(installed_path)
        if installed_hash != clone_hash:
            mismatches.append(f"{package_relative}:content")
            continue
        relative_hashes[f"pepsy/{package_relative}"] = clone_hash
    if mismatches:
        raise RuntimeError(
            "installed Pepsy sources differ from the pristine clone: "
            f"{mismatches[:20]}"
        )
    digest = hashlib.sha256()
    for relative, value in sorted(relative_hashes.items()):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(value.encode("ascii"))
        digest.update(b"\n")
    return {
        "installed_source_root": str(package_root),
        "tracked_source_file_count": len(relative_hashes),
        "tracked_source_manifest_sha256": digest.hexdigest(),
        "all_tracked_package_sources_match_pristine_clone": True,
    }


def _conda_explicit_urls() -> list[str]:
    conda = os.environ.get("CONDA_EXE") or shutil.which("conda")
    if conda is None:
        raise RuntimeError("could not locate conda for lock conformance")
    output = _run(
        [
            conda,
            "list",
            "--prefix",
            str(Path(sys.prefix).resolve()),
            "--explicit",
            "--sha256",
        ]
    )
    return [
        line.strip()
        for line in output.splitlines()
        if line.strip().startswith("http")
    ]


def _pip_freeze() -> list[str]:
    output = _run(
        [
            sys.executable,
            "-m",
            "pip",
            "freeze",
            "--all",
        ]
    )
    return sorted(line.strip() for line in output.splitlines() if line.strip())


def _verify_environment_lock() -> dict[str, Any]:
    raw = ENVIRONMENT_LOCK.read_bytes()
    payload = _strict_json_bytes(raw)
    if not isinstance(payload, dict):
        raise RuntimeError("Pepsy environment lock root is not an object")
    if payload.get("schema") != ENVIRONMENT_LOCK_SCHEMA:
        raise RuntimeError("Pepsy environment lock schema mismatch")
    if payload.get("environment_name") != ENVIRONMENT_NAME:
        raise RuntimeError("Pepsy environment lock name mismatch")
    if payload.get("platform") != "linux-64":
        raise RuntimeError("Pepsy environment lock platform mismatch")
    upstream = payload.get("upstream", {})
    if (
        upstream.get("origin") != EXPECTED_PEPSY_ORIGIN
        or upstream.get("commit") != EXPECTED_PEPSY_COMMIT
        or upstream.get("tree") != EXPECTED_PEPSY_TREE
        or upstream.get("runtime_is_vcs_bound") is not True
    ):
        raise RuntimeError("Pepsy environment lock source identity mismatch")
    expected_prefix = Path(
        payload["environment_prefix_at_lock_time"]
    ).resolve()
    if expected_prefix != Path(sys.prefix).resolve():
        raise RuntimeError(
            f"environment prefix drift: {sys.prefix} != {expected_prefix}"
        )

    observed_records = _runtime_distribution_records()
    if observed_records != payload.get("pip_distribution_records"):
        raise RuntimeError(
            "installed Python distribution records differ from the Pepsy lock"
        )
    observed_freeze = _pip_freeze()
    if observed_freeze != payload.get("pip_freeze_all"):
        raise RuntimeError("pip freeze differs from the Pepsy lock")
    observed_conda = _conda_explicit_urls()
    if observed_conda != payload.get("conda_explicit_sha256_urls"):
        raise RuntimeError("Conda explicit URLs differ from the Pepsy lock")
    if payload.get("pip_check") != "No broken requirements found.":
        raise RuntimeError("Pepsy environment lock did not pass pip check")

    pepsy_record = observed_records.get("pepsy", {})
    vcs = (pepsy_record.get("direct_url") or {}).get("vcs_info", {})
    if (
        vcs.get("vcs") != "git"
        or vcs.get("commit_id") != EXPECTED_PEPSY_COMMIT
        or vcs.get("requested_revision") != EXPECTED_PEPSY_COMMIT
    ):
        raise RuntimeError("installed Pepsy VCS binding mismatch")
    installed_source = _installed_pepsy_source_identity()
    expected_source = payload.get("installed_pepsy_source", {})
    for key in (
        "tracked_source_file_count",
        "tracked_source_manifest_sha256",
        "all_tracked_package_sources_match_pristine_clone",
    ):
        if installed_source.get(key) != expected_source.get(key):
            raise RuntimeError(
                f"installed Pepsy source identity mismatch at {key}"
            )
    return {
        "path": str(ENVIRONMENT_LOCK.resolve()),
        "file_sha256": hashlib.sha256(raw).hexdigest(),
        "schema": payload["schema"],
        "environment_name": payload["environment_name"],
        "authoritative_runtime_conformance_checked": True,
        "conda_explicit_urls_exact": True,
        "pip_freeze_exact": True,
        "pip_distribution_records_exact": True,
        "installed_pepsy_source": installed_source,
        "selected_distribution_records": payload[
            "selected_distribution_records"
        ],
        "recreation_sequence_is_fully_hash_pinned": payload[
            "recreation_sequence_is_fully_hash_pinned"
        ],
    }


def _verify_committed_inputs() -> dict[str, Any]:
    head = _run(["git", "rev-parse", "HEAD"]).strip()
    if not re.fullmatch(r"[0-9a-f]{40,64}", head):
        raise RuntimeError(f"invalid project Git HEAD: {head!r}")
    hashes: dict[str, str] = {}
    blobs: dict[str, str] = {}
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
        blobs[relative] = _run(
            ["git", "rev-parse", f"HEAD:{relative}"]
        ).strip()
    return {
        "git_head": head,
        "relevant_inputs_match_head": True,
        "sha256": hashes,
        "git_blob": blobs,
    }


def _read_fixture(path: Path) -> tuple[dict[str, Any], str, str]:
    raw = path.read_bytes()
    payload = _strict_json_bytes(raw)
    if not isinstance(payload, dict) or payload.get("schema") != FIXTURE_SCHEMA:
        raise ValueError("unsupported PEPS pure-state fixture")
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


def _gate_semantic_residual(
    operation: Mapping[str, Any],
    gate: np.ndarray,
) -> float:
    """Compare the emitted gate with a separately evaluated matrix exponential."""
    from scipy.linalg import expm

    x = np.asarray([[0, 1], [1, 0]], dtype=np.complex128)
    y = np.asarray([[0, -1j], [1j, 0]], dtype=np.complex128)
    z = np.asarray([[1, 0], [0, -1]], dtype=np.complex128)
    kind = operation["kind"]
    if kind == "H":
        expected = (
            np.asarray([[1, 1], [1, -1]], dtype=np.complex128)
            / np.sqrt(2)
        )
    elif kind == "RY":
        angle = float(operation["angle_rad"])
        expected = expm(-0.5j * angle * y)
    elif kind == "PAULI_ROTATION":
        angle = float(operation["angle_rad"])
        matrices = {"X": x, "Z": z}
        generator = np.kron(
            matrices[operation["paulis"][0]],
            matrices[operation["paulis"][1]],
        )
        expected = expm(-0.5j * angle * generator)
    else:
        raise ValueError(f"unsupported operation kind: {kind!r}")
    return float(np.max(np.abs(gate - expected)))


def _validated_numpy_gate(
    operation: Mapping[str, Any],
) -> tuple[np.ndarray, float, float]:
    """Build and fail-closed validate one frozen complex128 gate."""
    gate = _numpy_gate(operation)
    if gate.dtype != np.complex128:
        raise RuntimeError(
            f"gate dtype drifted from complex128 to {gate.dtype!r}"
        )
    if gate.shape not in {(2, 2), (4, 4)}:
        raise RuntimeError(f"gate shape drifted: {gate.shape!r}")
    if not np.isfinite(gate).all():
        raise RuntimeError("gate contains a non-finite matrix entry")
    identity = np.eye(gate.shape[0], dtype=np.complex128)
    unitary_residual = float(
        np.max(np.abs(gate.conj().T @ gate - identity))
    )
    semantic_residual = _gate_semantic_residual(operation, gate)
    if (
        not np.isfinite(unitary_residual)
        or unitary_residual > GATE_RESIDUAL_LIMIT
    ):
        raise RuntimeError(
            "gate unitarity residual exceeds the frozen limit: "
            f"{unitary_residual!r} > {GATE_RESIDUAL_LIMIT!r}"
        )
    if (
        not np.isfinite(semantic_residual)
        or semantic_residual > GATE_RESIDUAL_LIMIT
    ):
        raise RuntimeError(
            "gate closed-form half-angle residual exceeds the frozen limit: "
            f"{semantic_residual!r} > {GATE_RESIDUAL_LIMIT!r}"
        )
    return gate, unitary_residual, semantic_residual


def _validate_positive_integer(value: int, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _resource_plan(
    fixture: Mapping[str, Any],
    *,
    max_dense_bytes: int,
    max_host_rss_bytes: int,
    max_device_allocation_bytes: int,
    max_contraction_intermediate_bytes: int,
    output_state: Path,
) -> dict[str, Any]:
    site_count = int(fixture["site_count"])
    dense_elements = 1 << site_count
    dense_bytes = dense_elements * np.dtype(np.complex128).itemsize
    output_state.parent.mkdir(parents=True, exist_ok=True)
    disk_free_bytes = int(shutil.disk_usage(output_state.parent).free)
    return {
        "dense_elements": dense_elements,
        "dense_dtype": "complex128",
        "dense_payload_bytes": dense_bytes,
        "max_dense_bytes": _validate_positive_integer(
            max_dense_bytes,
            name="max_dense_bytes",
        ),
        "max_host_rss_bytes": _validate_positive_integer(
            max_host_rss_bytes,
            name="max_host_rss_bytes",
        ),
        "max_device_allocation_bytes": _validate_positive_integer(
            max_device_allocation_bytes,
            name="max_device_allocation_bytes",
        ),
        "max_contraction_intermediate_bytes": _validate_positive_integer(
            max_contraction_intermediate_bytes,
            name="max_contraction_intermediate_bytes",
        ),
        "output_filesystem_free_bytes_before_execution": disk_free_bytes,
        "minimum_output_filesystem_bytes": dense_bytes + 64 * 1024**2,
        "resource_limits_are_numerical_only": True,
    }


def _static_unavailable_reason(
    resource_plan: Mapping[str, Any],
) -> dict[str, Any] | None:
    if (
        resource_plan["dense_payload_bytes"]
        > resource_plan["max_dense_bytes"]
    ):
        return {
            "code": "dense_payload_exceeds_declared_limit",
            "required_bytes": resource_plan["dense_payload_bytes"],
            "limit_bytes": resource_plan["max_dense_bytes"],
        }
    if (
        resource_plan["minimum_output_filesystem_bytes"]
        > resource_plan["output_filesystem_free_bytes_before_execution"]
    ):
        return {
            "code": "insufficient_output_filesystem_space",
            "required_bytes": resource_plan[
                "minimum_output_filesystem_bytes"
            ],
            "available_bytes": resource_plan[
                "output_filesystem_free_bytes_before_execution"
            ],
        }
    return None


def _resolve_device(device_name: str) -> tuple[Any, dict[str, Any]]:
    import torch

    if device_name == "auto":
        device_name = "cuda" if torch.cuda.is_available() else "cpu"
    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable in worker process")
    if device_name == "cuda":
        device_name = "cuda:0"
    device = torch.device(device_name)
    identity: dict[str, Any] = {
        "type": device.type,
        "torch_version": metadata.version("torch"),
        "torch_build_cuda": torch.version.cuda,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }
    if device.type == "cuda":
        torch.cuda.set_device(device)
        torch.cuda.reset_peak_memory_stats(device)
        properties = torch.cuda.get_device_properties(device)
        free_bytes, total_bytes = torch.cuda.mem_get_info(device)
        identity.update(
            {
                "name": properties.name,
                "total_memory_bytes": int(total_bytes),
                "free_memory_bytes_before_execution": int(free_bytes),
                "compute_capability": [
                    int(properties.major),
                    int(properties.minor),
                ],
            }
        )
    return device, identity


def evolve_and_materialize(
    fixture: Mapping[str, Any],
    *,
    max_bond: int,
    device: Any,
    contraction_optimize: str,
    max_contraction_intermediate_bytes: int,
) -> tuple[np.ndarray | None, dict[str, Any], dict[str, Any] | None]:
    """Return the complete vector, diagnostics, and optional unavailable row."""
    import pepsy
    import torch

    max_bond = _validate_positive_integer(max_bond, name="max_bond")
    exact_bond_ceiling = int(fixture["exact_per_edge_bond_ceiling"])
    if max_bond > exact_bond_ceiling:
        raise ValueError(
            f"max_bond {max_bond} exceeds frozen ceiling "
            f"{exact_bond_ceiling}"
        )
    rows = int(fixture["lattice"]["rows"])
    columns = int(fixture["lattice"]["columns"])
    state = pepsy.ps_to_peps(
        rows,
        columns,
        dtype="complex128",
        theta=0.0,
    )
    state.apply_to_arrays(
        pepsy.backend_torch(device=str(device), dtype=torch.complex128)
    )
    expected_output_inds = tuple(
        state.site_ind(*divmod(qubit, columns))
        for qubit in range(int(fixture["site_count"]))
    )
    if set(state.outer_inds()) != set(expected_output_inds):
        raise RuntimeError("Pepsy initial physical-index set drifted")

    gate_cache: dict[tuple[Any, ...], Any] = {}
    max_gate_unitarity_residual = 0.0
    max_gate_semantic_residual = 0.0
    applied_operation_count = 0
    started = time.perf_counter()
    with torch.no_grad():
        for operation_index, operation in enumerate(fixture["operations"]):
            cache_key = (
                operation["kind"],
                operation.get("angle_rad"),
                tuple(operation.get("paulis", ())),
            )
            gate = gate_cache.get(cache_key)
            if gate is None:
                (
                    gate_numpy,
                    unitary_residual,
                    semantic_residual,
                ) = _validated_numpy_gate(operation)
                max_gate_unitarity_residual = max(
                    max_gate_unitarity_residual,
                    unitary_residual,
                )
                max_gate_semantic_residual = max(
                    max_gate_semantic_residual,
                    semantic_residual,
                )
                gate = torch.as_tensor(
                    gate_numpy,
                    dtype=torch.complex128,
                    device=device,
                )
                gate_cache[cache_key] = gate
            where = tuple(
                divmod(int(target), columns)
                for target in operation["targets"]
            )
            contract: bool | str = (
                True if len(where) == 1 else "reduce-split"
            )
            pepsy.gate(
                state,
                gate,
                where=where,
                contract=contract,
                max_bond=max_bond,
                cutoff=0.0,
                cutoff_mode="rsum2",
                path_canonize=False,
                path_compress=False,
                inplace=True,
            )
            applied_operation_count += 1
            actual_max_bond = int(state.max_bond())
            if actual_max_bond > max_bond:
                raise RuntimeError(
                    "Pepsy exceeded the declared state-bond cap"
                )
            if (
                (operation_index + 1) % 25 == 0
                or operation_index + 1 == fixture["operation_count"]
            ):
                print(
                    f"pepsy D={max_bond} operation "
                    f"{operation_index + 1}/{fixture['operation_count']} "
                    f"actual_max_bond={actual_max_bond}",
                    file=sys.stderr,
                    flush=True,
                )
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    evolution_seconds = time.perf_counter() - started
    if applied_operation_count != fixture["operation_count"]:
        raise RuntimeError(
            "Pepsy applied-operation count differs from the fixture"
        )

    contraction_optimizer, optimizer_identity = (
        _serial_contraction_optimizer(contraction_optimize)
    )
    path_started = time.perf_counter()
    contraction_info = state.contraction_info(
        output_inds=expected_output_inds,
        optimize=contraction_optimizer,
    )
    path_search_seconds = time.perf_counter() - path_started
    largest_intermediate_elements = int(
        contraction_info.largest_intermediate
    )
    largest_intermediate_bytes = (
        largest_intermediate_elements * np.dtype(np.complex128).itemsize
    )
    diagnostics: dict[str, Any] = {
        "api": "pepsy.gate",
        "requested_max_bond": max_bond,
        "actual_max_bond": int(state.max_bond()),
        "cutoff": 0.0,
        "cutoff_mode": "rsum2",
        "operation_count": applied_operation_count,
        "max_gate_unitarity_residual": max_gate_unitarity_residual,
        "max_gate_semantic_residual": max_gate_semantic_residual,
        "evolution_seconds": evolution_seconds,
        "contraction_optimizer": optimizer_identity,
        "contraction_path_search_seconds": path_search_seconds,
        "contraction_largest_intermediate_elements": (
            largest_intermediate_elements
        ),
        "contraction_largest_intermediate_bytes_complex128": (
            largest_intermediate_bytes
        ),
        "full_physical_output_index_order": list(expected_output_inds),
        "complete_dense_vector_required": True,
        "local_diagnostics_used_as_fidelity": False,
    }
    if largest_intermediate_bytes > max_contraction_intermediate_bytes:
        return (
            None,
            diagnostics,
            {
                "code": "exact_contraction_intermediate_exceeds_limit",
                "required_bytes": largest_intermediate_bytes,
                "limit_bytes": max_contraction_intermediate_bytes,
            },
        )

    contraction_started = time.perf_counter()
    with torch.no_grad():
        dense = state.to_dense(
            expected_output_inds,
            optimize=contraction_optimizer,
        )
    if device.type == "cuda":
        torch.cuda.synchronize(device)
    diagnostics["exact_dense_contraction_seconds"] = (
        time.perf_counter() - contraction_started
    )
    if not isinstance(dense, torch.Tensor):
        raise RuntimeError(
            f"Pepsy exact contraction returned {type(dense).__name__}, "
            "expected a Torch tensor"
        )
    if dense.dtype != torch.complex128:
        raise RuntimeError(
            f"Pepsy dense state dtype drifted to {dense.dtype}"
        )
    dense_numpy = np.asarray(dense.detach().cpu().numpy()).reshape(-1)
    expected_shape = (1 << int(fixture["site_count"]),)
    if dense_numpy.shape != expected_shape:
        raise RuntimeError(
            f"Pepsy dense-state shape drift: {dense_numpy.shape!r}"
        )
    if dense_numpy.dtype != np.complex128:
        raise RuntimeError(
            f"Pepsy dense state dtype drifted to {dense_numpy.dtype!r}"
        )
    if not np.isfinite(dense_numpy).all():
        raise RuntimeError("Pepsy dense state contains non-finite amplitudes")
    norm_squared = float(np.vdot(dense_numpy, dense_numpy).real)
    if not np.isfinite(norm_squared) or norm_squared <= 0.0:
        raise RuntimeError(f"invalid Pepsy state norm: {norm_squared!r}")
    diagnostics["norm_squared"] = norm_squared
    diagnostics["norm_residual"] = abs(norm_squared - 1.0)
    return dense_numpy, diagnostics, None


def _current_resource_usage(device: Any) -> dict[str, int]:
    import torch

    peak_device_bytes = 0
    if device.type == "cuda":
        peak_device_bytes = int(torch.cuda.max_memory_allocated(device))
    return {
        "python_peak_rss_bytes": int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        ),
        "peak_device_allocated_bytes": peak_device_bytes,
    }


def _post_execution_unavailable_reason(
    usage: Mapping[str, int],
    resource_plan: Mapping[str, Any],
) -> dict[str, Any] | None:
    if usage["python_peak_rss_bytes"] > resource_plan["max_host_rss_bytes"]:
        return {
            "code": "host_rss_exceeds_declared_limit",
            "observed_bytes": usage["python_peak_rss_bytes"],
            "limit_bytes": resource_plan["max_host_rss_bytes"],
        }
    if (
        usage["peak_device_allocated_bytes"]
        > resource_plan["max_device_allocation_bytes"]
    ):
        return {
            "code": "device_allocation_exceeds_declared_limit",
            "observed_bytes": usage["peak_device_allocated_bytes"],
            "limit_bytes": resource_plan[
                "max_device_allocation_bytes"
            ],
        }
    return None


def _fixture_identity(
    fixture: Mapping[str, Any],
    *,
    path: Path,
    file_hash: str,
    canonical_hash: str,
) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "file_sha256": file_hash,
        "canonical_sha256": canonical_hash,
        "schema": fixture["schema"],
        "distance_label": fixture["distance_label"],
        "site_count": fixture["site_count"],
        "operation_count": fixture["operation_count"],
        "amplitude_convention": fixture["amplitude_convention"],
    }


def _unavailable_summary(
    *,
    fixture: Mapping[str, Any],
    fixture_identity: Mapping[str, Any],
    reason: Mapping[str, Any],
    resource_plan: Mapping[str, Any],
    device_identity: Mapping[str, Any],
    diagnostics: Mapping[str, Any] | None,
    provenance: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema": RESULT_SCHEMA,
        "status": "UNAVAILABLE",
        "claim_boundary": fixture["claim_boundary"],
        "reason": dict(reason),
        "fixture": dict(fixture_identity),
        "state": None,
        "resource_plan": dict(resource_plan),
        "resource_usage": provenance["resource_usage"],
        "device": dict(device_identity),
        "diagnostics": (
            dict(diagnostics) if diagnostics is not None else None
        ),
        "environment_lock": provenance["environment_lock"],
        "pepsy_source_clone": provenance["pepsy_source_clone"],
        "installed_pepsy": provenance["installed_pepsy"],
        "provenance": provenance["provenance"],
        "forbidden_substitute_used": False,
    }


def _is_resource_memory_error(error: BaseException) -> bool:
    if isinstance(error, MemoryError):
        return True
    return any(
        marker in str(error).lower() for marker in _MEMORY_ERROR_MARKERS
    )


def _serial_contraction_optimizer(policy: str) -> tuple[Any, dict[str, Any]]:
    import cotengra

    if policy != SERIAL_CONTRACTION_POLICY:
        raise ValueError(
            f"unsupported contraction policy: {policy!r}"
        )
    optimizer = cotengra.AutoHQOptimizer(parallel=False)
    if getattr(optimizer, "kwargs", {}).get("parallel") is not False:
        raise RuntimeError("Cotengra serial optimizer contract drifted")
    return optimizer, {
        "policy": SERIAL_CONTRACTION_POLICY,
        "implementation": "cotengra.AutoHQOptimizer",
        "cotengra_version": metadata.version("cotengra"),
        "parallel": False,
        "path_search_child_processes": False,
    }


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
        "--contraction-optimize",
        choices=(SERIAL_CONTRACTION_POLICY,),
        default=SERIAL_CONTRACTION_POLICY,
        help="Serial exact-contraction path-search policy.",
    )
    parser.add_argument(
        "--max-dense-bytes",
        type=int,
        default=DEFAULT_MAX_DENSE_BYTES,
    )
    parser.add_argument(
        "--max-contraction-intermediate-bytes",
        type=int,
        default=DEFAULT_MAX_CONTRACTION_INTERMEDIATE_BYTES,
    )
    parser.add_argument(
        "--max-host-rss-bytes",
        type=int,
        default=DEFAULT_MAX_HOST_RSS_BYTES,
    )
    parser.add_argument(
        "--max-device-allocation-bytes",
        type=int,
        default=DEFAULT_MAX_DEVICE_ALLOCATION_BYTES,
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.output_state.resolve() == args.output_summary.resolve():
        raise ValueError("state and summary outputs must be distinct")
    if args.output_state.exists():
        raise FileExistsError(
            f"refusing stale state output: {args.output_state}"
        )
    if args.output_summary.exists():
        raise FileExistsError(
            f"refusing stale summary output: {args.output_summary}"
        )

    isolation = _verify_process_isolation()
    committed_inputs = _verify_committed_inputs()
    clone_identity = _verify_pristine_clone()
    environment_lock = _verify_environment_lock()
    fixture, fixture_file_hash, fixture_canonical_hash = _read_fixture(
        args.fixture
    )
    fixture_identity = _fixture_identity(
        fixture,
        path=args.fixture,
        file_hash=fixture_file_hash,
        canonical_hash=fixture_canonical_hash,
    )
    resource_plan = _resource_plan(
        fixture,
        max_dense_bytes=args.max_dense_bytes,
        max_host_rss_bytes=args.max_host_rss_bytes,
        max_device_allocation_bytes=args.max_device_allocation_bytes,
        max_contraction_intermediate_bytes=(
            args.max_contraction_intermediate_bytes
        ),
        output_state=args.output_state,
    )
    device, device_identity = _resolve_device(args.device)

    def provenance_payload() -> dict[str, Any]:
        installed_pepsy = dict(
            environment_lock["selected_distribution_records"]["pepsy"]
        )
        installed_pepsy["installed_source"] = environment_lock[
            "installed_pepsy_source"
        ]
        return {
            "provenance": {
                "git_head": committed_inputs["git_head"],
                "relevant_inputs_match_head": committed_inputs[
                    "relevant_inputs_match_head"
                ],
                "committed_input_sha256": committed_inputs["sha256"],
                "committed_input_git_blob": committed_inputs["git_blob"],
                "process_isolation": isolation,
                "worker_path": str(Path(__file__).resolve()),
                "worker_sha256": _file_sha256(Path(__file__).resolve()),
            },
            "environment_lock": environment_lock,
            "pepsy_source_clone": clone_identity,
            "installed_pepsy": installed_pepsy,
            "resource_usage": _current_resource_usage(device),
        }

    unavailable_reason = _static_unavailable_reason(resource_plan)
    if unavailable_reason is not None:
        summary = _unavailable_summary(
            fixture=fixture,
            fixture_identity=fixture_identity,
            reason=unavailable_reason,
            resource_plan=resource_plan,
            device_identity=device_identity,
            diagnostics=None,
            provenance=provenance_payload(),
        )
        _atomic_write_json(args.output_summary, summary)
        print(json.dumps(summary, allow_nan=False, sort_keys=True), flush=True)
        return 0

    try:
        state, diagnostics, unavailable_reason = evolve_and_materialize(
            fixture,
            max_bond=args.max_bond,
            device=device,
            contraction_optimize=args.contraction_optimize,
            max_contraction_intermediate_bytes=(
                args.max_contraction_intermediate_bytes
            ),
        )
    except Exception as error:
        if not _is_resource_memory_error(error):
            raise
        state = None
        diagnostics = None
        unavailable_reason = {
            "code": "memory_allocation_failed",
            "exception_type": type(error).__name__,
            "message": str(error),
        }

    provenance = provenance_payload()
    if unavailable_reason is None:
        unavailable_reason = _post_execution_unavailable_reason(
            provenance["resource_usage"],
            resource_plan,
        )
    if unavailable_reason is not None:
        summary = _unavailable_summary(
            fixture=fixture,
            fixture_identity=fixture_identity,
            reason=unavailable_reason,
            resource_plan=resource_plan,
            device_identity=device_identity,
            diagnostics=diagnostics,
            provenance=provenance,
        )
        _atomic_write_json(args.output_summary, summary)
        print(json.dumps(summary, allow_nan=False, sort_keys=True), flush=True)
        return 0

    if state is None:
        raise RuntimeError("completed Pepsy path returned no dense state")
    _atomic_save_npy(args.output_state, state)
    summary = {
        "schema": RESULT_SCHEMA,
        "status": "completed",
        "claim_boundary": fixture["claim_boundary"],
        "fixture": fixture_identity,
        "state": {
            "path": str(args.output_state.resolve()),
            "file_sha256": _file_sha256(args.output_state),
            "shape": list(state.shape),
            "dtype": str(state.dtype),
            "amplitude_convention": fixture["amplitude_convention"],
            "source_kind": "complete_complex128_state_vector",
            "contains_every_amplitude": True,
        },
        "resource_plan": resource_plan,
        "resource_usage": provenance["resource_usage"],
        "device": device_identity,
        "diagnostics": diagnostics,
        "environment_lock": provenance["environment_lock"],
        "pepsy_source_clone": provenance["pepsy_source_clone"],
        "installed_pepsy": provenance["installed_pepsy"],
        "provenance": provenance["provenance"],
        "forbidden_substitute_used": False,
    }
    _atomic_write_json(args.output_summary, summary)
    print(json.dumps(summary, allow_nan=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
