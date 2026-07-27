# Kim, Oh, and Kim arXiv:2607.03939v1 — independent source review

Date: 2026-07-27

Reviewer ID:
`independent_kim_2607_source_review_2026_07_27`

Decision: **FAIL — not admissible to the source-only corpus**

The candidate packet is strong on the qutrit Clifford count, the exact AKLT
theorem, the limits of the phase-wide and perturbative claims, numerical
resource scope, and the absence of PEPS, instrument/Record, and leakage
mechanisms. It nevertheless makes one load-bearing semantic error: it treats
the paper's simultaneous state/Hamiltonian update as an unresolved conjugation
ambiguity. The printed update is a consistent active-frame transformation,
and it needs no inverse-circuit convention.

This report does not modify the candidate note, candidate audit, or current
corpus manifest. Its FAIL decision does not reject the paper as useful
source-only evidence after repair.

## 1. Independence and review procedure

The complete `deep-read-paper` workflow and its reading-note template were
read before source review. I then:

1. verified the pinned PDF byte stream, hash, metadata, page count, header,
   xref tail, and terminal `%%EOF`;
2. read all 30 PDF pages in source order before opening either candidate
   artifact;
3. rendered and visually inspected all 30 pages, including Fig. 1, Eqs.
   (1)--(12), End Matter, Eqs. (S1)--(S134), Tables S1--S3, Figs. S1--S3,
   Lemmas 1--3, Propositions 1--3, and Theorem 1;
4. fixed the source-only judgments below before reading the candidate note
   or audit;
5. only then checked all 33 evidence records, their primary pages, every
   assigned closure row, the notation ledger, the operation replay, project
   application, kill conditions, hashes, schema state, and manifest exclusion.

Extracted text was used for traversal and full-text search. Formula, theorem,
figure, and frame-orientation judgments were made from the rendered source.
No earlier Kim review or project synthesis was used to form the source
judgment.

## 2. Fixed review objects

| object | observed identity |
|---|---|
| pinned source | `docs/papers/2607.03939v1.pdf` |
| source SHA-256 | `f02ec3815f3776c25b2e4a460eaaea2988b180deaecf9b602d4c0017c903cb9b` |
| PDF structure | PDF 1.7, 1,282,484 bytes, unencrypted, 30 pages |
| title and authors | *Disentangling Haldane Phase by Generalized Clifford Circuits*; Minsoo Kim, Changhun Oh, Donghoon Kim |
| version/date | arXiv:2607.03939v1 footer dated 4 July 2026; paper title block dated 7 July 2026 |
| candidate note | `docs/papers/reading_notes/kim_qutrit_camps_haldane_2607.03939v1_source_review.md` |
| candidate note SHA-256 | `c1514b91ec333b4764e15fd69d87312cc429ef2fdb7fb832bdd3161eed14eaec` |
| candidate audit | `docs/simulator_validation/KIM_2607_03939V1_SOURCE_ONLY_AUDIT_2026-07-27.md` |
| candidate audit SHA-256 | `36e8c2a8894e66d614db82056eb22c255c79fc8c70bdbb743a9918eb95981a2e` |
| note-declared source hash | exact match |
| note-declared audit hash | exact match |
| current manifest SHA-256 at review time | `a13b89d80a9b3ce1a99f7d642ed43670d3c0d5ce91b9a048e776c8cb3b12f42c` |

## 3. Independent source reconstruction

### 3.1 The 90-candidate result is one-sided and correctly counted

Supplement S1 first removes projective Pauli freedom:

\[
\mathrm{Cl}^{(3)}_2/P^{(3)}_2 \simeq
\operatorname{Sp}(4,\mathbb F_3),
\qquad
\left|\operatorname{Sp}(4,\mathbb F_3)\right|
=3^4(3^2-1)(3^4-1)=51840.
\]

Post-action local single-qutrit Cliffords preserve the bipartite Schmidt
spectrum. Their induced symplectic subgroup has order

\[
\left|\operatorname{Sp}(2,\mathbb F_3)\right|^2=24^2=576,
\]

so the one-sided index is

\[
51840/576=90.
\]

The source calls these “left cosets” after describing equivalence by left
multiplication with local gates. The operational content is the left action
of the output-local subgroup, or the left quotient \(H\backslash G\) in the
column-vector convention. It is not a double-sided local-equivalence
classification. The source gives the count and later partitions the selected
90 representatives into ten AKLT response types, but it does not print an
executable 90-gate transversal.

The candidate note and audit preserve all of these boundaries. Their 90-count,
one-sided qualification, double-sided gap, and missing-representative gap are
faithful.

### 3.2 The printed state/Hamiltonian direction is not ambiguous

PDF page 2 prints

\[
|\mathrm{CAMPS}\rangle=C|\mathrm{MPS}\rangle
\]

