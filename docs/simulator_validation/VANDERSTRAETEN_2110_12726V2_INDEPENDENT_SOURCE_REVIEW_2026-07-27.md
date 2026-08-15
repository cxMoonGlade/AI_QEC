# Independent source-only admission review — Vanderstraeten et al., arXiv:2110.12726v2

Date: 2026-07-27

Reviewer: `codex-independent-source-review-vanderstraeten-2110.12726v2-2026-07-27`

Verdict: **FAIL — locator correction, one retained source limitation, and a
fresh independent rereview are required**

The candidate is scientifically conservative on \(D\) versus \(\chi\), the
variational objective, benchmark scope, finite-\(\chi\) caveats, multi-site
VUMPS failure, and the QEC/CAPEPS/Record absences. It cannot be admitted yet
because three neighboring evidence records cross source section boundaries,
and the packet omits the paper's explicit applicability limitation for the
Hermitian-transfer subclass.

This review did not modify the candidate note, source-only audit, source PDF,
or `docs/papers/CURRENT_CORPUS.toml`.

## Reviewed byte identities

| object | SHA-256 |
|---|---|
| pinned source, `docs/papers/2110.12726v2.pdf` | `58763a732ef1c5b660bacbc708a2134b1c8a09096eca1e44326c03a1b540a184` |
| candidate note, `docs/papers/reading_notes/vanderstraeten_variational_peps_contraction_2110.12726v2_source_review.md` | `1d7f45eab016942297476c9c1e737648e6ee32aef8787357ee9772584c505a51` |
| source-only audit, `docs/simulator_validation/VANDERSTRAETEN_2110_12726V2_SOURCE_ONLY_AUDIT_2026-07-27.md` | `6269a29356c3e5d32992ecdd063fbd8cd0a99102f610c0222b30a98647f26aa5` |

The note's stored source and audit hashes equal the actual source and audit
hashes above.

## Independent source pass

The pinned PDF has a valid `%PDF-1.5` signature, contains 18 pages, and has a
visible `arXiv:2110.12726v2 [cond-mat.str-el] 7 Jun 2022` stamp on PDF page 1.
Its title and eight-author block match the candidate identity.

All 18 pages were read in source order before the candidate note and audit
were opened. PDF pages 1--12 and 14--18 were freshly rendered and visually
inspected; page 13 contains references only. The visual pass covered every
load-bearing equation, tensor diagram, benchmark plot, caption, caveat, and
Appendix-B failure figure used in this review. Text extraction was used only
for traversal.

No quarantined legacy note, RAG result, knowledge graph, project synthesis, or
old output verdict was used as evidence.

## Structural preflight

The artifact-verifying parser rejects the actual candidate at the expected
draft gate:

```text
admission_status must be 'source_only_reviewed'
```

A no-write simulation replaced only

```text
admission_status = "draft_pending_review"
```

with

```text
admission_status = "source_only_reviewed"
```

in memory. Every remaining schema, relation, checked-page, source-hash, and
audit-hash check passed:

```text
total=26 paper_fact=19 literature_gap=7 relations=4
```

The status-only diagnostic note SHA-256 was
`81fda80379a62a2bda1f4200c5da23a559b70426356d0f1e7e3cb94a142c4f45`.
That hash is not admissible: the reviewer remained
`pending_independent_source_only_review`, and structural success cannot
override the semantic blockers below.

No candidate slug, source ID, or source hash appears in
`docs/papers/CURRENT_CORPUS.toml`. That exclusion is correct.

## Blocking locator defects

### 1. The two-row fact includes the first three-row equation

Candidate record: `vander2110-two-row-construction`

Current locator:

```text
PDF pages 5--6, Sec. IV.B, Eqs. (36)--(44)
```

Section IV.B's two-row construction is Eqs. (36)--(43). Equation (44) appears
after the `C. More than two rows` heading and is the three-row recursive
eigenvalue system. Including Eq. (44) in a two-row atomic fact crosses the
source's explicit domain boundary.

The claim itself is supported after narrowing the locator to Sec. IV.B,
Eqs. (36)--(43), PDF pp. 5--6.

### 2. The three-row fact names the wrong subsection and omits its fidelity equation

Candidate record: `vander2110-three-row-breakdown`

Current locator:

```text
PDF page 6, Sec. IV.B, Eqs. (45)--(46), and Appendix B opening on PDF page 15
```

