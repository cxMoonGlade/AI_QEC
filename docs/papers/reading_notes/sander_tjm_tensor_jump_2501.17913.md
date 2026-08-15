# Full-text review (targeted 精读) — Sander et al., "Large-scale stochastic simulation of open quantum systems" — the Tensor Jump Method (arXiv:2501.17913, Nature Communications 2025)

> **Provenance (2026-07-02): FULL-TEXT 精读.** Fetched from arXiv HTML (2501.17913v1). Nature Communications 16, 11074 (2025). DOI: 10.1038/s41467-025-66846-x. This note evaluates the TJM as a candidate MPS-based open-quantum-system solver and contrasts it with our coupling-simulator approach.

## Metadata [paper]
- Authors / affiliation: Aaron Sander, Maximilian Frohlich, Martin Eigel, Jens Eisert, Patrick Gels, Michael Hintermuller, Richard M. Milbradt, Robert Wille, Christian B. Mendl — TU Munich, WIAS Berlin, FU Berlin, Helmholtz-Zentrum Berlin, Zuse Institute Berlin.
- Venue / status: Nature Communications 16, 11074 (2025). arXiv:2501.17913 (January 2025).
- Type: Scalable stochastic algorithm for Lindbladian open quantum systems using MPS + TDVP.
- Code: Implemented in MQT-YAQS (Munich Quantum Toolkit).

## Executive summary [paper]
The Tensor Jump Method (TJM) extends the Monte Carlo Wave Function (MCWF) method to matrix product states (MPS), enabling embarrassingly parallel stochastic simulation of Markovian Lindblad dynamics at system sizes up to 1000 spins on a consumer CPU. Three components: **(1)** MCWF on MPS via Strang-split Trotterization (Hermitian evolution via TDVP, dissipative part via exact local contraction), **(2)** dynamic hybrid 1TDVP/2TDVP strategy (2TDVP allows bond growth, auto-switch to 1TDVP when cap is reached), **(3)** a "sampling MPS" that lags behind the true state by one half-step to avoid recomputation. The method converges to Lindbladian dynamics independent of system size (proved analytically and numerically), with complexity O(N n L chi_max^3 [dD + d^2]) (⚠ corrected 2026-07-06 from "chi^3 [D + d^2]"; paper Eq. (88)/(C3)).

## Method (deep) [paper]

**MCWF-on-MPS (Section III):** The core idea: each MCWF trajectory propagates a pure MPS state through non-Hermitian effective Hamiltonian evolution + quantum jumps. The Lindbladian L(rho) = -i[H, rho] + sum_m (L_m rho L_m^dag - 1/2{L_m^dag L_m, rho}) is unraveled into stochastic pure-state trajectories.

**Strang splitting (Section III.2):**
e^{-i H_D delta t/2} e^{-i H_0 delta t} e^{-i H_D delta t/2}
where H_0 = H_eff (Hermitian part) and H_D is the dissipative part. Half-steps at boundaries are merged across time steps. Error: O(delta t^3) for the full step.

**Dynamic TDVP (Section III.3):**
- **1TDVP:** Site-by-site forward/backward sweep. Forward: d/dt M_l(t) = -i H^eff_l M_l(t) with Lanczos exponentiation and QR for orthogonality center shift. Backward: d/dt C_l(t) = +i H~^eff_l C_l(t) (positive sign from reversed time direction).
- **2TDVP:** Two-site merging via SVD with threshold s_max, allowing bond dimension growth.
- **Hybrid:** Start with 2TDVP, allow bond growth until chi_max is reached, then switch to 1TDVP (bond dimension capped). This is explicitly a truncation-error vs. bond-dimension tradeoff.

**Dissipative contraction (Section III.4):** Exact and local: D[delta t] = ⊗_{l=1}^L D_l[delta t] where each D_l is a d x d matrix exponential of local jump operators. This "does not increase the bond dimension when applied to an MPS." The factorization relies on jump operators being single-site (local).

