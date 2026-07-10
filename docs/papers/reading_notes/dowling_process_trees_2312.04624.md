# Full-text review — N. Dowling, K. Modi, R. N. Munoz, S. Singh & G. A. L. White, "Capturing Long-Range Memory Structures with Tree-Geometry Process Tensors" (arXiv:2312.04624 / PRX 14, 041018)

> **Provenance (2026-07-09): FULL-TEXT 精读.** HTML-to-text from arXiv:2312.04624v2 (quant-ph) → final published version (PRX 14, 041018, 2024). 3879 lines of extracted text (including appendices). All references to sections, equations, figures from this source.

> **ID/title verified.** The paper is exactly the Dowling et al. process-tree paper cited in the user brief. arXiv:2312.04624 matches the published PRX 14 041018.

## Metadata [paper]

- **Authors / affiliation:** Neil Dowling, Kavan Modi, Roberto N. Munoz, Sukhbinder Singh, Gregory A. L. White — School of Physics & Astronomy, Monash University, Clayton, VIC, Australia (Dowling, Modi, Munoz, Singh); Quantum for New South Wales (Modi); Multiverse Computing, Toronto (Singh); Freie Universitat Berlin / Dahlem Center (White).
- **Venue / status:** arXiv:2312.04624v2 [quant-ph] -> Phys. Rev. X 14, 041018 (2024). Published.
- **Type:** Theory + numerical method + benchmark (new tensor network ansatz for non-Markovian quantum processes).

## Executive summary [paper]

The paper introduces **process trees** — a class of quantum non-Markovian processes represented by a tensor network with **binary-tree geometry** (not the usual chain/MPO geometry). The process tree is constructed by iteratively applying a **one-time-to-two-time superprocess** (a "fine-graining" map) that is **causality-preserving** and optionally **scale-consistent**. The key claims:

1. Process trees **generically exhibit polynomially decaying temporal correlations** (Theorem 1), in stark contrast to MPO processes which generically decay exponentially (Proposition 2). This mimics the spatial-TTN result: tree geometry enables power-law correlations.
2. The long-range correlations originate **almost entirely from non-Markovian memory effects**, and can be **genuinely quantum** (entanglement in time) for structured (low-randomness) unitaries (Sec. V).
3. The process tree **outperforms fixed-bond-dimension MPO** in fitting the spin-boson model across a BKT phase transition — using **2-60x fewer parameters** achieving better overlap (Sec. VI).
4. The process tree can be **systematically constructed from an underlying Hamiltonian** using 2D tensor network renormalization group (TRG) methods applied to the **Feynman-Vernon influence functional** (Sec. VII, Fig. 9).

The spin-boson model serves as the primary benchmark: its Ohmic variant exhibits polynomially decaying non-Markovianity across coupling strengths, and process trees fit it with high fidelity (F2 overlap > 0.9 for most coupling regimes). Notably, a **scale-and-time-homogeneous** process tree (single W-brick across all positions and scales) fit to an **8-step process generalizes to 16, 32, and 64 steps** with surprisingly good overlap — a predictive capability.

## Method (deep) [paper]

### Process tensor background (Sec. II)

The paper builds on the **process tensor** formalism [Pollock et al. 2018a, 2018b]: a multitime quantum process is a CPTP map from a sequence of instruments (operations) to the final system state, represented as a Choi state. The canonical causal constraints (Eq. 7) enforce that future instruments cannot affect past measurement statistics.

In MPO representation (the standard chain/tensor-train geometry), the process tensor has bond dimension = environment dimension dE. **Proposition 2** (App. B, D) proves that such MPO processes with finite dE generically exhibit **exponentially decaying temporal correlations** — a direct consequence of the spectral gap of a repeated CPTP map. This is the time-domain analog of the MPS area-law: bounded bond dimension implies exponentially decaying correlations.

### Process tree construction (Sec. III)

**Core building block: the W-superprocess (Eq. 17).** This is a one-time-to-two-time superprocess parameterized by two unitaries U1, U2 and a density matrix rho:

```
W = (diagram in Eq. 17): three CPTP maps Lambda1=U2, Lambda2=U2^dag U1, Lambda3=U1^dag
    + ancilla space + preparation rho
```

