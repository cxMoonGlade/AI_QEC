# Independent source-only review — Nakhl et al., arXiv:2411.12482v2

Date: 2026-07-27

Reviewer role: independent source-only admission reviewer

Review result: **FAIL**

Admission decision: **BLOCKED at the exact reviewed bytes**

This report reviews the primary PDF and the two named companion artifacts. It
does not revise, admit, or hash-update the reading note, audit packet, or
`CURRENT_CORPUS.toml`.

## Exact reviewed objects

| object | size | SHA-256 |
|---|---:|---|
| `docs/papers/2411.12482v2.pdf` | 655811 bytes | `86de97a1ac18ac9c98272e5180e222115c0590d5cd0759a1eb7fd829ab81eaee` |
| `docs/papers/reading_notes/nakhl_mast_magic_state_injection_stn_2411.12482v2_source_review.md` | 17836 bytes | `38cf74639359d76a4b76832fa324e831aad23e7eb461e195121b4318b8cefd79` |
| `docs/simulator_validation/NAKHL_HARPER_MAST_2411_12482V2_SOURCE_ONLY_AUDIT_2026-07-27.md` | 22067 bytes | `5db0b9d8eec2ce4d08d05effb6f9085f2f3d1a480f6142b6bedfb346a8a05deb` |

The note's `source_sha256` and `audit_packet_sha256` match these exact bytes.
The PDF begins with `%PDF-1.5`, ends in `%%EOF`, is unencrypted, and has 12
pages.

## Review method and visual verification

The complete 12-page PDF was read in page order. Text extraction was used only
for traversal. The following source pages were rendered and visually inspected
at equation/figure fidelity:

| PDF page | visually checked content |
|---:|---|
| 1 | title/version/date, abstract, Eq. (1), destabilizer-tableau wording |
| 2 | Fig. 1 injection gadget, deferred-projection prose, random ensemble definition |
| 3 | Fig. 2 axes/legend/caption, three regions, sampling-complexity paragraph |
| 4 | Fig. 3, projection-order result, CAMPS comparison, conclusion wording |
| 5 | Data Availability implementation pointer |
| 7 | Eqs. (A1)--(A2), (B1)--(B3), binary-index and generator definitions |
| 8 | Eqs. (B4)--(B11), expectation and selective-projection rules |
| 9 | Eqs. (C1)--(C2), Fig. 4, the \(k<N\)/\(k\ge N\) case split |
| 10 | Fig. 5, Appendix C.2, Eq. (C3), Appendices D--E opening |
| 11 | Figs. 6--7 and the four-\(T\)/seven-\(T\) decomposition statements |
| 12 | Fig. 8 plots, legend, hardware/shot statement, and caption defect |

Page 6 contains references, was read as part of the complete source traversal,
and contains no load-bearing equation or result used by the note other than
the continuation of Ref. [54].

## Gate checklist

| gate | result | independent finding |
|---|---|---|
| Versioned object, PDF signature, page count, and hashes fixed | PASS | The object is the 12-page arXiv v2 artifact identified above. |
| Full-text traversal | PASS | All pages, appendices, captions, Data Availability, and references were read. |
| Load-bearing math and figures visually verified | PASS | Eqs. (1), (A1)--(A2), (B1)--(B11), (C1)--(C3), and Figs. 1--8 were checked against rendered pages. |
| Required evidence-record shape | PASS | The note has 17 `paper_fact` and 11 `literature_gap` records; required leading fields, unique Fact IDs, and `Gap scope: source_local` are present. |
| Core formula transcription | PASS | The note accurately transcribes the intended coefficient-MPS representation, the B3--B9 update chain, the physical projector, and the printed B10/B11/C1/C2/C3 defects it names. |
| Fact atomicity | FAIL | One record combines independently locatable projection-order and decomposition-dependence claims; other body claims outrun their named locator. |
| Exact locator coverage | FAIL | At least the random-complexity and selection-scope record bodies use evidence outside their declared locators. |
| Notation/type/range ledger | FAIL | Several load-bearing symbols and a material scope change of \(N\) are absent; \(S,D\) are typed too loosely. |
| Complexity qualification | PASS | The note/audit preserve the ensemble-average \(t\lesssim N\) boundary, distinguish it from a worst-case theorem, and retain the general-sampling limitation. |
| Printed-anomaly coverage | FAIL | Two source inconsistencies relevant to the scaling argument are not recorded. |
| Source facts versus project application separated | PASS | Project mapping is kept in the audit packet rather than asserted as a Nakhl-paper fact. |
| CAPEPS current boundary | FAIL | The project mapping calls CAPEPS proposed and omits the current implemented raw-branch/reset boundary and its exact non-Record limitations. |
| Relation structural validity | PASS | Every edge points to an existing `paper_fact`, and every `object_label` occurs in the referenced Claim. |
| Relation semantic validity | FAIL | Three relation identities/types encode a different or misleading concept from the source claim. |
| Operation replay | FAIL | The Hidden Bit Shift numerical curves are labeled replayable despite missing seeds, complete workload specification, raw data, and pinned code. |
| Current corpus preflight | PASS | The artifact-verified corpus audit excludes this note for `admission_status must be 'source_only_reviewed'`; it is not currently admitted. |

