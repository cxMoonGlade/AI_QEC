# Full-text review — Ivander, Lindoy, Lee, "Unified Framework for Open Quantum Dynamics with Memory" (arXiv:2312.13233)

> **Provenance (2026-06-30): FULL-TEXT read (精读).** PDF (arxiv 2312.13233v4, 6.25 MB, 32 pp) →
> txt `outputs/papers/2312.13233.txt` (PyMuPDF, 101642 chars). All §/Eq/Fig/Table refs from that text.
> Figures not pixel-extracted — figure facts = captions + numbers stated in text. Published: Nat. Commun.
> 15, s41467-024-52081-3 (2024).

## Metadata [paper]
- **Authors / affiliation:** Felix Ivander (Harvard, Quantum Science & Engineering); Lachlan P. Lindoy
  (National Physical Laboratory, UK); Joonho Lee (Harvard Chemistry + **Google Quantum AI**, corresponding).
- **Venue / status:** arXiv:2312.13233v4 [quant-ph], 4 Jun 2024; published Nature Communications 2024
  (s41467-024-52081-3).
- **Type:** Theory + numerics (analytic derivation of an equivalence + HEOM/i-QuAPI verification on the
  spin-boson model). No hardware.

## Executive summary [paper]
Two exact non-Markovian open-system formalisms — the **Nakajima–Zwanzig (NZ) memory kernel** `K` (from the
generalized quantum master equation, GQME) and the **Feynman–Vernon influence functional** `I` (INFPI /
path-integral, the object underneath QuAPI, HEOM, TEMPO/process-tensor) — are shown to be **analytically,
explicitly equivalent**, connected *through the reduced system propagator* `U`. The connection is exact (up
to Trotter error), non-perturbative, valid at any coupling strength, for the class where **an N-level system
is linearly (bilinearly) coupled to Gaussian baths** with **simultaneously diagonalizable** coupling
operators (their **Class 1**). Each order-N term of `K_N` maps 1:1 onto a **Dyck path** of order N; the
number of terms is the Catalan number `C_N`. Cost to build `K_N` scales `O(N·2^N)` (super-combinatorial in
time-order N). Two headline payoffs: (i) approximate path-integral methods (e.g. i-QuAPI's `I_k=1` truncation
beyond `k_max`) are **exactly** re-read as specific approximate memory kernels; (ii) an **inverse map**
`ρ → U → K → I → η → J(ω)` **learns the bath spectral density `J(ω)` (Hamiltonian learning) from reduced
system trajectories alone**, given `Ĥ_S`.

## Method (deep) [paper]

### The exact NZ↔IF connection — the load-bearing equations (verbatim)
Trotterized propagator, Eq. (1): `e^{-iĤΔt} = e^{-iĤ_S Δt/2} e^{-iĤ_env Δt} e^{-iĤ_S Δt/2} + O(Δt³)`,
`Ĥ_env = Ĥ - Ĥ_S`. Reduced dynamics via path sum, Eq. (2), collapses to the **system propagator** form,
**Eq. (4):**
> `⟨x⁺_{2N}|ρ_N|x⁻_{2N}⟩ = Σ_{x±_0} (U_N)_{x±_{2N} x±_0} ⟨x⁺_0|ρ_0|x⁻_0⟩`.

Discretized **homogeneous NZ equation, Eq. (5):**
> `ρ_N = L ρ_{N-1} + Δt² Σ_{m=1}^{N} K_{N-m} ρ_{m-1}`, with `L ≡ (1 - (i/ℏ)L_S Δt)`, `L_S• ≡ [Ĥ_S, •]`.

The identical recursion holds for the propagator, **Eq. (6):**
> `U_N = L U_{N-1} + Δt² Σ_{m=1}^{N} K_{N-m} U_{m-1}`.

Eq. (6) is the pivot: it lets one read `K_N` off `{U_k}` as a **cumulant expansion** — the discrete analog of
the transfer-tensor method (Cerrillo–Cao, ref 41), but here `U` is itself written in terms of `I`. First terms:
- `K_0 = (1/Δt²)(U_1 - L)` (deviation from bare dynamics within one step);
- `K_1 = (1/Δt²)(U_2 - U_1 U_1)`;
- `K_2 = (1/Δt²)(U_3 - U_2 U_1 - U_1 U_2 + U_1 U_1 U_1)`.

