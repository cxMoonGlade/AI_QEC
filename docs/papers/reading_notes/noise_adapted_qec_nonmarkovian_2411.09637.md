# Full-text review — Biswas, Utagi & Mandayam, "Noise-adapted Quantum Error Correction for Non-Markovian Noise" (arXiv:2411.09637, Phys. Rev. A 111, 052413, 2025)

> **Provenance (2026-07-03): FULL-TEXT read (精读).** PDF downloaded via `outputs/papers/fetch_and_extract.py` from `arxiv.org/pdf/2411.09637` (0.68 MB, 15 pp) -> text `outputs/papers/2411.09637.txt` (fitz). All section/Eq/Fig refs from that text. Published as Phys. Rev. A 111, 052413 (2025). Tags: **[paper]** = stated in the paper; **[twin]** = our application/inference for `qec_twin`, NOT the paper's claim.

## Metadata [paper]
- **Authors / affiliation.** Debjyoti Biswas, Shrikant Utagi, Prabha Mandayam — Department of Physics and Center for Quantum Information, Communication and Computing (CQuICC), Indian Institute of Technology Madras, Chennai, India.
- **Venue / status.** arXiv:2411.09637v1 [quant-ph], 14 Nov 2024; published Phys. Rev. A 111, 052413 (2025). 15 pp, 6 figures.
- **Type.** **Theoretical proposal** for noise-adapted approximate QEC using the Petz recovery map for non-Markovian (CP-indivisible) noise. Analyzes fidelity bounds for exact/stabilizer QEC and noise-adapted QEC under Hermiticity-preserving trace-preserving (HPTP) noise maps, with a concrete case study of non-Markovian amplitude damping.

## Executive summary [paper]
The paper extends noise-adapted approximate QEC to non-Markovian noise, where the intermediate-time noise map is non-completely-positive (NCP) but the full map is CPTP. Key claims:

1. **Approximate QEC conditions generalize naturally to HPTP (NCP) noise maps** (Theorem 1, Eqs 23-24). The Petz recovery map adapted to the full non-Markovian noise map achieves fidelity bounds structurally identical to the Markovian case, with the same near-optimality guarantee.

2. **Standard stabilizer QEC fails for non-Markovian noise** — the worst-case fidelity can vanish (drop below 0.5) in finite time. For the 5-qubit code with stabilizer recovery on non-Markovian amplitude damping, `F^2_min = 1 - 1.875(gamma^2 - gamma^3) - 0.625 gamma^4` (Eq 32), which reaches ~0.375 at maximum damping.

3. **The non-Markovian Petz map safeguards the code space even at maximum noise** (fidelity > 0.5), by leveraging the information backflow inherent in non-Markovian dynamics. It outperforms both stabilizer-based recovery and the Leung recovery map.

4. **A Markovian Petz map** (adapted to the Kraus operator structure but not to the time-dependent noise parameter) achieves **similar performance** to the non-Markovian Petz map, at the cost of making the composite QEC channel non-unital. This non-unitality causes a small additional fidelity drop but remains above the worst-case limit for most parameters.

5. **The non-Markovianity of the composite QEC superchannel** (R ◦ E) is diagnosed via the eigenvalue spectrum of its matrix representation (Eq 35, Fig 3-4) — the P-divisibility criterion `d lambda_k/dt <= 0` (Eq 40) is violated whenever the fidelity revives.

## Key theoretical framework — HPTP noise and QEC (§§II-III) [paper]

**Non-Markovianity and NCP maps (Eqs 1-5):** The system evolution follows a time-dependent GKSL master equation:
```
d rho/dt = sum_j Gamma_j(t)[L_j(t) rho L^dagger_j - 1/2{L^dagger_j L_j, rho}]
```
When at least one canonical decay rate `Gamma_j(t)` becomes negative, the map is non-Markovian (CP-indivisible). The map from `t_0` to `t_2` is CPTP, but the intermediate map `E(t_2, t_1)` can be NCP (Hermiticity-preserving trace-preserving, HPTP). Such NCP maps admit an **operator sum-difference representation** (Eq 9):
```
E_HPTP[rho] = sum_i sign(i) E_i rho E^dagger_i
```
where some coefficients `sign(i)` may be -1.

