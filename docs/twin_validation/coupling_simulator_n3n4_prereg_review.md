# Review — Coupling Simulator n=3–4 Pre-registration

**Reviewed object:** `docs/twin_validation/coupling_simulator_n3n4_prereg.md` (dated 2026-07-01)
**Review date:** 2026-07-01
**Review panel:** 3 independent agents (literature/epistemic fidelity, faithfulness protocol compliance, build feasibility/staging) + orchestrator direct fact-checks
**Verdict: REVISE (P0 + 4× P1) → BUILD**

---

## TL;DR

The pre-registration's core architecture is strong — mechanism correctly anchored to `[2506.10308]` SM §S2, the layered observable stack (BLP/RHP → D_Choi/1−F_e → %ΔLER) resolves the N=1 pilot's metric contradiction, the Gaussian shared-blind-spot is honestly declared, and the simulator (not twin) framing is clean and consistent. The issues are in epistemic-tag precision, a gate-vs-discovery classification conflict, and build-plan honesty about dependencies. **5 findings should be fixed before build (1× P0, 4× P1); 6 more are P2 (acceptable to defer); 2 are P3 (nice-to-have).**

---

## P0 — Must fix before build

### 1. Split the epistemic tag for "1/f as finite Lorentzian sum" (line 100)

**Reviewer:** Faithfulness Protocol + GLE reading note `[2402.11705]`

The current tag `(b→a)` conflates two regimes:

- The Lorentzian-sum **fit** within the fitted spectral range → bounded by BCF fit residual ε — plausibly (a)-class
- The **1/f power-law tail** beyond the Lorentzian approximation → explicitly **NOT** theorem-bounded

The GLE note `[2402.11705]` is explicit: "true power-law / 1/f long-memory with a rigorous bound — the exponential-decay assumption fails, the bound voids (branch-cut, M^γ_ω→∞)." Assigning a single (a)-adjacent tag to a simplification with an acknowledged unbounded component violates Rule III (unbounded → STOP, per `docs/FAITHFULNESS_PROTOCOL.md`). The tag `(b→a)` suggests the entire simplification is upgraded to (a)-class, when in fact the tail component is explicitly unbounded.

**Fix:** Split into two lines:

```markdown
- **(a) Lorentzian-sum BCF fit residual** — bounded by ε (Eq. S9) within the fitted spectral range
- **(c) 1/f tail via Lorentzian-sum representation** — heuristic, unbounded (the GLE bound voids for the
  branch cut; `[2402.11705]`); bracketed, NOT theorem-bounded
```

---

## P1 — Should fix before build

### 2. Reclassify the non-Gaussian boundary gate conjunct (lines 89–93, 120–124)

**Reviewers:** Faithfulness Protocol + Build Feasibility (independent agreement)

The non-Gaussian boundary gate is classified as a **(b) prediction band** in §4 and §9 ("a miss is a finding, widens scope"), but §7's acceptance gate makes it a **(c) blocking conjunct**. This creates a perverse outcome: if the Gaussian carrier unexpectedly *matches* the non-Gaussian TLS oracle, that's a positive scientific finding (scope is wider than claimed), but the gate would **block progress**.

The falsifier at lines 91–92 says: "it matches → the Gaussian scope is wider than claimed (a finding, widens scope)" — this is a discovery, not a failure. The only STOP condition is "the discrepancy is unbounded/uninterpretable" (line 93).

**Fix:** Remove conjunct (iv) from the acceptance gate (§7). The non-Gaussian boundary remains a (b) registered bet and a research finding; it does not gate the next rung. The acceptance gate becomes: (i) CPTP carrier + BCF match, (ii) oracle agreement ≤1e-3, (iii) wedge real + non-tautological + motional-narrowing, (iv) n_max bounded. Also revise C7 in §6 from a gate-like falsifier to a discovery statement.

### 3. Fix the motional-narrowing `γ₀/λ<1/2` model mismatch (lines 82–84, C6)

**Reviewer:** Literature Fidelity

The pre-reg describes a **pure-dephasing** build (`Ŝ_j = Z_j`, §1), but the motional-narrowing gate references `γ₀/λ<1/2` — a parameterization from the **JC/amplitude-damping** model (`[2509.19685]`), not pure dephasing. For pure dephasing, non-Markovianity depends on BCF oscillatory structure: the TCL rate `γ(t) ∝ ∫₀ᵗ Re C(τ)dτ`, and the wedge vanishes when the BCF is a non-oscillatory pure exponential. The `γ₀/λ` parameter belongs to the JC arm, which the pre-reg explicitly defers to the next rung.

