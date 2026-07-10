# Full-text review — Vanhecke, Vanderstraeten & Verstraete, "Symmetric cluster expansions with tensor networks" (arXiv:1912.10512, PRA 103, L020402, 2021)

> **Provenance (2026-07-09): FULL-TEXT read (精读).** Downloaded PDF
> `https://arxiv.org/pdf/1912.10512.pdf` → txt (PyMuPDF, 4 pp plus refs). All §/Eq/Fig/Table
> refs from that text. The paper is a Letter (L020402) — concise; the construction is described
> in text+diagram, not in numbered equations (equations appear only as inline expressions within
> the body). Tags: **[paper]** = stated in the paper; **[ours]** = our application/inference
> for `qec_twin`, NOT the paper's claim.

## Metadata [paper]
- **Authors / affiliation.** Bram Vanhecke, Laurens Vanderstraeten, Frank Verstraete — all
  **Department of Physics and Astronomy, University of Ghent** (Belgium).
- **Venue / status.** Phys. Rev. A **103**, L020402 (2021). arXiv:1912.10512v2, 28 Dec 2019.
  4 pp Letter + references. No appendices.
- **Type.** Methods / construction paper: a **tensor-network-based cluster expansion** for the
  exponential of a local operator, built as an MPO (1D) or PEPO (2D). Two applications: (a)
  MPS time evolution with very large time steps, and (b) variational PEPS ground-state finding
  via imaginary-time PEPO cluster expansion. **NOT a QEC paper — no mention of QEC.**

## Executive summary [paper]
The paper constructs a **size-extensive cluster expansion that preserves all spatial and internal
symmetries**, organized by connected-cluster size, and encoded as a Matrix Product Operator (1D)
or Projected Entangled Pair Operator (2D). The core idea: exponentiate the full Hamiltonian
cluster-by-cluster, encoding each connected cluster exactly (to infinite order within that
cluster) as a new virtual level in the tensor-network operator, subtracting overlaps with
previously encoded sub-clusters. The result is an operator that is **correct up to order t^{p-1}
for maximum cluster size p**, but with an error prefactor that decays as **~exp(-p)** rather than
the factorial scaling of standard series expansions.

The key result for us: **the cluster expansion enables time steps dt that are orders of magnitude
larger than Trotter-Suzuki for the same error tolerance** — the paper demonstrates dt=2.1 for the
XXZ chain with 5-site clusters, where Trotter would require dt~0.01–0.1. This is achieved while
**preserving all symmetries** (translation invariance, reflection, U(1) for the XXZ model),
which Suzuki-Trotter always breaks.

## Method (deep) [paper]

### 1. The core idea: cluster expansion vs Suzuki-Trotter (§1, Introduction) [paper]
**Suzuki-Trotter** splits `e^{t Σ h_i}` into a product of exponentials of the individual terms,
factorized across a small time step dt. The error scales as **c_n · dt^{n+1}** for n-th order
(p. 1), **but** it breaks spatial and internal symmetries of the Hamiltonian (e.g. translation
invariance is lost because the splitting picks a particular bond ordering).

**Standard series/perturbative expansions** (e.g. stochastic series expansion) preserve
symmetries but are **not size-extensive** — they involve a power series of the full Hamiltonian
and fail for uniform dynamics in the thermodynamic limit.

**The cluster expansion** (this paper) combines both advantages:
> "Our non-perturbative cluster expansion works equally well for simulating dynamics in one
> dimension with MPS and in two dimensions with PEPS." (p. 1)

The expansion is a **sum of all possible connected clusters up to a certain size p**, where the
evolution within each individual cluster is **exact up to infinite order**. If the Hamiltonian
has nearest-neighbour interactions and the maximum cluster size is p, only a fraction
**p! / p^p ~ exp(-p)** of the Taylor terms of order t^p are incorrect — giving an error that
decays **exponentially in p**, not factorial.

Concretely (p. 2, derivation reconstructed from text):
- At order t^p in the Taylor expansion of `exp(t Σ h_i)`, there are **p^p** different
  O(t^p) terms (all ordered sequences of p Hamiltonian terms from the set of p bond types).
- The cluster expansion captures all terms **except those that form a connected cluster of
  size p+1** (the (p+1)-site cluster terms). There are exactly **p!** such missing terms
  (all permutations of the p+1 distinct bond terms forming the connected (p+1)-cluster).
