# Full-text review — J. Dziarmaga, "Time evolution of an infinite projected entangled pair state: a neighborhood tensor update" (arXiv:2107.06635)

> **Provenance (2026-07-09): FULL-TEXT read (精读).** PDF (arXiv:2107.06635v1, 14 Jul 2021) →
> `outputs/papers/pepo_survey/2107.06635.txt` (PyMuPDF, 11 pages / 1109 lines). All §/Eq/Fig/Table refs from that text.
>
> **ID/title verified.** arXiv:2107.06635 IS the paper: Dziarmaga, PRB 104, 094411 (2021). Title matches "Time evolution of an infinite projected entangled pair state: a neighborhood tensor update." The method is explicitly named **neighborhood tensor update (NTU)**.

## Metadata [paper]
- **Author / affiliation:** Jacek Dziarmaga (Jagiellonian University, Institute of Theoretical Physics, Krakow, Poland — corresponding `dziarmaga@th.if.uj.edu.pl`).
- **Venue / status:** Phys. Rev. B 104, 094411 (2021). Published. arXiv:2107.06635v1 [quant-ph], 14 Jul 2021.
- **Type:** Method + numerical simulation (tensor-network truncation algorithm, benchmarked on 2D quantum Ising model — sudden quench real-time evolution + finite-temperature thermal states).

## Executive summary [paper]
The paper introduces the **neighborhood tensor update (NTU)**, an intermediate truncation scheme for iPEPS time evolution that sits between the Simple Update (SU) and Full Update (FU) in the environment-size hierarchy. NTU uses the **nearest-neighbor (NN) tensor cluster** — the two sites being truncated plus their six adjacent bonds — as the environment providing the error metric. This NN cluster is small enough to be **contracted exactly** (no approximations, no CTMRG), yielding a metric tensor **g** that is provably **Hermitian and non-negative down to machine precision** (SSII, Fig. 4). The exactness of g is the central advantage: the quadratic truncation-error measure `e = (MAM_B^T - RAR_B^T)^\dagger g (MAM_B^T - RAR_B^T)` (Eq. 2) is a well-behaved, non-negative quadratic form with no sign-breaking or non-Hermiticity from approximate contraction. The cost of computing g scales as O(D^8), but these are pure matrix multiplications that are **fully parallelizable**. On the 2D quantum Ising model, NTU is benchmarked against SU, SVDU, and FTU/FU for (i) unitary real-time evolution after a sudden quench (SSIII, Fig. 6-7) and (ii) thermal state preparation via imaginary-time evolution of a manifestly Hermitian purification (SSIV-V, Figs. 9-12). NTU reproduces FU-quality results for correlation lengths up to **xi ~ 20 lattice sites**, whereas SU is limited to xi ~ 2. The paper also introduces two complementary schemes: the **local SVD update (SVDU)**, cheaper-than-SU, and the **full tensor update (FTU)**, a variant of FU with the same reduced-tensor formalism.

## Method (deep) [paper]

**The iPEPS truncation problem (SSII, Figs. 1-3):** After applying a two-site Suzuki-Trotter gate G to nearest-neighbor iPEPS tensors A and B, the bond index dimension between them grows from D to D*r (where r is the gate rank). Truncation back to D is required. The problem: given an exact (untruncated) product `R_A R_B^T` (Fig. 2b), find the best approximation `M_A M_B^T` (Fig. 2d) that minimizes an error measure. Different truncation schemes differ in which environment defines the error measure.

**SVDU (SSII, Fig. 1-2):** The simplest scheme. The SVD of the local `dD^3 x dD^3` matrix (Fig. 1b) is truncated to D singular values. Cost ~O(D^9), reducible to O(D^5) by QR reduction to smaller matrices `R_{A,B}` (Fig. 2). The Frobenius norm error measure treats ALL directions equally — zero modes are preserved as accurately as dominant modes, wasting bond dimension. No bond-weight metric (inverse-free, though).

