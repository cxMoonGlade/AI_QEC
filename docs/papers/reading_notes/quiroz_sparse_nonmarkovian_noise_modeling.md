# Full-text review — Oda, Schultz, Norris, Shehab & Quiroz, "Sparse Non-Markovian Noise Modeling of Transmon-Based Multi-Qubit Operations" (arXiv:2412.16092, PRX Quantum 7, 020327 2026)

> **Provenance (2026-07-03): FULL-TEXT read (精读).** PDF downloaded from `arxiv.org/pdf/2412.16092`
> (`outputs/papers/2412.16092.pdf`, 4.06 MB, 31 pp) → text `outputs/papers/2412.16092.txt` (fitz).
> All §/Eq/Table/Fig refs from that text; figures not pixel-extracted — figure facts below are from
> captions and numbers stated in the running text. Tags: **[paper]** = stated in the paper;
> **[ours]** = application/inference for `qec_twin`, NOT the paper's claim.

## Metadata [paper]

- **Authors.** Yasuo Oda, Kevin Schultz, Leigh Norris, Omar Shehab, Gregory Quiroz (Johns Hopkins
  University / JHU APL / IBM Quantum).
- **Venue.** PRX Quantum 7, 020327 (published 12 May 2026); arXiv:2412.16092v1 [quant-ph],
  20 Dec 2024.
- **Type.** Hybrid noise **characterization + forward simulation** framework for transmon-based
  superconducting qubits. Builds an effective noise model from real hardware calibrations (7 IBM
  Quantum devices, 39 qubits) and validates it against RB, multi-qubit DD, and VQE experiments.

## Executive summary [paper]

The paper presents a sparse-parameter noise model for transmon qubits that combines three
formalisms: (i) a **Lindblad master equation (LME)** for Markovian and extended-Markovian
(small extended Hilbert space) dynamics; (ii) a **stochastic Hamiltonian** for temporally correlated
Gaussian dephasing and control noise; and (iii) a **quantum channel** reduction for scalability.
The model is parameterized by 10 parameters per qubit + 3 per qubit pair, learned from 7
characterization experiments (T1, T2/Ramsey, FTTPS, FPW, SPAM, crosstalk, CR gate).

Key findings:
- **64% of qubits are purely Markovian**; 26% show correlated dephasing; 10% show correlated
  control noise; ~5% show both (Table II).
- **Correlated dephasing is dominated by DC/quasistatic noise** (ω_max < δω_min), limiting FTTPS
  QNS resolution; well-characterized by a Lorentzian PSD S_L(ω) = S_0/(1+(ω/ω_max)^α).
- **CR/ECR gates are well described by single-qubit dissipative parameters** plus 3 coherent
  Hamiltonian corrections (ϵ_zx, ζ, J) — no two-qubit dissipative terms needed.
- **VQE H2 prediction achieves 0.5% relative error** (7x improvement over IBM default model).
- **Model reduction to composite channels** (Eqs 28-32) reformulates the LME noise processes as
  error maps (GAD, dephasing, control noise, ZZ crosstalk, TLS coupling) for scalable simulation.

## Method (deep) [paper]

### Noise model structure (§II, Eq 1-10)

The LME (Eq 1) acts on H = H_D ⊗ H_Sp ⊗ H_TLS (data, spectator qubits, two-level systems).
The Hamiltonian (Eq 2) has four components:
- H_C(t): control (single-qubit x-rotations + virtual Z; ECR two-qubit ZX_π/2, Eq 4)
- H_N(t): stochastic noise — local Gaussian dephasing β_j(t) + control amplitude noise ϵ_j(t)
  (Eq 10). Both are Gaussian, wide-sense stationary, specified by mean and PSD S(ω).
- H_XT: ZZ crosstalk to spectator qubits (Eq 7): H_XT = Σ_j σ_z^(j) Σ_{i∈C(j)} J_ij σ_z^(i)
- H_TLS: ZZ coupling to two-level systems (Eq 8): H_TLS = Σ_j σ_z^(j) Σ_k ξ_jk σ_z,TLS^(j,k)

Dissipative terms (L_k, γ_k) cover **generalized amplitude damping** (GAD, with T1, q),
**phase damping** (PD, with T_ϕ), and **control noise** (bit-flip, rate ν during x-rotations only).

### Three noise tiers (local-Markovian / extended-Markovian / stochastic) [paper]

- **Locally Markovian:** uncorrelated per-qubit GAD + PD + control dissipation, described entirely
  within the LME (no extended Hilbert space).
