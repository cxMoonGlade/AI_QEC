# Full-text review — Tong Shen & Daniel A. Lidar, "Real-time Sign-Problem-Suppressed Quantum Monte Carlo Algorithm For Noisy Quantum Circuit Simulations" (arXiv:2502.18929v2)

> **Provenance (2026-06-20): full PDF read.** Built from the cached PDF
> `docs/papers/Real-time Sign-Problem-Suppressed Quantum Monte Carlo Algorithm For Noisy.pdf`
> (20 pp.: 7-pp. main text incl. four End Matters, then the Supplemental Material S1–S8 with
> Algorithms 1–2, error-bound proofs, and scaling fits). The Read tool false-rejects the PDF as
> "password-protected" (owner-encryption quirk, shared by other papers in this cache); I worked from a
> `pdftotext -layout` extract (`/tmp/qmc_signprob.txt`, 1804 lines = the complete text incl. all
> equations and captions) **plus** per-page `pdftoppm -png` raster renders. **Figures inspected
> visually:** Fig. 1 (algorithm schematic + the two benchmark circuits), Fig. 2(a–f) (the load-bearing
> benchmark panel — read at 220 dpi), and the page-level layout of Figs. 3–4 and S1–S9. **Figure-curve
> numbers are flagged as figure-reads;** all scaling-fit constants, parameter values, and runtimes are
> taken from the **stated text/captions**, not pixel extraction. Epistemic tags: **[paper]** =
> stated/derived in the paper; **[twin]** = our application/inference for `qec_twin` (not the paper's
> claim).

## Metadata [paper]

- **Authors / affiliation.** Tong Shen and Daniel A. Lidar, **University of Southern California** (Dept.
  of Electrical & Computer Engineering; Center for Quantum Information Science & Technology; Depts. of
  Chemistry and of Physics & Astronomy). This is the Lidar open-quantum-systems / quantum-annealing
  group — note the heavy self-citation to dynamical-decoupling and Redfield-equation work
  (Tripathi 2022, Ezzell 2023, Mozgunov–Lidar 2020, Brown–Lidar 2025).
- **Venue / status.** arXiv:2502.18929**v2** [quant-ph], dated **10 Sep 2025**; no journal version in this
  cache. Code, scripts, and data are stated to be on GitHub (refs [59], [60]; T. Shen, 2025).
- **Type.** A **classical forward-simulation method** for *open-system, real-time* dynamics of noisy
  quantum circuits: a **density-matrix-based Quantum Monte Carlo (QMC)** that stochastically compresses
  the vectorized density matrix into integer-valued **signed walkers** and evolves them with FCIQMC-style
  population dynamics, with a built-in mechanism to keep the **sign problem** suppressed in real time.
- **Lineage.** A direct generalization of **Full Configuration Interaction QMC (FCIQMC)**
  (Booth–Thom–Alavi 2009 [18]) and its descendants: complex walkers for real-time evolution
  (Guther 2018 [21]/[2-SM]), **density-matrix** walker dynamics (Blunt 2014 [19]/[3-SM]), and **Liouvillian**
  walker evolution for open systems (Nagy–Savona 2018 [22]/[4-SM]). The new ingredients are (i) full
  *time-dependent* open-system real-time dynamics, (ii) **dynamic** (real-time) sign cancellation rather
  than end-of-run cancellation, and (iii) exploiting trace preservation to fix the diagonal walker count
  and thereby remove FCIQMC's population-control bias.

## TL;DR [paper]

The paper column-vectorizes the `D×D` density matrix to a superket `|ρ(t)⟩⟩ = vec[ρ(t)]` (`D = 2ⁿ`) and
rewrites the master equation as `d/dt|ρ⟩⟩ = L(t)|ρ⟩⟩` with the Liouvillian superoperator `L(t)` (Eq. 2). It
then represents `|ρ⟩⟩` **stochastically** by a finite set of integer-valued **signed walkers** living on
computational-basis dyads `|i,j⟩⟩ = vec(|i⟩⟨j|)`, each carrying a complex sign
`sₐ ∈ {1, −1, +i, −i}` (Eq. 3). The walkers are propagated by an FCIQMC-style **spawn → annihilation**
loop: each occupied dyad spawns walkers onto `L`-connected dyads (binomial count Eq. S8/S9, multinomial
destination Eq. S10, sign inherited from the sign of the relevant real/imaginary `L`-matrix element), then
**opposite-sign walkers on the same dyad annihilate in real time** (End Matter; Algorithm 1). Two design
choices make this work: **(1)** the noisy circuit's density matrix becomes **pseudo-sparse** in the
computational basis (off-diagonals decay under relaxation/dephasing), so the occupied subspace has
dimension `O(λD)` with `λ ≪ 1` and only `O(nλD)` Liouvillian entries are ever touched; **(2)** because the
Liouvillian is trace-preserving (`Tr[L|ρ⟩⟩] = 0`), the **number of diagonal walkers `N_diag` is a conserved
constant** — so a single control parameter `N_diag` sets the precision (error `∝ 1/N_diag`, Eq. 6 / S23),
the dynamic annihilation suppresses the sign problem **continuously** (no accumulation), and FCIQMC's
heuristic population control (and its bias) is eliminated. Benchmarked on a **10-qubit XX
dynamical-decoupling crosstalk-suppression circuit** and **n-qubit GHZ preparation**, QMC beats QuTiP's
improved quantum-trajectory (QT) method by **>10× (dense `|+⟩ₙ`) to ~100× (sparse `|W⟩ₙ`)** in runtime at
matched precision, reaches **n = 30** where QT is memory-bound at **n = 16**, and — uniquely — **converges
to the exact solution in the non-Markovian regime** (negative jump rates, Redfield equation) where QT
diverges (Fig. 3). The headline scaling is an **effective subspace `dim(H_QMC) = O(λD)` growing as
`O(1.210ⁿ)` (DD) / `O(1.278ⁿ)` (GHZ)** vs the `2ⁿ` density-matrix wall, projecting 50-qubit runs at
~560 GB / ~80 GB RAM (Fig. 2f; Supp. S5).

