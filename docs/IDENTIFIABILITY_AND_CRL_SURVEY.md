# Identifiability and Causal Representation Learning: Survey and Application to the twin

This note records a survey of tools from causal representation learning (CRL),
identifiable latent-variable models, and quantitative finance that are directly
applicable to the the twin alias quotient and counterfactual validity problems.
It is a reference document, not a claim: none of the tools below have been
validated on this codebase yet.

## Structural Isomorphism

The observation that motivated this survey: the QEC noise-learning problem and the
latent-factor identification problem in quantitative finance are structurally
isomorphic. The precise correspondence is:

| QEC (the twin) | Finance / CRL |
|---|---|
| Observational alias quotient: `p(y\|m_a) ≈ p(y\|m_b)` | Factor rotation indeterminacy: `Σ = L Lᵀ = (LR)(LR)ᵀ` |
| DEM parity map `A ∈ F₂^{B×M}` (sparse, known) | Factor loading matrix (dense, unknown) |
| Calibration contexts `C_cal(r)`, `r = 0..4` | Multi-regime / multi-environment data |
| Interventional knob: `do(E_i → I) → ΔP_L` | Counterfactual stress test: `do(rate shock) → Δ portfolio` |
| CPTP constraint on the channel field | No-arbitrage / HJM drift restriction |
| Noise drift across calibration periods | Time-varying factor loadings / regime switching |
| CUDA-Q teacher (exact controlled ground truth) | No analogue in pure finance |

The last row is the critical asymmetry: unlike finance, the twin has a
controlled teacher that enables direct counterfactual validation at small scale.
This is the justification for the B path (ADR 0006) and makes the QEC setting
more favorable than pure finance for closing the observational-vs-interventional
gap.

The alias quotient problem belongs to the CRL literature. CRL has produced a body
of rigorous identifiability results in the past five years that directly address
the rotation / alias / indeterminacy problem. The sections below survey the most
applicable results and their mapping to the twin.

## Applicable Tools

### iVAE — Identifiable VAE with Auxiliary Variables

**Reference.** Khemakhem et al. (2020). *Variational Autoencoders and Nonlinear
ICA: A Unifying Framework.* arXiv:1907.04809. AISTATS 2020.

**Core theorem.** Let the generative model be `p_θ(y, z | u)` where context
`u` conditions the prior as a factorial exponential family:

```
p(z | u) = ∏ᵢ h(zᵢ) exp( ∑ⱼ Tᵢⱼ(zᵢ) · λᵢⱼ(u) ) / Zᵢ(u)
```

If the mixing function `f` is injective and smooth, and the matrix

```
M = ( λ(u₁) − λ(u₀) | … | λ(u_{nk}) − λ(u₀) ) ∈ ℝ^{nk × nk}
```

is invertible for `nk + 1` distinct auxiliary values, then any two parameter sets
generating the same `p(y, u)` are related by component-wise monotone
transformations and a permutation. This is the minimal unavoidable equivalence
class for latent variable models.

**Mapping to the twin.** The calibration contexts `r = 0..4` are the auxiliary
variable `u`. The noise mechanism strengths are the latent `z`. With `k = 1`
sufficient statistic per mechanism and `5` distinct contexts, up to `n = 4`
mechanisms are identifiable. Identifying `n` mechanisms requires `nk + 1` contexts.
To cover the full 35-mechanism catalog in principle, multiple iVAE instances
stratified by physical location / mechanism type are needed, or `k > 1` sufficient
statistics (e.g., mean and variance of the mechanism strength prior per context).

**Critical adaptation required.** iVAE requires a continuous, injective mixing
function. Syndrome data `y ∈ {0,1}^B` is binary; the DEM map `A` is not injective
over `ℝ`. The correct adaptation is to work at the **detector polarization level**:

```
π_b = E[(-1)^{y_b}] ∈ [-1, +1]     (continuous, real-valued)
```

