# Full-text review — C. Mc Keever & M. H. Szymanska, "Dynamics of two-dimensional open quantum lattice models with tensor networks" (arXiv:2012.12233)

> **Provenance (2026-07-09): FULL-TEXT read (精读).** PDF (arXiv:2012.12233v1, 22 Dec 2020) →
> `outputs/papers/pepo_survey/2012.12233.txt` (PyMuPDF, 15 pages / 1863 lines). All §/Eq/Fig/Table refs from that
> text. Figures not pixel-extracted — figure facts = captions + numbers stated in text.
>
> **ID/title verified.** arXiv:2012.12233 IS the Mc Keever & Szymanska iPEPO+FET+WTG paper that introduced
> Full Environment Truncation and Weighted Trace Gauge for 2D open quantum lattice mixed states.
> The companion Evenbly (2018) paper [68] introduced FET/WTG for closed-system iPEPS; this paper adapts them
> to mixed states (iPEPO / Lindblad dynamics).

## Metadata [paper]

- **Authors / affiliation:** C. Mc Keever and M. H. Szymanska, Department of Physics and Astronomy, University College London.
- **Venue / status:** arXiv:2012.12233v1 [quant-ph], dated December 22, 2020. Preprint (appears to be a method-development paper leading to the later 2512.01781 by J. Dunham & M. H. Szymanska). Not yet journal-tracked in our records.
- **Type:** Method + numerical simulation (tensor-network algorithm for 2D open quantum lattice dynamics; benchmarks against exact solutions of the dissipative transverse Ising model + comparison with Corner Space Renormalization for a driven-dissipative hard core boson model).
- **Key references for our purposes:** [68] G. Evenbly, "Gauge fixing, canonical forms, and optimal truncations in tensor networks with closed loops," Phys. Rev. B 98, 085155 (2018) — the original FET/WTG paper for iPEPS; [63] Kshetrimayum, Weimer & Orus (2017) — the original iPEPO+SU for 2D steady states; [79] Foss-Feig et al. (2017) — the exact solution family used as benchmark.

## Executive summary [paper]

The paper develops a **tensor network method for 2D open quantum lattice dynamics directly in the thermodynamic limit**, using an **iPEPO (infinite Projected Entangled Pair Operator)** ansatz for the density matrix. The central innovation is adapting **Full Environment Truncation (FET)** and **Weighted Trace Gauge (WTG)** — previously introduced by Evenbly [68] for closed-system iPEPS — to the **mixed-state (iPEPO) context**, where the truncation objective is a **mixed-state fidelity** (Eq. 9) rather than the pure-state overlap used by Evenbly.

The method proceeds as a TEBD-like application of Trotterized Lindblad dynamics (Eqs. 1-8). Each timestep: apply the dynamical map (Krylov subspace without explicit `e^{τL}` construction), SVD-decompose the enlarged bond pair, keep singular values above threshold `ε_D' = 10^{-8}`, then **truncate from D' back to D** using FET — which constructs the **Hilbert-Schmidt bond environment tensor Υ_jl** from the effective environment `E_hs` and optimizes a Rayleigh quotient to find the isometries `ũ, ṽ` and bond matrix `σ̃` that maximize the mixed-state fidelity between truncated and untruncated networks (Appendix B, Fig. 8-9). **WTG fixes the gauge** across the truncated bond, enabling efficient reuse of the environment as the CTMRG initial guess for the next timestep.

**Headline result:** WTG+FET reproduces exact dynamics for the dissipative transverse Ising model to precision `I(t) < 10^{-10}` at `D=4-5` in the strongly dissipative regime, and `D=5-6` in the weakly dissipative regime (Fig. 3). **WTG+FET outperforms Simple Update (SU) by ~10× in trace distance and infidelity** (Fig. 4-5), and **controls the accumulation of internal correlations** (measured by cycle entropy `S_cycle`, Fig. 5a). In the anisotropic dissipative XY model, the method reveals that the mean-field-predicted staggered-XY phase is **unstable to fluctuations** when correlations are included (Fig. 6), corroborating Keldysh field theory predictions [82].

## Method (deep) [paper]

