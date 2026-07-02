# Post-adjudication state confirmation — 2026-07-02 (READ + AUDIT round; no edits to pending-ratification files)

**Author context:** the week-1 agent (M1 prereg → M2 v3 → CGF probe → Branch B; commits bc3b605,
c7d8b48, a54304f, 2a12243, 1390674, c7abebd, 52ad01a, a7038a2, 4efc4b7). This round: READ-ONLY
audit per the state-confirmation prompt; the only writes are this doc + one durable-fact memory
line (Q1). HANDOFF §5, tex, existing preregs, adjudication doc: untouched. No runs, no GPU.

Epistemic labels: (a) exact / (b) registered band / (c) design-decision / [PROVISIONAL] as in
METRICS.md. All first-hand numbers quoted below are from committed logs/npz
(`outputs/logs/cgf_probe_v1.log`, `outputs/logs/quantum_bath_m2_dual_arm_v3.log`,
`outputs/_cgf_probe_v1.npz`, `outputs/_m2_quantum_bath_dual_arm_v3.npz`).

---

## 1. Sync confirmation (T1)

Read in full: `novelty_ownership_adjudication_2026-07-02.md`; the 9 new reading notes (budini
2305.16136, paz_silva 1609.01792, gicev 2310.12448, vonlupke 1912.04982, regev 2605.03054,
artag 2605.15882, maity 2601.01122, farina 1907.04704, remm 2502.17722 — plenio_knight reused
from A-P1-READ); the updated memory index (adjudication entry present, MEMORY.md:61).
**Consistency check:** every adjudication claim I could cross-check against a note's head
section matches (incl. the Gicev authorship correction verified against the note's own
"NOT Harper — verified from the PDF byline" line, and the von-Lüpke Huber-M-estimation reading).
No sync conflicts found.

## 2. Adversarial confirmation of the main-session readings (T2)

