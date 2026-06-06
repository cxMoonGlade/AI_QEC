# Cached Reference Papers

Local PDF cache of the load-bearing references behind the identifiability /
counterfactual-validity work. Goal: avoid repeated web search. Each entry gives
the citation, why it matters here, and which doc / action item it backs.

Companion docs:
- `docs/IDENTIFIABILITY_AND_CRL_SURVEY.md` — CRL / identifiable-latent-variable survey.
- `docs/adr/0006-cptp-twin-build-order.md`, `docs/adr/0007-b-validation-methodology.md` — the B-path plan these references inform.

Note on attribution: arXiv IDs are verified (the PDF resolves to the stated
title). For a few entries the exact author list is given as "see arXiv abstract"
to avoid misattribution; trust the arXiv ID over any remembered author list.

---

## Finance — calibration as an inverse problem (the master analogy)

The QEC label-free calibration problem (`E ← syndrome stats`) is structurally the
derivatives-calibration inverse problem (`vol surface ← option prices`). These
five papers carry that analogy.

| File | Citation | Why it matters |
|---|---|---|
| `cont2006_model_uncertainty.pdf` | Cont (2006), *Model Uncertainty and Its Impact on the Pricing of Derivative Instruments*, Math. Finance 16(3):519–547. | Coherent measure of model uncertainty = range of a quantity over the SET of models consistent with market. Direct template for the **alias-induced knob band**: report `[min,max] ΔLER` over CPTP fields consistent with the syndrome stats. Backs the model-uncertainty-band addition to B5 and memory mitigation (4). |
| `fouque_uvm_stochastic_bounds.pdf` | Fouque et al., *Uncertain Volatility Models with Stochastic Bounds*. | Avellaneda UVM / Black–Scholes–Barenblatt worst-case pricing over a parameter band. Template for a **computable worst-case `ΔLER`**. ⚠ The UVM pointwise-extremize shortcut needs monotonicity (vega>0); LER is NOT monotone in channel params, so QEC must extremize numerically over the CPTP-consistent set. |
| `finance_localvol_convex_regularization_1211.0170.pdf` | Albani & Zubelli (arXiv:1211.0170), *Online Local Volatility Calibration by Convex Regularization (Morozov + convergence rates)*. | Local-vol calibration is a provably **ill-posed inverse problem**; the fix is regularization toward a prior. Gives `CPTP + locality + orbit-sharing` a precise identity: they are the regularization operator that selects within the alias class, not just "interpretability." |
| `gierjatowicz2020_neural_sdes.pdf` | Gierjatowicz, Sabate-Vidales, Šiška, Szpruch, Žurič (2020), *Robust Pricing and Hedging via Neural SDEs* (arXiv:2007.04154). | Closest finance analogue to the amortized `f_ψ(c)` + differentiable-forward calibration: learn drift/diffusion as NNs, calibrate to instruments, get **robust (worst-case over the calibrated set) price/hedge bounds** with P- and Q-measure consistency. |
| `fouque_mcmc_multiscale_sv.pdf` | Fouque et al., *McMC Estimation of Multiscale Stochastic Volatility Models*. | Two-timescale (fast mean-reverting + slow) latent vol with MCMC/particle estimation. Template for **Google 15 h slow calibration drift + fast shot noise**; informs C-stage drift tracking and what to log (timestamped calibration windows). |

## Identifiability / Causal Representation Learning

