# Current literature concept index

Generated from the explicit current corpus manifest. Only source-reviewed `paper_fact`
relationships appear here. This is routing metadata; the cited PDF and locator remain
the evidence.

- corpus status: active
- sources: 11
- concept nodes: 42
- source-located relationships: 42
- dangling relationships: 0

## bond environment (concept)

- **defines** — Gauge fixing, canonical forms, and optimal truncations in tensor networks with closed loops — `Sec. II, Eq. (1) and Fig. 1`, PDF p. 2 — The bond environment `Upsilon` is obtained by contracting the state norm network while leaving a selected bond and its conjugate open, and contracting it with the two bond matrices recovers the state norm. ([docs/papers/reading_notes/evenbly_closed_loop_truncation_1801.05390_source_review.md](reading_notes/evenbly_closed_loop_truncation_1801.05390_source_review.md))

## mixed-canonical matrix-product-state cut (concept)

- **defines** — Time-evolution methods for matrix-product states — `Secs. 2.4–2.6.1, Eqs. (11)–(15) and Figs. 4–6`, PDF p. 7 — A mixed-canonical matrix-product-state cut supplies orthonormal effective bases on both sides of the selected bond, so the bond tensor can be treated as the coefficient matrix for that bipartition. ([docs/papers/reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md](reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md))

## TDVP error decomposition (concept)

- **defines** — Time-evolution methods for matrix-product states — `Sec. 6.2.2, complete error discussion`, PDF p. 49 — The TDVP error decomposition contains finite-manifold projection error, finite time-step error, two-site SVD truncation error, and inexact local-solver error. ([docs/papers/reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md](reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md))

## TEBD time-step and truncation errors (concept)

- **defines** — Time-evolution methods for matrix-product states — `Sec. 4.1.1, first and final paragraphs`, PDF p. 18 — TEBD time-step and truncation errors are distinct: the Trotter error is controlled by step size and decomposition order, while MPS truncation is controlled by discarded weight or bond dimension and can affect unitarity and conserved quantities. ([docs/papers/reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md](reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md))

## DLM twirl (limitation)

- **limits** — Quantification and Characterization of Leakage Errors — `Sec. VI.A.3, Eq. (49) and its preceding paragraph`, PDF p. 8 — The printed DLM twirl introduces independent leakage-subspace unitaries `U_2,V_2` and sums over both, while Eq. (49) divides by only one factor of `|P_2|`. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

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

## sequential cutwise SVD local optimality (limitation)

- **limits** — Time-evolution methods for matrix-product states — `Sec. 2.6.1, final paragraph`, PDF p. 9 — Sequential cutwise SVD local optimality does not guarantee a globally optimal compressed matrix-product state when truncation errors are large. ([docs/papers/reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md](reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md))

## single-site jump-operator factorization (limitation)

- **limits** — Large-scale stochastic simulation of open quantum systems — `Sec. III.D, Eqs. (38)–(40)`, PDF p. 7 — The paper's exact dissipative contraction is a single-site jump-operator factorization whose local factors commute, do not increase MPS bond dimension, and are contracted sitewise. ([docs/papers/reading_notes/sander_tensor_jump_2501.17913_source_review.md](reading_notes/sander_tensor_jump_2501.17913_source_review.md))

## solver-induced norm error (limitation)

- **limits** — One-dimensional many-body entangled open quantum systems with tensor network methods — `Sec. III.B, paragraph immediately after Eq. (25)`, PDF p. 11 — Solver-induced norm error can contaminate the physical norm loss used for quantum-trajectory jump timing because the local Runge–Kutta method can enhance or prevent the loss caused by the effective Hamiltonian. ([docs/papers/reading_notes/jaschke_open_system_tn_1804.09796_source_review.md](reading_notes/jaschke_open_system_tn_1804.09796_source_review.md))

## full-environment truncation (method)

- **defines** — Gauge fixing, canonical forms, and optimal truncations in tensor networks with closed loops — `Sec. V, Eq. (12) and Fig. 5`, PDF p. 6 — Full-environment truncation replaces a selected bond by a lower-rank factorization and chooses its factors to maximize normalized whole-network pure-state fidelity. ([docs/papers/reading_notes/evenbly_closed_loop_truncation_1801.05390_source_review.md](reading_notes/evenbly_closed_loop_truncation_1801.05390_source_review.md))

