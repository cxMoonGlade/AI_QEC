# PEPS and FET validation status

Status: **research carrier; local invariants partially pass; end-to-end FET scientific gate fails**.

## Current owner

`src/error_coupling_simulator/carrier/peps/` owns the single-wire two-dimensional qutrit PEPS
trajectory carrier. It is registered as `peps_single_wire` with status `RESEARCH` and emits a
`PackedShotBatch` that can be converted through the current record contract.

The current acceptance surface is:

- `tests/test_peps_host_seam.py`
- `tests/test_peps_trajectory_carrier.py`
- `tests/test_peps_fet.py`

The host seam, sampling maps, state construction, local contractions, environment construction,
independent dense comparisons, and full-rank fallback have current executable checks. Those checks
are local or bounded invariants; they do not certify the complete multi-round record.

## Current blocker

`tests/test_peps_fet.py::test_fet_env_round_preserves_stabilizer_entropy` currently fails on the
registered d3 leak-off case:

```text
carrier entropy       = 0.10860941571062639
independent GF(2) ref = 2.0
tolerance             = 1e-4
```

The independent reference is computed in the test from GF(2) stabilizer algebra and shares no PEPS
truncation implementation. This is a scientific invariant failure, not an exit-139 execution
failure. It remains visible and blocks any claim that the environment-aware truncation is
state-faithful or record-faithful for this case.

## Claim boundary

- A passing local environment matrix, dense-overlap, or full-rank identity check does not override
  the failed entropy invariant.
- Bond dimension, local entropy, discarded weight, and local environment fidelity are resource or
  state diagnostics. None alone proves equality of the detector/observable record law.
- No d5/d7 distributional result may be used as a scientific premise.
- No tolerance, reference value, or truncation objective may be weakened to admit the current
  implementation.
- Any proposed FET change requires a fresh primary-literature closure, a written constraint ledger,
  an independent corruption falsifier, and explicit source-change confirmation.

Historical local outputs and pre-cleanup contracts are discovery material only. The next valid
evidence must be generated from the current source and current tests with complete provenance.
