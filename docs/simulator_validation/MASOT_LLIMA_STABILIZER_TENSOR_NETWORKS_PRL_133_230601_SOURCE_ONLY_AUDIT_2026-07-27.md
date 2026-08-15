# Source-only claim audit — Masot-Llima and Garcia-Saez, PRL 133, 230601

Date: 2026-07-27

Evidence status: `persisted`

Revision status: `source_only_review_pass_after_repair`

First independent review:
`docs/simulator_validation/MASOT_LLIMA_STN_PRL_133_230601_INDEPENDENT_SOURCE_REVIEW_2026-07-27.md`

First independent review SHA-256:
`e2631163e858a1c5e82e355de13c76b01ffef89cfe4f28e4715644fa1b0c9546`

Round-2 independent review:
`docs/simulator_validation/MASOT_LLIMA_STN_PRL_133_230601_INDEPENDENT_SOURCE_REREVIEW_ROUND2_2026-07-27.md`

Round-2 independent review SHA-256:
`956897767dd6071967a8375290c940f7fbf19c20b2fa7f682d0e6a0bc3a23e4d`

Admission reviewer: `independent_stn_vor_source_rereview_round2_2026_07_27`

Primary source: version of record for
`doi:10.1103/PhysRevLett.133.230601`

Article artifact:
`docs/papers/PhysRevLett.133.230601_version_of_record.pdf`

Article SHA-256:
`7630570f2d8281ac29a99075082c7e992f8f68aa9d05bd13cf190c473f08946c`

Official supplemental artifact:
`docs/papers/PhysRevLett.133.230601_supplement_version_of_record.pdf`

Supplement SHA-256:
`5d9dcbd7746b79c38678a72fb42f6b4a529ea4678de2b873b0ee85fbc276b2d1`

The six-page article and eleven-page official supplement were read in full.
The article PDF pp. 1--4 and supplement PDF pp. 1--6, 8--9 were rendered and
visually checked. These pages contain every formula, theorem, figure, and
proof line used below. Text extraction was used only for traversal and
search. The supplement text extraction contains a NUL byte, so formula
judgments were made from the rendered PDF.

## Version choice and source boundary

The source of record is the published article, *Physical Review Letters* 133,
230601 (2024), received 9 April 2024, revised 17 September 2024, accepted 24
October 2024, and published 3 December 2024. The official supplement was
retrieved as the supplemental member of the APS article package and is bound
above by its own SHA-256.

