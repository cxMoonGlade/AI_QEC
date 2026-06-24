# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Main line

`qec_twin` builds **the twin**: a teacher-learner digital twin of QEC error
mechanisms — a **validated causal model** (the twin as an SCM; `do()` = Pearl
intervention) that **recovers, understands, manipulates, and predicts** hardware
error mechanisms. Binding spec: `docs/TWIN.md`.

Path: **B (validate the counterfactual loop on a controlled rep-code toy — done) →
harden (in progress: richer/correlated mechanisms, larger d, drift) → C (real Google)**. Spine:
the validated counterfactual loop (`do()` vs controlled-teacher ground truth) as a
causal model, exact Born-rule observation-NLL calibration (ADR 0003), honest
alias/uncertainty bands. Counterfactual validity is established only against
controlled-teacher `do()` ground truth, never by calibration fit alone. (The
finance↔QEC framing of ADR 0004 is retired as decorative — an early-twin idea, no
longer guiding, 2026-06-22.)

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
The editable install + `pyproject.toml`'s `pythonpath=["src"]` already put `qec_twin`
on the path; do not set `PYTHONPATH="$PWD/src"`. One console script exists —
`qec-twin-m4` (→ `qec_twin.hardware.m4_report:main`, ADR 0007); otherwise the twin is
driven through the library + `tests/`, which double as the executable spec:
- `test_twin_*` — the four capabilities + audit / contexts / d5 scaling.
- `test_twin_h*` — the HARDEN axes (H0 matched baseline, H1 coherent hidden-failure,
  H2 crosstalk — all green).
- `test_decision_regret_gate` — the plan2 Go/No-Go gate.
- `test_hardware_m*` — the R2-lite real-Google rung M1–M4 (skip without
  `QEC_TWIN_HW_DATA=/home/cx/Document`).
- `test_window_channel` / `test_diff_*` / `test_physical_channels` / `test_fault_graph` /
  `test_kernels_*` — the forward + DEM + CUDA-kernel substrate.
- `test_qutrit_dm_exact` / `test_carrier_seam_*` / `test_seam` / `test_soft_readout` /
  `test_bayes_floor` / `test_hypergraph_dem_tn_d3_surface` — the scalable-carrier +
  non-Pauli/leakage frontier (ADR 0008/0010).
Read the matching test first to see a capability end-to-end.

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
  forward/      exact differentiable forward: cptp_channel + channels +
                window_channel (live d3 white-box recover object) + exact/
                (density-matrix ⚠ feasibility-only ≤~15q) + scalable/ (the
                carrier — ACTIVE, see Backend boundary) + kernels/ (fused CUDA)
  mechanisms/   mechanism defs + controlled teachers: Pauli (teachers/catalog),
                non-Pauli leakage (qutrit_teachers) + seam (seam_teachers)
  contexts/     probe-richness ladder C_cal(r) + probes
  decoder/      frozen-MWPM DEM substrate
  hardware/     R2-lite real-Google ingestion + M1–M4 drivers; observations-only
                (isolation contract); evaluator-side baselines + DEM prior
  # non-core
  audit/        gating (identifiability) / bands (uncertainty) / validity (curve)
                + bayes_floor (model-free decoding-floor oracle)
  util/         placeholder for small helpers
  numerics.py   NUMERICAL_ZERO floor
