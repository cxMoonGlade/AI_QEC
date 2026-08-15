# E3 measurement-interleaved truncation theorem (gap G-A) — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: PRE-REGISTRATION, 2026-08-04. Registered BEFORE any proof drafting, counterexample
construction, or numerical run. Closure packet: survey gap G-A (4/4 independent votes +
search-confirmed absent; `03_TAXONOMY_MERGED.md` §4) + the E3 focused closure
(`outputs/temporal_memory_survey_2026-08-04/E3_CLOSURE_REPORTS.md`, four ingredient reports
L-A..L-D with primary-verified locators). Test-bed substrate: frozen E1 artifacts. This is a
THEORY experiment: deliverables are proofs, counterexamples, and bound-validity numerics — no
`src/**`, no production code.

## -1. Question charter

- **Decision + consequence.** Prove (or refute at the registered boundary) the family of
  statements that convert LOCAL truncation data into JOINT-Record-law TV bounds for circuits
  interleaved with mid-circuit instruments. Positive results convert the survey's K5/K6
  approximate machinery from UNBOUNDED_APPROXIMATION_RESEARCH into BOUNDED_APPROXIMATION with a
  registered certificate route; the boundary results (T3b) fix forever which conditional-query
  guarantees are impossible without extra structure. Either way Direction 3 gets its keystone.
- **Plausible attack + independent anchor.** The closure located every ingredient at
  primary-verified grade: the telescoping stack (AKN Lemmas 12-13/Thm 4; Watrous TQI Prop
  3.48(2)/Eq. (3.306)/Thm 3.52), the per-branch engine (Werner v2 App. D: Def. 5, Lemma 1,
  Lemma 6, Thm 7 — with the state-dependence trick and its subnormalized Hölder variant), the
  fixed-approximant adaptive lemma (BGL 2112.08499v2 Lemma 1, TV ≤ 16Σε_t), the amplification
  lore (AA §1.2.2; PBG Lemma 2/Thm 3/Thm 4), the union-bound route (OV 2103.07827v2 Thm 1.3;
  KMW 1804.08144v2 Thm 1), and the sign obstruction (Jacob–Thiery 1309.6473v4 Thm 2.1).
- **Alternative formulations + invariants.** Each bound must be checkable two ways: symbolic
  proof and numerical validity on the E1 exact fixtures (a proved bound can NEVER be exceeded by
  a measured instance — a single violation kills the proof).
- **Kill conditions.** (K1) numerical violation of a claimed-proved bound (halts that claim:
  proof wrong or scope misdeclared). (K2) discovery of a published theorem already stating T3a
  (novelty dies; becomes citation + the numerical study stands). (K3) T1/T2 compile failure
  (would contradict textbook material — treated as our misunderstanding, full stop and reread).
- **Selection warning.** T3's openness is evidenced, not assumed (isoTNS arXiv:2602.02245v2
  states the needed control does not exist; BGL's gap is branch-dependence, nowhere closed).

## 0. Grounding ledger

Full locator table lives in `E3_CLOSURE_REPORTS.md` (L-A..L-D, verification grades marked).
Grade-B (model-mediated) quotes carry a registered citation-hygiene debt: BBCCGH Eq. (10)/Thm 1,
Gao 1410.5688 version pin, AA 1011.3245 final-version pin, PBG 1712.02806 final-version pin,
Harrow–Lowe 2510.08518 version pin — each must be pixel-level re-opened before any external
writeup (not blocking internal proofs). KSV §11 unopened (may contain an exact-constant AKN
variant) — one library check registered as debt.

## 1. Registered theorem targets

Conventions fixed once: TV(p,q) = ½Σ|p−q|; diamond distance of channels ∈ [0,2]; AKN "t.v.d."
= 2·TV; per-step instrument error = diamond distance of the instrument-as-QC-register-channel.
The evaluator's object is always the SUBNORMALIZED branch tree over record prefixes (no mid-way
renormalization); the public law is the leaf-mass vector pushed through the layout.

