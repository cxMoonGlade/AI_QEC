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

## Simulator source budgets / bath-spectrum anchors

| Note | One-line takeaway |
|---|---|
| [google_suppressing_errors_budget_2207.06431](google_suppressing_errors_budget_2207.06431.md) | Sycamore 72Q Table III budget: data-idle row is **19.2%** and is explicitly post-DD low-frequency-flux-noise dephasing; detector-event scale is ~0.10–0.19 per stabilizer/round. |
| [google_below_threshold_error_budget_2408.13687](google_below_threshold_error_budget_2408.13687.md) | Willow-era Table S4 budget: data idle ~20%, local CZ/SQ/readout/reset ~63%, CZ-related rows ~57%; **68/89 µs coherence is 105Q, not the 72Q Table-S4 budget device**. |
| [bylander_flux_noise_spectroscopy_1101.4707](bylander_flux_noise_spectroscopy_1101.4707.md) | Flux-qubit DD spectroscopy source for **1/f^0.9** shape over ~0.2–20 MHz; amplitude is device-specific and only bracket/design-prior for Google transmons. |
| [thermal_relaxation_stabilizer_sim_2512.09189](thermal_relaxation_stabilizer_sim_2512.09189.md) | Combined amplitude-damping+dephasing admits **exact positive Clifford+reset decomposition when T2 <= T1**; PTA misestimates LER by 2–10x depending on code state and distance — a concrete design option for our composed carrier's thermal-relaxation block. |

## Quantum-noise / record-classicality probes

| Note | One-line takeaway |
|---|---|
| [crow_joynt_classical_simulation_quantum_noise_1309.6383](crow_joynt_classical_simulation_quantum_noise_1309.6383.md) | Pure dephasing admits an exact random-unitary / classical-field simulation, while affine population-moving channels such as relaxation do not; this is the channel-layer classical-representability boundary. |
| [schoelkopf_qubits_spectrometers_quantum_noise_cond-mat-0210247](schoelkopf_qubits_spectrometers_quantum_noise_cond-mat-0210247.md) | Qubit-as-spectrometer canon: excitation samples negative-frequency noise, relaxation samples positive-frequency noise; detailed balance fixes the asymmetry in equilibrium. |
| [clerk_quantum_noise_measurement_amplification_0810.4729](clerk_quantum_noise_measurement_amplification_0810.4729.md) | RMP-level quantum-noise reference: non-symmetrized spectral density, frequency asymmetry, detailed balance, and TLS/oscillator spectrum-analyzer Golden-Rule rates. |
| [milz_when_nonmarkovian_process_classical_1907.05807](milz_when_nonmarkovian_process_classical_1907.05807.md) | Temporal process classicality = Kolmogorov consistency of sequential measurement records; owns the framework, not a QEC-specific instantiation. |
| [plenio_knight_quantum_jump_dissipative_quant-ph-9702007](plenio_knight_quantum_jump_dissipative_quant-ph-9702007.md) | Quantum-jump / MCWF canon: no-jump survival, reset after detection, waiting-time distributions, and anti-bunching / sub-Poissonian record statistics. |
| [budini_environment_nonclassicality_dissipative_2305.16136](budini_environment_nonclassicality_dissipative_2305.16136.md) | Map-level non-classicality quantifier: `Q_t=1` for unital maps (a **quantified departure-from-unitality**), dual-propagator only — operational/record definition flagged **open**; no γ/2, no additive g⁴ split. Bone A floor owner at the **channel/map** level. |
| [paz_silva_multiqubit_gaussian_quantum_noise_1609.01792](paz_silva_multiqubit_gaussian_quantum_noise_1609.01792.md) | Names S⁻ the **"quantum spectrum"** (non-zero only when the bath is quantum) + full multiqubit Gaussian cross-spectrum identifiability — but via **active control** (filter functions + tomography), 2nd-order-in-coupling, **not** passive detector records. Bone A asymmetry + Bone B continuous-Σ owner (active-control only). |
| [artag_complementary_quantum_classical_records_2605.15882](artag_complementary_quantum_classical_records_2605.15882.md) | Coherence-vs-which-path complementarity **V²+D²=1** in the *environment*, driven by conditioning + Darwinism; N̄ only smooths. A **different axis** from Bone A's N̄-driven measurement-record floor — does not pre-empt. |
| [maity_kolmogorov_classicality_signatures_2601.01122](maity_kolmogorov_classicality_signatures_2601.01122.md) | KCC-violation classicality quantifier: a **single scalar** (Eq.2) with a **multiplicative** factorization (Eq.18), manufactured by measuring *off* the pointer basis (opposite of a surviving floor); zero QEC. Does not pre-empt Bone A's additive floor⊕modulated decomposition. |
| [gicev_syndrome_error_structure_2310.12448](gicev_syndrome_error_structure_2310.12448.md) | Real IBM QEC syndrome correlations via the Chen-et-al. **signed** p_ij covariance ratio (negatives representable, ±diverging colorbar); reports only positive/excess structure, no sign-based quantum-vs-classical discriminator. **Corrects the "p_ij≥0 by construction" premise** for Bone C. |
| [bath_statistics_tagging_1907.04704](bath_statistics_tagging_1907.04704.md) | Discriminates **boson vs fermion** baths (both quantum) via single-time state-distinguishability (Helstrom / quantum Chernoff), no QEC — a weak, different-observable competitor to Bone C's detection-record-sign discriminator. |
| [vonlupke_two_qubit_spatiotemporal_noise_spectroscopy_1912.04982](vonlupke_two_qubit_spatiotemporal_noise_spectroscopy_1912.04982.md) | Two-qubit spatiotemporal cross-spectrum spectroscopy on **isolated** qubits (spin-locking + tomography); physicality is **emergent (Huber-loss robust M-estimation), not a PSD/Bochner constraint**, and **not** from QEC data. Closest Bone #3 prior art; does not pre-empt. |
| [regev_closed_form_ler_surface_2605.03054](regev_closed_form_ler_surface_2605.03054.md) | Closed-form surface-code LER for **i.i.d./single-global-mode** noise (combinatorial power-law, not a Gaussian-characteristic-function sum); no covariance interpolant, no ∂(floor)/∂f metric. Bone #2 interpolant survives. |
| [remm_syndrome_correlation_decoding_2502.17722](remm_syndrome_correlation_decoding_2502.17722.md) | Estimates **discrete independent Bernoulli error-event** probabilities (one per unique syndrome signature) by inverting detector-moment correlations (generalizes Spitz); degenerate events lumped, **no continuous-Σ identifiability/gauge map**. Bone B sliver survives. |

