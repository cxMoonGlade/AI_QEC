# Current literature concept index

Generated from the explicit current corpus manifest. Only source-reviewed `paper_fact`
relationships appear here. This is routing metadata; the cited PDF and locator remain
the evidence.

- corpus status: active
- sources: 32
- concept nodes: 95
- source-located relationships: 95
- dangling relationships: 0

## bond environment (concept)

- **defines** — Gauge fixing, canonical forms, and optimal truncations in tensor networks with closed loops — `Sec. II, Eq. (1) and Fig. 1`, PDF p. 2 — The bond environment `Upsilon` is obtained by contracting the state norm network while leaving a selected bond and its conjugate open, and contracting it with the two bond matrices recovers the state norm. ([docs/papers/reading_notes/evenbly_closed_loop_truncation_1801.05390_source_review.md](reading_notes/evenbly_closed_loop_truncation_1801.05390_source_review.md))

## collapse-operator gauge invariance (concept)

- **defines** — Fundamental Speed Limits on Quantum Coherence and Correlation Decay — `Methods, Eqs. (10)–(11)`, PDF p. 5 — The summed dissipator has collapse-operator gauge invariance under unitary mixing, while adding an identity multiple to a collapse operator produces only the stated effective-Hamiltonian correction. ([docs/papers/reading_notes/oi_schirmer_pure_dephasing_1109.0954_source_review.md](reading_notes/oi_schirmer_pure_dephasing_1109.0954_source_review.md))

## generalized MPO (concept)

- **defines** — A simplified and improved approach to tensor network operators in two dimensions — `Sec. III A and Fig. 1`, PDF p. 4 — A generalized MPO adds an external virtual index `beta_i` to each operator-valued MPO matrix, and summing those indices couples operators outside the one-dimensional MPO domain into a sum of ordinary MPOs. ([docs/papers/reading_notes/orourke_chan_simplified_pepo_1911.04592.md](reading_notes/orourke_chan_simplified_pepo_1911.04592.md))

## mixed-canonical matrix-product-state cut (concept)

- **defines** — Time-evolution methods for matrix-product states — `Secs. 2.4–2.6.1, Eqs. (11)–(15) and Figs. 4–6`, PDF p. 7 — A mixed-canonical matrix-product-state cut supplies orthonormal effective bases on both sides of the selected bond, so the bond tensor can be treated as the coefficient matrix for that bipartition. ([docs/papers/reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md](reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md))

## monotonic convergence (concept)

- **supports** — Simulation of IBM's kicked Ising experiment with Projected Entangled Pair Operator — `Sec. IV B and Fig. 3`, PDF p. 5 — For the 20-step `Z_62` expectation, the paper observes monotonic convergence with increasing `chi` in the intermediate-angle regime and fits the finite-`chi` values with `b exp(-a/chi)` to extrapolate toward infinite bond dimension. ([docs/papers/reading_notes/liao_heisenberg_pepo_2308.03082.md](reading_notes/liao_heisenberg_pepo_2308.03082.md))

## TDVP error decomposition (concept)

- **defines** — Time-evolution methods for matrix-product states — `Sec. 6.2.2, complete error discussion`, PDF p. 49 — The TDVP error decomposition contains finite-manifold projection error, finite time-step error, two-site SVD truncation error, and inexact local-solver error. ([docs/papers/reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md](reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md))

## TEBD time-step and truncation errors (concept)

- **defines** — Time-evolution methods for matrix-product states — `Sec. 4.1.1, first and final paragraphs`, PDF p. 18 — TEBD time-step and truncation errors are distinct: the Trotter error is controlled by step size and decomposition order, while MPS truncation is controlled by discarded weight or bond dimension and can affect unitarity and conserved quantities. ([docs/papers/reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md](reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md))

## DLM twirl (limitation)

- **limits** — Quantification and Characterization of Leakage Errors — `Sec. VI.A.3, Eq. (49) and its preceding paragraph`, PDF p. 8 — The printed DLM twirl introduces independent leakage-subspace unitaries `U_2,V_2` and sums over both, while Eq. (49) divides by only one factor of `|P_2|`. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## error-correction-regime projection (limitation)

- **limits** — Heralded Leakage Detection with Preserved Computational-State Coherence in a Fixed-Frequency Transmon — `Supplemental Sec. IX, opening paragraphs`, PDF p. 16 — The error-correction-regime projection assumes leakage population below about one percent and treats post-detection ge-to-f late flips as flagged in the subsequent detection cycle, so that contribution is not counted as an unheralded error. ([docs/papers/reading_notes/miyamura_heralded_leakage_2607.17204v1.md](reading_notes/miyamura_heralded_leakage_2607.17204v1.md))

## finite-boundary-dimension sampling (limitation)

- **limits** — Simulating and Sampling from Quantum Circuits with 2D Tensor Networks — `Section IV, first paragraph on finite-dimensional pathological states, page 9`, PDF p. 9 — The source limits finite-boundary-dimension sampling by noting that some finite-dimensional tensor-network states require boundary dimension exponential in system size for perfect sampling. ([docs/papers/reading_notes/rudolph_tindall_gpu_peps_2507.11424.md](reading_notes/rudolph_tindall_gpu_peps_2507.11424.md))

## identity norm matrix (limitation)

- **limits** — Algorithms for finite projected entangled pair states — `Sec. III.B.2, first three paragraphs`, PDF p. 7 — An open-boundary MPS can be gauged so that its local norm matrix is the identity, while a generic PEPS has no local gauge transformation that guarantees an identity norm matrix. ([docs/papers/reading_notes/lubasch_finite_peps_1405.3259_source_review.md](reading_notes/lubasch_finite_peps_1405.3259_source_review.md))

## leakage randomized benchmarking decay model (limitation)

- **limits** — Quantification and Characterization of Leakage Errors — `Sec. III, assumptions (i)--(ii)`, PDF p. 3 — The leakage randomized benchmarking decay model requires computational-subspace twirling to average cross-subspace coherence and the leakage-subspace population to be depolarized. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## monotone bond-dimension convergence (limitation)

