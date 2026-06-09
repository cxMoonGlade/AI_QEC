# Deep review — Perry, von Kügelgen & Schölkopf, Causal Discovery in Heterogeneous Environments Under the Sparse Mechanism Shift Hypothesis

> Deep reading note (academic-paper-review format; full read Secs. 1–3 incl. the CGM/
> multi-environment setup, the augmented-CGM + environment node, the soft-intervention
> and SMS assumptions Eqs. 2.3–2.4, and the Mechanism-Shift-Score / pairwise-vs-pooled
> identifiability; Secs. 4–6 at the result level). **Relevance to the twin** centerpiece.
> NB: the cache filename `mooij2022_*` is a **misnomer** — the paper is Perry et al. 2022.

## Metadata
- **Authors.** Ronan Perry, Julius von Kügelgen, Bernhard Schölkopf (MPI for Intelligent Systems, Tübingen; Univ. Cambridge). (Shared last author.)
- **Venue / status.** NeurIPS 2022; arXiv:2206.02013.
- **Domain / type.** Causal discovery / representation learning; **theoretical** (identifiability + a score) + empirical estimator comparison.

## Executive summary
The paper shows that **sparse distribution shifts across environments make the causal graph identifiable beyond the Markov-equivalence class (MEC)** — without parametric assumptions. Setup: a causal graphical model `M=(G,P_X)` with Markov factorization `P(X)=∏_j P(X_j|PA_j)` (Eq. 2.1); multi-environment data `D={D^1,…,D^{n_E}}`, each environment `e` arising from **soft interventions on an unknown subset `I^e⊆[d]` of mechanisms** (Asm. 2.3): `P^e(X)=∏_{j∈I^e}P̃^e(X_j|PA_j)·∏_{j∉I^e}P(X_j|PA_j)`, under **independent causal mechanisms** (Asm. 2.4: changing one mechanism tells you nothing about the others). An **augmented CGM** adds an **environment indicator node `E`** with an edge `E→X_i` iff mechanism `i` changes (Def. 2.5), under pseudo-causal sufficiency (Asm. 2.6). The **Sparse Mechanism Shift (SMS) hypothesis** (Asm. 2.7): `0<|I^e|<d` — between-environment changes are *sparse*.

The contributions: (i) under SMS, even the **bivariate** structure (which i.i.d. data leaves undirected) is identifiable (Cor. 4.2); (ii) the **Mechanism Shift Score (MSS)** = the number of conditionals that change across **pairs** of environments — the **true graph minimizes the MSS** (Prop. 5.1), and uniquely so with high probability given enough sparsely-changing environments (Cor. 5.4); (iii) crucially, **pairwise** environment comparisons beat **pooling**: pooling all environments makes the shifts look *dense* (only the MEC is recovered), while comparing *pairs* keeps them sparse and orients the edges (Fig. 1A–C: "Paired PC" vs "Pooled PC"). Even the **weakest** shift signal — a change in the *variance* of a conditional — suffices to orient edges that Markov-equivalence leaves undirected.

For the twin this is **probe richness as heterogeneous environments, formalized for structure discovery**: the probe-richness ladder `C_cal(r)` is exactly a set of environments, moving between levels is a (sparse) mechanism shift, and the MSS could *orient the mechanism graph* from that sparse-shift signal. Two operational lessons land directly: **variance/higher-moment shifts orient what first-moment shifts can't** (the iVAE Prop-1 lesson, restated for structure), and **compare adjacent levels pairwise, don't pool** (the D2 calibrate-on-`r≤k` protocol). The SMS *independence + sparsity* assumption is also a **named risk** for the harden stage: coherent cross-talk could violate sparsity.

## Contributions (claim → evidence → strength)
- **C1. SMS ⇒ structure identifiability beyond the MEC (Cor. 4.2).** Bivariate + multivariate edge orientation under sparse shifts. *Evidence:* augmented-CGM analysis, Fig. 1. *Strength: strong.*
- **C2. The Mechanism Shift Score; true graph minimizes it (Prop. 5.1, Cor. 5.4).** Number of changing conditionals across environment pairs; nonparametric. *Strength: strong.*
- **C3. Pairwise ≫ pooled (Fig. 1C).** Pooling makes sparse pairwise shifts look dense ⇒ only MEC; pairwise keeps them sparse ⇒ full structure. *Strength: strong — the actionable protocol lesson.*
- **C4. Nonparametric + sparsity-leveraging; accommodates multiple estimators (Sec. 6).** *Strength: moderate-strong.*

## Method (deep)
- **Multi-environment / augmented CGM.** Environments = soft interventions on unknown `I^e` (Eq. 2.3); ICM (Asm. 2.4); augmented graph with `E→X_i` iff mechanism `i` shifts (Def. 2.5); pseudo-causal sufficiency (confounders are functions of `E`, Asm. 2.6).
- **SMS.** `0<|I^e|<d` (Asm. 2.7). The value: sparse shifts break the MEC symmetry.
- **MSS.** For each candidate graph, count conditionals that differ across environment pairs; the true graph minimizes the count (independent mechanisms shift sparsely; non-causal factorizations induce *more* changes). Estimators: parametric + nonparametric conditional-shift tests.
- **Pairwise vs pooled (Fig. 1).** Pooled PC on `X∪E`: orients some edges but pooling dense-ifies shifts. Paired PC across environment pairs: each pair differs sparsely ⇒ more orientations. Convergence rate in the number of environments (Cor. 5.4).

