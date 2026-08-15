# Full-text review — Coupled Lindblad pseudomode theory (arXiv:2506.10308)

> **Provenance (2026-06-30): FULL-TEXT read (CERTIFICATE-GRADE 精读).** PDF `outputs/papers/2506.10308.pdf` -> txt
> `outputs/papers/2506.10308.txt` (PyMuPDF, 11 pages = 6-page Letter + 5-page Supplemental Material, arXiv
> v2, 26 Mar 2026). All section/equation/figure/table references from that text. Figures not pixel-extracted:
> figure facts = captions + numbers stated in text. Published as PRL 136, 090403 (2026).

---

## Metadata [paper]

- **Title.** Coupled Lindblad pseudomode theory for simulating open quantum systems.
- **Authors.** Zhen Huang (UC Berkeley, Math), Gunhee Park (Caltech, EAS), Garnet Kin-Lic Chan (Caltech, Chemistry),
  Lin Lin (UC Berkeley Math + LBNL Applied Math). Corresponding: linlin@math.berkeley.edu.
- **Venue / status.** arXiv:2506.10308v2 [quant-ph], 26 Mar 2026; published PRL 136, 090403 (2026).
- **Extent.** 6-page Letter + 5-page Supplemental Material (SM). 65 references.
- **Type.** Theory + numerical demonstration. No hardware experiment.
- **Extraction.** PyMuPDF -> txt. SM sections S1--S7 fully extracted.

---

## Executive summary [paper]

**Core problem.** Simulate the reduced dynamics of a system linearly coupled to a Gaussian (bosonic/fermionic)
bath using a finite number of auxiliary pseudomodes. Two requirements: (1) *efficiency* -- few modes;
(2) *physicality* -- the enlarged dynamics is a CPTP quantum channel (stable classically, realizable on
quantum hardware).

**Prior trade-off.** Unitary-mode and Lorentzian-pseudomode representations are CPTP but require `poly(T/epsilon)`
modes. Quasi-Lindblad and non-Hermitian pseudomodes achieve `polylog(T/epsilon)` but are NOT completely positive
(not a valid quantum channel; numerically unstable, realizable only with an exponentially large T-dependent
subnormalization on quantum hardware). Coupled Lindblad pseudomodes (dense `H`, dense `Gamma >= 0` coupling the
modes to each other) are CPTP, but their asymptotic scaling was previously unknown and their construction relied
on non-convex optimization.

**Two contributions of this Letter.**
1. **Theorem 1** (Eq. 6--7): A gauge transformation maps any quasi-Lindblad BCF to a coupled-Lindblad BCF with the
   **same number of modes `N`** whenever a semidefinite **feasibility condition** (Eq. 7) holds. Consequently the
   `polylog(T/epsilon)` scaling of quasi-Lindblad transfers to coupled-Lindblad, now with CPTP.
2. **Robust SDP construction** (Eq. 8): Avoids the non-convex optimization of prior coupled-Lindblad work.
   An alternative frequency-domain realization-based construction is given in SM Section S1.

**Numerical headline.** `N = O(log T)` at fixed `epsilon = 1e-6` (Fig. 1a). Spin-boson ultra-strong-coupling
population dynamics accurate with `N = 4` vs `N = 10` of prior state-of-the-art (Lednev et al. PRL 132 (2024),
Fig. 2). Dimer absorption spectra captured with `N = 3` coupled modes for two very different spectral
densities, at 0 K and 77 K (Fig. 3). Fermionic Anderson impurity model with `N = 2, 4` per spin (SM Fig. S1).
Sub-Ohmic spectral density `J(omega) = omega^{1/2} e^{-omega}` with same `polylog` scaling and `N = 4` accuracy
despite the omega=0 singularity (SM Fig. S3).

---

## Model setup [paper, verbatim]

### The spin-boson Hamiltonian

The total Hamiltonian (Eq. 1 context):

```
H = H_S + H_B + H_SB
H_B = integral_0^infty omega b_dagger_omega b_omega domega
H_SB = S B                         (S, B Hermitian)
B = integral_0^infty sqrt(J(omega)) (b_omega + b_dagger_omega) domega
```

- `b_omega` = bosonic annihilation operator.
- `J(omega)` = spectral density.
- Factorized initial state `rho(0) = rho_S(0) otimes rho_B(0)`, where `rho_B(0)` is the thermal equilibrium state of `H_B`.

### The bath correlation function (BCF) -- the reduction target

Eq. 1:
```
C(t) = tr[ B(t) B(0) rho_B(0) ],   B(t) = e^{i H_B t} B e^{-i H_B t}.
```

**Key fact** (citing Tamascelli et al. PRL 120, 030402 (2018), ref [5]): For fixed `H_S, S, rho_S(0)`, the
BCF `C(t)` on `[0, T]` uniquely determines the reduced system dynamics `rho_S(t)` up to time `T`. The entire
approximation problem therefore reduces to **fitting the BCF** by a finite-mode surrogate whose own BCF
matches `C(t)` on `[0, T]` to precision `epsilon`.

---

## Core theorems and constructions [paper, verbatim equation references]

### 1. Coupled-Lindblad pseudomode dynamics (Eq. 2) -- the CPTP embedding

