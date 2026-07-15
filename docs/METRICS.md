# METRICS — current simulator ledger

This file defines only metrics that have a current implementation or registered test owner in
`error_coupling_simulator`. The simulated object is the multi-time detector/observable record;
metrics are measurements of that object, not substitutes for it. The binding product boundary is
`docs/SIMULATOR.md`, and the machine-readable owner map is `docs/service_status.json`.

## Registration rule

A quantitative result is claim-bearing only when it declares:

1. the object and coordinate being measured;
2. the metric name and formula;
3. the implementation owner and acceptance test;
4. whether the value is exact, sampled, or a project gate;
5. the comparison band and its provenance.

An unregistered score is exploratory output, not simulator evidence. A new metric requires a
source-backed definition, a current owner, an independent value test, and an update to this ledger.

The current certification ledger uses the classes carried by
`error_coupling_simulator.certify.types`:

- **(a) exact** — an enumerated value, theorem, or algebraic identity;
- **(b) prediction band** — a falsifiable value with an explicitly declared comparison band;
- **(c) heuristic gate** — a numerical or resource decision rule that is not a scientific premise.

An undeclared value is class (c). `UNANCHORED` is an evidence gap, never a pass. Independent
PEPO/PEPS reference evidence is currently bounded to d3; record-level finite-truncation fidelity
and d5/d7 scientific certification are open.

## Shared conventions

- Records use `RecordBatch.det` and `RecordBatch.obs`. Detector bits are temporal events, with
  `d[0,j]=s[0,j]` and `d[r,j]=s[r,j] XOR s[r-1,j]` for `r>=1`. A raw syndrome array must be named as
  raw syndrome data. `tests/test_carrier_record_fold.py` owns the fold identities and corruption
  checks.
- `NUMERICAL_ZERO == 1e-12` is a floating comparison threshold. It must not replace structural
  zeros, binary values, counts, or probability mass.
- Population metrics and sampled estimates must be labelled separately. A project acceptance band
  is not a confidence interval unless a derivation explicitly establishes that interpretation.
- A metric must be evaluated against an independent reference route. Shared-code agreement is a
  regression check, not scientific certification.

## Record certification

These are the quantities implemented by `certify/core.py` and enumerated by
`certify/types.Statistic`.

| Quantity | Current formula and convention | Owner and executable gate |
|---|---|---|
| Full joint record distance | `TV(p,q)=0.5*sum_x abs(p(x)-q(x))` over the joint detector/observable support | `certify.core.total_variation`; `tests/test_certify_core_units.py` independently pins the half factor and mismatch verdict |
| Detector-record marginal distance | The same TV formula after marginalizing away the logical-observable bit | `Statistic.SYNDROME_DIST`; `tests/test_certify_core_units.py` pins the marginalization and TV comparison |
| Detector and observable marginals | Per-column detector firing means plus the observable-flip mean; comparison value is `max(abs(a-b))` | `Statistic.DETECTOR_MARG`; `tests/test_certify_core_units.py` |
| Round-to-round detector correlation | For each adjacent round and stabilizer, Pearson correlation of binary detector columns; reduce to `mean_j abs(corr[r,j])`; compare with maximum absolute component error | `Statistic.RR_CORR`, `reduce_rr_corr`; `tests/test_certify_core_units.py` |
| Same-round spatial correlation | Per round, `mean_{j!=k} abs(corr[r,j,k])`; diagonal self-correlations are excluded; compare with maximum absolute component error | `Statistic.SPATIAL_CORR`, `reduce_spatial_corr`; `tests/test_certify_core_units.py` |
| Registered scalar identity | `abs(value-reference)` for a named closed-form quantity | `Statistic.SCALAR_FUNC`; current anchor and certification tests under `tests/test_certify*.py` |

The implemented distribution band is a project gate:

```text
max(6/sqrt(N), 3*sqrt(K/N)) + statistical_anchor_band
```

