# Full-text note - Darmawan & Poulin, Linear-time General Decoding Algorithm for the Surface Code

> Provenance: full-text read from the cached PDF
> `docs/papers/bayes_tn/darmawan_poulin_linear_time_decoder_1801.01879.pdf`
> using `pdftotext -layout`. arXiv:1801.01879, Phys. Rev. E 97, 051302 (2018).

## Metadata

- **Authors.** Andrew S. Darmawan, David Poulin.
- **Status.** Phys. Rev. E 97, 051302 (2018); arXiv:1801.01879v2.
- **Role in the Bayes-TN line.** The practical decoder version of Darmawan-Poulin's non-Pauli/correlated-noise logical-channel TN.

## Executive Summary

This paper turns the 2017 realistic-noise TN simulator into a decoder that can exploit general noise features. The decoder takes a syndrome `s` and a known physical noise map `N`, approximately computes the syndrome-conditioned logical channel `E_{s,N}`, and chooses the logical Pauli correction that best inverts it.

The important statement for our architecture is that a Bayes-TN decoder can account for non-Pauli coherence and spatial correlations if the physical noise process can be represented as a two-dimensional tensor network. The paper explicitly frames the cost as:

```text
O(N D^3 chi^3)
```

where `N` is the number of physical qubits, `D` is the bond dimension of the noise CPTP map, and `chi` is the contraction bond dimension.

## Bayes-TN Object

The decoder computes an approximation to:

```text
E_{s,N} = R_s o N
```

restricted to the code space as a single-logical-qubit channel. For each logical Pauli correction `L in {I, X, Y, Z}`, it evaluates a logical error norm:

```text
|| L o E_{s,N} - I ||
```

and chooses the correction minimizing this value.

This is the non-Pauli analogue of BSV's coset posterior: the posterior object is a conditional logical channel, not an edge graph.

## Contributions

- **C1. General-noise surface-code decoder.** The decoder supports any physical CPTP map representable as a 2D TN, including local non-Pauli noise and certain spatially correlated noise.
- **C2. Approximate logical-channel contraction.** It uses PEPO/TN contraction to estimate the syndrome-conditioned logical channel.
- **C3. Orders-of-magnitude improvement over MWPM in tested regimes.** For amplitude damping and correlated bit-flip noise, the TN decoder substantially outperforms matching.
- **C4. Practical small-chi evidence.** The experiments fix `chi=8` and obtain near-optimal behavior in the studied settings.

## Results

- Under low-strength amplitude damping, the TN decoder is indistinguishable from the optimal decoder in the tested sizes and improves by orders of magnitude over MWPM.
- Near threshold, the TN decoder remains close to the optimal logical-channel decoder; MWPM is far worse.
- Under a correlated bit-flip model defined by a local Boltzmann distribution, the TN decoder improves over MWPM across the explored noise range.

## Limitations

- The noise model `N` is assumed known.
- Syndrome measurements are noiseless; noisy extraction requires a 3D TN.
- The paper does not infer `N` from data and does not quantify posterior uncertainty over `N`.
- The final correction set is Pauli logical corrections; the internal channel can be non-Pauli, but the actuator is still a correction choice.

## Relevance to `qec_twin`

1. **This is the decoder engine we should mean by non-Pauli Bayes-TN.** It consumes `s` and `N`, computes a logical channel posterior, and selects a correction.
2. **Strong separation of roles.** Our learner should provide `N` or a posterior over `N`; the TN decoder computes `P(logical/channel | s, N)`.
3. **Architecture implication.** A self-calibrating decoder can be structured as:

```text
syndrome history -> posterior over theta/N -> TN logical-channel posterior -> correction/reranking
```

4. **Not a toy path.** This is directly surface-code, non-Pauli, and decoder-performance relevant.

## How To Use

- Treat as the main implementation reference for a non-Pauli Bayes-TN decoder.
- Use its logical-channel computation as the target abstraction for a `forward/scalable` posterior engine.
- Pair with Kobori-Todo for learning/updating the noise parameters rather than assuming them.

