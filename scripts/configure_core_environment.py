#!/usr/bin/env python3
"""Bind the active Conda environment to the locked CUDA-13.0 wheel toolchain."""

from __future__ import annotations

from importlib import metadata
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
            f"configure the canonical {contract['conda_environment']} environment, "
            f"not {environment_name}"
        )

    provider = Path(
        metadata.distribution("nvidia-cuda-nvcc").locate_file("nvidia/cu13")
    ).resolve()
    nvcc = provider / "bin" / "nvcc"
    cudart = provider / "lib" / "libcudart.so.13"
    if not nvcc.is_file() or not cudart.is_file():
        raise SystemExit(
            "locked CUDA provider is incomplete; sync the environment from uv.lock first"
        )

    # NVIDIA's runtime wheel ships the SONAME file but not the development
    # linker name expected by torch.utils.cpp_extension (``-lcudart``).
    cudart_link = provider / "lib" / "libcudart.so"
    if cudart_link.is_symlink() and cudart_link.resolve() != cudart.resolve():
        cudart_link.unlink()
    if not cudart_link.exists():
        cudart_link.symlink_to(cudart.name)

    # Put the locked compiler on the Conda prefix's ordinary command path too.
    # PYTORCH_NVCC is also set because cpp_extension honours it explicitly.
    nvcc_link = Path(sys.prefix) / "bin" / "nvcc"
    if nvcc_link.is_symlink() and nvcc_link.resolve() != nvcc.resolve():
        nvcc_link.unlink()
    if nvcc_link.exists() and nvcc_link.resolve() != nvcc.resolve():
        raise SystemExit(f"refusing to replace non-provider compiler at {nvcc_link}")
    if not nvcc_link.exists():
        nvcc_link.symlink_to(nvcc)

    extension_cache = (
        Path(sys.prefix)
        / ".cache"
        / "torch_extensions"
        / "torch-2.12.0-cu130"
    )
    subprocess.run(
        [
            "conda",
            "env",
            "config",
            "vars",
            "set",
            "-p",
            sys.prefix,
            f"CUDA_HOME={provider}",
            f"LD_LIBRARY_PATH={provider / 'lib'}",
            f"PYTORCH_NVCC={nvcc}",
            f"TORCH_EXTENSIONS_DIR={extension_cache}",
        ],
        check=True,
    )
    print(f"CUDA_HOME={provider}")
    print(f"LD_LIBRARY_PATH={provider / 'lib'}")
    print(f"PYTORCH_NVCC={nvcc}")
    print(f"TORCH_EXTENSIONS_DIR={extension_cache}")
    print("Conda environment variables saved; subsequent `conda run` calls use them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
