# No-cutoff structure census result — 2026-08-03

## Status and claim boundary

This is the bounded structure-only execution of the active preregistration
`NO_CUTOFF_STRUCTURE_CENSUS_PREREG_2026-08-03.md`.  It compiles/plans the
frozen persistent coherent declared-error shadows without coefficient cutoff,
sampling, or state-vector allocation.  It does not construct or certify the
complete non-Markovian detector/observable Record.

The terminal status is:

```text
report_status = VALID_BOUNDED_STRUCTURE_CENSUS_CODE_BLOCKED
clifft_frame = NOT_KILLED_ON_FROZEN_GRID
exact_pair = INDETERMINATE
dynamic_add = INDETERMINATE
retained_boundary_tn = INDETERMINATE
faithfulness_disposition = UNAVAILABLE
certification_verdict = UNANCHORED
solver_permission = CODE_BLOCKED
```

`NOT_KILLED_ON_FROZEN_GRID` means only that the pinned Clifft representation
fails the preregistered all-three-doubling rejection rule.  It is not evidence
of asymptotic or full-Record scalability.

## Frozen grid observations

`B_Clifft=2**k_Clifft` is the only headline active-coordinate burden.  The
SymFT monolithic burden is supplemental and cannot kill its component route.

| d | rounds | Clifft k | Clifft burden | SymFT k | SymFT monolithic burden |
|---:|---:|---:|---:|---:|---:|
| 3 | 1 | 0 | 1 | 4 | 16 |
| 3 | 3 | 8 | 256 | 7 | 128 |
| 3 | 5 | 8 | 256 | 7 | 128 |
| 3 | 7 | 8 | 256 | 7 | 128 |
| 5 | 1 | 0 | 1 | 12 | 4,096 |
| 5 | 3 | 24 | 16,777,216 | 22 | 4,194,304 |
| 5 | 5 | 24 | 16,777,216 | 22 | 4,194,304 |
| 5 | 7 | 24 | 16,777,216 | 22 | 4,194,304 |

For both distances, Clifft proves doubling on `1->3` and proves non-doubling
on `3->5` and `5->7`.  Therefore both fixed-distance slices and the aggregate
are `NOT_KILLED_ON_FROZEN_GRID`.  The initial jump is large—`1 -> 256` at d3
and `1 -> 16,777,216` at d5—but it is not sustained across the frozen grid.

The supplemental SymFT planner also plateaus after round 3.  At d5 its selected
component diagnostics for rounds `(1,3,5,7)` are:

| quantity | R=1 | R=3 | R=5 | R=7 |
|---|---:|---:|---:|---:|
| component count | 12 | 36 | 60 | 84 |
| peak live dimension | 4,096 | 1,048,580 | 1,048,580 | 1,048,580 |
| allocated dimension | 4,138 | 1,048,666 | 1,048,714 | 1,048,762 |

These component quantities are diagnostics only; no preregistered SymFT route
disposition exists.

## Cutoff and non-degeneracy controls

- Every primary-plus, primary-minus, tiny-plus, and tiny-minus shadow completed.
  Within each `(d,R)` cell, the four complete Clifft active histories and the
  four normalized SymFT structural outputs were identical.
- The tiny half-turn parser argument was the nonzero binary64 value
  `1.2732395447351627e-20` (`0x1.e1042c3d96d7fp-67`).  It was not demoted to
  zero by the headline squeeze-only Clifft route.
- All eight algebraic `t=0` shadows omitted every replacement `R_Z` row and
  returned Clifft `k=0` and SymFT `k=0`.  Their histories/structures remained
  distinct from the corresponding nonzero targets; at `R>=3`, target Clifft
  `k` was strictly positive.
- The independent exact-SymPy tracer matched a separate matrix-branch
  construction.  Its frozen positive tail atom remained exactly
  `7984925229121/64063097262168921289605376`, strictly between zero and
  `1e-12`, while the wrong-observable atom remained an exact structural zero.

## Mandatory unavailable families

No numerical value was manufactured for an absent owner:

| family | status / reason | route disposition |
|---|---|---|
| `N_pair` | `UNAVAILABLE/NO_EXACT_PAIR_OWNER` | `INDETERMINATE` |
| dynamic `N_DD` | `UNAVAILABLE/NO_EXACT_DYNAMIC_ADD_OWNER` | `INDETERMINATE` |
| retained-boundary `tw` and mixed-domain burden | `UNAVAILABLE/NO_CANONICAL_RETAINED_RECORD_TN_OWNER` | `INDETERMINATE` |
| complete-Record `Delta_TV_cert` | `UNAVAILABLE/UNANCHORED_FULL_RECORD` | faithfulness `UNAVAILABLE` |

The exact final-PMF MTBDD in the small oracle remains explicitly supplemental;
it cannot populate dynamic `N_DD`.  A raw recursion count, fixed-output scalar
treewidth, heuristic treewidth, sampled TV, fidelity, or sentinel zero is also
ineligible.

## Execution and provenance

The canonical run artifact is
`outputs/external_baselines/no_cutoff_structure_census_20260803/report_v3.json`,
SHA-256
`88e6175dc3b7d1474c155f06cf1857484a96a8d3f6754a5e91b4c66a5292918b`.
It is canonical finite JSON, contains the complete Clifft histories, binds every
fixture/variant/source/output hash, records both external trees as pristine,
and independently revalidates after reload.

- Census serializer source SHA-256:
  `382cf0145b92cdda021f5534657ddc357dd439733e79bfd41a848e829b0a6bf9`.
- Exact-small oracle source SHA-256:
  `0cbb222a716f9e4717b6661a2fb1a2f70559d99c6b83a244776d499df50a735f`.
- Fixture manifest SHA-256:
  `40474ca0beab8341d53bfa41da5438e052744bb83ae6af2632e1bfe273c53c74`.
- Active preregistration SHA-256:
  `be17c2930c5b0a8acdf817163e75ec285fc2de276ef856d5e6a846a6b6f20216`.
- Clifft commit/tree:
  `2c1dfa6029c4f0573c499e938e9a88106a6801b3` /
  `9306ba4fa6d64ec0b9c5835298bf7586916e5b6c`; wheel SHA-256
  `8b8ce0e13fec7071881a6f43fe48ac85339701cccfefd49a6454954c9cbb81f0`;
  extension SHA-256
  `01c6bbba85080507104081ec0ec12b4af67c964fb91b58f40797efe5ecf4a1a1`.
- SOFT/SymFT commit/tree:
  `bc9a8d2e33b1e03d411c4088f8255299c80a51eb` /
  `c24cefb2001cf295fe555637e3be5962d2bf0ffa`; planner executable SHA-256
  `dbb71c5571231effcc414bb87bdc86967966dcdae473d74d720d87a24c9f921b`.

The Clifft wheel and SymFT executable are content-bound, but their build
dependency locks are honestly recorded as not attested.  This caveat does not
change the observed hashes or finite-grid disposition; it does prevent treating
the build environment as a fully locked reproducibility package.

Engineering verification at this result snapshot:

```text
conda run -n ecs python -m pytest -q tests/test_external_no_cutoff_structure_census.py
31 passed

independent report reload + validate_report
VALIDATED
```

No `src/**` file was changed, and no solver was added.