| File | Citation | Why it matters |
|---|---|---|
| `khemakhem2020_ivae.pdf` | Khemakhem, Kingma, Monti, Hyvärinen (2020), *Variational Autoencoders and Nonlinear ICA: A Unifying Framework* (iVAE, arXiv:1907.04809). | The central identifiability tool. With auxiliary variable `u` (= contexts `r=0..4`), latents are identified up to permutation + element-wise transform — exactly shrinking the alias quotient. Invertibility condition bounds how many mechanisms `5` contexts can separate. Survey §iVAE; action P1. **Apply at polarization level, not raw binary syndromes.** |
| `moran2022_sparse_vae_identifiable.pdf` | Moran, Sridhar, Wang, Blei (2022), *Identifiable Deep Generative Models via Sparse Decoding* (arXiv:2110.10804). | Anchor-feature identifiability: each mechanism needs ≥2 syndrome bits that fire for it alone — **checkable today from the DEM parity map `A`**. Gives the no-modeling-assumption ceiling on which catalog mechanisms are identifiable. Survey §Sparse VAE; action **P0**. |
| `lachapelle2022_mechanism_sparsity.pdf` | Lachapelle, Brouillard, Deleu, Lacoste-Julien (2022), *Disentanglement via Mechanism Sparsity Regularization* (arXiv:2107.10098). | Regularizing the decoder to the known sparse DEM footprint achieves identifiability up to permutation — physical sparsity AS an identification constraint. Apply to the `diff_cptp_channel` decoder. Action P1. |
| `heinze_deml2018_nonlinear_icp.pdf` | Heinze-Deml, Peters, Meinshausen (2018), *Invariant Causal Prediction for Nonlinear Models* (arXiv:1706.08576). | ICP in recovered-mechanism space: which mechanisms have an invariant `p(P_L \| m_S)` across contexts → causal parents of LER. Two-stage (recover then test). Survey §ICP; action P3. |
| `squires2020_ut_igsp.pdf` | Squires et al. (2020), *Permutation-Based Causal Structure Learning with Unknown Intervention Targets* (UT-IGSP, arXiv:1910.09007). | Multi-environment causal discovery when each environment perturbs an **unknown** subset of mechanisms — the realistic case, since no context isolates one mechanism. Orients the mechanism interaction graph. Action P3. |
| `mooij2022_sparse_mechanism_shift.pdf` | *Causal Discovery in Heterogeneous Environments Under the Sparse Mechanism Shift Hypothesis* (arXiv:2206.02013; see abstract for authors). | Variance heterogeneity across environments (weakest shift) suffices to orient edges Markov-equivalence can't. Maps onto contexts that change the variance of coherent-sensitive syndrome bits. Action P3. |
| `nasr2023_counterfactual_nonidentifiability.pdf` | *Counterfactual (Non-)identifiability of Learned Structural Causal Models* (arXiv:2301.09031; see abstract for authors). | The impossibility theorem: with general multi-dim exogenous noise, counterfactuals are NOT point-identified from observational data even with known structure. The formal core of "observational ≠ interventional" — the binding reason ADR 0006 validates the loop on a controlled teacher first. Survey W1. |

## QEC noise learning from syndromes (in-domain version of the same problem)

| File | Citation | Why it matters |
|---|---|---|
| `qec_learnable_logical_noise_2601.22286.pdf` | *Efficient learning of logical noise from syndrome data* (arXiv:2601.22286, 2026). | Necessary & sufficient conditions + explicit **learnable degrees of freedom** of circuit-level Pauli faults from syndromes (Fourier / compressed sensing, sample-complexity guarantees). The information-theoretic ceiling any identifiability claim must respect (survey W2; action **P0**). In-domain form of the Girsanov "what is identifiable" question. |
| `qec_insitu_benchmarking_clifford_2601.21472.pdf` | *In-situ benchmarking of fault-tolerant quantum circuits. I. Clifford circuits* (arXiv:2601.21472, 2026). | Learnability conditions for physical AND logical noise from given syndrome data; predicts logical fidelity with polynomial samples even at exponentially-suppressed LER. Companion ceiling/feasibility result to 2601.22286. |
| `qec_dem_estimation_syndrome_2504.14643.pdf` | *Estimating detector error models from syndrome data* (arXiv:2504.14643, 2025). | The DEM-from-syndrome baseline (Walsh–Hadamard). This is the **moment-matching baseline** that ADR 0007 keeps only as a negative control (it Pauli-shadows coherent structure). |
| `qec_coherent_errors_dem_2510.23797.pdf` | *Estimating and decoding coherent errors of QEC experiments with detector error models* (arXiv:2510.23797, 2025). | Coherent errors as DEM hyperedges / interference in syndrome fire rates → why `r=4` phase-sensitive probes are required. The "drift" subspace of the Girsanov reframe; the exact slice B5 must attack (survey W5). |
| `qec_differentiable_mle_noise_2602.19722.pdf` | *Differentiable Maximum Likelihood Noise Estimation for Quantum Error Correction* (arXiv:2602.19722, 2026). | Differentiable MLE of noise from syndromes — **directly parallel to `diff_circuit_sim` / `recover_channel` NLL calibration**. Closest external prior art; benchmark the B-path calibration against it. |

