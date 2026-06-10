"""CUDA-kernel acceleration for the exact forward's inner loop (forward/kernels/, ADR 0001).

JIT-loads the fused subsystem-Kraus kernel from the package-local
``src/qec_twin/forward/kernels/`` folder and wraps it in an autograd Function that is
a drop-in for the reference
``apply_channel_local`` chain (embed + ``apply_kraus`` + hermitianize):

- forward: one fused CUDA kernel (raw sum) + hermitianize — bit-compatible with
  ``apply_kraus``'s convention;
- backward(rho): the adjoint channel via the same kernel with the dagger Kraus stack;
- backward(kraus): a small subspace-einsum composite (no full-space embedding),
  derived by autograd on the reference subspace contraction — only paid when the
  Kraus stack requires grad (the twin side).

Fallback: reference path on CPU tensors, when CUDA/nvcc is unavailable, or when
``QEC_TWIN_NO_KERNELS=1``. The reference implementation remains the correctness
oracle (``tests/test_kernels_fused_kraus.py``).
"""
from __future__ import annotations

import os
from pathlib import Path

import torch

from qec_twin.forward.cptp_channel import hermitianize

_EXT = None
_EXT_TRIED = False


def _kernels_dir() -> Path:
    return Path(__file__).resolve().parent / "kernels"


def _load_ext():
    global _EXT, _EXT_TRIED
    if _EXT_TRIED:
        return _EXT
    _EXT_TRIED = True
    if os.environ.get("QEC_TWIN_NO_KERNELS") == "1" or not torch.cuda.is_available():
        return None
    src = _kernels_dir()
    cu, cpp = src / "fused_kraus_local.cu", src / "fused_kraus_local.cpp"
    if not (cu.exists() and cpp.exists()):
        return None
    try:
        from torch.utils.cpp_extension import load

        _EXT = load(
            name="qec_twin_kernels",
            sources=[str(cpp), str(cu)],
            extra_cuda_cflags=["-O3"],
            verbose=False,
        )
    except Exception:
        _EXT = None
    return _EXT


def available() -> bool:
    return _load_ext() is not None


def _subspace_raw(rho: torch.Tensor, kraus: torch.Tensor, targets, n: int) -> torch.Tensor:
    """Reference raw (unhermitianized) channel action via subspace permute — used
    only inside backward for the Kraus vjp; no full-space kron."""
    targets = [int(q) for q in targets]
    m = len(targets)
    rest = [q for q in range(n) if q not in targets]
    order = targets + rest
    b = rho.shape[0]
    v = rho.reshape(b, *([2] * (2 * n)))
    perm = [0] + [1 + q for q in order] + [1 + n + q for q in order]
    v = v.permute(*perm).reshape(b, 2**m, 2 ** (n - m), 2**m, 2 ** (n - m))
    raw = torch.einsum("ksu,bupvq,ktv->bsptq", kraus, v, kraus.conj())
    raw = raw.reshape(b, *([2] * (2 * n)))
    inv = [0] + [1 + order.index(q) for q in range(n)] + [1 + n + order.index(q) for q in range(n)]
    return raw.permute(*inv).reshape(b, 2**n, 2**n)


class _FusedLocalKraus(torch.autograd.Function):
    @staticmethod
    def forward(ctx, rho: torch.Tensor, kraus: torch.Tensor, targets: tuple, n: int):
        ext = _load_ext()
        raw = ext.fused_local_kraus(rho, kraus, list(targets), n)
        ctx.save_for_backward(rho, kraus)
        ctx.targets, ctx.n = targets, n
        return hermitianize(raw)

    @staticmethod
    def backward(ctx, grad_out: torch.Tensor):
        rho, kraus = ctx.saved_tensors
        targets, n = ctx.targets, ctx.n
        ext = _load_ext()
        gh = 0.5 * (grad_out + grad_out.conj().transpose(-1, -2))
        grad_rho = grad_kraus = None
        if ctx.needs_input_grad[0]:
            kdag = kraus.conj().transpose(-1, -2).contiguous()
            grad_rho = ext.fused_local_kraus(gh.contiguous(), kdag, list(targets), n)
        if ctx.needs_input_grad[1]:
            gh3 = gh if gh.dim() == 3 else gh.unsqueeze(0)
            rho3 = rho if rho.dim() == 3 else rho.unsqueeze(0)
            with torch.enable_grad():
                k2 = kraus.detach().requires_grad_(True)
                raw = _subspace_raw(rho3.detach(), k2, targets, n)
                (grad_kraus,) = torch.autograd.grad(raw, k2, grad_outputs=gh3)
        return grad_rho, grad_kraus, None, None


def apply_channel_local_fused(
    rho: torch.Tensor, kraus: torch.Tensor, targets, n: int
) -> torch.Tensor:
    """Drop-in for ``circuit_sim.apply_channel_local`` on CUDA tensors."""
    return _FusedLocalKraus.apply(rho, kraus, tuple(int(q) for q in targets), int(n))
