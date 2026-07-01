# Full-text review — Parish & Duraisamy, "Non-Markovian Closure Models for Large Eddy Simulations using the Mori-Zwanzig Formalism" (arXiv:1611.03311)

> **Provenance (2026-06-30): FULL-TEXT read (精读).** PDF `outputs/papers/1611.03311.pdf` → txt
> `outputs/papers/1611.03311.txt` (PyMuPDF, 31 pages, 68844 chars). All §/Eq/Fig/Table refs from that
> text. Figures not pixel-extracted — figure facts = captions + numbers stated in the body. Published as
> Phys. Rev. Fluids **2**, 014604 (2017); arXiv v2, 23 Jan 2017.

## Metadata [paper]
- **Authors / affiliation:** Eric J. Parish, Karthik Duraisamy — Dept. of Aerospace Engineering, University of Michigan, Ann Arbor.
- **Venue / status:** arXiv:1611.03311v2 (physics.flu-dyn), 23 Jan 2017; PRFluids 2, 014604.
- **Type:** Theory + numerical simulation (CFD / turbulence coarse-graining; no experiment).

## Executive summary [paper]
The paper builds **sub-grid (LES) closure models** for turbulence by treating coarse-graining (removing
unresolved small scales) as an application of the **Mori–Zwanzig (M-Z) formalism**. M-Z re-casts the exact
resolved-variable dynamics as a **generalized Langevin equation (GLE)** with three terms: a Markovian term,
a convolution **memory** integral, and an **orthogonal-dynamics noise** term (Eq. 10). The memory integral
is intractable (it needs the orthogonal-dynamics PDE, Eq. 12), so they adopt **Stinis' finite-memory
models** (Eqs. 21–26): the memory is assumed to have finite support τ, differentiated in time to yield a
**closed hierarchy of auxiliary ODEs** `w^(m)` (Eq. 26) that is truncated by neglecting the next level. The
one free quantity, the **memory length τ**, is set by a **dynamics-based heuristic**: `τ ∝ 1/ρ(∂R/∂u)`, the
inverse spectral radius of the Jacobian of the *resolved* variables (§III.B.1), fit over 60 Burgers cases to
`τ₀ ≈ 0.2 / ρ(∂R/∂u)`. Tested on viscous Burgers, homogeneous isotropic turbulence, Taylor-Green vortex,
and channel flow, the finite-memory models match filtered-DNS energy/dissipation/sub-grid-transfer without a
modeler-imposed closure form. **Headline claim: the closure FORM is derived from the coarse-graining
mathematics, not postulated** (§VI).

## Method (deep) [paper]

### 1. Demonstrative linear reduction (the essence) — §II, Eqs. 1–4
Two-state linear system `dx/dt = A₁₁x + A₁₂y`, `dy/dt = A₂₁x + A₂₂y`. Solving the unresolved `y(t)` exactly
and substituting gives a **closed, non-Markovian** equation for `x` alone:

```
dx/dt = A₁₁ x  +  A₁₂A₂₁ ∫₀ᵗ x(t−s) e^{A₂₂ s} ds  +  A₂₁ y(0) e^{A₂₂ t}      (Eq. 4)
              └─ Markovian ─┘  └──────── memory (convolution) ────────┘   └── noise (init cond of y) ──┘
```