- **Extended Markovian:** processes requiring enlarged Hilbert space but still LME-tractable:
  spectator qubit ZZ crosstalk (H_XT) and TLS ZZ coupling (H_TLS). The TLS is treated as an
  effective qubit in |+⟩, coupling via ZZ.
- **Stochastic (non-Markovian):** time-correlated Gaussian dephasing β_j(t) and control ϵ_j(t)
  noise. Captured by the noise PSDs S_β(ω), S_ϵ(ω) via the Filter Function Formalism (FFF).
  Three regimes by ω_max vs δω_min (qubit coherence-limited frequency resolution):

### Characterization protocol (§III, Table I, Fig 1)

Seven experiment classes C = {M, T1, T2, P, Q, XT, CR}:

| Parameter | Experiment | Expression |
|---|---|---|
| γ, q (T1, equilibrium) | T1 | v_T1(τ) ≈ 1 − 2q(1−e^{−γτ}) (Eq 13) |
| λ (dephasing) | T2 Hahn echo | v_T2(τ) ≈ e^{−τ(γ/2+λ)} (Eq 14) |
| β (detuning), ξ (TLS) | Ramsey (R) | v_R(τ) = e^{−(γ/2+λ)τ} cos(β_eff τ) cos(ξτ) (Eq 15) |
| s (SPAM) | M | p_M(δt) ≈ s |
| ϵ (coherent), S_β, S_ϵ | FTTPS (Q) | v_k^Q(τ) ≈ e^{−τδ_k} cos(2πkϵ) (Eq 16) |
| ν (incoherent control) | FPW (P) | v_P(τ) ≈ e^{−τ(3γ/4+λ/2+ν)} cos(4β_eff τ/3π) (Eq 17) |
| J (crosstalk) | XT | v_XT(τ) ≈ e^{−ατ}(cos(Jτ) + (γ_S/2J) sin(Jτ)) (Eq 18) |
| ϵ_zx, ζ (CR) | CR | ⟨Y_t⟩, ⟨Z_t⟩ per Eq 19 |

Model fitting: Markovian parameters first via MSE minimization (δ < 1%). If RB fails validation,
add stochastic dephasing/control PSD via FTTPS → QNS.

### Non-Markovian characterization (§IV.C): correlated dephasing

- **FTTPS protocol** (Fig 5a): K sequences with N=2(K+1) X gates spaced at τ_k ≈ τ/2^k.
  The survival probability conveys PSD information via filter-function overlap integral.
- **PSD model:** Lorentzian S_L(ω) = S_0 / (1 + (ω/ω_max)^α) (Eq 20). Qubit 0 of ibmq_belem:
  α=2 (colored). Qubit 2: α=0 (white/Markovian).
- **DC regime:** ω_max < δω_min → quasistatic, modeled by a δ-peak PSD. Detected by comparing
  Ramsey vs HE decay rates (Fig 5e-f).
- **Correlated control noise (Fig 6):** detected via FTTPS vs R-FTTPS (with alternating X sign
  to cancel low-frequency control noise). Coherent control noise → quadratic k-decay.
  Stochastic control noise → exponential k-decay.

### Model scalability (§VI.B): composite channel reduction

The LME is reduced to a composition of quantum channels (Eqs 26-32):
- E_GAD: generalized amplitude damping (4 Kraus ops, Eq 28)
- E_D: dephasing channel — U_β(τ) E_β(ρ) U_β†(τ), where E_β(ρ) = (1−p_β)ρ + p_β σ_z ρ σ_z
  and p_β = (1+e^{−χ_β(τ)})/2 with χ_β = ∫ S_β(ω)F_β(ω,τ)dω / π (Eqs 29-30)
- E_CN: control noise — U_ϵ(τ) E_ϵ(ρ) U_ϵ†(τ) with analogous structure (Eq 31)
- E_ZZ: ZZ crosstalk + TLS — unitary from H_XT + H_TLS (Eq 32)
- E_M: measurement error (Eq 5)

## The OBSERVABLE / metric [paper]

- **Survival probability** p(τ) = ⟨0|E_M(ρ(τ))|0⟩ = (1 + (1−2s)v_z(τ))/2 — the primary
  experimental observable.
- **RB error-per-Clifford (EPC)** from exponential fit p_RB(L) = (1 + (1−2s)e^{−rL})/2.
- **Relative energy error** Δ(R) = |E_sim(R) − E_exp(R)|/|E_exp(R)| × 100% (Eq 25) for VQE.
- **Fitting quality:** MSE distance D(x⃗,y⃗) = (1/N)√Σ(x_i−y_i)², with δ-optimal threshold <1%.

