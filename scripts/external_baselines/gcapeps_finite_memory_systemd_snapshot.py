#!/usr/bin/env python3
"""ExecStopPost failure snapshot for finite-memory transient services."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
from typing import Any, Mapping, Sequence


SNAPSHOT_SCHEMA = (
    "error_coupling_simulator.external.gcapeps_finite_memory."
    "systemd_failure_snapshot.v1"
)
SNAPSHOT_FILENAME = "failure_snapshot.json"
SNAPSHOT_MAX_BYTES = 1_048_576
_LAUNCH_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,95}")
_COUNTER_FILES = (
    "memory.current",
    "memory.peak",
    "memory.swap.current",
    "pids.current",
    "pids.peak",
)
_MAP_FILES = ("memory.events", "pids.events", "cpu.stat")


def _strict_uint(raw: str, *, name: str) -> int:
    if not raw or not raw.isascii() or not raw.isdecimal():
        raise ValueError(f"{name} is not an unsigned decimal integer")
    return int(raw)


def _read_counter(path: Path) -> int:
    raw = path.read_text(encoding="ascii")
    if not raw.endswith("\n") or raw.count("\n") != 1:
        raise ValueError(f"{path.name} is not one canonical counter line")
    return _strict_uint(raw[:-1], name=path.name)


def _read_map(path: Path) -> dict[str, int]:
    result: dict[str, int] = {}
    raw = path.read_text(encoding="ascii")
    if not raw.endswith("\n"):
        raise ValueError(f"{path.name} lacks its terminal newline")
    for index, line in enumerate(raw.splitlines()):
        fields = line.split(" ")
        if (
            len(fields) != 2
            or not fields[0]
            or fields[0] in result
            or not fields[0].isascii()
        ):
            raise ValueError(f"{path.name} line {index} is malformed")
        result[fields[0]] = _strict_uint(
            fields[1],
            name=f"{path.name}.{fields[0]}",
        )
    if not result:
        raise ValueError(f"{path.name} is empty")
    return dict(sorted(result.items()))


def own_cgroup_path(
    *,
    proc_cgroup: Path = Path("/proc/self/cgroup"),
    cgroup_root: Path = Path("/sys/fs/cgroup"),
) -> Path:
    lines = proc_cgroup.read_text(encoding="ascii").splitlines()
    matches = [line[3:] for line in lines if line.startswith("0::/")]
    if len(matches) != 1:
        raise RuntimeError("process does not have exactly one cgroup-v2 path")
    relative = matches[0]
    if "\x00" in relative or any(part in ("", ".", "..") for part in relative.split("/")):
        raise RuntimeError("process cgroup path is not canonical")
    candidate = cgroup_root.joinpath(*relative.split("/"))
    resolved_root = cgroup_root.resolve(strict=True)
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(resolved_root) or not resolved.is_dir():
        raise RuntimeError("resolved cgroup path escaped the unified root")
    return resolved


def read_live_cgroup(cgroup: Path) -> dict[str, Any]:
    counters = {
        name.replace(".", "_"): _read_counter(cgroup / name)
        for name in _COUNTER_FILES
    }
    mappings = {
        name.replace(".", "_"): _read_map(cgroup / name)
        for name in _MAP_FILES
    }
    return {**counters, **mappings}


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _projection(payload: Mapping[str, Any]) -> str:
    projected = dict(payload)
    projected.pop("result_projection_sha256", None)
    return hashlib.sha256(canonical_json_bytes(projected)).hexdigest()


def build_snapshot(
    *,
    launch_id: str,
    service_result: str,
    exit_code: str,
    exit_status: str,
    invocation_id: str,
    cgroup: Path,
) -> dict[str, Any]:
    if _LAUNCH_ID.fullmatch(launch_id) is None:
        raise ValueError("launch_id is invalid")
    for name, value in (
        ("service_result", service_result),
        ("exit_code", exit_code),
        ("exit_status", exit_status),
        ("invocation_id", invocation_id),
    ):
        if not isinstance(value, str) or not value or "\x00" in value:
            raise ValueError(f"{name} must be a nonempty string")
    payload = {
        "schema": SNAPSHOT_SCHEMA,
        "launch_id": launch_id,
        "service_result": service_result,
        "exit_code": exit_code,
        "exit_status": exit_status,
        "invocation_id": invocation_id,
        "cgroup_path": str(cgroup),
        "live_cgroup": read_live_cgroup(cgroup),
        "result_projection_sha256": "",
    }
    payload["result_projection_sha256"] = _projection(payload)
    return payload


def publish_snapshot_and_stop(
    payload: Mapping[str, Any],
    *,
    runtime_directory: Path,
    stop_process=os.kill,
) -> None:
    expected_name = f"gcapeps-fm-{payload['launch_id']}"
    if runtime_directory.name != expected_name:
        raise ValueError("runtime directory does not match launch_id")
    lexical = runtime_directory.absolute()
    resolved = lexical.resolve(strict=True)
    if lexical != resolved or not resolved.is_dir():
        raise ValueError("runtime directory must be an existing nonsymlink directory")
    directory_fd = os.open(
        resolved,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    file_fd = -1
    try:
        raw = canonical_json_bytes(payload)
        if len(raw) > SNAPSHOT_MAX_BYTES:
            raise ValueError("failure snapshot exceeds its byte cap")
        file_fd = os.open(
            SNAPSHOT_FILENAME,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | os.O_CLOEXEC,
            0o644,
            dir_fd=directory_fd,
        )
        written = 0
        while written < len(raw):
            count = os.write(file_fd, raw[written:])
            if count <= 0:
                raise OSError("short failure-snapshot write")
            written += count
        os.fsync(file_fd)
        identity = os.fstat(file_fd)
        if (
            not stat.S_ISREG(identity.st_mode)
            or stat.S_IMODE(identity.st_mode) != 0o644
            or identity.st_nlink != 1
            or identity.st_uid != os.geteuid()
            or identity.st_size != len(raw)
        ):
            raise RuntimeError("failure snapshot inode identity is invalid")
        os.fsync(directory_fd)
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        os.close(directory_fd)
    stop_process(os.getpid(), signal.SIGSTOP)


def _environment(name: str) -> str:
    value = os.environ.get(name)
    if value is None or not value:
        raise RuntimeError(f"missing ExecStopPost environment {name}")
    return value


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--launch-id", required=True)
    arguments = parser.parse_args(argv)
    service_result = _environment("SERVICE_RESULT")
    if service_result == "success":
        return 0
    cgroup = own_cgroup_path()
    payload = build_snapshot(
        launch_id=arguments.launch_id,
        service_result=service_result,
        exit_code=_environment("EXIT_CODE"),
        exit_status=_environment("EXIT_STATUS"),
        invocation_id=_environment("INVOCATION_ID"),
        cgroup=cgroup,
    )
    publish_snapshot_and_stop(
        payload,
        runtime_directory=Path(f"/run/gcapeps-fm-{arguments.launch_id}"),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
