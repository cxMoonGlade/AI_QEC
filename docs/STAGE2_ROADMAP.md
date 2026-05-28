# Stage 2 Roadmap: SCOPE-Static Discovery

This roadmap is the compact execution view for Stage 2. The detailed contract
and historical run notes live in `docs/SCOPE_STATIC_DISC.md`.

Stage 2 keeps the Stage 1 fixed DEM/Bernoulli likelihood:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
lambda_j = logit(p_j)
```

Here `A in F_2^{B x M}` is the DEM parity map, `e in {0,1}^M` is the
latent effective-fault vector for one shot, and `y in {0,1}^B` is the observed
detector/logical bit vector. `M` is the number of effective DEM fault
mechanisms after duplicate-mask canonicalization; `B` is the number of
observation bits.

Use `A` only for the DEM parity map, `omega(j)` for hidden oracle labels, and
`S` or `Pi` for learned discovery assignments.

## Claim Boundary

Stage 2 can claim synthetic oracle recovery only when evaluator-visible labels
exist and ARI/NMI are reported without using those labels for training,
initialization, selection, or checkpointing.

Stage 2 must not claim true physical-mechanism recovery on Google data. Google
work is external predictive validation unless an explicit proxy partition is
defined and labelled as proxy-only.

The project-level target remains the six-axis physical generation problem:
generation fidelity, interpretability, decoder utility, cross-context
generalization, drift prediction, and identifiability. Stage 2 mainly builds the
identifiability and early interpretability evidence needed before that full
physical generation claim can be made.

## Tracks

### Stage 2A: Static DEM Quotient Recovery

Question:

```text
Can observations recover hidden DEM-fault sharing structure omega(j)?
```

Status:

- Stage 2A.0 free assignment: likelihood can improve without reliable quotient
  recovery.
- DISC10/DISC13/DISC13b: hidden quotient is valid in teacher parameter space,
  but passive observation likelihood does not isolate it cleanly.
- Stage 2A.1/2A.2 remain useful diagnostics for optimization and
  identifiability-aware probe design.

Keep reporting `delta_nll_known_orbit`, ARI/NMI, active prototypes, collapse
flags, and evaluator-only label-use audits.

### Stage 2C: Local Inverse Representation Discovery

Question:

```text
Can fitted local inverse logits/probabilities be denoised, factorized, and
clustered better than direct S/alpha assignment learning?
```

Status:

- DISC15 promoted local inverse representations to a first-class route.
- DISC15c/16a show the predeclared `local_logit_probability` representation can
  reach strong recovery in the controlled synthetic setting.
- DISC16b freezes the claim as robustly near-strong, with failures dominated by
  split/merge near misses rather than collapse.

Next use Stage 2C as the default synthetic mechanism-discovery baseline:

```text
physical observations
-> local inverse probability / PTM-like response representation
-> clustering
-> ARI/NMI against oracle labels
```

### S2D_PHYS: Physical-Oracle Non-Stim Teacher

Question:

```text
Can the Stage 2C local-inverse-first route recover known oracle physical
mechanisms when data comes from a non-Stim physical-channel teacher?
```

Default backend:

```text
cudaq
cuda-quantum
target=nvidia option=fp32
```

CPU fallback is disabled for default S2D runs. Treat a missing GPU as an
environment visibility problem to diagnose, not as evidence for a CPU-first
experiment design.

Implemented gate order:

```text
S2D_PHYS0_preflight
S2D_PHYS1_teacher
S2D_PHYS2_oracle_separability
S2D_PHYS3_local_inverse
```

The preferred orchestration layer is the Physical Oracle Stack facade:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_physical_oracle_stack \
  --config configs/scope_static/d3_r1_S2D_PHYS_cudaq.yaml \
  --run-local-inverse auto
```

The facade preserves the existing PHYS1/PHYS2/PHYS3 artifact folders and adds
`physical_oracle_stack.json` plus `physical_oracle_stack.md`.

Artifacts:

```text
outputs/scope_static/S2D_PHYS0_preflight/backend_audit.{json,md}
outputs/scope_static/S2D_PHYS1_teacher/
outputs/scope_static/S2D_PHYS2_oracle_separability/
outputs/scope_static/S2D_PHYS3_local_inverse/
```

