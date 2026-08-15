# Reading note (精读): Luppi, Fernández-Acebal, Huelga, Smirne, "Multitime memory beyond the quantum regression theorem in sequential measurement statistics" (arXiv:2605.06427)

> **Provenance (2026-07-05): FULL-TEXT read (精读).** arxiv HTML → txt `outputs/papers/2605.06427.txt`
> (24 pages, 6 figures). All §/Eq refs from that text.
> Adjudication target: does this paper provide the exact decomposition that maps the QRT-like
> term and the memory term onto our TV residual and incoherent null model? **Verdict: YES —
> Φ^{A1(P)} and Φ^{A1(Q)} are the direct formal analogues of our null-model fit and residual,
> respectively. The second-order weak-coupling correction gives the explicit connection to
> finite-γ bath correlations.**

## Metadata [paper]
- **Author:** Luppi, Fernández-Acebal, Huelga, Smirne (Universidad Autónoma de Madrid / INL, Braga)
- **Venue / status:** arXiv:2605.06427v2 [quant-ph], 18 Jun 2026 (revised)
- **Type:** theory (exact decomposition + perturbative expansion + numerical demonstration)

## Executive summary [paper]

Establishes the **exact decomposition of the two-time quantum propagator** into a QRT-like
part (fully determined by the reduced dynamical map) and a memory part that encodes all
system-environment correlations across the intermediate intervention. The central object is
the two-time sequential measurement probability p(a₂,t₂; a₁,t₁) = Tr[ P_{a₂} Λ_{t₂,t₁}[ P_{a₁}
Λ_{t₁}[ρ(0)] ] ], which the quantum regression theorem (QRT) would evaluate using only the
reduced map: p_QRT(a₂,t₂; a₁,t₁) = Tr[ P_{a₂} Λ_S(t₂−t₁)[ P_{a₁} Λ_S(t₁)[ρ(0)] ] ]. The
difference defines the memory correction.

The decomposition uses the projection superoperator formalism: P is the projector onto
the relevant (system) subspace, Q = I − P is the complement. At each intervention time,
the environment carries correlations built up during the preceding evolution. The QRT-like
term discards these correlations; the memory term propagates them through the second
interval. This provides an exact, process-agnostic separation — no assumption about
weak coupling, Markovianity, or specific system-environment model is required for the
decomposition itself.

A key finding is that **reduced-state non-Markovianity and multitime memory are inequivalent**:
the authors demonstrate parameter regimes where P-divisibility is maximally violated but
multitime QRT violation is near zero, and vice versa (Fig. 2). This is critical for the twin
project because it means our TV residual (which measures multitime memory) and standard
non-Markovianity witnesses (which measure reduced-state divisibility) are probing different
physics. The second-order weak-coupling correction (Eq. 37-38) expresses the memory kernel
directly in terms of the reduced map and the bath correlation function — giving the explicit
bridge to finite-γ corrections in the JC model.

## Key equations/findings [paper]

### Exact two-time propagator decomposition — Eq. (22)
```
Λ^{A1}(t₂,t₁) = Λ^{A1(P)}(t₂,t₁) + Λ^{A1(Q)}(t₂,t₁)
```
The two-time sequential-measurement propagator splits into a QRT-like part (P-projected)
and a memory part (Q-projected). This is operational: no approximation, no assumption about
the environment.

### QRT-like term — Eq. (24)
```
Λ^{A1(P)}[ρ] = Λ_S(t₂−t₁) ∘ A₁ ∘ Λ_S(t₁)[ρ]
```
where A₁ = P_{a₁} is the first measurement effect. This is fully determined by the reduced
dynamical map Λ_S(t) = Tr_B[ e^{tL} [· ⊗ R] ]. It reproduces the standard QRT prescription:
the first measurement conditions the system state, evolve forward, the second measurement
conditions again.

### Memory term — Eq. (25)
```
Λ^{A1(Q)}[ρ] = Tr_B[ e^{(t₂−t₁)L} ∘ (A₁ ⊗ I_B) ∘ Q ∘ e^{t₁L}[ρ ⊗ R] ]
```
The memory term propagates the **environmental correlations** that survive the first
measurement (those in the Q-subspace). These correlations are established during [0,t₁],
are not erased by the measurement A₁, and bias the subsequent evolution [t₁,t₂]. This IS
the formal expression for what our TV residual captures.