**Master equation (the object evolved), Eqs. 1-2 (ln 187-217):**
```
dρ/dt = L(ρ) = -i[H,ρ] + D(ρ),   D(ρ) = Σ_α [ L_α ρ L_α† - ½{L_α†L_α, ρ} ]
```
Time-independent nearest-neighbor Hamiltonian (Eq. 10 gives the dissipative Ising example). Local Lindblad operators (single-site, translationally invariant). This is **GKSL/Lindblad — Markovian, time-local.**

**iPEPO ansatz (Fig. 2a, ln 222-248):**
- Rank-6 tensor A_j per site: physical indices bra/ket (each dim d) + four bond indices (dim D)
- Vectorized form: fuse bra/ket → d², making the iPEPO algebraically identical to an iPEPS for pure states (the key trick enabling reuse of iPEPS contraction machinery)
- Two-site unit cell (A_j, A_l) for translation invariance with a staggered structure; each unique bond gets a bond matrix σ
- Environment: **trace effective environment** `E_tr` (Fig. 8a) — for computing reduced density matrices; **Hilbert-Schmidt effective environment** `E_hs` (Fig. 8b) — for truncation optimization
- Both environments computed via CTMRG (Appendix A, Fig. 7), using a variant [76] with intermediate SVD for stability

**Time evolution (Fig. 2b-g, ln 310-411):**
- Trotter decomposition: `e^{τL} = e^{τL^e_x} e^{τL^o_x} e^{τL^e_y} e^{τL^o_y} + O(τ^2)` (Eq. 8)
- Each layer applied to nearest-neighbor pairs A_j, A_l
- The linear map `e^{τL}(A_j A_l)` computed via **Krylov subspace methods** (no explicit `e^{τL}` construction)
- Result: enlarged tensor `A'_{j,l}`, decomposed via SVD → bond dimension D' > D (Fig. 2c-d)

**FET — Full Environment Truncation (Appendix B, Fig. 8-9, ln 1313-1380):**

This is the core technical contribution adapted from Evenbly [68]. The goal: given the enlarged bond (dim D'), find isometries ũ, ṽ (D'×D) and new bond matrix σ̃ (D×D) that optimally truncate back to D.

*Step 1 — Construct the Hilbert-Schmidt environment E_hs (Fig. 7c, ln 1229-1239):*
For each tensor A_j in the vectorized iPEPO, form `ahs_j = tr_d(vec(A_j) vec(A_j)†)` — the Hilbert-Schmidt inner product over physical indices, leaving all bond indices open. This is an 8th-rank tensor per site (for 4 bonds). The full `E_hs` is the CTMRG-approximated contraction of the infinite network of these `ahs` tensors (same geometry as Fig. 7b but with `ahs` instead of traced `atr`). This is the **mixed-state analogue** of the pure-state environment in Evenbly — it captures the Hilbert-Schmidt norm of the full state with the unit cell's bonds left uncontracted.

