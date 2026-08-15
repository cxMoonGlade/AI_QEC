# Reading note: Szańkowski, Trippenbach & Cywiński, "Spectroscopy of cross-correlations of environmental noises with two qubits" (arXiv:1507.03897, PRA 2016)

> **Provenance (2026-07-05): FULL-TEXT read (精读).** PDF → txt `outputs/papers/1507.03897.txt`
> (10 pages). Published as Phys. Rev. A 94, 012109 (2016).
> Adjudication target: does this paper provide a method for directly MEASURING the
> cross-correlation between noises on two qubits — i.e., a direct observable of the r = g₁/g₀ ratio?
> **Verdict: YES — it provides the exact dynamical decoupling protocol for reconstructing
> S₁₂(ω), the cross-spectrum that encodes r.**

## Metadata [paper]
- **Authors:** Piotr Szańkowski, Marek Trippenbach (U. Warsaw), Łukasz Cywiński (IFPAN)
- **Venue / status:** arXiv:1507.03897 [cond-mat.mes-hall], 2015 → Phys. Rev. A 94, 012109 (2016)
- **Type:** theory (DD-based noise spectroscopy extended to two qubits)

## Executive summary [paper]
Extends dynamical-decoupling-based noise spectroscopy (DDENS) from single-qubit to two-qubit
systems. By applying sequences of π pulses to two spatially separated qubits, one can reconstruct
the full **cross-correlation spectrum S₁₂(ω)** of the environmental noises acting on them. Key
results:
- Same sequence on both qubits → **real part S^R₁₂(ω)** (degree of common noise at frequency ω)
- Two distinct sequences (PDD on one, CP on the other) → **imaginary part S^I₁₂(ω)** (causal
  correlations / signal propagation)
- Entanglement enhances signal but is NOT necessary (separable state → only 2× smaller signal)
- The two-qubit coherence ρ_{σ₁σ₂, −σ₁−σ₂} carries the cross-correlation information

## Key equations [paper]

### Hamiltonian — Eq. (1)
Ĥ = Σ_{α=1,2} (Ω_α + ξ_α(t)) σ̂_z^{(α)} / 2
Pure dephasing with classical noise ξ_α(t). The noise correlation matrix:
C_{αβ}(t) = ⟨ξ_α(t) ξ_β(0)⟩, spectrum S_{αβ}(ω) = ∫ e^{iωt} C_{αβ}(t) dt.

### Cross-correlation spectrum — Eq. (2)
S_{αβ}(ω) = S^R_{αβ}(ω) + i S^I_{αβ}(ω), where:
- S^R₁₂(ω): even in ω, quantifies **common noise** — weighted sum of source spectra
- S^I₁₂(ω): odd in ω, quantifies **causal correlations** / signal propagation delays

### Two-qubit coherence decay — Eq. (5)
ρ_{σ₁σ₂, −σ₁−σ₂}(T) ∝ exp(−χ₁₁ − χ₂₂ − 2σ₁σ₂ χ₁₂)
where χ_{αα} = single-qubit self-dephasing, χ₁₂ = cross-dephasing term.

### Cross-dephasing spectroscopy — Eq. (11)-(12)
χ₁₂ = (1/2) ∫ S₁₂(ω) f̃₁(−ω) f̃₂(ω) dω/(2π)
Same sequence (f₁=f₂): χ₁₂ ≈ (4T/π²) S^R₁₂((n+1)π/T) → reconstructs real part.
Different sequences (PDD + CP): reconstructs imaginary part via phase-sensitive filtering.

## Relevance to project [ours]
**This is the direct observable for r = g₁/g₀.** Our coupling ratio r determines the noise
cross-correlation: when both qubits feel the same bath with couplings g₁, g₂, then
ξ₁(t) = g₁ ξ₀(t), ξ₂(t) = g₂ ξ₀(t), and:
- S₁₁(ω) = g₁² S₀(ω), S₂₂(ω) = g₂² S₀(ω)
- **S₁₂(ω) = g₁g₂ S₀(ω)** = **r g₀² S₀(ω)** (at r = g₁/g₀)
- **S^R₁₂(ω)/√(S₁₁ S₂₂) = 1** for fully common noise (r=1)
- **S^R₁₂(ω) = 0** for independent noise (r=0)

The two-qubit coherence decay directly encodes r:
- **χ₁₂ ∝ g₁g₂ = r × g₀²** → the cross-dephasing rate IS the r observable
- At r=1: χ₁₂ = χ₁₁ = χ₂₂ (fully correlated, DFS for {|01⟩,|10⟩})
- At r<0: χ₁₂ < 0 → **cross-dephasing REVERSES sign** → enhanced decoherence of the
  {|01⟩,|10⟩} subspace!

**This connects directly to K:** the two-qubit coherence measured in DDENS is the same
physical quantity that the K protocol probes (multi-time coherence of the data-qubit pair).
The DDENS protocol is essentially a controlled version of what our joint-parity extraction
does passively.

## Mapping to our setting
| DDENS concept | Our K-survival setting |
|---|---|
| Two qubits, DD pulses | Two data qubits, joint-parity extraction rounds |
| Two-qubit coherence ρ_{σ₁σ₂,−σ₁−σ₂} | K = Kolmogorov violation on syndrome records |
| χ₁₂ ∝ g₁g₂ = r × g₀² | K(r) ∝ |1−r| (distance from DFS point) |
| S₁₂(ω) = g₁g₂ S₀(ω) | coupling correlation = r × single-qubit strength |
| r=1: χ₁₂ = χ₁₁ = χ₂₂ → DFS | r=1: K ∼ 0 (dark mode) |
| r<0: χ₁₂ < 0 → enhanced decoherence | r<0: K maximal (bright mode) |

## Limitations [paper]
- Classical noise model (Gaussian); quantum bath requires generalization
- DD pulses are active control; our syndrome extraction is passive measurement
- Single-frequency spectroscopy; our K protocol integrates over all ω

## Tags
- `[paper]` two-qubit DDENS: direct measurement of noise cross-correlation S₁₂(ω)
- `[paper]` χ₁₂ ∝ g₁g₂ = the r-dependent cross-dephasing rate
- `[paper]` r<0 ⇒ χ₁₂ < 0 ⇒ sign reversal enhances decoherence of {|01⟩,|10⟩}
- `[ours]` DDENS protocol = controlled version of what joint-parity does passively
- `[ours]` K(r) ∼ |χ₁₂(r)| = strength of cross-dephasing on the measurement subspace
