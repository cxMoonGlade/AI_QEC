# Vanderstraeten arXiv:2110.12726v2 — Round-3 blocker repair

Date: 2026-07-27

Repair owner: `/root/repair_vander_audit_round3`

Repair status: `MECHANICAL_REPAIR_APPLIED_PENDING_FRESH_INDEPENDENT_REREVIEW`

This packet records the mechanical repair of exactly the three blockers in
`VANDERSTRAETEN_2110_12726V2_INDEPENDENT_SOURCE_REREVIEW_ROUND3_2026-07-27.md`.
It does not make an independent source-review decision, change the candidate's
draft status, or change `docs/papers/CURRENT_CORPUS.toml`.

## 1. Direct pinned-source checks

The pinned 18-page PDF was verified as an unencrypted `%PDF-1.5` artifact with
SHA-256
`58763a732ef1c5b660bacbc708a2134b1c8a09096eca1e44326c03a1b540a184`.
The following source pages and formulas were checked directly before editing:

| Round-3 blocker | direct source check | bounded repair consequence |
|---|---|---|
| bare benchmark `D=5` | PDF p. 2, Sec. II first paragraph visually separates the physical index from the four virtual indices and assigns bond dimension `D` to those four virtual indices; PDF p. 9, Sec. VI opening gives benchmark bond dimension `D=5` | the independently readable benchmark row now says “PEPS virtual bond dimension `D=5`” |
| conflated `M` notation | PDF p. 3, Sec. II, Eqs. (10)--(12) visually uses `M` and `M̃` for boundary MPSs found from the two directions; footnote 3 says there is generally no simple relation between them. PDF p. 4, Sec. IV.A, Eqs. (24)--(29) visually uses `M` and `M̄` for the Hermitian variational ket/bra pair | the notation ledger and replay now keep `M,M̃` separate from `M,M̄` |
| lost `N/L` overload | PDF p. 1 Abstract and PDF p. 6 Sec. V opening use “`N`-point” for correlation-function insertion count. PDF p. 8 Eq. (62) visually displays window tensors `N_1,N_2,...,N_L`. PDF pp. 10--11, Sec. VI.C prose/Figs. 5--6 use `N` for benchmark window size, including `N=10` in the Fig. 6 caption | the notation ledger has three separate entries and the replay attaches each use to its own locator |

No additional mechanism, result, application, or project bridge was added.

## 2. Exact repair scope

### Source-only audit

Only these audit surfaces changed:

1. assigned-closure row `reported contraction benchmarks`:
   `On selected D=5 ...` became
   `On selected ... PEPS with PEPS virtual bond dimension D=5 ...`;
2. notation ledger:
   the former conflated `M,M̄` row was replaced by distinct `M,M̃` and
   `M,M̄` rows with exact source roles and locators;
3. notation ledger:
   the former single finite-window-`N` row was replaced by distinct
   `N`-point, `N_i` through `N_L`, and benchmark-window-size `N` rows;
4. operation replay §§5.1--5.3:
   the general left/right boundary tensors, Hermitian ket/bra tensors, and
   three overloaded `N/L` roles are now named and source-located explicitly.

### Source-only note

The note body and every source-evidence record are byte-unchanged. The only
note edit is the frontmatter value
`audit_packet_sha256`, updated to the repaired audit hash. In particular:

```toml
admission_status = "draft_pending_review"
admission_reviewer = "pending_fresh_independent_source_only_rereview_after_repair"
```

remain unchanged.

### Excluded surfaces

- `docs/papers/CURRENT_CORPUS.toml` was not written;
- the pinned PDF was not written;
- the Round-3 reviewer report and earlier reviewer reports were not written;
- no source code, test, manifest generator, or schema was written.

## 3. Before/after artifact ledger

The before identities are the exact Round-3 reviewed snapshots recorded in the
Round-3 report. The after identities were recomputed from the repaired files.

| artifact | before bytes | before SHA-256 | after bytes | after SHA-256 |
|---|---:|---|---:|---|
| pinned PDF | 1,620,330 | `58763a732ef1c5b660bacbc708a2134b1c8a09096eca1e44326c03a1b540a184` | 1,620,330 | `58763a732ef1c5b660bacbc708a2134b1c8a09096eca1e44326c03a1b540a184` |
| source-only audit | 13,248 | `d33603d6d00baafe90113d1e3969918ba77fd87d3c3ab45a062de1ab15b06af0` | 15,024 | `4cd67341564d8f8354252331f68e07abc35fad557dccbc01c2c7b9ca1ed26046` |
| source-only note | 14,193 | `9573f307893f70d0833342f4b0b7b7ef556db793148d35e8c49309518bd80bc6` | 14,193 | `9b51b118037d3f8696b7b5c0ab03ab6dcc1f28e6f3f4afd7efd52cd630c5d017` |

The note's stored `audit_packet_sha256` is exactly the after audit SHA-256.

`docs/papers/CURRENT_CORPUS.toml` was outside the repair write scope. Its
post-repair observed SHA-256 was
`3a9445ccffdc2fbc21f4f2b3ce3e13f021d072a060d41ea87f12b1afcb29cd29`,
and neither `arxiv:2110.12726` nor the Vanderstraeten note path was present.
That hash records the shared-workspace observation only; it is not claimed as
a before/after identity for this task.

## 4. Status-toggle-only artifact preflight

The on-disk note was first kept unchanged. A self-deleting temporary copy in
the note directory changed exactly one byte-string occurrence:

```toml
admission_status = "draft_pending_review"
```

to:

```toml
admission_status = "source_only_reviewed"
```

`parse_note(..., verify_artifact=True)` then completed without exception and
returned:

```text
total=28 paper_fact=21 literature_gap=7 relations=5
checked_pages=1,2,3,4,5,6,7,8,9,10,11,12,14,15,16,17,18
audit_packet_sha256=4cd67341564d8f8354252331f68e07abc35fad557dccbc01c2c7b9ca1ed26046
```

The status-only diagnostic note SHA-256 was
`8757f347cfbd10a4104c67798d06233eb53dc03cabddc0c6a24886703e1b21bc`.
It is a temporary diagnostic identity and is not written to the corpus
manifest.

After the temporary file was closed and removed, the original on-disk note was
byte-compared with its preflight input. A direct artifact-verifying parse of
that on-disk note stopped at the intended draft gate:

```text
admission_status must be 'source_only_reviewed'
```

Thus the preflight records structural and artifact consistency under the
single simulated status toggle. It is not a semantic rereview, source-review
verdict, or corpus-promotion authorization.

## 5. Required next boundary

The repaired draft still requires a fresh independent source-first rereview.
This repair packet does not change reviewer identity, candidate status, or
corpus membership.
