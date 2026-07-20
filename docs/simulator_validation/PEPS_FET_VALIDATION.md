# PEPS and FET validation status

Status: **research carrier; focused owner non-degeneracy passes; clean-head release evidence pending**.

## Current owner

`src/error_coupling_simulator/carrier/peps/` owns the single-wire two-dimensional qutrit PEPS
trajectory carrier. It is registered as `peps_single_wire` with status `RESEARCH` and emits a
`PackedShotBatch` that can be converted through the current record contract.

The current acceptance surface is:

- `tests/test_peps_host_seam.py`
- `tests/test_peps_trajectory_carrier.py`
- `tests/test_peps_fet.py`

The host seam, sampling maps, state construction, local contractions, environment construction,
independent dense comparisons, and full-rank fallback have current executable checks. The selector
admits only finite, target-meeting, rank-reducing maps; rejection is an identity no-op, two-endpoint
absorption is transactional, and solver randomness is private. The local-QR/SVD feasible candidate
is frozen before gauge/ALS work and scored under the same strict environment-fidelity target. Those
are local or bounded engineering invariants; they do not certify the complete multi-round record.

## Current focused disposition

The former all-noop result had two concrete causes:

- `_fix_gauge` passed a reshape/view backed by the verdict-driving `Gamma` tensor into eig calls. On
  the real d3 case, the later scorer observed a relative `Gamma` change of order one.
- the carrier-local SVD existed only as an incomplete ALS seed. The complete pair of bond factors
  that analytically reconstructs the local two-site contraction was not retained as a scored
  feasible candidate.

The focused repair clones/contiguates both eig inputs, freezes the full local-QR/SVD candidate before
gauge/ALS work, binds its pseudo-inverse cutoff to the shared `NUMERICAL_ZERO`, and still applies the
normal finite/target/rank/map mutation firewall. The independent real-d3 known-answer test stops the
drive at the first FET call and reconstructs the candidate without importing `fet.py` or the
carrier's QR/SVD helper. Its frozen case is `B1_3`, stored dimension 12, structural local rank 4; the
independent local reconstruction, dense overlap, and `Fid_Gamma` all meet their original bars, and
the production selector accepts a rank no larger than 4 without changing `eps_fid=1e-8`.

Current dirty-worktree focused evidence on 2026-07-20 is:

```text
Gamma immutability + real-d3 known-answer  = 3 passed
non-degeneracy + independent GF(2) entropy = 2 passed
complete tests/test_peps_fet.py owner suite = 38 passed
```

The non-degeneracy test now observes at least one authenticated rank-reducing write-back, while the
separate entropy test still matches the inline GF(2) reference at its unchanged tolerance. This
clears the focused owner blocker only. No clean-head fresh-process replay artifact, aggregate service
result, or full-record comparison has yet been generated for the repaired source.

The previous committed evidence record remains useful only as historical pre-repair evidence:
`docs/simulator_validation/TENSOR_NETWORK_TRUNCATION_REPAIR_VALIDATION_2026-07-16.md`; its local
artifact is
`outputs/simulator_validation/diagnostics/peps_fet_replay_audit_postfix/report.json` with content
hash `8c6d13b2a41ac6843f444d788ec12bd0d2744132399d2ca015d1f0bf17330228`.
It authenticates the old `c8c553e` all-noop state and cannot grade the current worktree.

## Claim boundary

- A passing local environment matrix, feasible-candidate reconstruction, non-degeneracy check,
  entropy equality, or dense overlap does not establish the detector/observable Record law or
  full-record faithfulness.
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

Historical local outputs and pre-cleanup contracts are discovery material only. Release evidence
must be regenerated from current committed source and current tests with complete provenance.
