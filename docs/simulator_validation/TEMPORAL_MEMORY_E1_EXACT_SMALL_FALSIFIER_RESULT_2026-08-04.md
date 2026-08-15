# E1 exact-small falsifier + dual-oracle qualification — RESULT

Date: 2026-08-04. Preregistration:
`TEMPORAL_MEMORY_E1_EXACT_SMALL_FALSIFIER_PREREG_2026-08-04.md` (gate: pass; sha in the survey
`FREEZE_RECORD.txt`). Frozen inputs: `outputs/temporal_memory_survey_2026-08-04/`
`E1_INSTANCE_DECLARATION.md` (sha 2ca03ca3…) and `E1_AMENDMENT_1.md` (sha 2be51ec5…, registered
after Stage 1, before any F1b computation). All artifacts under
`outputs/temporal_memory_survey_2026-08-04/e1_stage1/` and `e1_stage2/`. No `src/**` was touched.

## Verdict

**All four candidate primitives QUALIFIED on the frozen cells (provisional, per-primitive,
frozen-cells-only per prereg §5).** Un-led reviewer verdict: CONFIRM_WITH_FINDINGS; all findings
dispositioned below, the two owed trip-closures executed. No kill condition fired; no inert
corruption; no qualification cell overturned.

| Primitive | Capability × cells | Guarantee tier exercised | Result |
|---|---|---|---|
| P1 hybrid forward filter | SCORE_PREFIX/SCORE_RECORD/full law; F1/F1b/F2/F3/F4(+feedback-off)/F5(RESET·HOLD·ADVANCE); corruption vehicle for C1/C2/C4/C7a/C7b/C9/C9b/C5/C8 | ALGEBRAIC_EXACT (Fraction end to end) | exact rational equality with O1 on every law entry |
| P2 affine-collapse HMM filter | same instances | ALGEBRAIC_EXACT | exact equality |
| P3 tilted-Fourier + inverse WHT | same instances; 512 Walsh coefficients (F1_mem); μ(r*) exact; feedback bit kept resolved in F4 (registered mechanic exercised) | ALGEBRAIC_EXACT | exact equality incl. μ(r*) as exact fraction |
| P4 WFA realization + equivalence | F1_mem vs {F1_iid, F1b_iid, C7b-gauge, itself} | ALGEBRAIC_EXACT | INEQUIVALENT / INEQUIVALENT / EQUIVALENT / EQUIVALENT — all confirmed against exact PMF comparison |

Sampler row (class (c)): P1 chain-rule sampling, N=10⁵, scored by the independent scorer against
O1's law — universal-mixture e-process below the 1/α=1000 rejection threshold; empirical TV
within the registered project band.

## Independence chain

Four structurally independent implementations now agree exactly on the frozen laws: O1 (Builder
A, rational trajectory enumeration), O2 (Builder B, dense probability-vector instrument chain;
agreement ≤ 1.11e-15 per entry vs gate 1e-13), P1–P3 (Builder C, from declarations only — the
candidate script provably reads no artifact files), and the un-led reviewer's own fourth
brute-force enumerator (8 laws, 3 deltas, μ(r*), all P4 verdicts re-verified). Chronology
audited by the reviewer: spec freeze 08:03Z → ORACLES_AGREE 08:21Z → Amendment 1 registered
08:22:58Z before F1b computed → amendment gate + rehash 08:32Z → candidate build 09:29Z →
scorecard 09:34Z. Post-amendment artifact pins: `o1_artifacts.json` sha256 def7f674…bbc9c2e (sic:
def7f6741acdaf11570232b122cf90c0f8dd1c274bb2e6991f252bf4bfb49c2e), `o2_artifacts.json`
3aa403314d053999b8176931e17bf618f7d43b13bfc9ce6a3ea51c8a707c0e0d.

## Preregistered class-(a) rows — all PASS (exact)

A1 closure structural zeros (F1/F3); A2 F2 support law (8-point support, off-support mass
exactly 0); A3 rival cross-round independence (exact factorization); A4 RESET product law; A5
gauge invariance (C7b bit-identical); A6 normalization exactly 1; A7 μ(r*) =
74993015823674485463778145545999 / 25·10⁴⁶ ≈ 2.9997×10⁻¹⁶ > 0 with the pre-written witness
trajectory as a verified lower-bound term. Amendment rows: A8 per-round detector-block laws of
F1b_iid equal F1_mem exactly (all three rounds); A9 exact cross-round independence of F1b; A10
closure zeros.

## Preregistered class-(b) bands — outcomes (misses are findings; nothing re-banded)