Additionally, for a matrix-valued BCF, the "overdamped limit" is defined by the eigenvalue spectrum of `K = H − iΓ` (all eigenvalues having negative imaginary parts), not by a scalar `γ₀/λ` ratio.

**Fix:** Replace the gate condition with:

```markdown
- **(c) GATE — wedge vanishes in motional narrowing.** BLP N, RHP I **→ 0** when the BCF is a
  non-oscillatory pure exponential (pure-dephasing case: γ(t) = ∫₀ᵗ Re C(τ)dτ monotone, no sign
  change → no CP-divisibility breaking). For a matrix BCF, the overdamped limit is defined by all
  eigenvalues of K = H−iΓ having negative imaginary parts. *The JC amplitude-damping γ₀/λ<1/2
  form is deferred to the JC/RWA-CPTP arm (next rung).* Falsifier: nonzero wedge in the
  non-oscillatory-BCF limit → the wedge is an artifact.
```

### 4. Tag the closed-form multi-qubit oracle as "TO BE DERIVED" (lines 58–61)

**Reviewers:** Literature Fidelity + Faithfulness Protocol + user's own flag #1

The pre-reg presents the functional form `exp(−Σ_ij (Δs)_i(Δs)_j Γ_ij(t))` as an "(a) from-scratch theorem" (§3, §9). But the user explicitly flags it as **not yet derived**. The cumulant formula is a standard result for Gaussian baths — the risk is not theoretical novelty but **independence**: if the derivation inadvertently references the pseudomode K or g, the circularity-protection collapses and the oracle shares the carrier's blind spot.

**Fix:** Add an explicit pre-build gate before the oracle can be trusted:

```markdown
- **(a) [TO BE DERIVED — pre-build theory task]** Closed-form multi-qubit independent-boson oracle.
  The derivation must start from the bare system-bath Hamiltonian H = Σ_i Z_i Â_i using the cumulant
  expansion, with **zero reference** to the pseudomode construction (K, g, Γ). The functional form
  exp(−Σ_ij (Δs)_i(Δs)_j Γ_ij(t)) is the known Gaussian-bath cumulant result applied to our
  multi-qubit notation — not a novel theorem. **Independence check:** verify that Γ_ij(t) is
  computed from the BCF via the Hamiltonian cumulant path, not via the pseudomode K.
```

### 5. Fix the "reuse the v1 engine" overstatement (line 131)

**Reviewer:** Build Feasibility

The pre-reg says "dense, GPU, exact — reuse the v1 engine." But the N=1 pilot's own results state: "the pilot required a NEW dense engine — the existing per-site MCWF has no shared-bath representation" (`coupled_pseudomode_pilot_v1_results.md` lines 95–96). The v1 core Liouvillian construction CAN be reused, but the **dense-Γ jump-operator factorization** and **multi-mode (N>1) extension** are new builds — which the pre-reg itself acknowledges at lines 36–38.

**Fix:**

```markdown
(c) enlarged CPTP GKSL on n=3–4 ⊗ N modes (dense, GPU, exact — reuse the v1 engine's core
Liouvillian construction; the dense-Γ jump-operator factorization (see §1) and multi-mode
(N>1) extension are new builds)
```

---

## P2 — Should fix, acceptable to defer

### 6. D_Choi convention gap at n=3–4 (lines 50–52)

**Reviewer:** Build Feasibility

The METRICS.md ledger defines `D_Choi` as **per-seam reduced-block** Choi trace distance (support ≤6q). At n=3–4 there is no seam — the full 2^(3–4)×2^(3–4) Choi matrix is directly computable. The metric is the same (½‖J₁ − J₂‖₁), but the convention (full-channel vs. per-seam reduced-block) differs.

Additionally, "D_Choi / 1−F_e" presents them as interchangeable alternatives — they are distinct metrics (trace-distance distinguishability vs. Uhlmann-fidelity of Choi states), related through Fuchs–van de Graaf but not identical.

