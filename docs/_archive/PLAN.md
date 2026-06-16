> **ARCHIVED 2026-06-15.** Superseded as the live roadmap by [../plan3.md](../plan3.md); kept for its methodology/invariants + decision history.

# The Twin — Project Plan

Binding roadmap for **the twin** (`qec_twin`). Division of labor:
[`docs/TWIN.md`](../TWIN.md) is the **object contract** (*what* the twin is); the
[ADR spine](../adr/) (0002→0008) records **decisions** (*why*); this file is the **path**
(*how / when / how it falsifies*). It is **strict** on physics, mathematics, and the
aim↔object map, and **deliberately open** on architecture/parameterization (ADR 0005).

**How to read it.** Each item is tagged **STRICT** (non-negotiable, phase-independent)
or **FLEXIBLE** (chosen later, against the four capabilities). Every phase gate in §3 is
a **triple — a physical criterion, a mathematical criterion, an aim↔object criterion —
plus a falsification signal**. Nothing here moves the claim boundary (§1.3); it
organizes work *inside* it.

## 1. Invariants — hold in every phase

### 1.1 Physical — graded by strictness

CPTP is the **floor, not the standard**. "Is just CPTP enough?" has a sharp answer: no —
CPTP-only with a data fit *is* the moment-matched / local-vol negative control (§1.2,
ADR 0003/0004). The load-bearing physical rule is the **exact Born rule on a
non-Clifford-capable forward**.

**1.1a — Load-bearing (STRICT, never relax).** Dropping any one collapses the twin into
the pre-registered DEM/local-vol failure mode:

1. **Exact Born-rule observation likelihood** — `p(y|c) = Tr[M_y · C_E(c)(ρ0)]`,
   `y=(s,m)`, `C_E(c)=∏_q (E_q ∘ G_q)` in circuit order. Calibration scores this, not
   moments.
2. **Non-Clifford / non-Pauli-capable forward** — coherent and non-Clifford structure
   must be *representable*, or the counterfactual it drives is invisible from the start.
3. **CPTP-by-construction** — `E_q = PhysDec(θ_q) ∈ CPTP` (Stinespring / GKSL). `θ`
   *generates* the channel; it is **not** a `do()` handle. This is the physical floor /
   a Tikhonov regularizer — necessary, never sufficient.
4. **LER under a predeclared, frozen decoder `D`** — `do() → ΔLER` is the headline
   observable; `p(y)` is its decoder-free, finer companion. `D` is fixed across teacher,
   twin, base, and `do()` evaluations; no retuning inside a score.

**1.1b — Bounded-but-swappable (STRICT within a declared window).** The exact
density-matrix backend (`forward/exact`) is *exact* where used but **feasibility-only
≤~15 qubits** (`2^n×2^n`). The invariant is the **channel object + Born interface**
(`forward/cptp_channel`), not the backend; `forward/scalable` swaps in for the
>50-qubit target (ADR 0005, deferred). A backend swap is a replacement, not a rewrite.

**1.1c — Construction freedom (FLEXIBLE).** Stinespring isometry vs GKSL generator for
*building* the CPTP channel is open — GKSL is required only once Tier-1
generator-scaling `do()` (`E=exp(kL)`) is in play; Tier-0 `E→I` needs neither. `θ`'s
parameterization (per-location field vs factor vs DEM-bulk+corrections) is open by
ADR 0005.

**HARDEN re-raises physical strictness as hardware realism.** Beyond the qubit-channel
idealization, realistic noise forces explicit modeling choices that must be *declared,
not silently approximated*: **leakage** breaks the 2-level / CPTP-on-subspace
assumption (a qutrit channel, not a qubit one); **correlated / crosstalk** errors break
per-location factorization `∏_q E_q`. Each is a strictness decision HARDEN records,
its approximation audited by the band (§1.2).

### 1.2 Mathematical — the inverse problem and its guardrails (STRICT)

