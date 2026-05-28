# Code Architecture

This repository implements `scope_static`, a fixed-context QEC research package.
The primary implemented object is still the DEM/Bernoulli model:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
lambda_j = logit(p_j)
```

The physical-oracle S2D work is synthetic validation and observability tooling
around local physical mechanisms. It is not a hardware CPTP/GST/GKSL learner.

The project-level target is the six-axis physical generation problem: prove that
a physically constrained generation model holds simultaneously in generation
fidelity, interpretability, decoder utility, cross-context generalization, drift
prediction, and identifiability. The current architecture contains partial
static and synthetic-oracle slices toward that target, not the complete
SCOPE-Twin solution.

## Package Map

```text
src/scope_static/
  fault_graph.py          canonical DEM fault graph and feature audits
  stim_dem.py             Stim circuit/DEM construction helpers
  parity_map.py           parity-map utilities
  fields.py               local, hard-orbit, soft-orbit, and discovery logit fields
  likelihood.py           exact global/window DEM likelihood and CUDA dispatch
  likelihoods/            objective adapters such as local-window parity
  windows.py              local-window builders and audits
  training.py             generic field fitting loop
  evidence.py             metrics, threshold summaries, compression audits
  baselines.py            local, DMLE-style, hard-orbit, soft-orbit baselines
  discovery.py            Stage 2 assignment metrics and known-orbit deltas
  hardening.py            Stage 2A.1 assignment hardening helpers
  identifiability/        DISC10 passive visible-signature clustering
  multi_env.py            DISC12 shared-assignment multi-environment models
  local_mechanism.py      Stage 2C local-inverse representation transforms
  google_set1.py          Google Set1 read-only adapter
  google_mechanism.py     Google proxy partitions and local-inverse audits
  physical/               S2D physical teacher, PTM, observability, typed learners
  physical_oracle/        PHYS1/PHYS2/PHYS3 stack facade
  experiments/            runnable `python -m ...` entry points
  cuda/                   C++/CUDA exact DEM/window kernels