- **T1 — mass-aggregated leaked-mass lemma (branch trees).** Claim: if the evaluator, at step t
  on branch b, applies an arbitrary perturbation of trace-norm size η_{b,t} to the subnormalized
  branch state (dropping a branch entirely = η equal to its mass), then
  `TV(μ, μ̃) ≤ ½ · Σ_t Σ_b η_{b,t}`, with equality mechanism exhibited; downstream transport by
  CP-trace-non-increasing ℓ1-contractivity (Werner Eq.-(71)-style recursion, per branch).
  Status from closure: adaptable — Werner's single-trajectory summation + AGP's coupling shape;
  the branch aggregation is the new (short) content. **Prediction (a): provable, ≤2 pages,
  constant ½ as stated.**
- **T2 — instrument telescoping compile.** Claim: adaptive instrument sequence, step-t
  implemented map within diamond distance ε_t of declared (FIXED maps) ⇒ joint record-law
  TV ≤ ½Σε_t. Proof = the registered two-line compile (instrument → QC-register channel;
  feedback → classically-controlled channel; Watrous Eq. (3.306); readout by Thm 3.52/data
  processing). **Prediction (a): provable by compile; the write-up also states the strategy-norm
  per-round chaining lemma (unwritten in the literature per L-A) as a corollary attempt.**
- **T3a — branch-dependent truncation runtime certificate.** Claim: for state-dependent
  truncations applied per branch (top-k / SVD with per-branch runtime-measured discarded data),
  with per-branch trace-norm perturbation η_{b,t} obtained from 2-norm discarded weight via the
  subnormalized Hölder bound `‖XX†−X̃X̃†‖₁ ≤ (‖X‖₂+‖X̃‖₂)‖X−X̃‖₂` (locally purified, canonical
  form where available; NO renormalization), T1's aggregation applies verbatim and yields
  `TV(μ, μ̃) ≤ ½ΣΣ η_{b,t}` — an a-posteriori (runtime) certificate in exactly Werner's sense,
  now for the joint record law of an instrument-interleaved evaluator. **Prediction (b):
  provable by combining the closure's transferable pieces; the risk is the branch/conditioning
  bookkeeping. A numerical violation on any fixture kills it (K1).** Registered hypotheses that
  must appear: truncation never merges record branches (Kraus-index truncation carrying record
  identity is excluded as semantic change — L-B open question (iii)); adaptivity fixed per
  record prefix.
- **T3b — conditional-query impossibility boundary.** Claim: no bound on CONDITIONAL
  (prefix-conditioned) law error in terms of aggregated local truncation mass alone can avoid a
  `1/p(prefix)` factor: registered counterexample construction — adversarial truncation schedule
  concentrating all error on a low-mass prefix (AA §1.2.2 mechanism made concrete on an E1-size
  instance), demonstrating conditional-TV ≈ (total mass)/p while joint-TV obeys T3a.
  **Prediction (b): constructible; the three published escape hatches (1/p factor;
  multiplicative-error structure à la BBCCGH ratio sampling; anticoncentration side condition à
  la PBG Thm 3) are the complete registered classification of what evades it.**
