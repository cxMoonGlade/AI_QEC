# Source-only claim audit — Kim, Oh, and Kim, arXiv:2607.03939v1

Date: 2026-07-27

Source artifact: `docs/papers/2607.03939v1.pdf`

Source SHA-256:
`f02ec3815f3776c25b2e4a460eaaea2988b180deaecf9b602d4c0017c903cb9b`

Read status: `complete`

Evidence status: `persisted`

Independent review status: `passed`

Review basis:
`docs/simulator_validation/KIM_2607_03939V1_INDEPENDENT_SOURCE_REREVIEW_ROUND2_2026-07-27.md`

Review basis SHA-256:
`99e4db26c34834564b294dfe7a08cec2d744af0883a2db670f4b454a8cf4c9a6`

Admission reviewer: `independent_kim_2607_source_rereview_round2_2026_07_27`

Revision basis:
`docs/simulator_validation/KIM_2607_03939V1_INDEPENDENT_SOURCE_REVIEW_2026-07-27.md`

The complete 30-page PDF, including the main article, End Matter, and
Supplemental Material, was read in source order. Load-bearing equations and
claims were additionally checked in rendered pages: source identity and qutrit
definitions on PDF pp. 1--2 and 8; the claimed optimal circuit, numerical
results, and scope on pp. 3--5; the 90-class quotient on p. 9; the boundary
lemma on p. 12; canonical-form propagation, characteristic polynomials,
majorization, and Theorem 1 on pp. 17--19; the post-sweep result on p. 21; and
the symmetry-classification proofs on pp. 22--25. Text extraction was used for
navigation, not as a substitute for those visual checks.

This packet is source-only. It does not treat the paper as evidence for a
project implementation, a PEPS residual, a QEC instrument, or qutrit leakage.

## Assigned closure rows

