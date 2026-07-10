# Full-text review -- Jacek Dziarmaga, "Time evolution of an infinite projected entangled pair state: a gradient tensor update in the tangent space" (arXiv:2205.11067 / PRB 106, 014304 (2022))

> **Provenance (2026-07-09): FULL-TEXT read (精读).** PDF text extracted via PyMuPDF
> from `outputs/papers/pepo_survey/2205.11067.txt` (9 pages / 994 lines). All section/Eq/Fig
> refs from that text. Figures not pixel-extracted -- figure facts = captions and numbers
> stated in text.
>
> **ID/title verified.** arXiv:2205.11067v3 IS the paper: "Time evolution of an infinite
> projected entangled pair state: a gradient tensor update in the tangent space" by
> Jacek Dziarmaga (Jagiellonian University). Published PRB 106, 014304 (2022). Method
> is named "gradient tensor update (GTU)" (Sec. II, ln 87). No mismatch.
>
> **Second full-text verification pass (2026-07-09, pre-engine-build):** re-read the original
> end-to-end. All load-bearing claims confirmed (Eqs. 1–9; SVDU→NTU→GTU Eq. 8; reduced-tensor
> metric D²d×D²d; +20–30% past NTU with NTU itself dropping the error "several times" from SVDU;
> KZ τ_Q = 12.8 at D=3, 3–4× past plain NTU, exponent 0.37 vs exact 0.386; hx=2hc: GTU D=6 >2×
> the FU-D=8 evolution time; hx=hc: "somewhat longer"). Three details ADDED: (i) the GTU stage's
> registered truncation-error STOPPING thresholds are 1−O > 2e-6 (hx=2hc) and 5e-6 (hx=hc)
> (Fig. 7 caption) — a concrete overlap-based stopping-rule precedent; (ii) the NTU initialization
> inside GTU uses clusters LARGER than the original NTU paper's (Fig. 2 caption: "the NTU clusters
> in the bottom are larger than in Ref. 74"); (iii) the "GTU D=8 goes even further" row in the
> findings table is a FIGURE-read (Fig. 4) — the text itself demonstrates only the D=6 claims.

## Metadata [paper]
- **Author / affiliation.** Jacek Dziarmaga -- Institute of Theoretical Physics, Jagiellonian University, Krakow, Poland (`dziarmaga@th.if.uj.edu.pl`).
- **Venue / status.** arXiv:2205.11067v3, 11 Jul 2022. **Published: Phys. Rev. B 106, 014304 (2022).** Categories: quant-ph; cond-mat.str-el.
- **Type.** Method + numerical benchmark: a new iPEPS bond-dimension truncation algorithm (GTU) for real-time evolution, benchmarked on the 2D quantum Ising model (sudden quench + Kibble-Zurek ramp). Preceded by the author's own NTU (Neighbourhood Tensor Update, Ref. 74, PRB 2021).
- **Lineage.** Directly extends the author's own NTU (Dziarmaga 2021, PRB 104, 094411) and builds on the long iPEPS time-evolution program (Full Update FU, Ref. 57; Simple Update SU). GTU is the highest-accuracy iPEPS truncation in this line, operating in the tangent space of the iPEPS variational manifold. Also related to variational contraction methods (Vanderstraeten et al., Ref. 103).