- **Objective.** Recover `E` by **exact multi-context Born-NLL**,
  `min_E −Σ_{c∈C_cal(r)} Σ_n log p_E(s_n,m_n|c)`. **Never moment matching** — detector
  marginals + pairwise correlations are exactly what a stochastic Pauli channel
  reproduces, so moments **Pauli-shadow** the coherent structure (finance: "vanillas pin
  marginals, not dynamics"). Moment matching is a **negative control only**.
- **Identifiability = the observational alias quotient.** An observational fit pins `E`
  only up to `{E′ : p_{E′}(·|c)=p_E(·|c) ∀c∈C_cal}`. **Probe richness (data) is the only
  thing that shrinks it** — the ladder `C_cal(r)`: memory → multi-round/bases → active →
  basis-rotated → coherent-sensitive. Physical priors (CPTP, locality, known circuit) are
  **Tikhonov regularizers**: they shrink the variance/parameter space, **not** a genuine
  observational alias (ADR 0005 — parameter/orbit sharing retired as an identifiability
  lever).
- **Report bands, not points — and split them (three layers).** Over the
  calibration-consistent set `{E : NLL(E) ≤ NLL_min + slack}`: the **epistemic alias
  band** = range of `ΔLER` over that model set (Cont/UVM); the **statistical estimation
  band** = `ΔLER` spread under bootstrap of finite shots (the `1/√N` scale). Under
  HARDEN's misspecification axes a **third, model-class band** appears — `B_misspec`, the
  `ΔLER` deviation when the teacher's true object lies *outside* the learner's class
  (qutrit leakage vs qubit learner; non-factorized crosstalk vs factorized learner).
  Report the three **separately, never summed** (not independent; LER is **non-monotone**
  — coherent interference + decoder non-monotonicity — so the UVM pointwise shortcut
  fails, extremize **numerically** — and the decision-regret gate found even this is *not cheap*:
  on the toy a local / named-member evaluation **under-covers** the epistemic band, which needs
  **global continuation**, not a single fiber endpoint). `B_misspec` is measurable only against the
  controlled teacher; on hardware it is only *bounded* via transfer. **Band width vs `r`**
  is the single most important plot.
- **Hard theoretical guardrails** (survey W1–W5,
  [`IDENTIFIABILITY_AND_CRL_SURVEY.md`](../IDENTIFIABILITY_AND_CRL_SURVEY.md)):
  - **W1** counterfactual non-identifiability — observational ≠ interventional
    equivalence; a knob is validated only against realized ground truth.
  - **W2** learnable-degrees-of-freedom ceiling — the observation map has finite
    learnable DOF; directions outside it carry an honest nonzero band, *not* a recovered
    point. The *fundamental* ceiling is the rank/spectrum of the **Born-map Fisher
    information** `I(θ)=E[∂_θ log p·∂_θ log pᵀ]`; the DEM parity map `A` is the cheap
    **Pauli-linearized proxy for its stochastic sector only** — anchor/Moran on `A` gates
    the stochastic (Girsanov quadratic-variation) directions and is **blind to the
    coherent/drift directions** (W5), which live in the full Fisher and are earned by
    phase-sensitive probes. Gate with anchor/Moran + the DOF ceiling on `A` *before*
    measuring the curve — necessary, but partial.
  - **W3** binary observations break continuous identifiability tools — adapt, don't
    import naively.
  - **W4** CPTP constraints do not factorize in Kraus form — enforce by construction,
    not as a per-factor penalty.
  - **W5** coherent errors break the Pauli-DEM assumption — the reason 1.1a(2) is
    non-negotiable.
- **Girsanov decomposition** (the per-direction prediction): the stochastic/Pauli part is
  the **quadratic variation** — identifiable from second-order syndrome statistics; the
  coherent part is the **drift** — **alias-invisible** to second order, recoverable only
  with measure-distinguishing **phase-sensitive probes**. This predicts, per direction,
  where `B_LER(r)` can and cannot fall.
- **Probe design *could* become active (opportunity, not a committed method).** Beyond
  climbing `C_cal(r)`, the next probe could be targeted at the knob functional `g=∇ΔLER`
  (the finance *replicating portfolio* for the `do()` subspace, ADR 0004) — a direction
  to record, specified only if pursued.

### 1.3 Claim & isolation discipline (STRICT)

- **Isolation contract.** The learner consumes **only observations** `p(s,m|c)`. The
  teacher's true channels / parameters / axes / labels are **evaluator-only** — they
  *score* counterfactual validity (`B_LER=|ΔLER_teacher−ΔLER_twin|`, `B_obs=dist(Δp)`),
  never feed the learner.
- **`do()` discipline.** A knob is a **channel-level, parameterization-independent**
  transform — Tier 0 remove `E→I`; Tier 1a CPTP-safe weakening `(1−a)I+aE` (**built**);
  Tier 1b generator-scaling `exp(kL)` amplify (**deferred to GKSL**, ADR 0003) — scored
  by ΔLER under frozen `D`, **never** an edit of a teacher-native parameter (`ε`/`γ`/
  axis), which is undefined on a channel known only up to the alias.
- **Claim discipline.** Controlled, exact, small-scale until C is reached and earned. No
  Google physical-mechanism / Born-generation / CPTP-learning claim beyond the validated
  loop. Honest bands always. Numerical floor `NUMERICAL_ZERO = 1e-12` for floating floors
  only (never structural zeros).
- **Metric discipline.** Every quantitative claim is scored by a **field-standard** metric via the
  [`METRICS.md`](../METRICS.md) ladder — a ledger metric → if none fits, the frontier-standard one (then
  added to the ledger) → only if none exists, a metric explicitly flagged **project-defined**. No silent
  non-standard stand-in; each metric's convention travels with its numbers. HARDEN's new axes (coherent
  fidelity/diamond distance, leakage, drift) enter through this ladder, not by ad-hoc stand-in.

## 2. The aim↔object map (the four capabilities — STRICT)

The spec is **four capabilities over hardware-realistic noise**, each reduced to a
*falsifiable object-level criterion* — not an architecture (ADR 0005).

| Capability | Object it acts on | Falsifiable success criterion | Math tool / guardrail | Finance analogue | Status |
|---|---|---|---|---|---|
| **recover** | the field `E` | `calib_kl ≈ 0` **and** held-out `p(s,m\|c)` match | Born-NLL inverse; anchor-feature identifiability | vol-surface calibration | **DONE** (toy) |
| **understand** | learner-visible decomposition of `Ê` | a **quotient-level** split — coherent-sensitive vs stochastic directions, identifiable mechanism *families*, non-identifiable alias *classes* — **with** honest bands; teacher-mechanism alignment is evaluator-only (scoring, not a learner claim) | Girsanov split; ICP; Fisher / learnable-DOF | model-uncertainty / factor interpretation | **partial** (toy): coherent-vs-stochastic Fisher-null split demonstrated (H0/H1 exponent witness, Kraus coords); no `understand` module yet |
| **manipulate** | `do(Ê) → ΔLER` | `\|ΔLER_teacher − ΔLER_twin\|` within the reported band | counterfactual validity vs **W1** | Greeks / hedging / scenario | **DONE** (toy): Tier-0 + Tier-1 weakening; generator-scaling → GKSL |
| **predict** | `E(t)` / rare events | held-out-time / regime ΔLER forecast within band | SMC-MCMC state-space | regime / multiscale stochastic-vol | placeholder |

"Done (toy)" = validated on the exact rep-code teacher only; **not** a hardware claim. A
capability is *complete* only when its criterion holds **under HARDEN-level complexity
with honest bands**, never by in-sample fit.

## 3. Phased path with strict gates

`B (done) → HARDEN (in progress) → C (deferred)`. Uniform milestone altitude; each gate
is a (physical / mathematical / aim↔object) triple plus a falsification signal.

### B — validate the counterfactual loop · DONE (exact rep-code toy)

- **Shown.** Label-free calibration recovers a coherent over-rotation teacher
  (`calib_kl ≈ 0`); the channel-level `do()` matches the teacher's true ΔLER (knob error
  `twin_B_LER = 1.594e-5` at `r=1`, `<1e-6` on the identifiable bit-flip teacher);
  negative controls fail as pre-registered (moment-matched **≈942×**, shuffled **≈1503×**
  worse — test-pinned); probe richness breaks the alias (`B_LER` falls `2.709e-3 → 1.594e-5`,
  `r=0→1`); Tier-0 bands cover truth and shrink with richness; d3→d5 holds (band even tightens).
