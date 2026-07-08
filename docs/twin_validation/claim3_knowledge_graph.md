# Claim 3 Knowledge Graph — Multi-Time Non-Classicality Decomposition

> **Maintained 2026-07-05.** Maps the 15-paper literature spine to Claim 3's three
> confusion terms: ① coherence, ② collectiveness, ③ finite-γ memory.
> Cross-references: `docs/papers/reading_notes/README.md` (RAG index),
> `docs/twin_validation/` (working notes).

## Entity Map: Confusion Terms → Papers → Operational Criteria

### ① Coherence (genuinely quantum energy exchange, vacuum-Rabi revival structure)

```
smirne_coherence_nonclassicality_markov_1709.05267
  └─ Theorem 2: Markovian ⇒ (non-classicality ⇔ CGD)
  └─ CGD definition: Δ∘Λ(t)∘Δ∘Λ(τ)∘Δ ≠ Δ∘Λ(t+τ)∘Δ [Eq. 5]
  └─ LIMIT: equivalence BREAKS under non-Markovianity
  └─ Role in Claim 3: FOUNDATIONAL — explains σz (NCGD→classical) vs σ− (CGD→non-classical)

milz_when_nonmarkovian_process_classical_1907.05807
  └─ Non-Markovian: coherence NOT the sole driver → discord takes over
  └─ Genuinely quantum processes exist only in non-Markovian regime
  └─ Role in Claim 3: THEORETICAL WARNING — Claim 3's "coherence is core" premise
     is the Markovian answer applied to a non-Markovian system

smirne_experimental_nonclassicality_coherence_1910.11830
  └─ D_K ∝ C (linear, Markovian only)
  └─ Role in Claim 3: EXPERIMENTAL BASELINE — what coherence-driven
     non-classicality looks like when memory is absent
```

### ② Collectiveness (superradiant collective decay, shared-mode-mediated correlations)

```
fanchini_independent_common_nonmarkovianity_1301.3146
  └─ Collective NM is SUPER-ADDITIVE (cannot = sum of independent NM)
  └─ BLP and LFS measures can DISAGREE for collective dissipation
  └─ Optimal probe states differ: independent vs common bath
  └─ Role in Claim 3: GROUNDS CONTROL 2 — independent-AD null cannot
     capture collective signatures regardless of parameter tuning

wang_collective_dephasing_common_bath_1409.0172
  └─ Cross-term ∝ √(J₁J₂) in master equation = collective signature
  └─ Γ_common = Γ_indep + 8√(J₁J₂) [Eq. 14]
  └─ J_eff(r) = J₁·(1−|r|)² → K(r) ∝ (1−|r|)²
  └─ DFS at r=1 (J₁=J₂): single-excitation subspace decoupled
  └─ Role in Claim 3: ANALYTICAL TEMPLATE — adapts from σz dephasing
     to σ− amplitude damping cross-term structure

taranto_hierarchy_multitime_classical_memory_2307.11905
  └─ Collectiveness maps to Separable or Quantum Memory rung
  └─ N≥3 required to distinguish from Classical Memory
  └─ Role in Claim 3: HIERARCHY PLACEMENT — where ② sits in the
     formal memory-class taxonomy
```

### ③ Finite-γ Memory (residual non-Markovianity from finite mode decay rate)

```
luppi_multitime_beyond_QRT_2605.06427
  └─ Φ = Φ_QRT + Φ_memory [Eq. 22]: exact propagator decomposition
  └─ Φ_memory encodes s-e correlations across intervention
  └─ ε_QRT [Eq. 28]: operational quantifier of QRT violations
  └─ Reduced-state NM ≠ multitime memory (INEQUIVALENT)
  └─ Second-order correction: memory kernel ∝ bath correlation
     functions [Eqs. 37-38]
  └─ Role in Claim 3: FORMAL DECOMPOSITION — the QRT-like term
     = incoherent null; the memory term = TV residual

budini_dni_violation_hallmark_2301.02500
  └─ DNI: three-measurement protocol, I(t,τ) [Eq. 9] = K-analogue
  └─ Unitary s-e coupling ⇒ DNI violation
  └─ Role in Claim 3: OPERATIONAL PROTOCOL — I(t,τ) directly
     measures measurement invasiveness of finite-γ memory

budini_superclassical_dni_2411.13471
  └─ Superclassical class: non-Markovian but DNI-satisfying
  └─ Finite-γ memory CAN be classical (not all NM is quantum)
  └─ Role in Claim 3: NULL MODEL — finite-γ memory may be in
     superclassical class, meaning it's CLASSICAL despite NM appearance

bracht_factorization_multitime_correlations_2605.22386
  └─ n-time correlations factorize for Δt > τ_c
  └─ Temporal volume O(τ_c^n), not O(t^n)
  └─ Role in Claim 3: COMPUTATIONAL BOUND — if γ is large enough
     that τ_c ~ 1/γ < Δt_syndrome, then ③ contributes only at
     2-time level, not multiplicatively across rounds
```

