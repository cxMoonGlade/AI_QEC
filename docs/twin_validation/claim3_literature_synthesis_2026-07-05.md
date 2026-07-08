# Claim 3 Literature Sweep — Final Synthesis (2026-07-05)

> **15 papers, deep-read.** 9 new reading notes + 6 existing modernized.
> RAG index: `docs/papers/reading_notes/README.md` §"Multi-time non-classicality decomposition".
> Knowledge graph: `docs/twin_validation/claim3_knowledge_graph.md`.

---

## 0. What this sweep found

**The user's suspicion was correct.** The adjacent literature is NOT a vacuum — it is
rich, current (2026), and speaks directly to Claim 3's decomposition problem. The
single most important finding: **the 2026 literature provides the formal tools to
separate the three confusion terms, but no one has assembled them for passive
dual-axis syndrome records in shared-mode σ− relaxation.** The gap is narrow and
the components are ready.

Two results change the status of Claim 3:

1. **Milz et al. (2020) is now solidly confirmed by 2026 follow-ups (Luppi, Gangwar,
   Vienna thesis):** in non-Markovian regimes, coherence is NOT the sole driver of
   multi-time non-classicality. Discord-mediated system-environment correlations take
   over. The user's finite-γ JC model operates in exactly this regime.

2. **Luppi et al. (2026) provides the exact propagator decomposition** that maps
   directly onto the user's TV-residual: Φ = Φ_QRT + Φ_memory. The QRT-like term
   is what the incoherent null model captures; the memory term IS the residual
   being decomposed. The second-order weak-coupling correction gives an analytical
   form for the finite-γ contribution.

---

## 1. The 15 papers — ranked by relevance to Claim 3

### Tier 1 — Directly provides formal tools for the decomposition

| # | Paper | What it gives Claim 3 |
|---|-------|----------------------|
| 1 | **Luppi et al. (2605.06427)** — "Multitime memory beyond QRT" | **Exact Φ = Φ_QRT + Φ_memory decomposition** [Eq. 22]. Operational ε_QRT quantifier [Eq. 28]. Second-order weak-coupling correction ∝ bath correlation functions [Eqs. 37-38]. Reduced-state NM ≠ multitime memory (inequivalence). **This is the formal engine for the decomposition.** |
| 2 | **Milz et al. (1907.05807)** — "When is a non-Markovian quantum process classical?" | **Non-Markovian non-classicality ⇏ coherence.** Discord-mediated s-e correlations become the driver. Genuinely quantum processes exist only with memory. **The theoretical warning that Claim 3's "coherence is core" premise is the Markovian answer applied to a non-Markovian system.** |
| 3 | **Gangwar & Sen (2603.28277)** — "Genuine and Non-Genuine Quantum NM" | **Definitive 2026 classification:** classical NM (convex mixing) ⊊ non-genuine ⊊ genuine (temporal entanglement). Information revivals CAN be classical. **The decision tree for which confusion term is genuinely quantum.** |
| 4 | **Smirne et al. (1709.05267)** — "Coherence and non-classicality of quantum Markov processes" | **Theorem 2: CGD ⇔ non-classicality (under Markovianity).** Explains why σz (NCGD) is classically simulable but σ− (CGD) is not. **BUT the theorem's condition (Markovianity) fails for finite γ — exactly where Claim 3 lives.** |

### Tier 2 — Provides operational framework or specific component

| # | Paper | What it gives Claim 3 |
|---|-------|----------------------|
| 5 | **Zonnios & Binder (2606.19511)** — "Bounded coherent memory" | **MAD framework:** d_A parametrizes coherent memory. The user's min-TV = d^{(N)}_{MAD}(exact, null; d_A=1). Residual = gap to true d_A. **The operational language for "how much of the residual is coherent memory."** |
| 6 | **Taranto et al. (2307.11905)** — "Hierarchy of multi-time processes" | **Five-rung strict hierarchy:** ③↔Classical Memory, ②↔Separable/Quantum, ①↔Quantum Memory. For N≥3 all classes strictly distinct. **Why multi-time (N≥3) data is needed to separate ② from ③.** |
| 7 | **Artag et al. (2605.15882)** — "Complementary records of decoherence" | **Environment stores TWO records:** concentrated quantum (cat state, one mode >95%) + redundant classical (Darwinism, R≈13). V²+D²=1 complementarity. **The dual-axis (X+Z) measurement sees both — which dominates depends on the basis.** |
| 8 | **Budini (2301.02500)** — "Violation of DNI" | **DNI operational protocol:** I(t,τ) [Eq. 9] = direct K-analogue. Unitary s-e coupling ⇒ DNI violation. **The measurement protocol for testing whether finite-γ memory is invasive (quantum) or non-invasive (classical).** |

