# Vanderstraeten et al. arXiv:2110.12726v2 — independent source rereview, Round 3

Date: 2026-07-27  
Reviewer: `/root/vander_round3_review`  
Stable review label: `codex-independent-source-rereview-vanderstraeten-round3-2026-07-27`  
Decision: **FAIL — the Round-2 physical/virtual-bond error is repaired, but three audit-packet blockers remain**

The source-only note now correctly calls the benchmark value \(D=5\) the
**PEPS virtual bond dimension**, and neither the note nor the audit contains
the prohibited phrase “physical bond dimension” or an equivalent
physical-bond description of \(D\). The three locator repairs and the two
explicit applicability limitations required by the first review also remain
closed.

Admission is nevertheless unsafe at the exact snapshots below. One audit
closure row leaves its independently readable \(D=5\) occurrence unqualified
instead of naming it as the PEPS virtual bond dimension. More importantly, the
audit notation ledger conflates the general left/right boundary tensors
\(M,\widetilde M\) with the Hermitian variational ket/bra pair
\(M,\bar M\), and it does not preserve the source's overloaded \(N/L\)
window notation. These are source-notation defects in a packet that declares
its operation replay complete; they are not project-policy preferences.

This review created only this Round-3 report. It did not modify the candidate
note, source-only audit, pinned PDF, either earlier review, or
`docs/papers/CURRENT_CORPUS.toml`.

## 1. Exact reviewed inputs

### Primary admission inputs

| object | bytes | SHA-256 |
|---|---:|---|
| pinned PDF, `docs/papers/2110.12726v2.pdf` | 1,620,330 | `58763a732ef1c5b660bacbc708a2134b1c8a09096eca1e44326c03a1b540a184` |
| candidate note, `docs/papers/reading_notes/vanderstraeten_variational_peps_contraction_2110.12726v2_source_review.md` | 14,193 | `9573f307893f70d0833342f4b0b7b7ef556db793148d35e8c49309518bd80bc6` |
| source-only audit, `docs/simulator_validation/VANDERSTRAETEN_2110_12726V2_SOURCE_ONLY_AUDIT_2026-07-27.md` | 13,248 | `d33603d6d00baafe90113d1e3969918ba77fd87d3c3ab45a062de1ab15b06af0` |

The note's stored source hash and audit-packet hash exactly equal the reviewed
PDF and audit hashes.

### Prior-review checklists, not source evidence

| object | SHA-256 |
|---|---|
| first independent review, `docs/simulator_validation/VANDERSTRAETEN_2110_12726V2_INDEPENDENT_SOURCE_REVIEW_2026-07-27.md` | `56e2d675ff98a692d99332c300c8d7471c75585c3fad866f05fe12463715b730` |
| Round-2 rereview, `docs/simulator_validation/VANDERSTRAETEN_2110_12726V2_INDEPENDENT_SOURCE_REREVIEW_ROUND2_2026-07-27.md` | `9fba9ddeeba7aa67e0c712fae48ac093e3eb93c2eca6365c4756b50ca38828c2` |

The prior reports were used only after the fresh source reconstruction, as
repair checklists. They were not used to settle source meaning.

## 2. Independent full-source protocol

The pinned object has a valid `%PDF-1.5` signature, is unencrypted, and
contains 18 PDF pages. A temporary run of the repository's
`deep-read-paper` acquisition/extraction helper independently returned the
same PDF hash, 18 pages, and 67,385 navigable text characters. The title page
shows the title, the eight-author block, and the visible stamp
`arXiv:2110.12726v2 [cond-mat.str-el] 7 Jun 2022`.

All 18 pages were read in source order, including the complete bibliography,
Appendix A, Appendix B, and the terminal figure captions. Text extraction was
used only for traversal and completeness.

All 18 pages were freshly rendered at 160 DPI. The load-bearing pages
visually inspected at symbol, equation-label, diagram, axis, caption, and
paragraph level were PDF pages 1--12 and 14--18. PDF page 13 is bibliography
only and was read in the full-text traversal. The visual pass covered:

- the title/version/abstract and the introductory \(D/\chi\) distinction;
- the five-leg PEPS tensor and virtual-versus-physical-index statement on
  PDF page 2;
- Eqs. (1)--(69), including every section boundary used by a candidate
  locator;
