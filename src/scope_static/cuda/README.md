# DEM Likelihood CUDA Backend

The Python likelihood module owns the public interface. This directory contains an optional C++/CUDA backend for the exact DEM parity dynamic program.

The pure PyTorch implementation is the correctness oracle. The extension is intentionally narrow: it receives fault logits, packed parity masks, and `B`, then returns the exact parity-state distribution. When gradients are enabled, the Python wrapper uses a custom autograd path backed by a CUDA adjoint dynamic program.

The Stage-1 claim does not depend on Stim sampling as likelihood. Stim only constructs DEMs and optional samples.
