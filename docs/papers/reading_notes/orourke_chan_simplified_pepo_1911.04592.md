# Full-text review -- O'Rourke & Chan, "Simplified and improved approach to tensor network operators in two dimensions" (arXiv:1911.04592)

> **Provenance (2026-07-09): FULL-TEXT 精读.** Full text read from cached TXT at `outputs/papers/pepo_survey/1911.04592.txt` (arXiv plain text). Published as Phys. Rev. B 101, 205142 (2020). The paper reformulates PEPO expectation value evaluation as a sequence of MPO/gMPO operations via sequential 2D bipartitions, achieving orders-of-magnitude cost reduction for long-range interactions.

## Metadata [paper]

- **Authors / affiliation:** Matthew J. O'Rourke and Garnet Kin-Lic Chan -- Division of Chemistry and Chemical Engineering, Caltech.
- **Venue / status:** Phys. Rev. B 101, 205142 (2020); arXiv:1911.04592.
- **Type:** Methodological -- reformulation of 2D tensor network operator (PEPO) evaluation into MPO/gMPO operations, with application to finite-range and long-range 2D Hamiltonians.

## Executive summary [paper]

The paper addresses the under-utilization of PEPOs (projected entangled-pair operators) in 2D tensor network simulations. Two barriers are identified: (1) PEPO construction is conceptually more complex than the 1D MPO case, and (2) PEPO-based contraction significantly increases computational cost relative to the local-operator representations currently used in 2D simulations.

The solution is **three-fold**:

**First**, a new object called a **generalized MPO (gMPO)** is introduced (Section III A). A gMPO elevates the operator-valued MPO matrices to rank-3 tensors by adding a virtual index beta_i, allowing each gMPO tensor to encode *multiple* different MPO matrices. When the beta indices are summed, a gMPO represents a sum of many regular 1D MPOs, enabling coupling between operators acting "outside" the 1D domain of the regular MPO.

**Second**, a **boundary gMPO method** (Section III B) reformulates the PEPO expectation value contraction into a series of MPO and gMPO operations. The key insight: by bipartitioning the 2D system row-by-row (a horizontal cut), the Hamiltonian decomposes into three groups: terms fully below the cut, fully above the cut, and those crossing it. As the boundary-MPS contraction proceeds row-by-row, the algorithm constructs and applies MPOs and gMPOs sequentially to extract the energy "on-the-fly." This avoids ever constructing or contracting a full PEPO.

**Third**, for **long-range isotropic interactions** (Section IV C), a new scheme uses a 2D Gaussian basis -- exploiting the unique property that a 2D radial Gaussian factorizes into a product of 1D Gaussians. Vertical MPOs encode one-dimensional Gaussian interactions in columns, and horizontal gMPOs encode them in rows; their product recovers the desired 2D radially symmetric potential. This avoids the fictitious superlattice and complex radially-symmetrization schemes required by prior PEPO-based approaches.

The resulting algorithm is:
- **1-2 orders of magnitude faster** than explicit PEPO evaluation for finite-range Hamiltonians (Tables I-II)
- **Up to ~600x faster** than brute-force evaluation for uniform long-range interactions (Table II)
- **Many orders of magnitude more accurate** than PEPO-based CF (corner-function) approaches for Coulomb/long-range potentials (Figure 7)
- **Equally accurate or more accurate** than both PEPO and brute-force baselines across all tested cases

## Method (deep) [paper]

### Generalized MPOs (Section III A)

