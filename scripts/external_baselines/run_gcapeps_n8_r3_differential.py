#!/usr/bin/env python3
"""Supervise the frozen GCAPEPS equal-status candidate differential."""

from __future__ import annotations

import argparse
import copy
import ctypes
from dataclasses import dataclass
import errno
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import re
import stat
import subprocess
import sys
import tempfile
import statistics
import time
import uuid
from typing import Any, Mapping, Sequence


RESULT_SCHEMA = (
    "error_coupling_simulator.external."
    "gcapeps_n8_r3_candidate_state_action_differential.v1"
)
WORKER_RESOURCE_ENVELOPE = {
    "MemoryMax": 8 * 1024**3,
    "MemorySwapMax": 0,
    "RuntimeMaxSec": 300,
    "TasksMax": 32,
}
EXPECTED_FIXTURE_SHA256 = (
    "a494512a74ed20b28c067734359e9a09ab3df72ad07467160855c3c475ed0b8d"
)
EXPECTED_FORK_ORIGIN = "https://github.com/cxMoonGlade/quimb.git"
EXPECTED_FORK_COMMIT = "6fbbf74cd36686ed30a4d8865697ce46e47056c1"
EXPECTED_FORK_TREE = "ffdfdf421fbe4d9674c2c88029710042fd18ae14"
EXPECTED_PYPROJECT_SHA256 = (
    "c8b48e06ee8595be41cc5dff6d4f8e768a9064d5a0f84efaec5ff12a7e8aa344"
)
EXPECTED_PIXI_LOCK_SHA256 = (
    "854da99b417c69dbdca4118c2545656470ad4e0f276a606b1b8c3082f795db35"
)
EXPECTED_PIXI_VERSION = "0.72.2"
EXPECTED_PIXI_SHA256 = (
    "2f301e44ac4caa9e137d505e5d0606fd029182d4df6f9e3add80bc077effea87"
)
EXPECTED_STIM_VERSION = "1.16.0"
EXPECTED_QUIMB_VERSION = "1.14.1.dev83+g6fbbf74cd"
EXPECTED_GENERATED_QUIMB_VERSION_SHA256 = (
    "abc0aa87777df73c9abba1945ec7772d62530324b3b47365fbd1a2c4f109a629"
)
EXPECTED_SYSTEMD_MAJOR = 255
MAIN_PIXI_ENVIRONMENT = "testpymid"
CONTROLS_SCHEMA = "error_coupling_simulator.external.gcapeps_n8_r3_controls_only.v1"
PLAIN_WORKER_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_n8_r3_plain_quimb_worker.v1"
)
GCAPEPS_WORKER_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_n8_r3_gcapeps_worker.v1"
)
_SCRIPT_PATH = Path(__file__).resolve()
_REPO_ROOT = _SCRIPT_PATH.parents[2]
_SCRIPT_DIR = _SCRIPT_PATH.parent
_EMITTER_PATH = _SCRIPT_DIR / "emit_gcapeps_n8_r3_fixture.py"
_ANCHOR_PATH = _SCRIPT_DIR / "gcapeps_n8_r3_dense_anchor.py"
_COMPARATOR_PATH = _SCRIPT_DIR / "compare_gcapeps_n8_r3_differential.py"
_PLAIN_WORKER_PATH = _SCRIPT_DIR / "plain_quimb_n8_r3_worker.py"
_GC_WORKER_PATH = _SCRIPT_DIR / "gcapeps_n8_r3_worker.py"
_SDIM_WORKER_PATH = _SCRIPT_DIR / "gcapeps_n8_r3_sdim_worker.py"
_CONTROLS_PATH = _SCRIPT_DIR / "run_gcapeps_n8_r3_controls.py"
DEFAULT_PIXI_EXECUTABLE = Path(
    "/home/cx/miniforge3/pkgs/pixi-0.72.2-ha759004_0/bin/pixi"
)
DEFAULT_FORK_SOURCE = _REPO_ROOT / "external/forks/quimb-gcapeps"
DEFAULT_SDIM_PYTHON = Path("/home/cx/miniforge3/envs/gcapeps-sdim/bin/python")
CLAIM_BEARING_PATHS = (
    _EMITTER_PATH,
    _ANCHOR_PATH,
    _COMPARATOR_PATH,
    _PLAIN_WORKER_PATH,
    _GC_WORKER_PATH,
    _SDIM_WORKER_PATH,
    _CONTROLS_PATH,
    _SCRIPT_PATH,
    _REPO_ROOT / "tests/test_external_gcapeps_n8_r3_differential.py",
    _REPO_ROOT / "docs/METRICS.md",
    _REPO_ROOT / "docs/NUMERICAL_PROVENANCE.md",
    _REPO_ROOT / "tests/CODEBOOK.md",
)


def warmup_launch_order() -> tuple[str, ...]:
    """Return the one discarded serial warmup per candidate."""

    return ("plain", "gcapeps")


def measured_launch_order() -> tuple[str, ...]:
    """Return the preregistered serial AB/BA order repeated three times."""

    return ("plain", "gcapeps", "gcapeps", "plain") * 3


def _validated_positive_integer_samples(
    values: Sequence[int],
    *,
    label: str,
) -> tuple[int, ...]:
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise ValueError(f"{label} must be a sequence")
    samples = tuple(values)
    if len(samples) != 6:
        raise ValueError(f"{label} must contain exactly six samples")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or value <= 0
        for value in samples
    ):
        raise ValueError(f"{label} samples must be strictly positive integers")
    return samples


def _median_and_mad(samples: Sequence[int]) -> dict[str, Any]:
    median = float(statistics.median(samples))
    deviations = tuple(abs(float(value) - median) for value in samples)
    mad = float(statistics.median(deviations))
    if not math.isfinite(median) or not math.isfinite(mad):
        raise ValueError("sample summary is nonfinite")
    return {
        "raw": list(samples),
        "median": median,
        "mad": mad,
    }


def summarize_efficiency_samples(
    *,
    plain_update_ns: Sequence[int],
    gcapeps_update_ns: Sequence[int],
    plain_peak_rss_bytes: Sequence[int],
    gcapeps_peak_rss_bytes: Sequence[int],
    interpretation_eligible: bool,
) -> dict[str, Any]:
    """Summarize raw samples while gating every interpreted ratio."""

    if not isinstance(interpretation_eligible, bool):
        raise ValueError("interpretation_eligible must be boolean")
    plain_update = _validated_positive_integer_samples(
        plain_update_ns,
        label="plain update time",
    )
    gcapeps_update = _validated_positive_integer_samples(
        gcapeps_update_ns,
        label="GCAPEPS update time",
    )
    plain_rss = _validated_positive_integer_samples(
        plain_peak_rss_bytes,
        label="plain peak RSS",
    )
    gcapeps_rss = _validated_positive_integer_samples(
        gcapeps_peak_rss_bytes,
        label="GCAPEPS peak RSS",
    )
    plain_update_summary = _median_and_mad(plain_update)
    gcapeps_update_summary = _median_and_mad(gcapeps_update)
    plain_rss_summary = _median_and_mad(plain_rss)
    gcapeps_rss_summary = _median_and_mad(gcapeps_rss)

    if interpretation_eligible:
        update_ratio = plain_update_summary["median"] / gcapeps_update_summary["median"]
        rss_ratio = plain_rss_summary["median"] / gcapeps_rss_summary["median"]
        directional = bool(update_ratio > 1.0)
    else:
        update_ratio = None
        rss_ratio = None
        directional = None
    return {
        "sample_count_per_lane": 6,
        "plain_update_ns": plain_update_summary,
        "gcapeps_update_ns": gcapeps_update_summary,
        "plain_peak_rss_bytes": plain_rss_summary,
        "gcapeps_peak_rss_bytes": gcapeps_rss_summary,
        "update_ratio_plain_over_gcapeps": update_ratio,
        "rss_ratio_plain_over_gcapeps": rss_ratio,
        "directional_hypothesis_plain_slower": directional,
        "directional_hypothesis_is_acceptance_gate": False,
        "interpretation_eligible": interpretation_eligible,
    }


_AT_FDCWD = -100
_RENAME_NOREPLACE = 1
_PUBLICATION_FIELDS = {
    "publication_status": "prepared_for_atomic_publication",
    "claims_offline_durability_confirmation": False,
    "target_filesystem_collision_probe_passed": True,
    "target_filesystem_noreplace_success_probe_passed": True,
    "artifact_file_fsync_success_attested_in_bundle": False,
    "staging_directory_fsync_success_attested_in_bundle": False,
    "final_staged_set_revalidation_success_attested_in_bundle": False,
    "rename_noreplace_success_attested_in_bundle": False,
    "parent_directory_fsync_success_attested_in_bundle": False,
    "published_destination_identity_recheck_success_attested_in_bundle": False,
    "successful_supervisor_return_is_only_publication_confirmation": True,
}


def _canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _renameat2_noreplace() -> Any:
    if platform.system() != "Linux":
        raise OSError(errno.ENOTSUP, "publication requires Linux renameat2")
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise OSError(errno.ENOTSUP, "renameat2 is unavailable")
    renameat2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    return renameat2


def _rename_directory_noreplace(
    source_name: str,
    destination_name: str,
    *,
    parent_fd: int,
) -> None:
    renameat2 = _renameat2_noreplace()
    result = renameat2(
        parent_fd,
        os.fsencode(source_name),
        parent_fd,
        os.fsencode(destination_name),
        _RENAME_NOREPLACE,
    )
    if result != 0:
        error_code = ctypes.get_errno()
        raise OSError(error_code, os.strerror(error_code), destination_name)


def _entry_identity(parent_fd: int, name: str) -> tuple[int, int, int]:
    stat_result = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    return (
        int(stat_result.st_dev),
        int(stat_result.st_ino),
        int(stat_result.st_mode),
    )


def _entry_exists(parent_fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def _probe_noreplace_filesystem(parent_fd: int) -> None:
    parent_proc = Path(f"/proc/self/fd/{parent_fd}")
    source_name: str | None = None
    destination_name: str | None = None
    try:
        source_name = Path(
            tempfile.mkdtemp(prefix=".gcapeps-probe-source-", dir=parent_proc)
        ).name
        destination_name = Path(
            tempfile.mkdtemp(prefix=".gcapeps-probe-destination-", dir=parent_proc)
        ).name
        source_identity = _entry_identity(parent_fd, source_name)
        destination_identity = _entry_identity(parent_fd, destination_name)
        try:
            _rename_directory_noreplace(
                source_name,
                destination_name,
                parent_fd=parent_fd,
            )
        except FileExistsError:
            pass
        else:
            raise OSError(
                errno.ENOTSUP,
                "target filesystem failed the collision-preservation probe",
            )
        if (
            _entry_identity(parent_fd, source_name) != source_identity
            or _entry_identity(parent_fd, destination_name) != destination_identity
        ):
            raise OSError(
                errno.ENOTSUP,
                "collision probe changed a directory identity",
            )
        os.rmdir(destination_name, dir_fd=parent_fd)
        _rename_directory_noreplace(
            source_name,
            destination_name,
            parent_fd=parent_fd,
        )
        if _entry_exists(parent_fd, source_name):
            raise OSError(errno.ENOTSUP, "successful rename left its source")
        if _entry_identity(parent_fd, destination_name) != source_identity:
            raise OSError(errno.ENOTSUP, "successful rename changed identity")
    finally:
        for name in (source_name, destination_name):
            if name is None:
                continue
            try:
                os.rmdir(name, dir_fd=parent_fd)
            except FileNotFoundError:
                pass


@dataclass
class PublicationPreflight:
    destination: Path
    parent: Path
    destination_name: str
    parent_fd: int
    parent_identity: tuple[int, int]
    collision_probe_passed: bool = True
    noreplace_success_probe_passed: bool = True
    _closed: bool = False

    def close(self) -> None:
        if not self._closed:
            os.close(self.parent_fd)
            self._closed = True

    def __enter__(self) -> "PublicationPreflight":
        if self._closed:
            raise RuntimeError("publication preflight is already closed")
        return self

    def __exit__(self, _type: Any, _value: Any, _traceback: Any) -> None:
        self.close()


def preflight_publication(destination: Path) -> PublicationPreflight:
    """Seal the target parent fd and exercise both no-replace outcomes."""

    lexical = Path(os.path.abspath(os.fspath(destination)))
    if lexical.name in {"", ".", ".."}:
        raise ValueError("publication destination must name one new directory")
    parent = lexical.parent
    parent_stat = os.stat(parent, follow_symlinks=False)
    if not parent.is_dir():
        raise FileNotFoundError(f"publication parent is not a directory: {parent}")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    parent_fd = os.open(parent, flags)
    try:
        opened_stat = os.fstat(parent_fd)
        identity = (int(opened_stat.st_dev), int(opened_stat.st_ino))
        if identity != (int(parent_stat.st_dev), int(parent_stat.st_ino)):
            raise RuntimeError("publication parent identity changed while opening")
        if _entry_exists(parent_fd, lexical.name):
            raise FileExistsError(f"refusing to replace publication: {lexical}")
        _probe_noreplace_filesystem(parent_fd)
        return PublicationPreflight(
            destination=lexical,
            parent=parent,
            destination_name=lexical.name,
            parent_fd=parent_fd,
            parent_identity=identity,
        )
    except BaseException:
        os.close(parent_fd)
        raise


def _validate_preflight(preflight: PublicationPreflight) -> None:
    if preflight._closed:
        raise RuntimeError("publication preflight is closed")
    descriptor_stat = os.fstat(preflight.parent_fd)
    descriptor_identity = (
        int(descriptor_stat.st_dev),
        int(descriptor_stat.st_ino),
    )
    if descriptor_identity != preflight.parent_identity:
        raise RuntimeError("sealed publication parent fd identity changed")
    path_stat = os.stat(preflight.parent, follow_symlinks=False)
    path_identity = (int(path_stat.st_dev), int(path_stat.st_ino))
    if path_identity != preflight.parent_identity:
        raise RuntimeError("publication parent path identity changed")
    if _entry_exists(preflight.parent_fd, preflight.destination_name):
        raise FileExistsError(
            f"refusing to replace publication: {preflight.destination}"
        )


def _validated_artifact_name(name: str) -> PurePosixPath:
    if not isinstance(name, str) or not name:
        raise ValueError("artifact name must be a nonempty string")
    relative = PurePosixPath(name)
    if (
        relative.is_absolute()
        or any(part in {"", ".", ".."} for part in relative.parts)
        or relative.name == "manifest.json"
    ):
        raise ValueError(f"invalid artifact name: {name!r}")
    return relative


def _write_stage_file(path: Path, payload: bytes) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short write while sealing publication artifact")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _regular_file_snapshot(root: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        stat_result = path.lstat()
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("publication stage contains a non-regular file")
        relative = path.relative_to(root).as_posix()
        payload = path.read_bytes()
        rows[relative] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
            "st_dev": int(stat_result.st_dev),
            "st_ino": int(stat_result.st_ino),
            "st_mode": int(stat_result.st_mode),
        }
    return rows


