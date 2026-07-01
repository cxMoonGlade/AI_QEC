# Deep review — Moran, Sridhar, Wang & Blei, Identifiable Deep Generative Models via Sparse Decoding (Sparse VAE)

## Provenance

- **Source:** arXiv:2110.10804 (full PDF, open access), fetched 2026-06-30; TMLR 2023 (Transactions on Machine Learning Research, Volume 2022/2023), OpenReview: https://openreview.net/forum?id=vd0onGWZbE
- **Reading method:** FULL-TEXT read (精读) of the arXiv PDF — Secs. 1-2 (sparse DGM, Spike-and-Slab-Lasso prior, sparse-VAE algorithm, anchor-feature identifiability result, positioning vs iVAE/ICA) in full; Secs. 3-5 at result level
- **Status:** complete full-text close-read

> Deep reading note (academic-paper-review format; full read Secs. 1–2 incl. the sparse DGM
> Eq. 1, the Spike-and-Slab-Lasso prior Eqs. 2–4, the sparse-VAE algorithm, and the
> anchor-feature identifiability result + its positioning vs iVAE/ICA; Secs. 3–5 at the
> result level). **Relevance to the twin** centerpiece — the D5a structural gate.

## Metadata
- **Authors.** Gemma E. Moran, Dhanya Sridhar, Yixin Wang, David M. Blei (Columbia; Mila / Univ. Montréal; Univ. Michigan).
- **Venue / status.** TMLR 2023; arXiv:2110.10804.
- **Domain / type.** Identifiable representation learning / deep generative models; **theoretical** (identifiability theorem) + a sparse-VAE estimator + real-data studies.

## Executive summary
The paper makes **deep generative models identifiable using *structure alone*** — a single environment, **no context/distributional variation** — by requiring the factor→feature decoder to be **sparse** and to possess **anchor features**. The **sparse DGM** (Eq. 1): a per-feature selector `w_j∈ℝ^K` masks which of `K` latent factors produce feature `j`, with `x_ij ~ N((f_θ(w_j⊙z_i))_j, σ_j²)`, `z_i~N(0,Σ_z)`, and a **Spike-and-Slab Lasso (SSL)** prior on `w_jk` (Eqs. 2–4: `η_k~Beta(a,b)`, `γ_jk~Bernoulli(η_k)`, `w_jk~γ_jk·Laplace(λ_1)+(1−γ_jk)·Laplace(λ_0)`, `λ_0≫λ_1` — a negligible "spike" or a large "slab"). The proportion `η_k` "zeros out" extraneous factors and estimates the number of factors `K` (Beta-Bernoulli ≈ Indian Buffet Process).

The **identifiability theorem**: a sparse DGM is identifiable (up to permutation + element-wise transform) **iff each latent factor has ≥2 "anchor features"** — observed dimensions that load on *that factor alone*. Crucially, **anchors need only *exist*, not be known in advance**, and — unlike ICA — **the factors need not be independent**. The anchor assumption removes the **rotational invariance** of the latent factors (the role played by non-Gaussianity in ICA and by the auxiliary variable in iVAE), but does so **structurally**. The **sparse VAE** (Alg. 1) fits it by MAP for `(W,θ,η)` + amortized VI for `z`; the SSL prior naturally favors anchor-satisfying solutions. Empirically it recovers ground-truth factors *even when correlated*, gives better held-out reconstruction, and finds interpretable structure on text/ratings/genomics.

For the twin this is the paper behind the **D5a structural identifiability gate** (`audit/gating`): an **anchor feature for mechanism `j` is a syndrome bit `b` with `A[b,j]=1` and `A[b,j']=0` for all `j'≠j`** (fires for `j` alone), and `identifiable(j) ⇔ ≥2 such bits`. This is **checkable *today* from the known DEM parity map `A`, before any modeling assumption** (action P0) — the information-theoretic ceiling on per-mechanism identifiability. The rep-code's "0 anchored faults, every detector shared" is exactly this theorem applied — which is *why* the probe-richness ladder (iVAE's distributional route) is load-bearing there.

## Contributions (claim → evidence → strength)
- **C1. The sparse DGM with an SSL prior on the factor→feature map (Eqs. 1–4).** *Strength: strong (the structural model + the right prior).* 
- **C2. Anchor-feature identifiability: ≥2 anchors per factor ⇒ identifiable up to permutation + element-wise transform (Sec. 2).** *Evidence:* theorem + proof; anchors need only exist; no factor independence. *Strength: strong — the headline.*
- **C3. The sparse VAE estimator (Alg. 1).** MAP for `W,θ,η`, amortized VI for `z`; SSL favors anchor solutions. *Strength: strong.*
- **C4. Empirical recovery (incl. correlated factors) + interpretability (Secs. 3–5).** *Strength: moderate-strong.*