Polarizations are continuous linear functionals of the syndrome distribution and
carry the same information as detector marginals. Apply iVAE to `π` vectors, not
to raw syndrome bits.

---

### Sparse VAE Anchor Feature Identifiability

**Reference.** Moran, Sridhar, Wang, Blei (2022). *Identifiable Deep Generative
Models via Sparse Decoding.* arXiv:2110.10804. TMLR 2023.

**Core theorem.** A sparse deep generative model is identifiable up to permutation
and element-wise transformation if and only if each latent factor `zⱼ` has at
least two **anchor features**: observed coordinates that load on `zⱼ` alone (zero
loading from all other factors).

**Mapping to the twin.** An anchor feature for mechanism `j` is a syndrome bit
`b` such that the DEM parity map column `A_{:,j}` has `A_{b,j} = 1` and
`A_{b,j'} = 0` for all `j' ≠ j`. In other words, syndrome bit `b` fires only
when mechanism `j` is active and no other mechanism can trigger it.

This condition is **verifiable today** from the known DEM structure:

```python
for j in range(M):
    anchor_bits = [b for b in range(B)
                   if A[b, j] == 1 and A[b, :].sum() == 1]
    identifiable = len(anchor_bits) >= 2
```

Mechanisms without two anchor bits enter the alias quotient and cannot be
identified without auxiliary context variation. This calculation gives the
information-theoretic ceiling on mechanism-level identifiability before any
modeling assumption.

**Advantage over iVAE.** Works in a single-environment setting; identification
comes from structure alone, not distributional variation across contexts. The two
approaches are complementary: anchor features identify mechanisms from physics,
iVAE strengthens identification via context variation for mechanisms without
anchors.

---

### UT-IGSP and the Sparse Mechanism Shift Hypothesis

**References.**
- Squires et al. (2020). *Permutation-Based Causal Structure Learning with Unknown
  Intervention Targets (UT-IGSP).* arXiv:1910.09007. UAI 2020.
- Mooij et al. (2022). *Causal Discovery in Heterogeneous Environments Under the
  Sparse Mechanism Shift Hypothesis.* arXiv:2206.02013. NeurIPS 2022.

**Core idea.** The Sparse Mechanism Shift Hypothesis posits that distributional
shifts across environments are caused by changes in only a small number of causal
conditionals. The Mechanism Shift Score (MSS) identifies the complete causal
graph under this assumption, even when intervention targets are unknown.

**Mapping to probe-richness ladder.** Each calibration context `r` is an
environment with a sparse set of mechanism activations changing. Context `r = 0`
(memory circuit) establishes a Pauli-noise baseline; `r = 2` (active probes)
changes the variance of coherent-sensitive syndrome bits; `r = 4` (non-Clifford)
activates phase-sensitive mechanisms. The sparsity of these shifts across contexts
is precisely the MSS condition.

UT-IGSP handles unknown intervention targets (which mechanisms each context
perturbs) — the realistic case for the twin, since no context surgically isolates
a single mechanism. Applied to polarization vectors across contexts, it returns
the interventional Markov equivalence class of the mechanism interaction graph.

**Limitation.** MSS requires distributional testing across environments and needs
sufficient samples per context. At low physical error rates, the required sample
count to detect mechanism-level shifts may be large.

---

### Mechanism Sparsity Regularization

**Reference.** Lachapelle, Brouillard, Deleu, Lacoste-Julien (2022).
*Disentanglement via Mechanism Sparsity Regularization: A New Principle for
Nonlinear ICA.* arXiv:2107.10098. CLeaR 2022.

**Core result.** Regularizing the learned decoder to be sparse — so that each
latent factor influences only the observed coordinates physically reachable by
that mechanism — achieves identifiability up to permutation when a graph
connectivity criterion is satisfied.

