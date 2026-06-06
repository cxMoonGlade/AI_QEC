# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Main line

The project builds **the twin**: a teacher-learner, quantitative-finance-structured
digital twin of QEC error mechanisms that **recovers, understands, manipulates, and
predicts** hardware error mechanisms. Binding spec: `docs/TWIN.md`. The earlier
"SCOPE / Symmetry-Compressed Orbit-Physical Emulator" thesis and orbit-sharing as an
identifiability lever are retired (`docs/adr/0009-retire-scope-reframe-twin.md`);
`scope_static` is a stable code identifier only, not the thesis.

Path: **B (validate the counterfactual loop on a controlled toy — done on the
rep-code) → harden (richer/correlated mechanisms, larger d, drift) → C (real
Google)**. The methodological spine is the finance↔QEC calibration isomorphism
(ADR 0008), exact Born-rule observation-NLL calibration (ADR 0007), and honest
alias/uncertainty bands. Counterfactual validity is established only against
controlled-teacher `do()` ground truth, never by calibration fit alone.

## Commands

All commands run inside the `aiqec` Conda environment:

```bash
conda run -n aiqec python -m pip install -e .                  # install (editable)
conda run -n aiqec python -m pip install -e '.[cuda-extension]' # + ninja, for the JIT CUDA backend
conda run -n aiqec python -m pytest -q tests/                  # full suite — scope to tests/ (see note)
conda run -n aiqec python -m pytest -q tests/test_<name>.py    # single test file
# Verify CUDA before GPU-heavy runs:
conda run -n aiqec python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)"
scope-static-toolbox                                           # toolbox manifest
```

Always scope pytest to `tests/`. Bare `pytest -q` from the repo root recurses into
`external/` — ~480 vendored baseline/reference test files (pyro, Stim, PyMatching,
pgmpy, …) whose collection hangs or errors. `external/` is gitignored and not part
of `scope_static`; our suite is the ~450 tests under `tests/`.

Do not set `PYTHONPATH="$PWD/src"` — it can interfere with PyTorch CUDA/NVML
discovery; use the editable install. If console scripts are missing, reinstall.

### Key paths

- **The twin (current active path)** — B-path calibration, `do()` knobs, validity
  curve, alias bands, gating: `scope_static.experiments.scope_twin.*` on the exact
  primitives `scope_static.primitives.diff_{cptp_channel,circuit_sim,rep_code}`.
- **Controlled catalog substrate** (teacher generator → teacher audit → label-free
  learner): `scope_static.experiments.qec_noise_catalog.*`.
- **Google V2 visible surface** (bounded no-oracle real-data replay):
  `scope-google-s3-visible-{cache,aggregate,adapter}-v2`.

Configs live under `configs/scope_static/`; outputs under `outputs/`. See
`docs/RUNBOOK.md` for the full command set.

## Architecture

GPU-first QEC research package; target workstation has ≥ RTX 5090 class CUDA.
CPU-only results are not evidence of a GPU-path failure.

### Package map (`src/scope_static/`)

```
primitives/              channels, PTM, CPTP/POVM audits, density sim, + the differentiable substrate
                         diff_cptp_channel (PhysDec), diff_circuit_sim (exact forward), diff_rep_code
dem/                     DEM/Bernoulli: parity maps, fault logits, likelihoods, baselines
google/                  Google/Willow readers, inventory, S3 visible surface cache/adapter
data_preparation/        teacher generator (mechanism records, probes, sampled obs, audits)
teacher/                 teacher self-audit; verifies teacher/catalog separability
learner/                 label-free learner; visible recovery + replay quality
identifiability/         observational alias quotient + identifiability diagnostics
mechanism_observability/ local inverse, typed SPAM/gate features, calibration
mechanism_discovery/     latent assignment, prototype, transfer, robustness, effect audits
catalog_pipeline/        controlled-catalog orchestration façade
experiments/             thin CLI/config wrappers, grouped by family: static/, qec_noise_catalog/,
                         stage3/, stage4/, stage5/, willow_data/, scope_twin/ (the twin B-path)
cuda/                    C++/CUDA exact DEM/window kernels — optional, JIT-compiled at
                         runtime via torch cpp_extension (+ninja); the pure-PyTorch path
                         is the correctness oracle, so there is nothing to pre-build
```