**Sampling MPS (Section III.6.2):** A separate MPS |Phi> that lags behind the true state |Psi> by one final half-step. At any time step j, applying the final half-step subfunction F_n to |Phi(j delta t)> retrieves |Psi(j delta t)>. This avoids recomputing the final half-step after each jump decision.

**Monte Carlo convergence (Section IV.2):** Density matrix constructed as MPO by averaging:
rho(t) = (1/N_traj) sum_i |Psi_i(t)><Psi_i(t)|
or expectation values independently averaged:
<O(t)> = (1/N_traj) sum_i <Psi_i(t)| O |Psi_i(t)>
Frobenius variance (Appendix B) follows standard MCWF scaling.

## The noise model [paper -> ours]
The TJM targets **Markovian Lindblad dynamics with single-site jump operators and nearest-neighbor Hamiltonians**. This is structurally different from our coupling simulator in several key ways:

1. **Local vs. non-local jump operators:** TJM assumes L_m = I ⊗ ... ⊗ L_local ⊗ ... ⊗ I (single-site). Our shared-bath pseudomode couples to a collective operator (sum_i sigma_i^z or similar) — a **global multi-site jump operator**. The TJM's locality assumption is violated by our model, which is the entire reason we need TDVP/W^II instead of TEBD.

2. **Discrete jumps vs. continuous Lindblad:** TJM uses the MCWF unraveling (discrete quantum jumps at random times). Our approach computes the deterministic Lindblad evolution directly (via vectorized rho MPS). TJM's stochastic sampling may be more efficient for large systems with weak dissipation; our deterministic approach may be better for strong dissipation or when precise channel reconstruction is needed.

3. **Markovian only:** TJM assumes a Lindblad master equation with time-independent generators. It does not handle non-Markovian bath memory, which is central to our approach (pseudomodes + collective coupling).

4. **Nearest-neighbor Hamiltonian:** The XXX Heisenberg test model has NN-only interactions. Our surface-code Hamiltonian + pseudomode coupling has long-range interactions in the vectorized Lindbladian.

## TJM vs. our W^II/TDVP choice [ours -> paper]
The TJM's dynamic hybrid 1TDVP/2TDVP for Hermitian evolution is complementary to our chosen W^II method for non-Hermitian Lindbladian evolution:

| Aspect | TJM (this paper) | Our approach (W^II) |
|---|---|---|
| Evolution operator | Hermitian (H_eff separate from dissipation) | Non-Hermitian Lindbladian directly |
| Method for unitary part | TDVP (1-site and 2-site hybrid) | N/A (we evolve the full Lindbladian) |
| Dissipation handling | MCWF jumps (stochastic) | Deterministic via vectorized Liouvillian MPO |
| Locality assumption | Single-site jump operators | Can handle long-range via W^II |
| Non-Markovian | No | Yes (pseudomodes) |
| Error control | Projection error (TDVP) + Monte Carlo sampling | Truncation error (MPO bond dimension) + time-step |

The TJM demonstrates that MPS-based Lindblad simulation up to 1000 sites is practical. However, its assumptions (local jumps, Markovian, nearest-neighbor Hamiltonian) bound its relevance to our specific problem. We would need to generalize it for collective jump operators.

## Bond dimension scaling [paper]
- User-specified chi_max = maximum bond dimension. ⚠ corrected 2026-07-06: the paper's own runs use SMALL chi — chi in {2,4,8} at 30 sites (Fig. 5), chi = 4 for the L=100 steady-state run (Sec. VI B) AND for the 1000-site run (Sec. VI C, Fig. 7 caption); the earlier "20-100 typical" was not from the paper.
- 2TDVP allows growth until threshold; 1TDVP caps it.
- Dissipative contraction does not increase bond dimension.
- The paper claims complexity O(N n L chi_max^3 [dD + d^2]) (⚠ corrected 2026-07-06; Eq. (88)/(C3)) independent of system size for fixed chi.
- The "independent of system size" claim is demonstrated numerically but likely depends on locality structures.

