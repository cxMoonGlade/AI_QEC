+++
schema = "error_coupling_simulator.literature.note.v1"
source_id = "arxiv:2604.27058"
source_version = "v2"
source_uri = "https://arxiv.org/abs/2604.27058v2"
source_artifact = "docs/papers/2604.27058v2.pdf"
source_sha256 = "3dfea923648f67793c3e5f368bdedff15549312ad9d030b4264ef4bec619c421"
title = "Clifft: Fast Exact Simulation of Near-Clifford Quantum Circuits"
publication_status = "preprint"
read_status = "complete"
evidence_status = "persisted"
review_scope = "full_text"
operation_replay_status = "complete"
audit_packet = "docs/simulator_validation/CHASE_LABIB_2604_27058V2_CLIFFT_FRAME_FACTORED_AUDIT_2026-08-02.md"
audit_packet_sha256 = "d27d7655c30f5694873a094916bef28d0b0b994aeaa52ace61e4d78bb15f5f7e"
admission_status = "source_only_reviewed"
admission_reviewer = "independent_clifft_source_review_2026_08_02"
admission_date = "2026-08-02"
visually_checked_pages = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 17, 20, 21, 22, 23]

[[relations]]
predicate = "defines"
object_id = "clifft-frame-factored-state"
object_type = "model"
object_label = "frame-factored"
fact_id = "clifft-state-definition"

[[relations]]
predicate = "defines"
object_id = "clifft-heisenberg-mapping"
object_type = "method"
object_label = "Heisenberg"
fact_id = "clifft-virtual-basis-map"

[[relations]]
predicate = "defines"
object_id = "clifft-pauli-localization"
object_type = "method"
object_label = "Pauli localization"
fact_id = "clifft-localization-lemma"

[[relations]]
predicate = "measures"
object_id = "clifft-peak-active-virtual-dimension"
object_type = "observable"
object_label = "peak active virtual dimension"
fact_id = "clifft-active-dimension"

[[relations]]
predicate = "supports"
object_id = "clifft-coordinate-amplitude-decoupling"
object_type = "theorem"
object_label = "before sampling"
fact_id = "clifft-theorem-one"

[[relations]]
predicate = "derives"
object_id = "clifft-sample-time-cost-law"
object_type = "method"
object_label = "per-shot"
fact_id = "clifft-sample-cost"

[[relations]]
predicate = "uses"
object_id = "clifft-measurement-driven-contraction"
object_type = "method"
object_label = "demoted"
fact_id = "clifft-measurement-cases"

[[relations]]
predicate = "limits"
object_id = "clifft-coherent-noise-active-dimension-growth"
object_type = "limitation"
object_label = "24"
fact_id = "clifft-table-one"

[[relations]]
predicate = "limits"
object_id = "clifft-exact-representation-without-truncation"
object_type = "limitation"
object_label = "approximation schemes"
fact_id = "clifft-conclusion-scope"

[[relations]]
predicate = "uses"
object_id = "clifft-expectation-value-probe"
object_type = "observable"
object_label = "expectation-value probe"
fact_id = "clifft-fidelity-probe"
+++
# Full-text review — Chase and Labib, "Clifft: Fast Exact Simulation of Near-Clifford Quantum Circuits"

## Source identity [paper_fact]
Fact ID: clifft-source-identity
Source locator: Title page, author block, abstract, and the arXiv version line in the left margin
PDF page: 1
Claim: The reviewed source is arXiv:2604.27058v2 by Bradley Chase and Farrokh Labib of Unitary Foundation, with the version line dated 20 May 2026.

The artifact has 24 PDF pages: five numbered sections, a reference list, and
four appendices A through D.  The title-page footer carries the repository URL
`https://github.com/unitaryfoundation/clifft`.

## Represented object and the frame-factored state [paper_fact]
Fact ID: clifft-state-definition
Source locator: Sec. 2.2, Definition 2, Eqs. (2)-(3)
PDF page: 5
Claim: The source represents the physical pure state at time \(t\) in frame-factored form \(|\psi^{(t)}\rangle=\gamma^{(t)}U_C^{(t)}\tilde P^{(t)}\bigl(|\phi^{(t)}\rangle_A\otimes|0\rangle_D\bigr)\), with a Clifford frame \(U_C^{(t)}\in\mathcal C_N\), a phase-free \(N\)-qubit virtual Pauli frame \(\tilde P^{(t)}\), disjoint active and dormant virtual qubit sets \(A\) and \(D\) with \(|A|=k\), a dense active state vector \(|\phi^{(t)}\rangle_A\in\mathbb C^{2^k}\), and a global scalar \(\gamma^{(t)}\).

