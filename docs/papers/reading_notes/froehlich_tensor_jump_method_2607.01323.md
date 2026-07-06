# Full-text review — Frohlich et al., "Noisy quantum circuit simulation with the tensor jump method" (arXiv:2607.01323)

> **Provenance (2026-07-03): FULL-TEXT 精读.** Fetched from arXiv HTML (2607.01323v1). Fresh submission (July 2026). The paper presents a variance-aware tensor-network MCWF framework that unifies the tensor jump method with local TDVP gate evolution on MPS plus a sparse Pauli-Lindblad noise model, supporting correlated multi-qubit Lindblad noise.
>
> **Provenance update (2026-07-06): second full-text pass (PDF, 18 pp) for the TJM-backend decision.** PDF now cached at `docs/papers/froehlich_tensor_jump_method_2607.01323.pdf` (arXiv v1, dated June 29 2026), verified via `pdftotext`. This pass verified the 2026-07-03 note against the full text and extends it where it was thin for the question "add a parallel TJM trajectory backend next to our MCWF-on-MPS qutrit-leakage carrier?": (a) exact trajectory/jump bookkeeping, (b) cost model vs plain MCWF/Kraus-insertion, (c) mid-circuit measurement handling, (d) relation to Sander 2501.17913. All 2026-07-03 content checked out against the PDF (equations, Theorem 1, benchmark numbers); the new sections below are additive.

## Metadata [paper]
- **Authors / affiliation:** Maximilian Frohlich, Aaron Sander, Martin Eigel, Robert Wille, Michael Hintermuller — TU Munich (Wille: Chair of Quantum Algorithms and Software, MQT), Weierstrass Institute Berlin (Eigel, Hintermuller), BMW Group (Sander).
- **Venue / status:** arXiv:2607.01323 (quant-ph, July 2026). Part of the Munich Quantum Toolkit (MQT-YAQS). No journal reference yet; submitted two days ago.
- **Type:** Methodological — variance-reduced quantum trajectory method for noisy circuit simulation with tensor-network (MPS) compression + sparse Pauli-Lindblad noise model (SPLM).

## Executive summary [paper]

The paper presents the **circuit Tensor Jump Method (cTJM)**, a hybrid framework combining:
1. **Local TDVP** for unitary gate application on the MPS manifold (eliminates SWAP overhead for non-nearest-neighbor gates)
2. **Monte Carlo wavefunction (MCWF) trajectory sampling** with tensor-network state compression
3. **Sparse Pauli-Lindblad model (SPLM)** of hardware noise, where Pauli jump operators yield state-independent hazards and a dissipative contraction that reduces to a global scalar

Two complementary variance-aware unravelings are introduced: **analog unitary-mixture sampling** (effective at weak noise) and **projector-jump sampling** (effective at moderate-to-strong noise, produces closed-form variance laws on absorbing circuit windows). The method supports arbitrary correlated multi-qubit Lindblad noise consistent with hardware connectivity, including long-range noise operators on non-adjacent subsets via an exact bond-2 MPO independent of separation.

Demonstrated numerically on: (a) a two-qubit SPLM variance check against analytic predictions, (b) a 25-qubit noisy XY quench with X_ell X_{ell+1} flip noise, and (c) IBM's 127-qubit kicked-Ising benchmark (Eagle heavy-hex) with two-qubit depolarizing noise at three strengths and three dynamical regimes (identity-equivalent, Clifford, non-Clifford).

## Method (deep) [paper]

**Local TDVP gate application (Section II.1):** Each multi-qubit gate U = e^{-iHt} is interpreted as the exponential of a local Hamiltonian and integrated via the Schrodinger equation projected onto the MPS manifold. Naturally handles gates between non-neighboring qubits without explicit SWAP operations. Bond dimension dynamically adjusted during evolution.

**Tensor Jump Method (Section II.2):** Standard MCWF with Strang splitting for the effective non-Hermitian Hamiltonian:

> H_eff = H - (i/2) Sigma_m gamma_m L_m^dagger L_m
>
> e^{-i H_eff delta t} = D[delta t/2] * U[delta t] * D[delta t/2] + O(delta t^3)

where D is the dissipative contraction and U the coherent evolution. Unnormalized no-jump update: |psi~> = D[delta t/2] U[delta t] D[delta t/2] |psi>. Total jump probability delta p = 1 - ||psi~||^2.

**Sparse Pauli-Lindblad model (Section II.3):** L(ρ) = Sigma_m gamma_m (P_m ρ P_m^dagger - ρ) with Pauli strings P_m in {I,X,Y,Z}^⊗n. Because P_m P_m^dagger = I, the jump probability δp_m = δt gamma_m is **state-independent**, and the dissipative contraction reduces to a global scalar e^{-½ δt Γ_tot} I that cancels upon renormalization.