The source location is Sec. IV.C, not Sec. IV.B. The three-row setup begins at
Eq. (44); Eq. (46) rejects the simultaneous free-energy variational
principle, Eq. (47) defines that non-real candidate cost, and Eq. (48) gives
the sequential normalized-fidelity optimization that the claim says remains
available. Appendix B's matching normalized-fidelity equation is Eq. (B4) on
PDF page 16, not the page-15 opening alone.

The claim is source-supported, but its exact locator must cover Sec. IV.C,
Eqs. (44)--(48), PDF p. 6, and Appendix B Eqs. (B1)--(B4), PDF pp. 15--16.
The numerical failure evidence remains Figs. 9--10 on PDF p. 18.

### 3. The finite-window fact begins with equations from the preceding section

Candidate record: `vander2110-window-mps`

Current locator:

```text
PDF pages 6--8, Sec. V, Eqs. (47)--(68)
```

Equations (47)--(48) belong to Sec. IV.C's three-row discussion. Section V
begins with the structure factor at Eq. (49). The local transfer-matrix
perturbation and finite-window construction are introduced in Eqs. (58)--(68),
with Eqs. (49)--(61) establishing the correlation sum that the window
approximates.

The source-only audit repeats the same `Eqs. (47)--(68)` range in its assigned
finite-window row. Both artifacts must use a range beginning at Eq. (49), or a
more precise split between Eqs. (49)--(61) and Eqs. (58)--(68).

These are scientific locator defects, not parser formatting issues. The local
schema proves that a locator field exists and its anchor page was visually
checked; it does not prove that the named section and equation range contain
the attributed operation.

## Blocking completeness gap — Hermitian-subclass applicability

PDF page 12, Discussion and Outlook, gives an explicit limitation that the
candidate packet does not retain:

- a Hermitian transfer matrix has only real eigenvalues;
- transfer-matrix eigenvalues encode dominant correlation wavevectors in the
  cited MPS setting; and
- the authors therefore expect states with dominant incommensurate
  correlations, including critical states with incommensurate filling, to be
  poorly described by their Hermitian PEPS subclass.

The same discussion states that the paper studies only square-lattice PEPS and
leaves triangular, kagome, and more complicated unit-cell settings for future
investigation.

The existing `vander2110-hermitian-transfer` fact correctly says the positive
result is a subclass rather than a generic PEPS result. The audit also says
that arbitrary PEPS, chiral states, and arbitrary unit cells are not covered.
Those negative scope statements do not preserve the paper's affirmative,
mechanism-specific failure expectation for dominant incommensurate
correlations. Because this is the source's explicit answer to when the
Hermitian restriction may be unsafe, it is load-bearing contrary evidence and
requires its own source-located `paper_fact` or an equivalently atomic retained
limitation.

## Assigned scientific rows