## Contributions (claim → evidence → strength) [paper]

- **C1 — A real-time, density-matrix QMC for open systems with time-dependent Hamiltonians.** Extends
  FCIQMC walker dynamics from imaginary-time / time-independent / closed settings to **real-time,
  time-dependent, open** dynamics of the *full* density matrix. *Evidence:* the vectorized master equation
  (Eq. 1→2), the signed-walker representation (Eq. 3), Algorithm 1, and the unbiasedness proof of the
  spawning step (Supp. Eqs. S1–S12, `E[∆N|N] = ∆t·L|N⟩⟩`). The authors claim it is, to their knowledge,
  **the only current QMC able to simulate noisy circuits with time-dependent Hamiltonians** (End Matter,
  modulo one impurity-model exception [58]). *Strength: strong — this is the method.*
- **C2 — Real-time ("dynamic") sign-problem suppression via continuous annihilation + conserved `N_diag`.**
  The sign problem (from non-stoquastic Hamiltonians [29–32] and coherent evolution [33]) is controlled by
  **annihilating opposite-sign walkers every step**, and by exploiting `Tr[L|ρ⟩⟩]=0` to hold `N_diag`
  fixed, which **eliminates FCIQMC's population-control bias** [24]. *Evidence:* End Matter on
  sign-problem suppression; Fig. 4 (the diagonal phase angle `θ = arctan[Im(N_diag)/Re(N_diag)]` stays
  **below 0.02** and `Re(N_diag)` stays flat for `|+⟩₁₀, |W⟩₁₀, |GHZ⟩₁₀`); Supp. S2–S3 (Hermiticity and
  positivity improve monotonically with `N_diag`; Figs. S2–S3). *Strength: strong, but empirical —* the
  "suppression" is a controlled-by-`N_diag` numerical effect, not a proof that the sign problem is gone;
  Eq. 6/S23 bounds the *variance*, not the sign-cancellation efficiency directly. *(Phase-angle numbers
  are figure-reads, Fig. 4 / S2.)*
- **C3 — Pseudo-sparsity → `O(λD)` memory, with an unbiased over-truncation argument.** Noisy circuits make
  `ρ` pseudo-sparse; stochastic compression + the FCIQMC **initiator** truncation (`ξ = 0.1%`) confine the
  operative subspace to `O(λD)` while **averaging over samples keeps the bias minimal**. *Evidence:* the
  `O(nλD)` storage count (main text, p.2); the Liouvillian sparsity bound `‖L‖₀ = O(nD²)` so its *density*
  is `O(1/D²) = O(4⁻ⁿ)` (Supp. Eqs. S26–S28); the truncation study Fig. S4 (trace-norm distance vs `ξ`,
  showing averaging mitigates over-truncation) and the inferred `λ = 10⁻⁸–10⁻¹⁰` at n≈50.
  *Strength: strong for the studied circuits; **the pseudo-sparsity premise is the load-bearing
  assumption** and is circuit/noise-dependent (see W3).*
- **C4 — Order-of-magnitude speedup + system-size reach over QT at matched precision.** *Evidence:*
  Fig. 2(a) inset (QMC error bars **≈10× smaller** than QT at comparable runtime, `|+⟩₁₀`); Fig. 2(b)
  runtime-vs-n (**>10× speedup for the worst case `|+⟩ₙ`**, ~**100× for `|W⟩ₙ`**); Fig. 2(d–e) (QMC
  reaches **n = 30** via replica aggregation; **QT memory-bound at n = 16**); Fig. 2(f) effective-subspace
  scaling `O(1.210ⁿ)/O(1.278ⁿ)`. *Strength: strong, but the comparison is QMC-vs-QT only* (no comparison
  to tensor-network methods, and QT runtimes for large n are *extrapolated* from the
  `O(N_traj^{-1/2})` error law, not measured — main text p.3–4). *(Speedup ratios are stated in text;
  the n-scaling exponents are stated fit constants.)*
- **C5 — Convergence in the non-Markovian (CP-violating, negative-rate) regime where QT fails.**
  *Evidence:* Fig. 3 — two qubits coupled to a shared bosonic bath, Born–Markov + Redfield (Eq. 5) with
  rates `λ₁ = −0.5178 < 0`, `λ₂ = 3.0178`; QMC tracks the exact diagonal populations `ρ̃₀₀, ρ̃₁₁, ρ̃₂₂`
  with a **single 10⁶-walker sample**, while QT (QuTiP influence-martingale method [51]) is accurate only
  at short times and its trace **deviates from 1** as evolution proceeds; off-diagonals in Supp. Fig. S8
  tell the same story. *Strength: strong as a qualitative demonstration; the model is a single
  small 2-qubit/3-level Redfield example, not a sweep.*