- **Gate (passed).** *Physical*: exact Born-NLL on the non-Clifford forward, frozen `D`.
  *Mathematical*: alias band shrinks with `r`; controls fail per the Girsanov prediction.
  *Aim↔object*: recover + manipulate criteria met on the toy.
- **Evidence (at the B gate).** 87 tests passed at this gate (B + H0/H1 + the
  decision-regret gate); this is the B-gate snapshot, not the whole-project total
  (the current count lives in CLAUDE.md / `metric_results.md`).
- **Falsification (it survived).** Had the band failed to shrink with `r` on the
  controlled teacher, interventional validity would be unrecoverable → stop/redesign.

### HARDEN — richer complexity · IN PROGRESS

**HARDEN is not "add realism until it works."** It is a sequence of controlled
**misspecification and identifiability stress tests**. Each added realism axis declares
(i) the true teacher object, (ii) the learner model class, (iii) the probe subspace
expected to shrink the relevant alias band, (iv) the negative control expected to fail,
and (v) the **failure attribution** if it does — non-identifiability, misspecification,
finite shots, or backend approximation (the three bands of §1.2 + §1.1b). The matrix
below *is* that declaration — concrete for the near-term cuts, named for the rest.

| # | Added realism | Teacher truth | Learner class | Probe requirement | Main plot | Falsification |
|---|---|---|---|---|---|---|
| **H0** | same-`r` richer baseline | no drift | matched model | fixed `C_cal(r)` | calibration + band | fit bad → numerical / model bug |
| **H1** | coherent 1Q/2Q | coherent channel | CPTP exact | phase-sensitive | band vs `r` | coherent band fails to shrink |
| **H2** | non-factorized crosstalk | two-location channel | factorized vs non-factorized | crosstalk probes | misspecification gap | factorized model overconfident |

