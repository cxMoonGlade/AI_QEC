# Source-only claim audit — Masot-Llima et al., arXiv:2602.15942v2

Date: 2026-07-27

Source artifact: `docs/papers/2602.15942v2.pdf`

Source SHA-256:
`ec572bd96d4a937667c2c6fb9c1996da92ff359072050c2fe47b501ed80aa83e`

Independent mathematical review:
`docs/simulator_validation/MASOT_2602_15942V2_INDEPENDENT_MATH_REVIEW_2026-07-27.md`

Independent mathematical review SHA-256:
`fc4527cc6ba9c052194c8eebbca93c9f8725e437af1c0afb7c3694c5bdcf108c`

Read status: `complete`

Evidence status: `persisted`

Independent review status: `passed_for_faithful_source_only_admission`

Review basis:
`docs/simulator_validation/MASOT_2602_15942V2_INDEPENDENT_SOURCE_REVIEW_2026-07-27.md`

Independent review SHA-256:
`ba42c95d804e41968db329af82fd54d93d39d00369057036c13d75aa81da2feb`

Admission reviewer: `independent_masot_2602_source_review_2026_07_27`

Revision status: `source_only_review_pass_theorem_still_fails_as_printed`

The full 17-page v2 source was traversed. PDF pages 1--3, 5--7, 9,
and 13--17 were rendered and visually inspected for every source claim and
gap retained in the companion note. Text extraction was used only for
navigation. This packet separates the source's statements from the
project-level mathematical adjudication below.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| Clifford tensor-network representation | Sec. II.A, Definition 1 and Eq. (1), PDF p. 2 | A CTN represents \(\lvert\psi\rangle=C\lvert\psi_T\rangle\), with a Clifford component and a tensor-network component updated together. | It does not make this representation a PEPS implementation or a measurement instrument. | `closed` |
| heuristic cooling update | Sec. II.B, Definition 2, Eq. (2), and Fig. 2, PDF pp. 2--3 | A local sweep tests Clifford candidates and evaluates an entropy objective, retaining an improving candidate up to depth \(d\). | It does not give a generic global optimum or a complete objective prescription for every \(k>2\) use. | `closed` |
| printed two-qubit relation and count | Sec. II.B local-equivalence paragraph, PDF p. 3 | It defines \(V=(L_1\otimes L_2)U(R_1\otimes R_2)\) and then reports 20 representatives. | It does not enumerate the 20 gates or derive that count from the printed double-sided relation. | `contradicted` |
| exact-cooling sufficient construction | Definition 3 and Appendix A, PDF pp. 4 and 12--13 | For an affected separable stabilizer site, a Pauli-string rotation is decomposed into a local rotation and a controlled-Pauli cascade absorbed into the Clifford component. | This sufficient construction does not establish the necessity direction of Theorem III.1. | `closed_as_source_statement` |
| universal single-qubit no-go statement | Sec. III.C, Theorem III.1, PDF pp. 6--7 | The paper states that the qualifying unitary is Clifford iff the fixed last-qubit input is stabilizer. | The theorem statement does not unambiguously freeze whether \(U\) is existential or universal, or whether it is fixed across \(\theta\). | `contradicted — FAIL_AS_PRINTED` |
| Appendix B proof | Appendix B, Eqs. (B1)--(B32), PDF pp. 13--17 | The paper supplies a two-block unitary decomposition, a purported Gram--Schmidt step, and a purity argument as its proof. | It supplies no independent proof that avoids the failed steps identified by the bound mathematical review. | `contradicted — FAIL_AS_PRINTED` |
| reported MPS workload observations | Secs. III.A and IV, Figs. 4, 5, and 7--9, PDF pp. 5 and 7--8 | For the selected random Clifford-plus-rotation MPS workloads, the paper reports no clear improvement from \(k=3\) or greater tested sweep depth and reports accumulation delayed by smaller rotation angles. | These finite-workload observations are not an asymptotic, PEPS, or Record-law result. | `closed_for_reported_workloads` |
| PEPS scope | Sec. V future-work paragraph, PDF p. 9 | Higher-dimensional tensor networks are future work. | No PEPS construction, contraction rule, benchmark, correctness theorem, or resource comparison is supplied. | `missing` |
| measurement--reset--Record scope | complete source scope, with Sec. V on PDF p. 9 | The source treats unitary Clifford/TN simulation and entanglement cooling. | No selective measurement, reset, Born branch mass, conditional trajectory, detector Record, or Record-law metric is defined. | `missing` |

## Notation ledger

