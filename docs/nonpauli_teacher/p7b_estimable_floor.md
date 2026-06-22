# P7b — Estimable Bayes floor at large R (the ⑦ floor-artifact fix + core scoring capability)

**Status:** pre-registration / build spec. Theory-first: the math + the falsifiable prediction
are fixed here BEFORE any run. Supersedes the in-sample plug-in floor used in
`p7_leakage_headroom_prereg.md` / `p7_decision*.py`.

**One-line:** the ⑦ NOT-CAPPED verdict was an artifact of a **down-biased in-sample Bayes-floor
plug-in** at R=5 (red-team af7c9b, 2026-06-21). This doc specifies an **unbiased, estimable**
floor (exact-per-sample Monte-Carlo, DM-evaluated), validated against exact enumeration, graduated
to `src/qec_twin/audit/` as core scoring infra (the gap-to-Bayes is needed for every axis,
binary AND soft). It then re-decides the binary-leakage capped/not-capped question definitively.

---

## 0. Why (the red-team finding)

The Bayes floor for the logical decision from the syndrome history is

> `F(R) = Σ_s min( P(s, f=0), P(s, f=1) )`,  s ∈ {0,1}^(8R), f = logical flip.

Equivalently `F = E_{s∼P(s)}[ min(P(0|s), P(1|s)) ] = P(f ≠ f*(s))`, where `f*(s)=argmax_f P(f|s)`
is the Bayes (optimal) decoder. `F` is the smallest achievable LER; `gap = LER_decoder − F ≥ 0`
is the headroom. `gap_leak = gap(bg+leak) − gap(bg)`; `τ_cap = 2e-3` absolute / `5%` relative.

**The artifact.** The build estimated `F` by the **in-sample plug-in**
`F̂_in = Σ_s min(n(s,0), n(s,1)) / N`. In the under-sampled regime `2^(8R) ≫ N` (at R=5: 2^40 ≫ N,
collision_frac 0.72–0.92), most syndromes are singletons → `min(n(s,0),n(s,1)) = min(1,0) = 0` →
the plug-in **under-counts** the overlap → **`F̂_in` is down-biased**. Evidence (red-team): `F̂_in`
**rises monotonically with N** (0.00171 → 0.00204 → 0.00236 over N = 1e5 → 3e5 → 1e6 at R=5) — a
model-free proof it has not converged and the true `F` is strictly higher. A floor that is too low
**inflates** `gap = LER − F` → a **false NOT-CAPPED**. (The prereg's "down-biased floor ⇒ verdict is
conservative" was backwards for *not-capped*: a low floor makes not-capped *easier* — a false positive.)

---

## 1. The valid bracket (exact, identity-grade)

Two cheap estimators bracket the truth:

- **In-sample plug-in** `F̂_in` — assigns each syndrome to its in-sample-majority class and scores on
  the *same* data ⇒ optimistic ⇒ **`E[F̂_in] ≤ F`** (down-biased; the artifact).
- **Cross-fit / held-out** `F̂_cv` — fit `f̂*(s)` on a train split, score on a disjoint test split.
  The fitted decoder is suboptimal (finite train) ⇒ its true error `≥ F` ⇒ **`E[F̂_cv] ≥ F`** (up-biased).

So `E[F̂_in] ≤ F ≤ E[F̂_cv]`, and the **true gap lives in `[LER − F̂_cv, LER − F̂_in]`**. The red-team's
R=5 bracket `[~0.0012, ~0.0033]` **straddles `τ_cap`** ⇒ UNDECIDED with the in-sample estimator. This
is a *valid* but *loose* bracket. We need an estimator that pins `F` directly. **(epistemic class: exact —
a sample-splitting identity; the only thing both arms assume is i.i.d. shots.)**

---

## 2. The core method — exact-per-sample Monte-Carlo floor (UNBIASED)

The plug-in's bias comes entirely from estimating `P(f|s)` by **counting** (singletons → 0/1). We remove
it by evaluating `P(f|s)` **exactly** per sample from the certified DM oracle (the exact teacher
distribution; the DM is the exact evolution under the #11 L1 independently-verified components —
schedule byte-identical to the raw `.stim`, leak dynamics / WG slice vs a from-scratch oracle,
⟨S⟩/logical/detectors vs stim. The `1.5e-18` is the parsing/geometry cert, not a
DM-output-distribution-vs-circuit residual; the leakage is INJECTED by our WG model, so there is no
external circuit-leakage distribution to certify against — the faithfulness IS component-wise).

**Estimator.** Draw `s_i ∼ P(s)` (Born-branch the DM down a random measurement path, or reuse MCWF
syndromes — both are exactly `∼P(s)`). For each path keep the **unnormalized** conditional DM `ρ_{s_i}`
(`tr ρ_{s_i} = P(s_i)`); then `P(s_i,f) = tr(Π_f ρ_{s_i})` with `Π_f` the logical-observable projector, and

> `F̂_mc = (1/N) Σ_i  min( P(s_i,0), P(s_i,1) ) / tr(ρ_{s_i})  =  (1/N) Σ_i min(P(0|s_i), P(1|s_i))`.

**Unbiasedness (proof).** `E_{s∼P}[min(P(0|s),P(1|s))] = Σ_s P(s)·min(P(0|s),P(1|s))
= Σ_s min(P(s,0),P(s,1)) = F.` Each summand is computed **exactly** (DM path-propagation), so the only
error is **MC variance** `Var ≤ (1/N)·Var_s[min(·)] ≤ 0.0625/N` (min ∈ [0,½], usually ≈0 since most
syndromes are decisive ⇒ small effective variance). **No singleton/sparsity down-bias.** This is the
fix — *not* a less-biased plug-in, an *unbiased* estimator. **(epistemic class: exact estimator +
honest MC band.)**

**Independence (FAITHFULNESS rule I).** This is **not** circular self-validation: the engine's
faithfulness is established **component-wise** by the #11 L1 independent lane (vs the raw `.stim` + a
from-scratch oracle — schedule byte-identical, leak dynamics |2⟩(R) to 1.4e-15, WG slice exp(L/4) to
1.75e-13, ⟨S⟩/logical/detectors vs stim; the `1.5e-18` is the parsing/geometry cert, not a
DM-output-distribution-vs-circuit residual, and the leakage is INJECTED by our WG model so there is no
external circuit-leakage distribution to certify against); given that, the DM *is* the exact teacher
distribution, and `F` is a property *of that distribution*. We additionally validate `F̂_mc` against
**exact enumeration** at R=1 (§4 L1).

