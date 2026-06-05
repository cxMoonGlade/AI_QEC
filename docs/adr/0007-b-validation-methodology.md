# ADR 0007: B Feasibility-Validation Methodology

## Status

Accepted. The B5 deliverable here is refined by ADR 0008 (derivatives-calibration
framing): calibrate-on-`r≤k`/predict-held-out-`r`, uncertainty bands, and a
pre-registered negative-control failure mode.

## Context

ADR 0006 builds B first: a controlled feasibility step asking whether a
label-free CPTP twin can produce trustworthy counterfactual ("knob") answers,
validated against controlled-teacher ground truth. The binding risk is that an
observational fit identifies the channel field only up to the observational
alias quotient, so the twin can reproduce data yet give wrong knob answers.

A DEM-style moment-matching calibration (detector marginals plus pairwise
correlations, as SI1000/DEM use) is inadequate here: those low-order moments are
exactly what a stochastic Pauli channel reproduces, so moment matching
Pauli-shadows the coherent/non-Clifford structure that is the whole point of the
exact CPTP substrate. The toy is an exactly-simulable small repetition code
(ADR 0006 / Q3).

## Decision

**Calibration objective — exact Born-rule observation likelihood, not moment
matching.** Recover the local CPTP channel field `E` by

```
minimize  NLL(E) = - sum_{c in C_cal(r)} sum_n log p_E(s_n, m_n | c)
```

under the exact density-matrix forward model, fitting the full observation
distribution `p(s, m | c)` (detector-event trajectory `s` plus logical outcome
`m`). Label-free. DEM-style moment matching is retained only as a
negative-control baseline.

**Calibration contexts — multi-context, probe-rich, indexed by richness `r`.**
Not a single memory context. `C_cal(r)` grows:

```
r=0: single repetition memory circuit
r=1: multiple rounds / both logical bases
r=2: active / enhanced local probes
r=3: Clifford sandwiches / basis-rotated probes
r=4: mechanism-stressing probes, incl. coherent / non-Clifford-sensitive contexts
```

The same local channel slot is reused across contexts so context diversity
breaks the alias quotient. Coherent/non-Clifford mechanisms require
basis-sensitive and phase-sensitive probes.

**Interventions — channel-level, parameterization-independent** (see the `do()`
glossary in `CONTEXT.md`). Tier 0: `E_i -> I` (remove, unambiguous). Tier 1:
strength scaling under a declared log branch with a CPTP guardrail. Raw teacher
parameters (`epsilon`/`gamma`/axis) are not handles.

**Deliverable — a curve, not a point: counterfactual-validity error vs probe
richness.** For each `r`:

```
1. Calibrate E_hat_r on base observations (label-free, multi-context exact NLL).
2. Apply the same channel-level do() to teacher-true E and to twin E_hat_r.
3. Exact-forward both to a held-out QEC eval circuit.
4. Score:
   B_LER(r) = | dLER_D^teacher - dLER_D^twin_r |        (decoder D)
   B_obs(r) = distance( dp_teacher(s,m), dp_twin_r(s,m) )
```

The decoder `D` is predeclared and fixed across teacher, twin, base, and `do()`
evaluations; no decoder retuning happens inside the `B_*` score.

B's question is therefore not "can a single context miraculously recover the
hidden channel" but "how much probe/context diversity is needed before a
label-free twin yields trustworthy, decoder-relevant knobs."

## Consequences

- Calibration and evaluation use a held-out split: calibrate on `C_cal(r)`,
  validate knobs on a separate memory eval circuit (cross-context built in).
- Negative controls: a shuffled-channel twin must give wrong counterfactuals
  (universal fail). A moment-matched (DEM-style) twin need not fail universally —
  it must underperform/fail specifically on the coherent/non-Clifford-sensitive
  slice (high-`r`, phase-sensitive probes), as the Pauli-shadowing control.
- Tier-1 strength scaling `exp(k * Log(E))` is well-defined and CPTP only when
  `E` is infinitesimally divisible (principal log exists / small-noise) or is
  recovered as a GKSL generator (`k * L` is then valid by construction). Before
  the GKSL PhysDec (ADR 0006 step A), B uses Tier 0 plus a CPTP-safe weakening
  `(1-a) I + a E`, `a in [0, 1]`; full generator-scaling (incl. amplify `k > 1`)
  lands with the GKSL PhysDec. This is an additional motivation for the GKSL form.
- The same observation-NLL plus probe-richness framing transfers to the real-data
  analogue (C), but loses the ground-truth `B_*(r)` curve (no true `E` on
  hardware).