The earlier arXiv:2403.08724v2 artifact remains useful for version comparison
but is not the authority for this audit. The version of record adds a formal
multi-term-unitary factorization statement and additional locality examples;
supplement PDF p. 10 still leaves software implementation of unitaries with
arbitrary decomposition to future work.
Neither version supplies reset, a multi-round Record law, a PEPS residual
implementation, or a matched PEPS resource comparison.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| stabilizer-basis coefficient representation | article Fig. 1 and Eq. (2), PDF p. 2; supplement Lemma 1, PDF p. 1 | A tableau-defined stabilizer basis is paired with tensor-network coefficients; the supplement proves the basis states are normalized, mutually orthogonal, and span the Hilbert space. | It does not identify those coefficient tensors with a physical-lattice PEPS. | `closed` |
| Clifford update | article Eqs. (3)--(4), PDF pp. 2--3 | Clifford conjugation updates the stabilizer basis and leaves the coefficient state unchanged. | It does not establish a runtime or memory advantage for a PEPS residual. | `closed` |
| two-term non-Clifford update | article Eqs. (5)--(6), PDF p. 3; supplement Lemma 2, PDF pp. 2--3 | A two-term unitary decomposition becomes a basis update plus a multi-qubit Pauli-axis rotation on the coefficient state. | It does not show that the pulled-back rotation stays geometrically local. | `closed_as_source_mechanism` |
| multi-term unitary statement | supplement Eqs. (17)--(19), PDF pp. 3--4; implementation qualifier on PDF p. 10 | The published supplement states a formal product-of-rotations extension for decompositions with more than two terms. | It does not implement arbitrary-decomposition unitaries in the reported Python code, and gives no target-circuit PEPS benchmark or generic contraction guarantee. | `closed_as_formal_source_statement` |
| selective projective measurement | article Eqs. (7)--(9), PDF p. 3; supplement Lemma 3 and Eqs. (24), (27)--(35), PDF pp. 4--6 | The source computes \(p_\pm=(1\pm\langle O\rangle)/2\). For \(\hat n\ne0\) it defines a basis update and \(P_k\widetilde R\); for \(\hat n=0\), Eq. (27) instead leaves the basis unchanged and gives a diagonal coefficient projection. The physical branch norm follows directly from the projector identity. | Lemma 3 does not supply one well-defined \(P_k\widetilde R\) rule for \(\hat n=0\), and the source does not define reset, a branch-history ledger, or a multi-round Record pushforward. | `closed_by_explicit_case_split`; uniform Lemma 3 rule and printed proof `contradicted` |
| coefficient-bond behavior under measurement | article paragraph following Eq. (9), PDF p. 3 | The source warns that both non-Clifford gates and measurements can introduce coefficient correlations that increase \(\chi\). | It does not prove that repeated measurements monotonically shrink support or bond dimension. | `closed` |
| concrete tensor-network backend | article Tensor networks paragraph and Eq. (1), PDF p. 1 | The worked coefficient backend is a one-dimensional MPS. | No PEPS residual is constructed or executed. | `closed_for_MPS`; PEPS `missing` |
| operator-Schmidt bond bound | supplement Eqs. (40)--(42), PDF pp. 8--9 | The source states a \(k\chi\) upper bound after applying an operator-Schmidt-rank-\(k\) bipartite gate and derives \(4\chi\) or \(16\chi\) circuit-routing bounds. | The proof's claim that the displayed product expansion is already a Schmidt decomposition is not valid in general; the rank upper bound survives because the expansion contains at most \(k\chi\) product terms. | `closed_as_bound`; proof wording `contradicted` |
| reset and complete Record law | full article and supplement scope | Measurement is treated as a single selective projective primitive. | Reset, raw-history mass, prefix mass, repeated-round Record construction, detector/observable folds, and Record-law fidelity are absent. | `missing` |
| QEC/PEPS efficiency result | article conclusion, PDF pp. 4--5; supplement p. 9 | Higher-connectivity tensor-network geometries are mentioned as a possible way to reduce routing-induced bond growth, with higher contraction complexity. | No syndrome-circuit experiment, PEPS algorithm, runtime, peak memory, or matched-accuracy full-PEPS comparison is reported. | `missing` |

## Notation ledger

| symbol | source meaning | type / range | fixed or variable | exact source location |
|---|---|---|---|---|
| \(S=\langle s_1,\ldots,s_n\rangle\) | stabilizer group defining \(\lvert\psi_S\rangle\) | commuting \(n\)-qubit Pauli generators | basis state | article PDF p. 2; supplement Eq. (1), PDF p. 1 |
| \(D=\langle d_1,\ldots,d_n\rangle\) | destabilizer group paired with \(S\) | Pauli generators with the stated commutation relations | basis label system | article PDF p. 2; supplement Eq. (1), PDF p. 1 |
| \(\mathcal B(S,D)\) | stabilizer basis \(\{\delta_i\lvert\psi_S\rangle\}\) | \(2^n\) orthonormal states | changes under basis updates | article Fig. 1 and Eq. (2), PDF p. 2; supplement Lemma 1, PDF p. 1 |
| \(\lvert\nu\rangle\) | coefficient state in the stabilizer basis | \(n\)-qubit amplitude vector represented by a TN | updated by non-Clifford gates and measurement | article Fig. 1 and Eqs. (2)--(9), PDF pp. 2--3 |
| \(\chi\) | MPS bond dimension of the coefficient state | positive integer | workload- and update-dependent | article PDF pp. 1, 3--4 |
| \(U=\sum_i\phi_i\delta_{\hat d_i}\sigma_{\hat s_i}\) | operator decomposition in stabilizer-basis Pauli factors | unitary decomposition | physical operation | article Eq. (5), PDF p. 3; supplement Eq. (6), PDF p. 2 |
| \(O=\alpha\delta_{\hat n}\sigma_{\hat m}\) | measured Pauli observable in the basis decomposition | Hermitian Pauli observable with phase \(\alpha\) | measured operation | article Eqs. (7)--(9), PDF p. 3 |
| \(p_\pm\) | probability of the positive or negative measurement outcome | \([0,1]\) | branch-dependent | article measurement paragraph, PDF p. 3; supplement Eq. (22), PDF p. 4 |
| \(k\) | operator Schmidt number in the bond-growth argument | positive integer | gate-dependent | supplement Eqs. (40)--(42), PDF pp. 8--9 |

