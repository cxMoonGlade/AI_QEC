# Harper et al. arXiv:2605.29514v1 — independent source rereview, Round 2

Date: 2026-07-27  
Reviewer: `/root/review_masot_source`  
Stable review label: `codex-independent-source-rereview-harper-round2-2026-07-27`  
Decision: **PASS — the repaired evidence packet is source-faithful and the prior semantic blockers are closed**

This is a PASS for the fresh independent semantic review. It does not mean that
the paper supplies the mechanisms, provenance, Record law, or resource evidence
that the repaired packet correctly marks as missing. The note is still a draft
and is not presently schema-admissible or a member of the current corpus. The
normal status, audit-hash, final note-hash, validator, and manifest sequence must
still occur after this report.

This review created only this Round 2 report. It did not modify the candidate
reading note, candidate audit, pinned PDF, or `docs/papers/CURRENT_CORPUS.toml`.

## 1. Independent protocol

The exact pinned artifact `docs/papers/2605.29514v1.pdf` was read from the title
page through the end of the bibliography before the repaired reading note,
repaired audit, or previous FAIL report was opened. All eight PDF pages were
rendered and visually inspected. Pages 2, 4, 5, and 6 were additionally checked
at high resolution for Eq. (2), Eq. (1)'s logical-angle wording, the
non-Clifford \(T/U\) derivation, Eq. (8), the \(N/n\) notation, and Fig. 5.

Only after that source judgment was fixed were the repaired note and audit read
in full. The previous FAIL report was opened last and used as a closure
checklist, not as the basis of the source reconstruction.

Text extraction was used for traversal and source-local term searches. Formula,
circuit, table, figure, and notation judgments were made from the rendered
pinned PDF.

## 2. Reviewed immutable snapshots

| object | SHA-256 | disposition |
|---|---|---|
| pinned PDF | `c13096aa841acf2b2161f18140c56dd9d3549b268969f79328ff0865583a35dd` | matches note and audit; PDF 1.7, 545,689 bytes, unencrypted, 8 pages |
| repaired candidate note | `7dac99d22227e142cf5d00a4ab6d03f6115f905c196648ac47175ab5d9b72928` | reviewed candidate snapshot |
| repaired candidate audit | `ada8ae7a500bd9a2ea0780980fb6c26a30ebb64da9b4c1f430577cafd1e85d2b` | reviewed candidate snapshot; matches the note's `audit_packet_sha256` |
| previous independent FAIL report | `188aa847924c5fa49dd5698dd8553fa0c4cac84bcb75a98c90b16a9f72bd3dce` | used only after the fresh source and packet reads |

These note and audit hashes bind the candidates reviewed here. They are not the
eventual admitted hashes: updating the audit with the Round 2 result changes the
audit hash, which must then be updated in the note before the final note hash is
computed.

## 3. Fresh source reconstruction

The source studies coherent nearest-neighbour \(ZZ\) crosstalk during repeated
rotated-surface-code syndrome extraction. It uses a GCAMPS
Clifford-frame/MPS-residual simulation, applies a PTA-derived PyMatching error
model for decoding, truncates the MPS at a reported maximum bond dimension, and
reports a logical-error observable built from syndrome-associated logical
rotation angles.

The following source boundaries are load-bearing:

- Eq. (2) prints a one-qubit depolarizing sum with coefficient \(p_1/3\), while
  the following index sentence includes \(I\). Read literally, the printed map
  has trace \(1+p_1/3\). The source never states the plausible repair
  \(i\in\{X,Y,Z\}\).
- The Sec. IV.A prose calls the non-Clifford operation \(T\), while the displayed
  derivation uses \(U\). The generic displayed Pauli sum has no coefficients or
  normalization.
- Eq. (8) visibly sums from \(1\) through \(\chi-1\). The following bound uses
  uppercase \(N\); Eq. (1) already uses \(N\) for sample count, while the Fig. 2
  caption uses lowercase \(n\) for physical-qubit count.
- Eq. (1) defines the final average once logical angles \(\theta_i\) exist, but
  the source does not define how a sampled syndrome, PTA-derived correction, and
  coherent conditional output produce each logical angle.
- Sec. IV explicitly names GCAMPS as the library used. Reference [21] is the
  GCAMPS proceedings paper; Ref. [22] is the separate stabilizer-tensor-network
  magic-state-injection paper. Neither the body nor references supply the
  version, commit, release, repository locator, or executable artifact used for
  the reported run.