```

Milestone-era run scripts + logs live in `outputs/` (gitignored, local-only) — the
scripted-execution audit trail (see Code conventions), not importable package code.

**Backend boundary:** `forward/exact` (density matrix) explodes past ~15 qubits — it
is feasibility-only. The 50+ qubit target is `forward/scalable`, now the **active
carrier** (no longer a placeholder), in two arms: the **C1 composed carrier** (DEM/HMM
bulk + window-exact CPTP corrections + a declared seam rule — `composed.py`,
`marginals.py`, `pins.py`; ADR 0008) and the **non-Pauli leakage carrier** (qutrit
MCWF on a `quimb` MPS — `mps_forward.py`/`sv_sampler.py`, the teacher→decoder
`seam.py`, plus `soft_readout.py` / `hypergraph_dem.py`; ADR 0010 — leakage is not
DEM-reducible). The channel object + the four capabilities stay backend-agnostic, so
swapping the backend is not a rewrite. Detail: `forward/scalable/README.md`.

**CUDA kernels:** `src/qec_twin/forward/kernels/` (fused subsystem-Kraus apply;
loader `forward/accel.py`, auto-routed on CUDA tensors, CPU fallback,
`QEC_TWIN_NO_KERNELS=1` disables; correctness oracle
`tests/test_kernels_fused_kraus.py`). Device policy (measured 2026-06-09,
`src/qec_twin/forward/kernels/README.md`): the d=3 toy stays **CPU-default** (the
sequential LBFGS loop is launch-bound — cuda is 0.5× there); cuda pays per-call
from n≈5 and decisively at R2-lite window sizes n=11–15 (102–405×).

### Status
B validated → HARDEN H0–H2 done → R2-lite M1–M4 landed on real Google XZZX; the live
frontier is the **scalable carrier + non-Pauli/leakage axis** (ADR 0008/0010) under the
**small-window-twin + composition** identity of `docs/plan3.md`. Status moves fast and is
deliberately NOT snapshotted here — read [docs/STATUS.md](docs/STATUS.md) (milestone
history), [docs/plan3.md](docs/plan3.md) (operative roadmap), and the live working notes
under `docs/nonpauli_teacher/` + `docs/twin_validation/`.

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
- **Theory-first discipline:** the mathematics/physics derivation precedes every code
  experiment — the predicted outcome (direction, scaling, threshold) is written down
  before the run; experiments verify derived predictions, never explore-then-rationalize.
  HARDEN's predict-before-measure gates are the template; the rule applies to all
  experiments, including real-data (R2-lite) milestones.
- **Sequencing discipline:** deferred novelty positions (Claim-B band engine, the
  composed prioritization engine, the d=5/d=7 surface-code twin) are trigger-gated,
  never dropped — but the current gated cut finishes before new ambitions open
  (ADR 0007).
- **Metric discipline:** score every quantitative claim with a field-standard metric via
  `docs/METRICS.md`. Its ladder is forced — ledger metric → frontier-literature research → explicitly
  flagged project-defined; never a silent non-standard stand-in, and carry each metric's convention
  with its numbers. Unsure a metric is the standard? STOP and run the ladder first.
- **Baseline discipline (2026-06-10):** `external/baselines/` holds 16 vendored upstream repos in
  PRISTINE state (DMLE-QEC, PyMatching, Stim, fusion-blossom, qecGPT, pyro, pgmpy, pomegranate,
  causal-learn, coniii, GGLasso, prosper, PyTorch-GAN, pytorch-examples, RBM, …), and the datasets
  ship their own baselines (SI1000 circuits, RL-prior decoding artifacts). Future milestones run
  baselines COMPREHENSIVELY from this pool, each at its OWN recommended/default settings.
  **Never modify baseline code** — minimal adaptors/helpers only (I/O glue, format conversion),
  living in OUR tree, never patches inside `external/`. Declare each baseline's version/commit and
  settings alongside its numbers. (`external/` stays gitignored; keep pytest scoped to `tests/`.)
- **Epistemic-status discipline (2026-06-10):** every pre-registration declares each quantitative
  item as **(a) exact** (theorem/identity/zero-tolerance check — the only class allowed as a
  premise or derivation basis), **(b) prediction band** (registered falsifiable bet; a miss is a
  finding, never later citable as fact), or **(c) heuristic gate/decision rule** (thresholds,
  significance conventions, eliminative controls, empirical design constants — go/no-go gating
  and tripwires ONLY, never a premise, definition, derivation step, error bound, or basis for a
  conclusion). Undeclared ⇒ defaults to (c). **Provisional-conclusion corollary (2026-06-10):
  any conclusion without theorem-grade justification is PROVISIONAL — reportable and usable
  for go/no-go gating, but NOTHING may be built on it (no definitions, derivations, designs,
  or further conclusions take it as a premise); label provisional status explicitly. Every
  milestone closes with a metric audit (all scores field-standard or rung-3 flagged) and a
  rigor audit (every conclusion classified theorem-backed vs provisional).** Full rule:
  METRICS.md "epistemic-status declaration"; binding instances: window-closure X1/X2
  (`hardware/windows.py` STATUS WARNING), the M1/M2 retro-audit in `metric_results.md`.
- **Scripted-execution discipline (HARD CONSTRAINT, 2026-06-12):** every code run — process
  control (kill/launch/verify), audits, surgeries, baseline probes, benches, ad-hoc analysis —
  MUST be a committed script file (under `outputs/` for milestone-era work), never an inline
  one-liner that runs project logic. Each script carries (a) precondition assertions, (b) printed
  evidence of effects (pids/pgids/mtimes/hashes), (c) flushed output, (d) an
  `if __name__ == "__main__"` guard whenever it touches multiprocessing (unguarded spawn re-exec
  → nested-pool crash loop — the 2026-06-12 bench hang). The only inline-bash exception is
  trivial read-only inspection (`ls`/`tail`/`pgrep`/`cat`) that runs no project logic. Rationale:
  scripts are the debug/audit trail; the bench-hang night's failures were all inline-command
  failures (silent pgid mis-kills, a `tail` pipe swallowing errors, sed-in-place edits).
- **Faithfulness protocol (anti-toy, HARD CONSTRAINT, 2026-06-20):** every load-bearing model /
  faithfulness claim follows `docs/FAITHFULNESS_PROTOCOL.md`. Root cause of every toy we hit =
  **circular verification** (checked against a reference sharing its own blind spot — lumped-vs-lumped
  oracle, "our own qutip", R=1-where-the-instrument-is-inert). Three mandatory rules: **(I)** verify
  against ground truth INDEPENDENT of the implementation (raw artifact / closed-form theorem /
  from-scratch reconstruction) — a check vs the engine's own oracle is NOT certification; **(II)** a
  constraint ledger of the physical theorems the model must satisfy + a falsifying test each, written
  BEFORE building (apply every physical gate the real circuit contains; information–disturbance;
  Clifford/detector-invariant ≠ dynamics-invariant; CPTP+symmetries; read raw inputs end-to-end;
  underdetermined⇒bracket); **(III)** declare + BOUND every simplification (epistemic class + error vs
  faithful; unbounded = STOP). Enforced as required deliverables (ledger + independent ground-truth
  check + bounded-simplification list, by the builder, before "done") + a from-scratch adversarial
  red-team + baked into every agent brief. Unlimited token budget; **slow is fast** — front-loaded
  rigor ≪ the 10× debug later.

## Notation (`docs/TWIN.md` is the full contract)

`A` DEM parity map (never an assignment matrix); `E` the CPTP channel field;
`lambda_j = logit(p_j)` (never `ell_j`); `m` logical observable (never `o`);
`omega(j)` a known DEM grouping (symbol reservation, not an identifiability lever —
ADR 0005).

## Key reference documents

- `docs/TWIN.md` — binding twin spec: object contract, four capabilities, methodology.
- `docs/METRICS.md` — metric ledger + the forced standard-metric ladder (governs every score); dated
  values in `docs/metric_results.md`.
- `docs/FAITHFULNESS_PROTOCOL.md` — the anti-toy faithfulness protocol the convention above binds to.
- `docs/plan3.md` — live whole-project plan (operative roadmap).
- `docs/_archive/PLAN.md` — whole-project roadmap: phase gates (B → HARDEN → C), strict
  physical/mathematical/aim↔object invariants, and what stays open (historical; operative
  plan = `docs/plan3.md`).
- `docs/_archive/plan2.md` — extended decision-regret / prioritization-engine plan (headline
  object: decision regret, not parameter recovery); commitment to it is gated by
  `tests/test_decision_regret_gate.py` (historical decision-regret pre-registration).
- `CONTEXT.md` — glossary and claim boundaries.
- `AGENTS.md` — main line, doc routing, working rules.
- `docs/ARCHITECTURE.md` — full module map (+ per-module READMEs).
- `docs/teacher_learner.md` — teacher/learner roles + isolation contract.
- `docs/IDENTIFIABILITY_AND_CRL_SURVEY.md` + `docs/papers/` — CRL/finance toolset and cached references.
- `docs/.datasets/` — reading notes for the four local Google QEC datasets (R2 rungs, ADR 0007):
  per-dataset design/formats/logicals/baselines + `_sources/` cached CC-BY originals
  (dot-prefixed ⇒ gitignored, local-only). Read the matching note — including layout/figure
  facts — before touching any hardware data; dataset documentation is a mandatory derivation
  input for R2 pre-registrations.
- `docs/adr/` — decisions; spine 0001 (GPU-first) → 0002 (build order) → 0003 (B methodology) → 0004 (finance framing — retired as decorative, 2026-06-22) → 0005 (retire SCOPE / reframe) → 0006 (channel-field architecture) → 0007 (R2-lite published-data rung ∥ H2; d=5/d=7 surface-code target; hardware-data metrics) → 0008 (scalable-carrier feasibility study; C1 composed architecture) → 0009 (Bayes / TN-posterior decoding spine) → 0010 (non-Pauli leakage scalable carrier).
