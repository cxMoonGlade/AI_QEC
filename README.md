# QEC Error-Mechanism Digital Twin

`qec_twin` is a QEC noise-learning research package. Its goal is a
**teacher-learner digital twin of QEC error mechanisms** — a validated causal
model of the device noise (the twin as a structural causal model; `do()` = Pearl
intervention) — that can **recover**, **understand**, **manipulate**, and
**predict** error mechanisms on hardware-realistic noise:

- **recover** — label-free calibration of mechanisms from observations;
- **understand** — interpret them, with honest uncertainty / alias bands;
- **manipulate** — channel-level `do()` knobs that predict ΔLER;
- **predict** — drift, rare-failure, and decoder-impact forecasting.

The organizing principle is the **causal model**: the circuit/DEM is the causal
graph, the mechanisms are its structural equations, and a channel-level `do()` is a
Pearl intervention whose ΔLER is validated against controlled-teacher ground truth —
never by calibration fit alone. Calibration is an ill-posed inverse problem, so
identifiability and honest bands (which mechanisms the data fixes, and where it
cannot) are central. See `docs/IDENTIFIABILITY_AND_CRL_SURVEY.md`.

> The package name `qec_twin` is a stable code identifier only. The earlier
> orbit-symmetry-compression thesis, and orbit-sharing
> as an identifiability lever, are retired — see `docs/adr/0005-retire-scope-reframe-twin.md`.

## Current state

**The counterfactual loop (the "B path") is validated at small exact scale.** On a
repetition-code toy: the twin is label-free calibrated by exact multi-context
Born-rule observation-NLL, a channel-level `do()` knob is applied, and its
predicted ΔLER is checked against controlled-teacher ground truth. Demonstrated
results — calibration recovers the teacher to machine precision; **probe richness
breaks the observational alias** (out-of-basis exotic prediction error collapses
~10⁵× once basis-rotated probes enter calibration); the recovered knob matches the
teacher's true ΔLER; moment-matched and shuffled-channel twins fail as
pre-registered. See ADR 0002/0003/0004.

This is a controlled, exact, small-scale capability result — **not** yet a
validated real-hardware twin. No Google physical-mechanism, drift, transfer, or
decoder-utility claim is made.

### Substrate

- **Exact differentiable forward** (`qec_twin.forward`): a CPTP-by-construction
  channel (`forward.cptp_channel`) plus an exact density-matrix
  circuit-to-observation forward model (`forward.exact`),
  `p(y|c) = Tr[M_y C(c)(rho0)]`. The density-matrix backend is feasibility-only
  (≤~15 qubits); `forward.scalable` is the placeholder >50-qubit carrier (ADR 0005).
  Mechanism definitions + controlled teachers live in `qec_twin.mechanisms`; the
  probe-richness context ladder in `qec_twin.contexts`.
- **Minimal DEM** (`qec_twin.decoder`): parity map (`DemParityMap`), fault graph
  (`FaultGraph`), and stim-DEM extraction — the frozen-MWPM-decoder path only.

The B-path is the four capability modules over this substrate —
`qec_twin.calibration` (recover) and `qec_twin.knobs` (channel-level `do()` → ΔLER),
with evaluator-side gating / alias bands / validity curve in `qec_twin.audit`
(`understand` and `prediction` are placeholders). Everything else — the discovery /
observability / catalog / Google program — was retired and removed (ADR 0005).

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

The twin B-path is driven through the library — `qec_twin.calibration` / `knobs` /
`audit` over `qec_twin.forward` — and its tests under `tests/test_twin_*.py`; there
are no standing console scripts.

## Docs

- `CONTEXT.md` — glossary and claim boundaries.
- `AGENTS.md` — main line, doc routing, and working rules.
- `docs/ARCHITECTURE.md` — module map.
- `docs/teacher_learner.md` — teacher/learner roles and isolation contract.
- `docs/TWIN.md` — binding twin spec: object contract, four capabilities, notation.
- `docs/IDENTIFIABILITY_AND_CRL_SURVEY.md` + `docs/papers/` — the CRL / identifiability toolset.
- `docs/adr/` — durable decisions (current spine 0001 → 0010).