Introduce `N` auxiliary bosonic modes `A` initialized in **vacuum**: `rho_A(0) = |0><0|`. The joint
system+pseudomode density operator `rho^c_SA(t)` obeys a genuine GKSL Lindblad master equation:

```
d/dt rho^c_SA = -i[ H_S + H_A + H_SA , rho^c_SA ] + D_A(rho^c_SA)                (Eq. 2)
```

where

```
H_A     = sum_{k,l=1..N} H_{kl} b_dagger_k b_l           (H = H_dagger, i.e. Hermitian)
H_SA    = S A,   A = sum_k g_k b_dagger_k + conj(g_k) b_k   (coupling vector g in C^N)
D_A(*)  = sum_{k,l=1..N} Gamma_{kl} ( 2 b_l * b_dagger_k - { b_dagger_k b_l , * } )
                                                              (Gamma >= 0, positive semidefinite)
```

**Conditions `H = H_dagger` and `Gamma >= 0` are exactly the GKSL conditions => the joint dynamics is CPTP (physical).**
"Coupled" = `H` and `Gamma` may be **dense** (off-diagonal elements couple modes). Lorentzian pseudomode is the
special case where `H` and `Gamma` are diagonal.

The pseudomode BCF (Eq. 3, citing refs [9, 28]):

```
C^c(t) = g_dagger e^{-i K t} g,     K = H - i Gamma        (non-Hermitian effective generator)      (Eq. 3)
```

So `C^c(t)` is a sum of complex exponentials `e^{-i K t}` weighted by `g`. The dissipative part `Gamma`
supplies the **decay** that a finite unitary bath cannot produce.

### 2. Quasi-Lindblad pseudomode (Eq. 4--5) -- efficient but NOT CP

Quasi-Lindblad (Park et al. PRB 110, 195148 (2024), ref [25]) adds a **system-bath dissipator**:

```
D_SA(*) = L_q * S + S * L_q_dagger - 1/2 { S (L_q + L_q_dagger), * }           (Eq. 4)
```

with `L_q = sum_k 2 alpha_k b_k`. With `l_k, r_k = g_k +/- i alpha_k` and **diagonal** `H, Gamma`
(`H_kk = omega_k`, `Gamma_kk = gamma_k`), its BCF (Eq. 5):

```
C^q(t) = sum_{k=1..N} l_k r_k e^{(-i omega_k - gamma_k) t} = l_dagger e^{-i Lambda t} r       (Eq. 5)
```

where `Lambda = diag(omega_k - i gamma_k)`. Setting `l_k = r_k` (alpha=0) recovers the Lorentzian pseudomode
(positive real weights). In general the weights `l_k r_k` are **complex**, which is the extra freedom that
enables `polylog(T/epsilon)` scaling.

**`D_SA` breaks CP** when there is no dissipation acting on the system. Quasi-Lindblad is therefore **not a
quantum channel**; can be numerically unstable (ref [46] notes that "Hamiltonian-induced stability" only
sometimes saves it) and cannot be efficiently realized on quantum hardware (ref [51]: would need an
exponentially large T-dependent subnormalization factor). Under analyticity assumptions on `J(omega)`, the
number of modes is `polylog(T/epsilon)` (citing Thoenniss-Vilkoviskiy-Abanin PRB 112, 155114 (2025), ref [26]).

### 3. Theorem 1 -- the load-bearing result: coupled Lindblad = quasi-Lindblad via a gauge (Eq. 6--7)

**Theorem 1.** Let `rho^c_S(t)` and `rho^q_S(t)` denote the reduced system density operators from the coupled
Lindblad and quasi-Lindblad theory respectively. If the BCFs coincide, then the reduced dynamics are identical:

```
C(t) = C^c(t) = C^q(t)  =>  rho_S(t) = rho^c_S(t) = rho^q_S(t)                  (Eq. 6)
```

Furthermore, if the following **feasibility condition** holds:

```
exists Y >> 0 (positive definite) s.t.
  Y r = l                                          (Hermiticity condition)
  i( Y Lambda - Lambda_dagger Y ) >= 0              (Positivity condition)          (Eq. 7)
```

then there exists a coupled Lindblad BCF `C^c(t)`, with the same number of modes `N` as the quasi-Lindblad
BCF `C^q(t)`, such that `C^c(t) = C^q(t)`.

**Proof sketch.** The gauge transformation:
```
Lambda -> K = X Lambda X^{-1}
l_dagger -> l_dagger X^{-1}
r -> X r
```
with invertible `X` leaves `C^q(t)` invariant. The gauge-transformed BCF takes coupled-Lindblad form iff:
- (a) `g = (l_dagger X^{-1})_dagger = X r` (Hermiticity of the coupling -- ensures `g` is consistent as
  both left and right vector)
- (b) `Gamma = (K_dagger - K)/2i >= 0` (the GKSL positivity of the dissipator)

Introducing `Y = X_dagger X` (positive definite) and multiplying by `X, X_dagger` turns (a) and (b) into the
equality and linear matrix inequality (LMI) constraints of Eq. 7. `X` invertible => `Y >> 0`.

**Consequence.** When Eq. 7 is feasible, `N_{coupled} <= N_{quasi}`, so the `polylog(T/epsilon)` scaling
of quasi-Lindblad transfers to coupled Lindblad, now with CPTP. This is the paper's headline theoretical
contribution.

