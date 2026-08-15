# Reading note (精读): Bäcker, Beyer, Strunz, "Local Disclosure of Quantum Memory in Non-Markovian Dynamics" (arXiv:2310.01205)

> **Provenance (2026-07-05): FULL-TEXT read (精读).** HTML → txt `outputs/papers/2310.01205.txt`
> (6 pages, Phys. Rev. Lett. 132, 230401, 2024). All §/Eq refs from that text.
> Adjudication target: does this paper give us a COMPUTABLE criterion for deciding
> whether the finite-γ memory in the shared-mode σ− relaxation is genuinely quantum
> or classically expressible? **Verdict: YES — Theorem 1 (quantum memory criterion
> via entanglement of assistance) is directly computable from Choi states of the
> reduced dynamics, and the zero-T vs finite-T results bound the user's γ=0.15
> operating point.**

## Metadata [paper]

- **Authors:** Bäcker, Beyer, Strunz (TU Dresden, Institut fur Theoretische Physik)
- **Venue / status:** arXiv:2310.01205v2 [quant-ph], 5 Mar 2024 → Phys. Rev. Lett. 132, 230401 (2024)
- **Type:** theory (criterion + examples)

## Executive summary [paper]

Establishes a necessary and sufficient condition for quantum memory in open quantum
dynamics using **entanglement of assistance** (E♯). For two-time dynamics D = (ℰ₁, ℰ₂)
with Choi states χ₁, χ₂: if E♯[χ₁] < E[χ₂] then quantum memory is required — the
channel ℰ₂ cannot extract more entanglement from the Choi state than ℰ₁ could have
provided via an optimal measurement, unless genuine quantum memory is present.
**Key physical result:** zero-temperature amplitude damping REQUIRES quantum memory
in any non-Markovian regime (concurrence of assistance equals concurrence at all
times, and concurrence is non-monotonous). Finite-temperature amplitude damping
(β=0.51) can admit a classical memory realization when the damping parameter p₂≥0.86.
**Operational advantage:** only single-time channel tomography is needed — no multi-time
statistics, no process tensor reconstruction. The criterion is sufficient but NOT
necessary (inconclusive region exists).

### Definitions

- **Classical memory (Def. 1):** ℰ₂[ρ] = Σᵢ Φᵢ[Mᵢ ρ Mᵢ†] where {Mᵢ} is a Kraus
  decomposition of ℰ₁ and Φᵢ are CPT maps. Physical meaning: a measurement maps the
  pre-measurement state to a classical index i, the environment stores only that
  classical label, and the subsequent evolution depends only on i.
- **Choi state:** χ[ℰ] = (ℰ⊗𝟙)|ϕ⁺⟩⟨ϕ⁺| with |ϕ⁺⟩ = (1/√d) Σⱼ|j_S⟩|j_A⟩. The Choi
  state encodes the full channel information in an entangled state on system × ancilla.
- **Entanglement of assistance (E♯):** E♯[ρ_AB] = max_{p_k, |ψ_k⟩} Σ_k p_k E[|ψ_k⟩⟨ψ_k|],
  the maximum average entanglement that can be distilled by one party measuring its
  subsystem and communicating the outcome. E is an entanglement monotone (e.g.,
  concurrence, negativity).

## Key equations/findings [paper]

### Quantum memory criterion — Theorem 1

For two-time dynamics D = (ℰ₁, ℰ₂) with Choi states χ₁, χ₂:

```
E♯[χ₁] < E[χ₂]  ⇒  quantum memory IS required
```

Intuition: ℰ₁ is probed by a maximally entangled input. Optimal measurement on
the ancilla "disentangles" system and environment, yielding at most E♯[χ₁]
entanglement. If this is less than the entanglement extracted from ℰ₂, the
environment must have stored quantum (not classical) information between rounds.

### Concurrence of assistance equals concurrence for zero-T AD

For zero-temperature amplitude damping, the Choi state satisfies:

```
C♯[χ(t)] = C[χ(t)]  ∀t
```

where C♯ is concurrence of assistance, C is concurrence. This equality holds for
any single-qubit amplitude damping channel. Proof: the Choi state is rank-2, and
for rank-2 states C♯ = C identically (no optimization needed).

**Physical implication:** Since C[χ(t)] is non-monotonous in the non-Markovian
regime (the memory bump), there ALWAYS exist times t₂ > t₁ such that:

```
C♯[χ(t₁)] < C[χ(t₂)]  ⇒  quantum memory REQUIRED
```

Therefore: "Zero-temperature non-Markovian amplitude damping cannot be realized by
means of classical memory."

### Finite-temperature AD admits classical regime

At finite temperature β=0.51 (excitation probability of the thermal environment),
with initial damping parameter p₁=0.9:

- **p₂ < 0.11:** quantum memory detected (criterion fires)
- **0.11 ≤ p₂ < 0.86:** INCONCLUSIVE (white region — criterion does not fire but
  quantum memory is not ruled out either)
- **p₂ ≥ 0.86:** CLASSICAL MEMORY SUFFICIENT — explicit construction given

The explicit classical memory construction for p₂ ≥ 0.86:

