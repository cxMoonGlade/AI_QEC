## Provenance

- **Source:** arXiv:2512.09189, fetched 2026-07-03
- **Reading method:** FULL-TEXT read (精读) via arXiv HTML — all sections, equations, appendices, and figures
- **Status:** complete full-text close-read

# Deep review — Garner et al., Exact and Efficient Stabilizer Simulation of Thermal-Relaxation Noise for Quantum Error Correction

> Deep reading note (academic-paper-review format; full read Secs. I–V incl. the
> combined QPD decomposition Eqs. 36–37, the positivity condition T2 <= T1, the
> reset-based approximation Eq. 38, finite-temperature extension Eqs. 43–45, and
> the surface code / BB code numerical experiments Figs. 6–9). **Relevance to the
> twin** centerpiece.

## Metadata
- **Authors.** Sean R. Garner, Nathan M. Myers, Meng Wang, Samuel Stein, Chenxu Liu, Ang Li (Pacific Northwest National Laboratory; University of Washington; University of British Columbia).
- **Venue / status.** arXiv:2512.09189, Dec 2025.
- **Domain / type.** QEC noise simulation; **theoretical + numerical** (stabilizer simulation with Clifford+reset decomposition, GPU-accelerated STABSim).

## Executive summary
The paper develops a **stabilizer-compatible simulation method for thermal relaxation noise** (amplitude damping + dephasing) that avoids the Pauli-twirling approximation (PTA). The key technical result: the **combined amplitude-damping + dephasing channel admits a fully positive Clifford+reset decomposition** whenever T2 <= T1 — the experimentally relevant regime for superconducting and semiconductor qubits. When T2 > T1, the quasi-probabilistic decomposition acquires negativity but with **lower sampling overhead** than treating the channels independently. They introduce an **approximated reset channel** that removes the negativity while achieving higher channel fidelity to the true thermal relaxation than PTA. The method extends to finite temperature. Numerically, they apply the model to **rotated surface codes (d=3,5,7,11) and bivariate bicycle (BB) codes** on superconducting platforms, finding that PTA can misestimate LER by 2--10x in either direction depending on code state and distance, and that **differing logical performances across code states** imply noise-model-informed decoders will be essential.

## Contributions (claim → evidence → strength)

- **C1. Combined QPD of thermal relaxation is fully positive when T2 <= T1 (Sec. II.4, Eqs. 36--37).** *Evidence:* Decomposition `E_th,0 = q_+ I + q_- Z + p_gamma R_{|0>}` with coefficients `q_+/- = [e^{-tau/T1} +/- e^{-tau/T2}]/2`; when T2 <= T1, `q_- >= 0` so the distribution is strictly positive — no QPD sampling overhead (Gamma = 1, Fig. 3). *Strength: strong — the central exact result, analytically derived.*

- **C2. Reset-based approximation outperforms PTA when T2 > T1 (Sec. II.4.1, Eq. 38; Figs. 4--5).** *Evidence:* The approximated channel `E_reset = q_+ I + (1-q_+) R_{|0>}` removes the negative component while retaining directional bias; channel fidelity difference `Delta F = F_reset - F_PTA > 0` consistently for T2/T1 up to at least 2 (Figs. 4, 5). *Strength: strong; fidelity advantage grows with increasing tau/T1.*

- **C3. Finite-temperature extension preserves the same sampling cost (Sec. II.4.2, Eqs. 40--45).** *Evidence:* Generalized amplitude damping + dephasing decomposes with the same negativity condition; temperature only adds `p_1 p_gamma R_{|1>}` and does not alter the sampling overhead. *Strength: strong (straightforward extension, same structure).*

- **C4. PTA misestimates LER by 2--10x, direction depends on code state (Sec. III.2, Fig. 6).** *Evidence:* Surface code LER for |0>_L: PTA underestimates; for |+>_L: PTA overestimates (Fig. 6a–b). BB codes show ~1.5--2x lower LER with exact model vs PTA (Fig. 8). *Strength: moderate-strong (specific to MWPM decoder, limited distance range, no statistical error bars on the factor range).*

