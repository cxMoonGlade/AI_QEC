# PEPS and FET validation status

Status: **research carrier; mutation firewall passes; non-degenerate FET scientific gate fails**.

## Current owner

`src/error_coupling_simulator/carrier/peps/` owns the single-wire two-dimensional qutrit PEPS
trajectory carrier. It is registered as `peps_single_wire` with status `RESEARCH` and emits a
`PackedShotBatch` that can be converted through the current record contract.

The current acceptance surface is:

- `tests/test_peps_host_seam.py`
- `tests/test_peps_trajectory_carrier.py`
- `tests/test_peps_fet.py`

The host seam, sampling maps, state construction, local contractions, environment construction,
independent dense comparisons, and full-rank fallback have current executable checks. The repaired
selector admits only finite, target-meeting, rank-reducing maps; rejection is an identity no-op,
two-endpoint absorption is transactional, and solver randomness is private. Those are local or
bounded engineering invariants; they do not certify useful truncation or the complete multi-round
record.

## Current blocker

A 2026-07-16 local pre-commit falsifier on the registered strict-``eps_fid=1e-8`` d3 leak-off run
matched the independent GF(2) entropy reference, but the same run emitted 16 FET cut rows and applied
zero rank-reducing write-backs. Every candidate was rejected and the state followed the full-rank
identity fallback. This observation is not yet the committed fresh-process artifact; it fixes the
expected gate disposition for that replay. The explicit non-degeneracy test therefore fails:

`tests/test_peps_fet.py::TestFetEnvWiring::test_fet_env_exercises_an_accepted_rank_reducing_writeback`

```text
entropy gate                         = PASS (S_A=2.0, GF(2)=2.0, tolerance=1e-4)
FET cut rows                         = 16
authenticated rank-reducing writes  = 0
non-degeneracy gate                  = RED_ALL_NOOP
```

The independent entropy reference is computed in the test from GF(2) stabilizer algebra and shares
no PEPS truncation implementation. Its equality authenticates the untruncated fallback state, not
the usefulness or fidelity of FET pruning. The fail-closed mutation repair is working as intended,
but the solver/pruning path remains scientifically RED. A fresh-process replay must reproduce and
authenticate this split verdict before the evidence is promoted.

## Claim boundary

- A passing local environment matrix, entropy equality, dense-overlap, or full-rank identity check
  does not override the failed non-degeneracy gate.
- Bond dimension, local entropy, discarded weight, and local environment fidelity are resource or
  state diagnostics. None alone proves equality of the detector/observable record law.
- No d5/d7 distributional result may be used as a scientific premise.
- No tolerance, reference value, or truncation objective may be weakened to admit the current
  implementation.
- The registered target may not be loosened merely to force a write-back. Any alternate epsilon or
  solver must be evaluated by a preregistered convergence ladder with an independent state/record
  reference and corruption falsifier.
- A local-FET-to-QEC-observable literature bridge remains open; local fidelity is not assumed to be
  a complete-record error bound.

Historical local outputs and pre-cleanup contracts are discovery material only. The next valid
evidence must be generated from the current source and current tests with complete provenance.
