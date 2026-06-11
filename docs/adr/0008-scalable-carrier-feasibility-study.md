# ADR 0008 — Scalable-carrier feasibility study (charter)

## Status

**Proposed — charter recorded 2026-06-10; C1+C2 (theory panel + review) COMPLETE 2026-06-10;
decision: the C1 composed architecture is CONDITIONALLY ADMISSIBLE under conditions K1–K5
(§"C2 outcome" below); study continues at C3 (seam-test prototype first). Panel reports
archived verbatim at `docs/.reports/adr0008_panel/` (T1 requirements, T2 candidates, T3
adversarial, reviewer verdict in the session record).**

**C3 seam test RUN COMPLETE (2026-06-11; results + audits in `docs/metric_results.md`
"ADR 0008 SEAM-TEST RESULTS"). C1 composed architecture: conditionally admissible under
K1–K5 — K1 first read ABSTAIN: real seam residual (sandwich 9.3e-4–2.7e-3, k2ry
3.2e-2–8.1e-2 TV over φ ∈ [0.05, 0.15]; sandwich scaling LINEAR, the registered quadratic
ansatz falsified), no derivation-cited band ⇒ registered abstain on seam-straddling
φ-sensitive functionals with window-limited fallback; no structural break, no in-window
contamination; the C3 perturbative module NOT triggered; K1 OPEN pending the
seam-straddling re-tiling second read (own registration, trigger-gated). In-window
admissibility unchanged (P-d/R_det/T3 recovery at exact grade; fit-free bunching readout
confirmed the T-B theorem at run level). Determinism item 14 missed at (a)
(tolerance-level; carried OPEN). L0b/L1–L3 lemmas still gate hardware bands and surface
registrations as scheduled.** The study's two unblocking
conditions (ADR 0006 Decision 4) are met: (i) the support-structure question is resolved on
controlled teachers — H2's theorem-backed verdict is that **declared edge DOFs, not probe
richness, close the φ-sensitive misspecification band**; (ii) the >15-qubit feasibility wall
is now load-bearing — the d=5/d=7 surface-code twin target (ADR 0007 Decision 2) cannot run
on `forward/exact` (density-matrix, feasibility-only ≤~15q). This document is the BINDING
CHARTER for the study: the decision question, requirement categories, candidate seeds, and
process are fixed here BEFORE any derivation or prototype; the panel's derivations fill the
requirements and scoring; prototypes (if any) get their own pre-registrations in
`docs/metric_results.md`. Per the epistemic-status declaration (METRICS.md), every
requirement, criterion, and score in this study carries its class — (a) exact / (b)
prediction band / (c) heuristic gate.

## Decision question

Which scalable forward **carrier** — the substrate that computes the twin's observation law
`p(y|c) = Tr[M_y C(c)(ρ0)]` beyond the exact density-matrix wall — supports all four twin
capabilities (recover / understand / manipulate / predict) on **d=5 and d=7 surface-code
windows** (the local Google releases: `google_72Q_surface_code_d3_d5_set1/2`,
`google_105Q_surface_code_d3_d5_d7`), under the binding constraints below?

## Requirement categories (the panel DERIVES the precise statements; classes pre-assigned)

- **R-NLL** (a/b): the observation-NLL must be computable with a DECLARED exactness class —
  exact, or approximate with a quantified, claim-carried bound. A silent approximation is a
  claim-discipline violation, never a candidate feature.
- **R-EDGE** (a): per H2/ADR 0006, the carrier must host **declared 2-body edge DOF slots**
  (coherent corrections), not only factorized per-location channels; the H2 fork
  ((b) explicit edge slots → (a)) binds.
- **R-GRAD** (a): end-to-end differentiability for label-free LBFGS calibration (the
  registered fit machinery), with the execution-mode-equality discipline (P1h precedent)
  applicable.
- **R-SCALE** (b): derived cost model at d=5/d=7 window sizes (state, syndrome conditioning,
  per-closure cost); the M3 execution diagnosis binds the model: host-dispatch-bound loops,
  not FLOPs, are the realistic wall — the cost model must count kernel launches/syncs, not
  only arithmetic.
- **R-GPU** (c, design constant): GPU-only for model compute (user directive, ledgered);
  single-context execution patterns preferred (measured WSL2 anti-patterns bind).
