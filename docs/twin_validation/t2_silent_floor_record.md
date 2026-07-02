# T-#2 record — the exact interpolating silent-floor functional (2026-07-02)

**Tracked record for the #2 deliverable** (HANDOFF_math_spine §3 T-#2). Full statements + proofs in
the gitignored draft `docs/coupling_simulator_intro_draft.tex` §`sec:silent-floor`; verification
script `outputs/t2_silent_floor_verify.py` (+ logs) is the local audit trail. Builds on the T-B
probe calculus (`sec:ident-gauge`, record `tb_ident_gauge_theorem_record.md`).

## Positioning (cite-don't-claim; adjudication #2.1 [PROVISIONAL] no-owner)

Clader 2101.11631 owns the binary fixed-marginal Gaussian-moment endpoints incl. the literal
15 = (2d−1)!! (精读 note committed); Regev 2605.03054 owns the nearest closed form (i.i.d. Pauli +
one global Bernoulli mode; no interpolation parameter, no derivative metric). Ours = the
arbitrary-Σ interpolating functional (finite Gaussian-CF Fourier sum) + the metric structure.

## Results claimed (epistemic classes)

| # | Statement | Class |
|---|---|---|
| F1 | Exact functional: F(Σ) = P(all detectors quiet ∧ obs flip) = P(m̄=0, x=1⃗) = 2^{−kR−n}Σ_{u,χ}(−1)^{χ·1}W(u,χ) = finite Fourier sum of Gaussian CFs e^{−½âᵀΣâ} with machine coefficients, arbitrary Σ, dressings included | (a) proven (Walsh inversion + Lemma A) |
| F2 | Hafnian leading law: F = 4^{−n}Σ_r E[Π_q θ_{q,r}²](1+O(Σ)); n=3 uniform-ρ pinned-marginal curve = σ⁶(1+6ρ²+8ρ³) — Clader's 15 decomposes as 1+pair(6)+triangle(8); n=2 curve = σ⁴(1+2ρ²) → 3 | (a) proven (single-round collective-flip dominance + Isserlis) |
| F3 | Metric theorem: ∂F/∂f\|₀ = 0 EXACTLY at every σ and every dressing (per-qubit re-signing gauge is odd on every cross-qubit grade two-point function at f=0) ⇒ honest device metric = ∂²F/∂f²\|₀ (coefficient 6, n=3 uniform) + the f³ triangle term (coefficient 8, first loop-sign carrier). Refines the "∂(floor)/∂f\|₀" language of the adjudication: the first derivative is an exact zero, a theorem not a small number | (a) proven (gauge corollary) |
| F4 | Scissors coherence: floor rises O(C²) while detection rate falls O(C²) (T2 quieting) — joint analytic statement | (a) corollary |
| F5 | Measured instance: ×15.9 (R=20, N=1e6, grounded OU + seam, registered band [3,30]) = committed tier-1 result; +6% over asymptotic 15 = finite-σ/seam correction | measured (committed log), cited not rerun |

## Registered verification bets (committed BEFORE the run)

Script: `outputs/t2_silent_floor_verify.py`. Machine side = the verified brute-force record-law
engine (T-B); independent route = per-φ exact conditional amplitudes + Monte-Carlo φ-average
(different mathematics; 3 seeds). Gates declared: (a)-exact limits carry (c) convergence gates.

- **S1 (hafnian curve, n=3):** p's=0, R=2, block-diagonal Σ, pinned σ², uniform ρ ∈
  {−0.4,−0.25,0.25,0.5,0.75,1}: F(ρ)/F(0) → 1+6ρ²+8ρ³ on a σ-ladder {0.4,0.2,0.1}; gates:
  relative error at σ=0.1 < 3e-2 AND monotone shrinking along the ladder.
- **S1b (n=2):** same with law 1+2ρ² (endpoint 3).
- **S2 (endpoint):** ρ=1 → 15 (n=3) within the same gates — the Clader-limit contact (cited).
- **S3 (metric):** at FIXED finite σ=0.3, cross-scale c: odd part F(c)−F(−c) has local log₂-slope
  ∈ [2.9, 3.1] (pure c³; NO linear term — the exact-vanishing theorem), even part slope ∈
  [1.95, 2.05]; repeated at nonzero dressings (p_M=0.011, p_F=0.007, p_Z=0.0034); leading
  coefficients: odd(c)/(F(0)c³) → 8, even(c)/(F(0)c²) → 6 within 10% at c=0.05, σ→0.1.
- **S4 (gauge instance):** F invariant under an admissible suffix re-signing (relative < 1e-12);
  a non-admissible ε moves F (relative > 1e-6).
- **S5 (temporal sensitivity):** adding a cross-round block changes F (relative > 1e-6) — the
  arbitrary-Σ axis beyond the single-shot spatial family.
- **S6 (independent route):** graded-sum F vs conditional-amplitude MC (N=4e5 φ-samples × 3
  seeds, p's=0): agreement within 3 MC-σ, and MC-σ/F < 2%.

## Amendment A-T2-1 (2026-07-02, after run 1 — registered S1b FALSIFIED; leading law CORRECTED;
committed before the rerun)

**Run-1: 15/16 PASS; S1b (n=2 law 1+2ρ²) FAILED at rel err 0.327** — and the failure pattern
diagnoses the root cause exactly: at ρ=1, R=2 the machine gives ratio 4 vs predicted 3. The
same-round-only assumption in F2 was WRONG: collective-flip amplitudes at different rounds are
indistinguishable by every detector and add COHERENTLY before squaring. **Corrected F2:
F → 4^{−n} E[(Σ_r Π_q θ_{q,r})²]** — diagonal = hafnian rate terms (the old law); off-diagonal =
cross-round interference: vanishes for ODD n at zero temporal correlation (odd Gaussian moments —
why the n=3 curve 1+6ρ²+8ρ³ converged untouched, rel err 9.9e-3 ~ σ²), survives for EVEN n
(n=2 block-diag: 1+(R+1)ρ² — R=2 gives 4 at ρ=1 ✓ matches the falsification exactly) and for any
n with temporal correlation. **New physics content: the silent floor is a coherent accumulation
across rounds — a rate-based/factorized simulator produces the diagonal only; the floor's
R-growth at fixed per-round statistics (S1c: n=2, R=3 → 1+4ρ²) is the falsifiable signature.**
Bets amended: S1b → corrected law; S1c added (R-scaling). n=3 curve, metric theorem (F3),
S2–S6: unchanged, already green in run 1.

## Results (appended after the rerun)

*(pending)*
