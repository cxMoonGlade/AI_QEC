#!/usr/bin/env python3
"""Synchronize the canonical Conda environment from the locked uv resolution."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    contract = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["aiqec"][
        "core-environment"
    ]
    environment_name = Path(sys.prefix).name
    if environment_name != contract["conda_environment"]:
        raise SystemExit(
            f"sync the canonical {contract['conda_environment']} environment, "
            f"not {environment_name}"
        )

    uv = Path(sys.prefix) / "bin" / "uv"
    if not uv.is_file():
        raise SystemExit(f"uv is missing at {uv}; update from environment-ecs.yml first")

    environment = os.environ.copy()
    # Conda does not set VIRTUAL_ENV.  Setting it explicitly makes --active
    # target this Conda prefix instead of creating or reusing repo-local .venv.
    environment["VIRTUAL_ENV"] = sys.prefix
    subprocess.run(
        [
            str(uv),
            "sync",
            "--active",
            "--locked",
            "--no-dev",
            "--extra",
            "cuda-extension",
            "--extra",
            "gpu-cu130",
            "--extra",
            "test",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
    )
    print(f"{contract['conda_environment']} synchronized from locked uv.lock")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
