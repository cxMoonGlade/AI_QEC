# Independent source-only admission rereview — Schwarz, Buerschaper, and Eisert, arXiv:1606.06301v2

Date: 2026-07-27

## Verdict

**PASS.** The candidate reading note and source-only audit are semantically
faithful to the pinned source at their stated conditional scope. I found no
source-semantic blocker to source-only corpus admission.

Admission is safe only after bookkeeping finalization: record this PASS and
the reviewer identifier in the audit, recompute the audit hash in the note,
replace the note's pending admission status and reviewer, rerun the
artifact-backed parser, and only then add the resulting note identity to
`CURRENT_CORPUS.toml`.

This verdict binds only the exact source and candidate revisions below.
Semantic edits require renewed review.

## Reviewed revisions

| object | path | SHA-256 |
|---|---|---|
| source PDF | `docs/papers/1606.06301v2.pdf` | `bc240a9b78a84e886360d4d0a621a0b06b12fef93e4e399c6b9aa1f66d1e43c3` |
| candidate note | `docs/papers/reading_notes/schwarz_approximating_local_observables_peps_1606.06301v2_source_review.md` | `b1c3430a7adf8710ca348c01e0510cb43d1a392fa9999220c5cf30b44c4d7284` |
| source-only audit | `docs/simulator_validation/SCHWARZ_1606_06301V2_SOURCE_ONLY_AUDIT_2026-07-27.md` | `37e8119e8ebc1e24dc94018621214e5f638b7e514c36d1d0ffb91601d96accb9` |

The source object is a valid, unencrypted seven-page PDF 1.5 file of 586,577
bytes with a valid header, cross-reference tail, and EOF marker. The title,
authors, arXiv identifier, v2 stamp, and 29 August 2016 version date agree with
the packet.

## Independent review method

I opened the pinned PDF before either candidate artifact. I read the complete
seven-page main text, references, and appendix in source order, then rendered
and visually inspected every page. Text extraction was used only for
navigation and bounded terminology scans. The source interpretation,
assumption ledger, complexity qualifications, and anomaly ledger were fixed
before the note and audit were opened.

The load-bearing displays and passages visually checked include Conjectures
1--2 and Theorem 1 on p. 2; the injectivity and uniform-prefix-gap definitions,
Eqs. (2)--(4), and the proof sketch on p. 3; Eqs. (5)--(7), the LTQO
qualification, and the main-text cross-references on p. 4; the detailed proof
on pp. 5--6, Eqs. (8)--(18); and the quantum and transfer-operator arguments on
p. 7, Eqs. (19)--(24).

## Theorem and operation replay

The packet preserves the theorem's actual input class and output:

| stage | source requirement or operation | exact locator | review result |
|---|---|---|---|
| conjectural bridge | Conjecture 1 concerns a PEPS approximation for each local observable; Conjecture 2 additionally requires injectivity and a gapped parent Hamiltonian and is stated for constant \(\epsilon\). Neither conjecture is Theorem 1. | p. 2, Conjectures 1--2 | PASS |
| theorem input | An unnormalised injective PEPS on a fixed-dimensional lattice, finite local dimension, bond dimension \(D\), local maps \(A_i\), and a uniformly gapped parent-Hamiltonian family. | p. 2, Theorem 1 | PASS |
| injectivity | After constant blocking, every local map is assumed left-invertible using its Moore--Penrose inverse. | p. 3, paragraph after Eq. (2) | PASS |
| uniform gap | Every prefix/sub-PEPS parent Hamiltonian \(H_t\), not merely the terminal \(H_N=H_*\), must obey \(\Delta_t\geq\Delta_*\). | p. 3, uniform-gap definition; p. 5 after Eq. (8) | PASS |
| observable and error | \(O_X\) has support on fewer than a constant number of sites, although \(X\) may be disconnected. The result is additive absolute error in one normalized scalar expectation, not a global state norm. | pp. 2--3, Theorem 1 and continuation | PASS |
| boundary removal | Exponential clustering is applied to every prefix; choosing \(O_i=(A_i^{-1})^\dagger A_i^{-1}\) gives a one-step error containing \(\kappa(A_i)^2\). | pp. 5--6, Eqs. (9)--(13) | PASS |
| accumulated error | Removing \(O(\ell^{d-1})\) boundary tensors produces the printed bound \(\ell^{d-1}e^{-O(\ell\Delta_*)}\kappa_*^2\|O_X\|\). | p. 6, Eq. (14) | PASS |
| local reduction | Boundary removal yields the exact patch--remainder factorization and reduces the target to the normalized patch expectation without a global norm computation. | p. 6, Eqs. (16)--(18) | PASS |
| classical output | The sufficient finite patch is contracted exactly with printed cost \((Dd)^{O(\ell^d)}\). This is not a finite-bond boundary-environment approximation. | p. 6, paragraph after Eq. (18) | PASS |

