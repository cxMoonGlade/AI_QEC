+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2607.03939"
source_version = "v1"
source_uri = "https://arxiv.org/abs/2607.03939v1"
source_artifact = "docs/papers/2607.03939v1.pdf"
source_sha256 = "f02ec3815f3776c25b2e4a460eaaea2988b180deaecf9b602d4c0017c903cb9b"
title = "Disentangling Haldane Phase by Generalized Clifford Circuits"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/KIM_2607_03939V1_SOURCE_ONLY_AUDIT_2026-07-27.md"
audit_packet_sha256 = "85ea87de03027d8ddee61bea3bcdc952acbb7faeced9c393720cd8e689bd2613"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_kim_2607_source_rereview_round2_2026_07_27"
admission_date = "2026-07-27"
visually_checked_pages = [1, 2, 3, 4, 5, 8, 9, 12, 17, 18, 19, 21, 22, 23, 24, 25]
+++
# Full-text review — Kim, Oh, and Kim, “Disentangling Haldane Phase by Generalized Clifford Circuits”

## Source identity [paper_fact]
Fact ID: kim2607-source-identity
Source locator: PDF page 1, title block, author block, date, and arXiv footer
PDF page: 1
Claim: The source is the 30-page arXiv:2607.03939v1 preprint by Minsoo Kim, Changhun Oh, and Donghoon Kim, with a July 7, 2026 date printed on the title page.

## Qutrit Pauli setup [paper_fact]
Fact ID: kim2607-qutrit-pauli-setup
Source locator: PDF page 1, Setup and algorithm overview, final paragraph
PDF page: 1
Claim: The source defines qutrit shift and phase operators by \(X\lvert s\rangle=\lvert s+1\bmod 3\rangle\) and \(Z\lvert s\rangle=\omega^s\lvert s\rangle\), with \(\omega=e^{2\pi i/3}\).

## Qutrit Clifford generators [paper_fact]
Fact ID: kim2607-qutrit-clifford-generators
Source locator: PDF page 2, Setup and algorithm overview, first column
PDF page: 2
Claim: The source uses single-qutrit Pauli, Fourier, and phase gates together with the two-qutrit SUM gate as generators of its generalized Clifford framework.

## Qutrit MPS notation [paper_fact]
Fact ID: kim2607-qutrit-mps
Source locator: PDF page 2, Eq. (1) and following sentence
PDF page: 2
Claim: The source writes a qutrit MPS using physical labels \(s_j\in\{0,1,2\}\) and matrices \(A_j^{s_j}\) of size \(\chi_{j-1}\times\chi_j\).

## CAMPS ansatz [paper_fact]
Fact ID: kim2607-camps-ansatz
Source locator: PDF page 2, Fig. 1(a) and algorithm paragraph below Eq. (1)
PDF page: 2
Claim: The source prints the qutrit Clifford-augmented ansatz as \(\lvert\mathrm{CAMPS}\rangle=C\lvert\mathrm{MPS}\rangle\), where \(C\) is accumulated from selected two-site Clifford gates.

## Local Clifford selection [paper_fact]
Fact ID: kim2607-local-selection
Source locator: PDF page 2, algorithm paragraph below Eq. (1)
PDF page: 2
Claim: During a DMRG sweep, the source applies candidate two-site Clifford gates at each bond and selects a gate that maximally reduces the MPS entanglement across that bond.

## Printed Hamiltonian update [paper_fact]
Fact ID: kim2607-printed-hamiltonian-update
Source locator: PDF page 2, Fig. 1(b) and algorithm paragraph below Eq. (1)
PDF page: 2
Claim: The source prints the simultaneous Hamiltonian update as \(\widetilde H=C_{\mathrm{opt}}HC_{\mathrm{opt}}^\dagger\) and says generalized Pauli strings remain generalized Pauli strings under the Clifford conjugation.

## Main numerical comparison [paper_fact]
Fact ID: kim2607-main-numerical-comparison
Source locator: PDF page 2, Fig. 2 and final two paragraphs
PDF page: 2
Claim: For the displayed \(N=128\) Heisenberg and BLBQ workloads, the source reports lower ground-state energy error and lower residual-MPS entanglement for CAMPS-DMRG than for standard DMRG at the shown bond dimensions, using a \(\chi=1000\) DMRG calculation as reference.

