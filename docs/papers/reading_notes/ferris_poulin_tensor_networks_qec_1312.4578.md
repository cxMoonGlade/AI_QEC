# Full-text note - Ferris & Poulin, Tensor Networks and Quantum Error Correction

> Provenance: full-text read from the cached PDF
> `docs/papers/bayes_tn/ferris_poulin_tensor_networks_qec_1312.4578.pdf`
> using `pdftotext -layout`. arXiv:1312.4578, PRL 113, 030501 (2014).

## Metadata

- **Authors.** Andrew J. Ferris, David Poulin.
- **Status.** Phys. Rev. Lett. 113, 030501 (2014); arXiv:1312.4578v3.
- **Role in the Bayes-TN line.** Foundational equivalence paper: decoding a QEC code can be written as a tensor-network contraction. It is not a surface-code performance baseline by itself.

## Executive Summary

Ferris and Poulin establish the conceptual bridge that makes the later Bayes-TN decoder literature natural: a QEC decoding problem is a conditional probabilistic inference problem, and the conditional distribution can be represented as a tensor network. For Clifford encoders with memoryless Pauli channels, the TN is built from the encoding circuit, local error-probability tensors, and syndrome indicator tensors. Conditioning on a syndrome means contracting the syndrome legs with indicator tensors; marginal decoding or logical decoding is then a contraction task.

The paper also maps code families to TN families: convolutional codes to MPS, concatenated codes to tree TNs, topological codes to PEPS/MERA-like structures, and polar/branching-MERA codes to efficiently contractible spectral/branching networks. The main new code proposal is branching-MERA quantum polar-like codes, not surface-code decoding.

For our project, the value is not an algorithm to import directly. The value is the citation that "Bayesian decoding = TN contraction" is a standard object, and that the posterior one computes need not be a pairwise graph object. It may be a marginal logical posterior, a global logical posterior, or an effective conditional channel.

## Bayes-TN Object

The paper's basic object is a conditional distribution over errors after observing syndrome information. In project notation, it justifies writing decoder inference as:

```text
P(error or logical event | syndrome, noise model)
```

and evaluating that quantity by tensor contraction.

In the appendix, the authors also extend the formulation beyond Clifford/Pauli to arbitrary encoding circuits and memoryless CPTP maps: the hard part of decoding becomes evaluating an effective conditional channel `F_{j|s}` by an `n`-point TN correlation. That is the conceptual predecessor of Darmawan-Poulin's logical-channel decoder.

## Contributions

- **C1. Formal equivalence between decoding and TN contraction.** The core construction conditions the error distribution on observed syndrome bits and contracts the resulting TN.
- **C2. Code-family/TN-family map.** MPS, tree TN, MERA, PEPS, polar/spectral TNs are linked to known QEC code families and decoder structures.
- **C3. Branching-MERA code proposal.** The paper proposes efficiently decodable branching-MERA quantum codes and compares them to quantum polar codes.
- **C4. General decoding appendix.** The appendix shows that the same logic can be phrased for CPTP channels via effective conditional channels, not only Pauli probability distributions.

## Method Notes

- For Clifford plus Pauli noise, local error probabilities are small tensors over `{I, X, Y, Z}`.
- Syndrome observations are indicator tensors that condition the distribution.
- Tracing out irrelevant qubits is a uniform contraction.
- For arbitrary CPTP noise, wires are doubled and the decoding quantity becomes an effective channel conditioned on the syndrome.

## Limitations

- The main text is not a modern surface-code TN decoder benchmark.
- The direct efficient algorithms are for special code/TN families, especially polar and branching-MERA codes.
- It does not solve noisy syndrome extraction, real hardware calibration, or parameter posterior inference.
- It is a conceptual foundation rather than the implementation reference for our Layer-1 engine.

## Relevance to `qec_twin`

1. **Terminology anchor.** This is the clean citation for saying that QEC decoding can be formulated as tensor-network Bayesian inference.
2. **Stops the pairwise trap.** The inferred object is not "pairwise edge rates"; it is a conditional distribution or channel obtained by summing over compatible latent histories.
3. **Bridge to later papers.** BSV turns the idea into surface-code coset probabilities; Darmawan-Poulin turns it into per-syndrome logical channels; Kobori-Todo puts a Bayesian posterior over noise parameters on top.
4. **Claim boundary.** Do not cite this as evidence that a practical surface-code Bayes-TN decoder beats MWPM on Google data. Use BSV/Darmawan/Kobori for that layer.

## How To Use

- Cite for the general equivalence: `decoding = TN contraction`.
- Do not use as the primary surface-code baseline.
- Do not use as proof that a freely learnable TN carrier is identifiable from syndromes.

