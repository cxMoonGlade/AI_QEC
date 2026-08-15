#!/usr/bin/env python3
"""Run the heldout-shaped finite-memory sweep as a development diagnostic.

This entry point deliberately does not implement or impersonate the formal
systemd/amendment/held-out path.  It reuses the frozen target-grid fixture
semantics in fresh ordinary subprocesses, retains every raw worker core and
timing trailer inside a development-only binary envelope, and publishes one
claim-ineligible report.  No output from this script is formal evidence.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import secrets
import signal
import stat
import struct
import subprocess
import sys
import tempfile
import time
from typing import Any, BinaryIO, Callable, Mapping, Sequence


_SCRIPT_PATH = Path(__file__).resolve(strict=True)
_SCRIPT_DIR = _SCRIPT_PATH.parent
_REPOSITORY = _SCRIPT_DIR.parent.parent
_PLAN_PATH = _SCRIPT_DIR / "gcapeps_finite_memory_development_sweep.py"
_FIXTURE_PATH = _SCRIPT_DIR / "emit_gcapeps_finite_memory_fixture.py"
_TIMING_PATH = _SCRIPT_DIR / "gcapeps_finite_memory_timing.py"
_ORCHESTRATION_PATH = _SCRIPT_DIR / "gcapeps_finite_memory_orchestration.py"
_FORK_ROOT = _REPOSITORY / "external" / "forks" / "quimb-gcapeps"
_FORK_PIXI_LOCK = _FORK_ROOT / "pixi.lock"

_DEFAULT_FORK_PYTHON = (
    _FORK_ROOT
    / ".pixi"
    / "envs"
    / "testpymid"
    / "bin"
    / "python"
)
_DEFAULT_SDIM_PYTHON = Path(
    "/home/cx/miniforge3/envs/gcapeps-sdim/bin/python"
)

_SCHEMA_PREFIX = "error_coupling_simulator.external.gcapeps_finite_memory."
INPUT_SCHEMA = _SCHEMA_PREFIX + "development_sweep_input.v1"
CHILD_SCHEMA = _SCHEMA_PREFIX + "development_sweep_child.v1"
FIXTURE_ARTIFACT_SCHEMA = _SCHEMA_PREFIX + "development_sweep_fixture.v1"
REPORT_SCHEMA = _SCHEMA_PREFIX + "development_sweep.v1"
PREFLIGHT_SCHEMA = (
    _SCHEMA_PREFIX + "development_interpreter_preflight.v1"
)
PARENT_SOURCE_SCHEMA = _SCHEMA_PREFIX + "development_parent_source.v1"
DEVELOPMENT_SWEEP = "DEVELOPMENT_SWEEP"

SDIM_INVENTORY = "sdim_inventory"
DENSE_REFERENCE = "dense_reference"
PLAIN_EVIDENCE = "plain_evidence"
GCAPEPS_EVIDENCE = "gcapeps_evidence"
PLAIN_PERFORMANCE = "plain_performance"
GCAPEPS_PERFORMANCE = "gcapeps_performance"
SDIM_COMPUTATION = "sdim_computation"
TERMINAL_COMPARATOR = "terminal_comparator"

ROLE_OWNER = {
    SDIM_INVENTORY: "collect_gcapeps_finite_memory_sdim_inventory.py",
    DENSE_REFERENCE: "gcapeps_finite_memory_dense_reference.py",
    PLAIN_EVIDENCE: "plain_quimb_finite_memory_evidence_worker.py",
    GCAPEPS_EVIDENCE: "gcapeps_finite_memory_evidence_worker.py",
    PLAIN_PERFORMANCE: "plain_quimb_finite_memory_performance_worker.py",
    GCAPEPS_PERFORMANCE: "gcapeps_finite_memory_performance_worker.py",
    SDIM_COMPUTATION: "gcapeps_finite_memory_sdim_worker.py",
    TERMINAL_COMPARATOR: "compare_gcapeps_finite_memory_bond32.py",
}
ROLE_CORE_SCHEMA = {
    SDIM_INVENTORY: _SCHEMA_PREFIX + "sdim_inventory.v1",
    DENSE_REFERENCE: _SCHEMA_PREFIX + "dense_reference.v1",
    PLAIN_EVIDENCE: _SCHEMA_PREFIX + "plain_evidence_worker.v1",
    GCAPEPS_EVIDENCE: _SCHEMA_PREFIX + "gcapeps_evidence_worker.v1",
    PLAIN_PERFORMANCE: _SCHEMA_PREFIX + "plain_performance_worker.v1",
    GCAPEPS_PERFORMANCE: _SCHEMA_PREFIX + "gcapeps_performance_worker.v1",
    SDIM_COMPUTATION: _SCHEMA_PREFIX + "sdim_frame_control.v1",
    TERMINAL_COMPARATOR: _SCHEMA_PREFIX + "comparator_worker.v1",
}
FIXTURE_SCHEMA = _SCHEMA_PREFIX + "fixture.v1"
CORE_CAP = {
    SDIM_INVENTORY: 67_108_864,
    DENSE_REFERENCE: 1_073_741_824,
    PLAIN_EVIDENCE: 268_435_456,
    GCAPEPS_EVIDENCE: 268_435_456,
    PLAIN_PERFORMANCE: 67_108_864,
    GCAPEPS_PERFORMANCE: 67_108_864,
    SDIM_COMPUTATION: 67_108_864,
    TERMINAL_COMPARATOR: 67_108_864,
}
TRAILER_CAP = 16_777_216
MANIFEST_CAP = 1_048_576
STDERR_CAP = 1_048_576

ROLE_DEPENDENCIES = {
    SDIM_INVENTORY: (),
    DENSE_REFERENCE: ("fixture",),
    PLAIN_EVIDENCE: ("fixture",),
    GCAPEPS_EVIDENCE: ("fixture",),
    PLAIN_PERFORMANCE: ("fixture",),
    GCAPEPS_PERFORMANCE: ("fixture",),
    SDIM_COMPUTATION: ("fixture", "inventory"),
    TERMINAL_COMPARATOR: (
        "fixture",
        "dense",
        "plain_input1",
        "plain_input2",
        "gcapeps_input1",
        "gcapeps_input2",
        "sdim",
    ),
}
ROLE_PARAMETER_KEYS = {
    SDIM_INVENTORY: frozenset(),
    DENSE_REFERENCE: frozenset(),
    PLAIN_EVIDENCE: frozenset({"input_id"}),
    GCAPEPS_EVIDENCE: frozenset({"input_id"}),
    PLAIN_PERFORMANCE: frozenset(
        {"input_id", "sample_kind", "sample_index"}
    ),
    GCAPEPS_PERFORMANCE: frozenset(
        {"input_id", "sample_kind", "sample_index"}
    ),
    SDIM_COMPUTATION: frozenset(),
    TERMINAL_COMPARATOR: frozenset(),
}
ENTRY_CORE_SCHEMA = {
    "fixture": FIXTURE_SCHEMA,
    "inventory": ROLE_CORE_SCHEMA[SDIM_INVENTORY],
    "dense": ROLE_CORE_SCHEMA[DENSE_REFERENCE],
    "plain_input1": ROLE_CORE_SCHEMA[PLAIN_EVIDENCE],
    "plain_input2": ROLE_CORE_SCHEMA[PLAIN_EVIDENCE],
    "gcapeps_input1": ROLE_CORE_SCHEMA[GCAPEPS_EVIDENCE],
    "gcapeps_input2": ROLE_CORE_SCHEMA[GCAPEPS_EVIDENCE],
    "sdim": ROLE_CORE_SCHEMA[SDIM_COMPUTATION],
}
PREFLIGHT_KEYS = frozenset(
    {
        "schema",
        "run_partition",
        "formal_claim_eligible",
        "is_heldout_evidence",
        "kind",
        "python_executable",
        "python_version",
        "modules",
        "distributions",
        "fork_identity",
        "result_projection_sha256",
    }
)
PREFLIGHT_MODULES = {
    "fork": ("numpy", "quimb", "stim", "quimb.experimental.gcapeps"),
    "sdim": ("sdim", "stim"),
}
PREFLIGHT_DISTRIBUTIONS = {
    "fork": ("numpy", "quimb", "stim"),
    "sdim": ("sdim", "stim"),
}
FORK_COMMIT = "d90bb5ea210e666cbd7ecf8a8b7fa02390519baf"
FORK_TREE = "f7cd3496c48ec69f1800d41eabcaa8d53cab3b5b"
FORK_PIXI_LOCK_SHA256 = (
    "854da99b417c69dbdca4118c2545656470ad4e0f276a606b1b8c3082f795db35"
)


def _load_path(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _canonical(value: Mapping[str, Any] | Sequence[Any]) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_canonical(raw: bytes, *, name: str) -> dict[str, Any]:
    try:
        value = json.loads(
            raw.decode("ascii"),
            object_pairs_hook=_strict_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"nonfinite JSON token: {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{name} is not canonical JSON") from exc
    if not isinstance(value, dict) or _canonical(value) != raw:
        raise ValueError(f"{name} is not compact canonical ASCII JSON")
    return value


def _projection(value: Mapping[str, Any]) -> str:
    projected = dict(value)
    projected.pop("result_projection_sha256", None)
    return hashlib.sha256(_canonical(projected)).hexdigest()


def _plain_int(
    value: Any,
    *,
    name: str,
    minimum: int = 0,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be a plain integer")
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{name} is outside its allowed range")
    return value


def _require_sha256(value: Any, *, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{name} must be a lowercase SHA-256")
    return value


def _read_exact(stream: BinaryIO, count: int) -> bytes:
    chunks: list[bytes] = []
    remaining = count
    while remaining:
        chunk = stream.read(min(remaining, 1024 * 1024))
        if not chunk:
            raise ValueError("binary transport is truncated")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _copy_exact(
    source: BinaryIO,
    destination: BinaryIO,
    count: int,
    *,
    digest: Any | None = None,
) -> None:
    remaining = count
    while remaining:
        chunk = source.read(min(remaining, 1024 * 1024))
        if not chunk:
            raise ValueError("artifact core is truncated")
        destination.write(chunk)
        if digest is not None:
            digest.update(chunk)
        remaining -= len(chunk)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_output(repository: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ("git", "-C", str(repository), *arguments),
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30.0,
    ).stdout


def _collect_repository_source_identity(
    *,
    repository: Path,
    source_relative_paths: Sequence[str],
) -> dict[str, Any]:
    repository = repository.resolve(strict=True)
    if not repository.is_dir():
        raise ValueError("parent repository is not a directory")
    status = _git_output(
        repository,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    status_sha256 = hashlib.sha256(status).hexdigest()
    if status:
        raise RuntimeError(
            "parent repository has tracked or untracked source drift"
        )
    head_commit = _git_output(repository, "rev-parse", "HEAD").decode(
        "ascii", errors="strict"
    ).strip()
    head_tree = _git_output(repository, "rev-parse", "HEAD^{tree}").decode(
        "ascii", errors="strict"
    ).strip()
    for name, value in (("HEAD", head_commit), ("HEAD tree", head_tree)):
        if (
            len(value) != 40
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise RuntimeError(f"parent repository {name} is invalid")
    relative_paths = tuple(sorted(set(source_relative_paths)))
    if not relative_paths:
        raise ValueError("parent source identity requires source files")
    source_files = []
    for raw_relative in relative_paths:
        if not isinstance(raw_relative, str) or not raw_relative:
            raise ValueError("parent source relative path is invalid")
        relative = Path(raw_relative)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("parent source relative path is invalid")
        lexical = repository / relative
        resolved = lexical.resolve(strict=True)
        observed = resolved.stat()
        if (
            resolved != lexical.absolute()
            or not resolved.is_relative_to(repository)
            or not stat.S_ISREG(observed.st_mode)
        ):
            raise RuntimeError("parent source file identity is invalid")
        _git_output(
            repository,
            "ls-files",
            "--error-unmatch",
            "--",
            relative.as_posix(),
        )
        source_files.append(
            {
                "relative_path": relative.as_posix(),
                "realpath": str(resolved),
                "byte_length": observed.st_size,
                "sha256": _file_sha256(resolved),
            }
        )
    payload = {
        "schema": PARENT_SOURCE_SCHEMA,
        "run_partition": DEVELOPMENT_SWEEP,
        "formal_claim_eligible": False,
        "repository_realpath": str(repository),
        "head_commit": head_commit,
        "head_tree": head_tree,
        "status_porcelain_v1_z_sha256": status_sha256,
        "tracked_and_untracked_clean": True,
        "source_files": source_files,
        "result_projection_sha256": "",
    }
    payload["result_projection_sha256"] = _projection(payload)
    return payload


def _parent_source_relative_paths() -> tuple[str, ...]:
    paths = {
        _SCRIPT_PATH,
        _PLAN_PATH,
        _FIXTURE_PATH,
        _TIMING_PATH,
        _ORCHESTRATION_PATH,
        *(_SCRIPT_DIR / owner for owner in ROLE_OWNER.values()),
    }
    return tuple(
        sorted(path.relative_to(_REPOSITORY).as_posix() for path in paths)
    )


def _authenticate_parent_repository() -> dict[str, Any]:
    return _collect_repository_source_identity(
        repository=_REPOSITORY,
        source_relative_paths=_parent_source_relative_paths(),
    )


def _development_report_provenance(
    parent_source_identity: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        parent_source_identity.get("schema") != PARENT_SOURCE_SCHEMA
        or parent_source_identity.get("run_partition") != DEVELOPMENT_SWEEP
        or parent_source_identity.get("formal_claim_eligible") is not False
        or parent_source_identity.get("tracked_and_untracked_clean") is not True
        or parent_source_identity.get("result_projection_sha256")
        != _projection(parent_source_identity)
    ):
        raise ValueError("parent source identity is invalid")
    return {
        "parent_source_identity": dict(parent_source_identity),
        "cpu_affinity_frozen": False,
        "scheduler_migration_controlled": False,
        "timing_portability": (
            "descriptive_development_only_not_a_portable_benchmark"
        ),
    }


def _resolve_development_output_root(
    output_root: Path,
    *,
    repository: Path,
) -> Path:
    resolved_root = Path(os.path.abspath(output_root))
    repository = repository.resolve(strict=True)
    if resolved_root.is_relative_to(repository):
        relative = resolved_root.relative_to(repository).as_posix()
        ignored = subprocess.run(
            (
                "git",
                "-C",
                str(repository),
                "check-ignore",
                "-q",
                "--",
                relative,
            ),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=30.0,
            check=False,
        )
        if ignored.returncode == 1:
            raise ValueError(
                "in-repository development output root must be gitignored"
            )
        if ignored.returncode != 0 or ignored.stderr:
            raise RuntimeError("cannot verify development output ignore rule")
    return resolved_root


def _base_interpreter_identity(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    observed = resolved.stat()
    if not stat.S_ISREG(observed.st_mode) or not os.access(resolved, os.X_OK):
        raise ValueError(f"not an executable interpreter: {resolved}")
    version = subprocess.run(
        (str(resolved), "--version"),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True,
        timeout=10.0,
    ).stdout.decode("utf-8", errors="strict").strip()
    return {
        "path": str(resolved),
        "sha256": _file_sha256(resolved),
        "st_dev": observed.st_dev,
        "st_ino": observed.st_ino,
        "python_version": version,
    }


def _execute_interpreter_preflight(kind: str) -> int:
    import importlib
    import importlib.metadata

    if kind not in PREFLIGHT_MODULES:
        raise ValueError("unknown interpreter preflight kind")
    modules = PREFLIGHT_MODULES[kind]
    distributions = PREFLIGHT_DISTRIBUTIONS[kind]
    module_rows = []
    for name in modules:
        module = importlib.import_module(name)
        origin_raw = getattr(module, "__file__", None)
        if not isinstance(origin_raw, str):
            raise RuntimeError(f"module {name} has no file origin")
        origin = Path(origin_raw).resolve(strict=True)
        module_rows.append(
            {
                "name": name,
                "origin": str(origin),
                "origin_sha256": _file_sha256(origin),
            }
        )
    distribution_rows = [
        {"name": name, "version": importlib.metadata.version(name)}
        for name in distributions
    ]
    versions = {row["name"]: row["version"] for row in distribution_rows}
    if versions.get("stim") != "1.16.0":
        raise RuntimeError("Stim preflight version drifted")
    fork_identity = None
    if kind == "fork":
        checkout = _FORK_ROOT.resolve(strict=True)
        head = subprocess.run(
            ("git", "-C", str(checkout), "rev-parse", "HEAD"),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.decode("ascii", errors="strict").strip()
        tree = subprocess.run(
            ("git", "-C", str(checkout), "rev-parse", "HEAD^{tree}"),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.decode("ascii", errors="strict").strip()
        status = subprocess.run(
            (
                "git",
                "-C",
                str(checkout),
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
            ),
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
        pixi_lock = _FORK_PIXI_LOCK.resolve(strict=True)
        lock_stat = pixi_lock.stat()
        if (
            not pixi_lock.is_relative_to(checkout)
            or not stat.S_ISREG(lock_stat.st_mode)
        ):
            raise RuntimeError("fork preflight pixi.lock is not a regular file")
        pixi_lock_sha256 = _file_sha256(pixi_lock)
        status_sha256 = hashlib.sha256(status).hexdigest()
        if head != FORK_COMMIT:
            raise RuntimeError("fork preflight commit drifted")
        if tree != FORK_TREE:
            raise RuntimeError("fork preflight tree drifted")
        if pixi_lock_sha256 != FORK_PIXI_LOCK_SHA256:
            raise RuntimeError("fork preflight pixi.lock drifted")
        if status:
            raise RuntimeError("fork preflight worktree is dirty")
        origins = {row["name"]: Path(row["origin"]) for row in module_rows}
        for name in ("quimb", "quimb.experimental.gcapeps"):
            if not origins[name].is_relative_to(checkout):
                raise RuntimeError(
                    f"{name} import is not owned by the frozen fork"
                )
        fork_identity = {
            "checkout": str(checkout),
            "commit": head,
            "tree": tree,
            "pixi_lock_realpath": str(pixi_lock),
            "pixi_lock_sha256": pixi_lock_sha256,
            "status_porcelain_v1_z_sha256": status_sha256,
            "tracked_and_untracked_clean": True,
        }
    else:
        if versions.get("sdim") != "1.3.3":
            raise RuntimeError("SDIM preflight version drifted")
    payload = {
        "schema": PREFLIGHT_SCHEMA,
        "run_partition": DEVELOPMENT_SWEEP,
        "formal_claim_eligible": False,
        "is_heldout_evidence": False,
        "kind": kind,
        "python_executable": str(Path(sys.executable).resolve(strict=True)),
        "python_version": sys.version,
        "modules": module_rows,
        "distributions": distribution_rows,
        "fork_identity": fork_identity,
        "result_projection_sha256": "",
    }
    payload["result_projection_sha256"] = _projection(payload)
    _write_all(1, _canonical(payload))
    return 0


def _validate_preflight_payload(
    preflight: Mapping[str, Any],
    *,
    kind: str,
    resolved: Path,
) -> None:
    if set(preflight) != PREFLIGHT_KEYS:
        raise RuntimeError(f"{kind} interpreter preflight has wrong keys")
    if (
        preflight["schema"] != PREFLIGHT_SCHEMA
        or preflight["run_partition"] != DEVELOPMENT_SWEEP
        or preflight["formal_claim_eligible"] is not False
        or preflight["is_heldout_evidence"] is not False
        or preflight["kind"] != kind
        or preflight["result_projection_sha256"] != _projection(preflight)
        or not isinstance(preflight["python_version"], str)
        or not preflight["python_version"]
    ):
        raise RuntimeError(f"{kind} interpreter preflight identity drifted")
    executable = preflight["python_executable"]
    if not isinstance(executable, str) or Path(executable).resolve(
        strict=True
    ) != resolved:
        raise RuntimeError(f"{kind} preflight executable drifted")
    modules = preflight["modules"]
    expected_modules = PREFLIGHT_MODULES[kind]
    if (
        not isinstance(modules, list)
        or len(modules) != len(expected_modules)
        or any(not isinstance(row, Mapping) for row in modules)
        or tuple(row["name"] if "name" in row else None for row in modules)
        != expected_modules
    ):
        raise RuntimeError(f"{kind} preflight module order drifted")
    module_origins: dict[str, Path] = {}
    for row in modules:
        if not isinstance(row, Mapping) or set(row) != {
            "name",
            "origin",
            "origin_sha256",
        }:
            raise RuntimeError(f"{kind} preflight module row has wrong keys")
        origin_raw = row["origin"]
        if not isinstance(origin_raw, str):
            raise RuntimeError(f"{kind} preflight module origin is invalid")
        origin = Path(origin_raw).resolve(strict=True)
        if _file_sha256(origin) != _require_sha256(
            row["origin_sha256"],
            name=f"{kind}.{row['name']}.origin_sha256",
        ):
            raise RuntimeError(f"{kind} preflight module hash drifted")
        module_origins[row["name"]] = origin
    distributions = preflight["distributions"]
    expected_distributions = PREFLIGHT_DISTRIBUTIONS[kind]
    if (
        not isinstance(distributions, list)
        or len(distributions) != len(expected_distributions)
        or any(not isinstance(row, Mapping) for row in distributions)
        or tuple(
            row["name"] if "name" in row else None for row in distributions
        )
        != expected_distributions
    ):
        raise RuntimeError(f"{kind} preflight distribution order drifted")
    versions: dict[str, str] = {}
    for row in distributions:
        if not isinstance(row, Mapping) or set(row) != {"name", "version"}:
            raise RuntimeError(
                f"{kind} preflight distribution row has wrong keys"
            )
        version = row["version"]
        if not isinstance(version, str) or not version:
            raise RuntimeError(f"{kind} preflight version is invalid")
        versions[row["name"]] = version
    if versions.get("stim") != "1.16.0":
        raise RuntimeError("Stim preflight version drifted")
    fork_identity = preflight["fork_identity"]
    if kind == "fork":
        if not isinstance(fork_identity, Mapping) or set(fork_identity) != {
            "checkout",
            "commit",
            "tree",
            "pixi_lock_realpath",
            "pixi_lock_sha256",
            "status_porcelain_v1_z_sha256",
            "tracked_and_untracked_clean",
        }:
            raise RuntimeError("fork preflight identity has wrong keys")
        checkout = _FORK_ROOT.resolve(strict=True)
        pixi_lock = _FORK_PIXI_LOCK.resolve(strict=True)
        empty_status_sha256 = hashlib.sha256(b"").hexdigest()
        if (
            fork_identity["checkout"] != str(checkout)
            or fork_identity["commit"] != FORK_COMMIT
            or fork_identity["tree"] != FORK_TREE
            or fork_identity["pixi_lock_realpath"] != str(pixi_lock)
            or fork_identity["pixi_lock_sha256"]
            != FORK_PIXI_LOCK_SHA256
            or _file_sha256(pixi_lock) != FORK_PIXI_LOCK_SHA256
            or fork_identity["status_porcelain_v1_z_sha256"]
            != empty_status_sha256
            or fork_identity["tracked_and_untracked_clean"] is not True
        ):
            raise RuntimeError("fork preflight repository identity drifted")
        for name in ("quimb", "quimb.experimental.gcapeps"):
            if not module_origins[name].is_relative_to(checkout):
                raise RuntimeError(f"{name} is outside the frozen checkout")
    elif fork_identity is not None or versions.get("sdim") != "1.3.3":
        raise RuntimeError("SDIM preflight identity drifted")


def _authenticate_interpreter(path: Path, *, kind: str) -> dict[str, Any]:
    base = _base_interpreter_identity(path)
    resolved = Path(base["path"])
    completed = subprocess.run(
        (str(resolved), "-I", str(_SCRIPT_PATH), "--preflight", kind),
        cwd=_REPOSITORY,
        env=_child_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60.0,
        check=False,
    )
    if (
        len(completed.stdout) > MANIFEST_CAP
        or len(completed.stderr) > STDERR_CAP
    ):
        raise RuntimeError(f"{kind} interpreter preflight output exceeded cap")
    if completed.returncode != 0 or completed.stderr:
        raise RuntimeError(
            f"{kind} interpreter preflight failed: "
            f"returncode={completed.returncode}, "
            f"stderr_sha256={hashlib.sha256(completed.stderr).hexdigest()}"
        )
    preflight = _parse_canonical(
        completed.stdout,
        name=f"{kind} interpreter preflight",
    )
    _validate_preflight_payload(preflight, kind=kind, resolved=resolved)
    return {**base, "authenticated_preflight": preflight}


@dataclass(frozen=True)
class ArtifactIdentity:
    path: str
    byte_length: int
    sha256: str
    header: Mapping[str, Any]
    core_offset: int
    core_byte_length: int
    trailer_offset: int
    trailer_byte_length: int

    def binding(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
            "artifact_schema": self.header["schema"],
            "source_core_schema": self.header["source_core_schema"],
            "source_core_sha256": self.header["source_core_sha256"],
            "source_core_projection_sha256": self.header[
                "source_core_projection_sha256"
            ],
        }


def _artifact_header(
    *,
    schema: str,
    role: str,
    case_id: str | None,
    role_parameters: Mapping[str, Any],
    source_core_schema: str,
    source_core_projection_sha256: str,
    core_bytes: bytes,
    trailer_bytes: bytes,
    process_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema": schema,
        "run_partition": DEVELOPMENT_SWEEP,
        "formal_claim_eligible": False,
        "is_heldout_evidence": False,
        "execution_class": "claim_ineligible_development_diagnostic",
        "heldout_shaped_fixture_reuse_only": True,
        "transport_equivalent_to_B_CAL_or_B_HELD": False,
        "role": role,
        "case_id": case_id,
        "role_parameters": dict(role_parameters),
        "source_core_schema": source_core_schema,
        "source_core_byte_length": len(core_bytes),
        "source_core_sha256": hashlib.sha256(core_bytes).hexdigest(),
        "source_core_projection_sha256": source_core_projection_sha256,
        "source_trailer_byte_length": len(trailer_bytes),
        "source_trailer_sha256": hashlib.sha256(trailer_bytes).hexdigest(),
        "development_process_receipt": dict(process_receipt),
    }


def _write_all(fd: int, raw: bytes) -> None:
    cursor = 0
    while cursor < len(raw):
        written = os.write(fd, raw[cursor:])
        if written <= 0:
            raise RuntimeError("artifact write made no progress")
        cursor += written


def _publish_binary_artifact(
    path: Path,
    *,
    header: Mapping[str, Any],
    core_bytes: bytes,
    trailer_bytes: bytes,
) -> ArtifactIdentity:
    """Publish one development binary envelope without replacement."""

    if not path.is_absolute():
        raise ValueError("artifact path must be absolute")
    parent = path.parent.resolve(strict=True)
    if parent != Path(os.path.abspath(path.parent)):
        raise ValueError("artifact parent must be a nonsymlink lexical path")
    header_bytes = _canonical(header)
    raw_prefix = struct.pack(">Q", len(header_bytes)) + header_bytes
    raw_middle = struct.pack(">Q", len(core_bytes))
    raw_suffix = struct.pack(">Q", len(trailer_bytes)) + trailer_bytes
    expected_length = (
        len(raw_prefix)
        + len(raw_middle)
        + len(core_bytes)
        + len(raw_suffix)
    )
    temporary = f".{path.name}.tmp-{secrets.token_hex(12)}"
    parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    fd = -1
    linked = False
    try:
        fd = os.open(
            temporary,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | os.O_CLOEXEC,
            0o644,
            dir_fd=parent_fd,
        )
        for raw in (raw_prefix, raw_middle, core_bytes, raw_suffix):
            _write_all(fd, raw)
        os.fsync(fd)
        observed = os.fstat(fd)
        if (
            not stat.S_ISREG(observed.st_mode)
            or stat.S_IMODE(observed.st_mode) != 0o644
            or observed.st_size != expected_length
            or observed.st_nlink != 1
        ):
            raise RuntimeError("temporary artifact identity is invalid")
        os.link(
            temporary,
            path.name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
            follow_symlinks=False,
        )
        linked = True
        os.unlink(temporary, dir_fd=parent_fd)
        os.fsync(parent_fd)
    finally:
        if fd >= 0:
            os.close(fd)
        if not linked:
            try:
                os.unlink(temporary, dir_fd=parent_fd)
            except FileNotFoundError:
                pass
        os.close(parent_fd)
    return _read_artifact_identity(path)


def _read_artifact_identity(path: Path) -> ArtifactIdentity:
    resolved = path.resolve(strict=True)
    observed = resolved.stat()
    if (
        not stat.S_ISREG(observed.st_mode)
        or stat.S_IMODE(observed.st_mode) != 0o644
        or observed.st_nlink != 1
    ):
        raise ValueError("development artifact inode is invalid")
    digest = hashlib.sha256()
    with resolved.open("rb") as source:
        prefix = _read_exact(source, 8)
        digest.update(prefix)
        header_length = struct.unpack(">Q", prefix)[0]
        if header_length > MANIFEST_CAP:
            raise ValueError("development artifact header exceeds cap")
        header_bytes = _read_exact(source, header_length)
        digest.update(header_bytes)
        header = _parse_canonical(header_bytes, name="artifact header")
        if (
            header.get("run_partition") != DEVELOPMENT_SWEEP
            or header.get("formal_claim_eligible") is not False
            or header.get("is_heldout_evidence") is not False
            or header.get("heldout_shaped_fixture_reuse_only") is not True
            or header.get("transport_equivalent_to_B_CAL_or_B_HELD") is not False
        ):
            raise ValueError("artifact claim boundary drifted")
        projection = header.get("source_core_projection_sha256")
        if (
            not isinstance(projection, str)
            or len(projection) != 64
            or any(character not in "0123456789abcdef" for character in projection)
        ):
            raise ValueError("artifact source-core projection hash is invalid")
        core_prefix = _read_exact(source, 8)
        digest.update(core_prefix)
        core_length = struct.unpack(">Q", core_prefix)[0]
        if core_length != header.get("source_core_byte_length"):
            raise ValueError("artifact core length disagrees with header")
        core_offset = source.tell()
        core_digest = hashlib.sha256()
        remaining = core_length
        while remaining:
            chunk = source.read(min(remaining, 1024 * 1024))
            if not chunk:
                raise ValueError("artifact core is truncated")
            digest.update(chunk)
            core_digest.update(chunk)
            remaining -= len(chunk)
        if core_digest.hexdigest() != header.get("source_core_sha256"):
            raise ValueError("artifact core hash disagrees with header")
        trailer_prefix = _read_exact(source, 8)
        digest.update(trailer_prefix)
        trailer_length = struct.unpack(">Q", trailer_prefix)[0]
        if trailer_length != header.get("source_trailer_byte_length"):
            raise ValueError("artifact trailer length disagrees with header")
        trailer_offset = source.tell()
        trailer_digest = hashlib.sha256()
        remaining = trailer_length
        while remaining:
            chunk = source.read(min(remaining, 1024 * 1024))
            if not chunk:
                raise ValueError("artifact trailer is truncated")
            digest.update(chunk)
            trailer_digest.update(chunk)
            remaining -= len(chunk)
        if trailer_digest.hexdigest() != header.get("source_trailer_sha256"):
            raise ValueError("artifact trailer hash disagrees with header")
        if source.read(1):
            raise ValueError("artifact has trailing bytes")
    return ArtifactIdentity(
        path=str(resolved),
        byte_length=observed.st_size,
        sha256=digest.hexdigest(),
        header=header,
        core_offset=core_offset,
        core_byte_length=core_length,
        trailer_offset=trailer_offset,
        trailer_byte_length=trailer_length,
    )


def _read_artifact_part(
    identity: ArtifactIdentity,
    *,
    offset: int,
    length: int,
) -> bytes:
    path = Path(identity.path)
    observed = _read_artifact_identity(path)
    if (
        observed.sha256 != identity.sha256
        or observed.byte_length != identity.byte_length
    ):
        raise ValueError("development artifact identity drifted")
    with path.open("rb") as source:
        source.seek(offset)
        return _read_exact(source, length)


def _read_artifact_core(identity: ArtifactIdentity) -> tuple[bytes, dict[str, Any]]:
    raw = _read_artifact_part(
        identity,
        offset=identity.core_offset,
        length=identity.core_byte_length,
    )
    value = _parse_canonical(raw, name="source worker core")
    if value.get("schema") != identity.header["source_core_schema"]:
        raise ValueError("source worker core schema drifted")
    return raw, value


def _read_artifact_trailer(identity: ArtifactIdentity) -> dict[str, Any]:
    raw = _read_artifact_part(
        identity,
        offset=identity.trailer_offset,
        length=identity.trailer_byte_length,
    )
    if not raw:
        raise ValueError("worker artifact has no timing trailer")
    return _parse_canonical(raw, name="source worker trailer")


def _transport_manifest(
    *,
    role: str,
    case_id: str | None,
    role_parameters: Mapping[str, Any],
    entries: Mapping[str, ArtifactIdentity],
) -> dict[str, Any]:
    expected_names = ROLE_DEPENDENCIES[role]
    if tuple(entries) != expected_names:
        raise ValueError("development dependency order drifted")
    return {
        "schema": INPUT_SCHEMA,
        "run_partition": DEVELOPMENT_SWEEP,
        "formal_claim_eligible": False,
        "is_heldout_evidence": False,
        "execution_class": "claim_ineligible_development_diagnostic",
        "heldout_shaped_fixture_reuse_only": True,
        "transport_equivalent_to_B_CAL_or_B_HELD": False,
        "role": role,
        "case_id": case_id,
        "role_parameters": dict(role_parameters),
        "entries": [
            {
                "name": name,
                "source_core_schema": identity.header["source_core_schema"],
                "byte_length": identity.core_byte_length,
                "sha256": identity.header["source_core_sha256"],
            }
            for name, identity in entries.items()
        ],
    }


def _write_transport(
    path: Path,
    *,
    role: str,
    case_id: str | None,
    role_parameters: Mapping[str, Any],
    entries: Mapping[str, ArtifactIdentity],
) -> None:
    manifest = _transport_manifest(
        role=role,
        case_id=case_id,
        role_parameters=role_parameters,
        entries=entries,
    )
    manifest_bytes = _canonical(manifest)
    if len(manifest_bytes) > MANIFEST_CAP:
        raise ValueError("development transport manifest exceeds cap")
    with path.open("xb") as destination:
        destination.write(struct.pack(">Q", len(manifest_bytes)))
        destination.write(manifest_bytes)
        for name, identity in entries.items():
            destination.write(struct.pack(">Q", identity.core_byte_length))
            with Path(identity.path).open("rb") as source:
                source.seek(identity.core_offset)
                digest = hashlib.sha256()
                _copy_exact(
                    source,
                    destination,
                    identity.core_byte_length,
                    digest=digest,
                )
            if digest.hexdigest() != identity.header["source_core_sha256"]:
                raise ValueError(f"dependency {name} drifted while copied")
        destination.flush()
        os.fsync(destination.fileno())


def _read_transport(
    stream: BinaryIO,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest_size = struct.unpack(">Q", _read_exact(stream, 8))[0]
    if manifest_size > MANIFEST_CAP:
        raise ValueError("development input manifest exceeds cap")
    manifest = _parse_canonical(
        _read_exact(stream, manifest_size),
        name="development input manifest",
    )
    if set(manifest) != {
        "schema",
        "run_partition",
        "formal_claim_eligible",
        "is_heldout_evidence",
        "execution_class",
        "heldout_shaped_fixture_reuse_only",
        "transport_equivalent_to_B_CAL_or_B_HELD",
        "role",
        "case_id",
        "role_parameters",
        "entries",
    }:
        raise ValueError("development input manifest has wrong keys")
    if (
        manifest.get("schema") != INPUT_SCHEMA
        or manifest.get("run_partition") != DEVELOPMENT_SWEEP
        or manifest.get("formal_claim_eligible") is not False
        or manifest.get("is_heldout_evidence") is not False
        or manifest.get("execution_class")
        != "claim_ineligible_development_diagnostic"
        or manifest.get("heldout_shaped_fixture_reuse_only") is not True
        or manifest.get("transport_equivalent_to_B_CAL_or_B_HELD") is not False
    ):
        raise ValueError("development input claim boundary drifted")
    role = manifest.get("role")
    if role not in ROLE_DEPENDENCIES:
        raise ValueError("development input role is unknown")
    case_id = manifest.get("case_id")
    if role == SDIM_INVENTORY:
        if case_id is not None:
            raise ValueError("inventory development case id must be null")
    elif not isinstance(case_id, str) or not case_id.startswith(
        "development-sweep-c"
    ):
        raise ValueError("development case id is invalid")
    parameters = manifest.get("role_parameters")
    if (
        not isinstance(parameters, Mapping)
        or set(parameters) != ROLE_PARAMETER_KEYS[role]
    ):
        raise ValueError("development role parameters have wrong keys")
    if "input_id" in parameters:
        _plain_int(
            parameters["input_id"],
            name="input_id",
            minimum=1,
            maximum=2,
        )
    if role in {PLAIN_PERFORMANCE, GCAPEPS_PERFORMANCE}:
        if parameters["input_id"] != 1:
            raise ValueError("development performance input must be one")
        sample_kind = parameters["sample_kind"]
        sample_index = parameters["sample_index"]
        if sample_kind == "warmup":
            if sample_index is not None:
                raise ValueError("development warmup sample index must be null")
        elif sample_kind == "measured":
            _plain_int(
                sample_index,
                name="sample_index",
                minimum=0,
                maximum=2,
            )
        else:
            raise ValueError("development performance sample kind is invalid")
    rows = manifest.get("entries")
    if not isinstance(rows, list):
        raise ValueError("development input entries must be a list")
    if tuple(row.get("name") for row in rows) != ROLE_DEPENDENCIES[role]:
        raise ValueError("development input dependency order drifted")
    cores: dict[str, dict[str, Any]] = {}
    for row in rows:
        if set(row) != {
            "name",
            "source_core_schema",
            "byte_length",
            "sha256",
        }:
            raise ValueError("development input entry has wrong keys")
        length = _plain_int(
            row["byte_length"],
            name="entry.byte_length",
            minimum=0,
            maximum=1_073_741_824,
        )
        observed = struct.unpack(">Q", _read_exact(stream, 8))[0]
        if observed != length:
            raise ValueError("development input entry prefix drifted")
        raw = _read_exact(stream, length)
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("development input entry hash drifted")
        core = _parse_canonical(raw, name=f"entry {row['name']}")
        if (
            row["source_core_schema"] != ENTRY_CORE_SCHEMA[row["name"]]
            or core.get("schema") != row["source_core_schema"]
        ):
            raise ValueError("development input entry schema drifted")
        cores[row["name"]] = core
    if stream.read(1):
        raise ValueError("development input has trailing bytes")
    return manifest, cores


def _execute_child(role: str) -> int:
    if role not in ROLE_OWNER:
        raise ValueError("unknown development child role")
    file_limit = CORE_CAP[role] + TRAILER_CAP + 16
    resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))
    manifest, cores = _read_transport(sys.stdin.buffer)
    if manifest["role"] != role:
        raise ValueError("child argv/manifest role mismatch")
    parameters = manifest["role_parameters"]
    owner = _load_path(
        _SCRIPT_DIR / ROLE_OWNER[role],
        f"_gcapeps_fm_dev_{role}_{os.getpid()}",
    )
    if role == SDIM_INVENTORY:
        result = owner.run_inventory_worker()
        framed = result["framed_bytes"]
    elif role == DENSE_REFERENCE:
        framed = owner.build_framed_worker_output(cores["fixture"])
    elif role in {PLAIN_EVIDENCE, GCAPEPS_EVIDENCE}:
        result = owner.run_evidence(
            cores["fixture"],
            input_id=parameters["input_id"],
        )
        framed = result["framed_bytes"]
    elif role in {PLAIN_PERFORMANCE, GCAPEPS_PERFORMANCE}:
        result = owner.run_performance(
            cores["fixture"],
            input_id=parameters["input_id"],
        )
        framed = result["framed_bytes"]
    elif role == SDIM_COMPUTATION:
        result = owner.run_frame_control_worker(
            cores["fixture"],
            inventory_core=cores["inventory"],
        )
        framed = result["framed_bytes"]
    elif role == TERMINAL_COMPARATOR:
        timing = _load_path(
            _TIMING_PATH,
            f"_gcapeps_fm_dev_timing_{os.getpid()}",
        )
        result = owner.run_comparator_worker(
            fixture=cores["fixture"],
            dense_core=cores["dense"],
            plain_input1_core=cores["plain_input1"],
            plain_input2_core=cores["plain_input2"],
            gcapeps_input1_core=cores["gcapeps_input1"],
            gcapeps_input2_core=cores["gcapeps_input2"],
            sdim_core=cores["sdim"],
            timing_module=timing,
        )
        framed = result["framed_bytes"]
    else:
        raise AssertionError("unreachable development role")
    cursor = 0
    while cursor < len(framed):
        written = os.write(1, framed[cursor:])
        if written <= 0:
            raise RuntimeError("development child stdout write failed")
        cursor += written
    return 0


def _child_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in (
        "PYTHONPATH",
        "PYTHONHOME",
        "VIRTUAL_ENV",
        "CONDA_PREFIX",
        "CONDA_DEFAULT_ENV",
        "LD_PRELOAD",
    ):
        environment.pop(name, None)
    environment.update(
        {
            "CUDA_VISIBLE_DEVICES": "",
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "BLIS_NUM_THREADS": "1",
        }
    )
    return environment


def _process_group_exists(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError as exc:
        raise RuntimeError(
            "cannot verify development process group"
        ) from exc
    return True


def _wait_process_group_gone(
    process_group_id: int,
    *,
    timeout_seconds: float,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while _process_group_exists(process_group_id):
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.01)
    return True


def _signal_process_group(process_group_id: int, signal_number: int) -> bool:
    try:
        os.killpg(process_group_id, signal_number)
    except ProcessLookupError:
        return False
    except PermissionError as exc:
        raise RuntimeError(
            "cannot signal development process group"
        ) from exc
    return True


def _cleanup_process_group(process: subprocess.Popen[bytes]) -> None:
    """Terminate every descendant in the child's dedicated process group."""

    process_group_id = process.pid
    _signal_process_group(process_group_id, signal.SIGTERM)
    if process.poll() is None:
        try:
            process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            pass
    if _wait_process_group_gone(process_group_id, timeout_seconds=1.0):
        return
    _signal_process_group(process_group_id, signal.SIGKILL)
    if process.poll() is None:
        try:
            process.wait(timeout=5.0)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                "development child leader survived SIGKILL"
            ) from exc
    if not _wait_process_group_gone(process_group_id, timeout_seconds=5.0):
        raise RuntimeError(
            "development process group survived SIGKILL cleanup"
        )


