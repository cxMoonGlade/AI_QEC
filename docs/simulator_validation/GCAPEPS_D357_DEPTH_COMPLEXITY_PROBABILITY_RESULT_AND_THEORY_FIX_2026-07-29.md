# GCAPEPS distance/depth/complexity/probability result and theory-fix

Date: 2026-07-29

## Decision

**Theory-fix action: `REPAIR`.**

The sealed run is valid as a bounded, complex128, fresh-process,
compilation-inclusive engineering telemetry result. It does **not** support
the broad statement that GCAPEPS is generically more efficient than ordinary
PEPS, that its residual update is faster, or that error probability changes
exact representation cost.

The repair is interpretive:

1. call the registered `update_ns` result **cold first-call update time**;
2. report full child wall time as a separate post-run sensitivity lens;
3. separate Clifford-shell time from non-Clifford residual-update time;
4. quarantine the cgroup `MemoryPeak` comparison;
5. treat the probability slice as a coefficient calibration, not a sampled
   occurrence-rate experiment;
6. retain all three stress-corner censors as negative results.

No original preregistration or raw result was rewritten.

## Frozen claim under review

| field | frozen object |
|---|---|
| decision/consequence | Whether the run can support a reportable current-implementation efficiency comparison |
| mechanism | GCAPEPS stores the Clifford H/CX shell in a Stim tableau and applies each pulled-back rank-2 Pauli rotation only to the Quimb PEPS residual; ordinary Quimb applies the same physical shell and rotations directly |
| measured object | Fresh-process `update_ns`, launch wall time, `ru_maxrss`, bond dimensions, tensor elements, logical tensor bytes, completion, and censor location |
| bridge | The fixture fixes the same physical operation ledger; Stim and SDIM independently agree on all signed pullbacks; the two lanes remain equal-status candidates rather than truth/reference lanes |
| observed scale | 21 paired cells, 3 GCAPEPS resource-guard censors; registered update ratios 30.62–551.37 |
| invariants | \(p_{\mathrm{twirl}}=\sin^2(\theta/2)\); changing a nonzero coefficient does not change the exact rank-2 operator support; no finite bond cap; complex128 |
| possible no-go | Exact PEPS contraction is not requested and no contraction-efficiency claim is allowed |
| implementation target | Parent commit `ed267372663b0ff6f1157479af9d1d5777153699`; Quimb fork commit `6fbbf74cd36686ed30a4d8865697ce46e47056c1` |

The result is seductive because the registered update-time ratios are very
large. The component and full-process lenses below show why those ratios
cannot be promoted to a generic efficiency statement.

## Execution and integrity

- Grid: \(d\in\{3,5,7\}\), eight cells per distance, 24 cells total.
- Each lane/cell: one discarded fresh-process warmup and three measured
  fresh processes.
- Launches: 192, in frozen `P,G,G,P,P,G` measured order after `P,G` warmup.
- Worker outcomes: 180 completed and 12 structured censors.
- Paired finite ratios: 21/24 cells.
- Dtype: complex128.
- Plain and GCAPEPS finite bond cap: none.
- SDIM independently reproduced all 60 accumulated-frame signed pullbacks:
  12 for \(d=3\), 20 for \(d=5\), and 28 for \(d=7\).
- Independent reconstruction of every median, MAD, ratio, and operation-time
  sum from the 192 raw workers produced zero mismatches.
- Target manifest covers 411 artifacts with zero observed hash or size
  mismatch.

Artifact identities:

```text
target bundle:
  /tmp/gcapeps-d357-grid-target-20260729
target manifest content hash:
  3adc28deda5d7f1673ac8ba3c9e48adda33d1583c324d07e01a35dc3ae013e4b
result content hash:
  7e243e87245b985b0c8f285a77e6b470d48e82561e1632c01fd6c59c7a1ae819

controls bundle:
  /tmp/gcapeps-d357-grid-controls-20260729
controls manifest content hash:
  0e9c27e31922ac7251e050ef6e477d4f56ae9063e33a9f3c7f29eb8fc4cca305
```