## Findings + numbers [paper]

- **39 qubits, 7 devices** (Falcon r5.11T, Eagle r1): 64% pure Markovian, 26% correlated dephasing,
  10% correlated control, ~5% both (Table II). Correlated dephasing stable over time.
- **Qubit 4, ibm_hanoi** (Fig 5a): FTTPS with N=128, τ≈9μs, δω≈0.7MHz, ω_max ≳ δω_min regime.
  PSD reconstructed via ARMA model.
- **Qubit 0, ibmq_belem** (Fig 5b,d): α=2 (colored), CPMG improved with d=8 pulses.
- **Qubit 2, ibmq_belem** (Fig 5b,d): α=0 (white), no CPMG improvement beyond d=2.
- **Qubit 7, ibm_algiers** (Fig 5e): DC regime — single echo pulse recovers coherence.
- **Qubit 3, ibmq_lima** (Fig 6b,c): coherent control error (quadratic k-decay in FTTPS).
- **Qubit 2, ibmq_lima**: stochastic control error (exponential k-decay, reproduced by 1/f PSD).
- **ECR gate** (qubits 0-1, ibm_lagos, Fig 7): ϵ_zx ≈ 0.14, ζ ≈ 0.01 MHz, τ_CR = 0.576μs.
  LME with single-qubit noise captures decay up to n=16 repetitions. Only fails when J ≈ 0.5 MHz.
- **VQE H2** (qubits 12,15 of ibm_algiers, Fig 9): at optimal bond length R_opt = 0.75 Angstrom,
  Δ(R_opt) = 0.5% (Oda et al.) vs 3.6% (IBM default) → 7× improvement. With non-Markovian
  correlations removed: Δ≈3.8%.
- **Multi-qubit DD** (qubit 1 + spectators 0,2,4, ibm_cairo, Fig 8): XY4 on main qubit, 1176
  repetitions, T=83.5μs. LME captures state-dependent oscillatory dynamics (due to TLS + ZZ
  crosstalk).

## Assessment table [paper]

| Criterion | Assessment |
|---|---|
| Non-Markovian/temporal correlations | YES — central; Gaussian dephasing PSD S_β(ω) (Lorentzian/DC), control PSD S_ϵ(ω) |
| Simulator or characterization | BOTH — characterization framework (learning params) + forward simulator (LME/channel) |
| "Blind spot"/"gauge"/"invisible" | Not directly; model detects non-Markovianity via RB model violation, then QNS |
| Detector/syndrome records | No — uses standard QCVV circuits (T1, T2, Ramsey, FTTPS, FPW, RB), not QEC |
| Closed-form analytic expressions | YES — Eqs 13-19, A3, A21: LME solutions for all characterization circuits |
| Noise model | Gaussian continuous PSD (dephasing, control) + LME (GAD, PD, bit-flip) + ext. Hilbert (TLS ZZ, crosstalk ZZ) |
| Connection to coupling simulator | YES — continuous Gaussian Σ (S_β(ω), S_ϵ(ω) PSDs); FFF overlap integral framework; "DC+white" model relevant to Σ decomposition |
| PSD structure | Lorentzian S_L(ω) = S_0/(1+(ω/ω_max)^α) or DC+white; α=2 (colored) or α=0 (white) |
| Scalability | 10 params/qubit + 3/edge; composition-of-channels reduction for >few qubits |

## Limitations [paper]

- **L1. Restricted to fixed-frequency transmons** with CR gates. The model and characterization
  are specifically for IBMQP architecture, though the formalism is general.
- **L2. No two-qubit dissipative terms** — only single-qubit incoherent errors suffice for the
  ECR gate. This may break for other architectures or stronger coupling regimes.
- **L3. Characterization per-qubit, not per-cycle.** Model is fitted to isolated qubits/pairs;
  cross-device transferability not tested beyond 7 devices.
- **L4. DC-dominated correlated noise regime** limits QNS resolution for most qubits (ω_max < δω_min);
  PSD characterization relies on parametric assumption of Lorentzian form.
- **L5. LME/channel reduction is additive** — simultaneous noise processes are combined linearly;
  correlations between noise sources (e.g., dephasing × crosstalk) are not modeled.