and says that because the disentangler acts on the state, the Hamiltonian is
updated simultaneously:

\[
\widetilde H=C_{\mathrm{opt}}H C_{\mathrm{opt}}^\dagger.
\]

Read as the active frame update the source describes, these equations are
algebraically consistent. For

\[
|\psi'\rangle=C|\psi\rangle,\qquad H'=CHC^\dagger,
\]

one has

\[
\langle\psi'|H'|\psi'\rangle
=
\langle\psi|C^\dagger C H C^\dagger C|\psi\rangle
=
\langle\psi|H|\psi\rangle.
\tag{R1}
\]

The rest of the paper uses the same direction consistently:

- Eq. (4) applies \(U_{\mathrm{KW}}\) to the AKLT state;
- Eqs. (8), (S16)--(S26), and the symmetry analysis use
  \(U_{\mathrm{KW}}HU_{\mathrm{KW}}^\dagger\);
- Eqs. (10)--(12) and (S111)--(S133) evaluate the actively transformed
  \(U_{\mathrm{KW}}|\mathrm{AKLT}\rangle\).

The alternative \(C^\dagger H C\) is the effective operator obtained in a
different question: keep a physical Hamiltonian \(H\) fixed and pull it back
through the passive ansatz \(C|\mathrm{MPS}\rangle\) to residual-MPS
coordinates. The source instead states that it transforms the state and
Hamiltonian together. No inverse-circuit convention is needed to reconcile
its displayed energy-preserving update.

This makes `kim2607-gap-frame-orientation` false as written. The same false
ambiguity appears in the audit's assigned closure row, notation ledger,
operation replay, project application, and source-local verdict. Because a
reader could reject or reverse a correct Hamiltonian update on this basis,
the error is load-bearing for admission.

### 3.3 Theorem 1 and the majorization argument have a narrow exact scope

The supplement's exact chain is:

1. Definition 1 fixes a \((\mathbf u,\mathbf v;a)\)-canonical tensor with
   \(\|\mathbf u\|^2=a\), \(\|\mathbf v\|^2=1-a\), and
   \(\mathbf u^\dagger\mathbf v=-\sqrt2/3\).
