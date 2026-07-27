# Independent source-only admission review — Qian, Huang, and Qin, arXiv:2405.09217v2

Date: 2026-07-27

Reviewer: `agent:/root/review_qian_source`

Review target:

- `docs/papers/reading_notes/qian_clifford_augmented_dmrg_2405.09217v2_source_review.md`
- `docs/simulator_validation/QIAN_2405_09217_SOURCE_ONLY_AUDIT_2026-07-27.md`

Primary source:

- artifact: `docs/papers/2405.09217v2.pdf`
- SHA-256:
  `13e1369ff2817d5dc20c595716b2f89a505c239d245603ef89811b51e672e2b7`
- PDF pages: 6
- arXiv footer: `arXiv:2405.09217v2 [cond-mat.str-el] 21 Nov 2024`
- title-page manuscript date: 22 November 2024

## Admission decision

**FAIL — do not admit this revision to `CURRENT_CORPUS.toml`.**

The central scientific correction in the draft is right: Qian et al. optimize
SVD truncation loss/discarded singular values, not an objective that the paper
calls Rényi-2 entropy or purity; the PEPS statement is only prospective; and
the source contains no measurement--reset--Record instrument. However, two
load-bearing descriptions exceed the source:

1. the audit promotes the source's unspecified “discarded singular values” to
   a defined “discarded-SVD-weight” objective; and
2. the note/audit promote the source's unexplained count of 720 candidates
   after what it calls “phase redundancy” to a complete “phase-free
   two-qubit Clifford set.”

The source-only note also violates the one-fact/source-gap separation contract
in several records. These are repairable defects, but they must be repaired
and independently rechecked before admission.

## Review method

I read all six PDF pages independently before reading either target artifact.
The extracted text was traversed from title through Ref. [55]. PDF pages 2,
3, 4, and 6 were rendered and visually checked:

- page 2: Eqs. (1)--(4), Eq. (2) ansatz, and Fig. 1;
- page 3: Eq. (5), the local-search paragraph, the stated count of 720, and
  Fig. 2;
- page 4: Figs. 3--4, runtime paragraph, PEPS sentence, and local-minimum
  warning;
- page 6: Ref. [54]'s empirical small-bond note.

The local PDF hash matches the note and audit. The audit hash stored in the
note also matches the current audit artifact:
`f8c829047f6d8c35da75ae247e60cd5a9819d69631a1c610a9af4d43b55adfff`.
The repository audit correctly excludes the note only because its current
`admission_status` is `draft_pending_review`; parser acceptance would not
resolve the semantic findings below.

## Independent source reconstruction