## iPEPO density-operator evolution (method)

- **defines** — On the stability of the infinite Projected Entangled Pair Operator ansatz for driven-dissipative 2D lattices — `Appendix A.2, first three paragraphs, page 15`, PDF p. 15 — The iPEPO density-operator evolution vectorizes a PEPO into a PEPS-shaped state and replaces imaginary-time Hamiltonian gates by real-time two-body Liouvillian gates. ([docs/papers/reading_notes/kilda_ipepo_stability_2012.03095.md](reading_notes/kilda_ipepo_stability_2012.03095.md))

## quantum-trajectory jump-channel selection (method)

- **defines** — One-dimensional many-body entangled open quantum systems with tensor network methods — `Sec. III.B, steps (a)–(c) and Fig. 3`, PDF p. 12 — Quantum-trajectory jump-channel selection normalizes the expectations `p_nu = <psi|L_nu^dagger L_nu|psi>`, samples one channel, applies its Lindblad operator, and then renormalizes the state. ([docs/papers/reading_notes/jaschke_open_system_tn_1804.09796_source_review.md](reading_notes/jaschke_open_system_tn_1804.09796_source_review.md))

## tensor jump method (method)

- **defines** — Large-scale stochastic simulation of open quantum systems — `Sec. III.A, Eqs. (14)–(20) and Fig. 1`, PDF p. 5 — The tensor jump method composes dynamic TDVP, dissipative contraction, and stochastic jumping through a sampling MPS whose reordered evolution permits physical-state retrieval at requested time steps. ([docs/papers/reading_notes/sander_tensor_jump_2501.17913_source_review.md](reading_notes/sander_tensor_jump_2501.17913_source_review.md))

## terminal tensor-network sampling method (method)

- **defines** — Simulating and Sampling from Quantum Circuits with 2D Tensor Networks — `Section II, sampling definitions and procedure, page 4`, PDF p. 4 — The terminal tensor-network sampling method draws a final computational-basis bitstring x from q(x), while p(x)=|<x|psi>|^2 is the terminal distribution encoded by the final tensor-network state. ([docs/papers/reading_notes/rudolph_tindall_gpu_peps_2507.11424.md](reading_notes/rudolph_tindall_gpu_peps_2507.11424.md))

## depolarizing leakage extension (model)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. VI.A.2, Eqs. (46)--(47)`, PDF p. 8 — The depolarizing leakage extension of a computational-subspace channel is the model in Eq. (46), parameterized by leakage and seepage rates and completely depolarizing maps between the two subspaces. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## depolarizing leakage model (model)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. VI.A.3, Eq. (48)`, PDF p. 8 — The depolarizing leakage model is the DLE special case in Eq. (48) whose computational-subspace component is depolarizing. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## finite open-boundary PEPS (model)

- **defines** — Algorithms for finite projected entangled pair states — `Sec. II, PEPS definition and Fig. 1`, PDF p. 2 — The source studies a finite open-boundary PEPS on a square lattice, with one physical index per lattice site and virtual bond dimension `D`. ([docs/papers/reading_notes/lubasch_finite_peps_1405.3259_source_review.md](reading_notes/lubasch_finite_peps_1405.3259_source_review.md))

## Lindblad leakage model (model)

- **uses** — Quantification and Characterization of Leakage Errors — `Sec. VI.C, Eqs. (69)--(70)`, PDF p. 10 — A Lindblad leakage model is written as `E = exp[t(mathcal H + mathcal D)]`, where superoperator `mathcal H` acts as `mathcal H(rho) = -i[H,rho]` for Hamiltonian `H` and `mathcal D` is presented as the dissipative generator. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## locally purified tensor network (model)

- **defines** — A positive tensor network approach for simulating open quantum many-body systems — `Main text, Eq. (3) and Fig. 1(a)`, PDF p. 2 — A locally purified tensor network represents the density operator as `rho = X X^dagger`, with `X` decomposed into local tensors carrying physical, bond, and Kraus indices. ([docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md](reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md))