- The Fig. 5 caption reports that random-sign coherent logical-error rates are
  identical to the PTA despite the coherence. Fig. 5 itself legends the
  fixed-sign and random-sign coherent curves, not a separately drawn PTA curve,
  so the null is retained exactly as a source-reported caption result rather
  than promoted to an independently demonstrated three-arm equality.
- Table I supplies reset and measurement error-rate parameters, and Sec. IV.A
  gives only a high-level projective-measurement pull-through. The source does
  not provide a selective measurement instrument, branch masses and normalized
  conditional states, a reset transaction, or a reset-state invariant.
- Repeated ancilla outcomes are called an error syndrome, but the source gives
  no absolute raw columns, temporal detector fold, logical-observable XOR rows,
  canonical raw-to-Record map, or complete Record law.
- The source provides no matched-accuracy runtime, peak-memory, or throughput
  comparison. PEPS and tree tensor networks are future-layout suggestions, not
  implemented or benchmarked result arms.

The repaired packet preserves all of these as source-local ambiguities,
inconsistencies, or absences. It does not silently repair the formulas or infer
missing executable semantics.

## 4. Prior FAIL blocker closure

Here, `CLOSED_AS_PACKET_GAP` means the repaired packet now faithfully records
that the source itself does not close the row.

| previous blocker | repaired evidence | Round 2 disposition |
|---|---|---|
| Eq. (2) omitted, including the identity-index normalization problem | `harper2605-one-qubit-depolarizing` plus `harper2605-gap-one-qubit-depolarizing`; Eq. (3) is separately recorded | `CLOSED_AS_PACKET_GAP` |
| non-Clifford \(T/U\) switch and missing Pauli coefficients omitted | `harper2605-nonclifford-pullthrough` plus `harper2605-gap-nonclifford-expansion` | `CLOSED_AS_PACKET_GAP` |
| Eq. (8) uppercase \(N\)/lowercase \(n\) ambiguity omitted | separate Fig. 2 \(n\) fact, Eq. (8) replay, and `harper2605-gap-truncation-size-symbol`; the \(\chi-1\) defect remains separately recorded | `CLOSED_AS_PACKET_GAP` |
| syndrome/correction-to-logical-angle bridge omitted | `harper2605-gap-logical-angle-bridge` and audit Secs. 3.1, 4, and 6 | `CLOSED_AS_PACKET_GAP` |
| GCAMPS identity and executable-provenance boundary omitted | `harper2605-gcamps-identity` plus `harper2605-gap-gcamps-provenance`; audit distinguishes named library from missing executable identity | `CLOSED_AS_PACKET_GAP` |
| Fig. 5 random-sign/PTA null omitted | `harper2605-random-sign-pta-agreement` and the contrary-result discussion in audit Secs. 3.6 and 4 | `CLOSED` |
| multi-page evidence records bundled behind one integer page | source circuit, threshold wording/results, same-twirl/null, coupling values, reset/measurement, and MPS/PEPS resource rows are split into single-page records | `CLOSED` |

Every semantic blocker listed in the prior FAIL report is closed. No new
load-bearing discrepancy was found in Round 2.

## 5. Single-page atomic-locator audit

The repaired note uses one positive integer `PDF page` for every evidence
record, and every used page is present in `visually_checked_pages`. The
load-bearing former bundles are now separated as follows:

| former bundle | repaired atomic records |
|---|---|
| repeated syndrome extraction and Fig. 1 circuit | p. 2 repeated-round fact; p. 3 circuit fact |
| abstract and detailed threshold wording | p. 1 abstract fact; p. 5 detailed result fact |
| same-twirl model and Fig. 5 null | p. 5 model/discussion fact; p. 6 caption fact |
| cross-page \(\theta\) values | p. 2 parameter-table fact; p. 3 coupling-product gap; p. 5 results-parameter fact |
| reset and measurement semantics | p. 2 reset gap; p. 4 selective-measurement gap |
| \(n\) and \(N\) notation | p. 4 lowercase-\(n\) fact; p. 5 uppercase-\(N\) gap |
| resource absence | p. 4 matched-MPS/optimizer gap; p. 7 matched-PEPS gap |

The complete-Record gap is anchored to the p. 2 repeated-outcome passage, the
place where a raw/Record construction would have to begin. Its broader absence
was confirmed by the full-source read. This is a source-local absence record,
not a claim that one paragraph explicitly enumerates the missing project schema.

## 6. Record-by-record reading-note decision

`PASS_AS_GAP` means that the source-local absence or defect is accurately
located and scoped.