| Item | Verdict | Evidence (first-hand) |
|---|---|---|
| 1a: component (i) chain "identity → M2 γ/2 → P2 survival" | **AGREE, with one load-bearing precision** | Chain is right qualitatively. BUT Δ_term = 0.1718 ± 4.0e-4 is a **different-protocol object** (terminal-only: no mid-circuit Zeno pinning, single-bit λ-grid, coherent R·τ_m evolution). My §8 recorded exactly this: "Δ_term (0.172) ≫ Δ_record (0.019): mid-circuit measurements Zeno-pin both arms and SHRINK the wedge — the measurement-off variant changes the dynamical regime." ⇒ 0.172 must never be used as "component (i)'s size inside the record protocol" (bears on Q2/Q3 below). |
| 1a: (ii) scalings A^1.4–1.8, ~g⁴, saturation gτ≈0.63 = (b)-grade | **AGREE** | Matches my §8 registration status verbatim; with the Q2 caveat that both scalings were measured on the TOTAL wedge, not a separated component. |
| 1a: P4 = single-config provisional | **AGREE** | One operating point (g₀, N̄=0, R=4); companion statistic only; ex_q = −4.06e-2, ex_c = +3.30e-3 (log S3). |
| 1a: additivity of (i)+(ii) unverified | **AGREE — and unverifiABLE from existing outputs** | See Q3: the npz stores summary statistics only; no in-protocol component isolation exists; and at pinned χ the A-sweep scales BOTH components (non-unitality ∝ (γ↓−γ↑) ∝ A at fixed γ↓+γ↑), so no combination of existing sweeps isolates the floor. |
| D1: L2 non-unital classical rate imitator = the real adversary; L1 kept as fold-attenuation measurement | **AGREE on the design** | Q1 confirms L1/M2's class is unital-only ⇒ L2 needs a new definition. First-hand support for "L1 is weak": the probe's Δ_base (1.92e-2) is ~3.5× smaller than the naive round-1 single-λ marginal gap (~6.8e-2 from p_eg^q = 0.0882 vs p_eg^cl = 0.0440) — control × occupation-reweighting forges most of the directional marginal (the O(g²) selection channel registered in my P3 pre-run amendment). |
| D1: "D_comb > 0 vs L1 is decided by theorem BEFORE any run ⇒ vacuous as a gate" | **DISAGREE with the justification (the design action stands)** | (a) Data-processing/contractivity runs the WRONG WAY for a lower bound: composing both arms with the identical code machine can only shrink trace distance; the γ/2 theorem pins the PRE-machine channel gap, and no theorem carries it through the machine at any resolution. (b) First-hand measured attenuation: at g₀/4 the Markov-estimate channel-scale gap is ~γ_win/2 ≈ 2.5e-2 ((c)-rough, adiabatic-elimination units-caveat) while the record wedge is Δ = 9.65e-5 ± 1.1e-5 — an attenuation of order 10² already in the R=4 probe. ⇒ "D_comb(vs L1) > 0" is expected-positive (b), NOT theorem-guaranteed; as a gate it is *weak*, not *vacuous* — a null result would be a real (surprising, reportable) finding, not a contradiction. The M3 prereg must not cite a false theorem here (D3's own checklist). |
| D2: no meas-off switch at code layer; g-scan + N̄-scan instruments; register operating points away from gτ = 0.63 | **AGREE + two first-hand amendments** | (i) The probe's g-ladder local slopes are 3.90 / 3.74 / 3.19 (g₀/4→g₀/2→g₀→2g₀): **no visible ~g² component down to g₀/4** (a g²-floor would pull the small-g slope toward 2; it reads ≈3.9). If the floor is ~g², it is subdominant in the total wedge over the whole measured ladder ⇒ the g-scan alone may not separate the components at reachable MC power; the L2-DIFFERENCING instrument (Δ vs L1 minus Δ vs L2) is the robust separator, with the g-scan as corroboration. (ii) "c₂ pinned by the γ/2 value" needs a derived channel-floor → record-CGF transfer map (different objects/units); without it c₂ must float with a γ/2-scaling consistency CHECK, not a pin. |
| D3: theorem-inventory checklist before any M3 kill criterion | **AGREE + three additions** | Add: (1) machine/comb contractivity direction — no automatic comb-level lower bounds from channel-level theorems (the D1 correction above); (2) the structure lemma's exact-null theorem covers CLASSICAL-Gaussian sources only — the QUANTUM unit's "memoryless null" is NOT lemma-covered and needs its own declared construction (e.g., mode-reset-per-round; an A3-style definitional choice with a declared bound); (3) unraveling equivalence (A3) for any MCWF record claim. |
| D4: P4 as (b)-direction bet at the detector layer, never a premise; signed-p_ij framing | **AGREE** | T3 sweep confirms my artifacts contain no "≥0 by construction" language anywhere (grep-verified) and no 2310.12448/Harper attribution anywhere. The reframe obligation lands on future M3/paper text, not on existing files. |
| 1c: math spine = #2 + #3 + B | **AGREE** (independently re-confirms my Branch-B decision; no first-hand conflict) | My §8 Branch-B consequence line already pointed at #2+#3; B strengthens it. |
| 1c: paper identity sentence (lift Chen/Zheng learnable-vs-gauge to continuous Σ under passive records) | **NO-OBJECTION** [outside my first-hand evidence] | Consistent with everything I measured; Frame-D positioning condition (cite Chen/Zheng as precedent) noted. |
| 1c: Bone A final role = certification methodology + quantum-bath characterization apparatus | **AGREE** | Matches and hardens my A-P1 downgrade; my §9(1) language anticipated exactly this. |
| 1c: g⁴/A-crossover derivation + additivity check demoted to methods hygiene | **AGREE + scheduling note** | The additivity check needs the L2 instrument (Q3) and lands nearly-free INSIDE M3's imitator-ladder runs — keep it owed but schedule it there. |
| 1c: work order B → #2 → #3 → M3 | **NO-OBJECTION + one dependency observation** | M3's prereg inputs (L2 definition, c₂-transfer derivation, D1–D4, A-P1-READ D3 observables) do not depend on B/#2/#3 completion; the L2-definition derivation could proceed in parallel if wall-clock matters. Deferred to ratification. |

## 3. Self-audit violation list (T3) — found by pattern sweep over my touched files; NOT fixed this round

Positive sweep results first ((a), grep-verified): **no** "≥0 by construction" claims anywhere in
my artifacts; **no** 2310.12448/Harper mis-attribution anywhere; the tex Thesis/Contributions and
the 2026-07-02b/c ledger blocks already carry A-P1-compliant attributions.

| # | Locus | Offending phrase | Violates | Proposed fix (one line) |
|---|---|---|---|---|
| V1 | `coupling_simulator_intro_draft.tex:115` (header PENDING block) | "the classically-unforgeable arm of the paper" | Bone A (all three ingredients owned) | "the classical-boundary arm (ingredient physics owned per adjudication; ours = the QEC instantiation)" |
| V2 | `memory/project-quantum-bath-m1-m2.md` | "**(a)-THEOREM (new, clean)**" | cite-don't-claim (qualitative boundary owned L–S/C–J; constant folklore) | drop "new, clean"; append "(qualitative obstruction owned Landau–Streater/Crow–Joynt; constant = elementary corollary)" |
| V3 | `memory/project-quantum-bath-m1-m2.md` | "Two-component record-wedge decomposition = the real product" | Bone A verdict (decomposition = methodology sliver) | "= the surviving methodology sliver (ingredients owned per adjudication)" |
| V4 | `quantum_bath_slot_prereg.md:141–155` (§4) | "(a) THEOREM (why the classical carrier CANNOT host this slot — the sharp no-shortcut statement)… EXACTLY classically unrepresentable" — no ownership citations (pre-adjudication text) | Bone A attribution duty | future amendment (A-M1-1): add "(qualitative obstruction: Landau–Streater via Crow–Joynt; quantified map-level: Budini; our addition = the γ/2 constant (folklore-grade) + the QEC instantiation)" |
| V5 | `quantum_bath_slot_prereg.md:198, 240, 249, 324` | "decisive classically-unforgeable comparison"; "coherence-sector unforgeability EXCESS"; "unforgeable dissipative asymmetry"; "a SECOND unforgeability direction" | Bone A attribution duty | same A-M1-1 amendment: soften to "classical-boundary" language + owner cites; keep the measured numbers untouched |
| V6 | `cgf_probe_prereg.md:189` (§8) | "the probe delivered more than a bound: a two-component decomposition…" | Bone A (already superseded IN-DOC by §9(1) downgrade) | no action strictly needed; optionally add "(superseded by §9)" pointer when preregs are next amended |
| V7 | `memory/feedback-theory-first-and-sequencing.md` (my 2026-07-02 paragraph) | stale "Tregub/Kümmerer–Maassen" attribution | correction 3 lineage (P2 source = Landau–Streater) | superseded in-file by the DEBT-PAID block; optionally annotate the older paragraph |
| V8 | `coupling_simulator_intro_draft.tex` Contributions (vi) | "establishes the classical-forgeability boundary" (owners cited inline, so borderline) | tone vs Bone A | MINOR: "characterizes the classical-forgeability boundary … (boundary concept owned; ours = the γ/2 constant + QEC instantiation)" |

Note: header lines 47–49 ("SURVIVING novelty = detection-rate DECREASE …") are the PRIOR A9
adjudication's own output, not overturned by this round — left as-is deliberately.

## 4. Technical questions (T4) — answered from existing artifacts only; no reruns

**Q1 — M2's imitator class: unital-only, or already non-unital-capable?**
**(a) Unital-only.** The class is "classical Gaussian field entering via a Hamiltonian +
deterministic control" ⇒ per-path unitary ⇒ random-unitary ⇒ unital, and the arm is BUILT that
way: per-path exact 2×2 unitaries (`quantum_bath_m2_dual_arm.py` S3), with unitality enforced as
a structural CRASH gate — v3 log: "unitality (structural): ||Tr_ref J - I/2||_max = 2.22e-16".
The amplitude ladder s ∈ {0.5…1.25} stays inside the unital class (scaled fields are still
random-unitary). No jump/reset or population-pumping process exists anywhere in the arm.
⇒ **M3's L2 (non-unital classical rate imitator) needs a NEW definition; nothing inherits from
M2's prescription** except the matching/χ-pinning discipline and the rate-gate instrument.
(Durable fact — one line added to `memory/project-quantum-bath-m1-m2.md`.)

**Q2 — P3's power law was measured on WHICH object?**
**(a) The TOTAL record wedge**, Δ = max over the registered λ-grid of |K_q − K_cl^opt| against the
L1(+control) imitator, at N̄ = 0 in the R = 4 mid-circuit protocol — with no floor/terminal
subtraction of any kind. Evidence: `cgf_probe_v1.py` S6 calls the same `optimize_imitator`
objective as S3/S4; log lines "[S6] g = … Delta = …". Consequences for the proposed refit
c₂g² + c₄g⁴ (+ saturation): (i) it must fit the TOTAL-wedge ladder {9.6455e-5, 1.43772e-3,
1.91664e-2, 1.75301e-1} whose local slopes 3.90/3.74/3.19 show **no visible g² component down to
g₀/4** — rough bound from the smallest point: c₂·(g₀/4)² ≲ 2e-5 in record-CGF units; (ii) "c₂
pinned by the γ/2 value" is not yet well-posed — γ/2 is a channel-Choi trace-distance, Δ is a
record-CGF distance; the pin needs a derived transfer map (a small derivation deliverable for the
M3 prereg), else c₂ floats with a γ/2-scaling consistency check.

**Q3 — Additivity of (i)+(ii) checkable from existing outputs?**
**No — three independent blockers ((a) each):** (1) `_cgf_probe_v1.npz` stores summary statistics
only (D_base, asym_D, pow_D, D_term, slope, ex_q/ex_c…) — the record distributions P_q, P_cl^opt
were not persisted; (2) even with them, no in-protocol isolation of component (i) exists —
Δ_term is a different protocol (see T2 row 1) and CANNOT serve as the floor's in-protocol value;
(3) at pinned χ the asymmetry sweep scales BOTH components (the non-unital shift ∝ (γ↓−γ↑) ∝ A at
fixed γ↓+γ↓), so no linear combination of the existing sweeps separates them.
**Minimal run that decides it (for M3, not this round):** same R = 4 record protocol, add the L2
arm per point; then additivity ⇔ Δ(quantum vs L1) ≈ Δ(quantum vs L2) + Δ(L2 vs L1 at the
quantum-matched rates), tested across the g-ladder — i.e., the additivity check drops out of
M3's imitator-ladder instrument for free. Persist full P vectors in the npz this time.

**Q4 — A^1.4–1.8: crossover vs genuine anomalous power, from existing data?**
**Partially decidable — the constant-single-power hypothesis is REJECTED; the specific A¹+A²
crossover form is NOT confirmed.** From the printed sweep (Δ/Δ_base = 1, 0.7315, 0.2914, 0.0845,
0.01295 at A = 1, 0.8333, 0.5, 0.2, 0.04762), the LOCAL exponents between successive pairs are
**1.71, 1.80, 1.35, 1.31** with propagated SEs ±0.02–0.05 — a statistically decisive decrease
(≈9σ between the middle pairs) ⇒ no single power fits ((b)-grade conclusion from (a) numbers).
The trend direction (larger exponent at large A, smaller toward small A) is crossover-LIKE; but
the strict two-term unit-sum model c₁A + c₂A² (calibrated at A = 0.5 ⇒ c₁ = 0.166) misses the two
small-A points by −21% and −25% against 3–6% errors ⇒ the pure A¹→A² form is also rejected as
exact. Deciding "crossover toward slope 1" vs "intermediate effective power ~1.3" needs smaller-A
points (N̄ > 10, feasible with the GPU-RK4 route + cache) or the L2 component-resolved instrument
— an M3-adjacent run, not this round.

## 5. M3 readiness (T5)

**The M3 prereg must contain (D1–D4 as amended above + additions):**
1. **Imitator ladder** L1 (matched-BCF classical Gaussian + control; inherits M2's corrected
   prescription + rate gate) / **L2 (non-unital classical rate imitator — NEW DEFINITION REQUIRED:
   a classical jump/reset record-law with γ↓, γ↑ matched to the quantum rates; must state exactly
   what it can and cannot match, derived BEFORE registration)** / L3 (bounded-memory HMM/PT,
   reconnecting the owned-boundary literature). With the D1 justification corrected: L1 comparison
   = fold-attenuation measurement, expected-positive (b), NOT theorem-vacuous.
2. **Instruments:** L2-differencing as the primary component separator; g-ladder (dual registered
   operating points, extended BELOW g₀/4 with MC-power planning, since no g² component is visible
   down to g₀/4 in the probe); N̄-scan as the total-kill; the additivity check via the L1/L2 pair
   (Q3); full record-distribution persistence in the npz.
3. **Derivation deliverables BEFORE registration:** (i) the channel-floor → record-CGF transfer
   map (or declared floating-c₂ + scaling check); (ii) the L2 definition + its
   matching theorem; (iii) the QUANTUM unit's memoryless-null construction (mode-reset-per-round
   or alternative) with a declared bound — the structure lemma does NOT cover it.
