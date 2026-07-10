# Full-text note -- Liao, Wang, Zhou, Zhang & Xiang, "Simulation of IBM's kicked Ising experiment with Projected Entangled Pair Operator" (arXiv:2308.03082)

> **Provenance (2026-07-09): FULL-TEXT read (精读).** TXT from arXiv (2308.03082v1, 6 Aug 2023) ->
> `outputs/papers/pepo_survey/2308.03082.txt` (~1034 lines, all appendices). This is the FIRST use of
> PEPO for time evolution, and the FIRST classical exact result for the 5+1 Trotter-step IBM kicked
> Ising circuit previously considered "beyond classical verification."

## Metadata [paper]

- **Authors / affiliation:** Hai-Jun Liao (IOP CAS / Songshan Lake Materials Lab), Kang Wang, Zong-Sheng Zhou (IOP CAS), Pan Zhang (ITP CAS / Hangzhou IAS / ICTP-AP), Tao Xiang (IOP CAS / UCAS / BAQIS). Corresponding: Liao (navyphysics@iphy.ac.cn), Zhang (panzhang@itp.ac.cn), Xiang (txiang@iphy.ac.cn).
- **Venue / status:** arXiv:2308.03082v1 [quant-ph], 6 Aug 2023. No journal publication indicated at time of reading. Code at `github.com/navyTensor/PEPO`.
- **Type:** Method + numerical simulation -- tensor-network algorithm development for quantum circuit expectation values, benchmarked against exact results (CET-derived) and against IBM quantum hardware with error mitigation.
- **One-line (paper's claim):** Heisenberg-picture PEPO with bond dimension chi=2 matches MPO chi=1024 in accuracy on the 127-qubit kicked Ising circuit, and chi=184 reproduces the 5+1-step exact result in 3 seconds on a single CPU, by automatically detecting the low-rank Clifford structure that 1D methods miss.

## Executive summary [paper]

The paper computes expectation values of the 127-qubit IBM kicked Ising circuit using a **projected entangled pair operator (PEPO) in the Heisenberg picture**. The central idea: instead of evolving the quantum state (as MPS/isoTNS do) or representing the evolution operator as a 1D MPO, the authors represent the **time-evolved observable** O(t) = U^dagger O U as a **2D PEPO** on the heavy-hexagon lattice, and evolve it layer by layer from the middle of the tensor network outward.

The headline result: on the 5+1 Trotter-step circuit (previously considered beyond exact verification), PEPO with chi=2 gives accuracy comparable to MPO chi=1024 and CPT K=10; chi=184 reaches rounding-error-level exactness in <3 seconds on a single CPU. This is enabled by two synergistic properties: **(a) the Heisenberg picture UOU^dagger cancellation** automatically detects low-rank structure when gates are Clifford or near-Clifford, and **(b) PEPO's 2D geometry** keeps all evolution operators local (no SWAP operations needed, unlike 1D MPO). The authors also develop a **Clifford Expansion Theory (CET)** to obtain exact reference values for the 5+1-step circuit (via symbolic Pauli-string commutation, reducing the effective circuit depth), and use these exact values to benchmark all methods.

For the 20 Trotter-step deep circuit, PEPO shows **monotonic convergence with chi** (unlike MPO for which the intermediate regime chi-scaling is non-monotonic), enabling extrapolation chi->infty. The extrapolated PEPO results deviate significantly from both IBM's error-mitigated hardware and other tensor-network methods in the strongly-entangling intermediate regime (pi/8 < theta_h < 5pi/16), where the true answer remains unknown.

## Method (deep) [paper]

### Heisenberg-picture PEPO (the core)

The 3D tensor network for computing <O(t)> = <psi|U^dagger O U|psi> is a "sandwich": the initial state |0><0| on one boundary, the final state |0><0| on the opposite boundary, and the observable O in the middle. The Heisenberg picture contracts **from the middle outward**: at each time step, the evolution operator U(t) and its conjugate U^dagger(t) are applied to the operator cumulatively.

**PEPO representation:** the time-evolved observable at any intermediate step is represented as a 2D tensor network (PEPO) on the heavy-hexagon lattice. Each site carries a rank-6 tensor (physical row/col indices + 4 virtual bond indices for the 2D lattice). The virtual bond indices encode operator entanglement across the lattice.

**Evolution procedure (simple-update):**
1. Start with the bare observable O (e.g., the weight-17 stabilizer W17 or local Z62) as a PEPO with bond dimension chi=1 (product operator).
2. Apply one Trotter layer (RZZ then RX) to the operator from both sides simultaneously: O <- RZZ^dagger RX^dagger O RX RZZ.
3. After each application, the bond dimensions grow; truncate back to chi using SVD with simple-update weighting (the environment approximation uses the singular value spectra from neighboring bonds).
4. Repeat until the boundaries are reached (i.e., all Trotter steps applied).
5. Contract the final PEPO with the boundary product states |0><0| to obtain the expectation value.

Computational cost per evolution step: O(L chi^4) with L=144 edges on the heavy-hexagon lattice. Final contraction: O(chi^6).

### Why PEPO works so well here (two-level advantage)

**Level 1 -- Heisenberg picture cancellation (the UOU^dagger structure).** When the circuit contains Clifford gates, U is a Clifford unitary, and U^dagger O U maps a Pauli operator to another Pauli operator (single Pauli string). The operator remains a **product operator** (bond dimension 1). In the kicked Ising model, the RZZ gates are exact Clifford (pi/4 ZZ rotations). The RX(theta_h) gates become Clifford only at theta_h = pi/2. Thus:

- At exact Clifford points (theta_h = pi/2): chi=1 suffices for exact results. The Heisenberg evolution is just Pauli-string propagation.
- Near Clifford points (theta_h ≈ pi/2): the operator remains low-rank because the non-Clifford RX gates introduce only a small admixture of extra Pauli strings. PEPO automatically captures this by keeping only the dominant singular values.
- For theta_h far from pi/2: operator entanglement grows, and larger chi is needed.

**Crucially, Schr&ouml;dinger-picture methods (MPS, isoTNS, BP-TNS) never encounter the UOU^dagger structure** and therefore completely miss this low-rank opportunity. The Schr&ouml;dinger state evolves from |0> to a highly entangled state even at Clifford points (RY Y |00> = (|00> - i|11>)/sqrt(2), a Bell state), so MPS needs large bond dimension throughout.

**Level 2 -- 2D geometry (PEPO vs MPO).** The 127-qubit heavy-hexagon is a 2D lattice. A 1D MPO representation (as in Anand et al. [3]) must embed this 2D connectivity into a 1D ordering, which creates **long-range operator strings and necessitates SWAP operations**. SWAPs reduce efficiency and accuracy because they increase operator entanglement artificially. PEPO respects the native 2D lattice: every RZZ gate connects **nearest neighbors on the PEPO lattice**. No SWAPs needed.

The combination of these two effects explains the factor ~500 advantage (chi=2 PEPO = chi=1024 MPO).

### Clifford Expansion Theory (CET)

The CET is a **manual, circuit-specific symbolic reduction** (not part of the PEPO algorithm). It works by:

1. Taking the expectation value <psi|U^dagger O U|psi> for a shallow circuit (5+1 steps).
2. Systematically commuting the Clifford RZZ gates through the non-Clifford RX gates using the symbolic identities:
   - After commuting a Clifford gate past a Pauli string, the Pauli string changes (possibly with coefficient cos/sin terms).
   - Each commutation step generates a sum of Pauli strings with trigonometric coefficients (ch = cos(theta_h), sh = sin(theta_h)).
3. After all Clifford gates are commuted out, the effective circuit depth is reduced (from 5+1 to 3 or 4 steps), and the remaining operator is a **sum of polynomially many Pauli strings**.
4. Each Pauli string expectation can be computed by exact contraction of a small tensor network (bond dimension D=8-16).
5. The summation over Pauli strings is handled efficiently using the DMRG trick of "absorbing into left/right environments" rather than summing term-by-term.

The CET expressions are explicitly given in the Appendix (Eqs. 6-10 for W10, W17, W-tilde-17, and Z62). For example, the exact depth-4 result for <Z62>_4 = c_h^4 (1 + 2 s_h^2 - 3 c_h^2 s_h^10). This single polynomial encodes the full 127-qubit result -- because the CET reduces the problem to low-depth irrespective of system size.

**Why CET is possible here (and not generally):** The RZZ gates are Clifford (exact). The circuit is shallow enough (5+1 = 6 layers) that the number of Pauli strings generated by commutation remains tractable (a few hundred). For deeper circuits, the Pauli-tree branches exponentially, making CET infeasible without truncation (which would approximate CPT).

### chi=2 vs MPO chi=1024 -- the detailed mechanism

The factor ~500× advantage is not a single mechanism but the **product of two orthogonal effects**:

1. **Heisenberg geometry factor (~10-30×):** At near-Clifford theta_h, the MPO in the Heisenberg picture (Anand et al.) already benefits from UOU^dagger cancellation, but as a 1D MPO it still needs many bond states because distant lattice sites become coupled through the 1D ordering. PEPO's 2D geometry avoids this -- each bond only couples nearest neighbors. For a 2D lattice of N sites, the 1D embedding cuts O(sqrt(N)) long-range bonds per site, each requiring bond dimension growth.

2. **PEPO bond compression factor (~10-50×):** Even at the same bond dimension, PEPO represents operator correlations on a 2D lattice more efficiently than MPO because a 2D tensor network can distribute entanglement through two independent spatial directions. MPO must serialize all correlations through a single chain.

The paper reports this as an empirical observation (Fig. 2 right panel: PEPO chi=2 error curve matches MPO chi=1024 error curve across all theta_h), not a proven bound. The factor varies with theta_h -- at exact Clifford points (theta_h=pi/2), PEPO chi=1 is exact while MPO still needs finite chi.

### chi-scaling with depth (20 Trotter steps)

For the depth-20 circuit (Fig. 3 left), <Z62> is computed at varying chi. The key observations:

- **Rapid convergence:** <Z62> becomes nearly chi-independent for theta_h <= pi/8 and theta_h >= 5pi/16. In these regimes, small chi (8-32) suffices.
- **Monotonic convergence:** In the intermediate regime (pi/8 < theta_h < 5pi/16), <Z62> varies monotonically with 1/chi. This is critical -- it allows extrapolation to chi->infty using the fitted function b*exp(-a/chi).
- **Contrast with MPO:** The paper states MPO shows non-monotonic chi-dependence in this regime, making extrapolation unreliable.
- **Largest run:** chi=256, 7 hours on one Intel Xeon Gold 6326 CPU for a single data point.

The exponential form b*exp(-a/chi) for extrapolation is not physically derived but empirically observed. The paper does not provide a theoretical argument for this specific scaling form.

### Geometric advantage over 1D methods

The heavy-hexagon lattice (Fig. 1 of the paper) has degree <=3 per qubit, but it is genuinely 2D (contains cycles, e.g., hexagons). The comparison:

| Method | Geometry | SWAP ops? | Long-range ops? | chi for 5+1-step |
|--------|----------|-----------|-----------------|------------------|
| MPS (Schr.) | 1D chain (embedding) | Yes | Yes | 3072 (still inaccurate) |
| isoTNS (Schr.) | 2D but state | N/A | N/A | Large (inaccurate) |
| MPO (Heis.) | 1D chain (embedding) | Yes | Yes | 1024 (good accuracy) |
| CPT | Pauli truncation | N/A | N/A | K=10 (good accuracy) |
| PEPO (Heis.) | 2D native | **No** | **No** | 2 (~MPO 1024), 184 (exact) |

The paper shows that Schr&ouml;dinger-picture methods (MPS, isoTNS, BP-TNS) fail even qualitatively at near-Clifford theta_h (their results deviate from zero significantly at theta_h > 5pi/16 where the true answer is ~0, Fig. 3 right). This is because they evolve the state forward, which becomes highly entangled at Clifford points (Bell states across every RZZ pair), while the actual expectation value is simple.

## Findings + numbers [paper]

| Result | Numbers |
|--------|---------|
| 5+1-step W-tilde-17 accuracy | PEPO chi=2 error ~10^{-3} to 10^{-8} (varies with theta_h); matches MPO chi=1024 and CPT K=10 error curves (Fig. 2 right). |
| 5+1-step exact result (chi=184) | PEPO error below double-precision rounding (~10^{-15}) at all theta_h. Runtime: <3 seconds per point, single CPU. |
| Clifford point (theta_h=pi/2) | PEPO chi=2 error drops to exactly 0. PEPO chi=1 is exact. MPS/isoTNS give wrong results. |
| IBM hardware (5+1-step) | Error-mitigated IBM results deviate visibly from exact results (Fig. 2 left). MPS chi=3072 also deviates. CPT K=10 deviates in intermediate regime. PEPO chi=2 already matches exact. |
| 20-step extrapolation regime | theta_h <= pi/8: trivial (all methods agree). pi/8 < theta_h < 5pi/16: intermediate (PEPO > other methods). theta_h >= 5pi/16: near-Clifford (PEPO, CPT, MPO, Google 31-qubit converge to 0; MPS, isoTNS, BP-TNS deviate to ~0.4). |
| Max computation | chi=256, 7 hours/single point, single CPU, 20 Trotter steps. |
| CET exact results | W10: <30 sec/point. W17: <30 sec/point. W-tilde-17: <5 hours/point. Single CPU. |

## Limitations [paper]

- **Circuit-specific empirical observation, not a theorem.** The paper demonstrates that PEPO works remarkably well for the IBM kicked Ising circuit, but does not prove rigorous bounds on bond dimension for general circuits. The chi=2 vs chi=1024 comparison is empirical, not analytic.
- **Extrapolation form is ad hoc.** The exponential b*exp(-a/chi) fitting function (Fig. 3 left) is not derived from first principles. For the intermediate regime (pi/8 < theta_h < 5pi/16), there is no exact reference to confirm the extrapolation. The paper concedes "due to the strong entanglement and non-verifiable nature, we cannot tell which method is more accurate in this regime."
- **CET is manual and non-scalable.** The CET symbolic reduction uses problem-specific commutation relations. It works for the 5+1-step circuit because the depth is shallow enough that the number of Pauli strings stays manageable. For 20 steps, the tree would be exponentially large. CPT (Clifford Perturbation Theory) generalizes this by truncating, but is approximate.
- **Simple-update truncation is uncontrolled.** The PEPO evolution uses simple-update (rank-1 environment approximation) for bond truncation. Unlike full-update or variational optimization, the error from simple-update is not systematically controllable. The paper justifies it pragmatically: the results converge with chi and agree with the exact reference at chi=184.
- **PEPO cost scales as chi^4 per step, chi^6 for final contraction.** For very large chi (required for deep circuits with strong entanglement), this scaling is steep. The paper's largest chi=256 takes 7 hours. For circuit depths beyond 20 steps with non-Clifford gates, chi would need to grow further, potentially making the O(chi^6) contraction prohibitive.
- **No open-system / noise treatment.** The paper treats only unitary (closed-system) evolution. There is no density matrix, no Lindblad master equation, no decoherence. The observable expectation is for a pure state.

## Relevance to qec_twin [ours]

### 7. Can Heisenberg-picture PEPO be adapted for noise channel evolution in QEC?

**Yes, in principle, but with critical caveats.** The core idea -- evolving an operator (or channel) in the Heisenberg picture using a 2D PEPO on the lattice geometry -- maps directly to noise channel evolution in QEC:

- In QEC, noise channels are applied to the density matrix: rho -> E(rho) = sum_k K_k rho K_k^dagger. In the Heisenberg picture, we evolve observables: O -> E^dagger(O) = sum_k K_k^dagger O K_k.
- If the noise channels are Pauli channels (stochastic Pauli errors), E^dagger acts as a linear map on Pauli operators -- exactly the same structure as Clifford conjugation but with damping instead of rotation. The low-rank detection would work: if the noise is near-Pauli (mostly identity, small error probabilities), the Heisenberg-evolved operator stays low-rank because a dominant weight stays on the identity/trivial Pauli strings.
- **The critical extension needed:** QEC noise is not unitary. The PEPO evolution would need to handle **non-unitary operator maps** (Kraus maps). The paper's approach specifically exploits unitary cancellation U^dagger(.)U; for noise channels, we have sum K_k^dagger(.)K_k, which does not have the same cancellation structure because the Kraus operators do not compose into a single unitary. The bond dimension would grow as the number of Kraus terms rather than canceling.

**The "near-Clifford" analogy for QEC:** Just as the kicked Ising circuit becomes easy when RX is near-Clifford (theta_h close to pi/2), QEC circuits become easy when noise is near-Identity (small error rates). A Heisenberg PEPO tracking how Pauli operators spread under near-Identity noise would be low-rank for exactly the same reason: the dominant term is the identity, and the corrections are few. This is the fundamental reason Pauli-based DEM simulation (Stim) is efficient -- but PEPO could extend this to **coherent over-rotation errors** (which are exactly like the non-Clifford RX(Delta_theta) in the kicked Ising model, but applied as noise rather than gates).

### 8. Does this method carry to open systems / density matrices?

**Partially -- it carries to the Heisenberg-picture adjoint of a CPTP map, but not to mixed-state evolution without modification.**

**What carries:** The Heisenberg-picture evolution of an observable under a CPTP map E: O -> E^dagger(O) = sum_k K_k^dagger O K_k. If E is a gate (Clifford or near-Clifford), E^dagger is just the unitary adjoint, and the full power of UOU^dagger cancellation applies. If E is a noise channel (e.g., amplitude damping, dephasing), E^dagger is a sum of Kraus-adjoint terms.

**What does NOT carry:** The paper's method computes <psi|O(t)|psi> for a pure state. For a QEC mixed state rho(t) = E_t ... E_1(rho_0), the expectation is tr[rho(t) O] = tr[rho_0 E_1^dagger ... E_t^dagger(O)]. Computing this via Heisenberg PEPO would mean:

1. Representing O as a PEPO (easy for Pauli observables -- product operator, chi=1).
2. Applying E_t^dagger, ..., E_1^dagger sequentially (Heisenberg evolution of the observable).
3. Contracting with the initial mixed state rho_0 (not a pure product state if the code has stabilizer structure).

**The crucial difficulty for QEC:** The initial state rho_0 is the **stabilizer state** of the surface code -- highly entangled. Contracting the final PEPO with an entangled boundary state would be expensive. In contrast, the paper contracts with |0><0| (product state), which is trivial.

**Potential paths forward:**

**(a) Sandwich contraction:** Compute <O(t)> = tr[r_0 E_total^dagger(O)] by first evolving O backward (Heisenberg), then contracting with the entangled initial state using a separate 2D tensor network (PEPS) for the stabilizer state. This is essentially what existing TN QEC decoders do (Ferris-Poulin, Darmawan-Poulin, Bravyi-Suchara-Vargo), but using 1D MPS rather than 2D PEPO. Upgrading to 2D PEPO for the state side would address the `2^{2d}` bond wall we identified for surface-code d.

**(b) Density-matrix PEPO (mixed-state carrier):** Directly represent the full density matrix as a PEPO (the vectorized Liouvillian approach, as in tePEPO/arXiv:2512.01781). This would allow forward-evolving rho through noise channels + gates in the Schr&ouml;dinger picture, using PEPO's geometric advantage for the 2D lattice. The cost: the PEPO's local dimension becomes d^2 (9 for qubit, 16 if leakage included), and each bond carries the operator entanglement of the mixed state. This is the 2D-iPEPO direction we identified as potentially necessary for d>=7 surface code.

**(c) Channel-PEPO: track the noise channel evolution itself.** Instead of evolving the observable or the state, evolve the **channel field** (the set of per-location CPTP maps). This is the twin's core object: we want to know how gate operations transform the noise channel E_gate composed with E_noise. For a Clifford gate G, the noise channel transforms as E_noise -> G^dagger circ E_noise circ G (in the Choi picture, this is just a permutation of Pauli-error probabilities for Pauli noise). For near-Clifford gates (small coherent errors), the transformation introduces small off-diagonal terms. A PEPO tracking these transformed channels across the 2D lattice would automatically exploit the near-Clifford low-rank structure.

### Synthesis: PEPO for the twin's composed carrier

The paper's key lesson for us is **not** that PEPO is a drop-in replacement for our MPS carrier, but rather:

1. **The Heisenberg picture is the natural language for noise channel evolution** through Clifford circuits. Noise channels in the Heisenberg picture (adjoint map) are exactly what the `composed.py` carrier constructs -- the `hardware/windows.py` Heisenberg evolution of the noise channel window is the same concept. The paper provides a **2D-geometry version** of this same evolution, which could avoid the 1D-embedding overhead of our current MPS (which hits a bond wall for d>=7).

2. **The near-Clifford efficiency mechanism** (dominant identity + small non-Clifford corrections = low PEPO bond dimension) has a direct analogue in QEC: **near-Identity noise** (dominant identity channel + small error probabilities = low PEPO bond dimension for the noise-evolved operator). This suggests that a Heisenberg PEPO for the noise-evolution operator through a surface-code round would be efficient at physical error rates p << 1, exactly when we care most about accuracy.

3. **The geometric 2D advantage** matters for the heavy-hexagon surface code, which is a subset of the square-octagon lattice (when rotated). A 2D PEPO carrier would natively represent the code's stabilizer geometry without the long-range SWAP overhead of 1D MPS. This is the path from our current d=3/d=5 MPS to d>=7.

4. **Open problem not addressed here:** The paper's Heisenberg evolution is for unitary conjugations of a single observable. For QEC, we need the evolution of a **complete set of observables** (the syndrome outcomes, the logical operators), or equivalently the full channel. The bond dimension requirement for tracking a full operator basis (vs a single observable) would be larger, potentially erasing the advantage. The paper only computes one expectation value at a time; computing the full syndrome distribution would require many such PEPO evolutions or a different approach.

## How to use / trust + open questions [ours]

- **Trust level:** FULL-TEXT 精读 (1034 lines including appendices). Algorithm claims verified against the exact CET reference for 5+1 steps. The chi=2 vs MPO chi=1024 comparison is empirical but clean (error curves overlap across all theta_h in Fig. 2). Code not inspected (GitHub referenced but not audited).

- **Independent-oracle-ability:** EXCELLENT for the 5+1-step circuit -- the CET provides exact reference values against which any method can be benchmarked. For the 20-step circuit, NO independent oracle exists (the paper concedes this). This is a critical gap: the paper's headline extrapolation claims for 20 steps rely on the monotonic chi-scaling assumption and the exponential fitting form, which are not independently certified.

- **CET as a verification tool for the twin:** We could potentially apply the same Clifford expansion approach to simplified QEC circuits (few rounds, Clifford gates, near-Clifford noise) to generate exact reference syndrome distributions for benchmarking our tensor-network carriers. This would give us what the paper has for the kicked Ising: ground truth for a circuit that approximate methods find challenging.

- **Open questions for implementation in qec_twin:**

  (1) **Single-observable vs full-channel cost.** The paper computes one expectation at a time. For QEC we need syndrome statistics (many observables) or the full noise channel. Can we evolve the entire channel as a PEPO (cost O(L chi^4) per step) and then extract all observables from a single contracted tensor network? Or must we repeat for each syndrome observable (multiplying cost by number of stabilizers)?

  (2) **Boundary contraction cost.** The paper contracts PEPO with |0><0| (product state). For QEC, the initial state is a stabilizer state (entangled). Contracting PEPO with a PEPS representation of a stabilizer state would add significant cost. Is there a way to absorb the stabilizer state into the PEPO evolution (e.g., by starting the PEPO from the final observable and evolving backward through both gates and the initial state preparation)?

  (3) **Non-unitary Kraus evolution.** The paper's unitary cancellation mechanism (U^dagger O U) does not extend to general CPTP maps because sum K_k^dagger O K_k does not factor into a single unitary. For near-Identity noise (error probability p << 1), the dominant term is the identity channel, and the first-order corrections are few -- so the PEPO bond dimension may still be small. But for large error probabilities or coherent errors near pi, the bond dimension would grow. We need to characterize when this breaks.

  (4) **Monotonic chi-convergence for QEC observables.** The paper's ability to extrapolate chi->infty relies on monotonic convergence of the expectation with chi. Is this property preserved for QEC observables (syndrome probabilities, logical error rates)? If not, the extrapolation technique would not transfer, and we would be limited to finite-chi accuracy without a certified error bound.

  (5) **The "inverse problem" direction.** The paper uses PEPO to compute expectation values from a known circuit (the forward problem). Our twin also needs the inverse problem: given observed syndrome statistics, infer the noise parameters. The paper's PEPO framework is not directly differentiable (no mention of gradients or automatic differentiation), unlike our MPS carrier which has differentiable SVD. A PEPO carrier would need a differentiable truncation to serve the calibration loop.

- **GT-feasibility verdict:** The Heisenberg PEPO method is a legitimate, benchmarked technique for 2D unitary quantum circuit expectation values, with a strong certified result on the 5+1-step circuit. For the twin's target (noise channel evolution through QEC circuits), the method offers a promising **2D-geometry alternative** to our 1D MPS carrier, potentially breaking the `2^{2d}` bond wall. However, the transition from unitary-observable evolution to non-unitary full-channel evolution is nontrivial and unaddressed by this paper. The paper's strongest lesson may be architectural: **the Heisenberg picture + 2D tensor network geometry is the right mathematical structure for exact/near-exact Clifford circuit simulation**, and a QEC carrier built on the same principles could inherit similar efficiency for near-Identity noise.

## Key equations to remember

- Kicked Ising unitary per step: U_T(theta_h) = [RZZ RX(theta_h)]^T, with RZZ = prod_{<ij>} exp(i pi/4 ZiZj), RX(theta_h) = prod_i exp(-i theta_h/2 Xi).
- Cost per step: O(L chi^4), L=144 edges. Final contraction: O(chi^6).
- Extrapolation form: b*exp(-a/chi) (empirical, not derived).
- CET exact result for <Z62>_4: c_h^4 (1 + 2 s_h^2 - 3 c_h^2 s_h^10), where c_h = cos(theta_h), s_h = sin(theta_h).