def _remove_private_stage(stage: Path, *, parent_fd: int) -> None:
    if not stage.name.startswith(".gcapeps-stage-"):
        raise RuntimeError("refusing to remove a non-private stage")
    if not _entry_exists(parent_fd, stage.name):
        return
    for root, directories, files in os.walk(stage, topdown=False):
        root_path = Path(root)
        for filename in files:
            (root_path / filename).unlink()
        for directory in directories:
            (root_path / directory).rmdir()
    os.rmdir(stage.name, dir_fd=parent_fd)


def publish_bundle_noreplace(
    preflight: PublicationPreflight,
    *,
    artifacts: dict[str, bytes],
    manifest_payload: dict[str, Any],
) -> dict[str, Any]:
    """Seal a complete stage, rename once, fsync, and confirm outside bytes."""

    _validate_preflight(preflight)
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("publication requires at least one artifact")
    normalized_artifacts: dict[str, bytes] = {}
    for name, payload in artifacts.items():
        relative = _validated_artifact_name(name)
        if not isinstance(payload, bytes):
            raise ValueError("publication artifact payloads must be bytes")
        normalized_artifacts[relative.as_posix()] = payload
    if not isinstance(manifest_payload, dict):
        raise ValueError("manifest payload must be an object")
    forbidden_manifest_keys = set(_PUBLICATION_FIELDS) | {"artifacts", "content_hash"}
    if forbidden_manifest_keys.intersection(manifest_payload):
        raise ValueError("manifest payload contains publisher-owned fields")

    parent_proc = Path(f"/proc/self/fd/{preflight.parent_fd}")
    stage = Path(tempfile.mkdtemp(prefix=".gcapeps-stage-", dir=parent_proc))
    stage_name = stage.name
    published = False
    try:
        artifact_rows: dict[str, dict[str, Any]] = {}
        for name in sorted(normalized_artifacts):
            payload = normalized_artifacts[name]
            _write_stage_file(stage / name, payload)
            artifact_rows[name] = {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
            }

        manifest = copy.deepcopy(manifest_payload)
        manifest.update(_PUBLICATION_FIELDS)
        manifest["artifacts"] = artifact_rows
        content_scope = copy.deepcopy(manifest)
        manifest["content_hash"] = hashlib.sha256(
            _canonical_json_bytes(content_scope)
        ).hexdigest()
        manifest_bytes = _canonical_json_bytes(manifest)
        _write_stage_file(stage / "manifest.json", manifest_bytes)

        stage_fd = os.open(stage, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            os.fsync(stage_fd)
        finally:
            os.close(stage_fd)
        expected_snapshot = _regular_file_snapshot(stage)
        expected_names = set(normalized_artifacts) | {"manifest.json"}
        if set(expected_snapshot) != expected_names:
            raise RuntimeError("publication stage exact file set drifted")
        stage_stat = stage.stat()
        stage_identity = (int(stage_stat.st_dev), int(stage_stat.st_ino))

        _validate_preflight(preflight)
        _rename_directory_noreplace(
            stage_name,
            preflight.destination_name,
            parent_fd=preflight.parent_fd,
        )
        published = True
        destination_identity = _entry_identity(
            preflight.parent_fd,
            preflight.destination_name,
        )[:2]
        if destination_identity != stage_identity:
            raise RuntimeError("published destination identity changed at rename")
        os.fsync(preflight.parent_fd)
        _validate_published_identity = _entry_identity(
            preflight.parent_fd,
            preflight.destination_name,
        )[:2]
        if _validate_published_identity != stage_identity:
            raise RuntimeError("published destination identity changed after fsync")
        published_root = parent_proc / preflight.destination_name
        observed_snapshot = _regular_file_snapshot(published_root)
        if observed_snapshot != expected_snapshot:
            raise RuntimeError("published artifact set differs from sealed stage")
        final_identity = _entry_identity(
            preflight.parent_fd,
            preflight.destination_name,
        )[:2]
        if final_identity != stage_identity:
            raise RuntimeError("published destination identity changed after recheck")
        return {
            "published_destination": str(preflight.destination),
            "rename_noreplace_success": True,
            "parent_directory_fsync_success": True,
            "published_destination_identity_recheck_success": True,
            "successful_supervisor_return_is_only_publication_confirmation": True,
        }
    finally:
        if not published:
            _remove_private_stage(stage, parent_fd=preflight.parent_fd)


_REMOVED_WORKER_ENVIRONMENT_NAMES = frozenset(
    {
        "PYTHONPATH",
        "PYTHONHOME",
        "VIRTUAL_ENV",
        "CUDA_HOME",
        "LD_LIBRARY_PATH",
        "NUMBA_CACHE_DIR",
    }
)
_SINGLE_THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "BLIS_NUM_THREADS": "1",
}