## Operation replay

### Stabilizer-basis state

The source pairs a tableau basis with a coefficient vector:

\[
\lvert\psi\rangle
=\sum_i\nu_i\,\delta_i\lvert\psi_S\rangle.
\]

Supplement Lemma 1 proves normalization, mutual orthogonality, and dimension
\(2^n\) using binary indices \(i\in\{0,\ldots,2^n-1\}\). This supplies the
representation invariant. The article's Eq. (2) prints an inclusive upper
limit \(2^n\); that conflict is recorded as an indexing anomaly, not silently
corrected in a quotation.

### Clifford update

For a Clifford \(G\), the source conjugates the stabilizers and destabilizers
to a new basis \(\mathcal B(\widetilde S,\widetilde D)\). Equations (3)--(4)
state that the coefficient state is unchanged. This closes an exact basis
update only; it does not measure the cost of a particular tensor-network
backend.

### Non-Clifford update

For a two-term decomposition, article Eqs. (5)--(6) and supplement Lemma 2
rewrite the operation as a Clifford/basis factor together with

\[
R_{X_{I_x}Y_{I_y}Z_{I_z}}(2\theta)
=\cos\theta\,I-i\sin\theta\,
X_{I_x}Y_{I_y}Z_{I_z}
\]

acting on \(\lvert\nu\rangle\). The pulled-back support is determined by the
basis labels and can be nonlocal in the MPS ordering. Supplement Eqs.
(17)--(19) state the published multi-term extension as a sequence of such
rotations.

### Selective projective measurement

For \(O=\alpha\delta_{\hat n}\sigma_{\hat m}\), the article computes

\[
\langle O\rangle
=\alpha\langle\nu\rvert X_{\hat n}Z_{\hat m}\lvert\nu\rangle,
\qquad
p_\pm=\frac{1\pm\langle O\rangle}{2}.
\]

After choosing an outcome, the coefficient update must be replayed in the two
source cases separately. When \(\hat n\ne0\), \(k\) is the position of the
first one in \(\hat n\); the source updates the tableau basis and applies
\(P_k\widetilde R\). When \(\hat n=0\), Eq. (27) keeps the basis fixed and
directly applies the diagonal projection \((I\pm\alpha Z_{\hat m})/2\) to the
coefficient state. Supplement Lemma 3 states that the physical unnormalized
branch has norm

\[
\mathcal N=\sqrt{\frac{1\pm\langle O\rangle}{2}}.
\]

This is an outcome-resolved projective-measurement primitive. It is not a
reset transaction or a proof of a complete multi-round classical Record law.
The physical norm is accepted from the direct identity
\(\|(I\pm O)\lvert\psi\rangle/2\|^2=(1\pm\langle O\rangle)/2\), not from the
printed uniform proof. Lemma 3 leaves \(k\) and \(P_k\) undefined for
\(\hat n=0\); the attempted \(\hat i_k\equiv0\) rejoining does not fix that
domain error and conflicts with the bit-flip equivalence later used in Eq.
(34). Equation (34) also contains the separate inconsistent intermediate
global-expectation term described below.

### Bond upper bound

The supplement expands a state of Schmidt rank at most \(\chi\) under an
operator of Schmidt number \(k\) into at most \(k\chi\) product terms. That
immediately gives Schmidt rank at most \(k\chi\). The printed sentence that
the expansion is itself a valid Schmidt decomposition does not follow from
operator-basis orthogonality, because the vectors
\(A_i\lvert\psi_A^j\rangle\) and
\(B_i\lvert\psi_B^j\rangle\) need not be mutually orthogonal over the pair
\((i,j)\). The upper bound is retained; the stronger wording is rejected.

## Source-local anomalies

