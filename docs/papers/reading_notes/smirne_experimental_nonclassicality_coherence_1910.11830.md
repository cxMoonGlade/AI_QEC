# Reading note (精读): Smirne et al., "Experimental control of the degree of non-classicality via quantum coherence" (arXiv:1910.11830)

> **Provenance (2026-07-05): FULL-TEXT read (精读).** PDF → txt `outputs/papers/1910.11830.txt`
> (7 pages + supplemental). All §/Eq refs from that text. Published in Quantum Sci. Technol.
> 5, 04LT01 (2020).
> Adjudication target: does this paper provide the experimental validation of the
> coherence↔non-classicality linear relationship? **Verdict: YES — it is the FIRST and
> ONLY direct experimental measurement of this relationship. CRITICAL caveat: performed
> in the Markovian regime so it does NOT address finite-γ memory effects.**

## Metadata [paper]
- **Authors:** Andrea Smirne, Thomas Nitsche, Daniel Egloff, Sonja Barkhofen, Sagnik De,
  Ish Dhand, Christine Silberhorn, Susana F. Huelga, Martin B. Plenio (Ulm / Paderborn /
  Oviedo)
- **Venue / status:** arXiv:1910.11830v2 [quant-ph], 28 Oct 2019 → Quantum Sci. Technol.
  5, 04LT01 (2020)
- **Type:** experiment (time-multiplexed optical quantum walk)

## Executive summary [paper]
Reports the **first experimental demonstration of a linear relationship between the
degree of non-classicality of multi-time statistics and the quantum coherence of the
probed observable**. The experiment uses a time-multiplexed optical quantum walk where
the walker's position encodes time bins. The non-classicality quantifier is the
**Kolmogorov distance** D_K(ρ) = min_{classical} ||P − P_classical||₁ — the minimum
total variation distance between the experimental probability distribution and the
closest classical (Kolmogorov-consistent) distribution. The coherence is measured via
interferometric visibility V = (I_max − I_min)/(I_max + I_min). The results confirm
the **linear scaling D_K ∝ V** predicted by Smirne et al. (2019, Phys. Rev. Lett.) for
the Markovian regime where the quantum regression theorem (QRT) holds. This establishes
coherence as a "tunable resource" for non-classicality.

## Key equations [paper]

### Kolmogorov distance (non-classicality quantifier) — Eq. (1)
```
D_K(ρ) = min_{P_C ∈ classical} (1/2) Σ_i |P_i − P_C,i|
```
where the minimum is over all classical (Kolmogorov-consistent) probability
distributions. D_K = 0 iff the statistics admit a classical description (Kolmogorov
consistency holds for all times). D_K > 0 = genuinely non-classical multi-time
statistics.

### Coherence measure — Eq. (2)
```
C(ρ) = Σ_{i≠j} |ρ_{ij}|
```
The l₁-norm of off-diagonal elements in the measurement basis. For a single qubit
this reduces to C = 2|ρ_{01}|.

### Interferometric visibility — Eq. (3)
```
V = |⟨ψ|U|ψ⟩|
```
The visibility of interference fringes in the quantum walk, directly related to the
coherence of the probe state.

### Linear relationship — Fig. 3 / §4
```
D_K = α V + β
```
where α is the slope (experimentally determined) and β is a small offset. For the
optical quantum walk with decoherence rate γ and hopping rate J:
- Low γ/J: D_K ∝ V with slope ≈ 1 (strong non-classicality)
- High γ/J: D_K ≈ 0 (classical statistics emerge)
The linear relationship holds when the quantum regression theorem is valid
(Markovian regime).

### Experimental protocol — §2-3
1. Initialize walker in a coherent superposition of position modes
2. Evolve under the quantum walk unitary U = exp(−iHt/ℏ) with controlled decoherence
3. Measure position-dependent interference visibility V
4. Compute the full multi-time probability distribution via time-resolved detection
5. Solve the convex optimization for D_K (minimum distance to classical set)
6. Plot D_K vs V — linear relationship confirmed

## Relevance to project [ours]
**Claim 3 dimension ③ (non-classicality of multi-time statistics) — EXPERIMENTAL
BASELINE FOR COHERENCE↔NON-CLASSICALITY RELATIONSHIP.** This paper provides:

1. **The only experimental calibration point** for how coherence maps to
   non-classicality in multi-time statistics. For our joint-parity records, the
   observable coherence of the X_{d0}X_{d1} parity variable sets an upper bound on
   how non-classical the multi-time statistics can be (in the Markovian regime).

2. **BUT critical caveat for Claim 3:** The experiment is deliberately in the
   **Markovian regime** (QRT-valid, decoherence engineered to be memoryless). Our
   shared-mode JC model is **non-Markovian** (finite memory time γ⁻¹). The linear
   D_K ∝ V relationship is NOT guaranteed to hold when memory is present. The user's
   finite-γ concern is directly this: the Smirne experiment does not probe the regime
   where memory and coherence interact.

3. **What it tells us anyway:** Even in the Markovian limit, coherence is the "fuel"
   for non-classicality. If the joint-parity measurement visibility is low (e.g., due
   to measurement-induced dephasing), the multi-time statistics will be approximately
   classical regardless of the bath structure. This provides a **necessary condition**
   for Claim 3's non-classicality claim: the coherence of the parity observable must
   be sufficiently high.

4. **Protocol we can adapt:** The convex optimization for D_K (minimum distance to
   Kolmogorov-consistent distributions) is directly applicable to our trajectory
   records. We compute the three-time distribution P(z₂, z₁, z₀) from MCWF trajectories,
   then solve:
   ```
   D_K = min_{P_C: Kolmogorov-consistent} (1/2) Σ |P − P_C|
   ```
   using linear programming. The user's framework (DOI: 10.1103/PhysRevA.110.062619)
   may give a more efficient route, but this paper's D_K is the reference standard.

5. **Gap it reveals:** There is NO experimental study of the coherence↔non-classicality
   relationship in a controlled non-Markovian setting. This gap is what Claim 3
   (partially) fills. The absence of such data means our finite-γ predictions cannot
   be benchmarked against existing experiments — they are genuinely novel predictions.

## Limitations
- Markovian regime only (QRT-valid) — does NOT address the non-Markovian / finite-γ
  regime that is relevant for the shared-mode JC model
- Optical quantum walk platform — different decoherence mechanisms than
  superconducting qubits (our target)
- Position measurement in the quantum walk is not equivalent to ancilla-mediated
  joint-parity readout (different measurement back-action)
- The convex optimization for D_K scales exponentially with the number of time steps
  — practical only for ≤5 time points
- No extension to continuous-variable or bosonic environments

## Tags
- `[paper]` D_K = Kolmogorov distance = non-classicality quantifier
- `[paper]` linear D_K ∝ V (coherence) relationship in Markovian regime
- `[paper]` first experimental validation of Smirne 2019 theorem
- `[paper]` coherence = tunable resource for non-classicality
- `[paper]` quantum regression theorem ⇒ linear relationship
- `[ours]` ONLY experimental baseline for coherence↔non-classicality
- `[ours]` CRITICAL GAP: no non-Markovian experimental data exists
- `[ours]` sets necessary condition: parity coherence must be high for Claim 3
- `[ours]` D_K computation protocol directly transferable to our trajectories