2. Proposition 1 applies the specified
   \(U_{j,j+1}=X_{j+1}^2U^{\mathrm{SUM}}_{j,j+1}\), performs an SVD, retains
   two nonzero squared Schmidt values, and propagates
   \(a'=(2-a)/3\).
3. Table S2 groups the source's 90 representatives into ten
   characteristic-polynomial types \(T_0,\ldots,T_9\), with \(T_0\)
   containing the specified gate.
4. For \(a\in[4/9,2/3]\), Eqs. (S56)--(S59) show that the \(T_0\) Schmidt
   vector majorizes every non-\(T_0\) vector:

   \[
   p^{T_0}_{\mathrm{Sch}}\succ p^{T_t}_{\mathrm{Sch}},
   \qquad t=1,\ldots,9.
   \]

   The \(k=1\) inequality follows from the separated largest-root bounds;
   for \(k\ge2\), the \(T_0\) vector has only two nonzero entries and its
   partial sum is already one. Schur concavity then gives minimum entropy
   for \(T_0\).
5. Starting from \(a_1=2/3\), the recurrence has

   \[
   a_j=\frac12+\frac{(-1)^{j-1}}{2\,3^j},
   \]

   so it remains in the stated interval.

Theorem 1 is therefore about the open-boundary AKLT state with the fixed edge
vectors \(L=R=e_\uparrow\), a sequential greedy left-to-right sweep, and
two-qutrit Clifford choices represented by the stated 90-candidate search.
The final bond is checked separately. The following subsection checks that a
right-to-left local update of the displayed KW-transformed AKLT state cannot
reduce entanglement further.

It is not a global optimum over arbitrary Clifford circuits, other edge
states, other sweep schedules, general Haldane-phase states, perturbed
tensors, or non-Clifford gates. The candidate note and audit preserve these
restrictions and the majorization-based local optimum correctly.

### 3.4 Phase-wide and perturbative statements are extrapolations

The main text says the AKLT result “implies” optimality throughout the Haldane
phase, supported by the reported CAMPS-DMRG results. The theorem does not
establish that phase-wide statement. It proves the fixed AKLT greedy-sweep
claim above; selected finite-system numerics support broader observations.

Equation (S61) gives an approximately \(0.35\) entropy gap between \(T_0\) and
the next-best type over the exact canonical interval. This gap supplies a
qualitative continuity rationale for a sufficiently small neighborhood, but
the source provides no tensor norm, perturbation radius, Lipschitz estimate,
or optimizer-preservation theorem.

The candidate packet correctly separates:

- source wording from theorem scope;
- a qualitative robustness interpretation from a quantitative robustness
  theorem.

### 3.5 Numerical evidence has a finite, unmatched resource scope

The displayed numerical evidence includes:

- Fig. 2: \(N=128\), shown bond dimensions up to \(\chi=100\), with a
  \(\chi=1000\) DMRG result used as the energy reference;
- Fig. 3: \(N=128\), \(\chi=300\), selected Heisenberg and BLBQ parameters;
- Fig. S1: the \(Z_3\) clock workload at \(N=128\), a \(\chi=1000\)
  reference for the energy plot, and \(\chi=100\) for the displayed
  entanglement profile;
- Fig. S2: \(N=128\) trivial/dimerized workloads and a \(\chi=1000\) DMRG
  energy reference.

The paper does not provide matched runtime, peak memory, throughput,
asymptotic scaling, source code or commit provenance, convergence tolerances,
sweep counts, random seeds, raw numerical data, or an independent exact
reference for the largest ground-state benchmarks. The figures support only
the source-reported finite-workload energy and residual-entanglement
comparisons.

The candidate packet states this boundary faithfully. Its resource gap is
not a claim that the displayed curves are absent; it prevents promotion of
those curves into a matched efficiency or scaling result.

### 3.6 PEPS, instrument/Record, and leakage are absent

The source studies pure-state, one-dimensional spin-1/qutrit MPS and unitary
Clifford disentangling in ground-state DMRG. It does not construct a PEPS or
CAPEPS residual, a two-dimensional update/contraction, or a PEPS benchmark.

It also does not define a selective measurement, Born branch mass, reset
channel, conditional trajectory, raw-history law, detector/observable fold,
conditional fidelity, or Record total variation.

Its qutrit is the intended three-dimensional local Hilbert space of a spin-1
model. It is not a computational subspace plus leakage level, and the paper
defines no leakage/seepage channel, leakage observation, or return dynamics.

The corresponding candidate gaps are faithful and necessary.

## 4. Evidence-record audit

`PASS` below means the individual claim or gap is source-faithful. It does not
override the packet-wide blocking error.

| Fact ID | independent source check | result |
|---|---|---|
| `kim2607-source-identity` | title, authors, v1 footer, title-page date, and 30-page object are correct | PASS |
| `kim2607-qutrit-pauli-setup` | definitions of \(X\), \(Z\), and \(\omega\) are exact | PASS |
| `kim2607-qutrit-clifford-generators` | Pauli, Fourier, phase, and SUM generators are stated | PASS |
| `kim2607-qutrit-mps` | physical labels and tensor dimensions match Eq. (1) | PASS |
| `kim2607-camps-ansatz` | the printed state relation is exact | PASS |
| `kim2607-local-selection` | the source selects a bond gate by entanglement reduction | PASS |
| `kim2607-printed-hamiltonian-update` | \(C_{\rm opt}HC_{\rm opt}^\dagger\) is transcribed exactly | PASS; it is an active update |
| `kim2607-main-numerical-comparison` | finite \(N=128\) comparisons and the \(\chi=1000\) reference are correctly bounded | PASS |
| `kim2607-kw-circuit` | Eq. (4) is exact | PASS |
| `kim2607-canonical-recurrence` | \(a_{j+1}=(2-a_j)/3\) is exact | PASS |
| `kim2607-phase-wide-wording` | records the paper's own broader wording without promoting it to a theorem | PASS |
| `kim2607-locality-criterion` | preserves the source statement and notes the supplement's interior-site scope | PASS |
| `kim2607-long-range-order` | the reported/derived \(1/4\) and \(\pm1/2\) AKLT limits are correct | PASS |
| `kim2607-qudit-future-direction` | general qudits/ququarts are future work | PASS |
| `kim2607-projective-clifford` | projective Pauli and Clifford definitions are faithful | PASS |
| `kim2607-ninety-left-cosets` | \(51840/24^2=90\) and the source's one-sided language are faithful | PASS |
| `kim2607-boundary-product-lemma` | nondegeneracy plus \([H,Z_N]=0\) gives one surviving last-site sector | PASS |
| `kim2607-canonical-propagation` | squared Schmidt values and propagated canonical form match Eqs. (S48)--(S52) | PASS |
| `kim2607-polynomial-types` | ten response types and \(T_0\)'s role match Table S2 | PASS |
| `kim2607-aklt-greedy-theorem` | fixed \(L=R=e_\uparrow\) AKLT left-to-right greedy scope is preserved | PASS |
| `kim2607-entropy-gap` | approximately \(0.35\) and the source's qualitative interpretation are preserved | PASS |
| `kim2607-post-sweep-local-optimum` | correctly bounded to the displayed KW-transformed AKLT construction | PASS |
| `kim2607-onsite-symmetry` | Proposition 2's \(N\ge4\) Heisenberg classification is correct | PASS |
| `kim2607-gap-frame-orientation` | claims an ambiguity that the active simultaneous update resolves by Eq. (R1) | **FAIL — blocking** |
| `kim2607-gap-matched-resources` | no matched runtime/memory/throughput/scaling result appears | PASS |
| `kim2607-gap-peps` | no PEPS/CAPEPS construction or benchmark appears | PASS |
| `kim2607-gap-instrument` | no measurement--reset--Record instrument appears | PASS |
| `kim2607-gap-leakage` | intentional spin-1 qutrits are not a leakage model | PASS |
| `kim2607-gap-double-sided-quotient` | the source establishes only the one-sided post-local count | PASS |
| `kim2607-gap-representatives` | no executable 90-representative catalogue is printed | PASS |
| `kim2607-gap-theorem-scope` | excluded global/boundary/schedule/phase/non-Clifford scopes are correct | PASS |
| `kim2607-gap-perturbation-radius` | no quantitative perturbation theorem appears | PASS |
| `kim2607-gap-phase-wide-proof` | no exact phase-wide theorem appears | PASS |

The note has 23 `paper_fact` records and 10 `literature_gap` records. Fact IDs
are unique, the required field order is present, all primary PDF pages are in
the declared visual-page set, and there are no relation records.

## 5. Audit-packet disposition

Most assigned closure and replay rows are faithful. In particular, the audit
correctly handles:

- the qutrit Clifford algebra and one-sided 90-count;
- finite-workload numerical comparisons;
- the exact AKLT greedy theorem and post-sweep local optimum;
- the qualitative-only robustness and phase-wide extrapolation;
- locality and symmetry results;
- the missing PEPS, leakage, and measurement--reset--Record bridges.

The frame error is not isolated to one optional comment:

1. the assigned `frame convention` row calls the source ambiguous;
2. the notation ledger says the circuit orientation is not reconciled;
3. the operation replay marks gate accumulation ambiguous;
4. project application says the orientation must be independently settled
   before the Hamiltonian update can be reused;
5. the source-local verdict repeats `ansatz/Hamiltonian frame orientation:
   ambiguous`.

Those statements should instead close the active transformation
\((H,|\psi\rangle)\mapsto(CHC^\dagger,C|\psi\rangle)\). A separate passive
pullback \(C^\dagger H C\) may be documented if needed, but it must not be
presented as a contradiction in this source.

## 6. Schema, hash, and manifest state

The repository's artifact-verified parser currently rejects the candidate for
the expected pre-admission reason:

```text
admission_status must be 'source_only_reviewed'
```

A read-only in-memory substitution of only

```text
admission_status = "source_only_reviewed"
admission_reviewer = "independent_kim_2607_source_review_2026_07_27"
```

passes full `parse_note(..., verify_artifact=True)` validation and yields 33
sections: 23 paper facts, 10 literature gaps, and zero relations. This proves
the structural shape and artifact hashes, not semantic correctness.

At review time, the artifact-verified candidate audit reported:

- 279 candidate notes;
- 37 structurally validated notes;
- 242 excluded notes;
- the Kim note excluded only by its pending admission status.

The live manifest loaded 37 notes and 455 paper facts and contained no Kim
entry. That exclusion is correct. The manifest already had unrelated working
tree changes when inspected and was not modified by this review.

## 7. Admission decision and required repair

**Admission authorization is denied.** Before a new independent review:

1. remove or rewrite `kim2607-gap-frame-orientation` so it records the
   source's active paired update rather than a false inverse-convention gap;
2. repair the audit's frame closure row, notation ledger, operation replay,
   project application, and source-local verdict consistently;
3. retain the distinction between the active update \(CHC^\dagger\) and the
   passive residual-frame pullback \(C^\dagger H C\), without conflating
   them;
4. recompute the audit SHA-256 and update the note's declared audit hash;
5. obtain a fresh independent semantic review before changing the admission
   fields;
6. add the note to `CURRENT_CORPUS.toml` only after that repaired note passes
   artifact-verified validation.

No repair is requested to the paper facts or gaps concerning the 90
one-sided classes, theorem scope, phase-wide/perturbative extrapolation,
numerical resource boundary, PEPS, instrument/Record, or leakage. Any
scientific or locator change beyond the frame repair must also be reviewed.

## Final bounded verdict

- full-source read and visual review: `complete`
- source and candidate hashes: `verified`
- 90 one-sided qutrit classes: `faithful`
- exact AKLT greedy-sweep theorem and majorization: `faithful_at_source_scope`
- phase-wide exact optimality: `missing`
- quantitative perturbation robustness: `missing`
- numerical matched-resource claim: `missing`
- PEPS/CAPEPS mechanism: `missing`
- measurement--reset--Record mechanism: `missing`
- qutrit leakage mechanism: `missing`
- candidate frame-ambiguity record: `incorrect`
- source-only evidence pair: **FAIL**
- admission authorization: **DENIED**