@dataclass(frozen=True)
class ChildResult:
    artifact: ArtifactIdentity
    process_wall_ns: int


def _scientific_child_command(
    interpreter: Path,
    role: str,
) -> tuple[str, ...]:
    if role not in ROLE_OWNER:
        raise ValueError("unknown development child role")
    return (str(interpreter), "-I", str(_SCRIPT_PATH), "--child", role)


def _run_child(
    *,
    interpreter: Path,
    interpreter_identity: Mapping[str, Any],
    role: str,
    launch_id: str,
    case_id: str | None,
    role_parameters: Mapping[str, Any],
    entries: Mapping[str, ArtifactIdentity],
    artifact_path: Path,
    scratch: Path,
    timeout_seconds: float,
    parent_source_projection_sha256: str,
) -> ChildResult:
    transport = scratch / f"{launch_id}.stdin"
    stdout_path = scratch / f"{launch_id}.stdout"
    stderr_path = scratch / f"{launch_id}.stderr"
    _write_transport(
        transport,
        role=role,
        case_id=case_id,
        role_parameters=role_parameters,
        entries=entries,
    )
    started = time.perf_counter_ns()
    with (
        transport.open("rb") as stdin,
        stdout_path.open("xb") as stdout,
        stderr_path.open("xb") as stderr,
    ):
        process = subprocess.Popen(
            _scientific_child_command(interpreter, role),
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            cwd=_REPOSITORY,
            env=_child_environment(),
            start_new_session=True,
            close_fds=True,
        )
        timed_out = False
        try:
            return_code = process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            return_code = None
        finally:
            _cleanup_process_group(process)
        if timed_out:
            raise TimeoutError(f"development child {launch_id} timed out")
    if return_code is None:
        raise AssertionError("development child return code is unavailable")
    process_wall = time.perf_counter_ns() - started
    stderr_size = stderr_path.stat().st_size
    if stderr_size > STDERR_CAP:
        raise RuntimeError(f"development child {launch_id} stderr exceeded cap")
    stderr_raw = stderr_path.read_bytes()
    stdout_size = stdout_path.stat().st_size
    if stdout_size > CORE_CAP[role] + TRAILER_CAP + 16:
        raise RuntimeError(f"development child {launch_id} stdout exceeded cap")
    if return_code != 0 or stderr_raw:
        raise RuntimeError(
            f"development child {launch_id} failed: "
            f"returncode={return_code}, stderr_sha256="
            f"{hashlib.sha256(stderr_raw).hexdigest()}"
        )
    raw = stdout_path.read_bytes()
    timing = _load_path(
        _TIMING_PATH,
        f"_gcapeps_fm_dev_parent_timing_{launch_id.replace('-', '_')}",
    )
    core_bytes, trailer_bytes = timing.decode_two_frames(
        raw,
        core_max=CORE_CAP[role],
        trailer_max=TRAILER_CAP,
    )
    core = _parse_canonical(core_bytes, name=f"{launch_id} core")
    trailer = _parse_canonical(trailer_bytes, name=f"{launch_id} trailer")
    if core.get("schema") != ROLE_CORE_SCHEMA[role]:
        raise ValueError(f"{launch_id} core schema drifted")
    if core.get("result_projection_sha256") != _projection(core):
        raise ValueError(f"{launch_id} core projection identity drifted")
    plan = _load_path(
        _PLAN_PATH,
        f"_gcapeps_fm_dev_parent_plan_{launch_id.replace('-', '_')}",
    )
    plan.validate_worker_trailer(trailer, core_bytes=core_bytes)
    timing.validate_layered_timing(trailer["timing"])
    receipt = {
        "formal_claim_eligible": False,
        "process_kind": "fresh_ordinary_subprocess_without_systemd",
        "launch_id": launch_id,
        "role": role,
        "development_process_wall_ns": process_wall,
        "return_code": return_code,
        "stderr_byte_length": len(stderr_raw),
        "stderr_sha256": hashlib.sha256(stderr_raw).hexdigest(),
        "stdout_byte_length": len(raw),
        "stdout_sha256": hashlib.sha256(raw).hexdigest(),
        "interpreter": dict(interpreter_identity),
        "parent_source_projection_sha256": _require_sha256(
            parent_source_projection_sha256,
            name="parent_source_projection_sha256",
        ),
    }
    header = _artifact_header(
        schema=CHILD_SCHEMA,
        role=role,
        case_id=case_id,
        role_parameters=role_parameters,
        source_core_schema=core["schema"],
        source_core_projection_sha256=core[
            "result_projection_sha256"
        ],
        core_bytes=core_bytes,
        trailer_bytes=trailer_bytes,
        process_receipt=receipt,
    )
    artifact = _publish_binary_artifact(
        artifact_path,
        header=header,
        core_bytes=core_bytes,
        trailer_bytes=trailer_bytes,
    )
    for path in (transport, stdout_path, stderr_path):
        path.unlink(missing_ok=False)
    del raw, core_bytes, trailer_bytes, core, trailer
    return ChildResult(artifact=artifact, process_wall_ns=process_wall)


