#!/usr/bin/env python3
"""Fail closed when the active core GPU environment drifts from pyproject.toml."""

from __future__ import annotations

from importlib import metadata, util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib
from urllib.parse import unquote, urlparse

import yaml


ROOT = Path(__file__).resolve().parents[1]


def _normalise(name: str) -> str:
    return name.lower().replace("_", "-")


def main() -> int:
    contract = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["aiqec"][
        "core-environment"
    ]
    errors: list[str] = []

    actual_environment = Path(sys.prefix).name
    if actual_environment != contract["conda_environment"]:
        errors.append(
            f"Conda environment: expected {contract['conda_environment']}, "
            f"got {actual_environment}"
        )
    if os.environ.get("CONDA_DEFAULT_ENV") != contract["conda_environment"]:
        errors.append(
            f"CONDA_DEFAULT_ENV: expected {contract['conda_environment']}, "
            f"got {os.environ.get('CONDA_DEFAULT_ENV')}"
        )

    conda_manifest = yaml.safe_load((ROOT / "environment-ecs.yml").read_text())
    if conda_manifest.get("name") != contract["conda_environment"]:
        errors.append("environment-ecs.yml: canonical environment name drifted")
    if conda_manifest.get("channels") != ["conda-forge", "nodefaults"]:
        errors.append("environment-ecs.yml: expected conda-forge plus nodefaults")
    conda_dependencies = set(conda_manifest.get("dependencies", []))
    expected_conda_dependencies = {
        f"python={contract['python']}",
        f"pip={contract['pip']}",
        f"uv={contract['uv']}",
    }
    if conda_dependencies != expected_conda_dependencies:
        errors.append(
            "environment-ecs.yml dependencies: expected "
            f"{sorted(expected_conda_dependencies)}, got {sorted(conda_dependencies)}"
        )

    core_pins: dict[str, str] = {}
    for raw_line in (ROOT / "core-environment-cu130.lock").read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        requirement, version = line.split("==", maxsplit=1)
        name = _normalise(requirement.split("[", maxsplit=1)[0])
        if name in core_pins:
            errors.append(f"core lock {name}: duplicate pin")
        core_pins[name] = version

    contract_versions = {
        _normalise(name): version for name, version in contract["versions"].items()
    }
    if set(core_pins) != set(contract_versions):
        errors.append(
            "core lock package set drifted: "
            f"missing={sorted(set(contract_versions) - set(core_pins))}, "
            f"extra={sorted(set(core_pins) - set(contract_versions))}"
        )

    uv_data = tomllib.loads((ROOT / "uv.lock").read_text())
    uv_versions: dict[str, set[str]] = {}
    for package in uv_data["package"]:
        uv_versions.setdefault(_normalise(package["name"]), set()).add(package["version"])

    for name, expected in contract["versions"].items():
        normalised = _normalise(name)
        if core_pins.get(normalised) != expected:
            errors.append(
                f"core lock {name}: expected {expected}, got {core_pins.get(normalised)}"
            )
        if expected not in uv_versions.get(normalised, set()):
            errors.append(
                f"uv.lock {name}: expected {expected}, got {sorted(uv_versions.get(normalised, set()))}"
            )

    actual_python = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    if actual_python != contract["python"]:
        errors.append(f"python: expected {contract['python']}, got {actual_python}")
    for tool_name in ("pip", "uv"):
        try:
            actual_tool = metadata.version(tool_name)
        except metadata.PackageNotFoundError:
            if tool_name == "uv":
                uv_version = subprocess.run(
                    [str(Path(sys.prefix) / "bin" / "uv"), "--version"],
                    capture_output=True,
                    text=True,
                )
                actual_tool = (
                    uv_version.stdout.strip().split()[1]
                    if uv_version.returncode == 0 and uv_version.stdout.strip()
                    else "missing"
                )
            else:
                actual_tool = "missing"
        if actual_tool != contract[tool_name]:
            errors.append(
                f"{tool_name}: expected {contract[tool_name]}, got {actual_tool}"
            )

    for name, expected in contract["versions"].items():
        try:
            actual = metadata.version(name)
        except metadata.PackageNotFoundError:
            errors.append(f"{name}: missing (expected {expected})")
            continue
        if actual != expected:
            errors.append(f"{name}: expected {expected}, got {actual}")

    try:
        root_distribution = metadata.distribution("error-coupling-simulator")
        root_version = root_distribution.version
    except metadata.PackageNotFoundError:
        errors.append("error-coupling-simulator: current checkout is not installed editable")
    else:
        if root_version != "0.1.0":
            errors.append(f"error-coupling-simulator: expected 0.1.0, got {root_version}")
        direct_url_text = root_distribution.read_text("direct_url.json")
        if direct_url_text is None:
            errors.append("error-coupling-simulator: editable provenance is missing")
        else:
            direct_url = json.loads(direct_url_text)
            checkout = Path(unquote(urlparse(direct_url.get("url", "")).path)).resolve()
            if checkout != ROOT or not direct_url.get("dir_info", {}).get("editable"):
                errors.append(
                    "error-coupling-simulator: expected editable current checkout, "
                    f"got {direct_url}"
                )

    spec = util.find_spec("qutip_cuquantum")
    if spec is None or spec.origin is None:
        errors.append("qutip_cuquantum: import source not found")
    elif "external/baselines" in str(Path(spec.origin).resolve()):
        errors.append(f"qutip_cuquantum: still routed to ignored baseline {spec.origin}")

    # CUDA-Q is intentionally outside the canonical ecs environment.  Its
    # noiseless Grover adapter remains available only in the retained aiqec
    # environment, isolated from this process and the fused Torch extension.
    for forbidden in ("cudaq", "cuda-quantum-cu13"):
        try:
            actual = metadata.version(forbidden)
        except metadata.PackageNotFoundError:
            continue
        errors.append(f"{forbidden}: must be absent from ecs, found {actual}")
    cudaq_spec = util.find_spec("cudaq")
    if cudaq_spec is not None:
        errors.append(f"cudaq: import path must be absent from ecs, got {cudaq_spec.origin}")

    # Probe the native-backed QuTiP adapter in an isolated child process.
    for module in ("qutip_cuquantum",):
        try:
            probe = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"import {module}; print({module}.__file__)",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            errors.append(f"{module}: isolated import timed out after 30 seconds")
            continue
        if probe.returncode != 0:
            detail = (probe.stderr or probe.stdout).strip().splitlines()
            errors.append(
                f"{module}: isolated import failed with exit {probe.returncode}"
                + (f" ({detail[-1]})" if detail else "")
            )
        else:
            output_lines = probe.stdout.strip().splitlines()
            origin = Path(output_lines[-1]).resolve() if output_lines else None
            if origin is None or not origin.is_relative_to(Path(sys.prefix).resolve()):
                errors.append(
                    f"{module}: expected import below {sys.prefix}, got {origin}"
                )

    import torch
    from torch.utils.cpp_extension import CUDA_HOME

    if torch.version.cuda != contract["torch_cuda"]:
        errors.append(
            f"torch CUDA: expected {contract['torch_cuda']}, got {torch.version.cuda}"
        )

    expected_provider = Path(
        metadata.distribution("nvidia-cuda-nvcc").locate_file(contract["cuda_provider"])
    ).resolve()
    actual_provider = Path(CUDA_HOME).resolve() if CUDA_HOME else None
    if actual_provider != expected_provider:
        errors.append(f"CUDA_HOME: expected {expected_provider}, got {actual_provider}")

    expected_lib = str(expected_provider / "lib")
    ld_paths = [p for p in os.environ.get("LD_LIBRARY_PATH", "").split(":") if p]
    if [str(Path(path).resolve()) for path in ld_paths] != [expected_lib]:
        errors.append(
            f"LD_LIBRARY_PATH: expected only locked provider ({expected_lib}), got {ld_paths}"
        )

    expected_nvcc = expected_provider / "bin" / "nvcc"
    actual_pytorch_nvcc = os.environ.get("PYTORCH_NVCC")
    if actual_pytorch_nvcc is None or Path(actual_pytorch_nvcc).resolve() != expected_nvcc:
        errors.append(
            f"PYTORCH_NVCC: expected {expected_nvcc}, got {actual_pytorch_nvcc}"
        )
    path_nvcc = shutil.which("nvcc")
    if path_nvcc is None or Path(path_nvcc).resolve() != expected_nvcc:
        errors.append(f"PATH nvcc: expected {expected_nvcc}, got {path_nvcc}")

    expected_cache = (
        Path(sys.prefix)
        / ".cache"
        / "torch_extensions"
        / "torch-2.12.0-cu130"
    )
    actual_cache = os.environ.get("TORCH_EXTENSIONS_DIR")
    if actual_cache is None or Path(actual_cache).expanduser().resolve() != expected_cache:
        errors.append(
            f"TORCH_EXTENSIONS_DIR: expected {expected_cache}, got {actual_cache}"
        )

    nvcc = expected_provider / "bin" / "nvcc"
    cudart_link = expected_provider / "lib" / "libcudart.so"
    cudart_soname = expected_provider / "lib" / "libcudart.so.13"
    if not cudart_link.is_symlink() or cudart_link.resolve() != cudart_soname.resolve():
        errors.append(f"cudart linker name: expected {cudart_link} -> {cudart_soname.name}")
    if nvcc.is_file():
        version_text = subprocess.run(
            [str(nvcc), "--version"], check=True, capture_output=True, text=True
        ).stdout
        if "release 13.0," not in version_text:
            errors.append("nvcc: expected CUDA 13.0 compiler")
    else:
        errors.append(f"nvcc: missing at {nvcc}")

    for variable in ("PYTHONPATH", "ECS_DISABLE_NATIVE_KERNELS", "LD_PRELOAD"):
        if os.environ.get(variable):
            errors.append(f"{variable}: must be unset, got {os.environ[variable]}")

    pip_check = subprocess.run(
        [sys.executable, "-m", "pip", "check"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if pip_check.returncode != 0:
        errors.append(f"pip check failed: {(pip_check.stdout or pip_check.stderr).strip()}")

    uv_environment = os.environ.copy()
    uv_environment["VIRTUAL_ENV"] = sys.prefix
    uv_check = subprocess.run(
        [
            str(Path(sys.prefix) / "bin" / "uv"),
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
            "--check",
        ],
        cwd=ROOT,
        env=uv_environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if uv_check.returncode != 0:
        errors.append(
            "uv.lock environment sync failed: "
            f"{(uv_check.stderr or uv_check.stdout).strip()}"
        )

    if errors:
        print("core environment contract: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("core environment contract: PASS")
    print(f"python={actual_python} torch={torch.__version__} torch_cuda={torch.version.cuda}")
    print(f"CUDA_HOME={expected_provider}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