Then, expressing `{U_k}` in terms of influence functions `{I_k}` (Class-1, `Ĥ_I = Ŝ⊗B̂`, `Ŝ` diagonal, `I`
**pairwise separable**, Eq. (3)), gives the **direct `K_N`↔`{I_k}` map**, **Eqs. (7)–(10)** (with `F ≡ GG`
the bare double-step propagator, `Ĩ_{k,ij} ≡ I_{k,ij} - 1`):
> `K_{0,ik} = (1/Δt²)[ Σ_j G_{ij} I_{0,j} G_{jk} - L_{ik} ]`  (Eq. 7)
>
> `K_{1,im} = (1/Δt²) Σ_{jk} G_{ij} I_{0,j} F_{jk} Ĩ_{1,jk} I_{0,k} G_{km}`  (Eq. 8)
>
> `K_{2,ip} = (1/Δt²) Σ_{jkn} G_{ij} F_{jk} F_{kn} ( Ĩ_{2,jn} I_{1,jk} I_{1,kn} + Ĩ_{1,jk} Ĩ_{1,kn} )`
>          `I_{0,j} I_{0,k} I_{0,n} G_{np}`  (Eq. 9)
>
> `K_3` = the 5-term Eq. (10) (Dyck order 3). `K_4` = the 14-term Eq. (A64).

"We emphasize that Eqs. (7) to (10) are **exact up to the Trotter discretization error and valid for any
coupling strengths** in the models considered in this work." (§Main results.)

### The Dyck-path structure and cost
"each term in `K_N` is represented uniquely by each **Dyck path** of order N." Number of terms in `K_N` =
Catalan number `C_N = (1/(N+1)) C(2N,N)` (1,2,5,14,42,132,…) [§ after Eq. (10); App C E]. Building `K_N`
"gives a computational cost that scales **exponentially in time, `O(N 2^N_dim)`** where `N_dim` is the
**dimension of the system Hilbert space**" [§Main results — note the exponential is in the *time-order* N;
`N_dim` is the multiplicative per-step system-dimension factor]. The `Ĩ_N` (multiplicity-1) "crest" term
dominates `K_N` for the parameters studied [Fig 2].

### Approximate path-integral ⇔ approximate memory kernel (a headline claim, verbatim mechanism)
"approximate INFPI methods can be viewed through the lens of the corresponding memory kernel content (and
vice versa)." For i-QuAPI with `I_{k,ij}=1`, `Ĩ_{k,ij}=0` for `k > k_max`: at `k_max=1`, `K_0`,`K_1`
**unapproximated**; in `K_2` the surviving term is `(Ĩ_{2,jn}I_{1,jk}I_{1,kn} + Ĩ_{1,jk}Ĩ_{1,kn}) →
Ĩ_{1,jk}Ĩ_{1,kn}` (Eq. 11); in `K_3` only `Ĩ_{1,jk}Ĩ_{1,kn}Ĩ_{1,np}` survives. So a QuAPI memory-length
truncation `k_max` is **exactly** a definite truncation of the Dyck-diagram content of `K`.

### The inverse map (Hamiltonian learning) — verbatim chain
**Eq. (15) / (A71):** `ρ → U → K → I → η → J(ω)` (left to right).
- `U_N = P_N P_0^{-1}` from `N_L` linearly-independent reduced trajectories stacked as `P_N` (Eqs. A72–A74);
  noisy data → Moore–Penrose pseudoinverse.
- `K` from `U` by the Eq. (6) cumulant recursion.
- `I` from `K` recursively (inverse of Eqs. 8–10): `I_0 = G^{-1}(δt²K_0 + L)G^{-1}` (Eq. 12);
  `I_{1,jk} = 1 + Δt²(G^{-1}K_1 G^{-1})_{jk}/(F_{jk}I_{0,j}I_{0,k})` (Eq. 13); `I_2` = Eq. (14); general
  procedure = "move all Dyck diagrams except the crest term to the `K_N` side, divide by the rest → `Ĩ_N`"
  (App C F).