Current default teacher mechanisms are defined in
`src/scope_static/physical/mechanism_catalog.py` and documented in
`docs/error_mechanisms.md`. The renumbered implemented catalog has 35 distinct
mechanisms:

```text
set_A: M0-M9
set_B: M0-M14
set_C: M0-M24
set_D: M0-M34
allM:  M0-M34
```

Decision rule:

```text
S2D_PHYS2 ARI/NMI >= 0.90:
  default teacher is identifying; continue to S2D_PHYS3 local inverse discovery

0.70 <= ARI/NMI < 0.90:
  continue, but label the teacher/probe set as limited

ARI/NMI < 0.70:
  redesign probes before learner tests
```

Keep detailed S2D physical-oracle run notes in `docs/SCOPE_STATIC_DISC.md`; this
roadmap should stay as a compact orientation page.

Current PHYC2-balanced local-observable teacher result:

```text
outputs/scope_static/local_observable_gpu_allM_30q_depth30_30groups_v2_slot_remap/

allM, 30 qubits, depth 30, 30 groups, 10k shots:
  contract_passed true
  balanced_accuracy 1.0000
  min_class_recall 1.0000
  scrambled-control BA gap 0.8567
  PHYC3 contract_passed true
  PHYC3 mean predicted channel/readout distance 0.000085
  PHYC3 max predicted channel/readout distance 0.003292
```

This result uses `local_observable_response_model: separability_v2` and the
local-observable observation-slot remap. Synthetic slot geometry is neutralized
in PHYC2 features; branch flags and sampled response/correlation features remain
visible. Slot-only leakage control BA is `0.0000`.

Current PHYC2-weighted local-observable teacher result:

```text
outputs/scope_static/local_observable_gpu_allM_30q_depth30_weighted_v2_slot_remap/

allM, 30 qubits, depth 30, uneven support 2-8, 10k shots:
  contract_passed true
  balanced_accuracy 1.0000
  min_class_recall 1.0000
  prevalence_weighted_accuracy 1.0000
  rare_class_recall_min 1.0000
  scrambled-control BA gap 0.8779
  slot-only leakage control BA 0.0313
  no-remap ablation weighted BA 0.9708
```

Current PHYC3 quantum-error-quality diagnostic:

```text
outputs/scope_static/local_observable_gpu_allM_30q_depth30_weighted_v2_slot_remap/PHYC3_quantum_error_quality/

allM, 30 qubits, depth 30, uneven support 2-8, 10k shots:
  contract_passed true
  mechanism balanced_accuracy 1.0000
  mechanism min_class_recall 1.0000
  mean predicted channel/readout distance 0.000026
  max predicted channel/readout distance 0.001364
  incompatible predictions 0
```

PHYC3 consumes PHYC2 grouped predictions, builds fold-trained mechanism
channel/readout prototypes from training groups, and compares predicted
prototypes to evaluator-only oracle mechanism channels. For the
`separability_v2` teacher this is a mechanism-to-error translation diagnostic,
not evidence that the sampled observations came from Born-rule circuit physics.

Current PHYC2-weighted scalability smoke:

```text
outputs/scope_static/local_observable_gpu_allM_74q_depth200_weighted_v2_slot_remap/

allM, 74 qubits, depth 200, uneven support 2-8, 10k shots:
  contract_passed true
  balanced_accuracy 1.0000
  min_class_recall 1.0000
  prevalence_weighted_accuracy 1.0000
  rare_class_recall_min 1.0000
  slot-only leakage control BA 0.0479
  teacher total wall-clock 4.0741s
  artifact size 1.7G
```

The same PHYC3 audit also passes on the 74-qubit/depth-200 weighted artifact
with the same mechanism and channel-distance metrics.

Current S2D_PHYS3 default result:

```text
physical_local_inverse_probability:
  ARI 1.0000
  NMI 1.0000
  label physical_oracle_strong_recovery

direct S/alpha:
  ARI 0.6887
  NMI 0.8865
```

### Stage 2D: Active Local-Logit Observability

Question:

