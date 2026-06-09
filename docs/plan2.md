# The Twin — Project Plan

Binding roadmap for **the twin** (`qec_twin`). Division of labor:
[`docs/TWIN.md`](TWIN.md) is the **object contract** (*what* the twin is); the
[ADR spine](adr/) (0002→0006) records **decisions** (*why*); this file is the **path**
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
- **Headline object — decision regret, not parameter recovery.** Identifiability is
  reported on the **decision functional**: the headline band is worst-case `ΔLER` over the
  calibration-consistent set `{E : NLL ≤ NLL_min + slack}`, and channel corank /
  Born-map-Fisher spectrum is its **diagnostic**, not the claim. The **directional** half of
  *"an alias matters iff it projects onto `do()→ΔLER`"* is **supported** (H0 + the Go/No-Go
  gate): the coherent alias has zero projection onto `do(E→I)` (carries no regret) and nonzero
  projection onto a phase-sensitive functional (carries it) — the projection ranks, not corank.
  That linear pushforward is **coordinate-invariant** and is exactly
  `audit/bands.tier0_alias_band`'s `gᵀH⁺g` (no separate GKSL module needed). The **magnitude**
  half — the exact band over the alias set — is the **open bet, NOT computed**:
  `tests/test_decision_regret_gate.py` found that *no* slack calibrates a local / named-member
  band even on the toy (overconfident at the real alias, vacuous elsewhere), because the MLE
  point and truth both sit at `NLL_min` yet are far apart in `ΔLER` and local ascent cannot
  traverse the curved identified set between them. Earning it needs the **deferred global
  continuation maximization** (§3) — already at the toy, not only at scale. What *is* banked is
  **Claim A**: non-Pauli (dissipative) representation that beats the field's Pauli/DEM standard
  on a decision-projecting gap (the floored downside).
- **Report bands, not points — and split them (three layers).** Over the
  calibration-consistent set `{E : NLL(E) ≤ NLL_min + slack}`: the **epistemic alias
  band** = range of `ΔLER` over that model set (Cont/UVM); the **statistical estimation
  band** = `ΔLER` spread under bootstrap of finite shots (the `1/√N` scale). Under
  HARDEN's misspecification axes a **third, model-class band** appears — `B_misspec`, the
  `ΔLER` deviation when the teacher's true object lies *outside* the learner's class
  (qutrit leakage vs qubit learner; non-factorized crosstalk vs factorized learner).
  Report the three **separately, never summed** (not independent; LER is **non-monotone**
  — coherent interference + decoder non-monotonicity — so the UVM pointwise shortcut
  fails, extremize **numerically**). `B_misspec` is measurable only against the
  controlled teacher; on hardware it is only *bounded* via transfer. The misspecification **family** it is
  calibrated across — which mechanisms, what ranges, what is held fixed — is a **first-class
  written artifact**, not an implicit Stim config; it is the reference set the C-phase
  transfer measures real data *against*, so without it "is hardware representative" has no
  scored answer. **Band width vs `r`**
  is the single most important plot.