## Multi-time non-classicality decomposition — Claim 3 literature spine (2026-07-05 sweep)

Fifteen papers grounding the Claim 3 question: can the TV-distinguishability of passive
dual-axis syndrome records in shared-mode σ− relaxation be decomposed into
**① coherence** (genuinely quantum energy exchange), **② collectiveness** (superradiant
collective decay), and **③ finite-γ memory** (residual non-Markovianity)? The answer
from the literature: **the decomposition has not been done, but all three components
are individually well-characterized and the tools to separate them now exist.**

### Foundational theory (Markovian → non-Markovian transition)

| Note | One-line takeaway |
|---|---|
| [smirne_coherence_nonclassicality_markov_1709.05267](smirne_coherence_nonclassicality_markov_1709.05267.md) | **Theorem 2:** Under the paper's Markovian repeated-measurement assumptions, multi-time non-classicality ⇔ CGD (Coherence-Generating-and-Detecting) dynamics for the chosen observable. This is instrument/basis dependent; it does not make every amplitude-damping record non-classical. The equivalence breaks under non-Markovianity. |
| [milz_when_nonmarkovian_process_classical_1907.05807](milz_when_nonmarkovian_process_classical_1907.05807.md) | Non-Markovian classicality is tested by Kolmogorov consistency; coherence is no longer the sole driver, and system-environment correlations/discord matter. Milz's stronger class—processes non-classical under every non-trivial fixed measurement scheme—can occur only with memory; Markovian CGD processes can still be non-classical for a chosen scheme. |
| [sakuldee_commutativity_classicality_multitime_2204.11698](sakuldee_commutativity_classicality_multitime_2204.11698.md) | Multi-time Kolmogorov consistency does NOT reduce to simple operator commutation — structurally richer than the Lüders two-time case. |

### Operational frameworks for non-classicality / non-Markovianity

| Note | One-line takeaway |
|---|---|
| [budini_dni_violation_hallmark_2301.02500](budini_dni_violation_hallmark_2301.02500.md) | **DNI (Diagonal Non-Invasiveness):** the operational three-measurement protocol. Unitary s-e coupling generically violates DNI; non-unitary (Lindblad) coupling can satisfy it. I(t,τ) [Eq. 9] IS the operational K-analogue. |
| [budini_superclassical_dni_2411.13471](budini_superclassical_dni_2411.13471.md) | **Superclassical dynamics:** non-Markovian processes that satisfy DNI — memory without measurement invasiveness. Characterizes which bipartite Lindblad evolutions satisfy this. |
| [smirne_experimental_nonclassicality_coherence_1910.11830](smirne_experimental_nonclassicality_coherence_1910.11830.md) | **Only experimental paper:** linear D_K ∝ C (Kolmogorov violation ∝ coherence) demonstrated in optical quantum walk. BUT: Markovian regime only — does not address finite-γ memory. |
| [giarmatzi_witnessing_quantum_memory_1811.03722](giarmatzi_witnessing_quantum_memory_1811.03722.md) | Process-matrix formalism: quantum memory ⇔ temporal entanglement. Classical memory processes have separable process matrices. Provides entanglement-witness test for whether collectiveness ② is genuinely quantum. |

### 2026 operational decomposition & hierarchy

| Note | One-line takeaway |
|---|---|
| [luppi_multitime_beyond_QRT_2605.06427](luppi_multitime_beyond_QRT_2605.06427.md) | **Exact two-time propagator decomposition:** Φ = Φ_QRT + Φ_memory [Eq. 22]. The QRT-like term = the incoherent null model's best fit; the memory term = the TV residual. Second-order weak-coupling correction ∝ bath correlation functions. **Reduced-state NM and multitime memory are INEQUIVALENT** — they peak in different parameter regimes. |
| [gangwar_sen_genuine_nonmarkovianity_review_2603.28277](gangwar_sen_genuine_nonmarkovianity_review_2603.28277.md) | **Definitive 2026 review.** Three-tier classification: classical NM (convex mixing) ⊊ non-genuine quantum NM (mixing-induced) ⊊ genuine quantum NM (temporally-entangled process tensor). Information revivals CAN be explained classically. Process-tensor temporal entanglement = the gold standard for genuine quantum NM. |
| [taranto_hierarchy_multitime_classical_memory_2307.11905](taranto_hierarchy_multitime_classical_memory_2307.11905.md) | **Strict five-rung hierarchy:** Memoryless ⊊ Mixed ⊊ Classical ⊊ Separable ⊊ Quantum Memory. For N ≥ 3, ALL classes strictly distinct. Claim 3's confusion terms map to different rungs: ③↔Classical Memory, ②↔Separable/Quantum, ①↔Quantum Memory. |
| [zonnios_bounded_coherent_memory_2606.19511](zonnios_bounded_coherent_memory_2606.19511.md) | **MAD framework:** process distinguishability parametrized by coherent memory dimension d_A. Separates generation of new distinguishing info from propagation/decay of prior info. The user's min-TV = d_A=1 (classical records only); the residual = gap to true d_A of JC dynamics. |
| [artag_complementary_quantum_classical_records_2605.15882](artag_complementary_quantum_classical_records_2605.15882.md) | Decoherence writes TWO records into the environment: a CONCENTRATED quantum record (cat state, one mode >95%) and a REDUNDANT classical which-path record (Darwinism, R≈13 fragments). Exact identity: |σ_x| = environmental branch overlap. Temperature weakens quantum record, strengthens classical. |

### Collective vs independent dissipation

