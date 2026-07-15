"""functorch/vmap-correctness regression guard for the fused subsystem-Kraus kernel.

The fused kernel's autograd Function (``src/error_coupling_simulator/carrier/accel.py``::
``_FusedLocalKraus``) was upgraded to be functorch/vmap-composable so the batched
Fisher score can drive the FAST fused CUDA kernel instead of the slow pure-torch
reference. This file is the PERMANENT guard that the capability never silently
regresses. It is independent of the scratch smoke ``outputs/accel_vmap_smoke.py``.

The independent truth in every test is a per-sample Python loop of PLAIN
``torch.autograd.grad`` (one ordinary unbatched backward per record). The fused,
vmap-composed result must equal that loop to floating round-off. The tests cover
the four vmap entry points the codebase uses:

  1. ``torch.autograd.grad(..., is_grads_batched=True)``  — the LEGACY ``_vmap``
     engine; THIS is the path the batched Fisher score backward uses. (rho AND kraus)
  2. ``torch.func.jacrev``                                — the functorch jacobian. (rho AND kraus)
  3. ``torch.func.vmap`` (forward)                         — functorch forward batching.
  4. ``torch.autograd.gradcheck``                          — finite-difference vs analytic
     (complex128, small shape) — a fully independent gradient oracle.
  5. the documented Kraus-vmap guard RAISES whenever a vmap dim lands on the Kraus
     (a per-sample Kraus is inexpressible for the single-shared-Kraus kernel): plain
     forward ``vmap`` over the Kraus, and ``vmap(jacrev(...))`` over a batched Kraus.
     (Plain reverse-mode ``jacrev``-of-a-scalar wrt the Kraus is NOT a vmap-over-Kraus
     — it is the ordinary backward's ``grad_kraus`` and is a required capability; the
     guard correctly does NOT fire there. The test pins that distinction.)
  6. teeth — the <1e-10 asserts are NOT tautological (a scrambled-batch baseline is
     rejected).

functorch subtlety (load-bearing): ``torch.func.jacrev`` / ``torch.func.grad`` reject
COMPLEX primal inputs (``error_if_complex``) — a functorch API restriction unrelated
to the kernel. So the jacrev/vmap-forward paths parameterise the complex
``rho``/``kraus`` by their real ``(re, im)`` parts (real inputs), reconstruct the
complex tensors INSIDE the closure (still flowing through the real fused kernel), and
recombine ``g = jac_re + 1j*jac_im``. For a REAL scalar loss of a complex variable
``z = re + 1j*im``, PyTorch's ``z.grad`` (what the loop returns) is the
conjugate-Wirtinger gradient ``∂L/∂re + 1j·∂L/∂im``, so the recombined complex jac is
bit-for-bit the loop's ``.grad`` — the < 1e-10 comparison against the loop is exact.

GPU-only: complex128 on CUDA; the kernel needs CUDA. Skips without it (mirrors
``tests/test_kernels_fused_kraus.py``).
"""
from __future__ import annotations

import pytest
import torch

cuda_ok = torch.cuda.is_available()
if cuda_ok:
    from error_coupling_simulator.carrier import accel

    cuda_ok = accel.available()

pytestmark = pytest.mark.skipif(not cuda_ok, reason="CUDA / kernel extension unavailable")

import torch as _torch  # noqa: E402

from error_coupling_simulator.carrier.accel import apply_channel_local_fused  # noqa: E402
from error_coupling_simulator.carrier.cptp_channel import apply_kraus  # noqa: E402
from error_coupling_simulator.carrier.exact.circuit_sim import embed_operator  # noqa: E402

TOL_GRAD = 1e-10   # grad agreement (is_grads_batched / jacrev) vs the plain-autograd loop
TOL_FWD = 1e-12    # forward agreement (vmap) vs the per-sample loop