- **R-MECH** (b): mechanism-class coverage — at minimum the M-series back-edge axes:
  correlated/edge structure (H2), the basis-independent bunching axis (M3: located R̂ up to
  17.7; leakage-like), drift hooks (M5). A carrier that structurally cannot express bunching
  repeats the pij arm's structural deficiency inside our own model class.
- **R-CLAIM** (a): isolation contract intact (observations only); identifiability/alias
  honesty at surface-code contexts (fiber-constant functional discipline; the registered
  craft rule: bands on identified functionals).

## Candidate seeds (the panel surveys; not exhaustive)

1. **(d) DEM-bulk + coherent-corrections** — ADR 0006's named deferred candidate: a
   stochastic DEM bulk carrying the budgeted mass + declared coherent/edge corrections.
2. **Tensor-network forward** (boundary-MPS / TN syndrome-likelihood) — existence proof at
   d=5: dMLE (arXiv:2602.19722; vendored PRISTINE at `external/baselines/DMLE-QEC` —
   read-only, recommended settings, minimal adaptors only per the baseline discipline).
3. **Pauli/stabilizer-propagation hybrids** (Clifford bulk + perturbative non-Clifford /
   coherent corrections).
4. **Generative/learned surrogates** (e.g. qecGPT, vendored pristine) — expected role:
   BASELINE arms, not the carrier (claim discipline: a learned surrogate has no exactness
   class), unless the panel derives otherwise.
5. Anything else the cached literature (docs/papers/, IDENTIFIABILITY_AND_CRL_SURVEY.md)
   supports with an existence/cost argument.

## Pre-registered decision rule

A candidate is ADMISSIBLE only if every (a)-class requirement is met exactly and every
(b)-class requirement has a derived band. Among admissible candidates, the pick minimizes
derived cost-at-d=7 subject to R-MECH coverage; ties break toward the candidate with the
strongest existing prior art (reproducible baseline). The decision is recorded as ADR 0008
"Accepted" with the panel's scoring table; if NO candidate is admissible, the fallback is
recorded honestly (window-limited surface-code work + re-derivation, never a silent
requirement drop).

## Study milestones

- **C1** — requirements derivation (theory; this panel).
- **C2** — candidate scoring against C1 (theory; this panel + reviewer).
- **C3** — minimal feasibility prototype(s) for the shortlist ONLY, each with its own
  pre-registration in `metric_results.md` (epistemic classes; predictions before runs).
- **Decision** — ADR status → Accepted, with the d=5/d=7 milestone plan handed to the
  ADR 0007 sequence (M4/M5 continue in parallel on the rep-code rungs).

## C2 outcome (panel + reviewer synthesis, 2026-06-10)

**The three-tier error taxonomy (binding for every carrier claim).** (1) *Family design* —
which marginals get scored: a DECLARED composite-marginal family is a proper scoring rule and
a design (M3 precedent), needing no error bound, provided equal treatment (all arms score the
identical family) and declared naming ("composite family NLL", never bare "syndrome NLL").
(2) *Evaluator approximation* (ε_log) — error in COMPUTING the declared marginals (truncation,
perturbative remainder, round-off): log-domain bound, no 1/√N shrinkage, optimizer-harvestable
(the registration-grade budget is SE/10 ⇒ ~3×10⁻⁶ relative per block at M3-scale SEs; the
informative-claim flip threshold is 2–4×10⁻³ per block), governed by the G-NLL guard block.
(3) *Model-class misspecification* (B_misspec) — truth outside the declared class+family:
functional-indexed, detected by negative controls and oracle seam tests, priced or abstained —
NEVER convertible into an ε_log. C1's cross-seam item is tier (3), not tier (2).

