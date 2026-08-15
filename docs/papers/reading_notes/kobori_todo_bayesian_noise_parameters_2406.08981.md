# Full-text note - Kobori & Todo, Bayesian Inference of General Noise-Model Parameters from Surface-Code Syndrome Statistics

> Provenance: full-text read from the cached PDF
> `docs/papers/bayes_tn/kobori_todo_bayesian_noise_parameters_2406.08981.pdf`
> using `pdftotext -layout`. arXiv:2406.08981v3, dated 2025-10-21.

## Metadata

- **Authors.** Takumi Kobori, Synge Todo.
- **Status.** arXiv:2406.08981v3.
- **Role in the Bayes-TN line.** The closest direct prior art for Bayesian inference of non-Pauli noise parameters from syndrome statistics using a tensor-network likelihood.

## Executive Summary

Kobori and Todo add the missing Bayesian parameter-inference layer on top of surface-code TN simulation. Earlier Bayes-TN decoders assume the physical noise model is known and compute `P(logical | syndrome, noise)` or a syndrome-conditioned logical channel. This paper asks how to infer the noise parameters themselves from syndrome statistics:

```text
P(alpha | syndrome history) proportional to P(syndrome history | alpha) P(alpha)
```

The likelihood `P(m | alpha)` is evaluated by a surface-code TN simulator, and the posterior is sampled with Monte Carlo methods. For stationary parameters, they use MCMC. For time-varying parameters, they use sequential Monte Carlo (SMC) / particle filtering. They test amplitude damping, phase damping, systematic rotation, two-parameter combinations, nonuniform parameters, and time-varying drift.

This is the most relevant paper for our current Layer-1 direction: the TN is a likelihood/posterior engine; the output is a posterior over noise-model parameters, not merely a fitted DEM.

## Bayes-TN Object

The parameter posterior is:

```text
P(alpha | m_0:n-1) proportional to P(m_0:n-1 | alpha) P(alpha)
```

where `alpha` parameterizes a general physical noise model and `m` denotes syndrome measurements.

The likelihood is computed by TN simulation of the surface code:

```text
P(m | alpha) = Tr[ product_i (I + m_i g_i)/2  E_alpha(rho) ]
```

For time-varying noise, SMC maintains particles over the parameter trajectory and updates particle weights by the per-time likelihood.

## Contributions

- **C1. Bayesian non-Pauli noise-parameter inference from syndrome data.** The paper moves beyond Pauli syndrome-estimation methods by using a general TN simulator for likelihood evaluation.
- **C2. MCMC for stationary noise.** Metropolis-Hastings samples the posterior using only the TN likelihood and prior.
- **C3. SMC for time-varying noise.** A bootstrap-filter-style particle method tracks drifting parameters using sequential syndrome data.
- **C4. Estimability diagnosis.** Some parameters are not learnable from the chosen syndrome statistics, and the paper ties this to weak likelihood dependence rather than treating it as optimizer failure.
- **C5. Decoder impact check.** Updating the TN decoder with inferred non-Pauli parameters improves performance over stale/no-update and Pauli-assumed alternatives in the time-varying amplitude-damping example.

## Method Notes

- Priors matter because syndrome statistics can have alias symmetries; the paper uses restricted uniform priors to avoid physically unreasonable duplicate solutions.
- MCMC samples the stationary posterior with a TN-computed likelihood.
- SMC uses proposal dynamics for parameter drift, likelihood weighting, resampling, and smoothing over recent EAP estimates.
- The paper stresses that for general non-Pauli noise, syndrome statistics can depend on initial logical information, unlike Pauli noise.
- Randomized compiling is discussed but not accepted as a complete reason to ignore general-noise estimation, partly because exact randomized compilation can be costly and its practical scaling remains unclear.

## Results

- One-parameter uniform amplitude damping, phase damping, and systematic rotation are estimated successfully.
- Systematic rotation has multimodal likelihood structure; simple MCMC plus EAP can fail unless the prior restricts the posterior to one mode.
- TN truncation introduces bias for too-small `chi`, but `chi=8` is reported as adequate in the amplitude-damping test and is consistent with earlier Darmawan-Poulin contraction experience.
- Two-parameter AD+dephase is estimable, with larger error bars than one-parameter cases.
- Generalized amplitude damping has a parameter that is difficult to estimate; the likelihood depends weakly on it.
- Nonuniform amplitude-damping parameters can be estimated, but require more syndrome samples.
- SMC tracks sinusoidal and linear time-varying amplitude damping, including nonuniform time-varying parameters.
- Using the tracked non-Pauli estimate improves TN decoder performance relative to stale parameters, MWPM, and a Pauli-assumed estimation arm.

## Limitations

- Experiments are code-capacity and Markovian; phenomenological/circuit-level syndrome extraction remains future work.
- Monte Carlo estimation is slow for practical online QEC without parallelization or thinning.
- MCMC with simple EAP is fragile for multimodal likelihoods; exchange Monte Carlo is suggested.
- Some general-noise parameters are not identifiable from the syndrome statistics used.
- The method assumes a declared parameterized noise family. It is not a fully nonparametric channel learner.

## Relevance to `qec_twin`

1. **Closest prior art for our Bayes layer.** This is the paper that says: infer `P(theta | syndrome history)` with a TN likelihood, then feed the decoder.
2. **Normalization and posterior bands.** The posterior, not a point estimate, is the correct object for uncertainty and alias bands.
3. **Learnable normalization signal.** Parameters that weakly change the likelihood should shrink or remain uncertain; that is not a failure if they also weakly affect decoder performance.
4. **Drift axis.** SMC is the natural formalism for our cross-window / temporal stitching layer. GNN/SSM can be amortization around this, not a replacement for posterior accounting.
5. **Claim boundary.** The paper does not solve circuit-level Google syndrome data or non-Markovian leakage/crosstalk. It gives the right probabilistic skeleton.

## How To Use

- Treat as the primary reference for `P(theta | syndrome history)` in a Bayes-TN architecture.
- Use MCMC for offline calibration experiments and SMC for drift/online experiments.
- Use held-out syndrome NLL, posterior calibration, and downstream decoder performance as the standard metric ladder.
- Do not collapse the posterior to a pairwise/hyperedge selection question.