**Feasibility (to profile in the build, GPU-only).** `F̂_mc` costs `N` DM path-propagations to R rounds
(each = R within-cycle channel applications + syndrome projections on the 3^9 DM). Budget knobs the build
must report: complex64 vs 128, path batching `B` (B DMs in a batch tensor), `N` vs target SE, and the R
range that fits wall-clock. **Fallback if R=5 DM is too slow:** exact-MC at R≤3 (cheap) to establish the
*exact* `F(R)` trend, + `F̂_cv` at R=4,5 **calibrated to F̂_mc at R=3** (validated, not assumed), + the
`[F̂_in, F̂_cv]` bracket. The verdict (§5) is then driven by the exact small-R trend + the flat |2⟩(R).

---

## 3. Placement (core scoring infra → src/, per the "core in src/" rule)

**Backend-agnostic (HARD — no d3-only dead-end, ADR 0008).** The MC floor LAYER (sample s∼P(s),
average `min(P(0|s),P(1|s))`) is substrate-independent. The per-sample `P(f|s)` evaluator is a
**pluggable backend** behind one interface, e.g. `PathJointEvaluator.path_joint(path, R) -> (P(s,0),
P(s,1))` (unnormalized joint along a syndrome path). `mc_floor`/`plugin`/`crossfit`/`convergence` call
ONLY this interface — never the DM directly. Backends: **(i) `DMPathEvaluator`** = the 3^9 density-matrix
= the d3 **exact certification ORACLE** (feasibility-only; 3^25 explodes at d5); **(ii) TN/MPDO** =
the scalable carrier (matrix-product density operator / locally-purified TN for the mixed leakage state)
= the d5/d7 workhorse, **faster even at d3** (area-law locality ≪ the full 6GB DM), **certified vs the
DM oracle on the d3 rung** (no exact oracle exists at d5 — the rung ladder IS the certification, per
FAITHFULNESS rule I). Speed and scale are the SAME lever = the carrier; the DM is kept only as the oracle.

Graduate from the gitignored `outputs/` one-off scripts into tracked `src/`:

- `src/qec_twin/audit/bayes_floor.py` — **NEW**. `mc_floor(...)` (the exact-per-sample MC),
  `enumerate_floor(...)` (exact, R small), `plugin_floor(...)` + `crossfit_floor(...)` (the bracket),
  `floor_convergence_report(...)` (the no-drift tripwire). Returns `F̂`, MC SE, the bracket, and the
  convergence flag. (`audit/` already owns gating/bands/validity — the floor is a validity capability.)
- **the seam** (teacher shots → detector-events + the round-to-round XOR convention) → graduate the
  verified G2 logic to `src/qec_twin/` (forward/scalable output adaptor or `decoder/` I/O), with its
  raw-circuit-detector control as a test. Used by every decoder/learner downstream.
- `tests/test_bayes_floor.py` — the L1–L6 ledger as executable tests.
- `outputs/teacher_prereg/p7b_*.py` — the **analysis/decision** harness (one-off; stays gitignored):
  runs the graduated `src/` capability across R, emits the bracket/convergence plots + the verdict JSON.

---

## 4. Constraint ledger (physical/statistical invariants + a falsifying test each — BEFORE building)