- **contradicts** — On the stability of the infinite Projected Entangled Pair Operator ansatz for driven-dissipative 2D lattices — `Section 2.2, Figure 6 and accompanying text, pages 6-8`, PDF p. 7 — The reported simulations contradict monotone bond-dimension convergence because increasing D can destroy a previously stationary simple-update iPEPO history. ([docs/papers/reading_notes/kilda_ipepo_stability_2012.03095.md](reading_notes/kilda_ipepo_stability_2012.03095.md))

## nonlinear trajectory observable (limitation)

- **limits** — One-dimensional many-body entangled open quantum systems with tensor network methods — `Sec. III.B, Eq. (27) and the following paragraph`, PDF p. 12 — A nonlinear trajectory observable such as density-matrix purity is not the average of the corresponding pure-trajectory value and can require all pairwise trajectory contractions. ([docs/papers/reading_notes/jaschke_open_system_tn_1804.09796_source_review.md](reading_notes/jaschke_open_system_tn_1804.09796_source_review.md))

## rank-one simple-update environment (limitation)

- **limits** — Efficient Time Evolution of 2D Open-Quantum Lattice Models with Long-Range Interactions using Tensor Networks — `Section V.C and Discussion, pages 8 and 13`, PDF p. 13 — The itrSU truncation retains a rank-one simple-update environment made from bond matrices, and the source calls this environment approximation uncontrolled. ([docs/papers/reading_notes/tepepo_2d_open_system_tn_2512.01781.md](reading_notes/tepepo_2d_open_system_tn_2512.01781.md))

## residual leakage (limitation)

- **limits** — Practical quantum error correction with the XZZX code and Kerr-cat qubits — `Sec. IV.B, paragraph beginning with leakage suppression at the physical level`, PDF p. 10 — After suppressing Kerr-cat leakage at the physical-operation level, the source neglects the residual leakage in its subsequent surface-code simulations. ([docs/papers/reading_notes/darmawan_xzzx_circuit_2104.09539_source_review.md](reading_notes/darmawan_xzzx_circuit_2104.09539_source_review.md))

## sequential cutwise SVD local optimality (limitation)

- **limits** — Time-evolution methods for matrix-product states — `Sec. 2.6.1, final paragraph`, PDF p. 9 — Sequential cutwise SVD local optimality does not guarantee a globally optimal compressed matrix-product state when truncation errors are large. ([docs/papers/reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md](reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md))

## single-site jump-operator factorization (limitation)

- **limits** — Large-scale stochastic simulation of open quantum systems — `Sec. III.D, Eqs. (38)–(40)`, PDF p. 7 — The paper's exact dissipative contraction is a single-site jump-operator factorization whose local factors commute, do not increase MPS bond dimension, and are contracted sitewise. ([docs/papers/reading_notes/sander_tensor_jump_2501.17913_source_review.md](reading_notes/sander_tensor_jump_2501.17913_source_review.md))

## solver-induced norm error (limitation)

- **limits** — One-dimensional many-body entangled open quantum systems with tensor network methods — `Sec. III.B, paragraph immediately after Eq. (25)`, PDF p. 11 — Solver-induced norm error can contaminate the physical norm loss used for quantum-trajectory jump timing because the local Runge–Kutta method can enhance or prevent the loss caused by the effective Hamiltonian. ([docs/papers/reading_notes/jaschke_open_system_tn_1804.09796_source_review.md](reading_notes/jaschke_open_system_tn_1804.09796_source_review.md))

## alternating ancilla pi-pulse scheme (method)

- **uses** — Leakage detection for a transmon-based surface code — `Appendix G, opening paragraph spanning PDF pp. 18-19`, PDF p. 19 — The alternating ancilla pi-pulse scheme applies a pi pulse to each ancilla every other cycle and compensates it in post-processing so that a leaked ancilla, assumed unaffected by the pulse, would create a defect every cycle. ([docs/papers/reading_notes/varbanov_leakage_detection_surface17_2002.07119.md](reading_notes/varbanov_leakage_detection_surface17_2002.07119.md))

## ancilla-assisted measurement of a single sigma-z operator (method)

- **defines** — Understanding the effects of leakage in superconducting quantum error detection circuits — `Abstract and Sec. I, PDF p. 1`, PDF p. 1 — The source studies repeated ancilla-assisted measurement of a single sigma-z operator for one data qutrit and analyzes leakage signatures in the ancilla readout sequence. ([docs/papers/reading_notes/ghosh_leakage_paralysis_1306.0925v2.md](reading_notes/ghosh_leakage_paralysis_1306.0925v2.md))

## boundary gMPO method (method)

- **supports** — A simplified and improved approach to tensor network operators in two dimensions — `Sec. III B, steps 1--6 and Fig. 4(c)--(g)`, PDF p. 6 — The boundary gMPO method precomputes upper norm environments, initializes a running energy from a bottom-row MPO, carries crossing interactions in `intops`, and alternates row gMPO contraction with an approximate `intops` update until the final scalar `<psi|H|psi>` is accumulated. ([docs/papers/reading_notes/orourke_chan_simplified_pepo_1911.04592.md](reading_notes/orourke_chan_simplified_pepo_1911.04592.md))

## corresponding plus or minus X eigenstate (method)

- **defines** — Practical quantum error correction with the XZZX code and Kerr-cat qubits — `Sec. III.B.4, Fig. 6 and adjacent paragraph`, PDF p. 7 — After projective readout places the measured ancilla in computational state zero or one conditional on the outcome, inverse rotations prepare the corresponding plus or minus X eigenstate for the next syndrome round. ([docs/papers/reading_notes/darmawan_xzzx_circuit_2104.09539_source_review.md](reading_notes/darmawan_xzzx_circuit_2104.09539_source_review.md))

## CTMRG projector truncation (method)