def _publish_fixture(
    *,
    path: Path,
    fixture: Mapping[str, Any],
    development_case_id: str,
    parent_source_projection_sha256: str,
) -> ArtifactIdentity:
    if fixture.get("result_projection_sha256") != _projection(fixture):
        raise ValueError("development fixture projection identity drifted")
    core_bytes = _canonical(fixture)
    receipt = {
        "formal_claim_eligible": False,
        "process_kind": "parent_deterministic_fixture_materialization",
        "development_process_wall_ns": None,
        "source_fixture_run_partition": "HELDOUT",
        "heldout_shaped_fixture_reuse_only": True,
        "parent_source_projection_sha256": _require_sha256(
            parent_source_projection_sha256,
            name="parent_source_projection_sha256",
        ),
    }
    header = _artifact_header(
        schema=FIXTURE_ARTIFACT_SCHEMA,
        role="neutral_fixture",
        case_id=development_case_id,
        role_parameters={
            "source_fixture_case_id": fixture["case_id"],
            "source_fixture_run_partition": fixture["run_partition"],
        },
        source_core_schema=fixture["schema"],
        source_core_projection_sha256=fixture[
            "result_projection_sha256"
        ],
        core_bytes=core_bytes,
        trailer_bytes=b"",
        process_receipt=receipt,
    )
    return _publish_binary_artifact(
        path,
        header=header,
        core_bytes=core_bytes,
        trailer_bytes=b"",
    )