4. **Theorem inventory (D3, extended):** γ/2 unitality floor (channel-level ONLY — no automatic
   comb transfer); structure lemma + its classical-source scope limit; machine/comb contractivity
   direction; Burke–Rosenblatt collider; unraveling equivalence; the A-sweep-scales-both-components
   fact (pinned-χ non-separability).
5. **Observable layer from A-P1-READ D3** (five field-anointed observables with owners + expected
   directions) + P4 as a (b)-direction bet with the signed-p_ij framing (D4).
6. **Engineering (task #4 list):** GPU-RK4 (λ_max = κ(2N̄+1)(n_max+1), λ·dt = 0.7), level-batch +
   mega-batch optimizer (c64 search / c128 report + printed gap), tree cache, section timestamps,
   Krylov expm-multiply as the contingency if dim-340-class trees dominate.
7. **A4 discipline:** effect-size registration from M2-v3 actuals + the probe's attenuation
   measurement before any full run; ≥3 seeds; machine-matched nulls; A8 scope.

**Blocked on user ratification:** HANDOFF §5 amendments; tex claim restructure (incl. my T3
V1/V8 fixes); the work order (B → #2 → #3 → M3 vs interleaving the L2-definition derivation);
the V4/V5 prereg amendment (A-M1-1).
**Proposed first concrete M3 step (post-ratification):** derive + register the **L2 imitator
definition** (the one object every M3 instrument depends on), together with the channel→record
transfer map — both zero-compute derivations that de-risk the entire prereg.

---

*Deliverable of the state-confirmation round; committed. No other files edited except the one
durable-fact memory line (Q1).*
