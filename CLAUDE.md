# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Main line

`qec_twin` builds **the twin**: a teacher-learner, finance-structured digital twin of
QEC error mechanisms that **recovers, understands, manipulates, and predicts**
hardware error mechanisms. Binding spec: `docs/TWIN.md`.

Path: **B (validate the counterfactual loop on a controlled rep-code toy — done) →
harden (in progress: richer/correlated mechanisms, larger d, drift) → C (real Google)**. Spine:
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
scaling; `test_twin_h*` are the HARDEN axes (H0 matched baseline, H1 coherent
hidden-failure, H2 crosstalk — all run green); `test_decision_regret_gate` is the
plan2 Go/No-Go gate; `test_hardware_m1_*` is the R2-lite published-data rung (skips
without `QEC_TWIN_HW_DATA=/home/cx/Document`); `test_diff_*` /
`test_physical_channels` / `test_fault_graph` cover the forward + DEM substrate.
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

**CUDA kernels:** `src/qec_twin/forward/kernels/` (fused subsystem-Kraus apply;
loader `forward/accel.py`, auto-routed on CUDA tensors, CPU fallback,
`QEC_TWIN_NO_KERNELS=1` disables; correctness oracle
`tests/test_kernels_fused_kraus.py`). Device policy (measured 2026-06-09,
`src/qec_twin/forward/kernels/README.md`): the d=3 toy stays **CPU-default** (the
sequential LBFGS loop is launch-bound — cuda is 0.5× there); cuda pays per-call
from n≈5 and decisively at R2-lite window sizes n=11–15 (102–405×).

### Status

B path validated on the rep-code toy: label-free calibration recovers a coherent
teacher (`calib_kl ≈ 0`); the `do()` knob matches the teacher's true ΔLER; negative
controls fail as pre-registered (moment-matched ≈ 900×, shuffled ≈ 1400× worse);
probe richness breaks the alias; Tier-0 bands cover truth and shrink with richness;
d3→d5 holds.

HARDEN: H0, H1 and **H2** landed (2026-06-09). H2 ran theory-first (three exact theorems
pre-registered, then verified 6/6): the factorized-learner fork is rung-indexed (b)→(a),
`B_misspec` is real and functional-indexed, **probe richness does not close the third band —
one declared edge DOF does** (ADR 0006 verdict: edge slots required for φ-sensitive
functionals; carrier feasibility study unblocked → ADR 0008). The decision-regret Go/No-Go
gate banked the **Claim-A floor** and deferred plan2's band engine. **R2-lite M1+M2+M3
landed** (ADR 0007 Track B, `qec_twin/hardware/` + `tests/test_hardware_*`): first
real-hardware contact on the local Google d=29 release. M1 — bit-exact m2d parity, detection
fractions in the derived band, three back-edge findings (device mirror-diagonal class ≈970×
the SI1000 sim, long-range tails, early-layer transient). M2 — window closure adjudicated
(single located grid-adjacent pair ⇒ 19 clean windows at margin 2). M3 (2026-06-10) — **the
window twin beats the shipped SI1000 prior on held-out hardware syndrome NLL in both bases**
(+56.2 X / +44.3 Z nats/shot/window at one-sided 99%; drift-isolated fallback corroborates);
findings (post-A1–A3 addendum, 2026-06-10): pij independent-edges deficiency is STRUCTURAL
(bunching DOF unrepresentable; the budget-rescale control was a no-op — the global P10 deficit
does not bind window constructions), located per-window bunching R̂ ∈ [1.0, 17.7] split-stable
(≥2 on 17/19 X / 16/19 Z; w20 = 1.000 both bases), inter-sample drift (M5 feed); P7's f̂ miss
was a coordinate artifact — predictions hold on the identified flip-rate r̂ (84%/81% in band,
edge absorption sign correct). M3 GPU
execution: static-Kraus-input CUDA graphs under the ledgered execution amendment — 84
fits/22 min on one context, bit-exact vs eager at three pin levels
(`hardware/m3_parallel.py`; model compute never falls back to CPU). **R2-lite M4 (decoder-prior
utility) LANDED (2026-06-13)** — the one held-out pass (samples 05–09, both bases, d′\*=5) under
frozen pymatching on the frozen M3 composition; the gate REVERSED: both calibrated DEM priors
(self-computed pij AND the M3 twin) decode the held-out ~**40% WORSE** than the shipped SI1000
prior (%ΔLER twin-vs-naive −40.3% X / −40.7% Z vs the registered +10% bet — a (b) miss = finding),
while the HEADLINE twin-vs-pij is IN BAND at ≈0 (−0.33%/−0.60%): **the M3 syndrome-NLL win and the
bunching certificate do NOT transfer to MWPM decoding through the independent-edges DEM format**
(covariation NULL both bases; S10 routing GATE_FAIL_CALIBRATION_DIRECTION + COVARIATION_NULL_STRUCTURAL;
PROVISIONAL, no mechanism attribution). The one decode-side positive: A3c two-pass +1.1%/+0.7% on
high-R̂ windows (sig @99%). This is the registered "honest decode-end cost accounting" (rearguard,
not the paper headline) and the strongest LER-level back-edge to the ADR 0008 carrier study.
Execution integrity: a held-out decode is a fixed function of the frozen DEMs + sample bytes — proven
by the ruling-28 bit-identity certificate (7 units sha256-identical across two attempts, a system
OOM, two restarts; same certificate validates the ruling-25/27 shot-slicing throughput fix). A4 dMLE
= documented-drop (none of the three upstream engines runs unmodified at the window instance within
the 32 GiB/70 GiB envelope; `outputs/m4_a4_dmle_attempt_dossier.md`); the dMLE comparison is
redirected to a registered r≈101 mid-scale bracket post-M4. M4 amendment 3 = rulings 19–28
(`docs/metric_results.md`). 151 tests (150 pass + 1 opt-in slow skip; hardware tests skip without
`QEC_TWIN_HW_DATA`). ADR 0008 carrier study: charter + C1/C2 theory panel DONE (2026-06-10) +
SEAM-TEST K1 first read ABSTAIN (2026-06-11) — verdict: the **C1 composed architecture**
(DEM/HMM bulk + window-exact CPTP coherent corrections; dMLE-TN as bulk engine + mandatory
baseline; perturbative cross-seam module trigger-gated) is conditionally admissible under
K1–K5; the dMLE TN is inadmissible as carrier (no coherent slot; bunching pinned at R=1 —
the sharp T-B theorem: only unital-diagonal iid fields are pinned, non-unital CPTP expresses
R>1 free). Next (M4 now banks the LER-level motivation): ADR 0008 carrier (the independent-edges
bottleneck is now measured at the decoder) ∥ M5 drift (sample-indexed; M3/M4 drift findings are the
input) ∥ the seam second read; the dMLE r≈101 bracket (own registration); H3/H4 sequenced by the
bunching axis.

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
- `docs/plan2.md` — extended decision-regret / prioritization-engine plan (headline
  object: decision regret, not parameter recovery); commitment to it is gated by
  `tests/test_decision_regret_gate.py`.
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
- `docs/adr/` — decisions; spine 0002 (build order) → 0003 (B methodology) → 0004 (finance framing) → 0005 (retire SCOPE / reframe) → 0006 (channel-field architecture) → 0007 (R2-lite published-data rung now ∥ H2; d=5/d=7 surface-code target → carrier study after H2; hardware-data metrics).