- **C6 — A single-knob error model with an explicit `O(1/N_diag)` convergence bound.** *Evidence:*
  Eq. 6 / Supp. Eq. S23: `E[‖ϵ_t‖₂² | |N⟩⟩] ≤ 2N_tot/(N_diag)² · Λ(t)`, with
  `Λ(t) = max_α (∆t)²·‖col_α[L]‖₀·‖col_α[L]‖₂² + ¼`; the rate is `O(1/N_diag)` when `N_diag ~ N_tot` and
  `Λ` is bounded; numerically verified linear-in-`(N_diag)⁻¹` error in Fig. S1 (r²≈0.97–0.997).
  *Strength: strong — a clean, proven variance bound;* note it is a **per-step conditional** bound that
  requires `N_diag` to stay constant (it degrades if `N_diag` drifts, Fig. S1's fifth point).

---

## Method (deep) [paper]

### 1. Vectorization and the Liouvillian (Eqs. 1–2)
The time-local master equation is
`dρ/dt = −i[H(t), ρ] + ½ Σ_k γ_k(t) D[L_k]ρ`, with `D[L]ρ = 2LρL† − {L†L, ρ}` (Eq. 1). Positive rates
`γ_k ≥ 0` give the GKSL/Lindblad (Markovian) generator; **negative rates `γ_k < 0` encode non-Markovian
dynamics** [7]. Column-vectorizing (`vec`, with Roth's relation [27]) yields
`d/dt|ρ⟩⟩ = L(t)|ρ⟩⟩` where (Eq. 2)

`L(t) = −iI⊗H(t) + iHᵀ(t)⊗I + ½ Σ_k γ_k(t)(2L_k⊗L̄_k − I⊗L_k†L_k − L_k†L_kᵀ⊗I)`.

`L` is `D²×D²`, but **only the columns over occupied dyads** are ever stored, each with `O(n)` nonzeros
(main text; Supp. S26–S28 prove `‖L‖₀ = O(nD²)`, i.e. density `O(4⁻ⁿ)`).

### 2. Signed integer walkers (Eq. 3) — the FCIQMC representation, generalized
The superket is represented by `N_tot` walkers, the `α`th being `w_α = sₐ·loc_α` with
**`loc_α = |i,j⟩⟩ = vec(|i⟩⊗|j⟩)`** the dyad it sits on and **`sₐ ∈ {1, −1, +i, −i}`** a *complex* sign
(real walkers à la Booth, extended to complex by Guther for real-time evolution). The population vector
`|N(t)⟩⟩ = Σ_α w_α^{(t)}` (integer-valued per dyad) maps to the physical superket by an ensemble average
(Eq. 3):

`|ρ(t)⟩⟩ ≈ (1/n_sample) Σ_i (1/N_diag) |N^{(i)}(t)⟩⟩`,

where **`N_diag ≡ Σ_{α: loc_α ∈ {|i,i⟩⟩}} w_α`** is the (signed) count of **diagonal** walkers. Because
`Tr[L|ρ⟩⟩]=0`, `N_diag` is **time-independent**; the simulation is initialized by distributing walkers to
match `|N(0)⟩⟩ := N_diag·|ρ(0)⟩⟩`, so **`N_diag` is the single precision/cost knob** (larger ⇒ smaller
statistical error and more RAM/time). The crux distinction from prior FCIQMC: this is **density-matrix
walkers on dyads**, evolved by the **Liouvillian**, in **real time**, with **time-dependent** `H(t)`.

### 3. Spawn → annihilation population dynamics (End Matter; Supp. S1, Algorithm 1)
One Euler step `|∆ρ⟩⟩ ≈ ∆t·L(t)|ρ⟩⟩` is realized stochastically (the paper actually uses the **2nd-order
Adams–Bashforth (AB2)** solver — `|ρ(t+2∆t)⟩⟩ ≈ |ρ(t+∆t)⟩⟩ + ∆t[(3/2)L(t+∆t)|ρ(t+∆t)⟩⟩ − (½)L(t)|ρ(t)⟩⟩]`
— at double memory/time, because first-order Euler has too much time-step error in real-time open-system
runs; End Matter on methodology):

- **Spawn (state-based scheme, the efficient one).** For each occupied dyad `|i,j⟩⟩` with `N_ij` walkers,
  draw the number of spawned walkers from a **binomial** `N_ij^sp ∼ B(N_ij, p_ij^sp)` with
  `p_ij^sp = ∆t·Σ_{kl}(|Re L_ij^{kl}| + |Im L_ij^{kl}|)` (Eqs. S8–S9), then distribute them over connected
  dyads `|k,l⟩⟩` by a **multinomial** with `p_{ij→(kl,c)} ∝ |c(L_ij^{kl})|`, `c∈{Re,Im}` (Eq. S10). Each
  spawned walker's **sign is inherited from the sign of the chosen real/imaginary `L` element**: real
  channel ⇒ `s_ij·sgn(Re L_ij^{kl})`, imaginary channel ⇒ `i·s_ij·sgn(Im L_ij^{kl})`. The expectation
  reproduces `∆t·L|N⟩⟩` exactly (Supp. S5/S7/S11–S12), so spawning is **unbiased**.
- **Annihilation (the sign-problem step).** Merge spawned walkers into the population; **pairs on the same
  dyad with opposite signs (`±1` or `±i`) cancel**. The total walker count therefore does **not** add
  simply (`N_tot(t+∆t) ≠ N_tot^sp + N_tot`). The diagonal count is re-formed from the diagonal-dyad
  spawned walkers (real + imaginary parts), and `N_diag` is monitored.

### 4. How the sign problem is suppressed (End Matter on sign-problem suppression; Supp. S2–S3)
The sign problem appears because both the coherent term (`±i` from `H`) and non-stoquastic structure give
`L` **mixed-sign / complex** matrix elements, so walkers of both signs/phases populate the same dyads;
naive averaging of large cancelling populations blows up the variance. The paper's three interlocking
defenses:

1. **Dynamic cancellation.** Opposite-sign walkers are annihilated **every step** (not deferred to the
   end as in conventional QMC), preventing the **accumulation** of sign error over the trajectory.
2. **Conserved `N_diag` from trace preservation.** A physical `ρ` is Hermitian, so any imaginary part of
   `N_diag` is a pure sign-problem artifact. Holding `N_diag` fixed (large) makes annihilation of
   opposite-sign walkers efficient and keeps `Tr[ρ_QMC] ≈ 1` **without heuristic population control** —
   removing the **population-control bias** that plagues FCIQMC [24]. Diagnostic: `θ = arctan[Im(N_diag)/
   Re(N_diag)]` (Fig. 4 keeps `θ < 0.02`; Supp. Fig. S2 shows small `N_diag` breaks this).
3. **Sufficiently large `N_diag`.** Supp. S3 shows that as `N_diag` grows, the QMC `ρ` approaches a
   **positive-semidefinite, Hermitian** matrix (Frobenius distances to Hermitian and to `ρ_exact` shrink,
   Fig. S3), so `N_diag` simultaneously controls statistical error, Hermiticity, and positivity — a single
   monitorable knob (the cost-free check is "does `N_diag(t)` stay near `N_diag(0)`?").

The **bias-elimination** is the conceptual advance over FCIQMC: trace preservation gives a *physical*
conserved quantity to anchor the population, so no ad-hoc shift/population-control loop (and its bias) is
needed.

### 5. Pseudo-sparsity, `O(λD)` truncation, and the unbiased over-truncation argument (main text; Supp. S4)
An open-system `ρ(t)` under a noisy circuit **becomes pseudo-sparse in the computational basis** because
off-diagonals decay under relaxation/dephasing. The method exploits this two ways: (a) **stochastic
compression** — only occupied dyads carry walkers, so storage is `O(nλD)`; (b) **moderate
over-truncation** — even in the transient regime where coherence has *not* fully decayed (decoherence time
> circuit duration), one can **deliberately over-truncate** the occupied subspace to `O(λD)`, `λ ≪ 1`, and
**recover the bias by averaging over samples** ("unbiased upon averaging", main text; the multi-sample
average of over-truncated runs converges, Fig. S4 inset blue vs green). Numerically this is the FCIQMC
**initiator approximation** (Algorithm 2): a dyad with `N_ij ≤ ξ·N_diag` is a "non-initiator" and may
**not** spawn into *unoccupied* dyads; `ξ = 0.1%` is the chosen sweet spot (Fig. S4). The Liouvillian's own
exponential sparsity (`O(4⁻ⁿ)` density, Supp. S28) guarantees that, in the compressed subspace, the
incremental vector stays sparse.

### 6. Markovian vs non-Markovian handling (main text; End Matter on Redfield)
- **Markovian:** `γ_k ≥ 0`, standard GKSL `L` (Eq. 2). Benchmark Hamiltonian:
  `H_S = −ω_q Σ_i σ_i^z + J Σ_{⟨i,j⟩} σ_i^z σ_j^z` (uniform freq + always-on ZZ crosstalk), with local
  **amplitude damping `L_k = σ_k^−`** and **dephasing `L_k = σ_k^z`**, `T₁ = 100 µs, T₂ = 50 µs`,
  `ω_q = 5 GHz, J = 100 kHz`; rotating frame + RWA, square pulses (10 ns 1-qubit, 50 ns 2-qubit).
- **Non-Markovian:** `γ_k` can be **negative** (Eq. 5 Redfield, derived from a 2-qubit-plus-bosonic-bath
  model via Born–Markov + rate-matrix diagonalization). QMC handles this **with no change** — it evolves
  `|ρ⟩⟩` under whatever `L` is supplied and never needs jump probabilities to be non-negative. This is the
  structural reason QT fails here (QT needs Born-positive jump rates) and QMC does not (Sec. "Non-Markovian
  dynamics"; Fig. 3).

### 7. Replica aggregation (Eq. 4) — extending `n` without extra RAM
Because evolution is trace-preserving, **independent replicas can be averaged**:
`|ρ_QMC⟩⟩ = (1/n_sample) (1/N_eff^diag) Σ_i Σ_j |N^{(i,j)}⟩⟩` with `N_eff^diag = r·N_diag` (Eq. 4). `r`
memory-light replicas at per-replica `N_diag` give an unbiased estimator with **`r×` the effective sample
size (error `∝ (N_eff^diag)^{-1/2}`) at no increase in per-replica RAM** — this is what pushes the
benchmarks from `n=10` (exactly checkable) to `n=30`.

### Cost / complexity and error/bias controls [paper]
- **Memory:** `O(nλD)` per replica (vs `O(D²)=O(4ⁿ)` for direct density-matrix integration, which caps at
  `n≈10`; vs `O(D)=O(2ⁿ)` for QT state vectors). Empirically `dim(H_QMC) = O(λD)` with fitted
  `dim(H_QMC) ≈ C·e^{βn}(N_diag)^γ`, `(β,γ) = (0.208, 0.721)` (DD `|+⟩`) / `(0.130, 0.425)` (GHZ); read as
  `O(1.210ⁿ)` / `O(1.278ⁿ)` (Fig. 2f; Supp. S5, Fig. S6). Projected 50-qubit: `dim(H_QMC) ≈ 3.5×10⁷`
  (DD) → **~560 GB**, `≈ 4.9×10⁶` (GHZ) → **~80 GB** (64 GB ↔ ~4×10⁶ states). Inferred `λ = 10⁻⁸–10⁻¹⁰`.
- **Statistical error:** `O(1/N_diag)` (Eq. 6 / S23), i.e. `‖ϵ_t‖₂² ≤ 2N_tot/(N_diag)²·Λ(t)`; verified
  linear in `(N_diag)⁻¹` (Fig. S1). The bound is **per-step conditional** and assumes `N_diag` constant.
- **Bias controls:** spawning is provably unbiased (S12); annihilation is exact; the **initiator
  truncation `ξ=0.1%`** introduces only a bias that **extrapolates to 0 as `ξ→0`** (End Matter; Fig. S4).
  **Population-control bias is eliminated** by the conserved-`N_diag` trick (the explicit improvement over
  FCIQMC). Hermiticity/positivity are not enforced but **converge with `N_diag`** (Supp. S3).
- **Time-stepping:** AB2 (not Euler) to control real-time open-system time-step error (2× cost).
- **Validity / failure modes:** requires `N_diag` large enough that `N_diag(t)` does not drift (else trace
  preservation and the `O(1/N_diag)` rate break, Fig. S1/S2); requires the circuit to be **pseudo-sparse**
  (the dense, maximally-coherent `|+⟩ₙ` case is the *worst* case and needs a basis change to the Pauli-X
  basis to be sparse at all — Supp. S6 Eq. S30); **measurement of a *global* observable "uncompresses"
  `|N⟩⟩` and destroys the memory advantage** — only *local* observables (fidelity, stabilizers) are cheap
  (Supp. S1).

---

## Key results, figures and tables [paper]

> No numbered tables; all results are figures. Numbers below are **stated text/caption values** unless
> flagged as a figure-read.

- **Fig. 1 — algorithm + circuits.** (a) Schematic: a pseudo-sparse `|ρ⟩⟩` is stochastically compressed by
  averaging integer population vectors; (b) the sparse `L(t)` acts only on columns matching nonzero
  walker entries, keeping `|∆N⟩⟩` sparse; **(c)** the **staggered XX dynamical-decoupling** crosstalk-
  suppression circuit; **(d)** the **n-qubit GHZ-preparation** circuit (each dashed box = one CNOT,
  realized as `Rz(−π/2)⊗Rx(−π/2)` then `Rzx(π/2)`, Supp. S6). *(Circuit identities confirmed by visual
  read of page 1/2.)*
- **Fig. 2 — the benchmark panel (the load-bearing figure; read at 220 dpi).**
  - **(a)** Fidelity of `|+⟩₁₀` and `|W⟩₁₀` under free evolution vs DD over 10⁴ ns; QMC and exact-master-
    equation curves overlap. **Inset:** at matched runtime, **QMC error bars ≈10× smaller than QT**
    (`|+⟩₁₀`: 3 QMC samples `N_diag=10⁶`, 3793 s vs **5800 QT trajectories, 4013 s**; `|W⟩₁₀`: 4 samples
    `N_diag=5×10⁶`, 677 s vs **1200 QT trajectories, 765 s**). *(≈10× is a stated caption value.)*
  - **(b)** Runtime vs `n` under DD (5×10³ ns): QMC ~flat, QT steep; **for the worst case `|+⟩ₙ`, QMC is
    >10× faster than QT's best-case**, and **~100× for the sparser `|W⟩ₙ`** (QT cannot exploit pseudo-
    sparsity). *(QT large-n runtimes are extrapolated via `O(N_traj^{-1/2})`, text p.3–4.)*
  - **(c)** QMC `|+⟩` fidelity at **n = 24, 27, 30** via 5-replica aggregation (`N_diag=2×10⁵ →
    N_eff=10⁶`); inset `Tr(ρ_QMC)` per replica scatters around 1, aggregate closer to 1.
  - **(d)** **30-qubit GHZ** preparation fidelity (5 replicas); CNOT-cycle peaks every 60 ns.
  - **(e)** GHZ runtime vs `n`: QMC **outperforms QT ~100× at large `n`** and reaches **n = 30**, while
    **QT is memory-bound at n = 16**.
  - **(f)** Effective subspace `dim(H_QMC)` vs `n` for both circuits, plotted against `2ⁿ`; fits
    **`O(1.210ⁿ)` (DD) and `O(1.278ⁿ)` (GHZ)** with optimized `N_opt^diag`.
- **Fig. 3 — non-Markovian convergence (the QT-failure demonstration).** Two qubits + shared bosonic bath,
  Redfield (Eq. 5), rates **`λ₁ = −0.5178`, `λ₂ = 3.0178`** (`ω₁=0.25, ω₂=0.5, γ₁=1, γ₂=4, α=3, κ=1`).
  Diagonal elements `ρ̃₀₀, ρ̃₁₁, ρ̃₂₂`: **QMC (single 10⁶-walker sample) tracks the exact solution
  throughout and preserves the trace**, while **QT (QuTiP influence-martingale [51], 10⁴ trajectories) is
  accurate only at short times and its average trace deviates from 1** as `t` grows. Off-diagonals: same
  conclusion (Supp. Fig. S8).
- **Fig. 4 — sign-problem suppression diagnostic.** `N_tot`, `Re(N_diag)`, and `θ` for `|+⟩₁₀, |W⟩₁₀,
  |GHZ⟩₁₀`: `Re(N_diag)` stays flat, **`θ < 0.02`** throughout (effective annihilation). `N_tot` tracks
  coherence — grows for `|+⟩` (noise-induced coherence in the X basis), decays for `|W⟩`, rises during GHZ
  entangling. *(θ bound is a stated caption value.)*
- **Supplement.** S1 Algorithms 1–2 + unbiasedness proofs; S2 error-bound proof (`O(1/N_diag)`, Fig. S1);
  S3 Hermiticity/positivity vs `N_diag` (Figs. S2–S3); S4 truncation/pseudo-sparsity (Fig. S4) +
  Liouvillian sparsity proof `O(4⁻ⁿ)`; S5 Hermiticity-error fits `ϵ ≈ A·e^{αn}(N_diag)^{-1/2}+ϵ_∞`
  (`α=0.0262` DD / `0.0715` GHZ; Figs. S5–S6) → 50-qubit RAM estimates; S6 circuit/pulse details; S7–S8
  more non-Markovian + 16-qubit benchmarks (Figs. S8–S9).

---

## USEFUL FOR OUR PROJECT [twin]

**Framing.** Our non-Pauli SIM-ONLY teacher (memory: *nonpauli-teacher-synthesis*,
*decoder-gate-and-frontier*) injects leakage (`|1⟩→|2⟩` + seepage), T1/T2, coherent over-rotation, and
**coherent leakage *transport*** (CZ-mediated `|21⟩↔|03⟩`) into a d3 XZZX surface code, emitting labeled
`(syndrome, logical)` data, later scaled to d5/d7. We have established (memory + `forward/exact` README):
**(i)** the *exact* d3 engine is a **9-data-qutrit density matrix (5.77 GiB)** — exact only for
**per-qubit-local** leakage; **(ii)** leakage **transport couples data + ancilla**, so the exact object is
the full **17-qutrit state (`3¹⁷×3¹⁷` density matrix, infeasible)** → we accept Monte Carlo. This paper is
relevant on exactly the four axes the brief names. The verdict, axis by axis:

### 1. Does our natural Monte Carlo have a sign problem? — **No. This is the crux, and it is decisive.**

**Our planned MC is quantum-trajectory (Kraus/jump) unraveling of CP, Markovian, positive-rate channels.**
Leakage `|1⟩→|2⟩`, seepage, amplitude damping (T1), dephasing (T2), coherent over-rotation, and the CZ
transport map are **all completely positive with non-negative rates** (they are honest Kraus channels /
GKSL generators). For a CP map `{K_m}`, the jump/trajectory unraveling draws outcome `m` with **Born
probability `p_m = ⟨ψ|K_m†K_m|ψ⟩ ≥ 0`** and applies `K_m|ψ⟩/√p_m`; the channel average reconstructs `ρ`
exactly (this is precisely the Manabe–Suzuki–Darmawan qutrit-MPS recipe, `p_i = Tr(K_i|ψ⟩⟨ψ|K_i†)`,
note `leakage_tensor_network_simulation_2308.08186`, Eq. A9). **Born-positive probabilities ⇒ no sign
problem.** So our pure-state trajectory MC is **sign-problem-free for the entire Markovian leakage/T1/T2/
transport teacher.**

**Reconciling with the paper's "QT struggles when Eq. (1) violates CP."** [paper] That statement is **about
the non-Markovian regime only** — when `γ_k < 0` (Eq. 1/5), the unraveling's effective jump rates go
**negative**, and QuTiP's QT must resort to special tricks (influence martingale [51], or the methods of
[11,49,50]) that fail to converge at long times (Fig. 3). It is **not** a claim that trajectory methods
have a sign problem for ordinary CP/Markovian channels — for those, QT in the paper *agrees with the exact
solution* (Fig. 2a, Fig. S9) and is merely **slower / more memory-hungry** than the new QMC, not wrong. So
our Markovian teacher sits squarely in the regime where **QT is correct and sign-problem-free**; the
paper's CP-violation caveat does not bite us **unless we deliberately add non-Markovian noise** (axis 3).

**The two "sign problems" are different objects — keep them separate.** [twin]
- **Signed-walker / vectorized-`ρ` QMC (this paper).** The sign problem here is intrinsic to **stochastically
  sampling the Liouvillian *superoperator* `L` in a fixed computational basis**: coherent terms put `±i`
  and non-stoquastic structure puts `±` into `L`'s matrix elements (Eqs. 2, S5), so walkers of opposite
  sign land on the same dyad and the **Monte-Carlo *estimator of `ρ`* has cancelling contributions whose
  variance can blow up** (the generic QMC sign problem, Troyer–Wiese [28]). It exists **even for
  CP/Markovian dynamics** (their `|+⟩₁₀` benchmark is Markovian and still shows a nonzero `θ`, Fig. 4) and
  is what their dynamic-annihilation machinery exists to suppress.
- **Pure-state trajectory MC (what we'd use).** No superoperator is sampled; we sample **measurement
  outcomes with Born-positive probabilities** and propagate a **pure state** (`|ψ⟩` or a pure-state MPS).
  There are **no signed walkers, no cancellation, no `N_diag` to conserve** — the only stochasticity is the
  outcome draw, which is a genuine probability. **A CP/Markovian trajectory unraveling cannot have a sign
  problem in this sense**, by construction.

**Net for us:** our default teacher MC (Kraus-jump trajectories of CP channels) is **sign-problem-free**;
the elaborate sign-suppression apparatus that is the entire point of this paper is **machinery we do not
need** for the Markovian rungs. We should *not* reach for signed-walker QMC to dodge a sign problem we do
not have. (Where it *could* matter: see axes 2 and 3.)

### 2. Is this a scaling engine for d3-with-transport (17 qutrits) and d5/d7? — **A candidate, but with two serious qudit caveats; it competes with — and is largely dominated by — the MPS-trajectory route for our use.**

The attractive part [paper→twin]: the `O(λD)` **compressed-density-matrix** representation is exactly a
carrier for the regime where the **QT state vector overflows** — `3¹⁷ ≈ 1.3×10⁸` amplitudes is fine for a
*pure* qutrit state vector (≈2 GB complex128) but the *density matrix* `3¹⁷×3¹⁷` is hopeless, and `3⁴⁹`
(d5-ish data-qutrit counts) overflows even the state vector. Their method **never forms the dense `ρ`** and
rides the **same pseudo-sparsity our noisy syndrome circuits create** (repeated stabilizer measurement +
relaxation collapse off-diagonals — the *same* physics the Manabe MPS paper calls the area law). So in
principle it is a memory-frugal mixed-state carrier where both the dense-`ρ` backend and (for very large
`n`) the QT state vector die.

But three things temper this hard:

- **It is demonstrated on QUBITS, not QUTRITS.** [paper] `D = 2ⁿ` throughout; the dyad basis is
  `{|i,j⟩⟩}`, `i,j ∈ {0,1}`. A **qutrit (qudit) generalization** is *conceptually* immediate — set
  `D = 3ⁿ`, walkers live on `9`-valued single-site dyads, `L` is built from qutrit Lindblads (leakage,
  seepage, transport) — but **nothing in the paper validates it.** The spawn/annihilation arithmetic, the
  `O(4⁻ⁿ)` sparsity bound (Supp. S28, derived for Pauli `σ^±, σ^z`), and the `λ = 10⁻⁸–10⁻¹⁰` sparsity
  estimate are all **qubit-specific** and would have to be re-derived/re-measured for qutrits, where the
  Liouvillian density is `O(9⁻ⁿ)` *naively* but the relevant constant (nonzeros per column, set by the
  qutrit gate + leakage connectivity) is unknown and **leakage/transport actively *fight* pseudo-sparsity**
  by populating `|2⟩` levels and creating data–ancilla correlations.
- **Pseudo-sparsity is the load-bearing premise and is *most* at risk exactly where leakage lives.**
  [twin] The method's whole memory advantage is `dim(H_QMC) = O(λD)`, `λ ≪ 1`. Their own **worst case is
  the maximally-coherent, dense `|+⟩ₙ`** (needs a basis change just to start, Supp. S6). Our teacher
  *injects coherence and transport* — coherent over-rotation and CZ-mediated `|21⟩↔|03⟩` transport
  **create and move off-diagonal weight**, i.e. **reduce sparsity**, precisely the regime where their
  effective subspace inflates. Near threshold (high coherence, slow decay) `λ` could approach `O(1)` and
  the `O(λD)` advantage collapses toward the dense `O(D²)` wall. This is the **same failure mode** flagged
  for the leakage axis in *nonpauli-teacher-synthesis* and for over-truncation here.
- **Comparison to the MPS/PEPS route (the incumbent in our program).** [twin] The paper itself argues
  tensor networks "degrade significantly with growing entanglement … limiting scalability with circuit
  depth" [16] — true for *generic* depth, but **QEC circuits are the special low-entanglement case** where
  area-law MPS is efficient and **bounded-`χ`** (Manabe et al. show qutrit-MPS holds hundreds of qutrits
  over ~100 rounds, `note leakage_tensor_network_simulation_2308.08186`). For **our** problem — *quasi-1D
  d3/d5/d7 surface codes, leakage-native, syndrome output* — the **qutrit-MPS-trajectory engine is the
  better-matched, already-validated carrier**: it is qutrit-native (validated), sign-problem-free
  (Born-positive Kraus sampling), produces syndrome shots directly, and its area-law `χ` is *bounded* by
  the QEC structure rather than relying on computational-basis pseudo-sparsity that leakage erodes. **This
  paper's QMC is qubit-only, not leakage-tailored, and its sparsity premise is weakest in our high-coherence
  regime** — so for the leakage teacher it is, at best, a **secondary / cross-check carrier**, not the
  primary one. Where this paper could still win is **deep-circuit, *high*-entanglement, *Markovian* regimes
  where even area-law MPS `χ` grows** — but that is not where our leakage syndrome data lives.

**Honest verdict (axis 2):** a real but **conditional** scaling option. Adopt it only if (a) we confirm
qutrit pseudo-sparsity survives leakage/transport at our noise levels (an experiment, not a given), and (b)
we accept building the qudit generalization ourselves. For the stated d3/d5/d7 surface-code leakage teacher,
**MPS-trajectory remains the front-runner**; this QMC is a candidate where MPS entanglement growth would
otherwise bite.

### 3. The non-Markovian axis — **Yes: this is the strongest, most differentiated reason to keep this paper on file.**

If/when we inject **correlated / colored / memory noise** — `1/f` flux noise, non-Markovian dephasing,
structured baths — the generator acquires **negative rates `γ_k(t) < 0`** (Eq. 1/5), the dynamics are
**CP-violating** at intermediate times, and **trajectory/jump methods fail** (negative jump probabilities;
QT diverges at long times even with the influence-martingale fix — Fig. 3, Supp. Fig. S8). [paper] This
QMC's signature result is that it **converges to the exact solution in exactly this regime**, with a
*single* sample, because it evolves `|ρ⟩⟩` under the supplied `L` and **never requires Born-positive jump
rates** — its dynamic annihilation handles the resulting sign structure. [twin] **This is the one place
where our default trajectory MC genuinely breaks and this engine genuinely wins.** Concretely: a
non-Markovian *teacher* (colored-noise surface code) is currently outside both our dense-`ρ` backend
(infeasible at scale) and a naive QT unraveling (CP-violating); **signed-walker QMC is a principled carrier
for it.** Caveat: the paper's non-Markovian demo is a **single 2-qubit/3-level Redfield example**, and it
needs the master equation `L(t)` *constructed* (diagonalizing the system Hamiltonian / building the memory
kernel is itself a bottleneck at large `n`, acknowledged in the End Matter, with a kernel-approximation
escape hatch [63]). So this is a **future-axis** tool: file it as the engine for the *correlated/memory*
rung, not the leakage rung.

### 4. Certification — **Yes, our exact 9-data-qutrit density matrix is the right oracle, with caveats.**

[twin] In the **per-qubit-local** limit (no transport), the exact d3 object is the **9-data-qutrit density
matrix (5.77 GiB)** we already own — and it is exactly the **mixed-state oracle** to certify *any*
stochastic teacher (a qutrit-MPS-trajectory engine, **or** a qudit-generalized version of this QMC) in that
limit: run the exact `ρ_exact(t)`, run the MC, compare **`‖ρ_MC − ρ_exact‖`** (trace-norm or Frobenius) and
the **syndrome/observable distributions**, and verify the MC error follows its claimed rate. This paper
**hands us the certification protocol verbatim**: their entire validation is "MC vs `ρ_exact` at the
largest exactly-solvable size" — trace-norm distance `T(ρ,σ)=½‖ρ−σ‖₁` (Supp. S4), Frobenius
`‖ρ_QMC − ρ_exact‖_F` and Hermiticity `‖ρ_QMC − ρ_QMC†‖_F` vs walker number (Figs. S3–S4), and the
`O(1/N_diag)` error fit (Fig. S1). We can reuse these **exactly** as the oracle-cross-check metrics, which
is also the rigorous version of the *self-consistency* check the Manabe MPS paper lacks (note W3 there).
**Two caveats:** (a) the oracle certifies only the **local** limit — the **transport** regime (the actual
reason we accept MC) has **no feasible exact oracle** (`3¹⁷`), so certification there must be indirect
(certify the engine locally, then trust it with transport, exactly as we accept the MPS engine); (b)
certification is **forward-fidelity only** — it bounds how well the MC reproduces `ρ`/syndromes, not
whether downstream *channel recovery* is identifiable (a separate axis, memory
*coherence-not-identifiable-syndrome-only*).

---

## What does NOT apply / limitations [paper + twin]

- **[paper] Qubits, not qutrits.** Every construction, sparsity bound (`O(4⁻ⁿ)`, Supp. S28), and the
  `λ=10⁻⁸–10⁻¹⁰` estimate is qubit-specific. **[twin] Our teacher is qutrit-native (leakage `|2⟩`);** a
  qudit port is unvalidated and the controlling constants (nonzeros/column, achievable `λ`) are unknown for
  leakage/transport Liouvillians.
- **[paper] Not QEC / leakage-tailored.** The circuits are **DD crosstalk suppression** and **GHZ
  preparation**; there is **no stabilizer code, no syndrome extraction, no decoder, no logical error
  rate**. The only QEC contact is a passing remark that local stabilizer expectations are cheap to measure
  (Supp. S1) and an aspirational mention in the conclusion. **[twin] It does not, as shipped, produce the
  `(syndrome, logical)` records our teacher must emit** — that pipeline (rounds of ancilla measurement,
  syndrome logging, MWPM/TN decode) would have to be built on top, unlike the Manabe MPS paper which
  produces syndrome shots natively.
- **[twin] The pseudo-sparsity premise is weakest exactly where our signal lives.** Sparsity comes from
  off-diagonal decay under relaxation/dephasing; **our coherent over-rotation + leakage transport *add*
  off-diagonal/coherent weight**, and **near threshold** (high coherence, slow decay) `λ→O(1)` and the
  `O(λD)` memory advantage degrades toward the dense wall. The paper's *own* worst case (dense `|+⟩ₙ`)
  warns of this.
- **[paper] Sign suppression is empirical, controlled by `N_diag`, not proven absent.** Eq. 6/S23 bounds
  the *variance*; the sign cancellation's efficiency is monitored (`θ<0.02`, Fig. 4) and improves with
  `N_diag`, but there is **no theorem that the sign problem stays benign as `n` grows** — and the sign
  problem is, in general, the reason QMC is hard. For a high-coherence qutrit leakage Liouvillian the
  required `N_diag` (hence cost) is unknown and could be large.
- **[paper] Global observables uncompress the state.** Only **local** observables keep the memory
  advantage (Supp. S1). **[twin] Multi-round syndrome histories are local** (stabilizers) — favorable —
  but any *global* logical-observable or full-distribution readout would forfeit the speedup.
- **[paper] QT comparison is the only baseline, and partly extrapolated.** No comparison to tensor-network
  methods (the natural QEC competitor); large-`n` QT runtimes are **extrapolated** from the
  `O(N_traj^{-1/2})` law rather than measured (text p.3–4). **[twin] The headline 10–100× is QMC-vs-QT,
  not QMC-vs-MPS** — and MPS is our incumbent carrier, so this paper does *not* establish QMC as the best
  engine for *our* problem.
- **[paper] Non-Markovian demo is a single small example;** building `L(t)` (diagonalizing `H`, the memory
  kernel) is itself a large-`n` bottleneck (End Matter on Redfield), with only a cited approximate escape
  [63].
- **[twin] Forward simulator only — not a learner.** Like the other teacher-side papers, it `recover`s
  nothing: it forward-evolves a *known* `L`. It contributes to the **teacher / `forward`** axis only, and
  says nothing about channel identifiability from syndromes.

## How to use / trust + open questions [twin]

- **Cite for:** (a) **the crux clarification** — that the "sign problem" of signed-walker / vectorized-`ρ`
  QMC is a *distinct object* from a pure-state trajectory unraveling, and that **CP/Markovian Kraus-jump
  trajectories (our teacher) are sign-problem-free** because jump probabilities are Born-positive; (b) the
  **non-Markovian carrier** — the engine of record for a future *correlated/colored-noise* teacher where QT
  fails (Fig. 3); (c) the **certification protocol** — trace-norm / Frobenius / `O(1/N_diag)` MC-vs-`ρ_exact`
  checks (Figs. S1, S3, S4) we should reuse against our exact 9-data-qutrit oracle; (d) the
  **conserved-`N_diag` / population-control-bias-elimination** trick as a clean idea if we ever do build a
  density-matrix walker engine.
- **Do NOT cite as:** a QEC/leakage simulation method (it has none); a qutrit method (it is qubit-only); a
  proof that trajectory MC has a sign problem for CP channels (it does not say that); the best scaling
  engine for *our* d3/d5/d7 leakage teacher (that is the qutrit-MPS-trajectory route, here at best a
  secondary carrier); or a method with a certified large-`n` sign-problem bound.
- **Adopt for us:** (i) **keep our default teacher MC as Kraus-jump trajectories of CP channels** — no sign
  problem, no walker machinery; (ii) reserve **signed-walker QMC for the non-Markovian rung** if we add
  memory noise; (iii) reuse their **MC-vs-`ρ_exact` certification metrics** at d3-local against our exact
  qutrit backend; (iv) **before** treating this as a scaling carrier, run the gating experiment: *does
  qutrit pseudo-sparsity (`λ`) survive leakage + transport at our noise levels?* — if `λ→O(1)`, abandon it
  for MPS.
- **Open questions.** (1) What is the **achievable `λ` for a qutrit leakage/transport Liouvillian**, and
  does it stay `≪1` near threshold (where coherence is high)? (2) Does the conserved-`N_diag` trick survive
  a **qutrit, leakage-inflated** Liouvillian, or does the required `N_diag` explode? (3) For a **colored-
  noise surface-code teacher**, is signed-walker QMC cheaper than building and integrating the full memory
  kernel? (4) Could a **hybrid** help — pure-state qutrit-MPS-trajectory for the CP/Markovian leakage rung,
  signed-walker `ρ`-QMC only for the non-Markovian rung — sharing the same exact-oracle certification?