### 4. Robust SDP construction (Eq. 8) -- avoiding non-convex optimization

When Eq. 7 is not exactly feasible (the generic case), solve the convex least-squares-with-SDP-constraint
problem:

```
min_{Y >> 0}  || l - Y r ||^2_2
subject to   i( Y Lambda - Lambda_dagger Y ) >= 0                                  (Eq. 8)
```

This can be solved efficiently with any standard SDP solver. Then:
1. Set `X = sqrt(Y)` (Cholesky or matrix square root).
2. Recover `K = X Lambda X^{-1}`, `g = X r`.
3. Compute `H = (K + K_dagger)/2`, `Gamma = (K_dagger - K)/(2i) >= 0`.

This replaces the non-convex optimization used in all prior coupled-Lindblad work (refs [27--30]).

### 5. Feasibility condition -- the polylog scaling gate (Eq. 7, restated)

The **two constraints** that determine whether quasi-Lindblad can be converted to coupled Lindblad without
increasing `N`:

1. `Y r = l` -- the Hermiticity condition. Requires that there exists a `Y >> 0` mapping the quasi-Lindblad
   right vector `r` to the left vector `l`. This ensures the coupling vector `g` is consistent.
2. `i(Y Lambda - Lambda_dagger Y) >= 0` -- the positivity condition. Requires that after the gauge transformation,
   the resulting `Gamma` is positive semidefinite, guaranteeing CPTP.

If both hold exactly, the coupled and quasi representations use the **exact same `N`**. If they hold
approximately (Eq. 8 solution yields a small residual `||l - Y r||_2`), the coupled BCF slightly differs from
the quasi BCF but the numerical results show this residual is small (Fig. 1: coupled tracks quasi closely).

### 6. Multi-qubit generalization (SM Section S2, Eq. S2--S4) -- crucial for us

The generalization from single-site to multi-site replaces the coupling **vector** `g in C^N` with a coupling
**matrix** `g in C^{N x n}`:

```
H_SA = sum_{j=1..n} S_j A_j
A_j = sum_{k=1..N} g_{kj} b_dagger_k + conj(g_{kj}) b_k                              (Eq. S2)
```

where `N` = number of pseudomodes, `n` = number of system-coupling terms. The BCF becomes an **n x n matrix**:

```
C^c(t) = g_dagger e^{-i K t} g,   g in C^{N x n},   K = H - i Gamma,   H = H_dagger,   Gamma >= 0   (Eq. S3)
```

The dynamics (Eq. S4):
```
d rho / dt = -i[ H_S + H_A + H_SA, rho ] + D_A(rho)                                       (Eq. S4)
```

This is **critical for our coupled-teacher design**: a **single pseudomode `b_k` couples to MULTIPLE system
operators `S_j` through the shared column-vs-row structure of `g`** -- this is exactly a shared bath
imprinting correlated noise on multiple qubits. The matrix-valued BCF captures cross-correlations between
different `S_j` operators.

### 7. Fermionic extension (SM Section S3, Eq. S5--S8)

For fermionic environments (e.g., Anderson impurity model), we need both **lesser and greater hybridization
functions**:

```
Delta_<(t) = integral J(omega) f^{mu,beta}_{FD}(omega) e^{-i omega t} domega
Delta_>(t) = integral J(omega) (1 - f^{mu,beta}_{FD}(omega)) e^{-i omega t} domega          (Eq. S6)
```

Each is fitted independently with coupled Lindblad parameters:
```
Delta_<(t) ~ Delta^c_<(t) = (g_<)_dagger e^{(-i H_< - Gamma_<) t} g_<
Delta_>(t) ~ Delta^c_>(t) = (g_>)_dagger e^{(-i H_> - Gamma_>) t} g_>                        (Eq. S7)
```

This requires **two independent sets** of pseudomodes (size `N1, N2`), with the enlarged dynamics given by
Eq. S8. Initial state: `rho(0) = rho_S(0) otimes (|1><1|)^{otimes N1} otimes (|0><0|)^{otimes N2}`.

### 8. Frequency-domain realization construction (SM Section S1, Eq. S1)

A second construction method for the case where the BCF is given in the frequency domain. Given `tilde{C}(omega)`
on a frequency grid, seek parameters satisfying:

```
tilde{C}(omega) ~ Im( g_dagger (K - omega I)^{-1} g ),   K = H - i Gamma                    (Eq. S1)
```

**Trick**: Write `tilde{C}(omega) = (1/2i) g_l_dagger (K - omega I)^{-1} g_r` with `g_l = [g; g]`,
`g_r = [g; -g]`, `K = diag(K, K)`. Fit this within the standard **Loewner-matrix** realization framework
(Mayo-Antoulas, ref [42], SVD-based). Then fix the undetermined gauge by an SDP similar to Eq. 7.

This avoids Fourier-transforming the spectral density, which "can introduce additional approximation errors,
particularly when `J(omega)` is only available on a discrete frequency grid with limited accuracy" (SM S1).

---

## Key assumptions [paper, verbatim]

1. **Gaussian bath.** The entire construction assumes the bath is Gaussian -- i.e., linearly coupled bosonic
   continuum (or fermionic Gaussian bath, SM Section S3). The bath's influence is fully captured by the
   2-point BCF (Eq. 1). No non-Gaussian / genuinely anharmonic environments.