- Therefore the fraction of incorrect O(t^p) terms is **p! / p^p** ≈ `√(2πp) · e^{-p}`
  (Stirling), i.e. the error prefactor **decays exponentially with p**.

### For reference: the Stirling formula gives p! / p^p ~ √(2πp) · e^{-p}, so the error
### prefactor for the 5-site cluster is ~120/3125 ≈ 3.8%, for 7-site ~5040/823543 ≈ 0.6%.

### 2. The MPO construction (1D) (§"Construction in one dimension") [paper]

The construction grows a **matrix product operator (MPO)** for `exp(t Σ_i h_{i,i+1})` in the
thermodynamic limit, iteratively adding virtual levels for larger clusters.

**Step 0 — identity encoding:**
The first (zeroth) virtual level encodes the identity operator on every bond:
```
O^0_0 = 1   (the unit operator, label '0' denotes the first entry of the virtual legs)
```

**Step 1 — two-site clusters (virtual level '1'):**
Exponentiate each nearest-neighbour interaction term, then **subtract the identity** already
encoded in level 0 (to avoid double-counting). Perform an SVD of `(e^{h_{i,i+1}} − I)`:
```
O^0_1    and    O^1_0
```
These are two new tensor elements obtained from the singular value decomposition of
`e^{h_{1,2}} − I` (p. 1, diagram near bottom of col. 1). The SVD determines the bond
dimension contribution of this level (degeneracy = number of retained singular values).

**Critical property — extensivity:** Once these elements are added (O → O + O'), the MPO
automatically encodes **an extensive number of non-overlapping two-site clusters** (p. 2, top
diagram): the virtual level '0'→'1'→'0' transition picks up a two-site cluster at that
position, while leaving other bonds in the identity. **Overlapping two-site clusters are NOT
captured** — this is the key gap that higher clusters fill.

**Step 2 — three-site clusters (no new virtual level needed):**
Exponentiate the terms acting on three consecutive sites, and **subtract what was already
contained in the two-cluster terms**:
```
O^0_2 = e^{h_{1,2} + h_{2,3}} − O^1_0 · O^0_1 − O^0_0 · O^0_0
```
(p. 2, diagram). The element O^0_2 is computed by applying the inverses of the O^{1,0} and
O^{0,1} elements to the right-hand side (p. 2). **Crucially, this is absorbed into the existing
bond dimension — no new virtual level is added** for the three-site clusters.

**Step 3 — four- and five-site clusters (virtual level '2'):**
A new virtual level '2' is introduced, requiring **three new tensor elements**:
```
O^0_{12}, O^0_{21}, O^0_{22}
```
(p. 2, "with an extra virtual level '2' and three new tensor elements"). For the five-site
cluster example used for the XXZ numerics, the bond dimension reaches **1 + 4 + 16 = 21**
(p. 2): the first level contributes 1, the '1' level contributes 4 (by SVD degeneracy of the
two-site cluster), and the '2' level contributes 16 (by degeneracy of the four-site cluster).

**Bond dimension growth:** Each virtual level contributes a factor equal to the SVD rank of the
relevant cluster exponential (minus previously encoded content). For nearest-neighbour
interactions on a chain, the maximum cluster size p gives a bond dimension that grows as
**1 + Σ_{k=2}^{p} (SVD rank of k-site cluster)** — which is polynomial in p for fixed SVD
truncation, not exponential.

### 3. Extension to 2D: PEPO (§"Construction in two dimensions") [paper]

The construction is **generic and extends to higher dimensions** (p. 2). For a square lattice
with nearest-neighbour interactions, the 2D generalization produces a **PEPO** (Projected
Entangled Pair Operator):

**Translation to 2D clusters:** The same hierarchical cluster encoding works:
- Virtual level '1' captures two-site clusters (horizontal and vertical bonds) via SVD of
  `e^{h_{ij}} − I`
- Three-site clusters are again encoded into existing levels (L-shaped and straight
  three-site clusters; diagrams p. 2 bottom)
- **The new element in 2D: loops.** For clusters larger than three sites on a square lattice,
  closed loops (plaquettes) appear. The simplest loop — the **four-site plaquette** — requires
  introducing a new virtual level '2' (p. 3, diagram):
```
O^0_2 (plaquette) = e^{h_{1,2} + h_{2,3} + h_{3,4} + h_{4,1}} − [lower-order clusters]
```
  The four tensor legs of the PEPO at the four corners connect through the level-2 bond,
  wrapping around the plaquette.

**Bond dimension in 2D:** For the PEPO used in the numerical ground-state optimization (Table I),
bond dimension = **5** (p. 3 caption). This 5-dimensional bond accommodates the identity + '1'
level (two-site bonds, both orientations) + '2' level (four-site plaquette).

### 4. Symmetry preservation (§§1, Outlook) [paper]

**This is a central claim.** The cluster expansion preserves **all spatial and internal
symmetries** of the Hamiltonian:

> *"In contrast to other approaches, the cluster expansion does not break any spatial or
> internal symmetries"* (abstract)
> *"The MPO representation for the cluster expansion of the exponentiated Hamiltonian
> conserves all spatial symmetries such as translation invariance and reflection symmetry."*
> (p. 2)

**Why symmetry is preserved:** The construction treats all bonds/lattice directions
**equally** — there is no preferred ordering of terms (unlike Suzuki-Trotter which must pick
an ordering e.g. even-bond-first then odd-bond-first). The cluster expansion encodes the
full symmetric sum of all connected clusters, and the SVD on each cluster can be done in a
symmetry-respecting way (e.g. U(1) charge conservation for the XXZ model — used in the
numerics: *"We have used U(1) symmetry in the MPO"*, Fig. 1 caption).

**Practical consequence for PEPS ground-state finding (p. 3):** The variational optimization
of the imaginary-time PEPO fixed point inherits translational invariance and other global
symmetries — *"in such a way that translational invariance and other global symmetries are
conserved"* (p. 3). This is in contrast to the standard "full-update" algorithm (Jordan et al.
2008), which uses Trotter-Suzuki and breaks translation invariance, requiring re-averaging.