## Executive summary [paper]
The paper introduces **gradient tensor update (GTU)**, a bond-dimension truncation method for iPEPS real-time evolution that goes beyond all previous local/neighbourhood approximations. After each Suzuki-Trotter gate increases the bond dimension from `D` to `rD`, GTU directly maximizes the **overlap per site** `O = (|⟨ψ|φ⟩|²/⟨ψ|ψ⟩)^{1/N}` between the exact high-bond iPEPS `|φ⟩` and the truncated `D`-bond iPEPS `|ψ⟩` (Eq. 7-9). The optimization operates in the **tangent space** of the iPEPS variational manifold: small variations `|δψ⟩` orthogonal to `|ψ⟩` (Eq. 1) define a quadratic cost function `F = ‖|φ⟩−|ψ⟩−|δψ⟩‖²/⟨ψ|ψ⟩` (Eq. 2), whose minimizer is `δA''_μ = G^{-1}_{μν} J_ν` (Eq. 5). Here `G_{μν}` is the **Gramm-Schmidt metric tensor** (Eq. 3) and `J_μ` the **gradient** (Eq. 4), both computed by **corner transfer matrix renormalization group (CTMRG)**. A line search along the steepest-descent direction (parametrized by scalar `x`, Eq. 6) optimizes the logarithmic overlap `O_x` (Eq. 7). GTU is the final stage of a **3-stage pipeline**: `SVDU → NTU → GTU` (Eq. 8). The SVDU (SVD update) provides an initial SVD truncation of the rD bond; NTU (neighbourhood tensor update) optimizes in a local 2x2 cluster; GTU then refines globally in the tangent space. Benchmarks on the 2D transverse-field Ising model show GTU with `D=6` achieves **longer evolution times** than FU or NTU with `D=8` (Fig. 4), and extends Kibble-Zurek ramp simulations 3-4x beyond the NTU limit (Fig. 5). The extra truncation-error reduction from GTU beyond NTU is moderate (20-30%, App. B), but this reduction translates to significantly extended evolution times because it delays the runaway truncation-error accumulation that terminates the simulation.

## Method (deep) [paper]

**iPEPS ansatz and Trotter evolution (Sec. I-II, Figs. 1-2):**
The iPEPS is an infinite checkerboard of two tensors `A` and `B`, each with one physical index (dimension `d`) and four bond indices (dimension `D`). A two-site Trotter gate applied to each horizontal NN bond between `A` and `B` increases the bond dimension from `D` to `rD` (the gate rank `r`). The resulting exact state is `|φ⟩`. The goal is to find a new iPEPS `|ψ⟩` with tensors `A''` and `B''` (bond dimension restored to `D`) that best approximates `|φ⟩`. The tensors are optimized in a loop `→ A'' → B'' →` until convergence.

**Tangent space optimization (Sec. II, Eqs. 1-7):**
Consider small variations `A'' → A'' + δA''`. To linear order, the state variation is:
```
|δψ⟩ = (1 - |ψ⟩⟨ψ|/⟨ψ|ψ⟩) Σ_μ δA''_μ |∂_μ ψ⟩   (Eq. 1)
```
where index `μ` numbers the elements of tensor `δA''` and `∂_μ` is the derivative w.r.t. element `A''_μ`. The projection orthogonal to `|ψ⟩` ensures variations stay in the tangent space. The cost function is:
```
F = ‖|φ⟩−|ψ⟩−|δψ⟩‖²/⟨ψ|ψ⟩ = δA''*_μ G_{μν} δA''_ν - δA''*_μ J_μ - J*_μ δA''_μ + F₀   (Eq. 2)
```
The **Gramm-Schmidt metric tensor**:
```
G_{μν} = ⟨∂_μ ψ|∂_ν ψ⟩/⟨ψ|ψ⟩ - (⟨∂_μ ψ|ψ⟩/⟨ψ|ψ⟩)(⟨ψ|∂_ν ψ⟩/⟨ψ|ψ⟩)   (Eq. 3)
```
The **gradient**:
```
J_μ = ⟨∂_μ ψ|φ⟩/⟨ψ|φ⟩ - ⟨∂_μ ψ|ψ⟩/⟨ψ|ψ⟩   (Eq. 4)
```
where the approximation `⟨ψ|φ⟩ ≈ ⟨ψ|ψ⟩` is used (accurate near convergence). The quadratic cost function is minimized by:
```
δA''_μ = G^{-1}_{μν} J_ν   (Eq. 5)
```
Beyond the linear approximation, the solution (5) is used to construct a line:
```
A'' + x[δA'' - A'' (J*_μ δA''_μ)]   (Eq. 6)
```
where `x` is a real variational parameter. For small `x`, `|ψ_x⟩ ≈ |ψ⟩ + x|δψ⟩` along the steepest-descent direction. The optimal `x` is found by **line search** maximizing the logarithmic overlap:
```
O_x = (|⟨ψ_x|φ⟩⟨φ|ψ_x⟩| / ⟨ψ_x|ψ_x⟩)^{1/N}   (Eq. 7)
```
where `N → ∞` for the infinite lattice. The overlap per site is finite (no orthogonality catastrophe) and computable via CTMRG.

