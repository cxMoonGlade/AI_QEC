# Restricted MPS Phase 7 — sparse sampled Record algorithm and bounded distribution diagnostic — GREEN — 2026-07-17

> Historical phase snapshot. Schema identities and registry counts below describe this phase at
> review time; current identities live in `docs/SIMULATOR.md` and the frontend owning README.

## Disposition

Disposition: **GREEN for the Phase 7 sparse-support algorithm, strategy-specific fail-closed
preflight, support-alignment regressions, and the frozen bounded distributional diagnostic**.

This change removes the sampled QT path's exponential final outcome-table construction. It does not
upgrade restricted MPS to a scientific Carrier, certify a full QEC Record law, or establish
production scalability.

## Exact and sampled behavior

| Route | Measurement algorithm | Emitted Record support | Preflight upper bound |
|---|---|---|---:|
| QT exact | exact joint binary branch enumeration | full binary support | `2**m` |
| QT sampled | sequential conditional single-site binary sampling | lexicographically sorted observed outcomes only; no zero-frequency rows | `min(2**m, Ntraj)` |

Here `m` is the immutable schedule-derived total measurement width and `Ntraj` is the declared
trajectory count. Each sampled target is projected as binary zero/one against the current
conditional state; the selected projected state conditions the next target. After all trajectories,
the Adapter builds counts only for observed bit tuples, sorts those tuples lexicographically, and
emits empirical probabilities `count / Ntraj`.

The exact path still materializes the full binary support. Sparse sampled support is not silently
reused as exact evidence.

## Resource firewall

`error_coupling_simulator.frontend.qt_mps_record_materialization_preflight.v2` records:

- `record_support_policy`;
- `trajectory_count`;
- measurement-boundary count and total width;
- `materialized_outcome_count_upper_bound`;
- the declared budget; and
- `checked_before_cuda=true` plus `checked_before_record_allocation=true`.

Both strategies fail closed when their upper bound exceeds the declared
`max_record_materialization_outcomes`; equality passes. The guard runs before CUDA acquisition,
Record allocation, direct execution, nested sweep/bundle delegation, or resource-probe CUDA
accounting. Final sampled-support materialization is therefore bounded by `Ntraj` instead of
`2**m`, without retiring the resource contract. This statement is an allocation bound, not an
unmeasured wall-time or peak-memory improvement claim.

## Sparse-support comparisons

Seed-sweep and dense-reference comparisons map each emitted Record value to its probability, form the
union of supports, and assign probability zero when one run omits an outcome. Record list position,
identical sparse support, and zero-frequency placeholder rows are not comparison prerequisites.

Sequential conditional measurement changes the number and order of RNG draws relative to the retired
joint-outcome sampler. Old same-seed per-trajectory bit identity is therefore deliberately not an
Interface requirement. The required comparison is distributional.

## Schema hard cut

The behavior-changing schema identities are:

- direct QT execution: `error_coupling_simulator.frontend.qt_mps_restricted_execution.v6`;
- QT bond sweep: `error_coupling_simulator.frontend.qt_mps_bond_sweep.v3`;
- QT trajectory seed sweep: `error_coupling_simulator.frontend.qt_mps_trajectory_seed_sweep.v3`;
- QT evidence bundle: `error_coupling_simulator.frontend.qt_mps_restricted_evidence_bundle.v3`;
- QT resource probe: `error_coupling_simulator.frontend.qt_mps_resource_probe.v3`;
- Record preflight: `error_coupling_simulator.frontend.qt_mps_record_materialization_preflight.v2`.

No retired direct, aggregate, or preflight schema is accepted through a compatibility reader.

## Durable regressions

`tests/test_mps_phase7_sparse_sampled_records.py` pins:

- all six schema identities;
- sampled `min(2**m, Ntraj)` and exact `2**m` preflight bounds;
- rejection before CUDA and full-support allocation;
- observed-only, sorted sampled rows with exact count/frequency binding;
- absence of full-support materialization on the sampled path;
- one-site-at-a-time conditional projection; and
- union-support comparison for reordered or missing sparse outcomes, including the canonical
  no-measurement sentinel.

The Phase 7 tests are included in the strict restricted-MPS gate that currently reports
`907 passed, 1 skipped` and 38 of 38 registered public units at their 100% statement/branch targets.

## Bounded distributional evidence

`scripts/mps_phase7_conditional_distribution_diagnostic.py` freezes a hand-checkable two-qubit Bell
fixture with two measurement boundaries and no reset between them. The exact restricted QT/MPS
branch table must assign probability one half to each of `0000` and `1111` and zero to the other
four-bit Records. Three sampled runs use 2,048 trajectories and explicit seeds `7`, `19`, and `73`.
Each comparison uses standard total variation,
`TV = 1/2 * sum_r |p_exact(r) - p_sampled(r)|`, after union-support alignment.

The frozen diagnostic confidence level is `0.999`. Its declared per-bin Hoeffding padding is
`sqrt(log(2/alpha)/(2*N))`, propagated conservatively to TV as `K/2` times that value. Acceptance
requires every seed to satisfy `min(0.2 + TV_padding, 0.45)`. A deliberate corruption flips the
final bit of every positive exact Record and must have TV at least `0.5` and be rejected by the
`0.45` ceiling.

The completed GPU artifact is
`outputs/simulator_validation/diagnostics/mps_phase7_conditional_distribution/report.json`:

- exact-versus-hand TV: `0.0`;
- sampled TV for seeds `7/19/73`: `0.0205078125`, `0.01416015625`, and `0.0078125`;
- every seed passes both the informational strict `0.2` gate and the confidence-adjusted `0.45`
  gate;
- deliberate-corruption TV: `1.0`, correctly rejected;
- schema: `error_coupling_simulator.diagnostics.mps_phase7_conditional_distribution_report.v1`;
- content hash: `3851e6dd351744b1fcd88076d9d4eadc8028cf6aa2eec19dbe287ae65251c31f`, independently recomputed;
- runtime: `32.7729 s`.

`tests/test_mps_phase7_conditional_distribution_diagnostic.py` rejects malformed distributions,
implicit probability coercion, misbound counts, duplicate seeds, wrong support policies, corrupted
provenance, and a nondiscriminating corruption control. It reports `15 passed, 1 skipped` by default
and `16 passed` with the explicit GPU diagnostic enabled; the combined Phase 7 regression reports
`28 passed, 1 skipped`.

This closes the Phase 7 implementation-consistency exit only. Exact and sampled modes share the
same restricted QT/MPS implementation, so the diagnostic is not an independent scientific oracle,
Record-faithfulness evidence, a production error bound, or a claim of production scalability.
Benchmark-driven performance work remains separately gated by invariant-preserving before/after
measurements and the full acceptance topology.