Beyond the current cut the later axes are **named, not yet specified** — **H3 leakage**
(qutrit teacher vs qubit learner; the `B_misspec` test), **H4 drift** (the first
`predict` exercise), **H5 larger `d`** (the backend-swap test) — each specified when
reached, not before.

- **Done so far (2026-06-09).** **H0** (`test_twin_h0_baseline`): frozen matched baseline,
  `calib_KL ≈ 1e-14`, Tier-0 band covers every `do(E→I)` knob; the coherent alias is a real
  `r=1` Fisher null (iso-marginal exponent `∝h⁴`) that does **not** project onto `do(E→I)`.
  **H1** (`test_twin_h1_coherent`): the null lifts (exponent `4→2`) at the accumulation rung;
  one Ê gives the right `do(E→I)` but the wrong phase-sensitive prediction (Pauli-shadow tie
  ≈1.07); the null is backdrop-dependent (observation-map, factorized teacher) → motivates H2.
  **H2** (`test_twin_h2_crosstalk`, 6/6): theory-first pre-registration (three exact theorems —
  repeats=1 contexts are *exactly* φ-blind; the edge twirl has no DEM column; Z-basis contexts
  are exactly even in φ) verified end-to-end; the fork is **rung-indexed (b)→(a)** (fit silent
  at r≤1 by theorem, 12%-leaky at r=2–3, surfaces ×622 at r=4); `B_misspec` is real and
  **functional-indexed** (zero on repeats=1 functionals, φ² + band-uncovered on sandwich
  functionals, φ-linear on k2ry; the ZZ edge is *echo-protective* — removing it raises LER);
  **probe richness does not close the third band; one declared edge DOF does** → ADR 0006
  support-structure verdict: edge slots (b) REQUIRED for φ-sensitive functionals. **R2-lite M1**
  (`test_hardware_m1_ingestion`, ADR 0007 Track B): first real-hardware contact — bit-exact m2d
  parity on the Google d=29 release, detection fractions in the derived band (X 5.13% / Z 5.00%),
  and three back-edge findings (a device mirror-diagonal class ≈970× the SI1000 sim, long-range
  tails, an early-layer transient). Numbers in [`metric_results.md`](../metric_results.md).
  *(M1 is the frozen horizon of this bullet, not the present frontier: the live R2-lite
  frontier — M2 window closure, M3 syndrome-NLL, M4 decoder-prior utility, the CF-WR
  window-covering work, and the ADR 0008 carrier study — is tracked in CLAUDE.md and
  `metric_results.md`.)*