The raw bundle does not contain a durable pytest/mutation transcript. The
pre-run session checks were green, but that fact is not promoted into a
bundle-internal release certificate.

## Registered primary result

Times are measured `update_ns` medians in milliseconds. `P/G` is ordinary
Quimb divided by GCAPEPS. Tensor elements and maximum bond are reported as
`plain / GCAPEPS`.

| \(d\) | role | \(L\) | \(K\) | \(p_{\mathrm{twirl}}\) | plain ms | GC ms | P/G | tensor elements | max bond |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | baseline | 1 | 1 | \(10^{-3}\) | 2379.273 | 4.339 | 548.30 | 206 / 72 | 2 / 2 |
| 3 | depth-2 | 2 | 1 | \(10^{-3}\) | 2387.790 | 5.156 | 463.12 | 288 / 72 | 2 / 2 |
| 3 | depth-\(d\) | 3 | 1 | \(10^{-3}\) | 2394.347 | 9.023 | 265.37 | 228 / 568 | 2 / 4 |
| 3 | complexity-2 | 1 | 2 | \(10^{-3}\) | 2382.241 | 8.296 | 287.14 | 206 / 148 | 2 / 4 |
| 3 | complexity-4 | 1 | 4 | \(10^{-3}\) | 2386.739 | 16.108 | 148.17 | 206 / 554 | 2 / 8 |
| 3 | low probability | 1 | 1 | \(10^{-4}\) | 2381.580 | 4.344 | 548.21 | 206 / 72 | 2 / 2 |
| 3 | high probability | 1 | 1 | \(10^{-2}\) | 2381.345 | 4.319 | 551.37 | 206 / 72 | 2 / 2 |
| 3 | stress | 3 | 4 | \(10^{-2}\) | 2392.100 | censored | — | — | — |
| 5 | baseline | 1 | 1 | \(10^{-3}\) | 2387.601 | 10.364 | 230.37 | 796 / 136 | 2 / 2 |
| 5 | depth-2 | 2 | 1 | \(10^{-3}\) | 2416.524 | 12.103 | 199.67 | 1088 / 136 | 2 / 2 |
| 5 | depth-\(d\) | 5 | 1 | \(10^{-3}\) | 2489.653 | 33.467 | 74.39 | 828 / 8344 | 2 / 8 |
| 5 | complexity-2 | 1 | 2 | \(10^{-3}\) | 2390.554 | 20.126 | 118.78 | 796 / 210 | 2 / 4 |
| 5 | complexity-4 | 1 | 4 | \(10^{-3}\) | 2394.232 | 40.510 | 59.10 | 796 / 742 | 2 / 16 |
| 5 | low probability | 1 | 1 | \(10^{-4}\) | 2392.929 | 10.231 | 233.90 | 796 / 136 | 2 / 2 |
| 5 | high probability | 1 | 1 | \(10^{-2}\) | 2386.632 | 10.213 | 233.68 | 796 / 136 | 2 / 2 |
| 5 | stress | 5 | 4 | \(10^{-2}\) | 2517.870 | censored | — | — | — |
| 7 | baseline | 1 | 1 | \(10^{-3}\) | 2415.597 | 19.917 | 121.28 | 1770 / 232 | 2 / 2 |
| 7 | depth-2 | 2 | 1 | \(10^{-3}\) | 2461.804 | 23.340 | 105.48 | 2400 / 232 | 2 / 2 |
| 7 | depth-\(d\) | 7 | 1 | \(10^{-3}\) | 2702.455 | 88.252 | 30.62 | 2212 / 131384 | 2 / 16 |
| 7 | complexity-2 | 1 | 2 | \(10^{-3}\) | 2421.950 | 38.701 | 62.58 | 1770 / 306 | 2 / 4 |
| 7 | complexity-4 | 1 | 4 | \(10^{-3}\) | 2410.512 | 76.268 | 31.61 | 1770 / 838 | 2 / 16 |
| 7 | low probability | 1 | 1 | \(10^{-4}\) | 2423.176 | 19.929 | 121.59 | 1770 / 232 | 2 / 2 |
| 7 | high probability | 1 | 1 | \(10^{-2}\) | 2414.293 | 19.836 | 121.71 | 1770 / 232 | 2 / 2 |
| 7 | stress | 7 | 4 | \(10^{-2}\) | 6599.118 | censored | — | — | — |