- `I → η → J(ω)`: `ln I` gives the pairwise coefficients `η_{kk'}` (Eqs. A79–A81); `η_{Δk}` is a Fourier
  transform of `F(ω) = (2/π)(J(ω)/ω²)(e^{βℏω/2}/sinh(βℏω/2)) sin²(ωΔt/2)`; invert the discrete FT →
  `J(ω)` (Eqs. A82–A86). Nodal frequencies `ωΔt/2 = nπ` are a **null kernel** — they do not affect reduced
  dynamics, so the map is "nearly bijective" (only the `J(ω)`-content that touches the reduced dynamics is
  recoverable). Pure-dephasing (`Ĥ_S` diagonal, commutes with `Ĥ_env`) degrades the bijection: only diagonal
  `I` / `Re η` survive, but `J(ω)` is still recoverable via inverse cosine transform.

### Driven systems ⇒ the process-tensor connection (verbatim)
For time-dependent `Ĥ_S(t)`, `K` loses time-translational invariance and depends on two times. **Factorize**
`K_{N+s,s}` into a time-dependent bare-propagator tensor `P` and a time-independent influence tensor `T`,
**Eq. (16):** `K_{N+s,s;…} = (1/Δt²) Σ_• P^{N+1+s,s}_{x_s,•,x_{s+2N+2}} T_{N;•}`, with `T_{N;•}` built purely
from influence functions up to `I_N` by the same Dyck construction. **The process-tensor statement (verbatim):**
> "The `T_{N;•}` tensor appears to be related to the process tensor. `T` represents `K` upon the contraction
> with `P`, but **the process tensor is used to construct `U` when contracted with `P`.** Subsequently, there
> is a non-trivial rearrangement of the terms to write `K` in terms of the process tensor. The simple
> relationship between `T` and `K` in Eq. (16) is our unique contribution." (§Generalization to Driven Systems;
> also App C H, where `T_1,jk = (I_{1,jk}-1)I_{0,j}I_{0,k}`, `T_2 = (Ĩ_2 I_1 I_1 + Ĩ_1 Ĩ_1)I_0 I_0 I_0`.)

So: `T` (their influence tensor) contracts with bare propagators `P` to give **`K`**; the **process tensor**
(refs 33,34 Jørgensen–Pollock; also TEMPO/PT-MPO refs 29–34) contracts with `P` to give **`U`**. Same
influence content, two different contractions, related by a non-trivial rearrangement.

## The SCOPE — settling the verifier split (verbatim quotes) [paper]

**The exact Dyck / bijective-inversion result is a Class-1 result:**
- **Class 1** (main text, where the clean `K↔I` Dyck equivalence + inversion live): "With only single α for
  all baths j …, `{Ŝ_j}` are all diagonalizable, and furthermore that `{Ŝ_j}` are all **simultaneously
  diagonalizable**. That is, **all terms in `{Ĥ_{I,j}}` commute**. The spin-boson model, other models in the
  same universality class, and Frenkel exciton models … belong to this class." Table I: Class 1 = diagonalizable
  ✓, simultaneously diagonalizable ✓, single `Ĥ_{I,j,α}` per bath ✓.

**On "N-level" — it is ONE central system, and multi-bath means ADDITIVE baths or SEQUENTIAL inversion:**
- "generalizing to **multiple additive environments is straightforward**" [App C B 1]; "generalizing to
  multilevel systems … amounts only to letting `x(t)` take more and different values" [App C B 1, after
  Eq. A40]. I.e. "N-level" = enlarge the **single** central system's local basis; the influence structure is
  unchanged.
- **Multiple environments on the one central system are underdetermined jointly and only invertible
  sequentially** (App C G, verbatim): with several baths, `I_{k'-k} → Π_j I^j_{k'-k}` (Eq. A91), so
  "we cannot obtain unique values for each `η`. This underdetermined problem is otherwise solved **if we
  obtain the IFs of each bath sequentially**. … we can obtain the spectral density of bath 2 … **if we have
  access to the dynamics of the system influenced by bath 1 only.**"
- Multi-bath **through a single central system** is the only distributed setting treated: "generalization to
  extract the `I_α` of multiple baths **through a single central system** is possible and straightforward"
  [§ after Eq. 14].

