# QEC Error-Mechanism Digital Twin

`scope_static` is a QEC noise-learning research package. Its goal is a
**teacher-learner digital twin of QEC error mechanisms**, structured like a
quantitative-finance calibration/risk system, that can **recover**,
**understand**, **manipulate**, and **predict** error mechanisms on
hardware-realistic noise:

- **recover** — label-free calibration of mechanisms from observations;
- **understand** — interpret them, with honest uncertainty / alias bands;
- **manipulate** — channel-level `do()` knobs that predict ΔLER;
- **predict** — drift, rare-failure, and decoder-impact forecasting.

The organizing principle is the structural isomorphism between QEC mechanism
learning and quantitative-finance calibration: vol-surface calibration ≡
label-free channel calibration; model-uncertainty bands ≡ alias-induced knob
bands; Greeks/hedging ≡ `do()` knobs; state-space/regime models ≡ drift. See
`docs/IDENTIFIABILITY_AND_CRL_SURVEY.md` and `docs/adr/0008-finance-calibration-framing.md`.

> The package name `scope_static` is a stable code identifier only. The earlier
> "SCOPE / Symmetry-Compressed Orbit-Physical Emulator" thesis, and orbit-sharing
> as an identifiability lever, are retired — see `docs/adr/0009-retire-scope-reframe-twin.md`.

## Current state

**The counterfactual loop (the "B path") is validated at small exact scale.** On a
repetition-code toy: the twin is label-free calibrated by exact multi-context
Born-rule observation-NLL, a channel-level `do()` knob is applied, and its
predicted ΔLER is checked against controlled-teacher ground truth. Demonstrated
results — calibration recovers the teacher to machine precision; **probe richness
breaks the observational alias** (out-of-basis exotic prediction error collapses
~10⁵× once basis-rotated probes enter calibration); the recovered knob matches the
teacher's true ΔLER; moment-matched and shuffled-channel twins fail as
pre-registered. See ADR 0006/0007/0008.

This is a controlled, exact, small-scale capability result — **not** yet a
validated real-hardware twin. No Google physical-mechanism, drift, transfer, or
decoder-utility claim is made.

### Supporting substrate

- **DEM/Bernoulli core** (`scope_static.dem`): `e_j ~ Bernoulli(p_j)`,
  `y = A e mod 2`, `lambda_j = logit(p_j)` — parity maps, fault-logit models,
  exact local-window likelihood, baselines, evidence records.
- **Controlled physical-mechanism catalog** (`data_preparation` → `teacher` →
  `learner`): generate teacher-declared noisy QEC observations from unitary/Kraus/
  readout mechanisms (CPTP/POVM-audited), verify teacher/catalog separability, and
  train label-free learners that recover and replay the learner-visible
  distribution. Evaluator-only labels/channels/PTMs/teacher-IDs stay out of the
  learner path.
- **Differentiable CPTP substrate** (`scope_static.primitives.diff_cptp_channel`,
  `diff_circuit_sim`, `diff_rep_code`): a CPTP-by-construction channel decoder plus
  an exact differentiable circuit-to-observation forward model
  `p(y|c) = Tr[M_y C(c)(rho0)]`.
- **Google/Willow real data** (`scope_static.google`): a public syndrome-response
  visible surface. The current real-data result is a bounded no-oracle visible
  replay that beats global/mean-only, shuffle, scramble, and stratified-null
  controls — not hardware mechanism recovery.

## Install

Python `>=3.10`. From the repository root:

```bash
python -m pip install -e .
```

On the GPU workstation use the `aiqec` environment
(`conda run -n aiqec python -m pip install -e .`). Do not set
`PYTHONPATH="$PWD/src"`; use the editable install.

## Use

```bash
scope-static-toolbox        # print the toolbox manifest
python -m pytest -q         # run the test suite
```

The teacher generator, catalog pipeline, Google V2 visible surface, and B-path
twin experiments run via console scripts and `scope_static.experiments.*` modules
— see `docs/RUNBOOK.md` for the full command set. Outputs are written under
`outputs/`.

## Docs

- `CONTEXT.md` — glossary and claim boundaries.
- `AGENTS.md` — main line, doc routing, and working rules.
- `docs/ARCHITECTURE.md` — module map.
- `docs/RUNBOOK.md` — install, test, GPU, and experiment commands.
- `docs/teacher_learner.md` — teacher/learner roles and isolation contract.
- `docs/TWIN.md` — binding twin spec: object contract, four capabilities, notation.
- `docs/IDENTIFIABILITY_AND_CRL_SURVEY.md` + `docs/papers/` — the CRL/finance toolset.
- `docs/adr/` — durable decisions (current spine 0006 → 0009).