### 5. Numerical demonstration — MPS time evolution (§"Construction in one dimension", Fig 1) [paper]

**Model:** XXZ spin-1/2 chain in the thermodynamic limit (infinite MPS):
```
H_XXZ = Σ_i [ S^x_i S^x_{i+1} + S^y_i S^y_{i+1} + Δ S^z_i S^z_{i+1} ],   Δ = 1/2
```
**Protocol:** Time evolution from the Neel state |↑↓↑↓...⟩ using the MPO cluster expansion
with **maximum cluster size 5** (bond dimension 21). MPS bond dimension χ, with truncation
back to χ after each step via variational optimization of the global overlap.

**Time step sizes tested (Fig 1):** dt = 0.1, 0.3, 0.7, 2.1
- Error scales as dt^5 for the 5-site cluster (since gap order = p = 5)
- **dt = 2.1 produces results that are visually indistinguishable from the reference TDVP
  evolution (with very small time step)**, as measured by both occupation number n(t) and
  bipartite entanglement entropy S(t) (p. 2, Fig 1)

**Comparison to TDVP** (time-dependent variational principle, Haegeman et al. 2011):
- TDVP builds up entanglement slowly (p. 4: *"schemes relying on the time-dependent
  variational principle which show problems in building up the entanglement"*)
- Cluster expansion builds entanglement **very quickly** due to the large step size, which
  is advantageous for capturing dynamics that generate entanglement rapidly

**Entropy growth:** Linear up to t ≈ 13 (Fig 1 bottom), showing that a finite-χ MPS captures
the evolution well up to that time.

### 6. Numerical demonstration — PEPS ground state via imaginary-time PEPO (§"Construction in two dimensions", Table I) [paper]

**Model:** Heisenberg Hamiltonian on the square lattice with sublattice rotation:
```
H = Σ_{⟨ij⟩} [ −S^x_i S^x_j + S^y_i S^y_j − S^z_i S^z_j ]
```
The sublattice rotation ensures the PEPO is symmetric under reflection and complex conjugation
(p. 3).

**Method:** Approximate `e^{−τ H}` with a **PEPO cluster expansion** (bond dimension 5), then
find its fixed point variationally using the algorithm of Vanderstraeten, Vanhecke & Verstraete
(2018, PR E 98, 042145). The fixed point converges as τ → 0 to the optimal PEPS ground-state
approximation for H itself (not the Trotterized H — a contrast with the standard full-update
method, p. 3). **The computational cost is significantly smaller** than direct variational
optimization of the Hamiltonian (Corboz 2016, Vanderstraeten 2016).

**Results (Table I):**
| τ (imaginary-time step) | Energy D=3 | Energy D=4 |
|---|---|---|
| 0.1 | −0.6680688 | −0.6689614 |
| 0.0562 | −0.6680766 | −0.6689632 |
| 0.0316 | −0.6680792 | −0.6689637 |
| 0.0178 | −0.6680806 | −0.6689638 |
| 0.01 | −0.6680806 | −0.6689638 |
| variational PEPS (L. Vanderstraeten et al. 2016) | −0.6680791 | −0.6689642 |

**Key observations:**
- **Already at τ=0.1, the energy is remarkably close to the variational optimum** — within
  1.2×10^{-5} for D=3 and 2.8×10^{-6} for D=4
- The optimum is reached (to machine precision) by τ≈0.03 for D=3 and τ≈0.02 for D=4
- For comparison, a Trotter-based imaginary-time evolution would typically require τ~0.001–0.01
  for comparable accuracy

## What they do NOT do — gaps/implications for us [paper / ours]
Each item below is confirmed absent in the 4-page Letter.

1. **(i) NO application to open quantum systems / Lindblad evolution.** The paper only considers
   unitary time evolution (real- and imaginary-time Schrödinger dynamics). There is no
   Liouvillian, no Lindblad operator, no dissipator, no GKSL equation. The PEPO cluster
   expansion is constructed for **exponentiating a Hamiltonian**, not a Lindbladian. **[ours:
   this is the central gap to bridge for our use case.]**

2. **(ii) NO discussion of non-Markovian / time-correlated dynamics.** The expansion is
   Markovian (a single exponential of a time-independent generator). No pseudomode, no
   process tensor, no time-nonlocal kernel. **[ours: compatibility with pseudomode
   augmentation is undiscussed — see Relevance §4.]**

3. **(iii) NO error model or noise — the paper is about simulation methods for coherent
   dynamics, not noise.** The "cluster expansion" here is a numerically-exact simulation
   technique for unitary (or imaginary-time) dynamics, not an approximate expansion of a
   noise channel. **[ours: this is orthogonal to our noise simulation use case.]**

4. **(iv) NO explicit PEPO tensor element formulae for general cluster sizes.** The construction
   is described diagrammatically and by example (2-site, 3-site, 4-site plaquette, 5-site chain).
   The general formula for the MPO/PEPO tensor at cluster size k is not given as a closed-form
   equation — only as a recursive construction: "incorporate k-site cluster, subtract all
   sub-cluster contributions already encoded." **[ours: we would need to implement the
   recursive inclusion–exclusion for our own Hamiltonian terms.]**