**SU (Simple Update, described as context):** Inserts diagonal bond tensors `lambda_i` on all bonds (the "nearest tensor environment"), giving a metric `g_SU = 1_d otimes 1_d otimes prod_j lambda_j` (Eq. 1) where j runs over the six bonds emanating from the NN pair. The weights give different directions different importance. Cost O(D^5). **Caveat**: requires inversion of `lambda_i -> lambda_i^{-1}` after every gate, which can be problematic.

**NTU — the core method (SSII, Fig. 4):** The environment is the **nearest-neighbor tensor cluster**: the two central sites plus their six adjacent bond tensors (four vertical/horizontal neighbors), shown in Fig. 3(b) and Fig. 4. This cluster is contracted exactly through these steps (Fig. 4a-d):
1. Define **double iPEPS tensors** by contracting pairs of corresponding external bra and ket indices.
2. Define **edge double tensors** by contracting pairs of corresponding external bra/ket indices of boundary tensors.
3. Define **double isometries**.
4. Assemble the metric g from these components (Fig. 4d,e).

The contraction yields a metric `g` of size `(D^2 x D^2)` that is:
- **Hermitian** by construction (bra/ket symmetry)
- **Non-negative** (positive semi-definite) down to machine precision
- **Exact** — no CTMRG truncation/approximation

Cost: O(D^8) for the optimal contraction sequence. But this consists solely of matrix multiplications (BLAS level 3), **fully parallelizable** across all bonds in the lattice (all NN pairs can be processed independently).

**The two key NN bonds** parallel to the truncated bond (Fig. 4, the bonds connecting left and right sides of the environment) are what distinguish NTU from SU/SVDU: they **prevent virtual loop entanglement from being built into the iPEPS and parasitically consuming bond dimension** (SSII, ln 271-272).

**Optimization procedure (SSII, Fig. 5):** With metric g, matrices M_A, M_B are iteratively optimized:
```
M_A = pinv(g_A) J_A   (Eq. 4, for fixed M_B)
M_B = pinv(g_B) J_B   (for fixed M_A)
```
Iterated to convergence `-> M_A -> M_B ->` (Eq. 5). The pseudo-inverse tolerance is dynamically adjusted. Thanks to the exactness of g in NTU, the optimal tolerance is close to machine precision. After convergence, a final SVD `M_A M_B^T = U_A S U_B^T` and balanced absorption `M_A' = U_A S^{1/2}`, `M_B'^T = S^{1/2} U_B^T` ensures symmetric truncation.

**FTU (Full Tensor Update, SSII, Fig. 3a):** Same formalism as NTU but the environment is the **infinite** iPEPS (via approximate CTMRG). Cost O(D^{10}-D^{12}) with approximate, non-Hermitian metric. Serves mainly as a benchmark in this paper. Distinct from standard FU in using the same reduced-tensor decomposition (isometries Q_{A,B} + reduced matrices R_{A,B}) as NTU/SVDU.

**Hierarchy (SSVI, Conclusion, ln 884):**
```
SVDU < SU < NTU < FTU ≈ FU
```
(ordered by increasing environment size and convergence rate with D)

## Cost comparison

| Scheme | Formal cost | Parallelizable? | Metric quality |
|--------|-------------|-----------------|----------------|
| SVDU   | O(D^5)      | No (sequential SVD) | Frobenius (uniform) |
| SU     | O(D^5)      | No (sequential SVD + bond-tensor inversion) | Diagonal bond weights |
| **NTU** | **O(D^8)** | **Yes (pure matmul, fully parallelizable)** | **Exact, Hermitian, non-negative** |
| FTU    | O(D^{10}-D^{12}) | Limited (CTMRG is sequential across RG steps) | Approximate, often non-Hermitian |
| FU     | O(D^{10}-D^{12}) | Limited (same CTMRG) | Approximate, often non-Hermitian |

**Critical nuance** (SSVI, ln 886-898): Although NTU is formally O(D^8) vs SU's O(D^5), the D^8 is **fully parallelizable matrix multiplication** (BLAS 3) while the D^5 involves **sequential, non-parallelizable SVD**. In practice, for D up to ~12, NTU's wall-clock cost is comparable to SU's. Similarly, relative to FU's D^{10}-D^{12}, NTU's D^8 is far cheaper, partially compensating for NTU's slower convergence with D.

