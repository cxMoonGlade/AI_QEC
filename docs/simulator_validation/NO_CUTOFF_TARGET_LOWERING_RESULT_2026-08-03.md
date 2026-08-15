# No-cutoff target lowering — result, 2026-08-03

## Terminal status

This is the bounded execution of
`NO_CUTOFF_TARGET_LOWERING_PREREG_2026-08-03.md`.  It qualifies static target
lowerings for the eight frozen `(d,R)` cells with `d in {3,5}` and
`R in {1,3,5,7}`.  It does not execute a pair frontier, compile an ADD root,
choose a TN order, contract a TN, or construct a complete Record law.

```text
report_status = VALID_STATIC_TARGET_LOWERING_QUALIFICATION_CODE_BLOCKED
neutral = QUALIFIED_STATIC_TARGET_LOWERING
pair = QUALIFIED_STATIC_TARGET_LOWERING
add_relations = QUALIFIED_STATIC_TARGET_LOWERING
tn = QUALIFIED_STATIC_TARGET_LOWERING
all architecture metrics = UNAVAILABLE/NOT_EXECUTED_STATIC_LOWERING_STAGE
delta_tv_cert = UNAVAILABLE/UNANCHORED_FULL_RECORD
route_disposition = NONE/STATIC_LOWERING_ONLY
solver_permission = CODE_BLOCKED
```

No route is killed or promoted by this result.

## Qualified objects

The publication owns 32 canonical programs: one evaluator-truth-free
`DeclaredErrorRecordProgram`, one complete local
`ExactPairTransitionProgram`, one root-independent
`DynamicADDRelationProgram`, and one uncontracted
`RetainedBoundaryFactorNetwork` for every frozen cell.

The pair object retains the persistent coherent latent, complete exact
Pauli/Kraus component rows, chronological codecs, and signed leftmost-pivot
GF(2) reductions.  The ADD object owns the full local input-by-output relation,
including invalid codes as exact structural zeros, but owns no root.  The TN
object owns dense exact templates and typed sign, raw, XOR, COPY, and KEEP
incidence, but owns no contraction.

## Independent evidence and falsifiers

- 56 independent receipts cover source text, pair matrices, signed GF(2), ADD
  relations, literal TN tables, incidence, and direct-density witnesses.
- The complete P1/P2 and T1--T4 ADD truth surfaces contain respectively
  `32,768`, `4,194,304`, `98,304`, `163,840`, `114,688`, and `44,040,192`
  input-output rows.  Owner and independent hashes agree for every valid and
  invalid code.  The T4 digest is
  `cc2a5ec8482d7f59cc2fc65c7d2a5321fcbaafdee6a634e3c862c331df05e6e9`.
- A joint persistent-sign audit traverses neutral declaration, pair initial
  prior/kernel/checkpoint binding, and the complete ordered TN `SIGN_EQ` chain.
  A resampled neutral declaration fails while pair and TN subchecks still pass;
  replacing every `SIGN_EQ` by an IID half factor fails only the TN subcheck and
  also changes the independent T3 retained tensor.
- All 33 registered corruption controls trip.  They cover source/Record drift,
  algebra and signed-RREF errors, codec/liveness loss, ADD coefficient/root
  injection, TN table/incidence/sign corruption, numeric metric injection, and
  historical-artifact drift.

No magnitude cutoff or floating zero is used by these qualifications.

## Publication evidence

Canonical report:

`outputs/external_baselines/no_cutoff_target_lowering_20260803/qualification_report.json`

- complete-file SHA-256:
  `0e274fe73c2067477802d8539be19885f0ee33bb8185a4ac60c7021d6a5d4db1`;
- internal content SHA-256:
  `bd11b9fec612019b30227a42ce68f2344f55baae1d9bb58b9b72f81936ca0c7e`.

Outer publication receipt:

`outputs/external_baselines/no_cutoff_target_lowering_20260803/publication_receipt.json`

- complete-file SHA-256:
  `63523f715e8a1e28e03ca020003bdad3a6f2e87cf665fe55c139fdea48853aef`;
- internal content SHA-256:
  `3abb91289bab54b867110748e90fb650092a4a39735a901ef5178ef143bf5dd6`.

The published tree contains exactly 34 regular files and no symlink.  The
production entry point observed the exact frozen six-file test set with
`98 passed`, `0 failed`, and 98 exact node IDs before minting its in-process
publication capability.  It then wrote a same-parent staging tree, strictly
reloaded it through held descriptors, fsynced files and directories, committed
with no-replace rename, and revalidated the committed inode.

## Verification snapshot

```text
manual frozen six-file qualification: 98 passed in 523.23 s
production fresh qualification embedded in report: 98 passed, 0 failed
post-publication strict reload and manifest rehash: PASS
published regular-file count: 34
published symlink count: 0
registered corruption controls: 33/33 TRIPPED
historical structure report SHA-256: 88e6175dc3b7d1474c155f06cf1857484a96a8d3f6754a5e91b4c66a5292918b
historical minimal-owner report SHA-256: fb645bb886c4b35c8efd2977956c50df9afca88c9c9be58716307d9dc6baf777
historical minimal-owner receipt SHA-256: ce6a332e16f2839d50839ee86ad54a269d3bc192ee65ba0795e7a83ecaae29b8
git diff --check: PASS
```

No `src/**` file was changed and no solver was added.