- Figs. 1--6 and their axes/captions;
- the transfer-gap footnote on PDF page 8;
- the real-eigenvalue/incommensurate-correlation and square-lattice
  limitations on PDF page 12;
- Appendix-A Eqs. (A1)--(A15);
- Appendix-B Eqs. (B1)--(B14); and
- Figs. 7--10 and the associated stability-window text.

No RAG result, knowledge graph, old output verdict, project synthesis, or
secondary summary was treated as evidence.

## 3. Fresh source reconstruction

The paper studies approximate contraction of infinite PEPS. It separates the
PEPS virtual bond dimension \(D\), which is the dimension of each of the four
virtual tensor legs, from the environment bond dimension \(\chi\) used by
CTMRG or boundary-MPS contraction. The tensor's fifth leg is the physical
index; the source never calls \(D\) a physical bond dimension.

For PEPS whose relevant transfer matrix is Hermitian under the stated local
tensor or larger-unit-cell conditions, the leading boundary MPS at fixed
\(\chi\) admits a variational norm/free-energy-density characterization.
The one-row stationarity equations correspond to the VUMPS fixed-point
equations. The stated two-row construction retains a real variational
formulation. For three or more rows, the simultaneous free-energy
interpretation can break down, while sequential normalized-fidelity
optimization remains available.

Section V turns transfer-matrix propagation of a local perturbation into a
finite-window MPS calculation. Window size and \(\chi\) are approximation
controls. The paper explicitly limits the finite-\(\chi\) summation-gradient
interpretation and conditions its convergence discussion on a transfer
spectral gap.

The numerical section uses optimized symmetry-constrained square-lattice
\(J_1\)-\(J_2\) infinite PEPS at **PEPS virtual bond dimension \(D=5\)** for
\(J_2=0\) and \(J_2=1/2\). Figure 1 displays monotone decrease only of
\(f=-\log\lambda\). Figure 4 is an empirical CTMRG/boundary-MPS energy
comparison, not an independently exact contraction. Figures 5--6 are
structure-factor comparisons; the paper expressly says the summed structure
factor is not variational.

Appendix B shows a three-row Ising example in which multi-site VUMPS becomes
unstable near \(T_c\), whereas the normalized-fidelity power method
converges. The source reports the observed instability-window size as largely
independent of the boundary-MPS bond dimension and its position as shifting
slightly toward lower temperature when that bond dimension increases.

The Discussion gives two explicit limits. The Hermitian subclass has only
real transfer eigenvalues, so the authors expect states with dominant
incommensurate correlations, including critical states at incommensurate
filling, to be poorly represented. The paper studies square-lattice PEPS and
leaves triangular, kagome, and more complicated unit-cell settings for
future work.

The source contains no finite syndrome circuit, Clifford frame,
GCAMPS/CAPEPS residual, selective measurement/reset instrument, raw-history
or prefix-mass law, detector/observable Record fold, conditional fidelity,
Record total variation, or matched CAPEPS/full-PEPS resource benchmark.
Those are source-local absences, not field-wide gaps.

## 4. Round-2 repair verification

| Round-2 requirement | current evidence | Round-3 decision |
|---|---|---|
| benchmark fact must call \(D=5\) the PEPS virtual bond dimension | note line 168 says exactly “PEPS virtual bond dimension \(D=5\)” | `PASS` |
| no physical-bond description of \(D\) | exhaustive case-insensitive scan of both current artifacts finds no physical-bond wording | `PASS` |
| audit must use virtual-bond terminology for \(D/\chi\) | audit lines 48, 65, 81, 93, 138, 155, and 172 use “PEPS virtual bond” or “virtual bond” | `PASS_EXCEPT_BARE_D5_ROW`; see blocker 1 |
| two-row locator must stop before Eq. (44) | note cites Sec. IV.B, Eqs. (36)--(43) | `PASS` |
| three-row locator must include Sec. IV.C Eqs. (44)--(48) and Appendix-B Eq. (B4) | note cites Sec. IV.C, Eqs. (44)--(48), and Appendix B, Eqs. (B1)--(B4) | `PASS` |
| finite-window locator must start at Sec. V Eq. (49) | note and audit cite Sec. V, Eqs. (49)--(68), identifying Eqs. (58)--(68) as the perturbation/window operation | `PASS` |
| retain the incommensurate-correlation limitation atomically | `vander2110-hermitian-incommensurate-limit`, PDF p. 12 | `PASS` |
| retain square-lattice/future-lattice scope atomically | `vander2110-square-lattice-scope`, PDF p. 12 | `PASS` |