- **Decision-regret gate** (plan2 go/no-go, `test_decision_regret_gate`). Ran before H2 to
  decide whether to commit to the [`plan2.md`](plan2.md) prioritization engine. **Verdict: bank
  the Claim-A floor** — non-Pauli-capable calibration beats the field's Pauli/DEM standard on a
  dissipative source (the gap projects onto the decision) — and **defer plan2's engine**: its
  calibrated decision band is real but **not cheaply computable** (no slack calibrates a local
  band on the toy; earning it needs global continuation machinery). The bounded plan here is the
  committed path; the non-Pauli floor is its banked headline.
- **Sequencing.** Non-linear: **H0 freezes first** (the same-`r` baseline) before the
  predict-held-out-`r` step; the coherent half is co-built with it; the epistemic and
  statistical bands are coupled through the `slack` knob. Dependency structure: **ADR
  0004 (D1–D5)**. **H0/H1/H2 done** (above; H2's misspecification ablation delivers the
  ADR 0006 support-structure verdict, which **unblocks the `forward/scalable` carrier
  feasibility study** — ADR 0007 Decision 3 → ADR 0008). *Current cut:* the carrier study ∥
  **R2-lite M2** (window-closure audit — the back-edge findings predict where closure fails);
  **H3 (leakage) / H4 (drift)** are sequenced by the R2-lite residual directions per the
  back-edge, not built blind.
- **Gate (per row, triple).** *Physical*: the mechanism declared at its true realism
  level (qutrit leakage / non-factorized crosstalk), no silent Pauli approximation.
  *Mathematical*: the **prediction-error-vs-`k`** curve and the **split bands vs `r`**
  behave as the W2/Girsanov gating *predicts in advance*. *Aim↔object*: recover +
  manipulate still hold with covering bands; understand emits the quotient-level split;
  predict forecasts within band. Thresholds are **predeclared and relative** (set before
  each run, not after).
- **Falsification.** If the coherent-slice prediction error / band does **not** improve
  with the phase-sensitive probes the gating predicts — realistic complexity breaks the
  loop even on a controlled teacher — that is a **stop/redesign signal before any C
  work**.

### C — real Google 72Q/105Q · DEFERRED