- **C5. Thermal relaxation LER is decoder-state-dependent (Sec. III.2, Figs. 6--7).** *Evidence:* |0>_L vs |+>_L differ notably; |0>_L vs |1>_L are nearly identical (Fig. 9), confirming the difference is decoder-driven (MWPM response to noise bias) rather than state population asymmetry. *Strength: moderate (observation, not exhaustively explored; single decoder).*

## Method (deep)

- **Thermal relaxation model (Sec. II.1).** Master equation `d_t rho = gamma(<n_b>+1) D[|0><1|](rho) + gamma <n_b> D[|1><0|](rho) + (gamma_phi/2) D[sigma_z](rho)` with dissipator `D[A](rho) = -1/2(A^+ A rho + rho A^+ A - 2 A rho A^+)`. Zero-temperature: `E_pd ∘ E_ad` with amplitude damping Kraus `E_ad,0 = diag(1, sqrt(1-p_gamma))`, `E_ad,1 = sqrt(p_gamma) |0><1|`, and dephasing `E_pd(rho) = (1-p_phi) rho + p_phi Z rho Z`. Key parameters: `p_gamma(tau) = 1 - e^{-tau/T1}`, `p_phi = 1/2 [1 - e^{-tau(1/T2 - 1/(2T1))}]`.

- **PTA (Sec. II.2).** Pauli twirl yields a stochastic Pauli channel with `p_x = p_y = p_gamma/4`, `p_z = 1/2 - p_gamma/4 - (1-2p_phi) sqrt(1-p_gamma)/2`. Fails to capture directional Z-axis relaxation (Fig. 1).

- **QPD (Sec. II.3).** Quasi-probabilistic decomposition following Bennink (2017): any channel decomposable into Clifford + reset with signed weights; negativity implies `Gamma = sum_x |q(x)| > 1` sampling overhead. Independent-channel QPD multiplies overhead exponentially.

- **Combined QPD (Sec. II.4).** The key trick: composing dephasing *after* amplitude damping produces the simple form `E_th,0 = q_+ I + q_- Z + p_gamma R_{|0>}`. When T2 <= T1, `q_- >= 0` so the distribution is positive. Intuition: dephasing "blurs" the coherent part of amplitude damping just enough to make the remaining Z-coefficient non-negative.

- **Reset approximation (Sec. II.4.1).** `E_reset = q_+ I + (1-q_+) R_{|0>}` discards the negative `q_- Z` term, renormalizing the reset probability. Captures the directional relaxation bias that PTA structurally misses.

- **Finite temperature (Sec. II.4.2).** Generalized AD Kraus set (4 operators). Conjugation by Pauli-X maps between zero/finite temperature (Eq. 40). Thermal equilibrium population `p_1 = <n_b>/(1+2<n_b>) = 1/(1+e^{hbar omega_0 / k_b T_b})`.

- **Simulator (Sec. III.1).** STABSim: CHP-derived stabilizer/destabilizer tableau with MPI+GPU parallelization. Key limitation of Stim: Pauli frame tracking "cannot admit probabilistic reset operations," limiting it to PTA only. STABSim injects thermal relaxation errors as probabilistic Clifford+reset gates during idles/before measurement.

## Results (deep)

- **Channel fidelity (Figs. 4--5).** Reset approximation consistently beats PTA on channel fidelity to the true thermal relaxation. Advantage grows with `tau/T1`; at `tau/T1 ~ 1`, `Delta F ~ 0.02` (T2/T1=1.5, Fig. 4). Finite temperature reduces but does not eliminate the gap (Fig. 5; T2/T1=1.5, p1 <= 0.1).

- **Surface code LER (Fig. 6, d=3,5,7,11).** MWPM decoder. |0>_L: PTA *underestimates* LER (exact thermal relaxation gives higher error). |+>_L: PTA *overestimates* LER (exact gives lower error). The offset is non-constant with distance. Scaling exponent (log-log slope) differs across models.