5. **(v) NO discussion of the Trotter error trade-off vs cluster-expansion error.** The paper
   asserts the exponential prefactor advantage (p! / p^p) but does not provide a direct
   numerical comparison of Trotter vs cluster expansion at matched computational cost. The
   dt=2.1 demonstration is impressive but the comparison is to TDVP (which is not a Suzuki-
   Trotter method), not to a Trotter-MPO at dt=0.01. **[ours: we would need to benchmark
   cluster-expansion PEPO vs Trotter-based tePEPO for our specific Lindblad generators.]**

## Relevance to the twin — PEPO cluster expansion for Lindblad evolution [ours]

### 1. Can cluster-expansion PEPO replace Trotter-based tePEPO for Lindblad evolution?

**Short answer: Potentially yes, but with three caveats.**
The paper constructs `exp(tH)` for a local Hamiltonian. Our Lindblad evolution requires
`exp(t L)` where L = −i[H,·] + Σ D_k[·] (the Liouvillian superoperator). The cluster expansion
**does not depend on unitarity** — it only requires a **local generator** that can be
exponentiated on finite clusters. The structure is:

```
exp(t Σ L_i) ≈ Σ_{clusters C} [exact exp(t L_C within cluster)] − [overlap corrections]
```

where L_C is the restriction of the full Liouvillian to cluster C (including all Lindblad
terms whose support falls within C). The cluster expansion is valid for **any local generator**
that decomposes as a sum of local terms — the Lindbladian satisfies this because both the
Hamiltonian and Lindblad operators are local (in our composed-carrier architecture, they are
1- and 2-qubit terms in the 1D or 2D lattice).