2. **Linear coupling.** `H_SB = S B` (or `H_SB = sum_i S_i A_i` in the multi-site case). The system-bath
   coupling operator `S` is Hermitian (bosonic case) or more general (fermionic case involving
   `S B + B_dagger S_dagger`, SM Section S3).

3. **BCF analyticity** (required for the `polylog(T/epsilon)` transfer). The `polylog` bound on quasi-Lindblad
   from ref [26] requires **analyticity conditions on `J(omega)`**. The paper does not restate these in detail
   but inherits them. Practically, the bound applies when the spectral density has a smooth analytic
   continuation away from the real axis.

4. **Factorized initial state.** `rho(0) = rho_S(0) otimes rho_B(0)`. Correlated initial states are not
   treated.

5. **Separability condition (Eq. 7).** For the exact `N`-preserving gauge transformation, the feasibility
   condition Eq. 7 must hold. When it does not hold exactly, the SDP (Eq. 8) minimally violates it and the
   numerics show the residual is small.

---

## Numerical demonstrations [paper, verbatim]

### BCF fitting benchmarks (Fig. 1)

- **Target BCF.** Derived from **Ohmic spectral density** `J(omega) = omega e^{-omega/omega_c}` for
  `omega >= 0` at zero temperature, `omega_c = 1`.
- **Fitting procedure.** First fit `tilde{C}(omega)` in the frequency domain using the realization-based method
  (SM S1); further refine using gradient-based optimization of `C(t)` in the time domain.
- **Error metric** (Eq. S9): `epsilon = ( (1/T) integral_0^T |C(t) - C_approx(t)|^2 dt )^{1/2}` (averaged L2).
- **Fig. 1a:** `epsilon = 1e-6` fixed, `T in [0, ~100]`. Coupled and quasi Lindblad: `N = O(log T)`
  (~5 modes at T=1, ~13 modes at T=100). Unitary and Lorentzian: `N = O(T)`.
- **Fig. 1b:** `T = 10` fixed. All methods show `N = O(log(1/epsilon))`, but coupled and quasi Lindblad
  converge **significantly faster** (larger per-mode slope). Coupled tracks quasi closely => feasibility
  condition violation is small.

### Spin-boson dynamics (Fig. 2)

- **System.** `H_S = (omega_e/2) sigma_z`, `S = sigma_x`. Lorentzian-like spectral density:
  `J(omega) = 2 g^2 kappa omega_c omega / [pi ((omega_c^2 - omega^2)^2 + kappa^2 omega^2)]` for `omega >= 0`,
  zero for `omega < 0`. Parameters: `omega_c = omega_e = 0.58`, `g = 0.25`, `kappa = 0.1 meV`.
- **Regime.** Ultra-strong coupling. Initial state `rho_S(0) = |0><0|`.
- **Result.** Population `n_0(t) = <0|rho_S(t)|0>`: N=2 and N=4 coupled modes vs reference (unitary N=400
  discretization). Our N=4 achieves accuracy comparable to Lednev et al.'s N=10.
- **Negative-frequency contribution.** ~1e-5 (N=4), vanishes to ~1e-9 (N=10) -- the SDP inherently suppresses
  unphysical negative-frequency contributions, whereas Lednev et al. needed explicit penalties.
- **TDVP solver.** SM Section S4: ITensors.jl / ITensorMPS.jl, TDVP, cutoff 1e-12, renormalize tr(rho)=1
  each step. Site ordering by dissipation magnitude (ref [25]).

### Dimer absorption spectra (Fig. 3, SM Section S7)

- **System.** Three-state dimer: `|g>, |epsilon_1>, |epsilon_2>`, `H_S = sum_i epsilon_i |epsilon_i><epsilon_i|
  + J(|epsilon_1><epsilon_2| + |epsilon_2><epsilon_1|)`. System-bath coupling: `S_i = |epsilon_i><epsilon_i|`
  (independent coupling to each excited state).
- **Environments.** `J_0(omega)` -- broad spectrum (Adolphs-Renger form, ref [62]).
  `J_1(omega) = J_0(omega) + J_AL(omega)` -- broad + anti-symmetrized Lorentzian peak (Eq. S10).
- **Absorption spectrum.** `S(omega) = omega Im[ integral_0^infty i C_mu(t) e^{i omega t} dt ]`,
  dipole-dipole correlation function `C_mu(t) = tr[ mu_dagger e^{L t} mu rho_S(0) otimes rho_B(0) ]`,
  `mu = sum_i |epsilon_i><g| + |g><epsilon_i|`, `rho_S(0) = |g><g|`. Evolved to `T = 5000`, `Delta t = 5e-4`,
  Fourier-transformed via ESPRIT (ref [59]).
- **Result.** N=3 coupled modes capture both `J_0` and `J_1` at 0 K and 77 K. Lorentzian pseudomode fails
  to reproduce the broad component and misplaces spectral peaks. The absorption spectrum shows a sharp peak in
  the negative-frequency region at zero temperature which becomes narrower and sharper as N increases.

### Sub-Ohmic spectral density (SM Fig. S3)

- `J(omega) = omega^{1/2} e^{-omega}` (alpha=1/2, omega_c=1). Known to be more challenging due to the
  omega=0 singularity.