**Sharp bunching boundary (corrects this charter's R-MECH phrasing, T1 theorem T-B).** Only
unital-diagonal (in particular Pauli/DEM) iid-in-time fields are pinned at R = 1; a
time-constant NON-UNITAL CPTP field expresses R > 1 with zero extra DOF (record asymmetry —
how the M3 twin expressed the measured bunching). R > 1 certifies {non-unital local structure}
∪ {hidden time-correlated mode}; the T-B/T-C discriminator is the multi-lag curve R_k
(geometric rate 1−p01−p10 DETERMINED by (r,R) in T-B vs free λ in T-C) — mechanism attribution
must be earned through it, never assumed from R̂ alone.

**Scoring (post-review).** C1 = DEM/HMM-bulk + window-exact CPTP coherent corrections (+ C2 as
bulk engine, + C3-module as trigger-gated cross-seam corrections): **conditionally admissible —
the shortlist** (only candidate meeting R-EDGE(a) and R-CLAIM(a) with a measured execution
profile, and the only one that has expressed the bunching axis in-class on hardware). C2-pure
(dMLE TN): inadmissible as carrier (no coherent slot — sums probabilities, not amplitudes;
Choi-lift squares the 2²⁷ intermediate to 2⁵⁴; bunching structurally pinned at R=1 by T-A/T-B),
but MANDATORY as the published-bar baseline arm and adopted as C1's bulk engine (log-domain
re-numerics under our floor discipline). C3-pure (perturbative hybrid): not separately
admissible (remainder bound underived; negativity domain); adopted as C1's cross-seam module,
precomputed-coefficient form only. C4 (qecGPT): baseline-only (optional NLL-ceiling probe with
declared semantics). C5 (Majorana single-axis oracle): parked pending D6.

**Feasible surface-window envelope for C1's window-exact corrections at d=5 (reconciled).**
With R=3 enumerated rounds, complex128: bulk windows up to 8 data qubits / 3 interior checks
per round are comfortable (≤~0.6 GB, minutes/fit); the 3×3-data / k=4 window (9 data) is
validation-only at R=3 (17.2 GB forward state). **D3 verdict (2026-06-10): R=2 for 2-layer
blocks is REFUTED in the general CPTP class** (syndrome-toggle covariance fails exactly on
the structures the carrier hosts); the 1.074 GB k=4 cell is earned legitimately by exact
leading-record CHUNKING (×16 passes, bit-deterministic) or by K=1 families — and per D2 no
currently-registered functional needs the k=4 window at all. k≥5 or n_w≥12 is dead.
R-EDGE slot inventories use D1's MEASURED pair lists (30–33 / 103 / 215–216 at d=3/5/7),
not the code-structure formula. Window count is linear in d² (≈12–30/basis at d=5,
~30–60 at d=7); per-window cost is d-independent. Per-shot COST scaling is intrinsic and must
be itemized; per-shot DISPATCH is prohibited (the shot-batching theorem). Fleet wall-clock is
unscoreable until the registered fleet is enumerated (D4) — earlier "~4–12 h / ~1 day" figures
are per-condition, not per-destination.

**Conditions on C1's admissibility (the ADR moves to Accepted only with these registered):**
- **K1** cross-seam residual: a derived functional-indexed B_misspec band on φ-sensitive claim
  functionals under seam-straddling mass, OR a registered abstain rule — established/falsified
  by the seam-test prototype against the exact oracle.
- **K2 — SUBSTANTIALLY DISCHARGED (2026-06-10, K2 panel derivation + reviewer; pending the
  mechanical L0–L1 circuit audits).** The K2-T1 footprint theorem (measurement-induced twirl)
  settles the recorded T1↔T3 disagreement in T3's direction by a STRONGER argument: on the
  released memory-only contexts, every bulk data slot's coherent AND non-unital structure is
  exactly aliased to its Pauli twirl at all orders (C0 — stronger than the rep code, which kept
  the δ direction); coherent edge slots collapse to their twirled correlated rate sin²φ (C1′);
  the only exceptions are weight-2 boundary checks at second order, temporal boundary layers,
  and order-d logical paths (C2′). q^eff survives as an exact gauge under XZZX
  (extraction-structure-independent proof). **Decision consequence: the d=5 carrier carries NO
  hardware edge-coherence claims on the released contexts — controlled-teacher coherent claims
  only; hardware edge claims are twirled hyperedge rates.** The identified quotient =
  footprint-class pooled Pauli rates + per-check q^eff (+ thin boundary blocks); claimable
  fiber-constant functionals: detector marginals, R_det/multi-lag R_k, spatial pairs.
  **R-MECH amendment: T-B does not transfer to the surface bulk** — d=5 bunching hooks are the
  T-C latent modulator and/or value-asymmetric readout {q01,q10}; requirement-list pins 21–23
  must be re-derived against those hooks (gates the later surface-window registrations, not
  the seam test). Remaining: L0 (gate order/leg map/extra-qubit attribution — confirms the
  theorem premises; note D1's round-dependent qubit counts), L1 (footprint-distinctness audit
  — exhaustifies the per-slot claims; required before any HARDWARE band), L2 (T-C latent
  gauge), L3 (boundary-layer Fisher vs r over the MEASURED ladder).
