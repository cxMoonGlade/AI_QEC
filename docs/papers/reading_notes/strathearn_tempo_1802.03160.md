# Full-text review -- Strathearn, Kirton, Kilda, Keeling & Lovett, "Efficient non-Markovian quantum dynamics using time-evolving matrix product operators" (TEMPO) (arXiv:1711.09641 / Nat. Commun. 9, 3322, 2018)

> **Provenance (2026-07-09): FULL-TEXT read (精读) from LaTeX source**
> `outputs/papers/pepo_survey/1802.03160.*` contains the WRONG paper (Censor-Hillel & Dory, distributed
> spanner approximation). Correct paper = **arXiv:1711.09641** (Nat. Commun. 9, 3322, 2018). Read from
> downloaded `tempo_paper.tex` + supporting figure PDFs (TEMPO.pdf, bondplot.pdf, spinhalf.pdf, spin1.pdf,
> dynamicsfigure.pdf, methodsfig.pdf). All section/equation/figure references from that source.
> 10 pages + 5 figures (1 schematic, 2 spin-boson results, 1 dynamics, 1 bond-dimension plot).

## Metadata [paper]

- Authors: Aidan Strathearn (St. Andrews), Peter Kirton (St. Andrews), Dainius Kilda (St. Andrews),
  Jonathan Keeling (St. Andrews), Brendon W. Lovett (St. Andrews, corresponding: bwl4@st-andrews.ac.uk).
- Venue: Nature Communications 9, Article 3322 (2018). DOI 10.1038/s41467-018-05617-3.
  Preprint arXiv:1711.09641 [quant-ph] (v1: 27 Nov 2017, v3: 24 Sep 2018).
- Type: original method paper (numerically exact open quantum system dynamics).
  NOT a QEC paper, but foundational for process-tensor / influence-functional tensor-network methods.
- Code: TEMPO code at Zenodo DOI 10.5281/zenodo.1322407; later maintained as OQuPy
  (oqupy.readthedocs.io).
- Data: DOI 10.17630/44616048-eaac-4971-bbff-1d36e2cef256.

## Executive summary [paper]