## Correlation length performance

- **SU (Simple Update):** correlation length xi ≲ 2 lattice sites (Fig. 9, ln 626-631). At hx = 2.9 (near quantum critical point), SU with D=14 *still* fails to converge to the FU benchmark. SU simply cannot capture correlations beyond ~2 sites because its rank-1 bond-weight metric has no long-range information.

- **NTU:** accurate up to xi ~ **20 lattice sites** — demonstrated explicitly at hx = 2.5 where xi ≈ 22 at the relevant beta (ln 814-815), and NTU converges with D = 5-6 (Table II, Fig. 11). Even at hx = 2.9 (near critical), NTU achieves xi ~ 15 at moderate D (ln 682-684) and converges to the FU benchmark for D = 7-9 (Table I, Fig. 10a). The NN environment provides enough information to capture correlations at this scale.

- **FTU/FU:** converge fastest with D (D = 5 is enough for hx = 2.5, 2.9), but require expensive CTMRG.

**Correlation length is NOT the sole factor** (ln 728-818): At hx = 2.5, xi ≈ **22** (the longest of all three test cases) yet NTU converges already at D = 5 — even SVDU converges well. At hx = 2.9, xi ≈ 15 (shorter) but both SVDU and NTU struggle more. The paper argues that the **quantum nature of the correlations** (strong quantum fluctuations near the quantum critical point) matters more than correlation length itself.

## SVDU and FTU as sub-algorithms

**SVDU (SVD Update, SSII, Figs. 1-2):** The simplest scheme in the paper's family. No metric tensor at all — Frobenius-norm minimization. Cost O(D^5). Demonstrates an **important warning** (SSV, Figs. 10-11): as D increases beyond 6, SVDU accuracy can **decline** rather than improve (the "SVDU drift" at D = 7, 8, 9 in Fig. 10a). The mechanism: at low D, the Frobenius uniform-weight metric accidentally weights directions similarly to the true environment; at higher D, the mismatch becomes more damaging. This is a caution against assuming monotonic convergence with D for local schemes.

**FTU (Full Tensor Update, SSII, Fig. 3a):** Same optimization formalism as NTU (iterative MA-MB optimization with metric g, Eq. 4-5) but g comes from approximate CTMRG of the infinite environment rather than exact NN-cluster contraction. Shows the fastest convergence with D (D=5 converged), but suffers from **(i) sudden crashes** during real-time evolution (ln 493-494) and **(ii) non-Hermitian/non-positive metric** due to CTMRG truncation, which degrades stability.

## Benchmark results

### Sudden quench (SSIII, Fig. 6-7)
- Real-time evolution of the 2D quantum Ising model after quench from infinite field to hx = 2hc, hc, hc/10.
- dt = 0.01, second-order Suzuki-Trotter, chi = 4D.
- NTU with D=12 matches FU with D=8 in simulation time but produces **longer stable evolution** than SVDU at all three hx values (Fig. 6).
- At hx = hc (critical), FTU still outperforms NTU as expected (the correlation range is longest here; Fig. 7 shows connected correlations).
- NTU never suffers the sudden crashes that FTU does.

### Thermal states (SSIV-V, Figs. 9-12)
- Manifestly Hermitian purification: the thermal state `rho(beta) = e^{-beta H}` is represented as an iPEPO via purification, with an explicit Hermitian parametrization (Fig. 8: rank-6 tensor O_a basis of Hermitian operators, d^2-dim physical index). The real-tensor parametrization (no complex arithmetic) speeds up computation by ~4x.
- Imaginary time evolution with dbeta = 0.0025, second-order Trotter.
- **Three test regimes:**
  1. **hx = 2.9 (near critical), weak bias hz = 5e-4** (Fig. 10a): SU fails even at D=14. SVDU gets close at D=6 then drifts away at D=7-9. NTU converges to FTU benchmark at D=7-9. Max correlation length xi ~ 15 at beta ~ 1.44-1.48.
  2. **hx = 2.9, stronger bias hz = 1e-2** (Fig. 10b): Shorter correlations (xi ~ 4). NTU converged already at D >= 6. SVDU drift much less severe.
  3. **hx = 2.5 (further from critical), weak bias hz = 5e-4** (Fig. 11): xi ~ **22** (longest), but NTU converged at D >= 5. SVDU with D=5-8 also converged. The quantum nature of correlations (not just correlation range) matters.