**Mapping to the twin.** The known DEM footprint of each mechanism (the set of
syndrome bits in column `j` of `A`) is the natural sparsity mask for the decoder.
Regularizing `diff_cptp_channel`'s syndrome prediction to respect the known DEM
structure is both physically motivated and provably sufficient for identifiability.
This turns a physical prior into an identification constraint without needing
additional context variation.

Physical constraint → identification constraint: CPTP + DEM sparsity structure
provides two independent routes to identifiability that can cross-validate.

---

### Invariant Causal Prediction (ICP) in Mechanism Space

**References.**
- Peters, Bühlmann, Meinshausen (2016). *Causal inference by using invariant
  prediction.* JRSS-B. DOI:10.1111/rssb.12167.
- Heinze-Deml, Peters, Meinshausen (2018). *Invariant Causal Prediction for
  Nonlinear Models.* arXiv:1706.08576.

**Core idea.** Identify causal parents `S*` of a target `Y` by testing which
subsets `S` have an invariant conditional distribution `p(Y | X_S)` across
environments. In the linear Gaussian case, invariance reduces to testing whether
residuals are i.i.d. across environments.

**Mapping to the twin.** The target `Y` is the logical error rate `P_L`; the
candidates are noise mechanism strengths `{m₁, …, m_M}`. ICP in mechanism space
asks which mechanisms are causal parents of `P_L` with a conditional distribution
that is invariant across calibration contexts.

**Two-stage caveat.** Standard ICP assumes causes are observed. Noise mechanisms
are latent — only syndromes are observed. A two-stage pipeline is required:

```
Stage 1: recover mechanisms up to permutation / scaling
         (via iVAE + anchor features + mechanism sparsity)
Stage 2: apply nonlinear ICP in recovered mechanism space
         (test invariance of p(P_L | m_S) across contexts)
```

Errors from Stage 1 propagate into Stage 2. The ICP test must be permutation-
invariant (require a mechanism matching step across contexts). The nonlinear
extension (arXiv:1706.08576) replaces the conditional independence test with a
nonparametric distributional test (KS or chi-squared on residual distributions),
adapted for the discrete binary setting.

---

### SMC-MCMC for Drift Tracking

**References.**
- arXiv:2507.06941. Robust SMC calibration for quantum devices.
- arXiv:2511.09491. Adaptive estimation of drifting Pauli noise in QEC.

**What exists.** Sequential Monte Carlo with Hamiltonian MC proposals for
quantum device parameter tracking. Particles drift under a parameter dynamics
model (e.g., Ornstein-Uhlenbeck); they are weighted by the new syndrome batch
likelihood and resampled. Validated on superconducting qubits; reports 10× lower
uncertainty than standard particle filters using 99.5% fewer calibration circuits.

The sliding-window Pauli drift estimator (arXiv:2511.09491) operates directly on
syndrome data without prior decoding, provides analytically optimal window sizes,
and handles multi-frequency drift in a single pass.

**For the twin.** Replace the Ramsey/Hahn echo likelihood (from the IBM
calibration context) with the exact syndrome NLL from `diff_circuit_sim`. The
sequential update structure is identical. The SMC-MCMC approach naturally handles
abrupt jumps (volatile drift) that standard Kalman filters miss.

---

### HJM / No-Arbitrage as a CPTP Analogy (Finance Import)

**Reference.** arXiv:2511.17892. Arbitrage-free neural term structure with HJM.

The Heath-Jarrow-Morton no-arbitrage constraint determines the forward rate drift
from the volatility:

```
μ(t, T) = σ(t, T) · ∫ₜᵀ σ(t, s) ds
```

This is mathematically analogous to CPTP: a constraint on the parameter dynamics
derived from first principles (no free lunch / trace preservation + complete
positivity). The neural HJM implementation enforces the constraint as a soft
penalty rather than a hard projection — the same approach available for CPTP in
the Pauli error rate parameterization.