TEMPO introduces a numerically exact and efficient method for simulating open quantum systems strongly
coupled to non-Markovian harmonic environments. It represents the **augmented density tensor (ADT)**
(Makri & Makarov's QUAPI formulation of the Feynman-Vernon influence functional) as a **matrix product
state (MPS)** and the multi-step propagator as a **matrix product operator (MPO)** along the **time
direction**. After each propagation step, the ADT-MPS is compressed via singular value decomposition
(SVD) with truncation, controlled by a cutoff `lambda_c`. This reduces the cost from exponential to
**polynomial in the memory cutoff K** (= tau_c / Delta). The paper demonstrates K up to **200 memory
steps** -- an order of magnitude beyond what standard QUAPI can reach (K < 20) -- enabling precise
location of the Ohmic spin-boson localization transition (alpha_c ~ 1.25 for spin-1/2, alpha_c ~ 0.28
for spin-1). It also models two spins in a common 1D/3D environment with widely separated timescales,
a problem inaccessible to existing methods.

## Method (deep) [paper]

### The ADT and QUAPI foundation (SSResults, Methods SSI)

The method starts from the discretized Feynman-Vernon influence functional for a system linearly coupled
to a bosonic bath. With a Trotter split (Eq. 3, symmetric second-order used in numerics), the reduced
density matrix at time t_N = N Delta is:

```
rho_{j_N}(t_N) = sum_{j_1...j_{N-1}} [ prod_{n=1}^N prod_{k=0}^{n-1} I_k(j_n, j_{n-k}) ] rho_{j_1}(Delta)
```

Each index j runs over d^2 Liouville-space elements for a d-dimensional system. The influence functions
I_k are:

```
I_k(j,j') = exp[phi_k(j,j')]  (k != 1)
I_1(j,j') = [e^{Delta L_0}]_{jj'} exp[phi_1(j,j')]
phi_k(j,j') = - O^-_j(O^-_{j'} Re[eta_k] + i O^+_{j'} Im[eta_k])
```

where O^-_j are eigenvalue differences of the coupling operator O, O^+_j the corresponding sums, and
eta_k are time-integrals of the bath correlation function C(t) (Eq. bathcorr):

```
eta_{n-n'} = int_{t_{n-1}}^{t_n} dt' int_{t_{n'-1}}^{t_{n'}} dt'' C(t'-t'')
C(t) = integral_0^infty domega J(omega) [ coth(omega/2T) cos(omega t) - i sin(omega t) ]
```

The summand is the ADT: an N-index tensor A^{j_N, j_{N-1}, ..., j_1}. The finite-memory approximation
sets I_k = 1 for k > K (= tau_c / Delta), so the ADT only has K legs at any time.

**Without compression**: the ADT has d^{2K} elements -- exponential in K, limited to K < 20 (Refs 14, 15).

### TEMPO: ADT as MPS + propagator as MPO (SSResults, Fig. 1, Methods SSI.A)

The key insight: the ADT can be decomposed as an MPS (Eq. 4):

```
A^{i_1,...,i_K} = a^{i_1}_{alpha_1} a^{i_2}_{alpha_1,alpha_2} ... a^{i_K}_{alpha_{K-1}}
```

where the bond dimensions alpha_m adapt to the temporal entanglement. The propagator B (a (2K-1)-index
tensor connecting A(t) to A(t+Delta)) is decomposed as an MPO (Eqs. 8-13):

```
B^{j_n,...,j_1}_{i_{n-1},...,i_1} = [b_0]^{j_n}_{alpha_1} (prod_{k=1}^{n-2}
  [b_k]^{alpha_k, j_{n-k}}_{alpha_{k+1}, i_{n-k}}) [b_{n-1}]^{alpha_{n-1}, j_1}_{i_1}
```

with the rank-4 core tensor:

```
[b_k]^{alpha, j}_{alpha', i} = delta^{alpha}_{alpha'} delta^{j}_{i} I_k(alpha, j)
```

**Propagation** proceeds in two phases (Fig. 1c-e):
1. **Grow** (n < K): successive contractions with asymmetric B tensors build the ADT from rank 1 to rank K.
2. **Propagate** (n >= K): contract with the fixed (K-independent) MPO B (Eq. 14), then sum over the
   oldest leg. The MPS maintains rank K.

At each step: contract MPS with MPO, then sweep left-to-right and right-to-left performing SVD
truncation at bond i, keeping singular values sigma >= lambda_c * sigma_0 (the standard MPS compression).

### Degeneracy exploitation (Methods SSI.A, final paragraph)

If the coupling operator O has degenerate eigenvalue differences (always true for spin operators: 2d-1
unique O^-_j values), the internal MPO bond dimension is reduced from O(d^8) to O(d^6). For the common
diagonal coupling case, O^--degeneracy gives a further reduction.

## Results [paper]

### Benchmark 1: Ohmic spin-boson localization transition (SSResults, Figs. 2-3)

The unbiased spin-boson model (Eq. 7): H = Omega S_x + S_z sum_i g_i (a_i + a_i^dagger) + sum_i omega_i a_i^dagger a_i
with Ohmic spectral density J(omega) = 2 alpha omega exp(-omega/omega_c).

Key results:
- **K = 200 memory steps used** -- an order of magnitude larger than standard QUAPI (Ref 14).
  The approach to the asymptotic limit near the phase transition requires this.
- **Crossover at alpha ~ 0.5**: from coherent decaying oscillations to incoherent decay (known result).
- **For alpha > 0.5**: <S_z(t)> decays exponentially, gamma(alpha) extracted from fits (Fig. 2a dotted lines).
- **Finite-memory artifact (CRITICAL)**: the finite-K ADT produces a gapped effective Liouvillian even in
  the localized phase where gamma should -> 0. So gamma(K, alpha) -> 0 only as K -> infinity for
  alpha > alpha_c. The transition is found by **extrapolating gamma vs 1/K to 1/K -> 0** (Fig. 2b).
- **Extracted alpha_c**: ~1.25 (spin-1/2) using cubic fits with 68%/95% confidence intervals (Fig. 2d).
  Consistent with analytic results (NRG: alpha_c = 1 + O(Omega/omega_c), Refs 26, 27, 3).
- **Errors**: sensitivity to lambda_c truncation < 1e-4, smaller than plot markers (Fig. 2d).
- **Spin-1 extension** (Fig. 3): d^2=9 per leg (vs 4 for spin-1/2), K=80 sufficient, alpha_c ~ 0.28,
  consistent with NRG (Ref 31) but disagreeing with variational ansatz (Ref 32).

### Benchmark 2: Two spins in a common environment (SSResults, Figs. 4)

Two spin-1/2 particles with Heisenberg coupling Omega and both coupled to a common phonon bath
(Eq. 16). Mapped to an effective SBM in the S_{z,a}+S_{z,b}=0 subspace (Methods SSII) with effective
spectral density J(omega) = 2 J_p(omega)(1 - F_D(omega R)) where F_D depends on dimensionality D.

The problem is **inaccessible to other methods** because:
- Fast timescale: Delta << 1/omega_c for local dissipation
- Slow timescale: tau_c >> R for environment-mediated interaction
- Standard ADT would need K = tau_c/Delta >> 1; TEMPO reaches K = 180 without memory cutoff
  (staying in "grow" phase throughout).

Results:
- **D=1 (Fig. 4b)**: Clear revivals at t = R due to strongly oscillating J(omega) producing a peak in C(t=R).
  Secondary revivals at t ~ 2R from re-interaction. Profile independent of R when R >> 1/omega_c.
- **D=3 (Fig. 4c)**: Much weaker oscillations; small amplitude features at t ~ R visible for R=8 but not R=16.

### Computational scaling (SSDiscussion, Methods, Fig. 5)

- **Standard ADT**: N_tot = d^{2K} = 4^K for spin-1/2 -- exponential.
- **TEMPO** (Fig. 5): total MPS size N_tot and max bond dimension chi_max vs K:
  - alpha = 0.1, 0.5 (weak/moderate coupling): ~quadratic growth with K.
  - alpha = 1, 1.5 (strong coupling, near/above transition): ~linear growth.
  - **Both polynomial** -- the central claim.
- **CPU time**: linear in N_tot. Largest run: alpha = 0.5, K = 200, 500 time points, ~20.5 hours on
  HPC Cirrus cluster (estimated ~RTX 5090 era).
- **Key insight**: the most demanding regime is alpha ~ 0.5 (crossover from underdamped to overdamped),
  not the strongly coupled regime.

## Analysis: 6-criterion methodology table

| Criterion | Score (1-5) | Evidence |
|---|---|---|
| **Soundness** (theoretical foundation) | 5 | Exact mapping from Feynman-Vernon influence functional to MPS/MPO is rigorous. Trotter error controllable. SVD compression controlled by lambda_c. |
| **Novelty** (contribution beyond prior art) | 5 | First to represent the ADT as an MPS with temporal MPO propagation. Breakthrough over QUAPI's exponential scaling. |
| **Reproducibility** (code, data, protocols) | 4 | Open-source code (Zenodo), data archived, and later OQuPy package. But no detailed convergence study (how chi scales with lambda_c for different models). |
| **Experimental design** (benchmarks appropriate) | 4 | Spin-boson transition is a standard benchmark. Two-spin problem is genuinely hard and well-motivated. Missing: comparison to other methods (PT-MPO, HEOM) on same problems. |
| **Statistical rigor** (error bars, sensitivity) | 4 | Lambda_c sensitivity checked (<1e-4). Cubic fits with confidence intervals for extrapolation. But only one extrapolation method tested. |
| **Scalability** (to larger systems, longer times) | 4 | Polynomial in K demonstrated (linear-quadratic). d^2 scaling per leg means spin-1 is feasible. Large systems not tried (would need 2D spatial network). |

## Strengths (S1-S3)

**S1. Exponential-to-polynomial reduction (SSMethods, Fig. 5).** The central achievement. Standard QUAPI
has N_tot = d^{2K} elements; TEMPO achieves N_tot ~ O(K^p) with p=1-2 depending on coupling, and this
is explicitly demonstrated with scaling plots. This is not a heuristic claim -- the bond dimension adapts
via SVD and is explicitly measured.

**S2. Reaches K=200 (SSResults, Fig. 2).** The spin-boson phase transition requires long memory near the
critical point because the localization gap closes. Standard ADT is stuck at K < 20 (Refs 14, 15) and
cannot extrapolate to the K->infinity limit. TEMPO's K=200 is sufficient for the cubic extrapolation,
and this is the key enabler of the main physics result (alpha_c estimate).

**S3. General and extensible (SSDiscussion).** The method is not tied to the Ohmic spin-boson model.
Any system with linear coupling to a harmonic bath works (any J(omega), any T). The Discussion mentions
future extensions: combination with tensor transfer (Ref 43) for long-time propagation, optimal boson
basis (Ref 44) for larger systems, which have since been realized in the ACE/OQuPy framework.

## Weaknesses / Limitations (W1-W3)

**W1. Single harmonic bath only (implicit throughout).** The entire formulation assumes a single
linearly-coupled harmonic environment via the Feynman-Vernon influence functional. Multiple independent
baths are not addressed. The independent-mode decomposition and stacking (which ACE later provides) is
not discussed.

**W2. Finite-memory extrapolation is the actual method for phase transitions (SSResults, Fig. 2b-d, and
Discussion).** The finite-K ADT always produces a gapped effective Liouvillian (Ref 29). This means
TEMPO *directly* cannot see a truly gapless phase; the phase transition must be inferred by
extrapolation. The authors acknowledge this ("origin of this discrepancy is the finite memory
approximation") and handle it carefully with cubic fits and confidence intervals, but it remains an
extrapolation with model-dependent fitting.

**W3. Single-site / few-level system only.** The local Hilbert space dimension d enters as d^{2K} in
the uncompressed tensor, and while TEMPO compresses this, the local legs still carry d^2 indices.
The paper explicitly says "easy extension to study larger quantum systems" is left to future work
("may also be combined with approaches such as ... optimal boson basis"). For many-qubit systems
(d=2^n), direct application is impossible -- this is the **PEPO gap**.

## Relevance to the twin (qec_twin)

### Temporal MPS as a carrier mechanism (THE KEY GAP)

TEMPO is foundational to the current reading campaign because it defines the **1D-temporal tensor
network** (influence functional as MPO along time) that is the first bridge toward a combined
**2D-spatial PEPO x 1D-temporal MPO = 3D tensor network** for quantum error correction. The key
connection and gap:

**TEMPO's structure**: time direction is an MPO chain because the influence functional only couples
nearby time steps (finite memory K). The system's evolution at time t only depends on a window
[t-K*Delta, t]. This is a **1D chain in time** -- perfect for MPS/MPO because the entanglement
is constrained along the single temporal direction.

**PEPO's structure (from the parallel reading)**: a 2D tensor network over space (qubits on a
surface code lattice) for the noise channel / density operator after a syndrome measurement round.
Spatial correlations (crosstalk, long-range entanglement from coherent errors, leakage) live in
the 2D plane.

**THE KEY GAP -- 2D spatial + 1D temporal = 3D network**: Combining TEMPO's non-Markovian temporal
propagation with PEPO's spatial 2D noise representation would give a **3D tensor network** with:
- 2 spatial dimensions (qubit lattice)
- 1 temporal dimension (memory / influence functional depth K)

No known method compresses a 3D tensor network efficiently in the general case. However, TEMPO
works because the temporal direction has **finite-range coupling** (the influence functional decays).
If we combine:
- TEMPO's temporal MPO (coupling only to K previous steps)
- PEPO's 2D spatial representation (coupling neighboring qubits)

We get a 3D network with **finite-range interactions in all directions**, which might be
contractable with a boundary MPS (similar to how 2D classical partition functions are contracted
with 1D MPS). This boundary-MPS approach is the likely path for a scalable non-Markovian QEC
simulator. TEMPO provides the **temporal half** of this picture; the PEPO reading provides the
**spatial half**.

### Specific relevance to twin capabilities

- **RECOVER (calibration)**: TEMPO's influence functional is the analytic time-domain object that
  the twin's calibration module must ultimately match for non-Markovian/temporally-correlated noise.
  The MPS representation offers a differentiable surrogate for the bath.
- **UNDERSTAND**: The temporal MPS bond dimension chi is a direct measure of "how much quantum
  memory" the bath induces. This maps onto the twin's alias band problem: longer memory means
  more hidden degrees of freedom in the observational channel.
- **MANIPULATE (knobs)**: TEMPO's format separates system propagator (M) from influence (I_k).
  The do() intervention on the system Hamiltonian only affects M, leaving I_k fixed for a given
  bath -- enabling fast re-evaluation across protocols.
- **PREDICT**: The process-tensor extension (ACE, Ref 2405.19319) makes TEMPO's influence functional
  a reusable object that can be computed once for a given device and then used to predict dynamics
  under any future control sequence.
- **Pseudomode contrast**: TEMPO captures the full continuous bath via the influence functional with
  adaptive bond dimension. Pseudomode methods (Garraway 1997, Iles-Smith 2014) discretize the bath
  into a few discrete modes living in an extended Hilbert space. TEMPO is more general (any J(omega),
  no fitting) but the bond dimension grows with memory time. Pseudomodes have fixed Hilbert space
  cost but require the spectral density to be decomposable into Lorentzians. For QEC hardware, where
  1/f noise + Ohmic + structured environments appear, TEMPO's generality is an advantage, but the
  bond dimension scaling with the longest correlation time limits how far ahead in cycles we can see.

## Open questions / next steps

1. **Can TEMPO's temporal MPO be combined with PEPO's spatial 2D network into a contractable 3D
   tensor network?** The finite-range temporal coupling (K memory steps) and local spatial coupling
   (nearest-neighbor gates) give finite interaction range in both space and time. A boundary-MPS
   contraction (sweeping a 2D "time slice" MPS through the 3D network) is the natural candidate.
   This is the central architectural question for the twin's scalable carrier.

2. **What is the computational cost of a full 3D contraction for QEC-relevant sizes?**
   TEMPO's temporal bond dimension grows as ~ O(K^p) with p=1-2. Spatial bond dimension for a
   surface code PEPO would grow as ~ exp(O(d)) for d x d patches under coherent noise.
   Combined: chi ~ exp(O(d)) x O(K^p). The d-scaling is the bottleneck -- can the coherent
   noise entropy be small enough for moderate d (3-7)?

3. **Does the TEMPO finite-memory extrapolation problem (W2) carry over to the QEC context?**
   In QEC, the analogous problem is whether finite-cycle Memory of syndrome measurements produces
   an effective Markovian description that artificially decouples logical error rates. The twin's
   "drift" prediction capability may require explicit extrapolation to infinite cycle count.

4. **Process tensor reformulation**: ACE (2405.19319) reformulates TEMPO's idea into a system-independent
   process tensor that can be precomputed. Can the twin precompute device-specific process tensors
   (one per physical qubit) and contract them with cycle-dependent system propagators for efficient
   prediction?

5. **Could TEMPO-style compression be applied to the Kraus operator representation of coherent gate
   noise?** The temporal compression works because influence functional correlation decays.
   Spatial compression of coherent noise across a surface-code round has no such decay -- but
   the finite-range of gates (nearest-neighbor CNOT/CZ) gives a spatial locality structure that a
   PEPO can exploit. The combination remains open.

## How to trust / use this paper

This is a **sound, well-executed method paper** from a group with a strong track record in open quantum
systems (Keeling, Lovett, Kirton). The mathematics is standard (MPS/MPO formalism from Schollwoeck/Orus,
Feynman-Vernon from Makri & Makarov). The benchmark is a known hard problem (Ohmic spin-boson
transition). The code is open source and has been maintained (OQuPy).

**Trust the core claim**: TEMPO achieves polynomial scaling with memory time for the Ohmic spin-boson
model. The evidence (Fig. 5) is clean. However, **do not over-generalize** -- the bond dimension
growth depends on the specific spectral density, coupling strength, and temperature. For more complex
environments (structured J(omega), multiple baths, non-zero T), the scaling may be worse.

**Use for the twin**: The temporal MPO is the correct framework for non-Markovian noise in QEC.
Read as the temporal half of the eventual 2D+1D tensor network. The pseudomode contrast (W3 discussion
above) frames the architectural choice the twin must make for the scalable carrier.

**Do NOT use as a QEC simulator directly** -- it is single-system only. The PEPO connection is the
required spatial extension.