---

## How to add a paper

```bash
curl -L --fail -o docs/papers/<descriptive_name>.pdf <pdf_url>
```

arXiv PDFs: `https://arxiv.org/pdf/<id>`. Verify with
`head -c4 docs/papers/<file>.pdf` returning `%PDF`. Then add a row above with the
citation and the reason it earns a slot.

---

## Reference implementations (cloned locally)

Reference code for the methods above is cloned under `external/reference_repos/`
(full clones, **gitignored** — this manifest is the tracked source of truth;
re-clone with the commands below). Each clone carries a `PROJECT_README.md`
mapping it to its paper and to the ADR 0008 D-items.

| Local dir | Paper | Upstream |
|---|---|---|
| `ivae/` | iVAE (1907.04809) | github.com/ilkhem/iVAE |
| `sparse_vae/` | Sparse VAE (2110.10804) | github.com/gemoran/sparse-vae-code |
| `mechanism_sparsity/` | Mechanism sparsity (2107.10098) | github.com/slachapelle/disentanglement_via_mechanism_sparsity |
| `utigsp/` | UT-IGSP (1910.09007) | github.com/csquires/utigsp |
| `nonlinear_icp/` | Nonlinear ICP (1706.08576, R) | github.com/christinaheinze/nonlinearICP-and-CondIndTests |
| `robust_nsde/` | Robust neural SDEs (2007.04154) | github.com/msabvid/robust_nsde |
| `dmle_qec/` | Differentiable MLE noise est. (2602.19722) | github.com/cxMoonGlade/DMLE-QEC |

Re-clone all:

```bash
mkdir -p external/reference_repos
git clone https://github.com/ilkhem/iVAE external/reference_repos/ivae
git clone https://github.com/gemoran/sparse-vae-code external/reference_repos/sparse_vae
git clone https://github.com/slachapelle/disentanglement_via_mechanism_sparsity external/reference_repos/mechanism_sparsity
git clone https://github.com/csquires/utigsp external/reference_repos/utigsp
git clone https://github.com/christinaheinze/nonlinearICP-and-CondIndTests external/reference_repos/nonlinear_icp
git clone https://github.com/msabvid/robust_nsde external/reference_repos/robust_nsde
git clone https://github.com/cxMoonGlade/DMLE-QEC external/reference_repos/dmle_qec
```

**QEC noise-learning code.** arXiv:2602.19722 (differentiable MLE noise
estimation) is cloned as `dmle_qec/` (our repo cxMoonGlade/DMLE-QEC) — it is the
closest external prior art to the B-path calibration, but Pauli/DEM-parameterized,
so it serves as the ADR 0008 D4 Pauli-shadowing negative-control reference, not a
coherent twin (see its `PROJECT_README.md`). arXiv:2504.14643 (DEM estimation from
syndrome data) links no public repository as of June 2026; closest public tooling
is Stim (already a dependency) and Sandia pyGSTi (`github.com/sandialabs/pyGSTi`,
the Blume-Kohout/Young characterization lineage) — clone on request.