- **Entry.** Only after the HARDEN gate passes.
- **Hard boundary (W1 + ADR 0004).** Real hardware has **no realized, mechanism-isolated
  counterfactual**, so calibration fit can **never** validate a `do()` knob there. (Some
  interventions *are* physically realizable — recalibrate a gate, change a pulse — but they
  are **non-surgical** (they move coherent + stochastic + crosstalk together), are **not** the
  channel-level `do(E→I)`, and stay **aliased** (W1) — so none can be tied to the twin's
  per-source prediction.) The only available validation is **cross-config transfer**
  (d3→d5/d7, X↔Z, set1→set2, 72→105Q) = calibrate-on-liquid / test-on-illiquid — exactly where
  finance flags well-fitting models still fail. This is **transfer / scenario-prediction
  validation, not realized-`do()` validation**.
- **Headline & claim.** Report **cross-config transfer (scenario-prediction) error** —
  observed `p(s,m)`, LER, and scenario-shift direction on the held-out config — **plus
  the inherited controlled-system alias band** as a prior on every Google knob; *not* a
  "counterfactual transfer error," since no hardware `do()` ground truth exists. **The
  band-as-prior is family-conditional:** its covering guarantee transfers **only inside the
  calibrated misspecification family**; if the hardware lands *outside* it (`B_misspec`,
  out-of-class), the band is only a **transfer bound**, not a covering prior, and that
  triggers the **R-ladder back-edge** (return to R1, widen the family along the exposed
  direction, re-gate). The claim stays bounded — no hardware physical-mechanism /
  Born-generation / CPTP-learning claim is licensed by fit alone.

## 4. What stays open (FLEXIBLE — selected later, against the four capabilities)

Per ADR 0005 the main-line architecture is *deliberately undecided*. Open knobs, chosen
later with **the four capabilities as the primary criteria and scalability as one
criterion among others**:

- **Main-line parameterization** — per-location CPTP field vs factor/orbit vs
  DEM-bulk + coherent-corrections. (If parameter sharing is ever used for scale, it is
  declared an approximation and audited by the misspecification band — never sold as free
  identifiability.)
- **Scalable carrier** — `forward/scalable` (>50q). The swap is gated to *after HARDEN*;
  the channel object + the four capabilities are backend-agnostic, so the swap is a
  backend replacement, not a rewrite — but it must first **prove `do()`-preservation** on
  overlapping exact instances (base `p(s,m)`, `do(E→I)` ΔLER, and band width match the
  exact backend) before C.
- **Amortized context map** `f_ψ(c)` — not committed now (TWIN.md).
- **Optimizer / numerics / code organization** — implementation detail.

## 5. Cross-references

- [`docs/TWIN.md`](../TWIN.md) — object contract `p(y|c)=Tr[M_y C(c)(ρ0)]`, the four
  capabilities, reserved notation.
- [`docs/plan2.md`](plan2.md) — the decision-regret / prioritization-engine extension of this
  plan, **gated** by `tests/test_decision_regret_gate.py` (verdict: Claim-A floor banked, the
  calibrated-band engine deferred — see §3 HARDEN).
- [`docs/METRICS.md`](../METRICS.md) — the metric ledger and the **forced standard-metric ladder**; every
  score is named with its field reference and convention (numbers, dated, in `metric_results.md`).
- [`docs/adr/`](../adr/) — 0002 (build order) · 0003 (B methodology) · 0004 (finance
  framing, D1–D5 + bands) · 0005 (retire SCOPE, architecture open) · 0006 (channel-field
  architecture: ratify object, scope support structure, defer carrier) · 0007 (R2-lite
  published-data rung now, in parallel with H2; d=5/d=7 surface-code target → carrier
  feasibility study after H2; hardware-data metric ledger) · 0008 (scalable-carrier
  feasibility-study charter: the d=5/d=7 carrier decision question, candidates, and
  seam-test process).
- [`docs/IDENTIFIABILITY_AND_CRL_SURVEY.md`](../IDENTIFIABILITY_AND_CRL_SURVEY.md) —
  finance ↔ QEC tools and the W1–W5 guardrails.
- [`docs/error_mechanisms.md`](../error_mechanisms.md) — physical mechanism taxonomy (the
  HARDEN richness axis).
- [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md) — module map and the backend boundary.