1. Measure ℰ₁ in the basis {M_α, M_β, M_γ, M_δ} (four-outcome POVM)
2. Apply outcome-dependent Pauli rotations {R_α, R_β, R_γ, R_δ}
3. Apply the fixed recovery channel ℰ₀ (independent of outcome)

This demonstrates a finite-temperature threshold above which thermal noise masks
the quantum nature of the memory — the dynamics is effectively classical even
though the underlying physical process involves a quantum environment.

### Sufficient but not necessary

The criterion provides a sufficient condition only. There is a "white region"
(inconclusive) where no statement about the classicality of the memory can be
made. This is expected: classical memory is a restrictive condition, and
distinguishing it from the full quantum hierarchy is provably hard.

## Relevance to project [ours]

**Claim 3 — "is the finite-γ memory in shared-mode σ− relaxation classically
expressible?"** This paper is central to adjudicating that claim. Here is why:

1. **Zero-T AD is the limiting case:** The user's shared-mode JC σ− relaxation
   with vacuum-initialized mode is approximately zero-temperature amplitude
   damping for the data qubits. In this limit, the paper's zero-T AD result says
   quantum memory is REQUIRED — period. No classical memory suffices.

2. **BUT: finite γ introduces effective temperature:** The mode decay √γ a
   creates an effective thermal bath. At the user's physical γ=0.15, the mode
   is NOT a perfect zero-T environment. The finite-temperature AD results (with
   β=0.51, p₁=0.9) show that above a threshold (p₂≥0.86), classical memory DOES
   suffice. This suggests the user's conjecture "classical may be sufficient"
   could be correct at the γ=0.15 operating point, even though the ideal
   zero-T limit requires quantum memory.

3. **COMPUTABLE PROTOCOL:** The user can directly compute E♯[χ₁] < E[χ₂] from
   the JC reduced dynamics:

   (a) Extract the two-time process tensor channels ℰ₁, ℰ₂ from the JC
       Master Equation or Monte Carlo simulation
   (b) Construct Choi states χ₁ = (ℰ₁⊗𝟙)|ϕ⁺⟩⟨ϕ⁺|, χ₂ = (ℰ₂⊗𝟙)|ϕ⁺⟩⟨ϕ⁺|
   (c) Compute concurrence C[χ₂] and concurrence of assistance C♯[χ₁]
       (for single-qubit channels, C♯[χ₁] = C[χ₁] for rank-2 Choi states)
   (d) If C[χ₁] < C[χ₂] → quantum memory REQUIRED → Claim 3 is FALSE for
       the ground truth
   (e) If C[χ₁] ≥ C[χ₂] → inconclusive — test at multiple time pairs

4. **Threshold mapping:** The critical question is: at γ=0.15, what is the
   effective temperature of the mode? If it maps to β < β_critical (where
   the finite-T AD admits classical simulation), then Claim 3 stands. If
   the mode is effectively zero-T, Claim 3 falls.

5. **Operational economy:** Only single-time channel tomography is needed.
   No process tensor reconstruction, no multi-time Monte Carlo sampling for
   the criterion itself. This makes the test cheap to compute from the
   user's existing JC simulation infrastructure.

## Limitations

- **Sufficient but not necessary:** the white region (inconclusive) means
  failing the criterion does NOT prove classical memory — it only says the
  test is inconclusive. Additional witnesses (e.g., the entropic witness from
  Bäcker 2501.17660) may be needed.
- **Single-qubit focus:** explicit examples are qubit amplitude damping.
  Extension to the 2-qubit shared-mode case (data qubits + bosonic mode)
  requires generalizing the Choi-state argument. The criterion itself is
  dimension-agnostic, but the C♯=C simplification for rank-2 states may
  not hold for d > 2.
- **Continuous-variable bath:** The bosonic mode is a continuous-variable
  system; the two-time channel on qubits is well-defined (trace out the mode),
  but the Choi-state construction requires a finite-dimensional ancilla
  isomorphic to the system.
- **Finite-T results specific to β=0.51:** The paper reports only one
  temperature. A full β-γ phase diagram for the user's model would require
  generalization.
- **Only two-time dynamics:** The criterion covers D = (ℰ₁, ℰ₂). Extending
  to the full (ℰ₁, ..., ℰ_n) multi-round QEC cycle requires sequential
  application or a process-tensor generalization.

## Tags

- `[paper]` Theorem 1: E♯[χ₁] < E[χ₂] ⇒ quantum memory required
- `[paper]` zero-T AD: quantum memory REQUIRED (C♯=C, non-monotonous concurrence)
- `[paper]` finite-T AD (β=0.51): classical memory suffices for p₂ ≥ 0.86
- `[paper]` classical memory definition: ℰ₂[ρ] = Σᵢ Φᵢ[Mᵢ ρ Mᵢ†]
- `[paper]` sufficient but not necessary criterion (inconclusive white region)
- `[ours]` central adjudicator for Claim 3 (quantum vs classical memory)
- `[ours]` γ=0.15 operating point may be in finite-T regime where classical memory suffices
- `[ours]` C♯[χ₁] vs C[χ₂] directly computable from JC reduced dynamics
