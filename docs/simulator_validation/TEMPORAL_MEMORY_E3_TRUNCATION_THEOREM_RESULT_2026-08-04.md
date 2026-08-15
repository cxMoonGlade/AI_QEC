# E3 measurement-interleaved truncation theorem (gap G-A) — RESULT

Date: 2026-08-04. Preregistration:
`TEMPORAL_MEMORY_E3_TRUNCATION_THEOREM_PREREG_2026-08-04.md` (gate: pass; sha cdbde733…).
Closure input: `outputs/temporal_memory_survey_2026-08-04/E3_CLOSURE_REPORTS.md` (sha cf7e1b4e…).
Artifacts: `outputs/temporal_memory_survey_2026-08-04/e3/` (proof notes, planted-flaw calibration
with sealed key, adversarial checker reports, numerical test bed + results, un-led review). No
`src/**` changes. Every verdict below is the un-led reviewer's, issued after 4/4 checker
calibration passed and after the reviewer independently re-derived the load-bearing chains.

## Verdicts (per registered target)

| Target | Verdict | Content |
|---|---|---|
| **T1** mass-aggregated leaked-mass lemma | **PROVED** | Subnormalized branch trees; arbitrary per-branch perturbations of trace-norm size η_{b,t}; `TV(μ, μ̃) ≤ ½·Σ_{t,b} η_{b,t}`; CP-TNI transport (erasure-completion argument), block additivity over the record tag, pinching readout; equality mechanism exhibited and realized (all 18 classical test-bed rows sit in the equality class) |
| **T2** instrument telescoping compile | **PROVED** (compile) | Adaptive instrument sequences, fixed-map diamond errors ⇒ record-law TV ≤ ½Σε_t; the AKN + Watrous Eq. (3.306) + Thm 3.52 stack compiled with instruments-as-QC-channels and feedback-as-controlled-channels; K3 discharged. Strategy-norm per-round chaining delivered as a *conditional* corollary (hypothesis CH; two grade-B locators) — registered as not-yet-verdict-grade |
| **T3a** branch-dependent truncation runtime certificate | **PROVED** (the research core) | State-dependent per-branch truncations, runtime-measured; Lemma A subnormalized Hölder `‖XX†−YY†‖₁ ≤ (‖X‖₂+‖Y‖₂)‖X−Y‖₂` (tight at Y=cX); Lemma C.2 aggregation `Σ_o ‖M_o(Y)‖₁ ≤ ‖Y‖₁` (the genuinely new step); prefix-fixed adaptivity lemma; hypotheses H1 (no branch merging) and H2 shown **necessary** by valid counterexamples. Result: local truncation data ⇒ joint-Record-law TV bound, a-posteriori, for instrument-interleaved evaluators |
| **T3b** conditional-query boundary | **COUNTEREXAMPLE-ESTABLISHED** | Explicit E1-sized instance: joint law obeys T3a while the conditional law given prefix E is off by exactly `2·(mass)/μ(E)` (8110× at μ(E)=2.5e-4, exact sweep, ratio 1 to the closed form); certificate-invariance theorem (no certificate depending only on truncation-mass data can help); escape hatches (1/p factor; multiplicative-error structure; anticoncentration) classified at three graded strengths |
| **T4** randomized/unbiased truncation | **PROVED** (assembly + obstruction) | Rhee–Glynn/Jacob–Thiery unbiased Record-functional estimation with the variance condition; sign obstruction instantiated (exact negative-output instance −0.28 from naive Russian-roulette on a branch tree); Bernoulli-factory escape stated via JT Thm 3.1 (connects gap G-G) |
| **T5** near-deterministic-measurement route | **PROVED within declared boundary** | Prop T5.3 / Cor T5.4: OV/KMW union-bound composition with T1 bookkeeping for projective near-deterministic syndrome extraction; boundaries pinpointed honestly — Gao's general-instrument problem sidestepped (not solved), and the reference-state mismatch blocks a runtime union-bound certificate |

## Quality evidence

- **Adversarial checking with planted-flaw calibration: 4/4 PASS** — each checker identified the
  planted document and the exact fatal step (three found refutations different from the key's
  own), and no FLAWED verdict was issued against a real note; all GAPS adjudicated valid and
  non-fatal.
- **Numerical validity (K1 never fired):** zero-truncation control exact (512 keys × 3
  instances); 18/18 classical rows VALID (equality class — a stringent η-bookkeeping check);
  quantum-memory toy validity ratio 0.783 with near-tight Hölder chain; **wrong-bound control
  fired** on the quantum toy (naive unweighted local bound violated ×5.27) after a structural
  proof that classical drop-only fixtures *cannot* fire it (registered fallback used as
  preregistered); T3b amplification sweep exact. The reviewer reproduced the numerics with an
  independent implementation.
- **Un-led review:** reviewer re-derived T1's full chain, Lemma A, Lemma C.2, the induction, and
  T3b's closed forms before issuing verdicts.

## Erratum-grade side discovery

**Werner et al. arXiv:1412.5746v2, Lemma 1: the √2 constant is false as published** — the proof
step needs `Re⟨X|Y⟩ ≤ |⟨X|Y⟩|²`, which fails in general; an overlap-½ counterexample gives √3 >
√2; the correct general constant is 2. E3's results do not depend on it (Lemma A is
self-contained), but the survey's L-B verification grade for that lemma was overclaimed —
recorded as an erratum row in the citation-hygiene ledger. Downstream effect on Werner's Thm 7
constant: ≈6√2 in place of 6 (reviewer's estimate, not re-derived to publication grade).

## What this closes and what it does not

Closed: survey gap G-A in its registered form — the local-truncation → joint-Record-law bridge
EXISTS as a runtime (a-posteriori) certificate for subnormalized instrument-interleaved
evaluators, with the conditional-query boundary provably fixed at 1/p. Direction 3's keystone is
in place: K5/K6-style truncated machinery can now, in principle, carry
`BOUNDED_APPROXIMATION`-class Record-law claims by tracking per-branch dropped mass —
**provided** outputs are joint laws (not renormalized conditionals) and truncation never merges
record branches (H1).

Not closed / registered debts: strategy-norm chaining (conditional, needs CH + locator
upgrades); T5 beyond projective near-deterministic measurements (Gao's problem stands); a-priori
(pre-run) bounds — everything here is a-posteriori; the fixture-level branch-merging control was
discharged analytically, never run (track before citing "all controls executed"); the
inequality-direction separation rests on a single quantum fixture (thin for external writeup);
grade-B citation pins (BBCCGH Eq. 10, Gao, AA, PBG, Harrow–Lowe versions) + KSV §11 check +
Werner erratum verification against the PRL supplement — all owed before any external
publication; calibration-design note (variants must be decoupled from originals so the flaw is
not diff-recoverable).

## Downstream

E4 (analytic record-law cells) remains the open survey follow-up; the E3 theorems give the
certificate vocabulary that a future truncating production evaluator (Direction 1 at scale, or
K5/K6 machinery) must implement: per-branch dropped-mass ledgers, H1 compliance, joint-law-only
claims, T3b-aware conditional-query refusal semantics. An external-writeup path (paper) now has
a complete skeleton: T1/T2/T3a/T3b/T4 + the numerical validity study + the Werner erratum.