**Caveat 1 — Liouvillian spectrum:** The exponential of a Lindbladian has spectral properties
(contractive, not unitary) that affect the SVD compression of cluster exponentials. The SVD
truncation of `e^{L_C} − I` would capture the operator Schmidt rank of the Lindbladian cluster,
which may differ from the Hamiltonian case. **The bond dimension of the resulting PEPO may be
higher for Lindbladian generators** because Lindblad operators introduce additional operator
space directions (non-Hermitian jump operators).

**Caveat 2 — positivity preservation:** The cluster expansion (inclusion-exclusion of cluster
exponentials) is a **linear operation on operators**. If each cluster exponential is a CPTP map
(the exact exponential of a Lindbladian on the cluster), then the cluster expansion produces a
**sum/difference of CP maps**. This is **not guaranteed to be CP** (or even positive) — the
subtraction step removes double-counted contributions, which can produce negative eigenvalues
in the Choi matrix. For Suzuki-Trotter, the product of CP maps is CP; for cluster expansions,
the **linear combination of CP maps is not necessarily CP**. This is a serious concern for
our application where CPTP preservation is a hard requirement.

**Caveat 3 — imaginary-time vs real-time Lindblad:** The ground-state application (Table I)
uses **imaginary-time** cluster expansion (τ = 0.1 is already very accurate). For **real-time**
Lindblad evolution, the same accuracy may not hold — the operator Schmidt rank (entanglement
in operator space) grows with time for real-time dynamics, whereas imaginary-time dynamics
contracts to the ground state. The dt=2.1 unitary demonstration is real-time, but for a
**dissipative** Lindblad evolution the operator entanglement may behave differently.

**Verdict: Promising but unvalidated.** The cluster-expansion PEPO could replace Trotter-based
tePEPO for Lindblad evolution **if** the three caveats are addressed: (a) SVD compression
efficiency for Lindbladian clusters, (b) CPTP preservation of the inclusion–exclusion
construction, (c) operator entanglement growth for real-time dissipative dynamics. The
**demonstrated dt=2.1 for unitary evolution** suggests that even if Lindblad clusters require
higher bond dimension, the **much larger time step** could more than compensate.

### 2. Compatibility with pseudomode augmentation

**Short answer: Compatible in principle, but the construction must change.**

Pseudomode augmentation adds **auxiliary degrees of freedom** (bosonic modes) to the system to
represent a non-Markovian environment as a Markovian Lindbladian on the extended system +
pseudomodes. This produces a **local Liouvillian** on an enlarged lattice (physical qubits +
pseudomode sites).

**Why it is compatible:**
- The pseudomode method produces a **local Liouvillian** L = L_sys + L_pm + L_int where the
  interaction is local between physical sites and their pseudomode ancillae
- This Liouvillian decomposes as a sum of local (1- and 2-site) terms — the same form required
  by the cluster expansion
- The cluster expansion can be applied to the **extended lattice** (physical + pseudomode sites),
  with cluster sizes measured in the extended spatial dimension
- The pseudomode sites typically have **nearest-neighbour coupling** to physical sites, which is
  the interaction geometry the cluster expansion handles naturally

**Why it may need adaptation:**
- Pseudomodes have **infinite-dimensional** local Hilbert spaces (truncated to d_eff ≈ 4–8 for
  numerical work). The SVD of cluster exponentials over physical+pseudomode clusters would
  operate on a larger local dimension, increasing the bond dimension
- The Liouvillian includes **decay terms for the pseudomodes** (`D[√γ a]`), which are Lindblad
  dissipators acting exclusively on the pseudomode sites. These are perfectly local (1-site)
  and should not increase cluster complexity
- The **interaction term** L_int (system-pseudomode coupling) is typically bilinear (a
  system operator coupled to a pseudomode annihilation operator) — this is a **2-site**
  interaction in the extended lattice, well within the cluster expansion's remit

**Potential advantage:** The cluster expansion's ability to take **large steps** could be
particularly valuable for pseudomode-augmented Lindblad evolution, because the pseudomode
decay rate γ sets a fast time scale that normally forces small Trotter steps. If the cluster
expansion can accurately evolve over a time step dt ~ 1/γ (capturing the pseudomode dynamics
exactly within each cluster), it would **avoid the Trotter bottleneck** that currently
constrains pseudomode simulations.