- **defines** — An introduction to infinite projected entangled-pair state methods for variational ground state simulations using automatic differentiation — `Sec. 2.2.2, Figs. 7--8 and Eqs. (4)--(6)`, PDF p. 10 — CTMRG projector truncation singular-value decomposes an approximate lattice-environment matrix `M=rho_B rho_T` and retains the leading `chi_E` singular subspace. ([docs/papers/reading_notes/naumann_varipeps_lectures_source_review.md](reading_notes/naumann_varipeps_lectures_source_review.md))

## direct binary leakage measurement (method)

- **defines** — Heralded Leakage Detection with Preserved Computational-State Coherence in a Fixed-Frequency Transmon — `Fig. 1 and accompanying text`, PDF p. 2 — The direct binary leakage measurement applies a near-resonant computational-transition Rabi drive during dispersive probing so the resonator responses of ground and first-excited states merge while the measured second-excited-state response remains distinct. ([docs/papers/reading_notes/miyamura_heralded_leakage_2607.17204v1.md](reading_notes/miyamura_heralded_leakage_2607.17204v1.md))

## echo pulse breaks leakage paralysis (method)

- **supports** — Protecting quantum entanglement from qubit errors and leakage via repetitive parity measurements — `Supplemental Sec. II.B, parenthetical sentence after the ZZ-and-XX effective-check example`, PDF p. 11 — In the repeated-ZZ experiment, the echo pulse breaks leakage paralysis by flipping the effective stabilizer of a leaked qubit on each round. ([docs/papers/reading_notes/bultink_repetitive_parity_leakage_1905.12731v1.md](reading_notes/bultink_repetitive_parity_leakage_1905.12731v1.md))

## finite-signaling-agent tePEPO construction (method)

- **defines** — Efficient Time Evolution of 2D Open-Quantum Lattice Models with Long-Range Interactions using Tensor Networks — `Section III.B, Eq. (7), Tables I-II, and Algorithm 1, pages 5-6`, PDF p. 5 — The finite-signaling-agent tePEPO construction assigns operator-valued rules to combinations of four virtual-edge signals and rejects signal patterns that do not encode accepted cluster terms. ([docs/papers/reading_notes/tepepo_2d_open_system_tn_2512.01781.md](reading_notes/tepepo_2d_open_system_tn_2512.01781.md))

## full-environment truncation (method)

- **defines** — Gauge fixing, canonical forms, and optimal truncations in tensor networks with closed loops — `Sec. V, Eq. (12) and Fig. 5`, PDF p. 6 — Full-environment truncation replaces a selected bond by a lower-rank factorization and chooses its factors to maximize normalized whole-network pure-state fidelity. ([docs/papers/reading_notes/evenbly_closed_loop_truncation_1801.05390_source_review.md](reading_notes/evenbly_closed_loop_truncation_1801.05390_source_review.md))

## Gaussian long-range approximation (method)

- **uses** — Efficient Time Evolution of 2D Open-Quantum Lattice Models with Long-Range Interactions using Tensor Networks — `Section IV, Eqs. (9)-(12) and Table III, pages 6-7`, PDF p. 7 — The Gaussian long-range approximation fits a radial interaction profile on a finite lattice disc by a weighted sum of separable Gaussian functions that each admit FSA rules. ([docs/papers/reading_notes/tepepo_2d_open_system_tn_2512.01781.md](reading_notes/tepepo_2d_open_system_tn_2512.01781.md))

## Heisenberg PEPO evolution (method)

- **supports** — Simulation of IBM's kicked Ising experiment with Projected Entangled Pair Operator — `Sec. III, paragraphs below Eqs. (4)--(5)`, PDF p. 3 — Heisenberg PEPO evolution represents the time-evolved observable as a PEPO, applies each gate together with its conjugate from the middle toward the two temporal boundaries, compresses by simple-update singular-value decompositions, and exactly contracts the final tensor network to a scalar expectation. ([docs/papers/reading_notes/liao_heisenberg_pepo_2308.03082.md](reading_notes/liao_heisenberg_pepo_2308.03082.md))

## iPEPO density-operator evolution (method)

- **defines** — On the stability of the infinite Projected Entangled Pair Operator ansatz for driven-dissipative 2D lattices — `Appendix A.2, first three paragraphs, page 15`, PDF p. 15 — The iPEPO density-operator evolution vectorizes a PEPO into a PEPS-shaped state and replaces imaginary-time Hamiltonian gates by real-time two-body Liouvillian gates. ([docs/papers/reading_notes/kilda_ipepo_stability_2012.03095.md](reading_notes/kilda_ipepo_stability_2012.03095.md))

## iterative simple-update truncation (method)

- **defines** — Efficient Time Evolution of 2D Open-Quantum Lattice Models with Long-Range Interactions using Tensor Networks — `Section V.C and Appendix D, pages 8-9 and 18`, PDF p. 18 — The iterative simple-update truncation reuses previous-step isometries on every non-target bond, performs a QR and truncated SVD on the remaining bond, updates the isometries and bond weight, and repeats over all bonds. ([docs/papers/reading_notes/tepepo_2d_open_system_tn_2512.01781.md](reading_notes/tepepo_2d_open_system_tn_2512.01781.md))

## neighborhood tensor update (method)

- **defines** — Time evolution of an infinite projected entangled pair state: a neighborhood tensor update — `Sec. II, Figs. 3--4`, PDF p. 4 — Neighborhood tensor update contracts a finite nearest-neighbor double-layer cluster exactly to obtain a metric that is Hermitian and nonnegative to machine precision. ([docs/papers/reading_notes/dziarmaga_ntu_2107.06635_source_review.md](reading_notes/dziarmaga_ntu_2107.06635_source_review.md))

## quantum-trajectory jump-channel selection (method)

- **defines** — One-dimensional many-body entangled open quantum systems with tensor network methods — `Sec. III.B, steps (a)–(c) and Fig. 3`, PDF p. 12 — Quantum-trajectory jump-channel selection normalizes the expectations `p_nu = <psi|L_nu^dagger L_nu|psi>`, samples one channel, applies its Lindblad operator, and then renormalizes the state. ([docs/papers/reading_notes/jaschke_open_system_tn_1804.09796_source_review.md](reading_notes/jaschke_open_system_tn_1804.09796_source_review.md))

