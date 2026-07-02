# Reading note: Crow & Joynt, "Classical Simulation of Quantum Dephasing and Depolarizing Noise"

Provenance: FULL-TEXT read (all 11 pages) of the extracted plaintext at
`outputs/papers/1309.6383.txt`. Every load-bearing claim below carries a short verbatim ASCII
quote and its `===== PAGE N =====` marker. Ligatures (ﬀ/ﬁ) and hyphen line-breaks in the source
were avoided by quoting clean ASCII fragments only.

---

## Metadata [paper]

- **Title (arXiv title differs from prompt):** the paper's own title is "Classical simulation of
  quantum dephasing and depolarizing noise" [paper, PAGE 1: "Classical simulation of quantum
  dephasing and depolarizing noise"]. (The prompt gave "Classical Simulation of Quantum Noise";
  the actual title names dephasing + depolarizing explicitly — this is itself the scope signal.)
- **Authors:** Daniel Crow and Robert Joynt, Physics Department, University of Wisconsin-Madison
  [paper, PAGE 1].
- **Ref:** arXiv:1309.6383v2 [quant-ph], 23 Apr 2014; published PRA 89, 042123 (2014).
- **PACS:** 03.65.Yz, 03.67.Lx, 42.50.Lc [paper, PAGE 1].
- **Funding:** DARPA-QuEst Grant No. MSN118850 [paper, PAGE 10].

---

## Executive summary [paper]

The paper asks which system-bath (SB) open-quantum-system models can be reproduced *exactly* by a
qubit subjected to a **classical random c-number field** (random-unitary / random-classical, "RC")
with no bath at all, and — beyond existence — how to **construct** that classical field explicitly.