- Same `polylog(T/epsilon)` scaling confirmed. N=4 achieves accurate fitting.

### Fermionic Anderson impurity (SM Fig. S1)

- Semicircular bath spectral density: `J(omega) = (Gamma/pi) sqrt(1 - (omega/W)^2)`, `W=10`, `Gamma=1`,
  inverse temperature `beta = 100`.
- Impurity Hamiltonian `H_S = epsilon (n_up + n_down) + U n_up n_down`, `U=8`, `epsilon=-4`.
- Initial empty impurity `rho_S(0) = |0><0|`.
- N1 = N2 = N modes for lesser and greater hybridization functions. Accurate with `N = 2, 4` per spin.

---

## Comparison: Coupled Lindblad vs quasi-Lindblad

| Property | Quasi-Lindblad | Coupled Lindblad |
|---|---|---|
| **Genuine Lindblad form (H=H_dagger, Gamma>=0)?** | No (D_SA breaks CP) | Yes (Eq. 2) |
| **Quantum channel?** | No | Yes |
| **Numerical stability?** | Can be unstable (ref [46]) | Stable (CPTP) |
| **Quantum hardware realizable?** | No (exp-large subnormalization, ref [51]) | Yes (trapped-ion analog simulators, refs [15,16]) |
| **BCF structure** | Diagonal Lambda, complex weights `l_dagger e^{-i Lambda t} r` | Non-Hermitian K, `g_dagger e^{-i K t} g` |
| **N for polylog?** | Yes (ref [26], conditionally) | Yes (via Thm 1 transfer, conditionally) |
| **Mode coupling** | None (diagonal H, Gamma) | Yes (dense H, Gamma) |
| **Parameter count** | O(N) | O(N^2) |
| **Construction** | ESPRIT/Prony (convex signal processing) | SDP Eq. 8 (convex) |
| **Efficiency gain over CPTP alternatives** | (not applicable, non-CP) | `polylog` vs `poly` for unitary/Lorentzian |

**What CPTP buys relative to quasi-Lindblad (the paper's key message):**
- Numerical stability for classical simulation (no risk of divergence from CP violation).
- Compatibility with quantum hardware (no exponentially large subnormalization factor).
- Same asymptotic scaling (polylog) when the feasibility condition Eq. 7 holds.

---

## Limitations and boundaries [paper]

1. **Gaussian bath only.** Non-Gaussian baths / genuinely anharmonic environments are out of scope. The entire
   approach relies on the bath being fully characterized by its 2-point BCF.

2. **`polylog(T/epsilon)` scaling is CONDITIONAL, not unconditional.** It transfers from quasi-Lindblad only
   when the feasibility condition Eq. 7 holds AND under the analyticity assumptions on `J(omega)` that
   ref [26] requires. The paper's own abstract: "We provide theoretical evidence that..." -- notably weaker
   language than "we prove." The scaling is demonstrated numerically (Fig. 1) but not proven as a universal bound
   for all BCFs.

3. **SDP feasibility is not guaranteed.** When Eq. 7 is far from satisfiable, the coupled Lindblad representation
   may require more modes than quasi-Lindblad, or the approximation quality may degrade. The paper's numerics
   show small violation for their examples but do not explore failure cases.

4. **Factorization of initial state.** `rho(0) = rho_S(0) otimes rho_B(0)` is assumed -- correlated initial
   states are not treated.

5. **Temperature via Fermi-Dirac/bath thermal state.** Handled by folding thermal occupation into the BCF
   (bosonic) or Fermi function (fermionic, Eq. S6). The pseudomodes start in vacuum (bosonic) or
   filled+empty (fermionic, Eq. S8). Only 77 K shown for the dimer; zero-temperature for the Ohmic and
   sub-Ohmic examples.

6. **Quantum-hardware realization cost.** Although CPTP (so in principle realizable), the paper notes (ref [51])
   that a general channel encoding needs an exponentially large T-dependent subnormalization on a quantum
   computer. Coupled Lindblad avoids the CP-violation obstruction that blocks quasi-Lindblad, but the
   *practical* quantum implementation cost at large T is not resolved. Classical simulation (TD-DMRG) has no
   such issue.

7. **Bosonic Fock truncation.** Not explicitly discussed as a limitation, but the pseudomodes require
   truncated Fock spaces; the truncation dimension is a practical hyperparameter.

8. **Scalability of the SDP.** Eq. 8 involves an N x N matrix variable `Y`. For large `N` (potentially needed
   for high precision or long time), the SDP cost scales as `O(N^3)` per iteration. The paper's examples use
   `N <= 13` so this is not an issue, but it could become one for very demanding targets.

---

## [paper] vs [ours] -- mapping to qec_twin

### What is directly reusable

| Paper component | Ours |
|---|---|
| Eq. 2: Coupled-Lindblad master equation (H=H_dagger, Gamma>=0) | Directly implementable as enlarged Markovian system on our MCWF/MPS carrier |
| Eq. 3: BCF `C^c(t) = g_dagger e^{-i K t} g` | Pre-processing computation; fit target BCF into this form |
| Eq. 8: SDP construction | Solves the non-convex fitting problem; one-shot SDP (cvxpy/scipy) |
| SM Eq. S2--S4: Matrix-valued g for multi-site | **Critical for us**: single pseudomode couples to multiple qubits => shared bath |
| SM Eq. S3: Matrix-valued BCF `C^c(t) = g_dagger e^{-i K t} g`, `g in C^{N x n}` | Captures cross-qubit noise correlations |
| SM Section S1: Loewner realization construction | Alternative when BCF is in frequency domain |
| SM Section S4: TDVP superoperator evolution | Reference solver; we can use MCWF unraveling instead |

### What needs verification

1. **Revival preservation under truncation.** Does `|L(t)|` (CP-divisibility breaking, coherence revival)
   survive `N = 3--4` truncation for a QEC-relevant 1/f/TLS BCF? The paper's formalism guarantees `C^c = C`
   to precision `epsilon`, but the fidelity of revival features at finite `N` must be checked empirically
   for our specific BCF targets. **Load-bearing for the non-Markovian wedge claim.**

2. **Matrix-valued (multi-qubit) SDP well-posedness.** For `n =` #qubits in a d=3 surface code (9--17 data
   qubits), the coupling matrix `g in C^{N x n}` and matrix-valued target BCF `C(t) in C^{n x n}` scale
   linearly in `n`. Does the SDP (Eq. 8 generalized to matrix `g`) stay well-posed? Does `N` stay small?
   This governs whether the shared-bath construction is practical at our QEC scale.

