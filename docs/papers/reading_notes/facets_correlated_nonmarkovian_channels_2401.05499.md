# Full-text review — Sabale, Dash, Kumar & Banerjee, "Facets of correlated non-Markovian channels" (arXiv:2401.05499v2; Annalen der Physik 2024, 2400151)

> **Provenance (2026-07-03): FULL-TEXT read (精读).** arXiv HTML fetch
> (`WebFetch arxiv.org/html/2401.05499v2`) + abstract page. 10+ figures across 6
> main sections + 2 appendices. All section/equation/figure refs from extracted text.
> Tags: **[paper]** = stated in the paper; **[twin]** = our application/inference for
> `qec_twin`, NOT the paper's claim.

## Metadata [paper]
- **Authors / affiliation.** Vivek Balasaheb Sabale, Nihar Ranjan Dash, Atul Kumar,
  Subhashish Banerjee (IIT Jodhpur, Depts. of Chemistry and Physics). Banerjee group
  has published extensively on non-Markovianity, open quantum systems, and correlated
  noise channels.
- **Venue / status.** arXiv:2401.05499v2 [quant-ph], 26 Jun 2024 (v1: 10 Jan 2024);
  published Annalen der Physik 2024, 2400151.
- **Type.** Analytic theory + numerical evaluation of correlated non-Markovian channels
  (unital and non-unital), studying non-Markovianity measures, volume of accessible
  states, freezing of correlations, and QEC success probability.

## Executive summary [paper]
The paper systematically studies **correlated non-Markovian channels** — quantum channels
where successive uses are correlated (controlled by a correlation factor `mu in [0,1]`)
and also individually non-Markovian (either CP-divisible or CP-indivisible). Three noise
models are used: **random telegraph noise (RTN)**, **Ornstein-Uhlenbeck noise (OUN)**,
and **non-Markovian amplitude damping (NMAD)**. Key findings:

1. **Channel correlation enhances non-Markovianity** for both unital (RTN, OUN) and
   non-unital (NMAD) channels. Two types of non-Markovianity are identified: (a)
   **retaining correlation** (CP-divisible, OUN) and (b) **information backflow**
   (CP-indivisible, RTN and NMAD).

2. **For unital channels (OUN, RTN):** Bell-state concurrence shows **decreased revival
   rates with increasing `mu`** (freezing at `mu = 1` for Bell-diagonal states).
   Locally transformed Bell states (`|alpha>` states) show **enhanced non-Markovianity**
   with increasing `mu`.

3. **For non-unital NMAD:** Concurrence revival rates for Bell states are **enhanced**
   with increasing `mu` — opposite to the unital case.

4. **SSS measure on correlated OUN** (CP-divisible) confirms that non-Markovianity `zeta`
   increases with `mu`, measured as deviation from temporal self-similarity.

5. **Volume of accessible states** `V(t) = det[F(t)]` provides a **state-independent**
   non-Markovianity witness: non-monotonic volume change (CP-indivisible) is enhanced
   by `mu`; monotonic volume increase (OUN) also grows with `mu`.

6. **Freezing of quantum correlations** occurs for specific states: Bell-diagonal states
   in unital channels with `mu = 1`; `|psi^{+-}>` states in fully correlated NMAD,
   requiring `c_1 = c_2`, `c_3 = -1`.

7. **Error correction success probability** for a concatenated code (3-qubit phase-flip x
   2-qubit bit-flip) depends on the correlation factor `mu`: higher `mu` improves
   success probability for both OUN and RTN correlated dephasing. This links channel
   correlation to QEC performance.

## Correlated channel construction (Section II) [paper]
The foundational construction of **correlated two-qubit channels** (Section II, Eqs. 1-5):

A single-qubit channel `E(rho) = sum_i A_i rho A_i^dagger`. Two-qubit channels acting on
two successive uses:

- **Uncorrelated:** `E^{uncorr}(rho) = sum_{ij} (A_i otimes A_j) rho (A_i^dagger otimes A_j^dagger)` — tensor product.
- **Correlated:** `E^{corr}(rho) = sum_{i1 i2} A_{i1 i2} rho A_{i1 i2}^dagger`, with
  `A_{i1 i2} = sqrt(p_{i1 i2}) B_{i1} otimes B_{i2}`.

