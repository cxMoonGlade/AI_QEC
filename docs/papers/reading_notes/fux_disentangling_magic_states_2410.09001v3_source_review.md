+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2410.09001"
source_version = "v3"
source_uri = "https://arxiv.org/abs/2410.09001v3"
source_artifact = "docs/papers/2410.09001v3.pdf"
source_sha256 = "18989f0d48b8115daf88bf6d1d13a61e69ba0878fbc0861d45622330cf982cd0"
title = "Disentangling magic states with classically simulable quantum circuits"
publication_status = "published"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/FUX_2410_09001_DISENTANGLING_AUDIT_2026-07-31.md"
audit_packet_sha256 = "37121caebb4a3c8f0204d426a210bc1df0349414c500771ea71ac04826a17cb3"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_clifford_frame_source_review_2026_07_31"
admission_date = "2026-07-31"
visually_checked_pages = [1, 2, 3, 4, 5, 6]

[[relations]]
predicate = "defines"
object_id = "fux-logical-operator-disentangling-criterion"
object_type = "theorem"
object_label = "logical operator"
fact_id = "fux-theorem-1-logical-criterion"

[[relations]]
predicate = "derives"
object_id = "fux-theorem-1-clifford-construction"
object_type = "method"
object_label = "absorbing Clifford"
fact_id = "fux-theorem-1-proof"

[[relations]]
predicate = "derives"
object_id = "fux-random-code-logical-probability"
object_type = "model"
object_label = "stabilizer code"
fact_id = "fux-random-code-probability"

[[relations]]
predicate = "derives"
object_id = "fux-analytic-disentangling-budget"
object_type = "concept"
object_label = "average gate budget"
fact_id = "fux-tau-analytic"

[[relations]]
predicate = "supports"
object_id = "fux-numerical-disentangling-budget"
object_type = "observable"
object_label = "full disentangling"
fact_id = "fux-numerical-budget"

[[relations]]
predicate = "defines"
object_id = "fux-arbitrary-angle-phase-gate-scope"
object_type = "concept"
object_label = "non-Clifford gate"
fact_id = "fux-arbitrary-angle-extension"

[[relations]]
predicate = "uses"
object_id = "fux-clifford-augmented-mps-form"
object_type = "method"
object_label = "bond dimension"
fact_id = "fux-camps-form-and-bond-bound"

[[relations]]
predicate = "uses"
object_id = "fux-two-qubit-clifford-quotient-search"
object_type = "method"
object_label = "20 Cliffords"
fact_id = "fux-twenty-clifford-quotient"

[[relations]]
predicate = "measures"
object_id = "fux-stabilizer-renyi-entropy"
object_type = "observable"
object_label = "nonstabilizerness"
fact_id = "fux-sre-definition"

[[relations]]
predicate = "measures"
object_id = "fux-per-gate-magic-calibration"
object_type = "observable"
object_label = "stabilizer Rényi entropy"
fact_id = "fux-per-gate-magic-values"

[[relations]]
predicate = "limits"
object_id = "fux-trotter-generator-count-obstruction"
object_type = "limitation"
object_label = "more Pauli strings than qubits"
fact_id = "fux-trotter-obstruction"

[[relations]]
predicate = "limits"
object_id = "fux-ising-partial-disentangling"
object_type = "limitation"
object_label = "Ising chain"
fact_id = "fux-end-matter-ising-partial"

[[relations]]
predicate = "limits"
object_id = "fux-first-step-obstruction"
object_type = "limitation"
object_label = "first time step"
fact_id = "fux-end-matter-first-step"

[[relations]]
predicate = "limits"
object_id = "fux-output-sampling-cost"
object_type = "limitation"
object_label = "output qubits"
fact_id = "fux-sampling-limitation"

[[relations]]
predicate = "defines"
object_id = "fux-nonstabilizer-logical-premise"
object_type = "concept"
object_label = "nonstabilizer"
fact_id = "fux-nonstabilizer-residual-premise"

[[relations]]
predicate = "derives"
object_id = "fux-projective-pauli-sampling-reduction"
object_type = "method"
object_label = "post-measurement state"
fact_id = "fux-projective-pauli-sampling"
+++
# Full-text review — Fux, Béri, Fazio, and Tirrito, “Disentangling magic states with classically simulable quantum circuits”

