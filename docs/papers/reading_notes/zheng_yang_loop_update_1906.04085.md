# Full-text review — Y. Zheng & S. Yang, "Loop update for infinite projected entangled-pair states in two spatial dimensions" (arXiv:1906.04085)

> **Provenance (2026-07-09): FULL-TEXT read (精读).** PDF (arXiv:1906.04085v1, 10 Jun 2019) →
> `outputs/papers/pepo_survey/1906.04085.txt` (PyMuPDF, 5 pages / 595 lines). All §/Eq/Fig/Table refs
> from that text. Figures not pixel-extracted — figure facts = captions + numbers stated in text.
>
> **ID/title verified.** The user brief named the target "Loop Update (LU) intermediate between SU and FU."
> arXiv:1906.04085 IS that paper: the title above, the method is "loop update" (§I, ln 84-86), and it
> treats cyclic optimal truncation on a 4-site plaquette loop for iPEPS imaginary-time evolution.

## Metadata [paper]
- **Authors / affiliation:** Yi Zheng and Shuo Yang (corresponding `shuoyang@tsinghua.edu.cn`), State Key Laboratory of Low-Dimensional Quantum Physics and Department of Physics, Tsinghua University, Beijing, China.
- **Venue / status:** arXiv:1906.04085v1 [cond-mat.str-el], 10 Jun 2019. Preprint, no journal publication information stated.
- **Type:** Method + numerical benchmark (tensor-network algorithm development; benchmarked on spin-1/2 AF Heisenberg model + transverse-field Ising model on square lattice).

## Executive summary [paper]
The paper proposes a **loop update (LU)** algorithm for infinite projected entangled-pair states (iPEPS) that lies **between simple update (SU) and full update (FU)** in accuracy and cost. The key idea is to treat each **4-site plaquette** (the A-loop or B-loop of a 2x2 unit cell) as an **MPS with periodic boundary conditions**, then perform a **cyclic optimal truncation** via full-environment truncation (FET) on the closed loop. This removes redundant internal correlations that SU misses near criticality, giving accuracy closer to FU at computational cost closer to SU. LU extends straightforwardly to **full loop update (FLU)** when combined with full-environment (BMPS/CTM) methods. Benchmarked on the gapless Heisenberg model (where SU struggles) and the transverse-field Ising model across its phase transition, LU consistently outperforms SU at the same bond dimension D.

## Method (deep) [paper]

### Structure
The iPEPS is a 2x2 unit cell of tensors `Γ_i[m_i]` (i=1..4) with physical index dimension d and virtual bond dimension D, interleaved with diagonal weight matrices `λ_α` (α∈{u,r,d,l}) on each bond (Eq. 1, Fig. 1). The Hamiltonian is decomposed as `H = Σ h[A] + h[B]`, where A and B are the two interleaved 4-site plaquettes of the checkerboard decomposition (Fig. 1a). Imaginary-time evolution applies `U(h_A) = e^{-δτ h_A}` (and similarly for h_B) as a **matrix product operator (MPO)** with virtual dimension χ_mpo (Fig. 2b). The A and B plaquettes consist of the same tensors in different orders and act as effective environments for each other.

### LU core: treating the 4-site loop as an MPS with PBC

1. **Evolved cluster (Eq. 2-3, Fig. 2a-c):** After applying the MPO U(h_A), the 4-site A-plaquette becomes a tensor cluster `F_A[λ̃_α, Γ̃_i]` where the bond dimensions are enlarged from D to D·χ_mpo. The enlarged weight matrices are `λ̃_α = λ_α ⊗ I`, and the evolved local tensors are `Γ̃_i[m_i] = (Π_β λ_β²) Σ_{m'_i} U_i^A[m_i, m'_i] Γ_i[m'_i]`. Two weight matrices `λ_β` on outward-pointing branches are included (as in standard SU for iTEBD/iPEPS) and must be removed by `λ_β^{-1}` at the end of each iteration (ln 196-200). The key observation: **Eq. 2 describes an MPS with periodic boundary conditions** (ln 201-202), with each physical leg and two open branches combined to give effective bond dimension D²d (Fig. 2c, ln 203-205).