| # | Invariant | Falsifying test (must FAIL LOUDLY when violated) |
|---|-----------|--------------------------------------------------|
| L1 | `F̂_mc(R=1)` = exact enumeration over all 2^8 syndromes (independent ground truth) | mismatch > 3·MC-SE ⇒ fail; assert on a from-scratch enumerator, not the engine's own min |
| L2 | `F̂_mc` does **not** drift with N (unbiased), unlike `F̂_in` which must rise | fit `F̂(N)` slope; `F̂_mc` slope ≈ 0 within SE, `F̂_in` slope > 0 (positive control that the tripwire works) |
| L3 | `F̂_in ≤ F̂_mc ≤ F̂_cv` (MC lands inside the valid bracket) | `F̂_mc` outside `[F̂_in, F̂_cv]` by > SE ⇒ fail |
| L4 | broken-decoder positive control: a deliberately-scrambled decoder ⇒ `gap ≫ 0`, **floor unchanged** | floor moves with the decoder, or gap stays ~0 ⇒ fail (floor must be decoder-independent) |
| L5 | observable alignment: the floor uses the **logical flip** `m` (the seam's observable), not raw syndrome parity | floor computed on a wrong observable ⇒ disagrees with the seam's planted-fault control ⇒ fail |
| L6 | CPTP / probability sanity along every path: `0 ≤ P(s,f)`, `P(s,0)+P(s,1)=P(s)`, `Σ_paths P(s)=1` (sampled) | any negative / normalization residual > 1e-9 ⇒ fail |

---

## 5. Decision rule (heuristic gate — class (c))

Per R, with the MC SE → a CI on `gap_leak(R)`:
- **CAPPED** if `upper-CI[gap_leak(R)] < τ_cap` for all tested R (no R-growth).
- **NOT-CAPPED** if `lower-CI[gap_leak(R)] > τ_cap` for some R **and** `gap_leak` grows with R.
- **UNDECIDED** if the CI straddles `τ_cap` ⇒ increase N (the MC SE shrinks as 1/√N — no bias wall,
  unlike the plug-in) until resolved, or fall back to the exact small-R trend (§2).

`τ_cap = 2e-3` abs / `5%` rel are class-(c) gates only (not premises).

---

## 6. Prediction (theory-first, falsifiable — class (b) band)

I predict the unbiased floor will show the binary-leakage headroom is **small and flat in R**, i.e.
**CAPPED**, and that the in-sample R-growth was the artifact:

1. **`F̂_mc(R=5)` lands near the cross-fit (low-gap) end, not the in-sample (high-gap) end:**
   `gap_leak_mc(R=5) ≈ 0.0009–0.0015 < τ_cap` (closer to 0.001 than to 0.0033).
2. **`gap_leak_mc(R)` is approximately flat in R** (R=3 → R=5 within ~1.5×), consistent with the
   certified flat |2⟩(R) (coherent DD-refocused leakage; no temporal growth of leaked population).
3. **`F̂_in` rises with N; `F̂_mc` does not** (L2) — the decisive model-free signature.

**A miss is a finding, not a fact:** if `F̂_mc(R=5)` lands high (~0.003) and grows with R despite a flat
|2⟩, the binary axis has genuine R-growing headroom (NOT-CAPPED) — report it, do not bury it.

---

## 7. Build plan (M3 — ≥3 disjoint agents, GPU-serial, un-led review)

1. **Floor estimator** (GPU-heavy) — `src/qec_twin/audit/bayes_floor.py`: `mc_floor` + `enumerate_floor`
   + `plugin`/`crossfit` + convergence report; L1, L2, L3, L6 as `tests/test_bayes_floor.py`. Owns the DM
   path-prop + feasibility profiling.
2. **Seam graduation + decoding foil** (GPU-light) — graduate G2 to `src/`; the frozen-MWPM LER path
   (the `gap` numerator); L4, L5 controls.
3. **Decision/convergence harness** (GPU-heavy) — `outputs/teacher_prereg/p7b_*.py`: run (1)+(2) across
   R + leakage/realistic arms; emit the bracket + convergence + the verdict JSON.
4. **Un-led reviewer** — given only the artifact + the goal (is the floor estimator unbiased & the verdict
   sound?), NOT my prediction.
5. **From-scratch red-team** — independently re-derive `F` (own enumerator at R=1,2; own MC) and try to
   break the verdict.

GPU-serial: run heavy agents (1)(3)(5) one at a time (exit-9 oversubscription lesson). commit-gate:
`src/` additions (1)(2) need user confirmation before commit; docs/outputs follow normal flow.

---

## 8. Epistemic-status audit (per METRICS.md)

- §1 bracket, §2 unbiasedness: **(a) exact** (identities/estimator theorems; the only premise = i.i.d. shots).
- §6 prediction: **(b) prediction band** (registered bet; a miss is a finding).
- §5 `τ_cap`, the CAPPED/NOT-CAPPED/UNDECIDED rule: **(c) heuristic gate** (go/no-go only, never a premise).
- The floor `F̂_mc` itself, once validated (L1) and converged (L2): a **field-standard Bayes-error** metric
  (the model-free decoding floor) — reportable as the gap-to-optimum denominator.