## selective measurement update (method)

- **defines** — On-State Commutativity of Measurements and Joint Distributions of Their Outcomes — `Sec. 2.2, Eq. (1)`, PDF p. 5 — A selective measurement update assigns outcome probability `Tr(Q_x rho)` and post-measurement state `A_x rho A_x^dagger/Tr(Q_x rho)` when `Q_x=A_x^dagger A_x`. ([docs/papers/reading_notes/czajkowski_grilo_sequential_measurements_2101.08313_source_review.md](reading_notes/czajkowski_grilo_sequential_measurements_2101.08313_source_review.md))

## tensor jump method (method)

- **defines** — Large-scale stochastic simulation of open quantum systems — `Sec. III.A, Eqs. (14)–(20) and Fig. 1`, PDF p. 5 — The tensor jump method composes dynamic TDVP, dissipative contraction, and stochastic jumping through a sampling MPS whose reordered evolution permits physical-state retrieval at requested time steps. ([docs/papers/reading_notes/sander_tensor_jump_2501.17913_source_review.md](reading_notes/sander_tensor_jump_2501.17913_source_review.md))

## terminal tensor-network sampling method (method)

- **defines** — Simulating and Sampling from Quantum Circuits with 2D Tensor Networks — `Section II, sampling definitions and procedure, page 4`, PDF p. 4 — The terminal tensor-network sampling method draws a final computational-basis bitstring x from q(x), while p(x)=|<x|psi>|^2 is the terminal distribution encoded by the final tensor-network state. ([docs/papers/reading_notes/rudolph_tindall_gpu_peps_2507.11424.md](reading_notes/rudolph_tindall_gpu_peps_2507.11424.md))

## two-hidden-state leakage model (method)

- **defines** — Leakage detection for a transmon-based surface code — `Appendix E, Eqs. (E1)-(E6)`, PDF p. 17 — The two-hidden-state leakage model uses computational and leaked states, a transition matrix parameterized by leakage and seepage per cycle, state-dependent defect emissions, and a Bayesian posterior update. ([docs/papers/reading_notes/varbanov_leakage_detection_surface17_2002.07119.md](reading_notes/varbanov_leakage_detection_surface17_2002.07119.md))

## XZZX check (method)

- **defines** — Practical quantum error correction with the XZZX code and Kerr-cat qubits — `Sec. II.A, Fig. 2(a-b), caption, and adjacent circuit description`, PDF p. 3 — One XZZX check is measured by preparing a face ancilla in the plus state, applying an ordered CZ, CX, CX, CZ sequence to its four data neighbors, and measuring the ancilla in the Pauli-X basis. ([docs/papers/reading_notes/darmawan_xzzx_circuit_2104.09539_source_review.md](reading_notes/darmawan_xzzx_circuit_2104.09539_source_review.md))

## YASTN layered architecture (method)

- **defines** — YASTN: Yet another symmetric tensor networks; A Python library for Abelian symmetric tensor network calculations — `Sec. 2 and Fig. 2`, PDF p. 4 — The YASTN layered architecture separates Abelian symmetry structure from dense numerical backends in `yastn.Tensor` and builds higher-level MPS and fPEPS modules above that symmetric-tensor layer. ([docs/papers/reading_notes/rams_yastn_codebase_source_review.md](reading_notes/rams_yastn_codebase_source_review.md))

## binary projection character (model)

- **supports** — Heralded Leakage Detection with Preserved Computational-State Coherence in a Fixed-Frequency Transmon — `Supplemental Sec. VII and Fig. S7`, PDF p. 15 — The binary projection character is supported by a coherent three-level input whose ground-first coherence is largely retained while ground-second and first-second coherences are strongly suppressed. ([docs/papers/reading_notes/miyamura_heralded_leakage_2607.17204v1.md](reading_notes/miyamura_heralded_leakage_2607.17204v1.md))

## depolarizing leakage extension (model)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. VI.A.2, Eqs. (46)--(47)`, PDF p. 8 — The depolarizing leakage extension of a computational-subspace channel is the model in Eq. (46), parameterized by leakage and seepage rates and completely depolarizing maps between the two subspaces. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## depolarizing leakage model (model)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. VI.A.3, Eq. (48)`, PDF p. 8 — The depolarizing leakage model is the DLE special case in Eq. (48) whose computational-subspace component is depolarizing. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## diagonal pure-dephasing rate (model)

- **defines** — Fundamental Speed Limits on Quantum Coherence and Correlation Decay — `Results, Eqs. (1)–(4)`, PDF p. 2 — A diagonal pure-dephasing rate is one half the summed squared diagonal entries minus their real cross product, and each coherence magnitude decays exponentially at that rate. ([docs/papers/reading_notes/oi_schirmer_pure_dephasing_1109.0954_source_review.md](reading_notes/oi_schirmer_pure_dephasing_1109.0954_source_review.md))

## effective N-minus-one-qubit parity check (model)

- **defines** — Protecting quantum entanglement from qubit errors and leakage via repetitive parity measurements — `Supplemental Sec. II.B, paragraph beginning with an N-qubit parity check`, PDF p. 11 — A leaked site reduces an N-qubit stabilizer measurement to an effective N-minus-one-qubit parity check plus a fixed phase from the leaked interaction. ([docs/papers/reading_notes/bultink_repetitive_parity_leakage_1905.12731v1.md](reading_notes/bultink_repetitive_parity_leakage_1905.12731v1.md))

## effective weight-three parity checks (model)

- **defines** — Leakage detection for a transmon-based surface code — `Appendix D, Eq. (D13) and following paragraph`, PDF p. 16 — At leakage conditional phase zero or pi, the branch operators become projectors onto effective weight-three parity checks and their anti-commutation fully randomizes individual ancilla outcomes. ([docs/papers/reading_notes/varbanov_leakage_detection_surface17_2002.07119.md](reading_notes/varbanov_leakage_detection_surface17_2002.07119.md))

