"""CUDA-kernel acceleration for the exact forward's inner loop (carrier/kernels/; GPU-first, docs/SIMULATOR.md).

JIT-loads the fused subsystem-Kraus kernel from the package-local
``src/qec_twin/forward/kernels/`` folder and wraps it in an autograd Function that is
a drop-in for the reference
``apply_channel_local`` chain (embed + ``apply_kraus`` + hermitianize):

- forward: one fused CUDA kernel (raw sum) + hermitianize — bit-compatible with
  ``apply_kraus``'s convention;
- backward(rho): the adjoint channel via the same kernel with the dagger Kraus stack;
- backward(kraus): a small subspace-einsum composite (no full-space embedding),
  derived by autograd on the reference subspace contraction — only paid when the
  Kraus stack requires grad (the differentiable / optimization path).

Fallback: reference path on CPU tensors, when CUDA/nvcc is unavailable, or when
``QEC_TWIN_NO_KERNELS=1``. The reference implementation remains the correctness
oracle (``tests/test_kernels_fused_kraus.py``).
"""
from __future__ import annotations

import os
from pathlib import Path

import torch

from .cptp_channel import hermitianize

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


# --------------------------------------------------------------------------- #
# functorch/vmap compatibility (mainline upgrade, 2026-06-16)                   #
# --------------------------------------------------------------------------- #
# The fused kernel must be differentiable AND composable under BOTH vmap paths so
# the batched Fisher score backward can use it instead of the slow pure-torch
# reference:
#   * torch.func.jacrev / torch.func.vmap  — the FUNCTORCH dispatcher; honors a
#     new-style autograd.Function's `vmap` staticmethod (incl. through the backward).
#   * torch.autograd.grad(is_grads_batched=True) — the LEGACY `_vmap` engine; does
#     NOT call the Function's `vmap` staticmethod. It passes a storage-less legacy
#     BatchedTensor straight into `backward`; a RAW C++ op there explodes on
#     `.data_ptr()` ("Cannot access data pointer of Tensor that doesn't have
#     storage"). A `torch.library.custom_op` boundary FIXES this: legacy `_vmap`
#     materializes the BatchedTensor across a custom-op call.
# So the raw kernel is wrapped in a NON-autograd `custom_op` (the legacy-vmap-safe
# boundary, with a flatten-into-batch `register_vmap` for functorch + a meta
# `register_fake`), and a new-style `autograd.Function` owns differentiation (so
# `jacrev` works — a custom_op's own `register_autograd` is NOT functorch-
# transform-compatible, PyTorch 2.x). The combination makes is_grads_batched AND
# jacrev/vmap both compose through `apply_channel_local_fused`.


def _kernel_call(rho: torch.Tensor, kraus: torch.Tensor, targets, n: int) -> torch.Tensor:
    """Raw (unhermitianized) fused-kernel apply with any leading vmap dim FOLDED into the kernel's batch dim.

    The CUDA kernel ``fused_local_kraus`` accepts ``rho`` as ``[D, D]`` or ``[B, D, D]`` and a single SHARED
    Kraus stack ``[K, dt, dt]`` (it parallelises over ``B*D*D`` threads; no notion of a second leading dim).
    Under functorch vmap the incoming ``rho`` may carry extra leading dims; collapse everything but the
    trailing ``[D, D]`` into one kernel batch dim, call the kernel once, and restore the leading shape:

      * ``[D, D]`` / ``[B, D, D]`` (no vmap)         → straight through;
      * ``[V, D, D]``                                → kernel sees ``[V, D, D]`` (V acts as B);
      * ``[V, B, D, D]`` (vmap over a batched apply)  → flatten to ``[V*B, D, D]``, one call, reshape back.

    ``kraus`` is always the SHARED stack. RAW sum only — the caller hermitianizes (the kernel's
    ``apply_kraus`` convention)."""
    ext = _load_ext()
    tgt = [int(q) for q in targets]
    if rho.dim() <= 3:
        return ext.fused_local_kraus(rho, kraus, tgt, int(n))
    lead = rho.shape[:-2]
    flat = rho.reshape(-1, rho.shape[-1], rho.shape[-1])
    out = ext.fused_local_kraus(flat, kraus, tgt, int(n))
    return out.reshape(*lead, out.shape[-1], out.shape[-1])