- **K3** transient-resolved family design. Round-range CORRECTION (D1 measured): set1/105Q
  ladders run r01–**r250**, set2 r05–r50 — stationary conditioning is not structurally blocked
  by round count; the surface transient length remains unmeasured (the open K3 item).
- **K4** cost-model closure: fleet enumeration (D4), minimal-R derivation (D3), t_eff
  microbenchmark (P4), end-to-end wall-clock prediction (FM10 form).
- **K5** do() pushforward: the channel→bulk map derived and pinned wherever the bulk engine
  carries mass; do() acts on the channel field only, never as a DEM-edge edit.

**C3 prototype order:** (1) **the seam test FIRST** — two-window ≤15q strip, controlled H2-style
coherent edge ON the seam + Markov bunching teacher (R≈5), exact DM oracle; swap-gate triplet
(base p(s,m), do(edge→I) ΔLER, band width) with the TEACHER side computed by forward/exact
(anti-cancellation form); amended to include the R_det pin and the theorem-pin suite on the
composed carrier. It attacks K1, exercises the composed architecture end-to-end, and is the
fastest kill (hours). (2) C2-as-bulk d=5 contraction reality check on our 5090/WSL2 + the
closed-form bunching-floor control — needed regardless (mandatory baseline) and instantiates
the FM7 determinism pins. (3) C3-module φ² coefficients — only if (1) shows the seam carries
real mass. Each prototype gets its own pre-registration in `metric_results.md` with epistemic
classes; the unified 39-item C3 requirement list (reviewer verdict §2: G-NLL block, H2
transplant battery, P1h/determinism pins, cost tripwires, bunching pins 21–24, theorem-pin
suite, FM8 legality table, alias-quotient prerequisite, anti-cancellation swap gate + d=5
B-loop re-run, do()-pushforward pin, surrogate semantics, d=7 single-replicate labeling) is
the binding checklist for those registrations.

**Open derivations.** C2-synthesis items (no runs): D1 stim/metadata inventories (rounds,
shots, CZ schedules, d7 ancilla count, edge/stray pairs); D2 functional↔window-geometry support
map; D3 minimal enumerated-round count per family; D4 destination fleet enumeration; D5
bunching representability + T-B/T-C discriminator write-up; D6 C5 likelihood-tractability
literature check; D7 re-instantiated ε_max = SE/(10·N_eval) for the d=5 design; D8
equal-treatment feasibility on the planned arms. C3-registration prerequisites: P1 = K1 text;
P2 = K2 derivations; P3 = K3 design; P4 t_eff microbenchmark; P5 perturbative remainder bound
(if module triggers); P6 TN additive→log bound + support floor (if truncation enters the d=7
bulk); P7 = K5 map; P8 implicit-vs-unrolled gradient tolerance; P9 sub-float64 round-off budget
(if ever used).

**Panel corrections recorded (reviewer §5):** T2's seam item reclassified to B_misspec; T2's
(n_w=8, k=4) cell geometrically unrealizable as a bulk surface window (k=4 forces n_w≥9);
fleet times re-scoped; T3 FM5 guard corrected per T-B; T3 flip threshold stated 2–4×10⁻³
(covers both bases); raw parameter counts carry gauge — only W2-gated identified DOF count;
H2 theorem labels written "H2-T1/H2-T2′" to avoid collision with panel agent names.

## Process (binding)

Heavy task ⇒ ≥3 agents + real-time reviewer (user rule, 2026-06-10): three INDEPENDENT
theory agents (T1 requirements; T2 candidate survey + cost models; T3 adversarial — what a
carrier can silently break), then a reviewer pass, then orchestrator synthesis into C2.
Theory-first: no prototype code before C2 lands and its registration is written. Baselines
stay pristine (CLAUDE.md baseline discipline). References: ADR 0002→0007 spine; H2 RESULTS,
M3 RESULTS + ADDENDUM (`docs/metric_results.md`); `docs/TWIN.md` (object contract);
`docs/.datasets/` notes (surface-code releases).