| Note | One-line takeaway |
|---|---|
| [fanchini_independent_common_nonmarkovianity_1301.3146](fanchini_independent_common_nonmarkovianity_1301.3146.md) | Systematic BLP-vs-LFS comparison across independent vs common baths. Collective dissipation produces super-additive NM; BLP and LFS can DISAGREE. Grounds Control 2: independent-AD null CANNOT reproduce collective-bath signatures. |
| [wang_collective_dephasing_common_bath_1409.0172](wang_collective_dephasing_common_bath_1409.0172.md) | **Exact analytical cross-term structure:** Γ_common = Γ_indep + 8√(J₁J₂). Constructive interference in non-single-excitation subspace, DFS in single-excitation. Adapts to σ− JC model: K(r) ∝ (1−|r|)², N-scaling saturation test. |

### Computational & factorization tools

| Note | One-line takeaway |
|---|---|
| [bracht_factorization_multitime_correlations_2605.22386](bracht_factorization_multitime_correlations_2605.22386.md) | Exact factorization of n-time correlations into products of lower-order ones for finite memory time τ_c. Temporal volume O(τ_c^n), not O(t^n). Bounds confusion term ③'s contribution: if Δt > τ_c, multi-time effects factorize. |

### Claim 3 synthesis: what the literature says

| Confusion term | Literature status | Key reference |
|---|---|---|
| ① Coherence | **Markovian:** ⇔ non-classicality (Smirne 2019). **Non-Markovian:** NOT the sole driver — discord takes over (Milz 2020). | Smirne 2019, Milz 2020, Gangwar 2026 |
| ② Collectiveness | Well-characterized analytically (Wang 2015 cross-terms) and numerically (Fanchini 2013 super-additivity). NOT captured by independent-AD null. | Wang 2015, Fanchini 2013, Taranto 2024 |
| ③ Finite-γ memory | Can be classical (Budini superclassical), quantum (Gangwar genuine NM), or protocol-dependent (Luppi QRT-memory inequivalence). | Budini 2023/2025, Luppi 2026, Bracht 2026 |
| **The decomposition** | **NOT DONE.** All components individually grounded; no one has assembled them for passive dual-axis syndrome records in shared-mode σ−. | — THIS IS THE GAP — |

### Classical vs quantum memory — is ③ genuinely quantum? (2026-07-05 supplement)

Six additional papers addressing the **narrower question**: given that the TV residual is
dominated by finite-γ multitime memory (Luppi Φ_memory, ~84% at physical γ), is this
memory **genuinely quantum** (requiring temporal entanglement / persistent quantum
environment) or **classically expressible** (superclassical / convex-mixing)?

| Note | One-line takeaway |
|---|---|
| [backer_local_disclosure_quantum_memory_2310.01205](backer_local_disclosure_quantum_memory_2310.01205.md) | **THE key paper.** Theorem 1: E♯[χ₁] < E[χ₂] ⇒ quantum memory REQUIRED. Zero-T amplitude damping ALWAYS requires quantum memory (C♯=C, non-monotonic → criterion fires). Dephasing is classical (random unitary). **Finite-T AD CAN be classical** (p₂≥0.86 region, explicit construction). Criterion uses ONLY single-time channel tomography — no multi-time statistics. |
| [backer_entropic_witness_quantum_memory_2501.17660](backer_entropic_witness_quantum_memory_2501.17660.md) | Von Neumann ENTROPY-based quantum memory witness — tractable for ANY dimension, including continuous-variable (bosonic mode). Scalable alternative to Choi-entanglement criterion. Demonstrated on damped harmonic oscillator (directly relevant to JC mode). |
| [vieira_eb_channels_quantum_memory_2402.16789](vieira_eb_channels_quantum_memory_2402.16789.md) | **Surprising caveat:** Entanglement-breaking channels are NOT classically simulable in multi-time scenarios. The Taranto-hierarchy "Classical Memory" rung (EB channel between rounds) may itself require quantum resources. "Classical enough" threshold is STRICTER than previously thought. |
| [yosifov_emergence_quantum_memory_2507.21907](yosifov_emergence_quantum_memory_2507.21907.md) | Memory type depends on RESERVOIR INITIALIZATION: GHZ state → classical memory sufficient; Bell state → quantum memory required. The user's vacuum-initialized mode is product (separable) — closer to GHZ case → suggests memory MAY be classically expressible. |
| [maity_kolmogorov_classicality_signatures_2601.01122](maity_kolmogorov_classicality_signatures_2601.01122.md) | KCC violation ⇔ non-Markovianity, linked to thermodynamic signatures (mutual information, Fano factor, entropy production). Negative-rate intervals in master equation = KCC amplification channels. |
| [luppi_temporal_nonclassicality_ctqw_2512.18873](luppi_temporal_nonclassicality_ctqw_2512.18873.md) | KCC quantifier for CTQWs: SHORT-TIME QUADRATIC scaling (~t²) vs linear single-time. MEASUREMENT-BASIS DEPENDENCE: site-basis dephasing → KCC→0; energy-basis dephasing → finite KCC. The user's dual-axis (X+Z) choice may be what makes non-classicality visible. |

### Synthesis: is the JC finite-γ memory classical or quantum?

| Factor | Leans CLASSICAL | Leans QUANTUM |
|--------|----------------|---------------|
| Channel type | — | Zero-T amplitude damping ALWAYS requires quantum memory (Bäcker 2310, Theorem 1) |
| Mode decay √γ a (effective temperature) | At finite T, AD CAN be classical (Bäcker 2310: p₂≥0.86 region). Mode decay → thermal noise → classical regime | At very low γ (near-unitary mode), close to zero-T → quantum |
| Reservoir initialization | Vacuum = separable (product) → classical per Yosifov GHZ analogy | Vacuum ≠ GHZ; has zero entanglement of any kind — may not provide the classical correlations Yosifov requires |
| Entanglement-breaking between rounds | — | EB channels are NOT classically simulable (Vieira 2025) — the "classical memory rung" may still be quantum |
| Measured observable (dual-axis X+Z) | Choice of measurement basis can render statistics classical (Luppi CTQW: site-basis dephasing kills KCC) | Dual-axis measurement may be the "energy basis" that preserves KCC violation |

