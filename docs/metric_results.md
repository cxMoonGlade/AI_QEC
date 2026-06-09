# METRIC RESULTS — dated headline values

Dated re-recordings of the metrics **defined** in [METRICS.md](METRICS.md). Definitions, standard names,
references, and conventions live there; **this file holds only numbers — each dated and attributed.**

The `tests/test_twin_*` suite is the live source of truth. Values here are snapshots and can go stale;
**regenerate against the suite before quoting.** New rows append with a date; do not edit old ones.

> **Provenance (2026-06-09).** These rows were *consolidated from existing in-repo docs* (PLAN.md,
> README, METRICS.md), **not freshly re-run**, when `metric_results.md` was created. **Branch caveat:**
> only the calibration NLL/KL + LER metrics resolve in the current `Dev-F` tree; the identifiability /
> cone block and the band/regret functions (`coherent_alias_floor`, `finite_displacement_regret`,
> `knob_dler_error`, …) live on the GKSL / integration line, not here — verify against that tree's suite
> before quoting. Reconciling METRICS.md's `Function` column with `Dev-F` code is an open item.

## 2026-06-09 — identifiability reproduction (cone / corrected-KL) · GKSL/integration line

PSD-constrained run; consolidated from the reproduction note in METRICS.md (§ identifiability). **Code
not in `Dev-F`** — `physical_corrected_kl` / `cone_status` / `physical_identification_order` resolve on
the integration line.

| Metric | Function | Value | Note |
|---|---|---|---|
| Corrected-KL | `physical_corrected_kl` | 8e-3 … 1.8e-1 | PSD-projected (certified-feasible) |
| Identification order `k` | `physical_identification_order` | ≈ 2.2 | **numerics-grade; output under review — not assumed true** |
| Kossakowski min eig | `cone_status` | at boundary (≥ −1e-12) | PSD-feasible |
| Unconstrained min eig | (no PSD projection) | ≈ −0.22 … −0.30 | escapes the cone — why the projection is load-bearing |
| Decision projection | `decision_pushforward` `\|v·ĝ\|` | ≈ 0.13 | coherent onset, exact |
| Decision regret | `finite_displacement_regret` | ≈ 1.5e-2 | Manski minimax over the fiber |

## B-path headline — exact rep-code toy

Narrative source: [PLAN.md](PLAN.md) §B / [README](../README.md); regenerate from `tests/test_twin_*`.

| Metric | Function | Value | Note |
|---|---|---|---|
| Calibration recovery | `calibration.nll.joint_kl` (`calib_kl`) | ≈ 0 | machine precision; joints agree |
| Knob counterfactual error | `knob_dler_error` `\|ΔLER_teacher − ΔLER_twin\|` | ≈ 6e-9 | Tier-0 `do(E→I)` on the coherent teacher |
| Negative control — moment-matched | (pre-registered) | ≈ 900× worse | fails as predicted |
| Negative control — shuffled | (pre-registered) | ≈ 1400× worse | fails as predicted |
| Probe-richness alias break | held-out exotic error | collapses ~10⁵× | once basis-rotated probes enter `C_cal(r)` |