*Step 2 — Construct the bond environment tensor Υ_jl (Fig. 8c-d, ln 1319-1333):*
Contract the updated tensors A'_j and A'_l (with enlarged bonds D') into the effective environment `E_hs_{j,l}`. This yields a **4th-rank tensor Υ_jl** (indices: two on the j-side of the bond, two on the l-side). Υ_jl encodes all information about how the rest of the infinite network "views" the bond being truncated.

*Step 3 — Set up the Rayleigh quotient (Fig. 8e-g, ln 1334-1344):*
The mixed-state fidelity between truncated state φ and untruncated state ρ is:
```
F(ρ, φ) = tr(ρφ) / sqrt(tr(ρ²) tr(φ²))                            (Eq. 9)
```
Maximizing `F²(ρ, φ) tr(ρ²)` (which is convex-equivalent to maximizing F) yields a Rayleigh quotient in the isometries u, v and bond matrix σ. The term `tr(ρ²)` is independent of the truncation and drops out. The resulting Rayleigh quotient is:
```
F²(ρ, φ) tr(ρ²) = (contraction of u, v, σ with Υ_jl) / (contraction of u, v, σ with B)
```
where B is the contraction of Υ_jl with appropriate factors (Fig. 9d).

*Step 4 — Alternating optimization (Fig. 9, ln 1341-1352):*
Define `R ≡ σv` (Fig. 9c). For fixed v, find `R_m` maximizing the Rayleigh quotient by solving the **generalized eigenvalue problem** `A R = λ B R` (Appendix C, ln 1353-1380). The optimal `R_m` is the principal eigenvector. Then SVD of `R_m` gives updated σ' and u'. Repeat symmetrically for `L ≡ v'σ'` (Fig. 9e-f). Iterate until convergence of ũ, ṽ, σ̃.

*Optimization details (Appendix C):* Since `A = P†P` (outer product), the optimal `R_m` can be found by `R_m = P B^{-1}` — solving a linear system rather than full diagonalization. In practice, use Moore-Penrose pseudoinverse, linear regression with truncated SVD, or iterative eigensolver (Lanczos/Arnoldi) for stability.

**WTG — Weighted Trace Gauge (ln 472-482):**
After FET finds the optimal isometries, the gauge across the newly truncated bond is fixed to WTG as described in Evenbly [68]. This is analogous to fixing the "canonical form" for a cyclic TN: the bond matrix σ is absorbed symmetrically such that the environment `E_hs` can be **recycled** as the initial guess for the CTMRG procedure that precedes the next FET step. This significantly reduces the number of CTMRG iterations needed.

**Simple Update (SU) baseline (ln 483-493):**
SU bypasses FET/WTG entirely: `ũ → ũ_su` and `ṽ → ṽ_su` are D'×D matrices with 1s on the diagonal and 0s elsewhere; `σ̃_su` retains the D largest singular values of σ'. This is equivalent to assuming the environment is **identity** — i.e., the bond being truncated is isolated from the network. The paper proves this is **not optimal** with respect to the mixed-state fidelity objective.

**Cycle Entropy S_cycle (Appendix E, ln 1451-1482):**
Adapted from Evenbly [68] for mixed states. Given the bond environment tensor Υ and bond matrix σ:
```
S_cycle = -Σ_α λ̃_α log₂(λ̃_α)                                     (Eq. E1)
```
where `λ̃_α = |λ_α| / (Σ_α |λ_α|)` are normalized absolute eigenvalues of `(σ ⊗ σ)Υ`.

- **S_cycle ≈ 0**: no significant internal correlations → WTG truncation alone (discard small WTG coefficients) is near-optimal; FET not needed.
- **S_cycle ⪆ 10^{-3}** [68]: internal correlations are present → FET is required to prevent accumulation. The paper finds that starting from a product state, S_cycle quickly grows, and FET is needed in almost all cases.

**Internal correlations** are defined as correlations in the TN that **do not contribute to any physical observable** of the quantum state but cause computational problems (ill-conditioned environments, breakdown of algorithms) if allowed to accumulate [68].

## The MECHANISM (for implementation) [paper -> ours]

- **Object:** the 2D open-system density matrix as an **iPEPO** vectorized to `(d², D, D, D, D)` per site, evolved by Trotterized Lindblad dynamics. This is the **2D-geometry mixed-state carrier** relevant to qec_twin's scalable-carrier front.

- **FET mechanism — what it actually does:**
    1. After a TEBD step, each pair of tensors is contracted with the dynamical map → one big tensor with an enlarged bond (D' > D).
    2. SVD is applied, yielding left/right isometries and singular values. **The SVD itself is a local, environment-blind decomposition.**
    3. FET then **re-embeds** the truncation decision in the full network context: it constructs `Υ_jl` by contracting the enlarged tensors into the CTMRG-approximated `E_hs` environment. This **4th-rank tensor** `Υ_jl` encodes the Hilbert-Schmidt norm of the remainder of the infinite network hanging off the two sites sharing the bond.
    4. The optimal isometries `ũ, ṽ` and bond matrix `σ̃` are those that, when inserted into the network, maximize the **global mixed-state fidelity** between the truncated and untruncated states. The optimization is reduced to a **generalized eigenvalue problem** per bond, with alternating sweeps (fix v, optimize uσ; fix u, optimize vσ).
    5. **Critically**, FET **removes internal correlations** — redundancy in the bond degrees of freedom that carries no physical information. This is why S_cycle is lower for WTG+FET than SU (Fig. 5a).

- **WTG mechanism — gauge fixing:**
    1. After truncation, the gauge across the bond is ambiguous (any invertible matrix G and its inverse can be inserted on either side without changing the physical state).
    2. WTG fixes this gauge by absorbing the bond matrix in a **balanced way** that makes the Schmidt weights (`σ̃` diagonal) the natural truncation measure in a translation-invariant network.
    3. Practical benefit: the `E_hs` from the previous timestep can be reused as the CTMRG initial guess, reducing iteration count.

- **FET vs SU — the essential difference:**
    - SU: truncates based on **local** singular values only. Equivalent to minimizing `||A'_j,l - A_j σ A_l||` in Frobenius norm assuming all other bonds are identity. Ignores the rest of the network.
    - FET: truncates to maximize **global** mixed-state fidelity. Equivalent to minimizing `||ρ - φ||` in Hilbert-Schmidt norm weighted by the actual network environment. Captures that truncating bond (j,l) affects the entire 2D tensor tangle.

- **Cycle entropy as a diagnostic:**
    - If S_cycle < ~10^{-3}: internal correlations are negligible → the simpler WTG-truncation (discard small WTG coefficients without FET optimization) suffices.
    - If S_cycle >= ~10^{-3}: FET is required. The paper shows S_cycle quickly exceeds this threshold in all non-trivial dynamics (Fig. 5a: S_cycle saturates at ~10^{-1} for D=4 in moderate damping).

- **FET's failure regime — correlation lengths and hopping dominance (Fig. 3c):**
    In the weak dissipation regime (V/γ = 4.0, hx/γ = 0), where hopping dominates and correlations are longer-ranged:
    - D=5,6 reproduce exact dynamics only up to tγ ≈ 2-3, then deviate while retaining qualitative behavior.
    - Larger D is required compared to strong dissipation (D=4 suffices there).
    - **Root cause:** the environment `E_hs` itself is approximate (truncated at CTMRG bond dim χ), and the FET optimization can only be as good as the environment it receives. When the correlation length ξ exceeds what χ can represent, the environment is no longer faithful, and even optimal FET truncation against a poor environment underperforms.
    - The paper notes (ln 1168-1179) that the **leading cost is CTMRG at O(χ³_hs D⁶)**, and scaling χ or D to capture longer correlations is expensive. This is the **computational bottleneck** — not FET itself.

- **Grounded parameters (Ising benchmark, §III.A):**
    - D up to 6, χ (environment dimension) = χ_tr = χ_hs up to 15
    - τγ = 0.01-0.005, ε_D' = 10^{-8}, CTMRG/FET convergence 10^{-10}
    - Local dim d = 2 (spin-½); two-site unit cell
    - The method converges well for **strongly dissipative regimes** at low D, needs larger D for coherent/hopping-dominated regimes

- **Where it acts:** nearest-neighbor dissipative Ising model (Eq. 10) with local Lindblad operators; driven-dissipative hard core boson model (Eq. 11) with single-site pump and loss; anisotropic dissipative XY model (Eq. 14) with local loss. All models are **Markovian** (Lindblad). No long-range interactions in this paper (unlike the later 2512.01781 which adds long-range via FSA).

- **Repo status:** NOT present. Our `forward/scalable/` carrier uses 1D MPS (`mps_forward.py`) + composed DEM (`composed.py`). No 2D iPEPO infrastructure exists. The FET/WTG algorithms would be new. However, the CTMRG machinery or VUMPS boundary-MPS (from the later 2512.01781) needed for the environments are also absent.

## The OBSERVABLE / metric [paper]

- **Magnetization** `m_x(t) = ½(tr(σ̂_x ρ_j) + tr(σ̂_x ρ_l))` (ln 567), averaged over two-site unit cell.
- **Purity** `Π₁ = ½(tr(ρ²_j) + tr(ρ²_l))` — single-site reduced density matrix purity.
- **Spin-spin correlations** `S^{xx}_{12}(t) = tr(σ̂_x_j ⊗ σ̂_x_l ρ_t)` (nearest neighbor) and `S^{xx}_{13}(t)` (next-nearest neighbor, same row/column, distance 2), averaged over 4 equivalent pairs each.
- **Infidelity of truncation** `I(t) = 1 - F(t)` averaged over the 4 Trotter layers per timestep, where F is the mixed-state fidelity Eq. 9 — measures how much information is lost per truncation step.
- **Trace distance** `T₂(t) = ½ tr(√((ρ_jl - φ_jl)†(ρ_jl - φ_jl)))` (ln 741) — used for **quantitative comparison** between WTG+FET and SU against the exact nearest-neighbor reduced density matrix. Averaged over the 4 nearest-neighbor pairs.
- **Cycle entropy** `S_cycle(t)` (Eq. E1) — diagnostic for internal correlation accumulation in the cyclic TN.
- **Convergence criterion** `ε_t = |tr(ô ρ_{t+τ}) - tr(ô ρ_t)| / (|tr(ô ρ_t)| τ) < 10^{-6}` (Eq. 13) for steady state.
- **Regime where informative:** infidelity I(t) is the most direct measure of truncation quality — it tracks the fidelity between the state with the enlarged bond (no truncation) and the state after truncation. Trace distance T₂ against an exact solution is the gold standard but requires the exact reference. Cycle entropy predicts when FET is needed vs when WTG alone suffices. **Epistemic class:** (b) prediction band for all metrics against exact; (c) heuristic for I(t) and S_cycle when no exact reference exists.

## Findings + numbers [paper]

| Result | Numbers | Conditions |
|---|---|---|
| Strong dissipation vs EXACT | D=4,5 reproduce exact to I(t) < 10^{-10}, mx(t), Π₁, S^{xx}_{12}, S^{xx}_{13} all match | V/γ=0.2, hx/γ=0, Fig. 3a |
| Moderate dissipation vs EXACT | D>3 good for single-site, D≥4 for correlators | V/γ=1.2, hx/γ=1.0, Fig. 3b |
| Weak dissipation vs EXACT | D=5,6 reproduce exact for tγ<2-3, then deviate qualitatively | V/γ=4.0, hx/γ=0, Fig. 3c |
| Beyond exact regime | Converged at D≥5, I(t) < 10^{-8} | V/γ=0.5, hx/γ=1.0, Fig. 3d |
| WTG+FET vs SU trace distance | T₂ ≈ 10× smaller for WTG+FET at D>3 | Moderate damping, D=4-6, Fig. 4a |
| WTG+FET vs SU infidelity | I(t) ≈ 10× smaller for WTG+FET at each step | D=4, moderate damping, Fig. 5b |
| Cycle entropy S_cycle | WTG+FET: saturates at ~0.2; SU: saturates at ~0.4 | D=4, moderate damping, Fig. 5a |
| Hard core boson steady state | n=0.09548, Re(⟨σ⁻⟩)=0.27670, g^{(2)}=1.06443 at D=4, χ=12 | ∆/γ=5.0, F/γ=2.0, J/γ=1.0, Table I |
| sXY phase stability | D=3 shows sXY order; D=4,5,6 shows **melting** to uniform phase | J/Γ=0.3, anisotropic XY, Fig. 6 |
| Even-step correlation decay | η ≈ 1.07 (exponential fit) | D=6, J/Γ=0.3, Fig. 6f inset |
| Leading computational cost | CTMRG: O(χ³_hs D⁶) | Appendix A, ln 1172 |
| FET convergence tolerance | 10^{-10} (also CTMRG) | ln 550-551 |

**Key comparison with SU (Fig. 4, 5):**
- SU shows **no systematic improvement** in T₂ as D increases beyond 3 (Fig. 4a inset): T₂ at D=3,4,5,6 are all similar and poor.
- WTG+FET shows **clear systematic improvement**: each increment of D reduces T₂.
- This is because SU's local truncation accumulates **internal correlations** (S_cycle grows and stays high) while FET's environment-aware truncation removes them.
- **Practical consequence:** increasing D under SU is wasteful — the extra bond dimension gets consumed by internal correlations rather than physical entanglement. FET ensures bond dimension is used for physical correlations.

## Limitations [paper]

- **Markovian/Lindblad ONLY.** The evolved object is `e^{tL}` for a GKSL generator (Eqs. 1-2). The Liouvillian L is time-independent and acts on nearest-neighbor pairs plus on-site dissipation. No non-Markovianity, no process tensor, no influence functional. Bath memory is nowhere in the construction.

- **Short-range interactions ONLY.** The Ising, hard core boson, and XY Hamiltonians (Eqs. 10, 11, 14) are nearest-neighbor. Long-range interactions (power-law) would require the FSA+Gaussian machinery of the later 2512.01781 — this paper does not have it.

- **Core bottleneck = CTMRG environment cost** (ln 1167-1179). O(χ³_hs D⁶) per CTMRG iteration, and the environment must be recalculated at each timestep for FET. WTG alleviates this by enabling environment recycling but does not eliminate the scaling. The paper suggests using boundary-MPS (VUMPS/TEBD) for speedup but does not implement it — this arrives in 2512.01781.

- **FET is uncontrolled for approximate environments.** The optimality of FET's truncation is only as good as the `E_hs` fed into it. `E_hs` itself is a CTMRG approximation with its own truncation (χ). In regimes where χ is insufficient for the correlation length, the "optimal" FET truncation is optimal against a wrong environment — the global error is not certified.

- **No certified error bound off the exactly-solvable line.** Only the hx=0 dissipative Ising has an exact reference. For all other regimes, convergence-in-D is shown but is convergence-only, not a rigorous bound.

- **PEPOs are not inherently positive** (ln 252-261). The iPEPO ansatz does not guarantee positivity of the density matrix. The paper relies on the CPTP nature of the dynamical map to maintain physicality in practice. The problem of deciding if an infinite MPO represents a physical state is provably undecidable [69].

- **S_cycle diagnostic has thresholds from Evenbly [68]** (S_cycle ⪆ 10^{-3} requires FET). These are **heuristic** thresholds, not theorem-backed. The paper does not re-derive or challenge them for the mixed-state case.

- **Limited demonstrated resolution:** d=2 only; D up to 6 (steady state) or 5-6 (dynamics); χ up to 15; tγ up to ~10. Larger systems, larger local Hilbert spaces, and longer times are not demonstrated. The D=1 mean-field solution is physically wrong in most regimes, and the gap between D=1 and D=4 is large — the method needs D≥4 to outperform mean field.

- **Two-site unit cell limitation.** The iPEPO uses a 2-site unit cell (A_j, A_l). While this captures staggered orders (like the sXY phase), a 1-site unit cell would be more natural for uniform systems. This is relaxed in the later 2512.01781 which uses a single-site unit cell.

- **Trotter error O(τ²).** The first-order Suzuki-Trotter decomposition (Eq. 8) introduces error. The paper uses τγ=0.01-0.005, which is small but the accumulated error over many timesteps is not tracked separately from the truncation error.

- **Scalability to larger/surface-code lattices not shown.** The anisotropic XY model (Fig. 6) is the most complex demonstration, with a 2D staggered phase and correlation function extraction. But this is still a simple spin model, not a stabilizer code with the complex syndrome structure.

## Relevance to qec_twin [ours]

- **This paper's FET and WTG are the natural resolution of the itrSU truncation problem identified in 2512.01781.** The tePEPO paper (2512.01781) uses itrSU — an iterative simple update — and explicitly flags (ln 1796-1799) that itrSU's rank-1 environment becomes uncontrolled when correlation length ξ exceeds ~2 lattice sites, citing "fast-full-update" or "belief-propagation" environments as needed extensions. **FET is precisely the fast-full-update environment** (full Hilbert-Schmidt environment weighted truncation), and WTG is the gauge that makes it efficient. Integrating FET+WTG into the tePEPO framework would:
    - Replace itrSU's identity environment with the full `E_hs` from CTMRG
    - Replace the environment-blind singular value truncation with the mixed-state fidelity-optimized generalized eigenvalue truncation
    - Use WTG to recycle the environment across timesteps, offsetting the cost of CTMRG
    - Directly address the `ξ ≳ 2` control loss that 2512.01781 flags

- **However, FET introduces the CTMRG cost O(χ³_hs D⁶) at each timestep**, vs itrSU's cheaper sweeps. The tradeoff is accuracy vs cost. 2512.01781's itrSU already cuts SU QR cost from O(d⁴ D⁶ η⁶) to O(d⁴ D⁶ η³), and adding FET would re-introduce environment computation. A pragmatic middle ground: use FET only where S_cycle exceeds threshold, and WTG-alone for low-S_cycle regimes.

- **FET+WTG would help with the bath/pseudomode site problem** — but only partially. Adding bath sites inflates local dim d (e.g., d=2 → d=4 for a 2-level bath per site) and bond dimension D (to capture system-bath entanglement). The FET's environment-aware truncation would make better use of the available D by removing internal correlations, but:
    - The CTMRG cost scales as D⁶, so inflating D by adding bath sites is **expensive** — going from D=4 to D=8 costs 64× more.
    - The environment `E_hs` itself would need larger χ to faithfully represent the longer correlation lengths induced by shared bath memory.
    - FET's optimal truncation is fundamentally limited by the quality of `E_hs` (which is χ-truncated). If bath-induced correlations push ξ beyond what χ can represent, the environment quality degrades and FET's advantage over SU shrinks.
    - **Practical judgment (2026-07-09):** For modest bath augmentation (1 TLS per site, d=4, D=6-8, χ=20-30), FET+WTG would likely outperform itrSU significantly because the extra D is used for physical system-bath entanglement rather than internal correlations. For large baths (d>6) or deep memory (multi-TLS per site), the D⁶ cost becomes prohibitive regardless of algorithm.

- **The S_cycle diagnostic is directly applicable** to qec_twin's composed carrier. Our `composed.py` DEM+HMM carrier is an acyclic 1D network (no closed loops) and doesn't suffer from internal correlations. But if we build a 2D iPEPO carrier, S_cycle would be the essential diagnostic for whether our truncation is using bond dimension efficiently.

- **The 10× trace distance improvement of FET over SU** (Fig. 4-5) gives a quantitative bound on how much better a full-environment truncation is over simple update. For our decision-making: implementing FET for a 2D carrier would yield at minimum ~1 order of magnitude better accuracy at the same D, or equivalently, reach the same accuracy at D-1 or D-2.

- **Concrete reuse candidates** if we build a 2D iPEPO carrier:
    1. The FET alternating optimization (Fig. 9 + Appendix C) as a drop-in replacement for itrSU step 3 (the isometry selection after SVD)
    2. The `E_hs` construction (Fig. 7c) as the environment for the truncation objective
    3. The S_cycle diagnostic (Eq. E1) as a runtime monitor
    4. The WTG gauge fixing (ln 472-482) for environment recycling
    5. The Rayleigh quotient → generalized eigenvalue formulation (Appendix C) for the fidelity optimization

- **BUT the fundamental gating issue:** 2512.01781 states that VUMPS (boundary-MPS) consumes the environment, and the current qec_twin repo has neither CTMRG nor VUMPS for 2D lattices. FET+WTG cannot be implemented without either of these environment solvers. The cost of building a CTMRG implementation (first step) must be counted.

## How to use / trust + open questions [ours]

- **Trust level:** FULL-TEXT 精读 (15 pp incl. appendices). All equation references and figure references verified against the text. Figures not pixel-extracted — figure numbers are from text/captions. The method section (II) and appendices (A-E) are well-documented with explicit tensor diagrams (Fig. 7-9).

- **Independent-oracle-ability:** GOOD for the dissipative Ising benchmark. The hx=0 case has a **closed-form exact solution** via the Foss-Feig method [79] (Appendix D), computed independently with QuantumOptics.jl. This oracle could be reused to certify any 2D-iPEPO carrier we build. The hard core boson benchmark uses the Corner Space Renormalization method [55] as cross-reference (semi-independent, but shares the Lindblad master equation). For the sXY phase stability result, the independent cross-check is the Keldysh field theory prediction [82] — approximate theory, not exact.

- **Pre-existing memory coverage:** The companion 2512.01781 tePEPO paper has a full reading note. That note flags the itrSU limitations (uncontrolled at ξ≳2) and identifies FET/fast-full-update as the natural resolution. **This paper (2012.12233) fills that gap**: it provides the full FET+WTG algorithm, exactly the environment-aware truncation that 2512.01781 needs. The two papers are in a **complementary relationship**: 2012.12233 develops FET+WTG for iPEPO, 2512.01781 develops the FSA+Gaussian long-range machinery and itrSU efficiency. Neither has both. Combining them would be the logical next step.

- **Open questions for qec_twin:**
    1. **FET cost vs benefit for our problem sizes.** The CTMRG O(χ³ D⁶) cost with D=8-10 and χ=20-30 is substantial. Is the 10× accuracy gain worth the cost, or would a cheaper approximate environment (e.g., boundary-MPS / VUMPS with a larger χ) suffice? **Need: a benchmark** comparing FET (full CTMRG environment) vs itrSU (rank-1 environment) vs a "medium-fidelity" boundary-MPS environment for a realistic 2D dissipative model at our target D.

    2. **S_cycle threshold for mixed states.** Evenbly's S_cycle ≈ 10^{-3} threshold is for pure-state iPEPS. Does the same threshold apply for mixed-state iPEPO? The paper doesn't re-derive it — is it a property of the bond network or of the state? **Need: numerical sweep** of S_cycle vs FET-vs-WTG-only accuracy for a mixed-state problem.

    3. **FET for non-nearest-neighbor bonds.** In 2512.01781, the tePEPO applies to arbitrary-distance pairs via FSA + Gaussian expansion. The FET environment E_hs must know which pair of sites is being truncated — does the FSA's many-bond structure complicate the construction of Υ_jl? **Need: extension** of Appendix B to the FSA-generated long-range bonds.

    4. **Batch / pseudomode site cost.** Adding N_bath bath sites per lattice site inflates d → d × (d_bath)^N_bath and bond dimension D → D × (d_bath)^N_bath (roughly). At D⁶ scaling, the cost compounds rapidly. Is there a "sweet spot" — e.g., 1 TLS per site (d=4, D×2≈8-12) — where FET+WTG still runs tractably? **Need: scaling analysis** with a toy model (1D chain or small 2D cluster) before committing to a full 2D FET+WTG+iPEPO.

    5. **Diagonal correlators.** 2512.01781 flags that VUMPS cannot compute diagonal (site-to-site diagonal) correlators — CTMRG is needed. If we build FET+WTG (which already needs CTMRG for E_hs), we get diagonal correlators "for free." This is a **positive synergy** between the method and the observable need for stabilizer code syndromes (where diagonal correlations are important).

    6. **Is FET actually needed for our target physics?** Our non-Markovian wedge (shared bath / TLS / 1/f noise) adds time-memory, not just spatial correlations. The truncation quality problem from itrSU (ξ≳2) is about spatial correlation length. Non-Markovianity adds an extra dimension (time) that neither FET nor itrSU addresses — both only truncate spatial bonds at each timestep. FET helps spatial correlation accuracy but does **nothing** for the temporal/memory axis. This remains the decisive limitation for using ANY 2D-iPEPO method as the non-Markovian carrier.

- **Epistemic-status declaration:**
    - **(a) Exact (theorem-backed):** The Rayleigh quotient formulation (Appendix C) for the fidelity maximization is mathematically exact given the bond environment — equivalent to finding the optimal isometries for the defined objective. The conversion of the fidelity maximization to a generalized eigenvalue problem (ln 1353-1380) is algebraically exact.
    - **(b) Prediction band (registered falsifiable):** The claim that WTG+FET outperforms SU by ~10× in trace distance is a numerical result for the specific models and parameter ranges tested. Extrapolation to other models or larger D is a prediction. The S_cycle ≈ 10^{-3} threshold for FET vs WTG-only is a heuristic carried over from Evenbly [68] — re-verify for the mixed-state iPEPO case.
    - **(c) Heuristic (go/no-go gating only, not a premise or conclusion basis):** The CTMRG convergence tolerance of 10^{-10}, the ϵ_D' = 10^{-8} SVD retention threshold, the τγ timestep sizes, the steady-state convergence criterion ϵ_t < 10^{-6} — all are empirical design choices. The S_cycle threshold for FET activation is heuristic.

- **GT-feasibility verdict:** The method is a legitimate, benchmarked, independently-oracled 2D open-system carrier with a clear accuracy advantage over SU for the same bond dimension. FET+WTG are the **natural upgrade path** for the itrSU truncation in 2512.01781, directly addressing the ξ≳2 control loss. However, the CTMRG cost O(χ³ D⁶) is a real barrier, and the **non-Markovian limitation is orthogonal and unresolved** — FET's environmental awareness helps spatial correlations but contributes nothing to temporal memory. For qec_twin's composed carrier, FET+WTG would be a candidate if we build a 2D iPEPO infrastructure for the Markovian baseline, with bath-augmented sites as the non-Markovian extension. The cost scaling of D⁶ with bath-inflated dimensions is the binding constraint.