## Source identity [paper_fact]
Fact ID: fux-source-identity
Source locator: Title page, author block, and arXiv version line
PDF page: 1
Claim: The reviewed source is the arXiv:2410.09001v3 preprint by Gerald E. Fux, Benjamin Béri, Rosario Fazio, and Emanuele Tirrito, dated 8 December 2025.

The listed affiliations are ICTP Trieste, the T.C.M. Group at the Cavendish
Laboratory, DAMTP Cambridge, and Università di Napoli “Federico II”. The
artifact has 8 PDF pages: a main text, an End Matter section, and references.

Publication status (recorded 2026-08-01): the paper is published as
*Physical Review Letters* 135, 260605 on 24 December 2025, DOI
10.1103/ggp1-byj1, verified by resolving the DOI to the APS landing page
“Disentangling Magic States with Classically Simulable Quantum Circuits |
Phys. Rev. Lett.” and against the INSPIRE literature record for
arXiv:2410.09001 (imprint date 2025-12-24, journal issue 26, same DOI from
both APS and arXiv metadata). The reviewed artifact remains the arXiv v3
preprint PDF bound above by SHA-256; the v3 text has not been diffed against
the version of record, so every locator and quotation in this note refers to
the v3 PDF only. Earlier arXiv versions carried the title “Disentangling
unitary dynamics with classically simulable quantum circuits”, which is how
some citing papers list this reference.

## Headline result [paper_fact]
Fact ID: fux-abstract-result
Source locator: Abstract, first two sentences; intro, final paragraph of the right column
PDF page: 1
Claim: States from deep random Clifford circuits doped with non-Clifford phase gates can be disentangled completely provided the number of non-Clifford gates is smaller than or approximately equal to the number of qubits, with the quoted average threshold \(t\lesssim N-1.607\).

The abstract states the consequence as efficient classical simulation of Pauli
expectation values “despite them exhibiting both extensive entanglement and
extensive nonstabilizerness”, and announces that the result is proved using a
quantum error correction formulation.

## Circuit setup [paper_fact]
Fact ID: fux-setup-alternating-circuit
Source locator: Sec. “Setup”, first paragraph; Fig. 1(a)
PDF page: 2
Claim: The studied circuit acts on \(N\) qubits initialized in the computational basis state and alternates deep random Clifford circuits with single non-Clifford phase gates.

The source notes that a single such layer already produces a highly entangled
state, whereas nonstabilizerness grows only slowly, one phase gate at a time.
Commuting the phase gates through the Clifford blocks moves nonstabilizerness
onto the initial state “but generally at the expense of increasing its
entanglement”.

## Nonstabilizer logical-state premise [paper_fact]
Fact ID: fux-nonstabilizer-residual-premise
Source locator: Sec. “Results”, paragraph introducing Fig. 1(b) immediately preceding Theorem 1
PDF page: 2
Claim: The setup sentence immediately preceding Theorem 1 applies the gate \(e^{i\phi P}\) to a state of a stabilizer code wherein a (nonstabilizer) logical state \(\lvert\varphi\rangle\) is encoded through a Clifford unitary \(C\), so the theorem constrains the logical state only through the exact encoding \(\lvert\psi\rangle=C(\lvert\varphi\rangle\otimes\lvert0\rangle^{\otimes(N-k)})\) with \(0\le k<N\) and places no stabilizerness requirement on \(\lvert\varphi\rangle\).

The sentence reads: “Here a gate \(e^{i\phi P}\) with phase \(\phi\) and
\(P\in\mathcal P_N\) (with \(\mathcal P_N\) the \(N\)-qubit Pauli group) is
applied to a state \(\lvert\psi\rangle\) of a stabilizer code wherein a
(nonstabilizer) logical state \(\lvert\varphi\rangle\) is encoded through a
Clifford unitary \(C\).” Theorem 1’s hypothesis line then requires only the
encoding form with \(0\le k<N\) and that \(P\) not be a logical operator of
the corresponding \([N,k]\) stabilizer code; the qualifier “(nonstabilizer)”
makes explicit that the encoded logical state is arbitrary.

