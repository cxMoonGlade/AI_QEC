# E4 analytic record-law cells (RTN + Gaussian dephasing) — RESULT

Date: 2026-08-04. Preregistration:
`TEMPORAL_MEMORY_E4_ANALYTIC_CELLS_PREREG_2026-08-04.md` (gate: pass; sha 9aa2c163…). Closure:
`outputs/temporal_memory_survey_2026-08-04/E4_CLOSURE_REPORTS.md` (sha fb346f63… at freeze;
post-review erratum appended, see below). Artifacts:
`outputs/temporal_memory_survey_2026-08-04/e4/` (notes, decoupled-variant calibration with
sealed key, checker reports, numerics + closure runs, un-led review). No `src/**`.

## Verdicts

**Both cells VERIFIED (un-led review: VERIFIED-WITH-FIXES; every fix subsequently executed and
closed).** Kill conditions K1/K2/K3 fired nowhere against registered targets.

- **A1 — RTN record law.** The joint N-outcome law of repeated Ramsey blocks under a single
  classical telegraph is exactly
  `P(m_1..m_N) = 1ᵀ [Π_k B_{m_k}(τ_k) D(δ_k)] π`, `B_± = ½[T ± Re K]`, with K the PUBLISHED
  endpoint-resolved kernel (Cheng–Wang–Joynt PRA 78, 022313; BGA Eqs. (30)–(32); Ramon PRB 92,
  155422) — the kernel is cited, never claimed. Claimed increment exactly as frozen: the
  N-outcome kernel-product (HMM) record law + QEC Record framing + multi-qubit
  common-fluctuator extension. Anchor reductions symbolic-exact: N=1 → BGA Eq. (35); echo →
  BGA Eq. (41). Reviewer re-derived the Re-K core (why no separate conjugate block is needed)
  and the (3ⁿ+1)/2 state-count bound; 36/36 re-derivation rows passed.
- **A2 — Gaussian record law.** The Walsh-inversion assembly lemma
  `P(m) = 2^{−N} Σ_S (Π_{k∈S} m_k)·C_S`, each C_S an explicit finite combination of single
  Gaussian characteristic functionals — OUR lemma, citing Sakuldee–Cywiński PRA 101, 012314
  Eqs. (6)/(7)–(11)/(19)/(22)–(28) for every ingredient (never attributed to them); n=2 reduces
  symbolically to Fink–Bluhm Eq. (2) (with the corrected Eq.-numbering erratum e1).
  Parity coefficients = single functionals ⇒ closed-form `EVALUATE_FUNCTIONAL` at any N.
- **Attribution audit (reviewer): clean — no inflation**; both notes claim exactly the frozen
  §-1 increments.

## Verification chain

- Calibration 2/2 full credit (decoupled variants per the E3 design fix; flaws localized at the
  key's exact step and mechanism; no FLAWED verdict against a real note). Residual design
  caveat: the `calib/` path leaks which doc is the variant — calibrates localization, not
  detection-in-the-wild (carry to the next iteration).
- Numerics (frozen instances RTN-I1 γ=0.3, v=1.0 oscillatory; RTN-I2 γ=1.0, v=0.6; GAUSS-I1 OU
  σ=0.8, τc=2.0; N=6): normalization ≤1.6e−50; independent ODE oracle ≤8.4e−53; anchor rows
  ≤6.7e−51; positivity structural; byte-identical rerun; reviewer's independent law
  re-implementation: zero float64 discrepancy on all three 64-point laws. Gaussian-MC
  discretization ledger honest (trapezoid-Σ verified by brute force; h² rates; Richardson
  4.1e−15; KL(P_h‖P)=1.7e−14).
- Corruption battery (all trips executed): γ↔2γ kernel swap crossed at 304 (budget 20 725);
  dropped cross-covariance at 134 (22 994); third registered row at 1 094 (77 286);
  parity-relabel (G9a closure) at 8 (449) with clean-sanity max logE −2.09; layout-identity
  (G9b closure) — see finding below. All KLs/budgets independently recomputed.
- G10 closure: a FROM-SCRATCH dense instrument-chain oracle (qubit ⊗ fluctuator, self-built
  16×16 vectorized Lindbladian, trace-preservation residual exactly 0, subnormalized instrument
  branches, 60-dps expm) agrees with the analytic kernel-product law at N=3 to **3.89e−62**
  (RTN-I1) and **9.72e−63** (RTN-I2) against a 1e−20 gate.

## Registered findings

1. **G9b structural finding (honest premise correction):** on the frozen RTN-I1 the record law
   depends on outcome popcount only (i.i.d. collapse of the pinned cell, note A1 §9), so the
   bit-reversal layout corruption FIXES the law exactly (TV ≈ 3.9e−52) — exactly the E1-C3
   "inert-by-design + identity-hash-must-change" pattern, and the hash trip fired
   (23951c37… → 2bccb349…). The statistical LR trip was additionally executed on a declared
   symmetry-broken vehicle **RTN-I1-LV** (non-palindromic τ schedule, inside the declared A1
   cell; execution-time vehicle addition, recorded as such): 56/64 entries change, TV = 0.4501,
   crossed at 13 (budget 788). Lesson recorded: exchange-symmetric fixtures cannot discriminate
   layout permutations statistically — falsifier design must include a symmetry-broken vehicle.
2. **G8 closure erratum (appended, not rewritten):** C-1's CWJ eigenvalue transcription had a
   spurious γ; the actual display is `λ = γ − iB₀m ± √(γ² − g²m² − 2igηm)` (pixel-confirmed).
3. Survey-record errata e1–e3 (Fink–Bluhm Eq. numbering; Layden order O(t^q), q = 2^{n−1}−1;
   BGA conventions) discharged in the prereg §0 and the notes.
4. Documentation nits (A2 §7 bands ±9.6e−4/±7.1e−4 — conclusions stand under the tighter bands;
   SC Eq. (30) added to the citation-debt ledger; A1 W3 instance parameters recorded in the
   post-review append, with the authoritative source noted as `e4/writer_checks_A1/verify_a1b.py`).

## What the cells buy ECS

Two production-grade analytic cells with published anchors: closed-form
`EVALUATE_FUNCTIONAL` at any N (both cells), exact `SCORE`/`ENUMERATE` at small N (kernel
products / Walsh inversion), exact two-stage `SAMPLE` (E2 discipline; circulant embedding for
the Gaussian cell), and — the program purpose — an ANALYTIC oracle family that is structure- and
code-path-independent of O1/O2 for every future falsifier battery. Continuous-time exact:
`time_discretization = EXACT_ZERO` in the ledger for the analytic laws.

## Citation-hygiene debts before any external writeup

SC 1907.01784 equation numbers vs published PRA PDF; Fink–Bluhm PRL supplement; SC Eq. (30);
Kubo/Anderson 1954 (SECONDARY only); grade-B pins from `E4_CLOSURE_REPORTS.md`; the E3 ledger's
existing debts (Werner erratum vs PRL supplement, etc.) remain separately tracked.

## Program status

E4 completes the survey's experiment set: E1 (exact core qualified) → E2 (production sampler
substrate qualified) → E3 (certificate theorem layer proved, boundary fixed) → E4 (analytic
oracle cells verified with honest priority). All three survey directions now have executed
anchors. Open registered items: nondeterministic-measurement cell (E2 debt), PECOS leg redo,
strategy-norm chaining hypothesis CH, a-priori (pre-run) certificates, external paper writeup
(after the hygiene ledger clears).