Equation (3) writes the Pauli frame as \(\tilde P^{(t)}=\bigotimes_{j}X_j^{x_j}Z_j^{z_j}\)
for binary vectors \(x^{(t)},z^{(t)}\in\{0,1\}^N\).  The dormant subspace is
fixed to \(|0\rangle_D\) in the virtual basis, so all coherent superposition not
captured by the two frames is confined to the active state vector.  At
initialization \(U_C^{(0)}=I\), \(\tilde P^{(0)}=I\), \(A=\varnothing\),
\(|\phi^{(0)}\rangle_A=[1]\) and \(\gamma^{(0)}=1\).  The object is a pure
state; the source defines no density matrix and no subsystem state.

## Heisenberg mapping into the virtual basis [paper_fact]
Fact ID: clifft-virtual-basis-map
Source locator: Sec. 2.1, Definition 1, Eq. (1)
PDF page: 4
Claim: Every active operation is expressed in the virtual basis by conjugating its Pauli generator through the cumulative Clifford frame, \(\tilde P_O=(U_C^{(t)})^{\dagger}P_O U_C^{(t)}\), a Heisenberg mapping whose image remains a valid Pauli string that may act on many virtual qubits.

Section 2.1 partitions circuit operations into passive Clifford unitaries, which
are absorbed into \(U_C\), and active operations, which are non-Clifford Pauli
rotations, projective Pauli measurements, stochastic Pauli noise, and
conditionally applied Pauli corrections.

## Peak active virtual dimension as the cost-determining quantity [paper_fact]
Fact ID: clifft-active-dimension
Source locator: Sec. 2.2, Eq. (4), and the abstract
PDF page: 5
Claim: The maximum active dimension over execution, \(k_{\max}=\max_t|A^{(t)}|\), bounds the dominant exponential cost of simulation, and the abstract states that this peak active virtual dimension expands during non-Clifford operations and contracts during measurements.

The source adds that for near-Clifford protocols with frequent measurements
\(k_{\max}\) can be much smaller than the total number of physical qubits
\(N\).  It proves no bound on \(k_{\max}\) itself in terms of circuit
parameters.

## Pauli localization to a single virtual axis [paper_fact]
Fact ID: clifft-localization-lemma
Source locator: Sec. 2.3, Lemma 1, and Eqs. (5)-(6)
PDF page: 5
Claim: Lemma 1 states that for any non-identity \(N\)-qubit virtual Pauli operator there exists a sequence of at most \(2N\) virtual Clifford gates \(V\) with \(V\tilde P_OV^{\dagger}=\alpha P_v\) acting non-trivially on exactly one virtual qubit \(v\), and Pauli localization inserts \(V^{\dagger}V=I\) so that \(V^{\dagger}\) is absorbed into \(U_C\) and the Pauli frame is conjugated to \(V\tilde PV^{\dagger}\).

Equation (6) is the factorization that makes this exact:
\(\exp(-i\theta P_O)|\psi\rangle=\gamma(U_CV^{\dagger})\exp(-i\theta\alpha P_v)(V\tilde PV^{\dagger})[V(|\phi\rangle_A\otimes|0\rangle_D)]\).

## Constructive localization algorithm [paper_fact]
Fact ID: clifft-localization-construction
Source locator: Appendix A, Eqs. (15)-(17)
PDF page: 20
Claim: The constructive proof is a greedy \(O(N)\) algorithm in two exclusive cases: when the \(X\)-support is non-empty it picks a pivot \(v\) with \(x_v=1\), clears \(X\)-support with \(\mathrm{CNOT}_{v\to q}\) and residual \(Z\)-support with \(\mathrm{CZ}_{v,q}\); for a pure \(Z\)-string it picks a pivot with \(z_v=1\) and applies \(\mathrm{CNOT}_{q\to v}\).