3. **Coupled Lindblad scaling for QEC-relevant BCFs.** Re-run Fig. 1-style `N` vs `T` and `N` vs `epsilon`
   for 1/f and TLS-sum spectral densities. The polylog claim is conditional and was demonstrated only for
   Ohmic, sub-Ohmic, semicircular, and Lorentzian-like spectral densities; 1/f noise has a different analytic
   structure and may behave differently.

4. **MCWF unraveling of dense `Gamma`.** The dissipator `D_A` with off-diagonal `Gamma_{kl}` requires
   eigen-decomposition: `Gamma = sum_mu gamma_mu c_mu c_mu_dagger` (factorization into independent jump
   channels). Each `gamma_mu` must be non-negative (guaranteed by `Gamma >= 0`). The jump operators become
   linear combinations of `b_k` modes. This is straightforward algebra but must be implemented.

### Open questions

1. **Fock truncation dimension.** For weak QEC dephasing (the relevant regime), pseudomode occupation numbers
   are small, so Fock dim = 2--4 is plausible. Must be verified for our target coupling strengths.

2. **SDP scaling with `N`.** The SDP's `O(N^3)` cost is fine for `N <= 13` (paper's regime), but if our QEC
   BCFs require larger `N`, the construction cost could become significant.

3. **Non-Gaussian single-TLS regime.** A strongly-coupled single TLS that behaves non-Gaussianly (telegraph
   noise saturation) is NOT a Gaussian bath and is OUT of scope of this paper. This is a real boundary for
   QEC 1/f modeling. The "1/f = sum of Lorentzian TLS" model is Gaussian (each TLS is a Gaussian process in
   its coupling operator), but if individual TLSs saturate into telegraph noise, the Gaussian assumption
   breaks. **This regime must be explicitly bracketed, not claimed.**

4. **Finite-temperature BCF structure.** The paper handles temperature via the thermal BCF (Fermi-Dirac for
   fermions, detailed balance for bosons). For our QEC temperatures (~10--20 mK, well below the TLS energy
   scale), the thermal effects may be negligible, but this should be confirmed.

### Corrections this paper forces on our current design

1. **Carry the SOURCE explicitly.** The paper validates the conclusion that a positive-rate
   `Sigma D[c_i]` is still Markovian and cannot carry the non-Markovian wedge. You must carry a bath.
   Pseudomodes ARE that explicit source, done in a provably-CPTP, few-mode, polylog-scaling way.

2. **Use convex SDP, not non-convex fitting.** The paper's Eq. 8 (convex SDP) supersedes any plan to
   hand-tune a non-convex coupled-mode fit. Use ESPRIT/Prony for the initial quasi-Lindblad fit (which
   is a standard signal-processing task, now convex), then solve the SDP to convert to coupled Lindblad.

3. **Matrix-valued BCF for shared bath.** SM Eq. S2--S4 directly gives the form of a multi-qubit shared-bath
   pseudomode embedding. The coupling vector `g` becomes a matrix `g in C^{N x n}`; the BCF becomes an
   n x n matrix-valued function. This is the form we should target, not a scalar-per-qubit approximation.

---

## Actionable implementation path [ours]

**Goal**: Implement a shared-bath pseudomode embedding for our QEC noise simulator such that the enlarged
(qubits + bosonic pseudomodes) system evolves under a genuine GKSL Lindbladian (Eq. 2 / SM Eq. S4), and
the reduced qubit dynamics reproduces a target non-Markovian BCF `C(t)` (scalar for single-qubit dephasing,
matrix-valued for multi-qubit shared dephasing).

### Complete computation chain

**Step 0: Choose the target BCF.**
- From QEC physics: select the shared-bath model (1/f noise, TLS bath, or combined).
- Compute the target BCF `C_target(t)` for `t in [0, T]` from the spectral density:
  `C(t) = (1/pi) integral_0^infty J(omega) [coth(beta omega/2) cos(omega t) - i sin(omega t)] domega`
  (bosonic thermal BCF at inverse temperature beta; at T=0, reduces to
  `C(t) = integral_0^infty J(omega) e^{-i omega t} domega`).
