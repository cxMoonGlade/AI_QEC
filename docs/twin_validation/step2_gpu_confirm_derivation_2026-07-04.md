# Track-1 Step-2 — GPU empirical confirm of Step-1 (predict-before-measure, 2026-07-04)

**Status: DERIVATION written BEFORE the run.** Committed script:
`outputs/twin_validation/step2_shared_vs_off_emit_confirm.py`. Confirms the Step-1 ANALYTIC `N_detect`
(`step1_shared_vs_off_lag2_Ndetect_derivation`) on the REAL dense `emit()` (`CoupledCycleTeacher`), with the
CORRECTED observable: **absolute lag≥2 shared-vs-off Spitz `p_ij`** (NEVER 2-point-TV, NEVER shared-minus-
markovian). Reuses the g6/`_gate_common` machinery (`emit_arm`, `round_delta_by_round`, Spitz Eq.13,
`cluster_bootstrap_se`). No `src/` change (custom source amplitude via the teacher `source=` param).

## What Step-1 predicted (the analytic values to confirm)

From `step1_shared_vs_off_lag2_Ndetect.py` (a-exact / committed): the off arm's round-delta stream is MA(1) ⇒
`p_ij(lag≥2)=0` structurally; the shared arm's `p_ij(lag≥2)` is common-mode-dominated + a decaying memory,
`∝ amp²`. Slice-1 (`amplitude_radns=1e-4`): shared `p_ij(lag2) ≈ 1.16e-4`; pooled `N_detect ≈ 5.85e4`.
Endpoint (`amp≈4e-4`): `p_ij(lag2) ≈ 8.7e-3` (`∝amp²` × the `q̄`/Spitz map), deeper feasible.

## PREDICTIONS (predict-before-measure)

- **S2-P0 (a-exact, control):** the REAL `off_source()` arm reads `p_ij(lag≥2) ≈ 0` within cluster-bootstrap
  SE (the structural MA(1) zero on the emitted cube) — confirming the off arm is the correct structural-zero
  null. (off `p_ij(lag1) = μ ≈ 0.0149`, nonzero — the MA(1) floor.)
- **S2-P1 (the confirm, b):** the REAL `shared` arm reads `p_ij(lag2) > 0`, matching the Step-1 analytic
  within ~2× (MC + the exact-emit vs analytic-covariance modeling gap): slice-1 `≈ 1e-4`, endpoint `≈ 1e-2`;
  `∝ amp²` between the two.
- **S2-P2 (feasibility, c):** shared `p_ij(lag2)` is resolvable from off (`|z| = p_ij/SE ≥ 3`) at the
  Step-1-predicted feasible N (slice-1 pooled `~6e4`; endpoint far fewer). The empirical `N_detect` (from the
  bootstrap SE) matches the Step-1 analytic `N_detect` in order of magnitude.
- **Falsifier:** if the REAL shared arm reads `p_ij(lag2) ≈ 0` (no better than off) OR the off arm reads
  `p_ij(lag2) ≠ 0`, the Step-1 analytic is not confirmed on the real emit — a FINDING (the analytic covariance
  model or the emit path diverge).

## Epistemic classes + execution

- **(a) exact:** S2-P0 (off structural zero). **(b) band:** S2-P1 (shared `p_ij` vs analytic), S2-P2
  (`N_detect`). **(c) gate:** `|z|≥3` resolvability; the `N≤1e6` cap.
- **Execution:** the dense `emit()` touches cuda (5q fixture — small); GPU-serial, scripted, predict-before-
  measure. `m=0` only. First run at a modest N to confirm the machinery + gauge cost, then scale to the
  feasible N. Reuse the g6/`_gate_common` helpers verbatim.