- **Hard theoretical guardrails** (survey W1–W5,
  [`IDENTIFIABILITY_AND_CRL_SURVEY.md`](IDENTIFIABILITY_AND_CRL_SURVEY.md)):
  - **W1** counterfactual non-identifiability — observational ≠ interventional
    equivalence; a knob is validated only against realized ground truth.
  - **W2** learnable-degrees-of-freedom ceiling — the observation map has finite
    learnable DOF; directions outside it carry an honest nonzero band, *not* a recovered
    point. The **diagnostic** for the decision-regret headline band — promoted to the headline
    itself only once **pushed forward onto `do()→ΔLER`** (a projection **not yet computed**;
    the immediate next step, §3) — is the rank/spectrum of the **Born-map Fisher
    information** `I(θ)=E[∂_θ log p·∂_θ log pᵀ]`; the DEM parity map `A` is the cheap
    **Pauli-linearized proxy for its stochastic sector only** — anchor/Moran on `A` gates
    the stochastic (Girsanov quadratic-variation) directions and is **blind to the
    coherent/drift directions** (W5), which live in the full Fisher and are earned by
    phase-sensitive probes. Gate with anchor/Moran + the DOF ceiling on `A` *before*
    measuring the curve — necessary, but partial. The **coherent sector** is **demonstrated
    identifiable** by the H0/H1 Fisher-null exponent: the iso-marginal coherence direction is a
    2nd-order NLL null at low `r` (`∝h⁴`) that lifts to ordinary curvature (`∝h²`) once
    phase-sensitive (accumulation) probes enter — measured in **Kraus** coordinates (the Born-map
    Fisher is **coordinate-invariant**, so no GKSL `(h,a)` module is required). A per-direction
    identification-order `k` and the **PSD-cone-as-a-probe** remain **hypotheses, not built**
    (there is no `audit/fisher_ceiling.py`; METRICS.md flags the cone outputs "not assumed true").
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
- **Decoder-sensitivity of the attribution (companion output).** Per source report the
  **pair**: frozen-decoder `ΔLER` vs **twin-configured-decoder** `ΔLER` (the attribution's
  decoder-dependence — large ⇒ do not act on the naive ranking), and twin-configured vs
  **per-channel-optimal** (the twin's own inadequacy reaching the decoder). Named
  **separately** — at R2 (no true channel) the optimal leg is twin-relative, hence a **lower
  bound** on inadequacy. Adaptive decoder pinned as twin-configured, ceiling'd by optimal.
- **Claim discipline.** Controlled, exact, small-scale until C is reached and earned. No
  Google physical-mechanism / Born-generation / CPTP-learning claim beyond the validated
  loop. Honest bands always. Numerical floor `NUMERICAL_ZERO = 1e-12` for floating floors
  only (never structural zeros).

## 2. The aim↔object map (the four capabilities — STRICT)

The spec is **four capabilities over hardware-realistic noise**, each reduced to a
*falsifiable object-level criterion* — not an architecture (ADR 0005).

Composed, the four capabilities are a **counterfactual prioritization engine**: *which error
source, if improved, most reduces LER — and with what confidence.* The `do()→ΔLER` knob is the
spine; the identifiability machinery (§1.2) is its uncertainty quantification; the
differentiation over a fitted noise model is the **counterfactual + the calibrated band**, not
the fit. The composition itself — a *ranking across sources* — is **not yet a capability**:
today every `do()` is scored one source at a time, and the row that would compose them is the
**decision-regret gate** (§3), still behind its dependencies.

| Capability | Object it acts on | Falsifiable success criterion | Math tool / guardrail | Finance analogue | Status |
|---|---|---|---|---|---|
| **recover** | the field `E` | `calib_kl ≈ 0` **and** held-out `p(s,m\|c)` match | Born-NLL inverse; anchor-feature identifiability | vol-surface calibration | **DONE** (toy) |
| **understand** | learner-visible decomposition of `Ê` | a **quotient-level** split — coherent-sensitive vs stochastic directions, identifiable mechanism *families*, non-identifiable alias *classes* — **with** honest bands; teacher-mechanism alignment is evaluator-only (scoring, not a learner claim) | Girsanov split; ICP; Fisher / learnable-DOF | model-uncertainty / factor interpretation | **partial** (toy): the coherent-vs-stochastic **Fisher-null split is demonstrated** (H0/H1 exponent witness, Kraus coords) — but there is **no `understand` module** and no GKSL/cone machinery (unbuilt) |
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
  (`calib_kl ≈ 0`); the channel-level `do()` matches the teacher's true ΔLER (≈6e-9);
  negative controls fail as pre-registered (moment-matched ≈900×, shuffled ≈1400×
  worse); probe richness breaks the alias (out-of-basis exotic error collapses ~10⁵×
  once basis-rotated probes enter); Tier-0 bands cover truth and shrink with richness;
  d3→d5 holds (band even tightens).
- **Gate (passed).** *Physical*: exact Born-NLL on the non-Clifford forward, frozen `D`.
  *Mathematical*: alias band shrinks with `r`; controls fail per the Girsanov prediction.
  *Aim↔object*: recover + manipulate criteria met on the toy.
- **Evidence.** 63 tests pass.
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

**Validation altitude — raise the rung, keep it a rung.** Each axis pushes the teacher
*outside* the learner's class but stays in simulation with ground truth retained (H2
non-factorized, H3 qutrit) — realism rises while the answer key, and with it the evidential
tiers, survive. Realism is never bought by trading the certificate for ungraded noise; the
rung moves up, it does not dissolve.

| # | Added realism | Teacher truth | Learner class | Probe requirement | Main plot | Falsification |
|---|---|---|---|---|---|---|
| **H0** | same-`r` richer baseline | no drift | matched model | fixed `C_cal(r)` | calibration + band | fit bad → numerical / model bug |
| **H1** | coherent 1Q/2Q | coherent channel | CPTP exact | phase-sensitive | band vs `r` | coherent band fails to shrink |
| **H2** | non-factorized crosstalk | two-location channel | factorized vs non-factorized | crosstalk probes | misspecification gap | factorized model overconfident |
| **H3** | leakage `\|1>→\|2>` | qutrit leaky channel | qubit `d=2` vs qutrit | `r ≤ 2` (no RY) | `calib_KL` & `B_LER` vs `γ` | both flat → leakage harmless |
| **H4** | parameter drift | rate drift / period | qubit, per-period | periods × `C_cal` | forecast ΔLER vs band | smooth drift escapes band |