The note's 29 `paper_fact` records keep each of these claims conditional. The
audit's operation replay introduces no hidden transformation and does not
promote the conjectural approximation bridge into a proved generic-PEPS
premise.

## Classical, quantum, and hardness qualifications

### Classical

The source's radius is

\[
\ell\in O\!\left(
\frac{2\ln\kappa_*+\ln\epsilon^{-1}+\ln\|O_X\|}
     {\Delta_*}
\right).
\]

Quasi-polynomial deterministic system-size scaling therefore requires fixed
lattice and physical dimensions, a nonvanishing common prefix gap, and
polynomial control of \(D\), \(\kappa_*\), \(\epsilon^{-1}\), and
\(\|O_X\|\). The source separately calls the one-dimensional MPS case
polynomial. The packet preserves these qualifications and records that the
source's “constant deterministic time” prose fails to mention the remaining
\(D\) dependence in its displayed cost.

The theorem does not give a polynomial-time contraction of arbitrary
two-dimensional PEPS, numerical environment truncation, or a directly
executable error certificate: the exponential-clustering constants and
prefactors are hidden in \(e^{-O(\ell\Delta_*)}\).

### Quantum

The quantum arm imports the patch-preparation method of Ref. 32 rather than
proving it in this paper. The printed patch-preparation cost is
\(O(\ell^d\operatorname{polylog}(\ell/\epsilon))\), with
polylogarithmic preparation depth, and the source adds
\(O(1/\epsilon^2)\) independent preparations and measurements for constant
failure probability. It reports total quantum time
\(\widetilde O(\ell^d/\epsilon^2)\).

Thus inverse-polynomial precision does not give polylogarithmic total sampling
time, even though the preparation depth remains polylogarithmic. The packet
correctly records the time, depth, sampling count, external dependency, and
the omitted observable-range/variance/\(\|O_X\|^2\) dependence.

### Hardness

The introduction retains the cited #P-completeness boundary for general PEPS
contraction. The appendix separately recounts the postselected/PP construction
of Ref. 27 and gives a conditional complexity argument for injective
perturbations with very small parent gaps. The candidate does not turn those
cited and complexity-assumption-dependent statements into a new unconditional
hardness theorem. It uses them only to delimit the constant-uniform-gap input
class of Theorem 1.

## Named anomaly verification

Every anomaly named in the candidate packet is present in the pinned PDF and
is represented faithfully:

| named anomaly | source locator | source check | result |
|---|---|---|---|
| overloaded \(d\) | pp. 2--3, Theorem 1 and Preliminaries | \(d\) denotes both lattice dimension and physical dimension, including in \((Dd)^{O(\ell^d)}\). | PASS |
| hidden clustering constants | pp. 3--4 and 5--6, Eqs. (3)--(5), (9)--(14) | The source prints \(e^{-O(\ell\Delta_*)}\) without an explicit decay constant or prefactor. | PASS |
| uncontrolled non-injective closeness sentence | p. 3, injectivity paragraph | “\(\epsilon\)-close” has no norm, construction, prefix-gap control, or conditioning control. | PASS |
| constant-time wording omits \(D\) | p. 3, Theorem 1 continuation | The prose fixes \(d,\Delta_*,\kappa_*,\epsilon\), while the displayed runtime still depends on \(D\). | PASS |
| main/appendix equation cross-references | p. 4 after Eq. (7) | The main text cites Eqs. (17)--(18) beside the objects displayed there as Eqs. (6)--(7); those numbers occur in the appendix repetition. | PASS |
| quantum patch-size inconsistency | p. 7, quantum discussion final sentence | From \(\ell=O(\log N)\), the source prints \(\ell^d=O(\log N)\) spins without an additional restriction; generally the fixed-dimensional count is \(O(\log^d N)\). | PASS |
| sampling-scale omission | p. 7, Chernoff sentence | The \(O(1/\epsilon^2)\) count omits a range, variance, or observable-norm factor. | PASS |
| reversed injectivity wording | p. 7, transfer discussion | The opening inheritance direction conflicts with the direction used later in the derivation. | PASS |
| undefined transfer \(\delta\) | p. 7, Eqs. (22), (24) | \(\delta\) is not defined or explicitly identified with \(\Delta_*\). | PASS |
| unqualified transfer spectral expansion | p. 7 before Eq. (23) | The simple biorthogonal eigenvector expansion does not treat Jordan blocks or non-diagonalizable transfer operators. | PASS |

