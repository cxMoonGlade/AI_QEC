# Finite-RTN free-induction diagnostic — post-result execution contract (2026-07-15)

> **Status:** current rerun contract. This is deliberately not called a preregistration. A historical
> result was inspected before its prediction document and script were committed, so repository
> history cannot establish audit-pristine preregistration. The narrow literature boundary is closed
> in `finite_rtn_free_induction_literature_closure_2026-07-15.md`.

## Object and claim boundary

The current `OneOverFDriftSource` emits endpoints of independent symmetric two-state chains. This
contract tests two separately declared single-qubit longitudinal free-induction diagnostics:

1. continuous symmetric-CTMC interpolation between endpoints;
2. a cycle-held phase using each emitted endpoint state.

Neither lift is the production source-parameter fan-out, scheduled QEC channel, measurement/reset
instrument, syndrome record, or downstream estimator. The production bridge is `OPEN` under every
diagnostic verdict.

## Bound current design inputs

Read directly from `OneOverFDriftSource()`:

```text
amplitude_radns = 1e-4
n_fluctuators = 8
gamma_per_cycle = geomspace(0.005, 0.5, 8)
cycle_time_ns = 1000
a_k = amplitude_radns * cycle_time_ns / sqrt(n_fluctuators)
p_flip,k = (1-exp(-2 gamma_k))/2
```

These are project-design defaults, not hardware-calibrated values.

## Continuous-CTMC diagnostic

For one mode,

```text
delta_k = sqrt(gamma_k^2-a_k^2)
L_k(t) = exp(-gamma_k t)
         [cosh(delta_k t) + (gamma_k/delta_k) sinh(delta_k t)].
```

Use analytic continuation for `a_k>gamma_k` and the continuous equality limit. Independence gives
`L(t)=product_k L_k(t)`. Ground truth uses a different `2^8` joint-state Feynman–Kac matrix
exponential.

## Cycle-held diagnostic

For one mode,

```text
T_k = [[1-p_k,p_k],[p_k,1-p_k]]
D_k = diag(exp(-i a_k), exp(+i a_k))
pi_k = [1/2,1/2]
L_k[n] = pi_k D_k (T_k D_k)^(n-1) 1, n>=1.
```

Ground truth constructs the full `2^8` transition matrix and evolves the joint weighted state
without multiplying single-mode characteristic functions.

## Observable and registered gates

For the declared pure-dephasing maps, the trace distance of antipodal equatorial states is `|L|`.
Report total and maximum positive adjacent excursion. A positive excursion is a BLP witness for the
named diagnostic only; a null is `NULL_WITHIN_HORIZON`, not a divisibility proof.

- horizon: 200 cycles;
- continuous display grid: 0.01 cycle;
- continuous oracle times: `0, 1, 10, 25, 50, 75, 100, 150, 200`;
- held oracle cycles: `0, 1, 2, 5, 25, 50, 75, 100, 150, 200`;
- product/oracle absolute tolerance: `1e-10`;
- monotonic-control maximum positive step: `1e-12`;
- high-precision analytic-zero gate: `|L(t0)|<=1e-60` and `|L(t0+1)|>1e-12`.

## Negative controls and corruption falsifiers

| check | deliberate alternative/corruption | required outcome |
|---|---|---|
| Gaussian control | second cumulant from the same positive exponential covariance | no positive step above `1e-12` |
| all-weak control | replace each rate by twice its amplitude | no positive step above `1e-12` |
| rate convention | use twice the directional rate in the factorized formula only | disagree with the unchanged joint oracle by more than `1e-8` |
| product completeness | omit one factor | disagree with the unchanged joint oracle by more than `1e-8` |
| formulation invariance | factorized and full joint implementations | agree within `1e-10` |

## Verdicts and artifact contract

- `IMPLEMENTATION_GATE_FAILED`: any oracle, high-precision, negative-control, or corruption gate
  fails.
- `CONFIRMED_DIAGNOSTIC_ONLY`: implementation gates pass and the named lift has a registered
  positive excursion.
- `NULL_WITHIN_HORIZON`: implementation gates pass but the named lift has no registered positive
  excursion.

The JSON schema is
`error_coupling_simulator.source.finite_rtn_free_induction_diagnostic.v1`. The default output is
`outputs/simulator_validation/diagnostics/finite_rtn_free_induction/report.json`. The report must
bind the clean tracked script, this contract, the current source implementation, and the Git commit.
Old schemas and old artifacts are not accepted as current evidence.

## Required execution state

Run in the canonical `ecs` environment, one fresh CPU-exclusive process. A signed current artifact
can only be generated after the migrated script, test, contract, and service registry are tracked in
a clean checkpoint. Until then, unit/oracle reruns are implementation evidence but not a signed
current artifact.