1. **Article Eq. (2) indexing.** PDF p. 2 prints
   \(\sum_{i=0}^{2^n}\) for a basis described as containing \(2^n\) states.
   Supplement Eq. (1) and Lemma 1 use the consistent binary range ending at
   \(2^n-1\). The article line is treated as an indexing typo.
2. **Supplement Lemma 3 at \(\hat n=0\).** PDF pp. 4--6 define \(k\) as the
   first one in \(\hat n\) and \(P_k=\lvert0\rangle\langle0\rvert_k\), but
   state the lemma without \(\hat n\ne0\). Equation (27) correctly gives a
   separate no-basis-update rule at \(\hat n=0\). The later convention
   \(\hat i_k\equiv0\) neither defines \(P_k\) nor satisfies Eq. (34)'s
   \(\hat i_k=0\iff(\hat i+\hat n)_k=1\) when \(\hat n=0\). The uniform
   coefficient rule is therefore undefined in that case.
3. **Supplement Eq. (34).** On supplement PDF p. 6, an intermediate line
   writes a sum whose summand contains the already-global expectation
   \(\langle\psi\rvert O\lvert\psi\rangle\) without the coefficient factors
   needed for that equality. The final Born norm is standard and can be
   obtained directly from the projector, but the printed intermediate
   equality is not a valid derivation as written.
4. **Supplement Eq. (42) prose.** PDF p. 9 calls the \(k\chi\)-term product
   expansion a valid Schmidt decomposition because \(A_i,B_i\) form
   orthogonal operator bases. Operator orthogonality does not imply
   orthogonality of all state vectors produced from arbitrary Schmidt vectors.
   The product-term count still proves the rank upper bound.

## Disconfirmation of the legacy note

The quarantined legacy note
`docs/papers/reading_notes/stabilizer_tensor_networks_2403.08724.md` must not
be used as current evidence. In particular:

- it treats the article Eq. (2) inclusive upper limit as if it were the
  correct basis range;
- it says measurement tends to shrink \(\chi\), whereas the article
  explicitly warns that measurement can introduce correlations that increase
  \(\chi\);
- it upgrades measurement plus a conditional Clifford into a native reset
  result even though reset is not specified;
- it extrapolates to repeated QEC rounds, qutrit leakage, PEPS resource
  behavior, and hardware cost without source support;
- it labels the measurement and bond proofs theorem-grade without retaining
  the printed proof anomalies above.

These statements remain quarantined project inference or are contradicted by
the version of record. None is copied into the clean source-only note.

## Project application and kill conditions

The source can support a stabilizer-basis/TN representation, an exact
Clifford basis update, a pulled-back non-Clifford update, and a single
selective Pauli-measurement primitive. It cannot by itself support any of the
following:

1. a Clifford-frame plus PEPS-residual construction;
2. reset correctness or complete raw-history branch masses;
3. a multi-round detector/observable Record law;
4. monotone bond reduction under repeated measurement;
5. a qutrit or leakage-capable tableau backend;
6. a matched runtime, memory, or accuracy advantage over full PEPS.

Any statement in those six categories is killed unless another source or an
independent target derivation and experiment closes it. The source's general
\(k\chi\) upper bound is not an empirical efficiency result, and a possible
reduction from \(16\chi\) to \(4\chi\) in a better-connected tensor network
does not include contraction cost, environment accuracy, branching, or
Record observables.

## Source-local verdict

- `read_status: complete`
- `evidence_status: persisted`
- stabilizer-basis completeness: `closed`
- Clifford coefficient-state invariance: `closed`
- two-term non-Clifford update: `closed_as_source_mechanism`
- published multi-term factorization statement: `closed_as_formal_source_statement`
- single selective Pauli measurement: `closed_by_explicit_case_split`
- uniform Lemma 3 coefficient rule at \(\hat n=0\): `contradicted`
- flawless printed measurement proof: `contradicted`
- \(k\chi\) Schmidt-rank upper bound: `closed`
- claim that the displayed expansion is already Schmidt decomposed: `contradicted`
- reset and complete Record law: `missing`
- PEPS/QEC implementation and matched efficiency: `missing`
- qutrit/leakage backend: `missing`