**Fidelity bound for exact QEC (Lemma 1, Eqs 10, 19-21):** For a noise channel with correctable errors `{E_k}` and uncorrectable `{F_l}`, the worst-case fidelity is:
```
F^2_min = 1 - min_{|psi>} sum_{k,l} [sign(l)/alpha_kk] (<psi|M^dagger_kl M_kl|psi> - |<psi|M_kl|psi>|^2)
```
where `alpha_kl P = P E^dagger_k E_l P` and `P M_kl P = P E^dagger_k F_l P`. The `sign(l)` term is crucial: when `sign(l) < 0` (information backflow), it **reduces** the infidelity (fidelity revival), while `sign(l) > 0` terms cause damping of revivals. This formalizes the oscillatory behavior seen in the fidelity curves.

## Petz recovery generalization for HPTP maps (§IV) [paper]

**Petz recovery map** (Eq 7): `R_{P,E}[.] = P E^dagger[E[P]^{-1/2} (.) E[P]^{-1/2}] P`

**Non-Markovian Petz channel (RNM):** Exactly adapted to the noise at all times — the recovery operators are time-dependent and the channel is CP-indivisible (Eq 22). The completeness condition includes sign factors: `sum_i sign(i) R^dagger_i R_i = I`.

**Markovian Petz channel (RM):** Adapted only to the **structure** of the Kraus operators, with a **fixed noise strength** chosen to keep the map CP-divisible. The recovery is exactly CP (no sign factors), but the composite `RM o E` channel becomes non-unital.

**AQEC conditions for HPTP noise (Theorem 1, Eqs 23-25):** Define `Delta_ij(t)` such that:
```
P E^dagger_i(t) E[P]^{-1/2} E_j(t) P = beta_ij(t) P + Delta_ij(t)
```
Then for the non-Markovian Petz recovery, the infidelity is:
```
eta(t) = sum_{i,j} sign(i) sign(j) (<psi|Delta^dagger_ij Delta_ij|psi> - |<psi|Delta_ij|psi>|^2)
```
If `Delta_ij = 0` (exact QEC conditions), the Petz map reduces to standard recovery. The near-optimality of Petz recovery **carries over from the CPTP case** because the full map `E(t_2, t_0)` is CPTP; the theorem's proof does not repeat the near-optimality argument.

## The non-Markovian amplitude damping channel (§V, Appendix A) — the concrete mechanism [paper]

**Model (Appendix A, Eqs A1-A5):** Damped Jaynes-Cummings model with Lorentzian spectral density:
```
J(omega) = Gamma_0 b^2 / [2 pi ((omega_0 - Delta - omega)^2 + b^2)]
```
- `Gamma_0`: system-environment coupling strength.
- `b`: spectral bandwidth.
- Non-Markovian regime: `b << 2 Gamma_0`. Markovian: `b >> 2 Gamma_0`.

**Kraus operators (Eq 29):** Standard AD form with time-dependent damping parameter `gamma(t) = 1 - |G(t)|^2`:
```
E_1(t) = diag(1, sqrt(1-gamma(t))),  E_2(t) = [[0, sqrt(gamma(t))], [0, 0]]
```
where `G(t)` satisfies an integro-differential equation (Eq A7-A8). The decay rate `Gamma(t) = -2 d/dt ln G(t)` becomes **negative** during non-Markovian evolution.

**Codes studied:**
- **[[5,1,3]] stabilizer code** (Eq 31) with syndrome-based recovery `R_S`.
- **4-qubit noise-adapted code** (Eq 33): `|0_L> = (|0000> + |1111>)/sqrt(2)`, `|1_L> = (|0011> + |1100>)/sqrt(2)` — designed to correct amplitude damping errors.

## Fidelity results (§V, Figs 1-2) [paper]

**[[5,1,3]] + stabilizer recovery (Fig 1):** Worst-case fidelity oscillates and drops below 0.5 at maximum damping. At `gamma = 1`: `F^2_min ~ 0.375`.

**4-qubit + Petz recovery (Fig 1):** Both Markovian and non-Markovian Petz recoveries outperform the 5-qubit stabilizer code. Non-Markovian Petz fidelity remains **above 0.5 at all times** (even at maximum noise). Analytic fits (Eq 34):
- Markovian Petz: `F^2_min = 1 - 1.658 gamma^2 + 1.069 gamma^3 - 1.517 gamma^4 + 2.563 gamma^5 - 0.955 gamma^6`
- Non-Markovian Petz: `F^2_min = 1 - 1.715 gamma^2 + 0.362 gamma^3 + 2.35 gamma^4 - 1.93 gamma^5 + 0.428 gamma^6`

