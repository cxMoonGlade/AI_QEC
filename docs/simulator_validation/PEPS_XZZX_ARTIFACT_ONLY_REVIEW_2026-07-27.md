# PEPS XZZX artifact-only implementation review

Status: **PASS**

Reviewer mode: `new_unled_read_only`

Reviewed implementation commit:
`dcd3f9407046893ef8f81c96c5c3cc73a8c6c76b`

Frozen preregistration commit:
`dc7f6a6a4bbc2ae3e8ba8dea6f00343ef9a9fc67`

Frozen preregistration SHA-256:
`76889bb6f9287ec7b5278257a81c71aacdbf697eb8a051003b1fbd90c05d4c36`

## Review boundary

This was a new, un-led, read-only review of the committed implementation
bytes named by `REVIEWED_IMPLEMENTATION_PATHS` in
`scripts/external_baselines/run_xzzx_record_peps_experiment.py`. No prior
review conclusion or target result was used. No tracer target, formal d3
primary/alternate output, formal d5 output, or other target output was opened
or executed. The implementation was not modified.

The frozen preregistration bytes were read directly from the frozen commit and
independently hashed to the value above. HEAD and every reviewed implementation
path were verified byte-clean at the reviewed commit. The exact per-path Git
blob and SHA-256 ledger is in the matching JSON sidecar.

## Findings

No preregistration-critical blocker was found.

- Fixture/spec identity is fail-closed for d2/d3/d5. The emitter reconstructs
  the inherited v1 neutral fixtures, preserves the registered Stim, fixture,
  enumeration-spec, and v2 run-spec hashes, fixes both `RY(0.02)` insertions,
  and rejects mutation, aliasing, replacement, and schedule drift.
- The exact data-projector worker is independent of Quimb, Qiskit, Stim, and
  candidate payloads. It derives signed, commuting, equal-round data checks
  from the neutral operation ledger, constructs both outcomes from projected
  vectors, preserves every positive probability, implements the frozen
  SHA-256 prefix selector exactly, derives the registered d3 alternate, and
  emits the complete d3 all-active or d5 `2^25` data vector in the frozen axis
  order.
- The full dense d2/d3 worker independently hand-builds the complete
  complex128 state evolution, selective reset, probability ledger, two RY
  blocks, X readout, and absolute detector/observable fold. Formal d3 replay
  consumes only the authenticated neutral branch bits from the exact primary;
  it does not consume exact state amplitudes as an oracle.
- The Quimb candidate accepts only the bits-only neutral branch and
  authenticated exact branch authority. Copied branches use isolated backend
  caches. Selective reset applies the normalized rank-one map directly,
  preserves gauge bytes, requires exact physical-one tensor-slice zeros, and
  records independent one-site RDM reset checks. Candidate artifacts export no
  tensors, gauges, or exact-reference probabilities/states.
- The metric owner is independent of both execution implementations. It
  requires complete complex128 vectors and frozen axis order, separately
  evaluates raw-law and folded-Record TV, aligns every probability column,
  computes maximum conditional-probability and log-mass error without a
  probability floor, checks reset trace distance and the realized absolute
  fold, and cannot promote high state fidelity when a mass/reset/fold gate
  fails.
- The runner authenticates this review and all committed inputs before
  execution, sanitizes inherited Python/Conda/loader/toolkit state, uses fresh
  process groups under the frozen wall/host/device limits and one GPU lock,
  and publishes to fresh, exclusive paths with file and directory fsync.
- Execution order is frozen. All core and Quimb corruption controls precede
  targets; d2 complete-law/nondegeneracy and both d3 exact-vs-dense gates
  precede every d3 PEPS point; both primary and alternate run
  `D=[1,2,4,8]`; d5 is authorized only by the conjunctive d2/control/d3 gate;
  d5 then runs only the exact primary and the fixed `D=[1,2,4]`,
  radius `[0,1,2,3]` grid. Missing alternate, incomplete vector, resource
  failure, or failed gate remains unavailable and blocks promotion.
- D3 monotonicity is reported with the frozen `1e-8` tolerance, while the
  preregistered bond-knob movement and both `D=8` usefulness verdicts are
  authorization gates. The terminal d5 verdict is owned only by `D=4`,
  radius 3 after the complete fixed grid is present.

## Non-target verification

The exact committed runner isolation was used:

- `ecs`: the five core fixture/dense/exact/metric/runner files — **61 passed,
  0 skipped** in 10.92 s.
- `ecs-baseline-quimb-peps` with
  `ECS_XZZX_REQUIRE_CUDA_CONTROLS=1`: the candidate file — **25 passed,
  0 skipped** in 210.05 s.

An earlier combined diagnostic in `ecs` reported nine skips, all at the
candidate suite's explicit isolated-Quimb environment guard. Those skips are
not credited as PASS evidence; rerunning the file in the committed runner's
required environment exercised and passed all 25 candidate tests.

This PASS authorizes only the committed experiment plumbing to proceed to its
frozen target gates. It is not a target result, a d5 full-law certificate, a
leakage/Kraus/decoder claim, or a scalable PEPS-faithfulness conclusion.