## finite open-boundary PEPS (model)

- **defines** — Algorithms for finite projected entangled pair states — `Sec. II, PEPS definition and Fig. 1`, PDF p. 2 — The source studies a finite open-boundary PEPS on a square lattice, with one physical index per lattice site and virtual bond dimension `D`. ([docs/papers/reading_notes/lubasch_finite_peps_1405.3259_source_review.md](reading_notes/lubasch_finite_peps_1405.3259_source_review.md))

## finite-temperature relaxation generator (model)

- **defines** — Exact and Efficient Stabilizer Simulation of Thermal-Relaxation Noise for Quantum Error Correction — `Sec. II.A, Eqs. (1)–(2)`, PDF p. 3 — The finite-temperature relaxation generator contains downward `gamma(n_bar+1)D[|0><1|]`, upward `gamma n_bar D[|1><0|]`, and pure-dephasing `(gamma_phi/2)D[sigma_z]` terms under one explicit dissipator convention. ([docs/papers/reading_notes/garner_thermal_relaxation_2512.09189_source_review.md](reading_notes/garner_thermal_relaxation_2512.09189_source_review.md))

## generalized amplitude-damping channel (model)

- **derives** — Microscopic derivation of the one qubit Kraus operators for amplitude and phase damping — `Sec. 3, Eqs. (17)–(18)`, PDF p. 5 — The finite-temperature master equation generates a generalized amplitude-damping channel with four Kraus branches and distinct positive downward and upward rates. ([docs/papers/reading_notes/arsenijevic_bankovic_damping_1606.01145_source_review.md](reading_notes/arsenijevic_bankovic_damping_1606.01145_source_review.md))

## incorrect stabilizer outcome (model)

- **uses** — The XZZX surface code — `Fault-tolerant threshold model, paragraph below Fig. 5`, PDF p. 6 — The fault-tolerant numerical study uses independent data Pauli errors and an independent incorrect stabilizer outcome with probability q equal to the sum of its declared high-rate and low-rate error probabilities. ([docs/papers/reading_notes/bonilla_ataides_xzzx_2009.07851_source_review.md](reading_notes/bonilla_ataides_xzzx_2009.07851_source_review.md))

## leakage conditional phases (model)

- **defines** — Leakage detection for a transmon-based surface code — `Sec. I.A, definitions following the CZ model`, PDF p. 2 — The leakage conditional phases are the phase differences imposed on the computational partner when either the fluxed or static CZ partner is leaked. ([docs/papers/reading_notes/varbanov_leakage_detection_surface17_2002.07119.md](reading_notes/varbanov_leakage_detection_surface17_2002.07119.md))

## leakage phase theta (model)

- **defines** — Understanding the effects of leakage in superconducting quantum error detection circuits — `Sec. II.A, Eqs. (7)-(8)`, PDF p. 3 — The leakage phase theta is defined as xi2 minus xi1 and is the dynamical phase difference that determines whether the ancilla becomes paralyzed during a data-leakage event. ([docs/papers/reading_notes/ghosh_leakage_paralysis_1306.0925v2.md](reading_notes/ghosh_leakage_paralysis_1306.0925v2.md))

## Lindblad leakage model (model)

- **uses** — Quantification and Characterization of Leakage Errors — `Sec. VI.C, Eqs. (69)--(70)`, PDF p. 10 — A Lindblad leakage model is written as `E = exp[t(mathcal H + mathcal D)]`, where superoperator `mathcal H` acts as `mathcal H(rho) = -i[H,rho]` for Hamiltonian `H` and `mathcal D` is presented as the dissipative generator. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## locally purified tensor network (model)

- **defines** — A positive tensor network approach for simulating open quantum many-body systems — `Main text, Eq. (3) and Fig. 1(a)`, PDF p. 2 — A locally purified tensor network represents the density operator as `rho = X X^dagger`, with `X` decomposed into local tensors carrying physical, bond, and Kraus indices. ([docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md](reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md))

## PEPS construction (model)

- **defines** — Computational Complexity of Projected Entangled Pair States — `“PEPS and postselection,” p. 1, right column`, PDF p. 1 — The PEPS construction starts from an arbitrary undirected graph, places dimension-`D` maximally entangled virtual pairs along its edges, and applies a local linear map from the incident virtual spaces to a dimension-`d` physical space at every vertex. ([docs/papers/reading_notes/schuch_peps_complexity_prl_98_140506_source_review.md](reading_notes/schuch_peps_complexity_prl_98_140506_source_review.md))

## phase-damping channel (model)

- **defines** — Microscopic derivation of the one qubit Kraus operators for amplitude and phase damping — `Sec. 4, Eqs. (48)–(49)`, PDF p. 12 — The phase-damping channel obeys `d rho/dt=r(sigma_z rho sigma_z-rho)` and is derived as pure decoherence without energy loss. ([docs/papers/reading_notes/arsenijevic_bankovic_damping_1606.01145_source_review.md](reading_notes/arsenijevic_bankovic_damping_1606.01145_source_review.md))

## quantum-trajectory effective non-Hermitian Hamiltonian (model)

- **defines** — One-dimensional many-body entangled open quantum systems with tensor network methods — `Sec. III.B, Eq. (25)`, PDF p. 11 — The quantum-trajectory effective non-Hermitian Hamiltonian is the system Hamiltonian minus one half of `i` times the sum of `L_nu^dagger L_nu`, and its norm loss is used to determine jump timing. ([docs/papers/reading_notes/jaschke_open_system_tn_1804.09796_source_review.md](reading_notes/jaschke_open_system_tn_1804.09796_source_review.md))

## simple dissipative leakage model (model)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. VI.C.1, Eq. (72)`, PDF p. 11 — The simple dissipative leakage model uses jump `A_21 = |2><1|` with rate `gamma_1` for leakage and jump `A_12 = |1><2|` with rate `gamma_2` for seepage. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## state-reset channel (model)