### Tier 3 — Grounds a specific confusion term

| # | Paper | What it gives Claim 3 |
|---|-------|----------------------|
| 9 | **Budini (2411.13471)** — "Superclassical non-Markovian dynamics" | **Superclassical class:** non-Markovian but DNI-satisfying. Finite-γ memory CAN be classical. **Null model: if the finite-γ JC satisfies superclassical conditions, ③ is classical despite NM appearance.** |
| 10 | **Wang et al. (1409.0172)** — "Collective dephasing common bath" | **Exact cross-term Γ_common = Γ_indep + 8√(J₁J₂).** J_eff(r) = J₁·(1−|r|)² → K(r) scaling. DFS at r=1. **Adaptable from σz dephasing to σ− amplitude damping: the analytical template for collective cross-terms.** |
| 11 | **Fanchini et al. (1301.3146)** — "Independent vs common NM" | **Collective NM is super-additive.** BLP and LFS can disagree. Independent-AD null CANNOT reproduce common-bath signatures. **Grounds Control 2: regardless of parameter tuning, the independent-AD null misses collective physics.** |
| 12 | **Giarmatzi & Costa (1811.03722)** — "Witnessing quantum memory" | **Quantum memory ⇔ temporal entanglement in process matrix.** Classical ⇒ separable. **If the JC process tensor is temporally entangled, collectiveness ② is genuinely quantum.** |

### Tier 4 — Supporting tools

| # | Paper | What it gives Claim 3 |
|---|-------|----------------------|
| 13 | **Smirne et al. (1910.11830)** — "Experimental control of non-classicality" | **Only experimental D_K ∝ C paper.** Markovian only. **Baseline for what coherence-driven non-classicality looks like without memory.** |
| 14 | **Sakuldee et al. (2204.11698)** — "Commutativity and classicality" | **Multi-time classicality ≠ simple commutation.** **Formalizes why the σz commutation intuition does not fully determine multi-time outcome.** |
| 15 | **Bracht & Cygorek (2605.22386)** — "Factorization rule" | **n-time correlations factorize for Δt > τ_c.** **Bounds ③: if τ_c ~ 1/γ < Δt_syndrome, multi-time effects collapse to 2-time.** |

---

## 2. What the literature now says about each confusion term

### ① Coherence — "Is it the irreducible core?"

**Literature verdict: NOT in the non-Markovian regime.**

- **Smirne 2019 (Theorem 2):** YES, coherence ⇔ non-classicality — but ONLY under
  Markovianity. The theorem is clean and exact, but its premise fails at finite γ.
- **Milz 2020:** The moment memory enters, discord-mediated system-environment
  correlations replace coherence as the driver. The Smirne equivalence breaks.
- **Gangwar 2026:** Confirms this in review form. Classical mixing can produce NM
  revivals indistinguishable from coherent backflow at the two-time level.
- **Luppi 2026:** The QRT-like term (Markovian, coherence-driven) and the memory
  term (non-Markovian, discord-driven) are distinct components of the propagator.
  The TV residual conflates both.

**Implication:** Claim 3's "coherence is the dominant driver" is the RIGHT answer
for a Markovian system and the WRONG question for the finite-γ JC model. The
correct question is: "what fraction of the residual is CGD-coherence, what fraction
is finite-γ memory, and what fraction is collectiveness?"

### ② Collectiveness — "Is it separable from coherence?"

