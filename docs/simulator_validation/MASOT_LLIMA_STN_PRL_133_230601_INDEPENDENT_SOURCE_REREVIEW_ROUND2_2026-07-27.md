# Independent source-only rereview, round 2 — Masot-Llima and Garcia-Saez, PRL 133, 230601

Date: 2026-07-27

Reviewer: `codex-independent-source-rereview-stn-vor-round2-2026-07-27`

Verdict: **PASS — the repaired source-only packet is semantically admissible**

Current-corpus admission: **NO — the reviewed note remains an intentionally
excluded draft until the separate metadata, hash, parser, and manifest
promotion is performed**

This rereview did not modify the reading note, source-only audit, source
artifacts, or `docs/papers/CURRENT_CORPUS.toml`.

## Reviewed byte identities

| object | SHA-256 |
|---|---|
| APS version-of-record article, `docs/papers/PhysRevLett.133.230601_version_of_record.pdf` | `7630570f2d8281ac29a99075082c7e992f8f68aa9d05bd13cf190c473f08946c` |
| official APS supplement, `docs/papers/PhysRevLett.133.230601_supplement_version_of_record.pdf` | `5d9dcbd7746b79c38678a72fb42f6b4a529ea4678de2b873b0ee85fbc276b2d1` |
| repaired reading note, `docs/papers/reading_notes/masot_llima_stabilizer_tensor_networks_prl_133_230601_source_review.md` | `35e20d69035e8d3191871a61338d931ea377ddb1a97cfea117d1838ccb6bda83` |
| repaired source-only audit, `docs/simulator_validation/MASOT_LLIMA_STABILIZER_TENSOR_NETWORKS_PRL_133_230601_SOURCE_ONLY_AUDIT_2026-07-27.md` | `484e70309eb2e7ca574ff3567799d24617475514ff73554506f03e5f62c6fd20` |
| first independent review, `docs/simulator_validation/MASOT_LLIMA_STN_PRL_133_230601_INDEPENDENT_SOURCE_REVIEW_2026-07-27.md` | `e2631163e858a1c5e82e355de13c76b01ffef89cfe4f28e4715644fa1b0c9546` |

The reading note's stored audit hash equals the repaired audit's actual hash.
Its stored article hash equals the pinned article's actual hash. The audit
binds the official supplement separately by its actual hash.

## Independent source pass

The six-page published article and eleven-page official supplement were
reopened from the pinned artifacts and read in full before the repaired note
and audit were graded. Load-bearing article pages 1--4 and supplement pages
1--10 were freshly rendered and visually inspected. In particular, the
formula and prose checks used the rendered source for:

- article Eq. (2), Eqs. (3)--(9), the measurement-bond warning, Fig. 2, and
  the conclusions;
- supplemental Lemmas 1--3 and Eqs. (7)--(35);
- supplemental Eqs. (40)--(42) and their Schmidt-decomposition prose; and
- the supplement page-10 software-implementation limitation.

No quarantined legacy reading note, old project synthesis, RAG result, or
knowledge-graph result was opened or used as evidence. The audit's
legacy-disconfirmation section was not used to grade admission. The repaired
packet was opened only after the independent source pass.

The article title, DOI, publication data, and authors agree with the pinned
article object. The supplement page-1 title and authors agree with that
article, so the companion-source identity is closed.

## Round-1 blocker closure