`H5 larger d` (the backend-swap test) remains **named, not yet specified** — specified
when reached, not before.

- **Sequencing.** Non-linear: **H0 freezes first** (the same-`r` baseline) before the
  predict-held-out-`r` step; the coherent half is co-built with it; the epistemic and
  statistical bands are coupled through the `slack` knob. Dependency structure: **ADR
  0004 (D1–D5)**. **H1 — DONE** (`tests/test_twin_h1_coherent.py`): the coherent
  hidden-failure axis — the Fisher null lifts (exponent `4→2`) at the accumulation rung; the
  same low-`r` Ê gives the right `do(E→I)` but the wrong phase-sensitive prediction (Pauli-shadow
  tie ≈1.07); loc0's null is **backdrop-dependent** (geometric / observation-map, resolved only
  by a coherent backdrop) → motivates H2. **H2 (coherent ZZ crosstalk) — PRE-REGISTERED, not
  built** (`tests/test_twin_h2_crosstalk.py`, skip-marked stubs): non-factorized *generator* vs
  factorized learner, targeting `B_misspec`. **H3 (leakage) and H4 (drift) — NAMED, not built**
  (no `forward/exact/leakage`, no `prediction/drift`, no run): H3 = a `dim=3` leaky teacher vs the
  `dim=2` learner (the out-of-class `B_misspec` case — the *predicted* finding is that leakage is a
  **detectable** misspecification, `calib_KL` *and* `B_LER` rising with `γ`, to be tested); H4 =
  the first `predict` cut. *Next:* the Go/No-Go gate already ran (below); then H2, then the H5
  backend-swap.
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

#### HARDEN gate review — consolidate the taxonomy before H5/C

**⚠ Pre-registration, not a result.** Only **H1 is built**; **H2/H3/H4 are not** (see the
sequencing bullet above). This review is the *planned* consolidation into one taxonomy — recast
the failure map as a 2×2, check each axis against its W2/Girsanov *pre*-prediction, and clear two
open gates — but the **H2/H3 rows below are predicted, not observed**, and the taxonomy is
**aspirational** until those axes are built and both gates pass. Only the H1 entries are run.

**Failure-mode map (2×2 — the dangerous cell is unique).**

| | `B_LER` low (knob right) | `B_LER` high (knob wrong) |
|---|---|---|
| **`calib_KL` ≈ 0** | benign / well-specified (H0) | **DANGEROUS — hidden failure (H1 coherent).** Fit is silent; only phase-sensitive probe richness catches it |
| **`calib_KL` high** | **should be empty** — if occupied, `calib_KL` is a *false alarm* on that axis (residual never reaches the knob); flag + investigate | self-exposing (H2 crosstalk; H3 leakage — *provisional*, Gate A) |

`calib_KL` is a **necessary-not-sufficient** alarm: it lights the self-exposing cells and
is blind to the dangerous one. The entire probe-richness program exists for the single
cell `calib_KL` cannot see.

**Predict-before-measure cross-check (each axis vs its structural prediction).**

| Axis / direction | Structural predictor | Predicted → observed |
|---|---|---|
| H1 coherent `Z⊗Z` | Girsanov drift; W5 | alias-invisible to 2nd order → lifts only at phase-sensitive `r≥3` (RY) → lifts at `r3`, `calib_KL≈0` (hidden) ✓ |
| H1 coherent `X⊗Z` | bit-value-conditioned rotation | sign→population needs coherent *accumulation* → lifts at `r=2` (repeats) + data1 variance, **earlier** than the RY gate → per-direction drop-level: `r2` for `X⊗Z`, `r3` for `Z⊗Z` → the hard `drop==3` assertion is **`Z⊗Z`-only** |
| stochastic `X⊗Z` | sector-aware Girsanov (W2: `A` = stochastic-sector proxy only) | `Z`-leg lives in the code's **blind (Z) sector** → permanent structural null **and** knob-irrelevant on the rep-code (`B_misspec≈0`) → recoverable + consequential only under X-stabilizer codes (C); this is the precise reading of the §3 "collinear alias" line |
| H2 crosstalk | W2 DOF gate on `A` | 2-body direction in the learnable subspace, factorized learner cannot absorb it → factorized blind/wrong → explicit edge structure (ADR 0006) — **predicted; H2 not built** |
| H3 leakage | model-class band `B_misspec`; `\|2>` outside the qubit class | syndrome-less logical errors → `calib_KL` **and** `B_LER` rise with `γ` → **predicted** self-exposing, **learner-relative** (Gate A) — **H3 not built** |