## Disentangling criterion [paper_fact]
Fact ID: fux-theorem-1-logical-criterion
Source locator: Theorem 1 and Eq. (1)
PDF page: 2
Claim: For \(\lvert\psi\rangle=C(\lvert\varphi\rangle\otimes\lvert0\rangle^{\otimes(N-k)})\) with \(0\le k<N\), if the Pauli operator \(P\) is **not** a logical operator of the corresponding \([N,k]\) stabilizer code, then a Clifford \(\tilde C\) exists with \(e^{i\phi P}\lvert\psi\rangle\propto\tilde C(\lvert\varphi\rangle\otimes\lvert x(\phi)\rangle\otimes\lvert0\rangle^{\otimes(N-k-1)})\).

Here \(\lvert x(\phi)\rangle=\lvert0\rangle\) or \(\lvert x(\phi)\rangle=e^{i\phi
Y}\lvert0\rangle\). The condition is membership in the logical-operator set of
the code induced by the current Clifford encoding. The theorem is stated for a
general phase \(\phi\) and a general Pauli \(P\in\mathcal P_N\).

## Proof construction [paper_fact]
Fact ID: fux-theorem-1-proof
Source locator: Proof of Theorem 1, Eqs. (2)–(3c)
PDF page: 2
Claim: The proof splits on the two ways \(P\) can fail to be logical — either \(P\) lies in the stabilizer group \(\mathcal S\), or \(P\) anticommutes with some generator \(S_j\) with \(j>k\) — and in the second case builds the absorbing Clifford explicitly from \(V=e^{i(\pi/4)LZ_{k+1}}\) and \(W=e^{i(\pi/4)L}\).

In the first case Eq. (1) holds with \(\lvert x(\phi)\rangle=\lvert0\rangle\)
and \(\tilde C=C\). In the second case the generators are relabelled so that
\(j=k+1\) and \(R=X_{k+1}\) without loss of generality, and Eq. (3c) yields
\(\lvert x(\phi)\rangle=e^{i\phi Y}\lvert0\rangle\). All of \(C\), \(V\), and
\(W\) are Clifford, which closes the argument.

## Random-code probability [paper_fact]
Fact ID: fux-random-code-probability
Source locator: Paragraph following the proof of Theorem 1, expression for \(p_{k+1}\)
PDF page: 2
Claim: For a random \([N,k]\) stabilizer code the probability that a uniformly random Pauli is not a logical operator is \(p_{k+1}=1-(4^{k}-1)2^{N-k}/(4^{N}-1)\).

The counting is stated as \(2^{N-k}\) representatives for each of the
\(4^{k}-1\) logical Pauli operators against \(4^{N}-1\) non-trivial Pauli
strings. The estimate is introduced as probabilistic and rests on the premise
that deep random Clifford circuits generate random stabilizer codes.

## Analytic gate budget [paper_fact]
Fact ID: fux-tau-analytic
Source locator: Paragraph following the proof of Theorem 1, final two lines
PDF page: 2
Claim: Combining the per-step probabilities as \(\Pr(t^{*})=(1-p_{t^{*}+1})\prod_{k=1}^{t^{*}}p_k\) and taking the large-\(N\) limit gives an average gate budget \(\langle\tau\rangle=\langle N-t^{*}\rangle\approx1.607\) with standard deviation \(\sigma_\tau\approx1.6565\).

The large-\(N\) form is written with \(q\)-Pochhammer symbols as
\(\Pr(N-j)\approx(\tfrac12;\tfrac12)_\infty 2^{-j}/(\tfrac12;\tfrac12)_j\). The
source also records that the process it analyses differs slightly from Fig. 1(a)
and “will slightly underestimate our estimate”.

## Arbitrary rotation angles [paper_fact]
Fact ID: fux-arbitrary-angle-extension
Source locator: Paragraph beginning “Although we phrased our argument using T-gates”
PDF page: 2
Claim: By Theorem 1 the result applies equally when the \(j\)-th non-Clifford gate is any \(e^{i\phi_j P_j}\) with \(P_j\in\mathcal P_N\), rather than a \(\pi/8\) phase gate.

The source qualifies the explicit product ansatz
\(\lvert\psi(t)\rangle=\tilde C_t(\lvert x(\phi_1)\dots x(\phi_t)\rangle\otimes
\lvert0\rangle^{\otimes(N-t)})\): it “applies only if \(P_j\) are not logical
operators and \(t<t^{*}\)”. Beyond that regime the state is represented as a
Clifford-augmented matrix product state instead.

