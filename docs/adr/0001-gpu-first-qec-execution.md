# ADR 0001: GPU-First QEC Execution

## Status

Accepted. Reframed 2026-06-06 to the twin context; the original SCOPE-Static / catalog
framing (Google runner, `cuda_extension` backend, S1.6 local-window kernels, `.b8`
loading) is retired (ADR 0005). The GPU-first decision itself is unchanged.

## Context

The twin (`qec_twin`; `docs/TWIN.md`) is GPU-heavy. The exact differentiable forward
(`forward/exact`) is a dense density-matrix simulator (`2^n × 2^n`); calibration is a
multi-context Born-NLL optimization; the uncertainty bands extremize ΔLER **numerically**
over the CPTP-consistent set with finite-shot bootstrap (ADR 0004). Calibration sweeps,
band search, and probe-richness ablations are the heavy paths, and the deferred scalable
backend (`forward/scalable`, >50q) will be heavier still.

The target workstation is assumed to have a CUDA device, at least RTX 5090 class, even
when a particular agent sandbox/session cannot see it. The working environment is the
`aiqec` conda env. CPU-only timing is **not** evidence of a GPU-path failure.

## Decision

GPU acceleration is P0 for this repository.

- Serious calibration, band, drift, and large-ablation runs prefer native CUDA/PyTorch
  execution; verify CUDA visibility from `aiqec` before long runs.
- CUDA invisibility in one sandbox/session is an **environment issue to diagnose, not a
  reason to design CPU-first**. CPU paths exist for correctness tests and tiny toys (the
  exact rep-code toy runs on either), not as the performance fallback for evidence runs.

## Consequences

- Low `nvidia-smi` utilization is not sufficient evidence the GPU path is inactive — the
  ≤~15q feasibility backend's kernels can be bursty and launch-bound.
- Wrappers (`/usr/bin/time`, Conda `--no-capture-output`) can make Torch report no
  CUDA/NVML even on a healthy GPU; prefer in-process `time.perf_counter()` for
  benchmarks, or get the wrapped command approved before treating CUDA invisibility as a
  real failure.
- When utilization is low, first check whether the workload is launch-bound or
  CPU-preprocessing-bound (forward/cache construction, Stim/DEM parsing) before
  concluding the GPU path is broken.
- Operational how-to (the CUDA-visibility check command, wrapper caveats) lives in
  `AGENTS.md` § "GPU-first execution"; this ADR is the decision record.

## References

`AGENTS.md` (GPU-first execution + commands), `docs/TWIN.md` (object / forward),
ADR 0004 (the band/bootstrap compute), ADR 0005 (retired the original program framing).