Cross-cutting refinement (the diagonal-vs-phase / sector correction, ADR 0006 + §1.2 W2):
**identifiability = (coherent vs stochastic) × (code-sector visibility)**. The naive
Girsanov "stochastic = 2nd-order identifiable" **fails in the code's blind sector** — the
stochastic `X⊗Z` null is the witness — so the DEM parity map `A` gates only the *visible*
stochastic sector.

**Open Gate A — leakage re-hiding (the H3 row is learner-relative).** "H3 self-exposing"
holds only against the *minimal* qubit learner (no readout-error DOF). Leakage's
syndrome-less-flip signature is observationally close to **readout error**, so an
expressive learner (per-location CPTP + readout-error params) can shadow much of it — a
readout↔leakage alias, i.e. an **H1-style hidden alias nested inside H3**. *Pre-registered
prediction:* adding a readout-error DOF **drops `calib_KL` but it floors** (irreducible
residual in the final-data-derived syndrome and in cross-round temporal correlation, which
i.i.d. readout error cannot mimic) **while `B_LER` worsens** (`do()` on readout-error ≠
`do()` on leakage). Re-hiding fingerprint = `B_LER` rising as `calib_KL` falls → then amend
the H3 row to "self-exposing only against a readout-blind learner; partially re-hides with
realistic readout params; residual in temporal correlation," and H3 slides toward the
dangerous cell. *Test:* fixed rounds, sweep `γ`, two learners (readout-blind vs
readout-augmented), compare `(calib_KL, B_LER)` trajectories.

**Open Gate B — drift band coverage (PREDICT not yet earned).** H4's "band has teeth"
rests on one smooth + one regime-change case, a smooth-*linear* teacher fit by *linear*
OLS (near-tautological), and a discontinuity escape that is trivially true. Two
requirements before `predict` is banked: (i) **empirical coverage** — many trajectories
incl. mildly-curving / heteroscedastic / autocorrelated-innovation drift, coverage
frequency vs nominal PI; a calibrated band must *accept* predictable variation and *reject*
the unpredictable, not merely reject jumps; (ii) **band propagation (§1.2)** — the OLS PI
treats per-cycle `ΔLER` estimates as noise-free, so the per-cycle finite-shot estimation
band must propagate into the forecast (errors-in-variables / weighted regression) or the
band is systematically too narrow. Until both, `predict` is **first-cut, not complete**
(§2).

**Exit (taxonomy banked; H5/C unblocked) when:** the 2×2 `(high-KL, low-B_LER)` cell is
confirmed empty; every axis matches its W2/Girsanov pre-prediction; Gate A settles the
leakage row's robustness; Gate B delivers calibrated drift coverage. Until then H5 (scale)
and H3b (seepage) would build on a provisional organizing claim — **defer**.

#### Decision-regret gate — the composed ranking (a *separate* claim from the taxonomy)

