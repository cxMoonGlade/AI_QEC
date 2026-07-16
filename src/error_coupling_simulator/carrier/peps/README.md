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

A full-record faithfulness claim requires comparison with an independent reference and an explicit
convergence study over the relevant approximation controls. The current FET entropy gate remains
red. Results beyond the bounded d3 implementation surface, including d5/d7 distributions, remain
provisional until those requirements pass.

The FET surface is not scientifically passed. Its current end-to-end entropy test reports
`0.10860941571062639` against an independent GF(2) reference of `2.0` at tolerance `1e-4`. Passing
local environment or dense-reference checks do not override that failure. No d5/d7 distributional
result, local bond statistic, or truncation objective is a full-record certificate.

Binding status: `docs/simulator_validation/PEPS_FET_VALIDATION.md` and
`docs/simulator_validation/COHERENT_LEAKAGE_TRUNCATION_EVIDENCE.md`.
