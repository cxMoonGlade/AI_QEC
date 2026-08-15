# Vanderstraeten et al. arXiv:2110.12726v2 — independent source rereview, Round 2

Date: 2026-07-27  
Reviewer: `/root/rereview_vanderstraeten`  
Stable review label: `codex-independent-source-rereview-vanderstraeten-round2-2026-07-27`  
Decision: **FAIL — all prior blockers are repaired, but one new source-notation blocker remains**

The repaired packet closes every defect named by the first independent review:
the two-row locator now stops at Eq. (43), the three-row record includes Sec.
IV.C Eqs. (44)--(48) and Appendix-B Eqs. (B1)--(B4), the finite-window record
starts at Sec. V Eq. (49) and identifies Eqs. (58)--(68) as the operative
construction, and the source's real-eigenvalue/incommensurate-correlation and
square-lattice limitations are now retained as atomic facts.

Admission nevertheless remains unsafe at the reviewed snapshot. The benchmark
fact calls the source's \(D=5\) a “physical bond dimension.” PDF page 2 explicitly
defines \(D\) as the bond dimension of the four **virtual** PEPS indices and
separately identifies the physical index. Because the note is an atomic RAG
evidence surface, its benchmark record must say “PEPS virtual bond dimension”
or simply “PEPS bond dimension,” not “physical bond dimension.” The companion
audit repeats related “physical bond \(D\)” wording and must be made consistent.

This review created only this Round-2 report. It did not edit or promote the
candidate reading note, source-only audit, pinned PDF, or
`docs/papers/CURRENT_CORPUS.toml`.

## 1. Independent protocol

The pinned PDF was traversed from the title page through Appendix B and the end
of the paper. Extracted text was used for navigation and completeness. PDF pages
1--12 and 14--18 were freshly rendered and visually inspected; page 13 contains
only bibliography entries and was read separately. The visual pass covered the
source identity and version stamp, tensor diagrams, Eqs. (1)--(69), the p. 8
transfer-gap footnote, Figs. 1--6, the p. 12 applicability discussion, Appendix-A
gradient construction, Appendix-B Eqs. (B1)--(B14), and Figs. 7--10.

The source-side interpretation was fixed before using the earlier FAIL report
as a repair checklist. The repaired candidate note and audit were then checked
record by record against the pinned source. No quarantined legacy note, RAG
result, knowledge graph, project synthesis, or old output verdict was treated
as evidence.

## 2. Reviewed immutable snapshots

| object | SHA-256 | disposition |
|---|---|---|
| pinned PDF, `docs/papers/2110.12726v2.pdf` | `58763a732ef1c5b660bacbc708a2134b1c8a09096eca1e44326c03a1b540a184` | valid `%PDF-1.5` byte stream; 1,620,330 bytes; unencrypted; 18 PDF pages |
| repaired candidate note, `docs/papers/reading_notes/vanderstraeten_variational_peps_contraction_2110.12726v2_source_review.md` | `7e1c5d643481c0287889b9e76b83b8828983482ba8bd2c501fb808bd2d009a38` | reviewed candidate snapshot; semantic FAIL below |
| repaired source-only audit, `docs/simulator_validation/VANDERSTRAETEN_2110_12726V2_SOURCE_ONLY_AUDIT_2026-07-27.md` | `c16d17fad8fa761fbb8307115fa51dc36c620db6d196661023b2bc7bd41978ea` | reviewed candidate snapshot; equals the note's stored audit hash |

The PDF shows the title *Variational methods for contracting projected
entangled-pair states*, the eight-author block, and the visible stamp
`arXiv:2110.12726v2 [cond-mat.str-el] 7 Jun 2022` on PDF page 1. The note's
source ID, pinned URI, source version, title, extent, and source hash agree with
that object.

## 3. Fresh source reconstruction

The paper studies approximate contraction of infinite PEPS. It distinguishes
the PEPS virtual bond dimension \(D\) from the environment bond dimension
\(\chi\), describes CTMRG and boundary-MPS environments, and identifies local
tensor conditions under which a row or multi-row transfer matrix is Hermitian.
For that subclass, the leading boundary MPS at fixed \(\chi\) admits a
variational norm/free-energy-density objective. The paper relates the one-row
stationarity equations to VUMPS, treats a special two-row construction, and
shows why a simultaneous free-energy characterization does not extend in the
same way to three or more rows.

For correlation functions, Sec. V converts the vertical correlation sum into
repeated transfer-matrix action on a finite-window MPS. Eqs. (58)--(61) define
the locally perturbed boundary state and the transfer resolvent; Eqs. (62)--(68)
define the finite window, its initial variational approximation, and each
subsequent normalized-fidelity compression. Window size and \(\chi\) remain
approximation controls, and the p. 8 footnote bounds the convergence discussion
by a transfer spectral gap.