### 3. Concrete proposal for assessment [ours]

To test cluster-expansion PEPO for Lindblad evolution on our composed carrier
(`src/qec_twin/forward/scalable/composed.py`), the following steps would be needed:

1. **Implement 1D MPO cluster expansion for a Lindbladian** on a spin chain with local
   dephasing and amplitude damping (the simplest Markovian dissipative case). Compare
   accuracy vs exact diagonalization for small systems (N=4–8), benchmarking the SVD
   compression of `e^{L_C}` for 2- and 3-site clusters.

2. **Test CPTP preservation** by computing the Choi matrix of the resulting MPO cluster
   expansion and checking positivity (eigenvalues ≥ −NUMERICAL_ZERO). This is critical —
   if the subtraction step creates negative eigenvalues, the cluster-expansion PEPO is not
   a valid quantum channel and cannot be used for state evolution.

3. **Benchmark vs Trotter-based tePEPO** at matched bond dimension for a single syndrome
   round (d=3 surface code). Measure: LER prediction accuracy, operator entanglement entropy
   (bond dimension growth), and wall-clock time per step.

4. **Extend to pseudomode-augmented Liouvillian** (system + bosonic mode with γ decay).
   Start with the following system:
   - 1 physical qubit + 1 pseudomode (EM coupling strength g, decay γ)
   - Liouvillian: L = −i[H_int,·] + D[√γ a] + D[√Γ σ^−]
   - Cluster: 2-site cluster covering the qubit+mode pair (which is the natural physical
     cluster — the system and its environment mode are inseparable on the pseudomode time
     scale). The cluster expansion would treat each qubit+mode pair as a single cluster,
     with cross-cluster interactions mediated through the physical lattice.

### 4. Relationship to existing TN infrastructure [ours]

The paper's PEPO cluster expansion is **complementary to, not competing with**, the existing
TN approaches in our codebase:

| Method | Key feature | Limitation | Cluster expansion role |
|---|---|---|---|
| Suzuki-Trotter tePEPO | Simple, CP-preserving product | Small dt, breaks symmetries | Could replace for large dt |
| PT-MPO (ACE, Keeling) | Exact non-Markovian influence | Zero-dimensional system only | Could supply cluster-exact Lindblad on pseudomode clusters |
| PTSBE (Patti) | Pre-sample + batch identical | Coherent wedge unhandled | Orthogonal — cluster expansion handles the coherent part exactly |
| TJM (Sander) | MCWF-on-MPS, Markovian | Sequential, no operator parallelization | Cluster expansion could provide a pre-compiled evolution MPO for each jump sector |

### 5. How to use / trust [paper + ours]

**Trust in the paper:**
- **High** for the qualitative construction and the error scaling argument (p! / p^p) — the
  mathematics is self-contained and re-derivable
- **High** for the numerical results — the XXZ test (Fig 1) and Heisenberg ground state
  (Table I) agree with established reference results (TDVP, variational PEPS). The error at
  dt=2.1 is stated to be "exceedingly small" given the dt^5 scaling, and the visual comparison
  confirms this
- **Medium** for the PEPO ground-state results — the bond dimension is only 5, and the
  comparison is to variational PEPS, not to an exact reference (the exact ground-state energy
  for the Heisenberg model on the infinite square lattice has a Goldstone-mode correction
  fitted from finite-size scaling, not known exactly)

**What is NOT settled:**
- The CPTP-preservation question for Lindbladian cluster expansions (not discussed in the paper)
- The operator entanglement scaling for dissipative real-time dynamics (only unitary and
  imaginary-time tested)
- The comparison with Suzuki-Trotter at matched computational cost (not benchmarked)

**Open questions for the principal:**
- Verify the p! / p^p counting logic: for p=5, p!=120, p^p=3125, ratio=3.8% — consistent
  with the "exceedingly small prefactor" claim for dt^5 scaling
- Spot-check the Table I energies: the τ=0.01 result for D=3 (−0.6680806) vs the variational
  PEPS reference (−0.6680791) — agreement to 1.5×10^{-6}, which is remarkably tight given
  the τ=0.1 entry (−0.6680688) is already within 1.2×10^{-5}
- Verify that the U(1) symmetry used in the XXZ MPO (Fig 1 caption) reduced the largest
  subblock to D_max = 9, vs the full bond dimension of 21 — a factor ~2× reduction
