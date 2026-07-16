# carrier/peps

Status: **single-wire two-dimensional qutrit PEPS research carrier; full-record faithfulness open**.

The carrier evolves pure-state trajectories on the full data-register geometry. It is GPU-only and
complex128. It shares geometry and bounded contraction helpers with the retained PEPO carrier while
keeping a single physical wire per site.

Modules:

- `state.py` — `PepsState`, codestate construction, local qutrit gates, and the bounded d3 dense
  bridge.
- `stab_tt.py` — selective stabilizer branch tensor trains.
- `contraction.py` — double-layer expectation contractions, Born reads, terminal effects, and
  independent read diagnostics.
- `sampling_maps.py` — the three uniform-to-outcome maps used by trajectory execution.
- `trajectory.py` — per-shot execution, truncation policies, record packing, and the
  `PepsSampler` entry point.
- `diagnostics.py` — bond, loop-correlation, and loop-rank diagnostics.
- `fet.py` — environment-aware single-bond rank selection.

Current record handling uses `carrier.records.PackedShotBatch` and the carrier-neutral temporal
detector fold. Raw syndrome access is explicit; public record conversion applies the declared fold.

The current owner tests are `tests/test_peps_host_seam.py`,
`tests/test_peps_trajectory_carrier.py`, and `tests/test_peps_fet.py`. They cover package ownership,
state and contraction invariants, sampling
maps, bounded exact comparisons, and local FET properties.

## Truncation contract

This is a single-wire two-dimensional qutrit PEPS research carrier. Bond dimensions, retained
ranks, FET objectives, local environments, local fidelities, entropies, and other truncation
diagnostics are numerical evidence about a declared approximation; none is a certificate for the
complete multi-round record law.

The FET mutation boundary is fail-closed. The selector distinguishes `accepted`, `noop`, and
`solver_failed`; only a finite `[0,1]` candidate meeting the declared fidelity target, with a finite
complex128 map of the expected shape, may reach in-place absorption. Rejected/nonfinite candidates
leave the tensors untouched, and the ledger separates candidate rank/fidelity from applied
rank/fidelity and records `writeback_applied`. ALS perturbations use a declared private solver seed,
never the ambient CPU or CUDA RNG; full-curve diagnostics are an explicit observer and cannot alter
the selected result. These controls prevent silent corruption but do not promote the carrier to a
record-faithful one. Absorption is transactional across both bond endpoints: shape,
dtype, device, and finiteness are authenticated before mutation, and a failure after either endpoint
has begun changing restores both original tensors.

A full-record faithfulness claim requires comparison with an independent reference and an explicit
convergence study over the relevant approximation controls. At the registered strict ``eps_fid``,
the post-fix d3 entropy equality is currently an all-noop result: no authenticated rank-reducing FET
write-back occurs, so the non-degeneracy gate is RED and the pruning path remains unvalidated. The
fresh-process replay bound to repair commit `c8c553e` authenticates this split result: scoped replay,
fallback contract, RNG neutrality, and entropy pass, while solver health and non-degeneracy remain
RED. The primary-literature bridge from the local FET objective to the QEC entropy and complete
record-law observables remains open.
Passing an entropy, local-environment, or dense-reference check does not by itself establish
full-record faithfulness. Results beyond the bounded d3 implementation surface, including d5/d7
distributions, therefore remain provisional. No d5/d7 distributional result, local bond statistic,
entropy value, or truncation objective is a full-record certificate.

Binding status: `docs/simulator_validation/PEPS_FET_VALIDATION.md` and
`docs/simulator_validation/COHERENT_LEAKAGE_TRUNCATION_EVIDENCE.md`.