**Fix:** State: "D_Choi at n=3–4 is the full-channel Choi trace distance ½‖J_coupled − J_factorized‖₁ (the ledger's per-seam reduced-block form does not apply here); 1−F_e is process infidelity — a supplementary but distinct metric."

### 7. Document the boundary gate's scope limitation (lines 66–68)

**Reviewer:** Faithfulness Protocol

ACE `add_single_mode` with a TLS tests **single-site** non-Gaussianity. It does NOT test non-Gaussian **shared-bath** correlations (e.g., two coupled TLSs both coupled to the qubits). The synthesis review flagged this explicitly: "ACE's non-Gaussian capability comes from `add_single_mode` (independent anharmonic modes) — a *different construction*, not collective-Â" (synthesis review claim #5).

**Fix:** Add after line 68: "This boundary gate tests only a single independent TLS; non-Gaussian shared-bath correlations (e.g., coupled-TLS network) require a future oracle and are not covered here."

### 8. Specify ESPRIT/Prony software dependency (lines 33, 129)

**Reviewer:** Build Feasibility

`scipy.signal` does NOT have ESPRIT. Options are: `pysespr` (non-standard package), custom matrix-pencil implementation, or the **Loewner frequency-domain route** (SM §S1, which avoids ESPRIT entirely and only needs `scipy.linalg` — already available). The build plan says "Loewner/ESPRIT" as if they're a single interchangeable step — they are distinct routes with different software requirements.

**Fix:** Choose one route and declare the software. Recommendation: the frequency-domain Loewner-SVD route (SM §S1), since the 1/f BCF is naturally specified in the frequency domain and only needs `scipy.linalg`.

### 9. Qualify [2602.21430 Eq. 18-20] as the single-Lorentzian building block (lines 39–41)

**Reviewer:** Literature Fidelity

2602.21430 Eq. 18 gives the **single** Lorentzian spectral density; Eq. 20 is the single-Lorentzian weak-damping BCF. The "finite Lorentzian sum" for 1/f noise is the standard multi-Lorentzian generalization (Tamascelli et al. PRL 120, 030402, 2018) — not written in 2602.21430 itself.

**Fix:** Add: "the single-Lorentzian building block (Eq. 18–20); the multi-Lorentzian sum for 1/f is the standard generalization."

### 10. Add code-scale transition constraint to acceptance gate (lines 123–124)

**Reviewer:** Build Feasibility

The PASS says "proceed to the code-scale rung (d≥3 patch, decoder, %ΔLER)." But the dense engine used at n=3–4 will not transfer to d≥3 (17+ data qubits × N modes × n_max Fock states = enormous Hilbert space). The code-scale rung needs MPS/TDVP — a different carrier. The acceptance gate should state what transfers (methodology) and what doesn't (the dense engine).

**Fix:** Add after line 124: "This gate certifies the SDP/ESPRIT construction method, the oracle methodology, and the wedge hypotheses. The dense GKSL engine is an n=3–4 prototype; the code-scale rung requires MPS/TDVP (the χ-truncation bound remains an open question — see synthesis review item (h))."

### 11. Clarify SDP "UNTESTED" scope (lines 31–35)

**Reviewer:** Literature Fidelity

The SDP Eq. 8 IS tested in the paper — on Ohmic, sub-Ohmic, Lorentzian-like, and semicircular spectral densities, all single-site (Fig. 1–3, SM Figs. S1, S3). What's **untested before this rung** is the SDP's application to a **multi-qubit matrix-valued BCF** with structured off-diagonal partial correlation. The current phrasing could be read as claiming the SDP itself is untested.

**Fix:** "The SDP construction (Eq. 8) is the paper's tested contribution. Its application to a **matrix-valued BCF with partial (Δs≠0) cross-qubit correlation** is UNTESTED before this rung."

---

## P3 — Nice to have

12. **Name the SDP solver backend** (line 35). Default: cvxpy + SCS (open-source BSD). Fallback: MOSEK or Clarabel if SCS has convergence issues on the matrix-BCF SDP.

13. **Acknowledge standing constraint omissions** (§6). Add a brief note explaining why the Faithfulness Protocol's standing constraints #2 (information–disturbance) and #3 (Clifford/detector-invariant ≠ dynamics-invariant) are structurally inapplicable: the object is a forward noise simulator, not a measurement instrument or a gate set. The omission is deliberate, not an oversight.

---

## Direct fact-checks (orchestrator)

| Claim | Status | Detail |
|---|---|---|
| cvxpy is a prerequisite (needs installing) | **BROKEN, worse than stated** | cvxpy IS installed in aiqec but **non-functional** — numpy incompatibility (`numpy.lib.array_utils` missing). Needs env fix before any SDP work |
| `[2602.21430]` has a 精读 note | ✓ | `docs/papers/reading_notes/markovian_embeddings_nonmarkovian_2602.21430.md` |
| ACE `[2405.19319]` has a 精读 note | ✓ | `docs/papers/reading_notes/ace_process_tensor_toolkit_2405.19319.md` |
| v1 pilot scripts exist | ✓ | `outputs/coupled_pseudomode_pilot_v1_n2.py` and revival robustness script |
| BLP/RHP closed forms match METRICS.md | ✓ | METRICS.md lines 315–316 verbatim match pre-reg lines 45–48 |
| ACE `add_single_mode` supports TLS | ✓ (syntactically) | NOT demonstrated for collective non-Markovian shared-bath case in the ACE paper |
| 2509.19685 is 精读'd | ✓ | `docs/papers/reading_notes/markovian_embedding_correlated_noise_2509.19685.md` |

---

## What holds up well

The pre-registration's core architecture is solid and learned the right lessons from the N=1 pilot and the synthesis review:

- **Mechanism anchoring.** The multi-qubit coupled-Lindblad construction (SM §S2 Eq. S2–S4) is correctly translated from the primary paper. The matrix-valued BCF with off-diagonal partial correlation is precisely what the N=1 pilot's Δs=0 tautology did NOT test.
- **Layered observable stack.** BLP/RHP (source) → D_Choi/1−F_e vs. factorized (channel) → %ΔLER coupled-vs-factorized (decoder, deferred) — correctly resolves the "coherence-sensitive ΔLER" self-contradiction the synthesis review flagged.
- **Gaussian shared-blind-spot declared, not hidden.** Lines 63–65 explicitly state that independence is method-level within the Gaussian regime. This is the synthesis review's central architectural finding, absorbed honestly.
- **Simulator (not twin) framing.** Consistently maintained throughout — forward faithfulness + value-over-factorized, no inverse/causal/do() claims. "Teacher" is explicitly redefined as "forward controlled generator."
- **Constraint ledger.** 8 rows (C1–C8), each with a genuine falsifier. The N=1 pilot's negative control (perturbed g → 7.3e-2 disagreement) proves the falsification pattern works.
- **Epistemic staging.** §9 prevents (b)/(c) items from hardening into downstream premises. The staging audit (engine+faithfulness+wedge this rung → %ΔLER+JC next rung) is clear and gated.
- **Build scope.** The pre-reg limits itself to n=3–4 with dense (exact) propagation, sidestepping the MPS χ-truncation that the synthesis review flagged as a Rule-III STOP. The open bound is acknowledged and deferred, not ignored.

---

## Acceptance gate (reviewer's assessment)

This pre-registration is **REVISE → BUILD** — the P0 and P1 items above are low-effort textual fixes (no code, no re-derivation). Once applied, the pre-registration is ready to gate the build per its own acceptance criteria (§7, with conjunct (iv) removed).

The three things the user flagged honestly are all correctly handled:
1. The multi-qubit closed-form oracle is properly identified as a theory-first gap (P1 #4 above strengthens the declaration)
2. cvxpy is indeed a prerequisite — and worse than "not installed," it's broken (numpy incompatibility)
3. This review satisfies the "review before build" discipline

---

## Review process

- **Literature/epistemic fidelity:** 1 architect agent (deepseek-v4-flash, 19 tool calls, ~98k tokens) — verified every equation translation against primary reading notes, checked epistemic tags, cross-referenced 2602.21430 and 2509.19685
- **Faithfulness Protocol compliance:** 1 architect agent (deepseek-v4-flash, 11 tool calls, ~54k tokens) — audited Rules I/II/III, checked for circular-verification traps, verified constraint ledger falsifiability
- **Build feasibility/staging:** 1 architect agent (deepseek-v4-flash, 16 tool calls, ~81k tokens) — verified metric conventions, checked software dependencies, audited acceptance gate logic
- **Orchestrator:** direct fact-checks (cvxpy status, v1 script existence, reading note existence, ACE capabilities, BLP/RHP closed-form verification)
