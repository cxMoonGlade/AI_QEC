# ADR 0009: Retire the SCOPE Framing — Reframe as a Teacher-Learner, Finance-Structured Error-Mechanism Digital Twin

## Status

Accepted (2026-06-05). Supersedes the orbit-compression "A" step and the SCOPE
thesis statement of ADR 0006; subsumes the orbit-sharing retirement. ADR 0007
(B methodology) and ADR 0008 (finance framing) carry forward unchanged and become
the methodological core.

## Context

"SCOPE" (Symmetry-Compressed Orbit-Physical Emulator) named a specific
architectural bet: orbit-symmetry compression as both the backbone and the
identifiability lever. Two findings retire it:

1. **Every identifiability win in B came WITHOUT the orbit field.** B ran on the
   per-location substrate; label-free calibration (KL ~1e-15), the k=3 exotic
   collapse, and the 6e-9 knob validity were all obtained with no orbit-sharing.
   What broke the observational alias was **probe richness (data)**, not
   parameter-tying.
2. **Orbit-sharing conflates a variance/scalability tool with an identifiability
   claim.** Tying parameters adds no observational information; it selects a
   representative *by assumption*, so it cannot break a genuine observational
   alias and risks a confident-wrong counterfactual. It is symptom relief, not a
   root-cause cure.

The work has converged on a different organizing principle, load-bearing all
session: the QEC mechanism-learning problem is structurally the
quantitative-finance calibration/risk problem (ADR 0008). That analogy, not
symmetry-compression, is the spine.

## Decision

1. **Retire SCOPE as thesis and narrative.** Drop "SCOPE / SCOPE-Twin /
   SCOPE-Static" as the project framing, and retire orbit-symmetry compression as
   a named identifiability or parameter-economy mechanism.

2. **Install the main line:** a teacher-learner-built, quantitative-finance-
   structured digital twin of QEC error mechanisms, delivering four capabilities
   over hardware-realistic noise:
   - **recover** — label-free calibration (inverse problem; finance: vol-surface calibration);
   - **understand** — mechanism interpretation + honest uncertainty/alias bands (finance: model-uncertainty / factor interpretation);
   - **manipulate** — channel-level `do()` knobs → ΔLER (finance: Greeks / hedging / scenario);
   - **predict** — drift / rare-failure / decoder-impact forecasting (finance: state-space / regime / multiscale SV).

3. **Scope: framing + architecture, NOT a code rename.** The package identifier
   `scope_static` (imports, console scripts, configs, tests) is retained as a
   neutral, stable code handle — a mechanical rename would risk the full test
   suite for zero scientific gain. "the twin" is the descriptive name until a new
   one is chosen.

4. **Symmetry.** No symmetry-compression as a named thesis or as an
   identifiability/economy claim. Exact, KNOWN structure (by-construction-
   identical locations in a controlled teacher; forward-map structure) may still
   be exploited silently for compute/correctness — that is implementation, not a
   thesis.

5. **Scalability deferred — not decided now.** We are in the
   infrastructure-building stage and the main-line approach itself is not yet
   settled, so **no scalability carrier is chosen now** (not DEM-bulk +
   coherent-corrections, not an orbit/factor parameterization, not anything else).
   Scalability re-enters LATER as **one selection criterion among others** when the
   main-line model is chosen. Surviving constraint regardless of timing: if
   parameter sharing is ever used for scale, it is declared as an approximation and
   audited by the misspecification band (step-2 coverage methodology), never sold
   as free identifiability.

## Consequences

- **ABC ladder:** the orbit-field "A" step is retired. The path is **B** (validate
  the loop — done on the toy) → **harden** (richer/correlated mechanisms, larger
  `d`, drift) → **C** (real Google), with recover/understand/manipulate/predict as
  the success axes.
- **Experimental plan barely changes — only the narrative.** The in-flight step-2
  (richer/correlated mechanism + misspecification-coverage band) stands; it now
  serves "recovery + understanding under realistic complexity," not "A's orbit
  setup."
- **The main-line model architecture is left open.** The four capabilities are the
  *spec*, not an architecture. Candidate parameterizations (per-location CPTP
  field, factor/orbit, DEM-bulk + corrections, …) are evaluated later against those
  capabilities, with **future scalability as one selection criterion** — deferred
  while infrastructure is still being built.
- **The implementation record stays valid.** The DEM/Bernoulli core, the
  controlled catalog, and the Stage-3/5 work remain the teacher-learner substrate;
  only their SCOPE-thesis wrapping is reframed.
- **Doc/memory propagation required** (reframe or remove): `docs/SCOPE_TWIN.md` (now removed; replaced by `docs/TWIN.md`)
  (the L2 orbit field + six-axis SCOPE thesis), `README.md`, `AGENTS.md`,
  `CONTEXT.md` (the knob-gap entry built on the orbit field), and the
  `qec-digital-twin-goal` memory (states the orbit field as "the identifiability
  lever").
- **No claim boundary moves outward.** Still controlled, small-scale; no Google
  physical-mechanism or counterfactual claim until the loop is validated and C is
  reached.

## References

ADR 0006 (superseded "A"), 0007 (B methodology), 0008 (finance framing),
`docs/IDENTIFIABILITY_AND_CRL_SURVEY.md`, `docs/papers/`.
