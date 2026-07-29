#!/usr/bin/env python3
"""Executable outer adapter for the finite-memory GCAPEPS experiment.

The intended formal path will delegate every scientific child lifecycle to the
systemd supervisor in ``run_gcapeps_finite_memory_bond32.py``; formal execution
remains unavailable until its authenticated adapter is wired.  The development
path is deliberately separate: it runs the same worker owners in fresh ordinary
subprocesses, records no systemd claims, is never claim-bearing, and cannot
publish a target amendment or a formal held-out report.
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
import signal
import stat
import subprocess
import sys
import time
from typing import Any, Callable, Mapping, Sequence


_SCRIPT_PATH = Path(__file__).resolve(strict=True)
_SCRIPT_DIR = _SCRIPT_PATH.parent
_REPOSITORY = _SCRIPT_DIR.parent.parent
_RUNNER_PATH = _SCRIPT_DIR / "run_gcapeps_finite_memory_bond32.py"
_ORCHESTRATION_PATH = _SCRIPT_DIR / "gcapeps_finite_memory_orchestration.py"
_EMITTER_PATH = _SCRIPT_DIR / "emit_gcapeps_finite_memory_fixture.py"
_DEVELOPMENT_SOURCE_PATHS = {
    "adapter": _SCRIPT_PATH,
    "orchestration": _ORCHESTRATION_PATH,
    "runner": _RUNNER_PATH,
}
_FORK_ROOT = _REPOSITORY / "external/forks/quimb-gcapeps"
_FORK_PIXI_LOCK = _FORK_ROOT / "pixi.lock"
_EXPECTED_FORK_COMMIT = "d90bb5ea210e666cbd7ecf8a8b7fa02390519baf"
_EXPECTED_FORK_TREE = "f7cd3496c48ec69f1800d41eabcaa8d53cab3b5b"
_EXPECTED_FORK_PIXI_LOCK_SHA256 = (
    "854da99b417c69dbdca4118c2545656470ad4e0f276a606b1b8c3082f795db35"
)
_DEFAULT_FORK_PYTHON = _FORK_ROOT / ".pixi/envs/testpymid/bin/python"
_DEFAULT_SDIM_PYTHON = Path(
    "/home/cx/miniforge3/envs/gcapeps-sdim/bin/python"
)
_EXPECTED_FORK_MODULE_ORIGINS = {
    "quimb": _FORK_ROOT / "quimb/__init__.py",
    "quimb.experimental.gcapeps": (
        _FORK_ROOT / "quimb/experimental/gcapeps/__init__.py"
    ),
}
_FORK_ORIGIN_PROBE = (
    "import json,quimb,quimb.experimental.gcapeps as gcapeps;"
    "print(json.dumps({'quimb':quimb.__file__,"
    "'quimb.experimental.gcapeps':gcapeps.__file__},"
    "sort_keys=True,separators=(',',':')))"
)
_SDIM_ORIGIN_PROBE = (
    "import json,sdim,stim;"
    "print(json.dumps({'sdim':sdim.__file__,'stim':stim.__file__},"
    "sort_keys=True,separators=(',',':')))"
)
_SDIM_MODULES = frozenset({"sdim", "stim"})

_SCHEMA_PREFIX = "error_coupling_simulator.external.gcapeps_finite_memory."
DEVELOPMENT_REQUEST_SCHEMA = _SCHEMA_PREFIX + "development_direct_request.v1"
DEVELOPMENT_PROCESS_SCHEMA = _SCHEMA_PREFIX + "development_direct_process.v1"
DEVELOPMENT_REPORT_SCHEMA = _SCHEMA_PREFIX + "development_direct.v1"
OUTER_TERMINAL_SCHEMA = _SCHEMA_PREFIX + "outer_terminal.v1"

_PUBLICATION_GATES = {
    "temporary_file_fsync": True,
    "rename_noreplace": True,
    "parent_directory_fsync": True,
    "destination_reopen_nofollow": True,
    "destination_identity_match": True,
    "exact_byte_reread": True,
}


def _load_path(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


@dataclass(frozen=True)
class RuntimeModules:
    runner: Any
    orchestration: Any
    runner_identity: Mapping[str, Any]


def initialize_runtime() -> RuntimeModules:
    """Set the parent nondumpable before importing any evaluator owner."""

    runner = _load_path(
        _RUNNER_PATH,
        "_gcapeps_finite_memory_experiment_runner",
    )
    runner_identity = runner.set_runner_nondumpable()
    orchestration = _load_path(
        _ORCHESTRATION_PATH,
        "_gcapeps_finite_memory_experiment_orchestration",
    )
    return RuntimeModules(
        runner=runner,
        orchestration=orchestration,
        runner_identity=runner_identity,
    )


def _strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_canonical_object(path: Path, *, canonical: Callable[[Any], bytes]) -> dict[str, Any]:
    raw = path.read_bytes()
    try:
        value = json.loads(
            raw.decode("ascii"),
            object_pairs_hook=_strict_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"nonfinite JSON token: {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path} is not canonical JSON") from exc
    if not isinstance(value, dict) or canonical(value) != raw:
        raise ValueError(f"{path} is not canonical compact ASCII JSON")
    return value


def _write_bytes_exclusive(path: Path, raw: bytes) -> dict[str, Any]:
    """Write one development artifact exactly once and fsync it."""

    if not path.is_absolute() or path.name in {"", ".", ".."}:
        raise ValueError("development artifact path must be absolute")
    parent = path.parent.resolve(strict=True)
    if parent != Path(os.path.abspath(path.parent)):
        raise ValueError("development artifact parent must be nonsymlink lexical")
    parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    fd = -1
    try:
        fd = os.open(
            path.name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o644,
            dir_fd=parent_fd,
        )
        cursor = 0
        while cursor < len(raw):
            written = os.write(fd, raw[cursor:])
            if written <= 0:
                raise RuntimeError("development artifact write made no progress")
            cursor += written
        os.fsync(fd)
        observed = os.fstat(fd)
        if (
            not stat.S_ISREG(observed.st_mode)
            or observed.st_size != len(raw)
            or stat.S_IMODE(observed.st_mode) != 0o644
            or observed.st_nlink != 1
        ):
            raise RuntimeError("development artifact inode identity is invalid")
        os.fsync(parent_fd)
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(parent_fd)
    return {
        "path": str(path),
        "byte_length": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _read_authenticated_bytes(identity: Mapping[str, Any]) -> bytes:
    if set(identity) != {"path", "byte_length", "sha256"}:
        raise ValueError("development artifact identity has wrong keys")
    path = Path(identity["path"])
    raw = path.read_bytes()
    if (
        len(raw) != identity["byte_length"]
        or hashlib.sha256(raw).hexdigest() != identity["sha256"]
    ):
        raise ValueError("development artifact identity drifted")
    return raw


@dataclass(frozen=True)
class DirectProduct:
    launch_id: str
    role: str
    terminal_kind: str
    core: Mapping[str, Any] | None
    core_bytes: bytes | None
    trailer_bytes: bytes | None
    stdout_identity: Mapping[str, Any]
    stderr_identity: Mapping[str, Any]
    process_receipt: Mapping[str, Any]
    process_receipt_identity: Any

@dataclass(frozen=True)
class DirectInterpreters:
    fork_python: Path
    fork_identity: Mapping[str, Any]
    sdim_python: Path
    sdim_identity: Mapping[str, Any]

    def select(self, runner: Any, role: str) -> tuple[Path, Mapping[str, Any]]:
        if role in {
            runner.SDIM_INVENTORY_COLLECTOR,
            runner.SDIM_COMPUTATION,
        }:
            return self.sdim_python, self.sdim_identity
        return self.fork_python, self.fork_identity


def _interpreter_identity(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    observed = resolved.stat()
    if not stat.S_ISREG(observed.st_mode) or not os.access(resolved, os.X_OK):
        raise ValueError(f"interpreter is not an executable regular file: {resolved}")
    raw = resolved.read_bytes()
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
        "byte_length": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "st_dev": observed.st_dev,
        "st_ino": observed.st_ino,
        "python_version": version,
    }


def _git_stdout(checkout: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ("git", "-C", str(checkout), *arguments),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        timeout=30.0,
    ).stdout


def _git_scalar(checkout: Path, *arguments: str) -> str:
    raw = _git_stdout(checkout, *arguments)
    try:
        value = raw.decode("ascii", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise RuntimeError("repository Git identity is not ASCII") from exc
    if not value or "\n" in value or "\r" in value:
        raise RuntimeError("repository Git identity is not one scalar")
    return value


def _source_file_identity(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    before = resolved.stat()
    if not stat.S_ISREG(before.st_mode):
        raise RuntimeError("development source identity is not a regular file")
    raw = resolved.read_bytes()
    after = resolved.stat()
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or len(raw) != after.st_size
    ):
        raise RuntimeError("development source identity changed while hashing")
    return {
        "path": str(resolved),
        "byte_length": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _parent_git_snapshot(checkout: Path) -> tuple[str, str, bytes]:
    return (
        _git_scalar(checkout, "rev-parse", "--verify", "HEAD^{commit}"),
        _git_scalar(checkout, "rev-parse", "--verify", "HEAD^{tree}"),
        _git_stdout(
            checkout,
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ),
    )


def _authenticate_parent_repository() -> dict[str, Any]:
    """Bind committed parent bytes; reject every tracked/untracked delta."""

    checkout = _REPOSITORY.resolve(strict=True)
    if not checkout.is_dir():
        raise RuntimeError("parent repository checkout is not a directory")
    commit, tree, status = _parent_git_snapshot(checkout)
    if status:
        raise RuntimeError("parent repository has tracked or untracked source drift")
    source_files = {
        name: _source_file_identity(path)
        for name, path in sorted(_DEVELOPMENT_SOURCE_PATHS.items())
    }
    commit_after, tree_after, status_after = _parent_git_snapshot(checkout)
    source_files_after = {
        name: _source_file_identity(path)
        for name, path in sorted(_DEVELOPMENT_SOURCE_PATHS.items())
    }
    if status_after:
        raise RuntimeError("parent repository changed during source authentication")
    if (
        commit_after != commit
        or tree_after != tree
        or source_files_after != source_files
    ):
        raise RuntimeError("parent repository identity changed during authentication")
    return {
        "checkout_realpath": str(checkout),
        "commit": commit,
        "tree": tree,
        "tracked_and_untracked_clean": True,
        "status_porcelain_v1_z_sha256": hashlib.sha256(status).hexdigest(),
        "source_files": source_files,
    }


def _authenticate_fork_checkout() -> dict[str, Any]:
    """Bind the exact clean fork source and its declared environment lock."""

    checkout = _FORK_ROOT.resolve(strict=True)
    lock = _FORK_PIXI_LOCK.resolve(strict=True)
    if not checkout.is_dir() or not lock.is_file():
        raise RuntimeError("fork checkout or pixi lock is not a regular source")
    try:
        lock.relative_to(checkout)
    except ValueError as exc:
        raise RuntimeError("fork pixi lock is outside the checkout") from exc

    commit = _git_scalar(checkout, "rev-parse", "--verify", "HEAD^{commit}")
    tree = _git_scalar(checkout, "rev-parse", "--verify", "HEAD^{tree}")
    status = _git_stdout(
        checkout,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    lock_sha256 = hashlib.sha256(lock.read_bytes()).hexdigest()
    if commit != _EXPECTED_FORK_COMMIT:
        raise RuntimeError("fork checkout commit drifted")
    if tree != _EXPECTED_FORK_TREE:
        raise RuntimeError("fork checkout tree drifted")
    if status:
        raise RuntimeError("fork checkout has tracked or untracked source drift")
    if lock_sha256 != _EXPECTED_FORK_PIXI_LOCK_SHA256:
        raise RuntimeError("fork pixi lock drifted")
    return {
        "checkout_realpath": str(checkout),
        "commit": commit,
        "tree": tree,
        "tracked_and_untracked_clean": True,
        "status_porcelain_v1_z_sha256": hashlib.sha256(status).hexdigest(),
        "pixi_lock_realpath": str(lock),
        "pixi_lock_sha256": lock_sha256,
    }


def _authenticate_fork_module_origins(python: Path) -> dict[str, Any]:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        (str(python), "-I", "-c", _FORK_ORIGIN_PROBE),
        cwd=_REPOSITORY,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30.0,
    )
    if completed.returncode != 0 or completed.stderr != b"":
        raise ValueError(
            "fork interpreter cannot cleanly import authenticated Quimb/GCAPEPS"
        )
    raw = completed.stdout
    try:
        value = json.loads(
            raw.decode("ascii").strip(),
            object_pairs_hook=_strict_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"nonfinite JSON token: {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("fork interpreter origin probe is invalid") from exc
    if not isinstance(value, dict) or set(value) != set(
        _EXPECTED_FORK_MODULE_ORIGINS
    ):
        raise ValueError("fork interpreter origin probe has wrong keys")
    authenticated: dict[str, str] = {}
    origin_sha256: dict[str, str] = {}
    for name, expected_path in _EXPECTED_FORK_MODULE_ORIGINS.items():
        observed_value = value[name]
        if not isinstance(observed_value, str):
            raise ValueError("fork interpreter module origin is not a path")
        try:
            observed = Path(observed_value).resolve(strict=True)
            expected = expected_path.resolve(strict=True)
        except OSError as exc:
            raise ValueError("fork interpreter module origin is unresolved") from exc
        if observed != expected:
            raise ValueError(
                f"fork interpreter imported {name} from an unauthenticated origin"
            )
        authenticated[name] = str(observed)
        origin_sha256[name] = _source_file_identity(observed)["sha256"]
    return {
        "isolated_python_mode": True,
        "module_origins": authenticated,
        "module_origin_sha256": origin_sha256,
        "probe_stdout_sha256": hashlib.sha256(raw).hexdigest(),
    }


def _authenticate_sdim_module_origins(python: Path) -> dict[str, Any]:
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        (str(python), "-I", "-c", _SDIM_ORIGIN_PROBE),
        cwd=_REPOSITORY,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30.0,
    )
    if completed.returncode != 0 or completed.stderr != b"":
        raise ValueError(
            "SDIM interpreter cannot cleanly import both sdim and stim"
        )
    raw = completed.stdout
    try:
        value = json.loads(
            raw.decode("ascii").strip(),
            object_pairs_hook=_strict_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"nonfinite JSON token: {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("SDIM interpreter origin probe is invalid") from exc
    if not isinstance(value, dict) or set(value) != _SDIM_MODULES:
        raise ValueError("SDIM interpreter origin probe has wrong keys")
    authenticated: dict[str, str] = {}
    origin_sha256: dict[str, str] = {}
    for name in sorted(_SDIM_MODULES):
        observed_value = value[name]
        if not isinstance(observed_value, str):
            raise ValueError("SDIM interpreter module origin is not a path")
        try:
            observed = Path(observed_value).resolve(strict=True)
        except OSError as exc:
            raise ValueError(
                "SDIM interpreter module origin is unresolved"
            ) from exc
        if not observed.is_file():
            raise ValueError("SDIM interpreter module origin is not a file")
        authenticated[name] = str(observed)
        origin_sha256[name] = _source_file_identity(observed)["sha256"]
    return {
        "isolated_python_mode": True,
        "module_origins": authenticated,
        "module_origin_sha256": origin_sha256,
        "probe_stdout_sha256": hashlib.sha256(raw).hexdigest(),
    }


def authenticate_direct_interpreters(
    *,
    fork_python: Path,
    sdim_python: Path,
) -> DirectInterpreters:
    fork = fork_python.resolve(strict=True)
    sdim = sdim_python.resolve(strict=True)
    fork_identity = _interpreter_identity(fork)
    fork_identity["module_origin_authentication"] = (
        _authenticate_fork_module_origins(fork)
    )
    fork_identity["fork_checkout_authentication"] = (
        _authenticate_fork_checkout()
    )
    sdim_identity = _interpreter_identity(sdim)
    sdim_identity["module_origin_authentication"] = (
        _authenticate_sdim_module_origins(sdim)
    )
    return DirectInterpreters(
        fork_python=fork,
        fork_identity=fork_identity,
        sdim_python=sdim,
        sdim_identity=sdim_identity,
    )


def _bind_development_source_identity(
    interpreters: DirectInterpreters,
    source_identity: Mapping[str, Any],
) -> DirectInterpreters:
    bound = dict(source_identity)
    fork_identity = dict(interpreters.fork_identity)
    sdim_identity = dict(interpreters.sdim_identity)
    if (
        "development_source_authentication" in fork_identity
        or "development_source_authentication" in sdim_identity
    ):
        raise ValueError("development source identity was already bound")
    fork_identity["development_source_authentication"] = bound
    sdim_identity["development_source_authentication"] = bound
    return DirectInterpreters(
        fork_python=interpreters.fork_python,
        fork_identity=fork_identity,
        sdim_python=interpreters.sdim_python,
        sdim_identity=sdim_identity,
    )


def _canonical_identity_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _direct_interpreters_identity(
    interpreters: DirectInterpreters,
) -> dict[str, Any]:
    return {
        "fork_python": str(interpreters.fork_python),
        "fork_identity": dict(interpreters.fork_identity),
        "sdim_python": str(interpreters.sdim_python),
        "sdim_identity": dict(interpreters.sdim_identity),
    }


def _recheck_development_execution_identity(
    *,
    interpreters: DirectInterpreters,
    source_identity: Mapping[str, Any],
) -> None:
    """Reject persistent source/environment drift before report publication."""

    current_source = _authenticate_parent_repository()
    if _canonical_identity_bytes(current_source) != _canonical_identity_bytes(
        source_identity
    ):
        raise ValueError("parent repository source changed during development run")
    current_interpreters = authenticate_direct_interpreters(
        fork_python=interpreters.fork_python,
        sdim_python=interpreters.sdim_python,
    )
    current_bound = _bind_development_source_identity(
        current_interpreters,
        current_source,
    )
    if _canonical_identity_bytes(
        _direct_interpreters_identity(current_bound)
    ) != _canonical_identity_bytes(
        _direct_interpreters_identity(interpreters)
    ):
        raise ValueError(
            "interpreter or source identity changed during development run"
        )


def _require_authenticated_direct_interpreters(
    interpreters: DirectInterpreters,
) -> None:
    if not isinstance(interpreters, DirectInterpreters):
        raise ValueError("development interpreters were not authenticated")
    try:
        identity_path = Path(interpreters.fork_identity["path"])
        authentication = interpreters.fork_identity[
            "module_origin_authentication"
        ]
        checkout_authentication = interpreters.fork_identity[
            "fork_checkout_authentication"
        ]
    except (KeyError, TypeError) as exc:
        raise ValueError("fork interpreter authentication is missing") from exc
    if identity_path != interpreters.fork_python:
        raise ValueError("fork interpreter identity path drifted")
    expected_origins = {
        name: str(path.resolve(strict=True))
        for name, path in _EXPECTED_FORK_MODULE_ORIGINS.items()
    }
    if not isinstance(authentication, Mapping):
        raise ValueError("fork module-origin authentication drifted")
    fork_origin_sha256 = authentication.get("module_origin_sha256")
    if (
        authentication.get("isolated_python_mode") is not True
        or authentication.get("module_origins") != expected_origins
        or not isinstance(fork_origin_sha256, Mapping)
        or set(fork_origin_sha256) != set(expected_origins)
        or any(
            not isinstance(value, str)
            or len(value) != 64
            or value.lower() != value
            or any(character not in "0123456789abcdef" for character in value)
            for value in fork_origin_sha256.values()
        )
        or not isinstance(authentication.get("probe_stdout_sha256"), str)
        or len(authentication["probe_stdout_sha256"]) != 64
    ):
        raise ValueError("fork module-origin authentication drifted")
    if dict(authentication) != _authenticate_fork_module_origins(
        interpreters.fork_python
    ):
        raise ValueError("fork module-origin authentication drifted")
    if (
        not isinstance(checkout_authentication, Mapping)
        or dict(checkout_authentication) != _authenticate_fork_checkout()
    ):
        raise ValueError("fork checkout authentication drifted")
    try:
        sdim_identity_path = Path(interpreters.sdim_identity["path"])
        sdim_authentication = interpreters.sdim_identity[
            "module_origin_authentication"
        ]
    except (KeyError, TypeError) as exc:
        raise ValueError("SDIM interpreter authentication is missing") from exc
    if sdim_identity_path != interpreters.sdim_python:
        raise ValueError("SDIM interpreter identity path drifted")
    if not isinstance(sdim_authentication, Mapping):
        raise ValueError("SDIM module-origin authentication drifted")
    sdim_origins = sdim_authentication.get("module_origins")
    sdim_origin_sha256 = sdim_authentication.get("module_origin_sha256")
    if (
        sdim_authentication.get("isolated_python_mode") is not True
        or not isinstance(sdim_origins, Mapping)
        or set(sdim_origins) != _SDIM_MODULES
        or not isinstance(sdim_origin_sha256, Mapping)
        or set(sdim_origin_sha256) != _SDIM_MODULES
        or any(
            not isinstance(value, str)
            or len(value) != 64
            or value.lower() != value
            or any(character not in "0123456789abcdef" for character in value)
            for value in sdim_origin_sha256.values()
        )
        or not isinstance(
            sdim_authentication.get("probe_stdout_sha256"),
            str,
        )
        or len(sdim_authentication["probe_stdout_sha256"]) != 64
    ):
        raise ValueError("SDIM module-origin authentication drifted")
    for origin in sdim_origins.values():
        if not isinstance(origin, str):
            raise ValueError("SDIM recorded module origin is invalid")
        try:
            if not Path(origin).resolve(strict=True).is_file():
                raise ValueError("SDIM recorded module origin is not a file")
        except OSError as exc:
            raise ValueError("SDIM recorded module origin is unresolved") from exc
    if dict(sdim_authentication) != _authenticate_sdim_module_origins(
        interpreters.sdim_python
    ):
        raise ValueError("SDIM module-origin authentication drifted")


def _dependency_names(runner: Any, spec: Any) -> tuple[str, ...]:
    role = spec.role
    if role in {
        runner.NEUTRAL_FIXTURE_EMITTER,
        runner.SDIM_INVENTORY_COLLECTOR,
    }:
        return ()
    if role in {
        runner.DENSE_REFERENCE,
        runner.PLAIN_CAP_PROBE,
        runner.GCAPEPS_CAP_PROBE,
        runner.PLAIN_EVIDENCE,
        runner.GCAPEPS_EVIDENCE,
        runner.PLAIN_PERFORMANCE,
        runner.GCAPEPS_PERFORMANCE,
    }:
        return ("fixture",)
    if role == runner.SDIM_COMPUTATION:
        return ("fixture", "inventory")
    if role == runner.TERMINAL_COMPARATOR:
        return (
            "fixture",
            "dense",
            "plain_input1",
            "plain_input2",
            "gc_input1",
            "gc_input2",
            "sdim",
        )
    raise ValueError(f"role {role!r} is not available in development-direct")


def _semantic_dependency_products(
    runner: Any,
    spec: Any,
    registry: Mapping[str, DirectProduct],
    *,
    inventory: DirectProduct,
) -> dict[str, DirectProduct]:
    launch_ids = tuple(spec.dependency_launch_ids)
    if len(set(launch_ids)) != len(launch_ids):
        raise ValueError("development dependency launch id is duplicated")
    try:
        dependencies = tuple(registry[launch_id] for launch_id in launch_ids)
    except KeyError as exc:
        raise ValueError("development dependency launch id is missing") from exc
    for launch_id, product in zip(launch_ids, dependencies, strict=True):
        if (
            product.launch_id != launch_id
            or product.terminal_kind != "completed_result"
            or product.core is None
        ):
            raise ValueError("development dependency producer is invalid")
    tokens = tuple(
        (
            product.role,
            product.process_receipt["role_parameters"].get("input_id"),
        )
        for product in dependencies
    )
    if spec.role == runner.NEUTRAL_FIXTURE_EMITTER:
        expected_tokens: tuple[tuple[str, int | None], ...] = ()
    elif spec.role == runner.TERMINAL_COMPARATOR:
        expected_tokens = (
            (runner.NEUTRAL_FIXTURE_EMITTER, None),
            (runner.DENSE_REFERENCE, None),
            (runner.PLAIN_EVIDENCE, 1),
            (runner.PLAIN_EVIDENCE, 2),
            (runner.GCAPEPS_EVIDENCE, 1),
            (runner.GCAPEPS_EVIDENCE, 2),
            (runner.SDIM_COMPUTATION, None),
        )
    elif spec.role in {
        runner.DENSE_REFERENCE,
        runner.PLAIN_CAP_PROBE,
        runner.GCAPEPS_CAP_PROBE,
        runner.PLAIN_EVIDENCE,
        runner.GCAPEPS_EVIDENCE,
        runner.PLAIN_PERFORMANCE,
        runner.GCAPEPS_PERFORMANCE,
        runner.SDIM_COMPUTATION,
    }:
        expected_tokens = ((runner.NEUTRAL_FIXTURE_EMITTER, None),)
    else:
        raise ValueError("development role has no dependency contract")
    if tokens != expected_tokens:
        raise ValueError("development dependency role/input cardinality drifted")
    names = _dependency_names(runner, spec)
    if spec.role == runner.SDIM_COMPUTATION:
        if (
            inventory.role != runner.SDIM_INVENTORY_COLLECTOR
            or inventory.terminal_kind != "completed_result"
            or inventory.core is None
        ):
            raise ValueError("development SDIM inventory dependency is invalid")
        products = dependencies + (inventory,)
    else:
        products = dependencies
    if len(names) != len(products):
        raise AssertionError("development semantic dependency arity drifted")
    return dict(zip(names, products, strict=True))


def _with_projection(runner: Any, payload: Mapping[str, Any]) -> dict[str, Any]:
    return runner.with_result_projection(dict(payload))


def _direct_request(
    runner: Any,
    spec: Any,
    dependencies: Mapping[str, DirectProduct],
) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for name, product in dependencies.items():
        core_identity = product.process_receipt.get("core_identity")
        if (
            product.terminal_kind != "completed_result"
            or not isinstance(product.core, Mapping)
            or not isinstance(product.core.get("schema"), str)
            or not isinstance(core_identity, Mapping)
        ):
            raise ValueError("development dependency is not a completed core")
        rows[name] = {
            "producer_launch_id": product.launch_id,
            "producer_role": product.role,
            "core_schema": product.core["schema"],
            "core_identity": dict(core_identity),
        }
    return _with_projection(
        runner,
        {
            "schema": DEVELOPMENT_REQUEST_SCHEMA,
            "formal_claim_eligible": False,
            "launch_id": spec.launch_id,
            "run_partition": spec.run_partition,
            "role": spec.role,
            "role_parameters": spec.parameter_map(),
            "dependencies": rows,
        },
    )


def _core_file_dependency_stub(product: DirectProduct) -> DirectProduct:
    """Drop parsed/raw payloads while retaining authenticated disk identity."""

    core_identity = product.process_receipt.get("core_identity")
    if (
        product.terminal_kind != "completed_result"
        or not isinstance(product.core, Mapping)
        or not isinstance(product.core.get("schema"), str)
        or not isinstance(core_identity, Mapping)
    ):
        raise ValueError("completed dependency product lacks a core-file identity")
    return DirectProduct(
        launch_id=product.launch_id,
        role=product.role,
        terminal_kind=product.terminal_kind,
        core={"schema": product.core["schema"]},
        core_bytes=None,
        trailer_bytes=None,
        stdout_identity=product.stdout_identity,
        stderr_identity=product.stderr_identity,
        process_receipt=product.process_receipt,
        process_receipt_identity=product.process_receipt_identity,
    )


def _retains_calibration_dependency(runner: Any, role: str) -> bool:
    return role in {
        runner.NEUTRAL_FIXTURE_EMITTER,
        runner.DENSE_REFERENCE,
        runner.PLAIN_EVIDENCE,
        runner.GCAPEPS_EVIDENCE,
        runner.SDIM_COMPUTATION,
    }


def _read_direct_dependency(
    runner: Any,
    row: Mapping[str, Any],
) -> dict[str, Any]:
    if set(row) != {
        "producer_launch_id",
        "producer_role",
        "core_schema",
        "core_identity",
    }:
        raise ValueError("development dependency row has wrong keys")
    raw = _read_authenticated_bytes(row["core_identity"])
    core = runner.parse_canonical_json_object(raw)
    if (
        core.get("schema") != row["core_schema"]
        or runner.ROLE_CORE_SCHEMAS[row["producer_role"]] != row["core_schema"]
    ):
        raise ValueError("development dependency schema drifted")
    runner.validate_result_projection(core)
    return core


def _development_child(
    request_path: Path,
    *,
    file_limit_bytes: int,
) -> int:
    """Execute exactly one owner in an ordinary, nonformal child process."""

    if (
        isinstance(file_limit_bytes, bool)
        or not isinstance(file_limit_bytes, int)
        or file_limit_bytes <= 0
    ):
        raise ValueError("development child file limit is invalid")
    resource.setrlimit(
        resource.RLIMIT_FSIZE,
        (file_limit_bytes, file_limit_bytes),
    )
    runtime = initialize_runtime()
    runner = runtime.runner
    request = _read_canonical_object(
        request_path,
        canonical=runner.canonical_json_bytes,
    )
    runner.validate_result_projection(request)
    partition = request.get("run_partition")
    if (
        request.get("schema") != DEVELOPMENT_REQUEST_SCHEMA
        or request.get("formal_claim_eligible") is not False
        or partition not in {runner.BOOTSTRAP, runner.CALIBRATION}
        or (
            partition == runner.BOOTSTRAP
            and request.get("role") != runner.SDIM_INVENTORY_COLLECTOR
        )
    ):
        raise ValueError("development child request identity is invalid")
    role = request["role"]
    runner.validate_role_parameters(
        request["run_partition"],
        role,
        request["role_parameters"],
    )
    expected_names = _dependency_names(runner, type("_Spec", (), {"role": role})())
    dependencies = request["dependencies"]
    if (
        not isinstance(dependencies, Mapping)
        or set(dependencies) != set(expected_names)
        or len(dependencies) != len(expected_names)
    ):
        raise ValueError("development child dependency sequence drifted")
    cores = {
        name: _read_direct_dependency(runner, dependencies[name])
        for name in expected_names
    }
    owner_path = runner.resolve_role_owner(role)
    owner = _load_path(
        owner_path,
        f"_gcapeps_fm_development_owner_{role}_{os.getpid()}",
    )
    parameters = request["role_parameters"]
    if role == runner.SDIM_INVENTORY_COLLECTOR:
        result = owner.run_inventory_worker()
    elif role == runner.NEUTRAL_FIXTURE_EMITTER:
        def build_fixture() -> Mapping[str, Any]:
            fixture = owner.build_fixture(
                run_partition=runner.CALIBRATION,
                width=parameters["width"],
                rounds=parameters["rounds"],
                axis_family=parameters["axis_family"],
                p_event_numerator=parameters["p_event_numerator"],
                seed=parameters["seed"],
                gamma_index=parameters["gamma_index"],
                run_blpensemble=parameters["run_blpensemble"],
            )
            owner.validate_fixture(fixture)
            return fixture

        result = runner._standard_result_from_core_builder(
            builder=build_fixture,
            root_span_id="neutral_fixture.root",
            root_scope="neutral_fixture_worker_total",
            compute_span_id="neutral_fixture.build",
            compute_scope="neutral_fixture_construction",
            lane="neutral_fixture",
            kind="deterministic_fixture",
        )
    elif role == runner.DENSE_REFERENCE:
        result = owner.build_framed_worker_output(cores["fixture"])
    elif role in {runner.PLAIN_CAP_PROBE, runner.GCAPEPS_CAP_PROBE}:
        result = owner.run_cap_probe(
            cores["fixture"],
            input_id=parameters["input_id"],
        )
    elif role in {runner.PLAIN_EVIDENCE, runner.GCAPEPS_EVIDENCE}:
        result = owner.run_evidence(
            cores["fixture"],
            input_id=parameters["input_id"],
        )
    elif role == runner.SDIM_COMPUTATION:
        result = owner.run_frame_control_worker(
            cores["fixture"],
            inventory_core=cores["inventory"],
        )
    elif role == runner.TERMINAL_COMPARATOR:
        result = owner.run_comparator_worker(
            fixture=cores["fixture"],
            dense_core=cores["dense"],
            plain_input1_core=cores["plain_input1"],
            plain_input2_core=cores["plain_input2"],
            gcapeps_input1_core=cores["gc_input1"],
            gcapeps_input2_core=cores["gc_input2"],
            sdim_core=cores["sdim"],
            timing_module=runner._TIMING,
        )
    else:
        raise ValueError("development child role is unsupported")
    framed = result if isinstance(result, bytes) else result["framed_bytes"]
    runner.decode_clean_worker_frames(framed, role=role)
    cursor = 0
    while cursor < len(framed):
        written = os.write(1, framed[cursor:])
        if written <= 0:
            raise RuntimeError("development child stdout write made no progress")
        cursor += written
    os.fsync(1)
    return 0


def _qualifier_from_core(runner: Any, spec: Any, core: Mapping[str, Any]) -> bool | None:
    """Recompute only the registered calibration gate; never read fidelity."""

    if spec.role == runner.DENSE_REFERENCE:
        fixed = core.get("fixed_blp")
        expected_keys = {
            "object",
            "difference_eigenvalues_by_round",
            "trace_distances",
            "increments",
            "summed_positive_increments",
            "maximum_increment",
            "witness_threshold",
            "verdict",
        }
        if not isinstance(fixed, Mapping) or set(fixed) != expected_keys:
            raise ValueError("dense core fixed-mask BLP shape drifted")
        distances = fixed["trace_distances"]
        spectra = fixed["difference_eigenvalues_by_round"]
        if (
            not isinstance(distances, list)
            or len(distances) < 2
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(float(value))
                for value in distances
            )
        ):
            raise ValueError("dense fixed-mask BLP distances are invalid")
        if not isinstance(spectra, list) or len(spectra) != len(distances):
            raise ValueError(
                "dense fixed-mask BLP difference spectra are invalid"
            )

        increments = [
            float(distances[index] - distances[index - 1])
            for index in range(1, len(distances))
        ]
        maximum = max(increments)
        qualifies = maximum > 1.0e-10
        expected_verdict = (
            "BLP_WITNESSED_FIXED_MASK"
            if qualifies
            else "NO_WITNESS_FIXED_MASK_FOR_REGISTERED_PAIR"
        )
        if (
            fixed["object"] != "fixed_carrier_mask"
            or fixed["witness_threshold"] != 1.0e-10
            or fixed["increments"] != increments
            or fixed["summed_positive_increments"]
            != float(math.fsum(max(0.0, value) for value in increments))
            or fixed["maximum_increment"] != maximum
            or fixed["verdict"] != expected_verdict
        ):
            raise ValueError("dense fixed-mask BLP summary is inconsistent")
        return qualifies
    if spec.role in {
        runner.PLAIN_CAP_PROBE,
        runner.GCAPEPS_CAP_PROBE,
        runner.PLAIN_EVIDENCE,
        runner.GCAPEPS_EVIDENCE,
    }:
        count = core.get("positive_cap_event_count")
        rows = core.get("split_records")
        if (
            isinstance(count, bool)
            or not isinstance(count, int)
            or count < 0
            or not isinstance(rows, list)
        ):
            raise ValueError("worker positive-cap evidence is invalid")
        positives = 0
        for row in rows:
            if not isinstance(row, Mapping) or not isinstance(
                row.get("positive_discarded_weight"),
                bool,
            ):
                raise ValueError("worker split-row positive flag is invalid")
            positives += int(row["positive_discarded_weight"])
        if count != positives:
            raise ValueError("worker positive-cap count disagrees with split rows")
        return count > 0
    if spec.role == runner.TERMINAL_COMPARATOR:
        gate = core.get("positive_bond32_gate")
        if not isinstance(gate, Mapping) or set(gate) != {
            "definition",
            "paths",
            "all_four_paths_positive",
        }:
            raise ValueError("comparator calibration terminal gate shape drifted")
        definition = gate["definition"]
        if (
            not isinstance(definition, Mapping)
            or set(definition)
            != {
                "configured_max_bond",
                "minimum_full_bond_dimension",
                "kept_bond_dimension",
                "discarded_squared_weight_strictly_greater_than",
                "cause",
            }
            or definition["configured_max_bond"] != 32
            or definition["minimum_full_bond_dimension"] != 33
            or definition["kept_bond_dimension"] != 32
            or definition["discarded_squared_weight_strictly_greater_than"]
            != 1.0e-12
            or definition["cause"] != "max_bond"
        ):
            raise ValueError("comparator positive-tail definition drifted")
        paths = gate["paths"]
        expected_paths = {
            ("plain", 1),
            ("plain", 2),
            ("gcapeps", 1),
            ("gcapeps", 2),
        }
        observed_paths: set[tuple[str, int]] = set()
        path_booleans = []
        if not isinstance(paths, list) or len(paths) != 4:
            raise ValueError("comparator calibration terminal paths drifted")
        for row in paths:
            if not isinstance(row, Mapping) or set(row) != {
                "lane",
                "input_id",
                "positive_bond32_event",
                "positive_event_count",
                "qualifying_event_locators",
            }:
                raise ValueError("comparator calibration path shape drifted")
            count = row["positive_event_count"]
            locators = row["qualifying_event_locators"]
            positive = row["positive_bond32_event"]
            if (
                not isinstance(row["lane"], str)
                or row["lane"] not in {"plain", "gcapeps"}
                or isinstance(row["input_id"], bool)
                or not isinstance(row["input_id"], int)
                or row["input_id"] not in {1, 2}
                or isinstance(count, bool)
                or not isinstance(count, int)
                or count < 0
                or not isinstance(locators, list)
                or len(locators) != count
                or not isinstance(positive, bool)
                or positive is not (count > 0)
            ):
                raise ValueError("comparator calibration path is inconsistent")
            observed_paths.add((row["lane"], row["input_id"]))
            path_booleans.append(positive)
        expected_all = all(path_booleans)
        if (
            observed_paths != expected_paths
            or gate["all_four_paths_positive"] is not expected_all
        ):
            raise ValueError("comparator calibration terminal gate is inconsistent")
        return expected_all
    return None


def _direct_process_receipt(
    runner: Any,
    *,
    spec: Any,
    pid: int,
    returncode: int | None,
    timed_out: bool,
    wall_ns: int,
    termination_method: str,
    terminal_kind: str,
    interpreter_identity: Mapping[str, Any],
    stdout_identity: Mapping[str, Any],
    stderr_identity: Mapping[str, Any],
    core_identity: Mapping[str, Any] | None,
    trailer_sha256: str | None,
) -> dict[str, Any]:
    return _with_projection(
        runner,
        {
            "schema": DEVELOPMENT_PROCESS_SCHEMA,
            "formal_claim_eligible": False,
            "systemd_facts": None,
            "launch_id": spec.launch_id,
            "run_partition": spec.run_partition,
            "role": spec.role,
            "role_parameters": spec.parameter_map(),
            "pid": pid,
            "returncode": returncode,
            "timed_out": timed_out,
            "termination_method": termination_method,
            "fresh_ordinary_subprocess": True,
            "interpreter_identity": dict(interpreter_identity),
            "process_wall_ns": wall_ns,
            "terminal_kind": terminal_kind,
            "stdout_identity": dict(stdout_identity),
            "stderr_identity": dict(stderr_identity),
            "core_identity": None if core_identity is None else dict(core_identity),
            "trailer_sha256": trailer_sha256,
        },
    )


def _bounded_regular_file(
    path: Path,
    *,
    byte_cap: int,
) -> tuple[dict[str, Any], bytes | None, bool]:
    if isinstance(byte_cap, bool) or not isinstance(byte_cap, int) or byte_cap < 0:
        raise ValueError("development file byte cap is invalid")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        observed = os.fstat(fd)
        if not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1:
            raise ValueError("development child output is not a single-link file")
        exceeded = observed.st_size > byte_cap
        digest = hashlib.sha256()
        chunks: list[bytes] | None = [] if not exceeded else None
        remaining = observed.st_size
        while remaining:
            chunk = os.read(fd, min(1 << 20, remaining))
            if not chunk:
                raise RuntimeError("development child output truncated during read")
            digest.update(chunk)
            if chunks is not None:
                chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(fd, 1):
            raise RuntimeError("development child output grew during read")
        identity = {
            "path": str(path),
            "byte_length": observed.st_size,
            "sha256": digest.hexdigest(),
        }
        return (
            identity,
            None if chunks is None else b"".join(chunks),
            exceeded,
        )
    finally:
        os.close(fd)


def _wait_for_process_group_exit(
    pgid: int,
    *,
    grace_seconds: float,
) -> None:
    if (
        isinstance(grace_seconds, bool)
        or not isinstance(grace_seconds, (int, float))
        or not math.isfinite(float(grace_seconds))
        or grace_seconds < 0
    ):
        raise ValueError("process-group cleanup grace is invalid")
    deadline = time.monotonic() + float(grace_seconds)
    while True:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError("development child process group survived SIGKILL")
        time.sleep(min(0.01, remaining))


def _terminate_process_group(
    process: subprocess.Popen[Any],
    *,
    grace_seconds: float = 2.0,
) -> str:
    parent_was_running = process.poll() is None
    if parent_was_running:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            pass
    group_survived_term = False
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        pass
    else:
        group_survived_term = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if process.poll() is None:
        process.wait(timeout=grace_seconds)
    if group_survived_term:
        _wait_for_process_group_exit(
            process.pid,
            grace_seconds=grace_seconds,
        )
        return "sigterm_then_sigkill_group"
    if parent_was_running:
        return "sigterm"
    return "already_exited"


def _close_development_streams(
    streams: Sequence[Any | None],
    *,
    active_error: bool,
) -> None:
    """Best-effort fsync and close every child stream without masking failures."""

    cleanup_error: BaseException | None = None
    for stream in streams:
        if stream is None:
            continue
        try:
            os.fsync(stream.fileno())
        except BaseException as exc:
            if cleanup_error is None:
                cleanup_error = exc
        try:
            stream.close()
        except BaseException as exc:
            if cleanup_error is None:
                cleanup_error = exc
    if cleanup_error is not None and not active_error:
        raise cleanup_error


def launch_development_direct(
    *,
    runtime: RuntimeModules,
    spec: Any,
    dependencies: Mapping[str, DirectProduct],
    output_root: Path,
    interpreters: DirectInterpreters,
    timeout_seconds: float,
) -> DirectProduct:
    """Launch one real fresh ordinary worker without lifecycle fabrication."""

    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(float(timeout_seconds))
        or timeout_seconds <= 0
    ):
        raise ValueError("development child timeout must be positive")
    runner = runtime.runner
    python_executable, interpreter_identity = interpreters.select(
        runner,
        spec.role,
    )
    request = _direct_request(runner, spec, dependencies)
    request_path = output_root / f"{spec.launch_id}.development-request.json"
    request_identity = runner.publish_canonical_json_noreplace(
        request_path,
        request,
    )
    stdout_path = output_root / f"{spec.launch_id}.development-stdout.frames"
    stderr_path = output_root / f"{spec.launch_id}.development-stderr.bin"
    stdout_cap = runner.frame_limits(spec.role)[2]
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.update(
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        }
    )
    stdout_file = None
    stderr_file = None
    process = None
    timed_out = False
    termination_method = "normal"
    start = time.monotonic_ns()
    try:
        stdout_file = stdout_path.open("xb", buffering=0)
        stderr_file = stderr_path.open("xb", buffering=0)
        process = subprocess.Popen(
            (
                str(python_executable),
                str(_SCRIPT_PATH),
                "--development-child-request",
                request_identity.path,
                "--development-file-limit-bytes",
                str(stdout_cap),
            ),
            stdin=subprocess.DEVNULL,
            stdout=stdout_file,
            stderr=stderr_file,
            cwd=_REPOSITORY,
            env=environment,
            close_fds=True,
            start_new_session=True,
        )
        try:
            returncode = process.wait(timeout=float(timeout_seconds))
        except subprocess.TimeoutExpired:
            timed_out = True
            termination_method = _terminate_process_group(process)
            returncode = process.returncode
        except BaseException:
            termination_method = _terminate_process_group(process)
            raise
    finally:
        active_error = sys.exc_info()[0] is not None
        _close_development_streams(
            (stdout_file, stderr_file),
            active_error=active_error,
        )
    if process is None:
        raise RuntimeError("development subprocess was not created")
    wall_ns = time.monotonic_ns() - start
    stdout_identity, stdout_raw, stdout_exceeded = _bounded_regular_file(
        stdout_path,
        byte_cap=stdout_cap,
    )
    stderr_identity, stderr_raw, stderr_exceeded = _bounded_regular_file(
        stderr_path,
        byte_cap=runner.STDERR_MAX_BYTES,
    )
    decoded = None
    terminal_kind = "supervisor_censor" if timed_out else "invalid_control"
    if (
        not timed_out
        and returncode == 0
        and not stdout_exceeded
        and not stderr_exceeded
        and stderr_raw == b""
        and stdout_raw is not None
    ):
        try:
            decoded = runner.decode_clean_worker_frames(stdout_raw, role=spec.role)
            terminal_kind = runner.classify_clean_worker_core(decoded.core)
        except (TypeError, ValueError):
            decoded = None
            terminal_kind = "invalid_control"
    core_identity = None
    if decoded is not None:
        core_path = output_root / f"{spec.launch_id}.development-core.json"
        core_identity = _write_bytes_exclusive(core_path, decoded.core_bytes)
    receipt = _direct_process_receipt(
        runner,
        spec=spec,
        pid=process.pid,
        returncode=returncode,
        timed_out=timed_out,
        wall_ns=wall_ns,
        terminal_kind=terminal_kind,
        termination_method=termination_method,
        interpreter_identity=interpreter_identity,
        stdout_identity=stdout_identity,
        stderr_identity=stderr_identity,
        core_identity=core_identity,
        trailer_sha256=(
            None
            if decoded is None
            else hashlib.sha256(decoded.trailer_bytes).hexdigest()
        ),
    )
    receipt_identity = runner.publish_canonical_json_noreplace(
        output_root / f"{spec.launch_id}.development-process.json",
        receipt,
    )
    return DirectProduct(
        launch_id=spec.launch_id,
        role=spec.role,
        terminal_kind=terminal_kind,
        core=None if decoded is None else decoded.core,
        core_bytes=None if decoded is None else decoded.core_bytes,
        trailer_bytes=None if decoded is None else decoded.trailer_bytes,
        stdout_identity=stdout_identity,
        stderr_identity=stderr_identity,
        process_receipt=receipt,
        process_receipt_identity=receipt_identity,
    )


def _development_search_json(orchestration: Any, result: Any) -> dict[str, Any]:
    selection = None
    if result.selection is not None:
        pair = result.selection.pair
        selection = {
            "gamma_index": pair.gamma_index,
            "gamma_label": pair.gamma_label,
            "gamma_float64_hex": pair.gamma_float64_hex,
            "rounds_index": pair.rounds_index,
            "rounds_star": pair.rounds,
            "qualifying_seeds": list(result.selection.qualifying_seeds),
        }
    return {
        "wall_root_ns": result.wall_root_ns,
        "wall_deadline_ns": result.wall_deadline_ns,
        "probe_attempt_count": result.probe_attempt_count,
        "prepublication_disposition": result.prepublication_disposition,
        "selection": selection,
        "launch_audit": [
            {
                "ordinal": row.spec.ordinal,
                "launch_id": row.spec.launch_id,
                "role": row.spec.role,
                "role_parameters": row.spec.parameter_map(),
                "dependency_launch_ids": list(row.spec.dependency_launch_ids),
                "executed": row.executed,
                "disposition": row.disposition,
                "terminal_kind": row.terminal_kind,
                "qualifier": row.qualifier,
                "direct_stdout_sha256": row.envelope_complete_file_sha256,
                "direct_process_receipt_sha256": (
                    row.launch_receipt_complete_file_sha256
                ),
                "prelaunch_wall_offset_ns": row.prelaunch_wall_offset_ns,
                "terminal_wall_offset_ns": row.terminal_wall_offset_ns,
                "probe_attempt_before": row.probe_attempt_before,
                "probe_attempt_after": row.probe_attempt_after,
            }
            for row in result.launch_audit
        ],
        "stage_seed_audit": [
            {
                "pair_id": row.pair_id,
                "stage": row.stage,
                "seed": row.seed,
                "disposition": row.disposition,
                "launch_ids": list(row.launch_ids),
            }
            for row in result.stage_seed_audit
        ],
    }


def build_development_report(
    *,
    runtime: RuntimeModules,
    inventory: DirectProduct,
    search_result: Any | None,
    bootstrap_terminal_kind: str,
    registry_resource_audit: Mapping[str, Any],
    source_identity: Mapping[str, Any],
) -> dict[str, Any]:
    runner = runtime.runner
    orchestration = runtime.orchestration
    return _with_projection(
        runner,
        {
            "schema": DEVELOPMENT_REPORT_SCHEMA,
            "formal_claim_eligible": False,
            "execution_mode": "fresh_ordinary_subprocesses",
            "systemd_facts": None,
            "calibration_graph": "frozen_adaptive_graph",
            "runs_full_adaptive_calibration": True,
            "development_pair_bound": None,
            "production_b_cal_transport_equivalent": False,
            "dependency_transport_note": (
                "development uses direct core-file dependencies and does not "
                "bind inventory into every production B_CAL transport"
            ),
            "source_identity": dict(source_identity),
            "dependency_registry": dict(registry_resource_audit),
            "bootstrap_terminal_kind": bootstrap_terminal_kind,
            "inventory": {
                "stdout_identity": dict(inventory.stdout_identity),
                "process_receipt_identity": (
                    inventory.process_receipt_identity.as_dict()
                ),
            },
            "calibration": (
                None
                if search_result is None
                else _development_search_json(orchestration, search_result)
            ),
            "direct_hash_semantics": {
                "launch_audit_envelope_hash_field_contains": (
                    "direct_worker_stdout_complete_file_sha256"
                ),
                "launch_audit_receipt_hash_field_contains": (
                    "development_process_receipt_complete_file_sha256"
                ),
            },
            "forbidden_outputs": [
                "target_amendment",
                "formal_heldout_report",
                "systemd_node_terminal",
                "systemd_launch_receipt",
            ],
            "claim_boundary": (
                "development-only execution smoke; not calibration evidence, "
                "not amendment-eligible, and not held-out evidence"
            ),
        },
    )


def run_development_direct(
    *,
    runtime: RuntimeModules,
    output_root: Path,
    interpreters: DirectInterpreters,
    timeout_seconds: float,
    source_identity: Mapping[str, Any] | None = None,
    launch_direct: Callable[..., DirectProduct] = launch_development_direct,
) -> tuple[dict[str, Any], Any]:
    """Run the complete frozen calibration graph in nonformal subprocesses."""

    runner = runtime.runner
    orchestration = runtime.orchestration
    _require_authenticated_direct_interpreters(interpreters)
    authenticated_source = (
        _authenticate_parent_repository()
        if source_identity is None
        else dict(source_identity)
    )
    if authenticated_source != _authenticate_parent_repository():
        raise ValueError("parent repository source authentication drifted")
    interpreters = _bind_development_source_identity(
        interpreters,
        authenticated_source,
    )
    output_root.mkdir(parents=True, exist_ok=False)
    registry_resource_audit = {
        "retention": "pair_scoped_authenticated_core_file_identity_only",
        "maximum_live_entries": 0,
        "maximum_retained_core_or_trailer_bytes": 0,
        "pair_reset_count": 0,
        "final_live_entries": 0,
    }
    inventory_spec = type(
        "DevelopmentInventorySpec",
        (),
        {
            "launch_id": "dev-sdim-inventory",
            "run_partition": runner.BOOTSTRAP,
            "role": runner.SDIM_INVENTORY_COLLECTOR,
            "dependency_launch_ids": (),
            "parameter_map": lambda self: {},
        },
    )()
    inventory = launch_direct(
        runtime=runtime,
        spec=inventory_spec,
        dependencies={},
        output_root=output_root,
        interpreters=interpreters,
        timeout_seconds=timeout_seconds,
    )
    if inventory.terminal_kind != "completed_result":
        _recheck_development_execution_identity(
            interpreters=interpreters,
            source_identity=authenticated_source,
        )
        report = build_development_report(
            runtime=runtime,
            inventory=inventory,
            search_result=None,
            bootstrap_terminal_kind=inventory.terminal_kind,
            registry_resource_audit=registry_resource_audit,
            source_identity=authenticated_source,
        )
        identity = runner.publish_canonical_json_noreplace(
            output_root / "development_direct_report.json",
            report,
        )
        return report, identity
    inventory = _core_file_dependency_stub(inventory)
    registry: dict[str, DirectProduct] = {}
    active_pair_key: tuple[int, int] | None = None

    def launch_one(spec: Any) -> Any:
        nonlocal active_pair_key
        parameters = spec.parameter_map()
        gamma_index = parameters.get("gamma_index")
        rounds_index = parameters.get("rounds_index")
        if (
            isinstance(gamma_index, bool)
            or not isinstance(gamma_index, int)
            or isinstance(rounds_index, bool)
            or not isinstance(rounds_index, int)
        ):
            raise ValueError("development calibration pair identity is invalid")
        pair_key = (gamma_index, rounds_index)
        if active_pair_key is None:
            active_pair_key = pair_key
        elif pair_key != active_pair_key:
            registry.clear()
            active_pair_key = pair_key
            registry_resource_audit["pair_reset_count"] += 1
        dependencies = _semantic_dependency_products(
            runner,
            spec,
            registry,
            inventory=inventory,
        )
        product = launch_direct(
            runtime=runtime,
            spec=spec,
            dependencies=dependencies,
            output_root=output_root,
            interpreters=interpreters,
            timeout_seconds=timeout_seconds,
        )
        qualifier = None
        if product.terminal_kind == "completed_result":
            if product.core is None:
                raise RuntimeError("completed development worker has no core")
            qualifier = _qualifier_from_core(runner, spec, product.core)
            if _retains_calibration_dependency(runner, spec.role):
                registry[spec.launch_id] = _core_file_dependency_stub(product)
        retained_bytes = sum(
            len(retained.core_bytes or b"")
            + len(retained.trailer_bytes or b"")
            for retained in registry.values()
        )
        registry_resource_audit["maximum_live_entries"] = max(
            registry_resource_audit["maximum_live_entries"],
            len(registry),
        )
        registry_resource_audit[
            "maximum_retained_core_or_trailer_bytes"
        ] = max(
            registry_resource_audit[
                "maximum_retained_core_or_trailer_bytes"
            ],
            retained_bytes,
        )
        if spec.role == runner.TERMINAL_COMPARATOR:
            for launch_id in spec.dependency_launch_ids:
                registry.pop(launch_id, None)
        return orchestration.NodeObservation(
            terminal_kind=product.terminal_kind,
            qualifier=qualifier,
            envelope_complete_file_sha256=product.stdout_identity["sha256"],
            launch_receipt_complete_file_sha256=(
                product.process_receipt_identity.sha256
            ),
        )

    result = orchestration.run_calibration_search(
        launch_one,
        clock_ns=time.monotonic_ns,
    )
    registry.clear()
    registry_resource_audit["final_live_entries"] = len(registry)
    _recheck_development_execution_identity(
        interpreters=interpreters,
        source_identity=authenticated_source,
    )
    report = build_development_report(
        runtime=runtime,
        inventory=inventory,
        search_result=result,
        bootstrap_terminal_kind=inventory.terminal_kind,
        registry_resource_audit=registry_resource_audit,
        source_identity=authenticated_source,
    )
    identity = runner.publish_canonical_json_noreplace(
        output_root / "development_direct_report.json",
        report,
    )
    return report, identity


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--development-direct", action="store_true")
    mode.add_argument("--formal-calibrate", action="store_true")
    mode.add_argument("--formal-heldout", action="store_true")
    mode.add_argument(
        "--development-child-request",
        type=Path,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--development-file-limit-bytes",
        type=int,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=(
            _REPOSITORY
            / "outputs/external_baselines/gcapeps_finite_memory_bond32_development"
        ),
    )
    parser.add_argument(
        "--fork-python-executable",
        "--python-executable",
        dest="fork_python_executable",
        type=Path,
        default=_DEFAULT_FORK_PYTHON,
    )
    parser.add_argument(
        "--sdim-python-executable",
        type=Path,
        default=_DEFAULT_SDIM_PYTHON,
    )
    parser.add_argument("--child-timeout-seconds", type=float, default=1800.0)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.development_child_request is not None:
        if args.development_file_limit_bytes is None:
            raise ValueError("development child requires a file-size limit")
        return _development_child(
            args.development_child_request.resolve(strict=True),
            file_limit_bytes=args.development_file_limit_bytes,
        )
    runtime = initialize_runtime()
    if args.development_direct:
        sys.stderr.write(
            "development-direct runs the full frozen adaptive calibration; "
            "it is nonformal and has no pair bound.\n"
        )
        interpreters = authenticate_direct_interpreters(
            fork_python=args.fork_python_executable,
            sdim_python=args.sdim_python_executable,
        )
        report, identity = run_development_direct(
            runtime=runtime,
            output_root=args.output_root.resolve(strict=False),
            interpreters=interpreters,
            timeout_seconds=args.child_timeout_seconds,
        )
        sys.stdout.write(
            json.dumps(
                {
                    "schema": report["schema"],
                    "formal_claim_eligible": False,
                    "report_path": identity.path,
                    "report_complete_file_sha256": identity.sha256,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        sys.stdout.write("\n")
        return 0
    raise RuntimeError(
        "formal execution is fail-closed until system-manager adapter "
        "authentication is supplied"
    )


if __name__ == "__main__":
    raise SystemExit(main())