## Generalized KW circuit [paper_fact]
Fact ID: kim2607-kw-circuit
Source locator: PDF page 3, Eq. (4)
PDF page: 3
Claim: The source defines \(U_{\mathrm{KW}}=U_{N-1,N}\cdots U_{2,3}U_{1,2}\) with \(U_{j,j+1}=X_{j+1}^2U^{\mathrm{SUM}}_{j,j+1}\).

## Canonical recurrence [paper_fact]
Fact ID: kim2607-canonical-recurrence
Source locator: PDF page 3, Eqs. (5)--(7)
PDF page: 3
Claim: For the source's canonical-form tensor, applying its local KW gate and an SVD produces another canonical-form tensor with parameter recurrence \(a_{j+1}=(2-a_j)/3\).

## Source phase-wide wording [paper_fact]
Fact ID: kim2607-phase-wide-wording
Source locator: PDF page 3, paragraph immediately following Eq. (4)
PDF page: 3
Claim: The source states that its analytic and numerical results imply that the generalized KW circuit is optimal throughout the Haldane phase.

## Locality criterion [paper_fact]
Fact ID: kim2607-locality-criterion
Source locator: PDF page 3, final paragraph
PDF page: 3
Claim: The source states that for a two-local operator \(O_{j,j+1}\), its generalized-KW transform remains local exactly when \([O_{j,j+1},Z_jZ_{j+1}]=0\), with the detailed interior-site statement supplied in its supplement.

## Long-range-order result [paper_fact]
Fact ID: kim2607-long-range-order
Source locator: PDF page 4, Fig. 3 and Eqs. (10)--(11)
PDF page: 4
Claim: The source reports nonzero long-distance \(S^z\) correlations in its transformed Haldane-phase workloads and derives limiting AKLT values \(1/4\) for the two-point function and \(\pm1/2\) for the one-point order parameter under the stated boundary labels.

## Qutrit future direction [paper_fact]
Fact ID: kim2607-qudit-future-direction
Source locator: PDF page 5, Discussion, second paragraph
PDF page: 5
Claim: The source identifies extension of CAMPS-based DMRG to general qudit systems, including ququarts, as future work.

## Projective qutrit Clifford definition [paper_fact]
Fact ID: kim2607-projective-clifford
Source locator: PDF page 8, Supplemental Material, Eqs. (S2)--(S4)
PDF page: 8
Claim: The supplement defines the projective generalized Pauli group and the qutrit Clifford group as its normalizer modulo global phase.

## Ninety one-sided classes [paper_fact]
Fact ID: kim2607-ninety-left-cosets
Source locator: PDF page 9, Supplemental Material, Eqs. (S6)--(S7)
PDF page: 9
Claim: The source computes \(\lvert\mathrm{Sp}(4,\mathbb F_3)\rvert=51840\) and divides by \(\lvert\mathrm{Sp}(2,\mathbb F_3)\rvert^2=24^2\) to obtain 90 left cosets after quotienting local single-qutrit Clifford freedom relevant to bipartite entanglement.

## Boundary disentanglement lemma [paper_fact]
Fact ID: kim2607-boundary-product-lemma
Source locator: PDF page 12, Supplemental Material, Lemma 1 and Eq. (S27)
PDF page: 12
Claim: For a nondegenerate eigenstate of a Hamiltonian commuting with the last-site \(Z_N\), the source proves that the last qutrit occupies only one computational-basis sector and is therefore unentangled from the preceding sites.