**4-qubit + Petz vs Leung recovery (Fig 2):** Leung recovery (both Markovian and non-Markovian adaptations) fails at large damping — fidelity goes to zero. The Petz map uniquely preserves the code space. The Petz advantage comes from the **transpose-channel structure** which adapts to the full noise process rather than relying on polar decomposition and syndrome extraction.

## Non-unitality and its consequences (§V.A) [paper]

When the Petz recovery is inexactly adapted (Markovian Petz for non-Markovian noise), the composite `RM o E` channel is no longer unital (`Phi[P] != P`). This adds an extra term to the fidelity (Eq 39):
```
F^2 = (1/d)(r^T . T . r + tau . r)      (non-unital)
vs   F^2 = (1/d)(r^T . T . r)           (unital)
```
The `tau.r` term (from the `vec{tau}` in Eq 38) causes the worst-case fidelity to drop below what the unital case would achieve. This explains the brief dips below 0.5 for the Markovian Petz in Fig 1.

## Non-Markovianity of the QEC superchannel (§V.B, Figs 3-4) [paper]

The composite `R o E` map's non-Markovianity is diagnosed via eigenvalue analysis of its matrix representation (Eq 35):
```
M_ij = Tr[O_i Phi[O_j]]
```
where `{O_i}` is a Hilbert-Schmidt basis. The P-divisibility condition (Eq 40):
```
d lambda_k(t) / dt <= 0  for all k, t
```
is **violated** whenever the fidelity shows revivals. For the 4-qubit code with Petz recovery, **all eigenvalues** are non-constant and contribute to violation (Fig 3). For the [[5,1,3]] code with stabilizer recovery, only **one eigenvalue** is non-constant (Fig 4).

## Limitations [paper]
- **L1. Single noise model (amplitude damping).** The detailed numerics and analysis focus entirely on the non-Markovian amplitude damping channel (damped Jaynes-Cummings model). Generalizability to other non-Markovian noise types (dephasing, correlated noise, leakage) is asserted but not demonstrated.
- **L2. Small codes only.** The numerical results use the 4-qubit code and [[5,1,3]] code. Scaling behavior with code distance is not explored. The claim that Petz recovery "safeguards the code space" is for these small codes only.
- **L3. No circuit-level implementation.** The Petz recovery map is defined abstractly via Kraus operators. The paper acknowledges that "writing down a quantum circuit for CP-indivisible channel remains an open problem" (§VI). The Markovian Petz approximation addresses this partially, but no explicit circuit construction is given.
- **L4. Perfect syndrome extraction assumed.** The framework assumes the codespace projector P is applied exactly (Petz recovery on the noise-affected code space). There is no analysis of faulty syndrome extraction or measurement errors — the standard circuit-level noise model is absent.
- **L5. HPTP maps only.** The work considers only CP-indivisible maps (the intermediate map is HPTP). Broader classes of non-Markovian noise (e.g., P-indivisible, non-invertible maps, or process-tensor non-Markovianity) are not covered. The authors acknowledge (§II.C) that "the two-time map approach [may be] insufficient in describing non-Markovian stochastic processes in full generality."
- **L6. No comparison to randomized benchmarking or GST.** The fidelity metric is the worst-case fidelity (Eq 8), which is not directly connected to experimentally measurable quantities like RB decay rates or logical error rates from decoding.

## Relevance to the twin — noise-adapted recovery + non-Markovian treatment concepts [twin]

1. **The Petz map framework provides the formal QEC-theoretic foundation for noise-adapted recovery** — "if you know the noise channel, adapt the recovery to it." This is the theoretical underpinning for our twin's decoder: our decoder is implicitly a noise-adapted decoder (using the DEM derived from the teacher's noise model). The paper shows that this adaptation principle extends to non-Markovian noise, and that the Petz map is **near-optimal** for HPTP noise maps.

2. **⚠ The failure of stabilizer QEC under non-Markovian noise is a potential threat to our twin's "frozen MWPM decoder" approach.** Our WS2 framework uses a fixed (marginalized-independent) DEM to decode data from the correlated teacher. If the teacher generates genuinely non-Markovian noise (e.g., 1/f noise, temporally correlated errors), the frozen MWPM decoder may suffer exactly the fidelity collapse described here (Eq 32, Fig 1). The Petz recovery result suggests that a decoder adapted to the full non-Markovian structure could recover, but our frozen DEM does not adapt.