| Band | Value | Outcome |
|---|---|---|
| B1 TV(F1_mem, F1_iid) ∈ [1e-4, 1e-1] | 0.05814748… (exact fraction recorded) | IN BAND |
| B1 second clause (single-round SYNDROME_DIST ≤ 1e-12) | round-2 block TV 9.747e-3, round-3 1.528e-2 | **MISS — prereg-drafting finding**: per-qubit-rate matching ≠ detector-marginal matching (detector firing nonlinear in rate). Remedied additively by Amendment 1 (F1b), not by re-banding |
| B2 RR_CORR(F1_mem) ∈ [1e-3, 0.3]; strictly positive | 0.050858…; (r1,r2) covariances exactly 0 (π=(1,0) makes m₁ deterministic) | IN BAND; "strictly positive" holds for (r2,r3) only — tallied as a band-note (reviewer F-4) |
| B3 μ(r*) ∈ [1e-17, 1e-15] | 2.9997×10⁻¹⁶ | IN BAND |
| B4 HOLD exchangeability defect ∈ [1e-4, 1e-1] | 0.1456016865772833 (exact fraction) | **MISS (above band by ~1.46×)** — fixture-band finding; both oracles agree; recorded, not re-banded |
| B4 ADVANCE vs HOLD > 1e-6 | 0.048378… | PASS |
| B5 closure activation ∈ [1e-3, 0.2]; feedback TV > 1e-4 | 0.0336; 0.037512 | PASS |
| B1b TV(F1_mem, F1b_iid) ∈ [1e-4, 1e-1] (amendment) | 0.02600685688369913 (exact fraction) | IN BAND — discrimination now provably cross-round + observable only (by A8) |
| B6 observable-marginal gap ∈ [1e-5, 1e-1] (amendment) | 0.004457628 (exact 1114407/25·10⁷) | IN BAND |

## Corruption battery — every row tripped (corrupted fires, clean passes)

C1 (operand swap): TV delta 0.07750078…, 64 changed entries — exact match to precomputation.
C2 (constant flip): exact match. C3 (row reorder): identity hash changed, law bit-identical
(inert-by-design pair behaved). C4 (undeclared reset): delta 0.05877090…, exact match — with the
correction that C4 *also* moves round-2/3 block marginals (TVs 0.04503/0.031521), so the prereg's
"catches marginal-only validators" clause was wrong for this corruption (reviewer F-3; recorded).
C5 (shot-order permutation): closed at candidate level — P1-variant law equals O1's C5 law
exactly; defect TV exactly 0.1456016865772833; declared order reproduces F5_HOLD with defect
exactly 0. C6 (contract relabel): validator rejection record emitted; no law computed. C7a
(evaluator-truth leak): delta 0.13710837…, exact match. C7b (gauge): bit-identical (A5). C8
(silent truncation): closed at candidate level — truncating P1 variant sends μ(r*) to exactly 0
and reproduces O1's F3_C8 law bit-identically (61 surviving terms, mass deficit ≈1.1457×10⁻⁹);
exact-tier comparison flags 128 entries incl. r*; normalization check fails. C9/C9b (silent
substitution): deltas equal B1/B1b values exactly. Structural-zero pseudocount falsifier:
floored F2/F1_mem laws fail A2/A1 exactly (mass 504/10³⁰ and 384/10³⁰); clean pass.
Normalization falsifier: +1/10¹⁵ single-branch perturbation detected exactly; clean sums to 1.

## Reviewer findings and dispositions

F-1 (C5/C8 candidate-level trips missing) — **closed** by `e1_stage2/close_f1_f2_trips.py`
(T1/T2, exact values above). F-2 (two never-run §3a falsifiers) — **closed** (T3/T4). F-3
(prereg C4 marginal clause wrong) — **accepted as a prereg-drafting erratum**; recorded here;
the registered text is not rewritten. F-4 (B2 strict-positivity sub-clause) — tallied above.
F-5 (in-place artifact overwrite during Amendment 1) — process note accepted; mitigated by the
comparator's value-level re-verification and post-amendment hash pins; future amendments should
version artifacts. F-6 (band misses must travel) — implemented: this result carries both misses;
any downstream consumer must cite them. F-7 (vocabulary/bookkeeping observations) — recorded in
`e1_stage2/review/REVIEW.md`.

## What E1 does NOT claim

No scaling behavior; no family qualification beyond the nine frozen instance laws; no
`FULL_RECORD_LAW_CERTIFIED` assurance beyond the enumerated instances themselves; no statement
about quantum-memory cells (all E1 instances are classical-latent); no physical-mechanism or
calibration claim (all fixtures are controlled, parameters declared); no endorsement of any
scaled solver. The B4/B1-clause misses are findings about fixture/prereg design, not about the
simulator. Sampler evidence is class-(c) statistical, not generator-bias certification.

## Artifact inventory

`e1_stage1/`: `o1_exact_rational_oracle.py`, `o2_dense_instrument_oracle.py`,
`o1_artifacts.json` (def7f674…), `o2_artifacts.json` (3aa40331…), `stage1_compare.py`,
`stage1_comparison.json`, `stage1_compare_amend1.py`, `stage1_comparison_amend1.json`.
`e1_stage2/`: `candidate_primitives.py`, `candidate_outputs.json`, `score_candidates.py`,
`stage2_scorecard.json`, `close_f1_f2_trips.py`, `f1_f2_closure.json`, `review/REVIEW.md`,
`review/reviewer_recheck.py`, `review/reviewer_recheck_results.json`.

## Downstream

E2 (production-sampler substrate qualification), E3 (G-A certificate theorem test bed), and E4
(analytic-cell derivation notes) may now consume the frozen oracle artifacts, subject to: citing
the two band misses; treating the F1 rival as per-qubit-rate-matched (use F1b for
marginal-matched claims); versioning artifacts on any future amendment. Committing the E1
scripts into the tracked tree (they currently live under gitignored `outputs/`) is an owner
decision.
