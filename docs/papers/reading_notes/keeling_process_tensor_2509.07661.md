# Full-text review (targeted 精读) — Keeling, Stoudenmire, Banuls, Reichman, "Process Tensor Approaches to Non-Markovian Quantum Dynamics" (arXiv:2509.07661, PRX 16, 020502, 2026)

> **Provenance (2026-07-02): FULL-TEXT 精读.** Fetched from arXiv HTML (2509.07661v1). Physical Review X 16, 020502 (2026), published 22 June 2026. DOI: 10.1103/1ncg-11hz. This invited Perspective reviews the process tensor framework combined with tensor-network methods for numerically exact non-Markovian quantum dynamics.

## Metadata [paper]
- Authors / affiliation: Jonathan Keeling (U. St Andrews), E. Miles Stoudenmire (Flatiron Institute/CCQ), Mari-Carmen Banuls (MPQ Garching / MCQST), David R. Reichman (Columbia U. Chemistry).
- Venue / status: PRX 16, 020502 (2026). arXiv:2509.07661 (September 2025; earlier version arXiv:2412.17862). Invited Perspective.
- Type: Comprehensive review/perspective on process tensor + tensor-network methods for non-Markovian open quantum systems.

## Executive summary [paper]
The review argues that the process tensor (PT) formalism, combined with efficient tensor-network representations (MPS/MPO), provides a unified framework for numerically exact simulation of non-Markovian quantum dynamics. It covers the core formalism (Section II), demonstrates how the PT unifies previously distinct methods — chain mappings (TEDOPA, NRG), hierarchical equations of motion (HEOM), hierarchy of pure states (HOPS), generalized quantum master equations (GQME, transfer tensors), and path-integral (QuAPI) approaches (Section III) — compares software packages (Table 1), and discusses applications and future directions. The PT is presented as a "Rosetta stone" for non-Markovian methods. The central technical advance is that tensor-network compression of the process tensor (PT-MPO) enables simulations at memory times and system sizes previously intractable.

## Method (deep) [paper]

**Process tensor definition (Section II.1):** A multilinear map from operations on a quantum system to its final state. Generalizes to state preparation, measurement, and arbitrary gates — not just Hamiltonian evolution. The construction: system-environment evolution is Trotterized into layers; the environment is traced out, leaving a tensor network of system-only evolution operators and environment-influence tensors (Fig. 3). This object "isolates the evolution of the bath from the possible interventions on the system, which can then be varied."

**Gaussian bosonic environments (Section II.2.1):** For bosonic baths with coupling H_SE = O_S sum_k (g_k a_k^dag + g_k^* a_k), the process tensor has a closed form:
F^{alpha_1 ... alpha_n} = prod_{1 <= j <= i <= n} b_{i-j}(alpha_i, alpha_j)
where the factors b_k(alpha, beta) depend on the bath correlation function integrated over time windows. **All higher-order cumulants vanish for Gaussian statistics** — only two-time correlations matter. This is the same Gaussian property leveraged in the Feynman-Vernon influence functional.

**Tensor network representations:**
- **MPS form** (diagonal coupling): When the system operator O_S commutes with the system Hamiltonian (or in the diagonal basis), the process tensor becomes an MPS — "each time step captured by a three-index tensor" (Fig. 3d).
- **MPO form** (general coupling, Section II.2): "Each time step has a four-index tensor, with two indices into the system Hilbert space (input and output indices), and each tensor connected to others by a bond index of moderate size chi." This is the PT-MPO (process tensor matrix product operator).
- **Bond dimension interpretation:** "The bond dimension can be understood as the smallest effective dimension of the environment required to capture its effect on the evolution of the system." The PT-MPO bond dimension is thus a quantitative measure of non-Markovian memory.

**PT-MPO computation algorithms (Section II.2, Section IV):**
1. **iTEBD for bosonic baths (Section II.2.1):** Reinterprets the Gaussian process tensor as a shallow, infinitely-wide quantum circuit of non-unitary gates, compressed via iTEBD to an infinite MPS. Complexity O(N_m log N_m) where N_m is memory depth.
2. **Fishman-White for fermionic baths (Section II.2.2):** Constructs MPS from the Hartree-Fock-Bogoliubov wavefunction (exp[c^dag_i M_{ik} c^dag_k]|0>) via iterative diagonalization of the 2N x 2N correlation matrix. The MPS has area-law entanglement when the influence functional's autocorrelation function decays sufficiently rapidly.
3. **Sequential algorithm** (Ref. [71]): O(N K) with memory truncation after K steps.
4. **Divide-and-conquer** (Ref. [69]): An alternative contraction scheme.
5. **Transverse contraction (Section III.1):** Applied to chain-mapped systems: process tensor MPO extracted by contracting the bath chain along the spatial rather than temporal direction.
6. **TTI-PT** (time-translation invariant, Ref. [68]): Exploits translational invariance to express the process tensor via a single unique tensor plus boundaries.

