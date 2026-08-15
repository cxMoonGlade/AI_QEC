# Full-text review — Keeling et al., "Process Tensor Approaches to Non-Markovian Quantum Dynamics" (arXiv:2509.07661 / PRX 16, 020502)

> **Provenance (2026-07-03): FULL-TEXT 精读.** Fetched from arXiv HTML (2509.07661v1) and PRX abstract (10.1103/1ncg-11hz). **Invited Perspective** published in Physical Review X 16, 020502 (June 2026). A landmark review unifying the process tensor formalism across non-Markovian open quantum system methods. Authors: Keeling (St Andrews), Stoudenmire (Flatiron/CCQ), Banuls (MPQ Garching/MCQST), Reichman (Columbia).

## Metadata [paper]
- **Authors / affiliation:** Jonathan Keeling (SUPA, St Andrews), E. Miles Stoudenmire (CCQ Flatiron Institute, NYC), Mari-Carmen Banuls (Max-Planck-Institut fur Quantenoptik / MCQST), David R. Reichman (Columbia University, Chemistry).
- **Venue / status:** Physical Review X 16, 020502 — Published 22 June 2026. This is a **Perspective** (invited review/roadmap), not a research article. arXiv:2509.07661 (quant-ph), September 2025.
- **Type:** Comprehensive review/tutorial — process tensor formalism as a unifying framework for non-Markovian open quantum system simulation.

## Executive summary [paper]

This PRX Perspective establishes the **process tensor** (PT) as a unifying mathematical object for non-Markovian open quantum system dynamics. The process tensor is a multilinear map from a sequence of operations on a quantum system to its final state — it encodes all multi-time correlations between system and environment without requiring explicit bath simulation. The central thesis is that coupling the process tensor formalism with efficient **tensor-network compression** (MPS/MPO representations) makes practical a wide range of non-Markovian problems that were previously intractable.

The paper provides a comprehensive taxonomy of non-Markovian methods classified by their explicit or implicit construction of the process tensor:

1. **Chain mappings** (TEDOPA, NRG) — transform the star-shaped system-bath model into a 1D chain treatable by MPS/TEBD
2. **Hierarchical Equations of Motion (HEOM)** — expand the bath autocorrelation into exponentials; auxiliary operators form a hidden tensor structure
3. **Hierarchy of Pure States (HOPS)** — trajectory-based non-Markovian quantum state diffusion
4. **Generalized Quantum Master Equations (GQME / Nakajima-Zwanzig)** — memory kernel connecting past and present
5. **Path integral methods** (QuAPI, SMatPI, MPI) — influence functional approaches

The process tensor is shown to be the **Rosetta stone** connecting all these methods: each is revealed as a particular way of constructing or approximating the same PT-MPO. The **time-translation-invariant (TTI) PT** construction (Refs. [68,69]) is highlighted as particularly efficient, reducing the upfront construction cost from O(N²) to O(N log N) by exploiting stationarity.

A software survey (Table 1) catalogs 13 publicly available packages spanning PT-MPO (OQuPy, ACE), HEOM (HEOM-QUICK, HierarchicalEOM.jl, MPSQD), path integral (PathSum, QuantumDynamics.jl), TEDOPA (MPSDynamics), HOPS (MesoHops), MCTDH, and general-purpose TN codes (Quantics, RENORMALIZER, pyTTN).

## Method (deep) [paper]

**Process tensor definition (Section II):** The process tensor F is a multilinear map from operations to final state. For N timesteps with system operations O_n between timesteps:

F scales as exp(O(N)) for a dense representation, but the environment's finite memory makes it compressible. The connection to **Hidden Markov Models** is explicit: the tensor-network decomposition of the PT defines "an effective set of hidden quantum degrees of freedom" such that system + hidden evolution becomes Markovian.

Two key computational approaches are detailed:

**1. TTI-PT for Gaussian bosonic environments (Section II.2.1):** For a system coupled via diagonal operator O_S = Σ λ_s |s⟩⟨s| to a free bosonic bath, the exact PT factorizes:

F^(α₁...α_n) = ∏_{1≤j≤i≤n} b_{i-j}(α_i, α_j)