| Fact ID | source check | decision |
|---|---|---|
| `harper2605-source-identity` | title/version/authors, p. 1; artifact extent independently verified | `PASS` |
| `harper2605-abstract-threshold-wording` | abstract closing wording, p. 1 | `PASS` |
| `harper2605-repeated-syndrome-extraction` | Sec. II repeated \(d\)-round description, p. 2 | `PASS` |
| `harper2605-syndrome-circuit` | Fig. 1 and caption, p. 3 | `PASS` |
| `harper2605-logical-error-observable` | Eq. (1) and following paragraph, p. 2 | `PASS` |
| `harper2605-error-rate-table` | Table I and Sec. III.A, p. 2 | `PASS` |
| `harper2605-one-qubit-depolarizing` | Eq. (2) and printed index sentence, p. 2 | `PASS` |
| `harper2605-two-qubit-depolarizing` | Eq. (3) and explicit \((I,I)\) exclusion, p. 2 | `PASS` |
| `harper2605-coherent-zz-channel` | Eqs. (4)–(5), circuit, and crosstalk location, p. 3 | `PASS` |
| `harper2605-pauli-twirl` | Eq. (6) and twirl discussion, p. 3 | `PASS` |
| `harper2605-pauli-decoder` | Sec. III.D PyMatching/PTA role, p. 3 | `PASS` |
| `harper2605-gcamps-identity` | Sec. IV opening names GCAMPS, p. 3 | `PASS` |
| `harper2605-hybrid-state` | Eq. (7), p. 4 | `PASS` |
| `harper2605-figure-qubit-symbol` | Fig. 2 caption's lowercase \(n\), p. 4 | `PASS` |
| `harper2605-clifford-update` | displayed \(G\) update, p. 4 | `PASS` |
| `harper2605-nonclifford-pullthrough` | printed \(T/U\) derivation and omitted coefficients, p. 4 | `PASS` |
| `harper2605-local-to-high-weight` | paragraph after the derivation, p. 4 | `PASS` |
| `harper2605-projective-measurement` | high-level measurement pull-through, p. 4 | `PASS` |
| `harper2605-qec-frame-interpretation` | source's ideal-frame interpretation, p. 4 | `PASS` |
| `harper2605-no-clifford-optimization` | Sec. IV.A closing optimizer discussion, p. 4 | `PASS` |
| `harper2605-mps-truncation` | Eq. (8) and truncation prose, p. 5 | `PASS` |
| `harper2605-truncation-bias` | Figs. 2–3 discussion and lower-bound wording, p. 5 | `PASS` |
| `harper2605-bond-cap` | \(\chi_{\max}=32\) sentence, p. 5 | `PASS` |
| `harper2605-results-coupling-parameters` | Sec. V.A values, p. 5 | `PASS` |
| `harper2605-coherent-twirled-result` | \(10^5\) samples and threshold prose, p. 5 | `PASS` |
| `harper2605-same-twirl-distributions` | Eq. (9) and associated discussion, p. 5 | `PASS` |
| `harper2605-random-sign-pta-agreement` | Fig. 5 caption, p. 6 | `PASS` |
| `harper2605-distance-nine-comparison` | Fig. 6 and caption, p. 6 | `PASS` |
| `harper2605-peps-future-work` | conclusion continuation, p. 7 | `PASS` |
| `harper2605-gap-zz-circuit-convention` | Eq. (4) versus printed circuit, p. 3 | `PASS_AS_GAP` |
| `harper2605-gap-coupling-product` | Eq. (5) and same-page hardware example, p. 3 | `PASS_AS_GAP` |
| `harper2605-gap-one-qubit-depolarizing` | Eq. (2) literal normalization, p. 2 | `PASS_AS_GAP` |
| `harper2605-gap-logical-angle-bridge` | Eq. (1) defining paragraph, p. 2 | `PASS_AS_GAP` |
| `harper2605-gap-gcamps-provenance` | Sec. IV opening identity without executable provenance, p. 3 | `PASS_AS_GAP` |
| `harper2605-gap-nonclifford-expansion` | \(T/U\) paragraph and derivation, p. 4 | `PASS_AS_GAP` |
| `harper2605-gap-schmidt-index` | Eq. (8)'s \(\chi-1\) upper limit, p. 5 | `PASS_AS_GAP` |
| `harper2605-gap-truncation-size-symbol` | undefined uppercase \(N\) bound, p. 5 | `PASS_AS_GAP` |
| `harper2605-gap-reset-transaction` | Table I/III.A reset parameter without instrument, p. 2 | `PASS_AS_GAP` |
| `harper2605-gap-measurement-instrument` | projective-measurement paragraph, p. 4 | `PASS_AS_GAP` |
| `harper2605-gap-complete-record` | repeated syndrome outcomes without Record construction, p. 2 | `PASS_AS_GAP` |
| `harper2605-gap-matched-mps-resources` | workload-specific optimizer passage without matched resources, p. 4 | `PASS_AS_GAP` |
| `harper2605-gap-peps-resources` | PEPS as future work without implementation/resources, p. 7 | `PASS_AS_GAP` |

