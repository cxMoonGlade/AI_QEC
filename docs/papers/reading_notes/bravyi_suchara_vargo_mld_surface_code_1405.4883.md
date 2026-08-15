# Full-text note - Bravyi, Suchara & Vargo, Efficient Algorithms for Maximum Likelihood Decoding in the Surface Code

> Provenance: full-text read from the cached PDF
> `docs/papers/bayes_tn/bravyi_suchara_vargo_mld_surface_code_1405.4883.pdf`
> using `pdftotext -layout`. arXiv:1405.4883, Phys. Rev. A 90, 032326 (2014).

## Metadata

- **Authors.** Sergey Bravyi, Martin Suchara, Alexander Vargo.
- **Status.** Phys. Rev. A 90, 032326 (2014); arXiv:1405.4883.
- **Role in the Bayes-TN line.** The canonical surface-code maximum-likelihood / Bayes-TN decoder reference for noiseless syndrome extraction and stochastic Pauli noise.

## Executive Summary

This paper defines the Bayes-TN decoder object we should mean when we say "TN baseline" for the surface code. Given an observed syndrome, the decoder computes four coset probabilities corresponding to the logical classes `I`, `X`, `Y`, and `Z`, and returns a recovery in the most likely coset. The computation is a partition-function / tensor-network contraction over all stabilizer-equivalent error configurations compatible with the syndrome.

Two implementations are given. For pure bit-flip noise, maximum likelihood decoding is reduced to a matchgate / fermionic Gaussian calculation and is exact in `O(n^2)`. For depolarizing noise and more general stochastic iid Pauli noise, the coset probabilities are written as contractions of a 2D tensor network on an extended surface-code lattice, approximated by MPS contraction with bond dimension `chi`, with cost `O(n chi^3)`.

The result is important because it makes the posterior object explicit:

```text
posterior logical class = argmax_{L in {I,X,Y,Z}} pi(f(s) L G)
```

This is not edge fitting. It is Bayesian summation over all compatible errors in a logical coset.

## Bayes-TN Object

For a syndrome `s`, choose one representative Pauli error `f(s)` with that syndrome. The errors compatible with `s` decompose into four stabilizer cosets:

```text
f(s)G, f(s)XG, f(s)YG, f(s)ZG
```

The decoder computes their probabilities under the noise model and chooses the largest. In our language:

```text
P(m | s, theta) proportional to sum_e 1[Ae=s, L(e)=m] P_theta(e)
```

The MPS/TN contraction is the computational engine for those sums.

## Contributions

- **C1. Precise MLD definition for the surface code.** The paper formalizes decoding as selecting the most likely logical coset conditioned on syndrome.
- **C2. Exact matchgate implementation for X-noise.** For independent bit-flip noise, MLD maps to a matchgate circuit / fermionic Gaussian simulation with `O(n^2)` runtime.
- **C3. Approximate MPS contraction for iid stochastic Pauli noise.** The surface-code coset probability becomes a 2D TN contraction; MPS approximates the column-by-column contraction.
- **C4. Strong empirical baseline.** For X-noise, `chi=6` or `8` is virtually indistinguishable from exact MLD. For depolarizing noise, small `chi` strongly outperforms MWPM and captures X/Z correlations ignored by matching.

## Method Notes

- The four logical coset probabilities are the sufficient statistics for maximum-likelihood decoding.
- The approximate TN is built on an extended lattice with stabilizer nodes and qubit nodes.
- Each tensor depends on the local Pauli error probabilities and on the chosen syndrome representative.
- Column contraction uses MPOs acting on an MPS boundary state, with Schmidt truncation controlling approximation.
- The paper notes that unlikely cosets may converge more slowly than the winning coset; for decoding, identifying the winner matters more than accurate absolute probabilities for every coset.

## Results

- X-noise exact ML threshold is consistent with the known Nishimori-line value around 10.9%.
- For X-noise at distance 25, MPS with `chi=6,8` is nearly indistinguishable from exact MLD.
- For depolarizing noise, MPS with small `chi` gives much lower logical error than MWPM because MWPM ignores X/Z correlations.
- The MPS decoder shows a threshold-like behavior for depolarizing noise, though the exact ML threshold is not reached with fixed small `chi`.

## Limitations

- Noise is stochastic Pauli, iid in the studied models.
- Syndrome extraction is noiseless; the authors identify noisy syndrome extraction as a 3D TN problem.
- There is no learning of the noise model. The decoder assumes `theta` is known.
- It computes Pauli logical-coset posteriors, not a coherent logical channel.

## Relevance to `qec_twin`

1. **This is the true Bayes-TN decoder baseline.** It computes `P(logical class | syndrome, theta)` by summing compatible histories.
2. **It defines the posterior metric we need.** We can score posterior odds, MAP LER, gap to Bayes optimum, and coset calibration, not just edge likelihood.
3. **It separates model and inference.** The TN is a posterior engine given `theta`; it does not solve `P(theta | data)`.
4. **It frames the next layer.** Kobori-Todo puts a posterior over `theta`; Darmawan-Poulin generalizes the posterior object beyond stochastic Pauli cosets.

## How To Use

- Use as the canonical Bayes-TN decoder citation.
- Compare AlphaQubit against this family as a decoder baseline, not against dMLE.
- For our Layer-1 architecture, use BSV for the posterior engine shape and Kobori-Todo for parameter posterior learning.