where b factors are exponentials of environment correlation integrals η_{i-j} that decay asymptotically ∝ C(Δt·|i−j|). A finite memory window N_m sets b_k ≈ 1 for k > N_m. The infinite-time PT can be reinterpreted as a shallow quantum circuit and converted to MPS via **iTEBD** (Fig. 5), scaling as O(N_m log N_m) — a dramatic improvement over O(N²) sequential construction.

**2. Free fermionic environments (Section II.2.2):** The fermionic influence functional uses Grassmann numbers and maps to a **Hartree-Fock-Bogoliubov (HFB) wavefunction** exp(c†_i M_ik c†_k)|0⟩ via the **Fishman-White algorithm** — iterative diagonalization of the 2N×2N correlation matrix with nearest-neighbor unitary transformations. With bounded orbital extent ℓ, bipartite entanglement does not grow extensively with N.

**Methods unification (Section III):**

- **Chain mappings (III.1):** Lanczos tridiagonalization transforms the star model into a 1D chain. The Trotterized evolution yields U(t=MΔ) ≈ (e^{-iH_S Δ} e^{-i(H_{SB}+H_B)Δ})^M (Eq. 4). The **temporal entanglement** concept is introduced — entanglement of the boundary vector in the time direction — and the method excels when temporal entanglement grows slower than spatial entanglement.
- **HEOM (III.2):** Bath autocorrelation α(t) ≈ Σ α_j e^{ν_j t}. Auxiliary density operators ρ_𝐧 evolve via Eq. 5. The auxiliary indices correspond to bosonic modes in the PT-MPO representation; the PT-MPO bond dimension is bounded by the number of HEOM auxiliary operators.
- **HOPS (III.3):** Quantum trajectory approach from the Feynman-Vernon path integral, producing a non-Markovian quantum state diffusion equation with auxiliary states.
- **GQME (III.4):** Nakajima-Zwanzig memory kernel ρ̇(t) = -iℒρ(t) + ∫₀ᵗ dτ K(t−τ)ρ(τ) (Eq. 6). Transfer tensors T_{n,k} (Eq. 7) connect to the process tensor formulation. QuAPI and SMatPI decompose the evolution operator ℰ_n into time-correlation matrices M^{nm} (Eq. 8).

**Benchmarking proposal (Section IV):** The **sub-Ohmic spin-boson model** (J(ω) = A ω^s Θ(ω, ω_c) with s < 1) is recommended as the most challenging simple benchmark, featuring zero-temperature localization critical points and prominent non-Markovian dynamics.

## Results [paper]

This is a Perspective/review paper, so there are no new empirical results. Key synthetic contributions:

- **Table 1:** Comprehensive catalog of 13 publicly available non-Markovian software packages with their algorithmic basis.
- **Fig. 6:** Scaling comparison of three PT construction approaches (sequential, divide-and-conquer, TTI-PT) for computing a quantum dot fluorescence spectrum, showing TTI-PT achieves near-linear scaling.
- **The quantitative efficiency claim:** PT upfront construction costs scale as O(N K) with memory truncation or O(N²) without (assuming bond dimension saturates). The PT becomes more efficient than direct simulation when m > 2 (no truncation) or m > 1 (with truncation) for m-time correlations. The TTI-PT approach can theoretically compute any correlation in constant time using its eigenspectrum.

## Contributions (claim -> evidence -> strength) [paper]

| Contribution | Evidence | Strength |
|--------------|----------|----------|
| Process tensor unifies all major non-Markovian OQS methods | Sections III.1-III.4 mapping each method to PT-MPO representation; connection to hidden quantum degrees of freedom | Strong — conceptually demonstrated, supported by Ref. [86] unified discussion. This is the Perspective's central thesis and is convincing though not a formal theorem. |
| TTI-PT enables linear-time PT construction via shallow-circuit + iTEBD | Section II.2.1, Fig. 5-6; Refs. [68,69]. O(N_m log N_m) scaling for diagonal coupling | Strong — methodologically established; scaling analysis shown in Fig. 6. |
| Free fermionic environments admit efficient MPS representation via Fishman-White algorithm | Section II.2.2; bath autocorrelation decay controls entanglement growth | Moderate — depends on rapid autocorrelation decay; not universal but well-justified. |
| PT framework enables reusability across time-dependent fields, control, self-consistent fields | Section V: four use cases (spectroscopy, control, mean-field, multi-time correlations) | Moderate — applications referenced from literature; each has been demonstrated separately. |