The prohibited “physical bond dimension \(D=5\)” error is closed. Blocker 1
below is narrower: the audit's standalone benchmark closure row still uses
bare \(D=5\), so it does not itself carry the required virtual-bond
qualification.

## 5. Blocking defects

### Blocker 1 — the audit's atomic benchmark row leaves \(D=5\) unqualified

Audit location: assigned-closure table, current line 71  
Source locator: PDF page 9, Sec. VI opening paragraph, read with PDF page 2,
Sec. II first paragraph

Current audit text:

```text
On selected \(D=5\), symmetry-constrained \(J_1\)-\(J_2\) PEPS, ...
```

PDF page 2 visually and textually defines \(D\) as the bond dimension of the
four **virtual** indices and separately identifies the physical index. PDF
page 9 then says the benchmark PEPS tensors have bond dimension \(D=5\).
The note's atomic benchmark fact correctly reconstructs the combined meaning.

Under the explicit Round-3 gate that \(D=5\) must be called the PEPS virtual
bond dimension, the audit row is not self-contained. A reader retrieving that
closure row alone should not need a separate notation row to discover which
bond \(D=5\) denotes.

Required repair:

```text
On selected symmetry-constrained \(J_1\)-\(J_2\) PEPS with PEPS virtual
bond dimension \(D=5\), ...
```

This is not a return of the old physical-bond error: no current text calls
\(D\) physical. It is the remaining qualification defect in the audit's
independently readable benchmark row.

### Blocker 2 — the audit conflates \(M,\widetilde M\) with \(M,\bar M\)

Audit location: notation ledger, current line 84  
Source locators: PDF page 3, Sec. II around Eqs. (10)--(12) and footnote 3;
PDF page 4, Sec. IV.A, Eqs. (24)--(29)

Current audit row:

```text
\(M,\bar M\) | boundary-MPS tensors approximating left/right transfer fixed
points | PDF pp. 2--5
```

This is not the source's notation.

- In the general contraction review on PDF page 3, boundary MPSs found from
  the two directions are parametrized by \(M\) and \(\widetilde M\).
  Footnote 3 explicitly says there is generally no simple relation between
  them.
- In the Hermitian single-row variational construction on PDF page 4,
  \(|\Psi_M\rangle\) is a single MPS parametrized by \(M\), and
  \(\bar M\) is its conjugate bra tensor in
  \(\Lambda(M,\bar M)\), Eqs. (25)--(29). It is not the independently
  parametrized opposite-direction fixed point \(\widetilde M\).

The current row therefore changes the role of a load-bearing symbol and
silently transfers Hermitian bra/ket notation into the preceding generic
left/right setting.

Required repair: split the concepts or state both explicitly:

1. \(M,\widetilde M\): independently parametrized boundary MPSs from the two
   directions in the general Sec. II environment, PDF p. 3,
   Eqs. (10)--(12) and footnote 3.
2. \(M,\bar M\): the Hermitian variational MPS tensor and its complex
   conjugate bra tensor, PDF p. 4, Eqs. (24)--(29).

The operation replay and any surrounding prose must preserve this distinction.

### Blocker 3 — the audit does not preserve the source's overloaded \(N/L\) window notation

Audit locations: notation ledger line 87; operation replay lines 119--122  
Source locators: PDF page 1 Abstract; PDF page 6, Sec. V opening; PDF page 8,
Eq. (62); PDF pages 10--11, Fig. 5 discussion and Fig. 6 caption

Current audit row:

```text
\(N\) | finite-window length in correlation summation |
PDF pp. 7--11, Eqs. (62)--(69)
```

The source uses nearby symbols in more than one role:

- “\(N\)-point” in the Abstract, Sec. V opening, and Discussion means the
  number of operator insertions in a general correlation function.
- Eq. (62) writes the window tensors as \(N_i\), displaying
  \(N_1,N_2,\ldots,N_L\); the displayed terminal index is \(L\).
- The benchmark prose and Fig. 5 use \(N\) for window size, and the Fig. 6
  caption fixes window size \(N=10\).

The note's `vander2110-window-mps` fact uses \(N\)-point in the first,
source-faithful sense. The audit ledger and replay use \(N\) as window size
without recording the overload and cite Eqs. (62)--(69) as though those
equations unambiguously define \(N\) as the length. That loses a source
ambiguity in a load-bearing notation ledger.

