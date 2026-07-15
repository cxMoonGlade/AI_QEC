# carrier/kernels/ — CUDA/C++ acceleration kernels

Custom CUDA kernels for hot paths of the exact forward (`carrier/exact`) and the
active fused within-cycle SV-MC carrier, per the GPU-first discipline in
`docs/SIMULATOR.md`. They are acceleration/execution assets, not a separate physics
or claim module.

## Scope (bounding)

- **Exact-forward family:** fused dense subsystem Kraus/unitary operations, loaded by
  `carrier/accel.py`. Its c128 result must agree numerically with the retained Torch reference
  within the declared `<=1e-12` gate; the reference remains the CPU/no-kernel fallback.
- **Fused-SV family:** the GPU-only `sv_traj_d3_wc` kernel, loaded by
  `carrier/kernels/sv_traj_d3_loader.py`; there is no CPU compute fallback. The sole compiled
  entry point consumes the within-cycle operation schedule. c64 is authorized only through the
  active `FusedWithinCycleSampler` optimization path.
- **Out of scope:** physics construction, tolerance selection, FET, and claim promotion. WG
  channels, codestates, composition, and CPTP checks are completed in c128 before the checked
  complex execution tables are cast at the fused-SV boundary.

## Engineering rationale

Small dense states can be launch-bound, while repeated local Kraus applications on larger states
benefit from avoiding full embedded operators and repeated tensor permutations. The fused path is
therefore an optional forward-engine acceleration, not a scientific gate and not evidence that every
workload benefits from GPU execution.

## Kernels

| Kernel | Replaces | Notes |
|---|---|---|
| `fused_local_kraus` | `embed_operator` + `apply_kraus` chain in `apply_channel_local` / `apply_unitary` (K=1) | one thread per output element; gathers the target-qubit subspace by bit arithmetic (qubit 0 = most significant, matching `circuit_sim`); raw (unhermitianized) sum — the torch side hermitianizes, matching `apply_kraus` exactly. Backward: `grad_rho` via the same kernel with the adjoint Kraus stack; `grad_kraus` via a small subspace-einsum composite (v2: fuse). |
| `qutrit_mcwf_ops` | repeated dense qutrit MCWF operations | c128-only reference path. It is not the c64 optimization engine. |
| `sv_traj_d3_wc` | per-operation Python/Torch launches for the d3 qutrit trajectory loop | separately compiled c128 (`complex128`/`float64`) and c64 (`complex64`/`float32`) ABIs. Only `run_purpose="optimization"` may use c64, and its artifact is `screening_only`; final/certification uses c128 and remains `c128_candidate`. Integer schedule tensors stay int32. Python and C++ guards validate dtype, device, shape, and index bounds before launch. |

## Verification boundary

`tests/test_kernels_fused_kraus.py` compares the fused forward result and gradients with the
reference Torch implementation. `tests/test_within_cycle_precision.py` pins the active SV
purpose/dtype/evidence contract. A c64 artifact never becomes evidence; a separate frozen c128
replay is required and is still only a candidate until the owning scientific gates pass.
Performance is workload- and device-dependent and must be measured in the actual simulator path;
historical fitting-workload timings are intentionally not part of this kernel contract.

## Build

JIT via `torch.utils.cpp_extension.load` on first use (ninja; nvcc from
`/usr/local/cuda`); no install step. `ECS_DISABLE_NATIVE_KERNELS=1` disables loading.
