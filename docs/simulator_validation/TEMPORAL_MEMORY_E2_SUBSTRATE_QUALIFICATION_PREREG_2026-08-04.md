# E2 production-sampler substrate qualification — Pre-Registration (theory-first, LITERATURE-GROUNDED)

Status: PRE-REGISTRATION, 2026-08-04. Predictions written BEFORE any F6 oracle computation and
BEFORE any substrate run. Parent packet: the 2026-08-04 temporal-memory survey and the E1 result
(`TEMPORAL_MEMORY_E1_EXACT_SMALL_FALSIFIER_RESULT_2026-08-04.md`). Instance addendum (binding):
`outputs/temporal_memory_survey_2026-08-04/E2_INSTANCE_ADDENDUM.md`. E1 conventions and the E1
prereg's §§2/3a/4/5 apply where not overridden. Downstream-citation duties inherited from E1:
the B4/B1 band misses travel with any use of F5/F1; marginal-matched claims use F1b. No
`src/**` changes.

## -1. Question charter

- **Decision + consequence.** Qualify (or refute) Direction 2's two-stage exact-sampling
  substrate mechanics at frozen-instance level: Python-owned exact-rational latent sampling
  composed with (S-A) stim FlipSimulator co-simulation — including the closed-loop
  outcome-conditioning discipline — and (S-B, conditional) PECOS stateful plugins. If
  qualified: the production SAMPLE path for classical-memory cells is anchored, and the V10
  discipline graduates from run-verified inference to preregistered qualification evidence. If
  refuted: the failure localizes (wiring, discipline, or framework semantics) before any scaled
  use.
- **Plausible attack + independent anchor.** All reference laws are frozen exact artifacts
  (E1 stage 1 + amendment; F6 added by the same dual-oracle gate in stage E2-0); substrate
  outputs are counts against known exact laws; corruption wirings serve *known exact
  alternative laws*, so detection power is computable in advance from exact KL divergences.
- **Alternative formulations + invariants.** Sampler correctness argued two ways: constructive
  (exact `randrange` Bernoulli path + source-verified injection semantics) and statistical
  (anytime-valid e-processes vs the exact laws); both must cohere. Invariants: A11 (rule-deleted
  F6 ≡ F1_mem), A12 closure zeros, seed-determinism of reruns.
- **Kill condition.** A clean-leg e-process rejection that reproduces under an independent
  reimplementation of the leg (not attributable to a wiring bug) — i.e., a genuine substrate
  semantic mismatch (e.g., the randomization discipline is wrong) — kills the affected
  substrate's qualification. Any registered corruption wiring that fails to be rejected within
  its budget (inert corruption) invalidates the battery. PECOS unavailability is censoring, not
  a kill.
- **Selection warning.** E2 is the dependency-ordered follow-up chosen in the survey; no
  novelty claim.

## 0. Grounding ledger

| premise | anchor | grade |
|---|---|---|
| FlipSimulator co-simulation semantics (state persistence across `do()`, injection API, latent-out-of-detectors, closed-loop = `reference_sample ⊕ measurement_flips` with stabilizer randomization ON; disabling randomization breaks outcome conditioning) | survey `04E` V10 — run-verified on stim 1.16.0; C++ flag name source-verified at main | closed (run-verified) |
| PECOS plugin lifecycle (instance persists across shot loop; `shot_reinit` plugin-controlled; `run_multisim` breaks cross-shot state) | survey `04E` V14 — source-verified at commit 8ad150ce | closed (source-verified) |
| Reference laws F1/F1b/F2/F4/F5×3 + corruption laws | E1 stage-1 artifacts, post-amendment pins (o1 def7f674…, o2 3aa40331…) | closed (dual-oracle, 4-implementation agreement) |
| F6 law | to be computed in stage E2-0 by the same Builder-A/Builder-B disjoint pattern with the 1e-13 gate | gate-conditional |
| e-process validity under optional stopping (Ville) | standard theorem; survey `05` F#9 registered the methodology | closed (class-a inequality; implementation under test) |
| Exact Bernoulli via integer `randrange` | elementary; PRNG quality declared as ledger row (Mersenne Twister, seeds registered) | closed (derivation) |

## 1. Mechanisms

Instances and substrates exactly per `E2_INSTANCE_ADDENDUM.md` (F6 closed-loop cell; clean legs
F1_mem, F1b_iid, F2, F4, F5_RESET/HOLD/ADVANCE, F6; corruption wirings W1–W6). No swept ranges;
everything frozen.

## 2. Metric binding

- Primary statistical gate: universal-mixture (Dirichlet(1,…,1) posterior-mixture likelihood
  ratio) e-process over the 512-support multinomial vs the exact H0 law; anytime-valid;
  rejection at e ≥ 1000 (α = 1e-3, per-leg semantics declared, no family-wise claim). This is a
  class-(c) gate: a clean pass is failure-to-reject corroboration, never generator-bias
  certification (the constructive argument carries exactness); a corruption rejection is a hard
  class-(a-style) trip.
- Diagnostics (registered, non-gating): empirical TV vs the project band
  `max(6/√N, 3·√(K/N))` from `docs/METRICS.md` (K = realized union support), per leg.