- **In scope (provably classically simulable):** (i) single-qubit **pure dephasing** by an
  arbitrary quantum bath; (ii) a restricted **multi-qubit "generalized dephasing"** class obeying a
  transitivity condition; (iii) the **depolarizing channel** on a qudit of arbitrary dimension.
  [paper, PAGE 1 abstract: "For a general dephasing model and a single qubit system, we explicitly
  construct the noise functional"; "depolarizing quantum models can be simulated classically for
  all dimensionalities".]
- **Out of scope / explicitly NOT simulable:** any process with an **affine (non-linear) map on the
  ordinary Bloch vector** — i.e. any channel that moves the fixed point / changes populations. Their
  worked counterexample is a qubit **cooled by a bath** (thermal relaxation / energy exchange, i.e.
  T1-type amplitude damping). [paper, PAGE 3: "a qubit initially in equilibrium at high temperature
  that is cooled by a bath ... cannot be mimicked by classical external noise in the sense of random
  unitary evolution".]
- **Method:** reduce "is this model classical?" to "can the qubit transfer matrix `T^(Q)` be written
  as a **convex combination of orthogonal matrices**" (a random-unitary decomposition). For pure
  dephasing they show `T^(Q)` is always a convex sum of two 2D rotations and give both fields
  `h1(t)`, `h2(t)` in closed form.
- **Demonstrations:** spin-boson (exact), central spin (approximate), quantum impurity (numerically
  exact, with a classical↔quantum phase crossover).

---

## Method (deep) [paper]

### Single-qubit dephasing setup
Total Hamiltonian [paper, PAGE 2, Eq. 1]:

```
H = HS[σi] + HB[λi] + HSB[σi, λi]                        (1)
```

Dephasing is *defined* by the commutation condition
[paper, PAGE 2: "We will focus on dephasing models, defined as those for which [HS, HSB] = 0."].

Density matrix expanded on Pauli⊗bath basis [paper, PAGE 2, Eq. 2]:

```
ρ = Σ_ij  Nij σi ⊗ λj                                    (2)
Nij = (1/2) Tr[(σi ⊗ λj) ρ]
```

**Product initial state assumed** — flagged as essential and open to relax
[paper, PAGE 2: "We assume that the initial ρ is in a product form"; "It is an open question whether
the results below can be generalized to non-product initial conditions."].

The whole qubit dynamics is carried by the **quantum transfer matrix** `T^(Q)` [paper, PAGE 2, Eq. 3]:

```
T^(Q)_ik (t) = Σ_l  Tr[ (σi ⊗ λ0) U (σk ⊗ λl) U† ] m_l    (3)
```

on the 4-component (affine-extended) Bloch vector `n_i = (1, nx, ny, nz)`. The paper stresses that on
the *ordinary* 3-vector this is an **affine** relation, and the affine part is what a classical model
can fail to reproduce [paper, PAGE 2: "if construed as a relation between the usual 3-dimensional
Bloch vectors, it is an affine relation"].

### Classical (RC) model and the reduction to convex sums of orthogonal matrices
Classical dephasing Hamiltonian [paper, PAGE 2, Eq. 4]:

```
HCl = -(1/2) B σz + (1/2) h(t) σz                         (4)
```

with `h(t)` a random c-number field and a probability functional `P[h]`. Averaging gives
[paper, PAGE 3, Eq. 6] a classical transfer matrix `T^(Cl)`. The key structural fact:

```
T^(Cl)_i0 = (1/2) Tr σi = δi0
```

so **the classical model always gives a purely linear (no affine term) Bloch map**
[paper, PAGE 3: "the classical model always gives a linear relation between initial and final
ordinary Bloch vectors— there is no affine term."]. Hence:

> [paper, PAGE 3] "This is another example of the fact that not all quantum models have a classical
> analog."

The reduction (discrete random-unitary form) [paper, PAGE 3, Eq. 7]:

```
ni(t) = Σ_{k,r}  p_r O^(r)_ik (t) n_k(0)                  (7)
```

with `O^(r)` orthogonal and `p_r ≥ 0`, `Σ p_r = 1`. Therefore
[paper, PAGE 3]: "the problem of showing that a quantum noise model is actually classical reduces to
the problem of showing that the matrix `T^(Q)_ik` can be written as a convex combination of
orthogonal matrices." **This is their operational statement of the random-unitary correspondence.**

### Pure-dephasing structure and the explicit construction
Choosing the pure-dephasing Hamiltonian [paper, PAGE 3, Eq. 8]:

```
H = -(1/2) B σz + HB[λi] + HSB[λi] σz                     (8)
```

σz is conserved, and the transfer matrix collapses to a single 2×2 rotation block
[paper, PAGE 4] with `c = T^(Q)_xx = T^(Q)_yy`, `s = -T^(Q)_xy = T^(Q)_yx`, and positivity gives
`c² + s² = r² ≤ 1`. The vector `(c,s)` is split into a convex sum of TWO unit vectors
[paper, PAGE 4, Eq. 13]:

```
r² = c² + s² = [T^(Q)_xx]² + [T^(Q)_xy]² ;   β = √(1 - r²) / r      (13)
```

yielding two rotation angles [paper, PAGE 4, Eq. 14]:

```
Φ1(t) = tan⁻¹[ (s - βc)/(c + βs) ]
Φ2(t) = tan⁻¹[ (s + βc)/(c - βs) ]                        (14)
```

and the two classical fields [paper, PAGE 4, Eq. 15]:

```
h1 = ∂Φ1/∂t + B ,   h2 = ∂Φ2/∂t + B                       (15)
```

with `P[h] = (1/2)δ[h - h1] + (1/2)δ[h - h2]` — a two-history, equal-weight random telegraph-like
field. This is packaged as a **Theorem + constructive proof** [paper, PAGE 4: "Theorem. The dynamics
of the open quantum system given by Eq. (8) can be simulated by the classical noise model ... the
density matrix of the qubit is the same for the two models at all times."].

### The non-injectivity/surjectivity map algebra
They define maps `f: QM → RS` (quantum→system evolution) and `g: CM → RS` (classical→system
evolution). They show `f` is **surjective** (every classical model has a quantum realization; built
via Eqs. 16–18, Gram-Schmidt completion of `U_T`) [paper, PAGE 5], `f` **not injective**, `g`
**not injective**, and — citing prior work — `g` **not surjective** [paper, PAGE 5: "earlier work
[6,7] had shown that g is not surjective."]. "g not surjective" is exactly the statement that some
quantum channels have no classical (random-unitary) analog — the non-unital ones.

### Multi-qubit generalized dephasing (Sec. IV)
Two-qubit dephasing defined again by `[HS, HSB] = 0`; the commuting generators `σi ⊗ σi` are
simultaneously diagonalized in the **Bell basis**, where populations are frozen
[paper, PAGE 7: "the populations of the Bell states remain constant in time"]. Evolution is
`ρij(t) = rij(t) ρij(0)` with `rij(t) = p̃(γij(t))` (Fourier transform of the noise distribution)
[paper, PAGE 8, Eqs. 20–21]. The catch is a **transitivity condition** [paper, PAGE 8]:
`γij(t) = γik(t) + γkj(t)`, which is restrictive. Generalized to n qubits via a set A of `2^n − 1`
commuting Pauli operators [paper, PAGE 8, using the Lawrence-Brukner-Zeilinger partition, ref [14]].
Crucially, not all such models are classical [paper, PAGE 7: "there are multiqubit dephasing models
that cannot be classically simulated [7]"], but the simulable subclass is non-trivial
[paper, PAGE 7: "there are multiqubit dephasing models that can be simulated classically and that
cannot be reduced to independent qubits."].

### N-dimensional depolarization (Sec. V)
Depolarizing channel `ρ(t) = (1 - p(t))ρ0 + p(t)(1/N)I` [paper, PAGE 8]. Classical construction:
Haar-random unitary evolution over SU(N) [paper, PAGE 9, Eq. 25]:

```
ρ(t) = ∫_{SU(N)} e^{-iH_U t} ρ(0) e^{iH_U t} dU           (25)
```

A symmetry argument (conjugation by any V fixing ρ0, then any W at t=1) forces ρ(1) ∝ I
[paper, PAGE 9]. A **finite** classical realization uses the **Clifford group as a unitary 2-design**
[paper, PAGE 10: "It has been shown that C(N) is a unitary 2-design ... averages over the Clifford
group ... are equal to uniform averages over the Haar measure [15-17]."]. For the single qubit an
explicit `nz(t)` is computed [paper, PAGE 9, Eq. 27] with a surprising root near t≈0.77 and limit 1/3.

---

## The MECHANISM (for implementation) [paper -> ours]

To reproduce a pure-dephasing bath by a classical field (no bath), our pipeline would:
1. Compute the qubit's off-diagonal decay: extract `c(t) = Re`, `s(t) = Im` of the decoherence
   factor (equivalently `T^(Q)_xx`, `T^(Q)_xy`). [paper, PAGE 4 definitions of c, s.]
2. Form `r² = c² + s²`, `β = √(1−r²)/r`. [paper, PAGE 4, Eq. 13.] Note `β` is real only while
   `r ≤ 1` (guaranteed by CPTP positivity for a *unital* dephasing map).
3. Build the two angles `Φ1, Φ2` [Eq. 14] and differentiate to get `h1(t), h2(t)` [Eq. 15].
4. Sample `h = h1` or `h = h2` each with probability 1/2; integrate `σz`-only unitaries; average.
   [paper, PAGE 4.] Because `[HCl(t), HCl(t')] = 0` for dephasing, time-ordering drops out
   [paper, PAGE 2/3: "the time-ordering can be dropped"].

This is a **random-unitary (mixture-of-unitaries) construction with exactly two histories** for one
qubit — cheap and exact for the dephasing sector [ours]. For depolarizing, the analogous mechanism is
a Clifford-group / Haar average (a unitary 2-design) [paper, PAGE 10] [ours: this is the *same*
random-unitary idea our carrier already exploits when it Pauli-twirls to a DEM].

**What our code must NOT do with this:** treat `T1`/amplitude-damping/relaxation as if it fell under
this construction. The affine/population-moving part has **no** two-field classical realization here
[paper, PAGE 3 counterexample] [ours].

---

## The OBSERVABLE / metric [paper]

- The equivalence criterion is **exact equality of the reduced qubit density matrix at all times**:
  `ρ^(Cl)_S(t) = ρ^(Q)_S(t)`, equivalently `T^(Cl)_ik(t) = T^(Q)_ik(t)` [paper, PAGE 3]. Not a
  distance or a bound — an identity.
- Load-bearing structural observable: the **affine coefficient** `T_i0`. Quantum: `T^(Q)_i0` can be
  nonzero (affine). Classical: `T^(Cl)_i0 = δi0` (never affine) [paper, PAGE 3]. The *gap between
  these* is the obstruction; the paper does **not** quantify it as a scalar floor (see Limitations).
- For the demonstrations they report the decoherence function `r(t) e^{iφ(t)}` and the resulting
  fields `h1(t), h2(t)` (Figs. 1–2), and `nz(t)` for depolarization (Fig. 3).

---

## Findings + numbers [paper]

- **Spin-boson (exact):** off-diagonals ∝ `e^{Γ(t)}`, `Γ(t) < 0`; ohmic bath gives closed-form Γ;
  fields plotted for `Ωτ = 20` show "initial quadratic decay crossing over to exponential"
  [paper, PAGE 6, Fig. 1].
- **Central spin (approximate):** `Dcs(t) = e^{i arctan(αt) − iBt}/√(1+α²t²)`; one field is a
  Lorentzian `h1 = 2α/(1+α²t²)`, the **other vanishes** `h2 = 0` [paper, PAGE 6]. Exact relation
  `r = cos φ` for all t [paper, PAGE 6]. For a GaAs dot `1/α ≈ 20 µs` [paper, PAGE 6].
- **Quantum impurity (numerically exact):** shows a **classical phase (v ≪ γ)** and a
  **quantum phase (v ≫ γ)** with a crossover; the quantum phase shows coherence oscillations —
  but the fields are always classical [paper, PAGE 7: "There is, however, nothing quantum about the
  fields at any value of v; they are classical noise sources."]. Fig. 2: v=3 (quantum), v=2
  (crossover), v=0.6 (classical).
- **Depolarization (single qubit, N=1 case):** `nz(t) = 1/3 + sin(2πt)/(3π) (t − t³)` [paper, PAGE 9,
  Eq. 27], root near t≈0.77, limit 1/3 [paper, PAGE 9]. Finite realization via Clifford 2-design
  [paper, PAGE 10].
- **Philosophical headline finding** [paper, PAGE 10]: "classical simulation is mainly possible when
  the decoherence arises from phase randomness ... and is more difficult when the decoherence comes
  from randomness in the population of those states". Population-changing noise is the hard/impossible
  case.

---

## Limitations [paper]

1. **Product initial state assumed throughout**, relaxation to correlated initial conditions is left
   open [paper, PAGE 2: "It is an open question whether the results below can be generalized to
   non-product initial conditions."].
2. **No amplitude-damping/relaxation construction is given.** The paper explicitly places
   population-moving / cooling processes OUTSIDE the random-unitary framework, but does **not** treat
   how to simulate them, nor quantify a residual distance/floor (no γ/2-type constant appears)
   [paper, PAGE 3; PAGE 10]. See "attribution" below.
3. **Multi-qubit result is narrow:** the transitivity condition is "quite restrictive"; only a
   subclass of generalized-dephasing models is captured, and known multi-qubit dephasing models
   remain non-simulable [paper, PAGE 7, PAGE 8].
4. Non-injectivity of both `f` and `g` means the SB↔RC correspondence is many-to-many — the classical
   model is not unique [paper, PAGE 4, PAGE 5].
5. Depolarization `nz(t)` overshoots ("proper depolarization ends before t = 1") requiring time
   reparameterization [paper, PAGE 9].

---

## Relevance [ours]

This paper is the **prior-art owner of the "unital / dephasing / depolarizing ⇒ random-unitary
(classically simulable)" fact** for the exact single-qubit dephasing case, WITH an explicit field
construction (not just an existence theorem — that existence part they attribute to Helm-Strunz
[5,7] and Landau-Streater [6]). For our project this bears directly on:

- **Our non-unitality relaxation-floor / γ/2 objects (M2, CGF-probe, meas-off-survives-BY-THEOREM).**
  Crow-Joynt's affine-term argument [PAGE 3] is the *same* structural fact our γ/2 floor rests on: a
  purely random-unitary (unital) qubit map cannot move the Bloch fixed point, so any non-unital
  (population-relaxing / amplitude-damping) part is exactly what random-unitary evolution cannot
  reproduce. **However — see the adjudication below — this paper does NOT quantify that gap.** It
  states the obstruction qualitatively and gives a single existence-level counterexample (cooling),
  no constant, no distance, no γ/2. So Crow-Joynt **owns the qualitative direction** ("relaxation is
  outside random-unitary") but does **NOT** own a *quantified non-unitality floor*.
- **Our Pauli-twirl → DEM carrier.** Their Sec. V (depolarizing = Clifford 2-design average = a
  random-unitary channel) is the textbook justification for why depolarizing/Pauli noise is
  DEM-reducible — consistent with our "coherent-CPTP=DEM-reducible vs leakage=NOT" synthesis.

---

## How to use / trust + open questions [ours]

**Attribution adjudication (the reason this note exists):**

1. **Which channels proven classically simulable?** DEPHASING (single-qubit, arbitrary bath; +a
   restricted multi-qubit class) AND DEPOLARIZING (any dimension). **NOT** amplitude
   damping / energy relaxation / T1. [paper, PAGE 1 title + abstract; PAGE 3 cooling counterexample.]
   IN = phase-randomizing (unital) channels; OUT = population-randomizing / affine (non-unital)
   channels.

2. **Random-unitary correspondence statement & citation.** They state it operationally as "T^(Q) is a
   convex combination of orthogonal matrices" [PAGE 3], not via the abstract "unital qubit channel =
   mixture of unitaries" theorem name. They do **cite Landau & Streater** (Linear Algebra Appl. 193,
   107 (1993), their ref [6]) as the general positive-map basis [paper, PAGE 1: "This is based on
   general results concerning existence of certain positive maps [6]."], and Helm-Strunz [5,7] for
   the one-qubit existence result. **They do NOT cite Tregub or Kümmerer-Maassen by name.** (Landau-
   Streater is the qubit-specific unital⇒mixture-of-unitaries result; that is the theorem in play.)
   Note: the well-known caveat that unital ⇒ random-unitary holds for QUBITS but fails in higher
   dimension is not discussed here — they only need the qubit case for dephasing and use a symmetry
   argument (not unital⇒RU) for depolarizing.

3. **Non-unital obstruction / floor?** They **assert the obstruction qualitatively** (classical/RC
   maps are linear-not-affine, cannot cool, cannot change populations) [PAGE 3, PAGE 10] and cite
   that `g` is "not surjective" [PAGE 5]. They do **NOT** quantify any distance, bound, or γ/2-type
   floor for the non-unital part — there is no such constant anywhere in the paper. **Verdict: they
   do not own a quantified non-unitality relaxation floor; only the qualitative "relaxation is not
   random-unitary-simulable" direction.**

4. **The three paradigmatic models + multi-qubit class:** spin-boson, central spin, quantum impurity
   [PAGE 1, Sec. III], plus the transitivity-constrained multi-qubit "generalized dephasing" class
   [Sec. IV] — all confirmed present and read.

**Trust:** single-qubit dephasing Theorem is exact and constructive (trust as (a) exact). Multi-qubit
result is exact but narrow. Depolarizing (Clifford-2-design) is exact. Everything about relaxation is
qualitative/absence — do NOT cite this paper for any *number* bounding a non-unital floor.

**Open questions for us:** (i) the quantified γ/2 non-unitality floor we use is NOT sourced here — it
must be attributed to whatever paper actually derives the constant (Crow-Joynt only gives the
direction). (ii) Non-product initial conditions (correlated bath) are open in their framework too —
relevant if our coupled/non-Markovian teacher wants classical-simulability claims.
