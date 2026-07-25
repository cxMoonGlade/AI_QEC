#!/usr/bin/env python3
"""Emit environment locks for the Aer and YASTN MPS comparison legs.

``docs/service_status.json`` has long declared ``ecs-baseline-aer`` and
``ecs-baseline-yastn``, but only the QuTiP leg ever carried a committed lock.
Two of the three wired MPS legs were therefore not reproducible: the
environments simply did not exist on a fresh host, and nothing recorded how to
rebuild them.  This script closes that gap in the shape of
``baseline-environment-qutip-linux-64.lock.json``.

The two legs have deliberately different provenance models, and this script
records each leg's own model rather than forcing a single one:

* YASTN is installed from the pristine clone as a commit-pinned VCS install, so
  the lock carries ``direct_url`` VCS binding exactly like QuTiP.  A plain
  directory install produces ``dir_info`` instead and the leg rejects it.
* Aer runs the released wheel on purpose -- its orchestrator requires
  ``direct_url`` to be ABSENT -- so the lock records the distribution identity
  and the pristine clone commit that the code map reads, and states plainly
  that the runtime is not VCS-bound.

This records environment provenance.  It makes no scientific claim.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any
from uuid import uuid4

REPO = Path(__file__).resolve().parents[2]

LEGS: dict[str, dict[str, Any]] = {
    "aer": {
        "environment": "ecs-baseline-aer",
        "clone": "external/baselines/qiskit-aer",
        "commit": "837c3ef3c39248aae936580360c22224dcefb265",
        "distribution": "qiskit-aer",
        "version": "0.17.2",
        "import_name": "qiskit_aer",
        "vcs_bound": False,
        "lock": "baseline-environment-aer-linux-64.lock.json",
        "schema": "error_coupling_simulator.environment_lock.aer_baseline.v1",
        "pip_step": "python -m pip install qiskit-aer==0.17.2",
    },
    "yastn": {
        "environment": "ecs-baseline-yastn",
        "clone": "external/baselines/yastn",
        "commit": "595bd802ba0753a187b4bf7fd5c6d5007c0170d0",
        "distribution": "yastn",
        "version": "1.6.2.dev384+g595bd802b",
        "import_name": "yastn",
        "vcs_bound": True,
        "lock": "baseline-environment-yastn-linux-64.lock.json",
        "schema": "error_coupling_simulator.environment_lock.yastn_baseline.v1",
        "pip_step": (
            "python -m pip install "
            "git+file://<repo>/external/baselines/yastn@595bd802ba0753a187b4bf7fd5c6d5007c0170d0"
        ),
    },
}


def say(message: str) -> None:
    print(message, flush=True)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as stream:
            stream.write(canonical_bytes(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        temporary.unlink(missing_ok=True)


def run(command: list[str], *, timeout: int = 600) -> str:
    completed = subprocess.run(
        command, cwd=str(REPO), capture_output=True, text=True, timeout=timeout
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed: {' '.join(command)}\n{completed.stdout[-2000:]}\n"
            f"{completed.stderr[-2000:]}"
        )
    return completed.stdout


def clone_is_pristine(clone: Path) -> tuple[bool, str]:
    """Pristine means clean INCLUDING ignored build artefacts.

    ``git status --porcelain --untracked-files=all`` hides ignored paths, so a
    directory install that writes ``build/``, ``*.egg-info/`` or a generated
    ``_version.py`` into the clone passes that check while the tree is in fact
    polluted.  The comparison legs then fail much later with an opaque
    source-tree mismatch, so this script checks the honest condition.
    """

    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--ignored"],
        cwd=str(clone),
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return status == "", status


def conda_explicit_urls(conda: str, environment: str) -> list[str]:
    output = run(
        [conda, "list", "-n", environment, "--explicit", "--md5"], timeout=900
    )
    return [line.strip() for line in output.splitlines() if line.strip().startswith("http")]


def environment_identity(conda: str, leg: dict[str, Any]) -> dict[str, Any]:
    script = (
        "import json, sys, importlib, importlib.metadata as md\n"
        f"module = importlib.import_module({leg['import_name']!r})\n"
        f"dist = md.distribution({leg['distribution']!r})\n"
        "files = [p for p in (dist.files or []) if p.name == 'direct_url.json']\n"
        "direct = json.loads(files[0].read_text()) if files else None\n"
        "print(json.dumps({\n"
        "    'python_version': sys.version.split()[0],\n"
        "    'module_version': getattr(module, '__version__', None),\n"
        "    'distribution_version': dist.version,\n"
        "    'direct_url': direct,\n"
        "}))\n"
    )
    output = run(
        [conda, "run", "-n", leg["environment"], "python", "-c", script], timeout=600
    )
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise RuntimeError(f"could not read the {leg['environment']} identity")


def build_lock(conda: str, name: str, leg: dict[str, Any]) -> dict[str, Any]:
    clone = REPO / leg["clone"]
    if not clone.is_dir():
        raise SystemExit(f"pristine clone missing: {clone}")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(clone), capture_output=True, text=True, check=True
    ).stdout.strip()
    if head != leg["commit"]:
        raise SystemExit(f"{name} clone is at {head}, expected {leg['commit']}")
    pristine, status = clone_is_pristine(clone)
    if not pristine:
        raise SystemExit(
            f"{name} clone is polluted (ignored files included):\n{status}\n"
            "clean it before locking; the leg compares the installed tree to this clone"
        )

    identity = environment_identity(conda, leg)
    if identity["distribution_version"] != leg["version"]:
        raise SystemExit(
            f"{name} distribution is {identity['distribution_version']}, "
            f"expected {leg['version']}"
        )
    direct = identity["direct_url"]
    if leg["vcs_bound"]:
        vcs = (direct or {}).get("vcs_info")
        if not isinstance(vcs, dict) or vcs.get("commit_id") != leg["commit"]:
            raise SystemExit(
                f"{name} must be a commit-pinned VCS install; observed direct_url={direct!r}. "
                "Install with git+file://<clone>@<commit>, not a plain directory path."
            )
    elif direct is not None:
        raise SystemExit(
            f"{name} must run the released wheel with no direct_url; observed {direct!r}"
        )

    lock: dict[str, Any] = {
        "schema": leg["schema"],
        "environment_name": leg["environment"],
        "platform": "linux-64",
        "python_version": identity["python_version"],
        "conda_explicit_sha256_urls": conda_explicit_urls(conda, leg["environment"]),
        "upstream": {
            "source_relative_to_repository": leg["clone"],
            "commit": leg["commit"],
            "installed_distribution_version": identity["distribution_version"],
            "module_version": identity["module_version"],
            "runtime_is_vcs_bound": bool(leg["vcs_bound"]),
        },
        "recreation_sequence": [
            f"conda create --name {leg['environment']} python={identity['python_version']}",
            leg["pip_step"],
        ],
        "claim_boundary": (
            "environment provenance only; it records how to rebuild the comparison "
            "environment and makes no claim about comparison results"
        ),
    }
    if leg["vcs_bound"]:
        lock["upstream"]["direct_url"] = direct
    else:
        lock["upstream"]["provenance_claim_boundary"] = (
            "the runtime is the released wheel and is bound by distribution name and "
            "version only; the pinned clone is the source reference the code map reads, "
            "not the executed code"
        )
    return lock


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("legs", nargs="*", choices=sorted(LEGS))
    args = parser.parse_args()
    if not args.legs:
        args.legs = sorted(LEGS)
    return args


def main() -> int:
    args = parse_args()
    conda = shutil.which("conda") or "/home/cx/miniforge3/bin/conda"
    for name in args.legs:
        leg = LEGS[name]
        say(f"locking {leg['environment']}")
        lock = build_lock(conda, name, leg)
        destination = REPO / leg["lock"]
        atomic_json(destination, lock)
        say(
            f"  {destination.name}: python {lock['python_version']}, "
            f"{leg['distribution']} {lock['upstream']['installed_distribution_version']}, "
            f"{len(lock['conda_explicit_sha256_urls'])} conda packages, "
            f"vcs_bound={lock['upstream']['runtime_is_vcs_bound']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