## quantum-trajectory effective non-Hermitian Hamiltonian (model)

- **defines** — One-dimensional many-body entangled open quantum systems with tensor network methods — `Sec. III.B, Eq. (25)`, PDF p. 11 — The quantum-trajectory effective non-Hermitian Hamiltonian is the system Hamiltonian minus one half of `i` times the sum of `L_nu^dagger L_nu`, and its norm loss is used to determine jump timing. ([docs/papers/reading_notes/jaschke_open_system_tn_1804.09796_source_review.md](reading_notes/jaschke_open_system_tn_1804.09796_source_review.md))

## simple dissipative leakage model (model)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. VI.C.1, Eq. (72)`, PDF p. 11 — The simple dissipative leakage model uses jump `A_21 = |2><1|` with rate `gamma_1` for leakage and jump `A_12 = |1><2|` with rate `gamma_2` for seepage. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## unitary leakage model (model)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. VI.B, Eqs. (57)--(58), first equality`, PDF p. 9 — The unitary leakage model starts from `H = (|1><2| + |2><1|)/2` and defines its propagator by `U(t) = exp(-i t H)`. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## bond-spectrum stationarity diagnostic (observable)

- **defines** — On the stability of the infinite Projected Entangled Pair Operator ansatz for driven-dissipative 2D lattices — `Section 2, Eq. (3) and Figure 2, page 4`, PDF p. 4 — The bond-spectrum stationarity diagnostic epsilon_Lambda is the maximum consecutive-step singular-value change divided by the timestep and the current maximum singular value. ([docs/papers/reading_notes/kilda_ipepo_stability_2012.03095.md](reading_notes/kilda_ipepo_stability_2012.03095.md))

## channel coherent leakage and seepage rates (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. V.B, Eqs. (42)--(43)`, PDF p. 7 — The channel coherent leakage and seepage rates are Haar averages of `C_L(E(|psi_j><psi_j|))` over rank-one projectors formed from all Haar-distributed pure states in subspaces `X_j`, for `j=1,2`. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## coherence of leakage (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. V.A, Eqs. (30)--(34)`, PDF p. 6 — The coherence of leakage of a state is `C_L(rho) = ||P_C(rho)||_1`, where `P_C(rho) = 1_1 rho 1_2 + 1_2 rho 1_1` is the cross-subspace block. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## direct-SVD discarded weight (observable)

- **defines** — Time-evolution methods for matrix-product states — `Sec. 2.6.1, Eq. (17) and the paragraph immediately following it`, PDF p. 9 — The direct-SVD approximation error at one canonical cut is the square root of the direct-SVD discarded weight, defined as the sum of the squared omitted singular values. ([docs/papers/reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md](reading_notes/paeckel_mps_time_evolution_1901.05824_source_review.md))

## dynamic-TDVP projection error (observable)

- **defines** — Large-scale stochastic simulation of open quantum systems — `Sec. IV.C, Eqs. (57)–(58)`, PDF p. 11 — The dynamic-TDVP projection error is the 2-norm of the component of `H_0|Phi>` outside the chosen MPS tangent space, and the one-site projector minimizes this local residual inside that space. ([docs/papers/reading_notes/sander_tensor_jump_2501.17913_source_review.md](reading_notes/sander_tensor_jump_2501.17913_source_review.md))

## leakage rate (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. II, Eq. (2)`, PDF p. 2 — For a CPTP map `E`, the leakage rate is `L_1(E) = L(E(1_1/d_1))` and the seepage rate is `L_2(E) = 1 - L(E(1_2/d_2))`, equal to Haar averages over input states in the respective subspaces. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## MCWF norm-deficit jump probability (observable)

- **defines** — Large-scale stochastic simulation of open quantum systems — `Sec. II.B, Eqs. (2)–(11)`, PDF p. 3 — The MCWF norm-deficit jump probability is `delta p = 1 - ||Psi^(i)(t+delta t)||^2`, with channel contributions `delta p_m = delta t gamma_m <Psi|L_m^dagger L_m|Psi>` normalized only after a jump is selected. ([docs/papers/reading_notes/sander_tensor_jump_2501.17913_source_review.md](reading_notes/sander_tensor_jump_2501.17913_source_review.md))