The registered result says that this Clifford-heavy cold first-call path is
faster in the GCAPEPS lane in every paired cell. It simultaneously shows that
the advantage shrinks as the residual problem becomes harder:

- at \(K=1,L=1,p=10^{-3}\), P/G falls from 548.30 at \(d=3\) to
  121.28 at \(d=7\);
- at \(L=1,p=10^{-3}\), increasing \(K\) from 1 to 4 lowers P/G from
  548.30 to 148.17 at \(d=3\), 230.37 to 59.10 at \(d=5\), and 121.28
  to 31.61 at \(d=7\);
- at \(K=1,p=10^{-3}\), increasing depth from 1 to \(d\) lowers P/G
  from 548.30 to 265.37, 230.37 to 74.39, and 121.28 to 30.62.

The representation ledger is not uniformly favorable. At depth \(L=d\), the
GCAPEPS residual has about 2.5, 10.1, and 59.4 times as many tensor elements
as plain Quimb for \(d=3,5,7\), respectively.

## Error-probability slice

The probability coordinate is

\[
p_{\mathrm{twirl}}=\sin^2(\theta/2),\qquad
\theta=2\arcsin\sqrt{p_{\mathrm{twirl}}}.
\]

The registered values are:

| \(p_{\mathrm{twirl}}\) | \(\theta\) radians |
|---:|---:|
| \(10^{-4}\) | 0.020000333348334228 |
| \(10^{-3}\) | 0.06325609887514336 |
| \(10^{-2}\) | 0.2003348423231196 |

For every distance and both lanes, the low, baseline, and high probability
cells have exactly the same final bond vector, tensor-element count, and
logical tensor bytes. Their timings show no registered monotone effect.

This is the expected exact-representation invariant: changing a nonzero
coefficient changes tensor values but not the rank-2 support pattern. The
slice therefore does **not** measure a sampled error occurrence rate and
cannot support a claim that larger \(p\) increases exact carrier cost.

A literal occurrence-probability experiment would require either:

- stochastic trajectories with a frozen seed/trajectory population and
  event-count conditioning; or
- a density-operator/Kraus carrier for the mixed Pauli channel.

Those are different experiments and are not retrofitted into this result.

## Stress-corner negative result

All four GCAPEPS attempts in each stress cell—warmup plus three measured
samples—were censored at the same deterministic preflight:

```text
classification = RESOURCE_GUARD_CENSORED
metric = max_predicted_bond_dimension
predicted = 128
limit = 64
stage = tree_pepo_construction_preflight
failed_routing_event_not_committed = true
```

| \(d\) | requested rotations | completed before censor | failure |
|---:|---:|---:|---|
| 3 | 12 | 8 | layer 3, location rank 1, target 6 |
| 5 | 20 | 7 | layer 2, location rank 4, target 30 |
| 7 | 28 | 7 | layer 2, location rank 4, target 58 |

This is evidence of residual bond-growth pressure under combined depth and
location complexity. It is not an OOM, timeout, or completed performance
sample, and no ratio is defined for these cells.

## Formulation sensitivity

### Cold first call

In every measured fresh plain process, the first physical prefix call
dominates the registered update:

| \(d\) | \(L=1\) | \(L=2\) | \(L=d\) |
|---:|---:|---:|---:|
| 3 | 100.00% | 99.68% | 99.40% |
| 5 | 100.00% | 99.03% | 96.33% |
| 7 | 100.00% | 98.03% | 89.42% |

Because every measured sample is a new process, the discarded warmup process
cannot warm the measured process. The 30.62–551.37 ratios therefore include
the plain lane's first-call/compilation path and are not steady-state
throughput ratios.

### Full child wall time

