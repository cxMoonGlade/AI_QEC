# Restricted MPS Phase 6 — certification ownership and public Interface — implementation GREEN — 2026-07-17

> Historical phase snapshot. Schema identities and registry counts below describe this phase at
> review time; current identities live in `docs/SIMULATOR.md` and the frontend owning README.

## Disposition

Disposition: **GREEN for the Phase 6 source ownership, public Interface, and strict public-unit
coverage gates; final phase acceptance remains pending generated-map/package/fresh-process
finalization**.

This packet is bound to the uncommitted reviewed working tree based on
`HEAD f0d52b3f153d3f4dd9e9a9cb30f65ed3b3f3ae54`. It does not register MPS as a scientific
Carrier, establish Record or LER faithfulness, choose a production pruning policy, or claim a
production-scalable backend.

## Ownership hard cuts

| Surface | Phase 6 result | Compatibility disposition |
|---|---|---|
| Dense restricted-MPS certification | Hard-moved from `frontend/axis1_mcwf_dense_certification.py` to `certify/axis1_mps.py`. The owner consumes immutable execution evidence and owns dense References, metrics, and final restricted acceptance. | No forwarding shim or old import path. |
| QT contract-only Module | `frontend/axis1_qt_mps_contract.py` deleted; the executable QT Adapter owns its execution contract. | No compatibility reader or alias. |
| MCWF contract-only Module | `frontend/axis1_mcwf_mps_contract.py` deleted; the executable MCWF Adapter owns its execution contract. | No compatibility reader or alias. |
| Restricted-MPS service | `docs/service_status.json` classifies `restricted_axis1_1d_mps` as `kind="restricted_verification"` and lists six executable public entry points. | It is not registered as a third scientific Carrier. |

The dependency direction is now `frontend Adapter -> carrier/mps mechanics` for execution and
`certify/axis1_mps.py -> immutable evidence + independent Reference` for certification. Execution
mechanics do not self-certify, and the certification owner does not mutate MPS state.

## Interface repairs

- MCWF pre-readout multilevel records, their counts/probabilities, and jump-family counts live under
  `evaluator_only_diagnostics`. They are not top-level emitted binary Records and are not downstream
  estimator inputs. Caller-declared `local_dims`, `initial_levels`, and `leaked_readout_b` remain
  configuration.
- Actual finite-bond split payloads use `actual_kept_bond_dimension`, meaning the retained virtual
  index size. A thresholded numerical rank is a different diagnostic and must serialize its
  threshold.
- The direct MCWF execution schema is v5. The QT direct schema reached v5 for the kept-dimension
  rename before Phase 7 changed its sampled-support semantics again; its current identity is v6.
  No retired direct schema is accepted through a fallback path.
- The non-scientific-carrier disclaimer is present in `docs/SIMULATOR.md`,
  `docs/ARCHITECTURE.md`, and `carrier/mps/README.md`.

## Strict public-unit coverage gate

The current registry reconciles ten Modules and 38 canonical public units one-to-one. It has zero
exemptions. The gate keeps a 100% statement and 100% branch target for every registered unit; it does
not lower targets or classify misses away.

Command:

```text
conda run -n ecs python tests/harness/gate.py \
  tests/_support/restricted_mps_coverage_targets.json
```

Current result:

```text
907 passed, 1 skipped, 27 warnings in 13.07s
```

Evidence:

- registry: `tests/_support/restricted_mps_coverage_targets.json`, SHA-256
  `a1042ae146857033d75ea34a5c126928b34d0d31e0196cf6ac76b4b9f2a5adf8`;
- gate log: `outputs/simulator_validation/logs/restricted_mps_coverage_targets_gate.log`, SHA-256
  `a4aef56227ddb8ee940e6ba0ed8ab54853642ea8f4f608673895f9924713dd1f`;
- coverage JSON: `outputs/simulator_validation/logs/restricted_mps_coverage_targets_coverage.json`,
  SHA-256 `fc893e1dbf6e8187cc0027846f57668fe97a60b4320369239a2bd0b811ad9854`.

The 100% statement/branch claim applies to the 38 registered public units, not every private helper
or every line in the ten source files.

## Pending finalization and non-claims

`python tools/gen_code_map.py --check` currently reports the generated CODE_MAP as stale. The
post-change package build and canonical aggregate fresh-process service acceptance are also not yet
recorded in this packet. Those are required before the complete Phase 6 exit is called accepted.

This report does not claim that evaluator-only diagnostics certify emitted Records, that a kept bond
dimension is a numerical rank, that coverage establishes scientific correctness, or that any
finite-bond discarded-weight ledger is a global state/Record/LER bound.
