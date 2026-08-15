# Theory-first grounding — Direction B: manifold-constrained noise fit + off-manifold residual

> **Provenance (2026-06-25):** theory-first pass triggered by the user's redirect — "lift the
> *manifold-optimization* idea off [[sen_mapping_networks_2602.19134]] (NN-weight compression) and apply
> it to OUR noise model to save (estimation) parameters + improve scaling/identifiability." This is a
> SYNTHESIS over already-committed grounding (no new 精读 needed — the anchors below are already read);
> it is a SCOPING deliverable, NOT a pre-registration. Sources read for this pass: this repo's
> `docs/IDENTIFIABILITY_AND_CRL_SURVEY.md` (full) + [[qec_learnable_logical_noise_2601.22286]] (full) +
> [[qec_coherent_errors_dem_2510.23797]] (full); cross-refs to the iVAE / sparse-VAE / mechanism-sparsity
> notes via the survey.

## The idea, stated precisely [ours]
Fit the noise model on a LOW-DIMENSIONAL MANIFOLD (parameterize a compact latent → channel/DEM, optimize
the latent) instead of the ambient high-dim DEM/channel space; treat the part of the data the on-manifold
fit CANNOT explain as the **off-manifold residual = the misspecification signal**. Two flavors:
- **B-phys:** the manifold = physically-realizable noise (a handful of physical params → DEM). The
  teacher IS this generative map.
- **B-learn:** the manifold = a LEARNED identifiable low-dim latent (the direct analog of the paper's
  `g: R^d → R^P`), conditioned on the calibration-context ladder.

## VERDICT: grounded — and MORE rigorously than the paper [ours]
The decisive upgrade over [[sen_mapping_networks_2602.19134]]: the paper *guesses* the low-dim weight
manifold EMPIRICALLY (a PCA/t-SNE plot — the "Weight-Manifold Hypothesis"). For OUR noise model the
manifold's intrinsic dimension is a **THEOREM**, not a hypothesis:

| Piece | Paper (NN weights) | Ours (noise model) — grounded |
|---|---|---|
| manifold exists | empirical PCA plot (Fig 2), near-tautological existence "theorem" | **Bravyi/Zheng Thm 1** [[qec_learnable_logical_noise_2601.22286]]: learnable ⇔ full column rank of `A_ℳ = ½(1−H_ℳ)` (restricted Walsh–Hadamard); the **gauge group is the exact unlearnable kernel** |
| right coordinates | latent `z` + fixed orthogonal map | **Pauli-rate vector** (survey W4 — no Kraus gauge freedom) or **iVAE** identifiable latent (Khemakhem 1907.04809), context = the `r=0..4` ladder |
| stay-on-manifold reg | smoothness/stability/alignment losses | **mechanism-sparsity / DEM-footprint** (Lachapelle 2107.10098) + **CPTP soft penalty** (HJM no-arbitrage analogy, survey) |
| optimizer | gradient descent on `z` | **differentiable MLE** [[qec_differentiable_mle_noise_2602.19722]] / **Bayesian** (Kobori 2406.08981) / **SMC drift** (Hauri 2511.09491) |

So "manifold-based optimization of the noise model" is the project's EXISTING CRL/identifiability program
(`docs/IDENTIFIABILITY_AND_CRL_SURVEY.md`), made concrete — the Mapping Networks paper adds nothing here;
its empirical-manifold intuition is the weaker version of Bravyi's theorem.

## The mechanism — operable [paper → ours]
- **Manifold dimension (certified):** compute the rank / near-null space of `A_ℳ = ½(1−H_ℳ)` from the
  known DEM parity map `A` (Bravyi Thm 1; sample count via the RIP bound Thm 3). This SUPERSEDES the
  twin's current first-moment proxy `learnable_first_moment_dim(A)` — Bravyi's note flags the proxy and
  gives the exact construction to port (its open-Q iii: check the rep-code "4 aliased DOF" matches the
  Hadamard-rank count). **The prior `Λ^prior` is ALWAYS learnable; the effective/logical distribution
  only if `σ(a)=σ(b) ⟺ a ∼_𝒢 b`** — this IS "fit-the-manifold ≠ counterfactual validity," proven.
- **Parameterize + fit ON the manifold:** Pauli-rate coords (or iVAE latent at the **polarization level**
  `π_b = E[(-1)^{y_b}] ∈ [-1,1]` — survey W3, since syndromes are binary and break continuous tools),
  constrained to the learnable subspace, CPTP as a soft penalty.