Required repair:

- distinguish \(N\)-point order from benchmark window-size \(N\);
- record that Eq. (62) labels the window tensors \(N_i\) through \(N_L\);
- attach the window-size-\(N\) definition to the PDF pp. 10--11 benchmark
  prose/Figs. 5--6; and
- qualify replay statements such as “Increasing \(N\)” and
  finite-\((\chi,N)\) so they unambiguously mean the benchmark window size.

## 6. Load-bearing locator decision

| source row | exact visual/source check | decision |
|---|---|---|
| source identity and scope | PDF p. 1, title, author block, abstract, arXiv stamp | `PASS` |
| PEPS \(D\) versus environment \(\chi\) | PDF pp. 1--2; p. 2 explicitly assigns \(D\) to four virtual indices and separates the physical index | note `PASS`; audit benchmark row `FAIL_QUALIFICATION` |
| CTMRG update | PDF p. 2, Eqs. (5)--(7) and absorption/truncation paragraph | `PASS` |
| boundary-MPS environment | PDF pp. 2--3, Eqs. (8)--(12) | fact `PASS`; audit \(M\)-notation `FAIL` |
| finite-environment ambiguity | PDF p. 3, end of Sec. II | `PASS` |
| Hermitian transfer conditions | PDF pp. 3--4, Eqs. (13)--(20) | `PASS` |
| single-row variational objective | PDF p. 4, Eqs. (21)--(30) | `PASS` |
| VUMPS fixed-point correspondence | PDF pp. 4--5, Eqs. (29)--(35) | `PASS` |
| two-row construction | PDF pp. 5--6, Sec. IV.B, Eqs. (36)--(43) | `PASS` |
| three-or-more-row boundary | PDF p. 6, Sec. IV.C, Eqs. (44)--(48); PDF pp. 15--16, Eqs. (B1)--(B4) | `PASS` |
| finite-window correlation method | PDF pp. 6--8, Sec. V, Eqs. (49)--(68) | mechanism `PASS`; audit \(N/L\) ledger `FAIL` |
| transfer-gap caveat | PDF p. 8, footnote 4 | `PASS`; no contrary universal-rate claim |
| finite-\(\chi\) gradient caveat | PDF p. 8, Sec. V.B | `PASS` |
| \(D=5\) benchmark workload | PDF p. 9, Sec. VI opening | note `PASS`; audit row `FAIL_QUALIFICATION` |
| monotone displayed quantity | PDF p. 9, Fig. 1 and Sec. VI.A | `PASS`; limited to \(f=-\log\lambda\) |
| direct optimization versus VUMPS | PDF pp. 9--10, Figs. 2--3 | `PASS`; empirical wall time, no complexity theorem |
| CTMRG/boundary-MPS comparison | PDF p. 10, Fig. 4 | `PASS`; selected empirical energy comparison |
| structure-factor qualification | PDF pp. 10--11, Figs. 5--6 | `PASS`; summed observable expressly nonvariational |
| incommensurate-correlation limitation | PDF p. 12, Discussion | `PASS`; expected limitation, not a general no-go theorem |
| square-lattice scope | PDF p. 12, Discussion | `PASS` |
| Appendix-A gradient construction | PDF pp. 14--15, Eqs. (A1)--(A15) | `PASS` |
| multi-site VUMPS instability | PDF pp. 15--18, Eqs. (B1)--(B14), Figs. 7--10 | `PASS` |
| QEC/CAPEPS/Record absences | complete 18-page scope | `PASS_AS_SOURCE_LOCAL_GAPS` |

No other equation range crosses a section boundary, and no cited figure
number, equation number, page number, or stated source limitation was found
to be false at the reviewed hashes.

## 7. Atomic evidence and source/inference boundary

The candidate contains 28 H2 evidence records: 21 `paper_fact` and seven
`literature_gap`. Each has exactly one Fact ID, source locator, anchor PDF
page, and Claim in the required order; every gap also declares
`Gap scope: source_local`.

The 21 paper facts are bounded to source concepts and findings. The seven
QEC/CAPEPS/Record records are explicitly source-local absences. They do not
claim a field-wide gap. The incommensurate-correlation expectation is
correctly distinguished from a proved universal no-go theorem.

