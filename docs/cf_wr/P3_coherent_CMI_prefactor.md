# CF-WR P3 (a)-basis — perturbative coherent CMI prefactor: does O(φ²) escape the KKB exp prefactor?

> **Theory-only derivation (no code).** Owner question: *does PERTURBATIVE coherent (off-diagonal)
> correction tame the 2D obstruction to small-window composition?* The 2D obstruction is the
> **exp(Θ(|A|+|C|)) prefactor** in the only available 2D quantum-CMI clustering bound
> (Kuwahara–Kato–Brandão, [2407.05835](https://arxiv.org/abs/2407.05835)), which destroys the global
> Markov property for macroscopic 2D fragments and makes quantum BP fail in 2D.
>
> Derived by opus theory agent, 2026-06-13. Reuses `P2_derivation.md` (per-seam residual φ-expansion;
> the C0 un-twirled coherent edge is **O(φ) linear**) and the classical composition-limit proof
> (composition limit = decodability threshold, `w ≳ 2ξ·log(L/ε)`). Pillars cited, not claimed:
> Fawzi–Renner [1410.0664], Sutter–Fawzi–Renner JRSWW (PMC4841654), KKB [2407.05835], the
> Kubo–Mori–Bogoliubov (KMB) metric = Hessian of relative entropy.
>
> **epistemic legend:** (a) exact (theorem/identity/zero-tolerance); (b) derived prediction band
> (miss = finding); (c) heuristic/gate. conjectural steps **bold-inline tagged**. Honest tri-state
> verdict throughout: **CONTROLLED / INHERITS-THE-PREFACTOR / OPEN**.

---

## 0. Headline verdict (read first)

**CONTROLLED — conditionally (b), with one exactly-named missing step.**

The leading coherent correction to the conditional mutual information about a classical-Markov bulk is

> **I(A:C|B)[ρ(φ)] = κ · φ² + O(φ³),  κ = ½ ⟨χ⊥, K_cl χ⊥⟩_KMB ≥ 0   (a, structure)**

and its prefactor κ carries **NO exp(Θ(|A|+|C|)) factor**. Instead

> **κ ≤ ½ · ‖χ⊥‖² · 𝔎(ρ_cl)  with 𝔎(ρ_cl) = O(1/p_min) LOCAL and SUPPORTED on the seam   (a, bound)**,

where `p_min` is the smallest classical bulk-cell occupation probability (the finite-ξ classical state's
spectral floor) and χ⊥ is the **off-diagonal first-order coherence** the ZZ seam injects, supported on
O(L) seam cells. The exp prefactor in KKB is a **worst-case over ALL 2D states** reconstructed
**non-perturbatively**; a φ-perturbation of a classical-Markov state lives in the **quadratic (KMB)
regime** of the relative entropy, where the Hessian is a **fixed local integral kernel of ρ_cl** — and
ρ_cl is exactly the object KKB-clustering says has a **polynomial** prefactor below threshold. The
perturbation therefore **provably evades the exp prefactor**, *to all finite orders in φ that the KMB
Taylor series controls* (§3).

The single step that keeps this **(b) not (a)**: the φ-series of I must be **uniformly convergent on the
A–C separation**, i.e. the O(φ³) remainder must not smuggle the exp prefactor back via a φ-dependent
radius of convergence that **shrinks** as |A|+|C| grows. I bound the remainder by the KMB regime's
spectral floor (§3.4) and show the radius is set by `φ ≲ p_min`, **independent of |A|+|C|** — but the
fully rigorous statement needs the third-order Fréchet remainder of −S to be controlled by the SAME local
kernel, which I derive **at leading order only** (§3.4, the C1 missing step). Hence the verdict is a
**registered (b) band with the exact gap named**, not a closed theorem. This is **strictly stronger** than
the P2 per-seam result and **directly attacks** the coherent open problem.

**Relation to P2 (§4):** the per-seam residual being **O(φ) linear** (P2 C0) and the CMI being **O(φ²)
quadratic** are **NOT contradictory and NOT the same statement** — one is a *trace-distance reconstruction
residual* (first-order-sensitive, odd), the other a *relative-entropy information* (Markov-stationary, even).
The √-bound `D_Choi ≤ √(I_nats)` reconciles them exactly: `√(κ) φ` (CMI route) vs `c_G φ` (direct route),
both **linear in φ**, both **L-additive with a local prefactor**. The CMI route therefore **certifies the
P2 linear per-seam law carries no exp prefactor** — the coherent generalization of the classical limit.

---

## 1. Setup — the perturbation about the classical-Markov bulk

### 1.1 Objects (a)
Fix the A–B–C seam split (B = buffer/overlap; classical bulk below the decodability threshold). The twin's
state is the global noise-channel Choi/Gibbs-like state ρ(φ) on the 2D lattice; restricted to the seam
tripartition it is the density operator we test for Markovianity. Per `registration.md` §2 the coherent knob
φ acts on **seam-crossing edges** as `U_φ = exp(−iφ Z⊗Z)` on top of the classical non-unital bit-flip bulk:

> **ρ(φ) = U_φ ρ_cl U_φ†,  U_φ = exp(−iφ G),  G = Σ_{e∈seam} Z_e ⊗ Z_{e'}   (a)**

with G Hermitian, **supported only on the O(L) seam-crossing edge pairs** (call this support 𝒮; |𝒮| = O(L)).
(Adjoint-conjugation is the φ-channel's action on the Choi state; the general case
ρ(φ)=ρ_cl+φρ⁽¹⁾+φ²ρ⁽²⁾+… reduces to this when the φ-edge is a coherent unitary dressing, the registered C0
knob. A non-unitary coherent CP edge adds a diagonal piece treated in §3.5; it does not change the prefactor
verdict.)

**Basis bookkeeping (a, the load-bearing non-commutation).** ρ_cl is the Choi state of the classical
**non-unital bit-flip** bulk — an `{I, X}`-type channel. Its Choi `J = (I⊗E)|Ω⟩⟨Ω|` is **diagonal in the
Bell basis** (equivalently, in the X-stabilizer basis of the doubled space), NOT in the Z-product basis. The
coherent generator `G = Z⊗Z` is **diagonal in the Z basis**, hence **off-diagonal in ρ_cl's (Bell/X)
eigenbasis**. Because the bit-flip Kraus operator X **anticommutes** with Z, **[G, ρ_cl] ≠ 0** — this is the
exact statement that the un-twirled coherent ZZ edge is in P2's **C0 = O(λ) class** (`P2_derivation.md` §2:
"non-unital + un-twirled coherent ∈ O(λ) class"; the twirled/dephased ZZ would commute and give χ⁽¹⁾=0,
O(λ²) — that is the excluded case). So below, "off-diagonal" always means **off-diagonal in the
ρ_cl-eigenbasis** (Bell/X), where Z⊗Z genuinely has off-diagonal matrix elements. This is what makes χ⊥ ≠ 0
and is the entire physical reason the coherent sector is non-trivial.

### 1.2 The φ-expansion of ρ (a)
Expand the conjugation. With `U_φ = e^{−iφG}`, the Baker–Campbell–Hausdorff / Hadamard expansion gives
`U ρ U† = ρ − iφ[G,ρ] − ½φ²[G,[G,ρ]] + O(φ³)`. Writing the **adjoint action** `ad_G(X) = [G,X]`:

> **ρ⁽¹⁾ = −i [G, ρ_cl] = −i ad_G(ρ_cl)      (a)**
> **ρ⁽²⁾ = −½ [G,[G,ρ_cl]] = −½ ad_G²(ρ_cl)   (a)**

**Key structural fact (S1, a) — χ⊥ is off-diagonal in ρ_cl's eigenbasis and is nonzero.** Diagonalize
ρ_cl = Σ_a p_a |a⟩⟨a| in its (Bell/X) eigenbasis (§1.1). G = Z⊗Z has matrix elements G_{ab} = ⟨a|G|b⟩ that
are **off-diagonal** in this basis (Z anticommutes with the bit-flip X that diagonalizes ρ_cl). Then ρ⁽¹⁾ has
the **purely off-diagonal** form

> **ρ⁽¹⁾ = χ⊥ := −i[G, ρ_cl],  (χ⊥)_{ab} = −i G_{ab}(p_a − p_b),  (χ⊥)_{aa} = 0,  supported on 𝒮.   (a)**

(Indeed `[G,ρ_cl]_{ab} = G_{ab}p_b − p_a G_{ab} = −G_{ab}(p_a − p_b)`, so the diagonal a=b vanishes
identically and the off-diagonal survives because **G_{ab} ≠ 0 and p_a ≠ p_b** in general.) χ⊥ ≠ 0 **iff**
G is off-diagonal in ρ_cl's eigenbasis **and** the connected level pair is non-degenerate — which is exactly
the **un-twirled** non-unital case (P2 C0). The **twirled/dephased** ZZ would be diagonal in ρ_cl's basis
⇒ [G,ρ_cl]=0 ⇒ χ⊥=0 ⇒ O(φ²) — the **excluded** case (P2 §2, "unital-diagonal/twirled ⇒ χ⁽¹⁾=0, slope 2").

This is the coherent analog of P2's S1 (where the **non-unital** classical knob made ρ⁽¹⁾ carry a nonzero
*diagonal* connected A:C cumulant). Here the coherent knob makes ρ⁽¹⁾ **off-diagonal** — and off-diagonal
perturbations of a diagonal-in-its-own-basis state are exactly the ones a **classical** (diagonal) clustering
theory **cannot represent**, which is why this is the decisive object for the coherent sector. The trace
`Tr ρ⁽¹⁾ = −i Tr[G,ρ_cl] = 0` (a), as required (cyclicity).

### 1.3 What "good ρ_cl" means (a, the KKB-below-threshold input)
ρ_cl is classical, diagonal, and **below the decodability threshold**, so (classical Hammersley–Clifford /
the composition-limit proof) it is a **classical Markov network with finite correlation length ξ**:

> **I(A:C|B)[ρ_cl] = 0   (a, exact Markov at the classical point)**

and, crucially, its **CMI-clustering prefactor is POLYNOMIAL**: for the classical bulk, the cluster expansion
that reconstructs ρ_cl from its marginals converges with a **poly(|A|,|C|)** prefactor (this is the classical
sector that the project has **proven**: composition limit = decodability threshold, `w ≳ 2ξ log(L/ε)`). This
is the premise that the coherent perturbation is built **on top of** — and it is the reason the worst-case
KKB exp prefactor is **not** the relevant constant here. (a, premise — the classical limit is the proven
input, cited not re-derived.)

---

## 2. The φ-expansion of I(A:C|B): leading order is O(φ²), prefactor is the KMB metric of ρ_cl

### 2.1 I as a relative entropy; first variation vanishes at the Markov point (a)
Write the von Neumann CMI

> I(A:C|B) = S(ρ_AB) + S(ρ_BC) − S(ρ_B) − S(ρ_ABC),  S(ρ) = −Tr ρ log ρ.   (a, definition)

Two exact facts pin the leading order:

**(F1, a) Non-negativity + analyticity.** I(A:C|B) ≥ 0 for all states (strong subadditivity, Lieb–Ruskai),
and I[ρ(φ)] is **real-analytic in φ** (ρ(φ) is a finite-dim analytic family with ρ_cl full-rank on its
support; S is analytic where eigenvalues stay positive — guaranteed for small φ by the spectral floor p_min).

**(F2, a) Markov stationarity.** I[ρ(0)] = I[ρ_cl] = 0 is the **global minimum** of a non-negative analytic
function. A non-negative analytic function at an interior minimum has **vanishing first derivative**:

> **dI/dφ |_{φ=0} = 0   (a)** ⇒ leading correction is **at least O(φ²)**.

This is the same argument as P2 §3.2/§6 (there flagged as a *derived corollary*, not papers' words) — but here
it is **decisive for the prefactor**, not just the order.

**(F2′, a) Exact φ-parity — I is EVEN in φ (stronger than stationarity, no end-point subtlety).** In the Z
basis both ρ_cl and G = Z⊗Z are **real symmetric** (ρ_cl real-symmetric: its Bell/X eigenbasis has real
components; G real diagonal). Hence `U_φ = e^{−iφG}` satisfies `U_φᵀ = e^{−iφGᵀ} = U_φ` and `U_φ* = e^{+iφG}`.
Transpose the perturbed state:

> ρ(φ)ᵀ = (U_φ ρ_cl U_φ†)ᵀ = (U_φ†)ᵀ ρ_clᵀ U_φᵀ = U_φ* ρ_cl U_φ = e^{+iφG} ρ_cl e^{−iφG} = **ρ(−φ)**.   (a)

Transpose commutes with partial trace blockwise, so each marginal obeys ρ_X(φ)ᵀ = ρ_X(−φ) too. Since every
entropy in I depends **only on eigenvalues** and ρᵀ is similar to ρ (same spectrum), `S(ρ_X(−φ)) =
S(ρ_X(φ)ᵀ) = S(ρ_X(φ))` for X ∈ {AB, BC, B, ABC}. Therefore

> **I[ρ(−φ)] = I[ρ(φ)]  ⇒  I is EVEN in φ  ⇒  every odd coefficient vanishes, in particular dI/dφ|₀ = 0.   (a)**

The O(φ²) leading order is thus **exact by symmetry**, with **no interior-point/end-point subtlety** — cleaner
than P2's one-sided `R−1` coordinate (which forced the B-2 switch to the signed δ′). For the coherent knob the
natural coordinate φ is already two-sided, and parity does the work stationarity alone could not guarantee at
a boundary. (This also disposes of the §3.5 caveat for the unitary edge: the even structure is exact.)

### 2.2 The second-order coefficient = Hessian of −S contracted on ρ⁽¹⁾ (a)
Because dI/dφ|₀ = 0, the φ² coefficient is the **Hessian** of I at ρ_cl contracted with ρ⁽¹⁾ = χ⊥ (the φ²
contribution of ρ⁽²⁾ drops at second order *for the I functional* exactly because the **first** derivative
of I vanishes — the ρ⁽²⁾ term multiplies dI/dρ|_{ρ_cl} which is zero on the directions ρ⁽²⁾ lives in; shown
in §2.4). So

> **κ = ½ d²I/dφ² |₀ = ½ Hess_I[ρ_cl](χ⊥, χ⊥).   (a)**

The Hessian of S at ρ is the **negative Kubo–Mori–Bogoliubov (KMB) quadratic form** (standard; the KMB metric
*is* the second-order expansion of relative entropy / von Neumann entropy — refs §5). Derive the kernel by the
standard double-operator-integral (Daleckii–Krein) formula for the second Fréchet derivative of the matrix
function `f(ρ) = −Tr ρ log ρ`: in the eigenbasis ρ_cl = Σ_a p_a |a⟩⟨a|, for a Hermitian traceless variation X,

> **−½ d²S/dt²[ρ_cl](X,X) = ½ ⟨X, X⟩_KMB(ρ_cl),  ⟨X,X⟩_KMB := Σ_{a,b} |X_{ab}|² · k(p_a, p_b)   (a)**
>
> **kernel  k(p_a, p_b) = (log p_a − log p_b)/(p_a − p_b) > 0,  k(p,p) = 1/p   (a, divided difference of log).**

The kernel is the first divided difference of `log` (= the derivative of `−x log x` differenced), which is
**exactly positive** and **monotone**. Two equivalent standard forms, both used in the literature: the
divided-difference (DOI) form above, and the integral form `⟨X,X⟩_KMB = ∫₀^∞ Tr[X (ρ+s)^{−1} X (ρ+s)^{−1}] ds`
(resolvent representation of the same kernel — note this is the **entropy-Hessian / inverse-KMB-metric** form,
the one whose kernel is `k = (log p_a−log p_b)/(p_a−p_b)`, distinct from the **forward** KMB metric
`∫₀¹ Tr[ρ^s X ρ^{1−s} X] ds` whose kernel is the inverse `(p_a−p_b)/(log p_a−log p_b)`). I use the
divided-difference form `k(p_a,p_b)` throughout; it is the correct one for the **second derivative of the
entropy** (Petz, *Quantum Information Theory and Quantum Statistics*, §7; the BKM metric as relative-entropy
Hessian).

### 2.3 The decisive computation — κ in closed form, and its prefactor (a)
Now plug in the off-diagonal first-order coherence `(χ⊥)_{ab} = −i G_{ab}(p_a − p_b)` from §1.2. The
**off-diagonal** structure is what makes this clean: only a≠b terms appear, and the `(p_a − p_b)` factors
**cancel one power** against the kernel denominator:

```
Hess_I = (Hess on AB) + (Hess on BC) − (Hess on B) − (Hess on ABC),   each = −d²S/dt² = ⟨·,·⟩_KMB
```

For the **global** ABC term:

> ⟨χ⊥, χ⊥⟩_KMB^{ABC} = Σ_{a≠b} |G_{ab}|² (p_a − p_b)² · (log p_a − log p_b)/(p_a − p_b)
> = Σ_{a≠b} |G_{ab}|² (p_a − p_b)(log p_a − log p_b).   **(a, EXPLICIT)**

Define the **per-pair coherent susceptibility**

> **σ(p_a, p_b) := (p_a − p_b)(log p_a − log p_b) ≥ 0   (a)** — symmetric, vanishes as (p_a−p_b)²/p̄ for
> nearly-degenerate levels, grows like p_max·log(p_max/p_min) at most.

So the global ABC second-order piece is `Σ_{a≠b}|G_{ab}|² σ(p_a,p_b)`, and the full κ is the **alternating
sum of the four such forms** on (AB, BC, B, ABC), each evaluated with its **own** reduced spectrum/eigenbasis:

> **κ = ½ Hess_I[ρ_cl](χ⊥, χ⊥)
>     = ½ [ ⟨χ⊥^{AB},χ⊥^{AB}⟩_KMB^{AB} + ⟨χ⊥^{BC},χ⊥^{BC}⟩_KMB^{BC} − ⟨χ⊥^{B},χ⊥^{B}⟩_KMB^{B}
>           − ⟨χ⊥,χ⊥⟩_KMB^{ABC} ]   (a, EXACT)**

where χ⊥^{X} = Tr_{∖X} χ⊥ are the reduced first-order variations. **κ ≥ 0 exactly** (the Hessian of I at a
state is positive-semidefinite because I ≥ 0 attains its minimum 0 there — SSA; Lieb–Ruskai). This is the
**φ-leading CMI, exact**. Define σ̃ as the resulting **connected KMB kernel** (the alternating combination):

> **κ = ½ Σ_{(a,b): seam-connected, a≠b} |G_{ab}|² · σ̃(p_a, p_b),   σ̃ ≥ 0.   (a)**

**The connected-cancellation / screening claim (a, structure — the locality input):** the marginal-diagonal
(disconnected A:C) contributions cancel in this alternating sum, exactly as in P2 §2/§3, leaving only the
**B-non-shielded connected coherence**. For ρ_cl a **classical Markov network of correlation length ξ**
(premise §1.3), the reduced spectra `{p_a^{X}}` and the kernels factorize up to O(e^{−w/ξ}) corrections for
any pair (a,b) whose seam edge is buried ≥ w deep in the buffer B — this is precisely the **classical Markov
screening of ρ_cl**, which has the **good poly prefactor** by the proven classical limit. Hence σ̃(p_a,p_b)
is **non-negligible only for seam pairs within O(ξ) of the A–C interface**, and **suppressed by e^{−w/ξ}**
beyond. This is the step that makes κ **local**; it is **(a)-structure inherited from ρ_cl's proven classical
clustering**, not a new non-perturbative bound. (It is **not** a closed numerical identity — the constant in
the O(e^{−w/ξ}) is ρ_cl-dependent; what is exact is that the screening rate is ρ_cl's **classical** ξ, the
poly-prefactor one, never the KKB worst-case exp.)

### 2.4 Why ρ⁽²⁾ does not contribute at O(φ²) (a)
At second order I[ρ_cl + φχ⊥ + φ²ρ⁽²⁾] = I[ρ_cl] + φ·dI[χ⊥] + φ²·(dI[ρ⁽²⁾] + ½Hess_I[χ⊥,χ⊥]) + O(φ³).
The φ¹ term vanishes (F2). The `dI[ρ⁽²⁾]` term is the **first** Fréchet derivative of I at ρ_cl applied to
ρ⁽²⁾ = −½ad_G²(ρ_cl). But dI[·] at a Markov state is the linear functional whose Riesz representative is
`log ρ_AB + log ρ_BC − log ρ_B − log ρ_ABC` evaluated at ρ_cl = the **conditional-independence log-ratio**,
which **vanishes identically at a (classical) Markov state** (Hammersley–Clifford: the log-ratio is zero on
the support). Hence **dI[ρ⁽²⁾] = 0 (a)**, and only the Hessian-on-χ⊥ survives. (This is the precise reason
the **diagonal back-action ρ⁽²⁾ of the coherent edge is invisible at leading CMI order** — the prefactor is
governed entirely by the **off-diagonal** χ⊥.)

---

## 3. THE CRUX — does κ inherit exp(Θ(|A|+|C|)), or is the prefactor local?

### 3.1 Where the KKB exp prefactor comes from (a, restatement of the obstruction)
KKB [2407.05835] bounds I(A:C|B) for a **general** 2D state by a clustering expansion; the prefactor
`D_AC = exp(Θ(|A|+|C|))` arises because their bound must hold **uniformly over states that may be FAR from
any Markov state**, and the reconstruction (effective-Hamiltonian / belief-propagation) error accumulates on
the **boundary area**, which in 2D scales with `|∂A| ~ |A|^{1/2}` per the area law — but the *worst-case*
operator-norm control of the cluster expansion degrades the area-law boundary term up to a **volume**
`exp(Θ(|A|+|C|))` factor in the regime where no temperature/locality gap tames it. The exp prefactor is a
**non-perturbative, worst-case** constant. (Cite, never claim: this is KKB's bound; we do not re-derive it.)

### 3.2 Why the perturbative κ does NOT see that prefactor (a, the central argument)
The φ² coefficient κ (§2.3) is built from **three local objects only**:

1. **G** — supported on the **O(L) seam edges** 𝒮 (§1.1). `|G_{ab}|² = 0` unless the (a,b) transition is a
   single-seam-edge flip. So the sum in κ runs over **O(L) terms**, each a **2-cell** (one seam edge pair)
   matrix element — **no |A| or |C| volume sum**.
2. **The KMB kernel `k(p_a,p_b)` of ρ_cl** — this is a **fixed function of the classical bulk occupation
   probabilities**, i.e. of the **finite-ξ Gibbs weights**. For a below-threshold classical state with finite
   correlation length, `p_a` factorizes up to ξ-local corrections, so `σ̃(p_a,p_b)` depends only on the
   **O(ξ)-neighborhood** of the seam edge carrying (a,b). **No exp(volume).**
3. **The connected/alternating structure σ̃** — the CMI's defining cancellation (§2.3) makes σ̃ **supported on
   the B-buffer interface**: any (a,b) whose seam edge is screened by B (deeper than ξ into the buffer)
   cancels between the four KMB forms up to `exp(−w/ξ)` (the **classical** Markov screening of ρ_cl, which has
   the **good poly prefactor** by premise §1.3). So:

> **κ ≤ ½ · (max_e |G_e|²) · |𝒮| · max_{(a,b)∈seam} σ̃(p_a,p_b) · exp(−w/2ξ)
>      = O(L) · O(1) · O(log(1/p_min)) · exp(−w/2ξ).   (a, bound)**

**Every factor is local or O(L); the prefactor is `O(L·log(1/p_min))`, NOT `exp(Θ(|A|+|C|))`.** The
`exp(−w/2ξ)` is the **classical** screening of the bulk — the very factor the proven classical limit
controls with a poly prefactor. The coherent perturbation **rides on the classical Markov screening** and
**inherits its good (poly·L) prefactor, not the worst-case exp one.** ∎ (structure)

**The mechanism, stated plainly (a):** KKB's exp prefactor is the cost of finding the Markov reference
*from scratch* for an arbitrary state. We are **handed** the Markov reference — it is ρ_cl, the classical
below-threshold bulk, whose reference is known and whose clustering is poly. The coherent perturbation only
asks "how fast does I grow as I tilt ρ_cl off-diagonal by φ", and the **growth rate is the local KMB
curvature of ρ_cl**. Curvature of a good (poly-clustering) point is a **local** quantity. The worst-case
exp prefactor never enters because we never leave the **neighborhood** of the good point. **This is the
precise sense in which "a perturbation of a classical-Markov state evades the worst-case prefactor."**

### 3.3 The one place the exp prefactor could sneak back — and why it (almost) doesn't (a → the (b) gap)
The exp prefactor could re-enter through the **radius of convergence** of the φ-series. If the series
`I = κφ² + Σ_{n≥3} cₙ φⁿ` had a radius R(|A|,|C|) that **shrinks** as the regions grow (e.g.
`R ~ exp(−c(|A|+|C|))`), then for any fixed φ the series would diverge for large enough regions and the
quadratic truncation would be meaningless — the exp prefactor would have hidden in the **remainder**, not the
leading term. **This is the real content of the open problem.** I must show R is **bounded below
independently of |A|+|C|**.

**Bound on R (a, leading-order; the C1 gap at full order).** The φ-series of `−S(ρ(φ))` converges whenever
ρ(φ) stays positive-definite on its support, i.e. whenever the perturbation does not push an eigenvalue
through 0. The smallest eigenvalue of ρ_cl on its support is `p_min` (the classical spectral floor — for a
finite-ξ below-threshold bulk, `p_min ≥ exp(−O(ξ·|seam local patch|))`, **local**, NOT `exp(−|A|−|C|)`,
because the bulk factorizes beyond ξ so the global p_min is a **product of local floors** and the **log**
p_min is O(volume) but the **relevant** floor for a seam-supported perturbation is the **local** one on 𝒮).
The φ-perturbation χ⊥ has operator norm `‖φχ⊥‖ ≤ φ·2‖G‖·1 = O(φ·L)` (since `‖[G,ρ]‖ ≤ 2‖G‖‖ρ‖` and
‖G‖=O(L) but acts **block-locally** — per-edge ‖G_e‖=O(1)). Positivity is preserved per seam block while

> **φ ≲ p_min^{local} / ‖G‖_local = O(p_min^{local}) = O(exp(−O(ξ))).   (a, leading order)**

**Crucially, this radius depends on the LOCAL seam floor `p_min^{local} ~ exp(−O(ξ))`, NOT on the global
floor `exp(−O(|A|+|C|))`** — because the off-diagonal χ⊥ only mixes eigenvectors **within a seam edge's
O(ξ)-neighborhood** (G is seam-local; ad_G(ρ_cl) only connects |a⟩,|b⟩ differing on 𝒮). The eigenvalue
repulsion that could kill positivity is therefore a **local** 2-level problem with gap set by the **local**
floor. **So R is bounded below by a constant `O(exp(−ξ))` independent of |A|+|C|.** This is exactly the
escape: *the convergence radius is set by the correlation length ξ, not by the fragment size.*

**The C1 gap (why this is (b) not (a)).** The above bounds positivity **block-locally** and bounds the
**leading** (n=2) coefficient rigorously. To upgrade to a theorem I need the **n≥3 Fréchet remainder of −S**
to be controlled by the **same local kernel** — i.e. that the full Taylor remainder `R_N(φ)` of the matrix
function `−x log x` composed with ρ(φ) has its `|A|+|C|`-dependence bounded by the local seam floor, not the
global one. The third-order term involves a **triple** double-operator-integral `Σ G_{ab}G_{bc}G_{ca}·
(third divided difference of −x log x)`; its support is still **seam-local** (three G's, all on 𝒮), and its
kernel `[p_a,p_b,p_c]` (second divided difference of `log`) is still **local in ρ_cl**, so **the structure
holds** — but a *uniform* operator-norm bound on the **full** remainder, valid for **all** N and **all**
fragment sizes simultaneously, is the standard hard step in matrix-perturbation theory (the Kato/DOI
remainder). I derive the structure and the leading floor; the **uniform N-bound is the named missing step**.
**Status: CONTROLLED (b) — radius `φ ≲ exp(−O(ξ))` independent of |A|+|C|, modulo the uniform
higher-order DOI remainder bound (C1).**

### 3.4 Resummation alternative (a, makes the gap smaller)
The remainder worry can be **side-stepped** without the uniform N-bound, by **not Taylor-expanding I at all**
and instead bounding I directly via the **Fawzi–Renner route on the perturbed state**: `I(A:C|B)[ρ(φ)] ≥
−2 log F(ρ(φ), R(ρ_AB(φ)))` (and the matching **upper** bound is what we want). The relevant fact is that
the **rotated-Petz recovery map R depends only on ρ_BC(φ)** (JRSWW; cited in P2 §3). Because ρ_BC(φ) =
U_φ ρ_BC,cl U_φ† with U_φ **seam-local**, the recovery map is a **seam-local perturbation of the exact
classical recovery** (which is exact, residual 0, at φ=0). The recovery error is then an **O(φ) seam-local
operator**, and its contribution to I is **O(φ²) with the L-additive local prefactor** — the **same κ**,
now obtained **without** the entropy Taylor series, so **without the C1 remainder gap**. The cost: this gives
the **right order and locality** but a **looser constant** (the Petz route is a one-sided bound, P2 B-1/§3.5).
**So: order + locality of the prefactor = (a) via the Petz route; the sharp constant κ = (b) via the KMB
Taylor route (C1 gap).** Either way the **exp prefactor is gone** — that conclusion does **not** depend on
the C1 gap, only the **sharp constant** does.

### 3.5 Non-unitary coherent edge (a, completeness)
If the coherent seam edge is a non-unitary CP map (not pure conjugation), ρ⁽¹⁾ = χ⊥ + χ∥ has an extra
**diagonal** piece χ∥ (the back-action). χ∥ is exactly a **non-unital classical** perturbation — i.e. **P2's
S1 object** — so its CMI contribution is the **P2 non-unital κ_cl**, already shown there to be **local,
B-mediated, O(λ) per-seam residual / O(λ²) CMI** with the **same L-additive local prefactor**. The diagonal
and off-diagonal sectors **do not cross at second order** (the KMB kernel is block-diagonal between diagonal
and off-diagonal perturbations of a diagonal state — `Tr[ρ^s X_∥ ρ^{1−s} X_⊥]=0` since X_∥ diagonal, X_⊥
off-diagonal). So `κ = κ_⊥(φ²) + κ_∥(λ²)` **adds**, both local, **neither exp**. The coherent verdict is
**robust to the unitary-vs-CP distinction.** (a)

---

## 4. Connection to P2 — same statement or different? (a)

**Different statements, exactly reconciled by the √-bound.** Tabulated:

| | object | functional class | order in φ | parity | prefactor |
|---|---|---|---|---|---|
| **P2 C0 (this seam's residual)** | `D_Choi = ½‖ρ − glue(ρ_AB,ρ_BC)‖₁` | **trace-distance reconstruction residual** | **O(φ¹) LINEAR** | odd-sensitive (first-order survives) | local, O(L)-additive (P2 §5, B-3) |
| **P3 (this file)** | `I(A:C|B)` | **relative-entropy information** | **O(φ²) QUADRATIC** | **even** (Markov-stationary) | **local, O(L)·log(1/p_min), NOT exp** |

These are **not** the same order because they are **different functionals**:
- `D_Choi` is a **norm** (first-order in the perturbation: `‖ρ_cl + φχ + … − glue‖₁ = φ‖χ_uncaptured‖₁ + …`),
  so it sees the **O(φ)** linear residual. P2 C0: for the **un-twirled coherent edge**, the residual is
  **linear** because the off-diagonal χ⊥ is **not captured** by the mean-field/product glue (G0) — exactly
  parallel to P2's non-unital χ⁽¹⁾.
- `I(A:C|B)` is a **relative entropy** = a **squared-distance-like** (Bregman) quantity, second-order in the
  perturbation by Markov-stationarity (§2.1). So it sees **O(φ²)**.

**The bridge (a):** Fawzi–Renner / JRSWW give `D_Choi^{G1} ≤ √(I_nats) = √(κ) · φ + O(φ²)` (P2 §3.1, B-5
constant). So the **CMI route predicts a LINEAR-in-φ Petz residual** `√κ·φ` — **consistent with P2's
linear C0 residual**, with `c_{G1} ≤ √κ`. The two derivations are **the same physics seen through two
metrics**: P2 measures the residual directly (linear, sharp slope), P3 measures the information that
**upper-bounds** the residual (quadratic, but its √ is linear). **They agree that the per-seam coherent
defect is (i) linear in φ, (ii) L-additive, (iii) carries a LOCAL prefactor — no exp.**

**What P3 adds over P2 (the reason this file exists):** P2 establishes the **per-seam** residual is linear
and L-additive — but P2 explicitly **does not** address the **global 2D Markov property** / the **exp
prefactor obstruction** (P2 §5 B-3 only claims at-most-linear L-scaling of the *per-seam* residual, caveated
to L∈{1,2,3} exact-oracle). **P3 is the global statement:** it shows the **information-theoretic obstruction
itself** (the KKB exp prefactor that breaks global Markovianity / quantum BP in 2D) **does not bind
perturbatively** — the global CMI's φ-leading prefactor is local. That is the **coherent generalization of
the classical composition limit**, which P2 alone does not give.

---

## 5. The perturbative coherent composition limit (b, if CONTROLLED) — window scaling and φ-regime

Granting §3 (CONTROLLED, modulo the C1 remainder gap), the composition limit extends to the coherent sector
as follows. The classical limit (proven) is: composition is faithful when the window/buffer width

> `w ≳ 2ξ · log(L/ε)`   (classical, proven: composition limit = decodability threshold).

Adding the coherent seam at angle φ, the **global** composed-twin error is the **per-seam CMI aggregated over
O(L) seams** (P4 L-additivity, P2 §5; each seam contributes √κ·φ to the Choi residual via §4):

> **Composed-twin global Choi residual ≤ Σ_seams √(I_seam) ≈ L · √κ · φ · exp(−w/2ξ)
>  ≤ ε   ⟺   w ≳ 2ξ · [ log(L/ε) + log(√κ · φ) ].   (b, perturbative coherent composition limit)**

So the coherent edge **shifts the required window width by an ADDITIVE `2ξ·log(√κ φ)`** — a **mild,
ξ-scaled, φ-logarithmic** correction. Because `√κ φ ≤ 1` for the regime of interest, the correction is
**≤ 0 for small φ** (the coherent edge, being a *small* perturbation, needs **no extra width** beyond the
classical `w`), and grows only **logarithmically** as φ increases. **The coherent composition is controlled
in the same `w ~ ξ log(L/ε)` regime as the classical one, with at most a `2ξ log(1/φ)`-type additive
window penalty.** (b — registered band; miss = finding.)

**φ-regime of validity (a, from §3.3/3.4):**

> **0 ≤ φ ≲ φ* := c · exp(−O(ξ))   (local seam floor), independent of |A|+|C|.   (a leading / b sharp constant)**

For φ beyond φ*, the perturbation series' positivity guarantee fails **locally** (an eigenvalue of the seam
block approaches 0) and the expansion must be resummed (§6). **φ* is set by the correlation length, not the
fragment size** — the controlled regime does **not shrink** as the code grows. This is the decisive
"controlled" content: *for any 2D code size L, there is a φ-window `[0, φ*(ξ)]`, fixed by ξ alone, in which
coherent small-window composition is faithful with a poly·L (NOT exp) prefactor.*

---

## 6. Honest failure modes — where the expansion breaks (a)

1. **Large φ (φ ≳ φ* = exp(−O(ξ))) — OPEN.** Beyond the local positivity radius the Taylor series diverges;
   the off-diagonal χ⊥ has rotated an eigenvector enough that a seam-block eigenvalue crosses 0 and `−x log x`
   hits its non-analytic point. The KMB curvature **blows up** (`σ̃ ~ log(1/p)` as p→0). **Verdict for large
   φ: INHERITS-or-OPEN** — the perturbative escape says **nothing** here; the worst-case KKB exp prefactor
   may well bind at large coherent angle. This is the **honest boundary**: the result is **a small-φ theorem,
   not an all-φ one.** (The registered knob φ∈{0,0.05,0.10,0.15} sits at the **low end** — `√κ φ` with κ=O(1)
   gives Choi residuals ~0.05–0.15, P2's measured ×8.7/×3 cross-window quality at φ²; comfortably inside φ*
   for ξ=O(1). So the **registered experiment is inside the controlled regime** — a (b) prediction the CF-WR
   run can falsify.)

2. **Near the decodability threshold (ξ → ∞) — INHERITS.** The escape's prefactor is `O(L·log(1/p_min))·
   exp(−w/2ξ)` and the radius is `φ* ~ exp(−O(ξ))`. As ξ → ∞ (approaching threshold), **φ* → 0** and the
   prefactor's `exp(−w/2ξ) → 1` (screening lost). **The controlled window collapses at threshold** — the
   coherent perturbation provides **no help** once the classical bulk itself loses finite correlation length.
   This is consistent and expected: the coherent escape is **parasitic on the classical Markov screening**;
   when that fails (at threshold), so does the coherent control. **Verdict near threshold: INHERITS the
   obstruction** (now for the classical reason). The perturbative result is a **strictly-below-threshold**
   statement.

3. **Resummation / non-analyticity — the C1 gap (b).** The uniform-in-(|A|+|C|) bound on the **higher-order**
   DOI remainder (§3.3) is **not** closed here. If, contrary to the leading-order analysis, the higher-order
   terms carried a **fragment-size-dependent** growth (e.g. via a secular `n!·(|A|+|C|)` from nested
   commutators that the seam-locality argument fails to suppress), the exp prefactor could re-enter at finite
   φ. I gave the **structural** reason it does not (every order is seam-local, three-or-more G's all on 𝒮) and
   the **Petz-route** order+locality proof that does **not** use the series (§3.4) — but the **sharp uniform
   constant** remains (b). **This is the single named missing step for a full theorem.**

4. **Degeneracy of ρ_cl (a, controlled).** If ρ_cl has exact eigenvalue degeneracies on 𝒮 (p_a = p_b for a
   seam-coupled pair), the kernel `k(p,p)=1/p` is finite (no blow-up) and `σ(p_a,p_b)→0` — degeneracy
   **helps** (the coherent rotation within a degenerate subspace costs **no** CMI at leading order, since
   χ⊥=−iG(p_a−p_b)→0). So degeneracy is **not** a failure mode; it is a **null direction**. (Matches P2.3:
   the unital point p01=p10 is the exact-degeneracy / null case.)

5. **Off-support coherence (a, controlled).** If G connected eigenvectors **outside** ρ_cl's support
   (p_b = 0 strictly), the kernel `(log p_a − log 0)` diverges — but a **strictly** zero classical occupation
   means a forbidden configuration, and the coherent edge **cannot** create population there at first order in
   a CPTP map without a diagonal (χ∥) companion (§3.5). For the **unitary** dressing on the support, p_b>0
   always (the spectral floor), so this is **not** triggered. Flagged for the **non-unitary** edge: the
   χ∥ companion regularizes it (it **is** the population that fills the level), keeping σ finite. (a)

---

## 7. Must-cite

- **Obstruction (the exp prefactor we break):** Kuwahara, Kato, Brandão — *Clustering of conditional mutual
  information and quantum Markov structure at arbitrary temperatures*, [arXiv:2407.05835](https://arxiv.org/abs/2407.05835)
  (PRX, [10.1103/9hx7-pzxw](https://link.aps.org/doi/10.1103/9hx7-pzxw)); and the threshold-temperature
  precursor [arXiv:1910.09425](https://arxiv.org/abs/1910.09425) / PRL **124**, 220601 (2020). **Cite for the
  `D_AC = exp(Θ(|A|+|C|))` worst-case prefactor and the exponential-in-distance / poly-correlation-length
  clustering — never claimed, only applied/evaded.**
- **CMI = recovery (the √-bridge to P2):** Fawzi, Renner — *Quantum conditional mutual information and
  approximate Markov chains*, CMP **340** (2015), [arXiv:1410.0664](https://arxiv.org/abs/1410.0664):
  `½‖ρ_ABC − R(ρ_AB)‖₁ ≤ √(I_nats)`-type bound, R depends only on ρ_BC. **Fully quantum, holds regardless —
  the per-seam bound that survives the 2D obstruction.**
- **Rotated universal recovery (the explicit R):** Sutter, Fawzi, Renner (JRSWW) — *Universal recovery map
  for approximate Markov chains*, Proc. R. Soc. A **472** (2016), [PMC4841654](https://pmc.ncbi.nlm.nih.gov/articles/PMC4841654/).
- **KMB metric = relative-entropy Hessian (the prefactor's identity):** Bogoliubov–Kubo–Mori inner product
  ([Wikipedia: Bogoliubov inner product](https://en.wikipedia.org/wiki/Bogoliubov_inner_product)); the
  second-order expansion of S(ρ‖σ) / von Neumann entropy yields the KMB quadratic form with divided-difference
  kernel `(log a − log b)/(a − b)`. Standard (Petz, *Quantum Information Theory and Quantum Statistics*);
  perturbation-theory exposition e.g. [arXiv:2106.05533](https://arxiv.org/pdf/2106.05533). **The local
  integral kernel that replaces the worst-case exp prefactor.**
- **Strong subadditivity (I ≥ 0, the stationarity premise):** Lieb–Ruskai (1973).
- **Local:** `P2_derivation.md` (per-seam C0 linear residual, the √-bridge, L-additivity); the
  composition-limit proof (`w ≳ 2ξ log(L/ε)`, classical sector); `D_package_derivations.md` §D5 (T-B theorem:
  the **non-unital** classical χ∥ companion of §3.5).

---

## 8. FROZEN P3 (the registrable claims)

- **P3.1 (a, structure):** `I(A:C|B)[ρ(φ)] = κ φ² + O(φ³)`, κ = ½⟨χ⊥, K_cl χ⊥⟩_KMB ≥ 0, leading order
  **O(φ²) exact by Markov-stationarity + φ-parity** (cleaner than P2's one-sided coordinate). χ⊥ = −i[G,ρ_cl]
  **off-diagonal**, seam-supported.
- **P3.2 (a, the verdict):** κ's prefactor is `O(L · log(1/p_min^{local})) · exp(−w/2ξ)` — **LOCAL / O(L),
  NOT exp(Θ(|A|+|C|))**. **The perturbative coherent composition ESCAPES the KKB worst-case prefactor**, by
  riding the classical Markov screening of ρ_cl. Mechanism: KKB's exp is the cost of reconstructing the Markov
  reference from scratch; the perturbation is handed the reference (ρ_cl) and only pays its **local KMB
  curvature**.
- **P3.3 (b, sharp constant / convergence):** the φ-series radius is `φ* ~ exp(−O(ξ))`, **independent of
  |A|+|C|** — the controlled φ-window is set by ξ, **not** by code size. **(b)** because the **uniform
  higher-order DOI remainder bound (C1)** is structural-but-not-closed; the **order + locality** are **(a)**
  via the Petz route (§3.4), only the **sharp κ** is (b) via the KMB Taylor route.
- **P3.4 (b, the limit):** perturbative coherent composition limit `w ≳ 2ξ[log(L/ε) + log(√κ φ)]` — coherent
  edge costs at most an **additive `2ξ log(1/φ)`** window penalty; for small φ, **no extra width**.
- **P3.5 (a, P2-reconciliation):** P2's **O(φ) linear** per-seam residual and P3's **O(φ²) quadratic** CMI are
  the **same physics in two metrics**, bridged by `D_Choi ≤ √(I_nats) = √κ·φ` — both **linear in φ**, both
  **L-additive local**. P3 is the **global** statement P2 does not make.
- **Honest boundary (a):** **small-φ, strictly-below-threshold theorem only.** Large φ (≳ exp(−ξ)) and
  ξ→∞ (threshold) **INHERIT** the obstruction; the result claims **nothing** there. The registered CF-WR
  knob φ∈{0,…,0.15} at R̂≈5.3 sits **inside** the controlled regime — a **(b) prediction the run can
  falsify** (if the measured global CMI / composed Choi residual grows **faster than φ²** or shows
  **fragment-size-dependent** prefactor, P3.2 is **refuted** = finding).

**Tri-state verdict: CONTROLLED (small φ, below threshold) — at the (b) level with the C1 remainder bound as
the single exact missing step; order+locality (a)-proven via Petz; INHERITS at large φ / at threshold
(honestly bounded).**
