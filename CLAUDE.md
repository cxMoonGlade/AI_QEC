# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands should be run inside the `aiqec` Conda environment:

```bash
# Install (editable)
conda run -n aiqec python -m pip install -e .

# Run all tests
conda run -n aiqec python -m pytest -q

# Run a single test file
conda run -n aiqec python -m pytest -q tests/test_<name>.py

# Verify CUDA visibility before GPU-heavy runs
conda run -n aiqec python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else None)"

# Print toolbox manifest
scope-static-toolbox
```

Do not set `PYTHONPATH="$PWD/src"` — it can interfere with PyTorch CUDA/NVML discovery. Use the editable install. If console scripts are missing, reinstall with `conda run -n aiqec python -m pip install -e .`.

### Key experiment pipelines

**Google S3 V2 visible surface (mainline real-data path):**
```bash
scope-google-s3-visible-cache-v2 --config configs/scope_static/google_s3_visible_cache_v2.yaml
scope-google-s3-visible-aggregate-v2 --config configs/scope_static/google_s3_visible_aggregate_v2.yaml
scope-google-s3-visible-adapter-v2 --config configs/scope_static/google_s3_visible_adapter_v2.yaml
```

**Controlled Stage 3/5 chain (current active path):**
```bash
conda run -n aiqec python -m scope_static.experiments.qec_noise_catalog.data_preparation_teacher \
  --config configs/scope_static/s5_medium_hard_allM_contract_teacher_20q_depth20_g20.yaml
conda run -n aiqec python -m scope_static.experiments.stage3.protocol_freeze \
  --config configs/scope_static/stage3a_protocol_freeze.yaml
conda run -n aiqec python -m scope_static.experiments.stage3.discovery_model \
  --config configs/scope_static/stage3b1_discovery_model.yaml
```

All configs live under `configs/scope_static/`. All outputs write to `outputs/scope_static/` and `outputs/google_static/`.

## Architecture

This is a GPU-first QEC noise-learning research package. Target workstation has at least RTX 5090 class CUDA. CPU-only results must not be treated as evidence of GPU path failure.

### Package map (`src/scope_static/`)

```
dem/                     Stage 1 DEM/Bernoulli: parity maps, fault logits, likelihoods, baselines
google/                  Google hardware data readers, inventory, S3 visible surface cache/adapter
primitives/              Low-level math: channels, PTM, CPTP/POVM audits, density sim,
                         diff_cptp_channel (PhysDec), diff_circuit_sim (exact forward model)
data_preparation/        Layer1 preprocessing – teacher generator
teacher/                 Layer 2 teacher self-audit; verifies teacher/catalog separability
learner/                 Layer 3 learner; visible-only mechanism classification and replay quality
identifiability/         Observational alias quotient and identifiability diagnostics
mechanism_observability/ S2D local inverse, typed SPAM/gate features, generator-space calibration
mechanism_discovery/     Stage 3/4/5 discovery, assignment, transfer, bridge, robustness artifacts
catalog_pipeline/        Controlled-catalog orchestration façade
experiments/             Thin CLI/config wrappers only, grouped by experiment family:
  static/                DEM and Stage 2 static-discovery commands
  qec_noise_catalog/     Catalog teacher, validation, observability commands
  stage3/                Stage 3A–3D commands
  stage4/                S4 bridge, source, transfer, and Google-unit commands
  stage5/                S5 context-relative property-recovery commands
  willow_data/           Google/Willow inventory, GPU diagnostics, S3 cache and visible adapters
  scope_twin/            Active SCOPE-Twin B-path experiments (new)
cuda/                    C++/CUDA exact DEM/window kernels
```

### Layer architecture

The catalog validation flow is:

```
mechanism catalog + enabled mechanism set
  -> data_preparation (Layer1 preprocessing – teacher generator)
  -> teacher (Layer 2 teacher self-audit)
  -> learner (Layer 3 learner: visible-only recovery and replay)
  -> mechanism_discovery (Stage 3–5 unsupervised latent quotient discovery)
```