Equation (15) gives
\(\mathrm{CNOT}_{v\to q}(X_v\otimes X_q)\mathrm{CNOT}^{\dagger}_{v\to q}=X_v\otimes I_q\),
Eq. (16) gives
\(\mathrm{CZ}_{v,q}(X_v\otimes Z_q)\mathrm{CZ}^{\dagger}_{v,q}=X_v\otimes I_q\),
and Eq. (17) gives
\(\mathrm{CNOT}_{q\to v}(Z_q\otimes Z_v)\mathrm{CNOT}^{\dagger}_{q\to v}=I_q\otimes Z_v\).
Each two-qubit gate erases generator support monotonically without respreading
to cleared qubits.

## Dormant invariance of the localization sequence [paper_fact]
Fact ID: clifft-dormant-invariance
Source locator: Sec. 2.3, Lemma 2, Eq. (7)
PDF page: 6
Claim: Lemma 2 states that a localization sequence built from controlled-Pauli operations whose controls lie in the dormant set acts as the identity on the computational-zero dormant subspace, so that localization changes only the coordinate and Pauli frames and not the active state vector.

The source says Clifft prefers such sequences whenever possible, and that when
the condition fails the localized operation may promote a dormant virtual qubit
into the active set.

## Expansion rule for non-Clifford rotations [paper_fact]
Fact ID: clifft-rotation-expansion
Source locator: Sec. 2.4, paragraph "Continuous Pauli rotations", with the case analysis in Appendix B.1
PDF page: 6
Claim: A localized non-Clifford rotation on a dormant axis that requires placing that axis in a conjugate basis promotes it into the active set, \(A\leftarrow A\cup\{v\}\), and the active state vector expands from dimension \(2^k\) to \(2^{k+1}\); a rotation diagonal on the dormant state contributes only a scalar phase, and a rotation on an already active axis leaves \(k\) unchanged.

Appendix B.1 on PDF page 21 gives the three cases explicitly as trivial phase,
subspace expansion with \(|\phi\rangle_A\leftarrow|\phi\rangle_A\otimes|+\rangle\),
and in-place active subspace rotation.  Equation (19) shows that commuting the
localized rotation past the Pauli frame only flips the sign of the angle
according to a Boolean parity.

## Contraction rule for projective measurements [paper_fact]
Fact ID: clifft-measurement-contraction
Source locator: Sec. 2.4, paragraph "Projective Pauli measurements", Eqs. (8)-(9)
PDF page: 6
Claim: A projective Pauli measurement is mapped and localized to a single virtual observable \(M_v\in\{X_v,Z_v\}\) with projector \(\Pi_m=\tfrac12(I+(-1)^mM_v)\), and commuting it past the virtual Pauli frame extracts only a parity shift, \(\Pi_m\tilde P=\tilde P\Pi_{m\oplus p}\), with \(p=1\) exactly when \(M_v\) anticommutes with \(\tilde P\).

The source states that the mapped projector does not need to be localized, and
that if the measured axis is dormant the active state vector is unchanged.

## Measurement case analysis and the demotion step [paper_fact]
Fact ID: clifft-measurement-cases
Source locator: Appendix B.2, Eqs. (20)-(22)
PDF page: 22
Claim: For a dormant measured axis the outcome is either deterministic up to the Pauli-frame shift or uniformly random with a virtual Hadamard absorbed as \(U_C\leftarrow U_CH_v\) and \(\tilde P\leftarrow H_v\tilde PH_v\), leaving the active state vector unchanged; for an active measured axis the shifted projector is applied to the corresponding tensor factor, the measured qubit is disentangled and then demoted from \(A\) to \(D\), reducing the active dimension by one.

This is the mechanical content of "cost contracts on measurement": contraction
happens only when the localized virtual axis of the measurement already lies in
the active set, and it removes exactly one axis per such measurement.

## Stochastic Pauli noise never touches the active state vector [paper_fact]
Fact ID: clifft-conditional-pauli
Source locator: Sec. 2.4, paragraph "Conditional Pauli operations", Eq. (10)
PDF page: 7
Claim: Stochastic Pauli noise, feed-forward corrections, and other classically controlled Pauli operations bypass Pauli localization and are absorbed into the virtual Pauli frame as \(\tilde P\leftarrow\tilde E^{c}\tilde P\) with any phase accumulated into \(\gamma\); they do not change \(U_C\), do not change \(A\), and do not traverse the active state vector.