| row | source location | source says | source does not say | status |
|---|---|---|---|---|
| qutrit generalized-Pauli and Clifford setup | PDF p. 2; SM PDF pp. 8--9, Eqs. (S1)--(S11) | The local qutrit Paulis, Fourier, phase, and SUM gates generate the qutrit Clifford framework used by the algorithm. | It does not define a leakage subspace, leakage channel, seepage/return mechanism, or measurement instrument. | `closed` for qutrit Clifford algebra; `missing` for leakage/QEC promotion |
| qutrit CAMPS ansatz | PDF p. 2, Eq. (1) and Fig. 1 | The source uses a one-dimensional qutrit MPS residual augmented by a sequential two-site Clifford circuit. | It does not implement GCAMPS circuit sampling, PEPS/CAPEPS, or a two-dimensional contraction. | `closed` for CAMPS-DMRG |
| active frame update | PDF p. 2, Fig. 1 and paragraph below Eq. (1) | The source prints the simultaneous active update \(\lvert\psi\rangle\mapsto C_{\rm opt}\lvert\psi\rangle\), \(H\mapsto C_{\rm opt}HC_{\rm opt}^\dagger\). This preserves the expectation because \(\langle C\psi\rvert CHC^\dagger\lvert C\psi\rangle=\langle\psi\rvert H\lvert\psi\rangle\). | It does not present the distinct passive-coordinate pullback obtained by holding the physical Hamiltonian fixed, for which the residual-frame operator would be \(C^\dagger H C\). | `closed` for the source's active simultaneous convention |
| reported 90 candidates | PDF p. 2; SM PDF p. 9, Eqs. (S6)--(S7) | After projectivizing by Paulis, the source counts 90 left cosets of the local symplectic subgroup in \(\mathrm{Sp}(4,\mathbb F_3)\), because left local gates do not change bipartite entanglement. | It does not establish a double-sided local-equivalence classification or list executable representatives in this paper. | `closed` for the printed one-sided count only |
| numerical qutrit CAMPS-DMRG result | PDF pp. 2 and 4, Figs. 2--3; SM PDF pp. 13--14, Figs. S1--S2 | For selected spin-1 and three-state-clock workloads, the source reports lower energy error and lower residual-MPS entanglement at fixed displayed bond dimension than standard DMRG, using a \(\chi=1000\) DMRG result as reference in the main benchmarks. | It gives no matched runtime, peak-memory, or asymptotic comparison and no independent exact reference for the largest benchmark. | `closed` for the displayed empirical comparisons |
| generalized KW circuit | PDF p. 3, Eq. (4); SM PDF p. 9, Eqs. (S10)--(S11) | The sequential circuit \(U_{N-1,N}\cdots U_{1,2}\), with \(U_{j,j+1}=X_{j+1}^2U^{\rm SUM}_{j,j+1}\), is the circuit selected and analyzed. | The source does not establish that every qutrit CAMPS workload selects this circuit. | `closed` with workload scope |
| exact optimality theorem | SM PDF p. 19, Theorem 1 and Eq. (S60) | For the specified AKLT state with \(L=R=e_\uparrow\), a greedy left-to-right sweep selecting the best two-qutrit Clifford at each bond chooses the stated \(U_{j,j+1}\). | It is not a global optimization over all Clifford circuits, boundary states, sweep schedules, Haldane-phase states, or perturbed tensors. | `closed` at theorem scope only |
| post-sweep local optimum | SM PDF pp. 20--21, Eqs. (S63)--(S65) and Table S3 | For the displayed KW-transformed AKLT construction, the source reports that no further two-site Clifford reduces the inspected bond entanglement, including separate boundary checks. | It is not a theorem against deeper/nonlocal circuits or non-Clifford disentanglers. | `closed` at source scope |
| robustness statement | PDF p. 3; SM PDF p. 19, Eq. (S61) | The source computes an approximately 0.35 entropy gap between its optimal and next-best gate types over the canonical interval and interprets it as robustness to small deviations. | It supplies no perturbation norm, admissible radius, or theorem mapping tensor perturbation to preservation of the optimizer. | `closed` as an interpretation; quantitative robustness `missing` |
| Haldane-phase extension | PDF p. 3, paragraphs surrounding Eq. (4); PDF p. 5, Discussion | The source combines the exact AKLT theorem with numerical CAMPS-DMRG observations in selected Haldane models and says the circuit is optimal throughout the Haldane phase. | The exact proof is only for the specified AKLT state and greedy sweep, so a phase-wide theorem is not established. | `closed` as source wording; phase-wide proof `missing` |
| transformed locality | PDF p. 3, Eq. (8); SM PDF pp. 10--12, Lemma 2 | For a two-site operator in the stated interior range, the transformed operator has support on at most three sites iff it commutes with \(Z_jZ_{j+1}\). | This is not a generic locality guarantee for arbitrary circuit perturbations or QEC noise terms. | `closed` |
| symmetry and SSB results | PDF pp. 3--5, Eqs. (9)--(12); SM PDF pp. 22--30 | The source classifies on-site product symmetries of its transformed Hamiltonians and derives AKLT order parameters and edge actions. | The BLBQ proof compresses several support-sector coefficient checks into prose rather than displaying the full algebra; none of these results supplies a QEC Record law. | `closed` for source claims; compressed replay noted |
| measurement--reset--Record bridge | full source scope, represented by PDF p. 5, Discussion | The source studies variational ground-state DMRG and unitary Clifford disentangling. | It gives no selective measurement, Born branch mass, reset map, raw-history law, detector/observable fold, conditional fidelity, or Record total variation. | `missing` |
| PEPS/CAPEPS bridge | full source scope, represented by PDF p. 5, Discussion | The source mentions extending CAMPS-based DMRG to general qudit systems as future work. | It supplies no PEPS ansatz, PEPS contraction/update, two-dimensional benchmark, or CAPEPS correctness/resource result. | `missing` |

## Notation ledger

