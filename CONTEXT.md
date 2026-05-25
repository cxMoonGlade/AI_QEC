# AI QEC Domain Context

This repository is currently centered on the SCOPE family of QEC noise-learning experiments.

## Terms

- **SCOPE-Twin**: the larger future model class that maps QEC circuit/control context into a physically constrained noise parameter field.
- **SCOPE-Static**: the first fixed-context stage. In this repository's current MVP, it means a DEM/Bernoulli fault-logit model, not a CPTP/GKSL channel model.
- **DEM parity map**: a binary matrix `A in F_2^{B x M}` mapping Bernoulli DEM fault bits to observed detector/logical bits via `y = A e mod 2`.
- **Observation bits**: the concatenation of detector bits and logical observable bits. Their count is `B`.
- **Fault mechanisms**: DEM error mechanisms. After duplicate-mask canonicalization, their effective count is `M`.
- **Orbit**: a known grouping of effective fault mechanisms used for hard sharing or soft feature sharing. Its count is `O`.
- **Soft feature orbit field**: a compressed fault-logit field `ell_j = alpha[o(j)] + dot(beta[o(j)], phi[j])`, where `phi[j]` is fixed.
- **d_Q^DEM**: the Stage-1 quotient-aware logit distance over only DEM-preserving fault permutations.

## Claim Boundary

The current MVP only studies sample efficiency, compression, and quotient-aware recovery for a fixed DEM/Bernoulli setting. It does not claim CPTP/GKSL learning, Born-rule likelihood, context-conditioned amortization, latent quotient discovery, OOD transfer, or temporal drift tracking.