- **defines** — Exact and Efficient Stabilizer Simulation of Thermal-Relaxation Noise for Quantum Error Correction — `Sec. II.C, Eq. (22)`, PDF p. 5 — The amplitude-damping decomposition includes a state-reset channel `R_|0>` that maps its branch to the state `|0>`. ([docs/papers/reading_notes/garner_thermal_relaxation_2512.09189_source_review.md](reading_notes/garner_thermal_relaxation_2512.09189_source_review.md))

## thermal down/up Lindblad generator (model)

- **defines** — Microscopic derivation of the one qubit Kraus operators for amplitude and phase damping — `Sec. 3, Eq. (16)`, PDF p. 5 — The microscopic thermal master equation contains a thermal down/up Lindblad generator with downward coefficient `2 pi J(omega_0)(n_bar+1)` and upward coefficient `2 pi J(omega_0)n_bar`. ([docs/papers/reading_notes/arsenijevic_bankovic_damping_1606.01145_source_review.md](reading_notes/arsenijevic_bankovic_damping_1606.01145_source_review.md))

## unitary leakage model (model)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. VI.B, Eqs. (57)--(58), first equality`, PDF p. 9 — The unitary leakage model starts from `H = (|1><2| + |2><1|)/2` and defines its propagator by `U(t) = exp(-i t H)`. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## XZZX bulk face check (model)

- **defines** — The XZZX surface code — `Results, Fig. 1(a) and caption`, PDF p. 2 — The XZZX bulk face check is a product of two Pauli-X terms and two Pauli-Z terms on square-lattice vertices, and the same stabilizer form is used at every bulk face. ([docs/papers/reading_notes/bonilla_ataides_xzzx_2009.07851_source_review.md](reading_notes/bonilla_ataides_xzzx_2009.07851_source_review.md))

## ancilla paralysis (observable)

- **defines** — Understanding the effects of leakage in superconducting quantum error detection circuits — `Sec. III.B, Eq. (24), following paragraph, and Fig. 4`, PDF p. 6 — The source labels theta modulo pi equal to zero as ancilla paralysis and describes it as a deterministic all-zero readout with no indication of the leaked data state. ([docs/papers/reading_notes/ghosh_leakage_paralysis_1306.0925v2.md](reading_notes/ghosh_leakage_paralysis_1306.0925v2.md))

## balanced detection fidelity (observable)

- **measures** — Heralded Leakage Detection with Preserved Computational-State Coherence in a Fixed-Frequency Transmon — `Fig. 3 and Eq. (5)`, PDF p. 4 — For prepared ground, first-excited, and second-excited states, an eighty-nanosecond window gives false-flag rate 2.3(3) percent, undetected-leakage rate 3.5(2) percent, and balanced detection fidelity 97.1(3) percent. ([docs/papers/reading_notes/miyamura_heralded_leakage_2607.17204v1.md](reading_notes/miyamura_heralded_leakage_2607.17204v1.md))

## bond-spectrum stationarity diagnostic (observable)

- **defines** — On the stability of the infinite Projected Entangled Pair Operator ansatz for driven-dissipative 2D lattices — `Section 2, Eq. (3) and Figure 2, page 4`, PDF p. 4 — The bond-spectrum stationarity diagnostic epsilon_Lambda is the maximum consecutive-step singular-value change divided by the timestep and the current maximum singular value. ([docs/papers/reading_notes/kilda_ipepo_stability_2012.03095.md](reading_notes/kilda_ipepo_stability_2012.03095.md))

## bond-weight convergence indicator (observable)

- **measures** — Efficient Time Evolution of 2D Open-Quantum Lattice Models with Long-Range Interactions using Tensor Networks — `Eq. (15), pages 8-9; Figure 11, page 13`, PDF p. 8 — The bond-weight convergence indicator is used to stop itrSU and, after division by the timestep, to plot convergence toward a steady state, but Eq. (15) is typeset as an inequality rather than an unambiguous definition. ([docs/papers/reading_notes/tepepo_2d_open_system_tn_2512.01781.md](reading_notes/tepepo_2d_open_system_tn_2512.01781.md))

## channel coherent leakage and seepage rates (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. V.B, Eqs. (42)--(43)`, PDF p. 7 — The channel coherent leakage and seepage rates are Haar averages of `C_L(E(|psi_j><psi_j|))` over rank-one projectors formed from all Haar-distributed pure states in subspaces `X_j`, for `j=1,2`. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## coherence of leakage (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. V.A, Eqs. (30)--(34)`, PDF p. 6 — The coherence of leakage of a state is `C_L(rho) = ||P_C(rho)||_1`, where `P_C(rho) = 1_1 rho 1_2 + 1_2 rho 1_1` is the cross-subspace block. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## computational-subspace likelihood (observable)

- **defines** — Protecting quantum entanglement from qubit errors and leakage via repetitive parity measurements — `Main text following Fig. 2, HMM definition paragraph`, PDF p. 3 — The hidden Markov model returns a computational-subspace likelihood from the observed parity-outcome string by alternating Markov evolution with Bayesian measurement updates. ([docs/papers/reading_notes/bultink_repetitive_parity_leakage_1905.12731v1.md](reading_notes/bultink_repetitive_parity_leakage_1905.12731v1.md))

## conditional average state fidelity (observable)

- **measures** — Heralded Leakage Detection with Preserved Computational-State Coherence in a Fixed-Frequency Transmon — `Fig. 4 and accompanying text`, PDF p. 5 — For a target equal mixture of computational and second-excited-state population, no-leakage post-selection gives conditional average state fidelity 92.9(5) percent over six cardinal states. ([docs/papers/reading_notes/miyamura_heralded_leakage_2607.17204v1.md](reading_notes/miyamura_heralded_leakage_2607.17204v1.md))

## data-leakage syndrome (observable)