**Finance lesson for the twin.** Impose CPTP as a soft Choi-PSD penalty in the
Pauli error rate parameterization during calibration, not as a hard projection
after each gradient step. Hard projections on Stiefel manifolds (Kraus form)
introduce gauge freedom; the Pauli rate parameterization (linear constraints) does
not.

## Critical Warnings

### W1: Counterfactual Non-Identifiability Theorem

**Reference.** Nasr, Mooij, Forré (2023). *Counterfactual (Non-)identifiability
of Learned Structural Causal Models.* arXiv:2301.09031.

**Result.** For general multi-dimensional exogenous noise, counterfactual
distributions are not point-identified from observational data alone, even with
known causal structure and no hidden confounding. A model that perfectly fits all
5 calibration-context syndrome distributions can still give wrong `do()` answers.

**Implication for the twin.** This is the central risk formalized. Counterfactual
validity cannot be established from observational equivalence alone. The CUDA-Q
teacher is the only available path to empirical b-validity validation (ADR 0006).

**Partial identification alternative.** Rather than point-estimating `do(remove
M7) → ΔP_L`, compute worst-case bounds using the Zhang-Bareinboim algorithm
(arXiv:2110.05690). This is the honest uncertainty quantification for `do()`
queries before b-validity is established.

---

### W2: Learnable Degrees of Freedom Ceiling

**Reference.** Bravyi, Haah, Hastings (2025). *Efficient Learning of Logical
Noise from Syndrome Data.* arXiv:2601.22286.

**Result.** The degrees of freedom learnable from syndrome data are strictly
smaller than `M`. The learnable subspace is the image of a specific linear map
determined by the DEM structure `A`. Any identifiability claim must remain within
this information-theoretic ceiling.

Before claiming that mechanism `j` is separately identified, verify that the
corresponding direction lies in the learnable subspace. Mechanisms that project
to zero in this subspace are fundamentally unrecoverable from syndromes alone,
regardless of the identification method used.

---

### W3: Binary Observations Break Continuous Tools

Every tool reviewed — ICA, PCA/Varimax, iVAE, IGSP, Kalman filters — assumes
continuous-valued observations. Syndrome data `y ∈ {0,1}^B` is binary. Apply
these tools at the **polarization level** (continuous, real-valued) rather than
the raw syndrome level. Kolmogorov-Smirnov and other continuous distributional
tests used in nonlinear ICP fail for binary data; use chi-squared or likelihood
ratio tests on contingency tables instead.

---

### W4: CPTP Constraints Do Not Factorize in Kraus Form

The Kraus representation has gauge freedom: different Kraus sets `{Kᵢ}` and
`{K̃ᵢ}` represent the same channel. This gauge freedom is an additional
indeterminacy layer on top of the alias quotient. The safe parameterization for
identifiability work is the **Pauli error rate vector** — a vector of
non-negative probabilities summing to at most 1, with linear constraints and no
gauge freedom. iVAE and sparse VAE identifiability results apply directly in this
parameterization.

---

### W5: Coherent Errors Break the Pauli DEM Assumption

**Reference.** Takou and Brown (2025). *Estimating and Decoding Coherent Errors
via Detector Error Models.* arXiv:2510.23797.

Coherent errors (unitary miscalibrations) produce DEM "hyperedges" absent in
Pauli-twirled models and manifest as interference effects in syndrome fire rates.
The `r = 4` probe contexts (non-Clifford, phase-sensitive) are necessary to
reveal them. The identification machinery must be extended to handle the nonlinear
observation model that coherent errors introduce. Until this extension is
implemented, the identified noise model is valid only for the stochastic Pauli
subspace.

## Prioritized Action Items