| assigned row | independent source result | status |
|---|---|---|
| \(D\) versus environment \(\chi\) | PDF pp. 1--3 distinguish physical PEPS virtual bond \(D\) from CTMRG/boundary-MPS environment bond \(\chi\). Finite \(\chi\) remains an approximate contraction. | `pass` |
| Hermitian subclass | Eqs. (13)--(20) support the stated reflection/time-reversal and more general tensor conditions. The candidate does not promote them to arbitrary PEPS, but the explicit PDF-p. 12 incommensurate-correlation limitation is missing. | `correction required` |
| variational objective scope | Eqs. (21)--(30) optimize the leading-transfer-eigenvalue/free-energy-density objective at fixed boundary-MPS bond. The packet correctly rejects physical-energy, global-fidelity, and generic exact-contraction interpretations. | `pass` |
| one-row VUMPS equivalence | Eqs. (29)--(35) support equivalence between the zero-gradient condition and VUMPS fixed-point equations in the stated one-row Hermitian setting. | `pass` |
| two-row construction | The scientific claim is supported by Eqs. (36)--(43), but the candidate locator incorrectly includes three-row Eq. (44). | `locator correction required` |
| three-or-more-row boundary | Sec. IV.C and Appendix B support breakdown of the simultaneous free-energy principle and retention of a sequential normalized-fidelity objective, but the candidate names the wrong subsection and omits Eqs. (47)--(48)/(B4). | `locator correction required` |
| finite-window correlation method | Sec. V supports the method, but Eqs. (47)--(48) are not in Sec. V and must be removed from this atomic locator. | `locator correction required` |
| finite-\(\chi\) gradient caveat | PDF p. 8 distinguishes a fixed-\(\chi\) gradient from the approximate summation gradient, which becomes fully compatible only in the infinite-\(\chi\) regime. | `pass` |
| benchmark workload | PDF p. 9 uses symmetry-constrained square-lattice \(J_1\)-\(J_2\) infinite PEPS at \(D=5\), for \(J_2=0\) and \(J_2=1/2\). | `pass` |
| CTMRG/boundary-MPS wording | Fig. 4 shows selected energy comparisons at matched \(\chi\); it is not an exact reference or a general equivalence theorem. The candidate wording is properly empirical. | `pass` |
| monotonicity | Fig. 1 supports monotone decrease only of the optimized \(f=-\log\lambda\) norm/free-energy objective in the displayed calculations. | `pass` |
| physical energy and structure factor | Fig. 4 reports energy convergence without a monotonicity theorem. Figs. 5--6 are empirical; PDF p. 11 explicitly says the summed structure factor is not variational and gives no reason to expect approach from below generally. | `pass` |
| direct optimization versus VUMPS | Figs. 2--3 and the surrounding text support faster initial VUMPS convergence and faster late direct-optimization convergence only for the displayed implementation/workload; no asymptotic theorem is claimed. | `pass` |
| Appendix-B multi-site VUMPS failure | Eqs. (B1)--(B14) and Figs. 7--10 distinguish free-energy and sequential-fidelity criteria and show instability near \(T_c\) for the three-row example, while the power method converges. | `pass` |
| transfer-gap caveat | PDF p. 8 footnote 4 says the window iteration's convergence argument uses a transfer spectral gap and expects slower summation for fine-tuned critical-correlation PEPS. The candidate makes no contrary universal-rate claim. | `pass; bounded in this report` |
| QEC/CAPEPS/Record gaps | The complete 18-page scope contains no circuit updates, Clifford frame, CAPEPS residual, selective Born branch, reset map, raw-history/prefix masses, detector/observable fold, conditional fidelity, Record-TV, or matched CAPEPS/full-PEPS resource experiment. | `pass` |

## Atomic record review

| Fact ID | result |
|---|---|
| `vander2110-source-identity` | `pass` |
| `vander2110-selection-scope` | `pass` |
| `vander2110-d-vs-chi` | `pass` |
| `vander2110-ctmrg-update` | `pass` |
| `vander2110-boundary-mps` | `pass`; the transfer row is diagrammatically an MPO |
| `vander2110-finite-environment-ambiguity` | `pass` |
| `vander2110-hermitian-transfer` | `supported but incomplete without the explicit PDF-p. 12 applicability limitation` |
| `vander2110-variational-objective` | `pass` |
| `vander2110-vumps-equivalence` | `pass` |
| `vander2110-two-row-construction` | `fail: locator crosses into Eq. (44)` |
| `vander2110-three-row-breakdown` | `fail: wrong subsection and incomplete equation locator` |
| `vander2110-window-mps` | `fail: locator includes preceding-section Eqs. (47)--(48)` |
| `vander2110-finite-chi-gradient-caveat` | `pass` |
| `vander2110-benchmark-workload` | `pass` |
| `vander2110-monotone-free-energy` | `pass` |
| `vander2110-direct-vumps-runtime` | `pass` |
| `vander2110-ctmrg-boundary-comparison` | `pass` |
| `vander2110-structure-factor-qualification` | `pass` |
| `vander2110-multisite-instability` | `pass` |
| `vander2110-gap-generic-exactness` | `pass` |
| `vander2110-gap-finite-chi-certificate` | `pass` |
| `vander2110-gap-global-fidelity` | `pass` |
| `vander2110-gap-finite-circuit` | `pass` |
| `vander2110-gap-instrument` | `pass` |
| `vander2110-gap-clifford` | `pass` |
| `vander2110-gap-matched-resources` | `pass` |

All four relations resolve to existing `paper_fact` IDs, and their labels name
concepts present in the corresponding claims.

## Correctly retained scientific boundaries

### Physical PEPS bond versus contraction environment

The source defines \(D\) as the virtual bond dimension of the PEPS tensor and
\(\chi\) as the bond dimension of CTMRG or boundary-MPS environment tensors.
The two controls are not interchangeable. Increasing \(\chi\) refines an
approximate contraction of a fixed PEPS; it does not increase the physical
PEPS bond \(D\).

