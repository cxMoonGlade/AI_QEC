# ADR 0002: GPU-First QEC Execution

## Status

Accepted.

## Context

The SCOPE-Static Google path is a large QEC preprocessing and local-likelihood
workflow. The target workstation is assumed to have a CUDA device, at least RTX
5090 class, even when a particular agent sandbox cannot see it. CPU execution is
not an accepted fallback for Google-data evidence or benchmark commands.

Recent S1.6 runs showed that the exact local-window likelihood can execute on
the C++/CUDA backend, while remaining runtime is often dominated by CPU-side
preparation: Stim/DEM parsing, `.b8` loading, observation aggregation,
window-cache construction, and cross-sample bookkeeping.

## Decision

GPU acceleration is P0 for this repository.

For serious runs, modules should prefer native CUDA/PyTorch/C++ execution. The
Google runner is GPU-only for current evidence paths: by default it uses CUDA
plus the `cuda_extension` backend when CUDA is visible; if CUDA is not visible,
the run fails and the environment must be fixed.

Performance work should prioritize:

- reusing prepared GPU caches across models, preprocessing modes, and samples;
- moving repeated preprocessing and aggregation out of Python loops;
- adding CUDA/C++ kernels for hot likelihood, window, and observation-cache
  paths;
- recording enough timing/audit metadata to distinguish GPU launch-bound work
  from CPU-preprocessing-bound work.

## Consequences

- Low `nvidia-smi` utilization is not sufficient evidence that the GPU path is
  inactive; local-window kernels can be bursty and launch-bound.
- CUDA invisibility in one agent/session is an environment issue to diagnose,
  not a reason to design CPU-first.
- Unit tests may mock Google runner outputs, but Google evidence commands should
  not fall back to CPU execution.