- For multi-qubit shared bath: form the matrix-valued BCF `C_target(t) in C^{n x n}` where `[C_target(t)]_{ij}`
  captures the correlation between noise on qubit `i` and qubit `j`.

**Step 1: Fit the quasi-Lindblad BCF (Eq. 5).**
Fit `C_target(t) ~ C^q(t) = sum_{k=1..N} l_k r_k e^{(-i omega_k - gamma_k) t}`.
- Time-domain: use ESPRIT (refs [25, 63]) or Prony (ref [64]) -- standard signal-processing algorithms for
  complex-exponential fitting. Most mature option: ESPRIT from the `esprit` package or via `scipy.signal`.
- Frequency-domain (if `C_target(omega)` is given on a grid): use the Loewner-matrix SVD realization
  (SM Section S1, ref [42]).
- **Output**: `N`, diagonals `{omega_k, gamma_k}`, complex weights `{l_k, r_k}`.
- **Hyperparameter**: `N` is increased until fitting error `epsilon` (Eq. S9) is below tolerance.
- **Check**: The `polylog(T/epsilon)` scaling should be confirmed empirically for the QEC BCF by
  reproducing Fig. 1-style N vs T, N vs epsilon plots.

**Step 2: Convert to coupled Lindblad via the SDP (Eq. 8).**
Solve the convex optimization:
```
min_{Y >> 0}  || l - Y r ||^2_2
subject to   i( Y Lambda - Lambda_dagger Y ) >= 0
```
- `Lambda = diag(omega_k - i gamma_k)` in C^{N x N}.
- `l, r` in C^N from Step 1.
- The LMI `i(Y Lambda - Lambda_dagger Y) >= 0` enforces `Gamma >= 0`.
- Solver: cvxpy with SDP backend (SCS, MOSEK, or Clarabel).
- **Output**: `Y >> 0` (N x N positive definite).
- **Edge case**: If infeasible (feasibility condition Eq. 7 strongly violated), increase `N` or accept
  a larger fit error.

**Step 3: Recover coupled Lindblad parameters.**
```
X = sqrt(Y)              (matrix square root, e.g. scipy.linalg.sqrtm)
K = X Lambda X^{-1}
g = X r
H = (K + K_dagger) / 2
Gamma = (K_dagger - K) / (2i)          (should be >= 0 by construction)
```
- **Check**: verify `Gamma >= 0` numerically (all eigenvalues non-negative).
- **Check**: verify `C^c(t) = g_dagger e^{-i K t} g` matches `C_target(t)` on `[0, T]` to tolerance.

**For multi-qubit (matrix-valued g):**
- Generalize: `g in C^{N x n}`, `l, r` become matrices `L, R in C^{N x n}` from fitting the matrix-valued
  BCF. The SDP objective becomes `|| L - Y R ||_F^2` (Frobenius norm). The LMI constraint remains on the
  N x N `Y`. The same steps apply component-wise.

**Step 4: Assemble and evolve the enlarged Lindbladian (Eq. 2 or SM Eq. S4).**
Construct the GKSL generator on the enlarged Hilbert space (system qubits + N bosonic pseudomodes):
```
d/dt rho = -i[ H_S + H_A + H_SA, rho ] + D_A(rho)
```
where:
- `H_A = sum_{k,l} H_{kl} b_dagger_k b_l` (bilinear bosonic Hamiltonian, dense H).
- `H_SA = sum_j S_j A_j` with `A_j = sum_k g_{kj} b_dagger_k + conj(g_{kj}) b_k` (system-pseudomode coupling).
- `D_A(rho) = sum_{k,l} Gamma_{kl} (2 b_l rho b_dagger_k - {b_dagger_k b_l, rho})` (off-diagonal dissipator).

Initial state: `rho(0) = rho_S(0) otimes |0><0|^{otimes N}` (pseudomodes in vacuum, or `|1><1|` for the
filled set in fermionic Eq. S8).

**Step 5: Unravel the Lindbladian for MCWF (jump operators from dense Gamma).**
For MCWF simulation, factorize the dense dissipator:
1. Diagonalize `Gamma = U Gamma_diag U_dagger` (unitary diagonalization, guaranteed as Gamma >= 0).
2. Jump operators: `c_mu = sqrt(gamma_mu) sum_k U_{k,mu} b_k` for each positive eigenvalue `gamma_mu` of `Gamma`.
3. MCWF: evolve each quantum trajectory under the effective non-Hermitian Hamiltonian
   `H_eff = H_S + H_A + H_SA - (i/2) sum_mu c_mu_dagger c_mu`, with stochastic jumps `c_mu` applied at
   rates `gamma_mu` and post-jump renormalization.

**For TDVP/superoperator evolution (SM Section S4):**
- Vectorize rho -> |rho>>.
- Construct super-Liouvillian `L = -i[H, .] + D_A(.)`.
- Evolve with TDVP (ITensors.jl / ITensorMPS.jl or our own MPS backend).
- Site ordering by dissipation magnitude (ref [25]).
- Cutoff epsilon = 1e-12. Renormalize tr(rho) = 1 each step.