# The custom-op boundary: the SAME raw kernel call, registered as a non-autograd custom op so the legacy
# `is_grads_batched` vmap materializes through it (and so functorch can vmap it via register_vmap). It is
# defined ONCE on import; if the extension is unavailable the op body raises on call (the CPU path never
# reaches here — see apply_channel_local_fused's docstring).
@torch.library.custom_op("qec_twin::fused_local_kraus_raw", mutates_args=())
def _fused_local_kraus_raw(rho: torch.Tensor, kraus: torch.Tensor, targets: list[int], n: int) -> torch.Tensor:
    return _kernel_call(rho, kraus, targets, n)


@_fused_local_kraus_raw.register_fake
def _(rho: torch.Tensor, kraus: torch.Tensor, targets: list[int], n: int) -> torch.Tensor:
    # meta/shape-only: the raw apply preserves rho's shape (a [.., D, D] -> [.., D, D] linear map).
    return torch.empty_like(rho)


def _fused_raw_vmap(info, in_dims, rho, kraus, targets, n):
    """functorch register_vmap for the raw custom op: fold the vmap dim into the kernel's batch dim.

    Expected/supported semantics (theory-first): the vmap dim lands on ``rho`` (the per-sample state) while
    ``kraus`` is SHARED. Move ``rho``'s vmap dim to front and call the op — its body folds the leading dim
    into the kernel batch dim. ``kraus`` MUST NOT be vmapped (the kernel takes a single shared Kraus stack;
    a per-sample Kraus is inexpressible) — raise rather than silently miscompute. ``targets``/``n`` static."""
    d_rho, d_kraus = in_dims[0], in_dims[1]
    if d_kraus is not None:
        raise RuntimeError(
            "apply_channel_local_fused: vmap over the Kraus argument is unsupported "
            "(the kernel takes a single shared Kraus stack). vmap rho only."
        )
    if d_rho is None:
        return _fused_local_kraus_raw(rho, kraus, targets, n), None
    rho_b = rho.movedim(d_rho, 0)
    return _fused_local_kraus_raw(rho_b, kraus, targets, n), 0


_fused_local_kraus_raw.register_vmap(_fused_raw_vmap)