**Circuit TJM (Algorithm 1):** For each gate g: (1) determine gate support and local jump set S_g = {m: supp(L_m) ∩ Q_g ≠ ∅}; (2) apply local TDVP gate; (3) local dissipative contraction D_g with m ∈ S_g only; (4) local jump sampling with L_g only. Only one jump per 2-qubit gate per trajectory. Error sources: MC variance, TDVP projection/integration error O(delta t^3), MPS SVD truncation.

**Analog unitary-mixture unraveling (Section IV.1):** Replace the Lindblad jump γ(PρP - ρ) with a continuous family of unitary kicks L_θ = sqrt(λ w(θ)) e^{iθP} with λ s = γ for generator matching (s = E_w[sin²θ]). Two variants: two-point law (θ = ±θ₀) and Gaussian law (θ ~ N(0, σ²)), with s = sin²θ₀ or s = ½(1 - e^{-2σ²}) respectively. The analog dissipative contraction gives global scalar exp(-(Γ_tot/(2s))δt).

**Projector-jump unraveling (Section IV.2):** Collapse operators L_± = sqrt(γ/2)(I ± P) = sqrt(2γ) Π_±. Theorem 1: for an observable O anticommuting with all active Pauli channels (no commuting channels, no Hamiltonian), the trajectory expectation X_t = ⟨O⟩_t is Bernoulli with P[X_t = 1] = e^{-2Γ_anti t}, giving Var_proj = e^{-2Γ_anti t}(1 - e^{-2Γ_anti t}) — an exact closed form. Absorbing property: after an anticommuting jump, ⟨O⟩ becomes 0 permanently.

**Long-range noise MPO (Section IV.3):** For a Pauli string P = σ_i ⊗ τ_j on non-adjacent sites i < j, each collapse operator L = a·I + b·P admits an exact bond-2 MPO independent of separation j-i. For projectors: L_± = sqrt(γ/2)(I ± P) ⇒ (a,b) = (1, ±1). For analog: L_θ = sqrt(λ w(θ)) (cos θ I + i sin θ P) ⇒ (a,b) = (cos θ, i sin θ). The bond-2 construction uses site-specific tensors: I on all sites before i; [I, σ] at i; [[I,0],[0,I]] on interior sites; [a·I; b·τ] at j; I after j.

## Results (deep) [paper]

**Two-qubit SPLM variance check (Figure 1):** X⊗I, I⊗X, X⊗X noise at equal rates, initial |00⟩, record ⟨Z_i⟩ per trajectory. All unravelings reproduce the analytic mean ⟨Z_i⟩_t = e^{-4γt} confirming generator matching. Projector variance follows the Bernoulli closed form e^{-4γt}(1 - e^{-4γt}) and decays rapidly. Standard unraveling variance approaches 1 - e^{-8γt} (unit-variance plateau). Both analog schemes plateau at 1/4 (analytic stationary variance). N_traj = 2000.

**Noisy XY chain, 25 qubits (Figure 2):** 20 Trotter steps, δt = 0.1, initial |0001 0001 ...⟩ pattern, X_ℓ X_{ℓ+1} flip noise (homogeneous SPLM on bonds). Five methods compared (Qiskit Aer MPS + four cTJM variants), N_traj = 200, χ_max = 128. Three noise regimes:

- γ = 10⁻³: Dynamics near coherent XY transport; all methods small variance; projector smallest; analog reduces variance relative to standard.
- γ = 10⁻²: Projector strongest variance reduction and **visibly slower bond dimension growth**, staying below χ_max = 128 up to depth 20; other methods saturate near χ_max around step 14.
- γ = 10⁻¹: Projector rapidly suppresses trajectory spread (absorbing-window behavior); projector trajectories remain extremely low-entangled (χ ~ O(1)), while standard and analog generate substantially larger bond dimensions.

Regime separation confirmed: analog beneficial at weak noise, projector advantageous at moderate-to-strong noise for both variance reduction and bond-dimension suppression.

**127-qubit IBM kicked Ising (Figure 3):** Eagle heavy-hex topology, two-qubit depolarizing after each entangling gate, γ ∈ {10⁻³, 10⁻², 10⁻¹}, θ_h ∈ {0, π/8, π/2}. N_traj = 100, χ_max = 128.

- θ_h = 0 (identity-equivalent): baseline isolating pure noise effects
- θ_h = π/2 (Clifford): nontrivial entangling
- θ_h = π/8 (non-Clifford): stabilizer methods inapplicable

Projector and standard means agree closely (unbiased). Projector variance stays uniformly bounded (peaking ~0.4) for θ_h ∈ {0, π/8}, while standard variance shows substantially larger fluctuations. For θ_h = π/2, projector variance can be higher (commuting projector jumps add within-event variance). The non-Clifford case is entanglement-limited: reaches χ_max = 128 at γ = 10⁻³ for both unravelings.

