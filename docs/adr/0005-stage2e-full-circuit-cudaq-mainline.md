# ADR 0005: Stage 2E Full-Circuit CUDA-Q Mainline

## Status

Accepted.

## Context

CUDA-QEC/CUDA-QX provides useful QEC memory-circuit, DEM, and decoder
infrastructure, but it does not natively express the repository's M0-M34
mechanism semantics over arbitrary full-circuit tomography schedules. A
CUDA-QEC memory-circuit artifact would not satisfy the Stage 2E physical
teacher contract.

The required Stage 2E teacher contract is:

```text
rho_probe -> full n-qubit ideal schedule of configured depth d
-> mechanism channels/readout -> sampled observations
```

## Decision

Use `full_circuit_cudaq` as the PHYC1 mainline. CUDA-QEC/NVIDIA-QEC companion
adapters, duck-test entry points, and optional install extras are not part of
the codebase mainline.

The full-circuit teacher must:

- sample literal n-qubit CUDA-Q circuits at configured depth;
- keep entangling gates as circuit operations;
- preserve M0-M34 mechanism semantics;
- write progress/checkpoint artifacts for resumable long runs;
- refuse CPU fallback when `require_gpu: true`.

## Consequences

- `separability_v2` remains synthetic separability evidence.
- Born-local remains an exact local diagnostic with effective depth one.
- Full-circuit CUDA-Q artifacts are the Stage 2E acceptance surface.
- CUDA-QEC/CUDA-QX can be reconsidered later for decoder-utility baselines, not
  as the PHYC1 teacher engine.
