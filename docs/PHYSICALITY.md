# Physicality Boundary

This note states what is physically constrained today and what is not yet
claimed.

## Current Implementation

Layer 1 generates teacher-declared noisy QEC observations from the implemented
physical mechanism catalog. Each enabled mechanism maps to one of three
representations:

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

## Current Claim

Valid:

- Layer 1 can generate teacher-declared noisy QEC observations from implemented
  unitary/Kraus/readout mechanism definitions.
- When Layer 3 predicts a catalog mechanism and reuses its catalog channel, the
  generated channel-level replay inherits the catalog mechanism definition.
- Layer 3 can also replay and score visible empirical noise distributions from
  learner-visible observations.

Not claimed yet:

- arbitrary learned CPTP channel generation by construction;
- arbitrary learned GKSL generator recovery;
- hardware CPTP/GST/GKSL learning;
- proof that every future user-supplied custom channel is physical without a
  per-run audit.

## Layer 1 Guardrail

Layer 1 emits:

```text
cptp_guardrail_audit.json
```

The audit checks every enabled mechanism record:

- complete positivity by representation class: unitary, Kraus, or classical
  stochastic readout matrix;
- channel dimension matches the declared qubit count;
- unitary: `U^dagger U = I`;
- Kraus: `sum_i K_i^dagger K_i = I`;
- readout: rows sum to `1` and entries lie in `[0, 1]`;
- parameters: probabilities and rates are within valid ranges.

The audit reports maximum residuals, per-mechanism pass/fail, and a
global pass/fail flag.