### Synthesis & Decomposition Frameworks

```
gangwar_sen_genuine_nonmarkovianity_review_2603.28277
  └─ Three-tier classification: classical NM ⊊ non-genuine quantum ⊊ genuine quantum
  └─ Convex mixing ⇒ classical NM (no entanglement, zero discord)
  └─ Process-tensor temporal entanglement ⇒ genuine quantum NM
  └─ Role in Claim 3: CLASSIFICATION DECISION TREE for each confusion term

zonnios_bounded_coherent_memory_2606.19511
  └─ MAD framework: d_A parametrizes coherent memory dimension
  └─ d_A=1 = classical records only; d_A>1 = coherent memory
  └─ Single-step decomposition for recurrent SE processes
  └─ Role in Claim 3: OPERATIONAL LANGUAGE — TV distance =
     d^{(N)}_{MAD}(exact, null; d_A=1); residual = gap to true d_A

artag_complementary_quantum_classical_records_2605.15882
  └─ Environment stores BOTH quantum (concentrated, cat-state)
     AND classical (redundant, Darwinian) records
  └─ |σ_x| = |⟨ψ↑|ψ↓⟩|: exact coherence-branch-overlap identity
  └─ V² + D² = 1: visibility-distinguishability complementarity
  └─ Role in Claim 3: PHYSICAL INTUITION — the user's dual-axis
     (X+Z) measurement probes BOTH records; which one dominates
     depends on the measurement basis

giarmatzi_witnessing_quantum_memory_1811.03722
  └─ Quantum memory ⇔ temporal entanglement in process matrix
  └─ Classical memory ⇒ separable process matrix
  └─ Entanglement witnesses → quantum memory witnesses
  └─ Role in Claim 3: WITNESS CONSTRUCTION — if the JC shared-mode
     process tensor is temporally entangled, collectiveness is
     genuinely quantum

sakuldee_commutativity_classicality_multitime_2204.11698
  └─ Multi-time classicality ≠ simple commutation
  └─ Structural conditions on process-tensor objects
  └─ Role in Claim 3: FORMAL BOUNDARY — the commutation-based
     intuition (σz sector blindness) does not fully determine
     multi-time classicality
```

## Cross-Paper Citation Graph

```
Smirne 2019 ──extends──→ Milz 2020 ──extends──→ Sakuldee 2022
    │                       │
    │ (CGD theorem)         │ (discord takeover)
    │                       │
    ├──cites──→ Smirne 2020 (experimental)    Taranto 2024 (hierarchy)
    │                                       /
    └──cites──→ Budini 2023/2025 ──parallel──→ Giarmatzi 2021
                     │                              │
                     │ (DNI/superclassical)          │ (process-matrix witness)
                     │                              │
    ┌────────────────┴──────────────────────────────┘
    │
    ├──→ Gangwar & Sen 2026 (unified review)
    │       └─ covers: Fanchini 2013, Milz 2020, Budini, Giarmatzi,
    │                  process-tensor methods, BLP/LFS/RHP
    │
    ├──→ Luppi 2026 (QRT-memory decomposition)
    │       └─ independent of: Zonnios 2026 (MAD framework)
    │
    ├──→ Zonnios & Binder 2026 (bounded coherent memory)
    │       └─ parallel concern to: Bracht 2026 (factorization rule)
    │
    ├──→ Artag 2026 (complementary records)
    │       └─ different object: spin-boson decoherence, not JC shared-mode
    │
    └──→ Wang 2015 (collective dephasing) ──parallel──→ Fanchini 2013
            (common bath, dephasing)                  (independent vs common)
```

## Claim 3 Control Experiments → Paper Grounding

```
Control 1 (r=0, γ scan: γ=5 → γ=20,50)
  ├─ Theory: Luppi 2026 (Φ_memory → 0 as γ→∞)
  ├─ Classification: Gangwar 2026 (γ=∞ → Markovian → CGD regime)
  ├─ Warning: Milz 2020 (non-Markovian regime may leave discord residue)
  ├─ Prediction: min-TV → 0 ⇒ ③ confirmed; plateau ⇒ ① or residual discord
  └─ Protocol: Budini 2023 (DNI I(t,τ) measurement)

Control 2 (add collective AD √Γ(σ−₁+σ−₂) to incoherent null family)
  ├─ Theory: Wang 2015 (cross-term ∝ √(J₁J₂) = collective signature)
  ├─ Classification: Fanchini 2013 (super-additive NM for common bath)
  ├─ Witness: Giarmatzi 2021 (temporal entanglement → genuinely quantum)
  ├─ Prediction: residual eaten ⇒ ② confirmed; residue remains ⇒ beyond collectiveness
  └─ Protocol: Taranto 2024 (N≥3 time steps required)
```