def _build_single_development_fixture(
    *,
    fixture_owner: Any,
    fixture_cell: Mapping[str, Any],
    development_cell: Mapping[str, Any],
    gamma_index: int,
) -> dict[str, Any]:
    if (
        fixture_cell.get("cell") != development_cell.get("cell")
        or fixture_cell.get("slice_membership")
        != development_cell.get("slice_membership")
        or fixture_cell.get("run_blpensemble")
        is not development_cell.get("run_blpensemble")
    ):
        raise ValueError("development cell/fixture metadata drifted")
    width, rounds, axis_family, numerator, denominator = fixture_cell["cell"]
    if denominator != 4:
        raise ValueError("development fixture probability denominator drifted")
    fixture = fixture_owner.build_fixture(
        run_partition="HELDOUT",
        width=width,
        rounds=rounds,
        axis_family=axis_family,
        p_event_numerator=numerator,
        seed=fixture_owner.HELDOUT_SEED,
        gamma_index=gamma_index,
        run_blpensemble=fixture_cell["run_blpensemble"],
    )
    observed = fixture_owner.validate_fixture(fixture)
    if (
        observed != fixture.get("result_projection_sha256")
        or fixture.get("case_id") != fixture_cell.get("case_id")
    ):
        raise ValueError("development fixture identity drifted")
    return fixture