## Methodology assessment
| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **4** | Identifiability under SMS rigorous; rests on ICM + faithfulness + pseudo-causal sufficiency (stated, strong assumptions). |
| Novelty | **4** | Formalizes SMS into a usable score with identifiability + the pairwise insight — sharpens a known hypothesis into method. |
| Reproducibility | **4** | Score + estimators described; synthetic experiments; assumptions explicit. |
| Experimental design | **4** | Multiple estimators/score functions compared; sparsity-vs-#environments studied (Fig. 1C). |
| Statistical rigor | **4** | Convergence rates (Cor. 5.4); finite-sample conditional-shift testing is the practical bottleneck. |
| Scalability | **3** | Pairwise comparisons + graph search scale combinatorially; the contribution is identifiability, not speed. |

## Strengths
- **S1 — sparse shifts as the identification lever (Cor. 4.2).** Turning "mechanisms shift sparsely and independently" into edge orientation beyond the MEC is a clean, assumption-light route to structure — and matches how real interventions/contexts behave.
- **S2 — the pairwise-vs-pooled insight (Fig. 1C).** The observation that *pooling destroys sparsity* (and pairwise preserves it) is a concrete, transferable protocol lesson, not just theory.
- **S3 — variance-shift suffices to orient (Sec. 5).** That even the weakest signal (a conditional-variance change) orients undirected edges is the structure-discovery analogue of "higher-moment probes break the alias."

## Weaknesses / limitations
- **W1 — ICM + sparsity + faithfulness are strong assumptions.** SMS requires *independent* mechanisms shifting *sparsely*; correlated/dense shifts violate it (and only the MEC is then recovered).
- **W2 — nonparametric conditional-shift testing is finite-sample-hard.** The score needs reliable detection of *which* conditionals changed; in high dim / low data this is the practical limit.
- **W3 — orients structure, not counterfactuals.** It learns the graph; it does not produce a `do()`-ΔLER or its band (the controlled-teacher's job).

## Relevance to the twin
This is **the probe-richness ladder reread as heterogeneous environments, for *structure* discovery (action P3)**:
1. **`C_cal(r)` IS the set of environments; moving between levels is a mechanism shift.** The twin's probe-richness ladder is exactly Perry et al.'s multi-environment data. When `r=3` basis-rotated/phase-sensitive probes enter, only the *phase-sensitive* mechanisms' statistics change — a **sparse** mechanism shift — and the MSS could orient the mechanism graph from that signal. This gives the twin a *structure-discovery* use of the ladder, complementary to iVAE's *latent-recovery* use.
2. **Variance/higher-moment shifts orient what first-moment shifts can't = the iVAE Prop-1 lesson, restated for structure.** Perry's "a conditional-variance change suffices to orient" is the same content as iVAE's Prop. 1 (mean-only context change leaves an irreducible alias): the twin's probes must change *higher* structure (variance/phase), and when they do, they both *recover the latent* (iVAE) and *orient the graph* (this paper).
3. **"Pairwise, not pooled" = the D2 calibrate-on-`r≤k`, predict-held-out protocol.** Fig. 1C is a direct mandate: compare **adjacent** probe-richness levels (where the shift is sparse) rather than pooling all contexts (where it looks dense and only the MEC survives). The twin's D2 protocol — calibrate on `r≤k`, predict the held-out richer level — is the pairwise comparison; this paper is its identifiability justification.
4. **The augmented-CGM environment node `E` = the probe-level as an explicit context variable.** Adding `E` with `E→X_i` iff mechanism `i` shifts is the twin treating the probe-richness index as a node whose children are exactly the mechanisms a given probe perturbs — a clean way to *read off which mechanisms a probe touches*.
5. **SMS independence+sparsity = a named harden-stage risk, and the lachapelle/ICP bridge.** The SMS assumption (mechanisms shift independently and sparsely) is exactly where **coherent cross-talk** (correlated mechanisms, the harden axis) could break sparsity — so this is a *diagnostic, not a guarantee*, for the twin, and a concrete thing to test when correlated mechanisms enter. The "soft interventions on unknown `I^e`" is identical to Lachapelle's **unknown-target interventions**, and the invariance predecessor is ICP (`heinze_deml2018`) — three notes naming one object (sparse, unknown-target, cross-environment shift).

## How to use / trust + open questions
- **Trust:** high as the *structure-discovery* justification for the probe ladder and the *pairwise protocol*; carry W1 (ICM+sparsity may fail under coherent cross-talk) and W3 (structure, not ΔLER).
- **Open questions for the project:** (i) Compute an **MSS over the twin's mechanism graph** across adjacent probe-richness levels — does it orient the coherent vs stochastic mechanisms, and does the orientation appear exactly when phase-sensitive probes enter? (ii) Adopt **pairwise adjacent-level comparison** as the D2 default (cite Fig. 1C). (iii) Use the **augmented-CGM `E`-node** to formally label which mechanisms each probe level perturbs. (iv) **Stress-test SMS under correlated mechanisms** (harden axis): when coherent cross-talk makes shifts dense, does identifiability degrade to the MEC as predicted? — a pre-registered harden experiment.
