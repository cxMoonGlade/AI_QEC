# DEM Likelihood CUDA Backend

The Python likelihood module owns the public interface. This directory contains
an optional C++/CUDA backend for the exact DEM parity dynamic program and the
batched local-window exact likelihood used by the Google S1.6 path.

The pure PyTorch implementation is the correctness oracle. The extension is
intentionally narrow: it receives fault logits, packed parity masks, and `B`,
then returns exact parity-state distributions or local-window NLLs. When
gradients are enabled, the Python wrapper uses a custom autograd path backed by
a CUDA adjoint dynamic program. Detached local-window evaluation uses a
forward-only CUDA kernel to avoid building gradient history.

`window_cache.cpp` / `window_cache_kernel.cu` build the observation
state/count tables for local windows on the GPU. They are cache-preparation
support, not a new statistical model: the output is the same
`WindowBatchNLLCache` consumed by the existing exact local-window likelihood.
The Google runner can persist these prepared caches on disk via
`--prepared-cache-dir` so repeated transfer runs do not rebuild identical
window histograms.

Training supports an opt-in spectral shadow path for the local-window exact
gradient. The default `dp` kernel remains the production reference.
`spectral_shadow` computes both DP and spectral gradients, returns the DP
result, and raises if the spectral result disagrees. The spectral kernel uses
active fault-window pairs from `WindowBatchNLLCache`; it does not allocate
history over all DEM faults. Explicit `spectral` mode is guarded by
`spectral_min_abs_factor` and a spectral memory cap.

For one window `W`, the spectral path evaluates the exact Walsh form
`P(y_W) = 2^-|W| sum_s (-1)^(s dot y_W) prod_j m_j(s)`, where
`m_j(s) = 1` when `s dot a_{j,W} = 0` and `m_j(s) = 1 - 2 sigmoid(lambda_j)`
otherwise. Gradients use prefix/suffix leave-one-out products over active
faults in the window.

The Stage-1 claim does not depend on Stim sampling as likelihood. Stim only constructs DEMs and optional samples.
