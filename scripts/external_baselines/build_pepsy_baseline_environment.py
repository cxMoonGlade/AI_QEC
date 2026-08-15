#!/usr/bin/env python3
"""Build and lock the isolated, commit-bound Pepsy PEPS environment.

The executed Pepsy distribution is installed from the pristine full clone by
an exact VCS revision.  The lock records the complete observed Python
distribution metadata, exact Conda package URLs, selected source-tree
identity, and the pristine upstream commit/tree.  It is installed-state
provenance for an external baseline, not a scientific result.

The optional ``--create`` path clones the already isolated Quimb-PEPS
environment because that environment owns the CUDA 13 PyTorch/Quimb stack on
this host.  This bootstrap and the two PyPI wheels are not byte-hash-pinned,
so the emitted lock states that recreation is not fully reproducible.  A
claim-bearing worker instead requires exact conformance to the observed lock.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Mapping


REPO = Path(__file__).resolve().parents[2]
CLONE = REPO / "external" / "baselines" / "pepsy"
LOCK = REPO / "baseline-environment-pepsy-linux-64.lock.json"
ENVIRONMENT = "ecs-baseline-pepsy"
BOOTSTRAP_ENVIRONMENT = "ecs-baseline-quimb-peps"
EXPECTED_ORIGIN = "https://github.com/quantinuum-dev/pepsy.git"
EXPECTED_COMMIT = "27cb956ec88a739daece90407833bd3c3f8e1d8f"
EXPECTED_TREE = "933de533b0fb4775987656f4a18adefbcdcbf2a9"
LOCK_SCHEMA = (
    "error_coupling_simulator.environment_lock.pepsy_peps_d5.v1"
)
PINNED_PYPI_DEPENDENCIES = ("cotengrust==0.2.1", "cmaes==0.13.0")
SELECTED_DISTRIBUTIONS = (
    "autoray",
    "cmaes",
    "cotengra",
    "cotengrust",
    "numpy",
    "pepsy",
    "quimb",
    "scipy",
    "torch",
    "tqdm",
)
SOURCE_ANCHORS = (
    "src/pepsy/__init__.py",
    "src/pepsy/boundary/metrics.py",
    "src/pepsy/operators/gates.py",
    "src/pepsy/optimizers/peps/optimizer.py",
    "src/pepsy/tensors/core.py",
)


def _say(message: str) -> None:
    print(message, flush=True)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_canonical_bytes(value) + b"\n")
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
    command: list[str],
    *,
    cwd: Path = REPO,
    timeout: int = 1800,
) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(command)}\n"
            f"{completed.stdout[-4000:]}\n{completed.stderr[-4000:]}"
        )
    return completed.stdout


def _git(*arguments: str) -> str:
    return _run(["git", *arguments], cwd=CLONE).strip()


def _source_reference() -> dict[str, Any]:
    if not CLONE.is_dir():
        raise RuntimeError(f"missing Pepsy full clone: {CLONE}")
    commit = _git("rev-parse", "HEAD")
    tree = _git("rev-parse", "HEAD^{tree}")
    origin = _git("remote", "get-url", "origin")
    if commit != EXPECTED_COMMIT:
        raise RuntimeError(
            f"Pepsy clone is at {commit}, expected {EXPECTED_COMMIT}"
        )
    if tree != EXPECTED_TREE:
        raise RuntimeError(
            f"Pepsy clone tree is {tree}, expected {EXPECTED_TREE}"
        )
    if origin != EXPECTED_ORIGIN:
        raise RuntimeError(
            f"Pepsy clone origin is {origin!r}, expected {EXPECTED_ORIGIN!r}"
        )
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
            "Pepsy clone is not pristine (ignored paths included):\n"
            f"{status}"
        )
    return {
        "source_relative_to_repository": str(CLONE.relative_to(REPO)),
        "origin": origin,
        "commit": commit,
        "tree": tree,
        "is_shallow": False,
        "pristine_including_ignored_paths": True,
        "license_sha256": _file_sha256(CLONE / "LICENSE"),
        "runtime_is_vcs_bound": True,
    }


def _normalize_distribution_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _identity_script() -> str:
    return r"""
import hashlib
import importlib.metadata as metadata
import json
import pathlib
import re
import sys

def normalize(name):
    return re.sub(r"[-_.]+", "-", name).lower()

rows = {}
for distribution in metadata.distributions():
    raw_name = distribution.metadata.get("Name")
    if not raw_name:
        continue
    name = normalize(raw_name)
    if name in rows:
        raise RuntimeError(f"duplicate installed distribution: {name}")
    direct_url = None
    record_path = None
    for item in distribution.files or ():
        if item.name == "direct_url.json":
            direct_url = json.loads(item.read_text())
        if item.name == "RECORD" and ".dist-info" in str(item):
            record_path = pathlib.Path(distribution.locate_file(item))
    rows[name] = {
        "version": distribution.version,
        "direct_url": direct_url,
        "record_sha256": (
            hashlib.sha256(record_path.read_bytes()).hexdigest()
            if record_path is not None
            else None
        ),
    }