**Operational verdict:** The underlying dynamics likely requires quantum memory in principle
(zero-T AD), but the user's specific operating point (γ=0.15, mode with decay, vacuum
initialization, restricted dual-axis measurements) may render the observable multi-time
statistics classically expressible. **Testable** via Bäcker 2310 criterion (compute
E♯[χ₁] vs E[χ₂] from JC reduced dynamics) or the entropy witness (Bäcker 2501).

## Correlated-noise QEC / spectroscopy anchors

| Note | One-line takeaway |
|---|---|
| [bergli_galperin_altshuler_rtn_0904.4597](bergli_galperin_altshuler_rtn_0904.4597.md) | Symmetric per-direction RTN rate `gamma` gives `C(t)=exp(-2 gamma t)`; exact free-induction coherence is non-Gaussian and independent fluctuators multiply. |
| [wold_brox_galperin_classical_telegraph_1206.2174](wold_brox_galperin_classical_telegraph_1206.2174.md) | Independent convention check: total relaxation `Gamma=Gamma_-+ + Gamma_+-=2 gamma` in the symmetric case, making its exact coherence formula identical to Bergli's. |
| [clader_correlations_heavytails_qec_2101.11631](clader_correlations_heavytails_qec_2101.11631.md) | Heavy-tailed coherent rotation noise plus spatial/temporal correlation can reduce effective code distance; correlated Cauchy noise gives no protection. |
| [harper_flammia_learning_correlated_39q_2303.00780](harper_flammia_learning_correlated_39q_2303.00780.md) | Real Sycamore 39-qubit correlated Pauli-noise learning; richer correlated models are needed for sub-threshold logical-rate prediction. |
| [layden_common_fluctuator_qec_1903.01046](layden_common_fluctuator_qec_1903.01046.md) | Common-fluctuator dephasing is a shared collective-Z source; the paper designs tailored non-Pauli codes, not surface-code detector statistics. |
| [quasistatic_phase_damping_stabilizer_2401.04530](quasistatic_phase_damping_stabilizer_2401.04530.md) | Quasistatic coherent phase damping is constant within a shot and resampled shot-to-shot; one cycle matches i.i.d. phase flips, multi-cycle records differ. |
| [rojas_arias_si_spin_correlated_scaling_2603.03051](rojas_arias_si_spin_correlated_scaling_2603.03051.md) | Silicon spin-qubit dephasing correlations: global magnetic drift is dangerous, measured short-range charge-noise correlations are mostly benign at fixed marginal. |
| [wang_symmetry_correlated_thresholds_2506.15490](wang_symmetry_correlated_thresholds_2506.15490.md) | Spatially correlated Pauli errors can help or hurt depending on whether their support is stabilizer-like or logical-like. |
| [paz_silva_multiqubit_gaussian_quantum_noise_1609.01792](paz_silva_multiqubit_gaussian_quantum_noise_1609.01792.md) | Active-control multiqubit QNS reconstructs Gaussian auto/cross spectra, including asymmetric quantum spectra. |
| [vonlupke_two_qubit_spatiotemporal_noise_spectroscopy_1912.04982](vonlupke_two_qubit_spatiotemporal_noise_spectroscopy_1912.04982.md) | Experimental two-qubit spectroscopy reconstructs self/cross spectra with spin-locking and robust M-estimation, not QEC detector records. |
| [gicev_syndrome_error_structure_2310.12448](gicev_syndrome_error_structure_2310.12448.md) | IBM heavy-hex syndrome correlations reject uniform depolarizing assumptions and show biased, inhomogeneous, spatiotemporal structure. |
| [remm_syndrome_correlation_decoding_2502.17722](remm_syndrome_correlation_decoding_2502.17722.md) | Syndrome-moment inversion estimates independent error-event probabilities directly from stabilizer records. |

## Non-Markovian noise learning & engine landscape (2026-07-03 payoff)

| Note | One-line takeaway |
|---|---|
| [montanalopez_nonmarkovian_learning_manybody_2511.16772](montanalopez_nonmarkovian_learning_manybody_2511.16772.md) | Provably efficient DESIGNED-experiment learning of Gaussian-environment kernel Taylor data / all-to-all coefficient covariance (log-N); no passive-record question, no gauge characterization, no PSD constraint, no QEC — B.1/#3.1 no-owner verdicts stand; mandatory third positioning corner beside Chen/Zheng. |
| [dong_nongaussian_digital_qns_2502.05408](dong_nongaussian_digital_qns_2502.05408.md) | Non-Gaussian correlated dephasing learned under digital control; resource cost scales with control complexity, not noise truncation order — the recent cost-of-lifting-Gaussianity endpoint for our Step 0.α boundedness discussion. |
| [bhardwaj_drifting_noise_estimation_2511.09491](bhardwaj_drifting_noise_estimation_2511.09491.md) | Sliding-window Pauli noise estimation from QEC syndrome statistics (Spitz formula); closed-form detector stat inversion, low-pass filter interpretation; no gauge degeneracy discussion — depolarizing symmetry may be hiding identifiability gaps. |
| [bhardwaj_adaptive_drifting_noise_2511.09491](bhardwaj_adaptive_drifting_noise_2511.09491.md) | PRX Quantum accepted 2026. Adaptive tracking of time-dependent Pauli noise from syndrome data; analytic window-size optimization and frequency-domain characterization. |
| [kobori_todo_bayesian_noise_parameters_2406.08981](kobori_todo_bayesian_noise_parameters_2406.08981.md) | Bayesian MCMC/SMC inference of general noise parameters from surface code syndrome statistics; beyond Pauli (amplitude damping). |
| [nonmarkovian_noise_sources_qem_2302.05053](nonmarkovian_noise_sources_qem_2302.05053.md) | Early (2023) study: non-Markovian noise sources increase QEM cost as system-bath coupling intensifies; spin-boson model anchor. |
| [nonmarkovian_noise_mitigation_spectral_2501.05019](nonmarkovian_noise_mitigation_spectral_2501.05019.md) | NMNM: time-local quantum master equation from bath correlation functions; describes HOW TO SIMULATE non-Markovian noise on classical devices; spectral property → QEM overhead direct connection. |
| [rb_forecasting_correlated_2312.06062](rb_forecasting_correlated_2312.06062.md) | RB extended to characterize and FORECAST temporally correlated (non-Markovian) processes; superconducting hardware demonstration from Markovian to highly non-Markovian. |
| [probing_nonmarkovian_noise_pmme_2510.12894](probing_nonmarkovian_noise_pmme_2510.12894.md) | Li, Tan, Gucev, Lidar: PMME on IBM hardware; channel-resolved memory kernels; crosstalk can DOMINATE non-Markovian effects; CP-divisibility violations and QMI revivals quantified. |
| [classical_nonmarkovian_symmetry_2501.06619](classical_nonmarkovian_symmetry_2501.06619.md) | Classical non-Markovian noise in symmetry-preserving quantum dynamics; classical noise fields under Lie-group symmetry constraints. |