## Relevance to AI_QEC [ours]

**Process tensors and the twin's non-Markovian coupling simulator:**

1. **Non-Markovianity in our coupling simulator:** Our continuous-Sigma Lindblad coupling simulator uses finite-state pseudomodes to approximate structured bath spectral densities (following the pseudomode / chain-mapping literature). The Keeling Perspective makes explicit that this approach is **equivalent to constructing a PT-MPO with bond dimension bounded by the number of pseudomodes** (Section III.2, HEOM connection). This is the "engine-side gauge" (as noted in our xu_ankerhold_qdmess_nonmarkovian_review reading note) — different representations of the same reservoir kernel.

2. **Identifiability implications:** The perspective does not discuss identifiability or gauge freedom (not its topic). However, the PT-MPO decomposition into hidden degrees of freedom explicitly highlights that **many different representations can produce the same system dynamics** — this is the process-tensor-level analog of the record-level gauge/alias problem. A PT-MPO bond dimension corresponds to a minimal number of hidden degrees of freedom needed to represent the environment's effect, but the decomposition is not unique. For our twin, this means the "environment representation" side of the coupling simulator is inherently gauge-variant — a finding consistent with our existing engine-side gauge understanding.

3. **Temporal entanglement:** The concept of **temporal entanglement** (entanglement in the time direction, Section III.1) measures how much past-future correlation exists after tracing out the system. This is directly relevant to our non-Markovian analysis: if temporal entanglement is low, the environment's effect on the system is short-memory (Markovian or near-Markovian). If temporal entanglement is high, long-range time correlations matter. This provides a quantitative diagnostic for when our Markovian approximation (composed carrier) fails.

4. **Passive detector records and PT:** The PT formalism treats the **operations** (gates, measurements) as inputs and the **final state** as output. In QEC, the operations are known (circuit gates) and the syndrome measurements are the outputs. The process tensor for the QEC circuit encodes the **dependence of syndrome correlations on environmental memory**. This is the formal language for our claim that non-Markovianity produces detectable syndrome-correlation signatures — though the paper does not address QEC specifically.

5. **Software ecosystem:** The catalog of 13 PT/HEOM/TN packages (Table 1) is directly relevant as a baseline/competitor map. Key packages for our project:
   - **ACE** (Automated Compression of Environments) — general non-Gaussian uncoupled bath modes; the closest to our continuous-Sigma approach for independent noise sources
   - **OQuPy** — PT-MPO for Gaussian bosonic baths; relevant if we model common-bath coupling
   - **MPSDynamics** — T-TEDOPA (thermalized MPS-based chain mapping); reference for our pseudomode discretization quality
   - **MPSQD** — MPS-based HEOM; hybrid HEOM+MPS approach similar in spirit to our MPS carrier

6. **Gauge/identifiability: NONE.** The paper does not address gauge or identifiability. As a forward-simulation framework, the PT encodes the complete dynamics; the issue of whether different PT representations yield equivalent observable predictions is not discussed.

## 6-criterion methodology table

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| **Soundness** | 5 | Perspective by field leaders; each method described is well-established in the literature. The unifying PT framework is mathematically rigorous. |
| **Novelty** | 3 | As a Perspective, the paper's primary contribution is synthesis and unification, not new results. The TTI-PT and bond-dimension discussions are drawn from earlier works. Novelty lies in the systematic organization and the explicit PT-to-method mappings. |
| **Reproducibility** | 4 | All methods referenced to published papers with code. Table 1 catalogs 13 software packages. Equations are fully specified. Reproducibility is inherited from the original method papers. |
| **Experimental design** | 4 | No new experiments. The benchmarking proposal (sub-Ohmic spin-boson model) is well-motivated. The software comparison is comprehensive. Lacking: quantitative comparison of the 13 packages on identical benchmarks. |
| **Statistical rigor** | 4 | Not an empirical paper; statistical issues are not addressed. For a review, the framing is rigorous. |
| **Scalability** | 3 | The O(N_m log N_m) TTI-PT scaling is a significant improvement. However, the scaling of PT methods with system size (as opposed to number of timesteps) is not systematically treated — the hidden bond dimension may still grow exponentially for strongly coupled systems. |

