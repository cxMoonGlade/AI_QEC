# Reading note (精读): Fanchini et al., "Probing the degree of non-Markovianity for independent and common environments" (arXiv:1301.3146)

> **Provenance (2026-07-05): FULL-TEXT read (精读).** PDF → txt `outputs/papers/1301.3146.txt`
> (10 pages + references). All §/Eq refs from that text. Published in Phys. Rev. A 88,
> 012105 (2013).
> Adjudication target: does this paper provide the quantitative framework for comparing
> independent-environment vs common-environment non-Markovianity? **Verdict: YES — it is
> the definitive systematic comparison of BLP and LFS measures across both scenarios,
> and directly grounds the Claim 3 Control 2 argument.**

## Metadata [paper]
- **Authors:** Felipe F. Fanchini, Baris Karpat, Leandro H. Castelano, Daniel Z. Rossatto
  (UNESP / São Carlos / UFSCar, Brazil)
- **Venue / status:** arXiv:1301.3146v2 [quant-ph], 14 Jan 2013 → Phys. Rev. A 88,
  012105 (2013)
- **Type:** theory (quantitative comparison of NM measures)

## Executive summary [paper]
Performs a **systematic comparison of two leading non-Markovianity measures** — the
BLP trace-distance measure (Breuer, Laine, Piilo, 2009) and the LFS mutual-information
measure (Luo, Fu, Song, 2012) — across two paradigmatic scenarios: **independent
environments** (each qubit coupled to its own reservoir) and **common (collective)
environment** (multiple qubits sharing a single reservoir). The key finding: for
independent environments, the degree of non-Markovianity **increases monotonically
with the number of qubits** for both measures. For common environments, the behavior
is qualitatively different — non-Markovianity can **increase or decrease** depending
on the specific process and the measure used, revealing that collective dissipation
fundamentally alters the NM structure. Importantly, **BLP and LFS do not always agree**,
particularly for collective dissipation, meaning the choice of NM measure is
consequential for characterizing shared-bath effects.

## Key equations [paper]

### BLP measure — Eq. (1)
```
N_BLP(Φ) = max_{ρ₁,ρ₂} ∫_{σ>0} dt σ(t, ρ₁,ρ₂)
```
where σ(t) = (d/dt)D(ρ₁(t), ρ₂(t)) is the time derivative of the trace distance
D(ρ₁, ρ₂) = (1/2) Tr|ρ₁ − ρ₂|. Integration is over time intervals where σ > 0
(information backflow = non-Markovianity). Maximization is over initial state pairs.

### LFS measure — Eq. (2)
```
N_LFS(Φ) = ∫_0^∞ dt |dI(ρ_{SE}(t))/dt|
```
where I(ρ_{SE}) = S(ρ_S) + S(ρ_E) − S(ρ_{SE}) is the mutual information between
system and environment. LFS quantifies the total variation of s-e correlations.
(BLP measures distinguishability of system states; LFS measures s-e information flow.)

### Independent environments — §3, Figs. 1-2
For N qubits each coupled to its own zero-temperature bosonic reservoir (independent
AD channels with Lorentzian spectrum γ(ω) ∝ 1/[(ω − ω₀)² + λ²]):
```
N_BLP(N) ∝ N   (linear increase)
N_LFS(N) ∝ N   (linear increase)
```
**Non-Markovianity scales approximately linearly with qubit number** for independent
reservoirs. This is the baseline that any common-environment model must deviate from.

### Common environment — §4, Figs. 3-4
For N qubits coupled to a SINGLE shared bosonic reservoir (collective dissipation
with Dicke-type coupling Σ_i g_i (σ₊ⁱ + σ₋ⁱ) ⊗ (a + a†)):
- **BLP measure:** N_NM can INCREASE or DECREASE with N depending on the specific
  process (non-monotonic). For certain initial states, adding more qubits REDUCES
  the trace-distance revivals.
- **LFS measure:** Shows **super-additivity** — the total s-e information flow
  exceeds the sum of individual-qubit contributions due to collective correlations.
- **Measure disagreement:** For collective dissipation, BLP and LFS can give
  OPPOSITE trends as N increases. LFS is more sensitive to collective effects.

### Optimal initial states — §5, Figs. 5-6
For BLP maximization:
- **Independent environments:** Optimal states are typically **entangled** (Bell states
  or GHZ-type for N > 2).
- **Common environment:** Optimal states are **NOT maximally entangled** — rank-2 or
  rank-4 states with small deviations from uniform weights produce the largest BLP.
  Maximally entangled states can be SUB-OPTIMAL due to the collective dissipation
  symmetry (dark states are protected from decoherence, reducing the revival signal).

