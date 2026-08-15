# Full-text review — Bhardwaj et al., "Adaptive Estimation of Drifting Noise in Quantum Error Correction" (arXiv:2511.09491)

> **Provenance (2026-07-02): FULL-TEXT 精读.** Fetched from arXiv HTML (2511.09491v1). PRX Quantum accepted 2026. The paper addresses time-dependent (non-stationary) Pauli noise estimation in QEC using syndrome statistics with sliding-window estimators.

## Metadata [paper]
- Authors / affiliation: Devansh Bhardwaj, Evangelia Takou, Yingjia Lin, Kenneth R. Brown — Duke Quantum Center, Duke University (ECE, Physics, Chemistry).
- Venue / status: arXiv:2511.09491; accepted at PRX Quantum (2026).
- Type: Analytical framework + simulation for adaptive estimation of drifting Pauli noise in QEC.

## Executive summary [paper]
The paper develops an analytical framework for estimating time-dependent Pauli noise in QEC from syndrome statistics. Three methods: **(i) sliding-window** (fixed-size window, low-pass filter interpretation with Dirichlet kernel), **(ii) iterative sliding-window** (coarse-to-fine frequency resolution), **(iii) relative window** (two overlapping windows for single-pass estimation). They prove the sliding-window estimator acts as a low-pass filter with cutoff determined by window size, derive optimal window sizes analytically, and show that using the estimated time-dependent DEM in decoding suppresses logical errors compared to static DEMs. Tested on phenomenological (repetition code d=3, rotated surface code d=3) and circuit-level (d=3 repetition code with CNOTs) noise models.

## Method (deep) [paper]

**Noise model:** Single-qubit depolarizing with time-varying probability:
E_t(rho) = (1 - g(t)) rho + (g(t)/3)(X rho X + Y rho Y + Z rho Z)
with g(t) = g_0 + sum_m g_m sin(omega_m t). Circuit-level adds two-qubit depolarizing on CNOTs.

**Spitz formulas (Eqs. 1-2):**
Bulk edges: p_{ij} = 1/2 - sqrt(1/4 - (<v_i v_j> - <v_i><v_j>) / (1 - 2(<v_i>+<v_j>) + 4<v_i v_j>))
Boundary edges: p_{ii} = 1/2 + (<v_i> - 1/2) / prod_{j != i}(1 - 2 p_{ij})
These formulas assume stationary noise, and are the starting point for the sliding-window generalization.

**Sliding-window estimator (Eq. 3):**
p_{ij}^{est}(t_l) = (1/W) sum_{k=0}^{W-1} p_{ij}(t_l - W Delta t + k Delta t)
The expectation values <v_i> and <v_i v_j> are computed as normalized counts within each specific window, across experimental shots. The estimator's frequency response is the Dirichlet kernel: |sin(pi m W / N) / sin(pi m / N)|.

**Optimal window size:** For a desired damping factor epsilon on the highest-frequency component m_c:
W_opt ≈ c(epsilon) N / m_c, where c(0.05) ≈ 0.12.
For the d=3 repetition code circuit-level test: W_opt = 1228 ± 42 (analytical) vs. ~1250 (empirical from Fig. 8a).

**Relative window estimation (Eq. 11):**
p_{ij}(t_l) = (W+1) p_{ij,W+1}^{est}(t_l + Delta t) - W p_{ij,W}^{est}(t_l)
Requires Savitzky-Golay filtering before difference to ensure C^1 differentiability.

**Logical error rate metric (Eq. 15):**
Delta = (epsilon_L^{est.} / epsilon_L^{stim}) - 1
Relative precision achieved: ~10^{-4} to 10^{-3}.

## Gauge / identifiability / blind-spot analysis [paper -> ours]
**CRITICAL OMISSION:** The paper does not discuss gauge freedom in the Pauli noise estimation problem. The Spitz formulas are treated as giving unique error probabilities from detector statistics. However, the mapping from detector statistics to edge probabilities has well-known degeneracies (gauge symmetries) — different DEM assignments can produce the same syndrome statistics. This is a blind spot:

- The paper's central claim — "logical error rates from estimated models consistently align with ground truth" — may depend on the depolarizing-channel ansatz (symmetric X/Y/Z errors) which eliminates the gauge freedom by symmetry. For asymmetric or coherent noise, gauge degeneracies would return.
- The paper's criticism of Ref. [Wang2023DGR] for requiring neural networks and being "ineffective in cases where edges associate with numerous correlated counterparts" does not acknowledge that those methods may be addressing genuine identifiability issues that the Spitz formula approach sidesteps via the symmetry assumption.
- No identifiability analysis is performed: the Fisher information, nullspace of the estimator, or gauge orbits of the estimated DEM are never examined.