Appendix B.3, Eqs. (23)-(24) on PDF page 22 repeats this with the explicit
phase-free collapse of the Pauli product.

## Coordinate-amplitude decoupling theorem [paper_fact]
Fact ID: clifft-theorem-one
Source locator: Sec. 2.5, Theorem 1 and its proof
PDF page: 7
Claim: Theorem 1 states that the trajectory of the Clifford frame \(U_C^{(t)}\) and the active-set geometry \(A^{(t)}\) are determined by the circuit structure and localization choices and are independent of stochastic Pauli error samples, probabilistic measurement outcomes, and the complex amplitudes of the active state vector, so that the evolution of \(U_C^{(t)}\) and \(A^{(t)}\), and hence the bound \(k_{\max}\), can be determined before sampling.

The proof observes that rotations expand the active set only when the mapped
generator and localization choice require promotion from the dormant subspace,
that measurements contract it only when the localized axis lies in \(A\), with
the measured eigenvalue affecting branch and normalization but not which axis is
demoted, and that conditional Paulis leave \(U_C\) and \(A\) unchanged.

## Compile-time cost law [paper_fact]
Fact ID: clifft-compile-cost
Source locator: Sec. 2.6, paragraph "Compile-time cost", Eq. (11)
PDF page: 7
Claim: With \(C\) Clifford operations, \(M\) measurements, \(T\) non-Clifford rotations and \(E\) stochastic Pauli error mechanisms, the total offline cost is bounded by \(O(CN+EN+(M+T)N^{2})\) and is incurred once per circuit.

Footnote 2 records that packed bit operations reduce some linear factors in
\(N\) by machine-word parallelism in practice.

## Sample-time cost law [paper_fact]
Fact ID: clifft-sample-cost
Source locator: Sec. 2.6, paragraph "Sample-time cost", Eqs. (12)-(14)
PDF page: 8
Claim: The total worst-case per-shot cost is \(O((T+M+E)N+(T+M_{\mathrm{active}})2^{k_{\max}})\), splitting into discrete tracking and sampling at \(O((T+M+E)N)\) and dense active-subspace evolution at \(O((T+M_{\mathrm{active}})2^{k_{\max}})\), where \(M_{\mathrm{active}}\) is the number of measurements that act on the active subspace.

Per-shot execution is independent of the number of passive Clifford gates
\(C\).  The source states that in the target near-Clifford regimes runtime is
typically dominated by active-array traversals of size \(2^{k_{\max}}\).

## Supported instruction surface [paper_fact]
Fact ID: clifft-instruction-support
Source locator: Sec. 3.1, stage 1 "Front-End: Heisenberg mapping"
PDF page: 9
Claim: The front-end accepts circuits in the Stim format extended with non-Clifford operations including \(T\), arbitrary-angle Pauli rotations such as R_X, and single-qubit rotations such as U3, and states that nearly all of Stim's existing noise channels, mid-circuit measurements, detectors, observables, and repeat blocks are supported without modification.

Clifft integrates Stim's optimized C++ tableau implementation directly and uses
its inverse tableau tracking to absorb physical Clifford gates into \(U_C\).
The artifact does not resolve which instructions the qualifier "nearly all"
excludes; it defers the full listing to the documentation and codebase.

## Scheduling pass that lowers the peak active dimension [paper_fact]
Fact ID: clifft-scheduling-pass
Source locator: Sec. 3.1, stage 2 "Middle-End: HIR optimization"
PDF page: 10
Claim: The second optimization pass reorders commuting measurements and non-Clifford operations to push non-Cliffords later and pull measurements earlier when possible, which the source says reduces the peak active dimension \(k_{\max}\), or more generally the total time spent at larger active dimensions.

This makes \(k_{\max}\) a joint property of the circuit and the compiler's
localization and scheduling heuristics rather than of the circuit alone.