**Unification of methods (Section III):**
- **Chain mappings + TEDOPA (Section III.1):** Lanczos tridiagonalization of the star Hamiltonian into a chain where the system couples only to the first site. The process tensor is then obtained by "transverse contraction" along the chain.
- **HEOM (Section III.2):** The hierarchy of auxiliary density operators corresponds to "a set of M auxiliary bosonic modes {n_k}" — each auxiliary index represents a term in the decomposition alpha(t) ≈ sum_j alpha_j e^{nu_j t} of the bath correlation function. The bond dimension chi of the PT-MPO is "upper bounded by the dimension of this site containing all auxiliary modes."
- **HOPS (Section III.3):** Non-linear stochastic Schrodinger equation, each trajectory corresponding to a stochastic process tensor.
- **GQME / transfer tensors (Section III.4):** T_{n,k} provides a discrete representation where rho(t_n) = E_n rho(0) = sum_{k=0}^{n-1} T_{n,k} rho(t_k) — interpretable as discrete Nakajima-Zwanzig equation.

## The noise model [paper -> ours]
The PT framework naturally handles **non-Markovian, continuous Gaussian environments** (bosonic/fermionic) — the primary noise sources in solid-state qubits (charge noise, flux noise, phonon baths). Key relationships to our coupling simulator:

1. **Pseudomode connection:** The HEOM decomposition alpha(t) ≈ sum_j alpha_j e^{nu_j t} is exactly the pseudomode decomposition: each exponential term corresponds to a Lorentzian spectral density peak represented by a damped harmonic oscillator (pseudomode). The PT-MPO bond dimension bound from HEOM (chi <= dimension of auxiliary subspace) mirrors our pseudomode bond dimension scaling.

2. **Memory quantification:** The PT-MPO bond dimension chi as "the smallest effective dimension of the environment" is a rigorous measure of non-Markovianity — directly relevant to our need to bound the bond dimension cost of pseudomode coupling.

3. **Multi-time correlations:** The process tensor formalism naturally encodes multi-time correlations (Eq. 2: b_{i-j} factors for all pairs of time steps). For QEC, syndrome statistics are multi-time measurements — the PT framework could in principle provide exact detector correlation formulas beyond the Markovian Spitz formulas. This is a potential bridge between our gauge analysis and open-quantum-system theory.

4. **Gaussian noise specialization:** The closed-form process tensor for Gaussian environments (factorization into pairwise terms) is the same mathematical structure that makes Gaussian quantum noise tractable in our setting. This is why classical Gaussian noise (1/f, quasi-static) can be efficiently simulated — the pairwise factorization avoids exponential scaling in the number of time steps.

## Gauge / identifiability [paper -> ours]
**Not discussed in the paper.** However, the process tensor formalism inherently suggests a gauge structure worth exploring:

- The PT-MPO has a gauge freedom: bond-dimension transformations U chi^{-1} ... chi U^dag preserve the physical process tensor while changing the internal representation. This is analogous to our gauge theorem's freedom in channel parameterization.
- The PT bond dimension chi as "the smallest effective environment dimension" has a similar connotation to our probe richness R — both quantify the complexity needed to capture the noise. If R is the minimal number of probe settings needed to break identifiability degeneracies, chi is the minimal environment dimension needed to capture non-Markovian memory. The two may be related through probe-state distinguishability bounds.

For our project, this suggests a research direction: **Using the PT-MPO bond dimension as a rigorous upper bound on the identifiability gap** — if the environment has effective dimension chi, then probe richness R >= chi is necessary (but may not be sufficient) to break gauge degeneracies.

## Software packages (Table 1) [paper]
| Package | Algorithm | Key feature |
|---|---|---|
| OQuPy | PT-MPO | Bosonic baths; mean-field & chain extensions |
| ACE | Automated Compression of Environments | General non-Gaussian (uncoupled) baths |
| PathSum | QuAPI/MPI/SMatPI | Iterative path integral methods |
| QuantumDynamics.jl | General IF | Tensor-network IF + QuAPI |
| MPSDynamics | T-TEDOPA | Thermalized MPS-based TEDOPA |
| HEOM-QUICK | HEOM | Fermionic impurity problems |
| HierarchicalEOM.jl | HEOM | Bosonic and/or fermionic baths |
| MPSQD | MPS-HEOM | Direct MPS/MPO functionality |
| Heidelberg MCTDH | ML-MCTDH | Tree tensor network wavefunction |
| pyTTN | TTN | Tree tensor networks |
| MesoHops | HOPS | Adaptive HOPS |