## Admission blockers

### B1 — The printed-anomaly ledger is incomplete

The note and audit correctly preserve the following visible defects:

- \(1,\ldots,2^N\) versus an \(N\)-bit decimal label;
- Eq. (B2)'s stabilizer-row wording for the intended destabilizer basis;
- Eq. (B10)'s \(c_i\) and undefined \(\hat i\cdot\hat b\) label operation;
- Eq. (B11)'s undefined \(\hat n\);
- the C1--C2 prefactor mismatch;
- the inconsistent \(\mathrm{Sp}(2n,\mathbb F_2)\),
  \(\mathbb F_2^n\), and \(\mathrm{Sp}(n;\mathbb F_2)\) dimensions around
  Eq. (C3); and
- Fig. 8's erroneous second “4 \(T\)” caption phrase.

Two further visible inconsistencies are load-bearing and absent:

1. **Conclusion swaps MAST and STN.** PDF page 4 says the \(N=200\) result has
   “bounded STN bond dimension.” That conflicts with the abstract, Fig. 2, its
   caption, and the surrounding conclusion: the bounded Region-A curve is
   MAST, whereas STN grows exponentially. The audit silently uses the intended
   MAST reading but does not preserve the printed contradiction.
2. **The Appendix-C boundary changes at \(k=N\).** PDF page 9 first partitions
   the argument into \(k<N\) and \(k\ge N\), then calls the second case
   \(k>N\). The next subsection indexes magic observables by
   \(N\le i<N+t\). Together with the source's unresolved zero/one-based label
   convention, the literal status of \(k=N\) is unspecified. This affects the
   exact case split used in the cost argument and must not be silently repaired.

Until both are recorded with exact locators and their intended readings are
explicitly separated from the printed text, `read_status: complete` is not
independently supportable.

### B2 — The load-bearing notation ledger is incomplete and partly conflated

The audit ledger does not close the domains, ranges, overloads, or fixed/variable
status required to replay the paper's algebra. Missing entries include
\(\hat d_i,\hat s_i,\hat a,\hat b\), \(j\), \(k\), \(\hat n\),
\(I_X,I_Y,I_Z\), \(\mathcal R\), \(\theta\), and the allowed phase role of
\(\alpha\). Several are precisely where the printed anomalies occur.

The entry for \(S,D\) calls them “binary Pauli tableau rows,” but the source
uses \(S,D\) for stabilizer/destabilizer structures and uses hatted binary
vectors to select products of their rows. Those are not one type.

The ledger also does not preserve the scope change of \(N\): in the benchmark
plots \(N\) is the data-qubit count and MAST ancillas are excluded, while the
generic Appendix-A/B coefficient-MPS formulas use \(N\) for the represented
qubit count, and Appendix C then introduces a data-plus-magic register. That
overload is material to the \(k=N\) boundary and the \(2^{N/2}\) statements.

### B3 — The operation replay overstates what can be reconstructed from the PDF

The Hidden Bit Shift replay row outputs “maximum-bond and selected runtime
curves” and labels the operation
`replayable_from_reported_benchmark_definition`, while its own final clause
says raw data are unavailable beyond the figures. The PDF gives the circuit
family, qualitative scaling of \(O_g\), decomposition choices, hardware, and
shot count, but does not give all random instances/seeds, complete software
defaults, raw observations, or a pinned implementation commit.

The figures can be read and the qualitative comparison can be audited; the
reported numerical curves cannot be replayed from this artifact alone. This
row must be marked quantitatively non-replayable, or split into a replayable
circuit/decomposition row and a non-replayable numerical-output row.

The two-term B3--B9 row is appropriately conditional on the intended
destabilizer reading, but the global `operation_replay_status = "complete"`
must mean “the replay audit was completed,” not “every printed operation is
implementation-replayable.” The audit should state that distinction directly.

### B4 — Fact atomicity and locator coverage do not fully satisfy the source-note contract

`mast2411-path-dependence` combines:

- non-minimal cost and projection-order dependence from the final
  random-circuit paragraph on PDF page 4; and
- decomposition-dependent resources from the Conclusion on page 4 and the
  concrete decomposition benchmark on pages 10--12.

These are separately locatable claims and should not share one evidence
record.

Two record bodies also extend beyond their named source locator:

- `mast2411-random-complexity` names pages 1--2, but its explanatory body
  invokes the first anticommuting tableau row, whose actual derivation is in
  Appendix C on pages 9--10.
- `mast2411-selection-scope` names the abstract/introduction on page 1, but its
  body adds the partial Hidden Bit Shift runtime result from Fig. 8 on page 12.

The Claim lines are broadly faithful, but the evidence record includes the
body. Locators must cover all load-bearing prose in the record or the prose
must be moved/split.

### B5 — The CAPEPS project application is stale and incomplete

