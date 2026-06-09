# Reading Notes — Cached Reference Papers (deep peer-review)

One **deep, peer-review-grade** note per cached PDF in `docs/papers/` (22 total),
produced with the `academic-paper-review` skill from a **full read** of each paper
(methods, key equations/theorems, results, assumptions, limitations) — not the
abstract. Each note has: metadata · executive summary · **contributions
(claim → evidence → strength)** · method (deep) · results (deep, where empirical) ·
**6-criterion methodology table** (Soundness / Novelty / Reproducibility /
Experimental design / Statistical rigor / Scalability, 1–5) · strengths (S1–S3 with
section refs) · weaknesses/limitations (W1–W3) · **relevance to the twin** (the
load-bearing, centerpiece section — recover/understand/manipulate/predict, the
finance framing, the ADRs, the code) · how-to-use/trust + open questions.

ADR numbering used (this repo): 0002 build order · 0003 B methodology · 0004
finance framing · 0005 retire-SCOPE reframe · 0006 channel-field architecture.
Spec: `docs/TWIN.md`. Companion: `../README.md` (cache index + relevance map),
`docs/IDENTIFIABILITY_AND_CRL_SURVEY.md`.

**Cross-cutting finding (the Girsanov split, confirmed three ways).** The twin's
coherent↔incoherent decomposition (`girsanov_split`) appears independently in three
fields: **off-diagonal PTM, no Pauli contribution** on hardware (Kaufmann
2307.08741), **`t` (dissipator) vs `t²` (Hamiltonian) short-time scaling** (Ivashkov
2603.05492), and the **`dP/dQ` Radon–Nikodym drift `ζ`** that *is* the finance↔QEC
isomorphism (Gierjatowicz 2007.04154, ADR 0004). **One uncertainty band, four
framings**: Cont's `μ_Q` range · Nasr's worst-case counterfactual error · Heinze-Deml's
effect bands · Gierjatowicz's `(inf,sup) E_Q[Ψ]` — all the alias band on ΔLER.

## Finance — calibration as an ill-posed inverse problem (the master analogy)