## Strengths (S1-S4)

- **S1 (Section III):** The unification of HEOM, TEDOPA, GQME, QuAPI, and HOPS under the PT-MPO framework is a genuine conceptual contribution. For practitioners, this clarifies that method "A vs B" choices are often just different ways of constructing the same object — enabling principled method selection based on problem structure rather than tradition.
- **S2 (Section II.2.1, Fig. 5-6):** The TTI-PT + iTEBD construction for Gaussian bosonic environments achieving O(N_m log N_m) scaling is a significant practical advance for long-time non-Markovian dynamics. The shallow-circuit-to-MPS conversion is elegant and efficient.
- **S3 (Section V):** The reuse framework (construct PT once, apply many pulse sequences/control fields) is the most practically compelling argument for the PT approach. In QEC contexts, this maps to: construct the process tensor for a syndrome extraction circuit once, then evaluate many candidate decoders or noise parameters without recomputation.
- **S4 (Section IV, Table 1):** The software survey provides a valuable resource, benchmarking an otherwise fragmented ecosystem. For us, it's a definitive landscape map of non-Markovian OQS simulation tools.

## Weaknesses (W1-W4)

- **W1 (Section III):** The unified picture is conceptually compelling but practically incomplete — the paper does not provide a decision procedure ("given problem X and resource constraints Y, use method Z"). The unification reveals connections but does not give operational guidance for method selection.
- **W2 (Section I.1):** The discussion of Markovian failure modes is thorough but the QEC context is entirely absent. No mention of syndrome correlations, passive detector records, or the specific challenges of QEC error mechanisms. The focus is on condensed matter, quantum optics, chemistry, and biology.
- **W3 (Section IV):** The claimed upfront cost advantage of PT methods assumes the bond dimension saturates (does not grow with number of timesteps). The conditions for this saturation are not systematically characterized — for high-entanglement environments (e.g., common baths with many qubits), the PT-MPO bond dimension may grow without bound.
- **W4 (Section V.4):** The mobile impurity section mentions the flow equation + TDVP approach for the Holstein model but truncates before giving concrete results or comparison. The paper has more breadth than depth in several application sections.

## How to use / trust + open questions [ours]

**Trust level:** High — PRX Perspective by established authors. The mathematical framework is rigorous; the software catalog is verifiable. The review status means there are no new untested claims.

**Critical implications for our project:**

- **The PT-MPO = pseudomode equivalence is explicitly confirmed** (Section III.2): our pseudomode Lindbladian is constructing a PT-MPO where bond dimension = number of pseudomodes. The TTI-PT construction provides an alternative: if our coupling simulator's noise is stationary and Gaussian, the TTI-PT + iTEBD approach may be significantly more efficient than explicit Lindblad evolution.

- **Temporal entanglement** is the quantitative diagnostic we lack for when our composed carrier's Markovian approximation fails. If temporal entanglement is low, memory effects are short and the DEM approximation is adequate. If high, we need the full memory kernel.

- **No QEC-specific barrier to adoption** of PT methods: the process tensor formalism is agnostic to circuit structure; it handles multi-time correlations naturally, which is exactly what QEC syndrome correlations are. The barrier is the upfront cost of constructing the PT for a large many-qubit environment.

**Open questions:**
- Can the TTI-PT construction be scaled to typical QEC code sizes (d=3 to d=7 surface code, 17-97 qubits) with realistic noise spectral densities? The paper's examples are single-impurity/small-system problems.
- What is the temporal entanglement of typical QEC noise environments (1/f flux noise, quasistatic charge noise, crosstalk)? This quantifies when non-Markovianity matters for syndrome correlations.
- Does the hidden-Markovian decomposition of the PT (Section II) correspond to our "engine-side gauge" in a formal sense, and can the gauge ambiguity be characterized by the non-uniqueness of the PT-MPO representation?