The source/audit separation is structurally correct: the Nakhl note does not
claim that MAST is CAPEPS. The substantive project mapping is not current,
however. It describes a “proposed CAPEPS route,” while the current authority
registers `carrier/capeps` as an implemented **RESEARCH engineering-mechanics
prototype** with invariant

\[
\lvert\psi\rangle=C\lvert\phi\rangle.
\]

The current prototype already has untruncated dense/Quimb residual mechanics,
coherent signed-Pauli pullback, ordered raw conditional branch log mass, and
computational-\(Z\) measure-reset. Its explicit boundary is equally important:
the branch ledger is not `RecordBatch`; there is no complete multi-round
detector/observable Record, leakage/qutrit semantics, controlled finite-bond
truncation, scaling result, or production-faithfulness claim. CAPEPS-specific
literature closure and preregistration remain open.

The audit's future-facing sentence about processing a temporal
measurement--reset schedule is not false, but without the current implemented
raw-branch boundary it can be read as saying CAPEPS has no measurement/reset
mechanics at all. The project application must name the current owner and
separate implemented raw branches from the still-open canonical Record law.
No MAST result may be used to inherit CAPEPS Record, PEPS, or efficiency
authority.

### B6 — Competing-source assertions lack an auditable source binding

The audit asserts that:

- the Masot-Llima/Garcia-Saez PRL is the cleaner source for the representation
  and outcome-resolved Pauli measurement; and
- arXiv:2605.29514v1 establishes later GCAMPS
  \(C\lvert\mathrm{MPS}\rangle\) surface-code work.

Neither assertion is established by the Nakhl PDF. In a competing-evidence
section these may be useful routing statements, but they need a versioned
artifact/hash and exact equation/section locator, or must be explicitly marked
as unverified routing outside this packet. A title/citation alone cannot close
a source row.

### B7 — The relation table passes syntax but not semantic admission review

The object labels are source-local and pass the validator's containment rule,
but these triples are misleading:

1. `mast-random-t-doped-clifford-regime` is typed as `method` while its label is
   the finding “polynomial MAST cost.” The edge should point to a source
   concept/theorem-like scaling claim, not type a cost result as a method.
2. `mast-projection-order-independence` names independence even though the
   cited Claim establishes projection-order **dependence**. The object ID is
   semantically inverted.
3. `mast-camps-equivalence` plus predicate `limits` and label “CAMPS protocol”
   does not encode what the Claim says. The source distinguishes the methods
   and attributes an optimization subroutine to CAMPS; it does not state a
   generic `limits(CAMPS protocol)` relation or establish an equivalence object.

These edges would introduce incorrect graph semantics even though their
labels occur literally in the Claims. They must be repaired or removed before
corpus admission.

## Source-faithfulness findings that pass

Subject to the blockers above, the following high-value parts of the note and
audit are faithful to this PDF:

- MAST is an injection augmentation of the STN
  destabilizer-basis coefficient-MPS representation, not a
  \(C\lvert\mathrm{MPS}\rangle\) or \(C\lvert\mathrm{PEPS}\rangle\)
  factorization.
- Clifford operations update the tableau basis and leave the coefficient MPS
  unchanged in the source's formalism.
- Eqs. (B3)--(B9) describe the source's Pauli/tableau decomposition and
  two-term coefficient-MPS rotation, with the literal-basis caveat retained.
- Appendix B.4 states the selected physical projector
  \((I+pO)/2\), tableau update, and MPS renormalization, but does not provide a
  complete Born-history/reset/Record instrument.
- For the source-defined uniformly random Clifford-plus-one-\(T\)-per-layer
  ensemble, the paper claims average polynomial MAST cost for
  \(t\lesssim N\); this is not presented by the note as an arbitrary-circuit
  worst-case theorem.
- Fig. 2 reports 1000-instance average maximum coefficient-MPS bond, with the
  three stated regions and the \(N=200\), \(N+10\)-layer stop.
- The source explicitly denies efficient general probability-distribution
  sampling and states \(O(\exp(w))\) dependence for MAST when \(t<N\).
- The Hidden Bit Shift figures support the reported 4000-qubit/320-\(T\)
  headline and the direction of the fixed-resource bond comparison.
- Figs. 6--8 distinguish the four-\(T\), ancilla-using and seven-\(T\),
  no-extra-ancilla decompositions; the audit correctly uses the legend and
  Appendix E rather than Fig. 8's defective caption phrase.
- The source contains no PEPS residual, XZZX syndrome-extraction benchmark,
  complete ordered outcome law, detector/observable fold, or matched
  full-PEPS efficiency study.

## Final verdict

- `read_status` of this independent review: `complete`
- `evidence_status` of this report: `persisted`
- source note semantic admission: `FAIL`
- audit packet semantic admission: `FAIL`
- relation admission: `FAIL`
- CAPEPS authority transfer from this source: `prohibited`
- `CURRENT_CORPUS.toml` action authorized by this review: `none`

The reviewed note is a strong draft and captures most of the source's central
mechanics and visible formula defects. It is not independently
`source_only_reviewed` until blockers B1--B7 are repaired and a fresh reviewer
checks the repaired bytes and hashes.