A standard MPO represents a 1D operator via operator-valued matrices W_hat[i] (rank-3 tensors with physical indices p_i, p'_i and virtual indices alpha_{i-1}, alpha_i). The full operator is reconstructed by matrix multiplication:

> O_hat = sum_{alpha} W_hat_{alpha1}[1] W_hat_{alpha1 alpha2}[2] ... W_hat_{alpha_{L-1}}[L]  (Eq. 4)

A **generalized MPO (gMPO)** elevates each W_hat[i] to a rank-3 operator-valued tensor M_hat_{beta_i}[i] by adding a virtual index beta_i in {1, ..., g}. Exposing all indices yields a rank-5 tensor M^{p_i p'_i}_{alpha_{i-1} alpha_i beta_i}[i]. For each value of beta_i, a different MPO matrix is encoded; the full gMPO represents a sum of up to g^L regular MPOs after the beta_i indices are summed.

The key function: the beta index couples a local operator acting "below" site i (from the other side of the bipartition) into specific matrix elements of the MPO along the row. This is the mechanism that couples vertical (inter-row) interactions into horizontal (intra-row) MPO structure.

**Example (Section III A, 2xL system):** A Hamiltonian with nearest-neighbor interactions between row 1 and row 2 (inter-row) plus nearest-neighbor interactions within row 2. The complementary operator vectors in row 1 are:

> O_hat_{beta_i}[i,1] = [I_hat_{i,1}, A_hat_{i,1}]  (Eq. 13)

and the gMPO tensors in row 2 (Eq. 14) consist of M1 = W_NN[i] (the standard nearest-neighbor MPO from Eq. 5) plus M2[i,2] which couples the A_hat_{i,1} from below. After contracting over beta_i (Eq. 15), the result is an effective MPO along row 2 that includes the inter-row interactions as effective on-site terms.

### Boundary gMPO method (Section III B)

The algorithm for evaluating <psi|H|psi> for a PEPS |psi> on an Lx x Ly lattice:

1. **Pre-compute environments** {envs[0], ..., envs[Ly-2]}: all partial contractions of <psi|psi> using the boundary method, starting from the top (row Ly) downward (Figure 4c).

2. **Row 1 MPO evaluation:** Construct the MPO for H_bot (all terms within row 1) and apply it between bra and ket of row 1; contract with envs[Ly-2] to get initial E_bot (Figure 4d).

3. **Complementary operator vectors:** Apply operator vectors O_hat (containing the A operators that will interact with sites above) between bra/ket of row 1 along vertical bonds. Call this partial TN "intops" (Figure 4e).

4. **Shift partition up** (between rows y and y+1). Construct a gMPO for row y encoding: (a) interactions within row y, and (b) interactions between row y and all rows below it. Contract with intops (below) and envs[Ly-y-1] (above). Add to E_bot (Figure 4f).

5. **Update intops:** Construct complementary operator matrices (MPO matrices along the vertical direction) relating O_hat in column x of row y-1 to O_hat in column x of row y. Apply these between bra/ket of row y, contract with old intops, compress (boundary method) to get new intops (Figure 4g).

6. **Iterate** steps 4-5 to the top row Ly.

The big-picture summary: At each bipartition between rows y and y+1, classify terms into three non-mutually-exclusive groups -- (1) both A and B below the partition, (2) A below but B above, (3) both below the previous partition. At each iteration, compute the difference (1)-(3) via gMPO + intops, then update intops to account for group (2).

**Computational savings:** Because intops has operator virtual indices only in the vertical direction (not horizontal), the boundary tensors lose the horizontal operator virtual index. This reduces the cost of boundary absorption by Dop^4 and compression by Dop^6 (where Dop is the PEPO virtual bond dimension).

### Finite-range Hamiltonians (Section IV A)

**Nearest-neighbor (Eq. 17):** The vertical MPOs are 2x2 (Eq. 18) because the gMPO extracts inter-row interactions immediately -- no need to "complete" B interactions in the vertical MPO. Speedup: ~30x over PEPOs, ~40x over brute force.

**Diagonal-neighbor (Eq. 19):** More complex gMPO tensors (Eq. 20) with a 4x4 M1 and M2 that couples A_hat_{x,y-1} from intops into both horizontal and diagonal interaction positions. After beta contraction (Eq. 21), the effective MPO matrix produces terms like (J2 A_hat_{x,y-1} + J1 A_hat_{x,y}) B_hat_{x+1,y}. Speedup: ~50x over PEPOs, ~60-70x over brute force.

**General finite-range (Appendix A):** For interactions up to horizontal range R and vertical range sqrt(2)R, vertical MPOs are (R+2)x(R+2), gMPOs are (2R+2)x(2R+2)x(R+1). The pattern generalizes: M1 encodes the horizontal interaction pattern; M2, ..., M_{R+1} couple vertical operators into the appropriate M1 matrix elements.

### Long-range Hamiltonians (Sections IV B-IV C)

**Uniform long-range (no coefficients, Eq. 22):** All-to-all interactions of equal strength. Requires 2x2 MPO matrices in the vertical direction (Eq. 23) where the identity in the lower-right corner accumulates all past A operators in a column (summing rather than discarding them). gMPO tensors (Eq. 24) are 4x4 for M1, 4x4 for M2. Scaling is O(N) vs brute force O(N^3), giving ~600x speedup at N=64.

**Long-range isotropic with coefficients (Eq. 25):** The key new scheme. Exploits the factorization e^{-lambda(x^2+y^2)} = e^{-lambda x^2} * e^{-lambda y^2} -- a 2D radial Gaussian = product of two 1D Gaussians. Vertical MPOs encode 1D Gaussian interactions (using the W_gen construction of Ref. [32] / Stoudenmire-White 2017), and horizontal gMPOs encode the complementary 1D Gaussians. Their product recovers the desired 2D potential.

A fit of the desired V(r) in a Gaussian basis (Eq. 26, V(r) approx sum_k c_k e^{-lambda_k r^2}) gives K terms, each requiring one set of vertical MPOs and gMPOs. The required bond dimension for the 1D Gaussian MPO is modest: max Dop = 14 for accuracy ~1e-10 (Figure 7a). Compared to PEPO-based approaches (which need Dop = 28 and suffer from additional numerical errors in radial symmetrization), gMPOs are **many orders of magnitude more accurate** (Figure 7b-c) at comparable computational effort.

## Results (deep) [paper]

### Speedups (Tables I-II)

**Table I: gMPO vs PEPO.** All tested Hamiltonians except LRAC show speedups of ~20-60x (gMPO over PEPO). For D=2 near-neighbor: 2.5-13x; D=2 diagonal: 3.7-28x; D=2 LRNC (uniform long-range): 3.7-27x. For D=3: 20-39x. For D=4: 19-33x. The LRAC (Coulomb potential) case is special: gMPO and PEPO have similar computational effort at fixed parameters, but gMPO is ~4 orders of magnitude more accurate.

**Table II: gMPO vs brute force.** Speedups are larger: ~35-60x for nearest-neighbor; ~60-120x for diagonal; ~570-1070x for LRNC (uniform long-range, O(N) vs O(N^3) scaling); ~16-34x for LRAC. A 16x16 system with D=2 shows 296x speedup for LRNC.

### Accuracy (Figure 5)

For finite-range and uniform long-range Hamiltonians, all three methods (gMPO, PEPO, brute force) exhibit the **same level of accuracy** for most parameter combinations. Where differences exist, gMPOs are observed to be *more* accurate than PEPOs -- the paper attributes this to gMPOs avoiding the additional truncation/approximation errors inherent in PEPO construction.

### Long-range Coulomb potential (Figure 7)

The key quantitative finding for the LRAC case (1/r potential on 8x8):

- **Figure 7a:** Maximum bond dimension of the 1D Gaussian MPO for L=250. Max Dop = 14 at singular value threshold 1e-10. Modest for an MPO, enabling practical use.
- **Figure 7b:** Varying boundary dimension chi at fixed K=12 basis functions. gMPO error decreases monotonically with chi; PEPO error stalls at ~1e-2 relative error.
- **Figure 7c:** Varying number of basis functions K at fixed chi. gMPO error decreases monotonically with K; PEPO error again stalls.

The stall is attributed to additional numerical errors in the PEPO's radial symmetrization (introducing a fictitious superlattice). The gMPO Gaussian basis is radially symmetric up to the SVD threshold (1e-10), whereas PEPO bases are "only radially symmetric up to significant numerical errors."

## Deep-dive: computational scaling reduction mechanism [paper]

The boundary gMPO method's cost reduction has two distinct origins depending on interaction type:

**For finite-range interactions:** The dominant savings come from eliminating the horizontal operator virtual index from the boundary tensors. In a full PEPO contraction, boundary tensors carry operator virtual indices in *both* directions, making boundary absorption scale with Dop^2 and compression with Dop^d (d ~ 3-4). In the gMPO method, intops carries operator virtual indices only vertically, reducing absorption by Dop^4 and compression by Dop^6 (Section III B). This 4-6 power reduction in Dop is the primary source of the 20-60x speedup.

**For long-range isotropic interactions:** The savings are more fundamental. Previous PEPO approaches (Refs. [25, 29, 30]) encoded the 2D radial potential through:
- Fictitious superlattices (introducing auxiliary sites)
- Complex radial symmetrization schemes (with intrinsic numerical errors)
- PEPO bond dimension scaling that makes contraction prohibitively expensive

The gMPO approach instead:
1. Fits the radial potential as a sum of 2D Gaussians (Eq. 26)
2. Each 2D Gaussian factorizes into 1D Gaussians (exact factorization, not approximate)
3. The 1D Gaussians are encoded as standard MPOs (horizontal) and vertical MPOs using the Stoudenmire-White SVD-based compression (Ref. [32])
4. No superlattice, no extra radial symmetrization step, no special PEPO construction

This avoids the fundamental difficulty that "functions of the Euclidean distance sqrt(x^2 + y^2) are difficult to represent efficiently within a tensor network structure" because 1D functions of x and y yield Manhattan distance or product functions, not radial ones. The Gaussian is special: e^{-lambda(x^2+y^2)} = e^{-lambda x^2} * e^{-lambda y^2}, which is an exact equality -- not an approximation.

## Contributions (claim -> evidence -> strength) [paper]

| Claim | Evidence | Strength |
|-------|----------|----------|
| gMPOs simplify PEPO construction by reducing it to familiar MPO concepts | Explicit gMPO tensors for 4 Hamiltonian classes (Eqs. 14, 20, 24, 28) + Appendix A general construction | Strong -- complete algebraic specifications |
| Boundary gMPO method reproduces PEPO accuracy | Figure 5: gMPO error vs PEPO error across all tested Hamiltonians and parameter regimes | Strong -- systematic comparison across three methods at multiple bond dimensions |
| gMPO method is 20-60x faster than explicit PEPO for finite-range interactions | Table I: speedups across D=2,3,4 and chi=5-40 for H_NN, H_D, H_LRNC | Strong -- consistent across parameter range |
| gMPO method is up to ~600x faster than brute force for uniform long-range | Table II: H_LRNC speedups; O(N) vs O(N^3) scaling cited | Strong -- scaling argument + numerical data |
| Gaussian basis + gMPO gives many orders of magnitude better accuracy than CF-PEPO for 1/r potential | Figure 7: gMPO error decreases monotonically with K and chi; PEPO error stalls ~1e-2 | Strong -- clean comparison at matched computational effort |
| Radial Gaussian factorizes exactly as 1D product | e^{-lambda(x^2+y^2)} = e^{-lambda x^2} * e^{-lambda y^2} (exact identity) | Theorem-grade -- exact algebraic equality |
| Boundary gMPO enables on-the-fly gradient computation for differentiable programming | Section III B final paragraph; Ref. [36] to Liao et al. 2019 | Moderate -- conceptual claim, no numerical demonstration |

## 6-criterion methodology table

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| **Soundness** | 5 | All constructions are explicit and algebraic: gMPO tensors are written in full, the boundary algorithm is step-by-step, and the equivalence to PEPO is argued from the bipartition decomposition. No hidden approximations beyond the standard boundary-MPS compression. The Gaussian basis factorization is exact. The Stoudenmire-White SVD compression is a known, controlled approximation. |
| **Novelty** | 4 | The gMPO concept and boundary gMPO method are new. The Gaussian-basis approach to 2D long-range interactions is elegant and novel. However, the individual components (MPO construction, boundary MPS method, Stoudenmire-White compression) are existing techniques. The contribution is the *reformulation* rather than a fundamentally new tensor network primitive. |
| **Reproducibility** | 4 | Complete algebraic specifications for all tensors. Reference implementations available online (Ref. [41], GitLab). Standard benchmarks (AFM Heisenberg, transverse-field Ising, 8x8 lattices). Missing: no explicit pseudocode or algorithm box summarizing the boundary gMPO method as a self-contained routine. |
| **Experimental design** | 4 | Systematic comparison across three methods (gMPO, PEPO, brute force) at multiple bond dimensions (D=2,3,4) and boundary dimensions (chi=5-40). Two different trial PEPS types (Heisenberg ground state, TFIM ground state). However, only 8x8 lattices are tested; no scaling study with system size (except the 16x16 point in Table II). |
| **Statistical rigor** | 3 | The reported speedups are "averages taken over multiple calculations for multiple different trial wavefunctions." No error bars on speedup numbers. Accuracy is reported only as relative error vs converged brute force, not as confidence intervals. The paper is clear about its metrics but does not provide uncertainty quantification. |
| **Scalability** | 4 | Finite-range: O(N) scaling demonstrated by construction and confirmed by speedup tables. Uniform long-range: O(N) vs brute-force O(N^3) scaling. Gaussian LR: Dop(L) saturates to a constant (max 14) independent of system size for a given lambda, enabling true O(N) with controllable accuracy. The bond dimension of the 1D Gaussian MPO does depend on lambda and may grow for very sharp potentials. |

## Strengths (S1-S4) [paper]

- **S1 (Section III B, boundary gMPO method):** The core algorithmic contribution -- reformulating PEPO evaluation as sequential MPO/gMPO operations is conceptually elegant and practically impactful. It lowers the barrier to using general 2D Hamiltonians in PEPS calculations because MPO concepts are much more widely understood.

- **S2 (Section IV C, Gaussian-basis long-range scheme):** An ingenious solution to a known hard problem (representing radially symmetric 2D potentials in tensor networks). The Gaussian factorization trick sidesteps the fundamental difficulty while remaining systematic (controlled by K and chi, with monotonic convergence).

- **S3 (Tables I-II, systematic speedup documentation):** The speedup numbers are consistently large and cover multiple Hamiltonian types, PEPS bond dimensions, and boundary dimensions. The comparison is fair (all methods implemented in the same straightforward manner).

- **S4 (Section IV A 2, diagonal-interaction gMPO construction):** The explicit diagonal-interaction example (Eq. 20) and the beta-contraction demonstration (Eq. 21) serve as an excellent pedagogical template for constructing gMPOs for arbitrary finite-range 2D Hamiltonians, clarified further by the Appendix A general construction.

## Weaknesses (W1-W4) [paper]

- **W1 (Section III B):** The boundary gMPO method is described only for finite rectangular lattices with boundary-MPS contraction. Extension to infinite (iPEPS) systems is discussed as "expected to generalize" but no explicit method or tensors are given. The requirement that "the contraction method starts from the boundary" restricts the class of compatible contraction algorithms.

- **W2 (Section IV C, LRAC):** The Gaussian-basis approach for long-range isotropic interactions works only for V(r) that can be well-approximated by a sum of Gaussians. While Gaussians can fit many decaying functions (Coulomb, Yukawa, etc.), sharply varying or oscillatory potentials may require many basis functions K, reducing the efficiency advantage. The paper does not characterize the K required for challenging potentials beyond the 1/r case.

- **W3 (Section IV):** The accuracy comparison (Figure 5) shows that gMPO and PEPO errors are comparable or gMPO is slightly better. However, the paper's claim that "gMPOs sacrifice no accuracy" is not a theorem -- it may depend on the specific PEPS and Hamiltonian. For some parameter regimes not tested, PEPO could potentially be more accurate.

- **W4 (Section III B, step 5):** The intops compression (the iterative update step) is described as using the boundary method contraction routine, but the truncation/compression is approximate. The accuracy impact of repeated intops compression through many rows (especially for large Ly) is not explicitly analyzed. Error accumulation over many rows could be a concern for tall lattices.

## Deep-dive: key explicit tensor forms [paper]

### The Stoudenmire-White MPO representation (Section II B 3)

The representation of a general two-body long-range Hamiltonian (Eq. 11):

> W_hat_{gen}[i] = [[I_hat, 0, 0],
>                    [(v_i)_a B_hat, (X_i)_{aa'} I_hat, 0],
>                    [C_hat, (w_i)_{a'} A_hat, I_hat]]

where v_i is a column vector of length l_i, X_i is an l_i x r_i matrix, and w_i is a row vector of length r_i. The continuous-index generalization: for a smooth V_ij, sub-blocks of its upper triangle are low-rank, and the SVD-based compression gives constant l_i, r_i independent of system size.

### Uniform-to-Gaussian generalization

The correspondence between uniform long-range (Section IV B) and Gaussian long-range (Section IV C) tensors illustrates the generalization pattern:

| Component | Uniform (constant J) | Gaussian (lambda) |
|-----------|---------------------|-------------------|
| Vertical MPO (Eqs. 23, 27) | 2x2: [[I, A], [0, I]] | (g+1)x(g+1): [[I, w A], [0, X I]] |
| M1 gMPO (Eqs. 24, 28) | 4x4 based on W_uniform-sym | (2g+2)x(2g+2) based on W_gen-sym |
| M_c gMPO (Eqs. 24, 28) | Single 4x4 M2 | g-1 matrices M_c, c=2..g |

The index g is the rank of the SVD compression for the Gaussian interaction coefficients.

## Relevance to AI_QEC [ours]

### 1. Can this simplified PEPO construction reduce the bond-dim cost for our use case?

**Short answer: Not directly for our primary carrier, but the boundary gMPO method has conceptual relevance for on-the-fly expectation value evaluation in TN-based decoders.**

Our use case (the qec_twin) has two main TN components:
- **The forward carrier** (MPS-based, either exact density-matrix for d3 or scalable MPS for larger systems): This evaluates a quantum circuit with noise (the observable = logical error rate). The operator is not a 2D Hamiltonian but a sequence of 1D (or quasi-1D) quantum channels applied to a state.
- **The decoder/audit layer** (Bayes-TN decoders, TN contraction for P(logical | syndrome)): This computes expectations over error configurations compatible with a syndrome.

The gMPO reformulation targets the *Hamiltonian expectation value evaluation* problem in PEPS ground-state optimization. This is structurally different from either of our use cases. However:

**Relevance point 1 -- On-the-fly evaluation:** The boundary gMPO method's principle -- evaluate operator expectation values incrementally during the contraction rather than first constructing a full PEPO and then contracting -- is conceptually transferable. If our TN decoder or audit layer needs to evaluate many operator expectations (e.g., multiple Hamiltonian-like terms for noise model averaging), a similar on-the-fly approach could reduce overhead.

**Relevance point 2 -- Gaussian-basis long-range interactions:** This is potentially relevant if our noise model includes long-range spatial correlations (e.g., crosstalk Hamiltonians with 1/r or screened Coulomb interactions between spectator qubits). The 2D Gaussian factorization technique could represent such interactions compactly within a 1D-MPO framework, which would be directly compatible with our MPS-based carrier.

**Relevance point 3 -- Operator compression:** The Stoudenmire-White technique for compressing long-range interactions (Section II B 3) is directly applicable to compressing any smoothly varying interaction matrix V_ij. If our noise model involves spatially correlated errors with a smooth correlation kernel, this technique could compress the MPO representation of the correlation operator.

### 2. Compatibility with FET/WTG truncation (2012.12233)

The FET (fixed-entanglement tensor) truncation / WTG (wavefunction tensor gauge) truncation from Stoudenmire & White (2012.12233) is the SVD-based MPO compression technique used in Section II B 3 (Ref. [32] of the paper). The paper explicitly uses this technique to construct the general MPO representation W_gen (Eq. 11). 

**Direct compatibility:** The gMPO construction of Section IV C (Eqs. 27-28) inherits this compatibility: the vertical MPOs and the gMPO tensors are built from the W_gen data ({v_i}, {w_i}, {X_i}) extracted via the FET/WTG method. The relationship is:

1. Run FET/WTG on the smooth interaction matrix V_ij to obtain compressed W_gen tensors for the 1D Gaussian interaction
2. Extract the site-dependent coefficient vectors/matrices
3. Plug into the gMPO template (Eqs. 27-28)

The paper demonstrates this works to very high accuracy (~1e-10 SVD threshold, Figure 7a).

**Limitation:** The FET/WTG compression requires that the interaction be a *smooth function of distance* for sub-blocks of V_ij to be low-rank. Abruptly truncated interactions (e.g., hard cutoff at a finite range) would not benefit. For our use case, if spatial noise correlations are smooth (e.g., Gaussian-correlated noise across qubits), FET/WTG would work; if they are structurally determined (e.g., by device geometry with sharp cutoffs), it may not.

### 3. Can this construction represent non-Markovian interactions?

**Short answer: No, not directly. The construction encodes spatial correlations (2D interaction potentials) but does NOT encode temporal (non-Markovian) correlations.**

The paper's Hamiltonians are all *static* (time-independent) 2D operators:
- H_NN: nearest-neighbor interactions
- H_D: nearest + diagonal neighbor
- H_LRNC: uniform all-to-all interactions (same strength, no temporal dependence)
- H_LRAC: long-range isotropic with distance-dependent coefficients

There is no time index, no memory, no dynamical map, and no process tensor. The construction is about efficient representation of *spatial* operator structure.

However, there is an indirect connection point: if a non-Markovian noise process can be represented as a **spatio-temporal tensor network** (e.g., a process tensor extended over both space and time), then the boundary gMPO method's row-by-row bipartition could be adapted to a layer-by-layer (time-step-by-time-step) bipartition. The gMPO would then couple "operator layers" from earlier time steps to later ones. But this would require:

1. Extending the operator from a 2D spatial object to a 3D spatio-temporal object
2. Representing the temporal correlations as additional indices in the MPO/gMPO structure
3. The bipartition would need to cut through time rather than through space

The paper does not attempt this, and the required generalization is non-trivial. The Gaussian basis technique (Section IV C) might generalize to smooth temporal correlation functions if they can be expressed as sums of Gaussians in the time difference, but this is speculative.

**For non-Markovian interactions, the process tensor / PT-MPO framework (Keeling 2026, ACE toolkit) is the appropriate formalism, not this PEPO reformulation.**

### 4. Additional relevance points

**Demarcation from our forward carrier:** The boundary gMPO method evaluates <psi|H|psi> for a PEPS ground state. Our carrier evaluates Tr[E_target(rho)] for logical error rate -- a fundamentally different expectation value structure (non-Hermitian effective channel, not a global Hamiltonian). The gMPO reformulation's cost reduction for PEPOs does not directly transfer to our channel evaluation problem.

**Gaussian-basis technique for noise spectral functions:** The factorization trick e^{-lambda(x^2+y^2)} = e^{-lambda x^2} * e^{-lambda y^2} might be adaptable to *spectral* representations of noise. If a noise power spectrum or bath correlation function factorizes spatially, the same technique could enable compact MPO representations of noise operators in larger lattices.

**Structural similarity to "Hamiltonian MPO" in DMRG:** The paper essentially shows that the familiar MPO construction for 1D Hamiltonians generalizes to 2D via gMPOs. The analogous statement for our setting: the MPO representation of a noise channel on a 1D qubit chain generalizes to 2D via PEPO-like constructions, but with the gMPO reformulation reducing the cost barrier.

**Code existence:** A reference implementation exists at GitLab (Ref. [41]), which could serve as a starting point if we need to implement the Gaussian-basis long-range operator in our TN infrastructure.

## How to use / trust + open questions [ours]

**Trust level:** High. The algebraic constructions are explicit and complete (all tensor forms written out). The numerical comparisons are clean, systematic, and cover multiple parameter regimes. The Gaussian-basis factorization is exact. The Stoudenmire-White compression is a controlled approximation with known SVD threshold. The 2017-2020 timeline from the Chan group at Caltech indicates mature, well-tested code.

**Direct use in our project:**
- The Stoudenmire-White MPO compression (Section II B 3, Ref. [32]) could be used directly to compress MPO representations of smooth correlation operators in our noise models.
- The Gaussian-basis technique (Section IV C) could be adapted if our spatial noise model includes long-range isotropic correlations.
- The boundary gMPO method's on-the-fly evaluation principle is conceptually instructive for designing efficient expectation value computations in our TN decoder/audit layer.

**Dependencies NOT met by this paper:**
- Does NOT provide a non-Markovian operator representation
- Does NOT address operator identification/learning (only forward evaluation given a known Hamiltonian)
- Does NOT provide an alternative to our MPS-based forward carrier for circuit simulation
- The operator structure is for static 2D Hamiltonians, not for dynamic quantum channels

**Open questions:**
- Can the Gaussian-basis technique represent cross-shaped correlation kernels (not fully isotropic) that commonly arise in device crosstalk?
- Does the boundary gMPO method's error from repeated intops compression (step 5) accumulate linearly or sub-linearly in the number of rows Ly?
- Can the gMPO formalism be adapted to represent multi-time (process tensor) operators extended over 2D space + 1D time?
- Is the Dop efficiency gain (removing horizontal operator virtual index) specific to boundary-MPS contraction, or does it generalize to other 2D contraction strategies (corner transfer matrix, CTMRG)?
