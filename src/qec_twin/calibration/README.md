# calibration — [RECOVER]

Label-free recovery of the local CPTP channel field `E` from observations, by
**exact multi-context Born-rule observation-NLL** over the probe-richness ladder
`C_cal(r)` (`contexts`). The learner sees only `p(s,m|c)` — never the teacher's
channels, parameters, or labels. NOT moment matching (which Pauli-shadows
coherence; ADR 0003).

- `nll.py` — the exact-NLL calibration loop + the per-location channel twin
  (`RepCodeTwin`, factorized) and the H2 non-factorized learner
  (`CoupledRepCodeTwin` = factorized + ONE learnable edge DOF `phi_hat`).
  A teacher's edge field is evaluator-only input to `calibrate` (it generates
  observations); the learner never receives it.

**Boundary.** This is the RECOVER capability only. It does not score validity
(→ `audit`), apply knobs (→ `knobs`), or interpret mechanisms (→ `understand`).
Builds channels via `forward`; uses `mechanisms` teachers + `contexts`.
Spec: `docs/TWIN.md`.