- **T4 — randomized/unbiased truncation (assembly + obstruction).** Claims: (i) Rhee–Glynn/
  Russian-roulette debiasing over a truncation-level hierarchy yields UNBIASED estimators of any
  bounded Record functional, with the variance condition stated (Jacob–Thiery Thm 1.1 form);
  (ii) the sign obstruction: no nonnegative unbiased law representation in general (Jacob–Thiery
  Thm 2.1 applied to the branch-mass functional), hence unbiased SAMPLING requires the
  Bernoulli-factory route (masses ∈ [0,1]; Keane–O'Brien condition) — connecting gap G-G.
  **Prediction (a): assembly with citations; obstruction instance written out.**
- **T5 (stretch, may be deferred without failing E3) — near-deterministic-measurement route.**
  Compose OV Thm 1.3 / KMW Thm 1 with T1 bookkeeping to bound the record law with per-step cost
  = actual dominant-outcome failure probabilities (better than diamond worst-case in the
  low-noise QEC regime); projective syndrome extraction only (general instruments open at the
  source — Gao's own conclusion). **Prediction (c): attempt; outcome recorded either way.**

## 2. Metric binding

TV as above (registered ledger metric); bound-validity ratio `measured TV / claimed bound`
(must be ≤ 1 for proved claims — class (a) check); tightness ratio (class (c) diagnostic, no
acceptance band); conditional-TV with declared prefix and its exact mass from O1. Forbidden
proxy: local discarded weight REPORTED WITHOUT the mass aggregation is exactly the object this
theorem exists to replace — it may appear only as input to the bounds.

## 3. Independent ground truth

O1 exact laws (frozen artifacts, hashed) for every numerical row; hand-computed toy instances
inside the proofs (≤2 branches, worked exactly); the E1-C8 run as the pre-existing classical
data point (deficit ≈1.1457e-9, truncated law bit-identical across implementations).

## 3a. Constraint ledger + falsifiers

| constraint | assertion | falsifying test | broken input | trip requirement |
|---|---|---|---|---|
| Proved bounds are valid | measured TV ≤ bound on every fixture run | numerical test bed | — (validity is the test) | any violation = K1 |
| Zero-perturbation control | zero truncation ⇒ bound 0 ⇒ exact equality | exact-evaluator run | — | equality to O1 exact |
| Non-degeneracy of the test bed | the WRONG (unweighted local) bound must be VIOLATED somewhere on the fixtures | wrong-bound control runs | naive bound formula | ≥1 fixture violates it; if none does, the fixtures are too weak — registered finding, add harder fixture |
| T3b non-vacuity | the counterexample's conditional error actually scales as 1/p | sweep prefix mass | — | measured scaling within declared factor 4 of 1/p |
| No branch merging | truncation preserves record-branch identity | audit + a deliberate merging variant | Kraus-index truncation | merging variant must produce a SEMANTIC mismatch flagged vs O1 (not a bounded error) |
| Proof integrity | every step checkable | adversarial proof review (independent checker per proof, tasked to break steps) | deliberately weakened lemma variant given to checker as calibration | checker must catch the planted flaw |

## 3b. Negative controls

Planted-flaw calibration for each proof checker (a deliberately broken variant of one lemma
step; the checker is not told which document is planted). Zero-truncation exactness. Wrong-bound
violation (above).

## 4. Bounded simplifications

Numerics run on classical-diagonal fixtures (E1 instances) — declared: they exercise T1/T3a's
classical case and the branch bookkeeping, not the quantum-memory Hölder constant; a 2-qubit
quantum-memory toy (dense, exact) is included for the (‖X‖+‖X̃‖) constant check. Floating
comparisons at 1e-12 with exact-rational escalation on any near-violation (|ratio−1| < 1e-6 ⇒
recompute in rationals before declaring violation/validity).

## 5. Epistemic status

(a): T1, T2, T4 (proof-or-compile with citations; misses = K3-grade findings); zero-perturbation
and validity checks. (b): T3a provability bet; T3b constructibility bet + escape-hatch
classification. (c): tightness diagnostics; T5 attempt. Headline stays PROVISIONAL pending the
un-led mathematical review; nothing is built on T3a until the review confirms and the validity
battery passes.

## 6. Build org

Provers: four independent agents (T1+T2 compile; T3a; T3b counterexample; T4 assembly), each
producing a self-contained proof note with every step explicit. Adversarial checkers: one per
proof note, independent, instructed to refute; planted-flaw calibration per §3b. Numerical test
bed: separate builder against O1 artifacts + the registered bound formulas (not the proofs).
Un-led mathematical reviewer at the end (receives prereg + notes + checker reports + numerics
only). No `src/**`; artifacts under `outputs/temporal_memory_survey_2026-08-04/e3/`.

---

Gate: `premises closed? yes (four closure reports, primary-verified anchor stack; grade-B quotes
carried as registered citation-hygiene debt, non-blocking) | standard metric bound? yes (TV +
validity/tightness ratios; forbidden-proxy declared) | predictions frozen? yes (T1/T2/T4 class-a
bets, T3a/T3b class-b bets with kill conditions, T5 attempt) | independent GT? yes (O1 exact
laws + hand instances + E1-C8 data point) | constraint falsifiers registered? yes (incl.
wrong-bound non-degeneracy control and planted-flaw checker calibration) | simplifications
bounded? yes | controls registered? yes | preregistration gate: pass`