| source object | exact source location | independently verified source statement |
|---|---|---|
| ansatz | PDF p. 2, Eq. (2), Fig. 1(a) | The paper defines \(\lvert\mathrm{CAMPS}\rangle=C\lvert\mathrm{MPS}\rangle\). |
| local DMRG problem | PDF p. 2, Eqs. (3)--(4) | A Pauli-string Hamiltonian is reduced to a two-site effective problem whose optimized state is \(\lvert\phi\rangle\). |
| local Clifford step | PDF pp. 2--3, Fig. 1(b), paragraph beginning “Now, the primary issue” | The paper applies a two-qubit Clifford \(C\), performs an SVD on \(C\lvert\phi\rangle\), and says it chooses among 720 candidates, “excluding phase redundancy,” to minimize truncation loss/discarded singular values. It gives no scalar loss equation and no definition or proof of the 720-element quotient. |
| Hamiltonian update | PDF p. 3, Eq. (5) and following paragraph | It updates \(H\) to \(H'=CHC^\dagger\) and uses Clifford preservation of Pauli-string form. |
| numerical findings | PDF pp. 3--4, Figs. 2--4 | It reports source-defined ground-state-energy relative errors and residual-MPS center-bond entropy for selected snake-mapped \(J_1-J_2\) workloads. The entropy curves are described as nearly identical below a critical bond dimension and separated above it. |
| timing | PDF p. 4, Discussion | It reports a CAMPS/MPS calculation-time ratio of about 1.2 for one \(10\times10\) OBC workload and says the ratio approaches one as bond dimension increases. |
| PEPS | PDF p. 4, Discussion | It states only that the Fig. 1(b) framework can be readily extended to tensor-network states “such as PEPS.” |
| local minima | PDF p. 4, Discussion; PDF p. 6, Ref. [54] | It warns of local minima and says empirically that they occur at small bond dimension, where it recommends not applying Clifford circuits. |

## Blocking findings

### F1 — The audit invents a defined “discarded-SVD-weight” objective

Severity: blocking

Affected locations:

- audit assigned-row status, line 24;
- audit Project application, lines 55--63;
- audit Source-local verdict, line 86.

The source says “minimize truncation loss,” “minimize the discarded singular
values,” and “calculating the singular values for all
\(C\lvert\phi\rangle\).” It does not define a scalar objective, discarded
weight, squared norm, retained rank, or aggregation over discarded singular
values. Therefore the source closes only this bounded row:

> the reported local search selects a candidate using SVD truncation
> loss/discarded singular values.

It does not close an exact “discarded-SVD-weight” functional. Replace every
such closure with the source's terminology and state that the scalar objective
is unspecified. This does not weaken the valid conclusion that the paper does
not state a Rényi-2 or purity objective.

### F2 — “720 phase-free two-qubit Cliffords” is an unsupported normalization

Severity: blocking

Affected locations:

- note local-search claim, line 92;
- audit assigned row, line 24;
- audit notation ledger, line 36;
- audit replay, line 48;
- audit Project application, lines 55--56.

The paper states “a total of 720 two-qubit Clifford circuits (excluding phase
redundancy, as they do not affect singular values).” It does not define the
equivalence relation, list representatives, or prove completeness. The
artifacts replace this ambiguity with “phase-free” and, in the replay, assert
that the set is complete.

The admissible source-only wording is:

> the paper reports evaluating 720 two-qubit Clifford candidates after
> excluding a redundancy it calls phase redundancy.

“Exhaustive” may be used only as “exhaustive over the paper's reported
720-candidate set.” Any claim that this is the complete two-qubit Clifford
group modulo a specified equivalence relation requires a separate
group-theoretic source and must remain outside this Qian source fact.

### F3 — Several evidence records bundle independently locatable facts or put gaps in `paper_fact`

Severity: blocking for source-only schema admission

Affected locations:

- note lines 57--59 append study scope to the source-identity record;
- note lines 67--68 put a source-local absence in the selection-scope
  `paper_fact`;
- note lines 76--77 append the separately located Eq. (1) MPS definition to
  the Eq. (2) ansatz record;
- note lines 94--96 put the Rényi-2 absence inside a `paper_fact`, duplicating
  the typed gap at lines 143--148;
- note lines 107--114 bundle the energy-error and center-bond-entropy findings
  and then append an unsupported-guarantee gap;
- note lines 131--132 put PEPS absences inside a `paper_fact`, duplicating the
  typed gap at lines 157--162;
- note lines 134--141 combine the p. 4 warning, the p. 6 empirical observation,
  and the p. 6 recommendation in one claim.

The reading-note contract requires one evidence record per independently
locatable claim and requires source-local absences to be typed as
`literature_gap`. Split the benchmark into at least energy-error and
residual-entropy records; split the p. 4 and p. 6 local-minimum facts; make Eq.
(1) a notation record if it is retained; and remove negative/gap prose from
`paper_fact` bodies when an explicit gap record already carries it. Update
relations whose `fact_id` changes.

## Required accuracy revisions

### F4 — Preserve the benchmark's threshold and reference definitions

Severity: required

The benchmark claim at note lines 107--114 says the residual-MPS entropy is
lower “at the shown bond dimensions.” The source itself says the MPS and
CAMPS entropies remain nearly identical before a critical bond dimension and
separate beyond it. Preserve that qualifier.

The revised energy record should also distinguish the source's references:
the \(J_2=0\) discussion invokes numerical QMC references, whereas the
subsequent Fig. 4 comparisons use a \(D=10000\) MPS result as the reference
energy. Do not turn the plotted relative errors into a general accuracy
guarantee.

### F5 — Visual-check metadata omits a page used by a claim

Severity: required

The local-minimum claim depends on Ref. [54] on PDF p. 6, while
`visually_checked_pages` lists only 2, 3, and 4. Page 6 has now been visually
checked in this independent review. After the record is split and rechecked,
the revised note should include page 6 in the visual-check ledger.

### F6 — Scope the Rényi-2 verdict as an attribution verdict

Severity: required

The source positively specifies discarded singular values/truncation loss and
does not state a Rényi-2/purity objective. Thus it is valid to reject a
sentence claiming that *Qian et al. state or derive* such an objective.
However, this paper alone does not prove a mathematical non-equivalence
between every possible scalarization of its unspecified truncation loss and
every Rényi-derived criterion. Phrase `contradicted` as a verdict on the
prior source attribution, not as a theorem comparing objective families.

## Claim-by-claim disposition

| target claim | source locator | disposition |
|---|---|---|
| source identity, version, date, hash | PDF p. 1; arXiv footer | PASS |
| MPS/DMRG ground-state scope | Abstract; PDF pp. 2--5 | PASS, after moving the QEC absence to its typed gap |
| \(C\lvert\mathrm{MPS}\rangle\) ansatz | PDF p. 2, Eq. (2), Fig. 1(a) | PASS |
| two-site effective Hamiltonian and \(\lvert\phi\rangle\) | PDF p. 2, Eqs. (3)--(4) | PASS |
| 720-candidate local search | PDF pp. 2--3, Fig. 1(b), local-search paragraph | FAIL as “complete phase-free set”; PASS only with the bounded reported-candidate wording in F2 |
| truncation-loss/discarded-singular-value criterion | PDF pp. 2--3 | PASS qualitatively; FAIL as a defined “discarded-SVD-weight” objective |
| no named Rényi-2/purity objective | full-text method and objective terminology | PASS as a source-local attribution gap |
| \(H'=CHC^\dagger\) Pauli-string update | PDF p. 3, Eq. (5) | PASS |
| reported ground-state benchmark | PDF pp. 3--4, Figs. 2--4 | PASS after F3/F4 split and qualification |
| reported runtime ratio | PDF p. 4, Discussion | PASS as a workload-specific reported observation |
| PEPS sentence is prospective only | PDF p. 4, Discussion | PASS |
| local-minimum warning and small-\(D\) note | PDF p. 4; PDF p. 6, Ref. [54] | PASS after split and visual-page update |
| no measurement--reset--Record instrument | full-text scope | PASS as a source-local gap |
| no PEPS implementation/correctness/efficiency result | PDF p. 4 and full-text scope | PASS as a source-local gap |

## Project-inference separation

The main architectural separation is correct:

- source facts and source-local gaps are in the reading note;
- CAPEPS applicability, Liu--Clark comparison, and kill conditions are in the
  separate audit packet;
- the PEPS sentence is not promoted to a CAPEPS implementation or result;
- no measurement, reset, branch-mass, conditional-state, or Record claim is
  imported from Qian et al.

The Liu--Clark statement is correctly placed under project/competing
evidence, and the repository manifest confirms that a source-only
Liu--Clark note is admitted. Its equation-level scientific content was not
re-adjudicated in this single-source Qian review. The audit should link the
relevant admitted fact/audit record if that comparison remains load-bearing.

## Re-review gate

Admission may be reconsidered only after all of the following:

1. F1 and F2 are corrected without substituting a new unstated objective or
   Clifford quotient.
2. F3 records are split and source-local absences are typed only as
   `literature_gap`.
3. F4--F6 qualifiers are incorporated.
4. The audit hash in the note is recomputed after the audit changes.
5. `admission_status` remains `draft_pending_review` until a reviewer checks
   the revised note and audit against the PDF.
6. A fresh independent review returns PASS before any
   `CURRENT_CORPUS.toml` edit.

Current result:

- `read_status: complete`
- `evidence_status: persisted`
- `independent_review_status: fail_required_revision`
- `admission_authorized: no`
