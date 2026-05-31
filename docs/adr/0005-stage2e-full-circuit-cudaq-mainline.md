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

Use `full_circuit_cudaq` as the data-preparation full-circuit source. CUDA-QEC/NVIDIA-QEC companion
adapters, duck-test entry points, and optional install extras are not part of
the codebase mainline.

The public catalog gates are distinct. `PHYC1/PHYC2/PHYC3` remain legacy artifact
aliases:

```text
data_preparation: Data Preparation (Prep)
  generate sampled observations from the declared teacher contract

teacher: Teacher Self-Distinguishment (Teacher)
  teacher self-distinguishment; the teacher itself must classify every
  generated mechanism with BA, min recall, ARI, and NMI all equal to 1.0

learner: Learner Classification and Noise Generation (Learner)
  no-leakage learner recovery plus quantum/readout and visible-generation
  quality; learner must consume learner-visible grouped predictions, not teacher
  teacher-self predictions
```

The full-circuit teacher must:

- sample literal n-qubit CUDA-Q circuits at configured depth;
- keep entangling gates as circuit operations;
- preserve M0-M34 mechanism semantics;
- write progress/checkpoint artifacts for resumable long runs;
- refuse CPU fallback when `require_gpu: true`.

## Consequences

- `separability_v2` remains synthetic separability evidence.
- Born-local remains an exact local diagnostic with effective depth one.
- Stage 2 is closed as a no-leakage physical-mechanism catalog validation
  stage: the system can generate controlled noisy QEC observations from declared
  mechanisms, verify teacher/catalog separability, and train learner models
  that recover and replay learner-visible noisy observation distributions
  without oracle leakage. Stage 3 is the next claim boundary: remove direct
  mechanism-label supervision and test whether latent mechanism structure can be
  inferred from visible observations alone.
- CUDA-QEC/CUDA-QX can be reconsidered later for decoder-utility baselines, not
  as the data-preparation teacher engine.