| Priority | Action | Tool / Reference |
|---|---|---|
| P0 | Check anchor bit condition for each of the 35 catalog mechanisms against the known DEM `A` | arXiv:2110.10804 |
| P0 | Compute the learnable subspace from `A`; confirm which mechanisms are above the information-theoretic ceiling | arXiv:2601.22286 |
| P1 | Apply iVAE at the polarization level; verify the invertibility condition for the sufficient statistics matrix with 5 contexts | arXiv:1907.04809 |
| P1 | Add DEM-footprint-matching mechanism sparsity regularization to `diff_cptp_channel` decoder | arXiv:2107.10098 |
| P2 | Implement Zhang-Bareinboim partial identification for `do()` query bounds before claiming point-identified counterfactuals | arXiv:2110.05690 |
| P2 | Integrate sliding-window Pauli drift estimator for calibration period tracking | arXiv:2511.09491 |
| P3 | Apply UT-IGSP / MSS to multi-context polarization vectors to orient the mechanism interaction graph | arXiv:1910.09007, arXiv:2206.02013 |

## Reference List

The load-bearing references are cached locally as PDFs under `docs/papers/`
(see `docs/papers/README.md` for the per-paper index and relevance map). Prefer
the local cache over a fresh web search.

### Identifiability and Nonlinear ICA

- Khemakhem et al. (2020). iVAE. arXiv:1907.04809.
- Moran, Sridhar, Wang, Blei (2022). Sparse VAE anchor identifiability. arXiv:2110.10804.
- Lachapelle et al. (2022). Mechanism sparsity regularization. arXiv:2107.10098.
- Hyvarinen, Sasaki, Turner (2019). Nonlinear ICA with auxiliary variables. AISTATS 2019.
- Ahuja et al. (2023). Sparse ICA without non-Gaussianity. arXiv:2408.10353.
- Rohe & Zeng (2023). Varimax identifies heavy-tailed factors. JRSS-B 85(4).

### Multi-Environment Causal Discovery

- Peters, Bühlmann, Meinshausen (2016). ICP. JRSS-B. DOI:10.1111/rssb.12167.
- Heinze-Deml, Peters, Meinshausen (2018). Nonlinear ICP. arXiv:1706.08576.
- Squires et al. (2020). UT-IGSP. arXiv:1910.09007.
- Mooij et al. (2022). Sparse mechanism shift / MSS. arXiv:2206.02013.
- Yu et al. (2025). Two environments suffice under sufficient variability. arXiv:2510.13583.
- von Kügelgen et al. (2023). Nonparametric identifiability from unknown interventions. arXiv:2306.00542.
- Arjovsky et al. (2019). Invariant Risk Minimization. arXiv:1907.02893.

### Counterfactual Validity and Partial Identification

- Nasr, Mooij, Forré (2023). Counterfactual non-identifiability. arXiv:2301.09031.
- Zhang & Bareinboim (2022). Partial counterfactual identification. arXiv:2110.05690.
- Borysov, Kenny, Alexander (2017). Causal data science for financial stress testing. arXiv:1703.03076.

### QEC-Specific Noise Learning and Drift

- Bravyi, Haah, Hastings (2025). Learnable degrees of freedom from syndromes. arXiv:2601.22286.
- Takou & Brown (2025). Coherent errors via DEMs. arXiv:2510.23797.
- Wills et al. (2025). DEM estimation via Walsh-Hadamard. arXiv:2504.14643.
- Kobori & Todo (2024). Bayesian noise inference from syndrome statistics. arXiv:2406.08981.
- Hauri et al. (2025). Sliding-window Pauli drift estimation. arXiv:2511.09491.
- arXiv:2507.06941. Robust SMC-MCMC calibration for quantum devices.
- arXiv:2603.00837. ReloQate: drift detection in surface code QEC.

### Finance / Physical Constraints Analogy

- arXiv:2511.17892. Neural HJM with no-arbitrage penalty (CPTP analogy).
- Xie et al. (2023). Generalized Independent Noise condition. arXiv:2308.06718.
- Lachapelle et al. (2023). Synergy between sufficient changes and sparse mixing. arXiv:2503.00639.