where `K` is the realized union support size. Array statistics use
`8/sqrt(N) + statistical_anchor_band`; an exact scalar reference uses the current `1e-9` absolute
comparison band. These formulas are implementation policy in `certify/core.py`, not universal
confidence bounds. Their branch and boundary behavior is pinned in
`tests/test_certify_core_units.py`.

## Channel diagnostics

| Quantity | Current formula and claim boundary | Owner and executable gate |
|---|---|---|
| Trace-preservation residual | Frobenius norm `norm(sum_k K_k^dagger K_k-I)` | `carrier.cptp_channel.tp_residual`; `tests/test_noise_mechanism_primitives.py` and channel-owner tests |
| Joint-vs-composed process infidelity | `1-F` where `F` is Uhlmann fidelity between trace-normalized Choi states | `carrier.joint_lindbladian.composed_vs_joint_infidelity`; independent NumPy/SciPy/QuTiP checks in `tests/test_joint_lindbladian.py` |
| Joint-vs-composed superoperator distance | Frobenius distance between the two superoperators | `composed_vs_joint_superop_distance`; `tests/test_joint_lindbladian.py` and `tests/test_axis1_mcwf_dense_certification.py` |
| Choi-state companion distance | Frobenius distance between trace-normalized Choi states; a diagnostic, not trace distance or diamond distance | `composed_vs_joint_choi_distance`; `tests/test_joint_lindbladian.py` |
| Pauli-transfer matrix | `R_ab=Tr(P_a Phi(P_b))/d` in the declared Pauli basis | `certify.channel_diagnostics`; `tests/test_channel_diagnostics.py` |

PTM off-diagonal entries establish basis-specific non-Pauli structure only. They do not, by
themselves, identify coherent error or its physical cause.

## Current record reductions

| Quantity | Current formula and claim boundary | Owner and executable gate |
|---|---|---|
| Logical error rate | Mean XOR between decoder predictions and actual observable bits, reported per observable and for any-observable failure | `frontend.simulator._decoder_summary`; `tests/test_simulator_frontend.py` |
| Detector-pair estimate | Spitz Eq. 13 `p_ij = 1/2-sqrt(1/4-cov/(1-2*mean(x_i XOR x_j)))` plus its delta-method standard error | `frontend.pij`; independent recomputation and corruption checks in `tests/test_interop_units.py` |

The pair estimate is a two-point reduction and is blind to hyperedges. Logical error rate requires
one named, fixed decoder and the actual observable bits; it is not evidence that the underlying
analog channel is exactly represented by a detector error model.

## Tensor-network implementation diagnostics

The retained PEPO and PEPS carriers expose bond dimensions, squared singular-value tails,
truncation objectives, trace checks, contraction deltas, and negativity diagnostics. Their current
owners are `carrier/pepo/` and `carrier/peps/`; their registered tests are listed under
`pepo_density_matrix_carrier` and `peps_single_wire` in `docs/service_status.json`.

These values measure representation cost or implementation consistency. None is a substitute for
the full record comparison. In particular:

- a discarded squared-singular-value tail is local to the stated cut;
- a bond cap is a resource limit;
- a local truncation objective is not a bound on record TV or logical error;
- trace and negativity checks are necessary validity diagnostics, not sufficient record
  certification.

The current PEPS/FET entropy falsifier is unresolved, so no PEPS/FET metric in this section carries
a passed record-faithfulness verdict.

## Bounded research diagnostics

Two research surfaces have current owners but do not certify the production record:

- `quantum_bath/observables.py` implements exact three-round distribution TV, Kolmogorov-consistency
  statistics, an L1 distance to the Markov-1 factorization, and conditional mutual information in
  bits. These apply only to the registered quantum-bath research distributions and are tested by
  `tests/test_quantum_bath_observables_units.py`.
- `scripts/finite_rtn_free_induction_diagnostic.py` reports positive trace-distance excursions for
  two explicitly declared single-qubit free-induction lifts. Its independent full-state oracles and
  corruption tests live in `tests/test_finite_rtn_free_induction_diagnostic.py`. The signed current
  artifact is pending, and no result transfers to the source-conditioned QEC channel or syndrome
  record.