**Step 6: Verification.**
- Reproduce the paper's Fig. 1 for Ohmic spectral density (sanity check on our fitting+SDP pipeline).
- Compute reduced `rho_S(t)` and compare with:
  - DM oracle (small system, d=3, using `forward/exact`).
  - Large-N unitary discretization (N=400, following paper's reference method).
- Plot `|L(t)|` (CP-divisibility witness) for the recovered dynamics vs target to verify the non-Markovian
  wedge survives truncation.
- Measure fitting error `epsilon` (Eq. S9) and verify `polylog(T/epsilon)` scaling for our QEC BCFs.

### Software dependencies needed

1. **ESPRIT or Prony implementation** for quasi-Lindblad BCF fitting (time-domain signals).
   - scipy.signal has `scipy.signal.esprit`? Or `pysespr` package. Or implement matrix-pencil method.
   - Ref [25] uses ESPRIT; ref [64] uses Prony.
2. **SDP solver** for Eq. 8.
   - cvxpy (python) with SCS/MOSEK/Clarabel backend.
   - Must support PSD matrix variables and LMI constraints.
3. **Matrix functions** for the gauge transformation.
   - `scipy.linalg.sqrtm` for `X = sqrt(Y)`.
   - `scipy.linalg.solve` for `X Lambda X^{-1}`.
4. **Quasi-Lindblad BCF value** evaluation tooling to compute `epsilon = ||C - C_approx||_{L2}`.
5. **Larger infrastructure**: bosonic pseudomode sites in our MPS/MCWF carrier (truncated Fock basis),
   bilinear bosonic Hamiltonian evolution, off-diagonal dissipator, MCWF jump operators from factorized
   `Gamma`.

### Verification targets

1. **Reproduce Fig. 1a/1b** (Ohmic J(omega), T up to ~100, epsilon down to 1e-8). This validates:
   - Our ESPRIT/Prony fitting produces correct quasi-Lindblad parameters.
   - Our SDP (Eq. 8) converts to coupled Lindblad without degrading fit quality.
   - `N = O(log T)` scaling holds.

2. **Reproduce Fig. 2** (spin-boson population dynamics with Lorentzian-like J(omega)). Validates:
   - The full Eq. 2 evolution matches the paper's TDVP results.
   - N=4 achieves the stated accuracy.

3. **Non-Markovian CP-divisibility check.** Construct a BCF known to yield non-Markovian reduced dynamics
   (e.g., revival-bearing). Verify that `|L(t)|` computed from the pseudomode-carrier dynamics shows the
   same revival structure as the exact dynamics. **Load-bearing.**

### Key risk registers

| Risk | Mitigation |
|---|---|
| Feasibility condition Eq. 7 strongly violated for our QEC BCF => more modes needed | Accept larger N; benchmark empirically; fall back to quasi-Lindblad with stability monitoring if N is prohibitive |
| Non-Gaussian single-TLS regime outside scope | Bracket explicitly; model only the Gaussian (Lorentzian-sum) component of 1/f |
| SDP fails to converge for large N or ill-conditioned data | Use robust solvers (MOSEK); pre-condition the quasi-Lindblad fit; accept suboptimal but feasible Y |
| Fock truncation cost at relevant coupling | Test Fock dim 2--6; occupation numbers should be low for weak QEC dephasing |
| MCWF cost with N=4--13 bosonic modes on MPS | Monitor bond dimension; use TDVP rather than MCWF if MCWF trajectories require too many samples |

---

## Summary verdict [ours]

1. **YES -- the embedded dynamics is a genuine Markovian CPTP channel** (Eq. 2 is exact GKSL:
   `H=H_dagger`, `Gamma>=0`), runnable as-is on our MCWF/2D-TN carrier as extra truncated-Fock bosonic sites;
   no memory kernel, no negative rates. The paper's Theorem 1 provides the theoretical bridge from the
   quasi-Lindblad `polylog` bound to CPTP coupled Lindblad.

2. **`polylog(T/epsilon)` scaling is CONDITIONAL** -- it transfers from quasi-Lindblad only when the SDP
   feasibility condition Eq. 7 holds AND under ref [26]'s analyticity assumptions on `J(omega)`. The paper
   calls it "theoretical evidence" + Fig. 1 empirics. For our QEC BCFs it must be re-confirmed empirically,
   not assumed.

3. **YES -- one pseudomode can couple to MULTIPLE qubits (shared bath).** SM Section S2 Eq. S2--S4:
   coupling matrix `g in C^{N x n}`, matrix-valued BCF `C^c(t) = g_dagger e^{-i K t} g`. This is exactly
   the cross-qubit correlated-noise carrier.

4. **The SDP construction (Eq. 8) replaces non-convex optimization** from prior work. The computation chain
   (BCF -> ESPRIT/Prony quasi-Lindblad fit -> SDP -> coupled Lindblad parameters -> enlarged Lindbladian
   evolution) is entirely convex or standard signal processing.

5. **Blocker/boundary:** Gaussian-bath restriction -- fits 1/f + Lorentzian-sum TLS (our target), but a
   strongly-coupled non-Gaussian single TLS (telegraph saturation) is OUT of scope. Bracket that regime
   explicitly.