## purification discarded weight (observable)

- **defines** — A positive tensor network approach for simulating open quantum many-body systems — `Appendix D, Definition 5 and Eq. (55)`, PDF p. 10 — Purification discarded weight is the square root of the sum of squared singular values omitted when one mixed-canonical local tensor is compressed along a bond or Kraus index. ([docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md](reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md))

## sample KL divergence (observable)

- **defines** — Simulating and Sampling from Quantum Circuits with 2D Tensor Networks — `Section II, Eq. (6), page 4`, PDF p. 4 — The sample KL divergence is defined as KLD(q,p)=E under q of log(q(x)/p(x)) for the terminal bitstring distributions. ([docs/papers/reading_notes/rudolph_tindall_gpu_peps_2507.11424.md](reading_notes/rudolph_tindall_gpu_peps_2507.11424.md))

## sample probability ratio (observable)

- **defines** — Simulating and Sampling from Quantum Circuits with 2D Tensor Networks — `Section II, Eq. (5), page 4`, PDF p. 4 — The sample probability ratio p(x)/q(x) has expectation under q equal to the norm of the represented tensor-network state. ([docs/papers/reading_notes/rudolph_tindall_gpu_peps_2507.11424.md](reading_notes/rudolph_tindall_gpu_peps_2507.11424.md))

## seepage rate (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. II, Eq. (2)`, PDF p. 2 — For a CPTP map `E`, the leakage rate is `L_1(E) = L(E(1_1/d_1))` and the seepage rate is `L_2(E) = 1 - L(E(1_2/d_2))`, equal to Haar averages over input states in the respective subspaces. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## state leakage (observable)

- **defines** — Quantification and Characterization of Leakage Errors — `Sec. II, Eq. (1)`, PDF p. 2 — State leakage is the population outside computational subspace `X_1`, defined by `L(rho) = Tr[1_2 rho] = 1 - Tr[1_1 rho]` on the direct sum `X = X_1 direct-sum X_2`. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## full-bond TJM convergence theorem (theorem)

- **supports** — Large-scale stochastic simulation of open quantum systems — `Sec. IV.B, Theorem 2 and Eqs. (52)–(56); Appendix B, Theorem 7 and Eqs. (B18)–(B22)`, PDF p. 10 — The full-bond TJM convergence theorem gives an unbiased fixed-time density estimator with matrix-norm standard deviation bounded by `c/sqrt(N)` when every trajectory MPS has full bond dimension. ([docs/papers/reading_notes/sander_tensor_jump_2501.17913_source_review.md](reading_notes/sander_tensor_jump_2501.17913_source_review.md))

## locally purified trace-norm certificate (theorem)

- **supports** — A positive tensor network approach for simulating open quantum many-body systems — `Appendix D, Theorem 7 and Eqs. (59)–(60)`, PDF p. 11 — The locally purified trace-norm certificate bounds final-state error by `(tb)^3 N^2/(4m^2) + 6(2m+1)N delta` for a nearest-neighbor chain whose local Liouvillians have diamond norm at most `b`, using `m` second-order steps and a common upper bound `delta` on every discarded weight. ([docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md](reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md))

## Proposition 2 bound (theorem)

- **supports** — Quantification and Characterization of Leakage Errors — `Sec. V.B, Proposition 2`, PDF p. 7 — The Proposition 2 bound states `C_Lj(E) <= 2 sqrt(L_j(E)(1-L_j(E)))` for the channel coherent leakage and seepage quantities. ([docs/papers/reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md](reading_notes/wood_gambetta_leakage_diagnostics_pra_97_032306.md))

## purification-to-trace-norm bound (theorem)

- **supports** — A positive tensor network approach for simulating open quantum many-body systems — `Appendix A, Lemma 1 and Eqs. (20)–(25)`, PDF p. 6 — The purification-to-trace-norm bound states that normalized factorizations `rho = X X^dagger` and `sigma = Y Y^dagger` satisfy `||rho-sigma||_1 <= sqrt(2) ||X-Y||_2`, with a companion fidelity lower bound. ([docs/papers/reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md](reading_notes/werner_positive_tensor_network_open_systems_1412.5746.md))