## Deep-dive (2026-07-06 pass): exact trajectory/jump bookkeeping [paper]

**One TJM step (Sec. II B, Eqs. 2-7).** Fix step δt, normalized input MPS |ψ⟩. Define

> "Heff = H − (i/2) Σ_m γm L†m Lm" (Eq. 2)

Strang split the non-Hermitian drift:

> "e^{−iHeff δt} = e^{−(1/2)δt Σ γm L†m Lm} · e^{−iH δt} · e^{−(1/2)δt Σ γm L†m Lm} + O(δt³)" — ":= D[δt/2] U[δt] D[δt/2]" (Eq. 3)

Unnormalized no-jump update |ψ̃⟩ = D[δt/2] U[δt] D[δt/2] |ψ⟩ (Eq. 4). The jump decision uses the **exact norm loss**:

> "δp = 1 − ∥ψ̃∥² ≈ δt Σ_m γm ⟨ψ|L†m Lm|ψ⟩, where the approximation is the standard first-order MCWF hazard for small δt." (Eq. 5)

With probability 1−δp: |ψ′⟩ = |ψ̃⟩/∥ψ̃∥ (no jump). Otherwise sample channel m with

> "P[m | jump] = γm ⟨ψ|L†m Lm|ψ⟩ / Σ_j γj ⟨ψ|L†j Lj|ψ⟩" (Eq. 6)

and apply the normalized jump |ψ′⟩ = Lm|ψ⟩/∥Lm|ψ⟩∥ (Eq. 7). "In tensor form, Lm is applied by contracting the corresponding local operator into the affected site(s), followed by re-canonicalization." (Sec. II B)

**Noise-model generality of the cTJM skeleton (Sec. III):**

> "Noise is given by an arbitrary Markovian Lindblad model with jump set {(γm, Lm)}_{m=1}^k where each Lm is an arbitrary Lindblad operator that has finite support in the qubit line." (Sec. III)

Per gate g with support Qg (|Qg| ∈ {1,2}), the active local jump set is Sg := {m : supp(Lm) ∩ Qg ≠ ∅} and the noise generator is windowed to Sg (Eq. 14). The cTJM step is: local TDVP gate on Qg → local dissipative contraction Dg (m ∈ Sg only) → local jump sampling (Lg only) → optionally record X_g = ⟨ψg|O|ψg⟩ (Algorithm 1). Crucially:

> "the only difference is that in cTJM we apply them once per gate with a full time step δt and omit the half-step contractions. We allow for at most one jump per 2-qubit gate per trajectory, which could be generalized to multijump events. Nevertheless this is out of the scope of this work." (Sec. III)

[ours] The at-most-one-jump-per-gate-window rule is a per-window truncation of the jump expansion — an O((Γ_window δt)²) bias per window relative to the exact window channel; the paper does not quantify it (declares multi-jump "out of scope"). This matters when comparing against a backend that applies the exact integrated slice channel (Kraus-sampled exp(L·t)): the exact-slice sampler has NO such per-window bias.

**SPLM specialization (Sec. II C 2) — where the bookkeeping collapses.** For Pauli jumps Lm := Pm, P†m Pm = 1 gives (Eq. 12) δp_m = δt γm ⟨ψ|ψ⟩ for all m — state-independent. Consequences, verbatim:

> "Thus the probability distribution stays the same for all n timesteps. Instead of calculating it again, it simply has to be calculated once before the first timestep. With this we also do not need the stochastic MPS Φ anymore, which is an auxiliary MPS used in [13] to sample the jump operators in each timestep." (Sec. II C 2)

The fixed probability vector p_m = γm / Σ_j γj is precomputed and "sample an index m from p in every timestep where ϵ < δp" (Sec. II C 2, ϵ a uniform draw). The dissipative contraction reduces to a global scalar (Eq. 13): D[δt] = e^{−(1/2)δt Γtot} · 1, "physically irrelevant after renormalization of the state. It only serves the norm reduction to sample the jump operators." (Sec. II C 2)

**Error budget (Sec. III B).** Four declared error sources: (i) Monte Carlo, SE = sqrt(Var(Xg)/Ntraj) (Eq. 15); (ii) TDVP time-integration "order O(δt³) per (sub)step and O(δt²) over a fixed evolution interval"; (iii) gate/noise interleave: "interleaving the coherent gate update with the dissipative/noise step constitutes an operator splitting, whose (Strang-type) time-step error scales as O(δt³)"; (iv) SVD truncation "controlled by the threshold and the cap χmax, which can be monitored via discarded weight." And the one un-estimable term:

> "The only error that cannot be estimated exactly in general is the projection error incurred by restricting the dynamics to a lower-dimensional manifold." (Sec. III B, Eq. 16 residual ε(χ))

## Deep-dive (2026-07-06 pass): cost model vs plain MCWF / Kraus insertion [paper]