The **scale consistency condition** (Eq. 16) is the crucial constraint: inserting identity (do-nothing) operations at both fine-grained time slots must reduce to identity at the coarse slot. This is equivalent to demanding that the W-brick satisfies W^T|union>>|union>> = |union>>, where |union>> is the Choi state of the identity instrument.

**Process tree = recursive fine-graining** (Fig. 2): Start from a single-time measurement process (Eq. 14). Apply one W to get 2 intervention times. Apply two W's (one per coarse slot) to get 4 times. Continue for N-1 steps -> 2^N intervention times. The resulting tensor network is a **binary tree** with baked-in causality.

**Scale causal cone** (Fig. 3): For W-type trees, any single intervention slot contracts to exactly one tensor per scale — O(N) tensors out of O(2^N) total. This is the temporal analog of the spatial TTN/MERA causal cone, but arises from the **scale consistency condition** rather than from isometric tensor properties.

### How tree-geometry differs from chain-geometry (TEMPO)

**TEMPO chain (MPO):** The process tensor has a linear (MPS/MPO) geometry. Bond dimension = environment Hilbert space dimension dE. Generically gives exponentially decaying correlations (Proposition 2, App. B). The physical reason: each additional time step adds a new application of the same CPTP map Lambda on a finite environment -> spectral gap of Lambda governs correlation decay -> exponential.

**Process tree:** Binary-hyperbolic geometry (Fig. 1, 2). The environment Hilbert space grows exponentially with the number of tree scales (each new scale introduces one new environment wire per branching -> 2^(s-1) environment wires at scale s, Fig. 6). Memory is **distributed across time scales** — different temporal scales carry correlations for different delay intervals. This distributed-memory structure is what produces **polynomial correlation decay**:

For a uniform process tree, the connected two-point correlator decays as ~Delta t^{-alpha} with alpha = |log(lambda_2)| where lambda_2 = lambda_2^L * lambda_2^R is the product of sub-leading eigenvalues of the left/right transfer matrices (Theorem 1, App. D). Since the eigenvalue lies strictly inside the unit disk for generic W, the decay is polynomial in Delta t = 2^n - 1, i.e., **exponential in n (tree level) translates to polynomial in Delta t**.

Key contrast: In chain (MPO) geometry, the bond dimension is fixed -> memory capacity is fixed -> exponential decay. In tree geometry, memory dimension grows with tree height -> power-law correlations are a **structural property** of the geometry, not a fine-tuning.

### 2D TRG derivation from influence functional (Sec. VII, Fig. 9)

**This is the crucial algorithmic contribution for deriving a process tree from first principles.**

The Feynman-Vernon influence functional (IF) for a system-environment Hamiltonian can be represented exactly as a **2D tensor network** (Fig. 9i): the horizontal direction is time, the vertical direction is spatial/environment modes. Each column is a Trotterized propagator. Contracting this 2D network directly is hard (worst-case exponential).

The paper proposes a **plaquette TRG scheme**:

1. **Unit cell identification** (Fig. 9i-ii): Group 2x2 blocks of the 2D IF lattice. Each block (red dotted box) contains four contiguous IF sites.
2. **Plaquette decomposition** (Fig. 9ii): Replace each 4-site block with a **structured tensor network** — horizontal and vertical isometries (triangles) mapping environment mode pairs to an artificial bond space of dimension chi, plus a central tensor. The decomposition is found variationally (minimizing the distance to the exact unit cell, Eq. 34).
3. **Bottom row** is special: the tensor that connects to the **system indices** (open wires at the base) must be parameterized as a **superprocess** (W or Y brick). This choice determines whether the final tree is W-type or Y-type (Eq. 35).
4. **Isometry absorption** (Fig. 9iii-iv): The horizontal (pink) and vertical (yellow) isometries contract into new coarse-grained tensors (gray boxes). The lattice is now 2x reduced in both directions.
5. **Iterate** (Fig. 9v-vi): Repeat the plaquette TRG on the coarse-grained lattice. Each iteration halves the number of time steps and environment modes.
6. **Final step** (Fig. 9vii): After O(log k) iterations, the lattice reduces to a single point. The remaining concatenation of superprocesses is **exactly a process tree** (with the bottom layer carrying the system's open indices).

The computational scaling of the TRG construction is **independent of the number of time steps k** (scales only with environment dimension / bond chi), unlike direct methods (TEMPO/ACE) whose upfront cost scales with k. But the TRG optimization must be performed for each unit cell; if the IF is translationally invariant in time, one optimization suffices. The paper explicitly leaves benchmarking against TEMPO/ACE to future work.

### Non-Markovianity analysis (Sec. V)

The process tree's non-Markovianity (quantum mutual information eta, Eq. 9) decays polynomially with temporal distance Delta t (Fig. 5iii), matching the two-point correlation behavior (Fig. 5ii). This is because the built-in **causal breaks at different time scales** force correlations to route through higher-scale environment wires (Fig. 6). The memory is **distributed across all scales** — each additional tree level adds one environment wire that carries correlations at a characteristic delay.

**Entanglement in time** (Eq. 28, Fig. 5iv): For random (Haar) U1, U2, negativity decays to zero within Delta t <= 10 — typical process trees have **classical memory** only. For structured unitaries (e.g., SWAP-like), negativity decays polynomially with Delta t. The scrambling character of W determines whether the power-law correlations are quantum or classical. This is interpreted as "quantum 1/f noise" — power-law correlation that cannot be produced by a classical model.

### Spin-boson fitting results (Sec. VI)

**Setup:** Variational optimization of process tree parameters (U1, U2 unitaries) to match the PT-TEMPO-computed spin-boson process tensor (Ohmic spectral density J(omega)=2*alpha*omega*exp(-omega/omega_c), omega_c=10 ps^-1, delta t=0.1 ps). Objective: 2-fidelity F2 (Eq. 31). Optimizer: L-BFGS-B with JAX autodiff.

**Key results:**

| Result | Numbers |
|--------|---------|
| D=2 process tree vs 16-step spin-boson | F2 overlap > ~0.8-0.95 for most alpha (0.1-5), minimum at phase transition alpha_c ~ 1 (Fig. 8ii) |
| D=3, D=4 process trees | F2 > 0.95 across almost all alpha (Fig. 8iii) |
| MPO (same bond dim) vs trees | MPO has **2-60x more parameters** but lower overlap, especially near alpha_c (Fig. 8ii-iii) |
| Relaxed (Y-type) trees | Perform better than W-type, but not substantially more free params — suggests scale consistency is somewhat restrictive |
| Homogeneous tree (single W) | Generalization: fit on 8-step, build 16/32/64 step process — F2 stays surprisingly high (Fig. 8vi) |
| Observable prediction | <Z> and <X> from tree fits match PT-TEMPO reference to 10^-2 -- 10^-3 error (Fig. 8iv) |

The **phase transition** is clearly visible in the fitting quality: the minimum overlap coincides with alpha_c ~ 1 (the BKT delocalized-to-localized transition). Near the phase transition, the process tree is most "expressive" but also hardest to fit with limited bond dimension. The authors note this is the first study (to their knowledge) of non-Markovianity across the spin-boson BKT transition.

### Computational scaling

**Process tree evaluation (correlation functions):**

- **Single-time expectation value:** Requires scaling up one side of the tree. Each left/right move costs O(d^6) (contraction of the W-brick with the instrument). Total: O(N d^6) for a tree of height N (2^N time steps). **Logarithmic in the number of time steps k=2^N** => O(log(k) * d^6).
- **Two-time correlator:** Each instrument ascends independently (cost O(log(Delta_t) * d^6) each), then fuses at their LCA (one fusion move O(d^6)), then ascends combined (O(log(k/Delta_t) * d^6)). Total: O(log(k) * d^6).
- **k-time correlator:** O(k * log(k) * d^6) — each instrument independently ascends, sequential fusions.

**TRG construction (from IF):** The plaquette optimization for each unit cell scales with bond dimension chi (approximation accuracy). Number of optimization rounds = O(log(k)). Environment dimension dependent, not directly k-dependent. No explicit scaling given — benchmarking deferred.

**Contrast with MPO chain:** MPO process tensor evaluation of l-time correlators costs O(k * chi^2 * d_S^2 + ...) with chi = bond dim = environment dim. For fixed chi, cost is linear in k (vs logarithmic for tree). But tree's bond dimension per wire (d^2) is like the **environment dimension at each scale**, and memory capacity grows exponentially with height.

## Polynomially decaying temporal correlations — mechanism

The mechanism is structural, not fine-tuned. Three complementary views:

1. **Transfer matrix spectrum** (Theorem 1, App. D): The connected correlator factors as <A_t' A_t>_c ~ |lambda_2|^n where n = O(log_2(Delta t)). Since |lambda_2| < 1, the decay is exponential in n, hence polynomial in Delta t = 2^n - 1. The exponent alpha = |log(|lambda_2|)| > 0 depends on spectral properties of WR and WL (CP maps derived from W). Generically this holds for any W (not fine-tuned), because the largest eigenvalue (=1, from scale consistency) is unique under generic conditions (Frobenius-Perron/Russo-Dye theorems).

2. **Distributed memory** (Fig. 6, Sec. V): Each tree level adds environment wires that carry correlations at different time scales. Nearest-neighbor slots may be correlated via short-scale wires (low-level paths), while far-separated slots must route through high-scale wires (Fig. 6 red paths). The number of "environment hops" grows logarithmically with Delta t, giving polynomial decay.

3. **Scale-invariant RG fixed point** (Sec. VIII discussion): The spin-boson fits suggest that at the phase transition, the process tree approaches a scale-invariant fixed point (single W repeated across all scales works well). This is the dynamical analog of MERA capturing CFT critical states — the tree's hyperbolic geometry naturally accommodates scale-invariant temporal correlations.

The key structural insight: **tree geometry is the natural representation for polynomially decaying temporal correlations, just as chain geometry is natural for exponentially decaying ones.** This is the time-domain analogue of the Evenbly-Vidal result [30] connecting tensor network geometry to correlation structure.

## Potential for combining 2D spatial PEPO + process tensor for QEC

**Q5 from the brief: Does this paper suggest a path to combining 2D spatial PEPO + process tensor for QEC?**

The paper **does not address QEC or spatial tensor networks** — its focus is purely temporal (multitime correlations for a single system qubit coupled to a bath). However, there are several suggestive directions:

**Direct relevance:**
1. **The TRG plaquette scheme (Fig. 9) is inherently 2D** — it starts from a 2D IF tensor network and applies a TRG algorithm to reduce it to a process tree. This is NOT a spatial PEPO; the vertical dimension is environment modes (or bath frequency), not physical lattice sites. But the TRG machinery could, in principle, be adapted to a 2D spatial geometry if the environment were replaced by neighboring qubits.

2. The paper explicitly states "we leave the problem of explicit numerical analysis and benchmarking against the state-of-the-art numerical packages — such as ACE or TEMPO — to future work" (Sec. VII). No QEC benchmarking is done.

**The crucial obstacle for QEC:**
1. The W-brick acts on a **single system qubit** d_S = 2 (the spin in the spin-boson model). The process tree describes the multitime correlations of a *single* system qubit with its environment. Moving to a many-qubit surface code would require a process tree for each qubit PLUS spatial correlations between them — a **spatiotemporal** tensor network.

2. The "environment wires" in the process tree (Fig. 6) represent the bath degrees of freedom for a single qubit. For QEC, the "environment" includes both physical noise sources AND syndrome measurement channels. The tree geometry would need to accommodate **multi-qubit stabilizer measurements** as operations on the process tensor.

3. The process tree's efficient scaling relies on the **scale-causal cone** — only one tensor per scale contributes to a given time-local observable. For a many-qubit process, the causal cone would involve tensors for each qubit times the number of scales, negating the log(k) scaling advantage.

**Bottom line: The process tree does not directly help with the spatial (multi-qubit) PEPO problem. It solves the temporal (long-memory) problem for a single system. Combining the two requires a separate spatiotemporal ansatz — e.g., a PEPO for spatial geometry at each time step, plus a process tree for memory across time steps.**

## Can tree-geometry be "spatialized"?

**Q6 from the brief: Can we use PEPO for spatial and process tree for temporal?**

This is not addressed in the paper. However, from the paper's framework:

**In principle yes**, because:
- The process tensor formalism (Eq. 5) is spatially agnostic — the "system" HS can be multi-qubit.
- The W-brick's local dimension d can, in principle, be a product over spatial qubit spaces: d_S_total = d_S^N_qubits.
- The TRG construction (Fig. 9) already separates "system" (bottom row) from "environment" (bulk). One could replace the bottom row's single-qubit system indices with many-qubit indices (the PEPO for a surface code patch).

**In practice, the cost is prohibitive:**
- The W-brick scales as O(d^6) per contraction. With d = 2^(number of qubits), this is exponential in system size.
- The scale-causal cone is a single W per scale, but each W would act on the *entire* multiqubit system-spatial-PEPO product space.
- The environment dimension per scale (the vertical bond dim in the tree) must carry the combined memory of all qubits' baths — multiplicatively larger than single-qubit case.

**More promising alternative not in this paper:** Use a **PEPS for the spatial state** at each time step, coupled through a **temporal MPS/process tensor** for the sequence of time steps, with the environment-induced correlations between time steps compressed by the process tree. This is a "2D+1D" architecture (spatial PEPS x time process tree). The Dowling paper does not explore this — it would be a new contribution.

## Relevance to pseudomode-on-2D-iPEPO architecture

**Q8 from the brief: Does the process tree offer an alternative to our pseudomode-on-2D-iPEPO architecture?**

**Direct alternatives:**

1. **Process tree as temporal carrier** (replacing TEMPO/TEDOPA): The process tree is more efficient than MPO/TEMPO for processes with **power-law (slow) memory decay**. If a QEC code's noise environment exhibits 1/f noise or slow TLS relaxation, the process tree could represent the temporal correlations of the noise with exponentially fewer parameters than an MPO process tensor. This directly helps the **temporal axis** of our problem.

2. **Process tree + PEPS** (not in paper, but natural extension): The process tree handles **time** (bath memory), PEPS handles **space** (2D lattice). This is a distinct architecture from pseudomode-on-iPEPO. The process tree replaces explicit pseudomodes with a hierarchical decomposition of memory across time scales. The pseudomode approach explicitly discretizes the bath spectral density; the process tree learns the effective memory structure from data or from a Hamiltonian.

3. **Where process tree helps:** If our non-Markovian QEC problem is dominated by **temporal correlations that span many time steps** (e.g., 1/f noise with correlation times >> a single syndrome extraction cycle), the process tree's O(log k) evaluation cost is exponentially better than MPO's O(k). This is exactly the regime where pseudomode discretization would require many modes, driving up the bond dimension of the carrier.

4. **Where process tree does NOT help:** The spatial (2D lattice) aspect. The process tree is inherently a **single-system** temporal object. Extending it to 2D many-qubit systems requires cross-qubit spatial correlations to be handled some other way (e.g., embedding multiple process trees with cross-bonds, or using a PEPS for the system and a process tree for each independent noise source). The paper provides no guidance on this.

5. **Comparison with pseudomode-on-iPEPO:**
   - **Pseudomode approach:** Discretize bath spectral density into a fixed number of Markovian pseudomodes. Spatial correlations from shared/common baths are handled by coupling multiple physical qubits to the same pseudomodes. Temporal correlations of each noise source are captured by the pseudomode dynamics (autonomous Markovian). **Strength:** handles both spatial and temporal correlations; **weakness:** number of pseudomodes grows with required spectral resolution.
   - **Process tree approach:** Non-Markovian temporal correlations handled hierarchically (tree geometry). **Strength:** exponential efficiency for long-memory processes; **weakness:** no built-in spatial correlation handling — extending to 2D requires additional structure.

6. **Could process tree replace pseudomodes?** Partially. The process tree is a **different representation of the same physics** — the environment's effect on the system is captured by the tree tensors rather than explicit pseudomode states. The equivalence is through the process tensor: both pseudomodes and the process tree represent the same multitime map, just with different internal structures. The choice depends on:
   - **Memory structure:** If memory decays roughly as a sum of exponentials (Lorentzian spectrum) -> pseudomodes are natural. If memory decays as a power law (1/f noise) -> process tree is exponentially more efficient.
   - **Spatial correlations:** If noise is primarily independent per qubit -> process tree per qubit + PEPS for spatial coupling is plausible. If noise is strongly correlated across qubits (shared bath, crosstalk) -> pseudomodes handle this more naturally (shared pseudomodes couple qubits).

**Verdict: The process tree is not a direct replacement for our pseudomode-on-2D-iPEPO architecture, but it offers a potentially superior alternative for the temporal (bath-memory) axis, especially for power-law noise spectra. The open problem is extending it to handle spatial correlations across a 2D many-qubit system — the paper does not address this, and solving it would be a new contribution.**

## Limitations [paper]

- **Single-qubit system only.** The process tree is constructed for a single system qubit. Extension to multi-qubit systems is asserted to be "straightforward" (the system dimension d can be increased) but the scaling implications (exponential in number of qubits) are not discussed. The spin-boson experiments use d_S = 2.
- **No numerical benchmark of the TRG construction.** Sec. VII sketches the TRG scheme but provides **no numerical results** — no comparison with TEMPO/ACE, no accuracy metrics, no runtime. The paper acknowledges this: "leave the problem of explicit numerical analysis and benchmarking against state-of-the-art numerical packages ... to future work."
- **W-type trees are restrictive.** The relaxed (Y-type) trees perform better in spin-boson fitting (Fig. 8ii-iii) despite similar parameter counts. This suggests scale consistency (Eq. 16) may not hold for some physical processes. The Y-type trees lack the efficient causal-cone contraction properties.
- **Generalization results are preliminary.** The impressive generalization (8-step fit -> 64-step prediction, Fig. 8vi) is only shown for the scale-time-homogeneous tree. It's unclear whether this would work for systems without approximate scale invariance.
- **No causal break in observables.** The spin-boson fits are validated via F2 overlap and <Z>/<X> predictions — these are not causal-break measures like the non-Markovianity eta. The process tree might fit the multitime statistics well but poorly capture the non-Markovianity.
- **No QEC demonstration.** Zero overlap with quantum error correction. The paper's relevance to QEC is entirely indirect (memory structure in environmental noise).
- **Exact pretraining cost.** The variational fitting (Sec. VI) requires access to the target process tensor (computed via PT-TEMPO, which scales with k). This makes the fitting method inefficient for large k — it's a proof of principle, not a practical algorithm for long-time simulation.

## Relevance to qec_twin [ours]

1. **Structural correlation type for QEC noise:** The paper establishes that **tree geometry** (not just chain/MPO) is the natural representation for polynomially decaying temporal correlations. For our QEC twin, this is directly relevant if the hardware noise environment (Google XZZX surface code) exhibits power-law noise spectra (1/f flux noise, TLS relaxation cascades). The process tree provides a compressed representation for such memory — O(log k) instead of O(k) evaluation cost.

2. **Alternative to MPS/MPO process tensors in non-Markovian coupling simulator:** Our coupling simulator currently uses explicit pseudomodes (finite-state bath representations). The process tree offers an alternative: fit a process tree to the noise's influence functional (via the TRG scheme, once implemented), and evaluate multitime correlations with exponential speedup relative to MPO-PT for long-memory processes.

3. **Temporal renormalization group:** The scale-consistency condition (Eq. 16) defines a temporal RG flow. The paper's spin-boson results (scale-time-homogeneous tree fitting the BKT transition) hint at a **fixed point** at the phase transition — this is the time-domain analog of MERA capturing CFT criticality. For our twin, temporal RG could provide a systematic way to coarse-grain noise processes — identifying which noise frequencies "matter" at which temporal scales in the QEC circuit.

4. **What the paper DOES NOT provide for our twin:**
   - No multi-qubit / spatial correlation mechanism
   - No QEC-specific construction (syndrome measurements as process tensor operations)
   - No numerical TRG implementation
   - No connection to 2D PEPS/iPEPO carriers
   - The scale-consistency condition may be too restrictive for real noise

5. **Verdict for our architecture:** The process tree is a **promising but incomplete** alternative for the **temporal axis** of our non-Markovian coupling problem. The key open problem the paper does not address is **spatiotemporal integration**: how to combine the tree's temporal efficiency with a 2D spatial (iPEPO) representation of a surface-code logical qubit. Solving this would be a novel contribution. For now, the process tree's primary value to our project is:
   - A mathematical language for temporal correlations across time scales
   - A potential alternative to TEMPO/ACE for computing process tensors of long-memory noise
   - A theoretical framework (temporal RG) that may guide our understanding of noise scale-dependence in QEC

## The CRUCIAL QUESTION: path to 2D spatial PEPO + process tensor for QEC?

**Direct answer from the paper: No.** The paper does not address this combination. The paper is single-qubit temporal theory.

**Indirect answer (extrapolating from the paper's framework):**

The paper's TRG construction (Sec. VII) is the most promising bridge. The 2D IF tensor network (Fig. 9i) has:
- **Horizontal axis:** time
- **Vertical axis:** environment modes

If one replaces the vertical axis (environment modes) with **spatial lattice sites** of a QEC code, the 2D network becomes:
- **Horizontal:** time (rounds of syndrome extraction)
- **Vertical:** spatial position (data qubits of the surface code)

The plaquette TRG scheme would then coarse-grain **spatiotemporal plaquettes** — blocks of neighboring qubits at neighboring times. This is exactly the **spatiotemporal tensor network** that has been explored in the tensor-network QEC literature (e.g., hyperbolic MERA for surface codes, or the Bravyi-Suchara-Vargo MLD). The process tree's bottom row (system indices) would correspond to the **syndrome measurement records** or **logical qubit observable** at all times.

**Concrete possibility:** The process tree + PEPS combination could work if:
1. Each spatial PEPS layer represents the surface code state at one time step.
2. The process tree's "system" is the **logical subspace** of the code, and the "environment" includes both physical noise and syndrome outcomes.
3. The W-bricks act on the logical subspace, encoding the cumulative effect of noise over multiple rounds.

**But this is speculative — the paper does not address this, and it would require substantial new theoretical development.**

## Key equations from the paper relevant to our work

1. **Scale consistency condition** (Eq. 16): the defining constraint for W-type trees. Determines whether the causal cone in the scale direction collapses to O(N) tensors.
2. **W-brick definition** (Eq. 17): the parameterized building block. 3 CPTP maps constructed from 2 unitaries + 1 density matrix.
3. **Transfer matrices WR, WL** (Eq. 22, D3): the elementary "right/left descending moves" that propagate instruments up the tree. Their spectrum governs correlation decay.
4. **Correlation decay rate** (Theorem 1, Eq. 23-26): <A'_tn A_t0>_c ~ Delta t^{-alpha} with alpha = |log(|lambda_2^L * lambda_2^R|)|.
5. **2D IF to process tree TRG** (Fig. 9, Eq. 34-35): the plaquette optimization scheme that yields a process tree from a Hamiltonian.

## 6-criterion methodology table

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| **Soundness** | 4 | Mathematical construction is rigorous (causality conditions, CPTP maps, Theorem 1 proof in App. D). The spin-boson fits use established PT-TEMPO as reference. The process tree is well-defined as a class of processes. Weakness: no numerical validation of the TRG construction (Sec. VII is entirely theoretical). |
| **Novelty** | 5 | The process tree is a genuinely new tensor network ansatz for multitime processes. The connection between tree geometry and polynomial memory decay is novel and clearly demonstrated. The temporal RG analog (scale consistency as an RG condition) is a significant conceptual contribution. |
| **Reproducibility** | 4 | All methods are specified in detail (parameterizations, optimization, TRG scheme). Code uses OQuPy (publicly available), JAX, quimb, ncon. But: the actual fitting code is not provided as an ancillary file or repository link. The numerical experiments (Fig. 5, 8) use random seeds — reproducibility of exact figures depends on code release. |
| **Experimental design** | 4 | Clear research arc: construct class (Sec. III), prove properties (Sec. IV-V), fit physical model (Sec. VI), construct from Hamiltonian (Sec. VII). The spin-boson model is an excellent benchmark (well-studied, known phase transition, established polynomial memory). Weakness: only one physical model tested. No comparison with alternative long-memory representations (e.g., ACE, TEDOPA with many modes). |
| **Statistical rigor** | 3 | The Haar-averaged correlation functions (Fig. 5) are shown as individual runs + averages — appropriate. The fitting results (Fig. 8) show best-overlap from multiple random seeds — but no error bars or distribution over seeds. No discussion of optimizer convergence or landscape properties. |
| **Scalability** | 4 | Clear analytic scaling: O(Nd^6) for 1-time observables (N = tree height, d = bond dim). Contrast with MPO O(k) is explicit. The log(k) scaling for the tree is a major advantage. Unclear: scaling with physical system size (d_S growing beyond 2). The TRG construction's scaling is not analyzed numerically. For our QEC application (d = 2^n_qubits), the O(d^6) factor is prohibitive without further structure. |

## Strengths (S1-S4)

**S1 — Structure-function mapping in tensor network geometry.** The paper's central contribution is forging a clear link: **tree geometry -> polynomial temporal correlations**. This is the time-domain analog of Evenbly-Vidal's spatial result and is proven analytically (Theorem 1). This is a genuine structural insight, not a numerical observation.

**S2 — Scale consistency = temporal RG condition.** The paper shows that imposing Eq. 16 makes the process tree interpretable as a **temporal RG flow** — at each scale, identity instruments coarse-grain to identity. This is not just a computational trick; it may define universality classes for quantum dynamics, analogous to MERA for critical ground states (discussed in Sec. VIII, citing spatial holographic duals [96,97]).

**S3 — Explicit outperformance of MPO.** Fig. 8ii-iii directly compare process trees (D=2,3,4) against a same-bond-dimension MPO: the MPO has 2-60x more free parameters but achieves lower F2 overlap, especially near the phase transition. This is the paper's headline "the ansatz beats the standard approach" result and is clearly presented.

**S4 — Generalization from small to large.** The scale-time-homogeneous tree fitted on 8 steps generalizing to 64 steps (Fig. 8vi) is a striking result. It suggests the process tree captures **scale-invariant features** of the dynamics — a temporal analog of a CFT fixed point. If this holds generally, it would mean process trees can **predict long-time dynamics from short-time measurements**, which has direct relevance for QEC noise characterization (learning noise on short timescales and predicting multi-round decoding behavior).

## Weaknesses (W1-W4)

**W1 — TRG construction is a sketch, not an algorithm.** Sec. VII provides the idea and diagrams but no implementation, no numerical results, no benchmarks, no convergence analysis, no accuracy guarantees. The paper acknowledges this, but it means the claimed "systematic construction from an underlying Hamiltonian" is unverified. The variational unit-cell optimization (Eq. 34) is described as "not obvious how to analytically construct" — this is the hard part, and it's defered to unspecified future work.

**W2 — Single-system limitation.** All numerical results are for d_S = 2 (one qubit). The paper asserts the generalization to larger d_S is conceptually straightforward (increase the system dimension in the W-brick), but this is a non-trivial scaling claim. The contraction cost scales as O(d_S^6) per W-brick operation. For a surface-code-sized system (d_S = 2^(O(d)), this is exponential. No discussion of how to factorize the many-qubit system across the tree.

**W3 — No spatial or multi-qubit structure.** The paper is entirely about temporal correlations of a single system with a bath. For QEC, the central challenge is the **combination** of spatial (multi-qubit) and temporal (multi-round) correlations. The paper does not contribute to the spatial side. Even the connection to 2D TRG (Sec. VII) uses the vertical axis for environment modes, not spatial lattice sites.

**W4 — Y-type trees are less efficient but more accurate.** The relaxed fit (Y-type, without scale consistency) outperforms W-type for the spin-boson model (Fig. 8ii-iii). But Y-type trees lack the causal-cone structure that gives W-type trees their O(log k) efficiency. The paper does not quantify this tradeoff or provide guidelines for when W-type vs Y-type is appropriate. If real physical processes require Y-type, the efficiency advantage is lost.

## Open questions for our twin

1. Can the process tree's TRG construction (Fig. 9) be adapted to produce a **process tree for a multiqubit system**? The vertical resolution would need to be spatial dimension, not just bath modes. This is not in the paper but is the natural spatiotemporal extension.

2. Does the process tree's polynomial memory decay hold for **stabilizer measurements as instruments**? The paper's instruments are general CP maps. Applying the process tree to QEC would mean the instruments are syndrome measurements (POVMs) and conditional feedback. The process tree framework supports this in principle, but the scaling analysis would need to account for the measurement backaction bond dimension.

3. Can a process tree be **learned from experimental data** (like quantum process tomography of the QEC process)? The paper fits to a numerically computed PT-TEMPO reference. Experimental process tensor tomography [White et al. 2022] could in principle provide the target for fitting. This would give a direct experimental probe of QEC memory structure — but the scaling of PT tomography (exponential in number of time steps) is prohibitive for QEC-scale experiments without further compression.

4. What is the **physical interpretation of the W-brick unitaries** for a QEC noise process? For the spin-boson model, U1 and U2 parameterize the system-bath interaction. For QEC noise, these would encode the effect of a single noise source over one time step, including the interplay with the system Hamiltonian (gate operations). Can we connect the process tree parameters to physical noise parameters (T1, T2, 1/f amplitude, TLS densities)?

5. **Does the process tree offer any advantage for the short-memory regime?** Most QEC noise models assume relatively short bath memory (Markovian or near-Markovian). The process tree's primary advantage is for **long-memory** processes. For short-memory noise, the MPO/chain representation is adequate and simpler. The process tree is overkill unless the noise has power-law spectral features.