| symbol | source meaning | type / range | fixed or variable | exact source location |
|---|---|---|---|---|
| \((C,T)\) | Clifford transformation plus tensor-network residual | hybrid representation | updated jointly | Sec. II.A, Definition 1, PDF p. 2 |
| \(\lvert\psi_T\rangle\) | state represented by the tensor-network component | MPS in the reported experiments | variable | Eq. (1), PDF p. 2 |
| \(\chi\) | tensor-network bond dimension | positive integer | simulation setting | Sec. II.A and Fig. 9 |
| \(U_C\) | Clifford inserted as \(I=U_CU_C^\dagger\) during cooling | Clifford unitary | optimized locally | Sec. II.B, PDF p. 2 |
| \(k\) | locality of a cooling update | positive integer; reported comparisons use 2 and 3 | algorithm setting | Definition 2 and Sec. III.A |
| \(d\) | number of cooling sweeps called depth | positive integer | algorithm setting | Definition 2 and Fig. 5 |
| \(S(\rho)\) | printed entropy objective | \(-\sum_i\rho_i\log_2\rho_i\), with \(\rho_i\) described as SVD values | evaluated per candidate | Eq. (2), PDF p. 3 |
| \(L_i,R_i\) | local single-qubit Cliffords in the printed relation | elements of \(\mathcal C_1\) | arbitrary | Sec. II.B, PDF p. 3 |
| \(R_C=\alpha I+\beta P\) | Clifford-conjugated Pauli rotation | \(P=P_1\otimes\cdots\otimes P_n\) | problem operation | Sec. III.C, PDF p. 6 |
| \(\lvert\phi_n\rangle\) | initially separable last-qubit state | one-qubit pure state | fixed in the theorem prose | Eqs. (4) and (6), PDF p. 6 |
| \(U\) | proposed state-agnostic disentangling unitary | unitary; dependence on \(\theta\) is ambiguous between theorem and proof | fixed across \(\lvert\Psi\rangle\) in the proof discussion | Theorem III.1 and Appendix B, PDF pp. 6 and 15 |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| CTN pair \((C,T)\) | update the Clifford and TN components while preserving \(\lvert\psi\rangle=C\lvert\psi_T\rangle\) | Clifford action can be kept in \(C\); non-Clifford action updates \(T\) | hybrid physical-state representation | Sec. II.A, Definition 1 and Eq. (1), PDF p. 2 | `complete` |
| local residual tensors | insert \(I=U_CU_C^\dagger\), apply \(U_C\) to the TN, and absorb \(U_C^\dagger\) into the Clifford frame | candidate \(U_C\) is Clifford | unchanged physical state with a different residual representation | Sec. II.B, PDF p. 2 | `complete` |
| a contiguous \(k\)-site block | evaluate local Clifford candidates with the printed entropy objective and retain an improvement | finite sweep depth; for \(k>2\) the paper acknowledges an objective choice | locally cooled residual | Definition 2, Eq. (2), and Fig. 2, PDF pp. 2--3 | `complete` |
| \(\mathcal C_2\) with 11,520 elements | quotient by the printed relation \(V=LUR\) | local operations on both sides are asserted not to alter entanglement | paper-reported 20 representatives | Sec. II.B, PDF p. 3 | `contradicted`: the printed relation does not derive 20 |
| Pauli-string rotation and an affected separable stabilizer factor | move a controlled-Pauli cascade into the Clifford component and leave a local rotation on the factor | the chosen site is a separable stabilizer and is acted on nontrivially | exact source-defined cooling construction | Definition 3 and Appendix A, PDF pp. 4 and 12--13 | `complete_as_sufficient_construction` |
| arbitrary candidate \(U\), fixed \(\lvert\phi_n\rangle\), and arbitrary \(\lvert\Psi\rangle\) | assert Eq. (B1), use Eq. (B5), infer collinearity in Eqs. (B6)--(B8), then use the general purity bounds | the two-block form is asserted for every unitary and the printed orthonormalization is treated as valid | Theorem III.1 iff conclusion | Appendix B, Eqs. (B1)--(B32), PDF pp. 13--17 | `FAIL_AS_PRINTED` |
| random Clifford-plus-rotation MPS circuits | compare \(k=2\) versus \(k=3\), sweep depths, and rotation angles | reported finite sizes and ensembles | workload-specific entropy and bond-growth observations | Secs. III.A and IV, Figs. 4, 5, and 7--9 | `complete_for_reported_workloads` |

