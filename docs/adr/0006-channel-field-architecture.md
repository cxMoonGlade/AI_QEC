# ADR 0006: Channel-Field Architecture — Ratify the Object, Scope the Support Structure, Defer the Carrier

## Status

Accepted (2026-06-06). Resolves, for the HARDEN regime, the "main-line architecture
is open" ambiguity left by ADR 0005. Does **not** choose the scalability carrier — that
stays deferred (ADR 0005).

## Context

ADR 0005 deliberately left the main-line architecture open (the four capabilities are the
spec; parameterizations are chosen "against the capabilities, scalability one criterion").
Entering HARDEN forces a concrete architecture question **now**: what is the learner's
channel parameterization for *correlated* mechanisms? Running the first cut (H1→H2, a
two-qubit correlated mechanism) architecture-blind would confound mechanism complexity
with parameterization choice. A targeted look-back — the channel kernel, the calibration
wiring, and the survey's CPTP/identifiability warnings — resolves most of it.

- **The object is forced, not open.** `forward/cptp_channel.py` parameterizes a CPTP
  channel by Stinespring dilation (Hermitian generator → isometry → Kraus),
  CPTP-by-construction, any power-of-two `dim`, non-Pauli / non-Clifford capable. Survey
  **W5** (coherent errors break Pauli-DEM) requires a coherence-capable object; **W4**
  says the identifiability-clean alternative (a Pauli-error-rate vector) is exactly the
  one that *cannot* carry coherence. So the channel is necessary, and its W4 gauge-freedom
  cost is already neutralized by the gauge-invariant **Choi** metric (`choi_matrix`) + the
  alias bands. B validated this end-to-end.
- **The support structure is the only open question — and it is wiring.** The field is a
  callable `field(t, i) → Kraus` (`calibration/nll.py` `RepCodeTwin`: a list of
  per-location `dim`-2 `StinespringChannel`s, time-shared); the forward applies it via
  `apply_channel_local(rho, kraus, targets, n)`, which is **arity-general**; the kernel is
  **dim-general**. Per-location vs explicit-edge vs factor therefore differ only in the
  twin's channel container, the `field` callable's protocol, and the forward's application
  loop — not in the kernel or the application primitive.
- **Identifiability caps the parameterization.** Survey **W2** (Bravyi–Haah–Hastings
  learnable-DOF ceiling): only directions in the learnable subspace of the probe set are
  recoverable; parameters outside it are unrecoverable regardless of expressiveness. The
  support structure must be gated by the DOF / anchor audit, not chosen by expressiveness.

## Decision

**1. Ratify the channel object** (closes ADR 0005's ambiguity for the object). The
main-line learner object is a **CPTP channel field**, each local channel a **Stinespring**
Kraus map, over the **exact differentiable Born forward**, calibrated by **exact
multi-context observation-NLL**, with gauge handled by the **Choi-invariant metric + alias
bands**, and **phase-sensitive (r ≥ 3) probes** as part of its identifiability surface
(W5). The **GKSL** generator form is a deferred variant, needed only for Tier-1b
generator-scaling `do()` / interpretability (ADR 0003).

**2. Scope the open question — the field's support structure.** Candidates, increasing in
expressiveness/cost:

- **(a) per-location `dim`-2 slots** — B's choice; factorized `∏_q E_q`;
- **(b) per-location + explicit edge `dim`-4 slots** on correlated pairs — represents
  2-body structure exactly;
- **(c) factor / shared parameterization** — fewer parameters, scalable, an approximation;
- **(d) DEM-bulk + coherent-corrections** — the scalable carrier (deferred; Decision 4).

**3. Fix the decision rule (the pick is earned, not asserted).**

- **(i) DOF gate (W2).** Compute the learnable-subspace / anchor condition (`audit/gating.py`)
  for the candidate 2-body direction under the H1 probe ladder. If that direction is
  outside the learnable subspace, explicit edge slots (b) are unrecoverable there → do not
  add them; report the residual as `B_misspec`.
- **(ii) Misspecification ablation.** Run H1 with the well-specified learner (b) and H2
  with the factorized learner (a) on the *same* 2-body teacher; the `B_misspec` magnitude
  (knob error of (a) vs (b)) decides whether factorized-plus-honest-band suffices or
  explicit correlation structure is required.
- **(iii) Scalability tiebreak (ADR 0005).** If two candidates are both adequate, prefer
  the one that scales, declaring any sharing as an approximation audited by the
  misspecification band — never sold as free identifiability.

**4. Defer the scalability carrier.** No carrier is chosen (ADR 0005). DEM-bulk +
coherent-corrections (d) is a post-HARDEN decision; W5 shows carrying coherence/hyperedges
in a DEM bulk is a hard, separate problem. The carrier is selected only after the
support-structure question is resolved on controlled teachers and the >15-qubit
feasibility wall (`forward/scalable`) is confronted.

## Consequences

- **H1/H2 are the architecture-selection experiment**, not just realism cuts. The first
  concrete step is the W2 DOF gate (cheap, `gating.py`) on a candidate 2-body mechanism —
  it predicts whether (b) is even recoverable before any fit is run.
- **Adding edge slots (b) is a bounded wiring change**, the extension points being: extend
  the field protocol `(t, i) → Kraus` to also yield edge channels `(t, (i,j)) → Kraus`;
  add edge channels to the twin container; add an edge-application step in the forward
  (`apply_channel_local` with `targets=[i, j]`). No kernel or primitive rebuild.
- **`B_misspec` gets its first concrete definition** (PLAN.md §1.2): the knob error of the
  factorized learner (a) against the controlled 2-body teacher.
- No claim boundary moves; this is an architecture-decision-framework ADR, not a
  capability claim.

## References

ADR 0003 (B methodology — Born-NLL, `do()` tiers), ADR 0004 (finance framing — bands),
ADR 0005 (architecture deferred / SCOPE retired). Survey **W2/W4/W5** and the learnable-DOF
+ coherent-DEM references: `docs/IDENTIFIABILITY_AND_CRL_SURVEY.md`, `docs/papers/`. Code:
`forward/cptp_channel.py` (kernel), `calibration/nll.py` (field wiring),
`forward/exact/circuit_sim.py` (`apply_channel_local`), `audit/gating.py` (DOF/anchor audit).