The numerical section uses optimized, symmetry-constrained square-lattice
\(J_1\)-\(J_2\) infinite PEPS with **PEPS virtual bond dimension** \(D=5\) at
\(J_2=0\) and \(J_2=1/2\). Figure 1 shows monotone decrease of the displayed
norm/free-energy proxy \(f=-\log\lambda\) with \(\chi\); the source does not
transfer that monotonicity to physical energy, structure factor, state fidelity,
or a Record observable. Figure 4 is an empirical CTMRG/boundary-MPS comparison,
not an independently exact contraction. Figures 5--6 show the displayed
structure-factor behavior, while the text explicitly says the summed structure
factor is not variational.

Appendix B separates blocked single-row free-energy optimality from sequential
normalized-fidelity optimality. In the displayed three-row Ising example,
multi-site VUMPS becomes unstable near \(T_c\), whereas the normalized-fidelity
power method converges. The source reports that the instability-window size is
largely independent of \(\chi\) and shifts slightly toward lower temperatures
as \(\chi\) increases.

The Discussion supplies two explicit applicability limits. A Hermitian transfer
matrix has only real eigenvalues, so the authors expect states with dominant
incommensurate correlations, including critical states at incommensurate
filling, to be poorly represented by the subclass. The construction studied in
the paper is restricted to square-lattice PEPS; triangular, kagome, and more
complicated unit-cell settings are left for future work.

The source contains no finite-lattice syndrome circuit, Clifford frame,
GCAMPS/CAPEPS residual, selective measurement/reset instrument, Born branch or
prefix mass ledger, detector/observable Record fold, conditional fidelity,
Record total variation, or matched CAPEPS/full-PEPS resource benchmark.

## 4. Prior FAIL blocker closure

| prior blocker | repaired candidate evidence | Round-2 disposition |
|---|---|---|
| two-row record crossed into three-row Eq. (44) | `vander2110-two-row-construction` now cites Sec. IV.B, Eqs. (36)--(43), PDF pp. 5--6 | `CLOSED` |
| three-row record named Sec. IV.B and omitted the normalized-fidelity equations | `vander2110-three-row-breakdown` now cites Sec. IV.C, Eqs. (44)--(48), and Appendix B, Eqs. (B1)--(B4), PDF pp. 15--16 | `CLOSED` |
| finite-window record began with preceding-section Eqs. (47)--(48) | `vander2110-window-mps` and the audit now start at Sec. V Eq. (49), with Eqs. (58)--(68) identified as the perturbation/window operation | `CLOSED` |
| p. 12 real-eigenvalue/incommensurate limitation omitted | `vander2110-hermitian-incommensurate-limit` now retains the expected failure regime and distinguishes it from a proved no-go theorem | `CLOSED` |
| square-lattice and future-lattice/unit-cell scope not retained atomically | `vander2110-square-lattice-scope` now records square-lattice-only scope and the triangular/kagome/nontrivial-unit-cell future-work boundary | `CLOSED` |

The repaired audit's assigned-row table, operation replay, bounded project-use
statements, and kill conditions also preserve these corrections. There is no
remaining defect from the first FAIL report.

## 5. New blocking source-notation defect

Candidate record: `vander2110-benchmark-workload`  
Candidate note line at the reviewed snapshot: 168  
Source locator: PDF page 9, Sec. VI opening paragraph, read together with PDF
page 2, Sec. II first paragraph

Current claim:

```text
The reported contraction benchmarks use optimized, symmetry-constrained
infinite PEPS with physical bond dimension D=5 ...
```

The source states on PDF page 2 that the PEPS tensor has four contracted
**virtual** indices and one physical index, and that \(D\) is the bond dimension
of those four virtual indices. PDF page 9 then says the benchmark tensors have
bond dimension \(D=5\). Therefore “physical bond dimension \(D=5\)” is not a
source-faithful technical description. The earlier `vander2110-d-vs-chi` record
correctly calls \(D\) a PEPS virtual bond dimension, but that does not cure an
independently retrievable atomic benchmark record.

Required note repair:

```text
physical bond dimension D=5
```

must become either

```text
PEPS virtual bond dimension D=5
```

or the source's less specific

```text
PEPS bond dimension D=5
```

The companion audit should make the same distinction consistently. At minimum,
the \(D\)-versus-\(\chi\) discussion and operation replay at reviewed lines 48,
65, 93, 138, 155, and 172 should replace “physical [PEPS] bond \(D\)” with
“PEPS virtual bond \(D\)” or “PEPS bond \(D\).” This is a terminology repair,
not a change to the source's \(D=5\) benchmark result or the physical-state
versus contraction-environment distinction.

