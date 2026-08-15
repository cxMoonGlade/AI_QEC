# Tensor-network truncation repair validation — 2026-07-16

Status: **MPS accounting repair accepted on its restricted scope; PEPS mutation repair accepted;
PEPS pruning remains scientific RED**.

This record validates the repair commit `c8c553e7f3665f6fae29cca5696905f09d6643d0`. It does
not replace the pre-fix differential audit and does not upgrade a local tensor-network diagnostic
into a complete QEC record-law certificate.

## Repair disposition

| Surface | Engineering disposition | Scientific disposition |
|---|---|---|
| Restricted QT/MCWF MPS | Actual Quimb splits, occurrence coverage, branch/path aggregation, and fail-closed finite-loss gates are implemented and tested. | Accepted only for the declared restricted carrier. Local discarded fractions remain heuristic, not a global state or record-law bound. |
| PEPS/FET write-back | Candidate selection, private RNG, endpoint validation, transactional rollback, and selector-to-map-to-endpoint authentication pass. | The strict-target d3 runs are all no-op; useful rank-reducing pruning is not validated. |
| PEPS replay | Fresh-process repeat, ambient-CUDA-seed change, and fidelity-curve debug observation are bitwise-equal on the declared captured scope. | Replay determinism does not cure solver failure or the absent active-truncation falsifier. |
| PEPS entropy | All four leak-off cases match the independent GF(2) value `S_A=2.0` with zero deviation at tolerance `1e-4`. | This authenticates the identity-fallback state, not FET pruning or the complete detector/observable law. |

## MPS repair

The previous shadow ledger counted dense logical cuts rather than the splits actually executed by
Quimb. The repair routes supported two-qubit unitaries through the pinned Quimb-1.14.0 swap,
operator, and reverse-swap sequence and records every low-level split. The adapter validates the cap,
operator, dtype, device, finiteness, norm-loss reconciliation, and transactional commit before the
candidate state replaces the input.

The execution layer now derives the expected gate-occurrence inventory before execution. Exact
branches must supply a unique contiguous branch set with unit incoming mass; sampled execution must
cover every expected occurrence once per declared trajectory, including zero-event trajectories.
Missing whole Strang passes and same-count/wrong-identity ledgers fail closed. Any observed finite
loss requires both an explicit worst-cut gate and an explicit path-total gate for restricted
acceptance. Jump/no-jump norms remain physical branch probabilities and are never routed through the
unitary truncation cutoff.

The restricted claim deliberately excludes capped multilevel clusters and connected Hamiltonian
clusters wider than two sites; those paths continue to fail before dense allocation. Per-split local
discarded fractions are diagnostic heuristics and are not asserted to be a global error bound.

## PEPS committed replay

Artifact:
`outputs/simulator_validation/diagnostics/peps_fet_replay_audit_postfix/report.json`

- schema: `error_coupling_simulator.peps.fet_replay_audit.v5`
- bound commit: `c8c553e7f3665f6fae29cca5696905f09d6643d0`
- content hash: `8c6d13b2a41ac6843f444d788ec12bd0d2744132399d2ca015d1f0bf17330228`
- file SHA-256: `38b9299ccf5cc82f660fb990c9382dba45e70a7d3d182558356072e4b9128deb`
- replay: `PASS_SCOPED_BITWISE`
- fallback/mutation contract: `PASS`
- entropy: `PASS`
- solver health: `RED`
- non-degeneracy: `RED`
- overall: `RED`

The four fixed cases are the fresh-process repeat pair, a changed ambient CUDA seed, and a
fidelity-curve-debug observer case. Each case emitted 16 cuts, applied zero authenticated
rank-reducing write-backs, kept ambient Torch RNG unchanged, and returned `S_A=2.0`. Across the 64
cuts, all 64 finite selected candidates were below the registered target; fallback produced no
mutation-contract violation and no nonfinite selected fidelity. Solver health nevertheless failed
on every cut: each cut contained at least one failed attempted rank, totalling 324 failed rank
attempts out of 432 attempts.

All three declared comparisons reported identical categorical capture, record payload, raw map-hash
sequence, and zero maximum captured scalar or `Fid_gamma` difference. Parent-side replay
authentication recomputed the raw wrapper/trajectory agreement and the selected-map-to-applied-map-
to-endpoint causal chain; a worker's self-declared authentication marker was not trusted.

## Verification commands and results

```text
tests/test_peps_fet_replay_audit.py
    33 passed

tests/test_peps_fet.py, CPU mutation-firewall subset
    25 passed, 10 deselected

tests/test_peps_fet.py, full d3 GPU falsifier
    34 passed, 1 expected scientific failure
    failing gate: accepted rank-reducing write-back required

MPS helper + dense certification + Axis-1 schedule + scope boundary
    247 passed, 1 skipped

PEPS host seam + trajectory carrier
    31 passed, 1 warning

py_compile, JSON validation, git diff --check, generated CODE_MAP drift check
    PASS
```

The full PEPS suite intentionally retains the non-degeneracy failure. Removing or weakening that
test would hide the present scientific blocker.

## Remaining repair route

The next PEPS phase is not a threshold relaxation. It must first diagnose the 324 failed rank
attempts and establish solver convergence/metric health under an explicit epsilon-and-rank ladder.
Any configuration that produces active truncation must then pass an independent d3 state or record
reference, the same corruption falsifiers, and the active-write non-degeneracy gate. The
primary-literature bridge from the local FET objective to QEC entropy and complete record-law error
also remains open. Until those conditions close, d5/d7 PEPS pruning and full-record faithfulness are
not accepted scientific premises.