print(json.dumps({
    "python_version": sys.version.split()[0],
    "python_executable": sys.executable,
    "python_prefix": sys.prefix,
    "distributions": dict(sorted(rows.items())),
}, allow_nan=False, sort_keys=True))
"""


def _environment_identity(conda: str) -> dict[str, Any]:
    output = _run(
        [
            conda,
            "run",
            "-n",
            ENVIRONMENT,
            "python",
            "-c",
            _identity_script(),
        ]
    )
    payload = json.loads(
        next(line for line in output.splitlines() if line.startswith("{"))
    )
    prefix = Path(payload["python_prefix"]).resolve()
    executable = Path(payload["python_executable"]).resolve()
    try:
        executable.relative_to(prefix)
    except ValueError as error:
        raise RuntimeError("environment Python escapes its prefix") from error
    if prefix.name != ENVIRONMENT:
        raise RuntimeError(
            f"unexpected environment prefix {prefix}; expected {ENVIRONMENT}"
        )
    rows = payload["distributions"]
    missing = sorted(set(SELECTED_DISTRIBUTIONS) - set(rows))
    if missing:
        raise RuntimeError(f"missing selected distributions: {missing}")
    pepsy_vcs = (rows["pepsy"]["direct_url"] or {}).get("vcs_info", {})
    if (
        pepsy_vcs.get("vcs") != "git"
        or pepsy_vcs.get("commit_id") != EXPECTED_COMMIT
        or pepsy_vcs.get("requested_revision") != EXPECTED_COMMIT
    ):
        raise RuntimeError(
            "installed Pepsy is not bound to the expected VCS revision: "
            f"{rows['pepsy']['direct_url']!r}"
        )
    return payload


def _tracked_package_sources() -> tuple[str, ...]:
    names = _git("ls-files", "src/pepsy").splitlines()
    sources = tuple(
        sorted(
            name
            for name in names
            if name.endswith((".py", ".json", ".toml", ".txt"))
            and (CLONE / name).is_file()
        )
    )
    if not sources:
        raise RuntimeError("Pepsy tracked package-source inventory is empty")
    return sources


def _source_tree_identity(
    environment_prefix: Path,
    *,
    python_version: str,
) -> dict[str, Any]:
    major_minor = ".".join(python_version.split(".")[:2])
    installed_root = (
        environment_prefix
        / "lib"
        / f"python{major_minor}"
        / "site-packages"
    )
    relative_hashes: dict[str, str] = {}
    mismatches: list[str] = []
    for clone_relative in _tracked_package_sources():
        package_relative = clone_relative.removeprefix("src/")
        clone_hash = _file_sha256(CLONE / clone_relative)
        installed_path = installed_root / package_relative
        if not installed_path.is_file():
            mismatches.append(f"{package_relative}:missing")
            continue
        installed_hash = _file_sha256(installed_path)
        if installed_hash != clone_hash:
            mismatches.append(f"{package_relative}:content")
            continue
        relative_hashes[package_relative] = clone_hash
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
    anchor_hashes = {
        anchor.removeprefix("src/"): relative_hashes[
            anchor.removeprefix("src/")
        ]
        for anchor in SOURCE_ANCHORS
    }
    return {
        "tracked_source_file_count": len(relative_hashes),
        "tracked_source_manifest_sha256": digest.hexdigest(),
        "source_anchor_sha256": anchor_hashes,
        "installed_source_root": str(installed_root / "pepsy"),
        "all_tracked_package_sources_match_pristine_clone": True,
    }
def _conda_explicit_urls(conda: str) -> list[str]:
    output = _run(
        [
            conda,
            "list",
            "-n",
            ENVIRONMENT,
            "--explicit",
            "--sha256",
        ]
    )
    urls = [
        line.strip()
        for line in output.splitlines()
        if line.strip().startswith("http")
    ]
    if not urls or any("#" not in url for url in urls):
        raise RuntimeError("Conda explicit package URLs are not SHA-256 bound")
    return urls


def _pip_freeze(conda: str) -> list[str]:
    output = _run(
        [
            conda,
            "run",
            "-n",
            ENVIRONMENT,
            "python",
            "-m",
            "pip",
            "freeze",
            "--all",
        ]
    )
    return sorted(line.strip() for line in output.splitlines() if line.strip())


def _pip_check(conda: str) -> str:
    return _run(
        [
            conda,
            "run",
            "-n",
            ENVIRONMENT,
            "python",
            "-m",
            "pip",
            "check",
        ]
    ).strip()


def _environment_exists(conda: str, name: str) -> bool:
    payload = json.loads(_run([conda, "env", "list", "--json"]))
    return any(Path(prefix).name == name for prefix in payload["envs"])


def _create_environment(conda: str) -> None:
    if _environment_exists(conda, ENVIRONMENT):
        raise RuntimeError(
            f"refusing to replace existing environment {ENVIRONMENT}"
        )
    if not _environment_exists(conda, BOOTSTRAP_ENVIRONMENT):
        raise RuntimeError(
            f"bootstrap environment is missing: {BOOTSTRAP_ENVIRONMENT}"
        )
    _say(
        f"cloning {BOOTSTRAP_ENVIRONMENT} into isolated {ENVIRONMENT}"
    )
    _run(
        [
            conda,
            "create",
            "--name",
            ENVIRONMENT,
            "--clone",
            BOOTSTRAP_ENVIRONMENT,
            "--yes",
        ],
        timeout=3600,
    )


def _install_environment(conda: str) -> None:
    if not _environment_exists(conda, ENVIRONMENT):
        raise RuntimeError(
            f"environment is missing; run with --create: {ENVIRONMENT}"
        )
    _run(
        [
            conda,
            "run",
            "--no-capture-output",
            "-n",
            ENVIRONMENT,
            "python",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            *PINNED_PYPI_DEPENDENCIES,
        ]
    )
    source_url = f"git+file://{CLONE}@{EXPECTED_COMMIT}"
    _run(
        [
            conda,
            "run",
            "--no-capture-output",
            "-n",
            ENVIRONMENT,
            "python",
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-deps",
            f"pepsy @ {source_url}",
        ],
        timeout=3600,
    )


def _selected_records(
    distributions: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        name: distributions[_normalize_distribution_name(name)]
        for name in SELECTED_DISTRIBUTIONS
    }


def _build_lock(conda: str) -> dict[str, Any]:
    source = _source_reference()
    identity = _environment_identity(conda)
    prefix = Path(identity["python_prefix"]).resolve()
    source_tree = _source_tree_identity(
        prefix,
        python_version=identity["python_version"],
    )
    pip_check = _pip_check(conda)
    if pip_check != "No broken requirements found.":
        raise RuntimeError(f"pip check did not pass: {pip_check!r}")
    distributions = identity["distributions"]
    return {
        "schema": LOCK_SCHEMA,
        "environment_name": ENVIRONMENT,
        "platform": "linux-64",
        "python_version": identity["python_version"],
        "environment_prefix_at_lock_time": str(prefix),
        "conda_explicit_sha256_urls": _conda_explicit_urls(conda),
        "pip_freeze_all": _pip_freeze(conda),
        "pip_distribution_records": distributions,
        "selected_distribution_records": _selected_records(distributions),
        "pip_check": pip_check,
        "upstream": source,
        "installed_pepsy_source": source_tree,
        "recreation_sequence": [
            (
                f"conda create --name {ENVIRONMENT} --clone "
                f"{BOOTSTRAP_ENVIRONMENT}"
            ),
            (
                f"conda run -n {ENVIRONMENT} python -m pip install "
                + " ".join(PINNED_PYPI_DEPENDENCIES)
            ),
            (
                f"conda run -n {ENVIRONMENT} python -m pip install "
                "--no-deps 'pepsy @ "
                "git+file://<repo>/external/baselines/pepsy"
                f"@{EXPECTED_COMMIT}'"
            ),
            f"conda run -n {ENVIRONMENT} python -m pip check",
        ],
        "recreation_sequence_is_fully_hash_pinned": False,
        "runtime_lock_conformance_policy": {
            "conda_explicit_urls_exact": True,
            "pip_freeze_exact": True,
            "pip_distribution_records_exact": True,
            "pepsy_vcs_revision_exact": True,
            "all_tracked_pepsy_package_sources_match_clone": True,
        },
        "claim_boundary": (
            "installed-state provenance for the isolated external Pepsy "
            "pure-state adapter only; the bootstrap and PyPI wheel bytes are "
            "not fully hash-pinned, and this lock makes no fidelity, Record, "
            "QEC, leakage, calibration, scalability, or product claim"
        ),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--create",
        action="store_true",
        help=(
            f"clone {BOOTSTRAP_ENVIRONMENT} into a new {ENVIRONMENT}"
        ),
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="install the pinned PyPI dependencies and Pepsy VCS revision",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    conda = os.environ.get("CONDA_EXE") or shutil.which("conda")
    if conda is None:
        raise RuntimeError("could not locate conda")
    _source_reference()
    if args.create:
        _create_environment(conda)
    if args.install:
        _install_environment(conda)
    lock = _build_lock(conda)
    _atomic_json(LOCK, lock)
    if _git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignored",
    ):
        raise RuntimeError("Pepsy clone changed while building the environment")
    _say(f"wrote {LOCK.relative_to(REPO)}")
    _say(
        "  "
        f"python={lock['python_version']} "
        f"pepsy={lock['selected_distribution_records']['pepsy']['version']} "
        f"pip_distributions={len(lock['pip_distribution_records'])} "
        f"conda_packages={len(lock['conda_explicit_sha256_urls'])}"
    )
    _say(
        "  "
        f"commit={EXPECTED_COMMIT} tree={EXPECTED_TREE} "
        "tracked_sources_match=true"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