| symbol | source meaning | type / range | fixed or variable | exact source location |
|---|---|---|---|---|
| \(X,Z\) | generalized single-qutrit Pauli shift and phase operators | \(X^3=Z^3=I\), \(ZX=\omega XZ\), \(\omega=e^{2\pi i/3}\) | fixed generators | PDF p. 1; SM PDF p. 8, Eq. (S1) |
| \(H^{(3)},S^{(3)},U^{\rm SUM}\) | Fourier, phase, and controlled-addition Clifford generators | qutrit Clifford gates | fixed generators | PDF p. 2; SM PDF pp. 8--9, Eqs. (S4)--(S5) |
| \(A_j^{s_j}\) | local qutrit MPS tensor | \(\chi_{j-1}\times\chi_j\) matrix for \(s_j\in\{0,1,2\}\) | variational | PDF p. 2, Eq. (1) |
| \(C\) | accumulated two-site Clifford circuit augmenting the MPS | sequential Clifford circuit | variational | PDF p. 2, Fig. 1 and following text |
| \(C_{\rm opt}\) | product of gates selected during a DMRG sweep | ordered product used in the source's simultaneous active state-and-Hamiltonian update | varies per sweep | PDF p. 2, paragraph below Eq. (1) |
| \(U_{j,j+1}\) | local generalized-KW gate | \(X_{j+1}^2U^{\rm SUM}_{j,j+1}\) | fixed gate type | PDF p. 3, Eq. (4) |
| \(a_j\) | scalar canonical-form parameter | recurrence \(a_{j+1}=(2-a_j)/3\), with \(a_j\in[4/9,2/3]\) in Theorem 1 | sweep-dependent | PDF p. 3, Eqs. (5)--(7); SM PDF p. 19, Eq. (S60) |
| \(T_t\) | one of ten characteristic-polynomial types induced by the 90 candidate representatives | \(t=0,\ldots,9\) | candidate class | SM PDF p. 18, Table S2 |
| \(\lambda_\pm\) | two nonzero squared Schmidt values after the stated local update | functions of \(a\) | sweep-dependent | SM PDF p. 17, Eq. (S48) |
| \(G_{\rm prod}(H)\) | group of on-site product symmetries commuting with \(H\) | subgroup of \(U(3)^{\otimes N}\) | Hamiltonian-dependent | SM PDF p. 21, Eq. (S66) |

## Operation replay

| input | transformation | assumption | output | exact source location | replay status |
|---|---|---|---|---|---|
| qutrit Hamiltonian as generalized-Pauli strings and a qutrit MPS | perform a two-site DMRG update and test two-site Clifford disentanglers before the SVD | Hamiltonian remains a manageable Pauli-string sum; local representative set is available | updated MPS and selected local Clifford | PDF p. 2, Fig. 1 and algorithm paragraph | `closed` at high level; implementation details absent |
| selected local Cliffords and the current state--Hamiltonian pair | accumulate the gates in sweep order and actively transform both state and Hamiltonian by the same \(C_{\rm opt}\) | \(C_{\rm opt}\) is unitary | transformed pair \((C_{\rm opt}\lvert\psi\rangle, C_{\rm opt}HC_{\rm opt}^\dagger)\) with invariant expectation value | PDF p. 2, paragraph below Eq. (1) | `closed` for the active simultaneous update; this is distinct from a passive residual-frame pullback |
| two-qutrit projective Clifford group | quotient left multiplication by local qutrit Clifford freedom in the symplectic representation | only bipartite entanglement after the gate is the objective | 90 left-coset representatives in count | SM PDF p. 9, Eqs. (S6)--(S7) | `closed` for the count; representative enumeration absent |
| canonical tensor \(B_j\) and AKLT tensor \(A_{j+1}\) | apply \(U_{j,j+1}\), reshape, and SVD | canonical conditions in Eq. (S39) | canonical \(B_{j+1}\), recurrence for \(a\), two Schmidt values | SM PDF pp. 16--17, Proposition 1 and Eqs. (S41)--(S52) | `closed` |
| each of 90 candidate classes | form \(F(\nu,a)=\widetilde\Theta^\dagger\widetilde\Theta\) and compare characteristic-polynomial roots | Table S2 polynomials and normalization | majorization ordering and locally optimal SUM-type gate | SM PDF pp. 17--19, Eqs. (S53)--(S59) | `closed` for printed classification; no executable representatives supplied |
| left boundary AKLT tensor | recursively apply the locally optimal gate from left to right | \(L=R=e_\uparrow\) and the stated greedy schedule | \(U_{\rm KW}\) selected across the chain | SM PDF p. 19, Theorem 1 | `closed` at theorem scope |
| selected model Hamiltonians | conjugate generalized Pauli strings with \(U_{\rm KW}\) | source algebra and stated boundary conditions | local transformed Hamiltonians and symmetry analysis | SM PDF pp. 9--12 and 22--30 | `closed` for displayed models |