**Isolation contract:** Evaluator-only labels, exact channels, PTMs, Kraus matrices, teacher IDs, and oracle prototypes must never enter the learner path. Teacher may use teacher-internal evidence for Layer 2 self-audit; Learner may not.

### Stage summary

| Stage | Status | Claim |
|---|---|---|
| S1 DEM/Bernoulli | Closed | Fault logit learning over canonicalized DEM faults |
| S2 catalog validation | Closed | No-leakage physical-mechanism catalog, teacher/learner separability |
| S3 discovery | Mainline | Visible-only latent structure recovery, Google V2 syndrome-response replay |
| S4 bridge/transfer | Active | Artifact-contract bridge, Google-unit source expansion |
| S5 effect audits | Evaluator-only | Context-relative action location and mechanism strength |
| SCOPE-Twin B path | Active build | Label-free CPTP calibration + counterfactual knob validation on small rep-code |

### Active priorities (2026-06)

The SCOPE-Twin **B path** is the highest current priority (ADR 0006): close the interventional loop on a small, exactly-simulable system before scaling. Core primitives:

- `scope_static.primitives.diff_cptp_channel` — CPTP-by-construction PhysDec channel decoder
- `scope_static.primitives.diff_circuit_sim` — exact differentiable `p_Θ(y|c) = Tr[M_y C_Θ(c)(ρ_0)]`
- Calibration: exact Born-rule NLL objective, multi-context `C_cal(r)`, NOT DEM moment-matching (ADR 0007)

The B path is a controlled capability substrate, not a validated twin. It makes no Google physical-mechanism or counterfactual claims.

## Code Conventions

### Notation (enforced — do not deviate)

| Symbol | Meaning |
|---|---|
| `A` | DEM parity map `F_2^{B×M}` — never use for assignment |
| `S` or `Pi` | Learned discovery assignment matrix |
| `lambda_j` | Stage-1 fault logit `logit(p_j)` — never `ell_j` |
| `omega(j)` | Known orbit assignment |
| `m` | Logical observable bit — never `o` |
| `e` | Latent DEM fault vector |
| `y` | Observed detector/logical bit vector |
| `K` | Prototype count |
| `B` | Number of observation bits |
| `M` | Number of effective DEM faults |

### Numerical floor

Use `scope_static.numerics.NUMERICAL_ZERO == 1e-12` for all floating numerical floors, probability floors, and simulation thresholds. Do not replace structural zeros (Pauli matrix entries, bit values, integer indices, counts, or exact algebraic identities).

### Module placement rules

- New implementation code → the responsibility package that owns it (not a flat module under `src/scope_static/`)
- New primitive math/sampling → `scope_static.primitives`
- New experiment wrappers → the matching `experiments/<family>/` subfolder
- Do not add flat `run_stage3*`, `run_stage4*`, `run_google*`, `run_static*`, `run_phyc*`, `run_layer*`, or `run_s2d*` modules anywhere under `scope_static.experiments`
- Do not rebuild a broad `scope_static.physical` package

### Claim discipline

Stage 4/5 artifacts and Google real-data results may claim only **visible syndrome-response replay/transfer evidence**, never:
- True Google physical mechanism recovery
- Google public F/M label recovery
- Google legacy catalog-ID (ARI/NMI) recovery
- Born-rule physical generation
- CPTP/GKSL channel learning (until the SCOPE-Twin B path validates it)

The `raw_target_only` score plus block-normalized reporting and controls is the current Google V2 headline metric, not `full_target` alone.

## Key Reference Documents

- `CONTEXT.md` — glossary and claim boundaries (read first for domain terms)
- `docs/ARCHITECTURE.md` — full package map
- `docs/SCOPE_TWIN.md` — SCOPE-Twin notation and object contract (reserved symbols)
- `docs/teacher_learner.md` — teacher/learner isolation contract
- `docs/RUNBOOK.md` — full command recipes
- `docs/adr/0006-cptp-twin-build-order.md` — why B path comes before A and C
- `docs/adr/0007-b-validation-methodology.md` — calibration objective and probe richness ladder
- `docs/BENCHMARKS_AND_BASELINES.md` — baseline selection rules and evidence ladder
