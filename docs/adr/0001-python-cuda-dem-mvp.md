# ADR 0001: Python plus C++/CUDA for the DEM Fault-Logit MVP

## Status

Accepted.

## Context

The first SCOPE-Static implementation needs a readable research layer, a precise DEM parity likelihood, and a path to GPU execution. The local environment already has Python, PyTorch with CUDA, Stim, CMake, `g++`, `nvcc`, and an RTX 5090. It does not currently have a Rust toolchain.

## Decision

Implement the research package in Python and isolate GPU-specific code behind a small likelihood module. Provide a pure PyTorch exact dynamic program as the correctness oracle and include C++/CUDA extension source for the parity-likelihood backend.

Rust is not part of the MVP implementation.

## Consequences

- Experiment code remains readable and easy to modify.
- The likelihood has a narrow interface that can move between PyTorch and C++/CUDA implementations.
- The Stage-1 claim remains limited to DEM/Bernoulli fault logits.
- Rust can be revisited later if a stable systems layer is worth the extra toolchain.
