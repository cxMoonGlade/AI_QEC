#!/usr/bin/env python3
"""Record the isolated CUDA-Q QEC and PECOS XZZX capability environments.

Both probes execute index-installed distributions with no ``direct_url``
metadata.  That does not prove whether pip selected a wheel or built an sdist.
The pristine upstream clones are pinned source references, not a claim that
installed bytes equal either clone.  The locks capture the full installed
distribution set, selected RECORD hashes, Conda base packages, and the
compatibility pins needed on this CUDA 13 host.

These are installed-state provenance locks, not fully hash-pinned recreation
locks.  They do not promote an external probe into simulator acceptance.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any


REPO = Path(__file__).resolve().parents[2]
ENVIRONMENTS: dict[str, dict[str, Any]] = {
    "cudaq-qec": {
        "environment": "ecs-baseline-cudaq-qec",
        "schema": (
            "error_coupling_simulator.environment_lock."
            "cudaq_qec_xzzx_capability.v1"
        ),
        "lock": "baseline-environment-cudaq-qec-linux-64.lock.json",
        "clone": "external/baselines/cudaqx-qec-0.6.0",
        "commit": "84d18ca948a8582afe54035c85e2aceb3f3bee19",
        "selected": {
            "cudaq-qec": "0.6.0",
            "cudaq-qec-cu13": "0.6.0",
            "cuda-quantum-cu13": "0.14.2",
            "cutensornet-cu13": "2.12.2",
            "cupy-cuda13x": "13.6.0",
            "stim": "1.16.0",
        },
        "recreation": [
            "conda create --name ecs-baseline-cudaq-qec python=3.12.13",
            (
                "python -m pip install cudaq-qec==0.6.0 "
                "cudaq-qec-cu13==0.6.0 stim==1.16.0"
            ),
            "python -m pip install cutensornet-cu13==2.12.2",
            "python -m pip check",
        ],
        "compatibility": {
            "cutensornet-cu13": "2.12.2",
            "reason": (
                "2.13.0 caused CUTENSORNET_STATUS_INVALID_VALUE/native aborts "
                "for minimal MPS measurement-reset kernels on this stack; "
                "2.12.2 passed repeated controls"
            ),
        },
    },
    "pecos": {
        "environment": "ecs-baseline-pecos",
        "schema": (
            "error_coupling_simulator.environment_lock."
            "pecos_xzzx_capability.v1"
        ),
        "lock": "baseline-environment-pecos-linux-64.lock.json",
        "clone": "external/baselines/PECOS",
        "commit": "fa974197f0debd6478343c760af47f6faa4f04d2",
        "selected": {
            "quantum-pecos": "0.9.0.dev2",
            "pecos-rslib": "0.9.0.dev2",
            "pecos-rslib-llvm": "0.9.0.dev2",
            "pytket-cutensornet": "0.12.1",
            "cupy-cuda13x": "14.1.1",
            "cuquantum-python-cu13": "26.6.0",
            "cutensornet-cu13": "2.13.0",
            "cuda-toolkit": "13.3.1",
            "nvidia-cublas": "13.6.0.2",
            "nvidia-cusolver": "12.2.6.9",
            "stim": "1.16.0",
        },
        "recreation": [
            "conda create --name ecs-baseline-pecos python=3.13.14",
            (
                "python -m pip install "
                "'quantum-pecos[cuda13]==0.9.0.dev2' stim==1.16.0 "
                "nvidia-cublas==13.6.0.2"
            ),
            "python -m pip install 'cupy-cuda13x[ctk]==14.1.1'",
            "python -m pip check",
        ],
        "compatibility": {
            "runtime_library_path": (
                "<env>/lib/python3.13/site-packages/nvidia/cu13/lib"
            ),
            "reason": (
                "the released CUDA extra needs the pip CUDA toolkit libraries "
                "and that environment-local directory on LD_LIBRARY_PATH"
            ),
        },
    },
}


def _run(command: list[str], *, cwd: Path = REPO, timeout: int = 900) -> str:
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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(
                value,
                stream,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            stream.write("\n")
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


def _source_reference(config: dict[str, Any]) -> dict[str, Any]:
    clone = REPO / config["clone"]
    if not clone.is_dir():
        raise RuntimeError(f"missing upstream clone: {clone}")
    commit = _run(["git", "rev-parse", "HEAD"], cwd=clone).strip()
    if commit != config["commit"]:
        raise RuntimeError(
            f"{clone} is at {commit}, expected {config['commit']}"
        )
    status = _run(
        [
            "git",
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--ignored",
        ],
        cwd=clone,
    ).strip()
    if status:
        raise RuntimeError(
            f"upstream clone is not pristine (ignored paths included):\n{status}"
        )
    tree = _run(["git", "rev-parse", "HEAD^{tree}"], cwd=clone).strip()
    return {
        "source_relative_to_repository": config["clone"],
        "commit": commit,
        "tree": tree,
        "pristine_including_ignored_paths": True,
        "runtime_is_vcs_bound": False,
        "provenance_claim_boundary": (
            "the runtime uses index-installed distributions with no direct_url "
            "metadata; wheel-vs-sdist provenance and byte identity are not "
            "attested, and this pristine commit is only the inspected source "
            "reference"
        ),
    }


def _environment_identity(
    conda: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    selected = config["selected"]
    identity_script = (
        "import hashlib, importlib.metadata as md, json, pathlib, sys\n"
        f"selected = {selected!r}\n"
        "all_dists = {}\n"
        "selected_rows = {}\n"
        "for dist in md.distributions():\n"
        "    name = (dist.metadata.get('Name') or '').lower()\n"
        "    if not name or name == 'error-coupling-simulator':\n"
        "        continue\n"
        "    all_dists[name] = dist.version\n"
        "    if name not in selected:\n"
        "        continue\n"
        "    direct = None\n"
        "    record_path = None\n"
        "    for item in dist.files or ():\n"
        "        if item.name == 'direct_url.json':\n"
        "            direct = json.loads(item.read_text())\n"
        "        if item.name == 'RECORD' and '.dist-info' in str(item):\n"
        "            record_path = pathlib.Path(dist.locate_file(item))\n"
        "    selected_rows[name] = {\n"
        "        'version': dist.version,\n"
        "        'direct_url': direct,\n"
        "        'record_sha256': hashlib.sha256(record_path.read_bytes()).hexdigest(),\n"
        "    }\n"
        "print(json.dumps({\n"
        "  'python_version': sys.version.split()[0],\n"
        "  'python_executable': sys.executable,\n"
        "  'python_prefix': sys.prefix,\n"
        "  'all_distributions': dict(sorted(all_dists.items())),\n"
        "  'selected_distributions': selected_rows,\n"
        "}, sort_keys=True))\n"
    )
    output = _run(
        [
            conda,
            "run",
            "-n",
            config["environment"],
            "python",
            "-c",
            identity_script,
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
    for name, expected_version in selected.items():
        observed = payload["selected_distributions"].get(name)
        if observed is None or observed["version"] != expected_version:
            raise RuntimeError(
                f"{name}: observed {observed}, expected {expected_version}"
            )
        if observed["direct_url"] is not None:
            raise RuntimeError(
                f"{name} must be index-installed with no direct_url metadata, "
                f"got {observed['direct_url']}"
            )
    return payload


def _conda_urls(conda: str, environment: str) -> list[str]:
    output = _run(
        [conda, "list", "-n", environment, "--explicit", "--sha256"]
    )
    return [
        line.strip()
        for line in output.splitlines()
        if line.strip().startswith("http")
    ]


def _build_lock(conda: str, config: dict[str, Any]) -> dict[str, Any]:
    identity = _environment_identity(conda, config)
    check = _run(
        [
            conda,
            "run",
            "-n",
            config["environment"],
            "python",
            "-m",
            "pip",
            "check",
        ]
    ).strip()
    return {
        "schema": config["schema"],
        "environment_name": config["environment"],
        "platform": "linux-64",
        "python_version": identity["python_version"],
        "conda_explicit_sha256_urls": _conda_urls(
            conda,
            config["environment"],
        ),
        "pip_distributions": identity["all_distributions"],
        "selected_distribution_records": identity["selected_distributions"],
        "pip_check": check,
        "upstream": _source_reference(config),
        "compatibility": config["compatibility"],
        "recreation_sequence": config["recreation"],
        "recreation_sequence_is_fully_hash_pinned": False,
        "provenance_scope": {
            "installed_state_only": True,
            "fully_reproducible": False,
            "wheel_bytes_attested": False,
        },
        "recreation_claim_boundary": (
            "the sequence installs the selected top-level distributions and "
            "compatibility overrides; pip_distributions records the observed "
            "full state but the sequence does not hash-pin every transitive "
            "artifact"
        ),
        "claim_boundary": (
            "installed-state provenance for an external execution-capability "
            "probe only; not fully reproducible, does not attest wheel bytes, "
            "and makes no simulator-product or scientific-faithfulness claim"
        ),
    }


def main() -> int:
    conda = shutil.which("conda") or "/home/cx/miniforge3/bin/conda"
    for name, config in ENVIRONMENTS.items():
        print(f"locking {config['environment']}", flush=True)
        lock = _build_lock(conda, config)
        destination = REPO / config["lock"]
        _atomic_json(destination, lock)
        print(
            f"  {name}: python={lock['python_version']} "
            f"pip={len(lock['pip_distributions'])} "
            f"conda={len(lock['conda_explicit_sha256_urls'])}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
