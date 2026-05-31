# Physicality Boundary

This note states what is physically constrained by the current implementation
and what is not yet claimed.

## Current Implementation

The data-preparation teacher is the first-class physical-process teacher. It generates
teacher-declared noisy QEC observations from the implemented physical mechanism
catalog, but it is not only a sampler: it validates the local process contract
before sampling and runs a post-sampling physicality audit before accepting the
artifact.

Each enabled mechanism maps to one of three representations:

- **unitary channel**: coherent control and coupling errors such as RX, RZ,
  RZZ, RXX/RYY, and mixed two-qubit rotations;
- **Kraus channel**: stochastic Pauli, depolarizing, amplitude damping,
  correlated relaxation, thermal excitation, reset, and non-Pauli stress
  channels;
- **classical readout assignment matrix**: readout and measurement-context
  bias mechanisms.

Enabling a mechanism ID selects its catalog definition and parameters. There is
no separate global `enable_cptp` switch. Physicality comes from the selected
mechanism implementation.

The legacy full-circuit CUDA-Q implementation remains as the underlying sampler
used by data preparation. Public evidence should cite the teacher contract,
not a bare legacy sampler artifact.

Legacy public entrypoints, including `scope-catalog-teacher` and
`scope_static.primitives.probe_catalog.generate_catalog_teacher_dataset`, now route
through data preparation as compatibility shims.

## Current Claim

Valid:

- Data preparation generates teacher-declared noisy QEC observations from implemented
  unitary/Kraus/readout mechanism definitions after a blocking pre-sampling
  physical-process contract.
- When learner predicts a catalog mechanism and reuses its catalog channel, the
  generated channel-level replay inherits the catalog mechanism definition.
- Learner can also replay and score visible empirical noise distributions from
  learner-visible observations.

Not claimed yet:

- arbitrary learned CPTP channel generation by construction;
- arbitrary learned GKSL generator recovery;
- hardware CPTP/GST/GKSL learning;
- proof that every future user-supplied custom channel is physical without a
  per-run audit.

## Data-Preparation Generation Contract

Data preparation writes:

```text
layer1p_pre_sampling_contract.json
layer1p_teacher_contract.json
Layer1_teacher_physicality_audit/
```

The generation chain is:

```text
configuration
-> declared mechanism catalog
-> pre-sampling CPTP/POVM/readout contract
-> full-circuit CUDA-Q Born-rule sampling
-> post-sampling physicality audit
-> accepted data-preparation teacher artifact
```

The mathematical object is:

```text
p_Theta(y | c) = Tr[M_y C_Theta(c)(rho_0)]
```

where `C_Theta(c)` is the circuit-ordered composition of ideal operations and
declared local noise modules, and `M_y` is the final measurement/readout POVM or
instrument-induced classical observation event.

Data are not CPTP. The physical object is the generating process.

## Local CPTP / POVM Proof

Data preparation uses `scope_static.primitives.cptp_guardrail` as an internal validator. That module should
remain in the codebase: it is not a legacy teacher path, it is the low-level
proof/check routine used by data preparation before sampling.

The guardrail checks every enabled mechanism record:

```text
unitary:
  U^dagger U = I

Kraus:
  sum_i K_i^dagger K_i = I

readout:
  A[x,y] >= 0
  sum_y A[x,y] = 1
```

For unitary mechanisms, complete positivity and trace preservation follow from:

```text
E(rho) = U rho U^dagger
```

For Kraus mechanisms, complete positivity follows from Kraus form and trace
preservation is the checked identity:

```text
E(rho) = sum_i K_i rho K_i^dagger
sum_i K_i^dagger K_i = I
```

For readout, the assignment matrix convention is:

```text
A[x,y] = P(reported y | ideal outcome x)
```

This embeds into a POVM:

```text
M_y = sum_x A[x,y] |x><x|
```

Because entries are nonnegative and rows sum to one:

```text
M_y >= 0
sum_y M_y = I
```

## Circuit Insertion

Mechanisms are inserted at declared operation sites in the full-circuit CUDA-Q
schedule:

```text
ideal operation on location ell
-> local mechanism channel for that operation/location, if declared
```

For example, an `rx` operation site applies the ideal `rx` gate and then the
matching local noise channel attached to `(operation="rx", qubits=(q,))`.
Two-qubit mechanisms attach similarly to `rzz` sites. Readout mechanisms are
applied as classical stochastic readout postprocessing after measurement, which
is equivalent to the POVM embedding above when the post-measurement state is not
used downstream.

M13 and M14 are explicitly defined:

- M13: context-dependent coherent overrotation attached to its declared
  operation axis. Exact single-context recovery is not required.
- M14: operation-dependent coherent error with a visible operation axis and a
  distinct error-generator axis. If the axes collapse to the same value, the
  Data-preparation pre-sampling contract fails.

## Circuit-Level Correctness

Once local modules pass, the circuit-level proof is closure:

- ideal gates are unitary CPTP;
- local unitary/Kraus noise modules are CPTP;
- tensor products of CPTP maps are CPTP;
- compositions of CPTP maps are CPTP;
- stochastic readout maps embedded as POVMs produce nonnegative normalized
  probabilities.

Therefore `p_Theta(y | c)` is a valid probability distribution. CUDA-Q samples
classical bitstrings from that distribution, and Data preparation writes those samples
to `observations.npz`.

## Post-Sampling Physicality Audit

After sampling, data preparation runs `Layer1.P_teacher_physicality_audit`. This audit
checks:

- unitary residuals;
- Kraus trace-preservation residuals;
- Choi positivity and trace-preservation diagnostics;
- readout stochasticity and POVM validity;
- reset/prep validity;
- leakage-surrogate bookkeeping;
- sampled circuit output nonnegativity and normalization;
- silent projection or renormalization usage.

The accepted claim is:

```text
Data preparation samples observation data from CPTP/POVM-defined or explicitly declared
surrogate quantum noise processes.
```

The rejected claim is:

```text
The data are CPTP.
```