```

`configs/scope_static/*.yaml` holds reproducible experiment plans. Runners write
artifacts under `outputs/scope_static/` or `outputs/google_static/`.

## Stage 1 Flow

Stage 1 learns `lambda_j` over effective DEM fault columns.

```text
Stim circuit or synthetic DEM
-> FaultGraph canonicalization
-> window plan / exact objective
-> FaultLogitField from fields.py
-> fit_field
-> evidence records, graph audits, window audits, compression audits
```

The scalable interface is sparse fault support plus packed masks. Dense `A`
exists for small tests and exact toy runs.

The main model families are:

```text
local
dmle_qec
hard_orbit
soft_feature_orbit
```

Local-window exact likelihood can use pure PyTorch or the C++/CUDA extension.
The Google runner is GPU-first and uses prepared graph/window caches to avoid
rebuilding expensive state across models, samples, and transfer evaluations.

## Stage 2 Static Flow

Stage 2 keeps the same DEM parity likelihood but withholds the known orbit map
from discovery learners.

```text
synthetic teacher with hidden omega(j)
-> sampled observations y
-> discovery field S[j, k] or local-inverse representation
-> evaluator-only ARI/NMI against omega(j)
```

The important tracks are:

```text
Stage 2A: direct free-assignment recovery of hidden DEM quotient
Stage 2C: local-inverse-first mechanism discovery
Stage 2D: active local-logit observability and typed physical learners
Stage 2E: Born-local physical baseline gate
Stage 2B: Google external predictive validation, no true ARI/NMI
```

Stage 2A established that direct `S`/`alpha` likelihood learning can be
predictive without reliably recovering hidden `omega(j)`. Stage 2C moved the
successful synthetic path to local inverse logits/probabilities, with recovery
evaluated only after training.

## S2D Physical-Oracle Flow

The S2D branch uses synthetic physical teachers to test whether learner-visible
probe data exposes local mechanism structure.

```text
PHYS1 physical teacher
-> finite-shot probe observations
-> PHYS2 oracle-only teacher self-distinguishability
-> PHYS3 learner-visible local-inverse recovery
```

Core implementation modules:

```text
physical/teacher.py                       teacher generation and mechanism taxonomy
physical/channels.py                      synthetic channel/mechanism definitions
physical/ptm.py                           oracle PTM and RZZ-type fingerprints
physical/local_inverse.py                 PHYS3 local-inverse discovery
physical/local_pauli_lindblad.py          S2D.9 local generator coordinates
physical/generator_space_calibration.py   S2D.10 nuisance geometry audit
physical/generator_invariant_calibration.py S2D.10b scalar invariants
physical/typed_spam_gate_invariant.py     S2D.11 typed gate/readout/prep learner
physical/m1_gate_calibration.py           S2D.11b M1 grouped calibration audit
physical/local_observable_teacher.py      Torch CUDA local-observable sampled teacher
physical/sampled_observation_separability.py PHYC2 sampled-observation separability
physical/sampled_quantum_error_quality.py PHYC3 mechanism-to-error quality audit
physical_oracle/stack.py                  PHYS1/PHYS2/PHYS3 facade
```

S2D.9 made local Pauli-Lindblad generator coordinates observable. S2D.10b
showed scalar invariants expose the coherent-vs-stochastic and RZZ-axis signal.
S2D.11 splits rows into visible typed branches:

```text
measure -> readout_branch
reset   -> prep_reset_branch
other   -> gate_process_branch
```

S2D.11b then reuses the S2D.11 artifacts and changes only gate-branch M1
calibration, converting the set_D typed learner into a pass.

## PHYC2/PHYC3 Local-Observable Flow

The local-observable Torch CUDA path is a scalable sampled-observation teacher,
not a full-circuit simulator:

```text
mechanism records + probe metadata
-> local response probabilities
-> Torch CUDA Bernoulli samples
-> PHYC2 grouped sampled-observation separability
-> PHYC3 mechanism-to-error prototype quality
```

`PHYC2-separability_v2` is an engineered separability stress teacher. It uses
branch-specific local response profiles, GPU-side pair-correlation overlays,
and slot remapping to avoid local-response overwrite in the PHYS1-compatible
`observations.npz` tensor. PHYC2 neutralizes synthetic slot geometry and runs a
slot-only leakage control to ensure slot/layout metadata alone do not classify
mechanisms.

PHYC3 consumes PHYC2 grouped predictions. For each held-out circuit group it
builds fold-trained channel/readout prototypes from training groups, maps each
predicted mechanism label to its prototype, and compares that vector to the
evaluator-only oracle channel/readout matrix. This validates
mechanism-to-error translation quality for the synthetic teacher; it does not
directly reconstruct a continuous channel from raw shots.

Stage 2E is the current physical-baseline gate:

```text
PHYC2-Born-local:
  local probe state -> CPTP/readout mechanism -> exact local Born probability
  -> GPU sampled observation bits
```

The Born-local teacher must not use mechanism-label response templates,
artificial response-code margins, or post-sampling pair-correlation overlays.
Stage 3 is blocked until the Born-local PHYC2/PHYC3 path passes. See
`docs/adr/0004-stage2e-born-local-gate.md` for the milestone-gating decision.

## Physical Oracle Stack Facade

`scope_static.physical_oracle.run_physical_oracle_stack` centralizes PHYS1,
PHYS2, and PHYS3 ordering while preserving the existing stage artifacts.

It writes:

```text
physical_oracle_stack.json
physical_oracle_stack.md
S2D_PHYS1_teacher/
S2D_PHYS2_oracle_separability/
S2D_PHYS3_local_inverse/
```

The stack keeps verdicts separate:

```text
teacher_self_verdict       oracle-only teacher separability
learner_recovery_verdict   learner-visible PHYS3 recovery
overall_diagnosis          probe_limited / learner_limited / near_strong / strong_recovery
```

With `run_local_inverse: auto`, PHYS3 is skipped if PHYS2 is below the configured
self-distinguishability threshold.

## Claim Boundaries

Valid implemented claims:

- fixed-context DEM/Bernoulli likelihood experiments.
- known-orbit, discovery, and local-inverse comparisons inside that DEM family.
- synthetic oracle ARI/NMI when hidden labels are evaluator-only.
- S2D physical-oracle observability diagnostics when labelled synthetic.
- Google predictive validation with proxy labels only when explicitly labelled.

Invalid claims:

- hardware CPTP/GST/GKSL learning.
- full noisy-circuit Born-rule likelihood.
- real-hardware true latent mechanism recovery.
- temporal drift or amortized SCOPE-Twin as implemented evidence.
- complete six-axis physical generation evidence.