## Fixed-layout runtime allocation [paper_fact]
Fact ID: clifft-runtime-allocation
Source locator: Sec. 3.2, opening paragraphs on the Schrodinger Virtual Machine
PDF page: 10
Claim: Each program instance allocates an active array of size \(2^{k_{\max}}\) together with bit vectors for the virtual Pauli frame, a complex scalar, record buffers and sampler state, and this fixed-layout execution model avoids per-shot allocation because the compiler has already determined \(k_{\max}\) and the active-set schedule.

The source records that execution stays single-threaded while the active state
fits in cache, and that the current implementation switches to OpenMP
parallelization of active-array kernels at \(k>18\).

## Validation strategy and dense expansion [paper_fact]
Fact ID: clifft-validation
Source locator: Sec. 3.3, final paragraph on cross-checking against external simulators
PDF page: 11
Claim: For sufficiently small circuits the source explicitly expands the factored state \(|\psi\rangle=\gamma U_C\tilde P|\phi\rangle_A\) into a dense computational-basis state vector and compares it against the Qiskit Aer state-vector simulator; on Clifford-compatible noisy circuits it compares detector and logical-observable statistics against Stim over millions of shots.

The third cross-check injects deterministic Pauli faults into topological
circuits and verifies that the same logical detector trajectories are produced.
Section 3.3 also lists expectation-value probes among the classical operations
evaluated inline during bytecode execution.

## Construction of the coherent-noise benchmark family [paper_fact]
Fact ID: clifft-benchmark-construction
Source locator: Sec. 4.1, paragraphs describing the three circuit families and the fixed noise configurations
PDF page: 12
Claim: The third benchmark family consists of coherent-noise variants of surface-code memory in which every Clifford gate is followed by a small unitary R_Z rotation; these variants use Stim's rotated memory experiment as the base circuit with an over-rotation of angle 0.02 co-located with each depolarizing channel, and are adapted from the Pauli Frame Sparse Representation work.

The source describes this family as the one that "pushes \(k_{\max}\) a bit
beyond the small limit to see how well Clifft can sustain performance as the
active subspace grows".  The rotation is single-qubit; no two-qubit coherent
generator is benchmarked.

## Measured active dimension on coherent-noise surface codes [paper_fact]
Fact ID: clifft-table-one
Source locator: Sec. 4.1, Table 1, rows under "Near-Clifford: Coherent Noise"
PDF page: 13
Claim: On rotated surface-code memory with coherent noise the reported peak active dimension is 5 at distance 3 with one round, 8 at distance 3 with three rounds, 13 at distance 5 with one round, and 24 at distance 5 with five rounds, with corresponding Clifft throughputs of 19.4 M, 1.7 M, 133.1 k and 0.7 shots per second and non-Clifford operation counts of 65, 195, 209 and 1045.

All four circuits use 26 or 64 physical qubits.  The prose under the table
states that as the peak active dimension grows from 5 to 24, throughput
decreases by several orders of magnitude as the active state vector grows
beyond CPU cache size and approaches the dense-state-vector regime.  For
contrast, the pure-Clifford distance-7 surface code with seven rounds has a peak
active dimension of 0.

## Contrasting magic-state result on the same quantity [paper_fact]
Fact ID: clifft-msc-locality
Source locator: Sec. 1, paragraph beginning "localized. For example"
PDF page: 3
Claim: For the end-to-end magic state cultivation protocol, which uses 463 physical qubits through the escape stage, the source reports that the peak active dimension never exceeds 10.

The source attributes this to frequent interleaved measurements keeping
non-Clifford effects spatially and temporally localized in that protocol.  The
same mechanism does not produce a bounded peak active dimension on the
coherent-noise surface-code family of Table 1.

## Expectation-value probe as the state-information interface [paper_fact]
Fact ID: clifft-fidelity-probe
Source locator: Appendix C, Eqs. (25)-(28) and the surrounding text
PDF page: 23
Claim: To estimate the prepared logical state quality the source uses a Clifft-native expectation-value probe evaluating the logical \(\langle Y_L\rangle\) after decoder correction, and converts it to fidelity through \(F=\tfrac12+\tfrac{1}{2\sqrt2}\langle X_L\rangle+\tfrac{1}{2\sqrt2}\langle Y_L\rangle\), reported as the conservative bound \(F\ge\tfrac12+\tfrac{1}{\sqrt2}\langle Y_L\rangle\).