## Canonical propagation proposition [paper_fact]
Fact ID: kim2607-canonical-propagation
Source locator: PDF page 17, Supplemental Material, Eqs. (S48)--(S52)
PDF page: 17
Claim: The source derives two nonzero squared Schmidt values for the stated local update and proves that the resulting tensor preserves its canonical form with \(a'=(2-a)/3\).

## Candidate polynomial classification [paper_fact]
Fact ID: kim2607-polynomial-types
Source locator: PDF page 18, Supplemental Material, Table S2 and Lemma 3 opening
PDF page: 18
Claim: The source partitions its 90 candidates into ten characteristic-polynomial types and identifies the type containing the SUM-derived gate as \(T_0\).

## Exact AKLT greedy-sweep theorem [paper_fact]
Fact ID: kim2607-aklt-greedy-theorem
Source locator: PDF page 19, Supplemental Material, Theorem 1 and Eq. (S60)
PDF page: 19
Claim: For the AKLT state with \(L=R=e_\uparrow\), the source proves that sequentially selecting the entanglement-minimizing two-qutrit Clifford from left to right chooses \(U_{j,j+1}\) at every bond.

## Reported entropy gap [paper_fact]
Fact ID: kim2607-entropy-gap
Source locator: PDF page 19, Supplemental Material, Eq. (S61) and following paragraph
PDF page: 19
Claim: The source reports a minimum entropy gap of approximately 0.35 between the optimal gate type and the next-best type over its canonical interval and interprets the gap as evidence of robustness to small tensor deviations.

## Post-sweep local optimum [paper_fact]
Fact ID: kim2607-post-sweep-local-optimum
Source locator: PDF page 21, Supplemental Material, Table S3 and paragraphs following it
PDF page: 21
Claim: For the displayed KW-transformed AKLT state, the source reports that the identity class minimizes the next local Clifford update and that separate boundary checks also find no further entanglement reduction.

## On-site symmetry classification [paper_fact]
Fact ID: kim2607-onsite-symmetry
Source locator: PDF page 22, Supplemental Material, Proposition 2 and Eqs. (S68)--(S72)
PDF page: 22
Claim: For the stated transformed Heisenberg Hamiltonian with \(N\ge4\), the source classifies each on-site product symmetry as a right-boundary symmetry times a power of its global \(\mathbb Z_2\) generator.

## No matched resource benchmark [literature_gap]
Fact ID: kim2607-gap-matched-resources
Source locator: PDF page 5, Discussion
PDF page: 5
Claim: This source does not report matched runtime, peak memory, throughput, or asymptotic scaling for qutrit CAMPS-DMRG versus standard DMRG.
Gap scope: source_local

## No PEPS or CAPEPS construction [literature_gap]
Fact ID: kim2607-gap-peps
Source locator: PDF page 5, Discussion
PDF page: 5
Claim: This source does not provide a PEPS residual, two-dimensional Clifford-augmented tensor-network algorithm, PEPS contraction rule, CAPEPS implementation, or PEPS benchmark.
Gap scope: source_local

## No measurement--reset--Record instrument [literature_gap]
Fact ID: kim2607-gap-instrument
Source locator: PDF page 5, Discussion and documented full-text scope
PDF page: 5
Claim: This source does not define selective measurements, Born branch masses, reset maps, conditional trajectories, raw-history probabilities, detector Records, conditional fidelity, or Record total variation.
Gap scope: source_local

## No qutrit leakage model [literature_gap]
Fact ID: kim2607-gap-leakage
Source locator: PDF page 5, Discussion and documented full-text scope
PDF page: 5
Claim: Although the source uses spin-1 qutrits, it does not define computational-versus-leakage sectors, leakage or seepage channels, leakage measurement, or return dynamics.
Gap scope: source_local

## One-sided quotient only [literature_gap]
Fact ID: kim2607-gap-double-sided-quotient
Source locator: PDF page 9, Supplemental Material, paragraph containing Eq. (S7)
PDF page: 9
Claim: This source does not establish that its 90 left cosets are double-sided local-equivalence classes or a complete classification under independent local gates on both sides.
Gap scope: source_local

## No executable representative list [literature_gap]
Fact ID: kim2607-gap-representatives
Source locator: PDF page 9, Supplemental Material, paragraph containing Eq. (S7)
PDF page: 9
Claim: This source gives the 90-class count but does not enumerate an executable representative gate for every class in the paper.
Gap scope: source_local

## Restricted theorem scope [literature_gap]
Fact ID: kim2607-gap-theorem-scope
Source locator: PDF page 19, Supplemental Material, Theorem 1
PDF page: 19
Claim: The source does not prove global optimality over all Clifford circuits, all AKLT edge states, alternate sweep schedules, general Haldane-phase states, or non-Clifford disentanglers.
Gap scope: source_local

## No quantitative perturbation theorem [literature_gap]
Fact ID: kim2607-gap-perturbation-radius
Source locator: PDF page 19, Supplemental Material, paragraph following Eq. (S61)
PDF page: 19
Claim: The source's robustness interpretation does not specify a tensor perturbation norm, a certified perturbation radius, or a bound that preserves the optimizer under perturbations.
Gap scope: source_local

## No phase-wide exact proof [literature_gap]
Fact ID: kim2607-gap-phase-wide-proof
Source locator: PDF page 3, paragraph immediately following Eq. (4)
PDF page: 3
Claim: The source does not supply an exact theorem extending its specified-AKLT greedy-sweep proof to every state throughout the Haldane phase.
Gap scope: source_local