def _artifact_bindings(
    rows: Mapping[str, ArtifactIdentity],
) -> dict[str, dict[str, Any]]:
    return {name: identity.binding() for name, identity in rows.items()}


def _component_timings(
    artifacts: Mapping[str, ArtifactIdentity],
) -> list[dict[str, Any]]:
    rows = []
    for artifact_key, identity in artifacts.items():
        if artifact_key == "fixture":
            continue
        trailer = _read_artifact_trailer(identity)
        roots = [
            row
            for row in trailer["timing"]["spans"]
            if row["parent_span_id"] is None
        ]
        if len(roots) != 1:
            raise ValueError("development component timing lacks one root")
        root = roots[0]
        receipt = identity.header["development_process_receipt"]
        rows.append(
            {
                "artifact_key": artifact_key,
                "role": identity.header["role"],
                "role_parameters": identity.header["role_parameters"],
                "launch_id": receipt["launch_id"],
                "development_process_wall_ns": _plain_int(
                    receipt["development_process_wall_ns"],
                    name="development_process_wall_ns",
                    minimum=0,
                ),
                "worker_root_scope": root["scope"],
                "worker_root_wall_ns": _plain_int(
                    root["wall_duration_ns"],
                    name="worker_root_wall_ns",
                    minimum=0,
                ),
                "worker_root_cpu_ns": _plain_int(
                    root["cpu_duration_ns"],
                    name="worker_root_cpu_ns",
                    minimum=0,
                ),
                "timing_artifact": identity.binding(),
            }
        )
        del trailer
    return rows