The gate-review Exit above is the **taxonomy gate** (per-axis: each mechanism in its right 2×2
cell, each axis matching its W2/Girsanov pre-prediction). **Ranking calibration is a different
claim and gets its own named gate** — the two pass and fail *independently*: a taxonomy can be
per-axis-correct while the *cross-source* ranking inverts (the frozen-vs-deployment-decoder
reason, §1.3 divergence pair). Ordered **behind** the taxonomy gate (you cannot rank sources
not yet correctly classified), the decision-regret gate — calibrate on `R_cal`, predict on
held-out `R_test` — passes iff: (1) **ranking** — the engine's prioritization of error sources
by `ΔLER`-reduction matches truth (top-k / rank-corr), not parameter coverage; (2) **steelman**
— it beats both the in-class GKSL point estimate (**load-bearing**: the strongest in-family
competitor) and twirl + a competent correlated-noise correction; (3) **calibrated catching,
two-sided** — the band covers the realized miss where the steelman is confidently wrong,
*while* its width on the easy (steelman-correct) cases tracks **that same in-class estimate's
posterior spread** — tightness as **ratio-to-achievable, never a hand-set constant** (crit-3's
yardstick *is* crit-2's tier).

**This gate is not yet runnable — state the dependency, don't hide it.** It sits behind
**Gate B**: ranking-on-held-out needs `predict`, which §2 marks placeholder and Gate B marks
*not yet earned*; until Gate B's errors-in-variables band propagation lands, the OLS forecast
band is "systematically too narrow" (Gate B's own words) and the ranking confidence **inherits
that narrowness** directly. And its precondition object — the **pushforward of the W2 Fisher
onto `do()→ΔLER`** (§1.2) — is **not yet computed**.

**Decision-regret bridge — directional half supported, magnitude half is the open bet.** The
**directional** filter is **supported** by H0 + the Go/No-Go gate (`tests/test_decision_regret_gate.py`):
the coherent alias's zero projection onto `do(E→I)` carries no regret, its nonzero projection onto a
phase-sensitive functional carries it — the projection ranks, not corank. The linear pushforward is
coordinate-invariant (= `tier0_alias_band`'s `gᵀH⁺g`; there is no `fisher_ceiling.decision_pushforward`
module). The **finite-displacement / magnitude** half is **NOT computed**: the gate found that **no slack
calibrates a local / named-member band on the toy** — overconfident at the real alias (never covers, even
40× slack), vacuous where there is none — because the MLE point and truth both sit at `NLL_min` yet are
far apart in `ΔLER`, and local ascent cannot traverse the curved identified set between them. So "the
named alias member *is* the band" is **false already at the toy**, not only at scale; earning slope≈1
needs the **deferred projected-ascent/continuation maximization**, not a named-member evaluation (and
there is no `finite_displacement_regret` / `test_audit_decision_pushforward`). **What is banked: Claim A**
— non-Pauli-capable calibration beats the field's Pauli/DEM standard on a decision-projecting gap (the
floored downside). The full decision-regret gate also still waits on `predict` (Gate B).

#### Rungs to C — trigger-gated, with a way back down

Validation climbs by **fireable triggers, not dates**: **R0** controlled well-specified (B,
done) → **R1** controlled misspecification (HARDEN; **H1 built; H2/H3/H4 pending** — taxonomy + decision-regret
gates pending) → **R2** first hardware-*adjacent* claim (the decision-regret protocol on a
**published** dataset — Google surface/rep-code releases; no `do()` ⇒ prediction-calibration
only, **no** miss-attribution) → **R3 = C** (live `do()`, the only field-checkable
counterfactual). Each entered only when the prior's gate fires. **Back-edge (load-bearing):**
if R2 lands the data *outside* the R1 family (§1.2), that is not a failure but R2's most
valuable output — **return to R1, widen the family *along the direction R2 exposed*, re-gate.**
A ladder that can only climb will climb past its own family-conditioning; the down-rung is what
keeps "calibrated across this family" from silently becoming "calibrated."

### C — real Google 72Q/105Q · DEFERRED

- **Entry.** Only after the HARDEN **taxonomy** and **decision-regret** gates pass **and** the
  **R2** hardware-adjacent gate (above). C is **R3** — never entered directly from R1.
- **Hard boundary (W1 + ADR 0004).** Real hardware has **no realized counterfactual**, so
  calibration fit can **never** validate a knob there. The only available validation is
  **cross-config transfer** (d3→d5/d7, X↔Z, set1→set2, 72→105Q) = calibrate-on-liquid /
  test-on-illiquid — exactly where finance flags well-fitting models still fail. This is
  **transfer / scenario-prediction validation, not realized-`do()` validation**.
- **Headline & claim.** Report **cross-config transfer (scenario-prediction) error** —
  observed `p(s,m)`, LER, and scenario-shift direction on the held-out config — **plus
  the inherited controlled-system alias band** as a prior on every Google knob; *not* a
  "counterfactual transfer error," since no hardware `do()` ground truth exists. The
  claim stays bounded — no hardware physical-mechanism / Born-generation / CPTP-learning
  claim is licensed by fit alone.

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

- [`docs/TWIN.md`](TWIN.md) — object contract `p(y|c)=Tr[M_y C(c)(ρ0)]`, the four
  capabilities, reserved notation.
- [`docs/adr/`](adr/) — 0002 (build order) · 0003 (B methodology) · 0004 (finance
  framing, D1–D5 + bands) · 0005 (retire SCOPE, architecture open) · 0006 (channel-field
  architecture: ratify object, scope support structure, defer carrier).
- [`docs/IDENTIFIABILITY_AND_CRL_SURVEY.md`](IDENTIFIABILITY_AND_CRL_SURVEY.md) —
  finance ↔ QEC tools and the W1–W5 guardrails.
- [`docs/error_mechanisms.md`](error_mechanisms.md) — physical mechanism taxonomy (the
  HARDEN richness axis).
- [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — module map and the backend boundary.