**Correlation model (the key formula, Eq. 4):**
`p_{i1 i2} = (1 - mu) p_{i1} p_{i2} + mu p_{i1} delta_{i1 i2}`
where `mu in [0,1]` is the **channel correlation factor**. `mu=0` = uncorrelated
(product distribution), `mu=1` = fully correlated (same index).

The overall map (Eq. 5):
`E^{corr}(rho) = (1 - mu) E^{uncorr}(rho) + mu E^{fcorr}(rho)`
— a convex combination of the uncorrelated and fully-correlated maps.

Channels are classified as **unital** (`E(I_2) = I_2`) or **non-unital** (`E(I_2) != I_2`).

## Noise models (Section III) [paper]

### Unital: RTN and OUN (Section III.1)
Single-qubit Kraus operators: `K_i = sqrt(q_i) sigma_i` for `i = 0,1,2,3`. For dephasing:
`q_0 = 1/2 [1 + p(t)]`, `q_1 = q_2 = 0`, `q_3 = 1/2 [1 - p(t)]`.

**RTN noise function:**
`p(t) = exp(-gamma t)[cos(omega gamma t) + sin(omega gamma t)/omega]` (Eq. 8a)
where `omega = sqrt((2a/gamma)^2 - 1)`, `a` = system-environment coupling strength,
`gamma` = fluctuation rate of the RTN process.

**OUN noise function:**
`p(t) = exp[-(G/2)(t + (1/g)(e^{-gt} - 1))]` (Eq. 8b)
where `g^{-1} = tau_c` = finite correlation time of the environment, `G` = effective
relaxation rate. The Markov limit is `1/g -> 0`.

The correlated unital map (Eqs. 9-11) for two qubits:
`E^{corr}(rho) = p_{00} (sigma_0 otimes sigma_0) rho (sigma_0 otimes sigma_0)
 + p_{03} (sigma_0 otimes sigma_3) rho (sigma_0 otimes sigma_3)
 + p_{30} (sigma_3 otimes sigma_0) rho (sigma_3 otimes sigma_0)
 + p_{33} (sigma_3 otimes sigma_3) rho (sigma_3 otimes sigma_3)`
with `p_{ij} = (1-mu) q_i q_j + mu q_i delta_{ij}`.

### Non-unital: NMAD (Section III.2)
Master equation (Eq. 12):
`L(rho) = gamma(t)[sigma_- rho sigma_+ - 1/2 sigma_+ sigma_- rho - 1/2 rho sigma_+ sigma_-]`

Time-dependent decay rate (Eq. 13):
`gamma(t) = -(2/|G(t)|)(d|G(t)|/dt)`

Decoherence function (Eq. 14):
`G(t) = e^{-gt/2}[cosh(l t/2) + (g/l) sinh(l t/2)]`
where `l = sqrt(g^2 - 2 gamma_0 g)`.

**Fully correlated NMAD Kraus operators (Eqs. 16a-16b):**
`E_{00} = diag(1, 1, 1, sqrt(1-p(t)))` — 4x4 matrix
`E_{11}` has a single nonzero entry: `[E_{11}]_{0,3} = sqrt(p(t))`
where `p(t) = 1 - |G(t)|^2` (Eq. 17).

The fully correlated NMAD master equation (Eq. 15):
`L^{fcorr}(rho) = gamma(t)[(sigma_- otimes sigma_-) rho (sigma_+ otimes sigma_+)
 - 1/2 (sigma_+ otimes sigma_+)(sigma_- otimes sigma_-) rho
 - 1/2 rho (sigma_+ otimes sigma_+)(sigma_- otimes sigma_-)]`

This represents a **two-qubit simultaneous decay** — both qubits decay together,
capturing a correlated amplitude damping process.

## Non-Markovianity measures (Section IV) [paper]
The paper uses a comprehensive set of complementary measures:

**BLP measure (trace distance, Eq. 21-23):**
`N_D(E) = max_{rho_1(0), rho_2(0)} int_{dD/dt > 0} (dD/dt) dt`
where `D(rho_1, rho_2) = 1/2 tr|rho_1 - rho_2|`. Non-Markovianity is signaled by
`dD/dt > 0` (information backflow).

**Entanglement-based non-Markovianity (Eqs. 24-26):**
For correlated channels (which are implementable via LOCC), entanglement (concurrence)
serves as the monotone `X`. Condition: `X[E_t rho_AB] > X[E_s rho_AB]` for `t > s`
signals non-divisible dynamics. The measure:
`N(E) = max_{rho_AB} int_{dX/dt > 0} (dX/dt) dt`