## Classical vs Quantum Memory — The Narrower Question (2026-07-05 supplement)

Six additional papers addressing whether the finite-γ memory contribution (Φ_memory,
~84% of TV residual) is genuinely quantum or classically expressible.

### Entity Map: Memory Witnesses → Criteria

```
backer_local_disclosure_quantum_memory_2310.01205
  └─ Theorem 1: E♯[χ₁] < E[χ₂] ⇒ quantum memory REQUIRED
  └─ Zero-T AD: C♯=C ∀t, non-monotonic ⇒ ALWAYS quantum
  └─ Finite-T AD: p₂≥0.86 region ⇒ CLASSICAL memory sufficient
  └─ Dephasing: random unitary ⇒ classical (coin-flip)
  └─ Criterion: sufficient but NOT necessary (white region)
  └─ Requires: single-time channel tomography only
  └─ Role: THE criterion — computable from JC reduced dynamics

backer_entropic_witness_quantum_memory_2501.17660
  └─ Von Neumann entropy-based witness
  └─ Works for ANY dimension (qudits + continuous-variable)
  └─ Demonstrated on damped harmonic oscillator
  └─ Role: SCALABLE alternative — compute from JC mode entropy

vieira_eb_channels_quantum_memory_2402.16789
  └─ EB channels NOT classically simulable in multi-time
  └─ Taranto "Classical Memory" rung may need quantum resources
  └─ Role: CAVEAT — "classical enough" threshold stricter than EB

yosifov_emergence_quantum_memory_2507.21907
  └─ GHZ initialization → classical memory; Bell → quantum
  └─ Vacuum (product) closer to GHZ → suggests classical
  └─ Role: INITIALIZATION MATTERS — vacuum may be why memory is classical

maity_kolmogorov_classicality_signatures_2601.01122
  └─ KCC violation ⇔ NM, thermodynamic signatures
  └─ Negative-rate intervals = KCC amplification channels
  └─ Role: THERMODYNAMIC COST of non-classical memory

luppi_temporal_nonclassicality_ctqw_2512.18873
  └─ Short-time KCC ~ t² (quadratic); measurement-basis dependence
  └─ Site-basis dephasing → KCC→0; energy-basis → finite KCC
  └─ Role: MEASUREMENT BASIS matters — dual-axis may preserve non-classicality
```

### Tension Map

```
Factor                    Leans CLASSICAL          Leans QUANTUM
─────────────────────────────────────────────────────────────────
Channel type              ─                        Zero-T AD always
Mode decay (effective T)  Finite-T AD can be       ─
                          classical (Bäcker)
Reservoir initialization  Vacuum = product          Vacuum ≠ GHZ
                          (Yosifov GHZ analogy)     (no correlations at all)
EB between rounds         ─                        EB channels NOT
                                                   classically simulable (Vieira)
Measurement basis         Site-basis kills KCC      Dual-axis may preserve
                          (Luppi CTQW)              KCC violation
```

### Operational Question

**Is the user's JC memory (γ=0.15, vacuum mode, dual-axis X+Z measurement)
classically expressible?**

- **For the full channel dynamics:** LIKELY QUANTUM (zero-T AD → Bäcker Theorem 1 fires).
  Mode decay may push it toward finite-T regime where classical suffices.
- **For the restricted dual-axis syndrome records:** OPEN — likely CLASSICAL.
  The Dicke collective null absorbs the collectiveness term classically (TV=6e-5).
  The memory term dominance (~84%) may be superclassical (Budini) or classical
  mixing (Gangwar) at this γ.
- **Test:** Compute Bäcker 2310 criterion from JC reduced dynamics.
  If E♯[χ₁] ≥ E[χ₂] at γ=0.15 → classical memory sufficient for this operating point.
  If E♯[χ₁] < E[χ₂] → quantum memory required even at this γ.

## Unresolved: The Vacuum

**No paper in this graph:**
- Decomposes multi-time TV distinguishability of passive dual-axis syndrome records
  into {coherence, collectiveness, finite-γ memory} contributions
- Applies the MAD framework (Zonnios 2026) to JC shared-mode relaxation
- Runs the Luppi propagator decomposition on a collective-decay channel
- Tests the Budini DNI protocol on syndrome-extraction records
- Applies the Bäcker (2310) quantum-memory criterion to JC-model reduced dynamics
- Computes the entropy witness (Bäcker 2501) for the JC bosonic mode

**The gap is real but narrow — and now testable.** The field has all the components
(CGD theorem, DNI protocol, MAD framework, collective cross-terms, process-tensor
hierarchy, propagator decomposition, quantum-memory witnesses); no one has assembled
them for this specific object. The Bäcker 2310 criterion is the most immediately
computable test of whether the JC memory is genuinely quantum.
