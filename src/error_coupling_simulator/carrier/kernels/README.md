# carrier/kernels/ — CUDA/C++ acceleration kernels

Custom CUDA kernels for the hot paths of the exact forward
(`carrier/exact`), per the GPU-first discipline (docs/SIMULATOR.md) and the
2026-06-09 user directive: everything runs on GPU where possible; repeated inner
computations get fused CUDA kernels. They live beside `carrier/accel.py` because
they are acceleration assets for the forward backend, not a separate model module.

## Scope (bounding)

- **In scope:** fused device kernels for inner-loop primitives that the profiled
  hot path repeats thousands of times per calibration — subsystem Kraus/unitary
  application on batched density matrices, and (future) fused branch projection /
  parity readout. Sources here are `.cu`/`.cpp` only; the Python side (JIT
  loading, autograd wrapping, dispatch, CPU fallback) lives in
  `src/qec_twin/forward/accel.py`.
- **Out of scope:** any physics or claim logic. A kernel must be a bit-for-bit
  (`<= 1e-12`) drop-in for its reference torch implementation, enforced by
  `tests/test_kernels_fused_kraus.py` (forward equivalence + autograd gradcheck).
  The reference path is never deleted — it is the fallback (CPU, no-CUDA, or
  `QEC_TWIN_NO_KERNELS=1`) and the correctness oracle.

## Profile that motivated this (2026-06-09, RTX 5090, torch 2.12+cu130)

Predictions written before measuring (theory-first, engineering form): the d=3 exact
forward is launch/overhead-bound, not FLOP-bound — `rho` is 8x8 (parity backend) with
the syndrome-branch batch in the leading axis; each noise layer pays
`embed_operator` (kron + 2n-axis permute + `.contiguous()` copy) per Kraus stack plus
an einsum. Measured: one heavy r=4 context forward = 67 ms CPU; a full C_cal(4) sweep
= 62 ms; a 600-step LBFGS fit = 2-3 min; the H2 file = ~30 min. The naive
`device="cuda"` path crashed (constants/teachers constructed on CPU) — fixed by the
device-plumbing pass (GPU-1).

## Kernels

| Kernel | Replaces | Notes |
|---|---|---|
| `fused_local_kraus` | `embed_operator` + `apply_kraus` chain in `apply_channel_local` / `apply_unitary` (K=1) | one thread per output element; gathers the target-qubit subspace by bit arithmetic (qubit 0 = most significant, matching `circuit_sim`); raw (unhermitianized) sum — the torch side hermitianizes, matching `apply_kraus` exactly. Backward: `grad_rho` via the same kernel with the adjoint Kraus stack; `grad_kraus` via a small subspace-einsum composite (v2: fuse). |

## Measured results (2026-06-09, RTX 5090; predictions stated in `outputs/*_bench.py` first)

Correctness: 9/9 (`tests/test_kernels_fused_kraus.py`) — forward ≤1e-12 vs reference
across n/targets/batch/K=1, gradients ≤1e-10; cuda end-to-end conserves probability;
`calibrate` on cuda reproduces the CPU `total_kl` exactly (7.055e-08 both).

Per-call fused-GPU vs CPU reference (`outputs/scale_bench.py`):

| n | D | speedup |
|---|---|---|
| 3 | 8 | 1.8× |
| 5 | 32 | 8.4× |
| 7 | 128 | 15.9× |
| 9 | 512 | 37.7× |
| 11 | 2048 | **102×** |
| 13 | 8192 | **405×** |

**Honest end-to-end caveat (d=3 toy):** a full `calibrate(steps=60)` on cuda+fused is
**0.51× CPU** (8.6 s vs 4.3 s, identical numerics) — the toy's 8×8 states leave the
sequential LBFGS loop launch-bound; per-call wins do not survive the launch chain.
**Device policy:** the d=3 toy stays CPU-default; cuda pays from n≈5 per-call and
decisively at the R2-lite window sizes n=11–15 (M2/M3 — the next real workload) and
any d≥5 simulation. Re-measure note (2026-06-10): at the small benchmark shape
(n=3, B=4096) fused and unfused-GPU sit within timing noise (0.9–1.5× across runs) —
the benchmark test asserts only "not catastrophically slower" there; the n≥5 wins
above are the kernel's claim.

**GPU-2 landed for the M3 window fit (2026-06-10):** the launch-bound fit closure is
solved by (i) the bit-exact parity-mask sweep fusion (`circuit_sim.dephase_parity_sweep`,
pinned by `tests/test_steady_state_fusions.py`), (ii) the Kraus hoist (ledger
amendment 7), and (iii) **static-Kraus-input CUDA-graph capture**
(`calibration/hardware_nll.py`, `torch.matrix_exp` eager at the boundary — it
host-syncs and cannot be captured): 84 production fits in 22 min on one context,
bit-exact vs the amended eager reference at three pin levels
(`tests/test_hardware_nll_graph_mode.py`, `outputs/m3_graph_realpin.py`, the fleet
`--verify`). Measured anti-patterns, for the record: 8 CUDA contexts on WSL2
time-slice BELOW sequential throughput; single-context threading is GIL-bound.

## Build

JIT via `torch.utils.cpp_extension.load` on first use (ninja; nvcc from
`/usr/local/cuda`); no install step. `QEC_TWIN_NO_KERNELS=1` disables loading.
