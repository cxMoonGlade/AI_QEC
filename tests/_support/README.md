# tests/_support — shared test support

Shared test support for the suite: fixtures and guards (`fixtures.py`) plus their
meta-tests (`test_support_selftest.py`). **NEVER production code** (nothing under
`src/` may import this package) and **NEVER a home for anything with an independence
constraint against a specific backend** — a reference implementation that referees a
backend stays deliberately local to its test file or its own dedicated reference
module (see the contract's "Explicitly NOT centralized" list; e.g. the dense
window/site apply reference family, soft_readout's `_arm_d2`, and
`test_mps_terminal_degenerate_guard.py`'s loaders per AM-4).

Binding contract: `docs/twin_validation/api_hardening_ownership_design.md`
(rows C1/C2, NAMING STANDARD N-1..N-5, v2 REVIEW DISPOSITIONS, DEVIOUS-TEST STANDARD).
The directory keeps its leading underscore per N-5 (pytest collection convention);
names inside are clean.

## GLOSSARY (N-1 — the one public vocabulary, aligned with the certify seam,
`src/error_coupling_simulator/certify/types.py`)

- **reference** — a from-scratch or INDEPENDENT implementation used for comparison
  against the backend under test (replaces the internal "referee"/"GT"); it must not
  share the tested code's implementation route (FAITHFULNESS_PROTOCOL Rule I).
- **anchor** — the certify port (`certify.types.Anchor`): an independent ground-truth
  capability (DM oracle / stim Clifford slice / closed-form identity) that answers a
  (statistic, regime) cell with declared exactness + epistemic class; feasibility
  (OOM) is data, not branching.
- **control** — the certify port (`certify.types.Control`) for FIRST-CLASS negative
  controls: a deliberately broken input/perturbation that MUST fire (fail/separate);
  an inert control forces the verdict to FAIL — a certification with no falsifier is
  rejected by construction.
- **preset** — a named, REGISTERED experiment configuration with frozen, explicit
  knobs (replaces the internal "cell"); no silent physics defaults.
- **gate** — a registered pass/fail check with a pre-declared threshold/tolerance
  (predict-before-measure); a miss is a FINDING to adjudicate, never a silent
  tolerance bump.
- **backend under test** — the implementation a test certifies (replaces the internal
  "arm"); its own oracles and helpers never referee it (anti-circular).

## K-CATALOG (DEVIOUS-TEST STANDARD — binding for every NEW test in this pass and after)

Design question every test must answer BEFORE it is done: **"what is the most devious
implementation that still passes me?"** — then add the discriminator that kills it.

**KILLER requirement.** Every load-bearing assert ships at least one KILLER: a
deliberately sabotaged input/implementation variant DEMONSTRATED to trip that assert
(the `assert_control_trips` shape). A check that has never been shown to fail is
unproven (scrutinize-vacuous-checks discipline, mandatory per-assert).

Every entry is a REAL bug class caught in the 2026-07-06/07 arc; new tests check
themselves against it and name which classes they defend:

- **K-1** inert seam / dead parameter (the P2-ii caller-table-ignored trap)
- **K-2** misindexing (off-by-one, Python negative-index wraparound, reversed order)
- **K-3** tie-break/comparison drift (`<=` vs `<`, first-vs-last, argmax-on-bool)
- **K-4** evil-marginal thresholds (engineered violation landing a hair above the
  gate: the measured 1.181e-12 vs CPTP_TOL=1e-12)
- **K-5** self-comparison vacuity (identical cap tuples; engine-vs-own-oracle)
- **K-6** symmetry blindness (permutation-symmetric operators hiding leg-order bugs;
  sign-blind observables)
- **K-7** degenerate-input shadowing (NaN-swallowed guards; zero-norm batch poisoning)
- **K-8** convention/gauge drift (MSB/site-order/lambda-vs-sigma units)
- **K-9** cross-shot/batch contamination (gather misalignment)
- **K-10** measurement-isolation contamination (absolute peaks counting other tests'
  standing allocations)

Discriminator patterns (the reusable answers): byte-level positive controls
(injection == equivalent static run), prefix-identity checks (round-0 block EXACT
equality), sabotage variants (swapped enumeration, reversed tables), unit tags in
names, masked-environment probes, heterogeneous-batch vs B=1 replays.

## What lives here

- `fixtures.py` — `require_precondition` (the greppable class-(c) prefix),
  `assert_control_trips` (the anti-vacuous control shape; bespoke broken inputs stay
  local), `random_cptp_kraus` / `random_density_matrix` (one builder each, backend +
  return-shape flags, internal 1e-12 asserts), `load_outputs_module` (importlib shim
  for committed `outputs/` scripts).
- `test_support_selftest.py` — the meta-tests: the infrastructure defends itself
  (prefix verbatim, double-negative killer, sabotaged-CPTP demonstration, mask-hook
  unknown-name fail-loud).