2. **Canonicalization within the loop (option iii, ln 224-235):** The paper enumerates four options for truncating the loop:
   - **(i)** Variational MPS minimization: cost `O(D^6 χ_mpo^6)`.
   - **(ii)** Successive SVD → quasi-canonical form: cost `O(D^7 χ_mpo^7 d^2)`.
   - **(iii)** The Orus-Vidal canonicalization procedure [40] designed for MPS under non-unitary evolutions: cost `O(D^5 χ_mpo^3 d)` — this is what they USE as a **pre-optimization** to retain the MPS-PBC form of Eq. 2 while preserving bond dimension (ln 237-241).
   - **(iv)** Full-environment truncation (FET) [Evenbly 2018]: cost `O(D^6 χ_mpo^6)`.

   They adopt (iii) as initialization, then (iv) as the actual truncation scheme.

3. **Cyclic optimal truncation via FET (Fig. 2c→e, ln 243-275):** For each bond α in the loop, the Schmidt weight matrix and two isometries are initialized by SVD: `λ̃_α = μ λ'_α ν†`. These isometries are then **variationally updated** by maximizing the fidelity:
   ```
   F = ⟨f|i⟩⟨i|f⟩ / (⟨f|f⟩⟨i|i⟩)
   ```
   where |i⟩ is the initial state (Fig. 2a, enlarged loop with dimension D·χ_mpo) and |f⟩ is the final state (Fig. 2e, truncated loop with dimension D). μ and ν serve as projectors that reduce bond dimension from D·χ_mpo back to D (ln 253-254). The result is `F_A[λ'_α, Γ'_i]` with `Γ'_i = ν† Γ̃_i μ`. This is the **FET cyclic optimal truncation** — it optimally removes redundant internal correlations on the closed loop.

4. **B-loop update (Fig. 2e→f, ln 277-279):** After completing the A-loop truncation, the same procedure is applied to the B-plaquette, which is obtained by rearranging (switching) the order of the renewed local tensors. This completes one full iteration.

### FLU (full loop update)
When the effective environment for each plaquette is calculated via BMPS or CTM (rather than relying on the interleaved A/B environment), the resulting scheme is called **full loop update (FLU)** (ln 280-287). The per-step cost of calculating the environment is `O(D^6 χ^3)` with χ > D² the two-layer truncated bond dimension.

## The OBSERVABLE / metric [paper]
- **Relative energy error** `ΔE = (E_0 - E) / E_0` vs QMC reference (Heisenberg model, Fig. 3a).
- **Staggered magnetization** M (Heisenberg model, Fig. 3b).
- **Cycle entropy** S_cycle [Evenbly 2018, ref 36] — a measure of internal (redundant) correlations in closed loops, defined on the 4-site loop (Fig. 3b inset).
- **Magnetization** `m_z = |⟨σ_z⟩|` as order parameter for the Ising phase transition (Fig. 4).
- **Critical exponents** β and **critical fields** h_c extracted from log-log fits of `m_z vs |h - h_c|` (Fig. 4 insets, table in §III).

## Findings + numbers [paper]

### Heisenberg model (gapless, Fig. 3)
| Metric | LU (D=6) | SU (D=6) | QMC reference |
|---|---|---|---|
| Energy per bond E_0 | -0.334377 | -0.334247 | -0.334719 |
| Relative error ΔE | 0.102% | 0.141% | — |

- Staggered magnetization is **reduced** in LU vs SU (closer to QMC).
- **Cycle entropy reduction** from SU to LU: at D=2, 0.0124 → 0.0105; at D=3, 0.0256 → 0.0235. The reduction grows with D (Fig. 3b inset), confirming FET removes redundant internal correlations.

### Transverse-field Ising model (Fig. 4, table in §III)
- **Off-critical (h=2.6):** all methods (LU, SU, FLU) agree within Δm_z < 10⁻², ΔE < 10⁻³.
- **Near-critical:** LU shows partial improvement over SU; **FLU shows significant improvement** in characterizing the quantum phase transition.

Critical exponents and fields extracted from FLU (table at ln 431-468):

| Method | h_c (D=2) | β (D=2) | h_c (D=3) | β (D=3) |
|---|---|---|---|---|
| FU + BMPS [13] | 3.10 | 0.346 | 3.06 | 0.332 |
| FU + CTM [14] | 3.08 | 0.333 | 3.04 | 0.328 |
| **FLU + BMPS** | **3.091** | **0.332** | **3.058** | **0.328** |
| **FLU + CTM** | **3.084** | **0.330** | **3.054** | **0.327** |
| QMC | 3.044 | 0.327 | — | — |