**Literature verdict: YES, it has a distinct analytical signature — but requires N≥3 times to separate from classical memory.**

- **Wang 2015:** The cross-term ∝ √(J₁J₂) in the master equation is a clean mathematical
  signature. Adaptable from σz dephasing to σ− amplitude damping via the collective
  jump operator L = √Γ(σ−₁+σ−₂).
- **Fanchini 2013:** Collective NM is super-additive. Independent-AD null cannot fit it.
  BLP and LFS can disagree — the user's TV (closer to BLP) may see different
  collectiveness signatures than correlation-based measures.
- **Taranto 2024:** Collectiveness maps to the Separable or Quantum Memory rung.
  At N=2 times, it can be confused with Mixed Memory (classical convex mixing).
  N≥3 required for clean separation.
- **Giarmatzi 2021:** If the process matrix is temporally entangled → collectiveness
  is genuinely quantum. This is testable.

**Implication:** Control 2 (adding collective AD to the null family) will absorb
the part of the residual that comes from collective jump structure. What remains
is ①+③. The N≥3 requirement means a 2-time TV protocol may misclassify some
collectiveness as classical memory.

### ③ Finite-γ Memory — "Is it really quantum?"

**Literature verdict: It CAN be classical or quantum — and the distinction is measurable.**

- **Budini 2023/2025:** The DNI protocol I(t,τ) directly tests whether finite-γ
  memory is invasive (quantum) or non-invasive (superclassical). If the JC model
  satisfies the superclassical conditions, finite-γ memory is classical even though
  it produces non-Markovian signatures.
- **Luppi 2026:** The memory term Φ_memory scales with bath correlation functions.
  As γ→∞ (Markovian limit), Φ_memory → 0. As γ→0 (strong memory), Φ_memory
  dominates. The second-order correction [Eqs. 37-38] gives the analytical scaling.
- **Bracht 2026:** For Δt_syndrome > τ_c ~ 1/γ, multi-time effects factorize.
  At γ=5, τ_c ~ 0.2 (in JC units) — if syndrome rounds are spaced wider than this,
  the memory contribution plateaus at the 2-time level.
- **Gangwar 2026:** Finite-γ memory can be in the "non-genuine" class (convex mixing
  of Markovian maps) or "genuine" (temporal entanglement). The distinction requires
  process-tensor analysis.

**Implication:** Control 1 (γ scan) can distinguish classical memory (vanishes at
γ→∞) from quantum memory (plateaus or shows discord residue). But the DNI protocol
is ALSO needed: even a non-vanishing residual at γ→∞ could be classical if the
superclassical conditions hold.

---

## 3. Updated evidence structure for Claim 3

### What is now HARD (theorem-backed)

| Statement | Grounding |
|-----------|-----------|
| σz sector is classically simulable (decoherence field, NCGD) | Smirne 2019 Thm 2 + crow_joynt |
| K is forgeable, not a witness (downgraded to diagnostic) | Budini 2023: superclassical dynamics can have K>0 without quantum memory |
| Reduced-state NM and multitime memory are inequivalent | Luppi 2026 Fig. 2: different parameter regimes |
| Independent-AD null cannot capture collective-bath signatures | Fanchini 2013: super-additivity; Wang 2015: cross-term structure |
| Process-tensor temporal entanglement ⇔ genuine quantum NM | Gangwar 2026 §5.5; Taranto 2024 hierarchy |

### What is PROVISIONAL (prediction band, needs Control 1/2)

| Statement | Status | Test |
|-----------|--------|------|
| "TV residual is dominated by coherence" | **UNVERIFIED ATTRIBUTION** — three-way confusion | Control 1 (γ scan) + Control 2 (collective null) |
| "Coherence amplifies ~5.5×, memory ~2.3×" | **Search-lower-bound artifact** — floor drift 0.037↔0.084 across passes | Recompute with Luppi decomposition as analytical constraint |
| "Coherent null closes 60-74% of gap" | **Provisional** — finite null family + non-convex search | Broaden to include superclassical nulls (Budini 2025) |
| "r=0 residual is the coherence floor" | **Confounded with ③** — single-qubit JC at γ=5 is still non-Markovian | Control 1 at r=0 |