**Concurrence (Eq. 27):** `C(rho) = max{0, lambda_1 - lambda_2 - lambda_3 - lambda_4}`
where `lambda_i` are sqrt of eigenvalues of `rho rho_tilde` with
`rho_tilde = (sigma_y otimes sigma_y) rho^* (sigma_y otimes sigma_y)`.

**SSS measure (Eq. 28) — for CP-divisible (OUN):**
`zeta = min_{L^*} (1/T) int_0^T || L(t) - L^* || dt`
where `L^*` is the time-independent generator of the quantum dynamical semigroup
(the Markov limit). `zeta` quantifies the deviation from temporal self-similarity.
For correlated OUN: `zeta` increases with `mu` (Fig. 2).

## Volume of accessible states (Section V) [paper]
**Definition (Eqs. 29-30):** `V(t) = det[F(t)]` where `F(t)` is the matrix
representation of the dynamical map in the operator basis. Non-Markovianity witness:
`dV(t)/dt > 0`.

**Results (Fig. 3):**
- **Correlated NMAD** (`g=0.02, gamma_0=6`): non-monotonic `V(t)`, oscillations
  enhanced with `mu` (CP-indivisible -> information backflow).
- **Correlated RTN** (`a=0.8, gamma=0.05`): similar non-monotonic behavior enhanced
  with `mu`.
- **Correlated OUN** (`g=0.05, G=1`): `V(t)` increases with `mu` but no non-monotonic
  behavior — consistent with CP-divisible dynamics.

The volume measure is **state-independent** — it captures non-Markovianity from the
map structure itself, not from a specific initial state.

## Freezing of correlations (Section VI) [paper]
**For unital correlated channels (Eqs. 31-32):** The evolved density matrix under
correlated dephasing has off-diagonal elements modulated by:
- Anti-diagonal entries `rho_{14}, rho_{23}, rho_{32}, rho_{41}` are multiplied by
  `tau(mu) = mu + p(t)^2 (1 - mu)`.
- Other off-diagonals are multiplied by `p(t)` alone.

For Bell-diagonal states `rho = 1/4 (I otimes I + sum_i c_i sigma_i otimes sigma_i)`:
`c(t) = {c_1 tau(mu), c_2 tau(mu), c_3}`.
**At `mu = 1`:** `tau(mu) = 1` => `c(t) = c(0)` — **complete freezing**.

**For fully correlated NMAD (Eq. 33):** Bell-diagonal states with `c_3 = -1` evolve as:
`c(t) = {1/2[c_1+c_2+(c_1-c_2)(1-p(t))], 1/2[c_1+c_2+(-c_1+c_2)(1-p(t))], -1}`.
Freezing when `c_1 = c_2` and `c_3 = -1` — the `|psi^{+-}>` state.

## Error correction success probability (Section VII) [paper]
**Code structure:** Concatenated code (3-qubit phase-flip outer + 2-qubit bit-flip inner):
- Outer: `|0_bar> = |+++>`, `|1_bar> = |--->`, stabilizer `<XXI, XIX>`, logical `ZZZ`.
- Inner: `|0_under> = |00>`, `|1_under> = |11>`, stabilizer `<ZZ>`.
- Building block: `|+-)> = (1/sqrt(2))(|0_under> +- |1_under>)`.

The test state is `|phi>_conc = (1/sqrt(2))(|0>_conc + |1>_conc)`, a 6-qubit
superposition encoding one logical qubit.

**Error detectability conditions (Eq. 39):** For each error operator `epsilon_i`:
`<0_conc| epsilon_i |0_conc> = <1_conc| epsilon_i |1_conc>` (diagonal equality)
`<0_conc| epsilon_i |1_conc> = <1_conc| epsilon_i |0_conc> = 0` (off-diagonal zero)

**Results (Fig. 5):**
- Correlated OUN (`G=1, g=0.05`): success probability `P_success` vs time for
  `mu = 0, 0.5, 1`. Higher `mu` gives higher success probability.
- Correlated RTN (`a=0.8, gamma=0.05`): same trend — higher `mu` improves QEC.
- The paper explicitly establishes the **link between channel correlation `mu` and
  QEC performance**: as the correlation factor increases, the success probability
  improves because correlated errors are more detectable by the concatenated code
  structure (they affect both qubits in the inner code identically, making them
  more likely to be corrected by the bit-flip inner code).