## Findings + numbers [paper]
| Quantity | Value | Source |
|---|---|---|
| Max system size | 1000 spins (XXX Heisenberg) | Section VI.3 |
| Runtime (1000 spins) | ~7.5 hours on consumer CPU | Section VI.3 |
| Comparison method (30 sites) | MPDO Lindbladian (full density matrix MPO) | Section VI.1 |
| Bond dimension cap (100 sites) | chi_max = 20-100 (typical) | Section VI.2 |
| Time-step error | O(delta t^3) (Strang splitting) | Section III.2 |
| Trajectory independence | Embarassingly parallel | Section III.1 |
| MCWF-Lindblad equivalence | Proved (Appendix A) | Appendix A |
| Convergence vs. system size | Independent (proved + numerical) | Abstract, Section IV |

## Limitations [paper]
- **Markovian only:** No non-Markovian dynamics. The Lindblad equation assumes the Born-Markov approximation.
- **Local jump operators only:** Cannot handle collective/delocalized dissipation (shared bath, spatially correlated noise) without reformulation.
- **No QEC context:** No discussion of stabilizer circuits, syndrome measurements, or decoders.
- **No gauge/identifiability:** The forward-simulation perspective assumes all Lindblad parameters are known; no estimation or identifiability analysis.
- **Nearest-neighbor Hamiltonian:** The benchmark is XXX Heisenberg (NN). Performance with long-range Hamiltonians (relevant for our surface-code + pseudomode model) is untested.
- **Discrete jumps only:** Does not handle continuous Gaussian noise (quantum state diffusion), which may be more efficient for some problems.

## Relevance to AI_QEC [ours]
**Medium-high relevance** as a complementary MPS solver, but with important structural mismatches:

1. **MPS carrier validation:** The TJM provides an independent benchmark for our MPS-based Lindblad solver. If we implement a similar 1TDVP/2TDVP approach for the unitary part of our evolution, the TJM's numerical results (30-site MPDO comparison, 100/1000-site scaling) serve as validation targets.

2. **Stochastic vs. deterministic tradeoff:** TJM's MCWF approach may be more memory-efficient than our vectorized-rho MPO approach for large systems (pure MPS vs. MPO), at the cost of Monte Carlo sampling noise. This tradeoff should be evaluated for our target regimes.

3. **Dynamic TDVP strategy:** The hybrid 1TDVP/2TDVP strategy (let bond grow until chi_max, then cap) is directly applicable to our evolving MPC/TDVP approach, regardless of whether we use W^II or TDVP for the Lindbladian.

4. **Gap to our model:** The paper's local-only assumption means we cannot directly apply TJM to our shared-bath collective-coupling model. Bridging this gap — extending TJM to handle collective jump operators — would be a nontrivial extension.

5. **Software implementation:** TJM is implemented in MQT-YAQS (C++/Python), not quimb. If we need a production MPS Lindblad solver for simple (local, Markovian) Lindbladians, TJM/MQT-YAQS may be usable off-the-shelf. For our specific model (non-Markovian, collective coupling), implementation in quimb is the right choice.

## How to use / trust + open questions [ours]
Trust level: **high** for Markovian Lindblad simulation with local jump operators and nearest-neighbor Hamiltonians. The derivations are sound, the numerical benchmarks are thorough (comparison to MPDO, scaling tests), and the Nature Communications venue provides peer review.

**Open questions for our project:**
- Can the TJM's MCWF-on-MPS framework be extended to handle collective jump operators (sum_i L_i)? This would require reformulating the dissipative contraction which currently relies on single-site factorization.
- How does the runtime compare to our deterministic MPO-W^II approach for (a) local-only Lindbladians and (b) collective-coupling Lindbladians? This is an empirical question.
- The TJM's MPS-based approach vs. our vectorized-rho MPO approach: which has better bond-dimension scaling for our target (pseudomode-enlarged system, 1-2 pseudomodes per qubit)?
- Can we combine TJM's dynamic TDVP strategy with our W^II Lindbladian evolution for better error control?

---

