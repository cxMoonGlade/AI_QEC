# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Main line

`qec_twin` builds **the twin**: a teacher-learner, finance-structured digital twin of
QEC error mechanisms that **recovers, understands, manipulates, and predicts**
hardware error mechanisms. Binding spec: `docs/TWIN.md`.

Path: **B (validate the counterfactual loop on a controlled rep-code toy — done) →
harden (richer/correlated mechanisms, larger d, drift) → C (real Google)**. Spine:
the finance↔QEC calibration isomorphism (ADR 0004), exact Born-rule observation-NLL
calibration (ADR 0003), honest alias/uncertainty bands. Counterfactual validity is
established only against controlled-teacher `do()` ground truth, never by calibration
fit alone.

## Commands

```bash
conda run -n aiqec python -m pip install -e .                # install (editable)
conda run -n aiqec python -m pytest -q tests/               # full suite
conda run -n aiqec python -m pytest -q tests/test_<name>.py          # single file
conda run -n aiqec python -m pytest -q tests/test_<name>.py::test_fn # single test
conda run -n aiqec python -c "import torch; print(torch.cuda.is_available())"  # CUDA check
```

Always scope pytest to `tests/`. Bare `pytest` from the repo root recurses into
`external/` (gitignored vendored baseline/reference repos — not part of `qec_twin`).
Do not set `PYTHONPATH="$PWD/src"`; use the editable install. There are no console
scripts — the twin is driven through the library + `tests/`, which double as the
executable spec: `test_twin_*` covers the four capabilities + audit/contexts/d5
scaling; `test_diff_*` / `test_physical_channels` / `test_fault_graph` cover the
forward + DEM substrate. Read the matching test first to see a capability end-to-end.

## Architecture

GPU-first; target workstation ≥ RTX 5090 CUDA (CPU-only results are not evidence of
a GPU-path failure). **Every module under `src/qec_twin/` has a `README.md` bounding
it**; full map in `docs/ARCHITECTURE.md`.

```
src/qec_twin/
  # model — the four capabilities
  calibration/  [RECOVER]     label-free exact Born-NLL calibration
  understand/   [UNDERSTAND]  interpret recovered channel  (placeholder)
  knobs/        [MANIPULATE]  channel-level do() → ΔLER
  prediction/   [PREDICT]     drift / forecast  (placeholder)
  # substrate
  forward/      exact differentiable forward; channels + cptp_channel +
                exact/ (density-matrix ⚠ feasibility-only ≤~15q) + scalable/ (placeholder >50q)
  mechanisms/   mechanism definitions + controlled teachers
  contexts/     probe-richness ladder C_cal(r) + probes
  decoder/      frozen-MWPM DEM substrate
  # non-core
  audit/        gating (identifiability) / bands (uncertainty) / validity (curve)
  util/         placeholder for small helpers
  numerics.py   NUMERICAL_ZERO floor
```

**Backend boundary:** `forward/exact` (density matrix) explodes past ~15 qubits — it
is feasibility-only. The 50+ qubit target needs `forward/scalable` (placeholder,
carrier deferred, ADR 0005). The channel object + the four capabilities are
backend-agnostic, so swapping the backend is not a rewrite.

### Status

B path validated on the rep-code toy: label-free calibration recovers a coherent
teacher (`calib_kl ≈ 0`); the `do()` knob matches the teacher's true ΔLER; negative
controls fail as pre-registered (moment-matched ≈ 900×, shuffled ≈ 1400× worse);
probe richness breaks the alias; Tier-0 bands cover truth and shrink with richness;
d3→d5 holds. 63 tests pass. Next: hardening (richer/correlated mechanisms).

### Isolation contract

The label-free learner (`calibration`) consumes only observations. Teacher
ground-truth channels / parameters / labels are evaluator-only — used by `audit` to
*score* validity, never fed to the learner.

## Code conventions

- **Numerical floor:** use `qec_twin.numerics.NUMERICAL_ZERO == 1e-12` for floating
  floors/thresholds. Do not replace structural zeros (Pauli entries, bit values,
  integer indices, counts, exact algebraic identities).
- **Module placement:** new code → the module that owns it (each has a README
  defining its scope). Do not add flat modules under `src/qec_twin/`; do not rename
  the `qec_twin` package.
- **do() discipline:** a knob is a channel-level, parameterization-independent
  transform, scored by ΔLER under a frozen decoder — never an edit of a
  teacher-native parameter.
- **Claim discipline:** controlled, small-scale, exact. No Google
  physical-mechanism / Born-rule / CPTP-learning claim beyond the validated
  controlled loop until C is reached. Report honest bands; never assume
  identifiability that probe richness did not earn.
- **Metric discipline:** score every quantitative claim with a field-standard metric via
  `docs/METRICS.md`. Its ladder is forced — ledger metric → frontier-literature research → explicitly
  flagged project-defined; never a silent non-standard stand-in, and carry each metric's convention
  with its numbers. Unsure a metric is the standard? STOP and run the ladder first.

## Notation (`docs/TWIN.md` is the full contract)

`A` DEM parity map (never an assignment matrix); `E` the CPTP channel field;
`lambda_j = logit(p_j)` (never `ell_j`); `m` logical observable (never `o`);
`omega(j)` a known DEM grouping (symbol reservation, not an identifiability lever —
ADR 0005).

## Key reference documents

- `docs/TWIN.md` — binding twin spec: object contract, four capabilities, methodology.
- `docs/METRICS.md` — metric ledger + the forced standard-metric ladder (governs every score); dated
  values in `docs/metric_results.md`.
- `docs/PLAN.md` — whole-project roadmap: phase gates (B → HARDEN → C), strict
  physical/mathematical/aim↔object invariants, and what stays open.
- `CONTEXT.md` — glossary and claim boundaries.
- `AGENTS.md` — main line, doc routing, working rules.
- `docs/ARCHITECTURE.md` — full module map (+ per-module READMEs).
- `docs/teacher_learner.md` — teacher/learner roles + isolation contract.
- `docs/IDENTIFIABILITY_AND_CRL_SURVEY.md` + `docs/papers/` — CRL/finance toolset and cached references.
- `docs/adr/` — decisions; spine 0002 (build order) → 0003 (B methodology) → 0004 (finance framing) → 0005 (retire SCOPE / reframe) → 0006 (channel-field architecture).