The benchmark, monotonicity, CTMRG comparison, structure-factor, and
multi-site-instability records each retain one coherent source finding plus
its directly coupled qualification or failure regime. No record crosses the
repaired IV.B/IV.C/V section boundaries. Round 3 requires no additional H2
split.

Project use and kill conditions remain in audit section 6, separate from the
source-only note. The note contains no project path, implementation owner, or
positive project-performance inference. The audit does not promote the
source into a CAPEPS algorithm, finite-circuit backend, Record-law
certificate, generic exact contraction, or matched resource advantage.

The three blockers above are source reconstruction/notation problems inside
the audit packet, not leakage of a positive project claim into the note.

## 8. Relation audit

All five relations resolve to existing `paper_fact` IDs. Every label names a
source concept present in the cited Claim; none introduces a project-defined
target.

| predicate / object label | Fact ID | semantic decision |
|---|---|---|
| `supports` / `Hermitian transfer matrix` | `vander2110-variational-objective` | `PASS` |
| `uses` / `environment bond dimension` | `vander2110-d-vs-chi` | `PASS` |
| `supports` / `boundary-MPS and CTMRG environments` | `vander2110-ctmrg-boundary-comparison` | `PASS` |
| `limits` / `multi-site VUMPS` | `vander2110-multisite-instability` | `PASS` |
| `limits` / `dominant incommensurate correlations` | `vander2110-hermitian-incommensurate-limit` | `PASS` |

The audit-notation blockers do not create dangling relations, but relation
resolution cannot cure them.

## 9. Artifact-backed structural preflight

The exact current candidate fails the artifact-verifying `parse_note` path at
the intended draft gate:

```text
admission_status must be 'source_only_reviewed'
```

A read-only in-memory simulation changed only:

```toml
admission_status = "draft_pending_review"
```

to:

```toml
admission_status = "source_only_reviewed"
```

Full artifact verification then passed the exact current PDF and audit hashes,
all evidence-record shapes, all relation references, and all checked-page
anchors:

```text
total=28 paper_fact=21 literature_gap=7 relations=5
checked_pages=1,2,3,4,5,6,7,8,9,10,11,12,14,15,16,17,18
```

The status-only diagnostic note SHA-256 was
`84318d06ee95a3a949114f87f0cf6fb63a6aab78d9fdf7a49bccbbf74589c7d6`.
It is not an admissible note hash and must not be placed in the manifest.

The note path, source ID, and source hash are absent from
`docs/papers/CURRENT_CORPUS.toml`. That exclusion is correct. Parser success
after a status-only simulation proves structural and artifact consistency,
not semantic correctness; it does not detect any of the three blockers.

## 10. Bounded decision and required sequence

At the reviewed hashes:

- full-source read status: `complete`
- review evidence status: `persisted`
- first-review locator blockers: `all_closed`
- Round-2 physical-bond blocker: `closed`
- note's \(D=5\) benchmark terminology: `pass_peps_virtual_bond_dimension`
- physical-bond wording anywhere in note/audit: `absent`
- audit benchmark-row qualification: `fail_bare_D5`
- audit \(M,\widetilde M\) versus \(M,\bar M\) notation: `fail_conflated`
- audit \(N/L\) window notation and overload: `fail_ambiguity_not_preserved`
- evidence-record locators apart from those audit-notation issues: `pass`
- relation labels and endpoints: `pass`
- source/project inference separation: `pass`
- fresh independent semantic decision: `FAIL_THREE_AUDIT_BLOCKERS`
- current-corpus admission: `NO`

Required sequence before another admission attempt:

1. qualify the audit's benchmark closure row as **PEPS virtual bond dimension
   \(D=5\)**;
2. split or correct the audit notation for
   \(M,\widetilde M\) versus \(M,\bar M\);
3. preserve the source's \(N\)-point/window-\(N\)/\(N_i\)-through-\(N_L\)
   overload and update replay wording/locators accordingly;
4. recompute the audit SHA-256 and update the note's stored audit hash;
5. obtain a fresh independent source-only rereview of the changed audit and
   its bound note;
6. only after a semantic PASS, set the final reviewer/status, recompute the
   final note hash, rerun artifact-backed validation, and admit exactly that
   identity to `CURRENT_CORPUS.toml`.

Until those steps are complete, the candidate remains a repaired but
unadmitted draft.