## Method (deep)
- **Model.** `x_ij~N((f_θ(w_j⊙z_i))_j,σ_j²)`; `w_jk≠0` ⇒ factor `k` may drive feature `j`; sparse `w_j` ⇒ few factors per feature (Fig. 1: sparse vs dense DGM).
- **SSL prior.** Spike `λ_0` (negligible) vs slab `λ_1` (large); `γ_jk` indicator; `η_k` = factor-`k` feature-usage rate → IBP-like factor-number selection.
- **Anchor theorem.** ≥2 anchors per factor removes rotational invariance ⇒ identifiable up to `~_P` + element-wise transforms. No independence assumption (vs Horan's local-isometry, which needs it).
- **Constraint.** `x_ij` must have *consistent meaning across samples* (genomics gene, not image pixel) — the sparse loading is shared across data points.

## Methodology assessment
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **5** | Rigorous anchor identifiability; SSL prior principled; correlated-factor case handled. |
| Novelty | **4** | Brings the anchor-feature idea (topic models/NMF) to deep generative models with a clean theorem — a solid, distinctive identifiability route. |
| Reproducibility | **4** | Model + SSL + algorithm explicit; real + synthetic experiments; code referenced. |
| Experimental design | **4** | Synthetic (incl. correlated factors), semi-synthetic, and real (text/ratings/genomics); compared to VAE/β-VAE/VSC/OI-VAE. |
| Statistical rigor | **4** | Identifiability (not sampling) guarantee; held-out reconstruction as the empirical metric. |
| Scalability | **4** | Sparse VAE scales; the per-feature mask + SSL add moderate overhead. |

## Strengths
- **S1 — identifiability from structure, single environment (anchor theorem).** No need for multiple environments / context variation — when anchors exist, the model is identifiable from one dataset. This is the *cheapest possible* identifiability lever.
- **S2 — anchors need only exist, and factors may be correlated.** Not requiring anchors to be known *or* factors to be independent makes the result far more applicable than ICA-style assumptions.
- **S3 — the SSL prior operationalizes the theorem.** The Spike-and-Slab Lasso *favors* anchor-satisfying sparse maps and estimates the factor count — theory and estimator are matched.

## Weaknesses / limitations
- **W1 — anchors are *sufficient*, not necessary.** Their absence does *not* prove non-identifiability; it means identification must come from elsewhere (context variation). For codes without anchors (rep code), the theorem is silent — by design.
- **W2 — requires consistent feature meaning across samples.** The shared sparse loading needs `x_j` to mean the same thing for all `i` (fine for syndrome bits; not for image pixels).
- **W3 — covers the *loading* (which factor → which feature), linear-in-mask.** It identifies the factor→feature *support*, not arbitrary nonlinear/coherent structure outside that support.

## Relevance to the twin
This is **the D5a structural identifiability gate — the only identifiability lever checkable from `A` *today*, before any data (action P0)**:
1. **Anchor feature for mechanism `j` = a syndrome bit that fires for `j` alone.** Precisely: a detector bit `b` with `A[b,j]=1`, `A[b,j']=0 ∀j'≠j`. The theorem gives the twin a **computable gate**: `identifiable(j) ⇔ ≥2 such anchor bits`. This is the `anchor_features(A)` computation in `audit/gating` — the per-mechanism identifiability ceiling read straight off the *known* DEM, with **no modeling assumption and no data**.
2. **The rep-code "0 anchored faults, every detector shared" is this theorem applied.** The rep code has *no* anchors (every detector is shared between two faults), so D5a returns "structurally non-identifiable" — and W1 says that is *not* a dead end but a *handoff*: identification must then come from **context variation (iVAE / the probe ladder)**. This is the formal reason the probe-richness ladder is load-bearing exactly where anchors fail — the two gates (D5a structural, iVAE distributional) compose.
3. **Consistent with ADR 0005 — known-structure identifiability, NOT parameter-tying.** Anchors are a property of the *fixed forward map* `A`; using them adds no free identifiability beyond what the physics already implies — exactly the permitted lever (like Lachapelle's known mask), never the retired orbit/parameter-sharing tie.
4. **The SSL prior = the twin's sparsity/locality regularizer, Bayesian form.** Moran's Spike-and-Slab Lasso on the factor→feature map is the same object as Lachapelle's binary mask (relaxation form) and Albani's convex regularizer `f_{a0}`: all encode "few factors per feature." The twin's locality prior can be stated as either; the SSL additionally *estimates the factor count* (the IBP connection) — useful if the number of active mechanisms is unknown.
5. **Three identifiability levers, layered — and the Pauli-only scope (W3).** Moran (structural anchors, single-environment, action P0), iVAE (distributional, multi-environment), Lachapelle/UT-IGSP (sparsity / interventional discovery) are the twin's complementary identifiability gates, all ADR-0005-compliant. But the anchor theorem is about the **factor→feature *loading*** — i.e. the `F_2` DEM `A`, the **Pauli/stochastic ("quadratic-variation") layer**. The **coherent** structure lives *outside* `A` entirely (cf. `qec_coherent_errors_dem_2510.23797`), in the off-diagonal PTM — so D5a (anchors, Pauli) and **D5b (coherent off-diagonal PTM / Girsanov, Kaufmann + Ivashkov)** are the two distinct identifiability layers the twin must gate separately.

## How to use / trust + open questions
- **Trust:** very high as the *structural identifiability gate read from `A`*; carry W1 (anchors sufficient, not necessary — absence hands off to the probe ladder) and W3 (Pauli-loading layer only; coherent is D5b).
- **Open questions for the project:** (i) Run `anchor_features(A)` as the **D5a P0 gate** on every code the twin targets (rep, then surface) and report the per-mechanism anchor count *before* any calibration. (ii) Where anchors are absent, **quantify how much probe richness (iVAE `L`-rank) is needed to substitute** — the explicit D5a→iVAE handoff. (iii) State the twin's locality prior as an SSL/IBP to *also estimate the active-mechanism count*. (iv) Keep D5a (Pauli/loading) and D5b (coherent/off-diagonal PTM) as **separate gates**, since the anchor theorem provably covers only the `F_2` `A` layer.