- **Critical temperature extraction (Tables I-II, Fig. 12):** NTU yields Tc estimates consistent with QMC and FU, albeit with wider error bars and overestimated exponent `1/(beta delta)`.

## Limitations [paper]
- **NTU cost O(D^8) is still formal-scaling heavy** — though parallelizable, D > ~14 becomes prohibitive. Dziarmaga notes (ln 891-893) that NTU's slower convergence with D vs FTU is partially offset by its ability to reach higher D due to better stability, but the absolute D ceiling is around 12-14.
- **Sudden-crash risk for FTU** (real-time evolution, ln 493-494) is not present in NTU.
- **SVDU shows non-monotonic convergence** (accuracy degrading for D > 6, Fig. 10a) — a caution for anyone using Frobenius-norm truncation without environment weighting.
- **Trotter error O(dt^2)** from the second-order Suzuki-Trotter decomposition is standard and not addressed.
- **Demonstrated only for D up to 12** (real-time) and D up to 9 (thermal), d=2 (spin-1/2), single-site unit cell, square lattice. Larger D, larger local dim, multi-site unit cells, and general graphs not shown.
- **NTU environment is still finite** — it cannot capture correlations longer than the environment's range (xi >> the cluster size will degrade accuracy). The paper demonstrates xi ~ 20 works for a 2x2+environment cluster; larger xi would presumably require larger clusters or FU.

## Critical relevance to qec_twin

### Q1: Could NTU replace itrSU in tePEPO (2512.01781) to handle correlation lengths xi > 2?

**Yes — this is the most directly actionable finding in this paper.**

The tePEPO paper (2512.01781) uses an **iterative simple update (itrSU)** for truncation and explicitly flags (ln 1796-1799) that SU's rank-1 environment approximation breaks down for correlation lengths xi > 2 — the exact regime where their long-range Rydberg and dissipative Ising benchmarks operate (they demonstrate xi ~ 2-10). Their response is to flag "full-environment (fast-full-update) or belief-propagation truncation" as needed extensions (ln 1799). They do NOT consider NTU.

