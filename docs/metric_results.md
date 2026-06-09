# METRIC RESULTS — dated headline values

Dated, **test-backed** values for the metrics defined in [METRICS.md](METRICS.md). Every entry below is
pinned or bounded by a named `tests/test_twin_*` test (the live source of truth) and was reproduced by a
green run on the stated date — not relayed from prose. Regenerate before quoting.

## 2026-06-09 — H0 frozen matched baseline · `tests/test_twin_h0_baseline.py`

The first code-backed HARDEN result. A richer matched teacher (heterogeneous single-qubit mechanisms,
all ≤2-Kraus → inside the `num_kraus=2` learner class) calibrated at fixed `r=1` and frozen as the
same-`r` baseline. Metrics: `calibrate(...)["total_kl"]` (calib_KL), `logical_error_rate` (ΔLER),
`tier0_alias_band`. Teacher: `loc0=("coherent",0.03,0.6)` · `loc1=("damped",0.05,0.5)` · `loc2=("pauli",0.04)`.

| Metric | Value | Note |
|---|---|---|
| calib_KL total (`total_kl`) | 1.0e-14 | machine floor — matched class recovered exactly (per-context max 1.0e-14) |
| held-out generalization (`evaluate_kl`) | < 1e-7 | cross-context, longer (R4) circuit (asserted bound) |
| loc0 ΔLER true / `knob_hat` | −4.100e-2 / −4.100e-2 | coherent; `stat_band` 6.21e-4, `alias_weight` 9.5e-7 |
| loc1 ΔLER true / `knob_hat` | −3.312e-2 / −3.312e-2 | T1+coherent (non-unital); `stat_band` 6.04e-4, `alias_weight` 9.5e-7 |
| loc2 ΔLER true / `knob_hat` | −2.391e-2 / −2.391e-2 | pure Pauli; `stat_band` 5.68e-4, `alias_weight` 9.4e-7 |

**Pre-registered prediction reversed (kept honestly):** the coherent-vs-stochastic `alias_weight` split
did NOT appear — all three sit at the floor (~9.4e-7, <0.2% of the statistical band). That signature
*alone* is degenerate (a real coherent alias orthogonal to `do(E→I)` vs nothing aliased at r=1 produce
the same flat `alias_weight`), so it was discriminated with a **Fisher-null check** at the r=1 point
(`test_h0_coherent_alias_is_a_real_fisher_null`) — NLL curvature along the iso-Z-marginal coherence
direction (the coherent↔stochastic alias) vs the rate direction:

| Direction | curvature `κ` (h=0.01) | scaling | reading |
|---|---|---|---|
| iso-marginal **coherence** (the alias) | → 0 (`κ_coh` 1.5e-3, h=0.01) | NLL ∝ **h⁴** (2nd-order null) | a **real** observational alias at r=1 |
| **rate** (control) | `κ_rate` ≈ 80.8 (stable) | NLL ∝ h² | resolved / well-conditioned |

`κ_coh/κ_rate ≈ 1.9e-5` and → 0 as h→0. So the coherent↔stochastic alias is **genuinely real at r=1**
yet does not project onto `do(E→I)` (`alias_weight` at the floor) — the *interesting* reading, which
**earns** the decision-regret principle ("an alias matters iff it projects onto the functional"), not the
boring "nothing is aliased". The alias resolving under phase-sensitive probes is the H1 job.

## 2026-06-09 — H1 coherent hidden-failure axis · TEST-BACKED (`tests/test_twin_h1_coherent.py`)

Held-out-`r` continuation of the H0 frozen mixed teacher (8 tests, green). Two claims confirmed; the
isolation control's prediction reversed into a finding.

**Claim 1 — the Fisher null lifts; scale-free witness = the exponent.** Log-log slope of profile-NLL vs
step `h` along the per-location iso-Z-marginal coherence direction (mixed teacher):

| location | r=1 | r=2 | r=3 | reading |
|---|---|---|---|---|
| loc0 pure-coherent | **4.00** | **2.00** | 2.00 | 2nd-order null at r=1, **lifts at r=2** (repeated-storage) |
| loc1 T1+coherent | 2.02 | — | — | no clean null — non-unitality resolves it early (a finding) |
| loc2 stochastic | 2.09 | — | — | always resolved (anchor) |

Control (reversed → finding): on a *pure-coherent teacher* loc0 reads exp **2.01** at r=1 (KL ~100× larger,
above floor) — the null is **backdrop-dependent**, so cross-location terms matter (feeds H2).

**Claim 2 — one Ê, two functionals** (`predict_held_out_curve`, mixed teacher, num_kraus=3, steps=300):

| k | calib_kl (precondition) | B_LER_max (do) | exotic_err (pred) |
|---|---|---|---|
| 1 | 2.21e-9 | 2.64e-7 (right) | 2.05e-1 (wrong) |
| 2 | 2.34e-8 | 1.35e-6 | 3.21e-1 |
| 3 | 1.19e-14 | 1.46e-8 | 8.58e-3 |

The same low-`r` Ê has a good fit (`calib_kl~0`), the **right** `do(E→I)` but the **wrong** exotic prediction
— the converse decision-regret statement. Shadow tie: low-`r` exotic / moment-matched twirl = **1.07**
(shadows like the twirl). Collapse k=1→k=3: **24×**. Nuance (kept honestly): the Fisher alias lifts at
**r=2** (accumulation) but the out-of-basis exotic collapses at **r=3** (basis-rotation) — two facets, two
rungs; the exotic shadow penalty (~24×) is **not** the do-functional's ~942× (larger high-`r` floor).

## 2026-06-09 — B-path counterfactual loop (exact rep-code toy) · `tests/test_twin_validity.py` + `tests/test_twin_intervention.py`

Confirmed by a green run (16/16) on 2026-06-09. The coherent-teacher numbers are **pinned** by
`test_same_r_baseline_is_frozen` (teacher `RX(θ)`+bit-flip; calibrate-on-`C_cal(r)`, eval `do(E→I)` on
held-out memory; `steps=200`, `seed=0`); the identifiable-teacher knob is **bounded** by
`test_twin_intervention`. Function/keys are the real ones (`counterfactual_scores → B_LER, B_obs`;
`negative_controls → twin_B_LER, moment_matched_B_LER, shuffled_B_LER`).

| Metric | Value | Test / status |
|---|---|---|
| Observational fit `calib_kl` (r=0 and r=1) | < 1e-6 | `test_observational_fit_succeeds_at_every_richness` (bound) |
| Knob validity, identifiable bit-flip teacher (`B_LER`, `B_obs`) | < 1e-6 | `test_tier0_remove_knob_matches_teacher_and_ranks_locations` (bound) |
| Knob validity, coherent teacher at r=1 (`twin_B_LER`) | 1.594e-5 | pinned, rel 0.25 |
| Counterfactual error at r=0 (`B_LER`) | 2.709e-3 | pinned, rel 0.15 — vs 1.594e-5 at r=1 ⇒ ≈170× richer-probe reduction |
| Negative control — moment-matched / Pauli-twirl (`B_LER`) | 1.501e-2 | pinned, rel 0.08 — ≈942× the twin's |
| Negative control — shuffled-location (`B_LER`) | 2.396e-2 | pinned, rel 0.12 — ≈1503× the twin's |