**No asymptotic-complexity claim is made over plain MCWF-on-MPS.** The paper's stated gains are (1) variance constants, (2) per-trajectory bond dimension, (3) bookkeeping (hazard precomputation + removal of the auxiliary sampling MPS of [13]):

> "Both schemes are unbiased and inherit the standard 1/√N Monte Carlo convergence, but with substantially smaller constants due to variance reduction. Empirically, projector sampling markedly reduces the required bond dimension per trajectory across many circuit architectures, while analog sampling excels at low noise." (Abstract)

> "This choice is algorithmically decisive: for Pauli jumps Lm = Pm one has P†m Pm = 1, so jump hazards become state-independent and the dissipative contraction collapses to a global scalar that cancels upon renormalization; jump probabilities can therefore be precomputed per layer." (Sec. I)

> "This removes auxiliary hazard estimators and makes layer-wise sampling stable and efficient while retaining pure state MPS scaling." (Sec. VI)

The paper's positioning against the two standard alternatives (Sec. I): vs density-matrix MPO/MPDO — "it trades determinism for memory efficiency by representing the mixed state as an ensemble of cheaper MPS trajectories"; vs standard trajectory sampling — the motivating problem is "the high variance in trajectories of standard Kraus-insertion approaches" (Abstract).

**The paper's own quantitative gain numbers (all SPLM/Pauli-specific):**
- Variance closed forms (2-qubit check, Sec. V A): Var_std = 1 − e^{−4Γanti t} = 1 − e^{−8γt} (Eq. 44) vs Var_proj = e^{−4γt}(1 − e^{−4γt}) (Eq. 45) vs analog plateau 1/4 (Eq. 46). N_traj = 2000.
- Bond dimension (25q XY quench, Sec. V B, γ = 10⁻²): projector "staying below the hard cap χmax = 128 up to depth 20, whereas the other unravelings saturate near χmax around step ≈ 14."
- γ = 10⁻¹: "projector trajectories remain extremely low-entangled (average bond dimension χ ∼ O(1)), while standard and analog unravelings continue to generate substantially larger bond dimensions."
- 127q kicked Ising (Sec. V C): "the projector unraveling keeps the variance uniformly bounded (peaking around ∼ 0.4), whereas the standard unraveling can exhibit substantially larger fluctuations"; "We observed that also in longer runs of up to 20 Trotter steps the projector-unraveling variance never permanently exceeded 0.4." N_traj = 100, χmax = 128.
- Long-range noise (Sec. IV C): any collapse operator of the form a·1 + b·P "admits an exact matrix product operator (MPO) with bond dimension D = 2, independent of the separation j − i" — no SWAP overhead for non-adjacent noise supports.

[ours] The explicit per-step complexity formula O(N n L χ³ [D + d²]) is in the parent TJM paper (2501.17913), not restated here; the cTJM cost per gate-window = one local TDVP gate + (SPLM: scalar contraction, free; generic Lm: local D_g contraction) + at most one local jump contraction + re-canonicalization. For a generic (non-Pauli) jump set the hazard ⟨ψ|L†m Lm|ψ⟩ must still be evaluated per window per active channel — i.e. the SPLM bookkeeping gain vanishes and the cost reverts to plain MCWF-on-MPS.

## Deep-dive (2026-07-06 pass): mid-circuit measurements / feedback [paper]

**Not treated.** The full text contains NO mid-circuit projective measurement, no measurement-outcome sampling, no classical record, and no feedback/feedforward. Verified by exhaustive search of the PDF text: circuits are gate-only sequences U = (U1, ..., UM) with |Qg| ∈ {1, 2} (Sec. III); readout in all three experiments is a trajectory-averaged *expectation value* (⟨Zi⟩, ⟨Z106⟩), never a sampled measurement outcome. The only two occurrences of "measurement":

> "(15) ... evaluated at the desired gate index g (or measurement positions)." (Sec. III, on where trajectory estimators X_g are recorded — not a projective collapse)