This Dziarmaga paper demonstrates:
- NTU handles xi up to ~20 lattice sites (factor 10x better than SU's xi ~ 2).
- NTU cost O(D^8) is parallelizable; the tePEPO itrSU is O(d^4 D^6 eta^3) for the QR step alone (their claimed savings), but this is iterative across 5 bonds and suffers from the SU environment limitation.
- NTU's proven Hermitian/non-negative metric is **guaranteed stable** — a property itrSU cannot provide because SU's bond-tensor metric is only a diagonal approximation.
- **NTU would not explode tePEPO's cost** because tePEPO already works at modest D (4-10), and D^8 for D=10 is manageable (10^8 ~ 1e8, fine for BLAS matmul). Also, tePEPO's Gaussian-sum factorization means `k_max` separate apply-truncate steps per timestep — each would use NTU individually, keeping per-step cost at D^8.

**Concrete pathway:** Replace itrSU (Appendix D of 2512.01781) with NTU:
1. After each tePEPO factor application, the bond grows D -> D * eta.
2. Instead of iterative SU truncation using rank-1 bond weights, contract the NN-cluster environment (Fig. 4 of Dziarmaga) to get the exact metric g.
3. Optimize M_A, M_B via the iterative linear solve (Eq. 4-5 of Dziarmaga) — this replaces itrSU's sequential bond-weight passes.
4. The parallelizability of NTU across all NN bonds (all bonds processed independently per timestep) maps naturally to tePEPO's GPU-friendly architecture.

**Caveats:**
- NTU requires a 2x2-site cluster environment (Fig. 4). tePEPO's vectorized iPEPO has fused d^2 physical index — the double-layer tensors would need that fusion respected.
- NTU was designed for real/imaginary-time evolution with a two-site Suzuki-Trotter gate. tePEPO's FSA-based super-operator is not a simple two-site gate — the bond-dimension growth is more complex (each factor of the Gaussian sum encodes long-range interactions on a larger support). However, after the FSA application, the truncation problem is still a nearest-neighbor bond truncation, so NTU's NN-environment metric is still applicable.
- The cross-bond correlation structure in tePEPO's long-range FSA network may not be fully captured by NTU's 2x2 cluster — this is an open question.

**Verdict:** NTU is a strong, directly applicable replacement candidate for itrSU that would extend tePEPO's accurate correlation-length range from xi ~ 2 to xi ~ 20 at modest additional computational cost (D^8 parallel matmul vs D^6 eta^3 sequential QR). The gain is **quantum** — not a marginal improvement.

### Q2: Feasibility of NTU for density-matrix PEPO (not just pure-state PEPS)

**Directly supported by the paper.** SSIV-SV explicitly develop and benchmark thermal states (mixed states) represented as **iPEPO (infinite Projected Entangled Pair Operator)**:

- The purification approach (Eq. 7-9, Fig. 8): `rho(beta) = rho(beta/2) rho(beta/2)` where `rho(beta/2)` is represented as an iPEPO — a rank-6 tensor with physical indices replaced by a d^2-dim index encoding Hermitian operator basis (O_1 = sigma_x, O_2 = sigma_y, O_3 = sigma_z, O_4 = I for spin-1/2).
- The manifestly Hermitian parametrization (Fig. 8a): a tensor O_a (a = 1..d^2) of Hermitian operators, making the full iPEPO represented by real tensors (no complex arithmetic — ~4x speedup).
- The truncation algorithms (SVDU, NTU, FTU) follow identically as in the pure-state case (SSIV, ln 564-565: "The SVDU, NTU, and FTU algorithms follow as in section II") — the only difference is the gate acting on the d^2-dim physical index.

**No fundamental difference for NTU:** The metric tensor g is built from double-layer tensors (bra and ket copies contracted over physical indices). Whether the physical index is d (pure state) or d^2 (density matrix/PEPO) doesn't change the contraction structure of the NN cluster — it just changes the bond dimensions of the double tensors. The O(D^8) cost scaling is in the bond dimension D, not the physical dimension.

**Relevance to tePEPO's iPEPO:** Dziarmaga's thermal-state iPEPO (Fig. 8) is structurally identical to tePEPO's vectorized-iPEPO carrier (Fig. 4a of 2512.01781). Both are rank-5/rank-6 tensors with fused d^2 physical index. The NTU truncation machinery applies directly to tePEPO's truncation step with no architectural changes needed.

### Q3: The NTU -> GTU pipeline connection (2205.11067)

The connection to **Graphic Tensor Update (GTU)** flows through the cluster-update concept:

- **Cluster update**[85, Wang & Verstraete 2011]: The general framework where the environment for truncation is a cluster of sites around the bond being truncated. NTU is the special case: cluster = nearest neighbors (2 sites + 6 adjacent bonds).
- **GTU** (arXiv:2205.11067, subsequent work, not by Dziarmaga): Generalizes the cluster idea to arbitrary cluster shapes (not necessarily nearest-neighbor) by using **graphical models / belief propagation** to compute the environment metric. GTU's cluster can be a **full 2D block**, a **plaquette**, or a **tree-shaped neighborhood**.
- **The pipeline in the paper's own framing** (SSI, ln 101-107): NTU is explicitly presented as a "special case of a cluster update where the size of the environment is a variable parameter interpolating between a local update and the infinite FU."
- **NTU -> GTU evolution**: GTU (2022) uses the same metric-tensor idea (Hermitian, non-negative from exact cluster contraction) but (i) enables larger/different clusters via the graphical-model solver, (ii) uses an iterative optimization that can handle loopy clusters via approximate inference, and (iii) provides a natural path to **infinite environment** as the cluster grows.
- **For our purposes**: NTU is the **practical, low-overhead entry point** to the cluster-update family. GTU would be the upgrade path if NTU's 2x2 cluster environment proves insufficient for tePEPO's long-range operator structure. The NTU-to-GTU pipeline provides a **controlled accuracy knob** (increase cluster size -> more accurate -> converges to FU) with the same mathematical foundation (exact metric from cluster contraction).

### Synthesis: What NTU means for the tePEPO-based carrier

The weak link in tePEPO (2512.01781) is itrSU's rank-1 environment failing at xi > 2. This Dziarmaga paper provides a drop-in replacement: NTU extends the accurate range to xi ~ 20 with guaranteed-stable Hermitian/non-negative metric, at cost O(D^8) that is fully parallelizable and thus potentially cheaper-in-wall-clock than itrSU's sequential bond-weight passes.

The key numbers:
| Property | itrSU (tePEPO) | NTU (this paper) |
|---|---|---|
| Max accurate xi | ~2 | ~20 |
| Metric quality | Diagonal bond weights, approximated | Full 2x2 environment, exact to machine precision |
| Metric guaranteed Hermitian? | No | Yes |
| Cost scaling | O(D^6 eta^3), sequential | O(D^8), fully parallel |
| Stability | Uncontrolled at xi > 2 | Stable at xi up to 20 |
| Demonstrated on iPEPO | Yes (vectorized Lindblad) | Yes (thermal-state purification) |

**For qec_twin's surface-code carrier goal:** If we build a 2D iPEPO carrier modeled on tePEPO, we should **build it with NTU truncation from the start** — not itrSU. The added implementation complexity (contraction of a 2x2 NN-cluster metric) is modest compared to the factor-of-10 gain in accessible correlation length. The parallelizability also maps naturally to GPU execution (our target hardware constraint).

## How to use / trust + open questions [ours]
- **Trust level:** FULL-TEXT 精读 (11 pp incl. all sections). Equations and figures transcribed from the PyMuPDF text. This is a **published, peer-reviewed** PRB paper (2021), not a preprint — higher trust baseline than the tePEPO paper.
- **Independent verification potential:** The 2D quantum Ising model benchmarks (Figs. 6-7, 9-12) use well-known physics (exact critical point hc = 3.04438(2) per Blote & Deng 2002, QMC reference from Hesselmann & Wessel 2016, FU reference from Czarnik et al. 2019). The thermal-state magnetization curves are cross-checkable against QMC and FU results. For the sudden quench, exact benchmarks for hx = 0 (classical limit) are D = 2 exact.
- **NTU code availability:** Not stated. The author (Dziarmaga) is a co-author on many later papers that use NTU (e.g., 2205.11067 GTU, the Czarnik et al. thermal-state papers). The reduction formalism (Q_A, Q_B isometries + R_A, R_B reduced matrices) is fully specified in Figs. 2-5 and should be straightforward to implement.
- **Open questions for our use:**
  1. **NTU + FSA compatibility**: tePEPO's FSA super-operator applies long-range interactions through a bond-dimension-expanding rule tensor (not a simple two-site Trotter gate). Can NTU's NN-cluster metric still be defined cleanly after an FSA application? The bond being truncated is still NN, but the FSA's signal-carrying auxiliary bonds carry long-range correlation information — NTU's 2x2 cluster may need to include those auxiliary bonds in its environment.
  2. **D cost ceiling**: Dziarmaga demonstrates NTU up to D=12 (real-time) and D=9 (thermal). For surface-code-relevant D (potentially 8-16), is O(D^8) tolerable? D=12 => D^8 ~ 4.3e8 scalar ops per contraction — this is fine for BLAS on a GPU, but the per-timestep, per-bond repetition must be counted.
  3. **NTU on non-square lattices**: The NN-cluster in Fig. 4 assumes a square lattice (checkerboard sublattice A/B). For general graphs (e.g., heavy-hex, the Google Sycamore topology), the NN environment would differ. The cluster-update framing (Wang & Verstraete 2011) handles general graphs, but the exact-contraction strategy is graph-specific.
  4. **Open-system (Lindblad) gate compatibility**: The paper only tests unitary (Hamiltonian) gates + thermal (imaginary-time) evolution. For a Lindblad jump operator applied as a two-site super-operator (e.g., correlated dissipation `L_{ij}`), the gate structure changes (vec-Lindblad form has 3 terms per L). Does NTU's metric still yield Hermitian/non-negative g for a non-Hermitian gate? The paper's metric is built from the state tensors (A, B) and isometries (Q_A, Q_B), independent of the gate content — so likely yes, but untested.
  5. **GTU upgrade path**: If NTU's 2x2 cluster is insufficient for the surface-code regime (correlated errors with longer-range structure), the GTU framework (2205.11067) provides the natural upgrade path with the same mathematical foundation.

## How NTU compares to other truncation schemes (summary)

| Scheme | Environment | Metric property | Cost | Max xi | Stability |
|--------|------------|-----------------|------|--------|-----------|
| SVD (bare) | None | Frobenius (uniform) | O(D^5) | ~0 | OK (but non-monotonic convergence) |
| SU | Diagonal bonds | Diagonal, invertible | O(D^5) | ~2 | OK (requires inversion) |
| **NTU** | **NN cluster (2x2)** | **Exact, Hermitian, non-negative** | **O(D^8) parallel** | **~20** | **Excellent (gauge-free)** |
| GTU (2205.11067) | Tunable cluster | Exact, Hermitian (NTU generalization) | O(D^{8+}) | Larger than NTU | Same foundation |
| FTU | CTMRG iPEPS | Approximate, often non-Hermitian | O(D^{10-12}) | Unlimited | Moderate (sudden crashes) |
| FU | CTMRG iPEPS | Approximate, often non-Hermitian | O(D^{10-12}) | Unlimited | Moderate |

NTU's sweet spot: **moderate correlation lengths (xi <= 20) at moderate bond dimensions (D <= 12-14) where parallelizability and stability are more important than asymptotic convergence rate.** This is precisely the regime tePEPO operates in.

## Key figures (for cross-reference)
- **Fig. 1-2**: SVDU schematics (baseline scheme).
- **Fig. 3**: FTU vs NTU environment diagrams (infinite vs NN cluster).
- **Fig. 4**: NTU metric construction (the core algorithmic diagram).
- **Fig. 5**: NTU/FTU optimization (iterative MA-MB solve + balanced SVD).
- **Fig. 6**: Sudden quench — NTU extends evolution time over SVDU for all hx.
- **Fig. 7**: Connected correlations at hx = hc (critical) — longest-range case.
- **Fig. 8**: Manifestly Hermitian iPEPO for thermal states (directly relevant to PEPO carriers).
- **Fig. 9**: SU failure at hx = 2.9 (D=14 can't converge) — motivation for NTU.
- **Fig. 10**: NTU convergence at hx = 2.9 (D=7-9 converges where SU fails).
- **Fig. 11**: NTU at hx = 2.5 (xi ~ 22 — longest-range success case).
- **Fig. 12**: Tc extraction from NTU magnetization curves (Tables I-II).

## Key quantities (for implementation reference)
- `D` = bond dimension of iPEPS tensors
- `d` = physical Hilbert space dimension (d=2 for spin-1/2)
- `r` = rank of the Trotter gate (the dimension of the index connecting G_A and G_B in Fig. 2a)
- `eta` = expansion factor after gate application: `D -> D * r` (pure state) or `D -> D * eta` (tePEPO, eta = FSA bond dim)
- `chi` = environmental bond dimension for CTMRG (used in expectation value calculation, set to `4D` in their simulations)
- `g` = metric tensor from NN-cluster contraction (size D^2 x D^2)
- `g_A`, `J_A` = reduced metric and source term for M_A optimization (Fig. 5b,c)
- `epsilon` = truncation error (Eq. 2): `(M_A M_B^T - R_A R_B^T)^\dagger g (M_A M_B^T - R_A R_B^T)`
- `R_A, R_B` = reduced matrices after QR decomposition (Fig. 2b)
- `M_A, M_B` = truncated reduced matrices (Fig. 2d)
- `Q_A, Q_B` = fixed isometries from QR decomposition (remain fixed through truncation)
- `S` = singular values after SVD of `R_A R_B^T` (Fig. 2c)