- **defines** — Protecting quantum entanglement from qubit errors and leakage via repetitive parity measurements — `Supplemental Sec. II.A, data-qubit leakage model`, PDF p. 10 — The repeated-ZZ data-leakage syndrome is defined as the product of ancilla outcomes two rounds apart, sD at round m equals MA at m times MA at m-minus-two. ([docs/papers/reading_notes/bultink_repetitive_parity_leakage_1905.12731v1.md](reading_notes/bultink_repetitive_parity_leakage_1905.12731v1.md))

## defect (observable)

- **defines** — Practical quantum error correction with the XZZX code and Kerr-cat qubits — `Sec. II.B, opening decoder definition`, PDF p. 3 — A defect occurs at face f and time t when the product of the check outcomes at times t minus one and t equals minus one. ([docs/papers/reading_notes/darmawan_xzzx_circuit_2104.09539_source_review.md](reading_notes/darmawan_xzzx_circuit_2104.09539_source_review.md))

## direct-SVD discarded weight (observable)

- **defines** — Time-evolution methods for matrix-product states — `Sec. 2.6.1, Eq. (17) and the paragraph immediately following it`, PDF p. 9 — The direct-SVD approximation error at one canonical cut is the square root of the direct-SVD discarded weight, defined as the sum of the squared omitted singular values. ([docs/papers/reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md](reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md))

## dynamic-TDVP projection error (observable)

- **defines** — Large-scale stochastic simulation of open quantum systems — `Sec. IV.C, Eqs. (57)–(58)`, PDF p. 11 — The dynamic-TDVP projection error is the 2-norm of the component of `H_0|Phi>` outside the chosen MPS tangent space, and the one-site projector minimizes this local residual inside that space. ([docs/papers/reading_notes/sander_tensor_jump_2501.17913_source_review.md](reading_notes/sander_tensor_jump_2501.17913_source_review.md))

## leakage rate (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. II, Eq. (2)`, PDF p. 2 — For a CPTP map `E`, the leakage rate is `L_1(E) = L(E(1_1/d_1))` and the seepage rate is `L_2(E) = 1 - L(E(1_2/d_2))`, equal to Haar averages over input states in the respective subspaces. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## MCWF norm-deficit jump probability (observable)

- **defines** — Large-scale stochastic simulation of open quantum systems — `Sec. II.B, Eqs. (2)–(11)`, PDF p. 3 — The MCWF norm-deficit jump probability is `delta p = 1 - ||Psi^(i)(t+delta t)||^2`, with channel contributions `delta p_m = delta t gamma_m <Psi|L_m^dagger L_m|Psi>` normalized only after a jump is selected. ([docs/papers/reading_notes/sander_tensor_jump_2501.17913_source_review.md](reading_notes/sander_tensor_jump_2501.17913_source_review.md))

## ordered projective outcome law (observable)

- **defines** — On-State Commutativity of Measurements and Joint Distributions of Their Outcomes — `Sec. 3.1, Eq. (9)`, PDF p. 7 — For projectors `A` followed by `B`, the ordered projective outcome law assigns probability `Tr(A B A rho)`, whereas the reversed order generally gives `Tr(B A B rho)`. ([docs/papers/reading_notes/czajkowski_grilo_sequential_measurements_2101.08313_source_review.md](reading_notes/czajkowski_grilo_sequential_measurements_2101.08313_source_review.md))

## parity-outcome string (observable)

- **measures** — Protecting quantum entanglement from qubit errors and leakage via repetitive parity measurements — `Main text following Fig. 2, paragraph beginning with leakage inference from the outcome string`, PDF p. 3 — Data-qubit leakage produces an apparent-error parity-outcome string with pairs of equal signs, exemplified by plus, plus, minus, minus, because the echo pulses act only on the unleaked data qubit. ([docs/papers/reading_notes/bultink_repetitive_parity_leakage_1905.12731v1.md](reading_notes/bultink_repetitive_parity_leakage_1905.12731v1.md))

## purification discarded weight (observable)

- **defines** — A positive tensor network approach for simulating open quantum many-body systems — `Appendix D, Definition 5 and Eq. (55)`, PDF p. 10 — Purification discarded weight is the square root of the sum of squared singular values omitted when one mixed-canonical local tensor is compressed along a bond or Kraus index. ([docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md](reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md))

## sample KL divergence (observable)

- **defines** — Simulating and Sampling from Quantum Circuits with 2D Tensor Networks — `Section II, Eq. (6), page 4`, PDF p. 4 — The sample KL divergence is defined as KLD(q,p)=E under q of log(q(x)/p(x)) for the terminal bitstring distributions. ([docs/papers/reading_notes/rudolph_tindall_gpu_peps_2507.11424.md](reading_notes/rudolph_tindall_gpu_peps_2507.11424.md))

## sample probability ratio (observable)

- **defines** — Simulating and Sampling from Quantum Circuits with 2D Tensor Networks — `Section II, Eq. (5), page 4`, PDF p. 4 — The sample probability ratio p(x)/q(x) has expectation under q equal to the norm of the represented tensor-network state. ([docs/papers/reading_notes/rudolph_tindall_gpu_peps_2507.11424.md](reading_notes/rudolph_tindall_gpu_peps_2507.11424.md))

## seepage rate (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. II, Eq. (2)`, PDF p. 2 — For a CPTP map `E`, the leakage rate is `L_1(E) = L(E(1_1/d_1))` and the seepage rate is `L_2(E) = 1 - L(E(1_2/d_2))`, equal to Haar averages over input states in the respective subspaces. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## spacing metric W (observable)

- **defines** — Understanding the effects of leakage in superconducting quantum error detection circuits — `Sec. III.B, Eq. (25)`, PDF p. 6 — The spacing metric W is the average number of cycles between consecutive ancilla-one outcomes and equals cosecant-squared theta-over-two without decoherence. ([docs/papers/reading_notes/ghosh_leakage_paralysis_1306.0925v2.md](reading_notes/ghosh_leakage_paralysis_1306.0925v2.md))