Repo layout beyond the package: `configs/` (run configs), `outputs/` (generated,
gitignored), `docs/` (specs + ADRs), and `external/` (gitignored vendored baseline
and reference repos — not imported by `scope_static`, excluded from our test scope).

### Isolation contract

Evaluator-only labels, exact channels, PTMs, Kraus matrices, teacher IDs, and
oracle prototypes must never enter the learner path. The teacher may use
teacher-internal evidence for its self-audit; the learner may not.

### Status

- **The twin — B path: validated on an exact rep-code toy.** Label-free
  calibration recovers a coherent teacher (`calib_kl ≈ 0`); the `do()` knob matches
  the teacher's true ΔLER; negative controls fail as pre-registered (moment-matched
  ≈ 900×, shuffled-channel ≈ 1400× worse); probe richness breaks the alias; Tier-0
  bands cover truth and shrink with richness. d3→d5 does not break the loop.
  Hardening (richer/correlated mechanisms) is next. See ADR 0006/0007/0008.
- **Substrate (valid, claim-bounded):** DEM/Bernoulli core (S1), controlled
  no-leakage catalog (S2), visible-only discovery + Google V2 replay, S5
  evaluator-only effect audits. These support the teacher-learner method; they do
  not claim hardware physical-mechanism recovery.

## Code conventions

### Notation (enforced — do not deviate)

| Symbol | Meaning |
|---|---|
| `A` | DEM parity map `F_2^{B×M}` — never use for assignment |
| `S` or `Pi` | Learned discovery assignment matrix |
| `lambda_j` | Fault logit `logit(p_j)` — never `ell_j` |
| `omega(j)` | Known orbit (DEM grouping) — a symbol reservation, not an identifiability lever (ADR 0009) |
| `m` | Logical observable bit — never `o` |
| `e` | Latent DEM fault vector |
| `y` | Observed detector/logical bit vector |
| `K` | Prototype count; `B` observation bits; `M` effective DEM faults |

### Numerical floor

Use `scope_static.numerics.NUMERICAL_ZERO == 1e-12` for all floating numerical
floors, probability floors, and simulation thresholds. Do not replace structural
zeros (Pauli matrix entries, bit values, integer indices, counts, exact algebraic
identities).

### Module placement

- New implementation code → the responsibility package that owns it (not a flat module under `src/scope_static/`).
- New primitive math/sampling → `scope_static.primitives`; new experiment wrappers → the matching `experiments/<family>/`.
- Do not add flat `run_stage3*`, `run_stage4*`, `run_google*`, `run_static*`, `run_phyc*`, `run_layer*`, or `run_s2d*` modules under `scope_static.experiments`.
- Do not rebuild a broad `scope_static.physical` package. Do not rename the `scope_static` package (ADR 0009 #3).

### Claim discipline

Controlled, small-scale, exact. The twin makes **no** Google physical-mechanism,
public-label, legacy-catalog-ID, Born-rule-generation, or CPTP/GKSL-learning claim
beyond the validated controlled loop until C is reached and earned. Google
real-data results claim only bounded visible syndrome-response replay/transfer; the
`raw_target_only` block-normalized score plus controls is the Google V2 headline,
not `full_target` alone. Report honest bands; never assume identifiability that
probe richness did not earn.

## Key reference documents

- `docs/TWIN.md` — binding twin spec: object contract, four capabilities, finance methodology, notation.
- `CONTEXT.md` — glossary and claim boundaries (read first for domain terms).
- `AGENTS.md` — main line, doc routing, working rules.
- `docs/ARCHITECTURE.md` — full package map.
- `docs/teacher_learner.md` — teacher/learner isolation contract.
- `docs/RUNBOOK.md` — full command recipes.
- `docs/IDENTIFIABILITY_AND_CRL_SURVEY.md` + `docs/papers/` — CRL/finance toolset and cached references.
- `docs/adr/` — decisions; current spine 0006 (build order) → 0007 (B methodology) → 0008 (finance framing) → 0009 (retire SCOPE / reframe).