```text
Which probe contexts improve recoverability of local inverse logits?
```

Use Stage 2D for active probe design after the S2D_PHYS default teacher is
separable. Keep it distinct from S2D_PHYS: Stage 2D designs probes, while
S2D_PHYS tests oracle physical mechanism recovery.

Current implementation state:

```text
S2D.7:  static mixed-basis final-shot moments were negative.
S2D.8a: depth sweep was control-matched negative.
S2D.8b: echo/no-echo was control-limited.
S2D.8c: saved-feature ceiling failed on balanced setB/setC.
S2D.8d: minimal deterministic interventions matched scrambled controls.
S2D.9:  local Pauli-Lindblad generator coordinates are algebraically observable.
S2D.10: generator-space calibration exposed nuisance geometry.
S2D.10b: scalar generator invariants made setB/setC grouped recovery pass.
S2D.11: typed gate/readout/prep learner was close on set_D but failed M8 recall.
S2D.11b: M8 gate-branch calibration converted set_D into a pass; artifact names still say `M1`.
```

Primary typed learner command:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d11_typed_spam_gate_invariant_learner \
  --config configs/scope_static/s2d11_typed_spam_gate_invariant_learner.yaml
```

Calibration-only S2D.11b command:

```bash
conda run --no-capture-output -n aiqec python -u -m scope_static.experiments.run_s2d11b_m1_gate_branch_grouped_calibration_audit \
  --config configs/scope_static/s2d11b_m1_gate_branch_grouped_calibration_audit.yaml
```

### Stage 2E: Born-Local Physical Baseline

Question:

```text
Can sampled local observations be generated from exact local Born probabilities
and still support mechanism classification plus high-quality quantum-error
reconstruction?
```

Stage 2E adds a physically correct local teacher:

```text
local probe state -> CPTP/readout mechanism -> exact local Born probability
-> GPU sampled observation bits
```

This teacher has effective circuit depth one by design: one explicit local
context, one ideal local operation when applicable, one mechanism
channel/readout, then one local POVM. Configured schedule depths remain artifact
provenance, not hidden repeated channel composition. The teacher must not use
mechanism-label response templates, artificial response-code margins, or
post-sampling pair-correlation overlays. Two-qubit correlations should come
from the exact two-qubit output distribution. Validate small cases against
direct density-matrix math and CUDA-Q local circuits, then rerun PHYC2 and
PHYC3.

M8 `spectator_crosstalk_rz_or_zz` stays outside the Stage 2E.1 thin slice until
the spectator contract specifies victim, aggressor operation or edge, and
whether the observable local support is RZ-on-victim or ZZ-on-pair.

The intended distinction is:

```text
PHYC2-separability_v2 / PHYC3-separability_v2:
  engineered sampled-observation stress teacher

PHYC2-Born-local / PHYC3-Born-local:
  mathematically and physically correct local baseline
```

Stage 3 is blocked until Stage 2E passes. The current `separability_v2`
evidence is good enough to motivate Stage 2E, but it does not close the physical
baseline milestone. The gating decision is recorded in
`docs/adr/0004-stage2e-born-local-gate.md`.

### Stage 2B: Google External Validation

Question:

```text
Do discovered/local-inverse representations improve real-data predictive
utility, calibration, transfer, or decoder-facing value?
```

Google data has no true hidden physical mechanism labels. Report predictive
metrics and explicitly labelled proxy ARI/NMI only.

## Immediate Next Steps

1. Keep `aiqec` clean for CUDA-Q S2D:

   ```text
   cuda-quantum installed
   CUDA-Q target nvidia visible
   no physical-teacher dependency on legacy simulator packages
   ```

2. Keep PHYS0 -> PHYS1 -> PHYS2 -> PHYS3 artifacts refreshed together when
   changing the physical teacher or local-inverse representation.
3. Use `docs/ARCHITECTURE.md` for module routing and `docs/RUNBOOK.md` for
   command recipes.
4. Run the S2E.1 learner test on existing PHYC2-Born-local data. The test
   reuses PHYC2 metrics and checks Born-local source, no overlays, and full
   S2E.1 mechanism scope before any Stage 3 work.