def _case_timing_scopes(
    *,
    workflow_wall_ns: int,
    with_fixture_wall_ns: int,
) -> dict[str, Any]:
    workflow = _plain_int(
        workflow_wall_ns,
        name="development_case_workflow_wall_ns",
        minimum=0,
    )
    with_fixture = _plain_int(
        with_fixture_wall_ns,
        name="development_case_with_fixture_wall_ns",
        minimum=workflow,
    )
    return {
        "development_case_workflow_wall_ns": workflow,
        "development_case_with_fixture_wall_ns": with_fixture,
        "development_case_timing_scope": {
            "workflow_includes": ["all_15_child_launches"],
            "with_fixture_includes": [
                "lazy_fixture_construction",
                "case_directory_creation",
                "fixture_artifact_publication",
                "all_15_child_launches",
            ],
            "both_exclude": [
                "global_parent_and_interpreter_preflight",
                "global_sdim_inventory",
                "case_summary_encoding",
                "top_level_report_encoding_and_publication",
            ],
        },
    }


def _case_summary(
    *,
    orchestration_module: Any,
    cell: Mapping[str, Any],
    fixture: Mapping[str, Any],
    artifacts: Mapping[str, ArtifactIdentity],
    measured: Sequence[tuple[str, int, ArtifactIdentity, int]],
    case_wall_ns: int,
    case_with_fixture_wall_ns: int,
) -> dict[str, Any]:
    strict_samples = []
    raw_samples = []
    for lane, sample_index, identity, process_wall in measured:
        core_bytes, core = _read_artifact_core(identity)
        trailer_bytes = _read_artifact_part(
            identity,
            offset=identity.trailer_offset,
            length=identity.trailer_byte_length,
        )
        final_hash = core.get("final_carrier_hash", {}).get("sha256")
        strict_lane = "plain" if lane == "plain" else "gc"
        sample = orchestration_module.measured_timing_sample_from_trailer(
            core_bytes=core_bytes,
            trailer_bytes=trailer_bytes,
            lane=strict_lane,
            case_id=fixture["case_id"],
            sample_index=sample_index,
            supervisor_launch_wall_ns=process_wall,
            final_carrier_hash=final_hash,
        )
        strict_samples.append(sample)
        raw_samples.append(
            {
                "lane": lane,
                "sample_index": sample.sample_index,
                "development_process_wall_ns": sample.supervisor_launch_wall_ns,
                "candidate_algorithm_case_e2e_wall_ns": sample.algorithm_wall_ns,
                "candidate_algorithm_case_e2e_cpu_ns": sample.algorithm_cpu_ns,
                "state_update_only_wall_ns": sample.state_update_wall_ns,
                "state_update_only_cpu_ns": sample.state_update_cpu_ns,
                "final_carrier_hash": sample.final_carrier_hash,
                "nested_spans": [
                    {
                        "scope": row[0],
                        "round_index": row[1],
                        "operation_index": row[2],
                        "step_index": row[3],
                        "kind": row[4],
                        "wall_ns": row[5],
                        "cpu_ns": row[6],
                    }
                    for row in sample.population_rows
                ],
            }
        )
        del core_bytes, core, trailer_bytes

    def evidence_identity(key: str) -> tuple[int, str]:
        core_bytes, core = _read_artifact_core(artifacts[key])
        trailer = _read_artifact_trailer(artifacts[key])
        roots = [
            row
            for row in trailer["timing"]["spans"]
            if row["scope"] == "evidence_worker_total"
        ]
        if len(roots) != 1:
            raise ValueError("evidence timing lacks a unique worker root")
        final_hash = core.get("no_shadow", {}).get(
            "final_carrier_hash", {}
        ).get("sha256")
        if not isinstance(final_hash, str) or len(final_hash) != 64:
            raise ValueError("evidence final-carrier hash is invalid")
        wall = _plain_int(
            roots[0]["wall_duration_ns"],
            name="evidence_worker_total.wall_duration_ns",
            minimum=0,
        )
        del core_bytes, core, trailer
        return wall, final_hash

    plain_evidence_wall, plain_evidence_hash = evidence_identity(
        "plain_input1"
    )
    gc_evidence_wall, gc_evidence_hash = evidence_identity(
        "gcapeps_input1"
    )
    strict = orchestration_module.aggregate_primary_timing(
        strict_samples,
        plain_evidence_worker_wall_ns=plain_evidence_wall,
        gc_evidence_worker_wall_ns=gc_evidence_wall,
        plain_evidence_final_carrier_hash=plain_evidence_hash,
        gc_evidence_final_carrier_hash=gc_evidence_hash,
    )
    lanes = {}
    for source_lane, report_lane in (("plain", "plain"), ("gc", "gcapeps")):
        lane_row = dict(strict["lanes"][source_lane])
        lane_row["development_process_wall_ns"] = lane_row.pop(
            "supervisor_launch_wall_ns"
        )
        lanes[report_lane] = lane_row
    ratios = dict(strict["ratios"])
    ratios["development_process_wall_gcapeps_over_plain"] = ratios.pop(
        "supervisor_launch_wall_gc_over_plain"
    )
    ratio_dispositions = dict(strict["ratio_dispositions"])
    ratio_dispositions[
        "development_process_wall_gcapeps_over_plain"
    ] = ratio_dispositions.pop("supervisor_launch_wall_gc_over_plain")
    aggregate = {
        "formal_claim_eligible": False,
        "strict_frozen_timing_parser_reused": True,
        "population_complete_3x3": True,
        "warmups_excluded": True,
        "ratio_direction": "gcapeps_over_plain",
        "development_process_wall_was_parser_launch_slot_only": True,
        "raw_samples": raw_samples,
        "lanes": lanes,
        "nested_per_step_aggregates": {
            "plain": strict["registered_population_aggregates"]["plain"],
            "gcapeps": strict["registered_population_aggregates"]["gc"],
        },
        "singleton_evidence_worker_wall_ns": {
            "plain": strict["singleton_evidence_worker_wall_ns"]["plain"],
            "gcapeps": strict["singleton_evidence_worker_wall_ns"]["gc"],
        },
        "ratios": ratios,
        "ratio_dispositions": ratio_dispositions,
        "state_update_only_is_report_only_no_registered_ratio": strict[
            "state_update_only_is_report_only_no_registered_ratio"
        ],
        "candidate_algorithm_wall_band": strict["primary_wall_band"],
    }
    comparator_raw, comparator = _read_artifact_core(artifacts["comparator"])
    del comparator_raw
    expected_comparator_bindings = {
        key: artifacts[key].header["source_core_projection_sha256"]
        for key in (
            "fixture",
            "dense",
            "plain_input1",
            "plain_input2",
            "gcapeps_input1",
            "gcapeps_input2",
            "sdim",
        )
    }
    if comparator["artifact_bindings"] != expected_comparator_bindings:
        raise ValueError("comparator/development artifact binding drifted")
    summary = {
        "run_partition": DEVELOPMENT_SWEEP,
        "formal_claim_eligible": False,
        "is_heldout_evidence": False,
        "development_case_id": cell["development_case_id"],
        "source_fixture_case_id": fixture["case_id"],
        "source_fixture_run_partition": fixture["run_partition"],
        "heldout_shaped_fixture_reuse_only": True,
        "cell": list(cell["cell"]),
        "slice_membership": list(cell["slice_membership"]),
        "run_blpensemble": cell["run_blpensemble"],
        "status": "COMPLETED_DEVELOPMENT_DIAGNOSTIC",
        **_case_timing_scopes(
            workflow_wall_ns=case_wall_ns,
            with_fixture_wall_ns=case_with_fixture_wall_ns,
        ),
        "artifact_bindings": _artifact_bindings(artifacts),
        "component_timings": _component_timings(artifacts),
        "timing": aggregate,
        "diagnostic_comparator_summary": {
            "positive_bond32_gate": comparator["positive_bond32_gate"],
            "exact_dense_memory_witnesses": comparator[
                "exact_dense_memory_witnesses"
            ],
            "checkpoint_metrics": comparator["checkpoint_metrics"],
            "final_bond32_faithfulness": comparator[
                "final_bond32_faithfulness"
            ],
            "claim_boundary": comparator["claim_boundary"],
            "source_comparator_projection_sha256": comparator[
                "result_projection_sha256"
            ],
            "comparator_input_projection_bindings": comparator[
                "artifact_bindings"
            ],
            "bindings_rechecked_against_development_artifacts": True,
        },
    }
    return summary


