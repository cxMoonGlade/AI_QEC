from __future__ import annotations

"""JIT loader for generic qutrit statevector MCWF CUDA ops.

These kernels accelerate the project-native finite-Kraus MCWF carrier. They do
not replace the carrier with qutip-cuquantum; the Torch-GPU implementation
remains the semantic reference.
"""

import logging
import os
from pathlib import Path
from typing import Sequence

import torch

_log = logging.getLogger(__name__)

_EXT = None
_EXT_TRIED = False


def _kernels_dir() -> Path:
    return Path(__file__).resolve().parent


def _load_ext():
    global _EXT, _EXT_TRIED
    if _EXT_TRIED:
        return _EXT
    _EXT_TRIED = True
    if os.environ.get("QEC_TWIN_NO_KERNELS") == "1" or not torch.cuda.is_available():
        return None
    src = _kernels_dir() / "qutrit_mcwf_ops.cu"
    if not src.exists():
        return None
    try:
        from torch.utils.cpp_extension import load

        _EXT = load(
            name="qec_twin_qutrit_mcwf_ops",
            sources=[str(src)],
            extra_cuda_cflags=["-O3"],
            verbose=False,
        )
    except Exception as exc:
        _EXT = None
        _log.error(
            "qutrit_mcwf_ops failed to JIT-compile even though CUDA is visible "
            "and source exists; this is a genuine toolchain/kernel error.",
            exc_info=True,
        )
        raise RuntimeError(
            f"qutrit_mcwf_ops failed to compile from {src}. Surface the nvcc/ninja "
            "error above; set QEC_TWIN_NO_KERNELS=1 only to intentionally disable "
            "the fused kernels while retaining the Torch-GPU Kraus-MCWF reference path."
        ) from exc
    return _EXT


def available() -> bool:
    return _load_ext() is not None


def apply_qubit_gate(psi: torch.Tensor, unitary: torch.Tensor, sites: Sequence[int], n: int) -> torch.Tensor:
    ext = _load_ext()
    if ext is None:
        raise RuntimeError("qutrit_mcwf_ops CUDA extension is unavailable")
    return ext.qutrit_apply_qubit_gate(psi, unitary, [int(s) for s in sites], int(n))


def multi_controlled_phase(
    psi: torch.Tensor,
    sites: Sequence[int],
    phase: complex | float,
    n: int,
) -> torch.Tensor:
    ext = _load_ext()
    if ext is None:
        raise RuntimeError("qutrit_mcwf_ops CUDA extension is unavailable")
    z = complex(phase)
    return ext.qutrit_multi_controlled_phase(psi, [int(s) for s in sites], float(z.real), float(z.imag), int(n))


def apply_kraus_site(
    psi: torch.Tensor,
    kraus: torch.Tensor,
    rand: torch.Tensor,
    site: int,
    n: int,
) -> torch.Tensor:
    ext = _load_ext()
    if ext is None:
        raise RuntimeError("qutrit_mcwf_ops CUDA extension is unavailable")
    return ext.qutrit_apply_kraus_site(psi, kraus, rand, int(site), int(n))


def apply_kraus_all_sites(
    psi: torch.Tensor,
    kraus: torch.Tensor,
    rand: torch.Tensor,
    sites: Sequence[int],
    n: int,
) -> torch.Tensor:
    ext = _load_ext()
    if ext is None:
        raise RuntimeError("qutrit_mcwf_ops CUDA extension is unavailable")
    return ext.qutrit_apply_kraus_all_sites(psi, kraus, rand, [int(s) for s in sites], int(n))


def run_cached_opstream(
    psi: torch.Tensor,
    op_kind: torch.Tensor,
    op_site_ptr: torch.Tensor,
    op_sites: torch.Tensor,
    kraus: torch.Tensor,
    rand: torch.Tensor,
    n: int,
) -> torch.Tensor:
    ext = _load_ext()
    if ext is None:
        raise RuntimeError("qutrit_mcwf_ops CUDA extension is unavailable")
    return ext.qutrit_run_cached_opstream(psi, op_kind, op_site_ptr, op_sites, kraus, rand, int(n))


def run_block_traj_opstream(
    psi: torch.Tensor,
    op_kind: torch.Tensor,
    op_site_ptr: torch.Tensor,
    op_sites: torch.Tensor,
    kraus: torch.Tensor,
    rand: torch.Tensor,
    n: int,
) -> torch.Tensor:
    ext = _load_ext()
    if ext is None:
        raise RuntimeError("qutrit_mcwf_ops CUDA extension is unavailable")
    return ext.qutrit_run_block_traj_opstream(psi, op_kind, op_site_ptr, op_sites, kraus, rand, int(n))