### Key parameters — §2
Lorentzian spectral density (common to both models):
```
J(ω) = (γ₀ λ²) / (2π [(ω − ω₀)² + λ²])
```
where γ₀ = coupling strength, λ = spectral width (inverse correlation time).
λ/γ₀ ≪ 1 ⇒ Markovian limit; λ/γ₀ ≫ 1 ⇒ non-Markovian.

## Relevance to project [ours]
**Claim 3 dimension ② (collectiveness) — DIRECT QUANTITATIVE GROUNDING FOR CONTROL 2.**
This paper provides the framework that proves the null model (independent AD per qubit)
CANNOT reproduce collective-bath signatures:

1. **Scaling test (our Control 2):** The paper establishes that for independent
   environments, N_BLP(N) ∝ N (approximately linear). For the common (shared-mode JC)
   environment, N_BLP(N) is NON-MONOTONIC. Therefore:
   - **Null model prediction:** As we increase from 2 qubits to 3 or 4, the
     degree of non-Markovianity (measured via BLP or LFS) increases linearly.
   - **Shared-mode prediction:** The scaling is non-monotonic; collective dissipation
     suppresses certain revivals due to subradiant / dark state effects.
   - **Control 2 test:** Measure N_BLP(2), N_BLP(3), N_BLP(4) from MCWF trajectories
     for the shared-mode JC model. If scaling is linear → null model cannot be
     ruled out. If non-monotonic → collective dissipation is confirmed.

2. **BLP vs LFS disagreement as a diagnostic:** The paper shows BLP and LFS disagree
   specifically for collective dissipation. For independent environments, they agree.
   Therefore, **disagreement between BLP and LFS is itself a signature of collective
   effects**. We can compute both measures from our trajectories and check:
   - Do they give the same trend with N? If yes → consistent with independent envs.
   - Do they disagree? If yes → collective dissipation signature confirmed.

3. **Optimal state result — practical consequence:** The paper finds that maximally
   entangled states are sub-optimal for detecting NM in common environments. Our
   default initial state (|00⟩ or |++⟩ for the two data qubits) may NOT be optimal
   for maximizing BLP. We should explore rank-2 initial states (e.g., mixtures of
   |00⟩ and |11⟩ with non-uniform weights) to maximize the BLP signal for our
   shared-mode system.

4. **LFS super-additivity test:** The paper's LFS super-additivity result for common
   environments provides a quantitative prediction:
   ```
   N_LFS(common, N) > Σ_i N_LFS(independent_i)
   ```
   We can compute the LFS for each qubit individually (by tracing out the other)
   and compare to the joint LFS. If joint > sum → collective correlations confirmed.

5. **Direct citation for null model impossibility:** The paper's central result —
   that independent and common environments produce qualitatively different NM scaling
   with N — is the rigorous basis for our Control 2 claim that independent AD (per
   qubit) cannot reproduce shared-mode signatures regardless of parameter tuning.

## Limitations
- BLP and LFS computed from the exact master equation (analytic), not from trajectory
  samples — our MCWF estimates will have finite-sampling noise that may obscure
  subtle BLP revivals
- Both measures require optimization over initial states — our computational budget
  may limit exhaustive search
- Lorentzian spectrum only — does not cover 1/f noise or structured environments
  that may appear in real superconducting hardware
- Zero-temperature reservoirs only — no finite-temperature extension (relevant for
  Google hardware at 15-20 mK where thermal photons are negligible but not zero)
- Two-qubit and three-qubit examples only — scaling to larger N is extrapolated
  rather than computed

## Tags
- `[paper]` BLP trace-distance measure: N_BLP ∝ N for independent envs
- `[paper]` LFS mutual-information measure: N_LFS ∝ N for independent envs
- `[paper]` common environment: BLP scaling NON-MONOTONIC (can decrease with N)
- `[paper]` common environment: LFS shows super-additivity
- `[paper]` BLP and LFS DISAGREE for collective dissipation (diagnostic!)
- `[paper]` optimal BLP states for common env are rank-2 or rank-4 (not maximally entangled)
- `[ours]` DIRECTLY GROUNDS Control 2: null model impossibility theorem
- `[ours]` scaling test N_BLP(N) as Control 2 experimental signature
- `[ours]` BLP vs LFS disagreement = collective dissipation diagnostic
- `[ours]` practical guidance: avoid maximally entangled initial states for BLP max