## Non-Markovian QEC simulation & beyond-Pauli simulators (2023–2026)

| Note | One-line takeaway |
|---|---|
| [qmctwin_master_equation_digital_twin_2606.19848](qmctwin_master_equation_digital_twin_2606.19848.md) | **Closest pre-empting work.** QMC + toggling-frame Lindblad ME for d=7 surface code (97q); coherent+dissipative+ZZ crosstalk; syndrome-extraction biases 7.5× vs Pauli-twirled; MARKOVIAN only, no leakage/qutrit, no independent exact oracle (conceded infeasible at 4⁹⁷) — our wedge: leakage, non-Markovian, independent oracle. |
| [quiroz_sparse_nonmarkovian_noise_modeling](quiroz_sparse_nonmarkovian_noise_modeling.md) | Sparse non-Markovian noise modeling for transmon multi-qubit ops; 7 IBM devices, 39 qubits; LME+stochastic-Hamiltonian+channel hybrid; 7× predictive accuracy; 64% qubits Markovian, 26% correlated dephasing, 10% correlated control noise. |
| [kam_nonmarkovian_surface_code_2410.23779](kam_nonmarkovian_surface_code_2410.23779.md) | "Streaky" temporal correlations in surface code memory; Stim+custom correlated sampling; multi-time correlations on syndrome qubits form temporal stringlike errors degrading LER scaling. |
| [kam_spatiotemporal_pauli_processes_2603.05474](kam_spatiotemporal_pauli_processes_2603.05474.md) | SPP framework: multi-time Pauli twirl maps non-Markovian dynamics to Pauli process; TN representations; d=19 surface code; pseudo-critical regime with error avalanches. |
| [qec_beyond_pauli_stochastic_sim_2603.18457](qec_beyond_pauli_stochastic_sim_2603.18457.md) | Sandia EEG→DEM toolchain; coherent errors shift thresholds, 8× LER increase vs stochastic; Markovian only, leakage explicitly excluded. |
| [qec_coherent_errors_dem_2510.23797](qec_coherent_errors_dem_2510.23797.md) | Duke: syndrome history detects coherent errors without prior benchmarking; DEM hyperedges absent in Pauli-twirled models; coherent decoding threshold ~2.5% vs stochastic 2.85%. |
| [harper_nonclifford_crosstalk_surface_2605.29514](harper_nonclifford_crosstalk_surface_2605.29514.md) | Hybrid stabilizer-TN sim of coherent ZZ crosstalk; χ_max=32 MPS; threshold ~0.8%; θ≈10⁻³ coherent rotations. |
| [nonmarkovian_noise_resilience_silicon_spin_2507.08713](nonmarkovian_noise_resilience_silicon_spin_2507.08713.md) | Silicon spin qubits under 1/f noise; QEC Markovianizes non-Markovian physical noise → T_L ∝ T_phys⁴; contrasts Kam (catastrophic temporal correlations) vs this (beneficial). |
| [thermal_relaxation_stabilizer_sim_2512.09189](thermal_relaxation_stabilizer_sim_2512.09189.md) | Exact Clifford+reset decomposition for thermal relaxation when T2 ≤ T1; PTA misestimates LER by 2–10×; design option for composed carrier. |
| [noise_adapted_qec_nonmarkovian_2411.09637](noise_adapted_qec_nonmarkovian_2411.09637.md) | Petz recovery map for non-Markovian QEC; generalizes AQEC to HPTP (NCP) maps; outperforms standard stabilizer QEC for non-Markovian amplitude damping. |
| [nonmarkovian_feedback_qec_gkp_2312.07391](nonmarkovian_feedback_qec_gkp_2312.07391.md) | Non-Markovian feedback for GKP QEC; realistic cavity-ancilla simulation; non-Markovian strategy uses all past observations. |
| [limitations_dynamical_error_suppression_correlated_noise_2407.04766](limitations_dynamical_error_suppression_correlated_noise_2407.04766.md) | Nonclassical temporally correlated noise causes bath-mediated error propagation DESPITE perfect reset; gate fidelity strictly saturates; PRX Quantum 2025. |
| [facets_correlated_nonmarkovian_channels_2401.05499](facets_correlated_nonmarkovian_channels_2401.05499.md) | Modified OU noise, RTN, non-Markovian amplitude damping with correlation factor μ; QEC success probability linked to μ. |

## Gauge / identifiability / unlearnable noise in QEC (2023–2026)

| Note | One-line takeaway |
|---|---|
| [chen_learnability_pauli_noise_2206.06362](chen_learnability_pauli_noise_2206.06362.md) | Pauli noise on Clifford gate sets: learnable = cycle space, gauge = cut space (complete partition); the structural template. |
| [qec_learnable_logical_noise_2601.22286](qec_learnable_logical_noise_2601.22286.md) | Zheng et al.: N&S learnability conditions for Pauli noise from syndrome data; Walsh-Hadamard, gauge group = unlearnable subspace; Pauli-only, coherent outside formalism. |
| [lee_gauging_spacetime_code_2606.05664](lee_gauging_spacetime_code_2606.05664.md) | Detectors = Wilson loops = gauge-invariant observables = learnable DOF; Z2 lattice gauge theory on Clifford circuits; discrete Pauli, not continuous Σ. |
| [chu_learning_mcm_backaction_2606.00433](chu_learning_mcm_backaction_2606.00433.md) | Learns Z-twirled MCM instrument from 3 repeated MCMs; one-parameter continuous gauge bounded by physicality; **closest discrete-Pauli analogue to our continuous-Σ gauge** — identical methodology (parameter counting, gauge matrix, physicality-bounded bands). |
| [unlearnable_noise_mcm_benchmarking_2606.29638](unlearnable_noise_mcm_benchmarking_2606.29638.md) | **Jun 30, 2026.** MCM-based cycle benchmarking isolates unlearnable Pauli components; "Pauli eigenvalues identifiable only up to multiplicative gauge factor"; superconducting hardware validation. |
| [srivastava_rb_blindspots_2510.13051](srivastava_rb_blindspots_2510.13051.md) | ZZ-coupling Hamiltonians produce CCC-type non-Markovian noise **completely invisible to RB**; identifies the RB-blind Hamiltonian class; maximal CCC mixing can suppress diamond errors from O(δ) to O(δ²). |