### What is now ACTIONABLE (literature-grounded next steps)

1. **Recompute min-TV using Luppi decomposition as the formal structure:**
   - Φ_exact from JC MPS trajectories
   - Φ_QRT = the best fit from the incoherent null family
   - TV residual = ||Φ_exact − Φ_QRT|| = ||Φ_memory + (Φ_exact − Φ_QRT − Φ_memory)||
   - Fit the second-order weak-coupling correction [Luppi Eqs. 37-38] to isolate the
     bath-correlation contribution

2. **Run Control 1 with the DNI protocol:**
   - r=0, scan γ from 5 → 20 → 50 → ∞ (Purcell limit)
   - Measure BOTH min-TV AND I(t,τ) [Budini Eq. 9]
   - I(t,τ) = 0 at any γ ⇒ superclassical ⇒ ③ is classical at that γ
   - min-TV → 0 AND I→0 ⇒ residual was ALL finite-γ classical memory
   - min-TV plateaus AND I>0 ⇒ residual has genuine quantum component (① or discord)

3. **Run Control 2 with process-tensor witness:**
   - Add collective AD L = √Γ(σ−₁+σ−₂) to null family
   - Reconstruct approximate process tensor for the JC model at r=1
   - Test temporal entanglement [Giarmatzi 2021, Gangwar 2026 §5.5]
   - Temporal entanglement ⇒ collectiveness is genuinely quantum
   - Separable ⇒ collectiveness is discord-only, can be simulated classically

4. **Extend to 3-time protocol:**
   - Taranto 2024: 2-time protocols cannot distinguish Mixed from Classical memory
   - Add a third syndrome round → 3-time TV protocol
   - Tests whether the residual structure requires genuinely quantum (temporally
     entangled) memory or is compatible with classical convex mixing

---

## 4. The decomposition the field now enables

The 15 papers, assembled, provide this decomposition framework:

```
TV(P_exact, P_null) = || Φ_exact − Φ_null ||

Φ_exact = Φ_QRT + Φ_memory                           [Luppi 2026, Eq. 22]
         = Φ_QRT + Φ_memory^coh + Φ_memory^coll + Φ_memory^cl

where:
  Φ_QRT          = best fit within incoherent null family (Markovian, independent)
  Φ_memory^coh   = genuinely quantum coherence contribution
                    (CGD under Markovianity [Smirne 2019],
                     discord-mediated in non-Markovian [Milz 2020])
  Φ_memory^coll  = collective (superradiant) contribution
                    (cross-term ∝ √(J₁J₂) [Wang 2015],
                     super-additive NM [Fanchini 2013])
  Φ_memory^cl    = classical finite-γ memory contribution
                    (superclassical if DNI holds [Budini 2025],
                     second-order ∝ bath correlations [Luppi 2026, Eqs. 37-38])

Operational separation:
  Control 1 (γ→∞):  Φ_memory^cl → 0, Φ_memory^coh → ? (plateau or vanish)
  Control 2 (+collective null): Φ_memory^coll absorbed if collective; residual = ①+③
  DNI protocol [Budini 2023]: I(t,τ)=0 ⇒ Φ_memory^cl is superclassical
  Process-tensor witness [Gangwar 2026]: temporal entanglement ⇒ Φ_memory^coh + Φ_memory^coll genuine
  Factorization [Bracht 2026]: if Δt > τ_c, n-time contributions bounded
```

**This decomposition was not possible before the 2026 literature.** The Luppi
propagator split, the Gangwar genuine-vs-non-genuine classification, the Zonnios
MAD framework, and the Artag complementary-records demonstration were all
published in 2026. They collectively provide the formal language that was missing.

---

## 5. What Claim 3 can now claim

### What SURVIVES (provisional, scope-bounded)

> Passive dual-axis syndrome records in shared-mode σ− relaxation are
> TV-distinguishable from ANY non-coherent amplitude-damping null family tested.