**Spatially-distinct / non-commuting site couplings = Classes 2–4, where the clean equivalence BREAKS:**
- **Class 2** ("No terms in `{Ŝ_j}` commute but each … diagonalizable … Generalizing … to multiple
  **nonadditive** baths"): worked for two bosonic baths whose system operators don't commute (App D). Result
  (verbatim): "The **recursive, combinatorial structure of this multi-bath problem is distinct** from the
  one-bath/multiple additive bath problems … detailed analysis and numerical evidence in this regard are
  **left for future work**." "there is **no apparent diagrammatic structure** underlying the expansion of `U`
  in terms of `I`" (App D A). Inversion only works assuming baths characterized **independently-sequentially**.
- **Class 3** ("common baths for some `Ĥ_{I,j,α}`" — "**Examples … arise when considering decoherence in
  models of coupled qubits**", ref 47): the IF "will **not factorize into pairwise separable form** … one
  needs to work with the non-pairwise separable IF" (App E). Sequential per-interaction inversion "**will not
  be possible** … since the correlation terms make this procedure underdetermined"; correlation term =
  geometric-mean spectral density `√(J_j(ω))√(J_k(ω))`. "A detailed analysis is **left for future work**."
- **Class 4** ("No terms in `{Ŝ_j}` commute and each … not diagonalizable" — Anderson impurity / SIAM):
  fermionic, Grassmann path integral, "the discretized IF will **not take a pairwise form** … we only show
  the **formal** relationship … which is algebraic in structure. Future work will focus on finding a geometric
  and diagrammatic structure" (App F).

**Verdict on the 2-1 split (settled from the text) [ours]:** The clean, exact, *invertible* NZ↔IF equivalence
with the Dyck-path combinatorics is a **single-central-N-level-system, simultaneously-diagonalizable-coupling,
Gaussian-bath (Class 1)** theorem. "N is formally arbitrary" is TRUE but refers to the **local dimension of
the one central system** — the cost carries the multiplicative `N_dim` factor per timestep (Eqs. cost
`O(N·2^{N_dim})`; each `K_N` order sum runs over system-basis indices `j,k,n,p,…`). So embedding a
**composite** of `s` sites into "one N-level system" is formally allowed but pays `N_dim = Π_i d_i` =
**exp(sites)** — exactly the wall it is claimed to be. And crucially, **the physically interesting
multi-site case for QEC — spatially-distributed sites, each with its OWN local bath, and/or a shared
(spatially-correlated) bath — is precisely Classes 2/3, where the paper states the IF is no longer pairwise
separable, the Dyck structure and clean inversion are LOST, and the analysis is "left for future work."**
The paper gives **no** treatment of spatially-correlated baths across distinct sites beyond the
"decoherence in coupled qubits ⇒ Class 3" pointer (ref 47) that it does not solve.

## The MECHANISM (for implementation) [paper → ours]
Not a noise *mechanism* — a **representation-conversion + learning apparatus**. What one could implement:
1. **`K_N` ↔ `{I_k}` converter** (Eqs. 7–10 forward; Eqs. 12–14 + Dyck "move crest, divide" inverse) —
   exact for a single N-level system with commuting (simultaneously diagonalizable) couplings to Gaussian
   baths. Requires: bare double-step propagators `G`, `F=GG`; the pairwise influence functions `I_{k,ij}`.
2. **The learning pipeline** `ρ → U → K → I → η → J(ω)` (Eqs. A72–A86): from `N_L` linearly-independent
   reduced trajectories, recover the propagator superoperator, then the memory kernel, then the influence
   functions, then the pairwise coefficients, then the bath spectral density — **using only reduced-system
   observables + knowledge of `Ĥ_S`** (an alternative to noise spectroscopy).
3. **`T`↔`K` / process-tensor bridge** (Eq. 16): `T` = pure influence tensor; `T·P → K`, whereas
   process-tensor `·P → U`. A recipe to move between a learned MZ kernel and a PT/IF object.
Repo: we have **no** NZ-kernel or process-tensor carrier module implementing this; nearest neighbors are the
non-Pauli/leakage MPS-MCWF carrier (`src/qec_twin/forward/scalable/mps_forward.py`) and the C1 composed
DEM/HMM+window carrier — neither is a memory-kernel/IF object.

## The OBSERVABLE / metric [paper]
- The recovered **bath spectral density `J(ω)`** is the terminal learned object; convergence measured by
  agreement of extracted `J(ω)` / `η_{Δk}` / `‖Ĩ_N‖` / `‖K_N‖` with analytic/HEOM references (Figs 2,3,6,11,12).
- **Operator norms `‖Ĩ_N‖`, `‖K_N‖` vs `NΔt`** are the diagnostic: their (typically exponential) decay rate
  = the truncation order needed = tied to the bath correlation-function decay. Slow-decay regime = strongly
  coupled subohmic (`s=0.5`), where truncation ≤16 fails to converge.
- **Statistic flagged INSUFFICIENT / lossy:** the `K↔I` map is **not bijective** at (a) nodal frequencies
  `ωΔt/2=nπ` (null kernel — `J(ω)` there is unobservable in reduced dynamics) and (b) pure-dephasing
  (off-diagonal `I` unrecoverable; only `Re η`). Only the `J(ω)`-content that **touches the reduced dynamics**
  is learnable — an explicit identifiability limit.

## Findings + numbers [paper]
- Exact `K_N`↔`{I_k}` for Class 1, verified: Dyck-constructed `K_N` matches transfer-tensor-postprocessed exact
  HEOM `K_N`; inverse-map `Ĩ_N` up to **N=16** matches analytic `Ĩ_N` (Fig 2).
- `#terms(K_N) = C_N`: 1,2,5,14,42,132,429,1430,4862,16796,58786,…; cost `O(N·2^{N_dim})`, super-combinatorial.
- Regimes (spin-boson, `Ĥ_S = εσ_z + Δσ_x`, `σ_z` coupling, `J(ω)=(ξπ/2)ω^s/ω_c^{s-1}e^{-ω/ω_c}`,
  Eq. 17): Ohmic `s=1`, `ξ=0.1/0.5` → rapid `Ĩ_N`,`K_N` decay, low-order truncation converges (Fig 3 a1,b1);
  subohmic `s=0.5`, `ξ=0.5` → slow (exponential-but-long) decay, needs order >16 (beyond their implementation).
- Learned `J(ω)` recovers even **highly structured** spectral densities (Brownian/Lorentzian multi-peak,
  Fig 12) and **fermionic** flat-band-with-smooth-edge baths (Fig 6), at high Dyck order (20–40, going
  `I→η→J` directly since `K→I` is infeasible that high).
- Reference solver = **free-pole HEOM** (AAA rational fit of the noise spectrum → sum-of-exponentials bath
  correlation, Eqs. A125–A126), evolved with a **two-site TEBD on an MPS of the ADO hierarchy** with a
  swap-network (star→chain) giving `O(K)` two-site updates/step (App G, Fig 8); cross-checked vs i-QuAPI.

## Limitations [paper]
- **Single central N-level system, simultaneously-diagonalizable (commuting) couplings, Gaussian baths
  (Class 1)** is the only regime with the exact Dyck equivalence + clean inversion. Isserlis/Wick (Eq. A13)
  needs Gaussian baths; non-Gaussian ⇒ must keep cumulants beyond 2nd order (inversion then "approximates an
  anharmonic environment by a harmonic one," App A B).
- **Multi-bath is only additive, or otherwise sequentially/underdetermined** (App C G): joint multi-bath `η`
  is underdetermined; per-bath recovery needs prior access to all-but-one bath's dynamics.
- **Non-commuting / non-additive / common-bath / non-diagonalizable couplings (Classes 2–4) are open:** IF
  loses pairwise separability, Dyck structure and clean inversion are lost, only formal/algebraic relations
  shown; **coupled-qubit decoherence is explicitly Class 3 and unsolved** ("left for future work").
- **Cost:** exponential/super-combinatorial in memory order N (`C_N` terms, `O(N·2^{N_dim})`); high orders
  (>~16) infeasible in their implementation. `T=0` at zero coupling; Trotter `O(Δt³)` error per step.
- Process-tensor link is stated as "**appears to be related**" + a non-trivial rearrangement — an informal
  bridge, not a fully worked isomorphism.

## Relevance to qec_twin (twin / non-Markovian coupling program) [ours]
Directly on-target for two live threads: (i) the **process-tensor / influence-functional carrier** candidate
and (ii) the **Mori/Nakajima–Zwanzig memory-kernel closure** candidate for the non-Markovian source
(`project-coupling-nonmarkovian-is-the-contribution`, `project-nonmarkovian-wedge-must-be-coherence`).

**What the unification BUYS us (the practical answer):**
- **Yes, in principle a learned MZ kernel `K` ↔ a process-tensor/IF object are inter-convertible** — same
  influence content, `T·P→K` vs PT`·P→U`, related by Eqs. (7)–(16). So the "MZ-kernel closure" and the
  "PT carrier" are **not two independent ingredients** at the single-central-system level — they are two
  encodings of the same influence data. Choosing one does not forfeit the other's diagnostics.
- **A concrete Hamiltonian-learning template:** `ρ → U → K → I → η → J(ω)` from reduced trajectories + `Ĥ_S`
  alone. This is exactly the shape of a twin "recover the environment from observations" claim, WITH a built-in
  honest identifiability caveat (null-kernel frequencies + pure-dephasing off-diagonal loss) — useful as a
  literature anchor for our bands/UQ discipline.
- **A rigor lever:** any INFPI/QuAPI-style memory-length truncation we adopt has an *exact* memory-kernel
  reading (Eq. 11), so a truncation is not an unbounded simplification — it maps to a definite Dyck-content
  drop we can name and (in principle) bound. Supports FAITHFULNESS_PROTOCOL rule III.

**The CORRECTION this paper forces (critical):**
- **It does NOT let us cheaply COMPOSE a memory-kernel closure with a process-tensor carrier across MULTIPLE
  coupled QEC sites.** The equivalence is exact only for **one** central system with **commuting** couplings
  to Gaussian baths. Our target — spatially-distributed data/ancilla qubits, each with local baths and/or a
  **shared/spatially-correlated bath (TLS / 1/f / shared-bath — our stated non-Markovian "contribution")** —
  is **Class 3** (common bath, coupled qubits, ref 47) or **Class 2** (non-commuting site couplings), both of
  which this paper leaves **unsolved** (IF non-separable, no Dyck structure, inversion underdetermined, "left
  for future work"). Embedding the composite as one big N-level system to stay in Class 1 costs
  `N_dim = Π d_i` = **exp(#sites)** — the identifiability + combinatorial `C_N` cost stack on top of an already
  exponential per-step factor. So: **the "two candidate ingredients are formally equivalent" claim is true but
  scoped to the single-system Gaussian regime; it does NOT deliver a tractable composition rule for the
  multi-site coupled regime we actually care about.**
- Corrects any assumption that "pick MZ-kernel OR process-tensor, they're the same" transfers to our
  distributed setting: the equivalence itself is what breaks (not just the cost) once site couplings don't
  commute or share a bath.

## RELEVANCE verdict (blunt) [ours]
- **Does it let us compose memory-kernel closure with a PT carrier?** For a **single** effective system
  coupled to Gaussian bath(s): **yes** — they are inter-convertible encodings (Eqs. 7–16), and we can pick the
  cheaper representation without losing the other's content or the `J(ω)`-learning pipeline. For the
  **multi-site spatially-correlated QEC** target: **no** — that is Class 2/3, where the paper shows the clean
  equivalence, Dyck combinatorics, and unique inversion all **fail** and are unsolved.
- **Trade-off / cost:** even in-scope, building `K_N` is `O(N·2^{N_dim})` with `C_N` Dyck terms and practical
  order ≲16; inversion is (super)combinatorial and only "nearly bijective" (null-kernel + dephasing gaps).
  Composing across `s` sites via the single-system embedding is `exp(s)`. Net: adopt this as the **theory
  anchor + honest-identifiability template for a single-effective-system arm**, and treat the multi-site
  coupled regime as an **open problem this paper explicitly defers**, not a solved composition we can build on.

## How to use / trust + open questions [ours]
- **Trust:** full-text 精读; all equations transcribed from the extracted txt (figures not pixel-read —
  figure claims = captions/text). Published Nat. Commun. peer-reviewed. High trust on the Class-1 theorem and
  the explicit Class-2/3/4 "unsolved / future work" disclaimers (both quoted verbatim above).
- **Open questions for us:** (1) Is the single-effective-system arm (bath = our shared TLS/1/f source folded
  into one Gaussian bath on a lumped system) rich enough to carry the QEC coupling wedge, or does folding
  destroy the very spatial correlation that is our contribution? (2) Can the `T`↔PT bridge (Eq. 16) be made
  a concrete converter in our stack, or is the "non-trivial rearrangement" prohibitive? (3) For Class 3
  (coupled-qubit common bath, ref 47) — the exact place our program lives — is there any tractable
  approximate closure, given the paper leaves it open? GT-feasibility: the `ρ→…→J(ω)` inversion is
  reproducible at d=1-system, Gaussian bath, HEOM-referenced; **not** demonstrated for any multi-site case.
