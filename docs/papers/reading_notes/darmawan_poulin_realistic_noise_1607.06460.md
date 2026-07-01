# Full-text note - Darmawan & Poulin, Tensor-Network Simulations of the Surface Code under Realistic Noise

> Provenance: full-text read from the cached PDF
> `docs/papers/bayes_tn/darmawan_poulin_realistic_noise_1607.06460.pdf`
> using `pdftotext -layout`. arXiv:1607.06460, Phys. Rev. Lett. 119, 040502 (2017).

## Metadata

- **Authors.** Andrew S. Darmawan, David Poulin.
- **Status.** Phys. Rev. Lett. 119, 040502 (2017); arXiv:1607.06460v2.
- **Role in the Bayes-TN line.** Extends surface-code TN simulation and decoding from stochastic Pauli coset probabilities to arbitrary local CPTP noise via per-syndrome logical channels.

## Executive Summary

Darmawan and Poulin introduce a tensor-network method to simulate surface-code error correction under arbitrary local noise, including non-Clifford / non-Pauli channels such as amplitude damping and systematic coherent rotation. The key move is to represent the encoded Bell state and its noisy density matrix as a PEPS/PEPO-like tensor network, apply local CPTP maps and syndrome projectors, and contract the resulting network to compute the per-syndrome logical channel.

This shifts the Bayes-TN object from BSV's four Pauli coset probabilities to a richer conditional channel:

```text
E_{L,s,N} = logical channel induced by physical noise N and syndrome s
```

The decoder then chooses the Pauli correction that minimizes a distance between this logical channel and the identity. This is the right ancestor for a non-Pauli Bayes-TN model: coherence is not compressed to independent Pauli edge probabilities before inference.

## Bayes-TN Object

For a known physical noise map `N` and observed syndrome `s`, the method computes the logical process matrix:

```text
C_ij(s, N) = Tr([P_i tensor P_j] ((R_s o N) tensor I)(|Psi+><Psi+|))
```

where `R_s` is the recovery-to-codespace map associated with syndrome `s`. The decoder chooses the correction that makes the resulting logical channel closest to identity.

This is Bayesian in the decoder sense: the syndrome-conditioned posterior object is no longer only a discrete logical class; it is a syndrome-conditioned logical channel.

## Contributions

- **C1. TN simulation of arbitrary local surface-code noise.** The method applies CPTP maps to a density-matrix TN and samples/checks syndromes by sequential projector contractions.
- **C2. Per-syndrome logical-channel computation.** The logical channel is computed via a Choi/Bell-state construction, then used for decoding.
- **C3. Non-Pauli benchmark results.** The method studies amplitude damping and systematic rotation channels, comparing exact channels to Pauli-twirl and honest-Pauli approximations.
- **C4. Approximate contraction with small `chi`.** Approximate contraction with `chi=8` matches exact results well in the tested regimes.

## Results

- For amplitude damping, the Pauli twirl can reproduce the threshold reasonably, while honest Pauli approximation is pessimistic.
- For systematic coherent rotation, Pauli approximations can be dramatically wrong below threshold; the paper reports a case where the Pauli twirl underestimates logical error by many orders of magnitude.
- Exact simulation reaches surface-code systems with over 100 data qubits for the studied settings, far beyond brute-force state-vector/density-matrix simulation.
- Approximate TN contraction reproduces exact data well for the tested non-Pauli channels.

## Limitations

- The physical noise model is assumed known.
- It is a forward simulator / decoder substrate, not a noise-parameter inference method.
- Syndrome measurements are perfect; noisy syndrome extraction is left as a future 3D TN problem.
- The decoder ultimately chooses among Pauli logical corrections, although the internal object is a coherent/non-Pauli logical channel.

## Relevance to `qec_twin`

1. **Non-Pauli posterior carrier.** This is the key reference for not reducing TN decoding to pairwise/Pauli edge models.
2. **Correct object for coherence.** The relevant posterior object is `E_{L,s,N}`, a conditional logical channel, not just a logical bit.
3. **Validation target.** If we build a differentiable Bayes-TN layer, dense exact d=3/d=5 windows can validate this logical-channel contraction.
4. **Claim boundary.** The paper assumes known `N`. Our novelty is learning a useful posterior over `N` or its parameters from syndrome data, then using the TN posterior engine.

## How To Use

- Use as the non-Pauli / coherent Bayes-TN forward-decoding reference.
- Use the Choi/logical-channel construction when designing metrics beyond Pauli LER.
- Do not cite it as evidence that syndrome-only data identifies arbitrary CPTP noise.