# --------------------------------------------------------------------------- #
# The UNFUSED reference forward (bypasses the kernel auto-route). NOT used as   #
# the grad truth here — the grad truth is a per-sample loop of plain autograd   #
# THROUGH THE FUSED apply, which is the genuinely independent check of the vmap #
# machinery (a different transform path, not a different forward). Kept to      #
# mirror the oracle test's conventions and to sanity-check forward values.      #
# --------------------------------------------------------------------------- #
def apply_channel_local(rho, kraus, targets, n):
    embedded = _torch.stack([embed_operator(k, targets, n) for k in kraus])
    return apply_kraus(rho, embedded)


def _rand_rho(b: int, n: int, *, device="cuda", seed: int = 0) -> torch.Tensor:
    g = torch.Generator(device="cpu").manual_seed(seed)
    a = torch.randn(b, 2**n, 2**n, dtype=torch.complex128, generator=g)
    rho = a @ a.conj().transpose(-1, -2)
    rho = rho / rho.diagonal(dim1=-2, dim2=-1).sum(-1).real[:, None, None]
    return rho.to(device)


def _rand_kraus(k: int, dt: int, *, device="cuda", seed: int = 1) -> torch.Tensor:
    g = torch.Generator(device="cpu").manual_seed(seed)
    return torch.randn(k, dt, dt, dtype=torch.complex128, generator=g).to(device)


# --------------------------------------------------------------------------- #
# Per-sample reference gradients via a plain autograd loop (the independent     #
# truth). For each batch row b: build a scalar |out|^2 loss and take an         #
# ORDINARY (unbatched) autograd.grad wrt rho[b] and the shared kraus.           #
# --------------------------------------------------------------------------- #
def _loop_grads(rho_b, kraus, targets, n):
    B = rho_b.shape[0]
    gr_rows, gk_rows = [], []
    for b in range(B):
        rb = rho_b[b].detach().clone().requires_grad_(True)
        kb = kraus.detach().clone().requires_grad_(True)
        out = apply_channel_local_fused(rb, kb, targets, n)
        loss = (out.real**2 + out.imag**2).sum()
        gr, gk = torch.autograd.grad(loss, (rb, kb))
        gr_rows.append(gr)
        gk_rows.append(gk)
    return torch.stack(gr_rows, 0), torch.stack(gk_rows, 0)


def _per_sample_loss(out_b):
    """Sum |out|^2 over the matrix axes → a (B,) per-sample scalar."""
    return (out_b.real**2 + out_b.imag**2).sum(dim=(-2, -1))


def _isgb_grads(rho_b, kraus, targets, n):
    """Per-sample grads via torch.autograd.grad(is_grads_batched=True): ONE batched
    backward whose grad_outputs is the (B,) identity. This is the legacy ``_vmap``
    engine — the path the batched Fisher uses, and the one that exploded on the old
    raw-ext backward. For rho (shape (B,D,D)) the per-sample grad is the diagonal
    v==b block of the (B,B,D,D) result (off-diagonal v!=b vanish: loss_v depends only
    on rho row v); for the SHARED kraus, loss_v's grad is the v-th row of (B,K,dt,dt)."""
    B = rho_b.shape[0]
    rho_l = rho_b.detach().clone().requires_grad_(True)
    kraus_l = kraus.detach().clone().requires_grad_(True)
    out = apply_channel_local_fused(rho_l, kraus_l, targets, n)  # (B, D, D)
    losses = _per_sample_loss(out)                               # (B,)
    eye = torch.eye(B, dtype=losses.real.dtype, device=losses.device)
    gr_batched = torch.autograd.grad(
        losses, rho_l, grad_outputs=eye, is_grads_batched=True, retain_graph=True
    )[0]  # (B, B, D, D): [v, b, :, :]
    gk_batched = torch.autograd.grad(
        losses, kraus_l, grad_outputs=eye, is_grads_batched=True, retain_graph=False
    )[0]  # (B, K, dt, dt): [v, :, :, :]
    gr = torch.stack([gr_batched[b, b] for b in range(B)], 0)    # (B, D, D)
    gk = gk_batched                                              # (B, K, dt, dt)
    return gr, gk