## Augmented representation and bond bound [paper_fact]
Fact ID: fux-camps-form-and-bond-bound
Source locator: Eq. (4) and the paragraph following it
PDF page: 3
Claim: Applying Theorem 1 at each intermediate step gives \(\lvert\psi(s)\rangle=\tilde C_s(\lvert\mathrm{MPS}^{(k)}\rangle\otimes\lvert0\rangle^{\otimes(N-k)})\) with \(k\le s\), so the final state carries matrix product state bond dimension at most \(2^{t-k}\).

When the next pulled-back operator is a logical operator of the current code
the bond dimension doubles instead; otherwise the logical register grows by one
qubit at no bond cost. The source expects \(t-k=O(1)\) for generic deep global
random Clifford circuits with \(t<t^{*}\), and expects \(k\) to increase rapidly
with \(t\) once \(t>t^{*}\).

## Two-qubit candidate quotient [paper_fact]
Fact ID: fux-twenty-clifford-quotient
Source locator: Paragraph describing the greedy entanglement-cooling search; Acknowledgements
PDF page: 3
Claim: The two-qubit Clifford search is taken over the quotient \(\tilde{\mathcal C}_2=\mathcal C_2/(\mathcal C_1\otimes\mathcal C_1)\), leaving exactly 20 Cliffords to check at each step, with \(\lvert\mathcal C_1\rvert=24\) and \(\lvert\mathcal C_2\rvert=11520\).

The search is a sweeping greedy procedure: trial two-qubit Cliffords are applied
to the first pair, the best is kept, the sweep advances along the chain and then
reverses, and the source reports that typically only \(O(1)\) sweeps are needed
with computation time scaling linearly in \(N\). The Acknowledgements credit
Poetri Tarabunga for pointing out that only 20 Clifford gates are necessary.

## Stabilizer Rényi entropy definition [paper_fact]
Fact ID: fux-sre-definition
Source locator: Eq. (7) and the sentence introducing it
PDF page: 3
Claim: Nonstabilizerness is quantified by \(\mathcal M(\lvert\psi\rangle)=-\log_2\left(\sum_{P\in\mathcal P_N}\Xi_P^2(\lvert\psi\rangle)\right)-N\) with \(\Xi_P(\lvert\psi\rangle)=2^{-N}\lvert\langle\psi\rvert P\lvert\psi\rangle\rvert^2\).

Entanglement is measured in parallel by Eq. (6), the von Neumann entropy of the
reduced density matrix for the first \(i\) qubits, with the reported quantity
taken as the maximum over all such cuts.

## Numerical gate budget [paper_fact]
Fact ID: fux-numerical-budget
Source locator: Paragraph beginning “Clifford gates on random (non-local) pairs of qubits”
PDF page: 4
Claim: Numerically the state disentangles completely for \(t\lesssim N\), and for large \(N\) full disentangling holds up to \(t^{*}=N-\tau\) with average \(\langle\tau\rangle=1.61\pm0.09\) and standard deviation \(\sigma_\tau=1.60\pm0.12\), described as in perfect agreement with the analytic result.

Each Clifford block \(C_j\) is built from \(2N^{2}\) two-qubit gates on random
non-local pairs, sampled independently and uniformly from \(\mathcal C_2\);
results are averaged over 256 random Clifford sequences. For \(t\gtrsim N\) the
bond dimension increases rapidly with \(t\), and the transition sharpens with
increasing \(N\).

## Per-gate magic calibration [paper_fact]
Fact ID: fux-per-gate-magic-values
Source locator: Fig. 3 caption and the paragraph preceding it
PDF page: 4
Claim: The source records \(\mathcal M(T\lvert+\rangle)\approx0.4150\) and \(\mathcal M(\sqrt{T}\lvert+\rangle)\approx0.2075\), exactly half, and reports that the maximal stabilizer Rényi entropy reachable while keeping bond dimension one is halved accordingly.

The same figure states that in both the \(T\)-gate and \(\sqrt{T}\)-gate cases
the matrix product state of the augmented ansatz can be completely disentangled
for approximately \(N\) time steps but not further, so the average threshold in
gate count is unchanged by the smaller per-gate magic.

## Trotterized dynamics obstruction [paper_fact]
Fact ID: fux-trotter-obstruction
Source locator: Sec. “Consequences for Hamiltonian dynamics”, first paragraph
PDF page: 4
Claim: For a generic Hamiltonian \(H=\sum_{j=1}^{M}\omega_j P_j\) with more Pauli strings than qubits, a single Suzuki–Trotter step already requires that many non-Clifford gates, which the source says suggests that Hamiltonian dynamics will generically not admit a completely disentangled augmented representation, not even at early times.