The justification uses the effective logical Pauli channel of Eq. (29) and the
attenuation relations Eqs. (30)-(31), verified numerically at distance 15 with
\(P(X_L)=4.679\times10^{-4}\), \(P(Z_L)=4.702\times10^{-4}\) and
\(P(Y_L)=8.372\times10^{-6}\).  The route to state information is a scalar Pauli
expectation value, not a state object.

## Release, licence and distribution [paper_fact]
Fact ID: clifft-release
Source locator: Sec. 1, paragraph following the contribution list, together with the title-page footer and Refs. [48]-[49]
PDF page: 3
Claim: The source states that Clifft is Apache 2.0 licensed and available as clifft on PyPI, with a WASM-based interactive playground, and names a companion clifft-paper repository from which circuits, analysis scripts, raw collected data and exact circuit files are reproducible.

The paper names two GitHub URLs and a PyPI package but no commit, tag or
release version for either repository.

## Exactness and the authors' own stated boundary [paper_fact]
Fact ID: clifft-conclusion-scope
Source locator: Sec. 5, Conclusion, first and third paragraphs
PDF page: 17
Claim: The conclusion describes Clifft as an exact simulator for near-Clifford quantum circuits that retains exact treatment of noise, mid-circuit measurement and classical control, and states as future work that "Coherent-noise workloads motivate approximation schemes, hybrid stabilizer-rank methods, and richer support for non-Pauli noise models such as leakage."

The same paragraph says better global scheduling and localization heuristics
"may reduce \(k_{\max}\) or the total time spent at large active dimension
beyond what the current greedy Pauli localization and HIR optimization passes
achieve", which places the Table 1 values as properties of this implementation
rather than as bounds on the representation.

## No truncation parameter or approximation error quantity [literature_gap]
Fact ID: clifft-gap-no-truncation
Source locator: Full-text scope; Secs. 2.2-2.6 and Sec. 3.3 in particular
PDF page: 8
Claim: The artifact defines no truncation cutoff, no bond or rank cap that discards weight, no discarded-weight or residual-norm observable, and no a-priori or a-posteriori approximation error bound anywhere in its 24 pages.

Gap scope: source_local

This is a consequence of the design rather than an oversight: the method is
exact, and the price of exactness is that the cost law of Eqs. (13)-(14) carries
an unmitigated \(2^{k_{\max}}\) factor.  A reader looking for a truncation
certificate in this family will not find one here.

## No reduced state, no subsystem object, no state distance [literature_gap]
Fact ID: clifft-gap-no-reduced-state
Source locator: Full-text scope; Sec. 2.2 Definition 2, Sec. 3.3, and Appendix C
PDF page: 23
Claim: The artifact defines no density matrix, no reduced density matrix, no partial trace, and no distance between two states; the only routes to state information it describes are dense expansion of the full pure state for sufficiently small circuits and scalar Pauli expectation-value probes.

Gap scope: source_local

Nothing in the artifact computes a subsystem state or compares two trajectories
against each other.

## No bound on the peak active virtual dimension [literature_gap]
Fact ID: clifft-gap-no-kmax-bound
Source locator: Full-text scope; Sec. 2.5 Theorem 1 and Sec. 4.1 Table 1
PDF page: 7
Claim: Theorem 1 establishes only that the peak active virtual dimension is a compile-time constant of the circuit and the localization choices; the artifact proves no theorem bounding that dimension for any circuit family and offers no fit or extrapolation for the four measured coherent-noise values.

Gap scope: source_local

The distinction matters because a quantity that is computable ahead of time is
not thereby bounded.  A reader may take the four Table 1 points as evidence of
growth in distance and round count, but the artifact itself states no functional
form.

## No tensor-network content [literature_gap]
Fact ID: clifft-gap-no-tensor-network
Source locator: Full-text scope; the tensor-network citations in Sec. 1 and the representation of Sec. 2.2
PDF page: 2
Claim: Tensor-network and matrix-product-state methods appear in the artifact only as a cited alternative class in the introduction; the represented object contains no tensor network, no bond dimension, and no matrix-product or projected-entangled-pair structure.

Gap scope: source_local

The dense active state vector of Definition 2 is an unfactorized complex array
of size \(2^{k}\).
