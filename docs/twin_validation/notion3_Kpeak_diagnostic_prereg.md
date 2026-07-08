# notion-3: why does K(|r|) PEAK at intermediate |r|? — Pre-Registration (theory-first)

Status: PRE-REGISTRATION, 2026-07-05. Predictions written BEFORE the run; a miss is a finding, not a re-fit.

**The puzzle.** On the faithful joint-parity carrier (2 data + 1 ancilla + shared σz pseudomode, |++> code
state), K(|r|) is NON-MONOTONE: K/K_proxy = 1.00, 1.33, 1.16, 0.35, 0.006 at |r| = 0, 0.25, 0.5, 0.75, 1.0
(`notion3_ancilla_mediated_prereg.md` §10). And K is CERTIFIED sign-blind (K(r)=K(−r),
[[project-jointparity-K-sign-blind-sx1]]) ⇒ K = f(|r|). The DFS/interference form `J_eff = (1−|r|)²`
(wang/hatifi) predicts a MONOTONE decline — but K RISES first. So **K ≠ J_eff; there is structure to explain.**
Scope: SIMULATOR record-char diagnostic (understand the observable), NOT twin recovery. Cheap (reuse v2).

## 0. Grounding (reuse; all 精读)

- **K ≡ Budini DNI-violation** `I(t,τ)=Σ|P₃−P₂|` (budini 2301.02500) = INVASIVENESS; requires BOTH memory AND
  measurement–coupling MISALIGNMENT. Superclassical = memory WITHOUT invasiveness (budini 2411.13471).
- **DFS/dark-mode** (wang 1409.0172 `J_eff=(1−|r|)²`; hatifi 2508.07046): at |r|=1 the measured (symmetric)
  mode is DARK ⇒ misalignment → 0 ⇒ K → 0. Governs the |r|=1 FALL (grounded, not re-tested here).
- **multi-time ≠ single-round** (sakuldee 2204.11698): the record's K is a genuine multi-round object; memory
  and invasiveness need not track together.

## 1. Hypothesis (the mechanism, decomposed)

**K = invasiveness ≈ [correlation strength C(|r|)] × [misalignment M(|r|)].** As |r| grows from 0:
- **C(|r|) RISES** — coupling the 2nd data qubit to the shared memory-bearing mode enriches the d0↔d1
  correlation the joint parity probes (more multi-time non-classical structure). Drives the RISE.
- **M(|r|) FALLS to 0 at |r|=1** — the measured symmetric mode becomes the DFS/dark mode; the coupling aligns
  with it; back-action to the measured observable destructively interferes (grounded DFS). Drives the FALL.
- Product ⇒ **K PEAKS at intermediate |r|** (~0.2–0.3).
- **Memory (C_pf, M_mem, CMI) ≈ C(|r|) ALONE** (needs only correlation, not misalignment) ⇒ **MONOTONE RISING.**

## 2. Observables (all on the joint-parity ancilla record; reuse v2 + add C_pf)

Fine |r| sweep (|r| ∈ {0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0}, g₀ fixed = 0.5, Fock-converged
nmax): per point compute **K** (Milz/DNI), **C_pf** (budini conditional past-future, Eq 11 — the DNI memory
axis), **M_mem**, **CMI**. Report all four vs |r| on one plot/table + the peak location of K + a fit.

## 3. Predicted behavior (falsifiable) + epistemic classes

- **(b) THE signature:** **K(|r|) rises then falls (peak ~|r|=0.2–0.3); C_pf AND M_mem/CMI rise MONOTONICALLY.**
  The DIVERGENCE (K peaks while memory climbs) is the budini superclassical mechanism: invasiveness = memory ×
  misalignment, and misalignment dies at the DFS. **Falsifier 1:** if C_pf/M_mem ALSO peak (not monotone), the
  "memory needs only correlation" decomposition is WRONG (a finding). **Falsifier 2:** if K is actually MONOTONE
  (no rise) at converged nmax, the v2 1.33× rise was a truncation/seed ARTIFACT (a finding — retract the peak).
- **(b) fit:** K(|r|) is better fit by a rise-then-fall form (e.g. `|r|^a(1−|r|)^b` or `C(|r|)(1−|r|)²`) than by
  the monotone `(1−|r|)²`; report the peak |r| and the fit residuals for both.
- **(a) exact / control:** K(r)=K(−r) sign-blind (reuse the certified σx₁ result — assert on ≥1 point);
  classical shared-bath arm K<1e-8 across |r| (the rise is genuinely quantum, not classical-feedback,
  gherardini); Fock convergence to 1e-4 at the PEAK and at |r|=1 (the rise must be converged, not truncation).
- **(c) gate:** Fock-converged; classical-K null; sign-blind re-check passes.

## 4. Independent ground truth (non-circular)

- **build_L2 GT** (2-qubit collective-dephasing closed form, reuse v2, 6.8e-10) — re-assert.
- **K ≡ DNI** self-consistency: our K_stat and budini I(t,τ) are the same statistic — assert numerically equal;
  C_pf is the INDEPENDENT memory axis (not derivable from K).
- **classical-K null across |r|** (Outcome-F control): the rise is quantum, not ancilla-reset feedback.
- **Fock convergence at the peak** (the rise is real, not truncation — Falsifier 2).