## stabilizer outcome differs from its preceding outcome (observable)

- **defines** — The XZZX surface code — `Fault-tolerant threshold discussion, Fig. 5(a-d) and caption`, PDF p. 6 — In the repeated-measurement phenomenological model, a defect is identified when a stabilizer outcome differs from its preceding outcome. ([docs/papers/reading_notes/bonilla_ataides_xzzx_2009.07851_source_review.md](reading_notes/bonilla_ataides_xzzx_2009.07851_source_review.md))

## state leakage (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. II, Eq. (1)`, PDF p. 2 — State leakage is the population outside computational subspace `X_1`, defined by `L(rho) = Tr[1_2 rho] = 1 - Tr[1_1 rho]` on the direct sum `X = X_1 direct-sum X_2`. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## surface-code defect (observable)

- **defines** — Leakage detection for a transmon-based surface code — `Sec. I.B, paragraph defining syndrome and defect bits`, PDF p. 3 — With ancillas left unreset, the surface-code defect is defined as d at cycle n equals m at n XOR m at n-minus-two, and a measured level two is declared as bit one. ([docs/papers/reading_notes/varbanov_leakage_detection_surface17_2002.07119.md](reading_notes/varbanov_leakage_detection_surface17_2002.07119.md))

## thermal equilibrium population (observable)

- **defines** — Exact and Efficient Stabilizer Simulation of Thermal-Relaxation Noise for Quantum Error Correction — `Sec. II.A, Eqs. (10) and (15)`, PDF p. 3 — The thermal equilibrium population is `p_1=n_bar/(1+2n_bar)`, while the total population-relaxation rate is `gamma(2n_bar+1)`. ([docs/papers/reading_notes/garner_thermal_relaxation_2512.09189_source_review.md](reading_notes/garner_thermal_relaxation_2512.09189_source_review.md))

## weight-six supercheck (observable)

- **defines** — Leakage detection for a transmon-based surface code — `Appendix D, paragraph following Eq. (D13) and Fig. 10a`, PDF p. 16 — At leakage conditional phase zero or pi, the product of two same-type weight-three gauge outcomes defines a weight-six supercheck parity when both same-type gauges are measured before either opposite-type gauge. ([docs/papers/reading_notes/varbanov_leakage_detection_surface17_2002.07119.md](reading_notes/varbanov_leakage_detection_surface17_2002.07119.md))

## full-bond TJM convergence theorem (theorem)

- **supports** — Large-scale stochastic simulation of open quantum systems — `Sec. IV.B, Theorem 2 and Eqs. (52)–(56); Appendix B, Theorem 7 and Eqs. (B18)–(B22)`, PDF p. 10 — The full-bond TJM convergence theorem gives an unbiased fixed-time density estimator with matrix-norm standard deviation bounded by `c/sqrt(N)` when every trajectory MPS has full bond dimension. ([docs/papers/reading_notes/sander_tensor_jump_2501.17913_source_review.md](reading_notes/sander_tensor_jump_2501.17913_source_review.md))

## general tensor-network contraction (theorem)

- **limits** — Computational Complexity of Projected Entangled Pair States — `“The classical complexity of PEPS,” p. 3, left column, second paragraph`, PDF p. 3 — The source concludes that general tensor-network contraction is `#P`-complete, using PEPS contraction for hardness and constructions based on `T` with its conjugate, a physical dimension-one PEPS norm, and tensor direct sums for membership. ([docs/papers/reading_notes/schuch_peps_complexity_prl_98_140506_source_review.md](reading_notes/schuch_peps_complexity_prl_98_140506_source_review.md))

## locally purified trace-norm certificate (theorem)

- **supports** — A positive tensor network approach for simulating open quantum many-body systems — `Appendix D, Theorem 7 and Eqs. (59)–(60)`, PDF p. 11 — The locally purified trace-norm certificate bounds final-state error by `(tb)^3 N^2/(4m^2) + 6(2m+1)N delta` for a nearest-neighbor chain whose local Liouvillians have diamond norm at most `b`, using `m` second-order steps and a common upper bound `delta` on every discarded weight. ([docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md](reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md))

## paper-defined exact PEPS primitives (theorem)

- **limits** — Computational Complexity of Projected Entangled Pair States — `“The classical complexity of PEPS,” p. 3, left column, first paragraph; note [16], p. 4`, PDF p. 3 — The source concludes that the paper-defined exact PEPS primitives are `#P`-complete under weakly parsimonious reductions. ([docs/papers/reading_notes/schuch_peps_complexity_prl_98_140506_source_review.md](reading_notes/schuch_peps_complexity_prl_98_140506_source_review.md))

## postselection--PEPS duality (theorem)

- **derives** — Computational Complexity of Projected Entangled Pair States — `“PEPS and postselection,” p. 2, left column, summary paragraph`, PDF p. 2 — The postselection--PEPS duality consists of efficient transforms in both directions between postselected circuit outputs and PEPS, with the circuit-to-state direction already realized by two-dimensional `D=d=2` PEPS. ([docs/papers/reading_notes/schuch_peps_complexity_prl_98_140506_source_review.md](reading_notes/schuch_peps_complexity_prl_98_140506_source_review.md))

## Proposition 2 bound (theorem)

- **supports** — Quantification and Characterization of Leakage Errors — `Sec. V.B, Proposition 2`, PDF p. 7 — The Proposition 2 bound states `C_Lj(E) <= 2 sqrt(L_j(E)(1-L_j(E)))` for the channel coherent leakage and seepage quantities. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## purification-to-trace-norm bound (theorem)

- **supports** — A positive tensor network approach for simulating open quantum many-body systems — `Appendix A, Lemma 1 and Eqs. (20)–(25)`, PDF p. 6 — The purification-to-trace-norm bound states that normalized factorizations `rho = X X^dagger` and `sigma = Y Y^dagger` satisfy `||rho-sigma||_1 <= sqrt(2) ||X-Y||_2`, with a companion fidelity lower bound. ([docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md](reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md))