**CTMRG computation of G and J (Sec. III, Eqs. 10-12):**
The derivative `|∂_ν ψ⟩` is a sum over all sites `s` on sublattice A of `|ψ_s^ν⟩` -- iPEPS `|ψ⟩` with tensor `A''` missing at site `s` (Fig. 3, Eq. 10). The gradient becomes:
```
J_μ = N [ ⟨ψ_0^μ|φ⟩/⟨ψ|φ⟩ - ⟨ψ_0^μ|ψ⟩/⟨ψ|ψ⟩ ] ≡ N (j_μ^φ - j_μ^ψ)   (Eq. 11)
```
where `0` is a reference site. The metric tensor:
```
G_{μν} = N ⟨ψ_0^μ|/⟨ψ|ψ⟩ Σ_s |ψ_s^ν⟩_c   (Eq. 12)
```
where `|ψ_s^ν⟩_c = |ψ_s^ν⟩ - j_ψ^{ν*} |ψ⟩` is a **connected derivative** -- orthogonal to `|ψ⟩` by construction. The sum over `s` is non-zero only within a correlation range of site 0, enabling efficient CTMRG evaluation. Both `J_μ` and `G_{μν}` are computed by CTMRG in the same way as 1-site expectation values and connected correlation functions (Corboz 2014/2016).

**Reduced tensors (Appendix A, Fig. 6):**
For computational efficiency, the optimization is not on full tensors `A'',B''` (size `D⁴d`) but on reduced matrices `M_A, M_B` of size `D²d`. The reduction contracts QR-decomposed gate tensors with the isometries `Q_A, Q_B`, which remain fixed during optimization. This shrinks the metric from a `D⁴d × D⁴d` matrix to a `D²d × D²d` matrix, and makes CTMRG contraction a factor `D²` more compact (ln 876-921).

**The 3-stage pipeline (Eq. 8):**
```
SVDU → NTU → GTU
```
- **SVDU (SVD update):** After `A·G_A = Q_A R_A`, `B·G_B = Q_B R_B` (QR), `R_A R_B^T = U_A S U_B^T` (SVD), truncate `S` to `D` singular values, set `M_A = U_A S^{1/2}`, `M_B^T = S^{1/2} U_B^T`. No further optimization (Fig. 6a-e).
- **NTU (neighbourhood tensor update):** Further optimize `M_A, M_B` variationally to minimize the Frobenius norm of the difference between the exact and approximate diagrams within a 2x2 cluster environment (Fig. 2, bottom panel).
- **GTU (gradient tensor update):** Further refine `M_A, M_B` via the tangent-space gradient optimization above, using CTMRG to compute the metric and gradient.

**Overlap per site as quality monitor (Eq. 9):**
After each stage, the overlap `O = (|⟨ψ|φ⟩⟨φ|ψ⟩|/⟨ψ|ψ⟩)^{1/N}` is computed. In benchmarks (App. B, Figs. 7-8): NTU drops error (1-O) several-fold from SVDU; GTU adds another 20-30% reduction.

## Findings + numbers [paper]