## 6. Record-by-record source decision

`PASS_AS_GAP` means the source-local absence is accurately scoped; it does not
close the corresponding field-wide literature question.

| Fact ID | source check | decision |
|---|---|---|
| `vander2110-source-identity` | title, authors, version stamp, and 18-page extent | `PASS` |
| `vander2110-selection-scope` | abstract and Introduction: approximate infinite-PEPS contraction, variational subclass, comparisons, and general-correlation scheme | `PASS` |
| `vander2110-d-vs-chi` | PDF pp. 1--2 distinguish PEPS virtual \(D\) from environment \(\chi\) | `PASS` |
| `vander2110-ctmrg-update` | PDF p. 2, Eqs. (5)--(7), absorption and truncation to \(\chi\) | `PASS` |
| `vander2110-boundary-mps` | PDF pp. 2--3, Eqs. (8)--(12), row-transfer MPO and boundary-MPS fixed points | `PASS` |
| `vander2110-finite-environment-ambiguity` | PDF p. 3 expressly leaves algorithm agreement, even at \(\chi\to\infty\), unclear | `PASS` |
| `vander2110-hermitian-transfer` | PDF pp. 3--4, Eqs. (13)--(20), local and larger-unit-cell Hermiticity conditions | `PASS` |
| `vander2110-hermitian-incommensurate-limit` | PDF p. 12 real-eigenvalue mechanism and expected incommensurate-correlation limitation | `PASS` |
| `vander2110-square-lattice-scope` | PDF p. 12 square-lattice-only scope and future lattice/unit-cell directions | `PASS` |
| `vander2110-variational-objective` | PDF p. 4, Eqs. (21)--(30), norm/free-energy-density objective at fixed \(\chi\) | `PASS` |
| `vander2110-vumps-equivalence` | PDF pp. 4--5, Eqs. (29)--(35), one-row zero-gradient/fixed-point correspondence | `PASS` |
| `vander2110-two-row-construction` | PDF pp. 5--6, Eqs. (36)--(43), two-row variational construction and coupled equations | `PASS` |
| `vander2110-three-row-breakdown` | PDF p. 6, Eqs. (44)--(48), and Appendix B, Eqs. (B1)--(B4) | `PASS` |
| `vander2110-window-mps` | PDF pp. 6--8, Eqs. (49)--(68), with operative finite-window steps in Eqs. (58)--(68) | `PASS` |
| `vander2110-finite-chi-gradient-caveat` | PDF p. 8 distinguishes fixed-\(\chi\) autodiff from infinite-\(\chi\) compatibility of approximate summation | `PASS` |
| `vander2110-benchmark-workload` | workload, model, symmetries, \(D=5\), and \(J_2\) values are right; “physical bond dimension” misidentifies virtual \(D\) | `FAIL_NOTATION` |
| `vander2110-monotone-free-energy` | PDF p. 9, Fig. 1, monotonicity only for displayed \(f=-\log\lambda\) | `PASS` |
| `vander2110-direct-vumps-runtime` | PDF pp. 9--10, Figs. 2--3, displayed wall-time behavior without complexity theorem | `PASS` |
| `vander2110-ctmrg-boundary-comparison` | PDF p. 10, Fig. 4, selected empirical energy comparison without independent exact reference | `PASS` |
| `vander2110-structure-factor-qualification` | PDF pp. 10--11, Figs. 5--6, nonvariational summed observable and small-\(\chi\) failure | `PASS` |
| `vander2110-multisite-instability` | Appendix B, Eqs. (B1)--(B14), Figs. 7--10, three-row Ising instability and power-method fallback | `PASS` |
| `vander2110-gap-generic-exactness` | arbitrary exact/certified contraction is absent | `PASS_AS_GAP` |
| `vander2110-gap-finite-chi-certificate` | no universal finite-\(\chi\) observable-error certificate | `PASS_AS_GAP` |
| `vander2110-gap-global-fidelity` | no approximate global-state fidelity/trace-distance result or circuit-update truncation analysis | `PASS_AS_GAP` |
| `vander2110-gap-finite-circuit` | no finite syndrome-circuit or full-PEPS circuit backend | `PASS_AS_GAP` |
| `vander2110-gap-instrument` | no selective measurement--reset--Record law | `PASS_AS_GAP` |
| `vander2110-gap-clifford` | no stabilizer tableau, Clifford frame, GCAMPS, or CAPEPS | `PASS_AS_GAP` |
| `vander2110-gap-matched-resources` | no matched CAPEPS/full-PEPS accuracy/runtime/memory comparison | `PASS_AS_GAP` |

