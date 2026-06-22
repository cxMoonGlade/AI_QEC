# P7 (⑦) — Leakage's effect on the LER (clean, honest floor + Pauli foils)

**Status:** pre-registration. Theory-first: arms + metrics + the falsifiable prediction fixed BEFORE the
run. **Supersedes** the contaminated `p7_leakage_headroom_prereg.md` (which used the down-biased in-sample
plug-in floor — red-team af7c9b). Uses the **honest estimable floor** (`audit/bayes_floor.py`,
convergence-checked) + the **graduated matched-Pauli-DEM foil** (`forward/scalable/seam.py`).

## The question (the actual science — deferred through the whole carrier arc)
Does leakage MATTER for the logical error rate, and is there **non-Pauli decodable headroom** that a
leakage-aware decoder captures over the **BEST Pauli-DEM**? (Two sub-questions: does leakage raise the
*optimal* LER; and is the residual-after-the-best-Pauli decodable.)

## Setup — d3, binary readout, DM forward + honest floor + two Pauli foils
**Arms:** `bg-only` (background depol, no leakage); `bg+leak` (background + WG leakage); `leak-only` (control).
Per arm, on the SAME data:
- **`F`** — the Bayes floor (the optimal LER, ANY decoder) via the estimable `mc_floor` (model-based, the
  exact-per-sample MC; **convergence-checked**, never the in-sample plug-in — protocol ledger #7).
- **`LER_blind`** — the matched-Pauli-DEM (leak-ABSENT, `build_matched_pauli_dem`, anti-circular) + frozen MWPM.
- **`LER_recal`** — a Pauli-DEM **moment-matched to the arm's syndrome rates** (the BEST Pauli, the "better-DEM"
  re-estimation) + frozen MWPM.

**Metrics:**
- **`ΔF = F_leak − F_bg`** — leakage's contribution to the OPTIMAL LER (does leakage raise the irreducible floor).
- `headroom_blind = LER_blind − F` — gap of the standard (leak-blind) decoder.
- **`headroom_recal = LER_recal − F`** — the residual after the BEST Pauli = the **non-Pauli (leakage)
  decodable contribution**. ← THE key number (the project's contribution metric: beat the best Pauli, not MWPM).
- `%ΔLER = headroom / LER` (Sivak convention: reduction, + = better).
- Scaling: WG rate, R.

## Floor + foil discipline (the lessons, baked in)
- `F` via the **estimable** `mc_floor` (model-based DM eval; **NOT** the in-sample plug-in; convergence-check
  it — must not drift with N). At d3 the DM is feasible (full-9q ~18 min/draw + sub-register cheap).
- Foils: `build_matched_pauli_dem` is leak-ABSENT (`assert_leak_absent_from_dem`, anti-circular); `LER_recal`
  is moment-matched (the better-DEM). FROZEN MWPM (the foil discipline — do() scored under a frozen decoder).
- Independent + no vacuous checks (the #11 lessons): the floor convergence-checked; the foils' LER on held-out
  shots; every claim's check able to fail.

## Prediction (theory-first — class (b) band; a miss is a finding)
1. **`ΔF = F_leak − F_bg > 0`, significant** — leakage RAISES the optimal LER: the leaked `|2⟩` population
   adds syndrome-only-undecodable error that no decoder can recover.
2. **`headroom_recal` is SMALL for BINARY readout** — the re-calibrated Pauli-DEM captures the
   stochastic-recalibratable part of leakage (~98% of the white-box's NLL gain per
   `project-coherence-not-identifiable-syndrome-only`); only the COHERENCE (the non-Pauli part) is left, and it
   is NOT decodable from binary syndromes → `headroom_recal ≈ the ~2% coherence residual` → **binary-leakage is
   CAPPED for the contribution metric.**
3. ⇒ the decodable headroom is expected in **SOFT readout (③)**, where the coherence IS observable. ⑦-binary
   settles the honest binary number (closing the contaminated-floor account) AND confirms the pivot to soft.

## Epistemic status
`F` = (a) estimable estimator + honest MC band; `ΔF`, `headroom` = (a) measured; `%ΔLER` = field-standard
(Sivak, METRICS.md); the prediction = (b) band; `τ`-style thresholds = (c) gates. d3 (DM feasible + #11-L1
component-certified faithful). SOFT readout (③) = the next phase, where the headroom is expected.

## Plan
(1) clean BINARY leakage-LER effect (this doc): the arms + the honest floor + the two foils + the metrics +
the prediction-check, d3. (2) un-led review of the ⑦ result (the #11 discipline). (3) → SOFT readout (③) where
the headroom lives. The Pauli foil is already graduated (`seam.py`); the floor is built + certified
(`bayes_floor.py`); the DM forward is d3-feasible.