The source states this as a consequence of the gate-count threshold rather than
as a separate theorem, and points to the End Matter for numerical confirmation
on a non-integrable one-dimensional Ising chain.

## Projective Pauli sampling reduction [paper_fact]
Fact ID: fux-projective-pauli-sampling
Source locator: Paragraph beginning “While computing Pauli expectations” and the following Pauli-based-computation paragraph
PDF page: 4
Claim: For sampling projective measurements of \(Z_1,\dots,Z_N\) on \(\lvert\psi(t)\rangle\), any \(\tilde Z_j=\tilde C_t^\dagger Z_j\tilde C_t\) that anticommutes with some \(Z_{j>k}\) yields outcome \(+1\) or \(-1\) with equal probability and a post-measurement state obtained via a Clifford unitary, after which at most \(k\) mutually commuting Pauli measurements remain and the quantum part of the problem is restricted to \(n\le k\) qubits.

The paragraph opens: “While computing Pauli expectations is classically
efficient, sampling the distribution of projective Pauli measurements is
harder”, and states that for the setup in Fig. 1(a) with \(t<N-O(1)\) only a
\(k\le t\) qubit quantum computer is needed. The retained measurements are
restricted to \(\lvert\mathrm{MPS}^{(k)}\rangle\) “since they have to feature
\(\mathbb 1\) or \(Z_j\) on qubits \(j>k\) to be retained”. The following
paragraph calls the approach akin to Pauli based computation and fixes its
scope: “while PBC is restricted to T-gates, our scheme allows for any
non-Clifford \(G_j=e^{i\phi_j P_j}\), as long as the Clifford blocks are
global random, i.e., deep random Clifford circuits.”

## Output sampling cost [paper_fact]
Fact ID: fux-sampling-limitation
Source locator: Paragraph beginning “Our results extend beyond Clifford + T circuits”
PDF page: 5
Claim: Pauli string expectation values are computable classically in polynomial time for the circuits considered, but sampling from \(O(N)\) output qubits appears to require exponential classical resources, while sampling from \(O[\log(N)]\) qubits stays classically efficient.

The stated reason is that the bond dimension of the matrix product state in the
augmented representation generically doubles with each output qubit projection.
The source draws the analogy to instantaneous quantum polynomial-time circuits.

## Ising-chain confirmation [paper_fact]
Fact ID: fux-end-matter-ising-partial
Source locator: End Matter, opening paragraph and Sec. “Hamiltonian dynamics”, Eq. (8) and Fig. 4
PDF page: 5
Claim: For the one-dimensional Ising chain of Eq. (8) with integrability-breaking longitudinal fields, the transient state can only be partly disentangled with Clifford circuits at very early times, which the source says suggests that generic Hamiltonian dynamics does not profit from the augmented ansatz.

The Hamiltonian is \(H=J\sum_{i=1}^{N-1}X_iX_{i+1}+h_x\sum_{i=1}^{N}X_i+
h_z\sum_{i=1}^{N}Z_i\) with \(J=1.0\) and \(h_z=0.5\), evolved from
\(\lvert+\rangle^{\otimes N}\) by a time-dependent variational principle. The
transformed Hamiltonian is written as a matrix product operator of bond
dimension at most \(3N-1\). Figure 4 covers \(N=4,8,16\) and shows the
stabilizer Rényi entropy density saturating above that of the corresponding
product magic state.

## First-step obstruction [paper_fact]
Fact ID: fux-end-matter-first-step
Source locator: End Matter, paragraph beginning “find Clifford unitaries that partially disentangle the state”
PDF page: 6
Claim: The source finds Cliffords that only partially disentangle at very early times or very small sizes, states that any reduction of entanglement seems to disappear for larger systems and later times, and notes that the state cannot be disentangled completely even immediately after the first time step.

The stated reason is that preparing the state at the first small time step
already requires \(3N-1\) gates of the form \(e^{i\phi_j P_j}\), with the
\(P_j\) drawn from the Pauli strings of Eq. (8), which places the first step
beyond the gate-count threshold established in the main text. The source
mentions matchgate circuits as an alternative disentangling family and leaves
that direction to future work.
