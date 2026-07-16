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

The committed fresh-process audit of repair commit
`c8c553e7f3665f6fae29cca5696905f09d6643d0` reproduced the registered strict-``eps_fid=1e-8`` d3
leak-off result in four fixed cases. Every case matched the independent GF(2) entropy reference but
emitted 16 FET cut rows and applied zero authenticated rank-reducing write-backs. Every selected
candidate was rejected and the state followed the full-rank identity fallback. The explicit
non-degeneracy test therefore fails:

Across the committed matrix there were zero rank-reducing write-backs.

`tests/test_peps_fet.py::TestFetEnvWiring::test_fet_env_exercises_an_accepted_rank_reducing_writeback`

```text
entropy gate                         = PASS (S_A=2.0, GF(2)=2.0, tolerance=1e-4)
FET cut rows                         = 16 per case, 64 total
authenticated rank-reducing writes  = 0
non-degeneracy gate                  = RED_ALL_NOOP
solver-health gate                   = RED (64/64 cuts unhealthy)
```

The independent entropy reference is computed in the test from GF(2) stabilizer algebra and shares
no PEPS truncation implementation. Its equality authenticates the untruncated fallback state, not
the usefulness or fidelity of FET pruning. The fail-closed mutation repair is working as intended,
but the solver/pruning path remains scientifically RED. The replay itself is
`PASS_SCOPED_BITWISE`, the fallback contract is `PASS`, and all four ambient-RNG checks pass. Those
engineering results do not override the solver-health and non-degeneracy failures.

The committed evidence record is
`docs/simulator_validation/TENSOR_NETWORK_TRUNCATION_REPAIR_VALIDATION_2026-07-16.md`; its local
artifact is
`outputs/simulator_validation/diagnostics/peps_fet_replay_audit_postfix/report.json` with content
hash `8c6d13b2a41ac6843f444d788ec12bd0d2744132399d2ca015d1f0bf17330228`.

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

Historical local outputs and pre-cleanup contracts are discovery material only. Further evidence
must be generated from current committed source and current tests with complete provenance.