## Tensor-network / process tensor / pseudomode infrastructure (2024–2026)

| Note | One-line takeaway |
|---|---|
| [keeling_process_tensor_2509.07661](keeling_process_tensor_2509.07661.md) | PRX 16, 020502 (2026). Landmark Perspective unifying HEOM/TEDOPA/GQME/HOPS under PT-MPO; PT-MPO = pseudomode equivalence (Sec III.2); temporal entanglement diagnostic for non-Markovianity. |
| [keeling_process_tensor_perspective_2509.07661](keeling_process_tensor_perspective_2509.07661.md) | Companion note with additional detail on PT-TN software ecosystem (ACE, OQuPy, MPSDynamics, etc.) and Gaussian process tensor factorization. |
| [ace_process_tensor_toolkit_2405.19319](ace_process_tensor_toolkit_2405.19319.md) | ACE: C++ toolkit for non-Markovian OQS via PT-MPO; million-step divide-and-conquer; config-file driven, no programming. |
| [coupled_lindblad_pseudomode_2506.10308](coupled_lindblad_pseudomode_2506.10308.md) | Huang et al.: gauge transformation maps quasi-Lindblad→coupled-Lindblad, achieving CPTP with polylog(T/ε) modes; robust SDP construction. |
| [sander_tjm_tensor_jump_2501.17913](sander_tjm_tensor_jump_2501.17913.md) | TJM: MCWF-on-MPS with hybrid 1TDVP/2TDVP; 1000-spin Heisenberg benchmark; Markovian Lindblad only; collective (multi-site) jump operators not supported. |
| [froehlich_tensor_jump_method_2607.01323](froehlich_tensor_jump_method_2607.01323.md) | cTJM: MPS+TDVP with sparse Pauli-Lindblad noise; correlated multi-qubit noise + crosstalk; 127-qubit IBM benchmark; Pauli-only SPLM assumption excludes coherent wedge. |
| [sander_computational_regimes_mps_trajectories_2606.13779](sander_computational_regimes_mps_trajectories_2606.13779.md) | (α,κ) cost-decision layer ON TJM (not a new kernel): bond inflation α vs sampling inflation κ, κ=α³/α⁵ hardware boundaries, pilot-extraction protocol; lower χ ≠ lower total cost; no mid-circuit measurements, spin-1/2 Lindblad only. |
| [shao_complexity_tn_noisy_circuits_2606.00474](shao_complexity_tn_noisy_circuits_2606.00474.md) | Rigorous OEE bounds: depolarizing→poly bond dim; coherent noise has c=1 (no contraction) — theorem-level formalization of our coherent wedge for MPS carrier. |
| [spinpulse_2601.10435](spinpulse_2601.10435.md) | Pulse-level spin qubit simulator with classical non-Markovian 1/f noise; quimb MPS integration; minimal QEC (cluster-state demo only). |
| [tn_decoders_process_tensor_nonmarkovian_2412.13739](tn_decoders_process_tensor_nonmarkovian_2412.13739.md) | Process tensor + TN for ML decoding under non-Markovian/crosstalk noise; 5-qubit perfect code + 7-qubit Steane code. |
| [time_invariant_process_tensors_2603.06840](time_invariant_process_tensors_2603.06840.md) | Time-invariant PT construction for stationary non-Markovian processes; efficient contraction. |
| [chain_mapping_block_lanczos_shared_bath_2407.10140](chain_mapping_block_lanczos_shared_bath_2407.10140.md) | Block Lanczos chain mapping for shared baths; efficient T-TEDOPA variant. |
| [leakage_tensor_network_simulation_2308.08186](leakage_tensor_network_simulation_2308.08186.md) | Qutrit-MPS leakage trajectories for repetition and thin `3×d` surface codes; in the reported `d=19` MLR comparison, an `L1,L2`-matched GTA overestimates LER by >3×. This is not a full-record, DEM/Markov-`k`, or universal-conservativeness theorem. |
| [jaschke_open_quantum_tensor_networks_1804.09796](jaschke_open_quantum_tensor_networks_1804.09796.md) | Early (2018) open quantum TN methods overview. |
| [sander_computational_regimes_mps_trajectories_2606.13779](sander_computational_regimes_mps_trajectories_2606.13779.md) | **(α,κ) MPS cost-decision framework:** bond-dimension inflation α + sampling inflation κ. Lower χ does NOT guarantee lower total cost — sampling overhead can dominate. Decision boundaries κ=α³ (thread-limited) and κ=α⁵ (memory-limited). Pilot extraction protocol for choosing optimal MCWF unraveling under our 65GB/GPU-serialized constraints. |

## GPU batched trajectory execution & operator fusion — the "vmap/quimb hot-loop" problem (2026-07-06 sweep)

Six papers addressing the **engineering bottleneck**: each JC syndrome round makes 70–90
small quimb operator calls in a Python loop; many independent trajectories (shots) need
batching; per-operator launch overhead dominates runtime.

