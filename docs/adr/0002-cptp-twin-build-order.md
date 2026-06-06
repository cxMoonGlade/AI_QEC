# ADR 0002: CPTP Twin Build Order — Validate the Counterfactual Loop First

## Status

Accepted — **superseded in part by [ADR 0005](0005-retire-scope-reframe-twin.md).**
The **B-first** build order below stands and is validated. The **"A next" step** — the
orbit-compression field / the SCOPE thesis that orbit-sharing shrinks the alias class —
is **retired**: probe richness (data), not parameter sharing, broke the alias, and
orbit/factor sharing is now a flexible scalability/regularization approximation, not an
identifiability lever (ADR 0005). Read the A / `theta` / `vartheta` / Layer-2 language
below (and the stale `qec_twin.primitives.*` paths) as historical.

## Context

The exact CPTP physical substrate (SCOPE-Twin Layer 3 PhysDec + Layer 4 circuit
likelihood) is built at small, exact scale (`qec_twin.primitives.diff_cptp_channel`,
`qec_twin.primitives.diff_circuit_sim`). Three next directions were
considered for advancing toward the interventional "noise simulator with knobs":

- **A** — build the Layer 2 orbit-compression field
  `theta_{i,t} = rho_t(g_{i<-omega}) vartheta_{omega,t} + U_{omega,t} z_{i,t}`
  plus a GKSL form of PhysDec.
- **B** — close the loop on a small controlled system: label-free calibrate the
  substrate, run the knobs, and validate counterfactual correctness against
  controlled-teacher `do()` ground truth.
- **C** — bridge to real Google 72Q/105Q data via stim-circuit ingestion plus a
  scalable DEM-bulk-with-coherent-corrections model.

The binding scientific risk across all three is that an observational fit
identifies the mechanism field only up to the observational alias quotient, so a
twin that reproduces data can still give wrong counterfactual (knob) answers:
observational equivalence need not be interventional equivalence.

## Decision

Build in the order **B then A**, with **C deferred**.

- **B first**, using the current per-location substrate, because it answers "does
  this path hold?" at minimum cost and directly measures the central
  observational-vs-interventional risk where controlled-teacher ground truth is
  available.
- **A next**: add the orbit-compression field and re-run B's counterfactual-
  validity test, yielding a controlled ablation of interventional validity with
  vs without the symmetry-compression prior — the strongest available evidence
  for the SCOPE thesis that orbit-sharing shrinks the alias class.
- **C deferred** until A/B establish confidence: fitting real observational data
  before the loop is validated cannot distinguish a causally correct twin from
  an aliased one.

## Consequences

- Two regimes are kept distinct to avoid a `theta`/`vartheta` contradiction: in
  the controlled B toy, per-location / simulator-slot interventions on
  `theta_{i,t}` ARE testable (the teacher gives per-location ground truth); for
  real hardware / Google, location-level actionability is NOT claimed — the
  currently trustworthy target is class/orbit-level (`vartheta_{omega,t}`) or the
  interventional quotient. The gap is the location residual `z_{i,t}` (the
  soft-residual / centered residual-rank claim), strictly harder and a
  prerequisite for any location-level actionability. B exercises execution-level
  (`theta_{i,t}`) interventions to validate the loop and can measure how far the
  residual is recoverable against the teacher's known per-location truth; A makes
  the class-level knob explicit; a location-level hardware instruction is a
  later, harder bar.
- B requires a new joint label-free calibration loop (fit multiple local
  channels to syndrome statistics) and an explicit controlled-intervention
  protocol on the teacher.
- Real-data accuracy, cross-context, and drift evidence are intentionally
  postponed; the near-term claim stays controlled, exact, and small-scale — no
  Google physical-mechanism or counterfactual claim until C.
- If B shows interventional validity is unrecoverable even with orbit-sharing on
  controlled ground truth, that is a stop/redesign signal before any real-data
  investment.