**Scope:** the specific null families tested (independent AD ± classical latent).
**Status:** SURVIVES_PROVISIONAL — the TV floor is real, not a numerical artifact.
**Literature support:** Luppi 2026 (Φ_memory ≠ 0 at finite γ), Milz 2020
(non-Markovian regime has irreducible non-classicality), Fanchini 2013
(common-bath signatures not capturable by independent nulls).

### What is NOW LITERATURE-GROUNDED (can be stated with citations)

> The three physical sources — coherence, collectiveness, and finite-γ memory —
> are individually well-characterized in the literature but have not been
> disentangled for this specific object (passive dual-axis syndrome records
> in shared-mode σ− relaxation). The tools to disentangle them now exist:
> the Luppi propagator decomposition [2605.06427], the Gangwar-Sen genuine-NM
> classification [2603.28277], the Budini DNI protocol [2301.02500], and the
> Wang collective cross-term analysis [1409.0172].

### What REQUIRES Control 1/2 (prediction band)

> We predict that Control 1 (r=0, γ→∞) will cause the min-TV residual to
> substantially decrease, consistent with the Luppi second-order scaling
> [2605.06427, Eqs. 37-38], and that Control 2 (collective-AD null) will absorb
> the r=1-specific excess residual, consistent with the Wang cross-term
> structure [1409.0172, Eq. 14]. If both controls close the residual, the
> dominant drivers are finite-γ memory and collectiveness, not coherence.

**Prior:** "大概率随 γ 掉下去" — the user's registered prior for Control 1.
**If confirmed:** Claim 3's "coherence is the (dominant) driver" is FALSIFIED;
replaced by "finite-γ memory + collectiveness are the drivers, coherence is
subdominant in this non-Markovian regime."

---

## 6. Reading notes created/updated

### New (9 notes, 2026-07-05)

| File | Lines | Key contribution |
|------|-------|-----------------|
| `luppi_multitime_beyond_QRT_2605.06427.md` | 142 | Propagator decomposition, ε_QRT quantifier |
| `smirne_coherence_nonclassicality_markov_1709.05267.md` | 144 | CGD/NCGD theorem, Markovian-nonMarkovian boundary |
| `zonnios_bounded_coherent_memory_2606.19511.md` | 164 | MAD framework, d_A parametrization |
| `giarmatzi_witnessing_quantum_memory_1811.03722.md` | 131 | Temporal entanglement witness |
| `smirne_experimental_nonclassicality_coherence_1910.11830.md` | 134 | Experimental D_K ∝ C baseline |
| `fanchini_independent_common_nonmarkovianity_1301.3146.md` | 154 | Independent vs common NM, super-additivity |
| `bracht_factorization_multitime_correlations_2605.22386.md` | 149 | n-time factorization for finite τ_c |
| `taranto_hierarchy_multitime_classical_memory_2307.11905.md` | 190 | Five-rung strict hierarchy |
| `wang_collective_dephasing_common_bath_1409.0172.md` | 219 | Cross-term structure, K(r) scaling |

### Existing (6 notes, verified/updated)

| File | Status |
|------|--------|
| `milz_when_nonmarkovian_process_classical_1907.05807.md` | ✓ Good, no update needed |
| `gangwar_sen_genuine_nonmarkovianity_review_2603.28277.md` | ✓ Good, no update needed |
| `artag_complementary_quantum_classical_records_2605.15882.md` | ✓ Good, no update needed |
| `budini_dni_violation_hallmark_2301.02500.md` | ✓ Good, no update needed |
| `budini_superclassical_dni_2411.13471.md` | ✓ Good, no update needed |
| `sakuldee_commutativity_classicality_multitime_2204.11698.md` | ✓ Good, no update needed |

### Infrastructure updated

| File | Change |
|------|--------|
| `docs/papers/reading_notes/README.md` | New section: "Multi-time non-classicality decomposition — Claim 3 literature spine" with all 15 entries + synthesis table |
| `docs/twin_validation/claim3_knowledge_graph.md` | NEW: entity map (confusion terms → papers → criteria), citation graph, control-experiment grounding, vacuum assessment |
