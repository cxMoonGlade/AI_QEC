# Stage 2 Roadmap: SCOPE-Static Discovery

This roadmap is the compact execution view for Stage 2. The detailed contract
and historical run notes live in `docs/SCOPE_STATIC_DISC.md`.

Stage 2 keeps the Stage 1 fixed DEM/Bernoulli likelihood:

```text
e_j ~ Bernoulli(p_j)
y = A e mod 2
lambda_j = logit(p_j)
```

Use `A` only for the DEM parity map, `omega(j)` for hidden oracle labels, and
`S` or `Pi` for learned discovery assignments.

## Claim Boundary

Stage 2 can claim synthetic oracle recovery only when evaluator-visible labels
exist and ARI/NMI are reported without using those labels for training,
initialization, selection, or checkpointing.

Stage 2 must not claim true physical-mechanism recovery on Google data. Google
work is external predictive validation unless an explicit proxy partition is
defined and labelled as proxy-only.

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
qiskit-aer-gpu
qiskit==1.4.5
qiskit-aer-gpu==0.15.1
```

CPU Aer fallback is disabled for default S2D runs. Treat a missing GPU as an
environment visibility problem to diagnose, not as evidence for a CPU-first
experiment design. Do not install `qiskit-ibm-runtime` in the `aiqec` S2D
environment; current runtime packages require Qiskit 2.x, while Aer GPU 0.15.1
needs the Qiskit 1.x provider API.

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
  --config configs/scope_static/d3_r1_S2D_PHYS_aer_gpu.yaml \
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

Current default teacher mechanisms:

```text
Gate/process:
M0 stochastic Pauli gate error
M1 coherent RZZ over-rotation
M2 coherent RX over-rotation
M3 coherent RZ over-rotation
M4 amplitude damping gate error
M5 hard custom non-Pauli Kraus channel
M6 two-qubit depolarizing after RZZ
M7 coherent RXX/RYY perturbation
M8 spectator crosstalk RZ/ZZ
M9 correlated two-qubit relaxation surrogate
M10 drifted coherent over-rotation with location-varying strength
M11 idle dephasing / relaxation error
M12 operation-dependent error

Readout/measurement:
M13 readout 0->1 bias
M14 readout 1->0 bias
M15 symmetric readout assignment noise
M16 measurement-context bias

Prep/reset:
M17 reset-to-1 bias
M18 prep-axis / reset-asymmetry bias

Other:
M19 weak Type-4-like PTM mixing
```

Named mechanism sets:

```text
set_A: M0-M4 plus M13-M16
set_B: M0-M7 plus M13-M16
set_C: M0-M9 plus M13-M16
set_D: M0-M18
allM:  M0-M19
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
S2D.11: typed gate/readout/prep learner was close on set_D but failed M1 recall.
S2D.11b: M1 gate-branch calibration converted set_D into a pass.
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

### Stage 2B: Google External Validation

Question:

```text
Do discovered/local-inverse representations improve real-data predictive
utility, calibration, transfer, or decoder-facing value?
```

Google data has no true hidden physical mechanism labels. Report predictive
metrics and explicitly labelled proxy ARI/NMI only.

## Immediate Next Steps

1. Keep `aiqec` clean for Aer GPU S2D:

   ```text
   qiskit==1.4.5
   qiskit-aer-gpu==0.15.1
   no qiskit-aer
   no qiskit-ibm-runtime
   ```

2. Keep PHYS0 -> PHYS1 -> PHYS2 -> PHYS3 artifacts refreshed together when
   changing the physical teacher or local-inverse representation.
3. Use `docs/ARCHITECTURE.md` for module routing and `docs/RUNBOOK.md` for
   command recipes.
4. After S2D.11b, do not treat readout/prep as the main blocker. The current
   passed fix is gate-branch M1 calibration over existing S2D.11 artifacts.
