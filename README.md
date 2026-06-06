# QEC Error-Mechanism Digital Twin

`qec_twin` is a QEC noise-learning research package. Its goal is a
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

> The package name `qec_twin` is a stable code identifier only. The earlier
> orbit-symmetry-compression thesis, and orbit-sharing
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

### Substrate

- **Differentiable CPTP substrate** (`qec_twin.primitives`): a
  CPTP-by-construction channel decoder (`diff_cptp_channel`) plus an exact
  differentiable circuit-to-observation forward model (`diff_circuit_sim`,
  `diff_rep_code`), `p(y|c) = Tr[M_y C(c)(rho0)]`, with the reusable mechanism and
  probe catalog (`mechanism_catalog`, `probe_catalog`).
- **Minimal DEM** (`qec_twin.dem`): parity map, fault graph, and stim-DEM
  extraction — the frozen-MWPM-decoder path only.

The B-path mainline is `qec_twin.experiments.twin` (calibration, `do()`
knobs, validity curve, alias bands, gating). Everything else — the discovery /
observability / catalog / Google program — was retired and removed (ADR 0009).

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
python -m pytest -q tests/        # run the test suite (twin B-path + substrate)
```

The twin B-path is driven through `qec_twin.experiments.twin` and its
tests under `tests/test_twin_*.py`; there are no standing console scripts.

## Docs

- `CONTEXT.md` — glossary and claim boundaries.
- `AGENTS.md` — main line, doc routing, and working rules.
- `docs/ARCHITECTURE.md` — module map.
- `docs/teacher_learner.md` — teacher/learner roles and isolation contract.
- `docs/TWIN.md` — binding twin spec: object contract, four capabilities, notation.
- `docs/IDENTIFIABILITY_AND_CRL_SURVEY.md` + `docs/papers/` — the CRL/finance toolset.
- `docs/adr/` — durable decisions (current spine 0006 → 0009).
