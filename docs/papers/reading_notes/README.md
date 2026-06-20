# Reading Notes — Cached Reference Papers (deep peer-review)

One **deep, peer-review-grade** note per cached PDF in `docs/papers/`,
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
| [chamberland_ai_predecoder_surface_code_2604.12841](chamberland_ai_predecoder_surface_code_2604.12841.md) | **NVIDIA AI pre-decoder + noise-learning** (sim-only, GB300/FP8): 3D-CNN pre-decoder cuts syndrome density → 3–3.5× end-to-end speedup with no LER regression vs *uncorrelated* matching; a 2D-CNN→GAP→MLP **noise-learning net** regresses syndrome stats → 25 circuit params through a **distance-independent, differentiable 18-edge/43-hyperedge** DEM parameterization (Stim-verified). = the **supervised** mirror of our label-free `hypergraph_dem` NLL; their "true DEM is a *lower bound* on uncorrelated-matching LER" **is** our exact-inverse rule. Adopt the parameterization; differentiate via explicit bands + exact TN-MLD; attack their open low-p/rare-event regime. |

## Bayes-TN posterior decoders and noise posteriors

| Note | One-line takeaway |
|---|---|
| [bayes_tn_qec_posterior_models_overview](bayes_tn_qec_posterior_models_overview.md) | Five-paper map: Bayes-TN means `P(logical/channel | syndrome, noise)` plus `P(noise parameters | syndrome history)`, not pairwise edge fitting. |
| [ferris_poulin_tensor_networks_qec_1312.4578](ferris_poulin_tensor_networks_qec_1312.4578.md) | Foundational equivalence: QEC decoding is a TN contraction; useful as terminology, not the surface-code baseline. |
| [bravyi_suchara_vargo_mld_surface_code_1405.4883](bravyi_suchara_vargo_mld_surface_code_1405.4883.md) | Canonical surface-code Bayes-TN decoder: compute logical coset probabilities `P(m | s, theta)` by MPS/TN contraction. |
| [darmawan_poulin_realistic_noise_1607.06460](darmawan_poulin_realistic_noise_1607.06460.md) | Non-Pauli TN forward/decoder carrier: compute syndrome-conditioned logical channels under arbitrary local CPTP noise. |
| [darmawan_poulin_linear_time_decoder_1801.01879](darmawan_poulin_linear_time_decoder_1801.01879.md) | Practical non-Pauli/correlated Bayes-TN decoder: approximate logical channel, choose correction, `O(N D^3 chi^3)`. |
| [kobori_todo_bayesian_noise_parameters_2406.08981](kobori_todo_bayesian_noise_parameters_2406.08981.md) | Closest prior art for our Layer-1 Bayes layer: TN likelihood inside MCMC/SMC gives `P(theta | syndrome history)` and drift tracking. |

## Surface-code / coherent-error / harden-frontier

| Note | One-line takeaway |
|---|---|
| [correcting_coherent_errors_surface_1710.02270](correcting_coherent_errors_surface_1710.02270.md) | Bravyi **Majorana free-fermion** trick: exact coherent surface-code sim; `P^L` = avg diamond-norm (the standard metric); coherence washes out but **exceeds the Pauli-twirl** sub-threshold. |
| [marton_asboth_coherent_readout_surface_2303.04672](marton_asboth_coherent_readout_surface_2303.04672.md) | Coherent + readout (3D syndrome); the **primary metric is maximum infidelity `p_L^i` (Eq. 15)**, diamond `P^L` secondary — closes the "Márton primary not yet computed" gap; threshold ≈ 2.6%. |
| [coherent_robust_pauli_2307.08741](coherent_robust_pauli_2307.08741.md) | Characterize the **coherent part robustly to Pauli** = the **Girsanov split on hardware** (off-diagonal PTM, no Pauli term, Eq. 4); echo probe; 2-qubit coherent + drift = harden axes. |
| [fail_fast_rare_events_2511.15177](fail_fast_rare_events_2511.15177.md) | Rare-event toolkit (`P(q)=T{f}(q)` failure-spectrum, min-weight fails, splitting) = the **`predict`** axis + the frozen-decoder ΔLER substrate; **coherent tails unhandled = the twin's wedge**. |
| [lindbladian_learning_insitu_2603.05492](lindbladian_learning_insitu_2603.05492.md) | **Ansatz-free Lindbladian learning** (H + dissipator in `(h,a)`) = the twin's GKSL `recover` form; **`t` vs `t²` = Girsanov split in time**; "steady states don't identify the generator" = the observational alias as a theorem. |

## External landscape — decoder baselines & coherent noise (not cached; first-pass digest, 2026-06-14)

Four user-supplied papers positioning the M3/M4 + plan3 work against the
coherent-noise-physics and neural-decoder frontiers. **Digest tier** — built from
sub-agent digests (paper-1 abstract verified directly); numbers must be re-checked
against the PDFs before entering any registration or the paper. Bilingual overview
hub + four standalone English peer-review notes (the hub keeps the CN/EN synthesis;
the deep notes are English, corpus-aligned).

| Note | One-line takeaway |
|---|---|
| [2026-06-14_coherent_noise_and_neural_decoders](2026-06-14_coherent_noise_and_neural_decoders.md) (hub, CN/EN) | Two clusters — **coherent/correlated noise has QEC-level consequence** (1+2) vs **efficient Mamba decoders on a static Pauli DEM** (3+4, both Sycamore). Our wedge sits in the gap: learn a coherent-capable structured noise object from real syndromes (M3 NLL win) + honest decode cost (M4 −40%) + drift (unbuilt headline) + bands. Map + cross-paper synthesis + citation guidance. |
| [harper_nonclifford_crosstalk_surface_2605.29514](harper_nonclifford_crosstalk_surface_2605.29514.md) | Hybrid **stabilizer-TN** sim of **coherent** crosstalk: raises LER, lowers threshold, spatial distribution matters — coherent-wedge physics backing + a coherence-preserving carrier-engine reference (ADR 0008). ✓ **full-text read 2026-06-15** — method (Clifford `C` + error-carrying MPS, χ_max=32, Schmidt-decay), θ≈10⁻³, threshold ~0.8%, forward-only/PTA-decode verified. |
| [darmawan_decoder_adaptation_local_noise_2403.08706](darmawan_decoder_adaptation_local_noise_2403.08706.md) | PRA. Near-optimal PEPS/TEBD oracle + **selective mischaracterization**: **few critical parameters** dominate; Pauli-adapted decoder near-optimal **only** for uncorrelated/small-θ → the closest anchor to M4, and the M3↔M4 bridge (bunching breaks his locality). |
| [sparse_mamba_decoder_2605.17156](sparse_mamba_decoder_2605.17156.md) | **Sparse Mamba** O(k) defect-centric decoder on Sycamore/SI1000; decoder-accuracy foil (XEB→DEM oracle = the independent-edges DEM M4 found lossy) + Component-B amortization precedent. |
| [scalable_neural_decoder_realtime_2510.22724](scalable_neural_decoder_realtime_2510.22724.md) | **Mamba O(d²)** vs Transformer O(d⁴); latency→effective-threshold honest accounting (echoes M4 rearguard). Near-duplicate positioning to paper 3; same orthogonal wedge. |
