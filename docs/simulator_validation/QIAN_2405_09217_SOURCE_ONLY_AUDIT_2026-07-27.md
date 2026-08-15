# Source-only claim audit — Qian, Huang, and Qin, arXiv:2405.09217v2

Date: 2026-07-27

Source artifact: `docs/papers/2405.09217v2.pdf`

Source SHA-256:
`13e1369ff2817d5dc20c595716b2f89a505c239d245603ef89811b51e672e2b7`

Read status: `complete`

Evidence status: `persisted`

Independent review status: `passed`

Review basis:
`docs/simulator_validation/QIAN_2405_09217_INDEPENDENT_SOURCE_REREVIEW_2026-07-27.md`

Admission reviewer: `independent_qian_2405_source_rereview_2026_07_27`

Revision basis:
`docs/simulator_validation/QIAN_2405_09217_INDEPENDENT_SOURCE_REVIEW_2026-07-27.md`

The six-page source was traversed in full, and all six PDF pages were rendered
and visually inspected. The checks covered source identity and scope, Eqs.
(1)--(5), Fig. 1, the reported 720-candidate statement, the numerical figures,
the runtime statement, the PEPS sentence, the Conclusion, and both parts of
the local-minimum limitation. Text extraction was used only for navigation and
full-text scope checks.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| Clifford-augmented ansatz | PDF p. 2, Eq. (2) and Fig. 1(a) | The CAMPS variational state is \(C\lvert\mathrm{MPS}\rangle\), with a Clifford circuit acting on MPS physical degrees of freedom. | It does not define a PEPS residual, a stabilizer-tableau execution carrier, or a syndrome-circuit instrument. | `closed` for the CAMPS ansatz |
| local truncation criterion | PDF p. 2, Fig. 1(b); PDF p. 3, local-search paragraph | The method applies a local two-qubit Clifford before SVD truncation and says it minimizes truncation loss/discarded singular values. | It gives no scalar objective, discarded-weight formula, norm, retained-rank convention, Rényi-2 expression, or purity expression. | `closed` for the qualitative source criterion; `missing` for an exact scalarization; the prior attribution that Qian states a Rényi-2 objective is `contradicted` as a citation claim |
| reported local candidate set | PDF p. 3, local-search paragraph | The paper reports 720 two-qubit Clifford candidates after excluding what it calls “phase redundancy” and says it calculates singular values for all of those candidates. | It does not define the equivalence relation, enumerate representatives, or prove that this is a complete two-qubit Clifford quotient. | `closed` for the paper-reported 720-candidate search; `missing` for a quotient/completeness claim |
| Hamiltonian update | PDF p. 3, Eq. (5) and following paragraph | The selected Clifford conjugates \(H\) to \(H'=CHC^\dagger\), and each Pauli string remains a Pauli string. | It does not give a CAPEPS frame/residual update or a selective-measurement update. | `closed` |
| energy benchmark | PDF p. 3, Fig. 2; PDF p. 4, Fig. 4 and surrounding text | On the selected snake-mapped \(J_1-J_2\) Heisenberg workloads, the paper reports lower source-defined relative ground-state-energy errors for CAMPS than for the shown MPS comparisons. The \(J_2=0\) discussion invokes QMC references; the Fig. 4 discussion uses a \(D=10000\) MPS energy as reference. | It does not establish an arbitrary-model or asymptotic accuracy guarantee. | `closed` for the reported workloads |
| residual-MPS entropy benchmark | PDF p. 3, Fig. 3 discussion; PDF p. 4, Fig. 3 caption | The paper reports that the center-bond entropy in the MPS part is nearly identical for CAMPS and MPS below a critical bond dimension, then saturates for CAMPS while continuing to rise for MPS above that threshold. | It does not establish the same behavior for PEPS or syndrome circuits. | `closed` for the reported workloads |
| reported runtime | PDF p. 4, Discussion | For the reported \(10\times10\) OBC Heisenberg calculation, the CAMPS/MPS calculation-time ratio is about 1.2 and is said to approach one as bond dimension grows. | It does not establish runtime, memory, bond, or Record efficiency for PEPS, XZZX, measurement branching, or coherent circuit simulation. | `closed` for the stated workload; `missing` for CAPEPS |
| PEPS extension | PDF p. 4, Discussion | The authors say the Fig. 1(b) framework can be readily extended to tensor-network states such as PEPS. | The paper supplies no PEPS construction, contraction rule, experiment, correctness theorem, complexity result, or implementation. | `missing` for a CAPEPS mechanism or result |
| local-minimum failure regime | PDF p. 4, Discussion; PDF p. 6, Ref. [54] | The paper warns that local Clifford optimization may encounter local minima; Ref. [54] reports this empirically at small bond dimension and recommends not applying Clifford circuits there. | It does not prove a global optimum or monotone benefit. | `closed` |
| measurement--reset--Record bridge | Full-text scope from Abstract through Conclusion, represented by PDF p. 5, Conclusion | The source addresses ground-state DMRG optimization. | It does not define selective Born branches, reset, raw-history mass, multi-round detector Records, conditional-state fidelity, or Record total variation. | `missing` |

## Notation ledger

| symbol | source meaning | type / range | fixed or variable | exact source location |
|---|---|---|---|---|
| \(M_i^{\sigma_i}\) | local MPS tensor | rank three; physical dimension \(d\), auxiliary dimension \(D\) | variational | PDF p. 2, Eq. (1) |
| \(C\) | Clifford circuit in Eq. (2), and a selected two-qubit Clifford in a local update | Clifford unitary; the source reports a 720-candidate local search after excluding what it calls phase redundancy | variable | PDF p. 2, Eq. (2) and Fig. 1(b); PDF p. 3, local-search paragraph |
| \(H=\sum_i a_iP_i\) | spin-\(\tfrac12\) Pauli-string Hamiltonian | \(P_i\) is an \(N\)-site Pauli string | fixed problem input before frame updates | PDF p. 2, Eq. (3) |
| \(H_{\mathrm{eff}}\) | two-site DMRG effective Hamiltonian at \(k,k+1\) | sum of left environment, two local Pauli factors, and right environment | changes with sweep position | PDF p. 2, Eq. (4) |
| \(\lvert\phi\rangle\) | optimized local ground state of \(H_{\mathrm{eff}}\) | two-site state in the local DMRG problem | variable per local solve | PDF p. 2, paragraph after Eq. (4) |
| discarded singular values | source wording for the local truncation criterion | singular values removed by the subsequent SVD truncation; scalarization unspecified | candidate-dependent | PDF p. 2, Fig. 1(b); PDF p. 3, local-search paragraph |
| \(H'=CHC^\dagger\) | Hamiltonian after the selected Clifford-frame update | Pauli-string sum in which each \(P_i\) maps to a Pauli string | changes after each selected \(C\) | PDF p. 3, Eq. (5) |
| \(D\) | MPS bond dimension | positive integer | swept in the numerical figures | PDF p. 2, Eq. (1); PDF pp. 3--4, Figs. 2--4 |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| Pauli-string Hamiltonian \(H\) and current MPS environments | Form the two-site effective Hamiltonian and solve \(H_{\mathrm{eff}}\lvert\phi\rangle=E_g\lvert\phi\rangle\). | Standard two-site DMRG environment construction used by the source. | optimized local state \(\lvert\phi\rangle\) | PDF p. 2, Eq. (4) and adjacent text | `closed` |
| \(\lvert\phi\rangle\) and the paper-reported 720 candidates | Apply each reported candidate to \(\lvert\phi\rangle\) and calculate singular values. | The source says it has excluded what it calls phase redundancy; it does not define the quotient or prove completeness. | candidate-dependent SVD spectra | PDF p. 3, local-search paragraph | `closed` for the reported procedure; quotient/completeness `missing` |
| candidate-dependent SVD spectra | Compare truncation loss/discarded singular values and select a candidate. | The scalarization, norm, and retained-rank convention are not specified by the source. | source-reported locally selected \(C\) | PDF pp. 2--3, Fig. 1(b) and local-search paragraph | `closed` only at the qualitative source level |
| selected \(C\lvert\phi\rangle\) | Truncate its SVD and update the two MPS tensors. | No global-state or observable error bound is asserted. | truncated local MPS update | PDF p. 2, Fig. 1(b) and final paragraph | `closed` |
| selected \(C\) and \(H\) | Conjugate every Pauli string, \(H'=CHC^\dagger\). | \(C\) acts on the selected two sites and maps Pauli strings to Pauli strings. | transformed Hamiltonian for subsequent DMRG steps | PDF p. 3, Eq. (5) | `closed` |
| transformed Hamiltonian and updated MPS | Continue the DMRG sweep with updated environments. | The Hamiltonian transformation is maintained consistently in the source algorithm. | next local DMRG problem | PDF p. 3, paragraph following Eq. (5) | `closed` |

## Project application

The source supports only an adjacent MPS/DMRG design:

- a local two-qubit Clifford can be searched before an SVD using the source's
  qualitative truncation-loss/discarded-singular-value criterion;
- the source reports evaluating 720 candidates after excluding what it calls
  phase redundancy, but it does not establish the relevant quotient or
  completeness;
- a Pauli-string Hamiltonian can be updated under the selected Clifford
  without expanding one Pauli string into a sum of Pauli strings.

The source does not support a claim that Qian et al. state a Rényi-2/purity
objective. It also does not define the exact scalar truncation objective
needed to replay candidate ordering independently.

The one-sentence PEPS statement is a future-direction assertion, not a CAPEPS
algorithm, correctness result, or efficiency benchmark. No measurement,
reset, branch-mass, conditional-state, or Record claim may be mapped from this
source.

## Competing evidence and kill conditions

- Liu--Clark, arXiv:2412.17209v2, Sec. IV.A Eq. (19), is a separate admitted
  source for a Rényi-2-derived local objective. That objective must be cited
  and audited independently; it is not supplied by Qian et al.
- Any sentence claiming that Qian et al. state or derive a Rényi-2/purity
  objective is rejected by the explicit truncation-loss/discarded-singular-
  value terminology on PDF pp. 2--3.
- Any use of the reported number 720 as a complete Clifford quotient is killed
  unless a separate group-theoretic source defines the equivalence relation
  and establishes the representative count.
- Any PEPS/XZZX efficiency transfer is killed unless a separate source or
  target experiment includes PEPS contraction, branching, Record correctness,
  optimizer cost, and matched full-process resource accounting.

## Source-local verdict

- `read_status: complete`
- `evidence_status: persisted`
- `independent_source_review: passed`
- `review_basis: QIAN_2405_09217_INDEPENDENT_SOURCE_REREVIEW_2026-07-27.md`
- Clifford-augmented MPS/DMRG ansatz: `closed`
- qualitative truncation-loss/discarded-singular-value criterion: `closed`
- exact scalarization of the local objective: `missing`
- paper-reported 720-candidate search: `closed`
- Clifford quotient/completeness: `missing`
- prior attribution that Qian states a Rényi-2 objective: `contradicted_as_citation_claim`
- Hamiltonian conjugation rule: `closed`
- selected MPS/DMRG benchmark observations: `closed`
- PEPS implementation/correctness/efficiency: `missing`
- measurement--reset--Record bridge: `missing`