**For our project:** OQuPy and ACE are the most relevant — OQuPy for bosonic PT-MPO (directly applicable to our charge/flux noise models), ACE for non-Gaussian environments (potential leakage bath models).

## Limitations [paper]
- **Single-system focus:** The examples are single-impurity problems (spin-boson, Anderson impurity). Multi-qubit systems with spatial noise correlations are not treated — the bottleneck of our coupling simulator.
- **No QEC context:** Zero discussion of stabilizer codes, syndrome extraction, or decoding. The PT formalism's potential for QEC syndrome statistics is unexplored in this review.
- **Gaussian bias:** The tractable closed-form process tensor for Gaussian environments may create a selection bias — the paper's examples lean heavily on Gaussian baths.
- **Computational scaling:** For multi-time correlations, "once the process tensor has been constructed, it will still take approximately N^m independent contractions to extract m-time correlators." The upfront cost vs. output cost tradeoff favors the PT only when m > 2 (without truncation) or m > 1 (with truncation). For binary detector statistics (m = 2), the benefit is marginal.
- **No identifiability analysis:** The PT helps characterize environment complexity but does not address whether system-observable-level identification of the PT suffices for predicting system response to arbitrary interventions.

## Relevance to AI_QEC [ours]
**High relevance** as the theoretical foundation linking our noise model to tensor-network methods:

1. **PT-MPO as our Lindbladian MPO:** The vectorized Lindbladian (Liouvillian superoperator) in our coupling simulator is a specific case of a process tensor MPO for Markovian dynamics. Extending it to non-Markovian pseudomodes corresponds to increasing the bond dimension (augmenting the PT-MPO with hidden memory degrees of freedom). The PT-MPO bond dimension offers a direct measure of the computational cost of our approach.

2. **Bath correlation function decomposition:** The HEOM/pseudomode connection (Section III.2) provides the mathematical bridge between our bath spectral density J(omega) and the pseudomode frequencies/number. This is the formal justification for the pseudomode decomposition in our coupling simulator.

3. **Memory quantification:** The PT-MPO bond dimension as the effective environment dimension gives a rigorous target: if our noise requires chi_mem effective dimensions, we need at least that many pseudomode states. This directly bounds the feasibility of our MPS carrier.

4. **Gaussian noise simplification:** The closed-form factorization of Gaussian process tensors (Eq. 2: F = prod b_{i-j}) explains why classical Gaussian noise (SpinPulse) is tractable: the pairwise factorization avoids exponential blowup. This justifies our current approach of modeling classical noise sources (1/f flux noise) as classical random fields rather than quantum pseudomodes — but also tells us where the quantum pseudomode treatment is essential (non-Gaussian noise, back-action).

5. **Multi-time detector correlations:** The PT framework could provide exact, fully quantum formulas for detector statistics in non-Markovian noise — a potential replacement for the Markovian Spitz formulas when memory effects are important. This would directly feed into our calibration and gauge analysis.

## How to use / trust + open questions [ours]
Trust level: **very high**. PRX invited Perspective, authored by leading practitioners (Keeling: PT pioneer; Stoudenmire: ITensor lead; Banuls: tensor-network methods; Reichman: quantum dynamics). The review is comprehensive and pedagogical.

**Open questions for our project:**
- How does the PT-MPO bond dimension chi relate to our probe-richness parameter R for identifiability? Is chi <= R a necessary condition for complete identifiability?
- Can we derive detector correlation formulas (replacing Spitz) from the Gaussian process tensor with memory? If yes, this would directly extend our calibration to non-Markovian noise.
- The transverse contraction method (Section III.1, Fig. 7c) for obtaining the PT-MPO from chain-mapped environments: can this be adapted to our surface-code grid with pseudomode couplings? The chain mapping would need to incorporate the 2D code structure.
- For our MPS carrier, should we implement the PT-MPO (via OQuPy-like methods) or continue with the direct W^II Lindbladian evolution? The PT-MPO approach would be more flexible (handle arbitrary time-dependent system Hamiltonians without recomputing the influence) but may have higher upfront cost.
- The paper notes that for m <= 2 correlators the PT may not provide a computational advantage. Since we mainly care about single-detector and two-detector statistics, this suggests a simpler approach (sliding-window Spitz formulas + non-Markovian corrections) may be more practical.