No candidate claim silently repairs one of these source defects.

Two additional literal cautions emerged in the fresh read. The source indexes
\(\{A_v\}_{0\leq v\leq N}\) despite describing \(N\) spins and elsewhere using
\(A_1,\ldots,A_N\), and Eq. (24) prints \(\lambda_2/\lambda_1\) without a
modulus even though a transfer operator can have complex subleading
eigenvalues. These do not block admission because the candidate makes no
tensor-count inference, reproduces Eq. (24) rather than repairing it, and
already confines the transfer claim behind the undefined-\(\delta\),
inheritance-direction, and spectral-expansion gaps. They are additional kill
conditions for any quantitative transfer-gap use.

## Transfer operator and LTQO

The packet correctly records that standard LTQO is not established: the proof
adds boundary terms to enforce uniqueness, whereas the cited LTQO condition
removes boundary terms. Only the paper's stated unique-ground-state variant is
retained.

The line-transfer argument additionally assumes Conjecture 2, all Theorem 1
assumptions, translational invariance, and contraction to a one-dimensional
line. Its inequality is retained only as the source's conditional printed
claim, qualified by the anomalies above. Nothing in the packet promotes it to
a gap theorem for arbitrary PEPS environments or transfer maps.

## Project gaps

The 18 `literature_gap` records and the audit correctly preserve the absent
bridges:

- no theorem for generic non-injective, G-injective, degenerate, or
  intrinsically topological PEPS;
- no higher-dimensional global trace-distance or fidelity guarantee;
- no finite-bond numerical environment truncation or approximation bound;
- no Clifford-augmented PEPS/CAPEPS mechanism, implementation, or matched
  accuracy/runtime/memory comparison;
- no outcome-resolved Born branch law or conditional post-measurement state;
- no reset operation or measurement--reset transaction; and
- no raw multi-time Record law, detector fold, logical bits, conditional
  fidelity, or Record-distance guarantee.

Consequently, this source cannot by itself certify an evolving CAPEPS residual,
uniform gaps and conditioning through Clifford/noise/measurement/reset
updates, or record-faithful scalable execution.

## Structural and fail-closed preflight

The note's source hash matches the PDF, and its
`audit_packet_sha256` matches the reviewed audit revision.

The on-disk note currently fails the artifact-backed parser at the intended
gate:

```text
admission_status must be 'source_only_reviewed'
```

A read-only in-memory simulation changed only the pending admission status and
reviewer values. With source and audit verification enabled, the complete note
then parsed successfully with 47 evidence records: 29 `paper_fact` records, 18
`literature_gap` records, and six validated relations.

At the validation snapshot, `CURRENT_CORPUS.toml` had file SHA-256
`450aa99e465d684d95cb3a1ef0cc67b38e822a550ca1e6e01d8030665cece7bf`,
loaded successfully with 40 notes and 525 paper facts, and had corpus identity
SHA-256
`234c11f2bca729e824368429a0c4c63028fdd593bc8f460adbcfe1a2d3e45157`.
The Schwarz note was absent, as required while review remained pending. The
artifact-verified candidate audit saw 280 candidates, 40 validated and 240
excluded; this note's reported exclusion was the pending admission status.

## Remaining blockers and admission decision

There are **no remaining source-semantic blockers** for the exact reviewed
revisions. The theorem restrictions, complexity regimes, source defects, and
project gaps are admission boundaries, not reasons to exclude the bounded
facts.

The only remaining blockers are mechanical and intentional:

1. update the audit's status and admission reviewer to cite this PASS;
2. recompute the audit SHA-256 in the note;
3. set `admission_status = "source_only_reviewed"` and replace the pending
   reviewer value;
4. rerun full artifact-backed note validation;
5. compute the finalized note hash and add that exact identity to the manifest;
6. rebuild and validate the RAG/KG corpus artifacts.

**Bounded admission verdict: safe to admit after those steps, for source-only
use and not as evidence for generic PEPS contraction, CAPEPS correctness or
efficiency, global fidelity, or measurement/reset/Record fidelity.**

Recommended reviewer identifier:
`independent_schwarz_1606_source_rereview_2026_07_27`.