| round-1 blocker | round-2 source check | status |
|---|---|---|
| source-identity locator did not establish the companion supplement | `stn-vor-source-identity` now names both the article title/DOI block and the matching official supplement title/author block; the audit binds both PDF hashes | `closed` |
| two-term basis-update claim lacked the load-bearing supplemental locator | `stn-vor-two-term-nonclifford` now cites Supplemental Sec. I.B, Lemma 2 and Eqs. (7)--(16), PDF pp. 2--3, in addition to article Eqs. (5)--(6) | `closed` |
| multi-term statement was overpromoted as implemented software | the note and audit now admit only the formal factorization in supplemental Eqs. (17)--(19); supplement PDF p. 10 explicitly leaves software implementation of arbitrary decompositions to future work | `closed` |
| measurement replay collapsed the \(\hat n\ne0\) and \(\hat n=0\) domains | the note and audit now give the \(k\), basis-update, and \(P_k\widetilde R\) path only for \(\hat n\ne0\), while Eq. (27)'s fixed-basis diagonal projection is used for \(\hat n=0\) | `closed` |
| Lemma 3's undefined zero-domain \(k/P_k\) and invalid Eq. (34) rejoining were omitted | `stn-vor-gap-measurement-zero-domain` now records that \(k\) and \(P_k\) are undefined at \(\hat n=0\), that the \(\hat i_k\equiv0\) convention does not define a physical coefficient qubit, and that it contradicts the bit-flip equivalence used in Eq. (34) | `closed` |
| the correct Born norm was not separated from the defective uniform coefficient proof | the physical norm is retained only through the Hermitian-Pauli projector identity; the uniform Lemma 3 coefficient proof is expressly rejected | `closed` |

The published article's brief statement that a more-term generalization was
implemented cannot carry an arbitrary-decomposition software claim. The
official supplement's implementation section limits the reported Python path
to circuits decomposed into \(\{\mathrm{CNOT},R_X,R_Y,R_Z\}\) and explicitly
reserves arbitrary decompositions for future work. The repaired packet uses
the narrower, source-safe formal-factorization claim.

## Measurement replay and proof audit

For
\[
O=\alpha\delta_{\hat n}\sigma_{\hat m},
\]
the source supports
\[
\langle O\rangle
=\alpha\langle\nu|X_{\hat n}Z_{\hat m}|\nu\rangle,\qquad
p_\pm=\frac{1\pm\langle O\rangle}{2}.
\]

The two coefficient-update domains must remain separate:

1. If \(\hat n\ne0\), the source can choose the first nonzero bit \(k\),
   update the stabilizer basis, define \(P_k\), and apply
   \(P_k\widetilde R\).
2. If \(\hat n=0\), no such \(k\) exists. Supplemental Eq. (27) instead keeps
   the basis fixed and directly applies
   \((I\pm\alpha Z_{\hat m})/2\) to the coefficient state.

The repaired packet makes that split explicit. It also keeps both independent
defects in the printed uniform proof:

- \(k\) and \(P_k\) are undefined for \(\hat n=0\), and the later
  \(\hat i_k\equiv0\) convention neither constructs \(P_k\) nor satisfies
  Eq. (34)'s bit-flip equivalence when \(\hat n=0\);
- a separate intermediate line in Eq. (34) inserts the already-global
  \(\langle\psi|O|\psi\rangle\) into a remaining coefficient sum without the
  factors needed for that equality.

Neither defect changes the physical Born result, because for normalized
\(|\psi\rangle\) and Hermitian Pauli \(O\),
\[
\left\|\frac{I\pm O}{2}|\psi\rangle\right\|^2
=\left\langle\psi\left|\frac{I\pm O}{2}\right|\psi\right\rangle
=\frac{1\pm\langle O\rangle}{2}.
\]
The note and audit now use this projector identity, not the flawed uniform
coefficient derivation, as the accepted justification.

## Other anomaly and absence checks

All other source-local anomalies and scope limits remain correctly stated:

- article Eq. (2) prints the inclusive upper limit \(2^n\), while the stated
  basis cardinality and Supplemental Lemma 1 require labels
  \(0,\ldots,2^n-1\);
- supplemental Eq. (42)'s displayed expansion has at most \(k\chi\) product
  terms and therefore proves a Schmidt-rank upper bound, but operator-basis
  orthogonality does not make the displayed state vectors a Schmidt
  decomposition in general;
- the source explicitly permits measurements to increase coefficient-state
  correlations and bond dimension, so no monotone-shrink claim is admitted;
- the concrete coefficient backend is an MPS; no PEPS residual is
  implemented;
- the source mentions QEC and gives a toric-code locality example, but it
  supplies no syndrome-extraction implementation or QEC benchmark;