This is the template: eliminating unresolved DOF turns a **Markovian coupled** system into a
**non-Markovian closed** system = Markovian term + memory convolution + noise. The exponential
`e^{A₂₂ s}` (the *unresolved* subsystem's propagator) is the memory kernel; if `A₂₂` has negative
eigenvalues the kernel decays → **finite memory support** with timescale ∝ 1/|eigenvalue|.

### 2. Formal M-Z identity (the GLE) — §II, Eqs. 5–13
Semi-discrete nonlinear ODE `dφ/dt = R(φ)`, split `φ = {φ̂ (resolved, N modes), φ̃ (unresolved, M modes)}`.
Recast as a **linear Liouville PDE** `∂u/∂t = L u` (Eq. 6), with Liouville operator
`L = Σ_k R_k(φ₀) ∂/∂φ₀_k`; solution `u(φ₀,t) = g(e^{tL}φ₀)` (semigroup). Define projection `P: L² → L̂²`
onto resolved space and `Q = I − P`. Apply the **Duhamel identity**
`e^{tL} = e^{tQL} + ∫₀ᵗ e^{(t−s)L} P L e^{sQL} ds` to `∂/∂t e^{tL}φ₀ⱼ = e^{tL} L φ₀ⱼ` to obtain the exact
**Mori–Zwanzig identity / GLE** (Eq. 10):

```
∂/∂t e^{tL}φ₀ⱼ  =  e^{tL} P L φ₀ⱼ           (Markovian)
                +  e^{tQL} Q L φ₀ⱼ           (Noise — lives in null space of P, "orthogonal dynamics")
                +  ∫₀ᵗ e^{(t−s)L} P L e^{sQL} Q L φ₀ⱼ ds   (Memory — convolution kernel)
```

Define `F_j(φ₀,t) = e^{tQL} Q L φ₀ⱼ` (noise) and `K_j = P L F_j` (memory integrand). `F_j` obeys the
**orthogonal-dynamics equation** (Eq. 12): `∂F_j/∂t = Q L F_j`, `F_j(0) = Q L φ₀ⱼ`, with `P F_j = 0` for all
time. Compact GLE (Eq. 13):
`∂φ_j/∂t = R_j(φ̂) + F_j + ∫₀ᵗ K_j(φ̂(t−s), s) ds`. Projecting kills the noise (Eq. 14):
`∂/∂t Pφ_j = P R_j(φ̂) + P ∫₀ᵗ K_j(φ̂(t−s), s) ds` — the best L̂² approximation given the initial density of
φ̃. **Note (Eq. 14 caveat):** for nonlinear R the projection does NOT commute (`E[f(x)] ≠ f(E[x])`); the
paper "casually commutes" it (Eqs. 30, 35) — an admitted approximation.

### 3. Structure of the memory kernel (why finite support) — §II.A, Eqs. 15–19
For a **linear** system `dφ/dt = Aφ`, the orthogonal dynamics is solved by an **auxiliary linear ODE**
`dφ_Q/dt = A_Q φ_Q`, `A_Q = A Q` (Eq. 17). Diagonalizing, `φ_Q(t) = S e^{Λt} S⁻¹ φ₀` (Eq. 18), so the memory
integrand carries the factor `e^{Λs}`. **Negative eigenvalues Λ ⇒ integrand has finite support, timescale ∝
1/|Λ|** (§II.A, Fig. 1). This is the derived justification for a finite-memory approximation and — critically
— the origin of the τ-heuristic.

### 4. Finite-memory models (the tractable closure) — §II.B, Eqs. 20–26
- **t-model** (Eq. 20): Taylor-expand the integrand about s=0, keep leading term →
  `P ∫₀ᵗ … ds ≈ t · P L Q L φ_j(t)`. Time appears explicitly ⇒ no coefficients, but unstable/over-dissipative
  at long t. Equivalent to assuming **infinitely long memory**.
- **Finite-memory hierarchy** (Stinis; Eqs. 21–26): assume the memory has finite support `[t−τ_m, t]`.
  Define `w_j^(m)(t) = P ∫_{aₘ(t)}^t e^{sL} P L e^{(t−s)QL} (QL)^{m+1} φ₀ⱼ ds` (Eq. 21). **Differentiate in
  time** and apply the **trapezoidal rule** to the residual integral → an ODE whose RHS is closed except for
  the *next* memory level `w^(m+1)` (Eq. 25). This builds an **infinite hierarchy of Markovian auxiliary
  ODEs**, truncated by neglecting `w^(m+1)` (justified if support/magnitude shrinks under repeated `QL`).
  **The operative model** (constant memory length, one sub-interval, Eq. 26):

  ```
  d/dt w_j^(m)(t) = −(2/τ_m) w_j^(m)(t) + 2 e^{tL} P L (QL)^{m+1} φ₀ⱼ  + w_j^(m+1)      (Eq. 26)
  ```

  This is a **linear relaxation ODE** for each auxiliary variable: relaxation rate `2/τ_m`, forced by an
  algebraic term computable from the resolved field (`e^{tL}PL(QL)^{m+1}φ₀ⱼ`, e.g. Eq. 31 for Burgers), plus
  the next (neglected) level. Truncating at m=0 with `w^(1)≈0` gives the first-order finite-memory model
  **FM1**; FM2/FM3 keep more levels (Appendix A, Eqs. 41–42 give the Burgers `(QL)²`, `(QL)³` forcing terms
  following a Pascal-triangle pattern). The sub-grid stress is recovered as `w^(0) = ik·τ_SGS` (§III.C).

### 5. The memory-length heuristic (the ONE remaining knob) — §III.B.1, Appendix B
τ cannot be computed directly (needs orthogonal dynamics). **Heuristic:** since the linear analysis ties the
memory timescale to the eigenvalues of the auxiliary system, and Burgers lacks scale separation, hypothesize
a mean timescale set by the **spectral radius of the Jacobian of the resolved variables**:

```
τ ∝ 1 / ρ(∂R/∂u)         →   fit:  τ₀ ≈ 0.2 / ρ(∂R/∂u₀)      (§III.B.1)
```

Validated by a **60-case parametric study** (ν ∈ {0.05,0.01,0.005,0.001,0.0005}, k_c ∈ {8,16,32}, U₀* ∈
{1,2,5,10}; DNS 4096 modes). For each case τ₀ found by an **inverse problem** (least-squares minimize the
mismatch in kinetic-energy dissipation rate vs DNS over t∈[0,2], Nelder-Mead downhill simplex, penalty
`J = Σ_n (dK_n/dt|_{M-Z} − dK_n/dt|_{DNS})²`). Inferred τ₀ collapses **linearly** against `1/ρ(∂R/∂u)`
(k_c=16,32 collapse to one line; k_c=8 slightly steeper — Fig. 2). Higher-order memory lengths were NOT
fit; simply set `τ₁=τ₂=0.5τ₀`. **Alternate heuristic** (§IV.C, VI): scale the LES time step by the ratio of
grid size to estimated Kolmogorov scale. **Physical interpretation (kept honest):** τ is NOT a physical
parameter and NOT a tuning constant — higher Re → smaller τ, coarser mesh → larger τ (§III.B.1).
Appendix B does a **stochastic UQ** on τ (Gaussian weight `w`, `τ₀ = w/ρ(∂F/∂u)`, 1000 Monte-Carlo draws):
integrated quantities (energy, dissipation) are **well-concentrated** around the mean, sub-grid `w^(0)`
somewhat wider → results are **insensitive to the exact τ**.

## The MECHANISM (for implementation) [paper → ours]
The implementable object is **Eq. 26** — a bank of linear relaxation ODEs (`w^(0)`, optionally `w^(1)`, …)
carrying the memory of the unresolved DOF, coupled to the resolved-variable evolution, with:
1. a **relaxation rate `2/τ`** set by the **inverse spectral radius of the resolved-variable Jacobian**
   (`τ ≈ 0.2/ρ(∂R/∂u)`);
2. a **forcing term** `e^{tL}PL(QL)^{m+1}φ₀ⱼ` computed algebraically from the resolved field each step (for a
   quadratic nonlinearity this is a convolution over resolved modes; Eq. 31);
3. truncation by neglecting the next level (FM1 = keep `w^(0)` only).

Repo status: **not implemented.** No M-Z / GLE / memory-kernel machinery exists in `qec_twin` (the codebase
is quantum-channel / DEM / MPS-carrier; no coarse-graining-in-time closure).

## The OBSERVABLE / metric [paper]
- **Fit/validation metric:** L2 error of the **kinetic-energy dissipation rate** `dK/dt` vs filtered DNS
  (penalty `J`, §III.B.1); also total kinetic energy, energy spectra E(k), resolved transfer spectrum T(k),
  and **sub-grid transfer spectrum** `T_SGS(k) = u_i*(k) w_i^(0)(k)` (§IV.C).
- **The diagnostic the paper uses to prove the closure is right:** phase-space **trajectories of individual
  modes** of `u` and `w^(0)` (Fig. 4). Smagorinsky gets integrated energy roughly right but its `w^(0)`
  trajectories bear **no resemblance** to DNS (it predicts max sub-grid content at t=0 even when fully
  resolved) — i.e. matching an integrated scalar is INSUFFICIENT to certify a sub-grid model; the
  mode-resolved sub-grid trajectory is the discriminating observable. **[ours: this is a direct analogue of
  our "integrated LER agrees but the mechanism is wrong" trap.]**
- **Memory-length indicator:** `ρ(∂R/∂u)`, spectral radius of the resolved Jacobian (§III.B.1).

## Findings + numbers [paper]
- Burgers (k_c=16, ν=0.01, U₀*=1, DNS 2048 modes → LES 32 modes): FM1 accurate on E(k) at low k; FM2/FM3
  accurate across **all** wave numbers; constants `τ₀=0.135`, `τ₁=0.07`, `τ₂=0.07` (Table 1). t-model
  qualitatively right but over-dissipative for t>0.5 and errors grow with explicit t.
- HIT (DNS 512³ → LES 64³, Re_λ≈200, τ₀=0.1, C_s=0.16): finite-memory model **comparable to dynamic
  Smagorinsky**, good across all wave numbers, excellent on sub-grid transfer (Table 2).
- Taylor-Green Vortex (Re=800, 1600; LES 32³, τ₀=0.1): finite-memory model captures the **double-peaked
  dissipation-rate** structure (~t=8); Smagorinsky & t-model over-dissipative and wrongly remove energy at
  t=0 when the flow is still resolved (Tables 3–4).
- Channel flow (Re_τ=180, 32×64×32): mean-velocity profile and Reynolds stresses improved, comparable to
  dynamic Smagorinsky; a **non-decaying** case where finite memory is *essential* (§V).
- τ heuristic: `τ₀ ≈ 0.2/ρ(∂R/∂u)`; k_c=16,32 collapse to one line, k_c=8 steeper (§III.B.1, Fig. 2).

## Limitations [paper]
- **Not a-priori error control.** The finite-memory assumption is "evidence rather than proof" (§III.B.1);
  FM1 error = trapezoidal quadrature error + neglecting `w^(1)`. τ is fit/heuristic, not derived.
- **Nonlinear projection is "casually commuted"** (`E[f(x)] ≠ f(E[x])`, Eqs. 14, 30, 35) — an uncontrolled
  approximation for the Markovian term.
- **Zero-variance Gaussian initial density** (P sets unresolved modes to 0; §III.A). Not valid when initial
  conditions have unresolved content (§VI).
- Fourier-Galerkin only ⇒ **periodic problems**; extension to FE/FV/FD needs scale-separation operators (VMS,
  spectral element). Higher-order memory lengths `τ₁,τ₂` not fit (set to 0.5τ₀). Stability: t-model needs a
  smaller time step than FM. No Galilean-invariance / physical-constraint enforcement on the sub-grid stress.
- **"Numerical memory, not physical memory"** (§II, after Eq. 10): the memory arises from *coarse-graining*,
  its timescale depends on both physics AND the discretization/resolution level — it is resolution-dependent
  by construction.

## Relevance to qec_twin (the fluctuator-bath non-Markovian closure) [ours]

**Why we pulled this paper.** We want a *principled, derived* (not ad-hoc) non-Markovian closure to represent
the effect of an unresolved **fluctuator bath (1/f / TLS)** on the qubit-resolved dynamics — a memory kernel
+ noise, transferable from turbulence coarse-graining. M-Z/GLE is exactly the "eliminate unresolved DOF →
memory + noise" operation.

**What transfers [ours]:**
1. **The FORM is derived, not postulated.** The GLE (Eq. 10) = Markovian + memory-convolution + noise is the
   *generic consequence* of projecting out any set of DOF — this is precisely the structure we want for
   "trace out the fluctuator bath, keep the qubit." Our `project-nonmarkovian-wedge-must-be-coherence` /
   `project-coupling-nonmarkovian-is-the-contribution` memories say the contribution is a **memory kernel +
   noise carrying the source explicitly** — M-Z is the mathematically-honest way to *derive* that form rather
   than assert `ΣD[c_i]` (which stays Markovian).
2. **Finite-memory-as-auxiliary-ODEs (Eq. 26)** is a concrete, cheap representation: a convolution memory
   becomes a small bank of linear relaxation ODEs. This is the **classical analogue of a "pseudomode" /
   auxiliary-DOF unraveling** of a non-Markovian bath — same shape as the reaction-coordinate / HEOM-style
   trick used in open quantum systems (extend the state with auxiliary variables that relax at rate 1/τ).
3. **The certifying observable lesson (Fig. 4):** an integrated scalar (energy ↔ our LER) matching is NOT
   proof; the **mode-resolved sub-grid trajectory** discriminates. Direct analogue of our repeated finding
   that LER agreement is vacuous and the coherence-revival / mode-level signature is the real discriminator
   (`project-twin-axisA-gate-result`, `feedback-scrutinize-vacuous-checks`).
4. **Memory-length = inverse spectral radius of the resolved Jacobian** is a transferable *design heuristic*:
   the bath memory time we plug in could be gauged by the spectral gap / fastest resolved rate, rather than
   hand-tuned — worth registering as a heuristic (class (c)) if we build a GLE closure.

**What does NOT transfer [ours] (blunt):**
1. **This is a CLASSICAL, real-valued PDE/ODE closure — NOT an open-quantum-system method.** The M-Z memory
   kernel here acts on real Fourier modes of a deterministic PDE. Our object is a **CPTP map / density matrix
   / Lindbladian**; the correct quantum analogue is the **Nakajima–Zwanzig master equation** (the quantum
   M-Z), the **time-convolutionless (TCL)** expansion, HEOM, or pseudomode unravelings — NOT this fluids
   closure. The physics that M-Z-for-CFD leaves out (complete positivity, trace preservation, the
   Kubo–Martin–Schwinger bath statistics, coherence) is exactly what we cannot drop.
2. **The τ-heuristic is a Burgers-fit empirical constant** (`0.2/ρ(∂R/∂u)`), validated only on non-chaotic
   fluid toy models. It is **not a physical memory time** (the paper says so explicitly). For a real 1/f/TLS
   bath the memory time is a *physical* quantity (set by TLS switching rates / bath spectral density) — we
   must ground it in the bath spectrum, not borrow a CFD fit. Laundering it as a "design constant" would hit
   our `feedback-toy-generators-audit` rule.
3. **"Numerical memory, not physical memory."** Their memory is a *coarse-graining artifact* whose timescale
   depends on grid resolution. Ours must be **physical** (CP-divisibility breaking of the true bath). Borrowing
   the machinery is fine; borrowing the *interpretation* would be a toy.
4. **No a-priori error bound.** Fails our epistemic-status discipline if used as a *premise*: any M-Z closure
   we build is at best class (b) prediction-band / (c) heuristic, never (a) exact — the truncation
   (neglecting `w^(m+1)`) and the "casual commuting" are uncontrolled.

**RELEVANCE VERDICT [ours]:** M-Z/GLE is the **right conceptual FRAMEWORK** ("project out the bath → memory
kernel + noise, derived not postulated") and worth citing as the lineage for a principled non-Markovian
closure — but **this specific paper is the CFD instance, not a usable recipe for us.** The direct, faithful
transfer is the **quantum** members of the same family (Nakajima–Zwanzig / TCL / HEOM / pseudomodes), which
enforce CPTP + bath statistics. Concretely reusable from *this* paper: (i) the finite-memory → auxiliary-ODE
reduction (Eq. 26) as the *shape* of a tractable memory representation (≈ pseudomode), and (ii) the
"integrated-scalar-match is vacuous; mode-trajectory is the discriminator" methodology lesson. What must be
adapted: replace real-mode dynamics with the Lindblad/CPTP generator, ground τ in the physical bath spectrum
(not a Jacobian fit), and pick the quantum projection (Nakajima–Zwanzig) so complete positivity survives.
Trade-off: M-Z gives *derivation legitimacy* (the form is not ad-hoc) at the cost of *no a-priori error
control* — usable for go/no-go and as a modeling scaffold, never as a theorem-grade premise.

## How to use / trust + open questions [ours]
- **Trust:** full-text 精读 (equations transcribed from body + all three appendices). Figures not
  pixel-extracted — Fig. 2 (τ collapse) and Figs. 3–9 (spectra/trajectories) read from captions + stated
  numbers only.
- **Open questions for implementation (if we pursue a GLE closure):**
  1. Which quantum projection? Nakajima–Zwanzig (time-convolution, matches Eq. 10 structure) vs TCL
     (time-local) — the classical M-Z here is the *convolution* form.
  2. Does the finite-memory auxiliary-ODE bank (Eq. 26) map onto a **pseudomode / reaction-coordinate**
     representation that preserves CPTP? (Believed yes; needs a from-scratch check — that is the actual
     faithfulness gate, not this paper.)
  3. Ground τ: replace `0.2/ρ(∂R/∂u)` with the **bath correlation time** from the TLS/1/f spectral density
     (`feedback-underdetermined-bracket-not-freeze`: if underdetermined, bracket + sweep, don't freeze).
- **GT-feasibility:** for our setting the independent ground truth is a *quantum* one (exact d3 qutrit /
  HEOM-converged / analytic single-TLS), NOT anything in this fluids paper — so this note grounds the
  *framework choice*, and a separate quantum-M-Z / open-system reading note must ground the *implementation*.