- **Excited-state population (Fig. 7).** |0>_L and |+>_L populations differ only slightly — the LER difference is MWPM's response to noise *bias* (Z-dominated for |0>_L, X/Z mixed for |+>_L), not asymmetric relaxation dynamics.

- **BB codes (Fig. 8).** Exact model consistently ~1.5--2x lower LER than PTA. Error dispersion across many qubits averages to a nearly constant offset. BP-OSD decoding (1000 BP, 10 OSD iterations).

## Methodology assessment

| Criterion | 1–5 | Assessment |
|---|---|---|
| Soundness | **5** | QPD decomposition derived analytically from composited Kraus operators; positivity condition proven; channel fidelity comparisons well-defined. |
| Novelty | **4** | The combined decomposition and positivity condition (T2 <= T1) is the clean technical result; reset approximation is a natural heuristic after the exact result. Overlaps with existing QPD literature (Bennink, Rall, Hakkaku). |
| Reproducibility | **3** | Methods and algorithms described; but STABSim is not publicly available, no code link, and the ~1.5--2x BB offset and 2--10x surface factor ranges have insufficient shot count / error bar reporting to pin precisely. |
| Experimental design | **4** | Surface + BB codes, two logical states, multiple distances — good coverage. MWPM and BP-OSD decoders are standard. Missing: statistical error analysis on the LER ratio claims, comparison of more than one decoding strategy for the state-dependence finding. |
| Statistical rigor | **2** | LER curves are shown without error bars; the claim "2--10x misestimation" is a qualitative range; shot counts for the high-distance results are not specified. The comparison is visually convincing but not statistically rigorous. |
| Scalability | **4** | Clifford+reset decomposition is stabilizer-native, so exact, positive, and O(n^2) per shot when T2 <= T1. STABSim GPU+MPI targets large codes. BB codes up to moderate size. The main limit: the positive decomposition only covers this one combined channel. |

## Strengths

- **S1 — the positivity condition T2 <= T1 (Sec. II.4.1, Eq. 37).** A clean, analytically proven result: when the environment dephases the qubit faster than or as fast as it relaxes (the universal experimental regime for superconducting qubits on the timescale of an idling/measurement step), the combined channel costs *no* QPD overhead — exact, positive, stabilizer-compatible. This is practically useful and theoretically satisfying.

- **S2 — physical interpretation of the reset approximation vs PTA (Sec. II.4.1, Fig. 4).** The paper explicitly states why the reset model outperforms PTA: it captures the "directional bias of the thermal relaxation error channel" — the asymmetry between |0> and |1> that PTA structurally discards. The channel fidelity comparison (Fig. 4) cleanly demonstrates this advantage across the parameter range.

- **S3 — state-dependent LER finding (Sec. III.2, Fig. 6).** Demonstrating that PTA's misestimation *direction* depends on the logical state (underestimates for |0>_L, overestimates for |+>_L) and that this is decoder-driven (Fig. 9 confirms |0>_L ~ |1>_L) is a concrete actionable finding: noise-model-aware decoding must account for the decoder's response to noise bias, not just the channel itself.

## Weaknesses / limitations

- **W1 — single-channel scope.** The combined decomposition is derived and optimized for thermal relaxation only. The paper notes the question ("what other useful channels... can these principles be applied to?") but does not provide a general recipe for constructing positive Clifford decompositions of composite non-Clifford channels. The result is practically useful but narrow.

- **W2 — no public simulator / limited reproducibility.** STABSim is described but not released. The numerics rely on it. The LER ratio claims (2--10x, 1.5--2x) are given as ranges without shot counts, error bars, or confidence bounds. The BB code results use BP-OSD at a specific but not uniquely justified iteration count.

- **W3 — single-decoder, single-noise-profile experiments.** The state-dependence finding uses a single decoder (MWPM for surface, BP-OSD for BB). The "noise-model-informed decoders" conclusion is plausible but not tested — they do not actually build or run such a decoder. The experiments use a single noise profile (T1 = T2, tau varied), so sensitivity to T1/T2 ratio is not explored despite being the paper's central parameter.