def _jacrev_grads(rho_b, kraus, targets, n):
    """Per-sample grads via torch.func.jacrev, vmapped over the batch.

    functorch rejects complex primal inputs, so parameterise rho/kraus by (re, im)
    real parts, reconstruct inside the loss, take jacrev wrt the real parts, then
    recombine g = jac_re + 1j*jac_im == the loop's complex .grad (conj-Wirtinger)."""
    import torch.func as tf

    def loss_one(rho_re, rho_im, k_re, k_im):
        rho_one = torch.complex(rho_re, rho_im)
        kraus_one = torch.complex(k_re, k_im)
        out = apply_channel_local_fused(rho_one, kraus_one, targets, n)
        return (out.real**2 + out.imag**2).sum()

    rb_re, rb_im = rho_b.real.contiguous(), rho_b.imag.contiguous()
    k_re, k_im = kraus.real.contiguous(), kraus.imag.contiguous()

    jr = tf.vmap(tf.jacrev(loss_one, argnums=(0, 1)), in_dims=(0, 0, None, None))(
        rb_re, rb_im, k_re, k_im
    )
    gr = torch.complex(jr[0], jr[1])  # (B, D, D) == loop's rho.grad
    jk = tf.vmap(tf.jacrev(loss_one, argnums=(2, 3)), in_dims=(0, 0, None, None))(
        rb_re, rb_im, k_re, k_im
    )
    gk = torch.complex(jk[0], jk[1])  # (B, K, dt, dt) == loop's kraus.grad
    return gr, gk


# shapes: n in {3,4,5} + the 6q d3-window case; a couple of targets each; K in {1,2,3}.
# dt = 2**len(targets), so the Kraus stack is (K, dt, dt).
_VMAP_SHAPES = [
    (3, (0,), 1),
    (3, (0, 2), 2),
    (4, (1, 3), 3),
    (5, (0, 4), 2),
    (5, (4, 0), 3),       # reversed targets — exercises the permute path
    (6, (2, 3), 2),       # representative of the d3 2x2 window (n=6)
    (6, (0, 5), 3),       # n=6, spread targets
]
_BATCH = 4


@pytest.mark.parametrize("n,targets,K", _VMAP_SHAPES)
def test_is_grads_batched_matches_autograd_loop(n, targets, K) -> None:
    """(1) torch.autograd.grad(is_grads_batched=True) == per-sample plain-autograd loop,
    for BOTH grad_rho and grad_kraus, < 1e-10. This is the Fisher's path."""
    rho_b = _rand_rho(_BATCH, n, seed=100 + n)
    kraus = _rand_kraus(K, 2 ** len(targets), seed=200 + n)

    gr_loop, gk_loop = _loop_grads(rho_b, kraus, targets, n)
    gr_isgb, gk_isgb = _isgb_grads(rho_b, kraus, targets, n)

    d_gr = (gr_isgb - gr_loop).abs().max().item()
    d_gk = (gk_isgb - gk_loop).abs().max().item()
    assert d_gr < TOL_GRAD, f"is_grads_batched grad_rho off {d_gr:.3e} (n={n}, targets={targets}, K={K})"
    assert d_gk < TOL_GRAD, f"is_grads_batched grad_kraus off {d_gk:.3e} (n={n}, targets={targets}, K={K})"


@pytest.mark.parametrize("n,targets,K", _VMAP_SHAPES)
def test_jacrev_matches_autograd_loop(n, targets, K) -> None:
    """(2) torch.func.jacrev (vmapped over the batch) == per-sample plain-autograd loop,
    for BOTH grad_rho and grad_kraus, < 1e-10."""
    rho_b = _rand_rho(_BATCH, n, seed=300 + n)
    kraus = _rand_kraus(K, 2 ** len(targets), seed=400 + n)

    gr_loop, gk_loop = _loop_grads(rho_b, kraus, targets, n)
    gr_jac, gk_jac = _jacrev_grads(rho_b, kraus, targets, n)

    d_gr = (gr_jac - gr_loop).abs().max().item()
    d_gk = (gk_jac - gk_loop).abs().max().item()
    assert d_gr < TOL_GRAD, f"jacrev grad_rho off {d_gr:.3e} (n={n}, targets={targets}, K={K})"
    assert d_gk < TOL_GRAD, f"jacrev grad_kraus off {d_gk:.3e} (n={n}, targets={targets}, K={K})"