- Forbidden proxies: histogram closeness may not replace the e-process for ordered-batch legs;
  per-round marginal agreement may not stand in for joint-law legs (E1's B1 lesson); a PASS on
  S-A may not be transferred to S-B or vice versa.
- Power table: exact KLs (natural log) between the frozen laws, computed and frozen in E2-0
  before substrate runs; corruption budget per wiring `min(100·N*, 10^6)` with
  `N* = ln(1000)/KL(served‖H0)`.

## 2a. Predicted observables

- Class (a): A11 (rule-deleted F6 ≡ F1_mem, exact, checked in E2-0); A12 (F6 closure zeros);
  seed-determinism (bit-identical counts on rerun with same seed and version pins).
- Class (b): B7 `TV(F6, F1_mem) ∈ [1e-4, 1e-1]`; B8 `P_F6(d[3,c1]=1) > P_{F1}(d[3,c1]=1)`
  (escalation direction). Computed in E2-0 from exact laws; misses are findings.
- Class (c): every clean leg (8 legs × available substrates, N=10^5, registered seeds) ends
  with e < 1000; every corruption wiring W1–W6 rejects within budget; empirical-TV diagnostics
  within the project band on clean legs.

## 2b. Disconfirmation surface

Strongest competitor to "substrate exact": *compensating-error agreement* (a wiring bug whose
served law happens to be statistically indistinguishable at N=10^5). Separator: the corruption
battery is built from exactly the plausible wiring bugs (W1–W6 = drop-the-loop, reset-vs-hold,
extra-kernel, forgot-the-chain, drop-feedback, mid-shot reset), each with precomputed detection
power; plus the constructive audit (scorer reads the sampling path for float thresholds,
randomization flags, injection calls). A bug outside the registered list that evades both is a
declared residual risk, recorded, not claimed away.

## 3. Independent ground truth

The frozen E1 dual-oracle laws (+ F6 by the same dual gate in E2-0); the substrate never scores
itself; the scorer (not Builder S) runs all statistics; the un-led reviewer re-runs a subset
with fresh seeds and their own e-process implementation.

## 3a. Constraint ledger + falsifiers

| constraint | assertion | falsifying test | broken input | trip requirement |
|---|---|---|---|---|
| Closed-loop discipline correct | F6 leg passes vs F6 law | W1 | rule-dropped wiring | e ≥ 1000 within budget |
| Randomization discipline load-bearing | disabling stabilizer randomization breaks F6 | W7 (registered here): F6 leg with `disable_stabilizer_randomization` | discipline-broken run | e-process rejects OR the leg fails a registered determinism check; either counts as the trip (V10 predicts biased outcome conditioning) |
| Cross-shot HOLD real | F5_HOLD leg | W2, W3 | reset / extra-kernel wirings | rejection within budget |
| Chain wiring real | F1_mem leg | W4 | marginal-draw wiring | rejection within budget |
| Feedback wiring real | F4 leg | W5 | feedback dropped | rejection within budget |
| No undeclared reset | F1_mem leg | W6 | mid-shot redraw | rejection within budget |
| Latent stays private | detectors/observables contain no latent columns | config audit + A12 | deliberate latent-bit-to-detector variant (W8, registered here) | detector marginals shift ≥ precomputed amount; scorer detects |
| Exact sampling path | no float thresholds in Bernoulli/categorical draws | code audit by scorer | a float-threshold variant run (W9) on F3-rates leg is NOT required (values too small to distinguish statistically) — audit-only row, declared as such |
| Censoring honesty | PECOS absence = CENSORED | env probe | — | verdict vocabulary check |

## 4. Bounded simplifications

Sampling-path floats: none (exact integer draws). PRNG: Mersenne Twister with registered seeds —
declared ledger row, not a proof obligation. Finite N: statistical, ledgered as sampling
uncertainty. No truncation, no discretization. W9 is audit-only (declared limitation of
statistical detection for tiny rates).

## 5. Epistemic status

(a): A11, A12, seed-determinism, exact-draw construction. (b): B7, B8. (c): all e-process gates,
TV diagnostics, budgets. Headline verdict per substrate: "S-A (and S-B if available) qualified
as an exact two-stage sampling substrate on the frozen classical-latent cells incl. the
closed-loop cell" — PROVISIONAL, frozen-cells-only, sampler-capability-only (no scoring claim,
no scaling claim, no quantum-memory claim).

## 6. Build org

E2-0: Builder A / Builder B extend their own oracles with F6 (disjoint authorship preserved;
artifacts versioned this time — new files, no in-place overwrite, per E1 reviewer F-5);
comparator gates + freezes the KL power table. E2-1: Builder S-A (stim substrate; may read the
declarations, V10 probe notes, and stim docs; may NOT read oracle scripts or artifacts —
scorer grades), Builder S-B (PECOS, conditional, separate agent). E2-2: independent scorer
(all statistics + code audit). E2-3: un-led reviewer (fresh seeds, own e-process, subset rerun,
process audit). Resource caps: 600 s / 8 GB per run; censoring semantics per E1.

---

Gate: `premises closed? yes (V10 run-verified, V14 source-verified, E1 artifacts frozen; F6
gate-conditional and computed before substrate runs) | standard metric bound? yes (e-process
registered as class-(c) gate + METRICS TV band diagnostics; power table frozen in E2-0) |
predictions frozen? yes (A11/A12, B7/B8, W1–W9 trip requirements, budgets) | independent GT?
yes (dual-oracle laws; scorer ≠ builder; reviewer re-runs) | constraint falsifiers registered?
yes (W1–W8 executable trips + one declared audit-only row W9) | simplifications bounded? yes |
controls registered? yes (A11 identity, seed determinism, censoring vocabulary) |
preregistration gate: pass`