> "the projector variance can be higher because commuting projector jumps induce measurement backaction and add a nonzero within-event contribution P[Ec]σ²_comm" (Sec. V C — "measurement" here describes the *unraveling's* projector jumps, not circuit measurements)

Theorem 1 and the absorbing-window machinery explicitly assume "(i) no Hamiltonian/gate action" inside the window (Theorem 1) — the variance theory is derived for measurement-free noise windows, and the absorbing-window condition is stated via back-propagated observables through Clifford segments (Sec. IV B 1), not through measurement collapse.

[ours] Consequence for a QEC record generator: per-round projective stabilizer measurements + leaked-readout POVM + conditioning are *outside the paper's scope*. Grafting Born-sample-and-collapse onto cTJM trajectories is mechanically compatible (a trajectory is a pure state; this is exactly what our sv/mps carrier already does), but (i) none of the paper's variance theory survives across a projective collapse (the Bernoulli law conditions on "no jump by time t" from a fixed O-eigenstate; a mid-window projective measurement re-prepares the state and resets the bookkeeping), and (ii) the paper offers no guidance on measurement-conditioned records (syndrome streams), which are the twin's actual output object.

## Deep-dive (2026-07-06 pass): relation to Sander 2501.17913 (the original TJM) [paper]

**cTJM extends 2501.17913; it does not supersede it.** Ref. [13] of this paper IS Sander et al., Nature Communications 16, 11074 (2025) = arXiv:2501.17913 (same group; Sander is 2nd author here, 1st author there; see our note `sander_tjm_tensor_jump_2501.17913.md`).

> "In this section, the main idea of the TJM is recalled, which was recently proposed in [13]." (Sec. II B)

> "We adapt the TJM to noisy quantum circuits by interleaving its trajectory sampling using the dissipative contraction and the stochastic jump rule with the local TDVP update for quantum circuits described in Sec. II A." (Sec. III)

Delta over 2501.17913, itemized:
1. **Continuous-time → circuit windowing:** the original TJM Strang-splits continuous Lindblad evolution with half-step contractions merged across steps; cTJM applies "them once per gate with a full time step δt and omit[s] the half-step contractions" (Sec. III), one noise window per gate.
2. **Hamiltonian TDVP → per-gate local TDVP:** gate application via the local-TDVP circuit method of ref. [5] (Sander et al., arXiv:2508.10096) — long-range gates without SWAP insertion.
3. **Sampling-MPS removed (SPLM only):** the auxiliary "stochastic MPS Φ" of [13] is eliminated because SPLM hazards are state-independent (Sec. II C 2, quoted above). For generic Lm this reduction does not apply.
4. **New in this paper:** the two variance-aware unravelings (analog unitary mixture with exact generator matching; projector jumps with Theorem 1 closed-form Bernoulli variance), the absorbing-window analysis with the sharp variance sandwich (Eq. 42), and the exact bond-2 long-range noise MPO (Sec. IV C).
5. **Jump truncation:** at most one jump per 2-qubit gate window (multi-jump declared out of scope) — the original TJM's per-δt jump loop has no such per-window cap (its δt is the resolution).

[ours] For our backend decision the two papers play different roles: 2501.17913 is the *generic* MCWF-on-MPS-with-TDVP engine (arbitrary Lm, continuous-time, proved MCWF↔Lindblad equivalence in its Appendix A); 2607.01323 is its *circuit-level, Pauli-noise-specialized* variance-engineering layer. Everything in 2607.01323 that goes beyond 2501.17913 is conditioned on Pauli jump structure (P† = P, P² = 1) except the per-gate windowing skeleton itself.

## Contributions (claim -> evidence -> strength) [paper]

| Claim | Evidence | Strength |
|-------|----------|----------|
| cTJM unifies local TDVP + TJM + SPLM into a single variance-aware framework | Algorithm 1 and full implementation in MQT-YAQS (Julia + Python) | Strong — algorithmic contribution with code release |
| SPLM with Pauli jump operators gives state-independent hazards | Eqs. 11-13: P_m P_m† = I => δp_m = δt γ_m (exact identity) | Theorem-grade — exact algebraic, not approximate |
| Projector unraveling yields closed-form Bernoulli variance for anticommuting channels | Theorem 1 (Eqs. 26-28), validated in Figure 1 | Theorem-grade — exact under stated conditions |
| Analog and projector unravelings have complementary noise-strength regimes | Figure 2 (XY chain) and Figure 3 (kicked Ising) numerical results | Moderate — empirically demonstrated, not theoretically proven optimal |
| Long-range noise operators on non-adjacent qubits reduce to bond-2 MPO | Section IV.3 explicit construction, independent of separation | Strong — exact algebraic construction |
| Method scales to 127 qubits with non-Clifford dynamics under depolarizing noise | Figure 3: θ_h = π/8, γ = 10⁻³, χ_max = 128 | Moderate — single benchmark, restricted noise model |

## Relevance to AI_QEC [ours]

**Direct intersections with our scalable carrier (C1 composed + non-Pauli leakage):**

1. **MPS trajectory carrier vs our TDVP-on-vectorized-Lindbladian-MPO:** Both use MPS compression for noisy circuit simulation. The cTJM approach represents the mixed state as an ensemble of MPS trajectories; our scalable carrier (mps_forward.py) uses TDVP on a vectorized Lindbladian MPO for deterministic mixed-state evolution. The cTJM's trajectory approach trades exactness for cheaper per-trajectory states; our approach trades trajectory noise for bond-dimension compression of the density operator. This is a fundamental design trade-off: **stochastic vs deterministic compression** of the mixed state.

2. **SPLM vs our GKSL parameterization:** The paper's noise model is the sparse Pauli-Lindblad model (Pauli jump operators only), which is the standard Pauli-error DEM model expressed as a Lindblad generator. Our coupling simulator uses continuous Lindblad generators with arbitrary Hamiltonian and dissipative terms, including non-Pauli coherent contributions. The SPLM assumption (all jump operators are Pauli) excludes our coherent wedge entirely. However, the paper's Theorem 1 (closed-form projector variance) and the MPO long-range construction are general to **any** Lindblad generator — they could be adapted to non-Pauli channels.

3. **The absorbing-window concept:** The projector unraveling's absorbing property (an anticommuting jump zeros the observable expectation permanently) is a structural feature of Pauli anticommutation. For non-Pauli Lindblad operators (our target), this clean absorbing structure does not hold — a fundamental limitation when extending beyond SPLM.

4. **Variance reduction techniques:** The analog/projector dual-unraveling approach provides a template for variance reduction in our MPS-based trajectory methods, if we adopt quantum-jump-based sampling for the non-Pauli component. The regime-separation principle (projector at strong noise, analog at weak) is directly applicable.

5. **Gauge/identifiability: NONE.** The paper assumes known noise parameters (forward simulation only, not estimation). There is no identifiability analysis, no gauge characterization, no mention of parameter non-identifiability under observational equivalence. This is purely a forward-simulation tool — relevant as a carrier/simulator benchmark but not to the twin's inverse-problem core.

6. **Passive detector records context:** Not treated. The method simulates circuit execution with noise at the Lindblad level; detector/syndrome records would be computed from the simulation output, but the paper does not address their correlation structure or information content for parameter learning.

### Applicability map to OUR qutrit-leakage MCWF-on-MPS carrier (2026-07-06 pass) [ours]

Our carrier (`src/qec_twin/forward/scalable/mps_forward.py`, ADR 0010): 9+ data qutrits as a quimb MPS (phys_dim=3, snake order), per-round within-cycle op streams (single-qutrit H/X gates; per-CZ-layer `exp(L/4)` Wood-Gambetta leakage slices, **Kraus-sampled exactly on the dim-3 leg** — coherent |1⟩-|2⟩ exchange θ + jumps g_seep/g_heat), then per-round **projective stabilizer parity Born-measurements** with a leaked-readout POVM, then a transversal Y frame. In the paper's own taxonomy our carrier is a "Kraus-insertion" trajectory method — but with the *exact integrated slice channel*, not a first-order jump discretization.

**Maps directly (structure-level):**
- The per-gate/per-window noise interleaving of Algorithm 1 is isomorphic to our within-cycle marshalling (gate stream + per-CZ leak slice). A TJM backend would slot into the same op-stream walk.
- The generic cTJM skeleton accepts "arbitrary Lindblad operator that has finite support" (Sec. III) and nothing in Algorithm 1 or in MPS/TDVP restricts local dimension to 2 — local dim 3 is mechanically fine for the *skeleton*.
- Our leakage jump set is single-site, so the local dissipative contraction D_g factorizes exactly (the same structure the original TJM exploits).

**Needs adaptation (and loses the paper's gains):**
- **(b) Kraus channels vs continuous Lindblad:** cTJM samples the *Lindblad unraveling* per window with at most one jump (O((Γδt)²) per-window bias, multi-jump out of scope); our carrier samples the *exact* Kraus decomposition of exp(L·t/4) per slice (zero per-window channel bias). Adopting TJM = replacing an exact slice channel by a δt-controlled approximation of it, unless the backend implements multi-jump/substepping. The trade would have to be bought back by variance/bond gains — which are Pauli-specific (next item).
- **State-dependent hazards:** our jump operators L = g|1⟩⟨2|, g|2⟩⟨1| have L†L = g²|2⟩⟨2|, g²|1⟩⟨1| ≠ 1. Every SPLM bookkeeping gain (precomputed probability vector, scalar dissipative contraction, removal of the sampling MPS) is conditioned on P†P = 1 and evaporates. Hazards must be evaluated per window per channel — plain-MCWF cost.
- **Variance-aware unravelings do NOT transfer:** the analog scheme needs e^{iθP} with P² = 1 (π-periodicity + s = E[sin²θ] generator matching); the projector scheme needs Hermitian involutive P to form Π± = (1±P)/2; Theorem 1 additionally needs {O, Pk} = 0 and no gate action in the window. Qutrit leakage operators are non-Hermitian, non-unitary, non-involutive — none of the machinery applies as stated. (Open question, unchanged from the 2026-07-03 pass: whether any absorbing-window analogue exists for leakage jumps; the paper offers "structured approximations" as outlook only, Sec. VI.)
- **(a) Mid-evolution projective measurements/feedback:** absent from the paper (see deep-dive above). Our per-round parity Born-measurement + collapse + leaked-readout POVM would be grafted on unchanged from our existing carrier; the paper contributes nothing here, and its variance theory does not survive the collapse.
- **(c) Local dim 3:** skeleton yes; every quantitative result (SPLM, both unravelings, Theorem 1, the a1+bP bond-2 MPO with Pauli blocks) is stated and proved for qubit Pauli strings only.

**Genuinely usable bits for us [ours]:**
- The bond-2 MPO trick generalizes to ANY operator of the form a·1⊗...⊗1 + b·(σ_i⊗...⊗τ_j) — our *stabilizer parity projectors* (1 ± P̃)/2 (P̃ the generalized qutrit parity string on the stabilizer support) have exactly this form, so a bond-2 MPO application is an alternative to our current per-site sqrt(E_s) contraction. Cheap experiment, independent of the TJM question.
- The regime observation "projector sampling suppresses trajectory entanglement at strong noise" is a hint that *unraveling choice is a bond-dimension lever* — relevant if our χ ever becomes the binding constraint, but it requires inventing a non-Pauli analogue first.
- Local TDVP for long-range gates (ref [5], not this paper's contribution) is relevant to our snake-order CZ layers if SWAP overhead ever binds.

**Net verdict for the parallel-TJM-backend decision [ours]:** the paper does NOT supply a drop-in gain for our setting. Its headline advantages are (i) Pauli-conditioned (state-independent hazards, both variance-aware unravelings, Theorem 1) and (ii) measured against a *first-order jump* baseline, whereas our carrier already applies exact slice channels. A TJM backend for the leakage Lindbladian would be plain MCWF with per-window one-jump bias — a strictly weaker equivalence class than the current carrier — unless extended with multi-jump sampling AND a new non-Pauli variance-reduction idea, both beyond the paper.

### Equivalence gate a TJM backend must pass (2026-07-06 pass) [ours]

What the paper itself proves/demonstrates (the basis for any gate):
- **Generator equivalence, exact:** analog unraveling matches the Pauli-Lindblad generator exactly under λs = γ (Eqs. 19-20); projector unraveling reproduces γ(PρP − ρ) exactly (Eq. 25 algebra). Both algebraic, qubit-Pauli-conditioned.
- **Unbiasedness:** trajectory means reproduce Tr(Oρ_t) — validated numerically against a density-matrix baseline only in the 2-qubit check (Fig. 1: mean e^{−4γt}), and cross-method (Qiskit Aer MPS) at 25q/127q. No exact-oracle comparison beyond 2 qubits.
- **Deterministic bias:** TDVP integration O(δt³)/substep, O(δt²)/interval; Strang interleave O(δt³); SVD truncation via discarded weight; TDVP projection error not estimable in general (Eq. 16); PLUS the undeclared-order one-jump-per-window truncation.
- **Theorem 1 (exact, conditions:** no gate action in window, all channels anticommute with O, O-eigenstate init): mean e^{−2Γanti t}, variance e^{−2Γanti t}(1 − e^{−2Γanti t}).

Therefore a gate vs our existing carrier + DM oracle should assert:
1. **vs exact density-matrix oracle (d3, 8e-style):** ensemble-mean observables and syndrome/record statistics converge to the DM oracle with bias → 0 as (δt → 0, multi-jump on, χ full) at rate O(δt²) over the cycle, MC error √(Var/N) removed by matched-N or CI; any residual at finite δt must be bounded and attributed to the one-jump truncation (measure it by halving δt).
2. **vs our MCWF-on-MPS (same trajectories):** at full χ and matched RNG semantics the two backends are NOT bit-for-bit comparable (different unraveling = different trajectory measure); the gate is distributional — same record law: matched means within SE AND a two-sample test on syndrome-record statistics at the certification sample size.
3. **Variance accounting (the only reason to adopt):** measured across-trajectory variance and per-trajectory mean χ of the TJM backend must beat the exact-slice Kraus carrier at matched accuracy — the paper's Fig. 2-3 pattern re-established on OUR non-Pauli noise, which the paper gives no theory for. If it does not beat it, the backend is pure cost.

## 6-criterion methodology table

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| **Soundness** | 5 | The TJM, TDVP, and SPLM components are individually sound (standard methods). The analytical derivations (state-independent hazards, projector variance Theorem 1, MPO construction) are exact algebraic results. Numerical validation confirms generator matching across all unravelings. |
| **Novelty** | 4 | The cTJM combination is novel. Variance-aware dual unravelings (analog+projector) with complementary regime and closed-form variance for projector are new. The bond-2 long-range MPO construction is a useful technical contribution. However, the individual components are not new. |
| **Reproducibility** | 4 | Code released via MQT-YAQS (open source). Algorithms fully specified. Numerical experiments use standard benchmarks (IBM kicked Ising). Key limitation: Julia implementation + Python package require the MQT ecosystem — not trivially portable but documented. |
| **Experimental design** | 4 | Three numerical experiments at multiple noise strengths and circuit types. Variance check against analytic predictions validates correctness. The XY chain and kicked-Ising benchmarks cover different entanglement regimes. Missing: comparison against density-matrix MPO/MPDO reference at small scale to validate absolute accuracy (only cross-method comparison). |
| **Statistical rigor** | 4 | Unbiased trajectory estimators by construction; standard error formulas provided (Eq. 15). N_traj = 200-2000. Variance reduction claims are quantitative (theorem + numerical). No analysis of convergence rate vs bond dimension as function of noise. |
| **Scalability** | 3 | Demonstrated to 127 qubits (maximum in paper). MPS bond dimension capped at χ_max = 128. Key concern: the trajectory approach, while memory-efficient per trajectory, requires many trajectories for accurate expectation values. The regime where trajectory count × MPS bond dimension is cheaper than a single MPO/MPDO evolution of the mixed state is not rigorously characterized. Deep circuits remain challenging. |

## Strengths (S1-S4)

- **S1 (Section IV.2, Theorem 1):** Exact closed-form variance for projector unraveling on anticommuting channels — rare in MCWF methods. Provides a clean benchmark case and enables principled variance-aware hybrid sampling strategies.
- **S2 (Section IV.3):** Bond-2 MPO construction for long-range Pauli noise, independent of qubit separation. Important for hardware with cross-talk or long-range coupling — commonly a challenge for tensor-network methods.
- **S3 (Section V.3):** Successful 127-qubit non-Clifford simulation under two-qubit depolarizing noise. The non-Clifford regime (θ_h = π/8) is exactly where stabilizer methods fail and where full quantum simulation matters — a genuine demonstration of the method's value proposition.
- **S4 (Section V.2):** The regime-dependent bond-dimension suppression under projector unraveling at strong noise is practically significant. If the MPS bond dimension stays O(1) at realistic hardware noise levels, deep circuits become tractable.

## Weaknesses (W1-W4)

- **W1 (Section II.3, Eq. 8-10):** SPLM restricts to Pauli jump operators only. Coherent errors are assumed "Pauli-tailored" via randomized compiling. This means the method cannot simulate native coherent errors without twirling them into stochastic Pauli noise — which is exactly the approximation that the twin's coherent wedge shows can mis-predict LER.
- **W2 (Section V.3):** The 127-qubit demonstration uses only two-qubit depolarizing noise, which is a very simple noise structure (no correlated multi-qubit, no non-Pauli, no crosstalk beyond depolarizing). The paper claims support for "correlated multi-qubit Lindblad noise" and "crosstalk," but the only non-trivial correlated model tested is the nearest-neighbor XX flip chain (25 qubits). The long-range MPO capability (Section IV.3) is not demonstrated numerically.
- **W3 (Section VI):** No definitive comparison against density-matrix MPO/MPDO for identical circuits and noise to quantify when the trajectory approach is cheaper. The regime boundaries are empirically observed rather than theoretically characterized, leaving the practical adoption guidance incomplete.
- **W4 (Section V.2-V.3):** The number of trajectories (100-200) is modest. For weak noise or high-precision applications, the trajectory noise floor may be prohibitive. The paper acknowledges N_traj = 2000 for the small check but uses only 100-200 for the large demonstrations.

## How to use / trust + open questions [ours]

**Trust level:** High for the theoretical components (state-independent hazards, projector variance Theorem 1, MPO construction — all exact algebraic results). Moderate for the numerical regime-separation claims (empirically demonstrated, not proven optimal). The code is open-source and part of the established MQT ecosystem.

**Relevance to our project:**
- **Forward-carrier comparison:** The cTJM MPS-trajectory approach is an alternative carrier for noisy circuit simulation. If our TDVP-on-Lindbladian-MPO approach struggles with specific regimes, cTJM provides a complementary approach using the same tensor-network backend (quimb is compatible with MPS trajectory methods). The key trade-off: trajectory ensemble vs deterministic mixed state.
- **Variance-reduction techniques:** The analog/projector dual unraveling is directly applicable if we extend our carrier to support trajectory-based non-Pauli sampling.
- **SPLM limitation:** The paper's restriction to Pauli noise (justified by randomized compiling) is exactly the limitation the twin is designed to overcome for coherent/correlated mechanisms. Our non-Pauli leakage carrier addresses what cTJM explicitly avoids.

**Open questions:**
- Can the projector-unraveling absorbing window concept be generalized to non-Pauli Lindblad operators (our regime), or does it depend essentially on P^2 = I anticommutation?
- What is the trajectory count × bond-dimension cost crossover relative to our deterministic Lindbladian MPO approach for the same circuits?
- Does the long-range bond-2 MPO construction work for non-Pauli operators (e.g., XX+YY exchange), or only for Pauli strings?