| Result | Numbers |
|---|---|
| Sudden quench to `h_x = 2h_c` | GTU `D=6` evolution time >2x longer than FU `D=8`; GTU `D=8` goes even further before energy departs by 0.01 (Fig. 4). |
| Sudden quench to critical `h_x = h_c` | GTU `D=6` achieves somewhat longer evolution time than FU/NTU `D=8` (Fig. 4). Progress in time with increasing `D` remains slow at the critical point. |
| Kibble-Zurek ramp | GTU with `D=3` reaches quench times `τ_Q = 12.8` -- 3-4x longer than plain NTU (`τ_Q ≈ 3-4`, Ref. 75). Power-law scaling `Q ∝ τ_Q^{-3×0.37}` approaches the exact exponent `-3×0.386` (Fig. 5). |
| Truncation error reduction (GTU vs NTU) | 20-30% additional error reduction after NTU initialization (App. B, Fig. 7). |
| Truncation error reduction (GTU vs SVDU) | Order-of-magnitude reduction from SVDU baseline (App. B, Fig. 8). |
| Maximum D demonstrated | Sudden quench: `D=6-8`; Kibble-Zurek: `D=3` (long-timescale ramp, limited by local-dim budget for `D` at long `τ_Q`). |
| Line search | `x` optimised via direct line search on overlap `O_x` (Eq. 7) beyond quadratic approximation. |

## Limitations [paper]

- **GTU overhead is significant.** The gradient and metric require CTMRG computation of connected correlation functions (Eq. 12), which is the computational bottleneck. The paper does not give explicit cost scaling, but CTMRG-connected-correlation evaluation is substantially costlier than NTU's Frobenius-norm minimization on a 2x2 cluster. Practical trade-off: GTU extra 20-30% error reduction vs cost. From the quench benchmarks, the extra evolution time gained extends well beyond what NTU alone achieves, but the per-step cost is higher.

- **Diminishing returns at the critical point.** Even with GTU, progress in evolution time when quenching to `h_x = h_c` (gapless) is slow when increasing `D`. This is inherent: quasiparticle pairs created at the critical point separate ballistically, requiring bond dimension to grow exponentially in time (Calabrese-Cardy quasiparticle horizon, Ref. 85). GTU gets closer to optimal `D` use but cannot overcome this fundamental barrier.

- **Oscillations from truncation at the longest quench times.** For the longest `τ_Q = 12.8` Kibble-Zurek ramp, small extra oscillations appear on top of the KZ excitation energy for smaller `t/ˆt` where the KZ energy is small (ln 629-633). These are induced by truncation at the fixed bond dimension `D=3`. The problem worsens for even longer quench times.

- **Demonstrated only on one model (2D quantum Ising).** The 2D transverse-field Ising model (Eq. 13) is the sole benchmark. Performance on models with larger local Hilbert spaces, fermions, or more complex (e.g. frustrated) Hamiltonians is not shown. The GTU formalism is general but its practical viability on other models remains unproven.

- **Single-site unit cell only.** The checkerboard pattern (tensors `A` and `B`) is a 2-site unit cell. The method's extension to larger unit cells (needed for e.g. the planar code, Kagome, or inhomogeneous systems) is not discussed.

- **No comparison with variational contraction truncation.** The paper mentions variational methods (Vanderstraeten et al., Ref. 103) as a possible future improvement direction (ln 643-644), but does not compare GTU's performance against the variational contraction approach to truncation.

- **No explicit cost scaling reported.** While the GTU metric/gradient compute cost via CTMRG is noted as the bottleneck, no wall-clock times, FLOP counts, or convergence iteration counts are reported, making quantitative cost-benefit analysis difficult from the paper alone.

## Relevance to qec_twin [ours]

**This paper addresses the central iPEPS truncation problem for 2D lattice simulation.** Our `forward/scalable/` carrier is currently 1D-MPS (`mps_forward.py`) and composed DEM (`composed.py`); we identified that scaling to surface-code geometries will require a 2D tensor-network carrier (memory: `project-fulld-1dmps-wall-and-2dpeps`). When we move to a 2D iPEPO (mixed-state) carrier for the surface code, the truncation problem is the decisive bottleneck -- every Trotter or operator-application step enlarges bond dimensions that must be truncated back. GTU is the highest-accuracy truncation in the iPEPS literature, and understanding its machinery is essential before deciding on a truncation strategy.

