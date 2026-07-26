#!/usr/bin/env python3
"""Record the isolated, commit-bound Quimb PEPS d5 environment.

This is an installed-state provenance lock.  Conda artifacts are recorded by
explicit SHA-256 URLs and every installed Python distribution is enumerated,
but the human-readable recreation sequence does not hash-pin every pip
transitive artifact.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any


REPO = Path(__file__).resolve().parents[2]
ENVIRONMENT = "ecs-baseline-quimb-peps"
LOCK_PATH = REPO / "baseline-environment-quimb-peps-linux-64.lock.json"
SCHEMA = "error_coupling_simulator.environment_lock.quimb_peps_d5.v2"
CLONE = REPO / "external" / "baselines" / "quimb"
EXPECTED_COMMIT = "3c89529fe0a3487133a3928201691161e110abdf"
EXPECTED_ORIGIN = "https://github.com/jcmgray/quimb.git"
SELECTED = {
    "autoray": "0.8.11",
    "cotengra": "0.8.2",
    "numpy": "2.4.6",
    "opt-einsum": "3.4.0",
    "quimb": "1.14.1.dev80+g3c89529fe",
    "scipy": "1.17.1",
    "torch": "2.12.0",
}


def _run(
    command: list[str],
    *,
    cwd: Path = REPO,
    timeout: int = 900,
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


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(
                payload,
                stream,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
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


def _clone_identity() -> dict[str, Any]:
    head = _run(["git", "rev-parse", "HEAD"], cwd=CLONE).strip()
    if head != EXPECTED_COMMIT:
        raise RuntimeError(f"Quimb clone is at {head}, expected {EXPECTED_COMMIT}")
    if (
        _run(["git", "rev-parse", "--is-shallow-repository"], cwd=CLONE).strip()
        != "false"
    ):
        raise RuntimeError("Quimb clone is shallow")
    status = _run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--ignored",
        ],
        cwd=CLONE,
    ).strip()
    if status:
        raise RuntimeError(f"Quimb clone is not pristine:\n{status}")
    origin = _run(["git", "remote", "get-url", "origin"], cwd=CLONE).strip()
    if origin != EXPECTED_ORIGIN:
        raise RuntimeError(f"unexpected Quimb origin: {origin!r}")
    return {
        "path_relative_to_repository": "external/baselines/quimb",
        "origin": origin,
        "commit": head,
        "tree": _run(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=CLONE
        ).strip(),
        "is_shallow": False,
        "pristine_including_ignored_paths": True,
    }


def _environment_identity(conda: str) -> dict[str, Any]:
    identity_script = (
        "import hashlib, importlib.metadata as md, json, pathlib, re, sys\n"
        "import quimb\n"
        f"selected = {SELECTED!r}\n"
        "prefix = pathlib.Path(sys.prefix).resolve(strict=True)\n"
        "origin_lexical = pathlib.Path(quimb.__file__).absolute()\n"
        "origin = origin_lexical.resolve(strict=True)\n"
        "if origin_lexical != origin:\n"
        "    raise RuntimeError('Quimb import origin traverses a symlink')\n"
        "if not origin.is_relative_to(prefix):\n"
        "    raise RuntimeError('Quimb import origin escapes Python prefix')\n"
        "package_root = origin.parent\n"
        "source_manifest = {}\n"
        "for item in sorted(package_root.rglob('*')):\n"
        "    if item.is_symlink():\n"
        "        raise RuntimeError(f'symlink in Quimb package: {item}')\n"
        "    if not item.is_file() or item.suffix != '.py':\n"
        "        continue\n"
        "    resolved = item.resolve(strict=True)\n"
        "    if not resolved.is_relative_to(package_root):\n"
        "        raise RuntimeError(f'Quimb source escapes package: {item}')\n"
        "    relative = resolved.relative_to(package_root).as_posix()\n"
        "    source_manifest[relative] = hashlib.sha256(\n"
        "        resolved.read_bytes()\n"
        "    ).hexdigest()\n"
        "if not source_manifest or '__init__.py' not in source_manifest:\n"
        "    raise RuntimeError('Quimb Python source manifest is incomplete')\n"
        "all_dists = {}\n"
        "all_records = {}\n"
        "selected_rows = {}\n"
        "project_distribution_present = False\n"
        "for dist in md.distributions():\n"
        "    raw_name = dist.metadata.get('Name') or ''\n"
        "    name = re.sub(r'[-_.]+', '-', raw_name).lower()\n"
        "    if not name:\n"
        "        continue\n"
        "    if name == 'error-coupling-simulator':\n"
        "        project_distribution_present = True\n"
        "        continue\n"
        "    if name in all_dists:\n"
        "        raise RuntimeError(f'duplicate distribution: {name}')\n"
        "    direct = None\n"
        "    record_path = None\n"
        "    for item in dist.files or ():\n"
        "        if item.name == 'direct_url.json':\n"
        "            direct = json.loads(item.read_text())\n"
        "        if item.name == 'RECORD' and '.dist-info' in str(item):\n"
        "            record_path = pathlib.Path(dist.locate_file(item))\n"
        "    row = {\n"
        "        'version': dist.version,\n"
        "        'direct_url': direct,\n"
        "        'record_sha256': (\n"
        "            hashlib.sha256(record_path.read_bytes()).hexdigest()\n"
        "            if record_path is not None else None\n"
        "        ),\n"
        "    }\n"
        "    all_dists[name] = dist.version\n"
        "    all_records[name] = row\n"
        "    if name in selected:\n"
        "        selected_rows[name] = row\n"
        "print(json.dumps({\n"
        "  'python_version': sys.version.split()[0],\n"
        "  'python_executable': sys.executable,\n"
        "  'python_prefix': sys.prefix,\n"
        "  'all_distributions': dict(sorted(all_dists.items())),\n"
        "  'all_distribution_records': dict(sorted(all_records.items())),\n"
        "  'selected_distributions': selected_rows,\n"
        "  'project_distribution_present': project_distribution_present,\n"
        "  'installed_quimb_source': {\n"
        "    'import_origin_relative_to_prefix': "
        "origin.relative_to(prefix).as_posix(),\n"
        "    'package_root_relative_to_prefix': "
        "package_root.relative_to(prefix).as_posix(),\n"
        "    'python_source_manifest_sha256': "
        "dict(sorted(source_manifest.items())),\n"
        "    'python_source_file_count': len(source_manifest),\n"
        "    'symlinks_rejected': True,\n"
        "    'prefix_escape_rejected': True,\n"
        "  },\n"
        "}, sort_keys=True))\n"
    )
    output = _run(
        [
            conda,
            "run",
            "-n",
            ENVIRONMENT,
            "python",
            "-c",
            identity_script,
        ]
    )
    payload = json.loads(
        next(line for line in output.splitlines() if line.startswith("{"))
    )
    if payload["project_distribution_present"]:
        raise RuntimeError("project distribution leaked into baseline environment")
    for name, version in SELECTED.items():
        observed = payload["selected_distributions"].get(name)
        if observed is None or observed["version"] != version:
            raise RuntimeError(
                f"{name}: observed {observed}, expected version {version}"
            )
    quimb_direct = payload["selected_distributions"]["quimb"]["direct_url"]
    vcs = (quimb_direct or {}).get("vcs_info", {})
    if (
        vcs.get("vcs") != "git"
        or vcs.get("commit_id") != EXPECTED_COMMIT
        or vcs.get("requested_revision") != EXPECTED_COMMIT
    ):
        raise RuntimeError(f"installed Quimb is not commit-bound: {quimb_direct}")
    return payload


def _conda_explicit_urls(conda: str) -> list[str]:
    output = _run(
        [conda, "list", "-n", ENVIRONMENT, "--explicit", "--sha256"]
    )
    return [
        line.strip()
        for line in output.splitlines()
        if line.strip().startswith("http")
    ]


def _cuda_probe(conda: str) -> dict[str, Any]:
    code = (
        "import json, torch\n"
        "payload={'available': torch.cuda.is_available(),"
        "'torch_version': torch.__version__,"
        "'torch_build_cuda': torch.version.cuda}\n"
        "if payload['available']:\n"
        " p=torch.cuda.get_device_properties(0);"
        " payload.update({'name':p.name,'total_memory_bytes':p.total_memory,"
        "'compute_capability':[p.major,p.minor]})\n"
        "print(json.dumps(payload,sort_keys=True))\n"
    )
    output = _run(
        [conda, "run", "-n", ENVIRONMENT, "python", "-c", code]
    )
    payload = json.loads(
        next(line for line in output.splitlines() if line.startswith("{"))
    )
    if not payload["available"]:
        raise RuntimeError("CUDA is unavailable in the Quimb PEPS environment")
    return payload


def main() -> int:
    conda = shutil.which("conda") or "/home/cx/miniforge3/bin/conda"
    identity = _environment_identity(conda)
    pip_check = _run(
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
    if pip_check != "No broken requirements found.":
        raise RuntimeError(f"pip check failed: {pip_check}")
    payload = {
        "schema": SCHEMA,
        "environment_name": ENVIRONMENT,
        "platform": "linux-64",
        "python_version": identity["python_version"],
        "conda_explicit_sha256_urls": _conda_explicit_urls(conda),
        "pip_distributions": identity["all_distributions"],
        "pip_distribution_records": identity["all_distribution_records"],
        "selected_distribution_records": identity["selected_distributions"],
        "installed_quimb_source": identity["installed_quimb_source"],
        "pip_check": pip_check,
        "cuda_probe": _cuda_probe(conda),
        "upstream": _clone_identity(),
        "recreation_sequence": [
            "conda create --name ecs-baseline-quimb-peps python=3.12.13",
            (
                "python -m pip install "
                "'git+file:///home/cx/AI_QEC/AI_QEC/external/baselines/"
                f"quimb@{EXPECTED_COMMIT}'"
            ),
            "python -m pip install torch==2.12.0",
            "python -m pip check",
        ],
        "recreation_sequence_is_fully_hash_pinned": False,
        "provenance_scope": {
            "installed_state_only": True,
            "quimb_vcs_commit_bound": True,
            "installed_quimb_python_source_bytes_bound": True,
            "fully_reproducible": False,
        },
        "claim_boundary": (
            "installed-state provenance for the isolated Quimb pure-state "
            "PEPS baseline only; not a simulator-product or scientific "
            "faithfulness verdict"
        ),
    }
    _atomic_json(LOCK_PATH, payload)
    print(
        f"wrote {LOCK_PATH}: python={payload['python_version']} "
        f"pip={len(payload['pip_distributions'])} "
        f"commit={payload['upstream']['commit']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