# UPDATE (2026-07-06): targeted full-PDF 精读 — TJM as a candidate PARALLEL trajectory backend for the qutrit-leakage MCWF-on-MPS carrier

> **Provenance:** PDF (arXiv:2501.17913v2, 22 Jul 2025; Nature Communications version) now cached at
> `docs/papers/sander_tjm_tensor_jump_2501.17913.pdf`; pdftotext extraction at
> `outputs/papers/2501.17913.txt` (main text + Methods VIII A–F + Appendices A–C, all read).
> This section EXTENDS the 2026-07-02 note above (written from the coupling-simulator / W^II angle);
> it does not replace it. Two quantitative corrections to the 2026-07-02 tables were applied in place
> (flagged ⚠ above). Adjudication question [ours]: should a TJM trajectory backend sit NEXT TO
> `src/qec_twin/forward/scalable/mps_forward.py` (the d3+ qutrit-leakage QEC record generator)?

## 1. What the TJM computes, precisely [paper]

Object: the Markovian Lindblad master equation, Eq. (1), with a fixed Hermitian system Hamiltonian
`H0` (stored as an MPO) and a set of **single-site** jump operators. The required inputs are listed
in Sec. III F 1: "1. |Ψ(0)⟩: Initial quantum state vector, represented as an MPS. 2. H0: Hermitian
system Hamiltonian, represented as an MPO. 3. {Lm}, {γm}: A set of single-site jump operators stored
as matrices with their respective coupling factors. 4. δt: Time step size. 5. T: Total evolution
time. 6. χmax: Maximum allowed bond dimension. 7. N: Number of trajectories."

Unraveling scheme: quantum-jump (MCWF) unraveling; each trajectory is a **pure MPS**. Per Sec. III A:
"The stochastic time-evolution of one trajectory in the TJM consists of three main elements: 1. A
dynamic TDVP U[δt]. 2. A dissipative contraction D[δt]. 3. A stochastic jump process Jϵ[δt]."
One trajectory is the operator product U(T) = Π F_{n−i}[δt] (Eq. (14)) with subfunctions (Eq. (15))

    F_j[δt] = Jϵ[δt] D[δt/2] U[δt]   (j = n)
    F_j[δt] = Jϵ[δt] D[δt]   U[δt]   (0 < j < n)
    F_j[δt] = Jϵ[δt] D[δt/2]         (j = 0)

**dt/Trotter structure** (Sec. III B): Strang (second-order) splitting of the non-Hermitian
effective Hamiltonian H = H0 + HD, HD = −(i/2) Σ_m γm Lm†Lm (Eq. (3)):
"U(i)(δt) = e^{−iHD δt/2} e^{−iH0 δt} e^{−iHD δt/2} + O(δt³)" (Eq. (23)), and "we have combined
neighboring half time steps of dissipative operations, which is valid since HD commutes with itself
for any choice of jump operators."

**Unitary part** U[δt] = e^{−iH0 δt} via **dynamic TDVP** (Sec. III C): "during each sweep, we
locally use 2TDVP if the bond dimension has room to grow, otherwise we use 1TDVP at the site" —
2TDVP grows bonds by SVD (threshold s_max) until χmax, then 1TDVP confines evolution to the current
manifold. Local effective Hamiltonians are exponentiated with Lanczos; a sweep = two half-sweeps of
δt/2 each.

**Dissipative sweep** D[δt] = e^{−iHD δt} (Sec. III D): "we focus on single-site jump operators";
the exponential "can be factorized into purely local operations due to the commutativity of the sums
of single site operators… the dissipation term is equivalent to a single contraction of the
dissipative operator D[δt] into the current MPS |Φ(t)⟩. Additionally, this does not increase the
bond dimension when applied to an MPS and the dissipative contraction is exact without inducing
errors." Explicitly D[δt] = ⊗_ℓ Dℓ[δt] with Dℓ = e^{−(δt/2) Σ_{j∈S(ℓ)} γj Lj[ℓ]† Lj[ℓ]} ∈ C^{d×d}
(Eq. (40)). [ours] Note the single-site restriction is LOAD-BEARING for this factorization.