| Note | One-line takeaway |
|---|---|
| [cont2006_model_uncertainty](cont2006_model_uncertainty.md) | Model uncertainty = range of a quantity over the *set* of calibrated models → the **alias-band template** (`[min,max] ΔLER`). |
| [finance_localvol_convex_regularization_1211.0170](finance_localvol_convex_regularization_1211.0170.md) | Calibration is **provably ill-posed** (compact forward / injective-but-compact derivative = the band's width); CPTP/locality priors ARE the Tikhonov regularizer (shrink variance, *not* the observational alias). |
| [fouque_uvm_stochastic_bounds](fouque_uvm_stochastic_bounds.md) | Worst-case price over a band (BSB PDE); ⚠ its boundary shortcut needs monotonicity — **LER isn't monotone → extremize numerically** (Tier-1 TRS). |
| [gierjatowicz2020_neural_sdes](gierjatowicz2020_neural_sdes.md) | Neural-SDE robust pricing = closest analogue to **amortized `f_ψ(c)` + differentiable-forward calibration + constructive `(inf,sup)` band**; Eq. 1.3 `dP/dQ` Girsanov = the **ADR-0004 isomorphism's home**. |
| [fouque_mcmc_multiscale_sv](fouque_mcmc_multiscale_sv.md) | Two-timescale latent vol via MCMC = template for **Google 15 h slow drift + fast shot noise** (`predict`/C-stage); **fast-factor ID enables slow-factor accuracy** → couple D3b band + drift jointly. |

## Identifiability / Causal Representation Learning

| Note | One-line takeaway |
|---|---|
| [khemakhem2020_ivae](khemakhem2020_ivae.md) | iVAE: **context/auxiliary variation identifies latents** (the `L`-rank condition (iv) = countable "how much richness"; Prop. 1 = why mean-only probes leave an irreducible alias) — formal backbone of ADR 0005. |
| [moran2022_sparse_vae_identifiable](moran2022_sparse_vae_identifiable.md) | **Anchor-feature** condition (≥2 detectors fire for a fault alone) = the **D5a gate**, checkable from `A` today (action P0); covers only the Pauli/`A` layer (coherent = D5b). |
| [lachapelle2022_mechanism_sparsity](lachapelle2022_mechanism_sparsity.md) | Known sparse DEM footprint `A` **IS** the mechanism mask `G` AS an identification constraint (Thm. 5) — the twin gets it for free; complements iVAE's auxiliary route (action P1). |
| [nasr2023_counterfactual_nonidentifiability](nasr2023_counterfactual_nonidentifiability.md) | **Impossibility theorem** (Y¹/Y² same observational, different counterfactual) = the formal core of "observational ≠ interventional"; the moment-matched control is literally a constructed `Y²` (W1). |
| [heinze_deml2018_nonlinear_icp](heinze_deml2018_nonlinear_icp.md) | ICP: causal parents of LER via cross-context invariance + **effect confidence bands + prediction-under-intervention** = the `understand`→`manipulate` bridge (two-stage, action P3). |
| [squires2020_ut_igsp](squires2020_ut_igsp.md) | Interventional discovery when probes perturb an **unknown** mechanism subset; **unknown-target ID = known-target ID** (the ladder keeps full power); discovers which mechanisms each probe touches (action P3). |
| [mooij2022_sparse_mechanism_shift](mooij2022_sparse_mechanism_shift.md) | (Perry et al.) Sparse-shift / variance heterogeneity orients edges the MEC can't; **pairwise > pooled** (= the D2 adjacent-level protocol). |

## QEC noise learning from syndromes (in-domain version)

| Note | One-line takeaway |
|---|---|
| [qec_learnable_logical_noise_2601.22286](qec_learnable_logical_noise_2601.22286.md) | The **learnable-DOF ceiling** from syndromes (the rigorous D5a; gauge DOF like GST) — action P0, W2. |
| [qec_insitu_benchmarking_clifford_2601.21472](qec_insitu_benchmarking_clifford_2601.21472.md) | Predict logical fidelity from syndromes with **poly samples** below threshold — feasibility companion. |
| [qec_dem_estimation_syndrome_2504.14643](qec_dem_estimation_syndrome_2504.14643.md) | The **moment-matching DEM baseline = the negative control** (Pauli-shadows coherence; "degeneracy" = the in-domain alias). |
| [qec_coherent_errors_dem_2510.23797](qec_coherent_errors_dem_2510.23797.md) | Coherent errors as DEM **interference + hyperedges**; Pauli-twirl underestimates LER — **the coherent "drift" slice** the twin targets (W5). |
| [qec_differentiable_mle_noise_2602.19722](qec_differentiable_mle_noise_2602.19722.md) | **dMLE**: exact differentiable syndrome-NLL calibration — closest external prior art; the Pauli/DEM **Pauli-shadowing negative-control reference** (D4). |

## Surface-code / coherent-error / harden-frontier

| Note | One-line takeaway |
|---|---|
| [correcting_coherent_errors_surface_1710.02270](correcting_coherent_errors_surface_1710.02270.md) | Bravyi **Majorana free-fermion** trick: exact coherent surface-code sim; `P^L` = avg diamond-norm (the standard metric); coherence washes out but **exceeds the Pauli-twirl** sub-threshold. |
| [marton_asboth_coherent_readout_surface_2303.04672](marton_asboth_coherent_readout_surface_2303.04672.md) | Coherent + readout (3D syndrome); the **primary metric is maximum infidelity `p_L^i` (Eq. 15)**, diamond `P^L` secondary — closes the "Márton primary not yet computed" gap; threshold ≈ 2.6%. |
| [coherent_robust_pauli_2307.08741](coherent_robust_pauli_2307.08741.md) | Characterize the **coherent part robustly to Pauli** = the **Girsanov split on hardware** (off-diagonal PTM, no Pauli term, Eq. 4); echo probe; 2-qubit coherent + drift = harden axes. |
| [fail_fast_rare_events_2511.15177](fail_fast_rare_events_2511.15177.md) | Rare-event toolkit (`P(q)=T{f}(q)` failure-spectrum, min-weight fails, splitting) = the **`predict`** axis + the frozen-decoder ΔLER substrate; **coherent tails unhandled = the twin's wedge**. |
| [lindbladian_learning_insitu_2603.05492](lindbladian_learning_insitu_2603.05492.md) | **Ansatz-free Lindbladian learning** (H + dissipator in `(h,a)`) = the twin's GKSL `recover` form; **`t` vs `t²` = Girsanov split in time**; "steady states don't identify the generator" = the observational alias as a theorem. |