def execute_cells_serially(
    cells: Sequence[Mapping[str, Any]],
    execute_one: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Execute cells one-at-a-time and retain JSON summaries, never raw bytes."""

    summaries: list[dict[str, Any]] = []
    for expected_index, cell in enumerate(cells):
        if cell.get("cell_index") != expected_index:
            raise ValueError("development cell order drifted")
        summary = execute_one(cell)
        if not isinstance(summary, Mapping):
            raise TypeError("development case callback returned non-mapping")
        retains_raw = any(
            isinstance(value, (bytes, bytearray, memoryview))
            for value in _walk(summary)
        )
        if retains_raw:
            raise ValueError("development case summary retained raw payload bytes")
        encoded = _canonical(summary)
        if len(encoded) > 67_108_864:
            raise ValueError("development case summary exceeds bounded size")
        summaries.append(dict(summary))
        del summary, encoded
    return summaries


def _walk(value: Any):
    yield value
    if isinstance(value, Mapping):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk(child)


def _publish_report(path: Path, report: Mapping[str, Any]) -> dict[str, Any]:
    raw = _canonical(report)
    temporary = path.with_name(f".{path.name}.tmp-{secrets.token_hex(12)}")
    with temporary.open("xb") as target:
        os.chmod(temporary, 0o644)
        target.write(raw)
        target.flush()
        os.fsync(target.fileno())
    try:
        os.link(temporary, path, follow_symlinks=False)
    finally:
        temporary.unlink(missing_ok=True)
    parent_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)
    observed = path.read_bytes()
    if observed != raw:
        raise RuntimeError("development report reread mismatch")
    return {
        "path": str(path),
        "byte_length": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _require_identity_unchanged(
    initial: Mapping[str, Any],
    observed: Mapping[str, Any],
    *,
    name: str,
) -> None:
    if _canonical(initial) != _canonical(observed):
        raise RuntimeError(f"{name} changed during development sweep")


def _recheck_execution_identities(
    *,
    parent_source_identity: Mapping[str, Any],
    fork_identity: Mapping[str, Any],
    sdim_identity: Mapping[str, Any],
    fork_python: Path,
    sdim_python: Path,
) -> None:
    _require_identity_unchanged(
        parent_source_identity,
        _authenticate_parent_repository(),
        name="parent source identity",
    )
    _require_identity_unchanged(
        fork_identity,
        _authenticate_interpreter(fork_python, kind="fork"),
        name="fork interpreter identity",
    )
    _require_identity_unchanged(
        sdim_identity,
        _authenticate_interpreter(sdim_python, kind="sdim"),
        name="SDIM interpreter identity",
    )


def run_sweep(
    *,
    output_root: Path,
    gamma_index: int,
    rounds_star: int,
    fork_python: Path,
    sdim_python: Path,
    timeout_seconds: float,
    cell_limit: int | None,
) -> dict[str, Any]:
    parent_source_identity = _authenticate_parent_repository()
    parent_source_projection = parent_source_identity[
        "result_projection_sha256"
    ]
    plan_module = _load_path(_PLAN_PATH, "_gcapeps_fm_dev_plan")
    orchestration_module = _load_path(
        _ORCHESTRATION_PATH, "_gcapeps_fm_dev_orchestration"
    )
    fixture_owner = _load_path(_FIXTURE_PATH, "_gcapeps_fm_dev_fixture")
    plan = plan_module.build_development_plan(
        gamma_index=gamma_index,
        rounds_star=rounds_star,
    )
    fixture_cells = fixture_owner.build_heldout_cells(rounds_star)
    if plan["fixture_seed"] != fixture_owner.HELDOUT_SEED:
        raise RuntimeError("development plan/fixture seed drifted")
    if [row["cell"] for row in plan["cells"]] != [
        row["cell"] for row in fixture_cells
    ]:
        raise RuntimeError("development plan/fixture cell union drifted")
    fork_identity = _authenticate_interpreter(fork_python, kind="fork")
    sdim_identity = _authenticate_interpreter(sdim_python, kind="sdim")
    parent_source_recheck = _authenticate_parent_repository()
    _require_identity_unchanged(
        parent_source_identity,
        parent_source_recheck,
        name="parent source identity during preflight",
    )
    output_root = _resolve_development_output_root(
        output_root,
        repository=_REPOSITORY,
    )
    if output_root.exists():
        raise FileExistsError("development output root must be fresh")
    output_root.mkdir(mode=0o700, parents=True)
    scratch = output_root / ".ephemeral"
    scratch.mkdir(mode=0o700)
    inventory_result = _run_child(
        interpreter=sdim_python.resolve(strict=True),
        interpreter_identity=sdim_identity,
        role=SDIM_INVENTORY,
        launch_id="dev-inventory",
        case_id=None,
        role_parameters={},
        entries={},
        artifact_path=output_root / "development-inventory.devbin",
        scratch=scratch,
        timeout_seconds=timeout_seconds,
        parent_source_projection_sha256=parent_source_projection,
    )
    inventory = inventory_result.artifact
    cells = plan["cells"]
    if cell_limit is not None:
        cell_limit = _plain_int(
            cell_limit,
            name="cell_limit",
            minimum=1,
            maximum=len(cells),
        )
        cells = cells[:cell_limit]

    def execute_one(cell: Mapping[str, Any]) -> Mapping[str, Any]:
        index = cell["cell_index"]
        case_with_fixture_started = time.perf_counter_ns()
        fixture = _build_single_development_fixture(
            fixture_owner=fixture_owner,
            fixture_cell=fixture_cells[index],
            development_cell=cell,
            gamma_index=gamma_index,
        )
        case_dir = output_root / f"development-c{index:02d}"
        case_dir.mkdir(mode=0o700)
        fixture_artifact = _publish_fixture(
            path=case_dir / "fixture.devbin",
            fixture=fixture,
            development_case_id=cell["development_case_id"],
            parent_source_projection_sha256=parent_source_projection,
        )
        artifacts: dict[str, ArtifactIdentity] = {
            "fixture": fixture_artifact,
        }
        measured: list[tuple[str, int, ArtifactIdentity, int]] = []
        case_started = time.perf_counter_ns()
        for launch in cell["launches"]:
            role = launch["role"]
            if role == DENSE_REFERENCE:
                entries = {"fixture": fixture_artifact}
                artifact_key = "dense"
            elif role == PLAIN_EVIDENCE:
                entries = {"fixture": fixture_artifact}
                artifact_key = f"plain_input{launch['input_id']}"
            elif role == GCAPEPS_EVIDENCE:
                entries = {"fixture": fixture_artifact}
                artifact_key = f"gcapeps_input{launch['input_id']}"
            elif role in {PLAIN_PERFORMANCE, GCAPEPS_PERFORMANCE}:
                entries = {"fixture": fixture_artifact}
                lane = "plain" if role == PLAIN_PERFORMANCE else "gcapeps"
                sample = launch["sample_index"]
                artifact_key = (
                    f"{lane}_warmup"
                    if launch["sample_kind"] == "warmup"
                    else f"{lane}_measured_{sample}"
                )
            elif role == SDIM_COMPUTATION:
                entries = {
                    "fixture": fixture_artifact,
                    "inventory": inventory,
                }
                artifact_key = "sdim"
            elif role == TERMINAL_COMPARATOR:
                entries = {
                    "fixture": fixture_artifact,
                    "dense": artifacts["dense"],
                    "plain_input1": artifacts["plain_input1"],
                    "plain_input2": artifacts["plain_input2"],
                    "gcapeps_input1": artifacts["gcapeps_input1"],
                    "gcapeps_input2": artifacts["gcapeps_input2"],
                    "sdim": artifacts["sdim"],
                }
                artifact_key = "comparator"
            else:
                raise ValueError("development launch role drifted")
            interpreter = (
                sdim_python.resolve(strict=True)
                if role == SDIM_COMPUTATION
                else fork_python.resolve(strict=True)
            )
            interpreter_row = (
                sdim_identity if role == SDIM_COMPUTATION else fork_identity
            )
            role_parameters = {
                key: launch[key]
                for key in ROLE_PARAMETER_KEYS[role]
            }
            result = _run_child(
                interpreter=interpreter,
                interpreter_identity=interpreter_row,
                role=role,
                launch_id=launch["launch_id"],
                case_id=cell["development_case_id"],
                role_parameters=role_parameters,
                entries=entries,
                artifact_path=case_dir / f"{launch['launch_id']}.devbin",
                scratch=scratch,
                timeout_seconds=timeout_seconds,
                parent_source_projection_sha256=parent_source_projection,
            )
            artifacts[artifact_key] = result.artifact
            if (
                role in {PLAIN_PERFORMANCE, GCAPEPS_PERFORMANCE}
                and launch["sample_kind"] == "measured"
            ):
                lane = "plain" if role == PLAIN_PERFORMANCE else "gcapeps"
                measured.append(
                    (
                        lane,
                        launch["sample_index"],
                        result.artifact,
                        result.process_wall_ns,
                    )
                )
        case_wall = time.perf_counter_ns() - case_started
        case_with_fixture_wall = (
            time.perf_counter_ns() - case_with_fixture_started
        )
        if len(measured) != 6:
            raise AssertionError("development measured timing population drifted")
        summary = _case_summary(
            orchestration_module=orchestration_module,
            cell=cell,
            fixture=fixture,
            artifacts=artifacts,
            measured=measured,
            case_wall_ns=case_wall,
            case_with_fixture_wall_ns=case_with_fixture_wall,
        )
        del fixture, artifacts, measured
        return summary

    case_summaries = execute_cells_serially(cells, execute_one)
    if any(scratch.iterdir()):
        raise RuntimeError("development ephemeral directory is not empty")
    scratch.rmdir()
    _recheck_execution_identities(
        parent_source_identity=parent_source_identity,
        fork_identity=fork_identity,
        sdim_identity=sdim_identity,
        fork_python=fork_python,
        sdim_python=sdim_python,
    )
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "run_partition": DEVELOPMENT_SWEEP,
        "formal_claim_eligible": False,
        "is_heldout_evidence": False,
        "execution_class": "claim_ineligible_development_diagnostic",
        "heldout_shaped_fixture_reuse_only": True,
        "heldout_shaped_fixture_explanation": (
            "Workers consumed HELDOUT-shaped neutral fixtures solely to reuse "
            "the preregistered width/round/axis/probability semantics."
        ),
        "transport_equivalent_to_B_CAL_or_B_HELD": False,
        **_development_report_provenance(parent_source_identity),
        "claim_boundary": (
            "Fresh ordinary subprocess development diagnostic only; not "
            "system-manager isolated, not amendment-bound, not held-out "
            "evidence, and not a generic PEPS or QEC Record result."
        ),
        "plan": plan,
        "executed_cell_count": len(case_summaries),
        "complete_frozen_cell_count": len(plan["cells"]),
        "full_plan_executed": len(case_summaries) == len(plan["cells"]),
        "interpreter_identities": {
            "fork": fork_identity,
            "sdim": sdim_identity,
        },
        "inventory_artifact": inventory.binding(),
        "inventory_component_timing": _component_timings(
            {"inventory": inventory}
        )[0],
        "cases": case_summaries,
        "result_projection_sha256": "",
    }
    report["result_projection_sha256"] = _projection(report)
    identity = _publish_report(output_root / "development-report.json", report)
    return {"report": report, "artifact_identity": identity}


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", choices=tuple(ROLE_OWNER))
    parser.add_argument("--preflight", choices=("fork", "sdim"))
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--gamma-index", type=int, choices=range(4))
    parser.add_argument("--rounds-star", type=int, choices=(4, 6, 8, 10, 12))
    parser.add_argument(
        "--fork-python-executable",
        type=Path,
        default=_DEFAULT_FORK_PYTHON,
    )
    parser.add_argument(
        "--sdim-python-executable",
        type=Path,
        default=_DEFAULT_SDIM_PYTHON,
    )
    parser.add_argument("--timeout-seconds", type=float, default=1800.0)
    parser.add_argument("--cell-limit", type=int)
    parser.add_argument("--print-plan", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.child is not None and args.preflight is not None:
        raise ValueError("--child and --preflight are mutually exclusive")
    if args.preflight is not None:
        forbidden = (
            args.output_root,
            args.gamma_index,
            args.rounds_star,
            args.cell_limit,
        )
        if any(value is not None for value in forbidden) or args.print_plan:
            raise ValueError("interpreter preflight accepts only --preflight")
        return _execute_interpreter_preflight(args.preflight)
    if args.child is not None:
        forbidden = (
            args.output_root,
            args.gamma_index,
            args.rounds_star,
            args.cell_limit,
        )
        if any(value is not None for value in forbidden) or args.print_plan:
            raise ValueError("development child accepts only --child")
        return _execute_child(args.child)
    if args.gamma_index is None or args.rounds_star is None:
        raise ValueError("parent requires --gamma-index and --rounds-star")
    plan_module = _load_path(_PLAN_PATH, "_gcapeps_fm_dev_cli_plan")
    if args.print_plan:
        print(
            _canonical(
                plan_module.build_development_plan(
                    gamma_index=args.gamma_index,
                    rounds_star=args.rounds_star,
                )
            ).decode("ascii"),
            flush=True,
        )
        return 0
    if args.output_root is None:
        raise ValueError("execution requires an explicit fresh --output-root")
    if (
        not math.isfinite(args.timeout_seconds)
        or args.timeout_seconds <= 0.0
    ):
        raise ValueError("--timeout-seconds must be finite and positive")
    result = run_sweep(
        output_root=args.output_root,
        gamma_index=args.gamma_index,
        rounds_star=args.rounds_star,
        fork_python=args.fork_python_executable,
        sdim_python=args.sdim_python_executable,
        timeout_seconds=args.timeout_seconds,
        cell_limit=args.cell_limit,
    )
    print(_canonical(result["artifact_identity"]).decode("ascii"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