class _FusedLocalKraus(torch.autograd.Function):
    """New-style (functorch/vmap-compatible) autograd Function for the fused subsystem-Kraus kernel.

    Split into ``forward`` (no ctx) + ``setup_context`` (saves rho/kraus/targets/n) + ``backward`` (the
    SAME exact math as the prior old-style Function) + an explicit ``vmap`` staticmethod. The forward value
    convention (raw kernel sum + ``hermitianize``) and the backward math (``grad_rho`` via the dagger-Kraus
    kernel; ``grad_kraus`` via ``_subspace_raw`` autograd) are IDENTICAL to the prior wrapper — verified
    bit-/grad-identical by ``tests/test_kernels_fused_kraus.py``.

    The kernel call goes through the ``qec_twin::fused_local_kraus_raw`` custom op (NOT the raw ext op
    directly) in BOTH forward and backward, so:
      * ``torch.autograd.grad(is_grads_batched=True)`` (legacy ``_vmap``) works — the custom-op boundary
        materializes the otherwise storage-less legacy BatchedTensor cotangent in ``backward``;
      * ``torch.func.jacrev`` / ``torch.func.vmap`` (functorch) work — this Function's ``vmap`` staticmethod
        (and the custom op's ``register_vmap``) fold the vmap dim into the kernel's batch dim.

    Why a new-style Function on top of the custom op (not the custom op's own ``register_autograd``): a
    custom op's ``register_autograd`` builds an internal autograd.Function that is NOT functorch-transform-
    compatible (it lacks the functorch ``setup_context`` hook), so ``jacrev`` over it raises. A hand-written
    new-style Function IS functorch-compatible. Why an explicit ``vmap`` (not ``generate_vmap_rule=True``):
    the kernel takes exactly one leading batch dim, so the autogenerated rule (which adds an extra vmap dim
    the kernel can't consume) does not apply; the explicit rule folds the vmap dim into the batch dim."""

    @staticmethod
    def forward(rho: torch.Tensor, kraus: torch.Tensor, targets: tuple, n: int):
        return hermitianize(_fused_local_kraus_raw(rho, kraus, list(targets), int(n)))

    @staticmethod
    def setup_context(ctx, inputs, output):
        rho, kraus, targets, n = inputs
        ctx.save_for_backward(rho, kraus)
        ctx.targets, ctx.n = targets, n

    @staticmethod
    def backward(ctx, grad_out: torch.Tensor):
        rho, kraus = ctx.saved_tensors
        targets, n = ctx.targets, ctx.n
        gh = 0.5 * (grad_out + grad_out.conj().transpose(-1, -2))
        grad_rho = grad_kraus = None
        if ctx.needs_input_grad[0]:
            # adjoint channel via the SAME kernel with the dagger Kraus stack, through the custom-op
            # boundary (NOT the raw ext op). Under is_grads_batched=True the cotangent ``gh`` is a legacy
            # BatchedTensor; the custom-op boundary materializes it so the kernel's .data_ptr() succeeds.
            # The adjoint map is linear in ``gh`` and maps the Hermitian ``gh`` to a Hermitian result, so
            # the final hermitianize is an identity (to round-off) on the true grad — grad bit-identical to
            # the prior raw-ext backward (verified <1e-10 by tests/test_kernels_fused_kraus.py).
            kdag = kraus.conj().transpose(-1, -2).contiguous()
            grad_rho = hermitianize(_fused_local_kraus_raw(gh, kdag, list(targets), int(n)))
        if ctx.needs_input_grad[1]:
            gh3 = gh if gh.dim() == 3 else gh.unsqueeze(0)
            rho3 = rho if rho.dim() == 3 else rho.unsqueeze(0)
            # grad_kraus = VJP of the reference subspace contraction _subspace_raw(rho, ·) wrt the Kraus
            # stack, at cotangent gh3. Computed with torch.func.vjp (NOT requires_grad_ + autograd.grad):
            # functorch transforms (jacrev/grad through this Function) forbid requires_grad_() inside a
            # transformed region, whereas torch.func.vjp composes. In eager mode torch.func.vjp is
            # bit-identical to the old autograd.grad path (verified <1e-10 by tests/test_kernels_fused_kraus
            # .py). _subspace_raw is bilinear in the Kraus, all standard torch ops ⇒ vmap-safe.
            _, vjp_fn = torch.func.vjp(
                lambda k: _subspace_raw(rho3.detach(), k, targets, n), kraus.detach()
            )
            (grad_kraus,) = vjp_fn(gh3)
        return grad_rho, grad_kraus, None, None

    @staticmethod
    def vmap(info, in_dims, rho, kraus, targets, n):
        """functorch vmap rule for the Function: fold the vmap dim into the kernel's batch dim.

        ``in_dims`` is the per-input batched-dim spec ``(d_rho, d_kraus, d_targets, d_n)`` (None = not
        batched). Move ``rho``'s vmap dim to front and run the (hermitianizing) forward — whose custom-op
        body folds the leading dim into the kernel batch dim — returning out-dim 0. ``kraus`` MUST NOT be
        vmapped (single shared Kraus stack); raise otherwise. ``targets``/``n`` are static."""
        d_rho, d_kraus = in_dims[0], in_dims[1]
        if d_kraus is not None:
            raise RuntimeError(
                "apply_channel_local_fused: vmap over the Kraus argument is unsupported "
                "(the kernel takes a single shared Kraus stack). vmap rho only."
            )
        if d_rho is None:
            return _FusedLocalKraus.apply(rho, kraus, targets, n), None
        rho_b = rho.movedim(d_rho, 0)
        out = _FusedLocalKraus.apply(rho_b, kraus, targets, n)
        return out, 0


def apply_channel_local_fused(
    rho: torch.Tensor, kraus: torch.Tensor, targets, n: int
) -> torch.Tensor:
    """Drop-in for ``circuit_sim.apply_channel_local`` on CUDA tensors.

    functorch/vmap-compatible: ``torch.autograd.grad(..., is_grads_batched=True)`` and
    ``torch.func.jacrev`` / ``torch.func.vmap`` compose through it (the kernel's batch dim absorbs the vmap
    dim). The CPU / ``QEC_TWIN_NO_KERNELS`` fallback is unchanged — callers route there via
    ``circuit_sim.apply_channel_local`` when ``accel.available()`` is False; this function is only invoked
    on the CUDA kernel path."""
    return _FusedLocalKraus.apply(rho, kraus, tuple(int(q) for q in targets), int(n))