**Where jumps enter** (Sec. III E): after each F(i)_j. δp is the exact norm loss of the MPS —
"In contrast to the MCWF, we do not use a first-order approximation of e^{−iHδt} to calculate δp(t)
since the time-evolution has been carried out by the TDVP projectors and the dissipative
contraction." (Eq. (42): one final-tensor contraction in mixed canonical form.) If ϵ ≥ δp:
normalize, no jump. If ϵ < δp: jump probabilities Πm computed in a half-sweep with local
contractions per site in mixed canonical form (Eqs. (43)–(45)); the selected single-site Lm is
contracted into its site tensor; "The state is then normalized through successive SVDs before moving
onto the next time step. This allows the state to naturally compress as the application of jumps
often suppress entanglement growth in the system. Note that this is a fundamental departure from the
MCWF in which the jump is applied to the state at the previous time t." (TJM applies the jump to the
POST-evolved state |Φ(i)(t+δt)⟩.)

**No measurements anywhere** [paper, checked full text]: the framework contains no projective
measurement, no POVM, no measurement record, no feedback/conditioning; the only stochastic element
is the environment-jump unraveling. "Measurement" enters only as expectation values of observables
⟨O(t)⟩ averaged over trajectories (Eq. (20)). Non-Markovian dynamics is explicitly future work
(Sec. I: "can be further built on through new unravelling and splitting techniques [48–50] and the
addition of non-Markovian processes [51]").

## 2. Sampling structure: what is shared across trajectories [paper]

- **Across trajectories: NOTHING is shared.** "This results in an embarassingly parallel process
  since each trajectory is independent and may be discarded after calculating the relevant
  expectation value." (Sec. III A, after Eq. (20)). Implementation: "using a parallelization scheme
  in which each TJM trajectory runs on a separate thread" (Sec. V, consumer i5-13600KF, 14 cores).
  [ours] The TJM offers NO cross-trajectory batching/amortization of tensor ops — its answer to
  throughput is thread-level trajectory parallelism, exactly like plain MCWF.
- **Within a trajectory, across time steps:** the **sampling MPS** |Φ⟩. The Strang reordering makes
  "the unitary evolution … lag behind the dissipative evolution by a half-time step, which is only
  corrected when the final operator Fn[δt] is applied" (Sec. III A). Φ(0) = F0|Ψ(0)⟩ (Eq. (16)),
  Φ((j+1)δt) = Fj|Φ(jδt)⟩ (Eq. (17)), and the physical state at ANY intermediate step is retrieved
  as |Ψ(jδt)⟩ = Fn[δt]|Φ(jδt)⟩ (Eq. (18)): "This allows us to sample at the desired time steps
  without compromising the reduction in time step error from applying the operators in this order."
  [ours] i.e. the sampling MPS shares the merged half-step structure across TIME, so mid-run
  observable reads cost one extra Fn on a copy instead of breaking the half-step merge. It is a
  read-only device — the retrieved |Ψ(jδt)⟩ is inspected, not fed back.
- **Within a sweep:** "we compute the effective Hamiltonians using left and right environments which
  are updated and reused throughout the evolution" (Sec. III C 2).
- A noise-free reference (γ=0) needs "only a single 'trajectory'" (Fig. 7 caption).

## 3. Claimed gains + the paper's own numbers [paper]

Complexity (Table I; Eq. (88)/(C3); d = local dim, L sites, n steps, N trajectories, D Hamiltonian-MPO bond):

| Method | Time evolution | Storage | Exp. value |
|---|---|---|---|
| Lindblad (dense superop) | O(n d^{6L}) | O(d^{2L}) | O(d^{6L}) |
| MCWF (dense SV) | O(N n d^{3L}) | O(N d^L) | O(N d^{4L}) |
| MPO Lindblad | O(n L d^4 D_H² D_s²) | O(L d² D_s²) | O(L d² D_s³) |
| **TJM** | **O(N n L χmax³ [dD + d²])** | **O(N L d χmax²)** | **O(N L d D χmax³)** |

- vs dense MCWF: TJM is more compact iff "χmax < sqrt(d^L/(Ld))" (Eq. (89)) — always true at scale.
- vs MPO Lindbladian (Sec. VI A, 30-site XXX, LindbladMPO package, D = 400 reference): "While the
  MPO simulation required over 24 hours to complete, each TJM simulation (with N = 100) ran in under
  5 minutes." — with χ ∈ {2,4,8} and N = 100 only. "We also note that the TJM is positive
  semi-definite by construction … while the MPO solver does not guarantee this."
- Scale demonstrations: L = 100 edge-driven XXX to the exact steady state (Δ < 10⁻² by Jt ≈ 90000;
  δt = 0.1, N = 100, χ = 4, Sec. VI B); L = 1000 noisy XXX "took roughly 7.5 hours" on the consumer
  CPU (γ = 0.1, χ = 4, N = 100, δt = 0.5, Sec. VI C).
- vs prior trajectory-MPS work (Sec. I): "existing trajectory-based methods often suffer from
  practical numerical instabilities, particularly when using TDVP to evolve under a non-Hermitian
  effective Hamiltonian"; the TJM "avoids instabilities that arise when applying TDVP to a
  non-Hermitian generator, maintains robustness across time steps, and swaps truncation error for
  projection error."

[ours] IMPORTANT altitude check: Table I's "MCWF" row is DENSE-state-vector MCWF. The paper's gain
claims are vs (a) dense MCWF, (b) MPO/density-matrix solvers, (c) prior UNSTABLE trajectory-MPS
schemes that ran TDVP on the non-Hermitian H directly. It claims NO advantage over an MCWF-on-MPS
scheme that (like ours) has no continuous Hamiltonian to integrate — all three TJM innovations
(dynamic TDVP, Strang + sampling MPS, dissipative sweep) target the continuous-H0 component.

## 4. Error scaling in δt and bond dimension [paper]

Sec. IV C, verbatim: "The major error sources of the TJM are as follows: 1. the time step error of
the Strang splitting (O(δt³)) [63], 2. the time step error of the dynamic TDVP (O(δt³) per time step
and O(δt²) for the whole time-evolution), and 3. the projection error of the dynamic TDVP." Also:
"for 2TDVP the projection error is exactly zero if we consider Hamiltonians with only nearest
neighbor interactions"; "The errors in the dissipative contraction and in the jump application are
both zero."

Empirics (Sec. V, 10-site TFIM vs QuTiP exact): first-order Trotter baselines plateau ("all step
sizes induce a plateau, indicating that Trotter errors dominate when N becomes large") while the
"second-order TJM approach (solid lines) maintains ∼ C/√N scaling for both δt = 0.1 and δt = 0.2"
with C ≈ 0.1, up to N = 10⁴. Bond dimension (Sec. V B): "the number of trajectories plays a larger
role in the error scaling than the bond dimension, however, a higher bond dimension is required for
capturing certain parts of the dynamics"; χ = 8 vs χ = 16 nearly indistinguishable on their model.
[ours] There is NO a-priori bond-dimension error theorem — χ is a hyperparameter; the 1TDVP
projection error is only computable a posteriori (Eq. (57)); both convergence theorems assume
"MPS format of full bond dimension".

## 5. Exactness / convergence statements proved [paper]

- **Theorem 3 (Appendix A, MCWF ↔ Lindblad):** with H = H0 − (i/2)Σ γm Lm†Lm, "If the time step δt
  converges to 0, it holds that ρ(t) = lim_{N→∞} µ̄N(t) ∀t." The proof drops O(δt²) terms of
  U(δt) = 1 − iHδt + O(δt²) — i.e. the unraveling itself is proved equivalent to the master equation
  only in the DOUBLE limit δt → 0, N → ∞; at finite δt the per-step unraveling bias is the O(δt²)
  remainder (kept below MC noise empirically by the second-order splitting, Fig. 4a).
- **Theorem 2/7 (Monte Carlo convergence):** for trajectories "in MPS format of full bond
  dimension", E[ρN(t)] = ρ(t) and "there exists a c > 0 such that the standard deviation of ρN(t)
  can be upper bounded by σ(ρN(t)) ≤ c/√N for all matrix norms"; explicitly in Frobenius norm
  "σF[ρN(t)] = (1/√N) σF[|Ψ1(t)⟩⟨Ψ1(t)|] ≤ 2/√N" (Eq. (56)) — "independent of system size".
- Positivity: ρN is positive semi-definite by construction (sum of pure-state projectors;
  Theorem 7 proof).

## 6. Released code [paper]

"An open-source implementation of this work can be found in the MQT-YAQS package available at [52]
as part of the Munich Quantum Toolkit" — ref [52]: A. Sander, "Yaqs: Yet another quantum simulator",
github.com/munich-quantum-toolkit/yaqs. (Python; the paper's runs are CPU, one trajectory per
thread.)

## 7. Mapping onto OUR carrier (`mps_forward.py`) [ours]

Our carrier per trajectory: qutrit MPS (phys dim 3, quimb/torch cuda complex128), per-round
within-cycle stream = 1-site frame gates (H/X/Y) + per-CZ-layer exp(L/4) Wood-Gambetta leakage Kraus
slices (coherent |1⟩–|2⟩ exchange θ + jump g_seep/g_heat), then 8 PROJECTIVE stabilizer parity
Born-measurements (weight ≤ 4 sqrt(E_s) POVM Kraus — the ONLY bond-growing op, truncated at
max_bond=χ with a discarded-weight ledger), then a transversal Y frame; terminal biased/leaked
readout POVM. Trajectories run serially per shot; the measured d5 bottleneck is quimb gate_nonlocal
per-op overhead + the serial per-shot loop (see module docstring + `_with_gesvd_svd` note).

**(a) Mid-evolution PROJECTIVE measurements / feedback: NOT handled.** The TJM has no projective
measurement, no record, no conditioning (Sec. 1 above). Its stochastic operator Jϵ is an
environment-jump, not a syndrome extraction; the sampling-MPS device is read-only (retrieves
|Ψ(jδt)⟩ for expectation values) and its half-step-merge bookkeeping is broken by any operation that
must COLLAPSE the state mid-stream and feed the outcome forward, which is exactly what our
per-round stabilizer measurements do. Our measurement layer would have to be kept from OUR carrier
unchanged; the TJM contributes nothing to it. Additionally our sqrt(E_s) operators are weight-≤4
multi-site Kraus — outside the TJM's single-site operator class, whose locality is load-bearing for
the dissipative factorization (Eq. (40)).

**(b) Kraus channels vs continuous Lindblad:** the TJM is formulated ONLY for continuous
time-independent Lindblad dynamics; it never composes finite Kraus channels. Our WG leak slice IS
generated by a Lindbladian, so the between-measurement leak stream COULD be recast in TJM form:
the θ-exchange term goes to H0 (then purely single-site → TDVP degenerates to exact 1-site local
exponentials, no bond growth, no projection error, and the Strang splitting + sampling MPS become
pointless machinery), the seep/heat jumps go to {Lm} with D[δt] = our no-jump factor. But this is
just a DIFFERENT unraveling of the SAME single-site slice channel: our `leak_slice_kraus_torch`
already resolves exp(L·Δ) EXACTLY at finite slice width (ensemble mean = the slice channel, an
identity, no δt → 0 limit needed), whereas the TJM's jump unraveling is proved equivalent only as
δt → 0 (Theorem 3) with at most one jump per site per step. A TJM leak backend is therefore
strictly a convergence-in-δt approximation of what the carrier already does exactly, at the same
O(d²χ²) per-site cost class. No accuracy or complexity gain exists in our regime.

**(c) Local dimension 3:** fine. The formalism is generic in d (all complexities carry d; jump
operators are arbitrary d×d single-site matrices), though every benchmark in the paper is d = 2.

**What maps directly:** the convergence/equivalence theorems (Sec. 5) — they hold for any valid
unraveling averaged as (1/N)Σ|Ψi⟩⟨Ψi|, including ours; σF ≤ 2/√N is a citable, size-independent
N-budget for record/observable-level certification. The post-jump "normalize through successive
SVDs … naturally compress" trick is a minor implementable idea (post-Kraus recompression).
**What needs adaptation:** nothing worth adapting today — dynamic 2TDVP/1TDVP and the sampling MPS
only pay off once a genuinely CONTINUOUS multi-site H0 exists between measurement layers (e.g. an
always-on coupler/crosstalk Hamiltonian or coupled-pseudomode bath). That is the trigger condition
for revisiting TJM/MQT-YAQS as a between-measurement segment engine.
**What does not apply:** the entire measurement/record layer (a); cross-trajectory batching (the TJM
has none — Sec. 2 — so it does NOT address our serial-per-shot bottleneck); any a-priori bond-error
guarantee (none exists, Sec. 4); non-Markovian memory (explicit future work).

## 8. Equivalence-gate design for a hypothetical TJM backend [ours]

If a TJM-style leak backend were built next to `mps_forward.py`, the gate must be:
1. **Channel-level CONVERGENCE gate (not an identity gate):** per within-cycle segment, the TJM-step
   ensemble map must converge to the exact WG slice channel exp(L·Δ) as δt → 0, with the declared
   rates (Strang O(δt³)/step; unraveling bias vanishing with δt per Theorem 3). Finite-δt equality
   with our carrier is NOT expected and must not be asserted.
2. **Record-level gate at full χ:** syndrome+flip record statistics of TJM-backend vs our
   MCWF-on-MPS vs the exact DM oracle agree within the MC budget σF ≤ 2/√N (Theorem 2/7; both
   theorems assume full bond dimension — exactly our C8 zero-truncation anchor regime).
3. **Bond leg:** import NO bond-error claim from the paper; keep our per-cut discarded-weight ledger
   (`MpsTruncationLedger`) as the only χ accounting; TJM's a-posteriori projection error (Eq. (57))
   is the analogue on its side.

## Verdict [ours]

**Do NOT build a parallel TJM backend for the d3+ qutrit-leakage record generator now.** The TJM is
a continuous-Lindblad trajectory engine whose three innovations all target the continuous
multi-site-Hamiltonian component our teacher does not have; it cannot express our projective
per-round measurement layer (its single-site operator class and measurement-free framework exclude
it); on the leak stream it reduces to an O(δt)-biased re-unraveling of a slice channel we already
sample exactly; and it shares no tensor ops across trajectories, so it does not touch our actual
bottleneck (serial per-shot loop + per-op overhead). KEEP: the σF ≤ 2/√N size-independent MC bound
as a certification budget; the trigger condition (a real continuous multi-site H0 between rounds)
under which TJM/MQT-YAQS becomes the right reference engine to benchmark against.

## Tags (update)
- `[paper]` TJM = MCWF-on-MPS with Strang splitting (O(δt³)), dynamic 2TDVP/1TDVP for e^{−iH0δt}, exact ⊗-factorized dissipative sweep, jump applied to the POST-evolved state
- `[paper]` sampling MPS = within-trajectory, across-time sharing; trajectories embarrassingly parallel, nothing shared across them
- `[paper]` Theorem 3: unraveling ≡ Lindblad only in δt→0, N→∞; Theorem 2/7: σ(ρN) ≤ c/√N size-independent at full bond dimension
- `[paper]` single-site jump operators are load-bearing (dissipative factorization Eq. (40)); no projective measurement / record / feedback anywhere
- `[ours]` all three TJM innovations target the continuous-H0 component absent from our within-cycle teacher; measurement layer (weight-≤4 sqrt(E_s)) is outside its operator class
- `[ours]` verdict: no parallel TJM backend now; adopt the √N budget; trigger = continuous multi-site H0 between rounds
- `[gap]` no a-priori bond-dimension error bound; no mid-circuit measurement; non-Markovian explicitly future work