Recomputing medians from the independent supervisor
`launch_and_process_elapsed_ns` field gives P/G ratios of 1.640–1.714 over
the 21 paired cells. This lens includes imports, initialization, validation,
serialization, and update work. It agrees on direction but not scale with
the registered update metric.

### Component cost

The architecture transfers work rather than making every component faster:

- the plain/GC Clifford-shell time ratio is 974–29,417 over paired cells;
- the GCAPEPS non-Clifford residual-update time is 106–702 times the plain
  lane's local physical \(R_Y\) time.

Thus the observed advantage is specifically a **Clifford-heavy workload**
advantage: cheap tableau updates must outweigh more expensive pulled-back
residual updates.

As an explicitly post-hoc diagnostic, excluding layer 1 from the \(K=1,L=d\)
cells gives later-layer P/G ratios of 3.05, 3.91, and 4.19 for
\(d=3,5,7\). These values are useful only for designing a separately
preregistered warm-throughput experiment.

## Metric quarantine

The worker-read cgroup `MemoryPeak`, the same launch's systemd summary, and
`ru_maxrss` disagree systematically. All 192 launches exhibit an accounting
inconsistency. The cgroup ratio is therefore quarantined and must not enter a
performance conclusion until the accounting path is repaired and controlled.

The following remain usable within their stated classes:

- `ru_maxrss`: process-level numerical resource telemetry;
- maximum bond, tensor elements, logical tensor bytes: representation-resource
  telemetry;
- operation and launch clocks: numerical timing telemetry with the cold/warm
  distinction above.

None is a state-accuracy or contraction certificate.

## Stress-test wires

| wire | result | evidence and consequence |
|---|---|---|
| symmetry/invariant | survives only for restricted claim | Probability changes coefficients but exact support/rank resources are invariant |
| formulation and rate-vs-observable | **fires against broad efficiency** | Cold update ratios, full child wall time, and component times differ by orders of magnitude |
| independent lens | survives telemetry, not faithfulness | Raw-worker reconstruction has zero aggregation mismatches; supervisor wall time agrees only on direction |
| degenerate design | **fires against a probability-effect claim** | \(p=10^{-4},10^{-3},10^{-2}\) produce identical exact structure in both lanes |
| suppressing lens | blocks physical extrapolation | No contraction, vector, norm, fidelity, measurement, reset, or Record is computed |
| un-led adversarial review | restrict | Independent raw-only review reproduced the numbers and rejected a broad efficiency release |
| predict-before-measure | survives | All 24 cells were attempted; stress censors are retained and have no ratio |
| propagation | no prior consumer found | Repository search found no existing result narrative using these values as a premise |

Stress-test verdict:

```text
STOP — formulation and degenerate-design wires fire against the broad
efficiency and probability-effect claims.
```

## Final theory-fix handoff

```text
claim:
  GCAPEPS is more efficient than ordinary PEPS over d, depth, noise
  complexity, and error probability.

consequence/attack:
  The headline would be used in a graduate-course report, but it conflates
  cold first-call cost with throughput and treats a coefficient-only p knob
  as an occurrence-rate intervention.

formulations/invariants:
  cold update; full child wall; Clifford shell; non-Clifford residual;
  exact rank invariance under nonzero coefficient changes.

epistemic class:
  numerical_only / current_implementation / bounded_frozen_envelope.

closure status:
  closed for the mechanism and bounded telemetry; no literature gap is
  load-bearing because no novelty, generic speedup, or field-wide claim is
  retained.

contrary evidence/anomalies:
  three deterministic guard censors; residual-update slowdown; depth-driven
  tensor growth; cold-start dominance; degenerate p structure; quarantined
  cgroup accounting.

propagation sites:
  this result packet only; no prior premise-bearing consumer found.

REPAIR

allowed next action:
  use the bounded cold-start result and negative stress result in the course
  report with the exact restrictions above; preregister a within-process
  warm-throughput run before making a general efficiency claim; use
  trajectories or a density-operator carrier before claiming literal error
  occurrence-probability dependence.
```