- reset, ordered raw-history and prefix masses, a repeated-round Record law,
  detector/observable folds, and a Record-law fidelity metric are absent;
- no qutrit/general-qudit or leakage-capable tableau, measurement, and reset
  backend is supplied; and
- the source gives analytical rank/route bounds and qualitative efficiency
  discussion, so the retained absence is narrowly a lack of a matched-accuracy
  runtime or peak-memory comparison against full-TN, PEPS-residual, and
  Pauli-twirled alternatives.

The repaired note contains 22 source-located evidence records:

- 14 `paper_fact` records; and
- 8 `literature_gap` records.

The eighth gap is the newly explicit Lemma 3 zero-domain defect. None of the
retained gaps is used to turn an absence into a positive scientific result.

## Structural preflight

Running the artifact-verifying parser on the actual reading-note bytes
produced the expected exclusion:

```text
admission_status must be 'source_only_reviewed'
```

A no-write diagnostic replaced only

```text
admission_status = "draft_pending_review"
```

with

```text
admission_status = "source_only_reviewed"
```

in memory. The artifact-verifying parser then passed every remaining schema,
section, checked-page, source-hash, and audit-hash gate:

```text
total=22 paper_fact=14 literature_gap=8
```

The diagnostic in-memory note SHA-256 was
`6df0ec7ea3ea69accf9e3147e93a94e26d6cc10033e8526e1b19b30e1ae84570`.
That value is diagnostic only: it intentionally retained the pending reviewer
field and is not an identity that may be inserted into the corpus manifest.

The actual note still contains:

```text
admission_status = "draft_pending_review"
admission_reviewer = "pending_independent_source_only_review"
```

No entry matching the note slug, DOI, or source hash is present in
`docs/papers/CURRENT_CORPUS.toml`. That exclusion is correct at this stage.

## Exact admissible claim boundary

At the reviewed source, note, and audit hashes, the packet may support only:

1. a tableau-defined stabilizer basis with a coefficient state represented
   concretely by an MPS;
2. Clifford conjugation of the basis with unchanged coefficients;
3. the source's two-term pulled-back Pauli-axis rotation and the published
   formal multi-term factorization;
4. one selective Pauli-measurement primitive with the \(\hat n\ne0\) and
   \(\hat n=0\) coefficient updates kept separate;
5. Born probabilities and the physical branch norm from the direct projector
   identity;
6. the source's warning that measurement may increase coefficient bond
   dimension; and
7. the \(k\chi\), \(4\chi\), and \(16\chi\) rank/routing upper bounds, without
   accepting the stronger printed Schmidt-decomposition wording.

This PASS does not authorize claims of:

- an implemented arbitrary-decomposition software path;
- a Clifford-frame plus PEPS-residual simulator;
- reset correctness or a complete multi-round Record law;
- monotone coefficient-bond reduction under measurement;
- a qutrit or leakage-capable backend;
- a syndrome-extraction or QEC benchmark; or
- a matched runtime, peak-memory, or accuracy advantage over full tensor
  networks, PEPS residuals, or Pauli-twirled methods.

## Promotion boundary

This report authorizes a later mechanical promotion only if the reviewed
source artifacts, note body, and audit bytes remain scientifically unchanged.
That promotion must:

1. set `admission_status = "source_only_reviewed"`;
2. replace the pending reviewer with
   `codex-independent-source-rereview-stn-vor-round2-2026-07-27`;
3. recompute the resulting reading-note SHA-256;
4. rerun artifact-verified parsing on the actual promoted bytes; and
5. add exactly that validated identity to `docs/papers/CURRENT_CORPUS.toml`.

Any source, audit, locator, claim, replay, anomaly, or gap change falls outside
this PASS and requires a fresh independent source review.

Final status:

- `read_status: complete`
- `evidence_status: persisted`
- `independent_source_rereview_round2: pass`
- `semantic_packet_admissibility: pass`
- `structural_promotion_preflight: pass`
- `current_corpus_admission: no`

