# AI QEC Domain Context

This repository is currently centered on the SCOPE family of QEC noise-learning experiments.

## Terms

- **SCOPE-Twin**: the larger future model class that maps QEC circuit/control context into a physically constrained noise parameter field.
- **SCOPE-Static**: the fixed-context DEM/Bernoulli path. Stage 1 uses known orbit labels; Stage 2 static discovery learns hidden sharing assignments.
- **SCOPE-Static Discovery**: the Stage 2 fixed-context prototype that replaces the known orbit map with a learned assignment matrix `S[j, k]` over DEM-fault prototypes.
- **DEM parity map**: a binary matrix `A in F_2^{B x M}` mapping Bernoulli DEM fault bits to observed detector/logical bits via `y = A e mod 2`.
- **Observation bits**: the concatenation of detector bits and logical observable bits. Their count is `B`.
- **Fault mechanisms**: DEM error mechanisms. After duplicate-mask canonicalization, their effective count is `M`.
- **Orbit**: a known grouping of effective fault mechanisms used for hard sharing or soft feature sharing. Its count is `O`.
- **Soft feature orbit field**: a compressed fault-logit field `lambda_j = alpha[omega(j)] + dot(beta[omega(j)], phi[j])`, where `phi[j]` is a fixed centered residual feature.
- **Discovery assignment**: a learned row-stochastic matrix `S` or `Pi`. Do not call it `A`; `A` is reserved for the DEM parity map.
- **Prototype count**: `K` is the number of discovered Stage 2 DEM-fault prototypes. `K_t` is reserved for later template-specific SCOPE-Discovery.
- **d_Q^DEM**: the Stage-1 quotient-aware logit distance over only DEM-preserving fault permutations.
- **Window plan**: a reproducible set of observation-bit windows used by local exact likelihood training/evaluation, including builder config and audit metadata.
- **Logical-aware window plan**: a window plan that includes the logical observable bit directly, especially through deduplicated logical fault-support windows, so local exact likelihood evidence tests detector-logical coupling rather than detector-local syndromes alone.
- **Excess window NLL**: local-window model cross-entropy minus the heldout empirical entropy of the same projected windows. It is reported in nats per window and is the real-data analogue of an oracle delta NLL when no hidden teacher distribution is available.
- **Model-comparison effect sizes**: derived evidence fields that rescale excess window NLL into milli-nats per window, paired deltas versus the uncompressed `local` baseline, and diagnostic pseudo-likelihood deltas per shot. These make small but real local-window gaps readable; they do not change the training objective and are not global exact NLL claims.
- **Likelihood objective**: a prepared training objective over the DEM parity map, such as global exact, detector-only exact, or local-window exact likelihood.
- **Exact local-window parity likelihood**: the Stage-1 mathematical objective that evaluates the Bernoulli DEM parity model exactly on a prepared set of observation-bit windows. It consumes logits over effective DEM fault columns and is independent of orbit, discovery, Google schedule, or preprocessing choices. It does not choose the windows; detector/logical coverage belongs to the window plan and evidence audit.
- **GPU batched local-window exact adapter**: the C++/CUDA implementation of local-window exact likelihood that evaluates all prepared windows in one extension call and returns a first-order gradient for SCOPE-Static training.
- **Evidence record**: one metrics row for a trained SCOPE-Static model, including likelihood source, compression audit, baseline metadata, and threshold inputs.
- **Experiment plan**: the normalized SCOPE-Static run matrix compiled from YAML, including residual ranks, teacher cases, shot budgets, model names, backend choice, and output identity.

## Claim Boundary

The current implemented evidence package studies sample efficiency, compression,
and quotient-aware recovery for a fixed DEM/Bernoulli Stage 1 setting. It does
not claim CPTP/GKSL learning, Born-rule likelihood, context-conditioned
amortization, OOD transfer, or temporal drift tracking.

Stage 2 static discovery is specified in `docs/SCOPE_STATIC_DISC.md`. It may
claim latent assignment recovery only after synthetic teacher runs report
permutation-invariant discovery metrics such as ARI and NMI. Google hardware
datasets are external empirical validation data, not oracle hidden-partition
teachers.
