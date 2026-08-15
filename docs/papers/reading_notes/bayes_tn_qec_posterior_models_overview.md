# Overview - Bayes-TN Posterior Models for QEC

> Built from full-text reads of five cached PDFs in `docs/papers/bayes_tn/`.
> Scope: tensor-network methods where the central object is a Bayesian posterior
> or posterior-like conditional quantity in QEC, not pairwise edge fitting.

## The Core Object

The correct abstraction is:

```text
P(logical class or logical channel | syndrome, noise model)
```

plus the higher layer:

```text
P(noise-model parameters | syndrome history)
```

This is the architecture split we should use:

```text
syndrome history
  -> posterior over theta / channel field
  -> TN posterior engine for P(logical | syndrome, theta)
  -> correction / reranking / Bayes floor / decoder-prior utility
```

This is not a pairwise-vs-hyperedge decision. Pairwise/hyperedge terms may be exports, diagnostics, or priors, but the Bayes-TN model class is a posterior engine over compatible error histories or logical channels.

## Five-Paper Map

| Paper | Posterior Object | TN Role | Noise Class | What We Borrow |
|---|---|---|---|---|
| Ferris-Poulin 1312.4578 | Conditional error/logical distribution; effective conditional channel in appendix | General proof that decoding = TN contraction | Clifford/Pauli in main text; memoryless CPTP in appendix | Conceptual legitimacy and terminology |
| Bravyi-Suchara-Vargo 1405.4883 | Four logical coset probabilities given syndrome | MPS contraction of 2D surface-code TN | Stochastic iid Pauli, noiseless syndrome | Canonical Bayes-TN decoder baseline |
| Darmawan-Poulin 1607.06460 | Syndrome-conditioned logical channel | PEPS/PEPO surface-code TN forward simulation | Arbitrary local CPTP, including non-Pauli | Non-Pauli logical-channel posterior carrier |
| Darmawan-Poulin 1801.01879 | Approximate logical channel used to choose correction | Linear-time approximate TN decoder | 2D TN-representable CPTP, including correlations | Practical non-Pauli/correlated Bayes-TN decoder |
| Kobori-Todo 2406.08981 | Posterior over noise parameters from syndrome history | TN likelihood inside MCMC/SMC | General parameterized code-capacity noise | Bayesian calibration and drift layer |

## Architecture Consequence

Layer 1 should be framed as a **Bayesian TN posterior model**, not as a DEM edge model:

1. **Parameter posterior.** Use Kobori-style `P(theta | syndrome history)` as the recover/calibration object.
2. **Decoder posterior.** Use BSV/Darmawan-style TN contraction to compute `P(logical | s, theta)` or `E_{L,s,theta}`.
3. **Posterior predictive.** Integrate or sample over `theta` instead of pretending a single point estimate is earned:

```text
P(logical | s, data) = integral P(logical | s, theta) P(theta | data) dtheta
```

4. **Export is secondary.** A DEM or hypergraph can be emitted for PyMatching/Tesseract compatibility, but it is a lossy export from the posterior model.

## Metrics

Use the repo's standard-metric ladder:

- **Held-out syndrome NLL** for `P_theta(s)` or posterior predictive `P(s | data_train)`.
- **Bayes-optimal / MAP syndrome decoder LER** when exact or bounded.
- **Decoder-prior utility `%Delta LER`** under a frozen named decoder when exporting priors.
- **Logical-channel distance** for non-Pauli posterior objects, following Darmawan-Poulin/Bravyi-line metrics.
- **Posterior calibration / credible coverage** for parameter posterior claims.

## Relation To dMLE, SI1000, And AlphaQubit

- **dMLE.** A differentiable MLE TN likelihood engine. Important, but it returns point estimates under a Pauli/DEM parameterization rather than a Bayesian posterior. It is adjacent, not the Bayes-TN spine.
- **SI1000.** A baseline and possible topology/initialization prior, not the model.
- **AlphaQubit.** A learned decoder comparator. It should be compared on held-out LER/logical accuracy, but it does not replace the posterior model or explain the noise.

## Project Decision

The next serious model direction should be:

```text
Bayesian noise posterior + TN logical posterior
```

with optional amortization later:

```text
SMC / MCMC posterior core
  + neural proposal or low-dimensional drift state
  + GNN/SSM only for amortized stitching/proposals
```

This keeps the model disciplined: the TN computes the posterior, the Bayesian layer carries uncertainty, and neural components propose or amortize rather than silently becoming the scientific object.