## Limitations [paper]
- **L1 — Single-qubit channels.** All noise models are single-qubit channels (dephasing
  or amplitude damping); the correlated channel acts on two successive uses of the
  same single-qubit channel, not on a two-qubit system with a shared bath. This is
  a phenomenological correlation model, not a microscopic bath model.
- **L2 — No temporal structure beyond pairwise correlation.** The correlation parameter
  `mu` captures same-index correlation between two uses. Multi-time (>2) correlations
  are not modeled. The modified OUN noise is Markovian in the underlying process
  (the OU process is Gaussian-Markov), so it cannot produce the multi-time "streaky"
  correlations that are the catastrophic regime for QEC (cf. Kam et al.
  arXiv:2410.23779).
- **L3 — 2-use correlation only.** The model only correlates pairs of channel uses,
  not longer sequences. For QEC with many rounds, this limits applicability.
- **L4 — No full surface-code QEC.** The QEC analysis (Section VII) uses a
  concatenated code (6 physical qubits encoding 1 logical). No surface-code
  simulation with MWPM decoding is performed — the error correction is code-specific
  and the success probability is per-block, not per-logical-error.
- **L5 — No explicit detector statistics.** The paper computes concurrence, volume,
  and success probability, but does not compute detection event rates or detector
  correlation functions — the observables the twin uses.
- **L6 — SSS measure truncation.** The SSS measure requires a minimization over `L^*`,
  which is computationally non-trivial; the numerical results (Fig. 2) are shown for
  specific parameter values without exhaustive error bars.
- **L7 — No finite-temperature NMAD.** The NMAD model uses a zero-temperature bath
  (only decay, no excitation). Thermal effects would add the `sigma_+` process
  (excitation), producing a different correlation structure.

## Relevance to the twin — noise simulator, closed-form detector statistics [twin]
1. **The `mu` model as a phenomenological coupling-simulator ingredient.** The
   correlated channel construction `E^{corr} = (1-mu) E^{uncorr} + mu E^{fcorr}`
   (Eq. 5) is the simplest possible interpolation between independent and perfectly
   correlated noise. The twin could use this as a **minimal parametric model** for
   per-round correlated noise in the coupling simulator: `mu` controls the
   strength of same-type error correlation between consecutive QEC rounds, while
   the base noise model `p(t)` provides the non-Markovian (memory) component.
   **[twin: noise simulator]**

2. **Modified OUN noise for the twin's `Sigma` process.** The OUN noise function
   `p(t) = exp[-(G/2)(t + (1/g)(e^{-gt} - 1))]` (Eq. 8b) is a **closed-form
   stationary Gaussian process** with finite correlation time `tau_c = 1/g`. This
   is exactly the kind of noise model the twin needs for the continuous `Sigma`
   bath process in the coupling simulator: `Sigma(t)` can be modeled as an OUN
   process, and its time-discretized version at QEC round boundaries gives the
   per-round correlated noise. The OUN is **CP-divisible** (Markovian at the
   master-equation level despite the finite correlation time) — which means it's
   tractable analytically but cannot produce the catastrophic multi-time
   correlations that require CP-indivisible dynamics. **[twin: continuous Sigma]**

3. **Closed-form detector statistics for OUN noise.** Because OUN is a Gaussian-
   Markov process, the joint distribution of `Sigma` values at discrete round
   times `t_1, ..., t_R` is a multivariate Gaussian with exponential covariance
   `Cov(t_i, t_j) ~ exp(-g|t_i - t_j|)`. This gives **closed-form detector
   statistics** (marginal detection rates, pairwise correlations) for the twin's
   passive detector records when the noise is OUN-dephasing. The twin could
   compare these closed-form predictions to the MPS carrier's empirical detector
   statistics to validate the carrier. **[twin: closed-form detector statistics]**

4. **RTN as a two-state fluctuator model.** The RTN noise function (Eq. 8a) models
   the qubit coupled to a two-level fluctuator (TLF) — the canonical source of
   1/f noise in superconducting qubits. For the coupling simulator's `Sigma`
   process, a bath composed of many RTNs (each with different `gamma` and `a`)
   produces 1/f^alpha noise. The paper's correlated RTN model is a single-TLF
   version; the twin would need the multi-TLF generalization for realistic
   flux-noise simulation. **[twin: noise simulator]**