3. **The non-Markovian amplitude damping model (Lorentzian spectrum, Jaynes-Cummings) is a potential teacher component** for the coupling simulator's T1 axis. The `gamma(t) = 1 - |G(t)|^2` parametrization with the Lorentzian spectral density provides a closed-form, exactly solvable non-Markovian T1 channel. The b << 2 Gamma_0 regime gives strong non-Markovianity (oscillatory gamma(t) with negative intervals). This is a concrete candidate for the "non-Markovian amplitude damping" mechanism in our teacher catalog.

4. **The operator sum-difference representation (Eq 9) is relevant for representing non-CP intermediate maps** that appear in our gauge/identifiability analysis. If the twin's dynamical map has intermediate-time NCP segments (e.g., from strong-coupling effects), the decomposition `E = CP1 - CP2` with `sign(i) = +/-1` provides a linear representation even when the map is not completely positive. This is potentially useful for expressing the twin's noise channel in a form that admits linear inversion, even under non-Markovian dynamics.

5. **The non-unitality analysis (Eqs 35-39) has a direct connection to our decoder's fixed-point analysis.** The `tau` vector in Eq 38 (which is zero when the channel is unital onto the codespace) determines whether the worst-case fidelity has an extra penalty. For our MWPM decoder, the composite `R o E` channel may not be unital either — the analysis of whether this causes detectable fidelity degradation is relevant to our decoder benchmarking.

6. **The P-divisibility eigenvalue test (Eq 40) is a formal diagnostic for non-Markovianity** that could be applied to our carrier's time-dependent noise model. If we can compute the matrix M for the composite channel, the sign of `d lambda_k/dt` flags non-Markovianity. This is mathematically clean but may be impractical for the d=3 surface-code twin (the state space is already large).

7. **Contrast with Kam's temporal correlation work (2410.23779):** Biswas et al. approach non-Markovianity from the channel-fidelity perspective (how to recover the code state), while Kam approaches it from the decoder-misspecification perspective (how temporal correlations affect LER under a frozen decoder). The two are complementary: Kam tests whether a fixed stabilizer decoder survives temporal correlations (it doesn't for streaky class 1/2); Biswas tests whether an adapted (Petz) recovery can handle non-Markovianity (it can, even at maximum noise). For the twin, our decoder is closer to Kam's frozen decoder — we should expect Biswas's conclusions (adapted recovery helps) to be a motivation for future noise-adaptive decoding, not a description of our current decoder.

8. **The Markovian Petz compromise (structure-adapted only, not strength-adapted) is conceptually similar to our fixed-marginal construction.** Both preserve the operator structure of the noise but use a fixed (not time-dependent) parameter. The price in both cases is a non-unital composite channel / biased decoder, which costs some fidelity. This parallel strengthens the conceptual bridge between the two frameworks.

## How to use / trust + open questions [twin]
- **Trust:** high for the algebraic results (Lemma 1, Theorem 1 — the fidelity bound derivations are self-contained and standard). Medium for the numerical claims: the fidelity fits (Eqs 32, 34) are obtained from curve-fitting to numerical data, and the parameter choices (b=0.01, Gamma_0=5 for non-Markovian; b=0.1, Gamma_0=0.005 for Markovian Petz) are specific to the model. The comparison between Petz and Leung recovery (Fig 2) is qualitatively robust.
- **The paper addresses a fundamentally different question from ours** — "can we fix non-Markovian errors with an adapted recovery" vs "how do non-Markovian/correlated errors affect the twin's fixed-decoder performance." The Petz recovery result is an existence proof that non-Markovian noise is correctable in principle, not that it is easy to correct with practical decoders.
- **Open for our coupling simulator:** (i) The non-Markovian AD channel (Appendix A) is a drop-in candidate for the T1 component of the non-Pauli/non-Markovian axis of the teacher catalog — should we implement it? (ii) The operator sum-difference representation could help formalize the carrier's time-dependent CPTP map when the Lindblad rates become temporarily negative. (iii) The eigenvalue-based non-Markovianity diagnostic (Eq 40) could be applied to our carrier's channel as a validation check.
- **Key distinction to carry:** the paper's "non-Markovian" means CP-indivisible (intermediate-time NCP maps from strong system-bath coupling), while our twin's "non-Markovian" usage often refers to temporally correlated classical noise (e.g., 1/f, streaky Pauli errors). These are physically different regimes — the former is a quantum open-systems effect, the latter is a classical stochastic process with memory. The Petz recovery result applies to the former; whether it also helps with the latter depends on whether the full noise map is still CPTP (which it is for temporally correlated Pauli errors).