### Variational quantity

For the stated Hermitian transfer matrix, the Rayleigh-quotient construction
gives

\[
f(A,\bar A)=-\log\lambda
\]

and a fixed-\(\chi\) variational boundary-MPS objective. Figure 1 displays
monotone decrease of this optimized quantity with \(\chi\). The paper does not
transfer that monotonicity to:

- the physical Hamiltonian energy;
- the structure factor;
- global state norm error, trace distance, or fidelity;
- conditional branch fidelity;
- a QEC detector/observable distribution; or
- Record total variation.

### Benchmark comparison

The CTMRG/boundary-MPS energy comparison uses two selected, optimized,
symmetry-constrained \(D=5\) infinite PEPS. Agreement at larger \(\chi\) is an
empirical result on those workloads. The \(\chi=500\) value used as a
converged reference is not an independently exact contraction.

The structure-factor comparisons likewise show the displayed methods
converging numerically. The source expressly warns that the structure factor
is not variational, that approach from below has no general justification,
and that inadequate \(\chi\) can prevent convergence to the correct displayed
value as the window grows.

### Multi-row failure

Two rows retain the stated singular-vector/free-energy variational
construction. For three or more rows, simultaneously solving the multi-site
VUMPS equations is not backed by the rejected real free-energy objective in
Eq. (46). Sequential normalized-fidelity compression remains a valid power
method, and Appendix B exhibits a case where that power method converges but
multi-site VUMPS becomes unstable.

## Exact bounded admission verdict

After correction and a fresh source-only PASS, this source could support only:

1. the distinction between physical PEPS bond \(D\) and environment bond
   \(\chi\);
2. CTMRG and boundary-MPS contraction mechanics for infinite PEPS;
3. the algorithm-independent norm/free-energy variational objective for the
   stated Hermitian-transfer subclass;
4. the one- and two-row VUMPS/variational constructions under their stated
   hypotheses;
5. the finite-window normalized-fidelity correlation-summation algorithm,
   with finite-\(\chi\), finite-window, and transfer-gap caveats;
6. the displayed \(D=5\) \(J_1\)-\(J_2\) benchmark comparisons;
7. monotonicity only for the displayed optimized norm/free-energy objective;
   and
8. the explicit three-row multi-site VUMPS instability and robust
   normalized-fidelity power-method fallback.

This source cannot support:

- exact or certified contraction of arbitrary PEPS;
- applicability of the Hermitian subclass to dominant incommensurate
  correlations;
- identification of \(D\) with \(\chi\);
- a universal finite-\(\chi\) energy, correlation, or state-error bound;
- a global finite-\(\chi\) PEPS fidelity;
- monotone physical energy or structure-factor convergence;
- a finite-lattice gate-evolution or syndrome-extraction backend;
- a Clifford frame, GCAMPS, or CAPEPS construction;
- selective measurement, reset, raw-history/prefix mass, or a complete
  detector/observable Record law; or
- a matched CAPEPS/full-PEPS runtime, peak-memory, throughput, or Record-error
  advantage.

## Required repair and review sequence

Before another admission attempt:

1. narrow `vander2110-two-row-construction` to Sec. IV.B,
   Eqs. (36)--(43);
2. correct `vander2110-three-row-breakdown` to Sec. IV.C and add the
   normalized-fidelity locators Eqs. (47)--(48) and Eq. (B4);
3. start the finite-window source range at Sec. V Eq. (49), with
   Eqs. (58)--(68) identified as the finite-window operation, and make the
   same correction in the audit;
4. add an atomic source fact for the PDF-p. 12 real-eigenvalue /
   incommensurate-correlation limitation of the Hermitian subclass;
5. update the audit's assigned rows and bounded project application to retain
   that limitation;
6. recompute the audit hash stored in the note;
7. rerun the artifact-verifying parser;
8. obtain a fresh independent source-first semantic review; and
9. only after a PASS, set the reviewer/status, recompute the promoted note
   hash, and add exactly that identity to `CURRENT_CORPUS.toml`.

Until that sequence is complete:

- `read_status: complete`
- `evidence_status: persisted_pending_correction`
- `independent_source_review: fail`
- `semantic_packet_admissibility: fail`
- `structural_promotion_preflight: pass`
- `current_corpus_admission: no`