1. **[ours] Can GTU handle the `ξ > 2` regime where itrSU fails?** The tePEPO paper (Dunham 2025, 2512.01781) flags that at correlation length `ξ ≳ 2` lattice sites, the simple-update rank-1 environment approximation (which itrSU uses) begins to under-capture correlations -- they call for full-environment (fast-full-update) or belief-propagation truncation. GTU is exactly that: it works in the **full iPEPS tangent space** with **CTMRG-computed metric**, not a rank-1 environment. The metric tensor `G_{μν}` (Eq. 3) captures connected correlations between all derivative tensors (Eq. 12), which is a global, environment-aware computation. **Yes -- GTU is designed precisely for the regime where local approximations (SU, NTU) break down**, because the Gramm-Schmidt metric sums connected derivatives over all sites within correlation range. This makes GTU a natural candidate for the `ξ > 2` regime.

2. **[ours] Can GTU handle the shared-bath-induced correlation lengths?** Shared baths induce spatial correlations across the entire lattice (e.g. collective relaxation sets up long-range `ZZ` entangling interactions through the bath). GTU's CTMRG-based metric computes correlations via `|ψ_s^ν⟩_c` (connected derivatives) summed over all sites `s` (Eq. 12), with non-zero contributions only within correlation range. The CTMRG environment bond dimension `χ` controls the range of correlations captured -- by increasing `χ`, the environment can resolve longer correlation lengths. **GTU can in principle handle arbitrarily long correlation lengths as long as `χ` is sufficient to represent the environment**, though the computational cost scales with `χ`. This is a crucial advantage over itrSU's fixed rank-1 environment.

3. **[ours] Applicability to density-matrix PEPO (mixed states).** The paper treats pure-state iPEPS (`|ψ⟩`). Extending GTU to mixed-state iPEPO (density-matrix PEPS with `d²` physical leg) is:
   - **Formally straightforward.** The tangent-space formalism (overlap maximization, Gramm-Schmidt metric, gradient) carries over to the Frobenius inner product `⟨ρ|σ⟩ = tr(ρ†σ)` for vectorized density matrices. The metric becomes the Gramm-Schmidt metric in the space of vectorized PEPO tensors.
   - **Practically costlier.** The local dimension becomes `d²` instead of `d` (or `d` for each bra/ket). The reduced-tensor dimension grows from `D²d` to `D²d²`. The CTMRG contraction (already the bottleneck) scales correspondingly worse. For the surface code with `d=2` physical qubits, `d²=4` is manageable; for `d>2` (qutrits including leakage), `d²=9` is more taxing but still plausible.
   - **The metric tensor size.** For reduced tensors of shape `(D²d²)`, the metric is `(D²d² × D²d²)`. For `D=4, d=2`, this is `64×64` (manageable); for `D=6, d=2`, it's `144×144`. The CTMRG computation of connected correlations (not just the inversion) is the real bottleneck.
   - **No existing iPEPO tangent-space truncation in the literature.** The paper's tangent-space machinery would be a natural generalization, but no such extension has been published. It would be a methodological contribution.

4. **[ours] The GTU pipeline as a template for our 2D truncation.** The `SVDU → NTU → GTU` cascade (Eq. 8) provides a clear design: start with minimal SVD truncation (cheap), refine with a local-environment variational update (moderate), finish with a global tangent-space optimization (costly but most accurate). For a 2D surface-code carrier we would likely adopt the same layered approach, using GTU only when cheaper truncations (itrSU, NTU) are insufficient, i.e. in the high-correlation / long-evolution-time regime.

5. **[ours] The overlap objective as a truncation quality metric.** GTU maximizes the overlap per site `O` (Eq. 9) -- the same metric the paper uses to monitor truncation error (App. B). This is the **natural objective for truncation** in a 2D tensor-network carrier, as it directly measures how well the truncated state represents the exact one. Our composed carrier currently lacks such a global truncation quality metric; the overlap per site (or its PEPO analogue, the fidelity per site) would be valuable.

6. **[ours] The CTMRG bottleneck and its implications for GPU.** The paper's CTMRG computation is CPU-targeted (as typical for iPEPS codes ca. 2022). For GPU implementation of GTU on a surface-code iPEPO carrier, the CTMRG contraction (iterative corner transfer matrix renormalization to convergence) would need to be GPU-accelerated. This is a non-trivial engineering task but is well-suited to GPU tensor contractions. The alternative variational contraction methods (Vanderstraeten Ref. 103) may have better GPU mapping; this would need benchmarking.