The improvement is especially notable at D=2 (small bond dimension), where FLU brings β from 0.346 (FU+BMPS) down to 0.332 — much closer to the QMC β=0.327. This demonstrates that **cyclic truncations (LU) improve the accuracy of critical properties even at modest D**.

## Cost vs accuracy: LU vs SU vs FU [analysis]

| Scheme | Environment | Truncation | Leading cost | Accuracy regime |
|---|---|---|---|---|
| **SU** | Rank-1 (λ weights) | SVD on each bond independently | Low (`O(D^4)`) | Adequate far from criticality; fails when ξ > 2 |
| **LU** | Interleaved A/B plaquette (closed loop) | FET cyclic optimal truncation on 4-site MPS-PBC | Medium (`O(D^5 χ_mpo^3 d)` pre-opt + `O(D^6 χ_mpo^6)` FET) | Improved near criticality (removes redundant loop correlations) |
| **FLU** | BMPS/CTM full environment + loop truncation | FET + full environment | High (`O(D^6 χ^3)` environment + `O(D^6 χ_mpo^6)` FET) | Best critical exponents; matches FU accuracy at lower D |
| **FU** | BMPS/CTM full environment | SVD on each bond | High (`O(D^6 χ^3)` environment) | Accurate but expensive |

Key insight from Fig. 3a: the LU energy curve lies below the SU curve for all D, with the gap widening at larger D. This is because SU's rank-1 environment approximation (capturing only nearest-neighbor correlations through λ weights) becomes increasingly inadequate as entanglement grows — and the **cycle entropy grows with D** (inset Fig. 3b), meaning the loop carries more redundant correlation that SU leaves in place and LU optimally removes.

## Performance near criticality (where SU fails) [analysis]
The paper's motivation (§I, ln 38-40) states explicitly: "Near criticality, however, the growth of truncation errors may defeat the efficiency, especially in two (or higher) dimensional gapless systems." The Heisenberg model (gapless) is the primary test case — SU's error is ~40% larger than LU's at D=6 (0.141% vs 0.102%). The Ising model (critical point at h_c ≈ 3.044) shows that LU-only provides "partial improvement" over SU, but **FLU** is where the big improvement appears — capturing critical exponents accurately even at D=2.

The reason SU fails near criticality: the **correlation length ξ diverges**, and SU's bond weights (λ matrices from Schmidt decompositions) only capture local — essentially nearest-neighbor — entanglement structure. The loop carries **redundant internal correlations** from inelastic entanglement (short-range entanglement within the loop that is not part of the true long-range physical entanglement). LU's FET cycle optimally removes this redundancy, similar to how Loop-TNR removes short-range entanglement in tensor-network renormalization (ln 379-380, citing ref 38 by the same S. Yang).

## Relevance for PEPO mixed states [analysis]

### Could LU be used for PEPO mixed states?
**Yes, in principle.** The LU mechanism operates on the **tensor-network structure** (the 4-site loop, canonicalization, FET), not on the specific tensor semantics (wavefunction vs operator). A PEPO (projected entangled-pair operator) representing a 2D mixed state has the same square-lattice geometry with virtual bonds and a 2x2 unit cell — the only difference is that each tensor carries a fused physical index of dimension d² (bra × ket) instead of d for a wavefunction PEPS. The LU algorithm of: (1) forming the 4-site loop as an MPS-PBC, (2) canonicalizing via Orus-Vidal, (3) applying FET cyclic truncation — transfers directly.

**Potential benefit:** The paper shows LU helps most where SU's rank-1 environment under-captures correlations — i.e., when **correlation length ξ grows**. For PEPO mixed states, ξ depends on the system's mixing time / correlation decay length and can be large near dissipative phase transitions or for weakly-dissipative systems with long-range coherence. LU would improve accuracy there without going to full FU.

### Would LU help with the itrSU ξ > 2 problem?
**Likely yes, but with caveats.** The itrSU (iterative simple update) used in tePEPO [arXiv:2512.01781] already flags that ξ > 2 means simple-update's rank-1 environment approximation starts to fail (tePEPO paper, ln 1796-1799). LU addresses exactly this: it introduces a **closed-loop environment** (the 4-site plaquette) that carries more non-local information than bond weights alone.

However, there are important caveats:

1. **LU's loop is still small (4 sites).** It captures correlations within the 4-site plaquette but not beyond. For ξ ≫ 2, even 4-site loop information may be insufficient — FLU (LU + full BMPS/CTM environment) would be the extension needed. The paper's own Ising critical-exponent data shows LU-only provides "partial improvement" over SU; the large jump comes from FLU.

2. **itrSU's gauge assumption.** The tePEPO itrSU assumes a good Vidal gauge (the λ weights are meaningful Schmidt values). LU's canonicalization step (option iii) is designed precisely to fix such gauge issues for MPS-PBC (non-unitary evolution, periodic boundaries). So LU could simultaneously solve the gauge-fixing problem that itrSU flags as fragile.

3. **Scalability concern.** LU's leading cost `O(D^5 χ_mpo^3 d)` for canonicalization + `O(D^6 χ_mpo^6)` for FET is higher than SU. For tePEPO's typical D=4-10, this may be acceptable. But the cost scales as D^6 for FET, which becomes prohibitive for D > ~10-12.

### Compatibility with 2D density-matrix iPEPO
**Fully compatible geometrically.** The iPEPS in the paper assumes a square lattice (Fig. 1a) with a 2x2 unit cell and alternating A/B plaquette decomposition. A 2D density-matrix iPEPO on a square lattice has exactly the same topology — each site carries a tensor with four virtual bonds, and the checkerboard A/B decomposition applies identically.

**The key structural difference** is the MPO construction of the evolution operator. In the paper, U(h_A) is built from the **Hamiltonian** (imaginary-time evolution for ground state search). For a PEPO mixed state, the evolution operator would be the **vectorized Liouvillian** `e^{Δt · vec 𝓛}`, which has more complex MPO structure (doubled bonds from bra/ket copies). This means χ_mpo would be larger (typically χ_mpo ~ 2-5 for Hamiltonian vs χ_mpo ~ 3-8 for Lindbladian at the same interaction range). The LU method itself scales with χ_mpo, so larger χ_mpo means higher cost.

**The physical-index fusion** differs: PEPS fuses to dimension d² for the vectorized density operator vs d for the wavefunction. Since the physical index only appears in the factor `D²d` (ln 203-205), and D dominates d (D=4-10 vs d=2), this is a minor concern.

### Concrete adoption scenario
If one wanted to adopt LU for 2D PEPO mixed-state evolution:
- Drop LU into the tePEPO pipeline as a **drop-in replacement for the itrSU truncation step** (tePEPO §V.C): after applying the tePEPO super-operator and before truncating each bond, form the 4-site loop → canonicalize → FET.
- The canonicalization cost is `O(D^5 χ_mpo^3 d²)` (d → d² for the doubled physical index).
- The FET cost is `O(D^6 χ_mpo^6)`, independent of d.
- The benefit would be most visible for **small D** (D=4-6) where itrSU starts to fail near critical regions but FU is too expensive. For D ≥ 10, LU's FET cost `O(D^6)` may be as expensive as the full environment calculation.
- LU could also serve as a **warm-start** for FU: run LU for initial iterations, then switch to FU for final refinement.

## Limitations [paper]
- **2x2 unit cell only.** The paper assumes a 2x2 iPEPS unit cell (4-site plaquette). Extending to larger unit cells (d>3 surface code, eg) would require larger loops with more tensors, increasing the MPS-PBC canonicalization and FET costs.
- **Imaginary-time / ground-state focus.** The method is demonstrated only for ground-state search via imaginary-time evolution. Real-time evolution, finite-temperature (mixed-state), and Lindblad dynamics are mentioned as future work but not tested.
- **No rigorous error bound.** The accuracy improvement is empirical (better energies, better critical exponents), not certified.
- **Small improvement at large D?** The LU advantage is clearest at modest D (D=2-6). At very large D, the SU representation becomes expressive enough that the LU improvement may saturate — the paper does not explore D > 6 for the Heisenberg model.
- **Does not solve the fundamental iPEPS contraction problem.** LU improves truncation but still requires CTM/BMPS for computing observables (expectation values, correlators). The contraction cost `O(D^6 χ^3)` remains.
- **Not tested on model with sign problem or frustration.** The demonstrated models (Heisenberg, transverse Ising) are sign-problem-free and unfrustrated — standard cases for tensor-network methods.