For our twin project, this means the paper's methods are directly usable **only for the restricted case of symmetric depolarizing noise**. Porting the sliding-window approach to our setting (coherent + incoherent channels, asymmetric Pauli, non-Pauli leakage) would require extending the Spitz formulas to handle gauge degeneracies — or using our probe-richness framework (C_cal(r)) to break them.

## Non-Markovian vs. non-stationary [paper]
The paper treats **non-stationary (time-varying) Markovian** noise, not non-Markovian noise. Eq. (3) "holds for Markovian time-dependent noise." Section V explicitly marks non-Markovian extensions as future work. This is a key limitation for our drift / prediction capability: real noise likely has both non-stationarity (drift) AND non-Markovianity (memory from fluctuators). The paper handles only the former.

## Findings + numbers [paper]
| Quantity | Value | Source |
|---|---|---|
| Optimal window (repetition code, circuit-level) | W_opt = 1228 ± 42 (analytical), ~1250 (empirical) | Sec. IV.5, Fig. 8a |
| Damping factor threshold | epsilon = 0.05 (typical) | Sec. III.1 |
| Threshold constant | c(0.05) ≈ 0.12 | Sec. III.1 |
| Depolarizing baseline | g_0 = 0.1 (phenomenological) | Sec. IV.1 |
| Frequency components tested | omega = 2pi/(10^4 Delta t), 2pi/(2x10^3 Delta t), 2pi/(5x10^4 Delta t) | Sec. IV.1-IV.3 |
| Relative window precision | ~10^{-4} to 10^{-3} | Sec. IV.5 |
| Window sizes | 500 - 12000 cycles (sliding), 2000/2001 (relative) | Sec. IV |
| Iterative window range | 10^4 down to 10^3 cycles, threshold mu = 0.22 | Sec. IV.2 |
| Circuit-level repetition code | d=3, 4 CNOTs/round, inhomogeneous error rates (Table 1) | Sec. IV.4 |

## Limitations [paper]
- **Discrete Pauli only:** Depolarizing channel (symmetric X/Y/Z) — no coherent errors, no non-Pauli channels, no amplitude/phase damping.
- **Markovian assumption:** Time-varying but memoryless within each cycle. No treatment of 1/f noise or bath memory.
- **No gauge analysis:** Potential degeneracy in DEM estimation not addressed. The Spitz formulas may give one representative of a gauge orbit, not the unique ground-truth DEM.
- **Small codes only:** d=3 repetition code and rotated surface code. Scalability to d=5/d=7 not demonstrated.
- **Circuit-level limited:** Only repetition code with CNOTs; no surface code circuit-level validation.
- **Single-qubit/qubit-pair depolarizing:** No correlated noise across >2 qubits, no crosstalk, no leakage.

## Relevance to AI_QEC [ours]
**High relevance** for the error-budget estimation and drift-tracking aspects of our project:

1. **Sliding-window methodology:** The low-pass filter interpretation of sliding windows is directly applicable to our time-dependent DEM estimation. The optimal window derivation gives a rigorous criterion for balancing bias vs. variance.

2. **Spitz formula foundation:** Our `calibration` module's observation-NLL estimator should reproduce the Spitz formulas in the stationary limit. The paper's formulas provide a baseline correctness check.

3. **Drift-aware decoding:** The paper's demonstration that estimated time-varying DEMs suppress logical errors vs. static DEMs supports our predict/drift capability (the battlefield-verdict commit from scout analysis).

4. **Blind spot for our approach:** The paper's silence on gauge tells us we need to **(a)** characterize the gauge orbit of the Spitz estimates under our noise models, **(b)** verify that the depolarizing-channel symmetry assumption does not hide identifiability issues in our setting, and **(c)** extend the sliding-window approach to handle coherent noise components.

5. **Alternative to neural-network methods:** The paper's analytical approach (closed-form formulas, no training) aligns with our preference for interpretable, theory-first methods over black-box ML.

## How to use / trust + open questions [ours]
Trust level: **high** for the analytical derivations (frequency response, optimal window, filter interpretation) and the simulation results under the stated assumptions (symmetric depolarizing, small codes). The analytical framework is rigorous. The numerical validation covers relevant QEC settings.

**Open questions for our project:**
- How does the Spitz formula estimator perform under asymmetric Pauli noise (non-depolarizing)? The symmetric ansatz may break gauge degeneracies artificially.
- Can we port the sliding-window analytical framework to our continuous-noise (classical random field) setting, where error probabilities are not discrete per-cycle but continuous?
- The paper's future-work mention of non-Markovian extension is directly relevant to our drift-plus-memory noise models.
- What is the gauge orbit of the sliding-window estimator under our probe-richness framework? Does probe richness (C_cal(r)) break degeneracies that the Spitz formulas leave intact?