7. **[ours] Constraints on practical feasibility.** The paper only demonstrates `D` up to 8 (sudden quench) and `D=3` (Kibble-Zurek). For surface-code carriers, `D` would likely need to be larger (Dunham's tePEPO reaches `D=10` with itrSU). GTU's CTMRG-connected-correlation computation could become **prohibitively expensive** for `D > 10` on the 2D square lattice with physical dim `d²` (mixed state), especially with the additional bond-dimension overhead from shared-bath correlations. **A GTU-for-PEPO implementation's viable `D` range is an open engineering question.**

8. **[ours] What GTU does NOT do.** GTU is a truncation method for a **pure-state iPEPS time-evolution** step. It does NOT provide:
   - A **mixed-state** representation (need PEPO/vectorized Liouvillian extension)
   - A **non-Markovian** memory framework (the evolution is unitary / Lindblad by construction)
   - **Certified error bounds** for the truncation (overlap monitoring is diagnostic, not a bound)
   - An **environment contraction** for observables (CTMRG for truncation is separate from CTMRG for expectation values)

## How to use / trust + open questions [ours]

- **Trust level:** FULL-TEXT 精读 (9 pp incl. appendices). Figures not pixel-extracted but the text is self-contained (no figure-dependent claims without textual backup). Equations transcribed verbatim from the PyMuPDF text extraction.

- **Independent oracle / verifiability:** The 2D quantum Ising model with a known critical point `h_c = 3.04438(2)` (Blote & Deng 2002, Ref. 83) provides an independent reference. Kibble-Zurek scaling predictions (Eq. 16: `Q ∝ ξ^{-3} ∝ τ_Q^{-3×0.386}`) give a quantitative falsifiable check. The paper demonstrates approach to this scaling (exponent 0.37 vs 0.386 at longest `τ_Q`). No exact closed-form solution for the time-evolved state exists, but the convergence-in-`D` evidence is self-consistent.

- **Open questions for a 2D PEPO implementation:**
  (1) What is the cost scaling with `D` for CTMRG computation of the connected-correlation metric (Eq. 12) in a mixed-state (PEPO) setting with `d²` physical leg? Specifically, how does the `χ` (CTMRG environment bond dim) needed for convergence grow with correlation length from shared-bath effects?
  (2) Is the 20-30% per-step truncation-error improvement sufficient to justify GTU over lower-cost truncations (e.g., the itrSU from Dunham 2025) in a surface-code evolution where many Trotter steps are needed? The per-step improvement compounds, but the cost per step might dominate.
  (3) Can the GTU gradient and metric be approximated with the **variational contraction** approach (Vanderstraeten et al. Ref. 103) for better GPU efficiency?
  (4) GTU optimizes `A''` and `B''` in alternating sweeps. For a `K`-site unit cell surface code, would this sweep be `K` times more expensive, or can symmetries (stabilizer structure) reduce the parameter count?
  (5) Does the tangent-space optimization risk getting trapped in local minima when the SVDU→NTU initialization is poor? The paper initializes GTU from NTU (robust), but the question arises for regimes NTU itself handles poorly.
  (6) Can the overlap `O` be used as a **stopping criterion** for truncation quality in the carrier, replacing heuristic truncation-error thresholds?

- **GT-feasibility verdict:** GTU is the highest-accuracy iPEPS truncation method and is the natural candidate for a 2D tensor-network carrier in the `ξ > 2` regime where SU/NTU/itrSU fail. However, it has substantial per-step cost (CTMRG-connected-correlation metric), has been demonstrated only for pure-state `D ≤ 8`, and extending it to mixed-state (PEPO) surface-code carriers is an open engineering problem. **GTU is not drop-in ready for our use case, but its tangent-space formalism is the correct target for a high-accuracy 2D truncation -- and a full-environment alternative to itrSU that we can benchmark against.** The tractable `D` range in a mixed-state code with shared-bath correlation lengths must be determined by prototyping.