Twenty-seven of 28 evidence records are source-faithful as written: 20 of 21
`paper_fact` records pass, all seven `literature_gap` records pass, and the one
failed `paper_fact` needs only the exact notation repair above.

## 7. Relation audit

All five relations resolve to existing `paper_fact` records, their labels occur
in the cited claims, and their semantics stay within the source:

| relation | Fact ID | decision |
|---|---|---|
| supports Hermitian-transfer variational contraction | `vander2110-variational-objective` | `PASS` |
| uses environment bond dimension \(\chi\) | `vander2110-d-vs-chi` | `PASS` |
| supports boundary-MPS/CTMRG comparison | `vander2110-ctmrg-boundary-comparison` | `PASS` |
| limits generic multi-site VUMPS convergence | `vander2110-multisite-instability` | `PASS` |
| limits the Hermitian subclass for dominant incommensurate correlations | `vander2110-hermitian-incommensurate-limit` | `PASS` |

The new notation blocker is not relation-linked, so relation resolution alone
cannot detect it.

## 8. Source-only audit decision

The audit faithfully reconstructs the method, the two-row/three-row boundary,
the finite-window replay, the finite-\(\chi\) caveat, displayed benchmark scope,
multi-site VUMPS disconfirmation, p. 12 applicability limits, and the complete
QEC/CAPEPS/Record absences. It does not claim generic exact contraction,
identify \(D\) with \(\chi\), promote the displayed \(\chi=500\) result to an
independently exact reference, or infer a CAPEPS resource advantage.

Its only admission blocker is the same \(D\)-terminology inconsistency. The
audit's notation ledger already correctly says “virtual bond dimension of the
PEPS tensor,” so replacing the neighboring “physical bond \(D\)” phrases with
that exact terminology is source-preserving and internally consistent.

## 9. Artifact-backed status-only parser preflight

The current on-disk candidate fails the repository's artifact-verifying
`parse_note` path at exactly the intended draft gate:

```text
admission_status must be 'source_only_reviewed'
```

A read-only in-memory simulation changed only

```toml
admission_status = "draft_pending_review"
```

to

```toml
admission_status = "source_only_reviewed"
```

and left the reviewed note path, PDF, audit, hashes, reviewer field, body, and
relations unchanged. Full artifact verification then passed every remaining
structural check:

```text
total=28 paper_fact=21 literature_gap=7 relations=5
checked_pages=1,2,3,4,5,6,7,8,9,10,11,12,14,15,16,17,18
```

The status-only diagnostic note SHA-256 was
`96c276219d0dd39ba01f2a0774eebf4b1b497e2b5e729b9d3f668571641cf04d`.
It is not an admissible note hash and must not be placed in the manifest.

The candidate source ID and path are absent from
`docs/papers/CURRENT_CORPUS.toml`, which is correct while semantic review fails
and the front matter remains draft. This parser result establishes structure
and artifact identity, not source-semantic correctness; in particular, it did
not detect the virtual/physical-index error.

## 10. Exact bounded decision and next sequence

The packet is not safe to admit at the reviewed hashes. The following sequence
is required:

1. repair `vander2110-benchmark-workload` to call \(D=5\) the PEPS virtual bond
   dimension or PEPS bond dimension;
2. make every audit reference to the PEPS \(D\) versus environment \(\chi\)
   distinction use the same virtual-bond terminology;
3. recompute the audit SHA-256 and update the note's stored audit hash;
4. obtain a fresh independent source-only spot rereview of the changed fact,
   the surrounding \(D/\chi\) records, and the complete changed audit;
5. only after a PASS, set the final reviewer/status, recompute the final note
   hash, rerun artifact-backed validation, and add exactly that identity to
   `CURRENT_CORPUS.toml`.

No further scientific expansion is required by this review. The repaired
packet may eventually support only the bounded infinite-PEPS contraction,
Hermitian-subclass, finite-window, benchmark, and explicit limitation facts
enumerated above. It still cannot support a CAPEPS algorithm, QEC instrument,
Record correctness result, generic finite-\(\chi\) certificate, or matched
resource advantage.

Review read status: `complete`  
Review evidence status: `persisted`  
Prior FAIL blockers: `all_closed`  
Fresh independent semantic decision: `FAIL_ONE_NEW_NOTATION_BLOCKER`  
Candidate current schema status: `EXPECTED_FAIL_DRAFT_STATUS_ONLY`  
Current-corpus admission at this snapshot: `NO`
