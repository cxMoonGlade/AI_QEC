# Full-text note - Darmawan & Poulin, Tensor-Network Simulations of the Surface Code under Realistic Noise

> Provenance: full-text read from the cached PDF
> `docs/papers/bayes_tn/darmawan_poulin_realistic_noise_1607.06460.pdf`
> using `pdftotext -layout`. arXiv:1607.06460, Phys. Rev. Lett. 119, 040502 (2017).
>
> **Second full-text 精读 pass (2026-07-09, pre-PEPO-engine-build):** re-fetched + re-read end-to-end
> (`outputs/papers/pepo_survey/1607.06460.txt`, PyMuPDF, 8 pp incl. supplement). The original note
> below (Bayes-TN-decoder era) is accurate but MISSED the carrier-architecture facts the d5/d7
> DM-PEPO line is anchored on; the "CARRIER ARCHITECTURE FACTS" section below was added in this
> revision. Notably the note previously said only "over 100 data qubits" — the paper's exact figure
> is **153 data qubits (the 9×17 amplitude-damping lattice), simulated with the EXACT contraction**.

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

## CARRIER ARCHITECTURE FACTS (added 2026-07-09 — the DM-PEPO anchor content)

All verbatim-verified against the full text; these are the facts the d5/d7 PEPO prereg cites.

- **Scale:** "exact simulations on codes of up to **153 data qubits**" = the **9×17** amplitude-damping
  lattice (largest others: 9×9 depolarizing, 11×11 systematic rotation). Single round; syndrome
  measurements "performed perfectly" (assumed twice, intro + methods).
- **Layout:** the OPTIMIZED (rotated) layout of Bombin–Martin-Delgado [their ref 8]: qubits on the
  vertices of a W×L rectangular lattice, weight-4 x/z checks on alternating faces (checkerboard) +
  weight-2 boundary checks — the same family as our rotated XZZX patch.
- **Codestate construction:** |0⟩_L ∝ ∏_f ½(I+A_f)|0⟩^⊗N with each ½(I+A_f) a contraction of four
  bond-2 W(C) tensors (Q±=W(±X), R±=W(±Z); W(C)_{i,i',0}=δ_{i,i'}, W(C)_{i,i',1}=C_{i,i'}) — exactly
  the local-projector PEPS construction our §2.3 codestate plan uses.
- **Density-matrix network = SINGLE-layer:** per site B^(k)_{i,α} = A^(k) ⊗ A^(k)* (bra-ket fused
  into ONE tensor of bond dim D²) ⇒ ρ is one flat 2D network; noise = a local CPTP tensor update
  E_{ijj'i'} on the fused physical pair (Eq. 5); a check measurement appends the projector's Q±
  tensors (Eq. 6); Tr(Π_s ρ) caps the physical pairs → a scalar planar network. This is the
  "single-layer Tr(ρΠ)" structure the DESIGN correction block cites.
- **Syndrome sampling = sequential conditionals:** checks measured one at a time via
  q = Tr(P_{k+1} ρ_k); the same sequential-conditional pattern our engine's record law uses.
- **Two contraction routes + costs:** (i) EXACT column-merge contraction, memory exponential in the
  width — syndrome-sampling complexity **O(LW²·4^W)** (4^W = the (D²)^W column bond ceiling, W≤9
  reached); (ii) APPROXIMATE boundary-MPS (MPS×MPO, Schollwöck-style), **O(LW·χ³)**, with **χ = 8
  reproducing the exact logical-channel data** (same AD threshold within error; good agreement at
  low rates for SR + AD). ⇒ the D-P evidence that TRUNCATED χ_b ≪ the exact bisection ceiling —
  the P8 lever of the PEPO prereg.
- **Exact-contraction optimizations (supplement III):** absorb one Π_s layer into the other via
  trace cyclicity; z-checks commute with z-rotation noise → skip them (why SR reached 11×11);
  orient each check's 3 virtual bonds so only ONE crosses between columns; reuse unaffected column
  contractions across sequential check measurements and across C_ij rows (full C_ij in 2 lattice
  contractions).
- **Logical channel + decoding:** C_ij per syndrome via the half-encoded Bell state (CNOT-row tensor
  with an open ancilla virtual index); exact decoder = argmin over {I,X,Y,Z} of the 2-norm distance
  of D_s∘R_s∘N from identity — optimal given the exact channel; negligible extra cost once R_s∘N
  is contracted.
- **Headline discrepancy numbers:** at W=5, θ=0.005π systematic rotation: PTA UNDERESTIMATES the
  logical error rate by ~10¹⁰; HPA overestimates by ~10⁴. AD twirl ≈ exact (threshold 39±2% both);
  DP threshold 18.5±1.5% (consistent with the optimal 18.9(3)%). SR shows no clean threshold
  (symmetric about θ=0.25π; suppression stalls in 0.15π–0.225π).
- **Multi-round future work (their conclusion):** noisy measurements would need "PEPS time-evolution
  algorithms or ... contracting 3D tensor networks" — the gap our multi-round DM-PEPO engine fills.

## How To Use

- Use as the non-Pauli / coherent Bayes-TN forward-decoding reference.
- Use the Choi/logical-channel construction when designing metrics beyond Pauli LER.
- Do not cite it as evidence that syndrome-only data identifies arbitrary CPTP noise.
- (2026-07-09) Cite THIS note for the 153q / 9×17 / χ_b=8 / single-layer facts — they are now
  full-text-verified here (previously only carried by the DESIGN correction block + survey map).