## 5. Bounded simplifications (declared)

- **(c) independent-modes control is DIM-INFEASIBLE** (two modes ⇒ dim 4·nmax² ⇒ superop ~68 GB at converged
  nmax) — so the DFS-fall is argued analytically from the grounding (wang/hatifi), NOT tested by an
  independent-modes arm; the RISE is tested via the memory-vs-invasiveness DIVERGENCE (§3). Declared, bounded.
- **(c) |++> single X-stabilizer, pure σz-dephasing, 3-time K, CPU exact-DM, Fock nmax** — as v2.

## 6. Verdict (provisional, pre-code)

GROUNDED: the budini DNI decomposition (invasiveness = memory × misalignment) predicts the peak; the DFS grounds
the fall; the memory-vs-invasiveness divergence is the falsifiable signature. Cheap (reuse v2 + add C_pf + fine
sweep). PROVISIONAL until measured; a monotone-K (artifact) or a peaking-memory (wrong decomposition) are both findings.

## 7. Build org (lean — reuse v2 + builder + un-led reviewer)

Reuse `notion3_ancilla_mediated_run.py` v2 verbatim (build_L2 shared-bath, joint-parity extraction, K/M_mem/CMI,
controls, Fock convergence). Builder: (1) ADD C_pf (budini Eq 11) + assert K≡DNI-I numerically; (2) fine |r|
sweep (11 points, g₀=0.5) at converged nmax; (3) print K, C_pf, M_mem, CMI vs |r| + the K-peak location + a fit
(rise-then-fall vs monotone); (4) classical-K per |r|; (5) sign-blind re-check on one point; (6) Fock
convergence AT the peak. Scripted-execution + smoke. Un-led reviewer: confirm the peak is Fock-converged (not
artifact), C_pf is the genuine budini object (not a re-labeled K), and the divergence claim is honestly
supported. Then serial CPU run.

## 8. Post-run results (smoke, 2026-07-05) — peak REAL + converged; superclassical framing PARTLY over-stated

`outputs/twin_validation/notion3_Kpeak_diagnostic_run.py` (SMOKE only; `python-exit=0`; sha256 `a55982df…`;
GATE `NOTION3_KPEAK_SUPERCLASSICAL_DIVERGENCE`). Workflow builder + un-led reviewer (`meets_spec=true`,
`peak_is_real=true`).

**CONFIRMED (the core):** the K(|r|) peak is **GENUINELY Fock-converged, not a truncation artifact** — the
reviewer independently laddered nmax {10,14,18,22} at the true-peak region {0.3,0.4,0.5} (the run only laddered
0.2 & 1.0); dK 18→22 = 2.8e-6…7e-9 ≪ the 1e-4 gate. K rises `0.059 → ~0.081` then collapses to `3.3e-4` at
|r|=1; K/K_proxy peak **~1.38 at |r|=0.3** (fine grid; the smoke's 0.4 is coarse-grid). Rise-then-fall
`|r|^a(1−r)^b` fit beats monotone `(1−|r|)²`. **Falsifier-2 (artifact) REJECTED.** K is the genuine Milz/DNI
Kolmogorov violation (K_stat == Budini I == from-scratch, |diff|=0.0). ⇒ **the peak-then-collapse is real:
K=invasiveness peaks at intermediate |r| then the DFS suppresses it at |r|=1, while memory (M_mem/CMI) climbs —
the invasiveness-vs-memory divergence holds in the INTERIOR.**

**⚠ CAVEAT 1 (major, reviewer): C_pf is NOT an independent memory axis here.** On these symmetric records
`C_pf ≡ M_mem` to machine precision (structural identity: `sign(cov(x,z|y)) == g(x)g(z)` ⇒
`C_pf = ΣP(y)|cov| = M_mem`). C_pf is a genuinely distinct functional in code (diverges on random/anti-correlated
distributions) but DEGENERATE with M_mem on the carrier ⇒ the "divergence across MULTIPLE independent memory
axes" is really **K-vs-{M_mem, CMI}** (one memory functional + CMI), not two independent axes. The
"superclassical divergence" GATE is somewhat over-framed on memory-axis independence.

**⚠ CAVEAT 2 (minor):** full 11-pt sweep NEVER run (only 6-pt smoke); memory is monotone only after EXCLUDING
r=0 (on the fine grid M_mem DIPS r=0→0.1 and C_pf SIGN-FLIPS — the script reports full-grid-monotone=False
honestly); classical-K null is a single |r|-invariant point (the classical arm is r-independent by construction).

**RECONTEXTUALIZED by the crow_joynt reframe (`notion3_relaxation_dualaxis_prereg.md`):** this whole sector is
**PURE σz-DEPHASING = CLASSICALLY SIMULABLE** (crow_joynt 1309.6383) ⇒ the K-peak is a structured-but-LIMITED
signature of a classically-simulable component; the invasiveness peak + DFS collapse live entirely WITHIN the
classically-simulable sector. So this diagnostic explains the OLD-lens (pure-dephasing, X-only) behavior, and
correctly PLACES it — the genuinely-quantum test is the relaxation × dual-axis run, not this.