### Operational QRT-violation quantifier — Eq. (28)
```
ε_QRT(t₂,t₁) = ½ Σ_{a₁,a₂} | p(a₂,t₂; a₁,t₁) − p_QRT(a₂,t₂; a₁,t₁) |
```
The Kolmogorov distance between the exact and QRT-approximated two-time distributions.
This is the direct operational analogue of our TV distance: we compute the exact
distribution (from the JC simulation) and the QRT/null-model distribution (from the
incoherent reduced map), and the TV distance between them IS ε_QRT.

### Second-order weak-coupling correction — Eq. (37-38)
```
Λ^{A1(Q)}[ρ] ≈ ∫₀^{t₁} dτ ∫ dω J(ω) [ ... correlation terms ... ]
```
At second order in system-bath coupling, the memory kernel factorizes into the reduced
map and the bath correlation function C(τ) = Tr_B[ B(τ) B(0) R ]. This is the explicit
bridge to our finite-γ decomposition: **the bath correlation function C(τ) ≈ e^{−γτ}**
(for the Lorentzian spectral density we use), and the memory correction scales with γ/T₁.
This is the analytical basis for the Claim 3 prediction that TV ∝ (γ/T₁) · (coherence).

### Three-time QRT violations — Fig. 6
Three-time QRT violations can appear even when two-time statistics are QRT-compatible.
This means the two-time residual (our ε_QRT) is a necessary but not sufficient condition
for memory. Higher-order coherence can be hidden in the three-time marginals.

## Relevance to project [ours]

**This paper provides the EXACT formal decomposition that maps onto the Claim 3 TV-residual
problem.** The mapping is direct:

1. **QRT-like term → incoherent null model (best fit):** The null model predicts two-time
   statistics using only the reduced dynamical map Λ_S(t) — exactly the same CPTP channel
   our learner recovers from incoherent assumptions. The QRT-like term Λ^{A1(P)} is the
   projective-measurement analogue of our null-model prediction.

2. **Memory term → TV residual (the quantity being decomposed):** The memory term
   Λ^{A1(Q)} captures exactly what our TV residual measures: the difference between exact
   multitime statistics and the best incoherent QRT approximation. Our key Claim-3 question
   — "how much of the TV distance comes from coherent vs. collective vs. finite-γ effects?"
   — is algebraically the question of decomposing Λ^{A1(Q)} into its coherent (interference,
   off-diagonal in the measurement basis), collective (multi-qubit correlations), and
   finite-γ (bath memory, C(τ) decay rate) components.

3. **Second-order correction → finite-γ scaling prediction:** Eq. (37-38) directly expresses
   the memory correction in terms of C(τ). For our Lorentzian bath, C(τ) ∝ e^{−γτ}, and the
   resulting TV residual ∝ (γ/T₁) · ||coherence||. This is the analytical prediction that
   should appear in the Claim 3 decomposition.

4. **Inequivalence of P-divisibility and multitime memory → our decomposition protocol must
   measure BOTH:** Figs. 2-4 show regimes where P-divisibility violation peaks where
   ε_QRT ≈ 0, and vice versa. Our decomposition must jointly report the reduced-state
   non-Markovianity (Trace distance / BLP measure) AND the multitime memory (TV distance)
   — they are not redundant.

## Limitations
- The decomposition assumes projective measurements; extension to generalized
  measurements / POVMs (our soft-readout / ancilla-mediated parity extraction) requires
  replacing P_{a₁} with the instrument map
- The second-order expansion assumes weak coupling — our finite-γ JC model at strong
  coupling (g/γ not small) needs higher-order or exact treatment
- Three-time violations mean the two-time TV residual undercounts total memory —
  higher-order statistics matter and we should check whether Claim 3 needs 3-time evidence
- No explicit multi-qubit generalization (the collective axis of Claim 3)

## Tags
- `[paper]` exact decomposition: Λ^{A1} = Λ^{A1(P)} + Λ^{A1(Q)} (QRT-like + memory)
- `[paper]` ε_QRT = Kolmogorov distance between exact and QRT two-time distributions
- `[paper]` P-divisibility ≠ multitime memory (inequivalent, Fig. 2)
- `[paper]` second-order weak coupling: memory kernel = reduced map × C(τ)
- `[ours]` Φ^{A1(P)} = our incoherent null model prediction
- `[ours]` Φ^{A1(Q)} = our TV residual (the quantity decomposed in Claim 3)
- `[ours]` second-order correction gives TV ∝ (γ/T₁) · coherence (analytical basis)
- `[ours]` must measure BOTH reduced non-Markovianity AND multitime memory