- **L6. RB validation is the only non-Markovian detector** — relies on RB model violation rather
  than a direct multi-time correlation witness (c.f. Srivastava 2510.13051).

## Relevance to AI_QEC [ours]

1. **The noise model structure maps directly onto our coupling simulator's PSD-based noise.**
   The paper uses continuous Gaussian dephasing PSD S_β(ω) and control PSD S_ϵ(ω) — exactly the
   class of processes our coupling simulator handles (continuous Gaussian Σ in the Hamiltonian,
   Eq 10). The FFF overlap integral χ(τ) = ∫ S(ω)F(ω,τ)dω (their Eq 30 / Appendix B) is the
   same structure as our PSD-based noise injection for the carrier. The "DC+white" PSD
   simplification (Γ δ(ω) + S^{(u)}) is directly relevant to our quasistatic limit for dephasing.

2. **The "reduced channel" approach (Sec VI.B) is the complementary end of our composed carrier.**
   Their E_GAD, E_D, E_CN, E_ZZ channels (Eqs 28-32) are Kraus-operator reductions of the LME
   noise — essentially what our C1 composed carrier does (factorizing the noisy process into
   channel compositions). The difference: they reduce *from* a known fitted LME model, while
   our carrier builds *toward* an interpretable composed channel. Their E_D channel with
   χ(τ) = Γ F(0,τ)/π + S^{(u)} τ (DC+white dephasing) is a well-motivated simplification.

3. **Their 10-parameter qubit model is too heavy for our carrier** (we aim for sparser,
   mechanism-resolved parameters). But the *topology* of parameters (γ, q, λ for dissipation;
   β for detuning; ϵ, S_ϵ for control; S_β for dephasing; J for crosstalk; ξ for TLS) provides
   a completeness checklist for our model design — every mechanism they need to explain hardware
   data ought to have an analogue in our coupling simulator's parameter space.

4. **Key mechanism fact:** 64% Markovian across IBMQP devices suggests the TWIN's Pauli-approximate
   label-free learner may be *sufficient* for a majority of qubits, but the 26% with correlated
   dephasing and 10% with correlated control noise define the non-Markovian frontier. The
   correlated dephasing is **predominantly DC/quasistatic** — which our PSD-based teacher can
   produce with a low-frequency cutoff.

5. **The ECR gate finding** — no two-qubit dissipative terms needed — is consistent with our
   Axis-1 joint Lindbladian design (where two-qubit coherent Hamiltonian terms dominate, with
   single-qubit dissipative channels). It also validates our design choice to focus on Hamiltonian
   couplings for two-qubit mechanisms.

6. **What is NOT covered** that we need: (a) QEC detector/syndrome records (they use standard QCVV
   only); (b) non-Gaussian or discrete noise processes (pure Pauli, HMM states); (c) cross-talk
   mitigation via the composition ordering in a full QEC cycle; (d) drift/adaptive re-estimation
   (characterization once, not continuously updated). Their model is a static fit; our twin needs
   temporal tracking.

7. **What's complementary to Srivastava (2510.13051):** Quiroz detects non-Markovianity via RB
   *model violation* (deviations between predicted and measured ASF). Srivastava shows such
   violations can be *absent* for certain Hamiltonians (ZZ coupling → RB-blind). Together they
   bracket the detection problem: Quiroz shows the *detection path* when it works; Srivastava
   shows the *failure mode* Quiroz's approach would miss.

## How to use / trust + open questions [ours]

- **Trust:** high — PRX Quantum published, 31 pages, full experimental data from real IBM devices,
  analytic LME expressions validated against numerical simulation. Read full text.
- **Direct reuse:** the GAD/PD/dephasing-channel parameterization (Eqs 28-31) with their FFF-based
  χ(τ) integral; the DC+white PSD simplification for quasistatic dephasing; the Lorentzian PSD
  model S_L(ω) = S_0/(1+(ω/ω_max)^α) as a test case for our noise-PSD injection.
- **Do not take as given:** the claim "no two-qubit dissipative terms needed" is specific to
  IBMQP CR gates; our coupling simulator targets different hardware (Google XZZX) and must
  not assume this holds. The 64/26/10% Markovian/correlated split is IBM-specific, not universal.
- **Open question:** would the model's performance degrade under the "RB-blind" Hamiltonians
  identified by Srivastava 2510.13051 (e.g., ZZ coupling where temporal correlations are
  invisible to RB)? Quiroz's RB-based non-Markovianity detection could be blind to those —
  this is an undetected failure mode for their model selection criterion.