@pytest.mark.parametrize("n,targets,K", _VMAP_SHAPES)
def test_vmap_forward_matches_loop(n, targets, K) -> None:
    """(3) torch.func.vmap of the forward over a batch == the per-sample loop, < 1e-12.

    functorch rejects complex inputs, so vmap a real (re, im) closure that rebuilds the
    complex rho inside; recombine the complex output and compare to the per-sample
    apply. (kraus is shared/static.)"""
    import torch.func as tf

    rho_b = _rand_rho(_BATCH, n, seed=500 + n)
    kraus = _rand_kraus(K, 2 ** len(targets), seed=600 + n)

    def fwd_one(rho_re, rho_im):
        rho_one = torch.complex(rho_re, rho_im)
        out = apply_channel_local_fused(rho_one, kraus, targets, n)
        return out.real, out.imag

    out_re, out_im = tf.vmap(fwd_one, in_dims=(0, 0))(rho_b.real.contiguous(), rho_b.imag.contiguous())
    out_vmap = torch.complex(out_re, out_im)
    out_loop = torch.stack(
        [apply_channel_local_fused(rho_b[b], kraus, targets, n) for b in range(_BATCH)], 0
    )
    d = (out_vmap - out_loop).abs().max().item()
    assert d < TOL_FWD, f"vmap forward off {d:.3e} (n={n}, targets={targets}, K={K})"


def test_gradcheck_complex_small() -> None:
    """(4) torch.autograd.gradcheck (finite-difference vs analytic) on a SMALL complex128
    shape — a fully independent gradient oracle (no per-sample loop, no functorch). Double
    precision so the central-difference tolerances are tight and the check is rigorous."""
    n, targets = 3, [0, 1]
    rho = _rand_rho(1, n, seed=7)[0].clone().requires_grad_(True)   # (D, D) complex128
    kraus = _rand_kraus(2, 2 ** len(targets), seed=8).clone().requires_grad_(True)

    def fn(r, k):
        return apply_channel_local_fused(r, k, targets, n)

    assert torch.autograd.gradcheck(
        fn, (rho, kraus), eps=1e-6, atol=1e-6, rtol=1e-4, nondet_tol=1e-12
    )


def test_kraus_vmap_guard_raises() -> None:
    """(5) A vmap dim landing on the KRAUS raises the documented RuntimeError (a per-sample
    Kraus is inexpressible for the single-shared-Kraus kernel — must fail loudly, never
    silently miscompute). Two paths that genuinely create a Kraus vmap dim:
      (a) plain forward ``torch.func.vmap`` over the Kraus argument;
      (b) ``vmap(jacrev(...))`` over a BATCHED Kraus (the realistic per-sample-Jacobian
          form — the outer vmap puts a batch dim on the Kraus input).

    Plain reverse-mode ``jacrev``-of-a-scalar wrt the Kraus is deliberately NOT tested as
    raising: it seeds the OUTPUT cotangent and runs the Function's ``backward`` (which has a
    proper ``grad_kraus`` vjp) — no vmap dim is ever placed on the Kraus, so the guard does
    not (and must not) fire. That path is a required capability, verified by
    ``test_kraus_jacrev_reverse_mode_is_exact`` below."""
    import torch.func as tf

    n, targets = 5, (0, 4)
    rho = _rand_rho(1, n, seed=9)[0]
    kraus = _rand_kraus(2, 2 ** len(targets), seed=10)
    kraus_batch = kraus.unsqueeze(0).expand(3, *kraus.shape).contiguous()  # a "per-sample" Kraus stack

    # (a) functorch vmap over the Kraus arg
    with pytest.raises(RuntimeError, match="vmap over the Kraus"):
        tf.vmap(lambda k: apply_channel_local_fused(rho, k, targets, n), in_dims=0)(kraus_batch)

    # (b) vmap(jacrev) over a batched Kraus — the outer vmap places a vmap dim on the Kraus
    # input, which routes through the Function's vmap rule and must raise. (Real (re, im)
    # parts to clear functorch's complex-input guard so the Kraus-vmap guard is what fires.)
    kb_re = kraus.real.unsqueeze(0).expand(3, *kraus.shape).contiguous()
    kb_im = kraus.imag.unsqueeze(0).expand(3, *kraus.shape).contiguous()

    def loss_k(k_re, k_im):
        out = apply_channel_local_fused(rho, torch.complex(k_re, k_im), targets, n)
        return (out.real**2 + out.imag**2).sum()

    with pytest.raises(RuntimeError, match="vmap over the Kraus"):
        tf.vmap(tf.jacrev(loss_k, argnums=(0, 1)), in_dims=(0, 0))(kb_re, kb_im)