The replay is complete because every transformation in the source's chain has
been reconstructed. `complete` does not mean that the theorem proof passes;
the theorem replay terminates in `FAIL_AS_PRINTED`.

## Independent mathematical adjudication

The bound independent review is a project-level mathematical audit, not a
`paper_fact`. Its SHA-256 is fixed above. It establishes all of the following:

1. Eq. (B1) is false for a general bipartite unitary; a CNOT maps
   \(\lvert+0\rangle\) to a Bell state and cannot have the asserted fixed
   target-output block form.
2. Eq. (B5) is not Gram--Schmidt; the denominator should involve
   \(\sqrt{1-|\langle\Omega_1|\Omega_2\rangle|^2}\) away from the collinear
   case.
3. Eqs. (B6)--(B8) lose a general phase and a \(P_B\) factor; Eq. (B18) does
   not solve Eq. (B17) as printed.
4. The general proof omits the \(\beta\delta=0\) branches, while Eqs.
   (B25)--(B32) contain independent projector, denominator, and equality-case
   defects.
5. The literal theorem is refuted even with an affected stabilizer target:
   for \(P=X\otimes X\), \(\lvert\phi_2\rangle=|0\rangle\), and
   \(D=\mathrm{CNOT}_{2\to1}\), the non-Clifford
   \(U=(T\otimes I)D\) disentangles for every \(\theta\) and
   \(\lvert\Psi\rangle\).
6. Under the proof's pointwise-angle reading, \(\theta=\pi/4\) and
   \(U=R_\theta^\dagger\) give a Clifford cancellation for any target state.
7. The number 20 is the one-sided index \(11520/24^2\), not the number of
   classes under the printed double-sided relation.

Therefore the no-go theorem is `FAIL_AS_PRINTED`, not merely “pending a typo
fix.” A narrower existential theorem with a genuinely non-Clifford angle and
fully frozen dependencies remains open and would require a new proof.

## Project application

The source supports background for a hybrid Clifford/TN representation, a
local cooling heuristic, and a sufficient exact construction on an affected
separable stabilizer factor. It does not establish a two-dimensional residual
algorithm, a measurement instrument, finite-bond Record faithfulness, or an
efficiency result.

For a fixed-input score \(f_\psi(U)=E(U\lvert\psi\rangle)\), post-action local
Cliffords preserve the score, while pre-action locals can change it. The
project may therefore use a 20-element catalogue only as an independently
validated one-sided output-local transversal. It may not inherit that design
from the source's printed double-sided explanation.

No CAPEPS limitation, residual-spreading theorem, or Record-law claim may be
derived from Theorem III.1. The paper may be cited only as stating the failed
theorem and as reporting its bounded MPS observations.

## Competing evidence and kill conditions

- Córcoles et al., arXiv:1210.7011v2, Supplement, PDF p. 8, gives a complete
  four-class local/CNOT-like/iSWAP-like/SWAP decomposition with counts
  \(576,5184,5184,576\); it does not call this a formal fixed-input quotient.
- A one-sided 20-representative implementation requires its own exact
  catalogue, action convention, disjoint-coverage check, and fixed-input
  invariance proof.
- Any sentence saying Masot et al. “prove” the universal no-go is killed by
  the independent mathematical review unless a new theorem statement and
  independent corrected proof are supplied.
- Any transfer from the reported one-dimensional MPS workloads to PEPS,
  selective branching, reset, runtime, memory, or Record TV is killed without
  a separate construction and target experiment.

## Source-local verdict

- `read_status: complete`
- `evidence_status: persisted`
- CTN representation: `closed`
- heuristic cooling procedure: `closed`
- printed double-sided 20-class bridge: `contradicted`
- exact stabilizer-factor cooling construction: `closed_as_source_statement`
- Theorem III.1 as a source statement: `closed_as_statement_only`
- Theorem III.1 as a mathematical no-go: `contradicted — FAIL_AS_PRINTED`
- Appendix B as a valid proof: `contradicted — FAIL_AS_PRINTED`
- reported MPS numerical observations: `closed_for_reported_workloads`
- PEPS mechanism/result: `missing`
- measurement--reset--Record bridge: `missing`

## Admission boundary

This revision has not received an independent source-only admission PASS.
The companion note must remain `admission_status = "draft_pending_review"`.
The reviser who incorporated the mathematical audit is not authorized to
self-approve the note, edit `CURRENT_CORPUS.toml`, or regenerate
`CONCEPT_INDEX.md`. A fresh reviewer must compare every note claim and locator
to the pinned PDF and separately accept this audit before admission.
