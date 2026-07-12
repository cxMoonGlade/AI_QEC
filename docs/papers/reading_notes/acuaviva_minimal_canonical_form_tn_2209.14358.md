# Full-text review — A. Acuaviva et al., "The minimal canonical form of a tensor network" (arXiv:2209.14358)

> **Provenance (2026-07-12): FULL-TEXT read (精读) of the ORIGINAL.** PDF (arXiv:2209.14358v1,
> 28 Sep 2022) downloaded fresh and converted with PyMuPDF →
> `outputs/papers/peps_foundation/2209.14358.txt` (**51 pages / 3952 lines**). All §/Eq/Thm/Prop/Fig
> refs below are transcribed from that text, not from any second-hand summary. I read the front matter,
> the GIT preliminaries (§2), the full MPS development (§3, incl. the OBC/Vidal reduction §3.3), the
> full PEPS development (§4, incl. §4.4 tilings and §4.5 "when does one need the orbit closure"), and
> the algorithms (§5.1 first-order Algorithm 1, §5.2 error relations, §5.3 second-order) + the
> Conclusion §6 truncation proposal.
>
> **Verbatim anchors confirmed from the PDF** (guards against inheriting a note's blind spot):
> - Thm 4.8 characterization: "T is in minimal canonical form ... if and only if the reduced density
>   matrices of ρ = |T⟩⟨T| on the virtual bonds are the same in each direction, up to a transpose:
>   ρ_{k,1} = ρ_{k,2}^T" (line 1597-1604).
> - Prop 4.18 (line 2136-2140): "Suppose that there exists T such that S ∈ closure(G·T) but S ∉ G·T,
>   then there exists a nontrivial one-parameter subgroup g(z) ⊂ G ... such that g(z)·S = S."
> - Example 4.21 toric code (line 2239-2251): "This tensor is in minimal canonical form, since all
>   virtual marginals are maximally mixed ... this tensor has a finite symmetry group."
> - Conclusion §6.1 (line 3517-3523): "For two-dimensional PEPS there is no truncation scheme known
>   which has both these desirable properties ... Here, we propose the following natural truncation
>   scheme: given a tensor T, compute its minimal canonical form S. Then truncate to the subspace
>   spanned by the eigenvectors corresponding to the D' largest eigenvalues."
>
> **ID/title verified from the PDF front matter.** arXiv:2209.14358 IS this paper (Quantum 7, 1130
> (2023) in later publication). Title exactly: "The minimal canonical form of a tensor network."

## Metadata [paper]
- **Authors / affiliations:** Arturo Acuaviva (UC Madrid), Visu Makam (Radix Trading Europe,
  Amsterdam), Harold Nieuwboer (KdV Institute / QuSoft, U. Amsterdam), David Pérez-García (UC
  Madrid), Friedrich Sittner (UC Madrid), Michael Walter (Ruhr U. Bochum), Freek Witteveen (QMATH,
  U. Copenhagen).
- **Venue / status:** arXiv:2209.14358v1 [quant-ph], 28 Sep 2022 (later Quantum 7, 1130, 2023).
- **Type:** Pure-mathematics / theory paper. Geometric invariant theory (GIT) applied to tensor
  networks. NO physics benchmarks, NO numerical experiments beyond worked algebraic examples. Its
  deliverables are theorems (existence, uniqueness-up-to-unitary, a fundamental theorem, decidability)
  plus two provably-convergent algorithms for computing the canonical form.

## Executive summary [paper]
The paper defines the **minimal canonical form** of a (uniform) tensor network: the minimum-ℓ2-norm
tensor `T_min` in the **closure of the gauge-group orbit** `\overline{G·T}`, where the gauge group is
`G = GL(D_1) × ... × GL(D_m)` acting on the virtual (bond) legs only (Def 4.6, Eq 1.1). Its three
load-bearing results:

- **Result 1 / Thm 4.7 (canonical form):** every tensor has a minimal canonical form; it is unique up
  to the unitary subgroup `K = U(D_1)×...×U(D_m)`; and two tensors `S,T` share a minimal canonical
  form **iff** their orbit closures intersect (`\overline{G·S} ∩ \overline{G·T} ≠ ∅`), which is the
  natural definition of gauge equivalence.
- **Result 2 / Thm 4.8 (characterization):** `T` is in minimal canonical form **iff** for each spatial
  direction `k` the two virtual-bond marginals of `ρ=|T⟩⟨T|` are equal up to transpose, `ρ_{k,1} =
  ρ_{k,2}^T` (Eq 4.5, Fig 8). This is a *balancing* condition — the 2D analog of Vidal's even
  Schmidt-weight distribution, NOT the usual left/right MPS canonical form.
- **Result 3 / Thm 5.1, Cor 5.16 (computability):** the canonical form IS computable to ℓ2-error δ. A
  practical first-order gradient-descent algorithm (Algorithm 1) and a second-order box-constrained
  Newton method both converge, in time polynomial in `log(1/δ)` and the bitsize of `T` for fixed bond
  dimension — but **exponential in the bond dimension for m>1** (via a norm-lower-bound constant γ
  that can be exponentially small).
- **Result 4 / Thm 4.11 (fundamental theorem):** `S,T` are gauge equivalent **iff** `|S_π⟩ = |T_π⟩`
  for all contraction graphs π — i.e. on **surfaces of arbitrary topology, not just the torus/grid**.
  This makes "do two tensors give the same PEPS on all surfaces?" **decidable**, in stark contrast to
  the known **undecidability** on periodic rectangular grids [SMG+20].

The single most useful section for us is **§4.5 "When does one need the orbit closure?"** — it is the
rigorous statement of *when a bond dimension is larger than the physical entanglement requires and the
excess is removable gauge* (Prop 4.18, Prop 4.20, Examples 4.21–4.23).

## Method (deep) [paper]

### The object (Def 4.3, 4.6; §4.1)
A uniform PEPS tensor is `T = (T^{(i)})_{i=1}^d`, `T^{(i)} ∈ ⊗_{j=1}^m Mat_{D_j×D_j}`, equivalently a
state `|T⟩ ∈ (⊗_k H_{k,1}⊗H_{k,2}) ⊗ H_phys` with two virtual legs per spatial direction and one
physical leg. The **gauge action** (Def 4.3) is
`g·T = ( (g_1⊗...⊗g_m) T^{(i)} (g_1^{-1}⊗...⊗g_m^{-1}) )_i`, i.e. on the state
`g·|T⟩ = ( ⊗_k (g_k ⊗ g_k^{-T}) ⊗ I_phys ) |T⟩`. **The gauge touches only the virtual indices; the
physical index carries `I_phys` untouched.** Lemma 4.4: any `T' ∈ \overline{G·T}` gives the identical
PEPS on every contraction graph, `|T_π⟩=|T'_π⟩` — this is exact and holds through limits.

### GIT engine (§2, Thm 2.3, 2.5 Kempf–Ness)
The minimal canonical form is a *minimum-norm vector* for the reductive group `G` acting on the tensor
space. Kempf–Ness (Thm 2.5): a vector is a min-norm vector in its orbit closure **iff** it is
*critical* (`∂_{t=0}‖e^{tX}·v‖² = 0` for all Hermitian `X ∈ i·Lie(K)`); min-norm vectors form a single
`K`-orbit; two orbit closures intersect iff they share a min-norm vector; a critical orbit is closed
(Lemma 2.6: every orbit closure contains a unique closed orbit). Computing the critical condition for
the PEPS action (Eq 4.4) gives exactly `ρ_{k,1}=ρ_{k,2}^T` (Thm 4.8).

### The MECHANISM (for implementation) — Algorithm 1, first-order (§5.1)
The gauge-fixing objective is
`f_T(g) = ½‖g·T‖²` and its log `F_T(g)=log‖g·T‖`. Key structural fact: on the coset space `K\G`
(nonpositively-curved Riemannian manifold), `f_T` is **geodesically convex** and `F_T` is even
**geodesically log-convex** (§5.1). The gradient at `g=I` is exactly the marginal mismatch
`∇F_T(I) = (1/tr ρ)(ρ_{k,1} − ρ_{k,2}^T)_{k=1}^m` (Eq 5.6). Algorithm 1 is therefore:

```
g ← (I,...,I)
repeat:
    T ← g·T ;  ρ ← |T⟩⟨T|
    if (1/tr ρ) Σ_k ‖ρ_{k,1} − ρ_{k,2}^T‖²_2 ≤ ε²:  return g
    for each direction k:
        g_k ← exp( −(1/4m)(1/tr ρ)(ρ_{k,1} − ρ_{k,2}^T) ) · g_k
```
With the safe step `η = 1/(4m)` (F is 4m-smooth along geodesics), **each iteration strictly decreases
F by ≥ ε²/(8m)** (proof of Thm 5.1), giving a **guaranteed monotone** descent to the global optimum in
`O( (m/ε²) log(‖T‖/‖T_min‖) )` iterations. Prop 5.2 bounds `‖T_min‖ ≥ 1/∏ D_j` for integer-entried
`T`, converting the iteration count to `poly(1/ε, bits)` for fixed `D` (Cor 5.3). The second-order
box-constrained Newton method (Thm 5.15, Cor 5.16) achieves relative ℓ2-error δ in
`poly(γ^{-1}, D_1,...,D_m, log(1/δ), bits)`.

**This is a real, implementable gauge-fixer, not merely an existence theorem.** But note precisely
what it produces: the *balanced canonical form* (marginals equal up to transpose). It is a
**canonicalizer + diagnostic**, NOT a truncator (see next).

### The truncation PROPOSAL (Conclusion §6.1) — explicitly unproven
The paper proposes (but does not prove or test) a truncation scheme: compute the minimal canonical form
`S`, then **truncate to the subspace spanned by the eigenvectors of the D' largest marginal
eigenvalues** — the 2D analog of MPS left-canonical truncation. Crucially the paper states plainly:
"**For two-dimensional PEPS there is no truncation scheme known which has both these desirable
properties** [efficient AND optimal], which is closely related to the lacking of the equivalent of a
left or right canonical form" (line 3517-3519). The minimal-canonical-form truncation is offered as "a
natural" candidate whose usefulness "will require detailed numerical study" (line 3500-3501, 3524-3525)
and it comes with **NO approximation-error bound** in 2D. In 1D/MPS the OBC minimal canonical form
reduces exactly to Vidal's form (§3.3) and there truncation IS optimal (Eckart–Young) — but that
optimality does **not** carry to 2D.

## The rigorous statement about "bond larger than the physical entanglement requires" (§4.5) — THE part we came for

This section is the paper's answer to "is our growing per-edge bond counting removable gauge?"

- **Prop 4.20 (normal/injective ⇒ closed orbit):** if `\overline{G·T}` contains a normal (injective
  after blocking) tensor, then `G·T = \overline{G·T}` is already closed. For such tensors **no orbit
  closure / no limit is needed** — the canonical form is reached by an honest invertible gauge
  `g ∈ G`, and there is **no nontrivial continuous symmetry** collapsing the bond.
- **Prop 4.18 (non-closed ⇒ continuous symmetry):** the orbit closure is genuinely needed — i.e. the
  canonical form is only a *limit* `lim_j g^{(j)}·T` and the reduction sets off-diagonal blocks to zero
  / drops rank — **iff** the canonical form `S` possesses a **nontrivial one-parameter (continuous)
  symmetry** `g(z)·S=S`, `z∈C*`. Example 4.23 makes the mechanism explicit: a one-parameter subgroup
  `h(z)` sends `lim_{z→0} g(z)·S = T` with `rank(T^{(1)}) = 1 ≠ 2 = rank(S^{(1)})` — the excess bond
  literally becomes removable only in the limit, and only because of the continuous symmetry. **This is
  the precise phenomenology of a bond that "over-counts": the excess is removable gauge exactly when a
  continuous virtual symmetry is present.**
- **Example 4.21 (toric code) — directly our regime:** the toric-code PEPS tensor
  `T = ½ I^{⊗4} + ½ Z^{⊗4}` (equivalently `T^{(ijkl)} = |i⟩⟨j|⊗|l⟩⟨k|` for `i+j+k+l` even) **is
  already in minimal canonical form because all virtual marginals are maximally mixed**, and its
  symmetry group is **finite (discrete, ±1)** — NOT a continuous one-parameter subgroup. Example 4.22
  generalizes this to all abelian quantum-double / G-isometric PEPS: for abelian `G` the orbit is
  already closed, `\overline{GL(D)²·T} = GL(D)²·T`. **Consequence for us: a pure stabilizer
  surface-code PEPS is of this closed-orbit, finite-symmetry class — its virtual bonds are NOT
  over-counting removable gauge; the physical bond is genuine.** Growing bond in *our* pipeline is
  therefore NOT explained by this paper's continuous-gauge mechanism; it is a **solver artifact** of
  FET-ALS (as our crux resolution already concluded), not intrinsic removable gauge of the stabilizer
  state.

## Applies to our case? [ours]

**PARTIAL — foundational theorem yes, drop-in tool mostly no.**

- **What genuinely applies.** (i) The gauge action is physical-index-blind and *exactly* state
  preserving through limits (Lemma 4.4) — so any bond content that leaves the physical state invariant
  is, by Thm 4.11, gauge (up to closure). This is the rigorous backing for "excess bond = removable
  gauge" *whenever the two representations produce the same state*. (ii) Thm 4.8's balancing condition
  `ρ_{k,1}=ρ_{k,2}^T` is a well-defined, computable canonical target, and its marginal spectrum is the
  correct diagnostic for how much bond a given cut truly needs. (iii) §4.5 gives the clean dichotomy
  (closed orbit / finite symmetry ⇒ bond genuine; continuous symmetry ⇒ excess removable in the limit)
  that lets us *classify* whether our bond growth is intrinsic or artifact — and it classifies pure
  stabilizer surface code as **closed-orbit / genuine**, consistent with our S_A being bounded and
  exact.
- **What does NOT apply cleanly.** The entire theory is **uniform** (single translation-invariant
  tensor, one `GL(D_k)` per spatial *direction*, contraction on a torus/surface). Our carrier is a
  **finite, open-boundary, non-uniform** d3/d5 surface code with **distinct tensors per site**,
  per-**edge** bonds, and — decisively — **multi-round projective stabilizer measurement** that changes
  the state each round plus **weak non-Clifford leakage**. The uniform per-direction gauge group does
  not map onto a finite heterogeneous per-edge network. The paper's only *finite* development is the
  **OBC/non-uniform MPS** case (§3.3), which just reproduces Vidal's per-bond SVD canonical form; the
  finite **2D** case is not developed. So this is a **theorem we cite + a canonicalizer/diagnostic we
  can adapt**, **not** a finished finite-2D truncator.

## Cost at d3/d5 on one RTX 5090 [ours]
- **Per-tensor gauge fixing (Algorithm 1) is cheap in our regime.** Each iteration forms the two
  virtual marginals of a single PEPS tensor (rank `2m+1`, bonds `D∈{~4 (d3),~8–16 (d5)}`, physical
  `d=2` or 3 with leakage): `O(d·D^{2m})` per marginal, i.e. `~D^4` per site in 2D — negligible
  (microseconds–ms) on a 5090. A canonicalizing sweep over all d3 (q17) / d5 sites is seconds.
- **The theoretical worst case is bad but is not our operating point.** The *rigorous* convergence
  guarantee (Cor 5.16 / second-order) scales `poly(1/γ)` with `γ` (Def 5.4) potentially
  **exponentially small in the bond dimension** for `m≥2` (Prop 4.15 shows the exp-in-`D` dependence in
  the fundamental theorem is unavoidable). For our small bonds (`D ≤ 16`) this is not triggered in
  practice, but there is **no sub-exponential worst-case bound** — cost is empirically cheap, not
  provably-cheap-in-`D`.
- **Caveat:** these are single-tensor costs. Applying the method to the finite surface-code network
  requires an adaptation (per-edge / boundary-MPS sweep) the paper does not specify; the cost of *that*
  wrapper is on us, not bounded by the paper.

## Reliability vs our FET-ALS [ours]
**This is the paper's strongest offer — but only for the gauge-fixing sub-problem, not for truncation.**
- The gauge-fixing objective `F_T(g)=log‖g·T‖` is **geodesically (log-)convex** with a **global**
  minimum unique up to unitary (Kempf–Ness). Algorithm 1 is **monotone by construction** — F strictly
  decreases ≥ε²/8m each step (proof of Thm 5.1) — and **convergence is guaranteed**. It uses matrix
  exponentials of Hermitian marginal-mismatches, **no pseudo-inverse**. This is the exact structural
  opposite of our FET-ALS, which is **non-monotone** and **pinv-divergent on over-parameterized /
  long-range bonds**. So as a *canonicalizer / metric-balancer / removable-gauge diagnostic*, it is
  deterministic, monotone, and convergence-guaranteed where ALS is not.
- **HONEST LIMIT:** the convexity/monotonicity is for finding the *balanced canonical form*, **not for
  the bond truncation**. The paper supplies **no monotone 2D truncator and no 2D truncation error
  bound** (it explicitly flags 2D optimal truncation as an open problem, §6.1). It therefore does **not**
  by itself replace the truncation step of our pipeline with a guaranteed-reliable one — it replaces the
  *gauge/metric* part and hands us a principled spectrum to truncate on, with optimality unproven.

## leakage_interaction [ours]
**Gauge-fixing: safe (cannot corrupt physical S_A). Truncation-on-top: a real risk to flag.**
- The gauge acts as `⊗_k(g_k⊗g_k^{-T}) ⊗ I_phys` (Def 4.3) — **physical-index-blind and exactly
  state-preserving** (Lemma 4.4). Weak non-Clifford leakage lives entirely in the physical index (the
  |2⟩ qutrit level / non-stabilizer magic). The canonicalizer therefore **neither sees nor cuts the
  leakage (non-stabilizer) directions**; it cannot alter the physical reduced state or the true
  bipartition entropy `S_A`. In this sense leakage_interaction for the *gauge fix* is benign — closer
  to "N/A, by construction safe" than to a hazard.
- **BUT the proposed truncation step (drop smallest canonical-form marginal eigenvalues) is NOT
  state-preserving and CAN cut leakage.** If a weak-magic / leakage direction contributes a **small
  Schmidt weight** on a cut, a naive "keep the `D'` largest eigenvalues" truncation will preferentially
  **discard exactly the low-weight non-stabilizer direction that carries the leakage physics**,
  corrupting the physical `S_A` / the leakage signal. This is the same failure mode we already flagged
  generically (dropping smallest weights kills weak non-Clifford directions), and this paper's
  truncation proposal does nothing to protect against it — it truncates purely on marginal-eigenvalue
  magnitude, with no non-stabilizer-aware weighting. **So: adopt the canonicalizer freely; guard the
  truncation with a leakage-aware retention rule (never drop a non-stabilizer direction on magnitude
  alone), or it will silently erase the leakage we are trying to simulate.**

## Relevance to qec_twin [ours]
- **FORK A (deterministic loop-truncation replacing ALS):** this paper is the **root-(a) theorem
  foundation** and a **reliable canonicalizer + diagnostic**, but it is **not itself the loop
  truncator**. It rigorously certifies (Thm 4.11 + §4.5) that bond content leaving the state invariant
  is removable gauge, and it classifies the pure stabilizer surface code as **closed-orbit / genuine
  bond** (Ex 4.21/4.22) — which *confirms* our crux resolution (S_A bounded/exact; our ALS bond growth
  is a solver artifact, not intrinsic gauge). Its marginal spectrum `ρ_{k,1}=ρ_{k,2}^T` is the correct,
  deterministic, monotone-to-compute quantity to *diagnose* solver-failure vs genuine long-range
  physics — precisely the role our memory earmarks for the Evenbly-2018 WTG gauge-fixed canonical
  spectrum. **Use it to complement, not replace, Evenbly-2018:** Acuaviva gives the rigorous
  "removable-gauge iff continuous-symmetry" underpinning + a globally-convergent gauge fixer; Evenbly
  gives the practical loop/WTG gauge fix. The Acuaviva canonicalizer could serve as the deterministic
  PRIMARY gauge step, with its balanced marginal spectrum as the truncation diagnostic.
- **FORK B (stabilizer-frame carrier):** consistent with — Ex 4.21/4.22 say the stabilizer PEPS bond is
  genuine and finite-symmetry, i.e. its "extra" bond beyond leakage magic is not removable gauge, which
  is the exact premise a stabilizer-frame carrier exploits (bond tracks only leakage magic on top of a
  cleanly-canonical stabilizer frame). This paper does not build such a carrier but its classification
  supports the premise.
- **What it does NOT give us:** a finite-2D optimal truncation with an error bound (open problem, by
  the paper's own statement); a measurement-aware or leakage-aware truncator; anything specific to
  finite open-boundary heterogeneous networks. Those remain our engineering.

## Limitations [paper]
- **Uniform / translation-invariant only.** Single tensor, one `GL(D_k)` per direction, torus/surface
  contraction. Finite 2D open-boundary non-uniform networks are out of scope (only OBC-MPS §3.3 is
  finite, and that just recovers Vidal).
- **No numerics, no physics benchmark.** All examples are algebraic (GHZ, single-matrix Jordan form,
  toric code, the rank-drop Ex 4.23). Usefulness of the truncation proposal is explicitly left to
  future work (§6, line 3500-3501, 3524-3525).
- **Exponential-in-bond-dimension guarantees for m>1** (γ can be exp-small; Prop 4.15 shows the
  exp-in-`D` fundamental-theorem system size is unavoidable).
- **The truncation scheme (§6.1) is a PROPOSAL with no 2D approximation-error bound.** The paper states
  outright that no efficient-and-optimal 2D PEPS truncation is known.
- **Balancing ≠ rank reduction.** The canonical form makes marginals equal-up-to-transpose; it does not
  by itself certify that the bond can be reduced to match `S_A`. Rank/optimality of any subsequent
  truncation is unproven in 2D.

## Epistemic-status declaration [ours]
- **(a) exact (theorem-grade, citable as premise):** Thm 4.7 (existence + uniqueness up to unitary +
  gauge-equivalence characterization); Thm 4.8 (`ρ_{k,1}=ρ_{k,2}^T` characterization); Thm 4.11
  (fundamental theorem on all contraction graphs) + decidability; Prop 4.18 & 4.20 & Examples 4.21/4.22
  (closed-orbit / continuous-symmetry dichotomy, incl. toric-code-in-canonical-form); Thm 5.1 monotone
  convergence of Algorithm 1; Cor 5.16 poly-time computability. These are proved theorems in a
  peer-reviewed paper; usable as premises.
- **(b) prediction band:** none registered here — the paper makes no falsifiable numerical bet.
- **(c) heuristic gate / decision rule (NOT a premise):** the §6.1 truncation proposal ("truncate to
  the `D'` largest canonical-form marginal eigenvalues") — offered as natural, **unproven in 2D**, no
  error bound. Any use of it in our pipeline is a heuristic gate only. Likewise the [ours] cost
  estimates for d3/d5 are back-of-envelope (c)-class, not measured.
- **Provisional corollary:** "Acuaviva canonicalization can replace our FET-ALS truncation" is
  **FALSE as stated** — it can replace the gauge/metric sub-step (theorem-grade) but the *truncation*
  remains an open problem; do not build a truncator on §6.1 as if it were (a).

## How to use / trust + open questions [ours]
- **Trust:** FULL-TEXT 精读 of the original 51-page PDF; all load-bearing claims anchored to verbatim
  lines above. Peer-reviewed (Quantum 2023). High baseline trust for the *theorems*; the *truncation
  application* is self-described as speculative.
- **How to use:** (1) Adopt the Kempf–Ness gauge-fixer (Algorithm 1) as a **deterministic, monotone,
  pinv-free canonicalizer** to replace the non-monotone gauge/metric part of FET-ALS; (2) use the
  balanced marginal spectrum `ρ_{k,1}=ρ_{k,2}^T` as the **diagnostic** that separates solver-failure
  (excess bond that the canonical spectrum reveals as low-weight) from genuine long-range physics; (3)
  cite §4.5 (Prop 4.18/4.20, Ex 4.21) as the **rigorous certification** that our stabilizer surface
  code is closed-orbit / finite-symmetry, so bond growth is artifact not intrinsic gauge — the theorem
  backing for our crux resolution; (4) do **NOT** adopt §6.1 truncation as a reliable truncator, and if
  used at all, **wrap it with a non-stabilizer-aware retention rule** so weak leakage directions are
  never dropped on eigenvalue magnitude.
- **Open questions for us:**
  1. Finite, open-boundary, heterogeneous adaptation: the uniform single-tensor gauge fixer must be
     turned into a per-edge / boundary-MPS sweep for a finite d3/d5 network — cost and convergence of
     that wrapper are unproven here.
  2. Measurement interaction: multi-round projective stabilizer measurement changes the state each
     round; the canonical form must be recomputed per round — how does that compose with a trajectory
     loop, and does the balancing stay cheap?
  3. Leakage-aware truncation: can the marginal-eigenvalue truncation be reweighted so non-stabilizer
     (leakage) directions are protected? The paper offers nothing here.
  4. Relation to Evenbly-2018 WTG (still to be read): is the Acuaviva balanced canonical form the same
     fixed point as Evenbly's loop/WTG gauge fix, or a different one? (Thm 4.8's `ρ_{k,1}=ρ_{k,2}^T`
     "differs from previously proposed heuristics", line 1608-1612 — so likely a *different* fixed
     point than [PMV15]/[Eve18], which must be checked before treating them as interchangeable.)
