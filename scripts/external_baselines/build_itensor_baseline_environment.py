#!/usr/bin/env python3
"""Build and lock the isolated ITensorMPS baseline environment.

Creates a repository-owned Julia project that installs ITensorMPS from the
pristine vendored clone at its pinned commit, then publishes an environment
lock in the same spirit as ``baseline-environment-qutip-linux-64.lock.json``.

Two disciplines are enforced rather than assumed:

* the pristine upstream clone is never activated and never written to -- the
  Julia project lives under ``scripts/external_baselines/itensor_project`` and
  the clone's cleanliness is re-checked after the install;
* the installed package is bound to that clone by tree hash AND by per-file
  digests of the named source anchors, because Julia has no ``direct_url.json``
  analogue to bind a VCS install the way the QuTiP leg does.

This builds a comparison environment.  It makes no scientific claim.
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
CLONE = REPO / "external" / "baselines" / "ITensorMPS.jl"
PROJECT = REPO / "scripts" / "external_baselines" / "itensor_project"
LOCK = REPO / "baseline-environment-itensor-linux-64.lock.json"
ENVIRONMENT = "ecs-baseline-itensor"
EXPECTED_COMMIT = "7ce812c42bfedcb3da1c250fdd5f19cb20394d4d"
LOCK_SCHEMA = "error_coupling_simulator.environment_lock.itensor_baseline.v1"
SOURCE_ANCHORS = ("src/mps.jl", "src/abstractmps.jl", "src/mpo.jl", "src/defaults.jl")


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


def git(*arguments: str, cwd: Path) -> str:
    completed = subprocess.run(
        ["git", *arguments], cwd=str(cwd), capture_output=True, text=True, check=True
    )
    return completed.stdout.strip()


def julia(script: str, *, conda: str, timeout: int = 3600) -> str:
    completed = subprocess.run(
        [conda, "run", "--no-capture-output", "-n", ENVIRONMENT, "julia",
         f"--project={PROJECT}", "-e", script],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"julia failed ({completed.returncode}):\n"
            f"{completed.stdout[-4000:]}\n{completed.stderr[-4000:]}"
        )
    return completed.stdout


def clone_is_pristine() -> bool:
    status = git("status", "--porcelain", "--untracked-files=all", cwd=CLONE)
    return status == ""


def preflight(conda: str) -> None:
    if not CLONE.is_dir():
        raise SystemExit(f"pristine clone missing: {CLONE}")
    head = git("rev-parse", "HEAD", cwd=CLONE)
    if head != EXPECTED_COMMIT:
        raise SystemExit(f"clone is at {head}, expected {EXPECTED_COMMIT}")
    if not clone_is_pristine():
        raise SystemExit("upstream clone is dirty; refusing to build against it")
    for anchor in SOURCE_ANCHORS:
        if not (CLONE / anchor).is_file():
            raise SystemExit(f"pinned source anchor missing: {anchor}")
    version = subprocess.run(
        [conda, "run", "-n", ENVIRONMENT, "julia", "--version"],
        capture_output=True, text=True, timeout=300,
    )
    if version.returncode != 0:
        raise SystemExit(f"julia unavailable in {ENVIRONMENT}: {version.stderr.strip()}")
    say(f"preflight ok: clone {head[:12]} pristine, {version.stdout.strip()}")


def conda_explicit_urls(conda: str) -> list[str]:
    completed = subprocess.run(
        [conda, "list", "-n", ENVIRONMENT, "--explicit", "--md5"],
        capture_output=True, text=True, timeout=600, check=True,
    )
    return [
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip().startswith("http")
    ]


def install(conda: str) -> None:
    PROJECT.mkdir(parents=True, exist_ok=True)
    say(f"installing ITensorMPS@{EXPECTED_COMMIT[:12]} into {PROJECT}")
    # Pkg.add(url=..., rev=...) records a tree-hash-bound entry; Pkg.develop
    # would record a machine-local path and bind nothing.
    julia(
        "using Pkg; "
        f'Pkg.add(url="{CLONE}", rev="{EXPECTED_COMMIT}"); '
        'Pkg.add("JSON"); '
        "Pkg.resolve(); Pkg.instantiate(); Pkg.precompile()",
        conda=conda,
    )


def installed_identity(conda: str) -> dict[str, Any]:
    script = (
        "using Pkg, JSON; "
        "deps = Pkg.dependencies(); "
        "entry = first(v for v in values(deps) if v.name == \"ITensorMPS\"); "
        "println(JSON.json(Dict("
        '"julia_version" => string(VERSION), '
        '"active_project" => Base.active_project(), '
        '"itensormps_version" => string(entry.version), '
        '"itensormps_tree_hash" => string(entry.tree_hash), '
        '"itensormps_source_path" => entry.source)))'
    )
    for line in julia(script, conda=conda).splitlines():
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise RuntimeError("could not read the installed ITensorMPS identity")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-install", action="store_true",
                        help="only re-emit the lock from an already built project")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    conda = shutil.which("conda") or "/home/cx/miniforge3/bin/conda"
    preflight(conda)

    if not args.skip_install:
        install(conda)

    if not clone_is_pristine():
        raise SystemExit(
            "FATAL: the upstream clone changed during the install; "
            "the pristine-upstream contract was violated"
        )
    say("upstream clone still pristine after install")

    identity = installed_identity(conda)
    manifest = PROJECT / "Manifest.toml"
    if not manifest.is_file():
        raise SystemExit(f"expected a resolved Manifest at {manifest}")

    installed_root = Path(identity["itensormps_source_path"])
    anchors: dict[str, str] = {}
    mismatches: list[str] = []
    for anchor in SOURCE_ANCHORS:
        clone_digest = file_sha256(CLONE / anchor)
        anchors[anchor] = clone_digest
        installed = installed_root / anchor
        if installed.is_file() and file_sha256(installed) != clone_digest:
            mismatches.append(anchor)
    if mismatches:
        raise SystemExit(
            "FATAL: installed sources differ from the pristine clone at "
            f"{mismatches}; the leg would not be comparing the pinned code"
        )
    say(f"installed sources byte-identical to the clone for {len(anchors)} anchors")

    lock = {
        "schema": LOCK_SCHEMA,
        "environment_name": ENVIRONMENT,
        "platform": "linux-64",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "julia_version": identity["julia_version"],
        "julia_project": str(PROJECT.relative_to(REPO)),
        "conda_explicit_urls": conda_explicit_urls(conda),
        "itensor_vcs": {
            "source_relative_to_repository": str(CLONE.relative_to(REPO)),
            "commit": EXPECTED_COMMIT,
            "installed_distribution_version": identity["itensormps_version"],
            "tree_hash": identity["itensormps_tree_hash"],
        },
        "manifest_sha256": file_sha256(manifest),
        "project_sha256": file_sha256(PROJECT / "Project.toml"),
        "source_anchor_sha256": anchors,
        "recreation_sequence": [
            f"conda create --name {ENVIRONMENT} -c conda-forge julia",
            "python scripts/external_baselines/build_itensor_baseline_environment.py",
        ],
        "claim_boundary": (
            "environment provenance only; it binds the running package to the "
            "pinned pristine clone and makes no claim about comparison results"
        ),
    }
    atomic_json(LOCK, lock)
    say(f"lock written: {LOCK.relative_to(REPO)}")
    say(f"  julia {lock['julia_version']}, ITensorMPS {identity['itensormps_version']}")
    say(f"  tree_hash {identity['itensormps_tree_hash']}")
    say(f"  manifest_sha256 {lock['manifest_sha256'][:16]}...")
    say(f"  conda explicit packages: {len(lock['conda_explicit_urls'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