All 42 evidence records pass source fidelity: 29 `paper_fact` and 13
`literature_gap` records. All nine relations resolve to existing
`paper_fact` records and do not widen the source claims.

## 7. Audit-packet decision

The repaired source-only audit was checked line by line against the pinned
source.

| audit area | Round 2 decision |
|---|---|
| pinned identity and scope | faithful |
| surface-code circuit and repeated rounds | faithful; correctly stops before a complete Record claim |
| Eq. (1) observable replay | faithful; missing logical-angle construction is explicit |
| Eqs. (2)–(6), ZZ circuit, and parameter anomalies | faithful; no silent repair |
| GCAMPS identity and \(C|\mathrm{MPS}\rangle\) update | faithful; executable provenance remains missing |
| \(T/U\) and missing coefficients | faithful |
| measurement/reset transaction boundary | faithful |
| optimizer and truncation claims | faithful and workload-scoped |
| Eq. (8), \(\chi-1\), and \(N/n\) | faithful |
| threshold and same-twirl results | faithful as source-reported statements |
| Fig. 5 PTA null | retained and used to limit a blanket anti-twirl inference |
| CAPEPS disconfirmation section | source facts are separated from the one labeled project inference |
| final source-only verdict table | agrees with the source and does not promote PEPS, Record, or resource claims |

No audit statement requires a semantic correction before admission.

## 8. Schema preflight

The current candidate was passed directly to the repository's
artifact-verifying `parse_note` path. It fails at exactly the intended
pre-admission gate:

```text
admission_status must be 'source_only_reviewed'
```

An isolated copy under `/tmp` was then changed only in two front-matter fields:

```toml
admission_status = "source_only_reviewed"
admission_reviewer = "codex-independent-source-rereview-harper-round2-2026-07-27"
```

Full artifact-verified parsing of that temporary copy passed all remaining
current checks, including note structure, source identity, source PDF hash,
audit path and hash, locator pages, checked-page membership, Fact-ID uniqueness,
and relation endpoints:

```text
PASS paper_facts=29 evidence_records=42 relations=9
checked_pages=(1, 2, 3, 4, 5, 6, 7)
```

The temporary diagnostic note hash was
`47fa7a9635b56ba912d7ec7890ef4f8695f057ebabadfb48a13f65108ddfecb3`;
it is not an admission hash and must not be placed in the manifest.

The read-only manifest drift check reported:

```text
candidates      280
audit-valid     38
in manifest     38
orphaned         0
stale            0
```

The Harper candidate is absent from the manifest, which is correct while its
front matter remains draft.

Schema preflight judgment:

- current candidate: `EXPECTED_FAIL_DRAFT_STATUS_ONLY`;
- hypothetical promoted metadata over the reviewed snapshots:
  `PASS_ALL_REMAINING_ARTIFACT_VERIFIED_SCHEMA_CHECKS`;
- semantic Round 2 gate: `PASS`;
- current-corpus admission now: `NO`, pending the standard promotion sequence.

## 9. Exact admission boundary and next sequence

This packet may support the narrow adjacent-work claim that GCAMPS was used as
a Clifford-frame/MPS-residual simulator for coherent crosstalk during repeated
rotated-surface-code syndrome extraction, together with the source-reported
workload results and limitations recorded in the note.

It may not support an executable logical-angle construction, complete
measurement/reset instrument, complete raw or detector/observable Record law,
state- or Record-faithfulness theorem, GCAMPS run reproduction, PEPS/CAPEPS
implementation, truncation guarantee, or matched efficiency/scaling claim.

The standard promotion sequence may now proceed:

1. update the source-only audit to record this Round 2 PASS and reviewer;
2. recompute the audit SHA-256 and place that exact hash in the note;
3. set the note's admission status and reviewer;
4. compute the final note SHA-256 and rerun direct artifact-verified validation;
5. add only that final validated identity to `CURRENT_CORPUS.toml`, then run the
   read-only drift check again.

Review read status: `complete`  
Review evidence status: `persisted`  
Fresh independent semantic decision: `PASS`  
Candidate current schema status: `EXPECTED_FAIL_DRAFT_STATUS_ONLY`  
Current-corpus admission at this snapshot: `NO`