## The observable (off-manifold residual = misspecification) — operable [paper → ours]
Bravyi is **Pauli-ONLY** (its W1) — the Walsh–Hadamard structure does not cover coherent/non-Clifford.
So the off-Pauli-manifold residual is exactly the twin's coherent/leakage wedge, and it has a concrete,
grounded signature from [[qec_coherent_errors_dem_2510.23797]] (Takou–Brown):
- **boundary edge enhancement** `p_coh = sin²(2θ) ≈ 2·p_stoch` (weight-4 checks),
- **DEM hyperedges** (3-/4-point detection events) absent in Pauli-twirled models,
both estimable from the same `⟨v_i⟩, ⟨v_i v_j⟩` correlation formulas, revealed by the `r=4` (non-Clifford)
probes (survey W5).
- **CORRECTION carried (Takou–Brown §III, relevance pt 2):** moment-based estimation is NOT blind to all
  coherence — it sees the boundary enhancement + hyperedges. The RIGHT negative control (the "manifold"
  baseline whose residual we measure) is the **INDEPENDENT-EDGE, Pauli-twirled DEM**, which misattributes
  those structural features — NOT "second moments see nothing." State the on-manifold baseline as
  independent-edge Pauli DEM; the residual = the structural (boundary/hyperedge/leakage) excess.

## Caveats it carries (the project's central risk, theorem-grounded) [ours]
- **W1 (counterfactual non-identifiability, Nasr 2301.09031 + Bravyi prior/effective split):** a fit that
  matches the manifold (the always-learnable prior) can still give wrong `do()` answers. The controlled
  teacher is the ONLY path to counterfactual (b-)validity — the asymmetry that makes QEC better than the
  finance analogue. **Nothing built on a manifold fit alone is counterfactually certified.**
- **W2 (learnable ceiling):** do not claim identifiability beyond `rank(A_ℳ)`; gauge directions are
  honestly unidentifiable and the band must declare them (the Tier-0 gauge null-space of `H`).
- **B-learn extra risk:** a learned manifold that is too NARROW = under-fit = it *absorbs* the
  misspecification it should expose (it learns the leakage as if it were on-manifold). The residual
  observable must be computed against a FIXED, declared on-manifold class, not a class flexible enough to
  swallow the off-manifold signal — else the whole point (expose misspecification) is defeated. This is
  the [[feedback-prevent-toy-from-the-start]] bar: SWEEP the manifold richness, report the residual as a
  band, never freeze the class.

## What is NOT done (the genuine work) + the frontier [ours]
The survey states plainly (line 6-7): *"none of the tools below have been validated on this codebase
yet."* So the GROUNDING is complete; the IMPLEMENTATION is the open work — the survey's action items:
P0 certified learnable-subspace (`A_ℳ` rank, supersede the proxy) + anchor-bit check; P1 iVAE at the
polarization level + mechanism-sparsity reg on `cptp_channel`; the off-manifold residual = reproduce the
independent-edge DEM control + measure the boundary/hyperedge residual on a coherent teacher.
**The genuine FRONTIER (Bravyi open-Q i):** extend the gauge/learnability (manifold/residual) split OFF
the Pauli group to a coherent/leakage generator — where the Walsh–Hadamard structure no longer applies.
That boundary IS the twin's unique contribution; the Pauli-manifold part is grounded and (largely)
owned by Bravyi + Takou–Brown.

## Recommendation [ours]
- The manifold idea is REAL and lands on a grounded, mostly-already-surveyed program — **on the
  estimation/twin side, NOT the carrier scaling** (carrier stays PEPS/boundary-MPS; that conclusion is
  unchanged). The "save parameters" payoff is in the ESTIMATION dimension (fit `rank(A_ℳ)` DOF, not the
  ambient DEM), with better identifiability + natural bands.
- **[[sen_mapping_networks_2602.19134]] is superseded for our purposes** by Bravyi (theorem > empirical
  PCA) — do NOT build on the paper; it contributed only the prompt to look here.
- **Next theory-first step IF pursued:** a pre-registration for ONE concrete, falsifiable cut — most
  naturally **the certified learnable-subspace (`A_ℳ` rank) vs the current first-moment proxy** (an
  (a)-exact check: does `rank(½(1−H_ℳ))` equal the proxy's alias-DOF on the rep code / d3?), with the
  off-manifold residual (independent-edge DEM vs coherent teacher) as the paired observable. That is a
  small, theorem-anchored, teacher-validatable first bet — not a build of the whole program.