## Relevance to the twin

This paper is **directly relevant to our forward simulator's noise channel selection** and the **composed carrier (C1) design**:

1. **PTA distorts thermal relaxation noise — our carrier must handle this.** The paper shows PTA misestimates LER by 2--10x depending on code state and distance, consistent with the twin's Pauli-shadowing thesis. Our composed carrier (C1, ADR 0008) must include non-Pauli thermal relaxation, not just twirled channels, to be faithful. The fidelity gap (Delta F ~ 0.02 at tau/T1 ~ 1) is the channel-level cost of the Pauli-twirl approximation for this specific noise.

2. **Clifford+reset decomposition is a candidate for the thermal relaxation component of the composed carrier.** When T2 <= T1 (the typical case: Table 1 shows median T1/T2 = 1.29 across IBM Heron devices), thermal relaxation admits an **exact, positive, stabilizer-compatible** representation. This means our scalable composed carrier can include thermal relaxation as a stabilizer-native operation — no density-matrix blowup, no QPD sampling overhead, no PTA distortion. This is a concrete design option for the carrier's thermal relaxation block.

3. **State-dependent LER confirms the twin's "structural decoder loss" thesis.** The finding that PTA misestimates LER *in opposite directions* depending on logical state (Fig. 6) echoes the twin's M4 finding: incorrect noise models cause structural decoder loss that is not captured by a uniform error-rate shift. The paper's conclusion that "noise-model-informed decoders will be essential" is aligned with the twin's thesis that recover/understand/manipulate/predict requires channel-level fidelity, not just Pauli-twirled LER matching.

4. **Gauge/identifiability not addressed.** The paper operates at the simulation level (given known noise, compute LER), not the identification level (estimate noise from syndromes). It does not discuss the observational alias, probe richness, or gauge freedom — those remain the twin's domain. The noise-model-informed decoder question is stated as an open problem, not solved.

5. **Complementary to the twin's coherent noise vector.** The paper's thermal relaxation channel is the **incoherent/dissipative** half of the full noise model; the twin's coherent wedge (single-axis over-rotation, crosstalk) is the other half. A complete forward simulator needs both, and the Clifford+reset decomposition is a natural way to include thermal relaxation without conflict with the coherent block (they compose linearly at the channel level).

6. **Practical deployment use.** The twin's `hardware/M1--M4` pipeline ingests real Google data with known T1/T2 from calibration. This paper's decomposition means the twin can include those measured T1/T2 values in its forward model without dropping into density-matrix simulation — directly enhancing the `prediction` capability's faithfulness to device calibration data.

## How to use / trust + open questions

- **Trust:** high for the exact decomposition result (Eqs. 36--37, positivity condition) — these are analytic. The reset approximation (Eq. 38) is a heuristic but well-motivated. The numerical LER results are directionally credible but lack the statistical rigor (no error bars, single simulator) to trust the precise factor ranges; treat those as qualitative rather than quantitative.

- **Open questions for the project:** (i) **Incorporate the Clifford+reset thermal relaxation decomposition into the C1 composed carrier** as the stabilizer-compatible non-Pauli block for T1/T2 noise — this avoids PTA distortion with zero QPD overhead for typical device parameters. (ii) **Verify the state-dependent LER finding with the twin's own forward simulator** (reproduce Fig. 6 to validate the carrier's thermal relaxation implementation). (iii) **Extend to the twin's noise model**: the paper uses a single uniform T1=T2 assumption; the twin's T1/T2 inputs from calibration are per-qubit and vary — does the positivity condition hold per-qubit? What about spatially correlated T1/T2 fluctuations? (iv) **Channel-to-logical mapping open problem** (flagged in Sec. IV): the twin's band engine is the natural framework to address this — the channel-level fidelity gap (Delta F) is a lower bound on the LER misestimation, but the mapping is not linear and depends on code, decoder, and state.
