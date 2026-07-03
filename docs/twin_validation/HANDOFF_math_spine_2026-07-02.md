# HANDOFF — math spine (post-ratification), 2026-07-02 (session close)

**For the next session. Self-contained: read this + `CLAUDE.md` + memory index; everything else is
linked. SUPERSEDES `HANDOFF_coupling_simulator_2026-07-02.md` §5 (its bones are adjudicated and the
work order below is user-ratified 2026-07-02); that file's §1–§4/§6 remain valid background.**

## 0. Mission (user-ratified 2026-07-02)

Paper = the coupling error simulator (SIMULATOR, not decoder — A8). **Math spine = #2 + #3 + B.**
**Ratified work order: B theorem → #2 functional → #3 recovery identities → M3 prereg+run —
with T-L2 (the non-unital classical imitator definition, zero-compute derivation) running IN
PARALLEL from day one.** Identity sentence (proposed, consistent with adjudication):
characterize the mathematical structure of the coupling simulator's observable record —
identifiability theorem (B) + exact closed-form functionals (#2) + recovery-machinery
identifiability constraints (#3). Real hardware data enters ONLY as a simulator validation
target (does the simulator produce records matching the device?), not as a direct estimation
substrate in the current phase. Estimator demonstration on real data is a downstream milestone
gated by simulator validation.

## 1. Where everything is

| Asset | Path |
|---|---|
| THIS handoff (current) | `docs/twin_validation/HANDOFF_math_spine_2026-07-02.md` |
| Previous handoff (background §1–§4/§6) | `docs/twin_validation/HANDOFF_coupling_simulator_2026-07-02.md` |
| Novelty-ownership adjudication (5 bones + corrections + negative-coverage log) | `docs/twin_validation/novelty_ownership_adjudication_2026-07-02.md` |
| State-confirmation audit (AGREE/DISAGREE + T3 violations + Q1–Q4 + M3 readiness) | `docs/twin_validation/post_adjudication_state_confirmation_2026-07-02.md` |
| Quantum-bath M1 prereg + A-M2-1/2/3 amendments | `docs/twin_validation/quantum_bath_slot_prereg.md` |
| CGF probe prereg + results §8 + A-P1 §9 + reading-debt §9.1 | `docs/twin_validation/cgf_probe_prereg.md` |
| Constitution (A1–A9) | `docs/twin_validation/B_syndrome_shot_bridge_prereg.md` §8 |
| Metric ledger (D_Choi / D_comb / BLP / RHP rows) | `docs/METRICS.md` |
| Paper draft (Thesis + Contributions now Branch-B; header = epistemic ledger; GITIGNORED) | `docs/coupling_simulator_intro_draft.tex` |
| Structure lemma (proved, in-draft) | tex `\label{sec:structure-lemma}` |
| M2 v3 dual-arm script + log + npz | `outputs/quantum_bath_m2_dual_arm.py`, `outputs/logs/quantum_bath_m2_dual_arm_v3.log`, `outputs/_m2_quantum_bath_dual_arm_v3.npz` |
| Un-led M2 review artifacts (reviewer's own scripts) | `outputs/review_m2_classical_match.py`, `outputs/review_m2_rate_fix.py` |
| CGF probe script + log + npz | `outputs/cgf_probe_v1.py`, `outputs/logs/cgf_probe_v1.log`, `outputs/_cgf_probe_v1.npz` |
| Tier-0 comb machinery (the lemma's numerical anchor) | `outputs/step4_v2b_tier0_comb_distance.py` |
| Silent-flip scissors (=#2's measured instance) | `outputs/step4_v2b_tier1_silent_flips.py` |
| Reading notes (incl. this round's 14: A-P1 5 + adjudication 9) | `docs/papers/reading_notes/` |
| Real Google data (for #3 demo) | `QEC_TWIN_HW_DATA=/home/cx/Document`; ingestion `src/qec_twin/hardware/`; dataset notes `docs/.datasets/` |
| Session commits (this arc) | bc3b605, c7d8b48, a54304f, 2a12243, 1390674, c7abebd, 52ad01a, a7038a2, 4efc4b7, 4076afb, 8927b66 |

## 2. Evidence state (all committed-script printed numbers)

- **M1**: quantum slot = T1 sub-share of data-idle row, s_T1 ∈ [0.25, 0.67] rep 0.4 (⇒ ~5–13% of
  budget); (a)-floor: DD does not refocus T1. TLS brackets from Gao.
- **M2 v3 (un-led-review-cleared; run-2's ¼-power BLOCKER fixed via A-M2-3, reviewer's numbers
  reproduced to 5 decimals):** engine 7.2e-16 (JC closed form) / 5.0e-5 (full-line unitary oracle)
  / KMS 3.3e-16; G-Q3-rate 0.9983; **D_matched: resonant 0.43364(21) = ×1.51 floor; dispersive
  0.07064(11) = ×11 floor, φ_opt = 0.053; D_class brackets: detuned [0.00632, 0.00734], resonant
  [0.2866, 0.4165]**; γ/2 floor exactly saturated at the Markov point (4.829466e-3, dev 0.0).
- **CGF probe (branch decider; internals, cite-don't-claim per A-P1):** Δ_base = 1.9166e-2(2.7e-5);
  asymmetry sweep Δ/Δ_base = 1 / 0.732 / 0.291 / 0.084 / 0.013 at A = 1/0.833/0.5/0.2/0.048
  (local exponents 1.71/1.80/1.35/1.31 — constant power REJECTED, pure A+A² also rejected);
  Δ_term = 0.1718 (theorem-forced survival — different protocol, NEVER the in-protocol floor);
  power ladder local slopes 3.90/3.74/3.19 (no g² visible down to g₀/4); P4: −4.06e-2 (q) vs
  +3.30e-3 (cl). Gates: GPU-RK4 cross-val 1.67e-15; rate gate 1.0013 (directional 2.0026 vs 2.0 =
  registered physics); c64-search/c128-report gap 1.9e-7.
- **Adjudication verdicts [PROVISIONAL]:** A = PARTIALLY OWNED (methodology sliver survives);
  C = OPEN-narrow (signed-p_ij reframe); B = PARTIALLY OWNED (continuous-Σ × passive-moments
  unowned); #2 = OPEN (interpolant + ∂/∂f); #3 = OPEN (PSD-constrained × QEC-data conjunction
  empty; von Lüpke = Huber-emergent, not constrained). Independent Brave cross-check: all three
  OPEN survive. Corrections: p_ij SIGNED; 2310.12448 = Gicev–Hollenberg–Usman.
- **State-confirmation (8927b66):** D1's "theorem-vacuous" JUSTIFICATION corrected (contractivity
  gives NO comb lower bound; measured fold-attenuation ~O(10²) at g₀/4); Q1 = M2 imitator
  UNITAL-ONLY ⇒ L2 needs new definition; Q2 = P3 slope measured on TOTAL wedge, c₂-pin needs a
  channel→record transfer map; Q3 = additivity unverifiable from existing outputs (3 blockers),
  lands free in M3's L2 instrument; Q4 = needs smaller-A or L2 instrument.

## 3. THE TASKS (ratified order; specs)

**T0 — hygiene (first commit of the next session; wordings are pre-approved in the
state-confirmation doc §3):** apply V1/V8 (tex), V2/V3 (memory), A-M1-1 amendment for V4/V5
(quantum_bath_slot_prereg §4 + §5 attribution: Landau–Streater via Crow–Joynt; Budini quantified
map-level; ours = γ/2 constant (folklore-grade) + QEC instantiation); optional V6/V7 pointers.

**T-B — the identifiability/gauge theorem (headline #1).** Object: which functionals of a
continuous spacetime Gaussian covariance Σ are identifiable from which ORDER of passive detector
(syndrome-difference) moments, and which are provably gauge-invisible. Base case = the structure
lemma (single-leg marginals ↔ diag(Σ); off-diagonals enter only ≥2-detector moments). Positioning:
lift Chen 2206.06362 / Zheng 2601.22286 (discrete-Pauli learnable-vs-gauge) to continuous Σ;
Remm 2502.17722 = the discrete moment-estimator boundary; Paz-Silva/von Lüpke = active-control
prior art. ⚠ theory-first check: a Chen 2206.06362 精读 note may NOT exist in-repo (Zheng's does)
— verify; if absent, 精读 BEFORE writing B's positioning. Deliverable: theorem statement + proof
LaTeX + an (a)-exact numerical verification script against the tier-0 comb machinery.

**T-L2 (PARALLEL, zero-compute).** Define the non-unital classical rate imitator: a classical
jump/reset record-law with (γ↓, γ↑) matched to the quantum rates; derive its matching theorem
(exactly what it can/cannot match — populations yes, what of coherence-sector/record statistics);
derive the channel-floor → record-CGF transfer map (Q2's missing piece; else declare floating-c₂
+ γ/2-scaling check). These two derivations de-risk the whole M3 prereg.

**T-#2 — the exact interpolating silent-floor functional.** From the structure lemma: silent-run
probability = finite Fourier sum of Gaussian CFs for ARBITRARY Σ; derive the general closed form +
∂(floor)/∂f|₀ (the device metric). Verify: Clader endpoints (cite, never claim the moment law) +
the measured 15.9× d=3 instance (`step4_v2b_tier1`) + tier-0 comb numerics. Cite Regev 2605.03054
as nearest (i.i.d./global-only). Deliverable: LaTeX + verification script.

**T-#3 — recovery-machinery identifiability constraints (downstream; needed only AFTER simulator
validation).** PSD/Bochner-CONSTRAINED recovery of Σ from detector moments (the constraint in the
estimator, not emergent); demo on real Google detector data is a future milestone gated by
simulator validation — the current phase establishes the identifiability structure (p_Z
absorption gauge, ridge rank, R-POOL pooling correctness). Baselines: the operational estimators
(Blume-Kohout/Young p_ij, Bhardwaj, + note Takou 2606.11496 from the Brave check). A8:
estimation, NEVER decoding. Biggest piece; needs its own prereg with registered bands before any
fit is read.

**T-M3 — prereg then run (after B and #2 land; full spec = state-confirmation §5).** Musts:
imitator ladder L1/L2/L3 (L1 = fold-attenuation measurement, expected-positive (b), NOT
theorem-vacuous); L2-differencing as primary component separator *[per A-L2-1: differencing =
theorem-grounded CONTAINMENT + MEASURED additivity, and the L2 null must be KERNEL-matched]*;
g-ladder extended below g₀/4 with
MC-power planning + dual registered operating points (avoid gτ = 0.63); N̄-scan total-kill;
additivity check (free in the L2 instrument); QUANTUM unit's memoryless-null construction declared
(structure lemma does NOT cover it); theorem inventory (γ/2 channel-only, contractivity direction,
B-R collider, unraveling equivalence, pinned-χ non-separability); A-P1-READ D3 five observables
(non-unital affine term [CJ/L-S]; detailed-balance FDT [Schoelkopf/Clerk]; KCC residual [Milz];
waiting-time/Mandel-Q [Plenio-Knight]; BLP backflow [ledgered]); P4 as (b)-direction with
signed-p_ij framing; A4 effect-size registration from M2-v3 actuals + probe attenuation; full
record-distribution persistence in npz.

**Paper assembly (interleave):** figures (all results are console tables), Methodology
"pseudomode engine retained" sentence + Experiments "Honest boundaries" rewrite (per tex header
REWRITE STATUS), abstract/discussion, repro package.

## 4. Rules that bit us (cumulative; do not relearn)

- **Cite-don't-claim fence:** every claim near the five bones carries its owner citation; the
  negative-coverage log is [PROVISIONAL] positioning, never a premise. p_ij is SIGNED.
- **Observable-layer theory-first:** registered predictions/kill-criteria need their OWN
  literature pass + a check against the project's standing theorems (P2 contradicted our own γ/2
  floor; P4's sign was canon). Probe outputs need A9-style adjudication BEFORE claim language.
- **Anchor verdicts + oracle floors:** rerun/read a reused anchor's verdict line FIRST (pilot-3
  printed CHECK); an oracle gates an engine only after its own floor is measured vs an exact
  referee; gate revisions = documented amendments (never silent).
- **Kill-criteria vs class definitions:** the imitator class INCLUDES deterministic control —
  implement it before quoting a wedge (the Lamb-phase trap fired twice: A-M2-2, and ¼-power via
  the dropped rate gate). Rate gates compare DIRECTION-SUMMED intensity; directional ratio
  (N̄+1)/(N̄+½) is physics, not a bug.
- **No comb lower bounds from channel theorems** (contractivity direction); fold-attenuation is
  measured ~O(10²) — expected-positive (b) claims only.
- **Numerics:** GPU-RK4 stability λ_max = κ(2N̄+1)(n_max+1), λ·dt = 0.7 OK (nan at 1.79);
  c64-search/c128-report with printed gap; level-batch trees; tree cache (`outputs/_cgf_tree_cache/`,
  CACHE_VER); section timestamps; fp64-GEMM is the wall for dim-340 c128 trees (~3e15 flops) —
  Krylov expm-multiply is the contingency; zvode "Excess work" → nsteps + dense tlist; halving
  gates on the OBJECT USED (record law, weak error), per-path strong error is diagnostic.
- **Env/process:** WSL `/home/cx/miniconda3/envs/aiqec/bin/python` via `wsl -d ubuntu-f bash -lc
  '...'`; LITERAL paths (`$VAR`/`$(...)` die in the quote chain); `;` not `&&`; ONE compute job at
  a time (live desktop, 70 GB; mesolve dim ≤ 600 + printed Liouvillian budget); scripted execution
  (committed scripts, asserts, printed evidence, flush); ≥3 seeds; prereg commit BEFORE run;
  un-led review before relying on any new load-bearing result; src/qec_twin promotion commit-gated.
- **Docs in English; 精读 with verbatim short-ASCII quote verification; metric ledger only
  (RMSE ⚠ diagnostic).**

## 4.5 SESSION 2 CLOSE (2026-07-02, math-spine execution — T0/B/#2/L2 DONE + review-cleared)

**Landed (commits 1f9314b, f26802e, 72285b3, 9999ebb, 4167832, a3e03c2, 094a8fa, 92d438f,
a836a25, 1b86b5d + records):**
- **T0** hygiene per §3 pre-approved wordings (A-M1-1 in quantum_bath_slot_prereg §4.1; V1/V8
  tex; V2/V3/V7 memory; V6 pointer).
- **T-B** (tex `sec:ident-gauge` + `tb_ident_gauge_theorem_record.md`): Chen 2206.06362 精读'd
  (note committed — was absent); probe calculus (deterministic support paths); re-signing gauge
  group (increment-admissible ε — STRENGTHENED after run-1 falsified a lag-1-visible sub-claim,
  A-TB-1); order-1 hypercube/cosh law (analytic quieter-scissors + O(C²) dilution mechanism);
  order-2 cosh-factorized law; window locality + order↔reach ladder; rank certificates
  (PAIR2+readout FULL 21/21; syndrome-only count-limited; PAIR1-full corank-6 with Σ-DEPENDENT
  null = [O] open). 38 checks green.
- **T-#2** (tex `sec:silent-floor` + `t2_silent_floor_record.md`): exact arbitrary-Σ CF-sum
  functional; leading law CORRECTED by machine falsification (A-T2-1) to the coherently-summed
  moment law E[(Σ_r Π_q θ)²] — interference term = new separation vs rate-based simulators
  (n=2: 1+(R+1)ρ² certified R=2/3; n=3 curve 1+6ρ²+8ρ³, endpoint 15 = 1+6+8 Clader-cited);
  METRIC THEOREM ∂F/∂f|₀ = 0 exact (gauge corollary) ⇒ honest metric = ∂²F/∂f² (6) + f³
  triangle (8). 20/20 green incl. independent MC anchors.
- **T-L2** (`l2_imitator_and_transfer_map_derivation.md`): L2a/L2b PDMP definition; Thm L2-1
  EXACT record equivalence at the Markov point; Thm L2-2 coherence inert on Z-record;
  transfer-map no-go ⇒ c₂ FLOATS + γ/2-scaling check. **⚠ AMENDED BY A-L2-1 (in-doc, binding
  for M3): matching = per-window KERNEL matching (TCL2 = interpretation; O(g⁴) confound);
  differencing = containment (theorem) + additivity (MEASURED, Q3); P4 is NOT L1-only — sign
  kills L1, magnitude is a live (b)-instrument vs L2a at N̄=0 (threshold p_M ≥ 4.4574e-2);
  [H,Π_z]=0 + classification-only-noise hypotheses stated.** §4 checklist superseded per
  A-L2-1; M3 registration must read A-L2-1, not the §4 originals.
- **Un-led review (independent agent; trail `outputs/review_tb_t2_findings.md`): (A) and (B)
  both SOUND-WITH-FIXES; all theorems independently rederived + confirmed** (reviewer supplied
  a stronger ∂F/∂f|₀ proof — adopted; proved the functional's event ≡ tier-1's measured object).
  MAJOR methodology fix applied: tb's independence claim overstated (reviewer's deliberate-bug
  run passes S1–S5, caught only by the MC anchor at z≈40) → tb docstring scope correction +
  **A-T2-2 S7 dressed-MC anchor (p_Z/p_M/p_F independently exercised): z = 0.72/0.28/1.18
  GREEN.** B + #2 are now review-cleared for M3-prereg reliance.

**T-#3 progress (2026-07-02/03; REWRITTEN 07-03 after TWO un-led review rounds — the earlier
version of this block cited the overturned v3 pass):** prereg ef99910 → v3 teacher gate
"passed" (b5f5120) → **4-way review round 2 (95a3b38) OVERTURNED the v3 reading** (undeclared
η/β split = exact rank-11/12 ridge; band-containment not accuracy; bands 2× inflated;
hardware-unlock RETRACTED) → A-T3-1 + addenda 1–2, v4 gate green (3b6d801) → **4-way review
round 3 (R5–R8)**: forward model + identifiability PROVEN (p_Z-absorption exact; rank 11/11;
xdist multi-μ moments = strongest ridge-breakers), but v4 run-3 = deterministic re-scoring
(zero fresh randomness), per-functional gate false-fails perfect estimators 20–40%/run,
addendum-2 diagnosis contradicted by its own bootstrap → **A-T3-1 addendum 3 FINAL (c6fcb50):
v5 gate = fresh seeds {37,47,57}, JOINT rank-matched Mahalanobis coverage+straw at 99.7%,
2000 draws, both intervals reported-not-gating + pileup fraction, grids/pins closed, AMENDMENT
BUDGET exhausted (v5 failure = finding + STOP).** **v5 VERDICT: GATE FAILED (66f179f) — seed 47
joint T = 46.28 > 21.85 (37/57 pass at 16.8/8.5); failing realization: w-pileup 28.3%,
kernel-sector error 6.3e-2 INVISIBLE to χ² (8.9 in-band), both interval types miss 10/18,
μ/d exact. REGISTERED FINDING (never citable as validated): boundary-pileup fragility at ~1/3
hardware-equivalent realizations. STOP honored; hardware LOCKED.**
**REDESIGN REGISTERED (R-POOL, prereg section "REDESIGN REGISTRATION R-POOL — the v6 gate",
user-ratified priority):** r-position pooling per moment class — (a)-basis = T-B bulk
stationarity (expectations exactly r-independent, V2-verified) ⇒ pure statistics upgrade,
forward model/dof unchanged; teacher R=12 with pinned per-class position counts; pooled
per-shot statistic + exact shot-level covariance; same joint-criterion FORM, FRESH seeds
{67,77,87}; bets b1 (SE shrink ≥1.8× on ℓ≤3 classes) / b2 (pileup < 5% all seeds) / b3
(coverage 3/3 + straw power); **ZERO-amendment budget — v6 failure ⇒ the registered fallback
axis (grid/parametrization redesign) under a fresh prereg.**
**v6 VERDICT (2026-07-03, run 2026-07-02T23:04 PT): ALL GATES PASS + ALL THREE BETS PASS,
zero amendments, one run one verdict (gate-record v6 section = binding).** Joint coverage
T = 5.57/4.65/6.70 ≤ 21.85; straw 712/714/793 (~25× v5 power); **w-pileup 0.0%/0.0%/0.0%**
(v5 mechanism REMOVED at pooled statistics); b1 min gain 2.08/2.07/2.07 ≥ 1.8; interval
misses 0/18 both types all seeds; worst |f_corr−truth| ≤ 7.5e-3; P1a unchanged 1e-14.
**Hardware extraction UNLOCKED.** Power content per addendum-3 item 7 (joint consistency,
NOT per-functional accuracy); V-levels stay +δz-gauge-shifted; v5 finding stands for the
single-position statistic. Ops note: run scripts through a committed bash runner —
PowerShell→wsl.exe pre-expands `$?` through an outer bash layer (exit evidence must be
captured in-log by the runner; `run_t3_teacher_validation_v6.sh` is the template).
**Hardware chain (2026-07-03, then RE-SCOPED — gate-record final section = binding):**
extraction `t3_hw_moments.py` ran and its **DUAL-ROUTE gate PASSED integer-exact** (route A ==
unmodified M1-validated pij module on 249 overlap columns, every sample; == flat-gather
arithmetic on all 634 columns; cache `outputs/_t3_moments_x00_09.npz`, 634 pooled classes,
S2 bulk profile spread 2.2–3.0% printed). The fit `t3_fit_real.py` was **TERMINATED mid-P5 by
user decision under the re-scoped mission §0** (hardware = simulator-validation target;
estimator demo = downstream, gated). Retained [PROVISIONAL] products: χ² = 716 307/dof 312
(model-class miss ~0.1% relative at 20–40σ pooled precision) + **~28/384 window blocks
PERSISTENTLY infeasible for the Gaussian-dephasing class up to n=2.5e5** (r̂ = m_same/o1² ≥ 1
feasibility theorem fails on-data) = the simulator-target characterization; w-pileup ~58%
on hardware; ⚠ P4 ran with a κ-pooled baseline instead of the pinned moment-wise inversion —
disclosed in the record, P4/P5 NOT citable. **UN-LED REVIEW 4 DONE (2026-07-03,
`outputs/review4_v6_extraction_findings.md`): A1 v6 gate = SOUND (thresholds independently
recomputed; (a)-pooling basis verified with a POWERED falsifying control; ALL-PASS stands);
A2 extraction = SOUND-WITH-FIXES (PASS valid; fixes gate RELIANCE: R4-8 MAJOR — pooled
hardware moments are layer-AVERAGES at ~40× the pooled SE, so before ANY un-parking of the
hardware fit: register a flatness criterion OR re-declare the estimand + Jensen-gap in S1;
R4-9 moment-set re-scope trail note filed; R4-10 M1-substrate dependency explicit; R4-5
pooled χ² is null-typical at 1–3, only the band's upper edge means anything; R4-7 closed
form is ≥2-check-chains only). Annotations in the gate record; v6 chain is now
review-cleared for M3 reliance.** **Next order (PRIORITY RATIFIED by user 2026-07-03:
"能把这个simulator做出来 这是第一优先级" — BUILD outranks everything). ⚠ STATE CORRECTION
(2026-07-03, repo-verified — the 2026-06-26 build contract's "NOT YET EARNED" list is
STALE): the axis1 line (src/qec_twin/simulator/, ~50 files, Jun 27–30) already built
forward/joint_lindbladian.py (G2 gate PASS, tracked docs/twin_validation/gates/
g2_jointL.json: ZZ×T2 commutator exactly 0.0 + channel 2.5e-11; DR×ZZ 1−F_e in-band),
mechanisms/{axis1_primitives,source_coupling,source_process}.py, the frontend stack
(CircuitIR/CodeSpec/XZZX compiler/Stim import/sealed SubstepSchedule/.b8 record sampling
from the exact Axis-1 record distribution), MCWF dense cert + QT/MPS restricted carriers,
and the FULL within-substep coupling cert (`axis1_coupling_status.md` A: six heterogeneous
mechanisms, from-scratch scipy GT 2.42e-15, pairwise effect-size table, ALL PASS).
**Mainline = what remains** (per `axis1_coupling_status.md` B + the
`project-coupled-cycle-teacher-build-state` memory, reviewer-adjudicated 06-30):
(1) `mechanisms/coupled_teachers.py::CoupledCycleTeacher` via Path A-corrected — inject an
optional `params_for_substep(substep)` callable into the dense emitter
(`axis1_record_evidence.py`, default None = byte-identical freeze regression); teacher owns
round-index derivation (round_index is a DEAD field — derive from barrier/measurement-key
prefixes); slice-1 coupling rides on ζ×γφ only; G0 pre-build effect-size gate (record
imprint above shot noise) + emit-returns-{det,obs}-only + compiler-seal assert + memory-ful
source; (2) record-level gates G4–G8 (gates/ has only g2); (3) the NON-MARKOVIAN memory
carrier (axis1 status B: the actual contribution, NOT built — Axis-2/Axis-3 bath-memory
source on top of source_coupling + the Phase-B joint-collapse seam). Read
`HANDOFF_coupling_simulator_2026-07-02.md` + `axis1_coupling_status.md` +
`src/qec_twin/simulator/README.md` BEFORE the old build contract. H6 commit-gate =
module-by-module with separate-lane reviewer, user confirms every src/qec_twin/ commit.
T-M3 prereg stays QUEUED (content unchanged, read A-L2-1) but yields mainline to the
build; the estimator's real-data demo stays PARKED until simulator validation.** Reviewer meta-rules standing:
straw-null power controls at target statistics; no criterion re-selection on realized data;
amendment budgets in every prereg; print pileup fraction always; χ²-in-band ≠ parameter
accuracy; pipefail on every tee'd run.

**Agent-ops lesson (this session):** heavy monolithic math-review briefs STALL general-purpose
subagents (two stalls: 55 min and ~8 min zero-tool-call reasoning loops); the working recipe =
reduced numbered scope + MANDATORY incremental scratch-file appends after every step +
time-boxes; a killed agent can be RESUMED with context intact (SendMessage) — resume beats
relaunch once reading cost is paid.

## 4.6 READING DEBT — PAID 2026-07-03 (items 1–4; item 5 awaits user input)

1. **arXiv:2511.16772 — 精读 DONE, HELD-PENDING RESOLVED.** Note:
   `docs/papers/reading_notes/montanalopez_nonmarkovian_learning_manybody_2511.16772.md`.
   All four deltas VERIFIED in text (access = designed ρ_S/W-layer/observables/time-traces,
   no mid-circuit measurement; objects = t=0 kernel Taylor data / quasistatic Σ_ab; NO
   PSD/Bochner constraint, NO gauge/unlearnability content, NO QEC content — full-text
   keyword sweeps, hits only in bibliography). **B.1 and #3.1 no-owner verdicts STAND**
   (tb record COVERAGE GAP section rewritten to RESOLVED). New duties: cite as third
   positioning corner (Chen/Zheng/Montañà-López); add to #3 baseline table (unconstrained
   comparator); Step 0.α anchor (their Eq. 6 ≡ classical Gaussian Hamiltonian noise). The
   queued involuntary-W derivation check is **RESOLVED (2026-07-03,
   `involuntary_w_check_2026-07-03.md`, prereg → registered-P2 miss → A-IW-1 → 16/16
   gates):** Prop IW-1 = passive records are EVEN in the commutator (Im-K) sector
   (realness/parity theorem, exact machine nulls 0.0e+00); outcome-discarded moments are
   EXACTLY classical (cosh law, ≤ 1.3e−13 at all g); the quantum imprint is quadratic
   (W₁₂ ≈ −8κ², cross-window commutator integrals) and lives only in outcome-resolved
   cross moments; their Case-3 W = S·H is COMPLEX = precisely the structure a real passive
   machine lacks. "Invisible" language SAFE with the class × access × order scope explicit;
   draft duties in that doc §6.
2. arXiv:2601.02160 — body-read DONE:
   `docs/papers/reading_notes/xu_ankerhold_qdmess_nonmarkovian_review_2601.02160.md`
   (QD-MESS umbrella = recency-preferred engine-landscape anchor; their mode-space
   invariance = ENGINE-side representation gauge, distinct from our record gauge).
3. arXiv:2401.17255 — body-read DONE:
   `docs/papers/reading_notes/li_yan_dqme_sq_quantum_simulation_2401.17255.md`
   (DQME-SQ second-quantized dissipaton embedding, quantum-circuit substrate; landscape
   only, zero ownership contact).
4. arXiv:2502.05408 — body-read DONE:
   `docs/papers/reading_notes/dong_nongaussian_digital_qns_2502.05408.md`
   (non-Gaussian digital-control QNS; active pole, verdicts unaffected; cite as the
   recent cost-of-lifting-Gaussianity endpoint in the Step 0.α boundedness discussion).
5. IEEE 10240942 — UNIDENTIFIED (paywall, no accessible index); user to supply title/arXiv
   mirror, then same treatment. STILL OPEN.
LESSON (search design): the 6-axis adjudication search had no "simulation-methods/review" axis
and its learnability axis under-covered late-2025 postings — future ownership searches add an
explicit engine-methods axis + a recency sweep of the last 12 months.

## 4.7 USER-ROUND CORPUS TRIAGE (2026-07-03) — verdicts + PAPER-PHASE duties (NOT mainline;
priority ratification: build > positioning)

User ran their own search round (README 9→14 sections, 110 entries), catching a June-2026
cluster all prior sweeps missed. Triage against the load-bearing claims (notes are
精读-grade in-repo):
- **B.1 STANDS, two "first" claims DEMOTED:** Chu 2606.00433 (Jiang group) = continuous
  1-param gauge R(t) + uniqueness theorem + physicality-bounded GAUGE BANDS on repeated-MCM
  records, 60q hardware — methodologically point-for-point our pattern; we can no longer
  write "first continuous gauge in a record setting" or "first physicality-band reporting".
  Surviving deltas: object (Σ ∈ Sym⁺(nR), structured gauge GROUP + dimension counts vs one
  scalar t), machine (multi-qubit stabilizer parity detectors vs 1q MCM strings), noise
  class (continuous Gaussian field vs 8 classical HMM probabilities). Their gauge = the
  classic 2-state-HMM similarity gauge → new dialect axis (HMM identifiability, Petrie/
  Ito-Amari line; Burke-Rosenblatt already in bib).
- **Lee 2606.05664:** detectors = Wilson loops = gauge-invariant = learnable DOF (discrete
  Pauli/Clifford; maps to Chen's PTG). DUTY: cite at our "loop products = identifiable sign
  content" sentence + explicit disambiguation of the two senses of "gauge" (lattice-gauge
  redundancy group vs identifiability gauge).
- **Cheng 2606.29638 (Jun 30!):** MCM insertion BREAKS the Chen gauge (|δ| MCMs = cost);
  no post-MCM residual-gauge characterization (their W2); their open problems #1/#2 point
  directly at our territory. DUTY: 4th data point in the access-relativity statement;
  their binomial flip diagnostic = adaptable non-Markovianity test for stabilizer rounds
  (build-phase idea, not claim-relevant).
- **#2 untouched** (nothing in corpus touches arbitrary-Σ closed-form silent-floor).
  **#3 STANDS-NARROWED:** Chu bands = mandatory methodology precedent; GLE 2402.11705
  body-read queued (constraint type?); PMME 2510.12894 / Quiroz 39q join the active-pole
  baseline rows. **Wedge REINFORCED:** Shao 2606.00474 c=1 no-contraction theorem =
  supporting citation; TJM/cTJM Pauli-only = contrast; 2507.08713 ("QEC Markovianizes
  noise") = counter-narrative to treat honestly in the wedge-magnitude discussion.
- **Positioning posture (ratified direction):** from "creating a methodology" to
  "completing the unoccupied corner of a rapidly-forming picture" — four corners: Chen
  (discrete/active/duality) · Chu (continuous scalar gauge/MCM records/physicality bands) ·
  Lee (detector=loop=learnable, discrete) · Montañà-López (continuous kernels/designed
  access/positive protocols) → ours = continuous Σ × passive stabilizer machine × gauge
  group + dimension counts + closed forms. ALL of this = PAPER-PHASE maintenance; no
  further search rounds as mainline; search-design lesson extended (new axes: MCM/
  instrument characterization, lattice-gauge/spacetime-code, classical HMM identifiability;
  acceptance test = naive-query robustness).

## 5. Parked (trigger-gated, not lost)

B4′ surface-mix scissors bet (17q); CZ coherent-ZZ slot; f hardware grounding (von Lüpke as
source); Cox sampler d≥5; half-silent spectrum; λ=0.04 tail (starred); Tier-2 frozen-decoder demo
(A8 instrument-only); Bone #5 monotone-information inequality (parked per original §5); direct
Landau–Streater 精读 (small debt, only if the theorem becomes load-bearing in prose).