def build_worker_environment(
    base: Mapping[str, str],
    *,
    private_root: Path,
) -> dict[str, str]:
    """Build the isolated one-thread, CPU-only fresh-worker environment."""

    if not isinstance(base, Mapping):
        raise ValueError("base worker environment must be a mapping")
    root = Path(private_root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("private worker root must be an existing directory")
    environment: dict[str, str] = {}
    for name, value in base.items():
        if not isinstance(name, str) or not isinstance(value, str):
            raise ValueError("worker environment keys and values must be strings")
        if (
            name in _REMOVED_WORKER_ENVIRONMENT_NAMES
            or name.startswith("CONDA_")
            or name.startswith("_CE_")
        ):
            continue
        environment[name] = value

    cache = root / "cache"
    numba_cache = root / "numba-cache"
    temporary = root / "tmp"
    cache.mkdir(mode=0o700, exist_ok=False)
    numba_cache.mkdir(mode=0o700, exist_ok=False)
    temporary.mkdir(mode=0o700, exist_ok=False)
    environment.update(
        {
            "HOME": str(root),
            "XDG_CACHE_HOME": str(cache),
            "NUMBA_CACHE_DIR": str(numba_cache),
            "TMPDIR": str(temporary),
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
            "CUDA_VISIBLE_DEVICES": "",
            **_SINGLE_THREAD_ENVIRONMENT,
        }
    )
    return environment


def build_systemd_worker_command(
    *,
    unit_name: str,
    cpu_id: int,
    worker_command: Sequence[str],
    worker_environment: Mapping[str, str] | None = None,
    working_directory: Path | None = None,
) -> list[str]:
    """Wrap one fresh child in the frozen systemd-v255 resource envelope."""

    if not isinstance(unit_name, str) or not re.fullmatch(
        r"[A-Za-z0-9_.@-]{1,128}", unit_name
    ):
        raise ValueError("systemd unit name is invalid")
    if not isinstance(cpu_id, int) or isinstance(cpu_id, bool) or cpu_id < 0:
        raise ValueError("CPU id must be a nonnegative integer")
    command = tuple(worker_command)
    if not command or any(not isinstance(item, str) or not item for item in command):
        raise ValueError("worker command must contain nonempty strings")
    properties = (
        "MemoryAccounting=yes",
        f"MemoryMax={WORKER_RESOURCE_ENVELOPE['MemoryMax']}",
        f"MemorySwapMax={WORKER_RESOURCE_ENVELOPE['MemorySwapMax']}",
        f"RuntimeMaxSec={WORKER_RESOURCE_ENVELOPE['RuntimeMaxSec']}",
        f"TasksMax={WORKER_RESOURCE_ENVELOPE['TasksMax']}",
        f"CPUAffinity={cpu_id}",
        (
            "UnsetEnvironment=PYTHONPATH PYTHONHOME VIRTUAL_ENV "
            "CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_SHLVL _CE_CONDA "
            "_CE_M LD_LIBRARY_PATH CUDA_HOME"
        ),
    )
    wrapped = [
        "systemd-run",
        "--user",
        "--wait",
        "--pipe",
        "--service-type=exec",
        "--collect",
        f"--unit={unit_name}",
    ]
    for value in properties:
        wrapped.extend(("--property", value))
    if working_directory is not None:
        lexical_workdir = working_directory.absolute()
        resolved_workdir = lexical_workdir.resolve(strict=True)
        if lexical_workdir != resolved_workdir or not resolved_workdir.is_dir():
            raise ValueError("worker working directory must be a nonsymlink directory")
        wrapped.append(f"--working-directory={resolved_workdir}")
    if worker_environment is not None:
        for name, value in sorted(worker_environment.items()):
            if (
                not isinstance(name, str)
                or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is None
                or not isinstance(value, str)
                or "\x00" in value
                or "\n" in value
            ):
                raise ValueError("worker environment contains an invalid entry")
            wrapped.append(f"--setenv={name}={value}")
    wrapped.append("--")
    wrapped.extend(command)
    return wrapped


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.resolve(strict=True).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _reject_duplicate_pairs(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON token is forbidden: {value}")


def _load_strict_json(path: Path, *, canonical: bool = False) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    raw = resolved.read_bytes()
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid strict JSON artifact: {resolved}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON artifact must contain one object: {resolved}")
    if canonical and raw != _canonical_json_bytes(value):
        raise ValueError(f"JSON artifact is not canonical: {resolved}")
    return value


def _load_script(path: Path, module_name: str) -> Any:
    source = path.resolve(strict=True)
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load script module: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _git_value(checkout: Path, *arguments: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(checkout), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    value = process.stdout.strip()
    if not value or "\n" in value:
        raise RuntimeError("Git identity command did not return one scalar")
    return value


def _git_status(checkout: Path, *, include_ignored: bool) -> str:
    command = [
        "git",
        "-C",
        str(checkout),
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    ]
    if include_ignored:
        command.append("--ignored")
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def claim_bearing_source_hashes() -> dict[str, str]:
    return {
        path.resolve(strict=True).relative_to(_REPO_ROOT).as_posix(): _sha256_file(path)
        for path in CLAIM_BEARING_PATHS
    }


def verify_committed_parent_checkout(repo_root: Path = _REPO_ROOT) -> dict[str, Any]:
    """Require the target supervisor and every owner to be committed and clean."""

    lexical = repo_root.absolute()
    root = lexical.resolve(strict=True)
    if lexical != root or not root.is_dir():
        raise RuntimeError("parent checkout must be a nonsymlink directory")
    top = Path(_git_value(root, "rev-parse", "--show-toplevel")).resolve(strict=True)
    if top != root:
        raise RuntimeError("parent checkout root is not its Git top level")
    if _git_status(root, include_ignored=False):
        raise RuntimeError("parent checkout must be clean before controls or target")
    relative_paths = [
        path.resolve(strict=True).relative_to(root).as_posix()
        for path in CLAIM_BEARING_PATHS
    ]
    subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", *relative_paths],
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        "root": str(root),
        "commit": _git_value(root, "rev-parse", "HEAD^{commit}"),
        "tree": _git_value(root, "rev-parse", "HEAD^{tree}"),
        "clean_including_untracked": True,
        "claim_bearing_source_sha256": claim_bearing_source_hashes(),
    }


def verify_frozen_fork_checkout(checkout: Path) -> dict[str, Any]:
    lexical = checkout.absolute()
    root = lexical.resolve(strict=True)
    if lexical != root or not root.is_dir():
        raise RuntimeError("fork checkout must be a nonsymlink directory")
    top = Path(_git_value(root, "rev-parse", "--show-toplevel")).resolve(strict=True)
    commit = _git_value(root, "rev-parse", "HEAD^{commit}")
    tree = _git_value(root, "rev-parse", "HEAD^{tree}")
    origin = _git_value(root, "remote", "get-url", "origin")
    if (
        top != root
        or commit != EXPECTED_FORK_COMMIT
        or tree != EXPECTED_FORK_TREE
        or origin != EXPECTED_FORK_ORIGIN
    ):
        raise RuntimeError("fresh fork identity drifted")
    if _git_status(root, include_ignored=True):
        raise RuntimeError("fresh fork is not ignored-inclusive pristine")
    pyproject = root / "pyproject.toml"
    pixi_lock = root / "pixi.lock"
    if _sha256_file(pyproject) != EXPECTED_PYPROJECT_SHA256:
        raise RuntimeError("fresh fork pyproject.toml hash drifted")
    if _sha256_file(pixi_lock) != EXPECTED_PIXI_LOCK_SHA256:
        raise RuntimeError("fresh fork pixi.lock hash drifted")
    return {
        "path": str(root),
        "origin": origin,
        "commit": commit,
        "tree": tree,
        "pyproject_sha256": EXPECTED_PYPROJECT_SHA256,
        "pixi_lock_sha256": EXPECTED_PIXI_LOCK_SHA256,
        "ignored_inclusive_pristine": True,
    }


def materialize_fresh_fork(source: Path, destination: Path) -> dict[str, Any]:
    """Clone the frozen local fork without mutating or cleaning the source."""

    source_lexical = source.absolute()
    source_root = source.resolve(strict=True)
    if source_lexical != source_root or not source_root.is_dir():
        raise ValueError("fork source must be a nonsymlink directory")
    source_top = Path(
        _git_value(source_root, "rev-parse", "--show-toplevel")
    ).resolve(strict=True)
    source_commit = _git_value(source_root, "rev-parse", "HEAD^{commit}")
    source_tree = _git_value(source_root, "rev-parse", "HEAD^{tree}")
    source_origin = _git_value(source_root, "remote", "get-url", "origin")
    if (
        source_top != source_root
        or source_commit != EXPECTED_FORK_COMMIT
        or source_tree != EXPECTED_FORK_TREE
        or source_origin != EXPECTED_FORK_ORIGIN
        or _sha256_file(source_root / "pyproject.toml")
        != EXPECTED_PYPROJECT_SHA256
        or _sha256_file(source_root / "pixi.lock") != EXPECTED_PIXI_LOCK_SHA256
    ):
        raise RuntimeError("development fork does not contain the frozen head")
    if _git_status(source_root, include_ignored=False):
        raise RuntimeError("development fork has tracked or untracked changes")
    target = destination.absolute()
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"fresh fork destination already exists: {target}")
    subprocess.run(
        [
            "git",
            "clone",
            "--no-local",
            "--no-hardlinks",
            "--no-checkout",
            "--quiet",
            str(source_root),
            str(target),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(target),
            "checkout",
            "--detach",
            "--quiet",
            EXPECTED_FORK_COMMIT,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(target), "remote", "set-url", "origin", EXPECTED_FORK_ORIGIN],
        check=True,
        capture_output=True,
        text=True,
    )
    return verify_frozen_fork_checkout(target)


def _bundle_artifacts(root: Path) -> dict[str, bytes]:
    artifacts: dict[str, bytes] = {}
    resolved = root.resolve(strict=True)
    for path in sorted(resolved.rglob("*")):
        if path.is_dir():
            continue
        if path.is_symlink() or not path.is_file():
            raise RuntimeError("private artifact tree contains a non-regular file")
        artifacts[path.relative_to(resolved).as_posix()] = path.read_bytes()
    return artifacts


def load_published_bundle(root: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    """Validate exact artifact bytes and the publisher-owned manifest hash."""

    lexical = root.absolute()
    resolved = lexical.resolve(strict=True)
    if lexical != resolved or not resolved.is_dir():
        raise RuntimeError("published bundle must be a nonsymlink directory")
    manifest_path = resolved / "manifest.json"
    manifest = _load_strict_json(manifest_path, canonical=True)
    artifacts = _bundle_artifacts(resolved)
    manifest_bytes = artifacts.pop("manifest.json", None)
    if manifest_bytes is None:
        raise ValueError("published bundle has no manifest")
    rows = manifest.get("artifacts")
    if not isinstance(rows, dict) or set(rows) != set(artifacts):
        raise ValueError("published bundle artifact set drifted")
    for name, payload in artifacts.items():
        row = rows[name]
        if not isinstance(row, dict) or row != {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
        }:
            raise ValueError(f"published artifact identity drifted: {name}")
    content_hash = manifest.get("content_hash")
    content_scope = copy.deepcopy(manifest)
    content_scope.pop("content_hash", None)
    if content_hash != hashlib.sha256(_canonical_json_bytes(content_scope)).hexdigest():
        raise ValueError("published manifest content hash drifted")
    for name, expected in _PUBLICATION_FIELDS.items():
        if manifest.get(name) != expected:
            raise ValueError(f"published manifest field drifted: {name}")
    return manifest, artifacts


def validate_controls_bundle(root: Path) -> dict[str, Any]:
    manifest, artifacts = load_published_bundle(root)
    required = {
        "fixture.json",
        "controls.json",
        "orientation.json",
        "gc-construction.json",
        "sdim-normal.json",
        "sdim-flip.json",
    }
    if not required.issubset(artifacts):
        raise ValueError("controls bundle is missing required evidence")
    if hashlib.sha256(artifacts["fixture.json"]).hexdigest() != EXPECTED_FIXTURE_SHA256:
        raise ValueError("controls fixture bytes drifted")
    controls_path = root.resolve(strict=True) / "controls.json"
    controls = _load_strict_json(controls_path, canonical=True)
    body = dict(controls)
    observed_content_hash = body.pop("content_sha256", None)
    if observed_content_hash != hashlib.sha256(_canonical_json_bytes(body)).hexdigest():
        raise ValueError("controls report content hash drifted")
    if (
        controls.get("schema") != CONTROLS_SCHEMA
        or controls.get("report_role") != "supervisor_private_controls_only"
        or controls.get("controls_passed") is not True
        or controls.get("controls_gate_passed_for_later_preflights") is not True
        or controls.get("target_execution_authorized_by_this_report_alone") is not False
        or controls.get("external_evidence_all_supplied_and_passed") is not True
    ):
        raise ValueError("controls report did not pass")
    external = controls.get("external_evidence")
    required_external = {
        "one_site_quimb_orientation",
        "gc_construction_pytests",
        "sdim_normal_and_first_sign_flip",
    }
    if (
        not isinstance(external, Mapping)
        or set(external) != required_external
        or any(
            not isinstance(external[name], Mapping)
            or external[name].get("status") != "PASS"
            or external[name].get("passed") is not True
            for name in required_external
        )
    ):
        raise ValueError("controls external evidence binding drifted")
    scope = controls.get("execution_scope")
    if (
        not isinstance(scope, Mapping)
        or scope.get("clean_plain_n8_candidate_executed") is not False
        or scope.get("clean_gcapeps_n8_candidate_executed") is not False
        or scope.get("anchor_enters_timing_or_rss") is not False
        or scope.get("sdim_enters_timing_or_rss") is not False
    ):
        raise ValueError("controls execution scope drifted")
    sources = controls.get("source_sha256")
    expected_sources = {
        "fixture_emitter": _sha256_file(_EMITTER_PATH),
        "numpy_anchor": _sha256_file(_ANCHOR_PATH),
        "complete_vector_comparator": _sha256_file(_COMPARATOR_PATH),
        "plain_quimb_worker": _sha256_file(_PLAIN_WORKER_PATH),
        "gcapeps_worker": _sha256_file(_GC_WORKER_PATH),
        "sdim_worker": _sha256_file(_SDIM_WORKER_PATH),
        "controls_runner": _sha256_file(_CONTROLS_PATH),
    }
    if sources != expected_sources:
        raise ValueError("controls report source binding drifted")
    if (
        manifest.get("schema") != CONTROLS_SCHEMA
        or manifest.get("status") != "PASS"
        or manifest.get("controls_passed") is not True
        or manifest.get("clean_n8_plain_candidate_executed") is not False
        or manifest.get("clean_n8_gcapeps_candidate_executed") is not False
        or manifest.get("fixture_sha256") != EXPECTED_FIXTURE_SHA256
        or manifest.get("fork_commit") != EXPECTED_FORK_COMMIT
    ):
        raise ValueError("controls bundle manifest binding drifted")
    return {
        "root": str(root.resolve(strict=True)),
        "manifest": manifest,
        "controls": controls,
        "artifacts": artifacts,
        "bundle_artifact_sha256": {
            name: hashlib.sha256(payload).hexdigest()
            for name, payload in artifacts.items()
        },
        "passed": True,
    }


def _run_captured(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    environment: Mapping[str, str] | None = None,
    timeout_seconds: int = 600,
    require_success: bool = True,
) -> dict[str, Any]:
    if not command or any(not isinstance(item, str) or not item for item in command):
        raise ValueError("captured command must contain nonempty strings")
    started = time.perf_counter_ns()
    process = subprocess.run(
        list(command),
        cwd=None if cwd is None else str(cwd),
        env=None if environment is None else dict(environment),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    elapsed = time.perf_counter_ns() - started
    record = {
        "command": list(command),
        "cwd": None if cwd is None else str(cwd.resolve(strict=True)),
        "returncode": int(process.returncode),
        "launch_and_process_elapsed_ns": int(elapsed),
        "stdout": process.stdout,
        "stderr": process.stderr,
        "stdout_sha256": hashlib.sha256(process.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(process.stderr.encode()).hexdigest(),
    }
    if require_success and process.returncode != 0:
        raise RuntimeError(
            "captured command failed: "
            + " ".join(command)
            + f"\nstdout:\n{process.stdout}\nstderr:\n{process.stderr}"
        )
    return record


def verify_pixi_executable(pixi_executable: Path) -> dict[str, Any]:
    lexical = pixi_executable.absolute()
    resolved = lexical.resolve(strict=True)
    if (
        lexical != resolved
        or not resolved.is_file()
        or not os.access(resolved, os.X_OK)
    ):
        raise RuntimeError("Pixi executable must be one executable nonsymlink file")
    digest = _sha256_file(resolved)
    if digest != EXPECTED_PIXI_SHA256:
        raise RuntimeError("Pixi executable SHA-256 drifted")
    record = _run_captured([str(resolved), "--version"], timeout_seconds=30)
    match = re.search(r"\b(\d+\.\d+\.\d+)\b", record["stdout"] + record["stderr"])
    if match is None or match.group(1) != EXPECTED_PIXI_VERSION:
        raise RuntimeError("Pixi version drifted")
    return {
        "path": str(resolved),
        "sha256": digest,
        "version": EXPECTED_PIXI_VERSION,
        "version_command": record,
    }


def _write_exclusive_file(path: Path, payload: bytes, *, mode: int = 0o600) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, mode)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short write")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _private_subdirectory(parent: Path, name: str) -> Path:
    if re.fullmatch(r"[A-Za-z0-9_.-]+", name) is None or name in {".", ".."}:
        raise ValueError("invalid private directory name")
    path = parent / name
    os.mkdir(path, mode=0o700)
    return path.resolve(strict=True)


def _provision_environment_variables(private_root: Path) -> dict[str, str]:
    home = _private_subdirectory(private_root, "pixi-home")
    cache = _private_subdirectory(private_root, "pixi-cache")
    numba_cache = _private_subdirectory(private_root, "numba-cache")
    temporary = _private_subdirectory(private_root, "pixi-tmp")
    environment: dict[str, str] = {}
    for name, value in os.environ.items():
        if (
            name in _REMOVED_WORKER_ENVIRONMENT_NAMES
            or name.startswith("CONDA_")
            or name.startswith("_CE_")
        ):
            continue
        environment[name] = value
    environment.update(
        {
            "HOME": str(home),
            "XDG_CACHE_HOME": str(cache),
            "PIXI_HOME": str(home),
            "PIXI_CACHE_DIR": str(cache),
            "RATTLER_CACHE_DIR": str(cache / "rattler"),
            "NUMBA_CACHE_DIR": str(numba_cache),
            "TMPDIR": str(temporary),
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
            "CUDA_VISIBLE_DEVICES": "",
            **_SINGLE_THREAD_ENVIRONMENT,
        }
    )
    return environment


def _remove_expected_pixi_project_residue(
    *,
    fork_checkout: Path,
    detached_prefix: Path,
) -> dict[str, Any]:
    """Remove only the two deterministic ignored files Pixi just generated."""

    checkout = fork_checkout.resolve(strict=True)
    prefix = detached_prefix.resolve(strict=True)
    pixi_directory = checkout / ".pixi"
    pixi_info = pixi_directory.lstat()
    if pixi_directory.is_symlink() or not stat.S_ISDIR(pixi_info.st_mode):
        raise RuntimeError("Pixi project residue is not one real directory")
    entries = sorted(path.name for path in pixi_directory.iterdir())
    if entries != ["envs"]:
        raise RuntimeError("Pixi project residue contains unexpected entries")
    environments_link = pixi_directory / "envs"
    if not stat.S_ISLNK(environments_link.lstat().st_mode):
        raise RuntimeError("Pixi detached environments marker is not a symlink")
    resolved_environments = environments_link.resolve(strict=True)
    if resolved_environments != prefix.parent:
        raise RuntimeError("Pixi detached environments marker target drifted")

    generated_version = checkout / "quimb" / "_version.py"
    version_info = generated_version.lstat()
    if (
        generated_version.is_symlink()
        or not stat.S_ISREG(version_info.st_mode)
        or _sha256_file(generated_version)
        != EXPECTED_GENERATED_QUIMB_VERSION_SHA256
    ):
        raise RuntimeError("generated Quimb version file drifted")
    tracked = _run_captured(
        [
            "git",
            "-C",
            str(checkout),
            "ls-files",
            "--",
            ".pixi",
            "quimb/_version.py",
        ],
        timeout_seconds=30,
    )
    if tracked["stdout"].strip():
        raise RuntimeError("refusing to remove a tracked Pixi project path")

    generated_version.unlink()
    environments_link.unlink()
    pixi_directory.rmdir()
    return {
        "removed_generated_paths": [".pixi/envs", "quimb/_version.py"],
        "generated_version_sha256": EXPECTED_GENERATED_QUIMB_VERSION_SHA256,
        "detached_environments_target": str(resolved_environments),
        "tracked_path_check": tracked,
        "fork_pristine_cleanup_is_exact": True,
    }


def provision_locked_main_environment(
    *,
    pixi_executable: Path,
    fork_checkout: Path,
    private_root: Path,
) -> dict[str, Any]:
    """Install testpymid from the frozen lock into an external detached prefix."""

    pixi = verify_pixi_executable(pixi_executable)
    fork_before = verify_frozen_fork_checkout(fork_checkout)
    root = private_root.resolve(strict=True)
    detached = _private_subdirectory(root, "detached-environments")
    environment = _provision_environment_variables(root)
    config_path = root / "pixi-config.toml"
    config_bytes = f'detached-environments = "{detached}"\n'.encode("utf-8")
    _write_exclusive_file(config_path, config_bytes)
    environment["PIXI_CONFIG_FILE"] = str(config_path)
    install_command = [
        pixi["path"],
        "install",
        "--manifest-path",
        str(fork_checkout / "pyproject.toml"),
        "--environment",
        MAIN_PIXI_ENVIRONMENT,
        "--locked",
        "--frozen",
        "--config-file",
        str(config_path),
        "--color",
        "never",
        "--no-progress",
    ]
    install = _run_captured(
        install_command,
        cwd=fork_checkout,
        environment=environment,
        timeout_seconds=1800,
    )
    info = _run_captured(
        [
            pixi["path"],
            "info",
            "--json",
            "--manifest-path",
            str(fork_checkout / "pyproject.toml"),
            "--config-file",
            str(config_path),
        ],
        cwd=fork_checkout,
        environment=environment,
        timeout_seconds=120,
    )
    try:
        info_payload = json.loads(
            info["stdout"],
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_json_constant,
        )
    except json.JSONDecodeError as exc:
        raise RuntimeError("Pixi info did not emit JSON") from exc
    rows = [
        row
        for row in info_payload.get("environments_info", [])
        if row.get("name") == MAIN_PIXI_ENVIRONMENT
    ]
    if len(rows) != 1:
        raise RuntimeError("Pixi testpymid prefix is ambiguous")
    prefix = Path(rows[0]["prefix"]).resolve(strict=True)
    if not prefix.is_dir() or not prefix.is_relative_to(detached):
        raise RuntimeError("Pixi environment prefix escaped detached-environments")
    python_executable = (prefix / "bin" / "python").resolve(strict=True)
    if not python_executable.is_file():
        raise RuntimeError("detached Pixi environment has no Python")
    pixi_project_cleanup = _remove_expected_pixi_project_residue(
        fork_checkout=fork_checkout,
        detached_prefix=prefix,
    )
    runtime_check = _run_captured(
        [
            str(python_executable),
            "-s",
            "-B",
            "-c",
            (
                "import json,pathlib,platform,quimb,stim;"
                "print(json.dumps({'python':platform.python_version(),"
                "'stim':stim.__version__,'quimb':quimb.__version__,"
                "'quimb_file':str(pathlib.Path(quimb.__file__).resolve())},"
                "sort_keys=True))"
            ),
        ],
        cwd=fork_checkout,
        environment=environment,
        timeout_seconds=120,
    )
    runtime = json.loads(runtime_check["stdout"])
    if (
        not str(runtime["python"]).startswith("3.13.")
        or runtime["stim"] != EXPECTED_STIM_VERSION
        or runtime["quimb"] != EXPECTED_QUIMB_VERSION
        or Path(runtime["quimb_file"]).resolve(strict=True)
        != (fork_checkout / "quimb" / "__init__.py").resolve(strict=True)
    ):
        raise RuntimeError("main Pixi Python/Stim/Quimb identity drifted")
    fork_after = verify_frozen_fork_checkout(fork_checkout)
    if fork_after != fork_before:
        raise RuntimeError("fork changed while provisioning detached environment")
    return {
        "pixi": pixi,
        "configuration": {
            "path": str(config_path),
            "sha256": hashlib.sha256(config_bytes).hexdigest(),
            "detached_environments": str(detached),
            "outside_fork_checkout": not detached.is_relative_to(fork_checkout),
        },
        "environment_name": MAIN_PIXI_ENVIRONMENT,
        "prefix": str(prefix),
        "python_executable": str(python_executable),
        "install_lock_semantics": "--locked_--frozen_then_direct_execution_without_pixi_mutation",
        "install_command": install,
        "info_command": info,
        "runtime_check": runtime_check,
        "runtime": runtime,
        "pixi_project_cleanup": pixi_project_cleanup,
        "fork_pristine_before_and_after": True,
    }


def preflight_systemd_resource_envelope(*, private_root: Path) -> dict[str, Any]:
    version = _run_captured(["systemd-run", "--version"], timeout_seconds=30)
    first_line = (version["stdout"] or version["stderr"]).splitlines()[0]
    match = re.search(r"systemd\s+(\d+)", first_line)
    if match is None or int(match.group(1)) != EXPECTED_SYSTEMD_MAJOR:
        raise RuntimeError("systemd major version drifted")
    controllers = Path("/sys/fs/cgroup/cgroup.controllers")
    if not controllers.is_file():
        raise RuntimeError("cgroup v2 unified controllers are unavailable")
    controller_names = controllers.read_text(encoding="ascii").split()
    if "memory" not in controller_names or "cpu" not in controller_names:
        raise RuntimeError("required cgroup v2 controllers are unavailable")
    allowed = sorted(int(cpu) for cpu in os.sched_getaffinity(0))
    if not allowed:
        raise RuntimeError("supervisor has no allowed CPU")
    cpu_id = allowed[0]
    probe_root = _private_subdirectory(
        private_root.resolve(strict=True), "systemd-probe"
    )
    environment = build_worker_environment(
        {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
        private_root=probe_root,
    )
    unit_name = f"gcapeps-preflight-{uuid.uuid4().hex}"
    command = build_systemd_worker_command(
        unit_name=unit_name,
        cpu_id=cpu_id,
        worker_command=["/bin/true"],
        worker_environment=environment,
        working_directory=private_root,
    )
    probe = _run_captured(
        command,
        environment=environment,
        timeout_seconds=60,
    )
    return {
        "systemd_major": EXPECTED_SYSTEMD_MAJOR,
        "systemd_version_command": version,
        "cgroup_version": 2,
        "controllers": sorted(controller_names),
        "allowed_cpu_affinity": allowed,
        "selected_lowest_cpu": cpu_id,
        "resource_envelope": dict(WORKER_RESOURCE_ENVELOPE),
        "probe_unit": unit_name,
        "probe_command": probe,
        "passed": True,
    }


def _worker_environment_for_prefix(prefix: Path, private_root: Path) -> dict[str, str]:
    base = {
        "PATH": f"{prefix / 'bin'}:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    for name in ("XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"):
        value = os.environ.get(name)
        if value is not None:
            base[name] = value
    return build_worker_environment(base, private_root=private_root)


def run_candidate_worker(
    *,
    lane: str,
    sample_kind: str,
    sample_index: int,
    fixture_path: Path,
    fork_checkout: Path,
    python_executable: Path,
    cpu_id: int,
    runtime_parent: Path,
) -> dict[str, Any]:
    """Launch one fully fresh candidate process and retain its private output."""

    if lane not in {"plain", "gcapeps"}:
        raise ValueError("candidate lane must be plain or gcapeps")
    if sample_kind not in {"warmup", "measured"}:
        raise ValueError("candidate sample kind drifted")
    if (
        not isinstance(sample_index, int)
        or isinstance(sample_index, bool)
        or sample_index < 0
    ):
        raise ValueError("candidate sample index must be nonnegative")
    token = f"{sample_kind}-{sample_index:02d}-{lane}-{uuid.uuid4().hex}"
    private_root = _private_subdirectory(runtime_parent, token)
    environment = _worker_environment_for_prefix(
        python_executable.resolve(strict=True).parent.parent,
        private_root,
    )
    output_directory = _private_subdirectory(private_root, "output")
    if lane == "plain":
        script = _PLAIN_WORKER_PATH
    else:
        script = _GC_WORKER_PATH
    worker_command = [
        str(python_executable.resolve(strict=True)),
        "-s",
        "-B",
        str(script.resolve(strict=True)),
        "--fixture",
        str(fixture_path.resolve(strict=True)),
        "--fork-checkout",
        str(fork_checkout.resolve(strict=True)),
        "--output-directory",
        str(output_directory),
        "--sample-kind",
        sample_kind,
        "--sample-index",
        str(sample_index),
    ]
    unit_name = (
        f"gcapeps-{sample_kind}-{sample_index:02d}-{lane}-{uuid.uuid4().hex[:12]}"
    )
    systemd_command = build_systemd_worker_command(
        unit_name=unit_name,
        cpu_id=cpu_id,
        worker_command=worker_command,
        worker_environment=environment,
        working_directory=fork_checkout,
    )
    process = _run_captured(
        systemd_command,
        cwd=fork_checkout,
        environment=environment,
        timeout_seconds=WORKER_RESOURCE_ENVELOPE["RuntimeMaxSec"] + 30,
        require_success=False,
    )
    process["unit_name"] = unit_name
    process["lane"] = lane
    process["sample_kind"] = sample_kind
    process["sample_index"] = sample_index
    process["private_output_directory"] = str(output_directory)
    if process["returncode"] != 0:
        raise RuntimeError(
            f"{lane} {sample_kind} sample {sample_index} failed under systemd: "
            f"{process['stderr']}"
        )
    summary_name = "plain_worker.json" if lane == "plain" else "gcapeps_worker.json"
    summary_path = output_directory / summary_name
    if not summary_path.is_file():
        raise RuntimeError("candidate worker returned without its sealed summary")
    return {
        "lane": lane,
        "sample_kind": sample_kind,
        "sample_index": sample_index,
        "private_root": str(private_root),
        "output_directory": str(output_directory),
        "summary_path": str(summary_path.resolve(strict=True)),
        "process": process,
    }


def run_anchor_worker(
    *,
    fixture_path: Path,
    python_executable: Path,
    runtime_parent: Path,
) -> dict[str, Any]:
    """Run the untimed NumPy-only anchor after all candidate outputs are sealed."""

    private_root = _private_subdirectory(runtime_parent, f"anchor-{uuid.uuid4().hex}")
    output_directory = _private_subdirectory(private_root, "output")
    environment = _worker_environment_for_prefix(
        python_executable.resolve(strict=True).parent.parent,
        private_root,
    )
    command = [
        str(python_executable.resolve(strict=True)),
        "-I",
        "-B",
        str(_ANCHOR_PATH.resolve(strict=True)),
        "--fixture",
        str(fixture_path.resolve(strict=True)),
        "--output-directory",
        str(output_directory),
    ]
    process = _run_captured(
        command,
        environment=environment,
        timeout_seconds=120,
    )
    report_path = output_directory / "anchor_report.json"
    if not report_path.is_file():
        raise RuntimeError("anchor worker returned without its report")
    return {
        "private_root": str(private_root),
        "output_directory": str(output_directory),
        "report_path": str(report_path.resolve(strict=True)),
        "process": process,
        "enters_timing_or_rss_ratio": False,
    }


def _runpy_bootstrap(script: Path) -> str:
    return (
        "import runpy;"
        f"runpy.run_path({str(script.resolve(strict=True))!r},run_name='__main__')"
    )


def run_sdim_control_worker(
    *,
    flip_first_sign: bool,
    fixture_path: Path,
    fork_checkout: Path,
    sdim_python: Path,
    cpu_id: int,
    runtime_parent: Path,
) -> dict[str, Any]:
    """Run one SDIM frame-only control with the fresh fork first on sys.path."""

    label = "sdim-flip" if flip_first_sign else "sdim-normal"
    private_root = _private_subdirectory(runtime_parent, f"{label}-{uuid.uuid4().hex}")
    environment = _worker_environment_for_prefix(
        sdim_python.resolve(strict=True).parent.parent,
        private_root,
    )
    output_json = private_root / f"{label}.json"
    worker_command = [
        str(sdim_python.resolve(strict=True)),
        "-s",
        "-B",
        "-c",
        _runpy_bootstrap(_SDIM_WORKER_PATH),
        "--fixture-json",
        str(fixture_path.resolve(strict=True)),
        "--output-json",
        str(output_json),
        "--fork-checkout",
        str(fork_checkout.resolve(strict=True)),
        "--expected-fork-commit",
        EXPECTED_FORK_COMMIT,
        "--expected-fork-tree",
        EXPECTED_FORK_TREE,
        "--environment-yaml",
        str((fork_checkout / "environment-gcapeps-sdim.yml").resolve(strict=True)),
    ]
    if flip_first_sign:
        worker_command.append("--flip-first-sign-control")
    unit_name = f"gcapeps-{label}-{uuid.uuid4().hex[:12]}"
    systemd_command = build_systemd_worker_command(
        unit_name=unit_name,
        cpu_id=cpu_id,
        worker_command=worker_command,
        worker_environment=environment,
        working_directory=fork_checkout,
    )
    process = _run_captured(
        systemd_command,
        cwd=fork_checkout,
        environment=environment,
        timeout_seconds=120,
        require_success=False,
    )
    expected_returncode = 0
    if process["returncode"] != expected_returncode or not output_json.is_file():
        raise RuntimeError(f"{label} worker failed: {process['stderr']}")
    return {
        "label": label,
        "output_json": str(output_json.resolve(strict=True)),
        "process": process,
        "enters_timing_or_rss_ratio": False,
    }


def _load_exact_c128_vector(path: Path, *, expected_content_hash: str) -> Any:
    import numpy as np

    resolved = path.resolve(strict=True)
    array = np.load(resolved, allow_pickle=False)
    if (
        not isinstance(array, np.ndarray)
        or array.shape != (256,)
        or array.dtype != np.dtype("complex128")
        or not array.flags.c_contiguous
        or not np.all(np.isfinite(array))
    ):
        raise ValueError(
            f"candidate vector artifact is not exact c128[256]: {resolved}"
        )
    content_hash = hashlib.sha256(
        np.ascontiguousarray(array, dtype="<c16").tobytes(order="C")
    ).hexdigest()
    if content_hash != expected_content_hash:
        raise ValueError(f"candidate vector content hash drifted: {resolved}")
    return array


def _validate_common_worker_envelope(
    report: Mapping[str, Any],
    *,
    cpu_id: int,
    private_root: Path,
) -> None:
    envelope = report.get("process_envelope")
    expected_numba_cache = (
        private_root.resolve(strict=True) / "numba-cache"
    ).resolve(strict=True)
    numba_cache_raw = (
        envelope.get("numba_cache_directory")
        if isinstance(envelope, Mapping)
        else None
    )
    numba_cache = (
        Path(numba_cache_raw).resolve(strict=True)
        if isinstance(numba_cache_raw, str)
        and Path(numba_cache_raw).is_absolute()
        else None
    )
    numba_cache_info = numba_cache.stat() if numba_cache is not None else None
    required_process = {
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "TZ": "UTC",
        "CUDA_VISIBLE_DEVICES": "",
    }
    if (
        not isinstance(envelope, Mapping)
        or envelope.get("cpu_affinity") != [cpu_id]
        or envelope.get("python_no_user_site") is not True
        or envelope.get("python_dont_write_bytecode") is not True
        or envelope.get("pythonpath_absent") is not True
        or envelope.get("process_environment") != required_process
        or envelope.get("thread_environment") != _SINGLE_THREAD_ENVIRONMENT
        or numba_cache != expected_numba_cache
        or numba_cache_info is None
        or not stat.S_ISDIR(numba_cache_info.st_mode)
        or stat.S_IMODE(numba_cache_info.st_mode) & 0o077
    ):
        raise ValueError("candidate process envelope drifted")
    usage = report.get("resource_usage")
    cgroup = usage.get("cgroup_memory_peak") if isinstance(usage, Mapping) else None
    if (
        not isinstance(usage, Mapping)
        or not isinstance(usage.get("peak_rss_bytes"), int)
        or isinstance(usage.get("peak_rss_bytes"), bool)
        or usage["peak_rss_bytes"] <= 0
        or not isinstance(cgroup, Mapping)
        or cgroup.get("status") != "available"
        or not isinstance(cgroup.get("bytes"), int)
        or isinstance(cgroup.get("bytes"), bool)
        or cgroup["bytes"] <= 0
    ):
        raise ValueError("candidate memory evidence is unavailable")


def _validate_artifact_exact_set(
    output_directory: Path,
    *,
    expected_names: set[str],
) -> None:
    names: set[str] = set()
    for path in output_directory.iterdir():
        info = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(info.st_mode):
            raise ValueError("worker output contains a non-regular artifact")
        names.add(path.name)
    if names != expected_names:
        raise ValueError("worker output exact artifact set drifted")


def validate_plain_worker_output(
    run: Mapping[str, Any],
    *,
    cpu_id: int,
    fork_checkout: Path,
) -> dict[str, Any]:
    output = Path(str(run["output_directory"])).resolve(strict=True)
    _validate_artifact_exact_set(
        output,
        expected_names={
            "preparation.npy",
            "after_clifford.npy",
            "final_physical.npy",
            "plain_worker.json",
        },
    )
    report = _load_strict_json(output / "plain_worker.json")
    if (
        report.get("schema") != PLAIN_WORKER_SCHEMA
        or report.get("status") != "completed"
        or report.get("candidate_status") != "equal_status_candidate_not_truth"
        or report.get("fixture_sha256") != EXPECTED_FIXTURE_SHA256
        or report.get("sample")
        != {"kind": run["sample_kind"], "index": run["sample_index"]}
    ):
        raise ValueError("plain worker headline contract drifted")
    if report.get("orientation_control") != {
        "status": "NOT_EXECUTED_IN_TARGET_WORKER",
        "external_pre_target_control_required": True,
        "target_fixture_apply_count": 0,
    }:
        raise ValueError("plain target improperly executed its orientation control")
    provenance = report.get("provenance")
    quimb = provenance.get("quimb") if isinstance(provenance, Mapping) else None
    if (
        not isinstance(provenance, Mapping)
        or provenance.get("worker_sha256") != _sha256_file(_PLAIN_WORKER_PATH)
        or provenance.get("other_candidate_or_anchor_payload_seen") is not False
        or provenance.get("fork_pristine_before_and_after") is not True
        or provenance.get("candidate_output_input_paths_accepted") != []
        or provenance.get("anchor_output_input_paths_accepted") != []
        or not isinstance(quimb, Mapping)
        or quimb.get("commit") != EXPECTED_FORK_COMMIT
        or quimb.get("tree") != EXPECTED_FORK_TREE
        or quimb.get("clean_including_ignored") is not True
        or Path(str(quimb.get("root"))).resolve(strict=True)
        != fork_checkout.resolve(strict=True)
        or quimb.get("hybrid_imported") is not False
    ):
        raise ValueError("plain worker provenance drifted")
    construction = report.get("operator_construction")
    if (
        not isinstance(construction, Mapping)
        or construction.get("term_product_pepo_count") != 3
        or construction.get("instance_add_PEPO_call_count") != 2
        or construction.get("target_pepo_apply_call_count") != 1
        or construction.get("contract") is not True
        or construction.get("compress") is not False
        or construction.get("sequential_operator_application_used") is not False
    ):
        raise ValueError("plain direct-sum PEPO construction drifted")
    after_pepo_gauges = (
        report.get("state_resources", {}).get("after_pepo", {}).get("gauges")
    )
    if after_pepo_gauges != {
        "status": "UNAVAILABLE_NATIVE_PEPO_RESULT_NOT_VIDAL_GAUGED",
        "gauge_elements": None,
        "old_circuit_gauges_reused": False,
    }:
        raise ValueError("plain worker reused stale gauges")
    timing = report.get("timing_ns")
    if (
        not isinstance(timing, Mapping)
        or any(
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
            for value in timing.values()
        )
        or timing.get("plain_update")
        != timing.get("physical_clifford")
        + timing.get("pepo_build")
        + timing.get("pepo_apply")
    ):
        raise ValueError("plain timing formula drifted")
    _validate_common_worker_envelope(
        report,
        cpu_id=cpu_id,
        private_root=Path(str(run["private_root"])),
    )
    vectors: dict[str, Any] = {}
    vector_hashes: dict[str, str] = {}
    npy_file_hashes: dict[str, str] = {}
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, Mapping) or set(artifacts) != {
        "preparation",
        "after_clifford",
        "final_physical",
    }:
        raise ValueError("plain vector artifact ledger drifted")
    for name, row in artifacts.items():
        path = output / str(row["file"])
        file_hash = _sha256_file(path)
        if file_hash != row.get("file_sha256"):
            raise ValueError("plain vector file hash drifted")
        npy_file_hashes[name] = file_hash
        content_hash = str(row["vector_sha256_little_endian_c128_c_order"])
        vectors[name] = _load_exact_c128_vector(
            path, expected_content_hash=content_hash
        )
        vector_hashes[name] = content_hash
    return {
        "report": report,
        "vectors": vectors,
        "vector_hashes": vector_hashes,
        "npy_file_hashes": npy_file_hashes,
        "update_ns": int(timing["plain_update"]),
        "peak_rss_bytes": int(report["resource_usage"]["peak_rss_bytes"]),
        "cgroup_memory_peak_bytes": int(
            report["resource_usage"]["cgroup_memory_peak"]["bytes"]
        ),
        "output_directory": str(output),
    }


def validate_gcapeps_worker_output(
    run: Mapping[str, Any],
    *,
    cpu_id: int,
    fork_checkout: Path,
) -> dict[str, Any]:
    output = Path(str(run["output_directory"])).resolve(strict=True)
    vector_filenames = {
        "residual_preparation": "gcapeps_residual_preparation_vector.npy",
        "after_clifford": "gcapeps_after_clifford_vector.npy",
        "residual_after_update": "gcapeps_residual_after_update_vector.npy",
        "physical_after_update": "gcapeps_physical_after_update_vector.npy",
    }
    _validate_artifact_exact_set(
        output,
        expected_names=set(vector_filenames.values()) | {"gcapeps_worker.json"},
    )
    report = _load_strict_json(output / "gcapeps_worker.json")
    fixture = report.get("fixture")
    if (
        report.get("schema") != GCAPEPS_WORKER_SCHEMA
        or report.get("status") != "completed"
        or not isinstance(fixture, Mapping)
        or fixture.get("canonical_sha256") != EXPECTED_FIXTURE_SHA256
        or fixture.get("file_sha256") != EXPECTED_FIXTURE_SHA256
        or report.get("sample")
        != {"kind": run["sample_kind"], "index": run["sample_index"]}
        or report.get("no_candidate_or_anchor_output_consumed") is not True
    ):
        raise ValueError("GCAPEPS worker headline contract drifted")
    fork = report.get("fork")
    provenance = report.get("provenance")
    if (
        not isinstance(fork, Mapping)
        or fork.get("commit") != EXPECTED_FORK_COMMIT
        or fork.get("tree") != EXPECTED_FORK_TREE
        or fork.get("origin") != EXPECTED_FORK_ORIGIN
        or fork.get("clean_including_ignored") is not True
        or Path(str(fork.get("path"))).resolve(strict=True)
        != fork_checkout.resolve(strict=True)
        or not isinstance(provenance, Mapping)
        or provenance.get("worker_sha256") != _sha256_file(_GC_WORKER_PATH)
        or provenance.get("fork_pristine_before_and_after") is not True
        or provenance.get("candidate_output_input_paths_accepted") != []
        or provenance.get("anchor_output_input_paths_accepted") != []
    ):
        raise ValueError("GCAPEPS worker provenance drifted")
    event_binding = report.get("coherent_event", {}).get("coherent_term_binding")
    if (
        not isinstance(event_binding, Mapping)
        or event_binding.get("coefficients_and_signed_words_exactly_bound") is not True
    ):
        raise ValueError("GCAPEPS coherent applied-event term binding is unavailable")
    if (
        report.get("refactor_implemented") is not False
        or report.get("compression_applied") is not False
        or report.get("truncation_applied") is not False
        or report.get("approximate_contraction_applied") is not False
    ):
        raise ValueError("GCAPEPS frozen untruncated lowering drifted")
    timing = report.get("timing_ns")
    if (
        not isinstance(timing, Mapping)
        or any(
            not isinstance(value, int) or isinstance(value, bool) or value <= 0
            for value in timing.values()
        )
        or timing.get("gcapeps_update_ns")
        != timing.get("tableau_prefix_ns")
        + timing.get("coherent_ir_build_ns")
        + timing.get("carrier_apply_ns")
    ):
        raise ValueError("GCAPEPS timing formula drifted")
    _validate_common_worker_envelope(
        report,
        cpu_id=cpu_id,
        private_root=Path(str(run["private_root"])),
    )
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, Mapping) or set(artifacts) != set(vector_filenames):
        raise ValueError("GCAPEPS vector artifact ledger drifted")
    vectors: dict[str, Any] = {}
    vector_hashes: dict[str, str] = {}
    npy_file_hashes: dict[str, str] = {}
    for name, filename in vector_filenames.items():
        row = artifacts[name]
        path = output / filename
        file_hash = _sha256_file(path)
        if row.get("filename") != filename or file_hash != row.get("file_sha256"):
            raise ValueError("GCAPEPS vector file hash drifted")
        npy_file_hashes[name] = file_hash
        content_hash = str(row["content_sha256_c_order_little_endian_c16"])
        vectors[name] = _load_exact_c128_vector(
            path, expected_content_hash=content_hash
        )
        vector_hashes[name] = content_hash
    return {
        "report": report,
        "vectors": vectors,
        "vector_hashes": vector_hashes,
        "npy_file_hashes": npy_file_hashes,
        "update_ns": int(timing["gcapeps_update_ns"]),
        "peak_rss_bytes": int(report["resource_usage"]["peak_rss_bytes"]),
        "cgroup_memory_peak_bytes": int(
            report["resource_usage"]["cgroup_memory_peak"]["bytes"]
        ),
        "output_directory": str(output),
    }


def validate_anchor_output(run: Mapping[str, Any]) -> dict[str, Any]:
    output = Path(str(run["output_directory"])).resolve(strict=True)
    report = _load_strict_json(output / "anchor_report.json")
    body = dict(report)
    content_hash = body.pop("content_hash", None)
    if content_hash != hashlib.sha256(_canonical_json_bytes(body)).hexdigest():
        raise ValueError("anchor report content hash drifted")
    if (
        report.get("fixture", {}).get("sha256") != EXPECTED_FIXTURE_SHA256
        or report.get("anchor_self_verdict") != "PASS"
        or report.get("all_checks_passed") is not True
        or report.get("scope", {}).get("enters_efficiency_timing_or_rss") is not False
        or report.get("runtime_provenance", {}).get("forbidden_loaded_modules") != []
    ):
        raise ValueError("anchor report did not qualify its independent formulations")
    vectors: dict[str, Any] = {}
    vector_hashes: dict[str, str] = {}
    for name, row in report.get("vectors", {}).items():
        path = output / str(row["relative_path"])
        vectors[name] = _load_exact_c128_vector(
            path, expected_content_hash=str(row["sha256"])
        )
        vector_hashes[name] = str(row["sha256"])
    required = {
        "closed_form_preparation",
        "gate_replay_preparation",
        "residual_state",
        "physical_preparation_after_clifford",
        "physical_from_residual_lift",
        "physical_from_signed_terms",
    }
    if set(vectors) != required:
        raise ValueError("anchor vector family drifted")
    return {
        "report": report,
        "vectors": vectors,
        "vector_hashes": vector_hashes,
        "output_directory": str(output),
        "enters_timing_or_rss_ratio": False,
    }


def require_lane_determinism(
    samples: Sequence[Mapping[str, Any]], *, lane: str
) -> dict[str, Any]:
    if len(samples) != 6:
        raise ValueError(f"{lane} must have six measured samples")
    names = set(samples[0]["vector_hashes"])
    for sample in samples:
        if set(sample["vector_hashes"]) != names:
            raise ValueError(f"{lane} vector family drifted across samples")
    hashes = {
        name: [str(sample["vector_hashes"][name]) for sample in samples]
        for name in sorted(names)
    }
    if any(len(set(values)) != 1 for values in hashes.values()):
        raise ValueError(
            f"{lane} complete vectors are nondeterministic across measured workers"
        )
    npy_hashes = {
        name: [str(sample["npy_file_hashes"][name]) for sample in samples]
        for name in sorted(names)
    }
    if any(len(set(values)) != 1 for values in npy_hashes.values()):
        raise ValueError(
            f"{lane} NPY bytes are nondeterministic across measured workers"
        )
    return {
        "lane": lane,
        "measured_sample_count": 6,
        "vector_hashes_by_sample": hashes,
        "npy_file_hashes_by_sample": npy_hashes,
        "all_complete_vectors_byte_identical": True,
        "all_npy_files_byte_identical": True,
    }


def aggregate_equal_status_differential(
    *,
    fixture: Mapping[str, Any],
    measured_runs: Sequence[Mapping[str, Any]],
    anchor: Mapping[str, Any],
    controls: Mapping[str, Any],
    parent_identity: Mapping[str, Any],
    fork_identity: Mapping[str, Any],
    environment_identity: Mapping[str, Any],
    systemd_preflight: Mapping[str, Any],
) -> dict[str, Any]:
    """Grade equal-status outputs, then conditionally expose efficiency ratios."""

    plain = [row["validated"] for row in measured_runs if row["lane"] == "plain"]
    gcapeps = [row["validated"] for row in measured_runs if row["lane"] == "gcapeps"]
    if len(plain) != 6 or len(gcapeps) != 6:
        raise ValueError("measured target population is not six per lane")
    if tuple(row["lane"] for row in measured_runs) != measured_launch_order():
        raise ValueError("measured target launch order drifted")
    plain_determinism = require_lane_determinism(plain, lane="plain")
    gcapeps_determinism = require_lane_determinism(gcapeps, lane="gcapeps")
    comparator = _load_script(
        _COMPARATOR_PATH,
        f"_gcapeps_target_comparator_{uuid.uuid4().hex}",
    )
    grading = comparator.grade_candidate_state_action(
        plain_preparation=plain[0]["vectors"]["preparation"],
        gcapeps_preparation=gcapeps[0]["vectors"]["residual_preparation"],
        plain_after_clifford=plain[0]["vectors"]["after_clifford"],
        gcapeps_after_clifford=gcapeps[0]["vectors"]["after_clifford"],
        plain_final=plain[0]["vectors"]["final_physical"],
        gcapeps_final=gcapeps[0]["vectors"]["physical_after_update"],
        gcapeps_residual=gcapeps[0]["vectors"]["residual_after_update"],
        anchor_vectors=anchor["vectors"],
        bands=fixture["metric_bands"],
    )
    sdim_frame_verdict = (
        "PASS"
        if controls["controls"]["external_evidence"]["sdim_normal_and_first_sign_flip"][
            "status"
        ]
        == "PASS"
        else "INELIGIBLE"
    )
    terminal = comparator.terminal_semantics(
        differential_verdict=grading["differential_verdict"],
        anchor_verdict=grading["anchor_verdict"],
        sdim_frame_verdict=sdim_frame_verdict,
        exact_structure_and_fairness_passed=bool(grading["fairness_passed"]),
        controls_passed=controls.get("passed") is True,
        provenance_passed=True,
        publication_preflight_passed=True,
    )
    eligible = terminal["efficiency_interpretation"] != "INELIGIBLE"
    efficiency = summarize_efficiency_samples(
        plain_update_ns=[row["update_ns"] for row in plain],
        gcapeps_update_ns=[row["update_ns"] for row in gcapeps],
        plain_peak_rss_bytes=[row["peak_rss_bytes"] for row in plain],
        gcapeps_peak_rss_bytes=[row["peak_rss_bytes"] for row in gcapeps],
        interpretation_eligible=eligible,
    )
    efficiency["cgroup_memory_peak_bytes"] = {
        "plain": _median_and_mad([row["cgroup_memory_peak_bytes"] for row in plain]),
        "gcapeps": _median_and_mad(
            [row["cgroup_memory_peak_bytes"] for row in gcapeps]
        ),
        "ratio_plain_over_gcapeps": (
            statistics.median([row["cgroup_memory_peak_bytes"] for row in plain])
            / statistics.median([row["cgroup_memory_peak_bytes"] for row in gcapeps])
            if eligible
            else None
        ),
    }
    efficiency["anchor_enters_any_ratio"] = False
    efficiency["sdim_enters_any_ratio"] = False
    efficiency["candidate_role"] = "equal_status"
    efficiency["ordinary_quimb_is_truth"] = False
    efficiency["gcapeps_is_truth"] = False
    return {
        "schema": RESULT_SCHEMA,
        "status": "completed",
        "experiment_role": "equal_status_candidate_state_action_and_efficiency_differential",
        "candidate_semantics": {
            "ordinary_quimb": "equal_status_candidate",
            "gcapeps": "equal_status_candidate",
            "ordinary_quimb_is_truth": False,
            "gcapeps_is_truth": False,
            "numpy_anchor_role": "untimed_one_fixture_implementation_accident_check_and_state_action_qualification",
            "numpy_anchor_is_generic_peps_truth": False,
            "pairwise_difference_is_primary_numeric_comparison": True,
        },
        "fixture": {
            "sha256": EXPECTED_FIXTURE_SHA256,
            "n_qubits": 8,
            "active_rank": 3,
            "dtype": "complex128",
        },
        "terminal": terminal,
        "complete_vector_grading": grading,
        "measured_determinism": {
            "plain": plain_determinism,
            "gcapeps": gcapeps_determinism,
        },
        "efficiency": efficiency,
        "launch_protocol": {
            "warmup_order": list(warmup_launch_order()),
            "measured_order": list(measured_launch_order()),
            "warmup_discarded": True,
            "fresh_process_per_sample": True,
            "strictly_serial": True,
            "sample_count_per_lane": 6,
        },
        "provenance": {
            "parent": dict(parent_identity),
            "fresh_fork": dict(fork_identity),
            "main_environment": dict(environment_identity),
            "systemd_cgroup_preflight": dict(systemd_preflight),
            "controls_bundle": {
                "root": controls["root"],
                "bundle_artifact_sha256": controls["bundle_artifact_sha256"],
                "controls_content_sha256": controls["controls"]["content_sha256"],
            },
            "claim_bearing_source_sha256": claim_bearing_source_hashes(),
            "all_workers_bound_to_same_fixture_fork_cpu_dtype": True,
        },
        "publication_semantics": {
            "preflight_passed_before_target_workers": True,
            "terminal_payload_is_prepared_before_atomic_rename": True,
            "successful_supervisor_return_is_required_for_publication_confirmation": True,
        },
        "claim_boundary": {
            "one_input_state_action_only": True,
            "generic_peps_contraction_certificate": False,
            "all_input_operator_equality": False,
            "record_or_measurement_law": False,
            "scaling_evidence": False,
            "portable_performance_claim": False,
            "ordinary_quimb_optimality_claim": False,
        },
    }


def run_orientation_control_worker(
    *,
    fixture_path: Path,
    fork_checkout: Path,
    python_executable: Path,
    cpu_id: int,
    runtime_parent: Path,
) -> dict[str, Any]:
    private_root = _private_subdirectory(
        runtime_parent, f"orientation-{uuid.uuid4().hex}"
    )
    environment = _worker_environment_for_prefix(
        python_executable.resolve(strict=True).parent.parent,
        private_root,
    )
    output_json = private_root / "orientation.json"
    worker_command = [
        str(python_executable.resolve(strict=True)),
        "-I",
        "-B",
        str(_CONTROLS_PATH.resolve(strict=True)),
        "orientation",
        "--fixture-json",
        str(fixture_path.resolve(strict=True)),
        "--fork-checkout",
        str(fork_checkout.resolve(strict=True)),
        "--expected-fork-commit",
        EXPECTED_FORK_COMMIT,
        "--expected-fork-tree",
        EXPECTED_FORK_TREE,
        "--output-json",
        str(output_json),
    ]
    unit_name = f"gcapeps-orientation-{uuid.uuid4().hex[:12]}"
    command = build_systemd_worker_command(
        unit_name=unit_name,
        cpu_id=cpu_id,
        worker_command=worker_command,
        worker_environment=environment,
        working_directory=fork_checkout,
    )
    process = _run_captured(
        command,
        cwd=fork_checkout,
        environment=environment,
        timeout_seconds=120,
    )
    if not output_json.is_file():
        raise RuntimeError("orientation control did not seal evidence")
    return {"output_json": str(output_json.resolve(strict=True)), "process": process}


def run_gc_construction_control_worker(
    *,
    fork_checkout: Path,
    python_executable: Path,
    cpu_id: int,
    runtime_parent: Path,
) -> dict[str, Any]:
    private_root = _private_subdirectory(
        runtime_parent, f"construction-{uuid.uuid4().hex}"
    )
    environment = _worker_environment_for_prefix(
        python_executable.resolve(strict=True).parent.parent,
        private_root,
    )
    output_json = private_root / "gc-construction.json"
    worker_command = [
        str(python_executable.resolve(strict=True)),
        "-I",
        "-B",
        str(_CONTROLS_PATH.resolve(strict=True)),
        "gc-construction",
        "--fork-checkout",
        str(fork_checkout.resolve(strict=True)),
        "--expected-fork-commit",
        EXPECTED_FORK_COMMIT,
        "--expected-fork-tree",
        EXPECTED_FORK_TREE,
        "--output-json",
        str(output_json),
    ]
    unit_name = f"gcapeps-construction-{uuid.uuid4().hex[:12]}"
    command = build_systemd_worker_command(
        unit_name=unit_name,
        cpu_id=cpu_id,
        worker_command=worker_command,
        worker_environment=environment,
        working_directory=fork_checkout,
    )
    process = _run_captured(
        command,
        cwd=fork_checkout,
        environment=environment,
        timeout_seconds=180,
    )
    if not output_json.is_file():
        raise RuntimeError("GC construction control did not seal evidence")
    return {"output_json": str(output_json.resolve(strict=True)), "process": process}


def collect_controls_report(
    *,
    fixture_path: Path,
    orientation_json: Path,
    construction_json: Path,
    sdim_normal_json: Path,
    sdim_flip_json: Path,
    runtime_parent: Path,
) -> dict[str, Any]:
    private_root = _private_subdirectory(runtime_parent, f"collect-{uuid.uuid4().hex}")
    output_json = private_root / "controls.json"
    command = [
        str(Path(sys.executable).resolve(strict=True)),
        "-I",
        "-B",
        str(_CONTROLS_PATH.resolve(strict=True)),
        "collect",
        "--fixture-json",
        str(fixture_path.resolve(strict=True)),
        "--orientation-evidence-json",
        str(orientation_json.resolve(strict=True)),
        "--gc-construction-evidence-json",
        str(construction_json.resolve(strict=True)),
        "--sdim-normal-evidence-json",
        str(sdim_normal_json.resolve(strict=True)),
        "--sdim-flip-evidence-json",
        str(sdim_flip_json.resolve(strict=True)),
        "--output-json",
        str(output_json),
    ]
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    process = _run_captured(command, environment=environment, timeout_seconds=180)
    report = _load_strict_json(output_json, canonical=True)
    if (
        report.get("schema") != CONTROLS_SCHEMA
        or report.get("controls_passed") is not True
    ):
        raise RuntimeError("collected controls did not pass")
    return {
        "output_json": str(output_json.resolve(strict=True)),
        "report": report,
        "process": process,
    }


def _canonical_record_bytes(value: Mapping[str, Any]) -> bytes:
    return _canonical_json_bytes(dict(value))


def run_controls_supervisor(
    *,
    destination: Path,
    fork_source: Path = DEFAULT_FORK_SOURCE,
    pixi_executable: Path = DEFAULT_PIXI_EXECUTABLE,
    sdim_python: Path = DEFAULT_SDIM_PYTHON,
) -> dict[str, Any]:
    """Run controls only; no clean n=8 candidate is ever launched here."""

    parent = verify_committed_parent_checkout()
    with preflight_publication(destination) as publication:
        with tempfile.TemporaryDirectory(prefix="gcapeps-controls-") as temporary:
            runtime_root = Path(temporary).resolve(strict=True)
            os.chmod(runtime_root, 0o700)
            checkout_path = runtime_root / "fork"
            materialized = materialize_fresh_fork(fork_source, checkout_path)
            environment_root = _private_subdirectory(runtime_root, "main-environment")
            main_environment = provision_locked_main_environment(
                pixi_executable=pixi_executable,
                fork_checkout=checkout_path,
                private_root=environment_root,
            )
            capability_root = _private_subdirectory(runtime_root, "capability")
            capability = preflight_systemd_resource_envelope(
                private_root=capability_root
            )
            cpu_id = int(capability["selected_lowest_cpu"])
            emitter = _load_script(
                _EMITTER_PATH,
                f"_gcapeps_controls_emitter_{uuid.uuid4().hex}",
            )
            fixture = emitter.build_fixture()
            if emitter.validate_fixture(fixture) != EXPECTED_FIXTURE_SHA256:
                raise RuntimeError("controls fixture semantic identity drifted")
            fixture_path = runtime_root / "fixture.json"
            fixture_bytes = emitter.canonical_json_bytes(fixture)
            if hashlib.sha256(fixture_bytes).hexdigest() != EXPECTED_FIXTURE_SHA256:
                raise RuntimeError("controls fixture byte identity drifted")
            _write_exclusive_file(fixture_path, fixture_bytes)
            workers_root = _private_subdirectory(runtime_root, "control-workers")
            orientation = run_orientation_control_worker(
                fixture_path=fixture_path,
                fork_checkout=checkout_path,
                python_executable=Path(main_environment["python_executable"]),
                cpu_id=cpu_id,
                runtime_parent=workers_root,
            )
            construction = run_gc_construction_control_worker(
                fork_checkout=checkout_path,
                python_executable=Path(main_environment["python_executable"]),
                cpu_id=cpu_id,
                runtime_parent=workers_root,
            )
            sdim_normal = run_sdim_control_worker(
                flip_first_sign=False,
                fixture_path=fixture_path,
                fork_checkout=checkout_path,
                sdim_python=sdim_python,
                cpu_id=cpu_id,
                runtime_parent=workers_root,
            )
            sdim_flip = run_sdim_control_worker(
                flip_first_sign=True,
                fixture_path=fixture_path,
                fork_checkout=checkout_path,
                sdim_python=sdim_python,
                cpu_id=cpu_id,
                runtime_parent=workers_root,
            )
            collected = collect_controls_report(
                fixture_path=fixture_path,
                orientation_json=Path(orientation["output_json"]),
                construction_json=Path(construction["output_json"]),
                sdim_normal_json=Path(sdim_normal["output_json"]),
                sdim_flip_json=Path(sdim_flip["output_json"]),
                runtime_parent=workers_root,
            )
            fork_after = verify_frozen_fork_checkout(checkout_path)
            if fork_after != materialized:
                raise RuntimeError("fresh fork changed during controls")
            artifacts = {
                "fixture.json": fixture_bytes,
                "orientation.json": Path(orientation["output_json"]).read_bytes(),
                "gc-construction.json": Path(construction["output_json"]).read_bytes(),
                "sdim-normal.json": Path(sdim_normal["output_json"]).read_bytes(),
                "sdim-flip.json": Path(sdim_flip["output_json"]).read_bytes(),
                "controls.json": Path(collected["output_json"]).read_bytes(),
                "logs/orientation.json": _canonical_record_bytes(
                    orientation["process"]
                ),
                "logs/gc-construction.json": _canonical_record_bytes(
                    construction["process"]
                ),
                "logs/sdim-normal.json": _canonical_record_bytes(
                    sdim_normal["process"]
                ),
                "logs/sdim-flip.json": _canonical_record_bytes(sdim_flip["process"]),
                "logs/collect.json": _canonical_record_bytes(collected["process"]),
                "provenance/parent.json": _canonical_record_bytes(parent),
                "provenance/fresh-fork.json": _canonical_record_bytes(fork_after),
                "provenance/main-environment.json": _canonical_record_bytes(
                    main_environment
                ),
                "provenance/systemd-cgroup.json": _canonical_record_bytes(capability),
            }
            confirmation = publish_bundle_noreplace(
                publication,
                artifacts=artifacts,
                manifest_payload={
                    "schema": CONTROLS_SCHEMA,
                    "status": "PASS",
                    "controls_passed": True,
                    "clean_n8_plain_candidate_executed": False,
                    "clean_n8_gcapeps_candidate_executed": False,
                    "fixture_sha256": EXPECTED_FIXTURE_SHA256,
                    "parent_commit": parent["commit"],
                    "fork_commit": EXPECTED_FORK_COMMIT,
                },
            )
    return {
        "status": "PASS",
        "destination": str(destination.absolute()),
        "publication": confirmation,
        "clean_n8_candidates_executed": False,
    }


def _compact_provenance(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _compact_provenance(item)
            for key, item in value.items()
            if key not in {"stdout", "stderr"}
        }
    if isinstance(value, list):
        return [_compact_provenance(item) for item in value]
    if isinstance(value, tuple):
        return [_compact_provenance(item) for item in value]
    return value


def _add_tree_artifacts(
    target: dict[str, bytes],
    *,
    prefix: str,
    root: Path,
) -> None:
    for name, payload in _bundle_artifacts(root).items():
        key = f"{prefix.rstrip('/')}/{name}"
        if key in target:
            raise RuntimeError(f"duplicate final artifact name: {key}")
        target[key] = payload


def _target_sample_rows(
    measured_runs: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for launch_index, run in enumerate(measured_runs):
        validated = run["validated"]
        rows.append(
            {
                "launch_index": launch_index,
                "lane": run["lane"],
                "lane_sample_index": run["sample_index"],
                "update_ns": validated["update_ns"],
                "peak_rss_bytes": validated["peak_rss_bytes"],
                "cgroup_memory_peak_bytes": validated["cgroup_memory_peak_bytes"],
                "summary_file_sha256": _sha256_file(Path(run["summary_path"])),
                "process_launch_and_worker_elapsed_ns": run["process"][
                    "launch_and_process_elapsed_ns"
                ],
                "process_returncode": run["process"]["returncode"],
            }
        )
    return rows


def run_target_supervisor(
    *,
    destination: Path,
    controls_bundle: Path,
    fork_source: Path = DEFAULT_FORK_SOURCE,
    pixi_executable: Path = DEFAULT_PIXI_EXECUTABLE,
) -> dict[str, Any]:
    """Execute the frozen target population once after sealed controls pass."""

    controls = validate_controls_bundle(controls_bundle)
    parent = verify_committed_parent_checkout()
    if controls["manifest"].get("parent_commit") != parent["commit"]:
        raise ValueError("controls bundle parent commit differs from target parent")
    with preflight_publication(destination) as publication:
        with tempfile.TemporaryDirectory(prefix="gcapeps-target-") as temporary:
            runtime_root = Path(temporary).resolve(strict=True)
            os.chmod(runtime_root, 0o700)
            failure_context: dict[str, Any] = {
                "parent": _compact_provenance(parent),
                "controls_bundle": controls["root"],
                "clean_target_worker_launches": [],
            }
            success_publication_attempted = False
            try:
                checkout_path = runtime_root / "fork"
                materialized = materialize_fresh_fork(fork_source, checkout_path)
                failure_context["fresh_fork"] = materialized
                environment_root = _private_subdirectory(
                    runtime_root, "main-environment"
                )
                main_environment = provision_locked_main_environment(
                    pixi_executable=pixi_executable,
                    fork_checkout=checkout_path,
                    private_root=environment_root,
                )
                failure_context["main_environment"] = _compact_provenance(
                    main_environment
                )
                capability_root = _private_subdirectory(runtime_root, "capability")
                capability = preflight_systemd_resource_envelope(
                    private_root=capability_root
                )
                failure_context["systemd_cgroup"] = _compact_provenance(capability)
                cpu_id = int(capability["selected_lowest_cpu"])
                emitter = _load_script(
                    _EMITTER_PATH,
                    f"_gcapeps_target_emitter_{uuid.uuid4().hex}",
                )
                fixture = emitter.build_fixture()
                if emitter.validate_fixture(fixture) != EXPECTED_FIXTURE_SHA256:
                    raise RuntimeError("target fixture semantic identity drifted")
                fixture_bytes = emitter.canonical_json_bytes(fixture)
                if hashlib.sha256(fixture_bytes).hexdigest() != EXPECTED_FIXTURE_SHA256:
                    raise RuntimeError("target fixture byte identity drifted")
                if fixture_bytes != controls["artifacts"]["fixture.json"]:
                    raise RuntimeError("target fixture differs from controls fixture")
                fixture_path = runtime_root / "fixture.json"
                _write_exclusive_file(fixture_path, fixture_bytes)
                workers_root = _private_subdirectory(runtime_root, "target-workers")
                python_executable = Path(main_environment["python_executable"])
                warmup_runs: list[dict[str, Any]] = []
                for lane in warmup_launch_order():
                    run = run_candidate_worker(
                        lane=lane,
                        sample_kind="warmup",
                        sample_index=0,
                        fixture_path=fixture_path,
                        fork_checkout=checkout_path,
                        python_executable=python_executable,
                        cpu_id=cpu_id,
                        runtime_parent=workers_root,
                    )
                    run["validated"] = (
                        validate_plain_worker_output(
                            run,
                            cpu_id=cpu_id,
                            fork_checkout=checkout_path,
                        )
                        if lane == "plain"
                        else validate_gcapeps_worker_output(
                            run,
                            cpu_id=cpu_id,
                            fork_checkout=checkout_path,
                        )
                    )
                    warmup_runs.append(run)
                    failure_context["clean_target_worker_launches"].append(
                        {"lane": lane, "sample_kind": "warmup", "sample_index": 0}
                    )
                measured_runs: list[dict[str, Any]] = []
                next_index = {"plain": 0, "gcapeps": 0}
                for lane in measured_launch_order():
                    sample_index = next_index[lane]
                    next_index[lane] += 1
                    run = run_candidate_worker(
                        lane=lane,
                        sample_kind="measured",
                        sample_index=sample_index,
                        fixture_path=fixture_path,
                        fork_checkout=checkout_path,
                        python_executable=python_executable,
                        cpu_id=cpu_id,
                        runtime_parent=workers_root,
                    )
                    run["validated"] = (
                        validate_plain_worker_output(
                            run,
                            cpu_id=cpu_id,
                            fork_checkout=checkout_path,
                        )
                        if lane == "plain"
                        else validate_gcapeps_worker_output(
                            run,
                            cpu_id=cpu_id,
                            fork_checkout=checkout_path,
                        )
                    )
                    measured_runs.append(run)
                    failure_context["clean_target_worker_launches"].append(
                        {
                            "lane": lane,
                            "sample_kind": "measured",
                            "sample_index": sample_index,
                        }
                    )
                # All candidate outputs are sealed before this independent worker runs.
                anchor_run = run_anchor_worker(
                    fixture_path=fixture_path,
                    python_executable=python_executable,
                    runtime_parent=workers_root,
                )
                anchor = validate_anchor_output(anchor_run)
                fork_after = verify_frozen_fork_checkout(checkout_path)
                if fork_after != materialized:
                    raise RuntimeError("fresh fork changed during target execution")
                result = aggregate_equal_status_differential(
                    fixture=fixture,
                    measured_runs=measured_runs,
                    anchor=anchor,
                    controls=controls,
                    parent_identity=parent,
                    fork_identity=fork_after,
                    environment_identity=_compact_provenance(main_environment),
                    systemd_preflight=_compact_provenance(capability),
                )
                result["raw_measured_sample_rows"] = _target_sample_rows(measured_runs)
                result["warmup_samples"] = [
                    {
                        "lane": row["lane"],
                        "sample_index": row["sample_index"],
                        "summary_file_sha256": _sha256_file(Path(row["summary_path"])),
                        "discarded_from_all_summaries": True,
                    }
                    for row in warmup_runs
                ]
                result["candidate_outputs_sealed_before_anchor_execution"] = True
                result_bytes = _canonical_json_bytes(result)
                artifacts: dict[str, bytes] = {
                    "result.json": result_bytes,
                    "fixture.json": fixture_bytes,
                    "controls/source-manifest.json": _canonical_json_bytes(
                        controls["manifest"]
                    ),
                    "provenance/main-environment-full.json": _canonical_json_bytes(
                        main_environment
                    ),
                }
                for name, payload in controls["artifacts"].items():
                    artifacts[f"controls/{name}"] = payload
                for sequence, run in enumerate(warmup_runs):
                    prefix = f"workers/warmup/{sequence:02d}-{run['lane']}"
                    _add_tree_artifacts(
                        artifacts,
                        prefix=prefix,
                        root=Path(run["output_directory"]),
                    )
                    artifacts[f"{prefix}/launch.json"] = _canonical_json_bytes(
                        run["process"]
                    )
                for sequence, run in enumerate(measured_runs):
                    prefix = f"workers/measured/{sequence:02d}-{run['lane']}"
                    _add_tree_artifacts(
                        artifacts,
                        prefix=prefix,
                        root=Path(run["output_directory"]),
                    )
                    artifacts[f"{prefix}/launch.json"] = _canonical_json_bytes(
                        run["process"]
                    )
                _add_tree_artifacts(
                    artifacts,
                    prefix="anchor",
                    root=Path(anchor_run["output_directory"]),
                )
                artifacts["anchor/launch.json"] = _canonical_json_bytes(
                    anchor_run["process"]
                )
                success_publication_attempted = True
                confirmation = publish_bundle_noreplace(
                    publication,
                    artifacts=artifacts,
                    manifest_payload={
                        "schema": RESULT_SCHEMA,
                        "status": "completed",
                        "fixture_sha256": EXPECTED_FIXTURE_SHA256,
                        "candidate_role": "equal_status",
                        "ordinary_quimb_is_truth": False,
                        "gcapeps_is_truth": False,
                        "differential_verdict": result["terminal"][
                            "differential_verdict"
                        ],
                        "anchor_verdict": result["terminal"]["anchor_verdict"],
                        "sdim_frame_verdict": result["terminal"]["sdim_frame_verdict"],
                        "state_action_qualification_status": result["terminal"][
                            "state_action_qualification_status"
                        ],
                        "efficiency_interpretation": result["terminal"][
                            "efficiency_interpretation"
                        ],
                    },
                )
                return {
                    "status": "completed",
                    "destination": str(destination.absolute()),
                    "terminal": result["terminal"],
                    "publication": confirmation,
                }
            except Exception as exc:
                # A completed publication may already have crossed renameat2.
                # Preserve that original error; never attempt a second bundle.
                if success_publication_attempted:
                    raise
                failure = {
                    "schema": RESULT_SCHEMA,
                    "status": "INELIGIBLE_EXECUTION_FAILURE",
                    "failure_type": type(exc).__name__,
                    "failure_message": str(exc),
                    "differential_verdict": "INELIGIBLE",
                    "anchor_verdict": "INELIGIBLE",
                    "sdim_frame_verdict": "INELIGIBLE",
                    "state_action_qualification_status": "INELIGIBLE",
                    "efficiency_interpretation": "INELIGIBLE",
                    "efficiency_ratios_emitted": False,
                    "partial_context": _compact_provenance(failure_context),
                    "ordinary_quimb_is_truth": False,
                    "gcapeps_is_truth": False,
                }
                confirmation = publish_bundle_noreplace(
                    publication,
                    artifacts={"failure.json": _canonical_json_bytes(failure)},
                    manifest_payload={
                        "schema": RESULT_SCHEMA,
                        "status": "INELIGIBLE_EXECUTION_FAILURE",
                        "fixture_sha256": EXPECTED_FIXTURE_SHA256,
                        "candidate_role": "equal_status",
                        "ordinary_quimb_is_truth": False,
                        "gcapeps_is_truth": False,
                    },
                )
                return {
                    "status": "INELIGIBLE_EXECUTION_FAILURE",
                    "destination": str(destination.absolute()),
                    "failure_type": type(exc).__name__,
                    "failure_message": str(exc),
                    "publication": confirmation,
                }


def run_preflight_only(
    *,
    destination: Path,
    fork_source: Path = DEFAULT_FORK_SOURCE,
    pixi_executable: Path = DEFAULT_PIXI_EXECUTABLE,
    sdim_python: Path = DEFAULT_SDIM_PYTHON,
) -> dict[str, Any]:
    """Provision and probe every capability without running controls or target."""

    parent = verify_committed_parent_checkout()
    sdim_resolved = sdim_python.absolute().resolve(strict=True)
    if not sdim_resolved.is_file() or not os.access(sdim_resolved, os.X_OK):
        raise RuntimeError("SDIM Python is unavailable")
    with preflight_publication(destination):
        with tempfile.TemporaryDirectory(prefix="gcapeps-preflight-") as temporary:
            root = Path(temporary).resolve(strict=True)
            os.chmod(root, 0o700)
            checkout = root / "fork"
            fork = materialize_fresh_fork(fork_source, checkout)
            environment_root = _private_subdirectory(root, "main-environment")
            main_environment = provision_locked_main_environment(
                pixi_executable=pixi_executable,
                fork_checkout=checkout,
                private_root=environment_root,
            )
            capability_root = _private_subdirectory(root, "capability")
            capability = preflight_systemd_resource_envelope(
                private_root=capability_root
            )
            fork_after = verify_frozen_fork_checkout(checkout)
            if fork_after != fork:
                raise RuntimeError("fresh fork changed during preflight")
            return {
                "status": "PASS",
                "scope": "capability_preflight_only",
                "clean_n8_candidates_executed": False,
                "controls_executed": False,
                "destination_was_only_probed_and_not_created": True,
                "parent": _compact_provenance(parent),
                "fresh_fork": fork_after,
                "main_environment": _compact_provenance(main_environment),
                "sdim_python": str(sdim_resolved),
                "systemd_cgroup": _compact_provenance(capability),
            }


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "controls", "target"):
        command = commands.add_parser(name)
        command.add_argument("--destination", type=Path, required=True)
        command.add_argument("--fork-source", type=Path, default=DEFAULT_FORK_SOURCE)
        command.add_argument(
            "--pixi-executable",
            type=Path,
            default=DEFAULT_PIXI_EXECUTABLE,
        )
        if name in {"preflight", "controls"}:
            command.add_argument(
                "--sdim-python", type=Path, default=DEFAULT_SDIM_PYTHON
            )
        if name == "target":
            command.add_argument("--controls-bundle", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "preflight":
        result = run_preflight_only(
            destination=args.destination,
            fork_source=args.fork_source,
            pixi_executable=args.pixi_executable,
            sdim_python=args.sdim_python,
        )
    elif args.command == "controls":
        result = run_controls_supervisor(
            destination=args.destination,
            fork_source=args.fork_source,
            pixi_executable=args.pixi_executable,
            sdim_python=args.sdim_python,
        )
    elif args.command == "target":
        result = run_target_supervisor(
            destination=args.destination,
            controls_bundle=args.controls_bundle,
            fork_source=args.fork_source,
            pixi_executable=args.pixi_executable,
        )
    else:
        raise RuntimeError(f"unsupported supervisor command: {args.command!r}")
    print(
        json.dumps(
            result,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        flush=True,
    )
    return 0 if result["status"] in {"PASS", "completed"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