## Project application

This source is useful for only two narrow project-facing roles.

First, it independently demonstrates that the Clifford-augmented tensor-network
idea is not intrinsically qubit-only: a qutrit MPS can be paired with generalized
Clifford generators, and a source-specific one-sided quotient reduces a local
entanglement search to 90 classes. This is adjacent algebraic evidence for a
future qutrit residual, not a qutrit-leakage backend.

Second, it shows why a learned/optimized Clifford layer can have physical
structure rather than being only a compression heuristic. Its exact optimality
claim is nevertheless limited to a specified AKLT boundary state and greedy
left-to-right sweep. The broader Haldane-phase wording is supported by selected
numerics, not by the theorem.

The source cannot be used to justify CAPEPS, a two-dimensional residual, a
measurement/reset instrument, Born branch accounting, detector Records,
Record-TV, or an efficiency advantage over full PEPS. Its printed Hamiltonian
formula is internally consistent as an active simultaneous state-and-Hamiltonian
update. A CAPEPS implementation that instead holds the physical Hamiltonian
fixed must explicitly use the distinct passive residual-frame pullback.

## Competing evidence and kill conditions

- Hostens--Dehaene--De Moor is the separate primary source for arbitrary-
  dimension stabilizer and Clifford algebra. This paper's 90-count is a
  source-specific one-sided entanglement quotient, not a substitute for that
  general formalism.
- Harper et al., arXiv:2605.29514v1, is the direct GCAMPS/QEC continuation. This
  qutrit DMRG paper does not replace Harper as the syndrome-circuit source.
- Any claim of a phase-wide exact optimality theorem is killed by Theorem 1's
  explicit \(L=R=e_\uparrow\), AKLT-state, and greedy-sweep restrictions.
- Any inference from the entropy gap to a certified perturbation radius is
  killed unless a separate perturbation theorem supplies the norm and radius.
- Any claim that the 90 classes are double-sided local-equivalence classes is
  killed by the explicit left-coset construction on PDF p. 9.
- Any claim of qutrit leakage support is killed unless a separate source and
  implementation define leakage states, channels, measurements, and return.
- Any PEPS, Record-faithfulness, or resource-scaling transfer is killed without
  a separate mechanism and target experiment.

## Source-local verdict

- `read_status: complete`
- `evidence_status: persisted`
- `independent_source_review: pending`
- qutrit generalized-Clifford algebra: `closed`
- source-reported 90 one-sided candidate classes: `closed`
- qutrit CAMPS-DMRG numerical comparisons: `closed_at_workload_scope`
- exact AKLT greedy-sweep theorem: `closed_at_theorem_scope`
- phase-wide exact optimality: `missing`
- quantitative perturbation robustness: `missing`
- active simultaneous state/Hamiltonian frame update: `closed`
- qutrit leakage mechanism: `missing`
- PEPS/CAPEPS mechanism: `missing`
- measurement--reset--Record bridge: `missing`

Admission remains pending an independent full-source semantic review and direct
schema validation of the corresponding source-only note.