5. **Freezing of correlations and noise simulator gauge.** The freezing phenomenon
   (`mu = 1` => `c(t) = c(0)` for Bell-diagonal states) is a striking effect:
   **fully correlated dephasing noise does NOT decohere Bell-diagonal states at
   all** (the off-diagonal decay factor `tau(mu)` becomes unity). This has gauge
   implications: a learner that only sees Bell-diagonal states (e.g., the encoded
   logical state in a stabilizer code) would infer zero noise when `mu = 1`,
   even though individual qubits are dephased. This is a concrete example of
   how channel correlation creates **observational aliasing** — the same logical
   outcome can arise from different physical noise regimes. **[twin: gauge/
   identifiability]**

6. **Volume of accessible states as a gauge witness.** The volume measure
   `V(t) = det[F(t)]` is state-independent and changes with both non-Markovianity
   and correlation. For the twin's audit capability, `V(t)` could serve as a
   **model-independent witness** of non-Markovian correlated noise: if the
   dynamical map's accessible volume changes non-monotonically, the noise has
   CP-indivisible (non-Markovian) components that cannot be captured by any
   time-independent Lindbladian. The twin could compute an estimate of `V(t)`
   from the reconstructed dynamical map to test for non-Markovianity.
   **[twin: audit]**

7. **Concatenated code QEC success as a benchmark for the twin's coupling
   simulator.** The paper's linking of `mu` to QEC success probability provides
   a **benchmark curve**: for a given `(mu, t)`, the success probability `P_success`
   should follow the paper's Fig. 5. The twin's coupling simulator, fed with
   the same noise model parameters, should reproduce this curve as a validation
   test. This is particularly valuable because it's a **non-trivial nonlinear
   observable** (the QEC success probability depends on the full correlated noise
   structure, not just marginals) — a passing test would be strong evidence
   that the carrier correctly captures correlation effects. **[twin: validation]**

8. **Contrast with Kam et al. (2410.23779).** Both papers study correlated noise
   and QEC, but in complementary ways:
   - Kam studies **multi-time streaky correlations** (the catastrophic regime)
     using surface-code simulation. The present paper studies **pairwise
     channel-use correlation** `mu` using a concatenated code.
   - Kam's correlations are **temporal** (across rounds). This paper's `mu` could
     be interpreted as either spatial (correlation between two qubits in the same
     code) or temporal (correlation between two successive uses), but the model
     is inherently two-use.
   - Kam's key result is that **detector autocorrelation is insufficient** to
     distinguish benign from catastrophic correlations. This paper's volume and
     concurrence measures could be complementary witnesses that do distinguish.
   - The twin should use **both**: Kam's streaky model for the temporal axis
     (WS2 5b), and the `mu` model of this paper for the **pairwise correlation
     axis** — they describe different physical regimes and have different
     observable signatures. **[twin: complementary axes]**

## How to use / trust + open questions [twin]
- **Trust:** medium-high. The analytic derivations (channel construction, Kraus operators
  for correlated NMAD, closed-form freezing conditions) are exact. The numerical results
  (concurrence, volume, SSS measure) are from standard numerical integration and are
  consistent across measures. Main caveat: the `mu` model is phenomenological, not
  derived from a microscopic bath — results depending on the specific `p_{ij}` form
  may not generalize to other correlation structures.
- **How to use:** (i) OUN noise (Eq. 8b) as the closed-form model for the twin's
  continuous `Sigma` process; (ii) the `mu`-correlated channel as a minimal parametric
  model for per-round correlated dephasing; (iii) the freezing of Bell-diagonal states
  at `mu=1` as a gauge/identifiability test case; (iv) the QEC success probability
  (Fig. 5) as a benchmark for the twin's coupling simulator validation.
- **Open for the twin:** (i) Generalize the `mu` model from 2-use to R-use — does
  the convex combination structure extend naturally, or does `mu` need to become
  `mu_{ij}`? (ii) Can the volume measure `V(t)` be estimated from the twin's
  reconstructed dynamical map (with finite data and tomography noise)? (iii) Does
  the OUN closed-form `p(t)` match the noise autocorrelation extracted from the
  twin's MPS carrier at equivalent parameter values? (iv) The paper's NMAD model
  uses zero temperature — the twin's amplitude damping model should include
  finite-temperature effects (thermal excitation rate `n_th gamma`).