def test_kraus_jacrev_reverse_mode_is_exact() -> None:
    """Companion to (5): plain reverse-mode ``torch.func.jacrev`` of a scalar loss wrt the
    Kraus SUCCEEDS (no vmap dim on the Kraus → the guard does not fire) and equals plain
    autograd EXACTLY. This pins that the Kraus-vmap guard is scoped to vmap-over-Kraus and
    does not over-fire on the legitimate ``grad_kraus`` backward the Fisher needs."""
    import torch.func as tf

    n, targets = 5, (0, 4)
    rho = _rand_rho(1, n, seed=9)[0]
    kraus = _rand_kraus(2, 2 ** len(targets), seed=10)
    k_re, k_im = kraus.real.contiguous(), kraus.imag.contiguous()

    def loss_k(kr, ki):
        out = apply_channel_local_fused(rho, torch.complex(kr, ki), targets, n)
        return (out.real**2 + out.imag**2).sum()

    j_re, j_im = tf.jacrev(loss_k, argnums=(0, 1))(k_re, k_im)

    kr = k_re.clone().requires_grad_(True)
    ki = k_im.clone().requires_grad_(True)
    out = apply_channel_local_fused(rho, torch.complex(kr, ki), targets, n)
    (out.real**2 + out.imag**2).sum().backward()

    d_re = (j_re - kr.grad).abs().max().item()
    d_im = (j_im - ki.grad).abs().max().item()
    assert d_re < TOL_GRAD and d_im < TOL_GRAD, f"jacrev-wrt-kraus != autograd (re {d_re:.3e}, im {d_im:.3e})"


def test_isgb_check_has_teeth() -> None:
    """(6) Teeth: the < 1e-10 is_grads_batched assert is NOT a tautology. A scrambled-batch
    baseline (the per-sample loop evaluated against the WRONG record ordering) must be
    rejected by the same tolerance — so a genuine batch-fold regression WOULD be caught."""
    n, targets, K = 5, (0, 4), 3
    rho_b = _rand_rho(_BATCH, n, seed=42)
    kraus = _rand_kraus(K, 2 ** len(targets), seed=43)

    gr_loop, gk_loop = _loop_grads(rho_b, kraus, targets, n)
    gr_isgb, _ = _isgb_grads(rho_b, kraus, targets, n)

    # correct: matches the correctly-ordered loop tightly
    d_correct = (gr_isgb - gr_loop).abs().max().item()
    assert d_correct < TOL_GRAD, f"control failed: correct match not < 1e-10 ({d_correct:.3e})"

    # scrambled: compare against a rolled (mis-paired) loop baseline — must NOT pass < 1e-10,
    # i.e. the records are genuinely distinct (so a batch-fold bug would move them apart).
    gr_scrambled = torch.roll(gr_loop, shifts=1, dims=0)
    d_scrambled = (gr_isgb - gr_scrambled).abs().max().item()
    assert d_scrambled > 1e-6, (
        f"TEETH DEAD: is_grads_batched matched a scrambled-batch baseline ({d_scrambled:.3e}) "
        "— the per-sample records are indistinguishable, so the <1e-10 check has no teeth"
    )
