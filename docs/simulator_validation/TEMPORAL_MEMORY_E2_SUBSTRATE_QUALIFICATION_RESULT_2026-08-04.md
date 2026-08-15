# E2 production-sampler substrate qualification — RESULT

Date: 2026-08-04. Preregistration:
`TEMPORAL_MEMORY_E2_SUBSTRATE_QUALIFICATION_PREREG_2026-08-04.md` (gate: pass). Frozen inputs:
`outputs/temporal_memory_survey_2026-08-04/E2_INSTANCE_ADDENDUM.md` (sha ce20c592…),
`E2_AMENDMENT_2.md` (sha fcdbbcba…, registered after the stage-3 review, before the fresh
corruption pass). Parent: E1 result. Artifacts: `outputs/temporal_memory_survey_2026-08-04/`
`e2_stage0/ … e2_stage4/`. No `src/**` changes.

## Verdict

**S-A (stim FlipSimulator two-stage co-simulation substrate): QUALIFIED as an exact-in-law
SAMPLE substrate on the frozen classical-latent cells — with two registered narrowings.**
**S-B (PECOS): VOID / CENSORED_RESOURCE — qualification fully open.**

Narrowings (binding on every downstream citation):

1. **Closed-loop conditioning is qualified for deterministic-reference circuits only.** W7
   proved (bit-identical streams, knob ON/OFF) that the stabilizer-randomization discipline is
   vacuous on the frozen cells — every measurement is reference-deterministic because all
   stochasticity is Python-injected. The V10 randomization-discipline row is NOT covered by E2
   (registered debt: a future nondeterministic-measurement cell).
2. **Sampler capability only.** No scoring/enumeration/structured-law claim; exactness is argued
   constructively (exact integer `randrange` sampling path, independently code-audited; zero
   float thresholds) and statistically corroborated — a clean e-process pass is
   failure-to-reject, not generator-bias certification.

## Evidence chain

- **E2-0 (F6 closed-loop instance, dual-oracle)**: STAGE0_PASS — O1/O2 agree to 3.3e-16; A11
  exact (rule-deleted F6 ≡ F1_mem entrywise); A12 closure zeros; B7 = TV(F6, F1_mem) =
  0.02119349481132753 (exact fraction recorded) IN BAND; B8 escalation direction holds
  (0.08198959… > 0.070834 exactly). KL power table frozen
  (`e2_stage0/stage0_results.json`, sha 545f6f80…).
- **E2-1 clean legs (S-A, stim 1.16.0, N=10⁵ each, registered seeds)**: F1_mem, F1b_iid, F2,
  F4, F5_RESET, F5_HOLD, F5_ADVANCE, F6 — all pass the universal-mixture e-process gate (never
  cross e ≥ 1000); empirical TV within the registered METRICS band on every leg.
- **E2 stage-3 un-led review**: CONFIRM_WITH_FINDINGS; independent e-process reproduces the
  scorecard exactly; out-of-registration replication (fresh seed 271828182, N=2×10⁴, F6) passes;
  constructive provenance probes (chunk-aligned bit-identical re-runs) pass. Three major
  findings — cured as follows.
- **Amendment 2 (registered prereg-design erratum)**: the corruption budgets `100·N*` were
  derived for a simple likelihood-ratio test while the prereg registered the mixture e-process
  for corruption runs too; the mixture's ~O(K/2·log N) redundancy made the budgets unreachable
  by construction (wirings demonstrably not inert: oracle LR crosses at ≈N*). Cure: corruption
  statistic corrected to the simple LR e-process (valid under H0; laws are exact frozen
  artifacts), fresh registered seeds, clean-leg code untouched.
- **E2-4 fresh corruption pass**: **CORRUPTION_BATTERY_PASS**, confirmed by an un-led reviewer
  with exact integer-rational recomputation (zero discrepancies):

| wiring | bug modeled | first crossing N | frozen budget |
|---|---|---:|---:|
| W1 | closed-loop rule dropped (serves F1_mem for F6) | 631 | 36 473 |
| W2 | HOLD → reset each boundary | 41 | 5 491 |
| W3 | HOLD → spurious boundary kernel | 386 | 102 026 |
| W4 | chain → per-round marginal ("forgot the chain") | 366 | 88 559 |
| W5 | feedback dropped | 234 | 8 741 |
| W6 | undeclared mid-shot reset | 269 | 25 227 |
| W8 | latent leaked into observable | 18 | 2 291 (KL(C7a‖F1_mem)=0.30162 nats) |

  Sanity (H0 true): the W4-LR e-process on the clean F1_mem stream never crosses over 10⁵
  records (max e 4.955; final log e −905.70). W8 marginal criterion: all 9 record bits within
  5 SE of the exact C7a marginals (max |z| 2.57). Retrospective scoring of the superseded
  stage-1 corruption streams (non-gating, transparency): all crossings comparable (473/52/592/
  943/25/261/23). Substrate integrity: script sha unchanged; 16/16 config-hash identity;
  bit-identical regeneration with registered (and superseded) seeds.

## Findings inventory and dispositions

Stage-3 review: F-1 statistic/budget mismatch → cured by Amendment 2 + fresh pass (above).
F-2 W7 inert by cell structure → narrowing #1 + registered debt. F-3 S-B non-re-derivable,
byte-identical to S-A, environment unpinned → S-B VOID; PECOS open. F-4 corruption seeds not in
the frozen addendum → seeds frozen in Amendment 2. F-5 W8 criterion post hoc → frozen in
Amendment 2 §D and applied in the fresh pass. F-6 inherited E1 citation duties → restated here:
any use of F5 cites the B4 HOLD-defect band miss (0.1456 > 0.1); any marginal-matched-rival
claim uses F1b, not F1's per-qubit-rate rival. Fresh-pass advisory: F-R1 pin builder-script
hashes in manifests at build time (adopted as practice going forward); F-R2 ≤1-shot budget
rounding ambiguity (immaterial; ceil convention recorded).

## What E2 does NOT claim

No scoring capability; no scaling behavior; no quantum-memory or coherent-error cells; no
randomization-discipline evidence (narrowing #1); no PECOS evidence; no family qualification
beyond the eight frozen legs; statistical passes are corroboration, not bias certification.

## Downstream

Direction 2's production-sampler architecture now has a qualified substrate exemplar (S-A) and
a frozen validation pattern (two-stage build, mixture-e-process clean gates, LR-e-process
corruption battery with KL-frozen budgets, un-led review). Open items for any E2b/E3/E4:
nondeterministic-measurement cell for the randomization discipline; PECOS leg from scratch with
environment pins; scaled-instance legs (larger codes) under the same pattern.
