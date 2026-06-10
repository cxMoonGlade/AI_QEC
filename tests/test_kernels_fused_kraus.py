"""Equivalence + gradcheck for the fused subsystem-Kraus CUDA kernel.

The kernel must be a <= 1e-12 drop-in for the reference
``apply_channel_local`` chain — forward values AND autograd (rho and Kraus
gradients). The source lives in ``src/qec_twin/forward/kernels/``. Skips without
CUDA / when the extension cannot build.
"""
from __future__ import annotations

import pytest
import torch

cuda_ok = torch.cuda.is_available()
if cuda_ok:
    from qec_twin.forward import accel

    cuda_ok = accel.available()

pytestmark = pytest.mark.skipif(not cuda_ok, reason="CUDA / kernel extension unavailable")

from qec_twin.forward.exact.circuit_sim import apply_channel_local  # noqa: E402


def _rand_rho(b: int, n: int, *, device="cuda", seed: int = 0) -> torch.Tensor:
    g = torch.Generator(device="cpu").manual_seed(seed)
    a = torch.randn(b, 2**n, 2**n, dtype=torch.complex128, generator=g)
    rho = a @ a.conj().transpose(-1, -2)
    rho = rho / rho.diagonal(dim1=-2, dim2=-1).sum(-1).real[:, None, None]
    return rho.to(device)

def _rand_kraus(k: int, dt: int, *, seed: int = 1) -> torch.Tensor:
    g = torch.Generator(device="cpu").manual_seed(seed)
    return torch.randn(k, dt, dt, dtype=torch.complex128, generator=g)


@pytest.mark.parametrize("n,targets", [(3, [0]), (3, [2]), (3, [0, 1]), (4, [1, 3]), (5, [0, 4]), (5, [4, 0])])
def test_forward_equivalence(n, targets) -> None:
    from qec_twin.forward.accel import apply_channel_local_fused

    rho = _rand_rho(7, n)
    kraus = _rand_kraus(3, 2 ** len(targets)).cuda()
    ref = apply_channel_local(rho, kraus, targets, n)
    fused = apply_channel_local_fused(rho, kraus, targets, n)
    assert torch.allclose(fused, ref, atol=1e-12, rtol=0.0), (fused - ref).abs().max().item()


def test_forward_equivalence_unbatched_and_k1() -> None:
    from qec_twin.forward.accel import apply_channel_local_fused

    rho = _rand_rho(1, 3)[0]
    kraus = _rand_kraus(1, 4).cuda()  # unitary-like K=1 stack
    ref = apply_channel_local(rho, kraus, [0, 2], 3)
    fused = apply_channel_local_fused(rho, kraus, [0, 2], 3)
    assert torch.allclose(fused, ref, atol=1e-12, rtol=0.0)


def test_gradients_match_reference() -> None:
    from qec_twin.forward.accel import apply_channel_local_fused

    n, targets = 3, [0, 1]
    rho0 = _rand_rho(4, n)
    kraus0 = _rand_kraus(2, 4).cuda()

    def run(fn):
        rho = rho0.clone().requires_grad_(True)
        kraus = kraus0.clone().requires_grad_(True)
        out = fn(rho, kraus, targets, n)
        loss = (out.real**2 + out.imag**2).sum()
        loss.backward()
        return rho.grad.clone(), kraus.grad.clone()

    gr_ref, gk_ref = run(apply_channel_local)
    gr_fused, gk_fused = run(apply_channel_local_fused)
    assert torch.allclose(gr_fused, gr_ref, atol=1e-10, rtol=0.0), (gr_fused - gr_ref).abs().max().item()
    assert torch.allclose(gk_fused, gk_ref, atol=1e-10, rtol=0.0), (gk_fused - gk_ref).abs().max().item()


def test_benchmark_report() -> None:
    import time

    from qec_twin.forward.accel import apply_channel_local_fused

    n, targets, B = 3, [0, 1], 4096
    rho = _rand_rho(B, n, seed=3)
    kraus = _rand_kraus(2, 4, seed=4).cuda()
    rho_cpu, kraus_cpu = rho.cpu(), kraus.cpu()

    def bench(fn, *args, reps=50):
        for _ in range(5):
            fn(*args)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(reps):
            fn(*args)
        torch.cuda.synchronize()
        return (time.perf_counter() - t0) / reps

    t_ref_cpu = bench(apply_channel_local, rho_cpu, kraus_cpu, targets, n, reps=10)
    t_ref_gpu = bench(apply_channel_local, rho, kraus, targets, n)
    t_fused = bench(apply_channel_local_fused, rho, kraus, targets, n)
    print(
        f"\nB={B} n={n}: reference CPU {t_ref_cpu*1e3:.2f} ms | reference GPU "
        f"{t_ref_gpu*1e3:.2f} ms | fused GPU {t_fused*1e3:.2f} ms "
        f"(x{t_ref_cpu/t_fused:.0f} vs CPU, x{t_ref_gpu/t_fused:.1f} vs GPU ref)"
    )
    assert t_fused < t_ref_gpu