| Note | One-line takeaway |
|---|---|
| [patti_ptsbe_2504.16297](patti_ptsbe_2504.16297.md) | **PTSBE (NVIDIA):** pre-sample ALL stochastic noise decisions BEFORE state evolution → group identical patterns → evolve once per group. 35q QEC: 10⁶× speedup; 85q TN: 16×. Generated 1 trillion shots in 4,445 H100 GPU-hours. In production as `cudaq.ptsbe.sample()` (>10⁷× for non-proportional). **Pre-sample JC jumps, group by identical jump sequences, batch evolve.** |
| [doi_batch_shots_gpu_2308.03399](doi_batch_shots_gpu_2308.03399.md) | **Qiskit-Aer multi-shot GPU:** batch-shots (all shots in single kernel, ID-gate padding) + shot-branching (tree-structured state sharing — branch only when randomness occurs). Before the first JC jump, ALL trajectories share identical evolution. |
| [jiang_bqsim_gpu_batch_dd_2503_asplos](jiang_bqsim_gpu_batch_dd_2503_asplos.md) | **BQSim (ASPLOS'25):** Decision-Diagram gate fusion (1.4–6.7×) → DD-to-ELL GPU kernel → task-graph overlap (1.5–1.7×). 3.25× vs cuQuantum, 159× vs Qiskit Aer. **Compile MPO once per fused operator group, reuse across trajectories; overlap MPS contraction with data transfer.** |
| [zhang_tensorcircuit_ng_2602.14167](zhang_tensorcircuit_ng_2602.14167.md) | **TensorCircuit-NG:** JAX/XLA trace-once → compile → operator fusion → vmap over shots. MPS backend with differentiable SVD. quimb interop (`qop2quimb`/`quimb2qop`). 0.084s/trajectory on H200 for 20q/40-layer MIPT. **THE direct "replace serial quimb hot loop" path.** |
| [schieffer_cudaq_mps_2501.15939](schieffer_cudaq_mps_2501.15939.md) | **CUDA-Q MPS on Grace Hopper:** SVD phase = 70% time, 33% GPU activity, <1% Tensor Core utilization. Contractions idle 60% from 128-byte host-to-device transfers. Best batch size: χ_max≥16 minimum. **Profiles EXACTLY our GPU bottlenecks.** |
| [patti_batched_tn_sampling_2604.08467](patti_batched_tn_sampling_2604.08467.md) | **UPV+NBS (NVIDIA):** fuse error→gate tensors preserving topology, batch multiple bitstrings per contraction, flexible batch sizing. Optimal b=10 gives 282 qubits/s vs CUDA-Q default b=24 at 11 qubits/s — 25× improvement. Non-proportional: 10⁸× data speedup. **Sub-warp batching for our 70-90 small independent contractions/round.** |

### Tactical stack mapping

```
Current:  for op in 70-90 ops: quimb.apply(op, state)   ← Python overhead × 70–90
                                                              per trajectory, per round

Optimize: ① TensorCircuit-NG: trace once → XLA fuse → zero Python loop
          ② cuQuantum MPS: gate fusion → batched GPU contraction
          ③ PTSBE: pre-sample jumps → group identical → evolve once per group
          ④ Batched TN (UPV): pack 70-90 small contractions → sub-warp batches
```

## Engine landscape + simulation methods (supplementary)

| Note | One-line takeaway |
|---|---|
| [xu_ankerhold_qdmess_nonmarkovian_review_2601.02160](xu_ankerhold_qdmess_nonmarkovian_review_2601.02160.md) | QD-MESS unifying review: HEOM/pseudomodes/chains/stochastic unravelings = one kernel, different reservoir-mode representations. |
| [li_yan_dqme_sq_quantum_simulation_2401.17255](li_yan_dqme_sq_quantum_simulation_2401.17255.md) | DQME-SQ second-quantized dissipaton, quantum-circuit representable, any Gaussian environment. |
| [shen_lidar_realtime_signproblem_qmc_2502.18929](shen_lidar_realtime_signproblem_qmc_2502.18929.md) | Shen/Lidar real-time sign-problem-suppressed QMC; precursor to QMCtwin; non-Markovian master equations supported. |
| [spatially_correlated_noise_driven_qubits_2308.03054](spatially_correlated_noise_driven_qubits_2308.03054.md) | Zou/Bosco/Loss (npj QI 2024): analytical study of driven qubits under spatially correlated classical vs quantum noise; noise-induced coherent interactions (Ising, exchange, DM). |
| [spam_robust_noise_spectroscopy_2402.12361](spam_robust_noise_spectroscopy_2402.12361.md) | SPAM-robust multi-axis noise spectroscopy; non-Markovian qubit dynamics from microscopic noise models. |
| [gle_memory_kernel_learning_apriori_2402.11705](gle_memory_kernel_learning_apriori_2402.11705.md) | GLE memory kernel learning with a-priori physical constraints. |

## PEPO (Projected Entangled Pair Operator) — 2D open-system TN carrier (2026-07-09 sweep)

Fifteen foundational and cutting-edge papers covering the full PEPO literature:
origin iPEPO, stable algorithms (FET/WTG), truncation methods (NTU/GTU/LU), QEC
applications, simplified constructions, non-Markovian process-tensor connections,
and GPU-compatible contraction. **Synthesized map:** `outputs/papers/pepo_survey/PEPO_COMPREHENSIVE_MAP.md`.

### Foundation — iPEPO origin + stable algorithms

| Note | One-line takeaway |
|---|---|
| [kshetri_weimer_orus_origin_ipepo_1612.00656](kshetri_weimer_orus_origin_ipepo_1612.00656.md) | **Origin iPEPO** (Nat. Commun. 2017): parallelism between imaginary-time ground-state evolution and real-time Lindblad steady-state evolution; simple-update truncation, CTM contraction. SU is environment-blind in 2D; later FET/WTG methods improve the objective in tested regimes but do not make it certified. |
| [evenbly_gauge_closed_loops_1801.05390](evenbly_gauge_closed_loops_1801.05390.md) | **WTG/FET foundation (PRB 2018):** top-WTG truncation is optimal at zero cycle entropy and only heuristically near-optimal when small. At nonzero cycle entropy the paper proposes iterative FET; it gives no deterministic global-optimum or QEC-record theorem. |
| [mc_keever_stable_ipepo_fet_wtg_2012.12233](mc_keever_stable_ipepo_fet_wtg_2012.12233.md) | **FET+WTG (PRX 2021):** mixed-state FET uses an alternative Hilbert-Schmidt fidelity and approximate CTMRG environment. Its ~10× SU improvement is benchmark-specific; it is not a long-range-record guarantee. |
| [kilda_ipepo_stability_2012.03095](kilda_ipepo_stability_2012.03095.md) | **iPEPO stability (SciPost 2021):** near dissipative critical points (J_y≲1.32 for XYZ), SU-iPEPO becomes UNSTABLE. D does NOT help monotonically (D=12 works, D=14 fails). εΛ diagnostic. Most actionable: upgrade to FET before committing to 2D carrier. |

### Truncation methods (截断) — from SU to GTU

| Note | One-line takeaway |
|---|---|
| [dziarmaga_ntu_truncation_2107.06635](dziarmaga_ntu_truncation_2107.06635.md) | **NTU (PRB 2021):** bridge between SU and FU. Exact NN-environment contraction → Hermitian non-negative metric → guaranteed stability. ξ~20 at O(D⁸) parallel cost. Demonstrated on thermal-state iPEPO (density matrices). **Direct drop-in replacement for itrSU in tePEPO — ~10× ξ gain.** |
| [dziarmaga_gtu_truncation_2205.11067](dziarmaga_gtu_truncation_2205.11067.md) | **GTU (PRB 2022):** direct overlap maximization in iPEPS tangent space via CTMRG Gramm-Schmidt gradient. SVDU→NTU→GTU 3-stage pipeline. ξ~30+. Extension to PEPO mixed states formally straightforward but costlier. Correct formalism, not drop-in ready. |
| [zheng_yang_loop_update_1906.04085](zheng_yang_loop_update_1906.04085.md) | **Loop Update:** cyclic optimal truncation on 4-site plaquette as MPS with PBC → canonicalization → FET. SU error ~40% larger than LU at D=6. Transfers directly to PEPO geometry; candidate drop-in for itrSU truncation step. |

### PEPO constructions — simplified + cluster expansion

| Note | One-line takeaway |
|---|---|
| [orourke_chan_simplified_pepo_1911.04592](orourke_chan_simplified_pepo_1911.04592.md) | **gMPO reformulation (PRB 2020):** PEPO → sequential bipartition MPO-like operators; on-the-fly expectation values. 20–60× over PEPOs for finite-range, ~600× for long-range. Gaussian basis technique for isotropic spatial correlations. |
| [vanhecke_cluster_expansion_pepo_1912.10512](vanhecke_cluster_expansion_pepo_1912.10512.md) | **Cluster expansion PEPO (PRA 2021):** organizes exp(t Σ h_i) by connected-cluster size → infinite-order exact per cluster. Preserves ALL symmetries. Large timestep δt=2.1 achievable. **CPTP not guaranteed** (inclusion-exclusion can create negative Choi eigenvalues). |

### QEC applications — PEPO for surface codes + decoding

| Note | One-line takeaway |
|---|---|
| [manabe_suzuki_darmawan_leakage_tn_2308.08186](manabe_suzuki_darmawan_leakage_tn_2308.08186.md) | **Leakage TN thin strip (NJP 2025):** MPS-based, 3×d strip ONLY — SVD bottleneck at d≥5 even on thin strip. Area-law-in-time saturation = encouraging for 2D-PEPO path. Explicitly calls for PEPS/isoTNS for full d×d. |
| [marshall_kafri_incoherent_leakage_sta_2312.10277](marshall_kafri_incoherent_leakage_sta_2312.10277.md) | **Exact qutrit vs STA (PRApplied 2025):** measurement can suppress computational/leakage coherence, but pure coherent-CZ d3 detector/LER outputs still differ from channel-level STA; arbitrary per-slice pinching is not the same operation. |
| [liao_heisenberg_pepo_2308.03082](liao_heisenberg_pepo_2308.03082.md) | **Heisenberg-picture PEPO:** χ=2 matches MPO χ=1024 via operator compression + 2D geometry. 127-qubit exact result in 3s CPU. Near-Clifford (near-identity) noise is similarly compressible. Cannot directly handle CPTP channels but near-unitary coherent errors stay efficient. |
| [piveteau_tn_decoding_2310.10722](piveteau_tn_decoding_2310.10722.md) | **TN decoding beyond 2D (PRX Quantum 2024):** PEPS sweeping + SU for 3D codes. Snaking procedure compresses circuit-level noise into cubic lattice. Assumes known noise models — incompatible with twin's recovery goal. |
| [rudolph_tindall_gpu_peps_2507.11424](rudolph_tindall_gpu_peps_2507.11424.md) | **GPU PEPS sampling:** generalized boundary MPS contraction for ANY planar topology. 35×+ GPU speedup. Heavy-hex (IBM) vs Willow (rotated-square) loop correlation divergence. Maps to PEPO contraction but: no mixed-state demo, no mid-circuit measurement, noiseless-only. |

### Non-Markovian bridge — TEMPO, process tensor, process trees

| Note | One-line takeaway |
|---|---|
| [strathearn_tempo_1802.03160](strathearn_tempo_1802.03160.md) | **TEMPO (Nat. Commun. 2018):** influence functional→temporal MPO; SVD compression. K=200 steps (10× over QUAPI). 1D temporal axis. **Spatial PEPO + temporal TEMPO = 3D TN — the central architectural open problem.** |
| [jorgensen_pollock_pt_tempo_1902.00315](jorgensen_pollock_pt_tempo_1902.00315.md) | **PT-TEMPO (PRL 2019):** process tensor unifies influence functional; LOCAL boundary → 1–2 orders speedup. Temporal MPO per site, but outer bond dim scales as d^{2N} for N qubits. **Oracle tier** for small-window forward model, not full carrier. |
| [dowling_process_trees_2312.04624](dowling_process_trees_2312.04624.md) | **Process trees (PRX 2024):** tree-geometry process tensor via 2D TRG from Feynman-Vernon IF. Polynomial temporal decay. 2–60× fewer parameters than MPO near phase transitions. **Single-qubit temporal only** — not spatial. Complementary to iPEPO, not a replacement. |

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
