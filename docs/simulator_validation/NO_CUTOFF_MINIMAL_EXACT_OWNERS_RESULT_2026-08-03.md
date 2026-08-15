# No-cutoff minimal exact owners — result, 2026-08-03

## Terminal status

This is the bounded execution of
`NO_CUTOFF_MINIMAL_EXACT_OWNERS_PREREG_2026-08-03.md`.  It qualifies three
corruption-sensitive exact micro-owners; it does not lower the frozen d=3/5
QEC circuit into any of them.

```text
report_status = VALID_MINIMAL_EXACT_OWNER_QUALIFICATION_CODE_BLOCKED
pair_micro_owner = QUALIFIED
dynamic_add_micro_owner = QUALIFIED
retained_boundary_tn_micro_owner = QUALIFIED
target_pair_owner = UNAVAILABLE/NO_TARGET_QEC_PAIR_LOWERING
target_dynamic_add_owner = UNAVAILABLE/NO_TARGET_QEC_DYNAMIC_ADD_LOWERING
target_retained_boundary_tn_owner = UNAVAILABLE/NO_TARGET_QEC_TN_LOWERING
target_d3_d5_metrics = UNAVAILABLE
delta_tv_cert = UNAVAILABLE/UNANCHORED_FULL_RECORD
route_disposition = NO_ROUTE_KILLED_OR_PROMOTED_BY_MICROFIXTURE
solver_permission = CODE_BLOCKED
```

The historical d=3/5 census artifact remains byte-identical at SHA-256
`88e6175dc3b7d1474c155f06cf1857484a96a8d3f6754a5e91b4c66a5292918b`.
None of its unavailable cells was rewritten.

## Library-to-metric conclusion

The source-level audit found no direct library owner for any of the three
frozen metrics:

- pair: Stim is an adaptor and SymPy is the independent exact oracle;
- dynamic ADD: Sylvan is the strongest inspected future substrate, with OxiDD
  next; neither owns the project codec, recurrence, count, or certificate;
- retained-boundary TN: cotengra, Jdrasil, and NetworkX are corroborators or
  planners with different objectives/certificates.

Therefore a missing one-stop library was not used to kill a route, and the
existence of these micro-owners was not used to promote one.

## Exact observations

| owner | frozen exact observation | qualification boundary |
|---|---|---|
| pair | support history `[2,8,2]`; peak `8` at `E1_BRANCH` | trivial-coset microfixture only |
| dynamic ADD | terminal-inclusive reachable-node history `[7,20,11]`; peak `20` | dynamic pair map, not a final Record-PMF MTBDD |
| retained-boundary TN | exact width `3`; exact mixed-domain `lambda=6`; dense capacity `64` | five internal plus two retained Record indices |

The pair and ADD owners retain the exact nonzero tail
`sqrt(2)/2^42 < 1e-12` while deleting the independently derived exact-zero
interference branch.  No magnitude cutoff or floating terminal is used.

The retained-boundary owner optimizes its two objectives separately.  The
unweighted selected order has `(width,lambda)=(3,7)`; the weighted selected
order has `(4,6)`.  The independent 120-order oracle finds respectively 12 and
16 optimal orders, with disjoint optimum sets, and reproduces both complete
32-cell subset-DP tables.

## Independent checks and falsifiers

- The independent SymPy 1.14.0 module restates the fixture without importing
  owner model/codec/transition/serialization helpers.  It checks every 64, 64,
  and 128 checkpoint assignment and every 4,096 and 8,192 relation assignment.
- The independent stdlib TN module restates factors, domains, KEEP indices,
  replay, exhaustive orders, and subset DP without importing candidate graph or
  proof helpers.
- The report validator reconstructs every checkpoint and relation canonical ADD
  table from the independent literal witnesses.  It also re-executes the exact
  control ledger rather than trusting self-hashed expected values.
- Rehashed forgeries of a control result, ADD terminal, pair/oracle nested hash,
  test receipt, SymPy version, provenance field, publication step, and report
  complete-file hash are rejected.
- Codec/transition/order/GC controls, both sensitive TN edge deletions, domain
  changes, missing KEEP, unknown/duplicate/invalid/incomplete schemas, fixed-
  output `(2,5)` ineligibility, and corrupted proof/floor/tie-break all fire.

## Artifact and publication evidence

Canonical report:

`outputs/external_baselines/no_cutoff_minimal_exact_owners_20260803/report.json`

- complete-file SHA-256:
  `fb645bb886c4b35c8efd2977956c50df9afca88c9c9be58716307d9dc6baf777`;
- internal content SHA-256:
  `5fd753b7e5de415a3063dd65a0322f22f3baef42ce09a054ab5c400f822ab395`.

Outer publication receipt:

`outputs/external_baselines/no_cutoff_minimal_exact_owners_20260803/publication_receipt.json`

- complete-file SHA-256:
  `ce6a332e16f2839d50839ee86ad54a269d3bc192ee65ba0795e7a83ecaae29b8`;
- internal content SHA-256:
  `dde71354e384c199eaf3c9364be563d13719ae64ae3af273a1b3e607f6e639e2`.

The report identifies itself only as prepared for exclusive publication.  The
outer receipt owns successful no-replace return, file and parent-directory
fsync, strict reload, report complete-file hash, and a fresh seven-test report-
contract execution.  A second CLI publication is required to fail no-replace.

The report additionally binds CPython 3.12.13, SymPy 1.14.0, pytest 8.4.2,
Python executable, package version/tree/import origin, Git commit/tree and
honest dirty state, tracked diff, `uv.lock`, `pyproject.toml`, Conda package
records/history, exact run shape, source/test bytes, active preregistration,
library audit, and historical census.

## Verification snapshot

```text
fresh owner/oracle qualification embedded by report: 27 passed
fresh report contract bound by outer receipt: 7 passed
focused owners + oracles + report + historical census: 65 passed
git diff --check: PASS
python tools/gen_code_map.py --check: PASS
independent adversarial audit: SURVIVES CURRENT WIRES
```

No `src/**` file was changed and no solver was added.
