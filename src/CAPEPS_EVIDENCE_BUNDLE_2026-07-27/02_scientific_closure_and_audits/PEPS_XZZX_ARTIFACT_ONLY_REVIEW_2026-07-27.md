# PEPS XZZX artifact-only implementation review

Status: **PASS**

Reviewer mode: `new_unled_read_only`

Reviewed implementation commit:
`f89d04c22f003c265a28c765e7e4e65808ecf0f4`

Frozen preregistration commit:
`dc7f6a6a4bbc2ae3e8ba8dea6f00343ef9a9fc67`

Frozen preregistration SHA-256:
`76889bb6f9287ec7b5278257a81c71aacdbf697eb8a051003b1fbd90c05d4c36`

## Boundary and method

This was a new, un-led, read-only review of the committed Git bytes named by
`REVIEWED_IMPLEMENTATION_PATHS` in
`scripts/external_baselines/run_xzzx_record_peps_experiment.py`. The reviewed
implementation was compared with the frozen preregistration independently of
earlier review conclusions.

No target or formal result under `outputs/**` was opened, enumerated, or
executed. The implementation, scripts, tests, preregistration, and other
course documents were not modified. Only this Markdown sidecar and its
matching JSON sidecar were updated after the PASS determination.

The preregistration was read from the frozen Git object and independently
hashed. Every reviewed worktree path was checked against the corresponding
blob at the reviewed implementation commit. The exact Git-blob and SHA-256
ledger is recorded in the JSON sidecar.

## Static review result

No preregistration-critical blocker was found.

- The emitter fixes the inherited d2/d3/d5 fixture, Stim, enumeration-spec,
  and v2 run-spec identities; it applies exactly two `RY(0.02)` blocks and
  preserves the frozen absolute detector/observable rows.
- The exact data-projector worker derives the equal-round signed commuting
  checks from the neutral ledger without Stim, Quimb, Qiskit, or candidate
  inputs. Both projector outcomes come from explicit projected-vector norms.
  Their conditional probability pair is normalized without clipping or a
  floor, while the selected poststate is normalized by its raw projected
  weight. Structural zeros and representable positive probabilities remain
  distinct.
- The SHA-256 prefix selector, one-shot d3/d5 seeds, alternate-branch rule,
  complete d3 all-active embedding, and complete d5 `2^25` sorted-data vector
  follow the frozen preregistration.
- The independent dense route hand-builds the d2/d3 evolution, selective
  measurement/reset, X readout, branch-mass ledger, checkpoint, and absolute
  fold. The fixed d2/d3 control branches and the formal d3 primary comparator
  seam exercise the projector/dense agreement bands.
- The Quimb candidate uses complex128 `CircuitPEPSSimpleUpdate`, cutoff
  exactly zero, the registered D/radius grids, private copied-branch
  conversion caches, and direct normalized rank-one reset. Reset-time gauge
  keys, shapes, dtypes, and bytes are checked unchanged; physical-one slices
  must be exact zeros before RDM/state extraction.
- The metric owner requires complete hash-bound complex128 vectors in the
  frozen axis order, keeps raw-law TV distinct from folded-Record TV, aligns
  every conditional-probability column, evaluates log mass, reset trace
  distance, and the realized absolute fold, and fails closed on proxy or
  independence violations.
- The runner authenticates the frozen preregistration, this review, and the
  exact implementation path set; sanitizes inherited Python, Conda, loader,
  toolkit, and `ECS_*` state; uses fresh process groups and the frozen
  wall/host/device limits; and preserves the preregistered d2, d3, and d5
  execution and authorization order.

## Formal non-target controls

The controls were run from worktree bytes verified identical to commit
`f89d04c22f003c265a28c765e7e4e65808ecf0f4`, in an isolated environment with
no `PYTHONPATH`:

- `ecs`, the five runner-declared core test files: **65 passed, 0 skipped** in
  **11.10 s**.
- `ecs-baseline-quimb-peps`, the runner-declared candidate test file, under
  the GPU lock with `ECS_XZZX_REQUIRE_CUDA_CONTROLS=1`: **25 passed,
  0 skipped** in **210.34 s**.

Total credited formal controls: **90 passed, 0 skipped**.

This PASS is limited to the committed implementation and preregistered
experiment plumbing. It is not a target result, a d5 full-law certificate, a
leakage/Kraus/decoder claim, or a scalable PEPS-faithfulness conclusion.
